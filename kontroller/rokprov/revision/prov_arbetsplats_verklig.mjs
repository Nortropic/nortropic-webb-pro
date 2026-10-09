// Användarresan i arbetsytan med verkliga sessioner (ägarens uppdrag 2026-10-09 om den kompletta arbetsplatsen, punkt 11):
// nio punkter genom arbetsytans egna knappar, i en provinstans med fiktivt material. Startas av prov_arbetsplats_verklig.py.
//   node prov_arbetsplats_verklig.mjs <bas> <nyckel> <kund> <rot> <granskarnyckelns fil> <ut>
// Varje punkt beläggs mot filerna (domloggen, startjournalen, bussen, VINNARE.json) och processlistan, inte bara mot vyn.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from '../../node_modules/playwright/index.mjs';

const [bas, nyckel, slug, rot, granskarfil, ut] = process.argv.slice(2);
const U = path.join(rot, 'underlag', slug), K = path.join(rot, 'kunder', slug);
const bilder = path.join(ut, 'bilder'); fs.mkdirSync(bilder, { recursive: true });
const sammanfattning = { start: new Date().toISOString(), punkter: {}, natanrop: [], vscode: null, sidfel: [] };
const logg = (...x) => { const r = `${new Date().toISOString().slice(11, 19)} ${x.join(' ')}`; console.log(r); fs.appendFileSync(path.join(ut, 'resan.log'), r + '\n'); };
const las = (p) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; } };
const domar = () => { try { return fs.readFileSync(path.join(U, 'DESIGNDOMAR.jsonl'), 'utf8').split('\n').filter(Boolean).map((x) => JSON.parse(x)); } catch { return []; } };
const meddelanden = () => { const d = path.join(U, 'arbetsyta', 'meddelanden'); try { return fs.readdirSync(d).filter((f) => f.endsWith('.json')).map((f) => las(path.join(d, f))).filter(Boolean); } catch { return []; } };
const lageAv = (m) => { const h = m.handelser || []; const sista = h.at(-1)?.lage; if (['okant', 'ej_levererat', 'tillbaka'].includes(sista)) return sista; const efter = h.map((x) => x.lage).lastIndexOf('tillbaka'); const o = ['sparat', 'koat', 'tillbaka', 'levererat', 'mottaget', 'besvarat', 'genomfort']; return h.slice(efter + 1).reduce((b, x) => (o.indexOf(x.lage) > o.indexOf(b) ? x.lage : b), 'sparat'); };
const nar = (m, lage) => (m?.handelser || []).filter((x) => x.lage === lage).map((x) => x.tid).at(-1) || null;
const styrning = () => { const d = path.join(U, 'arbetsyta', 'styrning'); try { return fs.readdirSync(d).map((f) => las(path.join(d, f))).filter(Boolean); } catch { return []; } };
const sha = (p) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function vanta(fn, tak, vad, steg = 2000) { const slut = Date.now() + tak; while (Date.now() < slut) { const v = await fn(); if (v) return v; await new Promise((r) => setTimeout(r, steg)); } throw new Error('väntade förgäves: ' + vad); }
function punkt(n, ok, belagg) { sammanfattning.punkter[n] = { ok, ...belagg }; logg(`PUNKT ${n}: ${ok ? 'OK' : 'INTE OK'} ${JSON.stringify(belagg).slice(0, 400)}`); fs.writeFileSync(path.join(ut, 'resan.json'), JSON.stringify(sammanfattning, null, 1)); }
async function extern(metod, vag, data) {
  const r = await fetch(bas + vag, { method: metod, headers: { Authorization: 'Bearer ' + fs.readFileSync(granskarfil, 'utf8').trim(), 'Content-Type': 'application/json' }, body: data ? JSON.stringify(data) : undefined });
  return { status: r.status, data: await r.json().catch(() => ({})) };
}
try { execFileSync('pgrep', ['-x', 'Code']); sammanfattning.vscode = 'Visual Studio Code körde under provet; resan använde den inte (inga anrop till /oppna)'; } catch { sammanfattning.vscode = 'Visual Studio Code körde inte'; }

const browser = await chromium.launch({ headless: true });
async function oppna() {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => sammanfattning.sidfel.push(e.message));
  page.on('request', (r) => { if (r.method() !== 'GET') sammanfattning.natanrop.push(`${r.method()} ${new URL(r.url()).pathname}`); });
  await page.goto(`${bas}/#nyckel=${nyckel}&till=arbetsyta/${slug}`);
  await page.locator('#ay-huvud').getByText('Testdata').waitFor({ timeout: 30000 });
  return { ctx, page };
}
const bild = async (page, namn) => page.screenshot({ path: path.join(bilder, namn + '.png') });
let { ctx, page } = await oppna();
try {
  // 1. Öppna ett projekt och starta ett tillåtet arbetssteg: ditt första val (beslutstjänsten) och förfiningen (flödets start)
  await page.getByRole('button', { name: 'Visa bilden och besluta' }).click();
  await page.locator('#ay-beslutsrad').getByRole('button', { name: 'Välj vidare' }).click();
  await page.locator('#ay-beslutstext').fill('Testdata: den här vidare (provet).');
  await page.locator('#ay-beslutsrad').getByRole('button', { name: 'Välj vidare' }).click();
  await vanta(() => domar().some((d) => d.beslut === 'valj' && d.arbetsyta?.sedd?.length), 30000, 'valet i domloggen');
  const val = domar().find((d) => d.beslut === 'valj');
  await bild(page, '1a-valet');
  const forfina = page.locator('[data-handling="valda"]');
  await forfina.waitFor({ timeout: 60000 });
  await forfina.dblclick();  // ett dubbelklick ska bli en start
  await vanta(() => { const d = path.join(U, 'ateljestarter'); try { return fs.readdirSync(d).some((f) => (las(path.join(d, f)) || {}).handling === 'valda'); } catch { return false; } }, 60000, 'startjournalen');
  const starter = fs.readdirSync(path.join(U, 'ateljestarter')).map((f) => las(path.join(U, 'ateljestarter', f))).filter((x) => x && x.handling === 'valda');
  punkt(1, starter.length === 1 && Boolean(val?.arbetsyta?.sedd?.[0]?.bild_sha), { val: val && { kandidater: val.kandidater, sedd: val.arbetsyta?.sedd }, starter: starter.length });

  // 2. Följa riktiga sessioner: en session med löpare dyker upp och arbetar
  const arbetare = await vanta(() => styrning().find((s) => s.ansvar === 'utforande' && !s.slut && s.lage === 'arbetar' && s.init), 15 * 60000, 'en arbetande session med löpare', 3000);
  await page.locator(`[data-skriv-till="${arbetare.session_id}"]`).waitFor({ timeout: 60000 });
  await page.locator(`[data-folj="${arbetare.session_id}"]`).click();
  await page.waitForTimeout(1500);
  await bild(page, '2-folj');
  await page.locator('[data-folj-slut]').click();
  punkt(2, true, { session: arbetare.session_id, roll: arbetare.roll, modell: arbetare.init?.modell, skills: (arbetare.init?.skills || []).length, mcp: arbetare.init?.mcp });

  // 3. Skicka en instruktion under arbete (Meddelanden, till sessionen som arbetar)
  await page.locator(`[data-skriv-till="${arbetare.session_id}"]`).click();
  await page.locator('[data-syfte="andringsinstruktion"]').click();
  await page.locator('#ay-mtext').fill('Gör huvudrubriken kort och tydlig: "Reparationer i Testby". Ändra inget annat. KVITTERA med ett kvittoblock när det är gjort.');
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka' }).click();
  const instr = await vanta(() => meddelanden().find((m) => m.avsandare?.typ === 'agare' && m.syfte === 'andringsinstruktion' && m.mottagare?.session_id === arbetare.session_id), 30000, 'instruktionen i bussen');
  await vanta(() => ['mottaget', 'besvarat'].includes(lageAv(meddelanden().find((m) => m.id === instr.id))), 10 * 60000, 'instruktionen mottagen', 3000);
  await bild(page, '3-instruktion-mottagen');

  // 4. Ett granskningsfynd överlämnas till rätt arbetare: ditt uttryckliga mandat i arbetsytan (körning, kandidat, tillåtna
  // åtgärder), den riktiga Codex läser provinstansens granskningspaket skrivskyddat och lämnar fyndet, som postas med
  // granskarnyckeln. Saknas Codex postar provet en egen text och säger det (ingen annan modell ersätter Codex).
  await page.locator('.ay-mandat summary').click();
  await page.locator('[data-mandat="granskare"]').selectOption('extern:codex');
  await page.locator('[data-mandat="kandidat"]').selectOption(arbetare.kandidat).catch(() => {});
  await page.locator('[data-mandat="omfattning"]').fill('rubrikens längd och läsbarhet i mobil');
  await page.locator('[data-mandat-atgard="granskningsfynd"]').check();
  await page.locator('#ay-mandatform').getByRole('button', { name: 'Ge mandat' }).click();
  await vanta(() => { try { return fs.readdirSync(path.join(U, 'arbetsyta', 'mandat')).length; } catch { return 0; } }, 30000, 'mandatet');
  const mandatet = fs.readdirSync(path.join(U, 'arbetsyta', 'mandat')).map((f) => las(path.join(U, 'arbetsyta', 'mandat', f))).find((x) => x && x.granskare?.namn === 'codex');
  const underlag = await extern('GET', `/api/extern/${slug}/underlag`);
  const kand = underlag.data.kandidater.find((k) => k.id === arbetare.kandidat) || underlag.data.kandidater[0];
  let fyndData = { syfte: 'granskningsfynd', till: 'utforande', kandidat: kand.id, version: kand.version,
    text: 'Rubriken bryts på för många rader i 390 px; korta den till högst två rader.', belagg: [`bilder/${kand.id}/390.png: rubriken bryts på flera rader`] };
  let forfattare = 'provets egen text (Codex saknas)';
  const paket = path.join(ut, 'codex-paket');
  try {
    execFileSync(path.join(rot, '.venv', 'bin', 'python'), ['-B', path.join(rot, 'kontroller', 'extern_granskare.py'), '--bas', bas, 'paket', 'codex', slug, paket],
      { env: { ...process.env, NWP_GRANSKARE_NYCKLAR: path.dirname(granskarfil) }, stdio: 'pipe' });
    execFileSync('codex', ['exec', '--ignore-user-config', '-s', 'read-only', '--skip-git-repo-check', '--ephemeral', '-C', paket, '--output-schema', path.join(paket, 'fynd-schema.json'),
      '-o', path.join(ut, 'codex-fynd.json'), `Ofarligt prov med fiktiva testdata. Läs AGENTS.md och underlag.json och titta på bilderna för ${kand.id}. Lämna exakt ett granskningsfynd till utforande för ${kand.id} inom mandatets omfattning, med konkret belägg ur bilden, och be om kvitto. Använd ${kand.id}:s version ur underlag.json.`],
      { stdio: ['ignore', fs.openSync(path.join(ut, 'codex.log'), 'a'), fs.openSync(path.join(ut, 'codex.log'), 'a')], timeout: 10 * 60000 });
    const f = (las(path.join(ut, 'codex-fynd.json'))?.fynd || []).find((x) => x.till === 'utforande');
    if (f) { fyndData = f; forfattare = 'Codex (codex exec, skrivskyddat, i provinstansens paket)'; }
  } catch (e) { logg('Codex gick inte att köra:', String(e.message).slice(0, 200)); }
  const fynd = await extern('POST', `/api/extern/${slug}/fynd`, fyndData);
  if (fynd.status !== 200) throw new Error('granskarens fynd nekades: ' + JSON.stringify(fynd));
  const mottaget = await vanta(() => { const m = meddelanden().find((x) => x.id === fynd.data.id); return m && m.levererat_till && ['mottaget', 'besvarat', 'genomfort'].includes(lageAv(m)) && m; }, 15 * 60000, 'granskarens fynd mottaget av en arbetande session', 3000);
  await bild(page, '4-granskarens-fynd');
  const mottagaren = styrning().find((x) => x.session_id === mottaget.levererat_till.session_id);
  punkt(4, mottaget.avsandare.typ === 'extern' && mottaget.levererat_till.ansvar === 'utforande' && mottaget.levererat_till.kandidat === kand.id && Boolean(mottaget.mandat)
    && Boolean(nar(mottaget, 'levererat')) && Boolean(nar(mottaget, 'mottaget')) && mottaget.korning === (las(path.join(U, 'atelje', 'STATUS.json')) || {}).startad,
    { meddelande: mottaget.id, forfattare, avsandare: mottaget.avsandare, korning: mottaget.korning, mandat: mottaget.mandat, mandatet: mandatet && { korning: mandatet.korning, kandidat: mandatet.kandidat, atgarder: mandatet.atgarder },
      levererat_till: mottaget.levererat_till, mottagaren_arbetade: Boolean(mottagaren && mottagaren.init), registrerat: nar(mottaget, 'sparat'), levererat: nar(mottaget, 'levererat'), mottaget: nar(mottaget, 'mottaget') });

  // 5. Pausa och återuppta med rätt omfattning: sessionen, sedan körningen
  let pausad = null;
  if (styrning().find((s) => s.session_id === arbetare.session_id && !s.slut)) {
    await page.locator(`[data-paus-session="${arbetare.session_id}"]`).click();
    await bild(page, '5a-paus-bekrafta');
    await page.locator(`[data-paus-ja="${arbetare.session_id}"]`).click();
    pausad = await vanta(() => { const s = styrning().find((x) => x.session_id === arbetare.session_id); return s && s.lage === 'pausad' && s; }, 5 * 60000, 'sessionen pausad');
    await page.locator('#ay-roller').getByText('Pausad').first().waitFor({ timeout: 30000 });
    await bild(page, '5b-pausad');
    await page.locator(`[data-skriv-till="${arbetare.session_id}"]`).click().catch(() => {});
    await page.locator('[data-syfte="fraga"]').click();
    await page.locator('#ay-mtext').fill('En fråga under pausen: vad var du mitt i när pausen kom? KVITTERA.');
    await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka' }).click();
    const underPausen = await vanta(() => meddelanden().find((m) => m.avsandare?.typ === 'agare' && m.syfte === 'fraga' && m.text.includes('under pausen')), 30000, 'frågan under pausen');
    await page.waitForTimeout(6000);
    const ilevererad = lageAv(meddelanden().find((m) => m.id === underPausen.id));
    await page.locator(`[data-aterta-session="${arbetare.session_id}"]`).click();
    const ater = await vanta(() => { const s = styrning().find((x) => x.session_id === arbetare.session_id); return s && (s.lage === 'arbetar' || s.slut) && s.aterupptagen && s; }, 5 * 60000, 'sessionen återupptagen');
    // körningen: ingen ny session startar bakom pausen, och den som arbetar pausas
    await page.locator('[data-paus-projekt]').click();
    await bild(page, '5c-projektpaus-bekrafta');
    await page.locator('[data-paus-projekt-ja]').click();
    const projekt = await vanta(() => { const d = las(path.join(U, 'arbetsyta', 'STYRNING.json')); return d && d.projekt && d; }, 30000, 'projektets paus');
    await vanta(() => styrning().filter((s) => !s.slut && s.lage === 'arbetar').length === 0, 5 * 60000, 'inga sessioner arbetar under projektets paus');
    await bild(page, '5d-projektpausad');
    await page.locator('[data-aterta-projekt]').click();
    await vanta(() => !(las(path.join(U, 'arbetsyta', 'STYRNING.json')) || {}).projekt, 30000, 'projektets paus hävd');
    punkt(5, Boolean(pausad && ater && ilevererad === 'sparat'), { pausad_session: { sedan: pausad.sedan, verktyg_kvar: pausad.verktyg_kvar }, under_pausen: ilevererad, aterupptagen: ater.aterupptagen, projektpaus: projekt.projekt });
  } else punkt(5, false, { skal: 'sessionen slutade innan pausen kunde prövas' });

  // 6. Stänga och öppna arbetsytan utan förlorat läge eller dubbla starter
  const foreStang = meddelanden().map((m) => [m.id, lageAv(m)]);
  await ctx.close();
  ({ ctx, page } = await oppna());
  await page.getByRole('tab', { name: /Meddelanden/ }).click();
  await page.locator('#ay-samtal').getByText(instr.id).waitFor({ timeout: 30000 });
  const startNu = fs.readdirSync(path.join(U, 'ateljestarter')).map((f) => las(path.join(U, 'ateljestarter', f))).filter((x) => x && x.handling === 'valda');
  await bild(page, '6-aterupptagen-flik');
  punkt(6, startNu.length === 1, { meddelanden_fore: foreStang.length, meddelanden_efter: meddelanden().length, starter: startNu.length });

  // 3 (forts.) och 4 (forts.): besvarade när arbetarens tur slutat
  const forfinad = await vanta(() => { const st = las(path.join(U, 'atelje', 'STATUS.json')); return st && ['klar_for_bedomning', 'fel'].includes(st.steg) && st; }, 40 * 60000, 'förfiningen klar', 5000);
  const instrNu = meddelanden().find((m) => m.id === instr.id), fyndNu = meddelanden().find((m) => m.id === fynd.data.id);
  punkt(3, ['besvarat', 'genomfort'].includes(lageAv(instrNu)), { meddelande: instr.id, lage: lageAv(instrNu), kvitto: instrNu.kvitto, svar: (instrNu.svar?.text || '').slice(0, 300) });
  Object.assign(sammanfattning.punkter[4], { lage_till_slut: lageAv(fyndNu), besvarat: nar(fyndNu, 'besvarat'), kvitto: fyndNu.kvitto || null,
    genomfort: fyndNu.syfte === 'andringsinstruktion' ? 'se genomförandet i arbetsytan' : 'ett granskningsfynd har inget genomförandeläge; kvittot är mottagarens påstående' });
  logg('körningen:', forfinad.steg, JSON.stringify(forfinad.fel || '').slice(0, 200));

  // 7. Jämföra versioner och begära en ändring
  await page.reload(); await page.locator('#ay-huvud').getByText('Testdata').waitFor({ timeout: 30000 });
  await page.locator('[data-material="jamfor"]').click();
  await page.waitForTimeout(1500);
  const jamfor = await page.locator('#ay-jamformed option').allTextContents().catch(() => []);
  if (jamfor.some((t) => t.startsWith('Tidigare version'))) await page.locator('#ay-jamformed').selectOption({ label: jamfor.find((t) => t.startsWith('Tidigare version')) });
  await bild(page, '7a-jamfor');
  await page.getByRole('tab', { name: /Meddelanden/ }).click();
  const till = await page.locator('#ay-mottagare option').allTextContents();
  await page.locator('#ay-mottagare').selectOption({ index: till.findIndex((t) => t.startsWith('Utföraren för')) });
  await page.locator('[data-syfte="andringsinstruktion"]').click();
  await page.locator('#ay-mtext').fill('Nästa varv: ge telefonnumret en tydligare plats i första vyn.');
  await page.locator('#ay-skriv').getByRole('button', { name: 'Skicka' }).click();
  const andring = await vanta(() => meddelanden().find((m) => m.avsandare?.typ === 'agare' && m.text.startsWith('Nästa varv')), 30000, 'ändringen i bussen');
  punkt(7, jamfor.length > 0 && andring.mottagare.typ === 'adress', { jamfor_med: jamfor, andring: { id: andring.id, mottagare: andring.mottagare, version: andring.version, lage: lageAv(andring) } });

  // 8. Godkänna exakt den version som visats (Prototypvyns beslutstjänst, bunden till bilden)
  await page.getByRole('tab', { name: /Partnern/ }).click();
  await page.getByRole('button', { name: 'Visa bilden och besluta' }).click();
  const godk = page.locator('#ay-beslutsrad').getByRole('button', { name: 'Godkänn denna version' });
  let p8 = { skal: 'Godkänn visades inte (kandidaten är inte förfinad)' };
  if (await godk.count()) {
    await godk.click(); await bild(page, '8a-godkann-bekrafta');
    await page.locator('#ay-beslutsrad').getByRole('button', { name: 'Godkänn' }).click();
    const g = await vanta(() => domar().find((d) => d.beslut === 'godkand'), 60000, 'godkännandet i domloggen').catch(() => null);
    const vin = las(path.join(U, 'atelje', 'VINNARE.json')) || {};
    const sedd = g?.arbetsyta?.sedd?.[0];
    const bildNu = sedd ? sha(path.join(rot, sedd.bild)) : null;
    let bygge = 'inget'; try { execFileSync('pgrep', ['-f', `kor.sh ${slug}`]); bygge = 'kor.sh kör'; } catch { /* inget bygge */ }
    await bild(page, '8b-godkand');
    p8 = { godkand: Boolean(g), version: g?.kandidater?.[0]?.version, sedd, bild_nu_sha: bildNu, vinnare: vin.godkand && { version: vin.godkand.version, kandidat: vin.godkand.kandidat },
      helbygge: bygge, korningar: fs.existsSync(path.join(K, 'korningar')) ? fs.readdirSync(path.join(K, 'korningar')) : [] };
    punkt(8, Boolean(g) && sedd?.bild_sha === bildNu && vin.godkand?.version === g.kandidater[0].version && bygge === 'inget', p8);
  } else punkt(8, false, p8);

  // 9. Hitta rapport, beslut och bevis i efterhand: meddelandena med lägen, sessionens historik och besluten i Prototyp
  await page.getByRole('tab', { name: /Meddelanden/ }).click(); await bild(page, '9a-meddelanden');
  const historik = page.locator(`[data-historik="${arbetare.session_id}"]`);
  let rader = 0;
  let gren = null;
  if (await historik.count()) {
    await historik.click(); await page.locator('.ay-historik li').first().waitFor({ timeout: 30000 }); rader = await page.locator('.ay-historik li').count(); await bild(page, '9b-historik');
    // följdfrågan till den avslutade sessionen: en förgrening som bara läser, registrerad med föräldern
    if (await page.locator('#ay-ftext').count()) {
      await page.locator('#ay-ftext').fill('Vilka filer ändrade du för rubriken, och varför?');
      await page.locator('#ay-foljdform').getByRole('button', { name: 'Fråga' }).click();
      gren = await vanta(() => { const d = path.join(U, 'arbetsyta', 'grenar'); try { return fs.readdirSync(d).filter((f) => f.endsWith('.json') && !f.startsWith('svar-')).map((f) => las(path.join(d, f))).find((g) => g && g.foralder === arbetare.session_id && g.slut); } catch { return null; } }, 10 * 60000, 'följdfrågans svar', 3000);
      const svar = las(path.join(U, 'arbetsyta', 'grenar', `svar-${gren.id}.json`)) || {};
      gren = { id: gren.id, foralder: gren.foralder, session_id: gren.session_id, ansvar: gren.ansvar, behorighet: gren.behorighet, fel: Boolean(svar.is_error), svar: String(svar.result || '').slice(0, 300),
        egen_session: Boolean(gren.session_id) && gren.session_id !== gren.foralder };
      await page.waitForTimeout(4500); await bild(page, '9c-foljdfraga');
    }
    await page.locator('[data-historik-slut]').click();
  }
  await page.goto(`${bas}/#/prototyp/${slug}`); await page.waitForTimeout(2500); await bild(page, '9d-prototyp');
  const prototypText = await page.locator('#vy').innerText();
  await page.goto(`${bas}/#/dokumentation`); await page.waitForTimeout(2000); await bild(page, '9e-dokumentation');
  punkt(9, rader > 0 && meddelanden().length >= 4 && Boolean(gren?.egen_session && !gren.fel), { historikrader: rader, foljdfraga: gren, meddelanden: meddelanden().length, domar: domar().map((d) => d.beslut), prototyp_nämner_godkänd: /godk/i.test(prototypText) });
} catch (e) {
  logg('FEL:', e.stack || e.message); sammanfattning.fel = String(e.message || e); await bild(page, 'fel').catch(() => {});
} finally {
  sammanfattning.slut = new Date().toISOString();
  sammanfattning.editor_anropad = sammanfattning.natanrop.some((x) => x.includes('/oppna'));
  fs.writeFileSync(path.join(ut, 'resan.json'), JSON.stringify(sammanfattning, null, 1));
  await browser.close();
}
const ok = Object.keys(sammanfattning.punkter).length === 9 && Object.values(sammanfattning.punkter).every((p) => p.ok) && !sammanfattning.fel && !sammanfattning.editor_anropad;
logg(ok ? 'RESAN OK' : 'RESAN INTE HEL');
process.exit(ok ? 0 : 1);
