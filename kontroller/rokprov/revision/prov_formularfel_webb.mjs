// Riktig HTTP och Chromium mot kundsajtens Worker ur exporten (D1 som SQLite, R2 och mejltjänsten som attrapper:
// worker_attrapper.mjs), ingen faktisk leverantör. Endast syntetiska fält.
import assert from 'node:assert/strict';
import http from 'node:http';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync } from 'node:fs';
import { d1, r2 } from './worker_attrapper.mjs';
const [kopian, root, bilder] = process.argv.slice(2);
const require = createRequire(root + '/kontroller/package.json');
const { chromium } = require('playwright');
const axe = readFileSync(require.resolve('axe-core/axe.min.js'),'utf8');
const { default: worker } = await import(pathToFileURL(kopian + '/worker.mjs'));
const events = [];
let mode = 'ok';
const DB = d1(kopian + '/migrations', async (vad) => { if (vad === 'd1.batch' && mode === 'lagerfel') throw new Error('syntetiskt lagringsfel'); });
// Workern skickar aldrig till Resend från localhost; provets mejltjänst är en lokal adress (attrappen nedan svarar)
const MEJL = 'http://127.0.0.1:9/emails';
globalThis.fetch = async (url) => {
  assert.equal(url,MEJL);
  events.push(['mejl']);
  return new Response('{"id":"00000000-0000-4000-8000-000000000001"}',{status:mode === 'mejlfel' ? 422 : 200});  // nekat: fel i utkorgen
};
const start = '<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Syntetiskt formulärprov</title></head><body><main><h1>Provformulär</h1><form action="/api/forfragan/" method="post" enctype="multipart/form-data"><label for="namn">Namn</label><input id="namn" name="namn" required><label for="telefon">Telefon</label><input id="telefon" name="telefon" type="tel" required><label for="meddelande">Meddelande</label><textarea id="meddelande" name="meddelande" required></textarea><label for="bild">Bild (valfritt)</label><input id="bild" name="bild" type="file"><button>Skicka förfrågan</button></form></main></body></html>';
const sockets = new Set();
const server = http.createServer(async (req,res) => {
  try {
    const origin = 'http://127.0.0.1:'+server.address().port;
    const sidor = { '/': start, '/tack/': '<!doctype html><html lang="sv"><title>Tack</title><main><h1>Provets tacksida</h1></main></html>',
      '/mottagen/': '<!doctype html><html lang="sv"><title>Mottagen</title><main><h1>Provets mottagen-sida</h1></main></html>' };
    const ASSETS = { fetch: async (q) => { const s = sidor[new URL(q.url).pathname]; return new Response(s || 'saknas', { status: s ? 200 : 404, headers: { 'Content-Type': 'text/html; charset=utf-8' } }); } };
    const env = { ASSETS, DB, BILAGOR: r2(), MILJO: 'produktion', RESEND_API_KEY: 'syntetiskt', RESEND_API_URL: MEJL, FORFRAGAN_TILL: 'test@example.invalid', FORFRAGAN_FRAN: 'test@example.invalid' };
    const q = new Request(origin+req.url,{method:req.method,headers:req.headers,body:req.method === 'POST' ? req : undefined,duplex:'half'});
    const r = await worker.fetch(q, env);
    res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));
  } catch (e) { res.writeHead(500);res.end('Provfel');console.error(e.stack); }
});
server.on('connection',s => {sockets.add(s);s.on('close',()=>sockets.delete(s));});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin = 'http://127.0.0.1:'+server.address().port;
let browser;
try {
  browser = await chromium.launch({headless:true});
  for (const width of [320,390,768,1440]) {
    const context = await browser.newContext({viewport:{width,height:900},javaScriptEnabled:false});
    await context.route('**/*',route=>route.request().url().startsWith(origin+'/') ? route.continue() : route.abort());
    const page = await context.newPage();
    let meddelande;
    const steg = (namnet) => { meddelande = `\n Syntetiskt meddelande 🧪 ${width} ${namnet}\n</textarea><script>globalThis.xss=true</script>\n `; };
    const namn = 'Syntetisk <text> & "citat"';
    steg('forst');
    const fyll = async (n=namn) => {
      await page.goto(origin+'/');await page.getByLabel('Namn',{exact:true}).fill(n);
      await page.getByLabel('Telefon',{exact:true}).fill('0700000000');
      await page.getByLabel('Meddelande',{exact:true}).fill(meddelande);
    };
    const skicka = async () => {
      const [response] = await Promise.all([page.waitForResponse(r=>r.request().method()==='POST'),page.getByRole('button',{name:'Skicka förfrågan',exact:true}).click()]);
      await page.waitForLoadState();return response;
    };
    await fyll('   ');
    const first = await skicka();assert.equal(first.status(),422);
    assert.equal(await page.getByLabel('Meddelande',{exact:true}).inputValue(),meddelande);
    assert.equal(await page.getByLabel('Telefon',{exact:true}).inputValue(),'0700000000');
    assert.equal(await page.locator('script').count(),0);
    await page.getByRole('link',{name:/Namn: Skriv ditt namn/}).click();
    // Målet ligger efter sammanfattningen i DOM och länken leder rätt även utan JS.
    assert.equal(await page.evaluate(()=>document.activeElement.id),'namn');
    await page.getByLabel('Namn',{exact:true}).fill(namn);
    assert.equal((await skicka()).status(),303);assert.equal(new URL(page.url()).pathname,'/tack/');
    steg('bild');await fyll();
    await page.getByLabel('Bild (valfritt)',{exact:true}).setInputFiles({name:'prov.svg',mimeType:'image/svg+xml',buffer:Buffer.from('<svg/>')});
    assert.equal((await skicka()).status(),422);
    assert.equal(await page.getByLabel('Namn',{exact:true}).inputValue(),namn);
    assert.equal(await page.getByLabel('Meddelande',{exact:true}).inputValue(),meddelande);
    assert.ok((await page.locator('body').innerText()).includes('Välj bilden igen'));
    assert.equal(await page.getByLabel('Bild (valfritt)',{exact:true}).inputValue(),'');
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),width+' spill');
    if (bilder) {mkdirSync(bilder,{recursive:true});await page.screenshot({path:bilder+'/formular-bilagefel-'+width+'.png',fullPage:true});}
    mode='lagerfel';steg('lager');await fyll();
    const fore = events.filter(e=>e[0]==='mejl').length;
    assert.equal((await skicka()).status(),503);
    assert.equal(events.filter(e=>e[0]==='mejl').length,fore);
    assert.equal(await page.getByLabel('Meddelande',{exact:true}).inputValue(),meddelande);
    mode='mejlfel';
    assert.equal((await skicka()).status(),303);assert.equal(new URL(page.url()).pathname,'/mottagen/');  // D1: aldrig en sida på POST-adressen
    assert.equal(await page.getByRole('heading',{level:1}).innerText(),'Provets mottagen-sida');
    assert.equal(await page.locator('form').count(),0);
    console.log(JSON.stringify({bredd:width,utan_js:true,aterhamtning:true,sparad_skild_fran_osaker:true}));
    // dubbelklick på Skicka utan JavaScript: samma innehåll inom fönstret blir ett ärende
    mode='ok';steg('dubbel');await fyll();
    const fore2 = DB.db.prepare('SELECT count(*) AS n FROM forfragningar').get().n;
    await skicka();await page.goBack();await page.waitForLoadState();
    if (new URL(page.url()).pathname === '/') { await fyll(); await skicka(); }
    assert.equal(DB.db.prepare('SELECT count(*) AS n FROM forfragningar').get().n,fore2+1);
    mode='ok';await context.close();
  }
  // Axe kör i en separat kontext. Förloppen ovan behöver inga script i sidan.
  const context=await browser.newContext({viewport:{width:390,height:900},bypassCSP:true});
  const page=await context.newPage();await page.goto(origin+'/');
  await page.getByLabel('Namn',{exact:true}).fill(' ');
  await page.getByLabel('Telefon',{exact:true}).fill('0700000000');
  await page.getByLabel('Meddelande',{exact:true}).fill('Syntetiskt meddelande');
  await Promise.all([page.waitForNavigation(),page.getByRole('button',{name:'Skicka förfrågan',exact:true}).click()]);
  await page.addScriptTag({content:axe});
  const r=await page.evaluate(async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}));
  assert.deepEqual(r.violations.map(v=>({id:v.id,nodes:v.nodes.length})),[]);
  await page.keyboard.press('Tab');assert.ok(await page.evaluate(()=>document.activeElement.tagName!=='BODY'));
  console.log(JSON.stringify({axe:0,tangentbord:true}));await context.close();
  // lagret efter förloppen: per bredd ett aviserat ärende, ett sparat men inte aviserat, och dubbelinskicket som ett
  const st = DB.db.prepare('SELECT u.status AS s, count(*) AS n FROM forfragningar f JOIN utkorg u ON u.forfragan = f.id GROUP BY u.status ORDER BY u.status').all();
  assert.deepEqual(st.map((x)=>[x.s,x.n]),[['accepterad',8],['fel',4]]);
  console.log(JSON.stringify({arenden:st.map((x)=>[x.s,x.n])}));
} finally {
  if(browser) await browser.close();
  for(const s of sockets)s.destroy();await new Promise(r=>server.close(r));
}
