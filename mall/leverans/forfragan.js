// Förfrågningsformulärets serverfunktion vid lansering (kunskap/forfragan.md, "Vid lansering"): samma kontrakt som
// demons mottagare. Sidan förrenderas inte; resten av sajten är statisk. Läggs i kundrepot av kontroller/exportera.py
// som src/pages/api/forfragan.js, med Vercel-adaptern.
//
// Ordningen: storlek → honeypot och tidsfälla → validering → lagring (privat Vercel Blob, före mejlet) → mejl (Resend)
// → 303 till /tack/. Svaret bär X-Forfragan med utfallet (demo, skickad, sparad, honeypot, ofullstandig, for-stor, fel),
// så att leveransprovet kan pröva funktionen genom riktiga HTTP-svar. Inga personuppgifter loggas.
export const prerender = false;

const MAX_BYTE = 4_400_000; // under Vercels gräns 4,5 MB för en funktions begäran (docs: Functions limits)
const MAX_BILD = 4_000_000;
const BILDTYPER = ['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/gif', 'image/avif'];

function svar(mal, utfall, status = 303, orsak = '') {
  const headers = { Location: mal, 'X-Forfragan': utfall, 'Cache-Control': 'no-store' };
  if (orsak) headers['X-Forfragan-Orsak'] = orsak.replace(/[^\w .:-]/g, '').slice(0, 120); // felets slag, aldrig fältens innehåll
  return new Response(null, { status, headers });
}

function miljo(namn) {
  return (typeof process !== 'undefined' && process.env ? process.env[namn] : undefined) || '';
}

async function spara(falt, bild) {
  // Privat Vercel Blob: lagret kopplas till projektet (BLOB_STORE_ID med OIDC, eller BLOB_READ_WRITE_TOKEN utanför Vercel).
  if (!miljo('BLOB_STORE_ID') && !miljo('BLOB_READ_WRITE_TOKEN')) return null;
  const { put } = await import('@vercel/blob');
  const tid = new Date().toISOString();
  const mapp = `forfragningar/${tid.slice(0, 10)}/${tid.replace(/[:.]/g, '')}-${crypto.randomUUID().slice(0, 8)}`;
  let bildvag = null;
  if (bild) {
    const r = await put(`${mapp}/${bild.name.replace(/[^\w.-]+/g, '_').slice(-80) || 'bild'}`, bild, { access: 'private', contentType: bild.type });
    bildvag = r.pathname;
  }
  const r = await put(`${mapp}/forfragan.json`, JSON.stringify({ ...falt, tid, bild: bildvag }), { access: 'private', contentType: 'application/json' });
  return r.pathname;
}

async function mejla(falt, bild) {
  const text = [`Namn: ${falt.namn}`, `Telefon: ${falt.telefon}`, '', falt.meddelande, '', bild ? `Bild: ${bild.name}` : 'Ingen bild'].join('\n');
  const kropp = {
    from: miljo('FORFRAGAN_FRAN'), to: miljo('FORFRAGAN_TILL').split(',').map((x) => x.trim()).filter(Boolean),
    subject: `Förfrågan från webbplatsen: ${falt.namn.slice(0, 60)}`, text,
  };
  if (bild) kropp.attachments = [{ filename: bild.name || 'bild', content: Buffer.from(await bild.arrayBuffer()).toString('base64') }];
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST', headers: { Authorization: `Bearer ${miljo('RESEND_API_KEY')}`, 'Content-Type': 'application/json' }, body: JSON.stringify(kropp),
  });
  if (!r.ok) throw new Error(`mejltjänsten svarade ${r.status}`);
}

export async function POST({ request }) {
  if (Number(request.headers.get('content-length') || 0) > MAX_BYTE) {
    return new Response('Förfrågan är för stor: bilden får vara högst 4 MB.', { status: 413, headers: { 'X-Forfragan': 'for-stor' } });
  }
  let form;
  try {
    form = await request.formData();
  } catch (e) {
    return svar('/kontakt/?saknas=1#forfragan-saknas', 'ofullstandig', 303, `formuläret gick inte att läsa: ${e && e.name}: ${e && e.message}`);
  }
  const t = (k) => String(form.get(k) ?? '').trim();
  if (t('webbplats')) return svar('/tack/', 'honeypot'); // honeypoten ifylld: tyst, som om det gick bra
  const fylltid = Number(t('fylltid') || 0);
  if (fylltid > 0 && fylltid < 1500) return svar('/tack/', 'honeypot'); // tidsfällan: för snabbt för en människa
  const falt = { namn: t('namn'), telefon: t('telefon'), meddelande: t('meddelande') };
  const giltig = falt.namn.length >= 1 && falt.namn.length <= 100 && falt.telefon.length >= 6 && falt.telefon.length <= 40
    && /\d/.test(falt.telefon) && falt.meddelande.length >= 1 && falt.meddelande.length <= 4000;
  if (!giltig) return svar('/kontakt/?saknas=1#forfragan-saknas', 'ofullstandig');
  const b = form.get('bild');
  const bild = b && typeof b === 'object' && b.size > 0 ? b : null;
  if (bild && (bild.size > MAX_BILD || !BILDTYPER.includes(bild.type))) return svar('/kontakt/?saknas=1#forfragan-saknas', 'ofullstandig');
  const konfigurerad = miljo('RESEND_API_KEY') && miljo('FORFRAGAN_TILL') && miljo('FORFRAGAN_FRAN');
  const lage = miljo('VERCEL_ENV') || 'development';
  if (!konfigurerad && lage !== 'production') return svar('/tack/', 'demo'); // förhandsvisning utan mottagare: inget skickas
  let sparad = null;
  try {
    sparad = await spara(falt, bild);
  } catch (e) {
    console.error('forfragan: lagringen föll', e && e.name);
  }
  if (!konfigurerad) {
    console.error('forfragan: mottagaren är inte konfigurerad i produktion (RESEND_API_KEY, FORFRAGAN_TILL, FORFRAGAN_FRAN)');
    return svar('/fel/', sparad ? 'sparad' : 'fel');
  }
  try {
    await mejla(falt, bild);
  } catch (e) {
    console.error('forfragan: mejlet föll', String(e && e.message).slice(0, 80));
    return svar('/fel/', sparad ? 'sparad' : 'fel');
  }
  return svar('/tack/', 'skickad');
}

export function ALL() {
  return new Response(null, { status: 405, headers: { Allow: 'POST' } });
}
