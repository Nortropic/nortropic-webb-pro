#!/usr/bin/env python3
"""Kundregistret i mallens Worker (mall/leverans/worker/index.js, katalogens k10-pipedrive-lead) med D1 som riktig SQLite
och en märkt attrapp av Pipedrives API i Node (prov_kundregister_node.mjs): ett sparat ärende blir person, lead och
anteckning efter svaret (ctx.waitUntil), med raden i kundregister efter varje steg; inget förs över när kunden inte valt
det, utanför produktionen, med ofullständig eller ogiltig konfiguration, när raden inte kan skrivas eller för ett andra
inskick av samma ärende; ett nej före första skapandet är fel, allt annat utan kvitto står som skickar med de id som hann
sparas; besökarens svar påverkas aldrig; meddelandet escapas i anteckningen; nyckeln och leverantörens text syns aldrig
i rad, svar eller logg. Dessutom exportens driftvärde för kontots underdomän."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LEVERANS = ROOT / 'mall' / 'leverans'
NODE = Path(__file__).with_name('prov_kundregister_node.mjs')
NYCKEL = 'SYNTETISKT-HEMLIG-PIPEDRIVE-NYCKEL-0000'


class Kundregister(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run(['node', '--no-warnings', str(NODE), str(LEVERANS / 'worker' / 'index.js'), str(LEVERANS / 'migrations')],
                           capture_output=True, text=True, timeout=120)
        if r.returncode:
            raise AssertionError(r.stderr[-1500:])
        cls.f = {x['namn']: x for x in json.loads(r.stdout)}

    def test_person_lead_och_anteckning_efter_svaret(self):
        f = self.f['klar']
        self.assertEqual(f['svar'], [{'status': 303, 'location': '/tack/', 'utfall': 'skickad', 'vantande': 1}])
        self.assertEqual([(a['metod'], a['url'], a['nyckel']) for a in f['anrop']],
                         [('POST', 'https://provab.pipedrive.com/api/v2/persons', True), ('POST', 'https://provab.pipedrive.com/api/v1/leads', True),
                          ('POST', 'https://provab.pipedrive.com/api/v1/notes', True)])
        person, lead, notis = (a['kropp'] for a in f['anrop'])
        self.assertEqual(person, {'name': 'Prov <Provsson>', 'phones': [{'value': '070-000 00 00', 'primary': True, 'label': 'work'}]})
        self.assertEqual(lead, {'title': 'Förfrågan från webbplatsen: Prov <Provsson>', 'person_id': 4711})
        self.assertEqual(notis['lead_id'], 'adf21080-0e10-11eb-879b-05d71fb426ec')
        self.assertIn('Rad ett<br>&lt;script&gt;x&lt;/script&gt; &amp; &quot;citat&quot;', notis['content'])
        self.assertNotIn('<script>', notis['content'])
        self.assertEqual(f['rader'], [{'status': 'klar', 'person_id': '4711', 'lead_id': 'adf21080-0e10-11eb-879b-05d71fb426ec', 'forsok': 1, 'fel': None}])

    def test_inget_overfors_utan_val_eller_utanfor_produktionen(self):
        for n in ('ej-valt', 'demo', 'halvt-konfigurerat', 'ogiltig-doman', 'radfel'):
            with self.subTest(n=n):
                f = self.f[n]
                self.assertEqual(f['anrop'], [], 'ingen begäran till Pipedrive')
                self.assertEqual(f['svar'][0]['status'], 303, 'besökarens svar påverkas inte')
        self.assertEqual(self.f['ej-valt']['rader'], []); self.assertEqual(self.f['ej-valt']['svar'][0]['vantande'], 0)
        self.assertEqual(self.f['demo']['svar'][0]['utfall'], 'demo')
        for n in ('halvt-konfigurerat', 'ogiltig-doman'):
            self.assertTrue(any('valt men inte konfigurerat' in x for x in self.f[n]['logg']), self.f[n]['logg'])
        self.assertTrue(any('raden kunde inte skrivas' in x for x in self.f['radfel']['logg']))

    def test_nej_okant_utfall_och_frist(self):
        rad = lambda n: self.f[n]['rader'][0]  # noqa: E731
        self.assertEqual((rad('nekad-person')['status'], rad('nekad-person')['person_id'], rad('nekad-person')['fel']),
                         ('fel', None, 'kundregistret nekade (HTTP 401)'))
        self.assertEqual((rad('nekad-lead')['status'], rad('nekad-lead')['person_id'], rad('nekad-lead')['lead_id']), ('skickar', '4711', None),
                         'ett nej efter att personen skapats är inte ett rent fel: avstämningen ser personen')
        self.assertEqual((rad('serverfel')['status'], rad('serverfel')['fel']), ('skickar', 'kundregistret bekräftade inte (HTTP 502)'))
        self.assertEqual((rad('oläsbart')['status'], rad('oläsbart')['person_id']), ('skickar', '4711'))
        self.assertEqual((rad('langsam')['status'], rad('langsam')['lead_id']), ('skickar', 'adf21080-0e10-11eb-879b-05d71fb426ec'))
        self.assertIn('fristen', rad('langsam')['fel'])
        self.assertEqual(rad('natfel')['status'], 'skickar')
        for n in ('nekad-person', 'nekad-lead', 'serverfel', 'oläsbart', 'langsam', 'natfel'):
            self.assertEqual(self.f[n]['svar'][0]['status'], 303, n)

    def test_ett_andra_inskick_av_samma_arende_fors_inte_over_igen(self):
        f = self.f['dubblett']
        self.assertEqual([s['utfall'] for s in f['svar']], ['skickad', 'dubblett'])
        self.assertEqual(len(f['anrop']), 3); self.assertEqual(len(f['rader']), 1)

    def test_nyckeln_och_leverantorens_text_syns_aldrig(self):
        for n, f in self.f.items():
            text = json.dumps([f['svar'], f['rader'], f['logg']], ensure_ascii=False)
            self.assertNotIn(NYCKEL, text, n)
            self.assertNotIn('SYNTETISKT-HEMLIGT', text, n)

    def test_exportens_driftvarde(self):
        mall = (LEVERANS / 'wrangler.jsonc').read_text(encoding='utf-8')
        self.assertIn('"PIPEDRIVE_DOMAN": "provab"', exportera.wrangler_namn(mall, 'prov', {'pipedrive_doman': 'provab'}))
        self.assertIn('"PIPEDRIVE_DOMAN": ""', exportera.wrangler_namn(mall, 'prov', None))
        self.assertNotRegex(mall, r'"PIPEDRIVE_TOKEN"\s*:', 'nyckeln är en hemlighet')


if __name__ == '__main__':
    unittest.main()
