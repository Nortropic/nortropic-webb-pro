// Lighthouse (pinnad) på varje sida, mobil och desktop. Generell form av kund-demo-norrglanta/scripts/prov/lighthouse.mjs.
//   node kontroller/lighthouse.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG [--omgangar=3]
//        [--representativa=/,/kontakt/] [--medianformer=mobil,desktop] [--enheter=mobil|desktop|båda]
// Metoden står fast före körningen och skrivs först till METOD.json (Codex helhetsbedömning 2026-10-04, punkt 7;
// Lighthouse om variabilitet: upprepade mätningar och medianen): en representativ sida mäts --omgangar gånger och
// medianen av prestandan gäller; en övrig sida mäts en gång, och hamnar den under kravet mäts den tills --omgangar
// mätningar finns och medianen gäller. Aldrig bästa av flera. Utan --representativa är alla sidor representativa.
// --medianformer begränsar de representativa sidornas upprepade mätningar till de formerna (provet: mobil, den
// strängare och mer varierande; desktop mäts en gång och mäts om under kravet), så att provet ryms i stoppvaktens tid.
// Tillgänglighet, bästa praxis och SEO tas som den lägsta över sidans mätningar, och de underkända granskningarna ur
// alla mätningar. Spridningen (lägst–högst prestanda) och datorns belastning står vid varje rad.
// Prospektanalysen (kontroller/prospekt.py) kör en omgång och bara mobil: en främmande sajt ska mätas, inte nå kravet.
// Krav (planen 2026-10-01): prestanda ≥ 90, tillgänglighet ≥ 95, bästa praxis ≥ 95, SEO ≥ 90 i båda formerna.
// Chrome: CHROME_PATH, annars systemets Google Chrome, annars Playwrights chromium.
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { loadavg, tmpdir } from 'node:os';
import { join } from 'node:path';
import * as chromeLauncher from 'chrome-launcher';
import lighthouse from 'lighthouse';
import desktopConfig from 'lighthouse/core/config/desktop-config.js';
import { chromium } from 'playwright';
import { vakta } from './slugvakt.mjs';
import { viaTjanst, natgrans, natpolicy, arLokal } from './webblasare/gemensamt.mjs';

await viaTjanst('lighthouse', process.argv.slice(2));  // sandlådat bygge: Chrome kan inte starta i sandlådan, tjänsten kör mätningen

const arg = (namn) => process.argv.find((a) => a.startsWith(`--${namn}=`))?.slice(namn.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
vakta(ut);
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG'); process.exit(2); }
if (natpolicy() !== null && !arLokal(base)) { console.error('lighthouse i tjänstens läge mäter bara byggets lokala server (Chrome utan route-vakt)'); process.exit(2); }  // F36, Codex R24
const omgangar = Math.max(1, parseInt(arg('omgangar') || '3', 10) || 3);
const repArg = arg('representativa');
const representativa = new Set(repArg === undefined ? sidor : repArg.split(',').filter(Boolean));
const medianformer = new Set((arg('medianformer') || 'mobil,desktop').split(',').map((x) => x.trim()).filter(Boolean));
const okandaRep = [...representativa].filter((x) => !sidor.includes(x));
if (okandaRep.length) { console.error('--representativa måste vara sidor ur --sidor: ' + okandaRep.join(', ')); process.exit(2); }
const enheter = arg('enheter') || 'båda';
const FORMER = enheter === 'mobil' ? ['mobil'] : enheter === 'desktop' ? ['desktop'] : ['mobil', 'desktop'];

const SYSTEM = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const chromePath = process.env.CHROME_PATH || (existsSync(SYSTEM) ? SYSTEM : chromium.executablePath());
const require = createRequire(import.meta.url);
const lhVersion = JSON.parse(readFileSync(require.resolve('lighthouse/package.json'), 'utf8')).version;
const KRAV = { prestanda: 90, tillganglighet: 95, bastaPraxis: 95, seo: 90 };
const slug = (s) => (s === '/' ? 'hem' : s.replace(/^\/|\/$/g, '').replaceAll('/', '-'));

// medianen: mittvärdet av de sorterade mätningarna; vid jämnt antal det lägre av de två mittersta (aldrig det gynnsammare)
const median = (xs) => { const s = [...xs].sort((a, b) => a - b); return s[Math.floor((s.length - 1) / 2)]; };
const METOD = { omgangar, representativa: [...representativa], medianformer: [...medianformer],  // representativa i given ordning: startsidan, kontaktsidan, tyngsta övriga sidan
  regel: `representativa sidor i ${[...medianformer].join(' och ')}: ${omgangar} mätningar, medianen av prestandan gäller; övriga sidor och former: en mätning, under prestandakravet ${omgangar} mätningar och medianen gäller; aldrig bästa av flera`,
  ovriga: 'tillgänglighet, bästa praxis och SEO: lägsta över sidans mätningar', krav: KRAV, lighthouseVersion: lhVersion };

mkdirSync(ut, { recursive: true });
writeFileSync(join(ut, 'METOD.json'), JSON.stringify({ ...METOD, tid: new Date().toISOString(), sidor, former: FORMER }, null, 1) + '\n');  // före första mätningen
const profil = mkdtempSync(join(tmpdir(), 'nwp-lh-'));
const grans = await natgrans([base]);  // i tjänstens läge: nätgränsen (domänpolicyn) också för sidans underresurser
const chrome = await chromeLauncher.launch({ chromePath, userDataDir: profil, chromeFlags: ['--headless=new', '--no-first-run', '--no-default-browser-check', '--disable-extensions', ...(grans ? grans.chromeFlags : [])] });
const rader = [];
// de första träffarna i en audits detaljer, som text; detaljernas form skiljer sig mellan audits (lista, tabell, inget)
const traffar = (x) => (Array.isArray(x?.details?.items) ? x.details.items : []).slice(0, 3)
  .map((i) => (i && typeof i === 'object' ? String(i.node?.snippet || i.url || i.source?.url || i.label || i.node?.nodeLabel || '') : String(i ?? '')).slice(0, 160))
  .filter(Boolean);
try {
  const mat = async (form, sida) => {
    const runner = await lighthouse(base + sida, { port: chrome.port, output: 'json', logLevel: 'error' }, form === 'desktop' ? desktopConfig : undefined);
    const lhr = runner.lhr;
    const p = (id) => Math.round((lhr.categories[id]?.score ?? 0) * 100);
    const underkanda = Object.values(lhr.audits).filter((x) => x.score !== null && x.score < 0.9 && x.scoreDisplayMode !== 'informative' && x.scoreDisplayMode !== 'notApplicable' && x.scoreDisplayMode !== 'manual')
      // titel, mätvärde och de första träffarna, så att byggaren slipper läsa rapportens JSON själv (backlogposten om Lighthouse-grinden)
      .map((x) => ({ id: x.id, titel: x.title || '', varde: x.displayValue || '', traffar: traffar(x) }));
    const rad = {
      sida, form,
      prestanda: p('performance'), tillganglighet: p('accessibility'), bastaPraxis: p('best-practices'), seo: p('seo'),
      lcpMs: Math.round(lhr.audits['largest-contentful-paint']?.numericValue ?? 0),
      cls: +(lhr.audits['cumulative-layout-shift']?.numericValue ?? 0).toFixed(3),
      tbtMs: Math.round(lhr.audits['total-blocking-time']?.numericValue ?? 0),
      viktByte: Math.round(lhr.audits['total-byte-weight']?.numericValue ?? 0),
      underkanda, varningar: lhr.runWarnings, belastning: +loadavg()[0].toFixed(1),
    };
    rad.ok = rad.prestanda >= KRAV.prestanda && rad.tillganglighet >= KRAV.tillganglighet && rad.bastaPraxis >= KRAV.bastaPraxis && rad.seo >= KRAV.seo;
    return { rad, rapport: runner.report };
  };
  for (const form of FORMER) {
    for (const sida of sidor) {
      // Prestanda varierar med datorns belastning (samma bygge gav P 93 och P 77, fynd 2026-10-01): metoden ovan avgör
      // antalet mätningar, och medianen gäller; varje mätning och belastningen står i resultatet.
      const rep = representativa.has(sida) && medianformer.has(form);
      const matningar = [await mat(form, sida)];
      if (rep || matningar[0].rad.prestanda < KRAV.prestanda) while (matningar.length < omgangar) matningar.push(await mat(form, sida));
      const p = median(matningar.map((m) => m.rad.prestanda));
      const mitt = matningar.find((m) => m.rad.prestanda === p);
      writeFileSync(join(ut, `${slug(sida)}-${form}.json`), mitt.rapport);
      const lagst = (k) => Math.min(...matningar.map((m) => m.rad[k]));
      const rad = { ...mitt.rad, prestanda: p, tillganglighet: lagst('tillganglighet'), bastaPraxis: lagst('bastaPraxis'), seo: lagst('seo'),
        underkanda: [...new Map(matningar.flatMap((m) => m.rad.underkanda).map((u) => [u.id, u])).values()],  // unionen, en gång per audit
        representativ: rep, matt: matningar.length > 1 ? 'median' : 'en mätning',
        spridning: [Math.min(...matningar.map((m) => m.rad.prestanda)), Math.max(...matningar.map((m) => m.rad.prestanda))],
        forsok: matningar.map((m) => ({ prestanda: m.rad.prestanda, tillganglighet: m.rad.tillganglighet, bastaPraxis: m.rad.bastaPraxis, seo: m.rad.seo, lcpMs: m.rad.lcpMs, belastning: m.rad.belastning })) };
      rad.ok = rad.prestanda >= KRAV.prestanda && rad.tillganglighet >= KRAV.tillganglighet && rad.bastaPraxis >= KRAV.bastaPraxis && rad.seo >= KRAV.seo;
      rader.push(rad);
      console.log(form, sida, 'P', rad.prestanda, 'A', rad.tillganglighet, 'BP', rad.bastaPraxis, 'SEO', rad.seo,
        matningar.length > 1 ? `(median av ${matningar.length}, spridning ${rad.spridning.join('–')}, belastning ${rad.belastning})` : '', rad.ok ? 'ok' : 'UNDER KRAV: ' + rad.underkanda.map((u) => u.id).join(','));
    }
  }
} finally {
  await chrome.kill();
  if (grans) await grans.stang();
  rmSync(profil, { recursive: true, force: true });
}
const ok = rader.length > 0 && rader.every((r) => r.ok);
writeFileSync(join(ut, 'lighthouse.json'), JSON.stringify({ base, lighthouseVersion: lhVersion, chromePath, tid: new Date().toISOString(), krav: KRAV, metod: METOD, ok, rader }, null, 1) + '\n');
console.log(`Lighthouse ${lhVersion}: ${ok ? 'alla sidor når kraven' : 'minst en sida under kraven'}`);
process.exitCode = ok ? 0 : 1;
