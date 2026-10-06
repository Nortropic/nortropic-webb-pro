#!/usr/bin/env python3
"""korregister.py — maskinvitt register över pågående körningar (den oberoende granskningen 2026-10-06, fynd 3).
Underhållet ändrar delad miljö (Homebrew, globala npm-paket, ~/.impeccable, och den .venv och de kontroller/node_modules
som varje worktree länkar till), så det måste se körningar i alla utcheckningar, inte bara den egna. Ateljéns arbetare,
kor.sh och rokprov.sh anmäler sig här med pid och tar bort sin post när de slutar; en post vars process inte lever (eller
vars pid återanvänts av något annat) räknas inte.

    /tmp/nwp-korningar/<pid>.json   {"pid", "vad", "utcheckning", "slug", "start", "kommando"}

    .venv/bin/python kontroller/korregister.py in <vad> [--slug S] [--pid P]
    .venv/bin/python kontroller/korregister.py ut [--pid P]
    .venv/bin/python kontroller/korregister.py lista

Underhållets egna rökprov i en worktree (NWP_UNDERHALL_PROV=1) anmäls inte: de är underhållets egna prov.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

KATALOG = Path(os.environ.get('NWP_KORREGISTER') or '/tmp/nwp-korningar')
KANNETECKEN = {'arbetare': 'atelje.py', 'bygge': 'kor.sh', 'rokprov': 'rokprov.sh'}
BYTESLAS = KATALOG / '.byte'  # underhållets intag, ett i taget på maskinen; startkontrollen väntar på det


def ps(falt, pid):
    """Ett fält ur ps för processen, med LC_ALL=C så att samma process alltid ger samma text oavsett anroparens locale
    (macOS ps skriver å, ä och ö olika under C och UTF-8; granskningen av r72, H2), eller '' när ps inte svarar (en
    sandlåda, ett prov som bytt ut subprocess)."""
    try:
        return subprocess.run(['ps', '-o', '%s=' % falt, '-p', str(int(pid))], capture_output=True, text=True, timeout=10,
                              env=dict(os.environ, LC_ALL='C')).stdout.strip()
    except Exception:  # noqa: BLE001 — registret får aldrig stoppa en körning
        return ''


def kommando(pid):
    return ps('command', pid)


def startad(pid):
    """Processens starttid: identiteten som skiljer den från en senare process med samma pid."""
    return ps('lstart', pid)


def lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def registrera(vad, slug=None, pid=None, utcheckning=None):
    """Anmäler körningen; ger posten eller None (registret går inte att skriva: körningen fortsätter, och det står i
    stderr)."""
    if os.environ.get('NWP_UNDERHALL_PROV') == '1':
        return None
    try:
        pid = int(pid or os.getpid())
        KATALOG.mkdir(parents=True, exist_ok=True)
        f = KATALOG / ('%d.json' % pid)
        f.write_text(json.dumps({'pid': pid, 'vad': vad, 'slug': slug, 'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                                 'utcheckning': str(utcheckning or Path(__file__).resolve().parents[1]),
                                 'kommando': kommando(pid)[:300], 'pstart': startad(pid)}, ensure_ascii=False), encoding='utf-8')
        return f
    except Exception as e:  # noqa: BLE001 — registret får aldrig stoppa en körning
        print('korregister: kunde inte anmäla körningen (%s: %s)' % (type(e).__name__, e), file=sys.stderr)
        return None


def avregistrera(pid=None):
    try:
        (KATALOG / ('%d.json' % int(pid or os.getpid()))).unlink()
    except Exception:  # noqa: BLE001
        pass


VANTAR = KATALOG / 'vantar'  # startkontroller som väntar på intagslåset: <pid>


def vill_starta(pid=None):
    """Startkontrollen väntar på intagslåset: ett långt prov efter ett byte på plats avbryts då (underhall.py)."""
    try:
        VANTAR.mkdir(parents=True, exist_ok=True)
        (VANTAR / str(int(pid or os.getpid()))).write_text(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    except OSError:
        pass


def startat(pid=None):
    try:
        (VANTAR / str(int(pid or os.getpid()))).unlink()
    except (OSError, ValueError):
        pass


def start_vantar():
    """Väntar en start på intagslåset? (en levande process i VANTAR)"""
    for f in (VANTAR.iterdir() if VANTAR.is_dir() else ()):
        if f.name.isdigit() and lever(int(f.name)):
            return True
    return False


def poster():
    """Levande poster; en död eller återanvänd pid tas bort."""
    ut = []
    for f in sorted(KATALOG.glob('*.json')) if KATALOG.is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
            pid = int(d['pid'])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        # en återanvänd pid har en annan starttid än den som anmäldes (äldre poster: kännetecknet i kommandoraden);
        # svarar inte ps (en sandlåda) räknas posten
        levande = lever(pid)
        if d.get('pstart'):
            nu_s = startad(pid) if levande else ''
            aterbrukad = bool(nu_s) and nu_s != d['pstart']
        else:
            nu_k = kommando(pid) if levande else ''
            tecken = KANNETECKEN.get(d.get('vad'), '')
            aterbrukad = bool(nu_k) and bool(tecken) and tecken not in nu_k
        if not levande or aterbrukad:
            try:
                f.unlink()
            except OSError:
                pass
            continue
        ut.append(d)
    return ut


def pagaende(utom=()):
    """Beskrivningar av pågående körningar på maskinen, utom de angivna pid:arna."""
    utom = set(int(x) for x in utom)
    return ['%s%s (pid %d, %s)' % (d['vad'], (' ' + d['slug']) if d.get('slug') else '', d['pid'], d.get('utcheckning') or '?')
            for d in poster() if int(d['pid']) not in utom]


def main(argv=None):
    p = argparse.ArgumentParser(prog='korregister', description=__doc__.split('\n\n')[0])
    p.add_argument('atgard', choices=('in', 'ut', 'lista'))
    p.add_argument('vad', nargs='?')
    p.add_argument('--slug')
    p.add_argument('--pid', type=int)
    a = p.parse_args(argv)
    if a.atgard == 'in':
        if a.vad not in KANNETECKEN:
            print('vad: %s' % ', '.join(KANNETECKEN), file=sys.stderr)
            return 2
        registrera(a.vad, a.slug, a.pid or os.getppid())
    elif a.atgard == 'ut':
        avregistrera(a.pid or os.getppid())
    else:
        print('\n'.join(pagaende()) or 'inga pågående körningar')
    return 0


if __name__ == '__main__':
    sys.exit(main())
