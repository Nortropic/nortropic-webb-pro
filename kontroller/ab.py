#!/usr/bin/env python3
"""ab.py — rättvis A/B-jämförelse av ett val i flödet: samma verksamhet byggs två gånger, en gång per värde, och
ägaren väljer blint i dashboardens vy Jämförelser vilken som är bäst. Tid, turer och granskarens betyg står bredvid
och visas först efter valet.

    .venv/bin/python kontroller/ab.py starta <slug> "<verksamhet>" [--variabel effort] [--a medium] [--b high]
    .venv/bin/python kontroller/ab.py lista
    .venv/bin/python kontroller/ab.py hash <id>      # äldre jämförelse utan dist-hash: sätt den ur armarnas nuvarande dist

Variabler: effort (NWP_EFFORT), modell (NWP_MODELL), originalitet (NWP_GRANSKNING_ORIGINALITET: skugga, avgor),
inspo (NWP_MCP_CONFIG: av, kontroller/mcp/inspo.json), atelje (NWP_ATELJE: av, pa).
Byggena heter <slug>-abx och <slug>-aby; vilket värde som hör till x och y lottas och sparas i kunder/ab/<id>.json,
som dashboarden döljer tills ägaren har valt. Finns katalogerna redan vägrar starten: ett nytt försök får en ny slug.
Byggets dist-hash sparas när armen är klar; dashboarden låter ägaren välja först när båda körningarna avslutats och
bara om byggena är oförändrade sedan dess. Syskonbygget räknas inte som tidigare bygge (upptagna val, granskaren),
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import inte_i_bygge  # noqa: E402  (revisionen 2026-10-03, F1: körs aldrig inne i ett bygge)
import prova  # noqa: E402  dist_hash: armens slutversion fastställs av ab.py självt

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
AB = KUNDER / 'ab'
VARIABLER = {'effort': 'NWP_EFFORT', 'modell': 'NWP_MODELL', 'originalitet': 'NWP_GRANSKNING_ORIGINALITET', 'inspo': 'NWP_MCP_CONFIG', 'atelje': 'NWP_ATELJE'}
SLUG = re.compile(r'^[a-z0-9-]{2,52}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def kontextdjup(rader, fonster=1_000_000):
    """Hur djupt bygget gick i modellens fönster: största kontexten i ett meddelande (indata, skriven och läst cache)
    och antal meddelanden över halva fönstret. Ingen regel, en variabel att ha när nästa par döms (ur caveman-intaget)."""
    storlekar = []
    for r in rader:
        if r.get('type') == 'assistant':
            u = (r.get('message') or {}).get('usage') or {}
            storlekar.append(sum(u.get(k) or 0 for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')))
    return {'kontext_max': max(storlekar, default=0), 'over_halva': sum(s > fonster // 2 for s in storlekar),
            'meddelanden': len(storlekar)}


def matt(slug):
    """Tid, turer och kontextdjup ur körningens logg och granskarens betyg, efter bygget."""
    k = KUNDER / slug
    loggar = sorted(k.glob('korning-*.jsonl'))
    resultat = {}
    if loggar:
        rader = []
        for rad in loggar[-1].read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                rader.append(json.loads(rad))
            except ValueError:
                continue
        slut = next((r for r in reversed(rader) if r.get('type') == 'result'), None)
        if slut:
            resultat = {'turer': slut.get('num_turns'), 'minuter': round((slut.get('duration_ms') or 0) / 60000, 1)}
        fonster = max([m.get('contextWindow') or 0 for m in ((slut or {}).get('modelUsage') or {}).values()] or [0]) or 1_000_000
        resultat.update(kontextdjup(rader, fonster))
    g = las(k / 'granskning' / 'GRANSKNING.json') or {}
    s = las(k / 'prov' / 'STATUS.json') or {}
    dist = k / 'sajt' / 'dist'
    return {**resultat, 'provet_gront': s.get('ok'), 'granskning_godkand': g.get('godkand'),
            'dist_sha256': prova.dist_hash(dist) if (dist / 'index.html').is_file() else None,  # slutversionen, mätt här
            'betyg': {n: x.get('betyg') for n, x in (g.get('kriterier') or {}).items()},
            'omgangar': len(list((k / 'granskning').glob('runda-*'))) if (k / 'granskning').is_dir() else 0}


def starta(a):
    if not SLUG.match(a.slug):
        print('ogiltig slug (högst 52 tecken, a–z, 0–9, -)')
        return 2
    if a.variabel not in VARIABLER:
        print('variabel ska vara en av ' + ', '.join(VARIABLER))
        return 2
    x, y = a.slug + '-abx', a.slug + '-aby'
    # Varje försök får egna arbetskataloger: ett nytt försök med samma slug skulle annars ärva kod, underlag, domar och
    # granskningar från det förra, och äldre jämförelser skulle peka på mappar som ändrats (revisionen 2026-10-03, F16).
    upptagna = [str(d.relative_to(ROOT)) for s in (x, y) for d in (KUNDER / s, ROOT / 'underlag' / s) if d.exists()]
    if upptagna:
        print('finns redan från ett tidigare försök: %s. Välj en ny slug (till exempel %s-2) så att försöken inte blandas.' % (', '.join(upptagna), a.slug))
        return 2
    AB.mkdir(parents=True, exist_ok=True)
    ident = 'ab-%s-%s' % (a.slug, datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    varden = [a.a, a.b]
    random.shuffle(varden)
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


def hash_(a):
    """Sätt saknad dist-hash för en äldre, ovald jämförelse ur armarnas nuvarande dist (uttrycklig åtgärd, så att en
    jämförelse utan hash aldrig verifieras tyst; revisionen 2026-10-03, F15)."""
    fil = AB / (a.id + '.json')
    p = las(fil)
    if not p:
        print('ingen jämförelse %s' % a.id)
        return 2
    if p.get('val') is not None:
        print('redan vald; hashen behövs inte')
        return 2
    if not p.get('klar'):
        print('jämförelsen är inte klar; vänta tills båda armarna är avslutade')
        return 2
    for slug in p.get('byggen', []):
        post = p.setdefault('korningar', {}).setdefault(slug, {})
        dist = KUNDER / slug / 'sajt' / 'dist'
        if post.get('dist_sha256'):
            print('%s: hash finns redan' % slug)
        elif (dist / 'index.html').is_file():
            post['dist_sha256'] = prova.dist_hash(dist)
            post['dist_sha256_satt_i_efterhand'] = nu()
            print('%s: hash satt ur nuvarande dist (%s)' % (slug, post['dist_sha256'][:12]))
        else:
            print('%s: inget dist att hasha' % slug)
            return 1
    fil.write_text(json.dumps(p, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
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
    h = sub.add_parser('hash', help='sätt saknad dist-hash för en äldre, ovald jämförelse')
    h.add_argument('id')
    a = p.parse_args(argv)
    inte_i_bygge('ab.py')
    return {'starta': starta, 'lista': lista, 'hash': hash_}[a.kommando](a)


if __name__ == '__main__':
    sys.exit(main())
