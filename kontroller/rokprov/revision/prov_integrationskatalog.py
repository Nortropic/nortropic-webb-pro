#!/usr/bin/env python3
"""Integrationskatalogen K01–K18 (kontroller/integrationskatalog.py): katalogen är giltig, valideringen fäller varje
slag av brist, och planen är deterministisk, utan sidoeffekter och skiljer kundval från önskemål, beroenden, konflikter,
utredningsvägar och okända kostnader (uppdraget 2026-10-09: T01, T04, T05, T06, T31)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import integrationskatalog as ik  # noqa: E402

KAT = ik.las()


def val(*par, lage='kundval'):
    return [{'omrade': p[:3].upper(), 'paket': p, 'lage': lage} for p in par]


class Katalog(unittest.TestCase):
    def test_katalogen_ar_giltig_och_tacker_alla_omraden(self):
        self.assertEqual(ik.brister(KAT), [])
        self.assertEqual([o['id'] for o in KAT['omraden']], ['K%02d' % i for i in range(1, 19)])
        self.assertTrue(all(any(p['omrade'] == o for p in KAT['paket']) for o in ik.OMRADEN))
        # K18 är flera namngivna val, aldrig en enda övrigt-ruta
        self.assertGreaterEqual(len([p for p in KAT['paket'] if p['omrade'] == 'K18']), 5)
        # ingen färdighet utan körväg och prov; inget leverantörsprov påstås
        for p in KAT['paket']:
            if p['fardighet'] in ('kontraktsprovat', 'leverantorsprovat'):
                self.assertTrue(p['prov'] and all((ik.ROOT / f).is_file() for f in p['prov']), p['id'])
        self.assertNotIn('leverantorsprovat', {p['fardighet'] for p in KAT['paket']})

    def brist(self, andra, vantat):
        k = copy.deepcopy(KAT)
        andra(k)
        b = ik.brister(k, importera=False)
        self.assertTrue(any(vantat in x for x in b), (vantat, b))

    def test_valideringen_faller_varje_slag_av_brist(self):
        p = lambda k, pid: next(x for x in k['paket'] if x['id'] == pid)  # noqa: E731
        self.brist(lambda k: p(k, 'k03-formular-worker').pop('dataflode'), 'saknar dataflode')
        self.brist(lambda k: p(k, 'k02-cloudflare-workers')['funktioner'].update(tillampa='os.system'), 'utanför FUNKTIONER')
        self.brist(lambda k: p(k, 'k02-cloudflare-workers')['kraver'].append('k03-formular-worker'), 'cirkulärt beroende')
        self.brist(lambda k: p(k, 'k02-vercel-befintlig').update(utesluter=[]), 'inte ömsesidig')
        self.brist(lambda k: p(k, 'k07-matning-utreds')['kostnad'].update(belopp=0), 'kräver valuta, källa och datum')
        self.brist(lambda k: p(k, 'k03-formular-worker').update(prov=[]), 'kontraktsprovat utan prov')
        self.brist(lambda k: p(k, 'k03-formular-worker').update(prov=['kontroller/finns-inte.py']), 'finns inte')
        self.brist(lambda k: p(k, 'k09-bokningslank')['funktioner'].update(tillampa=None) or p(k, 'k09-bokningslank').update(fardighet='implementerat'), 'utan körväg')
        self.brist(lambda k: p(k, 'k12-handel-utreds').update(fardighet='implementerat'), 'under utredning')
        self.brist(lambda k: p(k, 'k02-cloudflare-workers').update(fardighet='leverantorsprovat'), 'privat leverantörsbevis')
        self.brist(lambda k: k.update(paket=[x for x in k['paket'] if x['omrade'] != 'K13']), 'K13 saknar paket')
        self.brist(lambda k: p(k, 'k05-search-console')['kraver'].append('okand-formaga'), 'okänt paket eller förmåga')
        self.brist(lambda k: p(k, 'k06-hitta-hit').update(id='k07-hitta-hit'), 'börja med sitt område')
        self.brist(lambda k: p(k, 'k06-hitta-hit')['kallor'].append({'url': 'http://x', 'last': 'igår'}), 'utan https-adress')


class Plan(unittest.TestCase):
    def test_grundvagen_ar_klar_for_bygge_i_beroendeordning(self):
        pl = ik.planera(val('k02-cloudflare-workers', 'k03-formular-worker', 'k04-resend-transaktion'), arende={'id': 'A', 'revision': 3})
        self.assertTrue(pl['klar_for_bygge'], pl['hinder'])
        self.assertLess(pl['ordning'].index('k02-cloudflare-workers'), pl['ordning'].index('k03-formular-worker'))
        self.assertEqual(pl['arende'], {'id': 'A', 'revision': 3})
        self.assertIn('k04-resend-transaktion', pl['okand_kostnad'], 'okänd kostnad visas som okänd, aldrig som noll')
        self.assertNotIn('k02-cloudflare-workers', pl['okand_kostnad'])
        self.assertTrue(any(m['handling'].startswith('ansluta kontot') for m in pl['manniska']))
        self.assertTrue(all(a['funktion'] is None and a['besked'] for a in pl['avveckling']), 'avvecklingen är uttryckligen mänsklig')

    def test_planen_ar_deterministisk_och_bunden_till_val_och_arende(self):
        v = val('k02-cloudflare-workers', 'k03-formular-worker', 'k04-resend-transaktion')
        a, b = ik.planera(v), ik.planera(list(reversed(v)))
        self.assertEqual(a['plan_sha256'], b['plan_sha256'], 'ordningen i valet ändrar inte planen')
        self.assertNotEqual(a['plan_sha256'], ik.planera(v, arende={'id': 'A', 'revision': 4})['plan_sha256'])
        self.assertNotEqual(a['plan_sha256'], ik.planera(v[:2] + val('k04-befintlig-brevlada'))['plan_sha256'])

    def test_onskemal_och_framtida_ingar_inte_i_omfattningen(self):
        pl = ik.planera(val('k02-cloudflare-workers') + val('k11-stripe-betallank', lage='onskemal') + val('k14-nyhetsbrev-utreds', lage='framtida'))
        self.assertEqual([x['paket'] for x in pl['omfattning']], ['k02-cloudflare-workers'])
        self.assertEqual(sorted(x['paket'] for x in pl['ovriga']), ['k11-stripe-betallank', 'k14-nyhetsbrev-utreds'])
        self.assertTrue(pl['klar_for_bygge'])

    def test_beroende_konflikt_utredning_och_okant_paket_ger_tydliga_hinder(self):
        pl = ik.planera(val('k02-cloudflare-workers', 'k03-formular-worker'))
        self.assertEqual(pl['saknade_beroenden'], [{'paket': 'k03-formular-worker', 'kraver': 'transaktionsmejl'}])
        self.assertFalse(pl['klar_for_bygge'])
        pl = ik.planera(val('k02-cloudflare-workers', 'k02-vercel-befintlig'))
        self.assertEqual(pl['konflikter'][0]['paket'], ['k02-cloudflare-workers', 'k02-vercel-befintlig'])
        pl = ik.planera(val('k02-cloudflare-workers', 'k12-handel-utreds'))
        self.assertTrue(any('utredningsväg' in h for h in pl['hinder']))
        pl = ik.planera([{'omrade': 'K10', 'paket': 'k10-hubspot-api', 'lage': 'kundval'}])
        self.assertTrue(any('okänt paket' in h for h in pl['hinder']), 'en påhittad leverantör blir ett hinder, inte en anslutning')
        pl = ik.planera([{'omrade': 'K04', 'paket': 'k03-formular-worker', 'lage': 'kundval'}])
        self.assertTrue(any('hör till K03' in h for h in pl['hinder']))
        pl = ik.planera([{'omrade': 'K02', 'paket': 'k02-cloudflare-workers', 'lage': 'beslutat'}])
        self.assertTrue(any('okänt läge' in h for h in pl['hinder']))

    def test_flera_instanser_kraver_egen_identitet(self):
        two = [{'omrade': 'K09', 'paket': 'k09-bokningslank', 'lage': 'kundval', 'instans': 'filial-a'},
               {'omrade': 'K09', 'paket': 'k09-bokningslank', 'lage': 'kundval', 'instans': 'filial-b'}]
        pl = ik.planera(two)
        self.assertEqual([x['instans'] for x in pl['omfattning']], ['filial-a', 'filial-b']); self.assertEqual(pl['hinder'], [])
        pl = ik.planera([dict(two[0], instans=None), dict(two[1], instans=None)])
        self.assertTrue(any('två gånger' in h for h in pl['hinder']))

    def test_planen_importerar_eller_kor_inga_paketfunktioner(self):
        # ett vilande eller valt paket startar ingenting när planen räknas fram (T05)
        kod = ('import sys; sys.path.insert(0, %r); import integrationskatalog as ik; '
               'ik.planera([{"omrade": "K02", "paket": "k02-cloudflare-workers", "lage": "kundval"}]); '
               'print(sorted(m for m in ("kundrepo", "workersprov", "exportera", "driftkoll", "seo_kontroll") if m in sys.modules))') % str(ik.ROOT / 'kontroller')
        r = subprocess.run([sys.executable, '-B', '-c', kod], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout.strip(), '[]')

    def test_kommandoraden(self):
        self.assertEqual(ik.main(['--prova']), 0)


if __name__ == '__main__':
    unittest.main()
