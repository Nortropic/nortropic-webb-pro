#!/usr/bin/env python3
"""Funktioner och anslutningar i Kundstarts ärende (kontroller/kundstart_integration.py): ägarens paketval mot
katalogen, kundens läge som källa till beställningen, inaktuella val när kundens behov ändras, versionsbunden plan, den
riktiga HTTP-ingången och att inget val startar något (uppdraget 2026-10-09, etapp 3; T01, T03, T04, T05, T07)."""
import contextlib
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
import prov_kundstart_beredning as grundprov  # noqa: E402
import korregister  # noqa: E402
import kundstart as ks  # noqa: E402
import kundstart_agare as ka  # noqa: E402
import kundstart_integration as ki  # noqa: E402
import server as dash  # noqa: E402

GRUND = [('K02', 'k02-cloudflare-workers'), ('K03', 'k03-formular-worker'), ('K04', 'k04-resend-transaktion')]


class Funktioner(unittest.TestCase):
    gor = grundprov.Beredning.gor
    forslag = grundprov.Beredning.forslag

    def setUp(self):
        grundprov.Beredning.setUp(self)

    def valj(self, vid, omrade, paket, behov=None, motivering='Syntetisk motivering.'):
        d = self.db.internt(self.e)
        data = {'id': vid, 'omrade': omrade, 'paket': paket, 'motivering': motivering}
        if behov:
            data['behov'] = behov
        return ki.valj(self.db, self.e, d['revision'], data)

    def test_grundleveransen_ger_en_plan_utan_kundens_kryss(self):
        for i, (o, p) in enumerate(GRUND):
            self.valj('grund-%d' % i, o, p)
        pl = ki.plan(self.db.internt(self.e))
        self.assertTrue(pl['klar_for_bygge'], pl['hinder'])
        self.assertEqual([x['lage'] for x in pl['omfattning']], ['grund'] * 3)
        self.assertEqual(pl['arende']['id'], self.e)

    def test_ett_val_utan_kundens_behov_ar_ett_forslag_aldrig_en_bestallning(self):
        self.valj('bokning', 'K09', 'k09-bokningslank')
        pl = ki.plan(self.db.internt(self.e))
        self.assertEqual(pl['omfattning'], []); self.assertEqual(pl['ovriga'][0]['lage'], 'onskemal')

    def test_kundens_lage_styr_och_en_andring_gor_valet_inaktuellt(self):
        self.gor('integrationsbehov', {'id': 'bokning', 'behov': 'Besökaren bokar en tid.', 'lage': 'kundval'})
        self.valj('bokning-val', 'K09', 'k09-bokningslank', behov='bokning')
        pl = ki.plan(self.db.internt(self.e))
        self.assertEqual([(x['paket'], x['lage']) for x in pl['omfattning']], [('k09-bokningslank', 'kundval')])
        self.assertFalse(pl['klar_for_bygge'], 'kundens val utan ett accepterat erbjudande för omfattningen')
        self.assertTrue(any('accepterat erbjudande' in h for h in pl['hinder']))
        # samma behov kan inte bära ett andra paket
        with self.assertRaises(ks.Vagrad):
            self.valj('crm-val', 'K10', 'k10-csv-export', behov='bokning')
        sha_fore = pl['plan_sha256']
        # kunden ändrar sitt behov: valet blir inaktuellt och står utanför planen tills ägaren väljer igen (T03)
        self.gor('integrationsbehov', {'id': 'bokning', 'behov': 'Besökaren bokar och betalar en tid.', 'lage': 'kundval'})
        pl = ki.plan(self.db.internt(self.e))
        self.assertEqual(pl['omfattning'], []); self.assertFalse(pl['klar_for_bygge'])
        self.assertEqual(pl['inaktuella_val'][0]['skal'], 'kundens behov har ändrats efter valet')
        self.assertNotEqual(pl['plan_sha256'], sha_fore)
        d = self.db.internt(self.e)
        self.assertTrue(any(h['slag'] == 'ersatt_integrationsbehov' for h in d['historik']), 'historiken bevaras')
        self.valj('bokning-val', 'K09', 'k09-bokningslank', behov='bokning', motivering='Omprövat efter kundens rättelse.')
        self.assertEqual(ki.plan(self.db.internt(self.e))['omfattning'][0]['lage'], 'kundval')
        self.assertTrue(any(h['slag'] == 'ersatt_integrationsval' for h in self.db.internt(self.e)['historik']))

    def test_onskemal_forblir_onskemal_aven_nar_agaren_valjer(self):
        self.gor('integrationsbehov', {'id': 'betalning', 'behov': 'Kanske betalning senare.', 'lage': 'onskemal'})
        self.valj('betal', 'K11', 'k11-stripe-betallank', behov='betalning')
        pl = ki.plan(self.db.internt(self.e))
        self.assertEqual(pl['omfattning'], []); self.assertEqual(pl['ovriga'][0]['lage'], 'onskemal')

    def test_okant_paket_fel_omrade_och_okant_behov_nekas_utan_andring(self):
        rev = self.db.internt(self.e)['revision']
        for vid, o, p, b in (('x', 'K10', 'k10-hubspot-api', None), ('x', 'K04', 'k03-formular-worker', None), ('x', 'K09', 'k09-bokningslank', 'finns-inte')):
            with self.assertRaises(ks.Vagrad):
                self.valj(vid, o, p, behov=b)
        with self.assertRaises(ks.Konflikt):
            ki.valj(self.db, self.e, rev - 1, {'id': 'y', 'omrade': 'K09', 'paket': 'k09-bokningslank', 'motivering': 'Gammal revision.'})
        self.assertEqual(self.db.internt(self.e)['revision'], rev)
        self.assertNotIn('integrationsval', self.db.internt(self.e))

    def test_samma_val_igen_ar_ingen_ny_revision_och_avmarkering_bevarar_historiken(self):
        self.valj('a', 'K06', 'k06-hitta-hit'); rev = self.db.internt(self.e)['revision']
        self.valj('a', 'K06', 'k06-hitta-hit'); self.assertEqual(self.db.internt(self.e)['revision'], rev)
        ki.avmarkera(self.db, self.e, rev, 'a')
        d = self.db.internt(self.e)
        self.assertEqual(d['integrationsval'], {}); self.assertTrue(any(h['slag'] == 'avmarkerat_integrationsval' for h in d['historik']))

    def test_valet_gor_ett_accepterat_erbjudande_inaktuellt_men_inte_aldre_arenden(self):
        d = self.db.internt(self.e)
        fore = ks.omfattning(d)
        self.assertEqual(fore, ks.omfattning({**d, 'integrationsval': {}}), 'ett ärende utan val behåller sin omfattning')
        self.valj('a', 'K06', 'k06-hitta-hit')
        self.assertNotEqual(ks.omfattning(self.db.internt(self.e)), fore, 'ett nytt val är en materiell ändring av omfattningen')

    def test_vyn_laser_bara_och_har_fyra_skilda_dimensioner(self):
        self.gor('integrationsbehov', {'id': 'bokning', 'behov': 'Besökaren bokar en tid.', 'lage': 'kundval'})
        self.valj('b', 'K09', 'k09-bokningslank', behov='bokning')
        rev = self.db.internt(self.e)['revision']
        v = ki.vy(self.db.internt(self.e))
        self.assertEqual(self.db.internt(self.e)['revision'], rev, 'läsningen skriver ingen ny version')
        self.assertEqual(len(v['omraden']), 18)
        self.assertEqual(v['behov'][0]['bestallning'], 'kundval'); self.assertEqual(v['behov'][0]['anslutning']['konto'], 'okant')
        self.assertEqual(v['val'][0]['paket'], 'k09-bokningslank')
        p = next(x for o in v['omraden'] for x in o['paket'] if x['id'] == 'k09-bokningslank')
        self.assertEqual(p['fardighet'], 'dokumenterat')


class AiForslag(unittest.TestCase):
    """T02: modellen föreslår funktioner i samma tur som intervjun; förslagen prövas och blir aldrig val."""
    gor = grundprov.Beredning.gor
    forslag = grundprov.Beredning.forslag

    def setUp(self):
        grundprov.Beredning.setUp(self)
        self.gor('meddelande', {'text': 'Kunderna vill kunna boka tid själva på webben.'})
        self.jobb = self.db.ta_jobb('beredare')
        self.assertIsNotNone(self.jobb)
        self.mid = [m for m in self.jobb['dokument']['meddelanden'] if m['roll'] == 'kund'][-1]['id']
        self.bas = {'nytta': 'Färre samtal om tider (hypotes).', 'alternativ': 'Behåll telefonbokningen.',
                    'konsekvens': 'Kundens konto i en bokningstjänst krävs.', 'osakerhet': 'Okänt om ett system redan finns.',
                    'foljdfraga': 'Använder ni ett bokningssystem i dag?'}

    def svar(self, *forslag):
        return {'text': 'Tack, det hjälper.', 'forslag': [], 'fragor': [], 'integrationsforslag': list(forslag)}

    def test_forslag_ar_forslag_och_okanda_paket_blir_utredning(self):
        f = lambda i, o, p: dict(self.bas, id=i, omrade=o, paket=p, kallor=[self.mid])  # noqa: E731
        self.assertTrue(self.db.modellsvar(self.jobb, self.svar(f('bok', 'K09', 'k09-bokningslank'), f('crm', 'K10', 'k10-hubspot-api'),
                                                               f('hosting', 'K02', 'k02-cloudflare-workers'), f('fel-omrade', 'K11', 'k09-bokningslank'),
                                                               f('oklart', 'K18', 'utreds'))))
        d = self.db.internt(self.e)
        x = {p['id']: p for p in d['integrationsforslag']['forslag']}
        self.assertEqual((x['bok']['paket'], x['bok']['utreds'], x['bok']['paketversion']), ('k09-bokningslank', False, '1.0.0'))
        self.assertEqual((x['crm']['paket'], x['crm']['utreds'], x['crm']['avvisat_paket']), (None, True, 'k10-hubspot-api'))
        self.assertTrue(x['hosting']['utreds'] and x['fel-omrade']['utreds'] and x['oklart']['utreds'])
        self.assertIsNone(x['oklart']['avvisat_paket'])
        self.assertEqual(d['integrationsforslag']['avsandare'], 'modell')
        self.assertNotIn('integrationsval', d, 'ett förslag blir aldrig ett val')
        self.assertEqual(ki.plan(d)['omfattning'], [])
        self.assertEqual(ki.vy(d)['forslag']['revision'], self.jobb['revision'])

    def test_forslag_utan_kundkalla_eller_med_eget_val_faller_hela_svaret(self):
        rev = self.db.internt(self.e)['revision']
        for felaktigt in (dict(self.bas, id='a', omrade='K09', paket='k09-bokningslank', kallor=[]),
                          dict(self.bas, id='a', omrade='K09', paket='k09-bokningslank', kallor=['påhittad-källa']),
                          dict(self.bas, id='a', omrade='K09', paket='k09-bokningslank', kallor=[self.mid], kundval=True),
                          dict(self.bas, id='a', omrade='K99', paket='utreds', kallor=[self.mid]),
                          dict(self.bas, id='a', omrade='K09', paket=['k09-bokningslank'], kallor=[self.mid])):
            with self.subTest(f=felaktigt):
                with self.assertRaises(ks.Vagrad):
                    self.db.modellsvar(self.jobb, self.svar(felaktigt))
        d = self.db.internt(self.e)
        self.assertEqual(d['revision'], rev); self.assertNotIn('integrationsforslag', d)

    def test_kontexten_bar_katalogen_utan_grundpaket_och_schemat_faltet(self):
        import kundstart_modell as km
        v = json.loads(km.kontext(self.db.internt(self.e)))
        ids = {p['id'] for p in v['integrationskatalog']}
        self.assertIn('k09-bokningslank', ids); self.assertNotIn('k02-cloudflare-workers', ids)
        self.assertIn('integrationsforslag', km.SVARSSCHEMA['properties'])
        self.assertNotIn('integrationsforslag', km.SVARSSCHEMA['required'])
        self.assertIn('Hitta aldrig på ett paket', km.SYSTEM)


class Http(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-', 'funktionernas HTTP-prov'))).resolve()
        self.stack.enter_context(patch.object(dash, 'ROOT', self.root))
        self.server = dash.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
        self.host = '127.0.0.1:' + str(self.server.server_address[1])
        self.stack.enter_context(patch.dict(dash.VARD, {'tillatna': {self.host}}))
        t = threading.Thread(target=self.server.serve_forever, daemon=True); t.start()
        self.addCleanup(lambda: (self.server.shutdown(), self.server.server_close(), t.join(3)))

    def req(self, method, path, data=None):
        c = http.client.HTTPConnection(self.host, timeout=10)
        try:
            c.request(method, path, None if data is None else json.dumps(data),
                      headers={'Content-Type': 'application/json', 'Origin': 'http://' + self.host})
            r = c.getresponse(); return r.status, json.loads(r.read())
        finally:
            c.close()

    def test_agarens_val_genom_den_riktiga_ingangen(self):
        st, d = self.req('POST', '/api/kundstart', {'slug': 'prov-funktion', 'namn': 'Syntetisk kund', 'fiktiv': True, 'modellbudget': 0, 'operation': 'f1'})
        self.assertEqual(st, 200, d); eid = d['arende']
        st, det = self.req('GET', '/api/kundstart/' + eid); self.assertEqual(st, 200, det)
        self.assertEqual(len(det['funktioner']['omraden']), 18); self.assertEqual(det['funktioner']['val'], [])
        rev = det['arende']['revision']
        st, r = self.req('POST', '/api/kundstart/%s/integrationsval' % eid,
                         {'revision': rev, 'val': {'id': 'grund-k02', 'omrade': 'K02', 'paket': 'k02-cloudflare-workers', 'motivering': 'Grundleveransen.'}})
        self.assertEqual(st, 200, r)
        st, det = self.req('GET', '/api/kundstart/' + eid)
        self.assertEqual(det['funktioner']['val'][0]['paket'], 'k02-cloudflare-workers')
        self.assertEqual(det['funktioner']['plan']['omfattning'][0]['lage'], 'grund')
        self.assertIsNone(det['drift']['kundserver_aktiverad'], 'ett val startar ingen server')
        st, r = self.req('POST', '/api/kundstart/%s/integrationsval' % eid,
                         {'revision': det['arende']['revision'], 'val': {'id': 'x', 'omrade': 'K10', 'paket': 'k10-hubspot-api', 'motivering': 'Påhittat.'}})
        self.assertEqual(st, 400, r)
        st, r = self.req('POST', '/api/kundstart/%s/avmarkera_integration' % eid, {'revision': det['arende']['revision'], 'val': 'grund-k02'})
        self.assertEqual(st, 200, r)
        self.assertEqual(self.req('GET', '/api/kundstart/' + eid)[1]['funktioner']['val'], [])


if __name__ == '__main__':
    unittest.main()
