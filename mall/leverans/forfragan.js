// Produktionsmottagare för vanlig POST, även utan JavaScript. Exporteras till kundrepot.
// Valideringsfel återger texten i en skyddad felsida. Bara ett lagringskvitto får följas
// av mejl. Mottaget men ej aviserat skiljs från mottagning som inte kunde bekräftas.
// Ingen idempotensgaranti: ett helt tappat första svar kan ännu ge dubbla inskick.
export const prerender = false;

const MAX_BYTE = 4_400_000;
const MAX_BILD = 4_000_000;
const BILDTYPER = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/gif', 'image/avif'];
const TOMT = { namn: '', telefon: '', meddelande: '' };
const RUBRIKER = { namn: 'Namn', telefon: 'Telefon', meddelande: 'Meddelande', bild: 'Bild' };
const esc = (v) => String(v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' })[c]);

function svar(mal, utfall) {
  return new Response(null, { status: 303, headers: {
    Location: mal, 'X-Forfragan': utfall, 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
  } });
}

function sida(rubrik, innehall, status, utfall) {
  const html = `<!doctype html><html lang="sv"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>${esc(rubrik)}</title><style>
  *{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#242424;font:1rem/1.6 system-ui,sans-serif}main{max-width:42rem;margin:3rem auto;padding:0 1.25rem 3rem}h1{font-size:clamp(1.8rem,6vw,2.4rem);line-height:1.2}a{color:#163c78}label{display:block;font-weight:650;margin-top:1.5rem}input,textarea,button{font:inherit;max-width:100%}input,textarea{display:block;width:100%;border:1px solid #555;border-radius:.2rem;padding:.65rem;background:#fff;color:#242424}textarea{min-height:10rem;resize:vertical}button{padding:.7rem 1.3rem;background:#163c78;color:#fff;border:0;border-radius:.2rem;min-height:44px;margin-top:1.5rem;cursor:pointer}a:focus-visible,input:focus-visible,textarea:focus-visible,button:focus-visible{outline:3px solid #1c5ab3;outline-offset:3px}.fel{color:#a01818}.sammanfattning{border-left:4px solid #a01818;padding:1rem;background:#fff}.hjalp{font-size:.95rem}p,li{overflow-wrap:anywhere}.falla{display:none}input[type=file]{overflow-wrap:anywhere}
  </style></head><body><main><h1>${esc(rubrik)}</h1>${innehall}</main></body></html>`;
  return new Response(html, { status, headers: {
    'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Forfragan': utfall,
    'X-Robots-Tag': 'noindex, nofollow', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
  } });
}

function felvy(falt, fel, status, utfall, besked, bildVald = false) {
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
  <div class="falla" aria-hidden="true"><label for="webbplats">Lämna tomt</label><input id="webbplats" name="webbplats" tabindex="-1" autocomplete="off"></div><input type="hidden" name="fylltid" value="0">
  <p>Uppgifterna används för att besvara din förfrågan. <a href="/integritet/">Så hanteras dina uppgifter</a>.</p>
  <button type="submit">Skicka förfrågan</button></form><p><a href="/kontakt/">Andra kontaktvägar</a></p>`, status, utfall);
}

function mottagen() {
  return sida('Förfrågan är mottagen', '<p>Din förfrågan är sparad, men mejlaviseringen till verksamheten kunde inte bekräftas.</p><p>Du behöver inte skicka formuläret igen. Om du behöver nå verksamheten direkt finns <a href="/kontakt/">andra kontaktvägar</a>.</p>', 202, 'sparad');
}

function miljo(namn) {
  return (typeof process !== 'undefined' && process.env ? process.env[namn] : undefined) || '';
}

async function tidsatt(ms, arbete) {
  const controller = new AbortController();
  let timer;
  const stopp = new Promise((_, reject) => {
    timer = setTimeout(() => {
      const fel = new Error('Leverantörens tidsgräns nåddes');
      controller.abort(fel); reject(fel);
    }, ms);
  });
  try { return await Promise.race([arbete(controller.signal), stopp]); }
  finally { clearTimeout(timer); }
}

async function spara(falt, bild, signal) {
  if (!miljo('BLOB_STORE_ID') && !miljo('BLOB_READ_WRITE_TOKEN')) return null;
  const { put } = await import('@vercel/blob');
  signal.throwIfAborted();
  const tid = new Date().toISOString();
  const mapp = `forfragningar/${tid.slice(0, 10)}/${tid.replace(/[:.]/g, '')}-${crypto.randomUUID().slice(0, 8)}`;
  let bildvag = null;
  if (bild) {
    const vag = `${mapp}/bilaga/bild`; // Klientens filnamn styr aldrig lagringsnamnet.
    const r = await put(vag, bild, { access: 'private', contentType: bild.type, addRandomSuffix: false, allowOverwrite: false, abortSignal: signal });
    signal.throwIfAborted();
    if (!r || r.pathname !== vag) throw new Error('Bildens lagringskvitto stämmer inte');
    bildvag = r.pathname;
  }
  const vag = `${mapp}/forfragan.json`;
  const r = await put(vag, JSON.stringify({ schema: 1, ...falt, tid, bild: bildvag, avisering: 'inte_bekraftad' }), { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: false, abortSignal: signal });
  signal.throwIfAborted();
  return r && r.pathname === vag ? r.pathname : null;
}

async function mejla(falt, bild, signal) {
  const text = [`Namn: ${falt.namn}`, `Telefon: ${falt.telefon}`, '', falt.meddelande, '', bild ? `Bild: ${bild.name}` : 'Ingen bild'].join('\n');
  const kropp = {
    from: miljo('FORFRAGAN_FRAN'), to: miljo('FORFRAGAN_TILL').split(',').map((x) => x.trim()).filter(Boolean),
    subject: `Förfrågan från webbplatsen: ${falt.namn.slice(0, 60)}`, text,
  };
  if (bild) kropp.attachments = [{ filename: bild.name || 'bild', content: Buffer.from(await bild.arrayBuffer()).toString('base64') }];
  signal.throwIfAborted();
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST', signal, headers: { Authorization: `Bearer ${miljo('RESEND_API_KEY')}`, 'Content-Type': 'application/json' }, body: JSON.stringify(kropp),
  });
  signal.throwIfAborted();
  if (!r.ok) throw new Error('Mejltjänsten bekräftade inte mottagningen');
  const kvitto = await r.json();
  signal.throwIfAborted();
  if (!kvitto || Array.isArray(kvitto) || typeof kvitto.id !== 'string' || !/^[A-Za-z0-9_-]{1,256}$/.test(kvitto.id) || kvitto.error) throw new Error('Mejltjänstens kvitto stämmer inte');
  return kvitto.id;
}

async function sparaAvisering(mottagningsfil, id, signal) {
  // Ett separat kvitto lämnar mottagningsfilen orörd. Saknat kvitto betyder okänt,
  // aldrig att ett mejl säkert saknas: kontrollera leverantören före manuell omsändning.
  const { put } = await import('@vercel/blob');
  signal.throwIfAborted();
  const vag = mottagningsfil.replace(/forfragan\.json$/, 'avisering.json');
  const r = await put(vag, JSON.stringify({ schema: 1, mottagningsfil, id, tid: new Date().toISOString(), utfall: 'accepterat_av_mejltjansten' }),
    { access: 'private', contentType: 'application/json', addRandomSuffix: false, allowOverwrite: false, abortSignal: signal });
  signal.throwIfAborted();
  if (!r || r.pathname !== vag) throw new Error('Aviseringens lagringskvitto stämmer inte');
}

async function lasForm(request) {
  // Mät också strömmen; frånvarande eller felaktig Content-Length får inte kringgå taket.
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTE) return { forStor: true };
  const reader = request.body?.getReader();
  if (!reader) throw new Error('Ingen kropp');
  const chunks = []; let storlek = 0;
  try {
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      storlek += value.byteLength;
      if (storlek > MAX_BYTE) { await reader.cancel(); return { forStor: true }; }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const kropp = new Blob(chunks);
  const ny = new Request(request.url, { method: 'POST', headers: { 'content-type': request.headers.get('content-type') || '' }, body: kropp });
  return { form: await ny.formData() };
}

export async function POST({ request }) {
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
  const falt = Object.fromEntries(Object.entries(raw).map(([k,v]) => [k,v.replace(/\r\n?/g, '\n').trim()]));
  const fel = {};
  if (!falt.namn || falt.namn.length > 100) fel.namn = 'Skriv ditt namn, högst 100 tecken.';
  if (!/^[0-9+\-() ]{6,40}$/.test(falt.telefon) || !/\d/.test(falt.telefon)) fel.telefon = 'Skriv ett telefonnummer med 6–40 tecken: siffror, mellanslag, +, bindestreck eller parenteser.';
  if (!falt.meddelande || falt.meddelande.length > 4000) fel.meddelande = 'Skriv ett meddelande, högst 4 000 tecken.';
  const b = form.get('bild');
  const bild = b && typeof b === 'object' && b.size > 0 ? b : null;
  let status = 422, utfall = 'ofullstandig';
  if (bild && bild.size > MAX_BILD) { fel.bild = 'Bilden är för stor. Högst 4 MB.'; status = 413; utfall = 'for-stor'; }
  else if (bild && !BILDTYPER.includes(bild.type)) fel.bild = 'Välj en bild i något av de angivna formaten.';
  if (Object.keys(fel).length) return felvy(raw, fel, status, utfall, 'Inget har skickats. Rätta de markerade fälten; texten finns kvar.', !!bild);
  const konfigurerad = miljo('RESEND_API_KEY') && miljo('FORFRAGAN_TILL').split(',').some(x => x.trim()) && miljo('FORFRAGAN_FRAN');
  // Utanför produktionen (förhandsvisning, utveckling) sparas och skickas aldrig något, också när mejl- och lagringsvariablerna
  // råkar gälla alla miljöer (GR-20261008-r117-claude#D2): ett riktigt mejl ur en förhandsvisning vore ett fel (driftkoll.py).
  if (miljo('VERCEL_ENV') !== 'production') return svar('/tack/', 'demo');
  let sparad = null;
  try { sparad = await tidsatt(10000, signal => spara(falt, bild, signal)); }
  catch { console.error('forfragan: lagringen kunde inte bekräftas'); }
  if (!sparad) return felvy(raw, {}, 503, 'fel', 'Vi kunde inte bekräfta att förfrågan sparades. Texten finns kvar. Försök igen senare eller använd en annan kontaktväg.', !!bild);
  if (!konfigurerad) { console.error('forfragan: mejlmottagaren är inte konfigurerad'); return mottagen(); }
  let mejlid;
  try { mejlid = await tidsatt(8000, signal => mejla(falt, bild, signal)); }
  catch { console.error('forfragan: mejlaviseringen kunde inte bekräftas'); return mottagen(); }
  try { await tidsatt(2000, signal => sparaAvisering(sparad, mejlid, signal)); }
  catch { console.error('forfragan: mejlet accepterades men aviseringskvittot kunde inte sparas; kontrollera lagrade ärenden manuellt'); }
  return svar('/tack/', 'skickad');
}

export function ALL() {
  return new Response(null, { status: 405, headers: { Allow: 'POST' } });
}
