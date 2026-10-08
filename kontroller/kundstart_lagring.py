#!/usr/bin/env python3
"""Intern gallring och lokala säkerhetskopior, aldrig aktiverad på tid av import.

Endast ett daterat ägarbeslut gör ett ärende gallringsbart. En separat beständig
journal spärrar åtkomst före radering och följer med vid återställning. Kopior
utanför det registrerade lokala backupområdet kan inte raderas här. Härledda
eller ändrade filer som inte längre ägs av överlämningen lämnas för manuell
bedömning, och resultatet är då uttryckligen ofullständigt.
"""
import contextlib
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import threading
import time
import kundstart as ks
import kundstart_beredning as kb
import korregister

_LAS={}
_LASVAKT=threading.Lock()
_ANROP=threading.local()


def saker(p):
    p=Path(p).absolute()
    if any(x.is_symlink() for x in (p,*p.parents)):
        raise ks.Vagrad('Kundstarts lagring får inte gå genom en symbolisk länk.')
    return p


@contextlib.contextmanager
def anropslas(lager,eid):
    """Gallring och modelltransport får inte passera varandra. Kundredigering låses inte.

    Stabil låsfil per ärende; kvar utan kundtext efter gallring så att samtidiga
    väntare aldrig låser olika inoder. Tas alltid före lagringens transaktionslås.
    """
    ks.nyckel(eid)
    key=str(lager.rot)+':'+eid
    egna=getattr(_ANROP,'egna',set())
    if key in egna:raise ks.Vagrad('Ett pågående modellanrop kan inte gallra sitt eget underlag.')
    fil=saker(lager.rot/('.transport-'+eid+'.las'))
    fd=os.open(fil,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ks.Vagrad('Transportlåset är ingen vanlig fil.')
        fcntl.flock(fd,fcntl.LOCK_EX)
        _ANROP.egna=egna|{key}
        try:yield
        finally:_ANROP.egna=egna
    finally:os.close(fd)


@contextlib.contextmanager
def las(lager):
    """En återinträdesbar maskin-/trådlåsning för mutation, backup och gallring."""
    key=str(lager.rot)
    with _LASVAKT:
        lock,local=_LAS.setdefault(key,(threading.RLock(),threading.local()))
    with lock:
        if getattr(local,'djup',0):
            local.djup+=1
            try:yield
            finally:local.djup-=1
            return
        f=saker(lager.rot/'.lagring.las');fd=os.open(f,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):raise ks.Vagrad('Lagringslåset är ingen vanlig fil.')
            fcntl.flock(fd,fcntl.LOCK_EX);local.djup=1
            yield
        finally:
            local.djup=0;os.close(fd)


def journal(lager):
    f=saker(lager.rot/'GALLRING.json')
    if not f.exists():return {'schema':1,'arenden':{}}
    try:
        if not f.is_file() or f.stat().st_size>10_000_000:raise ValueError()
        d=json.loads(f.read_text())
        if not isinstance(d,dict) or d.get('schema')!=1 or not isinstance(d.get('arenden'),dict):raise ValueError()
        for k,v in d['arenden'].items():
            ks.nyckel(k)
            if not isinstance(v,dict) or v.get('status') not in ('raderar','klar','ofullstandig'):raise ValueError()
        return d
    except (OSError,ValueError,TypeError):raise ks.Vagrad('Gallringsjournalen kunde inte läsas; åtkomst och återställning avbryts.') from None


def sparrad(lager,eid):
    return eid in journal(lager)['arenden']


def skrivjournal(lager,d):
    kb.atomiskt(saker(lager.rot/'GALLRING.json'),(ks.jsontext(d)+'\n').encode())


def lagringsbeslut(lager,eid,revision,radera_efter,andamal,ansvarig):
    if radera_efter is not None and (type(radera_efter) not in (int,float) or not math.isfinite(radera_efter) or radera_efter<=0):
        raise ks.Vagrad('Ange en verklig tidpunkt eller inget fastställt gallringsdatum.')
    with lager.trans() as c:
        d=lager._doc(c,eid)
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades före lagringsbeslutet.')
        d['lagring']={'radera_efter':radera_efter,'andamal':ks.text(andamal,2000),'ansvarig':ks.text(ansvarig,120),'tid':time.time()}
        lager._spara(c,d);return lager._vy(c,d)


def kopiera_db(kalla,mal):
    """SQLite online backup, inte filkopiering av en öppen databas."""
    saker(kalla);saker(mal)
    with sqlite3.connect(Path(kalla).as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(mal) as dst:
        os.chmod(mal,0o600);src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ks.Vagrad('Säkerhetskopian kunde inte verifieras.')
        if dst.execute('PRAGMA foreign_key_check').fetchall():raise ks.Vagrad('Säkerhetskopian har brutna relationer.')


def filtrera_db(f,ids,aterkalla=False):
    with sqlite3.connect(saker(f)) as c:
        c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA secure_delete=ON')
        for eid in ids:c.execute('DELETE FROM arenden WHERE id=?',(eid,))
        if aterkalla:c.execute('UPDATE atkomst SET aterkallad=1')
        c.commit();c.execute('VACUUM')
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ks.Vagrad('Den filtrerade kopian kunde inte verifieras.')


def manifest(d):
    f=saker(d/'arenden.sqlite3')
    return {'schema':1,'id':d.name,'tid':time.time(),'sha256':ks.sha(f.read_bytes())}


def las_kopia(lager,bid):
    ks.nyckel(bid);d=saker(lager.rot/'sakerhetskopior'/bid)
    try:
        m=json.loads(saker(d/'MANIFEST.json').read_text());f=saker(d/'arenden.sqlite3')
        if not f.is_file() or m.get('schema')!=1 or m.get('id')!=bid:raise ValueError()
        h=ks.sha(f.read_bytes())
        if m.get('sha256')!=h:
            # Journalen skrivs före DB-bytet. Bara just det förverifierade nya
            # innehållet får användas om processen dog före manifestbytet.
            byte=json.loads(saker(d/'UTBYTE.json').read_text())
            ny=byte['ny']
            if (byte.get('schema')!=1 or byte.get('id')!=bid or byte.get('fore')!=m.get('sha256')
                    or ny.get('schema')!=1 or ny.get('id')!=bid or ny.get('sha256')!=h):raise ValueError()
            m=ny
        return d,m
    except (OSError,ValueError,TypeError,KeyError):raise ks.Vagrad('Säkerhetskopian saknas eller har ändrats.') from None


@contextlib.contextmanager
def arbetskopia(lager):
    d=Path(korregister.egen_tmp('nwp-kundstart-','kundstarts backup/gallring',dir=lager.rot))
    try:yield d
    finally:shutil.rmtree(d)


def sakerhetskopiera(lager):
    with las(lager):
        j=journal(lager);bas=saker(lager.rot/'sakerhetskopior');bas.mkdir(exist_ok=True,mode=0o700)
        with arbetskopia(lager) as tmp:
            bid=ks.id_();st=tmp/bid;st.mkdir(mode=0o700)
            kopiera_db(lager.fil,st/'arenden.sqlite3');filtrera_db(st/'arenden.sqlite3',j['arenden'])
            m=manifest(st);kb.atomiskt(st/'MANIFEST.json',(ks.jsontext(m)+'\n').encode())
            os.rename(st,bas/bid)
            return m


def rensa_kopior(lager,ids):
    bas=saker(lager.rot/'sakerhetskopior')
    if not bas.exists():return []
    fel=[]
    for d in sorted(bas.iterdir()):
        try:
            d,m=las_kopia(lager,d.name)
            with arbetskopia(lager) as tmp:
                f=tmp/'arenden.sqlite3';kopiera_db(d/'arenden.sqlite3',f);filtrera_db(f,ids)
                ny={'schema':1,'id':d.name,'tid':time.time(),'sha256':ks.sha(f.read_bytes())}
                # Laga först ett föregående avbrutet byte innan nästa journal
                # ersätts; ett nytt fel får inte tappa föregående förankring.
                if json.loads((d/'MANIFEST.json').read_text())!=m:
                    kb.atomiskt(d/'MANIFEST.json',(ks.jsontext(m)+'\n').encode())
                kb.atomiskt(d/'UTBYTE.json',(ks.jsontext({'schema':1,'id':d.name,'fore':m['sha256'],'ny':ny})+'\n').encode())
                os.replace(f,d/'arenden.sqlite3')
                kb.atomiskt(d/'MANIFEST.json',(ks.jsontext(ny)+'\n').encode())
                (d/'UTBYTE.json').unlink(missing_ok=True)
        except (OSError,ValueError):fel.append('sakerhetskopior/'+d.name)
    return fel


def filplan(lager,d,poster):
    filer={};rotter=set()
    for p in poster:
        repo=saker(p['repo']);u=saker(repo/'underlag'/d['slug']);rotter.add(str(u));rotter.add(str(repo/'kunder'/d['slug']))
        for samling in ('filer','tidigare'):
            for n,h in p[samling].items():
                rel=Path(n)
                if rel.is_absolute() or '..' in rel.parts:raise ks.Vagrad('En överlämningspost har en otillåten filväg.')
                f=saker(u/rel);filer.setdefault(str(f),set()).add(h)
        for n,h in p['tidigare'].items():
            if n in ('KUNDSTART.json','VERKSAMHET.json','UPPDRAG.md'):
                f=saker(u/'kundstart/overlamningar'/p['id']/('fore-'+n));filer.setdefault(str(f),set()).add(h)
        marker=ks.jsontext(dict(json.loads(p['texter']['KUNDSTART.json']),status='publicerar'))+'\n'
        filer.setdefault(str(u/'KUNDSTART.json'),set()).add(ks.sha(marker.encode()))
    bevis=saker(lager.rot/'bevis'/d['id']);rotter.add(str(bevis));antal=0
    if bevis.exists():
        for bas,dirs,namn in os.walk(bevis,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
            for n in dirs+namn:
                f=saker(Path(bas)/n);antal+=1
                if antal>10000:raise ks.Vagrad('Bevisområdet behöver manuell inventering före gallring.')
                if f.is_file():filer.setdefault(str(f),set()).add(ks.sha(f.read_bytes()))
                elif not f.is_dir():raise ks.Vagrad('Bevisområdet innehåller något annat än vanliga filer och kataloger.')
    return {p:sorted(hs) for p,hs in filer.items()},sorted(rotter)


def rensa_filer(p):
    kvar=[]
    # Endast bokförda, oförändrade filer raderas; andra härledningar redovisas.
    for namn,hs in p['filer'].items():
        f=Path(namn)
        try:
            saker(f)
            if not f.exists():continue
            if not f.is_file() or ks.sha(f.read_bytes()) not in hs:kvar.append(namn);continue
            f.unlink()
        except (OSError,ValueError):kvar.append(namn)
    for namn in p['rotter']:
        root=Path(namn)
        try:
            saker(root)
            if not root.exists():continue
            for bas,dirs,filer in os.walk(root,followlinks=False,onerror=lambda e:(_ for _ in ()).throw(e)):
                for n in dirs:
                    if (Path(bas)/n).is_symlink():kvar.append(str(Path(bas)/n))
                for n in filer:
                    if n!='.atelje-start.las':kvar.append(str(Path(bas)/n))
        except (OSError,ValueError):kvar.append(namn)
    return sorted(set(kvar))


def gallra(lager,eid,revision):
    """Ägarinitierat, återupptagbart. Ingen tidsstyrd tjänst aktiveras här."""
    ks.nyckel(eid)
    with anropslas(lager,eid), las(lager):
        j=journal(lager);p=j['arenden'].get(eid)
        if p:
            if p['revision']!=revision:raise ks.Konflikt('Gallringsbegäran hör till en annan revision.')
        else:
            with lager.trans() as c:
                d=lager._doc(c,eid)
                if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades före gallringen.')
                tid=d.get('lagring',{}).get('radera_efter')
                if tid is None or tid>time.time():raise ks.Vagrad('Ärendet saknar ett förfallet gallringsbeslut.')
                poster=[json.loads(x[0]) for x in c.execute('SELECT post FROM overlamningar WHERE arende=?',(eid,))]
                filer,rotter=filplan(lager,d,poster)
                p={'status':'raderar','revision':revision,'tid':time.time(),'filer':filer,'rotter':rotter,'kvar':[]}
            j['arenden'][eid]=p;skrivjournal(lager,j)
        # Spärren ligger beständigt före varje borttagning och varje felväg.
        kvar=rensa_kopior(lager,j['arenden'])
        # Aktiva byggen kan inte raderas under fötterna. Globala/sluglåsen återanvänds.
        underlag=[Path(r) for r in p['rotter'] if Path(r).parent.name=='underlag']
        with contextlib.ExitStack() as stack:
            for u in underlag:
                if u.is_dir():stack.enter_context(kb.arbetslas(u,u.parent.parent))
            kvar+=rensa_filer(p)
            with lager.trans() as c:c.execute('DELETE FROM arenden WHERE id=?',(eid,))
        p.update(status='ofullstandig' if kvar else 'klar',kvar=sorted(set(kvar)),slut=time.time())
        skrivjournal(lager,j);return p


def aterstall(lager,bid,mal):
    """Endast en ny tom lagringsrot; aktuell gallringsjournal är auktoritativ.

    Alla gamla kundlänkar återkallas. Inga servrar eller modelljobb startas.
    Externa filkopior återställs inte och kvitton prövar fortfarande filhashar.
    """
    mal=saker(mal)
    if mal.exists():raise ks.Vagrad('Återställningen kräver en ny, tom lagringsrot.')
    with las(lager):
        d,m=las_kopia(lager,bid);j=journal(lager)
        with arbetskopia(lager) as tmp:
            kopiera_db(d/'arenden.sqlite3',tmp/'arenden.sqlite3')
            filtrera_db(tmp/'arenden.sqlite3',j['arenden'],aterkalla=True)
            # Verifiering sker före första skrivningen i den begärda målroten.
            mal.mkdir(mode=0o700)
            try:
                os.replace(tmp/'arenden.sqlite3',mal/'arenden.sqlite3')
                kb.atomiskt(mal/'GALLRING.json',(ks.jsontext(j)+'\n').encode())
                return ks.Lager(mal)
            except BaseException:
                shutil.rmtree(mal);raise
