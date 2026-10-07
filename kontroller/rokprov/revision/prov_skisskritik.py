#!/usr/bin/env python3
"""prov_skisskritik.py — skisskritikens kompetens och sessionerna som bedömer eller forskar (ägarens ord 2026-10-07: "Du
behöver ju fixa luckan där med de verktyg vi har tillgängliga"; BESLUT.md, tillägget 2026-10-07), i en isolerad kopia av
repot med falska byggen, webbläsare, motorer och sessioner:

1. kritikens block: passet skisskritik har en roll med kärna, alternativ, förhandsvisning, detektor och Refero och
   Mobbin; sessionen får blockets verktyg och tjänsterna genom kundvakten, och prompten bär blockets uppgift i stället
   för egna kriterier;
2. kritikens förhandsvisning skriver i kritikens egen katalog (granskare/), tar 390, 768, 1280 och 1440 med menyn,
   tangentbordet och reflow, och skaparens varv, varvräkning och anrop är orörda;
3. blindningen: skaparens text, uppdrag, referenspaket och kod nekas, också transkripten och spåren, och verktygen ger
   ingen kod (byggloggen, fotograferingens logg, detektorns utdrag och spårfilerna); ett kodgivande verktyg i ett blint
   pass fälls av kompetens.prova;
4. kompetenskvittot räknar kärnan, de valda alternativen, verktygsanropen och tjänsternas anrop med utfall, och
   SKISSKRITIK.json bär kvittot, kandidatens version och bilderna kritiken bedömde;
5. tiden: fristen och reserven bygger på mätningen, och skissförsöket lämnar kritiken just den fristen;
6. de andra sessionerna (research, jämförelsen och granskningens två pass i läget full) får sina block, verktyg,
   tjänster och kvitton, och metodkartans lista över sessioner utan block stämmer med koden;
7. en tom eller saknad 768-bild leder aldrig till att kritiken tros ha bedömt mellanbredden;
8. metodlåset: metod.py och kompetens.py prövar kartan, och en ändrad källa stoppar leveransen.

    .venv/bin/python kontroller/rokprov/revision/prov_skisskritik.py <repo>

Fallen var röda mot 63c09c5 (gren B:s topp, där skisskritiken bara hade läsverktygen). Varje fall redovisas för sig på
stderr; slutkod 1 när något fall föll. Ingenting skrivs i repots underlag/ eller kunder/, och inga privata data läses: den
syntetiska kunden finns bara i provets kopia.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT_REAL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-skisskritik-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):  # också när provet faller: annars fyller kvarlämnade kopior disken
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
KOPIA = TMP / 'repo'
FEL = []


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:900]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


# --- den isolerade kopian ---
utom = shutil.ignore_patterns('node_modules', '.git', 'underlag', 'kunder', 'dist', '.astro', '__pycache__', '.venv')
for d_ in ('kontroller', 'kunskap', 'kritik', 'mall', '.claude'):
    shutil.copytree(ROOT_REAL / d_, KOPIA / d_, ignore=utom, symlinks=True)
for f_ in ('README.md', 'BESLUT.md', 'CLAUDE.md', 'LARDOMAR.md', 'kor.sh', 'requirements.txt', 'requirements-lock.txt', '.gitignore'):
    if (ROOT_REAL / f_).exists():
        shutil.copy2(ROOT_REAL / f_, KOPIA / f_)
os.symlink(os.path.realpath(ROOT_REAL / '.venv'), KOPIA / '.venv')
os.symlink(os.path.realpath(ROOT_REAL / 'kontroller' / 'node_modules'), KOPIA / 'kontroller' / 'node_modules')
for k_ in ('NWP_SLUG', 'NWP_SKISSKRITIK', 'NWP_KANDIDAT_FRIST_SKISSKRITIK', 'NWP_KANDIDAT_SKISSKRITIK_RESERV', 'NWP_KANDIDAT_FRIST_SKISS',
           'NWP_KANDIDATLAGE', 'IMPECCABLE_BIN'):
    os.environ.pop(k_, None)
os.environ['NWP_STADNING'] = 'av'
os.environ['NWP_OBSERVATION'] = 'av'  # sessionerna här är falska: observatören ska inte fråga claude --help

sys.path.insert(0, str(KOPIA / 'kontroller'))
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import forhandsvisa  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import metod  # noqa: E402
import prova  # noqa: E402
assert atelje.ROOT == KOPIA and forhandsvisa.ROOT == KOPIA and bildkedja.ROOT == KOPIA, (atelje.ROOT, forhandsvisa.ROOT)
bildkedja.PROJEKT = TMP / 'projekt'  # sessionernas transkript: provets egna, aldrig ägarens

SLUG = 'kv-prov'
KODMARKOR = 'KODMARKOR-hemlig-klass'
SKAPARMARKOR = 'SKAPARENS-HEMLIGA-MOTIVERING'
UPPDRAGSMARKOR = 'UPPDRAGETS-HEMLIGA-FORM'


def png(bredd=390, hojd=844):
    """En liten men hel PNG (signatur, IHDR, IDAT, IEND) med de angivna måtten i huvudet."""
    import struct
    import zlib

    def chunk(typ, data):
        return struct.pack('>I', len(data)) + typ + data + struct.pack('>I', zlib.crc32(typ + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', bredd, hojd, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\x00' * 8)) + chunk(b'IEND', b''))


def skriv(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(text, bytes) else p.write_text)(text)
    return p


def kund(slug=SLUG):
    """En syntetisk kund med plan, två kandidater, skaparens text, uppdrag, referenspaket, kod och ett helt varv."""
    u, k = atelje.UNDERLAG / slug, atelje.KUNDER / slug
    shutil.rmtree(u, ignore_errors=True)  # varje fall börjar med en ny kund i provets kopia
    shutil.rmtree(k, ignore_errors=True)
    skriv(u / 'VERKSAMHET.json', json.dumps({'namn': 'Provfirman Trä AB', 'adress': {'ort': 'Exempelby'},
                                             'kontaktvagar': [{'typ': 'telefon', 'varde': '000-111 22 33'}]}))
    skriv(u / 'BRIEF.md', '# Brief\n\n## §2 Målgrupper och toppuppgifter\n\n1. Se liknande jobb före kontakt\n')
    skriv(u / 'REFERENSER.md', '# Referenser\n\nReferensbeslutet %s\n' % UPPDRAGSMARKOR)
    skriv(u / 'referenser' / 'paket-v01' / 'xref' / 'vy-390-forsta.png', png())
    skriv(u / 'referenser' / 'tjanster' / 'TJANSTER.md', '# tjänsterna %s\n' % UPPDRAGSMARKOR)
    skriv(u / 'DESIGNDOMAR.jsonl', json.dumps({'tid': '2026-10-02T10:00:00Z', 'kalla': 'ägaren', 'beslut': 'ny_riktning', 'text': 'pröva nya grundidéer'}) + '\n')
    r = kd.rot(slug)
    skriv(r / 'KANDIDATPLAN.json', json.dumps({'lage': 'skiss', 'tid': '2026-10-07T08:00:00Z', 'kandidater': {
        'k01': {'uppgift': 'Besökaren vill se ett liknande jobb och ringa.', 'titel': UPPDRAGSMARKOR},
        'k02': {'uppgift': 'Besökaren vill skriva en förfrågan.'}}}))
    skriv(r / 'FORSKNING.md', '# Research %s\n' % UPPDRAGSMARKOR)
    skriv(r / 'metod' / 'METOD-skiss.md', '# Metoden\n')
    for kid in ('k01', 'k02'):
        d = kd.kdir(slug, kid)
        skriv(d / 'UPPDRAG.md', '# Uppdrag %s\n' % UPPDRAGSMARKOR)
        skriv(d / 'RIKTNING.md', 'Huvudreferens: Xref — kompositionen\n\n## Idén\n\n%s\n' % SKAPARMARKOR)
        skriv(d / 'STATUS.json', json.dumps({'id': kid, 'status': 'under_arbete', 'titel': UPPDRAGSMARKOR}))
        skriv(d / 'kod' / 'index.astro', '<h1 class="%s">Skiss</h1>\n' % KODMARKOR)
        skriv(d / 'kod-src' / 'styles' / 'sida.css', '.%s { color: red }\n' % KODMARKOR)
        skriv(d / 'DESIGN.md', '# Design %s\n' % KODMARKOR)
        skriv(d / 'versioner' / 'abc123' / 'kod' / 'index.astro', KODMARKOR)
        skriv(d / 'svar-skiss-1.json', json.dumps({'result': SKAPARMARKOR}))
        vd = d / 'varv' / 'start' / 'varv-01'
        for b_ in ('390', '1440'):  # skaparens förhandsvisning utan --mellan: 390 och 1440
            for s_ in ('forsta', 'hela'):
                skriv(vd / ('vy-%s-%s.png' % (b_, s_)), png(int(b_)))
        skriv(vd / 'vy-390-spar.zip', b'PK\x03\x04' + KODMARKOR.encode())
        skriv(vd / 'FORHAND.md', '# Förhandsvisning varv-01\n')
        sajt = kd.ksajt(slug, kid)
        skriv(sajt / 'package.json', '{}')
        skriv(sajt / 'src' / 'pages' / 'index.astro', '<header><button aria-expanded="false">Meny</button></header>\n<h1 class="%s">Skiss</h1>\n' % KODMARKOR)
        skriv(sajt / 'src' / 'pages' / '404.astro', '404')
        skriv(sajt / 'src' / 'styles' / 'sida.css', '.%s { color: red }\n' % KODMARKOR)
        skriv(sajt / 'DESIGN.md', '# Design %s\n' % KODMARKOR)
    return u


# --- falska byggen och en falsk webbläsare: förhandsvisningen och fotograferingen körs på riktigt runt dem ---
INSPEKTERAT, BYGG = [], {'rc': 0, 'logg': 'byggt'}


def bygg_falsk(sajt, timeout=900):
    if BYGG['rc']:
        return BYGG['rc'], BYGG['logg']
    pages, dist = Path(sajt) / 'src' / 'pages', Path(sajt) / 'dist'
    for p_ in pages.rglob('index.astro'):
        skriv(dist / p_.relative_to(pages).parent / 'index.html', p_.read_text())
    return 0, 'byggt'


def kor_falsk(cmd, cwd=None, timeout=900):
    cmd = [str(x) for x in cmd]
    if any(x.endswith('inspektera.mjs') for x in cmd):
        INSPEKTERAT.append(cmd)
        ut_ = Path(cmd[cmd.index('--ut') + 1])
        ut_.mkdir(parents=True, exist_ok=True)
        vyer = cmd[cmd.index('--vyer') + 1].split(',')
        tillst = cmd[cmd.index('--tillstand') + 1].split(',')
        rapport = {'vyer': {}}
        for vy in vyer:
            if vy == BILD.get('tom'):
                skriv(ut_ / ('vy-%s-forsta.png' % vy), b'')  # en tom bild: fotograferingen gav ingenting
            elif vy != BILD.get('saknas'):
                for s_ in ('forsta', 'hela'):
                    skriv(ut_ / ('vy-%s-%s.png' % (vy, s_)), png(int(vy)))
            skriv(ut_ / ('vy-%s-spar.zip' % vy), b'PK\x03\x04' + KODMARKOR.encode())
            t_ = {}
            if '--meny' in cmd:
                bild_ = ut_ / ('vy-%s-meny.png' % vy)
                if vy in ('390', '768'):
                    skriv(bild_, png(int(vy)))
                    t_['meny'] = {'klickad': True, 'expanded': 'true', 'bild': str(bild_)}
                else:
                    t_['meny'] = {'knapp': False, 'klickad': False, 'expanded': None, 'skal': 'ingen synlig menyknapp'}
            if 'tangentbord' in tillst:
                t_['tangentbord'] = [{'synligFokus': True}] * 6
                t_['tangentbord_utan_synlig_fokus'] = 0
            if 'reflow' in tillst:
                skriv(ut_ / ('vy-%s-reflow320.png' % vy), png(320))
                t_['reflow_320'] = {'spill': False}
            rapport['vyer'][vy] = {'konsol': [], 'sidfel': [], 'spill': {'spill': False}, 'tillstand': t_}
        skriv(ut_ / 'INSPEKTION.json', json.dumps(rapport))
        skriv(ut_ / 'EXTRAKT.md', '# Extrakt\n')
        if BILD.get('logg'):
            return 1, BILD['logg']
        return 0, ''
    if any(x.endswith('axe.mjs') for x in cmd):
        ut_ = Path(next(x for x in cmd if x.startswith('--ut='))[5:])
        skriv(ut_ / 'axe.json', json.dumps({'allvarliga': 0, 'totalt': 0, 'axeVersion': 'x', 'rader': []}))
        return 0, ''
    raise AssertionError('oväntat kommando i provet: %s' % cmd[:3])


class ServerFalsk:
    def __init__(self, *a, **k):
        self.url = 'http://127.0.0.1:9'

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


BILD = {}
prova.bygg_inom_grans, prova.kor, prova.Server = bygg_falsk, kor_falsk, ServerFalsk


# --- falska sessioner med transkript i provets egen projektkatalog ---
SESSIONER, SVAR = [], {}


def rad(**r):
    return json.dumps(r, ensure_ascii=False)


def transkript(handelser, sid):
    """Ett transkript i Claude Codes radformat: (verktyg, input, svar) där svar är text, ('fel', text), ('bild',) eller None."""
    rader = [rad(type='user', timestamp='2026-10-07T10:00:00.000Z', message={'role': 'user', 'content': 'uppdraget'}),
             rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'pendingMcpServers': [], 'needsAuthMcpServers': [], 'failedMcpServers': [],
                                               'addedNames': ['mcp__refero__refero_search_screens', 'mcp__mobbin__search_screens']})]
    for i, (namn, inp, svar) in enumerate(handelser, 1):
        rader.append(rad(type='assistant', timestamp='2026-10-07T10:00:%02d.000Z' % (i % 60), message={'role': 'assistant', 'model': 'claude-sonnet-5-5',
                                                                                                         'content': [{'type': 'tool_use', 'id': 't%d' % i, 'name': namn, 'input': inp}]}))
        if svar is None:
            continue
        fel = isinstance(svar, tuple) and svar[0] == 'fel'
        innehall = [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': 'iVBORw0KGgo='}}] if svar == ('bild',) else \
            [{'type': 'text', 'text': svar[1] if fel else svar}]
        rader.append(rad(type='user', timestamp='2026-10-07T10:00:%02d.500Z' % (i % 60), message={'role': 'user', 'content': [
            dict({'type': 'tool_result', 'tool_use_id': 't%d' % i, 'content': innehall}, **({'is_error': True} if fel else {}))]}))
    pr = bildkedja.PROJEKT / 'p'
    pr.mkdir(parents=True, exist_ok=True)
    (pr / (sid + '.jsonl')).write_text('\n'.join(rader) + '\n')
    return sid


def sess_falsk(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None):
    SESSIONER.append({'prompt': prompt, 'verktyg': list(verktyg), 'ut': Path(ut).name, 'schema': schema, 'frist': frist, 'nekas': list(nekas),
                      'slug': slug, 'modell': modell, 'max_turer': max_turer})
    nyckel = next((k_ for k_ in SVAR if k_(prompt, schema)), None)
    so, sid = SVAR[nyckel](prompt, schema) if nyckel else (None, None)
    svar_ = {'structured_output': so, 'num_turns': 9, 'duration_ms': 60000, 'total_cost_usd': 0.1, 'session_id': sid}
    Path(ut).write_text(json.dumps(svar_))
    return svar_


atelje.session = sess_falsk
KRITIKSVAR = {'storsta_problem': 'första vyns bild är för liten i 390', 'synliga_problem': ['768: rubriken bryts i fyra rader'],
              'generiskt': False, 'rekommendation': 'byt komposition', 'motivering': 'idén bär men formen gör det inte',
              'bredder': ['390', '768', '1280', '1440'], 'tillstand': ['meny', 'tangentbord', 'reflow'],
              'forebilder': [{'tjanst': 'refero', 'forebild': 'en snickares startsida', 'jamforelse': 'förebilden låter jobben bära första vyn'}],
              'valda': [{'fil': '.claude/skills/hallmark/references/slop-test.md', 'varfor': 'sex axlar för det generiska'}]}


def kritiker(sid_fn=None, svar=None):
    """Kritikens falska session: svaret, och ett transkript ur sid_fn() när det ges."""
    SVAR.clear()
    SVAR[lambda p, s: s is kd.SKISSKRITIK_SCHEMA] = lambda p, s: (dict(KRITIKSVAR, **(svar or {})), sid_fn() if sid_fn else None)


def nekade(regler, vag):
    """Täcker någon av Read-reglerna vägen (relativ repots rot, eller absolut med //)? Samma form som Claude Codes regler:
    Read(./a/b) är filen, Read(./a/**) allt under a, Read(./a/**/*.zip) varje .zip under a, Read(//abs/**) absolut."""
    import fnmatch
    for r_ in regler:
        m = re.fullmatch(r'Read\((.+)\)', r_)
        if not m:
            continue
        mon = m.group(1)
        mon = mon[2:] if mon.startswith('./') else ('/' + mon[2:]) if mon.startswith('//') else mon
        if mon.endswith('/**') and (vag == mon[:-3] or vag.startswith(mon[:-3] + '/')):
            return True
        if '**/' in mon:
            bas, _, svans = mon.partition('/**/')
            if vag.startswith(bas + '/') and fnmatch.fnmatch(Path(vag).name, svans):
                return True
        if vag == mon:
            return True
    return False


# ===== 1. kritikens block =====
@fall('1 kritikens block: passet skisskritik har kärna, alternativ, förhandsvisning, detektor och Refero och Mobbin; sessionen får blockets verktyg och tjänster, och prompten bär blockets uppgift')
def _block():
    k = kompetens.tolka()
    roller = kompetens.for_pass('skisskritik', k)
    assert len(roller) == 1, [r['id'] for r in roller]
    r = roller[0]
    assert 'kunskap/visuell-niva.md' in r['karna'] and len(r['karna']) >= 2 and r['valj'], r
    assert {'förhandsvisning', 'detektor'} <= set(r['verktyg']) and set(r['mcp']) == {'refero', 'mobbin'}, r
    assert kompetens.prova() == [], kompetens.prova()
    kund()
    kritiker()
    SESSIONER.clear()
    post = kd.skisskritik(SLUG, 'k01')
    s = [x for x in SESSIONER if x['schema'] is kd.SKISSKRITIK_SCHEMA]
    assert post and len(s) == 1, SESSIONER
    s = s[0]
    v = s['verktyg']
    for m in ('Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --granskare)' % SLUG,
              'Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --granskare *)' % SLUG,
              'Bash(.venv/bin/python kontroller/detektor.py %s --kandidat k01 --granskare)' % SLUG, 'Skill', 'ToolSearch', 'Read'):
        assert m in v, (m, v)
    assert not any(x.startswith(('Write', 'Edit')) or x.endswith('--kandidat k01 *)') or x.endswith('--kandidat k01)') for x in v), v
    # tjänsterna når sessionen genom kundvakten och Mobbins anslutning, som för skaparen
    assert s['slug'] == SLUG and s['modell'] == kd.GRANSKARE_MODELL and s['frist'] == kd.FRIST_SKISSKRITIK, s
    a = atelje.session_args(v, kd.SKISSKRITIK_SCHEMA, 10, 'm', 'high', s['nekas'], SLUG)
    assert '--settings' in a and 'kundvakt.py' in a[a.index('--settings') + 1] and str(KOPIA / 'kontroller' / 'mcp' / 'mobbin.json') in a, a
    assert a[a.index('--tools') + 1] == 'Bash,Glob,Grep,Read,Skill,ToolSearch', a[a.index('--tools') + 1]
    p = s['prompt']
    assert 'Rollerna i skisskritiken' in p and r['uppgift'] in p and all(kompetens.vag(f) in p for f in r['karna']), p[:1500]
    assert 'MCP: Refero' in p and 'Mobbin' in p and 'mode "standard"' in p and 'aldrig kundens namn' in p, p
    assert 'detektor.py %s --kandidat k01 --granskare' % SLUG in p and '--granskare' in p, p
    # kriterierna bor i blocket: kartans uppgift ändras, så ändras prompten (inga egna kriterier i koden)
    spara = kompetens.tolka
    kompetens.tolka = lambda text=None: {k_: dict(x_, uppgift='ÄNDRAD UPPGIFT UR KARTAN') if k_ == r['id'] else x_ for k_, x_ in spara(text).items()}
    try:
        SESSIONER.clear()
        kd.skisskritik(SLUG, 'k01')
        assert 'ÄNDRAD UPPGIFT UR KARTAN' in SESSIONER[0]['prompt'] and 'första vyns huvudkomposition' not in SESSIONER[0]['prompt'], SESSIONER[0]['prompt'][:800]
    finally:
        kompetens.tolka = spara
    # svaret följer schemat med bredderna, tillstånden, förebilderna och de valda alternativen
    req = set(kd.SKISSKRITIK_SCHEMA['required'])
    assert {'bredder', 'tillstand', 'forebilder', 'valda', 'storsta_problem', 'rekommendation'} <= req, req


# ===== 2. förhandsvisningen i kritikens egen katalog =====
def avbild(rot):
    return {str(p.relative_to(rot)): p.read_bytes() for p in sorted(Path(rot).rglob('*')) if p.is_file()}


@fall('2 kritikens förhandsvisning skriver i granskare/, tar fyra bredder med menyn, tangentbordet och reflow, och skaparens varv och anrop är orörda')
def _katalog():
    kund()
    d = kd.kdir(SLUG, 'k01')
    fore, nr_fore = avbild(d / 'varv'), kd.varvnummer(SLUG, 'k01')
    INSPEKTERAT.clear()
    rc, text, ut = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
    assert rc == 0 and ut == d / forhandsvisa.GRANSKARE / 'start' / 'varv-01', (rc, ut, text[:300])
    c = INSPEKTERAT[-1]
    assert c[c.index('--vyer') + 1] == '390,768,1280,1440' and c[c.index('--meny') + 1] == forhandsvisa.MENYKNAPP, c
    assert {'tangentbord', 'reflow'} <= set(c[c.index('--tillstand') + 1].split(',')), c
    assert avbild(d / 'varv') == fore and kd.varvnummer(SLUG, 'k01') == nr_fore == [1], 'skaparens varv och varvräkning är orörda'
    assert not list(ut.glob('*.zip')) and (d / 'varv' / 'start' / 'varv-01' / 'vy-390-spar.zip').is_file(), 'kritikens spår tas bort, skaparens står kvar'
    for b_ in forhandsvisa.BREDDER:
        assert forhandsvisa.giltig_bild(ut / ('vy-%s-forsta.png' % b_)) and kd.rel(ut / ('vy-%s-forsta.png' % b_)) in text, (b_, text)
    assert 'tangentbord' in text and 'meny' in text and 'reflow' in text, text
    # kommandoraden, med samma flagga som kritikens behörighet
    assert forhandsvisa.main([SLUG, '--kandidat', 'k01', '--granskare']) == 0 and (d / forhandsvisa.GRANSKARE / 'start' / 'varv-02').is_dir()
    assert forhandsvisa.main([SLUG, '--granskare']) == 2, '--granskare gäller bara en kandidats sida'
    # skaparens anrop är oförändrat: varvet hamnar i varv/, bara 390 och 1440 utan --mellan, och spåret står kvar
    rc, text, ut2 = forhandsvisa.forhandsvisa(SLUG, kandidat='k01')
    c2 = INSPEKTERAT[-1]
    assert rc == 0 and ut2 == d / 'varv' / 'start' / 'varv-02' and c2[c2.index('--vyer') + 1] == '390,1440' and '--meny' not in c2, (ut2, c2)
    assert list(ut2.glob('*.zip')) and kd.varvnummer(SLUG, 'k01') == [1, 2]
    shutil.rmtree(ut2)
    # ett avbrutet försök sparas med kritikens bilder, som hör till det försöket
    mal = kd.arkivera_forsok(SLUG, 'k01', {'forsok': 1})
    assert (mal / forhandsvisa.GRANSKARE / 'start' / 'varv-01').is_dir() and not (d / forhandsvisa.GRANSKARE).exists(), list(mal.iterdir())


# ===== 3. blindningen =====
@fall('3 blindningen: skaparens text, uppdrag, referenspaket och kod nekas, också transkripten och spåren; verktygen ger ingen kod')
def _blind():
    kund()
    kritiker()
    (kd.kdir(SLUG, 'k01') / forhandsvisa.GRANSKARE / 'start' / 'varv-01').mkdir(parents=True, exist_ok=True)
    skriv(kd.kdir(SLUG, 'k01') / forhandsvisa.GRANSKARE / 'start' / 'varv-01' / 'vy-768-forsta.png', png(768))
    SESSIONER.clear()
    kd.skisskritik(SLUG, 'k01')
    neka = SESSIONER[-1]['nekas'] + atelje.NEKAS
    # skalkommandona som läser filer nekas: i en verklig session läste `… --granskare | grep -r <ord> underlag/<slug>`
    # skaparens RIKTNING.md förbi Read-förbuden (2026-10-07)
    for c_ in ('grep', 'rg', 'cat', 'head', 'tail', 'find', 'sed', 'awk', 'xargs', 'strings'):
        assert 'Bash(%s *)' % c_ in neka and 'Bash(%s)' % c_ in neka, 'kritiken får inte %s: %s' % (c_, [x for x in neka if x.startswith('Bash(')][:6])
    u, d, sajt = 'underlag/%s' % SLUG, 'underlag/%s/atelje/kandidater/k01' % SLUG, 'kunder/%s/kandidater/k01/sajt' % SLUG
    hemliga = ['%s/RIKTNING.md' % d, '%s/UPPDRAG.md' % d, '%s/STATUS.json' % d, '%s/kod/index.astro' % d, '%s/kod-src/styles/sida.css' % d,
               '%s/DESIGN.md' % d, '%s/versioner/abc123/kod/index.astro' % d, '%s/svar-skiss-1.json' % d, '%s/varv/start/varv-01/vy-390-spar.zip' % d,
               '%s/src/pages/index.astro' % sajt, '%s/src/styles/sida.css' % sajt, '%s/DESIGN.md' % sajt, '%s/dist/index.html' % sajt,
               '%s/REFERENSER.md' % u, '%s/referenser/paket-v01/xref/vy-390-forsta.png' % u, '%s/referenser/tjanster/TJANSTER.md' % u,
               '%s/atelje/KANDIDATPLAN.json' % u, '%s/atelje/FORSKNING.md' % u,
               'underlag/%s/atelje/kandidater/k02/RIKTNING.md' % SLUG, 'kunder/%s/kandidater/k02/sajt/src/pages/index.astro' % SLUG]
    oppna = ['%s/varv/start/varv-01/vy-390-forsta.png' % d, '%s/%s/start/varv-01/vy-768-forsta.png' % (d, forhandsvisa.GRANSKARE),
             '%s/BRIEF.md' % u, '%s/DESIGNDOMAR.jsonl' % u, '%s/atelje/metod/METOD-skiss.md' % u, 'kunskap/visuell-niva.md',
             '.claude/skills/impeccable/reference/critique.md']
    for h in hemliga:
        assert nekade(neka, h), 'kritiken når %s' % h
    for o in oppna:
        assert not nekade(neka, o), 'kritiken nekas %s, som den ska se' % o
    assert nekade(neka, str(bildkedja.PROJEKT / 'p' / 'x.jsonl')), 'transkripten (skaparens text och kod) nekas: %s' % neka[-6:]
    p = SESSIONER[-1]['prompt']
    assert SKAPARMARKOR not in p and UPPDRAGSMARKOR not in p and KODMARKOR not in p, 'prompten bär aldrig skaparens text, uppdrag eller kod'
    # verktygen: byggloggen och fotograferingens logg når aldrig kritiken, men skaparen får dem som förut
    BYGG.update(rc=1, logg='src/pages/index.astro:2:5\n> 2 | <h1 class="%s">\nSyntaxfel' % KODMARKOR)
    try:
        rc, text, _ = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
        assert rc == 2 and KODMARKOR not in text and 'bygget föll' in text, text
        rc, text, _ = forhandsvisa.forhandsvisa(SLUG, kandidat='k01')
        assert rc == 2 and KODMARKOR in text, 'skaparen får byggloggen som förut'
    finally:
        BYGG.update(rc=0, logg='byggt')
    BILD.update(saknas='1440', logg='Error at %s\n    at render (src/pages/index.astro:2)' % KODMARKOR)
    try:
        rc, text, ut = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
        assert rc == 2 and KODMARKOR not in text and 'fotograferingen gav inte' in text, text
    finally:
        BILD.clear()
    # detektorn: utan --granskare utdragen (som skaparen får dem), med --granskare regeln, beskrivningen och antalet, aldrig koden
    motor = skriv(TMP / 'motor' / 'impeccable', '#!/bin/bash\ncat <<\'EOF\'\n%s\nEOF\n' % json.dumps([
        {'antipattern': 'side-tab', 'name': 'Side-tab accent border', 'description': 'Thick colored border on one side of a card.', 'severity': 'warning',
         'category': 'slop', 'file': '/x/%s/dist/index.html' % KODMARKOR, 'line': 3, 'snippet': '<div> "%s": border-left: 4px' % KODMARKOR},
        {'antipattern': 'side-tab', 'name': 'Side-tab accent border', 'description': 'Thick colored border on one side of a card.', 'severity': 'warning',
         'category': 'slop', 'snippet': '.%s' % KODMARKOR, 'message': 'class %s' % KODMARKOR, 'selector': '.%s' % KODMARKOR}]))
    motor.chmod(0o755)
    skriv(kd.ksajt(SLUG, 'k01') / 'dist' / 'index.html', '<h1 class="%s">Skiss</h1>' % KODMARKOR)
    env = dict(os.environ, IMPECCABLE_BIN=str(motor))
    cmd = [str(KOPIA / '.venv' / 'bin' / 'python'), '-B', str(KOPIA / 'kontroller' / 'detektor.py'), SLUG, '--kandidat', 'k01']
    r1 = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    r2 = subprocess.run(cmd + ['--granskare'], capture_output=True, text=True, env=env, timeout=60)
    assert r1.returncode == 0 and KODMARKOR in r1.stdout, 'utan --granskare ger detektorn utdragen: %s' % r1.stdout
    assert r2.returncode == 0 and KODMARKOR not in r2.stdout + r2.stderr and 'side-tab' in r2.stdout and '×2' in r2.stdout, r2.stdout + r2.stderr
    # ett verktyg som ger kod eller skaparens text kan aldrig tilldelas ett blint pass
    karta = metod.KARTA.read_text(encoding='utf-8')
    rid = kompetens.for_pass('skisskritik')[0]['id']
    blk = re.search(r'```kompetens %s\n.*?```' % rid, karta, re.S).group(0)
    lackt = karta.replace(blk, re.sub(r'(?m)^verktyg: (.*)$', r'verktyg: \1, design', blk))
    assert any('blind' in f_ and 'design' in f_ for f_ in kompetens.prova(lackt)), kompetens.prova(lackt)


# ===== 4. kvittot =====
KARNSID = '1f0e0d0c-0b0a-4908-8706-050403020101'


def kritikens_transkript(slug=SLUG, kid='k01', karna=None, bilder=None):
    d = kd.kdir(slug, kid)
    g = d / forhandsvisa.GRANSKARE / 'start' / 'varv-01'
    karna = [kompetens.vag(f) for f in kompetens.for_pass('skisskritik')[0]['karna']] if karna is None else karna
    alt = kompetens.vag(kompetens.for_pass('skisskritik')[0]['valj'][0])
    h = [('Read', {'file_path': str(KOPIA / f)}, 'innehållet') for f in karna] + [('Read', {'file_path': str(KOPIA / alt)}, 'innehållet')]
    h += [('Bash', {'command': '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat %s --granskare' % (slug, kid)}, '# Förhandsvisning (granskarens)'),
          ('Bash', {'command': '.venv/bin/python kontroller/detektor.py %s --kandidat %s --granskare' % (slug, kid)}, ('fel', 'Exit code 3\nmotorn saknas')),
          ('mcp__refero__refero_search_screens', {'query': 'carpenter website hero mobile', 'platform': 'web'}, ('bild',)),
          ('mcp__mobbin__search_screens', {'query': 'contractor landing page', 'mode': 'standard'}, '{"results": []}')]
    for b_ in (bilder if bilder is not None else [str(g / ('vy-%s-forsta.png' % b)) for b in forhandsvisa.BREDDER] + [str(g / 'vy-390-meny.png'), str(g / 'vy-390-reflow320.png'), str(g / 'FORHAND.md')]):
        h.append(('Read', {'file_path': b_}, ('bild',) if b_.endswith('.png') else 'innehållet'))
    return transkript(h, KARNSID)


@fall('4 kompetenskvittot räknar kärnan, de valda alternativen, verktygsanropen och tjänsternas anrop med utfall; SKISSKRITIK.json bär versionen och bilderna')
def _kvitto():
    kund()
    rc, text, g = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
    assert rc == 0, text
    kritiker(sid_fn=lambda: kritikens_transkript())
    post = kd.skisskritik(SLUG, 'k01')
    f = json.loads((kd.kdir(SLUG, 'k01') / 'SKISSKRITIK.json').read_text())
    assert f['rekommendation'] == 'byt komposition' and f['storsta_problem'] and f['varv'] == 1, f
    kv = f['kompetens']
    roll = kompetens.for_pass('skisskritik')[0]
    assert kv['verifierad'] and sorted(kv['lasta']) == sorted(kompetens.vag(x) for x in roll['karna']) and not kv['saknas'], kv
    assert kv['valda'] == [kompetens.vag(roll['valj'][0])], kv['valda']
    assert kv['verktyg_anrop']['förhandsvisning'] == {'anrop': 1, 'ok': 1, 'fel': 0} and kv['verktyg_anrop']['detektor'] == {'anrop': 1, 'ok': 0, 'fel': 1}, kv['verktyg_anrop']
    T = kompetens.TILLSTAND
    t = {r_['roll']: r_ for r_ in kv['tillstand']}[roll['id']]
    assert t['karna']['tillstand'] == kompetens.LASKVITTO and t['verktyg'] == {'förhandsvisning': T['anvant'], 'detektor': T['blockerat']}, t
    assert t['mcp']['refero']['tillstand'] == T['anvant'] and t['mcp']['mobbin']['tillstand'] == T['blockerat'] and 'tomt resultat' in t['mcp']['mobbin']['orsak'], t['mcp']
    # versionen är kandidatens version när kritiken började: samma hash som fotograferingen ger för samma kod
    v = f['version']
    assert v == kd.projektets_version(SLUG, 'k01'), v
    kd.fotografera(SLUG, 'k01', skiss=True)
    assert kd.version(SLUG, 'k01') == v, 'kritikens version och fotograferingens ska vara samma hash för samma kod'
    assert f['bilder'] == [kd.rel(kd.kdir(SLUG, 'k01') / 'varv' / 'start' / 'varv-01' / ('vy-%s-%s.png' % (b_, s_))) for b_ in ('390', '1440') for s_ in ('forsta', 'hela')], f['bilder']
    bed = f['bedomt']
    assert bed['verifierad'] and bed['bedomda_bredder'] == list(forhandsvisa.BREDDER) and bed['tillstand']['meny'] and bed['tillstand']['tangentbord'], bed
    assert not bed['pastadda_utan_belagg'], bed
    # tangentbordets steg i förhandsvisningens svar räknas som sett, utan att FORHAND.md lästs
    tsid = transkript([('Bash', {'command': '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --granskare 2>&1 | tail -60' % SLUG},
                        'Interaktionsvägen:\n- 390 px tangentbord: 6 steg, 0 utan synlig fokus')], '3f0e0d0c-0b0a-4908-8706-050403020103')
    assert kd.bedomt(tsid, SLUG, 'k01')['tillstand']['tangentbord'], 'tangentbordet i förhandsvisningens svar'
    tsid = transkript([('Bash', {'command': '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01' % SLUG},
                        '- 390 px tangentbord: 6 steg, 0 utan synlig fokus')], '3f0e0d0c-0b0a-4908-8706-050403020104')
    assert not kd.bedomt(tsid, SLUG, 'k01')['tillstand']['tangentbord'], 'skaparens förhandsvisning är inte granskarens'
    # kvittot för en session utan transkript är inte observerat, aldrig inte gjort
    kritiker()
    post = kd.skisskritik(SLUG, 'k01')
    t2 = {r_['roll']: r_ for r_ in post['kompetens']['tillstand']}[roll['id']]
    assert not post['kompetens']['verifierad'] and t2['verktyg']['förhandsvisning'] == T['ej_observerat'] and not post['bedomt']['bedomda_bredder'], t2


# ===== 5. tiden =====
@fall('5 tiden: fristen och reserven bygger på mätningen, och skissförsöket ger kritiken just den fristen')
def _tid():
    assert kd.MATT_SKISSKRITIK['sekunder'] > 0 and kd.MATT_SKISSKRITIK['modell'] == kd.GRANSKARE_MODELL, kd.MATT_SKISSKRITIK
    assert kd.FRIST_SKISSKRITIK >= kd.MATT_SKISSKRITIK['sekunder'] * 1.25, (kd.FRIST_SKISSKRITIK, kd.MATT_SKISSKRITIK)
    assert kd.SKISSKRITIK_RESERV == kd.FRIST_SKISSKRITIK + kd.SVAR_MIN, (kd.SKISSKRITIK_RESERV, kd.FRIST_SKISSKRITIK, kd.SVAR_MIN)
    skapare = kd.FRIST_SKISS - kd.FOTO_RESERV - kd.SKISSKRITIK_RESERV
    assert skapare >= 15 * 60, 'skaparens tid i försöket: %d s' % skapare
    # skissförsöket med en falsk klocka: skaparen får försöket minus reserven, och kritiken just sin frist
    kund()

    class Klocka:
        t = 0.0

        def __getattr__(self, n_):
            import time as tid_
            return getattr(tid_, n_)

        def monotonic(self):
            return Klocka.t
    spara = kd.time
    kd.time = Klocka()
    SVAR.clear()

    def skapa(p, s):
        Klocka.t += 600
        return None, None

    def kritik(p, s):
        Klocka.t += 300
        return dict(KRITIKSVAR), None
    SVAR[lambda p, s: s is kd.SKISSKRITIK_SCHEMA] = kritik
    SVAR[lambda p, s: s is None] = skapa
    SESSIONER.clear()
    kd.satt_status(SLUG, 'k01', 'planerad', 'prov', ta_bort=('skisskritik',))
    try:
        kd.skissa(SLUG, 'k01')
    finally:
        kd.time = spara
    sk = [x for x in SESSIONER if x['schema'] is kd.SKISSKRITIK_SCHEMA]
    forsta = SESSIONER[0]
    assert sk and sk[0]['frist'] == kd.FRIST_SKISSKRITIK, [(x['ut'], x['frist']) for x in SESSIONER]
    assert forsta['frist'] == kd.FRIST_SKISS - kd.FOTO_RESERV - kd.SKISSKRITIK_RESERV, forsta['frist']


# ===== 6. de andra sessionerna =====
@fall('6 research, jämförelsen och granskningens två pass får sina block, verktyg, tjänster och kvitton; listan över sessioner utan block stämmer med koden')
def _andra():
    kund()
    T = kompetens.TILLSTAND
    for p_ in ('forska', 'jamforelse', 'kritik_a', 'kritik_b'):
        assert kompetens.for_pass(p_), 'passet %s har ingen roll' % p_
    assert kompetens.for_pass('kritik_a') == kompetens.for_pass('skisskritik'), 'granskningens första pass delar kritikens block: samma uppgift'
    # researchen
    SVAR.clear()
    SVAR[lambda p, s: s in (kd.FORSKA_SCHEMA, kd.FORSKA_SCHEMA_SKISS, kd.FORSKA_SCHEMA_SKISS_BRED)] = lambda p, s: (
        {'varfor': 'befintligt material räcker', 'riktningar': 'tre grunder', 'sajter': [], 'fragor': [],
         'antaganden': [{'antagande': 'besökaren vill se jobb', 'underlag': 'ännu inte observerat', 'provning': 'uppgift', 'om_fel': 'kontakt först'}]},
        transkript([('Read', {'file_path': str(KOPIA / kompetens.vag(f))}, 'x') for f in kompetens.for_pass('forska')[0]['karna']]
                   + [('mcp__refero__refero_search_styles', {'query': 'warm craftsman editorial'}, ('bild',))], '2f0e0d0c-0b0a-4908-8706-050403020102'))
    SESSIONER.clear()
    import skapande
    spara_k = skapande.komplettera
    skapande.komplettera = lambda *a, **k: (_ for _ in ()).throw(AssertionError('inget hämtas när materialet räcker'))
    try:
        kd.forska(SLUG, 3, skiss=True)
    finally:
        skapande.komplettera = spara_k
    s = SESSIONER[0]
    assert 'Rollerna i researchen' in s['prompt'] and 'Bash(.venv/bin/python -B kontroller/uxsok.py *)' in s['verktyg'] and s['slug'] == SLUG, s['verktyg']
    fo = json.loads((kd.rot(SLUG) / 'FORSKNING.json').read_text())
    assert fo['kompetens']['verifierad'] and not fo['kompetens']['saknas'] and fo['kompetens']['mcp_anrop'] == {'mcp__refero__refero_search_styles': 1}, fo['kompetens']
    assert 'Kompetensen' in (kd.rot(SLUG) / 'FORSKNING.md').read_text()
    # jämförelsen och granskningens två pass (läget full)
    for kid in ('k01', 'k02'):
        b = kd.kdir(SLUG, kid) / 'bilder' / 'start'
        for b_ in ('390', '768', '1440'):
            for s_ in ('forsta', 'hela'):
                skriv(b / ('vy-%s-%s.png' % (b_, s_)), png(int(b_)))
        kd.satt_status(SLUG, kid, 'klar', 'prov', version='v-%s' % kid)
    SVAR.clear()
    SVAR[lambda p, s: s is kd.JAMFOR_SCHEMA] = lambda p, s: ({'sammanfattning': 'olika', 'par': []}, None)
    SVAR[lambda p, s: s is kd.KRITIK_A_SCHEMA] = lambda p, s: ({'forsta_intryck': {'framgar': 'x', 'genomarbetat': 'x', 'skaver': 'x'},
                                                                'uppgift': {'uppgift': 'x', 'kan_genomforas': 'ja', 'belagg': 'x'}, 'styrkor': [],
                                                                'niva': 'nastan', 'material': 'x', 'avvikelser': []}, None)
    SVAR[lambda p, s: s is kd.KRITIK_B_SCHEMA] = lambda p, s: ({'helhet': 'x', 'referens': {'kvaliteten_bar': 'delvis', 'skal': 'x'}, 'motiveringar': []}, None)
    SESSIONER.clear()
    kd.jamfor(SLUG)
    j = SESSIONER[-1]
    assert 'Rollerna i jämförelsen' in j['prompt'] and 'Skill' in j['verktyg'], j['verktyg']
    assert 'kompetens' in json.loads((kd.rot(SLUG) / 'JAMFORELSE.json').read_text())
    SESSIONER.clear()
    kd.kritik(SLUG, 'k01')
    a_, b_ = [x for x in SESSIONER if x['schema'] is kd.KRITIK_A_SCHEMA][0], [x for x in SESSIONER if x['schema'] is kd.KRITIK_B_SCHEMA][0]
    assert 'Rollerna i granskningens första pass' in a_['prompt'] and 'Bash(.venv/bin/python kontroller/detektor.py %s --kandidat k01 --granskare)' % SLUG in a_['verktyg'], a_['verktyg']
    neka = a_['nekas']
    assert nekade(neka, 'kunder/%s/kandidater/k01/sajt/src/pages/index.astro' % SLUG) and nekade(neka, 'underlag/%s/referenser/paket-v01/xref/vy-390-forsta.png' % SLUG), \
        'granskningens första pass är blint för koden och referenspaketet, som kritiken'
    assert not nekade(neka, 'underlag/%s/atelje/kandidater/k01/bilder/start/vy-390-forsta.png' % SLUG), 'första passet ser bilderna'
    assert 'Rollerna i granskningens andra pass' in b_['prompt'], b_['prompt'][:300]
    k_ = json.loads((kd.kdir(SLUG, 'k01') / 'KRITIK.json').read_text())
    assert set(k_['kompetens']) == {'a', 'b'} and 'tillstand' in k_['kompetens']['a'], k_.get('kompetens')
    # listan över sessioner utan block stämmer med koden: varje session i kandidatflödet har ett block eller ett skäl
    koden = kompetens.sessioner_i_koden()
    utan = kompetens.utan_block()
    for f_ in ('skisskritik', 'forska', 'jamfor', 'kritik'):
        assert koden[f_] and all(x['kompetens'] for x in koden[f_]), (f_, koden.get(f_))
    assert set(utan) == {f_ for f_, xs in koden.items() if any(not x['kompetens'] for x in xs)}, (utan, koden)
    assert all(len(s_) >= 60 and not re.fullmatch(r'(?i)\W*ingen\s+tilldelning\W*', s_) for s_ in utan.values()), utan
    assert kompetens.sessionsfel() == [], kompetens.sessionsfel()
    # skälen går att pröva: sessionerna utan block (skaparen i läget full och förbättringsrundan) bygger efter metodens
    # före-fil METOD-skapa.md, och läsningen av den prövas i transkriptet (kandidater.lasningen)
    import ast
    fns = {n.name: n for n in ast.walk(ast.parse((KOPIA / 'kontroller' / 'kandidater.py').read_text(encoding='utf-8'))) if isinstance(n, ast.FunctionDef)}
    for f_ in utan:
        anropade = {x.func.id for x in ast.walk(fns[f_]) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)}
        assert {'lasningen', 'skapar_prompt'} <= anropade, (f_, sorted(anropade))
        assert 'METOD-skapa' in utan[f_] and 'lasningen' in utan[f_], 'skälet säger vad som prövas: %s' % utan[f_]
    assert 'METOD-skapa' in kd.skapar_prompt(SLUG, 'k01') and 'METOD-skapa' in kd.skapar_prompt(SLUG, 'k01', forbattra=True)
    # en session utan block som saknar skäl i kartan fälls, och ett tomt skäl likaså
    karta = metod.KARTA.read_text(encoding='utf-8')
    utan_rad = re.search(r'(?m)^(%s): .+$' % re.escape(sorted(utan)[0]), karta).group(0)
    assert any(sorted(utan)[0] in f_ for f_ in kompetens.sessionsfel(karta.replace(utan_rad + '\n', ''))), 'en session utan block och utan skäl fälls'
    assert any(sorted(utan)[0] in f_ for f_ in kompetens.prova(karta.replace(utan_rad + '\n', ''))), 'kompetens.prova fäller den också'
    assert any('skäl' in f_ for f_ in kompetens.sessionsfel(karta.replace(utan_rad, '%s: ingen tilldelning' % sorted(utan)[0]))), '"ingen tilldelning" är inget skäl'


# ===== 7. en tom eller saknad 768-bild =====
@fall('7 en tom eller saknad 768-bild leder aldrig till att kritiken tros ha bedömt mellanbredden')
def _tom768():
    kund()
    d = kd.kdir(SLUG, 'k01')
    BILD.update(tom='768')
    try:
        rc, text, g = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
    finally:
        BILD.clear()
    assert rc == 0 and (g / 'vy-768-forsta.png').stat().st_size == 0 and not (g / 'vy-768-hela.png').exists(), list(g.iterdir())
    fh = (g / 'FORHAND.md').read_text()
    assert re.search(r'vy-768-forsta\.png \(saknas eller är tom', fh) and re.search(r'vy-768-hela\.png \(saknas eller är tom', fh), fh
    # kritiken läser den tomma bilden utan fel och säger sig ha sett 768: det belagda säger något annat
    kritiker(sid_fn=lambda: kritikens_transkript(bilder=[str(g / ('vy-%s-forsta.png' % b)) for b in forhandsvisa.BREDDER]))
    post = kd.skisskritik(SLUG, 'k01')
    bed = post['bedomt']
    assert not bed['bredder']['768']['bedomd'] and bed['bredder']['768'].get('tomma') and '768' not in bed['bedomda_bredder'], bed['bredder']['768']
    assert '768' in bed['pastadda_utan_belagg'] and bed['bedomda_bredder'] == ['390', '1280', '1440'], bed
    rader = '\n'.join(kd.skisskritik_rader(post))
    assert 'inte bedömt: 768' in rader and 'vilar inte på en bild' in rader, rader
    # en tom bild hos skaparen erbjuds aldrig kritiken som sedd
    skriv(d / 'varv' / 'start' / 'varv-01' / 'vy-1440-hela.png', b'')
    kritiker()
    SESSIONER.clear()
    post = kd.skisskritik(SLUG, 'k01')
    assert 'vy-1440-hela.png' not in SESSIONER[-1]['prompt'] and all('1440-hela' not in b_ for b_ in post['bilder']), post['bilder']


# ===== 8. metodlåset =====
@fall('8 metodlåset: metod.py och kompetens.py prövar kartan, och en ändrad källa i kritikens kärna stoppar leveransen')
def _las():
    fel, kallor = metod.prova()
    assert fel == [] and kompetens.prova() == [], (fel, kompetens.prova())
    for f_ in kompetens.for_pass('skisskritik')[0]['karna'] + kompetens.for_pass('forska')[0]['karna']:
        assert f_ in kallor, '%s ligger utanför låset' % f_
    kalla = metod.kalla(kompetens.for_pass('skisskritik')[0]['karna'][-1])
    spara = kalla.read_text(encoding='utf-8')
    kalla.write_text(spara + '\nen ändring\n', encoding='utf-8')
    try:
        fel2, _ = metod.prova()
        assert any('har ändrats' in f_ for f_ in fel2), fel2
    finally:
        kalla.write_text(spara, encoding='utf-8')
    r_ = subprocess.run([str(KOPIA / '.venv' / 'bin' / 'python'), '-B', str(KOPIA / 'kontroller' / 'kompetens.py'), '--prova'], capture_output=True, text=True, timeout=120)
    assert r_.returncode == 0 and 'kompetenserna håller' in r_.stdout, r_.stdout + r_.stderr


print('skisskritikens prov: %d fall, %d föll' % (8, len(FEL)), file=sys.stderr)
sys.exit(1 if FEL else 0)
