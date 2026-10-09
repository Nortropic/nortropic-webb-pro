// Kundsajtens Worker på Cloudflare Workers (ägarens beslut 2026-10-09: Cloudflare Workers är målplattform). Sidorna är
// förrenderade och serveras som Static Assets; bara vägarna under /api/ körs här (wrangler.jsonc, run_worker_first).
//
// Förfrågan (POST /api/forfragan/), även utan JavaScript:
// - valideringsfel återger texten i en skyddad felsida (422, 413, 400);
// - en förfrågan sparas beständigt i D1, och en bilaga privat i R2, före varje avisering; inget sparat ger 503 med texten kvar;
// - aviseringen är en utkorg i D1 (vantar → skickar → accepterad | fel): sparad men inte aviserad svarar 303 till den
//   förrenderade /mottagen/, och raden står kvar för uppföljning; "skickar" utan slut är ett osäkert utfall som stäms av
//   mot mejltjänsten före ett nytt försök, aldrig ett nytt mejl i blindo;
// - samma inskick två gånger (formulärets inskicks-id, annars innehållet inom tio minuter) blir ett ärende, inte två;
// - utanför produktionen (MILJO annat än produktion) sparas och skickas ingenting.
// Svar som Workern skapar får sina säkerhetshuvuden här; _headers gäller bara de statiska filerna.

const MAX_BYTE = 4_400_000;
const MAX_BILD = 4_000_000;
const BILDTYPER = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/gif', 'image/avif'];
const TOMT = { namn: '', telefon: '', meddelande: '' };
const RUBRIKER = { namn: 'Namn', telefon: 'Telefon', meddelande: 'Meddelande', bild: 'Bild' };
const RESEND = 'https://api.resend.com/emails';
const SAKERHET = {
  'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
  'Strict-Transport-Security': 'max-age=63072000; includeSubDomains', 'Cache-Control': 'no-store',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
};
const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' })[c]);

function svar(mal, utfall) {
  return new Response(null, { status: 303, headers: { ...SAKERHET, Location: mal, 'X-Forfragan': utfall } });
}

function enkel(status, text, extra = {}) {
  return new Response(text, { status, headers: { ...SAKERHET, 'Content-Type': 'text/plain; charset=utf-8', ...extra } });
}

function sida(rubrik, innehall, status, utfall) {
  const html = `<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>${esc(rubrik)}</title><style>
  *{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#242424;font:1rem/1.6 system-ui,sans-serif}main{max-width:42rem;margin:3rem auto;padding:0 1.25rem 3rem}h1{font-size:clamp(1.8rem,6vw,2.4rem);line-height:1.2}a{color:#163c78}label{display:block;font-weight:650;margin-top:1.5rem}input,textarea,button{font:inherit;max-width:100%}input,textarea{display:block;width:100%;border:1px solid #555;border-radius:.2rem;padding:.65rem;background:#fff;color:#242424}textarea{min-height:10rem;resize:vertical}button{padding:.7rem 1.3rem;background:#163c78;color:#fff;border:0;border-radius:.2rem;min-height:44px;margin-top:1.5rem;cursor:pointer}a:focus-visible,input:focus-visible,textarea:focus-visible,button:focus-visible{outline:3px solid #1c5ab3;outline-offset:3px}.fel{color:#a01818}.sammanfattning{border-left:4px solid #a01818;padding:1rem;background:#fff}.hjalp{font-size:.95rem}p,li{overflow-wrap:anywhere}.falla{display:none}input[type=file]{overflow-wrap:anywhere}
  </style></head><body><main><h1>${esc(rubrik)}</h1>${innehall}</main></body></html>`;
  return new Response(html, { status, headers: {
    ...SAKERHET, 'Content-Type': 'text/html; charset=utf-8', 'X-Forfragan': utfall, 'X-Robots-Tag': 'noindex, nofollow',
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
const giltigtInskick = (v) => typeof v === 'string' && /^[A-Za-z0-9-]{16,64}$/.test(v);
const kort = (e) => String((e && e.message) || e).slice(0, 200);

function konfigurerad(env) {
  return Boolean(env.RESEND_API_KEY && String(env.FORFRAGAN_TILL || '').split(',').some((x) => x.trim()) && env.FORFRAGAN_FRAN);
}

// Mejltjänstens adress: Resend i drift; en lokal provmottagare bara på 127.0.0.1 eller localhost (provet), aldrig en
// godtycklig adress ur konfigurationen.
function mejladress(env) {
  const prov = String(env.RESEND_API_URL || '');
  return /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?\//.test(prov) ? prov : RESEND;
}

async function lasForm(request) {
  // Mät också strömmen; frånvarande eller felaktig Content-Length får inte kringgå taket.
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTE) return { forStor: true };
  const reader = request.body?.getReader();
  if (!reader) throw new Error('Ingen kropp');
  const delar = []; let storlek = 0;
  try {
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      storlek += value.byteLength;
      if (storlek > MAX_BYTE) { await reader.cancel(); return { forStor: true }; }
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

// Idempotensnyckeln: formulärets inskicks-id (sätts i webbläsaren när sidan laddas), annars innehållet i ett tiominutersfönster,
// så att också ett inskick utan JavaScript som skickas igen efter ett tappat svar blir samma ärende.
async function idempotens(inskick, falt, bild) {
  if (giltigtInskick(inskick)) return 'i:' + inskick;
  const fonster = Math.floor(Date.now() / 600000);
  return 'h:' + await sha256([falt.namn, falt.telefon, falt.meddelande, bild ? `${bild.type}/${bild.size}` : '', fonster].join('\n'));
}

function base64(bytes) {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

async function befintlig(env, nyckel) {
  return env.DB.prepare('SELECT f.id AS id, u.status AS status FROM forfragningar f LEFT JOIN utkorg u ON u.forfragan = f.id WHERE f.nyckel = ?')
    .bind(nyckel).first();
}

async function radera(env, nyckel) {
  // Bästa försök. Misslyckas det står objektet kvar utan ärende och hittas av avstämningen (föräldralösa bilagor).
  try { await env.BILAGOR.delete(nyckel); } catch { console.error('forfragan: bilagan kunde inte tas bort efter ett fel'); }
}

async function spara(env, id, nyckel, falt, bild, nu) {
  let bilaga = null;
  if (bild) {
    bilaga = `forfragningar/${nu.slice(0, 10)}/${id}/bilaga`; // Klientens filnamn styr aldrig lagringsnamnet.
    const obj = await env.BILAGOR.put(bilaga, await bild.arrayBuffer(), {
      httpMetadata: { contentType: bild.type }, customMetadata: { forfragan: id },
    });
    if (!obj || obj.key !== bilaga) throw new Error('Bilagans lagringskvitto stämmer inte');
  }
  const dagar = Math.max(1, Number(env.GALLRING_DAGAR || 365));
  const gallras = new Date(Date.parse(nu) + dagar * 86400000).toISOString();
  let resultat;
  try {
    // En batch är en transaktion: ärendet och dess utkorgsrad finns båda eller ingen av dem.
    resultat = await env.DB.batch([
      env.DB.prepare(`INSERT INTO forfragningar (id, nyckel, mottagen, namn, telefon, meddelande, bilaga, bilaga_typ, bilaga_storlek, bilaga_namn, gallras)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(nyckel) DO NOTHING`)
        .bind(id, nyckel, nu, falt.namn, falt.telefon, falt.meddelande, bilaga, bild ? bild.type : null, bild ? bild.size : null,
          bild ? String(bild.name || '').slice(0, 200) : null, gallras),
      env.DB.prepare(`INSERT INTO utkorg (forfragan, status, forsok, uppdaterad) SELECT ?, 'vantar', 0, ? WHERE EXISTS (SELECT 1 FROM forfragningar WHERE id = ?)`)
        .bind(id, nu, id),
    ]);
  } catch (e) {
    if (bilaga) await radera(env, bilaga);
    throw e;
  }
  if (!resultat[0].meta.changes) {  // samma inskick hann före: det första ärendet gäller
    if (bilaga) await radera(env, bilaga);
    return { dubblett: await befintlig(env, nyckel) };
  }
  return { id, bilaga };
}

async function mejla(env, falt, bild, signal) {
  const text = [`Namn: ${falt.namn}`, `Telefon: ${falt.telefon}`, '', falt.meddelande, '', bild ? `Bild: ${bild.name || 'bild'}` : 'Ingen bild'].join('\n');
  const kropp = {
    from: env.FORFRAGAN_FRAN, to: String(env.FORFRAGAN_TILL).split(',').map((x) => x.trim()).filter(Boolean),
    subject: `Förfrågan från webbplatsen: ${falt.namn.slice(0, 60)}`, text,
  };
  if (bild) kropp.attachments = [{ filename: bild.name || 'bild', content: base64(new Uint8Array(await bild.arrayBuffer())) }];
  const r = await fetch(mejladress(env), {
    method: 'POST', signal, headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'Content-Type': 'application/json' }, body: JSON.stringify(kropp),
  });
  if (!r.ok) throw new Error('Mejltjänsten bekräftade inte mottagningen (' + r.status + ')');
  const kvitto = await r.json();
  if (!kvitto || Array.isArray(kvitto) || typeof kvitto.id !== 'string' || !/^[A-Za-z0-9_-]{1,256}$/.test(kvitto.id) || kvitto.error) throw new Error('Mejltjänstens kvitto stämmer inte');
  return kvitto.id;
}

async function utkorg(env, id, status, falt = {}) {
  const nu = new Date().toISOString();
  return env.DB.prepare(`UPDATE utkorg SET status = ?, forsok = forsok + ?, mejl_id = COALESCE(?, mejl_id), fel = ?, uppdaterad = ? WHERE forfragan = ?`)
    .bind(status, falt.forsok || 0, falt.mejl_id || null, falt.fel || null, nu, id).run();
}

async function forfragan(request, env) {
  const url = new URL(request.url);
  const origin = request.headers.get('origin');
  if (origin && origin !== url.origin) return enkel(403, 'Förfrågan kom från en annan webbplats och togs inte emot.');
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
  if (env.MILJO !== 'produktion' || !env.DB) return svar('/tack/', 'demo');
  const nyckel = await idempotens(t('inskick'), falt, bild);
  const redan = await befintlig(env, nyckel).catch(() => null);
  if (redan) return svar(redan.status === 'accepterad' ? '/tack/' : '/mottagen/', 'dubblett');
  const id = crypto.randomUUID(), nu = new Date().toISOString();
  let sparad;
  try { sparad = await spara(env, id, nyckel, falt, bild, nu); }
  catch (e) { console.error('forfragan: lagringen kunde inte bekräftas: ' + kort(e)); }
  if (!sparad) return felvy(raw, {}, 503, 'fel', 'Vi kunde inte bekräfta att förfrågan sparades. Texten finns kvar. Försök igen senare eller använd en annan kontaktväg.', !!bild, t('inskick'));
  if (sparad.dubblett) return svar(sparad.dubblett.status === 'accepterad' ? '/tack/' : '/mottagen/', 'dubblett');
  if (!konfigurerad(env)) { console.error('forfragan: mejlmottagaren är inte konfigurerad'); return mottagen(); }
  // Avsikten före nätanropet: "skickar" utan slutläge efter ett avbrott är ett osäkert utfall, inte ett skäl att skicka igen.
  try { await utkorg(env, id, 'skickar'); } catch { return mottagen(); }
  try {
    const mejlId = await mejla(env, falt, bild, AbortSignal.timeout(8000));
    try { await utkorg(env, id, 'accepterad', { forsok: 1, mejl_id: mejlId }); }
    catch { console.error('forfragan: mejlet accepterades men utkorgen kunde inte uppdateras; stäm av mot mejltjänsten'); }
    return svar('/tack/', 'skickad');
  } catch (e) {
    try { await utkorg(env, id, 'fel', { forsok: 1, fel: kort(e) }); }
    catch { console.error('forfragan: aviseringen föll och utkorgen kunde inte uppdateras'); }
    return mottagen();
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/api/forfragan/') {
      if (request.method !== 'POST') return enkel(405, 'Endast POST.', { Allow: 'POST' });
      return forfragan(request, env);
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
