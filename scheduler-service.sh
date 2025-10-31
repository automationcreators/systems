#!/bin/bash
# Personal OS Scheduler Service Manager
# Manages the Python-based daily scheduler as a background service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SCHEDULER_SCRIPT="$SCRIPT_DIR/daily-scheduler.py"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LOG_FILE="$SCRIPT_DIR/scheduler.log"
SERVICE_LOG="$SCRIPT_DIR/scheduler-service.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SERVICE_LOG"
}

start_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "❌ Scheduler is already running (PID $PID)"
            return 1
        else
            echo "⚠️  Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    echo "🚀 Starting Daily Scheduler service..."
    log_message "Starting scheduler service"

    # Start scheduler in background
    cd "$BASE_DIR"
    nohup python3 "$SCHEDULER_SCRIPT" --action start >> "$SERVICE_LOG" 2>&1 &

    # Give it a moment to start
    sleep 2

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✅ Scheduler started successfully (PID $PID)"
            log_message "Scheduler started with PID $PID"
            echo ""
            echo "📊 Service Info:"
            echo "   PID: $PID"
            echo "   Log: $LOG_FILE"
            echo "   Service Log: $SERVICE_LOG"
            echo ""
            echo "💡 Useful commands:"
            echo "   Check status:  $0 status"
            echo "   Stop service:  $0 stop"
            echo "   View logs:     tail -f $LOG_FILE"
            return 0
        fi
    fi

    echo "❌ Failed to start scheduler"
    log_message "Failed to start scheduler"
    return 1
}

stop_service() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Scheduler is not running (no PID file)"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ! kill -0 "$PID" 2>/dev/null; then
        echo "❌ Scheduler process not found (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi

    echo "🛑 Stopping scheduler (PID $PID)..."
    log_message "Stopping scheduler PID $PID"

    kill -TERM "$PID"

    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            echo "✅ Scheduler stopped successfully"
            log_message "Scheduler stopped successfully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo "⚠️  Forcing scheduler to stop..."
    kill -KILL "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    log_message "Scheduler force-stopped"
    echo "✅ Scheduler stopped (forced)"
    return 0
}

restart_service() {
    echo "🔄 Restarting scheduler..."
    stop_service
    sleep 2
    start_service
}

status_service() {
    python3 "$SCHEDULER_SCRIPT" --action status

    echo ""
    echo "📝 Recent logs (last 10 lines):"
    if [ -f "$LOG_FILE" ]; then
        tail -10 "$LOG_FILE"
    else
        echo "   No logs yet"
    fi
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    run-morning)
        echo "🌅 Running morning tasks now..."
        python3 "$SCHEDULER_SCRIPT" --action run-now --task morning
        ;;
    run-evening)
        echo "🌙 Running evening tasks now..."
        python3 "$SCHEDULER_SCRIPT" --action run-now --task evening
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "❌ No log file found at $LOG_FILE"
        fi
        ;;
    *)
        echo "Personal OS Scheduler Service Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|run-morning|run-evening|logs}"
        echo ""
        echo "Commands:"
        echo "  start        - Start the scheduler service"
        echo "  stop         - Stop the scheduler service"
        echo "  restart      - Restart the scheduler service"
        echo "  status       - Show scheduler status and configuration"
        echo "  run-morning  - Run morning tasks immediately"
        echo "  run-evening  - Run evening tasks immediately"
        echo "  logs         - Tail the scheduler log file"
        echo ""
        exit 1
        ;;
esac
