# JobRunner Guide

This guide covers how to access and manage the JobRunner service, including its logs and tmux sessions.

## Accessing JobRunner Logs

Logs for the runner are stored `~/.sqljobscheduler/logs/job_runner`. If any issues related to tmux operations are run into within the analysis of a job are stored in `~/.sqljobscheduler/logs/tmux`.

## TMUX Session Access

The JobRunner runs in a tmux session with specific socket and server configurations:

```bash
# The socket is located at
/tmp/tmux-$(id -u)/JobRunner

# attach to session which stores job runner
tmux /tmp/tmux-$(id -u)/JobRunner attach -t JobRunner

# attach to specific job
tmux /tmp/tmux-$(id -u)/JobRunner attach -t job[NUM]
```

## Systemd Settings

Service can be found under the name `joblister.service`.
