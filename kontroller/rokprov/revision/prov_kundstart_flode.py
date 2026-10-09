#!/usr/bin/env python3
"""Kundstarts verkliga databas mot byggflödets ingångar; bara syntetisk kund och modellsvardubbel."""
import contextlib
import fcntl
import json
from pathlib import Path
import sys
import unittest
import sqlite3
import os
import subprocess
import shutil
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart as ks
import kundstart_beredning as kb
import forberedelse as fb
import atelje
import skapande
import kundstart_kalla as kk
import sandlada
import processgrans


class KundstartFlode(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-','Kundstart till skapandeflödet'))).resolve()
        self.db=ks.Lager(self.root/'underlag/kundstart')
        self.slug='prov-sammanhang'
        self.e,self.token=self.db.skapa(self.slug,'Syntetisk beslutsfattare',modellbudget=8)
        for m in (atelje,skapande):
            self.stack.enter_context(patch.object(m,'ROOT',self.root))
            self.stack.enter_context(patch.object(m,'UNDERLAG',self.root/'underlag'))
        self.stack.enter_context(patch.object(atelje,'KUNDER',self.root/'kunder'))
        self.gor('meddelande',{'text':'Exempelverkstaden arbetar nationellt med service.'})
        jobb=self.db.ta_jobb('syntetisk-transport');mid=jobb['dokument']['meddelanden'][0]['id']
        v={'namn':'Exempelverkstaden','rackvidd':{'typ':'nationell'},'kontaktvagar':[],'tjanster':['Service']}
        self.db.modellsvar(jobb,{'text':'Stäm av uppgifterna.','forslag':[],'fragor':[],
            'verksamhet':{'varden':v,'kallor':{k:[mid] for k in v}}})
        d=self.db.las(self.e,self.token)
        d=self.gor('bekrafta_verksamhet',{'sha256':d['verksamhet_forslag']['sha256']})
        self.kvitto=kb.overlamna(self.db,self.e,d['revision'],'prov-overlamning-ett',self.root)
        self.u=self.root/'underlag'/self.slug

    def gor(self,slag,data):
        d=self.db.las(self.e,self.token)
        return self.db.kundhandling(self.e,self.token,d['revision'],ks.id_(),slag,data)

    def paket(self):
        p=self.u/'atelje/forberett';p.mkdir(parents=True)
        for n in fb.FILER:(p/n).write_text('Syntetiskt arbetsunderlag '+n)
        (p/'KUNDFORSTAELSE.md').write_text('\n\n'.join('## %s\n\n%s'%(r,'- Antaget: syntetiskt.' if r==fb.KUNDFORSTAELSE_RUBRIKER[-1] else 'Syntetiskt.')
                                                    for r in fb.KUNDFORSTAELSE_RUBRIKER)+'\n')  # förberedelsens sex rubriker (2026-10-09)
        return p

    def test_ny_kundrattelse_nekar_start_trots_oforandrade_snapshotfiler(self):
        fb.krav(self.slug)
        fore={p.name:p.read_bytes() for p in self.u.iterdir() if p.is_file()}
        self.gor('meddelande',{'text':'Rättelse: service ska inte längre ingå.'})
        self.assertFalse(kb.aktuell(self.db,self.u))
        self.assertEqual(fore,{p.name:p.read_bytes() for p in self.u.iterdir() if p.is_file()})
        with self.assertRaises(ValueError):fb.krav(self.slug)

    def test_sen_kundrattelse_nekar_publicering_av_forberedelsen(self):
        fb.krav(self.slug);p=self.paket();indata=fb.indata(self.slug)
        self.gor('meddelande',{'text':'Syntetisk ändring under bearbetningen.'})
        with self.assertRaises(ValueError):fb.publicera(self.slug,p,indata)
        self.assertFalse((self.u/'BRIEF.md').exists())
        self.assertFalse(fb.giltig(self.slug))

    def test_fardig_forberedelse_blir_inaktuell_vid_ny_kundrevision(self):
        p=self.paket();fb.publicera(self.slug,p,fb.indata(self.slug))
        self.assertTrue(fb.giltig(self.slug))
        self.gor('uppgift',{'id':'nytt','amne':'A','text':'Ett nytt syntetiskt önskemål.'})
        self.assertFalse(fb.giltig(self.slug))

    def test_starta_nekar_ny_och_aterupptagen_korning_fore_process(self):
        self.gor('meddelande',{'text':'Ny syntetisk källa.'})
        for handling in ('om','fortsatt','valda'):
            a=SimpleNamespace(slug=self.slug,start_id='kallprov-'+handling,
                **{n:n==handling for n in ('forbered','om','ny_riktning','putsa','valda','fortsatt','bara_domare')})
            with patch.object(atelje.subprocess,'Popen') as proc, self.assertRaises(ValueError):
                atelje.starta(a,self.u/'atelje')
            proc.assert_not_called()

    def test_kontrollen_skriver_inget_och_skapar_inte_saknad_databas(self):
        fore=self.db.fil.read_bytes()
        kk.krav(self.u)
        self.assertEqual(fore,self.db.fil.read_bytes())
        self.db.fil.unlink()
        self.assertFalse(kk.giltig(self.u))
        self.assertFalse(self.db.fil.exists())

    def test_skadad_saknad_och_lankad_kalla_nekar(self):
        fil=self.u/'KUNDSTART.json';b=fil.read_bytes()
        for data in ('null','[]','{}','{"status":"klar"}'):
            fil.write_text(data);self.assertFalse(kk.giltig(self.u))
        fil.write_bytes(b)
        db=self.db.fil;db.rename(db.with_suffix('.fore'))
        db.symlink_to(db.with_suffix('.fore'))
        self.assertFalse(kk.giltig(self.u))

    def test_ett_annat_arendes_andring_paverkar_inte_kallan(self):
        e,t=self.db.skapa('prov-annan','Annan syntetisk beslutsfattare')
        self.db.kundhandling(e,t,self.db.las(e,t)['revision'],ks.id_(),'meddelande',{'text':'Annan kund ändras.'})
        self.assertTrue(kk.giltig(self.u))

    def test_publicering_haller_kallans_las_utan_att_blockera_modellarbete(self):
        import threading
        p=self.paket();g=fb.indata(self.slug);start=threading.Event();klart=threading.Event();fel=[]
        def kundandring():
            start.set()
            try:self.gor('meddelande',{'text':'Syntetisk samtidig rättelse.'})
            except Exception as e:fel.append(type(e).__name__)
            finally:klart.set()
        trad=None;skriv=atelje.skriv_json_atomiskt
        def observera(f,d):
            nonlocal trad
            if d.get('status')=='publicerar':
                trad=threading.Thread(target=kundandring);trad.start()
                self.assertTrue(start.wait(2));self.assertFalse(klart.wait(.05))
            skriv(f,d)
        try:
            with patch.object(atelje,'skriv_json_atomiskt',side_effect=observera):fb.publicera(self.slug,p,g)
        finally:
            if trad:trad.join(3)
        self.assertTrue(klart.is_set());self.assertEqual(fel,[])
        self.assertFalse(fb.giltig(self.slug))

    def test_aldre_manuella_underlag_kraver_inte_kundstarts_databas(self):
        u=self.root/'underlag/prov-manuell';u.mkdir()
        self.assertTrue(kk.giltig(u))

    def test_borttagen_marker_blir_inte_ett_manuellt_underlag(self):
        self.gor('meddelande',{'text':'Syntetiskt nytt kundbeslut.'})
        (self.u/'KUNDSTART.json').unlink()
        self.assertFalse(kk.giltig(self.u))
        with self.assertRaises(ValueError):fb.krav(self.slug)

    def test_tomt_och_trasigt_filmanifest_ar_ingen_giltig_overlamning(self):
        with self.db.trans() as c:
            raw=c.execute('SELECT post FROM overlamningar WHERE arende=?',(self.e,)).fetchone()[0]
        for manifest in ({},[],None,{'KUNDSTART.json':'felhash'}):
            with self.subTest(manifest=manifest):
                post=json.loads(raw);post['filer']=manifest
                with self.db.trans() as c:
                    c.execute('UPDATE overlamningar SET post=? WHERE arende=?',(json.dumps(post),self.e))
                self.assertFalse(kk.giltig(self.u))
                with (self.db.rot/'.lagring.las').open('rb') as las:
                    fcntl.flock(las,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def test_ovantat_valideringsfel_lamnar_inte_kallan_last(self):
        with patch.object(kb,'post_aktuell',side_effect=RuntimeError('syntetiskt parserfel')):
            with self.assertRaises(RuntimeError):kk.krav(self.u)
        with (self.db.rot/'.lagring.las').open('rb') as las:
            fcntl.flock(las,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def test_filer_far_inte_utelamnas_ur_det_bokforda_manifestet(self):
        # Även en tredje deklarerad fil måste bindas. De obligatoriska filerna
        # räcker inte som kontroll av att hela överlämningen är oförändrad.
        f=self.u/'kundstart/material/prov/fakta.txt';f.parent.mkdir(parents=True);f.write_text('syntetisk bilaga')
        marker=self.u/'KUNDSTART.json';body=json.loads(marker.read_text())
        body['filer'][str(f.relative_to(self.u))]=ks.sha(f.read_bytes())
        marker.write_text(json.dumps(body))
        with self.db.trans() as c:
            post=json.loads(c.execute('SELECT post FROM overlamningar WHERE arende=?',(self.e,)).fetchone()[0])
            post['filer']=body['filer']|{'KUNDSTART.json':ks.sha(marker.read_bytes())}
            c.execute('UPDATE overlamningar SET post=? WHERE arende=?',(json.dumps(post),self.e))
        self.assertTrue(kk.giltig(self.u))
        f.write_text('ändrad syntetisk bilaga');self.assertFalse(kk.giltig(self.u))
        del post['filer'][str(f.relative_to(self.u))]
        with self.db.trans() as c:c.execute('UPDATE overlamningar SET post=? WHERE arende=?',(json.dumps(post),self.e))
        self.assertFalse(kk.giltig(self.u))

    def test_wal_nekar_utan_att_skapa_sqlites_sidofiler(self):
        with sqlite3.connect(self.db.fil) as c:
            self.assertEqual(c.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal')
        c.close()
        fore={p.name:p.read_bytes() for p in self.db.rot.iterdir() if p.is_file()}
        self.assertFalse(kk.giltig(self.u))
        self.assertEqual(fore,{p.name:p.read_bytes() for p in self.db.rot.iterdir() if p.is_file()})

    def test_processgransen_nekar_syntetiska_arendelagret_men_inte_egen_snapshot(self):
        kod = 'from pathlib import Path; import sys\ntry: Path(sys.argv[1]).read_bytes()\nexcept PermissionError: print("NEKAD")\nelse: print("LAST")\n'
        profil=processgrans.profil(self.slug,root=self.root,hem=str(self.root/'hem'))
        for fil,forvantat in ((self.db.fil,'NEKAD'),(self.u/'KUNDSTART.json','LAST')):
            cmd=[sys.executable,'-B','-c',kod,str(fil)]
            kontroll=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
            self.assertEqual(kontroll.stdout.strip(),'LAST')
            r=subprocess.run([processgrans.SANDBOX_EXEC,'-p',profil,*cmd],capture_output=True,text=True,timeout=10)
            self.assertEqual((r.returncode,r.stdout.strip()),(0,forvantat),r.stderr)

    def test_fasta_lasnekanden_finns_fore_arendekatalogen_skapas(self):
        for pa in (True,False):
            s=sandlada.installningar(self.slug,root=self.root,hem=str(self.root/'hem'),sandlada=pa)
            self.assertIn('Read(//'+str(self.db.rot).strip('/')+'/**)',s.get('permissions',{}).get('deny',[]))
        args=atelje.session_args(['Read'],slug=self.slug)
        self.assertIn('Read(//'+str(self.db.rot).strip('/')+'/**)',args)

    def test_kor_sh_med_arendelager_kraver_sandlada_fore_session(self):
        root=self.root
        (root/'kontroller/node_modules').mkdir(parents=True)
        (root/'.venv').symlink_to(Path(sys.executable).parent.parent)
        shutil.copyfile(Path(__file__).resolve().parents[3]/'kor.sh',root/'kor.sh')
        bin_=root/'bin';bin_.mkdir()
        fake=bin_/'claude';fake.write_text('#!/bin/sh\ntouch "'+str(root/'FEL-session')+'"\nexit 97\n');fake.chmod(0o700)
        env=dict(os.environ,PATH=str(bin_)+os.pathsep+os.environ['PATH'],NWP_SANDLADA='av')
        r=subprocess.run(['bash',str(root/'kor.sh'),self.slug,'Syntetiskt'],cwd=root,env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('Kundstarts ärendelager kräver sandlådan',r.stdout+r.stderr)
        self.assertFalse((root/'FEL-session').exists())

    def godkand_slutpost(self):
        import ateljeslut
        a=self.u/'atelje';a.mkdir()
        kod=a/'vinnare/kod';kod.mkdir(parents=True)
        (kod/'index.astro').write_text('<h1>Syntetiskt godkänd startsida</h1>')
        (self.root/'kunder'/self.slug/'sajt').mkdir(parents=True)
        status={'startad':'2026-10-08T00:00:00Z','klar':'2026-10-08T00:00:01Z',
                'kandidatflode':True,'lage':'valda','steg':'klar_for_bedomning'}
        atelje.skriv_status(a,status)
        dom=skapande.lagg_till_dom(self.slug,'ägaren','godkand','Syntetiskt teknikprov, ingen riktig ägardom.',
                                 tid='2026-10-08T00:00:02Z',underlag=self.root/'underlag')
        g={'tid':dom['tid'],'sha_index':skapande.sha256_fil(kod/'index.astro'),
           'sha_kod':skapande.sha256_katalog(kod),'underlag_sha':skapande.underlagsversion(self.slug)}
        atelje.skriv_json_atomiskt(a/'VINNARE.json',{'godkand':g})
        self.assertTrue(skapande.godkand_giltig(self.slug)[0])
        post=ateljeslut.bygg(self.slug,status,'20261008T000000Z')
        return ateljeslut.skriv(self.slug,'20261008T000000Z',post,status=status)[0]

    def agarbesked(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'dashboard'))
        import server
        with patch.multiple(server,ROOT=self.root,KUNDER=self.root/'kunder',UNDERLAG=self.root/'underlag'):
            return next(x for x in server.flodesbesked(self.slug)['tillstand'] if x['id']=='agaren_godkanner')

    def test_aktuellt_agargodkannande_visas_utan_att_slutposten_skrivs_om(self):
        f=self.godkand_slutpost();b=f.read_bytes()
        besked=self.agarbesked()
        self.assertEqual((besked['varde'],besked['status']),(True,'ja'))
        self.assertEqual(f.read_bytes(),b)

    def test_agargodkannandet_historiskt_vid_ny_kundrevision(self):
        import ateljeslut,flodesstart
        f=self.godkand_slutpost();b=f.read_bytes()
        self.gor('meddelande',{'text':'Syntetisk kundrättelse efter godkännandet.'})
        with self.assertRaises(ValueError):flodesstart.krav(self.slug,'helbygge')
        post=ateljeslut.aktuell(self.slug)['tillstand']['agaren_godkanner']
        self.assertIsNone(post['varde']);self.assertTrue(post['historik']['varde'])
        self.assertIn('Kundstart',post['text'])
        besked=self.agarbesked()
        self.assertEqual((besked['varde'],besked['status']),(None,'historiskt'))
        self.assertEqual(f.read_bytes(),b)

    def test_agargodkannandet_historiskt_vid_andrad_eller_saknad_vinnare(self):
        import flodesstart
        f=self.godkand_slutpost();b=f.read_bytes()
        (self.u/'atelje/vinnare/kod/index.astro').write_text('<h1>Ändrad syntetisk sida</h1>')
        for saknad in (False,True):
            if saknad:(self.u/'atelje/VINNARE.json').unlink()
            with self.subTest(saknad=saknad):
                with self.assertRaises(ValueError):flodesstart.krav(self.slug,'helbygge')
                besked=self.agarbesked()
                self.assertEqual((besked['varde'],besked['status']),(None,'historiskt'))
                self.assertEqual(f.read_bytes(),b)

    def test_ny_overlamning_med_samma_verksamhet_ateraktiverar_inte_helbyggets_dom(self):
        import korslut,prova,granska,exportera
        # Produktionsvägens metod och slutpost används: en tom metodstubb skulle
        # dölja skillnaden mellan ändrade företagsuppgifter och ändrat uppdrag.
        mekanik=Path(__file__).resolve().parents[3]
        for namn in ('kunskap','kritik'):
            (self.root/namn).symlink_to(mekanik/namn,target_is_directory=True)
        for modul,varden in (
            (granska,dict(ROOT=self.root,UNDERLAG=self.root/'underlag',KUNDER=self.root/'kunder',
                SCHEMA=self.root/'kritik/SCHEMA-granskning.json',SCHEMA_ORIGINALITET=self.root/'kritik/SCHEMA-originalitet.json')),
            (korslut,dict(ROOT=self.root)),
            (exportera,dict(ROOT=self.root,KUNDER=self.root/'kunder',UNDERLAG=self.root/'underlag'))):
            self.stack.enter_context(patch.multiple(modul,**varden))
        self.stack.enter_context(patch.dict(os.environ,NWP_ATELJE='pa'))
        self.godkand_slutpost()
        k=self.root/'kunder'/self.slug;sajt=k/'sajt'
        for d in ('src/pages','dist','public'):(sajt/d).mkdir(parents=True,exist_ok=True)
        for f in ('src/pages/index.astro','dist/index.html'):(sajt/f).write_text('<h1>Syntetiskt helbygge</h1>')
        (sajt/'package.json').write_text('{"dependencies":{}}')
        (sajt/'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        dh=prova.dist_hash(sajt/'dist');korning='20261008T000100Z'
        f=k/'korningar'/korning/'SLUT.json';f.parent.mkdir(parents=True)
        rapport=k/'RAPPORT.md';rapport.write_text('Syntetiskt mekanikprov, ingen kvalitetsdom.')
        metod=granska.aktuell_metod(self.slug)
        status={'ok':True,'dist_sha256':dh,'kallor_sha256':skapande.kallversion(sajt)}
        stopp={'kontroller_grona':True,'korning':korning,'dist_sha256':dh,'slapp':True,
               'rapport_sha256':korslut.sha_fil(rapport),'rapport_korning':korning}
        dom=k/'DOM.json';dom.write_text(json.dumps({'domar':[{'tid':'2026-10-08T00:01:02Z',
            'bygge_dist':dh[:12],'svar':{'namn':korslut.AGAREN_JA}}]}))
        granskning=dict(metod,dist_sha256=dh,godkand=True,runda=1,korning=korning,kriterier={})
        post=korslut.slutpost(k,'0',korning,status,stopp,granskning,dh,None,None,[],[],False,None,0,'Syntetiskt prov')
        f.write_text(json.dumps(post))
        self.assertEqual(post['metod']['granskning'],metod)
        self.assertTrue(korslut.aktuell(k)['tillstand']['klart_for_leverans']['varde'])
        self.assertTrue(exportera.exportera(self.slug,bygg=False)['ok'])
        gamla=[f,dom,*list((k/'exporter').glob('*/EXPORT.json'))]
        fore={p:p.read_bytes() for p in gamla}
        verksamhet=(self.u/'VERKSAMHET.json').read_bytes()
        self.gor('meddelande',{'text':'Syntetisk rättelse: offertformulär i stället för bokningsflöde.'})
        jobb=self.db.ta_jobb('syntetisk-ny-overlamning')
        mid=[m for m in jobb['dokument']['meddelanden'] if m['roll']=='kund'][-1]['id']
        v={'namn':'Exempelverkstaden','rackvidd':{'typ':'nationell'},'kontaktvagar':[],'tjanster':['Service']}
        self.db.modellsvar(jobb,{'text':'Syntetiskt förslag.','forslag':[],'fragor':[],
            'verksamhet':{'varden':v,'kallor':{n:[mid] for n in v}}})
        d=self.db.las(self.e,self.token)
        d=self.gor('bekrafta_verksamhet',{'sha256':d['verksamhet_forslag']['sha256']})
        kb.overlamna(self.db,self.e,d['revision'],'syntetisk-andra-overlamning',self.root)
        self.assertTrue(kk.giltig(self.u))
        self.assertEqual((self.u/'VERKSAMHET.json').read_bytes(),verksamhet)
        nu=korslut.aktuell(k)['tillstand']
        self.assertIsNone(nu['agaren_godkanner']['varde'])
        self.assertTrue(nu['agaren_godkanner']['historik']['varde'])
        self.assertFalse(nu['klart_for_leverans']['varde'])
        self.assertEqual((self.agarbesked()['varde'],self.agarbesked()['status']),(None,'historiskt'))
        ep=exportera.aktuell(self.slug)['tillstand']
        self.assertIsNone(ep['agaren_godkanner']['varde']);self.assertFalse(ep['klart_for_leverans']['varde'])
        self.assertEqual(fore,{p:p.read_bytes() for p in gamla})
        self.assertNotEqual(granska.aktuell_metod(self.slug)['metod_sha'],metod['metod_sha'])

    def test_helbyggets_besked_historiskt_nar_godkannandets_underlag_andras(self):
        # GR-20261008-r117-claude#A1: samma underlag som Flöde steg 5 och kor.sh prövar (skapande.godkand_giltig), inte bara metodhashen
        import korslut,prova,granska,exportera
        mekanik=Path(__file__).resolve().parents[3]
        for namn in ('kunskap','kritik'):
            (self.root/namn).symlink_to(mekanik/namn,target_is_directory=True)
        for modul,varden in (
            (granska,dict(ROOT=self.root,UNDERLAG=self.root/'underlag',KUNDER=self.root/'kunder',
                SCHEMA=self.root/'kritik/SCHEMA-granskning.json',SCHEMA_ORIGINALITET=self.root/'kritik/SCHEMA-originalitet.json')),
            (korslut,dict(ROOT=self.root)),
            (exportera,dict(ROOT=self.root,KUNDER=self.root/'kunder',UNDERLAG=self.root/'underlag'))):
            self.stack.enter_context(patch.multiple(modul,**varden))
        self.stack.enter_context(patch.dict(os.environ,NWP_ATELJE='pa'))
        self.godkand_slutpost()
        k=self.root/'kunder'/self.slug;sajt=k/'sajt'
        for d in ('src/pages','dist','public'):(sajt/d).mkdir(parents=True,exist_ok=True)
        for f in ('src/pages/index.astro','dist/index.html'):(sajt/f).write_text('<h1>Syntetiskt helbygge</h1>')
        (sajt/'package.json').write_text('{"dependencies":{}}')
        (sajt/'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        dh=prova.dist_hash(sajt/'dist');korning='20261008T000100Z'
        f=k/'korningar'/korning/'SLUT.json';f.parent.mkdir(parents=True)
        rapport=k/'RAPPORT.md';rapport.write_text('Syntetiskt mekanikprov, ingen kvalitetsdom.')
        metod=granska.aktuell_metod(self.slug)
        status={'ok':True,'dist_sha256':dh,'kallor_sha256':skapande.kallversion(sajt)}
        stopp={'kontroller_grona':True,'korning':korning,'dist_sha256':dh,'slapp':True,
               'rapport_sha256':korslut.sha_fil(rapport),'rapport_korning':korning}
        dom=k/'DOM.json';dom.write_text(json.dumps({'domar':[{'tid':'2026-10-08T00:01:02Z',
            'bygge_dist':dh[:12],'svar':{'namn':korslut.AGAREN_JA}}]}))
        granskning=dict(metod,dist_sha256=dh,godkand=True,runda=1,korning=korning,kriterier={})
        post=korslut.slutpost(k,'0',korning,status,stopp,granskning,dh,None,None,[],[],False,None,0,'Syntetiskt prov')
        f.write_text(json.dumps(post))
        self.assertTrue(post['startsida']['giltig_nu']['varde'])
        self.assertTrue(korslut.aktuell(k)['tillstand']['klart_for_leverans']['varde'])
        self.assertTrue(exportera.exportera(self.slug,bygg=False)['ok'])
        gamla=[f,dom,*list((k/'exporter').glob('*/EXPORT.json'))]
        fore={p:p.read_bytes() for p in gamla}
        metod_fore=granska.aktuell_metod(self.slug)['metod_sha']
        # kundens text ändras: ingår i godkännandets underlag (skapande.UNDERLAGSGRUND) men inte i granskningens metodhash
        (self.u/'TEXTUNDERLAG.md').write_text('Syntetisk ändrad text efter helbygget.')
        self.assertEqual(granska.aktuell_metod(self.slug)['metod_sha'],metod_fore)
        self.assertFalse(skapande.godkand_giltig(self.slug)[0])
        nu=korslut.aktuell(k)
        self.assertIsNone(nu['tillstand']['agaren_godkanner']['varde'])
        self.assertTrue(nu['tillstand']['agaren_godkanner']['historik']['varde'])
        self.assertFalse(nu['tillstand']['klart_for_leverans']['varde'])
        self.assertTrue(any('godkännande' in x for x in nu['provad']['andrat']),nu['provad'])
        self.assertEqual((self.agarbesked()['varde'],self.agarbesked()['status']),(None,'historiskt'))
        ep=exportera.aktuell(self.slug)['tillstand']
        self.assertIsNone(ep['agaren_godkanner']['varde']);self.assertFalse(ep['klart_for_leverans']['varde'])
        self.assertEqual(fore,{p:p.read_bytes() for p in gamla})

    def test_helbyggets_agarbesked_historiskt_ocksa_i_exporten(self):
        import korslut,prova,granska,exportera
        k=self.root/'kunder'/self.slug;sajt=k/'sajt'
        for d in ('src/pages','dist','public'):(sajt/d).mkdir(parents=True)
        for f in ('src/pages/index.astro','dist/index.html'):
            (sajt/f).write_text('<h1>Syntetisk startsida</h1>')
        (sajt/'package.json').write_text('{"dependencies":{}}')
        (sajt/'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        dh=prova.dist_hash(sajt/'dist')
        f=k/'korningar/20261008T000000Z/SLUT.json';f.parent.mkdir(parents=True)
        post={'typ':korslut.TYP,'korning':f.parent.name,'datum':'2026-10-08T00:00:01Z','slutkod':0,
              'dist_sha256':dh,'kallor_sha256':skapande.kallversion(sajt),
              'tillstand':{n:{'varde':True,'text':'Syntetiskt teknikprov, ingen kvalitetsdom'} for n,_ in korslut.TILLSTAND}}
        f.write_text(json.dumps(post));fore=f.read_bytes()
        dom=k/'DOM.json';dom.write_text(json.dumps({'domar':[{'tid':'2026-10-08T00:00:02Z',
            'bygge_dist':dh[:12],'svar':{'namn':korslut.AGAREN_JA}}]}));domfore=dom.read_bytes()
        with patch.object(granska,'aktuell_metod',return_value={}), \
             patch.multiple(exportera,ROOT=self.root,KUNDER=self.root/'kunder',UNDERLAG=self.root/'underlag'):
            self.assertEqual((self.agarbesked()['varde'],self.agarbesked()['status']),(True,'ja'))
            e=exportera.exportera(self.slug,bygg=False)
            self.assertTrue(e['ok']);self.assertFalse(e['klart_for_leverans'])
            self.gor('meddelande',{'text':'Syntetisk ändrad kundkälla efter helbyggets dom.'})
            nu=korslut.aktuell(k)['tillstand']['agaren_godkanner']
            self.assertIsNone(nu['varde']);self.assertTrue(nu['historik']['varde'])
            self.assertEqual((self.agarbesked()['varde'],self.agarbesked()['status']),(None,'historiskt'))
            ep=exportera.aktuell(self.slug)['tillstand']
            self.assertIsNone(ep['agaren_godkanner']['varde']);self.assertFalse(ep['klart_for_leverans']['varde'])
            self.assertEqual(f.read_bytes(),fore);self.assertEqual(dom.read_bytes(),domfore)


if __name__=='__main__':unittest.main()
