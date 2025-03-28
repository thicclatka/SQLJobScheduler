#!/bin/bash
# Environment variables
ENVSDRIVE="/mnt/EnvsDrive"
PYTHON_EXEC="$ENVSDRIVE/uv_pyenvs/SQLJS_env/bin/python"
SCRIPT_PATH="$ENVSDRIVE/scripts_dev/SQLJobScheduler/src/sqljobscheduler/JobRunner.py"
# ZSHRC="$ENVSDRIVE/scripts_dev/SQLJobScheduler/ServerService/zshrc4jobrunner"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    logger -t gpuJobRunner "$1"
}

SLEEP() {
    SLEEP_TIME=0.1
    sleep $SLEEP_TIME
}

TMUX=/usr/bin/tmux
TMUX_SOCKET_DIR="/tmp/tmux-$(id -u)"
JRSESSION="JobRunner"
TMSESSION="TaskManager"
mkdir -p "$TMUX_SOCKET_DIR"
chmod 700 "$TMUX_SOCKET_DIR"

log "Starting JobRunner service..."
TMUX_SERVER_FILE="$TMUX_SOCKET_DIR/gpuJobRunner"

setup_JR() {
    $TMUX -S "$TMUX_SERVER_FILE" new-session -d -s "$JRSESSION"
}

setup_TM() {
    $TMUX -S "$TMUX_SERVER_FILE" new-session -d -s "$TMSESSION" "/usr/bin/btop"
    SLEEP
    $TMUX -S "$TMUX_SERVER_FILE" split-window -h -t "$TMSESSION" "/usr/bin/nvtop"
    SLEEP
}

setup_Scratchpad() {
    $TMUX -S "$TMUX_SERVER_FILE" new-session -d -s "Scratchpad"
    SLEEP
    $TMUX -S "$TMUX_SERVER_FILE" send-keys -t "Scratchpad" "cd $HOME && clear" Enter
    SLEEP
}

log "Checking if tmux server is running..."
# Check if tmux server is running, start if not
if ! $TMUX -S "$TMUX_SERVER_FILE" list-sessions >/dev/null 2>&1; then
    log "No tmux server found, starting..."
    $TMUX -S "$TMUX_SERVER_FILE" start-server
fi

# Check if the tmux session already exists
if $TMUX -S "$TMUX_SERVER_FILE" list-sessions | grep -q "$JRSESSION"; then
    log "JobRunner session already exists"
else
    # If the session does not exist, create it
    log "Creating JobRunner session..."
    setup_JR
    setup_TM
    setup_Scratchpad
fi

# Send the Python command to the tmux session
log "Sending Python command to JobRunner session..."
$TMUX -S "$TMUX_SERVER_FILE" send-keys -t "$JRSESSION" "$PYTHON_EXEC $SCRIPT_PATH" Enter

# simple check to see if the session is still running
while true; do
    if ! $TMUX -S "$TMUX_SERVER_FILE" list-sessions | grep -q "$JRSESSION"; then
        log "JobRunner session died, restarting..."
        setup_JR
    fi
    if ! $TMUX -S "$TMUX_SERVER_FILE" list-sessions | grep -q "$TMSESSION"; then
        log "TaskManager session died, restarting..."
        setup_TM
    fi
    if ! $TMUX -S "$TMUX_SERVER_FILE" list-sessions | grep -q "Scratchpad"; then
        log "Scratchpad session died, restarting..."
        setup_Scratchpad
    fi
    sleep 60
done
