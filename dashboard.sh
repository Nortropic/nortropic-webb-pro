#!/bin/bash
# dashboard.sh — startar dashboarden på http://127.0.0.1:4771 och öppnar arbetsytan i webbläsaren. Ctrl-C stoppar.
#   ./dashboard.sh arbetsyta [kund]   öppnar arbetsytan (kunskap/arbetsyta.md), för kunden när den anges
#   ./dashboard.sh start [kund]       startgenvägen: tjänsten i bakgrunden om den inte kör, sedan arbetsytan; startar
#                                     inga modellsessioner (Mac-appen Nortropic arbetsyta anropar den)
#   ./dashboard.sh genvag             skapar Mac-appen ~/Applications/Nortropic arbetsyta.app (engångsinstallation, bara
#                                     från huvudutcheckningen: appen pekar på den utcheckning där genvägen skapades)
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
HUVUD="$(cd "$HOME/nortropic-repos/nortropic-webb-pro" 2>/dev/null && pwd -P)"
PORT="${NWP_DASHBOARD_PORT:-4771}"
URL="http://127.0.0.1:$PORT"
TILL=""
BAKGRUND=""
if [ "${1:-}" = "genvag" ]; then
  if [ "$ROOT" != "$HUVUD" ] && [ -z "${NWP_GENVAG_HAR:-}" ]; then
    echo "genvägen skapas från huvudutcheckningen ($HUVUD); en worktree städas bort och appen skulle peka dit (NWP_GENVAG_HAR=1 skapar den ändå)" >&2
    exit 2
  fi
  APP="$HOME/Applications/Nortropic arbetsyta.app"
  mkdir -p "$HOME/Applications" "$HOME/Library/Logs"
  # AppleScript-strängen: bakstreck och citattecken i sökvägen skyddas. Appen kör genom inloggningsskalet (/bin/zsh -l),
  # så att claude, node och npm hittas som i terminalen; ett program från Finder har annars bara /usr/bin:/bin:/usr/sbin:/sbin.
  SKRIPT="${ROOT//\\/\\\\}/dashboard.sh"
  SKRIPT="${SKRIPT//\"/\\\"}"
  /usr/bin/osacompile -o "$APP" -e "do shell script \"/bin/zsh -lc \" & quoted form of (quoted form of \"$SKRIPT\" & \" start\") & \" >> \" & quoted form of (POSIX path of (path to home folder) & \"Library/Logs/nortropic-arbetsyta-app.log\") & \" 2>&1 &\"" || exit 1
  echo "Mac-appen finns i $APP (öppna den från Program eller Dock; den anropar $ROOT/dashboard.sh start, loggen i ~/Library/Logs/nortropic-arbetsyta-app.log)"; exit 0
fi
# Reserv när skriptet startats utan inloggningsskalets PATH: claude och node hämtas ur den (A12 i granskningen).
if ! command -v claude >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
  P="$(/bin/zsh -lc 'printf %s "$PATH"' 2>/dev/null)"
  [ -n "$P" ] && export PATH="$P:$PATH"
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
[ "$ROOT" = "$HUVUD" ] || NYCKELFIL="$ROOT/kunder/.dashboard-nyckel"
oppna_korande() {
  NYCKEL="$(cat "$NYCKELFIL" 2>/dev/null | tr -d '[:space:]')"
  [ -n "${NWP_UTAN_OPPNA:-}" ] || open "$URL/#nyckel=$NYCKEL$TILL"; echo "Dashboarden kör redan: $URL"; exit 0
}
if curl -fs -o /dev/null "$URL/api/oversikt"; then oppna_korande; fi
# En start åt gången (dubbelklick på appen): den andra väntar på den första och öppnar med dess nyckel.
LAS="${TMPDIR:-/tmp}/nortropic-dashboard-$PORT.start"
if ! mkdir "$LAS" 2>/dev/null; then
  for _ in $(seq 1 40); do curl -fs -o /dev/null "$URL/api/oversikt" && oppna_korande; sleep 0.5; done
  if [ -n "$(find "$LAS" -maxdepth 0 -mmin +2 2>/dev/null)" ]; then rmdir "$LAS" 2>/dev/null; mkdir "$LAS" 2>/dev/null || exit 1
  else echo "en annan start av dashboarden pågår; försök igen om en stund" >&2; exit 1; fi
fi
trap 'rmdir "$LAS" 2>/dev/null' EXIT
NYCKEL="$("$ROOT/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(24))')"
if [ -n "$BAKGRUND" ]; then  # startgenvägen: tjänsten lossad från terminalen, loggen i ~/Library/Logs; inget arbete startas
  mkdir -p "$HOME/Library/Logs"
  ( cd "$ROOT" && NWP_DASHBOARD_NYCKEL="$NYCKEL" nohup "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT" \
      >>"$HOME/Library/Logs/nortropic-dashboard.log" 2>&1 & )
  for _ in $(seq 1 30); do curl -fs -o /dev/null "$URL/api/oversikt" && break; sleep 0.5; done
  curl -fs -o /dev/null "$URL/api/oversikt" || { echo "dashboarden svarade inte; se ~/Library/Logs/nortropic-dashboard.log" >&2; exit 1; }
  [ -n "${NWP_UTAN_OPPNA:-}" ] || open "$URL/#nyckel=$NYCKEL$TILL"; echo "Dashboarden kör i bakgrunden: $URL"; exit 0
fi
trap - EXIT
(for _ in $(seq 1 30); do curl -fs -o /dev/null "$URL/api/oversikt" && break; sleep 0.5; done; rmdir "$LAS" 2>/dev/null
 [ -n "${NWP_UTAN_OPPNA:-}" ] || open "$URL/#nyckel=$NYCKEL$TILL") &
NWP_DASHBOARD_NYCKEL="$NYCKEL" exec "$ROOT/.venv/bin/python" -B "$ROOT/dashboard/server.py" --port "$PORT"
