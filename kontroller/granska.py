#!/usr/bin/env python3
"""granska.py — oberoende granskning av ett bygge: två egna Claude-sessioner, utan byggarens resonemang och utan att se
varandra, dömer den färdiga sajten parallellt efter kritik/GRANSKARE.md och sätter betyg på fem kriterier. Domen tar
det lägsta betyget per kriterium och varje blockerande fynd från någon av dem, så godkänt kräver båda (granskarförsöket
2026-10-02: två fann fler av ägarens fel än en i alla tre dömda byggen, utan falska blockerande fynd). Kritiken går tillbaka till byggaren tills sajten
håller (generator och granskare, Anthropic "Harness design for long-running application development").

    .venv/bin/python kontroller/granska.py <slug> [--vanta SEK] [--om]

Kör först `kontroller/prova.py <slug> --snabb` (eller hela provet): granskningen gäller exakt det bygge som provet
senast byggde och tar provets skärmbilder som underlag. Granskaren körs i en egen process som överlever kommandot;
kommandot väntar på svaret högst --vanta sekunder (540). Pågår granskningen fortfarande: kör samma kommando igen.
Ett bygge som redan granskats svarar direkt med samma dom, utan ny session (--om tvingar en ny).

Resultat i kunder/<slug>/granskning/: GRANSKNING.json och GRANSKNING.md (senaste), runda-NN/ per omgång.
Exit: 0 godkänd · 1 underkänd · 2 fel i anropet eller saknat bygge · 3 taket för omgångar nått · 4 granskaren föll ·
5 pågår, kör igen.

Miljö: NWP_GRANSKARE_ANTAL (2 granskare per omgång; 1 för en), NWP_GRANSKARE_MODELL (opus[1m]), NWP_GRANSKARE_EFFORT (high),
NWP_GRANSKNING_MAX (5 omgångar per körning),
NWP_GRANSKNING_FRIST (1500 s per session), NWP_KORNING (sätts av kor.sh; omgångarna räknas per körning).
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova  # noqa: E402  dist_hash, sidor_i, Server

ROOT = prova.ROOT
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
INSTRUKTION = 'kritik/GRANSKARE.md'
SCHEMA = ROOT / 'kritik' / 'SCHEMA-granskning.json'
SCHEMA_ORIGINALITET = ROOT / 'kritik' / 'SCHEMA-originalitet.json'
SCHEMA_JAMFORELSE = ROOT / 'kritik' / 'SCHEMA-jamforelse.json'
ORIGINALITETSLAGEN = ('skugga', 'avgor', 'av')  # egen domare för originalitet: bredvid, avgörande eller avstängd
KRITERIER = ('designkvalitet', 'originalitet', 'hantverk', 'funktion', 'text')
TROSKEL = {k: 7 for k in KRITERIER}
MAX_RUNDOR = int(os.environ.get('NWP_GRANSKNING_MAX', '5'))
ANTAL = max(1, int(os.environ.get('NWP_GRANSKARE_ANTAL', '2')))  # isolerade granskare per omgång
FRIST = int(os.environ.get('NWP_GRANSKNING_FRIST', '1500'))
ARBETSROT = Path('/tmp/nwp-granskning')
MATTSTOCKAR = [
    ('Byggstandarden (punkterna fynden hänvisar till)', 'kunskap/byggstandard.md'),
    ('De åtta dimensionerna', 'kunskap/referenser-professionella.md'),
    ('Regeln mot slop', 'kunskap/copy-kontroll.md'),
    ('Redaktionellt pass', 'kunskap/redaktionellt-pass.md'),
    ('AI-mönster och designprinciper', 'kunskap/externa/anthropic-frontend-design-SKILL.md'),
    ('Vercels gränssnittsriktlinjer', 'kunskap/externa/vercel-web-interface-guidelines-command-e3d624ba.md'),
    ('Tillgänglighet', 'kunskap/externa/addyosmani-accessibility-SKILL.md'),
    ('Kvalitetsgranskning', 'kunskap/externa/addyosmani-web-quality-audit-SKILL.md'),
    ('Designteknik', 'kunskap/externa/emil-emil-design-eng-SKILL.md'),
]
VERKTYG = ['Read', 'Glob', 'Grep', 'Bash(node kontroller/sida.mjs *)',
           'Bash(node kontroller/webblasare/inspektera.mjs --ut /tmp/nwp-granskning/*)', 'Bash(ls *)']
NEKAS = ['Write', 'Edit', 'NotebookEdit', 'WebFetch', 'WebSearch', 'Task', 'Bash(git *)', 'Bash(rm *)', 'Bash(curl *)']
VYER = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def rel(p):
    return str(Path(p).relative_to(ROOT))


def lever(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def ren_miljo():
    """Granskaren är en egen session: inga variabler från en omgivande Claude-session eller från bygget (NWP_SLUG
    skulle annars väcka stoppvakten i granskarens egen session)."""
    return {k: v for k, v in os.environ.items()
            if k != 'CLAUDECODE' and not k.startswith('CLAUDE_CODE_') and not k.startswith('NWP_')}


NIVAER = ('godkänd', 'detaljrättning', 'ny riktning')


def niva(resultat):
    """0 godkänd, 1 underkänd med bara detaljfynd, 2 minst ett fynd kräver ny riktning; None för äldre granskningar
    utan omfattning. Jämförs med ägarens svar: som den är, efter små ändringar, inte utan större ändringar."""
    if godkand(resultat):
        return 0
    omf = [f.get('omfattning') for f in resultat.get('blockerande') or []]
    if 'riktning' in omf:
        return 2
    if omf and all(o == 'detalj' for o in omf):
        return 1
    return 2 if not omf else None  # betyg under tröskeln utan fynd räknas som större brist


def godkand(resultat):
    k = resultat.get('kriterier') or {}
    betyg_ok = all(isinstance((k.get(n) or {}).get('betyg'), int) and k[n]['betyg'] >= TROSKEL[n] for n in KRITERIER)
    visa_ok = all((k.get(n) or {}).get('visa', True) is not False for n in KRITERIER)  # ja/nej utöver betyget
    return betyg_ok and visa_ok and not resultat.get('blockerande')


# --- underlag till granskaren ---

def skarmbilder(rot, sajtrot):
    """Provets skärmbilder kopierade till omgången (provet tömmer sin mapp vid nästa körning). Skärmhöga rutor när
    provet har gjort dem; annars första vyn och den nedskalade helsidan."""
    ut = []
    for sida in sorted(p for p in (rot / 'prov' / 'inspektion').glob('*') if p.is_dir()):
        rutor = sorted(sida.glob('vy-390-ruta-*.png')) + sorted(sida.glob('vy-1440-ruta-*.png'))
        for f in rutor or [sida / vy for vy in VYER]:
            if f.is_file():
                vy = f.name
                mal = sajtrot / sida.name / vy
                mal.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, mal)
                ut.append(mal)
    return ut


def aria_trad(rot, sajtrot):
    """Tillgänglighetsträdet i 390 px per sida ur provets inspektion, kopierat till omgången."""
    ut = []
    for f in sorted((rot / 'prov' / 'inspektion').glob('*/vy-390-aria.txt')):
        mal = sajtrot / f.parent.name / f.name
        mal.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, mal)
        ut.append(mal)
    return ut


def referensbilder(slug):
    ut = []
    for d in sorted(p for p in (UNDERLAG / slug / 'referenser').glob('*') if p.is_dir()):
        for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
            hit = sorted(d.rglob(vy))
            if hit:
                ut.append(hit[0])
    return ut[:16]


def tidigare_byggen(slug):
    syskon = (KUNDER / slug / 'AB-SYSKON').read_text().strip() if (KUNDER / slug / 'AB-SYSKON').is_file() else None
    andra = [p for p in KUNDER.iterdir() if p.is_dir() and SLUG.match(p.name) and p.name not in (slug, syskon, 'ab')
             and not p.name.startswith('rokprov')]
    andra.sort(key=lambda p: (p / 'prov' / 'STATUS.json').stat().st_mtime if (p / 'prov' / 'STATUS.json').is_file() else 0, reverse=True)
    ut = []
    for p in andra[:6]:
        for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
            f = p / 'prov' / 'inspektion' / 'hem' / vy
            if f.is_file():
                ut.append(f)
    return ut


def domda_byggen(utom=None):
    """Byggen som ägaren har dömt, utom det som granskas (granskningen ska vara blind för sin egen dom)."""
    for p in sorted(KUNDER.iterdir()) if KUNDER.is_dir() else []:
        dom = (las_json(p / 'DOM.json') or {}).get('domar') or []
        if dom and p.name != utom:
            yield p, dom[-1].get('svar') or {}


def bildankare(utom=None):
    """Första vyn av dömda byggen med ägarens dom bredvid: nivåer visade med bilder, inte bara ord."""
    ut = []
    for p, svar in domda_byggen(utom):
        bilder = [p / 'prov' / 'inspektion' / 'hem' / vy for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png')]
        bilder = [b for b in bilder if b.is_file()]
        if bilder:
            ut.append((p.name, bilder, 'ägaren: %s; gjord för just den här verksamheten %s av 5' % (svar.get('namn', '?'), svar.get('specifik', '?'))))
    return ut[:4]


def kalibrering(utom=None):
    """Ägarens domar bredvid granskarens betyg för samma bygge: underlag för att döma som ägaren."""
    rader = []
    for p, svar in domda_byggen(utom):
        dom = [svar]
        g = las_json(p / 'granskning' / 'GRANSKNING.json')
        agaren = '; '.join('%s: %s' % (k, str(svar[k]).replace('\n', ' ')[:300]) for k in
                           ('namn', 'battre', 'specifik', 'mall_tecken', 'samsta', 'basta', 'en_andring') if svar.get(k) not in (None, ''))
        if g:
            betyg = ', '.join('%s %s' % (n, (g.get('kriterier') or {}).get(n, {}).get('betyg', '?')) for n in KRITERIER)
            dom = NIVAER[g['niva']] if g.get('niva') is not None else ('godkänd' if g.get('godkand') else 'underkänd')
            gr = 'granskaren: %s (%s)' % (dom, betyg)
        else:
            gr = 'ingen granskning'
        rader.append('- %s · %s · ägaren: %s' % (p.name, gr, agaren or 'inga svar'))
    return rader


def uppdrag_text(slug, url, sidor, arbetskatalog, bilder, refs, tidigare, kal, rdir, aria=(), ankare=()):
    u = UNDERLAG / slug
    v = las_json(u / 'VERKSAMHET.json') or {}
    rad = lambda p: '- ' + (rel(p) if str(p).startswith(str(ROOT)) else str(p))  # noqa: E731
    underlag = [u / f for f in ('VERKSAMHET.json', 'RESEARCH.md', 'BRIEF.md', 'REFERENSER.md', 'BESTALLNING.md') if (u / f).is_file()]
    if (u / 'bilder' / 'BILDER.md').is_file():
        underlag.append(u / 'bilder' / 'BILDER.md')
    trosklar = ', '.join('%s ≥ %d' % (k, TROSKEL[k]) for k in KRITERIER)
    delar = [
        'Du är granskaren. Läs %s först och följ den. Du ändrar inga filer.' % INSTRUKTION, '',
        'Bygge: %s · verksamhet: %s' % (slug, v.get('namn') or slug),
        'Sajten live: %s' % url,
        'Sidor: %s' % ', '.join(url + s for s in sidor),
        'Din arbetskatalog för egna skärmbilder och sida.mjs-utdata: %s' % arbetskatalog,
        'Trösklar för godkänt: %s, och inga blockerande fynd. Godkännandet räknas ut av verktyget.' % trosklar, '',
        'Ägarens domar: LARDOMAR.md', '',
        'Kalibrering, ägarens dom bredvid granskarens för tidigare byggen:',
        *(kal or ['- inga ännu']), '',
        'Bildankare, första vyn av byggen som ägaren dömt, med domen (titta på bilderna):',
        *(['- %s · %s: %s' % (namn, text, ', '.join(rel(b) for b in bb)) for namn, bb, text in ankare] or ['- inga ännu']), '',
        'Verksamhetens underlag:', *[rad(p) for p in underlag], '',
        'Sajtens skärmbilder från provet, varje sida uppifrån och ned i skärmhöga rutor i 390 och 1440 (läs varje):',
        *[rad(p) for p in bilder], '',
        'Tillgänglighetsträdet i 390 px per sida:', *([rad(p) for p in aria] or ['- saknas']), '',
        'Byggstandardens maskinella fynd: %s' % (rad(rdir / 'standard.md')[2:] if (rdir / 'standard.md').is_file() else 'saknas'),
        'Stilrapporten: %s' % (rad(rdir / 'STIL.md')[2:] if (rdir / 'STIL.md').is_file() else 'saknas'),
        'Copykontrollens fynd: %s' % (rad(rdir / 'copy.md')[2:] if (rdir / 'copy.md').is_file() else 'saknas'), '',
        'Referensernas skärmbilder:', *([rad(p) for p in refs] or ['- inga']), '',
        'Tidigare byggens första vy:', *([rad(p) for p in tidigare] or ['- inga']), '',
        'Måttstockar:', *['- %s: %s' % (namn, f) for namn, f in MATTSTOCKAR if (ROOT / f).is_file()],
    ]
    return '\n'.join(delar) + '\n'


def sla_ihop(delar):
    """Isolerade granskares svar till en dom: lägsta betyget per kriterium, ja bara när alla säger ja, och varje
    blockerande fynd från någon av dem. Godkänt kräver alltså att alla godkänner. Två granskare hittade fler av
    ägarens fel än en i alla tre dömda byggen, utan falska blockerande fynd (granskarförsöket 2026-10-02)."""
    if len(delar) == 1:
        return dict(delar[0])
    ut = {'kriterier': {}}
    for k in KRITERIER:
        bs = [d['kriterier'][k] for d in delar]
        lagst = min(bs, key=lambda b: b['betyg'])
        ut['kriterier'][k] = {'betyg': lagst['betyg'], 'motivering': lagst['motivering'], 'visa': all(b.get('visa') for b in bs)}
    ut['blockerande'] = sorted([dict(f, granskare=i + 1) for i, d in enumerate(delar) for f in d.get('blockerande') or []],
                               key=lambda f: -int(f.get('allvarlighet') or 0))
    for f in ('forbattringar', 'styrkor', 'sett', 'ej_bedomt'):
        ut[f] = list(dict.fromkeys(x for d in delar for x in d.get(f) or []))
    ut['kognitiv_genomgang'] = [dict(r, uppgift='[%d] %s' % (i + 1, r.get('uppgift', ''))) for i, d in enumerate(delar)
                                for r in d.get('kognitiv_genomgang') or []]
    ut['likhet_tidigare'] = ' '.join('Granskare %d: %s' % (i + 1, d.get('likhet_tidigare', '')) for i, d in enumerate(delar))
    ut['sammanfattning'] = ' '.join('Granskare %d: %s' % (i + 1, d.get('sammanfattning', '')) for i, d in enumerate(delar))
    ut['enskilda'] = [{'godkand': godkand(d), 'niva': niva(d), 'blockerande': len(d.get('blockerande') or []),
                       'betyg': {k: d['kriterier'][k]['betyg'] for k in KRITERIER}} for d in delar]
    return ut


# --- en omgång (körs i egen process) ---

def arbetare(rdir):
    rdir = Path(rdir)
    upp = las_json(rdir / 'UPPDRAG.json')
    slug = upp['slug']
    kund = KUNDER / slug
    try:
        shutil.copytree(kund / 'sajt' / 'dist', rdir / 'dist')
        for namn in ('copy.md', 'standard.md', 'stil/STIL.md'):
            if (kund / 'prov' / namn).is_file():
                shutil.copy2(kund / 'prov' / namn, rdir / Path(namn).name)
        bilder = skarmbilder(kund, rdir / 'sajt')
        aria = aria_trad(kund, rdir / 'sajt')
        if prova.dist_hash(rdir / 'dist') != upp['dist_sha256']:
            raise RuntimeError('bygget ändrades medan granskningen startade; kör provet och granskningen igen')
        claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
        antal = max(1, int(upp.get('granskare', 1)))
        delar, sessioner, fel = [], [], []
        with prova.Server(rdir / 'dist') as srv:
            # Två granskare (eller fler) dömer var för sig med samma kriterier, parallellt, var och en i egen session
            # och egen arbetskatalog; ingen ser den andras svar.
            korande = []
            for n in range(1, antal + 1):
                arbetskatalog = ARBETSROT / ('%s-%s-%d' % (slug, rdir.name, n))
                arbetskatalog.mkdir(parents=True, exist_ok=True)
                prompt = uppdrag_text(slug, srv.url, prova.sidor_i(rdir / 'dist'), arbetskatalog, bilder,
                                      referensbilder(slug), tidigare_byggen(slug), kalibrering(slug), rdir, aria, bildankare(slug))
                (rdir / ('PROMPT.txt' if n == 1 else 'PROMPT-%d.txt' % n)).write_text(prompt, encoding='utf-8')
                args = [claude, '-p', '--max-turns', '120', '--permission-mode', 'dontAsk', '--output-format', 'json',
                        '--setting-sources', 'project,local', '--strict-mcp-config',
                        '--model', upp['modell'], '--effort', upp['effort'],
                        '--json-schema', SCHEMA.read_text(encoding='utf-8'), '--add-dir', str(arbetskatalog),
                        '--allowedTools', *VERKTYG, '--disallowedTools', *NEKAS]
                ut = open(rdir / ('svar.json' if n == 1 else 'svar-%d.json' % n), 'wb')
                err = open(rdir / ('stderr-%d.log' % n), 'wb')
                proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=ut, stderr=err, cwd=str(ROOT), env=ren_miljo())
                proc.stdin.write(prompt.encode())  # alla får sin prompt direkt, så att de verkligen går samtidigt
                proc.stdin.close()
                korande.append((n, proc, ut, err))
            slut = time.time() + upp.get('frist', FRIST)
            for n, proc, ut, err in korande:
                try:
                    proc.wait(timeout=max(1, slut - time.time()))
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                ut.close()
                err.close()
                stderr = (rdir / ('stderr-%d.log' % n)).read_bytes()
                svar = las_json(rdir / ('svar.json' if n == 1 else 'svar-%d.json' % n)) or {}
                res = svar.get('structured_output')
                if proc.returncode or svar.get('is_error') or not isinstance(res, dict):
                    fel.append('granskare %d gav inget giltigt svar (kod %s, %s): %s' % (
                        n, proc.returncode, svar.get('subtype'), (stderr or b'').decode(errors='replace')[-300:] or str(svar.get('result'))[:300]))
                    continue
                delar.append(res)
                sessioner.append({'granskare': n, **{k: svar.get(k) for k in ('num_turns', 'duration_ms', 'session_id', 'total_cost_usd')}})
        if not delar:
            raise RuntimeError('; '.join(fel))
        res = sla_ihop(delar)
        if fel:
            res['ej_bedomt'] = list(res.get('ej_bedomt') or []) + ['En av granskarna föll, domen bygger på %d av %d: %s' % (len(delar), antal, '; '.join(fel))]
        svar = {'num_turns': sum(s.get('num_turns') or 0 for s in sessioner), 'duration_ms': max(s.get('duration_ms') or 0 for s in sessioner),
                'session_id': sessioner[0].get('session_id')}
        lage = upp.get('originalitet', 'skugga')
        if lage != 'av':
            sep = originalitet_separat(rdir, upp, slug, bilder, claude)
            res['originalitet_separat'] = sep
            if lage == 'avgor' and isinstance(sep, dict) and 'betyg' in sep:
                res['originalitet_huvud'] = res['kriterier']['originalitet']
                res['kriterier']['originalitet'] = {k: sep[k] for k in ('betyg', 'motivering', 'visa')}
                if sep['betyg'] >= TROSKEL['originalitet'] and sep['visa']:
                    res['blockerande'] = [f for f in res['blockerande'] if f.get('kriterium') != 'originalitet']
        post = {'schema': 1, 'slug': slug, 'runda': upp['runda'], 'korning': upp['korning'], 'tid': nu(),
                'startad': upp['tid'], 'dist_sha256': upp['dist_sha256'], 'modell': upp['modell'], 'effort': upp['effort'],
                'troskel': TROSKEL, 'godkand': godkand(res), 'niva': niva(res), **res,
                'session': {k: svar.get(k) for k in ('num_turns', 'duration_ms', 'session_id')}, 'sessioner': sessioner}
        (rdir / 'GRANSKNING.json').write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (rdir / 'GRANSKNING.md').write_text(markdown(post), encoding='utf-8')
    except Exception as e:  # omgången ska sluta med ett besked, aldrig tyst
        (rdir / 'FEL.txt').write_text('%s: %s\n' % (type(e).__name__, e), encoding='utf-8')
    finally:
        shutil.rmtree(rdir / 'dist', ignore_errors=True)
        (rdir / 'PAGAR').unlink(missing_ok=True)
    return 0


def originalitet_separat(rdir, upp, slug, bilder, claude):
    """En egen session som bara dömer originalitet (Anthropic: en isolerad domare per dimension). Körs i skugga bredvid
    huvudgranskaren så att vi kan se vilken av dem som stämmer bäst med ägarens domar."""
    hem = [b for b in bilder if b.parent.name == 'hem' and re.search(r'ruta-0[12]\.png$|forsta\.png$', b.name)]
    under = [b for b in bilder if b.parent.name != 'hem' and re.search(r'ruta-01\.png$|forsta\.png$', b.name)][:4]
    u = UNDERLAG / slug
    delar = ['Du dömer bara ett kriterium: originalitet, enligt avsnittet om originalitet i %s. Läs det först.' % INSTRUKTION,
             'Bär verksamhetens egna bilder, ord, material och plats sajten? Kunde ett annat företagsnamn sättas dit? Ankare:',
             '3 trasigt · 5 mall · 7 professionell nivå som ägaren kan visa · 9 i nivå med de starkaste referenserna.',
             '`visa` är ditt ja eller nej: räcker originaliteten för att ägaren ska visa sajten?', '',
             'Verksamhetens särart: %s (läs listan Bara de har)' % (rel(u / 'RESEARCH.md') if (u / 'RESEARCH.md').is_file() else 'saknas'),
             'Startsidan, de två första skärmarna i 390 och 1440:', *['- ' + rel(b) for b in hem],
             'Undersidornas första skärm:', *['- ' + rel(b) for b in under],
             'Tidigare byggens första vy:', *['- ' + rel(b) for b in tidigare_byggen(slug)],
             'Bildankare med ägarens dom:', *['- %s · %s: %s' % (n, t, ', '.join(rel(b) for b in bb)) for n, bb, t in bildankare(slug)],
             'Ägarens domar: LARDOMAR.md']
    args = [claude, '-p', '--max-turns', '40', '--permission-mode', 'dontAsk', '--output-format', 'json',
            '--setting-sources', 'project,local', '--strict-mcp-config', '--model', upp['modell'], '--effort', upp['effort'],
            '--json-schema', SCHEMA_ORIGINALITET.read_text(encoding='utf-8'), '--allowedTools', 'Read', 'Glob', 'Grep',
            '--disallowedTools', *NEKAS]
    try:
        with open(rdir / 'svar-originalitet.json', 'wb') as ut:
            p = subprocess.run(args, input='\n'.join(delar).encode(), stdout=ut, stderr=subprocess.PIPE, cwd=str(ROOT),
                               env=ren_miljo(), timeout=900)
        svar = las_json(rdir / 'svar-originalitet.json') or {}
        res = svar.get('structured_output')
        if p.returncode or not isinstance(res, dict):
            return {'fel': 'ingen giltig dom (kod %s)' % p.returncode}
        return {**res, 'lage': upp.get('originalitet', 'skugga'), 'turer': svar.get('num_turns')}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'fel': '%s: %s' % (type(e).__name__, e)}


def markdown(g):
    nv = g.get('niva')
    rad = ['# Granskning · %s · %s%s (omgång %d)' % (g['slug'], 'GODKÄND' if g['godkand'] else 'UNDERKÄND',
                                                   '' if g['godkand'] or nv is None else ', ' + NIVAER[nv], g['runda']), '',
           '%s · %s, %s · bygge %s. Godkänt kräver %s och inga blockerande fynd.' % (
               g['tid'], g['modell'], g['effort'], g['dist_sha256'][:12],
               ', '.join('%s ≥ %d' % (k, g['troskel'][k]) for k in KRITERIER)), '',
           '| Kriterium | Betyg | Motivering |', '|---|---|---|']
    for k in KRITERIER:
        x = (g.get('kriterier') or {}).get(k) or {}
        varn = '' if x.get('betyg', 0) >= g['troskel'][k] else ' (under)'
        rad.append('| %s | %s%s | %s |' % (k, x.get('betyg', '?'), varn, (x.get('motivering') or '').replace('|', '/').replace('\n', ' ')))
    if g.get('enskilda'):
        rad += ['', '%d granskare dömde var för sig; lägsta betyget och varje blockerande fynd gäller: %s.' % (
            len(g['enskilda']), '; '.join('granskare %d %s, %d blockerande' % (i, 'godkänner' if e['godkand'] else 'underkänner', e['blockerande'])
                                        for i, e in enumerate(g['enskilda'], 1)))]
    rad += ['', '## Blockerande fynd', '']
    for i, f in enumerate(g.get('blockerande') or [], 1):
        grad = ' · grad %s' % f['allvarlighet'] if f.get('allvarlighet') else ''
        punkt = ' · standard %s' % f['standardpunkt'] if f.get('standardpunkt') else ''
        punkt += ' · %s' % f['omfattning'] if f.get('omfattning') else ''
        rad.append('%d. **%s%s · %s%s.** %s Konsekvens: %s%s **Rättning:** %s%s' % (
            i, f['kriterium'] + (' (granskare %d)' % f['granskare'] if f.get('granskare') else ''), grad, f['var'], punkt, f['observation'], f['konsekvens'],
            (' Bryter: %s.' % f['heuristik']) if f.get('heuristik') else '', f['rattning'],
            ('\n   **Acceptanskriterium:** %s' % f['acceptanskriterium']) if f.get('acceptanskriterium') else ''))
    if not g.get('blockerande'):
        rad.append('Inga.')
    sep = g.get('originalitet_separat')
    if isinstance(sep, dict):
        rad += ['', '## Originalitet, egen domare (%s)' % sep.get('lage', 'skugga'), '',
                ('Fel: ' + sep['fel']) if 'fel' in sep else '%s av 10, %s visa. %s' % (sep.get('betyg'), 'ja' if sep.get('visa') else 'nej', sep.get('motivering', ''))]
    steg = g.get('kognitiv_genomgang') or []
    if steg:
        nej = [s for s in steg if not s.get('alla_ja')]
        rad += ['', '## Kognitiv genomgång', '', '%d steg, %d med minst ett nej.' % (len(steg), len(nej)), '',
                '| Uppgift | Steg | Fyra ja | Brist |', '|---|---|---|---|']
        rad += ['| %s | %s | %s | %s |' % (s['uppgift'].replace('|', '/'), s['steg'].replace('|', '/'), 'ja' if s.get('alla_ja') else 'nej',
                                          (s.get('brist') or '').replace('|', '/')) for s in steg]
    for rubrik, nyckel in (('Förbättringar', 'forbattringar'), ('Styrkor', 'styrkor'), ('Ej bedömt', 'ej_bedomt')):
        rad += ['', '## ' + rubrik, ''] + (['- ' + x for x in g.get(nyckel) or []] or ['Inga.'])
    rad += ['', '## Likhet med tidigare byggen', '', g.get('likhet_tidigare') or '-', '', '## Sammanfattning', '', g.get('sammanfattning') or '-', '']
    return '\n'.join(rad)


# --- bästa mot sista omgången ---

def summa(g):
    return (bool(g.get('godkand')), sum((g.get('kriterier') or {}).get(n, {}).get('betyg', 0) for n in KRITERIER))


def jamfor(slug):
    """Parvis jämförelse av omgångens skärmbilder: bästa mot sista, två gånger med ombytt ordning; oenighet = lika.
    Anthropics harness-artikel: en mellanomgång var ibland bättre än den sista."""
    gdir = KUNDER / slug / 'granskning'
    klara = [(r, las_json(r / 'GRANSKNING.json')) for r in rundor(gdir)]
    klara = [(r, g) for r, g in klara if g and (r / 'sajt' / 'hem').is_dir()]
    if len(klara) < 2:
        print('Färre än två granskade omgångar med skärmbilder; inget att jämföra.')
        return 0
    sista = klara[-1]
    basta = max(klara[:-1], key=lambda x: summa(x[1]))
    if summa(sista[1]) >= summa(basta[1]):
        print('Sista omgången (%s) har minst lika höga betyg som de tidigare; ingen jämförelse behövs.' % sista[0].name)
        return 0
    bilder = lambda r: [b for b in sorted((r / 'sajt' / 'hem').glob('vy-*-ruta-0[12].png'))] or sorted((r / 'sajt' / 'hem').glob('vy-*-forsta.png'))  # noqa: E731
    claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
    domar = []
    for a, b in ((basta, sista), (sista, basta)):
        delar = ['Två versioner av samma sajt, A och B, för samma verksamhet. Titta på varje bild med Read.',
                 'Vilken skulle ägaren hellre visa för verksamheten? Väg helhet, originalitet ur verksamhetens material,',
                 'hantverk och hur lätt besökaren tar kontakt. Svara A, B eller lika, med skäl. Läs %s för måttstocken.' % INSTRUKTION, '',
                 'A, startsidans två första skärmar i 390 och 1440:', *['- ' + rel(x) for x in bilder(a[0])],
                 'B, startsidans två första skärmar i 390 och 1440:', *['- ' + rel(x) for x in bilder(b[0])]]
        args = [claude, '-p', '--max-turns', '20', '--permission-mode', 'dontAsk', '--output-format', 'json',
                '--setting-sources', 'project,local', '--strict-mcp-config', '--model', 'opus[1m]', '--effort', 'high',
                '--json-schema', SCHEMA_JAMFORELSE.read_text(encoding='utf-8'), '--allowedTools', 'Read', '--disallowedTools', *NEKAS]
        p = subprocess.run(args, input='\n'.join(delar).encode(), capture_output=True, cwd=str(ROOT), env=ren_miljo(), timeout=600)
        try:
            res = json.loads(p.stdout or b'{}').get('structured_output') or {}
        except ValueError:
            res = {}
        val = res.get('val')
        domar.append({'A': a[0].name, 'B': b[0].name, 'val': val, 'vinnare': {'A': a[0].name, 'B': b[0].name}.get(val, 'lika'), 'skal': res.get('skal', '')})
    vinnare = domar[0]['vinnare'] if domar[0]['vinnare'] == domar[1]['vinnare'] else 'lika'
    ut = {'tid': nu(), 'basta': basta[0].name, 'sista': sista[0].name, 'vinnare': vinnare, 'domar': domar}
    (gdir / 'JAMFORELSE-OMGANGAR.json').write_text(json.dumps(ut, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    md = ['# Bästa mot sista omgången', '', 'Bästa enligt betygen: %s · sista: %s · vinnare: **%s**' % (basta[0].name, sista[0].name, vinnare), '']
    md += ['- Ordning A=%s, B=%s: %s. %s' % (d['A'], d['B'], d['val'] or 'inget svar', d['skal']) for d in domar]
    (gdir / 'JAMFORELSE-OMGANGAR.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    return 0


# --- kommandot ---

def rundor(gdir):
    return sorted(p for p in gdir.glob('runda-*') if p.is_dir())


def utfall(rdir):
    g = las_json(rdir / 'GRANSKNING.json')
    if g:
        return g
    if (rdir / 'FEL.txt').is_file():
        return {'fel': (rdir / 'FEL.txt').read_text(encoding='utf-8').strip()}
    return None


def svara(gdir, rdir, g):
    if 'fel' in g:
        print('Granskaren föll i %s: %s' % (rdir.name, g['fel']))
        return 4
    shutil.copy2(rdir / 'GRANSKNING.json', gdir / 'GRANSKNING.json')
    shutil.copy2(rdir / 'GRANSKNING.md', gdir / 'GRANSKNING.md')
    print((rdir / 'GRANSKNING.md').read_text(encoding='utf-8'))
    print('Hela granskningen: %s' % rel(gdir / 'GRANSKNING.md'))
    return 0 if g['godkand'] else 1


def vanta(gdir, rdir, sekunder, proc=None):
    slut = time.time() + sekunder
    while time.time() < slut:
        g = utfall(rdir)
        if g:
            return svara(gdir, rdir, g)
        pagar = rdir / 'PAGAR'
        pid = int(pagar.read_text().strip() or 0) if pagar.is_file() else 0
        if (proc.poll() is not None) if proc else not lever(pid):
            time.sleep(2)
            g = utfall(rdir)
            if g:
                return svara(gdir, rdir, g)
            (rdir / 'FEL.txt').write_text('granskarens process avslutades utan svar; se %s\n' % rel(rdir / 'arbetare.log'), encoding='utf-8')
            return svara(gdir, rdir, utfall(rdir))
        time.sleep(5)
    print('Granskningen pågår (%s, startad %s). Kör samma kommando igen för att vänta vidare.' % (
        rdir.name, (las_json(rdir / 'UPPDRAG.json') or {}).get('tid', '?')))
    return 5


def main(argv=None):
    p = argparse.ArgumentParser(prog='granska', description=__doc__.split('\n\n')[0])
    p.add_argument('slug', nargs='?')
    p.add_argument('--vanta', type=int, default=540)
    p.add_argument('--om', action='store_true')
    p.add_argument('--torr', action='store_true', help='bygg uppdraget och skriv det, utan att starta granskaren')
    p.add_argument('--jamfor', action='store_true', help='jämför bästa och sista omgången parvis')
    p.add_argument('--arbetare', help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    if a.arbetare:
        return arbetare(a.arbetare)
    if not a.slug or not SLUG.match(a.slug):
        p.print_usage()
        return 2
    if a.jamfor:
        return jamfor(a.slug)
    kund = KUNDER / a.slug
    dist = kund / 'sajt' / 'dist'
    status = las_json(kund / 'prov' / 'STATUS.json') or {}
    if not (dist / 'index.html').is_file():
        print('Inget bygge att granska: kör .venv/bin/python kontroller/prova.py %s --snabb först.' % a.slug)
        return 2
    hash_nu = prova.dist_hash(dist)
    if status.get('dist_sha256') != hash_nu:
        print('Provets skärmbilder gäller inte det nuvarande bygget. Kör .venv/bin/python kontroller/prova.py %s --snabb '
              'och sedan granskningen igen.' % a.slug)
        return 2
    gdir = kund / 'granskning'
    gdir.mkdir(exist_ok=True)
    korning = os.environ.get('NWP_KORNING') or 'manuell'

    if a.torr:
        rdir = Path(tempfile.mkdtemp(prefix='nwp-torr-'))
        bilder = skarmbilder(kund, rdir / 'sajt')
        for namn in ('copy.md', 'standard.md', 'stil/STIL.md'):
            if (kund / 'prov' / namn).is_file():
                shutil.copy2(kund / 'prov' / namn, rdir / Path(namn).name)
        prompt = uppdrag_text(a.slug, 'http://127.0.0.1:PORT', prova.sidor_i(dist), ARBETSROT / 'torr', bilder,
                              referensbilder(a.slug), tidigare_byggen(a.slug), kalibrering(a.slug), rdir,
                              aria_trad(kund, rdir / 'sajt'), bildankare(a.slug))
        (rdir / 'PROMPT.txt').write_text(prompt, encoding='utf-8')
        print(prompt)
        print('Torrkörning: %s. Ingen granskare startades.' % (rdir / 'PROMPT.txt'))
        return 0

    for r in reversed(rundor(gdir)):
        upp = las_json(r / 'UPPDRAG.json') or {}
        pagar = r / 'PAGAR'
        if pagar.is_file() and not utfall(r):
            pid = int(pagar.read_text().strip() or 0)
            if lever(pid) and upp.get('dist_sha256') == hash_nu:
                return vanta(gdir, r, a.vanta)
            if lever(pid):  # granskar ett äldre bygge: avbryt den
                try:
                    os.killpg(pid, signal.SIGTERM)
                except OSError:
                    pass
            (r / 'FEL.txt').write_text('avbruten: bygget ändrades eller processen dog\n', encoding='utf-8')
            pagar.unlink(missing_ok=True)
    if not a.om:
        for r in reversed(rundor(gdir)):
            g = las_json(r / 'GRANSKNING.json')
            if g and g.get('dist_sha256') == hash_nu:
                print('(Samma bygge är redan granskat i %s; ingen ny session.)' % r.name)
                return svara(gdir, r, g)

    egna = [r for r in rundor(gdir) if (las_json(r / 'UPPDRAG.json') or {}).get('korning') == korning]
    if len(egna) >= MAX_RUNDOR:
        print('Taket nått: %d granskningar i den här körningen (NWP_GRANSKNING_MAX=%d). Senaste dom: %s' % (
            len(egna), MAX_RUNDOR, rel(gdir / 'GRANSKNING.md') if (gdir / 'GRANSKNING.md').is_file() else 'ingen'))
        return 3
    n = max([int(r.name.split('-')[1]) for r in rundor(gdir)] or [0]) + 1
    rdir = gdir / ('runda-%02d' % n)
    rdir.mkdir()
    upp = {'slug': a.slug, 'runda': n, 'korning': korning, 'tid': nu(), 'dist_sha256': hash_nu,
           'modell': os.environ.get('NWP_GRANSKARE_MODELL') or 'opus[1m]',
           'effort': os.environ.get('NWP_GRANSKARE_EFFORT') or 'high', 'frist': FRIST, 'granskare': ANTAL,
           'originalitet': os.environ.get('NWP_GRANSKNING_ORIGINALITET', 'skugga') if os.environ.get('NWP_GRANSKNING_ORIGINALITET', 'skugga') in ORIGINALITETSLAGEN else 'skugga'}
    (rdir / 'UPPDRAG.json').write_text(json.dumps(upp, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with open(rdir / 'arbetare.log', 'wb') as logg:
        proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--arbetare', str(rdir)],
                                cwd=str(ROOT), env=ren_miljo(), stdin=subprocess.DEVNULL, stdout=logg,
                                stderr=subprocess.STDOUT, start_new_session=True)
    (rdir / 'PAGAR').write_text(str(proc.pid))
    print('Granskningen startad: %s (%s, %s). Väntar högst %d s.' % (rdir.name, upp['modell'], upp['effort'], a.vanta), flush=True)
    return vanta(gdir, rdir, a.vanta, proc)


if __name__ == '__main__':
    sys.exit(main())
