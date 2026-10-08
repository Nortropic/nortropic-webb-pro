#!/usr/bin/env python3
"""Produktionsmottagarens felkontrakt, enbart syntetiska fält och lokala leverantörsdubblar."""
import contextlib
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
BLOB = '''export async function put(pathname, body, options) {
  globalThis.skrivna ??= new Set();
  globalThis.events.push(['lagring', pathname, options.access, typeof body==='string' ? JSON.parse(body) : null]);
  if (globalThis.skrivna.has(pathname) && !options.allowOverwrite) throw new Error('Finns redan');
  globalThis.skrivna.add(pathname);
  if (globalThis.langsam === 'lagring' || globalThis.langsam === 'kvittot' && pathname.endsWith('/avisering.json')) {
    options.abortSignal?.addEventListener('abort',()=>globalThis.events.push(['avbrutet','lagring']));
    await new Promise(resolve=>globalThis.verkligTimer(resolve,80));
  }
  if (globalThis.kvittolagring && pathname.endsWith('/avisering.json')) throw new Error('SYNTETISKT-HEMLIGT kvittofel');
  if (globalThis.lagerfel) throw new Error('SYNTETISKT-HEMLIGT lagringsfel');
  if (globalThis.tomtkvitto) return {};
  if (globalThis.felkvitto === 'blankt') return {pathname:'   '};
  if (globalThis.felkvitto === 'annan') return {pathname:'annan/forfragan.json'};
  return { pathname };
}'''
NODE = r'''import { POST, ALL } from './forfragan.mjs';
const mode = process.argv[2];
for (const k of ['VERCEL_ENV','RESEND_API_KEY','FORFRAGAN_FRAN','FORFRAGAN_TILL','BLOB_STORE_ID','BLOB_READ_WRITE_TOKEN']) delete process.env[k];
Object.assign(process.env, {VERCEL_ENV:'production',RESEND_API_KEY:'syntetisk',FORFRAGAN_FRAN:'test@example.invalid',FORFRAGAN_TILL:'test@example.invalid',BLOB_STORE_ID:'syntetiskt'});
globalThis.verkligTimer = setTimeout;
globalThis.setTimeout = (fn,ms,...args) => verkligTimer(fn,[10000,8000,2000].includes(ms)?20:ms,...args);
globalThis.langsam = mode.startsWith('langsam-') ? mode.slice(8) : null;
globalThis.skrivna = new Set();
globalThis.events = []; globalThis.lagerfel = mode === 'lagerfel'; globalThis.tomtkvitto = mode === 'tomtkvitto';
globalThis.kvittolagring = mode === 'kvittolagring';
globalThis.felkvitto = mode === 'blanktkvitto' ? 'blankt' : mode === 'annatkvitto' || mode === 'annanbild' ? 'annan' : null;
const logs = []; console.error = (...x) => logs.push(x.join(' '));
globalThis.fetch = async (url, opts) => {
  if (url !== 'https://api.resend.com/emails') throw new Error('Förbjudet nät i provet');
  events.push(['mejl', JSON.parse(opts.body)]);
  if (langsam === 'mejl' || langsam === 'json') {
    opts.signal?.addEventListener('abort',()=>events.push(['avbrutet','mejl']));
    if (langsam === 'mejl') await new Promise(resolve=>verkligTimer(resolve,80));
    return {ok:true,json:async()=>{if(langsam==='json') await new Promise(resolve=>verkligTimer(resolve,80));return {id:'prov-id'};}};
  }
  if (mode === 'mejlkast') throw new Error('SYNTETISKT-HEMLIGT transportfel');
  const body = mode === 'tomtmejlkvitto' ? '{}' : mode === 'felmejlkvitto' ? '{"error":"fel"}' : mode === 'htmlmejlkvitto' ? '<html>ok</html>' : '{"id":"00000000-0000-4000-8000-000000000001"}';
  return new Response(body,{status: mode === 'mejlfel' ? 500 : 200});
};
const values = {namn:'Syntetisk <text> & "citat"', telefon:'0700000000', meddelande:'Rad ett\n</textarea><script>globalThis.xss=true</script>', fylltid:'9000'};
if (mode === 'validering') values.telefon = '';
if (mode === 'telefon') values.telefon = 'ring ABC123';
if (mode === 'langtext') values.meddelande = 'x\n'.repeat(1999)+'xx';
if (mode === 'honeypot') values.webbplats = 'falla';
if (mode === 'ingetlager') delete process.env.BLOB_STORE_ID;
if (mode === 'ingenmottagare') delete process.env.RESEND_API_KEY;
if (mode === 'demo') { process.env.VERCEL_ENV = 'preview'; delete process.env.RESEND_API_KEY; }
if (mode === 'preview-konfigurerad') process.env.VERCEL_ENV = 'preview';  // variablerna gäller alla miljöer (GR-20261008-r117-claude#D2)
const fd = new FormData(); for (const [k,v] of Object.entries(values)) fd.append(k,v);
if (mode === 'bildtyp') fd.append('bild',new Blob(['<svg/>'],{type:'image/svg+xml'}),'syntetisk.svg');
if (mode === 'bildstor') fd.append('bild',new Blob([new Uint8Array(4000001)],{type:'image/jpeg'}),'syntetisk.jpg');
if (mode === 'annanbild' || mode === 'langsam-lagring') fd.append('bild',new Blob(['syntetiskt'],{type:'image/jpeg'}),'syntetisk.jpg');
if (mode === 'filnamn-mottagning' || mode === 'filnamn-avisering') fd.append('bild',new Blob(['syntetisk bild'],{type:'image/png'}),mode === 'filnamn-mottagning' ? 'forfragan.json' : 'avisering.json');
let req = new Request('https://example.invalid/api/forfragan/', {method:'POST',body:fd});
if (mode === 'olast') req = new Request(req.url,{method:'POST',body:'x',headers:{'content-type':'multipart/form-data; boundary=saknas'}});
if (mode === 'forstor') req = new Request(req.url,{method:'POST',body:'x',headers:{'content-length':'5000000'}});
if (mode === 'strom' || mode === 'falsklangd') req = new Request(req.url,{method:'POST',body:'x'.repeat(4400001),headers:mode==='falsklangd'?{'content-length':'1'}:{}});
const r = mode === 'metod' ? ALL() : await POST({request:req});
if(langsam) await new Promise(resolve=>verkligTimer(resolve,120));
console.log(JSON.stringify({status:r.status,headers:Object.fromEntries(r.headers),html:await r.text(),events,logs,values}));
'''


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
        # Samma endpoint som exporten faktiskt placerade i det syntetiska kundrepot.
        shutil.copyfile(Path(res['ut'])/'src/pages/api/forfragan.js', self.tmp/'forfragan.mjs')
        blob = self.tmp/'node_modules/@vercel/blob'; blob.mkdir(parents=True)
        (blob/'package.json').write_text('{"type":"module","main":"index.js"}')
        (blob/'index.js').write_text(BLOB)
        (self.tmp/'prov.mjs').write_text(NODE)

    def kor(self, mode):
        r = subprocess.run(['node','prov.mjs',mode],cwd=self.tmp,text=True,capture_output=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr)
        return json.loads(r.stdout)

    def bevarat(self, d):
        import html
        self.assertIn('text/html', d['headers'].get('content-type',''))
        self.assertEqual(d['headers'].get('cache-control'), 'no-store')
        self.assertIn('noindex', d['headers'].get('x-robots-tag',''))
        self.assertEqual(d['headers'].get('referrer-policy'),'no-referrer')
        self.assertNotIn('location',d['headers'])
        for k in ('namn','telefon','meddelande'):
            # Multipart använder CRLF; webbläsarens textarea visar radsluten som LF.
            self.assertIn(html.escape(d['values'][k],quote=True),d['html'].replace('\r\n','\n'))
        self.assertNotIn('<script>',d['html'])
        self.assertIn('action="/api/forfragan/"',d['html'])
        self.assertIn('method="post"',d['html'])

    def test_serverfel_bevarar_falt_utan_url_eller_javascript(self):
        d=self.kor('validering'); self.assertEqual(d['status'],422); self.bevarat(d)
        self.assertIn('aria-invalid="true"',d['html']); self.assertIn('href="#telefon"',d['html'])
        self.assertEqual(d['events'],[])

    def test_bilagefel_bevarar_text_och_anger_att_bilden_maste_valjas_igen(self):
        for mode,status in [('bildtyp',422),('bildstor',413)]:
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],status);self.bevarat(d)
                self.assertIn('Välj bilden igen',d['html']);self.assertEqual(d['events'],[])

    def test_telefonen_foljer_samma_teckenregel_som_formularet(self):
        d=self.kor('telefon');self.assertEqual(d['status'],422);self.bevarat(d)
        self.assertEqual(d['events'],[])

    def test_utan_lagringskvitto_skickas_aldig_mejl(self):
        for mode in ('lagerfel','ingetlager','tomtkvitto'):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],503);self.bevarat(d)
                self.assertEqual(d['headers']['x-forfragan'],'fel')
                self.assertFalse(any(x[0]=='mejl' for x in d['events']))
                self.assertIn('inte bekräfta',d['html'])

    def test_sparat_vid_mejlfel_far_eget_mottaget_besked_utan_omskick(self):
        for mode in ('mejlfel','mejlkast','ingenmottagare'):
            with self.subTest(mode=mode):
                d=self.kor(mode);self.assertEqual(d['status'],202)
                self.assertEqual(d['headers']['x-forfragan'],'sparad')
                self.assertIn('Förfrågan är mottagen',d['html']);self.assertNotIn('<form',d['html'])
                self.assertIn('inte skicka',d['html']);self.assertEqual(d['events'][0][0],'lagring')
                self.assertNotIn('SYNTETISKT-HEMLIGT',json.dumps(d['logs'])+d['html']+json.dumps(d['headers']))

    def test_lagringskvittot_maste_galla_den_faktiska_filen(self):
        for mode in ('blanktkvitto','annatkvitto','annanbild'):
            d=self.kor(mode);self.assertEqual(d['status'],503)
            self.assertFalse(any(x[0]=='mejl' for x in d['events']))

    def test_ogiltigt_mejlkvitto_ar_inte_bekraftad_mejlacceptans(self):
        for mode in ('tomtmejlkvitto','felmejlkvitto','htmlmejlkvitto'):
            d=self.kor(mode);self.assertEqual(d['status'],202)
            self.assertEqual(d['headers']['x-forfragan'],'sparad')

    def test_fungerande_sandning_kommer_efter_varaktigt_kvitto(self):
        d=self.kor('giltig');self.assertEqual(d['status'],303)
        self.assertEqual(d['headers']['location'],'/tack/')
        self.assertEqual([e[0] for e in d['events']],['lagring','mejl','lagring'])
        self.assertEqual(d['events'][0][3]['avisering'],'inte_bekraftad')
        self.assertTrue(d['events'][2][1].endswith('/avisering.json'))
        self.assertEqual(d['events'][2][3]['mottagningsfil'],d['events'][0][1])
        self.assertEqual(d['events'][2][3]['utfall'],'accepterat_av_mejltjansten')

    def test_mottagningsfilen_stodjer_uppfoljning_utan_falskt_mejlbesked(self):
        d=self.kor('mejlfel');self.assertEqual(d['events'][0][3]['avisering'],'inte_bekraftad')
        self.assertFalse(any(x[0]=='lagring' and x[1].endswith('/avisering.json') for x in d['events']))
        d=self.kor('kvittolagring');self.assertEqual(d['status'],303)
        self.assertEqual(d['events'][0][3]['avisering'],'inte_bekraftad')
        self.assertNotIn('SYNTETISKT-HEMLIGT',json.dumps(d['logs']))

    def test_bilagans_filnamn_kan_inte_kollidera_med_kvittona(self):
        for mode in ('filnamn-mottagning','filnamn-avisering'):
            d=self.kor(mode);self.assertEqual(d['status'],303)
            skriv=[e for e in d['events'] if e[0]=='lagring']
            self.assertEqual(len({e[1] for e in skriv}),3)
            self.assertIsNone(skriv[0][3]);self.assertEqual(skriv[1][3]['bild'],skriv[0][1])
            self.assertEqual(skriv[2][3]['utfall'],'accepterat_av_mejltjansten')

    def test_lokala_deadliner_avbryter_anrop_och_forhindrar_sena_foljdsteg(self):
        for mode,status,antal_mejl,antal_put in [('lagring',503,0,1),('mejl',202,1,1),('json',202,1,1),('kvittot',303,1,2)]:
            with self.subTest(mode=mode):
                d=self.kor('langsam-'+mode);self.assertEqual(d['status'],status)
                self.assertTrue(any(e[0]=='avbrutet' for e in d['events']),d['events'])
                self.assertEqual(sum(e[0]=='mejl' for e in d['events']),antal_mejl)
                self.assertEqual(sum(e[0]=='lagring' for e in d['events']),antal_put)
                if status==503:self.bevarat(d)
                if status==202:self.assertNotIn('<form',d['html'])

    def test_demo_och_honeypot_ar_uttryckliga_utan_sandning(self):
        for mode,utfall in [('demo','demo'),('honeypot','honeypot'),('preview-konfigurerad','demo')]:
            d=self.kor(mode);self.assertEqual(d['status'],303)
            self.assertEqual(d['headers']['x-forfragan'],utfall);self.assertEqual(d['events'],[])

    def test_olasbar_och_overstor_kropp_lovar_inte_bevarade_falt(self):
        for mode,status in [('olast',400),('forstor',413)]:
            d=self.kor(mode);self.assertEqual(d['status'],status);self.assertEqual(d['events'],[])
            self.assertIn('kunde inte läsa',d['html']);self.assertNotIn('texten finns kvar',d['html'])
            self.assertNotIn('SYNTETISKT-HEMLIGT',d['html'])

    def test_annan_metod_nekas(self):
        d=self.kor('metod');self.assertEqual(d['status'],405);self.assertEqual(d['events'],[])

    def test_strommen_mats_ocksa_utan_eller_med_felaktig_langd(self):
        for mode in ('strom','falsklangd'):
            d=self.kor(mode);self.assertEqual(d['status'],413);self.assertEqual(d['events'],[])
            self.assertIn('kunde inte läsa hela',d['html'])

    def test_lang_text_med_radslut_som_ryms_i_formularet_godtas(self):
        d=self.kor('langtext');self.assertEqual(d['status'],303)
        self.assertEqual(d['events'][0][3]['meddelande'],d['values']['meddelande'])

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

    @unittest.skipUnless(os.environ.get('NWP_FORMULAR_WEBB')=='1','körs i rökprovet med Chromium')
    def test_riktig_webblasare_utan_js_och_tillgangliga_fel(self):
        r=subprocess.run(['node',str(Path(__file__).with_name('prov_formularfel_webb.mjs')),str(self.tmp),str(ROOT),
                          os.environ.get('NWP_FORMULAR_PROVBILDER','')],capture_output=True,text=True,timeout=90)
        print(r.stdout,end='');self.assertEqual(r.returncode,0,r.stderr)


if __name__=='__main__':unittest.main()
