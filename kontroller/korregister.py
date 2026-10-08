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
    .venv/bin/python kontroller/korregister.py tmp <prefix> <vad> --pid P [--dir D]   (skriver katalogens sökväg)

Underhållets egna rökprov i en worktree (NWP_UNDERHALL_PROV=1) anmäls inte: de är underhållets egna prov.

Tempkatalogerna (ägarens beslut 2026-10-07 om städningens villkor, BESLUT.md): egen_tmp skapar en katalog med
tempfile och registrerar den som körningens egen, med ägarfilen .nwp-agare.json i katalogen (pid, starttid ur ps, vad,
användaren och katalogens egen sökväg). Städningen (kontroller/stadning.py, punkt 4) raderar bara en sådan katalog, och
först när körningen som äger den är avslutad; en katalog med repots prefix men utan giltig registrering är en äldre rest
som redovisas och aldrig raderas.
"""
import argparse
import contextlib
import datetime
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KATALOG = Path(os.environ.get('NWP_KORREGISTER') or '/tmp/nwp-korningar')
KANNETECKEN = {'arbetare': 'atelje.py', 'bygge': 'kor.sh', 'rokprov': 'rokprov.sh'}
BYTESLAS = KATALOG / '.byte'  # underhållets intag, ett i taget på maskinen; startkontrollen väntar på det


def ps(falt, pid):
    """Ett fält ur ps för processen, med LC_ALL=C och TZ=UTC så att samma process alltid ger samma text oavsett
    anroparens locale och tidszon (macOS ps skriver å, ä och ö olika under C och UTF-8, och starttiden i lokal tid;
    granskningen av r72, H2, och r73, N5), eller '' när ps inte svarar (en sandlåda, ett prov som bytt ut subprocess)."""
    try:
        return subprocess.run(['ps', '-o', '%s=' % falt, '-p', str(int(pid))], capture_output=True, text=True, timeout=10,
                              env=dict(os.environ, LC_ALL='C', TZ='UTC')).stdout.strip()
    except Exception:  # noqa: BLE001 — registret får aldrig stoppa en körning
        return ''


def kommando(pid):
    return ps('command', pid)


def startad(pid):
    """Processens starttid: identiteten som skiljer den från en senare process med samma pid."""
    return ps('lstart', pid)


def startad_lokalt(pid):
    """Starttiden i lokal tid, som den äldre koden skrev den (granskningen av r74, L6: en post från före bytet till UTC
    räknas som samma process)."""
    try:
        env = {k: v for k, v in os.environ.items() if k != 'TZ'}
        return subprocess.run(['ps', '-o', 'lstart=', '-p', str(int(pid))], capture_output=True, text=True, timeout=10,
                              env=dict(env, LC_ALL='C')).stdout.strip()
    except Exception:  # noqa: BLE001
        return ''


def lever(pid):
    """Finns processen? EPERM betyder att den finns men inte får signaleras (en annan användares process, eller en
    sandlåda som nekar signaler): den lever (granskningen av r100, KAN-7)."""
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
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
    """Startkontrollen väntar på intagslåset: ett långt prov efter ett byte på plats avbryts då (underhall.py). Väntefilen
    bär processens starttid, så att en kvarlämnad fil vars pid nu tillhör en annan process räknas som gammal."""
    pid = int(pid or os.getpid())
    try:
        VANTAR.mkdir(parents=True, exist_ok=True)
        (VANTAR / str(pid)).write_text(json.dumps({'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'pstart': startad(pid)}))
    except OSError:
        pass


def startat(pid=None):
    try:
        (VANTAR / str(int(pid or os.getpid()))).unlink()
    except (OSError, ValueError):
        pass


def start_vantar():
    """Väntar en start på intagslåset? En levande process i VANTAR vars identitet stämmer: väntefilens starttid är processens
    (också när processen bara svarar med EPERM, som en annan användares), och en äldre fil utan starttid räknas bara för en
    process vars kommandorad är motorns (python med kontroller/ eller kor.sh). En kvarlämnad fil vars pid nu tillhör en
    annan process väntar inte (granskningen GR-20261007-r100-om, KAN-D). Svarar inte ps räknas filen som förr."""
    for f in (VANTAR.iterdir() if VANTAR.is_dir() else ()):
        if not f.name.isdigit() or not lever(int(f.name)):
            continue
        pid = int(f.name)
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            d = None
        d = d if isinstance(d, dict) else {}
        nu_s = startad(pid)
        if not nu_s:  # ps svarar inte (en sandlåda): processen räknas
            return True
        if d.get('pstart'):
            if d['pstart'] in (nu_s, startad_lokalt(pid)):
                return True
            continue  # pid:en är återanvänd: filen är gammal
        k_ = kommando(pid)
        if 'kor.sh' in k_ or ('python' in k_ and 'kontroller/' in k_):
            return True
    return False


def poster(rensa=True):
    """Levande poster; en död eller återanvänd pid tas bort (rensa=False: bara läsning, som städningens torrläge)."""
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
            aterbrukad = bool(nu_s) and d['pstart'] not in (nu_s, startad_lokalt(pid))
        else:
            nu_k = kommando(pid) if levande else ''
            tecken = KANNETECKEN.get(d.get('vad'), '')
            aterbrukad = bool(nu_k) and bool(tecken) and tecken not in nu_k
        if not levande or aterbrukad:
            try:
                if rensa:
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


# --- körningens egna tempkataloger (ägarens beslut 2026-10-07: prefixet ensamt räcker inte) ---

AGARFIL = '.nwp-agare.json'
AGARFIL_MAX = 4096  # en ägarfil är liten; en större fil läses inte


def registrera_tmp(katalog, vad, pid=None):
    """Registrerar en befintlig tempkatalog som körningens egen: ägarfilen AGARFIL i katalogen, skapad exklusivt och utan
    att följa en länk, med körningens pid, dess starttid ur ps (samma text som startad() ger), vad, användaren och
    katalogens egen sökväg (realpath). Ger katalogen. Går registreringen inte att skriva står katalogen kvar som
    oregistrerad (städningen redovisar den som en äldre rest och raderar den aldrig), och det står i stderr: registret får
    aldrig stoppa en körning."""
    try:
        pid = int(pid or os.getpid())
        d = os.path.realpath(katalog)
        post = {'schema': 1, 'pid': pid, 'pstart': startad(pid), 'vad': str(vad)[:80], 'uid': os.getuid(), 'sokvag': d,
                'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'utcheckning': str(Path(__file__).resolve().parents[1])}
        fd = os.open(os.path.join(d, AGARFIL), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(json.dumps(post, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001 — registret får aldrig stoppa en körning
        print('korregister: tempkatalogen %s kunde inte registreras (%s: %s)' % (katalog, type(e).__name__, e), file=sys.stderr)
    return str(katalog)


def egen_tmp(prefix, vad, dir=None, pid=None):
    """tempfile.mkdtemp(prefix=…, dir=…) som körningens registrerade katalog (registrera_tmp). Bara en sådan katalog får
    städningen radera, och först när körningen är avslutad (kontroller/stadning.py, punkt 4). Ger sökvägen som mkdtemp."""
    return registrera_tmp(tempfile.mkdtemp(prefix=prefix, dir=dir), vad, pid)


@contextlib.contextmanager
def egen_tmp_med(prefix, vad, dir=None):
    """Som tempfile.TemporaryDirectory, med registreringen: katalogen tas bort när blocket slutar."""
    d = egen_tmp(prefix, vad, dir)
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def tmp_agare(katalog):
    """(registreringen, None) när katalogens ägarfil är giltig, annars (None, skälet). Giltig är en vanlig fil, inte en
    länk, i en katalog som inte heller är en länk; båda ägda av användaren; schema 1 med pid, vad och användaren; och en
    registrerad sökväg som är katalogens egen (en ägarfil som kopierats eller flyttats till en annan katalog gäller inte
    där). Ingen länk följs."""
    try:
        sd = os.lstat(katalog)
    except OSError as e:
        return None, 'katalogen går inte att läsa (%s)' % (e.strerror or e)
    if stat.S_ISLNK(sd.st_mode) or not stat.S_ISDIR(sd.st_mode):
        return None, 'ingen riktig katalog (en länk eller en fil)'
    f = os.path.join(str(katalog), AGARFIL)
    try:
        sf = os.lstat(f)
    except FileNotFoundError:
        return None, 'ingen registrering (ägarfilen %s saknas)' % AGARFIL
    except OSError as e:
        return None, 'ägarfilen går inte att läsa (%s)' % (e.strerror or e)
    if stat.S_ISLNK(sf.st_mode) or not stat.S_ISREG(sf.st_mode):
        return None, 'ägarfilen %s är ingen vanlig fil (en länk följs aldrig)' % AGARFIL
    if sd.st_uid != os.getuid() or sf.st_uid != os.getuid():
        return None, 'katalogen eller ägarfilen ägs av en annan användare (uid %d, %d)' % (sd.st_uid, sf.st_uid)
    if sf.st_size > AGARFIL_MAX:
        return None, 'ägarfilen är för stor för en registrering (%d byte)' % sf.st_size
    try:
        fd = os.open(f, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'r', encoding='utf-8') as fh:
            post = json.loads(fh.read())
    except (OSError, ValueError) as e:
        return None, 'ägarfilen går inte att tolka (%s)' % type(e).__name__
    if not isinstance(post, dict) or post.get('schema') != 1 or not str(post.get('vad') or '').strip():
        return None, 'ägarfilen saknar schema 1 eller vad'
    try:
        pid = int(post.get('pid'))
    except (TypeError, ValueError):
        return None, 'ägarfilen saknar pid'
    if pid <= 1 or post.get('uid') != os.getuid():
        return None, 'ägarfilens pid eller användare stämmer inte (pid %s, uid %s)' % (post.get('pid'), post.get('uid'))
    if post.get('sokvag') != os.path.realpath(katalog):
        return None, 'den registrerade sökvägen (%s) är inte katalogens egen' % post.get('sokvag')
    return dict(post, pid=pid), None


def starttid(text):
    """ps lstart med LC_ALL=C ('Wed Oct  7 05:26:44 2026') som en tidpunkt utan zon, eller None när texten inte går att
    tolka."""
    try:
        return datetime.datetime.strptime(' '.join(str(text or '').split()), '%a %b %d %H:%M:%S %Y')
    except ValueError:
        return None


def tmp_avslutad(post):
    """(avslutad, skälet) för körningen som äger en registrerad katalog: True när processen inte lever, eller när pid:en
    lever med en annan starttid än den registrerade (återanvänd); False när den lever med samma starttid; None när det
    inte går att avgöra (ps svarar inte, eller registreringens starttid saknas eller inte går att tolka), och då räknas
    den som pågående. Starttiden jämförs som tid, inte som text, mot processens starttid i UTC och i lokal tid: en
    registrering i det andra formatet är samma process (granskningen av r100, KAN-7)."""
    pid = int(post['pid'])
    if not lever(pid):
        return True, 'pid %d lever inte' % pid
    reg = starttid(post.get('pstart'))
    if reg is None:
        return None, 'pid %d lever, och registreringens starttid (%s) går inte att tolka' % (pid, post.get('pstart') or 'saknas')
    nu_s = startad(pid)
    nu_t = [t for t in (starttid(nu_s), starttid(startad_lokalt(pid))) if t is not None]
    if not nu_t:
        return None, 'pid %d lever, och ps svarar inte med starttiden' % pid
    if any(abs((t - reg).total_seconds()) <= 1 for t in nu_t):
        return False, 'pid %d lever (startad %s)' % (pid, nu_s or post.get('pstart'))
    return True, 'pid %d har en annan starttid (%s) än den registrerade (%s): en annan process' % (pid, nu_s, post['pstart'])


def main(argv=None):
    p = argparse.ArgumentParser(prog='korregister', description=__doc__.split('\n\n')[0])
    p.add_argument('atgard', choices=('in', 'ut', 'lista', 'tmp'))
    p.add_argument('vad', nargs='?')
    p.add_argument('tmp_vad', nargs='?', help=argparse.SUPPRESS)
    p.add_argument('--slug')
    p.add_argument('--pid', type=int)
    p.add_argument('--dir')
    a = p.parse_args(argv)
    if a.atgard == 'tmp':  # ett skalskript: tmp <prefix> <vad> --pid $$ ger en registrerad katalog
        # --pid krävs: utan den vore ägaren föräldern, och i en kommandosubstitution kan det vara ett mellanskal som
        # slutar direkt (granskningen av r100, KAN-6)
        if not a.vad or not re.fullmatch(r'[A-Za-z0-9_.-]{2,40}', a.vad) or not a.tmp_vad or not a.pid or a.pid <= 1:
            print('tmp <prefix> <vad> --pid <körningens pid, i ett skalskript $$> [--dir D]', file=sys.stderr)
            return 2
        print(egen_tmp(a.vad, a.tmp_vad, dir=a.dir, pid=a.pid))
        return 0
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
