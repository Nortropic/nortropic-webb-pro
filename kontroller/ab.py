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
bara om byggena är oförändrade sedan dess. Armens besked kommer ur dess slutpost (kunder/<arm>/korningar/<körning>/
SLUT.json, kontroller/korslut.py): slutkoden, de fem tillstånden och granskarens dom över armens slutliga bygge med
aktuell metod, aldrig granskningens rotfil, som kan gälla ett äldre bygge (ägarens uppdrag 2026-10-07, punkt 4).
Syskonbygget räknas inte som tidigare bygge (upptagna val, granskaren), så att det ena bygget inte påverkar det andra. Körningen tar två fulla byggen; starta den med nohup.
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
import korslut  # noqa: E402  armens slutpost
import autonomi  # noqa: E402  råvärden och okända mått

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
AB = KUNDER / 'ab'
VARIABLER = {'effort': 'NWP_EFFORT', 'modell': 'NWP_MODELL', 'originalitet': 'NWP_GRANSKNING_ORIGINALITET', 'inspo': 'NWP_MCP_CONFIG', 'atelje': 'NWP_ATELJE'}
SLUG = re.compile(r'^[a-z0-9-]{2,52}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def forbered_skiss(slug, kid):
    import ab_skiss
    return ab_skiss.forbered(sys.modules[__name__], slug, kid)


def skissval(slug, kid, standard):
    import ab_skiss
    return ab_skiss.val(sys.modules[__name__], slug, kid, standard)


def skisskrav(slug):
    import ab_skiss
    return ab_skiss.krav(sys.modules[__name__], slug)


def skissavslutad(slug, kid):
    import ab_skiss
    return ab_skiss.avslutad(sys.modules[__name__], slug, kid)


def skissresultat(slug):
    import ab_skiss
    return ab_skiss.resultat(sys.modules[__name__], slug)


def skisskommando(a):
    try:
        if a.kommando == 'forbered-skiss':
            p = forbered_skiss(a.slug, a.kandidat)
            print('Förberett %s; inga sessioner startade. Kräver mandat för underlag och budget före körning.' % p['id'])
            print('Kör sedan befintligt prototypflöde med --fortsatt. Bedöm bilderna blint i Prototyp före resultatet.')
        else:
            import kandidater
            if not kandidater.domd(a.slug):
                raise ValueError('bedöm kandidaterna blint i Prototyp före resultatsammanställningen')
            print(json.dumps(skissresultat(a.slug), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as e:
        print(str(e)); return 2


def las(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def kontextdjup(rader, fonster=None):
    """Hur djupt bygget gick i modellens fönster: största kontexten i ett meddelande (indata, skriven och läst cache)
    och antal meddelanden över halva fönstret. Ingen regel, en variabel att ha när nästa par döms (ur caveman-intaget)."""
    storlekar, partiella, antal = [], [], 0
    for r in rader:
        if isinstance(r, dict) and r.get('type') == 'assistant':
            antal += 1
            med = r.get('message') if isinstance(r.get('message'), dict) else {}
            u = med.get('usage') if isinstance(med.get('usage'), dict) else {}
            v = [u.get(k) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')]
            giltiga = [x for x in v if type(x) is int and x >= 0]
            if giltiga:
                partiella.append(sum(giltiga))
            if len(giltiga) == len(v):
                storlekar.append(sum(giltiga))
    hel = bool(antal) and len(storlekar) == antal
    return {'kontext_max': max(storlekar) if hel else None,
            'over_halva': sum(s > fonster // 2 for s in storlekar) if hel and type(fonster) is int and fonster > 0 else None,
            'observerad_kontext_max': max(partiella, default=None), 'meddelanden': antal}


def skillanrop(rader):
    """Vilka skills bygget anropade, med antal, ur loggens Skill-anrop (backlogposten om Skill-räkningen): {namn: antal}."""
    ut = {}
    for r in rader:
        if not isinstance(r, dict) or r.get('type') != 'assistant':
            continue
        med = r.get('message') if isinstance(r.get('message'), dict) else {}
        innehall = med.get('content') if isinstance(med.get('content'), list) else []
        for c in innehall:
            if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') == 'Skill' and isinstance(c.get('input'), dict) and isinstance(c['input'].get('skill'), str):
                ut[c['input']['skill']] = ut.get(c['input']['skill'], 0) + 1
    return dict(sorted(ut.items()))


def matt(slug, efter=None):
    """Tid, turer och kontextdjup ur körningens logg, och armens besked ur dess slutpost (den senaste körningen från
    efter, en körningsidentitet): slutkoden, tillstånden, provet och granskarens dom och betyg för armens slutliga bygge
    med aktuell metod. Utan slutpost står det, och ingen dom läses någon annanstans ifrån."""
    k = KUNDER / slug
    fil, post = korslut.senaste_slutpost(k, efter=efter)
    loggar = sorted(p for p in k.glob('korning-*.jsonl') if not efter or p.stem.removeprefix('korning-') >= efter)
    if post:
        # En nyare sessionslogg får inte låna den föregående körningens slutbesked.
        loggar = [p for p in loggar if p.name == 'korning-%s.jsonl' % post.get('korning')]
    resultat = {'turer': None, 'minuter': None, 'modell': None, 'effort': None,
                'kontext_max': None, 'over_halva': None, 'logg': None, 'logg_lasfel': False}
    if loggar:
        rader = []
        lasfel = False
        try:
            raw = loggar[-1].read_text(encoding='utf-8').split('\n')
        except (OSError, UnicodeError):
            raw = []
            lasfel = True
        for rad in raw:  # JSONL: radslut, aldrig U+2028 (KAN-A)
            if not rad.strip():
                continue
            try:
                obj = json.loads(rad)
                if isinstance(obj, dict):
                    rader.append(obj)
                else:
                    lasfel = True
            except ValueError:
                lasfel = True
        slut = autonomi.resultat_ur_rader(raw)
        if slut:
            m = autonomi.summa([slut])
            resultat.update({x: m[x] for x in ('turer', 'minuter', 'duration_ms', 'listpris_usd')})
        init = next((r for r in rader if r.get('type') == 'system' and r.get('subtype') == 'init'), None) or {}
        resultat.update(modell=init.get('model'), version=init.get('claude_code_version'), skills=skillanrop(rader), logg=loggar[-1].name)
        anv = (slut or {}).get('modelUsage')
        f = [m.get('contextWindow') for m in anv.values() if isinstance(m, dict)] if isinstance(anv, dict) else []
        # Olika modellfönster saknar korrelation till varje meddelande: ingen gissad miljon.
        fonster = f[0] if f and all(type(x) is int and x > 0 and x == f[0] for x in f) else None
        resultat.update(kontextdjup(rader, fonster))
        resultat['logg_lasfel'] = lasfel
        if lasfel:
            resultat.update(kontext_max=None, over_halva=None)
    dist = k / 'sajt' / 'dist'
    ut = {**resultat, 'dist_sha256': prova.dist_hash(dist) if (dist / 'index.html').is_file() else None,  # slutversionen, mätt här
          'omgangar': len(list((k / 'granskning').glob('runda-*'))) if (k / 'granskning').is_dir() else 0}
    if not post:
        return {**ut, 'slutpost': None, 'slutpost_saknas': 'kor.sh skrev ingen slutpost för armen', 'provet_gront': None,
                'granskning_godkand': None, 'betyg': {}}
    t = post.get('tillstand') or {}
    dg = t.get('designgranskaren_godkanner') or {}
    aktuell = (post.get('designgranskning') or {}).get('aktuell') or {}
    return {**ut, 'slutpost': 'kunder/%s/korningar/%s/%s' % (slug, fil.parent.name, fil.name), 'korning': post.get('korning'),
            'slutkod': post.get('slutkod'), 'tillstand': {n: (x or {}).get('varde') for n, x in t.items()},
            'slutpost_dist_sha256': post.get('dist_sha256'),
            'provet_gront': ((post.get('kontroller') or {}).get('provet') or {}).get('varde'),
            'granskning_godkand': dg.get('varde'), 'granskning': dg.get('text'), 'betyg': aktuell.get('betyg') or {}}


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
        start, start_id = time.time(), datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')  # kor.sh:s körning börjar tidigast här
        rc = subprocess.run([str(ROOT / 'kor.sh'), slug, a.verksamhet], env=miljo, cwd=str(ROOT)).returncode
        post = las(fil)
        post.setdefault('korningar', {})[slug] = {'rc': rc, 'sekunder': round(time.time() - start), **matt(slug, efter=start_id)}
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
    f = sub.add_parser('forbered-skiss', help='förbered medium mot high i skisskaparen; startar inga sessioner')
    f.add_argument('slug')
    f.add_argument('--kandidat', default='k01')
    r = sub.add_parser('skissresultat', help='mått efter ägarens blinda val; ändrar inga standardvärden')
    r.add_argument('slug')
    a = p.parse_args(argv)
    inte_i_bygge('ab.py')
    return {'starta': starta, 'lista': lista, 'hash': hash_,
            'forbered-skiss': skisskommando, 'skissresultat': skisskommando}[a.kommando](a)


if __name__ == '__main__':
    sys.exit(main())
