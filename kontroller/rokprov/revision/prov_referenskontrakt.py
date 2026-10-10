#!/usr/bin/env python3
"""Referenskontraktet genom de verkliga ingångarna (ägarens uppdrag 2026-10-10 om obligatorisk branschresearch och om
hela referenskedjan); inga modeller eller nätanrop: sessionerna är attrapper och paketet syntetiskt.

- Tomma genomgångar, saknade sökningar och ett Awwwards som aldrig prövades stoppar researchen.
- En påstådd sökning som loggen inte visar står som kunskap ur minnet.
- Trasiga belägg, fel paketversion och värdeord utan observation stoppar planen; planeringen gör ett omförsök och stoppar.
- En äldre plan och en återupptagning kan inte kringgå kravet: skissa och skapa startar ingen session.
- Komplett underlag når rätt skapare: UPPDRAG.md bär bidragen med bilderna, ur just den planen.
- Researchrollen ensam får webben, bakom kundvakten; blindningen består.
- En fångst som dödas vid sin tidsgräns lämnar de sajter som hann fångas helt, med båda rollerna, i ett paket som går att
  läsa och ärva; kompletteringen ärver aldrig ett paket utan PAKET.json, och tidsgränsen redovisas (kandidatprovet
  2026-10-10).

--bas kör fallen mot HEAD:s kandidater.py, atelje.py, kundvakt.py, skapande.py och referens.py (föreprovet).
"""
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
import referensfixtur  # noqa: E402

if '--bas' in sys.argv:
    sys.argv.remove('--bas')
    for namn in ('kundvakt', 'skapande', 'referens', 'atelje', 'kandidater'):
        src = subprocess.run(['git', 'show', 'HEAD:kontroller/%s.py' % namn], cwd=ROOT, check=True, capture_output=True, text=True).stdout
        m = types.ModuleType(namn)
        m.__file__ = str(ROOT / 'kontroller' / ('%s.py' % namn))
        sys.modules[namn] = m
        exec(compile(src, m.__file__, 'exec'), m.__dict__)
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import kandidater as kd  # noqa: E402
import kundvakt  # noqa: E402
import referens as rf  # noqa: E402
import skapande  # noqa: E402
try:
    import referenskontrakt as rk  # noqa: E402
except ImportError:  # basen saknar modulen
    rk = None

SLUG = 'refkontrakt-prov'
PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000') + b'\x00' * 20
SID = '22222222-3333-4444-8555-666666666666'


def anrop(i, namn, data):
    return {'type': 'tool_use', 'id': i, 'name': namn, 'input': data}


def svar(i, text='ok', fel=False):
    return {'type': 'tool_result', 'tool_use_id': i, 'content': text, 'is_error': fel}


class Grund(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'referenskontraktets prov'))).resolve()
        self.u = self.tmp / 'underlag'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.u, KUNDER=self.tmp / 'kunder'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projects'))
        (self.tmp / 'projects' / 'p').mkdir(parents=True)
        v = {'schema': 1, 'namn': 'Provverkstan Lera', 'fiktiv': True, 'adress': {'ort': 'Provstad', 'gata': 'Provgatan 3', 'postnummer': '123 45'},
             'kontaktvagar': [{'typ': 'telefon', 'varde': '070-174 06 11'}], 'tjanster': ['Kurser']}
        (self.u / SLUG).mkdir(parents=True)
        (self.u / SLUG / 'VERKSAMHET.json').write_text(json.dumps(v, ensure_ascii=False))
        self.paket = self.u / SLUG / 'referenser' / 'paket-v01'

    def bygg_paket(self, bransch=3, insp=2, namn_paket='paket-v01'):
        p = self.u / SLUG / 'referenser' / namn_paket
        kand = []
        for i in range(bransch):
            kand.append(self.sajt(p, 'bransch-%d' % i, 'bransch', {'vag': 'websok', 'kalla': 'keramikkurs drejning'}))
        for i in range(insp):
            kand.append(self.sajt(p, 'galleri-%d' % i, 'hantverk', {'vag': 'galleri', 'kalla': 'https://www.awwwards.com/sites/galleri-%d' % i}))
        (p / 'PAKET.json').write_text(json.dumps({'schema': 2, 'version': namn_paket, 'kandidater': kand}))
        return p

    def sajt(self, p, namn, roll, upptackt):
        kat = p / namn / '01-start'
        kat.mkdir(parents=True)
        for b in ('390', '1440'):
            (kat / ('vy-%s-forsta.png' % b)).write_bytes(PNG)
        (kat / 'vy-390-hela.png').write_bytes(PNG)
        (kat / 'SEKTIONER.md').write_text('# Sektioner\n')
        (kat / 'vy-390-aria.txt').write_text('- form "Boka": button "Skicka"\n')  # bokningens funktionsbelägg
        return {'namn': namn, 'adress': 'https://%s.example/' % namn, 'roll': roll, 'ok': True, 'upptackt': upptackt, 'uppgift': ['komposition'],
                'sidor': [{'sida': '/', 'katalog': '%s/01-start' % namn, 'ok': True}]}

    def logg(self, awwwards=True, sok=True):
        ut = []
        if sok:
            ut.append({'verktyg': 'WebSearch', 'fraga': 'keramikkurs drejning studio', 'url': None, 'fel': None,
                       'traffar': ['https://bransch-0.example/', 'https://bransch-1.example/']})
        if awwwards:
            ut.append({'verktyg': 'WebFetch', 'fraga': None, 'url': 'https://www.awwwards.com/sites/galleri-0', 'fel': None, 'traffar': ['https://galleri-0.example/']})
        return ut

    def bel(self, namn):
        return 'underlag/%s/referenser/paket-v01/%s/01-start/vy-1440-forsta.png' % (SLUG, namn)

    def research(self, logg=None):
        return {'sok': self.logg() if logg is None else logg, 'urvalsfragor': referensfixtur.URVALSFRAGOR, 'tackning': referensfixtur.TACKNING}

    def plan(self):
        text = 'Rubriken bär ett konkret erbjudande i första vyn med pris och nästa kurstillfälle synligt direkt'
        bransch = [dict(referensfixtur.branschrad(SLUG, 'bransch-%d' % i), belagg=[self.bel('bransch-%d' % i)]) for i in range(3)]
        fb = [dict(referensfixtur.forebild(SLUG, 'galleri-%d' % i), belagg=[self.bel('galleri-%d' % i)]) for i in range(2)]
        bid = [{'kalla': 'bransch-0', 'roll': 'bransch', 'uppgift': 'kontakt', 'kundbehov': 'besökaren vill boka en kursplats snabbt',
                'observerad_kvalitet': text, 'matbart': False, 'beslut': 'infor', 'designbeslut': 'kurstillfällena först med boka-knapp intill',
                'tillampning': 'en kurslista med datum och plats överst i första vyn', 'bedomning': 'jämför 390 första vyn mot beläggets 390',
                'belagg': [self.bel('bransch-0')]},
               {'kalla': 'galleri-0', 'roll': 'visuellt', 'uppgift': 'bildregi', 'kundbehov': 'visa verkstaden och händerna i arbete',
                'observerad_kvalitet': text, 'matbart': False, 'beslut': 'anpassar', 'designbeslut': 'stor beskuren arbetsbild med kort rubrik över',
                'tillampning': 'helbild i första vyn med beskärning efter bildens uppgift', 'bedomning': 'jämför 1440 första vyn mot beläggets 1440',
                'belagg': [self.bel('galleri-0')]}]
        return {'paket': 'paket-v01', 'referenskontrakt': {'version': 1}, 'bransch': bransch, 'forebilder_utanfor': fb,
                'kandidater': {'k01': {'titel': 'Kurserna först', 'huvudreferens': 'egen', 'referensbilder': [], 'referensbidrag': bid}}}


@unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
class Researchen(Grund):
    def test_tomma_genomgangar_och_saknade_sokningar_stoppar(self):
        self.assertTrue(rk.researchbrister(SLUG, self.u, self.research(), None), 'utan paket')
        self.bygg_paket(bransch=2, insp=0)
        fel = rk.researchbrister(SLUG, self.u, self.research([]), self.paket)
        self.assertTrue(any('branschsajter' in f for f in fel) and any('gallerierna' in f for f in fel) and any('webbsökning' in f for f in fel), fel)
        self.assertTrue(any('Awwwards' in f for f in fel), fel)

    def test_komplett_research_godkanns(self):
        self.bygg_paket()
        self.assertEqual(rk.researchbrister(SLUG, self.u, self.research(), self.paket), [])

    def test_awwwards_som_inte_provats_eller_misslyckades(self):
        self.bygg_paket()
        self.assertTrue(any('Awwwards' in f for f in rk.researchbrister(SLUG, self.u, self.research(self.logg(awwwards=False)), self.paket)))
        misslyckat = self.logg(awwwards=False) + [{'verktyg': 'WebFetch', 'url': 'https://www.awwwards.com/sites/x', 'fel': '403', 'traffar': []}]
        self.assertTrue(any('gallerisökning' in f for f in rk.researchbrister(SLUG, self.u, self.research(misslyckat), self.paket)),
                        'ett misslyckat Awwwards-besök är ingen genomförd undersökning')

    def test_pastadd_sokning_utan_logg_ar_kunskap(self):
        s = {'namn': 'x', 'adress': 'https://okand.example/', 'upptackt': {'vag': 'websok', 'kalla': 'keramik'}}
        self.assertEqual(rk.verifiera_upptackt(s, self.logg())['vag'], 'kunskap')
        s['adress'] = 'https://bransch-1.example/'
        self.assertEqual(rk.verifiera_upptackt(s, self.logg())['vag'], 'websok')

    def test_sokloggen_ur_transkriptet(self):
        f = self.tmp / 'projects' / 'p' / ('%s.jsonl' % SID)
        h = [anrop('w1', 'WebSearch', {'query': 'keramikkurs'}), svar('w1', 'Links: [{"url":"https://bransch-0.example/om"}]'),
             anrop('w2', 'WebFetch', {'url': 'https://www.awwwards.com/sites/a', 'prompt': 'vilken sajt'}), svar('w2', 'Request failed with status code 403', True)]
        f.write_text(''.join(json.dumps({'message': {'content': [x]}}) + '\n' for x in h))
        logg = rk.sokningar(f)
        self.assertEqual([x['verktyg'] for x in logg], ['WebSearch', 'WebFetch'])
        self.assertEqual(logg[0]['traffar'], ['https://bransch-0.example/om'])
        self.assertTrue(logg[1]['fel'] and not logg[1]['traffar'])


@unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
class Planen(Grund):
    def test_tom_branschgenomgang_och_trasiga_belagg_stoppar(self):
        self.bygg_paket()
        p = self.plan()
        self.assertEqual(rk.planbrister(SLUG, self.u, p, self.paket), [])
        p['bransch'] = []
        self.assertTrue(any('branschgenomgången' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)))
        p = self.plan()
        p['bransch'][0]['belagg'] = ['underlag/%s/referenser/paket-v01/bransch-0/01-start/saknas.png' % SLUG]
        self.assertTrue(any('trasiga belägg' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)))
        p = self.plan()
        p['forebilder_utanfor'][0]['kvalitet'] = 'premium och modernt'
        self.assertTrue(any('konkret observerad kvalitet' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)), 'värdeord är ingen observation')

    def test_fel_paketversion_stoppar(self):
        self.bygg_paket()
        self.bygg_paket(namn_paket='paket-v02')
        p = self.plan()
        p['kandidater']['k01']['referensbidrag'][0]['belagg'] = ['underlag/%s/referenser/paket-v02/bransch-0/01-start/vy-1440-forsta.png' % SLUG]
        fel = rk.kandidatbrister(SLUG, self.u, p['kandidater']['k01'], self.paket)
        self.assertTrue(any('paketversion' in f for f in fel), fel)

    def test_egen_design_kringgar_inte_och_bada_kallorna_kravs(self):
        self.bygg_paket()
        k = self.plan()['kandidater']['k01']
        self.assertEqual(rk.kandidatbrister(SLUG, self.u, k, self.paket), [])
        self.assertTrue(rk.kandidatbrister(SLUG, self.u, dict(k, referensbidrag=k['referensbidrag'][:1]), self.paket), 'bara branschen räcker inte')
        self.assertTrue(rk.kandidatbrister(SLUG, self.u, dict(k, referensbidrag=[]), self.paket), 'egen huvudreferens utan bidrag')


@unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
class Grunder(Grund):
    """Ägarens tillägg 2026-10-10: ort, sökplacering, storlek, omdömen och utmärkelser avgör aldrig ensamma en designförebild."""
    def test_hoga_omdomen_utan_granskad_sajt_ar_ingen_designreferens(self):
        self.bygg_paket(bransch=2)
        p = self.plan()
        p['bransch'][2] = dict(p['bransch'][2], sajt='omdomesstjarnan', anseende='4,9 av 5 i 412 omdömen', evidens='omdomen')
        fel = rk.planbrister(SLUG, self.u, p, self.paket)
        self.assertTrue(any('omdomesstjarnan' in f for f in fel) and any('branschgenomgången har 2' in f for f in fel), fel)
        self.assertTrue(any('branschsajter' in f for f in rk.researchbrister(SLUG, self.u, self.research(), self.paket)))

    def test_stjarnor_och_recensionsantal_styr_inget(self):
        self.bygg_paket()
        utfall = []
        for anseende in ('4,9 av 5 i 412 omdömen', '2,1 av 5 i 3 omdömen', 'okänt'):
            p = self.plan()
            for b in p['bransch']:
                b['anseende'] = anseende
            utfall.append(rk.planbrister(SLUG, self.u, p, self.paket))
        self.assertEqual(utfall, [[], [], []], 'anseendet styr inte designfiltreringen')
        p = self.plan()
        p['bransch'][0]['styrkor'] = 'Över 400 omdömen med snittbetyg 4,9 visar att sajten fungerar för kunderna och besökarna'
        self.assertTrue(any('omdömen, betyg' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)), 'omdömen förs inte in som designbevis')

    def test_annan_ort_ger_inget_battre_designbetyg(self):
        self.bygg_paket()
        a, b = self.plan(), self.plan()
        for r in a['bransch']:
            r['lokal_marknad'] = 'samma ort som kunden: besökarna jämför med den här'
        for r in b['bransch']:
            r['lokal_marknad'] = 'annan ort, ej relevant för uppgiften'
        self.assertEqual(rk.planbrister(SLUG, self.u, a, self.paket), rk.planbrister(SLUG, self.u, b, self.paket))
        self.assertEqual(rk.kandidatbrister(SLUG, self.u, a['kandidater']['k01'], self.paket),
                         rk.kandidatbrister(SLUG, self.u, b['kandidater']['k01'], self.paket))

    def test_bokningsreferensen_kraver_funktionsbelagg(self):
        self.bygg_paket()
        (self.paket / 'bransch-1' / '01-start' / 'vy-390-aria.txt').unlink()  # högt företagsbetyg, men bokningen är inte fångad
        k = self.plan()['kandidater']['k01']
        self.assertEqual(rk.kandidatbrister(SLUG, self.u, k, self.paket), [], 'bransch-0 har bokningens funktionsbelägg')
        k2 = json.loads(json.dumps(k))
        k2['referensbidrag'][0].update(kalla='bransch-1', belagg=[self.bel('bransch-1')])
        self.assertTrue(any('funktionsuppgiften kontakt' in f for f in rk.kandidatbrister(SLUG, self.u, k2, self.paket)))

    def test_prospektpoang_paverkar_inget(self):
        self.bygg_paket()
        bas = (rk.researchbrister(SLUG, self.u, self.research(), self.paket), rk.planbrister(SLUG, self.u, self.plan(), self.paket))
        d = json.loads((self.paket / 'PAKET.json').read_text())
        for poang in (95, 5, None):
            for k in d['kandidater']:
                k['poang'] = poang
            (self.paket / 'PAKET.json').write_text(json.dumps(d))
            self.assertEqual((rk.researchbrister(SLUG, self.u, self.research(), self.paket), rk.planbrister(SLUG, self.u, self.plan(), self.paket)), bas)
        kod = (ROOT / 'kontroller' / 'referenskontrakt.py').read_text() + (ROOT / 'kontroller' / 'kandidater.py').read_text()
        self.assertNotIn('prospekt_poang', kod)
        self.assertNotIn('import prospekt', kod)

    def test_branschledande_men_misslyckad_inspektion_ar_ingen_observation(self):
        self.bygg_paket()
        d = json.loads((self.paket / 'PAKET.json').read_text())
        d['kandidater'][0].update(ok=False, varfor='branschledande enligt sökträffen')
        d['kandidater'][0]['sidor'][0]['ok'] = False
        (self.paket / 'PAKET.json').write_text(json.dumps(d))
        self.assertTrue(any('branschsajter' in f for f in rk.researchbrister(SLUG, self.u, self.research(), self.paket)))
        self.assertTrue(any('lyckad fångst' in f for f in rk.planbrister(SLUG, self.u, self.plan(), self.paket)))

    def test_dubletter_och_www_varianter_raknas_en_gang(self):
        self.bygg_paket()
        d = json.loads((self.paket / 'PAKET.json').read_text())
        d['kandidater'][1]['adress'] = 'https://www.bransch-0.example/'
        d['kandidater'][2]['adress'] = 'https://bransch-0.example/tjanster/'
        (self.paket / 'PAKET.json').write_text(json.dumps(d))
        self.assertTrue(any('branschsajter' in f for f in rk.researchbrister(SLUG, self.u, self.research(), self.paket)))
        self.assertTrue(any('upprepar en sajt' in f for f in rk.planbrister(SLUG, self.u, self.plan(), self.paket)))

    def test_urvalsfragor_tackning_och_affarsframgang(self):
        self.bygg_paket()
        r = self.research()
        r['urvalsfragor'] = {}
        self.assertTrue(any('urvalsfrågorna' in f for f in rk.researchbrister(SLUG, self.u, r, self.paket)))
        p = self.plan()
        p['bransch'][0]['affarsframgang'] = 'framgångsrik och växer snabbt'
        self.assertTrue(any('affärsframgång utan belägg' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)))
        p['bransch'][0]['affarsframgang'] = 'okänt'
        p['bransch'][0]['stark_for'] = 'premium och modern'
        self.assertTrue(any('stark webbplatsreferens' in f for f in rk.planbrister(SLUG, self.u, p, self.paket)))


class Startvillkoret(Grund):
    def skapa_kandidat(self, plan):
        (self.u / SLUG / 'atelje').mkdir(parents=True, exist_ok=True)
        (self.u / SLUG / 'atelje' / 'KANDIDATPLAN.json').write_text(json.dumps(plan, ensure_ascii=False))
        kd.satt_status(SLUG, 'k01', 'planerad', 'uppdraget skrivet', titel='Kurserna först', forsok=0)

    def test_aldre_plan_och_aterupptagning_startar_ingen_skapare(self):
        self.bygg_paket()
        gammal = self.plan()
        gammal.pop('referenskontrakt')
        self.skapa_kandidat(gammal)
        with patch.object(atelje, 'session', side_effect=AssertionError('ingen skaparsession får starta')):
            st = kd.skissa(SLUG, 'k01')
        self.assertEqual(st.get('status'), 'fel', st)
        self.assertTrue(any('äldre än referenskontraktet' in b for b in st.get('referenskontrakt_brister') or []), st)

    @unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
    def test_komplett_underlag_nar_ratt_skapare(self):
        self.bygg_paket()
        plan = self.plan()
        self.skapa_kandidat(plan)
        kd.skriv_uppdrag(SLUG, 'k01', plan['kandidater']['k01'], 1, 1)
        text = (kd.kdir(SLUG, 'k01') / 'UPPDRAG.md').read_text()
        self.assertIn(rk.MARKOR, text)
        self.assertIn('- ' + self.bel('galleri-0'), text, 'bilderna står en per rad och kan öppnas med Read')
        self.assertIn(self.bel('bransch-0'), kd.uppdragets_bilder(SLUG, 'k01'))
        self.assertEqual(rk.startbrister(SLUG, self.u, plan, 'k01'), [])
        # en ändrad kedja utan nytt UPPDRAG.md stoppas
        plan['kandidater']['k01']['referensbidrag'][0]['tillampning'] = 'en annan tillämpning som aldrig skrevs till skaparen här'
        self.assertTrue(any('UPPDRAG.md' in b for b in rk.startbrister(SLUG, self.u, plan, 'k01')))

    @unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
    def test_planeringen_gor_ett_omforsok_och_stoppar(self):
        self.bygg_paket()
        (self.u / SLUG / 'atelje').mkdir(parents=True, exist_ok=True)
        anropen = []

        def falsk(prompt, *a, **k):
            anropen.append(prompt)
            p = self.plan()
            return {'structured_output': {'variation': 'v', 'bransch': [], 'forebilder_utanfor': p['forebilder_utanfor'],
                                          'kandidater': [dict(p['kandidater']['k01'], ide='i', hypotes='h')]}, 'session_id': None}
        with patch.object(atelje, 'session', falsk), patch.object(kd.kompetens, 'kravbrister', return_value=[]), \
                patch.object(kd, 'planbrist', return_value=None), patch.object(kd, 'referensbrist', return_value=None), \
                patch.object(kd, 'plan_prompt', lambda slug, n, skiss=False, fel=None: 'PLAN fel=%s' % fel):  # prompten prövas i prov_revision
            with self.assertRaises(RuntimeError) as e:
                kd.planera(SLUG, 1, 'skiss')
        self.assertEqual(len(anropen), 2, 'ett omförsök med bristerna')
        self.assertIn('branschgenomgången', anropen[1])
        self.assertIn('referenskontraktet', str(e.exception))
        self.assertFalse((self.u / SLUG / 'atelje' / 'KANDIDATPLAN.json').exists(), 'ingen plan skrivs')


class Webben(Grund):
    def args(self, **k):
        return atelje.session_args(['Read'], slug=SLUG, **k)

    def test_bara_researchrollen_far_webben_och_aldrig_som_allow(self):
        with patch.object(atelje, 'refero_mcp_fil', return_value='r.json'), patch.object(atelje, 'tjugoforsta_mcp_fil', return_value='t.json'):
            utan = self.args()
            med = self.args(webb=True)
        tools = lambda a: a[a.index('--tools') + 1].split(',')  # noqa: E731
        neka = lambda a: a[a.index('--disallowedTools') + 1:]  # noqa: E731
        tillat = lambda a: a[a.index('--allowedTools') + 1:a.index('--disallowedTools')]  # noqa: E731
        self.assertNotIn('WebSearch', tools(utan))
        self.assertIn('WebSearch', neka(utan))
        self.assertIn('WebSearch', tools(med))
        self.assertIn('WebFetch', tools(med))
        self.assertNotIn('WebSearch', neka(med))
        self.assertNotIn('WebSearch', tillat(med), 'kundvaktens uttryckliga tillåtelse krävs, aldrig en allow-regel')
        with self.assertRaises(ValueError):
            atelje.session_args(['Read'], slug=SLUG, webb=True, blind='x.json')

    def test_kundvakten_provar_sokfragor_och_adresser(self):
        p = lambda namn, inp: kundvakt.provning(SLUG, self.u, {'tool_name': namn, 'tool_input': inp})  # noqa: E731
        self.assertIsNone(p('WebSearch', {'query': 'keramikkurs drejning för nybörjare'}))
        self.assertTrue(p('WebSearch', {'query': 'keramik Provstad'}), 'kundens ort')
        self.assertTrue(p('WebSearch', {'query': 'Provverkstan Lera kurser'}), 'kundens namn')
        self.assertTrue(p('WebFetch', {'url': 'http://exempel.example/', 'prompt': 'x'}), 'bara https')
        self.assertIsNone(p('WebFetch', {'url': 'https://www.awwwards.com/sites/helbak-ceramics', 'prompt': 'vilken sajt och utmärkelse'}))
        self.assertIn('WebSearch', kundvakt.MATCH)

    def test_blindningen_bestar(self):
        self.assertNotIn('UPPDRAG.md', kd.BLIND_LASBART)
        (self.u / SLUG / 'atelje' / 'kandidater' / 'k01').mkdir(parents=True)
        (self.u / SLUG / 'atelje' / 'kandidater' / 'k01' / 'UPPDRAG.md').write_text('skaparens uppdrag')
        nekas = ' '.join(kd.blind_nekas(SLUG, 'k01', ('varv',)))
        self.assertIn('kandidater', nekas)



@unittest.skipIf(rk is None, 'basen saknar referenskontraktet')
class Fangsten(Grund):
    """Fångstens tidsgräns (kandidatprovet 2026-10-10): åtta sajter nådde 1 800 s, det halva paketet saknade PAKET.json,
    kontraktet såg noll sajter och omförsöket kunde inte ärva."""
    def uppdrag(self):
        k = lambda n, roll: {'namn': n, 'adress': 'https://%s.se/' % n, 'roll': roll, 'varfor': 'prov', 'sidor': ['/'], 'tillstand': {},  # noqa: E731
                             'upptackt': {'vag': 'websok', 'kalla': 'prov'} if roll == 'bransch' else
                             {'vag': 'galleri', 'kalla': 'https://www.awwwards.com/sites/%s' % n}, 'uppgift': ['komposition']}
        return {'fragor': [], 'kandidater': [k('bransch-0', 'bransch'), k('bransch-1', 'bransch'), k('bransch-2', 'bransch'),
                                             k('galleri-0', 'hantverk'), k('galleri-1', 'hantverk')]}

    def fanga(self, dod_vid=None):
        """Fångar uppdraget med en attrapp för webbläsaren; processen dödas (KeyboardInterrupt, som ingen except fångar)
        när dod_vid sajter är klara."""
        klara = []

        def kor(adress, ut, tillat, tillstand, miljo, extrahera=None, bredder=rf.BREDDER_STANDARD):
            if str(ut).endswith('.pass1'):
                return 0, {}, ''
            if dod_vid is not None and len(klara) == dod_vid:
                raise KeyboardInterrupt('tidsgränsen: processen dödas mitt i nästa sajt')
            Path(ut).mkdir(parents=True, exist_ok=True)
            for b in bredder:
                (Path(ut) / ('vy-%s-forsta.png' % b)).write_bytes(PNG)
            klara.append(adress)
            return 0, {'ok': True}, ''

        def obs(rapport, ut, bestallda=(), bredder=rf.BREDDER_STANDARD):
            return {'ok': True, 'vyer': {b: {'bildfiler': {'vy-%s-forsta.png' % b: True}} for b in bredder}, 'kvar_blockerade': [],
                    'fel_resurser': [], 'begransningar': []}
        with patch.multiple(rf, kor_inspektera=kor, observationer=obs, blockerade_ursprung=lambda *a, **k: []):
            try:
                rf.samla(SLUG, self.uppdrag(), self.u)
            except KeyboardInterrupt:
                pass
        return skapande.senaste_paket(SLUG, self.u)

    def test_avbruten_fangst_behaller_det_som_hann_fangas_med_bada_rollerna(self):
        p = self.fanga(dod_vid=3)
        d = json.loads((p / 'PAKET.json').read_text())
        self.assertTrue(d.get('pagar'), 'paketet är märkt som avbrutet, aldrig som klart')
        self.assertFalse(d.get('alla_ok'))
        self.assertEqual([k['namn'] for k in d['kandidater']], ['bransch-0', 'galleri-0', 'bransch-1'], 'rollerna varvade i fångstordningen')
        self.assertEqual(skapande.senaste_lasbara_paket(SLUG, self.u), p)
        fel = rk.researchbrister(SLUG, self.u, self.research(), p)
        self.assertTrue(any('2 fångade branschsajter' in x for x in fel), fel)  # kontraktet räknar det som fångades, inte noll
        self.assertTrue(any('1 fångade sajter ur gallerierna' in x for x in fel), fel)

    def test_hel_fangst_ar_klar_utan_markering(self):
        d = json.loads((self.fanga() / 'PAKET.json').read_text())
        self.assertNotIn('pagar', d)
        self.assertTrue(d['alla_ok'])
        self.assertEqual(len(d['kandidater']), 5)

    def test_kompletteringen_arver_inte_ett_paket_utan_pakettext_och_tidsgransen_redovisas(self):
        self.bygg_paket()  # paket-v01 läsbart
        (self.u / SLUG / 'referenser' / 'paket-v02' / 'bransch-9').mkdir(parents=True)  # dödat före första färdiga sajt
        r = self.tmp / 'rot'
        r.mkdir()
        sedda = []

        def kor(args, frist):
            if 'referens.py' in args[2]:
                sedda.append(json.loads(Path(args[-1]).read_text()) if Path(args[-1]).is_absolute() else json.loads((ROOT / args[-1]).read_text()))
                raise subprocess.TimeoutExpired(args, frist)
            return types.SimpleNamespace(returncode=0, stdout='', stderr='')
        f = r / 'begaran.json'
        f.write_text(json.dumps({'varfor': 'prov', 'referens': {'kandidater': [{'namn': 'ny-sajt', 'adress': 'https://ny-sajt.se/', 'roll': 'bransch',
                                                                                 'varfor': 'prov', 'sidor': ['/']}]}}))
        ut = skapande.komplettera(SLUG, f, r, self.u, frist=7, kor=kor, bred=True, forbjudna={'ord': set(), 'siffror': set()})
        self.assertEqual(sedda[0].get('kompletterar'), 'paket-v01', 'ärver det senaste läsbara paketet, aldrig katalogen utan PAKET.json')
        self.assertIsNone(ut['referens']['rc'])
        self.assertEqual(ut['referens'].get('tidsgrans'), 7)
        self.assertTrue(ut['referens'].get('paket'), 'tidsgränsen redovisas med paketet som bär det som hann fångas')


if __name__ == '__main__':
    unittest.main(verbosity=1)
