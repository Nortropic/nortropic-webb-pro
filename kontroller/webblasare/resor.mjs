#!/usr/bin/env node
// resor.mjs — briefens viktigaste besökaruppgifter som prov (Codex helhetsbedömning 2026-10-04, punkt 6): varje resa har
// ett startläge, steg med avsedd handling, förväntat synligt resultat, och vid behov ett inmatningsfel och hur besökaren
// tar sig vidare. Resorna står i underlag/<slug>/RESOR.json (kunskap/resor.md). Bara nivån "lokalt prov" körs här, mot
// provets egen server på 127.0.0.1; inskick går bara till provets demomottagare. Övriga nivåer (testintegration,
// verklig leverans) listas som kvar till lanseringen. Normans principer som frågor: syns handlingen, ger den
// återkoppling, går felet att förstå och rätta.
//   node resor.mjs --adress http://127.0.0.1:PORT/ --resor underlag/<slug>/RESOR.json --ut DIR [--testmarkering TEXT]
// Steg: {"ga": "/väg"} · {"klicka": "väljare"} · {"fyll": {"väljare": "värde"}} · {"skicka": "formulärväljare"}
//       {"tangent": "Tab"} · {"vanta": "väljare"} · {"forvanta": {…}} (en kontroll mitt i resan)
// Förväntningar: {"url": "/tack/"} (sidans sökväg, med eller utan avslutande snedstreck) · {"text": "…"} (synlig text
//   på sidan, oavsett versaler) · {"lank": {"valjare": "…", "borjar": "tel:+46…"}} · {"synlig": "väljare"} ·
//   {"fel_vid_falt": "väljare"} (fältet ogiltigt och felet beskrivet med aria-describedby) · {"fokus_synlig": true}
// En väljare pekar på det första SYNLIGA elementet: en dold mobilmeny först i HTML:en fäller inte resan.
// klicka följer bara länkar inom sajten i samma fönster; tel:, mailto:, sms:, nytt fönster och andra webbplatser prövas
// med förväntan lank. {markering} blir provets testmarkering i fyll och i text.
import { args, oppna, origin, skriv, nu, viaTjanst, arLokal, VYER } from './gemensamt.mjs';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { vakta } from '../slugvakt.mjs';

await viaTjanst('resor', process.argv.slice(2));
const a = args(process.argv.slice(2));
vakta(a.ut);
if (!a.adress || !a.resor || !a.ut) { console.error('--adress URL --resor FIL --ut DIR [--testmarkering TEXT]'); process.exit(2); }
if (!arLokal(a.adress)) { console.error('resorna körs bara mot provets lokala server (127.0.0.1), inte ' + origin(a.adress)); process.exit(2); }
let uppdrag;
try { uppdrag = JSON.parse(readFileSync(a.resor, 'utf-8')); } catch (e) { console.error('RESOR.json kunde inte läsas: ' + e.message); process.exit(2); }
const resor = Array.isArray(uppdrag?.resor) ? uppdrag.resor : [];
const NIVAER = ['lokalt prov', 'testintegration', 'verklig leverans'];
const markering = String(a.testmarkering || 'NWP-PROV');
const markera = (x) => String(x).split('{markering}').join(markering);
const norm = (p) => String(p).replace(/\/+$/, '') || '/';
const synligt = (page, sel) => page.locator(sel).filter({ visible: true }).first();
const r = { schema: 1, verktyg: 'resor', tid: nu(), adress: a.adress, resor: [], kvar: [], fel: [],
  not: 'Lokalt prov mot provets demomottagare: kontrollerar handling och synligt resultat, inte leverans till människa.' };

async function kontrollera(page, f) {
  // en förväntan i taget; ger null när den håller, annars en mening om vad som inte höll
  if (f.url !== undefined) {
    // sökvägen jämförs hel, och adressen får hinna byta efter ett klick eller inskick
    const mal = norm(f.url);
    const ok = await page.waitForURL((u) => norm(u.pathname) === mal, { timeout: 5000 }).then(() => true).catch(() => false);
    return ok ? null : `adressen är ${new URL(page.url()).pathname}, väntade ${f.url}`;
  }
  if (f.text !== undefined) {
    // textinnehåll oavsett versaler (text-transform), bara element som syns och ligger på sidan (inte utanför kanten)
    const t = markera(f.text);
    const n = await page.getByText(t).evaluateAll((els) => els.filter((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && r.right + scrollX > 0 && r.bottom + scrollY > 0;
    }).length).catch(() => 0);
    return n ? null : `texten "${t}" syns inte`;
  }
  if (f.lank !== undefined) {
    const alla = page.locator(f.lank.valjare);
    if (!await alla.count()) return `ingen länk ${f.lank.valjare}`;
    const l = alla.filter({ visible: true }).first();
    if (!await l.count()) return `länken ${f.lank.valjare} syns inte`;
    const href = await l.getAttribute('href') || '';
    return href.startsWith(f.lank.borjar || '') ? null : `länken går till ${href}, väntade ${f.lank.borjar}…`;
  }
  if (f.synlig !== undefined) {
    return await synligt(page, f.synlig).count() ? null : `${f.synlig} syns inte`;
  }
  if (f.fel_vid_falt !== undefined) {
    const falt = page.locator(f.fel_vid_falt);
    if (!await falt.count()) return `fältet ${f.fel_vid_falt} finns inte`;
    let s;
    try {
      s = await falt.first().evaluate((e) => {
        if (!e.validity) return { inget: e.tagName.toLowerCase() };
        // utan sidoeffekt: checkValidity() skulle avfyra invalid och låta sidans egen hanterare visa felet
        const ogiltig = e.getAttribute('aria-invalid') === 'true' || e.matches(':invalid');
        const besked = (e.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean).map((id) => document.getElementById(id))
          .filter((x) => x && x.getBoundingClientRect().height > 0 && (x.innerText || '').trim()).map((x) => x.innerText.trim());
        return { ogiltig, besked: besked.join(' · ') };
      }, null, { timeout: 5000 });
    } catch (e) { return `fältet ${f.fel_vid_falt} gick inte att läsa: ${String(e.message || e).split('\n')[0].slice(0, 160)}`; }
    if (s.inget) return `${f.fel_vid_falt} är inget formulärfält (${s.inget})`;
    return s.ogiltig && s.besked ? null : `fältet ${f.fel_vid_falt} är inte markerat med ett synligt felbesked (ogiltigt: ${s.ogiltig}, besked: "${s.besked}")`;
  }
  if (f.fokus_synlig !== undefined) {
    const ok = await page.evaluate(() => { const e = document.activeElement; if (!e || e === document.body) return false; const s = getComputedStyle(e);
      return (s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) || s.boxShadow !== 'none'; });
    return ok ? null : 'fokus syns inte';
  }
  return 'okänd förväntan ' + JSON.stringify(f);
}

const sedda = new Set();
for (const [nr, resa] of resor.entries()) {
  // id: gemener, å/ä/ö utan prickar, a–z 0–9 och bindestreck; samma id två gånger får ett löpnummer (bilderna skrivs per id)
  const bas = String(resa.id || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9-]/g, '').slice(0, 40) || `resa-${nr + 1}`;
  let id = bas; for (let k = 2; sedda.has(id); k++) id = `${bas}-${k}`;
  sedda.add(id);
  const niva = resa.niva === undefined ? 'lokalt prov' : resa.niva;
  if (!NIVAER.includes(niva)) { r.fel.push(`${id}: okänd nivå "${niva}" (${NIVAER.join(', ')})`); continue; }
  if (niva !== 'lokalt prov') { r.kvar.push({ id, uppgift: resa.uppgift || '', niva }); continue; }
  const vy = String(resa.vy || '390');
  if (!VYER[vy]) { r.fel.push(`${id}: okänd vy "${vy}" (${Object.keys(VYER).join(', ')})`); continue; }
  const ut = { id, uppgift: resa.uppgift || '', niva, vy, steg: [], ok: false, skal: '' };
  let b = null;
  try {
    b = await oppna({ vy, tillat: [origin(a.adress)], mal: a.adress, lasande: true, skrivbara: [origin(a.adress)] });
    await b.page.goto(new URL(resa.start || '/', a.adress).href, { waitUntil: 'load', timeout: 30000 });
    let fel = null;
    const forvantningar = [...(resa.steg || []), ...((resa.forvantat || []).map((f) => ({ forvanta: f })))];
    for (const [i, s] of forvantningar.entries()) {
      const post = { nr: i + 1, steg: s };
      try {
        if (s.ga) await b.page.goto(new URL(s.ga, a.adress).href, { waitUntil: 'load', timeout: 30000 });
        else if (s.klicka) {
          const el = synligt(b.page, s.klicka);
          if (!await el.count()) throw new Error(`inget synligt element för ${s.klicka}`);
          const lank = await el.evaluate((e) => { const l = e.closest('a'); return l ? { href: l.getAttribute('href') || '', target: l.getAttribute('target') || '',
            annan: /^https?:$/.test(l.protocol) && l.origin !== location.origin } : null; }, null, { timeout: 5000 });
          if (lank && /^(tel|mailto|sms):/i.test(lank.href)) throw new Error(`${s.klicka} är en ${lank.href.split(':')[0]}:-länk; pröva den med förväntan lank, inte klicka`);
          if (lank && lank.target && lank.target !== '_self') throw new Error(`${s.klicka} öppnar ett nytt fönster; pröva den med förväntan lank`);
          if (lank && lank.annan) throw new Error(`${s.klicka} leder till en annan webbplats (${lank.href}); pröva den med förväntan lank`);
          await el.click({ timeout: 5000 });
          await b.page.waitForLoadState('load', { timeout: 10000 }).catch(() => {});
        }
        else if (s.fyll) { for (const [sel, varde] of Object.entries(s.fyll)) await synligt(b.page, sel).fill(markera(varde), { timeout: 5000 }); }
        else if (s.skicka) {
          const form = synligt(b.page, s.skicka);
          const knapp = form.locator('button[type=submit], button:not([type]), input[type=submit]').filter({ visible: true }).first();
          await knapp.click({ timeout: 5000 });
          await b.page.waitForLoadState('load', { timeout: 10000 }).catch(() => {});
        } else if (s.tangent) await b.page.keyboard.press(s.tangent);
        else if (s.vanta) await synligt(b.page, s.vanta).waitFor({ state: 'visible', timeout: 5000 });
        else if (s.forvanta) { const k = await kontrollera(b.page, s.forvanta); if (k) throw new Error(k); }
        else throw new Error('okänt steg ' + JSON.stringify(s));
        post.ok = true;
      } catch (e) {
        post.ok = false; post.fel = b.red(String(e.message || e)).split('\n')[0].slice(0, 300); fel = post;
      }
      post.bild = join(a.ut, `${id}-steg-${String(i + 1).padStart(2, '0')}.png`);
      await b.page.screenshot({ path: post.bild }).catch(() => { post.bild = null; });
      ut.steg.push(post);
      if (fel) break;
    }
    ut.ok = !fel && ut.steg.length > 0;
    // steget står med i skälet: Playwrights första rad ("Timeout 5000ms exceeded") säger inte vilken väljare som föll
    ut.skal = fel ? `steg ${fel.nr} ${JSON.stringify(fel.steg).slice(0, 140)}: ${fel.fel}` : (ut.steg.length ? 'alla steg och förväntningar höll' : 'resan har inga steg eller förväntningar');
    ut.slutadress = b.page.url();
  } catch (e) {
    ut.skal = (b ? b.red(String(e.message || e)) : String(e.message || e)).split('\n')[0].slice(0, 300);
  } finally {
    if (b) { ut.blockerade = b.logg.blockerade.length; await b.stang().catch(() => {}); }
  }
  r.resor.push(ut);
}
if (!r.resor.length) r.fel.push('inga resor på nivån lokalt prov i RESOR.json');
r.ok = !r.fel.length && r.resor.every((x) => x.ok);
skriv(a.ut, 'RESOR.json', r);
const md = ['# Resor — ' + a.adress + ' (' + r.tid + ')', '', r.not, ''];
for (const x of r.resor) {
  md.push(`## ${x.ok ? 'HÖLL' : 'HÖLL INTE'} · ${x.id} · ${x.uppgift} (${x.niva}, ${x.vy} px)`, '', `- ${x.skal}`);
  for (const s of x.steg) md.push(`  - steg ${s.nr} ${s.ok ? 'ok' : 'FEL'}: ${JSON.stringify(s.steg).slice(0, 160)}${s.fel ? ' — ' + s.fel : ''}${s.bild ? ' · ' + s.bild : ''}`);
  md.push('');
}
if (r.kvar.length) md.push('## Kvar till lanseringen', '', ...r.kvar.map((k) => `- ${k.id} · ${k.uppgift} (${k.niva})`), '');
for (const f of r.fel) md.push('- fel: ' + f);
skriv(a.ut, 'RESOR.md', md.join('\n') + '\n');
console.log(JSON.stringify({ ok: r.ok, resor: r.resor.length, hollnt: r.resor.filter((x) => !x.ok).map((x) => x.id), kvar: r.kvar.length }));
process.exitCode = r.ok ? 0 : 1;
