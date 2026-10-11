// Motorns sond för studions visuella kontroller (kunskap/designstudio.md, Sonden). Öppnar kandidatens byggda sida i en
// egen huvudlös Chromium med sidans JavaScript avstängt och nätet begränsat till förhandsvisningens ursprung
// (webblasare/gemensamt.mjs, oppna), hittar elementet genom källkartans id och avgör för varje efterfrågad egenskap
// vilken deklaration som vinner kaskaden: varje regel som matchar och sätter egenskapen får tillfälligt ett provvärde,
// och den regel vars provvärde syns i det beräknade värdet är ägaren. Sedan återställs regeln exakt. Regelns källa är
// dess --nwp-r (karta.mjs); en regel utan sådan (Tailwinds verktyg, ett paket i node_modules) har ingen redigerbar källa.
//
// Sidans eget påstående (bryggans markering) används aldrig här: motorn öppnar sidan själv. Utdata är JSON på stdout.
//
//     node kontroller/studio/sond.mjs --url http://127.0.0.1:<port>/ --sida / --bredd 1280 --k <id> [--instans 0]
//          [--barn img:0] --egenskaper font-size,line-height [--prova <json>] [--alla font-size]
//          [--bredder 390,900,1280]   flera bredder i samma webbläsare: {bredder: {<b>: före}, efter: {<b>: med --prova}}
import { oppna, horisontellSpill, args, VYER } from '../webblasare/gemensamt.mjs';

const a = args(process.argv.slice(2));
const bas = String(a.url || '');
const sida = String(a.sida || '/');
const bredd = Number(a.bredd || 1280);
const k = String(a.k || '');
if (!/^https?:\/\/(127\.0\.0\.1|localhost):\d+\/?$/.test(bas) || !sida.startsWith('/') || sida.includes('//') || !/^[0-9a-f]{12}$/.test(k)) {
  console.log(JSON.stringify({ fel: 'ogiltig fråga' }));
  process.exit(2);
}
if (!(bredd >= 280 && bredd <= 2560)) { console.log(JSON.stringify({ fel: 'ogiltig bredd' })); process.exit(2); }
const egenskaper = String(a.egenskaper || '').split(',').map((x) => x.trim()).filter((x) => /^(--)?[a-z][a-z0-9-]*$/.test(x)).slice(0, 40);
const barn = a.barn ? String(a.barn).match(/^(img|picture|video|svg):(\d{1,2})$/) : null;
const prova = a.prova ? JSON.parse(String(a.prova)) : null;
const alla = a.alla ? String(a.alla).split(',').filter((x) => /^[a-z][a-z-]*$/.test(x)).slice(0, 8) : [];

const bredder = a.bredder ? String(a.bredder).split(',').map(Number).filter((x) => x >= 280 && x <= 2560).slice(0, 5) : null;
const vyFor = (b) => (b <= 430 ? '390' : b <= 900 ? '768' : b <= 1360 ? '1280' : '1440');
const url = new URL(sida, bas).href;
const forsta = bredder ? bredder[0] : bredd;
const { page, stang } = await oppna({ vy: vyFor(forsta), tillat: [url], mal: url,
  extra: { javaScriptEnabled: false, viewport: { width: forsta, height: VYER[vyFor(forsta)].viewport.height } } });
const parametrar = (med) => ({ k, instans: Number(a.instans || 0), egenskaper, barn: barn ? [barn[1], Number(barn[2])] : null, prova: med ? prova : null, alla });
async function en(b, med) {
  await page.setViewportSize({ width: b, height: VYER[vyFor(b)].viewport.height });
  const svar = await page.goto(url, { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {});
  const r = await page.evaluate(sondera, parametrar(med));
  r.http = svar ? svar.status() : null;
  r.spill = await horisontellSpill(page);
  r.sida = sida; r.bredd = b;
  return r;
}
let ut;
try {
  if (bredder) {
    ut = { bredder: {}, efter: {} };
    for (const b of bredder) {
      ut.bredder[b] = await en(b, false);
      if (prova) ut.efter[b] = await en(b, true);
    }
  } else {
    ut = await en(bredd, true);
  }
} catch (e) {
  ut = { fel: String(e && e.message || e).slice(0, 300) };
} finally {
  await stang().catch(() => {});
}
console.log(JSON.stringify(ut));

// Körs i sidan. Inga externa beroenden: allt som behövs står här.
function sondera({ k, instans, egenskaper, barn, prova, alla }) {
  const ATTR = 'data-nwp-k';
  const RATTR = '--nwp-r';
  const KORT = {
    'padding-top': ['padding', 'padding-block', 'padding-block-start'], 'padding-bottom': ['padding', 'padding-block', 'padding-block-end'],
    'padding-left': ['padding', 'padding-inline', 'padding-inline-start'], 'padding-right': ['padding', 'padding-inline', 'padding-inline-end'],
    'margin-top': ['margin', 'margin-block', 'margin-block-start'], 'margin-bottom': ['margin', 'margin-block', 'margin-block-end'],
    'margin-left': ['margin', 'margin-inline', 'margin-inline-start'], 'margin-right': ['margin', 'margin-inline', 'margin-inline-end'],
    'row-gap': ['gap'], 'column-gap': ['gap'], 'font-size': ['font'], 'font-family': ['font'], 'font-weight': ['font'], 'line-height': ['font'],
    'background-color': ['background'], 'border-top-left-radius': ['border-radius'],
  };
  const ARVS = new Set(['font-size', 'font-family', 'font-weight', 'line-height', 'letter-spacing', 'color', 'text-align', 'text-transform', 'font-style']);
  const PROV = (p, bas) => {
    if (p.startsWith('--')) return '"nwp-prov"';
    if (/color$/.test(p) || p === 'color') return bas === 'rgb(1, 2, 3)' ? 'rgb(3, 2, 1)' : 'rgb(1, 2, 3)';
    if (p === 'font-family') return '"nwp-prov"';
    if (p === 'font-weight') return bas === '123' ? '321' : '123';
    if (p === 'object-position') return bas === '1% 2%' ? '2% 1%' : '1% 2%';
    if (p === 'aspect-ratio') return bas === '7 / 3' ? '3 / 7' : '7 / 3';
    if (p === 'object-fit') return bas === 'fill' ? 'contain' : 'fill';
    if (p === 'text-align') return bas === 'justify' ? 'right' : 'justify';
    if (p === 'text-transform') return bas === 'lowercase' ? 'uppercase' : 'lowercase';
    if (p === 'grid-template-columns') return '7px 9px';
    if (p === 'order') return bas === '777' ? '778' : '777';
    if (p === 'line-height') return bas === '7.77px' ? '8.88px' : '7.77px';
    return bas === '777.25px' ? '778.25px' : '777.25px';
  };
  const ber = (el, p) => getComputedStyle(el).getPropertyValue(p).trim();
  const regler = [];
  const samla = (lista, ram) => {
    for (const r of lista) {
      if (r instanceof CSSStyleRule) { regler.push({ r, ram }); if (r.cssRules && r.cssRules.length) samla(r.cssRules, ram.concat(['& ' + r.selectorText])); }
      else if (r instanceof CSSMediaRule) samla(r.cssRules, ram.concat(['@media ' + r.conditionText]));
      else if (r instanceof CSSSupportsRule) samla(r.cssRules, ram.concat(['@supports ' + r.conditionText]));
      else if (typeof CSSLayerBlockRule !== 'undefined' && r instanceof CSSLayerBlockRule) samla(r.cssRules, ram.concat(['@layer ' + r.name]));
      else if (typeof CSSContainerRule !== 'undefined' && r instanceof CSSContainerRule) samla(r.cssRules, ram.concat(['@container ' + r.conditionText]));
    }
  };
  for (const s of [...document.styleSheets]) { try { samla(s.cssRules, []); } catch (e) { /* ett ark från annat ursprung */ } }
  const matchar = (el, sel) => { try { return el.matches(sel); } catch (e) { return false; } };
  const rid = (r) => (r.style.getPropertyValue(RATTR) || '').replace(/["']/g, '').trim() || null;
  const satter = (stil, p) => stil.getPropertyValue(p) !== '' || (KORT[p] || []).some((s) => stil.getPropertyValue(s) !== '');
  const deklarerat = (stil, p) => {
    if (stil.getPropertyValue(p) !== '') return { varde: stil.getPropertyValue(p), viktig: stil.getPropertyPriority(p) === 'important', via: p };
    for (const s of KORT[p] || []) if (stil.getPropertyValue(s) !== '') return { varde: stil.getPropertyValue(s), viktig: stil.getPropertyPriority(s) === 'important', via: s };
    return null;
  };
  // Ägaren av p för el: den deklaration vars provvärde slår igenom. null när ingen deklaration som matchar el sätter p.
  const agare = (el, p) => {
    const fore = ber(el, p);
    const provv = PROV(p, fore);
    const kand = regler.filter(({ r }) => satter(r.style, p) && matchar(el, r.selectorText));
    if (satter(el.style, p)) kand.push({ inline: true });
    for (const c of kand) {
      const stil = c.inline ? el.style : c.r.style;
      const orig = stil.cssText;
      const d = deklarerat(stil, p);
      stil.setProperty(p, provv, d && d.viktig ? 'important' : '');
      const efter = ber(el, p);
      stil.cssText = orig;
      if (efter !== fore) {
        if (c.inline) return { slag: 'inline', varde: d ? d.varde : null, viktig: !!(d && d.viktig), via: d ? d.via : p };
        const r = rid(c.r);
        return { slag: r ? 'regel' : 'okand_regel', r, valjare: c.r.selectorText, ram: c.ram, varde: d ? d.varde : null,
          viktig: !!(d && d.viktig), via: d ? d.via : p, antal: (() => { try { return document.querySelectorAll(c.r.selectorText).length; } catch (e) { return null; } })() };
      }
    }
    return null;
  };
  const tokens = (varde) => [...new Set((String(varde || '').match(/var\(\s*(--[A-Za-z0-9_-]+)/g) || []).map((x) => x.replace(/var\(\s*/, '')))];
  // Var en token (anpassad egenskap) får sitt värde för el: regeln på el eller närmaste förfader som vinner.
  const tokenAgare = (el, namn) => {
    const fore = ber(el, namn);
    for (let x = el; x; x = x.parentElement) {
      const kand = regler.filter(({ r }) => r.style.getPropertyValue(namn) !== '' && matchar(x, r.selectorText));
      if (x.style && x.style.getPropertyValue(namn) !== '') kand.push({ inline: true, el: x });
      for (const c of kand) {
        const stil = c.inline ? c.el.style : c.r.style;
        const orig = stil.cssText;
        stil.setProperty(namn, '"nwp-prov"', stil.getPropertyPriority(namn));
        const efter = ber(el, namn);
        stil.cssText = orig;
        if (efter !== fore) {
          if (c.inline) return { slag: 'inline', k: c.el.getAttribute(ATTR), varde: c.el.style.getPropertyValue(namn).trim() };
          const r = rid(c.r);
          return { slag: r ? 'regel' : 'okand_regel', r, valjare: c.r.selectorText, ram: c.ram, varde: c.r.style.getPropertyValue(namn).trim(),
            anvandning: regler.filter(({ r: y }) => y.style.cssText.includes('var(' + namn)).length };
        }
      }
    }
    return null;
  };
  const kontrast = (el) => {
    const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null; const v = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: v[0], g: v[1], b: v[2], a: v.length > 3 ? v[3] : 1 }; };
    const lum = (c) => { const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
    const fg = rgb(ber(el, 'color'));
    let bg = null, kalla = null;
    for (let x = el; x; x = x.parentElement) { const c = rgb(ber(x, 'background-color')); if (c && c.a > 0.99) { bg = c; kalla = x.getAttribute(ATTR) || x.tagName.toLowerCase(); break; } if (ber(x, 'background-image') !== 'none') { kalla = 'bild'; break; } }
    if (!fg || !bg) return { kvot: null, bakgrund: kalla };
    const [l1, l2] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    return { kvot: Math.round(((l1 + 0.05) / (l2 + 0.05)) * 100) / 100, bakgrund: kalla };
  };

  const element = [...document.querySelectorAll('[' + ATTR + '="' + k + '"]')];
  let el = element[instans];
  if (!el) return { fel: 'elementet finns inte på sidan', antal: element.length };
  if (barn) {
    const b = el.querySelectorAll(barn[0])[barn[1]];
    if (!b) return { fel: 'barnelementet finns inte', antal: element.length };
    el = b;
  }
  if (prova) {
    // ett provat värde för motorns egen kontroll av ett sparande: samma väg som förhandsvisningen (en tillfällig regel)
    const ark = new CSSStyleSheet();
    ark.replaceSync(String(prova.css || ''));
    document.adoptedStyleSheets = [...document.adoptedStyleSheets, ark];
  }
  const rekt = el.getBoundingClientRect();
  const res = {
    k, instans, antal: element.length, tagg: el.tagName.toLowerCase(), barn: barn ? barn[0] + ':' + barn[1] : null,
    text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 200),
    rekt: { x: Math.round(rekt.x), y: Math.round(rekt.y + scrollY), b: Math.round(rekt.width), h: Math.round(rekt.height) },
    egenskaper: {}, tokens: {},
  };
  for (const p of egenskaper) {
    let ag = agare(el, p);
    let arvd = null;
    if (!ag && ARVS.has(p)) {
      for (let x = el.parentElement; x && !ag; x = x.parentElement) { const y = agare(x, p); if (y) { ag = y; arvd = { k: x.getAttribute(ATTR), tagg: x.tagName.toLowerCase() }; } }
    }
    res.egenskaper[p] = { berakn: ber(el, p), kalla: ag || { slag: 'standard' }, arvd };
    if (ag && ag.varde) for (const t of tokens(ag.varde)) if (!res.tokens[t]) res.tokens[t] = { berakn: ber(el, t), kalla: tokenAgare(el, t) || { slag: 'saknas' } };
  }
  if (egenskaper.includes('color')) res.kontrast = kontrast(el);
  if (el.tagName === 'IMG') {
    res.bild = { naturlig: [el.naturalWidth, el.naturalHeight], laddad: el.complete && el.naturalWidth > 0, aktuell: (el.currentSrc || el.src || '').replace(location.origin, ''),
      alt: el.getAttribute('alt') };
  }
  if (egenskaper.includes('font-family')) {
    const fam = ber(el, 'font-family').split(',').map((x) => x.trim().replace(/^["']|["']$/g, ''));
    res.typsnitt = fam.slice(0, 4).map((f) => ({ familj: f, tillganglig: !!(document.fonts && document.fonts.check('16px "' + f + '"')) }));
  }
  // regler med källa som matchar elementet (oavsett egenskap): där en ny deklaration kan sättas in, med antalet element
  // varje regel träffar på sidan (räckvidden)
  res.egnaRegler = regler.filter(({ r }) => rid(r) && matchar(el, r.selectorText)).map(({ r, ram }) => ({
    r: rid(r), valjare: r.selectorText, ram, antal: (() => { try { return document.querySelectorAll(r.selectorText).length; } catch (e) { return null; } })(),
  }));
  // markupens hash för elementet och förälderns barn: en strukturändring (variant, ordning) prövas mot dem efter bygget
  const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(16); };
  const utanId = (x) => x.outerHTML.replace(/ data-nwp-k="[0-9a-f]{12}"/g, '');  // id:n beror på trädet; en flyttad sektion jämförs utan dem
  res.markup = hash(utanId(el));
  // föräldern och syskonen: sektionsordningen prövas mot källan (studio.py, komposition)
  const far = el.parentElement;
  res.foralder = far ? { k: far.getAttribute(ATTR), tagg: far.tagName.toLowerCase(), id: far.id || null,
    barn: [...far.children].filter((x) => !['SCRIPT', 'STYLE', 'TEMPLATE'].includes(x.tagName)).map((x) => ({ k: x.getAttribute(ATTR), tagg: x.tagName.toLowerCase(), markup: hash(utanId(x)) })) } : null;
  if (alla.length) {
    // varje annoterat elements beräknade värden: före och efter ett sparande jämförs de, så att en ändring utanför
    // räckvidden syns (DS-U20, DS-U22)
    res.alla = {};
    const n = {};
    for (const x of document.querySelectorAll('[' + ATTR + ']')) {
      const id = x.getAttribute(ATTR); const i = n[id] = (n[id] || 0) + 1;
      res.alla[id + '#' + (i - 1)] = alla.map((p) => ber(x, p));
    }
  }
  return res;
}
