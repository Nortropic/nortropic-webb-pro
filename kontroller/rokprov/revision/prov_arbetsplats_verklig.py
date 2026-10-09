#!/usr/bin/env python3
"""prov_arbetsplats_verklig.py — användarresan i arbetsytan med verkliga sessioner, i en provinstans med fiktivt material
(ägarens uppdrag 2026-10-09 om den kompletta arbetsplatsen, punkt 11; kunskap/arbetsyta.md, Prov).

Förbereder och kör provet, aldrig i huvudutcheckningen:
1. testprojektet (arbetsyta_fixtur.py) i rotens underlag/ och kunder/, kundens grundprojekt ur mallen (ny_sajt.py
   --installera) och kandidaten fotograferad av motorns egen fotografering (kandidater.py --fotografera);
2. en granskarnyckel för provets externa granskare i en egen katalog (NWP_GRANSKARE_NYCKLAR), aldrig hemlighetsmappen;
3. provinstansens dashboard ur roten på en egen port med en egen nyckel och de billiga modellerna i miljön, som
   arbetaren ärver (NWP_ATELJE_MODELL, NWP_KANDIDAT_GRANSKARE, frister);
4. webbläsarprovet prov_arbetsplats_verklig.mjs, som går användarresans nio punkter genom arbetsytan; sedan stoppas
   dashboarden och provets processer, och bevisen ligger i --ut.

    .venv/bin/python -B kontroller/rokprov/revision/prov_arbetsplats_verklig.py --rot <worktree> --ut <katalog> [--port 4784]

Kostar modellanrop (Haiku). Startar inget helbygge och publicerar inget: godkännandet lämnar över till helbygget utan
att starta det, och provet kontrollerar att inget bygge startade.
"""
import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HUVUD = (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve()
MODELL = 'claude-haiku-4-5-20251001'


def vanta_upp(bas, tak=30):
    slut = time.time() + tak
    while time.time() < slut:
        try:
            urllib.request.urlopen(bas + '/api/oversikt', timeout=3).read()
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    return False


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--rot', required=True)
    p.add_argument('--ut', required=True)
    p.add_argument('--port', type=int, default=4784)
    p.add_argument('--slug', default='testdata-anvandarresa')
    p.add_argument('--modell', default=MODELL)
    p.add_argument('--bara-forbered', action='store_true')
    a = p.parse_args(argv)
    rot, ut = Path(a.rot).resolve(), Path(a.ut).resolve()
    if rot == HUVUD:
        raise SystemExit('provet körs aldrig i huvudutcheckningen (%s)' % HUVUD)
    ut.mkdir(parents=True, exist_ok=True)
    py = str(rot / '.venv' / 'bin' / 'python')
    logg = open(ut / 'forberedelse.log', 'a')

    def kor(*args, **kw):
        logg.write('\n$ %s\n' % ' '.join(map(str, args)))
        logg.flush()
        r = subprocess.run(list(args), cwd=str(rot), stdout=logg, stderr=subprocess.STDOUT, **kw)
        if r.returncode:
            raise SystemExit('steget föll (%s): se %s' % (' '.join(map(str, args[:3])), ut / 'forberedelse.log'))
    # 1. testprojektet och motorns fotografering av kandidaten
    if not (rot / 'underlag' / a.slug).exists():
        kor(py, '-B', 'kontroller/rokprov/revision/arbetsyta_fixtur.py', str(rot), '--slug', a.slug)
    if not (rot / 'kunder' / a.slug / 'sajt' / 'package.json').is_file():  # kundens grundprojekt, som motorn kräver före en körning
        kor(py, '-B', 'kontroller/ny_sajt.py', a.slug, '--installera', timeout=900)
    kor(py, '-B', 'kontroller/kandidater.py', a.slug, '--fotografera', 'k01', timeout=900)
    # 2. provets granskarnyckel
    nycklar = ut / 'granskarnycklar'
    env = dict(os.environ, NWP_GRANSKARE_NYCKLAR=str(nycklar))
    kor(py, '-B', 'kontroller/extern_granskare.py', 'nyckel', 'codex', env=env)
    if a.bara_forbered:
        return 0
    # 3. provinstansen
    nyckel = secrets.token_urlsafe(24)
    (ut / 'provnyckel').write_text(nyckel + '\n')
    os.chmod(ut / 'provnyckel', 0o600)
    env.update({'NWP_DASHBOARD_NYCKEL': nyckel, 'NWP_ATELJE_MODELL': a.modell, 'NWP_ATELJE_EFFORT': 'low',
                'NWP_KANDIDAT_GRANSKARE': a.modell, 'NWP_KANDIDAT_FRIST_FORFINA': '1800', 'NWP_ATELJE_FRIST_FORFINA': '1800',
                'NWP_MEDDELANDEN': 'pa', 'NWP_LOPARE_RA': str(ut / 'strom')})
    (ut / 'strom').mkdir(exist_ok=True)
    bas = 'http://127.0.0.1:%d' % a.port
    srv = subprocess.Popen([py, '-B', 'dashboard/server.py', '--port', str(a.port)], cwd=str(rot), env=env,
                           stdout=open(ut / 'dashboard.log', 'ab'), stderr=subprocess.STDOUT, start_new_session=True)
    try:
        if not vanta_upp(bas):
            raise SystemExit('provinstansen svarade inte; se %s' % (ut / 'dashboard.log'))
        t0 = time.time()
        r = subprocess.run(['node', str(Path(__file__).with_name('prov_arbetsplats_verklig.mjs')), bas, nyckel, a.slug, str(rot), str(nycklar / 'codex.nyckel'),
                            str(ut)], cwd=str(rot), env=dict(os.environ, PLAYWRIGHT_BROWSERS_PATH=os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
                                                             or str(Path.home() / 'Library' / 'Caches' / 'ms-playwright')),
                           stdout=open(ut / 'webb.log', 'ab'), stderr=subprocess.STDOUT)
        print(json.dumps({'webbprov': r.returncode, 'sekunder': round(time.time() - t0), 'ut': str(ut)}))
        return r.returncode
    finally:
        try:  # arbetaren och dess sessioner stoppas genom flödets egen stoppväg innan dashboarden stängs
            subprocess.run([py, '-B', 'kontroller/prototyp.py', a.slug, '--stoppa'], cwd=str(rot), env=env, timeout=120,
                           stdout=logg, stderr=subprocess.STDOUT)
        except Exception:  # noqa: BLE001
            pass
        os.killpg(srv.pid, signal.SIGTERM)
        srv.wait(timeout=30)


if __name__ == '__main__':
    sys.exit(main())
