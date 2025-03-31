# JobRunner Guide

This guide covers how to access and manage the JobRunner service, including its logs and tmux sessions.

## Accessing JobRunner Logs

The JobRunner service logs are managed through both systemd and tmux. Here's how to access them:

### Systemd Logs

```bash
# View real-time logs
sudo journalctl -u gpuJobRunner -f

# View logs since last boot
sudo journalctl -u gpuJobRunner -b

# View logs for a specific time period
sudo journalctl -u gpuJobRunner --since "1 hour ago" --until "now"
```

### TMUX Session Access

The JobRunner runs in a tmux session with specific socket and server configurations:

1. **TMUX Socket Location**:

```bash
# The socket is located at
/tmp/tmux-$(id -u)/gpuJobRunner
```

2. **List Available Sessions**:

```bash
# Using the specific socket
tmux -S /tmp/tmux-$(id -u)/gpuJobRunner ls
```

3. **Attach to the JobRunner Session**:

```bash
# Using the specific socket
tmux -S /tmp/tmux-$(id -u)/gpuJobRunner attach -t JobRunner
```

4. **Detach from Session**:

- Press `Ctrl + b` followed by `d` to detach
- The session will continue running in the background

## Logs

Logs for the runner are stored `logs/job_runner`. If any issues related to tmux operations are run into within the analysis of a job are stored in `logs/tmux`.
