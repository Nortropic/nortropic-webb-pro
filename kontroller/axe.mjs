// axe-core (pinnad) på varje sida i mobil och desktop, plus en adress som inte finns.
// Generell form av kund-demo-norrglanta/scripts/prov/axe.mjs: sidorna ges som argument, inga kundspecifika selektorer.
//   node kontroller/axe.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG [--tillstand=meny,formularfel]
// --tillstand prövar också sidan i de tillstånd en besökare framkallar (Codex helhetsbedömning 2026-10-04, punkt 7):
//   meny         startsidans menyknapp (aria-expanded eller details/summary i sidhuvudet) öppnad, i varje vy där den syns
//   formularfel  varje sidas första synliga formulär skickat tomt, så att fältens felbesked visas
// Tillstånden klickar på sidan och prövas därför bara mot byggets lokala server; inskick blockeras av läsvakten.
// Exit 0 när inga överträdelser med påverkan serious eller critical finns; 1 annars; 2 vid fel i anropet.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { vakta } from './slugvakt.mjs';
import { viaTjanst, natgrans, lasvakt, arLokal } from './webblasare/gemensamt.mjs';

await viaTjanst('axe', process.argv.slice(2));  // sandlådat bygge: Chromium kan inte starta i sandlådan, tjänsten kör mätningen
const arg = (namn) => process.argv.find((a) => a.startsWith(`--${namn}=`))?.slice(namn.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
vakta(ut);
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG [--tillstand=meny,formularfel]'); process.exit(2); }
const tillstand = new Set((arg('tillstand') || '').split(',').map((x) => x.trim()).filter(Boolean));
const KANDA_TILLSTAND = ['meny', 'formularfel'];
const okanda = [...tillstand].filter((t) => !KANDA_TILLSTAND.includes(t));
if (okanda.length) { console.error('okänt tillstånd: ' + okanda.join(', ') + ' (kända: ' + KANDA_TILLSTAND.join(', ') + ')'); process.exit(2); }
if (tillstand.size && !arLokal(base)) { console.error('tillstånden (meny, formularfel) klickar på sidan och prövas bara mot byggets lokala server, inte ' + base); process.exit(2); }
// en stängd meny: knapp med aria-expanded, eller details/summary, i sidhuvudet eller navigationen
const MENYKNAPP = ['header button[aria-expanded="false"]', 'nav button[aria-expanded="false"]',
  'header details:not([open]) > summary', 'nav details:not([open]) > summary'].join(', ');
const menysida = sidor.includes('/') ? '/' : sidor[0];  // startsidan om den mäts, annars första sidan

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const axeVersion = JSON.parse(readFileSync(require.resolve('axe-core/package.json'), 'utf8')).version;
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'];
const ALLVARLIG = new Set(['serious', 'critical']);
const VYER = {
  mobil: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
};

async function korAxe(page) {
  // axe läggs in på nytt när sidan bytts (ett inskick kan ha navigerat)
  if (!await page.evaluate(() => !!window.axe)) await page.evaluate(axeSource);
  return page.evaluate(async (tags) => {
    const x = await window.axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations', 'incomplete'] });
    const smal = (l) => l.map((v) => ({ id: v.id, impact: v.impact, help: v.help, noder: v.nodes.slice(0, 5).map((n) => ({ target: n.target, sammanfattning: n.failureSummary })) }));
    return { overtradelser: smal(x.violations), ofullstandiga: smal(x.incomplete), godkanda: x.passes.length };
  }, TAGS);
}

mkdirSync(ut, { recursive: true });
const rader = [];
const grans = await natgrans([base]);  // i tjänstens läge: nätgränsen (domänpolicyn) också för sidans underresurser
const browser = await chromium.launch(grans ? grans.playwright : {});
try {
  for (const [vy, opt] of Object.entries(VYER)) {
    const ctx = await browser.newContext({ ...opt, locale: 'sv-SE', reducedMotion: 'reduce', serviceWorkers: 'block' });
    await lasvakt(ctx, [base]);  // läsande: sidans skript får inte skriva till någon sajt (F36, Codex R24)
    const page = await ctx.newPage();
    const ga = (sida) => page.goto(base + sida, { waitUntil: 'networkidle', timeout: 45000 })
      // networkidle hinner inte på sajter med evig bakgrundstrafik (spårning, annonser): då räcker load
      .catch(() => page.goto(base + sida, { waitUntil: 'load', timeout: 45000 }));
    for (const [nr, sida] of [...sidor, '/finns-inte-nwp'].entries()) {
      let svar = null;
      try {
        svar = await ga(sida);
        rader.push({ vy, sida, tillstand: 'sida', http: svar?.status() ?? null, ...await korAxe(page) });
      } catch (e) {
        rader.push({ vy, sida, tillstand: 'sida', http: null, fel: String(e.message).slice(0, 200), overtradelser: [], ofullstandiga: [], godkanda: 0 });
        continue;
      }
      if (sida === '/finns-inte-nwp') continue;
      // menyn: bara på startsidan (sidhuvudet är gemensamt), i varje vy där en stängd menyknapp syns
      if (tillstand.has('meny') && sida === menysida) {
        // elementet hålls fast före klicket: väljaren slutar matcha när menyn är öppen (aria-expanded, open)
        const knapp = await page.locator(MENYKNAPP).filter({ visible: true }).first().elementHandle({ timeout: 1000 }).catch(() => null);
        if (knapp) {
          try {
            await knapp.click({ timeout: 5000 });
            await page.waitForTimeout(400);
            const oppen = await knapp.evaluate((e) => e.getAttribute('aria-expanded') === 'true' || !!e.closest('details')?.open).catch(() => false);
            const etikett = await knapp.evaluate((e) => (e.getAttribute('aria-label') || e.innerText || '').trim().slice(0, 60)).catch(() => '');
            rader.push({ vy, sida, tillstand: 'meny', http: svar?.status() ?? null, oppen, knapp: etikett, ...await korAxe(page) });
          } catch (e) {
            rader.push({ vy, sida, tillstand: 'meny', http: null, fel: 'menyn gick inte att öppna: ' + String(e.message).split('\n')[0].slice(0, 160), overtradelser: [], ofullstandiga: [], godkanda: 0 });
          }
          await ga(sida).catch(() => {});
        }
      }
      // formulärfel: sidans första synliga formulär skickat tomt; läsvakten stoppar varje inskick
      if (tillstand.has('formularfel')) {
        const form = page.locator('form').filter({ visible: true }).first();
        const knapp = form.locator('button[type=submit], button:not([type]), input[type=submit]').filter({ visible: true }).first();
        if (await form.count() && await knapp.count()) {
          try {
            const fore = page.url();
            await knapp.click({ timeout: 5000 });
            await page.waitForTimeout(400);
            await page.waitForLoadState('load', { timeout: 5000 }).catch(() => {});
            if (page.url() !== fore) {
              // inskicket gick iväg (inget fält stoppade det tomt): det finns inget feltillstånd att pröva, och sidan som
              // visas nu (svaret, eller webbläsarens felsida när läsvakten stoppat inskicket) är inte sajtens
              rader.push({ vy, sida, tillstand: 'formularfel', matt: false, adress: page.url().slice(0, 200), overtradelser: [], ofullstandiga: [], godkanda: 0,
                skal: 'formuläret skickades tomt utan att något fält stoppade det; inget feltillstånd att pröva' });
              await ga(sida).catch(() => {});
              continue;
            }
            const ogiltiga = await page.evaluate(() => document.querySelectorAll('[aria-invalid="true"], form :invalid').length).catch(() => 0);
            rader.push({ vy, sida, tillstand: 'formularfel', http: svar?.status() ?? null, ogiltiga_falt: ogiltiga, ...await korAxe(page) });
          } catch (e) {
            rader.push({ vy, sida, tillstand: 'formularfel', http: null, fel: 'formuläret gick inte att skicka tomt: ' + String(e.message).split('\n')[0].slice(0, 160), overtradelser: [], ofullstandiga: [], godkanda: 0 });
          }
        }
      }
    }
    await ctx.close();
  }
} finally {
  await browser.close();
  if (grans) await grans.stang();
}
const allvarliga = rader.reduce((n, r) => n + r.overtradelser.filter((v) => ALLVARLIG.has(v.impact)).length, 0);
const totalt = rader.reduce((n, r) => n + r.overtradelser.length, 0);
const fel = rader.filter((r) => r.fel).length;
const lage = (r) => r.vy + ' ' + r.sida + (r.tillstand && r.tillstand !== 'sida' ? ' [' + r.tillstand + ']' : '');
for (const r of rader) if (r.fel) console.log(lage(r), 'FEL', r.fel);
for (const r of rader) {
  if (r.overtradelser.length) console.log(lage(r), r.overtradelser.map((v) => `${v.id}(${v.impact})`).join(', '));
}
const provade = [...tillstand];
writeFileSync(join(ut, 'axe.json'), JSON.stringify({ base, axeVersion, tags: TAGS, tid: new Date().toISOString(), tillstand: provade, allvarliga, totalt, fel, rader }, null, 1) + '\n');
const iTillstand = rader.filter((r) => r.tillstand !== 'sida').length;
console.log(`axe-core ${axeVersion}: ${allvarliga} allvarliga (serious/critical) av ${totalt} överträdelser i ${rader.length} lägen` + (provade.length ? `, varav ${iTillstand} i tillstånd (${provade.join(', ')})` : ''));
process.exitCode = allvarliga === 0 && fel === 0 ? 0 : 1;
