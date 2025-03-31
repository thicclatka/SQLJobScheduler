import subprocess
from pathlib import Path
import pwd
import grp
import sys
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


def setup_service_files() -> None:
    """Generate service and runner files from templates."""
    print("Setting up service and runner files...")

    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    server_service_dir = project_root / "ServerService"

    server_services_files_dir = server_service_dir / "services"
    server_services_files_dir.mkdir(exist_ok=True)

    server_services_shell_scripts_dir = server_service_dir / "shell_scripts"
    server_services_shell_scripts_dir.mkdir(exist_ok=True)

    templates_dir = server_service_dir / "templates"

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

    scripts_dir = str(project_root)

    # Automatically detect current Python environment
    python_env = get_current_python_env()
    if not verify_python_env(python_env):
        print(f"Error: Current Python environment at '{python_env}' is not valid.")
        return

    while True:
        server_address = input(
            "Enter outgoing IP address of server if SQLJobScheduler is running remotely on a server (Hit Enter for default which will leave it blank): "
        )
        if server_address == "":
            server_address = None
            break
        else:
            break

    while True:
        port = input("Enter the port number for the job lister: ")
        if port.isdigit() and 1 <= int(port) <= 65535:
            break
        else:
            print(
                "Invalid port number. Please enter a valid port number between 1 and 65535."
            )

    while True:
        app_name = input(
            "Enter the name of the app (Hit Enter for default, which is 'gpujobs'): "
        )
        if app_name:
            break
        else:
            app_name = "gpujobs"
            break

    print("Using:")
    print(f"    User: {user}")
    print(f"    Group: {group}")
    print(f"    Python environment: {python_env}")
    print(f"    Scripts directory: {scripts_dir}")
    print(f"    Server address: {server_address}")
    print(f"    Port: {port}")
    print(f"    App name: {app_name}")

    print("Processing templates and generating service files...")
    print_bar()

    try:
        print("Generating start_jobrunner.sh...")
        # Process start_jobrunner.sh template
        with open(templates_dir / "template4_start_jobrunner", "r") as f:
            content = f.read()
        content = content.replace("{python_env}", str(python_env))
        content = content.replace("{scripts_dir}", scripts_dir)

        with open(server_services_shell_scripts_dir / "start_jobrunner.sh", "w") as f:
            f.write(content)

        print("Generating gpuJobRunner.service...")
        # Process gpuJobRunner.service template
        with open(templates_dir / "template4jpuJobRunner", "r") as f:
            content = f.read()
        content = content.replace("{user}", user)
        content = content.replace("{group}", group)
        content = content.replace("{scripts_dir}", scripts_dir)

        with open(server_services_files_dir / "gpuJobRunner.service", "w") as f:
            f.write(content)

        print("Generating jobLister.service...")
        # Process jobLister.service template
        with open(templates_dir / "template4JobLister", "r") as f:
            content = f.read()
        content = content.replace("{user}", user)
        content = content.replace("{python_env}", str(python_env))
        content = content.replace("{scripts_dir}", scripts_dir)
        content = content.replace("{port}", port)
        content = content.replace("{app_name}", app_name)

        with open(server_services_files_dir / "jobLister.service", "w") as f:
            f.write(content)

        print("Service files generated successfully!")

    except FileNotFoundError as e:
        print(f"Error: Template file not found: {e}")
        return
    except Exception as e:
        print(f"Error generating service files: {e}")
        return

    return (
        server_services_files_dir,
        server_services_shell_scripts_dir,
        server_address,
        port,
        app_name,
    )


def print_service_instructions_post_setup(
    server_services_files_dir: Path, server_services_shell_scripts_dir: Path
):
    print("\nTo install the service, run these commands:")
    print(f"    sudo cp {server_services_files_dir}/*.service /etc/systemd/system/")
    print("     sudo systemctl daemon-reload")

    for service in ["gpuJobRunner", "jobLister"]:
        if service == "gpuJobRunner":
            print(
                f"     sudo chmod +x {server_services_shell_scripts_dir}/start_jobrunner.sh"
            )
        print(f"     sudo systemctl enable {service}")
        print(f"     sudo systemctl start {service}")


def main():
    print("Welcome to the SQLJobScheduler setup script.")
    print_bar()

    # Setup service files
    print("First we need some information to setup the service files.")
    (
        server_services_files_dir,
        server_services_shell_scripts_dir,
        server_address,
        port,
        app_name,
    ) = setup_service_files()

    print(
        "\nNow we need to generate the email credentials to enable email notifications."
    )
    print(
        "Works best with gmail. Please refer to the documentation for more details to obtain app password: https://support.google.com/mail/answer/185833?hl=en\n"
    )
    dashboard_url = f"{server_address}:{port}/{app_name}"

    print(
        f"For the email credentials, we will use the following server address: {server_address}\nand the following dashboard url: {dashboard_url}\n"
    )
    EmailNotifier.generate_email_credentials_json(
        server_address=server_address, dashboard_url=dashboard_url
    )

    print_bar()
    print("Setup completed successfully!")

    print_service_instructions_post_setup(
        server_services_files_dir=server_services_files_dir,
        server_services_shell_scripts_dir=server_services_shell_scripts_dir,
    )


if __name__ == "__main__":
    main()
