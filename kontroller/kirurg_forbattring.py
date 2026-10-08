#!/usr/bin/env python3
"""Befintliga Kirurgens observationer och avgränsade lokala försök.

Ingen generell shell-ingång, modellstart, schemaläggning, mandatredigering eller
publicering. Dashboarden hanterar analys och paus; försök körs av denna lokala
CLI inom kirurg_forsok:s separata mandat och processgräns.
"""
import argparse
import json
from pathlib import Path
import sys
import kundstart as ks
import kirurg_loop as kl

ROOT=Path(__file__).resolve().parents[1]
HANDLINGAR=('signal','diagnos','plan','disposition','paus','stickprov','kundstart')


def loop(repo):return kl.Loop(Path(repo)/'kirurgen/forbattringar')


def vy(repo):
    p=Path(repo)/'kirurgen/forbattringar/FORBATTRINGAR.json'
    if not p.exists():
        d={'schema':1,'revision':0,'paus':False,'poster':{},'forsok':{},'forbrukat':{},'kundstart':{},'skapad':False}
    else:d=loop(repo).vy()|{'skapad':True}
    import kirurg_kallhalsa
    try:d['kallhalsa']=kirurg_kallhalsa.las(Path(repo)/'kirurgen/spaning')|{'status':'last'}
    except kl.Vagrad:d['kallhalsa']={'status':'lasfel','kallor':{}}
    return d


def handling(repo,namn,data):
    if namn not in HANDLINGAR:raise kl.Vagrad('Okänd förbättringshandling.')
    l=loop(repo)
    if namn=='signal':
        ks.falt(data,('problem','titel','fas','kalla','version','observation','belagg','kallandel'),
                      ('problem','titel','fas','kalla','version','observation','belagg'))
        return l.signal(**data)
    if namn=='diagnos':
        ks.falt(data,('pid','revision','slag','skal','alternativ','konsekvens','belaggsstyrka'),
                      ('pid','revision','slag','skal','alternativ','konsekvens','belaggsstyrka'))
        return l.diagnos(**data)
    if namn=='plan':
        ks.falt(data,('pid','revision','plan'),('pid','revision','plan'));return l.plan(**data)
    if namn=='disposition':
        ks.falt(data,('pid','revision','val','skal','ateroppna','backlog'),('pid','revision','val','skal'))
        return l.disposition(**data)
    if namn=='paus':
        ks.falt(data,('paus',),('paus',));l.pausa(data['paus']);return {'paus':data['paus']}
    if namn=='stickprov':
        ks.falt(data,('seed','antal'),('seed','antal'));return {'poster':l.stickprov(data['seed'],data['antal'])}
    if namn=='kundstart':
        ks.falt(data,('arende',),('arende',))
        import kirurg_signaler
        return kirurg_signaler.kundstart(ks.Lager(Path(repo)/'underlag/kundstart'),ks.nyckel(data['arende']),l)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__.split('\n\n')[0]);p.add_argument('handling',choices=('status','forsok','registrera-inforande','folj-upp','registrera-aterstallning',*HANDLINGAR))
    a=p.parse_args(argv)
    try:
        if a.handling=='status':resultat=vy(ROOT)
        else:
            raw=sys.stdin.read(500_001)
            if len(raw)>500_000:raise kl.Vagrad('Uppdraget är för stort.')
            data=json.loads(raw)
            if a.handling=='forsok':
                ks.falt(data,('pid','revision','mid','start_id','bas','andringar'),('pid','revision','mid','start_id','bas','andringar'))
                import kirurg_forsok
                resultat=kirurg_forsok.kor(loop(ROOT),root=ROOT,**data)
            elif a.handling in ('registrera-inforande','folj-upp','registrera-aterstallning'):
                import kirurg_uppfoljning as ku
                krav={'registrera-inforande':('pid','revision','forsok','mid','granskning','version'),
                      'folj-upp':('pid','revision','version','utfall','bevis','omfattning','observator'),
                      'registrera-aterstallning':('pid','revision','version','mid')}[a.handling]
                ks.falt(data,krav,krav)
                fn={'registrera-inforande':ku.registrera,'folj-upp':ku.folj_upp,'registrera-aterstallning':ku.aterstallning}[a.handling]
                resultat=fn(loop(ROOT),ROOT,**data)
            else:resultat=handling(ROOT,a.handling,data)
        print(ks.jsontext(resultat));return 0
    except (OSError,ValueError,TypeError,KeyError) as e:
        print(ks.jsontext({'fel':str(e)}),file=sys.stderr);return 2


if __name__=='__main__':sys.exit(main())
