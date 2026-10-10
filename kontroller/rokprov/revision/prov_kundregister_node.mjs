// Fallen ur prov_kundregister.py: mallens Worker med D1 som riktig SQLite (worker_attrapper.mjs) och en märkt attrapp
// av Pipedrives API i stället för nätet, enbart syntetiska uppgifter. Argument: worker.js, migreringskatalogen. Skriver
// varje falls svar, anropen till attrappen, kundregistrets rad och loggen som JSON.
import { pathToFileURL } from 'node:url';
import { d1, r2, assets } from './worker_attrapper.mjs';

const [workerFil, migreringar] = process.argv.slice(2);
const { default: worker } = await import(pathToFileURL(workerFil));
const verkligTimer = setTimeout;
const vanta = (ms) => new Promise((r) => verkligTimer(r, ms));
globalThis.setTimeout = (fn, ms, ...a) => verkligTimer(fn, ms >= 1000 ? 20 : ms, ...a);  // fristerna blir 20 ms

const NYCKEL = 'SYNTETISKT-HEMLIG-PIPEDRIVE-NYCKEL-0000';
const EMAIL = { async send() { return { messageId: '<prov@notis.example.invalid>' }; } };
const svar = (status, data) => new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

async function fall(namn, { miljo = 'produktion', vars = { PIPEDRIVE_TOKEN: NYCKEL, PIPEDRIVE_DOMAN: 'provab' }, pipedrive = {}, antal = 1, radfel = false, falt = {} } = {}) {
  const anrop = [];
  const logg = [];
  console.error = (...x) => logg.push(x.join(' '));
  const krok = async (vad, detalj) => {
    if (radfel && vad === 'd1.run' && typeof detalj === 'string' && detalj.includes('INSERT INTO kundregister')) throw new Error('SYNTETISKT-HEMLIGT lagringsfel');
    return null;
  };
  const env = { ASSETS: assets({ '/': '<h1>Start</h1>' }), MILJO: miljo, DB: d1(migreringar, krok), BILAGOR: r2(), EMAIL,
                FORFRAGAN_TILL: 'mottagare@example.invalid', FORFRAGAN_FRAN: 'formular@notis.example.invalid', GALLRING_DAGAR: '30', ...vars };
  globalThis.fetch = async (url, init = {}) => {
    const u = new URL(String(url));
    anrop.push({ url: String(url), metod: init.method, nyckel: (init.headers || {})['x-api-token'] === NYCKEL, kropp: JSON.parse(init.body) });
    const steg = u.pathname.split('/').pop();  // persons, leads, notes
    const lage = pipedrive[steg] || 'ok';
    if (lage === 'nekad') return svar(steg === 'persons' ? 401 : 400, { success: false, error: 'SYNTETISKT-HEMLIGT leverantörstext' });
    if (lage === 'serverfel') return svar(502, { success: false, error: 'SYNTETISKT-HEMLIGT' });
    if (lage === 'html') return new Response('<html>SYNTETISKT-HEMLIGT</html>', { status: 200 });
    if (lage === 'langsam') { await vanta(80); return svar(201, { success: true, data: { id: 1 } }); }
    if (lage === 'kast') throw new TypeError('SYNTETISKT-HEMLIGT nätfel');
    return svar(201, { success: true, data: { id: steg === 'persons' ? 4711 : steg === 'leads' ? 'adf21080-0e10-11eb-879b-05d71fb426ec' : 99 } });
  };
  const values = { namn: 'Prov <Provsson>', telefon: '070-000 00 00', meddelande: 'Rad ett\n<script>x</script> & "citat"', fylltid: '9000',
                   inskick: 'prov-kundregister-0000000001', ...falt };
  const svarslista = [];
  for (let i = 0; i < antal; i++) {
    const fd = new FormData();
    for (const [k, v] of Object.entries(values)) fd.append(k, v);
    const vantande = [];
    const ctx = { waitUntil: (p) => vantande.push(p) };
    const r = await worker.fetch(new Request('https://kund.example/api/forfragan/', { method: 'POST', body: fd, headers: { 'sec-fetch-site': 'same-origin' } }), env, ctx);
    svarslista.push({ status: r.status, location: r.headers.get('location'), utfall: r.headers.get('x-forfragan'), vantande: vantande.length });
    await Promise.all(vantande);
  }
  const rader = env.DB.db.prepare('SELECT status, person_id, lead_id, forsok, fel FROM kundregister').all();
  return { namn, svar: svarslista, anrop, rader, logg };
}

const ut = [
  await fall('klar'),
  await fall('ej-valt', { vars: {} }),
  await fall('demo', { miljo: 'forhandsvisning' }),
  await fall('halvt-konfigurerat', { vars: { PIPEDRIVE_TOKEN: NYCKEL } }),
  await fall('ogiltig-doman', { vars: { PIPEDRIVE_TOKEN: NYCKEL, PIPEDRIVE_DOMAN: 'evil.example/x' } }),
  await fall('nekad-person', { pipedrive: { persons: 'nekad' } }),
  await fall('nekad-lead', { pipedrive: { leads: 'nekad' } }),
  await fall('serverfel', { pipedrive: { persons: 'serverfel' } }),
  await fall('oläsbart', { pipedrive: { leads: 'html' } }),
  await fall('langsam', { pipedrive: { notes: 'langsam' } }),
  await fall('natfel', { pipedrive: { persons: 'kast' } }),
  await fall('dubblett', { antal: 2 }),
  await fall('radfel', { radfel: true }),
];
process.stdout.write(JSON.stringify(ut));
