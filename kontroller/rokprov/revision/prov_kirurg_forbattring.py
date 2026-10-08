#!/usr/bin/env python3
"""Förbättringsytans riktiga HTTP-ingång, syntetiska signaler och inga modeller."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import prov_kundstart_agare as pa


class Forbattring(unittest.TestCase):
    setUp=pa.Agare.setUp
    req=pa.Agare.req

    def signal(self):
        data={'problem':'syntetiskt-falt','titel':'Syntetisk överföring','fas':'forberedelse','kalla':'Lokal teststörning',
              'version':'v1','observation':'Ett redan insamlat fält föll bort.','belagg':'Syntetiskt prov, ingen riktig kund.'}
        st,d=self.req('POST','/api/kirurg/forbattringar/signal',data)
        self.assertEqual(st,200,d);return d,data

    def test_lasning_startar_inget_och_kand_skrivning_kraver_ursprung(self):
        st,d=self.req('GET','/api/kirurg/forbattringar');self.assertEqual(st,200,d)
        self.assertFalse(d['skapad']);self.assertFalse((self.root/'kirurgen').exists())
        st,_=self.req('POST','/api/kirurg/forbattringar/paus',{'paus':True},origin=False)
        self.assertEqual(st,403);self.assertFalse((self.root/'kirurgen').exists())
        for name in ('forsok','mandat','infor','publicera','shell','registrera-inforande','folj-upp','registrera-aterstallning'):
            self.assertEqual(self.req('POST','/api/kirurg/forbattringar/'+name,{})[0],404)

    def test_observation_diagnos_plan_och_parkering_ar_revisionsbundna(self):
        p,data=self.signal();self.assertEqual(self.req('POST','/api/kirurg/forbattringar/signal',data)[1],p)
        diag={'pid':p['id'],'revision':p['revision'],'slag':'overlamningsfel','skal':'Fältet finns redan.','alternativ':'Kontrollera överföringen.',
              'konsekvens':'stor','belaggsstyrka':'observerat'}
        st,p2=self.req('POST','/api/kirurg/forbattringar/diagnos',diag);self.assertEqual(st,200,p2)
        self.assertEqual(self.req('POST','/api/kirurg/forbattringar/diagnos',diag)[0],400)
        plan={'fraga':'Bevaras fältet?','jamforelse':'Samma data.','framgang':'Fältet bevaras.','forsamring':'Inga uppdiktade fält.',
              'provtyp':'regression','andel':'En funktion.','risk':'Endast isolerad kopia.','ansvarig':'Provroll'}
        st,p3=self.req('POST','/api/kirurg/forbattringar/plan',{'pid':p2['id'],'revision':p2['revision'],'plan':plan});self.assertEqual(st,200,p3)
        st,p4=self.req('POST','/api/kirurg/forbattringar/disposition',{'pid':p3['id'],'revision':p3['revision'],'val':'parkera','skal':'Väntar på försök.','ateroppna':'Nytt belägg.'})
        self.assertEqual(st,200,p4);self.assertEqual(p4['inforande'],'inte_infort')
        st,ur=self.req('POST','/api/kirurg/forbattringar/stickprov',{'seed':'prov','antal':5})
        self.assertEqual(st,200,ur);self.assertEqual(ur['poster'][0]['id'],p4['id'])
        self.assertEqual(self.req('GET','/api/kirurg/forbattringar')[1]['forsok'],{})

    def test_paus_och_trasigt_register_ger_arligt_besked(self):
        self.signal()
        self.assertEqual(self.req('POST','/api/kirurg/forbattringar/paus',{'paus':True})[0],200)
        self.assertTrue(self.req('GET','/api/kirurg/forbattringar')[1]['paus'])
        p=self.root/'kirurgen/forbattringar/FORBATTRINGAR.json';p.write_text('{trasigt')
        st,r=self.req('POST','/api/kirurg/forbattringar/paus',{'paus':False})
        self.assertEqual(st,400,r);self.assertEqual(p.read_text(),'{trasigt')
        st,r=self.req('GET','/api/kirurg/forbattringar');self.assertEqual(st,500,r)

    def test_kallhalsa_kan_lasas_utan_forsok_och_lasfel_ar_synligt(self):
        import kirurg_kallhalsa as h
        rot=self.root/'kirurgen/spaning';rot.mkdir(parents=True)
        h.bokfor(rot,[{'id':'prov','namn':'Provkälla','fel':None}],{'prov':{'hash':'v1'}},[])
        st,d=self.req('GET','/api/kirurg/forbattringar');self.assertEqual(st,200,d)
        self.assertEqual(d['kallhalsa']['kallor']['prov']['status'],'ok');self.assertEqual(d['forsok'],{})
        (rot/'HALSA.json').write_text('{trasigt')
        st,d=self.req('GET','/api/kirurg/forbattringar');self.assertEqual(st,200,d)
        self.assertEqual(d['kallhalsa']['status'],'lasfel');self.assertEqual(d['kallhalsa']['kallor'],{})
        self.assertEqual((rot/'HALSA.json').read_text(),'{trasigt')


if __name__=='__main__':unittest.main()
