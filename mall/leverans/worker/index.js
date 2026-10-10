// Kundsajtens Worker på Cloudflare Workers (ägarens beslut 2026-10-09: Cloudflare Workers är målplattform). Sidorna är
// förrenderade och serveras som Static Assets; bara vägarna under /api/ körs här (wrangler.jsonc, run_worker_first).
//
// Förfrågan (POST /api/forfragan/), även utan JavaScript:
// - valideringsfel återger texten i en skyddad felsida (422, 413, 400);
// - en förfrågan sparas beständigt i D1, och en bilaga privat i R2, före varje avisering; inget sparat ger 503 med texten kvar;
// - aviseringen är en utkorg i D1 (vantar → skickar → accepterad | fel): sparad men inte aviserad svarar 303 till den
//   förrenderade /mottagen/, och raden står kvar för uppföljning; "skickar" utan slut är ett osäkert utfall som stäms av
//   mot mejltjänsten före ett nytt försök, aldrig ett nytt mejl i blindo;
// - mejlet går genom Cloudflares send_email-bindning (EMAIL) till verksamhetens verifierade adress, med avsändaren på
//   Nortropics routningsdomän; bindningen är låst till just de adresserna i wrangler.jsonc (ägarens beslut 2026-10-10:
//   Cloudflares e-post är K04:s huvudväg);
// - varje lagringssteg har en frist: utan bekräftelse inom den svarar Workern i stället för att vänta;
// - samma inskick två gånger (formulärets inskicks-id, annars innehållet inom tio minuter) blir ett ärende, inte två;
// - utanför produktionen (MILJO annat än produktion) sparas och skickas ingenting.
//
// Nyhetsbrevet (POST /api/nyhetsbrev/, katalogens k14-brevo-dubbel) när kunden har valt det: anmälan med dubbel
// bekräftelse hos Brevo; se nyhetsbrev() nedan. Kundregistret (katalogens k10-pipedrive-lead) när kunden har valt det:
// ett sparat ärende förs över som person, lead och anteckning i verksamhetens Pipedrive efter svaret; se tillKundregister().
// Svar som Workern skapar får sina säkerhetshuvuden här; _headers gäller bara de statiska filerna.

const MAX_BYTE = 4_400_000;
const MAX_BILD = 4_000_000;
const BILDTYPER = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/gif', 'image/avif'];
const TOMT = { namn: '', telefon: '', meddelande: '' };
const RUBRIKER = { namn: 'Namn', telefon: 'Telefon', meddelande: 'Meddelande', bild: 'Bild' };
const FRIST_LAGRING = 10000;
const FRIST_MEJL = 8000;
// Referrer-Policy same-origin: felvyns formulär skickar då sitt Origin (no-referrer ger "Origin: null" på en POST och
// stänger ute ett nytt försök), och ingen adress lämnar webbplatsen.
const SAKERHET = {
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin', 'X-Frame-Options': 'DENY',
  'Strict-Transport-Security': 'max-age=63072000; includeSubDomains', 'Cache-Control': 'no-store',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
};
const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' })[c]);

function svar(mal, utfall, huvud = 'X-Forfragan') {
  return new Response(null, { status: 303, headers: { ...SAKERHET, Location: mal, [huvud]: utfall } });
}

function enkel(status, text, extra = {}) {
  return new Response(text, { status, headers: { ...SAKERHET, 'Content-Type': 'text/plain; charset=utf-8', ...extra } });
}

function sida(rubrik, innehall, status, utfall, huvud = 'X-Forfragan') {
  const html = `<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>${esc(rubrik)}</title><style>
  *{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#242424;font:1rem/1.6 system-ui,sans-serif}main{max-width:42rem;margin:3rem auto;padding:0 1.25rem 3rem}h1{font-size:clamp(1.8rem,6vw,2.4rem);line-height:1.2}a{color:#163c78}label{display:block;font-weight:650;margin-top:1.5rem}input,textarea,button{font:inherit;max-width:100%}input,textarea{display:block;width:100%;border:1px solid #555;border-radius:.2rem;padding:.65rem;background:#fff;color:#242424}textarea{min-height:10rem;resize:vertical}button{padding:.7rem 1.3rem;background:#163c78;color:#fff;border:0;border-radius:.2rem;min-height:44px;margin-top:1.5rem;cursor:pointer}a:focus-visible,input:focus-visible,textarea:focus-visible,button:focus-visible{outline:3px solid #1c5ab3;outline-offset:3px}.fel{color:#a01818}.sammanfattning{border-left:4px solid #a01818;padding:1rem;background:#fff}.hjalp{font-size:.95rem}p,li{overflow-wrap:anywhere}.falla{display:none}input[type=file]{overflow-wrap:anywhere}
  </style></head><body><main><h1>${esc(rubrik)}</h1>${innehall}</main></body></html>`;
  return new Response(html, { status, headers: {
    ...SAKERHET, 'Content-Type': 'text/html; charset=utf-8', [huvud]: utfall, 'X-Robots-Tag': 'noindex, nofollow',
    'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
  } });
}

function felvy(falt, fel, status, utfall, besked, bildVald = false, inskick = '') {
  const attrs = (k) => fel[k] ? ` aria-invalid="true" aria-describedby="${k}-fel"` : '';
  const rad = (k) => fel[k] ? `<p class="fel" id="${k}-fel">${esc(fel[k])}</p>` : '';
  const lista = Object.entries(fel).map(([k, v]) => `<li><a href="#${k}">${esc(RUBRIKER[k])}: ${esc(v)}</a></li>`).join('');
  return sida('Kontrollera din förfrågan', `<div class="sammanfattning"><p>${esc(besked)}</p>${lista ? `<ul>${lista}</ul>` : ''}</div>
  <form action="/api/forfragan/" method="post" enctype="multipart/form-data">
  <label for="namn">Namn</label><input id="namn" name="namn" autocomplete="name" required maxlength="100" value="${esc(falt.namn)}"${attrs('namn')}>${rad('namn')}
  <label for="telefon">Telefon</label><input id="telefon" name="telefon" type="tel" autocomplete="tel" required maxlength="40" pattern="(?=.*[0-9])[0-9+\\-\\(\\) ]{6,40}" value="${esc(falt.telefon)}"${attrs('telefon')}>${rad('telefon')}
  <label for="meddelande">Meddelande</label><textarea id="meddelande" name="meddelande" required maxlength="4000"${attrs('meddelande')}>
${esc(falt.meddelande)}</textarea>${rad('meddelande')}
  <label for="bild">Bild (valfritt)</label><p class="hjalp" id="bild-hjalp">Högst 4 MB. JPEG, PNG, WebP, HEIC, HEIF, GIF eller AVIF.${bildVald ? ' Välj bilden igen om du vill bifoga den; webbläsaren kan inte fylla i filfältet åt dig.' : ''}</p><input id="bild" name="bild" type="file" accept="${BILDTYPER.join(',')}" aria-describedby="bild-hjalp${fel.bild ? ' bild-fel' : ''}"${fel.bild ? ' aria-invalid="true"' : ''}>${rad('bild')}
  <div class="falla" aria-hidden="true"><label for="webbplats">Lämna tomt</label><input id="webbplats" name="webbplats" tabindex="-1" autocomplete="off"></div><input type="hidden" name="fylltid" value="0">${giltigtInskick(inskick) ? `<input type="hidden" name="inskick" value="${esc(inskick)}">` : ''}
  <p>Uppgifterna används för att besvara din förfrågan. <a href="/integritet/">Så hanteras dina uppgifter</a>.</p>
  <button type="submit">Skicka förfrågan</button></form><p><a href="/kontakt/">Andra kontaktvägar</a></p>`, status, utfall);
}

// Sparad men inte aviserad: 303 till den förrenderade /mottagen/, aldrig ett svar på POST-adressen, så att en omladdning
// eller bakåt/framåt aldrig blir ett nytt inskick. Sidan lovar ingen svarstid och säger att inget behöver skickas igen.
const mottagen = () => svar('/mottagen/', 'sparad');
// Klientens filnamn är bara en etikett i mejlet och ärendet: utan katalogdel och styrtecken.
const filnamn = (bild) => String(bild.name || '').split(/[\\/]/).pop().replace(/[\u0000-\u001f\u007f]/g, '').slice(0, 120) || 'bild';
const giltigtInskick = (v) => typeof v === 'string' && /^[A-Za-z0-9-]{16,64}$/.test(v);
const OBEKRAFTAD = 'Vi kunde inte bekräfta att förfrågan sparades. Texten finns kvar. Försök igen senare eller använd en annan kontaktväg.';
// Loggen och utkorgen får bara Workerns egna orsaker, aldrig en leverantörs feltext (den kan bära innehåll eller nycklar).
const egen = (text, extra = {}) => Object.assign(new Error(text), { egen: true }, extra);
const orsak = (e) => e && e.egen ? e.message.slice(0, 200)
  : e && typeof e.code === 'string' && /^E_[A-Z_]{2,60}$/.test(e.code) ? 'mejltjänsten: ' + e.code
  : e && (e.name === 'TimeoutError' || e.name === 'AbortError') ? 'avbrutet vid fristen'
  : 'fel hos leverantören (' + String((e && e.name) || 'okänt').slice(0, 40) + ')';

// Ett lagringssteg som inte bekräftas inom fristen räknas som obekräftat. Steget kan ändå bli klart senare; därför tas en
// bilaga bara bort efter ett uttryckligt fel, aldrig efter en frist (ärendet kan ha sparats och peka på den).
function frist(lofte, ms, vad) {
  let t;
  const tid = new Promise((_, nej) => { t = setTimeout(() => nej(egen(vad + ': ingen bekräftelse inom fristen', { frist: true })), ms); });
  return Promise.race([lofte, tid]).finally(() => clearTimeout(t));
}

function konfigurerad(env) {
  return Boolean(env.EMAIL && typeof env.EMAIL.send === 'function' && String(env.FORFRAGAN_TILL || '').split(',').some((x) => x.trim())
    && env.FORFRAGAN_FRAN);
}

// Bindningens felkoder (Cloudflare Email Service, Workers API): de här betyder att mejlet inte skickades; allt annat
// (E_INTERNAL_SERVER_ERROR, ett fel utan kod, en frist) är ett okänt utfall.
const NEKADE = new Set(['E_VALIDATION_ERROR', 'E_FIELD_MISSING', 'E_TOO_MANY_RECIPIENTS', 'E_TOO_MANY_ATTACHMENTS', 'E_SENDER_NOT_VERIFIED',
  'E_RECIPIENT_NOT_ALLOWED', 'E_RECIPIENT_SUPPRESSED', 'E_SENDER_DOMAIN_NOT_AVAILABLE', 'E_CONTENT_TOO_LARGE', 'E_DELIVERY_FAILED',
  'E_RATE_LIMIT_EXCEEDED', 'E_DAILY_LIMIT_EXCEEDED', 'E_HEADER_NOT_ALLOWED', 'E_HEADER_USE_API_FIELD', 'E_HEADER_VALUE_INVALID',
  'E_HEADER_VALUE_TOO_LONG', 'E_HEADER_NAME_INVALID', 'E_HEADERS_TOO_LARGE', 'E_HEADERS_TOO_MANY']);

async function lasForm(request, max = MAX_BYTE) {
  // Mät också strömmen; frånvarande eller felaktig Content-Length får inte kringgå taket.
  if (Number(request.headers.get('content-length') || 0) > max) return { forStor: true };
  const reader = request.body?.getReader();
  if (!reader) throw new Error('Ingen kropp');
  const delar = []; let storlek = 0;
  try {
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      storlek += value.byteLength;
      if (storlek > max) { await reader.cancel(); return { forStor: true }; }
      delar.push(value);
    }
  } finally { reader.releaseLock(); }
  const ny = new Request(request.url, { method: 'POST', headers: { 'content-type': request.headers.get('content-type') || '' }, body: new Blob(delar) });
  return { form: await ny.formData() };
}

async function sha256(text) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, '0')).join('');
}

// Idempotensen: { nyckel, innehall }. nyckel är ärendets identitet: formulärets inskicks-id (sätts i webbläsaren när sidan
// laddas) tillsammans med innehållet, så att ett nytt meddelande med ett återställt id (bakåt, omladdning) är ett nytt
// ärende; utan id är det innehållet i tiominutersfönstret. innehall är innehållet i fönstret och det föregående, så att
// samma innehåll skickat igen (också utan JavaScript, eller över en fönstergräns) blir samma ärende.
async function idempotens(inskick, falt, bild) {
  const fonster = Math.floor(Date.now() / 600000);
  const text = [falt.namn, falt.telefon, falt.meddelande, bild ? `${bild.type}/${bild.size}` : ''].join('\n');
  const innehall = await Promise.all([fonster, fonster - 1].map(async (f) => 'h:' + await sha256(text + '\n' + f)));
  const nyckel = giltigtInskick(inskick) ? 'i:' + inskick + ':' + (await sha256(text)).slice(0, 32) : innehall[0];
  return { nyckel, innehall };
}

function base64(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

async function befintlig(env, id) {
  return frist(env.DB.prepare(`SELECT f.id AS id, u.status AS status FROM forfragningar f LEFT JOIN utkorg u ON u.forfragan = f.id
    WHERE f.nyckel = ? OR f.innehall IN (?, ?) ORDER BY f.mottagen LIMIT 1`)
    .bind(id.nyckel, ...id.innehall).first(), FRIST_LAGRING, 'kontrollen av tidigare inskick');
}

async function radera(env, nyckel) {
  // Bästa försök. Misslyckas det står objektet kvar utan ärende och hittas av avstämningen (föräldralösa bilagor).
  try { await env.BILAGOR.delete(nyckel); } catch { console.error('forfragan: bilagan kunde inte tas bort efter ett fel'); }
}

async function spara(env, id, idem, falt, bild, nu) {
  let bilaga = null;
  const dagar = Math.max(1, Number(env.GALLRING_DAGAR || 365));
  const gallras = new Date(Date.parse(nu) + dagar * 86400000).toISOString();
  let resultat;
  try {
    if (bild) {
      bilaga = `forfragningar/${nu.slice(0, 10)}/${id}/bilaga`; // Klientens filnamn styr aldrig lagringsnamnet.
      const obj = await frist(env.BILAGOR.put(bilaga, await bild.arrayBuffer(), {
        httpMetadata: { contentType: bild.type }, customMetadata: { forfragan: id },
      }), FRIST_LAGRING, 'bilagan');
      if (!obj || obj.key !== bilaga) throw egen('Bilagans lagringskvitto stämmer inte');
    }
    // En batch är en transaktion: ärendet och dess utkorgsrad finns båda eller ingen av dem.
    resultat = await frist(env.DB.batch([
      env.DB.prepare(`INSERT INTO forfragningar (id, nyckel, innehall, mottagen, namn, telefon, meddelande, bilaga, bilaga_typ, bilaga_storlek, bilaga_namn, gallras)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(nyckel) DO NOTHING`)
        .bind(id, idem.nyckel, idem.innehall[0], nu, falt.namn, falt.telefon, falt.meddelande, bilaga, bild ? bild.type : null, bild ? bild.size : null,
          bild ? filnamn(bild) : null, gallras),
      env.DB.prepare(`INSERT INTO utkorg (forfragan, status, forsok, uppdaterad) SELECT ?, 'vantar', 0, ? WHERE EXISTS (SELECT 1 FROM forfragningar WHERE id = ?)`)
        .bind(id, nu, id),
    ]), FRIST_LAGRING, 'ärendet');
  } catch (e) {
    // Bilagan tas bara bort när raden bevisligen inte finns: ett tvetydigt fel (eller en frist) kan ha sparat ärendet.
    if (bilaga && !e.frist) {
      const finns = await befintlig(env, idem).catch(() => undefined);
      if (finns === null) await radera(env, bilaga);
    }
    throw e;
  }
  if (!resultat[0].meta.changes) {  // samma inskick hann före: det första ärendet gäller
    if (bilaga) await radera(env, bilaga);
    return { dubblett: (await befintlig(env, idem).catch(() => null)) || {} };
  }
  return { id, bilaga };
}

async function mejla(env, falt, bild) {
  const text = [`Namn: ${falt.namn}`, `Telefon: ${falt.telefon}`, '', falt.meddelande, '', bild ? `Bild: ${filnamn(bild)}` : 'Ingen bild'].join('\n');
  const meddelande = {
    from: env.FORFRAGAN_FRAN, to: String(env.FORFRAGAN_TILL).split(',').map((x) => x.trim()).filter(Boolean),
    subject: `Förfrågan från webbplatsen: ${falt.namn.slice(0, 60)}`, text,
  };
  // bilagan som base64-sträng (den lokala simuleringen kan inte serialisera ArrayBuffer)
  if (bild) meddelande.attachments = [{ content: base64(new Uint8Array(await bild.arrayBuffer())), filename: filnamn(bild), type: bild.type, disposition: 'attachment' }];
  let svar;
  try {
    svar = await frist(env.EMAIL.send(meddelande), FRIST_MEJL, 'mejlet');
  } catch (e) {
    if (e && typeof e.code === 'string' && NEKADE.has(e.code)) e.nekad = true;
    throw e;
  }
  if (!svar || typeof svar.messageId !== 'string' || !/^[^\s]{1,512}$/.test(svar.messageId)) throw egen('Mejltjänstens kvitto saknar meddelande-id');
  return svar.messageId;
}

async function utkorg(env, id, status, falt = {}) {
  const nu = new Date().toISOString();
  return frist(env.DB.prepare(`UPDATE utkorg SET status = ?, forsok = forsok + ?, mejl_id = COALESCE(?, mejl_id), fel = ?, uppdaterad = ? WHERE forfragan = ?`)
    .bind(status, falt.forsok || 0, falt.mejl_id || null, falt.fel || null, nu, id).run(), FRIST_LAGRING, 'utkorgen');
}

// Webbläsarens Sec-Fetch-Site först (sätts oberoende av referrer-policyn); utan den ett Origin som inte är webbplatsens.
function frammande(request) {
  const site = request.headers.get('sec-fetch-site');
  const origin = request.headers.get('origin');
  return site ? !['same-origin', 'none'].includes(site) : Boolean(origin && origin !== new URL(request.url).origin);
}

async function forfragan(request, env, ctx) {
  if (frammande(request)) return enkel(403, 'Förfrågan kom från en annan webbplats och togs inte emot.');
  let result;
  try { result = await lasForm(request); }
  catch {
    return felvy(TOMT, {}, 400, 'ofullstandig', 'Vi kunde inte läsa formuläret. Uppgifterna kunde inte återställas. Försök igen eller använd en annan kontaktväg.');
  }
  if (result.forStor) return felvy(TOMT, { bild: 'För stor begäran. Välj en mindre bild.' }, 413, 'for-stor', 'Vi kunde inte läsa hela formuläret eftersom det var för stort. Uppgifterna kunde inte återställas.');
  const form = result.form;
  const t = (k) => typeof form.get(k) === 'string' ? form.get(k) : '';
  if (t('webbplats').trim()) return svar('/tack/', 'honeypot');
  const fylltid = Number(t('fylltid') || 0);
  if (fylltid > 0 && fylltid < 1500) return svar('/tack/', 'honeypot');
  const raw = { namn: t('namn'), telefon: t('telefon'), meddelande: t('meddelande') };
  // Multipart normaliserar radslut till CRLF; fältets längd i webbläsaren räknar LF.
  const falt = Object.fromEntries(Object.entries(raw).map(([k, v]) => [k, v.replace(/\r\n?/g, '\n').trim()]));
  const fel = {};
  if (!falt.namn || falt.namn.length > 100) fel.namn = 'Skriv ditt namn, högst 100 tecken.';
  if (!/^[0-9+\-() ]{6,40}$/.test(falt.telefon) || !/\d/.test(falt.telefon)) fel.telefon = 'Skriv ett telefonnummer med 6–40 tecken: siffror, mellanslag, +, bindestreck eller parenteser.';
  if (!falt.meddelande || falt.meddelande.length > 4000) fel.meddelande = 'Skriv ett meddelande, högst 4 000 tecken.';
  const b = form.get('bild');
  const bild = b && typeof b === 'object' && b.size > 0 ? b : null;
  let status = 422, utfall = 'ofullstandig';
  if (bild && bild.size > MAX_BILD) { fel.bild = 'Bilden är för stor. Högst 4 MB.'; status = 413; utfall = 'for-stor'; }
  else if (bild && !BILDTYPER.includes(bild.type)) fel.bild = 'Välj en bild i något av de angivna formaten.';
  if (Object.keys(fel).length) return felvy(raw, fel, status, utfall, 'Inget har skickats. Rätta de markerade fälten; texten finns kvar.', !!bild, t('inskick'));
  // Utanför produktionen (förhandsvisning, test utan egna resurser, lokalt) sparas och skickas aldrig något, också om en
  // variabel råkar finnas: ett riktigt mejl eller ett riktigt ärende ur en förhandsvisning vore ett fel.
  if (env.MILJO !== 'produktion') return svar('/tack/', 'demo');
  if (!env.DB) {  // produktion utan ärendelager är en felkonfiguration, aldrig ett tyst tack
    console.error('forfragan: ärendelagret (D1) saknas i produktionen');
    return felvy(raw, {}, 503, 'fel', OBEKRAFTAD, !!bild, t('inskick'));
  }
  const idem = await idempotens(t('inskick'), falt, bild);
  const redan = await befintlig(env, idem).catch(() => null);
  if (redan) return svar(redan.status === 'accepterad' ? '/tack/' : '/mottagen/', 'dubblett');
  const id = crypto.randomUUID(), nu = new Date().toISOString();
  let sparad;
  try { sparad = await spara(env, id, idem, falt, bild, nu); }
  catch (e) { console.error('forfragan: lagringen kunde inte bekräftas: ' + orsak(e)); }
  if (!sparad) return felvy(raw, {}, 503, 'fel', OBEKRAFTAD, !!bild, t('inskick'));
  if (sparad.dubblett) return svar(sparad.dubblett.status === 'accepterad' ? '/tack/' : '/mottagen/', 'dubblett');
  // Kundregistret efter svaret (ctx.waitUntil): besökaren väntar aldrig på det, och ett fel där påverkar inte svaret.
  if (kundregisterAktivt(env) && ctx && typeof ctx.waitUntil === 'function') ctx.waitUntil(tillKundregister(env, id, falt, !!bild));
  else if (kundregisterValt(env)) console.error('kundregister: valt men inte konfigurerat (PIPEDRIVE_TOKEN eller PIPEDRIVE_DOMAN saknas eller är ogiltigt)');
  if (!konfigurerad(env)) { console.error('forfragan: mejlmottagaren är inte konfigurerad'); return mottagen(); }
  // Avsikten före nätanropet: "skickar" utan slutläge efter ett avbrott är ett osäkert utfall, inte ett skäl att skicka igen.
  try { await utkorg(env, id, 'skickar'); } catch { return mottagen(); }
  try {
    const mejlId = await mejla(env, falt, bild);
    try { await utkorg(env, id, 'accepterad', { forsok: 1, mejl_id: mejlId }); }
    catch { console.error('forfragan: mejlet accepterades men utkorgen kunde inte uppdateras; stäm av mot mejltjänsten'); }
    return svar('/tack/', 'skickad');
  } catch (e) {
    // Nekat mejl är fel; allt annat (frist, internt fel, oläsbart kvitto) står kvar som skickar: utfallet är okänt och
    // stäms av mot mejltjänstens logg (Email sending metrics och logs) före ett nytt försök.
    try { await utkorg(env, id, e && e.nekad ? 'fel' : 'skickar', { forsok: 1, fel: orsak(e) }); }
    catch { console.error('forfragan: aviseringen föll och utkorgen kunde inte uppdateras'); }
    return mottagen();
  }
}

// Kundregistret (katalogens k10-pipedrive-lead; kunskap/integrationer.md, Kundregister): ett sparat ärende blir en person
// (namn och telefon), ett lead och en anteckning med meddelandet i verksamhetens Pipedrive. Pipedrive har ingen
// idempotensnyckel: raden i D1-tabellen kundregister skrivs före första anropet och efter varje steg, ett andra inskick av
// samma ärende stoppas redan som dubblett, och "skickar" utan slutläge stäms av i Pipedrive i stället för att skickas
// igen. Bara de tre skrivningarna görs, fast nyckeln (hemligheten PIPEDRIVE_TOKEN) ger åtkomst till mer. Bilden förs inte
// över. Aktivt bara i produktionen när kunden valt kundregistret (PIPEDRIVE_DOMAN och nyckeln).
const FRIST_KUNDREGISTER = 8000;
const kundregisterValt = (env) => env.MILJO === 'produktion' && Boolean(env.PIPEDRIVE_TOKEN || env.PIPEDRIVE_DOMAN);
const kundregisterAktivt = (env) => kundregisterValt(env) && Boolean(env.DB && env.PIPEDRIVE_TOKEN
  && /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(String(env.PIPEDRIVE_DOMAN || '')));

async function pipedrive(env, vag, kropp) {
  const r = await frist(fetch(`https://${env.PIPEDRIVE_DOMAN}.pipedrive.com${vag}`, { method: 'POST', body: JSON.stringify(kropp),
    headers: { 'x-api-token': env.PIPEDRIVE_TOKEN, 'content-type': 'application/json', accept: 'application/json' } }), FRIST_KUNDREGISTER, 'kundregistret');
  let d = null;
  try { d = await r.json(); } catch { /* oläsbart kvitto: obekräftat nedan */ }
  // Ett klientfel (utom 429) är ett slutligt nej: inget skapades. Allt annat utan kvitto är ett okänt utfall.
  if (r.status >= 400 && r.status < 500 && r.status !== 429) throw egen('kundregistret nekade (HTTP ' + r.status + ')', { nekad: true });
  const id = d && d.success === true && d.data ? d.data.id : null;
  if (!r.ok || (typeof id !== 'number' && typeof id !== 'string') || !/^[A-Za-z0-9-]{1,64}$/.test(String(id))) {
    throw egen('kundregistret bekräftade inte (HTTP ' + r.status + ')');
  }
  return String(id);
}

function kundregisterRad(env, id, status, falt = {}) {
  return frist(env.DB.prepare(`INSERT INTO kundregister (forfragan, status, person_id, lead_id, forsok, fel, uppdaterad) VALUES (?, ?, ?, ?, 1, ?, ?)
    ON CONFLICT(forfragan) DO UPDATE SET status = excluded.status, person_id = COALESCE(excluded.person_id, kundregister.person_id),
    lead_id = COALESCE(excluded.lead_id, kundregister.lead_id), fel = excluded.fel, uppdaterad = excluded.uppdaterad`)
    .bind(id, status, falt.person_id ?? null, falt.lead_id ?? null, falt.fel ?? null, new Date().toISOString()).run(), FRIST_LAGRING, 'kundregistrets rad');
}

async function tillKundregister(env, id, falt, medBild) {
  try { await kundregisterRad(env, id, 'skickar'); }
  catch { console.error('kundregister: raden kunde inte skrivas; inget skickas'); return; }
  const steg = {};
  try {
    steg.person_id = await pipedrive(env, '/api/v2/persons', { name: falt.namn, phones: [{ value: falt.telefon, primary: true, label: 'work' }] });
    await kundregisterRad(env, id, 'skickar', steg);
    steg.lead_id = await pipedrive(env, '/api/v1/leads', { title: `Förfrågan från webbplatsen: ${falt.namn.slice(0, 60)}`, person_id: Number(steg.person_id) });
    await kundregisterRad(env, id, 'skickar', steg);
    const text = esc(falt.meddelande).replace(/\n/g, '<br>');
    await pipedrive(env, '/api/v1/notes', { lead_id: steg.lead_id, content: `<p>${text}</p>${medBild ? '<p>En bild finns i ärendet på webbplatsen.</p>' : ''}<p>Ärende ${id}</p>` });
    await kundregisterRad(env, id, 'klar', steg);
  } catch (e) {
    // Bara ett nej innan något skapats är fel; annars står raden kvar som skickar med de id som hann sparas.
    const slut = e && e.nekad && !steg.person_id ? 'fel' : 'skickar';
    try { await kundregisterRad(env, id, slut, { ...steg, fel: orsak(e) }); }
    catch { console.error('kundregister: överföringen föll och raden kunde inte uppdateras'); }
  }
}

// Nyhetsbrevet (katalogens k14-brevo-dubbel; kunskap/integrationer.md, Nyhetsbrev): anmälan med dubbel bekräftelse
// hos Brevo (POST /v3/contacts/doubleOptinConfirmation). Workern sparar ingenting och skickar inget själv: Brevo
// skickar bekräftelsemejlet ur kundens mall och lägger kontakten i listan först när besökaren klickar på länken i det;
// avregistrering och spärr sköts i Brevo. Vägen finns i produktionen bara när kunden har valt nyhetsbrevet (någon av
// NYHETSBREV_LISTA, NYHETSBREV_MALL eller hemligheten BREVO_API_NYCKEL är satt; annars 404 som en okänd väg), och utanför
// produktionen anropas Brevo aldrig. Svaret säger aldrig om adressen redan fanns i listan.
const BREVO_DOI = 'https://api.brevo.com/v3/contacts/doubleOptinConfirmation';
const FRIST_NYHETSBREV = 8000;
const MAX_NYHETSBREV = 16384;
const EPOST = /^[^\s@<>()",;:\\[\]]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;
const ID = /^[1-9][0-9]{0,9}$/;
const nyhetsbrevValt = (env) => Boolean(env.BREVO_API_NYCKEL || env.NYHETSBREV_LISTA || env.NYHETSBREV_MALL);
const nyhetsbrevAktivt = (env) => Boolean(env.BREVO_API_NYCKEL && ID.test(String(env.NYHETSBREV_LISTA || '')) && ID.test(String(env.NYHETSBREV_MALL || '')));
const ANMALAN_OBEKRAFTAD = 'Vi kunde inte bekräfta anmälan just nu. Försök igen senare.';
const nyhetsbrevSvar = (utfall) => svar('/nyhetsbrev/skickad/', utfall, 'X-Nyhetsbrev');

function nyhetsbrevvy(epost, fel, status, utfall, besked) {
  const rad = (k) => fel[k] ? `<p class="fel" id="${k}-fel">${esc(fel[k])}</p>` : '';
  const attrs = (k) => fel[k] ? ` aria-invalid="true" aria-describedby="${k}-fel"` : '';
  const lista = Object.entries(fel).map(([k, v]) => `<li><a href="#${k}">${esc(v)}</a></li>`).join('');
  return sida('Anmälan till nyhetsbrevet', `<div class="sammanfattning"><p>${esc(besked)}</p>${lista ? `<ul>${lista}</ul>` : ''}</div>
  <form action="/api/nyhetsbrev/" method="post">
  <label for="epost">E-postadress</label><input id="epost" name="epost" type="email" autocomplete="email" required maxlength="254" value="${esc(epost)}"${attrs('epost')}>${rad('epost')}
  <label for="samtycke"><input id="samtycke" name="samtycke" type="checkbox" value="ja" required${attrs('samtycke')}> Jag vill få nyhetsbrevet och kan avregistrera mig när som helst.</label>${rad('samtycke')}
  <div class="falla" aria-hidden="true"><label for="webbplats">Lämna tomt</label><input id="webbplats" name="webbplats" tabindex="-1" autocomplete="off"></div>
  <p>Du får ett mejl med en länk som bekräftar anmälan. <a href="/integritet/">Så hanteras dina uppgifter</a>.</p>
  <button type="submit">Anmäl mig</button></form>`, status, utfall, 'X-Nyhetsbrev');
}

async function nyhetsbrev(request, env) {
  if (frammande(request)) return enkel(403, 'Anmälan kom från en annan webbplats och togs inte emot.');
  let result;
  try { result = await lasForm(request, MAX_NYHETSBREV); }
  catch { return nyhetsbrevvy('', {}, 400, 'ofullstandig', 'Vi kunde inte läsa formuläret. Försök igen.'); }
  if (result.forStor) return nyhetsbrevvy('', {}, 413, 'for-stor', 'Formuläret var för stort och kunde inte läsas. Försök igen.');
  const form = result.form;
  const t = (k) => typeof form.get(k) === 'string' ? form.get(k) : '';
  if (t('webbplats').trim()) return nyhetsbrevSvar('honeypot');
  const epost = t('epost').trim();
  const fel = {};
  if (epost.length > 254 || !EPOST.test(epost)) fel.epost = 'Skriv en giltig e-postadress.';
  if (t('samtycke') !== 'ja') fel.samtycke = 'Kryssa i rutan om du vill få nyhetsbrevet.';
  if (Object.keys(fel).length) return nyhetsbrevvy(epost, fel, 422, 'ofullstandig', 'Ingen anmälan har skickats. Rätta det markerade.');
  // Utanför produktionen anropas Brevo aldrig, också om en nyckel skulle finnas.
  if (env.MILJO !== 'produktion') return nyhetsbrevSvar('demo');
  if (!nyhetsbrevAktivt(env)) {  // valt men inte färdigkonfigurerat: ett synligt fel, aldrig ett tyst tack
    console.error('nyhetsbrev: nyckeln, listans eller mallens id saknas eller är ogiltigt');
    return nyhetsbrevvy(epost, {}, 503, 'inte-aktiverat', ANMALAN_OBEKRAFTAD);
  }
  const kropp = { email: epost, includeListIds: [Number(env.NYHETSBREV_LISTA)], templateId: Number(env.NYHETSBREV_MALL),
                  redirectionUrl: new URL('/nyhetsbrev/bekraftad/', request.url).href, contactPixelTrackingConsent: false };
  let r;
  try {
    r = await frist(fetch(BREVO_DOI, { method: 'POST', body: JSON.stringify(kropp),
      headers: { 'api-key': env.BREVO_API_NYCKEL, 'content-type': 'application/json', accept: 'application/json' } }), FRIST_NYHETSBREV, 'nyhetsbrevet');
  } catch (e) {
    console.error('nyhetsbrev: Brevo bekräftade inte anmälan: ' + orsak(e));
    return nyhetsbrevvy(epost, {}, 503, 'fel', ANMALAN_OBEKRAFTAD);
  }
  try { await r.body?.cancel(); } catch { /* svaret läses aldrig: leverantörens text loggas inte */ }
  if (r.status === 201 || r.status === 204) return nyhetsbrevSvar('skickad');
  console.error('nyhetsbrev: Brevo tog inte emot anmälan (HTTP ' + r.status + ')');
  return nyhetsbrevvy(epost, {}, 503, 'fel', ANMALAN_OBEKRAFTAD);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/api/nyhetsbrev/' && (env.MILJO !== 'produktion' || nyhetsbrevValt(env))) {
      if (request.method !== 'POST') return enkel(405, 'Endast POST.', { Allow: 'POST' });
      return nyhetsbrev(request, env);
    }
    if (url.pathname === '/api/forfragan/') {
      if (request.method !== 'POST') return enkel(405, 'Endast POST.', { Allow: 'POST' });
      return forfragan(request, env, ctx);
    }
    if (url.pathname === '/api/forfragan') return new Response(null, { status: 308, headers: { ...SAKERHET, Location: '/api/forfragan/' } });
    if (url.pathname.startsWith('/api/')) return enkel(404, 'Finns inte.');
    const svar = await env.ASSETS.fetch(request);
    if (env.MILJO === 'produktion') return svar;
    // Förhandsvisningen (wrangler.jsonc: run_worker_first för alla vägar där) indexeras aldrig; skyddet är ändå Access.
    const ny = new Response(svar.body, svar);
    ny.headers.set('X-Robots-Tag', 'noindex, nofollow');
    return ny;
  },
};
