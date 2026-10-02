#!/usr/bin/env python3
"""prospektfiler.py — gemensam läsning och låst skrivning av prospektregistret (underlag/prospekt/<kampanj>/REGISTER.json).

Pipelinen (prospekt.py), körarna (prospekt_jobb.py, brev.py, utskick.py) och dashboarden (dashboard/prospekt.py) går
alla genom skriv_register, så två processer aldrig skriver över varandra: lås på <kampanj>/.las, skriv till temporär fil
och byt in med os.replace.

    from prospektfiler import las_register, skriv_register, hitta_post, text_sha, kampanjkatalog

Ingen CLI. Importeras från repots rot (sys.path med kontroller/).
"""
import fcntl
import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROSPEKT = ROOT / 'underlag' / 'prospekt'
KAMPANJ_ID = re.compile(r'^[a-z0-9-]{3,60}$')
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
STATUSAR = ('ny', 'utan-sajt', 'analyserad', 'vald', 'avvisad', 'demo', 'utkast', 'skickat', 'svar', 'kund', 'nej')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def kampanjkatalog(kampanj):
    if not KAMPANJ_ID.match(kampanj or ''):
        raise ValueError('kampanj-id: små bokstäver, siffror och bindestreck, 3–60 tecken')
    return PROSPEKT / kampanj


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def skriv_json(p, data):
    """Skriv till temporär fil i samma katalog och byt in: en läsare ser aldrig en halvskriven fil."""
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp%d' % os.getpid())
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def las_register(kampanj):
    return las_json(kampanjkatalog(kampanj) / 'REGISTER.json') or []


def skriv_register(kampanj, muterare):
    """Lås, läs, låt muterare(poster) ändra listan på plats (eller returnera en ny), skriv, släpp. Returnerar listan."""
    kdir = kampanjkatalog(kampanj)
    kdir.mkdir(parents=True, exist_ok=True)
    with open(kdir / '.las', 'w') as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        try:
            poster = las_json(kdir / 'REGISTER.json') or []
            ny = muterare(poster)
            if ny is not None:
                poster = ny
            skriv_json(kdir / 'REGISTER.json', poster)
        finally:
            fcntl.flock(las, fcntl.LOCK_UN)
    return poster


def hitta_post(poster, slug=None, peOrgNr=None):
    for p in poster:
        if slug and p.get('slug') == slug:
            return p
        if peOrgNr and p.get('peOrgNr') == peOrgNr:
            return p
    return None


def satt_status(kampanj, slug, status, **falt):
    """Byt status på en post (och sätt extra fält). Returnerar posten eller None när slugen saknas."""
    if status not in STATUSAR:
        raise ValueError('okänd status: %s' % status)
    ut = {}

    def mut(poster):
        p = hitta_post(poster, slug=slug)
        if p:
            p['status'] = status
            p.update(falt)
            p['uppdaterad'] = nu()
            ut['post'] = p
    skriv_register(kampanj, mut)
    return ut.get('post')


def logga(kampanj, handelse, **falt):
    kdir = kampanjkatalog(kampanj)
    kdir.mkdir(parents=True, exist_ok=True)
    rad = {'tid': nu(), 'handelse': handelse}
    rad.update(falt)
    with open(kdir / 'logg.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(rad, ensure_ascii=False) + '\n')


def text_sha(amne, text):
    """Hash av den godkända brevtexten: ämne + två radbrytningar + kropp, NFC-normaliserat och trimmat."""
    s = unicodedata.normalize('NFC', (amne or '').strip() + '\n\n' + (text or '').strip())
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def kampanjer():
    """Alla kampanjkataloger med KAMPANJ.json, nyast först."""
    if not PROSPEKT.is_dir():
        return []
    ut = []
    for d in PROSPEKT.iterdir():
        k = las_json(d / 'KAMPANJ.json')
        if d.is_dir() and k:
            ut.append(dict(k, id=d.name))
    return sorted(ut, key=lambda k: k.get('skapad', ''), reverse=True)


def lever(pid):
    """Finns processen? (mönstret ur kontroller/granska.py)"""
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def pagar_pid(katalog):
    """pid ur PAGAR i katalogen när processen lever, annars None (en död PAGAR-fil räknas som ingen körning)."""
    p = Path(katalog) / 'PAGAR'
    try:
        pid = int(p.read_text().strip() or 0)
    except (OSError, ValueError):
        return None
    return pid if pid and lever(pid) else None


def pagar_ta(katalog):
    """Skriv egen pid i PAGAR; ValueError om en annan körning lever."""
    p = Path(katalog)
    p.mkdir(parents=True, exist_ok=True)
    pid = pagar_pid(p)
    if pid:
        raise ValueError('en körning pågår redan (pid %d) i %s' % (pid, p))
    (p / 'PAGAR').write_text(str(os.getpid()))


def pagar_slapp(katalog):
    try:
        (Path(katalog) / 'PAGAR').unlink()
    except OSError:
        pass
