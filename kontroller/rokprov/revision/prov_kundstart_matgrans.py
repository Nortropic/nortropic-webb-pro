#!/usr/bin/env python3
"""Transport, hårt avbrott och gallring. Bara lokala attrapper och egen SQLite."""
import contextlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart as ks
import kundstart_modell as km
import kundstart_matt as matt
import kundstart_lagring as kl


def svar():
    return {'type':'message','stop_reason':'end_turn','content':[{'type':'text','text':json.dumps({'text':'Syntetiskt svar','forslag':[],'fragor':[]})}]}


class Matgrans(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-','syntetiska transportgränser'))).resolve()
        self.db=ks.Lager(self.root/'privat');self.e,self.t=self.db.skapa('prov-matgrans','Provperson',modellbudget=5)
        kl.lagringsbeslut(self.db,self.e,self.db.internt(self.e)['revision'],time.time()-10,'syntetiskt','Provroll')
        self.db.kundhandling(self.e,self.t,self.db.internt(self.e)['revision'],ks.id_(),'meddelande',{'text':'Syntetiskt underlag'})

    def test_ingen_metodhash_fore_transportunderlaget_finns(self):
        with patch.object(km,'kontext',side_effect=km.Modellfel('kontextgrans')):
            result=km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:self.fail('transport får inte starta')))
        self.assertEqual(result['slag'],'kontextgrans')
        self.assertIsNone(matt.lista(self.db,self.e)[0]['metod_sha256'])

    def test_saknad_metod_klassas_lika_i_arende_och_forsok(self):
        with patch.object(km,'METODFIL',self.root/'saknad.md'):
            result=km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:self.fail('transport får inte starta')))
        self.assertEqual(self.db.internt(self.e)['modell']['slag'],result['slag'])

    def test_lease_och_forsok_reserveras_atomiskt(self):
        self.db.ta_jobb('prov-arbetare')
        self.assertEqual(len(matt.lista(self.db,self.e)),self.db.internt(self.e)['budget']['anrop'])

    def test_ersatt_jobbs_utgangna_lease_avslutar_ocksa_forsoket(self):
        self.db.ta_jobb('syntetiskt-dott-jobb')
        self.db.kundhandling(self.e,self.t,self.db.internt(self.e)['revision'],ks.id_(),'meddelande',{'text':'Syntetisk senare rättelse'})
        with self.db.trans() as c:c.execute('UPDATE jobb SET lease_slut=0 WHERE lease_id IS NOT NULL')
        km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:svar()))
        self.assertEqual([m['status'] for m in matt.lista(self.db,self.e)],['avbruten','klar'])

    def test_utgangen_lease_avslutar_gammalt_forsok_utan_att_gissa_tid(self):
        self.db.ta_jobb('prov-arbetare')
        with self.db.trans() as c:c.execute("UPDATE jobb SET lease_slut=0 WHERE status='pagar'")
        km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:svar()))
        rows=matt.lista(self.db,self.e)
        self.assertEqual([m['status'] for m in rows],['avbruten','klar'])
        self.assertEqual(rows[0]['slag'],'lease_utgangen');self.assertIsNone(rows[0]['sekunder'])

    def test_gallring_mellan_reservation_och_transport_nekar_sandning(self):
        original=self.db.ta_jobb
        def reservera(*args,**kwargs):
            jobb=original(*args,**kwargs)
            kl.gallra(self.db,self.e,self.db.internt(self.e)['revision'])
            return jobb
        with patch.object(self.db,'ta_jobb',side_effect=reservera):
            result=km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:self.fail('gallrat underlag skickades')))
        self.assertEqual(result['status'],'ersatt')
        with self.db.trans() as c:self.assertEqual(c.execute('SELECT count(*) FROM modellanrop').fetchone()[0],0)

    def test_gallring_vantar_pa_borjad_transport_men_kundsvar_kan_sparas(self):
        borjad=threading.Event();slapp=threading.Event();gallrad=threading.Event();fel=[]
        def transport(_):borjad.set();self.assertTrue(slapp.wait(5));return svar()
        def modell():
            try:km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,transport))
            except BaseException as e:fel.append(e)
        worker=threading.Thread(target=modell);worker.start();self.assertTrue(borjad.wait(5))
        try:
            self.db.kundhandling(self.e,self.t,self.db.internt(self.e)['revision'],ks.id_(),'meddelande',{'text':'Syntetisk rättelse under anrop'})
            def radera():
                try:kl.gallra(self.db,self.e,self.db.internt(self.e)['revision']);gallrad.set()
                except BaseException as e:fel.append(e)
            remover=threading.Thread(target=radera);remover.start()
            self.assertFalse(gallrad.wait(.15),'gallringen blev klar medan transporten fortfarande körde')
        finally:slapp.set();worker.join(5);remover.join(5)
        self.assertFalse(worker.is_alive());self.assertFalse(remover.is_alive());self.assertFalse(fel,repr(fel));self.assertTrue(gallrad.is_set())

    def test_hart_avbrott_bevarar_forberett_forsok_senare_aterforsok_avslutar_det(self):
        code="""import os,signal,sys
sys.path.insert(0,sys.argv[1]);import kundstart as ks,kundstart_modell as km
def transport(p):os.kill(os.getpid(),signal.SIGKILL)
km.en_gang(ks.Lager(sys.argv[2]),km.ClaudeAPI('syntetisk',True,transport))
"""
        child=subprocess.run([sys.executable,'-B','-c',code,str(Path(ks.__file__).parent),str(self.db.rot)],timeout=10)
        self.assertEqual(child.returncode,-signal.SIGKILL)
        rows=matt.lista(self.db,self.e);self.assertEqual(len(rows),1)
        self.assertTrue(rows[0]['metod_sha256']);self.assertEqual(rows[0]['transportlage'],'forberedd')
        with self.db.trans() as c:c.execute("UPDATE jobb SET lease_slut=0 WHERE status='pagar'")
        km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:svar()))
        self.assertEqual([m['status'] for m in matt.lista(self.db,self.e)],['avbruten','klar'])

    def test_hart_avbrott_inne_i_reservationen_backar_budget_och_lease(self):
        code="""import os,signal,sys
sys.path.insert(0,sys.argv[1]);import kundstart as ks,kundstart_matt as matt
def bryt(*a,**kw):os.kill(os.getpid(),signal.SIGKILL)
matt.start=bryt
ks.Lager(sys.argv[2]).ta_jobb('syntetiskt-avbrott')
"""
        child=subprocess.run([sys.executable,'-B','-c',code,str(Path(ks.__file__).parent),str(self.db.rot)],timeout=10)
        self.assertEqual(child.returncode,-signal.SIGKILL)
        self.assertEqual(self.db.internt(self.e)['budget']['anrop'],0)
        self.assertEqual(matt.lista(self.db,self.e),[])
        km.en_gang(self.db,km.ClaudeAPI('syntetisk',True,lambda _:svar()))
        self.assertEqual(self.db.internt(self.e)['budget']['anrop'],1)
        self.assertEqual([m['status'] for m in matt.lista(self.db,self.e)],['klar'])


if __name__=='__main__':unittest.main()
