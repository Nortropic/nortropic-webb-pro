// UI-prov med riktiga klick och syntetiska HTTP-svar. Startlogiken prövas separat i prov_flodeshandling.py.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] || '.');
const html = await readFile(resolve(root, 'dashboard/index.html'));
// arbetsytans skript och stil också: Flöde ritas i arbetsytans ram (ägarens besked 2026-10-09 ~17:11Z)
const skript = new Map(await Promise.all(['kundstart-agare.js', 'kirurg-forbattring.js', 'arbetsyta.js', 'arbetsyta.css'].map(async namn =>
  ['/' + namn, await readFile(resolve(root, 'dashboard', namn))])));
const namn = ['Sessionen avslutades normalt', 'Tekniska kontroller', 'Designgranskning', 'Ägarens godkännande', 'Leverans inom angiven omfattning'];
let fas = 'klar', getFel = false, postFel = true;
let hallPost = false, slappPost;
const posts = [], starter = new Set();
function flode() {
  return { slug: 'prov-flode', blind: false, ab_dold: false, tid: '2026-01-01T00:00:00Z',
    korning: { startad: '2026-01-01T00:00:00Z', steg: fas, lage: 'forbered' },
    steg: [{ nr: 1, namn: 'Kundunderlag', status: fas === 'avbruten' ? 'stoppat' : 'skapat', nasta: 'Nästa handling står ovan.' }],
    besked: { version: 'syntetisk-version', tid: '2026-01-01T00:00:00Z', filer: [],
      tillstand: namn.map((n, i) => ({ namn: n, status: i === 1 ? 'historiskt' : i === 4 ? 'nej' : 'ej bedömt',
        varde: i === 4 ? false : null, text: fas === 'avbruten' ? 'Arbetet stoppades. Ingen ny version godkändes.' : 'Syntetiskt besked för provet.' })) },
    handlingar: [{ id: fas === 'pagar' ? 'stoppa' : 'forbered', text: fas === 'pagar' ? 'Stoppa arbetet' : 'Förbered kundunderlaget' }] };
}
const srv = createServer(async (req, res) => {
  const json = (x, kod = 200) => { res.writeHead(kod, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(x)); };
  if (req.method === 'POST') {
    let body = ''; for await (const b of req) body += b;
    const p = JSON.parse(body); posts.push(p);
    if (hallPost) await new Promise(resolve => { slappPost = resolve; });
    if (p.handling === 'stoppa') { fas = 'avbruten'; return json({ slutkod: 4, besked: 'Arbetet är stoppat.' }); }
    starter.add(p.start_id); // bara attrappens mekanik; den riktiga serverns idempotens provas i Python.
    await new Promise(r => setTimeout(r, 250));
    if (postFel) { postFel = false; return json({ fel: 'syntetiskt svarsfel efter mottagen start' }, 503); }
    fas = 'pagar'; return json({ slutkod: 5, besked: 'Arbetet är startat.' }, 202);
  }
  if (req.url === '/api/flode') {
    if (getFel) { getFel = false; return json({ fel: 'Syntetiskt läsfel' }, 503); }
    return json({ slugar: ['prov-flode','prov-andra'], pilot: [], kedjan: { steg: [] } });
  }
  if (req.url === '/api/flode/prov-flode') return json(flode());
  if (req.url === '/api/flode/prov-andra') return json({...flode(),slug:'prov-andra'});
  if (req.url === '/api/oversikt') return json({ byggen: [], backlog_vilande: 0, intag_pagar: 0, prospekt_vantar: 0 });
  if (req.url?.startsWith('/api/')) return json({});
  if (skript.has(req.url)) {
    res.writeHead(200, { 'Content-Type': req.url.endsWith('.css') ? 'text/css; charset=utf-8' : 'text/javascript; charset=utf-8' }); res.end(skript.get(req.url)); return;
  }
  if (req.url !== '/') { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); res.end(html);
});
await new Promise(r => srv.listen(0, '127.0.0.1', r));
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const origin = `http://127.0.0.1:${srv.address().port}`;
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  await page.goto(origin + '/#/flode/prov-flode');
  await page.getByRole('heading', { name: 'Aktuellt besked', exact: true }).waitFor();
  assert.deepEqual(await page.evaluate(() => [typeof kundstartvy, typeof kirurgForbattring]), ['function', 'function'],
    'dashboardens separata skript ska laddas som riktig JavaScript även i HTTP-fixturen');
  assert.equal(posts.length, 0, 'att läsa vyn startar inget');
  assert.equal(await page.locator('.ay #vy.ay-sektion .flodesbesked').count(), 1, 'Flöde ska ritas i arbetsytans ram');
  assert.equal(await page.locator('.ay-menylista a[aria-current="page"]').getAttribute('href'), '#/flode', 'navigeringen ska visa Flöde som aktuell del');
  for (const width of [320, 390, 768, 1280, 1440]) {
    await page.setViewportSize({ width, height: 950 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'spill vid ' + width);
    assert.equal(await page.locator('.flodesbesked dt').count(), 5);
    if (process.env.NWP_UI_BEVISET && [390, 1440].includes(width)) await page.screenshot({ path: process.env.NWP_UI_BEVISET.replace(/\.png$/, `-${width}.png`), fullPage: true });
    const size = await page.getByRole('button', { name: 'Förbered kundunderlaget' }).boundingBox();
    assert(size.height >= 44 && size.x >= 0 && size.x + size.width <= width, 'startknappen vid ' + width);
  }
  await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
  const axe = await page.evaluate(() => axe.run(document.querySelector('.flode'), { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }));
  assert.deepEqual(axe.violations.map(x => x.id), [], 'axe i ändrad flödesvy');
  getFel = true;
  await page.getByRole('button', { name: 'Läs aktuellt läge' }).click();
  await page.getByRole('status').filter({ hasText: 'Syntetiskt läsfel' }).waitFor();
  assert.equal(posts.length, 0);
  const button = page.getByRole('button', { name: 'Förbered kundunderlaget' });
  await button.focus(); await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelector('[data-flodeshandling]').disabled);
  await button.dispatchEvent('click'); // ett extra event får inte skicka en dubbelstart
  await page.getByRole('status').filter({ hasText: 'Svaret gick inte att bekräfta' }).waitFor();
  assert.equal(posts.length, 1);
  await page.reload();
  await page.getByRole('button', { name: 'Förbered kundunderlaget' }).click();
  await page.getByRole('button', { name: 'Stoppa arbetet' }).waitFor();
  assert.equal(posts.length, 2); assert.equal(posts[0].start_id, posts[1].start_id);
  assert.equal(starter.size, 1);
  assert.equal(await page.locator(':focus').getAttribute('id'), 'flode-besked-rubrik');
  await page.getByRole('button', { name: 'Stoppa arbetet' }).click();
  await page.getByRole('status').filter({ hasText: 'Arbetet är stoppat' }).waitFor();
  assert.equal(posts[2].handling, 'stoppa');
  assert(await page.locator('.flodesbesked').textContent().then(t => t.includes('Ingen ny version godkändes')));
  // Ett sent svar för A får inte byta tillbaka från B eller skriva besked i B:s vy.
  fas='klar';hallPost=true;
  await page.reload();await page.getByRole('button',{name:'Förbered kundunderlaget'}).click();
  while(!slappPost) await new Promise(r=>setTimeout(r,10));
  await page.goto(origin+'/#/flode/prov-andra');
  await page.getByRole('heading',{name:'Det här hände: prov-andra',exact:true}).waitFor();
  slappPost();hallPost=false;
  await page.waitForTimeout(450);
  assert.equal(await page.getByRole('heading',{name:'Det här hände: prov-andra',exact:true}).count(),1,'sena A-svaret skrev över B');
  assert.equal(await page.locator('#flode-handlingssvar').textContent(),'','A:s besked får inte stå i B');
  assert.deepEqual(errors, []);
  if (process.env.NWP_UI_BEVISET) await page.screenshot({ path: process.env.NWP_UI_BEVISET, fullPage: true });
  console.log(JSON.stringify({ bredder: [320, 390, 768, 1280, 1440], axe_fynd: axe.violations.length, dubbla_starter: false,
    omforsok_samma_id: true, tangentbord: true, laddning_fel_stopp_historik: true, api: 'syntetiska svar; riktig server prövas separat' }));
} finally {
  await browser?.close();
  await new Promise(r => srv.close(r));
}
