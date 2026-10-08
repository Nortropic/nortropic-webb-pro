// ikoner.mjs — apple-touch-icon (180×180) ur sajtens favicon.svg och delningsbild (1200×630) ur ett av verksamhetens
// egna foton, för byggstandarden 2.3 och 7.1. Renderas i Chromium (Playwright), inga andra beroenden.
//   node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <egen bild> [--bakgrund '#1b1b1b'] [--fokus 'center 30%']
//        [--logga <png-logga på vit bakgrund> [--loggfarg '#hex']]
// Skriver <sajt>/public/apple-touch-icon.png och <sajt>/public/delningsbild.png. --logga: en logga som bara finns som PNG på
// vit bakgrund (Holm 2026-10-03) får den vita bakgrunden borttagen (luminans, mjuka kanter bevaras), valfritt omfärgad till
// --loggfarg, och skrivs som <sajt>/public/logga-genomskinlig.png och <sajt>/public/favicon.svg (PNG:n inbäddad); favicon.svg
// behöver då inte finnas i förväg. --bakgrund är ikonens bakgrund (iOS
// fyller genomskinligt med svart). --fokus är CSS object-position för beskärningen av fotot. Exit 0 = båda skrivna.
import { existsSync, readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { extname, join, resolve } from 'node:path';
import { chromium } from 'playwright';
import { vakta } from './slugvakt.mjs';

import { viaTjanst, natgrans, lasvakt } from './webblasare/gemensamt.mjs';
import { inom } from './slugvakt.mjs';
await viaTjanst('ikoner', process.argv.slice(2));  // sandlådat bygge: Chromium kan inte starta i sandlådan, tjänsten ritar ikonerna
const arg = (n, std) => { const i = process.argv.indexOf('--' + n); return i >= 0 ? process.argv[i + 1] : std; };
const sajt = arg('sajt');
// sajten själv genomgås inte (node_modules är för stor); de faktiska skrivmålen prövas nedan (omgång sex, F1)
const foto = arg('foto');
const bakgrund = arg('bakgrund', '#ffffff');
const fokus = arg('fokus', 'center');
const logga = arg('logga');
const loggfarg = arg('loggfarg', '');
if (!sajt || !foto) { console.error("användning: node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <egen bild> [--bakgrund '#hex'] [--fokus 'center 30%']"); process.exit(2); }
const pub = resolve(sajt, 'public');
vakta(pub, 'public-katalogen');  // det faktiska skrivmålet: en symlänkad public får inte leda till ett annat bygge (omgång fem, F1)
vakta(join(pub, 'apple-touch-icon.png'), 'ikonfilen');
vakta(join(pub, 'delningsbild.png'), 'delningsbilden');
const favicon = join(pub, 'favicon.svg');
if (!existsSync(favicon) && !logga) { console.error('saknar ' + favicon + ' — skriv verksamhetens favicon som SVG först, eller ge --logga <png>'); process.exit(2); }
if (logga && !existsSync(logga)) { console.error('saknar loggan ' + logga); process.exit(2); }
if (logga && !/\.png$/i.test(logga)) { console.error('--logga ska vara en PNG'); process.exit(2); }
if (loggfarg && !/^#[0-9a-fA-F]{6}$/.test(loggfarg)) { console.error('--loggfarg ska vara en hexfärg med sex tecken'); process.exit(2); }
if (logga) { vakta(logga, 'loggan'); vakta(favicon, 'favicon'); vakta(join(pub, 'logga-genomskinlig.png'), 'den genomskinliga loggan'); }
if (!existsSync(foto)) { console.error('saknar fotot ' + foto); process.exit(2); }
if (!/^#[0-9a-fA-F]{3,8}$/.test(bakgrund)) { console.error('--bakgrund ska vara en hexfärg'); process.exit(2); }
if (!/^[a-z0-9% .-]+$/i.test(fokus)) { console.error('--fokus ska vara en CSS object-position, t.ex. center 30%'); process.exit(2); }
inom(sajt, 'sajtkatalogen'); vakta(foto, 'fotot');  // sajten prövas utan trädgenomgång (node_modules); fotot som läskälla (Codex R24/R25)

const TYP = { '.svg': 'image/svg+xml', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.avif': 'image/avif' };
const data = (f) => `data:${TYP[extname(f).toLowerCase()] || 'application/octet-stream'};base64,${readFileSync(f).toString('base64')}`;
mkdirSync(pub, { recursive: true });

const grans = await natgrans([]);  // i tjänstens läge: inga nätanrop alls utanför domänpolicyn
const browser = await chromium.launch(grans ? grans.playwright : {});
try {
  const ctx = await browser.newContext({ viewport: { width: 180, height: 180 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
  await lasvakt(ctx, []);  // inga nätanrop: bara data-adresser
  const sida = await ctx.newPage();
  if (logga) {
    // Vit bakgrund bort: alfa ur luminansen (helt vitt blir genomskinligt, kanterna mjuka); färgen byts när --loggfarg ges.
    await sida.setContent('<html><body></body></html>');
    const ut = await sida.evaluate(async ([src, farg]) => {
      const img = new Image(); img.src = src; await img.decode();
      const c = document.createElement('canvas'); c.width = img.naturalWidth; c.height = img.naturalHeight;
      const x = c.getContext('2d'); x.drawImage(img, 0, 0);
      const d = x.getImageData(0, 0, c.width, c.height); const p = d.data; let bort = 0, kvar = 0;
      const f = farg ? [1, 3, 5].map((i) => parseInt(farg.slice(i, i + 2), 16)) : null;
      for (let i = 0; i < p.length; i += 4) {
        const lum = 0.299 * p[i] + 0.587 * p[i + 1] + 0.114 * p[i + 2];
        const vithet = Math.max(0, Math.min(1, (lum - 200) / 55));
        const a = Math.round(p[i + 3] * (1 - vithet));
        p[i + 3] = a; if (a === 0) bort++; else kvar++;
        if (f && a > 0) { p[i] = f[0]; p[i + 1] = f[1]; p[i + 2] = f[2]; }
      }
      x.putImageData(d, 0, 0);
      return { png: c.toDataURL('image/png'), bort, kvar, bredd: c.width, hojd: c.height };
    }, [data(logga), loggfarg]);
    writeFileSync(join(pub, 'logga-genomskinlig.png'), Buffer.from(ut.png.split(',')[1], 'base64'));
    writeFileSync(favicon, `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ut.bredd} ${ut.hojd}" width="${ut.bredd}" height="${ut.hojd}"><image href="${ut.png}" width="${ut.bredd}" height="${ut.hojd}"/></svg>\n`);
    console.log(`logga: ${ut.bort} genomskinliga och ${ut.kvar} färgade pixlar (${ut.bredd}×${ut.hojd}); skrev ${favicon} och ${join(pub, 'logga-genomskinlig.png')}`);
  }
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
  if (grans) await grans.stang();
}
