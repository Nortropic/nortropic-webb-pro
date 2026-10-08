#!/usr/bin/env python3
"""Ett avgränsat lokalt regressionsförsök, inom ett separat ägarmandat.

Ingen modell startas. Ingen schemaläggning aktiveras. Kod körs bara i en egen
seatbelt-kopia utan nät och utan skrivåtkomst till metod, facit eller mandat.
Resultatet är ett reproduktionsprov; installation och verklig eftereffekt är
separata händelser och kan inte beställas av försökskoden.
"""
import contextlib
import fcntl
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
import uuid
import kirurg_loop as kl
import korregister
import processgrans


SKYDDAT=('kontroller/kirurg','kontroller/processgrans','kontroller/slugvakt','kontroller/commitvakt',
          'kontroller/korvakt','kontroller/korslut','kontroller/sandlada','kontroller/rokprov',
          'kunskap/designregler','kunskap/metodkarta','kunskap/visuell-niva','kritik/', '.claude/',
          'underlag/','kunder/','kirurgen/','backlog/','dashboard/', 'CLAUDE.md','BESLUT.md','.git')


def vag(v):
    if not isinstance(v,str) or not v or '\\' in v or '\x00' in v:raise kl.Vagrad('Ogiltig filväg.')
    p=PurePosixPath(v)
    if p.is_absolute() or any(x in ('','.','..') for x in v.split('/')):raise kl.Vagrad('Filvägen måste vara entydigt reporelativ.')
    return v


def mandat(loop,mid):
    kl.nyckel(mid)
    # Denna fil skapas/ändras inte av någon av förbättringsverktygens ingångar.
    p=kl.fil(loop.rot.parent/'AGARMANDAT.json',loop.rot.parent)
    try:
        if p.stat().st_size>100000:raise ValueError()
        data=json.loads(p.read_text());m=data['mandat'][mid]
        if data.get('schema')!=1 or m['klass']!='isolerat_regressionsprov':raise ValueError()
        for k in ('max_forsok','sekunder_per_variant'):
            if type(m[k]) is not int or not 1<=m[k]<=100:raise ValueError()
        if type(m['giltig_till']) not in (int,float) or not math.isfinite(m['giltig_till']) or m['giltig_till']<=time.time():raise ValueError()
        if m['granskning']!='oberoende' or m['aterstallning']!='kopian_kasseras':raise ValueError()
        if not isinstance(m['filer'],list) or not m['filer'] or len(m['filer'])>10:raise ValueError()
        for v in m['filer']:
            vag(v)
            if v.startswith(SKYDDAT) or not v.endswith(('.py','.mjs','.js','.md','.json','.css','.astro')):raise ValueError()
        v=vag(m['prov'])
        if not v.startswith('kontroller/rokprov/') or not v.endswith('.py') or not re.fullmatch(r'[a-f0-9]{64}',m['prov_sha256']):raise ValueError()
        kl.text(m['ansvarig'],120)
    except (OSError,ValueError,TypeError,KeyError):raise kl.Vagrad('Ett giltigt, avgränsat ägarmandat för försöket saknas.') from None
    return dict(m,id=mid,sha256=kl.hash_(m))


@contextlib.contextmanager
def ensam(loop):
    f=kl.fil(loop.rot/'.forsok.las',loop.rot)
    fd=os.open(f,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise kl.Vagrad('Försökslåset är ogiltigt.')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise kl.Vagrad('Ett förbättringsförsök pågår redan.') from None
        yield fd
    finally:os.close(fd)


def git(root,*args):
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0')
    r=subprocess.run(['git','-C',str(root),'-c','core.fsmonitor=false',*args],env=env,capture_output=True,timeout=15)
    if r.returncode:raise kl.Vagrad('Repots version kunde inte läsas.')
    return r.stdout


def snapshot(root,commit,mal):
    data=git(root,'archive','--format=tar',commit)
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        for f in t.getmembers():
            if not f.isfile() and not f.isdir():raise kl.Vagrad('Försöksbasen innehåller en länk eller specialfil.')
            if not f.name or f.name.startswith(('underlag/','kunder/','kirurgen/')):raise kl.Vagrad('Försöket får inte kopiera privat underlag.')
        t.extractall(mal,filter='data')


def prov(root,projekt,facit,timeout,loop,lasfd,kontroll):
    """Facit och förberedda instruktioner ligger utanför kodens skrivrätt.

    Provet är ett unittest-program och ska rapportera en avslutad svit. Att det
    passerar ersätter inte oberoende kodgranskning; ingen kryptografisk garanti
    om godtycklig testkods sanningsenlighet görs.
    """
    if not Path(processgrans.SANDBOX_EXEC).is_file():raise kl.Vagrad('Processgränsen saknas; inget körs utan den.')
    tmp=projekt/'.tmp';tmp.mkdir()
    # Ändringen läggs in av styrenheten före provet. Under körningen är även
    # provkopians metod och källkod skrivskyddad; bara dess egen .tmp är skrivbar.
    profil=processgrans.profil_katalog(tmp,root=root)
    # Försökskoden får inte läsa den aktiva kund-/metodmiljön eller använda
    # processignaler för att ändra styrenheten. Regressioner här behöver inte fork.
    profil+='\n(deny file-read* (subpath %s))\n'%processgrans.sbpl(Path(root).resolve())
    profil+='(deny signal)\n(deny process-fork)\n'
    for p in (loop.rot.parent,projekt.parent):
        profil+='(deny file-read* (subpath %s))\n'%processgrans.sbpl(Path(p).resolve())
    profil+='(allow file-read* (subpath %s) (literal %s))\n'%(processgrans.sbpl(projekt),processgrans.sbpl(facit))
    env={k:v for k,v in os.environ.items() if k in processgrans.MILJO_KATALOG}
    env.update(HOME=str(tmp),TMPDIR=str(tmp),PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(projekt/'kontroller'))
    start=time.monotonic()
    # Tolken hämtas ur körmiljön, inte ur kopians eller källans ändringsbara filer.
    py=Path(sys.executable).resolve()
    logg=projekt.parent/(projekt.name+'-prov.log')
    cfg={'args':[processgrans.SANDBOX_EXEC,'-p',profil,str(py),'-B',str(facit),str(projekt)],
         'cwd':str(projekt),'env':env,'logg':str(logg),'sekunder':timeout,'resultat':str(projekt.parent/(projekt.name+'-resultat.json'))}
    spec=projekt.parent/(projekt.name+'-vakt.json');spec.write_text(ks_json(cfg));os.chmod(spec,0o600)
    las,skriv=os.pipe();p=None
    try:
        kontroll()
        p=subprocess.Popen([str(py),'-B',str(Path(__file__).with_name('kirurg_vakt.py')),str(spec),
                            '--liv-fd',str(las),'--las-fd',str(lasfd)],
                           stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                           pass_fds=(las,lasfd),start_new_session=True)
        os.close(las);las=None
        while p.poll() is None:
            kontroll();time.sleep(.05)
        _,fel=p.communicate(timeout=5)
        if p.returncode!=0:raise kl.Vagrad('Provvakten avslutades inte normalt.')
        r=json.loads(Path(cfg['resultat']).read_text())
        if r['avbruten']:raise kl.Vagrad('Provets styrprocess avbröt försöket.')
        rc=r['rc'];timeoutfel=r['timeout']
        with logg.open('rb') as ut:raw=ut.read(1_000_001)
    finally:
        os.close(skriv)
        if las is not None:os.close(las)
        if p is not None:
            # EOF stoppar och väntar in barnet; släpp aldrig låset före vakten.
            p.communicate(timeout=timeout+7)
    kort=bool(re.search(rb'\nRan [1-9][0-9]* tests? in ',raw))
    klart=bool(kort and re.search(rb'\nOK\s*$',raw))
    fel=re.search(rb'\nFAILED \(failures=([1-9][0-9]*)\)\s*$',raw)
    reproducerat=bool(kort and fel and rc==1 and not timeoutfel)
    return {'rc':rc,'sekunder':round(time.monotonic()-start,3),'timeout':timeoutfel,
            'svit_klar':klart,'godkant':rc==0 and klart and not timeoutfel and len(raw)<=1_000_000,
            'reproducerat':reproducerat,'provfel':not (klart or reproducerat),
            'logg_sha256':__import__('hashlib').sha256(raw).hexdigest(),'logg':str(logg)}


def kor(loop,pid,revision,mid,start_id,root,bas,andringar):
    kl.nyckel(start_id);root=Path(root).resolve()
    if not isinstance(bas,str) or not re.fullmatch(r'[a-f0-9]{40}',bas):raise kl.Vagrad('Försöket behöver ett fullständigt bascommit.')
    begaran=kl.hash_({'post':pid,'mandat':mid,'bas':bas,'andringar':andringar})
    with ensam(loop) as lasfd:
        # Saknat arbetarlås med kvarstående pagar är ett avbrutet försök, aldrig
        # en nollställd budget eller ett automatiskt återförsök.
        with loop.trans() as d:
            for x in d['forsok'].values():
                if x['status']=='pagar':x.update(status='avbrutet',utfall='ofullstandigt',slut=time.time())
            gammal=d['forsok'].get(start_id)
            if gammal:
                if gammal['post']!=pid:raise kl.Vagrad('Operations-id hör till en annan förbättring.')
                if gammal.get('begaran')!=begaran:raise kl.Vagrad('Operations-id hör till ett annat försöksunderlag.')
                return gammal
        import kirurg_drift
        kirurg_drift.kapacitet(root)
        m=mandat(loop,mid)
        if not isinstance(andringar,dict) or not andringar or set(andringar)-set(m['filer']):raise kl.Vagrad('Ändringen ligger utanför mandatets filer.')
        for name,v in andringar.items():
            vag(name)
            if not isinstance(v,dict) or set(v)!= {'fore','text'} or not isinstance(v['text'],str) or len(v['text'].encode())>200000:raise kl.Vagrad('Ogiltig filändring.')
            if v['fore'] is not None and (not isinstance(v['fore'],str) or not re.fullmatch(r'[a-f0-9]{64}',v['fore'])):raise kl.Vagrad('Basfilens innehållshash behövs.')
        full=git(root,'rev-parse',bas+'^{commit}').decode().strip()
        if full!=bas:raise kl.Vagrad('Basversionen är inte exakt.')
        test=kl.fil(root/m['prov'],root)
        if not test.is_file() or test.stat().st_size>1_000_000:raise kl.Vagrad('Facit kan inte frysas.')
        facitbytes=test.read_bytes()
        if __import__('hashlib').sha256(facitbytes).hexdigest()!=m['prov_sha256']:raise kl.Vagrad('Facit skiljer sig från mandatets låsta prov.')
        with loop.trans() as d:
            p=loop._post(d,pid,revision)
            if d['paus']:raise kl.Vagrad('Förbättringsförsöken är pausade. Bevakning och analys kan fortsätta.')
            if not p['planer'] or p['planer'][-1]['provtyp']!='regression':raise kl.Vagrad('Den här arbetaren utför bara planerade regressionsprov.')
            if (p['planer'][-1]['diagnos']!=kl.hash_(p['diagnoser'][-1]) or
                p['diagnoser'][-1]['signaler']!=[s['id'] for s in p['signaler']]):raise kl.Vagrad('Nytt underlag behöver en aktuell diagnos och försöksplan.')
            import kirurg_kallhalsa
            kirurg_kallhalsa.krav(loop.rot.parent/'spaning',p['signaler'])
            bruk=d['forbrukat'].get(mid,0)
            if bruk>=m['max_forsok']:raise kl.Vagrad('Mandatets totala försöksbudget är förbrukad.')
            d['forbrukat'][mid]=bruk+1
            x={'id':start_id,'post':pid,'status':'pagar','utfall':'ofullstandigt','start':time.time(),
               'plan':p['planer'][-1],'signaler':kl.hash_(p['signaler']),'mandat':m,'bas':bas,'andringar':kl.hash_(andringar),'begaran':begaran,
               'budget_reserverad_sekunder':2*m['sekunder_per_variant'],'inforande':'inte_infort','effekt':'inte_observerad'}
            d['forsok'][start_id]=x;p['forsok'].append(start_id);p['revision']+=1
        def kontroll():
            if mandat(loop,mid)['sha256']!=m['sha256']:raise kl.Vagrad('Ägarmandatet ändrades under försöket.')
            kirurg_drift.kapacitet(root)
            with loop.trans() as d:
                if d['paus']:raise kl.Vagrad('Förbättringsförsöket pausades.')
                import kirurg_kallhalsa
                aktuell=d['poster'][pid]
                if (kl.hash_(aktuell['signaler'])!=x['signaler'] or aktuell['planer'][-1]!=x['plan'] or
                    kl.hash_(aktuell['diagnoser'][-1])!=x['plan']['diagnos']):
                    raise kl.Vagrad('Signal, diagnos eller försöksplan ändrades under försöket.')
                kirurg_kallhalsa.krav(loop.rot.parent/'spaning',aktuell['signaler'])
        try:
            run=loop.rot/'forsok'/start_id
            kl.fil(run,loop.rot);run.mkdir(parents=True,exist_ok=False,mode=0o700)
            import kundstart_beredning as kb
            kb.atomiskt(run/'ANDRINGAR.json',(ks_json(andringar)+'\n').encode())
            with korregister.egen_tmp_med('nwp-kirurg-','isolerat regressionsförsök') as temp:
                temp=Path(temp).resolve();facit=temp/'prov.py';facit.write_bytes(facitbytes)
                os.chmod(facit,0o400);x['facit_sha256']=__import__('hashlib').sha256(facit.read_bytes()).hexdigest()
                if x['facit_sha256']!=m['prov_sha256']:raise kl.Vagrad('Den frysta facitkopian stämmer inte.')
                for variant in ('fore','efter'):
                    kontroll()
                    projekt=temp/variant;projekt.mkdir();snapshot(root,bas,projekt)
                    for name,v in andringar.items():
                        f=kl.fil(projekt/name,projekt)
                        before=__import__('hashlib').sha256(f.read_bytes()).hexdigest() if f.is_file() else None
                        if before!=v['fore']:raise kl.Vagrad('Försöksbasen stämmer inte med filändringen.')
                        if variant=='efter':f.parent.mkdir(parents=True,exist_ok=True);f.write_text(v['text'])
                    r=prov(root,projekt,facit,m['sekunder_per_variant'],loop,lasfd,kontroll)
                    logg=Path(r.pop('logg'));shutil.copyfile(logg,run/(variant+'.log'));os.chmod(run/(variant+'.log'),0o600)
                    x[variant]=r
            kontroll();f,e=x['fore'],x['efter']
            x['utfall']='regression_rattad' if f['reproducerat'] and e['godkant'] else 'oforandrat' if f['godkant']==e['godkant'] else 'forsamrat'
            if f['timeout'] or e['timeout'] or f['provfel'] or e['provfel']:x['utfall']='ofullstandigt'
            x['status']='klart'
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:
            x.update(status='fel',utfall='ofullstandigt',fel=type(e).__name__+': '+str(e)[:500])
        finally:
            x['slut']=time.time()
            with loop.trans() as d:d['forsok'][start_id]=x
        return x


def ks_json(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
