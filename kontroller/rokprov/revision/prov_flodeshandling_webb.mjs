// UI-prov med riktiga klick och syntetiska HTTP-svar: Flöde i Byggflöde (ägarens mandat 2026-10-09 ~18:28Z). Adressen
// #/flode/<kund> leder till Byggflöde, som visar beskedet, starterna, stegen i detalj, det tänkta flödet och Figma-piloten
// ur samma läge som arbetsytan. Startlogiken på servern prövas separat i prov_flodeshandling.py.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
const root = resolve(process.argv[2] || '.');
const html = await readFile(resolve(root, 'dashboard/index.html'));
const filer = new Map(await Promise.all(['kundstart-agare.js', 'kirurg-forbattring.js', 'arbetsyta.js', 'arbetsyta.css'].map(async namn =>
  ['/' + namn, await readFile(resolve(root, 'dashboard', namn))])));
const namn = ['Sessionen avslutades normalt', 'Tekniska kontroller', 'Designgranskning', 'Ägarens godkännande', 'Leverans inom angiven omfattning'];
let fas = 'klar';
let hallPost = false, slappPost, postFel = true;
const posts = [], starter = new Set();
function lage(slug) {
  return { slug, tid: '2026-01-01T00:00:00Z', projekt: { namn: slug === 'prov-flode' ? 'Provflödet' : 'Andra provet', testdata: true }, blind: false, ab_dold: false,
    korning: { startad: '2026-01-01T00:00:00Z', steg: fas, lage: 'forbered' }, moment: { nr: 1, namn: 'Kundunderlag', status: 'skapat' },
    steg: [{ nr: 1, namn: 'Kundunderlag', status: fas === 'avbruten' ? 'stoppat' : 'skapat', underlag: ['`VERKSAMHET.json`'], utfall: [{ text: 'UPPDRAG.md', tid: '2026-01-01T00:00:00Z' }],
      kontroller: [], beslut: [], brister: ['Inget är verifierat i provet.'], nasta: 'Nästa handling står i beskedet.' }],
    besked: { version: 'syntetisk-version', tid: '2026-01-01T00:00:00Z', filer: [],
      tillstand: namn.map((n, i) => ({ namn: n, status: i === 1 ? 'historiskt' : i === 4 ? 'nej' : 'ej bedömt',
        varde: i === 4 ? false : null, text: fas === 'avbruten' ? 'Arbetet stoppades. Ingen ny version godkändes.' : 'Syntetiskt besked för provet.' })) },
    handlingar: [{ id: fas === 'pagar' ? 'stoppa' : 'forbered', text: fas === 'pagar' ? 'Stoppa arbetet' : 'Förbered kundunderlaget' }],
    startmiljo: { sandlada: 'av', kundstart_lager: false }, kandidater: [], sessioner: [], helbygge: [], preview: [], partner: null };
}
const flodet = { slugar: ['prov-flode', 'prov-andra'],
  kedjan: { steg: [{ steg: 'Kundunderlaget', vem: 'Kundstart samlar underlaget.', resultat: 'VERKSAMHET.json', saknas: 'En verklig kund.' }] },
  pilot: [{ id: 'moment-b', moment: 'B. Anpassa till kundens material', status: 'kontrollerat', aktuell: 'v2', figma: { fil: 'prov' }, kontroller: [], bedomningar: [], fynd: [],
    bilder: [{ lank: '/fil/prov/bild.png', text: 'Moment B', version: 'v2' }] }] };
const srv = createServer(async (req, res) => {
  const json = (x, kod = 200) => { res.writeHead(kod, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(x)); };
  const url = new URL(req.url, 'http://x'), vag = url.pathname;
  if (req.method === 'POST') {
    let body = ''; for await (const b of req) body += b;
    const p = JSON.parse(body); posts.push(p);
    if (hallPost) await new Promise(r => { slappPost = r; });
    if (p.handling === 'stoppa') { fas = 'avbruten'; return json({ slutkod: 4, besked: 'Arbetet är stoppat.' }); }
    starter.add(p.start_id);  // bara attrappens mekanik; den riktiga serverns idempotens prövas i Python
    await new Promise(r => setTimeout(r, 250));
    if (postFel) { postFel = false; return json({ fel: 'syntetiskt svarsfel efter mottagen start' }, 503); }
    fas = 'pagar'; return json({ slutkod: 5, besked: 'Arbetet är startat.' }, 202);
  }
  if (vag === '/api/arbetsyta') return json({ projekt: [{ slug: 'prov-flode', namn: 'Provflödet', testdata: true }, { slug: 'prov-andra', namn: 'Andra provet', testdata: true }] });
  const m = vag.match(/^\/api\/arbetsyta\/(prov-flode|prov-andra)(\/strom)?$/);
  if (m && m[2]) { res.writeHead(200, { 'Content-Type': 'text/event-stream' }); res.end(`retry: 1000\nevent: lage\ndata: ${JSON.stringify(lage(m[1]))}\n\n`); return; }
  if (m) return json(lage(m[1]));
  if (vag === '/api/flode') return json(flodet);
  if (vag === '/api/oversikt') return json({ byggen: [], backlog_vilande: 0, intag_pagar: 0, prospekt_vantar: 0 });
  if (vag.startsWith('/api/')) return json({});
  if (filer.has(vag)) { res.writeHead(200, { 'Content-Type': vag.endsWith('.css') ? 'text/css; charset=utf-8' : 'text/javascript; charset=utf-8' }); res.end(filer.get(vag)); return; }
  if (vag !== '/') { res.writeHead(404); res.end(); return; }
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
  // adressen #/flode/<kund> leder till Byggflöde för samma kund
  await page.goto(origin + '/#/flode/prov-flode');
  await page.getByRole('heading', { name: 'Aktuellt besked', exact: true }).waitFor();
  assert.equal(await page.evaluate(() => location.hash), '#/arbetsyta/prov-flode/flode', '#/flode/<kund> ska leda till Byggflöde');
  assert.equal(await page.getByRole('navigation', { name: 'Arbetsytans vyer' }).locator('a[aria-current="page"]').textContent(), 'Byggflöde');
  assert.equal(posts.length, 0, 'att läsa vyn startar inget');
  assert.equal(await page.locator('.ay-besked dt').count(), 5, 'beskedets fem tillstånd');
  const beskedet = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Aktuellt besked', exact: true }) });
  assert(await beskedet.textContent().then(t => t.includes('Byggversion syntetisk-ve') && t.includes('sandlåda av')), 'version och startmiljö');
  await page.locator('.ay-stegdetalj summary').filter({ hasText: 'Kundunderlag' }).click();
  assert(await page.locator('.ay-stegdetalj details[open]').textContent().then(t => t.includes('Fel, begränsningar') && t.includes('Nästa handling står i beskedet')), 'stegets detaljer');
  await page.locator('details.metod summary').click();
  await page.locator('#ay-metod').getByText('saknas i dag').waitFor();
  await page.locator('summary').filter({ hasText: 'Figma-metodprovet' }).click();
  assert.equal(await page.locator('.ay-pilotbilder figcaption').textContent(), 'version v2', 'pilotens bild med sin version');
  // Flöde är inte längre en egen del i menyn
  const kund = await page.getByRole('navigation', { name: 'Arbetsytans delar' }).locator('details').first().evaluate(d => [...d.querySelectorAll('.ay-menylista a')].map(a => a.getAttribute('href')));
  assert(!kund.some(h => h.startsWith('#/flode')), 'Flöde ska inte stå i menyn: ' + kund.join(' '));
  for (const width of [320, 390, 768, 1280, 1440]) {
    await page.setViewportSize({ width, height: 950 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'spill vid ' + width);
    if (process.env.NWP_UI_BEVISET && [390, 1440].includes(width)) await page.screenshot({ path: process.env.NWP_UI_BEVISET.replace(/\.png$/, `-${width}.png`), fullPage: true });
    const size = await page.locator('.ay-besked').getByRole('button', { name: 'Förbered kundunderlaget' }).boundingBox();
    assert(size.height >= 44 && size.x >= 0 && size.x + size.width <= width, 'startknappen vid ' + width);
  }
  await page.setViewportSize({ width: 1440, height: 950 });
  await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
  const axe = await page.evaluate(() => axe.run(document.querySelector('.ay'), { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }));
  assert.deepEqual(axe.violations.map(x => x.id), [], 'axe i Byggflödet med Flöde');
  // start med tangentbordet: ett extra klick under väntan skickar ingen andra start, och ett felsvar behåller start-id
  const knapp = page.locator('.ay-besked').getByRole('button', { name: 'Förbered kundunderlaget' });
  await knapp.focus(); await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.querySelector('.ay-besked [data-handling="forbered"]')?.getAttribute('aria-disabled') === 'true');
  await page.locator('.ay-besked [data-handling="forbered"]').dispatchEvent('click');
  await page.locator('#ay-handlingssvar').filter({ hasText: 'Svaret gick inte att bekräfta' }).waitFor();
  assert.equal(posts.length, 1);
  await page.reload();
  await page.locator('.ay-besked').getByRole('button', { name: 'Förbered kundunderlaget' }).click();
  await page.waitForFunction(() => location.hash === '#/arbetsyta/prov-flode', null, { timeout: 10000 });  // efter en start: arbetsytan, där sessionerna syns
  assert.equal(posts.length, 2); assert.equal(posts[0].start_id, posts[1].start_id, 'samma start-id efter felsvaret');
  assert.equal(starter.size, 1);
  // stopp i två steg från Byggflöde
  await page.evaluate(() => { location.hash = '#/arbetsyta/prov-flode/flode'; });
  await page.locator('.ay-besked').getByRole('button', { name: 'Stoppa arbetet' }).click();
  await page.locator('.ay-besked [data-bekraftad]').click();
  await page.locator('#ay-handlingssvar').filter({ hasText: 'Arbetet är stoppat' }).waitFor();
  assert.equal(posts[2].handling, 'stoppa');
  await page.locator('.ay-besked').filter({ hasText: 'Ingen ny version godkändes' }).waitFor();
  // ett sent svar för en kund skrivs aldrig i en annan kunds vy
  fas = 'klar'; hallPost = true; slappPost = null;
  await page.reload();
  await page.locator('.ay-besked').getByRole('button', { name: 'Förbered kundunderlaget' }).click();
  while (!slappPost) await new Promise(r => setTimeout(r, 10));
  await page.evaluate(() => { location.hash = '#/arbetsyta/prov-andra/flode'; });
  await page.locator('#ay-kund option:checked').filter({ hasText: 'Andra provet' }).waitFor({ state: 'attached' });
  slappPost(); hallPost = false;
  await page.waitForTimeout(800);
  assert.equal(await page.evaluate(() => location.hash), '#/arbetsyta/prov-andra/flode', 'det sena svaret får inte byta tillbaka kunden');
  assert.equal((await page.locator('#ay-handlingssvar').textContent()).trim(), '', 'den första kundens besked får inte stå hos den andra');
  assert.equal(await page.locator('.ay-besked [data-handling="forbered"]').getAttribute('aria-disabled'), null, 'knapparna är åter tillgängliga');
  assert.deepEqual(errors, []);
  if (process.env.NWP_UI_BEVISET) await page.screenshot({ path: process.env.NWP_UI_BEVISET, fullPage: true });
  console.log(JSON.stringify({ bredder: [320, 390, 768, 1280, 1440], axe_fynd: axe.violations.length, adressen_leder_till_byggflode: true, dubbla_starter: false,
    omforsok_samma_id: true, tangentbord: true, stopp_tva_steg: true, sent_svar_annan_kund: false, api: 'syntetiska svar; riktig server prövas separat' }));
} finally {
  await browser?.close();
  await new Promise(r => srv.close(r));
}
