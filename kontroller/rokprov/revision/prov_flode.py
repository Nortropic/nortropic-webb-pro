#!/usr/bin/env python3
"""prov_flode.py — dashboardens flödesvy (ägarens tillägg 2026-10-06, punkt 4), syntetiskt men i de riktiga filernas
form. Varje fall fäller en brist som granskningen av r96 eller omgranskningen fann (B1–B3, R1–R4, R2-rest, BÖR 1–3):

- det tänkta flödet ur README:s tabell "Kedjan från kundunderlag till leverans": en syntetisk tabell och repots egen
  README (nio steg); en rad utan fyra celler gör tabellen oläslig i stället för att tappas;
- blindningen (R4): före ditt första val i körningen ger samma fixtur samma utdata med och utan de dolda fälten (titlar,
  brister, DESIGN.md-fel, skisskritik, riktning), så att också en omformulerad läcka syns; före det blinda A/B-valet
  skiljer ingenting armarna åt (R3). Detektorn letar dessutom i den oförändrade utdatan efter de märkta texterna och
  prövas själv mot en läcka; efter valet ska bristerna och armarnas skillnader synas;
- stegen är bundna till körningen (B2): en tidigare körnings dom (också samma dygn som planen, och i det äldre
  flödet), bygge, dom över bygget och export är aldrig beslutade eller kontrollerade; förra körningens plan räknas inte
  i en ny körning som ännu inte arkiverat den, men en start som startkontrollen stoppade lämnar förra körningens läge
  som det senaste (steg 2 stoppat med skälet, ditt val efter stoppet syns); ett bygge från före godkännandet är
  inaktuellt, en dom över ett annat bygge väntar och en export före bygget är inaktuell;
- ett äldre helbygge utan slutpost och kompetensbevis är aldrig kontrollerat; korsluts äldre tekniska/designprövning
  redovisas fortfarande (B1): taket, avstängd granskning, underkänd granskning
  vid taket, stoppvaktens besked från en annan kor.sh-körning och en godkänd rotfil när omgången inte är klar räcker
  inte; godkännandet prövas som kor.sh prövar det, också i det äldre flödet (R1);
- förfiningen (R2): utan ny version är den underkänd, också när den föll med ett undantag (med kandidatens skäl, annars
  inte observerad); bara körningen som bär valet (statusens dom) är valets förfining, så utforskningen som fortsätter
  efter valet är varken pågående eller underkänd; en förfining för ett tidigare val räknas inte, medan den pågår pågår
  den, också när en annan kandidat är klar eller en vald väntar på sin tur, och med körningen stoppad eller arbetaren
  död är den stoppad; godkännandet väntar bara när det finns något förfinat att godkänna;
- Figma-piloten (B3): "kontrollerat" och "underkänt" bara när den aktuella versionen själv är bedömd, varje bild och
  bedömning bär versionen ur sitt katalog- eller filnamn, och vyns bildtext visar den; pilotens katalog är ingen kund;
- symlänkar: en länkad fil i underlaget eller en länkad bildkatalog i piloten visas inte;
- rutterna (/api/flode, /api/flode/<slug>, 404) och länkarna: varje länk vyn ger öppnas genom /fil/.

    .venv/bin/python kontroller/rokprov/revision/prov_flode.py <repo>

Allt skrivs i en temporär katalog; det riktiga underlaget rörs inte. Varje fel skrivs ut, och slutkoden är 1 om något
fall föll.
"""
import contextlib
import http.client
import http.server
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import zlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-flode-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_flode')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
import atelje  # noqa: E402
import granska  # noqa: E402
import kandidater  # noqa: E402
import prova  # noqa: E402
import server as dash  # noqa: E402
import skapande  # noqa: E402

U, K = TMP / 'underlag', TMP / 'kunder'
U.mkdir()
K.mkdir()
dash.ROOT, dash.UNDERLAG, dash.KUNDER, dash.AB = TMP, U, K, K / 'ab'
atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER = TMP, U, K  # bildvägarna blir relativa, som i dashboarden
granska.UNDERLAG, granska.KUNDER = U, K
skapande.UNDERLAG = U
fel = []


def kontroll(villkor, text):
    if not villkor:
        fel.append(text)


@contextlib.contextmanager
def fall(namn):
    try:
        yield
    except Exception as e:  # noqa: BLE001 — ett undantag är ett fallerat fall, inte ett avbrutet prov
        fel.append('%s: undantag %s: %s' % (namn, type(e).__name__, str(e)[:300]))


def skriv(p, data, tid=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        p.write_bytes(data)
    else:
        p.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    if tid:
        t = datetime.strptime(tid, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp()
        os.utime(p, (t, t))
    return p


def png():
    return b'\x89PNG\r\n\x1a\n' + b''.join(struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c)) for t, c in (
        (b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)), (b'IDAT', zlib.compress(b'\x00\xff\x00\x00')), (b'IEND', b'')))


def stegen(s):
    return {x['nr']: x for x in dash.flode(s)['steg']}


def statusar(s):
    return [stegen(s)[n]['status'] for n in range(1, 10)]


def texter(steg_, falt):
    return [x['text'] if isinstance(x, dict) else str(x) for x in steg_.get(falt) or []]


# Blindningens detektor (R4): letar i den oförändrade utdatan efter planens titlar, kandidaternas brister och DESIGN.md-fel
# (texterna, som fixturerna märker HEMLIG-, eller deras antal) och rapporten. Ingenting tas bort före sökningen.
ANTAL_BRISTER = re.compile(r'\d+ brister eller DESIGN\.md-fel')


def lackor(utdata):
    text = utdata if isinstance(utdata, str) else json.dumps(utdata, ensure_ascii=False)
    return sorted(set(re.findall(r'HEMLIG-[A-Z]+', text))) + ANTAL_BRISTER.findall(text)


kontroll(lackor('Förslag B: 1 brister eller DESIGN.md-fel') and lackor('{"titel": "HEMLIG-TITEL k01"}'), 'R4: detektorn ser inte en läcka')

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dash.VARD['tillatna'] = {'127.0.0.1:%d' % srv.server_port}


def hamta(vag):
    c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=20)
    c.request('GET', vag, headers={'Host': '127.0.0.1:%d' % srv.server_port})
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, data


# --- fixturer i de riktiga filernas form ---

def underlag(s):
    for n in ('BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md'):
        skriv(U / s / n, '# %s\n' % n)


def korning(s, **f):
    skriv(U / s / 'atelje' / 'STATUS.json', dict({'slug': s, 'kandidatflode': True, 'lage': 'ny', 'pid': None}, **f))


def plan(s, tid, ids):
    skriv(U / s / 'atelje' / 'KANDIDATPLAN.json', {'tid': tid, 'lage': 'skiss', 'antal': len(ids),
                                                   'kandidater': {k: {'titel': 'HEMLIG-TITEL %s' % k} for k in ids}})


def kandidat(s, kid, status, **f):
    d = U / s / 'atelje' / 'kandidater' / kid
    skriv(d / 'STATUS.json', dict({'id': kid, 'status': status, 'skal': '', 'tid': '2026-10-06T10:20:00Z', 'titel': 'HEMLIG-TITEL %s' % kid,
                                   'logg': [{'tid': '2026-10-06T10:20:00Z', 'status': status, 'skal': ''}]}, **f))
    return d


def dom(s, beslut, tid, kand=()):
    """En dom som atelje.doma skriver den i kandidatflödet: kandidaterna med version, etikett, titel och plan."""
    p = kandidater.plan_tid(s)
    namn = kandidater.etiketter(s, kandidater.lista(s))
    return skapande.lagg_till_dom(s, 'ägaren', beslut, 'Ägarens ord: %s.' % beslut, avser='skapandeflödet, kandidatplanen %s' % p,
                                  underlag=U, tid=tid, plan=p, kandidater=[{'id': k, 'version': v, 'etikett': namn.get(k), 'titel': 'HEMLIG-TITEL %s' % k,
                                                                            'plan': p, 'metod': None} for k, v in kand])


def forra_korningens_dom(s, tid, plan_='2026-10-01T09:00:00Z'):
    skapande.lagg_till_dom(s, 'ägaren', 'valj', 'Förra körningens val.', avser='skapandeflödet, kandidatplanen %s' % plan_,
                           underlag=U, tid=tid, plan=plan_, kandidater=[{'id': 'k01', 'version': 'f0' * 32, 'plan': plan_}])


def utan_dolda(s):
    """Samma fixtur utan det som är dolt före ditt första val: planens och kandidaternas titlar, brister, DESIGN.md-fel,
    skisskritik, granskning, huvudreferens och riktning. Ger en funktion som lägger tillbaka filerna som de var."""
    a_ = U / s / 'atelje'
    filer = [a_ / 'KANDIDATPLAN.json'] + sorted(a_.glob('kandidater/*/*'))
    spar = {p: p.read_bytes() for p in filer if p.is_file()}
    plan_ = json.loads(spar[a_ / 'KANDIDATPLAN.json'])
    for x in (plan_.get('kandidater') or {}).values():
        x.pop('titel', None)
    skriv(a_ / 'KANDIDATPLAN.json', plan_)
    for p in sorted(a_.glob('kandidater/*/STATUS.json')):
        skriv(p, {k_: v_ for k_, v_ in json.loads(spar[p]).items() if k_ not in ('titel', 'brister', 'design_fel', 'skisskritik', 'huvudreferens')})
    for p in sorted(a_.glob('kandidater/*/*')):
        if p.name in ('SKISSKRITIK.json', 'KRITIK.json', 'RIKTNING.md'):
            p.unlink()

    def tillbaka():
        for p, b in spar.items():
            p.write_bytes(b)
    return tillbaka


def utdata(f, s=None):
    """Flödets utdata för en jämförelse: utan läsningens tid, och med kundens namn utbytt när två kunder jämförs."""
    t = json.dumps({k_: v_ for k_, v_ in f.items() if k_ != 'tid'}, ensure_ascii=False, sort_keys=True)
    return t.replace(s, 'KUND') if s else t


GODKAND_SKAL = 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd'


def bygge(s, stampel, provtid, skal=GODKAND_SKAL, slapp=True, ok=True, info=None):
    """Ett helbygge som kor.sh lämnar det: sajten och dist/, körningens logg, rapporten, provet och stoppvaktens besked."""
    k = K / s
    skriv(k / 'sajt' / 'package.json', '{}')
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>%s %s</p>' % (s, stampel))
    h = prova.dist_hash(k / 'sajt' / 'dist')
    skriv(k / ('korning-%s.jsonl' % stampel), '{"type": "result", "subtype": "success", "num_turns": 1, "duration_ms": 1000}\n')
    skriv(k / 'RAPPORT.md', '# Rapport\n\n' + 'Byggets rapport. ' * 30)
    skriv(k / 'prov' / 'STATUS.json', dict({'ok': ok, 'tid': provtid, 'dist_sha256': h, 'grindar': {'bygge': {'ok': ok}, 'lankar': {'ok': True}}},
                                           **({'info': info} if info else {})))
    # rapporten bunden till körningen, som stoppvakten skriver det (ägarens uppdrag 2026-10-07, punkt 5)
    skriv(k / 'prov' / 'STOPPVAKT.json', {'tid': provtid, 'forsok': 1, 'tak': 4, 'korning': stampel, 'dist_sha256': h, 'kontroller_grona': ok,
                                          'rapport_finns': True, 'rapport_sha256': hashlib.sha256((k / 'RAPPORT.md').read_bytes()).hexdigest(),
                                          'rapport_korning': stampel, 'rapport_bunden': 'identitet', 'slapp': slapp, 'skal': skal})
    return h


def granskad(s, stampel, h, godkand=True, utfall='klar'):
    """En granskningsomgång för bygget med den metod som gäller nu, och rotfilen som granska.publicera skriver; giltig när
    utfallet är klar."""
    g = dict(granska.aktuell_metod(s), godkand=godkand, runda=1, dist_sha256=h, korning=stampel, tid='2026-10-06T23:00:00Z')
    gdir = K / s / 'granskning'
    skriv(gdir / 'runda-01' / 'UTFALL.json', {'status': utfall, 'tid': g['tid'], 'skal': ''})
    skriv(gdir / 'runda-01' / 'GRANSKNING.json', g)
    skriv(gdir / 'GRANSKNING.json', g)


# --- det tänkta flödet ---
with fall('kedjan'):
    tabell = ('# Repot\n\n## Kedjan från kundunderlag till leverans\n\nText.\n\n| Steg | Vem startar | Resultat | Saknas i dag |\n'
              '|---|---|---|---|\n| 1. Underlaget | en session: `ny_sajt.py <slug>` | underlag | ett eget kommando |\n'
              '| 2. Prototypen | ägaren: `prototyp.py <slug>` | förslagen | – |\n\n## Nästa avsnitt\n\n| a | b |\n|---|---|\n')
    skriv(TMP / 'README.md', tabell)
    k_ = dash.kedjan()
    kontroll(not k_.get('fel') and [r['steg'] for r in k_['steg']] == ['1. Underlaget', '2. Prototypen'], ('kedjan', k_))
    kontroll('<code>ny_sajt.py &lt;slug&gt;</code>' in k_['steg'][0]['vem'] and k_['steg'][1]['saknas'] == '', ('kodspann och tom cell', k_['steg']))
    skriv(TMP / 'README.md', tabell.replace('| 2. Prototypen | ägaren', '| 2. Prototypen | ägaren | extra'))
    kontroll('fel' in dash.kedjan(), 'en rad med fem celler tappades tyst')
    skriv(TMP / 'README.md', '# Repot\n')
    kontroll('fel' in dash.kedjan(), 'README utan kedjan')
with fall('R4 README'):  # repots egen README, så att en ändring som bryter vyn ger rött
    dash.ROOT = ROOT
    try:
        k_ = dash.kedjan()
    finally:
        dash.ROOT = TMP
    kontroll(not k_.get('fel') and len(k_.get('steg') or []) == 9 and k_['steg'][0]['steg'].startswith('1. Kundunderlaget')
             and k_['steg'][-1]['steg'].startswith('9. Leveransen'), ('R4: repots README läses inte som nio steg', k_.get('fel') or [r['steg'][:30] for r in k_['steg']]))

# --- R4: blindningen före ditt första val, och efter ---
s = 'fl-blind'
underlag(s)
forra_korningens_dom(s, '2026-10-01T09:30:00Z')
forra_korningens_dom(s, '2026-10-06T05:17:00Z', '2026-10-06T04:50:00Z')  # samma dygn som planen, som i de riktiga data (05:17Z, plan 18:45Z)
korning(s, steg='klar_for_bedomning', startad='2026-10-06T10:00:00Z', klar='2026-10-06T10:50:00Z')
plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
d1 = kandidat(s, 'k01', 'klar', version='a1' * 32, varv=3, brister=['HEMLIG-BRIST ett'], design_fel=['HEMLIG-DESIGNFEL ett'])
skriv(d1 / 'SKISSKRITIK.json', {'storsta_problem': 'HEMLIG-KRITIK'})
skriv(d1 / 'KRITIK.json', {'niva': 'nastan', 'forsta_intryck': 'HEMLIG-KRITIK första intrycket', 'helhet': 'HEMLIG-KRITIK helheten',
                           'version': 'a1' * 32, 'modell': 'opus', 'last': True})  # granskningens nivå: läcker den syns det bara i jämförelsen
skriv(d1 / 'RIKTNING.md', '# HEMLIG-TITEL riktning\n')
for vy in ('390', '1440'):
    skriv(d1 / 'bilder' / 'start' / ('vy-%s-forsta.png' % vy), png())
kandidat(s, 'k02', 'under_arbete')
with fall('R4 före första valet'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    kontroll(f['blind'] and not lackor(f), ('R4: läcka före ditt första val', lackor(f)))
    kontroll([x['nr'] for x in f['steg']] == list(range(1, 10)), 'nio steg')
    kontroll((st[1]['status'], st[2]['status'], st[3]['status']) == ('skapat', 'skapat', 'väntar på ägaren'), [(x['nr'], x['status']) for x in f['steg']])
    kontroll(not st[3]['beslut'] and any('hör inte till den här körningen' in t for t in texter(st[3], 'underlag')), ('B2: förra körningens dom', st[3]))
    kontroll(any('1 av 2 förslag' in t for t in texter(st[2], 'kontroller')), st[2]['kontroller'])
    lankar = [x['lank'] for x in st[2]['utfall'] if x.get('lank')]
    kontroll(lankar == ['/fil/underlag/fl-blind/atelje/kandidater/k01/bilder/start/vy-1440-forsta.png'], ('bildvägen är relativ och tillåten', lankar))
    # länken följer fil_tillaten: före valet bara skärmbilderna, aldrig skaparens anteckningar (M14)
    kontroll(dash._fil(d1 / 'RIKTNING.md')['lank'] is None and dash._fil(d1 / 'bilder' / 'start' / 'vy-1440-forsta.png')['lank'], 'R4: en länk förbi fil_tillaten')
with fall('R4 samma fixtur utan de dolda fälten'):  # också en omformulerad läcka syns som en skillnad (omgranskningen, BÖR 3)
    med = dash.flode(s)
    tillbaka = utan_dolda(s)
    try:
        utan = dash.flode(s)
    finally:
        tillbaka()
    kontroll(utdata(med) == utdata(utan), ('R4: utdatan före ditt första val beror på dolda fält',
                                           [(x['nr'], texter(x, 'utfall') + texter(x, 'kontroller') + texter(x, 'brister')) for x in med['steg'] if x not in utan['steg']]))
    kontroll(utdata(dash.flode(s)) == utdata(med), 'fixturen är inte tillbakalagd')
dom(s, 'valj', '2026-10-06T11:00:00Z', [('k01', 'a1' * 32)])
with fall('R4 efter första valet'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    etikett = kandidater.etiketter(s, ['k01', 'k02'])['k01']
    kontroll(not f['blind'] and st[3]['status'] == 'beslutat' and len(st[3]['beslut']) == 1 and etikett in st[3]['beslut'][-1]['text']
             and 'a1a1a1a1a1a1' in st[3]['beslut'][-1]['text'], st[3])
    kontroll(ANTAL_BRISTER.search(json.dumps(f, ensure_ascii=False)), ('R4: bristerna syns inte efter valet (detektorns motprov)', st[2]['brister']))
    kontroll('HEMLIG-TITEL' not in json.dumps(f, ensure_ascii=False), 'planens titlar visas aldrig i flödet')
    # ett val startar inget (ägarens uppdrag 2026-10-09, punkt 8): nästa steg är ett uppdrag, inte en förfining av de valda
    kontroll('valda' not in st[3]['nasta'] and st[4]['status'] == 'inte påbörjat' and st[5]['status'] == 'inte påbörjat', (st[3]['nasta'], st[4]['status'], st[5]['status']))

# --- R3: före det blinda A/B-valet skiljer ingenting armarna åt ---
AB = 'ab-prov-20261006T000000Z'
skriv(K / 'ab' / ('%s.json' % AB), {'id': AB, 'byggen': ['ab-x', 'ab-y'], 'val': None, 'variabel': 'atelje', 'verksamhet': 'Prov'})
for s, andra, atel in (('ab-x', 'ab-y', True), ('ab-y', 'ab-x', False)):
    underlag(s)
    skriv(K / s / 'AB-SYSKON', andra + '\n')
    h = bygge(s, '20261006T090000Z', '2026-10-06T09:30:00Z', skal=GODKAND_SKAL if atel else 'blockerad', slapp=atel)
    skriv(K / s / 'RAPPORT.md', '# HEMLIG-RAPPORT\n\n' + 'Armens rapport. ' * 30)
    if atel:  # ateljéarmen: en granskning, och ett beslutat förslag med brister
        granskad(s, '20261006T090000Z', h)
        korning(s, steg='klar_for_bedomning', startad='2026-10-06T07:00:00Z')
        plan(s, '2026-10-06T07:05:00Z', ['k01'])
        kandidat(s, 'k01', 'klar', version='ab' * 32, brister=['HEMLIG-BRIST arm'])
        dom(s, 'valj', '2026-10-06T07:30:00Z', [('k01', 'ab' * 32)])


def arm(f, s):
    return json.dumps({k_: v_ for k_, v_ in f.items() if k_ != 'tid'}, ensure_ascii=False, sort_keys=True).replace(s, 'ARM')


with fall('R3 före A/B-valet'):
    fx, fy = dash.flode('ab-x'), dash.flode('ab-y')
    kontroll(arm(fx, 'ab-x') == arm(fy, 'ab-y'), ('R3: armarna skiljer sig åt före det blinda valet', [x['status'] for x in fx['steg']], [x['status'] for x in fy['steg']]))
    kontroll(not lackor(fx) and not lackor(fy), ('R3: läcka före det blinda valet', lackor(fx), lackor(fy)))
    kod, data = hamta('/api/flode/ab-x')
    kontroll(kod == 200 and json.loads(data).get('ab_dold') is True, ('R3: rutten visar armen', kod, data[:200]))
skriv(K / 'ab' / ('%s.json' % AB), {'id': AB, 'byggen': ['ab-x', 'ab-y'], 'val': 'ab-x', 'variabel': 'atelje', 'verksamhet': 'Prov'})
with fall('R3 efter A/B-valet'):  # motprov: efter valet syns det som skiljer, också bristerna
    fx, fy = dash.flode('ab-x'), dash.flode('ab-y')
    kontroll(arm(fx, 'ab-x') != arm(fy, 'ab-y') and ANTAL_BRISTER.search(json.dumps(fx, ensure_ascii=False)), 'R3: armarna visas inte efter valet')

# --- B2: en ny körning i planfasen räknar inte förra körningens dom ---
s = 'b2-planfas'
underlag(s)
forra_korningens_dom(s, '2026-10-05T10:00:00Z')
korning(s, steg='plan', startad='2026-10-06T10:00:00Z')
with fall('B2 planfas'):
    st = stegen(s)
    kontroll(st[3]['status'] == 'inte påbörjat' and not st[3]['beslut'], ('B2: förra körningens dom är beslutad i den nya körningen', st[3]['status'], st[3]['beslut']))

# --- B2: en ny körning med förra körningens bygge, dom och export kvar i kunder/ ---
# Exporter utan versionskvitto är nu alltid 'inte observerat': filtid bevisar varken
# innehåll eller kontroller. prov_exportovergang prövar nya kvitton och inaktuell hash.
s = 'b2-korsvis'
underlag(s)
h = bygge(s, '20261001T110000Z', '2026-10-01T12:00:00Z')
granskad(s, '20261001T110000Z', h)
skriv(K / s / 'DOM.json', {'schema': 1, 'slug': s, 'domar': [{'tid': '2026-10-01T13:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, som den är'}}]})
skriv(K / s / 'kundrepo' / 'package.json', '{}', tid='2026-10-01T14:00:00Z')
korning(s, steg='klar_for_bedomning', startad='2026-10-06T10:00:00Z', klar='2026-10-06T10:50:00Z')
plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='c1' * 32)
kandidat(s, 'k02', 'klar', version='c2' * 32)
with fall('B2 korsvis'):
    f = dash.flode(s)
    kontroll([x['status'] for x in f['steg']][2:] == ['väntar på ägaren', 'inte påbörjat', 'inte påbörjat', 'inaktuellt', 'inaktuellt', 'inte observerat', 'inte observerat'],
             ('B2: förra körningens bygge, dom och export visas som den här körningens', [x['status'] for x in f['steg']]))
    kontroll(f['blind'] and not lackor(f), ('R4: läcka före första valet', lackor(f)))

# --- B1: äldre helbygge utan slutpost/kompetensbevis blir aldrig kontrollerat ---
for s, skal, g_ in (('b1-tak', 'släppt utan godkänd granskning: taket för granskningar i körningen är nått och ingen giltig granskning gäller det slutliga bygget', True),
                    ('b1-avstangd', 'kontrollerna gröna, RAPPORT.md finns och granskningen är avstängd', None),
                    ('b1-underkand', 'stoppvaktens tak nått: avslutet släpptes med granskning underkänd', False)):
    h = bygge(s, '20261006T120000Z', '2026-10-06T12:30:00Z', skal=skal)
    if g_ is not None:  # vid taket gäller den godkända omgången ett tidigare bygge; vid stoppvaktens tak underkände den
        granskad(s, '20261006T120000Z', 'ff' * 32 if g_ else h, godkand=g_)
    with fall('B1 ' + s):
        st = stegen(s)
        kontroll(st[6]['status'] == 'skapat' and any('korslut godkänner inte' in t for t in texter(st[6], 'brister')),
                 ('B1: släppt utan godkänd granskning visas som kontrollerat', s, st[6]['status']))
s = 'b1-godkand'
h = bygge(s, '20261006T120000Z', '2026-10-06T12:30:00Z', info={'vinnare': 'första vyn avviker 2 % från vinnaren'})
granskad(s, '20261006T120000Z', h)
with fall('B1 godkänt bygge'):
    st = stegen(s)
    kontroll(st[6]['status'] == 'inte observerat' and st[7]['status'] == 'väntar på ägaren', (st[6]['status'], st[6]['brister'], st[7]['status']))
    kontroll(any('kompetensbevis saknas' in t for t in texter(st[6], 'brister')), ('B1: äldre material upphöjs till verifierat', st[6]['brister']))
    # provets pixeljämförelse mot vinnaren är ingen identitet för godkännandet (R1)
    kontroll(any('vilket godkännande' in t for t in texter(st[6], 'brister')), ('R1: provets jämförelse med vinnaren döljer att godkännandet inte är bundet', st[6]['brister']))
    kontroll(any('domen visas efter din dom' in t for t in texter(st[6], 'kontroller')), st[6]['kontroller'])
s = 'b1-rod'
bygge(s, '20261006T120000Z', '2026-10-06T12:30:00Z', skal='blockerad', slapp=False, ok=False)
s2 = 'b1-borttagen'
bygge(s2, '20261006T120000Z', '2026-10-06T12:30:00Z')
(K / s2 / 'sajt' / 'package.json').unlink()
with fall('B1 rött och borttaget'):
    kontroll(stegen(s)[6]['status'] == 'underkänt', 'ett rött prov')
    kontroll(stegen(s2)[6]['status'] == 'inaktuellt', 'ett prov för en borttagen sajt')
# ett nytt kor.sh-bygge har startat (en ny logg); provet, stoppvakten och granskningen är det förra byggets
s = 'b1-ny-korning'
h = bygge(s, '20261006T120000Z', '2026-10-06T12:30:00Z')
granskad(s, '20261006T120000Z', h)
skriv(K / s / 'korning-20261006T150000Z.jsonl', '{"type": "system", "subtype": "init"}\n')
# kor.sh-körningen granskade bygget efter designsteget, men stoppvaktens besked är det förra byggets
s2 = 'b1-annan-stoppvakt'
h2 = bygge(s2, '20261006T120000Z', '2026-10-06T12:30:00Z')
skriv(K / s2 / 'korning-20261006T150000Z.jsonl', '{"type": "system", "subtype": "init"}\n')
granskad(s2, '20261006T150000Z', h2)
# rotfilen GRANSKNING.json säger godkänd, men omgången är inte klar (granska.utfall: pagar)
s3 = 'b1-rotfil'
h3 = bygge(s3, '20261006T120000Z', '2026-10-06T12:30:00Z')
granskad(s3, '20261006T120000Z', h3, utfall='pagar')
with fall('B1 stoppvakten och omgången'):
    for s_, vad in ((s, 'ett nytt kor.sh-bygge har startat; stoppvakten och granskningen gäller det förra'),
                    (s2, 'stoppvaktens besked gäller en annan kor.sh-körning än granskningen'),
                    (s3, 'rotfilen är godkänd men omgången är inte klar')):
        st = stegen(s_)
        kontroll(st[6]['status'] == 'skapat' and any('korslut godkänner inte' in t for t in texter(st[6], 'brister')),
                 ('B1: kontrollerat fast %s' % vad, s_, st[6]['status'], st[6]['brister'][:1]))

# --- B2 och R1: ett bygge bundet till körningens godkännande, och vad som bryter bindningen ---
s = 'b2-bunden'
underlag(s)
V1, V2 = 'd1' * 32, 'd2' * 32
korning(s, steg='klar_for_bedomning', fas='forfining', startad='2026-10-06T11:00:00Z', lage='valda', dom='2026-10-06T10:30:00Z',
        valda=['k01'], kandidater={'k01': 'forfinad', 'k02': 'klar'}, klar='2026-10-06T11:40:00Z')
plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version=V1)
kandidat(s, 'k02', 'klar', version='d3' * 32)
dom(s, 'valj', '2026-10-06T10:30:00Z', [('k01', V1)])
kandidat(s, 'k01', 'forfinad', version=V2, forfining={'dom': '2026-10-06T10:30:00Z', 'fran': V1, 'klar': '2026-10-06T11:40:00Z', 'varv': 4}, fordjupad=True)
vin = U / s / 'atelje' / 'vinnare'
skriv(vin / 'kod' / 'index.astro', '<h1>Godkänd startsida</h1>')
skriv(vin / 'DESIGN.md', '# DESIGN\n')
atelje.skriv_vinnare(U / s / 'atelje', {'riktning': 1, 'kandidat': 'k01', 'version': V2, 'plan': '2026-10-06T10:05:00Z', 'tid': '2026-10-06T12:00:00Z'})
gd = dom(s, 'godkand', '2026-10-06T12:00:00Z', [('k01', V2)])
atelje.skriv_vinnare(U / s / 'atelje', atelje.godkannande(s, gd))  # VINNARE.json som atelje.doma skriver den
kandidat(s, 'k01', 'godkand', version=V2, forfining={'dom': '2026-10-06T10:30:00Z', 'fran': V1, 'klar': '2026-10-06T11:40:00Z', 'varv': 4}, fordjupad=True)
h = bygge(s, '20261006T130000Z', '2026-10-06T13:30:00Z')
granskad(s, '20261006T130000Z', h)
with fall('B2 bundet bygge'):
    st = stegen(s)
    kontroll([st[n]['status'] for n in range(3, 8)] == ['beslutat', 'skapat', 'kontrollerat', 'inte observerat', 'väntar på ägaren'],
             ('ett bygge från körningens godkännande', [st[n]['status'] for n in range(1, 10)], st[5]['kontroller'], st[6]['brister']))
skriv(K / s / 'kundrepo' / 'package.json', '{}', tid='2026-10-06T12:30:00Z')  # efter körningens start, före byggets (B2-4)
with fall('B2 export före bygget'):
    st = stegen(s)
    kontroll((st[8]['status'], st[9]['status']) == ('inte observerat', 'inte observerat'), ('B2: en export från före bygget är den här körningens', st[8]['status'], st[9]['status']))
skriv(K / s / 'kundrepo' / 'package.json', '{}', tid='2026-10-06T14:00:00Z')
with fall('exporten'):
    st = stegen(s)
    kontroll(st[8]['status'] == 'inte observerat' and any('utan versionskvitto' in t for t in texter(st[8], 'brister')) and st[9]['status'] == 'inte observerat',
             (st[8]['status'], st[8]['brister'], st[9]['status']))
    # M18: migreringsläget med fem skilda besked; utan export är kunden inte påbörjad, och inget steg säger migrerad
    kontroll(any(t.startswith('Migreringsläge: inte påbörjad') for t in texter(st[9], 'kontroller'))
             and [t.split(':')[0] for t in texter(st[9], 'underlag')][-5:] == ['Förberedd', 'Måltestad', 'Trafik flyttad', 'Data avstämd', 'Legacy avvecklad']
             and not any('migrerad:' in t for t in texter(st[9], 'kontroller')), ('M18: migreringsläget i Leveransen', st[9]['kontroller'], st[9]['underlag']))
skriv(K / s / 'DOM.json', {'schema': 1, 'slug': s, 'domar': [{'tid': '2026-10-06T15:00:00Z', 'bygge_dist': 'e0' * 6, 'svar': {'namn': 'Ja, som den är'}}]})
with fall('B2 dom över ett annat bygge'):
    st = stegen(s)
    kontroll(st[7]['status'] == 'väntar på ägaren', ('B2: en dom över ett annat bygge visas som beslutad', st[7]['status']))
    # granskarens dom visas först efter din dom över just det här bygget, inte efter en dom över ett annat
    kontroll(any('domen visas efter din dom' in t for t in texter(st[6], 'kontroller')), ('B2: granskarens dom före din dom över bygget', st[6]['kontroller']))
skriv(K / s / 'DOM.json', {'schema': 1, 'slug': s, 'domar': [{'tid': '2026-10-06T15:00:00Z', 'bygge_dist': 'e0' * 6, 'svar': {'namn': 'Ja, som den är'}},
                                                             {'tid': '2026-10-06T16:00:00Z', 'bygge_dist': h[:12], 'svar': {'namn': 'Ja, efter små ändringar'}}]})
with fall('B2 dom över bygget'):
    st = stegen(s)
    kontroll(st[7]['status'] == 'beslutat' and 'Ja, efter små ändringar' in st[7]['beslut'][-1]['text'], (st[7]['status'], st[7]['beslut']))
    kontroll(any(t.startswith('granskningen') and t.endswith('godkänd') for t in texter(st[6], 'kontroller')), st[6]['kontroller'])
(K / s / 'korning-20261006T130000Z.jsonl').rename(K / s / 'korning-20261006T115900Z.jsonl')  # kor.sh startade före godkännandet
sv = json.loads((K / s / 'prov' / 'STOPPVAKT.json').read_text(encoding='utf-8'))
skriv(K / s / 'prov' / 'STOPPVAKT.json', dict(sv, korning='20261006T115900Z'))
with fall('B2 bygge före godkännandet'):
    st = stegen(s)
    kontroll((st[6]['status'], st[7]['status'], st[8]['status']) == ('inaktuellt', 'inaktuellt', 'inte observerat'),
             ('B2: ett bygge från före godkännandet', st[6]['status'], st[7]['status'], st[8]['status']))
(K / s / 'korning-20261006T115900Z.jsonl').rename(K / s / 'korning-20261006T130000Z.jsonl')
skriv(K / s / 'prov' / 'STOPPVAKT.json', sv)
skriv(vin / 'kod' / 'index.astro', '<h1>Ändrad efter godkännandet</h1>')  # som scenariot s5-godkand: kor.sh vägrar bygga
with fall('R1 ändrad vinnare'):
    st = stegen(s)
    kontroll(st[5]['status'] == 'inaktuellt' and any('ändrad' in t for t in texter(st[5], 'kontroller')), ('R1: ett godkännande som kor.sh nekar', st[5]['status'], st[5]['kontroller']))
    kontroll(st[6]['status'] == 'inte observerat', ('ett bygge utan giltigt godkännande', st[6]['status']))

# --- R1: det äldre flödet, ett godkännande utan kandidat ---
s = 'r1-aldre'
underlag(s)
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'steg': 'klar', 'startad': '2026-10-06T09:00:00Z', 'lage': 'ny', 'klar': '2026-10-06T09:40:00Z'})
vin = U / s / 'atelje' / 'vinnare'
skriv(vin / 'kod' / 'index.astro', '<h1>Ateljéns vinnare</h1>')
skriv(vin / 'DESIGN.md', '# DESIGN\n')
skriv(K / s / 'sajt' / 'src' / 'pages' / 'index.astro', '<h1>Ateljéns vinnare</h1>')
atelje.skriv_vinnare(U / s / 'atelje', {'riktning': 2, 'tid': '2026-10-06T09:40:00Z'})
gd = skapande.lagg_till_dom(s, 'ägaren', 'godkand', 'Godkänd.', avser='skapandeflödet, körningen 2026-10-06T09:00:00Z', underlag=U, tid='2026-10-06T10:00:00Z')
atelje.skriv_vinnare(U / s / 'atelje', atelje.godkannande(s, gd))
with fall('R1 äldre flödet'):
    st = stegen(s)
    kontroll(st[3]['status'] == 'beslutat' and st[5]['status'] == 'kontrollerat', ('R1: ett godkännande utan kandidat', st[3]['status'], st[5]['status'], st[5]['kontroller']))
skriv(vin / 'kod' / 'index.astro', '<h1>Ändrad efter godkännandet</h1>')
with fall('R1 äldre flödet, ändrad vinnare'):
    st = stegen(s)
    kontroll(st[5]['status'] == 'inaktuellt', ('R1: ett godkännande i det äldre flödet som kor.sh nekar', st[5]['status'], st[5]['kontroller']))

# --- B2: det äldre flödet, bara förra körningens dom (avser en annan körnings starttid) ---
s = 'b2-aldre-forra'
underlag(s)
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'steg': 'klar', 'startad': '2026-10-06T09:00:00Z', 'lage': 'ny', 'klar': '2026-10-06T09:40:00Z'})
skapande.lagg_till_dom(s, 'ägaren', 'putsa', 'Putsa vidare.', avser='skapandeflödet, körningen 2026-10-01T09:00:00Z', underlag=U, tid='2026-10-01T10:00:00Z')
with fall('B2 äldre flödet, förra körningens dom'):
    st = stegen(s)
    kontroll(st[3]['status'] == 'väntar på ägaren' and not st[3]['beslut'], ('B2: förra körningens dom är beslutad i det äldre flödet', st[3]['status'], st[3]['beslut']))

# --- B2: en ny körning (läget ny) innan arbetaren har arkiverat förra körningens plan, val och godkännande ---
s = 'b2-om'
underlag(s)
V1, V2 = 'b1' * 32, 'b2' * 32
korning(s, steg='klar_for_bedomning', fas='forfining', startad='2026-10-05T11:00:00Z', lage='valda', dom='2026-10-05T10:30:00Z', valda=['k01'])
plan(s, '2026-10-05T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version=V1)
kandidat(s, 'k02', 'klar', version='b3' * 32)
dom(s, 'valj', '2026-10-05T10:30:00Z', [('k01', V1)])
kandidat(s, 'k01', 'forfinad', version=V2, forfining={'dom': '2026-10-05T10:30:00Z', 'fran': V1, 'klar': '2026-10-05T11:40:00Z', 'varv': 4})
vin = U / s / 'atelje' / 'vinnare'
skriv(vin / 'kod' / 'index.astro', '<h1>Godkänd</h1>')
skriv(vin / 'DESIGN.md', '# DESIGN\n')
atelje.skriv_vinnare(U / s / 'atelje', {'riktning': 1, 'kandidat': 'k01', 'version': V2, 'plan': '2026-10-05T10:05:00Z', 'tid': '2026-10-05T12:00:00Z'})
atelje.skriv_vinnare(U / s / 'atelje', atelje.godkannande(s, dom(s, 'godkand', '2026-10-05T12:00:00Z', [('k01', V2)])))
# som atelje.arbeta skriver den nya körningens STATUS före startkontrollen och arkiveringen (--om)
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T10:00:00Z', 'modell': 'x', 'effort': 'max', 'antal': 3, 'lage': 'ny',
                                         'steg': 'startkontroll', 'pid': os.getpid(), 'faser': {}, 'kandidatflode': True})
with fall('B2 ny körning med förra körningens plan kvar'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    kontroll((st[3]['status'], st[4]['status']) == ('inte påbörjat', 'inte påbörjat') and not st[3]['beslut'] and f['blind'],
             ('B2: förra körningens val är beslutade i den nya körningen', st[3]['status'], st[3]['beslut'], st[4]['status'], f['blind']))
    kontroll(not st[2]['utfall'] and any('förra körningens plan' in t for t in texter(st[2], 'underlag')) and st[5]['status'] == 'inaktuellt',
             ('förra körningens förslag och godkännande', st[2]['utfall'], st[2]['underlag'], st[5]['status']))

# --- B2: en --om-start som startkontrollen stoppade arkiverar ingenting: förra körningens läge är det senaste ---
s = 'b2-om-stopp'
underlag(s)
korning(s, steg='klar_for_bedomning', startad='2026-10-05T10:00:00Z', klar='2026-10-05T10:50:00Z')
plan(s, '2026-10-05T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='d1' * 32)
kandidat(s, 'k02', 'klar', version='d2' * 32)
kandidater.efter_beslut(s, dom(s, 'valj', '2026-10-05T10:30:00Z', [('k01', 'd1' * 32)]))
STOPP = 'Startkontrollen stoppade starten: node svarar inte (underlag/b2-om-stopp/atelje/STARTKVITTO-STOPP.md)'
# atelje.arbeta: förälderns status (steg startar, läge ny, ny starttid) skrivs tillbaka med startkontroll_stopp
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'steg': 'startar', 'lage': 'ny', 'kandidatflode': True,
                                         'modell': 'opus', 'effort': 'max', 'antal': 3,
                                         'startkontroll_stopp': {'tid': '2026-10-06T09:00:10Z', 'fel': STOPP, 'stoppar': ['node svarar inte']}})
with fall('B2 stoppad start, förälderns status'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    kontroll(st[2]['status'] == 'stoppat' and STOPP in texter(st[2], 'brister') and len(st[2]['utfall']) == 2
             and st[3]['status'] == 'beslutat' and not f['blind'],
             ('B2: en stoppad start döljer förra körningen', st[2]['status'], st[2]['brister'], len(st[2]['utfall']), st[3]['status'], f['blind']))
# den andra grenen: steg fel med startkontrollens besked; sedan ditt val av förra körningens förslag i vyn Prototyp
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'steg': 'fel', 'lage': 'ny', 'kandidatflode': True,
                                         'modell': 'opus', 'effort': 'max', 'antal': 3, 'faser': {}, 'fel': STOPP,
                                         'startkontroll': {'status': 'stoppad', 'stoppar': ['node svarar inte']}})
kandidater.efter_beslut(s, dom(s, 'valj', '2026-10-06T09:30:00Z', [('k02', 'd2' * 32)]))
with fall('B2 stoppad start, steg fel och ditt val efter stoppet'):
    st = stegen(s)
    kontroll(st[2]['status'] == 'stoppat' and st[3]['status'] == 'beslutat' and 'd2d2d2d2d2d2' in st[3]['beslut'][-1]['text'] and st[4]['status'] == 'inte påbörjat',
             ('B2: ditt val efter en stoppad start syns inte', st[2]['status'], st[3]['status'], st[3]['beslut'][-1:], st[4]['status']))

# --- GR-20261007-r96-om3 BÖR-1 och BÖR-2: en vanlig körning i steg fel är ingen stoppad start (M3-2), och blindningen
# håller efter en stoppad start över förslag som ingen valt i (M3-5) ---
s = 'm32-fel'
underlag(s)
korning(s, steg='fel', fel='RuntimeError: arbetaren föll', startad='2026-10-06T09:00:00Z')
plan(s, '2026-10-06T09:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='f1' * 32)
kandidat(s, 'k02', 'under_arbete')
s2 = 'm32-fel-forra'  # samma fel före den nya planen: förra körningens plan döljs, som efter varje ny start
underlag(s2)
korning(s2, steg='fel', fel='RuntimeError: arbetaren föll', startad='2026-10-06T09:00:00Z')
plan(s2, '2026-10-05T10:05:00Z', ['k01', 'k02'])
kandidat(s2, 'k01', 'klar', version='f2' * 32)
kandidat(s2, 'k02', 'klar', version='f3' * 32)
with fall('M3-2 en vanlig körning i steg fel räknas inte som en stoppad start'):
    for s_ in (s, s2):
        st = stegen(s_)
        kontroll(st[2]['status'] == 'stoppat' and '--fortsatt' in st[2]['nasta'] and 'Startkontrollen' not in st[2]['nasta']
                 and 'RuntimeError: arbetaren föll' in texter(st[2], 'brister'),
                 ('M3-2: en vanlig körning i steg fel fick startkontrollens besked', s_, st[2]['status'], st[2]['nasta'], st[2]['brister']))
    f = dash.flode(s2)
    kontroll(f['blind'] and not lackor(f), ('M3-2: förra körningens plan efter ett vanligt fel', f['blind'], lackor(f)))
s = 'm35-stopp'
underlag(s)
korning(s, steg='klar_for_bedomning', startad='2026-10-05T10:00:00Z', klar='2026-10-05T10:50:00Z')
plan(s, '2026-10-05T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='g1' * 32, brister=['HEMLIG-BRIST k01'])
kandidat(s, 'k02', 'klar', version='g2' * 32)
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'steg': 'startar', 'lage': 'ny', 'kandidatflode': True,
                                         'modell': 'opus', 'effort': 'max', 'antal': 3,
                                         'startkontroll_stopp': {'tid': '2026-10-06T09:00:10Z', 'fel': 'Startkontrollen stoppade starten: prov',
                                                                 'stoppar': ['prov']}})
with fall('M3-5 blindningen håller efter en stoppad start över förslag som ingen valt i'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    kontroll(st[2]['status'] == 'stoppat' and f['blind'] and not lackor(f) and st[3]['status'] == 'inte påbörjat',
             ('M3-5: blindningen hävdes efter en stoppad start', st[2]['status'], f['blind'], lackor(f), st[3]['status']))
    status_, data_ = hamta('/api/flode/%s' % s)
    kontroll(status_ == 200 and not lackor(data_.decode('utf-8')), ('M3-5: API:t', status_, lackor(data_.decode('utf-8', 'replace'))))

# --- R2: förfiningen efter valet ---
VAL = '2026-10-06T10:30:00Z'
EFTER = dict(startad='2026-10-06T11:00:00Z', lage='valda', dom=VAL, valda=['k01'])


def forfiningsfall(s, run, kstatus, **kf):
    underlag(s)
    korning(s, **dict(EFTER, **run))
    plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
    kandidat(s, 'k01', 'klar', version='e1' * 32)
    kandidat(s, 'k02', 'klar', version='e2' * 32)
    dom(s, 'valj', VAL, [('k01', 'e1' * 32)])
    kandidat(s, 'k01', kstatus, agarens_dom=VAL, **kf)


KLAR = dict(steg='klar_for_bedomning', fas='forfining', klar='2026-10-06T11:40:00Z')
forfiningsfall('r2-fallen', dict(KLAR, kandidater={'k01': 'vald', 'k02': 'klar'}), 'vald', version='e1' * 32,
               skal='förfiningen gav ingen användbar version (sessionen slutade); den valda versionen står kvar',
               forfining={'dom': VAL, 'fran': 'e1' * 32, 'klar': '2026-10-06T11:40:00Z', 'avbruten': 'RuntimeError: x', 'varv': 0})
forfiningsfall('r2-pagar', dict(steg='forfina', pid=os.getpid()), 'under_arbete', version='e1' * 32,
               forfining_pagar={'dom': VAL, 'fran': 'e1' * 32, 'start_varv': 3})
forfiningsfall('r2-stoppad', dict(steg='fel', fel='RuntimeError: arbetaren föll'), 'under_arbete', version='e1' * 32,
               forfining_pagar={'dom': VAL, 'fran': 'e1' * 32, 'start_varv': 3})
forfiningsfall('r2-klar', dict(KLAR, kandidater={'k01': 'forfinad', 'k02': 'klar'}), 'forfinad', version='e9' * 32,
               forfining={'dom': VAL, 'fran': 'e1' * 32, 'klar': '2026-10-06T11:40:00Z', 'varv': 4}, fordjupad=True)
with fall('R2 förfiningen'):
    kontroll(statusar('r2-fallen')[3:5] == ['underkänt', 'inte påbörjat'], ('R2: en förfining utan ny version', statusar('r2-fallen')))
    kontroll(statusar('r2-pagar')[3] == 'pågår' and any('pågår' in t for t in texter(stegen('r2-pagar')[4], 'utfall')),
             ('R2: en förfining som pågår', statusar('r2-pagar'), stegen('r2-pagar')[4]['utfall']))
    kontroll(statusar('r2-stoppad')[3] == 'stoppat', ('R2: en förfining som stannade med körningen', statusar('r2-stoppad')))
    kontroll(statusar('r2-klar')[3:5] == ['skapat', 'väntar på ägaren'], ('en förfining med ny version', statusar('r2-klar')))
# en förfining som föll med ett undantag: kandidater.forfina_valda återställer kandidaten till vald med skälet (satt_status
# skriver tiden), utan någon förfiningspost för valet, och körningen slutar klar_for_bedomning (omgranskningen, R2-rest)
FALLEN = dict(KLAR, kandidater={'k01': 'vald', 'k02': 'klar'}, skal='0 av 1 valda kandidater förfinade; ägaren bedömer dem och godkänner en för helbygget')
forfiningsfall('r2-undantag', FALLEN, 'vald', version='e1' * 32, tid='2026-10-06T11:40:00Z',
               skal='förfiningen föll (RuntimeError: bygget föll); den valda versionen är återställd')
forfiningsfall('r2-aterstallning', FALLEN, 'vald', version='e1' * 32, tid='2026-10-06T11:40:00Z',
               skal='förfiningen föll (RuntimeError: bygget föll) och återställningen föll (OSError: disken); nästa förfining börjar från den valda versionen',
               forfining_pagar={'dom': VAL, 'fran': 'e1' * 32, 'start_varv': 3})
forfiningsfall('r2-utan-skal', FALLEN, 'vald', version='e1' * 32, tid='2026-10-06T11:40:00Z', skal='')
with fall('R2 förfiningen som föll med ett undantag'):
    st = stegen('r2-undantag')
    kontroll((st[4]['status'], st[5]['status']) == ('underkänt', 'inte påbörjat') and any('förfiningen föll' in t for t in texter(st[4], 'brister')),
             ('R2: en förfining som föll med ett undantag', st[4]['status'], st[4]['utfall'], st[4]['brister'], st[5]['status']))
    st = stegen('r2-aterstallning')
    kontroll(st[4]['status'] == 'underkänt' and any('återställningen föll' in t for t in texter(st[4], 'brister')),
             ('R2: en förfining där också återställningen föll', st[4]['status'], st[4]['brister']))
    st = stegen('r2-utan-skal')
    kontroll((st[4]['status'], st[5]['status']) == ('inte observerat', 'inte påbörjat'), ('R2: en klar körning utan förfiningens post och skäl', st[4]['status'], st[5]['status']))
# kombinationerna: ett nytt val efter en klar förfining, en död arbetare och en klar kandidat bredvid en som förfinas
forfiningsfall('r2-tidigare-val', dict(KLAR, kandidater={'k01': 'forfinad', 'k02': 'klar'}), 'forfinad', version='e9' * 32,
               forfining={'dom': VAL, 'fran': 'e1' * 32, 'klar': '2026-10-06T11:40:00Z', 'varv': 4}, fordjupad=True)
dom('r2-tidigare-val', 'putsa', '2026-10-06T12:00:00Z', [('k01', 'e9' * 32)])
kandidat('r2-tidigare-val', 'k01', 'vald', version='e9' * 32, agarens_dom='2026-10-06T12:00:00Z', tid='2026-10-06T12:00:00Z',
         forfining={'dom': VAL, 'fran': 'e1' * 32, 'klar': '2026-10-06T11:40:00Z', 'varv': 4}, fordjupad=True)  # efter_beslut: vald igen
dod = subprocess.Popen([sys.executable, '-c', 'pass'])
dod.wait()  # en arbetare som inte lever (atelje.avbruten)
forfiningsfall('r2-dod', dict(steg='forfina', pid=dod.pid), 'under_arbete', version='e1' * 32,
               forfining_pagar={'dom': VAL, 'fran': 'e1' * 32, 'start_varv': 3})
s = 'r2-blandat'
underlag(s)
korning(s, **dict(EFTER, steg='forfina', pid=os.getpid(), valda=['k01', 'k02']))
plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='e1' * 32)
kandidat(s, 'k02', 'klar', version='e2' * 32)
dom(s, 'valj', VAL, [('k01', 'e1' * 32), ('k02', 'e2' * 32)])
kandidat(s, 'k01', 'forfinad', version='e9' * 32, agarens_dom=VAL, forfining={'dom': VAL, 'fran': 'e1' * 32, 'klar': '2026-10-06T11:30:00Z', 'varv': 4})
kandidat(s, 'k02', 'under_arbete', version='e2' * 32, agarens_dom=VAL, forfining_pagar={'dom': VAL, 'fran': 'e2' * 32, 'start_varv': 2})
with fall('R2 kombinationerna'):
    kontroll(statusar('r2-tidigare-val')[3:5] == ['inte påbörjat', 'inte påbörjat'], ('R2: en förfining för ett tidigare val räknas för det nya', statusar('r2-tidigare-val')))
    kontroll(statusar('r2-dod')[3] == 'stoppat', ('R2: en förfining vars arbetare dött', statusar('r2-dod')))
    kontroll(statusar('r2-blandat')[3] == 'pågår', ('R2: en klar kandidat döljer att en annan förfinas', statusar('r2-blandat')))
# förfiningen pågår, och en vald kandidat väntar på sin tur (kor_pool): den är inte påbörjad, inte underkänd
forfiningsfall('r2-ko', dict(steg='forfina', pid=os.getpid()), 'vald', version='e1' * 32, skal='ägarens dom %s (valj)' % VAL)
with fall('R2 en vald kandidat väntar medan förfiningen pågår'):
    st = stegen('r2-ko')
    kontroll(st[4]['status'] == 'pågår' and texter(st[4], 'utfall') == ['%s · inte påbörjad' % kandidater.etiketter('r2-ko', ['k01', 'k02'])['k01']] and not st[4]['brister'],
             ('R2: en väntande kandidat räknas som underkänd', st[4]['status'], st[4]['utfall'], st[4]['brister']))
# ditt val medan utforskningen stod i steg fel, och sedan --fortsatt av utforskningen (inte förfiningen): valets
# förfining har aldrig startat, så den är varken pågående eller underkänd (omgranskning 2, R2)
s = 'r2-utforskning'
underlag(s)
korning(s, steg='fel', startad='2026-10-06T10:00:00Z', fel='Stoppad: arbetaren stoppades (signal 15)')
plan(s, '2026-10-06T10:05:00Z', ['k01', 'k02'])
kandidat(s, 'k01', 'klar', version='c1' * 32)
kandidat(s, 'k02', 'planerad')
kandidater.efter_beslut(s, dom(s, 'valj', VAL, [('k01', 'c1' * 32)]))  # som atelje.doma: k01 blir vald med skälet "ägarens dom … (valj)"
korning(s, steg='kandidater', startad='2026-10-06T11:00:00Z', lage='fortsatt', forra_lage='ny', pid=os.getpid())
with fall('R2 utforskningen fortsätter efter valet'):
    st = stegen(s)
    kontroll(st[4]['status'] == 'inte påbörjat', ('R2: utforskningen räknas som valets förfining medan den pågår', st[4]['status'], st[4]['utfall']))
korning(s, steg='klar_for_bedomning', startad='2026-10-06T11:00:00Z', lage='fortsatt', forra_lage='ny', klar='2026-10-06T11:40:00Z')
kandidat(s, 'k02', 'klar', version='c2' * 32)
with fall('R2 utforskningen klar efter valet'):
    st = stegen(s)
    kontroll(st[4]['status'] == 'inte påbörjat' and not st[4]['brister'], ('R2: utforskningen räknas som en förfining som föll', st[4]['status'], st[4]['utfall'], st[4]['brister']))

# --- B3: Figma-pilotens status och bilder, bundna till version ---
P = U / 'figma-pilot'
skriv(P / 'BRIEF.md', '# ingen kund\n')  # pilotens katalog är ingen kund, också med en BRIEF.md (M4)
m = P / 'moment-b'  # som den riktiga posten: granskad i v2, aktuell v2.1
skriv(m / 'VERSION.json', {'moment': 'B', 'aktuell': 'v2.1', 'status': 'kontrollerat', 'status_skal': 'v2 bedömd; v2.1 rättar',
                           'figma': {'fil': 'FIL-B', 'noder': {'dator': '7:3'}}, 'versioner': {'v1': {}, 'v2': {}}, 'varv': {'v1': {}, 'v2': {}, 'v2.1': {}}})
for kat, n in (('v1', 4), ('v2', 4), ('v2.1', 4), ('granskning-v1', 7), ('granskning-v2', 8), ('jamforelse', 6)):
    for i in range(n):
        skriv(m / kat / ('%d-vy.png' % i), png())
for n in ('BILDDOM-v1.md', 'BILDDOM-v2.md', 'JAMFORELSE-MED-SKAPAREN-v2.md'):
    skriv(m / 'bedomningar' / n, '# %s\n' % n)
m = P / 'moment-a'  # granskad i v5 (och v4 utan version i namnet), bilder ur granskning-v4 och -v5
skriv(m / 'VERSION.json', {'moment': 'A', 'aktuell': 'v5', 'status': 'kontrollerat', 'versioner': {'v4': {}}, 'varv': {'v4': {}, 'v5': {}}})
for kat in ('granskning-v4', 'granskning-v5'):
    for i in range(6):
        skriv(m / kat / ('%d-vy.png' % i), png())
skriv(m / 'bedomningar' / 'BILDDOM.md', '# v4\n')
skriv(m / 'bedomningar' / 'BILDDOM-v5.md', '# v5\n')
skriv(P / 'moment-w' / 'VERSION.json', {'moment': 'W', 'aktuell': 'v1', 'status': 'kontrollerat'})  # ingen versionsmärkt bedömning
skriv(P / 'moment-w' / 'bilder' / '1.png', png())
skriv(P / 'moment-x' / 'VERSION.json', {'moment': 'X', 'status': 'påhittad'})
m = P / 'moment-c'  # skapad, med bilder utan version
skriv(m / 'VERSION.json', {'moment': 'C', 'aktuell': 'C4', 'status': 'skapat', 'versioner': {'C3': {}, 'C4': {}}})
for i in range(3):
    skriv(m / 'bilder' / ('%d.png' % i), png())
m = P / 'moment-u'  # "underkänt" i posten för v3, men bara v2 är bedömd
skriv(m / 'VERSION.json', {'moment': 'U', 'aktuell': 'v3', 'status': 'underkänt', 'versioner': {'v2': {}, 'v3': {}}})
skriv(m / 'bedomningar' / 'BILDDOM-v2.md', '# v2\n')
skriv(m / 'v3' / '1.png', png())
m = P / 'moment-l'  # den aktuella versionens bildkatalog är en länk ut ur momentet
skriv(m / 'VERSION.json', {'moment': 'L', 'aktuell': 'v1', 'status': 'kontrollerat'})
skriv(m / 'bedomningar' / 'BILDDOM-v1.md', '# v1\n')
skriv(TMP / 'utanfor' / 'bilder' / '1.png', png())
(m / 'v1').symlink_to(TMP / 'utanfor' / 'bilder')


def katalogversion(bild):
    kat = bild['sokvag'].split('/')[-2]
    kat = kat[len('granskning-'):] if kat.startswith('granskning-') else kat
    return kat if re.fullmatch(r'v\d+(?:\.\d+)*|C\d+', kat) else 'inte observerat'


with fall('B3 piloten'):
    p = {x['id']: x for x in dash.figma_pilot()}
    b, a_, w, x_, c = p['moment-b'], p['moment-a'], p['moment-w'], p['moment-x'], p['moment-c']
    kontroll(b['status'] == 'skapat', ('B3: moment B är kontrollerat fast granskningen gällde v2, inte v2.1', b['status']))
    kontroll(w['status'] == 'inte observerat', ('B3: kontrollerat utan någon bedömd version', w['status']))
    kontroll((a_['status'], x_['status'], c['status']) == ('kontrollerat', 'inte observerat', 'skapat'), (a_['status'], x_['status'], c['status']))
    alla = [bild for x in p.values() for bild in x['bilder']]
    kontroll(alla and all(bild.get('version') == katalogversion(bild) for bild in alla),
             ('B3: en bild bär inte versionen ur sin katalog', [(bild['sokvag'].split('figma-pilot/')[1], bild.get('version')) for bild in alla][:6]))
    kontroll({bild.get('version') for bild in b['bilder']} == {'v2.1', 'v2'} and {bild.get('version') for bild in a_['bilder']} == {'v5'},
             ('B3: bilderna är inte den aktuella och den bedömda versionens', sorted({bild['sokvag'].split('/')[-2] for bild in b['bilder'] + a_['bilder']})))
    kontroll([x.get('version') for x in b['bedomningar']] == ['v1', 'v2', 'v2'] and [x.get('version') for x in a_['bedomningar']] == ['v5', 'inte observerat'],
             ('B3: bedömningarna bär inte sin version', [x.get('version') for x in b['bedomningar'] + a_['bedomningar']]))
    kontroll(any('gäller en tidigare version' in t for t in texter(b, 'kontroller')), ('B3: moment B säger inte att bedömningen gäller en tidigare version', b.get('kontroller')))
    kontroll(p['moment-u']['status'] == 'skapat', ('B3: underkänt fast granskningen gällde v2, inte v3', p['moment-u']['status']))
    kontroll(p['moment-l']['status'] == 'kontrollerat' and not p['moment-l']['bilder'], ('B3: bilder ur en länkad katalog', p['moment-l']['bilder'][:2]))
with fall('B3 vyns bildtext'):  # Byggflödet visar varje bilds version under bilden och i alt-texten (arbetsyta.js, pilotens bilder)
    js = (ROOT / 'dashboard' / 'arbetsyta.js').read_text(encoding='utf-8')
    mall_ = js[js.find('m.bilder.filter((b) => sakerLank(b.lank)).map('):]
    mall_ = mall_[:mall_.find('</figure>') + len('</figure>')]
    kontroll('<figcaption>version ${e_(b.version)}</figcaption>' in mall_ and ', version ${e_(b.version)}"' in mall_,
             ('B3: vyn visar inte bildens version', mall_[:160]))

# --- en länkad fil i kundens underlag visas inte (_fil följer ingen symlänk) ---
s = 'r4-lank'
skriv(U / s / 'RESEARCH.md', '# research\n')
skriv(U / s / 'TEXTUNDERLAG.md', '# text\n')
skriv(TMP / 'utanfor' / 'BRIEF.md', '# HEMLIG-UTANFOR brief\n')
(U / s / 'BRIEF.md').symlink_to(TMP / 'utanfor' / 'BRIEF.md')
with fall('R4 länkad fil'):
    f = dash.flode(s)
    st = {x['nr']: x for x in f['steg']}
    kontroll(texter(st[1], 'utfall') == ['RESEARCH.md', 'TEXTUNDERLAG.md'] and 'HEMLIG' not in json.dumps(f, ensure_ascii=False),
             ('R4: en länkad fil i underlaget visas', texter(st[1], 'utfall')))

# --- rutterna och länkarna ---
with fall('rutterna'):
    slugar = dash.flode_slugar()
    kontroll({'fl-blind', 'b2-korsvis', 'b1-godkand', 'ab-x', 'ab-y', 'r2-pagar'} <= set(slugar) and not {'figma-pilot', 'ab'} & set(slugar), slugar)
    kod, data = hamta('/api/flode')
    alla = json.loads(data) if kod == 200 else {}
    kontroll(kod == 200 and {'kedjan', 'slugar', 'pilot'} <= set(alla) and alla['slugar'] == slugar, (kod, data[:200]))
    kontroll(hamta('/api/flode/okand-kund')[0] == 404 and hamta('/api/flode/figma-pilot')[0] == 404, 'en okänd kund och pilotens katalog ska ge 404')
    kod, data = hamta('/api/flode/fl-blind')
    kontroll(kod == 200 and json.loads(data)['slug'] == 'fl-blind', (kod, data[:200]))
    # varje länk som vyn ger, för varje kund och för piloten, öppnas genom /fil/ (fil_tillaten och den verkliga sökvägen)
    lankar = {x['lank'] for s in slugar for st_ in json.loads(hamta('/api/flode/' + s)[1])['steg']
              for falt in ('underlag', 'utfall', 'kontroller', 'beslut') for x in st_[falt] if isinstance(x, dict) and x.get('lank')}
    lankar |= {x['lank'] for m in alla.get('pilot') or [] for x in m['bilder'] + m['bedomningar'] if x.get('lank')}
    stangda = sorted(l for l in lankar if hamta(l)[0] != 200)
    kontroll(len(lankar) > 20 and not stangda, ('länkar som /fil/ inte öppnar', len(lankar), stangda[:5]))
srv.shutdown()

if fel:
    for x in fel:
        print('FEL:', x, file=sys.stderr)
    sys.exit(1)
print('flödesvyn ok: kedjan ur README, blindningen före första valet och A/B-valet, stegen bundna till körningen, korsluts '
      'och kor.sh:s prövningar, förfiningen, pilotens versioner, rutterna och länkarna', file=sys.stderr)
