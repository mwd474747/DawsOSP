#!/bin/bash
# Streamlit Process Management Script
# Ensures only one Streamlit instance runs at a time

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/dawsos/venv/bin/python3"
STREAMLIT="$PROJECT_ROOT/dawsos/venv/bin/streamlit"
PIDFILE="$PROJECT_ROOT/.streamlit.pid"

case "$1" in
    start)
        # Check if already running
        if [ -f "$PIDFILE" ]; then
            PID=$(cat "$PIDFILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "❌ Streamlit is already running (PID: $PID)"
                echo "   Access at: http://localhost:8501"
                exit 1
            else
                # Stale PID file
                rm "$PIDFILE"
            fi
        fi

        # Start Streamlit
        echo "🚀 Starting DawsOS Streamlit UI..."
        cd "$PROJECT_ROOT"
        nohup "$STREAMLIT" run dawsos/main.py --server.port=8501 --server.headless=true > streamlit.log 2>&1 &
        echo $! > "$PIDFILE"
        sleep 2

        if ps -p $(cat "$PIDFILE") > /dev/null 2>&1; then
            echo "✅ Streamlit started successfully (PID: $(cat "$PIDFILE"))"
            echo "   Access at: http://localhost:8501"
            echo "   Logs: $PROJECT_ROOT/streamlit.log"
        else
            echo "❌ Failed to start Streamlit"
            rm "$PIDFILE"
            exit 1
        fi
        ;;

    stop)
        if [ -f "$PIDFILE" ]; then
            PID=$(cat "$PIDFILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "🛑 Stopping Streamlit (PID: $PID)..."
                kill "$PID"
                sleep 1

                # Force kill if still running
                if ps -p "$PID" > /dev/null 2>&1; then
                    echo "   Force killing..."
                    kill -9 "$PID"
                fi

                rm "$PIDFILE"
                echo "✅ Streamlit stopped"
            else
                echo "⚠️  Streamlit not running (stale PID file)"
                rm "$PIDFILE"
            fi
        else
            echo "⚠️  No PID file found - attempting to kill any running Streamlit processes..."
            pkill -f "streamlit run dawsos/main.py" && echo "✅ Processes killed" || echo "❌ No processes found"
        fi
        ;;

    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;

    status)
        if [ -f "$PIDFILE" ]; then
            PID=$(cat "$PIDFILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Streamlit is running (PID: $PID)"
                echo "   Access at: http://localhost:8501"
                echo "   Logs: $PROJECT_ROOT/streamlit.log"

                # Show resource usage
                echo ""
                echo "Resource usage:"
                ps -p "$PID" -o pid,ppid,%cpu,%mem,vsz,rss,tty,stat,start,time,command
            else
                echo "❌ Streamlit not running (stale PID file)"
                rm "$PIDFILE"
                exit 1
            fi
        else
            echo "❌ Streamlit is not running"

            # Check for rogue processes
            ROGUE=$(pgrep -f "streamlit run dawsos/main.py")
            if [ -n "$ROGUE" ]; then
                echo "⚠️  Found rogue Streamlit processes: $ROGUE"
                echo "   Run: $0 cleanup"
            fi
            exit 1
        fi
        ;;

    cleanup)
        echo "🧹 Cleaning up all Streamlit processes..."
        pkill -9 -f "streamlit run" && echo "✅ Killed Streamlit processes" || echo "❌ No processes found"
        [ -f "$PIDFILE" ] && rm "$PIDFILE" && echo "✅ Removed PID file"
        [ -f "$PROJECT_ROOT/streamlit.log" ] && > "$PROJECT_ROOT/streamlit.log" && echo "✅ Cleared log file"
        echo "✅ Cleanup complete"
        ;;

    logs)
        if [ -f "$PROJECT_ROOT/streamlit.log" ]; then
            tail -f "$PROJECT_ROOT/streamlit.log"
        else
            echo "❌ No log file found"
            exit 1
        fi
        ;;

    *)
        echo "DawsOS Streamlit Process Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|cleanup|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start Streamlit server (single instance)"
        echo "  stop     - Stop running Streamlit server"
        echo "  restart  - Restart Streamlit server"
        echo "  status   - Check if Streamlit is running"
        echo "  cleanup  - Force kill all Streamlit processes"
        echo "  logs     - Tail Streamlit logs"
        exit 1
        ;;
esac
