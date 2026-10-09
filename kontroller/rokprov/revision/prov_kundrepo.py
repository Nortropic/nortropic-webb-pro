#!/usr/bin/env python3
"""Kundrepot (kontroller/kundrepo.py) med attrapper för gh och vercel: lokalt repo från projektstarten, idempotent och
låst, fjärrepo bara för en verklig verksamhet och bara när beskrivningen bär projektets markör, CLAUDE.md utan läckor,
exporten som commit i det beständiga repot (exportera.py), push, Vercel-koppling och förhandsvisningens kvitto. Inget nät."""
import contextlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import exportera
import kundrepo
import korregister
import prototyp
import flodesstart

GH = r'''#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
st = Path(os.environ['PROV_GH_STATE']); st.mkdir(parents=True, exist_ok=True)
(st / 'anrop.log').open('a').write(json.dumps(sys.argv[1:]) + '\n')
a = sys.argv[1:]
if a[:2] == ['api'] + [a[1]] and a[1].startswith('repos/'):
    f = st / (a[1].split('/')[-1] + '.json')
    if f.is_file():
        print(f.read_text()); sys.exit(0)
    print('gh: Not Found (HTTP 404)', file=sys.stderr); sys.exit(1)
if a[:2] == ['repo', 'create']:
    if os.environ.get('PROV_GH_FEL'):
        print('gh: GraphQL: fel från provet', file=sys.stderr); sys.exit(1)
    namn = a[2].split('/')[-1]; d = {}; i = 3
    while i < len(a):
        if a[i] in ('--private', '--push', '--public'):
            d[a[i]] = True; i += 1
        else:
            d[a[i]] = a[i + 1]; i += 2
    if '--private' not in d:
        print('gh: provet kräver --private', file=sys.stderr); sys.exit(1)
    bare = st / (namn + '.git'); subprocess.run(['git', 'init', '--bare', '-q', str(bare)], check=True)
    src = d['--source']
    subprocess.run(['git', '-C', src, 'remote', 'add', d.get('--remote', 'origin'), str(bare)], check=True)
    if '--push' in d:  # som gh: bara med --push skickas lokala commits vid skapandet
        subprocess.run(['git', '-C', src, 'push', '-q', '-u', d.get('--remote', 'origin'), 'main'], check=True)
    (st / (namn + '.json')).write_text(json.dumps({'description': d.get('--description', ''), 'private': True, 'html_url': 'https://github.com/Nortropic/' + namn, 'clone_url': str(bare)}))
    sys.exit(0)
print('gh: okänt anrop i provet', file=sys.stderr); sys.exit(1)
'''
VERCEL = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
st = Path(os.environ['PROV_GH_STATE']); st.mkdir(parents=True, exist_ok=True)
(st / 'vercel.log').open('a').write(json.dumps(sys.argv[1:]) + '\n')
a = sys.argv[1:]
if a[:1] == ['link']:
    if os.environ.get('PROV_BYT_UNDER_KOPPLING') and Path('public/markor.txt').read_text() != 'B':  # R07: ett annat arbete ändrar kundrepot (A→B) under kopplingen
        Path('public/markor.txt').write_text('B')
        import subprocess as sp
        sp.run(['git', '-c', 'user.name=x', '-c', 'user.email=x@example.invalid', 'commit', '-qam', 'B under kopplingen'], check=True)
    namn = a[a.index('--project') + 1]
    if not (st / ('vercel-' + namn)).is_file():
        print('Error: Project not found', file=sys.stderr); sys.exit(1)
    Path('.vercel').mkdir(exist_ok=True); Path('.vercel/project.json').write_text(json.dumps({'projectId': 'prj_' + namn, 'orgId': 'team_nortropic'})); sys.exit(0)
if a[:2] == ['project', 'create']:
    (st / ('vercel-' + a[2])).write_text('x'); sys.exit(0)
if a[:1] == ['deploy']:
    if os.environ.get('PROV_VERCEL_FEL'):
        print('Error: bygget föll i provet', file=sys.stderr); sys.exit(1)
    m = Path('public/markor.txt')  # vad som faktiskt laddades upp (R07): arbetskatalogens innehåll när deploy körs
    (st / 'uppladdat.log').open('a').write(json.dumps({'cwd': os.getcwd(), 'markor': m.read_text() if m.is_file() else None}) + '\n')
    print('Inspect: https://vercel.com/nortropic/x', file=sys.stderr); print('https://kund-prov-abc123.vercel.app'); sys.exit(0)
if a[:1] == ['inspect']:
    print('  status      ● ' + os.environ.get('PROV_VERCEL_STATUS', 'Ready')); sys.exit(0)
print('vercel: okänt anrop i provet', file=sys.stderr); sys.exit(1)
'''


class Kundrepo(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kundrepots prov'))).resolve()
        self.slug = 'prov-kund'
        self.k, self.u = self.root / 'kunder' / self.slug, self.root / 'underlag' / self.slug
        self.u.mkdir(parents=True); self.k.mkdir(parents=True)
        (self.root / 'mall' / 'leverans').mkdir(parents=True)
        for n in ('gitignore', 'README.md', 'env.example', 'vercel.json', 'package.json', 'package-lock.json', 'forfragan.js'):
            (self.root / 'mall' / 'leverans' / n).write_bytes((Path(__file__).resolve().parents[3] / 'mall' / 'leverans' / n).read_bytes())
        (self.root / 'mall' / 'astro' / 'src' / 'pages').mkdir(parents=True)
        for n in ('fel.astro', 'mottagen.astro'):
            (self.root / 'mall' / 'astro' / 'src' / 'pages' / n).write_text('---\n---\n<p>%s</p>\n' % n)
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.multiple(exportera, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag',
                                                LEVERANS=self.root / 'mall' / 'leverans', MALL=self.root / 'mall' / 'astro'))
        self.bin = self.root / 'bin'; self.bin.mkdir()
        for n, t in (('gh', GH), ('vercel', VERCEL)):
            (self.bin / n).write_text(t); (self.bin / n).chmod(0o700)
        self.state = self.root / 'gh-state'
        self.stack.enter_context(patch.dict(os.environ, {'PATH': str(self.bin) + os.pathsep + os.environ['PATH'], 'PROV_GH_STATE': str(self.state)}))
        self.skriv_verksamhet(True)
        (self.u / 'BRIEF.md').write_text('# Brief\n\n**Primär handling:** begära offert via formuläret.\n')

    def skriv_verksamhet(self, fiktiv):
        (self.u / 'VERKSAMHET.json').write_text(json.dumps({'schema': 1, 'namn': 'Provfirman AB', 'fiktiv': fiktiv, 'tjanster': ['Prov', 'Kontroll'], 'kontaktvagar': []}))

    def gh_anrop(self):
        f = self.state / 'anrop.log'
        return [json.loads(r) for r in f.read_text().splitlines()] if f.is_file() else []

    def test_lokalt_repo_fran_projektstart_idempotent_och_utan_fjarr_for_fiktiv(self):
        kv = kundrepo.skapa(self.slug)
        r = self.k / 'kundrepo'
        self.assertTrue(kundrepo.ar_repo(r) and (r / 'CLAUDE.md').is_file() and (r / '.gitignore').is_file())
        self.assertEqual(kv['namn'], 'kund-prov-kund'); self.assertEqual(kv['org'], 'Nortropic'); self.assertEqual(kv['lokal'], 'kunder/prov-kund/kundrepo')
        self.assertEqual(kv['fjarr']['status'], 'saknas'); self.assertIn('fiktiv', kv['fjarr']['fel']); self.assertEqual(self.gh_anrop(), [])
        self.assertEqual(subprocess.run(['git', 'status', '--porcelain'], cwd=r, capture_output=True, text=True).stdout, '')
        md = (r / 'CLAUDE.md').read_text()
        self.assertNotIn('begära offert via formuläret', md, 'briefens text är privat råunderlag och följer inte med (R08)')
        self.assertIn('Nortropics brief', md); self.assertIn('Provfirman AB', md); self.assertIn('kund-prov-kund', md)
        self.assertEqual(exportera.lackor(r), [], 'CLAUDE.md får inte nämna lokala vägar, privat underlag eller nycklar')
        self.assertNotIn(str(self.root), md)
        kv2 = kundrepo.skapa(self.slug)
        self.assertEqual((kv2['projekt_id'], kv2['commit']), (kv['projekt_id'], kv['commit']), 'ett andra anrop skapar inget nytt')
        self.assertEqual(json.loads((self.k / 'KUNDREPO.json').read_text())['projekt_id'], kv['projekt_id'])

    def test_samtidiga_starter_ger_ett_repo(self):
        ut, fel = [], []
        def kor():
            try: ut.append(kundrepo.skapa(self.slug)['projekt_id'])
            except Exception as e: fel.append(repr(e))  # noqa: BLE001
        tr = [threading.Thread(target=kor) for _ in range(4)]
        [t.start() for t in tr]; [t.join() for t in tr]
        self.assertEqual(fel, []); self.assertEqual(len(set(ut)), 1)
        logg = subprocess.run(['git', 'log', '--oneline'], cwd=self.k / 'kundrepo', capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(len(logg), 1, logg)

    def test_verklig_verksamhet_far_privat_fjarrepo_med_markor(self):
        self.skriv_verksamhet(False)
        kv = kundrepo.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'skapat', kv['fjarr'])
        self.assertEqual(kv['fjarr']['adress'], 'https://github.com/Nortropic/kund-prov-kund')
        skapat = [a for a in self.gh_anrop() if a[:2] == ['repo', 'create']][0]
        self.assertIn('--private', skapat); self.assertIn('Nortropic/kund-prov-kund', skapat)
        self.assertIn(kundrepo.MARKOR + kv['projekt_id'], skapat[skapat.index('--description') + 1])
        fj = subprocess.run(['git', 'remote', '-v'], cwd=self.k / 'kundrepo', capture_output=True, text=True).stdout
        self.assertIn('origin', fj)
        self.assertEqual(kundrepo.skapa(self.slug)['fjarr']['status'], 'skapat')
        self.assertEqual(len([a for a in self.gh_anrop() if a[:2] == ['repo', 'create']]), 1, 'fjärrepot skapas en gång')
        p = kundrepo.push(self.slug)
        self.assertTrue(p['ok'], p); self.assertEqual(json.loads((self.k / 'KUNDREPO.json').read_text())['senaste_push']['commit'], kv['commit'])

    def test_namnkonflikt_binds_aldrig_och_fjarrfel_lamnar_lokalt_helt(self):
        self.skriv_verksamhet(False)
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / 'kund-prov-kund.json').write_text(json.dumps({'description': 'ett annat projekt', 'private': True, 'html_url': 'x'}))
        kv = kundrepo.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'namnkonflikt'); self.assertIn('fel kund', kv['fjarr']['fel'])
        self.assertNotIn('origin', subprocess.run(['git', 'remote'], cwd=self.k / 'kundrepo', capture_output=True, text=True).stdout)
        self.assertFalse(kundrepo.push(self.slug)['ok'])
        (self.state / 'kund-prov-kund.json').unlink()
        with patch.dict(os.environ, {'PROV_GH_FEL': '1'}):
            kv = kundrepo.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'fel'); self.assertIn('gh repo create', kv['fjarr']['fel'])
        self.assertTrue(kundrepo.ar_repo(self.k / 'kundrepo'), 'lokal skapning som lyckats står kvar')
        tom = self.root / 'tom'; tom.mkdir(); (tom / 'git').symlink_to(shutil.which('git'))  # git finns, gh saknas
        with patch.dict(os.environ, {'PATH': str(tom)}):
            kv = kundrepo.skapa(self.slug)
        self.assertEqual(kv['fjarr']['status'], 'fel'); self.assertIn('gh saknas', kv['fjarr']['fel'])
        self.assertEqual(kundrepo.skapa(self.slug)['fjarr']['status'], 'skapat', 'nästa försök lyckas när gh fungerar')

    def sajt(self):
        s = self.k / 'sajt'
        (s / 'src' / 'pages').mkdir(parents=True); (s / 'public').mkdir()
        (s / 'src' / 'pages' / 'index.astro').write_text('<h1>Prov</h1>'); (s / 'public' / 'markor.txt').write_text('v1')
        (s / 'package.json').write_text('{"dependencies":{}}')
        (s / 'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        return s

    def test_exporten_blir_commit_i_det_bestandiga_repot_och_pushas_nar_fjarr_ar_bundet(self):
        self.skriv_verksamhet(False)
        kundrepo.skapa(self.slug)
        s = self.sajt()
        r = self.k / 'kundrepo'
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=True, bygg=False)
        self.assertTrue(res['ok'], res.get('fel'))
        self.assertTrue(res.get('commit')); self.assertTrue(res['push']['ok'], res.get('push'))
        self.assertEqual((r / 'public' / 'markor.txt').read_text(), 'v1'); self.assertTrue((r / 'CLAUDE.md').is_file() and (r / 'src' / 'pages' / 'api' / 'forfragan.js').is_file())
        self.assertIn(res['id'], (r / 'CLAUDE.md').read_text())
        self.assertFalse((self.k / 'kundrepo-tidigare').exists(), 'historiken ligger i git, inte i en undankatalog')
        logg = subprocess.run(['git', 'log', '--format=%s'], cwd=r, capture_output=True, text=True).stdout.splitlines()
        self.assertEqual(len(logg), 2); self.assertTrue(logg[0].startswith('Export ' + res['id']), logg)
        akt = exportera.aktuell(self.slug)
        self.assertTrue(akt['aktuell'], 'exportens manifest stämmer med kundrepots träd (utan .git)')
        self.assertEqual(kundrepo.preview_krav(self.slug), None)
        (s / 'public' / 'markor.txt').write_text('v2')
        self.assertIn('inaktuell', kundrepo.preview_krav(self.slug))
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res2 = exportera.exportera(self.slug, git=True, bygg=False)
        self.assertTrue(res2['ok'] and res2['commit'] != res['commit'])
        self.assertEqual((r / 'public' / 'markor.txt').read_text(), 'v2')
        self.assertEqual(json.loads((self.k / 'KUNDREPO.json').read_text())['senaste_export']['id'], res2['id'])

    def test_forhandsvisningen_binds_till_commit_och_export_med_kvitto(self):
        kundrepo.skapa(self.slug)
        self.sajt()
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=True, bygg=False)
        self.assertTrue(res['ok'])
        pv = kundrepo.preview(self.slug)
        self.assertEqual(pv['status'], 'klar', pv); self.assertEqual(pv['url'], 'https://kund-prov-abc123.vercel.app')
        self.assertEqual((pv['commit'], pv['export'], pv['produktion']), (res['commit'], res['id'], False))
        logg = [json.loads(r) for r in (self.state / 'vercel.log').read_text().splitlines()]
        self.assertEqual([a[0] for a in logg], ['link', 'project', 'link', 'deploy', 'inspect'])
        dep = [a for a in logg if a[0] == 'deploy'][0]
        self.assertIn('nortropic_commit=' + res['commit'], dep); self.assertIn('nortropic_export=' + res['id'], dep); self.assertIn('nortropic', dep)
        self.assertIn('preview', dep); self.assertNotIn('production', ' '.join(dep))
        self.assertEqual(json.loads((self.k / 'KUNDREPO.json').read_text())['vercel']['projekt_id'], 'prj_kund-prov-kund')
        akt = kundrepo.preview_aktuell(self.slug)
        self.assertTrue(akt['aktuell'] and akt['fil'].endswith('.json'))
        self.assertFalse((self.k / 'kundrepo' / '.vercel').is_dir() and 'vercel' in exportera.exportmanifest(self.k / 'kundrepo'), '.vercel ingår aldrig i manifestet')
        # handlingen i Flöde: preview är nästa steg först när exportens commit är HEAD
        with patch.object(prototyp, 'lage', return_value=('valda', None)), patch.object(flodesstart, 'pagande', return_value=False):
            self.assertIn('preview', [h['id'] for h in prototyp.handlingar(self.slug)])
        flodesstart.krav(self.slug, 'preview')
        (self.k / 'sajt' / 'public' / 'markor.txt').write_text('v2')
        self.assertFalse(kundrepo.preview_aktuell(self.slug)['aktuell'] if exportera.aktuell(self.slug)['aktuell'] else False)
        with self.assertRaises(ValueError):
            flodesstart.krav(self.slug, 'preview')
        with patch.dict(os.environ, {'PROV_VERCEL_FEL': '1'}):
            with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
                exportera.exportera(self.slug, git=True, bygg=False)
            pv2 = kundrepo.preview(self.slug)
        self.assertEqual(pv2['status'], 'fel'); self.assertTrue(any('vercel deploy' in h for h in pv2['hinder']), pv2)
        self.assertEqual(len(list((self.k / 'leverans').glob('PREVIEW-*.json'))), 2, 'varje försök får sitt kvitto')

    def test_projektstart_med_lacka_avvisas_fore_commit_och_fjarrepo(self):
        # R08: en syntetisk lokal sökväg och ett syntetiskt nyckelmönster i det som genereras till CLAUDE.md avvisar projektstarten
        # innan något committas eller något fjärrepo skapas
        self.skriv_verksamhet(False)
        v = json.loads((self.u / 'VERKSAMHET.json').read_text())
        for falsk in ('Provfirman /Users/fiktiv/privat/BRIEF.md', 'Provfirman ghp_' + 'A1' * 15):
            v['namn'] = falsk
            (self.u / 'VERKSAMHET.json').write_text(json.dumps(v))
            with self.assertRaises(kundrepo.Hinder):
                kundrepo.skapa(self.slug)
            self.assertFalse(kundrepo.ar_repo(self.k / 'kundrepo'), 'ingen commit vid avvisad projektstart')
            self.assertEqual([a for a in self.gh_anrop() if a[:1] == ['repo']], [], 'inget fjärrepo vid avvisad projektstart')
            kv = json.loads((self.k / 'KUNDREPO.json').read_text())
            self.assertEqual(kv['projektstart']['status'], 'avvisad'); self.assertTrue(kv['projektstart']['lackor'])
        self.assertEqual(kundrepo.main([self.slug]), 1)
        # en godkänd projektstart efter rättelsen; därefter fäller en läcka i repot en push och ett nytt fjärrepo
        self.skriv_verksamhet(False)
        kv = kundrepo.skapa(self.slug)
        self.assertEqual((kv['projektstart']['status'], kv['fjarr']['status']), ('godkand', 'skapat'))
        (self.k / 'kundrepo' / 'anteckning.md').write_text('se underlag/prov-kund/BRIEF.md\n')
        subprocess.run(['git', '-c', 'user.name=x', '-c', 'user.email=x@example.invalid', 'add', '-A'], cwd=self.k / 'kundrepo', check=True)
        subprocess.run(['git', '-c', 'user.name=x', '-c', 'user.email=x@example.invalid', 'commit', '-qm', 'läcka'], cwd=self.k / 'kundrepo', check=True)
        p = kundrepo.push(self.slug)
        self.assertFalse(p['ok']); self.assertIn('läckagekontrollen', p['hinder'])

    def test_forhandsvisningen_laddar_upp_exportens_bytes_aven_om_repot_andras_under_kopplingen(self):
        # R07: A är exporterad och kontrollerad; under Vercel-kopplingen ändras kundrepot till B. Det som laddas upp är A, och
        # kvittot gäller A; kvittot är aldrig grönt för A medan B laddas upp
        kundrepo.skapa(self.slug)
        self.sajt()
        (self.k / 'sajt' / 'public' / 'markor.txt').write_text('A')
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=True, bygg=False)
        with patch.dict(os.environ, {'PROV_BYT_UNDER_KOPPLING': '1'}):
            pv = kundrepo.preview(self.slug)
        upp = [json.loads(x) for x in (self.state / 'uppladdat.log').read_text().splitlines()]
        self.assertEqual([u['markor'] for u in upp], ['A'], 'det som laddades upp är exportens A (R07)')
        self.assertNotEqual(Path(upp[0]['cwd']).resolve(), (self.k / 'kundrepo').resolve(), 'uppladdningen går ur det frysta underlaget')
        self.assertEqual((pv['status'], pv['commit'], pv['export']), ('klar', res['commit'], res['id']))
        self.assertEqual(pv['underlag_sha256'], res['export_sha256'])
        self.assertEqual((self.k / 'kundrepo' / 'public' / 'markor.txt').read_text(), 'B')
        self.assertFalse(kundrepo.preview_aktuell(self.slug)['aktuell'], 'kundrepot är nu B: kvittot för A är inte aktuellt')
        self.assertFalse(Path(upp[0]['cwd']).exists(), 'det frysta underlaget tas bort efteråt')
        # samma kontrakt för direkt CLI: kundens lås upptaget (en export pågår) ger ingen förhandsvisning
        import flodesstart
        with flodesstart.las(self.root, self.slug):
            self.assertEqual(kundrepo.main([self.slug, '--preview']), 1)

    def test_utan_kundrepo_ar_exporten_som_forr(self):
        self.sajt()
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=False, bygg=False)
        self.assertTrue(res['ok']); self.assertNotIn('commit', res)
        self.assertTrue((self.k / 'kundrepo' / 'CLAUDE.md').is_file() and not (self.k / 'kundrepo' / '.git').exists())
        self.assertIn('kundrepot finns inte', kundrepo.preview_krav(self.slug))


if __name__ == '__main__':
    unittest.main()
