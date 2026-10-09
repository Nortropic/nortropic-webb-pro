// Gemensamt för Digitalas webbläsarväg (Playwright 1.63, pinnad i package.json): start, vyer, värdverkställd
// ursprungsgräns, logg med redigerade hemligheter, spår. Ingen modell här; modellen (utvecklare, QA eller avskärmad
// besökare) sitter i sessionen som anropar verktygen.
import { chromium, webkit, devices } from 'playwright';
import { createHash } from 'node:crypto';
import http from 'node:http';
import net from 'node:net';
import dns from 'node:dns';
import { readFileSync, statSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export const VYER = { '390': { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'mobil (emulerad, inte fysisk enhet)' },
                      '768': { viewport: { width: 768, height: 1024 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'surfplatta (emulerad)' },
                      // mellanbredden: en datorlayout med fasta mått kan spilla mellan brytpunkten och 1440 (ägaren 2026-10-06)
                      '1280': { viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1, isMobile: false, hasTouch: false, namn: 'dator, mellanbredd' },
                      '1440': { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, isMobile: false, hasTouch: false, namn: 'dator' },
                      '320': { viewport: { width: 320, height: 640 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, namn: 'reflow 320 px (WCAG 1.4.10)' } };
const HEMLIGA_NAMN = /^(authorization|cookie|set-cookie|x-vercel-protection-bypass|x-vercel-set-bypass-cookie|proxy-authorization|cf-access-client-id|cf-access-client-secret|cf-access-jwt-assertion)$/i;
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

/** Skyddsundantag: privat fil (rättighet 0600, utanför tmp). Cloudflare Access (förhandsvisningen på Workers): två rader
 *  `CF-Access-Client-Id: …` och `CF-Access-Client-Secret: …`, en servicetoken. En ensam rad om minst 16 tecken är en äldre
 *  Vercel-förbikoppling (historik, för de sajter som ligger kvar på Vercel). Ger {huvud: värde}; värdena skrivs aldrig ut
 *  och skickas bara till målets ursprung. */
export function lasUndantag(fil) {
  if (!fil) return null;
  const st = statSync(fil);
  if ((st.mode & 0o077) !== 0) throw new Error('undantagsfilen ska ha rättighet 0600');
  if (/^\/(tmp|etc|var\/folders)\//.test(fil) || fil.startsWith('/private/tmp')) throw new Error('undantagsfilen får inte ligga i tmp, etc eller var/folders');
  const rader = readFileSync(fil, 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
  const ut = {};
  for (const r of rader) { const m = r.match(/^(CF-Access-Client-Id|CF-Access-Client-Secret)\s*:\s*(\S{8,})$/i); if (m) ut[m[1].toLowerCase()] = m[2]; }
  if (Object.keys(ut).length) {
    if (!ut['cf-access-client-id'] || !ut['cf-access-client-secret']) throw new Error('undantagsfilen ska bära både CF-Access-Client-Id och CF-Access-Client-Secret');
    return ut;
  }
  const v = (rader[0] || '').trim();
  if (v.length < 16 || /\s/.test(v)) throw new Error('undantagsfilen ska bära Cloudflare Access-servicetokenens två rader (eller en äldre förbikoppling om minst 16 tecken)');
  return { 'x-vercel-protection-bypass': v };  // historik: äldre Vercel-förhandsvisningar
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
/** Metoden webbläsaren använder efter ett hopp (Fetch-standarden): 303 ger GET (HEAD består), 301/302 byter bara POST
 *  till GET, 307/308 behåller metoden. PUT, PATCH och DELETE förs alltså vidare också vid 301/302 (Codex R25). */
export function nastaMetod(status, metod) {
  const m = String(metod).toUpperCase();
  if (status === 303) return m === 'HEAD' ? 'HEAD' : 'GET';
  if ((status === 301 || status === 302) && m === 'POST') return 'GET';
  return m;
}

// Icke-globalt nåbara block enligt IANA:s register över specialadresser (IPv4 och IPv6); allt som inte går att tolka
// räknas som icke-globalt (Codex R25: 198.18.0.0/15 med flera saknades).
const V4_ICKE_GLOBALA = ['0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8', '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.0.2.0/24',
                         '192.88.99.0/24', '192.168.0.0/16', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24', '224.0.0.0/4', '240.0.0.0/4'];
const V6_ICKE_GLOBALA = ['::/128', '::1/128', '64:ff9b:1::/48', '100::/64', '2001::/32', '2001:2::/48', '2001:10::/28', '2001:20::/28', '2001:db8::/32',
                         '2002::/16', '3fff::/20', '5f00::/16', 'fc00::/7', 'fe80::/10', 'fec0::/10', 'ff00::/8'];
function v4Tal(ip) { const d = ip.split('.').map(Number); return (((d[0] << 24) >>> 0) + (d[1] << 16) + (d[2] << 8) + d[3]) >>> 0; }
function v6Tal(ip) {
  let s = ip.toLowerCase().replace(/%.*$/, '');
  const m = s.match(/^(.*:)(\d+\.\d+\.\d+\.\d+)$/);
  if (m) { if (!net.isIPv4(m[2])) return null; const v = v4Tal(m[2]); s = m[1] + (v >>> 16).toString(16) + ':' + (v & 0xffff).toString(16); }
  const delar = s.split('::'); if (delar.length > 2) return null;
  const a = delar[0] ? delar[0].split(':') : [], b = delar.length === 2 && delar[1] ? delar[1].split(':') : [];
  const n = 8 - a.length - b.length; if (n < 0 || (delar.length === 1 && n !== 0)) return null;
  const grupper = [...a, ...Array(delar.length === 2 ? n : 0).fill('0'), ...b]; if (grupper.length !== 8) return null;
  let t = 0n; for (const g of grupper) { if (!/^[0-9a-f]{1,4}$/.test(g)) return null; t = (t << 16n) + BigInt(parseInt(g, 16)); } return t;
}
function iBlock4(t, cidr) { const [p, len] = cidr.split('/'); const skift = 32 - Number(len); return skift >= 32 ? true : (t >>> skift) === (v4Tal(p) >>> skift); }
function iBlock6(t, cidr) { const [p, len] = cidr.split('/'); const skift = 128n - BigInt(len); return (t >> skift) === (v6Tal(p) >> skift); }
/** Adress som inte är globalt nåbar (loopback, privat, länklokal, CGNAT, dokumentation, benchmark, multicast, reserverat,
 *  IPv6-motsvarigheter, ::ffff:-mappade IPv4)? Okänt format räknas som icke-globalt. */
export function privatAdress(ip) {
  const v = String(ip).toLowerCase();
  if (net.isIPv4(v)) { const t = v4Tal(v); return V4_ICKE_GLOBALA.some((c) => iBlock4(t, c)); }
  if (net.isIPv6(v)) {
    const t = v6Tal(v); if (t === null) return true;
    if ((t >> 32n) === 0xffffn) return V4_ICKE_GLOBALA.some((c) => iBlock4(Number(t & 0xffffffffn), c));  // ::ffff:a.b.c.d
    return V6_ICKE_GLOBALA.some((c) => iBlock6(t, c));
  }
  return true;
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
  if (prov) {
    const ms = Number(process.env.NWP_PROV_UPPSLAG_FORDROJNING || 0); if (ms > 0) await new Promise((r) => setTimeout(r, ms));  // bara rökprovet: ett sent svar
    if (!prov.has(h)) return { fel: 'gick inte att slå upp (provuppslag)' }; adresser = [prov.get(h)];
  }
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
async function startaProxy(tillaten, blockera, skrivbar = () => false) {
  const socklar = new Set();  // alla socklar, också överlämnade CONNECT-tunnlar: server.close() väntar annars för evigt på dem (exit 13)
  const anrop = new Set();    // pågående utgående http-anrop: förstörs vid stängning (Codex R26, F28)
  let stangd = false;         // prövas efter varje väntat uppslag: inget nytt utgående efter stang()
  const folj = (c) => { socklar.add(c); c.on('close', () => socklar.delete(c)); return c; };
  const srv = http.createServer(async (req, res) => {
    let u; try { u = new URL(req.url); } catch { res.writeHead(400); return res.end(); }
    const port = u.port || '80';
    const neka = (kod, skal) => { blockera(req.method, u.toString(), skal); try { res.writeHead(kod, { 'content-type': 'text/plain' }); res.end('blockerad'); } catch {} };
    if (!tillaten(u.hostname, port, 'http:')) return neka(403, 'utanför tillåtna ursprung');
    if (!LAS.has(req.method) && !skrivbar(u.hostname, port, 'http:')) return neka(405, 'skrivande anrop till ett ursprung som inte är skrivbart');
    const upp = await uppslag(u.hostname);
    if (stangd) return neka(503, 'proxyn stängd');
    if (!upp.ip) return neka(403, upp.fel);
    const p = http.request({ host: upp.ip, port: Number(port), method: req.method, path: u.pathname + u.search, headers: { ...req.headers, host: u.host } }, (r) => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
    anrop.add(p); p.on('close', () => anrop.delete(p));
    p.on('error', () => { try { res.writeHead(502); res.end(); } catch {} });
    req.pipe(p);
  });
  srv.on('connect', async (req, sock, head) => {
    const i = req.url.lastIndexOf(':'); const host = (i > 0 ? req.url.slice(0, i) : req.url).replace(/^\[|\]$/g, ''); const port = i > 0 ? req.url.slice(i + 1) : '443';
    const neka = (skal) => { blockera('CONNECT', 'https://' + req.url + '/', skal); try { sock.write('HTTP/1.1 403 Forbidden\r\n\r\n'); } catch {} sock.destroy(); };
    if (!tillaten(host, port, 'https:')) return neka('utanför tillåtna ursprung');
    const upp = await uppslag(host);
    if (stangd) return neka('proxyn stängd');
    if (!upp.ip) return neka(upp.fel);
    const s = folj(net.connect(Number(port) || 443, upp.ip, () => { sock.write('HTTP/1.1 200 Connection Established\r\n\r\n'); if (head && head.length) s.write(head); s.pipe(sock); sock.pipe(s); }));
    folj(sock);
    s.on('error', () => sock.destroy()); sock.on('error', () => s.destroy());
  });
  srv.on('connection', folj);
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  const stang = () => new Promise((r) => {
    let klar = false; const slut = () => { if (!klar) { klar = true; clearTimeout(t); r(); } };
    const t = setTimeout(slut, 2000);  // stängningen ska alltid bli klar: skriptets top-level await får aldrig lämnas hängande
    stangd = true;
    for (const p of anrop) p.destroy();
    for (const c of socklar) c.destroy();
    if (srv.closeAllConnections) srv.closeAllConnections();
    srv.close(slut);
  });
  return { server: 'http://127.0.0.1:' + srv.address().port, stang };
}

// värd:port mot en mängd ursprung: lokala värdnamn jämförs på port (localhost och 127.0.0.1 är samma mottagare)
function ursprungsvakt(tillatna, alltLokaltUtanLista) {
  const lokalaPortar = new Set([...tillatna].filter((o) => arLokal(o)).map((o) => { const u = new URL(o); return u.port || (u.protocol === 'https:' ? '443' : '80'); }));
  return (host, port, protokoll) => {
    const h = String(host).toLowerCase();
    if (LOKALA.has(h)) return (alltLokaltUtanLista && !tillatna.size) || lokalaPortar.has(String(port));
    if (!tillatna.size) return alltLokaltUtanLista;
    const std = protokoll === 'https:' ? '443' : '80';
    return tillatna.has(protokoll + '//' + h + (String(port) === std ? '' : ':' + port));
  };
}

// värd:port tillåten för proxyn: domänpolicyn och, när skriptet angett ursprung, just de ursprungen (också lokala portar:
// webbläsaren tvingas genom proxyn för loopback, så en sida kan inte nå andra lokala tjänster; Codex R25)
function anslutningsvakt(policy, tillatna) {
  const inom = ursprungsvakt(tillatna, true);
  return (host, port, protokoll) => {
    const h = String(host).toLowerCase();
    if (!LOKALA.has(h) && !vardTillaten(h, policy)) return false;
    return inom(host, port, protokoll);
  };
}

/** Nätgränsen för skript som startar Chromium själva (axe, stil, sida, ikoner, lighthouse): i tjänstens läge
 *  (NWP_NAT_TILLATNA satt, kontroller/webbtjanst.py) en filtrerande proxy enligt domänpolicyn och de givna ursprungen,
 *  som Chromium startas genom (playwright-alternativ eller Chrome-flagga); annars null och allt som förut. */
export async function natgrans(ursprung = [], skrivbara = []) {
  const policy = natpolicy();
  if (policy === null) return null;
  const tillatna = new Set(ursprung.filter(Boolean).map((o) => origin(o)));
  const skrivbaraSet = new Set(skrivbara.filter(Boolean).map((o) => origin(o)).filter((o) => arLokal(o)));
  const blockerade = [];
  const proxy = await startaProxy(anslutningsvakt(policy, tillatna), (metod, url, skal) => blockerade.push({ metod, url: redigeraUrl(url), tid: nu(), skal }), ursprungsvakt(skrivbaraSet, false));
  const server = proxy.server.replace(/^http:\/\//, '');
  // <-loopback>: också localhost går genom proxyn, annars kringgår webbläsaren den för lokala adresser
  return { server: proxy.server, playwright: { proxy: { server: proxy.server, bypass: '<-loopback>' } }, chromeFlags: ['--proxy-server=' + server, '--proxy-bypass-list=<-loopback>'], blockerade, stang: proxy.stang };
}

// Huvuden som följer kroppen vid ett metodbevarande hopp (307/308): innehållstypen och det allmänna, som webbläsaren
// själv skulle skicka; ursprungsbundna huvuden (cookie, authorization, skyddsundantaget, origin, referer) bara när hoppet
// stannar i samma ursprung; host och content-length sätts om av hämtningen (Codex R26, F31/F36).
const URSPRUNGSBUNDNA = new Set(['cookie', 'authorization', 'proxy-authorization', 'x-vercel-protection-bypass', 'cf-access-client-id', 'cf-access-client-secret', 'origin', 'referer']);
const BORT_VID_HOPP = new Set(['host', 'content-length', 'connection', 'keep-alive', 'transfer-encoding', 'upgrade', 'te']);
export function hopphuvuden(huvuden, sammaUrsprung) {
  const ut = {};
  for (const [k, v] of Object.entries(huvuden || {})) {
    const n = k.toLowerCase();
    if (BORT_VID_HOPP.has(n) || n.startsWith(':')) continue;
    if (URSPRUNGSBUNDNA.has(n) && !sammaUrsprung) continue;
    ut[n] = v;
  }
  return ut;
}

/** Route-vakten: samma regler i oppna och i skript som skapar sina kontexter själva (lasvakt). Värd mot policyn,
 *  ursprung mot skriptets lista, skrivande anrop bara till skrivbara (lokala) ursprung, WebSockets blockerade, varje
 *  omdirigeringshopp prövat; ett skrivande anrop som förs vidare med 307/308 följs här, hopp för hopp, bara till
 *  skrivbara ursprung (Codex R24: lokal POST → 307 lokalt → 307 extern domän stoppas). */
async function installeraVakt(ctx, { policy, tillatna, skrivbaraSet, undantag, malUrsprung, logg }) {
  // WebKit låter inte route.fulfill svara med en omdirigering (3xx): där blir ett prövat läsande hopp i en navigering en
  // sida som går vidare med meta refresh, och ett hopp i ett skript-anrop följs här; nästa anrop prövas av samma vakt
  const webkitMotor = ctx.browser()?.browserType().name() === 'webkit';
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
    if (undantag && o === malUrsprung) Object.assign(headers, undantag);  // bara målets ursprung, aldrig tredje part
    let svar;
    try { svar = await route.fetch({ headers, maxRedirects: 0 }); }
    catch (e) { logg.natverk.push({ metod: req.method(), url: redigeraUrl(u), id: sha256(String(u).split('#')[0]), status: null, fel: String(e.message).slice(0, 200), tid: nu() }); return route.abort('failed'); }
    let aktuell = u, hopp = 0, metodNu = req.method();
    while (arOmdirigering(svar)) {
      let mal, m; try { mal = new URL(svar.headers()['location'], aktuell).toString(); m = new URL(mal); } catch { blockera(req, 'ogiltig omdirigering'); return route.abort('blockedbyclient'); }
      logg.omdirigeringar.push({ metod: req.method(), fran: redigeraUrl(aktuell), till: redigeraUrl(mal), status: svar.status(), tid: nu() });
      if (!vardTillaten(m.hostname, policy) || (tillatna.size && !tillatna.has(m.origin))) { blockera(req, 'omdirigering till ' + redigeraUrl(mal) + ' utanför tillåtna ursprung'); return route.abort('blockedbyclient'); }
      const nasta = nastaMetod(svar.status(), metodNu);
      if (LAS.has(nasta) && !webkitMotor) return route.fulfill({ status: svar.status(), headers: { location: mal, 'cache-control': 'no-store' }, body: '' });  // webbläsaren följer läsande genom proxyn
      if (LAS.has(nasta) && req.isNavigationRequest()) {
        // märkt, så att efterOmdirigering() kan vänta förbi den: goto och load löser annars ut på mellansidan
        const html = '<!doctype html><meta charset="utf-8"><meta name="nwp-omdirigering" content="1"><meta http-equiv="refresh" content="0;url=' + mal.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;') + '">';
        return route.fulfill({ status: 200, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' }, body: html });
      }
      if (LAS.has(nasta)) {  // WebKit, skript-anrop: läsande hopp följs här, varje hopp prövat som ovan
        if (++hopp > 10) { blockera(req, 'för många omdirigeringar'); return route.abort('blockedbyclient'); }
        const h3 = hopphuvuden(req.headers(), m.origin === o); if (undantag && m.origin === malUrsprung) Object.assign(h3, undantag);
        // byter hoppet metod (303, eller POST vid 301/302) följer kroppen inte med (Fetch-standarden), inte heller dess huvuden
        const byter = nasta !== metodNu;
        if (byter) for (const n of Object.keys(h3)) if (/^content-(type|length|encoding|language)$/i.test(n)) delete h3[n];
        // route.fetch skulle återanvända originalets kropp; kontextens egen förfrågan gör ett rent anrop med samma vägar
        try { svar = byter ? await ctx.request.fetch(mal, { method: nasta, headers: h3, maxRedirects: 0 }) : await route.fetch({ url: mal, method: nasta, headers: h3, maxRedirects: 0 }); } catch (e) { return route.abort('failed'); }
        aktuell = mal; metodNu = nasta; continue;
      }
      // ett skrivande anrop som förs vidare (POST vid 307/308, PUT/PATCH/DELETE också vid 301/302): varje hopp måste gå till ett skrivbart ursprung och följs här
      if (!skrivbaraSet.has(m.origin)) { blockera(req, 'skrivande omdirigering (' + nasta + ') till ' + redigeraUrl(mal)); return route.abort('blockedbyclient'); }
      if (++hopp > 10) { blockera(req, 'för många omdirigeringar'); return route.abort('blockedbyclient'); }
      const h2 = hopphuvuden(req.headers(), m.origin === o); if (undantag && m.origin === malUrsprung) Object.assign(h2, undantag);
      try { svar = await route.fetch({ url: mal, method: nasta, headers: h2, maxRedirects: 0 }); } catch (e) { return route.abort('failed'); }
      aktuell = mal; metodNu = nasta;
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

/** Samma delegeringsvillkor som webbtjanst.delegeras: sandlådans proxy satt eller stoppkrokens processgräns
 *  (kontroller/processgrans.py, NWP_PROCESSGRANS=1), och inte redan inne i tjänsten (Codex R26, F1/F28). */
export function delegeras() {
  return Boolean(process.env.NWP_WEBBTJANST) && !process.env.NWP_I_TJANSTEN
    && Boolean(process.env.HTTP_PROXY || process.env.HTTPS_PROXY || process.env.NWP_PROCESSGRANS === '1');
}

/** Sandlådat bygge (kor.sh NWP_SANDLADA=pa): Chromium kan inte starta inne i Claude Codes sandlåda (mach-register nekas)
 *  eller stoppkrokens processgräns (nät bara till localhost), så skriptet körs av kontroller/webbtjanst.py utanför dem,
 *  bundet till sluggen, domänlistan och byggets kataloger. Delegerar bara när tjänsten är anvisad, sandlådans proxy
 *  eller processgränsens markör är satt och vi inte redan är inne i tjänsten; skriver verktygets utskrift och avslutar
 *  med dess slutkod. Node:s fetch går aldrig via proxyvariablerna. */
export async function viaTjanst(verktyg, argv) {
  const bas = (process.env.NWP_WEBBTJANST || '').replace(/\/$/, '');
  if (!bas || process.env.NWP_I_TJANSTEN || !delegeras()) return;
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
/** Vyn i WebKit: 390 px blir Playwrights iPhone 14-profil (390 × 664, iPhone-webbläsarsträng, pekskärm), övriga vyer
 *  samma mått som i Chromium. Belägg för layout och JavaScript i Safaris motor, inte för en riktig iPhone. */
export function webkitVy(vy) {
  const v = VYER[vy]; if (!v) return null;
  if (vy !== '390') return { ...v, namn: v.namn + ', WebKit' };
  const d = devices['iPhone 14'];
  return { viewport: d.viewport, deviceScaleFactor: d.deviceScaleFactor, isMobile: true, hasTouch: true, userAgent: d.userAgent,
           namn: 'iPhone 14-profil i WebKit (emulerad, inte fysisk enhet)' };
}

export async function oppna({ vy = '1440', tillat = [], undantag = null, hemliga = [], spar = null, extra = {}, mal = null, lasande = true, skrivbara = [], motor = 'chromium' }) {
  const malUrsprung = mal ? origin(mal) : (tillat.length ? origin(tillat[0]) : null);
  if (!['chromium', 'webkit'].includes(motor)) throw new Error('okänd motor: ' + motor + ' (chromium, webkit)');
  const v = motor === 'webkit' ? webkitVy(vy) : VYER[vy]; if (!v) throw new Error('okänd vy: ' + vy + ' (' + Object.keys(VYER).join(', ') + ')');
  const red = redigerare([...Object.values(undantag || {}), ...hemliga].filter(Boolean));
  const logg = { konsol: [], natverk: [], blockerade: [], dialoger: [], sidfel: [], omdirigeringar: [] };
  const policy = natpolicy();
  const tillatna = new Set(tillat.map(o => origin(o)));
  const skrivbaraSet = new Set(skrivbara.map(o => origin(o)).filter((o) => arLokal(o)));  // skrivande anrop bara till provets lokala mottagare (F36)
  const proxy = await startaProxy(anslutningsvakt(policy, tillatna), (metod, url, skal) => logg.blockerade.push({ metod, url: redigeraUrl(url), typ: 'proxy', tid: nu(), skal: (skal || 'utanför tillåtna ursprung') + ' (nätgränsen)' }), ursprungsvakt(skrivbaraSet, false));
  // <-loopback> är Chromiums sätt att tvinga också localhost genom proxyn; i WebKit vaktar route-vakten nedan varje anrop
  const browser = motor === 'webkit' ? await webkit.launch({ headless: true, proxy: { server: proxy.server } })
    : await chromium.launch({ headless: true, proxy: { server: proxy.server, bypass: '<-loopback>' } });
  // serviceWorkers: 'block': en service worker skulle annars kunna göra anrop förbi route-vakten
  const ctx = await browser.newContext({ viewport: v.viewport, deviceScaleFactor: v.deviceScaleFactor, isMobile: v.isMobile, hasTouch: v.hasTouch, ...(v.userAgent ? { userAgent: v.userAgent } : {}), locale: 'sv-SE', timezoneId: 'Europe/Stockholm', serviceWorkers: 'block', ...extra });
  await installeraVakt(ctx, { policy, tillatna, skrivbaraSet, undantag, malUrsprung, logg });
  ctx.on('page', p => {
    // sidans adress följer med, så att ett fel från en länkad sida (inspektionens bakåt/framåt) inte läggs på den inspekterade
    p.on('console', m => logg.konsol.push({ typ: m.type(), text: red(m.text()).slice(0, 500), tid: nu(), url: redigeraUrl(p.url()) }));
    p.on('pageerror', e => logg.sidfel.push({ text: red(e.message).slice(0, 500), tid: nu(), url: redigeraUrl(p.url()) }));
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

/** Väntar förbi vaktens omdirigeringssida (WebKit, där route.fulfill inte kan svara med 3xx): så länge sidan är den
 *  märkta mellansidan har navigeringen inte landat, och goto/load har löst ut för tidigt. Högst ms millisekunder. */
export async function efterOmdirigering(page, ms = 5000) {
  const slut = Date.now() + ms;
  while (Date.now() < slut) {
    const mellan = await page.evaluate(() => !!document.querySelector('meta[name="nwp-omdirigering"]')).catch(() => true);
    if (!mellan) { await page.waitForLoadState('load', { timeout: Math.max(1000, slut - Date.now()) }).catch(() => {}); return; }
    await page.waitForTimeout(100);
  }
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
