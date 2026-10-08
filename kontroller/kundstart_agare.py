#!/usr/bin/env python3
"""Ägarens befintliga dashboard till Kundstart; ingen kund-API eller modellstart."""
from pathlib import Path
import json
import kundstart as ks
import kundstart_beredning as kb
import kundstart_behorighet as kh
import kundstart_fortsatt as kf
import kundstart_lagring as kl
import kundstart_matt as km

HANDLINGAR=('overlamna','aterstall_overlamning','erbjudande','deltagare','aterkalla_person','returfraga','bedom_retursvar',
            'lagringsbeslut','gallra','sakerhetskopia')


def lager(repo):return ks.Lager(Path(repo)/'underlag/kundstart')


def lista(repo):
    if not (Path(repo)/'underlag/kundstart/arenden.sqlite3').exists():return {'arenden':[],'lagring':'inte_skapad'}
    db=lager(repo)
    with db.trans() as c:
        sparrade=kl.journal(db)['arenden']
        rows=[json.loads(r[0]) for r in c.execute('SELECT dokument FROM arenden ORDER BY uppdaterad DESC')]
        return {'arenden':[{'id':d['id'],'slug':d['slug'],'revision':d['revision'],'uppdaterad':d['uppdaterad'],
                 'bestallning':ks.vy(d)['bestallning'],'modell':d['modell']['status'],
                 'fragor':len(d['fragor'])+sum(q['status']!='svarad' for q in d.get('returfragor',{}).values()),
                 'fiktiv':d.get('fiktiv',True)} for d in rows if d['id'] not in sparrade],
                'lagring':'lokal_privata_sqlite','gallringar':{k:{n:p[n] for n in ('status','revision','kvar')} for k,p in sparrade.items()}}


def faser(d,repo):
    # Modellens markering är ett förslag som behöver klarläggas, aldrig ett
    # tyst ägarbeslut. Utan strukturerad fas får vi inte gissa att den kan vänta.
    hinder=['Kritisk modellfråga behöver prövas: '+q['text']
            for q in d.get('fragor',[]) if q.get('kritisk')]
    try:kb.paket(d)
    except ks.Vagrad as e:hinder.append(str(e))
    def fragor(fas):
        ordning=('forberedelse','skiss','helbygge','publicering','forvaltning')
        return [q['text'] for q in d.get('returfragor',{}).values()
                if ordning.index(q['fas'])<=ordning.index(fas) and q['kritisk'] and not kf.klarlagd(d,q)]
    prep=hinder+fragor('forberedelse')
    skiss=hinder+fragor('skiss')
    hel=hinder+fragor('helbygge')
    if not ks.vy(d)['bestallning']['aktuell']:hel.append('Ett aktuellt definierat erbjudande har inte accepterats.')
    if not d.get('overlamning',{} ) or not d['overlamning'].get('aktuell'):
        hel.append('En aktuell överlämning med oförändrade källor och filer saknas.')
    # Läs bara det befintliga designkontraktet. Ingen session eller nödingång.
    try:
        import skapande
        design,skal=skapande.godkand_giltig(d['slug'],Path(repo)/'underlag',Path(repo)/'kunder')
    except (OSError,ValueError,TypeError):design=None
    if not design:hel.append('Ett giltigt designgodkännande i byggflödet är inte observerat.')
    return {'forberedelse':{'kan_starta':not prep,'brister':prep,'innebord':'Kan lämnas till förberedelsen, inte ett kvalitetsgodkännande.'},
            'skiss':{'kan_starta':not skiss,'brister':skiss,'innebord':'Kan beredas för skiss; förberedelsens innehåll prövas före start.'},
            'helbygge':{'kan_starta':not hel,'brister':hel,'innebord':'Byggstarten gör dessutom sin egen aktuella kontroll.'},
            'publicering':{'kan_starta':False,'brister':['Rättigheter, leveransprov och separat publiceringsmandat prövas vid leverans.']}}


def detalj(repo,eid):
    db=lager(repo);d=db.internt(ks.nyckel(eid))
    return {'arende':d,'faser':faser(d,repo),'modellanrop':km.lista(db,eid),
            'retursvar':{k:{'svar_sha256':kf.svaridentitet(d,q),'klarlagd':kf.klarlagd(d,q)}
                        for k,q in d.get('returfragor',{}).items()},
            'drift':{'kundserver_aktiverad':None,'modell_aktiverad':None,
                     'text':'Denna vy startar ingen kundserver eller modell. Deras drift är inte observerad här; lokal separat server och uttrycklig modellkonfiguration krävs.'}}


def skapa(repo,data):
    ks.falt(data,('slug','namn','fiktiv','modellbudget','operation'),('slug','namn','fiktiv','modellbudget','operation'))
    db=lager(repo);eid,token=db.skapa(data['slug'],data['namn'],modellbudget=data['modellbudget'],fiktiv=data['fiktiv'],operation=data['operation'])
    return {'arende':eid,'nyckel':token,'aterforsok':token is None,
            'text':'Nyckeln visas endast nu. Ingen kundserver är startad.' if token else 'Ärendet skapades redan. Nyckeln sparas inte; skapa en ny personlig länk om första svaret försvann.'}


def handling(repo,eid,namn,data):
    if namn not in HANDLINGAR:raise ks.Vagrad('Ägarhandlingen är inte tillåten.')
    db=lager(repo);ks.nyckel(eid)
    if namn=='sakerhetskopia':
        ks.falt(data,());db.internt(eid);return kl.sakerhetskopiera(db)
    if namn=='overlamna':
        ks.falt(data,('revision','operation'),('revision','operation'))
        return kb.overlamna(db,eid,data['revision'],data['operation'],repo)
    if namn=='aterstall_overlamning':
        ks.falt(data,('operation',),('operation',))
        return kb.aterstall_overlamning(db,eid,data['operation'],repo)
    if namn=='erbjudande':
        ks.falt(data,('revision','text','villkor','ansvarig'),('revision','text','villkor','ansvarig'))
        return db.erbjudande(eid,data['revision'],data['text'],data['villkor'],data['ansvarig'])
    if namn=='deltagare':
        ks.falt(data,('revision','namn','roll','dagar'),('revision','namn','roll','dagar'))
        return kh.bjud_in(db,eid,data['revision'],data['namn'],data['roll'],data['dagar'])
    if namn=='aterkalla_person':
        ks.falt(data,('revision','person'),('revision','person'))
        return kh.aterkalla_person(db,eid,data['revision'],data['person'])
    if namn=='returfraga':
        ks.falt(data,('revision','overlamning','fraga'),('revision','overlamning','fraga'))
        return kf.returfraga(db,eid,data['revision'],data['overlamning'],data['fraga'])
    if namn=='bedom_retursvar':
        ks.falt(data,('revision','fraga','svar_sha256','bedomning','ansvarig'),('revision','fraga','svar_sha256','bedomning','ansvarig'))
        return kf.klarlagg_retursvar(db,eid,data['revision'],data['fraga'],data['svar_sha256'],data['bedomning'],data['ansvarig'])
    if namn=='lagringsbeslut':
        ks.falt(data,('revision','radera_efter','andamal','ansvarig'),('revision','radera_efter','andamal','ansvarig'))
        return kl.lagringsbeslut(db,eid,data['revision'],data['radera_efter'],data['andamal'],data['ansvarig'])
    if namn=='gallra':
        ks.falt(data,('revision',),('revision',));return kl.gallra(db,eid,data['revision'])
