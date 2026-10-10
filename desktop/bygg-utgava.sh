#!/bin/bash
# bygg-utgava.sh — bygger en signerad utgåva av Nortropic.app som motorn i den här utcheckningen serverar till appen
# (kunskap/desktop.md, Uppdatering). Artefakten (tar.gz av appen) signeras med minisign-nyckeln i hemlighetsmappen och
# signaturen binds till versionen i tauri.conf.json. Inget laddas upp någonstans; utgåvan ligger i desktop/utgava/
# (utanför git) och appen prövar signaturen med sin inbyggda publika nyckel före installation.
#   desktop/bygg-utgava.sh "Kort beskrivning av ändringen"
set -euo pipefail
DESKTOP="$(cd "$(dirname "$0")" && pwd -P)"
NYCKEL="$HOME/.nortropic-hemligheter/webb-pro/desktop-uppdatering.key"
[ -f "$NYCKEL" ] || { echo "signeringsnyckeln saknas: $NYCKEL (npx tauri signer generate -w <fil>, se kunskap/desktop.md)" >&2; exit 2; }
export PATH="$HOME/.cargo/bin:$PATH"
VERSION="$(/usr/bin/python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["version"])' "$DESKTOP/src-tauri/tauri.conf.json")"
cd "$DESKTOP"
npm ci --ignore-scripts --no-audit --no-fund >/dev/null
npx tauri build --bundles app
UT="$DESKTOP/utgava"; mkdir -p "$UT"; rm -f "$UT"/Nortropic.app.tar.gz "$UT"/Nortropic.app.tar.gz.sig "$UT"/utgava.json
COPYFILE_DISABLE=1 /usr/bin/tar -czf "$UT/Nortropic.app.tar.gz" -C "$DESKTOP/src-tauri/target/release/bundle/macos" Nortropic.app
npx tauri signer sign -f "$NYCKEL" -p "" --app-version "$VERSION" "$UT/Nortropic.app.tar.gz" >/dev/null
/usr/bin/python3 - "$UT" "$VERSION" "${1:-}" "$(git -C "$DESKTOP" rev-parse HEAD)" <<'PY'
import json, sys, time
from pathlib import Path
ut, version, noter, commit = sys.argv[1:5]
Path(ut, 'utgava.json').write_text(json.dumps({'version': version, 'kontrakt': 'desktop/1', 'noter': noter, 'commit': commit,
                                               'byggd': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, ensure_ascii=False, indent=1))
PY
echo "utgåva $VERSION i $UT (signerad; appen hittar den under Nortropic → Sök efter uppdatering)"
