#!/usr/bin/env python3
"""Riktiga lokala skillskript och statisk canvas; syntetiska filer i registrerad kopia.

--bas <repo>: samma prov mot äldre mekanik (saknad CLI är ett uttryckligt fel).
Inga modeller, installationer eller externa nätanrop. Kör seriellt med övriga rökprov.
"""
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
if '--bas' in sys.argv:
    i = sys.argv.index('--bas')
    REPO = Path(sys.argv[i + 1]).resolve()
    del sys.argv[i:i + 2]
if not (REPO / 'kontroller/skillskript.py').is_file():
    print('FEL: basen saknar den avgränsade skillskript-ingången; det riktiga anropet är inte körbart', file=sys.stderr)
    raise SystemExit(1)
sys.path.insert(0, str(REPO / 'kontroller'))
import korregister
if '--mekanik' in sys.argv:
    i = sys.argv.index('--mekanik')
    spec = importlib.util.spec_from_file_location('skillskript_provbas', sys.argv[i + 1])
    del sys.argv[i:i + 2]
    s = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s)
else:
    import skillskript as s
import webbtjanst


class Skillskript(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-skill-', 'skillskriptprov')))
        self.stack.enter_context(patch.object(s, 'ROOT', self.root))
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        # Ett vanligt PATH behövs för Node, men inga verkliga kund-/proxy-/nyckelvariabler.
        os.environ['PATH'] = os.defpath + ':/opt/homebrew/bin:/usr/local/bin'
        self.rel = 'underlag/prov/atelje/kandidater/k01'
        (self.root / self.rel).mkdir(parents=True)
        for skill in ('brand', 'design-system', 'ui-styling'):
            dst = self.root / '.claude/skills' / skill / 'scripts'
            shutil.copytree(REPO / '.claude/skills' / skill / 'scripts', dst)
        (self.root / '.venv').symlink_to((REPO / '.venv').resolve(), target_is_directory=True)
        for f in ('skillskript-canvas.mjs', 'webblasare/gemensamt.mjs'):
            dst = self.root / 'kontroller' / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / 'kontroller' / f, dst)
        (self.root / 'kontroller/node_modules').symlink_to((REPO / 'kontroller/node_modules').resolve(), target_is_directory=True)
        fontdir = REPO / '.claude/skills/canvas-design/canvas-fonts'
        if fontdir.is_dir():
            dst = self.root / '.claude/skills/canvas-design/canvas-fonts'
            dst.mkdir(parents=True)
            f = next(fontdir.glob('*.ttf'))
            shutil.copyfile(f, dst / f.name)
            self.font = f.name

    def fil(self, namn, text, rel=None):
        p = self.root / (rel or self.rel) / namn
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text if isinstance(text, bytes) else text.encode())
        return str(p.relative_to(self.root))

    def invoke(self, job, extra=()):
        p = self.fil('uppdrag.json', json.dumps(job))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return s.main(['prov', '--kandidat', 'k01', '--uppdrag', p, *extra])

    def resultat(self, id):
        p = self.root / self.rel / 'kompetens/skillskript' / id
        return p, json.loads((p / 'RESULTAT.json').read_text())

    def test_verkliga_brand_och_tokenfunktioner(self):
        md = self.fil('brand.md', '# Brand\n### Primary Colors\n| Name | Hex |\n|---|---|\n| Primary Color | #336699 |\n')
        for action in ('brand-context', 'brand-palette', 'brand-tokens'):
            with self.subTest(action=action):
                self.assertEqual(self.invoke({'id': action, 'action': action, 'input': md}), 0)
                p, r = self.resultat(action)
                self.assertEqual(r['status'], 'kord')
                self.assertEqual(r['visuell_kvalitet'], 'ej_bedomd')
                self.assertIn(md, r['inputs'])
                self.assertEqual(len(r['script_sha256']), 64)
                self.assertFalse(list(p.glob('nwp-skill-*')), 'den egna temporära katalogen ska städas')
        p, _ = self.resultat('brand-palette')
        self.assertIn('#336699', (p / 'stdout.txt').read_text())
        p, r = self.resultat('brand-tokens')
        self.assertTrue((p / 'design-tokens.css').stat().st_size)
        self.assertEqual(len(r['sources']), 2)
        tokens = self.fil('tokens.json', json.dumps({'semantic': {'color': {'brand': {'$type': 'color', '$value': '#336699'}}}}))
        for a in ('tokens-css', 'tokens-tailwind'):
            self.assertEqual(self.invoke({'id': a, 'action': a, 'input': tokens}), 0)
            p, _ = self.resultat(a)
            self.assertIn('#336699' if a == 'tokens-css' else 'var(--color-brand)',
                          (p / ('tokens.css' if a == 'tokens-css' else 'tokens.tailwind.cjs')).read_text())
        css = self.fil('tokens.css', ':root { --color-brand: #336699; }')
        self.assertEqual(self.invoke({'id': 'embed', 'action': 'tokens-embed', 'input': css}), 0)
        p, _ = self.resultat('embed')
        self.assertIn(':root { --color-brand: #336699; }', ' '.join((p / 'tokens.css').read_text().split()))

    def test_valideringens_fynd_ar_inte_godkant_resultat(self):
        css = self.fil('layout.css', 'body { color: #123456; padding: 17px; }')
        self.assertEqual(self.invoke({'id': 'audit', 'action': 'tokens-validate', 'files': [css]}), 1)
        _, r = self.resultat('audit')
        self.assertEqual(r['status'], 'underkand')
        html = self.fil('sida.astro', '<style>body { color: #123456; }</style>')
        self.assertEqual(self.invoke({'id': 'astro-audit', 'action': 'tokens-validate', 'files': [html]}), 1)
        svg = self.fil('x.svg', '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"/>')
        self.assertIn(self.invoke({'id': 'asset', 'action': 'brand-asset', 'input': svg}), (0, 1))
        p, r = self.resultat('asset')
        self.assertIn('valid', json.loads((p / 'stdout.txt').read_text()))
        self.assertEqual(r['visuell_kvalitet'], 'ej_bedomd')

    def test_tailwind_ar_utkast_utan_installation(self):
        self.assertEqual(self.invoke({'id': 'tailwind', 'action': 'tailwind-config', 'framework': 'nextjs',
                                     'colors': {'brand': '#336699'}, 'fonts': {'sans': 'Arial,sans-serif'}}), 0)
        p, _ = self.resultat('tailwind')
        text = (p / 'tailwind.config.ts').read_text()
        self.assertIn('#336699', text)
        self.assertFalse((self.root / 'package.json').exists())
        self.assertEqual(self.invoke({'id': 'installer', 'action': 'shadcn-add', 'input': 'button'}), 2)
        self.assertEqual(self.invoke({'id': 'plugins', 'action': 'tailwind-config', 'plugins': True}), 2)

    def test_eget_omrade_och_ingen_egen_kod(self):
        other = self.fil('hemligt.md', 'syntetiskt', 'underlag/prov/atelje/kandidater/k02')
        job = {'id': 'annan', 'action': 'brand-context', 'input': other}
        self.assertEqual(self.invoke(job), 2)
        for f in ('/etc/passwd', '../annat', self.rel + '/../k02/hemligt.md', 'underlag/annat/x'):
            self.assertEqual(self.invoke(dict(job, id='n' + str(len(f)), input=f)), 2)
        self.assertEqual(self.invoke({'id': 'argv', 'action': 'tailwind-config', 'argv': ['--output', '/tmp/x']}), 2)
        self.assertEqual(self.invoke({'id': 'script', 'action': 'tailwind-config', 'script': '/tmp/x.py'}), 2)
        with patch.object(s, 'kor', side_effect=AssertionError('får inte starta')):
            self.assertEqual(self.invoke({'id': 'extra', 'action': 'tailwind-config'}, ['--kandidat', 'k02']), 2)
            self.assertEqual(s.main(['prov', '--kand', 'k01', '--uppdrag', 'x']), 2)

    def test_absoluta_egna_vagar_fran_kundrepo(self):
        md = self.fil('koncept/brand.md', '# Brand\n### Primary Colors\n#336699\n')
        source = str(self.root / md)
        job = self.fil('kompetens/skriptuppdrag/absolut.json', json.dumps({
            'id': 'absolut', 'action': 'brand-palette', 'input': source}))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(s.main(['prov', '--kandidat', 'k01', '--uppdrag', str(self.root / job)]), 0)
        out, r = self.resultat('absolut')
        self.assertIn('#336699', (out / 'stdout.txt').read_text())
        self.assertIn(source, r['inputs'])
        own_src = self.fil('brand.md', '# Brand\n#336699\n', 'kunder/prov/kandidater/k01/sajt/src')
        self.assertEqual(self.invoke({'id': 'egen-src', 'action': 'brand-palette', 'input': str(self.root / own_src)}), 0)

    def test_absoluta_frammande_vagar_och_punktled_nekas(self):
        other = self.fil('brand.md', '# Syntetiskt', 'underlag/prov/atelje/kandidater/k02')
        own = self.fil('brand.md', '# Syntetiskt')
        bad_inputs = [str(self.root / other), str(self.root / self.rel) + '/../k01/brand.md',
                      str(self.root / self.rel) + '/./brand.md', str(self.root) + '-annat/' + own,
                      str(self.root / self.rel) + '//brand.md']
        for nr, source in enumerate(bad_inputs):
            with self.subTest(input=source):
                self.assertEqual(self.invoke({'id': 'neka-' + str(nr), 'action': 'brand-context', 'input': source}), 2)
        other_job = self.fil('uppdrag.json', json.dumps({'id': 'annan', 'action': 'tailwind-config'}),
                             'underlag/prov/atelje/kandidater/k02')
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(s.main(['prov', '--kandidat', 'k01', '--uppdrag', str(self.root / other_job)]), 2)
        link = self.root / self.rel / 'lank.md'
        link.symlink_to(self.root / other)
        self.assertEqual(self.invoke({'id': 'lank', 'action': 'brand-context', 'input': str(link)}), 2)

    def test_symlankar_hardlankar_och_forankring(self):
        own = self.fil('own.md', 'syntetiskt')
        link = self.root / self.rel / 'link.md'
        link.symlink_to(self.root / own)
        self.assertEqual(self.invoke({'id': 'link', 'action': 'brand-context', 'input': str(link.relative_to(self.root))}), 2)
        hard = self.root / self.rel / 'hard.md'
        os.link(self.root / own, hard)
        self.assertEqual(self.invoke({'id': 'hard', 'action': 'brand-context', 'input': own}), 2)
        dest = self.root / self.rel / 'kompetens'
        if dest.exists():
            shutil.rmtree(dest)
        outside = self.root / 'outside'
        outside.mkdir()
        dest.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.invoke({'id': 'escape', 'action': 'tailwind-config'}), 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_jobbet_ersatts_aldrig_och_fel_blir_inte_gront(self):
        job = {'id': 'ett', 'action': 'tailwind-config', 'colors': {'brand': '#336699'}}
        self.assertEqual(self.invoke(job), 0)
        p, r = self.resultat('ett')
        old = (p / 'RESULTAT.json').read_bytes()
        self.assertEqual(self.invoke(job), 2)
        self.assertEqual((p / 'RESULTAT.json').read_bytes(), old)
        def tom(script, args, tmp):
            (tmp / 'stdout.txt').write_text('')
            (tmp / 'stderr.txt').write_text('')
            return 0
        with patch.object(s, 'kor_subprocess', side_effect=tom):
            self.assertEqual(self.invoke(dict(job, id='tom')), 2)
        self.assertFalse((p.parent / 'tom/RESULTAT.json').exists())

    def test_katalogbyte_flyttar_inte_arbetskopian_eller_utdata(self):
        original = korregister.egen_tmp_med
        outside = self.root / 'utanforkandidaten'
        outside.mkdir()
        @contextlib.contextmanager
        def byt_katalog(prefix, vad, dir=None):
            if vad.startswith('skillskript '):
                out = self.root / self.rel / 'kompetens/skillskript/bytt'
                out.rename(out.with_name('egen-bevarad'))
                out.symlink_to(outside, target_is_directory=True)
            with original(prefix, vad, dir=dir) as tmp:
                yield tmp
        with patch.object(korregister, 'egen_tmp_med', side_effect=byt_katalog):
            self.assertEqual(self.invoke({'id': 'bytt', 'action': 'tailwind-config'}), 2)
        self.assertEqual(list(outside.iterdir()), [], 'ingen arbetsfil eller utdata får hamna via det utbytta målet')

    def test_miljon_kan_inte_lagga_till_node_program(self):
        os.environ['NODE_OPTIONS'] = '--require /finns-inte/otillatet.js'
        os.environ['PYTHONPATH'] = '/finns-inte'
        self.assertEqual(self.invoke({'id': 'ren', 'action': 'tailwind-config'}), 0)
        md = self.fil('brand.md', '# Brand\n### Primary\n#336699\n')
        self.assertEqual(self.invoke({'id': 'ren-node', 'action': 'brand-palette', 'input': md}), 0)

    def test_sigterm_stoppar_vendorprocess_och_stadar(self):
        marker = self.root / 'child-start.json'
        script = self.root / '.claude/skills/brand/scripts/inject-brand-context.cjs'
        script.write_text('require("fs").writeFileSync(%s,JSON.stringify({pid:process.pid,cwd:process.cwd()}));setInterval(()=>{},1000);' % json.dumps(str(marker)))
        src = self.fil('brand.md', '# Syntetiskt prov')
        job = self.fil('uppdrag.json', json.dumps({'id': 'signal', 'action': 'brand-context', 'input': src}))
        # Samma mekanikmodul också vid --mekanik, så signalfelet kan visas rött före rättelsen.
        code = ('import sys,importlib.util;from pathlib import Path;sys.path.insert(0,%r);'
                's=importlib.util.spec_from_file_location("provwrapper",%r);m=importlib.util.module_from_spec(s);'
                's.loader.exec_module(m);m.ROOT=Path(%r);sys.exit(m.main(%r))') % (
                    str(REPO / 'kontroller'), s.__file__, str(self.root), ['prov', '--kandidat', 'k01', '--uppdrag', job])
        proc = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        child, work = None, None
        try:
            end = time.monotonic() + 5
            while not marker.exists() and proc.poll() is None and time.monotonic() < end:
                time.sleep(0.02)
            self.assertTrue(marker.exists(), 'det syntetiska vendorskriptet måste ha startat')
            info = json.loads(marker.read_text()); child = info['pid']; work = Path(info['cwd'])
            proc.send_signal(signal.SIGTERM)
            out, err = proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 143, err.decode())
            with self.assertRaises(ProcessLookupError):
                os.kill(child, 0)
            self.assertFalse(Path(info['cwd']).exists(), 'registrerad arbetskopia ska städas också vid SIGTERM')
        finally:
            if proc.poll() is None:
                proc.kill(); proc.wait()
            if child:
                try:
                    os.killpg(child, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if work and work.exists():
                agare, _ = korregister.tmp_agare(work)
                if agare and agare.get('pid') == proc.pid:
                    shutil.rmtree(work)
            proc.stdout.close(); proc.stderr.close()

    def test_canvas_nekar_kod_nat_och_html(self):
        bodies = ['<script>alert(1)</script>', '<foreignObject><p>html</p></foreignObject>',
                  '<image href="file:///etc/passwd"/>', '<image href="https://example.com/a.png"/>',
                  '<rect onload="x()"/>', '<style>@import "https://example.com";</style>',
                  '<rect fill="url(https://example.com/a.svg)"/>']
        for i, body in enumerate(bodies):
            f = self.fil('canvas.svg', '<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>')
            self.assertEqual(self.invoke({'id': 'deny-' + str(i), 'action': 'canvas', 'input': f,
                                          'width': 48, 'height': 32}), 2)
        with self.assertRaises(s.Nekat):
            s.statisk_svg(b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>&x;</svg>')

    def test_canvas_verklig_png_pdf_utan_nya_beroenden(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 32"><rect width="48" height="32" fill="#336699"/><text x="2" y="20" font-family="%s" font-size="10">ABC</text></svg>' % self.font[:-4]
        f = self.fil('canvas.svg', svg)
        self.assertEqual(self.invoke({'id': 'canvas', 'action': 'canvas', 'input': f, 'width': 48,
                                     'height': 32, 'format': 'both', 'fonts': [self.font]}), 0)
        p, r = self.resultat('canvas')
        png = (p / 'canvas.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', png[16:24]), (48, 32))
        self.assertTrue((p / 'canvas.pdf').read_bytes().startswith(b'%PDF-'))
        self.assertEqual(json.loads((p / 'stdout.txt').read_text())['externa_anrop'], 0)
        self.assertEqual(r['visuell_kvalitet'], 'ej_bedomd')

    def test_canvas_delegeras_och_servern_nekar_andra_atgarder(self):
        f = self.fil('canvas.svg', '<svg xmlns="http://www.w3.org/2000/svg"/>')
        job = {'id': 'delegat', 'action': 'canvas', 'input': f, 'width': 48, 'height': 32}
        with patch.object(webbtjanst, 'delegeras', return_value=True), patch.object(webbtjanst, 'via_tjanst', return_value=7) as via:
            self.assertEqual(self.invoke(job), 7)
            self.assertEqual(via.call_args.args[0], 'skillskript-canvas')
            self.assertEqual(via.call_args.args[1][:3], ['prov', '--kandidat', 'k01'])
        p = self.fil('uppdrag.json', json.dumps({'id': 'ej-canvas', 'action': 'tailwind-config'}))
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(s.main(['--bara-canvas', 'prov', '--kandidat', 'k01', '--uppdrag', p]), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
