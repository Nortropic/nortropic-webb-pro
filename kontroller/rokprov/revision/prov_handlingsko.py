#!/usr/bin/env python3
"""Handlingskön (kontroller/handlingsko.py; ägarens tillägg 2026-10-10, punkt 1) och vägen från kundens val till en
fullständigt torrkörd aktivering för en fiktiv kund, med ett riktigt Kundstart-ärende i en tempkatalog: kön räknas fram ur
planen (katalogens människors handlingar, planens hinder och saknade beroenden) med ansvarig, skäl och vad som kan
fortsätta; en post blir klar bara med belägg (nyckelintaget, uppgifter, kontot, ägarens intyg med referens, aldrig ett
kryss); kundens ändrade behov gör posterna inaktuella; kundens vy har kön utan beläggens detaljer och utan ägarens
planposter; kundens nyckel kräver kundens beslutsfattare och syns aldrig i svar, ärende eller kön; och den fiktiva kunden
går från val via accepterat erbjudande till en torrkörning som listar varje steg utan att något saknas och utan
sidoeffekter (planens hinder stoppar aktiveringen tills erbjudandet är accepterat)."""
import contextlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import aktivera  # noqa: E402
import atelje  # noqa: E402
import exportera  # noqa: E402
import handlingsko as hk  # noqa: E402
import korregister  # noqa: E402
import kundstart as ks  # noqa: E402
import kundstart_agare as ka  # noqa: E402
import kundstart_behorighet as kh  # noqa: E402
import kundstart_integration as ki  # noqa: E402
import nyckelintag as ni  # noqa: E402

SLUG = 'prov-ko'
NYCKEL = 'xkeysib-SYNTETISK-KUNDNYCKEL-KO-0001'
GRUND = [('K02', 'k02-cloudflare-workers'), ('K03', 'k03-formular-worker'), ('K04', 'k04-cloudflare-epost')]


class Handlingsko(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-', 'handlingsköns prov'))).resolve()
        self.root = self.tmp / 'repo'
        (self.root / 'underlag' / SLUG).mkdir(parents=True); (self.root / 'kunder').mkdir()
        (self.root / 'underlag' / SLUG / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Syntetisk kund', 'fiktiv': True}))
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.multiple(exportera, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.konto = self.tmp / 'cloudflare.env'
        self.stack.enter_context(patch.dict(os.environ, {'NWP_NYCKELINTAG': str(self.tmp / 'intag'), 'NWP_CLOUDFLARE_FIL': str(self.konto)}))
        (self.root / 'mall' / 'leverans' / 'migrations').mkdir(parents=True)
        (self.root / 'mall' / 'leverans' / 'migrations' / '0001_forfragningar.sql').write_text('-- prov\n')
        self.db = ks.Lager(self.root / 'underlag' / 'kundstart')
        self.e, self.token = self.db.skapa(SLUG, 'Syntetisk kund', modellbudget=10)
        for i, (o, p) in enumerate(GRUND):
            self.valj('grund-%d' % i, o, p)
        self.gor('integrationsbehov', {'id': 'nyhetsbrev', 'behov': 'Besökare anmäler sig till ett nyhetsbrev.', 'lage': 'kundval'})
        self.valj('nyhetsbrev-val', 'K14', 'k14-brevo-dubbel', behov='nyhetsbrev')

    def gor(self, n, data, token=None):
        d = self.db.las(self.e, token or self.token)
        return self.db.kundhandling(self.e, token or self.token, d['revision'], ks.id_(), n, data)

    def valj(self, vid, omrade, paket, behov=None):
        data = {'id': vid, 'omrade': omrade, 'paket': paket, 'motivering': 'Syntetisk motivering.'}
        if behov:
            data['behov'] = behov
        return ki.valj(self.db, self.e, self.db.internt(self.e)['revision'], data)

    def ko(self):
        return hk.ko(self.db.internt(self.e))

    def post(self, borjan, k=None):
        return next(p for p in (k or self.ko())['poster'] if p['handling'].startswith(borjan))

    def test_kon_raknas_fram_ur_planen(self):
        k = self.ko()
        paket = {p['paket'] for p in k['poster']}
        self.assertTrue({'k02-cloudflare-workers', 'k03-formular-worker', 'k04-cloudflare-epost', 'k14-brevo-dubbel', 'plan'} <= paket, paket)
        for p in k['poster']:
            self.assertTrue(p['handling'] and p['skal'] and p['under_vantan'] and p['ansvarig'] in ('kund', 'agare', 'nortropic'), p)
        self.assertTrue(any(p['paket'] == 'plan' and 'accepterat erbjudande' in p['handling'] for p in k['poster']), 'planens hinder är ägarens post')
        self.assertEqual(self.post('Lämna Brevo-nyckeln', k)['status'], 'vantar')
        self.assertEqual(self.post('Lämna Brevo-nyckeln', k)['ansvarig'], 'kund')
        self.assertGreater(k['sammanfattning']['vantar_pa_kunden'], 0)

    def test_en_post_blir_klar_bara_med_belagg(self):
        ka.handling(self.root, self.e, 'nyckelintag', {'leverantor': 'brevo', 'nyckel': NYCKEL, 'falt': {'lista': '12', 'mall': '7'}})
        self.assertEqual(self.post('Lämna Brevo-nyckeln')['status'], 'klar')
        self.assertEqual(self.post('Skapa listan och bekräftelsemallen')['status'], 'klar')
        self.assertEqual(self.post('Anslut Nortropics Cloudflare-konto')['status'], 'vantar')
        self.konto.write_text('CLOUDFLARE_API_TOKEN=SYNTETISK\nCLOUDFLARE_ACCOUNT_ID=%s\nCLOUDFLARE_WORKERS_UNDERDOMAN=prov\n' % ('c' * 32)); self.konto.chmod(0o600)
        self.assertEqual(self.post('Anslut Nortropics Cloudflare-konto')['status'], 'klar', 'kontot är ett belägg, inget kryss')
        p = self.post('Låt integritetstexten nämna Brevo')
        rev = self.db.internt(self.e)['revision']
        with self.assertRaises(ks.Vagrad):
            ka.handling(self.root, self.e, 'intyga_handling', {'revision': rev, 'post': p['id'], 'referens': 'klart'})
        with self.assertRaises(ks.Konflikt):
            ka.handling(self.root, self.e, 'intyga_handling', {'revision': rev - 1, 'post': p['id'], 'referens': 'integritet.astro rad 12, commit abc123'})
        nej = self.post('Lämna Brevo-nyckeln')
        with self.assertRaises(ks.Vagrad):
            ka.handling(self.root, self.e, 'intyga_handling', {'revision': rev, 'post': nej['id'], 'referens': 'nyckeln lämnad muntligt 2026-10-10'})
        ka.handling(self.root, self.e, 'intyga_handling', {'revision': rev, 'post': p['id'], 'referens': 'integritet.astro rad 12, commit abc123'})
        p = self.post('Låt integritetstexten nämna Brevo')
        self.assertEqual(p['status'], 'klar'); self.assertIn('ägarens intyg', p['belagg'][0]['text'])

    def test_kundens_andrade_behov_gor_posterna_inaktuella(self):
        self.gor('integrationsbehov', {'id': 'nyhetsbrev', 'behov': 'Besökare anmäler sig och väljer ämnen i nyhetsbrevet.', 'lage': 'kundval'})
        k = self.ko()
        brevo = [p for p in k['poster'] if p['paket'] == 'k14-brevo-dubbel']
        self.assertTrue(brevo and all(p['status'] == 'inaktuell' and 'ändrats' in (p['varfor'] or '') for p in brevo), brevo)
        self.assertFalse(any(p['paket'] == 'k14-brevo-dubbel' and p['status'] == 'vantar' for p in k['poster']))

    def test_kundens_vy_och_nyckel(self):
        d = self.db.las(self.e, self.token)
        kv = d['handlingsko']
        self.assertTrue(kv['poster'])
        plan = [p['id'] for p in self.ko()['poster'] if p['paket'] == 'plan']
        self.assertTrue(plan, 'ägarvyn har planens poster')
        self.assertFalse(set(plan) & {p['id'] for p in kv['poster']}, 'kundens vy har inte ägarens interna planposter')
        self.assertEqual(kv['sammanfattning']['vantar'], sum(1 for p in kv['poster'] if p['status'] == 'vantar'))
        self.assertTrue(all(set(p) == {'id', 'handling', 'ansvarig', 'ansvarig_text', 'skal', 'under_vantan', 'status', 'nyckel'} for p in kv['poster']))
        self.assertEqual(next(p['nyckel'] for p in kv['poster'] if p['handling'].startswith('Lämna Brevo-nyckeln')), 'brevo')
        svar = self.gor('nyckel', {'leverantor': 'brevo', 'nyckel': NYCKEL, 'falt': {'lista': '12', 'mall': '7'}})
        self.assertNotIn(NYCKEL, json.dumps(svar)); self.assertNotIn(NYCKEL, json.dumps(self.db.internt(self.e)))
        self.assertNotIn(NYCKEL, json.dumps(self.db.las(self.e, self.token)))
        with self.db.trans() as c:
            self.assertNotIn(NYCKEL, ''.join(str(r) for r in c.execute('SELECT begaran, svar FROM operationer')))
        self.assertEqual(ni.las_for_aktivering(SLUG, 'brevo'), NYCKEL)
        self.assertEqual(ni.status(SLUG)['brevo']['kalla'], 'kund')
        self.assertEqual(self.db.internt(self.e)['nyckelhandelser'][-1]['leverantor'], 'brevo')

    def test_bara_beslutsfattaren_lamnar_en_nyckel(self):
        with patch.object(kh, 'roll', return_value='medverkande'):
            with self.assertRaises(ks.Obehorig):
                self.gor('nyckel', {'leverantor': 'brevo', 'nyckel': NYCKEL})
        self.assertIsNone(ni.las_for_aktivering(SLUG, 'brevo'))

    def test_fiktiv_kund_fran_val_till_torrkord_aktivering(self):
        self.assertIn('kundens val ingår, men inget accepterat erbjudande gäller den aktuella omfattningen', aktivera.torr(SLUG)['hinder'],
                      'planens hinder stoppar aktiveringen')
        # kunden skickar uppdraget, ägaren ger ett erbjudande och kundens beslutsfattare accepterar det
        self.gor('uppgift', {'id': 'mal', 'amne': 'A', 'text': 'Besökare ska kunna anmäla sig till nyhetsbrevet.'})
        self.gor('bekrafta', {'ids': ['mal']})
        d = self.gor('forfragan', {})
        erb = self.db.erbjudande(self.e, d['revision'], 'Syntetisk omfattning.', 'Syntetiska villkor.', 'Provägare')
        self.gor('acceptera', {'erbjudande': erb['id']})
        self.assertFalse(any(p['paket'] == 'plan' for p in self.ko()['poster']), 'planen har inga hinder kvar')
        self.konto.write_text('CLOUDFLARE_API_TOKEN=SYNTETISK\nCLOUDFLARE_ACCOUNT_ID=%s\nCLOUDFLARE_WORKERS_UNDERDOMAN=prov\n' % ('c' * 32)); self.konto.chmod(0o600)
        self.gor('nyckel', {'leverantor': 'brevo', 'nyckel': NYCKEL, 'falt': {'lista': '12', 'mall': '7'}})
        ka.handling(self.root, self.e, 'nyckelintag', {'leverantor': 'epost', 'falt': {'mottagare': 'post@kund.example.invalid'}})
        fore = sorted((str(p), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file())
        t = aktivera.torr(SLUG)
        self.assertEqual(sorted((str(p), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()), fore, 'inga sidoeffekter')
        self.assertEqual(t['valda'], ['k02-cloudflare-workers', 'k03-formular-worker', 'k04-cloudflare-epost', 'k14-brevo-dubbel'])
        self.assertEqual(t['saknas'], [], 'inget saknas för den fiktiva kunden')
        self.assertEqual({s['id']: s['status'] for s in t['steg']}, {'konto': 'klar', 'd1': 'gors', 'r2': 'gors', 'driftvarden': 'gors',
                                                                     'export': 'gors', 'migreringar': 'gors', 'hemlighet:BREVO_API_NYCKEL': 'vantar'})
        self.assertEqual(t['hinder'], ['en fiktiv verksamhet torrkörs men aktiveras aldrig'])
        self.assertFalse(t['kan_koras'])
        detalj = ka.detalj(self.root, self.e)
        self.assertEqual(detalj['aktivering']['plan_sha256'], t['plan_sha256'])
        self.assertTrue(detalj['handlingsko']['poster'])
        self.assertEqual(detalj['nyckelintag']['brevo']['nyckel'], True)
        self.assertNotIn(NYCKEL, json.dumps(detalj))


if __name__ == '__main__':
    unittest.main()
