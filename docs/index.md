# SQLJobScheduler

A SQL-based job scheduler system designed to manage GPU-intensive Python jobs for a server.

## Overview

- Job Queue Management: Uses SQLite to maintain a queue of Python jobs with their execution parameters, status, and metadata.
- Job Runner Service: A daemon process that:
    - Runs jobs sequentially using tmux sessions
    - Handles GPU resource allocation
    - Provides email notifications for job status
    - Manages conda/Python environments for different jobs
- Web Dashboard: A FastAPI-based interface that displays:
    - Current GPU status
    - Job queue with filtering options
    - Real-time job output
    - GPU usage timeline
- System Integration: Runs as a systemd service on Linux, with proper user permissions and environment management

## Quick Navigation

- [Installation](01_installation.md)
- [API](02_api_usage.md)
- [JobRunner](03_jobrunner.md)
- [Dashboard](04_joblister.md)
