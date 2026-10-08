#!/usr/bin/env python3
"""Kundstart till befintliga underlagsformat, utan påhittad research eller start av bygge.

Modellen får föreslå en struktur. Kunden måste stämma av den genom en egen
revisionsbunden handling. Ändrade kundsvar gör avstämningen inaktuell.
"""
import json
import contextlib
import fcntl
import os
import re
import stat
from pathlib import Path, PurePosixPath
import uuid
import kundstart as ks
import verksamhetsuppgifter


def grund(d):
    return ks.sha({'meddelanden':[m for m in d['meddelanden'] if m['roll']=='kund'], 'uppgifter':d['uppgifter'],
                   'integrationer':{k:{n:v for n,v in i.items() if n!='utredning'}
                                    for k,i in d.get('integrationer',{}).items()}})


def forslag(d, p):
    ks.falt(p,('varden','kallor'),('varden','kallor'))
    v,k=p['varden'],p['kallor']
    if not isinstance(v,dict) or {'schema','fiktiv'} & set(v) or not isinstance(k,dict) or set(k)!=set(v):
        raise ks.Vagrad('Verksamhetsförslaget behöver egna källor för varje uppgift; systemfält får inte skrivas.')
    kallor=ks.kundkallor(d)
    if any(not isinstance(ids,list) or not ids or any(not isinstance(i,str) or i not in kallor for i in ids) for ids in k.values()):
        raise ks.Vagrad('Verksamhetsförslaget saknar befintliga kundkällor.')
    values={'schema':1,'fiktiv':d.get('fiktiv',True),**v}
    try:varningar=verksamhetsuppgifter.validera(values)
    except (verksamhetsuppgifter.Vagrad,TypeError,ValueError,KeyError):
        raise ks.Vagrad('Grunduppgifterna kan ännu inte läsas av byggflödet. Fråga om de saknade uppgifterna.') from None
    ks.text(ks.jsontext(values))
    ut={'varden':values,'kallor':k,'kundgrund':grund(d),'kunskap':'tolkning','varningar':varningar}
    ut['sha256']=ks.sha(ut)
    return ut


def paket(d):
    """Härled ett komplett textpaket; skriver ingenting och antar inget designgodkännande."""
    v=d.get('verksamhet')
    if not isinstance(v,dict) or v.get('kunskap')!='kunden_bekraftar' or v.get('kundgrund')!=grund(d):
        raise ks.Vagrad('Aktuella verksamhetsuppgifter behöver stämmas av innan de lämnas till byggflödet.')
    try:verksamhetsuppgifter.validera(v['varden'])
    except (verksamhetsuppgifter.Vagrad,TypeError,ValueError,KeyError):
        raise ks.Vagrad('Verksamhetsuppgifterna kunde inte valideras.') from None
    current=ks.vy(d)
    snapshot={k:current[k] for k in ('id','slug','revision','uppgifter','forslag','fragor','material','bestallning')}
    snapshot.update({k:current.get(k,{}) for k in ('returfragor','integrationer')})
    snapshot.update(schema=1,status='klar',arenderevision=d['revision'],verksamhet=v,
                    omfattning_sha256=ks.omfattning(d),kundgrund=grund(d),helbygge_tillatet=False,
                    innebord='Underlag för förberedelse och skiss. Helbygge kräver separat giltigt designgodkännande.',
                    kallor=[m for m in d['meddelanden'] if m['roll']=='kund'])
    ut={'VERKSAMHET.json':ks.jsontext(v['varden'])+'\n'}
    if current['bestallning']['status']=='accepterad' and current['bestallning']['aktuell']:
        offer=next((e for e in d['erbjudanden'] if e['id']==current['bestallning'].get('erbjudande')),None)
        if not offer:raise ks.Vagrad('Det accepterade erbjudandet saknas.')
        ut['UPPDRAG.md']='\n'.join(['# Accepterat kunduppdrag','',
            'Källa: Kundstart %s, revision %d. Omfattning: %s.'%(d['id'],d['revision'],ks.omfattning(d)),
            '',offer['text'],'','## Villkor','',offer['villkor'],'',
            'Källstatus, avstådda/framtida önskemål och öppna frågor finns i KUNDSTART.json.',
            'Detta är inte ett designgodkännande eller publiceringsmandat.',''])
    snapshot['filer']={n:ks.sha(t.encode()) for n,t in ut.items()}
    ut['KUNDSTART.json']=ks.jsontext(snapshot)+'\n'
    return ut


def indata(d):
    data={k:d.get(k) for k in ('id','slug','uppgifter','forslag','fragor','material','verksamhet','returfragor','integrationer')}
    # Den härledda vyn får inte ändra källans identitet.
    data['bestallning']={k:v for k,v in d['bestallning'].items() if k!='aktuell'}
    return ks.sha(data|{'kundgrund':grund(d)})


def kvittovy(p,d):
    return {k:p[k] for k in ('id','revision','status','filer')}|{'aktuell':post_aktuell(p,d)}


def post_aktuell(p,d,u=None):
    try:
        if not isinstance(p,dict) or not isinstance(d,dict):return False
        filer=p.get('filer')
        if not isinstance(filer,dict) or not {'KUNDSTART.json','VERKSAMHET.json'} <= set(filer):return False
        for n,h in filer.items():
            if not isinstance(n,str) or not n or '\\' in n:return False
            vag=PurePosixPath(n)
            if vag.is_absolute() or '..' in vag.parts or str(vag)!=n:return False
            if not isinstance(h,str) or not re.fullmatch(r'[0-9a-f]{64}',h):return False
        repo=Path(p['repo']);mal=repo/'underlag'/d['slug']
        if not repo.is_absolute() or (u is not None and Path(u).absolute()!=mal):return False
        snapshot=json.loads(saker(mal/'KUNDSTART.json',repo).read_text())
        if not isinstance(snapshot,dict) or snapshot.get('filer')!={n:h for n,h in filer.items() if n!='KUNDSTART.json'}:return False
        if any(snapshot.get(n)!=v for n,v in {'id':d['id'],'slug':d['slug'],'status':'klar',
                'overlamning':p['id'],'indata_sha256':p['indata']}.items()):return False
        return bool(p['status']=='klar' and p['indata']==indata(d)
                    and all(filhash(saker(mal/n,repo))==h for n,h in filer.items()))
    except (OSError,ValueError,KeyError,TypeError,ks.Vagrad):return False


def saker(p,bas):
    p,bas=Path(p),Path(bas)
    try:p.relative_to(bas)
    except ValueError:raise ks.Vagrad('Överlämningens mål ligger utanför repot.') from None
    for x in (p,*p.parents):
        if x.is_symlink():raise ks.Vagrad('Överlämningen får inte gå genom en symbolisk länk.')
    return p


def atomiskt(p,b):
    tmp=p.with_name('.kundstart-'+uuid.uuid4().hex+'.tmp')
    try:
        with tmp.open('xb') as f:
            os.chmod(tmp,0o600);f.write(b);f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:tmp.unlink(missing_ok=True)


def filhash(p):
    if not p.exists():return None
    if not p.is_file() or p.is_symlink():raise ks.Vagrad('Överlämningens mål är ingen vanlig fil.')
    return ks.sha(p.read_bytes())


@contextlib.contextmanager
def arbetslas(u,repo):
    """Samma startlås som ateljén. Pågående bygge eller designarbete får inte hotpatchas."""
    fds=[]
    try:
        globalt=repo/'kunder/.bygge.las'
        saker(globalt.parent,repo).mkdir(exist_ok=True)
        saker(globalt,repo);fd=os.open(globalt,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fds.append(fd)
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ks.Vagrad('Bygglåset är ingen vanlig fil.')
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Äldre byggversioner tog inte flock. Utan processvaktens identitetsprov
        # kan deras PID-fil inte säkert tolkas som inaktiv.
        if (repo/'kunder/.bygge-pid').exists() or (repo/'kunder/.bygge-pid').is_symlink():
            raise ks.Vagrad('Ett äldre byggbesked behöver kontrolleras innan underlaget kan ändras.')
        fd=os.open(u/'.atelje-start.las',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600);fds.append(fd)
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        st=saker(u/'atelje/STATUS.json',repo)
        if st.exists():
            import korregister
            obj=json.loads(st.read_text())
            if obj.get('pid') and korregister.lever(obj['pid']):raise ks.Vagrad('Designarbetet pågår; underlaget ändras inte mitt i försöket.')
        yield
    except BlockingIOError:raise ks.Vagrad('Ett arbete pågår. Överlämningen får återupptas senare.') from None
    finally:
        for fd in reversed(fds):os.close(fd)


def overlamna(lager,eid,revision,op,repo=None):
    kvitto=_overlamna(lager,eid,revision,op,repo)
    from kirurg_signaler import efter_overlamning
    observation=efter_overlamning(lager,eid,Path(repo or ks.ROOT).absolute(),kvitto['id'])
    return kvitto|{'kirurg':observation}


def _overlamna(lager,eid,revision,op,repo=None):
    """Intern ägarhandling. Inget bygge startas och inga kundfiler går till Git.

    Reservationen skrivs beständigt före första filbytet. Klar skrivs sist, efter
    alla innehållshashar; samma op-id återupptar en avbruten publicering. Den
    ursprungliga versionen ligger kvar i ärendets revisionshistorik.
    """
    ks.nyckel(op)
    if type(revision) is not int:raise ks.Vagrad('En ärenderevision krävs.')
    repo=Path(repo or ks.ROOT).absolute()
    d=lager.internt(eid);u=saker(repo/'underlag'/d['slug'],repo)
    saker(repo/'underlag',repo).mkdir(exist_ok=True)
    u.mkdir(exist_ok=True,mode=0o700)
    with arbetslas(u,repo),lager.trans() as c:
        d=lager._doc(c,eid)
        row=c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?',(eid,op)).fetchone()
        if row:
            p=json.loads(row[0])
            if p['revision']!=revision or p['repo']!=str(repo):raise ks.Konflikt('Överlämnings-id hör till en annan begäran.')
            if p['status']=='klar':return kvittovy(p,d)
            if p['status']!='publicerar':raise ks.Vagrad('Överlämningen är avslutad utan publicering.')
            if p['indata']!=indata(d):raise ks.Konflikt('Ärendet ändrades under den avbrutna överlämningen; återställ den innan en ny beställs.')
        else:
            if d['revision']!=revision:raise ks.Konflikt('Ärendet har ändrats före överlämningen.')
            fore=c.execute('SELECT post FROM overlamningar WHERE arende=? ORDER BY rowid DESC LIMIT 1',(eid,)).fetchone()
            fore=json.loads(fore[0]) if fore else None
            if fore and fore['status']=='publicerar':raise ks.Vagrad('Återuppta eller återställ den tidigare ofullständiga överlämningen först.')
            if not fore and any(x.name!='.atelje-start.las' for x in u.iterdir()):
                raise ks.Vagrad('Sluggens underlag finns redan utan detta ärendes överlämning; ingen överskrivning görs.')
            tidigare=(fore['filer'] if fore['status']=='klar' else fore['tidigare']) if fore else {}
            for n,h in tidigare.items():
                if filhash(saker(u/n,repo))!=h:raise ks.Vagrad('Tidigare överlämnade filer har ändrats. De skrivs inte över.')
            texter=paket(d);body=json.loads(texter['KUNDSTART.json'])
            material={}
            for m in d['material']:
                b=c.execute('SELECT data FROM bilagor WHERE arende=? AND id=?',(eid,m['id'])).fetchone()
                if not b or ks.sha(b[0])!=m['sha256']:raise ks.Vagrad('Material saknas eller har ändrats.')
                material['kundstart/material/%s/%s'%(m['id'],m['namn'])]={'id':m['id'],'sha256':m['sha256']}
            body['filer'].update({n:m['sha256'] for n,m in material.items()})
            body.update(overlamning=op,indata_sha256=indata(d))
            texter['KUNDSTART.json']=ks.jsontext(body)+'\n'
            filer={n:ks.sha(t.encode()) for n,t in texter.items()}|{n:m['sha256'] for n,m in material.items()}
            p={'id':op,'revision':revision,'status':'publicerar','indata':indata(d),'filer':filer,
               'repo':str(repo),'tidigare':tidigare,'texter':texter,'material':material}
            # Commit av reservationen är avsiktlig. Processdöd under filbyten ska gå att återuppta.
            c.execute('INSERT INTO overlamningar VALUES(?,?,?,?,?)',(eid,op,revision,p['indata'],ks.jsontext(p)))
            c.commit();c.execute('BEGIN IMMEDIATE')
            d=lager._doc(c,eid)
            if p['indata']!=indata(d):raise ks.Konflikt('Ärendet ändrades medan överlämningen reserverades.')
        body=json.loads(p['texter']['KUNDSTART.json']);marker=ks.jsontext(dict(body,status='publicerar'))+'\n'
        arkiv=saker(u/'kundstart/overlamningar'/op,repo);arkiv.mkdir(parents=True,exist_ok=True,mode=0o700)
        # Tillåt bara föregående eller våra egna bytes när en publicering återupptas.
        for n in set(p['tidigare'])|set(p['filer']):
            f=saker(u/n,repo);h=filhash(f)
            tillatna={None,p['tidigare'].get(n),p['filer'].get(n)}
            if n=='KUNDSTART.json':tillatna.add(ks.sha(marker.encode()))
            if h not in tillatna:raise ks.Vagrad('En fil ändrades utanför överlämningen. Den skrivs inte över.')
            if n in ('KUNDSTART.json','VERKSAMHET.json','UPPDRAG.md') and h and h==p['tidigare'].get(n):
                backup=saker(arkiv/('fore-'+n),repo)
                if not backup.exists():atomiskt(backup,f.read_bytes())
                if filhash(backup)!=h:raise ks.Vagrad('Föregående underlag kunde inte bevaras.')
        atomiskt(saker(u/'KUNDSTART.json',repo),marker.encode())
        for n,m in p['material'].items():
            f=saker(u/n,repo);f.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            b=c.execute('SELECT data FROM bilagor WHERE arende=? AND id=?',(eid,m['id'])).fetchone()
            if not b or ks.sha(b[0])!=m['sha256']:raise ks.Vagrad('Materialet kunde inte läsas.')
            if filhash(f)!=m['sha256']:atomiskt(f,b[0])
        for n,t in p['texter'].items():
            if n!='KUNDSTART.json':atomiskt(saker(u/n,repo),t.encode())
        if 'UPPDRAG.md' in p['tidigare'] and 'UPPDRAG.md' not in p['filer']:
            saker(u/'UPPDRAG.md',repo).unlink(missing_ok=True)
        for n,h in p['filer'].items():
            if n!='KUNDSTART.json' and filhash(saker(u/n,repo))!=h:raise ks.Vagrad('Överlämningen är ofullständig.')
        atomiskt(saker(u/'KUNDSTART.json',repo),p['texter']['KUNDSTART.json'].encode())
        p['status']='klar'
        c.execute('UPDATE overlamningar SET post=? WHERE arende=? AND id=?',(ks.jsontext(p),eid,op))
        return kvittovy(p,d)


def aterstall_overlamning(lager,eid,op,repo=None):
    """Avsluta en avbruten publicering och återställ enbart dess egna filbyten.

    Alla berörda bytes och bevarade föreversioner prövas innan första ändringen.
    Ett främmande filbyte lämnas orört och gör att ägaren måste utreda det.
    Arkiv och ärendehistorik bevaras; samma handling kan återförsökas efter avbrott.
    """
    ks.nyckel(op);repo=Path(repo or ks.ROOT).absolute();d=lager.internt(eid)
    u=saker(repo/'underlag'/d['slug'],repo)
    with arbetslas(u,repo),lager.trans() as c:
        d=lager._doc(c,eid)
        row=c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?',(eid,op)).fetchone()
        if not row:raise ks.Vagrad('Överlämningen finns inte.')
        p=json.loads(row[0])
        if p['repo']!=str(repo):raise ks.Vagrad('Överlämningen hör till ett annat repo.')
        if p['status']=='avbruten':return kvittovy(p,d)
        if p['status']!='publicerar':raise ks.Vagrad('Bara en ofullständig överlämning får återställas.')
        body=json.loads(p['texter']['KUNDSTART.json'])
        marker=ks.sha((ks.jsontext(dict(body,status='publicerar'))+'\n').encode())
        steg=[]
        for n in sorted(set(p['tidigare'])|set(p['filer']),key=lambda n:(n=='KUNDSTART.json',n)):
            f=saker(u/n,repo);h=filhash(f);fore=p['tidigare'].get(n)
            if h not in {None,fore,p['filer'].get(n),marker if n=='KUNDSTART.json' else None}:
                raise ks.Vagrad('En fil ändrades utanför överlämningen. Återställningen lämnar den orörd.')
            if h==fore:continue
            if fore:
                backup=saker(u/'kundstart/overlamningar'/op/('fore-'+n),repo)
                if filhash(backup)!=fore:raise ks.Vagrad('Föreversionen saknas; inget återställs.')
                steg.append((f,backup.read_bytes()))
            else:steg.append((f,None))
        for f,b in steg:
            if b is None:f.unlink(missing_ok=True)
            else:atomiskt(f,b)
        p['status']='avbruten'
        c.execute('UPDATE overlamningar SET post=? WHERE arende=? AND id=?',(ks.jsontext(p),eid,op))
        return kvittovy(p,d)


def aktuell(lager,u):
    """Läsande kontroll av källärende och alla deklarerade filer, inte bara en klar-flagga."""
    try:
        u=Path(u);repo=u.parent.parent
        body=json.loads(saker(u/'KUNDSTART.json',repo).read_text())
        if body['status']!='klar':return False
        with lager.trans() as c:
            d=lager._doc(c,body['id'])
            p=c.execute('SELECT post FROM overlamningar WHERE arende=? AND id=?',(body['id'],body['overlamning'])).fetchone()
            if not p:return False
            p=json.loads(p[0])
            return post_aktuell(p,d,u)
    except (OSError,ValueError,KeyError,TypeError,ks.Vagrad):return False
