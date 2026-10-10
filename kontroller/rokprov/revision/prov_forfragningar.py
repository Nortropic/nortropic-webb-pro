#!/usr/bin/env python3
"""Driftens läge för formulärärenden (kontroller/forfragningar.py) mot SQLite med mallens D1-schema: antal per status,
väntande och okända aviseringar efter gränsen, fallna aviseringar, utgångna ärenden, utskrift utan personuppgifter,
torrkörd gallring, gallring som tar bilagan före raderna och som stannar när en bilaga inte kan tas bort.
Det riktiga Wrangler-provet mot lokal D1 och R2 är kontroller/workersprov.py."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import forfragningar as ff  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
NU = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def tid(**d):
    return ff.iso(NU + timedelta(**d))


class Drift(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        for f in sorted((ROOT / 'mall/leverans/migrations').glob('*.sql')):
            self.db.executescript(f.read_text(encoding='utf-8'))
        rader = [  # id, status, uppdaterad, gallras, bilaga
            ('00000000-0000-4000-8000-000000000001', 'accepterad', tid(hours=-5), tid(days=300), None),
            ('00000000-0000-4000-8000-000000000002', 'fel', tid(hours=-4), tid(days=300), 'forfragningar/x/2/bilaga'),
            ('00000000-0000-4000-8000-000000000003', 'skickar', tid(minutes=-40), tid(days=300), None),
            ('00000000-0000-4000-8000-000000000004', 'vantar', tid(minutes=-5), tid(days=300), None),
            ('00000000-0000-4000-8000-000000000005', 'accepterad', tid(days=-400), tid(days=-35), 'forfragningar/y/5/bilaga'),
        ]
        for i, (fid, status, uppd, gallras, bilaga) in enumerate(rader):
            self.db.execute('INSERT INTO forfragningar (id, nyckel, mottagen, namn, telefon, meddelande, bilaga, gallras) VALUES (?,?,?,?,?,?,?,?)',
                            (fid, 'i:%d' % i, uppd, 'Hemlig Persson', '0700000000', 'Privat meddelande', bilaga, gallras))
            self.db.execute('INSERT INTO utkorg (forfragan, status, forsok, fel, uppdaterad) VALUES (?,?,?,?,?)',
                            (fid, status, 1 if status in ('fel', 'accepterad') else 0, 'Mejltjänsten bekräftade inte mottagningen (500)' if status == 'fel' else None, uppd))
        self.borttagna = []

    def kor(self, sql):
        if sql.lstrip().upper().startswith('DELETE'):
            with self.db:
                self.db.executescript(sql)
            return []
        return [dict(r) for r in self.db.execute(sql)]

    def ta_bort(self, nyckel):
        self.borttagna.append(nyckel)

    def test_laget_utan_personuppgifter(self):
        l = ff.lage(self.kor, NU)
        self.assertEqual(l['status'], {'accepterad': 2, 'fel': 1, 'skickar': 1, 'vantar': 1}); self.assertEqual(l['totalt'], 5)
        self.assertEqual([x['id'][-1] for x in l['oklara']], ['3'], 'bara det som väntat längre än gränsen')
        self.assertEqual([x['id'][-1] for x in l['fel']], ['2'])
        self.assertEqual([(x['id'][-1], x['bilaga']) for x in l['utgangna']], [('5', True)])
        utskrift = json.dumps({k: v for k, v in l.items() if not k.startswith('_')}, ensure_ascii=False)
        for privat in ('Hemlig Persson', '0700000000', 'Privat meddelande', 'forfragningar/'):
            self.assertNotIn(privat, utskrift)

    def test_gallringen_ar_torr_tills_utfor_och_tar_bilagan_forst(self):
        plan = ff.gallra(self.kor, self.ta_bort, NU)
        self.assertEqual((plan['antal'], plan['bilagor'], plan['utfort']), (1, 1, False)); self.assertEqual(self.borttagna, [])
        self.assertEqual(self.db.execute('SELECT count(*) FROM forfragningar').fetchone()[0], 5)
        plan = ff.gallra(self.kor, self.ta_bort, NU, utfor=True)
        self.assertTrue(plan['utfort']); self.assertEqual(self.borttagna, ['forfragningar/y/5/bilaga'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM forfragningar').fetchone()[0], 4)
        self.assertEqual(self.db.execute("SELECT count(*) FROM utkorg WHERE forfragan LIKE '%5'").fetchone()[0], 0)

    def test_en_bilaga_som_inte_kan_tas_bort_stoppar_raderingen(self):
        def faller(nyckel):
            raise RuntimeError('wrangler r2 object delete')
        plan = ff.gallra(self.kor, faller, NU, utfor=True)
        self.assertFalse(plan['utfort']); self.assertTrue(plan['fel'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM forfragningar').fetchone()[0], 5, 'ärendet står kvar och pekar på bilagan')

    def test_csv_for_kundregistret_ar_privat_och_utan_formler(self):
        import csv
        import tempfile
        self.db.execute("UPDATE forfragningar SET namn = '=HYPERLINK(\"https://x.invalid\")', meddelande = '+46 ring mig' WHERE id LIKE '%1'")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'arenden.csv'
            self.assertEqual(ff.exportera_csv(self.kor, f), 5)
            self.assertEqual(f.stat().st_mode & 0o777, 0o600)
            rader = list(csv.reader(f.read_text(encoding='utf-8-sig').splitlines()))
            self.assertEqual(rader[0], ['id', 'mottagen', 'namn', 'telefon', 'meddelande', 'bild', 'avisering'])
            forsta = next(r for r in rader[1:] if r[0].endswith('1'))
            self.assertTrue(forsta[2].startswith("'=") and forsta[4].startswith("'+"), forsta)
            self.assertEqual(next(r for r in rader[1:] if r[0].endswith('2'))[5:], ['ja', 'fel'])
        kr = ROOT / 'kunder' / 'prov-forfragningar-csv' / 'kundrepo' / 'public'
        kr.mkdir(parents=True, exist_ok=True)
        try:
            with self.assertRaises(ValueError):
                ff.exportera_csv(self.kor, kr / 'a.csv')  # ett kundrepo pushas och driftsätts
        finally:
            import shutil
            shutil.rmtree(ROOT / 'kunder' / 'prov-forfragningar-csv', ignore_errors=True)
        for fel in (ROOT / 'kontroller' / 'arenden.csv', ROOT / 'arenden.csv'):
            with self.assertRaises(ValueError):
                ff.exportera_csv(self.kor, fel)
        self.assertFalse((ROOT / 'arenden.csv').exists())
        privat = ROOT / 'underlag' / 'prov-forfragningar-csv'
        try:
            privat.mkdir(parents=True, exist_ok=True)
            self.assertEqual(ff.exportera_csv(self.kor, privat / 'a.csv'), 5)
        finally:
            import shutil
            shutil.rmtree(privat, ignore_errors=True)

    def test_kundregistret_i_laget_och_gallringen_med_framande_nycklar(self):
        self.db.execute('PRAGMA foreign_keys = ON')  # som D1
        for fid, status, pid, lid, uppd, fel in (('00000000-0000-4000-8000-000000000001', 'klar', '11', 'a-1', tid(hours=-5), None),
                                                ('00000000-0000-4000-8000-000000000002', 'skickar', '12', None, tid(minutes=-40), 'kundregistret bekräftade inte (HTTP 502)'),
                                                ('00000000-0000-4000-8000-000000000003', 'fel', None, None, tid(minutes=-30), 'kundregistret nekade (HTTP 401)'),
                                                ('00000000-0000-4000-8000-000000000005', 'klar', '15', 'a-5', tid(days=-399), None)):
            self.db.execute('INSERT INTO kundregister (forfragan, status, person_id, lead_id, forsok, fel, uppdaterad) VALUES (?,?,?,?,1,?,?)',
                            (fid, status, pid, lid, fel, uppd))
        k = ff.lage(self.kor, NU)['kundregister']
        self.assertEqual(k['status'], {'klar': 2, 'skickar': 1, 'fel': 1})
        self.assertEqual([(x['id'][-1], x['person_id']) for x in k['oklara']], [('2', '12')], 'avstämningen ser hur långt överföringen kom')
        self.assertEqual([x['id'][-1] for x in k['fel']], ['3'])
        self.assertNotIn('Hemlig Persson', json.dumps(k, ensure_ascii=False))
        plan = ff.gallra(self.kor, self.ta_bort, NU, utfor=True)
        self.assertTrue(plan['utfort'], plan)
        self.assertEqual(self.db.execute("SELECT count(*) FROM kundregister WHERE forfragan LIKE '%5'").fetchone()[0], 0)
        self.assertEqual(self.db.execute('SELECT count(*) FROM kundregister').fetchone()[0], 3)

    def test_laget_utan_kundregistrets_tabell(self):
        self.db.execute('DROP TABLE kundregister')  # en äldre kunds D1 före migreringen 0002
        self.assertIsNone(ff.lage(self.kor, NU)['kundregister'])
        self.assertTrue(ff.gallra(self.kor, self.ta_bort, NU, utfor=True)['utfort'])

    def test_konverteringar_per_vecka_utan_personuppgifter(self):
        # NU är lördag 2026-10-10 (vecka 41); ärendena ovan är mottagna i veckorna 41 (fyra) och, 400 dagar tidigare, utanför
        k = ff.konverteringar(self.kor, NU, veckor=3)
        self.assertEqual([(v['vecka'], v['fran'], v['forfragningar'], v['aviserade']) for v in k['veckor']],
                         [('2026-V39', '2026-09-21', 0, 0), ('2026-V40', '2026-09-28', 0, 0), ('2026-V41', '2026-10-05', 4, 1)])
        self.assertEqual(k['totalt'], 4)
        utskrift = json.dumps(k, ensure_ascii=False)
        for privat in ('Hemlig Persson', '0700000000', 'Privat meddelande', '00000000-0000'):
            self.assertNotIn(privat, utskrift)
        self.db.execute("UPDATE forfragningar SET mottagen = '2026-10-04T23:59:59.000Z' WHERE id LIKE '%1'")  # söndag i vecka 40
        self.assertEqual([v['forfragningar'] for v in ff.konverteringar(self.kor, NU, veckor=2)['veckor']], [1, 3], 'veckan börjar måndag 00:00 UTC')
        for fel in (0, 105, '8'):
            with self.assertRaises(ValueError):
                ff.konverteringar(self.kor, NU, veckor=fel)

    def test_kommandoraden_kraver_konto_for_remote(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'NWP_CLOUDFLARE_FIL': '/finns/inte/cloudflare.env'}):
            self.assertEqual(ff.main([str(ROOT), '--remote']), 1)


if __name__ == '__main__':
    unittest.main()
