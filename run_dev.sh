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

# Pull the latest transactions from the Schwab API before starting the servers.
# Startup continues even if the sync fails (e.g. offline, token expired).
if [ -f "${SCRIPT_DIR}/data/schwab_token.json" ]; then
    printf "\033[1m[dev]\033[0m Syncing latest Schwab transactions...\n"
    python "${SCRIPT_DIR}/bin/sync_schwab_api.py" 2>&1 \
        | awk '{ print "\033[0;35m[schwab]  \033[0m" $0; fflush() }' \
        || printf "\033[1m[dev]\033[0m Schwab sync failed — continuing with existing data.\n"
else
    printf "\033[1m[dev]\033[0m No Schwab token — run \033[1mpython bin/schwab_login.py\033[0m once to enable API sync.\n"
fi

printf "\033[1m[dev]\033[0m Backend  → %s\n" "$BACKEND_URL"
flask --app "${SCRIPT_DIR}/trading.py" --debug run -h localhost -p 5000 2>&1 \
    | awk '{ print "\033[0;33m[backend] \033[0m" $0; fflush() }' &

printf "\033[1m[dev]\033[0m Frontend → %s\n" "$FRONTEND_URL"
(cd "${SCRIPT_DIR}/frontend" && pnpm dev 2>&1) \
    | awk '{ print "\033[0;36m[frontend]\033[0m " $0; fflush() }' &

printf "\n  \033[1mApp:\033[0m %s\n" "$FRONTEND_URL"
printf "  Press \033[1mCtrl+C\033[0m to stop.\n\n"

# Open browser at the dashboard after servers have had time to start
(sleep 2 && xdg-open "${FRONTEND_URL}/dashboard" >/dev/null 2>&1) &

wait
