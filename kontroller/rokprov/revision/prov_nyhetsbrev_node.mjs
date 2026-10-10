// Fallen ur prov_nyhetsbrev.py: mallens Worker (argumentet) mot en märkt attrapp av Brevos API i stället för nätet,
// enbart syntetiska uppgifter. Skriver varje falls svar, de anrop attrappen fick och loggen som JSON.
import { pathToFileURL } from 'node:url';

const [workerFil] = process.argv.slice(2);
const { default: worker } = await import(pathToFileURL(workerFil));
const verkligTimer = setTimeout;
const vanta = (ms) => new Promise((r) => verkligTimer(r, ms));
globalThis.setTimeout = (fn, ms, ...a) => verkligTimer(fn, ms >= 1000 ? 20 : ms, ...a);  // fristen 8 s blir 20 ms

const NYCKEL = 'xkeysib-SYNTETISKT-HEMLIG-NYCKEL-0000';
const BAS = { MILJO: 'produktion', ASSETS: { fetch: async () => new Response('<h1>Start</h1>') } };
const VALT = { ...BAS, BREVO_API_NYCKEL: NYCKEL, NYHETSBREV_LISTA: '12', NYHETSBREV_MALL: '7' };
const FALT = { epost: 'prov@example.invalid', samtycke: 'ja' };

async function fall(namn, { env = VALT, falt = FALT, metod = 'POST', huvuden = {}, brevo = 'ok201', kropp } = {}) {
  const anrop = [];
  const logg = [];
  console.error = (...x) => logg.push(x.join(' '));
  globalThis.fetch = async (url, init = {}) => {
    anrop.push({ url: String(url), metod: init.method, nyckel: (init.headers || {})['api-key'] === NYCKEL,
                 kropp: init.body ? JSON.parse(init.body) : null });
    if (brevo === 'kast') throw new TypeError('SYNTETISKT-HEMLIGT nätfel');
    if (brevo === 'langsam') { await vanta(80); return new Response(null, { status: 201 }); }
    if (brevo === 'ok204') return new Response(null, { status: 204 });
    if (brevo === 'nekad') return new Response(JSON.stringify({ code: 'invalid_parameter', message: 'SYNTETISKT-HEMLIGT leverantörstext' }), { status: 400 });
    if (brevo === 'serverfel') return new Response('SYNTETISKT-HEMLIGT', { status: 502 });
    return new Response(JSON.stringify({ id: 1 }), { status: 201 });
  };
  const body = kropp !== undefined ? kropp : new URLSearchParams(falt).toString();
  const req = new Request('https://kund.example/api/nyhetsbrev/', {
    method: metod, body: metod === 'POST' ? body : undefined,
    headers: { 'content-type': 'application/x-www-form-urlencoded', 'sec-fetch-site': 'same-origin', ...huvuden } });
  const r = await worker.fetch(req, env);
  const text = await r.text();
  return { namn, status: r.status, location: r.headers.get('location'), utfall: r.headers.get('x-nyhetsbrev'),
           allow: r.headers.get('allow'), csp: r.headers.get('content-security-policy'), robots: r.headers.get('x-robots-tag'),
           text, huvuden: JSON.stringify([...r.headers]), anrop, logg };
}

const ut = [
  await fall('ej-valt', { env: BAS }),
  await fall('ej-valt-get', { env: BAS, metod: 'GET' }),
  await fall('valt-get', { metod: 'GET' }),
  await fall('demo', { env: { ...VALT, MILJO: 'forhandsvisning' } }),
  await fall('demo-utan-val', { env: { ...BAS, MILJO: 'forhandsvisning' } }),
  await fall('skickad'),
  await fall('skickad-204', { brevo: 'ok204' }),
  await fall('nekad', { brevo: 'nekad' }),
  await fall('serverfel', { brevo: 'serverfel' }),
  await fall('natfel', { brevo: 'kast' }),
  await fall('langsam', { brevo: 'langsam' }),
  await fall('utan-samtycke', { falt: { epost: 'prov@example.invalid' } }),
  await fall('fel-epost', { falt: { epost: '"><script>x</script>@', samtycke: 'ja' } }),
  await fall('honeypot', { falt: { ...FALT, webbplats: 'robot' } }),
  await fall('frammande', { huvuden: { 'sec-fetch-site': 'cross-site' } }),
  await fall('frammande-origin', { huvuden: { 'sec-fetch-site': '', origin: 'https://annan.example' } }),
  await fall('for-stor', { kropp: 'epost=' + 'a'.repeat(20000) }),
  await fall('halvt-konfigurerat', { env: { ...BAS, BREVO_API_NYCKEL: NYCKEL, NYHETSBREV_LISTA: '12' } }),
  await fall('ogiltigt-id', { env: { ...VALT, NYHETSBREV_MALL: '7; DROP' } }),
];
process.stdout.write(JSON.stringify(ut));
