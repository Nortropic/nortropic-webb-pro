"""Materialtransport utan nät eller konton: officiella wire-format, mandat och återhämtning.

Attrappen ersätter endast HTTP. Registrering, kundgräns, kandidatägarskap, hash,
nyckelfil i egen temp och användning går genom materialstegets riktiga ingångar.
"""
import base64
import contextlib
from email.message import Message
import io
import json
import os
from pathlib import Path
import socket
import sys
import unittest
import urllib.error
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje
import kandidater
import korregister
import material
import material_transport as mt

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
MP4 = b'\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2'
RID = '00000000-0000-4000-8000-000000000001'


class HTTP:
    def __init__(self, replies, data=PNG, mime='image/png'):
        self.replies = list(replies); self.calls = []; self.data = data; self.mime = mime

    def json(self, url, headers, body=None, timeout=30):
        self.calls.append(('POST' if body is not None else 'GET', url, dict(headers), body))
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def las(self, url, **kwargs):
        self.calls.append(('FILE', url, kwargs.get('headers'), None))
        return self.data, self.mime


def gemini():
    return {'status': 'completed', 'steps': [{'type': 'model_output', 'content': [
        {'type': 'image', 'mime_type': 'image/png', 'data': base64.b64encode(PNG).decode()}]}]}


def higgs(typ='bild'):
    return [{'request_id': RID, 'status_url': 'https://foreign.example/status'},
            dict({'request_id': RID, 'status': 'completed'}, **({'images': [{'url': 'https://media.example/result.png?token=syntetiskt'}]} if typ == 'bild' else
                {'video': {'url': 'https://media.example/result.mp4?token=syntetiskt'}}))]


class Wire(unittest.TestCase):
    def setUp(self):
        self.no_network = patch.object(socket, 'create_connection', side_effect=AssertionError('nät är förbjudet i provet'))
        self.no_network.start(); self.addCleanup(self.no_network.stop)

    def test_gemini_aktuellt_restformat_inte_sdk_format(self):
        h = HTTP([gemini()]); j = mt.uppdrag('nano-banana', 'bild', 'An abstract shape')
        result = mt.kor(j, 'syntetisk-nyckel', http=h)
        self.assertEqual(result['data'], PNG)
        self.assertEqual(h.calls[0][:3], ('POST', mt.GEMINI, {'x-goog-api-key': 'syntetisk-nyckel'}))
        body = h.calls[0][3]
        self.assertEqual(body['input'], [{'type': 'text', 'text': 'An abstract shape'}])
        self.assertEqual(body['response_format']['delivery'], 'inline')
        self.assertIs(body['store'], False)
        with self.assertRaises(mt.TransportFel):
            mt.kor(j, 'key', http=HTTP([{'status': 'completed', 'output_image': {'data': 'a'}}]))

    def test_higgsfield_bild_och_seedance_video_delar_transport(self):
        for typ, data, mime in [('bild', PNG, 'image/png'), ('video', MP4, 'video/mp4')]:
            h = HTTP(higgs(typ), data, mime); ids = []
            j = mt.uppdrag('higgsfield', typ, 'An abstract shape')
            self.assertEqual(mt.kor(j, 'syntetisk', http=h, registrera=ids.append)['data'], data)
            self.assertEqual(ids, [RID])
            self.assertEqual(h.calls[0][1], mt.HIGGSFIELD + '/' + j['modell'])
            self.assertEqual(h.calls[0][2]['Authorization'], 'Key syntetisk')
            self.assertEqual(h.calls[0][2]['Idempotency-Key'], mt.sha(j))
            self.assertNotIn('input', h.calls[0][3])
            self.assertEqual(h.calls[1][1], mt.HIGGSFIELD + '/requests/' + RID + '/status')
            self.assertIsNone(h.calls[2][2], 'API-nyckel följer aldrig med till CDN')

    def test_byteplus_las_ar_separat_seedance_konto(self):
        h = HTTP([{'id': 'lsd-12345678'}, {'id': 'lsd-12345678', 'status': 'succeeded',
                                        'content': {'video_url': 'https://media.example/a.mp4'}}], MP4, 'video/mp4')
        j = mt.uppdrag('seedance', 'video', 'An abstract shape')
        self.assertEqual(mt.kor(j, 'syntetisk-las', http=h, registrera=lambda _: None)['data'], MP4)
        self.assertEqual(h.calls[0][1], mt.SEEDANCE)
        self.assertEqual(h.calls[0][2]['Authorization'], 'Bearer syntetisk-las')
        self.assertEqual(h.calls[0][3]['content'], [{'type': 'text', 'text': j['prompt']}])
        self.assertIs(h.calls[0][3]['generate_audio'], False)

    def test_parametrar_och_svarsidentitet(self):
        for params in ({'callback': 'https://some.example'}, {'duration': True}, {'duration': 16}, {'generate_audio': 'false'}):
            with self.assertRaises(mt.TransportFel):
                mt.uppdrag('seedance', 'video', 'shape', parametrar=params)
        with self.assertRaises(mt.TransportFel):
            mt.uppdrag('higgsfield', 'bild', 'shape', modell='../requests')
        h = HTTP([{'request_id': RID}, {'request_id': 'annat-id', 'status': 'completed'}])
        with self.assertRaises(mt.TransportFel):
            mt.kor(mt.uppdrag('higgsfield', 'bild', 'shape'), 'key', http=h, registrera=lambda _: None)
        h = HTTP([])
        with self.assertRaises(mt.TransportFel):
            mt.kor(mt.uppdrag('higgsfield', 'bild', 'shape'), 'key', http=h)
        self.assertEqual(h.calls, [], 'utan beständig jobbregistrering inget POST')

    def test_filkontroll_och_aterupptagning_gor_bara_get(self):
        h = HTTP(higgs()[1:]); result = mt.kor(mt.uppdrag('higgsfield', 'bild', 'shape'), 'key', http=h, befintligt=RID)
        self.assertEqual(result['ext'], '.png'); self.assertEqual([c[0] for c in h.calls], ['GET', 'FILE'])
        for url in ('http://media.example/a', 'https://user:password@media.example/a', 'https://media.example:81/a', 'https://media.example/\na'):
            self.assertFalse(mt.url_ok(url))
        for data, mime, typ in ((b'<html>error</html>', 'image/png', 'bild'), (PNG, 'text/html', 'bild'), (PNG, 'image/png', 'video')):
            with self.assertRaises(mt.TransportFel):
                mt.fil(data, mime, typ)

    def test_http_utan_omdirigering_och_feltext_utan_hemligheter(self):
        import hamta_sajt
        with patch.object(hamta_sajt, 'oppnare') as opener:
            real = mt.HTTP()
            opener.assert_called_once_with(folj=False)
        headers = Message(); headers['Content-Type'] = 'application/json'; headers['Content-Length'] = '11'

        class Response(io.BytesIO):
            status = 200

        r = Response(b'{"ok":true}'); r.headers = headers
        real.opener.open.return_value = r
        self.assertEqual(real.json(mt.GEMINI, {'x-goog-api-key': 'syntetisk'}, {'input': 'text'}), {'ok': True})
        request = real.opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(json.loads(request.data), {'input': 'text'})
        self.assertNotIn('syntetisk', request.full_url)
        real.opener.open.side_effect = urllib.error.HTTPError('https://example.org?secret=syntetiskt', 403, 'prompt hemligt', {}, io.BytesIO())
        with self.assertRaises(mt.TransportFel) as caught:
            real.json(mt.GEMINI, {})
        self.assertEqual(str(caught.exception), 'leverantörens HTTP-status 403')

    def test_pollning_slutar_vid_tidsgrans_utan_nytt_post(self):
        tid = [0.0]
        h = HTTP([{'request_id': RID}, {'request_id': RID, 'status': 'queued'}])
        with self.assertRaises(mt.TransportFel):
            mt.kor(mt.uppdrag('higgsfield', 'bild', 'shape'), 'key', http=h, timeout=1,
                   registrera=lambda _: None, clock=lambda: tid[0], sleep=lambda t: tid.__setitem__(0, tid[0] + t))
        self.assertEqual([c[0] for c in h.calls], ['POST', 'GET'])


class Kallbild(unittest.TestCase):
    """Redigering och bild till video ur registrets egna bild (GR-20261010-kompetens-integration, materialsteget)."""
    def setUp(self):
        self.no_network = patch.object(socket, 'create_connection', side_effect=AssertionError('nät är förbjudet i provet'))
        self.no_network.start(); self.addCleanup(self.no_network.stop)
        import hashlib
        self.kb = {'material': 'm001', 'version': 1, 'mime': 'image/png', 'bytes': len(PNG), 'sha256': hashlib.sha256(PNG).hexdigest()}

    def test_redigering_skickar_kallbilden_som_objekt_fore_texten(self):
        h = HTTP([gemini()]); j = mt.uppdrag('nano-banana', 'bild', 'Make the background warmer', kalla=self.kb)
        mt.kor(j, 'syntetisk', http=h, bilddata=PNG)
        inp = h.calls[0][3]['input']
        self.assertEqual(inp[0], {'type': 'image', 'data': base64.b64encode(PNG).decode(), 'mime_type': 'image/png'})
        self.assertEqual(inp[1], {'type': 'text', 'text': 'Make the background warmer'})

    def test_bild_till_video_forsta_rutan_som_data_url(self):
        h = HTTP([{'id': 'lsd-syntetisk-01'}, {'id': 'lsd-syntetisk-01', 'status': 'succeeded', 'content': {'video_url': 'https://media.example/v.mp4'}}], MP4, 'video/mp4')
        j = mt.uppdrag('seedance', 'video', 'Slow camera push', kalla=self.kb)
        mt.kor(j, 'syntetisk', http=h, bilddata=PNG, registrera=lambda _: None, sleep=lambda _: None)
        bild = [c for c in h.calls[0][3]['content'] if c['type'] == 'image_url']
        self.assertEqual(bild[0]['role'], 'first_frame')
        self.assertTrue(bild[0]['image_url']['url'].startswith('data:image/png;base64,'))

    def test_kallbilden_maste_stamma_och_higgsfield_kraver_publik_uppladdning(self):
        j = mt.uppdrag('nano-banana', 'bild', 'edit', kalla=self.kb)
        for data in (None, PNG + b'x', MP4):
            with self.assertRaises(mt.TransportFel):
                mt.kor(j, 'syntetisk', http=HTTP([gemini()]), bilddata=data)
        with self.assertRaises(mt.TransportFel):
            mt.uppdrag('higgsfield', 'video', 'motion', kalla=self.kb)
        with self.assertRaises(mt.TransportFel):
            mt.kor(mt.uppdrag('nano-banana', 'bild', 'ny'), 'syntetisk', http=HTTP([gemini()]), bilddata=PNG)

    def test_octet_stream_far_typen_ur_signaturen_och_utgangen_adress_ar_slutgiltig(self):
        self.assertEqual(mt.fil(PNG, 'application/octet-stream', 'bild')['mime'], 'image/png')
        with self.assertRaises(mt.TransportFel):
            mt.fil(PNG, 'text/html', 'bild')

        class Utgangen(HTTP):
            def las(self, url, **kwargs):
                raise mt.TransportFel('leverantörens HTTP-status 403')
        with self.assertRaises(mt.TransportFel) as fel:
            mt.kor(mt.uppdrag('higgsfield', 'bild', 'shape'), 'syntetisk', http=Utgangen(higgs()), registrera=lambda _: None)
        self.assertTrue(fel.exception.terminal)


class Bestallning(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'materialtransportens syntetiska prov'))).resolve()
        self.slug = 'prov-materialtransport'
        self.stack.enter_context(patch.multiple(atelje, UNDERLAG=self.root / 'underlag', KUNDER=self.root / 'kunder'))
        self.stack.enter_context(patch.object(material, 'HEM', self.root / 'konton'))
        self.stack.enter_context(patch.dict(os.environ, {}, clear=True))
        self.stack.enter_context(patch.object(socket, 'create_connection', side_effect=AssertionError('inget nät')))
        self.u = self.root / 'underlag' / self.slug; self.u.mkdir(parents=True)
        (self.u / 'VERKSAMHET.json').write_text(json.dumps({'namn': 'Fiktiva Testbolaget', 'adress': {'ort': 'Provorten'}}))
        material.HEM.mkdir()
        for lev in ('higgsfield', 'nano-banana', 'seedance'):
            l = material.LEVERANTORER[lev]; p = material.HEM / l['env']
            p.write_text(l['var'] + '=syntetisk-nyckel\n'); p.chmod(0o600)
        (kandidater.ksajt(self.slug, 'k01') / 'src').mkdir(parents=True)

    def bestall(self, lev='higgsfield', typ='bild', prompt='An abstract illustration of a tool'):
        return material.bestall(self.slug, prompt, typ, lev, kandidat='k01')

    def generera(self, t, h, **kwargs):
        return material.generera(self.slug, t['id'], t['versioner'][-1]['uppdrag_sha'], True, 'Syntetiskt rättighetsbelägg', http=h, **kwargs)

    def test_kallbild_ur_registret_genom_bestallning_generering_och_ko(self):
        forsta = self.generera(self.bestall('nano-banana'), HTTP([gemini()]))
        self.assertEqual(forsta['status'], 'genererad')
        with patch.object(material, 'las_nyckel', side_effect=AssertionError('beställningen får inte läsa konton')):
            red = material.bestall(self.slug, 'Warmer light on the same composition', 'bild', 'nano-banana', kandidat='k01', fran=forsta['id'])
            vid = material.bestall(self.slug, 'Slow push in', 'video', 'seedance', kandidat='k01', fran=forsta['id'] + '@v1')
        self.assertEqual(red['versioner'][-1]['bestallning']['kalla_bild']['sha256'], forsta['versioner'][-1]['sha256'])
        kon = material.ko(self.slug)['ko']
        self.assertEqual(sorted(x['id'] for x in kon), sorted([red['id'], vid['id']]))
        self.assertTrue(all(x['uppdrag_sha'] for x in kon))
        h = HTTP([gemini()]); done = self.generera(red, h)
        self.assertEqual(done['status'], 'genererad')
        self.assertEqual(h.calls[0][3]['input'][0]['type'], 'image')
        for ref, kid in (('m999', 'k01'), (forsta['id'], 'k02'), ('underlag/%s/bilder/foto.jpg' % self.slug, 'k01')):
            with self.assertRaises(ValueError):
                material.bestall(self.slug, 'edit', 'bild', 'nano-banana', kandidat=kid, fran=ref)
        with self.assertRaises(ValueError):
            material.bestall(self.slug, 'edit', 'bild', 'stubb', kandidat='k01', fran=forsta['id'])

    def test_bestallning_laser_inga_nycklar_och_hela_vagen_till_anvand(self):
        with patch.object(material, 'las_nyckel', side_effect=AssertionError('beställningen får inte läsa konton')):
            t = self.bestall()
        self.assertEqual(t['status'], 'vantar_mandat_konto')
        h = HTTP(higgs()); done = self.generera(t, h)
        self.assertEqual(done['status'], 'genererad')
        v = done['versioner'][-1]
        self.assertEqual((self.u / v['fil']).read_bytes(), PNG)
        self.assertEqual(v['sha256'], mt.fil(PNG, 'image/png', 'bild')['sha256'])
        self.assertEqual(self.generera(done, HTTP([])), done, 'samma mandat återanvänder utfallet, inget nytt POST')
        self.assertTrue(material.anvand(self.slug, t['id'], 'k01', 'hero')['ok'])
        self.assertFalse(material.anvand(self.slug, t['id'], 'k02', 'hero')['ok'])
        text = material.registerfil(self.slug).read_text()
        self.assertNotIn('syntetisk-nyckel', text); self.assertNotIn('token=syntetiskt', text)

    def test_betrodd_cli_verkstaller_exakt_sparad_bestallning(self):
        t = self.bestall('nano-banana'); h = HTTP([gemini()])
        self.assertEqual(t['status'], 'vantar_mandat_konto')
        with patch.object(mt, 'HTTP', return_value=h), contextlib.redirect_stdout(io.StringIO()) as out:
            rc = material.main([self.slug, '--generera', t['id'], '--uppdrag-sha', t['versioner'][0]['uppdrag_sha'],
                                '--godkann-kostnad', '--rattigheter', 'syntetiskt belägg'])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue())['status'], 'genererad')
        self.assertEqual(len(h.calls), 1)

    def test_nej_fore_nyckellasning_vid_mandat_identitet_och_kandidat(self):
        t = self.bestall(); sha = t['versioner'][-1]['uppdrag_sha']
        with patch.object(material, 'las_nyckel', side_effect=AssertionError('för tidig kontoläsning')):
            for args in [(sha, False, '', None), ('0' * 64, True, 'rättighet', None), (sha, True, 'rättighet', 'k01')]:
                with self.assertRaises(ValueError):
                    material.generera(self.slug, t['id'], args[0], args[1], args[2], kandidat=args[3])
            with patch.dict(os.environ, {'NWP_SLUG': self.slug}):
                with self.assertRaises(ValueError):
                    self.generera(t, HTTP([]))
            for prefix in ([self.slug, '--kandidat', 'k01'], [self.slug, '--kandidat=k01']):
                with contextlib.redirect_stdout(io.StringIO()):
                    rc = material.main(prefix + ['--generera', t['id'], '--uppdrag-sha', sha, '--godkann-kostnad', '--rattigheter', 'prov'])
                self.assertEqual(rc, 1)

    def test_kunduppgifter_och_olast_underlag_nekar_fore_nat(self):
        for prompt in ('Fiktiva Testbolaget illustration', 'illustration in Provorten', 'photo email name@example.com'):
            t = self.bestall(prompt=prompt)
            h = HTTP([])
            with self.assertRaises(ValueError):
                self.generera(t, h)
            self.assertFalse(h.calls)
        (self.u / 'VERKSAMHET.json').write_text('{')
        with self.assertRaises(ValueError):
            self.generera(self.bestall(), HTTP([]))

    def test_tidsfel_efter_submit_bevarar_jobbet_och_nytt_forsok_ar_get(self):
        t = self.bestall(); h = HTTP([{'request_id': RID}, mt.TransportFel('syntetiskt transportfel')])
        done = self.generera(t, h)
        self.assertEqual(done['status'], 'vantar_resultat')
        self.assertEqual(material.las(self.slug)['tillgangar'][t['id']]['versioner'][-1]['jobb'], RID)
        h2 = HTTP(higgs()[1:]); done = self.generera(done, h2)
        self.assertEqual(done['status'], 'genererad'); self.assertEqual([c[0] for c in h2.calls], ['GET', 'FILE'])

    def test_terminalt_fel_skickas_inte_igen(self):
        t = self.bestall(); h = HTTP([{'request_id': RID}, {'request_id': RID, 'status': 'nsfw'}])
        done = self.generera(t, h)
        self.assertEqual(done['status'], 'fel')
        with self.assertRaises(ValueError):
            self.generera(done, HTTP([]))

    def test_jobbet_ar_sparat_fore_forsta_pollningen(self):
        t = self.bestall()
        slug, tid, test = self.slug, t['id'], self

        class ObserveradHTTP(HTTP):
            def json(self, url, headers, body=None, timeout=30):
                if body is None:
                    v = material.las(slug)['tillgangar'][tid]['versioner'][-1]
                    test.assertEqual((v['jobb'], v['status']), (RID, 'vantar_resultat'))
                return super().json(url, headers, body, timeout)

        self.assertEqual(self.generera(t, ObserveradHTTP(higgs()))['status'], 'genererad')

    def test_tvetydigt_postfel_upprepas_inte_och_feltext_ar_fast(self):
        t = self.bestall('nano-banana'); done = self.generera(t, HTTP([mt.TransportFel('nyckel prompt signerad-adress')]))
        self.assertEqual(done['status'], 'oklart')
        self.assertNotIn('signerad-adress', json.dumps(done))
        with self.assertRaises(ValueError):
            self.generera(done, HTTP([]))
        new = material.bestall(self.slug, 'New abstract shape', 'bild', 'nano-banana', igen=t['id'], kandidat='k01')
        self.assertNotEqual(new['versioner'][-1]['uppdrag_sha'], t['versioner'][-1]['uppdrag_sha'])

    def test_konto_och_registerfel_ar_synliga_utan_dataforlust(self):
        t = self.bestall(); (material.HEM / 'higgsfield.env').unlink()
        self.assertEqual(self.generera(t, HTTP([]))['status'], 'saknar_konto')
        p = material.registerfil(self.slug); p.write_text('{')
        with self.assertRaises(ValueError):
            self.bestall()
        self.assertEqual(p.read_text(), '{')

    def test_lankad_materialrot_skrivs_inte(self):
        outside = self.root / 'annan'; outside.mkdir()
        (self.u / 'material').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.bestall()
        self.assertEqual(list(outside.iterdir()), [])


class Skrivmal(unittest.TestCase):
    """Verkliga mål: samma tester kan köras mot sparad material.py före rättelsen."""
    setUp = Bestallning.setUp
    def importerad(self):
        p = self.root / 'source.png'; p.write_bytes(PNG)
        return material.importera(self.slug, p, 'higgsfield', 'syntetiskt uppdrag', 'provkälla', 'provrättighet')

    def anvand_cli(self, t):
        with contextlib.redirect_stdout(io.StringIO()):
            return material.main([self.slug, '--kandidat', 'k01', '--anvand', t['id'], '--plats', 'hero'])

    def test_materialmalets_kataloglank_nekar_utan_extern_andring(self):
        t = self.importerad()
        outside = self.root / 'annan-kandidat'; outside.mkdir()
        mal = kandidater.ksajt(self.slug, 'k01') / 'src/assets/material'
        mal.parent.mkdir(); mal.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.anvand_cli(t), 1)
        self.assertEqual(list(outside.iterdir()), [])

    def test_befintligt_output_nekar_symlank_och_hardlank(self):
        for typ in ('symbolisk', 'hard'):
            t = self.importerad()
            outside = self.root / ('privat-' + typ + '.png'); outside.write_bytes(b'ORORD')
            mal = kandidater.ksajt(self.slug, 'k01') / 'src/assets/material'
            mal.mkdir(parents=True, exist_ok=True)
            f = mal / ('hero__%s-v01.png' % t['id'])
            if typ == 'hard':
                os.link(outside, f)
            else:
                f.symlink_to(outside)
            self.assertEqual(self.anvand_cli(t), 1)
            self.assertEqual(outside.read_bytes(), b'ORORD')

    def test_materialtextens_mal_nekar_lank_och_hardlank(self):
        t = self.importerad()
        outside = self.root / 'privat.md'; outside.write_text('ORORD')
        md = kandidater.kdir(self.slug, 'k01') / 'material/MATERIAL.md'
        md.parent.mkdir(parents=True)
        for typ in ('symbolisk', 'hard'):
            if typ == 'hard':
                os.link(outside, md)
            else:
                md.symlink_to(outside)
            self.assertEqual(self.anvand_cli(t), 1)
            self.assertEqual(outside.read_text(), 'ORORD')
            md.unlink()

    def test_canvas_nekar_lankad_kandidatrot_och_hardlankad_kalla(self):
        other = kandidater.kdir(self.slug, 'k02'); other.mkdir(parents=True)
        source = other / 'koncept.png'; source.write_bytes(PNG)
        own = kandidater.kdir(self.slug, 'k01')
        own.symlink_to(other, target_is_directory=True)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = material.main([self.slug, '--kandidat', 'k01', '--canvas', str(own / 'koncept.png'), '--bestall', 'prov'])
        self.assertEqual(rc, 1)
        self.assertEqual(material.las(self.slug)['tillgangar'], {})
        own.unlink(); own.mkdir()
        link = own / 'koncept.png'; os.link(source, link)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = material.main([self.slug, '--kandidat', 'k01', '--canvas', str(link), '--bestall', 'prov'])
        self.assertEqual(rc, 1)
        self.assertEqual(material.las(self.slug)['tillgangar'], {})

    def test_canvas_legitim_kandidatfil_ar_korbar(self):
        own = kandidater.kdir(self.slug, 'k01'); own.mkdir(parents=True)
        source = own / 'koncept.png'; source.write_bytes(PNG)
        with contextlib.redirect_stdout(io.StringIO()):
            rc = material.main([self.slug, '--kandidat', 'k01', '--canvas', str(source), '--bestall', 'prov'])
        self.assertEqual(rc, 0)
        t = next(iter(material.las(self.slug)['tillgangar'].values()))
        self.assertEqual(self.anvand_cli(t), 0)


if __name__ == '__main__':
    unittest.main()
