// Arbetsytans UI-prov i portalens ram (dashboard/arbetsyta.js, studio.js och portal.js; ägarens uppdrag 2026-10-09 och
// beskedet 2026-10-11: den gamla arbetsvyn finns inte längre, allt finns i den nya; kunskap/arbetsyta.md och
// kunskap/designstudio.md) med riktiga klick och syntetiska HTTP-svar: en node:http-server med index.html, dashboardens separata skript och ett påhittat
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
const filer = new Map(await Promise.all([['/', 'index.html'], ...['kundstart-agare.js', 'kundstart-agare.css', 'kirurg-forbattring.js', 'arbetsyta.js', 'arbetsyta.css', 'studio.js', 'studio.css', 'portal.js', 'portal.css']
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
const V3 = '3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f', V3K = V3.slice(0, 12);  // och versionen efter din ändring
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
const S = { blind: true, sessioner: [], partner: [], handlingar: [], startjournal: [], k01: 'klar', k01v: V1, k01versioner: [V1], utanKandidater: false,
  medd: [], pausad: null, projektpaus: null };
const BILDSHA = '8'.repeat(64);
// meddelandebussen i ägarens vy (dashboard/samverkan.py lage): agentens text döljs före första valet
const STEGN = ['sparat', 'koat', 'mottaget', 'besvarat'];
function meddelandeVy() {
  return { tid: new Date().toISOString(), korning: S.korning.id, blind: S.blind, oppna: S.medd.filter((m) => m.agent && !m.beslut).map((m) => m.id), mandat: [], pausade: [],
    styrning: { projekt: S.projektpaus, sessioner: {} }, syften: {}, lagen: {},
    meddelanden: S.medd.map((m) => ({ ...m, lage_text: m.lage, handelser: STEGN.slice(0, STEGN.indexOf(m.lage) + 1).map((l) => ({ tid: T(5), lage: l })),
      ...(S.blind && m.agent ? { text: 'visas efter ditt första val i körningen', belagg: [], dolt: true } : {}) })) };
}
function nyVersion(v) { S.k01v = v; S.k01versioner.push(v); }
// de bevarade versionerna ägaren får se (arbetsyta.synliga_versioner): före första valet bara den aktuella
const synligaVersioner = () => (S.blind ? [S.k01v] : S.k01versioner).map((v) => v.slice(0, 12));
function besvara(m, text) { Object.assign(m, { lage: 'svarat', slut: new Date().toISOString(), svar: { ...S.partner[0].svar, text } }); }
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
  if (S.utanKandidater) return [];
  return [
    { id: 'k01', etikett: 'Förslag A', status: S.k01, statustext: { klar: 'klar, väntar på ditt val', vald: 'vald', under_arbete: 'byggs om' }[S.k01] || S.k01,
      version: S.k01v.slice(0, 12), version_hel: S.k01v, fotograferad: S.k01v,
      preview: { url: `/visa/${SLUG}/k01`, finns: true, byggd: S.k01Byggd || T(20) },
      snapshot: { 390: `kunder/${SLUG}/kandidater/k01/bilder/390-forsta.png`, 1440: `kunder/${SLUG}/kandidater/k01/bilder/1440-forsta.png`, version: S.k01v.slice(0, 12), tid: T(21),
        sha: { 390: '9'.repeat(64), 1440: BILDSHA } },
      versioner: synligaVersioner() },
    { id: 'k02', etikett: 'Förslag B', status: 'skapas', statustext: 'skapas', version: null, version_hel: null, fotograferad: null,
      preview: { url: `/visa/${SLUG}/k02`, finns: false, byggd: null }, snapshot: { 390: null, 1440: null, version: null, tid: null }, versioner: [] },
  ];
}
// Förslagen (förr vyn Prototyp): kandidatvyns data som server.kandidatvy ger den, före ditt första val (domd: false)
const bilder_ = (kid) => Object.fromEntries(['390-forsta', '1440-forsta', '390-hela', '1440-hela'].map((b) => [b, `kunder/${SLUG}/kandidater/${kid}/bilder/${b}.png`]));
const prototypData = () => ({ slug: SLUG, kandidatflode: true, kandidatlage: 'skiss', tider: {}, steg: 'klar_for_bedomning', fas: S.forslagFas || 'skiss', lage: 'ny',
  startad: T(-60), klar: T(-30), fel: null, skal: null, domd: false, avbruten: false, antal: 3, forbattring_agaren: [], jamforelse: null, redovisning_md: null,
  forskning_md: null, domar: [], godkand: null, godkand_kandidat: null,
  kandidater: [
    { id: 'k01', etikett: 'Förslag A', status: S.forslagK01 || 'klar', statustext: S.forslagK01 === 'forfinad' ? 'förfinad' : 'klar', version: S.k01v, bygd: true,
      undersidor: ['/om/'], bilder: bilder_('k01'), referensjamforelse: { egen: true }, redovisning: [], brister: [], design_fel: [] },
    { id: 'k02', etikett: 'Förslag B', status: 'klar', statustext: 'klar', version: V2, bygd: false, bilder: bilder_('k02'), referensjamforelse: { egen: true },
      redovisning: [], brister: [], design_fel: [] },
    { id: 'k03', etikett: 'Förslag C', status: 'fel', statustext: 'föll', skal: 'bygget föll i varv 2', bilder: {} }] });
function preview(kand) {  // som arbetsyta.preview(): arbetsversion, bevarad ögonblicksbild, märkta för sig
  const ut = [];
  for (const k of kand) {
    const osaker = ['fel', 'under_arbete', 'ofullstandig'].includes(k.status);  // K6: bygget kan vara äldre än arbetet
    if (k.preview.finns) ut.push({ typ: 'arbetsversion', kalla: 'kandidat', kandidat: k.id, url: k.preview.url, byggd: k.preview.byggd, osaker,
      etikett: `${k.etikett}, arbetsversion byggd ${k.preview.byggd}${osaker ? '; kandidaten byggs om eller senaste bygget föll, så den kan vara äldre' : ''}` });
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
  // före första valet döljer läget rollen (roll_dold); provet låter rollnamnet stå kvar, så att vyn inte får lita på att servern tömt det
  const kand = kandidater(), p = partnerLage(false), sess = [p.session, ...S.sessioner.map((x) => ({ ...x, roll_dold: S.blind,
    styrning: x.roll === 'skapa-k01' && !x.slut ? { lopare: true, lever: true, blind: false, lage: S.pausad ? 'pausad' : 'arbetar', sedan: T(6), verktyg_kvar: [],
      paus: S.pausad ? { omfattning: 'session', begard: T(6) } : null, kan_meddelas: true, kan_pausas: !S.pausad } : { lopare: false } }))];
  const steg = STEGNAMN.map((namn, i) => ({ nr: i + 1, namn, status: S.stegstatus[i], underlag: [], kontroller: [], beslut: [], brister: [], nasta: '',
    utfall: i === 0 ? [{ text: 'VERKSAMHET.json, verksamhetens uppgifter (testdata)', lank: `/fil/underlag/${SLUG}/VERKSAMHET.json`, tid: T(-60) }] : [] }));
  const moment = steg.find((s) => ['pågår', 'väntar på ägaren'].includes(s.status)) || steg.filter((s) => !['inte påbörjat', 'inte observerat'].includes(s.status)).at(-1);
  return { schema: 'arbetsyta/1', tid: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'), slug: SLUG, ofullstandig: [],
    projekt: { slug: SLUG, namn: NAMN, testdata: true }, blind: S.blind, ab_dold: false, steg, startmiljo: null, handlingar: S.handlingar,
    besked: { version: 'syntetisk-version', tid: T(0), filer: [], tillstand: ['Sessionen avslutades normalt', 'Tekniska kontroller', 'Designgranskning', 'Ägarens godkännande',
      'Leverans inom angiven omfattning'].map((namn) => ({ namn, status: 'ej bedömt', varde: null, text: 'Syntetiskt besked för provet.' })) },
    moment: { nr: moment.nr, namn: moment.namn, status: moment.status }, korning: S.korning, kandidater: kand, helbygge: [], partner: p, sessioner: sess,
    startjournal: S.startjournal, roller: roller(sess, S.korning, p.lage), overlamningar: [], preview: preview(kand), redigeringar: S.redigeringar || [],
    observation: { senast_last: new Date().toISOString(), ofullstandig: [] }, version: String(++versionsnr).padStart(16, '0'),
    samverkan: { antal: S.medd.length, oppna: S.medd.filter((m) => m.agent && !m.beslut).length, nyckel: S.medd.map((m) => m.id + m.lage + (m.beslut ? 'b' : '')).join(), projektpaus: S.projektpaus, mandat: 0 } };
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
  const versioner = synligaVersioner(), nu = S.k01v.slice(0, 12), mot = q.get('mot') || nu;
  if (!versioner.includes(mot)) return [404, { fel: 'versionen finns inte bland de bevarade versionerna du kan se' }];  // som arbetsyta.kod()
  const ut = { kandidat: 'k01', arbetsversion: `kunder/${SLUG}/kandidater/k01/sajt (som det står nu)`, mot, versioner, fotograferad: nu, blind: S.blind, filer: lista };
  const fil = q.get('fil');
  if (fil) {
    if (!KOD[fil]) return [404, { fel: 'filen hör inte till kandidatens kod' }];
    ut.fil = { fil, text: KOD[fil], finns: true, diff: fil === 'kod/index.astro' ? [`--- version ${mot}`, ...DIFF.slice(1)] : fil.endsWith('Hero.astro') ? KOD[fil].trimEnd().split('\n').map((r) => '+' + r) : [],
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
      const m = { id: body.meddelande_id, tid: new Date().toISOString(), avsikt: body.avsikt, kontext: body.kontext, text: body.text, lage: body.vanta ? 'vantande' : 'arbetar', svar: null, fel: null, overlamning: null, slut: null };
      const forra = S.partner.find((x) => x.id === m.id);  // samma meddelande-id ger samma post (partner.skicka)
      if (forra) return json({ ...forra, upprepat: true });
      S.partner.push(m);
      return json(m);
    }
    if (vag === `/api/arbetsyta/${SLUG}/meddelande`) {
      const forra = S.medd.find((m) => m.id === body.id);
      if (forra) return json({ ...forra, upprepat: true });
      const m = { id: body.id, tid: new Date().toISOString(), avsandare: { typ: 'agare', klient: 'arbetsytan' }, mottagare: body.mottagare, syfte: body.syfte,
        syfte_text: body.syfte === 'fraga' ? 'Fråga' : 'Ändringsinstruktion', text: body.text, kandidat: body.kandidat, version: body.version, korning: body.korning, agent: false, lage: 'sparat' };
      S.medd.push(m);
      return json({ ...m, upprepat: false });
    }
    const mb = vag.match(new RegExp(`^/api/arbetsyta/${SLUG}/meddelande/([A-Za-z0-9_-]+)/beslut$`));
    if (mb) { const m = S.medd.find((x) => x.id === mb[1]); if (!m) return json({ fel: 'inget sådant meddelande' }, 400); m.beslut = { val: body.val, tid: new Date().toISOString() }; return json(m); }
    if (vag === `/api/arbetsyta/${SLUG}/paus`) {
      if (body.omfattning === 'session') S.pausad = body.aterta ? null : body.session_id;
      if (body.omfattning === 'projekt') S.projektpaus = body.aterta ? null : { lage: 'pausad', lage_text: 'pausad: inga sessioner arbetar och ingen ny startar', begard: T(7) };
      return json(meddelandeVy());
    }
    if (vag === `/api/arbetsyta/${SLUG}/beslut`) return json({ ok: true, dom: { tid: new Date().toISOString(), beslut: body.beslut } });
    if (vag === `/api/arbetsyta/${SLUG}/partner/vantande`) { S.partner = S.partner.filter((x) => !(x.id === body.meddelande_id && x.lage === 'vantande')); return json({ borttagen: body.meddelande_id }); }
    if (vag === `/api/arbetsyta/${SLUG}/redigera`) return json({ id: body.redigering_id, status: 'koad', fil: 'src/pages/index.astro', gammal: body.gammal, ny: body.ny, upprepat: false });
    if (vag === `/api/arbetsyta/${SLUG}/andring`) {
      if (++andringAnrop === 1) return json({ fel: `kandidaten har en ny version sedan du skrev ändringen (din ${String(body.version).slice(0, 12)}, nu 0a1b2c3d4e5f); stäm av mot den aktuella.`, slag: 'Inaktuell' }, 409);
      const upprepat = andringar.has(body.andring_id); andringar.add(body.andring_id);  // samma id ger samma rad (skicka_andring)
      if (!upprepat && S.k01 === 'klar') S.k01 = 'vald';  // kandidater.efter_beslut: efter den första raden är kandidaten vald
      return json({ ok: true, upprepat });
    }
    return json({ fel: 'finns inte' }, 404);
  }
  if (filer.has(vag)) { const f = filer.get(vag); res.writeHead(200, { 'Content-Type': f.typ }); return res.end(f.data); }
  if (vag === '/api/desktop/lage') return json({ kontrakt: 'desktop/1', session: false });  // webbläsaren, inte Nortropic.app: portalens ram ritas ändå
  // portalens kundlista (desktop.oversikt): kunden i skapandeflödet, så att stegraden, kundvalet och studion ritas
  if (vag === '/api/desktop/oversikt') return json({ kunder: [{ slug: SLUG, namn: NAMN, test: true, projekt: true, arenden: [], vy: `#/studio/${SLUG}`, senast: T(10) },
    { slug: 'prov-andra', namn: 'Provföretaget Två', test: true, projekt: true, arenden: [], vy: '#/studio/prov-andra', senast: T(-600) }], uppmarksamhet: [] });
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
  if (vag === `/api/arbetsyta/${SLUG}/partner/strom`) {  // partnerns ström (partner.delvis): provet skriver delhändelserna och slutet
    const id = url.searchParams.get('id');
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-store' });
    res.write('retry: 500\n\n');
    res.write(`event: borjan\ndata: ${JSON.stringify({ id })}\n\n`);
    partnerStrommar.set(id, res); res.on('close', () => { if (partnerStrommar.get(id) === res) partnerStrommar.delete(id); });
    return;
  }
  if (vag === `/api/arbetsyta/${SLUG}/redigera/karta`) {  // direktredigering.karta: en text som står på två ställen kan inte ändras direkt
    const t = url.searchParams.get('text');
    return json(t === 'Boka tid' ? { ok: false, skal: 'texten står på 2 ställen (src/pages/index.astro); välj en mer avgränsad text eller gör ett uppdrag', alternativ: 'uppdrag' }
      : { ok: true, fil: 'src/pages/index.astro', kontext: 'mall', text: t });
  }
  if (vag === `/api/arbetsyta/${SLUG}/partner`) return json(partnerLage(true));
  if (vag === `/api/arbetsyta/${SLUG}/meddelanden`) return json(meddelandeVy());
  if (vag === `/api/arbetsyta/${SLUG}/kod`) { const [k, d] = kod(url.searchParams); return json(d, k); }
  if (vag === `/api/arbetsyta/${SLUG}/logg`) return json(LOGG());
  if (vag === '/api/flode') return json({ slugar: [SLUG], pilot: [], kedjan: { steg: [{ steg: 'Kundunderlaget', vem: 'Kundstart samlar underlaget; du godkänner det.' },
    { steg: 'Prototypen', vem: 'Ateljén skapar kandidater med neutrala etiketter; granskarna dömer var för sig.' }] } });
  if (vag === `/api/prototyp/${SLUG}`) return S.utanPrototyp ? json({ fel: 'ingen prototyp för bygget' }, 404) : json(prototypData());
  if (vag === '/api/oversikt') return json({ byggen: [], backlog_vilande: 3, intag_pagar: 1, prospekt_vantar: 0 });
  if (vag === '/api/leverans') return json({ schema: 1, besked: '1 kunder; 1 äldre Vercel-projekt kvar', bestandsfel: null,  // formen ur migreringslage.oversikt()
    kunder: [{ slug: SLUG, besked: 'förberedd; nästa: måltestad', migrerad: false, i_drift: false,
               steg: { forberedd: 'ja', maltestad: 'nej', trafik_flyttad: 'nej', data_avstamd: 'inte_tillampligt', legacy_avvecklad: 'inte_tillampligt' } }],
    legacy_utan_kund: [{ projekt: 'gammal-provsajt', adress: 'gammal-provsajt.vercel.app', status: 'kvar', data: null }] });
  if (vag === '/api/underhall') return json({ senast: { start: T(90), slut: T(80), antal: { uppdaterad: 2, avvisad: 0, behallen: 1 } }, andringar: [], intervall_dagar: 1, pagar: null, md: '' });
  if (vag === '/api/bevakning') return json({ senast: { start: T(30), slut: T(29), automatisk: true, utfall: 'delvis', sen_timmar: 0.2 }, nasta: T(-600), tidszon: 'Europe/Stockholm',
    klockslag: '07:00', aktiv: true, forbattringar: { bevakade: 3, bedomda: 1, provade: 0, inforda: 0, verifierade: 0 },
    beslut: [{ id: 'besokarprov', fraga: 'När prövar vi en sajt med verkliga besökare?', lucka: 'ingen verklig användarobservation' }],
    luckor: [{ id: 'besokarprov', fraga: 'När prövar vi en sajt med verkliga besökare?', lucka: 'ingen verklig användarobservation', ansvar: 'skapandeflödet',
      post: 'B-prov', nasta_atgard: 'Codex prövar metoden månadsvis', forutsattning: 'ett skarpt uppdrag och 3–5 besökare' }],
    fragor: [{ id: 'matinstrumenten', utfall: 'fynd', senast_lyckad: T(30), nasta: T(-600), kontroll: ['kalla', 'underhall'], intervall: 'dag', problem: [] },
      { id: 'modeller', utfall: 'misslyckad', senast_lyckad: null, nasta: T(-600), kontroll: ['kalla'], intervall: 'dag', problem: ['källan föll'] }],
    codex: { aktiv: true, dags: ['ux-metod'], korningar: [{ tid: T(40), fraga: 'evals-och-domare', tokens: 59720 }] },
    forbrukning: { sessioner: 3, listpris_usd: 12.06, tokens_ut: 24023, codex: { granskningar: 1, tokens: 59720 } },
    tackning: { ux: { namn: 'UX-forskning, informationsarkitektur, innehåll och konvertering', fragor: 1, luckor: ['ingen verklig användarobservation'], lage: 'inaktuell' },
      frontend: { namn: 'Frontend, komponenter, ramverk, prestanda och testning', fragor: 2, luckor: [], lage: 'bevakad' } },
    dag: { besked: '1 nya fynd', handlingsbart: [{ fraga: 'matinstrumenten', typ: 'beroende_avvisad', text: 'axe-core: avvisad 4.13.0 → 4.14.0', belagg: 'underlag/startkontroll/UNDERHALL.md' }],
      kontroller_som_inte_lyckades: [{ id: 'modeller', utfall: 'misslyckad', problem: ['Claude platform release notes: senaste hämtningen föll'] }] } });
  if (vag.startsWith('/api/')) return json({});
  if (vag === `/visa/${SLUG}/k01` && S.bryggaPreview) { res.writeHead(302, { Location: forhandOrigin + '/' }); return res.end(); }  // kandidatens egen lokala adress, som visa_kandidat
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
// kandidatens förhandsvisning på ett eget ursprung, med arbetsytans brygga inlagd som prova.Server(brygga=…) lägger in den
const partnerStrommar = new Map();
const bryggkod = (await readFile(resolve(root, 'dashboard/forhandsbrygga.js'), 'utf8')).replace("'__NWP_URSPRUNG__'", JSON.stringify(origin));
const forhand = createServer((req, res) => {
  if (new URL(req.url, 'http://f').pathname === '/__nortropic/forhandsbrygga.js') { res.writeHead(200, { 'Content-Type': TYP.js }); return res.end(bryggkod); }
  res.writeHead(200, { 'Content-Type': TYP.html });
  res.end('<!doctype html><html lang="sv"><head><meta charset="utf-8"><title>Förslag A</title></head><body><h1>Surdeg som får ta tid</h1><p id="ingress">Vi bakar varje natt.</p>'
    + '<a href="/boka/">Boka tid</a> <a href="/kontakt/">Boka tid</a><section><h2>Bröd</h2><p>Surdeg <em>och</em> råg</p></section>'
    + '<script src="/__nortropic/forhandsbrygga.js" defer></script></body></html>');
});
await new Promise((r) => forhand.listen(0, '127.0.0.1', r));
const forhandOrigin = `http://127.0.0.1:${forhand.address().port}`;
assert(![4771, 4781].includes(srv.address().port), 'provet får inte använda dashboardens portar');
function skickaLage() {
  assert(strommar.size >= 1, 'en öppen ström behövs för att skicka ett nytt läge');
  const d = `event: lage\ndata: ${JSON.stringify(lage())}\n\n`;
  for (const r of strommar) r.write(d);
}
async function vantaPa(villkor, text, ms = 5000) { const slut = Date.now() + ms; while (!villkor()) { assert(Date.now() < slut, text); await sov(20); } }
const startPosts = () => posts.filter((p) => p.vag === `/api/flode/${SLUG}/start`).map((p) => p.body);

let browser;
const sammanfattning = { bredder: [320, 390, 768, 1024, 1280, 1440, 1672] };
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

  // 1. Nyckeln ur adressen, kunden, portalens stegrad och studions flikar; den gamla arbetsvyn finns inte (ägarens besked 2026-10-11)
  const flik = async (namn) => { const f = page.locator(`[data-st-flik="${namn}"]`); await f.click(); await page.locator(`#st-flik-${namn}`).waitFor(); };
  const omradeLank = (namn) => page.locator('.pt-stegrad a').filter({ hasText: namn });
  await page.goto(`${origin}/#nyckel=${NYCKEL}&till=arbetsyta/${SLUG}`);
  await page.locator('#st-rot .st-riktning').first().waitFor();
  await page.locator('#ay-anslutning[data-lage="ansluten"]').waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/studio/${SLUG}`, 'efter laddningen ska adressen vara studions (arbetsytans adress leder dit), utan nyckeln');
  assert(!page.url().includes(NYCKEL), 'nyckeln får aldrig stanna i adressen');
  assert.equal(await page.evaluate(() => localStorage.getItem('nwp-dashboardnyckel')), NYCKEL, 'nyckeln ska sparas i webbläsaren');
  assert.deepEqual(await page.evaluate(() => [typeof kundstartvy, typeof kirurgForbattring, typeof arbetsytavy, typeof NortropicStudio]), ['function', 'function', 'function', 'object'],
    'dashboardens separata skript ska laddas som riktig JavaScript');
  assert.equal(await page.locator('.ay-huvud, .ay-flikrad, .ay-meny, #ay-ytan, .ay-omraden').count(), 0, 'den gamla arbetsvyns huvud, flikrad, menyer och yta finns inte');
  assert.equal((await page.locator('#pt-lage #ay-kund option:checked').textContent()).trim(), `${NAMN} (testdata)`, 'stegradens läge ska visa kundens namn, märkt som testdata');
  assert(await page.locator('.pt-steg .pt-test').filter({ hasText: 'Testkund' }).isVisible(), 'stegraden ska märka testkunden');
  assert.equal((await page.locator('.pt-stegrad a[aria-current="step"]').textContent()).trim(), '4Designstudio', 'stegraden ska stå på Designstudio');
  assert.deepEqual(await page.locator('.pt-stegrad a').evaluateAll((a) => a.map((x) => x.getAttribute('href')).filter((h) => h.startsWith('#/arbetsyta') || h.startsWith('#/studio'))),
    [`#/studio/${SLUG}`, `#/arbetsyta/${SLUG}/forslag`, `#/arbetsyta/${SLUG}/flode`, `#/arbetsyta/${SLUG}/kod`], 'Designstudio, Förslag, Bygge och Granskning står i stegraden');
  assert.deepEqual(await page.getByRole('tablist', { name: 'Ändra, samtal och arbete' }).getByRole('tab').allTextContents().then((l) => l.map((x) => x.trim())), ['Ändra', 'Samtal', 'Arbete'],
    'studions panel har flikarna Ändra, Samtal och Arbete');
  assert.equal(posts.length, 0, 'att läsa studion skickar inget');
  // partnerns användningsrad: cache-siffrorna och listpriset som Claude Code rapporterar det, aldrig som en faktura
  await flik('samtal');
  const anv = page.locator('#ay-samtal .ay-msg.partnern .meta').first();
  await anv.waitFor();
  const anvText = (await anv.textContent()).replace(/\s+/g, ' ');
  assert.match(anvText, /1520 in, 8000 ur cache, 1200 till cache, 214 ut tokens/, 'partnerns användningsrad ska visa cache-siffrorna');
  assert.match(anvText, /listpris enligt Claude Code 0\.12 USD, inte fakturerat/, 'listpriset ska stå som Claude Codes siffra, inte fakturerat');
  assert.equal(await page.locator('#ay-partnerchip .ay-lage').getAttribute('data-lage'), 'avslutad', 'partnerns svarade tur ska stå som avslutad');

  // 4. Läget står i text, aldrig bara i färg (sessionerna under Arbete)
  await flik('arbete');
  sammanfattning.lagen_med_text = { studio: await statustexter('Designstudio') };

  // 5. Förhandsvisningen i studions duk: sandlåda utan toppnavigering och popup-fönster, ingen referent; bredden byter bara
  // ramens bredd och skala, aldrig sidan (sajtens egna brytpunkter svarar på ramens bredd)
  const ram_ = page.locator('#st-duk iframe');
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
  await page.locator('#st-verktyg').getByRole('button', { name: 'Mobil', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#st-duk iframe')?.style.width === '390px');
  assert.equal(await page.locator('#st-duk iframe').getAttribute('src'), src, 'Mobil ska byta ramens bredd, inte förhandsvisningens adress');
  assert.equal(await page.locator('#st-verktyg').getByRole('button', { name: 'Mobil', exact: true }).getAttribute('aria-pressed'), 'true');
  await ram();
  await page.locator('#st-verktyg').getByRole('button', { name: 'Dator', exact: true }).click();
  await page.waitForFunction(() => document.querySelector('#st-duk iframe')?.style.width === '1280px');
  await sov(150);
  assert.equal(forhandsvisningar - laddningarFore, 0, 'bredderna byter ramen, de laddar inte om förhandsvisningen');
  assert.match(await page.locator('#st-dukrad').textContent(), /Förslag A, version .* · 1280 px/, 'raden under duken säger version och bredd');
  sammanfattning.forhandsvisning = { sandbox: sandbox.join(' '), referrerpolicy: 'no-referrer', omladdningar_vid_breddbyte: forhandsvisningar - laddningarFore };

  // 12. Rörelsen följer prefers-reduced-motion
  const animation = () => page.locator('.ay-lage[data-lage="aktiv"] svg').first().evaluate((e) => getComputedStyle(e).animationName);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  assert.equal(await animation(), 'ay-andas', 'utan önskemål ska ett arbetande läge andas (provet ska kunna bli rött)');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  assert.equal(await animation(), 'none', 'med prefers-reduced-motion: reduce får inget läge animeras');
  await page.emulateMedia({ reducedMotion: null });

  // 2. Inget sidledes spill; studions tre delar står bredvid varandra i bred vy och under varandra i smal, och panelens flikar
  // visar en sak åt gången (förr arbetsytans områden Samtal, Resultat och Sessioner)
  const delarna = () => page.evaluate(() => ['st-vanster', 'st-mitten', 'st-hoger'].map((k) => {
    const el = document.querySelector('#st-rot > .' + k); const r = el?.getBoundingClientRect();
    return el && getComputedStyle(el).display !== 'none' && r.width > 0 ? { k, x: Math.round(r.left), y: Math.round(r.top) } : null; }).filter(Boolean));
  sammanfattning.spill = { studio: {}, byggflode: {}, kod: {} };
  for (const w of sammanfattning.bredder) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    const s = await spill(); sammanfattning.spill.studio[w] = s.bredd - s.fonster;
    assert(s.bredd <= s.fonster, `Designstudio: sidledes spill vid ${w} px (${s.bredd} > ${s.fonster})`);
    const d = await delarna();
    assert.deepEqual(d.map((x) => x.k), ['st-vanster', 'st-mitten', 'st-hoger'], `vid ${w} px ska riktningarna, duken och panelen synas`);
    if (w < 960) assert(d[0].y < d[1].y && d[1].y < d[2].y, `vid ${w} px står delarna under varandra: ${JSON.stringify(d)}`);
    else assert(d[0].x < d[1].x && d[1].x < d[2].x, `vid ${w} px står delarna bredvid varandra: ${JSON.stringify(d)}`);
    for (const f of ['andra', 'samtal', 'arbete']) {
      await flik(f); await ram();
      const s2 = await spill();
      assert(s2.bredd <= s2.fonster, `Designstudio, fliken ${f}: sidledes spill vid ${w} px (${s2.bredd} > ${s2.fonster})`);
      assert.deepEqual(await page.evaluate(() => ['andra', 'samtal', 'arbete'].filter((x) => !document.getElementById('st-flik-' + x).hidden)), [f], `vid ${w} px visar panelen en flik åt gången`);
    }
    // klippt inuti panelerna, inte spill på sidan: Kontrollers knappar och verktygsraden
    const klippt = await page.evaluate(() => {
      const ut = [];
      const k = document.getElementById('ay-ktl')?.closest('.ay-panel');
      if (!k) ut.push('Kontroller saknas');
      else for (const b of k.querySelectorAll('.ay-knapp')) {
        const r = b.getBoundingClientRect(), p = k.getBoundingClientRect();
        if (r.right > p.right + 0.5 || b.scrollWidth > b.clientWidth + 0.5) ut.push('knappen ' + b.textContent.trim());
      }
      for (const b of document.querySelectorAll('#st-verktyg button')) { const r = b.getBoundingClientRect(); if (r.right > innerWidth + 0.5 || r.left < -0.5) ut.push('verktyget ' + b.textContent.trim()); }
      return ut;
    });
    assert.deepEqual(klippt, [], `Designstudio vid ${w} px: klippt innehåll i panelerna`);
    if ([390, 1440].includes(w)) await bild('studio', w);
  }
  sammanfattning.studions_delar_i_alla_bredder = true;

  // 3. axe i studion (bred och smal), varje flik
  for (const w of [1440, 390]) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    for (const f of ['andra', 'samtal', 'arbete']) { await flik(f); await axeKor(`Designstudio ${w}, ${f}`); }
  }
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  // panelerna: avdelarna har sitt värde och flyttas med piltangenterna; en hopfälld panel visas igen från verktygsraden
  const delare = page.locator('[data-st-delare="hoger"]');
  const fore_bredd = Number(await delare.getAttribute('aria-valuenow'));
  await delare.focus(); await page.keyboard.press('ArrowLeft');
  assert.equal(Number(await delare.getAttribute('aria-valuenow')), fore_bredd + 24, 'pil vänster breddar panelen till höger med 24 px');
  await page.locator('[data-st-fall="vanster"]').click();
  assert(await page.locator('#st-rot > .st-vanster').isHidden(), 'riktningarna fälls ihop');
  await page.locator('[data-st-visa-panel="vanster"]').click();
  await page.locator('#st-rot > .st-vanster').waitFor();
  sammanfattning.panelerna = { avdelare_tangentbord: true, fall_och_visa: true };

  // 11. Byggflödet: nio steg, blindningen, systemförbättringen för sig; delarna i portalens navigering
  await omradeLank('Bygge').click();
  await page.locator('ol.ay-stegrad').waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/arbetsyta/${SLUG}/flode`);
  assert.equal((await page.locator('.pt-stegrad a[aria-current="step"]').textContent()).trim(), '7Bygge', 'stegraden ska stå på Bygge');
  assert.deepEqual(await page.locator('ol.ay-stegrad > li .namn').allTextContents(), STEGNAMN, 'stegraden ska visa README:s nio steg');
  assert.equal(await page.locator('ol.ay-stegrad > li[data-pagar]').count(), 1, 'ett steg pågår');
  assert(await page.locator('.ay-grupper .ay-notis').filter({ hasText: 'Ditt första val i körningen är inte gjort' }).isVisible(), 'blindningen ska stå i Byggflöde');
  const kortnamn = await page.locator('.ay-grupper .ay-session .namn').allTextContents();
  assert(kortnamn.length >= 2 && kortnamn.every((t) => /^(Utförare|Granskare|Nortropic-partnern)\b/.test(t.trim())), `Byggflödets sessionskort ska visa ansvaret, inte rollen, före första valet: ${kortnamn.join(' | ')}`);
  const system = page.getByRole('region', { name: 'Bevakning och systemförbättring, skilt från kundproduktionen' });
  assert.deepEqual(await system.getByRole('link').evaluateAll((a) => a.map((x) => [x.textContent.trim(), x.getAttribute('href')])).then((l) => l.filter(([t]) => ['Kirurgen och förbättringsloopen', 'Backlog'].includes(t))),
    [['Kirurgen och förbättringsloopen', '#/kirurgen'], ['Backlog', '#/backlog']], 'Kirurgen och Backlog ska nås från systemförbättringen');
  await system.locator('.ay-bevakning, .ay-notis, .svag').first().waitFor({ timeout: 10000 });  // bevakningens läge ritas, eller varför det inte gick
  assert.equal(await system.locator('.ay-stegrad, .ay-grupp, a[href^="#/flode"], a[href^="#/prototyp"], a[href^="#/kundstart"]').count(), 0,
    'systemförbättringen ska stå skild från kundproduktionen');
  // allt i den nya vyn (ägarens besked 2026-10-11): ingen klassisk vy och ingen gammal arbetsvy; delarna står i portalens
  // navigering, kundproduktionen skild från systemförbättringen, och en del ritas i ramens yta
  assert.equal(await page.locator('header.topp').count(), 0, 'den klassiska topplisten ska vara borta');
  assert.equal(await page.getByRole('link', { name: 'Klassisk vy' }).count(), 0, 'knappen Klassisk vy ska vara borta');
  const nav = page.locator('#pt-nav');
  const grupper = await nav.locator('details.pt-delar').evaluateAll((ds) => ds.map((d) => [d.querySelector('summary span').textContent.trim(),
    [...d.querySelectorAll('.pt-dellista a')].map((a) => a.querySelector('span').textContent.trim())]));
  const grupp = (text) => (grupper.find(([, l]) => l.includes(text)) || [])[0];
  assert.equal(grupp('Flöde'), undefined, 'Flöde är en del av Bygge, inte en egen post i navigeringen');
  assert.equal(grupp('Prototyp'), undefined, 'Prototyp är kundens Förslag, inte en egen post i navigeringen');
  for (const [text, g] of [['Byggen och dina domar', 'Kundproduktion'], ['Kundstart', 'Kundproduktion'], ['Jämförelser', 'Kundproduktion'], ['Leverans och förvaltning', 'Kundproduktion'],
    ['Prospekt', 'Kundproduktion'], ['Starta', 'Kundproduktion'], ['Underhåll och verktygslådan', 'Systemförbättring'], ['Kirurgen', 'Systemförbättring'], ['Backlog', 'Systemförbättring'],
    ['Kalibrering', 'Systemförbättring'], ['Lärdomar', 'Systemförbättring'], ['Designprov', 'Systemförbättring']])
    assert.equal(grupp(text), g, `navigeringen ska ha ${text} under ${g}`);
  assert.equal(await nav.getByRole('link', { name: 'Dokumentation och rapporter' }).count(), 1, 'Dokumentation och rapporter ska stå i navigeringen');
  assert.equal(await nav.getByRole('link', { name: 'Designstudio' }).getAttribute('href'), `#/studio/${SLUG}`, 'Designstudio leder till den senaste kunden');
  // grupperna går att använda i varje bredd: varje länk syns och går att klicka när gruppen är öppen
  for (const w of [1440, 390, 320]) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    for (const namn of ['Kundproduktion', 'Systemförbättring']) {
      const d = nav.locator('details.pt-delar').filter({ has: page.locator('summary', { hasText: namn }) });
      if (!(await d.evaluate((x) => x.open))) await d.locator('summary').click();
      const traffar = [];
      for (const a of await d.locator('.pt-dellista a').all()) {
        await a.scrollIntoViewIfNeeded();
        traffar.push(await a.evaluate((x) => { const r = x.getBoundingClientRect(), e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
          return [x.textContent.trim(), !!e && (e === x || x.contains(e)) && r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight]; }));
      }
      assert.deepEqual(traffar.filter(([, ok]) => !ok).map(([t]) => t), [], `${namn} vid ${w} px: varje länk ska synas och gå att klicka`);
    }
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `navigeringen spiller i sidled vid ${w} px`);
  }
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await page.evaluate(() => scrollTo(0, 0));
  await nav.locator('.pt-dellista a').filter({ hasText: 'Byggen och dina domar' }).click();
  await page.locator('#vy h1').filter({ hasText: 'Byggen och dina domar' }).waitFor();
  assert.equal(await page.evaluate(() => location.hash), '#/oversikt', 'delen behåller sin adress');
  assert.equal(await page.locator('.ay #vy.ay-sektion').count(), 1, 'delen ritas i ramens yta');
  assert.equal(await nav.locator('.pt-dellista a[aria-current="page"]').textContent().then((x) => x.trim()), 'Byggen och dina domar', 'navigeringen visar var du är');
  await page.waitForFunction(() => document.activeElement?.tagName === 'H1');
  assert.equal(await page.evaluate(() => document.activeElement?.tagName + ':' + document.activeElement?.textContent), 'H1:Byggen och dina domar', 'efter ett val i navigeringen har delens rubrik fokus');
  // räknarna ur översikten står i navigeringen och på gruppens rubrik, också i en annan del
  await page.locator('#pt-summa-system:not([hidden])').waitFor();
  assert.deepEqual([await page.locator('#n-kirurg').textContent(), await page.locator('#n-backlog').textContent(), await page.locator('#pt-summa-system').textContent()],
    ['1 pågår', '3', '4'], 'räknarna i Systemförbättring');
  // Leverans och förvaltning (M18): migreringsläget per kund och de äldre Vercel-sajterna, ritat i ramens yta
  await page.evaluate(() => { location.hash = '#/leverans'; });
  await page.locator('#vy h1').filter({ hasText: 'Leverans och förvaltning' }).waitFor();
  await page.locator('#leverans h2').filter({ hasText: 'Äldre sajter på Vercel' }).waitFor();
  assert.equal(await page.locator('#leverans .meddelande.fel').count(), 0, 'migreringsläget ska gå att läsa');
  assert.equal(await page.locator('#leverans').getByText('migrerad:', { exact: false }).count(), 0, 'ingen provkund står som migrerad');
  assert.deepEqual(await page.locator('#leverans tbody tr').first().locator('td').allTextContents(),
    ['ja', 'nej', 'nej', 'inte tillämpligt', 'inte tillämpligt', 'förberedd; nästa: måltestad'], 'fem skilda besked och läget');
  assert.equal(await page.locator('#leverans tbody tr').last().locator('td').last().textContent(), 'kvar på Vercel');
  await page.evaluate(() => { location.hash = '#/underhall'; });
  await page.locator('#vy h1').filter({ hasText: 'Underhåll och verktygslådan' }).waitFor();
  await page.locator('#verktygslada .chip').filter({ hasText: '2 uppdaterade' }).waitFor();
  assert.equal(await page.locator('#pt-summa-system').textContent(), '4', 'räknarna står kvar efter bytet');
  await axeKor('Underhåll 1440');
  // i smal bredd: navigeringen står överst, och varje del nås utan sidledes rullning
  for (const w of [390, 320]) {
    await page.setViewportSize({ width: w, height: 800 }); await ram();
    await page.evaluate(() => scrollTo(0, 0)); await ram();
    const doc = await nav.getByRole('link', { name: /^Dokumentation/ }).boundingBox();
    assert(doc && doc.x >= 0 && doc.x + doc.width <= w, `Dokumentation ska synas i navigeringen vid ${w} px: ${JSON.stringify(doc)}`);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `spill i delen vid ${w} px`);
  }
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await page.evaluate((s) => { location.hash = '#/arbetsyta/' + s + '/flode'; }, SLUG);
  await page.locator('ol.ay-stegrad').waitFor();
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  sammanfattning.lagen_med_text.byggflode = await statustexter('Byggflöde');
  await axeKor('Byggflöde 1440');
  await bild('byggflode', 1440);
  for (const w of sammanfattning.bredder) {
    await page.setViewportSize({ width: w, height: 900 }); await ram();
    const s = await spill(); sammanfattning.spill.byggflode[w] = s.bredd - s.fonster;
    assert(s.bredd <= s.fonster, `Byggflöde: sidledes spill vid ${w} px (${s.bredd} > ${s.fonster})`);
    if (w === 390) { await axeKor('Byggflöde 390'); await bild('byggflode', 390); }
  }

  // Kod och preview (stegradens Granskning)
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  await omradeLank('Granskning').click();
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
  await omradeLank('Designstudio').click();
  await page.locator('#st-rot .st-riktning').first().waitFor();
  await flik('arbete');
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
  // före första valet bär läget roll_dold: korten och meddelandena säger Utförare eller Granskare, aldrig rollnamnet
  assert.match(startText, /Granskare för Förslag A startade/, 'en ny session ska meddelas när den startar, med ansvaret i stället för rollen');
  await page.locator('#ay-roller .ay-ansvar').filter({ hasText: 'Granskning' }).locator('.ay-session .namn').filter({ hasText: 'Granskare · Förslag A' }).waitFor();
  const rollnamnen = /skaparen|granskningen|förfiningen|kritikern|panelen/;
  assert.doesNotMatch(await page.locator('#ay-roller').textContent(), rollnamnen, 'före första valet får inget kort visa rollnamnet');
  assert.doesNotMatch(await region.textContent(), rollnamnen, 'före första valet får inget meddelande visa rollnamnet');
  const skaparenA = page.locator('#ay-roller article.ay-session').filter({ has: page.locator('.namn', { hasText: 'Utförare · Förslag A' }) });
  assert.equal(await skaparenA.locator('.ay-lage').getAttribute('data-lage'), 'aktiv');
  avsluta(S.sessioner[0], 26);
  skickaLage();
  await skaparenA.locator('.ay-lage[data-lage="avslutad"]').waitFor();
  assert.equal((await skaparenA.locator('.ay-lage').textContent()).trim(), 'avslutad', 'rollkortet ska visa det nya läget i text');
  const slutText = await meddelat('Utförare för Förslag A: avslutad');
  assert(slutText.length <= 200, 'meddelandet ska vara kort');
  await sov(300);
  const fore = await page.evaluate(() => window.__meddelanden.length), textFore = await region.textContent();
  const skaparenB = page.locator('#ay-roller article.ay-session').filter({ has: page.locator('.namn', { hasText: 'Utförare · Förslag B' }) });
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

  // körningen väntar på ägaren: uppdraget erbjuds, med benämningen på det som startas (2026-10-09)
  for (const s of S.sessioner) if (s.lage !== 'avslutad') avsluta(s, 30);
  S.korning = korning('ny', START1, T(0), 'klar_for_bedomning', false);
  S.stegstatus = ['skapat', 'skapat', 'väntar på ägaren', ...Array(6).fill('inte påbörjat')];
  S.handlingar = [{ id: 'valda', text: 'Starta uppdraget: Rätta Förslag A' }];
  S.startjournal[0] = { ...S.startjournal[0], status: 'klar', slutkod: 0, process_lever: false };
  skickaLage();
  await meddelat('Körningen väntar på ditt beslut');
  await page.getByRole('button', { name: 'Starta uppdraget: Rätta Förslag A' }).waitFor();

  // 10. Samtalet: en fråga med markeringen; meddelande-id:t är en hash av innehållet och samtalets position
  const markLagret = (sida = page) => sida.evaluate((k) => JSON.parse(sessionStorage.getItem(k) || 'null'), `nwp-arbetsyta-markering:${SLUG}`);
  const galler = page.locator('#ay-markering');
  const gallerText = async () => (await galler.textContent()).replace(/\s+/g, ' ');
  const andringPosts = () => posts.filter((p) => p.vag === `/api/arbetsyta/${SLUG}/andring`).map((p) => p.body);
  const partnerPosts = () => posts.filter((p) => p.vag === `/api/arbetsyta/${SLUG}/partner`).map((p) => p.body);
  const skickaFraga = async (sida, text) => { await sida.locator('#ay-text').fill(text); await sida.locator('#ay-skriv').getByRole('button', { name: 'Skicka', exact: true }).click(); };
  const kanSkicka = (sida) => sida.waitForFunction(() => { const b = document.querySelector('#ay-skriv [data-skicka="partner"]'); return b && !b.disabled; });
  const nySida = async () => {  // en andra flik i samma webbläsare: samma nyckel (localStorage), egen sessionStorage
    const s = await ctx.newPage();
    s.on('pageerror', (e) => sidfel.push('andra fliken: ' + e.message));
    s.on('console', (m) => { if (m.type() === 'error') konsolfel.push({ text: m.text(), url: m.location()?.url || '' }); });
    await s.route((u) => u.origin !== origin, (route) => { externa.push(route.request().url()); return route.abort(); });
    await s.goto(`${origin}/#/arbetsyta/${SLUG}`);  // arbetsytans adress leder till studion
    await s.locator('[data-st-flik="samtal"]').click();
    await s.locator('#ay-skriv [data-avsikt="andring"]').waitFor();
    return s;
  };
  await flik('samtal');
  await skickaFraga(page, 'Vad saknas i första vyn för Förslag A?');
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Skickat' }).waitFor();
  let pp = partnerPosts();
  assert.equal(pp.length, 1, 'ett meddelande till partnern');
  assert.match(String(pp[0].meddelande_id), /^m[0-9a-f]{40}$/, 'meddelande-id:t ska vara en hash (m och 40 hex)');
  assert.equal(pp[0].avsikt, 'fraga'); assert.equal(pp[0].text, 'Vad saknas i första vyn för Förslag A?');
  assert.equal(pp[0].kontext?.kandidat, 'k01', 'markeringen ska följa med: kandidaten som visas');
  assert.equal(pp[0].kontext?.version, V1K); assert.equal(pp[0].kontext?.vy, 'Designstudio');
  assert.equal(await markLagret(), null, 'en fråga fryser ingen markering');
  besvara(S.partner.at(-1), 'Första vyn saknar ett tydligt nästa steg.'); skickaLage();
  await kanSkicka(page);

  // N2: samma korta svar vid två positioner i samtalet ger två meddelanden; samma position i två flikar ger ett
  const sida2 = await nySida();
  await sida2.locator('#ay-samtal .ay-msg.partnern').filter({ hasText: 'Första vyn saknar' }).waitFor();
  await kanSkicka(sida2);
  await skickaFraga(page, 'Ja');
  await vantaPa(() => partnerPosts().length === 2, 'det första "Ja" ska skickas');
  await skickaFraga(sida2, 'Ja');
  await sida2.locator('#ay-skrivsvar').filter({ hasText: 'Samma meddelande har redan skickats' }).waitFor();
  pp = partnerPosts();
  assert.equal(pp[2].meddelande_id, pp[1].meddelande_id, 'samma text vid samma position i samtalet från två flikar ska ge samma meddelande_id');
  await sida2.close();
  besvara(S.partner.at(-1), 'Bra, då föreslår jag en kortare rubrik.'); skickaLage();
  await kanSkicka(page);
  await skickaFraga(page, 'Ja');
  await vantaPa(() => partnerPosts().length === 4, 'det andra "Ja" ska skickas');
  pp = partnerPosts();
  assert.equal(pp[3].text, 'Ja');
  assert.notEqual(pp[3].meddelande_id, pp[1].meddelande_id, 'samma text vid en senare position i samtalet ska ge ett nytt meddelande_id');
  assert.equal(S.partner.filter((m) => m.text === 'Ja').length, 2, 'båda svaren "Ja" ska nå partnern');
  besvara(S.partner.at(-1), 'Jag formulerar ett förslag.'); skickaLage();
  await kanSkicka(page);

  // 1 och B3-rest. Markeringen fryses när avsikten blir Ändring, när en kandidat väljs och vid första tangenttryckningen utan markering
  await page.locator('#ay-skriv').getByRole('button', { name: 'Ändring', exact: true }).click();
  await page.locator('#ay-skriv .ay-notis').filter({ hasText: 'ditt val av kandidaten' }).waitFor();
  let mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning, mark?.beslut], ['k01', V1, T(0), 'uppdrag'], 'Ändring ska frysa kandidat, version, körning och beslut');
  assert.match(await gallerText(), new RegExp(`Förslag A.* version ${V1K}, körningen .*, vy Designstudio`), 'raden Gäller ska visa den frysta markeringen');
  const rensa = galler.getByRole('button', { name: 'Rensa markeringen' });
  await rensa.click();
  assert.equal(await markLagret(), null, 'Rensa markeringen ska ta bort markeringen');
  await rensa.waitFor({ state: 'detached', timeout: 2000 });
  await page.locator('#ay-text').press('G');
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning], ['k01', V1, T(0)], 'efter Rensa ska första tangenttryckningen i Ändring frysa en ny markering');
  await rensa.waitFor({ timeout: 2000 });
  await rensa.click();
  await rensa.waitFor({ state: 'detached', timeout: 2000 });
  await page.locator('#st-verktyg [data-st-visa="kandidater"]').click();  // studions Visa: Kandidater (arbetsytans material)
  await page.locator('#ay-material [data-kandidat="k01"]').click();
  await page.locator('#st-duk iframe').waitFor();  // valet visar riktningen i duken igen
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning], ['k01', V1, T(0)], 'en kandidat som väljs medan Ändring är vald ska frysas');
  await rensa.waitFor();
  const skickaAndring = page.locator('#ay-skriv').getByRole('button', { name: 'Spara uppdraget' });
  // uppdragets fält (ägarens uppdrag 2026-10-09, punkt 8): typen är förvald Rätta; resultat, omfattning och bevara fylls i
  const fyllUppdrag = async (sida) => { await sida.locator('#ay-resultat').fill('En kortare rubrik i första vyn.');
    await sida.locator('#ay-omfattning').fill('första vyns rubrik'); await sida.locator('#ay-bevara').fill('kompositionen'); };
  assert(await skickaAndring.isEnabled(), 'Spara uppdraget ska gå att använda när körningen väntar på ditt beslut');
  await page.locator('#ay-text').fill('Gör rubriken i första vyn kortare.');
  await page.locator('[data-falt="sida"]').fill('/'); await page.locator('[data-falt="del"]').fill('första vyn');
  await fyllUppdrag(page);
  // en ny version av den markerade kandidaten: markeringen blir inaktuell och inget skickas
  await page.locator('#ay-dialog-rubrik').click();
  nyVersion(V2);
  skickaLage();
  const notis = page.locator('#ay-skriv .ay-notis').filter({ hasText: 'Inaktuell markering' });
  await notis.waitFor();
  assert.match(await notis.textContent(), new RegExp(`kandidaten har en ny version sedan du markerade \\(${V1K}, nu ${V2K}\\)`), 'notisen ska säga varför');
  assert(await skickaAndring.isDisabled(), 'Spara uppdraget ska vara inaktiv när markeringen är inaktuell');
  assert.match(String(await skickaAndring.getAttribute('title')), /inaktuell.*stäm av/, 'knappens title ska säga varför den är inaktiv');
  await page.locator('#ay-text').press('Control+Enter');  // kortkommandot går förbi knappen: spärren ska sitta i sändningen
  await page.locator('#ay-skrivsvar').filter({ hasText: /^Inaktuell: kandidaten har en ny version/ }).waitFor();
  await sov(300);
  assert.equal(andringPosts().length, 0, 'en inaktuell markering får inte skickas');
  await notis.getByRole('button', { name: 'Stäm av mot den aktuella' }).click();
  await notis.waitFor({ state: 'detached', timeout: 2000 });
  assert(await skickaAndring.isEnabled(), 'efter Stäm av ska Spara uppdraget gå att använda');
  assert.equal(await skickaAndring.getAttribute('title'), '');
  mark = await markLagret();
  assert.deepEqual([mark?.version_hel, mark?.sida, mark?.del, mark?.beslut], [V2, '/', 'första vyn', 'uppdrag'], 'Stäm av ska binda den nya versionen och behålla sida och del');
  assert.match(await gallerText(), new RegExp(`version ${V2K}`), 'raden Gäller ska visa den avstämda versionen');

  // N3: en andra flik som markerade medan kandidaten ännu var klar; den skickar efter att kandidaten blivit vald
  const sida3 = await nySida();
  await sida3.locator('#ay-skriv').getByRole('button', { name: 'Ändring', exact: true }).click();
  const mark3 = await markLagret(sida3);
  assert.deepEqual([mark3?.version_hel, mark3?.beslut], [V2, 'uppdrag'], 'den andra flikens markering ska frysa beslutet uppdrag');
  await sida3.locator('#ay-text').fill('Gör rubriken i första vyn kortare.');
  await sida3.locator('[data-falt="sida"]').fill('/'); await sida3.locator('[data-falt="del"]').fill('första vyn');
  await fyllUppdrag(sida3);

  // 409: arbetsytan visar skälet och skickar inget av sig själv; omförsöket med samma innehåll ger samma id
  await skickaAndring.click();
  await page.locator('#ay-skrivsvar').filter({ hasText: /^Inaktuell/ }).waitFor();
  assert.match(await page.locator('#ay-skrivsvar').textContent(), /^Inaktuell: kandidaten har en ny version.* Stäm av/, 'ett 409 ska visas som Inaktuell med en uppmaning att stämma av');
  await sov(1000);
  assert.equal(andringPosts().length, 1, 'efter ett 409 skickar arbetsytan inget av sig själv');
  assert.equal(andringPosts()[0].version, V2, 'ändringen ska bära den avstämda versionen');
  await skickaAndring.click();
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Uppdraget är sparat' }).waitFor();
  const ap = andringPosts();
  assert.equal(ap.length, 2, 'två försök med ändringen');
  assert.match(String(ap[0].andring_id), /^a[0-9a-f]{40}$/, 'ändrings-id:t ska vara innehållets hash (a och 40 hex)');
  assert.equal(ap[1].andring_id, ap[0].andring_id, 'samma ändring ska ge samma id vid omförsöket');
  assert.deepEqual([ap[1].kandidat, ap[1].version, ap[1].beslut, ap[1].vy, ap[1].sida, ap[1].del, ap[1].korning, ap[1].fil],
    ['k01', V2, 'uppdrag', 'Designstudio', '/', 'första vyn', T(0), null], 'ändringen ska vara bunden till kandidat, version, körning och markering');
  assert.deepEqual(ap[1].uppdrag, { typ: 'ratta', resultat: 'En kortare rubrik i första vyn.', omfattning: ['första vyns rubrik'], bevara: ['kompositionen'] },
    'uppdraget ska bära typ, resultat, omfattning och det som bevaras');
  assert.equal(await markLagret(), null, 'en sparad ändring släpper markeringen');
  assert(!(await page.evaluate((k) => sessionStorage.getItem(k), `nwp-arbetsyta-utkast:${SLUG}`)), 'en skickad ändring ska inte ligga kvar som utkast');
  assert.equal(S.k01, 'vald', 'attrappen: efter den första raden är kandidaten vald');
  skickaLage();
  await sida3.waitForFunction(() => window.__arbetsyta.lage?.kandidater?.[0]?.status === 'vald');
  await sida3.locator('#ay-skriv').getByRole('button', { name: 'Spara uppdraget' }).click();
  await sida3.locator('#ay-skrivsvar').filter({ hasText: 'Uppdraget är sparat' }).waitFor();
  assert.equal(andringPosts().length, 3);
  assert.equal(andringPosts()[2].andring_id, ap[0].andring_id, 'samma ändring från en andra flik ska ge samma andring_id, också efter att kandidaten blivit vald');
  assert.equal(andringPosts()[2].beslut, 'uppdrag', 'POST-kroppen ska bära uppdraget, oberoende av kandidatens nya status');
  // B3-rest i samma flik: efter en skickad ändring fryser första tangenttryckningen en ny markering
  assert.equal(await markLagret(sida3), null);
  await sida3.locator('#ay-text').press('G');
  const mark3b = await markLagret(sida3);
  assert.deepEqual([mark3b?.version_hel, mark3b?.beslut], [V2, 'uppdrag'], 'efter en skickad ändring ska första tangenttryckningen frysa en ny markering');
  await sida3.locator('#ay-text').fill('Gör rubriken i första vyn kortare.');
  await sida3.locator('#ay-skriv').getByRole('button', { name: 'Spara uppdraget' }).click();
  await vantaPa(() => andringPosts().length === 4, 'den andra flikens nya markering ska kunna skicka');
  assert.equal(andringPosts()[3].beslut, 'uppdrag');
  assert.equal(andringPosts()[3].andring_id, ap[0].andring_id, 'samma uppdrag ger samma id, också efter kandidatens statusbyte');
  await sida3.locator('#ay-skrivsvar').filter({ hasText: 'Uppdraget är sparat' }).waitFor();
  await sida3.close();

  // B3-rest: kandidaten får en ny version efter din ändring; första tangenttryckningen fryser den då aktuella
  nyVersion(V3);
  skickaLage();
  await page.waitForFunction((v) => window.__arbetsyta.lage?.kandidater?.[0]?.version_hel === v, V3);
  await page.locator('#ay-text').press('K');
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.korning, mark?.beslut], ['k01', V3, T(0), 'uppdrag'], 'efter en skickad ändring ska första tangenttryckningen frysa den då aktuella versionen');
  assert.match(await gallerText(), new RegExp(`version ${V3K}`), 'raden Gäller ska visa versionen som ändringen nu är bunden till');
  await rensa.click();
  await rensa.waitFor({ state: 'detached', timeout: 2000 });
  // utan markering (ingen kandidat att markera) skickas ingen ändring
  S.utanKandidater = true; skickaLage();
  await page.waitForFunction(() => (window.__arbetsyta.lage?.kandidater || []).length === 0);
  await page.locator('#ay-text').fill('En ändring utan kandidat.');
  assert.equal(await markLagret(), null, 'utan kandidat fryses ingen markering');
  assert(await skickaAndring.isDisabled(), 'utan markering ska Spara uppdraget vara inaktiv');
  assert.match(String(await skickaAndring.getAttribute('title')), /markera kandidaten/);
  const andringarFore = andringPosts().length;
  await page.locator('#ay-text').press('Control+Enter');
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Markera kandidaten uppdraget gäller först' }).waitFor();
  await sov(300);
  assert.equal(andringPosts().length, andringarFore, 'utan markering får ingen ändring skickas');
  await page.locator('#ay-text').fill('');
  S.utanKandidater = false; skickaLage();
  await page.waitForFunction(() => (window.__arbetsyta.lage?.kandidater || []).length === 2);

  // 2. En markering i kodvyn (Granskning) följer med till studions samtal: raden Gäller visar filen och ändringen bär den
  await omradeLank('Granskning').click();
  await page.locator('#ay-filvy pre.ay-kodtext').waitFor();
  await page.locator('#ay-filer').getByRole('button', { name: /src\/pages\/index\.astro/ }).click();
  await page.locator('#ay-fil-rubrik').filter({ hasText: 'src/pages/index.astro' }).waitFor();
  await page.locator('#ay-filhuvud').getByRole('button', { name: 'Markera för en ändring' }).click();
  await meddelat('Filen är markerad');
  mark = await markLagret();
  assert.deepEqual([mark?.kandidat, mark?.version_hel, mark?.vy, mark?.fil], ['k01', V3, 'Kod och preview', 'src/pages/index.astro'], 'kodvyns markering ska binda kandidat, version och fil');
  await omradeLank('Designstudio').click();
  await flik('samtal');
  await galler.filter({ hasText: 'fil src/pages/index.astro' }).waitFor();
  assert.match(await gallerText(), /vy Kod och preview, fil src\/pages\/index\.astro/, 'raden Gäller ska visa kodvyns markering');
  assert.equal(await page.locator('#ay-skriv [data-avsikt="andring"]').getAttribute('aria-pressed'), 'true', 'en markering i kodvyn ska välja Ändring');
  await page.locator('#ay-text').fill('Korta rubriken i Hero till fyra ord.');
  await fyllUppdrag(page);  // ett sparat uppdrag tömmer fälten
  await page.locator('#ay-skriv').getByRole('button', { name: 'Spara uppdraget' }).click();
  await page.locator('#ay-skrivsvar').filter({ hasText: 'Uppdraget är sparat' }).waitFor();
  const kp = andringPosts().at(-1);
  assert.deepEqual([kp.fil, kp.vy, kp.kandidat, kp.version, kp.beslut], ['src/pages/index.astro', 'Kod och preview', 'k01', V3, 'uppdrag'], 'ändringen ska bära kodvyns fil');
  assert.notEqual(kp.andring_id, ap[0].andring_id, 'en annan ändring ger ett annat id');
  sammanfattning.partner = { meddelande_id: 'm+40 hex', samma_position_tva_flikar_samma_id: true, senare_ja_nytt_id: true, avsikt: 'fraga', kandidat: 'k01', blindvarning: true };
  sammanfattning.markering = { fryst_vid_andring: true, fryst_vid_kandidatval: true, fryst_vid_tangent_efter_rensa: true, fryst_vid_tangent_efter_skickad: true,
    utan_markering_ingen_post: true, rensa: true, inaktuell_utan_post: true, stam_av_ny_version: true, andring_409_utan_eget_omforsok: true, samma_id_omforsok: true,
    samma_id_andra_fliken_efter_statusbyte: true, beslut_ur_markeringen: true, beslut_utanfor_id: true, kodvyns_fil: true };

  // 6. Starten (under Arbete): dubbelklick och ett extra klick ger en begäran; ett förlorat svar ger samma start-id vid omförsöket
  await flik('arbete');
  const forfina = page.getByRole('button', { name: 'Starta uppdraget: Rätta Förslag A' });
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

  // förfiningen pågår: en ny körning med Stoppa; kandidaten byggs om, så arbetsversionen kan vara äldre (K6)
  S.k01 = 'under_arbete';
  S.korning = korning('valda', START2, T(32), 'forfina', true);
  S.stegstatus = ['skapat', 'skapat', 'beslutat', 'pågår', ...Array(5).fill('inte påbörjat')];
  S.handlingar = [{ id: 'stoppa', text: 'Stoppa arbetet' }];
  S.startjournal.unshift({ start_id: sp[0].start_id, handling: 'valda', tid: T(32), status: 'startad', slutkod: null, stopp_begart: false, stopp_sent: false, fel: null, process_lever: true });
  S.sessioner = [];
  S.sessioner.push(ateljesession('8e4b3daa-4f50-4162-9dce-3f4a5b6c7d8e', 'forfina-k01', 'utforande', 'k01', T(33), 'aktiv', 'processen lever', [handelse(33, 'Read')]));
  skickaLage();
  const nyText = await meddelat('En ny körning har startat');
  assert.match(nyText, /Utförare för Förslag A startade/);
  // K6: en riktning som arbetar visas med sin bevarade bild, och raden under duken säger att arbetsversionen kan vara äldre
  await page.locator('#st-duk img.st-bild').waitFor({ timeout: 3000 });
  assert.match(await page.locator('#st-dukrad').textContent(), /arbetsversionen kan vara äldre än arbetet/, 'märkningen ska säga varför');
  sammanfattning.forhandsvisning.osaker_markt = true;

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
  await omradeLank('Granskning').click();
  await page.locator('#ay-logg pre.ay-logg').first().waitFor();
  await page.locator('#ay-kodaktivitet li').nth(13).waitFor();
  await axeKor('Kod och preview efter valet 1440');
  await page.setViewportSize({ width: 390, height: 900 }); await ram();
  const s = await spill(); sammanfattning.spill.kod_efter_valet_390 = s.bredd - s.fonster;
  assert(s.bredd <= s.fonster, `Kod och preview efter valet: sidledes spill vid 390 px (${s.bredd} > ${s.fonster})`);
  await axeKor('Kod och preview efter valet 390');
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  // N7: den valda jämförelseversionen syns inte längre (en ny blind körning): vyn laddar om med den aktuella i stället för att fastna
  assert.deepEqual(await page.locator('#ay-kodmot option').evaluateAll((o) => o.map((x) => x.value)), [V1K, V2K, V3K], 'efter valet syns alla bevarade versioner');
  await page.locator('#ay-kodmot').selectOption(V1K);
  await page.locator('#ay-filvy .ay-kodtext span').filter({ hasText: `--- version ${V1K}` }).waitFor();
  S.blind = true; skickaLage();
  await page.waitForFunction(() => window.__arbetsyta.lage?.blind === true);
  await page.locator('#ay-filer').getByRole('button', { name: /src\/styles\/global\.css/ }).click();
  await page.locator('#ay-fil-rubrik').filter({ hasText: 'src/styles/global.css' }).waitFor({ timeout: 5000 });
  assert.equal(await page.locator('#ay-kodmot').inputValue(), V3K, 'kodvyn ska laddas om med den aktuella versionen');
  assert.equal(await page.locator('#ay-filer .ay-notis.fel').count(), 0, 'kodvyn får inte fastna på felet');
  sammanfattning.kodvyn_osynlig_version_laddas_om = true;
  await omradeLank('Designstudio').click();
  await flik('arbete');
  await page.locator('#ay-remsa').getByRole('heading', { name: 'Kontroller' }).waitFor();

  // 14. Samverkan (2026-10-09): meddelandefliken, agentens text blindad, ett meddelande till sessionen som arbetar med samma id
  // vid omförsök, pausens bekräftelse med omfattning, och beslutet under den bevarade bilden bundet till bildens hash
  await page.setViewportSize({ width: 1440, height: 900 }); await ram();
  const s14 = ateljesession('7d3e2c99-3e4f-4051-8cbd-2e3f4a5b6c7d', 'skapa-k01', 'utforande', 'k01', T(30), 'aktiv', 'processen lever', [handelse(31, 'Read')]);
  S.sessioner.push(s14);  // en session med löpare som arbetar, för avsnittet
  S.medd.push({ id: 'a-' + '1'.repeat(30), tid: T(4), avsandare: { typ: 'session', session_id: 'x', ansvar: 'granskning', kandidat: 'k01' }, mottagare: { typ: 'agare' },
    syfte: 'granskningsfynd', syfte_text: 'Granskningsfynd', text: 'HEMLIG-BEDOMNING: rubriken bryts på fyra rader.', belagg: ['vy-390'], kandidat: 'k01', version: S.k01v, agent: true, lage: 'sparat' });
  skickaLage();
  await flik('samtal');
  await page.getByRole('tab', { name: /Meddelanden/ }).click();
  await page.locator('#ay-samtal .ay-msg.agent').first().waitFor({ timeout: 5000 });
  const agenttext = await page.locator('#ay-samtal .ay-msg.agent').first().innerText();
  if (S.blind) assert(!agenttext.includes('HEMLIG-BEDOMNING') && /första val/.test(agenttext), 'agentens text döljs före första valet: ' + agenttext);
  else assert(agenttext.includes('Inte dina ord'), 'agentens meddelande märks som inte ägarens ord');
  assert.equal(await page.locator('#ay-oppna').innerText(), '1', 'räknaren visar meddelandet som väntar på dig');
  await axeKor('Meddelanden 1440');
  await page.locator('#ay-mottagare').selectOption({ value: `session:${s14.session_id}` });
  await page.locator('[data-syfte="andringsinstruktion"]').click();
  await page.locator('#ay-mtext').fill('Korta rubriken till två rader.');
  const forePosts = posts.length;
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka' }).click();
  await vantaPa(() => posts.length > forePosts, 'meddelandet skickas');
  const mp = posts.at(-1);
  assert.equal(mp.vag, `/api/arbetsyta/${SLUG}/meddelande`);
  assert.deepEqual([mp.body.syfte, mp.body.mottagare.typ, mp.body.version, mp.body.korning], ['andringsinstruktion', 'session', S.k01v, S.korning.startad], 'meddelandet bär syfte, mottagare, hel version och körning');
  await page.locator('#ay-msvar').filter({ hasText: 'Sparat' }).waitFor();  // svaret har kommit: fältet töms av det, inte av provet
  await page.locator('#ay-mtext').fill('Korta rubriken till två rader.');
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka' }).click();
  await vantaPa(() => posts.length > forePosts + 1, 'omförsöket skickas');
  assert.equal(posts.at(-1).body.id, mp.body.id, 'samma meddelande vid omförsök: samma id');
  sammanfattning.samverkan = { meddelande_id: 'o+hash', omforsok_samma_id: true, agenttext_blindad: S.blind };
  // pausen (under Arbete): bekräftelsen säger omfattningen
  await flik('arbete');
  await page.locator('[data-paus-session]').first().click();
  const bekr = await page.locator('.ay-bekraftruta').filter({ hasText: 'Pausa bara den här sessionen' }).innerText();
  assert(/resten av körningen fortsätter/.test(bekr) && /står kvar/.test(bekr), 'bekräftelsen säger omfattningen och att filändringar står kvar');
  await page.locator('[data-paus-ja]').click();
  await vantaPa(() => posts.some((p) => p.vag === `/api/arbetsyta/${SLUG}/paus` && p.body.omfattning === 'session' && p.body.session_id), 'pausen begärs för sessionen');
  skickaLage();
  await page.locator('#ay-roller').getByText(/Pausad/).first().waitFor({ timeout: 5000 });
  await axeKor('Sessionerna, pausad');
  await page.locator('[data-aterta-session]').first().click();
  await vantaPa(() => posts.some((p) => p.vag === `/api/arbetsyta/${SLUG}/paus` && p.body.aterta), 'återupptagningen begärs');
  sammanfattning.samverkan.paus = 'session med omfattning, återupptagen';
  // beslutet under den bevarade bilden, bundet till bildens hash
  const forraKorning = S.korning; S.korning = { ...S.korning, vantar_pa_agaren: true }; skickaLage();
  await page.getByRole('button', { name: 'Visa bilden och besluta' }).click();
  await page.locator('#ay-beslutsrad').getByRole('button', { name: 'Välj vidare' }).click();
  await axeKor('Beslutsraden');
  await page.locator('#ay-beslutsrad').getByRole('button', { name: 'Välj vidare' }).click();
  await vantaPa(() => posts.some((p) => p.vag === `/api/arbetsyta/${SLUG}/beslut`), 'beslutet skickas');
  const bp = posts.find((p) => p.vag === `/api/arbetsyta/${SLUG}/beslut`).body;
  assert.deepEqual([bp.beslut, bp.kandidater[0].version, bp.sedd[0].bild_sha, bp.sedd[0].version], ['valj', S.k01v, BILDSHA, S.k01v], 'beslutet bär den version och bild som visas');
  S.korning = forraKorning; S.sessioner.splice(S.sessioner.indexOf(s14), 1); skickaLage();
  sammanfattning.samverkan.beslut = 'bundet till bildens hash';
  await flik('samtal');
  await page.getByRole('tab', { name: /Partnern/ }).click();

  // 12b. Förslagen (förr vyn Prototyp; ägarens besked 2026-10-09 ~17:11Z: allt in i arbetsytan): den gamla adressen leder
  // dit, och besluten går genom arbetsytans beslutsväg med det du gillar, kundens belägg och bilderna du ser
  const beslutPosts = () => posts.filter((p) => p.vag === `/api/arbetsyta/${SLUG}/beslut`).map((p) => p.body);
  const forslag = () => page.getByRole('heading', { name: `Förslagen · ${SLUG}` });
  let fore_ = beslutPosts().length;
  await page.goto(origin + `/#/prototyp/${SLUG}`);
  await forslag().waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/arbetsyta/${SLUG}/forslag`, '#/prototyp/<kund> ska leda till Förslagen för samma kund');
  assert.equal((await page.locator('.pt-stegrad a[aria-current="step"]').textContent()).trim(), '5Förslag', 'stegraden ska stå på Förslag');
  assert.equal(await page.locator('.kkort').count(), 2, 'de två klara förslagen står i Förslagen');
  assert.equal(await page.locator('details summary').filter({ hasText: 'Förslag som inte blev klara (1)' }).count(), 1, 'förslaget som föll står med skälet');
  assert.equal(await page.locator('.kkort[data-k="k01"] a[href$="?sida=%2Fom%2F"]').count(), 1, 'undersidan öppnas från förslaget');
  await axeKor('Förslagen');
  await page.locator('[data-markera="k01"]').check(); await page.locator('[data-markera="k02"]').check();
  await page.locator('#k-jamfor h2').filter({ hasText: 'Sida vid sida (2)' }).waitFor();
  await page.locator('.kkort[data-k="k02"] summary').filter({ hasText: 'Det jag gillar här' }).click();
  await page.locator('[data-del="k02"]').fill('Rubrikernas tyngd.');
  await page.locator('input[name="k-b"][value="valj"]').check();
  await page.locator('#k-spara').click();
  await vantaPa(() => beslutPosts().length > fore_, 'valet ur Förslagen skickas genom arbetsytans beslutsväg');
  let fb = beslutPosts().at(-1);
  assert.deepEqual([fb.beslut, fb.kandidater.map((k) => k.id), fb.delar, typeof fb.startad, fb.avsandare, fb.sedd], ['valj', ['k01', 'k02'], { k02: 'Rubrikernas tyngd.' }, 'string', undefined, undefined],
    'valet bär båda förslagen, det du gillar och vyns tid');
  fore_ = beslutPosts().length;
  await forslag().waitFor();
  await page.locator('input[name="k-b"][value="jamfor"]').check();
  await page.locator('#k-u-avs').selectOption('kunden');
  await page.locator('#k-u-belagg').fill('Kundens mejl 2026-10-09 kl. 21.40');
  await page.locator('#k-spara').click();
  await vantaPa(() => beslutPosts().length > fore_, 'kundens jämförelse skickas');
  fb = beslutPosts().at(-1);
  assert.deepEqual([fb.beslut, fb.avsandare, fb.belagg], ['jamfor', 'kunden', 'Kundens mejl 2026-10-09 kl. 21.40'], 'kundens eget beslut bär belägget');
  // godkännandet av det förfinade förslaget binds till ögonblicksbilderna och deras hash ur arbetsytans läge
  S.forslagK01 = 'forfinad'; S.forslagFas = 'forfining';
  await omradeLank('Designstudio').click(); await omradeLank('Förslag').click();
  await page.locator('.kkort[data-k="k01"] .chip').filter({ hasText: 'förfinad' }).waitFor();
  await page.locator('[data-markera="k02"]').uncheck();
  fore_ = beslutPosts().length;
  await page.locator('input[name="k-b"][value="godkand"]').check();
  assert(await page.locator('#k-avsandare').isHidden(), 'godkännandet är ägarens: ingen avsändare att välja');
  await page.locator('#k-spara').click();
  await vantaPa(() => beslutPosts().length > fore_, 'godkännandet skickas');
  fb = beslutPosts().at(-1);
  assert.deepEqual([fb.beslut, fb.kandidater, fb.sedd.map((x) => [x.bild.split('/').pop(), x.bild_sha, x.version])],
    ['godkand', [{ id: 'k01', version: S.k01v }], [['390-forsta.png', '9'.repeat(64), S.k01v], ['1440-forsta.png', BILDSHA, S.k01v]]], 'godkännandet bär versionen och bilderna du ser');
  S.forslagK01 = undefined; S.forslagFas = undefined;
  // en kund utan körning: Förslagen säger det, inget fel
  S.utanPrototyp = true;
  await omradeLank('Designstudio').click(); await omradeLank('Förslag').click();
  await page.locator('#vy .ay-tom').filter({ hasText: 'Inga förslag än för kunden' }).waitFor();
  assert.equal(await page.locator('#vy .ay-notis.varn').count(), 0, 'en kund utan körning är inget läsfel');
  S.utanPrototyp = false;
  sammanfattning.forslagen = { adressen_leder_dit: true, val_med_delar: true, kundens_belagg: true, godkannande_med_bildernas_hash: true };

  // 15. Nortropic.app (2026-10-10): partnerns ström, Genomför i utkastet och den levande förhandsvisningens brygga
  await page.setViewportSize({ width: 1440, height: 900 });
  S.blind = false; S.k01 = 'klar'; S.korning = korning('valda', START2, T(40), 'klar_for_bedomning', false);
  S.handlingar = [{ id: 'valda', text: 'Starta uppdraget: Rätta Förslag A' }];
  await omradeLank('Designstudio').click();
  await flik('samtal');
  await page.locator('#ay-skriv').waitFor(); skickaLage();
  if (await page.locator('[data-vflik="partner"]').count()) await page.locator('[data-vflik="partner"]').click();
  await page.locator('#ay-skriv [data-avsikt="fraga"]').click();
  await kanSkicka(page);
  await skickaFraga(page, 'Hur gör vi rubriken kortare?');
  await vantaPa(() => partnerStrommar.size === 1, 'vyn öppnar partnerns ström för turen som pågår');
  const [mid, ps] = [...partnerStrommar.entries()][0];
  const strommaDel = (str, h) => str.write(`event: del\ndata: ${JSON.stringify({ handelser: h })}\n\n`);
  strommaDel(ps, [{ typ: 'resonerar' }, { typ: 'verktyg', namn: 'Read', fil: 'kunskap/arbetsyta.md' }, { typ: 'verktygssvar', fel: false }, { typ: 'stycke' }, { typ: 'text', text: 'Jag föreslår ' }]);
  strommaDel(ps, [{ typ: 'text', text: 'en rubrik på fyra ord.' }]);
  const deltext = page.locator('#ay-samtal .ay-deltext');
  await deltext.filter({ hasText: 'Jag föreslår en rubrik på fyra ord.' }).waitFor();
  assert.match(await deltext.innerText(), /Delsvar som strömmas: inte färdigt/, 'delsvaret är märkt som ofärdigt, skilt från svaret');
  assert.match(await page.locator('#ay-samtal .ay-aktivitet').innerText(), /resonerar \(innehållet visas inte\)[\s\S]*läser kunskap\/arbetsyta\.md/, 'den observerade aktiviteten');
  assert([null, 'off'].includes(await deltext.evaluate((e) => e.closest('[aria-live]')?.getAttribute('aria-live') || null)), 'tokenströmmen läses inte upp (U37)');
  // en väntande instruktion medan turen pågår: sparas utan ny ström, syns i samtalet och kan tas bort
  await page.waitForFunction(() => document.querySelector('#ay-skriv [data-skicka="partner"]')?.textContent === 'Spara som väntande');
  await page.locator('#ay-text').fill('Och knappen i första vyn?');
  await page.locator('#ay-skriv [data-skicka="partner"]').click();
  await vantaPa(() => partnerPosts().some((x) => x.vanta === true && x.text === 'Och knappen i första vyn?'), 'meddelandet sparas som väntande');
  await page.locator('#ay-samtal').getByText('Väntande: startar som nästa tur').waitFor();
  assert.equal(partnerStrommar.size, 1, 'ingen ny ström och ingen ny tur för en väntande instruktion');
  await page.locator('#ay-samtal [data-vantande-bort]').click();
  await vantaPa(() => posts.some((x) => x.vag === `/api/arbetsyta/${SLUG}/partner/vantande` && x.body.handling === 'ta_bort'), 'den väntande tas bort');
  await page.locator('#ay-samtal').getByText('Väntande: startar som nästa tur').waitFor({ state: 'detached' });
  const m1 = S.partner.find((x) => x.id === mid);
  const o = { kandidat: 'k01', version: S.k01v.slice(0, 12), sida: '/', del: 'rubriken', mal: 'En rubrik på fyra ord', avgransning: 'bilden och färgerna', forvantat: 'rubriken ryms på en rad i mobilen' };
  besvara(m1, 'Jag föreslår en rubrik på fyra ord.\n```overlamning\n' + JSON.stringify(o) + '\n```'); m1.overlamning = o;
  ps.write(`event: slut\ndata: ${JSON.stringify({ lage: 'svarat', fel: null })}\n\n`); skickaLage();
  await page.locator('#ay-samtal .ay-overlamning').waitFor();
  await meddelat('Partnern har svarat.');
  assert.equal(await page.locator('#ay-samtal .ay-deltext').count(), 0, 'efter slutet står svaret, inte delsvaret');
  // en tur som avbryts: det som hann strömmas visas som just det, aldrig som ett svar
  await kanSkicka(page);
  await skickaFraga(page, 'Och färgerna?');
  await vantaPa(() => [...partnerStrommar.keys()].some((k) => k !== mid), 'en egen ström för nästa tur');
  const [mid2, ps2] = [...partnerStrommar.entries()].find(([k]) => k !== mid);
  strommaDel(ps2, [{ typ: 'stycke' }, { typ: 'text', text: 'Färgerna kan bli ' }]);
  await deltext.filter({ hasText: 'Färgerna kan bli' }).waitFor();
  Object.assign(S.partner.find((x) => x.id === mid2), { lage: 'avbrutet', fel: 'fristen (600 s) tog slut; turen stoppades', slut: new Date().toISOString() });
  ps2.write(`event: slut\ndata: ${JSON.stringify({ lage: 'avbrutet', fel: 'fristen tog slut' })}\n\n`); skickaLage();
  await deltext.filter({ hasText: 'Det som hann strömmas: inget färdigt svar' }).waitFor();
  assert.match(await page.locator('#ay-samtal').innerText(), /fristen \(600 s\) tog slut/);
  // Genomför i utkastet: förslaget justeras och blir ett uppdrag som startas med samma operations-id, med ett klick
  await page.getByRole('button', { name: 'Genomför i utkastet…', exact: true }).click();
  assert.deepEqual([await page.locator('[data-g="resultat"]').inputValue(), await page.locator('[data-g="omfattning"]').inputValue(), await page.locator('[data-g="bevara"]').inputValue()],
    ['En rubrik på fyra ord', '/: rubriken', 'bilden och färgerna'], 'förslagets fält står i formuläret');
  await page.locator('[data-g="bevara"]').fill('bilden och färgerna\nknappens text');
  const foreA = andringPosts().length, foreS = startPosts().length;
  await page.getByRole('button', { name: 'Genomför i utkastet', exact: true }).click();
  await vantaPa(() => startPosts().length > foreS, 'genomförandet startas genom flödets ordinarie start');
  const ga = andringPosts().slice(foreA), gs = startPosts().slice(foreS);
  assert.equal(ga.length, 1, 'ett uppdrag'); assert.equal(gs.length, 1, 'en start');
  assert.match(ga[0].andring_id, /^g[0-9a-f]{40}$/);
  assert.deepEqual(ga[0].kalla, { typ: 'partnerforslag', meddelande_id: mid }, 'källan är partnerns förslag; beslutet är ditt klick');
  assert.deepEqual([ga[0].uppdrag.typ, ga[0].uppdrag.resultat, ga[0].uppdrag.bevara, ga[0].kandidat, ga[0].version], ['ratta', 'En rubrik på fyra ord', ['bilden och färgerna', 'knappens text'], 'k01', S.k01v]);
  assert.deepEqual([gs[0].handling, gs[0].start_id], ['valda', ga[0].andring_id], 'samma operations-id för uppdraget och starten');
  await page.locator('#ay-samtal').getByText(/Begäran är registrerad\. Operations-id g/).waitFor();
  // förhandsvisningens brygga i studions duk: kandidatens sida på ett eget ursprung, lägena Besök och Markera
  await page.route((u) => u.origin === forhandOrigin, (r) => r.continue());
  S.bryggaPreview = true; S.k01Byggd = T(41); skickaLage();
  await page.locator('#st-verktyg [data-st-visa="arbetsversion"]').click();  // beslutet visade den bevarade bilden; tillbaka till arbetsversionen
  const scen = page.frameLocator('#st-duk iframe');
  await scen.locator('h1').waitFor();
  await page.waitForFunction((x) => window.__arbetsyta.forhandsUrsprung === x, forhandOrigin);
  await page.locator('#st-verktyg [data-st-lage="besok"]').click();
  let ramen = page.frames().find((f) => f.url().startsWith(forhandOrigin));
  await ramen.evaluate(() => parent.postMessage({ nwp: 'forhandsbrygga/1', typ: 'markerat', tagg: 'h1', text: 'Förfalskad', selektor: 'h1', sida: '/' }, '*'));
  await sov(150);
  assert(!/Förfalskad/.test(await page.evaluate(() => window.__arbetsyta.mark?.del || '')), 'i Besök tas ingen markering emot, inte heller en förfalskad');
  await page.locator('#st-verktyg [data-st-lage="markera"]').click();
  await scen.locator('h1').click();
  await page.waitForFunction(() => /Surdeg som får ta tid/.test(window.__arbetsyta.mark?.del || ''));
  const mk = await page.evaluate(() => window.__arbetsyta.mark);
  assert.deepEqual([mk.kandidat, mk.sida, mk.version_hel, mk.vy], ['k01', '/', S.k01v, 'Designstudio'], 'markeringen bär kandidaten, sidan, den hela versionen och vyn');
  await meddelat('Markerat i förhandsvisningen');
  // Redigera text i förhandsvisningen (direktredigeringen) står i Granskningen, med samma brygga
  await omradeLank('Granskning').click();
  const scen2 = page.frameLocator('#ay-material iframe');
  await scen2.locator('h1').waitFor();
  await page.waitForFunction((x) => window.__arbetsyta.forhandsUrsprung === x, forhandOrigin);
  await page.locator('[data-forhandslage="redigera"]').click();
  await scen2.locator('#ingress').click();
  await page.locator('#ay-redigering').filter({ hasText: 'Redigera i förhandsvisningen' }).waitFor();
  await scen2.locator('#ingress[contenteditable]').waitFor();
  await page.keyboard.type('Vi bakar varje natt, även söndagar.');
  await page.keyboard.press('Enter');
  await page.locator('#ay-redigering').filter({ hasText: 'Ändra i källan?' }).waitFor();
  const redigeraPosts = () => posts.filter((x) => x.vag === `/api/arbetsyta/${SLUG}/redigera`).map((x) => x.body);
  assert.equal(redigeraPosts().length, 0, 'inget sparas före ditt klick');
  await page.getByRole('button', { name: 'Spara i källan och bygg om', exact: true }).click();
  await vantaPa(() => redigeraPosts().length === 1, 'redigeringen begärs');
  const rp = redigeraPosts()[0];
  assert.deepEqual([rp.kandidat, rp.version, rp.korning, rp.gammal, rp.ny, rp.sida], ['k01', S.k01v, S.korning.startad, 'Vi bakar varje natt.', 'Vi bakar varje natt, även söndagar.', '/']);
  assert.match(rp.redigering_id, /^r[0-9a-f]{40}$/);
  S.redigeringar = [{ id: rp.redigering_id, status: 'klar', kandidat: 'k01', fil: 'src/pages/index.astro', gammal: rp.gammal, ny: rp.ny, till_version: V3,
    skal: 'texten står i källan (src/pages/index.astro), sajten är ombyggd och fotograferad' }]; skickaLage();
  await page.locator('#ay-redigering').filter({ hasText: 'Direktredigering klar' }).waitFor();
  await page.locator('#ay-redigering').getByRole('button', { name: 'Stäng', exact: true }).click();
  await scen2.locator('a').first().click();
  await page.locator('#ay-redigering').filter({ hasText: 'står på 2 ställen' }).waitFor();
  assert.equal(page.frames().find((f) => f.url().startsWith(forhandOrigin)).url(), forhandOrigin + '/', 'ett klick i Redigera text navigerar inte på sajten');
  // den ärliga vägen: ett uppdrag med texten, som fortsätter i studions samtal (Granskningen har inget samtal)
  await page.getByRole('button', { name: 'Gör ett uppdrag i stället', exact: true }).click();
  await page.waitForFunction((s) => location.hash === '#/studio/' + s, SLUG);
  await page.locator('#ay-text').waitFor();
  assert.match(await page.locator('#ay-text').inputValue(), /^Byt texten «Boka tid»/, 'den ärliga vägen: ett uppdrag med texten');
  assert.equal(await page.locator('#ay-skriv [data-avsikt="andring"]').getAttribute('aria-pressed'), 'true', 'samtalet står på Ändring');
  assert.match(await page.locator('#ay-omfattning').inputValue(), /på \//, 'omfattningen följer med');
  await page.locator('#ay-text').fill(''); await page.evaluate((s) => { sessionStorage.removeItem('nwp-arbetsyta-utkast:' + s); localStorage.removeItem('nwp-arbetsyta-utkast:' + s); }, SLUG);
  await axeKor('Designstudio med strömmen, genomförandet och markeringen');
  sammanfattning.nortropic_app = { strom_delsvar_skilt_fran_svar: true, vantande_instruktion: true, avbrott_utan_pahittat_svar: true, genomfor_samma_operations_id: true,
    brygga_markering_i_studion: true, direktredigering_i_granskningen_efter_klick: true, ej_mappbar_blir_uppdrag_i_studions_samtal: true, forfalskad_markering_nekad: true };

  // 13. Inga sidfel; konsolfelen är bara de nätfel provet självt framkallar
  const avsiktliga = [/\/api\/prototyp\/prov-kund$/, /\/api\/flode\/prov-kund\/start$/, /\/api\/arbetsyta\/prov-kund\/andring$/, /\/api\/arbetsyta\/prov-kund\/strom$/, /\/api\/arbetsyta\/prov-kund\/kod$/];
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
  forhand.closeAllConnections?.();
  await new Promise((r) => srv.close(r));
  await new Promise((r) => forhand.close(r));
}
