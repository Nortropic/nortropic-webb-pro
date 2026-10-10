#!/bin/bash
# installera.sh — bygger Nortropic.app (release) och installerar den i ~/Applications, utan administratörsrätt
# (kunskap/desktop.md, Starta, installera och bygga). Appens data i ~/Library/Application Support/se.nortropic.desktop/
# och kundernas underlag i motorn berörs inte. En körande Nortropic avslutas först (motorn och dess arbete fortsätter).
#   desktop/installera.sh            bygger och installerar
#   desktop/installera.sh --utan-bygge   installerar den senast byggda releasen
set -euo pipefail
DESKTOP="$(cd "$(dirname "$0")" && pwd -P)"
APP="$DESKTOP/src-tauri/target/release/bundle/macos/Nortropic.app"
MAL="$HOME/Applications/Nortropic.app"
if [ "${1:-}" != "--utan-bygge" ]; then
  command -v cargo >/dev/null 2>&1 || [ -x "$HOME/.cargo/bin/cargo" ] || { echo "Rust saknas: installera med rustup (användarnivå), se kunskap/desktop.md" >&2; exit 2; }
  export PATH="$HOME/.cargo/bin:$PATH"
  ( cd "$DESKTOP" && npm ci --ignore-scripts --no-audit --no-fund >/dev/null && npx tauri build --bundles app,dmg )
fi
[ -d "$APP" ] || { echo "ingen byggd app i $APP" >&2; exit 1; }
if /usr/bin/pgrep -f "$MAL/Contents/MacOS/nortropic" >/dev/null 2>&1; then
  /usr/bin/osascript -e 'tell application id "se.nortropic.desktop" to quit' >/dev/null 2>&1 || true
  for _ in $(seq 1 20); do /usr/bin/pgrep -f "$MAL/Contents/MacOS/nortropic" >/dev/null 2>&1 || break; sleep 0.5; done
fi
mkdir -p "$HOME/Applications"
TMP="$HOME/Applications/.Nortropic.app.ny.$$"
rm -rf "$TMP"
/usr/bin/ditto "$APP" "$TMP"
if [ -d "$MAL" ]; then mv "$MAL" "$HOME/Applications/.Nortropic.app.forra.$$"; fi
mv "$TMP" "$MAL"
rm -rf "$HOME/Applications/.Nortropic.app.forra.$$"
echo "Nortropic.app installerad i $MAL ($(/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' "$MAL/Contents/Info.plist"))."
echo "Öppna den från Program eller Dock. Inställningarna och kunddata ligger kvar utanför appen."
