#!/usr/bin/env python3
"""Källgrundade krav prövade mot syntetiska sidor, utan nät eller kundmaterial."""
import contextlib
import fcntl
import io
import json
import os
import signal
import threading
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import copy_kontroll
import korregister
import seo_kontroll
import prototyp
import atelje
import ateljeslut
import forberedelse
import startkontroll


def kf(text, namn):
    """KUNDFORSTAELSE.md med förberedelsens sex rubriker i ordning (forberedelse.kundforstaelse_brister, 2026-10-09); andra filer som de är."""
    if namn != 'KUNDFORSTAELSE.md':
        return text
    r_ = forberedelse.KUNDFORSTAELSE_RUBRIKER
    return text + '\n\n' + '\n\n'.join('## %s\n\n%s' % (r, '- Antaget: syntetiskt.' if r == r_[-1] else 'Syntetiskt.') for r in r_) + '\n'


class Kallgap(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetiskt flödesprov')))
        self.slug = 'prov-forberedelse'
        self.u = self.root / 'underlag' / self.slug
        (self.u / 'atelje').mkdir(parents=True)
        self.stack.enter_context(patch.multiple(atelje, ROOT=self.root, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.dict(os.environ, {'NWP_SANDLADA': 'av', 'NWP_OBSERVATION': 'av'}))
        self.stack.enter_context(patch.object(atelje, 'krav_slug'))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        v = {'schema': 1, 'namn': 'Syntetisk verksamhet', 'fiktiv': True, 'kontaktvagar': [],
             'rackvidd': {'typ': 'nationell'}, 'tjanster': ['Syntetisk tjänst']}
        (self.u / 'VERKSAMHET.json').write_text(json.dumps(v))
        (self.u / 'UPPDRAG.md').write_text('Syntetiskt uppdrag. Fakta som saknas blir frågor.')

    def test_verklig_forberedelsestart_utan_sajt_och_idempotens(self):
        with patch.object(atelje.subprocess, 'Popen', return_value=SimpleNamespace(pid=987654)) as spawn, \
             patch.object(atelje, 'vanta', return_value=5), patch.object(atelje, 'bevara_forra'), \
             patch.object(atelje, 'lever', return_value=False):
            args = [self.slug, '--forbered', '--vanta', '0', '--start-id', 'prov-start-1']
            self.assertEqual(atelje.main(args), 5)
            st = atelje.las_json(self.u / 'atelje/STATUS.json')
            self.assertEqual(st['lage'], 'forbered')
            self.assertEqual(st['start_id'], 'prov-start-1')
            self.assertEqual(atelje.main(args), 5)
            self.assertEqual(spawn.call_count, 1)
            self.assertEqual(atelje.main([self.slug, '--om', '--start-id', 'prov-start-1']), 2)
        self.assertFalse((self.root / 'kunder' / self.slug / 'sajt').exists())

    def test_forberedelsens_worker_aterbruk_och_andring(self):
        def session(_prompt, tools, output, *_args, **_kw):
            self.assertNotIn('Bash', tools)
            for name in forberedelse.FILER:
                (output.parent / name).write_text(kf('Syntetiskt utkast ' + name, name))
            return {'structured_output': {'klar': True, 'saknas': []}}
        st = {}
        with patch.object(atelje, 'session', side_effect=session) as sess:
            forberedelse.kor(self.slug, st, lambda: None)
            self.assertEqual(st['steg'], 'forberedd')
            self.assertTrue(forberedelse.giltig(self.slug))
            forberedelse.kor(self.slug, st, lambda: None)
            self.assertEqual(sess.call_count, 1)
            (self.u / 'UPPDRAG.md').write_text('Ändrat syntetiskt uppdrag')
            self.assertFalse(forberedelse.giltig(self.slug))
            forberedelse.kor(self.slug, st, lambda: None)
            self.assertEqual(sess.call_count, 2)
        self.assertEqual(ateljeslut.utfall(st)[1], 0)
        self.assertEqual(ateljeslut.fas(dict(st, lage='forbered')), 'forberedelse')
        self.assertEqual(prototyp.lage(self.slug)[0], 'om')

    def test_ofullstandigt_paket_skrivs_inte_till_arbetsytan(self):
        paket = self.u / 'atelje/paket'
        paket.mkdir()
        (paket / 'RESEARCH.md').write_text('Nytt syntetiskt utkast')
        (self.u / 'RESEARCH.md').write_text('Befintligt syntetiskt utkast')
        with self.assertRaises(ValueError):
            forberedelse.publicera(self.slug, paket, forberedelse.indata(self.slug))
        self.assertEqual((self.u / 'RESEARCH.md').read_text(), 'Befintligt syntetiskt utkast')
        self.assertFalse((self.u / 'atelje/FORBEREDELSE.json').exists())

    def test_startlas_stoppar_dubbelstart_men_aldrig_stopp(self):
        with (self.u / '.atelje-start.las').open('w') as locked:
            fcntl.flock(locked, fcntl.LOCK_EX)
            with patch.object(atelje.subprocess, 'Popen') as spawn, patch.object(atelje, 'stoppa', return_value=4) as stop:
                self.assertEqual(atelje.main([self.slug, '--forbered', '--vanta', '0']), 5)
                spawn.assert_not_called()
                self.assertEqual(atelje.main([self.slug, '--stoppa']), 4)
                stop.assert_called_once()

    def test_arbetarens_forberedelse_har_slutpost_utan_design_eller_stadning(self):
        gamla = {s: signal.getsignal(s) for s in atelje.STOPPSIGNALER}
        self.addCleanup(lambda: [signal.signal(s, h) for s, h in gamla.items()])
        atelje.STOPP.clear()
        def session(_prompt, _tools, output, *_args, **_kw):
            for name in forberedelse.FILER:
                (output.parent / name).write_text(kf('Syntetiskt underlag ' + name, name))
            return {'structured_output': {'klar': True, 'saknas': []}}
        with patch.object(startkontroll, 'for_start', return_value=None), \
             patch.object(atelje, 'session', side_effect=session), patch.object(atelje, 'stada') as clean, \
             patch.object(atelje, 'aterkalla') as revoke:
            self.assertEqual(atelje.arbeta(self.slug, 'forbered'), 0)
            clean.assert_not_called()
            revoke.assert_not_called()
        st = atelje.las_json(self.u / 'atelje/STATUS.json')
        self.assertEqual(st['steg'], 'forberedd')
        self.assertNotIn('slutpost_fel', st)
        _, post = ateljeslut.post_for(self.slug, st)
        self.assertEqual(post['slutkod'], 0)
        self.assertIsNone(post['tillstand']['designgranskaren_godkanner']['varde'])
        self.assertIsNone(post['tillstand']['agaren_godkanner']['varde'])
        self.assertFalse(post['tillstand']['klart_for_leverans']['varde'])
        self.assertEqual(prototyp.lage(self.slug)[0], 'om')
        ref = self.u / 'referenser/nytt'; ref.mkdir(parents=True)
        (ref / 'bild.png').write_bytes(b'syntetiskt resursprov')
        self.assertTrue(forberedelse.giltig(self.slug), 'referensjaktens nya material gör inte kundfakta inaktuella')
        atelje.arkivera_vid_ny_start(self.u / 'atelje')
        self.assertTrue(forberedelse.giltig(self.slug), 'designstarten bevarar förberedelsens identitet')

    def test_avbrott_vid_publicering_ar_aldrig_forberett_underlag(self):
        paket = self.u / 'atelje/paket'; paket.mkdir()
        for n in forberedelse.FILER:
            (paket / n).write_text(kf('Syntetiskt nytt underlag', n))
        replace = os.replace
        def fel(src, dst):
            if Path(dst).name == 'TEXTUNDERLAG.md':
                raise OSError('syntetiskt avbrott')
            return replace(src, dst)
        with patch.object(forberedelse.os, 'replace', side_effect=fel), self.assertRaises(OSError):
            forberedelse.publicera(self.slug, paket, forberedelse.indata(self.slug))
        self.assertFalse(forberedelse.giltig(self.slug))
        with patch.object(atelje.subprocess, 'Popen') as spawn:
            self.assertEqual(atelje.main([self.slug, '--om', '--vanta', '0']), 2)
            spawn.assert_not_called()

    def test_slutkvitto_skrivs_inte_genom_planterad_templank(self):
        paket = self.u / 'atelje/paket'; paket.mkdir()
        for n in forberedelse.FILER:
            (paket / n).write_text(kf('Syntetiskt nytt underlag', n))
        marker = self.root / 'markor.txt'; marker.write_text('orörd')
        (self.u / 'atelje/.FORBEREDELSE.json.tmp').symlink_to(marker)
        forberedelse.publicera(self.slug, paket, forberedelse.indata(self.slug))
        self.assertEqual(marker.read_text(), 'orörd')
        self.assertFalse((self.u / 'atelje/FORBEREDELSE.json').is_symlink())

    def test_startfel_far_provas_igen_med_samma_id(self):
        args = [self.slug, '--forbered', '--vanta', '0', '--start-id', 'prov-startfel-1']
        with patch.object(atelje, 'bevara_forra'), patch.object(atelje, 'vanta', return_value=5):
            with patch.object(atelje.subprocess, 'Popen', side_effect=OSError('syntetiskt startfel')):
                self.assertEqual(atelje.main(args), 2)
            self.assertEqual(atelje.las_json(self.u / 'atelje/STATUS.json')['steg'], 'fel')
            with patch.object(atelje.subprocess, 'Popen', return_value=SimpleNamespace(pid=987654)) as spawn:
                self.assertEqual(atelje.main(args), 5)
                spawn.assert_called_once()

    def test_stopp_efter_reservation_startar_inget_barn(self):
        riktig = atelje.skriv_json_atomiskt
        riktigt_las = atelje.processlas
        tradar, utfall = [], []
        huvudtrad = threading.get_ident()
        antal_las = [0]
        def stoppa():
            utfall.append(atelje.main([self.slug, '--stoppa']))
        def skriv(fil, st):
            riktig(fil, st)
            if st.get('status') == 'reserverad' and not tradar:
                t = threading.Thread(target=stoppa, daemon=True)
                tradar.append(t); t.start()
                # Utan ett lås över reservation + status hinner stoppet avslutas här.
                t.join(.1)
        @contextlib.contextmanager
        def las(rot):
            forst = threading.get_ident() == huvudtrad and antal_las[0] == 0
            if threading.get_ident() == huvudtrad:
                antal_las[0] += 1
            with riktigt_las(rot):
                yield
            if forst and tradar:
                tradar[0].join(3)
                self.assertFalse(tradar[0].is_alive(), 'stoppet ska kunna reservera avbrott före spawn')
        with patch.object(atelje, 'skriv_json_atomiskt', side_effect=skriv), patch.object(atelje, 'processlas', side_effect=las), \
             patch.object(atelje, 'bevara_forra'), patch.object(atelje, 'lever', return_value=False), \
             patch.object(atelje, 'stoppa_kvarvarande', return_value=[]), patch.object(atelje, 'avsluta_i_forteckningen'), \
             patch.object(atelje.subprocess, 'Popen', return_value=SimpleNamespace(pid=987654)) as spawn:
            self.assertEqual(atelje.main([self.slug, '--forbered', '--vanta', '0', '--start-id', 'prov-stopp-1']), 4)
            spawn.assert_not_called()
        self.assertEqual(utfall, [0])
        self.assertEqual(atelje.las_json(self.u / 'atelje/STATUS.json')['avbrott']['slag'], 'stopp')

    def test_tidigare_arbetsunderlag_ar_inte_osynligt_eller_foretradande(self):
        (self.u / 'UPPDRAG.md').unlink()
        research = self.u / 'RESEARCH.md'; research.write_text('Syntetisk källa A')
        innehall = self.u / 'INNEHALL.md'; innehall.write_text('Syntetiskt gammalt innehåll')
        forberedelse.krav(self.slug)
        grund = forberedelse.indata(self.slug)
        paket = self.u / 'atelje/paket'; paket.mkdir()
        for n in forberedelse.FILER:
            (paket / n).write_text(kf('Syntetiskt nytt underlag ' + n, n))
        research.write_text('Syntetisk källa B')
        with self.assertRaises(ValueError):
            forberedelse.publicera(self.slug, paket, grund)
        self.assertEqual(research.read_text(), 'Syntetisk källa B')
        forberedelse.publicera(self.slug, paket, forberedelse.indata(self.slug))
        import skapande
        self.assertEqual(skapande.textfil(self.slug, atelje.UNDERLAG).name, 'TEXTUNDERLAG.md')
        self.assertEqual((paket / 'fore/INNEHALL.md').read_text(), 'Syntetiskt gammalt innehåll')
        innehall.write_text('Ny syntetisk arbetsfil')
        self.assertFalse(forberedelse.giltig(self.slug))

    def test_forberedelse_fore_designgodkannande(self):
        with patch.object(prototyp.atelje, 'main', return_value=0) as start, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(prototyp.main(['prov-forberedelse', '--forbered', '--vanta', '0']), 0)
        args = start.call_args.args[0]
        self.assertIn('--forbered', args)
        self.assertEqual(args[0], 'prov-forberedelse')

    def test_metadata_langd_ar_information(self):
        with korregister.egen_tmp_med('nwp-kallgap-', 'källgapets prov') as tmp:
            root = Path(tmp)
            kort = '<html lang="sv"><head><title>Prov</title><meta name="description" content="En syntetisk beskrivning."><link rel="canonical" href="https://example.com/"></head><body><h1>Prov</h1></body></html>'
            lang = kort.replace('>Prov</title>', '>' + 'En längre sanningsenlig rubrik för en tydligt avgränsad provsida ' * 2 + '</title>')
            lang = lang.replace('En syntetisk beskrivning.', 'En syntetisk beskrivning av innehållet på den här provsidan. ' * 4)
            p = root / 'index.html'
            p.write_text(kort)
            bas = seo_kontroll.rapport(root, 'lansering', doman='example.com')
            p.write_text(lang)
            res = seo_kontroll.rapport(root, 'lansering', doman='example.com')
            self.assertEqual(res['fynd_totalt'], bas['fynd_totalt'])
            self.assertEqual(len(res['per_sida'][0]['info']), 2)
            self.assertIn('information', seo_kontroll.markdown(res))
            fynd, _ = copy_kontroll.kontrollera_fil(p, lang, [])
            self.assertTrue(any(f['typ'] == 'metalängd' for f in fynd))
            self.assertFalse(any('≤' in f['riktning'] for f in fynd if f['typ'] == 'metalängd'))
            p.write_text(kort.replace('<title>Prov</title>', '').replace('<meta name="description" content="En syntetisk beskrivning.">', ''))
            res = seo_kontroll.rapport(root, 'lansering', doman='example.com')
            typer = {f['typ'] for f in res['per_sida'][0]['fynd']}
            self.assertTrue({'title saknas', 'description saknas'} <= typer)


if __name__ == '__main__':
    unittest.main()
