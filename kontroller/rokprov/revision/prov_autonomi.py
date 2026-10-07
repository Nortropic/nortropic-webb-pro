#!/usr/bin/env python3
"""Resursmått: okänt är inte noll, råvärden summeras och identifierade kopior räknas en gång."""
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import autonomi as au
import korregister


def svar(**andra):
    return {'num_turns': 2, 'duration_ms': 2400, 'total_cost_usd': 0.004, **andra}


class Resursmatt(unittest.TestCase):
    def test_saknat_ogiltigt_och_tomt_ar_okant(self):
        for v in (None, {}, {'duration_ms': 1}, svar(duration_ms=True), svar(duration_ms='fel'),
                  svar(duration_ms=-1), svar(duration_ms=float('nan')), svar(duration_ms=float('inf'))):
            with self.subTest(v=v):
                m = au.summa([v])
                self.assertFalse(m['fullstandigt'])
        self.assertIsNone(au.summa([])['minuter'])
        self.assertIsNone(au.summa([svar(), None])['minuter'])
        self.assertEqual(au.summa([svar(), None])['observerat']['duration_ms'], 2400)
        self.assertEqual(au.summa([svar(duration_ms=0)])['minuter'], 0)

    def test_identifierade_kopior_raknas_en_gang(self):
        a = svar(uuid='resultat-a', session_id='session-a')
        b = svar(uuid='resultat-b', session_id='session-a')  # återupptagen session, annat resultat
        m = au.summa([a, dict(a), b, svar(), svar()])
        self.assertEqual(m['sessioner'], 4)
        self.assertEqual(m['dubbletter'], 1)
        self.assertEqual(m['turer'], 8)
        self.assertTrue(m['fullstandigt'])
        # Äldre logg saknar resultat-id: bara identisk kopia med samma sessions-id kan slås samman.
        a.pop('uuid')
        self.assertEqual(au.summa([a, dict(a)])['sessioner'], 1)

    def test_motstridig_resultatidentitet_ar_okand(self):
        m = au.summa([svar(uuid='samma'), svar(uuid='samma', duration_ms=60000)])
        self.assertFalse(m['fullstandigt'])
        self.assertIsNone(m['minuter'])
        self.assertEqual(m['konflikter'], 1)

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetiska resursmått')))
        self.stack.enter_context(patch.multiple(au, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.k = au.KUNDER / 'prov-matt'
        self.k.mkdir(parents=True)

    def skriv(self, fil, v):
        fil.parent.mkdir(parents=True, exist_ok=True)
        fil.write_text(json.dumps(v))

    def test_omgangarnas_ravarden_summeras_fore_avrundning(self):
        for n in range(3):
            r = self.k / 'granskning' / ('runda-%02d' % n)
            self.skriv(r / 'UTFALL.json', {'status': 'fel'})
            self.skriv(r / 'svar.json', svar(uuid=str(n)))
        m = au.granskningen(self.k)['modell']
        self.assertEqual(m['duration_ms'], 7200)
        self.assertEqual(m['minuter'], 0.1)
        self.assertEqual(m['listpris_usd'], 0.01)

    def test_tom_fallen_omgang_ar_inte_gratis(self):
        self.skriv(self.k / 'granskning/runda-01/UTFALL.json', {'status': 'fel'})
        self.assertIsNone(au.granskningen(self.k)['modell']['minuter'])
        self.assertFalse(au.matt(au.bygge('prov-matt')))

    def test_totalen_deduplicerar_over_faser_och_bevarar_avbrutna(self):
        a = svar(type='result', uuid='a', session_id='session-a')
        self.skriv(self.k / 'korning-20260101T000000Z.jsonl', a)
        arkiv = au.UNDERLAG / 'prov-matt/atelje/foregaende'
        self.skriv(arkiv / 'svar-a.json', a)
        self.skriv(arkiv / 'svar-b.json', svar(uuid='b'))
        self.skriv(self.k / 'granskning/runda-01/svar.json', svar(uuid='c', is_error=True))
        m = au.bygge('prov-matt')
        self.assertEqual(m['totalt']['duration_ms'], 7200)
        self.assertEqual(m['totalt']['sessioner'], 3)
        self.assertTrue(au.matt(m))
        (self.k / 'korning-20260101T000001Z.jsonl').write_text('{"type":"system"}\n')
        m = au.bygge('prov-matt')
        self.assertIsNone(m['totalt']['minuter'])
        self.assertFalse(au.matt(m))
        self.assertIsNone(au.sammanstall([m])['median_minuter'])

    def test_rapporten_pastar_inte_kvot_eller_aktiv_agartid(self):
        b = au.bygge('prov-matt')
        text = au.markdown({'per_bygge': [b], 'sammanstallning': au.sammanstall([b])})
        self.assertNotIn('ett mått på kvoten', text)
        self.assertIn('inte aktiv arbetstid', text)
        self.assertIn('inte fakturerad kostnad', text)

    def test_omtagsarkivet_och_lankar_ar_kanda(self):
        a = au.UNDERLAG / 'prov-matt/atelje'
        self.skriv(a / 'svar-a.json', svar(uuid='a', duration_ms=60000))
        self.skriv(au.UNDERLAG / 'prov-matt/omtag/tid/atelje/foregaende/aldre/svar-b.json', svar(uuid='b', duration_ms=120000))
        self.assertEqual(au.bygge('prov-matt')['totalt']['duration_ms'], 180000)
        (a / 'svar-lank.json').symlink_to(self.root / 'finns-inte')
        self.assertFalse(au.matt(au.bygge('prov-matt')))

    def test_kand_granskarsession_utan_fil_ar_okand(self):
        r = self.k / 'granskning/runda-01'
        self.skriv(r / 'GRANSKNING.json', {'godkand':False, 'sessioner':[{'granskare':1},{'granskare':2}]})
        self.skriv(r / 'svar.json', svar(uuid='a'))
        self.assertIsNone(au.granskningen(self.k)['modell']['minuter'])

    def test_kand_skaparsession_utan_fil_ar_okand(self):
        a = au.UNDERLAG / 'prov-matt/atelje/kandidater/k01'
        self.skriv(a / 'svar-a.json', svar(uuid='a'))
        self.skriv(a / 'STATUS.json', {'sessioner':[{'svar':'svar-a.json'},{'svar':'svar-b.json'}]})
        self.assertFalse(au.matt(au.bygge('prov-matt')))

    def test_trasig_senare_resultatrad_inte_aldre_resultat(self):
        p = self.k / 'korning-20260101T000000Z.jsonl'
        self.skriv(p, svar(type='result'))
        p.write_text(p.read_text() + '\n{"type":"result",')
        self.assertIsNone(au.sessionsresultat(p))
        p.write_text('[{"type":"result"}]\n')
        self.assertIsNone(au.sessionsresultat(p))

    def test_ovantade_objektformer_kraschar_inte(self):
        r = self.k / 'granskning/runda-01'
        self.skriv(r / 'GRANSKNING.json', {'godkand':True, 'kriterier':{'text':[]}})
        self.skriv(r / 'UTFALL.json', ['fel'])
        self.skriv(r / 'svar.json', svar())
        self.assertEqual(au.granskningen(self.k)['omgangar'], 0)
        self.skriv(self.k / 'DOM.json', {'domar':[None]})
        self.assertFalse(au.agaren(self.k)['domd'])

    def test_stora_tal_blir_okanda_utan_infinity(self):
        for a in ([svar(duration_ms=10**400)], [svar(total_cost_usd=1e308), svar(total_cost_usd=1e308)]):
            m = au.summa(a)
            self.assertFalse(m['fullstandigt'])
            json.dumps(m, allow_nan=False)

    def test_sparad_dom_utan_ribbans_svar_ar_inte_bedomd(self):
        self.skriv(self.k / 'DOM.json', {'domar':[{'svar':{'annan':'syntetiskt'}}]})
        b = au.bygge('prov-matt')
        self.assertFalse(b['agaren']['domd'])
        self.assertIsNone(au.sammanstall([b])['andel_accepterade'])
        self.skriv(self.k / 'DOM.json', {'domar':[{'svar':{'namn':'Nej, inte utan större ändringar'}}]})
        b = au.bygge('prov-matt')
        self.assertTrue(b['agaren']['domd'])
        self.assertEqual(au.sammanstall([b])['underkanda'], 1)

    def test_startad_forberedelse_raknas_utan_sajt(self):
        self.skriv(au.UNDERLAG / 'prov-matt/atelje/STATUS.json', {'startad':'2026-01-01T00:00:00Z','steg':'fel'})
        self.assertIn('prov-matt', au.byggen())
        s = au.sammanstall([au.bygge('prov-matt')])
        self.assertEqual(s['startade'], 1)
        self.assertEqual(s['utan_giltig_agardom'], 1)

    def test_medianen_for_andliga_stora_tal_ar_andlig(self):
        self.assertEqual(au.median([1e308, 1e308]), 1e308)
        json.dumps({'median':au.median([1e308, 1e308])}, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
