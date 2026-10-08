#!/usr/bin/env python3
"""Syntetisk sidbevakning: verklig spana.sida, ingen hämtning från nätet."""
import contextlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import spana
import hamta_sajt


class Transport(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close);self.hits=[]
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                outer.hits.append(self.path)
                if self.path.startswith('/hopp'):
                    n=int(self.path.rsplit('/',1)[-1]);self.send_response(302)
                    self.send_header('Location',f'/hopp/{n+1}' if n<3 else '/klar')
                elif self.path=='/privat':
                    self.send_response(302);self.send_header('Location',f'http://localhost:{self.server.server_port}/hemlig')
                else:self.send_response(200)
                if self.path=='/kort':self.send_header('Content-Length','500')
                self.end_headers()
                if not self.path.startswith('/hopp') and self.path!='/privat':self.wfile.write(b'syntetiskt provsvar')
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stang);self.url=f'http://127.0.0.1:{self.server.server_port}'
        def adress(vard):
            if vard!='127.0.0.1':raise hamta_sajt.NekadAdress('syntetiskt nekat mål')
            return vard
        self.stack.enter_context(patch.object(hamta_sajt,'adress_for',side_effect=adress))
        self.stack.enter_context(patch.object(hamta_sajt,'VIA_PROXY',False))
    def stang(self):self.server.shutdown();self.server.server_close();self.thread.join(2)
    def test_samma_skyddade_transport_vid_start_och_omdirigering(self):
        h=spana.Hamtare(paus=0)
        self.assertEqual(h.hamta(self.url+'/klar'),b'syntetiskt provsvar')
        with self.assertRaises(Exception):h.hamta(self.url+'/privat')
        self.assertNotIn('/hemlig',self.hits)
        with patch.object(hamta_sajt,'adress_for',side_effect=hamta_sajt.NekadAdress('syntetiskt nekad start')):
            with self.assertRaises(Exception):h.hamta(self.url+'/aldrig')
        self.assertNotIn('/aldrig',self.hits)
    def test_hopp_forbrukar_anropstaket_och_trunkering_ar_fel(self):
        h=spana.Hamtare(max_anrop=2,paus=0)
        with self.assertRaises(spana.SlutPaAnrop):h.hamta(self.url+'/hopp/1')
        self.assertEqual(self.hits,['/hopp/1','/hopp/2']);self.assertEqual(h.anrop,2)
        with self.assertRaises(OSError):spana.Hamtare(paus=0).hamta(self.url+'/klar',tak=4)

    def test_for_kort_deklarerat_http_svar_ar_inte_hel_kalla(self):
        with self.assertRaises(OSError):spana.Hamtare(paus=0).hamta(self.url+'/kort')
    def test_varje_hopp_haller_takten_och_andra_scheman_nekas(self):
        with patch.object(spana.time,'sleep') as vila,patch.object(spana.time,'monotonic',return_value=10):
            self.assertEqual(spana.Hamtare(paus=1).hamta(self.url+'/hopp/1'),b'syntetiskt provsvar')
        self.assertEqual(vila.call_count,3)
        with self.assertRaises(hamta_sajt.NekadAdress):spana.Hamtare().hamta('file:///saknas')


class Kallor(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.rot=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kirurg-','syntetisk källbevakning'))).resolve()
        self.stack.enter_context(patch.object(spana,'SPANING',self.rot))
        self.k={'id':'prov','namn':'Syntetisk källa','url':'https://example.invalid/metod','typ':'sida','vikt':1}
        self.snap={}
    def sida(self,text):
        return spana.sida(self.k,spana.Hamtare(hamta=lambda *_:text.encode()),self.snap)
    def test_tillagt_andrat_och_borttaget_samt_dedupe(self):
        a='<p>Behåll kundens tidigare bekräftade svar.</p>'
        b='<p>Bekräfta aldrig en order från modellens eget förslag.</p>'
        self.assertFalse(self.sida(a)[0])
        till=self.sida(a+b)[0];self.assertEqual(len(till),1)
        self.assertIn('andringar',till[0]);self.assertTrue(till[0]['andringar']['tillagda'])
        self.assertFalse(self.sida(a+b)[0])
        andrad=self.sida(a+b.replace('aldrig','bara uttryckligen'))[0]
        self.assertTrue(andrad[0]['andringar']['tillagda']);self.assertTrue(andrad[0]['andringar']['borttagna'])
        bort=self.sida(a)[0];self.assertEqual(len(bort),1)
        self.assertTrue(bort[0]['andringar']['borttagna']);self.assertFalse(bort[0]['andringar']['tillagda'])
        self.assertEqual(len({till[0]['id'],andrad[0]['id'],bort[0]['id']}),3)
        self.assertFalse(spana.dedupe(till,{till[0]['nyckel_override']:{'dom':'nej'}})[0])
        self.assertTrue(spana.dedupe(andrad,{till[0]['nyckel_override']:{'dom':'nej'}})[0])
    def test_datumrad_ar_inte_innovation_men_deadline_bevaras(self):
        innehall='<p>Denna metod behåller en revisionsbunden källkoppling.</p>'
        self.sida('<p>Last updated: 2026-10-01</p>'+innehall)
        self.assertFalse(self.sida('<p>Last updated: 2026-10-02</p>'+innehall)[0])
        self.sida(innehall+'<p>API v1 stöds till 2026-12-01.</p>')
        self.assertTrue(self.sida(innehall+'<p>API v1 stöds till 2026-11-01.</p>')[0])
    def test_korta_rekommendationer_forsvinner_inte(self):
        self.sida('<p>Använd POST.</p>');r=self.sida('<p>Använd GET.</p>')[0]
        self.assertEqual(len(r),1);self.assertIn('Använd POST.',r[0]['andringar']['borttagna'])
    def test_filer_i_samma_repo_ar_olika_kallor(self):
        from kirurg_kallor import identitet
        a=identitet('https://github.com/example/prov/blob/main/ett.md?utm_source=prov')
        b=identitet('https://github.com/example/prov/blob/main/tva.md')
        self.assertNotEqual(a,b);self.assertEqual(a,identitet('https://github.com/example/prov/blob/main/ett.md'))
    def test_trunkerad_eller_olast_snapshot_ar_kallfel(self):
        from kirurg_kallor import Kallfel
        with self.assertRaises(Kallfel):self.sida('x'*spana.BYTE_SIDA)
        self.assertFalse(self.snap)
        (self.rot/'snapshot-prov.json').write_text('{trasig')
        with self.assertRaises(Kallfel):self.sida('<p>Syntetiskt innehåll.</p>')
        self.assertFalse(self.snap)

    def test_kodexempel_ordning_och_antal_ar_innehall(self):
        for a,b in (
            ('<p>Använd &lt;button&gt; för handlingen.</p>','<p>Använd &lt;div&gt; för handlingen.</p>'),
            ('<ol><li>Ta backup.</li><li>Radera.</li></ol>','<ol><li>Radera.</li><li>Ta backup.</li></ol>'),
            ('<p>Spara kvittot.</p>','<p>Spara kvittot.</p><p>Spara kvittot.</p>')):
            with self.subTest(a=a,b=b):
                self.snap={};self.sida(a);r=self.sida(b)[0]
                self.assertEqual(len(r),1,(a,b))
                self.assertTrue(r[0]['andringar']['tillagda'] or r[0]['andringar']['borttagna'])
                self.assertFalse(r[0].get('ny_version'),'ny_version betyder äldre nej i befintliga dashboarden')

    def test_kandidat_sparas_fore_snapshot_sa_omforsok_bevarar_andringen(self):
        state={'v':1}
        def hamta(*_):return ('<p>Behåll denna längre rekommendation i dokumentationen.</p>'+('<p>Ändra kontrollen enligt detta nya dokumenterade krav.</p>' if state['v']==2 else '')).encode()
        spana.spana([self.k],spana.Hamtare(hamta=hamta),kanda={});state['v']=2
        riktig=spana.skriv_json
        def fel(p,d):
            if Path(p).name=='KANDIDATER.json':raise OSError('syntetiskt skrivfel')
            return riktig(p,d)
        with patch.object(spana,'skriv_json',fel),self.assertRaises(OSError):spana.spana([self.k],spana.Hamtare(hamta=hamta),kanda={})
        _,r=spana.spana([self.k],spana.Hamtare(hamta=hamta),kanda={})
        self.assertEqual(len(r),1)
        _,igen=spana.spana([self.k],spana.Hamtare(hamta=hamta),kanda={});self.assertEqual(len(igen),1)


if __name__=='__main__':unittest.main()
