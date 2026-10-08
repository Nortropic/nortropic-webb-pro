#!/usr/bin/env python3
"""prov_rorelse.py — Motion AI Kit (den fria delen), GSAP som låst beroende och valet CSS, Motion eller GSAP per beteende
(ägarens uppdrag 2026-10-07, punkt 5C, och förtydligandet samma dag om aktivering, faktiska anrop och tre nivåer;
BESLUT.md, tillägget 2026-10-07 om Motion AI Kit och GSAP), i en isolerad kopia av repot utan nät och utan sessioner:

1. skillarna finns med KALLA.md: motion (11 upstream-filer, beslutstabellen css-or-motion.md) och gsap (åtta nästlade
   SKILL.md, llms.txt, LICENSE och vårt index), varje upstream-fil byte för byte lika den blob KALLA.md anger, och
   kontroller/mcp/motion.json bär bara den fria servern;
2. MCP-konfigurationen ges rollen: ateljéns argument bär motion.json efter mobbin.json utan strikt läge, rollen rorelse
   har mcp refero och motion, prompten säger vad som aktiveras med skillverktyget och vad som läses med Read, och
   startkontrollen visar Motion som tilldelad tjänst (provad, eller "tilldelad men åtkomst saknas"), aldrig som övrig
   anslutning, med verktygsbesluten ur metodkartan (uppgift, ingen uppgift, nytt);
3. kundvakten släpper generiska frågor till search-motion-docs och stoppar kundens namn, ort och personnamn ur
   underlaget, ett annat verktyg hos Motion, och krokens matcher täcker tjänsten; Refero och Mobbin går som förut;
4. GSAP-sidan i provbygget: rökprovets sida /rorelse/ med gsap.matchMedia för båda lägena och giltiga SEO-längder,
   rökprovets Playwright-kontroll, gsap 3.15.0 i båda mallarnas package.json och lås utan installationsskript, och
   beroendetabellen (det dynamiska provet är rökprovets eget steg);
5. metodkartan ger valet och kvittot visar det: rollen rorelses uppgift och visar, passchemats aktivering och teknikval,
   passets uppgift och prompt, kvittots tillämpning som sessionens redovisning (inte observation) och de tre nivåerna
   aktivering, användning och bedömd kvalitet var för sig, också ur ett transkript där en aktivering misslyckades;
6. metodlåset: metod.py och kompetens.py prövar kartan, och en ändrad ny källa stoppar leveransen;
7. städregeln känner provets tempprefix;
8. dokumentationen: beroenden.md (gsap-raden, Framer Motion-aliaset, valet), metodkartans lista Ingen uppgift,
   registrets ersättningsrad och BESLUT-posten;
9–12. hela MCP-avtrycket, ärliga nivåer, sparade passutfall och obesvarad Skill.

    .venv/bin/python kontroller/rokprov/revision/prov_rorelse.py <repo>

Varje fall redovisas för sig på stderr; slutkod 1 när något fall föll. Jämförelsen mot bas och mutationsutfall
redovisas med den granskade versionen i arbetsrapporten. Ingenting skrivs i repots underlag/ eller kunder/, och inga privata data läses: den syntetiska kunden finns
bara i provets kopia, och inga nästlade sessioner startas.
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
TMP = Path(tempfile.mkdtemp(prefix='nwp-rorelse-')).resolve()
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
os.environ['CLAUDE_CONFIG_DIR'] = str(TMP / 'claude')  # transkripten (bildkedja.PROJEKT) i provets katalog, aldrig ägarens
os.environ['NWP_KORREGISTER'] = str(TMP / 'korregister')
os.environ['NWP_STADNING'] = 'av'
os.environ['NWP_CLAUDE_BIN'] = str(TMP / 'claude-saknas')  # ingen session startas i provet
for k_ in ('NWP_SLUG', 'NWP_STARTKONTROLL', 'NWP_KANDIDATFLODE', 'NWP_ATELJE', 'NWP_MCP_CONFIG'):
    os.environ.pop(k_, None)

sys.path.insert(0, str(KOPIA / 'kontroller'))
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402
import kundvakt  # noqa: E402
import metod  # noqa: E402
import referenstjanster  # noqa: E402
import stadning  # noqa: E402
import startkontroll as sk  # noqa: E402

korregister.registrera_tmp(TMP, 'prov_rorelse')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)
SLUG = 'kv-rorelse'
T = kompetens.TILLSTAND
MOTION_VERKTYG = 'mcp__motion__search-motion-docs'
SKILLS = KOPIA / '.claude' / 'skills'


def skriv(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        p.write_bytes(text)
    else:
        p.write_text(text, encoding='utf-8')


def kund(slug=SLUG):
    """En syntetisk kund: verksamhet, brief med ett personnamn, domlogg, en kandidat med uppdrag och riktning."""
    u, k = atelje.UNDERLAG / slug, atelje.KUNDER / slug
    shutil.rmtree(u, ignore_errors=True)
    shutil.rmtree(k, ignore_errors=True)
    skriv(u / 'VERKSAMHET.json', json.dumps({'namn': 'Provfirman Trä AB', 'adress': {'ort': 'Exempelby'},
                                             'kontaktvagar': [{'typ': 'telefon', 'varde': '000-111 22 33'}]}))
    skriv(u / 'BRIEF.md', '# Brief\n\n## §2 Målgrupper och toppuppgifter\n\n1. Se liknande jobb före kontakt\n\n## §4 Primär handling\n\n'
                          'Ring. Ägaren Anna Svensson svarar.\n')
    skriv(u / 'DESIGNDOMAR.jsonl', json.dumps({'tid': '2026-10-02T10:00:00Z', 'kalla': 'ägaren', 'beslut': 'ny_riktning', 'text': 'pröva nya grundidéer'}) + '\n')
    d = kd.kdir(slug, 'k01')
    skriv(d / 'UPPDRAG.md', '# Uppdrag\n\nBesökaren vill se ett liknande jobb och ringa.\n')
    skriv(d / 'RIKTNING.md', 'Huvudreferens: Xref — kompositionen\n\n## Idén\n\nEn skiss.\n')
    skriv(d / 'STATUS.json', json.dumps({'id': 'k01', 'status': 'klar', 'titel': 'Uppdraget'}))
    sajt = kd.ksajt(slug, 'k01')
    skriv(sajt / 'package.json', '{}')
    skriv(sajt / 'src' / 'pages' / 'index.astro', '<h1>Skiss</h1>\n')
    return u


def rad(**r):
    return json.dumps(r, ensure_ascii=False)


def transkript(handelser, sid):
    """Ett transkript i Claude Codes radformat: (verktyg, input, svar) där svar är text, ('fel', text) eller None."""
    rader = [rad(type='user', timestamp='2026-10-07T10:00:00.000Z', message={'role': 'user', 'content': 'uppdraget'})]
    for i, (namn, inp, svar) in enumerate(handelser, 1):
        rader.append(rad(type='assistant', timestamp='2026-10-07T10:00:%02d.000Z' % (i % 60), message={
            'role': 'assistant', 'model': 'claude-prov', 'content': [{'type': 'tool_use', 'id': 't%d' % i, 'name': namn, 'input': inp}]}))
        if svar is None:
            continue
        fel = isinstance(svar, tuple) and svar[0] == 'fel'
        rader.append(rad(type='user', timestamp='2026-10-07T10:00:%02d.500Z' % (i % 60), message={'role': 'user', 'content': [
            dict({'type': 'tool_result', 'tool_use_id': 't%d' % i, 'content': [{'type': 'text', 'text': svar[1] if fel else svar}]},
                 **({'is_error': True} if fel else {}))]}))
    pr = bildkedja.PROJEKT / 'p'
    pr.mkdir(parents=True, exist_ok=True)
    (pr / (sid + '.jsonl')).write_text('\n'.join(rader) + '\n', encoding='utf-8')
    return sid


def vakt(slug, verktyg, indata):
    return kundvakt.provning(slug, atelje.UNDERLAG, {'tool_name': verktyg, 'tool_input': indata})


def blob_sha(p):
    return subprocess.run(['git', 'hash-object', str(p)], capture_output=True, text=True, check=True).stdout.strip()


# ===== 1. skillarna med KALLA.md =====
@fall('1 skillarna motion och gsap finns med KALLA.md, upstream-filerna byte för byte lika blobbarna i KALLA.md, och motion.json bär bara den fria servern')
def _skillarna():
    m, g = SKILLS / 'motion', SKILLS / 'gsap'
    for p in (m / 'SKILL.md', m / 'KALLA.md', m / 'best-practices' / 'css-or-motion.md', m / 'best-practices' / 'react.md', m / 'codex' / 'index.md',
              g / 'SKILL.md', g / 'KALLA.md', g / 'LICENSE', g / 'llms.txt'):
        assert p.is_file() and not p.is_symlink(), p
    for s_ in ('gsap-core', 'gsap-timeline', 'gsap-scrolltrigger', 'gsap-plugins', 'gsap-utils', 'gsap-react', 'gsap-performance', 'gsap-frameworks'):
        assert (g / s_ / 'SKILL.md').is_file(), s_
        assert re.search(r'^name: %s$' % s_, (g / s_ / 'SKILL.md').read_text(encoding='utf-8'), re.M), 'upstreams frontmatter orörd: %s' % s_
    km, kg = (m / 'KALLA.md').read_text(encoding='utf-8'), (g / 'KALLA.md').read_text(encoding='utf-8')
    assert 'github.com/motiondivision/ai-kit' in km and 'd1c5c26f424adfd47c112d894e9d424b57338c7e' in km and '2026-09-25' in km and 'MIT' in km, km[:400]
    assert 'ingen LICENSE-fil' in km or 'LICENSE-fil' in km, 'KALLA.md säger att källan saknar licensfil'
    assert 'Framer Motion' in km and 'motion/react' in km, 'KALLA.md säger att skillen också är Framer Motion-skillen'
    assert 'github.com/greensock/gsap-skills' in kg and 'aed9cfd3277740755f6bfc1155c7aa645403b760' in kg and '2026-04-21' in kg and 'MIT' in kg, kg[:400]
    assert 'Standard "No Charge"' in kg and '2025-04-30' in kg, 'KALLA.md anger bibliotekets licens med datum'
    assert 'MIT License' in (g / 'LICENSE').read_text(encoding='utf-8') and 'GreenSock' in (g / 'LICENSE').read_text(encoding='utf-8')
    # ordagrant: varje upstream-fils blob (git hash-object) står i KALLA.md (de åtta första tecknen)
    for p in sorted(x for x in m.rglob('*.md') if x.name != 'KALLA.md'):
        assert blob_sha(p)[:8] in km, 'motion: %s (blob %s) står inte i KALLA.md: filen är inte upstreams' % (p.relative_to(m), blob_sha(p)[:8])
    for p in sorted(list(g.glob('gsap-*/SKILL.md')) + [g / 'llms.txt']):
        assert blob_sha(p)[:8] in kg, 'gsap: %s (blob %s) står inte i KALLA.md: filen är inte upstreams' % (p.relative_to(g), blob_sha(p)[:8])
    # vårt index gör mappen till en skill: frontmatter name gsap, och det pekar på de åtta filerna och valet per beteende
    idx = (g / 'SKILL.md').read_text(encoding='utf-8')
    assert re.search(r'^name: gsap$', idx, re.M) and all(s_ in idx for s_ in ('gsap-core', 'gsap-scrolltrigger', 'gsap-timeline')) and 'matchMedia' in idx, idx[:300]
    # MCP-konfigurationen: en server, den fria, i repots mönster (type http); ingen plus-server
    cfg = json.loads((KOPIA / 'kontroller' / 'mcp' / 'motion.json').read_text(encoding='utf-8'))
    assert list(cfg['mcpServers']) == ['motion'] and cfg['mcpServers']['motion'] == {'type': 'http', 'url': 'https://mcp.motion.dev'}, cfg
    assert 'plus' not in json.dumps(cfg), 'Motion+ ges aldrig (ägarens beslut: bara den fria delen)'


# ===== 2. MCP-konfigurationen ges rollen =====
@fall('2 ateljéns argument bär motion.json efter mobbin.json utan strikt läge, rollen rorelse har MCP:n och aktiveringsraderna, och startkontrollen visar Motion som tilldelad')
def _mcp_till_rollen():
    kund()
    a = atelje.session_args(['Read'], None, 10, 'm', 'high', (), SLUG)
    i = a.index('--mcp-config')
    assert a[i + 1] == str(KOPIA / 'kontroller' / 'mcp' / 'mobbin.json') and a[i + 2] == str(KOPIA / 'kontroller' / 'mcp' / 'motion.json'), a[i:i + 3]
    assert '--strict-mcp-config' not in a and a.count('--mcp-config') == 1, a
    b = atelje.session_args(['Read'], None, 10, 'm', 'high', ())
    assert '--strict-mcp-config' in b and 'motion.json' not in ' '.join(b), 'utan slug inga MCP:er'
    assert MOTION_VERKTYG not in a, 'tjänstens verktyg står aldrig i --allowedTools: kundvakten öppnar dem anrop för anrop'
    k = kompetens.tolka()
    assert k['rorelse']['mcp'] == ['refero', 'motion'], k['rorelse']['mcp']
    assert MOTION_VERKTYG in kompetens.mcp_for_pass('rorelse') and MOTION_VERKTYG in kompetens.mcp_for_pass('skapa'), kompetens.mcp_for_pass('rorelse')
    assert kompetens.mcp_verktyg('motion') == [MOTION_VERKTYG] and kompetens.slappta()['motion'] == ['search-motion-docs'], kompetens.slappta()
    assert kompetens.MCPNAMN['motion'] and 'motion/react' in kompetens.MCPNAMN['motion'], kompetens.MCPNAMN
    # prompten (ägarens förtydligande): aktivera med skillverktyget, läs referensfiler med Read, misslyckanden syns
    p = re.sub(r'\s+', ' ', '\n'.join(kompetens.prompt_rader('rorelse', SLUG, 'k01')))  # raderna bryts mitt i meningar
    assert ('läs hela med Read: .claude/skills/impeccable/reference/animate.md, .claude/skills/emil-design-eng/SKILL.md, .claude/skills/emil-animate/SKILL.md' in p), p
    assert 'aktivera med skillverktyget: emil-' not in p, p
    assert ('aktivera med skillverktyget: motion (.claude/skills/motion/SKILL.md), gsap (.claude/skills/gsap/SKILL.md)' in p
            and '.claude/skills/motion/best-practices/css-or-motion.md' in p and '.claude/skills/gsap/gsap-core/SKILL.md' in p), p
    assert 'misslyckas skriver du i svaret innan beroende arbete fortsätter' in p, p
    assert 'search-motion-docs' in p and 'Motion+' in p and 'frågorna är alltid generiska' in p, p
    sa, la = kompetens.aktiverbara(k['rorelse']['valj'])
    assert 'gsap' in sa and 'motion' in sa and 'gsap/gsap-core/SKILL.md' in la, (sa, la)  # en nästlad SKILL.md är en fil, ingen skill
    # startkontrollen: Motion som tilldelad tjänst i ateljéns session, aldrig bland de övriga
    alla = [MOTION_VERKTYG] + [v for t in referenstjanster.TJANSTER.values() for v in t['verktyg']]
    med = {'resultat': 'ok', 'tid': '2026-10-07T12:00:00Z', 'flaggor': ['--setting-sources', '--settings', '--mcp-config'],
           'servrar': {'refero': 'connected', 'mobbin': 'connected', 'motion': 'connected', 'claude.ai Claude Docs': 'connected'}, 'verktyg': alla, 'skills': ['motion', 'gsap']}
    assert sk.mcp_atkomst(med, 'motion') == ('provat', None), sk.mcp_atkomst(med, 'motion')
    rader = {r['namn']: r for r in sk.atkomstrader(med, True)}
    assert rader['Motion i ateljéns session']['resultat'] == 'ok' and 'rorelse' in rader['Motion i ateljéns session']['detalj'], rader.get('Motion i ateljéns session')
    assert 'motion' not in rader['övriga MCP i ateljéns session']['detalj'] and 'Claude Docs' in rader['övriga MCP i ateljéns session']['detalj'], rader['övriga MCP i ateljéns session']
    utan = dict(med, servrar={'refero': 'connected', 'mobbin': 'connected'}, verktyg=[v for v in alla if v != MOTION_VERKTYG])
    r = {x['namn']: x for x in sk.atkomstrader(utan, True)}['Motion i ateljéns session']
    assert r['resultat'] == 'fel' and 'tilldelad men åtkomst saknas' in r['detalj'] and 'dokumentation' in r['detalj'] and 'motion.json' in r['detalj'], r
    saknat = dict(med, verktyg=[v for v in alla if v != MOTION_VERKTYG])
    assert sk.mcp_atkomst(saknat, 'motion')[0] == 'blockerat' and 'search-motion-docs' in sk.mcp_atkomst(saknat, 'motion')[1], sk.mcp_atkomst(saknat, 'motion')
    roll = {x['roll']: x for x in sk.roller(med, [], True)}['rorelse']
    assert roll['atkomst']['mcp']['motion']['tillstand'] == 'provat' and 'motion' in roll['tilldelat']['skills'] and 'gsap' in roll['tilldelat']['skills'], roll
    # verktygsbesluten: uppgift, ingen uppgift (beslut i kartan) och nytt (utan beslut), aldrig okänt
    upp = {'refero': {v.split('__')[-1] for v in referenstjanster.TJANSTER['refero']['verktyg']},
           'mobbin': {v.split('__')[-1] for v in referenstjanster.TJANSTER['mobbin']['verktyg']},
           'motion': {'search-motion-docs', 'generate-css-easing', 'foo-bar'}}
    vr = {x['namn']: x for x in sk.tjanstverktyg_rader(upp)}
    assert vr['Motions verktyg med uppgift']['resultat'] == 'ok', vr.get('Motions verktyg med uppgift')
    assert vr['generate-css-easing (Motion)']['resultat'] == 'ingen_uppgift' and '2026-10-07' in vr['generate-css-easing (Motion)']['detalj'], vr.get('generate-css-easing (Motion)')
    assert vr['foo-bar (Motion)']['resultat'] == 'nytt', vr.get('foo-bar (Motion)')
    borta = {x['namn']: x for x in sk.tjanstverktyg_rader(dict(upp, motion={'generate-css-easing'}))}['Motions verktyg med uppgift']
    assert borta['resultat'] == 'fel' and 'tilldelade men saknas' in borta['detalj'], borta


# ===== 3. kundvakten =====
@fall('3 kundvakten släpper generiska frågor till search-motion-docs, stoppar kundens namn, ort, personnamn och andra verktyg hos Motion, och krokens matcher täcker tjänsten')
def _kundvakten():
    kund()
    assert re.fullmatch(kundvakt.MATCH, MOTION_VERKTYG) and re.fullmatch(kundvakt.MATCH, 'mcp__refero__refero_search_screens'), kundvakt.MATCH
    assert not re.fullmatch(kundvakt.MATCH, 'mcp__railway__get-status'), 'andra MCP:er får ingen tillåtelse'
    inst = json.loads(atelje.kundvakt(SLUG))
    matcher = inst['hooks']['PreToolUse'][0]['matcher']
    assert matcher == kundvakt.MATCH and re.fullmatch(matcher, MOTION_VERKTYG), matcher
    assert MOTION_VERKTYG in kundvakt.tillatna() and set(referenstjanster.TJANSTER['mobbin']['verktyg']) <= kundvakt.tillatna(), kundvakt.tillatna()
    assert vakt(SLUG, MOTION_VERKTYG, {'platform': 'js', 'searchTerm': 'inView stagger reveal'}) is None
    assert vakt(SLUG, MOTION_VERKTYG, {'platform': 'react', 'searchTerm': 'layout animation accordion'}) is None
    s = vakt(SLUG, MOTION_VERKTYG, {'platform': 'js', 'searchTerm': 'hero for Provfirman Trä'}) or ''
    assert 'kundens namn' in s, s
    s = vakt(SLUG, MOTION_VERKTYG, {'platform': 'js', 'searchTerm': 'reveal Exempelby'}) or ''
    assert 'kundens namn, ort' in s or 'ort ur kundens underlag' in s, s
    s = vakt(SLUG, MOTION_VERKTYG, {'platform': 'js', 'searchTerm': 'testimonial Anna Svensson'}) or ''
    assert 'personnamn' in s, s
    s = vakt(SLUG, 'mcp__motion__generate-css-easing', {'kind': 'spring', 'duration': 0.4}) or ''
    assert 'inte ett av flödets verktyg' in s, s
    assert vakt(SLUG, 'mcp__mobbin__search_screens', {'query': 'contractor landing page', 'mode': 'standard'}) is None
    assert vakt(SLUG, 'mcp__refero__refero_search_styles', {'query': 'warm craft builder site'}) is None
    # krokens väg: kundvakt.py som process med krokens JSON på stdin: tillåtelse (0) och stopp (2)
    def krok(indata):
        return subprocess.run([str(KOPIA / '.venv' / 'bin' / 'python'), '-B', str(KOPIA / 'kontroller' / 'kundvakt.py'), SLUG, str(atelje.UNDERLAG)],
                              input=json.dumps(indata), capture_output=True, text=True, timeout=60)
    r = krok({'tool_name': MOTION_VERKTYG, 'tool_input': {'platform': 'js', 'searchTerm': 'scroll reveal'}})
    assert r.returncode == 0 and json.loads(r.stdout)['hookSpecificOutput']['permissionDecision'] == 'allow', (r.returncode, r.stdout, r.stderr)
    r = krok({'tool_name': MOTION_VERKTYG, 'tool_input': {'platform': 'js', 'searchTerm': 'Provfirman Trä reveal'}})
    assert r.returncode == 2 and 'kundens namn' in r.stderr and not r.stdout.strip(), (r.returncode, r.stdout, r.stderr)


# ===== 4. GSAP-sidan och låsen =====
@fall('4 rökprovets sida /rorelse/ med gsap.matchMedia för båda lägena och giltiga SEO-längder, rökprovets Playwright-steg, gsap 3.15.0 i båda mallarnas lås utan skript, och beroendetabellen')
def _gsap_sidan():
    sida = (KOPIA / 'kontroller' / 'rokprov' / 'src' / 'pages' / 'rorelse' / 'index.astro').read_text(encoding='utf-8')
    assert "import gsap from 'gsap'" in sida and 'gsap.matchMedia()' in sida, sida[:300]
    assert "'(prefers-reduced-motion: no-preference)'" in sida and "'(prefers-reduced-motion: reduce)'" in sida, 'båda lägena'
    assert "dataset.rorelse = 'stilla'" in sida and "dataset.rorelse = 'gsap'" in sida, 'märkena provet läser'
    assert 'Ram' in sida and 'sida="Rörelse"' in sida, 'sidan i rökprovets ram med brödsmulor (DESIGN.md kräver dem)'
    titel = re.search(r'titel="([^"]+)"', sida).group(1)
    beskr = re.search(r'beskrivning="([^"]+)"', sida).group(1)
    assert 50 <= len(titel) <= 60 and 120 <= len(beskr) <= 155, (len(titel), len(beskr))
    rp = (KOPIA / 'kontroller' / 'rokprov.sh').read_text(encoding='utf-8')
    assert 'kontroller/rokprov/rorelse.mjs' in rp and 'assert r.returncode == 0' in rp, 'rökprovet anropar och kräver beteendeprovets resultat'
    js = (KOPIA / 'kontroller/rokprov/rorelse.mjs').read_text()
    for marker in ('clock.runFor', 'new DOMMatrix', "rm === 'byte'", 'javaScriptEnabled: false'):
        assert marker in js, marker
    assert 'prov_rorelse.py' in rp and 'rorelse-prov.log' in rp, 'rökprovet kör det här provet'
    for m in ('astro', 'leverans'):
        pj = json.loads((KOPIA / 'mall' / m / 'package.json').read_text(encoding='utf-8'))
        assert pj['dependencies'].get('gsap') == '3.15.0', (m, pj['dependencies'].get('gsap'))
        assert pj['dependencies'].get('motion') == '14.0.0' and 'framer-motion' not in pj['dependencies'], 'motion kvar, aldrig framer-motion bredvid'
        las = json.loads((KOPIA / 'mall' / m / 'package-lock.json').read_text(encoding='utf-8'))
        g = las['packages']['node_modules/gsap']
        assert g['version'] == '3.15.0' and not g.get('hasInstallScript') and not g.get('dependencies') and 'standard-license' in g.get('license', ''), (m, g)
        assert las['packages']['']['dependencies'].get('gsap') == '3.15.0', (m, 'rotens beroenden i låset')
    b = (KOPIA / 'kunskap' / 'beroenden.md').read_text(encoding='utf-8')
    assert re.search(r'^\| gsap \| 3\.15\.0 \| Standard "No Charge" GSAP License', b, re.M), 'beroendetabellen'
    assert 'gzip' in b and '2026-10-07' in b and 'matchMedia' in b, 'kostnaden uppmätt och kravet på reducerad rörelse'


# ===== 5. metodkartan ger valet och kvittot visar det =====
@fall('5 rollen rorelse väljer per beteende, passchemat bär aktivering och teknikval, prompten säger det, och kvittot skiljer aktivering, användning och bedömd kvalitet åt')
def _valet_och_kvittot():
    kund()
    r = kompetens.tolka()['rorelse']
    for ord_ in ('CSS', 'Motion', 'GSAP', 'kvot', 'stilla'):
        assert ord_ in r['uppgift'], (ord_, r['uppgift'])
    assert 'teknikval' in r['visar'] and 'RIKTNING.md' in r['visar'], r['visar']
    assert 'css-or-motion.md' in r['uppgift'] and 'motion/best-practices/css-or-motion.md' in r['valj'], 'beslutstabellen läses före valet (prov_revision: skissens kärna under 160 000 tecken)'
    assert 'gsap/SKILL.md' in r['valj'] and 'gsap/gsap-scrolltrigger/SKILL.md' in r['valj'], r
    assert kompetens.storlek(kompetens.lasfiler('skapa')) < 160000, kompetens.storlek(kompetens.lasfiler('skapa'))
    s = kd.PASS_SCHEMA
    assert 'teknikval' in s['required'] and 'aktivering' in s['required'], s['required']
    assert s['properties']['teknikval']['items']['properties']['teknik']['enum'] == ['css', 'motion', 'gsap', 'stilla'], s['properties']['teknikval']
    assert s['properties']['aktivering']['items']['required'] == ['skill', 'lyckades', 'fel'], s['properties']['aktivering']
    assert 'GSAP' in kd.PASSUPPGIFT['rorelse'] and 'teknikval' in kd.PASSUPPGIFT['rorelse'] and 'kvot' in kd.PASSUPPGIFT['rorelse'], kd.PASSUPPGIFT['rorelse']
    assert 'css-or-motion.md hel före valet' in kd.PASSUPPGIFT['rorelse'], 'passet rörelse kräver tabellen före valet'
    p = kd.pass_prompt(SLUG, 'k01', 'rorelse')
    for ord_ in ('teknikval', 'aktivering', 'search-motion-docs', 'faktiskt anrop', 'fylla en ruta'):
        assert ord_ in p, (ord_, p[:500])
    # kvittot: valet som sessionens redovisning, inte observation; nivåerna var för sig
    bas = {'verifierad': True, 'lasta': [kompetens.vag(f) for f in r['karna']], 'skill_anrop': ['motion', 'emil-animate'], 'skill_fel': ['gsap'],
           'mcp_anrop': {MOTION_VERKTYG: 1}, 'mcp_utfall': {MOTION_VERKTYG: {'anrop lyckades': 1}}, 'mcp_lage': {'motion': 'ansluten', 'refero': 'ansluten'},
           'verktyg_anrop': {'förhandsvisning': {'anrop': 2, 'ok': 2, 'fel': 0}},
           'teknikval': [{'beteende': 'sektionen avtäcks vid scroll', 'teknik': 'gsap', 'skal': 'tidslinje i tre steg med scrub'},
                         {'beteende': 'menyknappen', 'teknik': 'css', 'skal': 'en övergång räcker'}],
           'visuell_bedomning': {'fore': 'a.png', 'efter': 'b.png', 'omdome': 'battre', 'skal': 'rytmen håller på mobilen'}}
    t = {x['roll']: x for x in kompetens.tillstand(bas, 'rorelse')}['rorelse']
    assert t['tillampning'].startswith(kompetens.REDOVISAT) and 'sektionen avtäcks vid scroll → gsap' in t['tillampning'] and 'menyknappen → css' in t['tillampning'], t['tillampning']
    assert t['teknikval'] == bas['teknikval'], t.get('teknikval')
    n = t['nivaer']
    assert n['aktivering'].startswith('misslyckad aktivering: gsap') and 'motion' in n['aktivering'], n['aktivering']
    assert n['anvandning'].startswith(T['anvant']) and 'motion' in n['anvandning'] and 'förhandsvisning' in n['anvandning'], n['anvandning']
    assert n['bedomd_kvalitet']['av_sessionen'].startswith(kompetens.REDOVISAT) and 'battre' in n['bedomd_kvalitet']['av_sessionen'], n['bedomd_kvalitet']
    assert 'granskning' in n['bedomd_kvalitet']['av_granskningen'] and 'ägarens dom' in n['bedomd_kvalitet']['av_granskningen'], n['bedomd_kvalitet']
    assert t['skillverktyget']['misslyckade'] == ['gsap'] and t['mcp']['motion']['tillstand'] == T['anvant'], (t['skillverktyget'], t['mcp'])
    # utan teknikval: inte observerat; i passet granskning räknas inget teknikval
    t0 = {x['roll']: x for x in kompetens.tillstand({k: v for k, v in bas.items() if k != 'teknikval'}, 'rorelse')}['rorelse']
    assert t0['tillampning'] == T['ej_observerat'] and 'teknikval' not in t0, t0.get('tillampning')
    tg = kompetens.tillstand(dict(bas, teknikval=bas['teknikval']), 'granskning')
    assert all(x['tillampning'] == T['ej_observerat'] for x in tg), [x['tillampning'] for x in tg]
    # en aktiverad skill utan misslyckanden, och en roll utan observation
    t1 = {x['roll']: x for x in kompetens.tillstand(dict(bas, skill_fel=[], skill_anrop=['motion', 'gsap', 'emil-animate', 'emil-design-eng'] + [
        s_ for s_ in {f.split('/')[0] for f in r['karna'] + r['valj']} if not s_.startswith(('kunskap', 'kritik'))]), 'rorelse')}['rorelse']
    assert t1['nivaer']['aktivering'].startswith('aktiverad med skillverktyget'), t1['nivaer']['aktivering']
    t2 = {x['roll']: x for x in kompetens.tillstand({'verifierad': False}, 'rorelse')}['rorelse']
    assert t2['nivaer']['aktivering'] == T['ej_observerat'] and t2['nivaer']['bedomd_kvalitet']['av_sessionen'] == T['ej_observerat'], t2['nivaer']
    # den läsbara raden visar nivåerna och tillämpningen
    rad_ = '\n'.join(kd.kompetensrad(dict(bas, tillstand=None), 'rorelse'))
    assert 'aktivering: misslyckad aktivering: gsap' in rad_ and 'användning: ' in rad_ and 'bedömd kvalitet: ' in rad_ and 'tillämpning: ' in rad_, rad_
    # ur ett transkript: en misslyckad aktivering räknas aldrig som läsning och syns för sig
    sid = transkript([('Skill', {'skill': 'motion'}, 'Skillen motion är laddad'), ('Skill', {'skill': 'gsap'}, ('fel', 'Unknown skill: gsap')),
                      ('Read', {'file_path': str(KOPIA / '.claude' / 'skills' / 'motion' / 'best-practices' / 'css-or-motion.md')}, 'tabellen'),
                      (MOTION_VERKTYG, {'platform': 'js', 'searchTerm': 'inView'}, 'Motion codex results for js. Docs: inView')],
                     '3f0e0d0c-0b0a-4908-8706-050403020201')
    ml = bildkedja.metodlasning(sid, [kompetens.vag(f) for f in r['karna']] + ['.claude/skills/motion/SKILL.md', '.claude/skills/gsap/SKILL.md',
                                                                             '.claude/skills/motion/best-practices/css-or-motion.md'])
    assert ml['verifierad'] and ml['skill_anrop'] == ['motion'] and ml['skill_fel'] == ['gsap'], ml
    assert '.claude/skills/motion/SKILL.md' in ml['fore'] + ml['efter'] and '.claude/skills/gsap/SKILL.md' in ml['saknas'], ml
    assert '.claude/skills/motion/best-practices/css-or-motion.md' in ml['fore'] + ml['efter'], ml
    kv = kompetens.kvitto([{'session_id': sid}], 'rorelse')
    assert kv['verifierad'] and kv['skill_fel'] == ['gsap'] and kv['mcp_anrop'] == {MOTION_VERKTYG: 1}, kv
    tk = {x['roll']: x for x in kv['tillstand']}['rorelse']
    assert tk['nivaer']['aktivering'].startswith('misslyckad aktivering: gsap'), tk['nivaer']


# ===== 6. metodlåset =====
@fall('6 metodlåset: metod.py och kompetens.py prövar kartan med de nya källorna, och en ändrad ny källa stoppar leveransen')
def _laset():
    fel, kallor = metod.prova()
    assert fel == [], fel
    for f in ('motion/best-practices/css-or-motion.md', 'gsap/SKILL.md', 'gsap/gsap-core/SKILL.md', 'motion/SKILL.md'):
        assert f in kallor, (f, sorted(k for k in kallor if k.startswith(('motion', 'gsap'))))
    assert kompetens.prova() == [], kompetens.prova()
    fil = KOPIA / '.claude' / 'skills' / 'motion' / 'best-practices' / 'css-or-motion.md'
    orig = fil.read_text(encoding='utf-8')
    try:
        fil.write_text(orig + '\nEn rad till.\n', encoding='utf-8')
        fel2, _ = metod.prova()
        assert any('motion/best-practices/css-or-motion.md har ändrats' in x for x in fel2), fel2
    finally:
        fil.write_text(orig, encoding='utf-8')
    assert metod.prova()[0] == []
    assert kompetens.tjanstverktyg()['motion']['search-motion-docs']['beslut'] == 'uppgift', kompetens.tjanstverktyg().get('motion')
    assert kompetens.tjanstverktyg()['motion']['generate-css-easing']['beslut'] == 'ingen uppgift', kompetens.tjanstverktyg().get('motion')
    # kartan utan Motions verktygsblock, eller med ett verktyg kundvakten inte släpper, är fel
    text = metod.KARTA.read_text(encoding='utf-8')
    utan = re.sub(r'```tjanstverktyg motion\n.*?```\n', '', text, flags=re.S)
    assert any('motion: search-motion-docs släpps av kundvakten' in x for x in kompetens.tjanstverktyg_fel(utan)), kompetens.tjanstverktyg_fel(utan)
    extra = text.replace('generate-css-easing: ingen uppgift', 'generate-css-easing: uppgift')
    assert any('generate-css-easing en uppgift' in x and 'kundvakten' in x and 'släpper det inte' in x for x in kompetens.tjanstverktyg_fel(extra)), kompetens.tjanstverktyg_fel(extra)


# ===== 7. städregeln =====
@fall('7 städregeln känner provets tempprefix')
def _prefix():
    assert 'nwp-rorelse-' in stadning.TMP_PREFIX, stadning.TMP_PREFIX
    assert TMP.name.startswith('nwp-rorelse-') and (TMP / korregister.AGARFIL).is_file(), 'provets katalog är registrerad'


# ===== 8. dokumentationen =====
@fall('8 dokumentationen: beroenden.md, metodkartans Avgöranden och lista Ingen uppgift, registrets ersättningsrad, BESLUT-posten och skillarnas KALLA')
def _dokumentationen():
    b = (KOPIA / 'kunskap' / 'beroenden.md').read_text(encoding='utf-8')
    for ord_ in ('framer-motion', 'motion/react', 'Framer Motion', 'Valet per beteende', 'gsap.matchMedia', 'ScrollSmoother', '2025-04-30', 'Webflow'):
        assert ord_ in b, ord_
    k = (KOPIA / 'kunskap' / 'metodkarta.md').read_text(encoding='utf-8')
    assert 'GSAP finns inte bland de låsta' not in k, 'listan Ingen uppgift säger inte längre att GSAP saknas i låset'
    assert 'Motion och GSAP (`kunskap/beroenden.md`)' in k and 'fylla en kvot' in k and 'Framer Motion' in k, 'Avgörandena Teknik'
    assert 'aktiverar rollens skills uttryckligen med skillverktyget' in k and 'aktivering, lyckad användning och bedömd kvalitet' in k, 'ägarens förtydligande i Kompetenserna'
    reg = (KOPIA / 'kunskap' / 'REGISTER.md').read_text(encoding='utf-8')
    assert 'Inget för våra sajter. Sämre. (Ersatt 2026-10-07 för GSAP' in reg, 'kirurgens post står kvar med ersättningsraden'
    assert '### 2026-10-07 · greensock/gsap-skills' in reg and '### 2026-10-07 · motiondivision/ai-kit' in reg, 'intagsposterna'
    beslut = (KOPIA / 'BESLUT.md').read_text(encoding='utf-8')
    assert '## Tillägg 2026-10-07: Motion AI Kit och GSAP (gren H2)' in beslut and 'bara den fria delen' in beslut, 'BESLUT-posten'
    assert 'Skilj aktivering, lyckad användning och bedömd kvalitet åt' in beslut, 'ägarens förtydligande ordagrant i posten'
    for s_ in ('motion', 'gsap'):
        km = (SKILLS / s_ / 'KALLA.md').read_text(encoding='utf-8')
        assert 'Förgranskning 2026-10-07' in km and 'LÅG' in km and 'Krockar med våra beslut' in km and 'Så används skillen här' in km, s_
    cl = (KOPIA / 'CLAUDE.md').read_text(encoding='utf-8')
    assert 'KALLA.md' in cl, 'CLAUDE.md kräver KALLA.md för varje skill'


@fall('9 sessionsavtrycket binder varje MCP-konfiguration: väg, innehåll, frånvaro och upprepade flaggor')
def _hela_sessionsavtrycket():
    import verktygslada as vl
    a, b, c = (TMP / n for n in ('a.json', 'b.json', 'c.json'))
    for f in (a, b, c):
        f.write_text('{"mcpServers": {}}')
    args = ['claude', '--model', 'syntetisk', '--mcp-config', str(a), str(b), '--settings', '{}']
    h = vl.sessionsavtryck(args, 'prov')
    b.write_text('{"mcpServers": {"annan": {}}}')
    assert vl.sessionsavtryck(args, 'prov') != h, 'andra filens innehåll'
    h2 = vl.sessionsavtryck(args, 'prov')
    b.unlink()
    assert vl.sessionsavtryck(args, 'prov') not in (h, h2), 'andra filens frånvaro'
    assert vl.sessionsavtryck(args, 'prov') != vl.sessionsavtryck([str(c) if x == str(b) else x for x in args], 'prov'), 'andra filens väg'
    x = ['--mcp-config', str(a), '--mcp-config', str(c)]
    h3 = vl.sessionsavtryck(x, 'prov')
    c.write_text('{"mcpServers": {"ny": {}}}')
    assert vl.sessionsavtryck(x, 'prov') != h3, 'upprepad flaggas andra fil'
    assert vl.sessionsavtryck(['--mcp-config={"mcpServers": {}}'], 'prov') != vl.sessionsavtryck(['--mcp-config={"mcpServers": {"ny": {}}}'], 'prov'), 'inline JSON'


@fall('10 okänt utfall förblir okänt; bara valda aktiverbara skills krävs, och Read är inte Skill')
def _arlda_nivaer():
    kv = {'verifierad': True, 'mcp_anrop': {MOTION_VERKTYG: 1}}
    t = {x['roll']: x for x in kompetens.tillstand(kv, 'rorelse')}['rorelse']
    assert t['mcp']['motion']['tillstand'] == T['ej_observerat'], t
    assert T['ej_observerat'] in t['nivaer']['anvandning'], t['nivaer']
    role = kompetens.tolka()['rorelse']
    required, _ = kompetens.aktiverbara(role['karna'])
    kv = {'verifierad': True, 'lasta': [kompetens.vag(f) for f in role['karna']], 'valda': [], 'skill_anrop': required}
    t = {x['roll']: x for x in kompetens.tillstand(kv, 'rorelse')}['rorelse']
    assert not required and t['nivaer']['aktivering'].startswith('inga Skill-aktiveringar tilldelade'), t['nivaer']
    assert 'utan aktivering' not in t['nivaer']['aktivering'], t['nivaer']
    n = kompetens.nivaer(['a', 'b'], ['a'], [], ['b'], {}, {}, None, True)
    assert n['aktivering'].startswith('delvis:') and 'Read' in n['aktivering'] and 'b' in n['aktivering'], n
    n = kompetens.nivaer([], [], [], [], {'motion': {'tillstand': T['ej_observerat']}}, {'prov': T['anvant']}, None, True)
    assert T['ej_observerat'] in n['anvandning'] and T['anvant'] in n['anvandning'], n


@fall('11 riktiga kompetenspasset bevarar MCP-utfallen och kräver Motion-resultat bara vid Motion-val')
def _passets_hela_kvitto():
    from copy import deepcopy
    from unittest.mock import patch
    kund()
    errors = []
    for tech, outcome, expected in [('motion', None, False), ('motion', 'tomt resultat', False),
                                    ('motion', 'fel', False), ('motion', 'anrop lyckades', True),
                                    ('css', None, True), ('stilla', None, True)]:
        st = {'status': 'klar', 'version': 'v1', 'kompetens': {}}
        def spara(slug, kid, status, skal='', ta_bort=(), **extra):
            st.update(status=status, skal=skal, **extra)
            for key in ta_bort:
                st.pop(key, None)
            return deepcopy(st)
        def foto(*a, **kw):
            st['version'] = 'v2'
            return deepcopy(st)
        kv = {'verifierad': True, 'saknas': [], 'lasta': [], 'valda': [], 'skill_anrop': [], 'skill_fel': [],
              'mcp_anrop': {MOTION_VERKTYG: 1} if outcome else {},
              'mcp_utfall': {MOTION_VERKTYG: {outcome: 1}} if outcome else {},
              'mcp_lage': {'motion': 'ansluten'}, 'verktyg_anrop': {'förhandsvisning': {'anrop': 1, 'ok': 1, 'fel': 0}}}
        so = {'teknikval': [{'beteende': 'menyn', 'teknik': tech, 'skal': 'syntetiskt mekanikprov'}],
              'beteende_provat': [{'vad': 'menyn', 'hur': 'lokalt prov', 'resultat': 'öppnad', 'bild': ''}],
              'kod_andrad': [], 'ingen_andring': '', 'aktivering': [], 'kvarstar': []}
        with patch.object(kd, 'las_status', side_effect=lambda *a: deepcopy(st)), patch.object(kd, 'satt_status', side_effect=spara), \
             patch.object(kd, 'bevara_version'), patch.object(kd, 'kopiera_bilder', return_value=[]), \
             patch.object(kd, 'fotografera', side_effect=foto), patch.object(atelje, 'session', return_value={'structured_output': so}), \
             patch.object(kompetens, 'kvitto', return_value=deepcopy(kv)):
            result = kd.kompetenspass(SLUG, 'k01', 'rorelse', 'mekanikprov')
        rec = json.loads(json.dumps(result))['kompetens']['mekanikprov:rorelse']
        for key in ('mcp_utfall', 'mcp_lage', 'verktyg_anrop', 'skill_fel'):
            if rec['kvitto'].get(key) != kv[key]:
                errors.append((tech, outcome, 'borttappat', key))
        if rec['genomford'] is not expected:
            errors.append((tech, outcome, 'genomford', rec['genomford'], expected))
    assert not errors, errors


@fall('12 obesvarad skill räknas inte som aktiverad eller läst')
def _obesvarad_skill():
    sid = transkript([('Skill', {'skill': 'motion'}, None)], '7f0e0d0c-0b0a-4908-8706-050403020201')
    f = '.claude/skills/motion/SKILL.md'
    m = bildkedja.metodlasning(sid, [f])
    assert m['skill_anrop'] == [] and f in m['saknas'], m


if FEL:
    print('rörelsens prov: %d fall föll: %s' % (len(FEL), '; '.join(FEL)), file=sys.stderr)
    sys.exit(1)
print('rörelsens prov: alla fall gröna', file=sys.stderr)
