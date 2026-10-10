#!/bin/bash
# Avinstallerar Nortropic.app (kunskap/desktop.md, Avinstallera). Utan flagga listas bara det som skulle tas bort.
#   desktop/avinstallera.sh            torrkörning: listar appen och appens egna data
#   desktop/avinstallera.sh --app      tar bort appen (~/Applications eller /Applications), behåller inställningarna
#   desktop/avinstallera.sh --allt     tar bort appen och appens egna data (inställningar, webbvyns lagring, cachen,
#                                      föregående version efter en uppdatering)
# Motorn rörs aldrig: repot, underlag/, kunder/, dashboardens nyckel och körande arbete står kvar. Appen ska vara avslutad.
set -euo pipefail
ID=se.nortropic.desktop
LAGE=torr
case "${1:-}" in
  '') ;;
  --app) LAGE=app ;;
  --allt) LAGE=allt ;;
  *) echo "okänd flagga: $1 (--app eller --allt)" >&2; exit 2 ;;
esac
APPAR=()
for a in "$HOME/Applications/Nortropic.app" "/Applications/Nortropic.app"; do
  [ -d "$a" ] && [ "$(/usr/bin/defaults read "$a/Contents/Info" CFBundleIdentifier 2>/dev/null)" = "$ID" ] && APPAR+=("$a")
done
DATA=()
for d in "$HOME/Library/Application Support/$ID" "$HOME/Library/WebKit/$ID" "$HOME/Library/Caches/$ID" \
         "$HOME/Library/HTTPStorages/$ID" "$HOME/Library/Saved Application State/$ID.savedState" \
         "$HOME/Library/Preferences/$ID.plist" "$HOME/Library/Logs/$ID"; do
  [ -e "$d" ] && DATA+=("$d")
done
for a in "${APPAR[@]+"${APPAR[@]}"}"; do  # bara den app som avinstalleras räknas, inte ett provbygge någon annanstans
  if /usr/bin/pgrep -f "$a/Contents/MacOS/nortropic" >/dev/null 2>&1; then
    [ "$LAGE" = torr ] || { echo "Nortropic kör: avsluta appen först (Cmd-Q). Arbetet i motorn påverkas inte." >&2; exit 3; }
    echo "(Nortropic kör just nu; avsluta den före en riktig avinstallation.)"
  fi
done
echo "Appen:"; [ ${#APPAR[@]} -gt 0 ] && printf '  %s\n' "${APPAR[@]}" || echo "  (ingen installerad Nortropic.app hittades)"
echo "Appens egna data:"; [ ${#DATA[@]} -gt 0 ] && printf '  %s\n' "${DATA[@]}" || echo "  (inga)"
echo "Står kvar: motorn (repot, underlag/, kunder/), dashboardens nyckel och allt arbete i motorn."
case "$LAGE" in
  torr) echo "Torrkörning: inget togs bort. --app tar bort appen, --allt också appens egna data." ;;
  app) for a in "${APPAR[@]+"${APPAR[@]}"}"; do rm -rf "$a"; echo "borttagen: $a"; done ;;
  allt) for p in "${APPAR[@]+"${APPAR[@]}"}" "${DATA[@]+"${DATA[@]}"}"; do rm -rf "$p"; echo "borttagen: $p"; done ;;
esac
