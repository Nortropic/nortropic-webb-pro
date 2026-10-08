#!/usr/bin/env python3
"""Källbundet underlag från syntetiskt kundärende; inga sessioner eller extern åtkomst."""
import contextlib
import json
import shutil
import subprocess
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart
import kundstart_beredning as kb


class Beredning(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.rot=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-','syntetisk överlämning'))).resolve()
        self.db=kundstart.Lager(self.rot/'privat')
        self.e,self.token=self.db.skapa('prov-beredning','Syntetisk kund',modellbudget=10)
        self.gor('meddelande',{'text':'Exempelverkstaden arbetar nationellt med reparationer. Kontaktväg kommer senare.'})
        self.v={'namn':'Exempelverkstaden','kontaktvagar':[],'rackvidd':{'typ':'nationell'},'tjanster':['Reparationer']}
        self.forslag()

    def gor(self,n,data):
        d=self.db.las(self.e,self.token)
        return self.db.kundhandling(self.e,self.token,d['revision'],kundstart.id_(),n,data)

    def forslag(self):
        jobb=self.db.ta_jobb('beredare')
        self.assertIsNotNone(jobb)
        mid=jobb['dokument']['meddelanden'][0]['id']
        return self.db.modellsvar(jobb,{'text':'Stämmer grunduppgifterna nedan?','forslag':[],'fragor':[],
            'verksamhet':{'varden':self.v,'kallor':{k:[mid] for k in self.v}}})

    def bekrafta(self):
        d=self.db.las(self.e,self.token)
        return self.gor('bekrafta_verksamhet',{'sha256':d['verksamhet_forslag']['sha256']})

    def test_modellforslag_ar_inte_verifierade_grunduppgifter(self):
        d=self.db.las(self.e,self.token)
        self.assertIsNone(d['verksamhet'])
        with self.assertRaises(kundstart.Vagrad):kb.paket(d)
        d=self.bekrafta();p=kb.paket(d)
        self.assertNotIn('UPPDRAG.md',p)
        v=json.loads(p['VERKSAMHET.json']);self.assertEqual(v['namn'],self.v['namn']);self.assertTrue(v['fiktiv'])
        b=json.loads(p['KUNDSTART.json']);self.assertEqual(b['bestallning']['status'],'utkast')
        self.assertFalse(b['helbygge_tillatet']);self.assertIn('kallor',b['verksamhet'])
        for fel in ('RESEARCH.md','BRIEF.md','INNEHALL.md','RESOR.json'):self.assertNotIn(fel,p)

    def test_forfragan_och_accepterad_omfattning_exporteras_olika(self):
        self.bekrafta();self.gor('uppgift',{'id':'mal','amne':'A','text':'Tydlig tjänstesida.'})
        self.forslag();self.bekrafta();d=self.gor('forfragan',{})
        self.assertNotIn('UPPDRAG.md',kb.paket(d))
        off=self.db.erbjudande(self.e,d['revision'],'Tjänstesida utan betalning.','Inga datumlovanden.','Syntetisk ägare')
        d=self.gor('acceptera',{'erbjudande':off['id']})
        p=kb.paket(d);self.assertIn('UPPDRAG.md',p);self.assertIn('Tjänstesida utan betalning.',p['UPPDRAG.md'])
        self.assertFalse(json.loads(p['KUNDSTART.json'])['helbygge_tillatet'],'designgodkännandet prövas separat')

    def test_sen_kundrattelse_kraver_ny_kallbunden_sammanstallning(self):
        d=self.bekrafta();kb.paket(d)
        d=self.gor('meddelande',{'text':'Rättelse: vi gör inte längre reparationer.'})
        with self.assertRaises(kundstart.Vagrad):kb.paket(d)
        with self.assertRaises(kundstart.Vagrad):self.gor('bekrafta_verksamhet',{'sha256':d['verksamhet_forslag']['sha256']})

    def test_okand_modellkalla_och_fiktiv_flagga_kan_inte_inforas(self):
        self.gor('meddelande',{'text':'Fortsätt.'});jobb=self.db.ta_jobb('beredare')
        for v,k in [(dict(self.v,fiktiv=False),{x:['saknas'] for x in self.v}),(self.v,{x:['saknas'] for x in self.v})]:
            with self.subTest(v=v),self.assertRaises(kundstart.Vagrad):
                self.db.modellsvar(jobb,{'text':'Förslag','forslag':[],'fragor':[],'verksamhet':{'varden':v,'kallor':k}})
        self.assertIsNone(self.db.las(self.e,self.token)['verksamhet'])

    def test_overlamning_aterforsok_och_material(self):
        self.bekrafta();self.gor('bilaga',{'namn':'material.txt','typ':'text/plain','data':'c3ludGV0aXNrdA=='})
        d=self.db.las(self.e,self.token);repo=self.rot/'repo';repo.mkdir()
        a=kb.overlamna(self.db,self.e,d['revision'],'overlamning-ett',repo)
        b=kb.overlamna(self.db,self.e,d['revision'],'overlamning-ett',repo)
        self.assertEqual(a,b);self.assertEqual(a['status'],'klar')
        u=repo/'underlag'/d['slug'];kv=json.loads((u/'KUNDSTART.json').read_text())
        self.assertEqual(kv['status'],'klar');self.assertFalse((u/'UPPDRAG.md').exists())
        self.assertEqual(len(list((u/'kundstart/material').rglob('material.txt'))),1)
        self.assertTrue(kb.aktuell(self.db,u))
        self.gor('meddelande',{'text':'Vi behöver ändra inriktningen.'})
        self.assertFalse(kb.aktuell(self.db,u),'ärendet ändrades utan att byggfilerna hunnit skrivas om')

    def test_delvis_publicering_kan_aterupptas_men_ar_inte_klar(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir()
        vanlig=kb.atomiskt
        def fel(p,b):
            if p.name=='VERKSAMHET.json' and p.parent.name==d['slug']:raise OSError('syntetiskt skrivfel')
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=fel),self.assertRaises(OSError):
            kb.overlamna(self.db,self.e,d['revision'],'overlamning-delvis',repo)
        u=repo/'underlag'/d['slug'];self.assertFalse(kb.aktuell(self.db,u))
        self.assertEqual(json.loads((u/'KUNDSTART.json').read_text())['status'],'publicerar')
        p=kb.overlamna(self.db,self.e,d['revision'],'overlamning-delvis',repo)
        self.assertEqual(p['status'],'klar');self.assertTrue(kb.aktuell(self.db,u))

    def test_symlank_och_frammande_underlag_vagras(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir();(repo/'underlag').mkdir()
        ut=self.rot/'annan';ut.mkdir();(repo/'underlag'/d['slug']).symlink_to(ut)
        with self.assertRaises(kundstart.Vagrad):kb.overlamna(self.db,self.e,d['revision'],'overlamning-nej',repo)
        self.assertEqual(list(ut.iterdir()),[])
        (repo/'underlag'/d['slug']).unlink();u=repo/'underlag'/d['slug'];u.mkdir();(u/'RESEARCH.md').write_text('Främmande provunderlag')
        with self.assertRaises(kundstart.Vagrad):kb.overlamna(self.db,self.e,d['revision'],'overlamning-nej2',repo)
        self.assertEqual((u/'RESEARCH.md').read_text(),'Främmande provunderlag')

    def test_kvittot_prövar_både_källärendet_och_de_skrivna_filerna(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir()
        p=kb.overlamna(self.db,self.e,d['revision'],'overlamning-kvitto',repo)
        self.assertTrue(p['aktuell']);self.assertTrue(self.db.las(self.e,self.token)['overlamning']['aktuell'])
        u=repo/'underlag'/d['slug'];(u/'VERKSAMHET.json').write_text('{}')
        self.assertFalse(kb.aktuell(self.db,u))
        self.assertFalse(kb.overlamna(self.db,self.e,d['revision'],'overlamning-kvitto',repo)['aktuell'])
        self.assertFalse(self.db.las(self.e,self.token)['overlamning']['aktuell'])

    def test_samma_filer_under_annan_rot_ar_ingen_giltig_overlamning(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir()
        kb.overlamna(self.db,self.e,d['revision'],'overlamning-rot',repo)
        u=repo/'underlag'/d['slug'];annat=repo/'annan-katalog'/d['slug']
        shutil.copytree(u,annat)
        self.assertFalse(kb.aktuell(self.db,annat));self.assertTrue(kb.aktuell(self.db,u))

    def test_kundrattelse_efter_avbrott_kan_aterstallas_och_overlamnas_pa_nytt(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir();vanlig=kb.atomiskt
        def fel(p,b):
            if p.name=='VERKSAMHET.json' and p.parent.name==d['slug']:raise OSError('syntetiskt skrivfel')
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=fel),self.assertRaises(OSError):
            kb.overlamna(self.db,self.e,d['revision'],'overlamning-fallen',repo)
        self.gor('meddelande',{'text':'Nytt önskemål: en enklare kontaktsida.'});self.forslag();nu=self.bekrafta()
        self.assertFalse(kb.aktuell(self.db,repo/'underlag'/d['slug']))
        kv=kb.aterstall_overlamning(self.db,self.e,'overlamning-fallen',repo)
        self.assertEqual(kv['status'],'avbruten');self.assertFalse(kv['aktuell'])
        self.assertEqual(kb.aterstall_overlamning(self.db,self.e,'overlamning-fallen',repo),kv)
        p=kb.overlamna(self.db,self.e,nu['revision'],'overlamning-ny',repo)
        self.assertTrue(p['aktuell']);self.assertTrue(kb.aktuell(self.db,repo/'underlag'/d['slug']))

    def test_arbetslas_finns_ocksa_fore_forsta_bygget(self):
        repo=self.rot/'repo';repo.mkdir();u=repo/'underlag/prov-las';u.mkdir(parents=True)
        with kb.arbetslas(u,repo):
            lock=repo/'kunder/.bygge.las'
            self.assertTrue(lock.is_file())
            code='import fcntl,sys; f=open(sys.argv[1],"a"); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)'
            r=subprocess.run([sys.executable,'-c',code,str(lock)],capture_output=True)
            self.assertNotEqual(r.returncode,0);self.assertIn(b'BlockingIOError',r.stderr)
        (repo/'kunder/.bygge-pid').symlink_to(repo/'saknad')
        with self.assertRaises(kundstart.Vagrad):
            with kb.arbetslas(u,repo):self.fail('hängande äldre PID-länk släpptes')

    def test_aterstallning_bevarar_foreversion_och_vagrar_frammande_andring(self):
        d=self.bekrafta();repo=self.rot/'repo';repo.mkdir()
        kb.overlamna(self.db,self.e,d['revision'],'overlamning-fore',repo)
        u=repo/'underlag'/d['slug'];fore={n:(u/n).read_bytes() for n in ('KUNDSTART.json','VERKSAMHET.json')}
        self.gor('meddelande',{'text':'Ny beskrivning.'});self.forslag();d=self.bekrafta()
        vanlig=kb.atomiskt
        def fel(p,b):
            if p.name=='KUNDSTART.json' and p.parent==u and json.loads(b)['status']=='klar':raise OSError('syntetiskt slutbytesfel')
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=fel),self.assertRaises(OSError):
            kb.overlamna(self.db,self.e,d['revision'],'overlamning-efter',repo)
        vf=u/'VERKSAMHET.json';efter=vf.read_bytes();vf.write_text('främmande ändring')
        med_fore={n:(u/n).read_bytes() for n in fore}
        with self.assertRaises(kundstart.Vagrad):kb.aterstall_overlamning(self.db,self.e,'overlamning-efter',repo)
        self.assertEqual({n:(u/n).read_bytes() for n in fore},med_fore)
        vf.write_bytes(efter)
        kb.aterstall_overlamning(self.db,self.e,'overlamning-efter',repo)
        self.assertEqual({n:(u/n).read_bytes() for n in fore},fore)
        self.assertFalse(kb.aktuell(self.db,u),'återställda filer är äldre än det ändrade ärendet')
        self.assertTrue(kb.overlamna(self.db,self.e,d['revision'],'overlamning-om',repo)['aktuell'])


if __name__=='__main__':unittest.main()
