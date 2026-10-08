#!/usr/bin/env python3
"""Två långa handlingar i flödesvyn, med ateljéns befintliga startjournal.

Ingen kö eller automatisk fortsättning. En uttrycklig begäran startar kor.sh eller
exportera.py; deras egna slutposter avgör resultatet. FD 8 håller kundens startlås
från reservation till avslut och kan inte ersättas av en miljöflagga.
"""
import argparse
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import shlex
import stat
import subprocess
import sys
import time
import uuid

import atelje
import skapande

FD = 8
HANDLINGAR = ('helbygge', 'exportera')


def lasfil(root, slug):
    if not re.fullmatch(r'[a-z0-9-]{2,60}',slug):raise ValueError('ogiltig slug')
    u = Path(root)/'underlag'/slug
    atelje.saker_vag(u,Path(root)/'underlag')
    if (Path(root)/'underlag').is_symlink():raise ValueError('underlagsroten är en länk')
    return u/'.atelje-start.las'


def har_las(root,slug,fd=FD):
    try:
        a,b=os.fstat(fd),os.lstat(lasfil(root,slug))
        if not stat.S_ISREG(a.st_mode) or not stat.S_ISREG(b.st_mode) or (a.st_dev,a.st_ino)!=(b.st_dev,b.st_ino):return False
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return True
    except (OSError,ValueError):return False


@contextlib.contextmanager
def las(root,slug,arv=False):
    if arv and har_las(root,slug):
        yield FD
        return
    fil=lasfil(root,slug)
    fil.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(fil,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('startlåset är ingen vanlig fil')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as e:raise ValueError('Ett arbete pågår för kunden. Läs aktuellt läge.') from e
        yield fd
    finally:os.close(fd)


def atelje_ledig(root,slug):
    p=Path(root)/'underlag'/slug/'atelje/STATUS.json'
    atelje.saker_vag(p,Path(root)/'underlag')
    try:st=json.loads(p.read_text())
    except FileNotFoundError:return
    except (OSError,ValueError) as e:raise ValueError('ateljéns status kan inte prövas') from e
    if not isinstance(st,dict):raise ValueError('ateljéns status kan inte prövas')
    if st.get('pid') and atelje.lever(st['pid']) and st.get('steg') not in atelje.AVSLUTADE:
        raise ValueError('Ateljéns arbetare avslutas ännu. Läs aktuellt läge.')
    if (st.get('steg') not in atelje.AVSLUTADE+('forberedd','fel') and st.get('steg')):
        raise ValueError('Ateljén pågår eller behöver avslutas/återupptas före denna handling.')


def post(slug,start_id):
    p=atelje.startfil(atelje.UNDERLAG/slug/'atelje',start_id)
    if p is None:raise ValueError('ett start-id behövs')
    try:
        d=json.loads(p.read_text())
        if not isinstance(d,dict) or d.get('handling') not in HANDLINGAR:raise ValueError('Start-id hör till en annan handling.')
        return p,d
    except FileNotFoundError:return p,None


@contextlib.contextmanager
def journallas(slug):
    p=lasfil(atelje.ROOT,slug).with_name('.flodesjournal.las')
    fd=os.open(p,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('journalens lås är ingen vanlig fil')
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally:os.close(fd)


def aterhamta(slug,start_id):
    """Fritt kundlås bevisar att varken startföräldern, arbetaren eller bygget lever med låset.

    Samma operations-id återstartas aldrig. Ett avbrott före Popen får ett ärligt slutbesked.
    """
    try:
        with las(atelje.ROOT,slug):
            with journallas(slug):
                p,d=post(slug,start_id)
                if d and d['status']!='slut':
                    atelje.skriv_json_atomiskt(p,dict(d,status='slut',slut=atelje.nu(),slutkod=4,fel='starten avbröts utan slutbesked'))
    except ValueError as e:
        if 'Ett arbete pågår' not in str(e):raise


def pagande(slug):
    """Bara den egna fasta arbetaringången får räknas som ett stoppbart arbete."""
    import korregister
    rot=atelje.UNDERLAG/slug/'ateljestarter'
    atelje.saker_vag(rot,atelje.UNDERLAG)
    ut=[]
    for fil in sorted(rot.glob('*.json')):
        atelje.saker_vag(fil,rot)
        d=json.loads(fil.read_text())
        if not isinstance(d,dict):raise ValueError('Startjournalen kan inte prövas.')
        if d.get('handling') not in HANDLINGAR:continue
        if d.get('status')=='slut':continue
        ut.append(dict(d,start_id=fil.stem,verifierad_pid=None))
        if type(d.get('pid')) is not int:continue
        try:args=shlex.split(korregister.kommando(d['pid']) or '')
        except ValueError:continue
        attendu=[str(atelje.ROOT/'kontroller/flodesstart.py'),slug,d['handling'],fil.stem,'--las-fd']
        if any(args[i:i+5]==attendu for i in range(len(args))):ut[-1]['verifierad_pid']=d['pid']
    return ut


def stoppa(slug):
    aktiva=pagande(slug)
    for d in aktiva:
        with journallas(slug):
            p,nu=post(slug,d['start_id'])
            if nu['status']=='slut':continue
            atelje.skriv_json_atomiskt(p,dict(nu,stoppbegard=True))
        # Signalen är bara ett komplement till den beständiga stoppbegäran.
        # Arbetaren prövar den igen innan den startar sitt kommando.
        aktuell=next((x for x in pagande(slug) if x['start_id']==d['start_id']),None)
        if aktuell and aktuell['verifierad_pid']:
            try:os.kill(aktuell['verifierad_pid'],signal.SIGTERM)
            except ProcessLookupError:pass
        elif aktuell and type(aktuell.get('barn_pid')) is int:
            # arbetaren lever inte eller går inte att verifiera: stoppet går till arbetets egen process när den är vår (B3)
            import korregister
            try:args=shlex.split(korregister.kommando(aktuell['barn_pid']) or '')
            except ValueError:args=[]
            egen=(d['handling']=='helbygge' and args[1:3]==[str(atelje.ROOT/'kor.sh'),slug]) or \
                 (d['handling']=='exportera' and str(atelje.ROOT/'kontroller/exportera.py') in args[:3] and slug in args[:4])
            if egen:
                try:os.kill(aktuell['barn_pid'],signal.SIGTERM)
                except ProcessLookupError:pass
        aterhamta(slug,d['start_id'])
    return 5 if aktiva else 0  # begärt stopp är inte ett påstått slutfört stopp


def krav(slug,handling):
    atelje_ledig(atelje.ROOT,slug)
    if handling=='helbygge':
        ok,skal=skapande.godkand_giltig(slug,atelje.UNDERLAG,atelje.KUNDER)
        if not ok:raise ValueError('Startsidan saknar aktuellt ägargodkännande: '+skal)
        v=json.loads((atelje.UNDERLAG/slug/'VERKSAMHET.json').read_text())
        if not isinstance(v,dict) or not isinstance(v.get('namn'),str) or not v['namn'].strip():raise ValueError('verksamhetens namn saknas')
    elif handling=='exportera':
        s=atelje.KUNDER/slug/'sajt'
        atelje.saker_vag(s,atelje.KUNDER)
        if not (s/'package.json').is_file() or not (s/'src/pages/index.astro').is_file():raise ValueError('Ingen sajt finns att exportera.')
    else:raise ValueError('okänd flödeshandling')


@contextlib.contextmanager
def kundlas_stang(kundlas):
    """Avslutar ett redan öppnat las()-sammanhang när blocket lämnas (starta öppnar det själv för att skilja upptaget lås från fel)."""
    try:yield
    finally:kundlas.__exit__(None,None,None)


def starta(slug,handling,start_id=None):
    if os.environ.get('NWP_SLUG'):raise ValueError('flödeshandlingar startas utanför bygget')
    if handling not in HANDLINGAR:raise ValueError('okänd flödeshandling')
    start_id=start_id or uuid.uuid4().hex
    # Journalen läses först även när låset är upptaget: samma begäran startas aldrig två gånger.
    p,tidigare=post(slug,start_id)
    if tidigare:
        if tidigare['handling']!=handling:raise ValueError('Start-id hör till en annan handling.')
        aterhamta(slug,start_id)
        _,tidigare=post(slug,start_id)
        return tidigare.get('slutkod',5) if tidigare.get('status')=='slut' else 5
    try:
        kundlas=las(atelje.ROOT,slug);fd=kundlas.__enter__()
    except ValueError as e:
        # samma begäran kan hålla låset just nu (två flikar, ett omförsök): då är den registrerad, inte vägrad (GR-20261008-r117-claude#B6)
        if 'Ett arbete pågår' in str(e):
            with journallas(slug):_,tidigare=post(slug,start_id)
            if tidigare and tidigare['handling']==handling:return tidigare.get('slutkod',5) if tidigare.get('status')=='slut' else 5
        raise
    with kundlas_stang(kundlas):
        p,tidigare=post(slug,start_id)
        if tidigare:
            if tidigare['handling']!=handling:raise ValueError('Start-id hör till en annan handling.')
            return tidigare.get('slutkod',5) if tidigare.get('status')=='slut' else 5
        krav(slug,handling)
        p.parent.mkdir(exist_ok=True)
        d={'handling':handling,'tid':atelje.nu(),'status':'reserverad','pid':None}
        with journallas(slug):atelje.skriv_json_atomiskt(p,d)
        try:
            with p.with_suffix('.log').open('ab') as logg:
                child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),slug,handling,start_id,'--las-fd',str(fd)],
                    cwd=atelje.ROOT,stdin=subprocess.DEVNULL,stdout=logg,stderr=subprocess.STDOUT,
                    pass_fds=(fd,),start_new_session=True)
            # Arbetaren skriver sin pid; ingen senare förälderskrivning kan återställa slutstatus.
        except OSError as e:
            with journallas(slug):
                _,d=post(slug,start_id)
                atelje.skriv_json_atomiskt(p,dict(d,status='slut',slutkod=4 if d.get('stoppbegard') else 2,fel='processen kunde inte starta: '+type(e).__name__))
            raise
    return 5


def arbetare(slug,handling,start_id,fd):
    if not har_las(atelje.ROOT,slug,fd):raise ValueError('arbetaren saknar startens ärvda lås')
    if fd!=FD:os.dup2(fd,FD);os.close(fd)
    os.set_inheritable(FD,True)
    p,d=post(slug,start_id)
    if not d or d['handling']!=handling or d['status']!='reserverad':raise ValueError('starten är inte reserverad')
    child=None;stoppad=False;avbrot=False
    def stopp(_sig,_ram):
        nonlocal stoppad
        stoppad=True
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,stopp)
    rc=2
    try:
        with journallas(slug):
            _,d=post(slug,start_id)
            stoppad=stoppad or bool(d.get('stoppbegard'))
            d=dict(d,status='startad',pid=os.getpid());atelje.skriv_json_atomiskt(p,d)
        if stoppad:return 4
        krav(slug,handling)  # Godkännandet prövas igen efter processstart.
        if stoppad:return 4
        with journallas(slug):_,d=post(slug,start_id)
        if d.get('stoppbegard'):stoppad=True;return 4
        if handling=='helbygge':
            v=json.loads((atelje.UNDERLAG/slug/'VERKSAMHET.json').read_text())
            args=['/bin/bash',str(atelje.ROOT/'kor.sh'),slug,v['namn']]
        else:args=[sys.executable,'-B',str(atelje.ROOT/'kontroller/exportera.py'),slug,'--git']
        # Exportens npm och byggskript kan skapa barn i egna sessioner. Följ samma
        # macOS-processidentiteter som korvakt, inte bara Popen-processens pid.
        import korvakt
        trad=korvakt.Trad(korvakt.las_process(os.getpid())) if handling=='exportera' else None
        child=subprocess.Popen(args,cwd=atelje.ROOT,env=dict(os.environ,NWP_FLODE_START_ID=start_id),pass_fds=(FD,))
        with journallas(slug):  # barnets pid: ett stopp når arbetet också om arbetaren dör (GR-20261008-r117-claude#B3)
            _,d=post(slug,start_id);atelje.skriv_json_atomiskt(p,dict(d,barn_pid=child.pid,barn_startad=atelje.nu()))
        frist=None;signalerade=set();avbrot=avbrot or stoppad;nasta_koll=0
        while True:
            if trad:trad.skanna()
            rc=child.poll()
            if not stoppad and rc is None and time.monotonic()>=nasta_koll:
                # den beständiga stoppbegäran gäller också när signalen inte nått arbetaren (GR-20261008-r117-claude#B2)
                nasta_koll=time.monotonic()+1
                try:
                    with journallas(slug):_,dj=post(slug,start_id)
                    stoppad=bool(dj and dj.get('stoppbegard'))
                except (OSError,ValueError):pass
            if stoppad and rc is None:avbrot=True
            barn=trad.under({trad.rot},()) if trad else []
            barn=[b for b in barn if b.pid!=os.getpid()]
            if stoppad or rc is not None:
                if frist is None:frist=time.monotonic()+2
                if not trad and stoppad and rc is None and 'hel' not in signalerade:
                    child.terminate();signalerade.add('hel')
                for b in barn:
                    sig=signal.SIGKILL if time.monotonic()>=frist else signal.SIGTERM
                    if (b.uid,sig) not in signalerade:
                        korvakt.signalera(b,sig);signalerade.add((b.uid,sig))
            if rc is not None and not barn:break
            time.sleep(.03)
        child.wait()
        if avbrot:rc=4
        return rc
    finally:
        with journallas(slug):
            _,d=post(slug,start_id)
            sen=bool(d.get('stoppbegard') or stoppad) and not avbrot and child is not None
            # slutkod 4 bara när stoppet avbröt arbetet; ett stopp som kom efter att arbetet slutat bokförs som sent (B2)
            atelje.skriv_json_atomiskt(p,dict(d,status='slut',slut=atelje.nu(),slutkod=4 if avbrot or child is None and (stoppad or d.get('stoppbegard')) else rc,
                                              **({'stoppbegard_sen':True} if sen else {})))
        os.close(FD)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('slug');a.add_argument('handling',choices=HANDLINGAR);a.add_argument('start_id');a.add_argument('--las-fd',type=int,required=True)
    v=a.parse_args()
    try:sys.exit(arbetare(v.slug,v.handling,v.start_id,v.las_fd))
    except (OSError,ValueError,RuntimeError) as e:print(str(e),file=sys.stderr);sys.exit(2)
