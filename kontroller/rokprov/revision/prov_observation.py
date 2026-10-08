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

import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_observation')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
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
    time.sleep(float(os.environ.get('FAKE_HJALP_SOV') or 0))
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
# stoppet går alltid igenom: ett stopp under frågan till claude --help, och ett stopp som kom medan den pågick
nollstall()
orig_ff = observation.flaggan_finns
observation.flaggan_finns = lambda *a_, **k_: (_ for _ in ()).throw(atelje.Stoppad('prov'))
try:
    atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-stopp-1.json', max_turer=7, slug=SLUG)
    raise AssertionError('stoppet skulle gå igenom')
except atelje.Stoppad:
    pass
observation.flaggan_finns = lambda *a_, **k_: (atelje.STOPP.set(), True)[1]
try:
    atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-stopp-2.json', max_turer=7, slug=SLUG)
    raise AssertionError('ingen ny session efter stoppet')
except atelje.Stoppad:
    pass
finally:
    atelje.STOPP.clear()
    observation.flaggan_finns = orig_ff
assert anropen()[0] == [], 'ingen session startade efter stoppen'
rr_ = subprocess.run
observation._HJALP.clear()
subprocess.run = lambda *a_, **k_: (_ for _ in ()).throw(atelje.Stoppad('prov'))
try:
    observation.flaggan_finns(str(BIN / 'claude'))
    raise AssertionError('flaggan_finns fångar bara programmets egna fel')
except atelje.Stoppad:
    pass
finally:
    subprocess.run = rr_


def stopp_under_anmalan(*a_, **k_):  # som arbetarens signalhanterare: sessionerna avslutas, sedan Stoppad
    atelje.stoppa_sessioner()
    raise atelje.Stoppad('prov')


observation._HJALP.clear()
observation.anmal = stopp_under_anmalan
try:
    atelje.session('SCENARIO:tom\nx', VERKTYG, KAND / 'k03' / 'svar-stopp-3.json', max_turer=7, slug=SLUG)
    raise AssertionError('stoppet under anmälan skulle gå igenom')
except atelje.Stoppad:
    pass
finally:
    observation.anmal = orig_anmal
    atelje.STOPP.clear()
assert not atelje.AKTIVA, ('sessionen som startade städades', atelje.AKTIVA)
# frågan till claude --help når sin tidsgräns: sessionen startar som förut, och svaret prövas igen först efter en stund
nollstall()
observation._HJALP.clear()
observation.HJALP_FRIST = 1
os.environ['FAKE_HJALP_SOV'] = '6'
t0 = time.time()
s3d = atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-hjalp-tidsgrans.json', max_turer=7, slug=SLUG)
del os.environ['FAKE_HJALP_SOV']
assert s3d['session_id'] == 'utan-id' and time.time() - t0 < 5, 'utan svar inom tidsgränsen: som förut'
atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-hjalp-cache.json', max_turer=7, slug=SLUG)
assert anropen()[1] == 1 and '--session-id' not in anropen()[0][-1]['argv'], 'felet prövas inte om direkt'
svar_, nar_ = observation._HJALP[str(BIN / 'claude')]
assert svar_ is False and nar_ is not None, 'ett fel cachas med sin tid, så att frågan prövas igen'
observation._HJALP[str(BIN / 'claude')] = (False, nar_ - observation.HJALP_OMPROVA_S - 1)  # tiden har gått
s3e = atelje.session('x', VERKTYG, KAND / 'k03' / 'svar-hjalp-igen.json', max_turer=7, slug=SLUG)
assert anropen()[1] == 2 and s3e['session_id'] != 'utan-id', 'efter en stund prövas frågan igen'
observation.HJALP_FRIST = 15
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

# 9. inga modellanrop och inga processer vid läsningen av avslutade sessioner; en levande pid som inte är en
#    claude-session pågår inte (bara ps frågas); fel i en del gör bara den delen ofullständig
nollstall()
startade = []
rp, rr = subprocess.Popen, subprocess.run


class Raknad(rp):
    def __init__(self, args, *a_, **k_):
        startade.append([str(x) for x in (args if isinstance(args, (list, tuple)) else [args])])
        super().__init__(args, *a_, **k_)


def rakna():
    subprocess.Popen = Raknad
    subprocess.run = lambda args, *a_, **k_: (startade.append([str(x) for x in args]), rr(args, *a_, **k_))[1]


def aterstall():
    subprocess.Popen, subprocess.run = rp, rr


rakna()
try:
    for _ in range(3):
        observation.oversikt(SLUG)
finally:
    aterstall()
assert startade == [] and anropen() == ([], 0), ('läsningen startar inga processer och gör inga anrop', startade)
sid_9 = '00000000-0000-4000-8000-0000000000aa'
observation._skriv(observation.katalog(SLUG) / (sid_9 + '.json'), {'session_id': sid_9, 'roll': 'skiss-9', 'kandidat': 'k03', 'svar': 'svar-skiss-9.json',
                                                                    'start': observation.nu(), 'modell': 'm', 'pid': os.getpid(), 'slut': None, 'utfall': None})
rakna()
try:
    ov_9 = observation.oversikt(SLUG)
finally:
    aterstall()
assert {s_['session_id']: s_ for s_ in ov_9['sessioner']}[sid_9]['pagar'] is False, 'en levande pid som inte är en claude-session'
assert startade and all(c[0] == 'ps' for c in startade), startade
(observation.katalog(SLUG) / (sid_9 + '.json')).unlink()
(observation.katalog(SLUG) / 'trasig.json').write_text('{inte json')
(observation.katalog(SLUG) / 'fel-form.json').write_text('{"session_id": "inte-ett-id"}')
(UNDERLAG / SLUG / 'atelje' / 'KANDIDATPLAN.json').write_text('{"kandidater": "fel form"}')
ov2 = observation.oversikt(SLUG)
trasiga = sorted(s_['ofullstandig'] for s_ in ov2['sessioner'] if s_.get('ofullstandig'))
assert len(ov2['sessioner']) == len(ov['sessioner']) + 2 and trasiga == ['förteckningsposten fel-form.json har oväntad form',
                                                                       'förteckningsposten trasig.json kunde inte läsas: JSONDecodeError'], trasiga
assert ov2['referenser']['kandidater'] == {}, 'en plan med fel form ger inga kandidater'
(observation.katalog(SLUG) / 'trasig.json').unlink(); (observation.katalog(SLUG) / 'fel-form.json').unlink()
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
assert o_t['mcp_lage'] == {'mobbin': 'ansluten'} and o_t['skills_erbjudna'] == 2 and o_t['slut']['utfall'] == 'success'
assert o_t['mcp'][0]['utfall'] == 'bild returnerad' and o_t['mcp'][0]['bilder'] == 1
assert not any(x in json.dumps(tj, ensure_ascii=False) for x in KANSLIGA)

# 11. dashboarden: senaste förhandsvarvets första vy får visas, inget annat ur varvet
sys.path.insert(0, str(ROOT / 'dashboard'))
import server as dash  # noqa: E402
v_ = 'underlag/x-y/atelje/kandidater/k01/varv/start/varv-03/vy-%s'
assert all(dash.KAND_VARV.match(v_ % b) for b in ('390-forsta.png', '1280-forsta.png', '1440-forsta.png'))
assert not any(dash.KAND_VARV.match(v_ % b) for b in ('390-hela.png', '390-extrakt.json', '390-aria.txt', '390-spar.zip', '768-forsta.png'))
assert not dash.KAND_VARV.match('underlag/x-y/atelje/kandidater/k01/varv/start/varv-03/INSPEKTION.md')

# 13. nekanden utan toolDenialKind (strömmade loggar): dontAsk, en PreToolUse-krok, en deny-regel; ett fel som inte
#     är ett nekande; bildlänkar räknas bara när de pekar på bilder
tjk2 = UNDERLAG / SLUG / 'referenser' / 'uppdrag' / 'refero'
tjk2.mkdir(parents=True)


def strom(*rader_):
    return '\n'.join(rader_) + '\n'


(tjk2 / 'session-2026-10-06T110000Z.jsonl').write_text(strom(
    rad(type='system', subtype='init', model='claude-sonnet-5-5', skills=[], mcp_servers=[{'name': 'refero', 'status': 'connected'}]),
    rad(type='assistant', timestamp=T0 % 1, message={'content': [
        {'type': 'tool_use', 'id': 'n1', 'name': 'mcp__refero__refero_search_screens', 'input': {'query': FRAS}},
        {'type': 'tool_use', 'id': 'n2', 'name': 'mcp__refero__refero_search_flows', 'input': {'query': FRAS}},
        {'type': 'tool_use', 'id': 'n3', 'name': 'Read', 'input': {'file_path': '/x/neka.md'}},
        {'type': 'tool_use', 'id': 'n4', 'name': 'mcp__refero__refero_search_sites', 'input': {'query': FRAS}},
        {'type': 'tool_use', 'id': 'n5', 'name': 'mcp__refero__refero_get_flow', 'input': {'id': 1}},
        {'type': 'tool_use', 'id': 'n6', 'name': 'mcp__mobbin__search_screens', 'input': {'query': FRAS, 'mode': 'x'}},
        {'type': 'tool_use', 'id': 'n7', 'name': 'mcp__mobbin__search_flows', 'input': {'query': FRAS}}]}),
    rad(type='user', timestamp=T0 % 2, message={'content': [
        {'type': 'tool_result', 'tool_use_id': 'n1', 'is_error': True, 'content': "Claude requested permissions to use mcp__refero__refero_search_screens, but you haven't granted it yet."},
        {'type': 'tool_result', 'tool_use_id': 'n2', 'is_error': True, 'content': 'PreToolUse:mcp__refero__refero_search_flows hook error: [x]: blockerat ' + EPOST},
        {'type': 'tool_result', 'tool_use_id': 'n3', 'is_error': True, 'content': '<tool_use_error>File is covered by a Read deny rule in your permission settings and cannot be written.</tool_use_error>'},
        {'type': 'tool_result', 'tool_use_id': 'n4', 'content': [{'type': 'text', 'text': json.dumps({'records': [
            {'url': 'https://refero.design/flows/7542', 'site': 'https://www.example.com/', 'thumbnail_url': 'https://images.refero.design/a.webp'}]})}]},
        {'type': 'tool_result', 'tool_use_id': 'n5', 'is_error': True, 'content': 'MCP error -32603: internt fel'},
        {'type': 'tool_result', 'tool_use_id': 'n6', 'content': [{'type': 'text', 'text': 'Error: mode must be "standard" or "extended"'}]},
        {'type': 'tool_result', 'tool_use_id': 'n7', 'content': [{'type': 'text', 'text': 'No screens matched your query.'}]}]})))
o13 = [t_ for t_ in observation.tjanstesessioner(SLUG) if '/uppdrag/refero/' in t_['logg']][0]['observation']
m13 = {m['verktyg']: m for m in o13['mcp']}
assert m13['refero_search_screens']['utfall'] == 'nekat' and m13['refero_search_flows']['utfall'] == 'nekat', m13
assert o13['verktyg']['Read'] == {'nekat': 1} and o13['nekade'] == 3, o13['verktyg']
assert m13['refero_get_flow']['utfall'] == 'fel'
assert m13['refero_search_sites']['utfall'] == 'anrop lyckades' and m13['refero_search_sites']['bildlankar'] == 1 and m13['refero_search_sites']['traffar'] == 1, m13
# en feltext utan felflagga och ett svar som säger att inget matchade är inte lyckade anrop med innehåll (GR-20261008-r117-claude#C6)
assert m13['search_screens']['utfall'] == 'fel' and m13['search_flows']['utfall'] == 'tomt resultat', m13
f14 = TMP / 't14.jsonl'
f14.write_text(strom(anrop(1, 'd1', 'Bash', {'command': 'ls'}), svar(2, 'd1', 'x', fel=True, nekad='permission-rule')))
s14 = observation.sammanfattning(f14)
assert s14['verktyg'] == {'Bash': {'nekat': 1}} and s14['nekade'] == 1, 'typfältet räcker för ett nekande'
# Claude Codes egna nekandetexter (också "Permission to read") är nekanden; en tjänsts egna fel med liknande ord är fel
f14b = TMP / 't14b.jsonl'
texter14 = [('Permission to read /x has been denied.', 'nekat'), ('Error: permission to access this collection (403)', 'fel'),
            ('Request denied by upstream rate limiter', 'fel'), ('webhook error while fetching', 'fel')]
f14b.write_text(strom(*[x for i, (txt, _) in enumerate(texter14) for x in (anrop(1, 'q%d' % i, 'mcp__refero__refero_search_sites', {'q': FRAS}),
                                                                           svar(2, 'q%d' % i, txt, fel=True))]))
s14b = observation.sammanfattning(f14b)
assert [m['utfall'] for m in s14b['mcp']] == [v for _, v in texter14], s14b['mcp']

# 14. en rad med oväntad form hoppas över och räknas, en gång; läsningen går vidare och räknar inget dubbelt
f15 = TMP / 't15.jsonl'
f15.write_text(strom(anrop(1, 'e1', 'Read', {'file_path': '/a'}), anrop(2, 'e2', 'Bash', {'command': 'x'}),
                     rad(type='system', subtype='compact_boundary', timestamp=T0 % 3, compactMetadata='inte en dict'),
                     rad(type='attachment', attachment={'type': 'model', 'identity': 'sträng'}),
                     rad(type='assistant', timestamp=T0 % 4, message={'model': 'm', 'usage': {'input_tokens': 'abc'}, 'content': [{'type': 'tool_use', 'id': 'e3', 'name': 'Grep', 'input': {}}]}),
                     rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'addedNames': 'mcp__x__y'})))
orig_anrop = observation._anrop
observation._anrop = lambda c, t: (_ for _ in ()).throw(KeyError('oväntad form')) if c.get('name') == 'Bash' else orig_anrop(c, t)
try:
    for _ in range(3):
        l15 = observation.las_session(f15)
finally:
    observation._anrop = orig_anrop
assert l15['pos'] == f15.stat().st_size and l15['oforstadda'] == 1, (l15['pos'], l15['oforstadda'])
assert set(l15['anrop']) == {'e1', 'e3'} and len(l15['komprimeringar']) == 1 and l15['mcp'] == {}, l15
assert l15['kontext'] == {'tokens': 53002, 'tid': T0 % 2}, 'användning som inte är tal ändrar inte den senaste uppskattningen'

# 15. en utbytt fil (ny inode) och en avkortad fil läses från början
f16 = TMP / 't16.jsonl'
f16.write_text(strom(anrop(1, 'g1', 'Grep', {}), anrop(2, 'g2', 'Grep', {})))
assert set(observation.las_session(f16)['anrop']) == {'g1', 'g2'}
ny16 = TMP / 't16-ny.jsonl'
ny16.write_text(strom(anrop(1, 'h1', 'Glob', {}), anrop(2, 'h2', 'Glob', {}), anrop(3, 'h3', 'Glob', {})))  # större än läspositionen
os.replace(ny16, f16)
assert set(observation.las_session(f16)['anrop']) == {'h1', 'h2', 'h3'}, 'en utbytt fil läses från början'
f16.write_text(strom(rad(type='assistant', message={'content': [{'type': 'tool_use', 'id': 'j1', 'name': 'X', 'input': {}}]})))
assert set(observation.las_session(f16)['anrop']) == {'j1'}, 'en avkortad fil läses från början'

# 16. samtidiga läsningar (dashboardens trådar) medan transkriptet växer: inga fel, inget ofullständigt, rätt antal
sid_17 = '00000000-0000-4000-8000-0000000000bb'
f17 = KONFIG / 'projects' / '-falsk-repo' / (sid_17 + '.jsonl')
f17.write_text('')
observation._skriv(observation.katalog(SLUG) / (sid_17 + '.json'), {'session_id': sid_17, 'roll': 'skiss-8', 'kandidat': 'k03', 'svar': 'svar-skiss-8.json',
                                                                     'start': observation.nu(), 'modell': 'm', 'pid': None, 'slut': observation.nu(), 'utfall': 'avslutad, kod 0'})
fel17 = []


def lasare():
    for _ in range(60):
        try:
            o_ = observation.oversikt(SLUG)
            json.dumps(o_)
            if not isinstance(o_['sessioner'], list) or any(s_.get('ofullstandig') or (s_.get('observation') or {}).get('lasfel') for s_ in o_['sessioner']):
                fel17.append('ofullständig: %s' % str(o_['sessioner'])[:200])
        except Exception as e:  # noqa: BLE001
            fel17.append(repr(e))


rader17 = []  # varje hel rad i f17 tolkas exakt en gång, också med fyra samtidiga läsare (låset; granskningen av r92, KAN 4)
orig_rad17 = observation._rad


def raknad_rad(lage, rad_):
    if lage['id'] == ident17:
        rader17.append(1)
        time.sleep(0.0002)  # vidgar fönstret: utan låset tolkar två läsare samma rader
    return orig_rad17(lage, rad_)


def skrivare():
    with open(f17, 'a') as f:
        for n in range(600):
            f.write(anrop(n % 60, 'w%d' % n, 'Read', {'file_path': str(ROOT / ('underlag/%s/referenser/p/%d.png' % (SLUG, n)))}) + '\n')
            f.write(svar(n % 60, 'w%d' % n, 'x', tur={'type': 'text', 'file': {'numLines': 1, 'startLine': 1, 'totalLines': 1}}) + '\n')
            f.flush()


tr17 = [threading.Thread(target=lasare) for _ in range(4)] + [threading.Thread(target=skrivare)]
byte_ = sys.getswitchinterval()
ident17 = (f17.stat().st_dev, f17.stat().st_ino)
sys.setswitchinterval(1e-6)  # täta trådbyten: en läsning utan lås överlappar då en annan trådens tolkning
observation._rad = raknad_rad
try:
    [t.start() for t in tr17]
    [t.join() for t in tr17]
    o17 = {s_['session_id']: s_ for s_ in observation.oversikt(SLUG)['sessioner']}[sid_17]['observation']
finally:
    sys.setswitchinterval(byte_)
    observation._rad = orig_rad17
assert not fel17, fel17[:3]
assert len(o17['referensfiler']) == 600
assert len(rader17) == 1200, ('varje rad tolkas en gång', len(rader17))

# 17. Read utan omfång i svaret, en oförändrad fil, och en MCP-server vars verktyg togs bort
f18 = TMP / 't18.jsonl'
f18.write_text(strom(anrop(1, 'k1', 'Read', {'file_path': str(ROOT / '.claude/skills/x/SKILL.md')}),
                     svar(2, 'k1', 'x', tur={'type': 'text', 'file': {'filePath': 'x', 'content': 'x'}}),
                     anrop(3, 'k2', 'Read', {'file_path': str(ROOT / '.claude/skills/x/SKILL.md')}),
                     svar(4, 'k2', 'File unchanged since last read', tur={'type': 'file_unchanged', 'file': {'filePath': 'x'}}),
                     rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'addedNames': ['mcp__refero__a', 'mcp__refero__b', 'mcp__mobbin__c']}),
                     rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'removedNames': ['mcp__refero__a', 'mcp__refero__b']})))
s18 = observation.sammanfattning(f18)
assert [x['utfall'] for x in s18['skillfiler']] == ['fil läst (omfång inte observerat)', 'oförändrad sedan förra läsningen'], s18['skillfiler']
assert s18['mcp_lage'] == {'refero': 'verktygen borttagna', 'mobbin': 'ansluten'}, s18['mcp_lage']

# 18. sessionens sida: skaparens arbete, granskningen och körningens gemensamma steg hålls isär
roller = ('skiss-1', 'skiss-1-granskning', 'skapa-2', 'pass-rorelse-k01-1', 'forbattra', 'forfina-1', 'skisskritik-1', 'kritik-a-1', 'kritik-b-2',
          'jamforelse', 'forska-1', 'plan', 'planprovning')
assert [observation.sida(r_) for r_ in roller] == ['skapare'] * 6 + ['granskare'] * 4 + ['korning'] * 3, [observation.sida(r_) for r_ in roller]
assert {s_['session_id']: s_ for s_ in observation.oversikt(SLUG)['sessioner']}[sid_a]['sida'] == 'skapare'

# 19. före ägarens beslut bara huvudreferensens namn, aldrig planens beskrivning; inga halvskrivna poster kvar
planer19 = {'k01': 'Tekt (tekt.com.au), referenspaketet paket-v06/tekt/01-start: avsnittet "Our Process" och rytmen',
            'k02': 'Tekt (tekt.com.au): avsnittet Our Process bär den luftiga rytmen', 'k03': 'Tekt (tekt.com.au) som bär den luftiga rytmen i projektlistan',
            'k04': 'Tekt: den luftiga rytmen i projektlistan', 'k05': 'Tekt bär den luftiga rytmen i projektlistan',
            'k06': 'Den luftiga rytmen i projektlistan hos en australisk byggfirma', 'k07': 'Tekt (för den luftiga rytmen och Our Process)'}
(UNDERLAG / SLUG / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps({'kandidater': {k: {'huvudreferens': v, 'referensbilder': ['a', 'b']} for k, v in planer19.items()}}))
r19 = {k: v['huvudreferens'] for k, v in observation.referenser(SLUG)['kandidater'].items()}
assert r19 == {'k01': 'Tekt (tekt.com.au)', 'k02': 'Tekt (tekt.com.au)', 'k03': 'Tekt (tekt.com.au)', 'k04': 'Tekt', 'k05': 'Tekt', 'k06': None, 'k07': 'Tekt'}, r19
vy19 = json.dumps(observation.oversikt(SLUG), ensure_ascii=False)
assert not any(x in vy19 for x in ('Our Process', 'luftiga', 'rytmen', 'projektlistan')), 'planens beskrivning syns aldrig'
assert not list(observation.katalog(SLUG).glob('.*.tmp')), 'inga halvskrivna poster kvar'

# 20. en session i en annan utcheckning av repot: referensen och metodutdraget känns igen ur sökvägen; paketets tid ur
#     PAKET.json (när paketet sammanställdes), aldrig katalogens ändringstid
f20 = TMP / 't20.jsonl'
annan_rot = '/Users/x/annan-utcheckning'
f20.write_text(strom(anrop(1, 'm1', 'Read', {'file_path': annan_rot + '/underlag/%s/referenser/paket-v01/a/01-start/vy-390-forsta.png' % SLUG}),
                     svar(2, 'm1', [{'type': 'image', 'source': {'data': BILDDATA}}], tur={'type': 'image'}),
                     anrop(3, 'm2', 'Read', {'file_path': annan_rot + '/underlag/%s/atelje/metod/METOD-skiss.md' % SLUG}),
                     svar(4, 'm2', 'x', tur={'type': 'text', 'file': {'numLines': 3, 'startLine': 1, 'totalLines': 3}})))
s20 = observation.sammanfattning(f20, SLUG)
assert [x['fil'] for x in s20['referensfiler']] == ['underlag/%s/referenser/paket-v01/a/01-start/vy-390-forsta.png' % SLUG], s20['referensfiler']
assert [x['utfall'] for x in s20['metodutdrag']] == ['fil läst (hel)'], s20['metodutdrag']
pk20 = UNDERLAG / SLUG / 'referenser' / 'paket-v01'
pk20.mkdir(parents=True, exist_ok=True)
(pk20 / 'PAKET.json').write_text(json.dumps({'version': 'paket-v01', 'tid': '2026-10-06T02:55:42Z'}))
(UNDERLAG / SLUG / 'atelje' / 'FORSKNING.json').write_text(json.dumps({'nytt': {'paket': 'paket-v01', 'tjanster': '2026-10-06T02:58:27Z'}}))
assert observation.referenser(SLUG)['paket_tid'] == '2026-10-06T02:55:42Z'

# 21. ett läsfel ger det senast lästa läget med en varning (felet, utan sökväg, och tiden för den senaste lyckade
#     läsningen), aldrig som aktuellt; nästa lyckade läsning tar bort varningen och läser det nya
f21 = TMP / 't21.jsonl'
f21.write_text(strom(anrop(1, 'n1', 'Grep', {}), anrop(2, 'n2', 'Grep', {})))
l21 = observation.las_session(f21)
assert set(l21['anrop']) == {'n1', 'n2'} and l21['lasfel'] is None and l21['senast_last'], l21
senast21 = l21['senast_last']
with open(f21, 'a') as f:
    f.write(anrop(3, 'n3', 'Grep', {}) + '\n')


def nekad_open(*a_, **k_):
    raise PermissionError(13, 'Permission denied', str(f21))


observation.open = nekad_open  # skuggar den inbyggda open i modulen
try:
    s21 = observation.sammanfattning(f21)
finally:
    del observation.open
assert s21['lasfel'] and s21['lasfel']['fel'] == 'PermissionError: Permission denied' and str(f21) not in json.dumps(s21), s21['lasfel']
assert s21['senast_last'] == senast21 and s21['verktyg'] == {'Grep': {'inget svar observerat': 2}}, ('det senast lästa, med varning', s21)
s21b = observation.sammanfattning(f21)
assert s21b['lasfel'] is None and s21b['verktyg'] == {'Grep': {'inget svar observerat': 3}}, ('varningen borta, det nya läst', s21b)
f21.unlink()  # en fil som försvunnit efter en läsning: samma varning över det senast lästa
s21c = observation.sammanfattning(f21)
assert s21c['lasfel']['fel'].startswith('FileNotFoundError') and s21c['verktyg'] == {'Grep': {'inget svar observerat': 3}}, s21c
s21d = observation.sammanfattning(TMP / 't21-aldrig.jsonl')  # utan tidigare läsning: ett tomt läge med varning
assert s21d['lasfel'] and s21d['senast_last'] is None and s21d['verktyg'] == {} and s21d['mcp'] == [], s21d
# vyn: sessionen med läsfel bär varningen i översikten, och prototypens skärmbild utan läsbar tid får ingen tid
sid_21 = '00000000-0000-4000-8000-0000000000cc'
f21e = KONFIG / 'projects' / '-falsk-repo' / (sid_21 + '.jsonl')
f21e.write_text(strom(anrop(1, 'p1', 'Grep', {})))
observation._skriv(observation.katalog(SLUG) / (sid_21 + '.json'), {'session_id': sid_21, 'roll': 'skiss-3', 'kandidat': 'k02', 'svar': 'svar-skiss-3.json',
                                                                     'start': observation.nu(), 'modell': 'm', 'pid': None, 'slut': observation.nu(), 'utfall': 'avslutad, kod 0'})
assert {s_['session_id']: s_ for s_ in observation.oversikt(SLUG)['sessioner']}[sid_21]['observation']['lasfel'] is None
observation.open = nekad_open
try:
    o21 = {s_['session_id']: s_ for s_ in observation.oversikt(SLUG)['sessioner']}[sid_21]['observation']
finally:
    del observation.open
assert o21['lasfel'] and o21['senast_last'] and o21['verktyg'] == {'Grep': {'inget svar observerat': 1}}, o21
(observation.katalog(SLUG) / (sid_21 + '.json')).unlink()
v21 = KAND / 'k02' / 'varv' / 'start' / 'varv-01'
v21.mkdir(parents=True)
(v21 / 'vy-390-forsta.png').write_bytes(b'png')
orig_mtid, orig_rot = observation._mtid, observation.ROOT
observation.ROOT = TMP  # bilderna ligger i provets underlag
try:
    p21_med = observation.prototyper(SLUG)['k02']['varv']
    observation._mtid = lambda p: 0
    p21 = observation.prototyper(SLUG)['k02']['varv']
finally:
    observation._mtid, observation.ROOT = orig_mtid, orig_rot
b21 = {'390': 'underlag/%s/atelje/kandidater/k02/varv/start/varv-01/vy-390-forsta.png' % SLUG}
assert p21_med['skarmbild_fangad'] and p21_med['bilder'] == b21, ('med läsbar tid står tiden', p21_med)
assert p21['skarmbild_fangad'] is None and p21['bilder'] == b21, ('utan läsbar tid ingen tid, aldrig 1970', p21)
shutil.rmtree(KAND / 'k02' / 'varv')
# 21b. en fil som aldrig gått att läsa är ingen observation: "inte observerat" med felet, aldrig "inga observerade"
#      (granskningen av r92, BÖR 1); en logg som lästs förut visar sitt senast lästa läge med varning
sid_21b = '00000000-0000-4000-8000-0000000000dd'
(KONFIG / 'projects' / '-falsk-repo' / (sid_21b + '.jsonl')).write_text(strom(anrop(1, 'q1', 'Grep', {})))
observation._skriv(observation.katalog(SLUG) / (sid_21b + '.json'), {'session_id': sid_21b, 'roll': 'skiss-4', 'kandidat': 'k02', 'svar': 'svar-skiss-4.json',
                                                                      'start': observation.nu(), 'modell': 'm', 'pid': None, 'slut': observation.nu(), 'utfall': 'avslutad, kod 0'})
ny_logg = UNDERLAG / SLUG / 'referenser' / 'tjanster' / 'refero' / 'session-2026-10-06T120000Z.jsonl'
ny_logg.parent.mkdir(parents=True, exist_ok=True)
ny_logg.write_text(strom(anrop(1, 'r1', 'mcp__refero__refero_search_screens', {'query': FRAS})))
observation.open = nekad_open
try:
    s21e = {s_['session_id']: s_ for s_ in observation.oversikt(SLUG)['sessioner']}[sid_21b]
    tj21 = {t_['logg']: t_ for t_ in observation.tjanstesessioner(SLUG)}
finally:
    del observation.open
assert s21e['observation'] is None and s21e['ofullstandig'] == 'transkriptet kunde inte läsas: PermissionError: Permission denied', s21e
t21n = tj21['referenser/tjanster/refero/session-2026-10-06T120000Z.jsonl']
assert 'observation' not in t21n and t21n['ofullstandig'] == 'loggen kunde inte läsas: PermissionError: Permission denied', t21n
t21g = tj21['referenser/tjanster/mobbin/session-2026-10-06T100000Z.jsonl']
assert t21g['observation']['lasfel'] and t21g['observation']['senast_last'] and t21g['observation']['mcp'], ('läst förut: senaste läget med varning', t21g)
(observation.katalog(SLUG) / (sid_21b + '.json')).unlink(); ny_logg.unlink()
# 21c. en FIFO där en tjänstelogg väntas blockerar aldrig observationens lås (granskningen av r92, KAN 3)
fifo = UNDERLAG / SLUG / 'referenser' / 'tjanster' / 'mobbin' / 'session-2026-10-06T130000Z.jsonl'
os.mkfifo(fifo)
svar21c = []
tr21c = threading.Thread(target=lambda: svar21c.append(observation.tjanstesessioner(SLUG)), daemon=True)
tr21c.start()
tr21c.join(10)
if tr21c.is_alive():  # släpp den blockerade läsningen först, så att låset frigörs innan provet faller
    os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
    tr21c.join(5)
assert svar21c, 'en FIFO blockerade läsningen'
f21c = [t_ for t_ in svar21c[0] if t_['logg'].endswith('T130000Z.jsonl')]
assert f21c and f21c[0]['ofullstandig'] == 'loggen kunde inte läsas: OSError: inte en vanlig fil', f21c
fifo.unlink()
# 21d. storleken och identiteten tas från den öppnade filen: byts filen mellan öppningen och läsningen läses den öppnade,
#      och den nya läses från början nästa gång (granskningen av r92, KAN 5)
import builtins  # noqa: E402
f21d, ny21d = TMP / 't21d.jsonl', TMP / 't21d-ny.jsonl'
f21d.write_text(strom(anrop(1, 'o1', 'Grep', {}), anrop(2, 'o2', 'Grep', {})))
ny21d.write_text(strom(*[anrop(i, 'n%d' % i, 'Glob', {}) for i in range(1, 6)]))


def byt_efter_oppning(*a_, **k_):
    h_ = builtins.open(*a_, **k_)
    os.replace(ny21d, f21d)
    del observation.open  # bara den här öppningen
    return h_


observation.open = byt_efter_oppning
try:
    l21d = set(observation.las_session(f21d)['anrop'])
finally:
    observation.__dict__.pop('open', None)
assert l21d == {'o1', 'o2'}, l21d
assert set(observation.las_session(f21d)['anrop']) == {'n1', 'n2', 'n3', 'n4', 'n5'}, 'den nya filen läses från början'

# 22. en skill som körts av en underagent (context: fork) märks så: dess läsningar står inte i sessionens transkript
f22 = TMP / 't22.jsonl'
f22.write_text(strom(anrop(1, 's1', 'Skill', {'skill': 'code-review'}), svar(2, 's1', 'Skill "code-review" completed (forked execution).'),
                     anrop(3, 's2', 'Skill', {'skill': 'impeccable'}), svar(4, 's2', 'Launching skill: impeccable')))
s22 = observation.sammanfattning(f22)
assert [(x['skill'], x['utfall']) for x in s22['skills_laddade']] == [('code-review', 'skill körd av en underagent (dess läsningar syns inte)'),
                                                                       ('impeccable', 'skill laddad via skillsystemet')], s22['skills_laddade']

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
