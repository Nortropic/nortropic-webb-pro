#!/usr/bin/env python3
"""prov_startkvitto.py — startkvittots betydelse och sessionernas verkliga åtkomst (ägarens uppdrag 2026-10-07, punkt 2, 3
och 10, ordagrant i minnet), i en isolerad kopia av repot med falska nät, modeller och claude:

1. research som inte körts: referensunderlaget står som planerat i researchen, förutsättningarna prövas, och inget
   saknat underlag gör kvittot rött;
2. giltigt underlag efter researchen utan REFERENSER.md godtas, och fel, tomma tjänster och uteblivna bilder redovisas
   som blockerade, aldrig som använda;
3. en tom eller inaktuell referensfil godtas inte (den äldre utforskningens REFERENSER.md, och kandidatflödets research
   från en tidigare körning), och helbygget prövar VINNARE.json;
4. upptäckt men otillåtet verktyg: "ingen uppgift" med metodkartans beslut och "nytt, obedömt" med åtgärd, aldrig
   "okänd", och inget av dem gör kvittot mer begränsat;
5. en tilldelad tjänst som sessionen inte når står som "tilldelad men åtkomst saknas", inte ok: ateljéns argument ger
   Mobbin utan att Refero faller bort, och startkontrollen prövar med just de argumenten;
6. kvittot per roll: varje roll i metodkartan med det tilldelade och åtkomsten i sessionen, och kompetenskvittot i
   tillståndsorden (ett läskvitto är belägg för läsning, inte för tillämpning);
7. en källa: kor.sh läser tjänsternas verktyg ur referenstjanster.TJANSTER, och metodkartans beslut prövas mot listan;
8. tåligheten: en oväntad form i underlaget eller ett sessionsprov som kastar stoppar aldrig starten, och research utan
   eget material står aldrig som använd.

    .venv/bin/python kontroller/rokprov/revision/prov_startkvitto.py <repo>

Fallen 1–5 var röda mot main 84c6994 och är gröna efter rättelsen. Varje fall redovisas för sig på stderr; slutkod 1
när något fall föll. Ingenting skrivs i repots underlag/ eller kunder/, och inga privata data läses.
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
TMP = Path(tempfile.mkdtemp(prefix='nwp-startkvitto-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):  # också när provet faller: annars fyller kvarlämnade kopior disken
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
KOPIA, FAKE = TMP / 'repo', TMP / 'fake'
FEL = []
ROTT = ('fel', 'delvis', 'okand', 'avvisad', 'behallen')  # behöver uppmärksamhet och gör kvittot begränsat


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:600]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


# --- den isolerade kopian ---
utom = shutil.ignore_patterns('node_modules', '.git', 'underlag', 'kunder', 'dist', '.astro', '__pycache__', '.venv')
for d in ('kontroller', 'kunskap', 'kritik', 'mall', '.claude'):
    shutil.copytree(ROOT_REAL / d, KOPIA / d, ignore=utom, symlinks=True)
for f in ('README.md', 'BESLUT.md', 'CLAUDE.md', 'LARDOMAR.md', 'kor.sh', 'requirements.txt', 'requirements-lock.txt', '.gitignore'):
    if (ROOT_REAL / f).exists():
        shutil.copy2(ROOT_REAL / f, KOPIA / f)
os.symlink(os.path.realpath(ROOT_REAL / '.venv'), KOPIA / '.venv')
os.symlink(os.path.realpath(ROOT_REAL / 'kontroller' / 'node_modules'), KOPIA / 'kontroller' / 'node_modules')
GIT = ['git', '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se', '-c', 'commit.gpgsign=false']
for a in (('init', '-q', '-b', 'main'), ('add', '-A'), ('commit', '-q', '-m', 'kopian')):
    subprocess.run(GIT + list(a), cwd=str(KOPIA), capture_output=True, check=True)

# falska binärer: claude svarar på --version, --help, mcp list och sessionsprovet (init-beskedet: Refero ur den lokala
# nivån, Mobbin bara när argumenten ger kontroller/mcp/mobbin.json, som i en riktig session med --setting-sources
# project,local), vercel och npm
(FAKE / 'bin').mkdir(parents=True)
(FAKE / 'version').write_text('2.1.289 (Claude Code)\n')
(FAKE / 'help').write_text('Usage: claude ' + ' '.join(['--json-schema', '--allowedTools', '--disallowedTools', '--settings', '--setting-sources', '--tools',
                                                        '--permission-mode', '--strict-mcp-config', '--mcp-config', '--effort', '--model',
                                                        '--output-format']) + '\n')
(FAKE / 'mcp').write_text('refero: https://api.refero.design/mcp (HTTP) - ✔ Connected\nmobbin: https://api.mobbin.com/mcp (HTTP) - ✔ Connected\n')
(FAKE / 'bin' / 'claude').write_text(
    '#!/bin/bash\nD=%s\necho "$*" >> "$D/claude-anrop"\ncase "$1" in --version) cat "$D/version";; --help) cat "$D/help";; mcp) cat "$D/mcp";; '
    '*) case " $* " in *" stream-json "*) echo "$*" >> "$D/sessionsprov"; if [[ " $* " == *"/kontroller/mcp/mobbin.json "* ]]; then cat "$D/init-med"; '
    'else cat "$D/init-utan"; fi; echo \'{"type":"result","subtype":"success","is_error":false,"result":"OK"}\';; *) echo "{}";; esac;; esac\n' % FAKE)
(FAKE / 'bin' / 'vercel').write_text('#!/bin/bash\necho "Vercel CLI 60.0.1"\n')
(FAKE / 'bin' / 'npm').write_text('#!/bin/bash\ncase "$1" in --version) echo 10.9.8;; *) exit 1;; esac\n')
for b in ('claude', 'vercel', 'npm'):
    (FAKE / 'bin' / b).chmod(0o755)
os.environ['PATH'] = '%s:%s' % (FAKE / 'bin', os.environ['PATH'])
os.environ['NWP_CLAUDE_BIN'] = str(FAKE / 'bin' / 'claude')
os.environ['NWP_SPANING_AV'] = '1'
os.environ['NWP_KORREGISTER'] = str(TMP / 'korregister')
os.environ['NWP_STADNING'] = 'av'
for k_ in ('NWP_SLUG', 'NWP_STARTKONTROLL', 'NWP_UNDERHALL_PROV', 'NWP_KANDIDATFLODE', 'NWP_ATELJE', 'NWP_MCP_CONFIG'):
    os.environ.pop(k_, None)

sys.path.insert(0, str(KOPIA / 'kontroller'))
import verktygslada as vl  # noqa: E402
import startkontroll as sk  # noqa: E402
import atelje  # noqa: E402
import kundvakt  # noqa: E402
import kompetens  # noqa: E402
import referenstjanster  # noqa: E402
import refero_mcp  # noqa: E402
import stadning  # noqa: E402
assert vl.ROOT == KOPIA, vl.ROOT
stadning.disk_matt = lambda p: (1000, 400)  # 40 % ledigt: diskvakten städar aldrig här
stadning.Ram.verklig = classmethod(lambda cls, *a, **k: (_ for _ in ()).throw(AssertionError('provet städar aldrig det verkliga systemet')))
vl.inventera = lambda k, delar=None: []  # versionerna prövas i prov_startkontroll.py; här gäller kvittots betydelse
vl.modellsvar = lambda *a, **k: None
vl.vaktprov = lambda *a, **k: None
FLODETS_REFERO = [v.split('__')[-1] for v in referenstjanster.TJANSTER['refero']['verktyg']]
REFERO = {'verktyg': FLODETS_REFERO + ['refero_search_apps']}  # Referos verktygslista (direkt och i sessionen)


class FalskKlient:
    def __init__(self, *a, **k):
        pass

    def starta(self):
        return {}

    def verktyg(self):
        return list(REFERO['verktyg'])

    def json(self, namn, args):
        return {'records': [{'uuid': 'u1', 'preview_url': 'https://images.refero.design/x.jpg'}]} if namn == 'refero_search_styles' else \
            {'colors': [1, 2], 'typography': [1]}


def falsk_bild(url, mal, max_byte=0):
    p = Path(str(mal) + '.jpg')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b'\xff\xd8\xffbild')
    return p


refero_mcp.Klient, refero_mcp.ladda_bild = FalskKlient, falsk_bild
refero_mcp.nyckel = lambda fil=None: 'provnyckel'
vl.prova_webblasaren = lambda k, prov_dir, node_modules=None: k.minns('prov:webblasare', 'v1', vl.GILTIGHET['prov']) or \
    k.spara('prov:webblasare', 'v1', resultat='ok', detalj='falsk sida inspekterad')
vl.prova_detektorn = lambda k, prov_dir: k.minns('prov:detektor', 'v1', vl.GILTIGHET['prov']) or \
    k.spara('prov:detektor', 'v1', resultat='ok', detalj='falsk motor')
vl.Cache(vl.lagekatalog() / 'CACHE.json').spara('prov:mobbin', 'v1', resultat='ok', detalj='sökning och 3 bilder (falskt prov)')


def skriv_init():
    """Init-beskedet för en session med respektive utan kontroller/mcp/mobbin.json, med Referos aktuella verktygslista."""
    for namn, med in (('init-med', True), ('init-utan', False)):
        servrar = [{'name': 'refero', 'status': 'connected', 'source': 'local'}] + (
            [{'name': 'mobbin', 'status': 'connected', 'source': 'dynamic'}] if med else []) + [
            {'name': 'claude.ai Claude Docs', 'status': 'connected', 'source': 'claudeai'}]
        verktyg = ['Glob', 'Grep', 'Read', 'Skill', 'ToolSearch', 'mcp__claude_ai_Claude_Docs__read'] + \
            ['mcp__refero__' + v for v in REFERO['verktyg']] + (list(referenstjanster.TJANSTER['mobbin']['verktyg']) if med else [])
        skills = sorted(p.name for p in (KOPIA / '.claude' / 'skills').iterdir() if p.is_dir())
        (FAKE / namn).write_text(json.dumps({'type': 'system', 'subtype': 'init', 'mcp_servers': servrar, 'tools': verktyg, 'skills': skills}) + '\n')


skriv_init()


def glom(*nycklar):
    """Glömmer sparade prov, så att nästa start gör om dem (Referos verktygslista, sessionsprovet)."""
    c = vl.Cache(vl.lagekatalog() / 'CACHE.json')
    for n in nycklar:
        c.d.pop(n, None)
    vl.skriv_json(c.fil, c.d)


def kund(slug, verksamhet=True):
    u = KOPIA / 'underlag' / slug
    (u / 'bilder').mkdir(parents=True, exist_ok=True)
    (u / 'BRIEF.md').write_text('# Brief\n\n## §4 Primär handling\n\nRing eller skicka en förfrågan i formuläret.\n')
    (u / 'RESEARCH.md').write_text('# Research\n\nProvets underlag.\n')
    (u / 'TEXTUNDERLAG.md').write_text('# Text\n\nProvets text.\n')
    (u / 'bilder' / 'BILDER.md').write_text('| fil | vad |\n|---|---|\n| a.jpg | jobb |\n')
    if verksamhet:
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Provfirman Exempel AB', 'kategorier': ['Byggfirma'], 'adress': {'ort': 'Provby'}}))
    return u


def referensrader(kv):
    """Kvittots rader om referensunderlaget (före rättelsen hette raden referenserna)."""
    return [r for r in kv['rader'] if r['grupp'] == 'uppdrag' and r['namn'] in ('referenserna', 'referensunderlaget')]


def kvitto_md(slug, namn='STARTKVITTO'):
    return (KOPIA / 'underlag' / slug / 'atelje' / (namn + '.md')).read_text(encoding='utf-8')


def begransande(kv):
    return sorted((r['grupp'], r['namn']) for r in kv['rader'] if r['resultat'] in ROTT)


T0, T1, T2 = '2026-10-06T18:00:00Z', '2026-10-06T18:20:00Z', '2026-10-06T18:40:00Z'


def researchat(slug, forsk_tid=T1, start=T0, tjanster=None, bild_saknas=False):
    """Kandidatflödet efter researchen: STATUS.json, FORSKNING.json och .md, referenspaketet, tjänsternas rapport med
    bilderna på disken och uppdragens material, utan REFERENSER.md."""
    u = kund(slug)
    a = u / 'atelje'
    a.mkdir(parents=True, exist_ok=True)
    (a / 'STATUS.json').write_text(json.dumps({'slug': slug, 'steg': 'skapa', 'lage': 'fortsatt', 'kandidatflode': True, 'tider': {'start': start}, 'faser': {}}))
    (a / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': T1, 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett förslag'}}}))
    (a / 'FORSKNING.json').write_text(json.dumps({'tid': forsk_tid, 'fel': None, 'slappta': [], 'antaganden': [], 'fragor': [], 'sajter': [],
                                                  'nytt': {'paket': 'paket-v01', 'sajter': ['ett', 'tva'], 'tjanster': forsk_tid},
                                                  'fore': {'paket': None, 'tjanster': None}}))
    (a / 'FORSKNING.md').write_text('# Research före kandidatplanen\n')
    p = u / 'referenser' / 'paket-v01'
    p.mkdir(parents=True, exist_ok=True)
    kandidater = []
    for namn in ('ett', 'tva'):  # sajternas sparade bilder ligger relativt paketet
        (p / namn / '01-start').mkdir(parents=True, exist_ok=True)
        (p / namn / '01-start' / 'vy-390-forsta.png').write_bytes(b'\x89PNG\r\n\x1a\nbild')
        kandidater.append({'namn': namn, 'ok': True, 'sidor': [{'sida': '/', 'katalog': namn + '/01-start', 'ok': True,
                                                                 'filer': [namn + '/01-start/vy-390-forsta.png', namn + '/01-start/EXTRAKT.md']}]})
    (p / 'PAKET.json').write_text(json.dumps({'version': 'paket-v01', 'kandidater': kandidater}))
    (p / 'PAKET.md').write_text('# Referenspaket\n')
    tjd = u / 'referenser' / 'tjanster'
    for t in ('refero', 'mobbin'):
        (tjd / t).mkdir(parents=True, exist_ok=True)
        (tjd / t / 'a.jpg').write_bytes(b'\xff\xd8\xffbild')
    tj = tjanster or {
        'refero': {'fragor': [{'fraga': 'x'}], 'anrop': {'mcp__refero__refero_search_screens': 2}, 'stilar': [], 'bilder': 1, 'ok': True, 'anmarkningar': [],
                   'traffar': [{'id': 'r1', 'fil': 'referenser/tjanster/refero/a.jpg'}] + ([{'id': 'r2', 'fil': None, 'fel': 'ingen bild'}] if bild_saknas else [])},
        'mobbin': {'fragor': [{'fraga': 'y'}], 'anrop': {'mcp__mobbin__search_screens': 1}, 'stilar': [], 'bilder': 1, 'ok': True, 'anmarkningar': [],
                   'traffar': [{'id': 'm1', 'fil': 'referenser/tjanster/mobbin/a.jpg'}]}}
    (tjd / 'TJANSTER.json').write_text(json.dumps({'schema': 2, 'tid': forsk_tid, 'torr': False, 'tjanster': tj}))
    (tjd / 'TJANSTER.md').write_text('# Referenstjänster\n')
    (u / 'referenser' / 'uppdrag' / 'mobbin').mkdir(parents=True, exist_ok=True)
    (u / 'referenser' / 'uppdrag' / 'mobbin' / 'c.jpg').write_bytes(b'\xff\xd8\xffbild')
    (a / 'UPPDRAGSMATERIAL.json').write_text(json.dumps({'tid': T2, 'mobbin': {'ok': True, 'bilder': 1}, 'kandidater': {
        'k01': {'mobbin_fraga': 'contact form', 'mobbin': [{'fil': 'underlag/%s/referenser/uppdrag/mobbin/c.jpg' % slug, 'titel': 't', 'beskrivning': 'b'}]}}}))
    return u


# ===== 1. research som inte körts =====

@fall('1 research som inte körts: underlaget står som planerat i researchen och gör inte kvittot rött')
def _research_ej_kord():
    slug = 'k1-fore'
    u = kund(slug)
    kv = sk.kor_kontroll(slug, 'ny')
    r = referensrader(kv)
    assert len(r) == 1, r
    assert r[0]['resultat'] not in ROTT, 'ett underlag som researchen ska skriva gör kvittot rött: %s' % r[0]
    assert not [x for x in begransande(kv) if 'referens' in x[1]], begransande(kv)
    assert 'REFERENSER.md saknas' not in kvitto_md(slug) and not (u / 'REFERENSER.md').exists(), 'kontrollen kräver eller skapar REFERENSER.md'
    assert r[0].get('tillstand') == 'planerat' and 'planerade i researchen' in r[0]['detalj'], r[0]
    # förutsättningarna prövas: utan kundens uppgifter kan kundvakten inte pröva frågorna, och då är researchen blockerad
    (u / 'VERKSAMHET.json').unlink()
    r2 = referensrader(sk.kor_kontroll(slug, 'ny'))[0]
    assert r2['resultat'] == 'fel' and 'kundvakten' in r2['detalj'], r2
    # körvägen: prototypkörningen i kandidatflödet, före researchen, och kvittot verifierar aldrig Figma-piloten
    assert kv['korvag']['id'] == 'kandidatflodet' and kv['korvag']['fas'] == 'fore_research', kv['korvag']
    md = kvitto_md(slug)
    assert 'prototypkörningen i kandidatflödet' in md and 'gäller inte Figma-piloten' in md, md[:600]


# ===== 2. giltigt underlag utan REFERENSER.md =====

@fall('2 giltigt underlag efter researchen utan REFERENSER.md godtas, i fortsättningen och förfiningen')
def _giltigt_underlag():
    slug = 'k2-efter'
    u = researchat(slug)
    for start in ('fortsatt', 'valda'):
        kv = sk.kor_kontroll(slug, start)
        r = referensrader(kv)
        assert len(r) == 1 and r[0]['resultat'] == 'ok', (start, r)
        assert r[0].get('tillstand') == 'anvant' and 'FORSKNING.json' in r[0]['detalj'] and 'paket-v01' in r[0]['detalj'], r[0]
        assert kv['korvag']['fas'] == 'efter_research', kv['korvag']
    assert not (u / 'REFERENSER.md').exists() and 'REFERENSER.md saknas' not in kvitto_md(slug)


@fall('2b fel, tomma tjänster och uteblivna bilder redovisas som blockerade, aldrig som använda')
def _brister_i_underlaget():
    slug = 'k2b-brister'
    researchat(slug, bild_saknas=True)
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'delvis' and 'Refero: 1 träffar utan bild' in r['detalj'] and 'blockerat eller misslyckat' in r['detalj'], r
    tom = {'refero': {'fragor': [{'fraga': 'x'}], 'anrop': {'mcp__refero__refero_search_screens': 1}, 'traffar': [{'fil': 'referenser/tjanster/refero/a.jpg'}],
                      'stilar': [], 'bilder': 1, 'ok': True},
           'mobbin': {'fragor': [{'fraga': 'y'}], 'anrop': {}, 'traffar': [], 'stilar': [], 'bilder': 0, 'ok': False, 'anmarkningar': ['inga verkliga verktygsanrop']}}
    slug = 'k2b-tom'
    u = researchat(slug, tjanster=tom)
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'fel' and 'Mobbin: inga verkliga anrop' in r['detalj'] and 'Mobbin med' not in r['detalj'], r
    (u / 'referenser' / 'tjanster' / 'refero' / 'a.jpg').unlink()  # en levererad bild som inte finns på disken
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert 'Refero: 1 bilder saknas på disken' in r['detalj'], r
    # referenspaketet: en sajt med brister är material med en brist; en sparad bild som saknas på disken är ett fel
    slug = 'k2b-paket'
    u = researchat(slug)
    pk = json.loads((u / 'referenser' / 'paket-v01' / 'PAKET.json').read_text())
    pk['kandidater'][1]['ok'] = False
    (u / 'referenser' / 'paket-v01' / 'PAKET.json').write_text(json.dumps(pk))
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'delvis' and '1 sajter i paket-v01 har brister' in r['detalj'] and 'sparade bilder från 2 av 2 sajter' in r['detalj'], r
    (u / 'referenser' / 'paket-v01' / 'tva' / '01-start' / 'vy-390-forsta.png').unlink()
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'fel' and '1 sparade bilder i paket-v01 saknas på disken' in r['detalj'], r


# ===== 3. tom eller inaktuell referensfil =====

@fall('3 tom eller inaktuell referensfil godtas inte; helbygget prövar VINNARE.json')
def _tom_eller_inaktuell():
    os.environ['NWP_KANDIDATFLODE'] = 'av'  # den äldre utforskningen, som läser REFERENSER.md
    try:
        slug = 'k3-tom'
        u = kund(slug)
        (u / 'REFERENSER.md').write_text('# Referenser\n\nInget urval ännu.\n')
        r = referensrader(sk.kor_kontroll(slug, 'ny'))
        assert len(r) == 1 and r[0]['resultat'] in ROTT, 'en tom REFERENSER.md godtogs: %s' % r
        slug = 'k3-inaktuell'
        u = kund(slug)
        (u / 'REFERENSER.md').write_text('# Referenser\n\nHuvudreferenskandidat: Snick — snickeri med stora bilder\n\n## Snick — snickeri\n\n'
                                         'Bildval: referenser/snick/vy-390-forsta.png — första vyn — Fråga: hur stor är bilden?\n')
        r = referensrader(sk.kor_kontroll(slug, 'ny'))
        assert len(r) == 1 and r[0]['resultat'] in ROTT and 'inaktuell' in r[0]['detalj'], 'en REFERENSER.md vars bilder saknas godtogs: %s' % r
        # samma fil med bilden på plats godtas
        (u / 'referenser' / 'snick').mkdir(parents=True)
        (u / 'referenser' / 'snick' / 'vy-390-forsta.png').write_bytes(b'\x89PNG\r\n\x1a\nbild')
        r = referensrader(sk.kor_kontroll(slug, 'ny'))
        assert r[0]['resultat'] == 'ok', r
    finally:
        os.environ.pop('NWP_KANDIDATFLODE', None)
    # kandidatflödet: research från en tidigare körning godtas inte, inte heller med en gammal REFERENSER.md bredvid
    slug = 'k3-tidigare'
    u = researchat(slug, forsk_tid=T0, start=T1)
    (u / 'REFERENSER.md').write_text('# Referenser\n\nHuvudreferens: Snick — snickeri\n')
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))
    assert len(r) == 1 and r[0]['resultat'] in ROTT and 'inaktuell' in r[0]['detalj'], 'research ur en tidigare körning godtogs: %s' % r
    # helbygget: VINNARE.json med huvudreferensens bilder, och utan den inget godkänt underlag
    slug = 'k3-bygge'
    u = kund(slug)
    r = referensrader(sk.kor_kontroll(slug, 'bygge'))
    assert len(r) == 1 and r[0]['resultat'] == 'fel' and 'VINNARE.json saknas' in r[0]['detalj'], r
    (u / 'referenser' / 'snick').mkdir(parents=True)
    (u / 'referenser' / 'snick' / 'a.png').write_bytes(b'\x89PNG\r\n\x1a\nbild')
    (u / 'atelje').mkdir(exist_ok=True)
    (u / 'atelje' / 'VINNARE.json').write_text(json.dumps({'kandidat': 'k01', 'huvudreferens': {
        'namn': 'Snick', 'vad': 'stora bilder', 'bilder': [['underlag/%s/referenser/snick/a.png' % slug, 'ur kandidatens uppdrag']]}}))
    r = referensrader(sk.kor_kontroll(slug, 'bygge'))
    assert r[0]['resultat'] == 'ok' and 'Snick med 1 bilder' in r[0]['detalj'] and 'inte godkänd' in r[0]['detalj'], r


# ===== 4. upptäckt men otillåtet verktyg =====

@fall('4 upptäckt men otillåtet verktyg: "ingen uppgift" med beslut och "nytt, obedömt", aldrig "okänd" och aldrig mer begränsat')
def _upptackt_verktyg():
    slug = 'k4-verktyg'
    kund(slug)
    # ett färskt underhåll och en färsk spaning: annars är kvittot redan begränsat, och fallet prövade inget
    underhall = vl.lagekatalog() / 'UNDERHALL.json'
    spaning = KOPIA / 'kirurgen' / 'spaning'
    spaning.mkdir(parents=True, exist_ok=True)
    vl.skriv_json(underhall, {'slut': vl.nu(), 'sammanfattning': 'provets underhåll'})
    vl.skriv_json(spaning / 'SENAST.json', {'slut': vl.nu()})
    vl.skriv_json(spaning / 'KANDIDATER.json', [])
    glom('prov:refero', 'prov:session')
    try:
        kv_a = sk.kor_kontroll(slug, 'ny')  # Referos lista med refero_search_apps, som har beslutet ingen uppgift
        REFERO['verktyg'] = FLODETS_REFERO + ['refero_search_apps', 'refero_search_widgets']  # ett nytt verktyg utan beslut
        skriv_init()
        glom('prov:refero', 'prov:session')
        kv_b = sk.kor_kontroll(slug, 'ny')
    finally:
        REFERO['verktyg'] = FLODETS_REFERO + ['refero_search_apps']
        skriv_init()
        glom('prov:refero', 'prov:session')
        underhall.unlink()
        shutil.rmtree(KOPIA / 'kirurgen')
    for kv in (kv_a, kv_b):
        okanda = [r for r in kv['rader'] if r['resultat'] == 'okand' and re.search(r'refero_search_(apps|widgets)', r['namn'] + ' ' + str(r.get('detalj')))]
        assert not okanda, 'ett upptäckt verktyg står som okänt: %s' % okanda
    assert kv_a['status'] == 'redo', 'provets förutsättning: utan det nya verktyget är kvittot redo (%s)' % begransande(kv_a)
    assert kv_b['status'] == 'redo' and begransande(kv_b) == begransande(kv_a), 'ett nytt verktyg gjorde kvittot begränsat: %s' % begransande(kv_b)
    rad = {r['namn']: r for r in kv_b['rader']}
    apps = rad.get('refero_search_apps (Refero)') or {}
    assert apps.get('resultat') == 'ingen_uppgift' and 'prövat 2026-10-07' in apps['detalj'] and 'iOS' in apps['detalj'], apps
    ny = rad.get('refero_search_widgets (Refero)') or {}
    assert ny.get('resultat') == 'nytt' and 'Åtgärd' in ny['detalj'] and 'metodkarta' in ny['detalj'], ny
    md = kvitto_md(slug)
    assert 'nytt, obedömt' in md and 'ingen uppgift (beslut)' in md and 'okänd | ' not in md.split('refero_search_widgets')[1][:40], md[:400]
    # kundvakten släpper bara flödets verktyg: båda nekas, och Mobbins verktyg hör till flödets
    for v in ('mcp__refero__refero_search_apps', 'mcp__refero__refero_search_widgets'):
        assert kundvakt.provning(slug, KOPIA / 'underlag', {'tool_name': v, 'tool_input': {'query': 'home builder'}}), v
    assert set(referenstjanster.TJANSTER['mobbin']['verktyg']) <= kundvakt.tillatna()


# ===== 5. tilldelad tjänst som sessionen inte når =====

@fall('5 tilldelad tjänst som sessionen inte når: "tilldelad men åtkomst saknas", inte ok; ateljéns argument ger Mobbin och Refero')
def _atkomst():
    slug = 'k5-atkomst'
    kund(slug)
    orig = atelje.session_args

    def utan_mobbin(*a, **k):  # ateljéns argument som de var på 84c6994: ingen --mcp-config
        args = orig(*a, **k)
        if '--mcp-config' in args:
            i = args.index('--mcp-config')
            del args[i:i + 2]
        return args
    atelje.session_args = utan_mobbin
    glom('prov:session')
    try:
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        atelje.session_args = orig
        glom('prov:session')
    sessionsrader = [r for r in kv['rader'] if 'Mobbin' in r['namn'] and 'session' in r['namn']]
    assert sessionsrader, 'kvittot säger inget om Mobbin i ateljéns session: %s' % [(r['namn'], r['resultat']) for r in kv['rader'] if 'obbin' in r['namn']]
    m = sessionsrader[0]
    assert m['resultat'] == 'fel' and 'tilldelad men åtkomst saknas' in m['detalj'] and 'Konsekvens' in m['detalj'] and 'Åtgärd' in m['detalj'], m
    assert not [r for r in sessionsrader if r['resultat'] == 'ok'], 'en tjänst som sessionen inte når står som ok'
    assert next(r for r in kv['rader'] if r['namn'] == 'Refero i ateljéns session')['resultat'] == 'ok'
    roll = {r['roll']: r for r in kv['roller']}
    for kid in ('plan', 'komposition', 'innehall', 'responsiv'):
        assert roll[kid]['atkomst']['mcp']['mobbin']['tillstand'] == 'blockerat', (kid, roll[kid]['atkomst'])
    assert 'tilldelad men åtkomst saknas' in kvitto_md(slug)
    # med ateljéns egna argument: Mobbin genom kontroller/mcp/mobbin.json, utan strikt läge, så att Refero står kvar
    kv = sk.kor_kontroll(slug, 'ny')
    rad = {r['namn']: r for r in kv['rader']}
    assert rad['Mobbin i ateljéns session']['resultat'] == 'ok' and rad['Refero i ateljéns session']['resultat'] == 'ok', rad['Mobbin i ateljéns session']
    a = atelje.session_args(['Read'], None, 10, 'm', 'high', (), slug)
    assert a[a.index('--mcp-config') + 1] == str(KOPIA / 'kontroller' / 'mcp' / 'mobbin.json') and '--strict-mcp-config' not in a, a
    b = atelje.session_args(['Read'], None, 10, 'm', 'high', ())
    assert '--strict-mcp-config' in b and '--mcp-config' not in b, 'utan slug inga MCP:er'
    # provet använde flödets egna argument: samma --setting-sources, --settings (kundvakten) och --mcp-config
    sista = (FAKE / 'sessionsprov').read_text().splitlines()[-1]
    for del_ in ('--setting-sources project,local', 'kundvakt.py', '--mcp-config %s' % (KOPIA / 'kontroller' / 'mcp' / 'mobbin.json'),
                 '--permission-mode dontAsk'):
        assert del_ in sista, (del_, sista[:300])
    # helbygget laddar ingen MCP och prövar inga ateljésessioner
    kvb = sk.kor_kontroll(slug, 'bygge')
    assert not [r for r in kvb['rader'] if r['grupp'] == 'åtkomst'] and kvb['roller'] == [], kvb['roller']


# ===== 6. kvittot per roll och kompetenskvittot i tillståndsorden =====

@fall('6 kvittot per roll: varje roll i metodkartan med det tilldelade och åtkomsten; kompetenskvittot i tillståndsorden')
def _roller():
    slug = 'k6-roller'
    kund(slug)
    kv = sk.kor_kontroll(slug, 'ny')
    k = kompetens.tolka()
    roll = {r['roll']: r for r in kv['roller']}
    assert set(roll) == set(k), (set(roll), set(k))
    for kid, x in k.items():
        r = roll[kid]
        assert r['tilldelat']['mcp'] == x['mcp'] and set(r['atkomst']['mcp']) == set(x['mcp']) and r['tilldelat']['verktyg'] == x['verktyg'], r
        assert r['atkomst']['skills']['i_sessionen'] == r['atkomst']['skills']['av'], r['atkomst']['skills']
        assert all(m['tillstand'] == 'provat' for m in r['atkomst']['mcp'].values()) and r['anvandning'] == 'ej_observerat', r
    md = kvitto_md(slug)
    assert '## Kompetensen per roll' in md and all('(%s)' % kid in md for kid in k), md[-1500:]
    # en skill som sessionen inte laddar syns som blockerad hos sina roller
    init = json.loads((FAKE / 'init-med').read_text())
    init['skills'] = [s for s in init['skills'] if s != 'better-layout']
    (FAKE / 'init-med').write_text(json.dumps(init) + '\n')
    glom('prov:session')
    try:
        roll = {r['roll']: r for r in sk.kor_kontroll(slug, 'ny')['roller']}
    finally:
        skriv_init()
        glom('prov:session')
    assert roll['responsiv']['atkomst']['skills']['saknas'] == ['better-layout'] and roll['responsiv']['atkomst']['tillstand'] == 'blockerat'
    # kompetenskvittot: ett läskvitto är belägg för läsning, inte för tillämpning; inte gjort skiljs från inte observerat
    filer = kompetens.lasfiler('skapa')
    sett = kompetens.tillstand({'verifierad': True, 'lasta': filer, 'saknas': [], 'valda': [], 'skill_anrop': [], 'mcp_anrop': {}}, 'skapa')
    blind = kompetens.tillstand({'verifierad': False}, 'skapa')
    for r in sett:
        assert r['karna']['tillstand'] == kompetens.LASKVITTO and r['tillampning'] == kompetens.TILLSTAND['ej_observerat'], r
        assert all(m['tillstand'] == kompetens.TILLSTAND['ej_gjort'] for m in r['mcp'].values()), r
    assert all(m['tillstand'] == kompetens.TILLSTAND['ej_observerat'] for r in blind for m in r['mcp'].values())
    med_anrop = kompetens.tillstand({'verifierad': True, 'lasta': filer, 'mcp_anrop': {'mcp__mobbin__search_screens': 2}}, 'skapa')
    assert {r['roll']: r['mcp'].get('mobbin', {}).get('tillstand') for r in med_anrop}['innehall'] == kompetens.TILLSTAND['anvant']


# ===== 8. tåligheten =====

@fall('8 en oväntad form i underlaget eller ett sessionsprov som kastar stoppar aldrig starten')
def _talig():
    slug = 'k8-form'
    u = researchat(slug)
    (u / 'atelje' / 'FORSKNING.json').write_text(json.dumps({'tid': T1, 'nytt': ['fel form'], 'fore': 'fel form'}))
    st = json.loads((u / 'atelje' / 'STATUS.json').read_text())
    (u / 'atelje' / 'STATUS.json').write_text(json.dumps(dict(st, tider=['fel form'])))
    kv = sk.kor_kontroll(slug, 'fortsatt')
    r = referensrader(kv)
    assert kv['status'] != 'stoppad' and len(r) == 1, (kv['stoppar'], r)
    assert r[0]['resultat'] == 'fel' and 'inget användbart material' in r[0]['detalj'], 'research utan material stod som använd: %s' % r[0]
    orig = vl.prova_sessionen

    def kastar(k):
        raise RuntimeError('provets fel')
    vl.prova_sessionen = kastar
    try:
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        vl.prova_sessionen = orig
    rad = {r_['namn']: r_ for r_ in kv['rader']}
    assert kv['status'] != 'stoppad' and rad['Mobbin i ateljéns session']['resultat'] == 'okand', (kv['stoppar'], rad.get('Mobbin i ateljéns session'))
    assert 'provets fel' in rad['Mobbin i ateljéns session']['detalj'] and kv['roller'], rad['Mobbin i ateljéns session']


# ===== 7. en källa för tjänsternas verktyg =====

@fall('7 en källa: kor.sh läser tjänsternas verktyg ur TJANSTER, och metodkartans beslut prövas mot listan')
def _en_kalla():
    kor = (KOPIA / 'kor.sh').read_text()
    assert not re.search(r'mcp__(mobbin__search|refero__refero_)', kor), 'kor.sh har en egen lista över tjänsternas verktyg'
    m = re.search(r"tjanstens_verktyg\(\) \{\n  \"\$ROOT/\.venv/bin/python\" -B -c '(?P<kod>.*?)' \"\$ROOT\" \"\$1\"\n\}", kor, re.S)
    assert m and 'tjanstens_verktyg mobbin' in kor and 'tjanstens_verktyg refero' in kor, 'kor.sh läser inte TJANSTER'
    for t in ('mobbin', 'refero'):
        r = subprocess.run([sys.executable, '-B', '-c', m.group('kod'), str(KOPIA), t], capture_output=True, text=True, timeout=60)
        assert r.returncode == 0 and r.stdout.split() == referenstjanster.TJANSTER[t]['verktyg'], (t, r.stdout, r.stderr[-300:])
    karta = (KOPIA / 'kunskap' / 'metodkarta.md').read_text()
    assert kompetens.tjanstverktyg_fel(karta) == [] and kompetens.prova(karta) == [], kompetens.prova(karta)
    fel = kompetens.tjanstverktyg_fel(re.sub(r'(?m)^search_flows: uppgift.*\n', '', karta))
    assert any('search_flows' in f and 'kundvakten' in f for f in fel), fel
    fel = kompetens.tjanstverktyg_fel(karta.replace('refero_search_apps: ingen uppgift —', 'refero_search_apps: uppgift —'))
    assert any('refero_search_apps' in f and 'släpper det inte' in f for f in fel), fel
    fel = kompetens.tjanstverktyg_fel(karta.replace('; prövat 2026-10-07', ''))
    assert any('refero_search_apps' in f and 'provdatum' in f for f in fel), fel


print('startkvittots prov: %d fel%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
