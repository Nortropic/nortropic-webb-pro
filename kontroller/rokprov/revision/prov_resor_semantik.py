#!/usr/bin/env python3
"""Besökarbetydelse genom resor.mjs; syntetisk lokal sida, inga externa anrop."""
import contextlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister

ROOT = Path(__file__).resolve().parents[3]


class Resor(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'semantiska resor'))).resolve()
        self.html = '<!doctype html><html lang="sv"><title>Lokalt prov</title><main><h1>Service</h1></main></html>'
        test = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                data = test.html.encode(); self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(data)
            def log_message(self, *args): pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.stack.callback(self.thread.join, 3); self.stack.callback(self.server.server_close); self.stack.callback(self.server.shutdown)

    def kor(self, steg, ok=True, forvantat=None):
        p=self.tmp/'RESOR.json'; p.write_text(json.dumps({'resor':[{'id':'betydelse','steg':steg,'forvantat':forvantat or []}]}))
        r=subprocess.run(['node',str(ROOT/'kontroller/webblasare/resor.mjs'),'--adress',f'http://127.0.0.1:{self.server.server_port}',
                          '--resor',str(p),'--ut',str(self.tmp/'resultat')],cwd=ROOT,text=True,capture_output=True,timeout=40)
        d=json.loads((self.tmp/'resultat/RESOR.json').read_text())
        self.assertEqual(d['ok'],ok,(r.stdout,r.stderr,d)); self.assertEqual(r.returncode,0 if ok else 1)
        return d

    def sida(self, innehall):
        self.html='<!doctype html><html lang="sv"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Lokalt prov</title><main><h1>Service</h1>'+innehall+'</main></html>'

    def test_samma_besokaruppgift_efter_flyttad_dom(self):
        steg=[{'klicka':{'roll':'button','namn':'Visa kontakt'}}]
        for html in ('<button onclick="this.textContent=\'Kontakt visas\'">Visa kontakt</button>',
                     '<section><div class="ny"><button onclick="this.textContent=\'Kontakt visas\'">Visa kontakt</button></div></section>'):
            self.sida(html); self.kor(steg,forvantat=[{'synlig':{'roll':'button','namn':'Kontakt visas'}}])

    def test_borttaget_tillgangligt_namn_faller(self):
        self.sida('<button aria-label="Annat">Visa kontakt</button>')
        d=self.kor([{'klicka':{'roll':'button','namn':'Visa kontakt'}}],False)
        self.assertIn('0 träffar',d['resor'][0]['skal'])

    def test_dubbletter_kraver_uttryckligt_omrade(self):
        self.sida('<section aria-label="Första"><button>Visa kontakt</button></section><section aria-label="Andra"><button>Visa kontakt</button></section>')
        d=self.kor([{'klicka':{'roll':'button','namn':'Visa kontakt'}}],False)
        self.assertIn('2 träffar',d['resor'][0]['skal'])
        self.kor([{'klicka':{'roll':'button','namn':'Visa kontakt','inom':{'roll':'region','namn':'Andra'}}}])

    def test_fyll_och_faltnara_fel_via_etikett(self):
        self.sida('<form aria-label="Kontakt"><label for="valfri">Meddelande</label><input id="valfri" required aria-describedby="fel"><p id="fel">Skriv ett meddelande</p></form>')
        self.kor([{'forvanta':{'fel_vid_falt':{'etikett':'Meddelande'}}},
                  {'fyll':[{'falt':{'etikett':'Meddelande'},'varde':'Syntetiskt meddelande'}]},
                  {'vanta':{'roll':'form','namn':'Kontakt'}}])

    def test_semantisk_lank_och_gammal_css_fungerar(self):
        self.sida('<a href="mailto:prov@example.invalid">Skriv</a><button id="visa">Visa</button>')
        self.kor([{'klicka':'#visa'}],forvantat=[{'lank':{'valjare':{'roll':'link','namn':'Skriv'},'borjar':'mailto:'}}, {'synlig':'#visa'}])

    def test_okand_eller_tvetydig_väljarform_avvisas(self):
        self.sida('<button>Visa</button>')
        for sel in ({'roll':'button','namn':'Visa','index':0},{'roll':'button','etikett':'Visa'},{'roll':'button'}, {'roll':'button','namn':'Visa','inom':'main'}):
            with self.subTest(sel=sel):
                d=self.kor([{'klicka':sel}],False); self.assertIn('väljare',d['resor'][0]['skal'])

    def test_omradet_maste_ocksa_vara_entydigt(self):
        self.sida('<section aria-label="Kontakt"><p>Ingen knapp här</p></section><section aria-label="Kontakt"><button>Visa</button></section>')
        d=self.kor([{'klicka':{'roll':'button','namn':'Visa','inom':{'roll':'region','namn':'Kontakt'}}}],False)
        self.assertIn('2 träffar',d['resor'][0]['skal'])

    def test_namnet_ar_exakt_och_dolda_kontroller_raknas_inte(self):
        self.sida('<button hidden>Visa</button><button>Visa</button><button>Visa mer</button>')
        self.kor([{'klicka':{'roll':'button','namn':'Visa'}}])


if __name__=='__main__': unittest.main()
