// Lighthouse (pinnad) på varje sida, mobil och desktop. Generell form av kund-demo-norrglanta/scripts/prov/lighthouse.mjs.
//   node kontroller/lighthouse.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG
// Krav (planen 2026-10-01): prestanda ≥ 90, tillgänglighet ≥ 95, bästa praxis ≥ 95, SEO ≥ 90 i båda formerna.
// Chrome: CHROME_PATH, annars systemets Google Chrome, annars Playwrights chromium.
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as chromeLauncher from 'chrome-launcher';
import lighthouse from 'lighthouse';
import desktopConfig from 'lighthouse/core/config/desktop-config.js';
import { chromium } from 'playwright';

const arg = (namn) => process.argv.find((a) => a.startsWith(`--${namn}=`))?.slice(namn.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG'); process.exit(2); }

const SYSTEM = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const chromePath = process.env.CHROME_PATH || (existsSync(SYSTEM) ? SYSTEM : chromium.executablePath());
const require = createRequire(import.meta.url);
const lhVersion = JSON.parse(readFileSync(require.resolve('lighthouse/package.json'), 'utf8')).version;
const KRAV = { prestanda: 90, tillganglighet: 95, bastaPraxis: 95, seo: 90 };
const slug = (s) => (s === '/' ? 'hem' : s.replace(/^\/|\/$/g, '').replaceAll('/', '-'));

mkdirSync(ut, { recursive: true });
const profil = mkdtempSync(join(tmpdir(), 'nwp-lh-'));
const chrome = await chromeLauncher.launch({ chromePath, userDataDir: profil, chromeFlags: ['--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-extensions'] });
const rader = [];
try {
  for (const form of ['mobil', 'desktop']) {
    for (const sida of sidor) {
      const runner = await lighthouse(base + sida, { port: chrome.port, output: 'json', logLevel: 'error' }, form === 'desktop' ? desktopConfig : undefined);
      const lhr = runner.lhr;
      writeFileSync(join(ut, `${slug(sida)}-${form}.json`), runner.report);
      const p = (id) => Math.round((lhr.categories[id]?.score ?? 0) * 100);
      const underkanda = Object.values(lhr.audits).filter((x) => x.score !== null && x.score < 0.9 && x.scoreDisplayMode !== 'informative' && x.scoreDisplayMode !== 'notApplicable' && x.scoreDisplayMode !== 'manual').map((x) => x.id);
      const rad = {
        sida, form,
        prestanda: p('performance'), tillganglighet: p('accessibility'), bastaPraxis: p('best-practices'), seo: p('seo'),
        lcpMs: Math.round(lhr.audits['largest-contentful-paint']?.numericValue ?? 0),
        cls: +(lhr.audits['cumulative-layout-shift']?.numericValue ?? 0).toFixed(3),
        tbtMs: Math.round(lhr.audits['total-blocking-time']?.numericValue ?? 0),
        underkanda, varningar: lhr.runWarnings,
      };
      rad.ok = rad.prestanda >= KRAV.prestanda && rad.tillganglighet >= KRAV.tillganglighet && rad.bastaPraxis >= KRAV.bastaPraxis && rad.seo >= KRAV.seo;
      rader.push(rad);
      console.log(form, sida, 'P', rad.prestanda, 'A', rad.tillganglighet, 'BP', rad.bastaPraxis, 'SEO', rad.seo, rad.ok ? 'ok' : 'UNDER KRAV: ' + underkanda.join(','));
    }
  }
} finally {
  await chrome.kill();
  rmSync(profil, { recursive: true, force: true });
}
const ok = rader.length > 0 && rader.every((r) => r.ok);
writeFileSync(join(ut, 'lighthouse.json'), JSON.stringify({ base, lighthouseVersion: lhVersion, chromePath, tid: new Date().toISOString(), krav: KRAV, ok, rader }, null, 1) + '\n');
console.log(`Lighthouse ${lhVersion}: ${ok ? 'alla sidor når kraven' : 'minst en sida under kraven'}`);
process.exitCode = ok ? 0 : 1;
