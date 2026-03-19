#!/bin/bash
# run_dev.sh — Start Flask backend + Vite frontend for local development
# Usage: ./run_dev.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_URL="http://localhost:5173"
BACKEND_URL="http://localhost:5000"

cleanup() {
    trap - INT TERM EXIT
    printf "\n\033[1m[dev]\033[0m Stopping dev servers...\n"
    for pid in $(jobs -p 2>/dev/null); do
        kill -- -"$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    printf "\033[1m[dev]\033[0m Done.\n"
}
trap cleanup INT TERM EXIT

export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

printf "\033[1m[dev]\033[0m Backend  → %s\n" "$BACKEND_URL"
flask --app "${SCRIPT_DIR}/trading.py" --debug run -h localhost -p 5000 2>&1 \
    | awk '{ print "\033[0;33m[backend] \033[0m" $0; fflush() }' &

printf "\033[1m[dev]\033[0m Frontend → %s\n" "$FRONTEND_URL"
(cd "${SCRIPT_DIR}/frontend" && pnpm dev 2>&1) \
    | awk '{ print "\033[0;36m[frontend]\033[0m " $0; fflush() }' &

printf "\n  \033[1mApp:\033[0m %s\n" "$FRONTEND_URL"
printf "  Press \033[1mCtrl+C\033[0m to stop.\n\n"

# Open browser after servers have had time to start
(sleep 2 && xdg-open "${FRONTEND_URL}" >/dev/null 2>&1) &

wait
