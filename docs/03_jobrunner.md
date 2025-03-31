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

## Job Output Display

The JobLister dashboard provides real-time display of currently running jobs through tmux session capture:

### Current Job Output

1. **Location**: The dashboard displays current job output in the "Current Job" section
2. **Source**: Output is captured from the tmux session of the currently running job
3. **Session Naming**: Each job runs in a tmux session named `job_XXXXX` where XXXXX is the zero-padded job ID
4. **Output Capture**: The dashboard uses tmux's `capture-pane` command to get the current output
5. **Storage**: Captured output is temporarily stored in `logs/tmux4WA/current_job`

### How It Works

1. The dashboard checks for currently running jobs using `check_gpu_lock_file()`
2. If a job is running:
   - For SQL-based jobs: Captures and displays the tmux output
   - For CLI jobs: Shows a warning that output cannot be displayed
3. The output is automatically refreshed when the dashboard is updated

### Limitations

- Only SQL-based jobs (jobs submitted through the system) can have their output displayed
- CLI jobs (run directly through the command line) cannot have their output captured
- Output is only available while the job is running
- The display is limited to the current tmux buffer size

### Troubleshooting

If you're not seeing job output in the dashboard:

1. Check if the job is SQL-based (not CLI)
2. Verify the job is currently running
3. Check the tmux session exists:

```bash
tmux -S /tmp/tmux-$(id -u)/gpuJobRunner ls | grep job_
```

4. Verify the tmux4WA directory exists and has proper permissions:

```bash
ls -l logs/tmux4WA
```
