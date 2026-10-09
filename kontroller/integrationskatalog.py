#!/usr/bin/env python3
"""integrationskatalog.py — integrationskatalogen K01–K18 (kontroller/integrationer/katalog.json): validering och en
deterministisk integrationsplan ur kundens val (uppdraget 2026-10-09, avsnitt 5 och 6).

Katalogens id:n (K01–K18) är integrationsområden och har inget med kalibreringens K-nummer att göra.

Fyra skilda dimensioner, aldrig ett gemensamt "klart":
- behovet (kundens läge i Kundstart: onskemal, kundval, framtida, avstatt, okant, inte_relevant);
- paketets färdighet (här): dokumenterat, implementerat, kontraktsprovat, leverantorsprovat, inaktuellt;
- kundens anslutning (Kundstarts utredning med belägg);
- genomförandets mandat och operationer (journalen och kvittona).

Paketets funktioner pekar bara på namngivna, granskade funktioner i FUNKTIONER, aldrig på kommandon i metadata.
Planen räknas fram ur valen och katalogen utan modell och utan sidoeffekter: samma val och samma katalog ger samma
plan och samma plan_sha256.

    .venv/bin/python kontroller/integrationskatalog.py --prova          # validera katalogen
    .venv/bin/python kontroller/integrationskatalog.py --plan VAL.json  # planen ur en lista med val
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
KATALOG = Path(__file__).resolve().parent / 'integrationer' / 'katalog.json'

NIVAER = ('forvaltning', 'lank', 'inbaddning', 'inbyggd', 'api', 'formedlad', 'utreds')
FARDIGHET = ('dokumenterat', 'implementerat', 'kontraktsprovat', 'leverantorsprovat', 'inaktuellt')
LAGEN = ('onskemal', 'kundval', 'framtida', 'avstatt', 'okant', 'inte_relevant', 'grund')
# grund: grundleveransens paket (katalogens grund: true), som ingår utan att kunden kryssar i dem (uppdraget, avsnitt 4:
# kvalitet är inte ett tillval); läget gäller bara sådana paket.
OMFATTNING = ('kundval', 'grund')
STEG = ('inspektera', 'planera', 'tillampa', 'aterlas', 'prova', 'avveckla')
# De enda funktioner ett paket får peka på: granskade, i repot, utan godtyckliga kommandon.
FUNKTIONER = {
    'kundrepo.preview_krav', 'kundrepo.preview', 'kundrepo.preview_aktuell', 'exportera.exportera',
    'workersprov.prova', 'driftkoll.kontroll', 'seo_kontroll.main', 'forfragningar.lage', 'forfragningar.exportera_csv',
}
FALT = ('id', 'version', 'omrade', 'niva', 'grund', 'funktion', 'passar', 'passar_inte', 'kunduppgifter', 'bevara', 'kallor',
        'formagor', 'kraver', 'utesluter', 'konto', 'rattigheter', 'dataflode', 'lagring', 'kostnad', 'funktioner',
        'fardighet', 'fardighet_omfattning', 'prov', 'driftkontroll', 'begransningar', 'paverkar', 'manniska')
OMRADEN = ['K%02d' % i for i in range(1, 19)]


class Fel(ValueError):
    pass


def las(fil=KATALOG):
    return json.loads(Path(fil).read_text(encoding='utf-8'))


def _datum(v):
    return isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v)


def brister(k, rot=ROOT, importera=True):
    """Lista med brister i katalogen; tom lista är en giltig katalog."""
    ut = []
    if k.get('schema') != 1:
        ut.append('schema ska vara 1')
    if not _datum(k.get('kontrollerad')):
        ut.append('kontrollerad saknar datum')
    omr = [o.get('id') for o in k.get('omraden', [])]
    if omr != OMRADEN:
        ut.append('omraden ska vara K01–K18 i ordning: %s' % omr)
    paket = k.get('paket', [])
    ids = [p.get('id') for p in paket]
    if len(ids) != len(set(ids)):
        ut.append('dubbla paket-id: %s' % sorted({i for i in ids if ids.count(i) > 1}))
    formagor = {f for p in paket for f in p.get('formagor', [])}
    for p in paket:
        pid = p.get('id', '?')
        saknas = [f for f in FALT if f not in p]
        if saknas:
            ut.append('%s saknar %s' % (pid, ', '.join(saknas)))
            continue
        okanda = sorted(set(p) - set(FALT))
        if okanda:
            ut.append('%s har okända fält %s' % (pid, okanda))
        if not re.fullmatch(r'k\d{2}-[a-z0-9-]+', pid) or pid[:3].upper() != p['omrade']:
            ut.append('%s: id ska börja med sitt område' % pid)
        if not re.fullmatch(r'\d+\.\d+\.\d+', p['version']):
            ut.append('%s: version ska vara x.y.z' % pid)
        if p['omrade'] not in OMRADEN:
            ut.append('%s: okänt område %s' % (pid, p['omrade']))
        if not isinstance(p['grund'], bool):
            ut.append('%s: grund ska vara true eller false' % pid)
        elif p['grund'] and p['niva'] == 'utreds':
            ut.append('%s: en utredningsväg kan inte vara grundleverans' % pid)
        if p['niva'] not in NIVAER:
            ut.append('%s: okänd nivå %s' % (pid, p['niva']))
        if p['fardighet'] not in FARDIGHET:
            ut.append('%s: okänd färdighet %s' % (pid, p['fardighet']))
        for kalla in p['kallor']:
            if not str(kalla.get('url', '')).startswith('https://') or not _datum(kalla.get('last')):
                ut.append('%s: källa utan https-adress eller läsdatum' % pid)
        for x in p['kraver']:
            if x not in ids and x not in formagor:
                ut.append('%s: kräver okänt paket eller förmåga %s' % (pid, x))
        for x in p['utesluter']:
            if x not in ids:
                ut.append('%s: utesluter okänt paket %s' % (pid, x))
            elif pid not in next(q for q in paket if q['id'] == x).get('utesluter', []):
                ut.append('%s: uteslutningen av %s är inte ömsesidig' % (pid, x))
        if set(p['funktioner']) != set(STEG):
            ut.append('%s: funktioner ska ange %s' % (pid, ', '.join(STEG)))
        for steg, namn in p['funktioner'].items():
            if namn is None:
                continue
            if namn not in FUNKTIONER:
                ut.append('%s: %s pekar på en funktion utanför FUNKTIONER (%s)' % (pid, steg, namn))
            elif importera:
                mod, _, fn = namn.partition('.')
                sys.path.insert(0, str(rot / 'kontroller'))
                try:
                    if not callable(getattr(importlib.import_module(mod), fn, None)):
                        ut.append('%s: %s finns inte' % (pid, namn))
                finally:
                    sys.path.pop(0)
        kostnad = p['kostnad']
        if set(kostnad) != {'modell', 'belopp', 'valuta', 'kalla', 'datum'} or not kostnad.get('modell'):
            ut.append('%s: kostnaden ska ange modell, belopp, valuta, källa och datum' % pid)
        elif kostnad['belopp'] is not None and not (kostnad['valuta'] and str(kostnad['kalla'] or '').startswith('https://') and _datum(kostnad['datum'])):
            ut.append('%s: ett belopp (också 0) kräver valuta, källa och datum; okänt är null' % pid)
        nivaordning = FARDIGHET.index(p['fardighet']) if p['fardighet'] in FARDIGHET else 0
        if p['fardighet'] in ('implementerat', 'kontraktsprovat', 'leverantorsprovat'):
            if not any(p['funktioner'].get(s) for s in ('tillampa', 'prova')):
                ut.append('%s: %s utan körväg (tillampa eller prova)' % (pid, p['fardighet']))
        if p['fardighet'] in ('kontraktsprovat', 'leverantorsprovat'):
            if not p['prov']:
                ut.append('%s: %s utan prov' % (pid, p['fardighet']))
        if p['fardighet'] == 'leverantorsprovat':
            ut.append('%s: leverantörsprovat kräver ett privat leverantörsbevis, som katalogen inte bär än' % pid)
        for f in p['prov']:
            if not (rot / f).is_file():
                ut.append('%s: provet %s finns inte' % (pid, f))
        if p['niva'] == 'utreds' and nivaordning > 0:
            ut.append('%s: ett paket under utredning kan inte vara mer än dokumenterat' % pid)
    for o in OMRADEN:
        if not any(p.get('omrade') == o for p in paket):
            ut.append('%s saknar paket (också en utredningsväg ska stå i katalogen)' % o)
    # inga cykler bland paketberoendena
    graf = {p['id']: [x for x in p.get('kraver', []) if x in ids] for p in paket if 'id' in p}
    try:
        _ordning(graf, list(graf))
    except Fel as e:
        ut.append(str(e))
    return ut


def _ordning(graf, noder):
    ut, tillstand = [], {}

    def besok(n, vag):
        if tillstand.get(n) == 'klar':
            return
        if tillstand.get(n) == 'pagar':
            raise Fel('cirkulärt beroende: %s' % ' → '.join(vag + [n]))
        tillstand[n] = 'pagar'
        for m in sorted(graf.get(n, [])):
            besok(m, vag + [n])
        tillstand[n] = 'klar'
        ut.append(n)
    for n in sorted(noder):
        besok(n, [])
    return ut


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def planera(val, katalog=None, arende=None):
    """Integrationsplanen ur val: [{'omrade', 'paket', 'lage', 'instans'?}]. arende: {'id', 'revision'} binder planen.
    Bara kundval och grundleveransen ingår i omfattningen; önskemål och framtida står som sådana. Inga sidoeffekter."""
    k = katalog or las()
    paket = {p['id']: p for p in k['paket']}
    ut = {'schema': 1, 'katalog': k['version'], 'arende': arende, 'omfattning': [], 'ovriga': [], 'hinder': [],
          'konflikter': [], 'saknade_beroenden': [], 'ordning': [], 'andringar': {'brief': [], 'design': [], 'kod': [], 'externt': []},
          'konton': [], 'kostnader': [], 'manniska': [], 'prov': [], 'begransningar': [], 'avveckling': []}
    valda, sedda = [], set()
    for v in val:
        if v.get('lage') not in LAGEN:
            ut['hinder'].append('okänt läge för %s: %s' % (v.get('paket'), v.get('lage')))
            continue
        p = paket.get(v.get('paket'))
        if not p:
            ut['hinder'].append('okänt paket %s: utred behovet i stället för att hitta på en leverantör' % v.get('paket'))
            continue
        if p['omrade'] != v.get('omrade'):
            ut['hinder'].append('%s hör till %s, inte %s' % (p['id'], p['omrade'], v.get('omrade')))
            continue
        if v['lage'] == 'grund' and not p['grund']:
            ut['hinder'].append('%s ingår inte i grundleveransen: kunden väljer det' % p['id'])
            continue
        nyckel = (p['id'], v.get('instans') or '')
        if nyckel in sedda:
            ut['hinder'].append('%s valt två gånger utan egen instans' % p['id'])
            continue
        sedda.add(nyckel)
        post = {'omrade': p['omrade'], 'paket': p['id'], 'version': p['version'], 'instans': v.get('instans'), 'lage': v['lage'],
                'niva': p['niva'], 'fardighet': p['fardighet'], 'fardighet_omfattning': p['fardighet_omfattning']}
        (ut['omfattning'] if v['lage'] in OMFATTNING else ut['ovriga']).append(post)
        if v['lage'] in OMFATTNING:
            valda.append(p)
    valda.sort(key=lambda p: (p['omrade'], p['id']))  # valens ordning ändrar inte planen
    vid = {p['id'] for p in valda}
    formagor = {f for p in valda for f in p['formagor']}
    for p in valda:
        for x in p['kraver']:
            if x not in vid and x not in formagor:
                ut['saknade_beroenden'].append({'paket': p['id'], 'kraver': x})
        for x in p['utesluter']:
            if x in vid and p['id'] < x:
                ut['konflikter'].append({'paket': [p['id'], x], 'skal': 'utesluter varandra; välj ett'})
        if p['niva'] == 'utreds':
            ut['hinder'].append('%s är en utredningsväg: kvalificera en leverantör före bygget' % p['id'])
        for falt in ('brief', 'design', 'kod', 'externt'):
            if p['paverkar'].get(falt):
                ut['andringar'][falt].append({'paket': p['id'], 'andring': p['paverkar'][falt]})
        ut['konton'].append({'paket': p['id'], **p['konto'], 'rattigheter': p['rattigheter']})
        kostnad = dict(p['kostnad'], paket=p['id'], kand=p['kostnad']['belopp'] is not None)
        ut['kostnader'].append(kostnad)
        ut['manniska'] += [{'paket': p['id'], 'handling': h} for h in p['manniska']]
        ut['prov'] += [{'paket': p['id'], 'prov': f} for f in p['prov']]
        if p['driftkontroll']:
            ut['prov'].append({'paket': p['id'], 'driftkontroll': p['driftkontroll']})
        ut['begransningar'] += [{'paket': p['id'], 'begransning': b} for b in p['begransningar']]
        ut['avveckling'].append({'paket': p['id'], 'funktion': p['funktioner']['avveckla'],
                                 'besked': 'ingen avvecklingsfunktion: avvecklingen är en mänsklig handling' if not p['funktioner']['avveckla'] else None})
    graf = {p['id']: [x for x in p['kraver'] if x in vid] for p in valda}
    try:
        ut['ordning'] = _ordning(graf, list(graf))
    except Fel as e:
        ut['hinder'].append(str(e))
    ut['hinder'] = sorted(set(ut['hinder']))
    ut['okand_kostnad'] = sorted(c['paket'] for c in ut['kostnader'] if not c['kand'])
    ut['klar_for_bygge'] = not (ut['hinder'] or ut['konflikter'] or ut['saknade_beroenden'])
    for lista in ('omfattning', 'ovriga'):
        ut[lista].sort(key=lambda x: (x['omrade'], x['paket'], x['instans'] or ''))
    ut['plan_sha256'] = sha({x: y for x, y in ut.items() if x != 'plan_sha256'})
    return ut


def main(argv=None):
    a = argparse.ArgumentParser(prog='integrationskatalog', description=__doc__.split('\n\n')[0])
    a.add_argument('--prova', action='store_true')
    a.add_argument('--plan')
    a.add_argument('--katalog', default=str(KATALOG))
    x = a.parse_args(argv)
    k = las(x.katalog)
    if x.prova:
        b = brister(k)
        for r in b:
            print('FEL ' + r)
        print('katalogen %s: %d områden, %d paket, %s' % (k.get('version'), len(k.get('omraden', [])), len(k.get('paket', [])),
                                                       'giltig' if not b else '%d brister' % len(b)))
        return 0 if not b else 1
    if x.plan:
        print(json.dumps(planera(json.loads(Path(x.plan).read_text(encoding='utf-8')), k), ensure_ascii=False, indent=1))
        return 0
    a.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
