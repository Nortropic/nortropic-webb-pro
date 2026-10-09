#!/usr/bin/env python3
"""kundrepo.py — kundprojektets eget repo och leveransvägen (ägarens uppdrag 2026-10-07, punkt 3, 4 och 10; 2026-10-08, 2A–2B).

Varje kundprojekt får från projektstarten (kontroller/ny_sajt.py --installera, via ateljén) ett eget lokalt git-repo i
kunder/<slug>/kundrepo med ett kort CLAUDE.md, och en verklig verksamhet (VERKSAMHET.json utan fiktiv: true) ett privat
GitHub-repo Nortropic/kund-<slug> (ägarens svar 2026-10-07: organisationen Nortropic). Identiteten står i
kunder/<slug>/KUNDREPO.json: projekt-id, slug, namn, lokal väg, fjärrepot med status och senaste push.
Samma repo återanvänds vid fortsättning, nya kandidater och återförsök; skapandet är idempotent och låst per kund
(.kundrepo.las), och ett GitHub-repo med samma namn som inte bär projektets markör i beskrivningen binds aldrig
(status namnkonflikt). Lokal skapning som lyckats men fjärrskapning som misslyckats står som det (status fel, med skälet).

Exporten (kontroller/exportera.py) blir en commit i det beständiga repot (synka_export) i stället för ett katalogbyte,
pushas till fjärrepot när det är bundet (push), och förhandsvisningen (preview) driftsätts på Cloudflare Workers
(ägarens beslut 2026-10-09: Cloudflare är målplattform, Vercel är det inte längre) som Workern kund-<slug>-forhandsvisning
(wrangler deploy --env forhandsvisning, utan databas, bucket och mejlhemlighet), byggd ur commitens frysta filer; kvittot
kunder/<slug>/leverans/PREVIEW-<tid>.json bär commit, export, Cloudflares versions-id, adress, skydd och status. Kontot
är Nortropics anslutna Cloudflare-konto (~/.nortropic-hemligheter/webb-pro/cloudflare.env, 0600: en avgränsad API-token,
konto-id och workers.dev-underdomänen); saknas det står förhandsvisningen som väntande med den exakta handlingen, och inget
faller tillbaka på Vercel. För en verklig verksamhet laddas inget upp förrän Cloudflare Access skyddar förhandsvisningens
adress, och skyddet prövas igen efter uppladdningen. En förhandsvisning är aldrig produktion; produktionspublicering är
ett eget ägarbeslut.

Privat underlag och hemligheter följer aldrig med: repot får bara exportens filer (exportera.lackor fäller lokala
sökvägar, privat underlag och nycklar) och CLAUDE.md nämner inget privat. Före varje push, också den första vid
fjärrskapningen och när ett äldre kundrepo återanvänds, prövas det som faktiskt skickas: varje commit som nås från den
commit som ska pushas, med varje fils innehåll, sökväg och commitmeddelande, också det som lagts till och sedan tagits
bort (historikens_lackor; N04 i GR-20261009-natt-omgranskning-codex). Granskningen och pushen gäller samma commit
(git push origin <commit>:refs/heads/main), och beskedet nämner commit, fil och slag av läcka, aldrig värdet. Historiken
skrivs aldrig om eller raderas här: en läcka i en tidigare commit stoppar pushen och väntar på ägaren. Projektstarten
committar bara sina egna filer (CLAUDE.md och .gitignore). gh används som det är inloggat (ägarens konto); Wrangler får
bara det anslutna Cloudflare-kontots token, i sin egen process; saknas något står det i kvittot, och inget skapas av gissning.

    .venv/bin/python kontroller/kundrepo.py <slug>              # skapa eller återanvänd (lokalt + fjärr när tillåtet)
    .venv/bin/python kontroller/kundrepo.py <slug> --utan-fjarr # bara lokalt
    .venv/bin/python kontroller/kundrepo.py <slug> --push       # pusha main till det bundna fjärrepot
    .venv/bin/python kontroller/kundrepo.py <slug> --preview    # förhandsvisning av exportens commit, med kvitto
    .venv/bin/python kontroller/kundrepo.py <slug> --visa       # kvittot
Slutkod 0 när det begärda gjordes, 1 när ett hinder stod i vägen (står i kvittot), 2 vid ogiltigt anrop.
"""
import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402

def _root():
    return atelje.ROOT


def _kunder():
    return atelje.KUNDER


def _underlag():
    return atelje.UNDERLAG


ORG = 'Nortropic'          # ägarens svar 2026-10-07 ~14:30Z: kundrepona i organisationen, inte på kontot
CLOUDFLARE_FIL = Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'cloudflare.env'  # NWP_CLOUDFLARE_FIL i proven
MARKOR = 'nortropic-projekt:'
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
FRIST = 180
GIT_IDENTITET = ['-c', 'user.name=Nortropic', '-c', 'user.email=noreply@nortropic.se']
nu = atelje.nu


class Hinder(Exception):
    """Det begärda gick inte: skälet står i kvittot."""


def identitet(slug):
    if not SLUG.match(slug or ''):
        raise ValueError('ogiltig slug')
    namn = 'kund-%s' % slug
    return {'slug': slug, 'namn': namn, 'org': ORG, 'worker': namn, 'worker_forhandsvisning': namn + '-forhandsvisning', 'lokal': 'kunder/%s/kundrepo' % slug,
            'fjarr_adress': 'https://github.com/%s/%s' % (ORG, namn)}


def repo(slug):
    return _kunder() / slug / 'kundrepo'


def kvittofil(slug, kund=None):
    return (Path(kund) if kund else _kunder() / slug) / 'KUNDREPO.json'


def las_kvitto(slug, kund=None):
    p = kvittofil(slug, kund)
    try:
        d = json.loads(p.read_text(encoding='utf-8')) if p.is_file() and not p.is_symlink() else None
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def ar_repo(p):
    p = Path(p)
    return p.is_dir() and not p.is_symlink() and (p / '.git').is_dir()


def git(rot, *args, frist=FRIST):
    return subprocess.run(['git', *GIT_IDENTITET, *args], cwd=str(rot), capture_output=True, text=True, timeout=frist)


def git_ok(rot, *args, frist=FRIST):
    r = git(rot, *args, frist=frist)
    if r.returncode:
        raise RuntimeError('git %s föll: %s' % (args[0], (r.stderr or r.stdout)[-400:].strip()))
    return r.stdout.strip()


def huvud(rot):
    """HEAD-commit, eller None i ett repo utan commit."""
    r = git(rot, 'rev-parse', 'HEAD')
    return r.stdout.strip() if r.returncode == 0 else None


def verksamhet(slug, underlag=None):
    try:
        d = json.loads(((Path(underlag) if underlag else _underlag()) / slug / 'VERKSAMHET.json').read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def fiktiv(slug):
    """En fiktiv verksamhet (piloten, proven) får aldrig ett fjärrepo i organisationen."""
    return verksamhet(slug).get('fiktiv') is True


def motorversion():
    try:
        r = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=str(_root()), capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or 'okänd' if r.returncode == 0 else 'okänd'
    except (OSError, subprocess.SubprocessError):
        return 'okänd'


def primar_handling(slug, underlag=None):
    """Besökarens viktigaste uppgift som en hänvisning, aldrig briefens text: briefen är Nortropics privata råunderlag och
    följer inte med till kundrepot (R08 i GR-20261008-06af6ff-omgranskning-codex); i en export bär DESIGN.md designens
    uppgift, som är godkänd text i projektet."""
    return 'står i Nortropics brief (privat underlag, följer inte med hit); i en export beskriver DESIGN.md designens uppgift'


def claude_md(slug, export_id=None, underlag=None):
    """Det korta projektspecifika CLAUDE.md (uppdraget 2026-10-07, punkt 4): syfte och besökaruppgift, teknik och
    kommandon, kodstruktur, design- och faktakälla, begränsningar, prov och leverans. Inget privat, inga lokala vägar."""
    v = verksamhet(slug, underlag)
    namn = str(v.get('namn') or slug)
    tjanster = [str(t) for t in (v.get('tjanster') or []) if isinstance(t, str)][:6]
    i = identitet(slug)
    return '\n'.join([
        '# %s — webbplatsen för %s' % (i['namn'], namn), '',
        'Projektet är en leverans från Nortropic. Motorn nortropic-webb-pro (version %s) bygger, granskar och exporterar; det här' % motorversion(),
        'repot innehåller bara det levererbara: sajtens källkod, låsta beroenden och projektkonfiguration. Kundens råunderlag,',
        'intervjuer, bedömningar, transkript och referensmaterial ligger kvar privat hos Nortropic och läggs aldrig här.', '',
        '## Syfte och besökarens viktigaste uppgift', '',
        '- Verksamheten: %s%s.' % (namn, (' (%s)' % ', '.join(tjanster)) if tjanster else ''),
        '- Besökarens viktigaste uppgift: %s.' % primar_handling(slug, underlag), '',
        '## Teknik och kommandon', '',
        'Astro för Cloudflare Workers, Node 24 för bygget. `npm ci` installerar de låsta versionerna, `npm run build` bygger de',
        'förrenderade sidorna i dist/, `npm run dev` kör lokalt, `npx wrangler dev` kör sidorna och Workern lokalt i workerd.', '',
        '## Kodstruktur', '',
        '`src/pages/` sidorna, `src/components/`, `src/layouts/`, `src/styles/`, `public/` statiska filer (med `_headers`),',
        '`worker/index.js` formulärets mottagning, `migrations/` dess D1-schema och `wrangler.jsonc` Workerns konfiguration.',
        '`DESIGN.md` beskriver designen när den är exporterad; `LICENSER.md` licensunderlaget.', '',
        '## Design- och faktakälla', '',
        '- Designen: `DESIGN.md` i repot%s. Ändra inte riktningen utan Nortropics och kundens beslut.' % (' (export %s)' % export_id if export_id else ''),
        '- Fakta om verksamheten: Nortropics verifierade underlag, aldrig påhittade uppgifter, omdömen, siffror eller meriter.',
        '- Ingen tidigare kunds färgval, typsnitt, smakdomar eller riktning ärvs av det här projektet.', '',
        '## Begränsningar', '',
        '- Inga hemligheter i repot: de läggs med `wrangler secret put` (se `.env.example`), aldrig i `vars` eller i en fil här.',
        '- Formuläret postar till `/api/forfragan/` (Workern sparar i D1 och R2 före aviseringen) och landar på `/tack/`,',
        '  `/mottagen/` eller en felsida med texten kvar.',
        '- Innehåll och navigation fungerar utan JavaScript; inline-händelser stoppas av CSP:n.', '',
        '## Prov och leverans', '',
        '- `npm run build` ska gå igenom; Nortropics export kör byggprovet och läckagekontrollen före varje commit hit.',
        '- Leveransen: export → commit i det här repot → förhandsvisning i Workern %s (Cloudflare, skyddad), bunden till' % i['worker_forhandsvisning'],
        '  commit och export-id → produktion först efter Nortropics och kundens uttryckliga godkännande.', ''])


def kommando(argv, cwd, frist=FRIST, env=None):
    try:
        return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=frist, env=env)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(argv, 124, '', 'tidsgränsen %d s nåddes' % frist)


def fjarr_skapa(slug, kv):
    """Det privata GitHub-repot i organisationen: binds bara när beskrivningen bär projektets markör. Ger statusdelen."""
    i = identitet(slug)
    gh = shutil.which('gh')
    tid = nu()
    if not gh:
        return {'status': 'fel', 'tid': tid, 'fel': 'gh saknas i PATH', 'adress': None}
    r = kommando([gh, 'api', 'repos/%s/%s' % (ORG, i['namn'])], repo(slug))
    if r.returncode == 0:
        try:
            d = json.loads(r.stdout)
        except ValueError:
            d = {}
        if MARKOR + kv['projekt_id'] in str(d.get('description') or ''):
            git(repo(slug), 'remote', 'remove', 'origin')
            git_ok(repo(slug), 'remote', 'add', 'origin', str(d.get('clone_url') or d.get('html_url') or i['fjarr_adress']))
            return {'status': 'skapat', 'tid': tid, 'fel': None, 'adress': str(d.get('html_url') or i['fjarr_adress']), 'privat': bool(d.get('private', True)), 'ateranvant': True}
        return {'status': 'namnkonflikt', 'tid': tid, 'adress': None,
                'fel': '%s/%s finns redan utan projektets markör i beskrivningen; repot binds inte (ingen koppling till fel kund)' % (ORG, i['namn'])}
    if 'HTTP 404' not in (r.stderr or '') and 'Not Found' not in (r.stderr or ''):
        return {'status': 'fel', 'tid': tid, 'adress': None, 'fel': 'gh api: %s' % (r.stderr or r.stdout)[-300:].strip()}
    # R08 och N04: inget fjärrepo och ingen push av något som läckagekontrollen fäller, i arbetskatalogen eller i historiken
    kandidat = huvud(repo(slug))
    lackor = granskning_fore_push(repo(slug), kandidat)
    if lackor:
        return {'status': 'fel', 'tid': tid, 'adress': None, 'fel': 'läckagekontrollen fällde repot: %s' % besked(lackor)}
    beskrivning = '%s%s Webbplats åt %s, levererad av Nortropic' % (MARKOR, kv['projekt_id'], str(verksamhet(slug).get('namn') or slug)[:60])
    # fjärrepot skapas utan --push: den första pushen går genom samma granskning och samma commit som varje senare (N04)
    r = kommando([gh, 'repo', 'create', '%s/%s' % (ORG, i['namn']), '--private', '--description', beskrivning,
                  '--source', str(repo(slug)), '--remote', 'origin'], repo(slug), frist=300)
    if r.returncode:
        return {'status': 'fel', 'tid': tid, 'adress': None, 'fel': 'gh repo create: %s' % (r.stderr or r.stdout)[-300:].strip()}
    ut = {'status': 'skapat', 'tid': tid, 'fel': None, 'adress': i['fjarr_adress'], 'privat': True, 'ateranvant': False}
    if kandidat:
        ut['forsta_push'] = pusha_granskad(repo(slug), kandidat)
    return ut


def lackor_i(rot):
    """Exportens läckagekontroll (exportera.lackor: lokala sökvägar, Nortropics privata underlag, nycklar) på katalogen."""
    import exportera
    return exportera.lackor(rot)


def _textblob(data):
    """Texten i en blob som inte ser binär ut (ingen NUL-byte i början), annars None."""
    if b'\x00' in data[:8000]:
        return None
    return data.decode('utf-8', errors='replace')


def historikens_lackor(rot, commit):
    """N04: läckagekontrollen på det som en push av commit faktiskt skickar: varje commit som nås från den, med varje
    textfils innehåll (också en fil som lagts till och sedan tagits bort, och en fil utan känd ändelse som .env), varje
    sökväg och varje commitmeddelande, mot exportens mönster (exportera.LACKA; package-lock.json och node_modules som där).
    Ger [(commit, plats, skäl)] utan värden. Kan historiken inte läsas blir det en egen rad: kontrollen stänger vid fel."""
    import exportera
    if not commit:
        return []
    fel = lambda e: [(str(commit)[:12], '-', 'historiken gick inte att läsa (%s)' % e)]  # noqa: E731
    try:
        rl = git(rot, 'rev-list', commit)
        if rl.returncode:
            return fel('rev-list')
        commits = rl.stdout.split()
        ut, sedda, blobbar = [], set(), {}
        for c in commits:
            m = subprocess.run(['git', 'log', '-1', '--format=%B', c], cwd=str(rot), capture_output=True, timeout=FRIST)
            if m.returncode:
                return fel('log')
            text = m.stdout.decode('utf-8', errors='replace')
            ut += [(c[:12], 'commitmeddelandet', skal) for monster, skal in exportera.LACKA if monster.search(text)]
            lt = subprocess.run(['git', 'ls-tree', '-r', '-z', c], cwd=str(rot), capture_output=True, timeout=FRIST)
            if lt.returncode:
                return fel('ls-tree')
            for post in lt.stdout.split(b'\x00'):
                if not post:
                    continue
                meta, vag = post.split(b'\t', 1)
                typ, sha = meta.split()[1].decode(), meta.split()[2].decode()
                vag = vag.decode('utf-8', errors='replace')
                if (sha, vag) in sedda:
                    continue
                sedda.add((sha, vag))
                ut += [(c[:12], vag, '%s i sökvägen' % skal) for monster, skal in exportera.LACKA if monster.search(vag)]
                if typ == 'blob' and Path(vag).name != 'package-lock.json' and 'node_modules' not in Path(vag).parts:
                    blobbar.setdefault(sha, (c[:12], vag))
        for sha, (c, vag) in blobbar.items():
            b = subprocess.run(['git', 'cat-file', 'blob', sha], cwd=str(rot), capture_output=True, timeout=FRIST)
            if b.returncode:
                return fel('cat-file')
            text = _textblob(b.stdout)
            if text is not None:
                ut += [(c, vag, skal) for monster, skal in exportera.LACKA if monster.search(text)]
        return list(dict.fromkeys(ut))
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as e:
        return fel(type(e).__name__)


def granskning_fore_push(rot, commit):
    """Läckorna i det som en push av commit skickar: arbetskatalogen (R08) och historiken (N04). [(plats, skäl) eller
    (commit, plats, skäl)]; tomt när inget fälls."""
    return [x for x in lackor_i(rot)] + historikens_lackor(rot, commit)


def besked(lackor):
    """Läckorna som text, högst fem: commit, plats och slag av läcka, aldrig det funna värdet."""
    return '; '.join(('%s (%s)' % x) if len(x) == 2 else ('%s i %s (%s)' % (x[2], x[1], x[0])) for x in lackor[:5]) + (
        ' och %d till' % (len(lackor) - 5) if len(lackor) > 5 else '')


def pusha_granskad(r, kandidat):
    """Granskar och pushar exakt kandidat till origin/main (N04): granskningen och pushen gäller samma commit, också om
    main flyttas emellan. Ger {'ok', 'commit', 'tid', 'hinder'|'fel'}."""
    lackor = granskning_fore_push(r, kandidat)
    if lackor:
        return {'ok': False, 'commit': kandidat, 'tid': nu(), 'hinder': 'läckagekontrollen fällde det som skulle pushas: %s' % besked(lackor)}
    res = git(r, 'push', 'origin', '%s:refs/heads/main' % kandidat, frist=300)
    ut = {'ok': res.returncode == 0, 'commit': kandidat, 'tid': nu(), 'granskad': kandidat}
    if res.returncode:
        ut['fel'] = (res.stderr or res.stdout)[-300:].strip()
    return ut


def _lasfil(slug):
    p = _kunder() / slug / '.kundrepo.las'
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def skapa(slug, fjarr=None):
    """Skapar eller återanvänder kundrepot; idempotent och låst per kund. fjarr: None = automatiskt (verklig verksamhet och
    gh finns), True = försök, False = bara lokalt. Ger kvittot."""
    i = identitet(slug)
    with open(_lasfil(slug), 'w') as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        kv = las_kvitto(slug) or {'schema': 1, 'projekt_id': uuid.uuid4().hex, 'skapad': nu(), 'skapad_med': motorversion()}
        kv.update({'slug': slug, 'namn': i['namn'], 'org': ORG, 'lokal': i['lokal']})
        r = repo(slug)
        atelje.saker_vag(r, _kunder())
        # R08: de genererade filerna prövas med exportens läckagekontroll innan något skrivs in eller committas; ett avvisat
        # projekt får ingen commit, inget fjärrepo och ingen push
        import korregister
        md = claude_md(slug)
        with korregister.egen_tmp_med('nwp-kundrepo-', 'projektstartens filer före läckagekontrollen') as tmp_:
            filer_ = Path(tmp_) / 'projekt'  # en egen katalog: tempkatalogens registreringsfil hör inte till projektet
            filer_.mkdir()
            (filer_ / 'CLAUDE.md').write_text(md, encoding='utf-8')
            shutil.copyfile(_root() / 'mall' / 'leverans' / 'gitignore', filer_ / '.gitignore')
            lackor = lackor_i(filer_) + (lackor_i(r) if r.is_dir() else [])
        if lackor:
            kv['projektstart'] = {'status': 'avvisad', 'tid': nu(), 'lackor': [{'fil': f, 'skal': s} for f, s in lackor]}
            atelje.skriv_json_atomiskt(kvittofil(slug), kv)
            raise Hinder('projektstarten avvisades av läckagekontrollen: %s' % '; '.join('%s (%s)' % x for x in lackor[:5]))
        kv['projektstart'] = {'status': 'godkand', 'tid': nu()}
        ny = not ar_repo(r)
        if ny:
            r.mkdir(parents=True, exist_ok=True)
            git_ok(r, 'init', '-q', '-b', 'main')
        if not (r / 'CLAUDE.md').is_file() or (r / 'CLAUDE.md').read_text(encoding='utf-8') != md:
            (r / 'CLAUDE.md').write_text(md, encoding='utf-8')
        if not (r / '.gitignore').is_file():
            shutil.copyfile(_root() / 'mall' / 'leverans' / 'gitignore', r / '.gitignore')
        git_ok(r, 'add', '--', 'CLAUDE.md', '.gitignore')  # bara projektstartens egna filer (N04): inget annat i katalogen committas här
        if git(r, 'diff', '--cached', '--quiet').returncode:
            git_ok(r, 'commit', '-q', '-m', ('Projektstart: %s' if ny else 'Projektkontext uppdaterad: %s') % i['namn'])
        kv['commit'] = huvud(r)
        kv['uppdaterad'] = nu()
        vill = (fjarr is True) or (fjarr is None and not fiktiv(slug))
        f = kv.get('fjarr') or {}
        if f.get('status') != 'skapat':
            if fiktiv(slug) and fjarr is not True:
                kv['fjarr'] = {'status': 'saknas', 'tid': nu(), 'adress': None, 'fel': 'fiktiv verksamhet: inget fjärrepo skapas i organisationen'}
            elif vill:
                kv['fjarr'] = fjarr_skapa(slug, kv)
                if kv['fjarr'].get('forsta_push'):
                    kv['senaste_push'] = kv['fjarr']['forsta_push']
            else:
                kv['fjarr'] = {'status': 'saknas', 'tid': nu(), 'adress': None, 'fel': 'fjärrepo inte begärt'}
        atelje.skriv_json_atomiskt(kvittofil(slug), kv)
        return kv


def synka_export(slug, stage, export_id, text='', rot=None):
    """Exportens filer in i det beständiga repot som en commit: allt utom .git byts mot stagens innehåll (CLAUDE.md ligger
    redan i stagen). Ger {'commit', 'oforandrad'}; inget katalogbyte, historiken ligger i git. rot: repot, när det inte
    ligger under ateljéns kunder/ (exporten ger sitt mål)."""
    r = Path(rot) if rot else repo(slug)
    if not ar_repo(r):
        raise RuntimeError('kundrepot är inget git-repo: %s' % r)
    stage = Path(stage)
    for p in list(r.iterdir()):
        if p.name in ('.git', '.vercel', '.wrangler', 'node_modules'):
            continue
        (shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink())
    for p in stage.iterdir():
        if p.name in ('.git', 'node_modules'):
            continue
        (shutil.copytree(p, r / p.name, symlinks=False) if p.is_dir() else shutil.copyfile(p, r / p.name))
    git_ok(r, 'add', '-A')
    if git(r, 'diff', '--cached', '--quiet').returncode == 0:
        return {'commit': huvud(r), 'oforandrad': True}
    git_ok(r, 'commit', '-q', '-m', 'Export %s%s\n\nLeverans från Nortropic (motorn version %s).' % (export_id, (': ' + text) if text else '', motorversion()))
    sha = huvud(r)
    kv = las_kvitto(slug, r.parent)
    if kv:
        kv.update(commit=sha, senaste_export={'id': export_id, 'commit': sha, 'tid': nu()}, uppdaterad=nu())
        atelje.skriv_json_atomiskt(kvittofil(slug, r.parent), kv)
    return {'commit': sha, 'oforandrad': False}


def push(slug, rot=None):
    """main till det bundna fjärrepot. Ger {'ok', 'commit', 'hinder'|'fel'} och skriver senaste_push i kvittot."""
    r = Path(rot) if rot else repo(slug)
    kv = las_kvitto(slug, r.parent)
    if not kv or not ar_repo(r):
        return {'ok': False, 'hinder': 'kundrepot finns inte'}
    if (kv.get('fjarr') or {}).get('status') != 'skapat':
        return {'ok': False, 'hinder': 'inget bundet fjärrepo (%s)' % ((kv.get('fjarr') or {}).get('fel') or (kv.get('fjarr') or {}).get('status'))}
    ut = pusha_granskad(r, huvud(r))  # R08 och N04: arbetskatalogen och historiken, bundna till den commit som pushas
    kv['senaste_push'] = ut
    atelje.skriv_json_atomiskt(kvittofil(slug, r.parent), kv)
    return ut


def cloudflare_konto():
    """Det anslutna Cloudflare-kontot ur cloudflare.env (0600): ({'token', 'konto', 'underdoman'}, None) eller
    (None, hindret med den exakta handlingen). Tokenen läses bara här och går bara till Wrangler-processen."""
    fil = Path(os.environ.get('NWP_CLOUDFLARE_FIL') or CLOUDFLARE_FIL)
    handling = ('anslut Nortropics Cloudflare-konto: lägg %s (0600) med CLOUDFLARE_API_TOKEN (avgränsad: Workers-skript, D1 och '
                'R2 för kontot), CLOUDFLARE_ACCOUNT_ID och CLOUDFLARE_WORKERS_UNDERDOMAN (kontots workers.dev-underdomän)' % fil)
    if not fil.is_file() or fil.is_symlink():
        return None, 'Cloudflare-kontot är inte anslutet: ' + handling
    if fil.stat().st_mode & 0o077:
        return None, 'cloudflare.env är läsbar för andra än ägaren: chmod 600 %s' % fil
    v = {}
    for rad in fil.read_text(encoding='utf-8').splitlines():
        k, _, val = rad.partition('=')
        if k.strip() and not k.strip().startswith('#'):
            v[k.strip()] = val.strip().strip('"\'')
    konto = {'token': v.get('CLOUDFLARE_API_TOKEN'), 'konto': v.get('CLOUDFLARE_ACCOUNT_ID'), 'underdoman': v.get('CLOUDFLARE_WORKERS_UNDERDOMAN')}
    saknas = [k for k, n in (('token', 'CLOUDFLARE_API_TOKEN'), ('konto', 'CLOUDFLARE_ACCOUNT_ID'), ('underdoman', 'CLOUDFLARE_WORKERS_UNDERDOMAN')) if not konto[k]]
    if saknas:
        return None, 'cloudflare.env saknar %s: %s' % (', '.join(saknas), handling)
    if not re.fullmatch(r'[a-f0-9]{32}', konto['konto']) or not re.fullmatch(r'[a-z0-9-]{1,63}', konto['underdoman']):
        return None, 'cloudflare.env har ett konto-id eller en underdomän i fel form'
    return konto, None


def cloudflare_miljo(konto, tmp):
    """Wranglers miljö: bara det anslutna kontots token och id, ingen ägarinloggning (konfigurationen i tmp), inga
    NWP_-, Claude- eller andra nycklar, inga mätdata."""
    m = {k: os.environ[k] for k in ('PATH', 'HOME', 'USER', 'LANG') if k in os.environ}
    m.update(CLOUDFLARE_API_TOKEN=konto['token'], CLOUDFLARE_ACCOUNT_ID=konto['konto'], WRANGLER_SEND_METRICS='false',
             XDG_CONFIG_HOME=str(Path(tmp) / 'xdg'), WRANGLER_LOG_PATH=str(Path(tmp) / 'wrangler-logg'), CI='1', NO_COLOR='1')
    return m


def forhandsadress(slug, konto):
    return 'https://%s.%s.workers.dev' % (identitet(slug)['worker_forhandsvisning'], konto['underdoman'])


def access_skyddar(url, frist=15):
    """(skyddad, observation): en anonym begäran utan omdirigering ska mötas av Cloudflare Access (302 till
    *.cloudflareaccess.com eller 401/403 från Access). Ett 200 betyder att adressen är öppen."""
    import urllib.error
    import urllib.request

    class Ingen(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    oppna = urllib.request.build_opener(urllib.request.ProxyHandler({}), Ingen)
    try:
        r = oppna.open(urllib.request.Request(url + '/', method='GET'), timeout=frist)
        return False, 'HTTP %d utan inloggning' % r.status
    except urllib.error.HTTPError as e:
        plats = e.headers.get('Location') or ''
        if e.code in (301, 302, 303, 307) and re.match(r'https://[a-z0-9-]+\.cloudflareaccess\.com/', plats):
            return True, 'HTTP %d till Cloudflare Access' % e.code
        if e.code in (401, 403) and (e.headers.get('cf-access-domain') or 'cloudflareaccess' in (e.read(4096) or b'').decode('utf-8', 'replace')):
            return True, 'HTTP %d från Cloudflare Access' % e.code
        return False, 'HTTP %d utan Access' % e.code
    except (OSError, ValueError) as e:
        return False, 'adressen kunde inte prövas: %s' % str(e)[:120]


def leveransdir(slug):
    return _kunder() / slug / 'leverans'


def preview_krav(slug):
    """Vad en förhandsvisning kräver: ett kundrepo med exportens commit som HEAD och ett rent träd; ger hindret eller None."""
    import exportera
    kv = las_kvitto(slug)
    r = repo(slug)
    if not kv or not ar_repo(r):
        return 'kundrepot finns inte'
    e = exportera.aktuell(slug)
    if not e or not e.get('ok'):
        return 'ingen lyckad export finns'
    if not e.get('aktuell'):
        return 'exporten är inaktuell (källorna eller filerna har ändrats): exportera igen'
    if not e.get('commit') or e.get('commit') != huvud(r):
        return 'exportens commit är inte kundrepots HEAD: exportera igen'
    if git(r, 'status', '--porcelain').stdout.strip():
        return 'kundrepots träd har ändringar utanför exporten'
    return None


def preview(slug, deploy=None, skydd=None):
    """Förhandsvisning av exportens commit på Cloudflare Workers (ingen produktion), med beständigt kvitto. Ger kvittot.
    Alla ingångar (Flöde, prototyp.py --preview, kundrepo.py --preview) går hit, under kundens lås (flodesstart.las, samma
    som exporten), och det som byggs och laddas upp är ett fryst underlag: commitens filer ur git, prövade mot exportens
    manifest, så att kvittot gäller exakt de bytes som laddades upp också om kundrepot ändras under tiden (R07 i
    GR-20261008-06af6ff-omgranskning-codex). deploy och skydd byts bara ut i proven."""
    import flodesstart
    with flodesstart.las(_root(), slug, arv=True):
        return _preview(slug, deploy or wrangler_deploy, skydd or access_skyddar)


def wrangler_deploy(underlag, konto, post, tmp):
    """npm ci, astro build innanför processgränsen och wrangler deploy --env forhandsvisning i det frysta underlaget.
    Ger (slutkod, utdata)."""
    import exportera
    import processgrans
    r = kommando(['npm', 'ci', '--no-audit', '--no-fund', '--ignore-scripts'], underlag, frist=900,
                 env={k: v for k, v in os.environ.items() if not k.startswith(('NWP_', 'CLAUDE', 'CLOUDFLARE', 'ANTHROPIC'))})
    if r.returncode:
        return r.returncode, 'npm ci föll: %s' % (r.stdout + r.stderr)[-400:]
    rc, ut = processgrans.kor_i_katalog(underlag, [underlag / 'node_modules' / '.bin' / 'astro', 'build'])
    if rc:
        return rc, 'astro build föll: %s' % ut[-400:]
    brister = exportera.publika_brister(underlag / 'dist')
    if brister:
        return 1, 'filer som inte får bli publika ligger i dist/: %s' % ', '.join(brister[:5])
    # Kontots identitet hos leverantören, inte bara etiketten i filen: tokenen ska nå just det angivna kontot.
    vem = kommando([str(underlag / 'node_modules' / '.bin' / 'wrangler'), 'whoami'], underlag, frist=120, env=cloudflare_miljo(konto, tmp))
    if vem.returncode or konto['konto'] not in (vem.stdout or '') + (vem.stderr or ''):
        return 1, 'tokenen når inte kontot %s… (wrangler whoami): ingen uppladdning' % konto['konto'][:6]
    res = kommando([str(underlag / 'node_modules' / '.bin' / 'wrangler'), 'deploy', '--env', 'forhandsvisning',
                    '--message', 'nortropic_commit=%s nortropic_export=%s' % (post['commit'], post['export'])],
                   underlag, frist=900, env=cloudflare_miljo(konto, tmp))
    return res.returncode, (res.stdout or '') + '\n' + (res.stderr or '')


def fryst_underlag(r, commit, tmp):
    """Commitens filer ur git (git archive) i tmp/repo; ger katalogen."""
    ut = Path(tmp) / 'repo'  # en egen katalog: tempkatalogens registreringsfil hör inte till underlaget
    ut.mkdir(parents=True)
    arkiv = Path(tmp) / 'commit.tar'
    with open(arkiv, 'wb') as fh:
        res = subprocess.run(['git', 'archive', '--format=tar', commit], cwd=str(r), stdout=fh, stderr=subprocess.PIPE, timeout=FRIST)
    if res.returncode:
        raise RuntimeError('git archive föll: %s' % res.stderr.decode('utf-8', 'replace')[-300:])
    import tarfile
    with tarfile.open(arkiv) as t:
        t.extractall(ut, filter='data')
    arkiv.unlink()
    return ut


def _preview(slug, deploy, skydd):
    import exportera
    import korregister
    i = identitet(slug)
    r = repo(slug)
    tid = nu()
    post = {'schema': 2, 'id': 'PREVIEW-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()), 'typ': 'förhandsvisningskvitto',
            'plattform': 'cloudflare-workers', 'slug': slug, 'tid': tid, 'worker': i['worker_forhandsvisning'], 'miljo': 'forhandsvisning',
            'produktion': False, 'status': 'fel', 'url': None, 'hinder': [], 'commit': None, 'export': None, 'version_id': None,
            'skydd': None, 'konto': None}
    hinder = preview_krav(slug)
    tmp = None
    if hinder:
        post['hinder'].append(hinder)
    else:
        e = exportera.aktuell(slug)
        post.update(commit=huvud(r), export=e.get('id'), export_sha256=e.get('export_sha256'))
        tmp = korregister.egen_tmp('nwp-preview-', 'förhandsvisningens frysta underlag')
        try:
            underlag = fryst_underlag(r, post['commit'], tmp)
            post['underlag_sha256'] = exportera.manifest_sha(exportera.exportmanifest(underlag))
            if post['underlag_sha256'] != post['export_sha256']:
                post['hinder'].append('commitens filer stämmer inte med exportens manifest: exportera igen')
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e_:
            post['hinder'].append('det frysta underlaget kunde inte skapas: %s' % str(e_)[:200])
    konto = None
    if tmp and not post['hinder']:
        konto, hinder = cloudflare_konto()
        if hinder:
            post['hinder'].append(hinder)
            post['status'] = 'vantar_pa_konto'
        else:
            post['konto'] = konto['konto']
            post['url'] = forhandsadress(slug, konto)
            if not fiktiv(slug):  # verkligt material laddas aldrig upp till en oskyddad adress
                ok, obs = skydd(post['url'])
                post['skydd_fore'] = obs
                if not ok:
                    post['hinder'].append('Cloudflare Access skyddar inte %s (%s): skapa Access-applikationen för adressen före '
                                          'uppladdningen' % (post['url'], obs))
                    post['status'] = 'vantar_pa_skydd'
    if konto and not post['hinder']:
        oklar = osakert_forsok(slug)
        if oklar:
            post['hinder'].append('ett tidigare försök (%s) har okänt utfall: stäm av med kundrepo.py %s --stam-av innan ett nytt '
                                  'försök' % (oklar['id'], slug))
            post['status'] = 'vantar_pa_avstamning'
    if konto and not post['hinder']:
        try:
            rc, ut = deploy(underlag, konto, post, tmp)
        except (OSError, subprocess.SubprocessError) as e_:  # verktyget kunde inte köras: ingenting laddades upp
            rc, ut = None, 'uppladdningen kunde inte köras: %s' % type(e_).__name__
        if exportera.manifest_sha(exportera.exportmanifest(underlag)) != post['underlag_sha256']:
            post['hinder'].append('det frysta underlaget ändrades under bygget eller uppladdningen')
        m = re.search(r'Current Version ID:\s*([0-9a-f-]{36})', ut)
        post['version_id'] = m.group(1) if m else None
        if rc == 124 or (rc and not post['version_id'] and NATFEL.search(ut or '')):
            # Svaret förlorades efter att uppladdningen kan ha börjat: utfallet är okänt, inte ett fel att försöka om.
            post['status'] = 'osaker'
            post['hinder'].append('utfallet är okänt (%s): stäm av med kundrepo.py %s --stam-av innan ett nytt försök'
                                  % ((ut or '')[-160:].strip(), slug))
        elif rc or not post['version_id']:
            post['hinder'].append('wrangler deploy: %s' % ((ut or '')[-300:].strip() or 'inget versions-id i svaret'))
        else:
            ok, obs = skydd(post['url'])
            post['skydd'] = obs if ok else 'öppen: ' + obs
            if not ok and not fiktiv(slug):
                post['hinder'].append('förhandsvisningen svarar utan Cloudflare Access (%s): ta ner den eller skydda den' % obs)
            post['status'] = 'klar' if not post['hinder'] else 'fel'
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    post['text'] = ('förhandsvisning klar: %s (version %s, commit %s, export %s); ingen produktion' % (post['url'], post['version_id'],
                    (post['commit'] or '')[:12], post['export']) if post['status'] == 'klar' else 'ingen förhandsvisning: ' + '; '.join(post['hinder']))
    d = leveransdir(slug)
    d.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(d / (post['id'] + '.json'), post)
    return post


NATFEL = re.compile(r'ETIMEDOUT|ECONNRESET|ECONNREFUSED|socket hang up|fetch failed|network|tidsgränsen', re.I)


def _kvitton(slug):
    d = leveransdir(slug)
    if not d.is_dir() or d.is_symlink():
        return []
    ut = []
    # skrivordningen, inte namnet: två kvitton inom samma sekund har slumpade suffix
    for f in sorted(d.glob('PREVIEW-*.json'), key=lambda f: (f.stat().st_mtime_ns, f.name)):
        try:
            ut.append(json.loads(f.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            continue
    return ut


def osakert_forsok(slug):
    """Det senaste kvittot om dess utfall är okänt och inte avstämt, annars None."""
    oklar = None
    for k in _kvitton(slug):
        if k.get('status') == 'osaker':
            oklar = k
        elif oklar and k.get('avstammer') == oklar.get('id') and k.get('status') in ('klar', 'avstamd_ingen', 'fel'):
            oklar = None  # avstämt: utfallet är känt
    return oklar


def wrangler_deployments(underlag, konto, tmp):
    """Förhandsvisningens deployments ur Cloudflare (läsande): wrangler deployments list --json."""
    r = kommando(['npm', 'ci', '--no-audit', '--no-fund', '--ignore-scripts'], underlag, frist=900,
                 env={k: v for k, v in os.environ.items() if not k.startswith(('NWP_', 'CLAUDE', 'CLOUDFLARE', 'ANTHROPIC'))})
    if r.returncode:
        raise RuntimeError('npm ci föll')
    res = kommando([str(underlag / 'node_modules' / '.bin' / 'wrangler'), 'deployments', 'list', '--env', 'forhandsvisning', '--json'],
                   underlag, frist=120, env=cloudflare_miljo(konto, tmp))
    if res.returncode:
        raise RuntimeError('wrangler deployments list: %s' % (res.stderr or res.stdout)[-200:])
    return json.loads(res.stdout or '[]')


def avstam(slug, lista=None, skydd=None):
    """Stämmer av ett försök med okänt utfall mot Cloudflares lista över deployments (läsande). Hittas en deployment
    med försökets commit och export blir den kvittot; annars är det säkert att försöka igen. Ger det nya kvittot."""
    import exportera
    import flodesstart
    import korregister
    with flodesstart.las(_root(), slug, arv=True):
        fore = osakert_forsok(slug)
        tid = nu()
        post = {'schema': 2, 'id': 'PREVIEW-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()), 'typ': 'avstämning',
                'plattform': 'cloudflare-workers', 'slug': slug, 'tid': tid, 'produktion': False, 'status': 'fel', 'hinder': [],
                'url': None, 'commit': None, 'export': None, 'version_id': None, 'skydd': None, 'konto': None,
                'avstammer': fore['id'] if fore else None}
        if not fore:
            return {'status': 'inget_att_stamma_av', 'text': 'det senaste försöket har inget okänt utfall'}
        post.update({k: fore.get(k) for k in ('url', 'commit', 'export', 'worker', 'miljo', 'konto', 'export_sha256', 'underlag_sha256')})
        konto, hinder = cloudflare_konto()
        tmp = None
        try:
            if hinder:
                post['hinder'].append(hinder)
                post['status'] = 'vantar_pa_konto'
            else:
                tmp = korregister.egen_tmp('nwp-preview-', 'förhandsvisningens avstämning')
                if lista is None:
                    underlag = fryst_underlag(repo(slug), fore['commit'], tmp)
                    deps = wrangler_deployments(underlag, konto, tmp)
                else:
                    deps = lista(konto, tmp)
                markor = 'nortropic_commit=%s nortropic_export=%s' % (fore['commit'], fore['export'])
                hittad = next((x for x in deps if markor in json.dumps(x, ensure_ascii=False)), None)
                if hittad is None:
                    post['status'] = 'avstamd_ingen'
                    post['text_avstamning'] = 'ingen deployment med försökets commit och export: ett nytt försök är säkert'
                else:
                    versioner = hittad.get('versions') or []
                    post['version_id'] = (versioner[0].get('version_id') if versioner and isinstance(versioner[0], dict) else None) or hittad.get('id')
                    ok, obs = (skydd or access_skyddar)(post['url'])
                    post['skydd'] = obs if ok else 'öppen: ' + obs
                    if not ok and not fiktiv(slug):
                        post['hinder'].append('förhandsvisningen svarar utan Cloudflare Access (%s): ta ner den eller skydda den' % obs)
                    post['status'] = 'klar' if not post['hinder'] else 'fel'
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as e_:
            post['hinder'].append('avstämningen kunde inte göras: %s' % str(e_)[:200])
            post['status'] = 'osaker'  # fortfarande okänt; nästa avstämning försöker igen
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
        post['text'] = {'klar': 'avstämd: deploymenten finns (version %s)' % post['version_id'],
                        'avstamd_ingen': 'avstämd: ingen deployment, ett nytt försök är säkert'}.get(post['status'], 'ingen avstämning: ' + '; '.join(post['hinder']))
        d = leveransdir(slug)
        d.mkdir(parents=True, exist_ok=True)
        atelje.skriv_json_atomiskt(d / (post['id'] + '.json'), post)
        return post


def preview_aktuell(slug):
    """Senaste förhandsvisningskvittot med 'aktuell': commit är kundrepots HEAD och exporten är aktuell."""
    import exportera
    d = leveransdir(slug)
    if not d.is_dir() or d.is_symlink():
        return None
    poster = sorted(d.glob('PREVIEW-*.json'), key=lambda f: (f.stat().st_mtime_ns, f.name))
    if not poster:
        return None
    try:
        post = json.loads(poster[-1].read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'status': 'fel', 'aktuell': False, 'hinder': ['kvittot kunde inte läsas'], 'fil': str(poster[-1])}
    e = exportera.aktuell(slug)
    post['fil'] = str(poster[-1])
    post['aktuell'] = bool(post.get('status') == 'klar' and ar_repo(repo(slug)) and post.get('commit') == huvud(repo(slug))
                           and e and e.get('aktuell') and e.get('id') == post.get('export'))
    return post


def preview_mojlig(slug):
    return preview_krav(slug) is None


def main(argv=None):
    p = argparse.ArgumentParser(prog='kundrepo', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    g = p.add_mutually_exclusive_group()
    g.add_argument('--push', action='store_true')
    g.add_argument('--preview', action='store_true')
    g.add_argument('--visa', action='store_true')
    g.add_argument('--stam-av', action='store_true', help='stäm av ett försök med okänt utfall mot Cloudflare (läsande)')
    p.add_argument('--utan-fjarr', action='store_true')
    a = p.parse_args(argv)
    if not SLUG.match(a.slug):
        print('ogiltig slug', file=sys.stderr)
        return 2
    if a.visa:
        print(json.dumps({'kvitto': las_kvitto(a.slug), 'preview': preview_aktuell(a.slug)}, ensure_ascii=False, indent=1))
        return 0
    if a.push:
        ut = push(a.slug)
    elif a.stam_av:
        try:
            ut = avstam(a.slug)
            ut = dict(ut, ok=ut.get('status') in ('klar', 'avstamd_ingen', 'inget_att_stamma_av'))
        except ValueError as e:
            ut = {'ok': False, 'hinder': str(e)}
    elif a.preview:
        try:
            ut = preview(a.slug)
            ut = dict(ut, ok=ut.get('status') == 'klar')
        except ValueError as e:  # kundens lås är upptaget: en export eller ett annat arbete pågår (R07)
            ut = {'ok': False, 'hinder': str(e)}
    else:
        try:
            kv = skapa(a.slug, fjarr=False if a.utan_fjarr else None)
            ut = dict(kv, ok=True)
        except Hinder as e:
            ut = {'ok': False, 'hinder': str(e)}
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0 if ut.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main())
