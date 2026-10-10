#!/usr/bin/env python3
"""nyckelintag.py — kundens nycklar och uppgifter per leverantör till integrationerna (ägarens tillägg 2026-10-10
~10:45Z, punkt 3; BESLUT.md). Nyckeln lämnas utan att den passerar chatten eller repot: i ägarens terminal (utan eko), i
dashboarden (ägarens nyckel) eller i kundens yta (kundens behörighet), och sparas privat, per kund och leverantör, utanför
repot: ~/.nortropic-hemligheter/webb-pro/kunder/<slug>/<leverantör>.nyckel (0600, katalogerna 0700). Uppgifterna som inte
är hemliga (listans id, kontots underdomän, mottagarens adress) ligger bredvid i <leverantör>.json.

Nyckeln läses bara av aktiveringen (kontroller/aktivera.py, genom las_for_aktivering) och går bara till Wrangler.
Läget (status) visar aldrig nyckeln, bara att den finns, när den lades, varifrån och vilken leverantör. En ny nyckel
ersätter den gamla (versionen räknas upp); återkallelse tar bort nyckeln här och markerar att aktiveringen ska ta bort
hemligheten i Workern.

    .venv/bin/python kontroller/nyckelintag.py <slug> <leverantör> [--falt namn=värde ...]   # nyckeln läses utan eko
    .venv/bin/python kontroller/nyckelintag.py <slug> --visa                              # läget, utan nycklar
    .venv/bin/python kontroller/nyckelintag.py <slug> <leverantör> --aterkalla
En nyckel tas aldrig emot som argument (den skulle synas i processlistan och skalets historik).
"""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
ID = r'[1-9][0-9]{0,9}'
EPOST = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
LEVERANTORER = {
    'brevo': {'namn': 'Brevo (nyhetsbrevet)', 'paket': 'k14-brevo-dubbel', 'hemlighet': 'BREVO_API_NYCKEL',
              'falt': {'lista': ID, 'mall': ID}, 'drift': {'lista': 'nyhetsbrev_lista', 'mall': 'nyhetsbrev_mall'}},
    'pipedrive': {'namn': 'Pipedrive (kundregistret)', 'paket': 'k10-pipedrive-lead', 'hemlighet': 'PIPEDRIVE_TOKEN',
                  'falt': {'doman': r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?'}, 'drift': {'doman': 'pipedrive_doman'}},
    'epost': {'namn': 'Formulärets mottagare (Cloudflares e-post)', 'paket': 'k04-cloudflare-epost', 'hemlighet': None,
              'falt': {'mottagare': r'%s(,%s){0,4}' % (EPOST, EPOST)}, 'drift': {'mottagare': 'forfragan_till'}},
}
NYCKEL = re.compile(r'[\x21-\x7e]{16,512}')  # synliga ASCII-tecken, inga blanksteg eller styrtecken
KALLOR = ('terminal', 'dashboard', 'kund')


class Fel(ValueError):
    pass


def rot():
    return Path(os.environ.get('NWP_NYCKELINTAG') or Path.home() / '.nortropic-hemligheter' / 'webb-pro' / 'kunder')


def _katalog(slug, skapa=False):
    if not SLUG.match(slug or ''):
        raise Fel('ogiltig kund')
    r = rot()
    k = r / slug
    for d in (r, k):
        if d.is_symlink():
            raise Fel('nyckelintagets katalog är en symlänk')
    if skapa:
        r.mkdir(parents=True, exist_ok=True, mode=0o700)
        k.mkdir(exist_ok=True, mode=0o700)
        os.chmod(r, 0o700); os.chmod(k, 0o700)
    return k


def _lev(leverantor):
    if leverantor not in LEVERANTORER:
        raise Fel('okänd leverantör: %s' % str(leverantor)[:40])
    return LEVERANTORER[leverantor]


def _skriv(fil, data):
    """Atomiskt och privat (0600): en ny fil skrivs bredvid och byter plats; följer aldrig en symlänk."""
    if fil.is_symlink():
        raise Fel('filen är en symlänk')
    tmp = fil.with_name('.%s.%d.tmp' % (fil.name, os.getpid()))
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(data)
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, fil)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _las(fil):
    if not fil.is_file() or fil.is_symlink():
        return None
    fd = os.open(fil, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r', encoding='utf-8') as f:
        return f.read()


@contextlib.contextmanager
def _las_kund(slug):
    k = _katalog(slug, skapa=True)
    fd = os.open(k / '.las', os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield k
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN); os.close(fd)


def nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def lamna(slug, leverantor, nyckel=None, falt=None, kalla='terminal'):
    """Tar emot en nyckel och/eller uppgifter för en leverantör. Ger läget för leverantören, aldrig nyckeln."""
    lev = _lev(leverantor)
    if kalla not in KALLOR:
        raise Fel('okänd källa')
    falt = dict(falt or {})
    if nyckel is not None and not lev['hemlighet']:
        raise Fel('%s har ingen nyckel' % lev['namn'])
    if nyckel is not None and (not isinstance(nyckel, str) or not NYCKEL.fullmatch(nyckel)):
        raise Fel('nyckeln har fel form (16–512 synliga tecken utan blanksteg)')
    for n, v in falt.items():
        if n not in lev['falt'] or not isinstance(v, str) or not re.fullmatch(lev['falt'][n], v.strip()):
            raise Fel('uppgiften %s har fel form för %s' % (str(n)[:30], lev['namn']))
    if nyckel is None and not falt:
        raise Fel('inget att lämna')
    with _las_kund(slug) as k:
        meta = json.loads(_las(k / (leverantor + '.json')) or '{}')
        meta.setdefault('falt', {})
        meta['falt'].update({n: v.strip() for n, v in falt.items()})
        meta.update(leverantor=leverantor, uppdaterad=nu(), kalla=kalla)
        if nyckel is not None:
            _skriv(k / (leverantor + '.nyckel'), nyckel)
            meta.update(nyckel_lagd=nu(), version=int(meta.get('version') or 0) + 1, aterkallad=None)
        _skriv(k / (leverantor + '.json'), json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
    return status(slug)[leverantor]


def aterkalla(slug, leverantor):
    """Tar bort nyckeln och markerar att aktiveringen ska ta bort hemligheten i Workern."""
    lev = _lev(leverantor)
    if not lev['hemlighet']:
        raise Fel('%s har ingen nyckel' % lev['namn'])
    with _las_kund(slug) as k:
        meta = json.loads(_las(k / (leverantor + '.json')) or '{}')
        with contextlib.suppress(FileNotFoundError):
            os.unlink(k / (leverantor + '.nyckel'))
        meta.update(leverantor=leverantor, aterkallad=nu(), uppdaterad=nu())
        _skriv(k / (leverantor + '.json'), json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
    return status(slug)[leverantor]


def status(slug):
    """Läget per leverantör utan nycklar: om en nyckel finns, när den lades, version, källa, uppgifterna och återkallelse."""
    k = _katalog(slug)
    ut = {}
    for n, lev in LEVERANTORER.items():
        meta = {}
        try:
            meta = json.loads(_las(k / (n + '.json')) or '{}') if k.is_dir() else {}
        except ValueError:
            meta = {'fel': 'läget kan inte läsas'}
        har = bool(lev['hemlighet']) and k.is_dir() and (k / (n + '.nyckel')).is_file() and not (k / (n + '.nyckel')).is_symlink()
        ut[n] = {'leverantor': n, 'namn': lev['namn'], 'paket': lev['paket'], 'hemlighet': lev['hemlighet'],
                 'nyckel': har if lev['hemlighet'] else None, 'nyckel_lagd': meta.get('nyckel_lagd') if har else None,
                 'version': meta.get('version'), 'kalla': meta.get('kalla'), 'falt': meta.get('falt') or {},
                 'aterkallad': meta.get('aterkallad'), 'fel': meta.get('fel')}
    return ut


def las_for_aktivering(slug, leverantor):
    """Nyckeln, för aktiveringen och bara den (kontroller/aktivera.py), som skickar den till Wrangler; None om den saknas."""
    _lev(leverantor)
    k = _katalog(slug)
    return _las(k / (leverantor + '.nyckel')) if k.is_dir() else None


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    a.add_argument('slug')
    a.add_argument('leverantor', nargs='?', choices=sorted(LEVERANTORER))
    a.add_argument('--falt', action='append', default=[], metavar='namn=värde')
    a.add_argument('--visa', action='store_true')
    a.add_argument('--aterkalla', action='store_true')
    x = a.parse_args(argv)
    try:
        if x.visa or not x.leverantor:
            ut = status(x.slug)
        elif x.aterkalla:
            ut = aterkalla(x.slug, x.leverantor)
        else:
            falt = dict(f.split('=', 1) for f in x.falt if '=' in f)
            nyckel = None
            if LEVERANTORER[x.leverantor]['hemlighet']:
                import getpass
                nyckel = getpass.getpass('%s för %s (visas inte; tom rad hoppar över nyckeln): ' % (LEVERANTORER[x.leverantor]['hemlighet'], x.slug)).strip() or None
            ut = lamna(x.slug, x.leverantor, nyckel, falt, 'terminal')
    except Fel as e:
        print(json.dumps({'fel': str(e)}, ensure_ascii=False))
        return 2
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
