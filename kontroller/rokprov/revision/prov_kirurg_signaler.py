#!/usr/bin/env python3
"""Riktiga Kundstart-övergångar med syntetiska svar och avsiktligt tappat fält."""
import json
import contextlib
import sqlite3
import threading
import time
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import prov_kundstart_beredning as pb
import kundstart as ks
import kundstart_beredning as kb
from kirurg_loop import Loop
import kirurg_signaler as s


class Signaler(unittest.TestCase):
    setUp=pb.Beredning.setUp
    gor=pb.Beredning.gor
    forslag=pb.Beredning.forslag
    bekrafta=pb.Beredning.bekrafta

    def lamna(self):
        self.gor('uppgift',{'id':'senare','amne':'A','text':'Syntetisk funktion avstås uttryckligen.','lage':'avstatt'})
        self.forslag();d=self.bekrafta()
        self.repo=self.rot/'repo';self.repo.mkdir()
        self.kvitto=kb.overlamna(self.db,self.e,d['revision'],'signal-prov-ett',self.repo)
        self.loop=Loop(self.repo/'kirurgen/forbattringar')
        self.u=self.repo/'underlag'/d['slug']
        return d

    def test_verklig_overlamning_observeras_utan_att_pasta_anvant_eller_levererat(self):
        self.lamna();self.assertEqual(self.kvitto['kirurg']['status'],'verifierad')
        obs=s.kundstart(self.db,self.e,self.loop)
        self.assertEqual(obs['insamlat'],1);self.assertEqual(obs['overfort'],1)
        self.assertIsNone(obs['anvant']);self.assertIsNone(obs['levererat'])
        self.assertEqual(self.loop.vy()['poster'],{})

    def test_redan_insamlat_som_tappas_ar_overlamningsfel_inte_ny_intervju(self):
        self.lamna();fore=self.db.internt(self.e)
        p=self.u/'KUNDSTART.json';d=json.loads(p.read_text());d['uppgifter']={};p.write_text(json.dumps(d))
        obs=s.kundstart(self.db,self.e,self.loop);self.assertEqual(obs['status'],'overlamningsfel')
        self.assertEqual(obs['overfort'],0)
        post=self.loop.vy()['poster'][obs['forbattring']]
        self.assertEqual(post['diagnoser'][-1]['slag'],'overlamningsfel')
        efter=self.db.internt(self.e)
        self.assertEqual({k:v for k,v in efter.items() if k!='overlamning'},
                         {k:v for k,v in fore.items() if k!='overlamning'},'kunden ska inte få en ny fråga eller ändrat ärende')
        self.assertFalse(efter['overlamning']['aktuell'],'den härledda vyn ska däremot upptäcka att filen ändrats')
        igen=s.kundstart(self.db,self.e,self.loop)
        self.assertEqual(igen['id'],obs['id']);self.assertEqual(len(self.loop.vy()['poster'][post['id']]['signaler']),1)
        self.assertEqual(len(self.loop.vy()['poster'][post['id']]['diagnoser']),1)
        raw=json.dumps(self.loop.vy());self.assertNotIn('Syntetisk funktion',raw);self.assertNotIn('Exempelverkstaden',raw)
        self.assertNotIn(fore['slug'],raw);self.assertNotIn(self.e,raw)

    def test_nya_kundsvar_ar_nytt_underlag_inte_gammal_forlust(self):
        self.lamna();self.gor('uppgift',{'id':'ny','amne':'B','text':'Nytt önskemål efter överlämningen.'})
        obs=s.kundstart(self.db,self.e,self.loop)
        self.assertEqual(obs['status'],'nytt_underlag');self.assertIsNone(obs['overfort'])
        self.assertEqual(self.loop.vy()['poster'],{})

    def test_olast_underlag_och_fallen_observation_sarskiljs(self):
        self.lamna();p=self.u/'KUNDSTART.json';p.write_text('{trasigt')
        obs=s.kundstart(self.db,self.e,self.loop)
        self.assertEqual(obs['status'],'overlamningsfel')
        self.assertIn('overlamnade_filer_kan_inte_verifieras',obs['brister'])
        register=self.loop.rot/'FORBATTRINGAR.json';register.write_text('{trasigt')
        r=kb.overlamna(self.db,self.e,self.kvitto['revision'],'signal-prov-ett',self.repo)
        self.assertEqual(r['status'],'klar');self.assertFalse(r['aktuell'])
        self.assertEqual(r['kirurg']['status'],'observationsfel');self.assertEqual(register.read_text(),'{trasigt')

    def test_observationsfel_doljer_inte_den_sparade_overlamningen(self):
        self.lamna()
        for fel in (sqlite3.OperationalError('syntetiskt läsfel'),RuntimeError('syntetiskt observationsfel')):
            with self.subTest(fel=type(fel).__name__),patch.object(s,'kundstart',side_effect=fel):
                r=kb.overlamna(self.db,self.e,self.kvitto['revision'],'signal-prov-ett',self.repo)
            self.assertEqual(r['status'],'klar');self.assertTrue(r['aktuell']);self.assertEqual(r['kirurg']['status'],'observationsfel')
            self.assertNotIn('syntetiskt läsfel',json.dumps(r));self.assertTrue(kb.aktuell(self.db,self.u))

    def test_aldre_omforsok_far_inte_senaste_overlamningens_matt(self):
        self.lamna();a=self.kvitto
        self.gor('uppgift',{'id':'ny','amne':'B','text':'Ytterligare ett syntetiskt önskemål.'});self.forslag();d=self.bekrafta()
        b=kb.overlamna(self.db,self.e,d['revision'],'signal-prov-tva',self.repo)
        self.assertEqual(b['kirurg']['overfort'],2)
        fore=self.loop.vy()['kundstart']
        r=kb.overlamna(self.db,self.e,a['revision'],'signal-prov-ett',self.repo)
        self.assertEqual(r['id'],'signal-prov-ett');self.assertFalse(r['aktuell'])
        self.assertEqual(r['kirurg']['operation_sha256'],s.hash_('signal-prov-ett'))
        self.assertEqual(r['kirurg']['status'],'ersatt_overlamning');self.assertIsNone(r['kirurg']['overfort'])
        self.assertEqual(self.loop.vy()['kundstart'],fore,'äldre omförsök ska inte ersätta senaste överlämningens observation')

    def test_snapshot_och_publicering_haller_samma_databaslas(self):
        self.lamna();redo=threading.Event();slapp=threading.Event();ny_redo=threading.Event();fel=[]
        original=self.loop.trans
        @contextlib.contextmanager
        def hall():
            if threading.current_thread().name=='aldre-observation':
                redo.set()
                if not slapp.wait(5):raise AssertionError('barriären släpptes inte')
            with original() as d:yield d
        def gammal():
            try:s.kundstart(self.db,self.e,self.loop)
            except BaseException as e:fel.append(e)
        def ny():
            try:
                self.gor('uppgift',{'id':'ny','amne':'B','text':'Senare kundsvar.'})
                s.kundstart(self.db,self.e,self.loop);ny_redo.set()
            except BaseException as e:fel.append(e)
        a=threading.Thread(target=gammal,name='aldre-observation');b=threading.Thread(target=ny)
        with patch.object(self.loop,'trans',hall):
            try:
                a.start();self.assertTrue(redo.wait(3));b.start()
                self.assertFalse(ny_redo.wait(.1),'ny kundrevision passerade äldre snapshots publicering')
            finally:
                slapp.set();a.join(5)
                if b.ident is not None:b.join(5)
        self.assertFalse(a.is_alive());self.assertFalse(b.is_alive());self.assertEqual(fel,[])
        obs=next(iter(self.loop.vy()['kundstart'].values()))
        self.assertEqual(obs['status'],'nytt_underlag');self.assertEqual(obs['insamlat'],2)

    def test_ersatt_kvitto_med_samma_underlag_skapar_inte_falskt_fel(self):
        self.lamna();a=self.kvitto
        b=kb.overlamna(self.db,self.e,a['revision'],'signal-prov-tva',self.repo)
        self.assertEqual(b['kirurg']['status'],'verifierad')
        fore=self.loop.vy()['kundstart']
        r=kb.overlamna(self.db,self.e,a['revision'],'signal-prov-ett',self.repo)
        self.assertEqual(r['kirurg']['status'],'ersatt_overlamning');self.assertIsNone(r['kirurg']['overfort'])
        self.assertEqual(self.loop.vy()['poster'],{});self.assertEqual(self.loop.vy()['kundstart'],fore)


if __name__=='__main__':unittest.main()
