#!/usr/bin/env python3
"""Ägarens befintliga dashboard till Kundstart; ingen kund-API eller modellstart."""
from pathlib import Path
import json
import kundstart as ks
import kundstart_beredning as kb
import kundstart_behorighet as kh
import kundstart_fortsatt as kf
import kundstart_integration as ki
import kundstart_lagring as kl
import kundstart_matt as km

HANDLINGAR=('overlamna','aterstall_overlamning','erbjudande','deltagare','aterkalla_person','returfraga','bedom_retursvar',
            'lagringsbeslut','gallra','sakerhetskopia','integrationsval','avmarkera_integration','intyga_handling','nyckelintag')


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
                 'fiktiv':d.get('fiktiv',True),
                 'foretag':next((a['text'] for a in d.get('anteckningar',[]) if a.get('slag')=='foretag'),None)} for d in rows if d['id'] not in sparrade],
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
    try:funktioner=ki.vy(d)  # katalogen och planen; läser bara
    except (OSError,ValueError,KeyError) as e:funktioner={'fel':'Integrationskatalogen kunde inte läsas: %s'%str(e)[:200]}
    import handlingsko,nyckelintag,aktivera
    try:ko=handlingsko.ko(d)  # "Detta behöver vi från kunden" ur planen; läser bara
    except (OSError,ValueError,KeyError) as e:ko={'fel':'Handlingskön kunde inte räknas fram: %s'%str(e)[:200]}
    try:intag=nyckelintag.status(d['slug'])  # bara att nycklarna finns, aldrig nycklarna
    except (OSError,ValueError) as e:intag={'fel':'Nyckelintaget kunde inte läsas: %s'%type(e).__name__}
    try:aktivering=aktivera.torr(d['slug'])  # torrkörningen: inga sidoeffekter, inget nät
    except (OSError,ValueError,KeyError) as e:aktivering={'fel':'Torrkörningen föll: %s'%str(e)[:200]}
    return {'arende':d,'faser':faser(d,repo),'modellanrop':km.lista(db,eid),'funktioner':funktioner,
            'handlingsko':ko,'nyckelintag':intag,'aktivering':aktivering,
            'retursvar':{k:{'svar_sha256':kf.svaridentitet(d,q),'klarlagd':kf.klarlagd(d,q)}
                        for k,q in d.get('returfragor',{}).items()},
            'drift':{'kundserver_aktiverad':None,'modell_aktiverad':None,
                     'text':'Denna vy startar ingen kundserver eller modell. Deras drift är inte observerad här; lokal separat server och uttrycklig modellkonfiguration krävs.'}}


def skapa(repo,data):
    ks.falt(data,('slug','namn','fiktiv','modellbudget','operation'),('slug','namn','fiktiv','modellbudget','operation'))
    db=lager(repo);eid,token=db.skapa(data['slug'],data['namn'],modellbudget=data['modellbudget'],fiktiv=data['fiktiv'],operation=data['operation'])
    return {'arende':eid,'nyckel':token,'aterforsok':token is None,
            'text':'Nyckeln visas endast nu. Ingen kundserver är startad.' if token else 'Ärendet skapades redan. Nyckeln sparas inte; skapa en ny personlig länk om första svaret försvann.'}


def anteckningar(repo,eid,operation,poster):
    # Ägarens anteckningar när kunden skapas ur portalen (dashboard/desktop.py): operatörens ord, aldrig kundens uppgifter
    # eller AI:s tolkning. Id:t härleds ur operationen, så att ett omförsök inte lägger till samma anteckning två gånger.
    import time
    db=lager(repo);ks.nyckel(eid)
    with db.trans() as c:
        d=db._doc(c,eid);fore={a['id'] for a in d.get('anteckningar',[])};nya=[]
        for slag,text in poster:
            if not text:continue
            aid=ks.sha([operation,slag])[:32]
            if aid in fore:continue
            nya.append({'id':aid,'slag':slag,'text':ks.text(text,2000),'kunskap':'agarens_anteckning','tid':time.time()})
        if nya:d.setdefault('anteckningar',[]).extend(nya);db._spara(c,d)
    return len(nya)


def _ko_om_ai(db,c,d):
    # Ett AI-jobb köas bara när ett finns att köra: ett fiktivt ärende med budget kvar (pilotens transport). Ett verkligt
    # ärende har ingen aktiverad AI-väg; svaret sparas och vyn säger det, i stället för en kö som aldrig töms.
    if d.get('fiktiv') is True and d['budget']['anrop']<d['budget']['max_anrop']:
        db._ko(c,d)
    else:
        d['modell']={'status':'avstangd','text':'Svaret är sparat. AI är inte aktiverad för det här ärendet: ett verkligt ärende kräver separat aktivering, och budgeten för ett testärende kan vara slut.'}


def intervju(repo,eid,namn,data):
    # Intervjun i portalen (dashboard/portal.js, kunskap/desktop.md): ägaren för samtalet med kunden.
    # svar: kundens ord som ägaren antecknar under samtalet; ett kundmeddelande märkt via ägaren, en kundkälla som AI:s
    # förslag får bindas till, och ett nytt AI-jobb köas som när kunden själv svarar (budget och transport gäller som förut).
    # rattelse: ägarens rättelse av en uppgift eller ett AI-antagande; blir en uppgift märkt agarens_rattelse (aldrig
    # kundens bekräftelse), och ett ersatt AI-förslag märks rattat. Samma operation ger samma svar; en annan revision än
    # den ägaren såg nekas (Konflikt), så att ett sent AI-svar aldrig skriver över en senare rättelse.
    import time
    if namn not in ('svar','rattelse'):raise ks.Vagrad('Okänd handling i intervjun.')
    ks.falt(data,('revision','operation','text','amne','forslag','uppgift'),('revision','operation','text'))
    if type(data['revision']) is not int:raise ks.Vagrad('En aktuell revision behövs.')
    db=lager(repo);ks.nyckel(eid);ks.nyckel(data['operation'])
    finger=ks.sha(['agare',namn,data])
    with db.trans() as c:
        fore=c.execute('SELECT begaran,svar FROM operationer WHERE arende=? AND id=?',(eid,data['operation'])).fetchone()
        if fore:
            if fore[0]!=finger:raise ks.Konflikt('Begärans id har redan använts för ett annat innehåll.')
            return json.loads(fore[1])
        d=db._doc(c,eid)
        if d['revision']!=data['revision']:raise ks.Konflikt('Ärendet har ändrats sedan du läste det. Läs om; din text är kvar.')
        t=ks.text(data['text'],ks.MAX_TEXT)
        if namn=='svar':
            if len(d['meddelanden'])>=500:raise ks.Vagrad('Ärendet behöver intern genomgång innan fler svar tas emot.')
            d['meddelanden'].append({'id':ks.id_(),'roll':'kund','person':'agaren','via':'agaren','text':t,'tid':time.time()})
            _ko_om_ai(db,c,d)
        else:
            amne=data.get('amne')
            if amne not in ks.AMNEN:raise ks.Vagrad('Välj vilket ämne rättelsen gäller.')
            fid,uid=data.get('forslag'),data.get('uppgift')
            if fid is not None and fid not in d['forslag']:raise ks.Vagrad('AI-förslaget finns inte längre.')
            if uid is not None and uid not in d['uppgifter']:raise ks.Vagrad('Uppgiften finns inte längre.')
            kid=uid or ks.id_()
            if uid:d['historik'].append({'slag':'ersatt_uppgift','uppgift':d['uppgifter'][uid],'tid':time.time(),'av':'agaren'})
            d['uppgifter'][kid]={'id':kid,'amne':amne,'text':t,'kunskap':'agarens_rattelse','bestallning':'onskemal','person':'agaren',
                                 'kalla':ks.id_(),'tid':time.time(),'motsagelse':False,**({'ersatter_forslag':fid} if fid else {})}
            if fid:d['forslag'][fid]['bestallning']='rattat'
            _ko_om_ai(db,c,d)
        db._spara(c,d)
        svar={'revision':d['revision'],'modell':d['modell'],'ai':{'fiktiv':d.get('fiktiv') is True,'budget':d['budget']}}
        c.execute('INSERT INTO operationer VALUES(?,?,?,?)',(eid,data['operation'],finger,ks.jsontext(svar)))
        return svar


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
    if namn=='integrationsval':
        ks.falt(data,('revision','val'),('revision','val'))
        return ki.valj(db,eid,data['revision'],data['val'])
    if namn=='avmarkera_integration':
        ks.falt(data,('revision','val'),('revision','val'))
        return ki.avmarkera(db,eid,data['revision'],data['val'])
    if namn=='intyga_handling':
        import handlingsko
        ks.falt(data,('revision','post','referens'),('revision','post','referens'))
        return handlingsko.intyga(db,eid,data['revision'],{'post':data['post'],'referens':data['referens']})
    if namn=='nyckelintag':
        import handlingsko
        return {'nyckelintag':handlingsko.lamna_nyckel(db,eid,data,'dashboard')}
    if namn=='gallra':
        ks.falt(data,('revision',),('revision',));return kl.gallra(db,eid,data['revision'])
