#!/usr/bin/env python3
"""Designstudions källbundna visuella kontroller (designstudion 2026-10-11, DS3; kunskap/designstudio.md) med provkandidaten
ur studio_fixtur.py i en isolerad rot: riktiga byggen innanför processgränsen (studions förhandsbygge), kandidatens
ordinarie fotografering och motorns sond i en egen webbläsare, utan modell. Fallen står vid sina acceptansprov
(byggpaketets ACCEPTANSPROV.md):

- källkartan: id i förhandsbygget, samma id ur källan, inga id i produktionsbygget (DS-U16, DS-U33);
- ägarskap och tvetydighet: samma text i två komponenter, en text ur en lista, ett känt prop-värde, en delad token
  (DS-U16); direktredigeringens textsökning nekar den delade texten;
- typografi, bildregi (mobil och dator var för sig, bildval), mellanrum (kortformens del, en mellanbredd), komposition
  (variant och sektionsordning) och färg (lokal och designgrund) sparas i rätt källa och kontrolleras efter bygget
  (DS-U18–DS-U22);
- en stale källa ger konflikt utan att skriva över, ett fallerat bygge lägger tillbaka originalet (DS-U23, DS-U24);
- samma ändrings-id ger samma begäran, och värden som försöker bli mer än ett värde nekas (DS-U14, DS-U32);
- blindningen: kontrollerna och sparandet finns först efter ägarens första val;
- bedömbar är inte bara laddad, och skaparens version publiceras tidigt, står vid ett stopp och tas upp igen över ett halvt
  svar (DS-U06, DS-U07, DS-U27); en skrivare per kandidat, och en kandidat vid sin gräns kan ändras medan andra arbetar
  (DS-U26).

    .venv/bin/python -B kontroller/rokprov/revision/prov_designstudio.py

Kräver rökprovets byggda mallsajt (kunder/rokprov-mall/sajt med node_modules, som rokprov.sh bygger tidigare); saknas den
hoppas provet över med skälet, och i rökprovet fäller ett överhoppat prov rökprovet.
"""
import contextlib
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import server as dash  # noqa: E402
import atelje  # noqa: E402
import direktredigering  # noqa: E402
import flodesstart  # noqa: E402
import kandidater  # noqa: E402
import korregister  # noqa: E402
import meddelanden  # noqa: E402
import observation  # noqa: E402
import prova  # noqa: E402
import studio  # noqa: E402
import studio_fixtur  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MALLSAJT = ROOT / 'kunder' / 'rokprov-mall' / 'sajt'
SLUG = 'testdata-studio'
H1, BILD, TJANSTER = '334f7e16fd58', '045c00fea0a1', '66ac994e2d9b'  # provkandidatens id (karta.mjs: väg i trädet)


def id_ur(html, monster):
    m = re.search(monster, html)
    return m.group(1) if m else None


class Studio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (MALLSAJT / 'node_modules').is_dir():
            raise unittest.SkipTest('mallsajten saknar node_modules (rokprov.sh bygger den tidigare)')
        cls.stack = contextlib.ExitStack()
        try:
            cls.root = Path(cls.stack.enter_context(korregister.egen_tmp_med('nwp-studio-', 'designstudions prov'))).resolve()
            for m in (dash, atelje):
                cls.stack.enter_context(patch.multiple(m, ROOT=cls.root, UNDERLAG=cls.root / 'underlag', KUNDER=cls.root / 'kunder'))
            cls.stack.enter_context(patch.multiple(observation, ROOT=cls.root, UNDERLAG=cls.root / 'underlag'))
            cls.stack.enter_context(patch.object(meddelanden, 'UNDERLAG', cls.root / 'underlag'))
            cls.stack.enter_context(patch.object(atelje, 'claude', return_value=str(cls.root / 'saknas' / 'claude')))
            studio_fixtur.bygg(cls.root, SLUG, MALLSAJT)
            st = kandidater.fotografera(SLUG, 'k01')
            assert st.get('status') == 'klar', st.get('skal')
            cls.sajt = kandidater.ksajt(SLUG, 'k01')
            html = (cls.sajt / 'dist' / 'index.html').read_text(encoding='utf-8')
            cls.h2 = id_ur(html, r'<h2 data-nwp-k="([0-9a-f]{12})" id="kontakt-rubrik"')
            cls.h3 = id_ur(html, r'<h3 data-nwp-k="([0-9a-f]{12})" class="tjanst__namn"')
            cls.knapp = id_ur(html, r'<a data-nwp-k="([0-9a-f]{12})" class="knapp knapp--primar"')
            cls.om = id_ur(html, r'<section data-nwp-k="([0-9a-f]{12})" class="om"')
        except BaseException:
            cls.stack.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()

    def setUp(self):
        self.startade = []
        p = patch.object(flodesstart, 'starta', side_effect=lambda slug, h, rid: self.startade.append((h, rid)) or 5)
        p.start()
        self.addCleanup(p.stop)
        d = patch.object(studio, '_dold', return_value=(False, False))
        d.start()
        self.addCleanup(d.stop)

    # --- hjälpare ---

    def karta(self, k, bredd=1280, **extra):
        return studio.karta(dash, SLUG, 'k01', dict({'sida': '/', 'bredd': str(bredd), 'k': k}, **extra))

    def kontroll(self, karta, kid):
        return next((c for lista in karta['omraden'].values() for c in lista if c['id'] == kid), None)

    def begar(self, k, andringar, bredd=1280, rid=None, **extra):
        st = kandidater.las_status(SLUG, 'k01')
        korning = (atelje.las_json(self.root / 'underlag' / SLUG / 'atelje' / 'STATUS.json') or {})['startad']
        rid = rid or 'prov-%s' % abs(hash((k, json.dumps(andringar), st['version'])))
        return studio.begar(dash, SLUG, dict({'andring_id': rid, 'kandidat': 'k01', 'version': st['version'], 'korning': korning,
                                              'sida': '/', 'bredd': bredd, 'k': k, 'andringar': andringar}, **extra))

    def spara(self, k, andringar, bredd=1280, **extra):
        """Begäran och arbetaren i processen (flodesstart startar den annars under kundens startlås): posten efteråt."""
        r = self.begar(k, andringar, bredd, **extra)
        self.assertEqual(r['status'], 'koad', r)
        rc = studio.kor(SLUG, r['id'])
        post = atelje.las_json(studio.katalog(SLUG) / ('%s.json' % r['id']))
        return post, rc

    def kalla(self, rel):
        return (self.sajt / rel).read_text(encoding='utf-8')

    # --- fallen ---

    def test_01_kallkartan_i_forhandsbygget_och_inte_i_produktionen(self):
        """DS-U16, DS-U33: förhandsbygget bär id för element och regler, motorns läsning ger samma id ur källan, och samma
        källa byggd som i helbygget (npm run build, utan studions bygge) bär varken id, regel-id eller bryggan."""
        html = (self.sajt / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('data-nwp-k="%s"' % H1, html)
        t = studio.tolka(SLUG, 'k01')
        ix = studio.index(t)
        self.assertEqual(ix['element'][H1][0], 'src/components/Hero.astro')
        css = ''.join(p.read_text(encoding='utf-8') for p in (self.sajt / 'dist' / '_astro').glob('*.css')) + html
        rid = set(re.findall(r'--nwp-r:"([0-9a-f]{12})"', css))
        self.assertTrue(rid and rid <= set(ix['regler']), 'regel-id i bygget som motorns läsning inte känner')
        with korregister.egen_tmp_med('nwp-studio-', 'produktionsbygge av provkandidaten') as tmp:
            kopia = Path(tmp) / 'sajt'
            shutil.copytree(self.sajt, kopia, symlinks=True, ignore=shutil.ignore_patterns('dist', '.astro'))
            r = subprocess.run(['npm', 'run', 'build', '--prefix', str(kopia)], capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])
            ut = ''.join(p.read_text(encoding='utf-8', errors='replace') for p in (kopia / 'dist').rglob('*') if p.suffix in ('.html', '.css', '.js'))
            for spar in ('data-nwp-k', '--nwp-r', '__nortropic', 'forhandsbrygga'):
                self.assertNotIn(spar, ut, 'produktionsbygget bär %s' % spar)

    def test_02_agarskap_och_tvetydighet(self):
        """DS-U16: samma text i två komponenter ändras bara där den markerades (direktredigeringens textsökning nekar den);
        en text ur en lista nekas med skälet; ett känt prop-värde är rubrikens källa; en delad token visar sin räckvidd."""
        with self.assertRaises(direktredigering.EjMappbar):
            direktredigering.kartlagg(SLUG, 'k01', 'Begär offert')
        k = self.karta(self.h2)
        self.assertTrue(k['ok'], k)
        text = self.kontroll(k, 'text/text')
        self.assertTrue(text['stod'] and text['kalla']['fil'] == 'src/components/Kontakt.astro', text)
        h3 = self.karta(self.h3, bredd=390, instans='1')
        t3 = self.kontroll(h3, 'text/text')
        self.assertFalse(t3['stod'])
        self.assertIn('lista', t3['skal'])
        self.assertIn('3 förekomster', self.kontroll(h3, 'typografi/font-size')['rackvidd']['text'])
        h1 = self.karta(H1)
        t1 = self.kontroll(h1, 'text/text')
        self.assertTrue(t1['stod'] and t1['kalla']['fil'] == 'src/pages/index.astro' and t1['kalla']['slag'] == 'prop', t1)
        tok = self.kontroll(h1, 'typografi/font-family/token')
        self.assertEqual(tok['rackvidd']['slag'], 'designgrund')
        self.assertIn('5 regler', tok['rackvidd']['text'])
        # ett ärvt värde är aldrig "detta objekt": färgen från body visar att allt som ärver ändras
        arvd = self.kontroll(h1, 'farg/color/arvd')
        self.assertEqual(arvd['rackvidd']['slag'], 'arvd')
        self.assertEqual(self.kontroll(h1, 'farg/color')['kalla']['slag'], 'ny_deklaration')

    def test_03_typografi_och_text_i_ratt_kalla(self):
        """DS-U18: storlek och radavstånd i rubrikens egen regel och texten i kontaktrubriken: rätt filer och lägen, det
        väntade beräknade värdet i 390, 900 och 1280 efter bygget, en ny version och samma värden i produktionsbygget."""
        fore = self.kalla('src/components/Hero.astro')
        post, rc = self.spara(H1, [{'kontroll': 'typografi/font-size', 'varde': '3rem'}, {'kontroll': 'typografi/line-height', 'varde': '1.2'}])
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        efter = self.kalla('src/components/Hero.astro')
        self.assertIn('font-size: 3rem; line-height: 1.2;', efter)
        self.assertEqual(efter.replace('font-size: 3rem; line-height: 1.2;', 'font-size: var(--typ-rubrik-storlek); line-height: var(--typ-rubrik-radavstand);'), fore,
                         'bara värdena ändras; resten av filen står kvar byte för byte')
        self.assertEqual(post['forvantat']['900']['efter']['font-size'], '48px')
        self.assertEqual(kandidater.las_status(SLUG, 'k01')['version'], post['till_version'])
        post2, rc2 = self.spara(self.h2, [{'kontroll': 'text/text', 'varde': 'Be om en offert'}])
        self.assertEqual((rc2, post2['status']), (0, 'klar'), post2.get('skal'))
        self.assertIn('>Be om en offert</h2>', self.kalla('src/components/Kontakt.astro'))
        self.assertIn('>Begär offert</Knapp>', self.kalla('src/components/Hero.astro'), 'knappens text med samma lydelse står kvar')

    def test_04_bildregi_mobil_och_dator_var_for_sig(self):
        """DS-U19: fokuspunkt och förhållande i mobilens regel ändrar inte datorns mediaregel; ett bildval byter importen
        till en annan av kundens bilder utan att röra originalen; ett namn som inte är kundens bild nekas."""
        post, rc = self.spara(BILD, [{'kontroll': 'bildregi/object-position', 'varde': '30% 70%'},
                                     {'kontroll': 'bildregi/aspect-ratio', 'varde': '3 / 2'}], bredd=390, barn='img:0')
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        hero = self.kalla('src/components/Hero.astro')
        self.assertIn('aspect-ratio: 3 / 2; object-fit: cover; object-position: 30% 70%;', hero)
        self.assertIn('aspect-ratio: 4 / 5; object-position: 60% 40%;', hero, 'datorns regel står kvar')
        dator = self.karta(BILD, bredd=1280, barn='img:0')
        self.assertEqual(self.kontroll(dator, 'bildregi/object-position')['varde'], '60% 40%')
        om_bild = id_ur((self.sajt / 'dist' / 'index.html').read_text(encoding='utf-8'), r'<section data-nwp-k="([0-9a-f]{12})" class="om"')
        k = self.karta(om_bild, barn='img:0')
        bv = self.kontroll(k, 'bildregi/bild')
        self.assertTrue(bv and bv['stod'] and bv['varde'] == 'detalj.jpg' and 'verkstad.jpg' in bv['val'], bv)
        with self.assertRaises(ValueError):
            self.begar(om_bild, [{'kontroll': 'bildregi/bild', 'varde': '../../../../hemlig.jpg'}], barn='img:0')
        original = (self.sajt / 'src' / 'assets' / 'atelje' / 'detalj.jpg').read_bytes()
        post, rc = self.spara(om_bild, [{'kontroll': 'bildregi/bild', 'varde': 'verkstad.jpg'}], barn='img:0')
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        self.assertIn("import detalj from '../assets/atelje/verkstad.jpg';", self.kalla('src/components/OmOss.astro'))
        self.assertEqual((self.sajt / 'src' / 'assets' / 'atelje' / 'detalj.jpg').read_bytes(), original, 'originalet rörs aldrig')

    def test_05_mellanrum_i_kortformens_del(self):
        """DS-U20: sidornas mellanrum i kortformen padding: A B ändrar bara B, prövat i 390, 900 och 1280 utan sidled-spill
        och utan att andra element ändras."""
        k = self.karta(TJANSTER)
        sidor = self.kontroll(k, 'mellanrum/padding:1')
        self.assertTrue(sidor['stod'] and sidor['tacker'] == ['padding-left', 'padding-right'], sidor)
        post, rc = self.spara(TJANSTER, [{'kontroll': 'mellanrum/padding:1', 'varde': '2.5rem'}])
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        self.assertIn('padding: var(--avstand-xl) 2.5rem;', self.kalla('src/components/Tjanster.astro'))
        self.assertEqual(sorted(post['forvantat']), ['1280', '390', '900'])

    def test_06_komposition_variant_och_ordning(self):
        """DS-U21: varianten ur Props sätts där komponenten används och prövas mot komponentens markup; sektionerna byter
        plats med sitt innehåll orört; en sektion i en lista eller ett uttryck erbjuds ingen ordning."""
        k = self.karta(H1)
        v = self.kontroll(k, 'komposition/prop:variant')
        self.assertEqual((v['stod'], v['val'], v['varde']), (True, ['delad', 'helbild'], 'delad'))
        post, rc = self.spara(H1, [{'kontroll': 'komposition/prop:variant', 'varde': 'helbild'}])
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        self.assertIn('<Hero variant="helbild" rubrik=', self.kalla('src/pages/index.astro'))
        fore = self.kalla('src/pages/index.astro')
        post, rc = self.spara(TJANSTER, [{'kontroll': 'komposition/ordning', 'varde': [0, 2, 1, 3]}])
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        efter = self.kalla('src/pages/index.astro')
        self.assertLess(efter.index('<OmOss />'), efter.index('<Tjanster tjanster={tjanster} />'))
        self.assertEqual(sorted(fore), sorted(efter), 'samma tecken, bara flyttade')
        h3 = self.karta(self.h3, bredd=390, instans='1')
        self.assertIsNone(self.kontroll(h3, 'komposition/ordning'), 'en lista får ingen ordning')

    def test_07_farg_lokal_och_designgrund(self):
        """DS-U22: en lokal färg är en ny deklaration i elementets egen regel; accentens token visar sin räckvidd och ändrar
        alla som använder den; kontrasten mot ytan redovisas."""
        k = self.karta(self.knapp)
        bg = self.kontroll(k, 'farg/background-color/token')
        self.assertTrue(bg and bg['rackvidd']['slag'] == 'designgrund', bg)
        self.assertIsNotNone(k['element']['kontrast']['kvot'])
        post, rc = self.spara(self.knapp, [{'kontroll': 'farg/background-color/token', 'varde': '#5a3418'}])
        self.assertEqual((rc, post['status']), (0, 'klar'), post.get('skal'))
        self.assertIn('--farg-accent: #5a3418;', self.kalla('src/styles/design.css'))

    def test_08_stale_kalla_ger_konflikt(self):
        """DS-U23: en källa som ändrats efter begäran ger konflikt; den senare ändringen står kvar och versionen är orörd."""
        v0 = kandidater.las_status(SLUG, 'k01')['version']
        r = self.begar(H1, [{'kontroll': 'typografi/max-width', 'varde': '20ch'}])
        p = self.sajt / 'src' / 'components' / 'Hero.astro'
        extern = p.read_text(encoding='utf-8') + '\n<!-- en annan skrivare -->\n'
        p.write_text(extern, encoding='utf-8')
        try:
            rc = studio.kor(SLUG, r['id'])
            post = atelje.las_json(studio.katalog(SLUG) / ('%s.json' % r['id']))
            self.assertEqual((rc, post['status']), (3, 'konflikt'), post)
            self.assertEqual(p.read_text(encoding='utf-8'), extern, 'den senare ändringen skrivs aldrig över')
            self.assertEqual(kandidater.las_status(SLUG, 'k01')['version'], v0)
        finally:
            p.write_text(extern[:-len('\n<!-- en annan skrivare -->\n')], encoding='utf-8')

    def test_09_fallerat_bygge_lagger_tillbaka_originalet(self):
        """DS-U24: ett bygge som faller efter skrivningen lägger tillbaka originalet (filen var fortfarande den som
        skrevs), fotograferar om och anger aldrig ändringen som klar."""
        fore = self.kalla('src/components/Hero.astro')
        r = self.begar(H1, [{'kontroll': 'typografi/max-width', 'varde': '22ch'}])
        orig = prova.bygg_inom_grans
        anrop = []

        def faller_forst(sajt, timeout=600):
            anrop.append(sajt)
            return (1, 'provets injicerade fel') if len(anrop) == 1 else orig(sajt, timeout)
        with patch.object(prova, 'bygg_inom_grans', side_effect=faller_forst):
            rc = studio.kor(SLUG, r['id'])
        post = atelje.las_json(studio.katalog(SLUG) / ('%s.json' % r['id']))
        self.assertEqual((rc, post['status']), (3, 'aterstalld'), post)
        self.assertEqual(self.kalla('src/components/Hero.astro'), fore)
        self.assertEqual(kandidater.las_status(SLUG, 'k01')['version'], kandidater.projektets_version(SLUG, 'k01'))

    def test_10_samma_id_och_ogiltiga_varden(self):
        """DS-U14, DS-U32: samma ändrings-id ger samma begäran och ingen andra start; ett värde som försöker bli mer än ett
        värde, en url eller en okänd kontroll nekas före något sparas; ett påhittat id ger ingen karta."""
        r1 = self.begar(H1, [{'kontroll': 'typografi/letter-spacing', 'varde': '0.01em'}], rid='prov-samma-id-0001')
        r2 = self.begar(H1, [{'kontroll': 'typografi/letter-spacing', 'varde': '0.01em'}], rid='prov-samma-id-0001')
        self.assertTrue(r2.get('upprepat'))
        self.assertEqual(len(self.startade), 1)
        self.assertEqual(r1['id'], r2['id'])
        for v in ('2rem; } body { display: none', 'url(https://exempel.se/x.png)', '1rem /* x */', 'red !important'):
            with self.assertRaises(ValueError, msg=v):
                self.begar(H1, [{'kontroll': 'typografi/font-size', 'varde': v}], rid='prov-ogiltigt-%d' % abs(hash(v)))
        with self.assertRaises(studio.EjMappbar):
            self.begar(H1, [{'kontroll': 'typografi/skuggfalt', 'varde': '1px'}], rid='prov-okand-kontroll-1')
        self.assertFalse(self.karta('0123456789ab')['ok'])
        with self.assertRaises(ValueError):
            self.karta(H1, sida='/../../etc/')

    def test_11_blind_ger_inga_kontroller(self):
        """Före ägarens första val i en blind körning ger studion inga kontroller och tar inga ändringar."""
        with patch.object(studio, '_dold', return_value=(True, False)):
            self.assertFalse(self.karta(H1)['ok'])
            with self.assertRaises(ValueError):
                self.begar(H1, [{'kontroll': 'typografi/font-size', 'varde': '2rem'}], rid='prov-blind-00001')

    # --- DS2: tidigt bedömbara förslag; DS4: en skrivare per kandidat och gränsen medan andra arbetar ---

    def test_12_bedombar_ar_inte_bara_laddad(self):
        """DS-U06: en sida som svarar 200 men är tom, visar ett fel, saknar h1 eller en bild i första vyn är inte bedömbar;
        mobil och dator prövas båda. Typsnitt som inte laddades och en tom main med text runt om är markeringar."""
        import forhandsvisa
        hel = {'bedombarhet': {'main': True, 'main_text_langd': 600, 'text_langd': 900, 'bilder_forsta_vyn': 1, 'brutna_bilder_forsta_vyn': [],
                               'typsnitt_fel': [], 'felsida': False}, 'h1': 1}
        def ins(**andrat):
            vy = json.loads(json.dumps(hel))
            for k, v in andrat.items():
                (vy if k == 'h1' else vy['bedombarhet'])[k] = v
            return {'vyer': {'390': json.loads(json.dumps(hel)), '1440': vy}}
        self.assertEqual(forhandsvisa.ej_bedombar(ins()), [])
        self.assertIn('felmeddelande', ' '.join(forhandsvisa.ej_bedombar(ins(felsida=True))))
        self.assertIn('1440 px: sidan är tom', ' '.join(forhandsvisa.ej_bedombar(ins(text_langd=12, main_text_langd=12))))
        self.assertIn('h1', ' '.join(forhandsvisa.ej_bedombar(ins(h1=0))))
        self.assertIn('hero.jpg', ' '.join(forhandsvisa.ej_bedombar(ins(brutna_bilder_forsta_vyn=['/_astro/hero.jpg']))))
        self.assertEqual(forhandsvisa.ej_bedombar({'vyer': {'390': {'h1': 1}}}), [], 'en äldre inspektion utan fältet prövas inte')
        mark = forhandsvisa.bedombarhetens_markeringar(ins(typsnitt_fel=['Fraunces'], main_text_langd=3))
        self.assertTrue(any('Fraunces' in x for x in mark) and any('main är tom' in x for x in mark), mark)
        # den riktiga inspektionen bär fälten: kandidatens senaste fotografering
        insp = atelje.las_json(kandidater.kdir(SLUG, 'k01') / 'bilder' / 'start' / 'INSPEKTION.json')
        b = insp['vyer']['1440']['bedombarhet']
        self.assertTrue(b['main'] and b['text_langd'] > 40 and b['bilder_forsta_vyn'] >= 1 and b['brutna_bilder_forsta_vyn'] == [], b)

    def test_13_tidig_publicering_och_avbrott(self):
        """DS-U07 och DS-U27: skaparens version blir bedömbar direkt med sina bilder bevarade (vyn visar dem medan svaret
        pågår); ett stopp lämnar den bedömbar, och återupptagningen lägger tillbaka den versionen över ett halvt svar."""
        fore = kandidater.las_status(SLUG, 'k01')
        st = kandidater.fotografera(SLUG, 'k01', skiss=True, tidig={'forsok': 1})
        try:
            self.assertEqual(st['status'], 'bedombar', st.get('skal'))
            v = st['version']
            self.assertEqual((st['bedombar'] or {}).get('version'), v)
            self.assertTrue((kandidater.kdir(SLUG, 'k01') / 'versioner' / v[:12] / 'bilder' / 'start' / 'vy-1440-forsta.png').is_file(), 'bilderna bevarade i versionen')
            k = next(x for x in kandidater.sammanstall(SLUG) if x['id'] == 'k01')
            self.assertIn('/versioner/%s/bilder/' % v[:12], k['bilder']['1440-forsta'], 'vyn visar den bevarade versionens bilder')
            self.assertIn('pågår', k['statustext'])
            # ett halvt svar i projektet, och ett stopp
            fil = self.sajt / 'src' / 'components' / 'Hero.astro'
            orig = fil.read_text(encoding='utf-8')
            fil.write_text(orig.replace('</section>', '<!-- halvt svar --></section>', 1), encoding='utf-8')
            try:
                kandidater.markera_avbrutna(SLUG, 'stopp', '2026-10-11T11:00:00Z')
            finally:
                atelje.SLUTFORD.clear()
            st2 = kandidater.las_status(SLUG, 'k01')
            self.assertEqual(st2['status'], 'bedombar', 'skaparens version står bedömbar efter stoppet')
            self.assertEqual(st2['bedombar_avbruten']['orsak'], 'stoppet')
            self.assertIn('avbröts vid stoppet', kandidater.statustext(st2))
            st3 = kandidater.ta_upp_bedombar(SLUG, 'k01', st2)
            self.assertEqual((st3['status'], st3['version']), ('klar', v), st3.get('skal'))
            self.assertEqual(fil.read_text(encoding='utf-8'), orig, 'det halva svaret är ersatt av den bedömbara versionen')
            self.assertEqual(kandidater.projektets_version(SLUG, 'k01'), v)
        finally:
            kandidater.satt_status(SLUG, 'k01', fore.get('status') or 'klar', 'provet: tillbaka')

    def test_14_en_skrivare_per_kandidat(self):
        """DS-U26: kandidatens skrivlås: en andra skrivare (en annan process, en annan tråd, körningens kedja) får det
        upptaget med vem som håller det; det släpps när skrivaren är klar, och en väntande tar det då."""
        import threading
        import time as time_
        with kandidater.skrivlas(SLUG, 'k01', vem='provets första skrivare'):
            with self.assertRaises(kandidater.Upptagen) as e:
                with kandidater.skrivlas(SLUG, 'k01', vem='andra'):
                    pass
            self.assertIn('provets första skrivare', str(e.exception))
            kod = ('import sys; sys.path.insert(0, %r); import atelje, kandidater; from pathlib import Path; r = Path(%r); '
                   'atelje.UNDERLAG = r / "underlag"\ntry:\n    kandidater.skrivlas(%r, "k01").__enter__(); print("tog")\n'
                   'except kandidater.Upptagen as e: print("upptaget:", e)') % (str(ROOT / 'kontroller'), str(self.root), SLUG)
            ut = subprocess.run([sys.executable, '-B', '-c', kod], capture_output=True, text=True, timeout=60)
            self.assertIn('upptaget', ut.stdout, ut.stdout + ut.stderr)
        with kandidater.skrivlas(SLUG, 'k01'):
            pass  # släppt
        las = kandidater.skrivlas(SLUG, 'k01', vem='hålls en sekund')
        las.__enter__()
        threading.Timer(1.0, lambda: las.__exit__(None, None, None)).start()
        t0 = time_.monotonic()
        with kandidater.skrivlas(SLUG, 'k01', vanta=10):
            self.assertGreater(time_.monotonic() - t0, 0.5, 'den väntande tog låset först när det släpptes')
        # körningens kedja håller kandidatens lås medan den arbetar
        sett = []
        def arbete(kid):
            try:
                with kandidater.skrivlas(SLUG, kid):
                    sett.append('ledigt')
            except kandidater.Upptagen:
                sett.append('upptaget')
        kandidater.kor_pool(SLUG, ['k01'], arbete, {}, lambda: None, parallellt=1)
        self.assertEqual(sett, ['upptaget'], 'kedjans arbete sker under kandidatens lås')

    def test_15_andring_vid_gransen_medan_andra_arbetar(self):
        """DS-U26: körningens arbetare lever och en annan kandidat arbetar; den här kandidaten står vid sin gräns och kan
        ändras. Kandidaten själv utan gräns nekas, och en ändring som finner kandidatens lås upptaget blir en konflikt utan
        att något skrivs."""
        stfil = self.root / 'underlag' / SLUG / 'atelje' / 'STATUS.json'
        fore_st = atelje.las_json(stfil)
        sov = subprocess.Popen(['sleep', '60'], stdin=subprocess.DEVNULL)
        self.addCleanup(sov.kill)
        atelje.skriv_json_atomiskt(stfil, dict(fore_st, pid=sov.pid, steg='kandidater'))
        k02 = kandidater.las_status(SLUG, 'k02').get('status')
        kandidater.satt_status(SLUG, 'k02', 'under_arbete', 'provet: en annan kandidat arbetar')
        try:
            v = kandidater.las_status(SLUG, 'k01')['version']
            studio._villkor(SLUG, 'k01', v, fore_st['startad'])  # inget undantag: k01 är vid sin gräns
            flodesstart.krav(SLUG, 'studio')
            with self.assertRaises(ValueError):
                flodesstart.krav(SLUG, 'exportera')  # andra flödeshandlingar väntar på ateljén som förut
            r = self.begar(H1, [{'kontroll': 'typografi/font-size', 'varde': '3.1rem'}], rid='prov-grans-00001')
            self.assertEqual(r['status'], 'koad', r)
            fore_kalla = self.kalla('src/components/Hero.astro')
            with kandidater.skrivlas(SLUG, 'k01', vem='provets andra skrivare'):
                self.assertEqual(studio.kor(SLUG, r['id']), 3)
            post = atelje.las_json(studio.katalog(SLUG) / ('%s.json' % r['id']))
            self.assertEqual(post['status'], 'konflikt', post)
            self.assertIn('provets andra skrivare', post['skal'])
            self.assertEqual(self.kalla('src/components/Hero.astro'), fore_kalla, 'inget skrevs')
            kandidater.satt_status(SLUG, 'k01', 'under_arbete', 'provet: kedjan arbetar')
            try:
                with self.assertRaises(studio.Inaktuell) as e:
                    studio._villkor(SLUG, 'k01', v, fore_st['startad'])
                self.assertIn('säker gräns', str(e.exception))
            finally:
                kandidater.satt_status(SLUG, 'k01', 'klar', 'provet: kedjan är klar')
        finally:
            kandidater.satt_status(SLUG, 'k02', k02 or 'klar', 'provet: tillbaka')
            atelje.skriv_json_atomiskt(stfil, fore_st)


if __name__ == '__main__':
    unittest.main(verbosity=2)
