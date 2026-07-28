#!/bin/bash
# run_dev.sh — Manage the dev environment: Schwab sync + Flask backend + Vite frontend
#
# Usage:
#   ./run_dev.sh start     Sync Schwab API, start backend + frontend in the background, open the browser
#   ./run_dev.sh stop      Stop the backend and frontend
#   ./run_dev.sh restart   Stop, then start (sync runs again as part of start)
#   ./run_dev.sh status    Show whether the backend and frontend are running
#
# Running with no argument (or an unrecognized one) prints this usage and exits 1 —
# there is no default command.
#
# start detaches immediately — the servers keep running after the terminal closes.
# Logs are written to .run/backend.log, .run/frontend.log and .run/schwab_sync.log.
# On each start, empty log files and gzipped logs older than 90 days are pruned
# from logs/ and .run/.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${SCRIPT_DIR}/.run"
BACKEND_PID_FILE="${RUN_DIR}/backend.pid"
FRONTEND_PID_FILE="${RUN_DIR}/frontend.pid"
BACKEND_LOG="${RUN_DIR}/backend.log"
FRONTEND_LOG="${RUN_DIR}/frontend.log"
SYNC_LOG="${RUN_DIR}/schwab_sync.log"
APP_LOG_DIR="${SCRIPT_DIR}/logs"
BACKEND_PORT=5000
FRONTEND_PORT=5173
BACKEND_URL="http://localhost:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

mkdir -p "$RUN_DIR"

cleanup_logs() {
    # Prune old log artifacts: empty files and gzipped rotations older than
    # 90 days. Scoped to the log directories only — running these finds from
    # the project root would delete the (legitimately empty) __init__.py files.
    local dir
    for dir in "$APP_LOG_DIR" "$RUN_DIR"; do
        [ -d "$dir" ] || continue
        find "$dir" -type f -size 0 -print -delete 2>/dev/null \
            | sed 's/^/  removed empty: /'
        find "$dir" -type f -name "*.gz" -mtime +90 -print -delete 2>/dev/null \
            | sed 's/^/  removed old archive: /'
    done
}

is_running() {
    # $1 = pid file. Cleans up the pid file if the process is gone.
    [ -f "$1" ] || return 1
    local pid
    pid="$(cat "$1" 2>/dev/null)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    rm -f "$1"
    return 1
}

is_port_listening() {
    ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":$1\$"
}

status_for() {
    local label="$1" pidfile="$2" port="$3"
    if is_running "$pidfile"; then
        local pid
        pid="$(cat "$pidfile")"
        if is_port_listening "$port"; then
            printf "  %-10s \033[0;32mrunning\033[0m   (pid %s, port %s)\n" "$label" "$pid" "$port"
        else
            printf "  %-10s \033[0;33mstarting\033[0m  (pid %s, port %s not listening yet)\n" "$label" "$pid" "$port"
        fi
    else
        printf "  %-10s \033[0;90mstopped\033[0m\n" "$label"
    fi
}

cmd_status() {
    printf "\033[1m[dev] Status:\033[0m\n"
    status_for "Backend" "$BACKEND_PID_FILE" "$BACKEND_PORT"
    status_for "Frontend" "$FRONTEND_PID_FILE" "$FRONTEND_PORT"
}

stop_one() {
    # $1 = label, $2 = pid file. Each process was started via setsid, so its
    # PID is also its process group ID — killing the negative PID takes down
    # the whole tree (e.g. Vite's child processes), not just the wrapper.
    local label="$1" pidfile="$2"
    if ! is_running "$pidfile"; then
        printf "\033[1m[dev]\033[0m %s is not running.\n" "$label"
        return
    fi
    local pid
    pid="$(cat "$pidfile")"
    printf "\033[1m[dev]\033[0m Stopping %s (pid %s)...\n" "$label" "$pid"
    kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null

    for _ in $(seq 1 25); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 0.2
    done

    if kill -0 "$pid" 2>/dev/null; then
        printf "\033[1m[dev]\033[0m %s did not stop in time — sending SIGKILL...\n" "$label"
        kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null
    fi
    rm -f "$pidfile"
}

cmd_stop() {
    stop_one "Backend" "$BACKEND_PID_FILE"
    stop_one "Frontend" "$FRONTEND_PID_FILE"
    printf "\033[1m[dev]\033[0m Done.\n"
}

cmd_help() {
    printf "Usage: %s {start|stop|restart|status}\n\n" "$0"
    printf "  start     Sync Schwab API, start backend + frontend in the background, open the browser\n"
    printf "  stop      Stop the backend and frontend\n"
    printf "  restart   Stop, then start (sync runs again as part of start)\n"
    printf "  status    Show whether the backend and frontend are running\n"
}

cmd_start() {
    if is_running "$BACKEND_PID_FILE" || is_running "$FRONTEND_PID_FILE"; then
        printf "\033[1m[dev]\033[0m Already running:\n"
        cmd_status
        printf "\nRun \033[1m./run_dev.sh restart\033[0m if you want to restart.\n"
        exit 1
    fi

    export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

    printf "\033[1m[dev]\033[0m Cleaning up old logs...\n"
    cleanup_logs

    # Pull the latest transactions from the Schwab API before starting the servers.
    # Startup continues even if the sync fails (e.g. offline, token expired).
    if [ -f "${SCRIPT_DIR}/data/schwab_token.json" ]; then
        printf "\033[1m[dev]\033[0m Syncing latest Schwab transactions... (log: .run/schwab_sync.log)\n"
        printf '===== sync started %s =====\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$SYNC_LOG"
        python "${SCRIPT_DIR}/bin/sync_schwab_api.py" 2>&1 \
            | tee -a "$SYNC_LOG" \
            | awk '{ print "\033[0;35m[schwab]  \033[0m" $0; fflush() }'
        # Pipeline exit status is awk's, so check the python stage explicitly.
        if [ "${PIPESTATUS[0]}" -ne 0 ]; then
            printf "\033[1m[dev]\033[0m Schwab sync failed — continuing with existing data.\n"
        fi
    else
        printf "\033[1m[dev]\033[0m No Schwab token — run \033[1mpython bin/schwab_login.py\033[0m once to enable API sync.\n"
    fi

    # setsid makes each process its own session/group leader (PID == PGID),
    # so `stop` can later kill the whole tree by PID from any terminal.
    printf "\033[1m[dev]\033[0m Backend  → %s (log: .run/backend.log)\n" "$BACKEND_URL"
    setsid flask --app "${SCRIPT_DIR}/trading.py" --debug run -h localhost -p "$BACKEND_PORT" \
        > "$BACKEND_LOG" 2>&1 < /dev/null &
    echo $! > "$BACKEND_PID_FILE"
    disown

    printf "\033[1m[dev]\033[0m Frontend → %s (log: .run/frontend.log)\n" "$FRONTEND_URL"
    setsid bash -c "cd '${SCRIPT_DIR}/frontend' && exec pnpm dev" \
        > "$FRONTEND_LOG" 2>&1 < /dev/null &
    echo $! > "$FRONTEND_PID_FILE"
    disown

    printf "\n  \033[1mApp:\033[0m %s\n" "$FRONTEND_URL"
    printf "  \033[1m./run_dev.sh status\033[0m to check, \033[1m./run_dev.sh stop\033[0m to stop.\n\n"

    (sleep 2 && xdg-open "${FRONTEND_URL}/dashboard" >/dev/null 2>&1) &
    disown
}

cmd_restart() {
    cmd_stop
    cmd_start
}

case "${1:-}" in
    start) cmd_start ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    status) cmd_status ;;
    "")
        cmd_help
        exit 1
        ;;
    *)
        printf "\033[1m[dev]\033[0m Unknown option: %s\n\n" "$1"
        cmd_help
        exit 1
        ;;
esac
