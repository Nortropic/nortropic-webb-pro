// Gemensamt för Digitalas webbläsarväg (Playwright 1.63, pinnad i package.json): start, vyer, värdverkställd
// ursprungsgräns, logg med redigerade hemligheter, spår. Ingen modell här; modellen (utvecklare, QA eller avskärmad
// besökare) sitter i sessionen som anropar verktygen.
import { chromium } from 'playwright';
import { createHash } from 'node:crypto';
import http from 'node:http';
import net from 'node:net';
import dns from 'node:dns';
import { readFileSync, statSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export const VYER = { '390': { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'mobil (emulerad, inte fysisk enhet)' },
                      '768': { viewport: { width: 768, height: 1024 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'surfplatta (emulerad)' },
                      '1440': { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, isMobile: false, hasTouch: false, namn: 'dator' },
                      '320': { viewport: { width: 320, height: 640 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'reflow 320 px (WCAG 1.4.10)' } };
const HEMLIGA_NAMN = /^(authorization|cookie|set-cookie|x-vercel-protection-bypass|x-vercel-set-bypass-cookie|proxy-authorization)$/i;
const HEMLIGA_PARAM = /^(x-vercel-protection-bypass|x-vercel-set-bypass-cookie|token|key|api_key|apikey|secret|password)$/i;

export function args(argv) {
  const ut = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const [k, v] = a.slice(2).split(/=(.*)/s);
      if (v !== undefined) ut[k] = v;
      else if (argv[i + 1] !== undefined && !argv[i + 1].startsWith('--')) ut[k] = argv[++i];
      else ut[k] = true;
    } else ut._.push(a);
  }
  return ut;
}

export function sha256(buf) { return createHash('sha256').update(buf).digest('hex'); }
export function nu() { return new Date().toISOString().replace(/\.\d+Z$/, 'Z'); }

/** Skyddsundantag: privat fil (rättighet 0600, en rad ≥ 16 tecken, utanför tmp). Värdet skrivs aldrig ut. */
export function lasUndantag(fil) {
  if (!fil) return null;
  const st = statSync(fil);
  if ((st.mode & 0o077) !== 0) throw new Error('undantagsfilen ska ha rättighet 0600');
  if (/^\/(tmp|etc|var\/folders)\//.test(fil) || fil.startsWith('/private/tmp')) throw new Error('undantagsfilen får inte ligga i tmp, etc eller var/folders');
  const v = readFileSync(fil, 'utf8').trim().split('\n')[0].trim();
  if (v.length < 16) throw new Error('undantagsfilen ska bära en rad om minst 16 tecken');
  return v;
}

export function hemligheter(fil) {
  if (!fil) return [];
  return readFileSync(fil, 'utf8').split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#')).map(l => l.split('=').slice(1).join('=').trim()).filter(v => v.length >= 8);
}

export function redigerare(varden) {
  return (text) => {
    let t = String(text);
    for (const v of varden) if (v) t = t.split(v).join('[REDIGERAT]');
    return t;
  };
}

export function redigeraUrl(url) {
  try {
    const u = new URL(url);
    for (const k of [...u.searchParams.keys()]) if (HEMLIGA_PARAM.test(k)) u.searchParams.set(k, 'REDIGERAT');
    return u.toString();
  } catch { return url; }
}

export function origin(url) { return new URL(url).origin; }

const LOKALA = new Set(['localhost', '127.0.0.1', '[::1]', '::1']);
/** Tjänstens domänpolicy (NWP_NAT_TILLATNA, kommaseparerad, '*.x' täcker underdomäner): satt när skriptet körs av
 *  kontroller/webbtjanst.py. Localhost är alltid tillåtet; utan variabeln gäller bara skriptets egna ursprung (tillat). */
export function natpolicy() {
  const v = process.env.NWP_NAT_TILLATNA;
  if (v === undefined) return null;
  return v.split(',').map((x) => x.trim().toLowerCase()).filter(Boolean);
}
export function vardTillaten(hostname, policy) {
  const h = String(hostname || '').toLowerCase().replace(/\.$/, '');
  if (!h) return false;
  if (LOKALA.has(h)) return true;
  if (!policy) return true;
  return policy.some((m) => (m.startsWith('*.') ? (h === m.slice(2) || h.endsWith(m.slice(1))) : h === m));
}
export function arLokal(url) { try { return LOKALA.has(new URL(url).hostname.toLowerCase()); } catch { return false; } }

const OMDIRIGERING = new Set([301, 302, 303, 307, 308]);
function arOmdirigering(svar) { return OMDIRIGERING.has(svar.status()) && svar.headers()['location'] !== undefined; }

/** Adress i det egna nätet (loopback, privat, länklokal, multicast, IPv6-motsvarigheter)? */
export function privatAdress(ip) {
  const v = String(ip).toLowerCase();
  if (net.isIPv4(v)) {
    const [a, b] = v.split('.').map(Number);
    return a === 0 || a === 10 || a === 127 || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || a >= 224;
  }
  const m = v.match(/^(?:::ffff:)?(\d+\.\d+\.\d+\.\d+)$/); if (m) return privatAdress(m[1]);
  return v === '::1' || v === '::' || v.startsWith('fe80:') || v.startsWith('fc') || v.startsWith('fd') || v.startsWith('ff');
}

// Provuppslag (bara i rökprovet): NWP_PROV_UPPSLAG="värd=ip;värd=ip" ersätter DNS, så att adresskontrollen kan prövas utan nät.
function provuppslag() {
  const v = process.env.NWP_PROV_UPPSLAG; if (!v) return null;
  const m = new Map(); for (const d of v.split(';')) { const [h, ip] = d.split('='); if (h && ip) m.set(h.trim().toLowerCase(), ip.trim()); } return m;
}

/** Adressen proxyn ansluter till för ett värdnamn: localhost-namn ger loopback; annars DNS, och varje adress måste vara
 *  publik. En tillåten domän som pekar in i det egna nätet ansluts aldrig (Codex R24: domänlistan ersätter inte
 *  adresskontrollen; OWASP om SSRF via DNS). */
export async function uppslag(host) {
  const h = String(host).toLowerCase().replace(/^\[|\]$/g, '');
  if (LOKALA.has(h) || h === '[::1]') return { ip: '127.0.0.1' };
  if (net.isIP(h)) return privatAdress(h) ? { fel: 'adress i det egna nätet' } : { ip: h };
  let adresser;
  const prov = provuppslag();
  if (prov) { if (!prov.has(h)) return { fel: 'gick inte att slå upp (provuppslag)' }; adresser = [prov.get(h)]; }
  else {
    try { adresser = (await dns.promises.lookup(h, { all: true })).map((x) => x.address); } catch { return { fel: 'gick inte att slå upp' }; }
  }
  if (!adresser.length) return { fel: 'gick inte att slå upp' };
  if (adresser.some(privatAdress)) return { fel: 'pekar in i det egna nätet (' + adresser.join(', ') + ')' };
  return { ip: adresser[0] };
}

const LAS = new Set(['GET', 'HEAD', 'OPTIONS']);

/** Nätgränsen för webbläsaren: en filtrerande proxy på 127.0.0.1 som Chromium startas med. Varje anslutning (http och
 *  CONNECT för https) prövas mot tjänstens domänpolicy och skriptets tillåtna ursprung, värdnamnet slås upp här och
 *  anslutningen görs till den godkända, publika adressen (Host-huvudet och TLS-namnet är värdnamnet); skrivande
 *  http-anrop till annat än localhost nekas (för https sköter route-vakten metoden). Allt nekat får 403/405 och loggas.
 *  Omdirigeringar och annat som route-vakten inte ser (Playwright följer dem utan ny kontroll) stoppas här (Codex R23/R24). */
async function startaProxy(tillaten, blockera) {
  const srv = http.createServer(async (req, res) => {
    let u; try { u = new URL(req.url); } catch { res.writeHead(400); return res.end(); }
    const port = u.port || '80';
    const neka = (kod, skal) => { blockera(req.method, u.toString(), skal); res.writeHead(kod, { 'content-type': 'text/plain' }); res.end('blockerad'); };
    if (!tillaten(u.hostname, port, 'http:')) return neka(403, 'utanför tillåtna ursprung');
    if (!LOKALA.has(u.hostname.toLowerCase()) && !LAS.has(req.method)) return neka(405, 'skrivande anrop till annan sajt');
    const upp = await uppslag(u.hostname);
    if (!upp.ip) return neka(403, upp.fel);
    const p = http.request({ host: upp.ip, port: Number(port), method: req.method, path: u.pathname + u.search, headers: { ...req.headers, host: u.host } }, (r) => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
    p.on('error', () => { try { res.writeHead(502); res.end(); } catch {} });
    req.pipe(p);
  });
  srv.on('connect', async (req, sock, head) => {
    const i = req.url.lastIndexOf(':'); const host = (i > 0 ? req.url.slice(0, i) : req.url).replace(/^\[|\]$/g, ''); const port = i > 0 ? req.url.slice(i + 1) : '443';
    const neka = (skal) => { blockera('CONNECT', 'https://' + req.url + '/', skal); sock.write('HTTP/1.1 403 Forbidden\r\n\r\n'); sock.destroy(); };
    if (!tillaten(host, port, 'https:')) return neka('utanför tillåtna ursprung');
    const upp = await uppslag(host);
    if (!upp.ip) return neka(upp.fel);
    const s = net.connect(Number(port) || 443, upp.ip, () => { sock.write('HTTP/1.1 200 Connection Established\r\n\r\n'); if (head && head.length) s.write(head); s.pipe(sock); sock.pipe(s); });
    s.on('error', () => sock.destroy()); sock.on('error', () => s.destroy());
  });
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  return { server: 'http://127.0.0.1:' + srv.address().port, stang: () => new Promise((r) => srv.close(() => r())) };
}

// värd:port tillåten för proxyn: localhost alltid; annars domänpolicyn och, när skriptet angett ursprung, just de ursprungen
function anslutningsvakt(policy, tillatna) {
  return (host, port, protokoll) => {
    const h = String(host).toLowerCase();
    if (LOKALA.has(h)) return true;
    if (!vardTillaten(h, policy)) return false;
    if (!tillatna.size) return true;
    const std = protokoll === 'https:' ? '443' : '80';
    return tillatna.has(protokoll + '//' + h + (String(port) === std ? '' : ':' + port));
  };
}

/** Nätgränsen för skript som startar Chromium själva (axe, stil, sida, ikoner, lighthouse): i tjänstens läge
 *  (NWP_NAT_TILLATNA satt, kontroller/webbtjanst.py) en filtrerande proxy enligt domänpolicyn och de givna ursprungen,
 *  som Chromium startas genom (playwright-alternativ eller Chrome-flagga); annars null och allt som förut. */
export async function natgrans(ursprung = []) {
  const policy = natpolicy();
  if (policy === null) return null;
  const tillatna = new Set(ursprung.filter(Boolean).map((o) => origin(o)));
  const blockerade = [];
  const proxy = await startaProxy(anslutningsvakt(policy, tillatna), (metod, url, skal) => blockerade.push({ metod, url: redigeraUrl(url), tid: nu(), skal }));
  return { server: proxy.server, playwright: { proxy: { server: proxy.server } }, chromeFlag: '--proxy-server=' + proxy.server.replace(/^http:\/\//, ''), blockerade, stang: proxy.stang };
}

/** Route-vakten: samma regler i oppna och i skript som skapar sina kontexter själva (lasvakt). Värd mot policyn,
 *  ursprung mot skriptets lista, skrivande anrop bara till skrivbara (lokala) ursprung, WebSockets blockerade, varje
 *  omdirigeringshopp prövat; ett skrivande anrop som förs vidare med 307/308 följs här, hopp för hopp, bara till
 *  skrivbara ursprung (Codex R24: lokal POST → 307 lokalt → 307 extern domän stoppas). */
async function installeraVakt(ctx, { policy, tillatna, skrivbaraSet, undantag, malUrsprung, logg }) {
  const blockera = (req, skal) => { logg.blockerade.push({ metod: req.method(), url: redigeraUrl(req.url()), typ: req.resourceType(), tid: nu(), ...(skal ? { skal } : {}) }); };
  await ctx.routeWebSocket('**/*', (ws) => { logg.blockerade.push({ metod: 'WS', url: redigeraUrl(ws.url()), typ: 'websocket', tid: nu(), skal: 'websocket blockerad' }); });
  await ctx.route('**/*', async (route) => {
    const req = route.request(); const u = req.url();
    let o, vard; try { const p = new URL(u); o = p.origin; vard = p.hostname; } catch { return route.abort('blockedbyclient'); }
    if (u.startsWith('data:') || u.startsWith('blob:')) return route.continue();
    if (!vardTillaten(vard, policy)) { blockera(req, 'utanför tjänstens domänlista'); return route.abort('blockedbyclient'); }
    if (tillatna.size && !tillatna.has(o)) { blockera(req); return route.abort('blockedbyclient'); }
    if (!LAS.has(req.method()) && !skrivbaraSet.has(o)) { blockera(req, 'skrivande anrop under läsande inspektion'); return route.abort('blockedbyclient'); }
    const headers = { ...req.headers() };
    if (undantag && o === malUrsprung) headers['x-vercel-protection-bypass'] = undantag;  // bara målets ursprung, aldrig tredje part
    let svar;
    try { svar = await route.fetch({ headers, maxRedirects: 0 }); }
    catch (e) { logg.natverk.push({ metod: req.method(), url: redigeraUrl(u), id: sha256(String(u).split('#')[0]), status: null, fel: String(e.message).slice(0, 200), tid: nu() }); return route.abort('failed'); }
    let aktuell = u, hopp = 0;
    while (arOmdirigering(svar)) {
      let mal, m; try { mal = new URL(svar.headers()['location'], aktuell).toString(); m = new URL(mal); } catch { blockera(req, 'ogiltig omdirigering'); return route.abort('blockedbyclient'); }
      logg.omdirigeringar.push({ metod: req.method(), fran: redigeraUrl(aktuell), till: redigeraUrl(mal), status: svar.status(), tid: nu() });
      if (!vardTillaten(m.hostname, policy) || (tillatna.size && !tillatna.has(m.origin))) { blockera(req, 'omdirigering till ' + redigeraUrl(mal) + ' utanför tillåtna ursprung'); return route.abort('blockedbyclient'); }
      const skrivandeVidare = [307, 308].includes(svar.status()) && !LAS.has(req.method());
      if (!skrivandeVidare) return route.fulfill({ status: svar.status(), headers: { location: mal, 'cache-control': 'no-store' }, body: '' });  // webbläsaren följer med GET genom proxyn
      if (!skrivbaraSet.has(m.origin)) { blockera(req, 'skrivande omdirigering till ' + redigeraUrl(mal)); return route.abort('blockedbyclient'); }
      if (++hopp > 10) { blockera(req, 'för många omdirigeringar'); return route.abort('blockedbyclient'); }
      const h2 = {}; if (undantag && m.origin === malUrsprung) h2['x-vercel-protection-bypass'] = undantag;
      try { svar = await route.fetch({ url: mal, headers: h2, maxRedirects: 0 }); } catch (e) { return route.abort('failed'); }
      aktuell = mal;
    }
    return fullborda(route, svar);
  });
}

/** Läsande vakt för skript som skapar sina kontexter själva (axe, stil, sida, ikoner): samma regler som oppna, utan
 *  skrivbara ursprung och utan skyddsundantag; skapa kontexten med serviceWorkers: 'block'. Ger loggen. */
export async function lasvakt(ctx, tillat = []) {
  const logg = { natverk: [], blockerade: [], omdirigeringar: [] };
  await installeraVakt(ctx, { policy: natpolicy(), tillatna: new Set(tillat.filter(Boolean).map((o) => origin(o))), skrivbaraSet: new Set(), undantag: null, malUrsprung: null, logg });
  return logg;
}
// Svaret lämnas till webbläsaren med kroppen redan avkodad: kodnings- och längdhuvuden tas bort.
async function fullborda(route, svar) {
  const headers = {};
  for (const [k, v] of Object.entries(svar.headers())) if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(k.toLowerCase())) headers[k] = v;
  return route.fulfill({ status: svar.status(), headers, body: await svar.body() });
}

/** Sandlådat bygge (kor.sh NWP_SANDLADA=pa): Chromium kan inte starta inne i Claude Codes sandlåda (mach-register nekas),
 *  så skriptet körs av kontroller/webbtjanst.py utanför sandlådan, bundet till sluggen, domänlistan och byggets kataloger.
 *  Delegerar bara när tjänsten är anvisad, sandlådans proxy är satt och vi inte redan är inne i tjänsten; skriver
 *  verktygets utskrift och avslutar med dess slutkod. Node:s fetch går aldrig via proxyvariablerna. */
export async function viaTjanst(verktyg, argv) {
  const bas = (process.env.NWP_WEBBTJANST || '').replace(/\/$/, '');
  if (!bas || process.env.NWP_I_TJANSTEN || !(process.env.HTTP_PROXY || process.env.HTTPS_PROXY)) return;
  let svar;
  try {
    const r = await fetch(bas + '/kor', { method: 'POST', headers: { 'content-type': 'application/json', 'x-nyckel': process.env.NWP_WEBBTJANST_NYCKEL || '' },
                                         body: JSON.stringify({ verktyg, args: argv }) });
    const text = await r.text();
    if (!r.ok) { console.error('webbtjänsten nekade (' + r.status + '): ' + text.slice(0, 300)); process.exit(2); }
    svar = JSON.parse(text);
  } catch (e) { console.error('webbtjänsten nås inte (' + bas + '): ' + e.message); process.exit(2); }
  process.stdout.write(svar.ut || '');
  process.exit(Number.isInteger(svar.rc) ? svar.rc : 1);
}

/** Startar webbläsare + kontext för en vy med värdverkställd ursprungsgräns (route-nivå: allt utanför tillåtna ursprung
 *  avbryts och loggas som blockerat), skyddsundantag som header bara mot målets ursprung (`mal`; tillåtna tredje parter
 *  får det aldrig), logg och spår. */
// utan-js.mjs använder extra: { javaScriptEnabled: false } i samma avgränsade browserkontext.
// lasande (standard): bara GET, HEAD och OPTIONS släpps igenom; ett skrivande anrop (POST, PUT, DELETE …) från sidans
// skript avbryts och loggas. Extern inspektion klickar på främmande sajter och får aldrig skicka något (omgång elva,
// F36). skrivbara: ursprung som får skriva ändå, till exempel provets egen lokala demomottagare.
export async function oppna({ vy = '1440', tillat = [], undantag = null, hemliga = [], spar = null, extra = {}, mal = null, lasande = true, skrivbara = [] }) {
  const malUrsprung = mal ? origin(mal) : (tillat.length ? origin(tillat[0]) : null);
  const v = VYER[vy]; if (!v) throw new Error('okänd vy: ' + vy + ' (390, 768, 1440, 320)');
  const red = redigerare([undantag, ...hemliga].filter(Boolean));
  const logg = { konsol: [], natverk: [], blockerade: [], dialoger: [], sidfel: [], omdirigeringar: [] };
  const policy = natpolicy();
  const tillatna = new Set(tillat.map(o => origin(o)));
  const proxy = await startaProxy(anslutningsvakt(policy, tillatna), (metod, url, skal) => logg.blockerade.push({ metod, url: redigeraUrl(url), typ: 'proxy', tid: nu(), skal: (skal || 'utanför tillåtna ursprung') + ' (nätgränsen)' }));
  const browser = await chromium.launch({ headless: true, proxy: { server: proxy.server } });
  // serviceWorkers: 'block': en service worker skulle annars kunna göra anrop förbi route-vakten
  const ctx = await browser.newContext({ viewport: v.viewport, deviceScaleFactor: v.deviceScaleFactor, isMobile: v.isMobile, hasTouch: v.hasTouch, locale: 'sv-SE', timezoneId: 'Europe/Stockholm', serviceWorkers: 'block', ...extra });
  // skrivande anrop (POST …) bara till lokala ursprung: provets egen demomottagare; aldrig till andras sajter (F36)
  const skrivbaraSet = new Set(skrivbara.map(o => origin(o)).filter((o) => arLokal(o)));
  await installeraVakt(ctx, { policy, tillatna, skrivbaraSet, undantag, malUrsprung, logg });
  ctx.on('page', p => {
    p.on('console', m => logg.konsol.push({ typ: m.type(), text: red(m.text()).slice(0, 500), tid: nu() }));
    p.on('pageerror', e => logg.sidfel.push({ text: red(e.message).slice(0, 500), tid: nu() }));
    p.on('dialog', async d => { logg.dialoger.push({ typ: d.type(), text: red(d.message()).slice(0, 200) }); await d.dismiss().catch(() => {}); });
    // id: hash av den omaskerade adressen utan fragment, så att ett anrop kan knytas till ett mål utan att hemliga parametrar
    // hamnar i rapporten; maskningen gör annars /api?key=a och /api?key=b identiska (omgång femton, F36)
    p.on('response', r => logg.natverk.push({ metod: r.request().method(), url: redigeraUrl(r.url()), id: sha256(String(r.url()).split('#')[0]), status: r.status(), typ: r.request().resourceType() }));
    p.on('requestfailed', r => logg.natverk.push({ metod: r.method(), url: redigeraUrl(r.url()), id: sha256(String(r.url()).split('#')[0]), status: null, fel: r.failure()?.errorText, typ: r.resourceType() }));
  });
  if (spar) await ctx.tracing.start({ screenshots: true, snapshots: true, sources: false });
  const page = await ctx.newPage();
  return { browser, ctx, page, logg, vy: v, red, stang: async (sparFil) => {
    try {
      if (spar && sparFil) await ctx.tracing.stop({ path: sparFil });
      else if (spar) await ctx.tracing.stop();
      await ctx.close(); // Flush context-owned HAR recordings before closing the browser.
    } finally { await browser.close(); await proxy.stang(); }
  } };
}

export async function horisontellSpill(page) {
  return page.evaluate(() => ({ spill: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1, scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth }));
}

/** Tangentbordsväg: Tab genom de första N fokuserbara elementen; registrerar element, synlig fokusmarkering och ordning. */
export async function tangentbord(page, n = 25) {
  const steg = [];
  for (let i = 0; i < n; i++) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate(() => {
      const el = document.activeElement; if (!el || el === document.body) return null;
      const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
      const synlig = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none';
      return { tagg: el.tagName.toLowerCase(), text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('alt') || el.value || '').trim().slice(0, 60), synligFokus: synlig, iVy: r.bottom > 0 && r.top < innerHeight, storlek: [Math.round(r.width), Math.round(r.height)] };
    });
    if (!info) break;
    if (steg.length && steg[steg.length - 1].tagg === info.tagg && steg[steg.length - 1].text === info.text) break;
    steg.push(info);
  }
  return steg;
}

export function skriv(dir, namn, data) {
  mkdirSync(dir, { recursive: true });
  const p = join(dir, namn);
  writeFileSync(p, typeof data === 'string' ? data : JSON.stringify(data, null, 1) + '\n');
  return p;
}
