#!/usr/bin/env python3
"""Produktionsmottagarens felkontrakt i Cloudflare-Workern, enbart syntetiska fält och lokala leverantörsdubblar.

Workern hämtas ur exporten (samma fil som kundrepot får) och körs i Node mot attrapperna i worker_attrapper.mjs: D1 som
riktig SQLite med mallens migreringar, R2 som en karta och mejltjänsten som en stubbe, med felinjektion. Det riktiga
runtimeprovet i workerd är kontroller/workersprov.py."""
import contextlib
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import subprocess
import sys
import os
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister
import exportera
import driftkoll

ROOT = Path(__file__).resolve().parents[3]
NODE = Path(__file__).with_name('prov_formularfel_node.mjs')
HEMLIGT = 'SYNTETISKT-HEMLIGT'


class Formular(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-', 'syntetiskt formulärprov'))).resolve()
        sajt=self.tmp/'kunder/prov-formular/sajt';(sajt/'src/pages').mkdir(parents=True)
        (sajt/'src/pages/index.astro').write_text('<h1>Syntetiskt exportprov</h1>')
        (sajt/'package.json').write_text('{"dependencies":{}}')
        (sajt/'astro.config.mjs').write_text("import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });")
        with patch.multiple(exportera,ROOT=self.tmp,KUNDER=self.tmp/'kunder',UNDERLAG=self.tmp/'underlag'):
            res=exportera.exportera('prov-formular',bygg=False)
        self.assertTrue(res['ok'],res);self.assertFalse(res['klart_for_leverans'])
        self.ut=Path(res['ut'])
        # Samma Worker och samma schema som exporten faktiskt placerade i det syntetiska kundrepot.
        shutil.copyfile(self.ut/'worker/index.js', self.tmp/'worker.mjs')
        shutil.copytree(self.ut/'migrations', self.tmp/'migrations')

    def kor(self, mode):
        r = subprocess.run(['node','--no-warnings',str(NODE),str(self.tmp/'worker.mjs'),str(self.tmp/'migrations'),mode],
                           cwd=self.tmp,text=True,capture_output=True,timeout=30)
        self.assertEqual(r.returncode,0,r.stderr)
        return json.loads(r.stdout)

    def lagring(self, d):
        return [e[0] for e in d['events'] if e[0] in ('r2.put','d1.batch')]

    def mejl(self, d):
        return [e[1] for e in d['events'] if e[0]=='mejl']

    def sakerhet(self, d):
        for k,v in (('x-content-type-options','nosniff'),('referrer-policy','same-origin'),('x-frame-options','DENY'),('cache-control','no-store')):
            self.assertEqual(d['headers'].get(k),v,(k,d['headers']))
        self.assertIn('max-age=',d['headers'].get('strict-transport-security',''))

    def bevarat(self, d):
        import html
        self.sakerhet(d)
        self.assertIn('text/html', d['headers'].get('content-type',''))
        self.assertIn('noindex', d['headers'].get('x-robots-tag',''))
        self.assertIn("script-src 'none'", d['headers'].get('content-security-policy',''))
        self.assertNotIn('location',d['headers'])
        for k in ('namn','telefon','meddelande'):
            # Multipart använder CRLF; webbläsarens textarea visar radsluten som LF.
            self.assertIn(html.escape(d['values'][k],quote=True),d['html'].replace('\r\n','\n'))
        self.assertNotIn('<script>',d['html'])
        self.assertIn('action="/api/forfragan/"',d['html'])
        self.assertIn('method="post"',d['html'])
        # samma inskick följer med felvyn, så att ett nytt försök blir samma ärende
        self.assertIn('name="inskick" value="%s"' % d['values']['inskick'],d['html'])
        self.assertNotIn(HEMLIGT,d['html']+json.dumps(d['headers']))

    def test_serverfel_bevarar_falt_utan_url_eller_javascript(self):
        d=self.kor('validering'); self.assertEqual(d['status'],422); self.bevarat(d)
        self.assertIn('aria-invalid="true"',d['html']); self.assertIn('href="#telefon"',d['html'])
        self.assertEqual(d['events'],[])

    def test_ogiltigt_inskicks_id_aterges_inte(self):
        d=self.kor('ogiltigt-inskick'); self.assertEqual(d['status'],422)
        self.assertNotIn('name="inskick"',d['html']); self.assertNotIn('<script>x',d['html'])

    def test_bilagefel_bevarar_text_och_anger_att_bilden_maste_valjas_igen(self):
        for mode,status in [('bildtyp',422),('bildstor',413)]:
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],status);self.bevarat(d)
                self.assertIn('Välj bilden igen',d['html']);self.assertEqual(d['events'],[])

    def test_telefonen_foljer_samma_teckenregel_som_formularet(self):
        d=self.kor('telefon');self.assertEqual(d['status'],422);self.bevarat(d)
        self.assertEqual(d['events'],[])

    def test_utan_lagringskvitto_skickas_aldrig_mejl(self):
        # D1 faller, D1 saknas i produktionen, R2 faller eller ger ett kvitto som inte gäller bilagan
        for mode in ('lagerfel','ingetlager','r2fel','r2kvitto','r2tomt'):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],503);self.bevarat(d)
                self.assertEqual(d['headers']['x-forfragan'],'fel')
                self.assertEqual(self.mejl(d),[]);self.assertEqual(d['rader'],[])
                self.assertIn('inte bekräfta',d['html'])
                self.assertEqual(d['r2'],[],'ingen bilaga blir kvar utan ärende efter ett uttryckligt fel')
                self.assertNotIn(HEMLIGT,json.dumps(d['logs']))
        self.assertTrue(any('D1' in l for l in self.kor('ingetlager')['logs']),'en saknad bindning syns i loggen')

    def test_sparat_vid_mejlfel_far_eget_mottaget_besked_utan_omskick(self):
        for mode,status in (('mejlfel','fel'),('mejlkast','fel'),('ingenmottagare','vantar')):
            with self.subTest(mode=mode):
                # 303 till den förrenderade /mottagen/, aldrig en sida på POST-adressen (GR-20261008-r117-claude#D1)
                d=self.kor(mode);self.assertEqual(d['status'],303);self.sakerhet(d)
                self.assertEqual(d['headers']['location'],'/mottagen/');self.assertEqual(d['headers']['x-forfragan'],'sparad')
                self.assertEqual(d['html'],'')
                self.assertEqual(self.lagring(d),['d1.batch'])
                self.assertEqual([r['status'] for r in d['rader']],[status])
                self.assertNotIn(HEMLIGT,json.dumps(d['logs'])+json.dumps(d['headers'])+json.dumps(d['rader']),'leverantörens feltext når varken loggen eller utkorgen')
        # samma inskick igen efter ett mejlfel: samma ärende, inget nytt mejl
        d=self.kor('mejlfel');self.assertEqual(len(d['rader']),1);self.assertEqual(len(self.mejl(d)),1)
        self.assertEqual([(s['status'],s['headers'].get('location'),s['headers'].get('x-forfragan')) for s in d['svar']],
                         [(303,'/mottagen/','sparad'),(303,'/mottagen/','dubblett')])

    def test_ogiltigt_mejlkvitto_ar_inte_bekraftad_mejlacceptans(self):
        for mode in ('tomtmejlkvitto','felmejlkvitto','htmlmejlkvitto'):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],303)
                self.assertEqual(d['headers']['location'],'/mottagen/');self.assertEqual(d['headers']['x-forfragan'],'sparad')
                self.assertEqual(d['rader'][0]['status'],'fel');self.assertIsNone(d['rader'][0]['mejl_id'])

    def test_bilagan_tas_bort_nar_arendet_inte_kunde_sparas(self):
        # bilagan lagras före ärendet; faller den skrivningen är bilden annars föräldralös (GR-20261008-r117-claude#D7)
        d=self.kor('jsonfel');self.assertEqual(d['status'],503);self.assertEqual(self.mejl(d),[])
        raderingar=[e[1] for e in d['events'] if e[0]=='r2.delete']
        lagrade=[e[1] for e in d['events'] if e[0]=='r2.put']
        self.assertEqual(len(raderingar),1);self.assertEqual(raderingar,lagrade);self.assertTrue(raderingar[0].endswith('/bilaga'))
        self.assertEqual(d['r2'],[]);self.assertEqual(d['rader'],[])
        self.assertNotIn(HEMLIGT,json.dumps(d['logs'])+d['html'])
        d=self.kor('jsonfel-raderfel');self.assertEqual(d['status'],503)
        self.assertTrue(any('bilagan kunde inte tas bort' in l for l in d['logs']),d['logs'])
        self.assertNotIn(HEMLIGT,json.dumps(d['logs'])+d['html'])
        d=self.kor('lagerfel');self.assertFalse(any(e[0]=='r2.delete' for e in d['events']),'utan lagrad bilaga raderas inget')

    def test_fungerande_sandning_kommer_efter_varaktigt_arende(self):
        d=self.kor('giltig');self.assertEqual(d['status'],303);self.sakerhet(d)
        self.assertEqual(d['headers']['location'],'/tack/');self.assertEqual(d['headers']['x-forfragan'],'skickad')
        # ärendet och utkorgen först, avsikten ("skickar") före nätanropet, sedan kvittot
        self.assertEqual([e[0] if e[0]!='d1.run' else 'utkorg:'+e[1] for e in d['events'] if e[0]!='d1.first'],
                         ['d1.batch','utkorg:skickar','mejl','utkorg:accepterad'])
        rad=d['rader'][0]
        self.assertEqual((rad['status'],rad['forsok'],rad['mejl_id']),('accepterad',1,'00000000-0000-4000-8000-000000000001'))
        self.assertEqual(self.mejl(d)[0]['idempotens'],'forfragan-'+rad['id'],'mejlet bär ärendets id som idempotensnyckel')
        self.assertEqual(rad['nyckel'],'i:'+d['values']['inskick'])
        self.assertEqual(rad['meddelande'],d['values']['meddelande']);self.assertEqual(rad['namn'],d['values']['namn'])
        mottagen=datetime.fromisoformat(rad['mottagen'].replace('Z','+00:00'))
        self.assertEqual(datetime.fromisoformat(rad['gallras'].replace('Z','+00:00'))-mottagen,timedelta(days=30))

    def test_bilagan_lagras_privat_under_arendets_nyckel(self):
        for mode,namn in (('giltig-bild','syntetisk.jpg'),('filnamn','bilaga')):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],303);self.assertEqual(d['headers']['x-forfragan'],'skickad')
                rad=d['rader'][0]
                nyckel='forfragningar/%s/%s/bilaga' % (rad['mottagen'][:10],rad['id'])
                self.assertEqual([k for k,_ in d['r2']],[nyckel],'klientens filnamn styr aldrig lagringsnamnet')
                self.assertEqual(d['r2'][0][1]['meta'],{'forfragan':rad['id']})
                self.assertEqual((rad['bilaga'],rad['bilaga_namn']),(nyckel,namn))
                self.assertEqual(self.mejl(d)[0]['bilagor'],[namn])

    def test_lokala_frister_avbryter_och_forhindrar_sena_foljdsteg(self):
        d=self.kor('langsam-r2');self.assertEqual(d['status'],503);self.bevarat(d)
        self.assertNotIn('d1.batch',self.lagring(d));self.assertEqual(self.mejl(d),[])
        # ärendet bekräftas inte inom fristen men blir klart senare: bilagan står kvar (ärendet pekar på den), inget mejl, och
        # samma inskick igen blir samma ärende, sparat men inte aviserat
        d=self.kor('langsam-batch');self.assertEqual(d['status'],503);self.assertEqual(self.mejl(d),[])
        self.assertFalse(any(e[0]=='r2.delete' for e in d['events']))
        self.assertEqual([r['status'] for r in d['rader']],['vantar']);self.assertEqual(len(d['r2']),1)
        self.assertEqual(d['r2'][0][0],d['rader'][0]['bilaga'])
        self.assertEqual((d['svar'][1]['status'],d['svar'][1]['headers']['location'],d['svar'][1]['headers']['x-forfragan']),(303,'/mottagen/','dubblett'))
        for mode in ('langsam-mejl','langsam-json'):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],303);self.assertEqual(d['headers']['location'],'/mottagen/')
                self.assertIn(['avbrutet','mejl'],d['events']);self.assertEqual(len(self.mejl(d)),1)
                self.assertEqual(d['rader'][0]['status'],'fel')
        # utkorgens avsikt bekräftas inte: inget mejl i blindo
        d=self.kor('langsam-utkorg');self.assertEqual(d['status'],303);self.assertEqual(d['headers']['location'],'/mottagen/')
        self.assertEqual(self.mejl(d),[])
        # en långsam kontroll av tidigare inskick stoppar inte förfrågan
        d=self.kor('langsam-kontroll');self.assertEqual((d['status'],d['headers']['x-forfragan']),(303,'skickad'))

    def test_demo_och_honeypot_ar_uttryckliga_utan_lagring_eller_sandning(self):
        for mode,utfall in [('demo','demo'),('honeypot','honeypot'),('snabb','honeypot')]:
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],303);self.assertEqual(d['headers']['location'],'/tack/')
                self.assertEqual(d['headers']['x-forfragan'],utfall);self.assertEqual(d['events'],[]);self.assertEqual(d['rader'],[])

    def test_olasbar_och_overstor_kropp_lovar_inte_bevarade_falt(self):
        for mode,status in [('olast',400),('forstor',413)]:
            d=self.kor(mode);self.assertEqual(d['status'],status);self.assertEqual(d['events'],[])
            self.assertIn('kunde inte läsa',d['html']);self.assertNotIn('texten finns kvar',d['html'])

    def test_metod_vag_och_ursprung(self):
        for mode,status,plats in [('metod',405,None),('utan-snedstreck',308,'/api/forfragan/'),('annan-api',404,None),('origin',403,None)]:
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],status);self.assertEqual(d['headers'].get('location'),plats)
                self.assertEqual(d['events'],[]);self.sakerhet(d)
        self.assertEqual(self.kor('metod')['headers'].get('allow'),'POST')
        self.assertEqual(self.kor('cross-site')['status'],403,'Sec-Fetch-Site cross-site nekas också med rätt Origin')
        d=self.kor('origin-null');self.assertEqual((d['status'],d['headers'].get('x-forfragan')),(303,'skickad'),'samma webbplats med "Origin: null" tas emot')
        d=self.kor('sida');self.assertEqual(d['status'],200);self.assertNotIn('x-robots-tag',d['headers'],'produktionens sidor indexeras')

    def test_strommen_mats_ocksa_utan_eller_med_felaktig_langd(self):
        for mode in ('strom','falsklangd'):
            d=self.kor(mode);self.assertEqual(d['status'],413);self.assertEqual(d['events'],[])
            self.assertIn('kunde inte läsa hela',d['html'])

    def test_lang_text_med_radslut_som_ryms_i_formularet_godtas(self):
        d=self.kor('langtext');self.assertEqual(d['status'],303)
        self.assertEqual(d['rader'][0]['meddelande'],d['values']['meddelande'])

    def test_samma_inskick_blir_ett_arende(self):
        d=self.kor('dubblett-inskick')
        self.assertEqual([(s['status'],s['headers'].get('location'),s['headers'].get('x-forfragan')) for s in d['svar']],
                         [(303,'/tack/','skickad'),(303,'/tack/','dubblett')])
        self.assertEqual(len(d['rader']),1);self.assertEqual(len(self.mejl(d)),1)
        # utan inskicks-id (ingen JavaScript): samma innehåll inom fönstret är samma ärende, annat innehåll ett nytt
        d=self.kor('dubblett-innehall')
        self.assertEqual([s['headers'].get('x-forfragan') for s in d['svar']],['skickad','dubblett','skickad'])
        self.assertEqual(len(d['rader']),2);self.assertTrue(all(r['nyckel'].startswith('h:') for r in d['rader']))
        # över en fönstergräns är det fortfarande samma ärende; efter 25 minuter ett nytt
        for mode,vantat in (('fonstergrans',['skickad','dubblett']),('nytt-fonster',['skickad','skickad'])):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual([s['headers'].get('x-forfragan') for s in d['svar']],vantat)
        # två samtidiga inskick med samma id: ett ärende, ett mejl
        d=self.kor('samtidigt')
        self.assertEqual(sorted(s['headers'].get('x-forfragan') for s in d['svar']),['dubblett','skickad'])
        self.assertEqual(len(d['rader']),1);self.assertEqual(len(self.mejl(d)),1)

    def test_exporten_bar_workern_schemat_och_mottagen_sidan(self):
        ut=self.ut
        self.assertTrue((ut/'src/pages/mottagen.astro').is_file() and (ut/'src/pages/fel.astro').is_file())
        self.assertIn('noindex',(ut/'src/pages/mottagen.astro').read_text(encoding='utf-8'))
        self.assertNotIn('vercel',(ut/'astro.config.mjs').read_text(encoding='utf-8').lower(),'sidorna förblir förrenderade, ingen adapter')
        self.assertFalse((ut/'vercel.json').exists() or (ut/'src/pages/api').exists())
        w=(ut/'wrangler.jsonc').read_text(encoding='utf-8')
        self.assertIn('"kund-prov-formular"',w);self.assertIn('"kund-prov-formular-forhandsvisning"',w)
        self.assertTrue((ut/'migrations/0001_forfragningar.sql').is_file() and (ut/'public/_headers').is_file())

    def test_driftkoll_kraver_felvy_och_skickar_inte_giltigt_i_produktion(self):
        for brist in (None,'gammal303','ingen-text','cache'):
            svar=[(200,{k:'syntetiskt' for k in driftkoll.SAKERHET},b'<h1>Prov</h1>'),
                  (200,{},b'User-agent: *'),(200,{},b'<urlset/>'),
                  (303,{'location':'/tack/'},b'')]
            for i in range(3):
                headers={'content-type':'text/html','cache-control':'no-store','x-robots-tag':'noindex',
                         'x-forfragan':'ofullstandig' if i==0 else 'for-stor'}
                kropp='Driftkoll Prov av formuläret '+('' if i==0 else '0700000000')
                status=422 if i==0 else 413
                if i==0 and brist=='gammal303':status=303;headers['location']='/kontakt/?saknas=1'
                if i==0 and brist=='ingen-text':kropp='Rätta formuläret'
                if i==0 and brist=='cache':headers['cache-control']='public'
                svar.append((status,headers,kropp.encode()))
            svar.append((403,{},b''))
            with patch.object(driftkoll,'hamta',side_effect=svar) as hamta, patch.object(driftkoll.os,'urandom',side_effect=lambda n:b'x'*n):
                ut=driftkoll.kontroll('https://example.invalid','produktion',formular=True)
            self.assertEqual(all(ok for ok,_ in ut),brist is None,(brist,ut))
            post=[c for c in hamta.call_args_list if len(c.args)>1 and c.args[1]=='POST']
            self.assertEqual(len(post),5)
            self.assertEqual(len(hamta.call_args_list),8)

    def test_driftkoll_provar_forhandsvisningen_bakom_access(self):
        access={'cf-access-client-id':'ID-SYNTETISK-01.access','cf-access-client-secret':'SYNTETISK-HEMLIGHET-0001'}
        sak={k:'syntetiskt' for k in driftkoll.SAKERHET}
        html={'content-type':'text/html','cache-control':'no-store','x-robots-tag':'noindex'}
        kropp='Driftkoll 0700000000 Prov av formuläret'.encode()
        till_access={'location':'https://nortropic.cloudflareaccess.com/cdn-cgi/access/login/x'}
        # (svaret utan behörighet, startsidans X-Robots-Tag, väntat utfall): skyddad och noindex; öppen; utan noindex
        for skydd,robots,vantat in (((302,till_access),'noindex, nofollow',True),((200,{}),'noindex, nofollow',False),((302,till_access),None,False)):
            svar=[(skydd[0],skydd[1],b''),
                  (200,dict(sak,**({'x-robots-tag':robots} if robots else {})),b'<h1>Prov</h1>'),
                  (303,{'location':'/tack/'},b''),
                  (422,dict(html,**{'x-forfragan':'ofullstandig'}),kropp),
                  (413,dict(html,**{'x-forfragan':'for-stor'}),kropp),
                  (413,dict(html,**{'x-forfragan':'for-stor'}),b''),
                  (403,{},b''),
                  (303,{'location':'/tack/','x-forfragan':'demo'},b'')]
            with patch.object(driftkoll,'hamta',side_effect=svar) as hamta, patch.object(driftkoll.os,'urandom',side_effect=lambda n:b'x'*n):
                ut=driftkoll.kontroll('https://kund-x-forhandsvisning.nortropic.workers.dev','forhandsvisning',formular=True,access=access)
            self.assertEqual(len(hamta.call_args_list),8);self.assertEqual(ut[0][0],skydd[0]==302,ut);self.assertEqual(all(ok for ok,_ in ut),vantat,ut)
            self.assertNotIn('cf-access-client-secret',json.dumps(hamta.call_args_list[0].kwargs)+json.dumps([str(a) for a in hamta.call_args_list[0].args]),
                             'skyddet prövas först utan behörighet')
            for c in hamta.call_args_list[1:]:
                huv=c.kwargs.get('huvuden') or (c.args[2] if len(c.args)>2 else {})
                self.assertEqual(huv.get('cf-access-client-secret'),access['cf-access-client-secret'],'behörigheten följer varje anrop efter skyddsprovet')
            self.assertNotIn(access['cf-access-client-secret'],json.dumps(ut),'hemligheten skrivs aldrig ut')
        # utan behörighet prövas varken sidan eller formuläret
        with patch.object(driftkoll,'hamta',side_effect=[(302,{'location':'https://nortropic.cloudflareaccess.com/x'},b'')]):
            ut=driftkoll.kontroll('https://kund-x-forhandsvisning.nortropic.workers.dev','forhandsvisning',formular=True)
        self.assertEqual([ok for ok,_ in ut],[True,False])

    def test_access_filen_ar_privat_och_bar_bada_raderna(self):
        mapp=self.tmp/'access';mapp.mkdir()
        f=mapp/'access.env';f.write_text('# servicetoken\nCF-Access-Client-Id: ID-SYNTETISK-01.access\nCF-Access-Client-Secret: SYNTETISK-HEMLIGHET-0001\n')
        f.chmod(0o644)
        with self.assertRaises(ValueError):driftkoll.las_access(f)
        f.chmod(0o600)
        self.assertEqual(driftkoll.las_access(f),{'cf-access-client-id':'ID-SYNTETISK-01.access','cf-access-client-secret':'SYNTETISK-HEMLIGHET-0001'})
        f.write_text('CF-Access-Client-Id: ID-SYNTETISK-01.access\n');f.chmod(0o600)
        with self.assertRaises(ValueError):driftkoll.las_access(f)

    @unittest.skipUnless(os.environ.get('NWP_FORMULAR_WEBB')=='1','körs i rökprovet med Chromium')
    def test_riktig_webblasare_utan_js_och_tillgangliga_fel(self):
        r=subprocess.run(['node',str(Path(__file__).with_name('prov_formularfel_webb.mjs')),str(self.tmp),str(ROOT),
                          os.environ.get('NWP_FORMULAR_PROVBILDER','')],capture_output=True,text=True,timeout=90)
        print(r.stdout,end='');self.assertEqual(r.returncode,0,r.stderr)


if __name__=='__main__':unittest.main()
