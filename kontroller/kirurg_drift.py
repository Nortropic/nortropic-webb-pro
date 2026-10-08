#!/usr/bin/env python3
"""Läsande kapacitetskontroll: kundarbete går före lokala förbättringsprov."""
import fcntl
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import korregister
from kirurg_loop import Vagrad,fil


def register_fritt():
    """Trasiga poster är okänd kapacitet, inte ledigt enligt posterns UI-reserv."""
    rot=korregister.KATALOG.resolve()
    try:
        filer=list(rot.iterdir()) if rot.exists() else []
        if len(filer)>10000:raise ValueError()
        for p in filer:
            if p.suffix!='.json':continue
            p=fil(p,rot)
            fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as f:
                info=os.fstat(f.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size>10000:raise ValueError()
                raw=f.read(10001)
            if len(raw)>10000:raise ValueError()
            d=json.loads(raw)
            if (type(d.get('pid')) is not int or d['pid']<1 or p.stem!=str(d['pid']) or
                not isinstance(d.get('vad'),str) or not d['vad']):raise ValueError()
            if d['vad'] not in ('bygge','arbetare') or not korregister.lever(d['pid']):continue
            start=korregister.startad(d['pid'])
            if d.get('pstart') and start and d['pstart'] not in (start,korregister.startad_lokalt(d['pid'])):continue
            raise Vagrad('Ett kundarbete pågår; förbättringsförsöket får vänta.')
    except (OSError,ValueError,TypeError,AttributeError) as e:
        if isinstance(e,Vagrad):raise
        raise Vagrad('Körregistrets kapacitet kunde inte prövas; försöket får vänta.') from None


def las_ledigt(lock):
    fd=os.open(lock,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise Vagrad('Kapacitetslåset är ogiltigt.')
        try:fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
        except BlockingIOError:raise Vagrad('Kundarbete håller kapaciteten; förbättringsförsöket får vänta.') from None
    finally:os.close(fd)


def kapacitet(root):
    if os.environ.get('NWP_SLUG'):raise Vagrad('Förbättringsförsök får inte startas inifrån ett kundbygge.')
    if korregister.start_vantar():raise Vagrad('Ett kundarbete väntar på start; förbättringsförsöket får vänta.')
    register_fritt()
    root=Path(root)
    lock=fil(root/'kunder/.bygge.las',root)
    if lock.exists():las_ledigt(lock)
    kundrot=fil(root/'underlag/kundstart',root)
    if kundrot.exists():
        # Kundrättelse kan ersätta jobbet medan dess transport fortfarande pågår.
        # Det riktiga transportlåset består genom hela anropet, även efter leasefel.
        for lock in kundrot.iterdir():
            if lock.name.startswith('.transport-') and lock.name.endswith('.las'):las_ledigt(fil(lock,root))
    db=fil(root/'underlag/kundstart/arenden.sqlite3',root)
    if db.exists():
        try:
            c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=.1)
            try:aktiv=c.execute("SELECT 1 FROM jobb WHERE status='pagar' AND lease_slut>? LIMIT 1",(time.time(),)).fetchone()
            finally:c.close()
        except sqlite3.Error:raise Vagrad('Kundstarts kapacitet kunde inte prövas; försöket får vänta.') from None
        if aktiv:raise Vagrad('Kundstart bearbetar ett svar; förbättringsförsöket får vänta.')
