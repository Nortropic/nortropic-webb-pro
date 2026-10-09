// Arbetsytans UI-prov (dashboard/arbetsyta.js och arbetsyta.css, ägarens uppdrag 2026-10-09; kunskap/arbetsyta.md) med
// riktiga klick och syntetiska HTTP-svar: en node:http-server med index.html, dashboardens separata skript och ett påhittat
// läge i samma form som arbetsyta.lage() och partner.lage(). Strömmen styrs av provet: nya lägen, ett tappat svar och
// nekade återanslutningar. Läsvägen och skrivvägarna på den riktiga servern prövas separat; ingen claude-process startas
// och inget anrop lämnar provets egen server.
//   node prov_arbetsyta_webb.mjs <repo>      (NWP_UI_BEVISET=<katalog> sparar vyernas skärmbilder vid 1440 och 390)
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import assert from 'node:assert/strict';

const root = resolve(process.argv[2] || '.');
const { chromium } = await import(resolve(root, 'kontroller/node_modules/playwright/index.mjs'));
const sov = (ms) => new Promise((r) => setTimeout(r, ms));

// --- dashboardens filer, som server.py serverar dem ---
const TYP = { js: 'text/javascript; charset=utf-8', css: 'text/css; charset=utf-8', html: 'text/html; charset=utf-8' };
const filer = new Map(await Promise.all([['/', 'index.html'], ...['kundstart-agare.js', 'kundstart-agare.css', 'kirurg-forbattring.js', 'arbetsyta.js', 'arbetsyta.css']
  .map((n) => ['/' + n, n])].map(async ([vag, n]) => [vag, { data: await readFile(resolve(root, 'dashboard', n)), typ: TYP[n.split('.').pop()] }])));
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=', 'base64');

// --- det syntetiska läget (formen ur dashboard/arbetsyta.py lage() och partner.py lage()) ---
const SLUG = 'prov-kund', NAMN = 'Bageriet Provhörnan', NYCKEL = 'provnyckel1234';
const LAGEN = { vantar: 'väntar på start', startar: 'start pågår', aktiv: 'arbetar', verktyg: 'väntar på verktyg', beslut: 'väntar på ditt beslut',
  avslutad: 'avslutad', avbruten: 'avbruten', okant: 'okänt läge' };
const STEGNAMN = ['Kundunderlaget', 'Prototypen', 'Ditt val', 'Förfiningen', 'Godkännandet', 'Helbygget', 'Din dom över bygget', 'Exporten till kundrepo', 'Leveransen'];
const BAS = Date.now() - 45 * 60000;
const T = (min) => new Date(BAS + min * 60000).toISOString().replace(/\.\d{3}Z$/, 'Z');
const V1 = 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678', V1K = V1.slice(0, 12);
const V2 = '9f8e7d6c5b4a3210fedcba9876543210abcdef01', V2K = V2.slice(0, 12);  // k01:s nästa version (en förbättringsrunda)
const START1 = '11111111-2222-4333-8444-555555555555', START2 = '66666666-7777-4888-9999-000000000000';
const PARTNER_SID = '9d0c3a52-7f41-4c1e-b8a6-2f5e0d4c7b19';
const KONF = { arbetsledning: 'claude-fable-5-1, effort medium (partnersamtalet)', utforande: 'opus (ateljéns arbetare)', granskning: 'sonnet (granskarna)' };
const handelse = (min, verktyg, utfall = 'ok', extra = {}) => ({ tid: T(min), verktyg, utfall, klar_tid: utfall === 'pågår' ? null : T(min), ...extra });
function korning(lage, startId, startad, steg, lever) {
  return { id: startad, startad, lage, steg, fas: null, start_id: startId, start_handling: lage, pid: 40411, arbetaren: lever ? 'lever' : 'lever inte',
    avslutad: !lever, avbruten: false, fel: null, vantar_pa_agaren: !lever && steg === 'klar_for_bedomning', klar: lever ? null : T(30) };
}
function ateljesession(id, roll, ansvar, kandidat, start, lage, lageText, handelser, pagaende = []) {
  return { session_id: id, roll, ansvar, kandidat, korning: S.korning.id, start, slut: null, utfall: null, pid: 40500 + S.sessioner.length, lage, lage_text: lageText,
    foralder: { typ: 'ateljéns arbetare', pid: S.korning.pid, start_id: S.korning.start_id }, modell_konfigurerad: ansvar === 'granskning' ? 'sonnet' : 'opus',
    modell_observerad: ansvar === 'granskning' ? 'claude-sonnet-5' : 'claude-opus-5-5', senaste_handelse: (handelser.at(-1) || {}).tid || null,
    kontext: { tokens: 48200 }, komprimeringar: 0, nekade: 0, lasfel: null, ofullstandig: null, kalla: 'ateljén',
    aktivitet: { handelser, antal: handelser.length, pagaende, senaste_handelse: (handelser.at(-1) || {}).tid || null } };
}
function avsluta(s, min) { Object.assign(s, { lage: 'avslutad', lage_text: 'avslutad ' + T(min), slut: T(min), utfall: 'avslutad, kod 0', aktivitet: { ...s.aktivitet, pagaende: [] } }); }
const S = { blind: true, sessioner: [], partner: [], handlingar: [], startjournal: [], k01: 'skapad', k01v: V1 };
S.korning = korning('ny', START1, T(0), 'divergera', true);
S.stegstatus = ['skapat', 'pågår', ...Array(7).fill('inte påbörjat')];
S.handlingar = [{ id: 'stoppa', text: 'Stoppa arbetet' }];
S.startjournal = [{ start_id: START1, handling: 'ny', tid: T(0), status: 'startad', slutkod: null, stopp_begart: false, stopp_sent: false, fel: null, process_lever: true }];
S.sessioner.push(ateljesession('5b1e0a77-1c2d-4e3f-8a9b-0c1d2e3f4a5b', 'skapa-k01', 'utforande', 'k01', T(2), 'aktiv', 'processen lever',
  [handelse(3, 'Skill', 'ok', { skill: 'bygg-sajt' }), handelse(5, 'Read'), handelse(9, 'Write')]));
S.sessioner.push(ateljesession('6c2f1b88-2d3e-4f40-9bac-1d2e3f4a5b6c', 'skapa-k02', 'utforande', 'k02', T(2), 'verktyg', 'väntar på Bash',
  [handelse(4, 'Read'), handelse(10, 'Bash', 'pågår')], ['Bash']));
S.partner.push({ id: 'b7c1d2e3-f4a5-4b6c-8d7e-9f0a1b2c3d4e', tid: T(1), avsikt: 'fraga', kontext: { kandidat: 'k01', version: V1K, vy: 'Arbetsyta' },
  text: 'Hur långt har förslagen kommit?', lage: 'svarat', fel: null, overlamning: null, slut: T(2),
  svar: { text: 'Båda förslagen byggs. **Förslag A** har en första version; Förslag B väntar på ett verktyg.', fel: false, subtyp: 'success', session_id: PARTNER_SID,
    turer: 1, ms: 8400, anvandning: { in: 1520, ut: 214, cache_las: 8000, cache_skriv: 1200, listpris_usd: 0.1234, modeller: ['claude-fable-5-1'] }, nekade: [] } });

function kandidater() {
  return [
    { id: 'k01', etikett: 'Förslag A', status: S.k01, statustext: S.k01 === 'skapad' ? 'byggd, väntar på ditt val' : S.k01, version: S.k01v.slice(0, 12), version_hel: S.k01v, fotograferad: S.k01v,
      preview: { url: `/visa/${SLUG}/k01`, finns: true, byggd: T(20) },
      snapshot: { 390: `kunder/${SLUG}/kandidater/k01/bilder/390-forsta.png`, 1440: `kunder/${SLUG}/kandidater/k01/bilder/1440-forsta.png`, version: S.k01v.slice(0, 12), tid: T(21) },
      versioner: S.k01v === V1 ? [V1K] : [V1K, S.k01v.slice(0, 12)] },
    { id: 'k02', etikett: 'Förslag B', status: 'skapas', statustext: 'skapas', version: null, version_hel: null, fotograferad: null,
      preview: { url: `/visa/${SLUG}/k02`, finns: false, byggd: null }, snapshot: { 390: null, 1440: null, version: null, tid: null }, versioner: [] },
  ];
}
function preview(kand) {  // som arbetsyta.preview(): arbetsversion, bevarad ögonblicksbild, märkta för sig
  const ut = [];
  for (const k of kand) {
    if (k.preview.finns) ut.push({ typ: 'arbetsversion', kalla: 'kandidat', kandidat: k.id, url: k.preview.url, byggd: k.preview.byggd, etikett: `${k.etikett}, arbetsversion byggd ${k.preview.byggd}` });
    if (k.snapshot['390'] || k.snapshot['1440']) ut.push({ typ: 'snapshot', kalla: 'kandidat', kandidat: k.id, bilder: { 390: k.snapshot['390'], 1440: k.snapshot['1440'] },
      version: k.snapshot.version, tid: k.snapshot.tid, aldre: !k.preview.finns, etikett: `${k.etikett}, bevarad version ${k.snapshot.version} (skärmbild ${k.snapshot.tid})` });
  }
  return ut;
}
function partnerLage(samtal) {
  const med = S.partner, senaste = med.at(-1);
  const sl = senaste?.lage === 'arbetar' ? 'aktiv' : senaste?.lage === 'svarat' ? 'avslutad' : 'vantar';  // som partner.lage(): en svarad tur är avslutad
  const text = { aktiv: 'partnern svarar', avslutad: 'partnern har svarat; nästa tur startar när du skriver', vantar: 'inget meddelande än' }[sl];
  const session = { session_id: PARTNER_SID, roll: 'partner', ansvar: 'arbetsledning', kandidat: null, korning: null, start: T(1), slut: senaste?.slut || null, pid: null,
    lage: sl, lage_text: text, foralder: { typ: 'dashboarden (en process per tur, samma sessions-id)', pid: null, start_id: null },
    modell_konfigurerad: 'claude-fable-5-1', modell_observerad: 'claude-fable-5-1', aktivitet: null, senaste_handelse: null, kalla: 'partnersamtalet' };
  const ut = { session_id: PARTNER_SID, skapad: T(1), modell: 'claude-fable-5-1', effort: 'medium', profil: { modell: 'claude-fable-5-1', effort: 'medium', frist: 600, max_turer: 12 },
    lage: sl, lage_text: text, session, antal: med.length, senaste: { id: senaste?.id ?? null, lage: senaste?.lage ?? null, tid: senaste?.tid ?? null },
    andra_processer: [], terminal: 'claude --resume ' + PARTNER_SID, arbetskatalog: `/syntetisk/underlag/${SLUG}/partner-rum` };
  if (samtal) ut.meddelanden = med;
  return ut;
}
function roller(sess, k, partnerlage) {  // som arbetsyta.roller()
  const ut = {};
  for (const [nyckel, rubrik] of [['arbetsledning', 'Arbetsledning'], ['utforande', 'Utförande'], ['granskning', 'Granskning']]) {
    const egna = sess.filter((s) => s.ansvar === nyckel), lev = egna.filter((s) => ['aktiv', 'verktyg', 'startar'].includes(s.lage));
    let lage, text;
    if (nyckel === 'arbetsledning') { lage = partnerlage || 'vantar'; text = 'partnersamtalet: ' + LAGEN[lage]; }
    else if (egna.length) { lage = (lev[0] || egna[0]).lage; text = `${egna.length} sessioner i körningen, ${lev.length} lever`; }
    else { lage = 'vantar'; text = `ingen session för ${rubrik.toLowerCase()} har startat i körningen${k.arbetaren === 'lever' ? ' än; körningen pågår' : ''}`; }
    if (nyckel === 'utforande' && k.vantar_pa_agaren && !['aktiv', 'verktyg', 'startar'].includes(lage)) { lage = 'beslut'; text += '; körningen väntar på ditt beslut'; }
    else if (nyckel === 'granskning' && k.vantar_pa_agaren && !['aktiv', 'verktyg', 'startar'].includes(lage)) text += '; körningen väntar på ditt beslut';
    ut[nyckel] = { rubrik, lage, lage_text: text, sessioner: egna.map((s) => s.session_id), konfigurerad: KONF[nyckel] };
  }
  return ut;
}
let versionsnr = 0;
function lage() {
  const kand = kandidater(), p = partnerLage(false), sess = [p.session, ...S.sessioner];
  const steg = STEGNAMN.map((namn, i) => ({ nr: i + 1, namn, status: S.stegstatus[i], underlag: [], kontroller: [], beslut: [], brister: [], nasta: '',
    utfall: i === 0 ? [{ text: 'VERKSAMHET.json, verksamhetens uppgifter (testdata)', lank: `/fil/underlag/${SLUG}/VERKSAMHET.json`, tid: T(-60) }] : [] }));
  const moment = steg.find((s) => ['pågår', 'väntar på ägaren'].includes(s.status)) || steg.filter((s) => !['inte påbörjat', 'inte observerat'].includes(s.status)).at(-1);
  return { schema: 'arbetsyta/1', tid: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'), slug: SLUG, ofullstandig: [],
    projekt: { slug: SLUG, namn: NAMN, testdata: true }, blind: S.blind, ab_dold: false, steg, startmiljo: null, handlingar: S.handlingar,
    besked: { version: 'syntetisk-version', tid: T(0), filer: [], tillstand: ['Sessionen avslutades normalt', 'Tekniska kontroller', 'Designgranskning', 'Ägarens godkännande',
      'Leverans inom angiven omfattning'].map((namn) => ({ namn, status: 'ej bedömt', varde: null, text: 'Syntetiskt besked för provet.' })) },
    moment: { nr: moment.nr, namn: moment.namn, status: moment.status }, korning: S.korning, kandidater: kand, helbygge: [], partner: p, sessioner: sess,
    startjournal: S.startjournal, roller: roller(sess, S.korning, p.lage), overlamningar: [], preview: preview(kand),
    observation: { senast_last: new Date().toISOString(), ofullstandig: [] }, version: String(++versionsnr).padStart(16, '0') };
}
// en sida i den form ett bygge har den: ett sextiotal rader och en lång rad, så att kodvyn behöver rulla åt båda hållen
const SIDA = ['---', "import Bas from '../layouts/Bas.astro';", "import Hero from '../components/Hero.astro';", "import Bild from '../components/Bild.astro';",
  "const oppettider = [['Tisdag–fredag', '07–17'], ['Lördag', '08–14'], ['Söndag', '09–13']];", '---',
  '<Bas titel="Bageriet Provhörnan" beskrivning="Surdegsbröd, kardemummabullar och kaffe vid torget. Bakat på plats varje morgon sedan klockan fyra, med mjöl från en kvarn i länet och smör från gården bredvid; beställ tårtor och smörgåstårtor senast två dagar innan, så har vi dem klara när du kommer.">',
  '  <Hero rubrik="Surdeg som får ta tid" ingress="Bakat på plats varje morgon." />',
  ...Array.from({ length: 12 }, (_, i) => [`  <section class="del del-${i + 1}" aria-labelledby="rubrik-${i + 1}">`, `    <h2 id="rubrik-${i + 1}">Avsnitt ${i + 1}</h2>`,
    `    <p>Text för avsnitt ${i + 1}, ur kundens underlag.</p>`, '  </section>']).flat(),
  '  <section class="oppet" aria-labelledby="oppet">', '    <h2 id="oppet">Öppettider</h2>', '    <dl>{oppettider.map(([dag, tid]) => <><dt>{dag}</dt><dd>{tid}</dd></>)}</dl>',
  '  </section>', '</Bas>'].join('\n') + '\n';
const KOD = {
  'kod/index.astro': SIDA,
  'kod-src/styles/global.css': ':root { --ytan: #fbf7f1; --text: #2a211b; }\nbody { margin: 0; background: var(--ytan); color: var(--text); }\n',
  'kod-src/components/Hero.astro': '---\nconst { rubrik, ingress } = Astro.props;\n---\n<section class="hero"><h1>{rubrik}</h1><p>{ingress}</p></section>\n',
};
const DIFF = [`--- version ${V1K}`, '+++ arbetsversionen', '@@ -6,4 +6,4 @@', ' ---', SIDA.split('\n')[6].replace(/^/, ' '),
  '-  <Hero rubrik="Nybakat varje morgon" />', '+  <Hero rubrik="Surdeg som får ta tid" ingress="Bakat på plats varje morgon." />',
  ...Array.from({ length: 6 }, (_, i) => [`@@ -${10 + i * 8},4 +${10 + i * 8},4 @@`, `   <section class="del del-${i + 1}" aria-labelledby="rubrik-${i + 1}">`,
    `-    <h2 id="rubrik-${i + 1}">Del ${i + 1}</h2>`, `+    <h2 id="rubrik-${i + 1}">Avsnitt ${i + 1}</h2>`, `     <p>Text för avsnitt ${i + 1}, ur kundens underlag.</p>`]).flat()];
function kod(q) {  // som arbetsyta.kod()
  if (q.get('kandidat') !== 'k01') return [404, { fel: 'okänd kandidat' }];
  const lista = [{ fil: 'kod-src/components/Hero.astro', andrad: true, ny: true, borttagen: false }, { fil: 'kod-src/styles/global.css', andrad: false, ny: false, borttagen: false },
    { fil: 'kod/index.astro', andrad: true, ny: false, borttagen: false }];
  const ut = { kandidat: 'k01', arbetsversion: `kunder/${SLUG}/kandidater/k01/sajt (som det står nu)`, mot: q.get('mot') || V1K, versioner: [V1K], fotograferad: V1K, blind: S.blind, filer: lista };
  const fil = q.get('fil');
  if (fil) {
    if (!KOD[fil]) return [404, { fel: 'filen hör inte till kandidatens kod' }];
    ut.fil = { fil, text: KOD[fil], finns: true, diff: fil === 'kod/index.astro' ? DIFF : fil.endsWith('Hero.astro') ? KOD[fil].trimEnd().split('\n').map((r) => '+' + r) : [],
      sokvag: `kunder/${SLUG}/kandidater/k01/sajt/src/${fil.replace(/^kod\//, 'pages/').replace(/^kod-src\//, '')}` };
  }
  return [200, ut];
}
const LOGG = () => ({ tid: new Date().toISOString(), blind: S.blind, loggar: [`underlag/${SLUG}/ateljestarter/${START1}.log`, `underlag/${SLUG}/atelje/arbetare.log`]
  .map((fil, n) => S.blind ? { fil, rader: [], dold: 'visas efter ditt första val: loggen kan bära bedömningar' }
    : { fil, andrad: T(34), rader: Array.from({ length: 120 }, (_, i) => `${T(32 + i / 60)} ${n ? 'arbetaren' : 'starten'}: steg ${i + 1} av förfiningen för k01, token=•••`) }) });

// --- provets server ---
const posts = [], strommar = new Set();
let vagraStrom = false, stromForsok = 0, nekadeStrommar = 0, startAnrop = 0, andringAnrop = 0, forhandsvisningar = 0, svar503 = 0;
let slappStart; const startGrind = new Promise((r) => { slappStart = r; });
let hallLage = null, lageHalls = 0;  // en grind för nästa läsning av läget: start-id:t ska släppas först efter den
const andringar = new Set();
const srv = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://prov'), vag = url.pathname;
  const json = (x, kod = 200) => { res.writeHead(kod, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(x)); };
  if (req.method === 'POST') {
    let text = ''; for await (const b of req) text += b;
    let body; try { body = JSON.parse(text); } catch { return json({ fel: 'ogiltig JSON' }, 400); }
    posts.push({ vag, nyckel: req.headers['x-nyckel'], body, tid: Date.now() });
    if (vag === `/api/flode/${SLUG}/start`) {
      if (++startAnrop === 1) {  // begäran tas emot, men svaret går förlorat: provet håller det tills dubbelklicken är gjorda
        await startGrind; await sov(200); svar503 = Date.now();
        return json({ fel: 'syntetiskt svarsfel efter mottagen begäran' }, 503);
      }
      return json({ slutkod: 5, start_id: body.start_id, besked: 'Begäran är registrerad.' });
    }
    if (vag === `/api/arbetsyta/${SLUG}/partner`) {
      const m = { id: body.meddelande_id, tid: new Date().toISOString(), avsikt: body.avsikt, kontext: body.kontext, text: body.text, lage: 'arbetar', svar: null, fel: null, overlamning: null, slut: null };
      const forra = S.partner.find((x) => x.id === m.id);  // samma meddelande-id ger samma post (partner.skicka)
      if (forra) return json({ ...forra, upprepat: true });
      S.partner.push(m);
      return json(m);
    }
    if (vag === `/api/arbetsyta/${SLUG}/andring`) {
      if (++andringAnrop === 1) return json({ fel: `kandidaten har en ny version sedan du skrev ändringen (din ${String(body.version).slice(0, 12)}, nu 0a1b2c3d4e5f); stäm av mot den aktuella.`, slag: 'Inaktuell' }, 409);
      const upprepat = andringar.has(body.andring_id); andringar.add(body.andring_id);  // samma id ger samma rad (skicka_andring)
      return json({ ok: true, upprepat });
    }
    return json({ fel: 'finns inte' }, 404);
  }
  if (filer.has(vag)) { const f = filer.get(vag); res.writeHead(200, { 'Content-Type': f.typ }); return res.end(f.data); }
  if (vag === '/api/arbetsyta') return json({ tid: new Date().toISOString(), lagen: LAGEN, projekt: [{ slug: SLUG, namn: NAMN, testdata: true, senast_andrad: T(10) },
    { slug: 'prov-andra', namn: 'Provföretaget Två', testdata: true, senast_andrad: T(-600) }] });
  if (vag === `/api/arbetsyta/${SLUG}`) { if (hallLage) { lageHalls++; await hallLage; } return json(lage()); }
  if (vag === `/api/arbetsyta/${SLUG}/strom`) {
    stromForsok++;
    if (vagraStrom) { nekadeStrommar++; return json({ fel: 'syntetiskt: strömmen nekas en stund' }, 503); }
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-store' });
    res.write('retry: 500\n\n');
    res.write(`event: lage\ndata: ${JSON.stringify(lage())}\n\n`);
    strommar.add(res); res.on('close', () => strommar.delete(res));
    return;
  }
  if (vag === `/api/arbetsyta/${SLUG}/partner`) return json(partnerLage(true));
  if (vag === `/api/arbetsyta/${SLUG}/kod`) { const [k, d] = kod(url.searchParams); return json(d, k); }
  if (vag === `/api/arbetsyta/${SLUG}/logg`) return json(LOGG());
  if (vag === '/api/flode') return json({ slugar: [SLUG], pilot: [], kedjan: { steg: [{ steg: 'Kundunderlaget', vem: 'Kundstart samlar underlaget; du godkänner det.' },
    { steg: 'Prototypen', vem: 'Ateljén skapar kandidater med neutrala etiketter; granskarna dömer var för sig.' }] } });
  if (vag === '/api/oversikt') return json({ byggen: [], backlog_vilande: 0, intag_pagar: 0, prospekt_vantar: 0 });
  if (vag.startsWith('/api/')) return json({});
  if (vag === `/visa/${SLUG}/k01`) {
    forhandsvisningar++;
    res.writeHead(200, { 'Content-Type': TYP.html });
    return res.end('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Förslag A</title></head><body><h1>Surdeg som får ta tid</h1><p>Syntetisk förhandsvisning för provet.</p></body></html>');
  }
  if (vag.startsWith('/fil/') && vag.endsWith('.png')) { res.writeHead(200, { 'Content-Type': 'image/png' }); return res.end(PNG); }
  res.writeHead(404); res.end();
});
await new Promise((r) => srv.listen(0, '127.0.0.1', r));
const origin = `http://127.0.0.1:${srv.address().port}`;
assert(![4771, 4781].includes(srv.address().port), 'provet får inte använda dashboardens portar');
function skickaLage() {
  assert(strommar.size >= 1, 'en öppen ström behövs för att skicka ett nytt läge');
  const d = `event: lage\ndata: ${JSON.stringify(lage())}\n\n`;
  for (const r of strommar) r.write(d);
}
async function vantaPa(villkor, text, ms = 5000) { const slut = Date.now() + ms; while (!villkor()) { assert(Date.now() < slut, text); await sov(20); } }
const startPosts = () => posts.filter((p) => p.vag === `/api/flode/${SLUG}/start`).map((p) => p.body);

let browser;
const sammanfattning = { bredder: [320, 390, 768, 1280, 1440, 1672] };
try {
  browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const sidfel = [], konsolfel = [], externa = [];
  page.on('pageerror', (e) => sidfel.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') konsolfel.push({ text: m.text(), url: m.location()?.url || '' }); });
  await page.route((u) => u.origin !== origin, (route) => { externa.push(route.request().url()); return route.abort(); });
  const ram = () => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  const bevis = process.env.NWP_UI_BEVISET;
  if (bevis) await mkdir(bevis, { recursive: true });
  const bild = async (namn, w) => { if (bevis) await page.screenshot({ path: join(bevis, `arbetsyta-${namn}-${w}.png`), fullPage: true }); };
  const statustexter = async (vy) => {
    const tomma = await page.evaluate(() => [...document.querySelectorAll('.ay-lage')].filter((e) => !e.textContent.trim()).map((e) => e.outerHTML.slice(0, 120)));
    const antal = await page.locator('.ay-lage').count();
    assert(antal > 0, `${vy}: vyn ska visa minst ett läge`);
    assert.deepEqual(tomma, [], `${vy}: ett läge får aldrig visas bara med färg eller ikon; varje .ay-lage ska ha text`);
    return antal;
  };
  const axeFynd = {};
  const axeKor = async (vy) => {
    if (!(await page.evaluate(() => typeof axe === 'object'))) await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
    // förhandsvisningen är kundens sajt (prövas i byggets egna prov); här prövas dashboardens yta runt den
    const v = await page.evaluate(async () => (await axe.run(document.querySelector('.ay'), { iframes: false, runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }))
      .violations.map((x) => ({ id: x.id, noder: x.nodes.slice(0, 4).map((n) => `${n.target.join(' ')}: ${n.failureSummary.replace(/\s+/g, ' ').slice(0, 220)}`) })));
    axeFynd[vy] = v;
    assert.deepEqual(v, [], `axe (wcag2a, wcag2aa, wcag21aa) i ${vy}`);
  };
  const spill = async () => page.evaluate(() => ({ bredd: document.documentElement.scrollWidth, fonster: innerWidth }));

  // 1. Nyckeln ur adressen, kunden och vyernas flikar
  await page.goto(`${origin}/#nyckel=${NYCKEL}&till=arbetsyta/${SLUG}`);
  await page.locator('#ay-roller').getByRole('heading', { name: 'Granskning' }).waitFor();
  await page.locator('#ay-anslutning[data-lage="ansluten"]').waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/arbetsyta/${SLUG}`, 'efter laddningen ska adressen vara arbetsytans, utan nyckeln');
  assert(!page.url().includes(NYCKEL), 'nyckeln får aldrig stanna i adressen');
  assert.equal(await page.evaluate(() => localStorage.getItem('nwp-dashboardnyckel')), NYCKEL, 'nyckeln ska sparas i webbläsaren');
  assert.deepEqual(await page.evaluate(() => [typeof kundstartvy, typeof kirurgForbattring, typeof arbetsytavy]), ['function', 'function', 'function'],
    'dashboardens separata skript ska laddas som riktig JavaScript');
  assert.equal((await page.locator('#ay-kund option:checked').textContent()).trim(), `${NAMN} (testdata)`, 'huvudet ska visa kundens namn, märkt som testdata');
  assert(await page.locator('#ay-huvud .ay-testdata').filter({ hasText: 'Testdata' }).isVisible(), 'huvudet ska visa märket Testdata');
  const flikar = page.getByRole('navigation', { name: 'Arbetsytans vyer' }).getByRole('link');
  assert.deepEqual(await flikar.allTextContents(), ['Arbetsyta', 'Byggflöde', 'Kod och preview'], 'arbetsytan ska ha tre vyer');
  assert.deepEqual(await flikar.evaluateAll((a) => a.map((x) => x.getAttribute('aria-current'))), ['page', null, null], 'aria-current ska stå på Arbetsyta');
  assert.equal(posts.length, 0, 'att läsa arbetsytan skickar inget');
  // partnerns användningsrad: cache-siffrorna och listpriset som Claude Code rapporterar det, aldrig som en faktura
  const anv = page.locator('#ay-samtal .ay-msg.partnern .meta').first();
  await anv.waitFor();
  const anvText = (await anv.textContent()).replace(/\s+/g, ' ');
  assert.match(anvText, /1520 in, 8000 ur cache, 1200 till cache, 214 ut tokens/, 'partnerns användningsrad ska visa cache-siffrorna');
  assert.match(anvText, /listpris enligt Claude Code 0\.12 USD, inte fakturerat/, 'listpriset ska stå som Claude Codes siffra, inte fakturerat');
  assert.equal(await page.locator('#ay-partnerchip .ay-lage').getAttribute('data-lage'), 'avslutad', 'partnerns svarade tur ska stå som avslutad');

  // 4. Läget står i text, aldrig bara i färg
  sammanfattning.lagen_med_text = { arbetsyta: await statustexter('Arbetsyta') };

  // 5. Förhandsvisningen: sandlåda utan toppnavigering och popup-fönster, ingen referent; Mobil byter bara ramen
  const ram_ = page.locator('#ay-material iframe');
  await ram_.waitFor();
  const sandbox = (await ram_.getAttribute('sandbox')).split(/\s+/).filter(Boolean);
  assert(sandbox.length > 0, 'förhandsvisningen ska ha attributet sandbox');
  assert(!sandbox.some((t) => t.startsWith('allow-top-navigation')), 'förhandsvisningen får inte navigera dashboarden (allow-top-navigation)');
  assert(!sandbox.some((t) => t.startsWith('allow-popups')), 'förhandsvisningen får inte öppna fönster (allow-popups)');
  assert.equal(await ram_.getAttribute('referrerpolicy'), 'no-referrer', 'förhandsvisningen ska inte få dashboardens adress som referent');
  const src = await ram_.getAttribute('src');
  assert.equal(src, `/visa/${SLUG}/k01`, 'förhandsvisningen ska visa den valda kandidatens arbetsversion');
  await vantaPa(() => forhandsvisningar >= 1, 'förhandsvisningen ska laddas');
  const laddningarFore = forhandsvisningar;
  await page.locator('#ay-material').getByRole('button', { name: 'Mobil', exact: true }).click();
  await page.locator('#ay-material .ay-scen[data-enhet="mobil"]').waitFor();
  assert.equal(await page.locator('#ay-material iframe').getAttribute('src'), src, 'Mobil ska byta ramens bredd, inte förhandsvisningens adress');
  assert.equal(await page.locator('#ay-material').getByRole('button', { name: 'Mobil', exact: true }).getAttribute('aria-pressed'), 'true');
  await ram();
  await page.locator('#ay-material').getByRole('button', { name: 'Dator', exact: true }).click();
  await page.locator('#ay-material .ay-scen[data-enhet="dator"]').waitFor();
  await sov(150);
  assert.equal(forhandsvisningar - laddningarFore, 0, 'Mobil och Dator byter bredden, de laddar inte om förhandsvisningen');
  sammanfattning.forhandsvisning = { sandbox: sandbox.join(' '), referrerpolicy: 'no-referrer', omladdningar_vid_enhetsbyte: forhandsvisningar - laddningarFore };

  // 12. Rörelsen följer prefers-reduced-motion
  const animation = () => page.locator('.ay-lage[data-lage="aktiv"] svg').first().evaluate((e) => getComputedStyle(e).animationName);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  assert.equal(await animation(), 'ay-andas', 'utan önskemål ska ett arbetande läge andas (provet ska kunna bli rött)');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  assert.equal(await animation(), 'none', 'med prefers-reduced-motion: reduce får inget läge animeras');
  await page.emulateMedia({ reducedMotion: null });

  // 2. Inget sidledes spill; på smala skärmar ett område åt gången
  const synliga = () => page.evaluate(() => ['ay-dialog', 'ay-mitten', 'ay-roller'].filter((k) => {
    const el = document.querySelector('#ay-ytan > .' + k); return el && getComputedStyle(el).display !== 'none' && el.getBoundingClientRect().width > 0; }));
  const omrade = (namn) => page.locator('.ay-omraden').getByRole('button', { name: namn, exact: true });
  sammanfattning.spill = { arbetsyta: {}, byggflode: {}, kod: {} };
  for (const w of sammanfattning.bredder) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    const s = await spill(); sammanfattning.spill.arbetsyta[w] = s.bredd - s.fonster;
    assert(s.bredd <= s.fonster, `Arbetsyta: sidledes spill vid ${w} px (${s.bredd} > ${s.fonster})`);
    if (w < 900) {
      assert.deepEqual(await synliga(), ['ay-mitten'], `vid ${w} px ska bara Resultat synas från början`);
      for (const [knapp, klass] of [['Samtal', 'ay-dialog'], ['Sessioner', 'ay-roller'], ['Resultat', 'ay-mitten']]) {
        await omrade(knapp).click(); await ram();
        assert.deepEqual(await synliga(), [klass], `vid ${w} px ska ${knapp} visa ett område åt gången`);
        assert.equal(await omrade(knapp).getAttribute('aria-pressed'), 'true', `${knapp} ska vara markerad`);
        const s2 = await spill();
        assert(s2.bredd <= s2.fonster, `Arbetsyta, ${knapp}: sidledes spill vid ${w} px (${s2.bredd} > ${s2.fonster})`);
      }
    } else assert.deepEqual(await synliga(), ['ay-dialog', 'ay-mitten', 'ay-roller'], `vid ${w} px ska samtal, resultat och sessioner synas samtidigt`);
    if ([390, 1440].includes(w)) await bild('arbetsyta', w);
  }
  sammanfattning.ett_omrade_at_gangen = true;

  // 3. axe i Arbetsyta (bred och smal)
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await axeKor('Arbetsyta 1440');
  await page.setViewportSize({ width: 390, height: 900 }); await ram();
  await axeKor('Arbetsyta 390');
  await omrade('Sessioner').click(); await axeKor('Arbetsyta 390, Sessioner');
  await omrade('Samtal').click(); await axeKor('Arbetsyta 390, Samtal');
  await omrade('Resultat').click();
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();

  // 11. Byggflödet: nio steg, blindningen, systemförbättringen för sig och Fler vyer
  await flikar.filter({ hasText: 'Byggflöde' }).click();
  await page.locator('ol.ay-stegrad').waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/arbetsyta/${SLUG}/flode`);
  assert.deepEqual(await flikar.evaluateAll((a) => a.map((x) => x.getAttribute('aria-current'))), [null, 'page', null], 'aria-current ska stå på Byggflöde');
  assert.deepEqual(await page.locator('ol.ay-stegrad > li .namn').allTextContents(), STEGNAMN, 'stegraden ska visa README:s nio steg');
  assert.equal(await page.locator('ol.ay-stegrad > li[data-pagar]').count(), 1, 'ett steg pågår');
  assert(await page.locator('.ay-grupper .ay-notis').filter({ hasText: 'Ditt första val i körningen är inte gjort' }).isVisible(), 'blindningen ska stå i Byggflöde');
  const system = page.getByRole('region', { name: 'Systemförbättring, skilt från kundproduktionen' });
  assert.deepEqual(await system.getByRole('link').evaluateAll((a) => a.map((x) => [x.textContent.trim(), x.getAttribute('href')])).then((l) => l.filter(([t]) => ['Kirurgen', 'Backlog'].includes(t))),
    [['Kirurgen', '#/kirurgen'], ['Backlog', '#/backlog']], 'Kirurgen och Backlog ska nås från systemförbättringen');
  assert.equal(await system.locator('.ay-stegrad, .ay-grupp, a[href^="#/flode"], a[href^="#/prototyp"], a[href^="#/kundstart"]').count(), 0,
    'systemförbättringen ska stå skild från kundproduktionen');
  await page.locator('.ay-meny summary').filter({ hasText: 'Fler vyer' }).click();
  const meny = page.getByRole('navigation', { name: 'Dashboardens övriga vyer' });
  await meny.waitFor();
  const menyn = await meny.evaluate((n) => [...n.children].map((x) => [x.tagName, x.textContent.trim()]));
  const grupp = (text) => { let g = null; for (const [tag, t] of menyn) { if (tag === 'H4') g = t; else if (t === text) return g; } return undefined; };
  for (const [text, g] of [['Kundstart', 'Kundproduktion'], ['Jämförelser', 'Kundproduktion'], ['Dokumentation och rapporter', 'Rapporter'], ['Kirurgen', 'Systemförbättring'], ['Backlog', 'Systemförbättring']])
    assert.equal(grupp(text), g, `Fler vyer ska ha ${text} under ${g}`);
  await page.locator('.ay-meny summary').click();
  sammanfattning.lagen_med_text.byggflode = await statustexter('Byggflöde');
  await axeKor('Byggflöde 1440');
  await bild('byggflode', 1440);
  for (const w of sammanfattning.bredder) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    const s = await spill(); sammanfattning.spill.byggflode[w] = s.bredd - s.fonster;
    assert(s.bredd <= s.fonster, `Byggflöde: sidledes spill vid ${w} px (${s.bredd} > ${s.fonster})`);
    if (w === 390) { await axeKor('Byggflöde 390'); await bild('byggflode', 390); }
  }

  // Kod och preview
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await flikar.filter({ hasText: 'Kod och preview' }).click();
  await page.locator('#ay-filvy pre.ay-kodtext').waitFor();
  assert.equal(await page.locator('#ay-fil-rubrik').textContent(), 'src/components/Hero.astro', 'kodvyn ska öppna den första ändrade filen');
  await page.locator('#ay-filer').getByRole('button', { name: /src\/pages\/index\.astro/ }).click();
  await page.locator('#ay-filvy .minus').filter({ hasText: 'Nybakat varje morgon' }).waitFor();
  await page.locator('#ay-logg').filter({ hasText: 'visas efter ditt första val' }).first().waitFor();
  sammanfattning.lagen_med_text.kod = await statustexter('Kod och preview');
  await axeKor('Kod och preview 1440');
  await bild('kod', 1440);
  for (const w of sammanfattning.bredder) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    const s = await spill(); sammanfattning.spill.kod[w] = s.bredd - s.fonster;
    assert(s.bredd <= s.fonster, `Kod och preview: sidledes spill vid ${w} px (${s.bredd} > ${s.fonster})`);
    if (w === 390) { await axeKor('Kod och preview 390'); await bild('kod', 390); }
  }
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await flikar.filter({ hasText: 'Arbetsyta' }).click();
  await page.locator('#ay-remsa').getByRole('heading', { name: 'Kontroller' }).waitFor();
  assert.equal(posts.length, 0, 'att byta vy skickar inget');

  // 8. Läget följer strömmen utan omladdning; övergångar meddelas kort, enskilda verktygsanrop inte
  await page.evaluate(() => { window.__laddad = performance.timeOrigin; window.__meddelanden = []; const r = document.getElementById('ay-meddelande');
    new MutationObserver(() => { if (r.textContent) window.__meddelanden.push(r.textContent); }).observe(r, { childList: true, characterData: true, subtree: true }); });
  const region = page.locator('#ay-meddelande');
  assert.equal(await region.getAttribute('role'), 'status'); assert.equal(await region.getAttribute('aria-live'), 'polite');
  const meddelat = async (text) => { await page.waitForFunction((t) => document.getElementById('ay-meddelande').textContent.includes(t), text, { timeout: 5000 }); return region.textContent(); };
  S.sessioner.push(ateljesession('7d3a2c99-3e4f-4051-8cbd-2e3f4a5b6c7d', 'kritik-a-k01', 'granskning', 'k01', T(25), 'startar', 'processen lever; transkriptet har inte observerats än', []));
  skickaLage();
  const startText = await meddelat('startade');
  assert.match(startText, /granskningen för Förslag A startade/, 'en ny session ska meddelas när den startar');
  await page.locator('#ay-roller .ay-ansvar').filter({ hasText: 'Granskning' }).locator('.ay-session .namn').filter({ hasText: 'granskningen · Förslag A' }).waitFor();
  const skaparenA = page.locator('#ay-roller article.ay-session').filter({ has: page.locator('.namn', { hasText: 'skaparen · Förslag A' }) });
  assert.equal(await skaparenA.locator('.ay-lage').getAttribute('data-lage'), 'aktiv');
  avsluta(S.sessioner[0], 26);
  skickaLage();
  await skaparenA.locator('.ay-lage[data-lage="avslutad"]').waitFor();
  assert.equal((await skaparenA.locator('.ay-lage').textContent()).trim(), 'avslutad', 'rollkortet ska visa det nya läget i text');
  const slutText = await meddelat('skaparen för Förslag A: avslutad');
  assert(slutText.length <= 200, 'meddelandet ska vara kort');
  await sov(300);
  const fore = await page.evaluate(() => window.__meddelanden.length), textFore = await region.textContent();
  const skaparenB = page.locator('#ay-roller article.ay-session').filter({ has: page.locator('.namn', { hasText: 'skaparen · Förslag B' }) });
  for (const [i, verktyg] of ['Grep', 'Glob', 'Edit'].entries()) {
    const b = S.sessioner[1]; b.aktivitet.handelser.push(handelse(27 + i, verktyg)); b.aktivitet.antal++; b.senaste_handelse = b.aktivitet.senaste_handelse = T(27 + i);
    skickaLage();
    await skaparenB.filter({ hasText: `${verktyg} (ok)` }).waitFor();  // läget kom fram: kortet visar det nya anropet
    await sov(250);
  }
  assert.equal(await page.evaluate(() => window.__meddelanden.length), fore, 'enskilda verktygsanrop får inte meddelas');
  assert.equal(await region.textContent(), textFore, 'meddelanderegionen ska stå orörd vid enskilda verktygsanrop');
  assert.equal(await page.evaluate(() => performance.timeOrigin), await page.evaluate(() => window.__laddad), 'sidan ska aldrig laddas om');
  sammanfattning.live = { start: startText, slut: slutText, verktygsanrop_meddelade: 0 };

  // körningen väntar på ägaren: Förfina de valda erbjuds
  for (const s of S.sessioner) if (s.lage !== 'avslutad') avsluta(s, 30);
  S.korning = korning('ny', START1, T(0), 'klar_for_bedomning', false);
  S.stegstatus = ['skapat', 'skapat', 'väntar på ägaren', ...Array(6).fill('inte påbörjat')];
  S.handlingar = [{ id: 'valda', text: 'Förfina de valda förslagen' }];
  S.startjournal[0] = { ...S.startjournal[0], status: 'klar', slutkod: 0, process_lever: false };
  skickaLage();
  await meddelat('Körningen väntar på ditt beslut');
  await page.getByRole('button', { name: 'Förfina de valda förslagen' }).waitFor();

  // 10. Samtalet: en fråga med markeringen; meddelande-id:t är innehållets hash
  const markLagret = () => page.evaluate((k) => JSON.parse(sessionStorage.getItem(k) || 'null'), `nwp-arbetsyta-markering:${SLUG}`);
  const galler = page.locator('#ay-markering');
  const gallerText = async () => (await galler.textContent()).replace(/\s+/g, ' ');
  const andringPosts = () => posts.filter((p) => p.vag === `/api/arbetsyta/${SLUG}/andring`).map((p) => p.body);
  await page.locator('#ay-text').fill('Vad saknas i första vyn för Förslag A?');
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka', exact: true }).click();
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Skickat' }).waitFor();
  const pp = posts.filter((p) => p.vag === `/api/arbetsyta/${SLUG}/partner`);
  assert.equal(pp.length, 1, 'ett meddelande till partnern');
  assert.match(String(pp[0].body.meddelande_id), /^m[0-9a-f]{40}$/, 'meddelande-id:t ska vara innehållets hash (m och 40 hex)');
  assert.equal(pp[0].body.avsikt, 'fraga'); assert.equal(pp[0].body.text, 'Vad saknas i första vyn för Förslag A?');
  assert.equal(pp[0].body.kontext?.kandidat, 'k01', 'markeringen ska följa med: kandidaten som visas');
  assert.equal(pp[0].body.kontext?.version, V1K); assert.equal(pp[0].body.kontext?.vy, 'Arbetsyta');
  assert.equal(await markLagret(), null, 'en fråga fryser ingen markering');

  // 1. Markeringen fryses: när avsikten blir Ändring och när en kandidat väljs medan Ändring är vald
  await page.locator('#ay-skriv').getByRole('button', { name: 'Ändring', exact: true }).click();
  await page.locator('#ay-skriv .ay-notis').filter({ hasText: 'ditt val av kandidaten' }).waitFor();
  let mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning], ['k01', V1, T(0)], 'Ändring ska frysa kandidat, version och körning');
  assert.match(await gallerText(), new RegExp(`Förslag A.* version ${V1K}, körningen .*, vy Arbetsyta`), 'raden Gäller ska visa den frysta markeringen');
  const rensa = galler.getByRole('button', { name: 'Rensa markeringen' });
  await rensa.click();
  assert.equal(await markLagret(), null, 'Rensa markeringen ska ta bort markeringen');
  await rensa.waitFor({ state: 'detached', timeout: 2000 });
  await page.locator('#ay-material').getByRole('button', { name: 'Kandidater', exact: true }).click();
  await page.locator('#ay-material [data-kandidat="k01"]').click();
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning], ['k01', V1, T(0)], 'en kandidat som väljs medan Ändring är vald ska frysas');
  await rensa.waitFor();
  const skickaAndring = page.locator('#ay-skriv').getByRole('button', { name: 'Skicka ändring' });
  assert(await skickaAndring.isEnabled(), 'Skicka ändring ska gå att använda när körningen väntar på ditt beslut');
  await page.locator('#ay-text').fill('Gör rubriken i första vyn kortare.');
  await page.locator('[data-falt="sida"]').fill('/'); await page.locator('[data-falt="del"]').fill('första vyn');
  // en ny version av den markerade kandidaten: markeringen blir inaktuell och inget skickas
  await page.locator('#ay-dialog-rubrik').click();
  S.k01v = V2;
  skickaLage();
  const notis = page.locator('#ay-skriv .ay-notis').filter({ hasText: 'Inaktuell markering' });
  await notis.waitFor();
  assert.match(await notis.textContent(), new RegExp(`kandidaten har en ny version sedan du markerade \\(${V1K}, nu ${V2K}\\)`), 'notisen ska säga varför');
  assert(await skickaAndring.isDisabled(), 'Skicka ändring ska vara inaktiv när markeringen är inaktuell');
  assert.match(String(await skickaAndring.getAttribute('title')), /inaktuell.*stäm av/, 'knappens title ska säga varför den är inaktiv');
  await page.locator('#ay-text').press('Control+Enter');  // kortkommandot går förbi knappen: spärren ska sitta i sändningen
  await page.locator('#ay-skrivsvar').filter({ hasText: /^Inaktuell: kandidaten har en ny version/ }).waitFor();
  await sov(300);
  assert.equal(andringPosts().length, 0, 'en inaktuell markering får inte skickas');
  await notis.getByRole('button', { name: 'Stäm av mot den aktuella' }).click();
  await notis.waitFor({ state: 'detached', timeout: 2000 });
  assert(await skickaAndring.isEnabled(), 'efter Stäm av ska Skicka ändring gå att använda');
  assert.equal(await skickaAndring.getAttribute('title'), '');
  mark = await markLagret();
  assert.deepEqual([mark?.version_hel, mark?.sida, mark?.del], [V2, '/', 'första vyn'], 'Stäm av ska binda den nya versionen och behålla sida och del');
  assert.match(await gallerText(), new RegExp(`version ${V2K}`), 'raden Gäller ska visa den avstämda versionen');
  // 409: arbetsytan visar skälet och skickar inget av sig själv; omförsöket med samma innehåll ger samma id
  await skickaAndring.click();
  await page.locator('#ay-skrivsvar').filter({ hasText: /^Inaktuell/ }).waitFor();
  assert.match(await page.locator('#ay-skrivsvar').textContent(), /^Inaktuell: kandidaten har en ny version.* Stäm av/, 'ett 409 ska visas som Inaktuell med en uppmaning att stämma av');
  await sov(1000);
  assert.equal(andringPosts().length, 1, 'efter ett 409 skickar arbetsytan inget av sig själv');
  assert.equal(andringPosts()[0].version, V2, 'ändringen ska bära den avstämda versionen');
  await skickaAndring.click();
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Ändringen är sparad' }).waitFor();
  const ap = andringPosts();
  assert.equal(ap.length, 2, 'två försök med ändringen');
  assert.match(String(ap[0].andring_id), /^a[0-9a-f]{40}$/, 'ändrings-id:t ska vara innehållets hash (a och 40 hex)');
  assert.equal(ap[1].andring_id, ap[0].andring_id, 'samma ändring ska ge samma id vid omförsöket');
  assert.deepEqual([ap[1].kandidat, ap[1].version, ap[1].beslut, ap[1].vy, ap[1].sida, ap[1].del, ap[1].korning, ap[1].fil],
    ['k01', V2, 'valj', 'Arbetsyta', '/', 'första vyn', T(0), null], 'ändringen ska vara bunden till kandidat, version, körning och markering');
  assert.equal(await markLagret(), null, 'en sparad ändring släpper markeringen');

  // 3. Samma ändring från en andra flik ger samma id
  const sida2 = await ctx.newPage();
  sida2.on('pageerror', (e) => sidfel.push('andra fliken: ' + e.message));
  sida2.on('console', (m) => { if (m.type() === 'error') konsolfel.push({ text: m.text(), url: m.location()?.url || '' }); });
  await sida2.route((u) => u.origin !== origin, (route) => { externa.push(route.request().url()); return route.abort(); });
  await sida2.goto(`${origin}/#/arbetsyta/${SLUG}`);
  await sida2.locator('#ay-skriv').getByRole('button', { name: 'Ändring', exact: true }).click();
  await sida2.locator('#ay-text').fill('Gör rubriken i första vyn kortare.');
  await sida2.locator('[data-falt="sida"]').fill('/'); await sida2.locator('[data-falt="del"]').fill('första vyn');
  await sida2.locator('#ay-skriv').getByRole('button', { name: 'Skicka ändring' }).click();
  await sida2.locator('#ay-skrivsvar').filter({ hasText: 'Ändringen är sparad' }).waitFor();
  assert.equal(andringPosts().length, 3);
  assert.equal(andringPosts()[2].andring_id, ap[0].andring_id, 'samma ändring från en andra flik ska ge samma andring_id');
  await sida2.close();

  // 2. En markering i kodvyn följer med till Arbetsyta: raden Gäller visar filen och ändringen bär den
  await flikar.filter({ hasText: 'Kod och preview' }).click();
  await page.locator('#ay-filvy pre.ay-kodtext').waitFor();
  await page.locator('#ay-filer').getByRole('button', { name: /src\/pages\/index\.astro/ }).click();
  await page.locator('#ay-fil-rubrik').filter({ hasText: 'src/pages/index.astro' }).waitFor();
  await page.locator('#ay-filhuvud').getByRole('button', { name: 'Markera för en ändring' }).click();
  await meddelat('Filen är markerad');
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.vy, mark?.fil], ['k01', V2, 'Kod och preview', 'src/pages/index.astro'], 'kodvyns markering ska binda kandidat, version och fil');
  await flikar.filter({ hasText: 'Arbetsyta' }).click();
  await galler.filter({ hasText: 'fil src/pages/index.astro' }).waitFor();
  assert.match(await gallerText(), /vy Kod och preview, fil src\/pages\/index\.astro/, 'raden Gäller ska visa kodvyns markering');
  assert.equal(await page.locator('#ay-skriv [data-avsikt="andring"]').getAttribute('aria-pressed'), 'true', 'en markering i kodvyn ska välja Ändring');
  assert.equal(await page.locator('#ay-text').inputValue(), '', 'en skickad ändring ska inte komma tillbaka som utkast');
  await page.locator('#ay-text').fill('Korta rubriken i Hero till fyra ord.');
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka ändring' }).click();
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Ändringen är sparad' }).waitFor();
  const kp = andringPosts().at(-1);
  assert.deepEqual([kp.fil, kp.vy, kp.kandidat, kp.version], ['src/pages/index.astro', 'Kod och preview', 'k01', V2], 'ändringen ska bära kodvyns fil');
  assert.notEqual(kp.andring_id, ap[0].andring_id, 'en annan ändring ger ett annat id');
  sammanfattning.partner = { meddelande_id: 'm+40 hex', avsikt: 'fraga', kandidat: 'k01', blindvarning: true };
  sammanfattning.markering = { fryst_vid_andring: true, fryst_vid_kandidatval: true, rensa: true, inaktuell_utan_post: true, stam_av_ny_version: true,
    andring_409_utan_eget_omforsok: true, samma_id_omforsok: true, samma_id_andra_fliken: true, kodvyns_fil: true };

  // 6. Starten: dubbelklick och ett extra klick ger en begäran; ett förlorat svar ger samma start-id vid omförsöket
  const forfina = page.getByRole('button', { name: 'Förfina de valda förslagen' });
  await forfina.click({ clickCount: 2 });
  await page.locator('[data-handling="valda"]').dispatchEvent('click');
  await vantaPa(() => startPosts().length >= 1, 'starten ska nå servern');
  await sov(200);
  const klickKlara = Date.now();
  assert.equal(startPosts().length, 1, 'dubbelklick och ett extra klick medan begäran väntar får bara skicka en begäran');
  assert.match(await page.locator('#ay-handlingssvar').textContent(), /Skickar begäran/, 'vyn ska visa att begäran väntar');
  slappStart();
  await page.locator('#ay-handlingssvar').filter({ hasText: 'Svaret gick inte att bekräfta' }).waitFor();
  assert(svar503 > klickKlara, 'klicken ska ha gjorts medan begäran väntade');
  assert.equal(startPosts().length, 1);
  // 5. start-id:t släpps först när läget lästs om efter svaret
  const startNyckel = `nwp-start:${SLUG}:valda`, sparat = () => page.evaluate((k) => sessionStorage.getItem(k), startNyckel);
  let slappLage; hallLage = new Promise((r) => { slappLage = r; });
  const hallnaFore = lageHalls;
  await forfina.click();
  await vantaPa(() => lageHalls > hallnaFore, 'efter svaret ska arbetsytan läsa om läget');
  assert.equal(startPosts().length, 2);
  assert.equal(await sparat(), startPosts()[1].start_id, 'start-id:t ska stå kvar medan läget läses om');
  hallLage = null; slappLage();
  await page.locator('#ay-handlingssvar').filter({ hasText: 'Begäran är registrerad.' }).waitFor();
  assert.equal(await sparat(), null, 'när läget lästs om ska start-id:t släppas');
  assert.equal(await page.locator('#ay-handlingssvar').getAttribute('role'), 'status');
  const sp = startPosts();
  assert.equal(sp.length, 2); assert.equal(sp[0].handling, 'valda'); assert.equal(sp[1].start_id, sp[0].start_id, 'omförsöket ska använda samma start-id');
  sammanfattning.start = { dubbla_starter: false, omforsok_samma_start_id: true, slapps_efter_omlasning: true };

  // förfiningen pågår: en ny körning med Stoppa
  S.partner.at(-1).lage = 'svarat'; S.partner.at(-1).slut = T(31);
  S.partner.at(-1).svar = { ...S.partner[0].svar, text: 'Första vyn saknar ett tydligt nästa steg.' };
  S.korning = korning('valda', START2, T(32), 'forfina', true);
  S.stegstatus = ['skapat', 'skapat', 'beslutat', 'pågår', ...Array(5).fill('inte påbörjat')];
  S.handlingar = [{ id: 'stoppa', text: 'Stoppa arbetet' }];
  S.startjournal.unshift({ start_id: sp[0].start_id, handling: 'valda', tid: T(32), status: 'startad', slutkod: null, stopp_begart: false, stopp_sent: false, fel: null, process_lever: true });
  S.sessioner = [];
  S.sessioner.push(ateljesession('8e4b3daa-4f50-4162-9dce-3f4a5b6c7d8e', 'forfina-k01', 'utforande', 'k01', T(33), 'aktiv', 'processen lever', [handelse(33, 'Read')]));
  skickaLage();
  const nyText = await meddelat('En ny körning har startat');
  assert.match(nyText, /förfiningen för Förslag A startade/);

  // 7. Stoppa kräver två steg; Avbryt återgår; bekräftelsen nås och trycks med tangentbordet
  const remsa = page.locator('#ay-remsa');
  const stopp = remsa.getByRole('button', { name: 'Stoppa', exact: true });
  await stopp.click();
  await remsa.locator('.ay-bekrafta').filter({ hasText: 'Stoppa arbetaren' }).waitFor();
  assert.equal(startPosts().length, 2, 'första klicket på Stoppa får inte skicka något');
  await remsa.getByRole('button', { name: 'Avbryt' }).click();
  await remsa.locator('[data-handling="stoppa"]:not([data-bekraftad])').waitFor();
  assert.equal(await remsa.getByText('Stoppa arbetaren').count(), 0, 'Avbryt ska ta bort bekräftelsen');
  assert.equal(await page.evaluate(() => document.activeElement?.dataset.fokus), 'h-stoppa', 'efter Avbryt ska fokus stå kvar på Stoppa');
  assert.equal(startPosts().length, 2, 'Avbryt skickar inget');
  await page.keyboard.press('Enter');
  await remsa.locator('[data-bekraftad]').waitFor();
  const fokus = () => page.evaluate(() => ({ nyckel: document.activeElement?.dataset.fokus, kontur: getComputedStyle(document.activeElement).outlineStyle,
    synlig: document.activeElement?.matches(':focus-visible') }));
  assert.equal((await fokus()).nyckel, 'bekrafta', 'bekräftelsen ska få fokus');
  await page.keyboard.press('Tab');
  assert.equal((await fokus()).nyckel, 'avbryt', 'Tab ska nå Avbryt');
  await page.keyboard.press('Shift+Tab');
  const f = await fokus();
  assert.equal(f.nyckel, 'bekrafta', 'Tab ska nå bekräftelsen');
  assert(f.synlig && f.kontur !== 'none', `fokus ska synas på bekräftelsen (outline-style ${f.kontur})`);
  assert.equal(startPosts().length, 2, 'att nå bekräftelsen skickar inget');
  await page.keyboard.press('Enter');
  await vantaPa(() => startPosts().length >= 3, 'den bekräftade stoppbegäran ska nå servern');
  await page.locator('#ay-handlingssvar').filter({ hasText: 'Begäran är registrerad.' }).waitFor();
  await sov(300);
  assert.equal(startPosts().length, 3, 'en bekräftelse ska ge exakt en stoppbegäran');
  assert.equal(startPosts()[2].handling, 'stoppa');
  sammanfattning.stopp = { tva_steg: true, avbryt: true, tangentbord: true, fokus_synlig: true };

  // 9. Ett tappat svar och nekade återanslutningar: Återansluter, sedan ansluten med luckan meddelad
  vagraStrom = true;
  const forsokFore = stromForsok;
  for (const r of strommar) r.destroy();
  await page.locator('#ay-anslutning[data-lage="ateransluter"]').waitFor({ timeout: 5000 });
  // ett felsvar stänger EventSource för gott (readyState 2): återanslutningen efter det måste vara vyns egen
  await page.waitForFunction(() => window.__arbetsyta.strom?.readyState === 2, null, { timeout: 5000 });
  await sov(1500);
  assert(nekadeStrommar >= 1 && stromForsok > forsokFore, 'minst en återanslutning ska ha nekats (provet ska pröva 503-vägen)');
  vagraStrom = false;
  await page.locator('#ay-anslutning[data-lage="ansluten"]').waitFor({ timeout: 15000 });
  const lucka = await meddelat('Luckan');
  assert.equal(await page.evaluate(() => performance.timeOrigin), await page.evaluate(() => window.__laddad), 'återanslutningen ska ske utan omladdning');
  sammanfattning.ateranslutning = { nekade_forsok: nekadeStrommar, webblasaren_gav_upp: true, lucka_meddelad: true, text: lucka };

  // 3 (forts.). Kod och preview efter valet: loggarna och aktiviteten i sin verkliga längd
  S.blind = false;
  const forfinaren = S.sessioner[0];
  for (let i = 0; i < 24; i++) forfinaren.aktivitet.handelser.push(handelse(34 + i / 4, ['Read', 'Edit', 'Bash', 'Grep'][i % 4], 'ok', { fil: `kunder/${SLUG}/kandidater/k01/sajt/src/pages/index.astro` }));
  forfinaren.aktivitet.antal = forfinaren.aktivitet.handelser.length;
  skickaLage();
  await page.locator('#ay-roller .ay-ansvar').first().waitFor();
  await flikar.filter({ hasText: 'Kod och preview' }).click();
  await page.locator('#ay-logg pre.ay-logg').first().waitFor();
  await page.locator('#ay-kodaktivitet li').nth(13).waitFor();
  await axeKor('Kod och preview efter valet 1440');
  await page.setViewportSize({ width: 390, height: 900 }); await ram();
  const s = await spill(); sammanfattning.spill.kod_efter_valet_390 = s.bredd - s.fonster;
  assert(s.bredd <= s.fonster, `Kod och preview efter valet: sidledes spill vid 390 px (${s.bredd} > ${s.fonster})`);
  await axeKor('Kod och preview efter valet 390');
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await flikar.filter({ hasText: 'Arbetsyta' }).click();
  await page.locator('#ay-remsa').getByRole('heading', { name: 'Kontroller' }).waitFor();

  // 13. Inga sidfel; konsolfelen är bara de nätfel provet självt framkallar
  const avsiktliga = [/\/api\/flode\/prov-kund\/start$/, /\/api\/arbetsyta\/prov-kund\/andring$/, /\/api\/arbetsyta\/prov-kund\/strom$/];
  const forvantat = (x) => (/^Failed to load resource/.test(x.text) && avsiktliga.some((r) => r.test(x.url.split('?')[0])))
    || /^EventSource's response has a status 503/.test(x.text);
  assert.deepEqual(sidfel, [], 'inga fel i sidans skript');
  assert.deepEqual(konsolfel.filter((x) => !forvantat(x)), [], 'inga oväntade konsolfel');
  assert(posts.every((p) => p.nyckel === NYCKEL), 'varje skrivning ska bära dashboardnyckeln ur adressen');
  sammanfattning.axe_fynd = Object.values(axeFynd).reduce((n, v) => n + v.length, 0);
  sammanfattning.axe_vyer = Object.keys(axeFynd);
  sammanfattning.sidfel = 0;
  sammanfattning.avsiktliga_natfel_i_konsolen = konsolfel.map((x) => `${x.url.replace(origin, '')}: ${x.text.slice(0, 70)}`);
  sammanfattning.externa_anrop_stoppade = externa.length;
  sammanfattning.reducerad_rorelse = true;
  sammanfattning.api = 'syntetiska svar; riktig server prövas separat';
  console.log(JSON.stringify(sammanfattning));
} finally {
  await browser?.close();
  srv.closeAllConnections?.();
  await new Promise((r) => srv.close(r));
}
