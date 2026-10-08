#!/usr/bin/env python3
"""Kundkapacitet och källhälsa i egna rötter; ingen riktig spaning eller AI."""
import contextlib
import fcntl
import json
import os
import subprocess
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kirurg_drift as drift
import kirurg_kallhalsa as h
import kirurg_loop as kl
import kundstart as ks


class Drift(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kirurg-','syntetisk kapacitetskontroll'))).resolve()
        self.stack.enter_context(patch.object(korregister,'KATALOG',self.root/'register'))
        self.stack.enter_context(patch.object(korregister,'VANTAR',self.root/'register/vantar'))
        self.span=self.root/'kirurgen/spaning';self.span.mkdir(parents=True)
    def test_bygglas_och_vantande_kund_har_foretrade(self):
        drift.kapacitet(self.root)
        p=self.root/'kunder/.bygge.las';p.parent.mkdir()
        with p.open('w') as f:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        drift.kapacitet(self.root)
        korregister.vill_starta(os.getpid())
        with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        korregister.startat(os.getpid());drift.kapacitet(self.root)
    def test_modelllease_i_kundstart_reserverar_kapacitet(self):
        db=ks.Lager(self.root/'underlag/kundstart');e,t=db.skapa('prov-drift','Provroll',modellbudget=1)
        db.kundhandling(e,t,1,'provmeddelande','meddelande',{'text':'Syntetiskt kundsvar.'})
        j=db.ta_jobb('syntetisk-arbetare');self.assertIsNotNone(j)
        with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        db.modellsvar(j,{'text':'Syntetiskt svar.','forslag':[],'fragor':[]});drift.kapacitet(self.root)

    def test_ersatt_jobb_med_aktiv_transport_haller_kundkapaciteten(self):
        import kundstart_modell as km
        db=ks.Lager(self.root/'underlag/kundstart');e,t=db.skapa('prov-drift','Provroll',modellbudget=3)
        db.kundhandling(e,t,1,'provmeddelande','meddelande',{'text':'Syntetiskt första svar.'})
        redo=threading.Event();slapp=threading.Event();fel=[]
        class Adapter:
            modell='syntetisk-attrapp'
            def konfigurerad(self):return True
            def svara(self,d):
                redo.set()
                if not slapp.wait(5):raise AssertionError('adapterbarriären släpptes inte')
                return {'text':'Syntetiskt svar.','forslag':[],'fragor':[]}
        def kor():
            try:km.en_gang(db,Adapter())
            except BaseException as x:fel.append(x)
        th=threading.Thread(target=kor)
        try:
            th.start();self.assertTrue(redo.wait(3))
            d=db.las(e,t);db.kundhandling(e,t,d['revision'],'ny-kundrattelse','meddelande',{'text':'Senare rättelse.'})
            with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        finally:slapp.set();th.join(5)
        self.assertFalse(th.is_alive());self.assertEqual(fel,[]);drift.kapacitet(self.root)

    def test_olast_eller_trasig_korregisterpost_ar_inte_ledig_kapacitet(self):
        p=korregister.registrera('arbetare',pid=os.getpid(),utcheckning=self.root)
        self.assertIsNotNone(p);p.write_text('{trasigt')
        with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        p.write_text(json.dumps({'pid':os.getpid()}))
        with self.assertRaises(kl.Vagrad):drift.kapacitet(self.root)
        p.unlink();drift.kapacitet(self.root)

    def test_specialfil_i_registret_nekas_utan_blockerande_lasning(self):
        korregister.KATALOG.mkdir(exist_ok=True);os.mkfifo(korregister.KATALOG/'123.json')
        code='''import sys
sys.path.insert(0,sys.argv[1])
import kirurg_drift as d
from kirurg_loop import Vagrad
try:d.kapacitet(sys.argv[2])
except Vagrad:print('nekad')
else:raise AssertionError('specialfil räknades som ledig kapacitet')
'''
        r=subprocess.run([sys.executable,'-B','-c',code,str(Path(drift.__file__).parent),str(self.root)],
                         env=dict(os.environ,NWP_KORREGISTER=str(korregister.KATALOG)),capture_output=True,text=True,timeout=2)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'nekad')
        (korregister.KATALOG/'123.json').unlink()
        for rel in ('underlag/kundstart/.transport-prov.las','kunder/.bygge.las'):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);os.mkfifo(p)
            try:
                r=subprocess.run([sys.executable,'-B','-c',code,str(Path(drift.__file__).parent),str(self.root)],
                                 env=dict(os.environ,NWP_KORREGISTER=str(korregister.KATALOG)),capture_output=True,text=True,timeout=2)
                self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),'nekad')
            finally:p.unlink()

    def test_kallfel_bokfors_aven_nar_kandidatlistans_skrivning_faller(self):
        import spana
        k={'id':'prov','namn':'Provkälla','url':'https://example.invalid/metod','typ':'sida','vikt':1}
        with patch.object(spana,'SPANING',self.span):
            spana.spana([k],spana.Hamtare(hamta=lambda *_:b'<p>Bevara uppgiften.</p>'),kanda={})
            vanlig=spana.skriv_json
            def skriv(p,d):
                if p.name=='KANDIDATER.json':raise OSError('Syntetiskt skrivfel')
                return vanlig(p,d)
            def hamta(*_):raise OSError('Syntetiskt transportfel')
            with patch.object(spana,'skriv_json',side_effect=skriv),self.assertRaises(OSError):
                spana.spana([k],spana.Hamtare(hamta=hamta),kanda={})
        self.assertEqual(h.las(self.span)['kallor']['prov']['status'],'fel')
        with self.assertRaises(kl.Vagrad):h.krav(self.span,[{'kalla':'spaning:prov','version':h.las(self.span)['kallor']['prov']['version']}])
    def test_kallfel_bevarar_senaste_lyckade_och_nekar_beroende_forsok(self):
        r={'id':'provkalla','namn':'Syntetisk källa','fel':None}
        d=h.bokfor(self.span,[r],{'provkalla':{'hash':'v1'}},[]);tid=d['kallor']['provkalla']['senast_lyckad']
        signaler=[{'kalla':'spaning:provkalla','version':'v1'}];h.krav(self.span,signaler)
        d=h.bokfor(self.span,[r|{'fel':'Syntetiskt transportfel'}],{},[])
        self.assertEqual(d['kallor']['provkalla']['senast_lyckad'],tid)
        with self.assertRaises(kl.Vagrad):h.krav(self.span,signaler)
        h.krav(self.span,[{'kalla':'lokal teststörning','version':'v1'}])
        h.bokfor(self.span,[r],{'provkalla':{'hash':'v2'}},[])
        with self.assertRaises(kl.Vagrad):h.krav(self.span,signaler)
    def test_andrad_kalla_blir_signal_inte_inforande_och_oforandrad_deduperas(self):
        k={'materiell_andring':True,'version':'v1','kalla_id':'provkalla','dokument':'https://example.invalid/metod',
           'sammanfattning':'En äldre delidé har ändrats.'}
        rapport=[{'id':'provkalla','namn':'Syntetisk källa','fel':None}]
        h.bokfor(self.span,rapport,{'provkalla':{'hash':'v1'}},[k]);h.bokfor(self.span,rapport,{'provkalla':{'hash':'v1'}},[k])
        d=kl.Loop(self.span.parent/'forbattringar').vy();p=next(iter(d['poster'].values()))
        self.assertEqual(len(p['signaler']),1);self.assertEqual(p['inforande'],'inte_infort');self.assertEqual(d['forsok'],{})
        f=self.span/'HALSA.json';f.write_text('{trasigt')
        with self.assertRaises(kl.Vagrad):h.bokfor(self.span,rapport,{},[])
        self.assertEqual(f.read_text(),'{trasigt')


if __name__=='__main__':unittest.main()
