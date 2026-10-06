#!/usr/bin/env python3
"""prov_observation.py — den passiva observatören (kontroller/observation.py; ägarens uppdrag 2026-10-06 om Claude Mods
och observation), syntetiskt och utan modell:

- sessionens start: prompten går fram oförändrad och exakt en gång, argumenten är desamma som förut utöver
  --session-id, och svaret är oförändrat; av (NWP_OBSERVATION=av) eller utan flaggan i claude --help: exakt som förut;
- observatörens fel blockerar aldrig: en förteckning som inte går att skriva, ett undantag i observatören, en saknad
  modul, en session som faller och en tidsgräns;
- inget nät och ingen dashboard behövs: sessionen startar med nätet avstängt i processen;
- tomma resultat, bilder, bildlänkar, för stora svar, fel, nekanden, hela läsningar och utdrag får rätt etikett, och
  känsliga strängar (nyckel, e-post, personnummer, bilddata, sökfraser, promptens text) syns aldrig i vyn eller
  förteckningen;
- två samtidiga sessioner blandas inte; läsningen är stegvis; latensen och lagringen mäts; inga extra modellanrop.

    .venv/bin/python kontroller/rokprov/revision/prov_observation.py <repo>

Allt skrivs i en temporär katalog (underlag och CLAUDE_CONFIG_DIR); det riktiga underlaget rörs inte.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-observation-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
KONFIG = TMP / 'claude-konfig'
(KONFIG / 'projects').mkdir(parents=True)
os.environ['CLAUDE_CONFIG_DIR'] = str(KONFIG)  # före importen: bildkedja.PROJEKT läses vid import
os.environ.pop('NWP_OBSERVATION', None)
sys.path.insert(0, str(ROOT / 'kontroller'))

import atelje  # noqa: E402
import bildkedja  # noqa: E402
import observation  # noqa: E402

assert bildkedja.PROJEKT == KONFIG / 'projects', bildkedja.PROJEKT
UNDERLAG = TMP / 'underlag'
observation.UNDERLAG = UNDERLAG
SLUG = 'obs-prov'
KAND = UNDERLAG / SLUG / 'atelje' / 'kandidater'
for k in ('k01', 'k02', 'k03'):
    (KAND / k).mkdir(parents=True)

HEMLIG = 'sk-ant-api03-HEMLIGTPROV'
EPOST = 'kund.person@exempel.se'
PNR = '19811218-9876'
BILDDATA = 'QUJDREVGSEVNTElHQklMRA'
FRAS = 'unik-sokfras-xyz'
PROMPTTEXT = 'PROMPTENS-EGEN-TEXT-SOM-ALDRIG-SYNS'
KANSLIGA = (HEMLIG, EPOST, PNR, BILDDATA, FRAS, PROMPTTEXT)

# --- den falska claude: registrerar varje anrop, skriver ett transkript under sitt --session-id och svarar som -p ---
BIN = TMP / 'bin'
BIN.mkdir()
LOGG = TMP / 'anrop'
LOGG.mkdir()
FALSK = r'''#!%(py)s
import json, os, sys, time, uuid
from pathlib import Path
logg = Path(%(logg)r)
a = sys.argv[1:]
if a[:1] == ['--help']:
    (logg / ('help-%%s' %% uuid.uuid4().hex)).write_text('help')
    print('Usage: claude [options]\n  -p, --print\n  --output-format\n' + ('' if os.environ.get('FAKE_UTAN_SID') else '  --session-id <uuid>  Use a specific session ID\n'))
    sys.exit(0)
prompt = sys.stdin.buffer.read()
(logg / ('p-%%s.json' %% uuid.uuid4().hex)).write_text(json.dumps({'argv': a, 'stdin': prompt.decode('utf-8')}))
sid = a[a.index('--session-id') + 1] if '--session-id' in a else None
if os.environ.get('FAKE_SOV'):
    time.sleep(float(os.environ['FAKE_SOV']))
if sid:
    scen = prompt.decode().split('SCENARIO:')[1].split()[0] if 'SCENARIO:' in prompt.decode() else 'tom'
    src = Path(os.environ['FAKE_SCENARIER']) / (scen + '.jsonl')
    d = Path(os.environ['CLAUDE_CONFIG_DIR']) / 'projects' / '-falsk-repo'
    d.mkdir(parents=True, exist_ok=True)
    (d / (sid + '.jsonl')).write_text(src.read_text() if src.is_file() else '')
if os.environ.get('FAKE_RC'):
    print(json.dumps({'type': 'result', 'is_error': True, 'subtype': 'error_during_execution', 'result': 'föll'}))
    sys.exit(int(os.environ['FAKE_RC']))
print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'klart', 'session_id': sid or 'utan-id', 'num_turns': 3}))
''' % {'py': sys.executable, 'logg': str(LOGG)}
(BIN / 'claude').write_text(FALSK)
(BIN / 'claude').chmod(0o755)
os.environ['PATH'] = '%s:%s' % (BIN, os.environ['PATH'])
assert atelje.claude() == str(BIN / 'claude'), atelje.claude()

# --- scenarierna: transkript i Claude Codes form, med känsliga strängar överallt där en mod eller logg kunde fånga dem ---
SCEN = TMP / 'scenarier'
SCEN.mkdir()
os.environ['FAKE_SCENARIER'] = str(SCEN)
T0 = '2026-10-06T10:00:%02d.000Z'


def rad(**r):
    return json.dumps(r, ensure_ascii=False)


def anrop(n, id_, namn, inn):
    return rad(type='assistant', timestamp=T0 % n, message={'role': 'assistant', 'model': 'claude-fable-5-1', 'content': [
        {'type': 'text', 'text': 'Jag tänker på %s och %s' % (HEMLIG, EPOST)}, {'type': 'tool_use', 'id': id_, 'name': namn, 'input': inn}],
        'usage': {'input_tokens': 1000 + n, 'cache_read_input_tokens': 50000, 'cache_creation_input_tokens': 2000, 'output_tokens': 10}})


def svar(n, id_, innehall, fel=None, tur=None, nekad=None):
    r = {'type': 'user', 'timestamp': T0 % n, 'message': {'role': 'user', 'content': [dict({'type': 'tool_result', 'tool_use_id': id_, 'content': innehall},
                                                                                             **({'is_error': fel} if fel is not None else {}))]}}
    if tur is not None:
        r['toolUseResult'] = tur
    if nekad:
        r['toolDenialKind'] = nekad
    return json.dumps(r, ensure_ascii=False)


REF = 'underlag/%s/referenser/paket-v01/tekt/01-start/vy-390-forsta.png' % SLUG
inledning = [rad(type='user', timestamp=T0 % 0, message={'role': 'user', 'content': PROMPTTEXT + ' ' + HEMLIG + ' ' + PNR}),
             rad(type='attachment', attachment={'type': 'skill_listing', 'isInitial': True, 'skillCount': 3, 'names': ['refero-design', 'impeccable', 'frontend-design'],
                                                'content': '- refero-design: ' + HEMLIG}),
             rad(type='attachment', attachment={'type': 'model', 'identity': {'modelId': 'claude-fable-5-1'}}),
             rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'addedNames': ['mcp__refero__refero_search_screens', 'mcp__mobbin__search_screens'],
                                                'pendingMcpServers': [], 'needsAuthMcpServers': ['figma'], 'failedMcpServers': []})]
k01 = inledning + [
    anrop(1, 'a1', 'Read', {'file_path': str(ROOT / '.claude/skills/refero-design/SKILL.md')}),
    svar(2, 'a1', 'innehåll ' + HEMLIG, tur={'type': 'text', 'file': {'filePath': 'x', 'content': HEMLIG, 'numLines': 120, 'startLine': 1, 'totalLines': 120}}),
    anrop(3, 'a2', 'Read', {'file_path': str(ROOT / REF)}),
    svar(4, 'a2', [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': BILDDATA}}], tur={'type': 'image', 'file': {'base64': BILDDATA}}),
    anrop(5, 'a3', 'Skill', {'skill': 'frontend-design', 'args': HEMLIG}),
    svar(6, 'a3', 'Launching skill: frontend-design ' + EPOST),
    anrop(7, 'a4', 'mcp__refero__refero_search_screens', {'query': FRAS + ' ' + EPOST}),
    svar(8, 'a4', [{'type': 'text', 'text': json.dumps({'pagination': {'count': 2}, 'records': [
        {'thumbnail_url': 'https://images.refero.design/s/a_thumb.jpg', 'note': HEMLIG}, {'thumbnail_url': 'https://images.refero.design/s/b_thumb.jpg'}]})}]),
]
k02 = inledning + [
    anrop(1, 'b1', 'Read', {'file_path': str(ROOT / '.claude/skills/impeccable/reference/layout.md'), 'limit': 50}),
    svar(2, 'b1', 'utdrag', tur={'type': 'text', 'file': {'filePath': 'x', 'content': 'x', 'numLines': 50, 'startLine': 1, 'totalLines': 200}}),
    anrop(3, 'b2', 'mcp__mobbin__search_screens', {'query': FRAS}),
    svar(4, 'b2', [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': BILDDATA}},
                   {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': BILDDATA}}, {'type': 'text', 'text': '[Image: source: /x/' + EPOST + ']'}]),
    anrop(5, 'b3', 'mcp__refero__refero_search_flows', {'query': FRAS}),
    svar(6, 'b3', [{'type': 'text', 'text': '{"pagination":{"count":0},"records":[]}'}]),
    anrop(7, 'b4', 'Bash', {'command': 'curl -H "Authorization: %s" https://x.se' % HEMLIG}),
    svar(8, 'b4', 'Permission to use Bash with command curl ' + HEMLIG + ' has been denied.', fel=True, nekad='permission-rule'),
    anrop(9, 'b5', 'mcp__refero__refero_get_style', {'id': FRAS}),
    svar(10, 'b5', 'Error: result (63,213 characters across 1 line) exceeds maximum allowed tokens. Output has been saved to /x/' + HEMLIG),
    anrop(11, 'b6', 'mcp__refero__refero_get_flow', {'id': FRAS}),
    svar(12, 'b6', 'MCP error -32603: ' + EPOST, fel=True),
    rad(type='system', subtype='compact_boundary', timestamp=T0 % 13, compactMetadata={'trigger': 'auto', 'preTokens': 190000}),
    anrop(14, 'b7', 'Read', {'file_path': str(ROOT / 'underlag' / SLUG / 'atelje' / 'metod' / 'METOD-skiss.md')}),
    svar(15, 'b7', 'metod', tur={'type': 'text', 'file': {'filePath': 'x', 'content': 'x', 'numLines': 40, 'startLine': 1, 'totalLines': 40}}),
    anrop(16, 'b8', 'mcp__mobbin__search_flows', {'query': FRAS}),  # utan svar: pågår eller avbröts
]
(SCEN / 'k01.jsonl').write_text('\n'.join(k01) + '\n')
(SCEN / 'k02.jsonl').write_text('\n'.join(k02) + '\n')
observation.ROOT = ROOT  # sökvägarna i transkripten är under det riktiga repot


def anropen():
    p = [json.loads(f.read_text()) for f in LOGG.glob('p-*.json')]
    return p, len(list(LOGG.glob('help-*')))


def nollstall():
    for f in LOGG.iterdir():
        f.unlink()


def post(sid):
    f = observation.katalog(SLUG) / (sid + '.json')
    return json.loads(f.read_text()) if f.is_file() else None


VERKTYG = ['Read', 'Glob', 'Grep']

# 1. vidarebefordran: oförändrad, exakt en gång; svaret oförändrat; --help en gång per process
nollstall()
prompt1 = 'SCENARIO:k01\n' + PROMPTTEXT + ' ' + HEMLIG + '\nåäö ✓\n'
ut1 = KAND / 'k01' / 'svar-skiss-1.json'
svar1 = atelje.session(prompt1, VERKTYG, ut1, max_turer=7, modell='claude-fable-5-1', effort='max', slug=SLUG)
p, h = anropen()
assert len(p) == 1 and h == 1, ('ett anrop och en hjälpfråga', len(p), h)
assert p[0]['stdin'] == prompt1, 'prompten oförändrad'
a = p[0]['argv']
i = a.index('--session-id')
sid1 = a[i + 1]
assert i == 1 and a[0] == '-p', a[:3]
vantat = atelje.session_args(VERKTYG, None, 7, 'claude-fable-5-1', 'max', (), SLUG)[1:]
assert a[:i] + a[i + 2:] == vantat, 'argumenten är desamma som förut utöver --session-id'
assert svar1 == json.loads(ut1.read_text()) and svar1['session_id'] == sid1 and svar1['result'] == 'klart', svar1
po = post(sid1)
assert set(po) == {'session_id', 'roll', 'kandidat', 'svar', 'start', 'modell', 'pid', 'slut', 'utfall'}, sorted(po)
assert po['roll'] == 'skiss-1' and po['kandidat'] == 'k01' and po['svar'] == 'svar-skiss-1.json' and po['utfall'] == 'avslutad, kod 0' and po['slut'], po
assert bildkedja.transkript(sid1), 'transkriptet hittas med sessionens id'
# en andra session i samma process frågar inte claude --help igen
nollstall()
atelje.session('SCENARIO:tom\nx', VERKTYG, KAND / 'k03' / 'svar-plan.json', max_turer=7, slug=SLUG)
p, h = anropen()
assert len(p) == 1 and h == 0, ('hjälpfrågan cachas', len(p), h)

# 2. av: exakt som förut (inget id, ingen förteckning, ingen hjälpfråga)
nollstall()
fore = set(observation.katalog(SLUG).glob('*.json'))
os.environ['NWP_OBSERVATION'] = 'av'
atelje.session('SCENARIO:k01\nx', VERKTYG, KAND / 'k03' / 'svar-av.json', max_turer=7, slug=SLUG)
del os.environ['NWP_OBSERVATION']
p, h = anropen()
assert p[0]['argv'] == atelje.session_args(VERKTYG, None, 7, None, None, (), SLUG)[1:] and h == 0, 'av: argumenten som förut'
assert set(observation.katalog(SLUG).glob('*.json')) == fore, 'av: ingen förteckning'
# claude utan --session-id i hjälpen: som förut (en ny process börjar utan cache)
nollstall()
observation._HJALP.clear()
os.environ['FAKE_UTAN_SID'] = '1'
atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-utan-flagga.json', max_turer=7, slug=SLUG)
del os.environ['FAKE_UTAN_SID']
p, h = anropen()
assert '--session-id' not in p[0]['argv'] and h == 1, 'utan flaggan i hjälpen: ingen flagga'
assert set(observation.katalog(SLUG).glob('*.json')) == fore
observation._HJALP.clear()

# 3. observatörens fel blockerar aldrig
nollstall()
orig_anmal = observation.anmal
observation.anmal = lambda *a_, **k_: (_ for _ in ()).throw(OSError('disken full'))
s3 = atelje.session('SCENARIO:tom\nx', VERKTYG, KAND / 'k03' / 'svar-fel-anmal.json', max_turer=7, slug=SLUG)
observation.anmal = orig_anmal
assert s3['result'] == 'klart', 'ett undantag i observatören stoppar inte sessionen'
assert post(anropen()[0][0]['argv'][2]) is None, 'en post som aldrig skrevs skapas inte vid sessionens slut'
modul = atelje.observation
atelje.observation = None
s3b = atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-utan-modul.json', max_turer=7, slug=SLUG)
atelje.observation = modul
assert s3b['session_id'] == 'utan-id', 'utan modulen: ingen flagga, sessionen går'
annan = 'obs-prov-fil'
(UNDERLAG / annan / 'atelje').mkdir(parents=True)
(UNDERLAG / annan / 'atelje' / 'sessioner').write_text('en fil där katalogen skulle ligga')
s3c = atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-ej-skrivbar.json', max_turer=7, slug=annan)
assert s3c['result'] == 'klart', 'en förteckning som inte går att skriva stoppar inte sessionen'
# en session som faller och en tidsgräns: samma fel som förut, och förteckningen säger utfallet
nollstall()
os.environ['FAKE_RC'] = '1'
try:
    atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-faller.json', max_turer=7, slug=SLUG)
    raise AssertionError('sessionen skulle falla')
except RuntimeError as e:
    assert 'sessionen föll (kod 1' in str(e), e
del os.environ['FAKE_RC']
sid_f = anropen()[0][0]['argv'][2]
assert post(sid_f)['utfall'] == 'avslutad, kod 1' and post(sid_f)['slut'], post(sid_f)
nollstall()
os.environ['FAKE_SOV'] = '20'
t0 = time.time()
try:
    atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-tidsgrans.json', max_turer=7, frist=2, slug=SLUG)
    raise AssertionError('tidsgränsen skulle nås')
except subprocess.TimeoutExpired:
    pass
del os.environ['FAKE_SOV']
assert time.time() - t0 < 15, 'tidsgränsen håller'
sid_t = anropen()[0][0]['argv'][2]
assert post(sid_t)['utfall'] == 'tidsgräns', post(sid_t)

# 4. inget nät och ingen dashboard behövs: sessionen startar med nätet avstängt i processen
riktig = socket.socket.connect
socket.socket.connect = lambda *a_, **k_: (_ for _ in ()).throw(OSError('nätet avstängt i provet'))
try:
    s4 = atelje.session('SCENARIO:tom\nx', VERKTYG, KAND / 'k03' / 'svar-utan-nat.json', max_turer=7, slug=SLUG)
finally:
    socket.socket.connect = riktig
assert s4['result'] == 'klart'
kalla = (ROOT / 'kontroller' / 'observation.py').read_text()
assert not any(x in kalla for x in ('urllib', 'socket', 'http.client', 'requests', 'mcp__refero__refero_search')), 'observatören har inga nätanrop'

# 5. två samtidiga sessioner blandas inte
nollstall()
res = {}


def kor(kid, scen):
    res[kid] = atelje.session('SCENARIO:%s\n%s' % (scen, PROMPTTEXT), VERKTYG, KAND / kid / 'svar-skiss-1.json', max_turer=7, slug=SLUG)


tr = [threading.Thread(target=kor, args=('k01', 'k01')), threading.Thread(target=kor, args=('k02', 'k02'))]
[t.start() for t in tr]
[t.join() for t in tr]
sid_a, sid_b = res['k01']['session_id'], res['k02']['session_id']
assert sid_a != sid_b and post(sid_a)['kandidat'] == 'k01' and post(sid_b)['kandidat'] == 'k02'
ov = observation.oversikt(SLUG)
per = {s['session_id']: s for s in ov['sessioner']}
oa, ob = per[sid_a]['observation'], per[sid_b]['observation']
assert [x['skill'] for x in oa['skillfiler']] == ['refero-design'] and oa['skillfiler'][0]['skillmd'] and oa['skillfiler'][0]['utfall'] == 'fil läst (hel)'
assert [x['skill'] for x in ob['skillfiler']] == ['impeccable'] and not ob['skillfiler'][0]['skillmd']
assert ob['skillfiler'][0]['utfall'] == 'fil läst (utdrag)' and ob['skillfiler'][0]['rader'] == [1, 50, 200], ob['skillfiler']
assert oa['referensfiler'] == [{'fil': REF, 'utfall': 'bild läst', 'tid': T0 % 3}] and not ob['referensfiler'], oa['referensfiler']
assert oa['skills_laddade'] == [{'skill': 'frontend-design', 'utfall': 'skill laddad via skillsystemet', 'tid': T0 % 5}] and not ob['skills_laddade']

# 6. etiketterna: tomt, bilder, bildlänkar, för stort, fel, nekat, inget svar; kontext, komprimering, skillista, MCP
assert oa['mcp'] == [{'tjanst': 'refero', 'verktyg': 'refero_search_screens', 'utfall': 'anrop lyckades', 'tid': T0 % 7, 'traffar': 2, 'bildlankar': 2}], oa['mcp']
mb = {m['verktyg']: m for m in ob['mcp']}
assert mb['search_screens']['utfall'] == 'bild returnerad' and mb['search_screens']['bilder'] == 2
assert mb['refero_search_flows']['utfall'] == 'tomt resultat'
assert mb['refero_get_style']['utfall'] == 'svaret för stort, sparat till fil'
assert mb['refero_get_flow']['utfall'] == 'fel'
assert mb['search_flows']['utfall'] == 'inget svar observerat'
assert ob['nekade'] == 1 and ob['verktyg']['Bash'] == {'nekat': 1}, ob['verktyg']
assert ob['metodutdrag'] == [{'fil': 'underlag/%s/atelje/metod/METOD-skiss.md' % SLUG, 'utfall': 'fil läst (hel)', 'tid': T0 % 14}], ob['metodutdrag']
assert ob['komprimeringar'] == [{'tid': T0 % 13, 'utlost': 'auto', 'fore': 190000}]
assert oa['kontext'] == {'tokens': 53007, 'tid': T0 % 7, 'uppskattning': True}, oa['kontext']
assert oa['skills_erbjudna'] == 3 and oa['modell'] == 'claude-fable-5-1'
assert oa['mcp_lage'] == {'refero': 'ansluten', 'mobbin': 'ansluten', 'figma': 'kräver inloggning'}, oa['mcp_lage']
assert oa['senaste_handelse'] == T0 % 8 and not per[sid_a]['pagar'] and per[sid_a]['slut']

# 7. känsliga strängar syns aldrig, varken i vyn eller i förteckningen
vy = json.dumps(ov, ensure_ascii=False)
forteckning = ''.join(f.read_text() for f in observation.katalog(SLUG).glob('*.json'))
FALT = {'session_id', 'roll', 'kandidat', 'svar', 'start', 'modell', 'pid', 'slut', 'utfall'}
assert all(set(json.loads(f.read_text())) <= FALT for f in observation.katalog(SLUG).glob('*.json')), 'bara de valda fälten'
for x in KANSLIGA:
    assert x not in vy, ('i vyn', x)
    assert x not in forteckning, ('i förteckningen', x)

# 8. stegvis läsning: bara nya rader tolkas, och en halv rad väntar
f_a = bildkedja.transkript(sid_a)
la = observation.las_session(f_a)
pos = la['pos']
with open(f_a, 'a') as f:
    f.write(anrop(30, 'c1', 'mcp__mobbin__search_sections', {'query': FRAS}) + '\n' + svar(31, 'c1', [{'type': 'text', 'text': '[]'}])[:40])
la = observation.las_session(f_a)
assert 'c1' in la['anrop'] and 'c1' not in la['svar'] and la['pos'] > pos, 'den hela raden lästes, den halva väntar'
with open(f_a, 'a') as f:
    f.write(svar(31, 'c1', [{'type': 'text', 'text': '[]'}])[40:] + '\n')
la = observation.las_session(f_a)
assert la['svar']['c1']['utfall'] == 'tomt resultat', la['svar'].get('c1')

# 9. inga modellanrop och inga processer vid läsningen; och fel i en del gör bara den delen ofullständig
nollstall()
rp, rr = subprocess.Popen, subprocess.run
subprocess.Popen = subprocess.run = lambda *a_, **k_: (_ for _ in ()).throw(AssertionError('observatören startade en process'))
try:
    for _ in range(3):
        observation.oversikt(SLUG)
finally:
    subprocess.Popen, subprocess.run = rp, rr
assert anropen() == ([], 0), 'läsningen gör inga anrop'
(observation.katalog(SLUG) / 'trasig.json').write_text('{inte json')
(UNDERLAG / SLUG / 'atelje' / 'KANDIDATPLAN.json').write_text('{"kandidater": "fel form"}')
ov2 = observation.oversikt(SLUG)
assert len(ov2['sessioner']) == len(ov['sessioner']) and ov2['referenser']['kandidater'] == {}, 'trasiga filer hoppas över'
orig_p = observation.prototyper
observation.prototyper = lambda s_: 1 / 0
ov3 = observation.oversikt(SLUG)
observation.prototyper = orig_p
assert 'ZeroDivisionError' in ov3['prototyper']['ofullstandig'] and ov3['sessioner'], 'en del ofullständig, resten visas'

# 10. tjänstesessionernas strömmade loggar (Refero och Mobbin) läses med samma etiketter
tjk = UNDERLAG / SLUG / 'referenser' / 'tjanster' / 'mobbin'
tjk.mkdir(parents=True)
(tjk / 'session-2026-10-06T100000Z.jsonl').write_text('\n'.join([
    rad(type='system', subtype='init', model='claude-sonnet-5-5', skills=['a', 'b'], mcp_servers=[{'name': 'mobbin', 'status': 'connected'}], cwd=str(ROOT)),
    rad(type='assistant', timestamp=T0 % 1, message={'content': [{'type': 'tool_use', 'id': 't1', 'name': 'mcp__mobbin__search_screens', 'input': {'query': FRAS}}]}),
    rad(type='user', timestamp=T0 % 2, message={'content': [{'type': 'tool_result', 'tool_use_id': 't1', 'content': [{'type': 'image', 'source': {'data': BILDDATA}}]}]},
        tool_use_result={'content': [], 'structuredContent': {'q': FRAS}}),
    rad(type='result', subtype='success', is_error=False, num_turns=2, timestamp=T0 % 3)]) + '\n')
tj = observation.tjanstesessioner(SLUG)
assert len(tj) == 1 and tj[0]['tjanst'] == 'mobbin' and tj[0]['del'] == 'tjanster', tj
o_t = tj[0]['observation']
assert o_t['mcp_lage'] == {'mobbin': 'connected'} and o_t['skills_erbjudna'] == 2 and o_t['slut']['utfall'] == 'success'
assert o_t['mcp'][0]['utfall'] == 'bild returnerad' and o_t['mcp'][0]['bilder'] == 1
assert not any(x in json.dumps(tj, ensure_ascii=False) for x in KANSLIGA)

# 11. dashboarden: senaste förhandsvarvets första vy får visas, inget annat ur varvet
sys.path.insert(0, str(ROOT / 'dashboard'))
import server as dash  # noqa: E402
v_ = 'underlag/x-y/atelje/kandidater/k01/varv/start/varv-03/vy-%s'
assert all(dash.KAND_VARV.match(v_ % b) for b in ('390-forsta.png', '1280-forsta.png', '1440-forsta.png'))
assert not any(dash.KAND_VARV.match(v_ % b) for b in ('390-hela.png', '390-extrakt.json', '390-aria.txt', '390-spar.zip', '768-forsta.png'))
assert not dash.KAND_VARV.match('underlag/x-y/atelje/kandidater/k01/varv/start/varv-03/INSPEKTION.md')

# 12. mätningen: latens på ett stort transkript (första läsningen och en stegvis), och lagringen per session
stor = KONFIG / 'projects' / '-falsk-repo' / '00000000-0000-4000-8000-000000000001.jsonl'
with open(stor, 'w') as f:
    for n in range(1000):
        f.write(anrop(n % 60, 'x%d' % n, 'Read', {'file_path': str(ROOT / ('underlag/%s/referenser/p/%d.png' % (SLUG, n)))}) + '\n')
        f.write(svar(n % 60, 'x%d' % n, [{'type': 'image', 'source': {'data': 'A' * 20000}}], tur={'type': 'image', 'file': {'base64': 'A' * 20000}}) + '\n')
storlek = stor.stat().st_size
t0 = time.perf_counter()
observation.las_session(stor)
forsta = time.perf_counter() - t0
with open(stor, 'a') as f:
    f.write(anrop(1, 'y1', 'Read', {'file_path': '/x'}) + '\n')
t0 = time.perf_counter()
observation.las_session(stor)
steg = time.perf_counter() - t0
poster = list(observation.katalog(SLUG).glob('*-*-*-*-*.json'))
per_post = max(f.stat().st_size for f in poster)
print('mätning: transkript %.1f MB, första läsningen %.0f ms, stegvis %.2f ms; förteckningen %d byte per session (högst), %d sessioner'
      % (storlek / 1e6, forsta * 1000, steg * 1000, per_post, len(poster)), file=sys.stderr)
assert forsta < 10 and steg < 0.5, (forsta, steg)
assert per_post < 600, per_post

print('observationens prov: alla gröna', file=sys.stderr)
