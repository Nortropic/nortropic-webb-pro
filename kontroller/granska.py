#!/usr/bin/env python3
"""granska.py — oberoende granskning av ett bygge: en egen Claude-session, utan byggarens resonemang, dömer den färdiga
sajten efter kritik/GRANSKARE.md och sätter betyg på fem kriterier. Kritiken går tillbaka till byggaren tills sajten
håller (generator och granskare, Anthropic "Harness design for long-running application development").

    .venv/bin/python kontroller/granska.py <slug> [--vanta SEK] [--om]

Kör först `kontroller/prova.py <slug> --snabb` (eller hela provet): granskningen gäller exakt det bygge som provet
senast byggde och tar provets skärmbilder som underlag. Granskaren körs i en egen process som överlever kommandot;
kommandot väntar på svaret högst --vanta sekunder (540). Pågår granskningen fortfarande: kör samma kommando igen.
Ett bygge som redan granskats svarar direkt med samma dom, utan ny session (--om tvingar en ny).

Resultat i kunder/<slug>/granskning/: GRANSKNING.json och GRANSKNING.md (senaste), runda-NN/ per omgång.
Exit: 0 godkänd · 1 underkänd · 2 fel i anropet eller saknat bygge · 3 taket för omgångar nått · 4 granskaren föll ·
5 pågår, kör igen.

Miljö: NWP_GRANSKARE_MODELL (opus[1m]), NWP_GRANSKARE_EFFORT (high), NWP_GRANSKNING_MAX (5 omgångar per körning),
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
KRITERIER = ('designkvalitet', 'originalitet', 'hantverk', 'funktion', 'text')
TROSKEL = {k: 7 for k in KRITERIER}
MAX_RUNDOR = int(os.environ.get('NWP_GRANSKNING_MAX', '5'))
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


def godkand(resultat):
    k = resultat.get('kriterier') or {}
    betyg_ok = all(isinstance((k.get(n) or {}).get('betyg'), int) and k[n]['betyg'] >= TROSKEL[n] for n in KRITERIER)
    return betyg_ok and not resultat.get('blockerande')


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
    andra = [p for p in KUNDER.iterdir() if p.is_dir() and SLUG.match(p.name) and p.name != slug and not p.name.startswith('rokprov')]
    andra.sort(key=lambda p: (p / 'prov' / 'STATUS.json').stat().st_mtime if (p / 'prov' / 'STATUS.json').is_file() else 0, reverse=True)
    ut = []
    for p in andra[:6]:
        for vy in ('vy-390-forsta.png', 'vy-1440-forsta.png'):
            f = p / 'prov' / 'inspektion' / 'hem' / vy
            if f.is_file():
                ut.append(f)
    return ut


def kalibrering():
    """Ägarens domar bredvid granskarens betyg för samma bygge: underlag för att döma som ägaren."""
    rader = []
    for p in sorted(KUNDER.iterdir()) if KUNDER.is_dir() else []:
        dom = (las_json(p / 'DOM.json') or {}).get('domar') or []
        g = las_json(p / 'granskning' / 'GRANSKNING.json')
        if not dom:
            continue
        svar = dom[-1].get('svar') or {}
        agaren = '; '.join('%s: %s' % (k, str(svar[k]).replace('\n', ' ')[:300]) for k in
                           ('namn', 'battre', 'specifik', 'mall_tecken', 'samsta', 'basta', 'en_andring') if svar.get(k) not in (None, ''))
        if g:
            betyg = ', '.join('%s %s' % (n, (g.get('kriterier') or {}).get(n, {}).get('betyg', '?')) for n in KRITERIER)
            gr = 'granskaren: %s (%s)' % ('godkänd' if g.get('godkand') else 'underkänd', betyg)
        else:
            gr = 'ingen granskning'
        rader.append('- %s · %s · ägaren: %s' % (p.name, gr, agaren or 'inga svar'))
    return rader


def uppdrag_text(slug, url, sidor, arbetskatalog, bilder, refs, tidigare, kal, rdir, aria=()):
    u = UNDERLAG / slug
    v = las_json(u / 'VERKSAMHET.json') or {}
    rad = lambda p: '- ' + (rel(p) if str(p).startswith(str(ROOT)) else str(p))  # noqa: E731
    underlag = [u / f for f in ('VERKSAMHET.json', 'RESEARCH.md', 'BRIEF.md', 'REFERENSER.md') if (u / f).is_file()]
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
        'Verksamhetens underlag:', *[rad(p) for p in underlag], '',
        'Sajtens skärmbilder från provet, varje sida uppifrån och ned i skärmhöga rutor i 390 och 1440 (läs varje):',
        *[rad(p) for p in bilder], '',
        'Tillgänglighetsträdet i 390 px per sida:', *([rad(p) for p in aria] or ['- saknas']), ''
        'Byggstandardens maskinella fynd: %s' % (rad(rdir / 'standard.md')[2:] if (rdir / 'standard.md').is_file() else 'saknas'),
        'Copykontrollens fynd: %s' % (rad(rdir / 'copy.md')[2:] if (rdir / 'copy.md').is_file() else 'saknas'), '',
        'Referensernas skärmbilder:', *([rad(p) for p in refs] or ['- inga']), '',
        'Tidigare byggens första vy:', *([rad(p) for p in tidigare] or ['- inga']), '',
        'Måttstockar:', *['- %s: %s' % (namn, f) for namn, f in MATTSTOCKAR if (ROOT / f).is_file()],
    ]
    return '\n'.join(delar) + '\n'


# --- en omgång (körs i egen process) ---

def arbetare(rdir):
    rdir = Path(rdir)
    upp = las_json(rdir / 'UPPDRAG.json')
    slug = upp['slug']
    kund = KUNDER / slug
    try:
        shutil.copytree(kund / 'sajt' / 'dist', rdir / 'dist')
        for namn in ('copy.md', 'standard.md'):
            if (kund / 'prov' / namn).is_file():
                shutil.copy2(kund / 'prov' / namn, rdir / namn)
        bilder = skarmbilder(kund, rdir / 'sajt')
        aria = aria_trad(kund, rdir / 'sajt')
        if prova.dist_hash(rdir / 'dist') != upp['dist_sha256']:
            raise RuntimeError('bygget ändrades medan granskningen startade; kör provet och granskningen igen')
        arbetskatalog = ARBETSROT / ('%s-%s' % (slug, rdir.name))
        arbetskatalog.mkdir(parents=True, exist_ok=True)
        claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
        with prova.Server(rdir / 'dist') as srv:
            prompt = uppdrag_text(slug, srv.url, prova.sidor_i(rdir / 'dist'), arbetskatalog, bilder,
                                  referensbilder(slug), tidigare_byggen(slug), kalibrering(), rdir, aria)
            (rdir / 'PROMPT.txt').write_text(prompt, encoding='utf-8')
            args = [claude, '-p', '--max-turns', '120', '--permission-mode', 'dontAsk', '--output-format', 'json',
                    '--setting-sources', 'project,local', '--strict-mcp-config',
                    '--model', upp['modell'], '--effort', upp['effort'],
                    '--json-schema', SCHEMA.read_text(encoding='utf-8'), '--add-dir', str(arbetskatalog),
                    '--allowedTools', *VERKTYG, '--disallowedTools', *NEKAS]
            with open(rdir / 'svar.json', 'wb') as ut:
                p = subprocess.run(args, input=prompt.encode(), stdout=ut, stderr=subprocess.PIPE, cwd=str(ROOT),
                                   env=ren_miljo(), timeout=upp.get('frist', FRIST))
        svar = las_json(rdir / 'svar.json') or {}
        res = svar.get('structured_output')
        if p.returncode or svar.get('is_error') or not isinstance(res, dict):
            raise RuntimeError('granskarens session gav inget giltigt svar (kod %s, %s): %s' % (
                p.returncode, svar.get('subtype'), (p.stderr or b'').decode(errors='replace')[-500:] or str(svar.get('result'))[:500]))
        post = {'schema': 1, 'slug': slug, 'runda': upp['runda'], 'korning': upp['korning'], 'tid': nu(),
                'startad': upp['tid'], 'dist_sha256': upp['dist_sha256'], 'modell': upp['modell'], 'effort': upp['effort'],
                'troskel': TROSKEL, 'godkand': godkand(res), **res,
                'session': {k: svar.get(k) for k in ('num_turns', 'duration_ms', 'session_id')}}
        (rdir / 'GRANSKNING.json').write_text(json.dumps(post, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (rdir / 'GRANSKNING.md').write_text(markdown(post), encoding='utf-8')
    except Exception as e:  # omgången ska sluta med ett besked, aldrig tyst
        (rdir / 'FEL.txt').write_text('%s: %s\n' % (type(e).__name__, e), encoding='utf-8')
    finally:
        shutil.rmtree(rdir / 'dist', ignore_errors=True)
        (rdir / 'PAGAR').unlink(missing_ok=True)
    return 0


def markdown(g):
    rad = ['# Granskning · %s · %s (omgång %d)' % (g['slug'], 'GODKÄND' if g['godkand'] else 'UNDERKÄND', g['runda']), '',
           '%s · %s, %s · bygge %s. Godkänt kräver %s och inga blockerande fynd.' % (
               g['tid'], g['modell'], g['effort'], g['dist_sha256'][:12],
               ', '.join('%s ≥ %d' % (k, g['troskel'][k]) for k in KRITERIER)), '',
           '| Kriterium | Betyg | Motivering |', '|---|---|---|']
    for k in KRITERIER:
        x = (g.get('kriterier') or {}).get(k) or {}
        varn = '' if x.get('betyg', 0) >= g['troskel'][k] else ' (under)'
        rad.append('| %s | %s%s | %s |' % (k, x.get('betyg', '?'), varn, (x.get('motivering') or '').replace('|', '/').replace('\n', ' ')))
    rad += ['', '## Blockerande fynd', '']
    for i, f in enumerate(g.get('blockerande') or [], 1):
        grad = ' · grad %s' % f['allvarlighet'] if f.get('allvarlighet') else ''
        punkt = ' · standard %s' % f['standardpunkt'] if f.get('standardpunkt') else ''
        rad.append('%d. **%s%s · %s%s.** %s Konsekvens: %s%s **Rättning:** %s%s' % (
            i, f['kriterium'], grad, f['var'], punkt, f['observation'], f['konsekvens'],
            (' Bryter: %s.' % f['heuristik']) if f.get('heuristik') else '', f['rattning'],
            ('\n   **Acceptanskriterium:** %s' % f['acceptanskriterium']) if f.get('acceptanskriterium') else ''))
    if not g.get('blockerande'):
        rad.append('Inga.')
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
    p.add_argument('--arbetare', help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    if a.arbetare:
        return arbetare(a.arbetare)
    if not a.slug or not SLUG.match(a.slug):
        p.print_usage()
        return 2
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
        for namn in ('copy.md', 'standard.md'):
            if (kund / 'prov' / namn).is_file():
                shutil.copy2(kund / 'prov' / namn, rdir / namn)
        prompt = uppdrag_text(a.slug, 'http://127.0.0.1:PORT', prova.sidor_i(dist), ARBETSROT / 'torr', bilder,
                              referensbilder(a.slug), tidigare_byggen(a.slug), kalibrering(), rdir,
                              aria_trad(kund, rdir / 'sajt'))
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
           'effort': os.environ.get('NWP_GRANSKARE_EFFORT') or 'high', 'frist': FRIST}
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
