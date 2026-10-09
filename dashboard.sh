#!/bin/bash
# dashboard.sh — startar dashboarden på http://127.0.0.1:4771 och öppnar den i webbläsaren. Ctrl-C stoppar.
#   ./dashboard.sh arbetsyta [kund]   öppnar arbetsytan (kunskap/arbetsyta.md), för kunden när den anges
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
PORT="${NWP_DASHBOARD_PORT:-4771}"
URL="http://127.0.0.1:$PORT"
TILL=""
if [ "${1:-}" = "arbetsyta" ]; then
  if [ -n "${2:-}" ] && ! [[ "$2" =~ ^[a-z0-9-]{2,60}$ ]]; then echo "okänd kund: $2" >&2; exit 2; fi
  TILL="&till=arbetsyta${2:+/$2}"
fi
# Dashboardnyckeln: skrivande anrop (ägarens domar, flödets handlingar) kräver den, och bara ägarens webbläsare får den, i
# adressens fragment (dashboard/server.py NYCKEL). Kör dashboarden redan läses nyckeln ur filen servern skrev (0600).
NYCKELFIL="$HOME/.nortropic-hemligheter/webb-pro/dashboard-nyckel"
# utanför huvudutcheckningen skriver server.py nyckeln i kunder/.dashboard-nyckel (kunskap/arbetsyta.md, Prov)
[ "$ROOT" = "$(cd "$HOME/nortropic-repos/nortropic-webb-pro" 2>/dev/null && pwd -P)" ] || NYCKELFIL="$ROOT/kunder/.dashboard-nyckel"
if curl -fs -o /dev/null "$URL/api/oversikt"; then
  NYCKEL="$(cat "$NYCKELFIL" 2>/dev/null | tr -d '[:space:]')"
  open "$URL/#nyckel=$NYCKEL$TILL"; echo "Dashboarden kör redan: $URL"; exit 0
fi
NYCKEL="$("$ROOT/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(24))')"
(sleep 1; open "$URL/#nyckel=$NYCKEL$TILL") &
NWP_DASHBOARD_NYCKEL="$NYCKEL" exec "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT"
