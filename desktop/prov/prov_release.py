#!/usr/bin/env python3
"""Användarbyggets negativa prov (kunskap/desktop.md, Prov; D22): den releasebyggda Nortropic.app har ingen
provinstrumentering. Ingen provsträng i binären, ingen datakatalog eller upplåsningsattrapp ur miljön, och ingen
lyssnande provport när appen kör; rätt arkitektur för mål-Macen. Startar appen med provmiljön satt och kontrollerar att
den inte lyssnar och inte skriver någon provstyrning.

    .venv/bin/python -B desktop/prov/prov_release.py [--app desktop/src-tauri/target/release/bundle/macos/Nortropic.app]
"""
import argparse
import json
import os
import plistlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', default=str(DESKTOP / 'src-tauri/target/release/bundle/macos/Nortropic.app'))
    app = Path(ap.parse_args().app)
    binar = app / 'Contents/MacOS/nortropic'
    ut = {'app': str(app)}
    data = binar.read_bytes()
    for s in (b'nwp-provstyrning', b'NWP_DESKTOP_PROV_UPPLAS', b'NWP_DESKTOP_DATA', b'X-Prov-Token', b'provstyrning.json'):
        ut[s.decode()] = s in data
    arkiv = subprocess.run(['/usr/bin/lipo', '-archs', str(binar)], capture_output=True, text=True).stdout.strip()
    ut['arkitektur'] = arkiv
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    ut['bundle'] = {k: info.get(k) for k in ('CFBundleIdentifier', 'CFBundleShortVersionString', 'LSMinimumSystemVersion')}
    ut['signatur'] = subprocess.run(['/usr/bin/codesign', '-dv', str(app)], capture_output=True, text=True).stderr.strip().splitlines()[-3:]
    # starta med provmiljön satt: användarbygget ska varken läsa den eller lyssna
    with tempfile.TemporaryDirectory(prefix='nwp-desktop-release-') as d:
        env = {'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin', 'NWP_DESKTOP_DATA': d, 'NWP_DESKTOP_PROV_UPPLAS': '1'}
        p = subprocess.Popen([str(binar)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(4)
            lyssnar = subprocess.run(['/usr/sbin/lsof', '-nP', '-a', '-p', str(p.pid), '-iTCP', '-sTCP:LISTEN'], capture_output=True, text=True).stdout.strip()
            ut['lyssnande_portar'] = lyssnar.splitlines()[1:] if lyssnar else []
            ut['provstyrning_skriven'] = (Path(d) / 'provstyrning.json').exists()
            ut['provdatakatalog_använd'] = any(Path(d).iterdir())
        finally:
            p.terminate()
            p.wait(10)
    fel = [k for k in ('nwp-provstyrning', 'NWP_DESKTOP_PROV_UPPLAS', 'NWP_DESKTOP_DATA', 'X-Prov-Token', 'provstyrning.json') if ut[k]]
    fel += ['lyssnar'] if ut['lyssnande_portar'] else []
    fel += ['provstyrning'] if ut['provstyrning_skriven'] else []
    fel += ['provdata'] if ut['provdatakatalog_använd'] else []
    fel += ['arkitektur'] if 'arm64' not in arkiv else []
    ut['utfall'] = 'godkänt' if not fel else 'underkänt: ' + ', '.join(fel)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 1 if fel else 0


if __name__ == '__main__':
    sys.exit(main())
