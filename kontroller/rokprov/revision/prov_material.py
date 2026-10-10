#!/usr/bin/env python3
"""Materialsteget (kontroller/material.py) som mekanik utan konton och utan nät: uppdrag → attrapp eller väntande beställning,
versioner som aldrig skrivs över, import av en färdig tillgång med källa och rättigheter, koncept ur canvas-design, och
den faktiska användningen i en kandidat (bara genererat material; video kräver poster; Egen nej, påstår verksamhet nej)."""
import contextlib
import json
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import kandidater
import korregister
import material


class Material(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'materialstegets prov'))).resolve()
        self.slug = 'prov-material'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.object(material, 'HEM', self.root / 'hem'))
        (self.root / 'underlag' / self.slug).mkdir(parents=True)
        self.sajt = kandidater.ksajt(self.slug, 'k01'); (self.sajt / 'src').mkdir(parents=True)
        (self.root / 'underlag' / self.slug / 'bilder').mkdir()
        (self.root / 'underlag' / self.slug / 'bilder' / 'BILDER.md').write_text('| fil | Egen |\n|---|---|\n| foto.jpg | ja |\n')
        (self.root / 'underlag' / self.slug / 'bilder' / 'foto.jpg').write_bytes(b'jpg')
        def inget_nat(*a, **k):
            raise AssertionError('materialsteget gör inga nätanrop utan konto')
        self.stack.enter_context(patch.object(socket, 'create_connection', inget_nat))

    def test_attrapp_och_versioner(self):
        t = material.bestall(self.slug, 'en varm illustration av verkstadens stämning', 'bild', 'stubb')
        self.assertEqual((t['id'], t['status'], t['roll'], t['pastar_verksamhet']), ('m001', 'stubb', 'illustrativ', False))
        f = self.root / 'underlag' / self.slug / t['versioner'][0]['fil']
        self.assertTrue(f.is_file() and f.name == 'v01.svg' and 'STUBB' in f.read_text())
        t2 = material.bestall(self.slug, 'samma uppdrag, ny version', 'bild', 'stubb', igen='m001')
        self.assertEqual([v['version'] for v in t2['versioner']], [1, 2]); self.assertTrue(f.is_file(), 'v01 skrivs aldrig över')
        self.assertEqual(material.bestall(self.slug, 'nästa', 'bild', 'stubb')['id'], 'm002')
        self.assertFalse(material.anvand(self.slug, 'm001', 'k01', 'hero')['ok'], 'en stubb används aldrig')
        self.assertIn('stubb', material.anvand(self.slug, 'm001', 'k01', 'hero')['hinder'])

    def test_leverantorer_utan_konto_gor_inget_anrop(self):
        for lev, typ in (('higgsfield', 'bild'), ('nano-banana', 'bild'), ('seedance', 'video')):
            t = material.bestall(self.slug, 'uppdrag', typ, lev)
            self.assertEqual(t['status'], 'vantar_mandat_konto'); self.assertIsNone(t['versioner'][0]['fil'])
            self.assertIn('inget konto har lästs', t['versioner'][0]['hinder'])
            self.assertFalse(material.anvand(self.slug, t['id'], 'k01', 'hero')['ok'])
        (self.root / 'hem').mkdir(); (self.root / 'hem' / 'higgsfield.env').write_text('HIGGSFIELD_API_KEY=prov\n')
        t = material.bestall(self.slug, 'uppdrag', 'video', 'higgsfield')
        self.assertEqual(t['status'], 'vantar_mandat_konto'); self.assertIn('inget konto har lästs', t['versioner'][0]['hinder'])
        with self.assertRaises(ValueError):
            material.bestall(self.slug, 'x', 'video', 'nano-banana')

    def test_import_canvas_och_anvandning(self):
        png = kandidater.kdir(self.slug, 'k01') / 'koncept.png'
        png.parent.mkdir(parents=True, exist_ok=True); png.write_bytes(b'\x89PNG\r\n\x1a\nprov')
        k = material.canvas(self.slug, png, 'k01', 'kompositionsstudie för hero')
        self.assertEqual((k['status'], k['roll'], k['leverantor'], k['typ']), ('genererad', 'koncept', 'canvas-design', 'bild'))
        self.assertIn('canvas-design @', k['versioner'][0]['kalla']); self.assertIn('k01', k['versioner'][0]['kalla'])
        self.assertTrue(png.is_file(), 'originalet rörs inte')
        r = material.anvand(self.slug, k['id'], 'k01', 'hero')
        self.assertTrue(r['ok'], r); self.assertEqual(r['fil'], 'src/assets/material/hero__%s-v01.png' % k['id'])
        self.assertTrue((self.sajt / r['fil']).is_file())
        md = (kandidater.kdir(self.slug, 'k01') / 'material' / 'MATERIAL.md').read_text()
        self.assertIn('| nej | nej |', md); self.assertIn('koncept', md); self.assertIn('canvas-design', md)
        self.assertEqual(atelje.egna_bilder(self.slug), ['foto.jpg'], 'materialet räknas aldrig som verksamhetens egna bilder')
        self.assertEqual(material.las(self.slug)['tillgangar'][k['id']]['anvand'][0]['plats'], 'hero')
        # en genererad video (importerad ur leverantörens tjänst) kräver posterbild; reducerad rörelse står i raden
        mp4 = self.root / 'klipp.mp4'; mp4.write_bytes(b'mp4')
        v = material.importera(self.slug, mp4, 'higgsfield', 'stämningsklipp', 'Higgsfield, ägarens konto 2026-10-08', 'licens enligt tjänstens villkor')
        self.assertEqual((v['typ'], v['status']), ('video', 'genererad')); self.assertIn('poster', v['webb']['hinder'][0])
        self.assertFalse(material.anvand(self.slug, v['id'], 'k01', 'intro')['ok'])
        self.assertFalse(material.anvand(self.slug, v['id'], 'k01', 'intro', poster='m999')['ok'])
        r2 = material.anvand(self.slug, v['id'], 'k01', 'intro', poster=k['id'])
        self.assertTrue(r2['ok'], r2); self.assertTrue((self.sajt / 'src' / 'assets' / 'material' / ('intro__%s-poster.png' % v['id'])).is_file())
        md = (kandidater.kdir(self.slug, 'k01') / 'material' / 'MATERIAL.md').read_text()
        self.assertIn('posterbilden visas; ingen autouppspelning', md)
        with self.assertRaises(ValueError):
            material.importera(self.slug, mp4, 'nano-banana', 'x', 'k', 'r')
        self.assertFalse(material.anvand(self.slug, k['id'], 'k01', 'Hero Bild')['ok'], 'platsen är en enkel sträng')


class Skaparens_vag(unittest.TestCase):
    """R05 (GR-20261008-06af6ff-omgranskning-codex): skaparens session når materialsteget kandidatavgränsat genom sina verkliga
    argument, verktyget vägrar allt utanför kandidaten, och användningen redovisas i tre nivåer (kopierad, i källan, renderad)."""
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'materialets väg i skaparen'))).resolve()
        self.slug = 'prov-r05'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.object(material, 'HEM', self.root / 'hem'))
        (self.root / 'underlag' / self.slug).mkdir(parents=True)
        self.k01, self.k02 = kandidater.kdir(self.slug, 'k01'), kandidater.kdir(self.slug, 'k02')
        for k_ in ('k01', 'k02'):
            (kandidater.ksajt(self.slug, k_) / 'src' / 'pages').mkdir(parents=True)
        (self.k01 / 'koncept').mkdir(parents=True)
        self.png = self.k01 / 'koncept' / 'hero__koncept-lager.png'; self.png.write_bytes(b'\x89PNG\r\n\x1a\nprov')

    def test_sessionens_argument_bar_den_kandidatavgransade_vagen(self):
        import kompetens
        v = kandidater.verktyg(self.slug, 'k01') + kompetens.verktyg('skapa', self.slug, 'k01')
        a = atelje.session_args(v, None, 10, 'm', 'high', (), None)
        tillatna = a[a.index('--allowedTools') + 1:a.index('--disallowedTools')]
        monster = 'Bash(.venv/bin/python kontroller/material.py %s --kandidat k01 *)' % self.slug
        self.assertIn(monster, tillatna)
        self.assertFalse(any('material.py' in x and x != monster for x in tillatna), [x for x in tillatna if 'material.py' in x])
        self.assertNotIn('Bash', [x for x in tillatna if not x.startswith('Bash(')], 'ingen generell Bash-åtkomst')
        self.assertNotIn('Bash(.venv/bin/python kontroller/material.py %s --kandidat k02 *)' % self.slug, tillatna)
        p = '\n'.join(kompetens.prompt_rader('skapa', self.slug, 'k01'))
        self.assertIn('kontroller/material.py %s --kandidat k01' % self.slug, p)

    def kor(self, *args):
        """material.py som skaparens kommando: förankrat på kunden och kandidaten som tillåtelsemönstret kräver."""
        return material.main([self.slug, '--kandidat', 'k01', *args])

    def test_kandidatens_canvas_registreras_och_anvands_i_tre_nivaer(self):
        self.assertEqual(self.kor('--canvas', str(self.png), '--bestall', 'kompositionsstudie för hero'), 0)
        tid = next(iter(material.las(self.slug)['tillgangar']))
        self.assertEqual(self.kor('--anvand', tid, '--plats', 'hero'), 0)
        a = material.anvandning(self.slug, 'k01')
        self.assertEqual([(x['kopierad'], x['i_kallan'], x['renderad']) for x in a], [(True, False, False)], 'kopierad bevisar inte användning')
        sajt = kandidater.ksajt(self.slug, 'k01')
        namn = Path(a[0]['fil']).name
        (sajt / 'src' / 'pages' / 'index.astro').write_text('---\nimport bild from "../assets/material/%s";\n---\n<img src={bild.src} alt="">\n' % namn)
        self.assertEqual([(x['kopierad'], x['i_kallan'], x['renderad']) for x in material.anvandning(self.slug, 'k01')], [(True, True, False)])
        (sajt / 'dist' / '_astro').mkdir(parents=True)
        (sajt / 'dist' / '_astro' / ('%s.Ab12Cd.webp' % Path(namn).stem)).write_bytes(b'webp')
        (sajt / 'dist' / 'index.html').write_text('<img src="/_astro/%s.Ab12Cd.webp" alt="">' % Path(namn).stem)
        self.assertEqual([(x['kopierad'], x['i_kallan'], x['renderad']) for x in material.anvandning(self.slug, 'k01')], [(True, True, True)])
        self.assertEqual(material.anvandning(self.slug, 'k02'), [], 'en annan kandidats användning syns inte här')

    def test_allt_utanfor_kandidaten_vagras(self):
        hemlig = self.root / 'hem' / 'nyckel.png'; hemlig.parent.mkdir(parents=True); hemlig.write_bytes(b'\x89PNG hemlig')
        (self.k02 / 'koncept').mkdir(parents=True); annan = self.k02 / 'koncept' / 'x.png'; annan.write_bytes(b'\x89PNG k02')
        for fil in (hemlig, annan, self.root / 'underlag' / self.slug / 'bilder' / 'foto.png'):
            self.assertEqual(self.kor('--canvas', str(fil), '--bestall', 'x'), 1, fil)
            self.assertEqual(self.kor('--fil', str(fil), '--bestall', 'x', '--kalla', 'x', '--rattigheter', 'x'), 1, fil)
        lank = self.k01 / 'koncept' / 'lank.png'; lank.symlink_to(hemlig)
        self.assertEqual(self.kor('--canvas', str(lank), '--bestall', 'x'), 1, 'en länk ut ur kandidaten')
        self.assertEqual(material.main([self.slug, '--kandidat', 'k01', '--canvas', str(self.png), '--bestall', 'x', '--kandidat', 'k02']), 2, 'en andra --kandidat')
        self.assertEqual(material.las(self.slug)['tillgangar'], {}, 'inget registrerades')
        self.assertEqual(self.kor('--bestall', 'stämningsbild', '--leverantor', 'higgsfield'), 1, 'leverantörsanropet kräver konto: inget anrop')


class Kandidatgrans(unittest.TestCase):
    """N02 (GR-20261009-natt-omgranskning-codex): kandidatgränsen i materialsteget, två vägar var för sig. Väg A: de
    slutligt tolkade argumenten; ett tillåtet k01-prefix skriver aldrig till k02, inte heller med en förkortad flagga.
    Väg B: registret; k01 når inte k02:s privata koncept genom --visa, ett känt id, en posterbild eller en ny version,
    och inte med Read i sessionen. k01:s eget och ägarens uttryckligen gemensamma material fungerar."""

    kor = Skaparens_vag.kor

    def setUp(self):
        Skaparens_vag.setUp(self)  # samma kund och kandidater som R05:s prov, utan dess fall
        (self.k02 / 'koncept').mkdir(parents=True)
        p2 = self.k02 / 'koncept' / 'hero__k02-hemligt.png'; p2.write_bytes(b'\x89PNG\r\n\x1a\nk02')
        self.assertEqual(material.main([self.slug, '--kandidat', 'k02', '--canvas', str(p2), '--bestall', 'K02 PRIVAT KONCEPT']), 0)
        self.m_k02 = self.id_for('K02 PRIVAT KONCEPT')

    def id_for(self, uppdrag):
        return next(k for k, t in material.las(self.slug)['tillgangar'].items() if t['uppdrag'] == uppdrag)

    def kopierat(self, kid):
        d = kandidater.ksajt(self.slug, kid) / 'src' / 'assets' / 'material'
        return sorted(x.name for x in d.iterdir()) if d.is_dir() else []

    def utdata(self, *args):
        import io
        ut = io.StringIO()
        with contextlib.redirect_stdout(ut):
            rc = material.main([self.slug, '--kandidat', 'k01', *args])
        return rc, ut.getvalue()

    def test_a_ett_k01_prefix_skriver_aldrig_till_k02(self):
        for forkortad in (['--kand', 'k02'], ['--kandi', 'k02'], ['--kand=k02'], ['--kandidat=k02']):
            rc = material.main([self.slug, '--kandidat', 'k01', *forkortad, '--anvand', self.m_k02, '--plats', 'hero'])
            self.assertEqual(rc, 2, forkortad)
        self.assertEqual(self.kopierat('k02'), [], 'k01:s tillåtna prefix lade något i k02:s projekt')
        self.assertEqual(self.kopierat('k01'), [])
        self.assertNotIn('anvand', material.las(self.slug)['tillgangar'][self.m_k02], 'ingen användning bokfördes')
        rc = material.main([self.slug, '--kandidat', 'k01', '--kand', 'k02', '--canvas', str(self.png), '--bestall', 'x'])
        self.assertEqual(rc, 2, 'en förkortad flagga i importen')
        self.assertEqual(len(material.las(self.slug)['tillgangar']), 1, 'inget registrerades')

    def test_b1_visa_ger_inte_k02_privata_koncept(self):
        rc, ut = self.utdata('--visa')
        self.assertEqual(rc, 0)
        self.assertNotIn('K02 PRIVAT KONCEPT', ut, '--visa gav k02:s koncept')
        self.assertNotIn(self.m_k02, json.loads(ut)['tillgangar'])

    def test_b2_ett_kant_id_ger_inte_k02_privata_koncept(self):
        rc, ut = self.utdata('--anvand', self.m_k02, '--plats', 'hero')
        self.assertEqual(rc, 1)
        self.assertNotIn('K02 PRIVAT', ut)
        self.assertEqual(self.kopierat('k01'), [], 'k01 använde k02:s koncept genom ett känt id')
        fore = json.dumps(material.las(self.slug)['tillgangar'][self.m_k02], sort_keys=True)
        self.assertEqual(self.utdata('--bestall', 'ny version', '--igen', self.m_k02)[0], 1, 'en ny version av k02:s koncept')
        self.assertEqual(json.dumps(material.las(self.slug)['tillgangar'][self.m_k02], sort_keys=True), fore, 'k02:s tillgång ändrades')
        # posterbilden: en video ur k01:s egen import med k02:s bild som poster vägras
        (self.k01 / 'koncept' / 'film.mp4').write_bytes(b'mp4')
        self.assertEqual(self.utdata('--fil', str(self.k01 / 'koncept' / 'film.mp4'), '--bestall', 'k01 film', '--kalla', 'egen', '--rattigheter', 'egna')[0], 0)
        film = self.id_for('k01 film')
        rc, ut = self.utdata('--anvand', film, '--plats', 'hero', '--poster', self.m_k02)
        self.assertEqual(rc, 1, 'k02:s bild som poster')
        self.assertEqual(self.kopierat('k01'), [])
        # direkt läsning förbi verktyget: registret och filerna nekas skaparens Read i sessionens argument
        import kompetens
        a = atelje.session_args(kandidater.verktyg(self.slug, 'k01') + kompetens.verktyg('skapa', self.slug, 'k01'), None, 10, 'm', 'high',
                                kandidater.andra_nekas(self.slug, 'k01'), self.slug)
        nekade = a[a.index('--disallowedTools') + 1:]
        self.assertIn('Read(./underlag/%s/material/**)' % self.slug, nekade)
        self.assertEqual(material.main([self.slug, '--kandidat', 'k02', '--anvand', self.m_k02, '--plats', 'hero']), 0, 'k02 använder sitt eget')

    def test_eget_och_gemensamt_material_fungerar(self):
        self.assertEqual(self.kor('--canvas', str(self.png), '--bestall', 'K01 EGET'), 0)
        egen = self.id_for('K01 EGET')
        agarens = self.root / 'agarens.png'; agarens.write_bytes(b'\x89PNG agaren')
        self.assertEqual(material.main([self.slug, '--fil', str(agarens), '--bestall', 'GEMENSAMT KUNDMATERIAL', '--kalla', 'kunden',
                                        '--rattigheter', 'kundens']), 0, 'ägarens import utan --kandidat')
        gem = self.id_for('GEMENSAMT KUNDMATERIAL')
        t = material.las(self.slug)['tillgangar']
        self.assertEqual((t[gem]['gemensam'], t[gem]['kandidat'], t[egen]['kandidat'], t[egen]['gemensam']), (True, None, 'k01', False))
        rc, ut = self.utdata('--visa')
        self.assertEqual(sorted(json.loads(ut)['tillgangar']), sorted([egen, gem]))
        self.assertEqual(self.kor('--anvand', egen, '--plats', 'hero'), 0)
        self.assertEqual(self.kor('--anvand', gem, '--plats', 'tjanster'), 0)
        self.assertEqual(len(self.kopierat('k01')), 2)
        self.assertEqual(material.main([self.slug, '--kandidat', 'k02', '--anvand', gem, '--plats', 'hero']), 0, 'det gemensamma för k02 också')
        k02_vy = material.synliga(material.las(self.slug), 'k02')['tillgangar']
        self.assertNotIn(egen, k02_vy, 'k01:s eget syns inte för k02')
        self.assertEqual([a['kandidat'] for a in k02_vy[gem]['anvand']], ['k02'], 'var k01 lade det gemensamma är k01:s val')
        self.assertEqual(self.kor('--bestall', 'ny version av det gemensamma', '--igen', gem), 1, 'en ny version av gemensamt material är ägarens')
        self.assertEqual(material.main([self.slug, '--bestall', 'ägarens nya version', '--igen', gem]), 0)


if __name__ == '__main__':
    unittest.main()
