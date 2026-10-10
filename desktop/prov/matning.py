#!/usr/bin/env python3
"""Appens resursmätning (D26; kunskap/desktop.md, Prov): kallstart från LaunchServices till synligt fönster, samlat
minne (appen och dess WebKit-processer) och CPU i vila, på den här Macen. Inga jämförelsesiffror mot andra ramverk.

    .venv/bin/python -B desktop/prov/matning.py [--app <Nortropic.app>] [--varv 3] [--vila 30]

Appen startas med `open` som från Finder och använder appens vanliga datakatalog (låst läge; ingen upplåsning).
WebKit-processerna (WebContent, Networking, GPU) är XPC-tjänster under launchd och räknas som de som startade efter appen.
"""
import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

DESKTOP = Path(__file__).resolve().parents[1]
FONSTER = Path(__file__).resolve().parent / 'fonster'


def processer():
    ut = {}
    for rad in subprocess.run(['/bin/ps', '-axo', 'pid=,rss=,%cpu=,comm='], capture_output=True, text=True).stdout.splitlines():
        f = rad.split(None, 3)
        if len(f) == 4:
            ut[int(f[0])] = {'rss_kb': int(f[1]), 'cpu': float(f[2]), 'namn': f[3]}
    return ut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', default=str(DESKTOP / 'src-tauri/target/release/bundle/macos/Nortropic.app'))
    ap.add_argument('--varv', type=int, default=3)
    ap.add_argument('--vila', type=int, default=30)
    a = ap.parse_args()
    app = Path(a.app)
    binar = str(app / 'Contents/MacOS/nortropic')
    starter = []
    sist = None
    for varv in range(a.varv):
        subprocess.run(['/usr/bin/pkill', '-f', binar])
        time.sleep(2)
        fore = set(processer())
        t0 = time.time()
        subprocess.run(['/usr/bin/open', str(app)], check=True)
        while time.time() - t0 < 30:
            rader = subprocess.run([str(FONSTER), 'Nortropic'], capture_output=True, text=True).stdout.splitlines()
            if any(r.split('\t')[2:4] == ['0', 'synlig'] for r in rader if len(r.split('\t')) > 3):
                break
            time.sleep(0.05)
        starter.append(round(time.time() - t0, 2))
        sist = fore
    time.sleep(5)
    pid = int(subprocess.run(['/usr/bin/pgrep', '-f', binar], capture_output=True, text=True).stdout.split()[0])
    nya = {p: v for p, v in processer().items() if p not in sist and ('WebKit' in v['namn'] or p == pid)}
    cpu_prov = []
    for _ in range(a.vila // 5):
        time.sleep(5)
        nu = processer()
        cpu_prov.append(round(sum(nu[p]['cpu'] for p in nya if p in nu), 2))
    nu = processer()
    minne = {nu[p]['namn'].split('/')[-1]: round(nu[p]['rss_kb'] / 1024, 1) for p in nya if p in nu}
    ut = {'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'mac': {'macos': platform.mac_ver()[0], 'arkitektur': platform.machine(),
          'modell': subprocess.run(['/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip(),
          'minne_gb': round(int(subprocess.run(['/usr/sbin/sysctl', '-n', 'hw.memsize'], capture_output=True, text=True).stdout) / 2**30)},
          'app': str(app), 'lage': 'låst (skalet), registrerad motor enligt appens inställningar',
          'kallstart_s': starter, 'kallstart_median_s': statistics.median(starter),
          'rss_mb_per_process': minne, 'rss_mb_summa': round(sum(minne.values()), 1),
          'cpu_procent_i_vila_var_5s': cpu_prov, 'cpu_procent_i_vila_median': statistics.median(cpu_prov) if cpu_prov else None,
          'not': 'RSS räknar delade sidor i varje process; summan är en övre gräns, inte en exakt footprint. CPU ur ps (%cpu, avklingande medel).'}
    subprocess.run(['/usr/bin/osascript', '-e', 'tell application id "se.nortropic.desktop" to quit'])
    print(json.dumps(ut, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
