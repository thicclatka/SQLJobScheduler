# Installation Guide

Can technically work as a library on Windows, Mac, or Linux. If you want to use as a standalone app, best to use with an Debian-based OS with systemd and a NVIDIA GPU.

## Prerequisites

- Python 3.9 or higher
- [TMUX](https://github.com/tmux/tmux/wiki) - For managing terminal sessions
- NVIDIA GPU (recommended for GPU-accelerated jobs)
- Systemd (for Linux service management)
- Gmail account (to enable email notifications)

## Installation

For best results as a standalone application, it is recommended to install in a virtual environment. It is recommended to use ***[uv](https://github.com/astral-sh/uv)*** as environment and package manager for Python. Regardless, can also be installed as a package to be used in other projects.

```bash
# Clone repository
git clone https://github.com/thicclatka/SQLJobScheduler.git
cd SQLJobScheduler

# if using uv
uv venv /path/to/env --python 3.12
source /path/to/env/bin/activate
uv pip install .

# if using conda
conda create -n ENV_NAME python=3.12
conda activate ENV_NAME
pip install .

# or installing as a library
# activate environment, as long as python version >= 3.9
pip install .
```

## Setup

To enable web app dashboard and background job runner for systemd, follow the steps above and then:

```bash
# be in desired venv
source /path/to/env/bin/activate

# make setup file executable
chmod +x setup.sh
# run setup
./setup.sh
```

During setup, you'll be prompted for:

- Username (with appropriate privileges)
- Group name (with appropriate privileges)
- Server IP address (if running remotely)
- Port number for the job lister
- App name (defaults to 'gpujobs')
- Email address to set up notifier (must be gmail)
- [Gmail App Password](https://support.google.com/mail/answer/185833?hl=en)

A message will be printed at the end with commands that can be copied to then enable and run the services. They should look something like this:

```bash
sudo cp /path/to/SQLJobScheduler/ServerService/services/*.service /etc/systemd/system/
sudo systemctl daemon-reload
chmod +x /path/to/SQLJobScheduler/ServerService/shell_scripts/start_jobrunner.sh
sudo systemctl enable gpuJobRunner
sudo systemctl start gpuJobRunner
sudo systemctl enable jobLister
sudo systemctl start jobLister
```

## Verification

To verify the installation:

```bash
sudo systemctl status [SERVICE-NAME] 
```

Access the web dashboard:

- Open a web browser
- Navigate to `http://<server_ip>:<port`
    - example: `http://localhost:8000`

## Uninstallation

To remove the services:

```bash
# Stop and disable services
sudo systemctl stop gpuJobRunner
sudo systemctl disable gpuJobRunner
sudo systemctl stop jobLister
sudo systemctl disable jobLister

# Remove service files
sudo rm /etc/systemd/system/gpuJobRunner.service
sudo rm /etc/systemd/system/jobLister.service

# Reload systemd
sudo systemctl daemon-reload
```
