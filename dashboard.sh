#!/bin/bash
# dashboard.sh — startar dashboarden på http://127.0.0.1:4771 och öppnar arbetsytan i webbläsaren. Ctrl-C stoppar.
#   ./dashboard.sh arbetsyta [kund]   öppnar arbetsytan (kunskap/arbetsyta.md), för kunden när den anges
#   ./dashboard.sh start [kund]       startgenvägen: tjänsten i bakgrunden om den inte kör, sedan arbetsytan; startar
#                                     inga modellsessioner (Mac-appen Nortropic arbetsyta anropar den)
#   ./dashboard.sh genvag             skapar Mac-appen ~/Applications/Nortropic arbetsyta.app (engångsinstallation)
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
PORT="${NWP_DASHBOARD_PORT:-4771}"
URL="http://127.0.0.1:$PORT"
TILL=""
BAKGRUND=""
if [ "${1:-}" = "genvag" ]; then
  APP="$HOME/Applications/Nortropic arbetsyta.app"
  mkdir -p "$HOME/Applications"
  /usr/bin/osacompile -o "$APP" -e "do shell script quoted form of \"$ROOT/dashboard.sh\" & \" start > /dev/null 2>&1 &\"" || exit 1
  echo "Mac-appen finns i $APP (öppna den från Program eller Dock; den anropar $ROOT/dashboard.sh start)"; exit 0
fi
if [ "${1:-}" = "start" ]; then BAKGRUND=1; set -- arbetsyta "${2:-}"; fi
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
  [ -n "${NWP_UTAN_OPPNA:-}" ] || open "$URL/#nyckel=$NYCKEL$TILL"; echo "Dashboarden kör redan: $URL"; exit 0
fi
NYCKEL="$("$ROOT/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(24))')"
if [ -n "$BAKGRUND" ]; then  # startgenvägen: tjänsten lossad från terminalen, loggen i ~/Library/Logs; inget arbete startas
  mkdir -p "$HOME/Library/Logs"
  ( cd "$ROOT" && NWP_DASHBOARD_NYCKEL="$NYCKEL" nohup "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT" \
      >>"$HOME/Library/Logs/nortropic-dashboard.log" 2>&1 & )
  for _ in $(seq 1 30); do curl -fs -o /dev/null "$URL/api/oversikt" && break; sleep 0.5; done
  curl -fs -o /dev/null "$URL/api/oversikt" || { echo "dashboarden svarade inte; se ~/Library/Logs/nortropic-dashboard.log" >&2; exit 1; }
  [ -n "${NWP_UTAN_OPPNA:-}" ] || open "$URL/#nyckel=$NYCKEL$TILL"; echo "Dashboarden kör i bakgrunden: $URL"; exit 0
fi
(sleep 1; open "$URL/#nyckel=$NYCKEL$TILL") &
NWP_DASHBOARD_NYCKEL="$NYCKEL" exec "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT"
