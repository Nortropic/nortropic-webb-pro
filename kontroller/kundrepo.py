#!/usr/bin/env python3
"""kundrepo.py — kundprojektets eget repo och leveransvägen (ägarens uppdrag 2026-10-07, punkt 3, 4 och 10; 2026-10-08, 2A–2B).

Varje kundprojekt får från projektstarten (kontroller/ny_sajt.py --installera, via ateljén) ett eget lokalt git-repo i
kunder/<slug>/kundrepo med ett kort CLAUDE.md, och en verklig verksamhet (VERKSAMHET.json utan fiktiv: true) ett privat
GitHub-repo Nortropic/kund-<slug> (ägarens svar 2026-10-07: organisationen Nortropic). Identiteten står i
kunder/<slug>/KUNDREPO.json: projekt-id, slug, namn, lokal väg, fjärrepot med status, Vercel-projektet och senaste push.
Samma repo återanvänds vid fortsättning, nya kandidater och återförsök; skapandet är idempotent och låst per kund
(.kundrepo.las), och ett GitHub-repo med samma namn som inte bär projektets markör i beskrivningen binds aldrig
(status namnkonflikt). Lokal skapning som lyckats men fjärrskapning som misslyckats står som det (status fel, med skälet).

Exporten (kontroller/exportera.py) blir en commit i det beständiga repot (synka_export) i stället för ett katalogbyte,
pushas till fjärrepot när det är bundet (push), och förhandsvisningen (preview) driftsätts med Vercels CLI i teamet
nortropic (vercel_koppla: projektet kund-<slug>; Vercels GitHub-app saknas i organisationen, ägarens nulägeskontroll
2026-10-07) med commit och export-id som metadata; kvittot kunder/<slug>/leverans/PREVIEW-<tid>.json bär commit,
export, adress och status. En förhandsvisning är aldrig produktion; produktionspublicering är ett eget ägarbeslut.

Privat underlag och hemligheter följer aldrig med: repot får bara exportens filer (exportera.lackor fäller lokala
sökvägar, privat underlag och nycklar) och CLAUDE.md nämner inget privat. gh och vercel används som de är inloggade
(ägarens konto); saknas de står det i kvittot, och inget skapas av gissning.

    .venv/bin/python kontroller/kundrepo.py <slug>              # skapa eller återanvänd (lokalt + fjärr när tillåtet)
    .venv/bin/python kontroller/kundrepo.py <slug> --utan-fjarr # bara lokalt
    .venv/bin/python kontroller/kundrepo.py <slug> --push       # pusha main till det bundna fjärrepot
    .venv/bin/python kontroller/kundrepo.py <slug> --vercel     # koppla till Vercel-projektet kund-<slug> i teamet nortropic
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
TEAM = 'nortropic'         # Vercel-teamet (Pro), inloggat med ägarens konto
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
    return {'slug': slug, 'namn': namn, 'org': ORG, 'team': TEAM, 'lokal': 'kunder/%s/kundrepo' % slug,
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
    """Besökarens viktigaste uppgift ur briefen, när raden finns; annars en hänvisning."""
    try:
        for rad in ((Path(underlag) if underlag else _underlag()) / slug / 'BRIEF.md').read_text(encoding='utf-8').splitlines():
            if re.search(r'prim[aä]r[a]? handling', rad, re.I) and ':' in rad:
                return rad.split(':', 1)[1].strip().strip('*').strip()[:200]
    except OSError:
        pass
    return 'står i Nortropics brief för projektet'


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
        'Astro med Vercels adapter, Node 24. `npm ci` installerar de låsta versionerna, `npm run build` bygger (Vercel-utdata i',
        '.vercel/output), `npm run dev` kör lokalt, `npm run preview` visar bygget.', '',
        '## Kodstruktur', '',
        '`src/pages/` sidorna och formulärets funktion `src/pages/api/forfragan.js`, `src/components/`, `src/layouts/`, `src/styles/`,',
        '`public/` statiska filer. `DESIGN.md` beskriver designen när den är exporterad; `LICENSER.md` licensunderlaget.', '',
        '## Design- och faktakälla', '',
        '- Designen: `DESIGN.md` i repot%s. Ändra inte riktningen utan Nortropics och kundens beslut.' % (' (export %s)' % export_id if export_id else ''),
        '- Fakta om verksamheten: Nortropics verifierade underlag, aldrig påhittade uppgifter, omdömen, siffror eller meriter.',
        '- Ingen tidigare kunds färgval, typsnitt, smakdomar eller riktning ärvs av det här projektet.', '',
        '## Begränsningar', '',
        '- Inga hemligheter eller miljövärden i repot: variablerna står i `.env.example` och sätts i Vercels projektinställningar.',
        '- Formuläret postar till `/api/forfragan/` (Vercel Blob) och landar på `/tack/`, `/mottagen/` eller `/fel/`.',
        '- Innehåll och navigation fungerar utan JavaScript; inline-händelser stoppas av CSP:n.', '',
        '## Prov och leverans', '',
        '- `npm run build` ska gå igenom; Nortropics export kör byggprovet och läckagekontrollen före varje commit hit.',
        '- Leveransen: export → commit i det här repot → förhandsvisning i Vercel-projektet %s (teamet %s), bunden till' % (i['namn'], i['team']),
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
    beskrivning = '%s%s Webbplats åt %s, levererad av Nortropic' % (MARKOR, kv['projekt_id'], str(verksamhet(slug).get('namn') or slug)[:60])
    r = kommando([gh, 'repo', 'create', '%s/%s' % (ORG, i['namn']), '--private', '--description', beskrivning,
                  '--source', str(repo(slug)), '--remote', 'origin', '--push'], repo(slug), frist=300)
    if r.returncode:
        return {'status': 'fel', 'tid': tid, 'adress': None, 'fel': 'gh repo create: %s' % (r.stderr or r.stdout)[-300:].strip()}
    return {'status': 'skapat', 'tid': tid, 'fel': None, 'adress': i['fjarr_adress'], 'privat': True, 'ateranvant': False}


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
        kv.update({'slug': slug, 'namn': i['namn'], 'org': ORG, 'lokal': i['lokal'], 'team': TEAM})
        r = repo(slug)
        atelje.saker_vag(r, _kunder())
        ny = not ar_repo(r)
        if ny:
            r.mkdir(parents=True, exist_ok=True)
            git_ok(r, 'init', '-q', '-b', 'main')
        md = claude_md(slug)
        if not (r / 'CLAUDE.md').is_file() or (r / 'CLAUDE.md').read_text(encoding='utf-8') != md:
            (r / 'CLAUDE.md').write_text(md, encoding='utf-8')
        if not (r / '.gitignore').is_file():
            shutil.copyfile(_root() / 'mall' / 'leverans' / 'gitignore', r / '.gitignore')
        git_ok(r, 'add', '-A')
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
        if p.name in ('.git', '.vercel', 'node_modules'):
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
    res = git(r, 'push', '-u', 'origin', 'main', frist=300)
    ut = {'ok': res.returncode == 0, 'commit': huvud(r), 'tid': nu()}
    if res.returncode:
        ut['fel'] = (res.stderr or res.stdout)[-300:].strip()
    kv['senaste_push'] = ut
    atelje.skriv_json_atomiskt(kvittofil(slug, r.parent), kv)
    return ut


def vercel_koppla(slug):
    """Kundrepot till Vercel-projektet kund-<slug> i teamet nortropic (skapas när det saknas). Skriver vercel i kvittot."""
    kv = las_kvitto(slug)
    r = repo(slug)
    if not kv or not ar_repo(r):
        return {'status': 'fel', 'fel': 'kundrepot finns inte'}
    v = shutil.which('vercel')
    i = identitet(slug)
    if not v:
        ut = {'status': 'fel', 'tid': nu(), 'fel': 'vercel saknas i PATH', 'team': TEAM, 'projekt': i['namn']}
    else:
        res = kommando([v, 'link', '--yes', '--scope', TEAM, '--project', i['namn']], r)
        if res.returncode and re.search(r'not found|does not exist|finns inte|Could not find', (res.stderr or '') + (res.stdout or ''), re.I):
            skapat = kommando([v, 'project', 'create', i['namn'], '--scope', TEAM], r)
            res = kommando([v, 'link', '--yes', '--scope', TEAM, '--project', i['namn']], r) if skapat.returncode == 0 else skapat
        if res.returncode:
            ut = {'status': 'fel', 'tid': nu(), 'fel': (res.stderr or res.stdout)[-300:].strip(), 'team': TEAM, 'projekt': i['namn']}
        else:
            try:
                pj = json.loads((r / '.vercel' / 'project.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                pj = {}
            ut = {'status': 'kopplat', 'tid': nu(), 'fel': None, 'team': TEAM, 'projekt': i['namn'], 'projekt_id': pj.get('projectId'), 'org_id': pj.get('orgId')}
    kv['vercel'] = ut
    atelje.skriv_json_atomiskt(kvittofil(slug), kv)
    return ut


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


def preview(slug):
    """Förhandsvisning av exportens commit med Vercels CLI (ingen produktion), med beständigt kvitto. Ger kvittot."""
    import exportera
    i = identitet(slug)
    r = repo(slug)
    tid = nu()
    post = {'schema': 1, 'id': 'PREVIEW-%s-%s' % (tid.replace(':', '').replace('-', ''), os.urandom(2).hex()), 'typ': 'förhandsvisningskvitto',
            'slug': slug, 'tid': tid, 'team': TEAM, 'projekt': i['namn'], 'produktion': False, 'status': 'fel', 'url': None, 'hinder': [],
            'commit': None, 'export': None}
    hinder = preview_krav(slug)
    if hinder:
        post['hinder'].append(hinder)
    else:
        e = exportera.aktuell(slug)
        post.update(commit=huvud(r), export=e.get('id'), export_sha256=e.get('export_sha256'))
        kv = las_kvitto(slug)
        if (kv.get('vercel') or {}).get('status') != 'kopplat':
            vercel_koppla(slug)
            kv = las_kvitto(slug)
        if (kv.get('vercel') or {}).get('status') != 'kopplat':
            post['hinder'].append('Vercel-projektet är inte kopplat: %s' % (kv.get('vercel') or {}).get('fel'))
        else:
            v = shutil.which('vercel')
            res = kommando([v, 'deploy', '--yes', '--scope', TEAM, '--target', 'preview', '-m', 'nortropic_commit=%s' % post['commit'],
                            '-m', 'nortropic_export=%s' % post['export']], r, frist=900)
            urlar = re.findall(r'https://[\w.-]+\.vercel\.app\S*', (res.stdout or '') + '\n' + (res.stderr or ''))
            if res.returncode or not urlar:
                post['hinder'].append('vercel deploy: %s' % ((res.stderr or res.stdout)[-300:].strip() or 'ingen adress i svaret'))
            else:
                post['url'] = urlar[-1].strip()
                insp = kommando([v, 'inspect', post['url'], '--scope', TEAM, '--wait', '--timeout', '5m'], r, frist=400)
                text = (insp.stdout or '') + '\n' + (insp.stderr or '')
                m = re.search(r'(?im)^\s*status\b[^\n]*', text)
                rad = (m.group(0) if m else '').lower()
                post['vercel_status'] = (m.group(0).strip() if m else None)
                post['status'] = 'klar' if 'ready' in rad else 'fel' if ('error' in rad or insp.returncode) else 'okänd'
                if post['status'] != 'klar':
                    post['hinder'].append('driftsättningens status: %s' % (post['vercel_status'] or 'inte observerad'))
    post['text'] = ('förhandsvisning klar: %s (commit %s, export %s); ingen produktion' % (post['url'], (post['commit'] or '')[:12], post['export'])
                    if post['status'] == 'klar' else 'ingen förhandsvisning: ' + '; '.join(post['hinder']))
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
    poster = sorted(d.glob('PREVIEW-*.json'))
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
    g.add_argument('--vercel', action='store_true')
    g.add_argument('--preview', action='store_true')
    g.add_argument('--visa', action='store_true')
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
    elif a.vercel:
        ut = vercel_koppla(a.slug)
        ut = dict(ut, ok=ut.get('status') == 'kopplat')
    elif a.preview:
        ut = preview(a.slug)
        ut = dict(ut, ok=ut.get('status') == 'klar')
    else:
        kv = skapa(a.slug, fjarr=False if a.utan_fjarr else None)
        ut = dict(kv, ok=True)
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0 if ut.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main())
