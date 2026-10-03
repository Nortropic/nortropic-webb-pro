// ikoner.mjs — apple-touch-icon (180×180) ur sajtens favicon.svg och delningsbild (1200×630) ur ett av verksamhetens
// egna foton, för byggstandarden 2.3 och 7.1. Renderas i Chromium (Playwright), inga andra beroenden.
//   node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <egen bild> [--bakgrund '#1b1b1b'] [--fokus 'center 30%']
// Skriver <sajt>/public/apple-touch-icon.png och <sajt>/public/delningsbild.png. --bakgrund är ikonens bakgrund (iOS
// fyller genomskinligt med svart). --fokus är CSS object-position för beskärningen av fotot. Exit 0 = båda skrivna.
import { existsSync, readFileSync, mkdirSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { chromium } from 'playwright';
import { vakta } from './slugvakt.mjs';

const arg = (n, std) => { const i = process.argv.indexOf('--' + n); return i >= 0 ? process.argv[i + 1] : std; };
const sajt = arg('sajt');
// sajten själv genomgås inte (node_modules är för stor); de faktiska skrivmålen prövas nedan (omgång sex, F1)
const foto = arg('foto');
const bakgrund = arg('bakgrund', '#ffffff');
const fokus = arg('fokus', 'center');
if (!sajt || !foto) { console.error("användning: node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <egen bild> [--bakgrund '#hex'] [--fokus 'center 30%']"); process.exit(2); }
const pub = resolve(sajt, 'public');
vakta(pub, 'public-katalogen');  // det faktiska skrivmålet: en symlänkad public får inte leda till ett annat bygge (omgång fem, F1)
vakta(join(pub, 'apple-touch-icon.png'), 'ikonfilen');
vakta(join(pub, 'delningsbild.png'), 'delningsbilden');
const favicon = join(pub, 'favicon.svg');
if (!existsSync(favicon)) { console.error('saknar ' + favicon + ' — skriv verksamhetens favicon som SVG först'); process.exit(2); }
if (!existsSync(foto)) { console.error('saknar fotot ' + foto); process.exit(2); }
if (!/^#[0-9a-fA-F]{3,8}$/.test(bakgrund)) { console.error('--bakgrund ska vara en hexfärg'); process.exit(2); }
if (!/^[a-z0-9% .-]+$/i.test(fokus)) { console.error('--fokus ska vara en CSS object-position, t.ex. center 30%'); process.exit(2); }

const TYP = { '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.avif': 'image/avif' };
const data = (f) => `data:${TYP[extname(f).toLowerCase()] || 'application/octet-stream'};base64,${readFileSync(f).toString('base64')}`;
mkdirSync(pub, { recursive: true });

const browser = await chromium.launch();
try {
  const sida = await browser.newPage({ viewport: { width: 180, height: 180 }, deviceScaleFactor: 1 });
  // Ikonen: märket centrerat med luft runt om, på en hel bakgrund.
  await sida.setContent(`<html><body style="margin:0;background:${bakgrund};display:grid;place-items:center;width:180px;height:180px">
    <img src="${data(favicon)}" style="width:136px;height:136px;object-fit:contain"></body></html>`);
  await sida.waitForLoadState('load');
  await sida.screenshot({ path: join(pub, 'apple-touch-icon.png'), clip: { x: 0, y: 0, width: 180, height: 180 } });
  await sida.setViewportSize({ width: 1200, height: 630 });
  await sida.setContent(`<html><body style="margin:0;background:${bakgrund}">
    <img src="${data(foto)}" style="display:block;width:1200px;height:630px;object-fit:cover;object-position:${fokus}"></body></html>`);
  await sida.waitForLoadState('load');
  await sida.screenshot({ path: join(pub, 'delningsbild.png'), clip: { x: 0, y: 0, width: 1200, height: 630 } });
  console.log('skrev ' + join(pub, 'apple-touch-icon.png') + ' (180×180) och ' + join(pub, 'delningsbild.png') + ' (1200×630)');
} finally {
  await browser.close();
}
