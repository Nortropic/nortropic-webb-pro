#!/usr/bin/env python3
"""Commitvakten (PreToolUse, Bash): begränsar vad en obevakad körning kan ändra i det publika repot.

Aktiv bara när NWP_COMMIT_TILLATET är satt (kirurgens intag: "kunskap/REGISTER.md,backlog/"; byggen: "backlog/").
Interaktiva sessioner påverkas inte. Läser kommandot ur hookens JSON på stdin och nekar (exit 2, skäl på stderr):
  - gh api (kan ändra och radera; använd gh repo view för metadata)
  - git add med någon flagga alls, eller av något annat än de tillåtna sökvägarna; sökvägar normaliseras, så att
    backlog/../CLAUDE.md inte räknas som backlog/
  - git commit med andra flaggor än -m/--message, -F/--file, -q/--quiet, -v/--verbose, --no-edit och --no-status (så
    att --pathspec-from-file, -a, --amend, --include, --only, --interactive med flera aldrig prövas en i taget), med
    sökvägar utanför det tillåtna på kommandoraden (git commit -- FIL går förbi index), eller när något utanför det
    tillåtna är köat
  - git push som inte är "git push origin main", eller när någon utgående commit rör annat än de tillåtna
    sökvägarna (varje commit räknas, inte bara skillnaden mellan slutträden)
  - git -c (en inställning kan starta program); -C, --git-dir och --work-tree bara för läsande kommandon
  - git bakom ett omslag (command, env, nice, exec …) prövas som git; git inuti ett inbäddat skal (sh -c, eval, xargs)
    nekas; en git-skrivning (add, commit eller push) måste vara hela kommandot, utan andra delar före eller efter
    (inget &&, ;, |, & eller radbrytning), så att varje steg prövas mot det tillstånd som gäller när det körs och inget
    cd kan smugglas in i samma anrop; git-skrivningar nekas när sessionens arbetskatalog ligger utanför repot (hookens
    cwd); andra skrivande underkommandon (merge, stash, rm, pull …) nekas
  - push prövar grenen main (refs/heads/main) mot origin/main, inte HEAD, går igenom varje utgående commit också på
    sidogrenar, och tar merge-commitens egen diff mot första föräldern
  - en hemlighet (API-nyckel, privat nyckel, nyckelrad ur en .env-fil) i det som ska committas (index och, vid
    sökvägar på kommandoraden, arbetskopian) eller i någon utgående commits tillagda rader; diffarna tas med --text
    och binära filer (ingen granskbar diff) nekas; bara fil, rad och nyckeltyp rapporteras, aldrig värdet
  - git-skrivningar bara från reporoten: relativa sökvägar tolkas annars från en annan katalog än vakten prövar
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
# commit-flaggor som tillåts; de med värde tar nästa ord (eller värdet ihopskrivet för de korta). Allt annat nekas.
COMMIT_MED_VARDE = {'-m', '--message', '-F', '--file'}
COMMIT_UTAN_VARDE = {'-q', '--quiet', '-v', '--verbose', '--no-edit', '--no-status'}
HEMLIGHETER = [('Resend-nyckel', r're_[A-Za-z0-9]{24,}'), ('Anthropic-nyckel', r'sk-ant-[A-Za-z0-9_-]{20,}'),
               ('sk-nyckel', r'\bsk-[A-Za-z0-9]{32,}'), ('GitHub-token', r'\b(ghp|gho)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}'),
               ('AWS-nyckel', r'\bAKIA[0-9A-Z]{16}'), ('Slack-token', r'\bxox[baprs]-[A-Za-z0-9-]{10,}'),
               ('privat nyckel', r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
               ('nyckelrad', r'\b(RESEND_API_NYCKEL|SCB_API_NYCKEL|[A-Z_]*API_KEY|[A-Z_]*SECRET[A-Z_]*|[A-Z_]*TOKEN)=\S{8,}')]
HEMLIGHET_RE = [(namn, re.compile(rx)) for namn, rx in HEMLIGHETER]
OMSLAG = {'command', 'builtin', 'exec', 'env', 'nice', 'nohup', 'time', 'caffeinate', 'ionice'}  # tillåtna ord före git
SKRIVANDE = {'add', 'commit', 'push'}  # de enda skrivande underkommandona som prövas; alla andra nekas
INBADDAT = re.compile(r'(^|[\s"\'`;&|(])git\s')
BUDGET = float(os.environ.get('NWP_COMMITVAKT_BUDGET') or 20.0)  # sekunder för hela vakten; settings.json ger kroken 30
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


def git(*args):
    """git i reporoten, som bytes: textläget skulle normalisera CR och göra radindelningen annan än gits (omgång sex,
    F27). Misslyckat anrop, tidsgräns eller slut på budgeten nekar (en vakt som inte vet säger nej)."""
    kvar = SLUT - time.monotonic()
    if kvar <= 0.5:
        neka('tidsbudgeten är slut; försök igen')
    p = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, timeout=min(GIT_FRIST, kvar))
    if p.returncode:
        neka('git %s misslyckades (%s); kommandot nekas' % (args[0], p.stderr.decode('utf-8', 'replace').strip()[-200:] or 'kod %d' % p.returncode))
    return p.stdout


def filer_z(ut):
    return [f.decode('utf-8', 'replace') for f in ut.split(b'\0') if f]


def rader_lf(data):
    """Rader delade bara på LF, som git själv delar dem: splitlines() delar också på VT, FF, CR och U+2028, och då
    tappar en del av en tillagd rad sitt plus (omgång sex, F27)."""
    return [r.decode('utf-8', 'replace') for r in data.split(b'\n')]


EXPANSION = re.compile(r'[*?\[\]{}~]|^:|\$')  # skalets expansioner: glob, klammer, tilde, pathspec-magi, variabler


AVGRANSARE = re.compile(r'&&|\|\||;|\||&|\n')  # samma avgränsare som Claude Codes egen behörighetskontroll, också ensamt &


def delkommandon(kommando):
    # Dela på ; && || | & och radbrytning; varje del prövas för sig (omgång fyra, F3: ensamt & räknas).
    return [d.strip() for d in AVGRANSARE.split(kommando) if d.strip()]


def sammansatt(kommando):
    """Har kommandot någon avgränsare alls, också en avslutande (git push origin main & körs i bakgrunden)?"""
    return len(AVGRANSARE.split(kommando)) > 1


def commit_sokvagar(args):
    """Sökvägarna på en commit-kommandorad (efter -- eller lösa). Varje flagga måste vara en av de tillåtna; annars nekas
    kommandot (en kort tillåten lista går att kontrollera, en växande förbudslista inte: --pathspec-from-file,
    --only, --include, -a, --amend …)."""
    vagar, i, efter = [], 0, False
    while i < len(args):
        a = args[i]
        if efter or not a.startswith('-'):
            vagar.append(a)
        elif a == '--':
            efter = True
        elif a.startswith('--'):
            namn, har_varde = a.split('=', 1)[0], '=' in a
            if namn in COMMIT_MED_VARDE:
                if not har_varde:
                    i += 1
            elif namn not in COMMIT_UTAN_VARDE:
                neka('git commit med flaggan %s nekas; tillåtet: %s' % (namn, ', '.join(sorted(COMMIT_MED_VARDE | COMMIT_UTAN_VARDE))))
        elif a in COMMIT_MED_VARDE:
            i += 1  # värdet är nästa ord
        elif a[:2] in COMMIT_MED_VARDE and len(a) > 2:
            pass  # värdet ihopskrivet: -mText
        elif a not in COMMIT_UTAN_VARDE:
            neka('git commit med flaggan %s nekas; tillåtet: %s' % (a, ', '.join(sorted(COMMIT_MED_VARDE | COMMIT_UTAN_VARDE))))
        i += 1
    return vagar


def hemlighet_i(diff):
    """(fil, rad, nyckeltyp) för den första tillagda raden som ser ut som en hemlighet, annars None. Värdet rapporteras
    aldrig: det hade annars hamnat i sessionens logg. Filhuvuden (---/+++) finns bara mellan 'diff --git' och första
    '@@'; inne i en hunk är en rad som börjar med '+++' innehåll (omgång tre, F27). Diffen är bytes, raderna LF."""
    fil, rad, i_huvud = '?', 0, True
    for r in rader_lf(diff):
        if r.startswith('diff --git '):
            i_huvud = True
        elif i_huvud and r.startswith('+++ '):
            fil = r[4:].removeprefix('b/').strip()
        elif r.startswith('@@'):
            i_huvud = False
            m = re.search(r'\+(\d+)', r)
            rad = int(m.group(1)) - 1 if m else 0
        elif not i_huvud and r.startswith('+'):
            rad += 1
            for namn, rx in HEMLIGHET_RE:
                if rx.search(r):
                    return fil, rad, namn
        elif not i_huvud and not r.startswith('-') and not r.startswith('\\'):
            rad += 1
    return None


def hemlighet_i_text(data):
    """(rad, nyckeltyp) för den första raden i en text (ett commit-meddelande) som ser ut som en hemlighet, annars None."""
    for i, r in enumerate(rader_lf(data if isinstance(data, bytes) else data.encode('utf-8', 'replace')), 1):
        for namn, rx in HEMLIGHET_RE:
            if rx.search(r):
                return i, namn
    return None


def commit_meddelanden(args):
    """Meddelandetexterna på en commit-rad: värdena till -m/--message (också --message= och -mText) och innehållet i
    filerna till -F/--file, lästa från reporoten (omgång elva, F27: diffen granskades, meddelandet inte)."""
    ut, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ('-m', '--message') and i + 1 < len(args):
            ut.append(args[i + 1].encode('utf-8', 'replace'))
            i += 2
            continue
        if a in ('-F', '--file') and i + 1 < len(args):
            try:
                ut.append((ROOT / args[i + 1]).read_bytes())
            except OSError:
                ut.append(b'')
            i += 2
            continue
        if a.startswith('--message='):
            ut.append(a[len('--message='):].encode('utf-8', 'replace'))
        elif a.startswith('--file='):
            try:
                ut.append((ROOT / a[len('--file='):]).read_bytes())
            except OSError:
                ut.append(b'')
        elif a.startswith('-m') and len(a) > 2 and not a.startswith('--'):
            ut.append(a[2:].encode('utf-8', 'replace'))
        elif a.startswith('-F') and len(a) > 2 and not a.startswith('--'):  # -Ffilnamn (omgång tolv, F27)
            try:
                ut.append((ROOT / a[2:]).read_bytes())
            except OSError:
                ut.append(b'')
        i += 1
    return ut


def hemlighet_i_fil(sokvag):
    """Som hemlighet_i men för en fil i arbetskopian (det som git add tar in). En fil med NUL-byte (binär) nekas: git
    visar ingen diff för den, så den går inte att granska (omgång fem, F27). En katalog expanderas till sina filer
    (spårade och ospårade, inte ignorerade) med git ls-files."""
    p = ROOT / sokvag
    if p.is_dir():
        for f in filer_z(git('ls-files', '-z', '--cached', '--others', '--exclude-standard', '--', sokvag)):
            tr = hemlighet_i_fil(f)
            if tr:
                return tr
        return None
    if not p.exists():
        return None  # inget innehåll att granska; git add själv faller på en sökväg som inte finns
    if p.is_symlink():
        return None  # git köar länken som text (dess mål), inte målets innehåll
    try:
        data = p.read_bytes()
    except OSError as e:  # en fil som finns men inte går att läsa är inte granskad; det nekar (omgång sex, F27)
        return sokvag, 0, 'kunde inte läsas (%s)' % type(e).__name__
    if b'\0' in data:
        return sokvag, 0, 'binär fil (NUL-byte); bara text får köas'
    for n, r in enumerate(rader_lf(data), 1):
        for namn, rx in HEMLIGHET_RE:
            if rx.search(r):
                return sokvag, n, namn
    return None


def binara_i(numstat):
    """Filer som git redovisar som binära i en --numstat-utskrift (-\t-\tfil): de har ingen granskbar diff."""
    return [rad.split('\t', 2)[2] for rad in rader_lf(numstat) if rad.startswith('-\t-\t')]


def skalord(kommando):
    """Kommandoraden delad i skalord, varje ord som fragment (text, citattyp) där citattypen är ', " eller None. Så syns
    om ett ord är helt citerat, helt ociterat eller sammansatt ('a'* eller ''{x,y}): skalet behandlar bara det citerade
    fragmentet bokstavligt, resten expanderas (omgång åtta, F3). Backslash utanför citat nekas: den behövs aldrig."""
    ord_, frag, text, citat, i = [], [], '', None, 0
    while i < len(kommando):
        c = kommando[i]
        if citat:
            if c == citat:
                frag.append((text, citat)); text, citat = '', None
            else:
                text += c
        elif c in ('"', "'"):
            if text:
                frag.append((text, None)); text = ''
            citat = c
        elif c == '\\':
            neka('backslash i ett skrivande git-kommando nekas; skriv värdena utan skaltecken')
        elif c.isspace():
            if text:
                frag.append((text, None)); text = ''
            if frag:
                ord_.append(frag); frag = []
        else:
            text += c
        i += 1
    if citat:
        neka('ett citat som inte stängs i ett skrivande git-kommando nekas')
    if text:
        frag.append((text, None))
    if frag:
        ord_.append(frag)
    return ord_


def bokstavligt(fragment):
    """Är skalordet ett enda fragment som skalet lämnar orört: helt enkelciterat, helt dubbelciterat (utan $ och backtick,
    som nekas för hela raden) eller ociterat utan expansionstecken?"""
    if len(fragment) != 1:
        return False
    text, citat = fragment[0]
    return citat is not None or not EXPANSION.search(text)


def utan_expansion(sub, args, kommando):
    """Skrivande git får inga argument som skalet expanderar och ingen kommando-, variabel- eller processubstitution:
    vakten (shlex) och skalet skulle annars pröva olika ord (omgång sex till åtta, F3 och F27). Varje skalord prövas
    som helhet med sin citering: commit-meddelandet får vara ett helt citerat ord eller ett ociterat ord utan
    expansionstecken; sammansatta ord ('a'*, ''{x,y}) och den hopskrivna formen -mVärde nekas. -F undantas inte.
    Flaggornas roll bestäms av det avciterade ordet, som git ser det: '-F' och "--file" är samma flagga som -F
    (omgång tio, F3); citeringen styr bara prövningen av värdena."""
    if '$(' in kommando or '`' in kommando or '<(' in kommando or '>(' in kommando or '$' in kommando:
        neka('git %s med $ (variabel, kommando- eller processubstitution) eller backtick nekas; skriv värdena bokstavligt' % sub)
    ord_ = skalord(kommando)
    vantar = None  # vilken flagga som konsumerar nästa ord: 'meddelande' (-m/--message) eller 'fil' (-F/--file)
    for frag in ord_:
        helt = ''.join(x for x, _ in frag)
        if vantar == 'meddelande':
            vantar = None
            if not bokstavligt(frag):
                neka('git %s: commit-meddelandet %r är inte ett helt citerat eller helt bokstavligt ord; citera hela meddelandet' % (sub, helt))
            continue
        if vantar == 'fil':  # värdet till -F är ett filnamn, också när det råkar heta -m (omgång nio, F3); prövas som vanligt ord
            vantar = None
            if len(frag) != 1 or EXPANSION.search(helt):
                neka('git %s: filargumentet %r till -F nekas; ange filen bokstavligt' % (sub, helt))
            continue
        if len(frag) == 1 and helt in ('-m', '--message'):  # också citerat: skalet tar bort citaten innan git ser ordet
            vantar = 'meddelande'
            continue
        if len(frag) == 1 and helt in ('-F', '--file'):
            vantar = 'fil'
            continue
        if helt.startswith('-m') and len(helt) > 2 and not helt.startswith('--'):
            neka('git %s: skriv meddelandet som -m "text", inte hopskrivet (%r)' % (sub, helt[:12]))
        if helt.startswith('--message='):
            varde = frag[:]  # fragmenten efter likhetstecknet: första fragmentet börjar med --message=
            forsta, citat = varde[0]
            varde[0] = (forsta[len('--message='):], citat)
            varde = [f for f in varde if f[0] or f[1]]
            if not bokstavligt(varde or [('', None)]):
                neka('git %s: --message= med sammansatt eller expanderbart värde nekas; citera hela meddelandet' % sub)
            continue
        if len(frag) != 1:
            neka('git %s: sammansatt skalord %r nekas; skriv argumenten som hela ord' % (sub, helt))
        if EXPANSION.search(helt):
            neka('git %s med %r nekas: ange filerna bokstavligt, utan glob, klammer, tilde, variabler eller pathspec-magi' % (sub, helt))


def git_kommando(ord_):
    """(index för ordet git, ja/nej inbäddat) i en kommandorads ord; omslag före git måste vara kända."""
    for i, o in enumerate(ord_):
        if Path(o).name == 'git':
            for f in ord_[:i]:
                if not (f in OMSLAG or f.startswith('-') or re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*', f) or f.isdigit()):
                    neka('git bakom %r nekas; bara direkta git-kommandon (eller command, env, nice, nohup, time) prövas' % f)
            return i
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
    delar = delkommandon(kommando)
    skrivningar = 0
    cwd = data.get('cwd')
    for del_ in delar:
        try:
            ord_ = shlex.split(del_)
        except ValueError:
            ord_ = del_.split()
        if not ord_:
            continue
        gi = git_kommando(ord_)
        if gi is None:
            if INBADDAT.search(del_) or any(INBADDAT.search(o) for o in ord_ if ' ' in o):
                neka('git inuti ett inbäddat skal eller en sträng (sh -c, eval, xargs …) nekas')
            continue
        ord_ = ord_[gi:]
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
        if sub not in LASANDE and sub not in SKRIVANDE:
            neka('git %s nekas i obevakade körningar; tillåtet att skriva: add, commit, push' % sub)
        if sub in SKRIVANDE:
            skrivningar += 1
            utan_expansion(sub, args, kommando)
            if sammansatt(kommando):
                neka('git %s måste vara hela kommandot: inga andra delar före eller efter (&&, ;, |, & eller radbrytning); kör ett steg i taget' % sub)
            # exakt reporoten: relativa sökvägar i kommandot tolkas av git från sessionens katalog, men vakten prövar
            # dem från roten (omgång fem, F3: git commit -- backlog/SKILL.md från .claude/skills avsåg skillfilen)
            if not cwd:
                neka('git-skrivningar kräver att kroken vet sessionens arbetskatalog (cwd saknas i anropet)')
            if Path(cwd).resolve() != ROOT:
                neka('git-skrivningar bara från reporoten %s; sessionens arbetskatalog är %s' % (ROOT, cwd))
        if annan_katalog:
            # Läsa i en klon (git -C /tmp/kirurg/repo log -1) är ofarligt; skriva eller starta program är det inte.
            farliga = [a for a in args if a.startswith(('--output', '--open-files-in-pager', '--ext-diff', '--textconv'))
                       or re.fullmatch(r'-O.*', a)]
            if sub in LASANDE and not farliga:
                continue
            neka('git -C/--git-dir/--work-tree tillåts bara för läsande kommandon (%s) utan --output, -O och --ext-diff'
                 % ', '.join(sorted(LASANDE)))
        if sub == 'add':
            flaggor = [a for a in args if a.startswith('-') and a != '--']
            vagar = [a for a in args if not a.startswith('-')]
            if flaggor or not vagar or any(a in ('.', '*') for a in vagar):
                neka('git add tar bara filnamn, inga flaggor; tillåtet: ' + ', '.join(prefix))
            utanfor = [v for v in vagar if not tillaten(v, prefix)]
            if utanfor:
                neka('git add utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            for v in vagar:  # det som köas prövas redan här: nästa kommando ser bara ett rent index
                tr = hemlighet_i_fil(normaliserad(v))
                if tr:
                    neka('filen som ska köas innehåller något som ser ut som en hemlighet (%s) i %s rad %d' % (tr[2], tr[0], tr[1]))
        elif sub == 'commit':
            vagar = commit_sokvagar(args)
            utanfor = [v for v in vagar if not tillaten(v, prefix)]
            if utanfor:
                neka('git commit med sökvägar utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            koade = filer_z(git('diff', '--cached', '--name-only', '-z'))
            utanfor = [f for f in koade if not tillaten(f, prefix)]
            if utanfor:
                neka('köade filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            bin_ = binara_i(git('diff', '--cached', '--numstat'))
            if bin_:
                neka('binära filer kan inte granskas och nekas: %s' % ', '.join(bin_[:5]))
            tr = hemlighet_i(git('diff', '--cached', '-U0', '--no-color', '--text'))  # --text: också filer git skulle kalla binära
            if not tr and vagar:  # med sökvägar committas arbetskopians innehåll, inte index
                for v in vagar:
                    tr = hemlighet_i_fil(normaliserad(v))
                    if tr:
                        break
            if tr:
                neka('det som ska committas innehåller något som ser ut som en hemlighet (%s) i %s rad %d' % (tr[2], tr[0], tr[1]))
            for text in commit_meddelanden(args):
                tr = hemlighet_i_text(text)
                if tr:
                    neka('commit-meddelandet innehåller något som ser ut som en hemlighet (%s) på rad %d; skriv aldrig nycklar i meddelanden' % (tr[1], tr[0]))
        elif sub == 'push':
            if args != ['origin', 'main']:
                neka('bara "git push origin main" är tillåtet')
            # grenen main är det som pushas (inte HEAD); varje utgående commit räknas, också på sidogrenar, och en
            # merge-commit visar sin egen diff mot första föräldern (--diff-merges, inte --first-parent: det senare hoppar
            # över sidogrenens commits; omgång fyra, F27)
            ut = filer_z(git('log', '--format=', '--name-only', '-z', '--diff-merges=first-parent', 'origin/main..refs/heads/main'))
            utanfor = sorted({f for f in ut if not tillaten(f, prefix)})
            if utanfor:
                neka('utgående commits rör filer utanför det tillåtna (%s): %s' % (', '.join(prefix), ', '.join(utanfor)))
            bin_ = binara_i(git('log', '--numstat', '--format=', '--diff-merges=first-parent', 'origin/main..refs/heads/main'))
            if bin_:
                neka('utgående commits innehåller binära filer som inte kan granskas: %s' % ', '.join(sorted(set(bin_))[:5]))
            tr = hemlighet_i(git('log', '-p', '-U0', '--no-color', '--text', '--format=', '--diff-merges=first-parent', 'origin/main..refs/heads/main'))
            if tr:
                neka('någon utgående commit lägger till något som ser ut som en hemlighet (%s) i %s rad %d' % (tr[2], tr[0], tr[1]))
            # commit-meddelandena i varje utgående commit (omgång elva, F27: --format= utelämnade dem)
            delar = git('log', '--format=%h%x00%B%x00', 'origin/main..refs/heads/main').split(b'\0')
            for h_, text in zip(delar[0::2], delar[1::2]):
                tr = hemlighet_i_text(text)
                if tr:
                    neka('commit %s har ett meddelande som ser ut att innehålla en hemlighet (%s) på rad %d' % (h_.decode('ascii', 'replace').strip(), tr[1], tr[0]))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # en vakt som dör ska neka, inte släppa igenom
        print('commitvakten föll (%s: %s) och nekar för säkerhets skull' % (type(e).__name__, e), file=sys.stderr)
        sys.exit(2)
