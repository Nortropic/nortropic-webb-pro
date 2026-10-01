#!/bin/bash
# dashboard.sh — startar dashboarden på http://127.0.0.1:4771 och öppnar den i webbläsaren. Ctrl-C stoppar.
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${NWP_DASHBOARD_PORT:-4771}"
URL="http://127.0.0.1:$PORT"
if curl -fs -o /dev/null "$URL/api/oversikt"; then open "$URL"; echo "Dashboarden kör redan: $URL"; exit 0; fi
(sleep 1; open "$URL") &
exec "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT"
