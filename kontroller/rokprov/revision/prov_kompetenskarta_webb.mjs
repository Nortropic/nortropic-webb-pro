// Kompetenskartans webbläsarprov, kört av prov_kompetenskarta_webb.py: Systemförbättring, Kompetenskartan i portalen,
// flikarna med tangentbordet, och varje flik med axe och spill i 390 och 1440 px.
import { resolve } from 'node:path';
import { mkdirSync } from 'node:fs';
import assert from 'node:assert/strict';
const [url, nyckel, bevis] = process.argv.slice(2);
const root = resolve('.');
const { chromium } = await import(resolve(root, 'kontroller/node_modules/playwright/index.mjs'));
const sov = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch({ headless: true });
try {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const sidfel = []; page.on('pageerror', (e) => sidfel.push(e.message));
  const origin = new URL(url).origin;
  await page.route((u) => u.origin !== origin && !u.hostname.startsWith('127.0.0.1'), (r) => r.abort());
  const bild = async (namn) => { if (bevis) { mkdirSync(bevis, { recursive: true }); await page.screenshot({ path: `${bevis}/kompetenskarta-${namn}.png`, fullPage: true }); } };
  await page.addInitScript(() => { try { sessionStorage.removeItem('nwp-kompetenskarta:flik'); } catch { /* */ } });
  await page.goto(`${url}/#nyckel=${nyckel}&till=start`);
  await page.locator('#pt-system summary').click();
  await page.locator('#pt-system a[href="#/kompetens"]').click();
  await page.locator('.kk h1').filter({ hasText: 'Kompetenskartan' }).waitFor();
  assert.equal(await page.locator('#pt-system a[href="#/kompetens"]').getAttribute('aria-current'), 'page');
  assert.match(await page.locator('.kk-summa').textContent(), /2 av 15 roller observerade/);
  // Luckor först: kärnan, MCP-kravet och det oobserverade, var och en med källa och förslag
  assert.equal(await page.locator('[data-kk-flik="luckor"]').getAttribute('aria-selected'), 'true');
  const luckor = await page.locator('.kk-lucka').allTextContents();
  assert(luckor.some((t) => /Kärnan.*kärnan lästes inte hel i 1 av 1/s.test(t)), 'kärnans lucka: ' + luckor.join(' | ').slice(0, 400));
  assert(luckor.some((t) => /MCP-krav.*refero/s.test(t)), 'researchens MCP-krav');
  assert(luckor.some((t) => /Inte observerat/.test(t)), 'de oobserverade stegen');
  assert(luckor.every((t) => /Källa:/.test(t) && /Förslag:/.test(t)));
  const prova = async (flik) => {
    await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
    const fynd = await page.evaluate(async () => (await axe.run(document.querySelector('#vy'), { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }))
      .violations.map((v) => `${v.id}: ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`));
    assert.deepEqual(fynd, [], `axe i fliken ${flik}`);
    for (const w of [390, 1440]) {
      await page.setViewportSize({ width: w, height: 900 }); await sov(250);
      // sidan får aldrig rulla i sidled; tabellen rullar i sin egen yta. Vid fel: de yttersta elementen som sticker ut
      const spill = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth ? [] : [`scrollWidth ${document.documentElement.scrollWidth} > ${innerWidth}`,
        ...[...document.querySelectorAll('body *')].filter((e) => e.getBoundingClientRect().right > innerWidth + 1 && !e.parentElement.closest('.kk-tabell'))
          .slice(0, 6).map((e) => `${e.tagName.toLowerCase()}${e.id ? '#' + e.id : ''}.${String(e.className).split(' ').slice(0, 2).join('.')} ${Math.round(e.getBoundingClientRect().width)}`)]);
      assert.deepEqual(spill, [], `sidledes spill i ${flik} vid ${w} px`);
      await bild(`${flik}-${w}`);
    }
    await page.setViewportSize({ width: 1440, height: 900 });
  };
  await prova('luckor');
  // flikarna med pilarna: Flödet, Kompetenserna, Tjänster och agenter
  await page.locator('[data-kk-flik="luckor"]').focus();
  await page.keyboard.press('ArrowRight');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.kkFlik), 'flodet');
  // ett steg per pass i kompetenskarta.FLODE, designfasens specialistpass med (2026-10-12); antalet ur API:t, inte ett fast tal
  const flode = (await page.evaluate(async () => (await fetch('/api/kompetenskarta')).json())).steg;
  assert(flode.length >= 24 && flode.some((s) => s.pass === 'ds_kritik'), 'flödet i API:t: ' + flode.map((s) => s.pass).join(', '));
  assert.equal(await page.locator('.kk-steg').count(), flode.length, 'varje steg i flödet');
  assert.match(await page.locator('.kk-steg').first().textContent(), /Förberedelsen av kundunderlaget/);
  assert.match(await page.locator('.kk-steg').filter({ hasText: 'Researchen' }).textContent(), /mobbin: använt med resultat ×1/);
  await prova('flodet');
  await page.locator('[data-kk-flik="flodet"]').focus();
  await page.keyboard.press('ArrowRight');
  await page.locator('.kk-tabell table').waitFor();
  const rader = await page.locator('.kk-tabell tbody th[scope="row"]').count();
  const d = await page.evaluate(async () => (await fetch('/api/kompetenskarta')).json());
  assert.equal(rader, Object.keys(d.skills).length + d.filer.filter((f) => f.typ === 'kunskap' || f.typ === 'kritik').length, 'varje skill och kunskapstext en rad');
  assert.match(await page.locator('.kk-tabell').textContent(), /ingen uppgift i flödet/);
  await prova('kompetenser');
  await page.locator('[data-kk-flik="kompetenser"]').focus();
  await page.keyboard.press('End');
  assert.equal(await page.evaluate(() => document.activeElement.dataset.kkFlik), 'utanfor');
  assert.match(await page.locator('#kk-panel').textContent(), /Ändringsagenten/);
  assert.match(await page.locator('#kk-panel').textContent(), /copy-kontroll/);
  await prova('utanfor');
  assert.deepEqual(sidfel, [], 'inga sidfel');
  console.log(JSON.stringify({ flikar: 4, axe: 0, spill: false, rader }));
} finally {
  await browser.close();
}
