#!/usr/bin/env python3
"""Privat förbättringsunderlag vid befintliga Kirurgen, utan automatisk aktivering.

Registret och backloggen behåller sina uppgifter. Denna post binder signaler,
diagnos, förhandsbestämt prov och eftereffekt med stabil identitet. En atomisk
fil och kort flock räcker för ett lokalt, begränsat antal försök. Exekvering och
mandat prövas separat av kirurg_forsok; modellen kan inte skriva ägarbeslut.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time
import uuid
import kundstart as ks
import kundstart_beredning as kb

ROOT=Path(__file__).resolve().parents[1]
DIAGNOSER=('saknat_underlag','overlamningsfel','kunskapsfel','metodkoppling','verktygsatkomst','implementation','bedomning','saknad_verifiering','mojlighet')
FASER=('kundstart','forberedelse','referenser','skiss','forfining','helbygge','granskning','leverans','forvaltning')


class Vagrad(ValueError):pass


def text(v,tak=4000):
    try:return ks.text(v,tak)
    except ks.Vagrad:raise Vagrad('Textfältet är ogiltigt eller innehåller känsliga strängar.') from None


def nyckel(v):
    if not isinstance(v,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',v):raise Vagrad('Ogiltig identitet.')
    return v


def hash_(v):return hashlib.sha256(ks.jsontext(v).encode()).hexdigest()


def fil(p,rot):
    p=Path(p).absolute();rot=Path(rot).absolute()
    if not p.is_relative_to(rot) or any(x.is_symlink() for x in (p,*p.parents)):raise Vagrad('Lagringen får inte gå genom en länk eller lämna sin rot.')
    return p


class Loop:
    def __init__(self,rot=None):
        self.rot=Path(rot or ROOT/'kirurgen/forbattringar').absolute()
        fil(self.rot,self.rot);self.rot.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(self.rot,0o700)
    @contextlib.contextmanager
    def trans(self):
        f=fil(self.rot/'.las',self.rot);fd=os.open(f,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):raise Vagrad('Låset är inte en vanlig fil.')
            fcntl.flock(fd,fcntl.LOCK_EX)
            p=fil(self.rot/'FORBATTRINGAR.json',self.rot)
            try:
                with p.open() as f:raw=f.read(8_000_001)
                if len(raw)>8_000_000:raise ValueError()
                d=json.loads(raw)
                if d.get('schema')!=1 or not isinstance(d.get('poster'),dict) or not isinstance(d.get('forsok'),dict):raise ValueError()
            except FileNotFoundError:d={'schema':1,'revision':0,'paus':False,'poster':{},'forsok':{},'forbrukat':{}}
            except (OSError,ValueError,TypeError,AttributeError):raise Vagrad('Förbättringsregistret kunde inte läsas. Inget skrivs över.') from None
            fore=ks.jsontext(d);yield d
            if ks.jsontext(d)!=fore:
                d['revision']+=1;data=(ks.jsontext(d)+'\n').encode()
                if len(data)>8_000_000:raise Vagrad('Registret kräver arkivering innan nya poster ryms.')
                kb.atomiskt(p,data)
        finally:os.close(fd)
    def vy(self):
        with self.trans() as d:return json.loads(ks.jsontext(d))
    def signal(self,problem,titel,fas,kalla,version,observation,belagg,kallandel=None):
        """Samma problemnyckel förenar flera källor; innehållsversionerna bevaras var för sig.

        Problemnyckeln är en uttrycklig klassning, inte ett påstående om automatisk
        semantisk deduplicering av godtyckliga texter.
        """
        nyckel(problem)
        if fas not in FASER:raise Vagrad('Okänd arbetsfas.')
        signal={'kalla':text(kalla),'version':text(version,200),'observation':text(observation),
                'belagg':text(belagg),'del':text(kallandel) if kallandel else None}
        sid=hash_(signal);pid='F-'+hash_({'problem':problem,'fas':fas})[:20]
        with self.trans() as d:
            p=d['poster'].setdefault(pid,{'id':pid,'problem':problem,'titel':text(titel,200),'fas':fas,'revision':0,
                'signaler':[],'diagnoser':[],'planer':[],'forsok':[],'disposition':'oppen','skal':None,
                'ateroppna':None,'backlog':None,'inforande':'inte_infort','effekt':'inte_observerad','uppfoljning':[]})
            if not any(x['id']==sid for x in p['signaler']):
                p['signaler'].append(dict(signal,id=sid,tid=time.time()));p['revision']+=1
                if p['disposition'] in ('avslag','parkera'):p['nytt_underlag']=True
            return json.loads(ks.jsontext(p))
    def _post(self,d,pid,revision):
        p=d['poster'].get(nyckel(pid))
        if not p:raise Vagrad('Förbättringsposten saknas.')
        if type(revision) is not int or p['revision']!=revision:raise Vagrad('Posten ändrades; läs den igen.')
        return p
    def diagnos(self,pid,revision,slag,skal,alternativ,konsekvens,belaggsstyrka):
        if slag not in DIAGNOSER:raise Vagrad('Okänd problemklass.')
        if konsekvens not in ('sanning_sakerhet','stor','begransad') or belaggsstyrka not in ('reproducerat','observerat','hypotes'):
            raise Vagrad('Ange konsekvens och beläggens styrka separat.')
        with self.trans() as d:
            p=self._post(d,pid,revision)
            diag={'slag':slag,'skal':text(skal),'alternativ':text(alternativ),'konsekvens':konsekvens,
                  'belaggsstyrka':belaggsstyrka,'signaler':[s['id'] for s in p['signaler']],'tid':time.time()}
            p['diagnoser'].append(diag);p['revision']+=1
            return json.loads(ks.jsontext(p))
    def plan(self,pid,revision,plan):
        krav=('fraga','jamforelse','framgang','forsamring','provtyp','andel','risk','ansvarig')
        if not isinstance(plan,dict) or set(plan)!=set(krav):raise Vagrad('Planen måste ange fråga, jämförelse, förhandskriterier och avgränsning.')
        plan={k:text(v) for k,v in plan.items()}
        if plan['provtyp'] not in ('regression','atkomst','integration','design','intervju'):raise Vagrad('Okänd provtyp.')
        with self.trans() as d:
            p=self._post(d,pid,revision)
            if not p['diagnoser']:raise Vagrad('Diagnostisera problemet före försöksplanen.')
            plan=dict(plan,diagnos=hash_(p['diagnoser'][-1]));plan['sha256']=hash_(plan)
            if not any(x['sha256']==plan['sha256'] for x in p['planer']):p['planer'].append(plan);p['revision']+=1
            return json.loads(ks.jsontext(p))
    def disposition(self,pid,revision,val,skal,ateroppna=None,backlog=None):
        if val not in ('oppen','delide','forsok','parkera','avslag'):raise Vagrad('Okänd disposition.')
        if val in ('parkera','avslag') and not ateroppna:raise Vagrad('Ange när underlaget ska kunna omprövas.')
        if backlog and not re.fullmatch(r'B-\d{8}-[a-z0-9-]+',backlog):raise Vagrad('Ange en befintlig backlogidentitet.')
        if backlog and not (ROOT/'backlog'/f'{backlog}.md').is_file():raise Vagrad('Backlogposten finns inte; ingen parallell uppgift skapas.')
        with self.trans() as d:
            p=self._post(d,pid,revision)
            p.update(disposition=val,skal=text(skal),ateroppna=text(ateroppna) if ateroppna else None,backlog=backlog,
                     revision=p['revision']+1,nytt_underlag=False)
            return json.loads(ks.jsontext(p))
    def pausa(self,paus):
        if type(paus) is not bool:raise Vagrad('Paus måste vara ja eller nej.')
        with self.trans() as d:d['paus']=paus
    def stickprov(self,frö,antal=5):
        nyckel(frö)
        if type(antal) is not int or not 1<=antal<=20:raise Vagrad('Stickprovet behöver 1–20 poster.')
        with self.trans() as d:
            ur=[p for p in d['poster'].values() if p['disposition'] in ('avslag','parkera')]
            return sorted(ur,key=lambda p:hash_(frö+p['id']))[:antal]
    def folj_upp(self,pid,revision,utfall,bevis,omfattning,observator,*,root=None,version=None):
        """Även direkta anrop behöver den versionsbundna införandegränsen."""
        if root is None or version is None:raise Vagrad('Eftereffekt kräver en verifierad införandeversion och repoidentitet.')
        import kirurg_uppfoljning
        return kirurg_uppfoljning.folj_upp(self,root,pid,revision,version,utfall,bevis,omfattning,observator)
