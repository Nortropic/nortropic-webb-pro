#!/usr/bin/env python3
"""autonomi.py — autonomins mått per bygge och över alla byggen (Codex helhetsbedömning 2026-10-04, punkt 9).

Kvalitet, tillförlitlighet och modellanvändning mäts tillsammans: andelen byggen som ägaren skulle visa för
verksamheten utan större ändringar, total körtid och modellanvändning inklusive granskare och ateljé, ägarens minuter,
återkommande röda grindar i provet, variationen mellan två körningar av samma verksamhet (A/B-paren) och om en ny
granskningsomgång förbättrade eller försämrade den bästa tidigare. Modellanvändningen redovisas som turer och listpris
(total_cost_usd ur sessionernas resultat): ett mått på kvoten, inte en kostnad (Max-abonnemanget).

Regressionsprov och förmågeprov hålls isär: rökprovet (kontroller/rokprov.sh) visar att kända beteenden håller;
förmågeprovet är riktiga byggen på varierade kundfall med ägarens blinda dom (kunskap/autonomi.md).

    .venv/bin/python kontroller/autonomi.py [--ut kunder/AUTONOMI.json] [--md kunder/AUTONOMI.md]

Läser bara (kunder/<slug>/korning-*.jsonl, granskning/, prov/historik.jsonl, prov/STOPPVAKT.json, DOM.json och
underlag/<slug>/atelje/svar-*.json); skriver bara de två utfilerna, som är privata (kunder/ är utanför git).
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
INTE_BYGGEN = {'ab', 'rokprov-mall'}
# ägarens svar på kärnfrågan "Skulle du sätta ditt namn på sajten och visa den för verksamheten?" (dashboard/server.py)
ACCEPTERAD = ('Ja, som den är', 'Ja, efter små ändringar')
TYDLIGT_DALIG = ('Nej',)  # Codex punkt 8: inte bara genomsnittet, också hur ofta ett bygge blir tydligt dåligt


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def sessionsresultat(fil):
    """Sista resultatraden i en strömmad sessionslogg (claude -p --output-format stream-json)."""
    slut = None
    try:
        with open(fil, encoding='utf-8', errors='replace') as f:
            for rad in f:
                if '"type":"result"' not in rad.replace(' ', ''):
                    continue
                try:
                    r = json.loads(rad)
                except ValueError:
                    continue
                if r.get('type') == 'result':
                    slut = r
    except OSError:
        return None
    return slut


def summa(svar):
    """Turer, minuter och listpris ur sessionssvar (dict med num_turns, duration_ms, total_cost_usd)."""
    svar = [s for s in svar if isinstance(s, dict)]
    return {'sessioner': len(svar), 'turer': sum(int(s.get('num_turns') or 0) for s in svar),
            'minuter': round(sum(float(s.get('duration_ms') or 0) for s in svar) / 60000, 1),
            'listpris_usd': round(sum(float(s.get('total_cost_usd') or 0) for s in svar), 2)}


def granskningen(k):
    """Omgångarna: betyg, blockerande fynd och modellanvändning per omgång, och om den sista var den bästa."""
    rundor = []
    for r in sorted((k / 'granskning').glob('runda-*')) if (k / 'granskning').is_dir() else []:
        g = las_json(r / 'GRANSKNING.json') or {}
        betyg = {n: (x or {}).get('betyg') for n, x in (g.get('kriterier') or {}).items()}
        svar = [las_json(p) for p in sorted(r.glob('svar*.json'))]
        rundor.append({'runda': r.name, 'godkand': g.get('godkand'), 'betyg': betyg,
                       'betygssumma': sum(b for b in betyg.values() if isinstance(b, (int, float))),
                       'blockerande': len(g.get('blockerande') or []), **summa(svar)})
    if not rundor:
        return {'omgangar': 0}
    # bäst: godkänd före underkänd, sedan färre blockerande fynd, sedan högre betygssumma
    nyckel = lambda x: (bool(x['godkand']), -x['blockerande'], x['betygssumma'])  # noqa: E731
    basta = max(range(len(rundor)), key=lambda i: (nyckel(rundor[i]), i))
    forsamringar = [rundor[i]['runda'] for i in range(1, len(rundor)) if nyckel(rundor[i]) < max(nyckel(x) for x in rundor[:i])]
    return {'omgangar': len(rundor), 'godkand': rundor[-1]['godkand'], 'sista_betyg': rundor[-1]['betyg'],
            'basta_runda': rundor[basta]['runda'], 'sista_ar_basta': nyckel(rundor[-1]) >= nyckel(rundor[basta]),
            'forsamrade_rundor': forsamringar, 'rundor': rundor,
            **{'modell': summa([{'num_turns': x['turer'], 'duration_ms': x['minuter'] * 60000, 'total_cost_usd': x['listpris_usd']} for x in rundor])}}


def provet(k):
    """Provets körningar ur historiken: hur många, hur ofta varje grind var röd och när provet först var helt grönt."""
    rader = []
    try:
        for rad in (k / 'prov' / 'historik.jsonl').read_text(encoding='utf-8').splitlines():
            try:
                rader.append(json.loads(rad))
            except ValueError:
                continue
    except OSError:
        pass
    roda = Counter(g for r in rader for g, ok in (r.get('grindar') or {}).items() if not ok)
    forsta = next((i + 1 for i, r in enumerate(rader) if r.get('ok') and not r.get('snabb')), None)
    return {'korningar': len(rader), 'roda_grindar': dict(roda.most_common()), 'forsta_hela_grona': forsta}


def agaren(k):
    """Ägarens senaste dom: svaret på namnfrågan, om det är accepterat och minuterna (när dashboarden mätt dem)."""
    domar = (las_json(k / 'DOM.json') or {}).get('domar') or []
    if not domar:
        return {'domd': False}
    d = domar[-1]
    svar = d.get('svar') or {}
    namn = svar.get('namn')
    return {'domd': True, 'tid': d.get('tid'), 'namn': namn, 'battre': svar.get('battre'), 'sakerhet': svar.get('sakerhet'),
            'accepterad': namn in ACCEPTERAD if namn else None, 'minuter': d.get('minuter'), 'domar': len(domar)}


def bygge(slug):
    k = KUNDER / slug
    loggar = sorted(k.glob('korning-*.jsonl'))
    korningar = [r for r in (sessionsresultat(f) for f in loggar) if r]
    ateljen = [las_json(p) for p in sorted((UNDERLAG / slug / 'atelje').glob('svar-*.json'))] if (UNDERLAG / slug / 'atelje').is_dir() else []
    g = granskningen(k)
    sv = las_json(k / 'prov' / 'STOPPVAKT.json') or {}
    b = {'slug': slug, 'start': (re.search(r'korning-(\d{8}T\d{6}Z)', loggar[0].name).group(1) if loggar else None),
         'bygget': summa(korningar), 'omtag': max(0, len(loggar) - 1), 'granskning': g,
         'ateljen': summa(ateljen) if ateljen else None, 'provet': provet(k),
         'stoppvakt': {x: sv.get(x) for x in ('slapp', 'forsok', 'tak', 'granskning', 'skal')} if sv else None,
         'agaren': agaren(k), 'ab_syskon': ((k / 'AB-SYSKON').read_text(encoding='utf-8').strip() if (k / 'AB-SYSKON').is_file() else None)}
    delar = [b['bygget'], g.get('modell') or {}, b['ateljen'] or {}]
    b['totalt'] = {'minuter': round(sum(x.get('minuter') or 0 for x in delar), 1),
                   'turer': sum(x.get('turer') or 0 for x in delar),
                   'listpris_usd': round(sum(x.get('listpris_usd') or 0 for x in delar), 2)}
    return b


def byggen():
    return sorted(p.name for p in KUNDER.iterdir()
                  if p.is_dir() and p.name not in INTE_BYGGEN and ((p / 'sajt').is_dir() or list(p.glob('korning-*.jsonl'))))


def median(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.median(xs), 1) if xs else None


def sammanstall(alla):
    domda = [b for b in alla if b['agaren'].get('domd')]
    acc = [b for b in domda if b['agaren'].get('accepterad')]
    roda = Counter()
    for b in alla:
        roda.update(b['provet']['roda_grindar'])
    par = []
    for b in alla:
        s = b.get('ab_syskon')
        if s and b['slug'] < s:
            a2 = next((x for x in alla if x['slug'] == s), None)
            if a2:
                par.append({'par': [b['slug'], s],
                            'minuter': [b['totalt']['minuter'], a2['totalt']['minuter']],
                            'listpris_usd': [b['totalt']['listpris_usd'], a2['totalt']['listpris_usd']],
                            'sista_betyg': [b['granskning'].get('sista_betyg'), a2['granskning'].get('sista_betyg')],
                            'agarens_namnsvar': [b['agaren'].get('namn'), a2['agaren'].get('namn')]})
    return {'byggen': len(alla), 'domda': len(domda), 'accepterade': len(acc),
            'andel_accepterade': round(len(acc) / len(domda), 2) if domda else None,
            'tydligt_daliga': sum(1 for b in domda if b['agaren'].get('namn') in TYDLIGT_DALIG),
            'median_minuter': median([b['totalt']['minuter'] for b in alla]),
            'median_listpris_usd': median([b['totalt']['listpris_usd'] for b in alla]),
            'median_minuter_accepterade': median([b['totalt']['minuter'] for b in acc]),
            'agarens_minuter': median([b['agaren'].get('minuter') for b in domda]),
            'vanligaste_roda_grindar': dict(roda.most_common(8)),
            'granskningen_forsamrade': [b['slug'] for b in alla if b['granskning'].get('forsamrade_rundor')],
            'sista_inte_basta': [b['slug'] for b in alla if b['granskning'].get('omgangar') and not b['granskning'].get('sista_ar_basta')],
            'ab_par': par}


def markdown(r):
    s = r['sammanstallning']
    pct = lambda x: '–' if x is None else '%d %%' % round(100 * x)  # noqa: E731
    rader = ['# Autonomins mått · %d byggen' % s['byggen'], '',
             'Kvalitet, tillförlitlighet och modellanvändning tillsammans (Codex helhetsbedömning 2026-10-04, punkt 9). Listpriset är',
             'sessionernas total_cost_usd: ett mått på kvoten, inte en kostnad. Ägarens minuter mäts från att byggets sida öppnades',
             'i dashboarden till att domen skickades, och finns bara för domar efter 2026-10-05. Namnsvaren gäller ribban när',
             'domen gavs: ägaren har därefter sagt (2026-10-03, kritik/GRANSKARE.md) att de egna byggena inte håller, så andelen',
             'accepterade bland äldre domar är en övre gräns tills nya domar finns.', '',
             '| Mått | Värde |', '|---|---|',
             '| Dömda byggen | %d av %d |' % (s['domda'], s['byggen']),
             '| Accepterade utan större ändringar | %d (%s av de dömda) |' % (s['accepterade'], pct(s['andel_accepterade'])),
             '| Tydligt dåliga (namnsvaret Nej) | %d |' % s['tydligt_daliga'],
             '| Median modelltid per bygge (bygge, granskare, ateljé) | %s min |' % s['median_minuter'],
             '| Median listpris per bygge | %s USD |' % s['median_listpris_usd'],
             '| Median modelltid per accepterat bygge | %s min |' % (s['median_minuter_accepterade'] if s['median_minuter_accepterade'] is not None else '–'),
             '| Ägarens minuter per dom (median) | %s |' % (s['agarens_minuter'] if s['agarens_minuter'] is not None else 'ej mätt än'),
             '| Granskningen försämrade den bästa tidigare omgången | %s |' % (', '.join(s['granskningen_forsamrade']) or 'inget bygge'),
             '| Sista omgången var inte den bästa | %s |' % (', '.join(s['sista_inte_basta']) or 'inget bygge'), '',
             '## Röda grindar i provet, över alla körningar', '',
             ', '.join('%s %d' % (g, n) for g, n in s['vanligaste_roda_grindar'].items()) or 'Inga.', '',
             '## Per bygge', '',
             '| Bygge | Start | Omtag | Modelltid (min) | Turer | Listpris (USD) | Omgångar | Godkänd | Provkörningar | Ägarens namnsvar |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for b in r['per_bygge']:
        g = b['granskning']
        rader.append('| %s | %s | %d | %s | %d | %s | %d | %s | %d | %s |' % (
            b['slug'], b['start'] or '–', b['omtag'], b['totalt']['minuter'], b['totalt']['turer'], b['totalt']['listpris_usd'],
            g.get('omgangar', 0), {True: 'ja', False: 'nej'}.get(g.get('godkand'), '–'), b['provet']['korningar'],
            b['agaren'].get('namn') or ('ej dömt' if not b['agaren'].get('domd') else '–')))
    if s['ab_par']:
        rader += ['', '## Variation mellan två körningar av samma verksamhet (A/B-paren)', '',
                  '| Par | Modelltid (min) | Listpris (USD) | Ägarens namnsvar |', '|---|---|---|---|']
        for p in s['ab_par']:
            rader.append('| %s | %s | %s | %s |' % (' / '.join(p['par']), ' / '.join(str(x) for x in p['minuter']),
                                                    ' / '.join(str(x) for x in p['listpris_usd']), ' / '.join(str(x or '–') for x in p['agarens_namnsvar'])))
    return '\n'.join(rader) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(prog='autonomi', description=__doc__.split('\n\n')[0])
    p.add_argument('--ut', default=str(KUNDER / 'AUTONOMI.json'))
    p.add_argument('--md', default=str(KUNDER / 'AUTONOMI.md'))
    a = p.parse_args(argv)
    for v in (a.ut, a.md):
        if not Path(v).resolve().is_relative_to(KUNDER.resolve()):
            print('utfilerna ligger i kunder/ (privat, utanför git): %s' % v, file=sys.stderr)
            return 2
    alla = [bygge(s) for s in byggen()]
    r = {'schema': 1, 'per_bygge': alla, 'sammanstallning': sammanstall(alla)}
    Path(a.ut).write_text(json.dumps(r, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    Path(a.md).write_text(markdown(r), encoding='utf-8')
    print(markdown(r))
    return 0


if __name__ == '__main__':
    sys.exit(main())
