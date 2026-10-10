#!/usr/bin/env python3
"""Kundrepot (kontroller/kundrepo.py) med attrapper för gh, Wrangler-uppladdningen och Access-prövningen: lokalt repo från
projektstarten, idempotent och låst, fjärrepo bara för en verklig verksamhet och bara när beskrivningen bär projektets
markör, CLAUDE.md utan läckor, exporten som commit i det beständiga repot (exportera.py), push, och förhandsvisningen på
Cloudflare Workers med kvitto: väntar på kontot utan cloudflare.env, laddar aldrig upp verkligt material till en adress
som Cloudflare Access inte skyddar, och kvittot gäller de bytes som laddades upp. Inget nät, inget riktigt konto."""
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
VERSION = '11111111-2222-4333-8444-555555555555'
KONTO = 'a' * 32
TOKEN = 'SYNTETISK-CLOUDFLARE-TOKEN-0001'


class Kundrepo(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'kundrepots prov'))).resolve()
        self.slug = 'prov-kund'
        self.k, self.u = self.root / 'kunder' / self.slug, self.root / 'underlag' / self.slug
        self.u.mkdir(parents=True); self.k.mkdir(parents=True)
        shutil.copytree(Path(__file__).resolve().parents[3] / 'mall' / 'leverans', self.root / 'mall' / 'leverans',
                        ignore=shutil.ignore_patterns('node_modules', '.wrangler'))
        (self.root / 'mall' / 'astro' / 'src' / 'pages').mkdir(parents=True)
        for n in ('fel.astro', 'mottagen.astro'):
            (self.root / 'mall' / 'astro' / 'src' / 'pages' / n).write_text('---\n---\n<p>%s</p>\n' % n)
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag'))
        self.stack.enter_context(patch.multiple(exportera, ROOT=self.root, KUNDER=self.root / 'kunder', UNDERLAG=self.root / 'underlag',
                                                LEVERANS=self.root / 'mall' / 'leverans', MALL=self.root / 'mall' / 'astro'))
        self.bin = self.root / 'bin'; self.bin.mkdir()
        (self.bin / 'gh').write_text(GH); (self.bin / 'gh').chmod(0o700)
        self.state = self.root / 'gh-state'
        self.cf = self.root / 'hemligt' / 'cloudflare.env'  # finns inte förrän ett prov ansluter kontot
        self.stack.enter_context(patch.dict(os.environ, {'PATH': str(self.bin) + os.pathsep + os.environ['PATH'], 'PROV_GH_STATE': str(self.state),
                                                         'NWP_CLOUDFLARE_FIL': str(self.cf)}))
        self.uppladdat, self.skyddsprov = [], []
        self.deploy_fel, self.skydd_svar, self.under_uppladdning = None, [], None
        self.skriv_verksamhet(True)
        (self.u / 'BRIEF.md').write_text('# Brief\n\n**Primär handling:** begära offert via formuläret.\n')

    def anslut_konto(self, rattighet=0o600, **andra):
        self.cf.parent.mkdir(exist_ok=True)
        v = {'CLOUDFLARE_API_TOKEN': TOKEN, 'CLOUDFLARE_ACCOUNT_ID': KONTO, 'CLOUDFLARE_WORKERS_UNDERDOMAN': 'nortropic-prov', **andra}
        self.cf.write_text(''.join('%s=%s\n' % kv for kv in v.items() if kv[1] is not None)); self.cf.chmod(rattighet)

    def deploy(self, underlag, konto, post, tmp):
        # Wrangler-uppladdningens attrapp: registrerar vad som laddades upp och ur vilken katalog
        if self.under_uppladdning:
            self.under_uppladdning()
        m = Path(underlag) / 'public' / 'markor.txt'
        self.uppladdat.append({'cwd': str(underlag), 'markor': m.read_text() if m.is_file() else None, 'konto': konto['konto'],
                               'wrangler': (Path(underlag) / 'wrangler.jsonc').is_file(), 'commit': post['commit'], 'export': post['export']})
        if self.deploy_fel:
            return 1, self.deploy_fel
        return 0, 'Uploaded kund-prov-kund-forhandsvisning\nDeployed kund-prov-kund-forhandsvisning triggers\nCurrent Version ID: ' + VERSION

    def skydd(self, url):
        self.skyddsprov.append(url)
        return self.skydd_svar.pop(0) if self.skydd_svar else (True, 'HTTP 302 till Cloudflare Access')

    def forhandsvisa(self):
        return kundrepo.preview(self.slug, deploy=self.deploy, skydd=self.skydd)

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
        self.assertEqual((r / 'public' / 'markor.txt').read_text(), 'v1')
        self.assertTrue(all((r / n).is_file() for n in ('CLAUDE.md', 'worker/index.js', 'wrangler.jsonc', 'migrations/0001_forfragningar.sql', 'public/_headers')))
        self.assertFalse((r / 'src' / 'pages' / 'api').exists() or (r / 'vercel.json').exists(), 'ingen Vercel-funktion i en ny export')
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

    def exportera_med_repo(self):
        kundrepo.skapa(self.slug)
        if not (self.k / 'sajt').is_dir():
            self.sajt()
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=True, bygg=False)
        self.assertTrue(res['ok'], res.get('fel'))
        return res

    def test_forhandsvisningen_vantar_pa_kontot_utan_cloudflare_env(self):
        self.exportera_med_repo()
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'vantar_pa_konto'); self.assertIn('Cloudflare-kontot är inte anslutet', pv['hinder'][0])
        self.assertIn('CLOUDFLARE_API_TOKEN', pv['hinder'][0]); self.assertEqual(self.uppladdat, [])
        self.anslut_konto(rattighet=0o644)
        pv = self.forhandsvisa(); self.assertEqual(pv['status'], 'vantar_pa_konto'); self.assertIn('chmod 600', pv['hinder'][0])
        self.anslut_konto(CLOUDFLARE_WORKERS_UNDERDOMAN=None)
        pv = self.forhandsvisa(); self.assertIn('CLOUDFLARE_WORKERS_UNDERDOMAN', pv['hinder'][0])
        self.anslut_konto(CLOUDFLARE_ACCOUNT_ID='inte-ett-id')
        pv = self.forhandsvisa(); self.assertIn('fel form', pv['hinder'][0])
        self.assertEqual(self.uppladdat, [], 'utan ett giltigt konto laddas ingenting upp')
        self.assertEqual(len(list((self.k / 'leverans').glob('PREVIEW-*.json'))), 4, 'varje försök får sitt kvitto')

    def test_forhandsvisningen_binds_till_commit_och_export_med_kvitto(self):
        res = self.exportera_med_repo()
        self.anslut_konto()
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'klar', pv)
        self.assertEqual(pv['url'], 'https://kund-prov-kund-forhandsvisning.nortropic-prov.workers.dev')
        self.assertEqual((pv['commit'], pv['export'], pv['produktion'], pv['version_id']), (res['commit'], res['id'], False, VERSION))
        self.assertEqual((pv['plattform'], pv['miljo'], pv['worker'], pv['konto']), ('cloudflare-workers', 'forhandsvisning', 'kund-prov-kund-forhandsvisning', KONTO))
        self.assertEqual(len(self.uppladdat), 1); self.assertTrue(self.uppladdat[0]['wrangler'])
        self.assertEqual(self.skyddsprov, [pv['url']], 'en fiktiv verksamhet prövas efter uppladdningen; skyddet noteras')
        kvitto = (self.k / 'leverans' / (pv['id'] + '.json')).read_text()
        self.assertNotIn(TOKEN, kvitto, 'tokenen hamnar aldrig i kvittot')
        akt = kundrepo.preview_aktuell(self.slug)
        self.assertTrue(akt['aktuell'] and akt['fil'].endswith('.json'))
        kopia = self.root / 'manifestkopia'; shutil.copytree(self.k / 'kundrepo', kopia, ignore=shutil.ignore_patterns('.git'))
        fore = exportera.exportmanifest(kopia)
        for x in ('.wrangler/state/v3/d1/db.sqlite', 'paket/index.js', '.vercel/project.json'):
            (kopia / x).parent.mkdir(parents=True, exist_ok=True); (kopia / x).write_text('lokalt')
        self.assertEqual(exportera.exportmanifest(kopia), fore, 'Wranglers lokala lager, provpaketet och Vercels koppling ingår aldrig i manifestet')
        (kopia / 'src' / 'pages' / 'paket').mkdir(parents=True); (kopia / 'src' / 'pages' / 'paket' / 'index.astro').write_text('<h1>Paket</h1>')
        self.assertIn('src/pages/paket/index.astro', exportera.exportmanifest(kopia), 'en sida som heter paket räknas')
        # handlingen i Flöde: preview är nästa steg först när exportens commit är HEAD
        with patch.object(prototyp, 'lage', return_value=('valda', None)), patch.object(flodesstart, 'pagande', return_value=False):
            self.assertIn('preview', [h['id'] for h in prototyp.handlingar(self.slug)])
        flodesstart.krav(self.slug, 'preview')
        (self.k / 'sajt' / 'public' / 'markor.txt').write_text('v2')
        self.assertFalse(kundrepo.preview_aktuell(self.slug)['aktuell'] if exportera.aktuell(self.slug)['aktuell'] else False)
        with self.assertRaises(ValueError):
            flodesstart.krav(self.slug, 'preview')
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            exportera.exportera(self.slug, git=True, bygg=False)
        self.deploy_fel = '✘ [ERROR] bygget föll i provet'
        pv2 = self.forhandsvisa()
        self.assertEqual(pv2['status'], 'fel'); self.assertTrue(any('wrangler deploy' in h for h in pv2['hinder']), pv2)
        self.assertIsNone(pv2['version_id'])
        self.deploy_fel = None
        with patch.object(self, 'deploy', return_value=(0, 'Uploaded utan versionsrad')):
            pv3 = self.forhandsvisa()
        self.assertEqual(pv3['status'], 'fel', 'utan versions-id finns inget att binda kvittot till')
        self.assertEqual(len(list((self.k / 'leverans').glob('PREVIEW-*.json'))), 3, 'varje försök får sitt kvitto')

    def test_verkligt_material_laddas_aldrig_upp_utan_access(self):
        self.skriv_verksamhet(False)
        self.exportera_med_repo()
        self.anslut_konto()
        self.skydd_svar = [(False, 'HTTP 200 utan inloggning')]
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'vantar_pa_skydd'); self.assertIn('Cloudflare Access skyddar inte', pv['hinder'][0])
        self.assertEqual(self.uppladdat, [], 'ingen uppladdning till en oskyddad adress')
        # skyddad före, öppen efter (Access-applikationen togs bort under tiden): kvittot är rött
        self.skydd_svar = [(True, 'HTTP 302 till Cloudflare Access'), (False, 'HTTP 200 utan inloggning')]
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'fel'); self.assertTrue(any('svarar utan Cloudflare Access' in h for h in pv['hinder']), pv)
        self.skydd_svar = []
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'klar'); self.assertEqual((pv['skydd_fore'], pv['skydd']), ('HTTP 302 till Cloudflare Access',) * 2)

    def test_okant_utfall_sparrar_nytt_forsok_tills_avstamning(self):
        # T10/T11: ett tappat svar efter uppladdningen är ett okänt utfall; inget nytt försök i blindo, och avstämningen
        # mot Cloudflares lista (läsande) avgör
        res = self.exportera_med_repo()
        self.anslut_konto()
        with patch.object(self, 'deploy', return_value=(124, 'tidsgränsen 900 s nåddes')):
            pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'osaker'); self.assertIn('--stam-av', pv['hinder'][0])
        self.assertFalse(kundrepo.preview_aktuell(self.slug)['aktuell'])
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'vantar_pa_avstamning'); self.assertEqual(self.uppladdat, [], 'inget nytt försök före avstämningen')
        self.assertEqual(kundrepo.main([self.slug, '--preview']), 1)
        markor = 'nortropic_commit=%s nortropic_export=%s' % (res['commit'], res['id'])
        # meddelandet ligger på versionen (wrangler deploy --message); deploymenten visar att den är driftsatt
        versioner = [{'id': 'aaaaaaaa-0000-4000-8000-000000000000', 'annotations': {'workers/message': 'annat'}},
                     {'id': VERSION, 'annotations': {'workers/message': markor, 'workers/triggered_by': 'upload'}}]
        lista = lambda konto, tmp: {'versioner': versioner, 'deployments': [{'id': 'd1', 'versions': [{'version_id': VERSION, 'percentage': 100}]}]}  # noqa: E731
        av = kundrepo.avstam(self.slug, lista=lista, skydd=self.skydd)
        self.assertEqual((av['status'], av['version_id'], av['typ']), ('klar', VERSION, 'avstämning'))
        self.assertTrue(kundrepo.preview_aktuell(self.slug)['aktuell'], 'den avstämda deploymenten är kvittot')
        self.assertIsNone(kundrepo.osakert_forsok(self.slug))
        self.assertEqual(kundrepo.avstam(self.slug, lista=lista)['status'], 'inget_att_stamma_av')
        self.assertNotIn(TOKEN, ''.join(f.read_text() for f in (self.k / 'leverans').glob('PREVIEW-*.json')))

    def test_avstamning_utan_traff_slapper_ett_nytt_forsok_och_ett_fel_i_avstamningen_ar_fortsatt_okant(self):
        self.exportera_med_repo()
        self.anslut_konto()
        with patch.object(self, 'deploy', return_value=(1, 'Error: fetch failed (ECONNRESET)')):
            self.assertEqual(self.forhandsvisa()['status'], 'osaker')
        def faller(konto, tmp):
            raise RuntimeError('wrangler deployments list: nätet svarar inte')
        self.assertEqual(kundrepo.avstam(self.slug, lista=faller)['status'], 'osaker')
        self.assertIsNotNone(kundrepo.osakert_forsok(self.slug), 'en misslyckad avstämning är fortfarande okänd')
        # versionen med försökets märke finns men är inte driftsatt: ett nytt försök är säkert
        pv_ = kundrepo.osakert_forsok(self.slug)
        markor = 'nortropic_commit=%s nortropic_export=%s' % (pv_['commit'], pv_['export'])
        av = kundrepo.avstam(self.slug, lista=lambda konto, tmp: {'versioner': [{'id': VERSION, 'annotations': {'workers/message': markor}}], 'deployments': []})
        self.assertEqual(av['status'], 'avstamd_ingen'); self.assertIn('inte driftsatt', av['text_avstamning'])
        pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'klar'); self.assertEqual(len(self.uppladdat), 1)
        # ett fel före uppladdningen (npm, bygget, kontot) är ett fel, inget okänt utfall, också vid en tidsgräns
        with patch.object(self, 'deploy', return_value=(124, 'npm ERR! network ETIMEDOUT', 'fore')):
            pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'fel'); self.assertIsNone(kundrepo.osakert_forsok(self.slug))
        # ett verktyg som inte kan köras är ett fel, inget okänt utfall
        with patch.object(self, 'deploy', side_effect=FileNotFoundError('wrangler')):
            pv = self.forhandsvisa()
        self.assertEqual(pv['status'], 'fel'); self.assertIsNone(kundrepo.osakert_forsok(self.slug))

    def test_release_kraver_verksamhet_forhandsvisning_driftvarden_och_agarens_klick(self):
        # K02:s produktion: en fiktiv verksamhet släpps aldrig; därefter förhandsvisning, driftvärden och ägarens mandat
        self.exportera_med_repo()
        self.anslut_konto()
        self.assertEqual(self.forhandsvisa()['status'], 'klar')
        self.assertIn('fiktiv', kundrepo.release_krav(self.slug))
        self.skriv_verksamhet(False)
        self.assertIn('D1-databasen är inte kopplad', kundrepo.release_krav(self.slug))
        with self.assertRaises(ValueError):
            kundrepo.releasemandat(self.slug, 'dashboard')
        (self.u / 'CLOUDFLARE.json').write_text(json.dumps({'database_id': '12345678-1234-4123-8123-123456789abc',
                                                            'forfragan_till': 'kontakt@exempel.invalid', 'forfragan_fran': 'webb@exempel.invalid'}))
        with patch.object(exportera, 'verifiera_bygge', return_value=(True, 'attrapp')):
            res = exportera.exportera(self.slug, git=True, bygg=False)
        konfig = (self.k / 'kundrepo' / 'wrangler.jsonc').read_text()
        self.assertIn('12345678-1234-4123-8123-123456789abc', konfig); self.assertIn('kontakt@exempel.invalid', konfig)
        self.assertIn('ingen aktuell förhandsvisning', kundrepo.release_krav(self.slug), 'en ny commit kräver en ny förhandsvisning')
        self.assertEqual(self.forhandsvisa()['status'], 'klar')
        self.assertIsNone(kundrepo.release_krav(self.slug))
        uppladdat_fore = len(self.uppladdat)
        rel = kundrepo.release(self.slug, deploy=self.deploy)
        self.assertEqual(rel['status'], 'vantar_pa_mandat'); self.assertEqual(len(self.uppladdat), uppladdat_fore, 'ingen release utan mandat')
        with self.assertRaises(ValueError):
            kundrepo.releasemandat(self.slug, 'session')
        kundrepo.releasemandat(self.slug, 'dashboard')
        rel = kundrepo.release(self.slug, deploy=self.deploy)
        self.assertEqual((rel['status'], rel['produktion'], rel['version_id'], rel['commit'], rel['export']), ('klar', True, VERSION, res['commit'], res['id']))
        self.assertEqual(rel['worker'], 'kund-prov-kund'); self.assertNotIn(TOKEN, json.dumps(rel))
        self.assertEqual(kundrepo.release(self.slug, deploy=self.deploy)['status'], 'vantar_pa_mandat', 'mandatet gäller en release')
        # ett okänt utfall spärrar nästa release
        kundrepo.releasemandat(self.slug, 'dashboard')
        with patch.object(self, 'deploy', return_value=(124, 'tidsgränsen nåddes')):
            self.assertEqual(kundrepo.release(self.slug, deploy=self.deploy)['status'], 'osaker')
        kundrepo.releasemandat(self.slug, 'dashboard')
        self.assertEqual(kundrepo.release(self.slug, deploy=self.deploy)['status'], 'vantar_pa_avstamning')
        # handlingen i Byggflöde visas när releasen är möjlig
        with patch.object(prototyp, 'lage', return_value=('valda', None)), patch.object(flodesstart, 'pagande', return_value=False):
            self.assertIn('release', [h['id'] for h in prototyp.handlingar(self.slug)])
        flodesstart.krav(self.slug, 'release')
        # felaktiga driftvärden hamnar aldrig i kundrepot
        (self.u / 'CLOUDFLARE.json').write_text(json.dumps({'database_id': 'inte-ett-id'}))
        with self.assertRaises(ValueError):
            exportera.driftvarden(self.slug)

    def test_wranglers_miljo_och_kommandon(self):
        tmp = self.root / 'wr-tmp'; tmp.mkdir()
        konto = {'token': TOKEN, 'konto': KONTO, 'underdoman': 'nortropic-prov'}
        with patch.dict(os.environ, {'NWP_HEMLIG': 'x', 'ANTHROPIC_API_KEY': 'x', 'CLAUDE_CODE_X': 'x', 'GH_TOKEN': 'x'}):
            m = kundrepo.cloudflare_miljo(konto, tmp)
            self.assertEqual((m['CLOUDFLARE_API_TOKEN'], m['CLOUDFLARE_ACCOUNT_ID'], m['WRANGLER_SEND_METRICS']), (TOKEN, KONTO, 'false'))
            self.assertTrue(m['XDG_CONFIG_HOME'].startswith(str(tmp)), 'ingen ägarinloggning: Wranglers konfiguration i tmp')
            self.assertFalse([k for k in m if k.startswith(('NWP_', 'ANTHROPIC', 'CLAUDE', 'GH_'))])
            anrop = []
            def kommando(argv, cwd, frist=None, env=None):
                anrop.append((argv, env))
                ut = ('konto ' + KONTO) if argv[1:2] == ['whoami'] else 'Current Version ID: ' + VERSION
                return subprocess.CompletedProcess(argv, 0, ut, '')
            import processgrans
            with patch.object(kundrepo, 'kommando', side_effect=kommando), patch.object(processgrans, 'kor_i_katalog', return_value=(0, 'byggd')), \
                    patch.object(exportera, 'publika_brister', return_value=[]):
                rc, ut, steg = kundrepo.wrangler_deploy(tmp, konto, {'commit': 'c' * 40, 'export': 'EXPORT-1'}, tmp)
        self.assertEqual((rc, steg), (0, 'uppladdning')); self.assertIn(VERSION, ut)
        with patch.object(kundrepo, 'kommando', side_effect=kommando), patch.object(processgrans, 'kor_i_katalog', return_value=(0, 'byggd')), \
                patch.object(exportera, 'publika_brister', return_value=[]):
            kundrepo.wrangler_deploy(tmp, konto, {'commit': 'c' * 40, 'export': 'EXPORT-1'}, tmp, miljo=None)
        self.assertNotIn('--env', anrop[-1][0], 'produktionen är kundrepots toppnivå i wrangler.jsonc')
        del anrop[3:]
        npm, vem, wr = anrop
        self.assertEqual(vem[0][1:], ['whoami'], 'kontots identitet prövas hos leverantören före uppladdningen')
        self.assertEqual(npm[0][:2], ['npm', 'ci']); self.assertFalse([k for k in npm[1] if k.startswith(('CLOUDFLARE', 'NWP_', 'ANTHROPIC', 'CLAUDE'))], 'npm ci får ingen nyckel')
        self.assertEqual(wr[0][1:4], ['deploy', '--env', 'forhandsvisning']); self.assertNotIn('production', ' '.join(wr[0]))
        self.assertIn('nortropic_commit=' + 'c' * 40, ' '.join(wr[0])); self.assertEqual(wr[1]['CLOUDFLARE_API_TOKEN'], TOKEN)
        with patch.object(kundrepo, 'kommando', side_effect=kommando), patch.object(processgrans, 'kor_i_katalog', return_value=(0, 'byggd')), \
                patch.object(exportera, 'publika_brister', return_value=['wrangler.jsonc']):
            rc, ut, steg = kundrepo.wrangler_deploy(tmp, konto, {'commit': 'c' * 40, 'export': 'EXPORT-1'}, tmp)
        self.assertEqual((rc, steg), (1, 'fore')); self.assertIn('inte får bli publika', ut); self.assertEqual(len(anrop), 4, 'ingen uppladdning när dist/ bär privata filer')
        # en token som inte når kontot: ingen uppladdning
        anrop.clear()
        def annat_konto(argv, cwd, frist=None, env=None):
            anrop.append(argv); return subprocess.CompletedProcess(argv, 0, 'konto ' + 'b' * 32, '')
        with patch.object(kundrepo, 'kommando', side_effect=annat_konto), patch.object(processgrans, 'kor_i_katalog', return_value=(0, 'byggd')), \
                patch.object(exportera, 'publika_brister', return_value=[]):
            rc, ut, steg = kundrepo.wrangler_deploy(tmp, konto, {'commit': 'c' * 40, 'export': 'EXPORT-1'}, tmp)
        self.assertEqual((rc, steg), (1, 'fore')); self.assertIn('når inte kontot', ut); self.assertFalse(any('deploy' in a_ for a_ in anrop))

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
        # R07: A är exporterad och kontrollerad; under uppladdningen ändras kundrepot till B. Det som laddas upp är A, och
        # kvittot gäller A; kvittot är aldrig grönt för A medan B laddas upp
        self.sajt()
        (self.k / 'sajt' / 'public' / 'markor.txt').write_text('A')
        res = self.exportera_med_repo()
        self.anslut_konto()
        def byt():
            r = self.k / 'kundrepo'
            (r / 'public' / 'markor.txt').write_text('B')
            subprocess.run(['git', '-c', 'user.name=x', '-c', 'user.email=x@example.invalid', 'commit', '-qam', 'B under uppladdningen'], cwd=r, check=True)
        self.under_uppladdning = byt
        pv = self.forhandsvisa()
        upp = self.uppladdat
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
