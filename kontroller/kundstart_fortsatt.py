#!/usr/bin/env python3
"""Byggflödets returfrågor och separata integrationsbelägg i samma kundärende.

De interna funktionerna exponeras aldrig av kundservern. Underlag, kontostöd och
genomfört prov får egna statusar. Ingen nätanslutning eller modell startas här.
"""
import datetime
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import kundstart as ks

FASER=('forberedelse','skiss','helbygge','publicering','forvaltning')


def returfraga(lager,eid,revision,overlamning,q):
    ks.falt(q,('id','amne','text','varfor','fas','kritisk','ansvarig'),('id','amne','text','varfor','fas','kritisk','ansvarig'))
    ks.nyckel(q['id']);ks.nyckel(overlamning)
    if q['amne'] not in ks.AMNEN or q['fas'] not in FASER or type(q['kritisk']) is not bool:
        raise ks.Vagrad('Returfrågan behöver ämne, påverkad fas och kritikalitet.')
    for n in ('text','varfor','ansvarig'):ks.text(q[n],3000)
    with lager.trans() as c:
        d=lager._doc(c,eid)
        row=c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?',(eid,overlamning)).fetchone()
        if not row:raise ks.Vagrad('Returfrågans överlämning hör inte till ärendet.')
        p=json.loads(row[0])
        if p['status']!='klar':raise ks.Vagrad('Returfrågan behöver en färdig överlämning som källa.')
        finger=ks.sha([q,overlamning,revision])
        tidigare=d.setdefault('returfragor',{}).get(q['id'])
        if tidigare:
            if tidigare['begaran']!=finger:raise ks.Konflikt('Frågans id har redan använts för annat innehåll.')
            return tidigare
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades innan kompletteringen bokfördes.')
        rad={**q,'begaran':finger,'status':'oppen','svar':[], 'tid':time.time(),
             'overlamning':overlamning,'kallrevision':p['revision'],'arenderevision':revision}
        d['returfragor'][q['id']]=rad;lager._spara(c,d)
        return rad


def svara(lager,c,d,person,data):
    ks.falt(data,('id','text','lage'),('id','text','lage'))
    q=d.get('returfragor',{}).get(ks.nyckel(data['id']))
    if not q or data['lage'] not in ('svarad','vet_inte','avstar','framtida'):
        raise ks.Vagrad('Kompletteringsfrågan eller svarsläget saknas.')
    if len(d['meddelanden'])>=500:raise ks.Vagrad('Ärendet behöver intern genomgång innan fler svar tas emot.')
    text=ks.text(data['text']);mid=ks.id_()
    q['status']=data['lage'];q['svar'].append({'kalla':mid,'person':person,'lage':data['lage'],'revision':d['revision']+1})
    d['meddelanden'].append({'id':mid,'roll':'kund','person':person,'text':text,'tid':time.time(),
                             'fraga':q['id'],'svarslage':data['lage']})
    lager._ko(c,d)


def svaridentitet(d,q):
    ids={x['kalla'] for x in q['svar']}
    return ks.sha({'lage':q['status'],'svar':q['svar'],
                   'kallor':[m for m in d['meddelanden'] if m['id'] in ids]})


def klarlagg_retursvar(lager,eid,revision,qid,svar_sha,bedomning,ansvarig):
    """Intern beredning av ett faktiskt svar; aldrig kundens kvittensknapp."""
    ks.nyckel(qid);ks.text(bedomning,3000);ks.text(ansvarig,120)
    with lager.trans() as c:
        d=lager._doc(c,eid);q=d.get('returfragor',{}).get(qid)
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades före svarsbedömningen.')
        if not q or not q['svar'] or svaridentitet(d,q)!=svar_sha:raise ks.Vagrad('Den bedömda svarsversionen saknas.')
        if q.get('klarlaggande'):d['historik'].append({'slag':'tidigare_svarsbedomning','fraga':qid,'bedomning':q['klarlaggande']})
        q['klarlaggande']={'svar_sha256':svar_sha,'bedomning':bedomning,'ansvarig':ansvarig,'tid':time.time()}
        lager._spara(c,d);return lager._vy(c,d)


def klarlagd(d,q):
    return bool(q['svar'] and q.get('klarlaggande',{}).get('svar_sha256')==svaridentitet(d,q))


def behov(d,person,data):
    namn=('id','behov','uppgift','befintligt','ansvarig','dataflode','aterkoppling','lage')
    ks.falt(data,namn,('id','behov','lage'));ks.nyckel(data['id'])
    if data['lage'] not in ('onskemal','kundval','avstatt','framtida','okant','inte_relevant'):
        raise ks.Vagrad('Integrationsbehovets beställningsläge är ogiltigt.')
    data=dict(data)
    for n in namn:
        if n not in ('id','lage'):
            if n=='behov' or data.get(n) is not None:ks.text(data.get(n),3000)
            else:data[n]=None  # uteblivet kundsvar är okänt, aldrig ett standardpåstående
    integrations=d.setdefault('integrationer',{})
    fore=integrations.get(data['id']);finger=ks.sha(data)
    if fore and fore['behov_sha256']==finger:return
    if fore:d['historik'].append({'slag':'ersatt_integrationsbehov','uppgift':fore,'tid':time.time()})
    u=dict(fore['utredning'],status='inaktuell') if fore else {
        'status':'inte_utrett','leverantor':{'status':'okant'},'konto':{'status':'okant'},'prov':{'status':'inte_provat'}}
    integrations[data['id']]={**data,'bestallning':data['lage'],'kunskap':'kunden_uppger','person':person,
        'kallstatus':{n:'kunden_uppger' if data[n] is not None else 'okant' for n in namn if n not in ('id','lage')},
        'kalla':ks.id_(),'behov_sha256':finger,'revision':d['revision']+1,'utredning':u}


def kalla(b):
    ks.falt(b,('status','kalla','datum','sha256','besked'),('status',))
    if b['status'] not in ('okant','dokumenterat','saknas'):raise ks.Vagrad('Okänt dokumentationsläge.')
    if b['status']=='okant':return {'status':'okant'}
    if set(b)!=set(('status','kalla','datum','sha256','besked')):raise ks.Vagrad('Ett dokumentationsbesked behöver daterad källa och innehållshash.')
    u=urlsplit(ks.text(b['kalla'],2000))
    if u.scheme not in ('https','http') or not u.hostname or u.username or u.password:
        raise ks.Vagrad('Dokumentationskällan behöver en webbadress utan åtkomstuppgifter.')
    try:datetime.date.fromisoformat(b['datum'])
    except (ValueError,TypeError):raise ks.Vagrad('Källdatum saknas.') from None
    if not isinstance(b['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',b['sha256']):raise ks.Vagrad('Källans innehållshash saknas.')
    ks.text(b['besked'],3000)
    return b


def belagg(lager,eid,b,slag):
    tillatna={'konto':('okant','tillgang_bekraftad','saknas'),
              'prov':('inte_provat','lokalt_provat','skarpt_provat','underkant')}[slag]
    ks.falt(b,('status','fil','sha256','besked'),('status',))
    if b['status'] not in tillatna:raise ks.Vagrad('Okänt beläggsläge.')
    if b['status'] in ('okant','inte_provat'):
        if set(b)!={'status'}:raise ks.Vagrad('Ett oprövat besked får inga utförandebelägg.')
        return b
    if set(b)!=set(('status','fil','sha256','besked')):raise ks.Vagrad('Kontrollens bevis och innehållshash saknas.')
    p=Path(ks.text(b['fil'],1000));bas=lager.rot/'bevis'/eid
    if p.is_absolute() or '..' in p.parts:raise ks.Vagrad('Beviset ska ligga i ärendets privata bevisområde.')
    f=bas/p
    if any(x.is_symlink() for x in (f,*f.parents)) or not f.is_file() or f.stat().st_size>2_000_000:
        raise ks.Vagrad('Belägget saknas eller är inte en tillåten vanlig fil.')
    if ks.sha(f.read_bytes())!=b['sha256']:raise ks.Vagrad('Belägget stämmer inte med den angivna versionen.')
    ks.text(b['besked'],3000)
    return b


def utred_integration(lager,eid,revision,kid,behov_sha,b):
    ks.nyckel(kid);ks.falt(b,('leverantor','konto','prov','vag','villkor'),('leverantor','konto','prov','vag','villkor'))
    if b['vag'] not in ('utreds','lank','inbaddning','inbyggd','api'):raise ks.Vagrad('Okänd integrationsväg.')
    ks.text(b['villkor'],5000)
    verifierad={**b,'leverantor':kalla(b['leverantor']),'konto':belagg(lager,eid,b['konto'],'konto'),
                'prov':belagg(lager,eid,b['prov'],'prov'),'status':'utredd','tid':time.time(),'behov_sha256':behov_sha}
    with lager.trans() as c:
        d=lager._doc(c,eid);i=d.get('integrationer',{}).get(kid)
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet har ändrats.')
        if not i or i['behov_sha256']!=behov_sha:raise ks.Konflikt('Integrationsbehovet har ändrats.')
        d['historik'].append({'slag':'tidigare_integrationsutredning','id':kid,'utredning':i['utredning']})
        i['utredning']=verifierad;lager._spara(c,d)
        return lager._vy(c,d)


def integration_klar(i):
    """Fullständiga bokförda belägg, aldrig ett självständigt publiceringsbeslut."""
    u=i['utredning']
    return bool(u.get('status')=='utredd' and u.get('vag') in ('lank','inbaddning','inbyggd','api') and u.get('behov_sha256')==i['behov_sha256']
                and u['leverantor']['status']=='dokumenterat' and u['konto']['status']=='tillgang_bekraftad'
                and u['prov']['status']=='skarpt_provat')
