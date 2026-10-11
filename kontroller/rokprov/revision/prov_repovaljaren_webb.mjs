// Repoväljarens webbläsarprov (kunskap/andringar.md, Repoväljaren), kört av prov_repovaljaren_webb.py mot den riktiga
// dashboardservern i en isolerad rot med provets gh och provagenten. del1: knappen och ⌘O (också från terminalen, utan
// att agenten får tangenten), sökning och tangentbord, axe och spill, byte under en levande agent (låt den arbeta, och
// stoppa den), klon efter bekräftelse, koppling med namnförslag, utgången inloggning, kundens sida och hämta/uppdatera
// i Ändringar. del2 (en ny serverinstans): Senast öppnade står kvar.
import { resolve } from 'node:path';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
const [del, url, nyckel, rot, bevis] = process.argv.slice(2);
const root = resolve('.');
const { chromium } = await import(resolve(root, 'kontroller/node_modules/playwright/index.mjs'));
const sov = (ms) => new Promise((r) => setTimeout(r, ms));
const browser = await chromium.launch({ headless: true });
const sammanfattning = { del };
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const sidfel = []; page.on('pageerror', (e) => sidfel.push(e.message));
  const origin = new URL(url).origin;
  await page.route((u) => u.origin !== origin && !u.hostname.startsWith('127.0.0.1'), (r) => r.abort());
  const bild = async (namn) => { if (bevis) { mkdirSync(bevis, { recursive: true }); await page.screenshot({ path: `${bevis}/repovaljaren-${namn}.png` }); } };
  const text = () => page.evaluate(() => { const t = window.__andringar?.term; if (!t) return ''; const b = t.buffer.active, ut = [];
    for (let i = 0; i < b.length; i++) { const l = b.getLine(i); if (l) ut.push(l.translateToString(true)); } return ut.join('\n'); });
  const vantaText = async (s, ms = 15000) => { const slut = Date.now() + ms; while (Date.now() < slut) { if ((await text()).includes(s)) return; await sov(150); } throw new Error(`terminalen visade aldrig "${s}"`); };
  const lage = (slug) => page.evaluate(async (s) => (await fetch(`/api/andringar/${s}`, { cache: 'no-store' })).json(), slug);
  const etiketter = () => page.locator('#rv .rv-etikett').allTextContents();
  const grupper = () => page.locator('#rv .rv-grupp').evaluateAll((g) => g.map((x) => [x.getAttribute('aria-label'), [...x.querySelectorAll('.rv-etikett')].map((e) => e.textContent)]));
  const aktiv = () => page.locator('#rv-sok').getAttribute('aria-activedescendant');
  const oppnad = async () => { await page.locator('#rv:not([aria-busy])').waitFor(); await page.locator('#rv .rv-alt').first().waitFor(); };  // listan omläst
  const oppnaMedKnapp = async () => { await page.locator('[data-rv-oppna]').first().click(); await oppnad(); };

  if (del === 'del2') {
    // en ny serverinstans och en ny webbläsarsession: Senast öppnade läses ur motorns fil, inte ur minnet
    await page.goto(`${url}/#nyckel=${nyckel}&till=andringar/gamma`);
    await page.locator('#an-rubrik').waitFor();
    await oppnaMedKnapp();
    const g = await grupper();
    assert.deepEqual(g[0], ['Senast öppnade', ['kund-gamma', 'kund-alfa', 'kund-beta']], 'Senast öppnade efter omstarten: ' + JSON.stringify(g));
    await bild('senast-efter-omstart');
    sammanfattning.senast = g[0][1];
  } else {
    await page.goto(`${url}/#nyckel=${nyckel}&till=andringar/alfa`);
    await page.locator('#an-rubrik').waitFor();
    const knapp = page.locator('.an-id [data-rv-oppna]');
    await knapp.waitFor();
    assert.equal(await knapp.getAttribute('aria-keyshortcuts'), 'Meta+O');
    // ⌘O från terminalen: väljaren öppnas, och agenten får aldrig tangenten
    await page.locator('[data-an-starta]').click();
    await vantaText('redo.');
    const pid = (await lage('alfa')).session.pid;
    await page.locator('#an-xterm').click();
    await page.keyboard.press('Meta+O');
    await page.locator('#rv').waitFor();
    assert.equal(await page.evaluate(() => document.activeElement.id), 'rv-sok', 'sökrutan har fokus');
    await page.locator('#rv .rv-alt').first().waitFor();
    assert(!(await text()).includes('fick:'), 'genvägen nådde inte agenten');
    assert.deepEqual((await etiketter()).sort(), ['kund-alfa', 'kund-beta', 'kund-gamma', 'kund-utan-markor'], 'organisationens kundrepon, inga andra');
    assert.deepEqual((await grupper()).map((g) => g[0]), ['Senast öppnade', 'Kundrepon i Nortropic']);
    assert.equal(await page.locator('#rv input').count(), 1, 'ingen sökvägs- eller tokenruta');
    // sökningen: delsträng, markerad träff, tomt besked utan listruta
    await page.locator('#rv-sok').fill('bet');
    assert.deepEqual(await etiketter(), ['kund-beta']);
    assert.equal(await page.locator('#rv .rv-etikett mark.rv-traff').first().textContent(), 'bet');
    await page.locator('#rv-sok').fill('snickeriet');
    assert.deepEqual(await etiketter(), ['kund-alfa'], 'kundens namn går också att söka på');
    await page.locator('#rv-sok').fill('zzz');
    await page.locator('#rv .rv-tomt').filter({ hasText: 'Inga kundrepon matchar' }).waitFor();
    assert.equal(await page.locator('#rv-yta[role="listbox"]').count(), 0);
    // tangentbordet: pilarna går runt, som i VS Codes Quick Pick
    await page.locator('#rv-sok').fill('');
    assert.equal(await aktiv(), 'rv-alt-0');
    await page.keyboard.press('ArrowUp'); assert.equal(await aktiv(), 'rv-alt-3');
    await page.keyboard.press('ArrowDown'); assert.equal(await aktiv(), 'rv-alt-0');
    await page.keyboard.press('ArrowDown'); assert.equal(await aktiv(), 'rv-alt-1');
    await page.keyboard.press('Control+End'); assert.equal(await aktiv(), 'rv-alt-3');
    await page.keyboard.press('Control+Home'); assert.equal(await aktiv(), 'rv-alt-0');
    assert.equal(await page.locator('#rv-antal').textContent(), '4 träffar', 'antalet läses upp');
    // axe och spill med väljaren öppen
    await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
    const fynd = await page.evaluate(async () => (await axe.run(document.querySelector('#rv'), { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }))
      .violations.map((v) => `${v.id}: ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`));
    assert.deepEqual(fynd, [], 'axe i repoväljaren');
    for (const w of [390, 1440]) {
      await page.setViewportSize({ width: w, height: 900 }); await sov(250);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `sidledes spill vid ${w} px`);
      const box = await page.locator('#rv').boundingBox();
      assert(box.x >= 0 && box.x + box.width <= w + 0.5, `väljaren ryms vid ${w} px`);
      // väljaren klipper sitt innehåll: inget i den får vara bredare än den (sökrutan sköts ut en gång)
      const utanfor = await page.evaluate(() => { const r = document.querySelector('#rv'), o = r.getBoundingClientRect();
        return [...r.querySelectorAll('*')].filter((e) => { const b = e.getBoundingClientRect(); return b.width > 0 && (b.left < o.left - 0.5 || b.right > o.right + 0.5); })
          .map((e) => `${e.tagName.toLowerCase()}.${e.className} ${Math.round(e.getBoundingClientRect().left)}–${Math.round(e.getBoundingClientRect().right)} (väljaren ${Math.round(o.left)}–${Math.round(o.right)})`)
          .concat(r.scrollWidth > r.clientWidth ? [`scrollWidth ${r.scrollWidth} > ${r.clientWidth}`] : []); });
      assert.deepEqual(utanfor, [], `inget i väljaren går utanför den vid ${w} px`);
      await bild(`lista-${w}`);
    }
    await page.setViewportSize({ width: 1440, height: 900 });
    // Esc stänger och lämnar fokus där det var (terminalen); knappen får fokus tillbaka när den öppnade
    await page.keyboard.press('Escape');
    await page.locator('#rv').waitFor({ state: 'detached' });
    assert(await page.evaluate(() => document.activeElement.classList.contains('xterm-helper-textarea')), 'fokus tillbaka i terminalen');
    await oppnaMedKnapp();
    await page.keyboard.press('Escape');
    assert.equal(await page.evaluate(() => document.activeElement.hasAttribute('data-rv-oppna')), true, 'fokus tillbaka på knappen');
    sammanfattning.lista = { genvag_fran_terminalen: true, filter: true, tangentbord: true, axe: 0, spill: false };

    // byte under en levande agent: låt den arbeta; sedan bekräftelsen och klonen
    await oppnaMedKnapp();
    await page.locator('#rv-sok').fill('beta'); await page.keyboard.press('Enter');
    await page.locator('[data-rv-ja="bakgrund"]').waitFor();
    await bild('byte');
    await page.locator('[data-rv-ja="bakgrund"]').click();
    await page.locator('[data-rv-ja="klona"]').waitFor();
    assert.match(await page.locator('#rv .rv-steg').textContent(), /kunder\/beta\/kundrepo/);
    await bild('klona');
    await page.locator('[data-rv-ja="klona"]').click();
    await page.waitForFunction(() => location.hash === '#/andringar/beta');
    await page.locator('#an-lage').filter({ hasText: 'Repo kund-beta' }).waitFor();
    await page.locator('[data-an-starta]').waitFor();
    assert.equal(await page.locator('.an-hinder').count(), 0, 'förkontrollen är grön efter klonen');
    const la = await lage('alfa');
    assert(la.session.lever && la.session.pid === pid, 'alfas agent arbetar vidare i bakgrunden, samma process');
    // Senast öppnade, och tillbaka till alfa: samma agent, ingen andra
    await oppnaMedKnapp();
    assert.deepEqual((await grupper())[0], ['Senast öppnade', ['kund-beta', 'kund-alfa']]);
    await page.locator('#rv-sok').fill('alfa'); await page.keyboard.press('Enter');
    await page.waitForFunction(() => location.hash === '#/andringar/alfa');
    await vantaText('redo.');
    assert.equal((await lage('alfa')).session.pid, pid, 'samma agentprocess efter bytet tillbaka');
    sammanfattning.byte_lat_arbeta = { samma_process: true, klon: true };

    // ett okopplat repo: aktivt val bland befintliga kunder (namnförslaget först), byte med stopp, koppling och klon
    await page.locator('body').click({ position: { x: 5, y: 5 } });
    await page.keyboard.press('Meta+O');
    await oppnad();
    await page.locator('#rv-sok').fill('gamma'); await page.keyboard.press('Enter');
    await page.locator('#rv-rubrik').filter({ hasText: 'Koppla kund-gamma till en kund' }).waitFor();
    assert.deepEqual(await etiketter(), ['Gamma Måleri (testdata)', 'Ny kund']);
    assert.match(await page.locator('#rv .rv-alt').first().textContent(), /namnförslag/);
    await page.locator('#rv-sok').fill('maleri');
    assert.deepEqual(await etiketter(), ['Gamma Måleri (testdata)'], 'sökningen bortser från diakritiska tecken');
    await page.keyboard.press('Enter');
    await page.locator('[data-rv-ja="stoppa"]').waitFor();
    await page.locator('[data-rv-ja="stoppa"]').click();
    await page.locator('[data-rv-ja="koppla"]').waitFor();
    await bild('koppla');
    assert.equal((await lage('alfa')).session.lever, false, 'agenten är stoppad innan något nytt öppnas');
    await page.locator('[data-rv-ja="koppla"]').click();
    await page.waitForFunction(() => location.hash === '#/andringar/gamma');
    await page.locator('#an-lage').filter({ hasText: 'Repo kund-gamma' }).waitFor();
    assert.equal(await page.locator('.an-hinder').count(), 0, 'förkontrollen är grön efter kopplingen');
    sammanfattning.koppla_och_stopp = true;

    // utgången inloggning: ett besked med åtgärden, ingen tokenruta, arbetskopiorna står kvar
    const cfgfil = resolve(rot, 'fejkgh.json'), cfg = JSON.parse(readFileSync(cfgfil, 'utf-8'));
    writeFileSync(cfgfil, JSON.stringify({ ...cfg, lage: 'utgangen' }));
    await oppnaMedKnapp();
    await page.locator('[data-rv-las-om]').click();
    await page.locator('#rv-besked').filter({ hasText: 'gått ut' }).waitFor();
    assert.match(await page.locator('#rv-besked').textContent(), /gh auth login/);
    assert.equal(await page.locator('#rv input').count(), 1, 'ingen tokenruta');
    assert.deepEqual((await etiketter()).sort(), ['kund-alfa', 'kund-beta', 'kund-gamma'], 'de bundna arbetskopiorna ur kvittona');
    await bild('utgangen');
    writeFileSync(cfgfil, JSON.stringify({ ...cfg, lage: 'ok' }));
    await page.locator('[data-rv-las-om]').click();
    await page.locator('#rv-besked').filter({ hasText: 'omläst' }).waitFor();
    await page.keyboard.press('Escape');
    sammanfattning.utgangen_inloggning = true;

    // kundens sida i portalen har samma knapp
    await page.evaluate(() => { location.hash = '#/kund/alfa'; });
    await page.locator('.pt-rubrikrad [data-rv-oppna]').waitFor();
    await page.locator('.pt-rubrikrad [data-rv-oppna]').click();
    await page.locator('#rv').waitFor();
    await page.keyboard.press('Escape');

    // hämta och uppdatera i Ändringar: läget före och efter, bara framåt
    await page.evaluate(() => { location.hash = '#/andringar/alfa'; });
    await page.locator('[data-an-hamta]').waitFor();
    await page.locator('[data-an-hamta]').click();
    await page.locator('#an-notis').filter({ hasText: 'Hämtat från origin/main' }).waitFor();
    assert.match(await page.locator('#an-notis').textContent(), /nu 2 efter och 0 före/);
    await page.locator('[data-an-uppdatera]').filter({ hasText: 'Uppdatera (2)' }).waitFor();
    await page.locator('[data-an-uppdatera]').click();
    await page.locator('#an-notis').filter({ hasText: 'Uppdaterad till origin/main (2 commits)' }).waitFor();
    await page.locator('#an-lage').filter({ hasText: 'I takt med origin/main' }).waitFor();
    await bild('uppdaterad');
    sammanfattning.hamta_uppdatera = true;
  }
  assert.deepEqual(sidfel, [], 'inga sidfel');
  console.log(JSON.stringify(sammanfattning));
} finally {
  await browser.close();
}
