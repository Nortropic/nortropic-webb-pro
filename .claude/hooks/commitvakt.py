#!/usr/bin/env python3
"""Commitvakten (PreToolUse, Bash): begränsar vad en obevakad körning kan ändra i det publika repot.

Aktiv bara när NWP_COMMIT_TILLATET är satt (kirurgens intag: "kunskap/REGISTER.md,backlog/"; byggen: "backlog/").
Interaktiva sessioner påverkas inte. Läser kommandot ur hookens JSON på stdin och nekar (exit 2, skäl på stderr):
  - gh api (kan ändra och radera; använd gh repo view för metadata)
  - git add av något annat än de tillåtna sökvägarna, eller -A, --all, -u, .; sökvägar normaliseras, så att
    backlog/../CLAUDE.md inte räknas som backlog/
  - git commit med -a/--all, --amend, --include, --interactive eller --patch, med sökvägar utanför det tillåtna på
    kommandoraden (git commit -- FIL går förbi index), eller när något utanför det tillåtna är köat
  - git push som inte är "git push origin main", eller när någon utgående commit rör annat än de tillåtna
    sökvägarna (varje commit räknas, inte bara skillnaden mellan slutträden)
  - git -c (en inställning kan starta program); -C, --git-dir och --work-tree bara för läsande kommandon
  - en hemlighet (API-nyckel, privat nyckel, nyckelrad ur en .env-fil) i det som köas eller pushas
Ett git-anrop som misslyckas eller tar för lång tid nekar; vakten håller sig inom en egen tidsbudget (BUDGET) så att
den hinner svara innan värdens timeout (settings.json, 30 s), eftersom en krok som tar slut på tid släpper igenom.
Bygger på forskningens råd att begränsa vad en lyckad attack kan göra, inte bara filtrera indata.
"""
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LASANDE = {'log', 'show', 'status', 'diff', 'rev-parse', 'ls-files', 'ls-tree', 'cat-file', 'describe', 'shortlog',
           'blame', 'grep', 'rev-list', 'for-each-ref', 'count-objects'}
# commit-flaggor vars värde är nästa ord (eller sitter ihop med flaggan för de korta)
VARDE_FLAGGOR = {'-m', '--message', '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message', '-t', '--template',
                 '--author', '--date', '--cleanup', '--trailer', '--fixup', '--squash', '--gpg-sign', '-S'}
HEMLIGHET = re.compile(r'(re_[A-Za-z0-9]{24,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{30,}|'
                       r'github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|'
                       r'-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(RESEND_API_NYCKEL|SCB_API_NYCKEL|[A-Z_]*API_KEY|[A-Z_]*SECRET[A-Z_]*|'
                       r'[A-Z_]*TOKEN)=\S{8,})')
BUDGET = 20.0  # sekunder för hela vakten; settings.json ger kroken 30
GIT_FRIST = 6  # sekunder per git-anrop
SLUT = time.monotonic() + BUDGET


def neka(skal):
    print('commitvakten: ' + skal, file=sys.stderr)
    sys.exit(2)


def normaliserad(sokvag):
    """Sökvägen relativt reporoten utan ./ och ..; None när den pekar utanför repot eller är absolut."""
    s = (sokvag or '').strip()
    if not s or s.startswith('/') or s.startswith('~'):
        return None
    s = posixpath.normpath(s.replace('\\', '/'))
    if s == '.' or s == '..' or s.startswith('../'):
        return None
    return s


def tillaten(sokvag, prefix):
    s = normaliserad(sokvag)
    if s is None:
        return False
    return any(s == p.rstrip('/') or (p.endswith('/') and s.startswith(p)) for p in prefix)


def git(*args, indata=None):
    """git i reporoten; misslyckat anrop, tidsgräns eller slut på budgeten nekar (en vakt som inte vet säger nej)."""
    kvar = SLUT - time.monotonic()
    if kvar <= 0.5:
        neka('tidsbudgeten är slut; försök igen')
    p = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, input=indata,
                       timeout=min(GIT_FRIST, kvar))
    if p.returncode:
        neka('git %s misslyckades (%s); kommandot nekas' % (args[0], (p.stderr or '').strip()[-200:] or 'kod %d' % p.returncode))
    return p.stdout


def filer_z(ut):
    return [f for f in ut.split('\0') if f]


def delkommandon(kommando):
    # Dela på ; && || | och radbrytning; varje del prövas för sig.
    return [d.strip() for d in re.split(r'&&|\|\||;|\||\n', kommando) if d.strip()]


def commit_sokvagar(args):
    """Sökvägarna på en commit-kommandorad (efter -- eller lösa), med flaggornas värden borträknade."""
    vagar, i, efter = [], 0, False
    while i < len(args):
        a = args[i]
        if efter or not a.startswith('-'):
            vagar.append(a)
        elif a == '--':
            efter = True
        elif a in VARDE_FLAGGOR:
            i += 1  # värdet är nästa ord
        i += 1
    return vagar


def hemlighet_i(diff):
    for rad in diff.splitlines():
        if rad.startswith('+') and not rad.startswith('+++') and HEMLIGHET.search(rad):
            return rad[:80]
    return None


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
        i, annan_katalog = 1, False
        while i < len(ord_) and ord_[i].startswith('-'):  # gits globala flaggor före underkommandot
            f = ord_[i]
            if (f.startswith('-c') and not f.startswith('--')) or f.startswith(('--config-env', '--exec-path')):
                # -c kan köra godtyckliga program även i läskommandon (core.pager, core.fsmonitor, alias med !)
                neka('git -c nekas alltid: en inställning kan starta program (core.pager, core.fsmonitor, alias med !)')
            if f in ('-C', '--git-dir', '--work-tree'):
                annan_katalog, i = True, i + 1  # flaggans värde är nästa ord
            elif f.startswith(('--git-dir=', '--work-tree=')) or (f.startswith('-C') and len(f) > 2):
                annan_katalog = True
            i += 1
        if i >= len(ord_):
            continue
        sub, args = ord_[i], ord_[i + 1:]
        if annan_katalog:
            # Läsa i en klon (git -C /tmp/kirurg/repo log -1) är ofarligt; skriva eller starta program är det inte.
            farliga = [a for a in args if a.startswith(('--output', '--open-files-in-pager', '--ext-diff', '--textconv'))
                       or re.fullmatch(r'-O.*', a)]
            if sub in LASANDE and not farliga:
                continue
            neka('git -C/--git-dir/--work-tree tillåts bara för läsande kommandon (%s) utan --output, -O och --ext-diff'
                 % ', '.join(sorted(LASANDE)))
        if sub == 'add':
            vagar = [a for a in args if not a.startswith('-')]
            if any(a in ('-A', '--all', '-u', '--update', '.', '*') for a in args) or not vagar:
                neka('git add måste namnge filerna; tillåtet: ' + ', '.join(prefix))
            utanfor = [v for v in vagar if not tillaten(v, prefix)]
            if utanfor:
                neka('git add utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
        elif sub == 'commit':
            if any(a in ('--all', '--amend', '--include', '--interactive', '--patch') or
                   (re.fullmatch(r'-[A-Za-z]+', a) and set(a[1:]) & set('aip')) for a in args):
                neka('git commit med -a, --amend, --include, --interactive eller --patch nekas; köa filerna med git add först')
            vagar = commit_sokvagar(args)
            utanfor = [v for v in vagar if not tillaten(v, prefix)]
            if utanfor:
                neka('git commit med sökvägar utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            koade = filer_z(git('diff', '--cached', '--name-only', '-z'))
            utanfor = [f for f in koade if not tillaten(f, prefix)]
            if utanfor:
                neka('köade filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            tr = hemlighet_i(git('diff', '--cached', '-U0', '--no-color'))
            if tr:
                neka('det köade innehåller något som ser ut som en hemlighet: %s' % tr)
        elif sub == 'push':
            if args != ['origin', 'main']:
                neka('bara "git push origin main" är tillåtet')
            ut = filer_z(git('log', '--format=', '--name-only', '-z', 'origin/main..HEAD'))
            utanfor = sorted({f for f in ut if not tillaten(f, prefix)})
            if utanfor:
                neka('utgående commits rör filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            tr = hemlighet_i(git('diff', '-U0', '--no-color', 'origin/main..HEAD'))
            if tr:
                neka('de utgående commitarna innehåller något som ser ut som en hemlighet: %s' % tr)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # en vakt som dör ska neka, inte släppa igenom
        print('commitvakten föll (%s: %s) och nekar för säkerhets skull' % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)
