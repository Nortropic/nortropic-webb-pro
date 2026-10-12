// rendera.mjs — en version ur Claude Design (dukens .dc.html-ritningar) renderad lokalt med Design-typens egen körmiljö
// (dc-runtime.js ur typens release, sparad privat i underlag/<slug>/design/runtime/), så att Code kan se, mäta och pröva
// exakt den källa som duken visar (kunskap/claude-design.md, Observation). Bilderna är inte skärmbilder ur Designs
// gränssnitt: de är ritningens källa i en vanlig Chromium-sida i den bredd som anges, och märks så i BILDER.json.
//   node kontroller/designfas/rendera.mjs --sida <katalog> --ritningar A.dc.html,B.dc.html --ut <katalog> [--kontroll] [--bredder 390,768,1440]
// Katalogen --sida har ritningarna, support.js (körmiljön) och _blob/<id> (dukens uppladdade tillgångar, med
// _blob/index.json {id: medietyp}). Skriver <ut>/bilder/<ritning>-<bredd>.png, <ritning>-390-meny.png när en menyknapp
// (aria-expanded i sidhuvudet eller navigationen) finns, och <ut>/BILDER.json med mätningarna per bredd: LCP-kandidaten,
// layoutskiften, bildernas storlek mot visad storlek, rörelsen vid laddningen och efter 5,5 s, och samma rörelse med
// prefers-reduced-motion: reduce i 390 och 1440 (varningar, inte fel); med --kontroll också axe (med menyn öppen och
// formulären skickade tomma), stilrapporten och impeccables detektor (med IMPECCABLE_MOTOR) i <ut>/kontroll/. Dessutom reflow i 320, synlig fokus för de tio första
// tabbstegen i 390 och 1440 (bild med och utan fokus) och om sidan förändras mellan 6 och 7 s utan interaktion. LCP och
// CLS här gäller ritningen lokalt, inte fältdata. Exit 0 när allt renderades, 1 när en ritning föll
// (sidfel, ingen h1, sidledsspill), 2 vid fel i anropet. Inget lämnar maskinen utom Google Fonts-länkar som ritningen själv har.
import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync, statSync } from 'node:fs';
import { join, extname, resolve, dirname, sep } from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const arg = (n, std) => { const i = process.argv.indexOf('--' + n); return i >= 0 ? process.argv[i + 1] : std; };
const sida = arg('sida');
const ut = arg('ut');
const ritningar = (arg('ritningar') || '').split(',').filter(Boolean);
const bredder = (arg('bredder') || '390,768,1440').split(',').map((x) => parseInt(x, 10)).filter((x) => x >= 280 && x <= 2560);
const kontroll = process.argv.includes('--kontroll');
const NAMN = /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,200}\.dc\.html$/;
if (!sida || !ut || !ritningar.length || ritningar.some((r) => !NAMN.test(r)) || !bredder.length) {
  console.error('användning: node kontroller/designfas/rendera.mjs --sida KATALOG --ritningar A.dc.html[,B.dc.html] --ut KATALOG [--kontroll] [--bredder 390,768,1440]');
  process.exit(2);
}
const rot = resolve(sida);
if (!existsSync(join(rot, 'support.js'))) { console.error('körmiljön saknas: ' + join(rot, 'support.js')); process.exit(2); }
const bloblista = existsSync(join(rot, '_blob', 'index.json')) ? JSON.parse(readFileSync(join(rot, '_blob', 'index.json'), 'utf-8')) : {};
const TYP = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.css': 'text/css' };
const begarda = [];
const srv = createServer((req, res) => {
  const vag = decodeURIComponent((req.url || '/').split('?')[0]);
  const p = resolve(join(rot, vag));
  if (!(p + sep).startsWith(rot + sep) && p !== rot) { res.writeHead(403); return res.end(); }
  let typ = TYP[extname(p)];
  const blob = vag.match(/^\/_blob\/([0-9a-f]{32})$/);
  if (blob) { typ = bloblista[blob[1]]; begarda.push(blob[1]); }
  if (!existsSync(p) || !statSync(p).isFile() || !typ) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': typ, 'cache-control': 'no-store' });
  res.end(readFileSync(p));
}).listen(0, '127.0.0.1');
await new Promise((r) => srv.once('listening', r));
const port = srv.address().port;
const bas = `http://127.0.0.1:${port}`;
mkdirSync(join(ut, 'bilder'), { recursive: true });

const MENY = 'header button[aria-expanded], nav button[aria-expanded], [role=banner] button[aria-expanded], button[aria-controls][aria-expanded]';
// mätningarna i sidan (tillägget 2026-10-12, punkt 5): LCP-kandidaten och layoutskiften ur PerformanceObserver, före laddningen
const MATARE = `window.__nwp = { lcp: [], cls: 0 };
try {
  new PerformanceObserver((l) => l.getEntries().forEach((e) => { const el = e.element; window.__nwp.lcp.push({ tid: Math.round(e.startTime),
    storlek: e.size, tagg: el ? el.tagName.toLowerCase() : null, src: el && el.currentSrc ? el.currentSrc.slice(-60) : (e.url || '').slice(-60),
    lazy: el ? el.getAttribute('loading') === 'lazy' : null, prio: el ? el.getAttribute('fetchpriority') : null,
    text: el && !el.currentSrc ? (el.textContent || '').trim().slice(0, 60) : null }); })).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver((l) => l.getEntries().forEach((e) => { if (!e.hadRecentInput) window.__nwp.cls += e.value; })).observe({ type: 'layout-shift', buffered: true });
} catch (e) { window.__nwp.fel = String(e); }`;
const ROREDATA = () => {
  const a = document.getAnimations();
  return { antal: a.length, oandliga: a.filter((x) => x.effect && x.effect.getComputedTiming().iterations === Infinity).length,
    pagar: a.filter((x) => x.playState === 'running').length };
};
const b = await chromium.launch();
const post = { tid: new Date().toISOString(), kalla: 'lokal rendering av dukens källa med Design-typens körmiljö (inte en skärmbild ur Designs gränssnitt)', bredder, ritningar: {} };
let fallna = 0;
for (const r of ritningar) {
  const rp = { bilder: {}, fel: [], varningar: [], konsol: [], matt: {} };
  for (const w of bredder) {
    // ingen mobilemulering: ritningarna saknar viewport-meta, och duken visar dem i en ram med ritningens bredd, så en
    // vanlig vy i samma bredd är det duken visar (med isMobile lägger Chromium sidan i 980 px; prövat 2026-10-12)
    const ctx = await b.newContext({ viewport: { width: w, height: 900 }, deviceScaleFactor: w <= 430 ? 2 : 1 });
    await ctx.addInitScript(MATARE);
    const pg = await ctx.newPage();
    pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') rp.konsol.push(`${w} ${m.type()}: ${m.text()}`.slice(0, 300)); });
    pg.on('pageerror', (e) => rp.fel.push(`${w} sidfel: ${e.message}`.slice(0, 300)));
    await pg.goto(`${bas}/${r}`, { waitUntil: 'networkidle', timeout: 60000 });
    await pg.waitForTimeout(700);
    const info = await pg.evaluate((menysel) => {
      const h1 = [...document.querySelectorAll('h1')].map((x) => x.textContent.trim().slice(0, 120));
      const knapp = document.querySelector(menysel);
      const synlig = knapp && getComputedStyle(knapp).display !== 'none' && knapp.getBoundingClientRect().width > 0;
      const bilder = [...document.images].map((i) => ({ src: i.getAttribute('src'), laddad: i.complete && i.naturalWidth > 0, alt: i.getAttribute('alt') }));
      const sma = [...document.querySelectorAll('a[href], button, input, select, textarea')].filter((e) => {
        const x = e.getBoundingClientRect(); return x.width > 0 && x.height > 0 && (x.width < 24 || x.height < 24);
      }).length;
      return { h1, sidled: document.documentElement.scrollWidth > innerWidth + 1, hojd: document.documentElement.scrollHeight,
        menyknapp: !!synlig, bilder, sma_klickytor: sma, lang: document.documentElement.lang, titel: document.title,
        formular: document.forms.length };
    }, MENY);
    // bildernas storlek mot visad storlek (× pixeltäthet) och LCP-kandidaten; rörelsen nu och efter 5,5 s
    const matt = await pg.evaluate(() => {
      const dpr = devicePixelRatio || 1;
      const bilder = [...document.images].filter((i) => i.complete && i.naturalWidth > 0).map((i) => {
        const x = i.getBoundingClientRect();
        const behov = Math.round(x.width * dpr);
        return { src: new URL(i.currentSrc || i.src, location.href).pathname.slice(-60), naturlig: i.naturalWidth, visad: Math.round(x.width), behov,
          kvot: behov ? +(i.naturalWidth / behov).toFixed(2) : null, lazy: i.getAttribute('loading') === 'lazy', i_forsta_vyn: x.top < innerHeight };
      });
      return { bilder, lcp: (window.__nwp.lcp || []).slice(-1)[0] || null, cls: +((window.__nwp.cls || 0).toFixed(4)) };
    });
    const rorelse0 = await pg.evaluate(ROREDATA);
    await pg.waitForTimeout(5500);
    const rorelse55 = await pg.evaluate(ROREDATA);
    const stam = r.replace(/\.dc\.html$/, '');
    const fil = `${stam}-${w}.png`;
    await pg.screenshot({ path: join(ut, 'bilder', fil), fullPage: true });
    rp.bilder[w] = { fil: `bilder/${fil}`, ...info };
    rp.matt = rp.matt || {};
    rp.matt[w] = { lcp: matt.lcp, cls: matt.cls, bildstorlekar: matt.bilder, rorelse: { vid_laddning: rorelse0, efter_5_5_s: rorelse55 } };
    rp.varningar = rp.varningar || [];
    for (const x of matt.bilder) {
      if (x.kvot !== null && x.kvot < 0.9) rp.varningar.push(`${w}: bilden ${x.src} är ${x.naturlig} px bred men visas i ${x.behov} enhetspixlar (suddig)`);
      if (x.kvot !== null && x.kvot > 2.5 && x.naturlig > 1200) rp.varningar.push(`${w}: bilden ${x.src} är ${x.naturlig} px för ${x.behov} enhetspixlar (överstor; bygget ska ge srcset)`);
    }
    if (matt.lcp && matt.lcp.lazy) rp.varningar.push(`${w}: LCP-elementet (${matt.lcp.tagg}) har loading=lazy`);
    if (matt.cls > 0.1) rp.varningar.push(`${w}: layoutskiften ${matt.cls} (> 0,1) under laddningen`);
    if (rorelse55.pagar > 0) rp.varningar.push(`${w}: ${rorelse55.pagar} animation(er) pågår efter 5,5 s (WCAG 2.2.2 kräver paus, stopp eller dölj för rörelse > 5 s)`);
    if (info.sidled) rp.fel.push(`${w}: sidledsspill`);
    if (!info.h1.length) rp.fel.push(`${w}: ingen h1`);
    if (info.bilder.some((x) => !x.laddad)) rp.fel.push(`${w}: ${info.bilder.filter((x) => !x.laddad).length} bild(er) laddades inte`);
    if (info.menyknapp) {
      const k = pg.locator(MENY).first();
      await k.click();
      await pg.waitForTimeout(400);
      const oppen = await k.getAttribute('aria-expanded');
      const mfil = `${stam}-${w}-meny.png`;
      await pg.screenshot({ path: join(ut, 'bilder', mfil), fullPage: false });
      rp.bilder[`${w}-meny`] = { fil: `bilder/${mfil}`, aria_expanded_efter_klick: oppen };
      if (oppen !== 'true') rp.fel.push(`${w}: menyknappen öppnade inget (aria-expanded ${oppen})`);
    }
    await ctx.close();
  }
  // reflow i 320 (WCAG 1.4.10), synlig fokus vid tabb (2.4.7) och förändring utan interaktion efter 5 s (2.2.2; fångar också
  // rörelse som skript driver med requestAnimationFrame, som getAnimations inte ser)
  {
    const ctx = await b.newContext({ viewport: { width: 320, height: 640 } });
    const pg = await ctx.newPage();
    await pg.goto(`${bas}/${r}`, { waitUntil: 'networkidle', timeout: 60000 });
    await pg.waitForTimeout(500);
    const spill = await pg.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    rp.reflow_320 = { sidledsspill_px: spill };
    if (spill > 1) rp.varningar.push(`320: sidledsspill ${spill} px (WCAG 1.4.10)`);
    await ctx.close();
  }
  rp.fokus = {};
  rp.stillhet = {};
  for (const w of bredder.filter((x) => x === 390 || x === 1440)) {
    const ctx = await b.newContext({ viewport: { width: w, height: 900 } });
    const pg = await ctx.newPage();
    await pg.goto(`${bas}/${r}`, { waitUntil: 'networkidle', timeout: 60000 });
    await pg.waitForTimeout(6000);
    const a1 = await pg.screenshot();
    await pg.waitForTimeout(1000);
    const a2 = await pg.screenshot();
    rp.stillhet[w] = { lika_6_och_7_s: a1.equals(a2) };
    if (!a1.equals(a2)) rp.varningar.push(`${w}: sidan förändras mellan 6 och 7 s utan interaktion (WCAG 2.2.2 kräver paus, stopp eller dölj)`);
    const resultat = [];
    for (let i = 0; i < 10; i++) {
      await pg.keyboard.press('Tab');
      await pg.waitForTimeout(120);
      const box = await pg.evaluate(() => {
        const e = document.activeElement;
        if (!e || e === document.body) return null;
        e.scrollIntoView({ block: 'center' });
        const x = e.getBoundingClientRect();
        return { tagg: e.tagName.toLowerCase(), text: (e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 40),
          x: Math.max(0, x.left - 8), y: Math.max(0, x.top - 8), w: x.width + 16, h: x.height + 16 };
      });
      if (!box || box.w < 4 || box.h < 4) break;
      const clip = { x: box.x, y: box.y, width: Math.min(box.w, w - box.x), height: Math.min(box.h, 900 - box.y) };
      if (clip.width < 4 || clip.height < 4) continue;
      const med = await pg.screenshot({ clip });
      await pg.evaluate(() => document.activeElement && document.activeElement.blur());
      await pg.waitForTimeout(80);
      const utan = await pg.screenshot({ clip });
      await pg.evaluate((t) => { const e = [...document.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')].find((x) => (x.getAttribute('aria-label') || x.textContent || '').trim().slice(0, 40) === t); if (e) e.focus({ focusVisible: true }); }, box.text);
      resultat.push({ tagg: box.tagg, text: box.text, synlig: !med.equals(utan) });
    }
    rp.fokus[w] = resultat;
    const osynliga = resultat.filter((x) => !x.synlig);
    if (osynliga.length) rp.varningar.push(`${w}: ${osynliga.length} av ${resultat.length} tabbade element ändrar inget synligt vid fokus (${osynliga.map((x) => x.tagg + ' "' + x.text + '"').join(', ').slice(0, 200)})`);
    await ctx.close();
  }
  rp.reducerad_rorelse = {};
  for (const w of bredder.filter((x) => x === 390 || x === 1440)) {
    const ctx = await b.newContext({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
    const pg = await ctx.newPage();
    await pg.goto(`${bas}/${r}`, { waitUntil: 'networkidle', timeout: 60000 });
    await pg.waitForTimeout(700);
    const nu_ = await pg.evaluate(ROREDATA);
    const vanlig = (rp.matt[w] || {}).rorelse || {};
    rp.reducerad_rorelse[w] = { reducerad: nu_, utan: vanlig.vid_laddning || null };
    if (nu_.oandliga > 0 || (vanlig.vid_laddning && nu_.antal > 0 && nu_.antal >= vanlig.vid_laddning.antal && vanlig.vid_laddning.antal > 0)) {
      rp.varningar.push(`${w}: med prefers-reduced-motion: reduce körs ${nu_.antal} animation(er) (${nu_.oandliga} oändliga); utan: ${(vanlig.vid_laddning || {}).antal}`);
    }
    await ctx.close();
  }
  if (rp.fel.length) fallna += 1;
  post.ritningar[r] = rp;
}
await b.close();
post.tillgangar_begarda = [...new Set(begarda)].sort();

if (kontroll) {
  const kontroller = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  // Kontrollerna körs asynkront: sidan serveras av servern i den här processen, och ett synkront barn (spawnSync)
  // blockerar händelseloopen, så att axe, stilrapporten och detektorn aldrig fick någon sida (ERR_FAILED; upptäckt
  // 2026-10-13, provet krävde bara att nyckeln fanns).
  const kor = (cmd, args, timeout) => new Promise((klar) => {
    let stdout = '', stderr = '', slut = false;
    const p = spawn(cmd, args, { env: process.env });
    const t = setTimeout(() => p.kill('SIGKILL'), timeout);
    p.stdout.on('data', (d) => { stdout += d; });
    p.stderr.on('data', (d) => { stderr += d; });
    const avsluta = (status, extra = '') => { if (!slut) { slut = true; clearTimeout(t); klar({ status, stdout, stderr: stderr + extra }); } };
    p.on('error', (e) => avsluta(null, String(e)));
    p.on('close', (code) => avsluta(code));
  });
  const sidor = ritningar.map((r) => '/' + r).join(',');
  const k = join(ut, 'kontroll');
  mkdirSync(k, { recursive: true });
  post.kontroll = {};
  for (const [namn, skript, extra] of [['axe', 'axe.mjs', ['--tillstand=meny,formularfel']], ['stil', 'stil.mjs', []]]) {
    const r = await kor(process.execPath, [join(kontroller, skript), `--url=${bas}`, `--sidor=${sidor}`, `--ut=${join(k, namn)}`, ...extra], 300000);
    post.kontroll[namn] = { slutkod: r.status, utdata: (r.stdout || '').slice(-1500), fel: (r.stderr || '').slice(-1500) };
  }
  // impeccables detektor på den renderade ritningen i 390 och 1440 (critique.md: "A skipped detector is a failed critique
  // run"; valideringen 2026-10-12): motorn får versionens adress och läser sidan i sin egen webbläsare
  if (process.env.IMPECCABLE_MOTOR) {
    const d = join(k, 'detektor');
    mkdirSync(d, { recursive: true });
    post.kontroll.detektor = {};
    const detektera = async (vp, r, scope) => {
      const x = await kor(process.env.IMPECCABLE_MOTOR, ['detect', '--json', '--no-config', ...(scope ? ['--scope', scope] : []), '--viewport', vp,
        `${bas}/${r}`], 240000);
      let fynd = null;
      try { const j = JSON.parse(x.stdout || '[]'); fynd = Array.isArray(j) ? j : (j.findings || j.results || []); } catch { /* */ }
      return [x, fynd && fynd.filter((f) => f && typeof f === 'object')];
    };
    for (const r of ritningar) {
      for (const vp of ['390x844', '1440x900']) {
        let [x, fynd] = await detektera(vp, r);
        // området per regel ur motorns --scope (type, layout), så att stationerna typografi, komposition och responsiv läser
        // sina fynd (valideringen 2026-10-12, skills del 1 åtgärd 4); en regel utanför båda har inget område
        const omrade = {};
        if (fynd && fynd.length) {
          for (const [sc, namn] of [['type', 'typografi'], ['layout', 'layout']]) {
            for (const f of (await detektera(vp, r, sc))[1] || []) if (f.antipattern) omrade[f.antipattern] = namn;
          }
        }
        // bara regelkatalogens fält: kodutdrag och sidans text får aldrig nå den blinda kritiken (detektor.for_granskaren)
        if (fynd) fynd = fynd.map((f) => Object.fromEntries([
          ...['antipattern', 'rule', 'name', 'description', 'severity', 'category', 'advisory'].filter((n) => f[n] !== undefined).map((n) => [n, f[n]]),
          ...(omrade[f.antipattern] ? [['omrade', omrade[f.antipattern]]] : [])]));
        const fil = join(d, `${r}-${vp.split('x')[0]}.json`);
        writeFileSync(fil, JSON.stringify(fynd && x.status !== 1 ? fynd : { fel: (x.stderr || '').slice(-800), slutkod: x.status }, null, 1) + '\n');
        post.kontroll.detektor[`${r} ${vp}`] = fynd && x.status !== 1 ? { fynd: fynd.length, slutkod: x.status }
          : { fel: fynd ? 'motorn kunde inte skanna sidan (slutkod 1)' : 'motorn gav inget läsbart svar', slutkod: x.status };
      }
    }
  }
}
srv.close();
writeFileSync(join(ut, 'BILDER.json'), JSON.stringify(post, null, 1) + '\n');
console.log(`${ritningar.length} ritning(ar) i ${bredder.join('/')}: ${fallna ? fallna + ' med brister' : 'utan brister'}${kontroll ? '; kontrollerna i ' + join(ut, 'kontroll') : ''}`);
process.exit(fallna ? 1 : 0);
