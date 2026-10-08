#!/usr/bin/env python3
"""Returfrågor och integrationsbelägg i ett syntetiskt, beständigt ärende."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import prov_kundstart_beredning as grundprov
import kundstart as ks
import kundstart_beredning as kb
import kundstart_fortsatt as kf


class Fortsatt(unittest.TestCase):
    gor=grundprov.Beredning.gor
    forslag=grundprov.Beredning.forslag
    bekrafta=grundprov.Beredning.bekrafta
    def setUp(self):
        grundprov.Beredning.setUp(self);self.bekrafta();self.repo=self.rot/'repo';self.repo.mkdir()
        d=self.db.las(self.e,self.token)
        self.export=kb.overlamna(self.db,self.e,d['revision'],'overlamning-for-retur',self.repo)

    def test_returen_hor_till_samma_arende_och_overlamningsversion(self):
        d=self.db.internt(self.e)
        q={'id':'kontaktvag','amne':'F','text':'Vem tar emot en inskickad förfrågan?',
           'varfor':'Mottagaren saknas i underlaget.','fas':'helbygge','kritisk':True,'ansvarig':'kund'}
        r=kf.returfraga(self.db,self.e,d['revision'],self.export['id'],q)
        again=kf.returfraga(self.db,self.e,d['revision'],self.export['id'],q)
        self.assertEqual(r,again)
        d=self.db.las(self.e,self.token);self.assertEqual(len(d['returfragor']),1)
        self.assertEqual(r['kallrevision'],self.export['revision']);self.assertEqual(r['status'],'oppen')
        before=d['revision'];d=self.gor('besvara_fraga',{'id':q['id'],'text':'Det vet vi inte än. Hjälp oss välja.','lage':'vet_inte'})
        self.assertEqual(d['returfragor'][q['id']]['status'],'vet_inte')
        self.assertGreater(d['revision'],before);self.assertEqual(d['meddelanden'][-1]['fraga'],q['id'])
        self.assertEqual(d['bestallning']['status'],'utkast');self.assertEqual(d['modell']['status'],'ko')
        self.assertFalse(kb.aktuell(self.db,self.repo/'underlag'/d['slug']))

    def test_frammande_export_och_modelleftersvar_ger_ingen_returfakt(self):
        d=self.db.internt(self.e);q={'id':'fraga','amne':'A','text':'Vilket mål?', 'varfor':'Saknas','fas':'skiss','kritisk':True,'ansvarig':'kund'}
        with self.assertRaises(ks.Vagrad):kf.returfraga(self.db,self.e,d['revision'],'annan-export',q)
        with self.assertRaises(ks.Vagrad):self.gor('besvara_fraga',{'id':'fraga','text':'Svar','lage':'svarad'})
        self.assertEqual(self.db.las(self.e,self.token)['revision'],d['revision'])

    def test_integrationsbehov_blandas_inte_med_konto_eller_funktionsprov(self):
        d=self.gor('integrationsbehov',{'id':'bokning','behov':'Besökaren väljer en ledig tid.',
            'uppgift':'Boka och kunna avboka.','befintligt':'Kunden använder ett befintligt bokningssystem.',
            'ansvarig':'Kundens administratör','dataflode':'Namn och tid till mottagaren.',
            'aterkoppling':'Bekräftelse och återförsök utan dubblering.','lage':'onskemal'})
        i=d['integrationer']['bokning'];self.assertEqual(i['utredning']['konto']['status'],'okant')
        self.assertEqual(i['utredning']['prov']['status'],'inte_provat')
        # Ägaren kan ange daterad dokumentation utan att påstå fungerande konto.
        bevis={'leverantor':{'status':'dokumenterat','kalla':'https://example.org/docs','datum':'2026-10-08',
                            'sha256':'a'*64,'besked':'En API-väg är dokumenterad i det syntetiska provet.'},
               'konto':{'status':'okant'},'prov':{'status':'inte_provat'},
               'vag':'api','villkor':'Kontots åtkomst och kostnad behöver prövas.'}
        d=kf.utred_integration(self.db,self.e,d['revision'],'bokning',i['behov_sha256'],bevis)
        i=d['integrationer']['bokning'];self.assertEqual(i['utredning']['leverantor']['status'],'dokumenterat')
        self.assertFalse(kf.integration_klar(i));self.assertFalse(i['utredning']['prov'].get('godkant',False))
        with self.assertRaises(ks.Vagrad):self.gor('integrationsbehov',{'id':'bokning','behov':'X','konto':{'status':'tillgang_bekraftad'}})
        # Ändrat behov bevarar det äldre belägget men gör det inaktuellt.
        d=self.gor('integrationsbehov',{'id':'bokning','behov':'Även betalning i bokningen.','uppgift':'Boka och betala.',
            'befintligt':'Befintlig tjänst','ansvarig':'Kunden','dataflode':'Utreds','aterkoppling':'Utreds','lage':'onskemal'})
        self.assertFalse(kf.integration_klar(d['integrationer']['bokning']))
        self.assertEqual(d['integrationer']['bokning']['utredning']['status'],'inaktuell')
        self.assertEqual(d['bestallning']['status'],'utkast')

    def test_ett_inte_provat_prov_kan_inte_fa_lokalt_godkannande_utan_bevis(self):
        d=self.gor('integrationsbehov',{'id':'kontakt','behov':'Skicka fråga.','uppgift':'Från formulär till mottagare.',
            'befintligt':'Inget','ansvarig':'Kunden','dataflode':'Kontaktuppgifter','aterkoppling':'Kvittens','lage':'onskemal'})
        b={'leverantor':{'status':'okant'},'konto':{'status':'okant'},'prov':{'status':'lokalt_provat'},'vag':'inbyggd','villkor':'Utreds'}
        with self.assertRaises(ks.Vagrad):kf.utred_integration(self.db,self.e,d['revision'],'kontakt',d['integrationer']['kontakt']['behov_sha256'],b)

    def test_integrationskundens_kalla_gar_genom_den_riktiga_modellpubliceringen(self):
        d=self.gor('integrationsbehov',{'id':'kontakt','behov':'Skicka fråga.','uppgift':'Från formulär till mottagare.',
            'befintligt':'Inget','ansvarig':'Kunden','dataflode':'Kontaktuppgifter','aterkoppling':'Kvittens','lage':'onskemal'})
        jobb=self.db.ta_jobb('provmodell');self.assertIsNotNone(jobb)
        kallid=d['integrationer']['kontakt']['kalla']
        from kundstart_modell import kontext
        self.assertIn(kallid,kontext(jobb['dokument']))
        self.assertTrue(self.db.modellsvar(jobb,{'text':'Vi behöver undersöka mottagningen.','fragor':[],
            'forslag':[{'id':'mottagning','amne':'F','text':'Utred kvittens och omförsök.','kunskap':'tolkning','kallor':[kallid]}]}))

    def test_aldre_assistentpastaende_ar_ingen_sjalvstandig_kundkalla(self):
        d=self.gor('meddelande',{'text':'Fortsätt utreda.'})
        aid=next(m['id'] for m in d['meddelanden'] if m['roll']=='assistent')
        jobb=self.db.ta_jobb('provmodell');self.assertIsNotNone(jobb)
        with self.assertRaises(ks.Vagrad):
            self.db.modellsvar(jobb,{'text':'Förslag','fragor':[],
                'forslag':[{'id':'ny-tolkning','amne':'A','text':'Nytt förslag.','kunskap':'tolkning','kallor':[aid]}]})
        self.assertNotIn('ny-tolkning',self.db.las(self.e,self.token)['forslag'])

    def test_andrat_integrationsunderlag_kan_inte_bekrafta_eller_exportera_aldre_forslag(self):
        behov={'id':'kontakt','behov':'Skicka fråga.','uppgift':'Från formulär till mottagare.',
            'befintligt':'Inget','ansvarig':'Kunden','dataflode':'Kontaktuppgifter','aterkoppling':'Kvittens','lage':'onskemal'}
        d=self.gor('integrationsbehov',behov);jobb=self.db.ta_jobb('provmodell')
        mid=d['integrationer']['kontakt']['kalla']
        self.db.modellsvar(jobb,{'text':'Stäm av uppgifterna.','forslag':[],'fragor':[],
            'verksamhet':{'varden':self.v,'kallor':{k:[mid] for k in self.v}}})
        d=self.bekrafta();kb.paket(d);fore=kb.grund(d);fsha=d['verksamhet_forslag']['sha256']
        d=self.gor('integrationsbehov',dict(behov,behov='En annan mottagare och uppgift.'))
        self.assertNotEqual(kb.grund(d),fore)
        with self.assertRaises(ks.Vagrad):kb.paket(d)
        with self.assertRaises(ks.Vagrad):self.gor('bekrafta_verksamhet',{'sha256':fsha})
        with self.assertRaises(ks.Vagrad):kb.overlamna(self.db,self.e,d['revision'],'andrat-behov',self.repo)

    def test_kunden_far_beskriva_behov_utan_att_veta_tekniken(self):
        d=self.gor('integrationsbehov',{'id':'bokningsonskan','behov':'Besökaren ska kunna boka en ledig tid.','lage':'onskemal'})
        i=d['integrationer']['bokningsonskan']
        self.assertIsNone(i['dataflode']);self.assertIsNone(i['aterkoppling'])
        self.assertEqual(i['kallstatus']['dataflode'],'okant')
        self.assertEqual(i['kallstatus']['behov'],'kunden_uppger')
        self.assertEqual(i['utredning']['konto']['status'],'okant');self.assertFalse(kf.integration_klar(i))

    def test_mottaget_svar_ar_inte_automatiskt_klarlagd_kritisk_fraga(self):
        import kundstart_agare as ka
        d=self.db.internt(self.e)
        q={'id':'viktig','amne':'A','text':'Vilken uppgift är viktigast?','varfor':'Styr skissen.',
           'fas':'skiss','kritisk':True,'ansvarig':'kund'}
        kf.returfraga(self.db,self.e,d['revision'],self.export['id'],q)
        d=self.gor('besvara_fraga',{'id':'viktig','text':'Vi behöver hjälp att bestämma det.','lage':'svarad'})
        with patch.object(kb,'paket',return_value={}):
            f=ka.faser(d,self.repo)
        self.assertTrue(f['forberedelse']['kan_starta']);self.assertFalse(f['skiss']['kan_starta'])
        q=d['returfragor']['viktig']
        d=kf.klarlagg_retursvar(self.db,self.e,d['revision'],'viktig',kf.svaridentitet(d,q),
                              'Intern hypotes avgränsad till skiss; inget nytt åtagande.','Syntetisk ansvarig')
        with patch.object(kb,'paket',return_value={}):self.assertTrue(ka.faser(d,self.repo)['skiss']['kan_starta'])
        d=self.gor('besvara_fraga',{'id':'viktig','text':'Vi behöver nu en annan uppgift.','lage':'svarad'})
        with patch.object(kb,'paket',return_value={}):self.assertFalse(ka.faser(d,self.repo)['skiss']['kan_starta'])


if __name__=='__main__':unittest.main()
