#!/usr/bin/env python3
"""backlog_commit.py — efter en byggkörning (kor.sh): committar och pushar bara byggets egna backlogposter, med
commitvaktens kontroller, och bara när korslut inte funnit ändrad mekanik (Codex 2026-10-04, F27 och F3).

    .venv/bin/python kontroller/backlog_commit.py <slug> <korning> <korslut-kod>

Byggets poster känns igen på frontmattern: kalla: bygge, korning: <körningens stämpel> (backlog.py ny skriver den ur
NWP_KORNING) och kallref under kunder/<slug>/. Andra sessioners okommitterade poster lämnas. Varje post prövas som
commitvakten prövar en köad fil (text, ingen NUL-byte, inget som ser ut som en hemlighet; bara typ och rad rapporteras),
och pushen sker bara när hela den utgående historiken enbart rör backlog/, saknar binärer och hemligheter i diffar och
meddelanden; annars stannar posterna committade lokalt. Slutkod 0 publicerat eller inget att publicera · 1 stoppat.
"""
import importlib.util
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

POST = re.compile(r'^backlog/B-[a-z0-9-]+\.md$')


def vakt():
    """Commitvaktens funktioner, laddade ur kroken (samma mönster, samma maskering)."""
    spec = importlib.util.spec_from_file_location('commitvakt', ROOT / '.claude' / 'hooks' / 'commitvakt.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.SLUT = time.monotonic() + 120  # efterkörningen får mer tid än en krok
    return m


def git(*a):
    return subprocess.run(['git', '-C', str(ROOT), *a], capture_output=True, text=True, timeout=120)


def frontmatter(p):
    """Postens frontmatter som dict (bara nyckel: värde-rader mellan de två ---)."""
    m = re.match(r'^---\n(.*?)\n---\n', p.read_text(encoding='utf-8'), re.S)
    ut = {}
    for rad in (m.group(1).splitlines() if m else []):
        k, _, v = rad.partition(':')
        if k.strip():
            ut[k.strip()] = v.strip()
    return ut


def byggets_poster(slug, korning):
    """Ospårade poster i backlog/ som bär körningens stämpel och byggets slug; allt annat lämnas."""
    ut, lamnade = [], []
    inv = git('ls-files', '--others', '--exclude-standard', '--', 'backlog')
    if inv.returncode:  # en inventering som inte vet säger inte 'inga poster' (Codex 2026-10-04, F3)
        raise RuntimeError('git ls-files misslyckades: %s' % inv.stderr.strip()[-200:])
    for rel in inv.stdout.splitlines():
        p = ROOT / rel
        if not POST.match(rel) or p.is_symlink() or not p.is_file():
            lamnade.append(rel)
            continue
        try:
            meta = frontmatter(p)
        except (OSError, UnicodeDecodeError):
            lamnade.append(rel)
            continue
        if meta.get('kalla') == 'bygge' and meta.get('korning') == korning and (meta.get('kallref') or '').startswith('kunder/%s/' % slug):
            ut.append(rel)
        else:
            lamnade.append(rel)
    return ut, lamnade


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 3 or not re.fullmatch(r'[a-z0-9-]{2,60}', argv[0]) or not re.fullmatch(r'[0-9TZ]{16}', argv[1]):
        print('användning: backlog_commit.py <slug> <korning> <korslut-kod>', file=sys.stderr)
        return 1
    slug, korning, kod = argv[0], argv[1], argv[2]
    if kod not in ('0', '1'):
        print('backlog: publicerar inget efter slutkod %s (mekaniken ändrad eller claude föll)' % kod)
        return 1
    try:
        poster, lamnade = byggets_poster(slug, korning)
    except RuntimeError as e:
        print('backlog: stoppat, %s' % e)
        return 1
    if not poster:
        print('backlog: inga egna poster att publicera' + (' (%d andra okommitterade lämnas)' % len(lamnade) if lamnade else ''))
        return 0
    v = vakt()
    try:
        for rel in poster:  # varje post prövas som en köad fil: text, ingen NUL-byte, inget som ser ut som en hemlighet
            tr = v.hemlighet_i_fil(rel)
            if tr:
                print('backlog: stoppat, %s innehåller något som ser ut som en hemlighet (%s) rad %d; inget committas' % (tr[0], tr[2], tr[1]))
                return 1
        gren = git('symbolic-ref', '-q', 'HEAD')
        if gren.returncode or gren.stdout.strip() != 'refs/heads/main':  # commiten ska hamna på main, inte på en annan utcheckad gren (F3)
            print('backlog: stoppat, %s är utcheckad i stället för main; inget committas' % (gren.stdout.strip() or 'ingen gren'))
            return 1
        if git('add', '--', *poster).returncode or git('commit', '-q', '-m', 'Bygge %s: backlogposter' % slug, '--', *poster).returncode:
            print('backlog: commit misslyckades; inget publicerat')
            return 1
        kand = git('rev-parse', 'HEAD').stdout.strip()  # kandidaten låses till ett commit-ID: kontrollen och pushen gäller exakt den (F3/F27)
        med = git('show', '--name-only', '--format=', kand).stdout.split()
        if not kand or any(rel not in med for rel in poster):
            print('backlog: stoppat, kandidaten %s innehåller inte posterna; inget pushas' % kand[:12])
            return 1
        print('backlog: committade %s som %s' % (', '.join(poster), kand[:12]))
        if git('remote', 'get-url', 'origin').returncode:
            print('backlog: ingen origin; ingen push')
            return 0
        bas = git('rev-parse', '--verify', '-q', 'origin/main').stdout.strip()
        if not bas:
            print('backlog: origin/main okänd; ingen push')
            return 1
        omrade = '%s..%s' % (bas, kand)
        ut = v.filer_z(v.git('log', '--format=', '--name-only', '-z', '--diff-merges=first-parent', omrade))
        utanfor = sorted({f for f in ut if not f.startswith('backlog/')})
        if utanfor:
            print('backlog: pushen stoppad, den utgående historiken rör annat än backlog/ (%s); posterna är committade lokalt' % ', '.join(utanfor[:5]))
            return 1
        bin_ = v.binara_i(v.git('log', '--numstat', '--format=', '--diff-merges=first-parent', omrade))
        if bin_:
            print('backlog: pushen stoppad, binära filer i den utgående historiken: %s' % ', '.join(sorted(set(bin_))[:5]))
            return 1
        tr = v.hemlighet_i(v.git('log', '-p', '-U0', '--no-color', '--text', '--format=', '--diff-merges=first-parent', omrade))
        if tr:
            print('backlog: pushen stoppad, något som ser ut som en hemlighet (%s) i %s rad %d i den utgående historiken' % (tr[2], tr[0], tr[1]))
            return 1
        delar = v.git('log', '--format=%h%x00%B%x00', omrade).split(b'\0')
        for h_, text in zip(delar[0::2], delar[1::2]):
            tr = v.hemlighet_i_text(text)
            if tr:
                print('backlog: pushen stoppad, commit %s har ett meddelande som ser ut att innehålla en hemlighet (%s)' % (h_.decode('ascii', 'replace').strip(), tr[1]))
                return 1
    except SystemExit as e:  # commitvaktens neka(): en vakt som inte vet säger nej
        print('backlog: stoppat av commitvaktens kontroll (kod %s)' % e.code)
        return 1
    p = git('push', '-q', 'origin', '%s:refs/heads/main' % kand)  # exakt den kontrollerade kandidaten, inte den rörliga main
    if p.returncode:
        print('backlog: committad lokalt; push misslyckades: %s' % (p.stderr.strip()[-200:] or 'okänt fel'))
        return 1
    print('backlog: pushad (%s)' % kand[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())
