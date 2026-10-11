#!/usr/bin/env python3
"""Repoväljarens provprojekt (kunskap/andringar.md, Repoväljaren): fyra syntetiska kunder i en isolerad rot och
organisationens GitHub som lokala nakna repon, nådda genom gits url.<…>.insteadOf, med provets gh
(kontroller/rokprov/repovaljaren/fejkgh.py) först i PATH. Riktiga GitHub nås aldrig.

- alfa: kopplad (kvittot binder kund-alfa), med arbetskopia, i takt med fjärren;
- beta: kopplad, utan arbetskopia (väljaren klonar efter bekräftelse);
- gamma: en befintlig kund utan kvitto; kund-gamma bär ett okänt projekt-id (kräver ett aktivt val, namnförslaget gamma);
- delta: en fiktiv verksamhet (får aldrig ett fjärrepo);
- i listan också kund-utan-markor (binds aldrig), motorns eget repo, ett arkiverat kundrepo och ett i en främmande
  organisation, som inte ska synas.

    .venv/bin/python -B kontroller/rokprov/revision/repovaljare_fixtur.py <rot>

I appens prov (desktop/prov/prov_repovaljaren_app.py) är roten en provinstans ur en worktree (aldrig huvudutcheckningen):
då får kunderna ett prefix (rvprov-alfa …), och provets gh, de nakna repona och konfigurationen ligger i en egen
hjälpkatalog utanför roten.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEJKGH = ROOT / 'kontroller' / 'rokprov' / 'repovaljaren' / 'fejkgh.py'
GIT = ['git', '-c', 'user.name=Nortropic', '-c', 'user.email=noreply@nortropic.se', '-c', 'core.hooksPath=/dev/null']
PID = {'alfa': 'a' * 32, 'beta': 'b' * 32, 'gamma': 'c' * 32}
KUNDER = (('alfa', 'Snickeriet Alfa (testdata)', False), ('beta', 'Bageriet Beta (testdata)', False),
          ('gamma', 'Gamma Måleri (testdata)', False), ('delta', 'Delta Provfirma (testdata)', True))
SIDA = '<html><body><main><h1>%s</h1><p>Öppettider vardagar 07–17.</p></main></body></html>\n'


def git(cwd, *args, env=None):
    return subprocess.run([*GIT, *args], cwd=str(cwd), capture_output=True, text=True, check=True, env=env).stdout.strip()


def miljo(hjalp):
    """Provets miljö: gh i PATH, konfigurationen och https://github.com/Nortropic/ som hjälpkatalogens nakna repon."""
    hjalp = Path(hjalp)
    return {'PATH': '%s%s%s' % (hjalp / 'bin', os.pathsep, os.environ.get('PATH', '')), 'NWP_FEJKGH': str(hjalp / 'fejkgh.json'),
            'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'url.file://%s/.insteadOf' % (hjalp / 'github' / 'Nortropic'),
            'GIT_CONFIG_VALUE_0': 'https://github.com/Nortropic/', 'GIT_TERMINAL_PROMPT': '0'}


def repo_post(namn, beskrivning='', agare='Nortropic', arkiverat=False, tid='2026-10-0%dT08:00:00Z'):
    return {'name': namn, 'nameWithOwner': '%s/%s' % (agare, namn), 'description': beskrivning, 'pushedAt': tid % (1 + len(namn) % 9),
            'defaultBranchRef': {'name': 'main'}, 'isPrivate': True, 'isArchived': arkiverat, 'url': 'https://github.com/%s/%s' % (agare, namn)}


def naket(hjalp, namn, rubrik, env):
    """Ett naket repo i organisationens GitHub med en första commit på main."""
    bar = hjalp / 'github' / 'Nortropic' / namn
    bar.mkdir(parents=True)
    git(bar, 'init', '-q', '--bare', '-b', 'main')
    arb = hjalp / 'tmp-frö' / namn
    arb.mkdir(parents=True)
    git(arb, 'init', '-q', '-b', 'main')
    (arb / 'src' / 'pages').mkdir(parents=True)
    (arb / 'src' / 'pages' / 'index.astro').write_text(SIDA % rubrik, encoding='utf-8')
    (arb / 'CLAUDE.md').write_text('# %s\n\nKundrepot (provprojektet).\n' % namn, encoding='utf-8')
    git(arb, 'add', '-A')
    git(arb, 'commit', '-q', '-m', 'Projektstart: %s' % namn)
    git(arb, 'push', '-q', 'https://github.com/Nortropic/%s' % namn, 'main', env=env)
    return bar


def ny_commit_pa_fjarren(hjalp, namn, text, env=None):
    """En commit som någon annan pushat till fjärren (en annan dator): repoväljaren ska se den först efter hämta."""
    env = env or dict(os.environ, **miljo(hjalp))
    arb = Path(hjalp) / 'tmp-andra' / namn
    if not arb.is_dir():
        arb.parent.mkdir(parents=True, exist_ok=True)
        git(arb.parent, 'clone', '-q', 'https://github.com/Nortropic/%s' % namn, str(arb), env=env)
    git(arb, 'pull', '-q', '--ff-only', env=env)
    f = arb / 'src' / 'pages' / 'index.astro'
    f.write_text(f.read_text(encoding='utf-8') + '<!-- %s -->\n' % text, encoding='utf-8')
    git(arb, 'commit', '-q', '-am', text)
    git(arb, 'push', '-q', 'origin', 'main', env=env)
    return git(arb, 'rev-parse', 'HEAD')


def bygg(rot, hjalp=None, prefix=''):
    """Skapar provprojektet: kunderna under rot, provets gh och fjärrarna i hjälpkatalogen (rot när den inte anges).
    Ger miljön som provet sätter i os.environ (gh, konfigurationen och fjärrarna)."""
    rot, hjalp = Path(rot), Path(hjalp or rot)
    if rot.resolve() == ROOT.resolve() and not ((rot / '.git').is_file() and prefix):
        raise SystemExit('provprojektet skapas aldrig i repots rot, utom i en worktrees provinstans med prefix')
    if (rot / '.git').is_dir():
        raise SystemExit('provprojektet skapas aldrig i huvudutcheckningen')
    m = miljo(hjalp)
    env = dict(os.environ, **m)
    (hjalp / 'bin').mkdir(parents=True, exist_ok=True)
    gh = hjalp / 'bin' / 'gh'
    gh.write_text('#!/bin/sh\nexec "%s" -I -B "%s" "$@"\n' % (sys.executable, FEJKGH), encoding='utf-8')
    os.chmod(gh, 0o755)
    namnet = dict((s, n) for s, n, _ in KUNDER)
    for bas, namn, fiktiv in KUNDER:
        u = rot / 'underlag' / (prefix + bas)
        u.mkdir(parents=True, exist_ok=True)
        (u / 'VERKSAMHET.json').write_text(json.dumps({'namn': namn, 'fiktiv': fiktiv, 'ort': 'Provby'}, ensure_ascii=False), encoding='utf-8')
    for bas in ('alfa', 'beta', 'gamma'):
        naket(hjalp, 'kund-%s%s' % (prefix, bas), namnet[bas], env)
    naket(hjalp, 'kund-%sutan-markor' % prefix, 'Utan markör', env)
    for bas in ('alfa', 'beta'):  # kvittona: projekt-id och det bundna fjärrepot, som kundrepo.skapa och fjarr_skapa skriver dem
        slug = prefix + bas
        k = rot / 'kunder' / slug
        k.mkdir(parents=True, exist_ok=True)
        (k / 'KUNDREPO.json').write_text(json.dumps({
            'schema': 1, 'projekt_id': PID[bas], 'slug': slug, 'namn': 'kund-%s' % slug, 'org': 'Nortropic', 'lokal': 'kunder/%s/kundrepo' % slug,
            'fjarr': {'status': 'skapat', 'tid': '2026-10-01T10:00:00Z', 'fel': None, 'adress': 'https://github.com/Nortropic/kund-%s' % slug, 'privat': True}},
            ensure_ascii=False), encoding='utf-8')
    git(rot / 'kunder' / (prefix + 'alfa'), 'clone', '-q', 'https://github.com/Nortropic/kund-%salfa' % prefix, 'kundrepo', env=env)
    markor = lambda bas: 'nortropic-projekt:%s Webbplats åt %s, levererad av Nortropic' % (PID[bas], prefix + bas)  # noqa: E731
    k = lambda bas: 'kund-%s%s' % (prefix, bas)  # noqa: E731
    cfg = {'lage': 'ok', 'logg': str(hjalp / 'fejkgh.logg'), 'repon': [
        repo_post(k('alfa'), markor('alfa')), repo_post(k('beta'), markor('beta')), repo_post(k('gamma'), markor('gamma')),
        repo_post(k('utan-markor'), 'ett repo utan projektets markör'), repo_post('nortropic-webb-pro', 'motorn'),
        repo_post(k('arkiv'), markor('alfa'), arkiverat=True), repo_post(k('alfa'), markor('alfa'), agare='Annan')]}
    (hjalp / 'fejkgh.json').write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    return m


def satt_lage(hjalp, lage):
    p = Path(hjalp) / 'fejkgh.json'
    cfg = json.loads(p.read_text(encoding='utf-8'))
    cfg['lage'] = lage
    p.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    a.add_argument('rot')
    print(json.dumps(bygg(a.parse_args().rot), ensure_ascii=False, indent=1))
