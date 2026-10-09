#!/usr/bin/env python3
"""Tio förslag och den rena designstarten (ägarens uppdrag 2026-10-09 ~17:53Z, punkt 12). Varje fall går genom den
verkliga koden med attrapper bara vid modellsessionerna, fotograferingen och återställningen:

- Den rena designstarten: klassningen post för post (kundens fakta, material, lås och kundrepo bevaras; ateljén,
  domloggen, referenserna, sajten och kandidaterna arkiveras), flytten med sha256 före och efter, registret, vakten (ett
  återställt gammalt material, en länk in i arkivet och en gammal spårad fil fälls; en ny sajt ur mallen gör det inte),
  återställningen och ett arkiv inne i repot som vägras.
- Gamla artefakter och instruktioner når inte nya sessioner: läsförbuden för arkivet, rapporterna och granskningarna,
  nivåfilen borta ur måttstockarna och metoden, granskarens sanningsenliga kalibreringsstatus, en gammal session som
  inte förgrenas, och vakten mot gammal styrning utan fynd i repot.
- Uppdragen: typ, resultat, omfattning och bevara krävs; kundens beslut kräver belägg och kan aldrig godkänna; ett val
  startar inget.
- En rättelse utlöser ingen utbyggnad: en ny sida i en rättelse återställs till versionen den gällde; inga specialistpass.
- Ett designomtag kan ändra en svag grundkomposition: prompten ger friheten, hela startsidan får skrivas om, och före och
  efter styr (bättre förs vidare, sämre återställs och står bevarad och valbar, oklart står som oklart).
- Referensbilder och kodunderlag når rätt roll: uppdraget bär utgångspunkten och implementationsgrunden; en skärmbild
  som kodmall och ett förslag som bara skiljer sig i färg avvisas; före/efter-granskaren är blind för skaparens kod och
  text och har inga skrivande verktyg.
- Tidigare versioner kan jämföras och väljas, och slutbedömningen gäller samma version som visas.
"""
import contextlib
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import bildkedja  # noqa: E402
import granska  # noqa: E402
import kandidater as kd  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402
import prototyp  # noqa: E402
import ren_designstart as rd  # noqa: E402
import sandlada  # noqa: E402
import skapande  # noqa: E402
import styrning  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def png(tagg):
    """En giltig PNG (signatur och IHDR med mått) med taggen som eget innehåll, så att två versioner skiljer sig."""
    import struct
    import zlib
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 0, 0, 0, 0)) + chunk(b'tEXt', b'tagg\0' + tagg.encode())
            + chunk(b'IDAT', zlib.compress(b'\0\0')) + chunk(b'IEND', b''))


def skriv(p, text='x'):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(text, bytes) else p.write_text)(text)
    return p


UPPDRAG = {'ratta': {'typ': 'ratta', 'resultat': 'rubriken läsbar i 390', 'omfattning': ['första vyns rubrik bryts fel i 390'],
                     'bevara': ['kompositionen']},
           'omarbeta': {'typ': 'omarbeta', 'resultat': 'en komposition som bär verkstadens bilder', 'omfattning': ['startsidans första vy och rytm'],
                        'bevara': ['texterna och sidorna']},
           'bygg_ut': {'typ': 'bygg_ut', 'resultat': 'hela startsidan och tjänstesidan', 'omfattning': ['/tjanster/'], 'bevara': ['första vyn']}}


class RenDesignstart(unittest.TestCase):
    """Punkt 3: manifest, verifierat arkiv utanför repot, borttaget ur den aktiva miljön, och vakten."""

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'den rena designstarten'))).resolve()
        self.rot, self.arkiv = self.tmp / 'repo', self.tmp / 'Arkiv' / 'ren'
        u, k = self.rot / 'underlag' / 'kund-a', self.rot / 'kunder' / 'kund-a'
        skriv(u / 'VERKSAMHET.json', '{"namn": "Kund A", "fiktiv": true}')
        skriv(u / 'BRIEF.md', '# Brief\n')
        skriv(u / 'bilder' / 'BILDER.md', '# Bilder\n')
        skriv(u / 'bilder' / 'verkstad.jpg', b'JPEG-kundens-egen')
        skriv(u / '.atelje-start.las', '')
        skriv(u / 'DESIGNDOMAR.jsonl', '{"beslut": "putsa"}\n')
        skriv(u / 'RIKTNINGSHISTORIK.json', '[]')
        skriv(u / 'atelje' / 'kandidater' / 'k01' / 'bilder' / 'start' / 'vy-390-forsta.png', b'PNG-gammal-kandidat')
        skriv(u / 'referenser' / 'paket-v01' / 'PAKET.md', '# gammalt referenspaket\n')
        skriv(u / 'okand-fil.txt', 'okänt ursprung')
        skriv(k / 'kundrepo' / 'CLAUDE.md', '# kundrepo\n')
        skriv(k / 'KUNDREPO.json', '{}')
        skriv(k / 'sajt' / 'src' / 'pages' / 'index.astro', '<h1>gammal genererad sida</h1>')
        skriv(k / 'sajt' / 'src' / 'styles' / 'mall.css', 'body{}')
        skriv(k / 'kandidater' / 'k01' / 'sajt' / 'src' / 'pages' / 'index.astro', '<h1>gammal kandidat</h1>')
        skriv(self.rot / 'underlag' / 'kalibrering' / 'ANKARE.txt', 'K01 · ankare\n')
        skriv(self.rot / 'underlag' / 'LARDOMAR-original.md', '# domar\n')
        skriv(self.rot / 'underlag' / 'rapporter' / 'R.md', '# rapport\n')
        skriv(self.rot / 'underlag' / 'rokprov-mall' / 'BESTALLNING.md', '# fixtur\n')
        skriv(self.rot / 'kunder' / 'figma-prov' / 'sajt' / 'index.html', 'figma')
        skriv(self.rot / 'mall' / 'astro' / 'src' / 'styles' / 'mall.css', 'body{}')
        skriv(self.rot / 'kunskap' / 'visuell-niva.md', '# gammal nivåfil\n')
        skriv(self.rot / 'LARDOMAR.md', '# Lärdomar\n\n## L1 · 2026-10-02 · kund-a\nGammal dom.\n')

    def test_klassningen_bevarar_fakta_och_arkiverar_designarbetet(self):
        poster, bevaras, oklassat = rd.klassa(self.rot)
        arkiv = {p['sokvag'] for p in poster}
        for x in ('underlag/kund-a/atelje', 'underlag/kund-a/DESIGNDOMAR.jsonl', 'underlag/kund-a/RIKTNINGSHISTORIK.json', 'underlag/kund-a/referenser',
                  'kunder/kund-a/sajt', 'kunder/kund-a/kandidater', 'underlag/kalibrering', 'underlag/LARDOMAR-original.md', 'kunder/figma-prov',
                  'underlag/kund-a/okand-fil.txt'):
            self.assertIn(x, arkiv)
        kvar = {b['sokvag'] for b in bevaras}
        for x in ('underlag/kund-a/VERKSAMHET.json', 'underlag/kund-a/BRIEF.md', 'underlag/kund-a/bilder', 'underlag/kund-a/.atelje-start.las',
                  'kunder/kund-a/kundrepo', 'kunder/kund-a/KUNDREPO.json', 'underlag/rapporter', 'underlag/rokprov-mall'):
            self.assertIn(x, kvar)
        self.assertEqual(next(p for p in poster if p['sokvag'] == 'underlag/kund-a/okand-fil.txt')['kategori'], 'okänt ursprung')
        self.assertTrue(all(p['skal'] for p in poster) and all(b['skal'] for b in bevaras), 'en post saknar skäl')
        self.assertEqual(oklassat, [])

    def test_arkivet_verifieras_och_det_gamla_lamnar_den_aktiva_miljon(self):
        fore = hashlib.sha256((self.rot / 'underlag/kund-a/atelje/kandidater/k01/bilder/start/vy-390-forsta.png').read_bytes()).hexdigest()
        man = rd.arkivera(self.rot, self.arkiv, brytpunkt='2026-10-09T18:40:00Z', commit='abc')
        self.assertFalse([p for p in man['poster'] if p.get('fel')], man['poster'])
        self.assertFalse((self.rot / 'underlag/kund-a/atelje').exists(), 'den gamla ateljén står kvar i den aktiva miljön')
        self.assertFalse((self.rot / 'kunder/kund-a/sajt').exists())
        self.assertFalse((self.rot / 'underlag/kalibrering').exists())
        for x in ('underlag/kund-a/VERKSAMHET.json', 'underlag/kund-a/bilder/verkstad.jpg', 'underlag/kund-a/.atelje-start.las', 'kunder/kund-a/kundrepo/CLAUDE.md',
                  'underlag/rapporter/R.md', 'underlag/rokprov-mall/BESTALLNING.md'):
            self.assertTrue((self.rot / x).exists(), 'aktuell kundinformation eller ett skydd försvann: %s' % x)
        summor = (self.arkiv / 'SHA256SUMS').read_text()
        self.assertIn('%s  underlag/kund-a/atelje/kandidater/k01/bilder/start/vy-390-forsta.png' % fore, summor)
        self.assertEqual(oct((self.arkiv).stat().st_mode & 0o777), '0o700')
        self.assertTrue((self.arkiv / 'git/kunskap/visuell-niva.md').is_file() and (self.arkiv / 'git/LARDOMAR.md').is_file())
        reg = json.loads((self.rot / rd.REGISTER).read_text())
        self.assertEqual((reg['brytpunkt'], reg['commit']), ('2026-10-09T18:40:00Z', 'abc'))
        self.assertTrue(all(p['verifierad'] for p in reg['poster']))
        self.assertNotIn('Gammal dom', (self.rot / rd.REGISTER).read_text(), 'registret bär innehåll, inte bara vägar')
        man2 = json.loads((self.arkiv / 'MANIFEST.json').read_text())
        self.assertTrue(man2['poster'] and all({'sokvag', 'kategori', 'skal', 'bytes'} <= set(p) for p in man2['poster']))

    def test_vakten(self):
        rd.arkivera(self.rot, self.arkiv)  # brytpunkten är arkiveringens tid; det som skapas efter den är nytt
        (self.rot / 'kunskap/visuell-niva.md').unlink()
        skriv(self.rot / 'LARDOMAR.md', '# Lärdomar\n\nSenaste dom före brytpunkten: L6.\n')
        self.assertEqual(rd.prova(self.rot), [], 'vakten fällde en ren miljö')
        skriv(self.rot / 'kunder/kund-a/sajt/src/styles/mall.css', 'body{}')  # en ny sajt ur mallen är nytt material
        self.assertEqual(rd.prova(self.rot), [])
        gammal = self.arkiv / 'underlag/kund-a/atelje/kandidater/k01/bilder/start/vy-390-forsta.png'
        skriv(self.rot / 'kunder/kund-a/sajt/public/bild.png', gammal.read_bytes())
        self.assertIn('arkiverat material har kommit tillbaka', [f['vad'] for f in rd.prova(self.rot)])
        (self.rot / 'kunder/kund-a/sajt/public/bild.png').unlink()
        os.symlink(self.arkiv / 'underlag/kund-a/referenser', self.rot / 'underlag/kund-a/genvag')
        self.assertIn('länk in i arkivet', [f['vad'] for f in rd.prova(self.rot)])
        (self.rot / 'underlag/kund-a/genvag').unlink()
        skriv(self.rot / 'kunskap/visuell-niva.md', (self.arkiv / 'git/kunskap/visuell-niva.md').read_text())
        self.assertIn('en gammal version är tillbaka i arbetsträdet', [f['vad'] for f in rd.prova(self.rot)])
        (self.rot / 'kunskap/visuell-niva.md').unlink()
        skriv(self.rot / 'LARDOMAR.md', '# Lärdomar\n\n## L1 · 2026-10-02 · kund-a\n')
        self.assertIn('domar från före brytpunkten i LARDOMAR.md', [f['vad'] for f in rd.prova(self.rot)])

    def test_aterstallningen_och_ett_arkiv_i_repot(self):
        rd.arkivera(self.rot, self.arkiv, brytpunkt='2026-10-09T18:40:00Z')
        mal = rd.aterstall('underlag/kund-a/referenser', self.rot)
        self.assertTrue((mal / 'paket-v01/PAKET.md').is_file())
        with self.assertRaises(ValueError):
            rd.arkivera(self.rot, self.rot / 'underlag' / 'arkiv')
        self.assertEqual(rd.prova(self.tmp / 'utan-register')[0]['vad'], 'registret saknas')


class GamlaNarInte(unittest.TestCase):
    """Punkt 12: gamla designartefakter och instruktioner når inte nya sessioner."""

    def test_lasforbuden(self):
        arkiv = 'Read(//%s/**)' % str(Path.home() / 'Arkiv').strip('/')
        for regel in ('Read(./underlag/rapporter/**)', 'Read(./underlag/granskningar/**)', 'Read(./underlag/rensning/**)', arkiv):
            self.assertIn(regel, atelje.NEKAS, 'flödets sessioner når %s' % regel)
        g = granska.nekas_for('x-prov')
        self.assertTrue({'Read(./underlag/rapporter/**)', 'Read(~/Arkiv/**)'} <= set(g), g)
        self.assertIn('~/Arkiv', sandlada.ARKIVERAT)
        kor = (ROOT / 'kor.sh').read_text()
        self.assertIn('"Read(~/Arkiv/**)"', kor)

    def test_nivafilen_och_kalibreringen(self):
        self.assertFalse((ROOT / 'kunskap/visuell-niva.md').exists())
        self.assertNotIn('kunskap/visuell-niva.md', [f for _n, f in granska.MATTSTOCKAR])
        self.assertFalse(any('visuell-niva' in f for v in skapande.METOD.values() for f in v['filer']))
        with tempfile.TemporaryDirectory() as d:
            st = granska.kalibreringsstatus(d)
        self.assertEqual((st['kalibrerad'], st['ankare']), (False, 0))
        self.assertIn('okalibrerad', st['text'])
        self.assertIn('gamla kalibreringsresultat gäller inte', st['text'])
        self.assertIn('Inga tidigare byggen som måttstock', (ROOT / 'kritik/GRANSKARE.md').read_text())
        self.assertIn('Senaste dom före brytpunkten: L6', (ROOT / 'LARDOMAR.md').read_text())

    def test_vakten_mot_gammal_styrning_finner_inget(self):
        fynd = styrning.prova()
        self.assertEqual(fynd, [], fynd[:5])
        self.assertTrue(styrning.fynd_i('Arbetsregeln är minst 3 varv', 'x'), 'den ersatta varvregeln fälls inte')
        self.assertTrue(styrning.fynd_i('Ribban: kunskap/visuell-niva.md', 'x'))
        self.assertTrue(styrning.fynd_i('De du väljer fördjupas till hela startsidan', 'x'))

    def test_en_gammal_session_forgrenas_inte(self):
        sys.path.insert(0, str(ROOT / 'dashboard'))
        import samverkan
        with tempfile.TemporaryDirectory() as d:
            u = Path(d) / 'underlag'
            skriv(u / 'rensning' / 'REN-DESIGNSTART-20261009.json', json.dumps({'brytpunkt': '2026-10-09T18:40:00Z'}))
            sid = '11111111-2222-3333-4444-555555555555'
            skriv(u / 'kund-a' / 'atelje' / 'sessioner' / ('%s.json' % sid), json.dumps({'start': '2026-10-09T12:00:00Z', 'slut': '2026-10-09T12:30:00Z'}))

            class Dash:
                UNDERLAG = u
            m = type('M', (), {'sessionslage': staticmethod(lambda slug, sid: None), 'Nekad': ValueError})
            with patch.multiple(samverkan, _m=lambda: m, _transkript=lambda sid: True, _spärr=lambda *a, **k: None):
                with self.assertRaises(ValueError) as e:
                    samverkan.foljdfraga(Dash, 'kund-a', {'id': 'gren-0001', 'session_id': sid, 'text': 'Varför valdes färgen?'})
        self.assertIn('före den rena designstarten', str(e.exception))


class Uppdragen(unittest.TestCase):
    """Punkt 8 och 11: uppdragets fält, kundens beslut och att ett val inte startar något."""

    def test_falten_kravs(self):
        for saknas in ('resultat', 'omfattning', 'bevara'):
            u = dict(UPPDRAG['ratta']); u.pop(saknas)
            with self.assertRaises(ValueError):
                skapande.uppdrag_giltigt(u)
        with self.assertRaises(ValueError):
            skapande.uppdrag_giltigt(dict(UPPDRAG['ratta'], typ='putsa'))
        u = skapande.uppdrag_giltigt(UPPDRAG['omarbeta'])
        self.assertEqual((u['namn'], u['specialister']), ('Omarbeta designen', None))
        self.assertEqual(kd.specialisterna(u), [('granskning', 'bedom')])
        self.assertEqual(kd.specialisterna(skapande.uppdrag_giltigt(UPPDRAG['ratta'])), [], 'en rättelse startade specialistpass')
        self.assertEqual(kd.specialisterna(skapande.uppdrag_giltigt(UPPDRAG['bygg_ut'])), [('rorelse', 'andra'), ('granskning', 'andra')])
        self.assertEqual(kd.specialisterna(skapande.uppdrag_giltigt(dict(UPPDRAG['bygg_ut'], specialister={}))), [], 'uttryckligen inga pass')

    def test_kundens_beslut(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                skapande.lagg_till_dom('k-a', 'kunden', 'uppdrag', 'Gör om första vyn', underlag=d, uppdrag=UPPDRAG['omarbeta'])
            with self.assertRaises(ValueError):
                skapande.lagg_till_dom('k-a', 'kunden', 'godkand', 'Godkänt', underlag=d, belagg='samtalet 10:00')
            post = skapande.lagg_till_dom('k-a', 'kunden', 'uppdrag', 'Gör om första vyn', underlag=d, belagg='samtalet 10:00', uppdrag=UPPDRAG['omarbeta'])
            self.assertTrue(skapande.ar_kundens(post) and skapande.ar_beslut(post) and not skapande.ar_agarens(post))
            self.assertIn('komposition och proportioner', post['ateroppnar'])
            self.assertEqual(skapande.avsandare(post)['typ'], 'kunden')
            v = skapande.lagg_till_dom('k-a', 'vidarebefordrad AI-bedömning', 'uppdrag', 'Codex föreslår', underlag=d, uppdrag=UPPDRAG['ratta'])
            self.assertFalse(skapande.ar_beslut(v), 'en AI-bedömning styr som kundens eller ägarens')
            self.assertEqual(skapande.senaste('k-a', underlag=d)['kalla'], 'kunden')


class Uppdragsfixtur(unittest.TestCase):
    """En vald kandidat k01 i version v1 med bevarad kod, attrapper vid sessionen, fotograferingen och återställningen."""
    SLUG = 'tio-prov'

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'uppdragen'))).resolve()
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.tmp / 'underlag', KUNDER=self.tmp / 'kunder'))
        self.stack.enter_context(patch.object(bildkedja, 'PROJEKT', self.tmp / 'projekt'))
        self.d = kd.kdir(self.SLUG, 'k01')
        self.pages = kd.ksajt(self.SLUG, 'k01') / 'src' / 'pages'
        skriv(self.pages / 'index.astro', '<h1>svag komposition</h1>')
        self.versioner, self.ater, self.sessioner = {'v1': {'index.astro': '<h1>svag komposition</h1>'}}, [], []
        self.nasta, self.fore_efter_svar = [2], {'totalt': 'oklart', 'skal': 'bilderna räcker inte', 'omraden': [], 'fynd': [], 'lasta': []}
        self.skapare = lambda prompt: None

        def rita_bilder(d_):
            for n in ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png'):
                skriv(d_ / n, png(n + json.dumps(sorted((str(p), p.read_text()) for p in self.pages.rglob('*.astro')))))

        def foto(slug, kid, skiss=None):
            sidor = {str(p.relative_to(self.pages)): p.read_text() for p in self.pages.rglob('*.astro')}
            v = next((k for k, x in self.versioner.items() if x == sidor), None)
            if not v:
                v = 'v%d' % self.nasta[0]; self.nasta[0] += 1
                self.versioner[v] = sidor
            rita_bilder(self.d / 'bilder' / 'start')
            return kd.satt_status(slug, kid, 'klar', 'fotograferad', version=v, axe={'allvarliga': 0})

        def ater(slug, kid, v):
            self.ater.append(v)
            import shutil
            shutil.rmtree(self.pages)
            self.pages.mkdir(parents=True)
            for n, t in self.versioner[v].items():
                skriv(self.pages / n, t)
            return foto(slug, kid)

        def bevara(slug, kid, v, bilder=True):
            mal = self.d / 'versioner' / str(v)[:12]
            skriv(mal / 'kod' / 'index.astro', self.versioner.get(v, {}).get('index.astro', 'x'))
            if bilder and (self.d / 'bilder' / 'start').is_dir() and not (mal / 'bilder').exists():
                for f in (self.d / 'bilder' / 'start').iterdir():
                    skriv(mal / 'bilder' / 'start' / f.name, f.read_bytes())
            return mal

        def session(prompt, verktyg, ut, schema=None, max_turer=200, modell=None, effort=None, frist=None, nekas=(), vid_start=None, slug=None, blind=None):
            self.sessioner.append({'prompt': prompt, 'verktyg': list(verktyg), 'schema': schema, 'nekas': list(nekas), 'blind': blind, 'modell': modell})
            so = None
            if schema is kd.FORE_EFTER_SCHEMA:
                so = self.fore_efter_svar
            elif schema is None:
                self.skapare(prompt)
                vd = self.d / 'varv' / 'start' / ('varv-%02d' % ((len(list((self.d / 'varv' / 'start').glob('varv-*'))) if (self.d / 'varv' / 'start').is_dir() else 0) + 1))
                rita_bilder(vd)  # ett helt förhandsvarv med fyra bilder
            svar = {'structured_output': so, 'session_id': None}
            Path(ut).write_text(json.dumps(svar))
            return svar

        self.stack.enter_context(patch.object(atelje, 'session', session))
        self.stack.enter_context(patch.multiple(kd, fotografera=foto, aterstall_och_fotografera=ater, bevara_version=bevara,
                                                bevarad=lambda slug, kid, v: str(v) in self.versioner,
                                                designkontroll=lambda slug, kid: {'ok': True, 'fel': []}, lasningen=lambda *a: None,
                                                metodinfo=lambda slug, steg: {'sha': 'm'}, regel_rader=lambda: [], metod_rader=lambda *a: [],
                                                etiketter=lambda slug, ids: {k: 'Förslag A' for k in ids}))
        self.stack.enter_context(patch.multiple(skapande, kritikrader=lambda *a, **k: [], fakta_rader=lambda *a, **k: [], telefon=lambda *a: None))
        self.stack.enter_context(patch.multiple(kompetens, prompt_rader=lambda *a, **k: [], verktyg=lambda *a, **k: []))
        kd.satt_status(self.SLUG, 'k01', 'vald', 'vald', version='v1', axe={'allvarliga': 0}, titel='A')
        rita_bilder(self.d / 'bilder' / 'start')

    def dom(self, typ, **u):
        return {'tid': '2026-10-09T19:00:00Z', 'kalla': 'ägaren', 'beslut': 'uppdrag', 'text': 'beställarens ord',
                'kandidater': [{'id': 'k01', 'version': 'v1'}], 'uppdrag': skapande.uppdrag_giltigt(dict(UPPDRAG[typ], **u))}


class RattelseUtanUtbyggnad(Uppdragsfixtur):
    def test_en_ny_sida_i_en_rattelse_aterstalls(self):
        self.skapare = lambda p: skriv(self.pages / 'tjanster' / 'index.astro', '<h1>ny undersida</h1>')
        st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('ratta'))
        self.assertEqual(st['status'], 'vald', st)
        self.assertIn('utanför omfattningen', st['skal'])
        self.assertEqual(st['version'], 'v1', 'rättelsen med en ny sida fördes vidare')
        self.assertFalse((self.pages / 'tjanster').exists())
        prompt = self.sessioner[0]['prompt']
        self.assertIn('Lägg inte till sidor', prompt)
        self.assertNotIn('hela startsidan', prompt, 'en rättelse beställde hela startsidan')
        self.assertFalse([s for s in self.sessioner if s['schema'] is kd.PASS_SCHEMA], 'en rättelse startade specialistpass')

    def test_en_rattelse_inom_omfattningen_fors_vidare_och_bedoms(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>rättad rubrik</h1>')
        self.fore_efter_svar = dict(self.fore_efter_svar, totalt='X')
        st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('ratta'))
        fe = st['forfining']['fore_efter']
        self.assertEqual(fe['utfall'], 'battre' if fe['efter_var'] == 'X' else 'samre')
        self.assertEqual(fe['avsandare'], skapande.AVSANDARTYPER['granskare'][0], 'före/efter bokfördes inte som en annan granskares bedömning')

    def test_omfattningsbrister(self):
        self.assertTrue(kd.omfattningsbrister({'typ': 'ratta', 'namn': 'Rätta'}, ['/'], ['/', '/ny/']))
        self.assertTrue(kd.omfattningsbrister({'typ': 'omarbeta', 'namn': 'Omarbeta designen'}, ['/'], ['/', '/ny/']))
        self.assertEqual(kd.omfattningsbrister({'typ': 'bygg_ut', 'omfattning': ['undersidan /tjanster/ och /kontakt/']}, ['/'], ['/', '/tjanster/']),
                         ['utbyggnaden saknar /kontakt/'])


class DesignomtagOchForeEfter(Uppdragsfixtur):
    def test_omtaget_far_byta_grundkomposition_och_battre_fors_vidare(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<main><section class="bildbard">helt ny komposition</section></main>')
        with patch.object(kd.random, 'random', lambda: 0.1):  # efter-versionen visas som X, och granskaren föredrar X
            self.fore_efter_svar = dict(self.fore_efter_svar, totalt='X')
            st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('omarbeta'))
        self.assertEqual(st['status'], 'forfinad', st)
        self.assertNotEqual(st['version'], 'v1')
        self.assertIn('helt ny komposition', (self.pages / 'index.astro').read_text())
        self.assertEqual(st['forfining']['fortsattning']['beslut'], 'fora_vidare')
        p = self.sessioner[0]['prompt']
        self.assertIn('Bär grundkompositionen inte: byt den', p)
        self.assertIn('Write(./kunder/%s/kandidater/k01/sajt/src/**)' % self.SLUG, self.sessioner[0]['verktyg'], 'omtaget får inte skriva om sidan')
        passen = [s for s in self.sessioner if s['schema'] is kd.PASS_SCHEMA]
        self.assertEqual(len(passen), 1)
        self.assertFalse([v for v in passen[0]['verktyg'] if str(v).startswith(('Write(', 'Edit('))], 'granskningen i läget bedöm fick skriva')

    def test_samre_aterstalls_och_star_valbar(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>sämre</h1>')
        with patch.object(kd.random, 'random', lambda: 0.9):  # efter är Y
            self.fore_efter_svar = dict(self.fore_efter_svar, totalt='X')  # granskaren föredrar före
            st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('omarbeta'))
        self.assertEqual((st['status'], st['version']), ('vald', 'v1'), 'en sämre version fördes vidare')
        efter = st['forfining']['fortsattning']['bevarad_efter']
        self.assertIn(efter, kd.valbara_versioner(st), 'den sämre versionen går inte att välja')
        self.assertIn('v1', kd.valbara_versioner(st))

    def test_oklart_star_som_oklart(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>annan</h1>')
        st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('omarbeta'))
        self.assertEqual(st['forfining']['fore_efter']['utfall'], 'oklart')
        self.assertEqual(st['forfining']['fortsattning']['beslut'], 'oklart')
        self.assertIn('inget besked', st['forfining']['fortsattning']['skal'])
        self.assertEqual(st['status'], 'forfinad', 'ett oklart resultat återställdes eller fördes vidare som bättre')

    def test_regeln(self):
        u = {'typ': 'ratta'}
        self.assertEqual(kd.fore_efter_regel(u, {'utfall': 'samre'}, {'granskning': {'visuell_bedomning': {'tekniskt_nodvandig': True}}})[0], 'kraver_losning')
        self.assertEqual(kd.fore_efter_regel(u, {'utfall': 'samre'}, {})[0], 'aterstall')
        self.assertEqual(kd.fore_efter_regel(u, {'utfall': 'likvardig'}, {})[0], 'fora_vidare')
        self.assertEqual(kd.fore_efter_regel(u, None, {})[0], 'oklart')


class RattRollFarRattUnderlag(Uppdragsfixtur):
    def test_fore_efter_granskaren_ar_blind_och_lasande(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>ändrad</h1>')
        kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('ratta'))
        fe = [s for s in self.sessioner if s['schema'] is kd.FORE_EFTER_SCHEMA]
        self.assertEqual(len(fe), 1)
        s = fe[0]
        self.assertTrue(s['blind'], 'före/efter-granskaren startade inte blind')
        self.assertTrue(any(n.startswith('Read(') and n.endswith('kunder/%s/**)' % self.SLUG) for n in s['nekas']), 'granskaren når kandidatens kod')
        self.assertTrue(any(n.startswith('Read(') and n.endswith('kandidater/k01/versioner/**)') for n in s['nekas']), 'granskaren når versionernas kod')
        self.assertFalse([v for v in s['verktyg'] if str(v).startswith(('Write(', 'Edit('))])
        self.assertNotIn('RIKTNING.md', s['prompt'], 'skaparens förklaring nådde granskaren')
        self.assertEqual(s['modell'], kd.GRANSKARE_MODELL)
        self.assertIn('fore_efter', kompetens.BLINDA)

    def test_uppdraget_bar_utgangspunkt_och_implementationsgrund(self):
        k = dict({f: '%s A' % f for f, _r in kd.PLANFALT}, titel='A', referensbilder=['underlag/x/referenser/a.png'],
                 utgangspunkt={'slag': 'komponent_21st', 'namn': 'Hero ur 21st', 'kalla': '21st.dev/x/hero'},
                 implementationsgrund={'slag': 'komponenter', 'kalla': '21st.dev/x/hero', 'ateranvands': 'komponentens TSX', 'aterskapas_ur_bild': False, 'insats': 'liten'},
                 skiljer_sig_i=['komposition', 'typografi'])
        kd.skriv_uppdrag(self.SLUG, 'k02', k, 2, 2)
        t = (kd.kdir(self.SLUG, 'k02') / 'UPPDRAG.md').read_text()
        self.assertIn('Implementationsgrund: komponenter, källa 21st.dev/x/hero', t)
        self.assertIn('Visuell utgångspunkt: Hero ur 21st', t)
        self.assertIn('underlag/x/referenser/a.png', t)
        self.assertIsNone(kd.planbrist(k))
        self.assertIn('skärmbild', kd.planbrist(dict(k, implementationsgrund=dict(k['implementationsgrund'], kalla='underlag/x/referenser/a.png'))))
        self.assertIn('bara i färg', kd.planbrist(dict(k, skiljer_sig_i=['farg'])))
        self.assertIn('bransch', kd.PLAN_SCHEMA['required'])


class Versionerna(Uppdragsfixtur):
    def test_en_tidigare_version_valjs_och_tas_fram(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>v2-innehåll</h1>')
        self.fore_efter_svar = dict(self.fore_efter_svar, totalt='likvardiga')
        st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('ratta'))
        self.assertEqual(st['status'], 'forfinad')
        nu = st['version']
        self.assertIn('v1', kd.valbara_versioner(st))
        rot = kd.rot(self.SLUG)
        skriv(rot / 'KANDIDATPLAN.json', json.dumps({'tid': '2026-10-09T18:00:00Z', 'kandidater': {'k01': {'titel': 'A'}}}))
        import ab
        self.stack.enter_context(patch.object(ab, 'skisskrav', lambda slug: None))
        ut = kd.prova_beslut(self.SLUG, 'valj', [{'id': 'k01', 'version': 'v1'}])
        self.assertEqual(ut[0]['version'], 'v1', 'en bevarad tidigare version gick inte att välja')
        with self.assertRaises(ValueError):
            kd.prova_beslut(self.SLUG, 'godkand', [{'id': 'k01', 'version': 'v1'}])  # godkännandet gäller versionen som visas
        dom = {'tid': '2026-10-09T19:30:00Z', 'kalla': 'ägaren', 'beslut': 'valj', 'text': 'v1 var bättre', 'kandidater': [{'id': 'k01', 'version': 'v1'}]}
        self.assertEqual(kd.versionsval(self.SLUG, dom), [('k01', 'v1')])
        status = {}
        kd.ta_fram_valda_versioner(self.SLUG, status, lambda: None, dom)
        st2 = kd.las_status(self.SLUG, 'k01')
        self.assertEqual((st2['version'], st2['vald_version'], st2['status']), ('v1', 'v1', 'vald'))
        self.assertTrue(kd.bevarad(self.SLUG, 'k01', nu), 'versionen som byttes ut bevarades inte')

    def test_slutbedomningen_galler_versionen_som_visas(self):
        self.skapare = lambda p: skriv(self.pages / 'index.astro', '<h1>efter</h1>')
        st = kd.forfina_kandidat(self.SLUG, 'k01', 'v1', self.dom('ratta'))
        fe = st['forfining']['fore_efter']
        self.assertEqual((fe['fore'], fe['efter']), ('v1', st['version']), 'före/efter gäller inte versionen som visas')


class Overlamningen(unittest.TestCase):
    """Punkt 7: den valda implementationen följer med som kod, komponenter och värden, med manifest och användning."""

    def test_manifestet(self):
        with tempfile.TemporaryDirectory() as d:
            paket = Path(d)
            skriv(paket / 'kod' / 'index.astro', '---\nimport Prislista from "../components/Prislista.astro";\n---\n<Prislista />')
            skriv(paket / kd.KODSRC / 'components' / 'Prislista.astro', '<table></table>')
            skriv(paket / kd.KODSRC / 'styles' / 'design.css', ':root{--farg-text:#111;--typ-rubrik-storlek:2rem}')
            with patch.object(kd, 'plan_tid', lambda slug: 'plan-1'):
                ut = kd.overlamning('x-prov', 'k01', 'a' * 64, paket, {'forfining': {'uppdrag': {'typ': 'bygg_ut', 'namn': 'Bygg ut', 'resultat': 'r'}}})
        man = json.loads(ut['OVERLAMNING.json'])
        self.assertEqual(man['komponenter'], [{'fil': 'components/Prislista.astro', 'anvands_i': ['index.astro']}])
        self.assertEqual(man['tokens']['variabler'], ['--farg-text', '--typ-rubrik-storlek'])
        self.assertIn('återskapas aldrig ur en sammanfattning', man['regel'])
        self.assertIn('kunder/x-prov/sajt', man['startapp'])
        self.assertIn('återskapar aldrig designen', ut['OVERLAMNING.md'])
        self.assertIn('OVERLAMNING.md', (ROOT / '.claude/skills/bygg-sajt/SKILL.md').read_text())


class ValetStartarInget(unittest.TestCase):
    """Ett val (valj) leder till väntan; ett uppdrag till läget valda; putsa i kandidatflödet stoppar."""

    def test_lage(self):
        st = {'steg': 'klar_for_bedomning', 'klar': '2026-10-09T18:00:00Z', 'startad': '2026-10-09T17:00:00Z', 'kandidatflode': True}
        def kor(dom, versionsval=()):
            with patch.multiple(prototyp.atelje, las_json=lambda p: st, avbruten=lambda s: False, kandidatkorning=lambda r, s: True), \
                 patch.multiple(prototyp.skapande, senaste=lambda slug, underlag=None: dom, agarens_senaste=lambda slug, underlag=None: {'oklara': []}), \
                 patch.object(kd, 'versionsval', lambda slug, d: list(versionsval)):
                return prototyp.lage('x-prov')
        bas = {'tid': '2026-10-09T18:30:00Z', 'kalla': 'ägaren', 'kandidater': [{'id': 'k01', 'version': 'v'}]}
        self.assertEqual(kor(dict(bas, beslut='valj'))[0], 'vanta', 'ett val startade arbete')
        self.assertEqual(kor(dict(bas, beslut='valj'), [('k01', 'v0')])[0], 'valda')
        self.assertEqual(kor(dict(bas, beslut='uppdrag', uppdrag={'namn': 'Rätta'}))[0], 'valda')
        self.assertEqual(kor(dict(bas, beslut='putsa'))[0], 'stopp')


if __name__ == '__main__':
    unittest.main()
