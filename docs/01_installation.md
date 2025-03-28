# Installation Guide

Can technically work with Windows, Mac, or Linux, but best to use with an Ubuntu-based OS with systemd and a NVIDIA GPU.

## Prerequisites

- Python 3.9 or higher
- [TMUX](https://github.com/tmux/tmux/wiki)

## Installation

For best results as a standalone application, it is recommended to install in a virtual environment. Best bet is to use [uv](https://github.com/astral-sh/uv) as environment and package manager for Python. Regardless, can also be installed as a package to be used in other projects.

```bash
# ensure python env is activated
# assuming uv is installed
source activate /path/to/python_env

# or if using anaconda
conda activate PYTHON_ENV_NAME

# install from github
pip install git+https://github.com/thicclatka/SQLJobScheduler.git

# if using uv
uv pip install git+https://github.com/thicclatka/SQLJobScheduler.git
```
