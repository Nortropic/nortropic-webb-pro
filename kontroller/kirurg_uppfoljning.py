#!/usr/bin/env python3
"""Observera ett separat granskat Git-införande och dess rapporterade eftereffekt.

Ändrar aldrig aktiv kod, Git, mandat eller granskningsbesked. Lokala operatören
förser registreringen med ett avgränsat mandat och separat granskningskvitto.
Dessa är betrodda lokala filer, inte kryptografiskt verifierade personidentiteter.
Ingen modell- eller HTTP-ingång erbjuds. Drift och nyttan härleds aldrig ur Git.
"""
import hashlib
import json
import math
import os
import stat
from pathlib import Path
import re
import time
import kirurg_loop as kl
import kirurg_forsok as kf


def las(p,rot):
    p=kl.fil(p,rot)
    try:
        if not p.is_file() or p.stat().st_size>500000:raise ValueError()
        data=p.read_bytes();v=json.loads(data)
        if not isinstance(v,dict):raise ValueError()
        return v,hashlib.sha256(data).hexdigest()
    except (OSError,ValueError,TypeError):raise kl.Vagrad('Införandets underlag kunde inte läsas; inget registreras.') from None


def mandat(loop,mid):
    kl.nyckel(mid)
    data,h=las(loop.rot.parent/'AGARMANDAT.json',loop.rot.parent)
    try:
        m=data['mandat'][mid]
        if data.get('schema')!=1 or m['klass']!='observera_gitinförande':raise ValueError()
        if type(m['giltig_till']) not in (int,float) or not math.isfinite(m['giltig_till']) or m['giltig_till']<=time.time():raise ValueError()
        if type(m['max_registreringar']) is not int or not 1<=m['max_registreringar']<=100:raise ValueError()
        if not isinstance(m['gren'],str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9/_-]{0,100}',m['gren']):raise ValueError()
        if not isinstance(m['filer'],list) or not 1<=len(m['filer'])<=10:raise ValueError()
        for n in m['filer']:
            kf.vag(n)
            if n.startswith(kf.SKYDDAT):raise ValueError()
        if not isinstance(m['granskare'],list) or not m['granskare']:raise ValueError()
        for n in m['granskare']:kl.nyckel(n)
        kl.text(m['ansvarig'],120)
        return dict(m,id=mid,fil_sha256=h)
    except (ValueError,KeyError,TypeError):raise kl.Vagrad('Giltigt mandat för införandeobservation saknas.') from None


def repoidentitet(root,version,gren):
    root=Path(root).resolve()
    if not isinstance(version,str) or not re.fullmatch('[a-f0-9]{40}',version):raise kl.Vagrad('Exakt Git-version krävs.')
    if Path(os.fsdecode(kf.git(root,'rev-parse','--show-toplevel')).strip()).resolve()!=root:raise kl.Vagrad('Git-roten är inte den begärda.')
    if kf.git(root,'rev-parse','HEAD').decode().strip()!=version:raise kl.Vagrad('Git-versionen är inte den begärda.')
    if kf.git(root,'symbolic-ref','--short','HEAD').decode().strip()!=gren:raise kl.Vagrad('Annan gren än mandatets.')
    if kf.git(root,'status','--porcelain','--untracked-files=no').strip():raise kl.Vagrad('Spårade filer eller index är ändrade.')
    # Status räcker inte: assume-unchanged och skip-worktree döljer arbetsfiler.
    try:
        for post in kf.git(root,'ls-tree','-rz','--full-tree',version).split(b'\0'):
            if not post:continue
            huvud,namn=post.split(b'\t',1);mode,typ,oid=huvud.split()
            if mode not in (b'100644',b'100755') or typ!=b'blob':raise kl.Vagrad('Spårade länkar och specialfiler stöds inte av observationen.')
            f=kl.fil(root/os.fsdecode(namn),root)
            if not stat.S_ISREG(f.lstat().st_mode):raise kl.Vagrad('En spårad fil är inte en vanlig fil.')
            b=f.read_bytes();objekt=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
            if objekt!=oid.decode() or bool(f.stat().st_mode & stat.S_IXUSR)!=(mode==b'100755'):raise kl.Vagrad('En spårad arbetsfil skiljer sig från Git-versionen.')
    except (OSError,ValueError):raise kl.Vagrad('Arbetskopians samtliga spårade filer kunde inte verifieras.') from None
    return kf.git(root,'rev-parse','HEAD^{tree}').decode().strip()


def patch(loop,x):
    a,_=las(loop.rot/'forsok'/x['id']/'ANDRINGAR.json',loop.rot)
    if kl.hash_(a)!=x['andringar'] or not a:raise kl.Vagrad('Ändringen stämmer inte med det låsta försöket.')
    for n,v in a.items():
        kf.vag(n)
        if n.startswith(kf.SKYDDAT) or not isinstance(v,dict) or set(v)!= {'fore','text'} or not isinstance(v['text'],str):raise kl.Vagrad('Ogiltigt ändringsunderlag.')
    return a


def filversion(root,version,n):
    """Bind både Git-objektet och arbetsfilen; indexflaggor får inte gömma ändringar."""
    data=kf.git(root,'ls-tree','-z',version,'--',n)
    if not data:return None
    poster=data.split(b'\0');poster=[p for p in poster if p]
    if len(poster)!=1:raise kl.Vagrad('Filversionen är inte entydig.')
    huvud,namn=poster[0].split(b'\t',1)
    mode,typ,oid=huvud.split()
    if namn.decode()!=n or mode not in (b'100644',b'100755') or typ!=b'blob':raise kl.Vagrad('Införandefilen är inte en vanlig fil.')
    b=kf.git(root,'cat-file','blob',oid.decode());f=kl.fil(Path(root)/n,root)
    if not f.is_file() or f.read_bytes()!=b:raise kl.Vagrad('Arbetsfilen skiljer sig från den registrerade Git-versionen.')
    return hashlib.sha256(b).hexdigest()


def registrera(loop,root,pid,revision,forsok,mid,granskning,version):
    root=Path(root).resolve();kl.nyckel(forsok);kl.nyckel(granskning)
    with kf.ensam(loop),loop.trans() as d:
        p=loop._post(d,pid,revision);m=mandat(loop,mid)
        if d['paus']:raise kl.Vagrad('Införandeobservationerna är pausade.')
        x=d['forsok'].get(forsok)
        if not x or x['post']!=pid or x['status']!='klart' or x['utfall']!='regression_rattad':raise kl.Vagrad('Ett slutfört lyckat regressionsförsök krävs.')
        if kl.hash_(p['signaler'])!=x['signaler'] or not p['planer'] or p['planer'][-1]!=x['plan'] or kl.hash_(p['diagnoser'][-1])!=x['plan']['diagnos']:raise kl.Vagrad('Nytt underlag kräver nytt försök.')
        a=patch(loop,x)
        if set(a)-set(m['filer']):raise kl.Vagrad('Ändringen ligger utanför mandatets filer.')
        data,gh=las(loop.rot.parent/'GRANSKNINGAR.json',loop.rot.parent)
        try:
            g=data['granskningar'][granskning]
            if (data.get('schema')!=1 or g['forsok']!=forsok or g['version']!=version or g['andringar']!=x['andringar']
                or g['plan']!=x['plan']['sha256'] or g['utfall']!='godkand' or g['granskare'] not in m['granskare']
                or g['skapare']==g['granskare'] or type(g['tid']) not in (int,float) or not math.isfinite(g['tid'])
                or not x['slut']<=g['tid']<=time.time()):raise ValueError()
            kl.nyckel(g['skapare']);kl.nyckel(g['granskare'])
        except (ValueError,KeyError,TypeError):raise kl.Vagrad('Separat godkänd granskning av exakt förslag/version saknas.') from None
        tree=repoidentitet(root,version,m['gren'])
        if kf.git(root,'merge-base',x['bas'],version).decode().strip()!=x['bas']:raise kl.Vagrad('Försöksbasen är inte införandets förfader.')
        changed={p.decode() for p in kf.git(root,'diff','--name-only','-z',x['bas'],version).split(b'\0') if p}
        if changed!=set(a):raise kl.Vagrad('Införandet innehåller andra ändringar än försöket.')
        efter={n:hashlib.sha256(v['text'].encode()).hexdigest() for n,v in a.items()}
        for n,h in efter.items():
            if filversion(root,version,n)!=h:raise kl.Vagrad('Git-versionen innehåller inte den provade ändringen.')
        ident=kl.hash_({'forsok':forsok,'version':version,'patch':x['andringar'],'granskning':granskning,'mandat':mid})
        gamla=p.setdefault('inforanden',[])
        if any(v['id']==ident for v in gamla):return json.loads(kl.ks.jsontext(p))
        if d['forbrukat'].get(mid,0)>=m['max_registreringar']:raise kl.Vagrad('Registreringsbudgeten är slut.')
        if mandat(loop,mid)!=m or las(loop.rot.parent/'GRANSKNINGAR.json',loop.rot.parent)[1]!=gh:raise kl.Vagrad('Mandat eller granskning ändrades.')
        if repoidentitet(root,version,m['gren'])!=tree:raise kl.Vagrad('Git ändrades under observationen.')
        b={'id':ident,'forsok':forsok,'version':version,'trad':tree,'gren':m['gren'],'tid':time.time(),
           'fore':{n:v['fore'] for n,v in a.items()},'efter':efter,'mandat':mid,'mandat_sha256':m['fil_sha256'],
           'granskning':granskning,'granskning_sha256':gh,'omfattning':'lokal Git-version, inte verifierad drift'}
        gamla.append(b);p.update(inforande='infort',effekt='inte_observerad',revision=p['revision']+1)
        x.update(inforande='infort',inforande_id=ident,effekt='inte_observerad');d['forbrukat'][mid]=d['forbrukat'].get(mid,0)+1
        return json.loads(kl.ks.jsontext(p))


def folj_upp(loop,root,pid,revision,version,utfall,bevis,omfattning,observator):
    if utfall not in ('inte_observerad','forbattrat','forsamrat','blandat','oforandrat','ofullstandigt'):raise kl.Vagrad('Okänt utfall.')
    with kf.ensam(loop),loop.trans() as d:
        p=loop._post(d,pid,revision)
        if p['inforande']!='infort' or not p.get('inforanden'):raise kl.Vagrad('Ingen verifierad införandeversion finns.')
        b=p['inforanden'][-1]
        if version!=b['version']:raise kl.Vagrad('Observationen avser en annan införandeversion.')
        repoidentitet(root,version,b['gren'])
        for n,h in b['efter'].items():
            if filversion(root,version,n)!=h:raise kl.Vagrad('Införandet har ändrats.')
        p['uppfoljning'].append({'utfall':utfall,'bevis':kl.text(bevis),'omfattning':kl.text(omfattning),
            'observator':kl.text(observator,120),'tid':time.time(),'version':version,'inforande_id':b['id'],
            'kalltyp':'inrapporterad observation'})
        p.update(effekt=utfall,revision=p['revision']+1)
        d['forsok'][b['forsok']]['effekt']=utfall
        return json.loads(kl.ks.jsontext(p))


def aterstallning(loop,root,pid,revision,version,mid):
    """Bekräfta redan genomförd återställning, utan att återställa eller skriva filer."""
    with kf.ensam(loop),loop.trans() as d:
        p=loop._post(d,pid,revision);m=mandat(loop,mid)
        if d['paus'] or p['inforande']!='infort' or not p.get('inforanden'):raise kl.Vagrad('Ingen aktiv införandepost att återställa.')
        b=p['inforanden'][-1]
        if b['mandat']!=mid or set(b['fore'])-set(m['filer']):raise kl.Vagrad('Annat återställningsmandat.')
        tree=repoidentitet(root,version,m['gren'])
        if version==b['version'] or kf.git(root,'merge-base',b['version'],version).decode().strip()!=b['version']:raise kl.Vagrad('Återställningen måste vara en efterföljande Git-version.')
        for n,h in b['fore'].items():
            if filversion(root,version,n)!=h:raise kl.Vagrad('Den tidigare filversionen är inte återställd.')
            if h is None and ((Path(root)/n).exists() or (Path(root)/n).is_symlink()):raise kl.Vagrad('En borttagen nytillagd fil finns kvar i arbetskopian.')
        if mandat(loop,mid)!=m or repoidentitet(root,version,m['gren'])!=tree:raise kl.Vagrad('Underlaget ändrades under observationen.')
        p.setdefault('aterstallningar',[]).append({'version':version,'trad':tree,'inforande_id':b['id'],'tid':time.time(),
            'omfattning':'manuellt återställda filer verifierade; orelaterade filer inte ändrade av observatören'})
        p.update(inforande='aterstallt',effekt='inte_observerad',revision=p['revision']+1)
        d['forsok'][b['forsok']].update(inforande='aterstallt',effekt='inte_observerad')
        return json.loads(kl.ks.jsontext(p))
