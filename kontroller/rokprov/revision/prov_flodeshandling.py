#!/usr/bin/env python3
"""Dashboardens ordinarie ingång med syntetiska underlag och en falsk arbetare."""
import contextlib
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
import server as dash
import atelje
import ateljeslut
import korslut
import korregister
import prototyp
import flodesstart
import os


class Flodeshandling(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'flödesvyns syntetiska ingång')))
        self.slug = 'prov-flodeshandling'
        self.u, self.k = self.root / 'underlag' / self.slug, self.root / 'kunder' / self.slug
        (self.u / 'atelje').mkdir(parents=True); self.k.mkdir(parents=True)
        for m in (dash, atelje):
            self.stack.enter_context(patch.multiple(m, ROOT=self.root, UNDERLAG=self.u.parent, KUNDER=self.k.parent))
        v = {'schema': 1, 'namn': 'Syntetiskt uppdrag', 'fiktiv': True, 'kontaktvagar': [],
             'rackvidd': {'typ': 'nationell'}, 'tjanster': ['Prov']}
        (self.u / 'VERKSAMHET.json').write_text(json.dumps(v))
        (self.u / 'UPPDRAG.md').write_text('Syntetiska uppgifter för isolerat prov.')
        (self.k / 'DOM.json').write_text(json.dumps({'domar': [{'bygge_dist': 'abc'}]}))

    def post(self, historisk=False):
        t = {n: {'varde': True, 'text': 'Syntetiskt verifierat'} for n, _ in korslut.TILLSTAND}
        if historisk:
            t['tekniskt_godkant'] = {'varde': None, 'historik': {'varde': True}, 'text': 'gällde den gamla versionen'}
        return {'typ': korslut.TYP, 'datum': '2026-01-01T01:00:00Z', 'korning': 'prov', 'dist_sha256': 'abc',
                'tillstand': t, 'brister': ['MARKOR-DOLD-KRITIK'], 'atgarder': ['MARKOR-REKOMMENDATION']}

    def test_fem_besked_lases_ur_slutposten(self):
        with patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertEqual(len(s['tillstand']), 5)
        self.assertTrue(s['tillstand'][1]['varde'])
        self.assertEqual(s['tillstand'][1]['status'], 'ja')

    def test_villkorat_godkannande_visas_for_sig(self):
        # GR-20261007-r101-om#KAN-7: "Ja, efter små ändringar" är ett eget värde i slutposten, och vyn visar det för sig
        p = self.post()
        p['tillstand']['agaren_godkanner'] = {'varde': 'villkorat', 'text': 'kärnfrågan namn: Ja, efter små ändringar'}  # korslut.VILLKORAT
        with patch.object(korslut, 'aktuell', return_value=p), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        ag = next(x for x in s['tillstand'] if x['id'] == 'agaren_godkanner')
        self.assertEqual((ag['varde'], ag['status']), ('villkorat', 'ja med villkor'))

    def test_historik_blir_inte_gron(self):
        with patch.object(korslut, 'aktuell', return_value=self.post(True)), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertIsNone(s['tillstand'][1]['varde'])
        self.assertEqual(s['tillstand'][1]['status'], 'historiskt')

    def test_blindningen_galler_hela_beskedet(self):
        with patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=True)
        self.assertNotIn('MARKOR', json.dumps(s))
        self.assertIsNone(s['tillstand'][2]['varde'])
        self.assertFalse(s['filer'])

    def test_saknat_slutbesked_ar_inte_ett_underkannande(self):
        with patch.object(korslut, 'aktuell', return_value=None), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertEqual({x['status'] for x in s['tillstand']}, {'saknas'})
        self.assertTrue(all(x['varde'] is None for x in s['tillstand']))

    def test_helbyggets_granskning_doljs_fore_dom_pa_samma_version(self):
        (self.k / 'DOM.json').write_text(json.dumps({'domar': [{'bygge_dist': 'gammal'}]}))
        with patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertIsNone(s['tillstand'][2]['varde'])
        self.assertNotIn('MARKOR', json.dumps(s))
        self.assertFalse(s['filer'])

    def test_ny_korning_gor_foregaende_slutbesked_historiskt(self):
        (self.u / 'atelje/STATUS.json').write_text(json.dumps({'startad': '2026-01-02T00:00:00Z', 'steg': 'startar'}))
        with patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertTrue(all(x['varde'] is None and x['status'] == 'historiskt' for x in s['tillstand']))

    def test_en_stopp_post_doljer_inte_helbyggets_gallande_besked(self):
        # GR-20261008-r117-claude#A4: en kort post om en start som stannade före körningen ersätter ingen post
        stopp = {'typ': ateljeslut.TYP_STOPP, 'datum': '2026-01-03T00:00:00Z', 'korning': {'startad': None}, 'skal': 'MARKOR-STOPPSKAL',
                 'tillstand': {n: {'varde': None, 'text': 'ingen körning startades'} for n, _ in korslut.TILLSTAND}, 'brister': []}
        with patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=stopp):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertEqual([x['status'] for x in s['tillstand']], ['ja'] * 5)
        self.assertTrue(any('MARKOR-STOPPSKAL' in b for b in s['brister']), s['brister'])
        with patch.object(korslut, 'aktuell', return_value=None), patch.object(ateljeslut, 'aktuell', return_value=stopp):
            s = dash.flodesbesked(self.slug, blind=False)
        self.assertEqual({x['status'] for x in s['tillstand']}, {'saknas'})

    def test_helbygget_ar_inte_kontrollerat_utan_godkand_granskning(self):
        # GR-20261008-r117-claude#C3: steg 6 ur slutposten är grönt bara när både tekniskt och designgranskaren godkänner (som B1)
        post = self.post()
        post['tillstand']['designgranskaren_godkanner'] = {'varde': False, 'text': 'MARKOR-UNDERKAND'}
        (self.k / 'DOM.json').write_text(json.dumps({'domar': []}))
        with patch.object(korslut, 'aktuell', return_value=post), patch.object(ateljeslut, 'aktuell', return_value=None), \
                patch.object(dash, '_fil', return_value=None):
            f = dash.flode(self.slug)
        s6 = f['steg'][5]
        self.assertEqual(s6['namn'], 'Helbygget')
        self.assertEqual(s6['status'], 'skapat')
        self.assertTrue(any('korslut godkänner inte' in b for b in s6['brister']), s6['brister'])
        self.assertTrue(any(t['text'].startswith('Designgranskaren: domen visas efter din dom') for t in s6['kontroller']), s6['kontroller'])
        self.assertNotIn('MARKOR-UNDERKAND', json.dumps(s6))
        post['tillstand']['designgranskaren_godkanner'] = {'varde': True, 'text': 'godkänd'}
        with patch.object(korslut, 'aktuell', return_value=post), patch.object(ateljeslut, 'aktuell', return_value=None), \
                patch.object(dash, '_fil', return_value=None):
            self.assertEqual(dash.flode(self.slug)['steg'][5]['status'], 'kontrollerat')

    def test_startmiljon_visas_och_hindrar_helbygget_fore_starten(self):
        # F07 (motorinventeringen): Flöde visar startmiljön, och ett helbygge med Kundstarts lager utan sandlåda hindras vid
        # knappen med skälet, i stället för att kor.sh nekar efter att starten registrerats
        (self.u.parent / 'kundstart').mkdir()
        with patch.dict(os.environ, {'NWP_SANDLADA': 'av'}), patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            f = dash.flode(self.slug)
            self.assertEqual((f['startmiljo']['sandlada'], f['startmiljo']['kundstart_lager']), ('av', True))
            self.assertIn('NWP_SANDLADA=pa', f['startmiljo']['hinder'])
            with patch.object(prototyp, 'lage', return_value=('godkand', None)), patch.object(flodesstart, 'pagande', return_value=False):
                h = {x['id']: x for x in prototyp.handlingar(self.slug)}
            self.assertIn('helbygge', h); self.assertIn('NWP_SANDLADA=pa', h['helbygge']['hinder'])
            self.assertTrue(all('hinder' not in x for i, x in h.items() if i != 'helbygge'), h)
        with patch.dict(os.environ, {'NWP_SANDLADA': 'pa'}), patch.object(korslut, 'aktuell', return_value=self.post()), patch.object(ateljeslut, 'aktuell', return_value=None):
            self.assertIsNone(dash.flode(self.slug)['startmiljo']['hinder'])
            with patch.object(prototyp, 'lage', return_value=('godkand', None)), patch.object(flodesstart, 'pagande', return_value=False):
                self.assertNotIn('hinder', {x['id']: x for x in prototyp.handlingar(self.slug)}['helbygge'])

    def test_avslutat_startid_svarar_med_sin_slutkod_inte_som_vagrad_start(self):
        # GR-20261008-r117-claude#B1: en begäran som redan är besvarad är inte en vägrad start; fliken får släppa sitt start-id
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        host = '127.0.0.1:%d' % srv.server_port
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        def anrop(data):
            c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=4)
            try:
                c.request('POST', '/api/flode/' + self.slug + '/start', json.dumps(data), {'Origin': 'http://' + host})
                r = c.getresponse(); return r.status, json.loads(r.read().decode())
            finally:
                c.close()
        (self.u / 'ateljestarter').mkdir(parents=True)
        (self.u / 'ateljestarter/prov-avslutad-1.json').write_text(json.dumps({'handling': 'exportera', 'status': 'slut', 'slutkod': 1}))
        with patch.object(prototyp, 'fran_dashboard', return_value=1):
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-avslutad-1'})
            self.assertEqual((status, svar['avslutad'], svar['slutkod']), (200, True, 1), svar)
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-ej-bokford-2'})
            self.assertEqual(status, 409, svar)

    def test_registrerad_kraver_journalpost_och_fliken_slapper_startid_efter_omlasning(self):
        # GR-20261008-r117-claude#B5: slutkod 5 utan journalpost (upptaget kundlås) är 409, inte registrerad; B7: nyckeln släpps efter omläsningen
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        host = '127.0.0.1:%d' % srv.server_port
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        def anrop(data):
            c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=4)
            try:
                c.request('POST', '/api/flode/' + self.slug + '/start', json.dumps(data), {'Origin': 'http://' + host})
                r = c.getresponse(); return r.status, json.loads(r.read().decode())
            finally:
                c.close()
        (self.u / 'ateljestarter').mkdir(parents=True)
        with patch.object(prototyp, 'fran_dashboard', return_value=5):
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-upptaget-1'})
            self.assertEqual(status, 409, svar); self.assertIn('journalpost', svar['fel']); self.assertEqual(svar['slutkod'], 5)
            (self.u / 'ateljestarter/prov-upptaget-1.json').write_text(json.dumps({'handling': 'exportera', 'status': 'startad', 'pid': None}))
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-upptaget-1'})
            self.assertEqual(status, 202, svar); self.assertIn('registrerad', svar['besked'])
            status, svar = anrop({'handling': 'stoppa-overgang', 'start_id': 'prov-stopp-2'})
            self.assertEqual(status, 202, svar)
        # starterna går genom arbetsytans handling() (Flöde är en del av Byggflöde sedan 2026-10-09)
        js = (Path(__file__).resolve().parents[3] / 'dashboard' / 'arbetsyta.js').read_text(encoding='utf-8')
        block = js[js.index('async function handling(id, bekraftad)'):js.index('// --- byggflödet ---')]
        self.assertGreater(block.index('slappId(nyckel, startId)'), block.index("await hamta('/api/arbetsyta/'"), 'start-id släpps först efter omläsningen (B7)')
        self.assertIn("'nwp-start:' + slug + ':' + id", block, 'samma start-id-nyckel som förut, per kund och handling')

    def test_skrivande_anrop_kraver_dashboardnyckeln(self):
        # B-20261005-dashboardens-api-tar-emot-agarens-domar-fran-vil: Origin lika med Host räcker inte; nyckeln krävs
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        host = '127.0.0.1:%d' % srv.server_port
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        self.stack.enter_context(patch.dict(dash.NYCKEL, {'varde': 'provnyckel-0123456789'}))
        def anrop(data, nyckel=None):
            c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=4)
            try:
                h = {'Origin': 'http://' + host}
                if nyckel is not None: h['X-Nyckel'] = nyckel
                c.request('POST', '/api/flode/' + self.slug + '/start', json.dumps(data), h)
                r = c.getresponse(); return r.status, json.loads(r.read().decode())
            finally:
                c.close()
        with patch.object(prototyp, 'fran_dashboard', return_value=0) as fd:
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-nyckel-1'})
            self.assertEqual(status, 403, svar); self.assertIn('dashboardnyckel', svar['fel']); fd.assert_not_called()
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-nyckel-1'}, 'fel-nyckel-0123456789')
            self.assertEqual(status, 403, svar); fd.assert_not_called()
            status, svar = anrop({'handling': 'exportera', 'start_id': 'prov-nyckel-1'}, 'provnyckel-0123456789')
            self.assertEqual(status, 200, svar); fd.assert_called_once()
        rot = Path(__file__).resolve().parents[3]
        html = (rot / 'dashboard' / 'index.html').read_text(encoding='utf-8')
        self.assertIn("'X-Nyckel': nyckel()", html); self.assertIn('#nyckel=', html)
        self.assertIn('#nyckel=$NYCKEL', (rot / 'dashboard.sh').read_text(encoding='utf-8'))
        self.assertEqual(len([l for l in html.splitlines() if "method: 'POST'" in l]), 1, 'ett enda POST-anrop i sidan, med nyckeln')

    def test_http_start_delar_cli_och_upprepat_id_startar_inte_igen(self):
        srv = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.addCleanup(srv.server_close); self.addCleanup(srv.shutdown)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        host = '127.0.0.1:%d' % srv.server_port
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {host}}))
        def anrop(method, data=None, origin=True):
            c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=4)
            try:
                headers = {'Origin': 'http://' + host} if origin else {}
                c.request(method, '/api/flode/' + self.slug + '/start', json.dumps(data) if data is not None else None, headers)
                r = c.getresponse(); return r.status, r.read().decode()
            finally:
                c.close()
        with patch.object(atelje.subprocess, 'Popen', return_value=SimpleNamespace(pid=987654)) as spawn, \
                patch.object(atelje, 'lever', return_value=False), patch.object(atelje, 'vanta', return_value=5), \
                patch.object(atelje, 'bevara_forra'), patch.object(atelje, 'krav_slug'):
            self.assertEqual(anrop('GET')[0], 404); spawn.assert_not_called()
            data = {'handling': 'forbered', 'start_id': 'prov-http-start-1'}
            self.assertEqual(anrop('POST', data, origin=False)[0], 403); spawn.assert_not_called()
            self.assertEqual(anrop('POST', data)[0], 202)
            self.assertEqual(anrop('POST', data)[0], 202)
            self.assertEqual(spawn.call_count, 1)
            self.assertEqual(anrop('POST', {'handling': 'godkand', 'start_id': 'prov-http-start-2'})[0], 400)
        self.assertFalse((self.u / 'DESIGNDOMAR.jsonl').exists())

    def test_godkand_startsida_har_en_uttrycklig_bygghandling(self):
        with patch.object(prototyp, 'lage', return_value=('godkand','syntetiskt giltigt beslut')):
            handlingar = prototyp.handlingar(self.slug)
        self.assertIn('helbygge', [x['id'] for x in handlingar])

    def test_teknisk_export_ar_en_handling_utan_publiceringslofte(self):
        (self.k/'sajt/src/pages').mkdir(parents=True)
        (self.k/'sajt/src/pages/index.astro').write_text('<h1>Syntetiskt prov</h1>')
        (self.k/'sajt/package.json').write_text('{}')
        with patch.object(prototyp,'lage',return_value=('vanta','syntetisk klar för bedömning')):
            handlingar = prototyp.handlingar(self.slug)
        self.assertIn('exportera',[x['id'] for x in handlingar])
        text_=[x['text'].lower() for x in handlingar if x['id']=='exportera'][0]
        self.assertIn('kundrepot',text_);self.assertIn('ingen publicering',text_)


if __name__ == '__main__':
    unittest.main()
