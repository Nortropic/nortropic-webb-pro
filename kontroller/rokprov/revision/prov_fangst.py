#!/usr/bin/env python3
"""Fångsten av främmande sajter (inspektera.mjs --samtycke och --lugn; kalibreringen, ägarens uppdrag 2026-10-09,
punkt 2): en samtyckesdialog stängs med sitt eget val, också när knappen är en text utan roll, men bara inne i dialogen;
första vyn fotograferas när sidans ändliga animationer är klara, och en oändlig animation väntas inte ut. Utan
flaggorna är fångsten som förut. Syntetisk sida på 127.0.0.1; inspektera.mjs och Chromium körs på riktigt."""
import contextlib
import functools
import http.server
import json
import socketserver
import subprocess
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SIDA = """<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Fångst</title><style>
body { margin: 0; font: 16px sans-serif; }
h1 { animation: in 1.6s ease-out both; }
@keyframes in { from { opacity: 0; } to { opacity: 1; } }
.snurra { width: 20px; height: 20px; background: #333; animation: varv 1s linear infinite; }
@keyframes varv { to { transform: rotate(360deg); } }
#kakor { position: fixed; inset: auto 0 0 0; background: #fff; border-top: 1px solid #000; padding: 16px; }
</style></head><body>
<p><span id="lockbete" onclick="document.title = 'lockbetet klickat'">OK</span></p>
<h1>Rubriken</h1><div class="snurra"></div>
<div id="kakor" class="cookie-banner"><p>Vi använder kakor.</p>
<div class="val" onclick="document.getElementById('kakor').remove(); document.title = 'stängd'"><span>Jag förstår</span></div></div>
</body></html>"""


class Tyst(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class Fangst(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = contextlib.ExitStack()
        cls.tmp = Path(cls.stack.enter_context(korregister.egen_tmp_med('nwp-fangst-', 'fångstens prov'))).resolve()
        (cls.tmp / 'sajt').mkdir()
        (cls.tmp / 'sajt' / 'index.html').write_text(SIDA, encoding='utf-8')
        hanterare = functools.partial(Tyst, directory=str(cls.tmp / 'sajt'))
        cls.server = socketserver.TCPServer(('127.0.0.1', 0), hanterare)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.adress = 'http://127.0.0.1:%d/' % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.stack.close()

    def fanga(self, namn, *flaggor):
        ut = self.tmp / namn
        r = subprocess.run(['node', str(ROOT / 'kontroller' / 'webblasare' / 'inspektera.mjs'), '--adress', self.adress, '--ut', str(ut),
                            '--vyer', '390', '--tillat-alla', '--tillstand', '', *flaggor], cwd=ROOT, capture_output=True, text=True, timeout=180)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        return json.loads((ut / 'INSPEKTION.json').read_text(encoding='utf-8'))['vyer']['390']

    def test_utan_flaggorna_ar_fangsten_som_forut(self):
        vy = self.fanga('utan')
        self.assertNotIn('samtycke', vy)
        self.assertNotIn('lugn', vy)

    def test_dialogen_stangs_med_sitt_eget_val_och_bara_inne_i_dialogen(self):
        vy = self.fanga('samtycke', '--samtycke')
        # lockbetet "OK" står före dialogen i sidan, utanför den: klickas det blir knappen "OK"
        self.assertEqual(vy.get('samtycke'), {'stangd': True, 'knapp': 'Jag förstår', 'roll': 'text'}, vy.get('samtycke'))

    def test_forsta_vyn_vantar_in_den_andliga_animationen_men_inte_den_oandliga(self):
        vy = self.fanga('lugn', '--lugn', '6000')
        lugn = vy.get('lugn') or {}
        self.assertEqual(lugn.get('animationer_kvar'), 0, lugn)
        self.assertGreaterEqual(lugn.get('ms', 0), 600, 'rubrikens intoning väntades inte in: %s' % lugn)
        self.assertLess(lugn.get('ms', 10 ** 6), 5000, 'den oändliga snurran räknades som en animation att vänta ut: %s' % lugn)


if __name__ == '__main__':
    unittest.main()
