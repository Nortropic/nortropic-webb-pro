#!/usr/bin/env python3
"""Metadata om verkliga överlämningar till Kirurgen, aldrig en ny kundintervju.

Källärendet läses under dess transaktion. En ändrad källa betyder väntande ny
överlämning, inte att den gamla överlämningen tappat information. Inga svar,
kundnamn, slugs, adresser eller råa dokument kopieras till förbättringsregistret.
Använt och levererat förblir okänt tills de stegen faktiskt observerats.
"""
import json
from pathlib import Path
import kundstart as ks
import kundstart_beredning as kb
from kirurg_loop import Loop,hash_,Vagrad


def kundstart(lager,eid,loop,overlamning=None):
    with lager.trans() as c:
        d=lager._doc(c,eid)
        senaste=c.execute('SELECT post FROM overlamningar WHERE arende=? ORDER BY rowid DESC LIMIT 1',(eid,)).fetchone()
        row=(c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?',(eid,overlamning)).fetchone()
             if overlamning is not None else senaste)
        if overlamning is not None and not row:raise Vagrad('Den angivna överlämningen finns inte.')
        senaste_id=json.loads(senaste[0])['id'] if senaste else None
        obs={'schema':1,'arende_sha256':hash_(eid),'revision':d['revision'],'insamlat':len(d['uppgifter']),
             'overfort':None,'anvant':None,'levererat':None,'kalla_sha256':kb.indata(d),
             'overlamning_sha256':None,'operation_sha256':None,'fil_sha256':None,'status':'saknad_overlamning','brister':[]}
        if row:
            p=json.loads(row[0]);obs['operation_sha256']=hash_(p['id'])
            obs['overlamning_sha256']=hash_({'id':p['id'],'indata':p['indata'],'filer':p['filer']})
            if p['status']!='klar':obs['status']='overlamning_inte_klar'
            elif p['id']!=senaste_id:obs['status']='ersatt_overlamning'
            elif p['indata']!=kb.indata(d):obs['status']='nytt_underlag'
            else:
                repo=Path(p['repo']);u=repo/'underlag'/d['slug'];obs['status']='verifierad'
                try:
                    raw=kb.saker(u/'KUNDSTART.json',repo).read_bytes();obs['fil_sha256']=ks.sha(raw)
                    if len(raw)>8_000_000:raise ValueError('för stort underlag')
                    body=json.loads(raw);expected=ks.vy(d)['uppgifter'];got=body.get('uppgifter')
                    if not isinstance(got,dict):raise ValueError('saknad uppgiftssamling')
                    obs['overfort']=sum(k in got and got[k]==v for k,v in expected.items())
                    if got!=expected:obs['brister'].append('uppgifter_avviker_fran_kalla')
                    if body.get('status')!='klar':obs['brister'].append('slutmarkor_saknas')
                    if any(kb.filhash(kb.saker(u/n,repo))!=h for n,h in p['filer'].items()):
                        obs['brister'].append('fil_avviker_fran_overlamning')
                except (OSError,ValueError,TypeError,AttributeError,ks.Vagrad):
                    obs['brister'].append('overlamnade_filer_kan_inte_verifieras')
                if obs['brister']:obs['status']='overlamningsfel'
        obs['id']=hash_(obs)
        # Samma DB→Loop-låsordning vid alla observationer. Kundändringar och en
        # senare observation kan inte passera mellan snapshot och publicering.
        # Ett omförsök av äldre op får aldrig ersätta senaste överlämningens vy.
        with loop.trans() as register:
            if row:
                register.setdefault('kundstart_overlamningar',{}).setdefault(obs['arende_sha256'],{})[obs['operation_sha256']]=obs
            if not row or p['id']==senaste_id:
                register.setdefault('kundstart',{})[obs['arende_sha256']]=obs
    if obs['status']=='overlamningsfel':
        post=loop.signal('kundstart-overlamning','Insamlat underlag avviker vid överlämning','kundstart',
                         'kundstart:'+obs['arende_sha256'],obs['id'],
                         'Källärendet är oförändrat men överlämnade filer avviker. Inga kundfrågor skapades.',
                         'metadata:'+obs['id'])
        # Återläsning med samma signal får inte skapa en ny diagnos varje gång.
        if not post['diagnoser'] or post['diagnoser'][-1]['signaler']!=[s['id'] for s in post['signaler']]:
            try:
                post=loop.diagnos(post['id'],post['revision'],'overlamningsfel',
                    'Uppgifterna finns i källärendet. Kontrollera överföringen och de deklarerade filerna.',
                    'Börja inte om kundintervjun. Ett senare filbyte kan också ha orsakat avvikelsen.',
                    'stor','observerat')
            except Vagrad:
                # En parallell diagnos ska inte skrivas över. Signalen finns redan kvar.
                pass
        obs['forbattring']=post['id']
    return obs


def efter_overlamning(lager,eid,repo,overlamning):
    """Observation får inte göra en redan sparad kundhandling osparad.

    Anroparen visar ett misslyckat observationsförsök som just observationsfel.
    Inget fel omtolkas till att kunduppgifterna skulle ha gått förlorade.
    """
    try:
        obs=kundstart(lager,eid,Loop(Path(repo)/'kirurgen/forbattringar'),overlamning)
        return {k:obs[k] for k in ('id','status','revision','operation_sha256','overlamning_sha256','insamlat','overfort','anvant','levererat')}
    except Exception:  # sidoobservation får inte dölja ett beständigt sparat kvitto; inga feltexter med kunddata kopieras
        return {'status':'observationsfel','innebord':'Överlämningens kvitto gäller; Kirurgens observation kunde inte sparas.'}
