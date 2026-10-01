#!/usr/bin/env python3
"""Commitvakten (PreToolUse, Bash): begränsar vad en obevakad körning kan ändra i det publika repot.

Aktiv bara när NWP_COMMIT_TILLATET är satt (kirurgens intag: "kunskap/REGISTER.md,backlog/"; byggen: "backlog/").
Interaktiva sessioner påverkas inte. Läser kommandot ur hookens JSON på stdin och nekar (exit 2, skäl på stderr):
  - gh api (kan ändra och radera; använd gh repo view för metadata)
  - git add av något annat än de tillåtna sökvägarna, eller -A, --all, -u, .
  - git commit med -a/--all, eller när något utanför de tillåtna sökvägarna är köat
  - git push som inte är "git push origin main", eller när utgående commits rör annat än de tillåtna sökvägarna
  - git med -c, --git-dir, --work-tree eller -C (omvägar runt kontrollen)
Bygger på forskningens råd att begränsa vad en lyckad attack kan göra, inte bara filtrera indata.
"""
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def neka(skal):
    print('commitvakten: ' + skal, file=sys.stderr)
    sys.exit(2)


def tillaten(sokvag, prefix):
    s = sokvag.strip().lstrip('./')
    return any(s == p.rstrip('/') or (p.endswith('/') and s.startswith(p)) for p in prefix)


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, timeout=20).stdout.split()


def delkommandon(kommando):
    # Dela på ; && || | och radbrytning; varje del prövas för sig.
    return [d.strip() for d in re.split(r'&&|\|\||;|\||\n', kommando) if d.strip()]


def main():
    prefix = [p.strip() for p in os.environ.get('NWP_COMMIT_TILLATET', '').split(',') if p.strip()]
    if not prefix:
        return 0
    data = json.load(sys.stdin)
    if data.get('tool_name') != 'Bash':
        return 0
    kommando = (data.get('tool_input') or {}).get('command') or ''
    if re.search(r'\bgh\s+api\b', kommando):
        neka('gh api nekas i obevakade körningar (det kan ändra och radera); använd gh repo view för metadata')
    for del_ in delkommandon(kommando):
        try:
            ord_ = shlex.split(del_)
        except ValueError:
            ord_ = del_.split()
        while ord_ and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', ord_[0]):
            ord_ = ord_[1:]  # miljötilldelningar före kommandot
        if not ord_ or Path(ord_[0]).name != 'git':
            continue
        i = 1
        while i < len(ord_) and ord_[i].startswith('-'):  # gits globala flaggor före underkommandot
            if ord_[i] in ('-c', '-C', '--git-dir', '--work-tree') or ord_[i].startswith(('--git-dir=', '--work-tree=', '--exec-path')):
                neka('git med -c, -C, --git-dir eller --work-tree nekas här')
            i += 1
        if i >= len(ord_):
            continue
        sub, args = ord_[i], ord_[i + 1:]
        if sub == 'add':
            vagar = [a for a in args if not a.startswith('-')]
            if any(a in ('-A', '--all', '-u', '--update', '.', '*') for a in args) or not vagar:
                neka('git add måste namnge filerna; tillåtet: ' + ', '.join(prefix))
            utanfor = [v for v in vagar if not tillaten(v, prefix)]
            if utanfor:
                neka('git add utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
        elif sub == 'commit':
            if any(a == '--all' or (re.fullmatch(r'-[A-Za-z]+', a) and 'a' in a) for a in args):
                neka('git commit -a nekas; köa filerna med git add först')
            koade = git('diff', '--cached', '--name-only')
            utanfor = [f for f in koade if not tillaten(f, prefix)]
            if utanfor:
                neka('köade filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
        elif sub == 'push':
            if args != ['origin', 'main']:
                neka('bara "git push origin main" är tillåtet')
            ut = git('diff', '--name-only', 'origin/main..HEAD')
            utanfor = [f for f in ut if not tillaten(f, prefix)]
            if utanfor:
                neka('utgående commits rör filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # en vakt som dör ska neka, inte släppa igenom
        print('commitvakten föll (%s: %s) och nekar för säkerhets skull' % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)
