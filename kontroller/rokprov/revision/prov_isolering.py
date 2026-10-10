#!/usr/bin/env python3
"""Kundernas resurser hålls isär på Cloudflare-vägen (uppdraget 2026-10-09, etapp 7, T07, T27, M05, M15): samma paket hos
två kunder ger egna Workers, egen D1, egen R2-bucket och egna driftvärden utan läckage mellan konfigurationerna; två
kandidater hos samma kund delar kundens enda uppsättning (identiteten bär ingen kandidat), så att tio förslag aldrig blir
tio Workers eller databaser; förhandsvisningen är en egen Worker utan kundens databas, bucket, mejl och kundregister."""
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exportera  # noqa: E402
import kundrepo  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MALL = (ROOT / 'mall' / 'leverans' / 'wrangler.jsonc').read_text(encoding='utf-8')


def jsonc(text):
    return json.loads(re.sub(r'^\s*//.*$', '', text, flags=re.M))


DRIFT = {
    'kund-a': {'database_id': '11111111-1111-4111-8111-111111111111', 'forfragan_till': 'a@kund-a.example.invalid',
               'forfragan_fran': 'kund-a@notis.example.invalid', 'nyhetsbrev_lista': '770001', 'nyhetsbrev_mall': '770002', 'pipedrive_doman': 'kunda'},
    'kund-b': {'database_id': '22222222-2222-4222-8222-222222222222', 'forfragan_till': 'b@kund-b.example.invalid',
               'forfragan_fran': 'kund-b@notis.example.invalid', 'nyhetsbrev_lista': '880001', 'nyhetsbrev_mall': '880002', 'pipedrive_doman': 'kundb'},
}


class Isolering(unittest.TestCase):
    def setUp(self):
        self.k = {s: jsonc(exportera.wrangler_namn(MALL, s, d)) for s, d in DRIFT.items()}

    def test_samma_paket_hos_tva_kunder_ger_egna_resurser(self):
        a, b = self.k['kund-a'], self.k['kund-b']
        self.assertEqual((a['name'], b['name']), ('kund-kund-a', 'kund-kund-b'))
        self.assertNotEqual(a['d1_databases'][0]['database_name'], b['d1_databases'][0]['database_name'])
        self.assertNotEqual(a['d1_databases'][0]['database_id'], b['d1_databases'][0]['database_id'])
        self.assertNotEqual(a['r2_buckets'][0]['bucket_name'], b['r2_buckets'][0]['bucket_name'])
        self.assertNotEqual(a['env']['forhandsvisning']['name'], b['env']['forhandsvisning']['name'])
        self.assertEqual(a['send_email'][0]['allowed_destination_addresses'], ['a@kund-a.example.invalid'])
        text_a = json.dumps(a)
        for varde in DRIFT['kund-b'].values():
            self.assertNotIn(varde, text_a, 'kund B:s driftvärde står i kund A:s konfiguration')

    def test_tva_kandidater_hos_samma_kund_delar_en_uppsattning(self):
        i = kundrepo.identitet('kund-a')
        self.assertNotIn('kandidat', json.dumps(i))
        self.assertEqual((i['worker'], i['worker_forhandsvisning']), (self.k['kund-a']['name'], self.k['kund-a']['env']['forhandsvisning']['name']))
        # exporten av en kandidat (kandidater/kNN/sajt) skriver samma wrangler.jsonc, med kundens namn och inget annat
        self.assertEqual(exportera.wrangler_namn(MALL, 'kund-a', DRIFT['kund-a']), exportera.wrangler_namn(MALL, 'kund-a', DRIFT['kund-a']))
        self.assertNotIn('k0', self.k['kund-a']['name'])

    def test_forhandsvisningen_ar_skild_fran_produktionens_resurser(self):
        f = self.k['kund-a']['env']['forhandsvisning']
        self.assertEqual(f['vars'], {'MILJO': 'forhandsvisning'})
        for nyckel in ('d1_databases', 'r2_buckets', 'send_email'):
            self.assertNotIn(nyckel, f)
        self.assertNotIn('PIPEDRIVE_DOMAN', f['vars']); self.assertNotIn('NYHETSBREV_LISTA', f['vars'])

    def test_mandat_och_kvitton_ligger_per_kund(self):
        self.assertNotEqual(kundrepo.mandatfil('kund-a'), kundrepo.mandatfil('kund-b'))
        self.assertEqual(kundrepo.mandatfil('kund-a').parent.parent.name, 'kund-a')
        with self.assertRaises(ValueError):
            kundrepo.identitet('../kund-b')


if __name__ == '__main__':
    unittest.main()
