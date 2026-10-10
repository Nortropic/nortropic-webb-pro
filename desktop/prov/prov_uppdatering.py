#!/usr/bin/env python3
"""Uppdateringens prov (D23, J12; kunskap/desktop.md, Uppdatering) i den riktiga appen: en kopia av provbygget i en
provkatalog som heter Applications, en provinstans som serverar en signerad utgåva ur worktreens desktop/utgava/, och:

1. appen hittar den nyare utgåvan;
2. en manipulerad artefakt nekas (signaturen) och appen är oförändrad;
3. en signatur bunden till en annan version nekas och appen är oförändrad;
4. den giltiga utgåvan installeras: paketet byts, versionen är den nya, föregående version är sparad, och appen startar om.

    .venv/bin/python -B desktop/prov/prov_uppdatering.py --port 4791 --utgava <katalog med Nortropic.app i version 0.1.1> --ut <katalog>

Utgåvans app byggs före provet med `npx tauri build --bundles app --config '{"version":"0.1.1"}'` och kopieras till
--utgava; provet packar, signerar (nyckeln i hemlighetsmappen) och lägger den i desktop/utgava/.
"""
import argparse
import json
import plistlib
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import appdrivare as ad  # noqa: E402
from prov_app import VERKTYG  # noqa: E402

NYCKEL = Path.home() / '.nortropic-hemligheter/webb-pro/desktop-uppdatering.key'
UTGAVA = ad.DESKTOP / 'utgava'


def version(app):
    return plistlib.loads((Path(app) / 'Contents/Info.plist').read_bytes())['CFBundleShortVersionString']


def lagg_utgava(app, signerad_version, beskriven_version, manipulera=False):
    UTGAVA.mkdir(exist_ok=True)
    for f in UTGAVA.iterdir():
        f.unlink()
    tgz = UTGAVA / 'Nortropic.app.tar.gz'
    subprocess.run(['/usr/bin/tar', '-czf', str(tgz), '-C', str(Path(app).parent), 'Nortropic.app'], check=True, env={'COPYFILE_DISABLE': '1', 'PATH': '/usr/bin:/bin'})
    subprocess.run(['npx', 'tauri', 'signer', 'sign', '-f', str(NYCKEL), '-p', '', '--app-version', signerad_version, str(tgz)], cwd=ad.DESKTOP, check=True,
                   capture_output=True)
    if manipulera:
        with open(tgz, 'ab') as f:
            f.write(b'manipulerad')
    (UTGAVA / 'utgava.json').write_text(json.dumps({'version': beskriven_version, 'kontrakt': 'desktop/1', 'noter': 'provets utgåva'}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--utgava', required=True, help='katalog med Nortropic.app i den nya versionen')
    ap.add_argument('--ut', required=True)
    a_ = ap.parse_args()
    ny_app = Path(a_.utgava) / 'Nortropic.app'
    ny_v = version(ny_app)
    ut = Path(a_.ut)
    ut.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='nwp-desktop-uppd-'))
    progr = tmp / 'Applications'
    progr.mkdir()
    shutil.copytree(ad.PROVAPP, progr / 'Nortropic.app', symlinks=True)
    gammal_v = version(progr / 'Nortropic.app')
    res = {'gammal': gammal_v, 'ny': ny_v}
    a = ad.App(ad.ROT, a_.port, app=progr / 'Nortropic.app', data=tmp / 'data')
    a.registrera(VERKTYG)
    try:
        def sok_och_installera():
            a.meny('uppdatering')
            a.vanta(lambda: 'finns' in (a.js("document.getElementById('uppd-svar').textContent") or '') or 'senaste' in (a.js("document.getElementById('uppd-svar').textContent") or ''), tid=30, text='sökningen')
            text = a.js("document.getElementById('uppd-svar').textContent")
            if not a.js("!!document.getElementById('installera-uppd')"):
                return text, None
            a.js("document.getElementById('installera-uppd').click(), true")
            try:
                svar = a.vanta(lambda: (lambda t: t if t and not t.startswith('Hämtar') else None)(a.js("document.getElementById('uppd-svar').textContent")), tid=60, text='installationen')
            except Exception as e:  # noqa: BLE001 — appen kan ha avslutats för omstarten
                svar = 'appen avslutades (%s)' % type(e).__name__
            return text, svar

        a.starta()
        a.vanta(lambda: a.js("document.querySelector('[data-vy=last]') && !document.querySelector('[data-vy=last]').hidden"), text='låsvyn')
        a.js("document.getElementById('las-upp').click(), true")
        a.vanta(lambda: (a.lage().get('url') or '').startswith('http://127.0.0.1'), text='upplåst')
        # 2. manipulerad artefakt
        lagg_utgava(ny_app, ny_v, ny_v, manipulera=True)
        hittad, svar = sok_och_installera()
        res['manipulerad'] = {'hittad': hittad, 'svar': svar, 'appens_version_efter': version(progr / 'Nortropic.app')}
        assert 'signaturen stämmer inte' in (svar or ''), svar
        assert version(progr / 'Nortropic.app') == gammal_v
        # 3. signatur för en annan version
        lagg_utgava(ny_app, '9.9.9', ny_v)
        hittad, svar = sok_och_installera()
        res['fel_version'] = {'svar': svar, 'appens_version_efter': version(progr / 'Nortropic.app')}
        assert 'signaturen gäller version 9.9.9' in (svar or ''), svar
        assert version(progr / 'Nortropic.app') == gammal_v
        # 4. giltig utgåva
        lagg_utgava(ny_app, ny_v, ny_v)
        hittad, svar = sok_och_installera()
        a.proc.wait(30)
        time.sleep(3)
        res['giltig'] = {'hittad': hittad, 'svar': svar, 'appens_version_efter': version(progr / 'Nortropic.app'),
                         'forra_version_sparad': version(tmp / 'data' / 'forra-version' / 'Nortropic.app'), 'appen_avslutades_for_omstart': a.proc.returncode is not None}
        assert version(progr / 'Nortropic.app') == ny_v
        assert version(tmp / 'data' / 'forra-version' / 'Nortropic.app') == gammal_v
        omstartad = subprocess.run(['/usr/bin/pgrep', '-f', str(progr / 'Nortropic.app/Contents/MacOS/nortropic')], capture_output=True, text=True).stdout.split()
        res['giltig']['omstartad_process'] = omstartad
        res['utfall'] = 'godkänt'
    except AssertionError as e:
        res['utfall'] = 'underkänt: %s' % e
    finally:
        a.avsluta()
        for p in subprocess.run(['/usr/bin/pgrep', '-f', str(progr / 'Nortropic.app/Contents/MacOS/nortropic')], capture_output=True, text=True).stdout.split():
            subprocess.run(['/bin/kill', p])
        for f in UTGAVA.iterdir() if UTGAVA.exists() else []:
            f.unlink()
    (ut / 'uppdatering.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if res['utfall'] == 'godkänt' else 1


if __name__ == '__main__':
    sys.exit(main())
