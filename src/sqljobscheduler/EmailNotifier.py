import os
from textwrap import dedent
import hashlib
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
from pathlib import Path
import getpass
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EmailNotifier:
    def __init__(self, smtp_server: str = "smtp.gmail.com", port: int = 587):
        self.smtp_server = smtp_server
        self.port = port

        credentials_manager = CredentialsManager()

        credentials = credentials_manager.decrypt_credentials()
        self.sender_email = credentials["email"]
        self.sender_password = credentials["password"]
        self.server_address = credentials["server_address"]
        self.dashboard_url = credentials["dashboard_url"]

    def send_test_email(self, recipient: str) -> None:
        """Send test email"""
        subject = "Test Email"
        # body = self.generate_header() + "\n\nThis is a test email"
        body = "This is a test email"
        self.send_email(recipient, subject, body)

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.sender_email
            msg["To"] = recipient
            msg["Subject"] = f"[SQL Job Scheduler] {subject}"
            msg.add_header("Reply-To", self.sender_email)
            msg.add_header("X-Priority", "3")
            msg.add_header("X-Mailer", "SQL Job Scheduler")

            signature = dedent("""
            This is an automated message sent from {}.
            Please do not reply to this email.""").format(self.server_address)

            bar = "-" * 100
            text_header = f"{self.generate_header()}\n{bar}"
            text_body = f"\n{body.strip()}\n\n{signature.strip()}"
            text_email = f"{text_header}\n{text_body}"
            msg.attach(MIMEText(text_email, "plain"))

            html_header = f"{self.generate_header(html=True)}<div style='color: #666; font-size: 0.9em; border-top: 1px solid #ccc'></div>"
            html_body = body.strip()
            html_signature = f"<div style='color: #666; font-size: 0.9em; border-top: 1px solid #ccc'>{signature.strip()}</div>"
            html_email = f"<pre>{html_header}\n{html_body}\n\n{html_signature}</pre>"
            msg.attach(MIMEText(html_email, "html"))

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logging.info(f"Email notification sent to {recipient}")
            return True

        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False

    def notify_job_added(
        self,
        recipient: str,
        job_id: str,
        script: str,
    ) -> None:
        """Notify when job is added to the queue"""
        subject = f"Job {job_id} Added"
        body = self.generate_email_body(
            job_type="added", job_id=job_id, script=script, pid="N/A"
        )
        self.send_email(recipient, subject, body)

    def notify_job_start(
        self, recipient: str, job_id: str, script: str, pid: str
    ) -> None:
        """Notify when job starts"""
        subject = f"Job {job_id} Started"
        body = self.generate_email_body(
            job_type="started", job_id=job_id, script=script, pid=pid
        )
        started_time = self.get_time_str()
        body += f"\nStarted at: {started_time}"
        self.send_email(recipient, subject, body)

    def notify_job_complete(
        self,
        recipient: str,
        job_id: str,
        script: str,
        pid: str,
    ) -> None:
        """Notify when job completes successfully"""
        subject = f"Job {job_id} Completed"
        body = self.generate_email_body(
            job_type="completed", job_id=job_id, script=script, pid=pid
        )
        completed_time = self.get_time_str()
        body += f"\nCompleted at: {completed_time}"
        self.send_email(recipient, subject, body)

    def notify_job_failed(
        self, recipient: str, job_id: str, script: str, pid: str, error: str
    ) -> None:
        """Notify when job fails"""
        subject = f"Job {job_id} Failed"
        body = self.generate_email_body(
            job_type="failed", job_id=job_id, script=script, pid=pid
        )
        error_time = self.get_time_str()
        body += f"\nFailed at: {error_time}"
        body += f"\nError: {error}"
        self.send_email(recipient, subject, body)

    @staticmethod
    def get_time_str() -> str:
        """Get current time as string"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_header(self, html: bool = False) -> str:
        """Generate header"""
        if html:
            divider = '<div style="color: #999; font-size: 0.9em; border-top: 1px dashed #ccc"></div>'
            header = [
                # divider,
                '<span style="font-size: 1.5em; font-weight: bold;">SQL Job Scheduler Notification System</span>',
                divider,
            ]
            header = "".join(header)
        else:
            bar = "#" * 100
            header = ["SQL Job Scheduler Notification Utility", bar.strip()]
            header = f"{bar}\n" + "\n".join(header)

        header = header.strip()

        if self.server_address is not None or self.dashboard_url is not None:
            header += "\nServer URLs:"

        if self.server_address is not None:
            if html:
                header += f"\nServer Address (for WIKI): <a href='{self.server_address}'>{self.server_address}</a>"
            else:
                header += f"\nServer Address (for WIKI): {self.server_address}"
        if self.dashboard_url is not None:
            header += f"\nDashboard URL: {self.dashboard_url}"

        return header

    def generate_email_body(
        self, job_type: str, job_id: str, script: str, pid: str
    ) -> str:
        """Generate email body"""
        body2generate = (
            f"Your job has {job_type}.\nJob ID: {job_id}\nScript: {script}\nPID: {pid}"
        )
        # body = self.generate_header() + "\n\n" + body2generate
        body = body2generate
        return body

    @staticmethod
    def generate_email_credentials_json(
        server_address: str | None = None, dashboard_url: str | None = None
    ):
        """Generate email credentials JSON file"""

        def check_bewteen_colon_slash(url: str) -> bool:
            """Check if url is between colon, slash, and slash"""
            import re

            pattern = r":\d+/"
            return re.search(pattern, url) is not None

        credentials_manager = CredentialsManager()

        print(
            "Utility to generate email credentials for SQL Job Scheduler email notifier"
        )
        print("Note: For Gmail, use an App Password from Google Account settings\n")

        while True:
            email_address = input("Enter your email address (gmail only): ")
            if "@" not in email_address or not email_address.endswith("gmail.com"):
                print(
                    f"{email_address} is not a valid gmail address. Please try again."
                )
            else:
                break

        while True:
            email_password = getpass.getpass(
                "Enter your email app password (THIS IS NOT YOUR EMAIL PASSWORD): "
            )
            email_password = email_password.replace(" ", "")
            if len(email_password) == 16:
                break
            else:
                print("App password must be 16 characters long. Please try again.")

        if server_address is None:
            server_address = input(
                "Enter your server address (Hit Enter for default which will leave it blank): "
            )

        if server_address == "":
            server_address = None

        if server_address is not None and dashboard_url is None:
            while True:
                dashboard_url = input(
                    f"Enter your dashboard URL (Hit Enter for default which will leave it blank. For proper entry, enter url as: {server_address}:PORT/APP_NAME).\nNote: This is for a streamlit app: "
                )
                if dashboard_url == "":
                    dashboard_url = None
                    break
                elif not dashboard_url.startswith(server_address):
                    print(
                        f"Dashboard URL must start with {server_address}. Please try again."
                    )
                elif not check_bewteen_colon_slash(dashboard_url):
                    print(
                        f"Dashboard URL must be in the format: {server_address}:PORT/APP_NAME. Please try again."
                    )
                else:
                    break

        credentials_manager.encrypt_credentials(
            {
                "email": email_address,
                "password": email_password,
                "server_address": server_address,
                "dashboard_url": dashboard_url,
            }
        )
        print(
            f"Email credentials saved to {credentials_manager.credentials_file}.\nGeneration complete."
        )


class CredentialsManager:
    def __init__(self):
        home_dir = Path.home()
        self.credentials_dir = home_dir / ".sqljobscheduler" / "Credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.username = getpass.getuser()

        # Generate consistent user code
        self.user_code = hashlib.md5(self.username.encode()).hexdigest()[:8]

        # Use code in filenames
        self.credentials_file = self.credentials_dir / f"email_{self.user_code}.json"
        self.key_file = self.credentials_dir / f".key_{self.user_code}"

    def generate_key(self):
        """Generate encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"sqljobscheduler",
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"sqljobscheduler"))
        return key

    def encrypt_credentials(self, data: dict) -> None:
        """Encrypt and save credentials"""
        # Create directory with restricted permissions
        self.credentials_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Generate and save key
        key = self.generate_key()
        self.key_file.write_bytes(key)
        os.chmod(self.key_file, 0o600)  # Read/write for owner only

        # Encrypt data
        f = Fernet(key)
        encrypted_data = f.encrypt(json.dumps(data).encode())

        # Save encrypted data
        self.credentials_file.write_bytes(encrypted_data)
        os.chmod(self.credentials_file, 0o600)

    def decrypt_credentials(self) -> dict:
        """Decrypt and return credentials"""
        if not self.credentials_file.exists() or not self.key_file.exists():
            raise FileNotFoundError("Credentials or key file not found")

        # Load key and decrypt
        key = self.key_file.read_bytes()
        f = Fernet(key)
        encrypted_data = self.credentials_file.read_bytes()
        decrypted_data = f.decrypt(encrypted_data)

        return json.loads(decrypted_data)


if __name__ == "__main__":
    EmailNotifier.generate_email_credentials_json()
