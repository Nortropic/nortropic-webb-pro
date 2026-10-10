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
8. metodlåset: metod.py och kompetens.py prövar kartan, och en ändrad källa stoppar leveransen;
9. kandidaternas oberoende (GR-20261007-r103#B1): skaparens sessioner nekas de läsande skalkommandona och de andra
   kandidaternas kataloger, och de egna verktygen (förhandsvisningen, typsnitten, design, detektorn, uxsok) och det
   egna projektet går som förut; varje session som arbetar med en kandidat får förbuden;
10. kritikens uttryckliga lista (GR-20261007-r103#B2): i underlag/<slug> bara briefen och kundens fakta och material,
   research på begäran nekas också när den uppstår under sessionen, kunder/<slug> nekas, och riktningshistoriken och
   domloggen nekas som filer (#K4, ägarens beslut 2026-10-07; en tom tupel ändrar det).

    .venv/bin/python kontroller/rokprov/revision/prov_skisskritik.py <repo>

Fall 1–8 var röda mot 63c09c5 (gren B:s topp, där skisskritiken bara hade läsverktygen), fall 9 och 10 mot 13743c9 (före
rättelsen av kandidaternas oberoende och kritikens lista). Varje fall redovisas för sig på stderr; slutkod 1 när något
fall föll. Ingenting skrivs i repots underlag/ eller kunder/, och inga privata data läses: den syntetiska kunden finns
bara i provets kopia.
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

# Även delprovens hjälpare måste importeras ur kopian: de använder sin egen
# __file__ för att lägga kontroller/ först och kan ladda fler produktionsmoduler.
# En återställning av sys.path efter en import räcker inte för sys.modules.
sys.path[:0] = [str(KOPIA / 'kontroller'), str(KOPIA / 'kontroller' / 'rokprov' / 'revision')]
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import forhandsvisa  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import metod  # noqa: E402
import prova  # noqa: E402
import korregister  # noqa: E402
from prov_kompetensflode import giltigt_kvitto
from prov_omgranskning import kompetenssteg
import referensfixtur  # noqa: E402  referenskontraktets fixtur
korregister.registrera_tmp(TMP, 'prov_skisskritik')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
assert atelje.ROOT == KOPIA and forhandsvisa.ROOT == KOPIA and bildkedja.ROOT == KOPIA, (atelje.ROOT, forhandsvisa.ROOT)
for namn in ('prov_kompetensflode', 'prov_omgranskning'):
    assert Path(sys.modules[namn].__file__).resolve().is_relative_to(KOPIA), 'provens hjälpare lästes utanför kopian: ' + namn
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
    import referensfixtur  # referenskontraktet uppfyllt, så att provet prövar skisskritiken och inte startvillkoret
    plan = referensfixtur.uppfyll(atelje.UNDERLAG, slug, {'lage': 'skiss', 'tid': '2026-10-07T08:00:00Z', 'kompetens': giltigt_kvitto('planera'), 'kandidater': {
        'k01': {'uppgift': 'Besökaren vill se ett liknande jobb och ringa.', 'titel': UPPDRAGSMARKOR},
        'k02': {'uppgift': 'Besökaren vill skriva en förfrågan.'}}})
    skriv(r / 'KANDIDATPLAN.json', json.dumps(plan))
    skriv(r / 'FORSKNING.md', '# Research %s\n' % UPPDRAGSMARKOR)
    skriv(r / 'metod' / 'METOD-skiss.md', '# Metoden\n')
    for kid in ('k01', 'k02'):
        d = kd.kdir(slug, kid)
        referensfixtur.uppdrag(atelje.UNDERLAG, slug, plan, kid, '# Uppdrag %s\n' % UPPDRAGSMARKOR)
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
                                               'addedNames': ['mcp__refero__refero_search_screens', 'mcp__mobbin__search_screens', 'mcp__21st__search']})]
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


def kompetens_transkript(pass_, extra=()):
    """Explicit syntetisk kompetens för positiva flödesfixturer; negativa läsprov ger eget transkript."""
    import uuid
    h = [(n, inp, 'syntetiskt läskvitto') for n, inp in kompetenssteg(pass_)]
    for m in dict.fromkeys(m for r in kompetens.for_pass(pass_) for m in r.get('mcp_krav', [])):
        namn = {'refero': 'refero_search_styles', 'mobbin': 'search_screens', '21st': 'search'}[m]
        h.append(('mcp__%s__%s' % (m, namn), {'query': 'synthetic service', 'mode': 'standard'}, ('bild',)))
    return transkript(h + list(extra), str(uuid.uuid4()))


def session_utan_block_fixtur(karta):
    """Pröva skälregeln även när alla verkliga sessioner numera har kompetensblock.

    Bara en syntetisk kodfil ändras; sessionsfel läser den med sin riktiga AST-tolk.
    """
    namn = 'syntetisk_session_utan_block'
    kod = (KOPIA / 'kontroller' / 'kandidater.py').read_text(encoding='utf-8')
    fil = Path(tempfile.mkdtemp(dir=TMP)) / 'kandidater.py'
    fil.write_text(kod + '\n\ndef %s(ut):\n    return atelje.session("syntetiskt uppdrag", [], ut)\n' % namn, encoding='utf-8')
    rad = namn + ': En syntetisk lässession utan skrivning; dess fasta svar och utdata prövas uttryckligen av detta isolerade prov.'
    block = kompetens.UTANBLOCK.search(karta)
    assert block, 'kartan saknar listan över sessioner utan block'
    karta = karta[:block.end('rader')] + rad + '\n' + karta[block.end('rader'):]
    assert kompetens.sessioner_i_koden(fil)[namn][0]['kompetens'] is False
    assert kompetens.sessionsfel(karta, fil=fil) == [], kompetens.sessionsfel(karta, fil=fil)
    return namn, rad, karta, fil


def sess_falsk(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None, blind=None, webb=False):
    SESSIONER.append({'prompt': prompt, 'verktyg': list(verktyg), 'ut': Path(ut).name, 'schema': schema, 'frist': frist, 'nekas': list(nekas),
                      'slug': slug, 'modell': modell, 'effort': effort, 'max_turer': max_turer, 'blind': blind})
    nyckel = next((k_ for k_ in SVAR if k_(prompt, schema)), None)
    so, sid = SVAR[nyckel](prompt, schema) if nyckel else (None, None)
    # Framgångsfixturernas modeller lämnar numera verklig syntetisk läs-/Skill-evidens.
    # Ett uttryckligt session-id används orört, också när dess transkript saknas.
    if sid is None:
        pass_ = next((p for s, p in ((kd.SKISSKRITIK_SCHEMA, 'skisskritik'), (kd.JAMFOR_SCHEMA, 'jamforelse'),
                                    (kd.KRITIK_A_SCHEMA, 'kritik_a'), (kd.KRITIK_B_SCHEMA, 'kritik_b')) if schema is s), None)
        if schema is None:
            pass_ = 'fordjupa' if Path(ut).name.startswith(('svar-forfina-', 'svar-uppdrag-')) else 'skapa'
        elif schema is kd.PASS_SCHEMA:
            pass_ = next(p for p, namn in kompetens.PASSNAMN.items() if 'specialisten för %s' % namn in prompt)
        if pass_:
            # det svaret redovisar som valt är också läst (kompetens.redovisade_brister): en framgångsfixtur bär sin evidens
            valda_ = [('Read', {'file_path': str(atelje.ROOT / v['fil'])}, 'syntetiskt läskvitto')
                      for v in (so or {}).get('valda') or [] if isinstance(v, dict) and isinstance(v.get('fil'), str)]
            sid = kompetens_transkript(pass_, valda_)
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


def monster(mon):
    """Ett vägmönster i Claude Codes regelform (gitignore) som reguljärt uttryck: ** över kataloger, * och ? inom en del."""
    ut, i = '', 0
    while i < len(mon):
        if mon.startswith('/**/', i):
            ut, i = ut + '/(?:.*/)?', i + 4
        elif mon.startswith('/**', i) and i + 3 == len(mon):
            ut, i = ut + '(?:/.*)?', i + 3
        elif mon.startswith('**', i):
            ut, i = ut + '.*', i + 2
        else:
            ut, i = ut + {'*': '[^/]*', '?': '[^/]'}.get(mon[i], re.escape(mon[i])), i + 1
    return ut


def nekade(regler, vag):
    """Täcker någon av Read-reglerna vägen (relativ repots rot, eller absolut med //)? Samma form som Claude Codes regler:
    Read(./a/b) är filen, Read(./a/**) allt under a, Read(./a/**/*.zip) varje .zip under a, Read(./a/X-*) varje fil i a
    vars namn börjar med X-, Read(//abs/**) absolut."""
    for r_ in regler:
        m = re.fullmatch(r'Read\((.+)\)', r_)
        if not m:
            continue
        mon = m.group(1)
        mon = mon[2:] if mon.startswith('./') else ('/' + mon[2:]) if mon.startswith('//') else mon
        if re.fullmatch(monster(mon), vag):
            return True
    return False


def bash_regler(regler):
    """Bash-reglerna som reguljära uttryck: * står för vad som helst, och regeln gäller hela kommandot från början."""
    return [re.compile('.*'.join(re.escape(d) for d in m.group(1).split('*'))) for m in (re.fullmatch(r'Bash\((.+)\)', r_) for r_ in regler) if m]


def bash_traff(regler, kommando):
    return any(r_.fullmatch(kommando) for r_ in bash_regler(regler))


# ===== 1. kritikens block =====
@fall('1 kritikens block: passet skisskritik har kärna, alternativ, förhandsvisning, detektor och Refero och Mobbin; sessionen får blockets verktyg och tjänster, och prompten bär blockets uppgift')
def _block():
    k = kompetens.tolka()
    roller = kompetens.for_pass('skisskritik', k)
    assert len(roller) == 1, [r['id'] for r in roller]
    r = roller[0]
    assert 'kunskap/designregler.md' in r['karna'] and len(r['karna']) >= 2 and r['valj'], r
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
               'underlag/%s/atelje/kandidater/k02/RIKTNING.md' % SLUG, 'kunder/%s/kandidater/k02/sajt/src/pages/index.astro' % SLUG,
               '%s/DESIGNDOMAR.jsonl' % u]  # domloggen som fil: ägarens beslut 2026-10-07 (GR-20261007-r103#K4), fall 10
    oppna = ['%s/varv/start/varv-01/vy-390-forsta.png' % d, '%s/%s/start/varv-01/vy-768-forsta.png' % (d, forhandsvisa.GRANSKARE),
             '%s/BRIEF.md' % u, '%s/atelje/metod/METOD-skiss.md' % u, 'kunskap/designregler.md',
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
          ('Bash', {'command': 'cat kontroller/forhandsvisa.py | head -40'}, '#!/usr/bin/env python3'),  # en läsning av skriptet är inget anrop (GR-20261008-r117-claude#C7)
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
    kritiker(lambda: '00000000-0000-4000-8000-000000000099')
    try:
        kd.skisskritik(SLUG, 'k01')
        raise AssertionError('saknat transkript fick passera kompetensgrinden')
    except RuntimeError as e:
        assert 'kompetenskrav' in str(e), e
    post = json.loads((kd.kdir(SLUG, 'k01') / 'SKISSKRITIK.json').read_text())
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
        kompetens_transkript('forska', referensfixtur.webbhandelser()))  # referenskontraktet: webbsökningen och Awwwards-besöket
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
    assert fo['kompetens']['verifierad'] and not fo['kompetens']['saknas'] and fo['kompetens']['mcp_anrop'] == {
        'mcp__refero__refero_search_styles': 1, 'mcp__mobbin__search_screens': 1, 'mcp__21st__search': 1}, fo['kompetens']
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
    # en syntetisk session utan block som saknar skäl i kartan fälls, och ett tomt skäl likaså
    karta = metod.KARTA.read_text(encoding='utf-8')
    utan_namn, utan_rad, provkarta, provkod = session_utan_block_fixtur(karta)
    assert any(utan_namn in f_ for f_ in kompetens.sessionsfel(provkarta.replace(utan_rad + '\n', ''), fil=provkod)), 'en session utan block och utan skäl fälls'
    from unittest.mock import patch
    las_koden = kompetens.sessioner_i_koden
    with patch.object(kompetens, 'sessioner_i_koden', side_effect=lambda fil=None: las_koden(fil or provkod)):
        assert any(utan_namn in f_ for f_ in kompetens.prova(provkarta.replace(utan_rad + '\n', ''))), 'kompetens.prova fäller den också'
    assert any('skäl' in f_ for f_ in kompetens.sessionsfel(provkarta.replace(utan_rad, '%s: ingen tilldelning' % utan_namn), fil=provkod)), '"ingen tilldelning" är inget skäl'
    # jämförelsen går inte att lura med ett alias för atelje.session: som värde, som argument eller som import fälls det
    # (GR-20261007-r103#K2)
    kod_ = (KOPIA / 'kontroller' / 'kandidater.py').read_text(encoding='utf-8')
    for namn_, tillagg_ in (('värde', '\n\ndef smyg_a(slug):\n    s = atelje.session\n    return s(slug, [])\n'),
                            ('argument', '\n\ndef smyg_b(slug, starta=atelje.session):\n    return starta(slug, [])\n'),
                            ('import', '\n\nfrom atelje import session as _s\n\n\ndef smyg_c(slug):\n    return _s(slug, [])\n')):
        f_ = Path(tempfile.mkdtemp(dir=TMP)) / 'kandidater.py'
        f_.write_text(kod_ + tillagg_, encoding='utf-8')
        fel_ = kompetens.sessionsfel(fil=f_)
        assert any('alias för atelje.session' in x for x in fel_), ('ett alias som %s fälldes inte' % namn_, fel_)


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


# ===== 9. kandidaternas oberoende =====
EGNA_KOMMANDON = {  # skaparens egna verktyg i passens form: de släpps och nekas aldrig
    'skiss': ['.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01' % SLUG,
              '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --mellan' % SLUG,
              '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --tillstand tangentbord,reflow --meny button' % SLUG,
              '.venv/bin/python kontroller/typsnitt.py %s @fontsource/inter' % SLUG,
              '.venv/bin/python -B kontroller/uxsok.py "carpenter portfolio" --domain ux'],
    'forfina': ['.venv/bin/python kontroller/design.py %s --kandidat k01' % SLUG, '.venv/bin/python kontroller/design.py %s --kandidat k01 --skriv' % SLUG,
                '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --mellan' % SLUG],
    'granskning': ['.venv/bin/python kontroller/detektor.py %s --kandidat k01' % SLUG, '.venv/bin/python kontroller/detektor.py %s --kandidat k01 --json' % SLUG,
                   '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --tillstand tangentbord' % SLUG],
}


def egna_slapps(verktyg, nekas, kommandon):
    """Varje eget kommando matchar en tillåtelse och inget förbud (sessionens och atelje.NEKAS)."""
    for c_ in kommandon:
        assert bash_traff(verktyg, c_), 'det egna kommandot tillåts inte: %s' % c_
        assert not bash_traff(list(nekas) + atelje.NEKAS, c_), 'det egna kommandot nekas: %s' % c_


@fall('9 kandidaternas oberoende: skaparens sessioner nekas de läsande skalkommandona och de andra kandidaternas kataloger; de egna verktygen och det egna projektet går som förut')
def _oberoende():
    kund()
    # skissförsöket som i flödet: skaparens session, kritiken och skaparens svar, med de argument koden ger
    SVAR.clear()
    SVAR[lambda p, s: s is kd.SKISSKRITIK_SCHEMA] = lambda p, s: (dict(KRITIKSVAR), None)
    SVAR[lambda p, s: s is None] = lambda p, s: (None, None)
    kd.satt_status(SLUG, 'k01', 'planerad', 'prov', ta_bort=('skisskritik',))
    SESSIONER.clear()
    kd.skissa(SLUG, 'k01')
    skapare = [x for x in SESSIONER if x['schema'] is None]
    assert [x['ut'] for x in skapare] == ['svar-skiss-1.json', 'svar-skiss-1-granskning.json'], [x['ut'] for x in SESSIONER]
    a, sajt = 'underlag/%s/atelje/kandidater' % SLUG, 'kunder/%s/kandidater' % SLUG
    # listan får inte krympa tyst: varje läsare här står i LASANDE_SKAL (en ändring av listan är en ändring av provet)
    lasare = ('cat', 'head', 'tail', 'less', 'more', 'grep', 'egrep', 'fgrep', 'rg', 'ag', 'ack', 'find', 'ls', 'tree', 'du', 'stat', 'file', 'wc',
              'sed', 'awk', 'cut', 'sort', 'uniq', 'tr', 'nl', 'tac', 'rev', 'paste', 'join', 'comm', 'diff', 'cmp', 'strings', 'xxd', 'od', 'hexdump',
              'base64', 'jq', 'xargs', 'zcat', 'unzip', 'zipinfo', 'tar', 'perl', 'ruby', 'python', 'python3', 'look', 'column', 'fold', 'iconv',
              'cp', 'mv', 'ln', 'tee', 'dd')
    assert set(lasare) <= set(kd.LASANDE_SKAL), sorted(set(lasare) - set(kd.LASANDE_SKAL))
    for s in skapare:
        n = s['nekas'] + atelje.NEKAS
        for c_ in lasare:  # ensamt och med argument; Claude Code prövar varje led i en pipe eller sekvens för sig
            assert 'Bash(%s)' % c_ in n and 'Bash(%s *)' % c_ in n, 'skaparen (%s) får %s' % (s['ut'], c_)
        for c_ in ('grep -r ord %s' % sajt, 'cat %s/k0*/sajt/src/pages/index.astro' % sajt, 'find %s -name index.astro' % sajt, 'ls -R %s' % a):
            assert bash_traff(n, c_), 'skaparen (%s) får köra %s' % (s['ut'], c_)
        for h in ('%s/k02/sajt/src/pages/index.astro' % sajt, '%s/k02/RIKTNING.md' % a, '%s/k02/kod/index.astro' % a):
            assert nekade(n, h), 'skaparen (%s) når %s' % (s['ut'], h)
        for o in ('%s/k01/sajt/src/pages/index.astro' % sajt, '%s/k01/sajt/src/styles/sida.css' % sajt, '%s/k01/RIKTNING.md' % a,
                  '%s/k01/UPPDRAG.md' % a, '%s/k01/varv/start/varv-01/vy-390-forsta.png' % a, 'underlag/%s/BRIEF.md' % SLUG, 'kunskap/designregler.md'):
            assert not nekade(n, o), 'skaparen (%s) nekas sitt eget %s' % (s['ut'], o)
        assert 'Write(./%s/k01/sajt/src/**)' % sajt in s['verktyg'] and 'Edit(./%s/k01/RIKTNING.md)' % a in s['verktyg'], s['verktyg']
        egna_slapps(s['verktyg'], s['nekas'], EGNA_KOMMANDON['skiss'])
    # förfiningen läser delarna ägaren gillade i k02 med Read, men inget skal; passet granskning har detektorn
    f_n = kd.andra_nekas(SLUG, 'k01', utom=['k02'])
    assert not nekade(f_n, '%s/k02/sajt/src/pages/index.astro' % sajt) and 'Bash(grep *)' in f_n, f_n
    egna_slapps(kd.forfina_verktyg(SLUG, 'k01'), f_n, EGNA_KOMMANDON['forfina'])
    egna_slapps(kd.verktyg(SLUG, 'k01', komplettering=False) + kompetens.verktyg('granskning', SLUG, 'k01'), kd.andra_nekas(SLUG, 'k01'),
                EGNA_KOMMANDON['granskning'])
    # varje session som arbetar med en kandidat nekas de andra kandidaterna och skalets läsare (andra_nekas, eller
    # blind_nekas som bygger på den); bara sessionerna före skisserna och jämförelsen, som ser alla kandidaters bilder, saknar förbud
    import ast
    fns = [n_ for n_ in ast.walk(ast.parse((KOPIA / 'kontroller' / 'kandidater.py').read_text(encoding='utf-8'))) if isinstance(n_, ast.FunctionDef)]
    utan, med = set(), {}
    for fn in fns:
        for x in ast.walk(fn):
            if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'session' and getattr(x.func.value, 'id', '') == 'atelje':
                nek = next((k_.value for k_ in x.keywords if k_.arg == 'nekas'), None)
                if nek is None:
                    utan.add(fn.name)
                else:
                    med.setdefault(fn.name, set()).add(ast.unparse(nek).split('(')[0])
    assert utan == {'forska', 'planera', 'planprovning', 'omplanera', 'jamfor'}, utan  # omplanera: återgångens planeringssession (2E), som planera
    assert all(v <= {'andra_nekas', 'blind'} for v in med.values()) and {'skissa', 'skapa', 'forbattra', 'uppdrag_session', 'kompetenspass'} <= set(med), med
    # uppdragets session (2026-10-10, samma anrop som Dyad-provet kör) startas av forfina_kandidat
    assert 'uppdrag_session' in {x.func.id for fn in fns if fn.name == 'forfina_kandidat' for x in ast.walk(fn) if isinstance(x, ast.Call) and isinstance(x.func, ast.Name)}
    assert all('blind_nekas' in ast.unparse(fn) for fn in fns if 'blind' in med.get(fn.name, set())), 'blind är blind_nekas'


# ===== 10. kritikens uttryckliga lista =====
@fall('10 kritikens blindning är en uttrycklig lista: i underlag/<slug> bara briefen och kundens fakta och material; research på begäran nekas också när den uppstår under sessionen, kunder/<slug> nekas, och historiken och domloggen nekas som filer (K4, lätt att ändra)')
def _lista():
    u = kund()
    skriv(u / 'RESEARCH.md', '# Research\n\n## Bara de har\n\n- syntetiskt\n')
    skriv(u / 'INNEHALL.md', '# Innehåll\n')
    skriv(u / 'TEXTUNDERLAG.md', '# Textunderlag\n')
    skriv(u / 'BESTALLNING.md', '# Beställning\n')
    skriv(u / 'bilder' / 'BILDER.md', '# Bilder\n')
    skriv(u / 'bilder' / 'jobb-1.png', png(64, 48))
    skriv(u / 'REFERENSUPPDRAG-2026-10-07T081500Z-abc123.json', json.dumps({'kandidater': [{'varfor': SKAPARMARKOR}]}))
    skriv(u / 'TJANSTEUPPDRAG-2026-10-07T081500Z-abc123.json', json.dumps({'fragor': [{'syfte': SKAPARMARKOR}]}))
    skriv(u / 'RIKTNINGSHISTORIK.json', json.dumps([{'namn': 'Tidigare grundidé', 'drag': UPPDRAGSMARKOR}]))
    skriv(u / 'UPPTAGNA-VAL.md', '# Upptagna val %s\n' % UPPDRAGSMARKOR)
    skriv(u / 'omtag' / '20261001T000000Z' / 'k09' / 'abc123def456' / 'kod' / 'index.astro', KODMARKOR)
    skriv(atelje.KUNDER / SLUG / 'sajt' / 'src' / 'pages' / 'index.astro', KODMARKOR)
    skriv(atelje.KUNDER / SLUG / 'kundrepo' / 'src' / 'pages' / 'index.astro', KODMARKOR)
    shutil.rmtree(u / 'referenser')  # referenssteget har inte gått ännu när kritiken startar
    (u / 'REFERENSER.md').unlink()
    SENARE = ('UPPTAGNA-VAL.md', 'DESIGNDOMAR-belagg.jsonl', 'UPPDRAG.md', 'KUNDSTART.json', 'DIAGNOS.md', 'FRASER.txt', 'material/MATERIAL.json',
              'diagnos/RAPPORT.md', 'forhand/vy-390-forsta.png', 'ateljestarter/start.json', 'kalla/extern/omdomen.txt', 'omtag/x/KVITTO.json')
    for f_ in SENARE:  # det systemet kan skriva i underlag/<slug>/ under kritiken finns inte när den startar (GR-20261007-r107#K2)
        if (u / f_).is_file():
            (u / f_).unlink()
    kritiker()
    SESSIONER.clear()
    kd.skisskritik(SLUG, 'k01')
    s = SESSIONER[-1]
    U, A = 'underlag/%s' % SLUG, 'underlag/%s/atelje/kandidater/k01' % SLUG
    # en annan kandidat begär research medan kritiken arbetar, och referenssteget skriver paketet och beslutet: mönstren
    # gäller också filer som inte fanns när sessionen startade
    skriv(u / 'REFERENSUPPDRAG-2026-10-07T120000Z-sent01.json', json.dumps({'kandidater': [{'varfor': SKAPARMARKOR}]}))
    skriv(u / 'TJANSTEUPPDRAG-2026-10-07T120000Z-sent01.json', json.dumps({'fragor': [{'syfte': SKAPARMARKOR}]}))
    skriv(u / 'REFERENSER.md', '# Referenser\n\nReferensbeslutet %s\n' % UPPDRAGSMARKOR)
    skriv(u / 'referenser' / 'paket-v01' / 'xref' / 'vy-390-forsta.png', png())
    for f_ in SENARE:
        skriv(u / f_, png() if f_.endswith('.png') else '%s\n' % UPPDRAGSMARKOR)
    hemliga = ['%s/%s' % ('underlag/%s' % SLUG, f_) for f_ in SENARE] + ['%s/%s' % (U, f_) for f_ in ('REFERENSUPPDRAG-2026-10-07T081500Z-abc123.json', 'TJANSTEUPPDRAG-2026-10-07T081500Z-abc123.json',
                                            'REFERENSUPPDRAG-2026-10-07T120000Z-sent01.json', 'TJANSTEUPPDRAG-2026-10-07T120000Z-sent01.json',
                                            'RIKTNINGSHISTORIK.json', 'DESIGNDOMAR.jsonl', 'UPPTAGNA-VAL.md', 'REFERENSER.md',
                                            'omtag/20261001T000000Z/k09/abc123def456/kod/index.astro', 'referenser/paket-v01/xref/vy-390-forsta.png')] + \
        ['kunder/%s/%s/src/pages/index.astro' % (SLUG, k_) for k_ in ('sajt', 'kundrepo', 'kandidater/k01/sajt', 'kandidater/k02/sajt')]
    oppna = ['%s/%s' % (U, f_) for f_ in ('BRIEF.md', 'VERKSAMHET.json', 'RESEARCH.md', 'INNEHALL.md', 'TEXTUNDERLAG.md', 'BESTALLNING.md',
                                          'bilder/BILDER.md', 'bilder/jobb-1.png', 'atelje/metod/METOD-skiss.md')] + \
        ['%s/%s/start/varv-01/vy-768-forsta.png' % (A, forhandsvisa.GRANSKARE), 'kunskap/designregler.md', '.claude/skills/hallmark/references/slop-test.md']
    for namn_, n, egna in (('skisskritiken', s['nekas'] + atelje.NEKAS, '%s/varv/start/varv-01/vy-390-forsta.png' % A),
                           ('granskningens första pass', kd.blind_nekas(SLUG, 'k01', ('bilder', forhandsvisa.GRANSKARE)) + atelje.NEKAS,
                            '%s/bilder/start/vy-390-forsta.png' % A)):
        for h in hemliga:
            assert nekade(n, h), '%s når %s' % (namn_, h)
        for o in oppna + [egna]:
            assert not nekade(n, o), '%s nekas %s, som den ska läsa' % (namn_, o)
        assert 'Bash(grep *)' in n and 'Bash(cat *)' in n, namn_
    # kritikens verktyg går som förut
    egna_slapps(s['verktyg'], s['nekas'], ['.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --granskare' % SLUG,
                                          '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 --granskare --sida /om/' % SLUG,
                                          '.venv/bin/python kontroller/detektor.py %s --kandidat k01 --granskare' % SLUG])
    # ägarens aktuella domar står i uppdraget, och uppdraget säger att domloggen och historiken är stängda
    p = s['prompt']
    assert 'pröva nya grundidéer' in p and 'domloggen och riktningshistoriken är stängda' in p, p[:1500]
    # K4 är ägarens beslut 2026-10-07 ("Ja, neka historiken") och lätt att ändra: en tom tupel öppnar filerna, och resten står kvar
    assert kd.BLIND_HISTORIK == ('RIKTNINGSHISTORIK.json', 'DESIGNDOMAR.jsonl'), kd.BLIND_HISTORIK
    spara = kd.BLIND_HISTORIK
    kd.BLIND_HISTORIK = ()
    try:
        n2 = kd.blind_nekas(SLUG, 'k01', ('varv', forhandsvisa.GRANSKARE))
        assert not nekade(n2, '%s/RIKTNINGSHISTORIK.json' % U) and not nekade(n2, '%s/DESIGNDOMAR.jsonl' % U), 'en tom tupel öppnar historiken'
        assert nekade(n2, '%s/REFERENSUPPDRAG-2026-10-07T081500Z-abc123.json' % U) and nekade(n2, '%s/UPPTAGNA-VAL.md' % U), n2
    finally:
        kd.BLIND_HISTORIK = spara
    # metodkartans block kritik säger samma sak som koden, och att beslutet är ägarens (2026-10-07), med fyndets id
    blk = re.search(r'```kompetens kritik\n(.*?)```', metod.KARTA.read_text(encoding='utf-8'), re.S).group(1)
    rad = next((r_ for r_ in blk.splitlines() if r_.startswith('blind:')), '')
    assert all(f_ in rad for f_ in kd.BLIND_HISTORIK) and 'ägarens beslut 2026-10-07' in rad and 'GR-20261007-r103#K4' in rad, rad


@fall('11 avbrutet försöks kritik och status följer med arkivet')
def _arkiv_kritik():
    kund(); d=kd.kdir(SLUG,'k01')
    kd.satt_status(SLUG,'k01','under_arbete',forsok=1,skisskritik={'gjord':True})
    skriv(d/'SKISSKRITIK.json',json.dumps({'version':'gammal','motivering':'syntetiskt gammalt omdöme'}))
    skriv(d/'svar-skisskritik-1.json','{"result":"syntetiskt"}')
    mal=kd.arkivera_forsok(SLUG,'k01',kd.las_status(SLUG,'k01'))
    assert (mal/'SKISSKRITIK.json').is_file() and not (d/'SKISSKRITIK.json').exists()
    assert json.loads((mal/'STATUS.json').read_text())['forsok']==1
    assert (mal/'svar-skisskritik-1.json').is_file()


@fall('12 behandla_skiss kör ny kritik efter avbrott trots gammal statusflagga')
def _aterupptagen_kritik():
    from unittest.mock import patch
    kund(); d=kd.kdir(SLUG,'k01'); kritiker(); SESSIONER.clear()
    huvud=atelje.KUNDER/SLUG/'sajt'
    shutil.copytree(kd.ksajt(SLUG,'k01'),huvud)
    (huvud/'node_modules').mkdir()
    kd.satt_status(SLUG,'k01','under_arbete',forsok=1,skisskritik={'gjord':True})
    skriv(d/'SKISSKRITIK.json',json.dumps({'version':'gammal'}))
    riktig=kd.forbered_projekt
    def forbered(slug,kid):
        riktig(slug,kid)
        skriv(kd.ksajt(slug,kid)/'src/pages/index.astro','<h1>Syntetiskt nytt försök</h1>')
        vd=kd.kdir(slug,kid)/'varv/start/varv-01'
        for b in ('390','1440'):
            for slag in ('forsta','hela'):skriv(vd/('vy-%s-%s.png'%(b,slag)),png(int(b)))
    with patch.object(kd,'forbered_projekt',forbered):
        kd.behandla_skiss(SLUG,'k01')
    anrop=[x for x in SESSIONER if x['schema'] is kd.SKISSKRITIK_SCHEMA]
    assert len(anrop)==1,[(x['ut'],bool(x['schema'])) for x in SESSIONER]
    post=json.loads((d/'SKISSKRITIK.json').read_text())
    assert post['identitet']['forsok']==2 and post['identitet']['kandidat']=='k01'
    assert (d/'forsok-1/SKISSKRITIK.json').is_file()


@fall('13 kritikens giltighet kräver samma försök, underlag och artefakt; saknad fil är okänd')
def _kritik_identitet():
    kund(); d=kd.kdir(SLUG,'k01'); kritiker()
    kd.satt_status(SLUG,'k01','under_arbete',forsok=1)
    post=kd.skisskritik(SLUG,'k01')
    assert kd.skisskritik_giltig(SLUG,'k01',post)
    fil=atelje.UNDERLAG/SLUG/'BRIEF.md';innan=fil.read_bytes();fil.write_bytes(innan+b'\nAndrat syntetiskt uppdrag')
    assert not kd.skisskritik_giltig(SLUG,'k01',post)
    fil.write_bytes(innan); assert kd.skisskritik_giltig(SLUG,'k01',post)
    index=kd.ksajt(SLUG,'k01')/'src/pages/index.astro';index.write_text('<h1>Ny version</h1>')
    assert not kd.skisskritik_giltig(SLUG,'k01',post)
    post=kd.skisskritik(SLUG,'k01'); assert kd.skisskritik_giltig(SLUG,'k01',post)
    kd.satt_status(SLUG,'k01','under_arbete',forsok=2)
    assert not kd.skisskritik_giltig(SLUG,'k01',post)
    (d/'SKISSKRITIK.json').unlink()
    assert not kd.skisskritik_giltig(SLUG,'k01')
    kd.satt_status(SLUG,'k01','klar',forsok=2,
                   kompetens={'skiss:skapa': {'pass': 'skapa', 'kvitto': giltigt_kvitto('skapa')}})
    antal=len(SESSIONER);kd.behandla_skiss(SLUG,'k01')
    assert len(SESSIONER)==antal,'färdig skiss arbetades om automatiskt'


def godkann_foto():
    st=kd.fotografera(SLUG,'k01',skiss=True)
    assert st['status']=='klar',st
    # Detta fall prövar material/version, så det får explicit syntetiskt komplett förfiningsunderlag.
    kd.satt_status(SLUG,'k01','forfinad',design_fel=[],
                   forfining={'dom': 'syntetisk', 'kompetens': giltigt_kvitto('fordjupa')},
                   kompetens={'fordjupa:syntetisk:%s' % p: {'pass': p, 'genomford': True, 'uppfyllt': True,
                                                           'kvitto': giltigt_kvitto(p)} for p in kd.KOMPETENSPASS})
    skriv(kd.rot(SLUG)/'STATUS.json',json.dumps({'kandidatflode':True,'steg':'klar_for_bedomning','fas':'forfining'}))
    return atelje.doma(SLUG,'ägaren','godkand','Syntetiskt godkännande.',
                       kandidater=[{'id':'k01','version':st['version']}],belagg='syntetiskt prov',tid=atelje.nu())


@fall('14 godkänd kandidat överför samma public-filer och kundbilder till helbygget')
def _materialoverforing():
    kund();s=kd.ksajt(SLUG,'k01')
    skriv(s/'public/illustration.svg','<svg><!-- syntetiskt original --></svg>')
    skriv(s/'src/assets/atelje/material.png',png())
    forhandsversion=kd.projektets_version(SLUG,'k01')
    godkann_foto()
    assert kd.version(SLUG,'k01')==forhandsversion
    huvud=atelje.KUNDER/SLUG/'sajt'
    skriv(huvud/'public/illustration.svg','annat tidigare material')
    atelje.installera_godkand(SLUG)
    assert (huvud/'public/illustration.svg').read_bytes()==(s/'public/illustration.svg').read_bytes()
    assert (huvud/'src/assets/atelje/material.png').read_bytes()==png()
    v=kd.projektets_version(SLUG,'k01')
    skriv(s/'public/illustration.svg','ändrad bild')
    assert kd.projektets_version(SLUG,'k01')!=v,'public-filen ingick inte i versionen'
    assert any(p.read_text()=='annat tidigare material' for p in (atelje.KUNDER/SLUG/'startsida-ersatt').rglob('*.svg'))


@fall('15 nytt underlag efter fotografering eller godkännande kräver ny bedömning')
def _andrat_underlag():
    kund();u=atelje.UNDERLAG/SLUG;st=kd.fotografera(SLUG,'k01',skiss=True)
    brief=u/'BRIEF.md';innan=brief.read_bytes();brief.write_bytes(innan+b'\nNytt behov')
    try:
        tmp,_=kd.forbered_vinnare(SLUG,'k01',st['version'])
    except ValueError as e:
        assert 'underlag' in str(e)
    else:
        shutil.rmtree(tmp)
        raise AssertionError('ändrat underlag godkändes mot äldre fotografering')
    brief.write_bytes(innan);godkann_foto()
    assert kd.skapande.godkand_giltig(SLUG,atelje.UNDERLAG,atelje.KUNDER)[0]
    skriv(u/'bilder/nytillkommen.png',png())
    ok,skal=kd.skapande.godkand_giltig(SLUG,atelje.UNDERLAG,atelje.KUNDER)
    assert not ok and 'underlag' in skal,(ok,skal)
    try:atelje.installera_godkand(SLUG)
    except RuntimeError as e:assert 'underlag' in str(e)
    else:raise AssertionError('överföringen accepterade ändrat underlag')


@fall('16 ändrat fryst material och länkade tillgångar ger inget godkännande eller delvis installation')
def _materialintegritet():
    kund();s=kd.ksajt(SLUG,'k01');skriv(s/'public/bild.svg','<svg/>');godkann_foto()
    fryst=kd.rot(SLUG)/'vinnare/material/public/bild.svg'
    assert fryst.is_file(),'materialet frystes inte'
    fryst.write_text('ändrat')
    huvud=atelje.KUNDER/SLUG/'sajt';skriv(huvud/'src/pages/index.astro','behåll')
    assert not kd.skapande.godkand_giltig(SLUG,atelje.UNDERLAG,atelje.KUNDER)[0]
    try:atelje.installera_godkand(SLUG)
    except RuntimeError:pass
    else:raise AssertionError('ändrat material installerades')
    assert (huvud/'src/pages/index.astro').read_text()=='behåll'
    kund();s=kd.ksajt(SLUG,'k01');skriv(s/'utanforsajt.txt','syntetiskt')
    (s/'public').mkdir();(s/'public/lank.txt').symlink_to('../utanforsajt.txt')
    try:kd.fotografera(SLUG,'k01',skiss=True)
    except (ValueError,RuntimeError):pass
    else:raise AssertionError('länkad tillgång försvann tyst ur versionen')


@fall('17 material som utelämnats ur den godkända kandidaten bevaras som tidigare material, inte i helbygget')
def _material_som_tagits_bort():
    kund();s=kd.ksajt(SLUG,'k01');skriv(s/'public/behall.svg','<svg/>');godkann_foto()
    huvud=atelje.KUNDER/SLUG/'sajt';skriv(huvud/'public/borttagen.svg','tidigare syntetiskt material')
    atelje.installera_godkand(SLUG)
    assert not (huvud/'public/borttagen.svg').exists()
    assert (huvud/'public/behall.svg').is_file()
    assert any(p.read_text()=='tidigare syntetiskt material' for p in (atelje.KUNDER/SLUG/'startsida-ersatt').rglob('borttagen.svg'))
    arkiv = atelje.KUNDER/SLUG/'startsida-ersatt'
    fore = sorted(str(p.relative_to(arkiv)) for p in arkiv.rglob('*'))
    assert atelje.installera_godkand(SLUG) == [], 'samma material ska inte installeras om'
    assert sorted(str(p.relative_to(arkiv)) for p in arkiv.rglob('*')) == fore, 'återförsöket skapade ett nytt arkiv'


@fall('18 fil på en godkänd underkatalogs plats stoppar före första ändringen')
def _material_malkonflikt():
    kund();s=kd.ksajt(SLUG,'k01');skriv(s/'public/bild/logo.svg','<svg/>');godkann_foto()
    huvud=atelje.KUNDER/SLUG/'sajt';skriv(huvud/'src/pages/index.astro','behåll index');skriv(huvud/'public/bild','behåll fil')
    try:atelje.installera_godkand(SLUG)
    except RuntimeError:pass
    else:raise AssertionError('en målkatalog var en vanlig fil')
    assert (huvud/'src/pages/index.astro').read_text()=='behåll index'
    assert (huvud/'public/bild').read_text()=='behåll fil'


@fall('19 kritikens försöksidentitet når slutposten och saknat bevis är inte genomförd kritik')
def _kritik_slutpost():
    import ateljeslut
    kund();kritiker();kd.satt_status(SLUG,'k01','under_arbete',forsok=1)
    post=kd.skisskritik(SLUG,'k01')
    kd.satt_status(SLUG,'k01','klar',version=post['version'],skisskritik={'gjord':True})
    def las():return ateljeslut.skisskritiken(SLUG,'k01',kd.las_status(SLUG,'k01'))
    assert las()['gjord'] and las()['aktuell'] and las()['identitet']==post['identitet']
    brief=atelje.UNDERLAG/SLUG/'BRIEF.md';brief.write_text(brief.read_text()+'\nÄndrat behov')
    assert not las()['gjord'] and las()['status']=='historisk' and las()['andrad_efter_bedomningen']
    (kd.kdir(SLUG,'k01')/'SKISSKRITIK.json').unlink()
    assert not las()['gjord'] and las()['status']=='okand'


@fall('20 ändrad råkälla upphäver underlagets godkännande')
def _rakalla():
    kund();kalla=atelje.UNDERLAG/SLUG/'kalla/fakta.txt';skriv(kalla,'Syntetisk uppgift A');godkann_foto()
    fore=kd.skapande.underlagsversion(SLUG,atelje.UNDERLAG);kalla.write_text('Syntetisk uppgift B')
    assert kd.skapande.underlagsversion(SLUG,atelje.UNDERLAG)!=fore
    assert not kd.skapande.godkand_giltig(SLUG,atelje.UNDERLAG,atelje.KUNDER)[0]


@fall('21 skisskaparens modell och effort når bara skaparens två pass, inte kritik eller generell ateljé')
def _skaparval():
    from unittest.mock import patch
    kund(); kritiker(); SESSIONER.clear()
    with patch.dict(os.environ, {'NWP_SKISSSKAPARE_MODELL': 'syntetisk-skaparmodell', 'NWP_SKISSSKAPARE_EFFORT': 'medium'}):
        kd.skissa(SLUG, 'k01')
        skapare = [x for x in SESSIONER if x['schema'] is None]
        krit = [x for x in SESSIONER if x['schema'] is kd.SKISSKRITIK_SCHEMA]
        assert len(skapare) == 2 and len(krit) == 1, [(s['ut'],s['schema'] is None) for s in SESSIONER]
        assert all(x['modell'] == 'syntetisk-skaparmodell' and x['effort'] == 'medium' for x in skapare), skapare
        assert krit[0]['modell'] == kd.GRANSKARE_MODELL and krit[0]['effort'] == 'high', krit
        args = atelje.session_args([], modell=skapare[0]['modell'], effort=skapare[0]['effort'])
        assert args[args.index('--model')+1] == 'syntetisk-skaparmodell' and args[args.index('--effort')+1] == 'medium'
        andra = atelje.session_args([])
        assert andra[andra.index('--model')+1] == atelje.MODELL and andra[andra.index('--effort')+1] == atelje.EFFORT
        st = kd.las_status(SLUG,'k01')
        assert st['skaparinstallningar']['begart'] == {'modell':'syntetisk-skaparmodell','effort':'medium'}, st
        assert st['skaparinstallningar']['observerat'] == {'modell':None,'effort':None}
        rapport = kd.redovisa_skiss(SLUG, {'modell':'syntetisk-allman-modell','tider':{}}).read_text()
        assert 'syntetisk-skaparmodell / medium' in rapport, 'rapporten tappade kandidatens begärda skaparval'
        assert 'inte bekräftat av modellen' in rapport, 'begärda inställningar visades som observerade'
    assert kd.skaparval() == {'modell':atelje.MODELL,'effort':kd.EFFORT_SKISS}


@fall('22 sammanhängande syntetiskt kundförlopp genom verkliga övergångar och kor.sh')
def _forlopp():
    import prov_forlopp
    prov_forlopp.kor(globals())

@fall('23 förberett A/B träffar bara skisskaparens två pass genom riktiga körvägen')
def _ab_skiss():
    sys.path.insert(0, str(KOPIA / 'kontroller' / 'rokprov' / 'revision'))
    from prov_ab_skiss_kedja import kor
    kor(globals())


@fall('24 K06: sessionen som svarar på granskningen eller fortsätter är en ny session utan minne: den får kompetensens rader och steg 0, aldrig beskedet att kärnan redan lästs')
def _ny_session():
    kr = {'varv': 1, 'storsta_problem': 'syntetiskt', 'synliga_problem': [], 'generiskt': False, 'rekommendation': 'behåll', 'motivering': 'm'}
    for p in (kd.skiss_prompt(SLUG, 'k01', kritik=kr), kd.skiss_prompt(SLUG, 'k01', fortsattning=True)):
        assert 'läste du i skissens första session' not in p and 'gjordes i skissens första session' not in p, p[-1500:]
        assert 'Detta är en ny session' in p and 'Steg 0 görs i varje session' in p, p[-1500:]
        assert 'Rollerna i ' in p and all(kompetens.vag(f) in p for f in kompetens.for_pass('skapa')[0]['karna']), 'kompetensens rader saknas i den nya sessionen'
    assert 'Detta är en ny session' not in kd.skiss_prompt(SLUG, 'k01'), 'den första sessionen är ingen fortsättning'



PNGHUVUD = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + (390).to_bytes(4, 'big') + (844).to_bytes(4, 'big') + b'\x08\x02\x00\x00\x00'


@fall('25 granskarens 14 luckor (GR-20261007-r103#K1): skalförbuden, detektorns granskarform, kritik_a som blint pass, tangentbordet, versionen, bildprövningen, granskningens tid, skälet och bildernas kataloger')
def _luckor_r103():
    kund()
    # M04–M06: de läsande skalkommandona base64, python3, cp, mv och ln nekas skaparen och kritiken
    sn = kd.skal_nekas()
    for c in ('base64', 'python3', 'cp', 'mv', 'ln'):
        assert 'Bash(%s)' % c in sn and 'Bash(%s *)' % c in sn, (c, [x for x in sn if c in x])
    # M16: detektorns granskarform har bara regelkatalogens fält, aldrig sidans kod eller plats
    import detektor
    g = detektor.for_granskaren([{'antipattern': 'tiny-text', 'name': 'Liten text', 'severity': 'hog', 'snippet': '<p>SIDANS KOD</p>',
                                  'file': 'index.html', 'line': 12, 'message': 'SIDANS TEXT'}])
    assert g and all(set(x) <= set(detektor.GRANSKARFALT) | {'antal'} for x in g) and 'SIDANS' not in json.dumps(g), g
    # M17: motorns egen felutskrift når aldrig granskaren
    dist = kd.ksajt(SLUG, 'k01') / 'dist'; dist.mkdir(parents=True, exist_ok=True)
    if not (dist / 'index.html').is_file():
        (dist / 'index.html').write_text('<p>bygget</p>')
    import contextlib, io
    spara_det = detektor.detektera
    detektor.detektera = lambda fil: (None, 'motorn gav inget läsbart svar (kod 1): <p>SIDANS KOD</p>')
    try:
        fel_ = io.StringIO()
        with contextlib.redirect_stderr(fel_):
            rc_ = detektor.main([SLUG, '--kandidat', 'k01', '--granskare'])
    finally:
        detektor.detektera = spara_det
    assert rc_ == 3 and 'SIDANS KOD' not in fel_.getvalue() and 'Impeccables motor' in fel_.getvalue(), fel_.getvalue()
    # M21: granskningens första pass (kritik_a) är blint: ett verktyg som ger kod där är ett fel i kartan
    karta = metod.KARTA.read_text(encoding='utf-8')
    rid = kompetens.for_pass('kritik_a')[0]['id']
    blk = re.search(r'```kompetens %s\n.*?```' % rid, karta, re.S).group(0)
    utan_skiss = re.sub(r'(?m)^pass: (.*)$', lambda m_: 'pass: ' + ', '.join(x for x in m_.group(1).split(', ') if x != 'skisskritik'), blk)
    lackt = karta.replace(blk, re.sub(r'(?m)^verktyg: (.*)$', r'verktyg: \1, design', utan_skiss))
    assert any('kritik_a' in f_ and 'design' in f_ for f_ in kompetens.prova(lackt)), [f_ for f_ in kompetens.prova(lackt) if 'blind' in f_]
    # M32: tangentbordet räknas bara ur granskarens egen FORHAND.md, aldrig ur skaparens
    skaparens = kd.kdir(SLUG, 'k01') / 'varv' / 'start' / 'varv-01' / 'FORHAND.md'
    skaparens.parent.mkdir(parents=True, exist_ok=True); skaparens.write_text('- 390 px tangentbord: 6 steg\ntangentbord: ok\n')
    sid_ = transkript([('Read', {'file_path': str(skaparens)}, 'innehållet')], '5a0e0d0c-0b0a-4908-8706-050403020125')
    assert kd.bedomt(sid_, SLUG, 'k01')['tillstand']['tangentbord'] == [], 'skaparens FORHAND.md är inte granskarens'
    # M69: bilder utanför kandidatens egna kataloger räknas inte som bedömda
    annan = kd.kdir(SLUG, 'k02') / 'varv' / 'start' / 'varv-01' / 'vy-390-forsta.png'
    annan.parent.mkdir(parents=True, exist_ok=True); annan.write_bytes(PNGHUVUD)
    sid_ = transkript([('Read', {'file_path': str(annan)}, ('bild',))], '5a0e0d0c-0b0a-4908-8706-050403020126')
    assert kd.bedomt(sid_, SLUG, 'k01')['bedomda_bredder'] == [], 'en annan kandidats bild räknas inte som k01:s'
    # M41–M42: bildprövningen godtar bara en hel PNG och följer aldrig en länk
    bilddir = Path(tempfile.mkdtemp(dir=TMP))
    (bilddir / 'gif.png').write_bytes(b'GIF89a' + b'\x00' * 30)
    (bilddir / 'hel.png').write_bytes(PNGHUVUD)
    (bilddir / 'lank.png').symlink_to(bilddir / 'hel.png')
    (bilddir / 'fel-signatur.png').write_bytes(b'GIF89a\r\n' + PNGHUVUD[8:])  # IHDR och mått, men inte PNG:s signatur (M41)
    (bilddir / 'utan-ihdr.png').write_bytes(PNGHUVUD[:12] + b'IDAT' + PNGHUVUD[16:])  # signaturen och mått, men inget IHDR
    assert forhandsvisa.giltig_bild(bilddir / 'hel.png') and not forhandsvisa.giltig_bild(bilddir / 'gif.png') and not forhandsvisa.giltig_bild(bilddir / 'lank.png')
    assert not forhandsvisa.giltig_bild(bilddir / 'fel-signatur.png') and not forhandsvisa.giltig_bild(bilddir / 'utan-ihdr.png')
    # M35: kundens bilder i src/assets/atelje/ ingår inte i kod-src: kritikens version är fotograferingens för samma kod
    atl = kd.ksajt(SLUG, 'k01') / 'src' / 'assets' / 'atelje'; atl.mkdir(parents=True, exist_ok=True)
    (atl / 'kundbild.jpg').write_bytes(b'\xff\xd8jpg')
    v_ = kd.projektets_version(SLUG, 'k01')
    kd.fotografera(SLUG, 'k01', skiss=True)
    assert kd.version(SLUG, 'k01') == v_, 'en kundbild i src/assets/atelje/ gav kritiken en annan version än fotograferingen'
    # M60: ett skäl i listan över sessioner utan block måste vara prövbart, inte en kort fras
    sess_, _, provkarta, provkod = session_utan_block_fixtur(karta)
    kort = re.sub(r'(?m)^(%s):\s*.*$' % re.escape(sess_), r'\1: för kort skäl här', provkarta, count=1)
    assert any(sess_ in f_ and 'prövbart skäl' in f_ for f_ in kompetens.sessionsfel(kort, fil=provkod)), kompetens.sessionsfel(kort, fil=provkod)


@fall('26 granskningen startar bara när skaparen hinner svara på den (GR-20261007-r103#K1, M53)')
def _granskningens_tid():
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
    # skaparen lämnar mer än granskningens frist men mindre än granskningen och ett svar
    mal_kvar = kd.FRIST_SKISSKRITIK + kd.SVAR_MIN // 2

    def skapa(p, s):
        Klocka.t = kd.FRIST_SKISS - kd.FOTO_RESERV - mal_kvar
        return None, None
    SVAR.clear()
    SVAR[lambda p, s: s is kd.SKISSKRITIK_SCHEMA] = lambda p, s: (dict(KRITIKSVAR), None)
    SVAR[lambda p, s: s is None] = skapa
    SESSIONER.clear()
    kd.satt_status(SLUG, 'k01', 'planerad', 'prov', ta_bort=('skisskritik',))
    try:
        kd.skissa(SLUG, 'k01')
    finally:
        kd.time = spara
    assert not [x for x in SESSIONER if x['schema'] is kd.SKISSKRITIK_SCHEMA], 'granskningen startade fast svaret inte hinner'
    st_ = kd.las_status(SLUG, 'k01').get('skisskritik') or {}
    assert st_.get('gjord') is False, st_


@fall('27 kompetensprovet går inte att lura med ett alias för atelje.session (GR-20261007-r103#K2)')
def _alias():
    kod_ = (KOPIA / 'kontroller' / 'kandidater.py').read_text(encoding='utf-8')
    assert kompetens.sessionsfel() == [], kompetens.sessionsfel()
    for tillagg in ('\n\ndef _ny_session(slug):\n    s = atelje.session\n    return s("x", LASVERKTYG, Path("/dev/null"))\n',
                    '\n\ndef _ny_session2(slug):\n    from atelje import session\n    return session("x", LASVERKTYG, Path("/dev/null"))\n',
                    '\n\ndef _ny_session3(slug):\n    return kor_med(atelje.session, slug)\n'):
        f_ = Path(tempfile.mkdtemp(dir=TMP)) / 'kandidater.py'
        f_.write_text(kod_ + tillagg, encoding='utf-8')
        fel_ = kompetens.sessionsfel(fil=f_)
        assert any('alias' in x for x in fel_), (tillagg, fel_)


print('skisskritikens prov: %d fall, %d föll' % (27, len(FEL)), file=sys.stderr)
sys.exit(1 if FEL else 0)
