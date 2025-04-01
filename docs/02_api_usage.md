# API Usage Guide

This guide covers the main API components of SQLJobScheduler, including email notifications and GPU management.

## Email Configuration

SQLJobScheduler supports email notifications for job status updates. It is best to run this as a CLI to have it set up before being used. Every file is made based on the user who runs the script.

1. Generate email credentials:

```bash
# Run the setup script which will prompt for email configuration
./setup.sh

# if you want to set up email credentials without running base set up
./setup.sh --email-only
```

2. The encrypted credentials file with its respective key will be created at `~/.sqljobscheduler/Credentials/` with the following structure:

```json
{
    "email": "your.email@example.com",
    "password": "your_app_specific_password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "server_address": "your.server.address",
    "dashboard_url": "http://your.server:port/app_name"
}
```

3. Using email notifications in your code:

```python
import os
from sqljobscheduler.EmailNotifier import EmailNotifier

# Initialize the notifier
notifier = EmailNotifier()

# notify job start
notifier.notify_job_start(
    recipient=job.email_address,
    job_id=job.id,
    script=job.programPath,
    pid=int(os.getpid()),
)

# notify job complete
notifier.notify_job_complete()
# notify job fail
notifier.notify_job_failed()
```

## GPU Management

SQLJobScheduler provides GPU locking functionality to prevent multiple jobs from using the same GPU simultaneously. This is implemented using lock files, which are stored in the system's temporary directory:

- Linux/Unix: `/tmp/gpu_lock.json`
- Windows: `C:\Users\<username>\AppData\Local\Temp\gpu_lock.json`
- macOS: `/var/folders/.../gpu_lock.json`

### Basic GPU Lock Usage

```python
import os
import getpass
from pathlib import Path
from sqljobscheduler import LockFileUtils

def main():
    # Check if GPU is available
    if not LockFileUtils.check_gpu_lock_file(

    ):
        print("Creating GPU lock file for this run")
        # inputting defaults
        LockFileUtils.create_gpu_lock_file(
            user=getpass.getuser(),
            script=Path(__file__).name,
            pid=int(os.getpid()),
            ctype="cli", # "cli" is default option
        )
    
    try:
        # Your GPU-intensive code here
        ...
    finally:
        # Always remove the lock file when done
        LockFileUtils.remove_gpu_lock_file()

if __name__ == "__main__":
    main()
```

### CLI vs running as a job from a job database

If you are running a script that handles non-SQL (CLI) or SQL-based executions, you need this line if you wish to adjust or modify based on those conditions:

```python
sql_parser = LockFileUtils.lock_file_argparser()
if not sql_parser.from_sql:
    # anything you want to do for CLI
if sql_parser.from_sql:
    # anything you want to do for SQL-based executions
```

### Best Practices

1. **Always Remove Lock Files**:
   - Use `try`/`finally` blocks to ensure lock files are removed
   - Call `LockFileUtils.remove_gpu_lock_file()` in the `finally` block

2. **Check GPU Availability**:
   - Use `LockFileUtils.check_gpu_lock_file()` before creating new locks
   - Consider using `gpu_lock_check_timer()` for timeouts

3. **Proper Lock File Creation**:
   - Include user information
   - Include script name
   - Include process ID
   - Specify client type ("cli" for command line)

4. **Command Line Integration**:
   - Use `LockFileUtils.lock_file_argparser()` for command line argument parsing
   - Handle SQL vs non-SQL execution paths appropriately
   - Use `parser.parse_known_args()` to handle both SQL and custom arguments:
