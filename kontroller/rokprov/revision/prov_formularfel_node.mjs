// Ett fall ur prov_formularfel.py: Workern ur exporten mot attrapperna, enbart syntetiska fält. Argument: worker.mjs,
// migreringskatalogen, fallet. Skriver svaret, händelserna, loggen och lagrets innehåll som JSON.
import { pathToFileURL } from 'node:url';
import { d1, r2, assets } from './worker_attrapper.mjs';

const [workerFil, migreringar, mode] = process.argv.slice(2);
const { default: worker } = await import(pathToFileURL(workerFil));
const verkligTimer = setTimeout;
const vanta = (ms) => new Promise((r) => verkligTimer(r, ms));
// Fristerna (sekunder i drift) blir 20 ms; en långsam leverantör svarar efter 80 ms.
globalThis.setTimeout = (fn, ms, ...a) => verkligTimer(fn, ms >= 1000 ? 20 : ms, ...a);
const verkligTimeout = AbortSignal.timeout.bind(AbortSignal);
AbortSignal.timeout = (ms) => verkligTimeout(ms >= 1000 ? 20 : ms);

const events = [];
const logs = []; console.error = (...x) => logs.push(x.join(' '));
const krok = async (vad, detalj, args) => {
  if (vad === 'd1.run') events.push([vad, args[0]]); else events.push([vad, typeof detalj === 'string' ? detalj : null]);
  if (vad === 'd1.batch' && (mode === 'lagerfel' || mode.startsWith('jsonfel'))) throw new Error('SYNTETISKT-HEMLIGT lagringsfel');
  if (vad === 'd1.batch.efter' && mode === 'sparad-men-fel') throw new Error('Network connection lost');
  if (vad === 'r2.put' && mode === 'r2fel') throw new Error('SYNTETISKT-HEMLIGT bilagefel');
  if (vad === 'r2.put' && mode === 'r2kvitto') return { svar: { key: 'annan/bilaga' } };
  if (vad === 'r2.put' && mode === 'r2tomt') return { svar: null };
  if (vad === 'r2.delete' && mode === 'jsonfel-raderfel') throw new Error('SYNTETISKT-HEMLIGT raderingsfel');
  if ((vad === 'r2.put' && mode === 'langsam-r2') || (vad === 'd1.batch' && mode === 'langsam-batch') ||
      (vad === 'd1.run' && args[0] === 'skickar' && mode === 'langsam-utkorg') || (vad === 'd1.first' && mode === 'langsam-kontroll')) await vanta(80);
  return null;
};
const DB = d1(migreringar, krok);
const BILAGOR = r2(krok);
const ASSETS = assets({ '/': '<!doctype html><h1>Start</h1>' });
// Cloudflares send_email-bindning som attrapp: felkoderna som i Workers API (E_…), en kastad fel utan kod, ett
// kvitto utan meddelande-id och ett långsamt svar
const felkod = (kod, text) => Object.assign(new Error(text), { code: kod });
const EMAIL = { async send(m) {
  events.push(['mejl', { to: m.to, from: m.from, subject: m.subject, bilagor: (m.attachments || []).map((b) => b.filename),
                         bilagetyp: (m.attachments || []).map((b) => typeof b.content), text: typeof m.text }]);
  if (mode === 'langsam-mejl') { await vanta(80); return { messageId: 'sen-1' }; }
  if (mode === 'mejlkast') throw new Error('SYNTETISKT-HEMLIGT transportfel');
  if (mode === 'mejlfel') throw felkod('E_INTERNAL_SERVER_ERROR', 'SYNTETISKT-HEMLIGT internt fel');
  if (mode === 'mejlnekad') throw felkod('E_RECIPIENT_NOT_ALLOWED', 'SYNTETISKT-HEMLIGT mottagaren är inte tillåten');
  if (mode === 'tomtmejlkvitto') return {};
  if (mode === 'felmejlkvitto') return { messageId: '' };
  if (mode === 'htmlmejlkvitto') return '<html>ok</html>';
  return { messageId: '<00000000-0000-4000-8000-000000000001@notis.nortropic.se>' };
} };
const env = { ASSETS, MILJO: 'produktion', DB, BILAGOR, EMAIL, FORFRAGAN_TILL: 'test@example.invalid', FORFRAGAN_FRAN: 'formular@notis.example.invalid', GALLRING_DAGAR: '30' };
if (mode === 'ingetlager') delete env.DB;
if (mode === 'ingenmottagare') delete env.EMAIL;
if (mode === 'demo') env.MILJO = 'forhandsvisning';  // också med nycklar och lager: ingenting sparas eller skickas

globalThis.fetch = async () => { throw new Error('Förbjudet nät i provet: Workern mejlar genom bindningen'); };

const values = { namn: 'Syntetisk <text> & "citat"', telefon: '0700000000', meddelande: 'Rad ett\n</textarea><script>globalThis.xss=true</script>', fylltid: '9000', inskick: 'prov-inskick-0000000000000001' };
if (mode === 'validering') values.telefon = '';
if (mode === 'telefon') values.telefon = 'ring ABC123';
if (mode === 'langtext') values.meddelande = 'x\n'.repeat(1999) + 'xx';
if (mode === 'honeypot') values.webbplats = 'falla';
if (mode === 'snabb') values.fylltid = '500';
if (mode === 'ogiltigt-inskick') { values.inskick = '"><script>x</script>'; values.telefon = ''; }
if (['utan-inskick', 'dubblett-innehall', 'fonstergrans', 'nytt-fonster'].includes(mode)) delete values.inskick;
// innehållsnyckelns tiominutersfönster: en sekund före en gräns, sedan över den (samma ärende) eller 25 minuter senare (nytt)
const verkligNu = Date.now.bind(Date);
let klocka = ['fonstergrans', 'nytt-fonster'].includes(mode) ? Math.ceil(verkligNu() / 600000) * 600000 - 1000 : null;
Date.now = () => klocka ?? verkligNu();
const bas = 'https://kund.example.invalid';
const begaran = (falt = values) => {
  const fd = new FormData(); for (const [k, v] of Object.entries(falt)) fd.append(k, v);
  if (mode === 'bildtyp') fd.append('bild', new Blob(['<svg/>'], { type: 'image/svg+xml' }), 'syntetisk.svg');
  if (mode === 'bildstor') fd.append('bild', new Blob([new Uint8Array(4000001)], { type: 'image/jpeg' }), 'syntetisk.jpg');
  if (['giltig-bild', 'r2fel', 'r2kvitto', 'r2tomt', 'langsam-r2', 'langsam-batch', 'sparad-men-fel'].includes(mode) || mode.startsWith('jsonfel')) fd.append('bild', new Blob(['syntetisk bild'], { type: 'image/jpeg' }), 'syntetisk.jpg');
  if (mode === 'filnamn') fd.append('bild', new Blob(['syntetisk bild'], { type: 'image/png' }), '../../forfragningar/annan/bilaga');
  const vard = bas;
  return new Request(vard + '/api/forfragan/', { method: 'POST', body: fd, headers: { origin: mode === 'origin' ? 'https://angripare.example.invalid' : vard } });
};
let req = begaran();
if (mode === 'olast') req = new Request(req.url, { method: 'POST', body: 'x', headers: { 'content-type': 'multipart/form-data; boundary=saknas' } });
if (mode === 'forstor') req = new Request(req.url, { method: 'POST', body: 'x', headers: { 'content-length': '5000000' } });
if (mode === 'strom' || mode === 'falsklangd') req = new Request(req.url, { method: 'POST', body: 'x'.repeat(4400001), headers: mode === 'falsklangd' ? { 'content-length': '1' } : {} });
if (mode === 'metod') req = new Request(req.url);
if (mode === 'utan-snedstreck') req = new Request(bas + '/api/forfragan', { method: 'POST', body: 'x' });
if (mode === 'annan-api') req = new Request(bas + '/api/annat/');
if (mode === 'sida') req = new Request(bas + '/');
// webbläsarens egna huvuden: en felvy med no-referrer gav "Origin: null" men Sec-Fetch-Site same-origin; en annan webbplats
// ger cross-site oavsett Origin
if (mode === 'origin-null') req = new Request(req.url, { method: 'POST', body: req.body, duplex: 'half', headers: { 'content-type': req.headers.get('content-type'), origin: 'null', 'sec-fetch-site': 'same-origin' } });
if (mode === 'cross-site') req = new Request(req.url, { method: 'POST', body: req.body, duplex: 'half', headers: { 'content-type': req.headers.get('content-type'), origin: bas, 'sec-fetch-site': 'cross-site' } });

const svar = [];
const kor = async (r) => { const s = await worker.fetch(r, env); svar.push({ status: s.status, headers: Object.fromEntries(s.headers), html: await s.text() }); };
if (mode === 'samtidigt') await Promise.all([kor(begaran()), kor(begaran())]);
else await kor(req);
if (mode.startsWith('langsam-')) await vanta(150);  // den sena operationen hinner bli klar innan lagret läses
if (mode === 'fonstergrans') klocka += 2000;
if (mode === 'nytt-fonster') klocka += 25 * 60000;
if (['dubblett-inskick', 'dubblett-innehall', 'langsam-batch', 'mejlfel', 'fonstergrans', 'nytt-fonster', 'sparad-men-fel'].includes(mode)) await kor(begaran());
// samma inskicks-id (återställt av webbläsaren efter bakåt eller omladdning) med ett nytt meddelande är ett nytt ärende
if (mode === 'nytt-meddelande-samma-inskick') { await kor(begaran({ ...values, meddelande: 'Ett helt annat meddelande.' })); }
if (mode === 'dubblett-innehall') await kor(begaran({ ...values, meddelande: 'Ett annat meddelande' }));
const rader = DB.db.prepare('SELECT f.*, u.status, u.forsok, u.mejl_id, u.fel FROM forfragningar f LEFT JOIN utkorg u ON u.forfragan = f.id ORDER BY f.mottagen').all();
console.log(JSON.stringify({ ...svar[0], svar, events, logs, values, rader, r2: [...BILAGOR.objekt.entries()] }));
