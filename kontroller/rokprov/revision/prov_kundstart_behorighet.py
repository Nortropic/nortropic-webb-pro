#!/usr/bin/env python3
"""Deltagarroller och uttryckligt klarläggande; bara egna syntetiska ärenden."""
import contextlib
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart as ks
import kundstart_behorighet as kh

class Behorighet(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.rot=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-','deltagarprov'))).resolve()
        self.db=ks.Lager(self.rot);self.e,self.token=self.db.skapa('prov-roller','Syntetisk beslutsfattare')
    def gor(self,token,n,data):
        d=self.db.las(self.e,token)
        return self.db.kundhandling(self.e,token,d['revision'],ks.id_(),n,data)
    def inbjud(self,roll,namn='Samma visningsnamn'):
        d=self.db.internt(self.e)
        return kh.bjud_in(self.db,self.e,d['revision'],namn,roll,7)
    def test_lasare_far_inte_andra_och_medverkande_far_inte_bestalla(self):
        r=self.inbjud('lasare');m=self.inbjud('medverkande')
        self.assertTrue(self.db.las(self.e,r['nyckel']))
        with self.assertRaises(ks.Obehorig):self.gor(r['nyckel'],'meddelande',{'text':'Försök till ändring.'})
        self.gor(m['nyckel'],'uppgift',{'id':'mal','amne':'A','text':'Visa tjänsterna.'})
        with self.assertRaises(ks.Obehorig):self.gor(m['nyckel'],'forfragan',{})
        d=self.gor(self.token,'forfragan',{})
        off=self.db.erbjudande(self.e,d['revision'],'En tjänstesida.','Syntetiska villkor.','Provets ägare')
        with self.assertRaises(ks.Obehorig):self.gor(m['nyckel'],'acceptera',{'erbjudande':off['id']})
        self.assertEqual(self.gor(self.token,'acceptera',{'erbjudande':off['id']})['bestallning']['status'],'accepterad')
    def test_samma_namn_ar_olika_deltagare_och_konflikten_kvarstar(self):
        a=self.inbjud('beslutsfattare');b=self.inbjud('beslutsfattare')
        self.assertNotEqual(a['person'],b['person'])
        self.gor(a['nyckel'],'uppgift',{'id':'mal','amne':'A','text':'En riktning.'})
        d=self.gor(b['nyckel'],'uppgift',{'id':'mal','amne':'A','text':'En annan riktning.'})
        self.assertTrue(d['uppgifter']['mal']['motsagelse'])
        d=self.gor(b['nyckel'],'uppgift',{'id':'mal','amne':'A','text':'En tredje formulering.'})
        self.assertTrue(d['uppgifter']['mal']['motsagelse'])
        with self.assertRaises(ks.Vagrad):self.gor(b['nyckel'],'forfragan',{})
        d=self.gor(b['nyckel'],'klarlagg_uppgift',{'id':'mal','text':'Gemensamt avstämd riktning.','skal':'Deltagarna har jämfört alternativen.'})
        self.assertFalse(d['uppgifter']['mal']['motsagelse'])
        self.assertTrue(any(h['slag']=='klarlagd_uppgift' for h in d['historik']))
    def test_aterkallad_person_kan_inte_lasa_eller_repetera_gammal_handling(self):
        m=self.inbjud('medverkande');d=self.db.las(self.e,m['nyckel']);op=ks.id_();data={'text':'Mottaget svar.'}
        self.db.kundhandling(self.e,m['nyckel'],d['revision'],op,'meddelande',data)
        kh.aterkalla_person(self.db,self.e,self.db.internt(self.e)['revision'],m['person'])
        with self.assertRaises(ks.Obehorig):self.db.las(self.e,m['nyckel'])
        with self.assertRaises(ks.Obehorig):self.db.kundhandling(self.e,m['nyckel'],d['revision'],op,'meddelande',data)
        self.assertTrue(self.db.las(self.e,self.token))
    def test_kund_kan_inte_ge_sig_sjalv_roll_eller_invite(self):
        m=self.inbjud('medverkande')
        for n in ('bjud_in','andra_roll','erbjudande','publicera'):
            with self.assertRaises(ks.Vagrad):self.gor(m['nyckel'],n,{'roll':'beslutsfattare'})

if __name__=='__main__':unittest.main()
