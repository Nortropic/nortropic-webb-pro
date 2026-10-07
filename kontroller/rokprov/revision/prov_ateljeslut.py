#!/usr/bin/env python3
"""prov_ateljeslut.py — skapandeflödets slutpost, status vid stopp och fel, första valbara skiss, avsändarna och
domloggens läsning (ägarens uppdrag 2026-10-07, punkt 4, 6, 7 och 10; GR-20261007-r100-om#KAN-A; gren C1):

- en stoppad kandidat som var under arbete märks "avbruten vid stoppet" med tiden, sessionen får sluttid och utfall i
  förteckningen, redovisningens huvud säger stoppet och steget, och körningens slutpost (med STATUS.json och
  REDOVISNING.md bredvid) säger samma sak; tiden till första valbara skiss står, fast körningen stoppades; en tråd som
  lever kvar efter stoppet skriver inte över märkningen;
- ett fel mitt i en körning ger en post med felet och steget där det hände, och ett fel märker bara de kandidater som
  körningen själv satte under arbete;
- en körning vars arbetare dödades får sin post i efterhand, med sin STATUS.json, innan nästa start skriver över den;
- återupptagningen efter stoppet sparar det avbrutna försöket, gör om det och skriver en ny post som ersätter den förra,
  utan att den förra körningens STATUS.json skrivs över;
- atelje.py:s och prototyp.py:s besked och slutkod kommer ur posten: i processen, genom prototyp.py:s stopp (en kort
  post) och genom den verkliga startvägen (prototyp.py → atelje.py → arbetaren i en egen process, i en repokopia med en
  falsk claude);
- en vidarebefordrad AI-bedömning mot ett ägarbeslut: den godkänner inget, drar inte tillbaka ett godkännande, ändrar
  inte läget, stoppar inget bygge och lyfter inte blindningen; ägaren via Codex räknas bara med belägg;
- en äldre domrad utan belägg står som ej belagd och styr ingenting, och loggen skrivs aldrig om;
- tiden till första valbara skiss i en äldre körning räknas fram ur statusloggen och märks så;
- domloggen läses på radslut: en dom med U+2028, U+2029 eller U+0085 räknas, en trasig rad syns med plats och skäl,
  radnumren och radernas hashar stämmer med filen, och en ny dom efter en avbruten rad hamnar på en egen rad;
- efter granskningen GR-20261007-r106: ägarens stopp genom den verkliga vägen (prototyp.py → atelje.py --arbetare som
  __main__, med sessioner mot en sovande falsk claude, och atelje.py --stoppa) avslutar varje session och ger den slut
  och utfall (B1); läget full prövar stoppet efter varje session; startkontrollens stopp av en ny start ger sitt besked
  direkt och ersätter inte den förra körningens post (BÖR-1); ett belägg i efterhand fästs vid raden i en bilaga utan att
  bli en ny dom (BÖR-2); SIGINT och ett annat avbrott slutar som fel (BÖR-3); vägen ut ur en oläsbar rad (KAN-2); slutkod
  6 utan valbara kandidater (KAN-5); godkännandets avsändare vid två rader samma sekund (KAN-6); ingen länk följs när
  redovisningen kopieras (KAN-8); vad ägarens val betyder i posten (KAN-9); och provluckorna i KAN-10.

    .venv/bin/python kontroller/rokprov/revision/prov_ateljeslut.py <repo>

Allt skrivs i en temporär katalog (nwp-ateljeslut-*); repots filer läses men ändras inte, inga privata data läses, och
ingen verklig session startas (claude är en falsk). Varje fall redovisas för sig på stderr; slutkod 1 när något föll.
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
PY = str(ROOT / '.venv' / 'bin' / 'python')
TMP = Path(tempfile.mkdtemp(prefix='nwp-ateljeslut-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(lambda: shutil.rmtree(TMP, True))
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_ateljeslut')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
os.environ['NWP_STARTKONTROLL'] = 'av'  # startkontrollen prövas för sig (prov_startkontroll.py)
os.environ.pop('NWP_SLUG', None)
os.environ.pop('NWP_ATELJE', None)
import atelje  # noqa: E402
import kandidater  # noqa: E402
import korslut  # noqa: E402
import observation  # noqa: E402
import prototyp  # noqa: E402
import skapande  # noqa: E402

RT = TMP / 'rot'  # som repots rot: underlag/ och kunder/ bredvid varandra (korslut.startsidan läser dem så)
U, K = RT / 'underlag', RT / 'kunder'
U.mkdir(parents=True)
K.mkdir(parents=True)
atelje.UNDERLAG, atelje.KUNDER = U, K
observation.UNDERLAG = U
FEL = []
TIDER = {}


def fall(namn):
    def kor_fallet(f):
        t0 = time.time()
        try:
            f()
            print('ok: %s (%.1f s)' % (namn, time.time() - t0), file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:1500]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-5:]), file=sys.stderr)
        finally:
            atelje.STOPP.clear()  # låset efter ett stopp (atelje.SLUTFORD) nollställer arbetaren själv när den startar
            for sig_ in (signal.SIGTERM, signal.SIGHUP):
                signal.signal(sig_, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.default_int_handler)
        return f
    return kor_fallet


def skriv(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (dict, list)):
        data = json.dumps(data, ensure_ascii=False, indent=1)
    p.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
    return p


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stampel(t_):
    """Körningens katalognamn ur starttiden (2026-10-07T12:00:00Z → 20261007T120000Z), som kor.sh:s körningar."""
    return t_.replace('-', '').replace(':', '')


def post_ur_status(slug, st):
    """Körningens slutpost som fil, ur statusens fält slutpost: (fil, post) eller (None, None)."""
    rel = (st or {}).get('slutpost')
    f = RT / rel if rel else None
    return (f, json.loads(f.read_text())) if f and f.is_file() else (None, None)


def ladda(namn, fil):
    spec = importlib.util.spec_from_file_location(namn, str(fil))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SV = ladda('stoppvakt_ateljeslut', ROOT / '.claude' / 'hooks' / 'stoppvakt.py')


def kund(slug, rot=None):
    """En kund med underlaget som ateljén kräver och en sajt ur mallen (bara det som läses), syntetiskt."""
    u, k = (rot or RT) / 'underlag' / slug, (rot or RT) / 'kunder' / slug
    skriv(u / 'BRIEF.md', '# Brief\n\nBesökaren vill se tidigare arbeten och ringa.\n')
    skriv(u / 'RESEARCH.md', '# Research\n\nSyntetiskt underlag för provet.\n')
    skriv(u / 'INNEHALL.md', '# Innehåll\n\nRubrik och text.\n')
    skriv(u / 'VERKSAMHET.json', {'namn': 'Provfirman AB', 'kontaktvagar': []})
    skriv(k / 'sajt' / 'package.json', {'name': 'prov', 'private': True})
    (k / 'sajt' / 'node_modules').mkdir(parents=True, exist_ok=True)
    return u, k


def domrad(post):
    """En rad i domloggens form (json.dumps med ensure_ascii=False, som skapande.lagg_till_dom), utan validering: så
    skrevs äldre rader, och provet skriver dem så att samma fil prövas före och efter ändringen."""
    return (json.dumps(post, ensure_ascii=False) + '\n').encode('utf-8')


def logg(slug, *poster):
    f = U / slug / skapande.DOMLOGG
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, 'ab') as fh:
        for p in poster:
            fh.write(domrad(p) if isinstance(p, dict) else p)
    return f


def dom(tid_, kalla, beslut, text, **extra):
    return dict({'tid': tid_, 'kalla': kalla, 'beslut': beslut, 'text': text, 'avser': 'prov', 'ateroppnar': skapande.ATEROPPNAR[beslut]}, **extra)


# ===== kandidatflödet i processen: research, plan och material ersatta, kandidaternas arbete styrt av provet =====

METOD_STEG = {s: {'sha': hashlib.sha256(s.encode()).hexdigest(), 'filer': [], 'karta': 'prov',
                  'delar': {'före': [], 'varv': [], 'text': [], 'uppslag': []}} for s in ('forska', 'plan', 'skapa', 'skiss', 'granska', 'forfina')}


def ersatt_stegen(slug, ids, fel_i=None):
    """Kandidatflödets steg före skisserna i provets form (samma filer och fält som de riktiga stegen skriver), utan
    sessioner. fel_i: steget som faller."""
    spara = {n: getattr(kandidater, n) for n in ('leverera_metod', 'forska', 'planera', 'uppdragsmaterial', 'planprovning', 'behandla_skiss', 'skissa', 'PARALLELLT')}

    def leverera_metod(s):
        skriv(kandidater.metodkatalog(s) / 'METOD.json', {'tid': kandidater.nu(), 'steg': METOD_STEG})
        return dict(METOD_STEG)

    def forska(s, n, skiss=False):
        if fel_i == 'forska':
            raise RuntimeError('provets research föll')
        post = {'tid': kandidater.nu(), 'fel': None, 'nytt': {'paket': None, 'sajter': [], 'tjanster': None}, 'antaganden': [], 'fragor': [], 'sajter': []}
        skriv(kandidater.rot(s) / 'FORSKNING.json', post)
        skriv(kandidater.rot(s) / 'FORSKNING.md', '# Research före kandidatplanen\n')
        return post

    def planera(s, n, lage=None):
        if fel_i == 'planera':
            raise RuntimeError('provets plan föll')
        plan = {'tid': kandidater.nu(), 'lage': 'skiss', 'kandidater': {k: {'titel': 'Förslag %s' % k, 'hypotes': 'h', 'huvudreferens': 'egen'} for k in ids}}
        skriv(kandidater.rot(s) / 'KANDIDATPLAN.json', plan)
        for k in ids:
            kandidater.satt_status(s, k, 'planerad', 'uppdraget skrivet', titel='Förslag %s' % k, hypotes='h', huvudreferens='egen')
        return plan

    kandidater.leverera_metod, kandidater.forska, kandidater.planera = leverera_metod, forska, planera
    kandidater.uppdragsmaterial = lambda s, klient=None: skriv(kandidater.rot(s) / kandidater.UPPDRAGSMATERIAL, {'tid': kandidater.nu()}) and {}
    kandidater.planprovning = lambda s: skriv(kandidater.rot(s) / 'PLANPROVNING.json', {'tid': kandidater.nu(), 'andrade': 0, 'sekunder': 1,
                                                                                         'kvitto': {}}) and {'andrade': 0, 'sekunder': 1}
    kandidater.PARALLELLT = 2
    return spara


def aterstall(spara):
    for n, v in spara.items():
        setattr(kandidater, n, v)


def starta(s, lage='ny', **bar):
    """Som atelje.py:s main före arbetaren: ateljékatalogen och statusen "startar" med det som bär körningen."""
    rot = U / s / 'atelje'
    rot.mkdir(parents=True, exist_ok=True)
    atelje.skriv_status(rot, dict(bar, slug=s, startad=atelje.nu(), steg='startar', pid=None, modell=atelje.MODELL, effort=atelje.EFFORT,
                                  antal=atelje.ANTAL, lage=lage, kandidatflode=True))
    return rot


def klar_kandidat(s, kid, text='<h1>Skiss</h1>'):
    """En skiss som blir klar för ägarens bedömning, med version (hashen över kod/ och DESIGN.md) och statuslogg; försöket
    räknas som i kandidater.skissa."""
    forsok = int(kandidater.las_status(s, kid).get('forsok') or 0) + 1
    kandidater.satt_status(s, kid, 'under_arbete', 'skiss, försök %d' % forsok, forsok=forsok, startad=kandidater.nu(), frist=2700)
    d = kandidater.kdir(s, kid)
    skriv(d / 'kod' / 'index.astro', text)
    skriv(d / 'DESIGN.md', '# Design\n')
    skriv(d / 'RIKTNING.md', '# Riktning\n')
    return kandidater.satt_status(s, kid, 'klar', 'fotograferad', version=kandidater.version(s, kid), varv=1)


# ===== fallen =====

STOPP_SLUG = 'prov-stopp'


@fall('en stoppad kandidat som var under arbete: avbruten vid stoppet med tiden, sessionen får sitt slut, redovisningen och slutposten säger stoppet, och första valbara skiss står')
def _stopp():
    s = STOPP_SLUG
    kund(s)
    ids = ['k01', 'k02', 'k03']
    spara = ersatt_stegen(s, ids)
    hang, sov, sen = threading.Event(), {}, threading.Event()

    def behandla_skiss(slug, kid):
        if kid == 'k01':
            return klar_kandidat(slug, kid)
        if kid == 'k03':  # den tredje börjar aldrig: den väntar på stoppet, som skissa när ingen ny session får starta
            atelje.STOPP.wait(30)
            raise atelje.Stoppad('ingen ny session')
        # k02: en skaparsession som pågår när ägaren stoppar, och vars tråd aldrig hinner skriva sitt slut (provet 10-06)
        kandidater.satt_status(slug, kid, 'under_arbete', 'skiss, försök 1', forsok=1, startad=kandidater.nu(), frist=2700)
        skriv(kandidater.ksajt(slug, kid) / 'src' / 'pages' / 'index.astro', '<h1>Halv skiss</h1>')
        skriv(kandidater.kdir(slug, kid) / 'RIKTNING.md', '# Riktning, halvskriven\n')
        p = subprocess.Popen(['sleep', '120'], start_new_session=True)
        sov['p'] = p
        with atelje.AKTIVA_LAS:
            atelje.AKTIVA.add(p.pid)
        sid = str(uuid.uuid4())
        sov['sid'] = sid
        observation.anmal(slug, sid, kandidater.kdir(slug, kid) / 'svar-skiss-1.json', 'claude-fable-5-1', p.pid)
        kandidater.satt_status(slug, kid, 'under_arbete', 'skiss, försök 1', session_pid=p.pid)
        slut = time.time() + 30
        while kandidater.las_status(slug, 'k01').get('status') != 'klar' and time.time() < slut:
            time.sleep(0.05)
        slut = time.time() + 3  # k01:s tråd skriver körningens status efter sin kandidat (den gamla koden skriver inget fält)
        while time.time() < slut and not ((atelje.las_json(kandidater.rot(slug) / 'STATUS.json') or {}).get('tider') or {}).get('forsta_valbara'):
            time.sleep(0.05)
        os.kill(os.getpid(), signal.SIGTERM)  # ägarens stopp (atelje.py --stoppa skickar SIGTERM till arbetaren)
        hang.wait(60)  # sessionens svar kommer aldrig, som när ett barn håller röret öppet
        try:  # en tråd som lever kvar efter stoppet (en fotografering som blir klar) skriver inte över slutpostens läge
            kandidater.satt_status(slug, kid, 'klar', 'fotograferad efter stoppet', version='e' * 64)
        finally:
            sen.set()
        raise atelje.Stoppad('försöket avbröts av stoppet')

    kandidater.behandla_skiss = behandla_skiss
    starta(s)
    try:
        rc = atelje.arbeta(s, 'ny')
    finally:
        hang.set()
        sen.wait(10)
        aterstall(spara)
        if sov.get('p'):
            sov['p'].kill()
    rot = U / s / 'atelje'
    st = json.loads((rot / 'STATUS.json').read_text())
    TIDER['stopp'] = st
    k01, k02, k03 = (kandidater.las_status(s, k) for k in ids)
    av = st.get('avbrott') or {}
    assert rc == 0 and st['steg'] == 'fel' and 'Stoppad' in st['fel'], (rc, st.get('steg'), st.get('fel'))
    assert av.get('slag') == 'stopp' and av.get('steg') == 'skapa' and av.get('tid'), ('stoppet och steget där det hände', av)
    # kandidaterna: den som var under arbete är avbruten vid stoppet, med tiden; den klara och den aldrig påbörjade orörda
    assert k02['status'] == 'avbruten' and k02['avbruten_vid']['orsak'] == 'stoppet' and k02['avbruten_vid']['tid'] == av['tid'], k02
    assert k02['skal'].startswith('avbruten vid stoppet %s' % av['tid']) and k02.get('session_pid'), k02['skal']
    assert k01['status'] == 'klar' and k03['status'] == 'planerad', (k01['status'], k03['status'])
    # första valbara skiss: satt när k01 blev valbar, fast körningen stoppades före resten
    klar_tid = next(x['tid'] for x in k01['logg'] if x['status'] == 'klar')
    assert (st.get('tider') or {}).get('forsta_valbara') == klar_tid, ('första valbara skiss vid stopp', st.get('tider'), klar_tid)
    # sessionen som stoppet avslutade har sluttid och utfall i förteckningen
    sp = json.loads((observation.katalog(s) / ('%s.json' % sov['sid'])).read_text())
    assert sp['slut'] == av['tid'] and sp['utfall'] == 'avbruten vid stoppet', ('k02:s session efter stoppet', sp)
    # redovisningens huvud säger stoppet och steget; k02 står som avbruten vid stoppet, inte under arbete
    red = (rot / 'REDOVISNING.md').read_text()
    assert ('**Körningens utfall:** stoppad i steg skapa, %s' % av['tid']) in red.split('\n')[2], red.split('\n')[:4]
    rad_k02 = next(r for r in red.split('\n') if r.startswith('| ') and '(k02)' in r)
    assert '| avbruten vid stoppet |' in rad_k02 and 'under arbete' not in rad_k02, rad_k02
    assert ('första valbara skissen %s;' % klar_tid) in red and '(framräknad' not in red, [r for r in red.split('\n') if 'första valbara' in r]
    # slutposten: i kunder/<slug>/atelje/korningar/<körning>/, med statusen och redovisningen bredvid
    import ateljeslut
    stamp = ateljeslut.stampel(st['startad'])
    d = K / s / 'atelje' / 'korningar' / stamp
    post = json.loads((d / 'SLUT.json').read_text())
    assert st['slutpost'] == 'kunder/%s/atelje/korningar/%s/SLUT.json' % (s, stamp) == post['slutpost'], (st.get('slutpost'), post.get('slutpost'))
    assert post['typ'] == 'slutpost (ateljén)' and post['slutkod'] == 4 and post['utfall']['slag'] == 'stoppad' and post['utfall']['steg'] == 'skapa', post['utfall']
    assert post['slutkod_text'].startswith('Slutkod 4: körningen föll, stoppades eller avbröts; stoppad i steg skapa'), post['slutkod_text']
    assert json.loads((d / 'STATUS.json').read_text()) == st and (d / 'REDOVISNING.md').read_bytes() == (rot / 'REDOVISNING.md').read_bytes()
    kp = {x['id']: x for x in post['kandidater']}
    assert kp['k02']['status'] == 'avbruten' and kp['k02']['avbruten_vid']['orsak'] == 'stoppet' and kp['k01']['version'] == k01['version'], kp
    assert post['tider']['forsta_valbara'] == klar_tid and post['tider']['forsta_valbara_kalla'] == kandidater.SATT, post['tider']
    t = post['tillstand']
    assert [t[n]['varde'] for n, _ in korslut.TILLSTAND] == [False, None, None, None, False], [t[n]['varde'] for n, _ in korslut.TILLSTAND]
    assert post['kompetenskedjan'] == 'inte observerat' and post['metod']['metod_json_sha256'] == sha(rot / 'metod' / 'METOD.json')
    assert ('kandidat k01 version %s (klar för ägarens bedömning)' % k01['version']) in post['granskad_identitet'], post['granskad_identitet']
    assert post['metod']['repo'] and len(post['metod']['repo']['commit']) == 40, post['metod']['repo']
    # terminalens besked ur posten: kandidaterna med stoppet, och slutkoden
    text = ateljeslut.text(post)
    assert ('Kandidaterna: 1 av 3 valbara; k01 klar för ägarens bedömning, k02 avbruten vid stoppet %s, k03 planerad' % av['tid']) in text.split('\n'), text
    assert text.split('\n')[-1] == post['slutkod_text'] and ('Slutpost: %s' % post['slutpost']) in text.split('\n'), text[-400:]


BARN_STOPP = r"""
import json, os, signal, sys, threading, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
os.environ['NWP_STARTKONTROLL'] = 'av'
import atelje, kandidater, observation
U, K, s = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
SIG = getattr(signal, sys.argv[5], signal.SIGTERM) if len(sys.argv) > 5 else signal.SIGTERM  # ägarens stopp (SIGTERM), SIGINT, eller SystemExit
atelje.UNDERLAG, atelje.KUNDER, observation.UNDERLAG = U, K, U
rot = U / s / 'atelje'
rot.mkdir(parents=True)
def skriv(f, d):
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    return d
# stegen före skisserna i provets form och utan sessioner, som ersatt_stegen i provet
kandidater.leverera_metod = lambda slug: {}
def forska(slug, n, skiss=False):
    return skriv(kandidater.rot(slug) / 'FORSKNING.json', {'tid': atelje.nu(), 'fel': None, 'nytt': {'paket': None, 'sajter': [], 'tjanster': None}})
IDS = ['k01', 'k02']
def planera(slug, n, lage=None):
    plan = skriv(kandidater.rot(slug) / 'KANDIDATPLAN.json', {'tid': atelje.nu(), 'lage': 'skiss', 'kandidater': {k: {'titel': 'Förslag %s' % k} for k in IDS}})
    for k in IDS:
        kandidater.satt_status(slug, k, 'planerad', 'uppdraget skrivet', titel='Förslag %s' % k)
    return plan
kandidater.forska, kandidater.planera = forska, planera
kandidater.uppdragsmaterial = lambda slug, klient=None: skriv(kandidater.rot(slug) / kandidater.UPPDRAGSMATERIAL, {'tid': atelje.nu()}) and {}
kandidater.planprovning = lambda slug: skriv(kandidater.rot(slug) / 'PLANPROVNING.json', {'tid': atelje.nu(), 'andrade': 0, 'sekunder': 1}) and {'andrade': 0, 'sekunder': 1}
kandidater.PARALLELLT = 2
def behandla_skiss(slug, kid):
    kandidater.satt_status(slug, kid, 'under_arbete', 'skiss, försök 1', forsok=1, startad=atelje.nu(), frist=2700)
    pool = sorted((t for t in threading.enumerate() if t.name.endswith('(arbeta)')), key=lambda t: int(t.name.split('-')[1].split()[0]))
    if threading.current_thread() is not pool[0]:  # arbetaren väntar på poolens första tråd först, inte på den här
        threading.Event().wait()  # den här sessionens svar kommer aldrig (provet 10-06: arbetaren fick dödas)
    slut = time.time() + 10  # ägarens stopp när båda kandidaterna är under arbete
    while time.time() < slut and any(kandidater.las_status(slug, k).get('status') != 'under_arbete' for k in IDS):
        time.sleep(0.02)
    os.kill(os.getpid(), SIG)
    atelje.STOPP.wait(10)
    raise atelje.Stoppad('ingen ny session')
kandidater.behandla_skiss = behandla_skiss
if sys.argv[5:6] == ['SystemExit']:  # ett annat avbrott i huvudtråden: planen avbryter körningen med SystemExit(3)
    def planera_exit(slug, n, lage=None):
        raise SystemExit(3)
    kandidater.planera = planera_exit
atelje.skriv_status(rot, {'slug': s, 'startad': atelje.nu(), 'steg': 'startar', 'pid': None, 'lage': 'ny', 'kandidatflode': True})
atelje.arbeta(s, 'ny')
print('ARBETAREN SLUTADE', flush=True)
"""
VAKT_CLAUDE = r'''#!/bin/sh
echo "$*" | cut -c1-200 >> "$(dirname "$0")/anrop.log"
exit 1
'''


def vaktmiljo():
    """En miljö där claude är en vakt som bara loggar anropet och faller: ett anrop vore en verklig session, och provet får
    aldrig göra ett. Ger (miljön, vaktens katalog)."""
    vakt = TMP / 'vakt-claude'
    if not (vakt / 'claude').exists():
        skriv(vakt / 'claude', VAKT_CLAUDE)
        (vakt / 'claude').chmod(0o755)
    return dict(os.environ, PATH=str(vakt) + os.pathsep + os.environ.get('PATH', ''), NWP_KORREGISTER=str(TMP / 'korregister')), vakt


def barn(s, sig='SIGTERM', slutad=True):
    """Barnprovet: arbetaren i en egen process, stoppad med signalen medan två skisser är under arbete (eller avbruten med
    SystemExit i huvudtråden). slutad: arbetaren förväntas sluta i ordning. Ger utskriften."""
    miljo, vakt = vaktmiljo()
    try:
        p = subprocess.run([PY, '-B', '-c', BARN_STOPP, str(ROOT / 'kontroller'), str(U), str(K), s, sig], capture_output=True, text=True, timeout=60, env=miljo)
    except subprocess.TimeoutExpired as e:
        raise AssertionError('arbetaren avslutades inte efter %s (en tråd höll kvar processen): %s' % (sig, str(e.stdout or '')[-300:]))
    assert not (vakt / 'anrop.log').exists(), 'provet startade claude: %s' % (vakt / 'anrop.log').read_text()[:300]
    assert ('ARBETAREN SLUTADE' in p.stdout) == slutad, (sig, p.returncode, p.stdout[-300:], p.stderr[-800:])
    return p


@fall('efter stoppet avslutas arbetaren, fast en sessions tråd aldrig får svar: stoppet behöver aldrig döda den, och posten är skriven')
def _stopp_avslutas():
    s = 'prov-hanger'
    u, k = kund(s)
    barn(s)
    st = json.loads((u / 'atelje' / 'STATUS.json').read_text())
    f, post = post_ur_status(s, st)
    assert post and post['utfall']['slag'] == 'stoppad' and post['utfall']['steg'] == 'skapa', (st.get('slutpost'), st.get('avbrott'))
    assert [kandidater.las_status(s, k)['status'] for k in ('k01', 'k02')] == ['avbruten', 'avbruten'], 'båda var under arbete vid stoppet'


@fall('SIGINT till arbetaren är samma stopp som SIGTERM: körningen slutar som fel med stoppet i posten och kandidaterna märkta, statusen säger aldrig att körningen pågår; ett annat avbrott (SystemExit) slutar också som fel')
def _sigint():
    s = 'prov-sigint'
    u, k = kund(s)
    barn(s, 'SIGINT')
    st = json.loads((u / 'atelje' / 'STATUS.json').read_text())
    assert st['steg'] == 'fel' and (st.get('avbrott') or {}).get('slag') == 'stopp' and 'pid' not in st and not atelje.avbruten(st), (st.get('steg'), st.get('avbrott'))
    f, post = post_ur_status(s, st)
    assert post and post['utfall']['slag'] == 'stoppad' and post['utfall']['steg'] == 'skapa' and post['slutkod'] == 4, (st.get('slutpost'), (post or {}).get('utfall'))
    assert [kandidater.las_status(s, k)['status'] for k in ('k01', 'k02')] == ['avbruten', 'avbruten'], 'kandidaterna under arbete märks vid SIGINT'
    vald, skal = prototyp.lage(s)
    assert 'förra körningen föll' in skal and '--fortsatt' in skal, ('läget efter SIGINT säger att körningen pågår', vald, skal)
    # ett annat avbrott i huvudtråden (SystemExit): körningen slutar som fel, posten säger avbrottet, och undantaget går vidare
    s2 = 'prov-exit'
    u2, _k2 = kund(s2)
    p2 = barn(s2, 'SystemExit', slutad=False)
    assert p2.returncode == 3, ('SystemExit gick inte vidare ur arbetaren', p2.returncode, p2.stderr[-400:])
    st2 = json.loads((u2 / 'atelje' / 'STATUS.json').read_text())
    assert st2['steg'] == 'fel' and str(st2.get('fel')).startswith('SystemExit') and (st2.get('avbrott') or {}).get('slag') == 'avbruten' and 'pid' not in st2, st2.get('avbrott')
    assert not atelje.avbruten(st2), 'statusen säger att körningen pågår'
    _f2, post2 = post_ur_status(s2, st2)
    assert post2 and post2['utfall']['slag'] == 'avbruten' and post2['utfall']['steg'] == 'planera' and post2['slutkod'] == 4, (post2 or {}).get('utfall')


@fall('återupptagning efter stoppet: det avbrutna försöket sparas och görs om, en ny post ersätter den förra, och den förra körningens STATUS.json står kvar')
def _aterupptagning():
    s = STOPP_SLUG
    st0 = TIDER['stopp']
    rot = U / s / 'atelje'
    d0 = K / s / 'atelje' / 'korningar' / stampel(st0['startad'])
    status0 = (d0 / 'STATUS.json').read_bytes() if (d0 / 'STATUS.json').is_file() else None
    spara = ersatt_stegen(s, ['k01', 'k02', 'k03'])
    gjorda = []

    def skissa(slug, kid, fel=None):
        gjorda.append(kid)
        if gjorda.count(kid) > 2:  # en status som aldrig skrivs (ett lås kvar från det förra stoppet) ger inget nytt försök
            raise RuntimeError('provet: kandidatens status skrevs inte')
        return klar_kandidat(slug, kid, '<h1>Skiss %s, nytt försök</h1>' % kid)

    kandidater.behandla_skiss, kandidater.skissa = spara['behandla_skiss'], skissa  # den riktiga återupptagningen
    # som atelje.py --fortsatt: statusen bär det som säger var körningen var, och arbetaren startar
    gammal = {k: st0[k] for k in ('faser',) + atelje.BARS + atelje.BARS_FORTSATT + ('foregaende',) + atelje.BARS_KANDIDAT if k in st0}
    time.sleep(1.1)  # en ny körning, en ny sekund
    starta(s, 'fortsatt', forra_lage='ny', **gammal)
    try:
        atelje.arbeta(s, 'fortsatt')
    finally:
        aterstall(spara)
    st = json.loads((rot / 'STATUS.json').read_text())
    k02 = kandidater.las_status(s, 'k02')
    assert st['steg'] == 'klar_for_bedomning' and sorted(gjorda) == ['k02', 'k03'], (st['steg'], gjorda)
    fs = (k02.get('forsok_tider') or [])
    av0 = st0.get('avbrott') or {}
    assert fs and fs[0].get('utfall') == 'avbruten' and fs[0].get('orsak') == 'stoppet' and av0.get('tid') and fs[0].get('klar') == av0['tid'], fs
    arkiv = U / s / 'atelje' / 'kandidater' / 'k02' / 'forsok-1'
    assert (arkiv / 'projekt' / 'src' / 'pages' / 'index.astro').read_text() == '<h1>Halv skiss</h1>' and (arkiv / 'RIKTNING.md').is_file(), 'försöket sparat'
    assert any(x['status'] == 'avbruten' and 'avbröts vid stoppet %s' % av0['tid'] in x['skal'] for x in k02['logg']), k02['logg'][-4:]
    assert k02['status'] == 'klar' and 'avbruten_vid' not in k02 and k02['forsok'] == 2, (k02['status'], k02.get('forsok'))
    # den nya posten ersätter den förra; den förra körningens STATUS.json står kvar oförändrad i sin katalog
    _f, post = post_ur_status(s, st)
    assert post and (d0 / 'SLUT.json').is_file(), ('ingen slutpost för körningarna', st.get('slutpost'))
    forra = json.loads((d0 / 'SLUT.json').read_text())
    assert post['slutkod'] == 0 and post['utfall']['slag'] == 'klar' and post['korning']['lage'] == 'fortsatt', (post['slutkod'], post['utfall'])
    assert forra['rapportstatus'] == 'ersatt' and post['id'] in forra['ersatt_av'] and post['foregaende'].startswith(forra['id']), (forra['rapportstatus'], forra['ersatt_av'])
    assert (d0 / 'STATUS.json').read_bytes() == status0 and json.loads(status0)['steg'] == 'fel', 'den förra körningens STATUS.json skrevs över'
    assert post['tider']['forsta_valbara'] == st0['tider']['forsta_valbara'] and post['tillstand']['agaren_godkanner']['varde'] is None
    assert 'väntar på ägarens bedömning' in post['tillstand']['agaren_godkanner']['text']


@fall('läget full prövar stoppet efter varje session, som skissa: en skaparsession, förbättringsrundan och granskningen som stoppet dödade avbryter försöket i stället för att fotografera eller märka kandidaten fel')
def _stopp_i_laget_full():
    s = 'prov-full'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'KANDIDATPLAN.json', {'tid': atelje.nu(), 'lage': 'full', 'kandidater': {'k01': {'titel': 'Ett'}}})
    kandidater.satt_status(s, 'k01', 'planerad', 'uppdraget skrivet', titel='Ett')
    namn = ('forbered_projekt', 'stilpaket_i_projekt', 'skapar_prompt', 'verktyg', 'andra_nekas', 'lasningen', 'fotografera', 'metodinfo',
            'objektiva', 'bevara_version', 'kritik')
    spara = {n: getattr(kandidater, n) for n in namn}
    spara_session = atelje.session

    def session(*_a, **_k):  # ägarens stopp kommer medan sessionen pågår: stoppet dödar den, och anropet faller
        atelje.STOPP.set()
        raise RuntimeError('sessionen föll (kod -9, None): dödad av stoppet')

    def aldrig(vad):
        def f(*_a, **_k):
            raise AssertionError('%s gjordes fast stoppet kom' % vad)
        return f

    try:
        kandidater.forbered_projekt = kandidater.stilpaket_i_projekt = kandidater.bevara_version = lambda *a, **k: None
        kandidater.skapar_prompt = lambda *a, **k: 'prompt'
        kandidater.verktyg = kandidater.andra_nekas = lambda *a, **k: []
        kandidater.metodinfo = lambda *a, **k: {'sha': 'm' * 64}
        kandidater.lasningen = aldrig('läsningen')
        kandidater.fotografera = aldrig('fotograferingen')
        atelje.session = session
        try:
            kandidater.skapa(s, 'k01')
            raise AssertionError('skapa fortsatte efter stoppet')
        except atelje.Stoppad:
            pass
        assert kandidater.las_status(s, 'k01')['status'] == 'under_arbete', 'försöket står kvar under arbete för märkningen'
        atelje.STOPP.clear()
        kandidater.satt_status(s, 'k01', 'klar', 'fotograferad', version='a' * 64)
        kandidater.objektiva = lambda *a, **k: ['rubriken (hog): kontrasten → höj den']
        try:
            kandidater.forbattra(s, 'k01')
            raise AssertionError('forbattra fortsatte efter stoppet')
        except atelje.Stoppad:
            pass
        st = kandidater.las_status(s, 'k01')
        assert st['status'] == 'under_arbete' and (st.get('forbattras') or {}).get('fore') == 'a' * 64, ('märkningen forbattras står kvar för återupptagningen', st)
        atelje.STOPP.clear()
        kandidater.satt_status(s, 'k01', 'klar', 'fotograferad', version='a' * 64, ta_bort=('forbattras',), forbattrad={'tid': atelje.nu(), 'behovdes_inte': True})

        def kritik(slug, kid, namn='KRITIK.json'):
            atelje.STOPP.set()
            raise RuntimeError('sessionen föll (kod -9, None): dödad av stoppet')

        kandidater.kritik = kritik
        try:
            kandidater.behandla(s, 'k01')
            raise AssertionError('behandla fortsatte efter stoppet')
        except atelje.Stoppad:
            pass
        st = kandidater.las_status(s, 'k01')
        assert st['status'] == 'klar' and 'granskningen föll' not in st.get('skal', ''), ('granskningen som stoppet dödade skrevs som fel hos kandidaten', st)
    finally:
        atelje.STOPP.clear()
        atelje.session = spara_session
        for n, v in spara.items():
            setattr(kandidater, n, v)


@fall('första valbara skiss i en äldre körning utan fältet: framräknad ur statusloggen och märkt som framräknad')
def _forsta_valbara_aldre():
    s = STOPP_SLUG
    st = dict(TIDER['stopp'], tider={k: v for k, v in TIDER['stopp']['tider'].items() if k != 'forsta_valbara'})
    klar_tid = min(x['tid'] for x in kandidater.las_status(s, 'k01')['logg'] if x['status'] == 'klar')  # k01 blev valbar i den stoppade körningen
    kandidater.redovisa_skiss(s, st)
    red = (U / s / 'atelje' / 'REDOVISNING.md').read_text()
    assert ('första valbara skissen %s (framräknad ur kandidaternas statuslogg)' % klar_tid) in red, [r for r in red.split('\n') if 'första valbara' in r]
    assert 'minuter (framräknad)' in red
    tid_, kalla = kandidater.forsta_valbara_tid(s, st)
    assert tid_ == klar_tid and kalla == kandidater.FRAMRAKNAD, (tid_, kalla)


@fall('fel mitt i en körning: slutposten säger felet och steget där det hände, och redovisningens huvud likaså')
def _fel():
    s = 'prov-fel'
    kund(s)
    spara = ersatt_stegen(s, ['k01'], fel_i='forska')
    starta(s)
    try:
        rc = atelje.arbeta(s, 'ny')
    finally:
        aterstall(spara)
    rot = U / s / 'atelje'
    st = json.loads((rot / 'STATUS.json').read_text())
    av = st.get('avbrott') or {}
    assert rc == 0 and st['steg'] == 'fel' and av.get('slag') == 'fel' and av.get('steg') == 'forska', (st.get('steg'), av)
    import ateljeslut
    d = K / s / 'atelje' / 'korningar' / ateljeslut.stampel(st['startad'])
    post = json.loads((d / 'SLUT.json').read_text())
    assert post['slutkod'] == 4 and post['utfall']['slag'] == 'fel' and post['utfall']['steg'] == 'forska', post['utfall']
    assert post['utfall']['text'] == 'föll i steg forska, %s: RuntimeError: provets research föll' % av['tid'], post['utfall']['text']
    assert post['bedomningsutfall'].startswith('ofullständigt (slutkod 4)') and post['brister'][0] == post['utfall']['text'], post['brister'][:2]
    assert any('--fortsatt' in x for x in post['atgarder']) and json.loads((d / 'STATUS.json').read_text()) == st
    red = (rot / 'REDOVISNING.md').read_text().split('\n')
    assert red[2] == '**Körningens utfall:** föll i steg forska, %s: RuntimeError: provets research föll.' % av['tid'], red[:4]


@fall('ett fel märker bara kandidaterna som körningen satte under arbete (avbruten av fel), och låser inte statusen')
def _fel_markering():
    s = 'prov-felmark'
    kund(s)
    for kid in ('k01', 'k02'):
        kandidater.satt_status(s, kid, 'planerad', 'uppdraget skrivet')
    kandidater.satt_status(s, 'k01', 'under_arbete', 'skiss, försök 1', forsok=1)  # från en arbetare som dött före körningen
    time.sleep(1.1)
    start = kandidater.nu()
    kandidater.satt_status(s, 'k02', 'under_arbete', 'skiss, försök 1', forsok=1)
    markerade = kandidater.markera_avbrutna(s, 'fel', '2026-10-07T12:00:00Z', 'RuntimeError: provet', efter=start)
    k01, k02 = kandidater.las_status(s, 'k01'), kandidater.las_status(s, 'k02')
    assert markerade == ['k02'] and k02['status'] == 'avbruten' and k02['avbruten_vid']['orsak'] == 'fel', (markerade, k02.get('avbruten_vid'))
    assert k02['skal'].startswith('avbruten av fel 2026-10-07T12:00:00Z') and kandidater.statustext(k02) == 'avbruten av fel', k02['skal']
    assert k01['status'] == 'under_arbete', 'en kandidat under arbete sedan före körningen lämnas åt återupptagningen'
    assert not atelje.SLUTFORD.is_set(), 'ett fel i huvudtråden lämnar inga trådar efter sig: statusen låses inte'
    kandidater.satt_status(s, 'k02', 'under_arbete', 'skiss, försök 2', forsok=2)
    assert 'avbruten_vid' not in kandidater.las_status(s, 'k02'), 'märkningen gäller bara medan kandidaten står avbruten'


@fall('atelje.py:s besked och slutkod kommer ur posten: den stoppade körningen, den som föll och prototyp.py:s väntan')
def _atelje_besked():
    for s, stn in ((STOPP_SLUG, None), ('prov-fel', 'fel')):
        st = json.loads((U / s / 'atelje' / 'STATUS.json').read_text())
        f, post = post_ur_status(s, st)
        assert f and post, (s, 'ingen post för körningen')
        import ateljeslut
        if stn == 'fel':  # utan flagga: förra körningen föll, och beskedet är postens
            ut = io.StringIO()
            with contextlib.redirect_stdout(ut):
                rc = atelje.main([s, '--vanta', '1'])
            assert rc == post['slutkod'] == 4 and ateljeslut.text(post) in ut.getvalue() and '--fortsatt' in ut.getvalue(), (rc, ut.getvalue()[-500:])
            ut = io.StringIO()
            with contextlib.redirect_stdout(ut):
                rc = prototyp.main([s, '--vanta', '1'])
            assert rc == 4 and ateljeslut.text(post) in ut.getvalue(), ('prototyp.py:s väntan på en körning som föll', rc, ut.getvalue()[-500:])
    # en klar körning: vanta ger postens besked och slutkod, och en ändrad post ändrar beskedet (inget räknas om vid sidan av)
    s = STOPP_SLUG
    rot = U / s / 'atelje'
    st = json.loads((rot / 'STATUS.json').read_text())
    f, post = post_ur_status(s, st)
    ut = io.StringIO()
    with contextlib.redirect_stdout(ut):
        rc = atelje.vanta(rot, 1)
    assert rc == 0 == post['slutkod'] and ut.getvalue().strip() == ateljeslut.text(post), ut.getvalue()[-600:]
    original = f.read_bytes()
    try:
        andrad = dict(post, slutkod=6, slutkod_text='Slutkod 6: provets ändrade post', utfall=dict(post['utfall'], text='PROVETS MARKÖR'))
        f.write_text(json.dumps(andrad, ensure_ascii=False))
        ut = io.StringIO()
        with contextlib.redirect_stdout(ut):
            rc = atelje.vanta(rot, 1)
        assert rc == 6 and 'PROVETS MARKÖR' in ut.getvalue() and ut.getvalue().strip().endswith('Slutkod 6: provets ändrade post'), (rc, ut.getvalue()[-300:])
    finally:
        f.write_bytes(original)


@fall('prototyp.py:s stopp före körningen: en kort slutpost med skälet, beskedet ur den och slutkod 2')
def _prototyp_stopp():
    s = 'prov-gammal'
    kund(s)
    (U / s / 'prototyp').mkdir(parents=True)  # tidigare designbeslut utan dom: prototypen gissar inte läget
    ut = io.StringIO()
    with contextlib.redirect_stdout(ut):
        rc = prototyp.main([s])
    poster = sorted((K / s / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert rc == 2 and len(poster) == 1, (rc, poster, ut.getvalue()[-400:])
    post = json.loads(poster[0].read_text())
    import ateljeslut
    assert post['typ'] == ateljeslut.TYP_STOPP and post['slutkod'] == 2 and 'tidigare designbeslut finns' in post['skal'], post
    assert ateljeslut.text(post) in ut.getvalue() and ut.getvalue().strip().endswith(post['slutkod_text']), ut.getvalue()[-400:]
    assert post['tillstand']['sessionen_avslutad']['varde'] is None and post['rapportstatus'] == 'färdig' and post['ersatt_av'] == 'ej angivet'
    # utan kundens katalog skrivs ingen post: en ny post direkt under kunder/ hör till ett bygges gräns (kor.sh)
    (U / 'prov-utan-kund' / 'prototyp').mkdir(parents=True)
    ut = io.StringIO()
    with contextlib.redirect_stdout(ut):
        rc = prototyp.main(['prov-utan-kund'])
    assert rc == 2 and not (K / 'prov-utan-kund').exists() and 'Slutpost: skrevs inte' in ut.getvalue(), ut.getvalue()[-300:]


@fall('en körning vars arbetare dödades (SIGKILL) får sin slutpost i efterhand, med sin STATUS.json, innan nästa start skriver över den')
def _efterhand():
    s = 'prov-dodad'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'KANDIDATPLAN.json', {'tid': '2026-10-07T08:01:00Z', 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}}})
    kandidater.satt_status(s, 'k01', 'under_arbete', 'skiss, försök 1', forsok=1)
    dod = subprocess.Popen(['true'])
    dod.wait()  # arbetarens pid, som inte lever längre
    st = {'slug': s, 'startad': '2026-10-07T08:00:00Z', 'steg': 'skapa', 'pid': dod.pid, 'lage': 'ny', 'kandidatflode': True,
          'kandidatlage': 'skiss', 'modell': 'claude-fable-5-1', 'effort': 'max', 'tider': {'start': '2026-10-07T08:00:00Z'}}
    skriv(rot / 'STATUS.json', st)
    skriv(rot / 'REDOVISNING.md', '# Redovisning · %s · 2026-10-06T08:00:00Z\n\nEn tidigare körnings.\n' % s)
    ut = io.StringIO()
    with contextlib.redirect_stdout(ut):
        rc = atelje.main([s])  # utan flagga: avbrottet sägs, och ingen ny körning startar
    poster = sorted((K / s / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert rc == 4 and len(poster) == 1, ('ingen post i efterhand för den dödade körningen', rc, poster, ut.getvalue()[-300:])
    post = json.loads(poster[0].read_text())
    assert post['utfall']['slag'] == 'avbruten' and post['korning']['startad'] == st['startad'] and post['slutkod'] == 4, post['utfall']
    assert json.loads((poster[0].parent / 'STATUS.json').read_text()) == st, 'den dödade körningens STATUS.json'
    assert not (poster[0].parent / 'REDOVISNING.md').exists() and 'inte körningens' in post['brister'][0], 'en äldre körnings redovisning kopieras inte'
    import ateljeslut
    assert post['typ'] == ateljeslut.TYP_EFTERHAND and post['efterhand'].startswith('i efterhand') and ateljeslut.text(post) in ut.getvalue()
    assert 'Förra körningen avbröts i steg skapa' in ut.getvalue() and kandidater.las_status(s, 'k01')['status'] == 'under_arbete'
    assert ateljeslut.bevara_forra(s, st) == (None, None) and len(sorted((K / s / 'atelje' / 'korningar').glob('*/SLUT.json'))) == 1, 'en gång'


FALSK_CLAUDE = r'''#!/bin/sh
case "$*" in *--help*) echo "Usage: claude [--session-id <uuid>]"; exit 0;; esac
cat > /dev/null
echo '{"type":"result","subtype":"error_during_execution","is_error":true,"result":"provets falska claude föll","num_turns":1,"duration_ms":10}'
exit 1
'''


def ateljerepo():
    """Repokopian för den verkliga startvägen (kontroller/ kopierad, resten länkad), skapad en gång."""
    ar = TMP / 'ateljerepo'
    if not ar.exists():
        shutil.copytree(ROOT / 'kontroller', ar / 'kontroller', ignore=shutil.ignore_patterns('node_modules', '__pycache__', 'rokprov'))
        for namn in ('.venv', 'kunskap', 'kritik', 'mall'):
            os.symlink(ROOT / namn, ar / namn)
        (ar / '.claude').mkdir()
        os.symlink(ROOT / '.claude' / 'skills', ar / '.claude' / 'skills')
    return ar


def startmiljo(**extra):
    """Miljön för en process på den verkliga startvägen: inget från den omgivande sessionen eller provet, startkontrollen av."""
    miljo = {k_: v for k_, v in os.environ.items() if not k_.startswith(('CLAUDE_CODE_', 'NWP_')) and k_ not in ('CLAUDECODE', 'PYTHONPATH')}
    miljo.update(NWP_STARTKONTROLL='av', NWP_KORREGISTER=str(TMP / 'korregister'), **extra)
    return miljo


def processer_med(markor):
    """pid för varje process (utom den egna) vars kommandorad bär markören, ur ps."""
    ut = subprocess.run(['ps', '-A', '-o', 'pid=,command='], capture_output=True, text=True).stdout
    pids = []
    for r in ut.split('\n'):
        if markor in r:
            pid = int(r.split(None, 1)[0])
            if pid != os.getpid():
                pids.append(pid)
    return pids


def doda(pids):
    """Processgrupperna (sessionerna har egna) och processerna avslutas; en som redan är borta hoppas över."""
    for pid in pids:
        for f in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
            try:
                f()
            except (ProcessLookupError, PermissionError):
                pass


@fall('den verkliga startvägen: prototyp.py startar arbetaren i en egen process, och beskedet och slutkoden kommer ur arbetarens slutpost')
def _startvagen():
    ar = ateljerepo()
    falsk = TMP / 'falsk-claude'
    skriv(falsk / 'claude', FALSK_CLAUDE)
    (falsk / 'claude').chmod(0o755)
    s = 'prov-start'
    kund(s, rot=ar)
    miljo = startmiljo(PATH=str(falsk) + os.pathsep + os.environ.get('PATH', ''))
    p = subprocess.run([PY, '-B', str(ar / 'kontroller' / 'prototyp.py'), s, '--vanta', '120'], capture_output=True, text=True,
                       cwd=str(ar), env=miljo, timeout=240)
    st = json.loads((ar / 'underlag' / s / 'atelje' / 'STATUS.json').read_text())
    poster = sorted((ar / 'kunder' / s / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert poster, ('arbetaren skrev ingen slutpost', p.returncode, p.stdout[-600:], p.stderr[-600:])
    post = json.loads(poster[-1].read_text())
    assert p.returncode == post['slutkod'] == 4 and post['utfall']['slag'] == 'fel' and post['utfall']['steg'] == 'forska', (p.returncode, post['utfall'])
    assert 'sessionen föll' in post['utfall']['text'] and post['korning']['startad'] == st['startad'] and st['slutpost'] == post['slutpost'], post['utfall']
    rader = p.stdout.split('\n')
    assert ('Skapandeflödet %s, körningen %s (läge ny; %s): %s' % (s, st['startad'], post['moment'], post['utfall']['text'])) in rader, p.stdout[-800:]
    assert p.stdout.rstrip('\n').endswith(post['slutkod_text']) and ('Slutpost: %s' % post['slutpost']) in rader, p.stdout[-400:]
    assert json.loads((poster[-1].parent / 'STATUS.json').read_text()) == st, 'postens STATUS.json är körningens'
    sess = [json.loads(x.read_text()) for x in (ar / 'underlag' / s / 'atelje' / 'sessioner').glob('*.json')]
    assert sess and all(x.get('slut') and x.get('utfall') for x in sess), ('sessionen har sitt slut i förteckningen', sess)


SOVANDE_CLAUDE = r'''#!/bin/sh
case "$*" in *--help*) echo "Usage: claude [--session-id <uuid>]"; exit 0;; esac
cat > /dev/null
sleep 300
echo '{"type":"result","subtype":"success","is_error":false,"result":"sov","num_turns":1,"duration_ms":10}'
'''

# Provets sitecustomize: Python importerar den vid starten av varje process som har katalogen i PYTHONPATH, också arbetaren
# som prototyp.py startar (python atelje.py <slug> --arbetare, alltså som __main__). Med NWP_PROV_ATELJE_STEG satt ersätts
# kandidatflödets steg före skisserna, och skisserna själva, med steg utan sessioner, utom den riktiga atelje.session mot
# den sovande falska claude. Repots kod ändras inte, och arbetaren startar som i verkligheten.
SITECUSTOMIZE = r'''
import os, sys
if os.environ.get('NWP_PROV_ATELJE_STEG'):
    sys.path.insert(0, os.environ['NWP_PROV_ATELJE_STEG'])
    import json
    import kandidater, atelje

    IDS = ['k01', 'k02']

    def skriv(f, d):
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
        return d

    def planera(slug, n, lage=None):
        plan = skriv(kandidater.rot(slug) / 'KANDIDATPLAN.json', {'tid': atelje.nu(), 'lage': 'skiss', 'kandidater': {k: {'titel': 'Förslag %s' % k} for k in IDS}})
        for k in IDS:
            kandidater.satt_status(slug, k, 'planerad', 'uppdraget skrivet', titel='Förslag %s' % k)
        return plan

    def behandla_skiss(slug, kid):
        kandidater.satt_status(slug, kid, 'under_arbete', 'skiss, försök 1', forsok=1, startad=atelje.nu(), frist=2700)
        d = kandidater.kdir(slug, kid)
        try:
            if kid == 'k01':  # som skissa: sessionens pid i kandidatens status
                atelje.session('prov', ['Read'], d / 'svar-skiss-1.json', max_turer=5, frist=600, slug=slug,
                               vid_start=lambda pid: kandidater.satt_status(slug, kid, 'under_arbete', 'skiss, försök 1', session_pid=pid))
            else:  # som skisskritiken: ingen vid_start och inget session_pid
                kandidater.satt_status(slug, kid, 'under_arbete', 'den kritiska granskaren ser bilderna')
                atelje.session('prov', ['Read'], d / 'svar-skisskritik-1.json', max_turer=5, frist=600, slug=slug)
        except RuntimeError:
            if atelje.STOPP.is_set():
                raise atelje.Stoppad('försöket avbröts av stoppet')
            raise
        if atelje.STOPP.is_set():
            raise atelje.Stoppad('försöket avbröts av stoppet')
        return kandidater.satt_status(slug, kid, 'klar', 'efter sessionen')

    kandidater.leverera_metod = lambda slug: {}
    kandidater.forska = lambda slug, n, skiss=False: skriv(kandidater.rot(slug) / 'FORSKNING.json', {'tid': atelje.nu(), 'fel': None, 'nytt': {'paket': None, 'sajter': [], 'tjanster': None}})
    kandidater.planera = planera
    kandidater.uppdragsmaterial = lambda slug, klient=None: skriv(kandidater.rot(slug) / kandidater.UPPDRAGSMATERIAL, {'tid': atelje.nu()}) and {}
    kandidater.planprovning = lambda slug: skriv(kandidater.rot(slug) / 'PLANPROVNING.json', {'tid': atelje.nu(), 'andrade': 0, 'sekunder': 1}) and {'andrade': 0, 'sekunder': 1}
    kandidater.PARALLELLT = 2
    kandidater.behandla_skiss = behandla_skiss
'''


def stopp_verklig(sig=None):
    import ateljeslut
    ar = ateljerepo()
    s = 'prov-stoppvag' + ('-%d' % sig if sig else '')
    u, k = kund(s, rot=ar)
    sov = TMP / 'sovande-claude'
    skriv(sov / 'claude', SOVANDE_CLAUDE)
    (sov / 'claude').chmod(0o755)
    skriv(TMP / 'pythonpath' / 'sitecustomize.py', SITECUSTOMIZE)
    miljo = startmiljo(PATH=str(sov) + os.pathsep + os.environ.get('PATH', ''), PYTHONPATH=str(TMP / 'pythonpath'), NWP_PROV_ATELJE_STEG=str(ar / 'kontroller'))
    markor = str(sov)
    status_f = u / 'atelje' / 'STATUS.json'
    sess_dir = u / 'atelje' / 'sessioner'
    prot = subprocess.Popen([PY, '-B', str(ar / 'kontroller' / 'prototyp.py'), s, '--vanta', '150'], cwd=str(ar), env=miljo,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        slut = time.time() + 90
        while True:
            sess = sorted(sess_dir.glob('*.json')) if sess_dir.is_dir() else []
            st = atelje.las_json(status_f) or {}
            if len(sess) >= 2 and len(processer_med(markor)) >= 2 and st.get('pid') and st.get('steg') == 'skapa':
                break
            assert prot.poll() is None, ('prototyp.py slutade före stoppet', prot.returncode, prot.communicate()[0][-1200:])
            assert time.time() < slut, ('sessionerna kom inte igång', len(sess), processer_med(markor), st.get('steg'))
            time.sleep(0.2)
        time.sleep(0.5)
        fore = {kid: json.loads((u / 'atelje' / 'kandidater' / kid / 'STATUS.json').read_text()).get('status') for kid in ('k01', 'k02')}
        assert fore == {'k01': 'under_arbete', 'k02': 'under_arbete'}, fore
        if sig:
            os.kill(st['pid'], sig)  # arbetarens eget stopp, utan --stoppa:s reservstädning
        else:
            r = subprocess.run([PY, '-B', str(ar / 'kontroller' / 'atelje.py'), s, '--stoppa'], cwd=str(ar), env=miljo, capture_output=True, text=True, timeout=120)
            assert r.returncode == 0 and 'Körningen stoppad' in r.stdout and 'Slutpost:' in r.stdout, (r.returncode, r.stdout[-600:], r.stderr[-600:])
        ut, _ = prot.communicate(timeout=90)
        slut = time.time() + 5
        while time.time() < slut and processer_med(markor):
            time.sleep(0.2)
        kvar = processer_med(markor)
        assert not kvar, 'sessioner lever kvar efter stoppet (utan tidsgräns, och de kan skriva vidare): %s' % kvar
        sess = [json.loads(f.read_text()) for f in sorted(sess_dir.glob('*.json'))]
        assert len(sess) >= 2 and all(x.get('slut') and str(x.get('utfall') or '').startswith('avbruten vid stoppet') for x in sess), (
            'varje session i körningen har slut och utfall', [(x.get('roll'), x.get('slut'), x.get('utfall')) for x in sess])
        kst = {kid: json.loads((u / 'atelje' / 'kandidater' / kid / 'STATUS.json').read_text()) for kid in ('k01', 'k02')}
        assert all(v['status'] == 'avbruten' and (v.get('avbruten_vid') or {}).get('orsak') == 'stoppet' for v in kst.values()), {k_: (v['status'], v.get('avbruten_vid')) for k_, v in kst.items()}
        st = json.loads(status_f.read_text())
        poster = sorted((k / 'atelje' / 'korningar').glob('*/SLUT.json'))
        assert poster and st.get('slutpost'), ('ingen slutpost', st.get('steg'), st.get('slutpost_fel'))
        post = json.loads(poster[-1].read_text())
        assert post['utfall']['slag'] == 'stoppad' and post['utfall']['steg'] == 'skapa' and post['slutkod'] == 4 == prot.returncode, (post['utfall'], prot.returncode, ut[-600:])
        assert ateljeslut.text(post) in ut, ('prototyp.py:s besked är postens', ut[-800:])
    finally:
        if prot.poll() is None:
            doda([prot.pid])
            prot.wait(timeout=10)
        doda(processer_med(markor))


@fall('ägarens stopp genom den verkliga vägen: prototyp.py startar arbetaren som __main__, --stoppa avslutar alla sessioner med slut och utfall och prototyp.py ger postens slutkod')
def _stopp_verklig():
    stopp_verklig()


@fall('SIGTERM och SIGINT direkt till CLI-arbetaren avslutar dess sessioner och skriver slut och utfall, även utan --stoppa:s reservstädning')
def _signal_verklig():
    for sig in (signal.SIGTERM, signal.SIGINT):
        stopp_verklig(sig)


STARTKONTROLL_STUB = '''"""Provets startkontroll (prov_ateljeslut.py): stoppar varje start, som när Mobbin inte svarar."""


def for_start(slug, start):
    return {'status': 'stoppad', 'stoppar': ['mobbin: provets stopp'], 'kvitto': 'underlag/%s/atelje/STARTKVITTO-STOPP.md' % slug, 'start': start}


def sammanfattning(kv):
    return kv
'''


@fall('startkontrollens stopp av en ny start: genom den verkliga vägen kommer prototyp.py:s besked och slutkod ur startens post direkt, och varken där eller när den förra körningens resultat står kvar märks den förra posten ersatt')
def _startkontroll_stopp():
    import ateljeslut
    ar = ateljerepo()
    s = 'prov-start'  # körningen i startvägsfallet, med sin post
    poster0 = sorted((ar / 'kunder' / s / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert len(poster0) == 1, poster0
    stub = ar / 'kontroller' / 'startkontroll.py'
    original = stub.read_bytes()
    skriv(stub, STARTKONTROLL_STUB)
    try:
        miljo = startmiljo(PATH=str(TMP / 'falsk-claude') + os.pathsep + os.environ.get('PATH', ''))
        del miljo['NWP_STARTKONTROLL']
        t0 = time.time()
        p = subprocess.run([PY, '-B', str(ar / 'kontroller' / 'prototyp.py'), s, '--om', '--vanta', '60'], capture_output=True, text=True, cwd=str(ar), env=miljo, timeout=150)
        tog = time.time() - t0
    finally:
        stub.write_bytes(original)
    poster = sorted((ar / 'kunder' / s / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert len(poster) == 2, ('startens post', poster, p.stdout[-400:])
    post, forra = json.loads(poster[-1].read_text()), json.loads(poster0[0].read_text())
    assert post['utfall']['slag'] == 'startkontrollen' and 'provets stopp' in post['utfall']['text'] and post['slutkod'] == 4, post['utfall']
    assert p.returncode == 4 and tog < 45 and 'Ateljén pågår' not in p.stdout and ateljeslut.text(post) in p.stdout, (p.returncode, round(tog), p.stdout[-700:])
    assert forra['rapportstatus'] != 'ersatt' and forra.get('ersatt_av') in (None, 'ej angivet'), ('den förra körningens post märktes ersatt fast ingen körning gjordes', forra['rapportstatus'])
    st = json.loads((ar / 'underlag' / s / 'atelje' / 'STATUS.json').read_text())
    assert st['steg'] == 'fel' and 'pid' not in st and st.get('slutpost') == post['slutpost'], (st.get('steg'), st.get('slutpost'))
    # den förra körningens resultat står kvar (kandidaterna väntar på ägaren): statusen bär stoppet, beskedet är startens post
    s2 = 'prov-sk-forra'
    u2, k2 = kund(s2)
    rot2 = u2 / 'atelje'
    skriv(rot2 / 'KANDIDATPLAN.json', {'tid': '2026-10-07T08:00:00Z', 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}}})
    klar_kandidat(s2, 'k01')
    st0 = {'slug': s2, 'startad': '2026-10-07T08:00:00Z', 'klar': '2026-10-07T08:30:00Z', 'steg': 'klar_for_bedomning', 'lage': 'ny', 'kandidatflode': True,
           'kandidatlage': 'skiss', 'tider': {'start': '2026-10-07T08:00:00Z'}, 'kandidater': {'k01': 'klar'}, 'skal': '1 av 1 skisser klara'}
    skriv(rot2 / 'STATUS.json', st0)
    import startkontroll
    spara = (startkontroll.for_start, startkontroll.sammanfattning)
    startkontroll.for_start = lambda slug, start: {'status': 'stoppad', 'stoppar': ['mobbin: provets stopp'], 'kvitto': 'underlag/%s/atelje/STARTKVITTO-STOPP.md' % slug}
    startkontroll.sammanfattning = lambda kv: kv
    try:
        rc = atelje.arbeta(s2, 'ny')
    finally:
        startkontroll.for_start, startkontroll.sammanfattning = spara
    st = json.loads((rot2 / 'STATUS.json').read_text())
    assert rc == 1 and st['steg'] == 'klar_for_bedomning' and 'pid' not in st and (st.get('startkontroll_stopp') or {}).get('slutpost'), (rc, st.get('steg'), st.get('startkontroll_stopp'))
    poster = sorted((k2 / 'atelje' / 'korningar').glob('*/SLUT.json'))
    assert len(poster) == 2, poster
    forra, post = json.loads(poster[0].read_text()), json.loads(poster[1].read_text())
    assert forra['typ'] == ateljeslut.TYP_EFTERHAND and forra['rapportstatus'] != 'ersatt', ('den förra körningens post i efterhand märktes ersatt', forra['rapportstatus'])
    assert post['utfall']['slag'] == 'startkontrollen' and st['startkontroll_stopp']['slutpost'] == post['slutpost'] and post['kandidater'] == [], post['utfall']
    ut = io.StringIO()
    with contextlib.redirect_stdout(ut):
        rc2 = atelje.vanta(rot2, 1)
    assert rc2 == 4 and ut.getvalue().strip() == ateljeslut.text(post), ('beskedet är startens post', rc2, ut.getvalue()[-500:])


@fall('omtagets stopp av kvarlevande sessioner tar också en kandidat som stoppet märkte avbruten: dess session avslutas med sitt träd')
def _kvarvarande():
    s = 'prov-kvar'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'KANDIDATPLAN.json', {'tid': atelje.nu(), 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}}})
    falsk = TMP / 'kvar-claude'
    skriv(falsk / 'claude', '#!/bin/sh\nsleep 300\n')
    (falsk / 'claude').chmod(0o755)
    p = subprocess.Popen([str(falsk / 'claude'), '-p', '--allowedTools', 'Read', s], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        time.sleep(0.3)
        assert atelje.kundens_session(p.pid, s), 'fixturen: processen känns igen som kundens flödessession'
        kandidater.satt_status(s, 'k01', 'avbruten', 'avbruten vid stoppet %s' % atelje.nu(), forsok=1, session_pid=p.pid,
                               avbruten_vid={'orsak': 'stoppet', 'tid': atelje.nu()})
        stoppade = atelje.stoppa_kvarvarande(s, rot, {'pid': None})
        assert p.pid in stoppade, ('sessionen hos den märkta kandidaten lämnades', stoppade)
        slut = time.time() + 5
        while time.time() < slut and atelje.lever(p.pid) and p.poll() is None:
            time.sleep(0.1)
        assert p.poll() is not None or not atelje.lever(p.pid), 'sessionen lever'
    finally:
        doda([p.pid])
    # --stoppa efter en arbetare som dog: en session utan session_pid (som skisskritikens) står bara i förteckningen; den
    # avslutas och får sluttid och utfall, också när arbetaren inte finns längre
    startad = atelje.nu()
    p2 = subprocess.Popen([str(falsk / 'claude'), '-p', '--allowedTools', 'Read', s], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        time.sleep(0.3)
        sid = str(uuid.uuid4())
        observation.anmal(s, sid, kandidater.kdir(s, 'k01') / 'svar-skisskritik-1.json', 'claude-fable-5-1', p2.pid)
        ut = io.StringIO()
        with contextlib.redirect_stdout(ut):
            rc = atelje.stoppa(s, rot, {'slug': s, 'startad': startad, 'steg': 'skapa', 'pid': None})
        assert rc == 0 and str(p2.pid) in ut.getvalue(), ('--stoppa lämnade förteckningens session', ut.getvalue())
        slut = time.time() + 5
        while time.time() < slut and p2.poll() is None and atelje.lever(p2.pid):
            time.sleep(0.1)
        assert p2.poll() is not None or not atelje.lever(p2.pid), 'förteckningens session lever efter --stoppa'
        post = json.loads((observation.katalog(s) / ('%s.json' % sid)).read_text())
        assert post['slut'] and post['utfall'] == 'avbruten vid stoppet', ('sessionen fick inget slut av --stoppa', post)
    finally:
        doda([p2.pid])


def dom_kommando(s, kalla, beslut):
    """kontroller/skapande.py dom med provets text; argparses avslut (SystemExit) blir slutkoden."""
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return skapande.main(['dom', s, '--kalla', kalla, '--beslut', beslut, '--fil', str(TMP / 'ai.txt')])
    except SystemExit as e:
        return e.code


@fall('en körning utan en enda valbar kandidat får slutkod 6 och säger att ägaren inget har att välja bland; ägarens val (valj) står i posten som ej bedömt med vad valet betyder, forkasta som nej och godkand som ja')
def _utan_valbara_och_valj():
    import ateljeslut
    s = 'prov-utanvalbara'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'KANDIDATPLAN.json', {'tid': '2026-10-07T07:00:00Z', 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}, 'k02': {'titel': 'Två'}}})
    for kid in ('k01', 'k02'):
        kandidater.satt_status(s, kid, 'fel', 'bygget föll', forsok=2)
    st = {'slug': s, 'startad': '2026-10-07T07:00:00Z', 'klar': '2026-10-07T07:40:00Z', 'steg': 'klar_for_bedomning', 'lage': 'ny', 'kandidatflode': True,
          'kandidatlage': 'skiss', 'skal': '0 av 2 skisser klara för ägarens bedömning', 'kandidater': {'k01': 'fel', 'k02': 'fel'}, 'tider': {'start': '2026-10-07T07:00:00Z'}}
    post = ateljeslut.bygg(s, st, '20261007T070000Z')
    assert post['slutkod'] == 6 and post['utfall']['slag'] == 'klar' and 'ingen kandidat blev valbar (0 av 2)' in post['utfall']['text'], (post['slutkod'], post['utfall'])
    assert post['slutkod_text'].startswith('Slutkod 6: ingen startsida att bygga vidare på; klar, men ingen kandidat blev valbar'), post['slutkod_text']
    t = post['tillstand']
    assert t['sessionen_avslutad']['varde'] is True and t['agaren_godkanner']['varde'] is None and 'inget att bedöma' in t['agaren_godkanner']['text'], t['agaren_godkanner']
    assert post['bedomningsutfall'].startswith('inget att bedöma (slutkod 6)'), post['bedomningsutfall']
    tom = ateljeslut.bygg(s, dict(st, kandidater={}), '20261007T070000Z')
    assert tom['slutkod'] == 6 and 'ingen kandidat blev valbar (0 av 0)' in tom['utfall']['text'], ('tom kandidatlista', tom['utfall'])
    # ägarens val efter en körning med en valbar kandidat (KAN-9)
    s2 = 'prov-valj'
    u2, _k2 = kund(s2)
    skriv(u2 / 'atelje' / 'KANDIDATPLAN.json', {'tid': '2026-10-07T08:00:00Z', 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}}})
    k01 = klar_kandidat(s2, 'k01')
    st2 = {'slug': s2, 'startad': '2026-10-07T08:00:00Z', 'klar': '2026-10-07T08:30:00Z', 'steg': 'klar_for_bedomning', 'lage': 'ny', 'kandidatflode': True,
           'kandidatlage': 'skiss', 'kandidater': {'k01': 'klar'}, 'tider': {'start': '2026-10-07T08:00:00Z'}}
    logg(s2, dom('2026-10-07T09:00:00Z', 'ägaren', 'valj', 'Välj Ett.', kandidater=[{'id': 'k01', 'version': k01['version']}]))
    ag = ateljeslut.bygg(s2, st2, '20261007T080000Z')['tillstand']['agaren_godkanner']
    assert ag['varde'] is None and 'beslut valj' in ag['text'] and 'förfining' in ag['text'] and 'inget nej' in ag['text'], ('ägarens val stod som nej', ag)
    rad_ = next(r for r in ateljeslut.text(ateljeslut.bygg(s2, st2, '20261007T080000Z')).split('\n') if r.strip().startswith('ägaren godkänner'))
    assert rad_.strip().startswith('ägaren godkänner: ej bedömt') and 'förfining' in rad_, rad_
    logg(s2, dom('2026-10-07T09:30:00Z', 'ägaren', 'forkasta', 'Förkasta alla.'))
    assert ateljeslut.bygg(s2, st2, '20261007T080000Z')['tillstand']['agaren_godkanner']['varde'] is False
    logg(s2, dom('2026-10-07T10:00:00Z', 'ägaren', 'godkand', 'Godkänd.'))
    assert ateljeslut.bygg(s2, st2, '20261007T080000Z')['tillstand']['agaren_godkanner']['varde'] is True


@fall('postens skrivning: domen körningen följer är ägarens egen, två poster samma sekund får var sin katalog, en länk på målet följs inte när redovisningen kopieras, och en körning som pågår får ingen post i efterhand')
def _postens_skrivning():
    import ateljeslut
    s = 'prov-skriv'
    u, k = kund(s)
    rot = u / 'atelje'
    st = {'slug': s, 'startad': '2026-10-07T06:00:00Z', 'klar': '2026-10-07T06:30:00Z', 'steg': 'klar', 'lage': 'ny'}
    skriv(rot / 'STATUS.json', st)
    skriv(rot / 'REDOVISNING.md', '# Redovisning · %s · 2026-10-07T06:30:00Z\n\nKörningens egen.\n' % s)
    logg(s, dom('2026-10-07T05:00:00Z', 'ägaren', 'ny_riktning', 'Ny riktning.'), dom('2026-10-07T05:30:00Z', 'vidarebefordrad AI-bedömning', 'putsa', 'Putsa.'))
    post = ateljeslut.bygg(s, st, '20261007T060000Z')
    assert post['agarens_beslut']['foljer']['tid'] == '2026-10-07T05:00:00Z' and post['agarens_beslut']['foljer']['agarens'], ('domen körningen följer', post['agarens_beslut']['foljer'])
    f1, p1 = ateljeslut.skriv_korning(s, dict(st))
    f2, p2 = ateljeslut.skriv_korning(s, dict(st))
    assert f1 != f2 and f2.parent.name == f1.parent.name + '-2' and f1.is_file() and json.loads(f1.read_text())['rapportstatus'] == 'ersatt', (f1, f2)
    korning3 = f1.parent.name + '-3'
    d3 = ateljeslut.postkatalog(s, korning3)
    mal = skriv(TMP / 'lankmal.md', 'ORÖRD')
    os.symlink(mal, d3 / 'REDOVISNING.md')
    ateljeslut.skriv(s, korning3, ateljeslut.bygg(s, st, korning3), status=st, redovisning=rot / 'REDOVISNING.md')
    assert mal.read_text() == 'ORÖRD' and not (d3 / 'REDOVISNING.md').is_symlink() and (d3 / 'REDOVISNING.md').read_text().startswith('# Redovisning'), 'länken på målet följdes'
    tempfalla = d3 / '.REDOVISNING.md.tmp'
    os.symlink(mal, tempfalla)
    ateljeslut.skriv(s, korning3, ateljeslut.bygg(s, st, korning3), status=st, redovisning=rot / 'REDOVISNING.md')
    assert mal.read_text() == 'ORÖRD' and tempfalla.is_symlink(), 'länken på ett förutsägbart tempnamn följdes eller togs bort'
    assert (d3 / 'REDOVISNING.md').read_bytes() == (rot / 'REDOVISNING.md').read_bytes(), 'redovisningens byte ändrades'
    assert ateljeslut.bevara_forra(s, dict(st, steg='skapa', pid=os.getpid())) == (None, None), 'en körning som pågår fick en post i efterhand'
    ny_slug = 'prov-levande-utanpost'
    kund(ny_slug)
    aktiv = dict(st, slug=ny_slug, steg='skapa', pid=os.getpid())
    assert ateljeslut.bevara_forra(ny_slug, aktiv) == (None, None), 'en levande körning utan tidigare post fick en slutpost'
    assert not ateljeslut.slutposter(ny_slug), 'posten skrevs trots att körningen lever'


@fall('en vidarebefordrad AI-bedömning mot ett ägarbeslut: den godkänner inget, drar inte tillbaka godkännandet, ändrar inte läget, stoppar inget bygge och lyfter inte blindningen')
def _vidarebefordrad():
    s = 'prov-avs'
    u, k = kund(s)
    rot = u / 'atelje'
    kod = skriv(rot / 'vinnare' / 'kod' / 'index.astro', '<h1>Godkänd</h1>')
    t_klar, t_godk, t_ai = '2026-10-06T10:00:00Z', '2026-10-06T11:00:00Z', '2026-10-06T12:00:00Z'
    skriv(rot / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'klar': t_klar, 'steg': 'klar', 'lage': 'ny'})
    skriv(rot / 'VINNARE.json', {'riktning': 1, 'godkand': {'tid': t_godk, 'av': 'ägaren', 'text': 'Godkänd.', 'sha_index': sha(kod)}})
    logg(s, dom(t_godk, 'ägaren', 'godkand', 'Godkänd.'))
    assert skapande.godkand_giltig(s, U, K)[0], 'utgångsläget: ägarens godkännande gäller'
    # en AI-bedömning som ägaren klistrat in, förd som "ägaren via Codex" utan belägg (så fördes C5): räknas inte
    logg(s, dom(t_ai, 'ägaren via Codex', 'ny_riktning', 'Jag tycker att riktningen inte bär.'))
    ok, skal = skapande.godkand_giltig(s, U, K)
    assert ok and skapande.senaste(s, underlag=U)['tid'] == t_godk, ('en vidarebefordrad bedömning drog tillbaka godkännandet', skal)
    assert prototyp.lage(s)[0] == 'godkand', prototyp.lage(s)
    assert SV.agarens_senare_dom(RT, s, t_klar) is None, 'stoppvakten stannade bygget på en vidarebefordrad bedömning'
    os.environ['NWP_SLUG'] = s
    try:
        ut = io.StringIO()
        with contextlib.redirect_stdout(ut):
            rc = atelje.main([s])
        assert rc != 6 and 'ska inte byggas vidare' not in ut.getvalue(), ('slutkod 6 i bygget av en vidarebefordrad bedömning', rc, ut.getvalue()[-300:])
    finally:
        del os.environ['NWP_SLUG']
    # korslut: godkännandets avsändare ur domloggen
    sida = korslut.startsidan(k)
    assert sida['avsandare'].startswith('ägarens egna ord och beslut (ägaren)') and 'ägaren via ägaren' not in sida['text'], sida
    # två rader med godkännandets tid: en vidarebefordrad bedömning bredvid ägarens tar inte över avsändaren (KAN-6)
    logg(s, dom(t_godk, 'vidarebefordrad AI-bedömning', 'godkand', 'Godkänn den.'))
    sida = korslut.startsidan(k)
    assert sida['avsandare_agarens'] and sida['avsandare'].startswith('ägarens egna ord och beslut (ägaren)') and sida['domrad'] == 1, (
        'en vidarebefordrad rad samma sekund blev godkännandets avsändare', sida)
    # med källan "vidarebefordrad AI-bedömning", genom samma väg som en dom utanför dashboarden: skrivs, men styr inget
    skriv(TMP / 'ai.txt', 'Byt till en ny riktning.')
    spara_u = skapande.UNDERLAG
    skapande.UNDERLAG = U
    try:
        assert dom_kommando(s, 'vidarebefordrad AI-bedömning', 'ny_riktning') == 0, 'källan för en vidarebefordrad bedömning'
        # ägaren via Codex utan belägg vägras nu, liksom ägarens ord utanför dashboarden utan belägg
        assert dom_kommando(s, 'ägaren via Codex', 'putsa') == 2 and dom_kommando(s, 'ägaren', 'putsa') == 2, 'ägarens ord kräver belägg'
    finally:
        skapande.UNDERLAG = spara_u
    sista = skapande.domar(s, U)[-1]
    assert sista['kalla'] == 'vidarebefordrad AI-bedömning' and not skapande.ar_agarens(sista), sista
    try:
        skapande.lagg_till_dom(s, 'ägaren via Codex', 'putsa', 'Utan belägg.', underlag=U)
        raise AssertionError('ägaren via Codex utan belägg skrevs')
    except ValueError as e:
        assert 'belägg' in str(e) and skapande.domar(s, U)[-1] == sista, e
    assert skapande.avsandare(sista)['text'] == 'vidarebefordrad AI-bedömning (vidarebefordrad AI-bedömning)', skapande.avsandare(sista)
    assert skapande.godkand_giltig(s, U, K)[0] and prototyp.lage(s)[0] == 'godkand'
    try:  # en vidarebefordrad bedömning godkänner aldrig en startsida
        atelje.doma(s, 'vidarebefordrad AI-bedömning', 'godkand', 'Godkänn den.')
    except ValueError:
        pass
    assert (json.loads((rot / 'VINNARE.json').read_text())['godkand'] or {}).get('tid') == t_godk, 'en vidarebefordrad bedömning skrev om godkännandet'
    # blindningen: bara ägarens eget beslut efter planen lyfter den
    skriv(rot / 'KANDIDATPLAN.json', {'tid': '2026-10-06T13:00:00Z', 'lage': 'skiss', 'kandidater': {'k01': {}}})
    logg(s, dom('2026-10-06T14:00:00Z', 'vidarebefordrad AI-bedömning', 'forkasta', 'Förkasta.'),
         dom('2026-10-06T14:30:00Z', 'ägaren via Codex', 'forkasta', 'Förkasta alla.'))
    assert not kandidater.domd(s), 'en vidarebefordrad bedömning lyfte blindningen'
    logg(s, dom('2026-10-06T15:00:00Z', 'ägaren via Codex', 'jamfor', 'Jämför.', belagg='ägarens meddelande 2026-10-06T15:00Z, ordagrant (provet)'))
    assert kandidater.domd(s) and skapande.senaste(s, underlag=U)['tid'] == '2026-10-06T15:00:00Z', 'ägarens ord via Codex med belägg räknas'
    assert not skapande.godkand_giltig(s, U, K)[0], 'ägarens belagda senare dom drar tillbaka godkännandet'


@fall('en äldre domrad utan belägg står som ej belagd, styr varken läget, prompterna eller slutposten, och loggen skrivs aldrig om')
def _aldre_rad():
    s = 'prov-aldre'
    u, _k = kund(s)
    f = logg(s, dom('2026-10-05T10:00:00Z', 'ägaren via Codex', 'ny_riktning', 'GAMMAL RAD UTAN BELÄGG.'))
    fore = sha(f)
    assert prototyp.lage(s)[0] == 'om', ('en obelagd rad gav läget', prototyp.lage(s))
    assert not any('GAMMAL RAD' in r for r in skapande.kritikrader(s, underlag=U, aktuella=True)), 'en obelagd rad stod i prompten som ägarens dom'
    assert skapande.senaste(s, underlag=U) is None and not skapande.aldre_domar(s, U)
    rad = skapande.domar(s, U)[0]
    av = skapande.avsandare(rad)
    assert av['text'] == 'ej belagd (källan ägaren via Codex, utan belägg)' and av['typ'] is None and not av['agarens'], av
    # i ateljéns slutpost står raden med sin avsändare, och den räknas inte som ägarens
    import ateljeslut
    st = {'slug': s, 'startad': '2026-10-05T09:00:00Z', 'steg': 'klar_for_bedomning', 'klar': '2026-10-05T09:30:00Z', 'lage': 'ny', 'kandidatflode': True, 'tider': {}}
    post = ateljeslut.bygg(s, st, '20261005T090000Z')
    e = post['agarens_beslut']['efter']
    assert len(e) == 1 and e[0]['avsandare'].startswith('ej belagd') and not e[0]['agarens'] and post['tillstand']['agaren_godkanner']['varde'] is None, e
    assert 'är inte ägarens och räknas inte' in post['tillstand']['agaren_godkanner']['text']
    assert sha(f) == fore, 'domloggen skrevs om'


@fall('ett belägg i efterhand fästs vid den befintliga raden i en bilaga bunden till radens sha256: raden räknas som ägarens utan att loggen skrivs om och utan att bli en ny dom; ett belägg till en annan källa eller av blanktecken vägras; en trasig bilagerad syns och räknas inte')
def _belagg_bilaga():
    import ateljeslut
    s = 'prov-bilaga'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'KANDIDATPLAN.json', {'tid': '2026-10-05T08:00:00Z', 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett'}}})
    klar_kandidat(s, 'k01')
    skriv(rot / 'STATUS.json', {'slug': s, 'startad': '2026-10-05T09:00:00Z', 'klar': '2026-10-05T09:30:00Z', 'steg': 'klar_for_bedomning', 'lage': 'ny',
                                'kandidatflode': True, 'kandidatlage': 'skiss', 'kandidater': {'k01': 'klar'}, 'tider': {'start': '2026-10-05T09:00:00Z'}})
    t1 = '2026-10-05T10:00:00Z'
    f = logg(s, dom(t1, 'ägaren via Codex', 'valj', 'VALD RAD UTAN BELÄGG.', kandidater=[{'id': 'k01', 'version': 'v' * 64}]))
    fore = sha(f)
    assert skapande.senaste(s, underlag=U) is None and prototyp.lage(s)[0] == 'vanta', 'utgångsläget: raden utan belägg räknas inte'
    for rad_, text_ in ((1, '   '), (7, 'finns inte')):
        try:
            skapande.lagg_till_belagg(s, rad_, text_, underlag=U)
            raise AssertionError('ett belägg %s skrevs' % ('av blanktecken' if rad_ == 1 else 'för en rad som inte finns'))
        except ValueError:
            pass
    assert not (u / skapande.BELAGGFIL).exists(), 'ett vägrat belägg skrevs ändå'
    post_b = skapande.lagg_till_belagg(s, 1, 'ägarens meddelande 2026-10-05 10:00, ordagrant (provet)', underlag=U, tid='2026-10-07T12:00:00Z')
    lg = skapande.domlogg(s, U)
    assert post_b['kalla'] == 'ägaren' and post_b['sha256'] == lg['domar'][0][1] and post_b['dom_rad'] == 1 and post_b['dom_tid'] == t1, post_b
    assert sha(f) == fore and len(skapande.jsonl_rader(f)) == 1, 'domloggen skrevs om, eller fick en ny rad'
    d = lg['domar'][0][2]
    assert skapande.ar_agarens(d) and d['belagg'].startswith('ägarens meddelande') and d['belagg_bilaga']['rad'] == 1 and d['belagg_bilaga']['tid'] == '2026-10-07T12:00:00Z', d
    assert skapande.senaste(s, underlag=U)['tid'] == t1, 'belägget blev ett nytt beslut i stället för att gälla raden'
    av = skapande.avsandare(d)
    assert av['agarens'] and av['typ'] == 'agaren' and 'belägget i bilagan' in av['text'] and 'rad 1' in av['text'], av
    assert prototyp.lage(s)[0] == 'valda', prototyp.lage(s)
    # i ateljéns slutpost räknas raden som ägarens, med belägget i avsändaren
    post = ateljeslut.bygg(s, json.loads((rot / 'STATUS.json').read_text()), '20261005T090000Z')
    e = post['agarens_beslut']['efter']
    assert len(e) == 1 and e[0]['agarens'] and 'bilagan' in e[0]['avsandare'] and post['tillstand']['agaren_godkanner']['varde'] is None, e
    # källan ägaren behöver inget belägg, och en vidarebefordrad bedömning kan aldrig få ett
    logg(s, dom('2026-10-05T11:00:00Z', 'ägaren', 'jamfor', 'Jämför.'), dom('2026-10-05T11:30:00Z', 'vidarebefordrad AI-bedömning', 'forkasta', 'Förkasta.'))
    for rad_, ord_ in ((2, 'behöver inget belägg'), (3, 'aldrig ägarens beslut')):
        try:
            skapande.lagg_till_belagg(s, rad_, 'ett belägg', underlag=U)
            raise AssertionError('rad %d fick ett belägg' % rad_)
        except ValueError as e_:
            assert ord_ in str(e_), e_
    assert not skapande.ar_agarens(skapande.domar(s, U)[2]), 'den vidarebefordrade raden blev ägarens'
    # en trasig rad i bilagan syns med plats och skäl, räknas inte, och det giltiga belägget gäller fortfarande
    with open(u / skapande.BELAGGFIL, 'ab') as fh:
        fh.write(b'{"kalla": "\xc3\xa4garen", "sha256": "abc"}\ntrasig\n')
    lg = skapande.domlogg(s, U)
    assert [x['rad'] for x in lg['bilaga_olasbara']] == [2, 3] and 'bilagans form' in lg['bilaga_olasbara'][0]['skal'] and lg['bilaga_olasbara'][1]['skal'].startswith('inte JSON'), lg['bilaga_olasbara']
    assert skapande.ar_agarens(lg['domar'][0][2]) and skapande.senaste(s, underlag=U)['tid'] == '2026-10-05T11:00:00Z', 'det giltiga belägget gäller fortfarande'
    post = ateljeslut.bygg(s, json.loads((rot / 'STATUS.json').read_text()), '20261005T090000Z')
    assert [x['rad'] for x in post['agarens_beslut']['bilaga_olasbara']] == [2, 3]
    # kommandot: ett belägg i efterhand utanför dashboarden, och visa säger bilagans trasiga rader
    spara_u = skapande.UNDERLAG
    skapande.UNDERLAG = U
    try:
        ut = io.StringIO()
        with contextlib.redirect_stdout(ut), contextlib.redirect_stderr(io.StringIO()):
            rc = skapande.main(['belagg', s, '--rad', '1', '--belagg', 'ägarens meddelande 2026-10-05 10:00 (provet, igen)'])
        assert rc == 0 and 'belägget tillagt för rad 1' in ut.getvalue() and 'bilagan' in ut.getvalue(), (rc, ut.getvalue())
        with contextlib.redirect_stdout(ut), contextlib.redirect_stderr(io.StringIO()):
            rc = skapande.main(['belagg', s, '--rad', '3', '--belagg', 'x'])
        assert rc == 2, 'kommandot gav en vidarebefordrad rad ett belägg'
        with contextlib.redirect_stdout(ut):
            skapande.main(['visa', s])
        assert skapande.BELAGGFIL in ut.getvalue() and '2 rad(er) går inte att läsa' in ut.getvalue(), ut.getvalue()[-400:]
    finally:
        skapande.UNDERLAG = spara_u
    assert skapande.domar(s, U)[0]['belagg'].endswith('(provet, igen)'), 'den sista bilageraden för en sha gäller'
    with open(u / skapande.BELAGGFIL, 'ab') as fh:  # ett intyg från någon annan än ägaren gäller aldrig, också med radens sha
        fh.write((json.dumps({'tid': '2026-10-07T13:00:00Z', 'kalla': 'Codex', 'sha256': post_b['sha256'], 'belagg': 'Codex intygar'}, ensure_ascii=False) + '\n').encode('utf-8'))
    lg = skapande.domar(s, U)
    assert lg[0]['belagg'].endswith('(provet, igen)') and [x['rad'] for x in skapande.bilagor(s, U)['olasbara']] == [2, 3, 5], ('ett intyg från Codex gällde', lg[0].get('belagg'))
    # ett belägg av blanktecken godtas aldrig, varken i loggen eller i doma (KAN-10, G22)
    for f_ in (lambda: skapande.lagg_till_dom(s, 'ägaren via Codex', 'putsa', 'Putsa.', underlag=U, belagg='   '),
               lambda: atelje.doma(s, 'ägaren via Codex', 'putsa', 'Putsa.', belagg='  ')):
        try:
            f_()
            raise AssertionError('ett belägg av blanktecken godtogs')
        except ValueError:
            pass
    assert len(skapande.domar(s, U)) == 3, 'en dom utan giltigt belägg skrevs'
    logg(s, dom('2026-10-07T14:00:00Z', 'ägaren via Codex', 'putsa', 'EN ANNAN OBELAGD RAD.'))
    assert not skapande.ar_agarens(skapande.domar(s, U)[-1]), 'en annan domrad fick det första belägget'
    assert skapande.senaste(s, underlag=U)['tid'] == '2026-10-05T11:00:00Z', 'belägget ändrade en annan doms status'


@fall('domloggen läses på radslut: en dom med U+2028, U+2029 eller U+0085 i texten räknas, och radnumren och hasharna stämmer med filen')
def _radslut():
    s = 'prov-radslut'
    u, _k = kund(s)
    rot = u / 'atelje'
    skriv(rot / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'klar': '2026-10-06T10:00:00Z', 'steg': 'klar', 'lage': 'ny'})
    tecken = {'U+2028': ' ', 'U+2029': ' ', 'U+0085': '\x85'}
    for i, (namn, c) in enumerate(tecken.items()):
        skapande.lagg_till_dom(s, 'ägaren', 'putsa', 'Rubriken%sär för stor (%s).' % (c, namn), underlag=U, tid='2026-10-06T1%d:00:00Z' % (1 + i))
    sv_ = SV.agarens_senare_dom(RT, s, '2026-10-06T10:00:00Z')  # stoppvakten: ägarens senaste dom efter körningen
    assert (sv_ or {}).get('text') == 'Rubriken\x85är för stor (U+0085).', ('stoppvakten såg inte domen', sv_)
    plan = '2026-10-06T08:00:00Z'
    skapande.lagg_till_dom(s, 'ägaren', 'valj', 'Välj k01.', underlag=U, tid='2026-10-06T15:00:00Z', kandidater=[{'id': 'k01', 'version': 'v' * 64, 'plan': plan}], plan=plan)
    data = (u / skapande.DOMLOGG).read_bytes()
    assert data.count(' '.encode()) == 1 and data.count(b'\n') == 4, 'fixturen: tecknen står oskyddade i raden, som dashboarden skriver dem'
    texter = [d['text'] for d in skapande.domar(s, U)]
    assert len(texter) == 4 and all(c in ''.join(texter) for c in tecken.values()), texter
    assert skapande.senaste(s, underlag=U)['beslut'] == 'valj'
    # radnumren och hasharna är filens egna rader: också omtagets urval (r100) pekar på rätt rad
    filrader = data.split(b'\n')
    rader = atelje.domrader(s)
    assert [r[0] for r in rader] == [1, 2, 3, 4] and all(r[1] == hashlib.sha256(filrader[r[0] - 1]).hexdigest() for r in rader), [r[:2] for r in rader]
    valda = atelje.bedomda(s, {'tid': plan}, {'k01': {}}, {'k01': {'version': 'v' * 64}}, lambda k_, s_: False, None, False)
    assert [r[0] for r in valda[('k01', 'v' * 64)]] == [4], valda
    # prototypen ser ägarens senaste dom (putsa efter körningen var den senaste före valet)
    skapande.lagg_till_dom(s, 'ägaren', 'putsa', 'Sista raden.', underlag=U, tid='2026-10-06T16:00:00Z')
    assert prototyp.lage(s)[0] == 'putsa', prototyp.lage(s)


@fall('en trasig rad i domloggen syns som oläsbar med plats och skäl, stoppar läget och godkännandet efter sig, och en ny dom efter en avbruten rad hamnar på en egen rad')
def _trasig_rad():
    s = 'prov-trasig'
    u, k = kund(s)
    rot = u / 'atelje'
    kod = skriv(rot / 'vinnare' / 'kod' / 'index.astro', '<h1>Godkänd</h1>')
    skriv(rot / 'STATUS.json', {'slug': s, 'startad': '2026-10-06T09:00:00Z', 'klar': '2026-10-06T10:00:00Z', 'steg': 'klar', 'lage': 'ny'})
    skriv(rot / 'VINNARE.json', {'riktning': 1, 'godkand': {'tid': '2026-10-06T11:00:00Z', 'av': 'ägaren', 'text': 'Godkänd.', 'sha_index': sha(kod)}})
    f = logg(s, dom('2026-10-06T11:00:00Z', 'ägaren', 'godkand', 'Godkänd.'))
    assert skapande.godkand_giltig(s, U, K)[0] and prototyp.lage(s)[0] == 'godkand'
    # en dom som skrevs till hälften (en skrivning som avbröts): ingen radslut sist
    with open(f, 'ab') as fh:
        fh.write(domrad(dom('2026-10-06T12:00:00Z', 'ägaren', 'ny_riktning', 'Avbruten mitt i'))[:60])
    ok, skal = skapande.godkand_giltig(s, U, K)
    assert not ok and 'rad 2' in skal and 'går inte att läsa' in skal, ('ett godkännande gäller förbi en oläsbar senare rad', skal)
    vald, skal = prototyp.lage(s)
    assert vald == 'stopp' and 'rad 2' in skal, (vald, skal)
    assert 'Vägen vidare: ett nytt beslut från ägaren efter raden' in skal and 'välj läget uttryckligen' in skal, ('vägen vidare står inte i lägets text', skal)
    assert 'Vägen vidare är ett nytt beslut från ägaren efter raden' in skal and 'som gäller från sin rad' in skal, ('vägen vidare står inte i domloggens text', skal)
    lg = skapande.domlogg(s, U)
    assert [x['rad'] for x in lg['olasbara']] == [2] and lg['olasbara'][0]['skal'].startswith('inte JSON'), lg['olasbara']
    assert 'rad 2' in skapande.olasbara_text(lg) and '1 rad går inte att läsa' in skapande.olasbara_text(lg), skapande.olasbara_text(lg)
    assert SV.agarens_senare_dom(RT, s, '2026-10-06T10:00:00Z') == {'oklar': skapande.oklara_text(skapande.agarens_senaste(s, U))}
    assert 'rad 2' in (SV.ateljen_forkastad(RT, s) or ''), 'stoppvakten låter inte bygget fortsätta förbi en oläsbar rad'
    # en ny dom efter den avbrutna raden hamnar på en egen rad och räknas
    skapande.lagg_till_dom(s, 'ägaren', 'putsa', 'Efter den avbrutna.', underlag=U, tid='2026-10-06T13:00:00Z')
    lg = skapande.domlogg(s, U)
    assert [p['text'] for _r, _s, p in lg['domar']] == ['Godkänd.', 'Efter den avbrutna.'] and [r for r, _s, _p in lg['domar']] == [1, 3], lg['domar']
    assert [x['rad'] for x in lg['olasbara']] == [2], 'den avbrutna raden står kvar som oläsbar, inget skrivs om'
    assert prototyp.lage(s)[0] == 'putsa' and not skapande.godkand_giltig(s, U, K)[0]
    # i ateljéns slutpost står den oläsbara raden som en brist
    import ateljeslut
    post = ateljeslut.bygg(s, dict(json.loads((rot / 'STATUS.json').read_text()), kandidatflode=False), '20261006T090000Z')
    assert any('rad 2' in b and 'går inte att läsa' in b for b in post['brister']), post['brister']
    # ett val före en trasig rad: läget stannar av egen kraft (inte bara genom godkännandet); en JSON-rad som inte är en dom
    # är också oläsbar; och vägen vidare är ett nytt beslut från ägaren efter raderna, som gäller från sin rad (KAN-2)
    s2 = 'prov-trasig-valj'
    u2, _k2 = kund(s2)
    skriv(u2 / 'atelje' / 'STATUS.json', {'slug': s2, 'startad': '2026-10-06T09:00:00Z', 'klar': '2026-10-06T10:00:00Z', 'steg': 'klar_for_bedomning', 'lage': 'ny', 'kandidatflode': True})
    val = dict(kandidater=[{'id': 'k01', 'version': 'v' * 64}])
    logg(s2, dom('2026-10-06T11:00:00Z', 'ägaren', 'valj', 'Välj k01.', **val))
    assert prototyp.lage(s2)[0] == 'valda', prototyp.lage(s2)
    logg(s2, b'{"tid": "2026-10-06T12:00:00Z", "kalla": "\xc3\xa4garen"}\n', b'trasig\n')
    vald, skal = prototyp.lage(s2)
    assert vald == 'stopp' and 'raderna 2, 3' in skal and 'nytt beslut' in skal, ('ett val före en trasig rad gav läget', vald, skal)
    lg = skapande.domlogg(s2, U)
    assert [x['rad'] for x in lg['olasbara']] == [2, 3] and 'ingen dom' in lg['olasbara'][0]['skal'] and lg['olasbara'][1]['skal'].startswith('inte JSON'), lg['olasbara']
    skapande.lagg_till_dom(s2, 'ägaren', 'valj', 'Välj k01, igen.', underlag=U, tid='2026-10-06T13:00:00Z', **val)
    assert prototyp.lage(s2)[0] == 'valda' and [x['rad'] for x in skapande.domlogg(s2, U)['olasbara']] == [2, 3], ('vägen vidare', prototyp.lage(s2))


@fall('de andra JSONL-filerna läses också på radslut: tjänstesessionens logg, underhållets ändringar och provets historik')
def _andra_jsonl():
    import autonomi
    import referenstjanster
    import verktygslada
    logg_ = TMP / 'jsonl' / 'session-prov.jsonl'
    rader = [{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't1', 'name': 'mcp__refero__refero_search_styles', 'input': {'q': 'x'}}]}},
             {'type': 'user', 'message': {'content': [{'type': 'tool_result', 'tool_use_id': 't1', 'content': [{'type': 'text', 'text': 'Stil\u2028med radbrytning'}]}]}},
             {'type': 'result', 'subtype': 'success', 'num_turns': 2, 'duration_ms': 10}]
    skriv(logg_, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rader))
    svar = []
    anrop, _res, slut = referenstjanster.las_logg(logg_, svar)
    assert anrop == {'mcp__refero__refero_search_styles': 1} and svar and svar[0][2] == 'Stil\u2028med radbrytning' and slut.get('subtype') == 'success', (anrop, svar, slut)
    skriv(TMP / 'jsonl' / 'ANDRINGAR.jsonl', json.dumps({'tid': '2026-10-07T10:00:00Z', 'vad': 'paket\u2029x'}, ensure_ascii=False) + '\n')
    assert [x['vad'] for x in verktygslada.andringar(TMP / 'jsonl')] == ['paket\u2029x']
    skriv(TMP / 'jsonl' / 'bygg' / 'prov' / 'historik.jsonl', ''.join(json.dumps({'ok': i == 1, 'grindar': {'axe': i == 1}, 'not': 'a\x85b'}, ensure_ascii=False) + '\n' for i in range(2)))
    p_ = autonomi.provet(TMP / 'jsonl' / 'bygg')
    assert p_['korningar'] == 2 and p_['forsta_hela_grona'] == 2, p_
    # korsluts läsning av byggets logg gick redan på radslut (en textfil läst rad för rad delar inte på U+2028): oförändrad
    k_ = TMP / 'jsonl' / 'kunder' / 'prov-bygge'
    skriv(k_ / 'korning-20261007T100000Z.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in (
        {'type': 'system', 'subtype': 'init', 'model': 'prov', 'claude_code_version': '0'},
        {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'rad rad'}]}},
        {'type': 'result', 'subtype': 'success', 'num_turns': 3, 'duration_ms': 60000, 'result': 'klart '})))
    se_ = korslut.sessionen(k_, '20261007T100000Z', '0')
    assert se_['resultat'] == 'success' and se_['turer'] == 3 and se_['modell'] == 'prov', se_
    # städningens förteckning (underlag/granskningar/FORTECKNING.jsonl): en registrering med U+2028 i ett fält gäller (G32)
    import stadning
    repo_ = TMP / 'jsonl' / 'repo'
    bevis = skriv(repo_ / 'underlag' / 'granskningar' / 'GR-prov' / 'bevis.txt', 'bevis')
    s_ = sha(bevis)
    skriv(repo_ / 'underlag' / 'granskningar' / 'FORTECKNING.jsonl',
          json.dumps({'sha256': s_, 'fil': 'granskningar/GR-prov/bevis.txt', 'bas': 'underlag/', 'not': 'rad\u2028bruten'}, ensure_ascii=False) + '\n')
    assert stadning.Kvitton(repo_).var(s_) == 'underlag/granskningar/GR-prov/bevis.txt', stadning.Kvitton(repo_).var(s_)
    # A/B-loggen (kunder/<slug>/korning-*.jsonl): slutraden med U+2028 i resultatet räknas (G33)
    import ab
    spara_k = ab.KUNDER
    ab.KUNDER = TMP / 'jsonl' / 'kunder'
    try:
        skriv(ab.KUNDER / 'prov-ab' / 'korning-20261007T100000Z.jsonl', ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in (
            {'type': 'system', 'subtype': 'init', 'model': 'prov', 'claude_code_version': '0'},
            {'type': 'result', 'subtype': 'success', 'num_turns': 7, 'duration_ms': 60000, 'result': 'klart\u2028'})))
        m_ = ab.matt('prov-ab')
        assert m_.get('turer') == 7 and m_.get('modell') == 'prov', m_
    finally:
        ab.KUNDER = spara_k


# Oberoende granskning av C1: signaler vid start/avslut och slutpostens bevis.
OBEROENDE_PROV = r'''import json, os, signal, subprocess, sys, threading, uuid
from pathlib import Path
def child(mode, repo):
    sys.path.insert(0, str(repo / 'kontroller'))
    import atelje
    import ateljeslut
    import kandidater
    import observation
    import skapande

    slug = 'prov-oberoende-' + mode
    rot = repo / 'underlag' / slug / 'atelje'
    rot.mkdir(parents=True)
    (repo / 'kunder' / slug).mkdir(parents=True)
    atelje.skriv_status(rot, {'steg': 'startar', 'startad': atelje.nu(), 'slug': slug})

    if mode == 'json-temp':
        resultat = []
        for n, namn in enumerate(('STATUS.json', 'SLUT.json'), 1):
            stamp = '20261007T01000%dZ' % n
            d = ateljeslut.postkatalog(slug, stamp)
            mal = repo / ('orord-%d.txt' % n)
            mal.write_text('ORÖRD\n')
            temp = d / ('.%s.tmp%d' % (namn, os.getpid()))
            temp.symlink_to(mal)
            post = {'id': 'syntetisk-%d' % n, 'datum': '2026-10-07T01:00:00Z', 'underlag': []}
            ateljeslut.skriv(slug, stamp, post, ersatt=False, status={'steg': 'fel'})
            resultat.append({'fil': namn, 'mal_orort': mal.read_text() == 'ORÖRD\n',
                             'slutfil_ar_lank': (d / namn).is_symlink(),
                             'post_upptackt': any(f.parent == d for f in ateljeslut.slutposter(slug))})
        return {'mode': mode, 'resultat': resultat}

    if mode == 'godkand-trasig':
        status = {'slug': slug, 'startad': '2026-10-07T01:00:00Z', 'steg': 'klar_for_bedomning',
                  'lage': 'ny', 'kandidatflode': True, 'kandidater': {}}
        atelje.skriv_status(rot, status)
        skapande.lagg_till_dom(slug, 'ägaren', 'godkand', 'Syntetiskt godkännande.',
                              tid='2026-10-07T02:00:00Z')
        f = repo / 'underlag' / slug / skapande.DOMLOGG
        with f.open('ab') as fh:
            fh.write(b'{"tid":"2026-10-07T03:00:00Z",')
        beslut = skapande.agarens_senaste(slug)
        post = ateljeslut.bygg(slug, status, '20261007T010000Z')
        import prototyp
        return {'mode': mode, 'lage': prototyp.lage(slug)[0],
                'oklara_rader': [x['rad'] for x in beslut['oklara']],
                'agaren_godkanner': post['tillstand']['agaren_godkanner']['varde'],
                'posttext': post['tillstand']['agaren_godkanner']['text'],
                'brist_olasbar_finns': any('går inte att läsa' in str(x) for x in post['brister'])}

    # Endast mekaniken körs: inga externa tjänster, inga verkliga underlag.
    atelje.aterkalla = lambda *args: None
    atelje.arkivera_vid_ny_start = lambda *args, **kwargs: None
    atelje.egna_bilder = lambda *args: []
    kandidater.redovisa = lambda *args: None

    if mode in ('popen-huvud', 'stopp-registrering'):
        if mode == 'stopp-registrering':
            class SignalSet(set):
                def discard(self, pid):
                    signal.raise_signal(signal.SIGTERM)
                    super().discard(pid)
            atelje.AKTIVA = SignalSet()
        fake = repo.parent / 'bin' / 'claude'
        fake.parent.mkdir(parents=True, exist_ok=True)
        fake.write_text('#!' + sys.executable + '\nimport time\ntime.sleep(120)\n')
        fake.chmod(0o755)
        sid = str(uuid.uuid4())
        atelje.session_args = lambda *args, **kwargs: [str(fake), '-p']
        atelje.observerad = lambda *args, **kwargs: (sid, slug)
        riktig_popen, processer = subprocess.Popen, []

        def med_signal(args, **kwargs):
            p = riktig_popen(args, **kwargs)
            if args[0] == str(fake):
                processer.append(p)
                if mode == 'popen-huvud':
                    signal.raise_signal(signal.SIGTERM)  # efter barnstart, före Popen-return i huvudtråden
                else:
                    p.terminate()
                    p.wait(timeout=5)
            return p

        def kor(_slug, status, skriv):
            status.update(steg='skapa', kandidater={})
            skriv()
            atelje.session('syntetiskt prov', [], rot / 'svar-prov.json', slug=slug)

        kandidater.kor = kor
        subprocess.Popen = med_signal
        try:
            atelje.arbeta(slug, 'ny')
            st = atelje.las_json(rot / 'STATUS.json')
            _, post = ateljeslut.post_for(slug, st)
            sess = atelje.las_json(observation.katalog(slug) / (sid + '.json')) or {}
            return {'mode': mode, 'post_slutkod': post['slutkod'],
                    'session_lever': any(p.poll() is None for p in processer),
                    'session_slut': sess.get('slut'), 'session_utfall': sess.get('utfall')}
        finally:
            subprocess.Popen = riktig_popen
            for p in processer:
                if p.poll() is None:
                    p.kill()
                p.wait(timeout=10)

    if mode == 'popen-stopp':
        fake = repo.parent / 'bin' / 'claude'
        fake.parent.mkdir(parents=True, exist_ok=True)
        fake.write_text('#!' + sys.executable + '\nimport time\ntime.sleep(120)\n')
        fake.chmod(0o755)
        sid = str(uuid.uuid4())
        atelje.session_args = lambda *args, **kwargs: [str(fake), '-p']
        atelje.observerad = lambda *args, **kwargs: (sid, slug)
        skapad, slapp, registrerad = threading.Event(), threading.Event(), threading.Event()
        processer, fel, tradar = [], [], []
        riktig_popen = subprocess.Popen

        def med_barriar(args, **kwargs):
            p = riktig_popen(args, **kwargs)
            if args[0] == str(fake):
                processer.append(p)
                skapad.set()
                if not slapp.wait(10):
                    p.kill()
                    p.wait()
                    raise RuntimeError('provbarriären fick inget svar')
            return p

        def session():
            try:
                atelje.session('syntetiskt prov', [], rot / 'svar-prov.json', slug=slug,
                               vid_start=lambda pid: registrerad.set())
            except BaseException as e:
                fel.append(type(e).__name__)

        def kor(_slug, status, skriv):
            status.update(steg='skapa', kandidater={})
            skriv()
            t = threading.Thread(target=session, daemon=True)
            tradar.append(t)
            t.start()
            assert skapad.wait(10), 'attrappen skapades inte'
            assert not atelje.AKTIVA, 'barriären ligger inte före AKTIVA.add'
            # Python levererar signalen i huvudtråden medan barnprocessen redan finns.
            def slapp_fran_annan_trad():
                assert atelje.STOPP.wait(10)
                slapp.set()
            frislappare = threading.Thread(target=slapp_fran_annan_trad)
            tradar.append(frislappare)
            frislappare.start()
            signal.raise_signal(signal.SIGTERM)

        def redovisa(*args):
            # Precis som en scheduler kan låta Popen återvända först under avslutet.
            slapp.set()
            assert registrerad.wait(10), 'sessionen registrerades inte efter stoppet'

        kandidater.kor = kor
        kandidater.redovisa = redovisa
        subprocess.Popen = med_barriar
        try:
            rc = atelje.arbeta(slug, 'ny')
            st = atelje.las_json(rot / 'STATUS.json')
            _, post = ateljeslut.post_for(slug, st)
            sess = atelje.las_json(observation.katalog(slug) / (sid + '.json'))
            return {'mode': mode, 'arbeta_rc': rc, 'steg': st.get('steg'),
                    'post_slag': post['utfall']['slag'], 'post_slutkod': post['slutkod'],
                    'session_lever_efter_slutpost': any(p.poll() is None for p in processer),
                    'stoppsignal_fangade_session': any(p.pid in atelje.STOPPAD.get('pids', set()) for p in processer),
                    'session_slut': sess.get('slut'), 'session_utfall': sess.get('utfall')}
        finally:
            slapp.set()
            subprocess.Popen = riktig_popen
            for p in processer:
                if p.poll() is None:
                    p.kill()
                p.wait(timeout=10)
            for t in tradar:
                t.join(timeout=5)

    if mode in ('stopp-redovisa', 'stopp-stada', 'stopp-slutpost'):
        def kor(_slug, status, skriv):
            kandidater.satt_status(slug, 'k01', 'klar', 'syntetiskt färdig kandidat',
                                  version='a' * 64, varv=1)
            status.update(steg='klar_for_bedomning', kandidater={'k01': 'klar'})
            skriv()

        def signalera(*args):
            signal.raise_signal(signal.SIGTERM)

        kandidater.kor = kor
        if mode == 'stopp-redovisa':
            kandidater.redovisa = signalera
        elif mode == 'stopp-stada':
            atelje.stada = signalera
        else:
            original_slutpost = atelje.slutpost
            signalerad = False
            def slutpost_med_signal(*args, **kwargs):
                nonlocal signalerad
                if not signalerad:
                    signalerad = True
                    signalera()
                return original_slutpost(*args, **kwargs)
            atelje.slutpost = slutpost_med_signal
        undantag = None
        try:
            atelje.arbeta(slug, 'ny')
        except BaseException as e:
            undantag = type(e).__name__
        st = atelje.las_json(rot / 'STATUS.json')
        _, post = ateljeslut.post_for(slug, st)
        return {'mode': mode, 'undantag': undantag, 'steg': st.get('steg'),
                'status_har_pid': bool(st.get('pid')), 'status_avbrott': st.get('avbrott'),
                'redovisning_fel': st.get('redovisning_fel'), 'post_skriven': post is not None,
                'post_slag': post['utfall']['slag'] if post else None,
                'post_slutkod': post['slutkod'] if post else None,
                'sessionen_avslutad': post['tillstand']['sessionen_avslutad']['varde'] if post else None}
    raise ValueError(mode)
print(json.dumps(child(sys.argv[1], Path(sys.argv[2])), ensure_ascii=False))
'''

@fall('slutpostens JSON-tempfiler följer inga länkar; stopp vid start och avslut; trasig domlogg ger inget ja')
def _oberoende_granskning():
    ar = ateljerepo()
    fil = skriv(TMP / 'oberoende-prov.py', OBEROENDE_PROV)
    resultat = {}
    for mode in ('json-temp', 'popen-stopp', 'popen-huvud', 'stopp-registrering', 'stopp-redovisa', 'stopp-stada', 'stopp-slutpost', 'godkand-trasig'):
        try:
            p = subprocess.run([PY, '-B', str(fil), mode, str(ar)], cwd=ar, env=startmiljo(),
                               capture_output=True, text=True, timeout=40)
        finally:
            # Även en mutation som låser huvudtråden städar provets egen sovande attrapp.
            doda(processer_med(str(ar.parent / 'bin' / 'claude')))
        assert p.returncode == 0, (mode, p.stderr[-1600:], p.stdout[-800:])
        resultat[mode] = json.loads(p.stdout.strip().split('\n')[-1])
    fel = []
    for r in resultat['json-temp']['resultat']:
        if not (r['mal_orort'] and not r['slutfil_ar_lank'] and r['post_upptackt']):
            fel.append(('JSON-temp', r))
    r = resultat['popen-stopp']
    if r['session_lever_efter_slutpost'] or not r['stoppsignal_fangade_session'] or not r['session_slut'] or not r['session_utfall']:
        fel.append(('start/stopp', r))
    for mode in ('popen-huvud', 'stopp-registrering'):
        r = resultat[mode]
        if r['session_lever'] or r['post_slutkod'] != 4 or not r['session_slut'] or not r['session_utfall']:
            fel.append((mode, r))
    for mode in ('stopp-redovisa', 'stopp-stada', 'stopp-slutpost'):
        r = resultat[mode]
        if r['undantag'] or r['status_har_pid'] or not r['post_skriven'] or r['post_slutkod'] != 4 or r['sessionen_avslutad']:
            fel.append((mode, r))
    r = resultat['godkand-trasig']
    if r['agaren_godkanner'] is not None:
        fel.append(('trasig domlogg', r))
    assert not fel, fel


print('ateljéns slutpost: %d fel' % len(FEL), file=sys.stderr)
sys.exit(1 if FEL else 0)
