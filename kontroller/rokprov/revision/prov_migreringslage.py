#!/usr/bin/env python3
"""Migreringsläget (kontroller/migreringslage.py, uppdraget 2026-10-09 M18): förberedd, måltestad, trafik flyttad, data
avstämd och legacy avvecklad är skilda besked med egna belägg; en förhandsadress blir aldrig "migrerad"; en ny kund utan
äldre drift blir "i drift", inte migrerad; trafiken räknas bara efter releasen och på kundens egen adress; läsningen
skriver ingenting; beståndet valideras; observationen följer inga omdirigeringar och känner igen Vercel."""
import contextlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje  # noqa: E402
import exportera  # noqa: E402
import korregister  # noqa: E402
import kundrepo  # noqa: E402
import migreringslage as ml  # noqa: E402

SLUG = 'prov-migrering'
CF = (200, {'server': 'cloudflare', 'cf-ray': 'x'}), (405, {'server': 'cloudflare', 'cf-ray': 'y', 'allow': 'POST'})
VERCEL = (200, {'server': 'Vercel', 'x-vercel-id': 'arn1::abc'}), (404, {'server': 'Vercel', 'x-vercel-id': 'arn1::abd'})


class Lage(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-migrering-', 'migreringslägets prov'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        (self.root / 'kunder' / SLUG).mkdir(parents=True)
        (self.root / 'kunder' / SLUG / 'KUNDREPO.json').write_text(json.dumps({'schema': 1, 'slug': SLUG}))
        self.export = None
        self.pv = None
        self.stack.enter_context(patch.object(exportera, 'aktuell', lambda slug: self.export))
        self.stack.enter_context(patch.object(kundrepo, 'preview_aktuell', lambda slug: self.pv))
        self.tid = iter('2026-10-10T08:%02d:00Z' % i for i in range(60))
        self.stack.enter_context(patch.object(kundrepo, 'nu', lambda: next(self.tid)))

    def kvitto(self, slag, **post):
        d = kundrepo.leveransdir(SLUG)
        d.mkdir(parents=True, exist_ok=True)
        post.setdefault('tid', next(self.tid))
        f = d / ('%s-%s.json' % (slag, post['tid'].replace(':', '')))
        f.write_text(json.dumps(post))
        return post

    def bestand(self, projekt):
        f = self.root / 'underlag' / 'leverans' / 'VERCEL-BESTAND.json'
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({'schema': 1, 'inventerat': '2026-10-09', 'projekt': projekt}))

    def status(self):
        return {s['id']: s['status'] for s in ml.lage(SLUG)['steg']}

    def klar_till_release(self):
        self.export = {'ok': True, 'aktuell': True, 'id': 'E1', 'commit': 'c' * 40}
        self.pv = {'status': 'klar', 'aktuell': True, 'plattform': 'cloudflare-workers', 'url': 'https://kund-prov-migrering-forhandsvisning.nortropic.workers.dev',
                   'version_id': 'v-pre', 'skydd': 'Access (302)', 'tid': '2026-10-10T08:00:00Z'}

    def test_stegen_ar_skilda_besked_med_egna_belagg(self):
        self.assertEqual(self.status(), {'forberedd': 'nej', 'maltestad': 'nej', 'trafik_flyttad': 'nej',
                                         'data_avstamd': 'inte_tillampligt', 'legacy_avvecklad': 'inte_tillampligt'})
        self.assertIn('inte påbörjad', ml.lage(SLUG)['besked'])
        self.export = {'ok': True, 'aktuell': True, 'id': 'E1', 'commit': 'c' * 40}
        self.assertEqual(self.status()['forberedd'], 'ja')
        self.klar_till_release()
        lg = ml.lage(SLUG)
        self.assertEqual([s['status'] for s in lg['steg'][:3]], ['ja', 'ja', 'nej'])
        self.assertFalse(lg['migrerad'] or lg['i_drift'], 'en förhandsvisning på workers.dev är inte trafik flyttad')
        self.assertIn('nästa: trafik flyttad', lg['besked'])
        self.assertEqual(lg['worker']['forhandsvisning_version'], 'v-pre')

    def test_release_utan_observation_efter_den_ar_inte_trafik_flyttad(self):
        self.klar_till_release()
        self.kvitto('TRAFIK', dom='cloudflare', adress='https://kund.example.se')  # före releasen: räknas inte
        self.kvitto('RELEASE', status='klar', version_id='v-prod')
        steg = ml.lage(SLUG)['steg'][2]
        self.assertEqual(steg['status'], 'nej'); self.assertIn('inte observerad efter', steg['belagg'])
        self.kvitto('TRAFIK', dom='vercel', adress='https://kund.example.se')
        self.assertIn('från Vercel', ml.lage(SLUG)['steg'][2]['belagg'])
        self.kvitto('TRAFIK', dom='cloudflare', adress='https://kund.example.se')
        lg = ml.lage(SLUG)
        self.assertEqual(lg['steg'][2]['status'], 'ja'); self.assertTrue(lg['i_drift'])
        self.assertFalse(lg['migrerad'], 'en ny kund utan äldre drift är i drift, inte migrerad')
        self.assertIn('i drift på Cloudflare', lg['besked'])
        self.assertEqual(lg['worker']['produktion_version'], 'v-prod')
        self.kvitto('RELEASE', status='fel', version_id=None)  # en fallen release ändrar inte den senaste klara
        self.assertEqual(ml.lage(SLUG)['steg'][2]['status'], 'ja')

    def test_migrerad_kraver_avstamd_data_och_avvecklad_legacy(self):
        self.klar_till_release()
        self.bestand([{'projekt': 'prov-gammal', 'slug': SLUG, 'adress': 'prov-gammal.vercel.app', 'data': 'Blob 2 filer', 'status': 'kvar'},
                      {'projekt': 'annan-kund', 'slug': 'annan', 'adress': 'annan.vercel.app', 'data': None, 'status': 'kvar'}])
        self.kvitto('RELEASE', status='klar', version_id='v-prod')
        self.kvitto('TRAFIK', dom='cloudflare', adress='https://kund.example.se')
        lg = ml.lage(SLUG)
        self.assertEqual({s['id']: s['status'] for s in lg['steg']}, {'forberedd': 'ja', 'maltestad': 'ja', 'trafik_flyttad': 'ja',
                                                                      'data_avstamd': 'nej', 'legacy_avvecklad': 'nej'})
        self.assertFalse(lg['migrerad']); self.assertIn('inte migrerad förrän', lg['besked'])
        self.assertEqual([p['projekt'] for p in lg['legacy']], ['prov-gammal'], 'en annan kunds projekt hör inte hit')
        self.kvitto('DATAAVSTAMNING', status='avstamd', omfattning='2 filer, 0 avvikelser')
        self.assertFalse(ml.lage(SLUG)['migrerad'])
        self.bestand([{'projekt': 'prov-gammal', 'slug': SLUG, 'adress': 'prov-gammal.vercel.app', 'data': 'Blob 2 filer', 'status': 'avvecklad',
                       'belagg': 'vercel project rm 2026-10-11, ägarens beslut'}])
        lg = ml.lage(SLUG)
        self.assertTrue(lg['migrerad']); self.assertTrue(lg['besked'].startswith('migrerad'))

    def test_lasningen_skriver_ingenting(self):
        self.klar_till_release()
        fore = sorted(p.relative_to(self.root) for p in self.root.rglob('*'))
        ml.lage(SLUG); ml.oversikt()
        self.assertEqual(sorted(p.relative_to(self.root) for p in self.root.rglob('*')), fore)

    def test_bestandet_valideras(self):
        self.bestand([{'projekt': 'x', 'status': 'avvecklad'}])
        self.assertEqual(ml.bestand()[0], []); self.assertIn('utan belägg', ml.bestand()[1])
        self.bestand([{'projekt': 'x', 'status': 'migrerad'}])
        self.assertIn('ogiltig', ml.bestand()[1])
        self.assertIn('ogiltig', ml.lage(SLUG)['bestandsfel'])

    def test_oversikten_visar_legacy_utan_kund(self):
        self.bestand([{'projekt': 'gammal-sajt', 'slug': None, 'adress': 'gammal.example.se', 'data': None, 'status': 'kvar'}])
        o = ml.oversikt()
        self.assertEqual([k['slug'] for k in o['kunder']], [SLUG])
        self.assertEqual([p['projekt'] for p in o['legacy_utan_kund']], ['gammal-sajt'])
        self.assertIn('1 äldre Vercel-projekt kvar', o['besked'])

    def test_observationen_galler_bara_kundens_adress(self):
        for fel in ('http://kund.example.se', 'https://kund-x-forhandsvisning.nortropic.workers.dev', 'https://x.vercel.app',
                    'https://127.0.0.1', 'https://localhost', 'https://kund.example.se/sida', 'https://u:p@kund.example.se',
                    'https://blue-field-8ca9.cloudflareaccess.com'):
            with self.assertRaises(ValueError, msg=fel):
                ml.observera_trafik(SLUG, fel, hamtare=lambda u: CF[0])
        self.assertFalse(kundrepo.leveransdir(SLUG).exists(), 'en nekad adress skriver inget kvitto')
        svar = iter(CF)
        k = ml.observera_trafik(SLUG, 'https://kund.example.se/', hamtare=lambda u: next(svar))
        self.assertEqual((k['dom'], k['adress'], k['svar']['api'], k['svar']['vercel']), ('cloudflare', 'https://kund.example.se', 405, False))
        self.assertTrue(list(kundrepo.leveransdir(SLUG).glob('TRAFIK-*.json')))
        svar = iter(VERCEL)
        self.assertEqual(ml.observera_trafik(SLUG, 'https://kund.example.se', hamtare=lambda u: next(svar))['dom'], 'vercel')

        def faller(u):
            raise OSError('nere')
        k = ml.observera_trafik(SLUG, 'https://kund.example.se', hamtare=faller)
        self.assertEqual(k['dom'], 'okant'); self.assertIn('OSError', k['fel'])

    def test_domen_kraver_workerns_kannetecken(self):
        self.assertEqual(ml.dom(*CF), 'cloudflare')
        self.assertEqual(ml.dom(CF[0], (404, {'server': 'cloudflare'})), 'okant', 'Cloudflare framför något annat än Workern')
        self.assertEqual(ml.dom((200, {'server': 'nginx'}), (405, {'allow': 'POST'})), 'okant')
        self.assertEqual(ml.dom(*VERCEL), 'vercel')

    def test_kommandoraden(self):
        import io
        with contextlib.redirect_stdout(io.StringIO()) as ut, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ml.main([SLUG]), 0)
            self.assertEqual(ml.main(['--oversikt']), 0)
            self.assertEqual(ml.main(['Ogiltig Slug!']), 2)
            with self.assertRaises(SystemExit):
                ml.main([])
        self.assertIn('"besked"', ut.getvalue())


class Hamta(unittest.TestCase):
    def test_foljer_inga_omdirigeringar_och_bar_egen_identitet(self):
        sett = []

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                sett.append(self.headers.get('User-Agent'))
                self.send_response(301 if self.path == '/' else 405)
                self.send_header('Location', 'https://annan.example/')
                self.send_header('Allow', 'POST')
                self.send_header('CF-RAY', 'z')
                self.end_headers()

            def log_message(self, *a):
                pass
        s = ThreadingHTTPServer(('127.0.0.1', 0), H)
        threading.Thread(target=s.serve_forever, daemon=True).start()
        self.addCleanup(s.shutdown)
        bas = 'http://127.0.0.1:%d' % s.server_address[1]
        status, h = ml.hamta(bas + '/')
        self.assertEqual((status, h.get('location'), 'cf-ray' in h), (301, 'https://annan.example/', True))
        self.assertEqual(ml.hamta(bas + '/api/forfragan/')[0], 405)
        self.assertEqual(sett, [ml.UA, ml.UA])


if __name__ == '__main__':
    unittest.main()
