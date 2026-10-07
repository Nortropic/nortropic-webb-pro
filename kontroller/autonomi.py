#!/usr/bin/env python3
"""autonomi.py — autonomins mått per bygge och över alla byggen (Codex helhetsbedömning 2026-10-04, punkt 9).

Kvalitet, tillförlitlighet och modellanvändning mäts tillsammans: andelen byggen som ägaren skulle visa för
verksamheten utan större ändringar, total körtid och modellanvändning inklusive granskare och ateljé, ägarens minuter,
återkommande röda grindar i provet, variationen mellan två körningar av samma verksamhet (A/B-paren) och om en ny
granskningsomgång förbättrade eller försämrade den bästa tidigare. Modellanvändningen redovisas som turer och listpris
(total_cost_usd ur sessionernas resultat): rapporterat listpris, inte fakturerad kostnad eller abonnemangskvot.

Regressionsprov och förmågeprov hålls isär: rökprovet (kontroller/rokprov.sh) visar att kända beteenden håller;
förmågeprovet är riktiga byggen på varierade kundfall med ägarens blinda dom (kunskap/autonomi.md).

    .venv/bin/python kontroller/autonomi.py [--ut kunder/AUTONOMI.json] [--md kunder/AUTONOMI.md]

Läser bara (kunder/<slug>/korning-*.jsonl, granskning/, prov/historik.jsonl, prov/STOPPVAKT.json, DOM.json och
underlag/<slug>/atelje/svar-*.json); skriver bara de två utfilerna, som är privata (kunder/ är utanför git).
"""
import argparse
import json
import math
import os
import re
import stat
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
NAMNSVAR = (*ACCEPTERAD, 'Nej, inte utan större ändringar', *TYDLIGT_DALIG)


def las_json(p):
    try:
        p = Path(p)
        if not stat.S_ISREG(p.lstat().st_mode):
            return None
        obj = json.loads(p.read_text(encoding='utf-8'))
        return obj if isinstance(obj, dict) else None
    except (OSError, ValueError):
        return None


def sessionsresultat(fil):
    """Sista resultatraden i en strömmad sessionslogg (claude -p --output-format stream-json)."""
    try:
        if not stat.S_ISREG(Path(fil).lstat().st_mode):
            return None
        with open(fil, encoding='utf-8', errors='replace') as f:
            return resultat_ur_rader(f)
    except OSError:
        return None


def resultat_ur_rader(rader):
    """Gemensam terminaltolkning för resursrapport och A/B; en senare trasig rad gör föregående resultat okänt."""
    slut = None
    for rad in rader:
        if not rad.strip():
            continue
        try:
            r = json.loads(rad)
        except ValueError:
            slut = None
            continue
        if not isinstance(r, dict):
            slut = None
            continue
        if r.get('type') == 'result':
            slut = r
    return slut


def andligt_tal(v):
    try:
        return type(v) in (int, float) and math.isfinite(v) and v >= 0
    except OverflowError:
        return False


def summa(svar):
    """Summera råvärden en gång; ofullständiga svar ger okänd total och en tydligt partiell observerad summa.

    Ett resultat-id identifierar en händelse. Utan det kan bara identiska kopior med
    samma sessions-id slås ihop; två anonyma resultat antas aldrig vara samma anrop.
    Dessa mått täcker hittade resultatfiler, inte anrop som saknar alla spår.
    """
    poster, identifierade, konflikter, dubbla = [], {}, set(), 0
    for s in svar:
        identitet = None
        if isinstance(s, dict):
            innehall = json.dumps(s, sort_keys=True, ensure_ascii=False)
            if isinstance(s.get('uuid'), str) and s['uuid']:
                identitet = ('resultat', s['uuid'])
            elif isinstance(s.get('session_id'), str) and s['session_id']:
                identitet = ('session-kopia', s['session_id'], innehall)
            if identitet in identifierade:
                plats, tidigare = identifierade[identitet]
                if tidigare == innehall:
                    dubbla += 1
                else:
                    konflikter.add(identitet)
                    poster[plats] = None
                continue
            if identitet:
                identifierade[identitet] = (len(poster), innehall)
        poster.append(s)
    observerat, saknade, totaler, summeringsfel = {}, {}, {}, []
    for nyckel in ('num_turns', 'duration_ms', 'total_cost_usd'):
        varden = [s.get(nyckel) if isinstance(s, dict) else None for s in poster]
        giltiga = [v for v in varden if andligt_tal(v)
                   and (nyckel != 'num_turns' or type(v) is int)]
        try:
            delsumma = sum(giltiga)
        except OverflowError:
            delsumma = None
        if not andligt_tal(delsumma):
            delsumma = None
            summeringsfel.append(nyckel)
        observerat[nyckel] = delsumma
        saknade[nyckel] = len(poster) - len(giltiga)
        totaler[nyckel] = delsumma if poster and not saknade[nyckel] else None
    ms, pris = totaler['duration_ms'], totaler['total_cost_usd']
    return {'sessioner': len(poster), 'turer': totaler['num_turns'], 'duration_ms': ms,
            'minuter': round(ms / 60000, 1) if ms is not None else None,
            'listpris_usd': round(pris, 2) if pris is not None else None,
            'observerat': observerat, 'saknade': saknade, 'dubbletter': dubbla, 'konflikter': len(konflikter),
            'summeringsfel': summeringsfel,
            'fullstandigt': bool(poster) and not any(saknade.values()) and not konflikter and not summeringsfel}


def granskningen(k, samlade=None):
    """Omgångarna: betyg, blockerande fynd och modellanvändning per omgång, och om den sista var den bästa. En omgång
    utan dom (ingen GRANSKNING.json, eller UTFALL.json som säger fel eller avbruten) rangordnas inte men räknas i
    modellanvändningen: dess sessioner körde (granskningen av r60, punkt 3)."""
    rundor, fallna, alla_svar = [], [], []
    for r in sorted((k / 'granskning').glob('runda-*')) if (k / 'granskning').is_dir() else []:
        g = las_json(r / 'GRANSKNING.json')
        terminal = las_json(r / 'UTFALL.json')
        utfall = (terminal or {}).get('status')
        filer = sorted(r.glob('svar*.json'))
        svar = [las_json(p) for p in filer]
        sessioner = (g or {}).get('sessioner')
        vantade = set()
        for s in sessioner if isinstance(sessioner, list) else []:
            n = s.get('granskare') if isinstance(s, dict) else None
            if type(n) is int and n > 0:
                vantade.add('svar.json' if n == 1 else 'svar-%d.json' % n)
        if vantade - {p.name for p in filer}:
            svar.append(None)
        svar = svar or [None]
        alla_svar.extend(svar)
        kriterier = (g or {}).get('kriterier') or {}
        if (not isinstance(g, dict) or utfall in ('fel', 'avbruten', 'pagar')
                or ((r / 'UTFALL.json').exists() and (not terminal or utfall != 'klar'))
                or not isinstance(kriterier, dict) or any(not isinstance(x, dict) for x in kriterier.values())):
            fallna.append({'runda': r.name, 'utfall': utfall or 'ingen dom', **summa(svar)})
            continue
        betyg = {n: x.get('betyg') for n, x in kriterier.items()}
        rundor.append({'runda': r.name, 'godkand': g.get('godkand'), 'betyg': betyg,
                       'betygssumma': sum(b for b in betyg.values() if isinstance(b, (int, float))),
                       'blockerande': len(g.get('blockerande') or []), **summa(svar)})
    modell = summa(alla_svar)
    if samlade is not None:
        samlade.extend(alla_svar)
    if not rundor:
        return {'omgangar': 0, 'fallna_rundor': fallna, 'modell': modell}
    # bäst: godkänd före underkänd, sedan färre blockerande fynd, sedan högre betygssumma
    nyckel = lambda x: (bool(x['godkand']), -x['blockerande'], x['betygssumma'])  # noqa: E731
    basta = max(range(len(rundor)), key=lambda i: (nyckel(rundor[i]), i))
    forsamringar = [rundor[i]['runda'] for i in range(1, len(rundor)) if nyckel(rundor[i]) < max(nyckel(x) for x in rundor[:i])]
    return {'omgangar': len(rundor), 'godkand': rundor[-1]['godkand'], 'sista_betyg': rundor[-1]['betyg'],
            'basta_runda': rundor[basta]['runda'], 'sista_ar_basta': nyckel(rundor[-1]) >= nyckel(rundor[basta]),
            'forsamrade_rundor': forsamringar, 'rundor': rundor, 'fallna_rundor': fallna, 'modell': modell}


def provet(k):
    """Provets körningar ur historiken: hur många, hur ofta varje grind var röd och när provet först var helt grönt."""
    rader = []
    try:
        for rad in (k / 'prov' / 'historik.jsonl').read_text(encoding='utf-8').split('\n'):  # JSONL: radslut (KAN-A)
            try:
                obj = json.loads(rad)
                if isinstance(obj, dict) and isinstance(obj.get('grindar'), dict):
                    rader.append(obj)
            except ValueError:
                continue
    except OSError:
        pass
    roda = Counter(g for r in rader for g, ok in (r.get('grindar') or {}).items() if not ok)
    forsta = next((i + 1 for i, r in enumerate(rader) if r.get('ok') and not r.get('snabb')), None)
    return {'korningar': len(rader), 'roda_grindar': dict(roda.most_common()), 'forsta_hela_grona': forsta}


def agaren(k):
    """Ägarens senaste dom och väggtid från öppning till sparning, inte aktiv arbetstid."""
    domar = (las_json(k / 'DOM.json') or {}).get('domar') or []
    if not isinstance(domar, list) or not domar or not isinstance(domar[-1], dict):
        return {'domd': False}
    d = domar[-1]
    svar = d.get('svar') if isinstance(d.get('svar'), dict) else {}
    namn = svar.get('namn')
    giltigt = isinstance(namn, str) and namn in NAMNSVAR
    return {'domd': giltigt, 'tid': d.get('tid'), 'namn': namn if giltigt else None, 'battre': svar.get('battre'), 'sakerhet': svar.get('sakerhet'),
            'accepterad': namn in ACCEPTERAD if giltigt else None, 'minuter': d.get('minuter'), 'domar': len(domar)}


def ateljesvar(slug):
    """Svar och kända saknade svar i aktiv ateljé och omtagsarkiv; inga länkar följs, läsfel är okänd användning."""
    ut = []
    kundrot = UNDERLAG / slug
    if kundrot.is_symlink():
        return [None]
    for bas in (kundrot / 'atelje', kundrot / 'omtag'):
        if bas.is_symlink():
            ut.append(None)
            continue
        if not bas.exists():
            continue
        for rot, dirs, filer in os.walk(bas, followlinks=False, onerror=lambda _e: ut.append(None)):
            rot = Path(rot)
            for d in list(dirs):
                if d in ('node_modules', '.git', 'dist', '.astro'):
                    dirs.remove(d)  # byggutdata och beroenden bär inga av flödets sessionsresultat
                elif (rot / d).is_symlink():
                    ut.append(None)
                    dirs.remove(d)
            for namn in filer:
                if namn.startswith('svar-') and namn.endswith('.json'):
                    ut.append(las_json(rot / namn))
            if 'STATUS.json' in filer:
                status = las_json(rot / 'STATUS.json')
                if status is None:
                    ut.append(None)
                    continue
                sessioner = status.get('sessioner')
                for s in sessioner if isinstance(sessioner, list) else []:
                    namn = s.get('svar') if isinstance(s, dict) else None
                    if isinstance(namn, str) and (Path(namn).name != namn or namn not in filer):
                        ut.append(None)
    return ut


def bygge(slug):
    k = KUNDER / slug
    loggar = sorted(k.glob('korning-*.jsonl'))
    resultat = [sessionsresultat(f) for f in loggar]
    # ateljéns alla sessioner: roten, arkiverade omgångar (omgang-N/) och tidigare körningar (foregaende/)
    ateljen = ateljesvar(slug)
    granskningssvar = []
    g = granskningen(k, granskningssvar)
    sv = las_json(k / 'prov' / 'STOPPVAKT.json') or {}
    start = re.search(r'korning-(\d{8}T\d{6}Z)', loggar[0].name) if loggar else None
    ateljestart = (las_json(UNDERLAG / slug / 'atelje/STATUS.json') or {}).get('startad')
    b = {'slug': slug, 'start': start.group(1) if start else ateljestart if isinstance(ateljestart, str) else None,
         'bygget': summa(resultat), 'omtag': max(0, len(loggar) - 1), 'granskning': g,
         'loggar_utan_resultat': sum(1 for r in resultat if not r),  # avbruten körning: modelltiden är inte mätt
         'ateljen': summa(ateljen) if ateljen else None, 'provet': provet(k),
         'stoppvakt': {x: sv.get(x) for x in ('slapp', 'forsok', 'tak', 'granskning', 'skal')} if sv else None,
         'agaren': agaren(k), 'ab_syskon': ((k / 'AB-SYSKON').read_text(encoding='utf-8').strip() if (k / 'AB-SYSKON').is_file() else None)}
    b['totalt'] = summa(resultat + granskningssvar + ateljen)
    return b


def byggen():
    kund = {p.name for p in KUNDER.iterdir() if p.is_dir() and not p.is_symlink()
            and ((p / 'sajt').is_dir() or list(p.glob('korning-*.jsonl')))} if KUNDER.is_dir() else set()
    for p in UNDERLAG.iterdir() if UNDERLAG.is_dir() else []:
        if p.is_dir() and not p.is_symlink() and (las_json(p / 'atelje/STATUS.json') or {}).get('startad'):
            kund.add(p.name)
    return sorted(kund - INTE_BYGGEN)


def matt(b):
    """Alla hittade resultat och kända försök har mätvärden. Inget bevis för helt ospårade anrop."""
    return not b.get('loggar_utan_resultat') and bool((b.get('totalt') or {}).get('fullstandigt'))


def median(xs):
    xs = sorted(x for x in xs if andligt_tal(x))
    if not xs:
        return None
    i = len(xs) // 2
    # Alla värden är icke-negativa: differensen och medelvärdet ryms även nära flyttalets övre gräns.
    v = xs[i] if len(xs) % 2 else xs[i - 1] + (xs[i] - xs[i - 1]) / 2
    return round(v, 1) if andligt_tal(v) else None


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
    return {'byggen': len(alla), 'startade': sum(bool(b.get('start')) for b in alla),
            'utan_giltig_agardom': sum(not b['agaren'].get('domd') for b in alla),
            'underkanda': len(domda) - len(acc), 'domda': len(domda), 'accepterade': len(acc),
            'andel_accepterade': round(len(acc) / len(domda), 2) if domda else None,
            'tydligt_daliga': sum(1 for b in domda if b['agaren'].get('namn') in TYDLIGT_DALIG),
            'median_minuter': median([b['totalt']['minuter'] for b in alla if matt(b)]),
            'median_listpris_usd': median([b['totalt']['listpris_usd'] for b in alla if matt(b)]),
            'median_minuter_accepterade': median([b['totalt']['minuter'] for b in acc if matt(b)]),
            'ej_matta': [b['slug'] for b in alla if not matt(b)],
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
             'sessionernas total_cost_usd: rapporterat listpris, inte fakturerad kostnad eller abonnemangskvot. Saknade värden är okända.',
             'Identifierade kopior räknas en gång; summan omfattar hittade resultat, inte helt ospårade anrop. Ägartiden är väggtid, inte aktiv arbetstid, från att byggets sida öppnades',
             'i dashboarden till att domen skickades, och finns bara för domar efter 2026-10-05. Namnsvaren gäller ribban när',
             'domen gavs: ägaren har därefter sagt (2026-10-03, kritik/GRANSKARE.md) att de egna byggena inte håller, så andelen',
             'accepterade bland äldre domar är en övre gräns tills nya domar finns.', '',
             '| Mått | Värde |', '|---|---|',
             '| Uppdrag med belagd start | %d av %d inventerade |' % (s['startade'], s['byggen']),
             '| Utan giltig ägardom på ribbans fråga | %d |' % s['utan_giltig_agardom'],
             '| Dömda byggen | %d av %d |' % (s['domda'], s['byggen']),
             '| Accepterade utan större ändringar | %d (%s av de dömda) |' % (s['accepterade'], pct(s['andel_accepterade'])),
             '| Tydligt dåliga (namnsvaret Nej) | %d |' % s['tydligt_daliga'],
             '| Kräver större ändringar eller underkända av ägaren | %d |' % s['underkanda'],
             '| Median modelltid per bygge (bygge, granskare, ateljé) | %s min |' % s['median_minuter'],
             '| Median listpris per bygge | %s USD |' % s['median_listpris_usd'],
             '| Median modelltid per accepterat bygge | %s min |' % (s['median_minuter_accepterade'] if s['median_minuter_accepterade'] is not None else '–'),
             '| Väggtid från öppnad vy till ägarens dom (median, min) | %s |' % (s['agarens_minuter'] if s['agarens_minuter'] is not None else 'ej mätt än'),
             '| Granskningen försämrade den bästa tidigare omgången | %s |' % (', '.join(s['granskningen_forsamrade']) or 'inget bygge'),
             '| Sista omgången var inte den bästa | %s |' % (', '.join(s['sista_inte_basta']) or 'inget bygge'),
             '| Ofullständiga resursmått (utanför medianerna) | %s |' % (', '.join(s['ej_matta']) or 'inga'), '',
             '## Röda grindar i provet, över alla körningar', '',
             ', '.join('%s %d' % (g, n) for g, n in s['vanligaste_roda_grindar'].items()) or 'Inga.', '',
             '## Per bygge', '',
             '| Bygge | Start | Omtag | Modelltid (min) | Turer | Listpris (USD) | Omgångar | Godkänd | Provkörningar | Ägarens namnsvar |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for b in r['per_bygge']:
        g = b['granskning']
        rader.append('| %s | %s | %d | %s | %s | %s | %d | %s | %d | %s |' % (
            b['slug'], b['start'] or '–', b['omtag'], b['totalt']['minuter'] if matt(b) else 'ej mätt', b['totalt']['turer'] if matt(b) else 'ej mätt',
            b['totalt']['listpris_usd'] if matt(b) else 'ej mätt',
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
