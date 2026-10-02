#!/usr/bin/env python3
"""ab.py — rättvis A/B-jämförelse av ett val i flödet: samma verksamhet byggs två gånger, en gång per värde, och
ägaren väljer blint i dashboardens vy Jämförelser vilken som är bäst. Tid, turer och granskarens betyg står bredvid
och visas först efter valet.

    .venv/bin/python kontroller/ab.py starta <slug> "<verksamhet>" [--variabel effort] [--a medium] [--b high]
    .venv/bin/python kontroller/ab.py lista

Variabler: effort (NWP_EFFORT), modell (NWP_MODELL), originalitet (NWP_GRANSKNING_ORIGINALITET: skugga, avgor).
Byggena heter <slug>-abx och <slug>-aby; vilket värde som hör till x och y lottas och sparas i kunder/ab/<id>.json,
som dashboarden döljer tills ägaren har valt. Syskonbygget räknas inte som tidigare bygge (upptagna val, granskaren),
så att det ena bygget inte påverkar det andra. Körningen tar två fulla byggen; starta den med nohup.
Källa: Anthropic, Prompting Claude Opus 5.5 (mät effort mot egna utvärderingar); OpenAI, Evaluation best practices
(parvis jämförelse är tillförlitligare än skalor).
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
AB = KUNDER / 'ab'
VARIABLER = {'effort': 'NWP_EFFORT', 'modell': 'NWP_MODELL', 'originalitet': 'NWP_GRANSKNING_ORIGINALITET'}
SLUG = re.compile(r'^[a-z0-9-]{2,52}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def matt(slug):
    """Tid och turer ur körningens logg och granskarens betyg, efter bygget."""
    k = KUNDER / slug
    loggar = sorted(k.glob('korning-*.jsonl'))
    resultat = {}
    if loggar:
        for rad in loggar[-1].read_text(encoding='utf-8', errors='replace').splitlines():
            if '"type":"result"' in rad.replace(' ', ''):
                try:
                    r = json.loads(rad)
                    resultat = {'turer': r.get('num_turns'), 'minuter': round((r.get('duration_ms') or 0) / 60000, 1)}
                except ValueError:
                    pass
    g = las(k / 'granskning' / 'GRANSKNING.json') or {}
    s = las(k / 'prov' / 'STATUS.json') or {}
    return {**resultat, 'provet_gront': s.get('ok'), 'granskning_godkand': g.get('godkand'),
            'betyg': {n: x.get('betyg') for n, x in (g.get('kriterier') or {}).items()},
            'omgangar': len(list((k / 'granskning').glob('runda-*'))) if (k / 'granskning').is_dir() else 0}


def starta(a):
    if not SLUG.match(a.slug):
        print('ogiltig slug (högst 52 tecken, a–z, 0–9, -)')
        return 2
    if a.variabel not in VARIABLER:
        print('variabel ska vara en av ' + ', '.join(VARIABLER))
        return 2
    AB.mkdir(parents=True, exist_ok=True)
    ident = 'ab-%s-%s' % (a.slug, datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    varden = [a.a, a.b]
    random.shuffle(varden)
    x, y = a.slug + '-abx', a.slug + '-aby'
    post = {'schema': 1, 'id': ident, 'verksamhet': a.verksamhet, 'variabel': a.variabel, 'varden': {x: varden[0], y: varden[1]},
            'byggen': [x, y], 'startad': nu(), 'status': 'bygger', 'val': None}
    fil = AB / (ident + '.json')
    fil.write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for slug, syskon in ((x, y), (y, x)):
        (KUNDER / slug).mkdir(parents=True, exist_ok=True)
        (KUNDER / slug / 'AB-SYSKON').write_text(syskon + '\n', encoding='utf-8')
    print('Jämförelse %s: %s mot %s, värdena lottade och dolda. Två byggen i följd.' % (ident, x, y), flush=True)
    for slug in (x, y):
        miljo = dict(os.environ, **{VARIABLER[a.variabel]: post['varden'][slug]})
        start = time.time()
        rc = subprocess.run([str(ROOT / 'kor.sh'), slug, a.verksamhet], env=miljo, cwd=str(ROOT)).returncode
        post = las(fil)
        post.setdefault('korningar', {})[slug] = {'rc': rc, 'sekunder': round(time.time() - start), **matt(slug)}
        fil.write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    post = las(fil)
    post['status'] = 'väntar på ägarens val'
    post['klar'] = nu()
    fil.write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Klar. Välj i dashboarden under Jämförelser.')
    return 0


def lista(_a):
    for f in sorted(AB.glob('ab-*.json')) if AB.is_dir() else []:
        p = las(f) or {}
        print('%s · %s · %s · %s' % (p.get('id'), p.get('variabel'), p.get('status'), ', '.join(p.get('byggen', []))))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog='ab', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='kommando', required=True)
    s = sub.add_parser('starta')
    s.add_argument('slug')
    s.add_argument('verksamhet')
    s.add_argument('--variabel', default='effort')
    s.add_argument('--a', default='medium')
    s.add_argument('--b', default='high')
    sub.add_parser('lista')
    a = p.parse_args(argv)
    return {'starta': starta, 'lista': lista}[a.kommando](a)


if __name__ == '__main__':
    sys.exit(main())
