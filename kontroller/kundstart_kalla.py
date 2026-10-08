"""Byggflödets läsande gräns mot Kundstarts källa, utan kundsvar i kvittot.

Ingen Lager initieras. Befintligt lås och SQLite i rollback-läge öppnas läsande;
WAL eller en journal som kan kräva återställning ger okänd källa utan sidoeffekter.
Ett manuellt underlag måste sakna både överlämning och ärende med samma slug.
"""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
from types import SimpleNamespace

import kundstart as ks
import kundstart_beredning as kb
import kundstart_lagring as kl

SKAL = 'Kundstarts källärende eller överlämning har ändrats eller kan inte verifieras. En aktuell överlämning krävs.'


def _fil(p, repo):
    p = kb.saker(p, repo)
    if not p.is_file() or not stat.S_ISREG(p.stat().st_mode):
        raise ValueError(SKAL)
    return p


@contextlib.contextmanager
def last(u):
    """Pröva källa och filkvitto, håll läslåset över ett kort publiceringssteg.

Låset samordnar Kundstarts skrivningar och gallring. Det får aldrig hållas under
en modellsession. Alla resurser stängs också vid ett oväntat valideringsfel.
"""
    u = Path(u).absolute()
    repo = u.parent.parent
    with contextlib.ExitStack() as resurser:
        try:
            marker = kb.saker(u / 'KUNDSTART.json', repo)
            rot = kb.saker(repo / 'underlag/kundstart', repo)
            body = None
            if marker.exists():
                if _fil(marker, repo).stat().st_size > 10_000_000:
                    raise ValueError(SKAL)
                body = json.loads(marker.read_text(encoding='utf-8'))
                if not isinstance(body, dict) or body.get('status') != 'klar' or body.get('slug') != u.name:
                    raise ValueError(SKAL)
                ks.nyckel(body['id']); ks.nyckel(body['overlamning'])
            if body is not None or rot.exists():
                lock = _fil(rot / '.lagring.las', repo)
                fd = os.open(lock, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                resurser.callback(os.close, fd)
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise ValueError(SKAL)
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                db = _fil(rot / 'arenden.sqlite3', repo)
                # mode=ro kan skapa WAL:s delade filer. Acceptera bara lagrets
                # nuvarande rollback-format; immutable skulle kunna missa WAL.
                with db.open('rb') as f:
                    huvud = f.read(20)
                if huvud[:16] != b'SQLite format 3\x00' or huvud[18:20] != b'\x01\x01':
                    raise ValueError(SKAL)
                for suffix in ('-wal', '-shm', '-journal'):
                    if kb.saker(Path(str(db) + suffix), repo).exists():
                        raise ValueError(SKAL)
                c = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=1, isolation_level=None)
                resurser.callback(c.close)
                c.execute('PRAGMA query_only=ON')
                c.execute('BEGIN')
                row = c.execute('SELECT id,dokument FROM arenden WHERE slug=?', (u.name,)).fetchone()
                if body is None:
                    if row is not None:
                        raise ValueError(SKAL)
                else:
                    if not row or row[0] != body['id'] or kl.sparrad(SimpleNamespace(rot=rot), body['id']):
                        raise ValueError(SKAL)
                    post = c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?', (body['id'], body['overlamning'])).fetchone()
                    if not post:
                        raise ValueError(SKAL)
                    d, p = json.loads(row[1]), json.loads(post[0])
                    if not isinstance(d, dict) or d.get('id') != body['id'] or d.get('slug') != u.name or not kb.post_aktuell(p, d, u):
                        raise ValueError(SKAL)
        except (OSError, ValueError, TypeError, KeyError, sqlite3.Error, ks.Vagrad):
            raise ValueError(SKAL) from None
        # Anroparens fel är anroparens fel, inte ett påstått läsfel i Kundstart.
        yield


def krav(u):
    with last(u):
        pass


def giltig(u):
    try:
        krav(u)
        return True
    except (OSError, ValueError, ks.Vagrad):
        return False
