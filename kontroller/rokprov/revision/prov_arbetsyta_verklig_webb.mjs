// Arbetsytans verkliga prov i webbläsaren (ägarens uppdrag 2026-10-09, acceptansfall 1, 2, 4, 5 och 6): en dashboard ur en
// worktree med testprojektet, riktiga sessioner genom prov_arbetsyta_verklig.py och vyn som ägaren ser den. Körs för hand.
//   node prov_arbetsyta_verklig_webb.mjs <dashboardens adress> <nyckel> <slug> <repo> <bildkatalog>
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
const [bas, nyckel, slug, repo, bilder] = process.argv.slice(2);
const { chromium } = await import(resolve(repo, 'kontroller/node_modules/playwright/index.mjs'));
const logg = [], fel = [];
const notera = (s) => { const t = new Date().toISOString(); logg.push(`${t} ${s}`); console.error(`${t} ${s}`); };
function driv(vad) {
  const p = spawn(resolve(repo, '.venv/bin/python'), ['-B', resolve(repo, 'kontroller/rokprov/revision/prov_arbetsyta_verklig.py'), slug, vad], { cwd: repo });
  const ut = []; p.stdout.on('data', (d) => ut.push(String(d))); p.stderr.on('data', (d) => ut.push(String(d)));
  return { p, klar: new Promise((r) => p.on('exit', (kod) => r({ kod, ut: ut.join('') }))) };
}
const b = await chromium.launch({ headless: true });
const sida = await b.newPage({ viewport: { width: 1672, height: 941 } });
sida.on('pageerror', (e) => fel.push(e.message));
sida.on('console', (m) => { if (m.type() === 'error') fel.push('console: ' + m.text()); });
try {
  await sida.goto(`${bas}/#nyckel=${nyckel}&till=arbetsyta/${slug}`);
  await sida.locator('#ay-roller').getByRole('heading', { name: 'Granskning' }).waitFor();
  const arbetsprov = sida.locator('#ay-roller .ay-session', { hasText: 'förfiningen' });
  assert.equal(await arbetsprov.count(), 0, 'ingen förfining före provet');

  // 1 och 2: en verklig session dyker upp av sig själv, granskningen väntar
  const t0 = Date.now(); const a = driv('arbete'); notera('arbete startat');
  await arbetsprov.first().waitFor({ timeout: 90000 });
  const syns = Date.now() - t0; notera(`sessionen syns i vyn efter ${syns} ms`);
  await sida.locator('#ay-roller .ay-ansvar', { hasText: 'Granskning' }).locator('.ay-lage[data-lage="vantar"]').first().waitFor();
  await sida.screenshot({ path: `${bilder}/verklig-1-arbetar.png` });
  await arbetsprov.first().getByRole('button', { name: 'Följ' }).click();
  await sida.locator('#ay-roller').getByText('Följer:').waitFor();
  await sida.waitForTimeout(8000);
  await sida.screenshot({ path: `${bilder}/verklig-2-foljer.png` });
  const handelser = await sida.locator('#ay-roller .ay-folj ol li').count(); notera(`händelser i följvyn: ${handelser}`);
  const ra = await a.klar; notera(`arbete slut kod ${ra.kod}: ${ra.ut.trim().slice(-300)}`);
  assert.equal(ra.kod, 0, 'utförarens prov ska sluta normalt');
  await sida.locator('#ay-roller .ay-lage[data-lage="avslutad"]').first().waitFor({ timeout: 30000 });

  // 4: omladdning visar samma slutbesked; förhandsvisningen är det ombyggda resultatet
  await sida.reload();
  await sida.locator('#ay-roller .ay-session', { hasText: 'förfiningen' }).first().locator('.ay-lage[data-lage="avslutad"]').waitFor({ timeout: 30000 });
  await sida.waitForTimeout(2500);
  const ram = sida.frames().find((f) => f !== sida.mainFrame() && f.url().startsWith('http://127.0.0.1'));
  const rubrik = ram ? await ram.locator('h1').first().textContent().catch(() => null) : null;
  notera(`förhandsvisningens h1 efter omladdning: ${rubrik}`);
  await sida.screenshot({ path: `${bilder}/verklig-3-resultat.png` });

  // 5 och 6: en session stoppas genom arbetsytans stoppknapp (flödets stoppväg); den visas som avbruten, aldrig godkänd
  const s = driv('stopprov'); notera('stopprov startat');
  const stoppsession = sida.locator('#ay-roller .ay-session', { hasText: 'förfiningen' }).filter({ hasText: /arbetar|väntar på verktyg|start pågår/ });
  await stoppsession.first().waitFor({ timeout: 90000 });
  await sida.getByRole('button', { name: 'Stoppa' }).first().click();
  await sida.locator('#ay-remsa').getByText('Stoppa arbetaren och dess sessioner?').waitFor();
  await sida.screenshot({ path: `${bilder}/verklig-4-bekrafta-stopp.png` });
  await sida.locator('#ay-remsa [data-bekraftad]').click();
  const rs = await s.klar; notera(`stopprov slut kod ${rs.kod}: ${rs.ut.trim().slice(-300)}`);
  await sida.locator('#ay-roller .ay-lage[data-lage="avbruten"]').first().waitFor({ timeout: 30000 });
  await sida.waitForTimeout(2000);
  await sida.screenshot({ path: `${bilder}/verklig-5-stoppad.png` });
  const svar = await sida.locator('#ay-handlingssvar').textContent(); notera(`handlingssvar: ${svar}`);
  console.log(JSON.stringify({ synlig_efter_ms: syns, handelser_i_foljvyn: handelser, arbete_kod: ra.kod, rubrik_efter_omladdning: rubrik,
    stopp_kod: rs.kod, handlingssvar: svar, sidfel: fel, logg }, null, 1));
} finally { await b.close(); }
