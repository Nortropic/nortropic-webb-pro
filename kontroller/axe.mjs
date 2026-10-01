// axe-core (pinnad) på varje sida i mobil och desktop, plus en adress som inte finns.
// Generell form av kund-demo-norrglanta/scripts/prov/axe.mjs: sidorna ges som argument, inga kundspecifika selektorer.
//   node kontroller/axe.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG
// Exit 0 när inga överträdelser med påverkan serious eller critical finns; 1 annars; 2 vid fel i anropet.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { chromium } from 'playwright';

const arg = (namn) => process.argv.find((a) => a.startsWith(`--${namn}=`))?.slice(namn.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG'); process.exit(2); }

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const axeVersion = JSON.parse(readFileSync(require.resolve('axe-core/package.json'), 'utf8')).version;
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'];
const ALLVARLIG = new Set(['serious', 'critical']);
const VYER = {
  mobil: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
};

mkdirSync(ut, { recursive: true });
const rader = [];
const browser = await chromium.launch();
try {
  for (const [vy, opt] of Object.entries(VYER)) {
    const ctx = await browser.newContext({ ...opt, locale: 'sv-SE', reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    for (const sida of [...sidor, '/finns-inte-nwp']) {
      const svar = await page.goto(base + sida, { waitUntil: 'networkidle' });
      await page.evaluate(axeSource);
      const r = await page.evaluate(async (tags) => {
        const x = await window.axe.run(document, { runOnly: { type: 'tag', values: tags }, resultTypes: ['violations', 'incomplete'] });
        const smal = (l) => l.map((v) => ({ id: v.id, impact: v.impact, help: v.help, noder: v.nodes.slice(0, 5).map((n) => ({ target: n.target, sammanfattning: n.failureSummary })) }));
        return { overtradelser: smal(x.violations), ofullstandiga: smal(x.incomplete), godkanda: x.passes.length };
      }, TAGS);
      rader.push({ vy, sida, http: svar?.status() ?? null, ...r });
    }
    await ctx.close();
  }
} finally {
  await browser.close();
}
const allvarliga = rader.reduce((n, r) => n + r.overtradelser.filter((v) => ALLVARLIG.has(v.impact)).length, 0);
const totalt = rader.reduce((n, r) => n + r.overtradelser.length, 0);
for (const r of rader) {
  if (r.overtradelser.length) console.log(r.vy, r.sida, r.overtradelser.map((v) => `${v.id}(${v.impact})`).join(', '));
}
writeFileSync(join(ut, 'axe.json'), JSON.stringify({ base, axeVersion, tags: TAGS, tid: new Date().toISOString(), allvarliga, totalt, rader }, null, 1) + '\n');
console.log(`axe-core ${axeVersion}: ${allvarliga} allvarliga (serious/critical) av ${totalt} överträdelser i ${rader.length} lägen`);
process.exitCode = allvarliga === 0 ? 0 : 1;
