#!/usr/bin/env python3
"""Betrodd vakt för ett enda lokalt Kirurgprov.

Ärver försökslåset och en läsände vars enda skrivände tillhör styrenheten.
Provprocessen får ingen av dem. Även hård styrenhetsdöd ger EOF; vakten
avslutar och väntar in provet före upplåsning. Provprofilen nekar process-fork.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import select
import signal
import subprocess
import time


def kor(spec,livfd,lasfd):
    os.fstat(lasfd)
    cfg=json.loads(Path(spec).read_text())
    stopp=False;barn=None
    def stoppa(*_):
        nonlocal stopp
        stopp=True
    for s in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(s,stoppa)
    start=time.monotonic();utfall={'rc':None,'timeout':False,'avbruten':False}
    # Gränsen gäller också ärvt stdout. Vakten exekverar aldrig kandidatkod.
    def begransa():
        resource.setrlimit(resource.RLIMIT_FSIZE,(1_000_000,1_000_000))
        cpu=max(1,int(cfg['sekunder'])+1);resource.setrlimit(resource.RLIMIT_CPU,(cpu,cpu))
    try:
        with Path(cfg['logg']).open('wb') as logg:
            os.chmod(cfg['logg'],0o600)
            # Pröva EOF även före starten, så ett redan avbrutet prov inte startar.
            if select.select([livfd],[],[],0)[0] and os.read(livfd,1)==b'':stopp=True
            if not stopp:
                barn=subprocess.Popen(cfg['args'],cwd=cfg['cwd'],env=cfg['env'],stdin=subprocess.DEVNULL,
                    stdout=logg,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=begransa)
            while barn and barn.poll() is None:
                if select.select([livfd],[],[],.02)[0] and os.read(livfd,1)==b'':stopp=True
                if time.monotonic()-start>=cfg['sekunder']:utfall['timeout']=True
                if stopp or utfall['timeout']:
                    try:os.killpg(barn.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    barn.wait(timeout=5);break
            utfall['rc']=barn.returncode if barn else None
            utfall['avbruten']=stopp
    finally:
        if barn and barn.poll() is None:
            try:os.killpg(barn.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            barn.wait(timeout=5)
        utfall['sekunder']=round(time.monotonic()-start,3)
        p=Path(cfg['resultat']);tmp=p.with_suffix('.tmp')
        try:
            with tmp.open('x') as f:os.chmod(tmp,0o600);json.dump(utfall,f);f.flush();os.fsync(f.fileno())
            os.replace(tmp,p)
        finally:tmp.unlink(missing_ok=True)
        os.close(livfd);os.close(lasfd)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec');p.add_argument('--liv-fd',type=int,required=True);p.add_argument('--las-fd',type=int,required=True)
    a=p.parse_args();kor(a.spec,a.liv_fd,a.las_fd)
