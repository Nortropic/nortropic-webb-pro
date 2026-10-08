// stil.mjs — stilrapport för den renderade sajten: typsnitt som faktiskt används, färgfamiljer, radier och kort,
// om nästa sektion skymtar i första vyn, klickytor under 24 px, och de standardval som modellerna själva namnger
// (Anthropic: Prompting Claude Opus 5.5, Frontend design defaults; OpenAI: Frontend prompt instructions), klickbar text som
// bryts på två rader (Hallmark, grind 49), och fem renderade mönster ur impeccables detektorregister (pbakaus/impeccable
// @ 508d7e8, crates/foundation/src/registry.rs: heading-rhythm, monotonous-spacing, side-tab, tiny-text; platt
// typskala ur dess typografiregler), med trösklarna skrivna här.
//   node kontroller/stil.mjs --url=http://127.0.0.1:PORT --sidor=/,/om/ --ut=KATALOG
// Skriver KATALOG/STIL.json och STIL.md. Rapporten är information; klickytorna läses av standardkontrollen (3.3).
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { VYER } from './webblasare/gemensamt.mjs';
import { vakta } from './slugvakt.mjs';

import { viaTjanst, natgrans, lasvakt } from './webblasare/gemensamt.mjs';
await viaTjanst('stil', process.argv.slice(2));  // sandlådat bygge: Chromium kan inte starta i sandlådan, tjänsten kör mätningen
const arg = (n) => process.argv.find((a) => a.startsWith(`--${n}=`))?.slice(n.length + 3);
const base = (arg('url') || '').replace(/\/$/, '');
const sidor = (arg('sidor') || '/').split(',').filter(Boolean);
const ut = arg('ut');
vakta(ut);
if (!base || !ut) { console.error('användning: --url=URL --sidor=/,/a/ --ut=KATALOG'); process.exit(2); }
mkdirSync(ut, { recursive: true });

function matPaSidan() {
  const vh = window.innerHeight;
  const rot = document.querySelector('main') ? 'main' : 'body';  // främmande sajter saknar ofta main
  const rgb = (s) => { const m = (s || '').match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/); return m && (m[4] === undefined || +m[4] > 0.05) ? [+m[1], +m[2], +m[3]] : null; };
  const hex = (c) => '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');
  const familj = (el) => (getComputedStyle(el).fontFamily || '').split(',')[0].replace(/["']/g, '').trim();
  const synlig = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && r.bottom > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0; };
  const typsnitt = {};
  for (const [roll, sel] of [['h1', 'h1'], ['h2', 'h2'], ['brodtext', `${rot} p`], ['knapp', 'a[href^="tel:"], button']]) {
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
  const text = rgb(getComputedStyle(document.querySelector(`${rot} p`) || document.body).color);
  const knapp = document.querySelector(`a[href^="tel:"], button, ${rot} a`);
  const accent = knapp ? (rgb(getComputedStyle(knapp).backgroundColor) || rgb(getComputedStyle(knapp).color)) : null;
  // En gradient räknas som toning bara när två intilliggande stopp har olika färg OCH olika position; hårda stopp
  // (en färg slutar där nästa börjar) är två platta fält (fynd i lulea-snickaren-abx).
  const toning = (bild) => {
    for (const g of bild.match(/(?:repeating-)?(?:linear|radial|conic)-gradient\((.*)\)/g) || []) {
      const stopp = [...g.matchAll(/(rgba?\([^)]*\))\s*([\d.]+(?:%|px))?/g)].map((m) => ({ farg: m[1].replace(/\s/g, ''), pos: m[2] ?? null }));
      for (let i = 1; i < stopp.length; i++) {
        if (stopp[i].farg !== stopp[i - 1].farg && (stopp[i].pos === null || stopp[i].pos !== stopp[i - 1].pos)) return true;
      }
    }
    return false;
  };
  const gradient = [...document.querySelectorAll('body, body *')].some((el) => toning(getComputedStyle(el).backgroundImage));
  // radier och kort
  const radier = new Map();
  const kort = [];
  for (const el of document.querySelectorAll(`${rot} *`)) {
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
  const main = document.querySelector(rot);
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
  // primära handlingar under 44 px (byggstandarden 3.3: primära knappar 44×44): knappar, ring- och mejllänkar och länkar
  // som är stilade som knappar. Vilka som är primära är en bedömning, så detta är information till granskaren, inte fel.
  const smaKnappar = [];
  for (const el of document.querySelectorAll('button, [role="button"], input[type="submit"], a[href^="tel:"], a[href^="mailto:"], a[class*="knapp"], a[class*="btn"], a[class*="button"], a[class*="cta"]')) {
    if (!synlig(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.height >= 44 && r.width >= 44) continue;
    smaKnappar.push({ text: (el.textContent || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 40), bredd: Math.round(r.width), hojd: Math.round(r.height) });
  }
  // sex renderade mönster ur gstacks designkatalog (lib/design-catalog.ts), trösklarna skrivna här
  const tecken = (() => { const c = document.createElement('canvas').getContext('2d'); return (el) => { const s = getComputedStyle(el); c.font = `${s.fontWeight} ${s.fontSize} ${s.fontFamily}`; return c.measureText('abcdefghijklmnopqrstuvwxyzåäö ').width / 30; }; })();
  const stycken = [...document.querySelectorAll(`${rot} p`)].filter((p) => synlig(p) && (p.textContent || '').trim().length > 80);
  const median = (xs) => { const s = [...xs].sort((a, b) => a - b); return s.length ? s[Math.floor(s.length / 2)] : null; };
  const radlangd = median(stycken.map((p) => Math.round(p.getBoundingClientRect().width / tecken(p))));
  const radhojd = median(stycken.map((p) => { const s = getComputedStyle(p); return parseFloat(s.lineHeight) / parseFloat(s.fontSize) || 1.2; }));
  const doltIVila = [...document.querySelectorAll(`${rot} *`)].filter((el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && (s.opacity === '0' || s.visibility === 'hidden') && ((el.textContent || '').trim().length > 20 || el.tagName === 'IMG'); }).length;
  const marginaljusterad = [...document.querySelectorAll(`${rot} p, ${rot} li`)].some((el) => getComputedStyle(el).textAlign === 'justify');
  const textblock = [...document.querySelectorAll(`${rot} p, ${rot} h1, ${rot} h2, ${rot} h3, ${rot} li`)].filter(synlig);
  const centrerad = textblock.length ? textblock.filter((el) => getComputedStyle(el).textAlign === 'center').length / textblock.length : 0;
  const rundade = [...document.querySelectorAll(`${rot} *`)].filter(synlig).map((el) => Math.round(parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0)).filter((r) => r > 0);
  const vanligast = rundade.length ? Math.max(...Object.values(rundade.reduce((m, r) => (m[r] = (m[r] || 0) + 1, m), {}))) : 0;
  const storRadie = rundade.length >= 5 ? Object.entries(rundade.reduce((m, r) => (m[r] = (m[r] || 0) + 1, m), {})).find(([r, n]) => n === vanligast && +r >= 16 && n / rundade.length > 0.8) : null;
  const monster = { radlangd, radhojd: radhojd ? Math.round(radhojd * 100) / 100 : null, doltIVila, marginaljusterad, centrerad: Math.round(centrerad * 100), enStorRadie: storRadie ? +storRadie[0] : null };
  // klickbar text som bryts på två rader (menylänk, knapp, sidfotslänk, brödsmula), utom länkar i löpande text
  const tvaRader = [];
  for (const el of document.querySelectorAll('a[href], button')) {
    if (!synlig(el)) continue;
    const s = getComputedStyle(el);
    const forald = el.parentElement;
    const iText = forald && /^(P|SPAN|EM|STRONG|BLOCKQUOTE|FIGCAPTION|TD|DD|SMALL|CITE)$/.test(forald.tagName) && (forald.textContent || '').trim().length > (el.textContent || '').trim().length + 3;
    if (iText || !(el.textContent || '').trim()) continue;
    // raderna räknas på textens egna rutor, så att en knapps minsta höjd eller utfyllnad inte räknas som en rad till
    const radhojd = parseFloat(s.lineHeight) || parseFloat(s.fontSize) * 1.2;
    const omr = document.createRange();
    omr.selectNodeContents(el);
    const toppar = [...omr.getClientRects()].filter((r) => r.width > 1 && r.height > 1).map((r) => r.top).sort((a, b) => a - b);
    const rader = toppar.filter((y, i) => i === 0 || y - toppar[i - 1] > radhojd * 0.5).length;
    if (rader > 1) tvaRader.push((el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40));
  }
  // fem mönster ur impeccable
  const mainEl = document.querySelector('main');
  const iMain = mainEl ? [...mainEl.querySelectorAll('*')].filter(synlig) : [];
  //   (1) rubrikrytm: luften ovanför en rubrik ska vara större än luften under den
  let trangaRubriker = 0;
  for (const h of iMain.filter((el) => /^H[23]$/.test(el.tagName))) {
    const fore = h.previousElementSibling, efter = h.nextElementSibling;
    if (!fore || !efter || !synlig(fore) || !synlig(efter)) continue;
    const r = h.getBoundingClientRect();
    if (efter.getBoundingClientRect().top - r.bottom - (r.top - fore.getBoundingClientRect().bottom) >= 12) trangaRubriker++;
  }
  //   (2) enformig luft: samma avstånd överallt
  const luft = [];
  for (const el of iMain) {
    const s = getComputedStyle(el);
    if (!/^(block|flex|grid|list-item)$/.test(s.display)) continue;
    for (const v of [s.marginTop, s.marginBottom, s.paddingTop, s.paddingBottom, s.rowGap]) {
      const px = Math.round((parseFloat(v) || 0) / 4) * 4;
      if (px > 0) luft.push(px);
    }
  }
  const luftAntal = luft.reduce((m, v) => (m[v] = (m[v] || 0) + 1, m), {});
  const vanligastLuft = Math.max(0, ...Object.values(luftAntal));
  const enformigLuft = luft.length >= 10 && Object.keys(luftAntal).length <= 3 && vanligastLuft / luft.length > 0.6 ? +Object.keys(luftAntal).find((k) => luftAntal[k] === vanligastLuft) : null;
  //   (3) platt typskala: största steget mellan två grannstorlekar under 1,25
  const storlekar = [...new Set([...document.querySelectorAll('h1, h2, h3, main p, main li')].filter(synlig).map((el) => Math.round(parseFloat(getComputedStyle(el).fontSize))))].sort((a, b) => a - b);
  const storstaSteg = storlekar.length >= 2 ? Math.max(...storlekar.slice(1).map((v, i) => v / storlekar[i])) : null;
  //   (4) färgad sidkant: tjock färgad kant på en sida av ett element
  const neutral = (c) => { if (!c) return true; const [h, s] = (() => { const [r, g, b] = c.map((v) => v / 255); const mx = Math.max(r, g, b), mn = Math.min(r, g, b); const l = (mx + mn) / 2; return [0, mx === mn ? 0 : (mx - mn) / (l > 0.5 ? 2 - mx - mn : mx + mn)]; })(); return s < 0.15; };
  const sidkanter = [];
  for (const el of iMain) {
    const s = getComputedStyle(el);
    const sidor = ['Left', 'Right', 'Top', 'Bottom'].map((k) => ({ k, w: parseFloat(s['border' + k + 'Width']) || 0, c: rgb(s['border' + k + 'Color']), st: s['border' + k + 'Style'] }));
    const radie = parseFloat(s.borderTopLeftRadius) > 0;
    for (const sd of sidor) {
      const ovriga = Math.max(...sidor.filter((x) => x.k !== sd.k).map((x) => x.w));
      if (sd.st !== 'none' && sd.w >= (radie ? 2 : 3) && sd.w >= 2 * Math.max(ovriga, 0.5) && !neutral(sd.c)) { sidkanter.push(el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.split(' ')[0] : '')); break; }
    }
  }
  //   (5) liten brödtext
  const litenText = [...document.querySelectorAll('main p, main li, main dd')].filter((el) => synlig(el) && (el.textContent || '').trim().length > 20 && parseFloat(getComputedStyle(el).fontSize) < 12).length;
  const impeccable = { trangaRubriker, enformigLuft, luftMatningar: luft.length, storstaSteg: storstaSteg ? Math.round(storstaSteg * 100) / 100 : null, sidkanter: [...new Set(sidkanter)].slice(0, 4), litenText };
  // mobilens första vy och kontaktvägar, uppmätt som underlag (riktningens val, inga varningar; rensningen inför 2.0):
  // sidhuvudets höjd, synlig meny eller hamburgare, eget foto i första skärmen, fast list längst ned med Ring och Skriv
  const huvud = [...document.querySelectorAll('header')].find((h) => synlig(h) && h.getBoundingClientRect().top < 10);
  const menyLankar = huvud ? [...huvud.querySelectorAll('nav a')].filter(synlig).length : 0;
  const hamburgare = !!(huvud && [...huvud.querySelectorAll('button[aria-expanded], button[aria-controls]')].some(synlig));
  const bilder = [...document.querySelectorAll(`${rot} img, ${rot} picture`)].filter(synlig);
  const fotoIForsta = bilder.some((b) => { const r = b.getBoundingClientRect(); return r.top < vh && r.width >= 120 && r.height >= 80; });
  const fasta = [...document.querySelectorAll('body *')].filter((el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return (s.position === 'fixed' || s.position === 'sticky') && synlig(el) && r.bottom >= vh - 2 && r.top > vh / 2; });
  const lankarI = (el) => (el.matches('a[href]') ? [el] : []).concat([...el.querySelectorAll('a[href]')]);
  const fastList = fasta.length ? { ring: fasta.some((el) => lankarI(el).some((a) => a.getAttribute('href').startsWith('tel:'))),
    skriv: fasta.some((el) => lankarI(el).some((a) => /kontakt|forfragan|#skriv/i.test(a.getAttribute('href')))) } : null;
  // menylänkar utanför skärmen (en rad som rullar dold i sidled: varning) och samma handling flera gånger i första vyn (mått)
  const vw = document.documentElement.clientWidth;
  const menyDolda = huvud ? [...huvud.querySelectorAll('nav a')].filter((a) => { const r = a.getBoundingClientRect(); return r.width > 0 && r.height > 0 && (r.right > vw + 1 || r.left < -1); }).map((a) => (a.textContent || '').trim()) : [];
  const iForsta = [...document.querySelectorAll('a[href]')].filter((a) => { const r = a.getBoundingClientRect(); return synlig(a) && r.top < vh && r.bottom > 0 && r.left < vw && r.right > 0; });
  const telIForsta = iForsta.filter((a) => a.getAttribute('href').startsWith('tel:')).length;
  const perHref = {};
  for (const a of iForsta) {
    const h = a.getAttribute('href');
    if (h.startsWith('tel:') || h.startsWith('#') || (huvud && huvud.contains(a) && a.closest('nav'))) continue;
    perHref[h] = (perHref[h] || 0) + 1;
  }
  const dubbla = Object.entries(perHref).filter(([, n]) => n >= 2).map(([h]) => h);
  const mobil = { sidhuvud: huvud ? Math.round(huvud.getBoundingClientRect().height) : null, menyLankar, hamburgare, bilder: bilder.length, fotoIForsta, fastList, menyDolda, telIForsta, dubbla };
  // text som inte ryms i sin egen ruta (OpenAI:s frontendprompt, kvar omätt; backloggen 2026-10-03): elementets egen text
  // spiller över sin bredd, eller ett enda ord är bredare än rutan (svenska sammansatta ord i knappar och spalter). Dokumentets
  // spill ser inte ett ord som sticker ut ur en knapp med overflow hidden eller en spalt med min-width 0.
  const textRyms = [];
  for (const el of document.querySelectorAll(`${rot} h1, ${rot} h2, ${rot} h3, ${rot} p, ${rot} li, ${rot} td, ${rot} dd, ${rot} figcaption, a[href], button, label`)) {
    if (!synlig(el) || !(el.textContent || '').trim()) continue;
    const r = el.getBoundingClientRect();
    let ord = el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1 ? (el.textContent || '').trim().replace(/\s+/g, ' ') : null;
    if (!ord) {
      const re = /\S{8,}/g;
      for (const tn of [...el.childNodes].filter((n) => n.nodeType === 3 && n.textContent.trim())) {
        let m;
        while (!ord && (m = re.exec(tn.textContent))) {
          const rg = document.createRange(); rg.setStart(tn, m.index); rg.setEnd(tn, m.index + m[0].length);
          const b = rg.getBoundingClientRect();
          if (b.width > r.width + 1 || b.right > r.right + 1 || b.left < r.left - 1) ord = m[0];
        }
        if (ord) break;
      }
    }
    if (ord) textRyms.push({ tagg: el.tagName.toLowerCase(), text: ord.slice(0, 40), bredd: Math.round(r.width) });
    if (textRyms.length >= 8) break;
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
    kortRader, kortIKort, nastaSektionTopp: nasta, vyhojd: vh, nastaSkymtar: nasta !== null && nasta < vh - 8, smaYtor, smaKnappar, standardval, monster, mobil, tvaRader, impeccable, textRyms,
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

const grans = await natgrans([base]);  // i tjänstens läge: nätgränsen också för sidans underresurser
const browser = await chromium.launch(grans ? grans.playwright : {});
const matningar = [];
try {
  for (const vy of ['390', '1440']) {
    const ctx = await browser.newContext({ ...VYER[vy], serviceWorkers: 'block' });
    await lasvakt(ctx, [base]);  // läsande: sidans skript får inte skriva till någon sajt (F36, Codex R24)
    for (const sida of sidor) {
      const page = await ctx.newPage();
      try {
        await page.goto(base + sida, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => page.goto(base + sida, { waitUntil: 'load', timeout: 45000 }));
        await page.evaluate(() => document.fonts.ready);
        const m = await page.evaluate(matPaSidan);
        m.familjer = { bakgrund: familjAv(m.bakgrund), accent: m.accent ? familjAv(m.accent) : null };
        matningar.push({ sida, vy, ...m });
      } catch (e) {
        matningar.push({ sida, vy, fel: String(e.message).slice(0, 200) });  // en sida som inte går att mäta fäller inte rapporten
      }
      await page.close();
    }
    await ctx.close();
  }
} finally {
  await browser.close();
  if (grans) await grans.stang();
}
const fel = matningar.filter((r) => r.fel);
const rader = matningar.filter((r) => !r.fel);

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
for (const r of rader) {
  const m = r.monster || {};
  const var_ = `${r.sida} @${r.vy}`;
  if (m.doltIVila > 0) varningar.push(`innehåll dolt i vila: ${m.doltIVila} element blir synliga först vid skroll (${var_})`);
  if (m.radlangd && (m.radlangd < 45 || m.radlangd > 75) && r.vy === '1440') varningar.push(`radlängd ${m.radlangd} tecken i brödtext, utanför 45–75 (${var_})`);
  if (m.radhojd && m.radhojd < 1.4) varningar.push(`radhöjd ${m.radhojd} i brödtext, under 1,4 (${var_})`);
  if (m.marginaljusterad) varningar.push(`marginaljusterad text (${var_})`);
  if (m.centrerad > 60) varningar.push(`${m.centrerad} procent av textblocken centrerade (${var_})`);
  if (m.enStorRadie) varningar.push(`en enda stor radie, ${m.enStorRadie} px, på nästan alla rundade element (${var_})`);
}
for (const r of rader) {
  const var_ = `${r.sida} @${r.vy}`;
  if (r.vy === '390' && r.tvaRader?.length) varningar.push(`klickbar text bryts på två rader: ${r.tvaRader.slice(0, 4).map((x) => '"' + x + '"').join(', ')} (${var_})`);
  if (r.vy === '390' && r.textRyms?.length) varningar.push(`text som inte ryms i sin ruta: ${r.textRyms.slice(0, 4).map((x) => '"' + x.text + '" (' + x.tagg + ', ' + x.bredd + ' px)').join(', ')} (${var_})`);
  const im = r.impeccable || {};
  if (im.trangaRubriker >= 2) varningar.push(`${im.trangaRubriker} rubriker står närmare blocket ovanför än sitt eget innehåll (${var_})`);
  if (im.enformigLuft) varningar.push(`enformig luft: ${im.enformigLuft} px står för över 60 procent av ${im.luftMatningar} avstånd (${var_})`);
  if (im.storstaSteg && im.storstaSteg < 1.25) varningar.push(`platt typskala: största steget mellan två textstorlekar är ${im.storstaSteg} (${var_})`);
  if (im.sidkanter?.length) varningar.push(`färgad sidkant på ${im.sidkanter.join(', ')} (${var_})`);
  if (im.litenText) varningar.push(`${im.litenText} textblock under 12 px (${var_})`);
}
const mobilStart = rader.find((r) => r.sida === '/' && r.vy === '390')?.mobil;
if (mobilStart) {
  if (mobilStart.menyDolda?.length) varningar.push(`${mobilStart.menyDolda.length} menylänkar ligger utanför skärmen i 390 (${mobilStart.menyDolda.slice(0, 3).map((x) => '"' + x + '"').join(', ')}): en rad som rullar dold i sidled; korta etiketterna eller lägg menyn på två rader`);
}
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
const smaKnappar = rader.filter((r) => r.vy === '390').flatMap((r) => (r.smaKnappar || []).map((y) => ({ sida: r.sida, ...y })));
const toppsektion = rader.filter((r) => r.sida === '/').map((r) => ({ vy: r.vy, h1: r.typsnitt.h1, nastaSektionTopp: r.nastaSektionTopp, vyhojd: r.vyhojd }));
writeFileSync(join(ut, 'STIL.json'), JSON.stringify({ base, tid: new Date().toISOString(), sammanfattning, toppsektion, varningar, smaYtor, smaKnappar, fel, rader }, null, 1) + '\n');
const md = ['# Stilrapport', '', 'Information, ingen grind. Varningarna är val att motivera ur verksamhetens material, inte förbud.', '',
  `- Typsnitt: ${sammanfattning.typsnitt.join(', ') || '-'} (rubriker: ${sammanfattning.rubriktypsnitt.join(', ') || '-'})`,
  `- Bakgrund: ${sammanfattning.bakgrund.join(', ')} (${bgFam.join(', ')}); accent: ${sammanfattning.accent.join(', ') || '-'}`,
  `- Radier: ${sammanfattning.radier.join(', ') || 'inga'} px`, '',
  '## Radlängd och radhöjd i brödtext', '', '| Sida | Vy | Radlängd, tecken | Radhöjd |', '|---|---|---|---|',
  ...rader.map((r) => `| ${r.sida} | ${r.vy} | ${r.monster?.radlangd ?? '-'} | ${r.monster?.radhojd ?? '-'} |`), '',
  '## Mobilens första vy (startsidan, 390)', '',
  ...(mobilStart ? [`- Sidhuvud: ${mobilStart.sidhuvud ?? '-'} px; meny: ${mobilStart.hamburgare ? 'hamburgare' : mobilStart.menyLankar + ' synliga länkar'}; numret ${mobilStart.telIForsta ?? 0} gånger och ${mobilStart.dubbla?.length ?? 0} upprepade länkar i första vyn`,
    `- Eget foto i första skärmen: ${mobilStart.fotoIForsta ? 'ja' : 'nej'} (${mobilStart.bilder} bilder i main)`,
    `- Fast list längst ned: ${mobilStart.fastList ? [mobilStart.fastList.ring && 'Ring', mobilStart.fastList.skriv && 'Skriv'].filter(Boolean).join(' och ') || 'utan Ring och Skriv' : 'ingen'}`] : ['- startsidan mättes inte']), '',
  '## Varningar', '', ...(varningar.length ? varningar.map((v) => '- ' + v) : ['Inga.']), '',
  '## Klickytor under 24 px i 390 (byggstandarden 3.3)', '', ...(smaYtor.length ? smaYtor.map((y) => `- ${y.sida}: "${y.text}" ${y.bredd}×${y.hojd}`) : ['Inga.']), '',
  '## Knappar, ring- och mejllänkar under 44 px i 390 (byggstandarden 3.3, primära knappar; granskaren avgör vilka som är primära)', '',
  ...(smaKnappar.length ? smaKnappar.map((y) => `- ${y.sida}: "${y.text}" ${y.bredd}×${y.hojd}`) : ['Inga.']), ''];
writeFileSync(join(ut, 'STIL.md'), md.join('\n'));
console.log(`stil: ${rader.length} mätningar, ${fel.length} fel, ${varningar.length} varningar, ${smaYtor.length} små klickytor`);
