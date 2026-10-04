// sida.mjs — en webbsida som underlag för kirurgen, sedd som en besökare ser den: full synlig text, skärmbilder i mobil
// och desktop (första vyn och hela sidan), en skrollsekvens som visar hur sidan förändras när man skrollar, och
// designfakta (typsnitt, storlekar, färger). Ingen ursprungsgräns: tredjepartsresurser laddas som hos en vanlig
// besökare. Bara GET och HEAD; inga formulär skickas. Kakrutor stängs, med "neka" före "acceptera".
//   node kontroller/sida.mjs 'URL' --ut KATALOG [--skroll 8]
// Skriver KATALOG/SIDA.md (läs först), TEXT.md, mobil-forsta.png, mobil-hela.png, desktop-forsta.png, desktop-hela.png
// och desktop-skroll-NN.png. Exit 0 = skrivet (även om sidan spärrade; då står det i SIDA.md), 2 = fel i anropet.
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { vakta } from './slugvakt.mjs';

import { viaTjanst, natgrans, lasvakt } from './webblasare/gemensamt.mjs';
await viaTjanst('sida', process.argv.slice(2));  // sandlådad session (granskare i egen sandlåda): tjänsten kör sidan utanför
const argv = process.argv.slice(2);
const url = argv.find((a) => /^https?:\/\//.test(a));
const flagga = (n, std) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : std; };
const ut = flagga('ut');
vakta(ut);
const antalSkroll = Math.max(0, Math.min(20, parseInt(flagga('skroll', '8'), 10) || 0));
if (!url || !ut) { console.error("användning: node kontroller/sida.mjs 'URL' --ut KATALOG [--skroll 8]"); process.exit(2); }
// Utdata får aldrig hamna i repot: en styrd session ska inte kunna skriva över kod som sedan pushas.
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');
if ((resolve(ut) + sep).startsWith(REPO + sep)) { console.error('--ut får inte ligga i repot; använd /tmp/kirurg/…'); process.exit(2); }
mkdirSync(ut, { recursive: true });

const VYER = {
  mobil: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
};
const MAX_HOJD = 14000;
const vanta = (ms) => new Promise((r) => setTimeout(r, ms));
const rapport = { url, tid: new Date().toISOString(), vyer: {}, filer: [], noter: [] };

async function stangKakruta(page) {
  for (const monster of [/neka|avvisa|endast nödvändiga|bara nödvändiga|reject|decline|only necessary|necessary only/i, /acceptera|godkänn|tillåt alla|jag förstår|accept|agree|allow all|got it|ok/i]) {
    const knapp = page.getByRole('button', { name: monster }).first();
    try {
      if (await knapp.isVisible({ timeout: 800 })) { const t = (await knapp.innerText()).trim().slice(0, 40); await knapp.click({ timeout: 2000 }); await vanta(600); return t; }
    } catch { /* ingen sådan knapp */ }
  }
  return null;
}

// Många sajter skrollar i en inre behållare (body overflow hidden). Hitta det element som faktiskt skrollar.
async function hittaSkrollare(page) {
  return page.evaluate(() => {
    const doc = document.scrollingElement || document.documentElement;
    const kand = [doc, ...document.querySelectorAll('body *')].filter((e) => e.scrollHeight > e.clientHeight + 50 &&
      (e === doc || /(auto|scroll|overlay)/.test(getComputedStyle(e).overflowY)) && e.clientHeight > window.innerHeight * 0.5);
    const valt = kand.sort((a, b) => b.scrollHeight - a.scrollHeight)[0] || doc;
    window.__nwpSkrollare = valt;
    return { inre: valt !== doc, hojd: valt.scrollHeight, synlig: valt === doc ? window.innerHeight : valt.clientHeight };
  });
}
const skrollaTill = (page, y) => page.evaluate((yy) => { const s = window.__nwpSkrollare || document.scrollingElement; s.scrollTo ? s.scrollTo({ top: yy, behavior: 'instant' }) : (s.scrollTop = yy); }, y);

async function skrollaIgenom(page, s) {
  for (let y = 0; y < Math.min(s.hojd, MAX_HOJD); y += s.synlig * 0.8) { await skrollaTill(page, y); await vanta(250); }
  await skrollaTill(page, 0);
  await vanta(500);
}

async function skrollsekvens(page, vy, s, antal) {
  const max = Math.min(s.hojd, MAX_HOJD) - s.synlig;
  for (let i = 0; i < antal && max > 0; i++) {
    const y = Math.round((max * i) / Math.max(antal - 1, 1));
    await skrollaTill(page, y);
    await vanta(700);
    const f = join(ut, `${vy}-skroll-${String(i + 1).padStart(2, '0')}.png`);
    await page.screenshot({ path: f });
    rapport.filer.push([f, `${vy}, skrollad till ${y} px (${Math.round((100 * y) / Math.max(s.hojd, 1))} %): visar hur sidan förändras vid skroll`]);
  }
}

const grans = await natgrans([url]);  // i tjänstens läge: tredjepartsresurser bara inom domänpolicyn
const browser = await chromium.launch(grans ? grans.playwright : {});
try {
  for (const [vy, opt] of Object.entries(VYER)) {
    const ctx = await browser.newContext({ ...opt, locale: 'sv-SE', timezoneId: 'Europe/Stockholm', serviceWorkers: 'block',
      userAgent: vy === 'mobil' ? undefined : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36' });
    await lasvakt(ctx, []);  // bara läsande anrop, inga WebSockets; i tjänstens läge dessutom domänpolicyn (ingen ursprungsgräns annars)
    const page = await ctx.newPage();
    const info = {};
    try {
      const svar = await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => page.goto(url, { waitUntil: 'load', timeout: 45000 }));
      info.http = svar?.status() ?? null;
      info.slutadress = page.url();
      await vanta(1500);
      info.kakruta = await stangKakruta(page);
      const f = join(ut, `${vy}-forsta.png`);
      await page.screenshot({ path: f });
      rapport.filer.push([f, `${vy}, första vyn (${opt.viewport.width} px)`]);
      const s = await hittaSkrollare(page);
      info.hojd = s.hojd;
      info.inre_skroll = s.inre;
      await skrollaIgenom(page, s);
      if (!s.inre) {
        const h = join(ut, `${vy}-hela.png`);
        await page.screenshot({ path: h, fullPage: info.hojd <= MAX_HOJD, clip: info.hojd > MAX_HOJD ? { x: 0, y: 0, width: opt.viewport.width, height: MAX_HOJD } : undefined });
        rapport.filer.push([h, `${vy}, hela sidan${info.hojd > MAX_HOJD ? ` (första ${MAX_HOJD} px av ${info.hojd})` : ''}`]);
      } else if (vy === 'mobil') {
        rapport.noter.push('sidan skrollar i en inre behållare; hela-bilden ersätts av skrollsekvenser');
        await skrollsekvens(page, vy, s, Math.min(6, Math.max(antalSkroll, 3)));
        await skrollaTill(page, 0);
      }
      if (vy === 'desktop') {
        info.meta = await page.evaluate(() => ({
          titel: document.title,
          beskrivning: document.querySelector('meta[name=description]')?.content || null,
          sprak: document.documentElement.lang || null,
          bilder: document.images.length, lankar: document.links.length,
          sektioner: document.querySelectorAll('section, main > div, main > article').length,
        }));
        info.design = await page.evaluate(() => {
          const stil = (sel) => { const el = document.querySelector(sel); if (!el) return null; const c = getComputedStyle(el);
            return { typsnitt: c.fontFamily.split(',')[0].replace(/["']/g, '').trim(), storlek: c.fontSize, vikt: c.fontWeight, radhojd: c.lineHeight, farg: c.color, versaler: c.textTransform === 'uppercase' || undefined, spatiering: c.letterSpacing !== 'normal' ? c.letterSpacing : undefined }; };
          const rakna = {};
          for (const el of Array.from(document.querySelectorAll('body *')).slice(0, 4000)) {
            const c = getComputedStyle(el); const r = el.getBoundingClientRect(); const yta = r.width * r.height;
            if (yta < 400) continue;
            for (const v of [c.backgroundColor, c.color]) { if (v && v !== 'rgba(0, 0, 0, 0)') rakna[v] = (rakna[v] || 0) + (v === c.backgroundColor ? yta : yta / 20); }
          }
          return {
            typsnitt_laddade: Array.from(new Set(Array.from(document.fonts).filter((f) => f.status === 'loaded').map((f) => f.family.replace(/["']/g, '')))).slice(0, 10),
            body: stil('body'), h1: stil('h1'), h2: stil('h2'), p: stil('p'), a: stil('a'), knapp: stil('button, .button, .btn, a[class*=button]'),
            bakgrund: getComputedStyle(document.body).backgroundColor,
            farger_mest: Object.entries(rakna).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k]) => k),
          };
        });
        const text = await page.evaluate(() => document.body.innerText);
        writeFileSync(join(ut, 'TEXT.md'), `# Synlig text: ${url}\n\n${text.slice(0, 80000)}\n`);
        rapport.filer.push([join(ut, 'TEXT.md'), 'hela den synliga texten (desktop)']);
        await skrollsekvens(page, vy, s, antalSkroll);
      }
    } catch (e) {
      info.fel = String(e.message || e).split('\n')[0].slice(0, 300);
      rapport.noter.push(`${vy}: ${info.fel}`);
    }
    rapport.vyer[vy] = info;
    await ctx.close();
  }
} finally {
  await browser.close();
  if (grans) await grans.stang();
}

const d = rapport.vyer.desktop?.design;
const m = rapport.vyer.desktop?.meta;
const rad = (o) => (o ? Object.entries(o).filter(([, v]) => v !== undefined).map(([k, v]) => `${k} ${v}`).join(', ') : '–');
const md = [
  `# Sidan sedd som besökare: ${url}`, '',
  `- Hämtad: ${rapport.tid}`,
  ...Object.entries(rapport.vyer).map(([vy, i]) => `- ${vy}: HTTP ${i.http ?? '?'}${i.slutadress && i.slutadress !== url ? `, hamnade på ${i.slutadress}` : ''}${i.kakruta ? `, kakruta stängd med "${i.kakruta}"` : ''}${i.hojd ? `, sidhöjd ${i.hojd} px` : ''}${i.fel ? `, FEL: ${i.fel}` : ''}`),
  ...(m ? [`- Titel: ${m.titel}`, `- Beskrivning: ${m.beskrivning ?? '–'}`, `- Språk: ${m.sprak ?? '–'} · bilder ${m.bilder} · länkar ${m.lankar} · sektioner ${m.sektioner}`] : []),
  '', '## Läs bilderna (med Read) — det är här designen syns', '',
  ...rapport.filer.filter(([f]) => f.endsWith('.png')).map(([f, t]) => `- ${f} — ${t}`),
  '', '## Designfakta (beräknade stilar, desktop)', '',
  ...(d ? [`- Laddade typsnitt: ${d.typsnitt_laddade.join(', ') || 'inga webbtypsnitt (systemtypsnitt)'}`, `- Bakgrund: ${d.bakgrund}`,
    `- h1: ${rad(d.h1)}`, `- h2: ${rad(d.h2)}`, `- brödtext: ${rad(d.p)}`, `- länk: ${rad(d.a)}`, `- knapp: ${rad(d.knapp)}`,
    `- Mest använda färger (yta och text): ${d.farger_mest.join(' · ')}`] : ['- (kunde inte läsas)']),
  '', '## Text', '', `- ${join(ut, 'TEXT.md')}`,
  ...(rapport.noter.length ? ['', '## Noter', '', ...rapport.noter.map((n) => `- ${n}`), '- Spärrade sidan (inloggning, robotkontroll)? Skriv det i bedömningen; påstå inget du inte har sett.'] : []),
  '', 'Skärmbilder är stillbilder: skrollsekvensen visar lägen, inte rörelsen mellan dem.',
];
writeFileSync(join(ut, 'SIDA.md'), md.join('\n') + '\n');
console.log(JSON.stringify({ ut: join(ut, 'SIDA.md'), bilder: rapport.filer.filter(([f]) => f.endsWith('.png')).length, fel: rapport.noter }));
