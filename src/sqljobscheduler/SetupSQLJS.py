import grp
import json
import os
import pwd
import socket
import subprocess
import sys
from pathlib import Path

from sqljobscheduler import configSetup
from sqljobscheduler.EmailNotifier import EmailNotifier


def print_bar() -> None:
    """Print a bar of 100 '#' characters."""
    print("#" * 100)


def user_exists(username: str) -> bool:
    """Check if a user exists on the system."""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def group_exists(groupname: str) -> bool:
    """Check if a group exists on the system."""
    try:
        grp.getgrnam(groupname)
        return True
    except KeyError:
        return False


def get_current_python_env() -> Path:
    """Get the current Python environment path."""
    # Get the path to the current Python executable
    python_exec = Path(sys.executable)
    # Get the parent directory (bin directory)
    bin_dir = python_exec.parent
    # Get the virtual environment root directory
    venv_root = bin_dir.parent
    return venv_root


def verify_python_env(python_env: Path) -> bool:
    """Verify that the Python environment has required packages."""
    try:
        python_exec = python_env / "bin" / "python"
        if not python_exec.exists():
            print(f"Python executable not found at {python_exec}")
            return False

        # Check for required packages
        required_packages = ["sqljobscheduler"]
        for package in required_packages:
            result = subprocess.run(
                [str(python_exec), "-c", f"import {package}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"Required package '{package}' not found in Python environment")
                return False
        return True
    except Exception as e:
        print(f"Error verifying Python environment: {e}")
        return False


def get_remote_ip() -> str:
    """Get the remote IP address of the system."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print(f"Error getting remote IP address: {e}")
        return None


def load_template(templates_dir: Path, template_name: str) -> str:
    """Load a template file from the templates directory"""
    template_path = templates_dir / template_name
    with open(template_path, "r") as f:
        return f.read()


def setup_service_files() -> None:
    """Generate service and runner files from templates."""
    print("Setting up service and runner files...")

    # Get the project root directory
    repo_dir = Path(__file__).parent.parent.parent
    server_service_dir = repo_dir / "ServerService"
    templates_dir = server_service_dir / "templates"
    output_dir = Path(configSetup.get_config_dir(), "SystemdServices")
    output_dir.mkdir(exist_ok=True, parents=True)

    shell_template = load_template(templates_dir, "sh_template.txt")
    service_template = load_template(templates_dir, "service_template.txt")

    output_shell_scripts_dir = output_dir / "shell_scripts"
    output_shell_scripts_dir.mkdir(exist_ok=True, parents=True)

    output_service_files_dir = output_dir / "services"
    output_service_files_dir.mkdir(exist_ok=True, parents=True)

    # load app settings
    with open(templates_dir / "app_settings.json", "r") as f:
        apps = json.load(f)

    # Configuration
    while True:
        user = input(
            "Enter the username (Recommended to use a user with admin privileges or with expanded privleges onto drive holding data): "
        )
        if user and user_exists(user):
            break
        else:
            print(f"User '{user}' does not exist on this system. Please try again.")

    while True:
        group = input(
            "Enter the group name (Recommended to use a group with admin privileges or with expanded privleges onto drive holding data): "
        )
        if group and group_exists(group):
            break
        else:
            print(f"Group '{group}' does not exist on this system. Please try again.")

    # Automatically detect current Python environment
    python_env = get_current_python_env()
    if not verify_python_env(python_env):
        print(f"Error: Current Python environment at '{python_env}' is not valid.")
        return

    server_address = get_remote_ip()
    print(f"Remote IP address found: {server_address}")
    while True:
        choice = input("Do you want to use this IP address? (y/n): ")
        if choice.lower() in ["y", "n"]:
            break
        else:
            print("Invalid choice. Please try again.")

    if choice.lower() == "n":
        print("Please enter the server address for remote access.")
        while True:
            server_address = input(
                "(use `ip a` to find broadcast address; type s or skip): "
            )
            if server_address:
                break
            elif server_address.lower() in ["s", "skip"]:
                server_address = None
                break
            else:
                print("Server address cannot be empty. Please try again.")

    print("Using:")
    print(f"    User: {user}")
    print(f"    Group: {group}")
    print(f"    Python environment: {python_env}")
    print(f"    Repo directory: {str(repo_dir)}")
    if server_address is not None:
        print(f"    Server address: {server_address}")

    print("Processing templates and generating service files...")
    print_bar()

    created_services = []

    for app_name, app_settings in apps.items():
        run_script_path = (
            output_shell_scripts_dir / f"run{app_settings['script_name'].upper()}.sh"
        )
        run_script_path.parent.mkdir(parents=True, exist_ok=True)

        if app_settings["port"] is not None:
            app_settings["command"] = app_settings["command"].format(
                port=app_settings["port"]
            )

        print(f"Processing {app_name}")
        for key, value in app_settings.items():
            print(f"    {key}: {value}")
        print()

        run_script_content = shell_template.format(
            python_env=python_env,
            repo_dir=str(repo_dir),
            service_name=app_settings["script_name"],
            command=app_settings["command"],
        )

        with open(run_script_path, "w") as f:
            f.write(run_script_content)

        service_content = service_template.format(
            description=app_settings["description"],
            user=user,
            group=group,
            shell_script_path=run_script_path,
            working_dir=os.path.dirname(run_script_path),
        )

        service_path = output_service_files_dir / f"{app_name.lower()}.service"
        with open(service_path, "w") as f:
            f.write(service_content)

        created_services.append(
            {
                "name": app_name,
                "script_name": app_settings["script_name"],
                "shell_name": run_script_path.name,
                "port": app_settings["port"],
                "service_path": service_path.name,
            }
        )
    print_bar()
    print("Service files generated successfully!")

    print("\nService files created successfully!")

    return (
        output_dir,
        created_services,
        server_address,
        user,
        group,
    )


def print_service_install_instructions(
    user: str, group: str, output_dir: Path, created_services: list
):
    print("Services user set to:", user)
    print("Services group set to:", group)
    print("\nTo install the services:")
    print("1. Copy the service files to systemd directory:")
    print(f"   sudo cp {output_dir}/services/*.service /etc/systemd/system/")

    print("\n2. Reload systemd daemon to log changes:")
    print("   sudo systemctl daemon-reload")

    print("\n3. Make run scripts executable and enable and start each service:")
    for service in created_services:
        print(f"For {service['name']}:")
        print(f"   chmod +x {output_dir}/shell_scripts/{service['shell_name']}")
        print(f"   sudo systemctl enable {service['name'].lower()}")
        print(f"   sudo systemctl start {service['name'].lower()}")
        print()

    print("\n4. Check status of services:")
    for service in created_services:
        print(f"   sudo systemctl status {service['name'].lower()}")


def main():
    print("Welcome to the SQLJobScheduler setup script.")
    print_bar()

    # Setup service files
    print("First we need some information to setup the service files.")
    (
        output_dir,
        created_services,
        server_address,
        user,
        group,
    ) = setup_service_files()

    print(
        "\nNow we need to generate the email credentials to enable email notifications."
    )
    print(
        "Works best with gmail. Please refer to the documentation for more details to obtain app password: https://support.google.com/mail/answer/185833?hl=en\n"
    )
    port2use = None
    for service in created_services:
        if service["port"] is not None:
            port2use = service["port"]
            break

    if server_address is None:
        dashboard_url = None
    else:
        dashboard_url = f"{server_address}:{port2use}"

    print(
        f"For the email credentials, we will use the following server address: {server_address}\nand the following dashboard url: {dashboard_url}\n"
    )
    EmailNotifier.generate_email_credentials_json(
        server_address=server_address, dashboard_url=dashboard_url
    )

    print_bar()
    print("Setup completed successfully!")

    print_service_install_instructions(
        user=user,
        group=group,
        output_dir=output_dir,
        created_services=created_services,
    )


if __name__ == "__main__":
    main()
