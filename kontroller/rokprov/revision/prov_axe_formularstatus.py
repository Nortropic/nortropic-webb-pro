#!/usr/bin/env python3
"""Axe mäter inte dokumentet efter ett blockerat formulärinskick.

Riktig lokal HTTP-server, Chromium, läsvakt och axe-CLI. Node-preloaden håller
bara page.url() kvar på adressen från senaste goto, vilket deterministiskt
återskapar URL-vaktens tidsfönster. Navigation, nätbegäran, DOM och axe är
oförändrade. Det är ett kontrollerat tidsfönster, inte ett påstående om att
Chromiums naturliga schemaläggning reproduceras vid varje körning.
Fallet täcker navigation som påbörjas vid klicket, inte ett separat tidsfönster
där navigationen börjar först inne i axe.run.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(os.environ.get('NWP_PROV_ROOT') or Path(__file__).resolve().parents[3]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister


PRELOAD = r"""
import { appendFileSync } from 'node:fs';
import { chromium } from __PLAYWRIGHT__;
const logg = __LOGG__;
const skriv = (post) => appendFileSync(logg, JSON.stringify(post) + '\n');
const starta = chromium.launch.bind(chromium);
chromium.launch = async (...args) => {
  const browser = await starta(...args);
  const context = browser.newContext.bind(browser);
  browser.newContext = async (...args) => {
    const ctx = await context(...args);
    const skapa = ctx.newPage.bind(ctx);
    ctx.newPage = async (...args) => {
      const page = await skapa(...args);
      const url = page.url.bind(page);
      const goto = page.goto.bind(page);
      let kvar = null;
      page.goto = async (...args) => {
        const svar = await goto(...args);
        kvar = url();
        return svar;
      };
      page.url = () => {
        const verklig = url();
        if (kvar && kvar !== verklig) skriv({ typ: 'kvarhallen_url', verklig, rapporterad: kvar });
        return kvar || verklig;
      };
      page.on('request', req => {
        if (req.isNavigationRequest() && req.frame() === page.mainFrame())
          skriv({ typ: 'navigation', metod: req.method(), url: req.url() });
      });
      return page;
    };
    return ctx;
  };
  return browser;
};
"""


class AxeFormularstatus(unittest.TestCase):
    def test_blockerad_navigation_ar_inte_formularfel_men_required_mats(self):
        with korregister.egen_tmp_med('nwp-kallgap-', 'axe formulärstatus med kvarhållen URL') as katalog:
            tmp = Path(katalog)
            poster = []
            huvud = ('<!doctype html><html lang="sv"><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width"><title>Formulärprov</title>'
                     '</head><body><main>')

            class Server(BaseHTTPRequestHandler):
                def log_message(self, *_args):
                    pass

                def do_GET(self):
                    vag = urlsplit(self.path).path
                    if vag in ('/giltigt/', '/required/'):
                        krav = ' required' if vag == '/required/' else ''
                        innehall = ('<h1>Formulärprov</h1><form method="post" action="/mottagare">'
                                    '<label for="epost">E-post</label><input id="epost" name="epost"' + krav + '>'
                                    '<button type="submit">Skicka</button></form>')
                        status = 200
                    else:
                        innehall, status = '<h1>Sidan finns inte</h1>', 404
                    body = (huvud + innehall + '</main></body></html>').encode()
                    self.send_response(status)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def do_POST(self):
                    poster.append(self.path)
                    self.send_response(500)
                    self.send_header('Content-Length', '0')
                    self.end_headers()

            server = ThreadingHTTPServer(('127.0.0.1', 0), Server)
            server.daemon_threads = True
            trad = threading.Thread(target=server.serve_forever, daemon=True)
            trad.start()
            try:
                logg, preload = tmp / 'navigation.jsonl', tmp / 'kvar-url.mjs'
                preload.write_text(PRELOAD.replace('__PLAYWRIGHT__', json.dumps(
                    (ROOT / 'kontroller/node_modules/playwright/index.mjs').resolve().as_uri()))
                    .replace('__LOGG__', json.dumps(str(logg))))
                env = {k: v for k, v in os.environ.items() if not k.startswith('NWP_')}
                base = 'http://127.0.0.1:%d' % server.server_address[1]
                p = subprocess.run(['node', '--import', str(preload), str(ROOT / 'kontroller/axe.mjs'),
                                    '--url=' + base, '--sidor=/giltigt/,/required/',
                                    '--ut=' + str(tmp / 'axe'), '--tillstand=formularfel'],
                                   cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
                self.assertTrue((tmp / 'axe/axe.json').is_file(), (p.returncode, p.stdout, p.stderr))
                rapport = json.loads((tmp / 'axe/axe.json').read_text())
                rader = [r for r in rapport['rader'] if r['tillstand'] == 'formularfel']
                giltiga = [r for r in rader if r['sida'] == '/giltigt/']
                kravda = [r for r in rader if r['sida'] == '/required/']
                handelser = [json.loads(r) for r in logg.read_text().splitlines()]
                self.assertEqual(poster, [], 'läsvakten måste stoppa POST före mottagaren')
                self.assertEqual(sum(r['typ'] == 'navigation' and r['metod'] == 'POST' for r in handelser), 2,
                                 'det verkliga navigationsanropet ska ske i båda vyerna')
                self.assertEqual({r['vy'] for r in giltiga}, {'mobil', 'desktop'}, rader)
                self.assertTrue(all(r.get('matt') is False and not r.get('fel') and not r['overtradelser']
                                    for r in giltiga), giltiga)
                self.assertEqual({r['vy'] for r in kravda}, {'mobil', 'desktop'}, rader)
                self.assertTrue(all(r.get('matt') is not False and not r.get('fel') and r.get('ogiltiga_falt', 0) > 0
                                    for r in kravda), kravda)
                self.assertEqual(p.returncode, 0, (p.stdout, p.stderr, rapport))
            finally:
                server.shutdown()
                server.server_close()
                trad.join(5)


if __name__ == '__main__':
    unittest.main()
