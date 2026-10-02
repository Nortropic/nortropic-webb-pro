// stil.mjs — stilrapport för den renderade sajten: typsnitt som faktiskt används, färgfamiljer, radier och kort,
// om nästa sektion skymtar i första vyn, klickytor under 24 px, och de standardval som modellerna själva namnger
// (Anthropic: Prompting Claude Opus 5.5, Frontend design defaults; OpenAI: Frontend prompt instructions).
//   node kontroller/stil.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG
// Skriver KATALOG/STIL.json och STIL.md. Rapporten är information; klickytorna läses av standardkontrollen (3.3).
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { VYER } from './webblasare/gemensamt.mjs';

const arg = (n) => process.argv.find((a) => a.startsWith(`--${n}=`))?.slice(n.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG'); process.exit(2); }
mkdirSync(ut, { recursive: true });

function matPaSidan() {
  const vh = window.innerHeight;
  const rgb = (s) => { const m = (s || '').match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/); return m && (m[4] === undefined || +m[4] > 0.05) ? [+m[1], +m[2], +m[3]] : null; };
  const hex = (c) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
  const familj = (el) => (getComputedStyle(el).fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
  const synlig = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && r.bottom > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0; };
  const typsnitt = {};
  for (const [roll, sel] of [['h1', 'h1'], ['h2', 'h2'], ['brodtext', 'main p'], ['knapp', 'a[href^="tel:"], button']]) {
    const el = document.querySelector(sel);
    if (el) typsnitt[roll] = { familj: familj(el), storlek: getComputedStyle(el).fontSize, vikt: getComputedStyle(el).fontWeight, stil: getComputedStyle(el).fontStretch };
  }
  // färger: ytor viktade med synlig area, plus textfärg och accent (knappar och länkar)
  const ytor = new Map();
  for (const el of document.querySelectorAll('body, body *')) {
    const c = rgb(getComputedStyle(el).backgroundColor);
    if (!c || !synlig(el)) continue;
    const r = el.getBoundingClientRect();
    const k = hex(c);
    ytor.set(k, (ytor.get(k) || 0) + r.width * Math.min(r.height, 4000));
  }
  const bodyBg = rgb(getComputedStyle(document.body).backgroundColor) || rgb(getComputedStyle(document.documentElement).backgroundColor) || [255, 255, 255];
  const text = rgb(getComputedStyle(document.querySelector('main p') || document.body).color);
  const knapp = document.querySelector('a[href^="tel:"], button, main a');
  const accent = knapp ? (rgb(getComputedStyle(knapp).backgroundColor) || rgb(getComputedStyle(knapp).color)) : null;
  const gradient = [...document.querySelectorAll('body, body *')].some((el) => /gradient\(/.test(getComputedStyle(el).backgroundImage));
  // radier och kort
  const radier = new Map();
  const kort = [];
  for (const el of document.querySelectorAll('main *')) {
    if (!synlig(el)) continue;
    const s = getComputedStyle(el);
    const rad = parseFloat(s.borderTopLeftRadius) || 0;
    const ram = parseFloat(s.borderTopWidth) > 0 || s.boxShadow !== 'none' || (rgb(s.backgroundColor) && hex(rgb(s.backgroundColor)) !== hex(bodyBg));
    const r = el.getBoundingClientRect();
    if (rad > 0 && r.width > 40) radier.set(Math.round(rad), (radier.get(Math.round(rad)) || 0) + 1);
    if (ram && rad > 0 && parseFloat(s.paddingTop) >= 8 && r.width > 120 && r.height > 80) kort.push(el);
  }
  const kortRader = [...new Set(kort.map((k) => k.parentElement))].filter((p) => p && kort.filter((k) => k.parentElement === p).length >= 3).length;
  const kortIKort = kort.filter((k) => kort.some((o) => o !== k && o.contains(k))).length;
  // nästa sektion i första vyn
  const main = document.querySelector('main');
  const block = main ? [...main.children].filter(synlig) : [];
  const nasta = block[1] ? Math.round(block[1].getBoundingClientRect().top) : null;
  // klickytor under 24 px som inte står i löpande text
  const smaYtor = [];
  for (const el of document.querySelectorAll('a[href], button, [role="button"], input:not([type="hidden"]), select, summary')) {
    if (!synlig(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.height >= 24 && r.width >= 24) continue;
    const forald = el.parentElement;
    const egen = (el.textContent || '').trim().length;
    const runt = (forald?.textContent || '').trim().length;
    const iText = forald && /^(P|SPAN|EM|STRONG|BLOCKQUOTE|FIGCAPTION|TD|DD|SMALL|CITE)$/.test(forald.tagName) && runt > egen + 3;
    if (iText) continue;
    smaYtor.push({ text: (el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 40), bredd: Math.round(r.width), hojd: Math.round(r.height) });
  }
  // modellernas namngivna standardval
  const standardval = [];
  const rubriker = [...document.querySelectorAll('h1, h2')];
  if (rubriker.some((h) => h.querySelector('em, i') || [...h.querySelectorAll('span')].some((s) => getComputedStyle(s).fontStyle === 'italic' || getComputedStyle(s).color !== getComputedStyle(h).color))) standardval.push('accentord i rubrik (kursivt eller annan färg)');
  if ([...document.querySelectorAll('body *')].some((el) => el.children.length === 0 && /^\s*0[1-9]\s*(\/|\.|—|–)?\s*$/.test(el.textContent || ''))) standardval.push('numrerade etiketter 01/02/03');
  if ([...document.querySelectorAll('body *')].some((el) => el.children.length === 0 && (el.textContent || '').trim() && /mono/i.test(getComputedStyle(el).fontFamily))) standardval.push('monospace-etiketter');
  if ([...document.querySelectorAll('a, button')].some((el) => { const r = el.getBoundingClientRect(); return synlig(el) && r.height >= 28 && parseFloat(getComputedStyle(el).borderTopLeftRadius) >= r.height / 2 - 1; })) standardval.push('pillerformade knappar');
  if ([...document.querySelectorAll('body *')].some((el) => el.children.length === 0 && (el.textContent || '').trim().length > 2 && getComputedStyle(el).textTransform === 'uppercase' && parseFloat(getComputedStyle(el).letterSpacing) > 0.5 && parseFloat(getComputedStyle(el).fontSize) < 15)) standardval.push('spärrade versaletiketter');
  return {
    typsnitt, ytor: [...ytor.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k]) => k),
    bakgrund: hex(bodyBg), text: text ? hex(text) : null, accent: accent ? hex(accent) : null, gradient,
    radier: [...radier.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(([r, n]) => ({ px: r, antal: n })),
    kortRader, kortIKort, nastaSektionTopp: nasta, vyhojd: vh, nastaSkymtar: nasta !== null && nasta < vh - 8, smaYtor, standardval,
  };
}

// färgfamiljer som leverantörerna varnar för (OpenAI) och Opus 5.5:s egna standardval (Anthropic)
function hsl([r, g, b]) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min, s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  const h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [h * 60, s, l];
}
const frånHex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
function familjAv(h) {
  const [ton, mattnad, ljus] = hsl(frånHex(h));
  if (ljus > 0.93 && mattnad < 0.25) return 'vit';
  if (ljus < 0.12) return 'nära svart';
  if (mattnad < 0.12) return 'grå';
  if (ton >= 30 && ton <= 60 && ljus > 0.8) return 'cream/beige';
  if (ton >= 15 && ton < 40 && ljus <= 0.8) return 'brun/orange';
  if (ton >= 255 && ton <= 300) return 'lila';
  if (ton >= 200 && ton < 255 && ljus < 0.35) return 'mörkblå/skiffer';
  if (ton >= 40 && ton < 70) return 'gul';
  if (ton < 15 || ton >= 340) return 'röd';
  if (ton >= 70 && ton < 170) return 'grön';
  return 'blå';
}

const browser = await chromium.launch();
const rader = [];
try {
  for (const vy of ['390', '1440']) {
    const ctx = await browser.newContext(VYER[vy]);
    for (const sida of sidor) {
      const page = await ctx.newPage();
      await page.goto(base + sida, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const m = await page.evaluate(matPaSidan);
      m.familjer = { bakgrund: familjAv(m.bakgrund), accent: m.accent ? familjAv(m.accent) : null };
      rader.push({ sida, vy, ...m });
      await page.close();
    }
    await ctx.close();
  }
} finally {
  await browser.close();
}

const alla = (f) => [...new Set(rader.flatMap(f).filter(Boolean))];
const varningar = [];
const bgFam = alla((r) => [r.familjer.bakgrund]);
if (bgFam.includes('cream/beige')) varningar.push('cream- eller beigebakgrund (Opus 5.5:s och OpenAI:s namngivna standard)');
if (bgFam.includes('nära svart') && alla((r) => [r.familjer.accent]).some((a) => ['gul', 'grön', 'röd'].includes(a))) varningar.push('nära svart bakgrund med en enda stark accent (namngiven AI-standard)');
if (alla((r) => [r.familjer.bakgrund, r.familjer.accent]).some((f) => ['lila', 'mörkblå/skiffer', 'brun/orange'].includes(f))) varningar.push('färgfamilj som OpenAI varnar för (lila, mörkblå/skiffer eller brun/orange); välj den med skäl ur verksamhetens material');
if (rader.some((r) => r.gradient)) varningar.push('gradient som bakgrund');
for (const s of alla((r) => r.standardval)) varningar.push(s + ' (namngivet standardval)');
if (rader.some((r) => r.kortIKort > 0)) varningar.push('kort i kort');
if (rader.some((r) => r.kortRader > 0)) varningar.push('rader med tre eller fler likadana kort');
const utanSkymt = rader.filter((r) => r.sida === '/' && !r.nastaSkymtar).map((r) => r.vy);
if (utanSkymt.length) varningar.push('nästa sektion skymtar inte i startsidans första vy (' + utanSkymt.join(', ') + ' px)');
const sammanfattning = {
  typsnitt: alla((r) => Object.values(r.typsnitt).map((t) => t.familj)),
  rubriktypsnitt: alla((r) => [r.typsnitt.h1?.familj]),
  bakgrund: alla((r) => [r.bakgrund]), accent: alla((r) => [r.accent]),
  familjer: { bakgrund: bgFam, accent: alla((r) => [r.familjer.accent]) },
  radier: alla((r) => r.radier.map((x) => x.px)).slice(0, 6),
};
const smaYtor = rader.filter((r) => r.vy === '390').flatMap((r) => r.smaYtor.map((y) => ({ sida: r.sida, ...y })));
const toppsektion = rader.filter((r) => r.sida === '/').map((r) => ({ vy: r.vy, h1: r.typsnitt.h1, nastaSektionTopp: r.nastaSektionTopp, vyhojd: r.vyhojd }));
writeFileSync(join(ut, 'STIL.json'), JSON.stringify({ base, tid: new Date().toISOString(), sammanfattning, toppsektion, varningar, smaYtor, rader }, null, 1) + '\n');
const md = ['# Stilrapport', '', 'Information, ingen grind. Varningarna är val att motivera ur verksamhetens material, inte förbud.', '',
  `- Typsnitt: ${sammanfattning.typsnitt.join(', ') || '-'} (rubriker: ${sammanfattning.rubriktypsnitt.join(', ') || '-'})`,
  `- Bakgrund: ${sammanfattning.bakgrund.join(', ')} (${bgFam.join(', ')}); accent: ${sammanfattning.accent.join(', ') || '-'}`,
  `- Radier: ${sammanfattning.radier.join(', ') || 'inga'} px`, '', '## Varningar', '', ...(varningar.length ? varningar.map((v) => '- ' + v) : ['Inga.']), '',
  '## Klickytor under 24 px i 390 (byggstandarden 3.3)', '', ...(smaYtor.length ? smaYtor.map((y) => `- ${y.sida}: "${y.text}" ${y.bredd}×${y.hojd}`) : ['Inga.']), ''];
writeFileSync(join(ut, 'STIL.md'), md.join('\n'));
console.log(`stil: ${rader.length} mätningar, ${varningar.length} varningar, ${smaYtor.length} små klickytor`);
