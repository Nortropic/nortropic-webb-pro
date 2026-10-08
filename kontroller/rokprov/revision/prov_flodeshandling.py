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
        self.assertIn('förbered',[x['text'].lower() for x in handlingar if x['id']=='exportera'][0])


if __name__ == '__main__':
    unittest.main()
