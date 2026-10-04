// extrahera.mjs — riktad designextraktion i samma webbläsarsession som fångsten (Codex 2026-10-04, glapp 2 och
// femstegsuppdraget steg 2): mätta värden för de element och sektioner som ska överföras, med källbilden bredvid.
// Allt här är uppmätt; byggaren skriver uppskattat och valt för kunden i REFERENSER.md och DESIGN.md.
//   import { extrahera } from './extrahera.mjs'; const x = await extrahera(page, ['h1', 'main p'], vy);
// Komposition: elementens rutor, gemensamma vänsterlinjer (spalter), textens och bildens relativa yta, tomrum.
// Typografi: deklarerad stack och renderat typsnitt (Chromium CSS.getPlatformFontsForNode), storlek, vikt,
// radavstånd, teckenavstånd, textbredd i tecken och de faktiska radbrytningarna.
// Färg: ytor viktade med synlig area, och textfärgerna som står på varje yta (grannar).
// Bildspråk: naturlig och renderad storlek, proportion, object-fit och object-position, beskärning.
// Rytm: sektionernas höjd, bakgrund, inre luft och textmängd uppifrån och ned.

export const STANDARD = ['h1', 'h2', 'h3', 'main p', 'main a', 'nav a', 'a[href^="tel:"]', 'a[href^="mailto:"]', 'button', 'header', 'footer'];

function matSidan(selektorer) {
  const rgb = (s) => { const m = (s || '').match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/); return m && (m[4] === undefined || +m[4] > 0.05) ? [+m[1], +m[2], +m[3]] : null; };
  const hex = (c) => c ? '#' + c.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('') : null;
  const synlig = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0; };
  const bakgrund = (el) => { for (let e = el; e; e = e.parentElement) { const c = rgb(getComputedStyle(e).backgroundColor); if (c) return hex(c); } return '#ffffff'; };
  const ruta = (el) => { const r = el.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top + scrollY), b: Math.round(r.width), h: Math.round(r.height) }; };
  const rader = (el) => {
    // ord för ord: varje ords rektangel ger raden; ord med samma topp hör till samma rad
    const ut = []; let topp = null; let rad = [];
    const gang = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = gang.nextNode(); n && ut.length < 14; n = gang.nextNode()) {
      const text = n.textContent; const re = /\S+/g; let m;
      while ((m = re.exec(text)) && ut.length < 14) {
        const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
        const rr = r.getClientRects()[0]; if (!rr) continue;
        const t = Math.round(rr.top);
        if (topp !== null && Math.abs(t - topp) > 3) { ut.push(rad.join(' ')); rad = []; }
        topp = t; rad.push(m[0]);
      }
    }
    if (rad.length) ut.push(rad.join(' '));
    return ut;
  };
  const element = [];
  for (const sel of selektorer) {
    const alla = Array.from(document.querySelectorAll(sel)).filter(synlig).slice(0, sel === 'main p' || sel === 'nav a' ? 3 : 2);  // få per väljare: de första synliga bär rollen
    alla.forEach((el, i) => {
      const s = getComputedStyle(el);
      const r = rader(el);
      el.setAttribute('data-nwp-extrakt', String(element.length));  // exakt matchning för det renderade typsnittet (CDP)
      const tecken = r.length ? Math.round(r.reduce((a, x) => a + x.length, 0) / r.length) : 0;
      element.push({ sel, nr: i, id: `${sel}#${i}`, tagg: el.tagName.toLowerCase(), text: (el.innerText || '').trim().slice(0, 160), ruta: ruta(el),
        typsnitt: { deklarerat: s.fontFamily, storlek: s.fontSize, vikt: s.fontWeight, stil: s.fontStyle, radavstand: s.lineHeight, teckenavstand: s.letterSpacing,
                    versaler: s.textTransform, justering: s.textAlign },
        farg: hex(rgb(s.color)), bakgrund: bakgrund(el), rader: r, tecken_per_rad: tecken, max_bredd: s.maxWidth });
    });
  }
  // sektionerna uppifrån och ned: barn till main (eller body), plus sidhuvud och sidfot
  const rot = document.querySelector('main') || document.body;
  const delar = [document.querySelector('body > header, header'), ...Array.from(rot.children), document.querySelector('body > footer, footer')].filter((e, i, a) => e && a.indexOf(e) === i && synlig(e) && e.getBoundingClientRect().height > 24);
  const sektioner = delar.slice(0, 24).map((el, i) => {
    const s = getComputedStyle(el); const r = ruta(el);
    const barn = Array.from(el.querySelectorAll('h1, h2, h3, p, img, picture, a, li')).filter(synlig);
    const vanster = [...new Set(barn.map((b) => Math.round(b.getBoundingClientRect().left / 4) * 4))].sort((a, b) => a - b).slice(0, 8);
    const textyta = barn.filter((b) => /^(H1|H2|H3|P|LI)$/.test(b.tagName)).reduce((a, b) => { const q = b.getBoundingClientRect(); return a + q.width * q.height; }, 0);
    const bildyta = barn.filter((b) => /^(IMG|PICTURE)$/.test(b.tagName)).reduce((a, b) => { const q = b.getBoundingClientRect(); return a + q.width * q.height; }, 0);
    const yta = Math.max(1, r.b * r.h);
    return { nr: i, tagg: el.tagName.toLowerCase(), id: el.id || null, ruta: r, bakgrund: bakgrund(el), luft: { topp: s.paddingTop, botten: s.paddingBottom },
             vanstra_linjer: vanster, textandel: +(textyta / yta).toFixed(3), bildandel: +(bildyta / yta).toFixed(3), tomrum: +Math.max(0, 1 - (textyta + bildyta) / yta).toFixed(3),
             rubrik: (el.querySelector('h1, h2, h3')?.innerText || '').trim().slice(0, 80) };
  });
  // gemensamma vänsterlinjer på hela sidan: x-lägen som minst tre textblock eller bilder delar (spalternas linjering)
  const lagen = {};
  for (const el of Array.from(document.querySelectorAll('h1, h2, h3, p, img, li, a')).filter(synlig)) { const x = Math.round(el.getBoundingClientRect().left / 4) * 4; lagen[x] = (lagen[x] || 0) + 1; }
  const linjer = Object.entries(lagen).filter(([, n]) => n >= 3).map(([x, n]) => ({ x: +x, antal: n })).sort((a, b) => b.antal - a.antal).slice(0, 8);
  // färgernas utbredning och grannar: ytor viktade med synlig area, och textfärgerna på varje yta
  const ytor = new Map();
  for (const el of document.querySelectorAll('body, body *')) {
    if (!synlig(el)) continue;
    const c = rgb(getComputedStyle(el).backgroundColor); if (!c) continue;
    const q = el.getBoundingClientRect(); const a = Math.max(0, Math.min(q.right, innerWidth) - Math.max(q.left, 0)) * q.height;
    const h = hex(c); const p = ytor.get(h) || { yta: 0, grannar: {} }; p.yta += a; ytor.set(h, p);
  }
  for (const el of document.querySelectorAll('h1, h2, h3, p, a, li, span, button')) {
    if (!synlig(el) || !(el.innerText || '').trim()) continue;
    const yt = bakgrund(el); const t = hex(rgb(getComputedStyle(el).color)); const p = ytor.get(yt); if (p && t) p.grannar[t] = (p.grannar[t] || 0) + 1;
  }
  const total = Math.max(1, [...ytor.values()].reduce((a, p) => a + p.yta, 0));
  const farger = [...ytor.entries()].map(([varde, p]) => ({ varde, andel: +(p.yta / total).toFixed(3), text_pa_ytan: Object.entries(p.grannar).sort((a, b) => b[1] - a[1]).slice(0, 4).map(([f]) => f) }))
    .sort((a, b) => b.andel - a.andel).slice(0, 10);
  // bilderna: proportion, beskärning, fokuspunkt
  const bilder = Array.from(document.querySelectorAll('img')).filter(synlig).slice(0, 12).map((img) => {
    const s = getComputedStyle(img); const r = ruta(img);
    const nat = [img.naturalWidth, img.naturalHeight];
    const beskuren = s.objectFit === 'cover' && nat[0] && nat[1] && Math.abs(nat[0] / nat[1] - r.b / Math.max(1, r.h)) > 0.02;
    return { src: (img.currentSrc || img.src || '').slice(0, 200), alt: (img.alt || '').slice(0, 120), ruta: r, naturlig: nat, proportion: r.h ? +(r.b / r.h).toFixed(3) : null,
             object_fit: s.objectFit, object_position: s.objectPosition, beskuren: !!beskuren, andel_av_bredd: +(r.b / innerWidth).toFixed(3) };
  });
  return { bredd: innerWidth, hojd: document.documentElement.scrollHeight, element, sektioner, linjer, farger, bilder };
}

export async function extrahera(page, selektorer = STANDARD) {
  const x = await page.evaluate(matSidan, selektorer);
  // renderat typsnitt per element: Chromiums egna uppgift om vilka typsnitt som ritade texten, skilt från den deklarerade
  // stacken; elementen hittas exakt genom attributet som mätningen satte
  try {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
    const { root } = await cdp.send('DOM.getDocument', { depth: 0 });
    const { nodeIds } = await cdp.send('DOM.querySelectorAll', { nodeId: root.nodeId, selector: '[data-nwp-extrakt]' });
    for (const nodeId of nodeIds) {
      const { attributes } = await cdp.send('DOM.getAttributes', { nodeId });
      const i = Number(attributes[attributes.indexOf('data-nwp-extrakt') + 1]);
      const e = x.element[i]; if (!e) continue;
      const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId }).catch(() => ({ fonts: [] }));
      e.typsnitt.renderat = (fonts || []).map((f) => ({ familj: f.familyName, postscript: f.postScriptName, eget: f.isCustomFont, tecken: f.glyphCount }));
    }
    await cdp.detach().catch(() => {});
  } catch (e) { x.renderat_fel = String(e.message || e).slice(0, 200); }
  return x;
}

export function sammanfatta(vy, x, bild) {
  const r = [`## ${vy} px — ${bild || ''}`, '', `Sidans höjd ${x.hojd} px. Gemensamma vänsterlinjer (x: antal): ${x.linjer.map((l) => `${l.x}: ${l.antal}`).join(', ') || 'inga'}.`, '', '### Typografi (uppmätt)', ''];
  for (const e of x.element.filter((e) => /^(h1|h2|h3|p|a|button)$/.test(e.tagg))) {
    const ren = (e.typsnitt.renderat || []).map((f) => f.familj + (f.eget ? ' (webbtypsnitt)' : ' (system)')).join(', ') || 'okänt';
    r.push(`- ${e.id}: renderat ${ren}; deklarerat ${e.typsnitt.deklarerat}; ${e.typsnitt.storlek}/${e.typsnitt.radavstand}, vikt ${e.typsnitt.vikt}, teckenavstånd ${e.typsnitt.teckenavstand}; ${e.rader.length} rader à ~${e.tecken_per_rad} tecken; färg ${e.farg} på ${e.bakgrund}; ruta ${e.ruta.b}×${e.ruta.h} vid x ${e.ruta.x}`);
    if (e.rader.length && /^h[1-3]$/.test(e.tagg)) r.push(`  - radbrytningar: ${e.rader.map((t) => `"${t}"`).join(' / ')}`);
  }
  r.push('', '### Färger (uppmätt yta och text på ytan)', '', ...x.farger.map((f) => `- ${f.varde}: ${(f.andel * 100).toFixed(1)} % av ytan; text på den: ${f.text_pa_ytan.join(', ') || '–'}`));
  r.push('', '### Rytm (sektionerna uppifrån)', '', ...x.sektioner.map((s) => `- ${s.nr} ${s.tagg}${s.rubrik ? ` "${s.rubrik}"` : ''}: höjd ${s.ruta.h} px, bakgrund ${s.bakgrund}, luft ${s.luft.topp}/${s.luft.botten}, text ${(s.textandel * 100).toFixed(0)} %, bild ${(s.bildandel * 100).toFixed(0)} %, tomrum ${(s.tomrum * 100).toFixed(0)} %, vänsterlinjer ${s.vanstra_linjer.join(', ')}`));
  r.push('', '### Bilder', '', ...x.bilder.map((b) => `- ${b.ruta.b}×${b.ruta.h} (${b.proportion}), ${(b.andel_av_bredd * 100).toFixed(0)} % av bredden, naturlig ${b.naturlig.join('×')}, ${b.object_fit} ${b.object_position}${b.beskuren ? ', beskuren' : ''}; "${b.alt}"`));
  return r.join('\n');
}
