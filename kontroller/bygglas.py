#!/usr/bin/env python3
"""Ett helbygge åt gången: ett flock-lås som kor.sh och dess processvakt håller till avslut.

PID-filen är läsbar status, inte reservationen. FD 9 ärvs av vakten men stängs för
byggsessionen och webbtjänsten. Filen tas aldrig bort: samtidiga starter måste låsa
samma inode även när föregående körning har dött. Inga modell- eller nätanrop.
"""
import fcntl
import os
from pathlib import Path
import stat
import sys
import re
import subprocess

FD = 9


def lasfil(root):
    root = Path(root)
    kund = root / 'kunder'
    if kund.is_symlink() or not kund.is_dir():
        raise OSError('kunder/ är ingen förankrad katalog')
    return kund / '.bygge.las'


def har_las(root):
    """Pröva själva ärvda filbeskrivaren, aldrig en flagga i miljön."""
    try:
        fil = lasfil(root)
        a, b = os.fstat(FD), os.lstat(fil)
        if not stat.S_ISREG(a.st_mode) or not stat.S_ISREG(b.st_mode) or (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
            return False
        fcntl.flock(FD, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def aldre_bygge(root):
    """Kompatibilitet med körningar som startade före flock-rättelsen; en återanvänd PID räcker inte."""
    import korregister
    root = Path(root).resolve()
    fil = lasfil(root).with_name('.bygge-pid')
    if fil.is_symlink():
        raise OSError('byggets PID-fil är en länk')
    try:
        pid = int(fil.read_text().strip())
    except FileNotFoundError:
        return False
    except (UnicodeError, ValueError) as e:
        raise OSError('byggets PID-status går inte att tolka') from e
    if pid <= 1 or not korregister.lever(pid):
        return False
    for post in korregister.poster(rensa=False):
        if post.get('pid') == pid and post.get('vad') == 'bygge':
            return Path(post.get('utcheckning') or '/').resolve() == root
    kommando = korregister.kommando(pid)
    if not kommando:
        raise OSError('PID-statusen kan inte prövas mot processen')
    slut = r'[\"\']?(?=\s|$)'
    if re.search(r'(?:^|\s)[\"\']?' + re.escape(str(root / 'kor.sh')) + slut, kommando):
        return True
    if 'korvakt.py' in kommando and re.search(r'(?:^|\s)--root(?:=|\s+)[\"\']?' + re.escape(str(root)) + slut, kommando):
        return True
    if re.search(r'(?:^|\s)(?:\./)?kor\.sh(?:\s|$)', kommando):
        try:
            svar = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(pid), '-d', 'cwd', '-Fn'],
                                  capture_output=True, text=True, timeout=5)
        except subprocess.SubprocessError as e:
            raise OSError('den äldre körningens arbetskatalog kan inte prövas') from e
        cwd = [rad[1:] for rad in svar.stdout.splitlines() if rad.startswith('n')]
        if svar.returncode or len(cwd) != 1:
            raise OSError('den äldre körningens arbetskatalog kan inte prövas')
        return Path(cwd[0]).resolve() == root
    return False


def main(argv):
    if len(argv)==3 and argv[0]=='--har-kund-las':
        import flodesstart
        return 0 if flodesstart.har_las(argv[1],argv[2]) else 1
    if len(argv) == 2 and argv[0] == '--har-las':
        return 0 if har_las(argv[1]) else 1
    if len(argv) == 2 and argv[0] == '--aldre':
        try:
            if aldre_bygge(argv[1]):
                print('ett bygge pågår redan: en äldre körning håller PID-statusen')
                return 0
            return 1
        except OSError as e:
            print('byggstarten väntar: %s' % e)
            return 0  # en oläsbar status prövas inte förbi
    if len(argv) != 3:
        print('bygglas: <repo> <slug> <verksamhet>', file=sys.stderr)
        return 2
    root, slug, verksamhet = argv
    try:
        fil = lasfil(root)
        fd = os.open(fil, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError('bygglåset är ingen vanlig fil')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if fd != FD:
                os.dup2(fd, FD)
            os.set_inheritable(FD, True)
        finally:
            if fd != FD:
                os.close(fd)
        import flodesstart
        with flodesstart.las(root,slug,arv=True) as kundfd:
            flodesstart.atelje_ledig(root,slug)
            if kundfd!=flodesstart.FD:os.dup2(kundfd,flodesstart.FD)
            os.set_inheritable(flodesstart.FD,True)
            os.execv('/bin/bash', ['bash', str(Path(root) / 'kor.sh'), slug, verksamhet])
    except BlockingIOError:
        print('ett bygge pågår redan: ett i taget')
    except (OSError,ValueError) as e:
        print('bygglåset kunde inte tas: %s' % e, file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
