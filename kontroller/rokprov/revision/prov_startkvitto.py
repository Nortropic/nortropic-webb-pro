#!/usr/bin/env python3
"""prov_startkvitto.py — startkvittots betydelse och sessionernas verkliga åtkomst (ägarens uppdrag 2026-10-07, punkt 2, 3
och 10, ordagrant i minnet; granskningen GR-20261007-r102), i en isolerad kopia av repot med falska nät, modeller och
claude:

1. research som inte körts: referensunderlaget står som planerat i researchen, förutsättningarna prövas, och inget
   saknat underlag gör kvittot rött; förra körningens research gäller inte en ny start (M01);
2. giltigt underlag efter researchen utan REFERENSER.md godtas; fel, en research som föll, en torrkörning, tomma
   tjänster och uteblivna bilder står som blockerade, aldrig som använda (2b); återanvänt material står som
   tillgängligt med sin tid, och en tjänst som researchen aldrig frågade och tomt uppdragsmaterial är brister (2c);
3. en tom eller inaktuell referensfil godtas inte (den äldre utforskningens REFERENSER.md, och kandidatflödets research
   från en tidigare körning), helbygget prövar VINNARE.json, och det som inte prövas står inte under Bekräftat;
4. upptäckt men otillåtet verktyg: "ingen uppgift" med metodkartans beslut och "nytt, obedömt" med åtgärd, aldrig
   "okänd", och inget av dem gör kvittot mer begränsat; ett verktyg med beslutet uppgift som kundvakten inte släpper
   och ett tilldelat verktyg som tjänsten tappat är fel;
5. en tilldelad tjänst som sessionen inte når står som "tilldelad men åtkomst saknas", inte ok: ateljéns argument ger
   Mobbin utan att Refero faller bort, startkontrollen prövar med just de argumenten, och Referos åtgärd ger aldrig
   sessionerna nyckeln;
6. kvittot per roll: varje roll i metodkartan med det tilldelade och åtkomsten i sessionen, och kompetenskvittot i
   tillståndsorden: ett läskvitto är belägg för läsning, ett tomt MCP-svar är inget material, och en session utan
   tjänsten är blockerad (också hela vägen genom observatören);
7. en källa: kor.sh läser tjänsternas verktyg ur referenstjanster.TJANSTER, och metodkartans beslut prövas mot listan;
8. tåligheten: en oväntad form i underlaget, ett undantag i åtkomsten eller ett sessionsprov som kastar stoppar aldrig
   starten, och research utan material står aldrig som använd;
9. körvägen följer ateljéns läge, och ett prov som inte gjorts är inte observerat;
10. kundvakten stoppar personnamn ur underlaget (personfälten och "Förnamn Efternamn" i briefen och texten), utan
    falsklarm för vanliga ord med stor bokstav;
11. Mobbins search_screens går bara med mode standard (deep kostar krediter), och prompterna säger det.

    .venv/bin/python kontroller/rokprov/revision/prov_startkvitto.py <repo>

Fallen 1–5 var röda mot main 84c6994. Fallen för granskningens rättelser (B1, B3–B6, K4, K6, K8, K9) var röda mot
7add728; fallen för de överlevande mutationerna (B2) fäller dem. Varje fall redovisas för sig på stderr; slutkod 1 när
något fall föll. Ingenting skrivs i repots underlag/ eller kunder/, och inga privata data läses.
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
        if REFERO.get('fel'):
            raise refero_mcp.ReferoFel('provets fel: Refero svarar inte')
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


def researchat(slug, forsk_tid=T1, start=T0, tjanster=None, bild_saknas=False, nytt=None, fore=None, tj_tid=None, um='full', forsk_fel=None,
               torr=False):
    """Kandidatflödet efter researchen: STATUS.json, FORSKNING.json och .md, referenspaketet, tjänsternas rapport med
    bilderna på disken och uppdragens material (um: full, tomt eller None), utan REFERENSER.md."""
    u = kund(slug)
    a = u / 'atelje'
    a.mkdir(parents=True, exist_ok=True)
    (a / 'STATUS.json').write_text(json.dumps({'slug': slug, 'steg': 'skapa', 'lage': 'fortsatt', 'kandidatflode': True, 'tider': {'start': start}, 'faser': {}}))
    (a / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': T1, 'lage': 'skiss', 'kandidater': {'k01': {'titel': 'Ett förslag'}}}))
    (a / 'FORSKNING.json').write_text(json.dumps({'tid': forsk_tid, 'fel': forsk_fel, 'slappta': [], 'antaganden': [], 'fragor': [], 'sajter': [],
                                                  'nytt': nytt if nytt is not None else {'paket': 'paket-v01', 'sajter': ['ett', 'tva'], 'tjanster': forsk_tid},
                                                  'fore': fore if fore is not None else {'paket': None, 'tjanster': None}}))
    (a / 'FORSKNING.md').write_text('# Research före kandidatplanen\n')
    p = u / 'referenser' / 'paket-v01'
    p.mkdir(parents=True, exist_ok=True)
    kandidater = []
    for namn in ('ett', 'tva'):  # sajternas sparade bilder ligger relativt paketet
        (p / namn / '01-start').mkdir(parents=True, exist_ok=True)
        (p / namn / '01-start' / 'vy-390-forsta.png').write_bytes(b'\x89PNG\r\n\x1a\nbild')
        kandidater.append({'namn': namn, 'ok': True, 'sidor': [{'sida': '/', 'katalog': namn + '/01-start', 'ok': True,
                                                                 'filer': [namn + '/01-start/vy-390-forsta.png', namn + '/01-start/EXTRAKT.md']}]})
    (p / 'PAKET.json').write_text(json.dumps({'version': 'paket-v01', 'tid': T0, 'kandidater': kandidater}))
    (p / 'PAKET.md').write_text('# Referenspaket\n')
    tjd = u / 'referenser' / 'tjanster'
    for t in ('refero', 'mobbin'):
        (tjd / t).mkdir(parents=True, exist_ok=True)
        (tjd / t / 'a.jpg').write_bytes(b'\xff\xd8\xffbild')
    tj = tjanster if tjanster is not None else {
        'refero': {'fragor': [{'fraga': 'x'}], 'anrop': {'mcp__refero__refero_search_screens': 2}, 'stilar': [], 'bilder': 1, 'ok': True, 'anmarkningar': [],
                   'traffar': [{'id': 'r1', 'fil': 'referenser/tjanster/refero/a.jpg'}] + ([{'id': 'r2', 'fil': None, 'fel': 'ingen bild'}] if bild_saknas else [])},
        'mobbin': {'fragor': [{'fraga': 'y'}], 'anrop': {'mcp__mobbin__search_screens': 1}, 'stilar': [], 'bilder': 1, 'ok': True, 'anmarkningar': [],
                   'traffar': [{'id': 'm1', 'fil': 'referenser/tjanster/mobbin/a.jpg'}]}}
    (tjd / 'TJANSTER.json').write_text(json.dumps({'schema': 2, 'tid': tj_tid or forsk_tid, 'torr': torr, 'tjanster': tj}))
    (tjd / 'TJANSTER.md').write_text('# Referenstjänster\n')
    (u / 'referenser' / 'uppdrag' / 'mobbin').mkdir(parents=True, exist_ok=True)
    (u / 'referenser' / 'uppdrag' / 'mobbin' / 'c.jpg').write_bytes(b'\xff\xd8\xffbild')
    if um == 'full':
        (a / 'UPPDRAGSMATERIAL.json').write_text(json.dumps({'tid': T2, 'mobbin': {'ok': True, 'bilder': 1}, 'kandidater': {
            'k01': {'mobbin_fraga': 'contact form', 'mobbin': [{'fil': 'underlag/%s/referenser/uppdrag/mobbin/c.jpg' % slug, 'titel': 't', 'beskrivning': 'b'}]}}}))
    elif um == 'tomt':
        (a / 'UPPDRAGSMATERIAL.json').write_text(json.dumps({'tid': T2, 'mobbin': {'ok': True, 'bilder': 0}, 'kandidater': {'k01': {}, 'k02': {}}}))
    return u


def rad_(kv, namn):
    return next((r for r in kv['rader'] if r['namn'] == namn), None)


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
    # M01: en ny start medan förra körningens FORSKNING.json ligger kvar. Arbetaren skriver den nya körningens STATUS.json
    # (steg startkontroll, utan tider) och kör startkontrollen före arkiveringen; förra körningens research gäller inte
    slug = 'k1-forra'
    u = researchat(slug)
    (u / 'atelje' / 'STATUS.json').write_text(json.dumps({'slug': slug, 'startad': vl.nu(), 'steg': 'startkontroll', 'lage': 'ny',
                                                          'pid': os.getpid(), 'faser': {}, 'kandidatflode': True}))
    r = referensrader(sk.kor_kontroll(slug, 'ny'))[0]
    assert r['resultat'] == 'planerat' and r['tillstand'] == 'planerat', 'förra körningens research räknades som den här startens: %s' % r
    # M13: före researchen är en tjänst som faller ett hinder, inte bara "inte bekräftad"
    REFERO['fel'] = True
    glom('prov:refero')
    try:
        r = referensrader(sk.kor_kontroll('k1-fore', 'ny'))[0]
    finally:
        REFERO.pop('fel', None)
        glom('prov:refero')
    assert r['resultat'] == 'fel' and 'Refero (direkt) fungerar inte' in r['detalj'], r


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
    assert r['resultat'] == 'fel' and r['tillstand'] == 'blockerat', 'blockerat underlag fick tillståndet %s' % r.get('tillstand')
    assert 'Mobbin: inga verkliga anrop' in r['detalj'] and 'Mobbin med' not in r['detalj'], r
    (u / 'referenser' / 'tjanster' / 'refero' / 'a.jpg').unlink()  # en levererad bild som inte finns på disken
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert 'Refero: 1 bilder saknas på disken' in r['detalj'] and r['tillstand'] == 'blockerat', r
    assert 'Refero med' not in r['detalj'].split('blockerat eller misslyckat')[0], 'en tjänst utan bilder på disken stod som använd: %s' % r
    # M09: en research som föll; M10: en torrkörning av tjänsterna; M11: uppdragens skärmar som saknas på disken
    r = referensrader(sk.kor_kontroll(researchat('k2b-foll', forsk_fel='sessionen föll (kod 1)') and 'k2b-foll', 'fortsatt'))[0]
    assert r['resultat'] == 'fel' and r['tillstand'] == 'blockerat' and 'researchen föll' in r['detalj'], r
    r = referensrader(sk.kor_kontroll(researchat('k2b-torr', torr=True) and 'k2b-torr', 'fortsatt'))[0]
    assert r['resultat'] == 'fel' and 'torrkörning' in r['detalj'], r
    u = researchat('k2b-uppdrag')
    (u / 'referenser' / 'uppdrag' / 'mobbin' / 'c.jpg').unlink()
    r = referensrader(sk.kor_kontroll('k2b-uppdrag', 'fortsatt'))[0]
    assert r['resultat'] == 'fel' and '1 av uppdragens Mobbin-skärmar saknas på disken' in r['detalj'], r
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


@fall('2c återanvänt, uteblivet och tomt material står aldrig som använt med resultat (granskningen GR-20261007-r102, B1)')
def _ateranvant_och_tomt():
    def anvant(r):  # delen av detaljen som säger använt med resultat
        d = r['detalj']
        return d.split('använt med resultat: ', 1)[1].split('. ', 1)[0] if 'använt med resultat: ' in d else ''
    # S1: skissresearchen återanvände förra researchens paket och tjänsternas rapport från 2026-09-01; inget nytt hämtades
    slug = 'k2c-s1'
    researchat(slug, nytt={'paket': None, 'sajter': [], 'tjanster': None}, fore={'paket': 'paket-v01', 'tjanster': '2026-09-01T10:00:00Z'},
               tj_tid='2026-09-01T10:00:00Z', um=None)
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['tillstand'] == 'tillgangligt' and not anvant(r), 'återanvänt material stod som använt med resultat: %s' % r
    assert 'återanvänd' in r['detalj'] and '2026-09-01T10:00:00Z' in r['detalj'] and 'återanvänt ur en tidigare research' in r['detalj'], r
    # S2: researchen frågade bara Refero, aldrig Mobbin
    slug = 'k2c-s2'
    researchat(slug, tjanster={'refero': {'fragor': [{'fraga': 'x'}], 'anrop': {'mcp__refero__refero_search_screens': 2}, 'stilar': [], 'bilder': 1,
                                          'ok': True, 'traffar': [{'id': 'r1', 'fil': 'referenser/tjanster/refero/a.jpg'}]}})
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'delvis' and 'researchen frågade aldrig Mobbin' in r['detalj'] and 'Mobbin med' not in anvant(r), r
    assert 'tilldelar Mobbin rollerna' in r['detalj'], 'en ofrågad tjänst saknar konsekvensen: %s' % r
    # S3: researchen ställde inga tjänstefrågor alls
    slug = 'k2c-s3'
    researchat(slug, nytt={'paket': 'paket-v01', 'sajter': ['ett', 'tva'], 'tjanster': None})
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'delvis' and 'frågade aldrig Refero' in r['detalj'] and 'frågade aldrig Mobbin' in r['detalj'], r
    assert 'Refero' not in anvant(r) and 'Mobbin med' not in anvant(r), r
    # uppdragens material utan ett enda stilpaket eller en enda skärm
    slug = 'k2c-tomt'
    researchat(slug, um='tomt')
    r = referensrader(sk.kor_kontroll(slug, 'fortsatt'))[0]
    assert r['resultat'] == 'delvis' and 'uppdragens material är tomt' in r['detalj'] and 'uppdragens material' not in anvant(r), r


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
    # K4: det som inte prövas står inte under Bekräftat: en provstart och helbyggets nödväg utan ateljé
    r = referensrader(sk.kor_kontroll(slug, 'prov'))
    assert r[0]['resultat'] == 'ej_tillampligt' and r[0]['tillstand'] == 'ej_observerat', r
    os.environ['NWP_ATELJE'] = 'av'
    try:
        (u / 'atelje' / 'VINNARE.json').unlink()
        r = referensrader(sk.kor_kontroll(slug, 'bygge'))
    finally:
        os.environ.pop('NWP_ATELJE', None)
    assert r[0]['resultat'] == 'ej_tillampligt' and 'nödvägen' in r[0]['detalj'], r
    assert '## Gäller inte den här starten' in kvitto_md(slug, 'STARTKVITTO-BYGGE'), kvitto_md(slug, 'STARTKVITTO-BYGGE')[:300]


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
    karta = KOPIA / 'kunskap' / 'metodkarta.md'
    fore_karta = karta.read_text()
    skill = KOPIA / '.claude' / 'skills' / 'slid'
    try:
        # M23 och K6: ett upptäckt verktyg med beslutet uppgift som kundvakten inte släpper är ett fel, inte "ingen uppgift"
        karta.write_text(fore_karta.replace('refero_search_apps: ingen uppgift —', 'refero_search_widgets: uppgift — provets rad\nrefero_search_apps: ingen uppgift —'))
        # M24: ett tilldelat verktyg som tjänsten inte längre har (refero_get_flow saknas i listan och i sessionen)
        REFERO['verktyg'] = [v for v in FLODETS_REFERO if v != 'refero_get_flow'] + ['refero_search_apps', 'refero_search_widgets']
        skriv_init()
        glom('prov:refero', 'prov:session')
        # M30: en skill utan roll vars namn bara är en del av ett ord i listan "Ingen uppgift i flödet" ("slides")
        skill.mkdir()
        (skill / 'SKILL.md').write_text('---\nname: slid\ndescription: provets skill\n---\n')
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        karta.write_text(fore_karta)
        shutil.rmtree(skill, ignore_errors=True)
        REFERO['verktyg'] = FLODETS_REFERO + ['refero_search_apps']
        skriv_init()
        glom('prov:refero', 'prov:session')
    w = rad_(kv, 'refero_search_widgets (Refero)') or {}
    assert w.get('resultat') == 'fel' and 'släpper det inte' in w.get('detalj', ''), w
    m = rad_(kv, 'Referos verktyg med uppgift') or {}
    assert m.get('resultat') == 'fel' and 'tilldelade men saknas hos Refero: refero_get_flow' in m.get('detalj', ''), m
    s = rad_(kv, 'skills utan roll eller skäl') or {}
    assert s.get('resultat') == 'nytt' and 'slid' in s.get('detalj', ''), s


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
    # M14: maskinens anslutning (claude mcp list) är tillgänglig, inte provad; K9: sessionens övriga MCP-servrar syns
    assert rad['mobbin']['tillstand'] == 'tillgangligt' and rad['refero']['tillstand'] == 'tillgangligt', rad['mobbin']
    ovr = rad.get('övriga MCP i ateljéns session') or {}
    assert ovr.get('resultat') == 'ingen_uppgift' and 'claude.ai Claude Docs' in ovr.get('detalj', ''), ovr
    # M19: en ansluten tjänst vars flödesverktyg saknas i sessionen är inte nådd
    init = json.loads((FAKE / 'init-med').read_text())
    init['tools'] = [v for v in init['tools'] if v != 'mcp__mobbin__search_sections']
    (FAKE / 'init-med').write_text(json.dumps(init) + '\n')
    glom('prov:session')
    try:
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        skriv_init()
        glom('prov:session')
    m = rad_(kv, 'Mobbin i ateljéns session') or {}
    assert m.get('resultat') == 'fel' and 'search_sections syns inte' in m.get('detalj', ''), m
    # B4: Referos åtgärd ger aldrig sessionerna nyckeln (session_miljo tar bort den; granskning 4, G15)
    init = json.loads((FAKE / 'init-med').read_text())
    init['mcp_servers'] = [s for s in init['mcp_servers'] if s['name'] != 'refero']
    init['tools'] = [v for v in init['tools'] if not v.startswith('mcp__refero__')]
    (FAKE / 'init-med').write_text(json.dumps(init) + '\n')
    glom('prov:session')
    try:
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        skriv_init()
        glom('prov:session')
    r_ = rad_(kv, 'Refero i ateljéns session') or {}
    assert r_.get('resultat') == 'fel' and 'tilldelad men åtkomst saknas' in r_.get('detalj', ''), r_
    assert 'mcp/refero.json' not in r_['detalj'] and 'med nyckeln' not in r_['detalj'] and 'huvudutcheckningen' in r_['detalj'], r_['detalj']


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
    # K8: skillverktyget saknar skillen, men dess filer läses med Read: tillgänglig, inte blockerad
    assert roll['responsiv']['atkomst']['skills']['saknas'] == ['better-layout'] and roll['responsiv']['atkomst']['tillstand'] == 'tillgangligt', roll['responsiv']['atkomst']
    # kompetenskvittot: ett läskvitto är belägg för läsning, inte för tillämpning; inte gjort skiljs från inte observerat
    filer = kompetens.lasfiler('skapa')
    sett = kompetens.tillstand({'verifierad': True, 'lasta': filer, 'saknas': [], 'valda': [], 'skill_anrop': [], 'mcp_anrop': {}}, 'skapa')
    blind = kompetens.tillstand({'verifierad': False}, 'skapa')
    for r in sett:
        assert r['karna']['tillstand'] == kompetens.LASKVITTO and r['tillampning'] == kompetens.TILLSTAND['ej_observerat'], r
        assert all(m['tillstand'] == kompetens.TILLSTAND['ej_gjort'] for m in r['mcp'].values()), r
    assert all(m['tillstand'] == kompetens.TILLSTAND['ej_observerat'] for r in blind for m in r['mcp'].values())
    T = kompetens.TILLSTAND

    def innehall(kv_, **kw):
        return {r['roll']: r for r in kompetens.tillstand(kv_, 'skapa', **kw)}['innehall']['mcp']['mobbin']
    # B3: ett lyckat anrop säger inte att svaret blev material. Ett sparat kvitto utan svarens utfall är inte observerat,
    # ett tomt svar är blockerat, och bara ett svar med innehåll är använt med resultat
    bas = {'verifierad': True, 'lasta': filer, 'mcp_anrop': {'mcp__mobbin__search_screens': 2}}
    assert innehall(bas)['tillstand'] == T['ej_observerat'], innehall(bas)
    assert innehall(dict(bas, mcp_utfall={'mcp__mobbin__search_screens': {'tomt resultat': 2}}))['tillstand'] == T['blockerat']
    assert innehall(dict(bas, mcp_utfall={'mcp__mobbin__search_screens': {'tomt resultat': 1, 'bild returnerad': 1}}))['tillstand'] == T['anvant']
    # en roll vars session aldrig fick tjänsten är blockerad med konsekvens, inte "inte gjort"
    utan = innehall({'verifierad': True, 'lasta': filer, 'mcp_anrop': {}}, mcp_lage={'refero': 'ansluten'})
    assert utan['tillstand'] == T['blockerat'] and 'tilldelad men åtkomst saknas' in utan['orsak'], utan
    assert innehall({'verifierad': True, 'lasta': filer, 'mcp_anrop': {}}, mcp_lage={'refero': 'ansluten', 'mobbin': 'ansluten'})['tillstand'] == T['ej_gjort']
    # hela vägen: kvittot ur ett transkript där sessionen hade Refero men inte Mobbin, och Referos enda svar var tomt
    import bildkedja
    sid = '0f0e0d0c-0b0a-4908-8706-050403020100'
    pr = TMP / 'projekt' / 'p'
    pr.mkdir(parents=True, exist_ok=True)

    def rad(**r):
        return json.dumps(r, ensure_ascii=False)
    T0_ = '2026-10-07T08:00:%02d.000Z'
    (pr / (sid + '.jsonl')).write_text('\n'.join([
        rad(type='user', timestamp=T0_ % 0, message={'role': 'user', 'content': 'uppdraget'}),
        rad(type='attachment', attachment={'type': 'deferred_tools_delta', 'addedNames': ['mcp__refero__refero_search_screens'], 'pendingMcpServers': [],
                                          'needsAuthMcpServers': [], 'failedMcpServers': []}),
        rad(type='assistant', timestamp=T0_ % 1, message={'role': 'assistant', 'model': 'claude-fable-5-1', 'content': [
            {'type': 'tool_use', 'id': 't1', 'name': 'mcp__refero__refero_search_screens', 'input': {'query': 'carpenter hero', 'platform': 'web'}}]}),
        rad(type='user', timestamp=T0_ % 2, message={'role': 'user', 'content': [
            {'type': 'tool_result', 'tool_use_id': 't1', 'content': [{'type': 'text', 'text': '{"pagination":{"count":0},"records":[]}'}]}]})]) + '\n')
    spara_projekt = bildkedja.PROJEKT
    bildkedja.PROJEKT = TMP / 'projekt'
    try:
        kv_ = kompetens.kvitto([sid], 'skapa')
    finally:
        bildkedja.PROJEKT = spara_projekt
    assert kv_['verifierad'] and kv_['mcp_anrop'] == {'mcp__refero__refero_search_screens': 1}, kv_
    roll_ = {r['roll']: r for r in kv_['tillstand']}
    assert roll_['typografi']['mcp']['refero']['tillstand'] == T['blockerat'] and 'tomt resultat' in roll_['typografi']['mcp']['refero']['orsak'], roll_['typografi']
    assert roll_['innehall']['mcp']['mobbin']['tillstand'] == T['blockerat'] and 'tilldelad men åtkomst saknas' in roll_['innehall']['mcp']['mobbin']['orsak'], roll_['innehall']
    assert roll_['innehall']['karna']['tillstand'] == T['ej_gjort'], 'ingen fil läst ska vara inte gjort: %s' % roll_['innehall']['karna']


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
    # M27: ett undantag i referensunderlaget (en oväntad form i TJANSTER.json) blir en rad, aldrig ett stopp
    u = researchat('k8-undantag')
    tj = json.loads((u / 'referenser' / 'tjanster' / 'TJANSTER.json').read_text())
    tj['tjanster']['refero']['anrop'] = {'mcp__refero__refero_search_screens': 'många'}
    (u / 'referenser' / 'tjanster' / 'TJANSTER.json').write_text(json.dumps(tj))
    kv = sk.kor_kontroll('k8-undantag', 'fortsatt')
    r = rad_(kv, 'referensunderlaget') or {}
    assert kv['status'] != 'stoppad' and r.get('resultat') == 'okand' and 'kunde inte prövas' in r.get('detalj', ''), (kv['stoppar'], r)
    # M28: ett undantag i åtkomstraderna och rollerna blir en rad och ett besked, aldrig ett stopp
    orig_atk = sk.mcp_atkomst

    def kastar_atk(sess, tjanst):
        raise RuntimeError('provets fel i åtkomsten')
    sk.mcp_atkomst = kastar_atk
    try:
        kv = sk.kor_kontroll(slug, 'ny')
    finally:
        sk.mcp_atkomst = orig_atk
    r = rad_(kv, 'åtkomsten i ateljéns session') or {}
    assert kv['status'] != 'stoppad' and r.get('resultat') == 'okand' and 'provets fel i åtkomsten' in r.get('detalj', ''), (kv['stoppar'], r)
    assert kv['roller'] is None and 'provets fel i åtkomsten' in kv.get('roller_fel', '') and 'Kvittot per roll kunde inte göras' in kvitto_md(slug)


# ===== 9. körvägen och det som inte prövats =====

@fall('9 körvägen följer ateljéns läge (valda, putsa och fortsättningen efter valet), och ett prov som inte gjorts är inte observerat')
def _korvagen():
    slug = 'k9-vag'
    u = kund(slug)
    (u / 'atelje').mkdir(parents=True, exist_ok=True)
    (u / 'atelje' / 'STATUS.json').write_text(json.dumps({'slug': slug, 'steg': 'fel', 'faser': {'valj': {'klar': T1}}}))
    assert sk.korvag(slug, 'valda')['id'] == 'kandidatflodet', 'M02: --valda gäller alltid kandidatflödet'
    v = sk.korvag(slug, 'putsa')
    assert v['id'] == 'aldre' and v['fas'] == 'efter_val', ('M04: --putsa är den äldre vägen', v)
    v = sk.korvag(slug, 'fortsatt')
    assert v['id'] == 'aldre' and v['fas'] == 'efter_val', ('M05: --fortsatt efter valet i den äldre vägen', v)
    # M15: utan prov är förmågan inte observerad, aldrig provad och fungerande (sparade prov glöms först)
    glom('prov:refero', 'prov:vakt', 'prov:session')
    kv = sk.kor_kontroll(slug, 'ny', prova=False)
    for namn in ('Refero (direkt)', 'kundvaktens mekanik', 'Mobbin i ateljéns session'):
        r = rad_(kv, namn) or {}
        assert r.get('tillstand') == 'ej_observerat' and r.get('resultat') != 'ok', (namn, r)
    assert sk.provtillstand('okand') == 'ej_observerat' and sk.provtillstand('ok') == 'provat' and sk.provtillstand('fel') == 'blockerat'


# ===== 10. personnamn ur underlaget (B5) =====

@fall('10 kundvakten stoppar personnamn ur underlaget, utan falsklarm för vanliga ord med stor bokstav')
def _personnamn():
    slug = 'k10-namn'
    u = kund(slug)
    (u / 'BRIEF.md').write_text('# Brief\n\n## Primär Handling\n\nÄgaren Anna Svensson svarar själv. Ring Per-Olof Lindqvist om offert.\n'
                                'Besökarna hittar oss via Google Maps; Apple Pay används inte. En tydlig Call To Action. Vi arbetar i Norra Sverige.\n'
                                'Material Design passar inte. Knappen "Get Started" och "Request A Quote".\n| Fält | Värde |\n|---|---|\n'
                                '| Kontakt | Erik Lund |\n')
    (u / 'TEXTUNDERLAG.md').write_text('# Text\n\n”Snabbt och snyggt jobb!” — Karin Ström, kund. Firman startades av **Lena Berg**.\n')
    v = json.loads((u / 'VERKSAMHET.json').read_text())
    (u / 'VERKSAMHET.json').write_text(json.dumps(dict(v, kontaktperson={'namn': 'Olle Holmqvist'}, omdomen=[{'namn': 'Sara Ek', 'text': 'Bra'}])))

    def prov(verktyg, inn):
        return kundvakt.provning(slug, KOPIA / 'underlag', {'tool_name': verktyg, 'tool_input': inn})
    skarm = 'mcp__refero__refero_search_screens'
    for inn in ({'query': 'anna svensson portfolio', 'platform': 'web'}, {'query': 'Karin Ström review card', 'platform': 'web'},
                {'query': 'KarinStröm testimonial', 'platform': 'web'}, {'query': 'karin%20str%C3%B6m', 'platform': 'web'},
                {'query': 'Per-Olof Lindqvist carpentry', 'platform': 'web'}, {'query': 'Lena Bergs firma', 'platform': 'web'},
                {'query': 'olle holmqvist', 'platform': 'web'}, {'query': 'holmqvist', 'platform': 'web'}, {'query': 'review from Sara Ek', 'platform': 'web'}):
        skal = prov(skarm, inn) or ''
        assert 'personnamn' in skal, ('träffen släpptes igenom', inn, skal)
    skal = prov('mcp__mobbin__search_sections', {'query': 'testimonial section', 'task_intent': 'site for Anna Svensson carpentry'}) or ''
    assert 'personnamn' in skal, skal
    skal = prov('mcp__refero__refero_get_screen_image', {'image_url': 'https://images.refero.design/s/anna-svensson.jpg'}) or ''
    assert 'adress' in skal, skal
    for inn in ({'query': 'google maps embed on contact page', 'platform': 'web'}, {'query': 'apple pay checkout', 'platform': 'web'},
                {'query': 'call to action hero section', 'platform': 'web'}, {'query': 'material design cards', 'platform': 'web'},
                {'query': 'get started button', 'platform': 'web'}, {'query': 'request a quote form', 'platform': 'web'},
                {'query': 'carpenter portfolio with project gallery', 'platform': 'web'}):
        assert prov(skarm, inn) is None, ('falsklarm', inn, prov(skarm, inn))
    # utan personnamn i underlaget är kundvakten som förut: kundens namn stoppas, ett generiskt anrop går
    assert prov(skarm, {'query': 'provfirman homepage', 'platform': 'web'}) and prov(skarm, {'query': 'builder site hero', 'platform': 'web'}) is None


# ===== 11. Mobbins krediter (B6) =====

@fall('11 Mobbins search_screens går bara med mode standard, och prompterna säger det')
def _mobbins_lage():
    slug = 'k11-lage'
    kund(slug)
    skarm = 'mcp__mobbin__search_screens'

    def prov(inn, verktyg=skarm):
        return kundvakt.provning(slug, KOPIA / 'underlag', {'tool_name': verktyg, 'tool_input': inn})
    for inn in ({'query': 'contact form page', 'platform': 'web'}, {'query': 'contact form page', 'platform': 'web', 'mode': 'deep'},
                {'query': 'contact form page', 'platform': 'web', 'mode': ''}):
        assert 'mode' in (prov(inn) or ''), ('deep eller utan mode släpptes igenom', inn)
    assert prov({'query': 'contact form page', 'platform': 'web', 'mode': 'standard'}) is None
    assert prov({'query': 'contact form page', 'platform': 'web', 'mode': 'fast'}) is None, 'fast är verktygets äldre namn på standard'
    assert prov({'query': 'onboarding with steps', 'platform': 'web'}, 'mcp__mobbin__search_flows') is None, 'search_flows har inget mode'
    assert prov({'query': 'pricing section'}, 'mcp__mobbin__search_sections') is None, 'search_sections har inget mode'
    # prompterna: skaparnas roller med Mobbin och tjänstesessionen
    rader = '\n'.join(kompetens.prompt_rader('skapa', slug, 'k01'))
    assert 'search_screens kräver mode "standard"' in rader and 'personnamn, citat' in rader, rader[-800:]
    assert 'search_screens kräver mode "standard"' in referenstjanster.prompt_for('mobbin', [{'fraga': 'x', 'syfte': '', 'typ': 'skarm'}], 'Byggfirma')
    assert 'pröva också mobile' not in referenstjanster.prompt_for('refero', [{'fraga': 'x', 'syfte': '', 'typ': 'skarm'}], 'Byggfirma')


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
        # M25: anslutningsfilen för tjänsten läser just den tjänstens verktyg
        gren = re.search(r'"\$ROOT/kontroller/mcp/%s\.json"\)\n\s*TJ="\$\(tjanstens_verktyg (\w+)\)"' % t, kor)
        assert gren and gren.group(1) == t, (t, gren.group(1) if gren else None)
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
