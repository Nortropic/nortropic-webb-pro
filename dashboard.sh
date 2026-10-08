#!/bin/bash
# dashboard.sh — startar dashboarden på http://127.0.0.1:4771 och öppnar den i webbläsaren. Ctrl-C stoppar.
ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${NWP_DASHBOARD_PORT:-4771}"
URL="http://127.0.0.1:$PORT"
# Dashboardnyckeln: skrivande anrop (ägarens domar, flödets handlingar) kräver den, och bara ägarens webbläsare får den, i
# adressens fragment (dashboard/server.py NYCKEL). Kör dashboarden redan läses nyckeln ur filen servern skrev (0600).
NYCKELFIL="$HOME/.nortropic-hemligheter/webb-pro/dashboard-nyckel"
if curl -fs -o /dev/null "$URL/api/oversikt"; then
  NYCKEL="$(cat "$NYCKELFIL" 2>/dev/null | tr -d '[:space:]')"
  open "$URL/#nyckel=$NYCKEL"; echo "Dashboarden kör redan: $URL"; exit 0
fi
NYCKEL="$("$ROOT/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(24))')"
(sleep 1; open "$URL/#nyckel=$NYCKEL") &
NWP_DASHBOARD_NYCKEL="$NYCKEL" exec "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT"
