#!/usr/bin/env python3
"""prov_bevakning.py — den löpande bevakningen (kontroller/bevakning.py; ägarens tillägg 2026-10-09 ~13:23Z), syntetiskt
och utan nät: registret i källregistret, kontrollerna mot spanarens och underhållets resultat, bevakningen av
bevakningen, schemat i Europe/Stockholm med ikappkörning, låset mot dubbla körningar, igenkänningen av tidigare fynd,
signalerna till förbättringsloopen och Codex svar.

    .venv/bin/python kontroller/rokprov/revision/prov_bevakning.py
"""
import contextlib
import json
import os
import sys
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import bevakning  # noqa: E402
import korregister  # noqa: E402
import spana  # noqa: E402

TABELL = """| typ | namn | url eller fråga | varför | vikt | område |
|---|---|---|---|---|---|
| sida | Provets release notes | https://example.org/release-notes | prov | 1.5 | agentflödet |
| rss | Provets flöde | https://example.org/flode.xml | prov | 1.0 | provet |
"""
BLOCK = """
```bevakning sessioner
fråga: Har sessionsbeteendet ändrats?
område: ai
steg: granskning
berör: claude code
källor: Provets release notes
källtyp: leverantor
kontroll: kalla, underhall
intervall: dag
ansvar: underhållet
```

```bevakning veckofraga
fråga: Ändras metoden?
område: ux
steg: forberedelse
källor: Provets flöde
källtyp: metod
kontroll: kalla, codex
intervall: vecka
ansvar: skapandeflödet
```

```bevakning en-lucka
fråga: Vad saknar vi?
område: juridik
lucka: ingen juridisk bedömning
kontroll: codex
intervall: manad
ansvar: ägaren
post: B-prov
nästa: Codex lämnar underlag
förutsättning: en jurist
```

```bevakning forbrukningen
fråga: Vad förbrukar vi?
område: larande
kontroll: forbrukning
intervall: vecka
ansvar: bevakningen
```
"""
FEL = """
```bevakning trasig
fråga: X
område: okant-omrade
källor: Finns inte
kontroll: kalla
intervall: dag
```
"""


def utc(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


class Bevakning(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.rot = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-bevakning-', 'bevakningens prov'))).resolve()
        self.reg = self.rot / 'spaning-kallor.md'
        self.reg.write_text(TABELL + BLOCK, encoding='utf-8')
        self.sp, self.uh, self.ut, self.fb = self.rot / 'spaning', self.rot / 'startkontroll', self.rot / 'bevakning', self.rot / 'forbattringar'
        self.sp.mkdir()
        self.uh.mkdir()
        self.stack.enter_context(patch.object(bevakning, 'REGISTER', self.reg))
        self.stack.enter_context(patch.object(spana, 'KALLOR', self.reg))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_BEVAKNING_UT': str(self.ut), 'NWP_SPANING_KATALOG': str(self.sp),
                                                         'NWP_UNDERHALL_KATALOG': str(self.uh), 'NWP_FORBATTRINGAR': str(self.fb),
                                                         'NWP_BEVAKNING_KLOCKSLAG': '07:00', 'NWP_SPANING_INTERVALL_DAGAR': '1'}))
        self.id_sida = next(k['id'] for k in spana.las_kallor() if k['namn'] == 'Provets release notes')
        self.id_flode = next(k['id'] for k in spana.las_kallor() if k['namn'] == 'Provets flöde')

    def drift(self, nar, version='v1', fel=None, underhall_slut=None, rader=()):
        """Spanarens och underhållets resultat som de skrivs av spana.py och underhall.py."""
        t = nar.timestamp()
        (self.sp / 'HALSA.json').write_text(json.dumps({'schema': 1, 'kallor': {
            self.id_sida: {'id': self.id_sida, 'namn': 'Provets release notes', 'status': 'fel' if fel else 'ok', 'fel': fel,
                           'senast_lyckad': None if fel else t, 'forsok': t, 'version': version},
            self.id_flode: {'id': self.id_flode, 'namn': 'Provets flöde', 'status': 'ok', 'fel': None, 'senast_lyckad': t, 'forsok': t, 'version': None}}}))
        (self.sp / 'SENAST.json').write_text(json.dumps({'start': (nar - timedelta(minutes=3)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                         'slut': nar.strftime('%Y-%m-%dT%H:%M:%SZ'), 'fel': ['Provets release notes: %s' % fel] if fel else [],
                                                         'kallor': [{}, {}]}))
        (self.sp / 'KANDIDATER.json').write_text('[]')
        (self.uh / 'UNDERHALL.json').write_text(json.dumps({'status': 'klart', 'slut': (underhall_slut or nar).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                            'sammanfattning': 'prov', 'rader': list(rader),
                                                            'inventering': [{'id': 'npm-global:@anthropic-ai/claude-code', 'namn': 'Claude Code'}]}))

    def test_registret_och_dess_fel(self):
        f, fel = bevakning.register()
        self.assertEqual(sorted(f), ['en-lucka', 'forbrukningen', 'sessioner', 'veckofraga'])
        self.assertEqual(f['sessioner']['kallor'], ['Provets release notes'])
        self.reg.write_text(TABELL + BLOCK + FEL, encoding='utf-8')
        f, fel = bevakning.register()
        self.assertNotIn('trasig', f)
        self.assertEqual(fel[0]['id'], 'trasig')
        self.assertTrue(any('okänt område' in x for x in fel[0]['fel']) and any('Finns inte' in x for x in fel[0]['fel']), fel)
        self.assertEqual(len(spana.las_kallor()), 2, 'blocken stör inte spanarens tabell')

    def test_schemat_i_stockholmstid_med_ikappkorning(self):
        # 2026-10-09 06:30 i Stockholm (04:30Z): före klockslaget
        self.assertFalse(bevakning.dags(nar=utc('2026-10-09T04:30:00Z')))
        self.assertTrue(bevakning.dags(nar=utc('2026-10-09T05:10:00Z')), 'efter 07:00 och ingen körning i dag')
        self.assertEqual(bevakning.nasta_korning(utc('2026-10-09T05:10:00Z')), '2026-10-10T05:00:00Z')
        self.assertEqual(bevakning.nasta_korning(utc('2026-10-09T04:30:00Z')), '2026-10-09T05:00:00Z')
        nar = utc('2026-10-09T05:10:00Z')
        self.drift(nar)
        bevakning.kor(automatisk=True, nar=nar)
        self.assertFalse(bevakning.dags(nar=utc('2026-10-09T15:00:00Z')), 'en körning per lokal dag')
        # datorn var avstängd: nästa dag först 10:00 lokal tid (08:00Z); en körning, märkt med hur sent den kom
        sen = utc('2026-10-10T08:00:00Z')
        self.assertTrue(bevakning.dags(nar=sen))
        self.drift(sen)
        d = bevakning.kor(automatisk=True, nar=sen)
        self.assertEqual(d['senast']['sen_timmar'], 3.0)
        self.assertEqual((d['senast']['tidszon'], d['senast']['klockslag']), ('Europe/Stockholm', '07:00'))
        self.assertFalse(bevakning.dags(nar=sen + timedelta(hours=1)))

    def test_intervallen_raknas_i_lokala_dagar(self):
        # i drift 2026-10-09: den första schemalagda körningen kom 19:04 lokal tid (12,1 h sent). Nästa dags körning 07:00
        # prövar ändå de dagliga frågorna, och veckans fråga prövas sju lokala dagar senare, inte först dagen därpå
        idag = datetime.now(bevakning.TZ).date()

        def lokal(dagar, h, m):
            d = idag + timedelta(days=dagar)
            return datetime(d.year, d.month, d.day, h, m, tzinfo=bevakning.TZ).astimezone(timezone.utc)

        def z(t):
            return t.strftime('%Y-%m-%dT%H:%M:%SZ')
        forsta = lokal(0, 19, 4)
        self.drift(forsta)
        d = bevakning.kor(automatisk=True, nar=forsta)
        self.assertEqual(d['fragor']['sessioner']['nasta'], z(lokal(1, 7, 0)))
        self.assertEqual(d['fragor']['veckofraga']['nasta'], z(lokal(7, 7, 0)))
        self.assertEqual({q['id']: q['nasta'] for q in bevakning.lage()['fragor']}['sessioner'], z(lokal(1, 7, 0)), 'dashboarden visar samma tid')
        morgon = lokal(1, 7, 5)
        self.assertTrue(bevakning.dags(nar=morgon))
        self.drift(morgon)
        d = bevakning.kor(automatisk=True, nar=morgon)
        self.assertEqual(d['fragor']['sessioner']['senaste_forsok'], z(morgon), 'den dagliga frågan prövas nästa lokala dag, också efter en sen körning')
        self.assertEqual(d['fragor']['veckofraga']['senaste_forsok'], z(forsta), 'veckans fråga väntar')
        sjunde = lokal(7, 7, 5)
        self.drift(sjunde)
        d = bevakning.kor(automatisk=True, nar=sjunde)
        self.assertEqual(d['fragor']['veckofraga']['senaste_forsok'], z(sjunde))
        # Codex granskningar: en vecka räknas i lokala dagar, och en fallen görs om vid nästa lokala dags körning
        (self.ut / 'codex').mkdir(parents=True, exist_ok=True)
        (self.ut / 'codex' / 'veckofraga-a.json').write_text(json.dumps({'tid': z(lokal(0, 18, 55)), 'fraga': 'veckofraga', 'fynd': []}))
        (self.ut / 'codex' / 'en-lucka-a.json').write_text(json.dumps({'tid': z(lokal(0, 18, 58)), 'fraga': 'en-lucka', 'fynd': [], 'fel': 'prov'}))
        self.assertEqual(bevakning.codex_dags(nar=lokal(0, 23, 59)), [])
        self.assertEqual(bevakning.codex_dags(nar=lokal(1, 7, 0)), ['en-lucka'])
        self.assertNotIn('veckofraga', bevakning.codex_dags(nar=lokal(6, 7, 0)))
        self.assertIn('veckofraga', bevakning.codex_dags(nar=lokal(7, 7, 0)))

    def test_fynd_kanns_igen_och_blir_signaler_en_gang(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar, version='v1')
        d1 = bevakning.kor(nar=nar)
        self.assertEqual(d1['fragor']['sessioner']['versioner'], {'Provets release notes': 'v1'}, 'första körningen sätter baslinjen')
        self.drift(nar, version='v2', rader=[{'id': 'npm-global:@anthropic-ai/claude-code', 'namn': 'Claude Code', 'fran': '2.1.290', 'till': '2.1.291',
                                              'resultat': 'uppdaterad'}], underhall_slut=nar + timedelta(minutes=1))
        d2 = bevakning.kor(nar=nar + timedelta(days=1))
        dag = json.loads(sorted((self.ut / 'dag').glob('*.json'))[-1].read_text())
        typer = sorted(f['typ'] for f in dag['handlingsbart'] if f['fraga'] == 'sessioner')
        self.assertEqual(typer, ['beroende_uppdaterad', 'kalla_andrad'])
        poster = json.loads((self.fb / 'FORBATTRINGAR.json').read_text())['poster']
        self.assertTrue(any(p['problem'] == 'bevakning-sessioner' for p in poster.values()))
        antal = sum(len(p['signaler']) for p in poster.values())
        # samma läge igen nästa dag (spanaren och underhållet har kört igen, utan förändring): inget nytt, fynden står
        # kvar, inga nya signaler
        self.drift(nar + timedelta(days=2), version='v2', rader=[{'id': 'npm-global:@anthropic-ai/claude-code', 'namn': 'Claude Code', 'fran': '2.1.290',
                                                                   'till': '2.1.291', 'resultat': 'uppdaterad'}])
        bevakning.kor(nar=nar + timedelta(days=2))
        dag = json.loads(sorted((self.ut / 'dag').glob('*.json'))[-1].read_text())
        self.assertFalse([f for f in dag['handlingsbart'] if f['fraga'] == 'sessioner'])
        self.assertGreaterEqual(dag['kvarstaende'], 1)
        poster = json.loads((self.fb / 'FORBATTRINGAR.json').read_text())['poster']
        self.assertEqual(sum(len(p['signaler']) for p in poster.values()), antal)
        self.assertEqual(d2['fragor']['en-lucka']['utfall'], 'ej_utford', 'luckan har sin kontroll: Codex granskning, inte gjord än')

    def test_misslyckad_kontroll_ar_inte_inget_nytt(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar, fel='OSError: Källsvaret översteg bytetaket')
        d = bevakning.kor(nar=nar)
        self.assertEqual(d['fragor']['sessioner']['utfall'], 'ofullstandig', 'källan föll, underhållet lyckades: ofullständig, aldrig inget nytt')
        self.assertEqual(d['senast']['utfall'], 'delvis')
        dag = json.loads(sorted((self.ut / 'dag').glob('*.json'))[-1].read_text())
        self.assertNotEqual(dag['besked'], 'inget handlingsbart i dag', 'inget handlingsbart kräver lyckade kontroller')
        self.assertIn('sessioner', [x['id'] for x in dag['kontroller_som_inte_lyckades']])
        self.assertEqual(d['fragor']['veckofraga']['utfall'], 'ofullstandig', 'källan prövad men Codex analys utebliven: ofullständig')
        self.assertTrue(any('Codex granskning har inte gjorts' in x for x in d['fragor']['veckofraga']['problem']))

    def test_bevakningen_av_bevakningen(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar - timedelta(days=4), underhall_slut=nar - timedelta(days=3))
        d = bevakning.kor(nar=nar)
        meta = {m['id']: m for m in d['meta']}
        self.assertEqual(meta['spanaren']['utfall'], 'fynd')
        self.assertIn('äldre än två intervall', meta['spanaren']['text'])
        self.assertEqual(meta['underhallet']['utfall'], 'fynd')
        self.assertNotIn('startkontrollens-grans', meta, 'startkontrollens gräns följer spanarens intervall (två intervall)')
        import verktygslada
        with patch.dict(verktygslada.GILTIGHET, {'spaning': 7 * 24 * 3600}):  # gränsen före 2026-10-09: en vecka
            meta = {m['id']: m for m in bevakning.meta(bevakning.kataloger(), nar)}
        self.assertEqual(meta['startkontrollens-grans']['utfall'], 'fynd', 'en gräns på 7 dygn för en daglig spaning upptäcks')

    def test_tva_korningar_samtidigt(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        k = bevakning.kataloger()
        with bevakning.last(k) as fick:
            self.assertTrue(fick)
            self.assertEqual(bevakning.kor(nar=nar), {'hoppad': 'en annan bevakningskörning pågår'})

    def test_codex_svar_ar_granskarforslag(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        svar = self.rot / 'svar.json'
        svar.write_text(json.dumps({'fynd': [{'fraga': 'veckofraga', 'forandring': 'ny artikel om metodval', 'steg': 'forberedelse', 'observerat': 'x',
                                              'kallans_stod': 'y', 'tolkning': 'z', 'nytta_risk': 'n', 'minsta_forsok': 'm', 'hur_vi_vet': 'h', 'beslut': 'senare',
                                              'kallor': [{'url': 'https://example.org/a', 'datum_eller_version': '2026-10-01', 'last': 'originalet'}]}]}))
        self.assertEqual(bevakning.codex_svar(svar), [{'fraga': 'veckofraga', 'beslut': 'senare'}])
        d = bevakning.kor(nar=nar)
        self.assertEqual(d['fragor']['veckofraga']['utfall'], 'fynd')
        dag = json.loads(sorted((self.ut / 'dag').glob('*.json'))[-1].read_text())
        f = [x for x in dag['handlingsbart'] if x['fraga'] == 'veckofraga' and x['typ'] == 'codex'][0]
        self.assertIn('Granskarförslag från codex (inte ägarens beslut)', f['text'])
        paket = bevakning.codex_paket(self.rot / 'paket')
        self.assertEqual(paket['fragor'], ['veckofraga', 'en-lucka'])
        self.assertEqual(sorted(p.name for p in (self.rot / 'paket').iterdir()), ['AGENTS.md', 'bevakning.json', 'schema.json'])

    def test_automatisk_codex_granskning_efter_intervall(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        anrop = []

        def korare(kat, prompt, ut, logg):
            q = json.loads((Path(kat) / 'bevakning.json').read_text())['fragor'][0]['id']
            anrop.append(q)
            if q == 'en-lucka':
                return 1, 'prov-modell', None  # en granskning som faller
            Path(ut).write_text(json.dumps({'fynd': [{'fraga': q, 'forandring': 'inget', 'steg': 'x', 'observerat': 'x', 'kallans_stod': 'x',
                                                       'tolkning': 'x', 'nytta_risk': 'x', 'minsta_forsok': 'x', 'hur_vi_vet': 'x', 'beslut': 'inget_nytt',
                                                       'kallor': [{'url': 'https://example.org', 'datum_eller_version': '2026-10-09', 'last': 'originalet'}]}]}))
            Path(logg).write_text('model: prov-modell\ntokens used\n12 345\n')
            return 0, 'prov-modell', 12345
        self.assertEqual(bevakning.codex_vid_behov(nar=nar, korare=korare), [], 'utanför huvudutcheckningen är Codex av som standard')
        os.environ['NWP_BEVAKNING_CODEX'] = 'pa'
        self.assertEqual(sorted(bevakning.codex_dags(nar=nar)), ['en-lucka', 'veckofraga'])
        rader = bevakning.codex_vid_behov(nar=nar, korare=korare)
        self.assertEqual(sorted(anrop), ['en-lucka', 'veckofraga'])
        self.assertEqual({r['fraga']: (r.get('tokens'), bool(r.get('fel'))) for r in rader}, {'veckofraga': (12345, False), 'en-lucka': (None, True)})
        idag = datetime.now(bevakning.TZ).date()
        self.assertEqual(bevakning.codex_dags(nar=datetime(idag.year, idag.month, idag.day, 23, 59, tzinfo=bevakning.TZ)), [],
                         'ingen ny granskning samma lokala dag')
        self.assertEqual(bevakning.codex_dags(nar=nar + timedelta(days=1, minutes=1)), ['en-lucka'], 'en fallen granskning görs om nästa lokala dag')
        self.assertIn('veckofraga', bevakning.codex_dags(nar=nar + timedelta(days=7)))
        d = bevakning.kor(nar=nar)
        self.assertEqual(d['fragor']['en-lucka']['utfall'], 'misslyckad', 'en fallen granskning är aldrig inget nytt')
        self.assertEqual(d['fragor']['veckofraga']['utfall'], 'inget_nytt', 'källan hämtad och Codex har faktiskt kontrollerat: inget nytt')
        logg = [json.loads(r) for r in (self.ut / 'codex-korningar.jsonl').read_text().splitlines()]
        self.assertEqual(len(logg), 2)
        with patch.dict(os.environ, {'NWP_BEVAKNING_CODEX': 'av'}):
            self.assertEqual(bevakning.codex_vid_behov(nar=nar + timedelta(days=40), korare=korare), [])

    def test_tokens_med_hart_mellanslag_och_svar_per_fraga(self):
        import subprocess as sp
        logg = self.rot / 'codex.log'
        kat = self.rot / 'kat'
        kat.mkdir()
        (kat / 'schema.json').write_text('{}')

        class Klar:
            pid = 0

            def __init__(self, *a, **kw):
                Path(logg).write_text('model: gpt-prov\ntokens used\n59\u00a0720\n')

            def wait(self, timeout=None):
                return 0
        with patch.object(sp, 'Popen', Klar), patch('shutil.which', return_value='/bin/codex'):
            self.assertEqual(bevakning._kor_codex(kat, 'p', kat / 'svar.json', logg), (0, 'gpt-prov', 59720))
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        svar = self.rot / 'tva.json'
        rad = {'steg': 'x', 'observerat': 'x', 'kallans_stod': 'x', 'tolkning': 'x', 'nytta_risk': 'x', 'minsta_forsok': 'x', 'hur_vi_vet': 'x',
               'kallor': [{'url': 'https://example.org', 'datum_eller_version': '2026-10-09', 'last': 'originalet'}]}
        svar.write_text(json.dumps({'fynd': [dict(rad, fraga='veckofraga', forandring='ett fynd', beslut='senare'),
                                             dict(rad, fraga='veckofraga', forandring='inget', beslut='inget_nytt'),
                                             dict(rad, fraga='en-lucka', forandring='annan fråga', beslut='nu')]}))
        ut = bevakning.codex_svar(svar, bara='veckofraga')
        self.assertIn({'fraga': 'en-lucka', 'fel': 'gäller inte den granskade frågan'}, ut)
        filer = list((self.ut / 'codex').glob('*.json'))
        self.assertEqual([f.name.split('-2')[0] for f in filer], ['veckofraga'], 'en fil för frågan, ingen för en annan fråga')
        self.assertEqual(len(json.loads(filer[0].read_text())['fynd']), 1, 'fyndet försvinner inte för att en senare post säger inget nytt')

    def test_underhallets_fel_och_saknade_beroenden_ar_problem(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        u = json.loads((self.uh / 'UNDERHALL.json').read_text())
        u.update(rader=[{'id': 'npm-global:@anthropic-ai/claude-code', 'namn': 'Claude Code', 'resultat': 'behallen', 'detalj': 'tillfälligt fel: npm svarade inte'}],
                 inventering=[{'id': 'npm-global:@anthropic-ai/claude-code', 'namn': 'Claude Code'}])
        (self.uh / 'UNDERHALL.json').write_text(json.dumps(u))
        q = bevakning.register()[0]['sessioner']
        f, p_, _ = bevakning._underhall(q, bevakning.kataloger(), {})
        self.assertTrue(any('tillfälligt fel' in x for x in p_), p_)
        q2 = dict(q, beror=['mobbin'])
        u['prov'] = {'Mobbin': {'resultat': 'fel', 'detalj': 'inloggningen gick ut'}}
        (self.uh / 'UNDERHALL.json').write_text(json.dumps(u))
        self.assertTrue(any('förmågeprovet Mobbin' in x for x in bevakning._underhall(q2, bevakning.kataloger(), {})[1]))
        q3 = dict(q, beror=['finns-inte'])
        self.assertTrue(any('finns inte i underhållets' in x for x in bevakning._underhall(q3, bevakning.kataloger(), {})[1]))

    def test_forbrukningen_matts_och_kvoten_star_som_saknad(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        sv = self.rot / 'underlag' / 'en-kund' / 'atelje' / 'svar-plan.json'
        sv.parent.mkdir(parents=True)
        sv.write_text(json.dumps({'total_cost_usd': 7.41, 'num_turns': 72, 'duration_ms': 352985,
                                  'modelUsage': {'claude-fable-5-1': {'outputTokens': 24023, 'costUSD': 7.41}}}))
        with patch.dict(os.environ, {'NWP_FORBRUKNING_ROT': str(self.rot / 'underlag')}):
            d = bevakning.kor(nar=nar)
        r = d['fragor']['forbrukningen']
        self.assertEqual(r['utfall'], 'fynd')
        self.assertEqual((r['forbrukning']['sessioner'], r['forbrukning']['listpris_usd'], r['forbrukning']['tokens_ut']), (1, 7.41, 24023))
        self.assertTrue(any('kvot' in x for x in r['problem']), 'kvoten är ett saknat mätvärde')

    def test_byggstarten_redovisar_bevakningen(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        self.assertEqual(bevakning.byggstart('en-kund', nar=nar)['status'], 'okand', 'bevakningen har inte körts')
        bevakning.kor(nar=nar)
        b = bevakning.byggstart('en-kund', nar=nar)
        self.assertIn('senaste bevakningen', b['detalj'])
        self.assertIn('en-lucka', b['luckor'])
        lage = json.loads((self.ut / 'LAGE.json').read_text())
        self.assertEqual(lage['fragor']['infor-byggstart']['kund'], 'en-kund')

    def test_lage_for_dashboarden(self):
        nar = datetime.now(timezone.utc)
        self.drift(nar)
        bevakning.kor(nar=nar)
        lage = bevakning.lage()
        self.assertEqual(set(lage['tackning']), set(bevakning.OMRADEN))
        self.assertEqual(lage['tackning']['juridik']['lage'], 'inaktuell', 'luckans kontroll är inte gjord')
        self.assertEqual(lage['tackning']['juridik']['luckor'], ['ingen juridisk bedömning'])
        self.assertFalse(lage['aktiv'], 'en manuell körning gör inte bevakningen aktiv')
        self.assertTrue(lage['dag'])


if __name__ == '__main__':
    unittest.main()
