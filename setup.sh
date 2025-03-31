#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if --email-only flag is passed
if [ "$1" == "--email-only" ]; then
  python "$SCRIPT_DIR/src/sqljobscheduler/EmailNotifier.py"
else
  # Run the full setup script
  python "$SCRIPT_DIR/src/sqljobscheduler/SetupSQLJS.py"
fi
