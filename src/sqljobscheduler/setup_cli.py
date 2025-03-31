#!/usr/bin/env python3
import argparse
from sqljobscheduler.SetupSQLJS import (
    setup_service_files,
    print_service_instructions_post_setup,
)
from sqljobscheduler.EmailNotifier import EmailNotifier


def main():
    parser = argparse.ArgumentParser(description="SQLJobScheduler Setup CLI")
    parser.add_argument(
        "--email-only",
        action="store_true",
        help="Only set up email notifications without full system setup",
    )
    args = parser.parse_args()

    if args.email_only:
        print("Setting up email notifications only...")
        EmailNotifier.generate_email_credentials_json()
        print("Email setup completed!")
    else:
        print("Running full SQLJobScheduler setup...")
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

        print("Setup completed successfully!")

        print_service_instructions_post_setup(
            server_services_files_dir=server_services_files_dir,
            server_services_shell_scripts_dir=server_services_shell_scripts_dir,
        )


if __name__ == "__main__":
    main()
