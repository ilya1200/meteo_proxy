#!/bin/bash

# Flask: Run with Gunicorn
# Based on .vscode/launch.json configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/run"
LOG_FILE="$LOG_DIR/gunicorn.log"
PID_FILE="$LOG_DIR/gunicorn.pid"

cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
if [ -d "$PROJECT_DIR/.venv" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
elif [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Environment variables
export FLASK_ENV=development
export REDIS_URL=redis://localhost:6379/0

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Server already running with PID $OLD_PID"
        echo "Use 'kill $OLD_PID' to stop it first"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

echo "Starting Gunicorn server..."
echo "Logging to: $LOG_FILE"

nohup "$PROJECT_DIR/.venv/bin/python" -m gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 1 \
    --reload \
    "weather_proxy.app:create_app()" \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_FILE"

echo "Server started with PID $PID"
echo "To stop: kill $PID"
echo "To view logs: tail -f $LOG_FILE"
