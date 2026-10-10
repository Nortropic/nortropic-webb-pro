#!/usr/bin/env node
// Utvecklarinspektion (användning 1): rendera adressen i valda vyer med brief- och kodkontext bifogad som lista med
// hashar, ta skärmbilder (första vyn och hela sidan), tillgänglighetsträd, konsol, nätverk, tillstånd (hover, fokus,
// tangentbord, reflow 320, meny, omladdning, bakåt/framåt), spår. Skärmbilder kompletterar interaktionen; ett textträd
// är inte bildseende — bedöm layout i bilderna.
//   node inspektera.mjs --adress URL --ut DIR [--vyer 390,1440] [--tillat ORIGIN;ORIGIN | --tillat-alla] [--undantag-fil F]
//        [--hemligheter FIL] [--kontext FIL,FIL] [--hover SEL;SEL] [--fokus SEL;SEL] [--meny SEL] [--tillstand tangentbord,reflow,reload,bakat,reducerad]
//        reducerad: sidan omladdad med prefers-reduced-motion: reduce; animationer som fortfarande löper räknas och fotograferas
//        [--extrahera standard | 'SEL;SEL'] — riktad designextraktion i samma session (extrahera.mjs): vy-<bredd>-extrakt.json,
//        EXTRAKT.md (hela mätningen, med interaktiva element, rörelsesekvensen och spårets steg per vy) och SEKTIONER.md (det
//        kuraterade underlaget: ett avsnitt per sektion med bild, mått, typsnitt, regler och DOM-utdrag)
//        [--svep] — ett svep över bredderna 320–1600 som registrerar var layouten byter form (SVEP.json, avsnitt i EXTRAKT.md)
//        [--extrakt-utan-kod] — granskarens form (forhandsvisa --granskare): måtten och typsnitten, men inga CSS-regler, inga
//        DOM-utdrag, inget SEKTIONER.md och animationsmål utan klasser; den blinda kritiken får aldrig skaparens kod
//        --hover och --fokus tar flera CSS-väljare åtskilda med semikolon: den första ger vy-<bredd>-hover.png, de följande
//        vy-<bredd>-hover-2.png …; utfallet per väljare står i tillstand.hover_lista (ägarens uppdrag 2026-10-07, punkt 7)
//        [--samtycke] [--lugn MS] [--motor webkit] — för fångst av främmande sajter (kalibreringen, ägarens uppdrag 2026-10-09,
//        punkt 2): en samtyckesdialog stängs med sitt eget val, helst det som avböjer; första vyn fotograferas först när
//        sidans animationer är klara och synliga videor har en bild (högst MS); WebKit spelar video som Chromium saknar
//        kodek för. Utfallen står i vyns samtycke och lugn. Utan flaggorna är fångsten som förut.
import { args, oppna, origin, horisontellSpill, tangentbord, skriv, sha256, nu, lasUndantag, hemligheter, VYER, viaTjanst } from './gemensamt.mjs';
import { readFileSync, rmSync } from 'node:fs';
import { join, basename } from 'node:path';
import { vakta } from '../slugvakt.mjs';
import { extrahera, sammanfatta, STANDARD, animationerPaSidan, interaktiva, sparsammanfattning, svep, svepsammanfattning, sektionsunderlag, MATERIALNOT } from './extrahera.mjs';

await viaTjanst('inspektera', process.argv.slice(2));
// Menyn i verkligt tillstånd (ägaren 2026-10-06: en bild med "meny" i filnamnet bevisar inte att menyn öppnades).
// Elementet hålls fast före klicket, som i axe.mjs: väljaren kan sluta matcha när menyn är öppen (aria-expanded, open).
// expanded: 'true' när knappen har aria-expanded="true" eller ligger i ett öppet details-element, 'false' när den har
// attributet eller ligger i ett details-element som är stängt, null när läget inte går att avläsa. Menybilden tas bara
// när menyn öppnades; annars står skälet i skal och ingen vy-<bredd>-meny.png finns. Utan synlig knapp räknas
// navigationens länkar utanför sidfoten (varje adress en gång) och hur många som syns: en mobil utan menyknapp där alla
// länkar syns är inget fel, men det ska sägas.
async function provaMeny(page, valjare, ut, vy) {
  const m = { valjare, knapp: false, klickad: false, expanded: null };
  rmSync(join(ut, `vy-${vy}-meny.png`), { force: true });
  const knapp = await page.locator(valjare).filter({ visible: true }).first().elementHandle({ timeout: 1000 }).catch(() => null);
  if (!knapp) {
    m.lankar = await page.evaluate(() => {
      const syns = (e) => {
        const r = e.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0 && r.right > 0 && r.left < innerWidth)) return false;
        if (e.checkVisibility && !e.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return false;
        const y = r.top + r.height / 2;
        if (y < 0 || y >= innerHeight) return true;  // utanför första vyn: storleken och synligheten avgör
        const t = document.elementFromPoint(Math.min(Math.max(r.left + r.width / 2, 0), innerWidth - 1), y);
        return !!t && (t === e || e.contains(t) || t.contains(e));
      };
      const alla = new Set(), synliga = new Set();
      for (const e of document.querySelectorAll('nav a[href]')) {
        if (e.closest('footer')) continue;
        alla.add(e.getAttribute('href'));
        if (syns(e)) synliga.add(e.getAttribute('href'));
      }
      return { totalt: alla.size, synliga: synliga.size, dolda: [...alla].filter((h) => !synliga.has(h)).slice(0, 6) };
    }).catch(() => null);
    m.skal = 'ingen synlig menyknapp (' + valjare + ')';
    return m;
  }
  m.knapp = true;
  m.etikett = await knapp.evaluate((e) => (e.getAttribute('aria-label') || e.innerText || '').trim().slice(0, 60)).catch(() => '');
  try { await knapp.click({ timeout: 5000 }); m.klickad = true; } catch (e) { m.skal = 'knappen gick inte att klicka: ' + String(e.message).split('\n')[0].slice(0, 160); return m; }
  await page.waitForTimeout(400);
  m.expanded = await knapp.evaluate((e) => {
    const x = e.getAttribute('aria-expanded'), d = e.closest('details');
    return x === 'true' || (d && d.open) ? 'true' : (x !== null || d) ? 'false' : null;
  }).catch(() => null);
  if (m.expanded === 'true') { m.bild = join(ut, `vy-${vy}-meny.png`); await page.screenshot({ path: m.bild }); }
  else m.skal = m.expanded === 'false' ? 'menyn öppnades inte: knappen är stängd efter klicket (aria-expanded eller details)'
    : 'menyns läge går inte att avläsa: knappen har varken aria-expanded eller ett details-element';
  return m;
}

// Flera väljare per tillstånd: varje väljare fotograferas för sig (hover: page.hover, fokus: page.focus); den första får
// det gamla filnamnet och fälten hover/hover_fel, så att förhandsvisningen och referenspaketets äldre inlägg läser som
// förut, och hover_lista bär utfallet per väljare.
async function provaTillstand(page, namn, valjare, ut, vy, regAnim) {
  const lista = [];
  for (let i = 0; i < valjare.length; i++) {
    const sel = valjare[i]; const post = { valjare: sel, bild: join(ut, i === 0 ? `vy-${vy}-${namn}.png` : `vy-${vy}-${namn}-${i + 1}.png`) };
    try { if (namn === 'hover') await page.hover(sel, { timeout: 5000 }); else await page.focus(sel, { timeout: 5000 }); }
    catch (e) { post.fel = String(e.message).split('\n')[0].slice(0, 120); }
    await page.waitForTimeout(250);
    if (!post.fel) await regAnim(`${namn} ${sel}`);
    await page.screenshot({ path: post.bild });
    lista.push(post);
  }
  return lista;
}

const a = args(process.argv.slice(2));
vakta(a.ut);
if (!a.adress || !a.ut) { console.error('användning: --adress URL --ut DIR [...]'); process.exit(2); }
// --tillat-alla: inga ursprungsgränser (främmande sajter i prospektanalysen lastar typsnitt, bilder och skript från CDN:er)
const tillat = a['tillat-alla'] ? [] : [origin(a.adress), ...(a.tillat ? String(a.tillat).split(';').filter(Boolean) : [])];
const undantag = lasUndantag(a['undantag-fil']);
const hemliga = hemligheter(a.hemligheter);
const vyer = String(a.vyer || '390,1440').split(',');
const tillstand = new Set(String(a.tillstand || 'tangentbord,reflow,reload,bakat').split(',').filter(Boolean));
// fasta och klibbiga element som syns i vyn, med andel av vyhöjden (körs i sidan)
const fastaIVyn = () => { const vh = window.innerHeight; return [...document.querySelectorAll('body *')].filter((el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect(); return (s.position === 'fixed' || s.position === 'sticky') && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < vh && s.visibility !== 'hidden'; }).map((el) => { const r = el.getBoundingClientRect(); return { element: el.tagName.toLowerCase() + (el.id ? '#' + el.id : el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/)[0] : ''), hojd: Math.round(r.height), andel: Math.round(100 * r.height / vh) }; }).filter((x) => x.andel >= 15).slice(0, 6); };
const kontext = (a.kontext ? String(a.kontext).split(',') : []).map(f => ({ fil: f, namn: basename(f), sha256: sha256(readFileSync(f)), byte: readFileSync(f).length }));
const extraktSel = a.extrahera ? (String(a.extrahera) === 'standard' || a.extrahera === true ? STANDARD : String(a.extrahera).split(';').map((x) => x.trim()).filter(Boolean).slice(0, 24)) : null;
const valjare = (v) => (v && v !== true ? String(v).split(';').map((x) => x.trim()).filter(Boolean).slice(0, 8) : []);
const hoverSel = valjare(a.hover), fokusSel = valjare(a.fokus);
const medKod = !a['extrakt-utan-kod'];
const motor = a.motor ? String(a.motor) : 'chromium';
// samtyckesdialogens knappar, i den ordning de väljs: först det som avböjer, sist det som godkänner
const SAMTYCKE = [/^(reject|decline|deny)( all)?( non-essential)?( cookies)?$/i, /^(avvisa|neka|avböj)( alla)?( kakor| cookies)?$/i,
  /^(only|endast|bara) (necessary|nödvändiga)( cookies| kakor)?$/i, /^(use )?necessary( cookies)? only$/i,
  /^(accept|godkänn|tillåt|acceptera)( all| alla)?( cookies| kakor)?$/i, /^(ok|i agree|i understand|jag godkänner|jag förstår|got it|förstått)$/i];
async function stangSamtycke(page) {
  // en knapp, en länk, eller sist en text utan roll, men bara inne i något som heter cookie, consent, gdpr eller samtycke
  const iDialog = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement) if (/cookie|consent|samtyck|gdpr/i.test(`${n.id || ''} ${typeof n.className === 'string' ? n.className : ''}`)) return true; return false; };
  for (const re of SAMTYCKE) for (const roll of ['button', 'link', 'text']) {
    const alla = (roll === 'text' ? page.getByText(re) : page.getByRole(roll, { name: re })).filter({ visible: true });
    let knapp = null;
    for (let i = 0, n = Math.min(await alla.count().catch(() => 0), 10); i < n && !knapp; i++) {
      if (roll !== 'text' || await alla.nth(i).evaluate(iDialog).catch(() => false)) knapp = alla.nth(i);
    }
    if (!knapp) continue;
    const namn = (await knapp.innerText().catch(() => '')).trim().slice(0, 60);
    try { await knapp.click({ timeout: 3000 }); await page.waitForTimeout(600); return { stangd: true, knapp: namn, roll }; }
    catch (e) { return { stangd: false, knapp: namn, fel: String(e.message).split('\n')[0].slice(0, 120) }; }
  }
  return { stangd: false, skal: 'ingen synlig samtyckesknapp' };
}
async function vantaLugn(page, ms) {
  const t0 = Date.now();
  const lage = () => page.evaluate(() => ({
    anim: document.getAnimations ? document.getAnimations().filter((x) => x.playState === 'running' && (x.effect?.getTiming?.().iterations ?? 1) !== Infinity).length : 0,
    vid: [...document.querySelectorAll('video')].filter((v) => { const r = v.getBoundingClientRect(); return r.width > 0 && r.bottom > 0 && r.top < innerHeight && v.readyState < 2; }).length }));
  let l = await lage().catch(() => ({ anim: 0, vid: 0 }));
  while ((l.anim || l.vid) && Date.now() - t0 < ms) { await page.waitForTimeout(250); l = await lage().catch(() => ({ anim: 0, vid: 0 })); }
  return { ms: Date.now() - t0, animationer_kvar: l.anim, videor_utan_bild: l.vid };
}
const extraktVyer = {};  // bredd → {x, rutor, skarmhojd}: EXTRAKT.md och SEKTIONER.md skrivs när alla vyer är klara
const rapport = { schema: 1, verktyg: 'inspektera', adress: a.adress, tid: nu(), tillatna_ursprung: tillat.length ? tillat : 'alla', undantag: !!undantag, kontext, vyer: {}, not: 'utvecklarinspektion med kontext; skärmbilderna avgör layout (textträdet är inte bildseende); mobilvyerna är emulerade, inte fysisk enhet' };
for (const vy of vyer) {
  const b = await oppna({ vy, tillat, undantag, hemliga, spar: true, mal: a.adress, motor });
  const r = { namn: b.vy.namn, sidor: [], tillstand: {}, rorelse: [] };
  // rörelsesekvensen: sidans animationer vid varje händelse, med händelsen som trigger (extrahera.animationerPaSidan)
  const regAnim = async (trigger) => { try { r.rorelse.push({ trigger, animationer: await b.page.evaluate(animationerPaSidan, medKod) }); } catch (e) { r.rorelse.push({ trigger, fel: String(e.message).slice(0, 120) }); } };
  // rörelse som document.getAnimations() inte ser (MDN: bara CSS-animationer, övergångar och Web Animations): sidans egna
  // requestAnimationFrame-anrop räknas från start, och canvas och spelande video noteras (ägarens uppdrag 2026-10-10, punkt 6)
  await b.page.addInitScript(() => { window.__nwpRaf = 0; const o = window.requestAnimationFrame; if (o) window.requestAnimationFrame = function (cb) { window.__nwpRaf++; return o.call(window, cb); }; }).catch(() => null);
  try {
    const svar = await b.page.goto(a.adress, { waitUntil: 'load', timeout: 45000 });
    r.status = svar?.status() ?? null; r.innehallstyp = svar?.headers()?.['content-type'] ?? null; r.titel = await b.page.title();
    await b.page.waitForTimeout(500);
    if (a.samtycke) r.samtycke = await stangSamtycke(b.page);
    if (a.lugn) r.lugn = await vantaLugn(b.page, Number(a.lugn) || 8000);
    r.rorelse_motor = await b.page.evaluate(async () => {
      const r0 = window.__nwpRaf || 0; await new Promise((ok) => setTimeout(ok, 1000));
      return { raf_per_s: (window.__nwpRaf || 0) - r0, canvas: document.querySelectorAll('canvas').length,
        video_spelar: [...document.querySelectorAll('video')].filter((v) => !v.paused).length,
        web_animations: document.getAnimations ? document.getAnimations().length : null };
    }).catch((e) => ({ fel: String(e.message).slice(0, 120) }));
    const m_ = r.rorelse_motor || {};
    if (!m_.fel && (m_.raf_per_s > 5 || m_.canvas || m_.video_spelar)) {  // en stillbild räcker inte: en kort bildsekvens av första vyn
      r.rorelse_motor.sekvens = [];
      for (let i = 1; i <= 3; i++) { const f = join(a.ut, `vy-${vy}-sekvens-${i}.png`); await b.page.screenshot({ path: f }).then(() => r.rorelse_motor.sekvens.push(f)).catch(() => null); await b.page.waitForTimeout(400); }
    }
    r.rorelse_motor.not = 'en tom getAnimations() bevisar inte att sidan saknar rörelse: canvas, requestAnimationFrame och video observeras här för sig, och en bildsekvens är en observation, inte en mätning av rörelsens egenskaper';
    r.forsta_vyn = skriv(a.ut, `vy-${vy}-forsta.png`, ''); await b.page.screenshot({ path: r.forsta_vyn });
    await regAnim('laddning');
    // Lata bilder (loading=lazy) och intoning vid skroll syns inte i en helsidesbild om sidan inte skrollats igenom först.
    await b.page.evaluate(async () => { const h = () => document.documentElement.scrollHeight; for (let y = 0; y < h(); y += innerHeight * 0.8) { scrollTo(0, y); await new Promise((ok) => setTimeout(ok, 150)); } scrollTo(0, 0); });
    await b.page.waitForFunction(() => Array.from(document.images).every((i) => i.complete), null, { timeout: 8000 }).catch(() => {});
    await b.page.waitForTimeout(300);
    r.hela_sidan = join(a.ut, `vy-${vy}-hela.png`); await b.page.screenshot({ path: r.hela_sidan, fullPage: true });
    await regAnim('skroll');
    // Skärmhöga rutor tagna genom att skrolla en skärm i taget: varje ruta är det besökaren ser i det läget, och
    // ruta 01 är alltid förstavyn. Chromiums helsidesbild kan börja mitt på sidan (lulea-snickaren-abx 2026-10-02),
    // så rutorna skärs inte ur den.
    r.rutor = [];
    const sidhojd = await b.page.evaluate(() => document.documentElement.scrollHeight);
    const skarmhojd = VYER[vy].viewport.height;
    for (let i = 0; i < Math.min(12, Math.ceil(sidhojd / skarmhojd)); i++) {
      await b.page.evaluate((y) => scrollTo(0, y), i * skarmhojd);
      await b.page.waitForTimeout(150);
      const fil = join(a.ut, `vy-${vy}-ruta-${String(i + 1).padStart(2, '0')}.png`);
      await b.page.screenshot({ path: fil });
      r.rutor.push(fil);
    }
    await b.page.evaluate(() => scrollTo(0, 0));
    r.skarmar = Math.ceil(sidhojd / skarmhojd);
    r.h1_i_forsta_vyn = await b.page.evaluate((h) => { const e = document.querySelector('h1'); return !!e && e.getBoundingClientRect().top < h; }, skarmhojd);
    if (extraktSel) {  // före tillstånden (hover, meny, reflow) som ändrar sidan; källbilden är vyns första ruta och helsida
      const x = await extrahera(b.page, extraktSel, { kod: medKod }).catch((e) => ({ fel: String(e.message || e).slice(0, 200) }));
      x.kallbilder = { forsta: r.forsta_vyn, rutor: r.rutor, hela: r.hela_sidan }; x.vy = vy; x.adress = a.adress; x.tid = nu(); x.matning = 'uppmätt';
      r.extrakt = skriv(a.ut, `vy-${vy}-extrakt.json`, x);
      if (x.fel) r.extrakt_fel = x.fel; else extraktVyer[vy] = { x, rutor: r.rutor.map((f) => basename(f)), skarmhojd, bild: basename(r.forsta_vyn), r };
      if (x.ogiltiga_valjare && x.ogiltiga_valjare.length) r.extrakt_ogiltiga = x.ogiltiga_valjare;
    }
    const aria = await b.page.locator('body').ariaSnapshot();
    r.tillganglighetstrad = skriv(a.ut, `vy-${vy}-aria.txt`, aria);
    r.interaktiva = interaktiva(aria);  // det besökaren kan göra: länkar, knappar, fält (ur trädet, inte ur koden)
    r.h1 = await b.page.locator('h1').count();
    r.spill = await horisontellSpill(b.page);
    if (hoverSel.length) { r.tillstand.hover_lista = await provaTillstand(b.page, 'hover', hoverSel, a.ut, vy, regAnim); r.tillstand.hover = r.tillstand.hover_lista[0].bild; if (r.tillstand.hover_lista[0].fel) r.tillstand.hover_fel = r.tillstand.hover_lista[0].fel; }
    if (fokusSel.length) { r.tillstand.fokus_lista = await provaTillstand(b.page, 'fokus', fokusSel, a.ut, vy, regAnim); r.tillstand.fokus = r.tillstand.fokus_lista[0].bild; if (r.tillstand.fokus_lista[0].fel) r.tillstand.fokus_fel = r.tillstand.fokus_lista[0].fel; }
    if (a.meny) { r.tillstand.meny = await provaMeny(b.page, String(a.meny), a.ut, vy); if (r.tillstand.meny.klickad) await regAnim('meny'); }
    if (tillstand.has('tangentbord')) { await b.page.goto(a.adress, { waitUntil: 'load' }); r.tillstand.tangentbord = await tangentbord(b.page, 25); r.tillstand.tangentbord_utan_synlig_fokus = r.tillstand.tangentbord.filter(s => !s.synligFokus).length; }
    if (tillstand.has('reflow')) { await b.page.setViewportSize({ width: 320, height: 640 }); await b.page.waitForTimeout(300); r.tillstand.reflow_320 = await horisontellSpill(b.page); await b.page.screenshot({ path: join(a.ut, `vy-${vy}-reflow320.png`) });
      // 400 % zoom (WCAG 1.4.10): 320×180; fasta och klibbiga element som täcker vyn (byggstandarden 3.3, backloggen 2026-10-03)
      await b.page.setViewportSize({ width: 320, height: 180 }); await b.page.waitForTimeout(200);
      r.tillstand.reflow_320x180 = { ...(await horisontellSpill(b.page)), fasta: await b.page.evaluate(fastaIVyn) }; await b.page.screenshot({ path: join(a.ut, `vy-${vy}-reflow320x180.png`) }); await b.page.setViewportSize(b.vy.viewport); }
    if (tillstand.has('reducerad')) {  // rörelsen respekterar prefers-reduced-motion: löpande animationer efter omladdning
      const lopande = async () => b.page.evaluate(() => document.getAnimations().filter((x) => x.playState === 'running').map((x) => (x.animationName || x.transitionProperty || x.id || x.constructor.name)).slice(0, 12));
      await b.page.goto(a.adress, { waitUntil: 'load' }); await b.page.waitForTimeout(250);
      const utan = await lopande();
      await b.page.emulateMedia({ reducedMotion: 'reduce' });
      await b.page.goto(a.adress, { waitUntil: 'load' }); await b.page.waitForTimeout(250);
      const med = await lopande();
      r.tillstand.reducerad = { lopande_utan: utan.length, lopande_med_reduce: med.length, namn_med_reduce: med, bild: join(a.ut, `vy-${vy}-reducerad.png`) };
      await b.page.screenshot({ path: r.tillstand.reducerad.bild });
      await b.page.emulateMedia({ reducedMotion: 'no-preference' });
    }
    if (tillstand.has('reload')) { const s2 = await b.page.reload({ waitUntil: 'load' }); r.tillstand.reload_status = s2?.status() ?? null; }
    if (tillstand.has('bakat')) { const lank = b.page.locator('a[href^="/"], a[href^="' + origin(a.adress) + '"]').first(); if (await lank.count()) { const href = await lank.getAttribute('href'); await lank.click({ timeout: 5000 }).catch(() => null); await b.page.waitForLoadState('load').catch(() => null); const efter = b.page.url(); await b.page.goBack({ waitUntil: 'load' }).catch(() => null); const tillbaka = b.page.url(); await b.page.goForward({ waitUntil: 'load' }).catch(() => null); r.tillstand.bakat = { lank: href, efter_klick: efter, efter_bakat: tillbaka, efter_framat: b.page.url() }; } }
  } catch (e) { r.fel = String(e.message).slice(0, 300); }
  r.konsol = b.logg.konsol; r.sidfel = b.logg.sidfel; r.dialoger = b.logg.dialoger; r.natverk = { antal: b.logg.natverk.length, fel: b.logg.natverk.filter(x => x.status === null || x.status >= 400), blockerade: b.logg.blockerade, laddade: b.logg.natverk.filter(x => x.status === 200).reduce((m, x) => { m[x.typ || 'other'] = (m[x.typ || 'other'] || 0) + 1; return m; }, {}) };  // laddade per typ: referenspaketet verifierar att bilder och typsnitt kom med
  r.spar = join(a.ut, `vy-${vy}-spar.zip`); await b.stang(r.spar);
  r.spar_sammanfattning = sparsammanfattning(r.spar);  // läsbar sammanfattning; filen förblir privat
  rapport.vyer[vy] = r;
}
if (a.svep) {  // svepet över bredderna: en egen datorkontext som bara byter bredd (extrahera.svep)
  const bs = await oppna({ vy: '1440', tillat, undantag, hemliga, spar: false, mal: a.adress });
  try { await bs.page.goto(a.adress, { waitUntil: 'load', timeout: 45000 }); await bs.page.waitForTimeout(300); rapport.svep = await svep(bs.page); }
  catch (e) { rapport.svep = { fel: String(e.message || e).slice(0, 200) }; }
  finally { await bs.stang(); }
  skriv(a.ut, 'SVEP.json', rapport.svep);
}
rapport.spar_privat = !!undantag;
if (undantag) rapport.not += '; spårfilerna bär skyddsundantaget i nätverksposter och är privata (delas aldrig); JSON-loggen är redigerad';
skriv(a.ut, 'INSPEKTION.json', rapport);
if (extraktSel) {
  const extraktMd = Object.keys(extraktVyer).sort((p, q) => Number(p) - Number(q)).map((vy) => { const v = extraktVyer[vy]; return sammanfatta(vy, v.x, v.bild, { interaktiva: v.r.interaktiva, rorelse: v.r.rorelse, spar: v.r.spar_sammanfattning }); });
  skriv(a.ut, 'EXTRAKT.md', ['# Extrakt — ' + a.adress + ' (' + rapport.tid + ')', '', MATERIALNOT, '',
    'Uppmätt i samma webbläsarsession som skärmbilderna (kontroller/webblasare/extrahera.mjs). Värdena är mätningar; tolkningen (uppskattat, valt för kunden) skrivs i REFERENSER.md och DESIGN.md.' + (medKod ? ' Det kuraterade underlaget per sektion står i SEKTIONER.md.' : ' Granskarens form: inga regler, utdrag eller SEKTIONER.md.'), '',
    ...(rapport.svep ? [svepsammanfattning(rapport.svep), ''] : []), ...extraktMd].join('\n') + '\n');
  if (medKod) skriv(a.ut, 'SEKTIONER.md', sektionsunderlag(a.adress, rapport.tid, Object.fromEntries(Object.entries(extraktVyer).map(([vy, v]) => [vy, { x: v.x, rutor: v.rutor, skarmhojd: v.skarmhojd }]))));
}
const md = ['# Inspektion — ' + a.adress + ' (' + rapport.tid + ')', '', 'Kontext bifogad: ' + (kontext.map(k => k.namn + ' ' + k.sha256.slice(0, 12)).join(', ') || 'ingen'), ''];
for (const [vy, r] of Object.entries(rapport.vyer)) md.push(`## Vy ${vy} — ${r.namn}`, '', `- status ${r.status}, titel "${r.titel}", h1 ${r.h1}, horisontell spill ${r.spill?.spill}`, ...(r.tillstand?.reflow_320x180 ? [`- 320×180 (400 % zoom): spill ${r.tillstand.reflow_320x180.spill}; fasta eller klibbiga element i vyn: ${r.tillstand.reflow_320x180.fasta.length ? r.tillstand.reflow_320x180.fasta.map((f) => `${f.element} ${f.hojd} px (${f.andel} %)`).join(', ') : 'inga'}`] : []), `- konsol ${r.konsol.length} (fel: ${r.konsol.filter(x => x.typ === 'error').length}), sidfel ${r.sidfel.length}, nätverksfel ${r.natverk.fel.length}, blockerade ${r.natverk.blockerade.length}`, `- tangentbord: ${r.tillstand.tangentbord?.length ?? '-'} steg, utan synlig fokus ${r.tillstand.tangentbord_utan_synlig_fokus ?? '-'}; reflow 320 spill ${r.tillstand.reflow_320?.spill ?? '-'}`, ...(r.tillstand.meny ? [`- meny: klickad ${r.tillstand.meny.klickad}, expanded ${r.tillstand.meny.expanded}; ${r.tillstand.meny.bild ? 'bild ' + r.tillstand.meny.bild : 'ingen bild: ' + r.tillstand.meny.skal}`] : []), ...(['hover', 'fokus'].filter((n) => r.tillstand[n + '_lista']).map((n) => `- ${n}: ${r.tillstand[n + '_lista'].map((p) => `${p.valjare} → ${basename(p.bild)}${p.fel ? ' (fel: ' + p.fel + ')' : ''}`).join('; ')}`)), `- interaktiva element: ${r.interaktiva?.totalt ?? '-'}`, ...(r.rorelse_motor && !r.rorelse_motor.fel ? [`- rörelse utanför getAnimations: requestAnimationFrame ${r.rorelse_motor.raf_per_s} per sekund, canvas ${r.rorelse_motor.canvas}, spelande video ${r.rorelse_motor.video_spelar}${r.rorelse_motor.sekvens ? '; bildsekvens ' + r.rorelse_motor.sekvens.map((x) => basename(x)).join(', ') : ''}`] : []), `- bilder: ${r.forsta_vyn}, ${r.hela_sidan}; träd ${r.tillganglighetstrad}; spår ${r.spar}`, '');
if (rapport.svep && !rapport.svep.fel) md.push(`Svepet: ${rapport.svep.brytpunkter.length} brytpunkter (SVEP.json).`, '');
md.push(rapport.not);
skriv(a.ut, 'INSPEKTION.md', md.join('\n') + '\n');
console.log(JSON.stringify({ ut: a.ut, vyer: Object.keys(rapport.vyer), blockerade: Object.values(rapport.vyer).reduce((s, r) => s + r.natverk.blockerade.length, 0), fel: Object.values(rapport.vyer).filter(r => r.fel).length }));
