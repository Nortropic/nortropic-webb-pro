// Arbetsytan (ägarens uppdrag 2026-10-09; kunskap/arbetsyta.md): samtal, riktig förhandsvisning, rollsessioner, byggflöde och
// kod på ett ställe, över samma läge (dashboard/arbetsyta.py) och samma identiteter. Läget kommer som en ström; vyn räknar
// inga egna statusar, startar inget av sig själv och visar det som saknas som okänt. Skrivningar går med dashboardnyckeln
// (post i index.html): partnerns meddelanden, ägarens ändringar och flödets befintliga start (samma start-id som Flöde).
(() => {
  const A = { slug: null, vy: '', lage: null, projekt: [], strom: null, anslutning: 'ansluter', senastLast: null, avbrott: null,
    valdKandidat: null, material: null, enhet: 'dator', folj: null, partner: null, partnerNyckel: null, avsikt: 'fraga',
    kod: { kandidat: null, fil: null, mot: null, visning: 'diff', data: null, fildata: null }, logg: null, loggNyckel: null,
    bekrafta: null, svar: '', metod: null, generation: 0, inaktuellTimer: null, pollTimer: null };
  const LAGESNAMN = { ny: 'ny utforskning', om: 'ny körning', valda: 'uppdrag', putsa: 'putsning', forbered: 'förberedelse', fortsatt: 'återupptagen' };
  const LAGEN = { vantar: 'väntar på start', startar: 'start pågår', aktiv: 'arbetar', verktyg: 'väntar på verktyg', beslut: 'väntar på ditt beslut',
    avslutad: 'avslutad', avbruten: 'avbruten', okant: 'okänt läge' };
  const IKON = {
    aktiv: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="currentColor"/></svg>',
    verktyg: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    startar: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="2.5" cy="6" r="1.4" fill="currentColor"/><circle cx="6" cy="6" r="1.4" fill="currentColor"/><circle cx="9.5" cy="6" r="1.4" fill="currentColor"/></svg>',
    vantar: '<svg viewBox="0 0 12 12" aria-hidden="true"><circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M6 3.5V6l1.8 1.2" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    beslut: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 11V1.5h6L7.5 4 9 6.5H3" fill="none" stroke="currentColor" stroke-width="1.4"/></svg>',
    avslutad: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2 6.3l2.6 2.6L10 3.5" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>',
    avbruten: '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 3l6 6M9 3L3 9" stroke="currentColor" stroke-width="1.8"/></svg>',
    okant: '<svg viewBox="0 0 12 12" aria-hidden="true"><text x="6" y="9.5" text-anchor="middle" font-size="9" font-weight="700" fill="currentColor">?</text></svg>',
  };
  const SVG = {
    marke: '<svg viewBox="0 0 26 26" aria-hidden="true"><rect width="26" height="26" rx="6" fill="#1d2431"/><path d="M7 19V7l12 12V7" fill="none" stroke="#e7ebf1" stroke-width="2.4" stroke-linejoin="round"/></svg>',
    vanster: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M6 3v10" stroke="currentColor" stroke-width="1.3"/></svg>',
    hoger: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="10" rx="2" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M10 3v10" stroke="currentColor" stroke-width="1.3"/></svg>',
    lank: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M9 3h4v4M13 3L7 9M11 9v4H3V5h4" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>',
    ladda: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 8a5 5 0 1 1-1.5-3.6M13 3v3h-3" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>',
  };
  const e_ = (s) => (typeof esc === 'function' ? esc(s) : String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
  const klocka = (t) => { if (!t) return '–'; const d = new Date(t); return isNaN(d) ? '–' : d.toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }); };
  const kort = (t) => { if (!t) return '–'; const d = new Date(t); return isNaN(d) ? '–' : d.toLocaleString('sv-SE', { dateStyle: 'short', timeStyle: 'short' }); };
  const sedan = (t) => { if (!t) return 'inte observerat'; const m = Math.floor((Date.now() - new Date(t)) / 60000); return m < 1 ? 'nyss' : m < 60 ? `för ${m} min sedan` : kort(t); };
  const roll = (s) => s.roll_dold ? (s.ansvar === 'granskning' ? 'Granskare' : 'Utförare') : s.roll === 'partner' ? 'Nortropic-partnern' : s.roll === 'helbygge' ? 'Helbygget' : (typeof rollnamn === 'function' ? rollnamn(s.roll) : s.roll) || 'roll inte observerad';
  const etikett = (kid) => ((A.lage?.kandidater || []).find((k) => k.id === kid) || {}).etikett || kid;
  const lagechip = (l, text) => `<span class="ay-lage" data-lage="${e_(l)}" title="${e_(text || '')}">${IKON[l] || IKON.okant}${e_(LAGEN[l] || l || 'okänt')}</span>`;
  const lager = (slug) => `nwp-arbetsyta:${slug}`;
  function layout(slug) { try { return JSON.parse(localStorage.getItem(lager(slug)) || '{}') || {}; } catch { return {}; } }
  function sparaLayout(andring) { if (!A.slug) return; const l = Object.assign(layout(A.slug), andring); try { localStorage.setItem(lager(A.slug), JSON.stringify(l)); } catch { /* bara en bekvämlighet */ } }
  function meddela(text) { const r = document.getElementById('ay-meddelande'); if (!r || !text) return; r.textContent = ''; setTimeout(() => { r.textContent = text; }, 60); }
  function nyttId(nyckel) { let id; try { id = sessionStorage.getItem(nyckel); } catch { id = null; } if (!id) { id = crypto.randomUUID(); try { sessionStorage.setItem(nyckel, id); } catch { /* utan lagring: ett nytt id per klick */ } } return id; }
  async function innehallsId(prefix, delar) {
    const b = new TextEncoder().encode(JSON.stringify(delar));
    const h = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', b))).map((x) => x.toString(16).padStart(2, '0')).join('');
    return prefix + h.slice(0, 40);
  }
  function slappId(nyckel, id) { try { if (sessionStorage.getItem(nyckel) === id) sessionStorage.removeItem(nyckel); } catch { /* inget att släppa */ } }
  async function postJson(url, body, ms = 45000) {
    const avbryt = new AbortController(), t = setTimeout(() => avbryt.abort(), ms);
    let r;
    try { r = await fetch(url, { method: 'POST', signal: avbryt.signal, headers: { 'Content-Type': 'application/json', 'X-Nyckel': (typeof nyckel === 'function' ? nyckel() : '') }, body: JSON.stringify(body) }); }
    catch (err) { throw new Error(err?.name === 'AbortError' ? `inget svar inom ${ms / 1000} s (begäran kan ha tagits emot)` : (err?.message || String(err))); }
    finally { clearTimeout(t); }
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { const fel = new Error(j.fel || ('HTTP ' + r.status)); fel.status = r.status; fel.slag = j.slag; throw fel; }
    return j;
  }
  async function hamta(url) { const r = await fetch(url, { cache: 'no-store' }); const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.fel || ('HTTP ' + r.status)); return j; }

  // --- ingången ---
  window.arbetsytavy = async function arbetsytavy(rest) {
    const [slug, vy] = String(rest || '').split('/');
    document.body.classList.add('ay-aktiv');
    if (typeof aktivNav === 'function') aktivNav('arbetsyta');
    const gen = ++A.generation;
    A.fokusDel = false;
    let lista;
    try { lista = await hamta('/api/arbetsyta'); } catch (err) { if (gen === A.generation) visaFel('Arbetsytan kunde inte läsa kunderna: ' + err.message); return; }
    if (gen !== A.generation) return;
    A.projekt = lista.projekt || [];
    if (!slug) {
      if (!A.projekt.length) { tomtLage(); return; }
      location.replace('#/arbetsyta/' + encodeURIComponent((A.projekt.find((p) => p.slug === localStorageSenaste()) || A.projekt[0]).slug));
      return;
    }
    if (!A.projekt.some((p) => p.slug === slug)) { visaFel(`Arbetsytan känner inte till kunden ${slug}. Välj en kund i listan.`); return; }
    const byte = A.slug !== slug;
    A.vy = ['flode', 'kod', 'forslag'].includes(vy) ? vy : '';
    if (byte) { stangStrom(); Object.assign(A, { mark: undefined, slug, lage: null, valdKandidat: null, folj: null, partner: null, partnerNyckel: null, material: null, logg: null, loggNyckel: null, svar: '', kod: { kandidat: null, fil: null, mot: null, visning: 'diff', data: null, fildata: null } }); }
    try { localStorage.setItem('nwp-arbetsyta:senaste', slug); } catch { /* bekvämlighet */ }
    const l = layout(slug);
    A.enhet = l.enhet === 'mobil' ? 'mobil' : 'dator';
    ram();
    ritaRaknare();
    if (A.lage) rita(); else {
      let d;
      try { d = await hamta('/api/arbetsyta/' + encodeURIComponent(slug)); } catch (err) { if (gen === A.generation) visaFel('Läget kunde inte läsas: ' + err.message); return; }
      if (gen !== A.generation || A.slug !== slug) return;  // ägaren har gått vidare under läsningen
      tillampa(d, true);
    }
    if (A.vy === 'forslag' && gen === A.generation) laddaForslagen();
    if (!A.strom && !A.pollTimer && A.slug === slug) oppnaStrom(slug);
  };
  function localStorageSenaste() { try { return localStorage.getItem('nwp-arbetsyta:senaste'); } catch { return null; } }

  function tomtLage() {
    A.vy = ''; A.sektion = null;
    document.getElementById('rot').innerHTML = `<div class="ay">${huvudTom()}${flikrad()}<main class="ay-tom" style="padding:40px 18px">Inga kunder med underlag än. Starta ett ärende i <a href="#/kundstart">Kundstart</a> eller förbered en kund under <a href="#/starta">Starta</a>.</main></div>`;
    ritaRaknare();
  }
  function visaFel(text) {
    const v = document.getElementById('rot');
    if (A.vy === 'sektion' || !v.querySelector('.ay')) { A.vy = ''; A.sektion = null; v.innerHTML = `<div class="ay">${huvudTom()}${flikrad()}</div>`; }
    const ruta = v.querySelector('.ay-felruta') || Object.assign(document.createElement('div'), { className: 'ay-felruta' });
    ruta.innerHTML = `<div class="ay-notis fel" role="alert" style="margin:12px 18px">${e_(text)}</div>`;
    v.querySelector('.ay').prepend(ruta);
  }
  const huvudTom = () => `<header class="ay-huvud"><div class="ay-marke">${SVG.marke}Nortropic arbetsyta</div></header>`;

  // --- strömmen ---
  function oppnaStrom(slug) {
    if (!window.EventSource) { A.pollTimer = setInterval(async () => { try { tillampa(await hamta('/api/arbetsyta/' + encodeURIComponent(slug))); satt('ansluten'); } catch { satt('ateransluter'); } }, 5000); return; }
    const es = new EventSource('/api/arbetsyta/' + encodeURIComponent(slug) + '/strom');
    A.strom = es;
    es.addEventListener('lage', (ev) => { if (A.strom !== es) return; try { tillampa(JSON.parse(ev.data)); } catch { /* en trasig händelse ersätts av nästa */ } });
    es.addEventListener('puls', (ev) => { if (A.strom !== es) return; try { A.senastLast = JSON.parse(ev.data).tid; } catch { /* */ } ritaAnslutning(); });
    es.addEventListener('fel', (ev) => { if (A.strom !== es) return; let d = {}; try { d = JSON.parse(ev.data); } catch { /* */ } A.lasfel = d; ritaAnslutning(); });
    es.onopen = () => {
      if (A.strom !== es) return;
      if (A.avbrott) meddela(`Anslutningen är tillbaka. Luckan ${klocka(A.avbrott)}–${klocka(new Date().toISOString())}; läget är omläst.`);
      A.luckor = A.avbrott ? [...(A.luckor || []).slice(-2), { fran: A.avbrott, till: new Date().toISOString() }] : A.luckor;
      A.avbrott = null; clearTimeout(A.inaktuellTimer); satt('ansluten');
    };
    es.onerror = () => {
      if (A.strom !== es) return;
      if (!A.avbrott) { A.avbrott = new Date().toISOString(); satt('ateransluter'); clearTimeout(A.inaktuellTimer); A.inaktuellTimer = setTimeout(() => { if (A.avbrott) { satt('inaktuellt'); meddela('Anslutningen till dashboarden är bruten; läget som visas kan vara inaktuellt. Arbetet påverkas inte.'); } }, 12000); }
      // ett felsvar på återanslutningen (503 vid för många strömmar, 403) stänger EventSource för gott och webbläsaren
      // försöker aldrig igen: vyn öppnar då en ny ström efter serverns retry-tid, tills kunden byts eller vyn lämnas
      if (es.readyState === EventSource.CLOSED) { clearTimeout(A.omTimer); A.omTimer = setTimeout(() => { if (A.strom === es && A.slug === slug) oppnaStrom(slug); }, 3000); }
    };
  }
  function stangStrom() { if (A.strom) { A.strom.close(); A.strom = null; } clearInterval(A.pollTimer); A.pollTimer = null; clearTimeout(A.inaktuellTimer); clearTimeout(A.omTimer); }
  function satt(l) { A.anslutning = l; ritaAnslutning(); }

  // --- läget kommer in ---
  function tillampa(d, forsta) {
    if (!d || d.slug !== A.slug) return;
    const fore = A.lage;
    A.lage = d; A.senastLast = d.tid; A.lasfel = null;
    if (!forsta && fore) overgangar(fore, d);
    if (!A.valdKandidat) {
      const ks = d.kandidater || [];
      A.valdKandidat = (ks.find((k) => k.preview.finns) || ks.find((k) => k.snapshot['1440'] || k.snapshot['390']) || {}).id || null;
    }
    const pn = JSON.stringify(d.partner?.senaste || null);
    if (pn !== A.partnerNyckel) { A.partnerNyckel = pn; laddaPartner(); }
    const sn = JSON.stringify([d.samverkan?.nyckel, d.blind, d.korning?.startad]);
    if (sn !== A.samverkanNyckel) { A.samverkanNyckel = sn; laddaSamverkan(); }
    rita();
  }
  function overgangar(f, n) {
    const fs = Object.fromEntries((f.sessioner || []).map((s) => [s.session_id, s]));
    const ut = [];
    for (const s of n.sessioner || []) {
      const g = fs[s.session_id];
      const vem = roll(s) + (s.kandidat ? ' för ' + etikett(s.kandidat) : '');
      if (!g && s.session_id) ut.push(`${vem} startade`);
      else if (g && g.lage !== s.lage && ['avslutad', 'avbruten', 'beslut'].includes(s.lage)) ut.push(`${vem}: ${LAGEN[s.lage]}`);
    }
    if (!f.korning?.vantar_pa_agaren && n.korning?.vantar_pa_agaren) ut.push('Körningen väntar på ditt beslut');
    if (f.korning?.startad !== n.korning?.startad && n.korning?.startad) ut.push('En ny körning har startat');
    if (ut.length) meddela(ut.slice(0, 3).join('. ') + '.');
  }

  // --- ramen ---
  function ram() {
    const v = document.getElementById('rot');
    const l = layout(A.slug);
    v.innerHTML = `<div class="ay" data-vy="${e_(A.vy)}"${A.vy === 'sektion' ? ` data-sektion="${e_(A.sektion)}"` : ''}>
      <header class="ay-huvud" id="ay-huvud">${huvudTom().replace(/^<header[^>]*>|<\/header>$/g, '')}</header>
      ${flikrad()}
      <p id="ay-meddelande" class="dolt" role="status" aria-live="polite" aria-atomic="true"></p>
      <main id="ay-innehall">${A.vy === 'sektion' ? '<div id="vy" class="ay-sektion"><p class="under">Laddar …</p></div>'
        : A.vy === 'forslag' ? '<div id="ay-forslagsnotis"></div><div id="vy" class="ay-sektion ay-forslagen"><p class="under">Laddar förslagen …</p></div>' : A.vy === 'flode' ? '<div class="ay-flode" id="ay-flode"></div>' : A.vy === 'kod' ? kodRam() : ytRam(l)}</main>
    </div>`;
    if (A.vy === '') kopplaDelare();
    if (A.vy === 'kod') laddaKod();
    if (A.vy === 'forslag') A.forslagNyckel = undefined;  // vyn är inte ritad än
  }
  // Arbetsytans delar utöver projektets tre vyer (ägarens besked 2026-10-09 ~17:11Z: allt ska in i arbetsytan). Adresserna
  // är desamma som förut (#/backlog, #/kundstart/<id> …), så länkar, bokmärken och vyernas egna kontroller av adressen
  // gäller; varje del ritas i arbetsytans ram med samma funktioner och skrivvägar som förut. Kundproduktionen och
  // systemförbättringen hålls isär (uppdraget 2026-10-09 ~07:24Z).
  const DELAR = [
    ['Kundproduktion', [['oversikt', 'Byggen och dina domar', 'helbyggena, deras prov och din dom'], ['ab', 'Jämförelser', 'blinda par: välj utan att veta vilket som är vilket'],
      ['kundstart', 'Kundstart', 'kundens ärende, underlag och överlämning'], ['prospekt', 'Prospekt', 'kampanjer, analyser och utskick', false, 'n-prospekt'],
      ['starta', 'Starta', 'kommandona för helbygge, backlog och prov']]],
    ['Systemförbättring', [['underhall', 'Underhåll och verktygslådan', 'det dagliga underhållet och versionerna'], ['kirurgen', 'Kirurgen', 'intag, spaningen och förbättringsarbetet', false, 'n-kirurg'],
      ['backlog', 'Backlog', 'vilande, pågående och klara poster', false, 'n-backlog'], ['kalibrering', 'Kalibrering', 'externa sajter att döma blint'],
      ['lardomar', 'Lärdomar', 'dina domar och granskarnas samstämmighet'], ['designprov', 'Designprov', 'ateljéns förslag per bygge, blint']]],
  ];
  const DELNAMN = Object.fromEntries([...DELAR.flatMap(([, d]) => d), ['dokumentation', 'Dokumentation och rapporter'], ['bygge', 'Bygget och din dom']].map(([k, n]) => [k, n]));
  function flikrad() {
    const del = A.vy === 'sektion' ? (A.sektion === 'bygge' ? 'oversikt' : A.sektion) : null;
    const sl = A.slug ? encodeURIComponent(A.slug) : '';
    const href = (k, projekt) => `#/${k}${projekt && sl ? '/' + sl : ''}`;
    const post = ([k, n, om, projekt, raknare]) => `<a href="${href(k, projekt)}" data-v="${k}"${del === k ? ' aria-current="page"' : ''}><span>${n}${raknare ? ` <b id="${raknare}" hidden></b>` : ''}</span><span class="ay-menyom">${om}</span></a>`;
    return `<div class="ay-flikrad">
        <nav aria-label="Arbetsytans vyer" class="ay-projektflikar">${[['', 'Arbetsyta'], ['forslag', 'Förslagen'], ['flode', 'Byggflöde'], ['kod', 'Kod och preview']].map(([k, n]) =>
          `<a href="#/arbetsyta${sl ? '/' + sl : ''}${k && sl ? '/' + k : ''}"${A.vy === k ? ' aria-current="page"' : ''}>${n}</a>`).join('')}</nav>
        <nav aria-label="Arbetsytans delar" class="ay-delar">${DELAR.map(([grupp, delar]) => { const har = delar.some(([k]) => k === del);
          return `<details class="ay-meny"><summary${har ? ' data-aktiv' : ''}>${grupp}${har ? `<span class="ay-meny-val">: ${e_(DELNAMN[A.sektion])}</span>` : ''}</summary>
          <div class="ay-menylista">${delar.map(post).join('')}</div></details>`; }).join('')}<a href="#/dokumentation" data-v="dokumentation"${del === 'dokumentation' ? ' aria-current="page"' : ''}>Dokumentation<span class="ay-lang"> och rapporter</span></a></nav>
      </div>`;
  }
  window.arbetsytaSektion = function arbetsytaSektion(h) {
    const [forsta, andra] = String(h || '').split('/');
    const sektion = DELNAMN[forsta] ? forsta : 'oversikt';
    document.body.classList.add('ay-aktiv');
    const gen = ++A.generation;  // en pågående läsning av en vy ger inte längre ramen
    let slug = forsta === 'bygge' && andra ? decodeURIComponent(andra) : (A.slug || localStorageSenaste());
    if (A.projekt.length && slug && !A.projekt.some((p) => p.slug === slug)) slug = A.projekt.some((p) => p.slug === A.slug) ? A.slug : null;  // ett bygge utan arbetsyta behåller kunden i huvudet
    bytKund(slug);
    A.vy = 'sektion'; A.sektion = sektion;
    ram();
    rita();
    ritaRaknare();
    if (A.fokusDel) { A.fokusDel = false; fokuseraDel(); }
    lasHuvud(gen);
  };
  // kunden i huvudet byts utan att delen lämnas: strömmen och läget hör till kunden, delen till adressen
  function bytKund(slug) {
    if (A.slug === slug) return;
    stangStrom();
    Object.assign(A, { mark: undefined, slug, lage: null, valdKandidat: null, folj: null, partner: null, partnerNyckel: null, material: null, logg: null, loggNyckel: null, svar: '', kod: { kandidat: null, fil: null, mot: null, visning: 'diff', data: null, fildata: null } });
    if (slug) { try { localStorage.setItem('nwp-arbetsyta:senaste', slug); } catch { /* bekvämlighet */ } }
  }
  async function lasHuvud(gen) {  // huvudet: kundlistan, kundens läge och strömmen, om de går att läsa; delen ritas oavsett
    try {
      const lista = (await hamta('/api/arbetsyta')).projekt || [];
      if (gen !== A.generation) return;
      A.projekt = lista;
      if (A.slug && !A.projekt.some((p) => p.slug === A.slug)) bytKund(null);
      ritaFlikrad(); rita();
      if (!A.slug) return;
      const slug = A.slug;
      if (!A.lage) { const d = await hamta('/api/arbetsyta/' + encodeURIComponent(slug)); if (gen !== A.generation || A.slug !== slug) return; tillampa(d, true); }
      if (gen === A.generation && A.slug === slug && !A.strom && !A.pollTimer) oppnaStrom(slug);
    } catch { /* utan kundens läge visas huvudet utan det; delen påverkas inte */ }
  }
  function ritaFlikrad() { const f = document.querySelector('.ay > .ay-flikrad'); if (f && !f.contains(document.activeElement)) { f.outerHTML = flikrad(); ritaRaknare(); } }
  // efter ett val i menyn: fokus på delens rubrik när den ritats, så att tangentbordet fortsätter i delen
  function fokuseraDel() {
    const vy = document.getElementById('vy'); if (!vy) return;
    const fokus = () => { const h = vy.querySelector('h1'); if (!h) return false; h.tabIndex = -1; h.focus({ preventScroll: true }); return true; };
    if (fokus()) return;
    const mo = new MutationObserver(() => { if (fokus()) mo.disconnect(); });
    mo.observe(vy, { childList: true, subtree: true }); setTimeout(() => mo.disconnect(), 10000);
  }
  // räknarna (vilande i backloggen, intag som pågår, prospekt som väntar): de sista kända från /api/oversikt, i menyn och
  // på gruppens knapp; läses om när de är äldre än en minut, och varje del som läser översikten uppdaterar dem (raknare)
  window.arbetsytaRaknare = function arbetsytaRaknare(o) { A.raknare = { tid: Date.now(), backlog: o.backlog_vilande || 0, kirurg: o.intag_pagar || 0, prospekt: o.prospekt_vantar || 0 }; ritaRaknare(); };
  async function ritaRaknare() {
    const r = A.raknare;
    const satt = (id, n, text) => { const b = document.getElementById(id); if (b) { b.hidden = !n; b.textContent = n ? text : ''; } };
    if (r) {
      satt('n-backlog', r.backlog, String(r.backlog)); satt('n-kirurg', r.kirurg, r.kirurg + ' pågår'); satt('n-prospekt', r.prospekt, String(r.prospekt));
      document.querySelectorAll('.ay-meny').forEach((m) => {
        const s = m.querySelector('summary'); if (!s) return;
        s.querySelectorAll('.ay-summa').forEach((b) => b.remove());
        for (const b of m.querySelectorAll('.ay-menylista b:not([hidden])')) {
          const namn = b.closest('a')?.querySelector('span')?.firstChild?.textContent.trim() || '';
          s.insertAdjacentHTML('beforeend', `<b class="ay-summa" title="${e_(namn + ': ' + b.textContent)}">${e_(b.textContent)}</b>`);
        }
      });
    }
    if (r && Date.now() - r.tid < 60000) return;
    if (A.raknareLaser) return;
    A.raknareLaser = true;
    try { window.arbetsytaRaknare(await hamta('/api/oversikt')); } catch { /* räknarna är en bekvämlighet; utan dem visas inga */ } finally { A.raknareLaser = false; }
  }
  function ytRam(l) {
    return `<div class="ay-omraden"><div class="ay-segment" role="group" aria-label="Visa område">${[['samtal', 'Samtal'], ['resultat', 'Resultat'], ['sessioner', 'Sessioner']].map(([k, n]) =>
        `<button type="button" data-omrade="${k}" aria-pressed="${(l.omrade || 'resultat') === k}">${n}</button>`).join('')}</div></div>
      <div class="ay-ytan" id="ay-ytan" data-omrade="${e_(l.omrade || 'resultat')}"${l.vansterDold ? ' data-vanster-dold' : ''}${l.hogerDold ? ' data-hoger-dold' : ''}
        style="${l.vanster ? `--ay-vanster:${Number(l.vanster)}px;` : ''}${l.hoger ? `--ay-hoger:${Number(l.hoger)}px;` : ''}">
        <section class="ay-panel ay-dialog" aria-labelledby="ay-dialog-rubrik">
          <div class="ay-panelhuvud"><h2 id="ay-dialog-rubrik">Samtal</h2>
            <div class="ay-segment ay-flikar" role="tablist" aria-label="Samtal och meddelanden">${[['partner', 'Partnern'], ['meddelanden', 'Meddelanden']].map(([k, n]) =>
              `<button type="button" role="tab" data-vflik="${k}" data-fokus="vf-${k}" aria-selected="${(A.vflik || 'partner') === k}" aria-controls="ay-samtal">${n}${k === 'meddelanden' ? ' <span class="ay-rakning" id="ay-oppna"></span>' : ''}</button>`).join('')}</div>
            <span id="ay-partnerchip"></span>
            <button class="ay-ikon" type="button" data-falla="vanster" aria-label="Fäll ihop samtalet">${SVG.vanster}</button></div>
          <div class="ay-panelkropp" id="ay-samtal" aria-live="off"></div>
          <form class="ay-skriv" id="ay-skriv" autocomplete="off"></form>
        </section>
        <div class="ay-delare" data-delare="vanster" role="separator" aria-orientation="vertical" aria-label="Samtalets bredd" tabindex="0"></div>
        <div class="ay-mitten">
          <section class="ay-panel ay-material" aria-labelledby="ay-material-rubrik" id="ay-material"></section>
          <div class="ay-remsa" id="ay-remsa"></div>
        </div>
        <div class="ay-delare" data-delare="hoger" role="separator" aria-orientation="vertical" aria-label="Sessionernas bredd" tabindex="0"></div>
        <section class="ay-panel ay-roller" aria-labelledby="ay-roller-rubrik" id="ay-roller"></section>
      </div>
      <div style="position:fixed;left:8px;bottom:8px;display:flex;gap:6px;z-index:5">
        <button class="ay-knapp liten ay-fallknapp ay-fall-vanster" type="button" data-visa="vanster">Visa samtalet</button>
        <button class="ay-knapp liten ay-fallknapp ay-fall-hoger" type="button" data-visa="hoger">Visa sessionerna</button></div>`;
  }
  function kodRam() {
    return `<div class="ay-kod">
      <section class="ay-panel ay-filer" aria-labelledby="ay-filer-rubrik"><div class="ay-panelhuvud"><h2 id="ay-filer-rubrik">Projektets filer</h2></div><div class="ay-panelkropp" id="ay-filer"></div></section>
      <section class="ay-panel" aria-labelledby="ay-fil-rubrik"><div class="ay-panelhuvud" id="ay-filhuvud"><h2 id="ay-fil-rubrik">Fil</h2></div><div class="ay-panelkropp" id="ay-filvy" style="padding:0" tabindex="0"></div></section>
      <section class="ay-panel ay-preview" aria-labelledby="ay-material-rubrik" id="ay-material"></section>
      <section class="ay-panel" aria-labelledby="ay-logg-rubrik"><div class="ay-panelhuvud"><h2 id="ay-logg-rubrik">Körningslogg</h2><button class="ay-knapp liten" type="button" data-logg-las>Läs om</button></div><div class="ay-panelkropp" id="ay-logg" tabindex="0"></div></section>
      <section class="ay-panel" aria-labelledby="ay-akt-rubrik"><div class="ay-panelhuvud"><h2 id="ay-akt-rubrik">Sessionens aktivitet</h2></div><div class="ay-panelkropp" id="ay-kodaktivitet" tabindex="0"></div></section>
    </div>`;
  }

  // --- ritningen ---
  function behallFokus(el, fn) {
    if (!el) return;
    const aktiv = document.activeElement, nyckel = aktiv && el.contains(aktiv) ? aktiv.dataset.fokus : null, rull = el.scrollTop;
    fn();
    el.scrollTop = rull;
    if (nyckel) el.querySelector(`[data-fokus="${CSS.escape(nyckel)}"]`)?.focus();
  }
  function rita() {
    if (!document.querySelector('.ay')) return;
    const h = document.getElementById('ay-huvud');
    if (!A.lage) { if (h && !h.contains(document.activeElement)) h.innerHTML = huvud(); return; }
    if (h && !h.contains(document.activeElement)) h.innerHTML = huvud();
    else ritaAnslutning();
    if (A.vy === '') { ritaMaterial(); behallFokus(document.getElementById('ay-remsa'), () => { document.getElementById('ay-remsa').innerHTML = remsa(); });
      behallFokus(document.getElementById('ay-roller'), () => { document.getElementById('ay-roller').innerHTML = roller(); }); ritaVanster(); }
    if (A.vy === 'flode') {
      if (!A.bevakningLast || Date.now() - A.bevakningLast > 300000) laddaBevakning();  // en gång och sedan var femte minut
      behallFokus(document.getElementById('ay-flode'), () => { document.getElementById('ay-flode').innerHTML = flode(); });
    }
    if (A.vy === 'kod') { ritaMaterial(); ritaKodaktivitet(); laddaLogg(); if (A.kod.kandidat !== kodKandidat()) laddaKod(); }
    if (A.vy === 'forslag') ritaForslagsnotis();
  }
  // Förslagen (ägarens besked 2026-10-09 ~17:11Z: allt ska in i arbetsytan): kandidatflödets hela vy, förr Prototyp, i
  // arbetsytans ram: bilderna i alla bredder, förslagen sida vid sida, referensen bredvid, det du gillar per förslag,
  // redovisningen, de tekniska kontrollerna, avslöjandet efter ditt första beslut, observationen och hela beslutet. Vyn
  // ritas när fliken öppnas; ett nytt läge visas som en notis när du har skrivit något, så att inget du skrivit töms.
  function forslagsnyckel() {
    const l = A.lage || {}, k = l.korning || {};
    return JSON.stringify([A.slug, k.startad, k.steg, (l.kandidater || []).map((x) => [x.id, x.version, x.status])]);
  }
  async function laddaForslagen() {
    const slug = A.slug, gen = A.generation;
    if (!slug || typeof prototypvy !== 'function') return;
    A.forslagNyckel = A.lage ? forslagsnyckel() : null;
    const n = document.getElementById('ay-forslagsnotis'); if (n) n.innerHTML = '';
    try { await prototypvy(slug); } catch (err) {
      if (gen !== A.generation || A.slug !== slug) return;
      const v = document.getElementById('vy'); if (!v) return;
      v.innerHTML = /ingen prototyp/.test(err.message)  // ingen körning för kunden än (server.prototyp: 404), inget fel
        ? `<h1>Förslagen · ${e_(slug)}</h1><div class="ay-tom">Inga förslag än för kunden. Förbered kundunderlaget och starta referensjakt och skiss under <a href="#/arbetsyta/${e_(slug)}/flode">Byggflöde</a>.</div>`
        : `<div class="ay-notis varn">Förslagen kunde inte läsas: ${e_(err.message)}</div>`;
    }
  }
  function ritaForslagsnotis() {
    if (!A.lage || A.forslagNyckel === undefined) return;
    const nyckel = forslagsnyckel();
    if (A.forslagNyckel === null) { A.forslagNyckel = nyckel; return; }  // läget lästes efter vyn: det är samma läge
    if (nyckel === A.forslagNyckel) return;
    const vy = document.getElementById('vy');
    const skrivet = vy && [...vy.querySelectorAll('textarea, input:not([type=checkbox]):not([type=radio])')].some((f) => f.value.trim());
    if (!skrivet && !(vy && vy.contains(document.activeElement))) { laddaForslagen(); return; }
    const n = document.getElementById('ay-forslagsnotis');
    if (n && !n.innerHTML) n.innerHTML = `<div class="ay-notis varn" role="status">Läget har ändrats sedan förslagen ritades: en ny version, ett nytt steg eller ett nytt beslut. <button class="ay-knapp" type="button" data-las-om-forslag>Läs om förslagen</button> Det du har skrivit här töms då.</div>`;
  }
  // det ägaren ser i Förslagen, ur arbetsytans läge: kandidatens fotograferade version och ögonblicksbildernas hash. Ett
  // godkännande binds till dem, och samverkan.beslut prövar dem mot filerna nu (som raden under ögonblicksbilden).
  window.arbetsytaSett = function arbetsytaSett(slug) {
    if (!A.lage || A.slug !== slug) return null;
    return Object.fromEntries((A.lage.kandidater || []).map((k) => [k.id, { version: k.version_hel, sedd: ['390', '1440']
      .filter((b) => k.snapshot?.[b] && k.snapshot?.sha?.[b]).map((b) => ({ kandidat: k.id, version: k.version_hel, bild: k.snapshot[b], bild_sha: k.snapshot.sha[b] })) }]));
  };
  function huvud() {
    if (!A.lage) return `<div class="ay-marke">${SVG.marke}<span>Nortropic</span></div>${A.projekt.length ? `<div class="ay-falt"><span><label for="ay-kund">Kund</label></span><select id="ay-kund" data-fokus="kund">${A.slug ? '' : '<option value="" selected>Välj kund</option>'}${A.projekt.map((x) => `<option value="${e_(x.slug)}"${x.slug === A.slug ? ' selected' : ''}>${e_(x.namn || x.slug)}</option>`).join('')}</select></div>` : ''}`;
    const l = A.lage, p = l.projekt || {}, k = l.korning || {}, kand = (l.kandidater || []).find((x) => x.id === A.valdKandidat);
    return `<div class="ay-marke">${SVG.marke}<span>Nortropic</span></div>
      <div class="ay-falt"><span><label for="ay-kund">Kund</label></span><select id="ay-kund" data-fokus="kund">${A.projekt.map((x) => `<option value="${e_(x.slug)}"${x.slug === A.slug ? ' selected' : ''}>${e_(x.namn || x.slug)}${x.testdata && !/testdata/i.test(x.namn || '') ? ' (testdata)' : ''}</option>`).join('')}</select></div>
      ${p.testdata ? '<span class="ay-testdata" title="Fiktiv verksamhet: testdata, aldrig en riktig kund">Testdata</span>' : ''}
      <div class="ay-falt mindre"><span>Uppdrag</span><span>${k.startad ? `Körning ${e_(kort(k.startad))}, ${e_(LAGESNAMN[k.lage] || k.lage || 'läge okänt')}${A.fokusStart && k.start_id === A.fokusStart ? ' (din start)' : ''}` : 'Ingen körning'}</span></div>
      <div class="ay-falt mindre"><span>Kandidat och version</span><span>${kand ? `${e_(kand.etikett)} · ${kand.version ? 'version ' + e_(kand.version) : 'ingen version'}` : 'ingen vald'}</span></div>
      <div class="ay-falt"><span>Moment</span><span>${l.moment ? `${e_(l.moment.nr)}. ${e_(l.moment.namn)} · ${e_(l.moment.status)}` : 'okänt'}</span></div>
      <div class="ay-hoger-huvud">${anslutning()}</div>`;
  }
  function anslutning() {
    const text = A.anslutning === 'ansluten' ? `Följer live, läst ${klocka(A.senastLast)}` : A.anslutning === 'ateransluter' ? `Återansluter… senast läst ${klocka(A.senastLast)}`
      : A.anslutning === 'inaktuellt' ? `Inaktuellt sedan ${klocka(A.avbrott)}` : 'Ansluter…';
    return `<span class="ay-anslutning" id="ay-anslutning" data-lage="${e_(A.anslutning)}"><i aria-hidden="true"></i>${e_(text)}${A.lasfel ? ` · läsfel ${e_(klocka(A.lasfel.tid))}` : ''}</span>`;
  }
  function ritaAnslutning() { const el = document.getElementById('ay-anslutning'); if (el) el.outerHTML = anslutning(); }

  // huvudmaterialet: följer momentet; arbetsversion, bevarad ögonblicksbild och export märkta för sig
  function materialval() {
    if (A.material) return A.material;
    const nr = A.lage.moment?.nr || 0;
    if (nr <= 1) return 'underlag';
    if (nr >= 6 && (A.lage.preview || []).some((p) => p.kalla === 'helbygget')) return 'forhandsvisning';
    const k = (A.lage.kandidater || []).find((x) => x.id === A.valdKandidat);
    return k ? (k.preview.finns ? 'forhandsvisning' : 'snapshot') : 'kandidater';
  }
  function ritaMaterial() {
    const el = document.getElementById('ay-material'); if (!el) return;
    const val = A.vy === 'kod' ? 'forhandsvisning' : materialval();
    const pv = previewFor(), nyckel = JSON.stringify([val, pv?.url, ['snapshot', 'jamfor'].includes(val) ? A.enhet : '', A.valdKandidat, pv?.byggd, pv?.osaker, A.lage.blind, val === 'jamfor' ? A.jamforMed : '', val === 'jamfor' ? (A.lage.kandidater || []).map((k) => k.version).join() : '', Boolean(A.lage.korning?.vantar_pa_agaren)]);  // osaker: ombygget ändrar inte byggd
    const huvud_ = `<div class="ay-panelhuvud"><h2 id="ay-material-rubrik">${A.vy === 'kod' ? 'Förhandsvisning' : 'Resultat'}</h2>
      ${A.vy === 'kod' ? '' : `<div class="ay-segment" role="group" aria-label="Vad som visas">${[['forhandsvisning', 'Förhandsvisning'], ['snapshot', 'Ögonblicksbild'], ['jamfor', 'Jämför'], ['kandidater', 'Kandidater'], ['underlag', 'Underlag']].map(([k, n]) =>
        `<button type="button" data-material="${k}" data-fokus="m-${k}" aria-pressed="${val === k}">${n}</button>`).join('')}</div>`}
      <div class="ay-segment" role="group" aria-label="Skärmbredd"><button type="button" data-enhet="dator" data-fokus="e-dator" aria-pressed="${A.enhet === 'dator'}">Dator</button><button type="button" data-enhet="mobil" data-fokus="e-mobil" aria-pressed="${A.enhet === 'mobil'}">Mobil</button></div>
      ${pv ? `<a class="ay-ikon" href="${e_(pv.url)}" target="_blank" rel="noopener" aria-label="Öppna förhandsvisningen i en ny flik">${SVG.lank}</a><button class="ay-ikon" type="button" data-ladda-om aria-label="Ladda om förhandsvisningen">${SVG.ladda}</button>` : ''}</div>`;
    if (el.dataset.nyckel === nyckel) {  // samma innehåll: bara huvudet och bredden, så att ramen inte laddas om
      el.querySelector('.ay-panelhuvud').outerHTML = huvud_;
      el.querySelector('.ay-scen')?.setAttribute('data-enhet', A.enhet);
      ritaBeslutsrad();
      return;
    }
    el.dataset.nyckel = nyckel;
    el.innerHTML = huvud_ + (['snapshot', 'jamfor'].includes(val) && A.lage.korning?.vantar_pa_agaren ? '<div class="ay-beslutsrad" id="ay-beslutsrad"></div>' : '') + materialKropp(val, pv);
    el.querySelector('.ay-scen')?.setAttribute('tabindex', '0');  // scenen rullar (ramen, en hel skärmbild): den ska nås med tangentbordet
    ritaBeslutsrad();
  }
  function ritaBeslutsrad() { const r = document.getElementById('ay-beslutsrad'); if (r) behallFokus(r, () => { r.innerHTML = beslutsruta(); }); }
  function previewFor() {
    const p = A.lage.preview || [];
    return p.find((x) => x.typ === 'arbetsversion' && x.kandidat === A.valdKandidat) || (A.valdKandidat ? null : p.find((x) => x.typ === 'arbetsversion' && x.kalla === 'helbygget'))
      || (A.vy === 'kod' ? p.find((x) => x.typ === 'arbetsversion') : null) || null;
  }
  function materialKropp(val, pv) {
    const l = A.lage;
    if (val === 'jamfor') return jamforelse();
    if (val === 'underlag') {
      const st = (l.steg || [])[0] || {}, filer = [...(st.utfall || [])];
      return `<div class="ay-adress"><span class="etikett">Kundunderlaget, läst ur körningens filer</span></div><div class="ay-scen"><div class="ay-underlagslista">${filer.length
        ? filer.map((f) => f.lank ? `<a href="${e_(f.lank)}" target="_blank" rel="noopener"><span>${e_(f.text)}</span><span class="svag">${e_(kort(f.tid))}</span></a>` : `<div class="ay-notis">${e_(f.text)}</div>`).join('')
        : '<div class="ay-tom">Inget kundunderlag än. Förbered det med handlingen under Kontroller.</div>'}</div></div>`;
    }
    if (val === 'kandidater') {
      const ks = l.kandidater || [];
      return `<div class="ay-adress"><span class="etikett">${l.blind ? 'Neutrala etiketter i slumpad ordning; bedömningar visas efter ditt första val (i Förslagen)' : 'Kandidaterna i körningen'}</span></div>
        <div class="ay-scen"><div class="ay-kandidatrutnat">${ks.length ? ks.map((k) => `<button type="button" class="ay-kandidat" data-kandidat="${e_(k.id)}" data-fokus="k-${e_(k.id)}" aria-pressed="${k.id === A.valdKandidat}">
          ${k.snapshot['1440'] ? `<img loading="lazy" src="/fil/${e_(k.snapshot['1440'])}" alt="${e_(k.etikett)}, bevarad skärmbild">` : '<span class="utan-bild">Ingen skärmbild än</span>'}
          <strong>${e_(k.etikett)}</strong><span class="svag">${e_(k.statustext || k.status)}${k.version ? ' · version ' + e_(k.version) : ''}</span></button>`).join('')
        : '<div class="ay-tom">Inga kandidater i körningen än.</div>'}</div></div>`;
    }
    if (val === 'snapshot') {
      const s = (l.preview || []).find((x) => x.typ === 'snapshot' && x.kandidat === A.valdKandidat);
      if (!s) return '<div class="ay-scen"><div class="ay-tom">Ingen bevarad ögonblicksbild för den valda kandidaten än.</div></div>';
      const bild = A.enhet === 'mobil' ? s.bilder['390'] || s.bilder['1440'] : s.bilder['1440'] || s.bilder['390'];
      return `<div class="ay-adress"><span class="etikett">${s.aldre ? '<b>Äldre</b>: ' : ''}${e_(s.etikett)}</span></div><div class="ay-scen"><img src="/fil/${e_(bild)}" alt="${e_(s.etikett)}"></div>`;
    }
    if (!pv) {
      const s = (l.preview || []).find((x) => x.typ === 'snapshot' && x.kandidat === A.valdKandidat);
      return `<div class="ay-scen">${s ? `<div><div class="ay-notis varn" style="margin-bottom:10px"><b>Äldre:</b> bygget finns inte just nu. ${e_(s.etikett)}.</div><img src="/fil/${e_(s.bilder['1440'] || s.bilder['390'])}" alt="${e_(s.etikett)}"></div>`
        : '<div class="ay-tom">Ingen förhandsvisning än: inget bygge finns för det som är valt. Kandidaterna visas under Kandidater när de är byggda.</div>'}</div>`;
    }
    const exp = (l.preview || []).find((x) => x.typ === 'export');
    const text = `${pv.kandidat ? etikett(pv.kandidat) : 'Helbygget'}, byggd ${kort(pv.byggd)}. ${pv.osaker ? 'Kandidaten byggs om eller senaste bygget föll, så den kan vara äldre än arbetet.' : 'Kan ändras medan arbetet pågår.'} Den bevarade versionen visas under Ögonblicksbild.${exp ? ' ' + exp.etikett + '.' : ''}`;
    return `<div class="ay-adress"><span class="etikett" title="${e_(text)}"><b>${pv.osaker ? 'Arbetsversion, kan vara äldre' : 'Arbetsversion'}</b>: ${e_(text)}</span></div>
      <div class="ay-scen" data-enhet="${e_(A.enhet)}"><iframe title="Förhandsvisning: ${e_(pv.etikett)}" src="${e_(pv.url)}" sandbox="allow-scripts allow-forms allow-same-origin" referrerpolicy="no-referrer" loading="lazy"></iframe></div>`;
  }
  function remsa() {
    const l = A.lage, hs = (l.handlingar || []);
    const stopp = hs.filter((h) => ['stoppa', 'stoppa-overgang'].includes(h.id)), ovriga = hs.filter((h) => !['stoppa', 'stoppa-overgang'].includes(h.id));
    const kontroller = `<section class="ay-panel" aria-labelledby="ay-ktl"><div class="ay-panelhuvud"><h2 id="ay-ktl">Kontroller</h2></div><div class="ay-panelkropp ay-bekrafta">
      ${A.bekrafta ? `<p style="margin:0">${e_(A.bekrafta.text)}</p><div class="ay-knapprad"><button class="ay-knapp fara" type="button" data-handling="${e_(A.bekrafta.id)}" data-bekraftad data-fokus="bekrafta">Stoppa</button><button class="ay-knapp" type="button" data-avbryt-bekraftelse data-fokus="avbryt">Avbryt</button></div>`
        : `<div class="ay-knapprad">${ovriga.map((h) => `<button class="ay-knapp primar" type="button" data-handling="${e_(h.id)}" data-fokus="h-${e_(h.id)}"${h.hinder || A.pagar ? ' aria-disabled="true"' : ''}${h.hinder ? ' title="' + e_(h.hinder) + '"' : ''}>${e_(h.text)}</button>`).join('')}
           ${stopp.map((h) => `<button class="ay-knapp fara" type="button" data-handling="${e_(h.id)}" data-fokus="h-${e_(h.id)}"${A.pagar ? ' aria-disabled="true"' : ''}>Stoppa</button>`).join('')}
           ${hs.length ? '' : '<span class="dampad">Ingen handling är möjlig just nu.</span>'}</div>`}
      ${ovriga.filter((h) => h.hinder).map((h) => `<p class="svag" style="margin:0">${e_(h.text)} går inte att starta: ${e_(h.hinder)}</p>`).join('')}
      ${projektpaus()}
      <p class="svag" style="margin:0" role="status" aria-live="polite" id="ay-handlingssvar">${e_(A.svar)}</p></div></section>`;
    const handelser = senasteHandelser(6);
    const obs = `<section class="ay-panel" aria-labelledby="ay-obs"><div class="ay-panelhuvud"><h2 id="ay-obs">Senast observerat</h2></div><div class="ay-panelkropp" tabindex="0" data-fokus="obs">
      ${handelser.length ? `<ul class="ay-handelser">${handelser.map((x) => `<li><time datetime="${e_(x.tid)}">${e_(klocka(x.tid).slice(0, 5))}</time><span>${e_(x.text)}</span></li>`).join('')}</ul>` : '<div class="ay-tom">Inga observerade händelser i körningen än.</div>'}
      ${(l.ofullstandig || []).length ? `<div class="ay-notis varn" style="margin-top:8px">Ofullständigt: ${e_(l.ofullstandig.join('; '))}</div>` : ''}</div></section>`;
    const k = l.korning || {}, b = l.besked || {};
    const beslut = `<section class="ay-panel" aria-labelledby="ay-besl"><div class="ay-panelhuvud"><h2 id="ay-besl">Nästa beslut</h2></div><div class="ay-panelkropp ay-bekrafta">
      ${k.vantar_pa_agaren ? `<p style="margin:0">Kandidaterna väntar på ditt beslut. Du beslutar under den bevarade bilden, som beslutet binds till.</p><div class="ay-knapprad"><button class="ay-knapp primar" type="button" data-visa-beslut data-fokus="visa-beslut">Visa bilden och besluta</button><a class="ay-knapp" href="#/arbetsyta/${e_(A.slug)}/forslag">Alla förslag i Förslagen</a></div>`
        : k.avbruten ? '<p style="margin:0">Körningen avbröts. Återuppta den under Kontroller; inget klart görs om.</p>'
        : k.arbetaren === 'lever' ? '<p style="margin:0">Inget beslut väntar på dig: arbetet pågår.</p>' : '<p style="margin:0">Inget beslut väntar på dig just nu.</p>'}
      ${(b.tillstand || []).length ? `<details><summary class="svag">Slutbeskedens fem lägen</summary><ul class="ay-handelser" style="margin-top:6px">${b.tillstand.map((t) => `<li><span>${e_(t.status)}</span><span>${e_(t.namn)}</span></li>`).join('')}</ul></details>` : ''}
      ${(l.overlamningar || []).length ? overlamningslista(l.overlamningar.slice(-3)) : ''}</div></section>`;
    return kontroller + obs + beslut;
  }
  function overlamningslista(lista) {
    const steg = [['skickad', 'skickad'], ['mottagen', 'mottagen'], ['arbete_startat', 'arbete startat'], ['resultat_sparat', 'resultat sparat'], ['verifierat', 'verifierat']];
    return `<div><h3 style="margin:4px 0">Dina ändringar</h3><ul class="ay-handelser">${lista.map((o) => `<li><time>${e_(klocka(o.tid).slice(0, 5))}</time><span>${e_(etikett(o.kandidat))}${o.version ? ' v' + e_(o.version) : ''}: ${steg.filter(([k]) => o.steg[k]).map(([, n]) => n).join(' → ')}${o.steg.verifierat ? '' : ' (inte verifierat)'}${o.aktuell ? '' : ' · kandidaten har en ny version'}</span></li>`).join('')}</ul></div>`;
  }
  function senasteHandelser(n) {
    const ut = [];
    for (const s of A.lage.sessioner || []) {
      for (const h of (s.aktivitet?.handelser || []).slice(-8)) ut.push({ tid: h.tid, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: ${h.verktyg}${h.fil ? ' ' + h.fil.split('/').slice(-2).join('/') : h.skill ? ' ' + h.skill : ''}, ${h.utfall}` });
      if (s.start) ut.push({ tid: s.start, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''} startade` });
      if (s.slut) ut.push({ tid: s.slut, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: ${s.lage_text || LAGEN[s.lage]}` });
    }
    for (const j of A.lage.startjournal || []) ut.push({ tid: j.tid, text: `Begäran ${j.handling || ''}: ${j.status || 'okänd'}${j.stopp_begart ? ', stopp begärt' : ''}${j.slutkod != null ? ', slutkod ' + j.slutkod : ''}` });
    return ut.filter((x) => x.tid).sort((a, b) => String(b.tid).localeCompare(String(a.tid))).slice(0, n);
  }
  function sessionskort(s) {
    const a = s.aktivitet || {}, sista = (a.handelser || []).slice(-1)[0];
    return `<article class="ay-session" aria-label="${e_(roll(s))}">
      <header><div><div class="namn">${e_(roll(s))}${s.kandidat ? ' · ' + e_(etikett(s.kandidat)) : ''}</div><div class="rad">${e_(s.modell_observerad || s.modell_konfigurerad || 'modell inte observerad')}</div></div>${lagechip(s.lage, s.lage_text)}</header>
      <div class="rad">${e_(s.lage_text || '')}</div>
      <div class="rad">Senaste händelse: ${e_(sedan(s.senaste_handelse))}${sista ? ` · ${e_(sista.verktyg)} (${e_(sista.utfall)})` : ''}</div>
      ${s.kontext ? `<div class="rad" title="Indata i senaste modellanropet, en uppskattning; fönstrets storlek står inte i transkriptet">Kontext cirka ${Math.round(s.kontext.tokens / 1000)} k tokens (uppskattning)</div>` : ''}
      ${styrrad(s)}${kompetensrad(s)}
      <div class="knappar"><button class="ay-knapp liten" type="button" data-folj="${e_(s.session_id || '')}" data-fokus="f-${e_(s.session_id || '')}"${s.session_id ? '' : ' disabled'}>Följ</button>${sessionsknappar(s)}</div>
      ${A.pausBekrafta?.session_id === s.session_id ? `<div class="ay-bekraftruta" role="group" aria-label="Bekräfta pausen"><p>Pausa bara den här sessionen? Den avbryts vid nästa möjlighet och väntar med samma process; resten av körningen fortsätter. Filändringar som redan gjorts står kvar.</p><div class="ay-knapprad"><button class="ay-knapp primar liten" type="button" data-paus-ja="${e_(s.session_id)}" data-fokus="pj-${e_(s.session_id)}">Pausa sessionen</button><button class="ay-knapp liten" type="button" data-paus-nej>Avbryt</button></div></div>` : ''}</article>`;
  }
  function roller() {
    const l = A.lage;
    if (A.folj) return foljvy();
    if (A.historik) return historikvy();
    const r = l.roller || {}, sess = l.sessioner || [];
    return `<div class="ay-panelhuvud"><h2 id="ay-roller-rubrik">Rollsessioner</h2><span class="svag">${sess.filter((s) => ['aktiv', 'verktyg', 'startar'].includes(s.lage)).length} lever</span>
        <button class="ay-ikon" type="button" data-falla="hoger" aria-label="Fäll ihop sessionerna">${SVG.hoger}</button></div>
      <div class="ay-panelkropp">${['arbetsledning', 'utforande', 'granskning'].map((nyckel) => {
        const x = r[nyckel] || { rubrik: nyckel, lage: 'okant', lage_text: 'inte observerat' };
        const egna = sess.filter((s) => s.ansvar === nyckel);
        return `<section class="ay-ansvar" aria-labelledby="ans-${nyckel}"><header><h3 id="ans-${nyckel}">${e_(x.rubrik)}</h3>${lagechip(x.lage, x.lage_text)}</header>
          ${egna.length ? egna.slice(0, 6).map(sessionskort).join('') + (egna.length > 6 ? `<p class="svag" style="margin:0">och ${egna.length - 6} till i Byggflöde</p>` : '')
            : `<div class="ay-session vantande"><div class="rad">${e_(x.lage_text)}</div>${x.konfigurerad ? `<div class="rad">Konfigurerad: ${e_(x.konfigurerad)}</div>` : ''}</div>`}</section>`;
      }).join('')}</div>`;
  }
  function foljvy() {
    const s = (A.lage.sessioner || []).find((x) => x.session_id === A.folj);
    if (!s) return `<div class="ay-panelhuvud"><h2 id="ay-roller-rubrik">Följer</h2><button class="ay-knapp liten" type="button" data-folj-slut data-fokus="folj-slut">Tillbaka</button></div><div class="ay-panelkropp"><div class="ay-tom">Sessionen finns inte längre i körningens läge.</div></div>`;
    const a = s.aktivitet || {};
    return `<div class="ay-panelhuvud"><h2 id="ay-roller-rubrik">Följer: ${e_(roll(s))}</h2><button class="ay-knapp liten" type="button" data-folj-slut data-fokus="folj-slut">Tillbaka</button></div>
      <div class="ay-panelkropp ay-folj">${lagechip(s.lage, s.lage_text)}
        <div class="svag">Sessions-id <code>${e_(s.session_id)}</code>${s.kandidat ? ' · ' + e_(etikett(s.kandidat)) : ''} · startad ${e_(kort(s.start))}${s.slut ? ' · slut ' + e_(kort(s.slut)) : ''}</div>
        <div class="svag">Förälder: ${e_(s.foralder?.typ || 'inte observerad')}${s.foralder?.pid ? ' (pid ' + e_(s.foralder.pid) + ')' : ''}${s.foralder?.start_id ? ' · start-id ' + e_(String(s.foralder.start_id).slice(0, 8)) : ''}</div>
        <div class="svag">Modell: konfigurerad ${e_(s.modell_konfigurerad || 'okänd')}, observerad ${e_(s.modell_observerad || 'inte observerad')}</div>
        ${A.lage.blind && s.kalla !== 'partnersamtalet' ? '<div class="ay-notis">Sökvägar i aktiviteten visas efter ditt första val i körningen.</div>' : ''}
        ${(a.pagaende || []).length ? `<div class="ay-notis">Väntar på verktyg: ${e_(a.pagaende.join(', '))}</div>` : ''}
        ${(a.handelser || []).length ? `<ol aria-label="Observerade händelser, nyast sist">${a.handelser.slice(-30).map((h) => `<li><time datetime="${e_(h.tid)}">${e_(klocka(h.tid))}</time><span>${e_(h.verktyg)} · ${e_(h.utfall)}${h.skill ? ' · ' + e_(h.skill) : ''}${h.fil ? `<div class="fil">${e_(h.fil)}</div>` : ''}</span></li>`).join('')}</ol>`
          : `<div class="ay-tom">${e_(s.ofullstandig || 'Inga verktygsanrop observerade i transkriptet än.')}</div>`}
        <p class="svag" style="margin:0">Följningen läser transkriptet; den startar ingen modell och skickar inget till sessionen. ${s.kalla === 'partnersamtalet' ? 'Partnern når du i samtalet.' : s.styrning?.kan_meddelas ? 'Skriv till sessionen under Meddelanden; den läser meddelandet mellan sina verktygsanrop.' : 'Den här sessionen tar inte emot meddelanden (' + e_(s.styrning?.blind ? 'en blind bedömning' : s.styrning?.text || 'den arbetar inte') + ').'}</p></div>`;
  }

  // --- partnern ---
  async function laddaPartner() {
    if (!A.slug) return;
    const slug = A.slug;
    try { const p = await hamta('/api/arbetsyta/' + encodeURIComponent(slug) + '/partner'); if (slug === A.slug) { A.partner = p; ritaPartner(); ritaSkriv(); } } catch { /* nästa läge försöker igen */ }
  }
  function formatera(text) {
    const delar = String(text || '').replace(/```overlamning[\s\S]*?```/g, '').trim().split(/\n{2,}/);
    const inline = (t) => e_(t).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    return delar.map((d) => /^\s*[-*] /m.test(d) && d.split('\n').every((r) => /^\s*[-*] /.test(r) || !r.trim())
      ? `<ul>${d.split('\n').filter((r) => r.trim()).map((r) => `<li>${inline(r.replace(/^\s*[-*] /, ''))}</li>`).join('')}</ul>` : `<p>${inline(d).replace(/\n/g, '<br>')}</p>`).join('');
  }
  function ritaPartner() {
    const el = document.getElementById('ay-samtal'); if (!el || A.vflik === 'meddelanden') return;
    const p = A.partner, chip = document.getElementById('ay-partnerchip');
    if (chip) chip.innerHTML = p && p.lage && p.lage !== 'vantar' ? lagechip(p.lage, p.lage_text) : '';
    const med = p?.meddelanden || [];
    const nere = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    el.innerHTML = `<div class="ay-modell">Arbetsledning: ${e_(p?.modell || p?.profil?.modell || 'okänd')}, effort ${e_(p?.effort || p?.profil?.effort || '?')} (en hypotes att pröva, ingen kvalitetssanning). Partnern läser samma läge som vyn och har bara läsrätt.</div>
      ${med.length ? med.map(meddelande).join('') : '<div class="ay-tom">Ställ en fråga om läget. Partnern läser kundens underlag och arbetsytans läge, ändrar inget och startar inget arbete.</div>'}
      ${p?.session_id && !med.some((m) => m.lage === 'arbetar') ? `<details><summary class="svag">Fortsätt i terminalen</summary><p class="svag" style="margin:6px 0">Samma session öppnas interaktivt med kommandot nedan, i <code>${e_(p.arbetskatalog)}</code>. Medan den är öppen tar samtalet här inga meddelanden (två processer får aldrig skriva i samma session).</p><code style="display:block;white-space:pre-wrap">cd "${e_(p.arbetskatalog)}" && ${e_(p.terminal)}</code></details>` : ''}`;
    if (nere) el.scrollTop = el.scrollHeight;
  }
  function meddelande(m) {
    const k = m.kontext || {}, kt = [k.kandidat ? etikett(k.kandidat) : null, k.version ? 'v' + k.version : null, k.vy ? 'vy ' + k.vy : null, k.sida ? 'sida ' + k.sida : null, k.del ? k.del : null].filter(Boolean).join(', ');
    const svar = m.svar;
    const anv = svar?.anvandning;
    return `<div class="ay-msg agaren"><div class="ay-kontextrad">${e_({ fraga: 'Fråga', plan: 'Planförslag', andring: 'Ändring' }[m.avsikt] || m.avsikt)}${kt ? ' · ' + e_(kt) : ''}</div>${formatera(m.text)}<div class="meta"><span>Du</span><time>${e_(klocka(m.tid).slice(0, 5))}</time></div></div>
      ${m.lage === 'arbetar' ? `<div class="ay-msg partnern">${lagechip('aktiv', 'partnern svarar')} <span class="svag">Partnern svarar…</span></div>`
        : m.lage === 'skickat' ? `<div class="ay-msg partnern">${lagechip('startar', '')}</div>`
        : svar ? `<div class="ay-msg partnern">${svar.fel ? `<div class="ay-notis fel">Turen slutade med fel (${e_(svar.subtyp || 'okänt')}).</div>` : ''}${formatera(svar.text)}
            ${m.overlamning ? overlamningskort(m) : ''}
            <div class="meta"><span>Partnern${anv ? ` · rapporterad användning: ${e_(anv.in ?? '?')} in, ${e_(anv.cache_las ?? '?')} ur cache, ${e_(anv.cache_skriv ?? '?')} till cache, ${e_(anv.ut ?? '?')} ut tokens${anv.listpris_usd != null ? `; listpris enligt Claude Code ${e_(Number(anv.listpris_usd).toFixed(2))} USD, inte fakturerat (prenumerationen räknar kvot)` : ''}` : ''}</span><time>${e_(klocka(m.slut).slice(0, 5))}</time></div></div>`
        : `<div class="ay-msg partnern"><div class="ay-notis fel">${e_(m.fel || 'Inget svar: processen lever inte och ingen svarsfil finns.')}</div></div>`}`;
  }
  function overlamningskort(m) {
    const o = m.overlamning;
    if (o['oläsligt']) return '<div class="ay-overlamning svag">Partnern föreslog en överlämning, men blocket gick inte att läsa.</div>';
    const rad = (n, v) => v ? `<dt>${n}</dt><dd>${e_(v)}</dd>` : '';
    return `<div class="ay-overlamning"><strong>Förslag till överlämning</strong><dl>${rad('Kandidat', o.kandidat ? etikett(o.kandidat) : null)}${rad('Version', o.version)}${rad('Sida', o.sida)}${rad('Del', o.del)}${rad('Mål', o.mal)}${rad('Avgränsning', o.avgransning)}${rad('Förväntat', o.forvantat)}</dl>
      <button class="ay-knapp liten" type="button" data-anvand-forslag="${e_(m.id)}">Använd som min ändring</button><span class="svag"> Du läser, ändrar och skickar själv.</span></div>`;
  }
  const VYNAMN = { '': 'Arbetsyta', flode: 'Byggflöde', kod: 'Kod och preview' };
  function levande(kid) {
    const k = (A.lage?.kandidater || []).find((x) => x.id === (kid ?? A.valdKandidat));
    return { kandidat: k?.id || null, version: k?.version || null, version_hel: k?.version_hel || null, vy: VYNAMN[A.vy], korning: A.lage?.korning?.startad || null };
  }
  const markLager = () => 'nwp-arbetsyta-markering:' + A.slug;
  function lasMark() { try { const m = JSON.parse(sessionStorage.getItem(markLager()) || 'null'); return m && typeof m === 'object' ? m : null; } catch { return null; } }
  function sparaMark(m) { A.mark = m; try { m ? sessionStorage.setItem(markLager(), JSON.stringify(m)) : sessionStorage.removeItem(markLager()); } catch { /* bara en bekvämlighet */ } }
  function markera(tillagg) {
    const m = Object.assign({}, levande(tillagg?.kandidat), tillagg || {});
    const k = (A.lage?.kandidater || []).find((x) => x.id === m.kandidat);
    m.beslut = 'uppdrag';  // en ändring är ett uppdrag: rätta, omarbeta designen eller bygg ut (2026-10-09); ett val startar inget
    sparaMark(m); return m;
  }
  // det ändringen gäller: den frysta markeringen om du gjort en, annars den kandidat som är vald just nu
  function markering() { if (A.mark === undefined) A.mark = lasMark(); return A.mark || levande(); }
  function inaktuellMark() {
    const m = A.mark; if (!m || !m.kandidat) return null;
    const nu = levande(m.kandidat);
    if (m.korning && nu.korning && m.korning !== nu.korning) return `körningen har bytts sedan du markerade (${kort(m.korning)}, nu ${kort(nu.korning)})`;
    if (m.version_hel && nu.version_hel && m.version_hel !== nu.version_hel) return `kandidaten har en ny version sedan du markerade (${m.version}, nu ${nu.version})`;
    return null;
  }
  // raden Gäller: det ändringen är bunden till (den frysta markeringen) eller det som är valt just nu. Ritas om på plats när
  // markeringen fryses eller släpps medan du skriver, så att raden aldrig visar en annan version än den ändringen bär.
  function gallerRad() {
    const mk = markering(), kand = mk.kandidat ? etikett(mk.kandidat) : null;
    return `Gäller: <b>${e_(A.lage.projekt?.namn || A.slug)}</b>${kand ? `, <b>${e_(kand)}</b>${mk.version ? ' version ' + e_(mk.version) : ''}` : ', ingen kandidat vald'}${mk.korning ? ', körningen ' + e_(kort(mk.korning)) : ''}, vy ${e_(mk.vy)}${mk.fil ? ', fil ' + e_(mk.fil) : ''}
        ${A.mark ? ' <button class="ay-knapp liten" type="button" data-rensa-markering data-fokus="rensa">Rensa markeringen</button>' : ''}`;
  }
  function ritaGaller() { const g = document.getElementById('ay-markering'); if (g && A.lage) g.innerHTML = gallerRad(); }
  function ritaSkriv() {
    const f = document.getElementById('ay-skriv'); if (!f || !A.lage || A.vflik === 'meddelanden') return;
    const mk = markering(), kand = mk.kandidat ? etikett(mk.kandidat) : null;
    const form = JSON.stringify([A.avsikt, A.lage.blind, mk.kandidat, mk.version, mk.vy, mk.fil, A.lage.projekt?.namn, inaktuellMark(), Boolean(A.mark)]);  // fryst eller levande syns på raden Gäller
    if (f.dataset.ritad === form || (f.contains(document.activeElement) && f.dataset.ritad)) { uppdateraSkrivstatus(); return; }
    const utkast = f.querySelector('textarea')?.value ?? (sessionStorageLas('nwp-arbetsyta-utkast:' + A.slug) || '');
    const behall = { sida: f.querySelector('[data-falt="sida"]')?.value || mk.sida || '', del: f.querySelector('[data-falt="del"]')?.value || mk.del || '', svar: f.querySelector('#ay-skrivsvar')?.textContent || '' };
    const falt = {}; f.querySelectorAll('[data-uppdrag]').forEach((x) => { falt[x.dataset.uppdrag] = x.value; });  // uppdragets fält står kvar när formuläret ritas om
    f.dataset.ritad = form;
    f.innerHTML = `<div class="ay-segment" role="group" aria-label="Avsikt">${[['fraga', 'Fråga'], ['plan', 'Planförslag'], ['andring', 'Ändring']].map(([k, n]) => `<button type="button" data-avsikt="${k}" data-fokus="a-${k}" aria-pressed="${A.avsikt === k}">${n}</button>`).join('')}</div>
      <label class="dolt" for="ay-text">Meddelande</label>
      <textarea id="ay-text" data-fokus="text" placeholder="${A.avsikt === 'andring' ? 'Vad ska ändras, och var?' : A.avsikt === 'plan' ? 'Vad vill du ha en plan för?' : 'Skriv en fråga om läget'}">${e_(utkast)}</textarea>
      ${A.avsikt === 'andring' ? `<div class="ay-skrivrad"><label class="svag">Sida <input data-falt="sida" data-fokus="sida" style="width:110px" class="ay-knapp liten" placeholder="/ (startsidan)"></label><label class="svag">Del <input data-falt="del" data-fokus="del" style="width:140px" class="ay-knapp liten" placeholder="t.ex. första vyn"></label></div>
      <div class="ay-skrivrad"><label class="svag">Uppdrag <select data-uppdrag="typ" data-fokus="u-typ" class="ay-knapp liten">${UPPDRAGSTYPER.map(([v, n]) => `<option value="${v}">${n}</option>`).join('')}</select></label>
        <label class="svag">Från <select data-uppdrag="avsandare" data-fokus="u-avs" class="ay-knapp liten"><option value="agaren">mig (ägaren)</option><option value="kunden">kunden</option></select></label></div>
      <p class="svag" style="margin:0" id="ay-uppdragstext"></p>
      <label class="svag" for="ay-resultat">Önskat resultat</label><input id="ay-resultat" data-uppdrag="resultat" data-fokus="u-resultat" class="ay-knapp">
      <label class="svag" for="ay-omfattning">Omfattning: en rad per brist, område eller del (för Bygg ut: vägarna, till exempel /tjanster/)</label><textarea id="ay-omfattning" data-uppdrag="omfattning" data-fokus="u-omfattning" rows="3"></textarea>
      <label class="svag" for="ay-bevara">Bevara: en rad per sak som ska stå kvar ("inget särskilt" om inget)</label><textarea id="ay-bevara" data-uppdrag="bevara" data-fokus="u-bevara" rows="2"></textarea>
      <label class="svag" for="ay-belagg" data-kundbelagg hidden>Var kundens egna ord står (samtalet, meddelandet och tiden)</label><input id="ay-belagg" data-uppdrag="belagg" data-kundbelagg hidden class="ay-knapp">` : ''}
      ${A.avsikt === 'andring' && A.lage.blind ? '<p class="ay-notis varn" style="margin:0">En ändring som du skickar är ditt val av kandidaten i körningen. Bedömningarna visas efter det.</p>' : ''}
      <div class="ay-markering" id="ay-markering">${gallerRad()}</div>
      <div id="ay-inaktuell"></div>
      <div class="ay-skrivrad"><span class="svag" id="ay-skrivsvar" role="status" aria-live="polite"></span><span class="ay-knapprad">
        ${A.avsikt === 'andring' ? `<button class="ay-knapp" type="submit" data-skicka="partner" data-fokus="s-partner">Be partnern formulera</button><button class="ay-knapp primar" type="button" data-skicka="andring" data-fokus="s-andring">Spara uppdraget</button>`
          : `<button class="ay-knapp primar" type="submit" data-skicka="partner" data-fokus="s-partner">Skicka</button>`}</span></div>`;
    if (behall.sida && f.querySelector('[data-falt="sida"]')) f.querySelector('[data-falt="sida"]').value = behall.sida;
    if (behall.del && f.querySelector('[data-falt="del"]')) f.querySelector('[data-falt="del"]').value = behall.del;
    if (behall.svar) document.getElementById('ay-skrivsvar').textContent = behall.svar;
    Object.entries(falt).forEach(([k, v]) => { const x = f.querySelector(`[data-uppdrag="${k}"]`); if (x) x.value = v; });
    visaUppdragstext();
    uppdateraSkrivstatus();
  }
  // de tre uppdragen (ägarens uppdrag 2026-10-09, punkt 8); benämningen är det som startas
  const UPPDRAGSTYPER = [['ratta', 'Rätta'], ['omarbeta', 'Omarbeta designen'], ['bygg_ut', 'Bygg ut']];
  const UPPDRAGSHJALP = { ratta: 'Rätta: de angivna bristerna inom befintlig omfattning. Inga nya sidor, sektioner eller funktioner.',
    omarbeta: 'Omarbeta designen: komposition, bildregi, typografi, rytm och hierarki inom det avtalade innehållet. En separat granskare jämför före och efter i bilderna.',
    bygg_ut: 'Bygg ut: de överenskomna sektionerna, undersidorna och funktionerna i förslagets form.' };
  function visaUppdragstext() {
    const f = document.getElementById('ay-skriv'); const typ = f?.querySelector('[data-uppdrag="typ"]')?.value; const p = document.getElementById('ay-uppdragstext');
    if (p) p.textContent = UPPDRAGSHJALP[typ] || '';
    const kund = f?.querySelector('[data-uppdrag="avsandare"]')?.value === 'kunden';
    f?.querySelectorAll('[data-kundbelagg]').forEach((x) => { x.hidden = !kund; });
  }
  function sessionStorageLas(k) { try { return sessionStorage.getItem(k); } catch { return null; } }
  function uppdateraSkrivstatus() {
    const p = A.partner, upptagen = (p?.meddelanden || []).some((m) => m.lage === 'arbetar') || (p?.andra_processer || []).length;
    const knapp = document.querySelector('#ay-skriv [data-skicka="partner"]');
    if (knapp) knapp.disabled = Boolean(upptagen);
    const a = document.querySelector('#ay-skriv [data-skicka="andring"]');
    if (a) {
      const k = A.lage.korning || {}, mk = markering();
      const hinder = !A.mark || !mk.kandidat || !mk.version_hel ? 'markera kandidaten ändringen gäller (under Kandidater)' : inaktuellMark() ? 'markeringen är inaktuell: stäm av mot den aktuella versionen'
        : !['klar_for_bedomning', 'fel'].includes(k.steg) ? 'körningen väntar inte på ditt beslut' : null;
      a.disabled = Boolean(hinder); a.title = hinder || '';
      const m = document.getElementById('ay-markering'); if (m) m.dataset.hinder = hinder || '';
    }
    // notisen om en inaktuell markering uppdateras också medan du skriver, utan att fokus flyttas
    const ruta = document.getElementById('ay-inaktuell'), gammal = inaktuellMark();
    if (ruta && (ruta.dataset.text || '') !== (gammal || '')) {
      ruta.dataset.text = gammal || '';
      ruta.innerHTML = gammal ? `<p class="ay-notis varn" style="margin:0">Inaktuell markering: ${e_(gammal)}. Stäm av mot den aktuella versionen innan du skickar. <button class="ay-knapp liten" type="button" data-stam-av data-fokus="stam-av">Stäm av mot den aktuella</button></p>` : '';
    }
    const s = document.getElementById('ay-skrivsvar');
    if (s && upptagen && !s.textContent) s.textContent = (p?.andra_processer || []).length ? 'Sessionen är öppen i en annan process.' : 'Partnern svarar…';
  }

  async function skickaPartner() {
    const t = document.getElementById('ay-text'), svar = document.getElementById('ay-skrivsvar');
    const text = t.value.trim(); if (!text) { svar.textContent = 'Skriv ett meddelande först.'; t.focus(); return; }
    const mk = markering();
    const kontext = { kandidat: mk.kandidat, version: mk.version, vy: mk.vy, korning: mk.korning, fil: mk.fil || null,
      sida: document.querySelector('[data-falt="sida"]')?.value || null, del: document.querySelector('[data-falt="del"]')?.value || null };
    const id = await innehallsId('m', [A.slug, A.partner?.antal ?? A.lage?.partner?.antal ?? 0, A.avsikt, text, kontext]);  // samma tur i två flikar: samma id; ett senare "Ja": ett nytt
    svar.textContent = 'Skickar…';
    try {
      const r = await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/partner', { meddelande_id: id, text, avsikt: A.avsikt, kontext });
      t.value = ''; try { sessionStorage.removeItem('nwp-arbetsyta-utkast:' + A.slug); } catch { /* */ }
      svar.textContent = r.upprepat ? 'Samma meddelande har redan skickats; svaret står i samtalet. Ändra texten för en ny fråga.' : 'Skickat. Partnern svarar i samma session.';
      await laddaPartner();
    } catch (err) { svar.textContent = (err.status === 409 ? '' : 'Svaret gick inte att bekräfta: ') + err.message + (err.status === 409 ? '' : '. Försök igen: samma text ger samma meddelande-id, så inget skickas två gånger.'); }
  }
  async function skickaAndring() {
    const t = document.getElementById('ay-text'), svar = document.getElementById('ay-skrivsvar'), mk = markering();
    const text = t.value.trim(); if (!text) { svar.textContent = 'Skriv vad som ska ändras, med dina eller kundens egna ord.'; t.focus(); return; }
    if (!A.mark || !A.mark.kandidat || !A.mark.version_hel) { svar.textContent = 'Markera kandidaten uppdraget gäller först (välj den under Kandidater).'; return; }
    if (inaktuellMark()) { svar.textContent = 'Inaktuell: ' + inaktuellMark() + '. Stäm av mot den aktuella versionen först.'; return; }
    const u = (k) => document.querySelector(`#ay-skriv [data-uppdrag="${k}"]`)?.value || '';
    const rader = (k) => u(k).split('\n').map((x) => x.trim()).filter(Boolean);
    const uppdrag = { typ: u('typ'), resultat: u('resultat').trim(), omfattning: rader('omfattning'), bevara: rader('bevara') };
    const saknas = !uppdrag.resultat ? 'det önskade resultatet' : !uppdrag.omfattning.length ? 'omfattningen' : !uppdrag.bevara.length ? 'vad som ska bevaras' : u('avsandare') === 'kunden' && !u('belagg').trim() ? 'var kundens ord står' : null;
    if (saknas) { svar.textContent = 'Uppdraget saknar ' + saknas + '.'; return; }
    const body = { text, beslut: 'uppdrag', uppdrag, kandidat: mk.kandidat, version: mk.version_hel, korning: mk.korning,
      vy: mk.vy, fil: mk.fil || null, sida: document.querySelector('[data-falt="sida"]')?.value || null, del: document.querySelector('[data-falt="del"]')?.value || null,
      ...(u('avsandare') === 'kunden' ? { avsandare: 'kunden', belagg: u('belagg').trim() } : {}) };
    const id = await innehallsId('a', [A.slug, body.text, body.kandidat, body.version, body.korning, body.vy, body.fil, body.sida, body.del, uppdrag, body.avsandare || '']);
    svar.textContent = 'Sparar uppdraget…';
    try {
      await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/andring', Object.assign({ andring_id: id }, body));
      t.value = ''; sparaMark(null); ritaGaller(); try { sessionStorage.removeItem('nwp-arbetsyta-utkast:' + A.slug); } catch { /* */ }  // som skickaPartner: en skickad ändring kommer inte tillbaka som utkast
      const f_ = document.getElementById('ay-skriv'); if (f_) { f_.dataset.ritad = ''; ritaSkriv(); }
      const nasta = (A.lage.handlingar || []).find((h) => h.id === 'valda');
      (document.getElementById('ay-skrivsvar') || svar).textContent = 'Uppdraget är sparat i domloggen' + (body.avsandare === 'kunden' ? ' som kundens beslut' : '') + ', bundet till kandidat och version. Inget arbete har startat: starta det under Kontroller' + (nasta ? ' (' + nasta.text + ').' : '. Läs om läget om knappen inte syns.');
    } catch (err) { svar.textContent = err.status === 409 ? 'Inaktuell: ' + err.message + ' Stäm av mot den aktuella versionen och läs igenom ändringen innan du skickar igen.' : 'Svaret gick inte att bekräfta: ' + err.message + '. Försök igen: samma ändring ger samma id, så den sparas inte två gånger.'; }
  }

  // --- handlingarna: flödets befintliga start, samma start-id som Flöde ---
  async function handling(id, bekraftad) {
    if (A.pagar) return;  // en begäran väntar på svar: ett dubbelklick eller ett extra klick skickar ingen andra
    if (['stoppa', 'stoppa-overgang'].includes(id) && !bekraftad) {
      A.bekrafta = { id, text: id === 'stoppa' ? 'Stoppa arbetaren och dess sessioner? Det som är klart bevaras; körningen kan återupptas med Återuppta arbetet.' : 'Begär stopp av helbygget, exporten eller förhandsvisningen? Stoppet sparas före processen nås; arbetets slutpost säger vad som hann bli klart.' };
      rita(); document.querySelector('[data-fokus="bekrafta"]')?.focus(); return;
    }
    A.bekrafta = null;
    // kunden tas när begäran skickas: byter ägaren kund medan svaret dröjer skrivs svaret aldrig i den andra kundens vy
    const slug = A.slug, nyckel = 'nwp-start:' + slug + ':' + id, startId = nyttId(nyckel);
    A.pagar = id; A.svar = 'Skickar begäran…'; rita();
    try {
      const r = await postJson('/api/flode/' + encodeURIComponent(slug) + '/start', { handling: id, start_id: startId });
      let d = null;
      try { d = await hamta('/api/arbetsyta/' + encodeURIComponent(slug)); slappId(nyckel, startId); } catch { /* läget lästes inte om: samma start-id används vid nästa försök */ }
      if (A.slug !== slug) { A.pagar = null; rita(); return; }
      A.fokusStart = startId;
      if (d) tillampa(d);
      A.svar = (r.besked || 'Begäran är registrerad.') + ` (start-id ${startId.slice(0, 8)})`;
      if (A.vy !== '' && !STOPP.includes(id)) { location.hash = '#/arbetsyta/' + encodeURIComponent(slug); return; }
    } catch (err) { if (A.slug === slug) A.svar = 'Svaret gick inte att bekräfta: ' + err.message + '. Läs läget eller försök igen; samma start-id används.'; } finally { A.pagar = null; }
    rita();
  }

  // --- byggflödet ---
  function flode() {
    const l = A.lage, sess = l.sessioner || [];
    const klass = (s) => ['skapat', 'kontrollerat', 'beslutat'].includes(s) ? 'data-klar' : s === 'pågår' ? 'data-pagar' : ['stoppat', 'underkänt'].includes(s) ? 'data-stopp' : s === 'väntar på ägaren' ? 'data-vantar' : '';
    const grupper = {};
    for (const s of sess) { const g = s.kalla === 'partnersamtalet' ? 'Arbetsledning' : s.roll === 'helbygge' ? 'Helbygget' : s.kandidat ? 'Kandidat: ' + etikett(s.kandidat) : 'Research och plan'; (grupper[g] = grupper[g] || []).push(s); }
    const vald = sess.find((s) => s.session_id === A.folj);
    return `<ol class="ay-stegrad" aria-label="Kundens observerade förlopp">${(l.steg || []).map((s) => `<li ${klass(s.status)}><span class="nod">${e_(s.nr)}</span><span class="namn">${e_(s.namn)}</span><span class="status">${e_(s.status)}</span></li>`).join('')}</ol>
      <div class="ay-grupper">
        ${l.ab_dold ? `<div class="ay-notis">${e_(l.dold || 'Kunden är en arm i en blind jämförelse som du inte har valt i än.')} Flödet visas efter ditt val i Jämförelser, så att jämförelsen förblir blind.</div>` : ''}
        ${l.blind ? '<div class="ay-notis">Ditt första val i körningen är inte gjort: förslagen har neutrala etiketter, och bedömningar, skäl och sökvägar i aktiviteten visas efter valet.</div>' : ''}
        ${l.ab_dold ? '' : beskedpanel()}
        ${Object.keys(grupper).length ? Object.entries(grupper).map(([g, ss]) => `<section class="ay-panel ay-grupp" aria-label="${e_(g)}"><div class="ay-panelhuvud"><h2>${e_(g)}</h2><span class="svag">${ss.length} sessioner</span></div><div class="ay-panelkropp">${ss.map(sessionskort).join('')}</div></section>`).join('')
          : '<div class="ay-tom">Inga sessioner i körningen än. När en körning startar dyker dess sessioner upp här av sig själva.</div>'}
        ${vald ? `<section class="ay-panel" aria-labelledby="ay-detalj-rubrik"><div class="ay-panelhuvud"><h2 id="ay-detalj-rubrik">${e_(roll(vald))}${vald.kandidat ? ' · ' + e_(etikett(vald.kandidat)) : ''}</h2>${lagechip(vald.lage, vald.lage_text)}<button class="ay-knapp liten" type="button" data-folj-slut>Stäng</button></div><div class="ay-panelkropp ay-detalj">${detalj(vald)}</div></section>` : ''}
        ${l.ab_dold ? '' : stegdetalj()}
        <section class="ay-panel"><details class="metod" data-oppen="metod"${oppen('metod')}><summary>Så är flödet tänkt (metodkartan, README)</summary><div class="ay-panelkropp" id="ay-metod">${metod()}</div></details></section>
        ${pilotpanel()}
        <section class="ay-panel" aria-labelledby="ay-system"><div class="ay-panelhuvud"><h2 id="ay-system">Bevakning och systemförbättring, skilt från kundproduktionen</h2></div><div class="ay-panelkropp">${bevakningsvy()}<div class="ay-knapprad"><a class="ay-knapp liten" href="#/underhall">Underhåll och verktygslådan</a><a class="ay-knapp liten" href="#/kirurgen">Kirurgen och förbättringsloopen</a><a class="ay-knapp liten" href="#/backlog">Backlog</a><a class="ay-knapp liten" href="#/kalibrering">Kalibrering</a><a class="ay-knapp liten" href="#/dokumentation">Dokumentation och rapporter</a></div></div></section>
      </div>
      <section class="ay-panel" aria-labelledby="ay-tl"><div class="ay-panelhuvud"><h2 id="ay-tl">Sessionsflöde</h2>${anslutning()}</div><div class="ay-panelkropp">
        <ul class="ay-tidslinje">${tidslinje().map((x) => `<li><time datetime="${e_(x.tid)}">${e_(klocka(x.tid).slice(0, 5))}</time><span>${e_(x.text)}</span></li>`).join('') || '<li><span class="dampad">Inget observerat än.</span></li>'}</ul>
        ${(l.helbygge || []).length ? `<h3 style="margin:14px 0 6px">Helbyggets körningar (historik)</h3><ul class="ay-tidslinje">${l.helbygge.map((k) => `<li><time>${e_(k.id.slice(9, 13))}</time><span>${e_(k.id)}: ${e_(LAGEN[k.lage] || k.lage)}${k.slutkod != null ? ', slutkod ' + e_(k.slutkod) : ''}${k.uteblev ? ', slutposten uteblev' : ''}</span></li>`).join('')}</ul>` : ''}</div></section>`;
  }
  // Flöde i Byggflöde (ägarens mandat 2026-10-09 ~18:28Z, "Gör det det du anser är rekommendationen"): samma läge som
  // förut (dash.flode genom arbetsyta.lage). En fil som finns är inte ett kontrollerat steg; stegen gäller den aktuella
  // körningen. Starterna går genom handling(), med samma start-id som arbetsytans kontroller.
  const STOPP = ['stoppa', 'stoppa-overgang'];
  const sakerLank = (u) => (/^(\/(?!\/)|https?:\/\/)/.test(String(u || '')) ? String(u) : null);
  const kodtext_ = (t) => e_(t).replace(/`([^`]+)`/g, '<code>$1</code>');
  const BESKEDTON = (s) => s === 'ja' ? 'ok' : s === 'nej' ? 'fel' : ['historiskt', 'ja med villkor'].includes(s) ? 'varn' : '';
  const STEGTON = (s) => ['skapat', 'kontrollerat', 'beslutat'].includes(s) ? 'ok' : ['stoppat', 'underkänt'].includes(s) ? 'fel' : ['väntar på ägaren', 'inaktuellt'].includes(s) ? 'varn' : s === 'pågår' ? 'info' : '';
  const ton = (t, text) => `<span class="ay-ton"${t ? ` data-ton="${t}"` : ''}>${e_(text)}</span>`;
  const oppen = (k) => (A.oppna || new Set()).has(k) ? ' open' : '';
  function poster(rubrik, lista) {
    if (!lista || !lista.length) return '';
    return `<div class="ay-poster"><h4>${e_(rubrik)}</h4><ul>${lista.map((x) => typeof x === 'string' ? `<li>${kodtext_(x)}</li>`
      : `<li>${sakerLank(x.lank) ? `<a href="${e_(sakerLank(x.lank))}" target="_blank" rel="noopener">${e_(x.text)}</a>` : kodtext_(x.text)}${x.tid ? ` <span class="svag">${e_(kort(x.tid))}</span>` : ''}${x.sha ? ` <code title="sha256, beräknad nu">${e_(x.sha)}</code>` : ''}</li>`).join('')}</ul></div>`;
  }
  function beskedpanel() {
    const l = A.lage, b = l.besked, hs = l.handlingar || [], m = l.startmiljo;
    const stopp = hs.filter((h) => STOPP.includes(h.id)), ovriga = hs.filter((h) => !STOPP.includes(h.id));
    const knappar = A.bekrafta ? `<p style="margin:0">${e_(A.bekrafta.text)}</p><div class="ay-knapprad"><button class="ay-knapp fara" type="button" data-handling="${e_(A.bekrafta.id)}" data-bekraftad data-fokus="bf-bekrafta">Stoppa</button><button class="ay-knapp" type="button" data-avbryt-bekraftelse data-fokus="bf-avbryt">Avbryt</button></div>`
      : `<div class="ay-knapprad">${ovriga.map((h) => `<button class="ay-knapp primar" type="button" data-handling="${e_(h.id)}" data-fokus="bf-${e_(h.id)}"${h.hinder || A.pagar ? ' aria-disabled="true"' : ''}${h.hinder ? ' title="' + e_(h.hinder) + '"' : ''}>${e_(h.text)}</button>`).join('')}
         ${stopp.map((h) => `<button class="ay-knapp fara" type="button" data-handling="${e_(h.id)}" data-fokus="bf-${e_(h.id)}"${A.pagar ? ' aria-disabled="true"' : ''}>${e_(h.text || 'Stoppa')}</button>`).join('')}
         ${hs.length ? '' : '<span class="dampad">Ingen handling är möjlig just nu.</span>'}</div>`;
    return `<section class="ay-panel" aria-labelledby="ay-besked-rubrik"><div class="ay-panelhuvud"><h2 id="ay-besked-rubrik" tabindex="-1">Aktuellt besked</h2>
        <span class="svag">${b?.version ? 'Byggversion ' + e_(String(b.version).slice(0, 12)) + ', ' : ''}${b?.tid ? 'slutpost ' + e_(kort(b.tid)) : 'ingen slutpost än'}</span></div>
      <div class="ay-panelkropp ay-besked">
        <p class="svag" style="margin:0">Godkännandena gäller bara angiven version och omfattning.</p>
        ${(b?.tillstand || []).length ? `<dl>${b.tillstand.map((r) => `<div><dt>${e_(r.namn)} ${ton(BESKEDTON(r.status), r.status)}</dt><dd>${e_(r.text)}${r.omfattning ? `<span class="svag">Omfattning: ${e_(r.omfattning)}</span>` : ''}</dd></div>`).join('')}</dl>` : '<p class="svag" style="margin:0">Inget besked än: körningen har ingen slutpost.</p>'}
        ${poster('Kontrollera underlaget', b?.filer)}
        ${m ? `<p class="svag" style="margin:0">Startmiljö: sandlåda ${e_(m.sandlada)}${m.kundstart_lager ? '; Kundstarts ärendelager finns' : ''} (ärvd från dashboardens process).</p>` : ''}
        ${knappar}
        ${ovriga.filter((h) => h.hinder).map((h) => `<p class="svag" style="margin:0">${e_(h.text)} går inte att starta: ${e_(h.hinder)}</p>`).join('')}
        <p class="svag" style="margin:0" role="status" aria-live="polite" id="ay-handlingssvar">${e_(A.svar)}</p>
        <p class="svag" style="margin:0">En startknapp beställer bara det namngivna steget. Att öppna vyn eller välja ett förslag startar inget arbete.</p>
      </div></section>`;
  }
  function stegdetalj() {
    const l = A.lage, steg = l.steg || [];
    if (!steg.length) return '';
    return `<section class="ay-panel" aria-labelledby="ay-steg-rubrik"><div class="ay-panelhuvud"><h2 id="ay-steg-rubrik">Stegen i detalj</h2>
        <span class="svag">${l.korning?.startad ? `Körningen ${e_(kort(l.korning.startad))}${l.korning.lage ? ', ' + e_(LAGESNAMN[l.korning.lage] || l.korning.lage) : ''}` : 'Ingen körning'}</span></div>
      <div class="ay-panelkropp ay-stegdetalj">
        ${steg.map((x) => `<details data-oppen="steg-${e_(x.nr)}"${oppen('steg-' + x.nr)}><summary><span class="nr">${e_(x.nr)}.</span> ${e_(x.namn)} ${ton(STEGTON(x.status), x.status)}</summary>
          ${poster('Underlag och versioner', x.underlag)}${poster('Vad steget producerade', x.utfall)}${poster('Kontroller och bedömningar', x.kontroller)}
          ${poster('Beslut', x.beslut)}${poster('Fel, begränsningar och det som inte är verifierat', x.brister)}
          ${x.nasta ? `<p class="svag" style="margin:6px 0 0">Nästa: ${kodtext_(x.nasta)}</p>` : ''}</details>`).join('')}
        <p class="svag" style="margin:0">Stegen gäller den aktuella körningen: det som hör till en tidigare körning är inaktuellt, och det som inte går att knyta till den är inte observerat. En fil som finns är inte ett kontrollerat steg.</p>
      </div></section>`;
  }
  function pilotpanel() {
    const p = A.pilot || [];
    if (!p.length) return '';
    return `<section class="ay-panel"><details data-oppen="pilot"${oppen('pilot')}><summary>Figma-metodprovet (${p.length} moment)</summary><div class="ay-panelkropp">
      <p class="svag" style="margin:0">Pilotens tre moment: A återskapar en referens, B anpassar till kundens material, C överför till webb. Inget i leveransen är verifierat genom piloten.</p>
      ${p.map((m) => `<div class="ay-pilot"><h3>${e_(m.moment || m.id)} ${ton(STEGTON(m.status), m.status)}</h3>
        ${m.status_skal ? `<p style="margin:0">Enligt VERSION.json: ${e_(m.status_skal)}</p>` : ''}
        <p class="svag" style="margin:0">Aktuell version ${e_(m.aktuell || 'inte observerat')}, Figma-fil ${e_(m.figma?.fil || '–')}${m.tid ? ', ' + e_(kort(m.tid)) : ''}</p>
        ${poster('Kontroller', m.kontroller)}${poster('Bedömningar (bilderna först, skaparens förklaring sedan)', m.bedomningar)}
        ${(m.bilder || []).filter((b) => sakerLank(b.lank)).length ? `<div class="ay-pilotbilder">${m.bilder.filter((b) => sakerLank(b.lank)).map((b) => `<figure><a href="${e_(sakerLank(b.lank))}" target="_blank" rel="noopener" title="${e_(b.text)}"><img src="${e_(sakerLank(b.lank))}" alt="${e_(b.text)}, version ${e_(b.version)}" loading="lazy"></a><figcaption>version ${e_(b.version)}</figcaption></figure>`).join('')}</div>` : ''}
        ${poster('Fynd', m.fynd)}</div>`).join('')}
    </div></details></section>`;
  }
  document.addEventListener('toggle', (ev) => { const k = ev.target.dataset?.oppen; if (!k) return; A.oppna = A.oppna || new Set(); ev.target.open ? A.oppna.add(k) : A.oppna.delete(k); }, true);

  // --- bevakningen: Nortropics löpande bevakning (kontroller/bevakning.py), läst ur /api/bevakning ---
  const BEVLAGE = { bevakad: 'bevakad', ofullstandig: 'ofullständig', inaktuell: 'inaktuell', saknar_tackning: 'saknar täckning' };
  const BEVUTFALL = { misslyckad: 'misslyckad', ofullstandig: 'ofullständig', ej_utford: 'inte gjord', fynd: 'fynd', inget_nytt: 'inget nytt', inte_dags: 'inte prövad än' };
  async function laddaBevakning() {
    A.bevakningLast = Date.now();
    try { A.bevakning = await hamta('/api/bevakning'); } catch (e) { A.bevakning = { fel: e.message }; }
    if (A.vy === 'flode') rita();
  }
  function bevakningsvy() {
    const b = A.bevakning;
    if (!b) return '<p class="svag" style="margin:0 0 10px">Läser bevakningen…</p>';
    if (b.fel) return `<p class="ay-notis fel" style="margin:0 0 10px">Bevakningen gick inte att läsa: ${e_(b.fel)}</p>`;
    const s = b.senast, d = b.dag || {};
    const lage = !s ? 'Inte aktiv: bevakningen har aldrig körts.'
      : !b.aktiv ? `Inte aktiv: den senaste körningen (${e_(kort(s.start))}) var manuell, och ingen schemalagd körning har gjorts än.`
        : `Aktiv: den senaste schemalagda körningen var ${e_(kort(s.start))}${s.sen_timmar ? `, ${e_(s.sen_timmar)} timmar efter klockslaget` : ''}; utfall ${e_(s.utfall)}.`;
    const fynd = (d.handlingsbart || []).slice(0, 8), ej = d.kontroller_som_inte_lyckades || [], fb = b.forbattringar || {};
    const tack = Object.values(b.tackning || {});
    return `<div class="ay-bevakning">
      <p style="margin:0">${lage} Nästa planerade körning: ${e_(kort(b.nasta))} (${e_(b.klockslag)} ${e_(b.tidszon)}).</p>
      ${d.besked ? `<p style="margin:8px 0 0"><b>I dag: ${e_(d.besked)}.</b></p>` : ''}
      ${fynd.length ? `<ul class="ay-bev-lista">${fynd.map((f) => `<li><b>${e_(f.fraga)}</b>: ${e_(String(f.text).slice(0, 280))}${f.konsekvens ? ` <span class="svag">Konsekvens: ${e_(f.konsekvens)}.</span>` : ''}${f.belagg ? ` <span class="svag">Belägg: <code>${e_(String(f.belagg).slice(0, 160))}</code></span>` : ''}</li>`).join('')}</ul>` : ''}
      ${ej.length ? `<details class="ay-bev-del"><summary>Kontroller som inte lyckades eller inte gjordes (${ej.length})</summary><ul class="ay-bev-lista">${ej.map((x) => `<li><b>${e_(x.id)}</b>: ${e_(BEVUTFALL[x.utfall] || x.utfall)}. ${e_((x.problem || []).join('; ').slice(0, 300))}</li>`).join('')}</ul></details>` : ''}
      <details class="ay-bev-del"><summary>Täckning per område (${tack.filter((t) => t.lage === 'bevakad').length} av ${tack.length} bevakade)</summary>
        <ul class="ay-bev-tackning">${tack.map((t) => `<li data-lage="${e_(t.lage)}"><span>${e_(t.namn)}</span><b>${e_(BEVLAGE[t.lage] || t.lage)}</b>${t.luckor.length ? `<span class="svag">Lucka: ${e_(t.luckor.join('; '))}</span>` : ''}</li>`).join('')}</ul></details>
      <details class="ay-bev-del"><summary>Frågorna (${(b.fragor || []).length}): senaste lyckade kontroll, fel och nästa</summary>
        <ul class="ay-bev-lista">${(b.fragor || []).map((q) => `<li><b>${e_(q.id)}</b>: ${e_(BEVUTFALL[q.utfall] || q.utfall || 'inte prövad')}. Senast lyckad ${e_(q.senast_lyckad ? kort(q.senast_lyckad) : 'aldrig')}, ${e_(String(q.nasta || '').includes('T') ? 'nästa ' + kort(q.nasta) : (q.nasta || 'nästa okänd'))} (${e_(q.kontroll.join(', '))}, ${e_(q.intervall)}).${(q.problem || []).length ? ` <span class="svag">${e_(q.problem.join('; ').slice(0, 240))}</span>` : ''}</li>`).join('')}</ul></details>
      ${(b.luckor || []).length ? `<details class="ay-bev-del"><summary>Luckor (${b.luckor.length}): ansvar, nästa åtgärd och förutsättning</summary><ul class="ay-bev-lista">${b.luckor.map((x) => `<li><b>${e_(x.lucka)}</b><br><span class="svag">Ansvar: ${e_(x.ansvar)}. Nästa: ${e_(x.nasta_atgard)}. Förutsättning: ${e_(x.forutsattning)}. Post: ${e_(x.post)}.</span></li>`).join('')}</ul></details>` : ''}
      <p class="svag" style="margin:8px 0 0">Codex-granskningen: ${b.codex?.aktiv ? 'automatisk enligt frågornas intervall' : 'avstängd'}; ${e_((b.codex?.dags || []).length)} frågor väntar på granskning${(b.codex?.korningar || []).length ? `; senast ${e_(kort(b.codex.korningar.at(-1).tid))}: ${e_(b.codex.korningar.at(-1).fraga)}, ${b.codex.korningar.at(-1).fel ? 'föll' : 'klar'}${b.codex.korningar.at(-1).tokens ? `, ${e_(b.codex.korningar.at(-1).tokens)} tokens` : ''}` : ''}.</p>
      ${b.forbrukning ? `<p class="svag" style="margin:4px 0 0">Förbrukning senaste 7 dygnen (uppmätt; listpris, inte fakturerat, och inte kvot): ${e_(b.forbrukning.sessioner)} motorsessioner, ${e_(b.forbrukning.listpris_usd)} USD i listpris, ${e_(b.forbrukning.tokens_ut)} utgående tokens; Codex ${e_(b.forbrukning.codex?.granskningar ?? 0)} granskningar, ${e_(b.forbrukning.codex?.tokens ?? 0)} tokens.</p>` : ''}
      <p class="svag" style="margin:8px 0 0">Förbättringsloopen, bevakningens poster: ${e_(fb.bevakade ?? 0)} bevakade, ${e_(fb.bedomda ?? 0)} bedömda, ${e_(fb.provade ?? 0)} prövade, ${e_(fb.inforda ?? 0)} införda, ${e_(fb.verifierade ?? 0)} verifierade (Kirurgen).</p>
    </div>`;
  }
  function detalj(s) {
    const h = s.aktivitet?.handelser || [];
    const skills = [...new Set(h.filter((x) => x.verktyg === 'Skill' && x.skill).map((x) => x.skill))];
    const lasta = h.filter((x) => x.verktyg === 'Read' && x.fil), skrivna = h.filter((x) => ['Edit', 'Write', 'MultiEdit'].includes(x.verktyg) && x.fil);
    const k = (A.lage.kandidater || []).find((x) => x.id === s.kandidat);
    return `<div><h4>Aktivitet</h4>${h.length ? `<ul class="ay-handelser">${h.slice(-10).map((x) => `<li><time>${e_(klocka(x.tid).slice(0, 5))}</time><span>${e_(x.verktyg)}, ${e_(x.utfall)}</span></li>`).join('')}</ul>` : '<p class="svag">Inget observerat.</p>'}</div>
      <div><h4>Underlag (lästa filer)</h4>${lasta.length ? `<ul class="ay-handelser">${lasta.slice(-8).map((x) => `<li><span>${e_(x.utfall)}</span><span class="mono">${e_(x.fil.split('/').slice(-3).join('/'))}</span></li>`).join('')}</ul>` : `<p class="svag">${A.lage.blind ? 'Visas efter ditt första val.' : 'Inga lästa filer observerade.'}</p>`}</div>
      <div><h4>Kompetenser</h4><p class="svag" style="margin:0">${skills.length ? 'Laddade via skillsystemet: ' + e_(skills.join(', ')) : 'Inga skills laddade i de senaste händelserna.'} Laddat är inte tillämpat; tillämpningen bedöms i granskningen.</p></div>
      <div><h4>Resultat</h4><p class="svag" style="margin:0">${skrivna.length ? e_(skrivna.length) + ' skrivna filer observerade. ' : ''}${k ? `${e_(k.etikett)}: ${e_(k.statustext || k.status)}${k.version ? ', version ' + e_(k.version) : ''}.` : ''} ${s.lage === 'avslutad' ? 'Sessionen avslutades; det är inget godkännande.' : ''}</p></div>`;
  }
  function tidslinje() {
    const ut = [], l = A.lage;
    for (const j of l.startjournal || []) {
      ut.push({ tid: j.tid, text: `Begäran ${j.handling || '?'} (start-id ${String(j.start_id).slice(0, 8)}): ${j.status || 'okänd'}${j.stopp_begart ? ', stopp begärt' : ''}${j.slutkod != null ? ', slutkod ' + j.slutkod : ''}${j.process_lever ? ', processen lever' : ''}` });
      if (j.stopp_tid) ut.push({ tid: j.stopp_tid, text: `Stopp begärt för start-id ${String(j.start_id).slice(0, 8)}` });
    }
    for (const s of l.sessioner || []) { if (s.start) ut.push({ tid: s.start, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: startade` }); if (s.slut) ut.push({ tid: s.slut, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: ${s.lage_text || LAGEN[s.lage]}` }); }
    for (const o of l.overlamningar || []) ut.push({ tid: o.tid, text: `Din ändring till ${etikett(o.kandidat)}: ${Object.keys(o.steg).join(' → ').replace(/_/g, ' ')}` });
    if (l.korning?.startad) ut.push({ tid: l.korning.startad, text: `Körningen startade (läge ${l.korning.lage || '?'})${l.korning.start_handling ? ' genom ' + l.korning.start_handling : ''}` });
    return ut.filter((x) => x.tid).sort((a, b) => String(b.tid).localeCompare(String(a.tid))).slice(0, 30);
  }
  function metod() {
    if (!A.metod && A.metodLaser) return '<p class="svag">Läser metodkartan…</p>';
    if (!A.metod) { A.metodLaser = true; hamta('/api/flode').finally(() => { A.metodLaser = false; }).then((d) => { A.metod = d.kedjan; A.pilot = d.pilot || []; if (A.vy === 'flode') rita(); }).catch((e) => { A.metod = { fel: 'Metodkartan gick inte att läsa: ' + e.message }; if (A.vy === 'flode') rita(); }); return '<p class="svag">Läser metodkartan…</p>'; }
    if (A.metod.fel) return `<p class="svag">${e_(A.metod.fel)}</p>`;
    return `<p class="svag">Arbetssättet, ur README.md; inte kundens förlopp.</p><ol style="margin:0;padding-left:18px;display:grid;gap:6px">${(A.metod.steg || []).map((s) => `<li><b>${e_(String(s.steg).replace(/<[^>]+>/g, ''))}</b><div class="svag">${e_(String(s.vem).replace(/<[^>]+>/g, '')).slice(0, 400)}</div>${s.resultat ? `<div class="svag">Resultat: ${e_(String(s.resultat).replace(/<[^>]+>/g, ''))}</div>` : ''}${s.saknas ? `<div>${ton('varn', 'saknas i dag')} <span class="svag">${e_(String(s.saknas).replace(/<[^>]+>/g, ''))}</span></div>` : ''}</li>`).join('')}</ol>`;
  }

  // --- kod och preview ---
  function kodKandidat() { const ks = A.lage?.kandidater || []; return (ks.find((k) => k.id === A.valdKandidat && (k.preview.finns || k.versioner.length)) || ks.find((k) => k.preview.finns || k.versioner.length) || {}).id || null; }
  async function laddaKod(fil, mot) {
    if (!A.lage) return;
    const kid = kodKandidat(), el = document.getElementById('ay-filer'); if (!el) return;
    if (!kid) { el.innerHTML = '<div class="ay-tom">Ingen kandidat med kod än.</div>'; document.getElementById('ay-filvy').innerHTML = ''; return; }
    A.kod.kandidat = kid;
    if (fil !== undefined) A.kod.fil = fil;
    if (mot !== undefined) A.kod.mot = mot;
    const q = new URLSearchParams({ kandidat: kid }); if (A.kod.fil) q.set('fil', A.kod.fil); if (A.kod.mot) q.set('mot', A.kod.mot);
    try { A.kod.data = await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/kod?' + q); }
    catch (err) {
      if (A.kod.mot && /versionen finns inte/.test(err.message)) { A.kod.mot = null; return laddaKod(); }  // versionen syns inte längre: den aktuella förvald
      el.innerHTML = `<div class="ay-notis fel">${e_(err.message)}</div>`; return;
    }
    const d = A.kod.data;
    if (!A.kod.fil && fil === undefined) { const forsta = (d.filer.find((f) => f.andrad) || d.filer[0] || {}).fil; if (forsta) return laddaKod(forsta); }
    el.innerHTML = `<label class="svag" for="ay-kodkand">Kandidat</label><select id="ay-kodkand" class="ay-knapp liten" style="width:100%;margin:4px 0 8px">${(A.lage.kandidater || []).filter((k) => k.preview.finns || k.versioner.length).map((k) => `<option value="${e_(k.id)}"${k.id === kid ? ' selected' : ''}>${e_(k.etikett)}</option>`).join('')}</select>
      <label class="svag" for="ay-kodmot">Jämför med bevarad version</label><select id="ay-kodmot" class="ay-knapp liten" style="width:100%;margin:4px 0 10px">${d.versioner.length ? d.versioner.map((v) => `<option value="${e_(v)}"${v === d.mot ? ' selected' : ''}>${e_(v)}${v === (d.fotograferad || '') ? ' (fotograferad)' : ''}</option>`).join('') : '<option value="">ingen bevarad version</option>'}</select>
      <p class="svag" style="margin:0 0 8px">Arbetsversionen: ${e_(d.arbetsversion)}.${d.blind ? ' DESIGN.md visas efter ditt första val.' : ''}</p>
      <ul class="ay-filtrad">${d.filer.map((f) => `<li><button type="button" data-kodfil="${e_(f.fil)}" aria-current="${f.fil === A.kod.fil}" title="${e_(sajtvag(f.fil))}"><span><bdi>${e_(sajtvag(f.fil))}</bdi></span>${f.ny ? '<span class="andrad">ny</span>' : f.borttagen ? '<span class="andrad">borttagen</span>' : f.andrad ? '<span class="andrad">ändrad</span>' : ''}</button></li>`).join('')}</ul>`;
    ritaFil();
  }
  // versionens namn på filerna (kod/, kod-src/) som projektets egna vägar: sidorna under src/pages/, resten under src/
  const sajtvag = (f) => f === 'DESIGN.md' ? 'DESIGN.md' : f.startsWith('kod/') ? 'src/pages/' + f.slice(4) : f.startsWith('kod-src/') ? 'src/' + f.slice(8) : f;
  function ritaFil() {
    const el = document.getElementById('ay-filvy'), h = document.getElementById('ay-filhuvud'); if (!el) return;
    const f = A.kod.data?.fil;
    if (!f) { h.innerHTML = '<h2 id="ay-fil-rubrik">Fil</h2>'; el.innerHTML = '<div class="ay-tom" style="padding:14px">Välj en fil. Ändrade filer är märkta mot den bevarade versionen.</div>'; return; }
    h.innerHTML = `<h2 id="ay-fil-rubrik" class="mono">${e_(sajtvag(f.fil))}</h2><div class="ay-segment" role="group" aria-label="Visning"><button type="button" data-kodvisning="diff" aria-pressed="${A.kod.visning === 'diff'}">Diff mot ${e_(A.kod.data.mot || '–')}</button><button type="button" data-kodvisning="hel" aria-pressed="${A.kod.visning === 'hel'}">Hela filen</button></div>${f.finns ? `<button class="ay-knapp liten" type="button" data-markera-fil="${e_(sajtvag(f.fil))}">Markera för en ändring</button><button class="ay-knapp liten" type="button" data-oppna-fil="${e_(f.fil)}">Öppna i editorn</button>` : ''}`;
    if (A.kod.visning === 'diff') {
      el.innerHTML = f.diff == null ? '<div class="ay-tom" style="padding:14px">Ingen bevarad version att jämföra med.</div>' : f.diff.length ? `<pre class="ay-kodtext">${f.diff.map((r) => `<span class="${r.startsWith('@@') ? 'hunk' : r.startsWith('+') ? 'plus' : r.startsWith('-') ? 'minus' : ''}">${e_(r)}</span>`).join('')}</pre>` : '<div class="ay-tom" style="padding:14px">Ingen skillnad mot den bevarade versionen.</div>';
    } else el.innerHTML = f.text == null ? '<div class="ay-tom" style="padding:14px">Filen finns inte i arbetsversionen.</div>' : `<pre class="ay-kodtext">${e_(f.text).split('\n').map((r) => `<span>${r || ' '}</span>`).join('')}</pre>`;
    el.querySelector('pre')?.setAttribute('tabindex', '0');  // långa rader rullar i sidled: nås med tangentbordet
  }
  async function laddaLogg(tvinga) {
    const el = document.getElementById('ay-logg'); if (!el || !A.lage) return;
    const nyckel = (A.lage.korning?.startad || '') + (A.lage.helbygge?.[0]?.id || '') + Math.floor(Date.now() / 15000);
    if (!tvinga && nyckel === A.loggNyckel) return;
    A.loggNyckel = nyckel;
    try { A.logg = await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/logg'); } catch (err) { el.innerHTML = `<div class="ay-notis fel">Körningsloggen kunde inte läsas: ${e_(err.message)}</div>`; return; }
    const rull = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    el.innerHTML = (A.logg.loggar || []).length ? A.logg.loggar.map((x) => `<h3 class="mono" style="margin:4px 0">${e_(x.fil)}${x.andrad ? ` <span class="svag">ändrad ${e_(kort(x.andrad))}</span>` : ''}</h3>${x.dold ? `<p class="svag">${e_(x.dold)}</p>` : x.fel ? `<p class="svag">${e_(x.fel)}</p>` : `<pre class="ay-logg">${e_(x.rader.join('\n')) || '(tom)'}</pre>`}`).join('')
      : '<div class="ay-tom">Ingen körningslogg för kunden än.</div>';
    if (rull) el.scrollTop = el.scrollHeight;
  }
  function ritaKodaktivitet() {
    const el = document.getElementById('ay-kodaktivitet'); if (!el) return;
    const sess = (A.lage.sessioner || []).filter((s) => s.session_id && (A.folj ? s.session_id === A.folj : s.kandidat === kodKandidat() || s.roll === 'helbygge'));
    const s = sess[0];
    el.innerHTML = s ? `<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><b>${e_(roll(s))}</b>${lagechip(s.lage, s.lage_text)}</div><ol class="ay-handelser">${(s.aktivitet?.handelser || []).slice(-14).reverse().map((h) => `<li><time>${e_(klocka(h.tid).slice(0, 5))}</time><span>${e_(h.verktyg)}, ${e_(h.utfall)}${h.fil ? ' · ' + e_(h.fil.split('/').slice(-2).join('/')) : ''}</span></li>`).join('')}</ol>`
      : '<div class="ay-tom">Ingen session för den här koden i körningen.</div>';
  }

  // --- panelerna: fälla ihop och dra ---
  function kopplaDelare() {
    document.querySelectorAll('.ay-delare').forEach((d) => {
      const sida = d.dataset.delare, ytan = document.getElementById('ay-ytan');
      const satt = (px) => { px = Math.max(240, Math.min(560, Math.round(px))); ytan.style.setProperty(sida === 'vanster' ? '--ay-vanster' : '--ay-hoger', px + 'px'); d.setAttribute('aria-valuenow', px); sparaLayout({ [sida]: px }); };
      d.setAttribute('aria-valuemin', 240); d.setAttribute('aria-valuemax', 560);
      // en fokuserbar avdelare ska säga sitt värde från början, inte först efter ett drag (WAI-ARIA separator; axe aria-required-attr)
      d.setAttribute('aria-valuenow', parseInt(getComputedStyle(ytan).getPropertyValue(sida === 'vanster' ? '--ay-vanster' : '--ay-hoger')) || (sida === 'vanster' ? 360 : 320));
      d.addEventListener('pointerdown', (ev) => {
        ev.preventDefault(); d.setPointerCapture(ev.pointerId);
        const rect = ytan.getBoundingClientRect();
        const flytta = (e2) => satt(sida === 'vanster' ? e2.clientX - rect.left - 18 : rect.right - e2.clientX - 18);
        d.addEventListener('pointermove', flytta);
        d.addEventListener('pointerup', () => d.removeEventListener('pointermove', flytta), { once: true });
      });
      d.addEventListener('keydown', (ev) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(ev.key)) return;
        ev.preventDefault();
        const nu = parseInt(getComputedStyle(ytan).getPropertyValue(sida === 'vanster' ? '--ay-vanster' : '--ay-hoger')) || 320;
        satt(nu + ((ev.key === 'ArrowRight') === (sida === 'vanster') ? 24 : -24));
      });
    });
  }

  // --- meddelanden: ägaren och sessionerna genom bussen (kontroller/meddelanden.py, dashboard/samverkan.py) ---
  async function laddaSamverkan() {
    if (!A.slug) return;
    const slug = A.slug;
    try { const d = await hamta('/api/arbetsyta/' + encodeURIComponent(slug) + '/meddelanden'); if (slug === A.slug) { A.samverkan = d; ritaVanster(); ritaRakning(); } }
    catch { /* nästa läge försöker igen */ }
  }
  function ritaRakning() { const el = document.getElementById('ay-oppna'); if (el) { const n = A.lage?.samverkan?.oppna || 0; el.textContent = n ? String(n) : ''; el.title = n ? `${n} meddelanden från sessionerna väntar på ditt beslut` : ''; } }
  function ritaVanster() {
    ritaRakning();
    document.querySelectorAll('[data-vflik]').forEach((b) => b.setAttribute('aria-selected', String((A.vflik || 'partner') === b.dataset.vflik)));
    if (A.vflik !== 'meddelanden') { ritaPartner(); ritaSkriv(); return; }
    const chip = document.getElementById('ay-partnerchip'); if (chip) chip.innerHTML = '';
    const el = document.getElementById('ay-samtal'), f = document.getElementById('ay-skriv'); if (!el || !f) return;
    const nere = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    behallFokus(el, () => { el.innerHTML = meddelandelista(); });
    if (nere) el.scrollTop = el.scrollHeight;
    ritaMeddelandeform();
  }
  const ROLLNAMN = (r) => (typeof rollnamn === 'function' ? rollnamn(r) : r);
  function avsandare(a) {
    if (!a) return 'okänd';
    if (a.typ === 'agare') return 'Du';
    if (a.typ === 'extern') return 'Extern granskare: ' + a.namn;
    return `${a.ansvar === 'granskning' ? 'Granskare' : 'Utförare'}${a.roll ? ' (' + ROLLNAMN(a.roll) + ')' : ''}${a.kandidat ? ' · ' + etikett(a.kandidat) : ''}`;
  }
  function mottagare(m) {
    if (!m) return '?';
    if (m.typ === 'agare') return 'dig';
    if (m.typ === 'extern') return 'den externa granskaren ' + m.namn;
    const vem = `${m.ansvar === 'granskning' ? 'granskaren' : 'utföraren'}${m.kandidat ? ' för ' + etikett(m.kandidat) : ''}`;
    return m.typ === 'adress' ? vem + ' (sessionen som arbetar med den nu eller härnäst)' : vem + ' (session ' + String(m.session_id).slice(0, 8) + ')';
  }
  const ATGARDER = { forslag: 'förslag', granskningsfynd: 'granskningsfynd', andringsinstruktion: 'begäran om rättelse' };
  const STEG = [['sparat', 'sparat'], ['koat', 'köat'], ['levererat', 'levererat'], ['mottaget', 'mottaget'], ['besvarat', 'besvarat'], ['genomfort', 'genomfört']];
  function leveransrad(m) {
    const sista = (m.handelser || []).slice(-1)[0] || {};
    if (['okant', 'ej_levererat', 'tillbaka'].includes(m.lage)) return `<div class="ay-leverans-text" data-lage="${e_(m.lage)}"><b>${e_(m.lage_text)}</b>${sista.notis ? ': ' + e_(sista.notis) : ''}</div>`;
    const i = STEG.findIndex(([k]) => k === m.lage);
    const stegen = m.syfte === 'andringsinstruktion' ? STEG : STEG.slice(0, 5);
    return `<ol class="ay-leverans" aria-label="Leveransläge: ${e_(m.lage_text)}">${stegen.map(([k, n], j) => { const h = (m.handelser || []).filter((x) => x.lage === k).slice(-1)[0];
      return `<li data-gjort="${j <= i}"${j === i ? ' aria-current="step"' : ''} title="${e_(h ? klocka(h.tid) + (h.bevis ? ' · ' + h.bevis : '') : 'inte belagt')}">${n}</li>`; }).join('')}</ol>`;
  }
  function meddelandekort(m) {
    const egen = !m.agent, avvisad = m.beslut?.val === 'avvisa';
    const g = m.genomforande;
    const knappar = m.agent && m.mottagare?.typ === 'agare' && !m.beslut && !A.samverkan?.blind
      ? (A.beslutOm === m.id ? `<div class="ay-bekraftruta"><label class="svag" for="ay-bt-${e_(m.id)}">${A.beslutVal === 'diskutera' ? 'Din fråga tillbaka' : 'Din text (valfri; förslaget används annars)'}</label><textarea id="ay-bt-${e_(m.id)}" data-fokus="bt-${e_(m.id)}" rows="3"></textarea>
          <div class="ay-knapprad"><button class="ay-knapp primar liten" type="button" data-besluta="${e_(m.id)}" data-val="${e_(A.beslutVal)}">${A.beslutVal === 'godta' ? 'Godta som min ändringsinstruktion' : A.beslutVal === 'diskutera' ? 'Skicka frågan' : 'Avvisa'}</button><button class="ay-knapp liten" type="button" data-besluta-avbryt>Avbryt</button></div></div>`
        : `<div class="ay-knapprad">${m.kandidat ? `<button class="ay-knapp liten" type="button" data-beslut-om="${e_(m.id)}" data-val="godta">Godta</button>` : ''}<button class="ay-knapp liten" type="button" data-beslut-om="${e_(m.id)}" data-val="diskutera">Diskutera</button><button class="ay-knapp liten" type="button" data-beslut-om="${e_(m.id)}" data-val="avvisa">Avvisa</button></div>`)
      : '';
    return `<article class="ay-msg ${egen ? 'agaren' : 'agent'}${avvisad ? ' avvisad' : ''}" aria-label="${e_(m.syfte_text)} från ${e_(avsandare(m.avsandare))}">
      <div class="ay-kontextrad"><b>${e_(m.syfte_text)}</b> · ${e_(avsandare(m.avsandare))} till ${e_(mottagare(m.mottagare))}${m.kandidat ? ' · ' + e_(etikett(m.kandidat)) : ''}${m.version ? ' v' + e_(String(m.version).slice(0, 12)) : ''}</div>
      ${m.agent ? `<div class="ay-notis${m.dolt ? '' : ' svag'}" style="margin:4px 0">${m.dolt ? 'Texten ' + e_(m.text) + '.' : 'Inte dina ord och inget godkännande: ' + e_(m.avsandare?.typ === 'extern' ? 'en extern granskare' : 'en session i motorn') + ' skrev det.'}</div>` : ''}
      ${m.dolt ? '' : formatera(m.text)}
      ${m.mandat ? `<div class="svag">Inom ditt mandat: ${e_(m.mandat.omfattning)}</div>` : ''}
      ${(m.belagg || []).length ? `<details><summary class="svag">Belägg (${m.belagg.length})</summary><ul class="ay-handelser">${m.belagg.map((b) => `<li><span>${e_(b)}</span></li>`).join('')}</ul></details>` : ''}
      ${leveransrad(m)}
      ${m.svar ? `<details${m.svar.dolt ? '' : ' open'}><summary class="svag">Svar ${e_(klocka(m.svar.tid).slice(0, 5))}</summary>${m.svar.dolt ? `<p class="svag">${e_(m.svar.text)}</p>` : formatera(String(m.svar.text || '').replace(/```kvitto[\s\S]*?```/g, ''))}</details>` : ''}
      ${m.kvitto ? `<div class="svag">Kvitto från mottagaren: ${m.kvitto.genomfort === false ? 'avstod' : 'säger genomfört'}${m.kvitto.beskrivning ? ' — ' + e_(m.kvitto.beskrivning) : ''}</div>` : ''}
      ${g ? `<div class="svag" data-genomforande="${e_(g.lage)}">Genomförande: ${e_(g.text)}${g.version_efter ? ` (${e_(g.version_fore)} → ${e_(g.version_efter)})` : ''}</div>` : ''}
      ${m.beslut ? `<div class="svag">Ditt beslut: ${e_({ godta: 'godtaget', avvisa: 'avvisat', diskutera: 'under diskussion' }[m.beslut.val] || m.beslut.val)} ${e_(kort(m.beslut.tid))}</div>` : ''}
      ${knappar}
      <div class="meta"><span>${e_(m.id)}</span><time datetime="${e_(m.tid)}">${e_(klocka(m.tid).slice(0, 5))}</time></div></article>`;
  }
  function meddelandelista() {
    const d = A.samverkan;
    if (!d) return '<div class="ay-tom">Läser meddelandena…</div>';
    if (d.dold) return '<div class="ay-notis">Kunden är en arm i en blind jämförelse som du inte valt i än: meddelandena visas efter ditt val.</div>';
    const lista = d.meddelanden || [], oppna = lista.filter((m) => (d.oppna || []).includes(m.id));
    return `<p class="svag" style="margin:0 0 8px">Meddelanden mellan dig och sessionerna i körningen, med leveransläget som går att belägga. Ett skickat meddelande är inget bevis för att något är utfört.${d.blind ? ' Före ditt första val visas inte sessionernas text.' : ''}</p>
      ${oppna.length ? `<h3 class="ay-underrubrik">Väntar på ditt beslut (${oppna.length})</h3>${oppna.map(meddelandekort).join('')}<h3 class="ay-underrubrik">Alla</h3>` : ''}
      ${lista.length ? lista.filter((m) => !(d.oppna || []).includes(m.id)).map(meddelandekort).join('') : '<div class="ay-tom">Inga meddelanden i körningen än. Skriv till en session som arbetar, eller till kandidatens utförare, nedan.</div>'}
      ${mandatruta()}`;
  }
  function mandatruta() {
    const d = A.samverkan || {}, akt = (d.mandat || []).filter((x) => x.aktivt);
    const ks = A.lage?.kandidater || [];
    return `<details class="ay-mandat"${A.mandatOppen ? ' open' : ''}><summary>Mandat för granskare (${akt.length})</summary>
      <p class="svag" style="margin:6px 0">En granskare med mandat får lämna de åtgärder du kryssar i till kandidatens utförare, i den här körningen och inom omfattningen du skriver. Utan mandat går granskarens fynd och förslag till dig.</p>
      ${akt.map((x) => `<div class="ay-mandatrad"><span>${e_(x.granskare?.typ === 'extern' ? 'Extern: ' + x.granskare.namn : x.granskare?.typ === 'ansvar' ? 'Motorns granskare' : 'Session ' + String(x.granskare?.session_id).slice(0, 8))} · ${e_(etikett(x.kandidat))}: ${e_(x.omfattning)} (${e_((x.atgarder || ['andringsinstruktion']).map((a) => ATGARDER[a] || a).join(', '))})</span><button class="ay-knapp liten" type="button" data-mandat-aterkalla="${e_(x.id)}">Återkalla</button></div>`).join('')}
      <form id="ay-mandatform" class="ay-mandatform" autocomplete="off"><label class="svag">Granskare <select data-mandat="granskare" class="ay-knapp liten"><option value="ansvar">Motorns granskare</option><option value="extern:codex">Codex (extern granskare)</option></select></label>
        <label class="svag">Kandidat <select data-mandat="kandidat" class="ay-knapp liten">${ks.map((k) => `<option value="${e_(k.id)}"${k.id === A.valdKandidat ? ' selected' : ''}>${e_(k.etikett)}</option>`).join('')}</select></label>
        <label class="svag" style="width:100%">Omfattning <input data-mandat="omfattning" class="ay-knapp liten" style="width:100%" placeholder="t.ex. kontrast och radbrytning i rubriken"></label>
        <fieldset class="ay-mandat-atgarder"><legend class="svag">Får lämna till utföraren</legend>${Object.entries(ATGARDER).map(([k, n]) => `<label class="svag"><input type="checkbox" data-mandat-atgard="${e_(k)}"> ${e_(n)}</label>`).join(' ')}</fieldset>
        <button class="ay-knapp liten" type="submit"${ks.length ? '' : ' disabled'}>Ge mandat</button><span class="svag" id="ay-mandatsvar" role="status" aria-live="polite"></span></form></details>`;
  }
  function mottagarval() {
    const ut = [];
    for (const s of A.lage?.sessioner || []) if (s.styrning?.kan_meddelas) ut.push([`session:${s.session_id}`, `${roll(s)}${s.kandidat ? ' · ' + etikett(s.kandidat) : ''} (arbetar nu)`]);
    for (const k of A.lage?.kandidater || []) ut.push([`adress:utforande:${k.id}`, `Utföraren för ${k.etikett} (nu eller härnäst)`]);
    return ut;
  }
  function ritaMeddelandeform() {
    const f = document.getElementById('ay-skriv'); if (!f || !A.lage) return;
    const val = mottagarval(), nyckel = JSON.stringify([val, A.mottagareVald, A.syfte, A.lage.blind, A.lage.korning?.startad]);
    if (f.dataset.ritad === 'm' + nyckel || f.contains(document.activeElement)) return;
    const utkast = f.querySelector('textarea')?.value || '';
    f.dataset.ritad = 'm' + nyckel;
    const vald = A.mottagareVald && val.some(([k]) => k === A.mottagareVald) ? A.mottagareVald : (val[0] || [''])[0];
    f.innerHTML = `<label class="svag" for="ay-mottagare">Till</label><select id="ay-mottagare" class="ay-knapp liten" style="width:100%" data-fokus="mottagare">${val.map(([k, n]) => `<option value="${e_(k)}"${k === vald ? ' selected' : ''}>${e_(n)}</option>`).join('') || '<option value="">Ingen session eller kandidat att skriva till</option>'}</select>
      <div class="ay-segment" role="group" aria-label="Syfte">${[['fraga', 'Fråga'], ['andringsinstruktion', 'Ändringsinstruktion']].map(([k, n]) => `<button type="button" data-syfte="${k}" data-fokus="sy-${k}" aria-pressed="${(A.syfte || 'fraga') === k}">${n}</button>`).join('')}</div>
      <label class="dolt" for="ay-mtext">Meddelande</label><textarea id="ay-mtext" data-fokus="mtext" placeholder="${A.syfte === 'andringsinstruktion' ? 'Vad ska ändras, var, och hur känner man igen att det är klart?' : 'Skriv en fråga till sessionen'}">${e_(utkast)}</textarea>
      <div class="ay-markering">${(() => { const k = (A.lage.kandidater || []).find((x) => x.id === (vald.split(':')[2] || A.valdKandidat)); return k ? `Gäller: <b>${e_(k.etikett)}</b>${k.version ? ', version ' + e_(k.version) : ''} (den fotograferade, som du ser under Ögonblicksbild)` : 'Gäller ingen kandidat'; })()}</div>
      <div class="ay-skrivrad"><span class="svag" id="ay-msvar" role="status" aria-live="polite"></span><button class="ay-knapp primar" type="submit" data-fokus="m-skicka"${val.length ? '' : ' disabled'}>Skicka</button></div>`;
  }
  async function skickaMeddelande() {
    const t = document.getElementById('ay-mtext'), svar = document.getElementById('ay-msvar'), till = document.getElementById('ay-mottagare')?.value || '';
    const text = (t?.value || '').trim(); if (!text) { svar.textContent = 'Skriv meddelandet först.'; t.focus(); return; }
    const [typ, a, b] = till.split(':');
    const mot = typ === 'session' ? { typ: 'session', session_id: a } : { typ: 'adress', ansvar: a, kandidat: b };
    const kid = mot.kandidat || ((A.lage.sessioner || []).find((s) => s.session_id === mot.session_id) || {}).kandidat || null;
    const k = (A.lage.kandidater || []).find((x) => x.id === kid);
    const syfte = A.syfte || 'fraga';
    if (syfte === 'andringsinstruktion' && !k?.version_hel) { svar.textContent = 'En ändringsinstruktion binds till en fotograferad version: välj en kandidat som har en.'; return; }
    const body = { mottagare: mot, syfte, text, kandidat: kid, version: k?.version_hel || null, korning: A.lage.korning?.startad || null };
    body.id = await innehallsId('o', [A.slug, body.mottagare, body.syfte, body.text, body.kandidat, body.version, body.korning]);
    svar.textContent = 'Sparar…';
    try {
      const r = await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/meddelande', body);
      t.value = '';
      svar.textContent = r.upprepat ? 'Samma meddelande finns redan; inget nytt skickades.' : 'Sparat. Läget visar när sessionen tagit emot och besvarat det.';
      await laddaSamverkan();
    } catch (err) { svar.textContent = (err.status === 409 ? '' : 'Svaret gick inte att bekräfta: ') + err.message + (err.status === 409 ? '' : '. Försök igen: samma text ger samma id, så det sparas inte två gånger.'); }
  }
  async function besluta(id, val) {
    const m = (A.samverkan?.meddelanden || []).find((x) => x.id === id); if (!m) return;
    const text = (document.getElementById('ay-bt-' + id)?.value || '').trim();
    if (val === 'diskutera' && !text) { meddela('Skriv vad du vill diskutera.'); return; }
    const k = (A.lage.kandidater || []).find((x) => x.id === m.kandidat);
    const body = { val, text, version: k?.version_hel || null, korning: A.lage.korning?.startad || null };
    body.nytt_id = await innehallsId('b', [A.slug, id, val, text, body.version]);
    try { await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/meddelande/' + encodeURIComponent(id) + '/beslut', body); A.beslutOm = null; meddela(val === 'godta' ? 'Godtaget: förslaget är nu din ändringsinstruktion till kandidatens utförare.' : val === 'avvisa' ? 'Avvisat.' : 'Din fråga är skickad tillbaka.'); await laddaSamverkan(); }
    catch (err) { meddela('Beslutet sparades inte: ' + err.message); }
  }
  async function geMandat(form) {
    const v = (n) => form.querySelector(`[data-mandat="${n}"]`)?.value || '';
    const g = v('granskare'), omf = v('omfattning').trim(), svar = document.getElementById('ay-mandatsvar');
    const atgarder = [...form.querySelectorAll('[data-mandat-atgard]:checked')].map((x) => x.dataset.mandatAtgard);
    if (!omf) { svar.textContent = 'Skriv omfattningen.'; return; }
    if (!atgarder.length) { svar.textContent = 'Kryssa i vad granskaren får lämna till utföraren.'; return; }
    const body = { kandidat: v('kandidat'), omfattning: omf, atgarder, korning: A.lage.korning?.startad || null,
      granskare: g === 'ansvar' ? { typ: 'ansvar' } : { typ: 'extern', namn: g.split(':')[1] } };
    body.id = await innehallsId('md', [A.slug, body.kandidat, body.granskare, body.omfattning, body.atgarder, body.korning]);
    try { await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/mandat', body); A.mandatOppen = true; await laddaSamverkan(); meddela('Mandatet gäller i den här körningen.'); }
    catch (err) { svar.textContent = 'Mandatet sparades inte: ' + err.message; }
  }

  // --- sessionernas styrning: paus, återupptagning, historik och följdfrågor ---
  function styrrad(s) {
    const st = s.styrning;
    if (!st || s.kalla === 'partnersamtalet') return '';
    if (!st.lopare) return '';
    const paus = st.lage === 'pausad' ? `<span class="ay-styr" data-styr="pausad">Pausad${st.paus?.omfattning === 'projekt' ? ' (projektet)' : ''} sedan ${e_(klocka(st.sedan).slice(0, 5))}</span>`
      : st.lage === 'paus_begard' ? '<span class="ay-styr" data-styr="paus_begard">Paus begärd: turen avbryts</span>' : '';
    const kvar = (st.verktyg_kvar || []).filter((x) => x.pid);
    return `${paus ? `<div class="rad">${paus}</div>` : ''}${st.lage === 'pausad' ? `<div class="rad svag">${kvar.length ? 'Arbetar fortfarande: ' + e_(kvar.map((x) => x.kommando).join(', ')) : 'Inga verktyg arbetar.'}</div>` : ''}`;
  }
  function kompetensrad(s) {
    const k = s.kompetens; if (!k) return '';
    const er = k.erbjuden || {}, la = k.laddad || {}, an = k.anropad || {};
    const mcp = er.mcp ? Object.entries(er.mcp).map(([n, v]) => `${n} ${v}`).join(', ') : null;
    return `<details class="ay-kompetens"><summary class="svag">Kompetens: ${er.skills ?? '?'} erbjudna, ${(la.skills || []).length} laddade, ${an.mcp ?? 0} MCP-anrop</summary>
      <dl><dt>Erbjuden</dt><dd>${er.skills ?? 'okänt'} skills i sessionens lista${mcp ? '; MCP: ' + e_(mcp) : ''}</dd>
      <dt>Laddad</dt><dd>${(la.skills || []).length ? e_(la.skills.join(', ')) : 'inga skills aktiverade'}${la.skillfiler ? `; ${la.skillfiler} skillfiler lästa` : ''}</dd>
      <dt>Anropad</dt><dd>${an.mcp || 0} MCP-anrop${(an.mcp_tjanster || []).length ? ' (' + e_(an.mcp_tjanster.join(', ')) + ')' : ''}, ${an.skillanrop || 0} skillanrop</dd>
      <dt>Påverkan</dt><dd>${e_(k.paverkan)}</dd></dl></details>`;
  }
  function sessionsknappar(s) {
    const st = s.styrning || {}, ut = [];
    if (st.kan_meddelas) ut.push(`<button class="ay-knapp liten" type="button" data-skriv-till="${e_(s.session_id)}">Skriv</button>`);
    if (st.kan_pausas) ut.push(`<button class="ay-knapp liten" type="button" data-paus-session="${e_(s.session_id)}" data-fokus="p-${e_(s.session_id)}">Pausa</button>`);
    if (st.paus?.omfattning === 'session') ut.push(`<button class="ay-knapp liten" type="button" data-aterta-session="${e_(s.session_id)}">Återuppta</button>`);
    if (s.session_id && s.kalla !== 'partnersamtalet' && !A.lage.blind) ut.push(`<button class="ay-knapp liten" type="button" data-historik="${e_(s.session_id)}">Historik</button>`);
    return ut.join('');
  }
  async function pausa(om, sid, aterta) {
    const body = { omfattning: om, session_id: sid || null, korning: A.lage.korning?.startad || null, aterta: Boolean(aterta) };
    try { const r = await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/paus', body); A.samverkan = r; A.pausBekrafta = null; A.projektPausBekrafta = false;
      meddela(aterta ? 'Återupptagning begärd: sessionen fortsätter från där den var, med meddelandena som kom under pausen.' : om === 'projekt' ? 'Paus begärd för hela körningen: ingen ny session startar, och de som arbetar avbryts vid nästa möjlighet.' : 'Paus begärd för sessionen.');
      tillampa(await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug))); }
    catch (err) { meddela('Pausen sparades inte: ' + err.message); }
  }
  function projektpaus() {
    const p = A.lage?.samverkan?.projektpaus, d = A.samverkan?.styrning?.projekt;
    if (p) {
      const kvar = [...(A.samverkan?.pausade || []).flatMap((x) => (x.verktyg_kvar || []).filter((v) => v.pid).map((v) => v.kommando)),
        ...(d?.tjanster || []).map((v) => v.kommando + (v.modell ? ' (en modellsession utan paus, till exempel en tjänstesession)' : ' (arbetarens eget steg)'))];
      const vantar = Number(d?.vantande || 0) || (p.vantande_start ? 1 : 0);
      const tak = (A.samverkan?.pausade || []).map((x) => x.tak).filter(Boolean).sort()[0];
      return `<div class="ay-notis${d?.lage === 'pausad' ? '' : ' varn'}"><b>${d?.lage === 'pausad' ? 'Pausad' : 'Paus begärd'}</b>: ${e_(d?.lage_text || 'ingen ny session startar')}${vantar ? `; ${vantar === 1 ? 'en session väntar' : vantar + ' sessioner väntar'} på återupptagningen` : ''}.${kvar.length ? ' Arbetar fortfarande: ' + e_(kvar.join(', ')) + '.' : ''} En paus återställer inga filändringar.${tak ? ` En pausad session avslutas med tidsgräns om pausen varar förbi ${e_(kort(tak))}.` : ''}</div>
        <div class="ay-knapprad"><button class="ay-knapp primar" type="button" data-aterta-projekt data-fokus="aterta-projekt">Återuppta körningen</button></div>`;
    }
    if (!(A.lage?.korning?.arbetaren === 'lever')) return '';
    if (A.projektPausBekrafta) {
      const n = (A.lage.sessioner || []).filter((s) => s.styrning?.kan_pausas).length;
      return `<div class="ay-bekraftruta"><p style="margin:0">Pausa hela körningen? Ingen ny session startar, och ${n} session${n === 1 ? '' : 'er'} som arbetar avbryts vid nästa möjlighet och väntar med sina processer. Byggen och fotograferingar som redan kör redovisas. Filändringar som redan gjorts står kvar.</p>
        <div class="ay-knapprad"><button class="ay-knapp primar" type="button" data-paus-projekt-ja data-fokus="paus-projekt-ja">Pausa körningen</button><button class="ay-knapp" type="button" data-paus-projekt-nej>Avbryt</button></div></div>`;
    }
    return '<div class="ay-knapprad"><button class="ay-knapp" type="button" data-paus-projekt data-fokus="paus-projekt">Pausa körningen</button></div>';
  }
  async function laddaHistorik(sid) {
    A.historik = { session_id: sid, data: null, fel: null }; rita();
    try { const d = await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/historik/' + encodeURIComponent(sid)); if (A.historik?.session_id === sid) { A.historik.data = d; rita(); } }
    catch (err) { if (A.historik?.session_id === sid) { A.historik.fel = err.message; rita(); } }
  }
  function historikvy() {
    const h = A.historik, d = h.data, s = (A.lage.sessioner || []).find((x) => x.session_id === h.session_id) || {};
    const kropp = h.fel ? `<div class="ay-notis fel">${e_(h.fel)}</div>` : !d ? '<div class="ay-tom">Läser sessionens historik…</div>'
      : `<p class="svag" style="margin:0">${e_(d.kalla)}; ${d.antal} rader, de senaste visas. Inga promptar till andra sessioner och inga verktygssvar.</p>
        <ol class="ay-historik">${d.rader.map((r) => `<li data-typ="${e_(r.typ)}"><time>${e_(klocka(r.tid).slice(0, 5))}</time><div>${r.typ === 'verktyg' ? '<span class="svag">verktyg</span> ' + e_(r.text) : `<span class="svag">${r.typ === 'in' ? 'till sessionen' : 'sessionen'}</span>${formatera(r.text)}`}</div></li>`).join('')}</ol>
        ${(d.grenar || []).map((g) => `<div class="ay-msg agent"><div class="ay-kontextrad"><b>Följdfråga</b> · förgrening ${e_(String(g.session_id || '…').slice(0, 8))} av ${e_(String(g.foralder).slice(0, 8))} · ${e_(g.ansvar)}</div>${formatera(g.text)}${g.svar ? `<div class="svag">Svar:</div>${formatera(g.svar.text)}${g.svar.listpris_usd != null ? `<div class="svag">Listpris enligt Claude Code ${e_(Number(g.svar.listpris_usd).toFixed(2))} USD, inte fakturerat</div>` : ''}` : `<div class="svag">${e_(g.lage === 'arbetar' ? 'Förgreningen svarar…' : g.lage || '')}</div>`}</div>`).join('')}
        ${s.styrning?.lever ? '<p class="svag">Sessionen arbetar: skriv till den under Meddelanden. En följdfråga förgrenar den först när den slutat.</p>'
          : `<form id="ay-foljdform" autocomplete="off"><label class="svag" for="ay-ftext">Följdfråga (en förgrening som bara läser; den ursprungliga sessionen ändras inte)</label><textarea id="ay-ftext" data-fokus="ftext" rows="3"></textarea>
            <div class="ay-skrivrad"><span class="svag" id="ay-fsvar" role="status" aria-live="polite"></span><button class="ay-knapp primar liten" type="submit">Fråga</button></div></form>`}`;
    return `<div class="ay-panelhuvud"><h2 id="ay-roller-rubrik">Historik: ${e_(roll(s))}${s.kandidat ? ' · ' + e_(etikett(s.kandidat)) : ''}</h2><button class="ay-knapp liten" type="button" data-historik-slut data-fokus="historik-slut">Tillbaka</button></div>
      <div class="ay-panelkropp ay-folj">${kropp}</div>`;
  }
  async function stallFoljdfraga() {
    const t = document.getElementById('ay-ftext'), svar = document.getElementById('ay-fsvar'), sid = A.historik?.session_id;
    const text = (t?.value || '').trim(); if (!text || !sid) { if (svar) svar.textContent = 'Skriv frågan först.'; return; }
    const id = await innehallsId('g', [A.slug, sid, text]);
    svar.textContent = 'Startar förgreningen…';
    try { await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/foljdfraga', { id, session_id: sid, text }); t.value = ''; laddaHistorik(sid);
      clearInterval(A.grenTimer); A.grenTimer = setInterval(() => { if (A.historik?.session_id !== sid) { clearInterval(A.grenTimer); return; } laddaHistorik(sid); if ((A.historik?.data?.grenar || []).every((g) => g.lage !== 'arbetar')) clearInterval(A.grenTimer); }, 4000); }
    catch (err) { svar.textContent = err.message; }
  }

  // --- besluten: samma beslutstjänst som Förslagen, bunden till den bild och version du ser ---
  function beslutsruta() {
    const k = (A.lage.kandidater || []).find((x) => x.id === A.valdKandidat);
    if (!k) return '<p style="margin:0">Kandidaterna väntar på ditt val. Välj en kandidat under Kandidater.</p>';
    const bild = k.snapshot['1440'] || k.snapshot['390'], sha = k.snapshot['1440'] ? k.snapshot.sha?.['1440'] : k.snapshot.sha?.['390'];
    if (!k.version_hel) return `<p style="margin:0">${e_(k.etikett)} har ingen fotograferad version att besluta över än.</p>`;
    if (!bild) return `<p style="margin:0">${e_(k.etikett)} har version ${e_(k.version)} men ingen bevarad bild: ett beslut binds till bilden du ser, så fotografera kandidaten först (eller besluta i <a href="#/arbetsyta/${e_(A.slug)}/forslag">Förslagen</a>).</p>`;
    const b = A.beslutBekrafta;
    const ogiltig = k.snapshot.giltig === false;  // en fotograferad felsida: ingen version att välja eller godkänna
    const godk = ['forfinad'].includes(k.status) && !ogiltig;
    return `<p style="margin:0">Beslutet gäller <b>${e_(k.etikett)}</b>, version ${e_(k.version)}, fotograferad ${e_(kort(k.snapshot.tid))}: bilden nedan${A.enhet === 'mobil' ? ' (beslutet binds till skärmbilden i 1440 px)' : ''}.</p>
      ${b ? `<div class="ay-bekraftruta"><p style="margin:0">${e_(b.text)}</p>${b.version_hel && b.version_hel !== k.version_hel && !b.aldre ? `<p class="ay-notis varn" role="alert" style="margin:0">${e_(k.etikett)} har fått en ny version (${e_(k.version)}) sedan du öppnade beslutet. Beslutet gäller version ${e_(b.version)}, som inte längre är kandidatens, och nekas: avbryt och se den nya versionen först.</p>` : ''}${['forkasta', 'ny_riktning'].includes(b.beslut) || b.beslut === 'valj' ? `<label class="svag" for="ay-beslutstext">${b.beslut === 'valj' ? 'Vad du gillar (valfritt)' : 'Vad håller inte, och vad ska nästa försök pröva?'}</label><textarea id="ay-beslutstext" rows="3" data-fokus="beslutstext"></textarea>` : ''}
          <div class="ay-knapprad"><button class="ay-knapp primar" type="button" data-beslut-ja data-fokus="beslut-ja">${e_(b.knapp)}</button><button class="ay-knapp" type="button" data-beslut-nej>Avbryt</button></div></div>`
        : `${ogiltig ? `<p class="ay-notis varn" role="alert" style="margin:0">Ögonblicksbilden av ${e_(k.etikett)} är ingen sida (${e_((k.snapshot.ogiltig || []).join('; '))}). Fotografera kandidaten igen innan du väljer eller godkänner den.</p>` : ''}<div class="ay-knapprad">${ogiltig ? '' : '<button class="ay-knapp primar" type="button" data-beslut="valj" data-fokus="b-valj">Välj vidare</button>'}${godk ? '<button class="ay-knapp primar" type="button" data-beslut="godkand" data-fokus="b-godkand">Godkänn denna version</button>' : ''}<button class="ay-knapp" type="button" data-beslut="forkasta">Underkänn alla</button><button class="ay-knapp" type="button" data-beslut="ny_riktning">Ny riktning</button></div>
          <p class="svag" style="margin:0">Jämför kandidaterna under Resultat → Jämför, eller alla sida vid sida i <a href="#/arbetsyta/${e_(A.slug)}/forslag">Förslagen</a>, där också hela beslutet finns. Välj vidare startar inget; ett uppdrag (Rätta, Omarbeta designen eller Bygg ut) ger du under Ändring, och det startas under Kontroller. Ett godkännande lämnar över till helbygget men startar det inte, och publiceringen är ett eget beslut.</p>`}
      <p class="svag" role="status" aria-live="polite" id="ay-beslutssvar" style="margin:0">${e_(A.beslutSvar || '')}</p>`;
  }
  const BESLUTSTEXT = {
    valj: (k) => [`Välj ${k.etikett} (version ${k.version}) för vidareutveckling? Inget arbete startar: nästa steg är ett uppdrag (Rätta, Omarbeta designen eller Bygg ut) eller ägarens godkännande.`, 'Välj vidare'],
    valj_version: (k, v) => [`Välj den tidigare versionen ${v} av ${k.etikett}? Den tas fram när du startar det under Kontroller; den nuvarande versionen ${k.version} står kvar bevarad och kan väljas igen.`, 'Välj versionen'],
    godkand: (k) => [`Godkänn ${k.etikett}, version ${k.version}, den bild du ser? Godkännandet binds till bilden och versionen; har arbetsversionen ändrats sedan fotograferingen nekas det. Helbygget startar inte.`, 'Godkänn'],
    forkasta: () => ['Underkänn alla kandidater i körningen? Din text blir nästa körnings kritik.', 'Underkänn alla'],
    ny_riktning: () => ['Be om en ny riktning? Din text blir nästa körnings kritik.', 'Be om ny riktning'],
  };
  async function fattaBeslut() {
    const b = A.beslutBekrafta, k = (A.lage.kandidater || []).find((x) => x.id === b.kandidat);
    const text = (document.getElementById('ay-beslutstext')?.value || '').trim();
    if (['forkasta', 'ny_riktning'].includes(b.beslut) && !text) { A.beslutSvar = 'Skriv vad som inte håller och vad nästa försök ska pröva.'; rita(); return; }
    // det du såg när du öppnade beslutet, inte det levande läget nu; servern nekar när det inte längre är kandidatens version
    const sedd = [{ kandidat: b.kandidat, version: b.version_hel, bild: b.bild, bild_sha: b.bild_sha }];
    const body = { beslut: b.beslut, kandidater: ['forkasta', 'ny_riktning'].includes(b.beslut) ? [] : [{ id: b.kandidat, version: b.version_hel }], text, sedd, korning: A.lage.korning?.startad || null };
    A.beslutSvar = 'Sparar beslutet…'; rita();
    try { await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/beslut', body); A.beslutBekrafta = null; A.beslutSvar = 'Beslutet är sparat i domloggen, bundet till ' + (k?.etikett || b.kandidat) + ' version ' + b.version + '.';
      tillampa(await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug))); }
    catch (err) { A.beslutSvar = (err.status === 409 ? 'Inaktuellt: ' : 'Beslutet sparades inte: ') + err.message; rita(); }
  }

  // --- jämförelsen: den valda kandidatens bevarade bild bredvid en annan kandidats eller en tidigare version ---
  function jamforelse() {
    const ks = A.lage.kandidater || [], k = ks.find((x) => x.id === A.valdKandidat);
    if (!k) return '<div class="ay-scen"><div class="ay-tom">Välj en kandidat under Kandidater först.</div></div>';
    const bredd = A.enhet === 'mobil' ? '390' : '1440';
    const bild = (x) => x.snapshot[bredd] || x.snapshot['1440'] || x.snapshot['390'];
    if (!bild(k)) return `<div class="ay-scen"><div class="ay-tom">${e_(k.etikett)} har ingen bevarad bild än; jämförelsen visar bevarade bilder sida vid sida.</div></div>`;
    const val = ks.filter((x) => x.id !== k.id && bild(x)).map((x) => ['k:' + x.id, x.etikett + (x.version ? ' v' + x.version : '')]);
    const vers = (k.versioner || []).filter((v) => v !== k.version).map((v) => ['v:' + v, 'Tidigare version ' + v]);
    const ref = k.referens && (k.referens[bredd] || k.referens['1440'] || k.referens['390']) ? [['r:', 'Huvudreferensen' + (k.referens.namn ? ': ' + k.referens.namn : '')]] : [];
    const alla = [...ref, ...val, ...vers];
    const med = A.jamforMed && alla.some(([x]) => x === A.jamforMed) ? A.jamforMed : (alla[0] || [''])[0];
    const refbild = k.referens && (k.referens[bredd] || k.referens['1440'] || k.referens['390']);
    const hoger = med === 'r:' ? `<figure><figcaption>Huvudreferensen${k.referens.namn ? ': ' + e_(k.referens.namn) : ''} (fångad startsida)</figcaption><img src="/fil/${e_(refbild)}" alt="Huvudreferensen ${e_(k.referens.namn || '')}"></figure>`
      : med.startsWith('k:') ? (() => { const x = ks.find((y) => y.id === med.slice(2)); return x ? `<figure><figcaption>${e_(x.etikett)}${x.version ? ', version ' + e_(x.version) : ''}</figcaption><img src="/fil/${e_(bild(x))}" alt="${e_(x.etikett)}"></figure>` : ''; })()
      : med.startsWith('v:') ? `<figure><figcaption>${e_(k.etikett)}, version ${e_(med.slice(2))}</figcaption><img src="/fil/${e_(String(bild(k)).replace(/\/bilder\//, '/versioner/' + med.slice(2) + '/bilder/'))}" alt="${e_(k.etikett)}, version ${e_(med.slice(2))}" onerror="this.replaceWith(Object.assign(document.createElement('p'),{className:'svag',textContent:'Den versionen bevarades utan bilder; jämför koden under Kod och preview.'}))"></figure>` : '<p class="svag">Inget att jämföra med än.</p>';
    const utanRef = k.referens && !refbild ? ` Referensen: ${e_(k.referens.saknas || 'ingen fångad sida')}.` : '';
    return `<div class="ay-adress"><span class="etikett">Bevarade bilder, ${bredd} px.${A.lage.blind ? ' Tidigare versioner visas efter ditt första val.' : ''}${utanRef}</span>
        ${alla.length ? `<label class="svag">Jämför med <select id="ay-jamformed" class="ay-knapp liten">${alla.map(([x, n]) => `<option value="${e_(x)}"${x === med ? ' selected' : ''}>${e_(n)}</option>`).join('')}</select></label>` : ''}</div>
      <div class="ay-scen"><div class="ay-jamfor"><figure><figcaption>${e_(k.etikett)}${k.version ? ', version ' + e_(k.version) : ''} (vald)</figcaption><img src="/fil/${e_(bild(k))}" alt="${e_(k.etikett)}"></figure>${hoger}</div></div>
      ${(() => { const v12 = med.startsWith('v:') ? med.slice(2) : null, hel = v12 && (k.valbara || []).find((x) => x.startsWith(v12));
        return hel && !A.lage.blind ? `<div class="ay-knapprad"><button class="ay-knapp" type="button" data-valj-version="${e_(hel)}" data-fokus="valj-version">Välj version ${e_(v12)}</button><span class="svag"> En tidigare bättre version kan väljas; den nuvarande står kvar bevarad.</span></div>` : ''; })()}
      ${k.uppdrag ? `<p class="svag" style="margin:0">Senaste uppdraget: ${e_(k.uppdrag.namn || k.uppdrag.typ)} från version ${e_(k.uppdrag.fran)}. Före och efter (${e_(k.uppdrag.avsandare || 'separat granskare')}, bilderna utan förklaring): ${e_({ battre: 'efter är bättre', samre: 'efter är sämre', likvardig: 'likvärdiga', oklart: 'oklart' }[k.uppdrag.utfall] || 'inte bedömd')}${k.uppdrag.fortsattning ? '; ' + e_({ fora_vidare: 'förs vidare', kraver_losning: 'tekniskt nödvändig men sämre: kräver fortsatt lösning', aterstall: 'versionen före gäller, efter-versionen kan väljas', oklart: 'står som oklart' }[k.uppdrag.fortsattning] || k.uppdrag.fortsattning) : ''}.</p>` : ''}`;
  }

  // --- händelserna ---
  document.addEventListener('click', (ev) => {
    const ay = ev.target.closest('.ay'); if (!ay) return;
    const t = ev.target.closest('button, a'); if (!t) return;
    const d = t.dataset;
    if ('lasOmForslag' in d) { laddaForslagen(); return; }
    if (d.material) { A.material = d.material; ritaMaterial(); document.querySelector(`[data-fokus="m-${d.material}"]`)?.focus(); return; }
    if (d.enhet) { A.enhet = d.enhet; sparaLayout({ enhet: d.enhet }); ritaMaterial(); document.querySelector(`[data-fokus="e-${d.enhet}"]`)?.focus(); return; }
    if (d.kandidat) { A.valdKandidat = d.kandidat; A.material = null; if ((A.avsikt === 'andring' || A.mark) && A.mark?.kandidat !== d.kandidat) markera({ kandidat: d.kandidat }); /* samma kandidat: markeringen (fil, sida, del) står kvar */ rita(); ritaSkriv(); return; }
    // knapparna står i formuläret och har fokus när de klickas: ritaSkriv ritar då inte om av sig själv, så formuläret tvingas (som Avsikt)
    if (d.rensaMarkering !== undefined) { sparaMark(null); document.getElementById('ay-skriv').dataset.ritad = ''; ritaSkriv(); document.getElementById('ay-text')?.focus(); return; }
    if (d.stamAv !== undefined) { const m = markering(); markera({ kandidat: m.kandidat, vy: m.vy, fil: m.fil, sida: m.sida, del: m.del }); document.getElementById('ay-skriv').dataset.ritad = ''; ritaSkriv(); document.getElementById('ay-text')?.focus(); return; }
    if (d.markeraFil) { markera({ kandidat: A.kod.kandidat, vy: 'Kod och preview', fil: d.markeraFil }); A.avsikt = 'andring'; meddela('Filen är markerad för en ändring. Skriv ändringen i samtalet under Arbetsyta.'); return; }
    if (d.laddaOm !== undefined) { const f = ay.querySelector('#ay-material iframe'); if (f) f.src = f.src; return; }
    if (d.folj !== undefined) { A.folj = d.folj || null; if (A.vy === 'kod') ritaKodaktivitet(); else rita(); document.querySelector('[data-fokus="folj-slut"]')?.focus(); return; }
    if (d.foljSlut !== undefined) { const id = A.folj; A.folj = null; rita(); document.querySelector(`[data-fokus="f-${CSS.escape(id || '')}"]`)?.focus(); return; }
    if (d.falla) { const ytan = document.getElementById('ay-ytan'); ytan.toggleAttribute(d.falla === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold', true); sparaLayout({ [d.falla === 'vanster' ? 'vansterDold' : 'hogerDold']: true }); document.querySelector(`[data-visa="${d.falla}"]`)?.focus(); return; }
    if (d.visa) { const ytan = document.getElementById('ay-ytan'); ytan.removeAttribute(d.visa === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold'); sparaLayout({ [d.visa === 'vanster' ? 'vansterDold' : 'hogerDold']: false }); return; }
    if (d.omrade) { const ytan = document.getElementById('ay-ytan'); ytan.dataset.omrade = d.omrade; sparaLayout({ omrade: d.omrade }); ay.querySelectorAll('[data-omrade]').forEach((b) => b.tagName === 'BUTTON' && b.setAttribute('aria-pressed', String(b.dataset.omrade === d.omrade))); return; }
    if (d.avsikt) { A.avsikt = d.avsikt; if (d.avsikt === 'andring' && !A.mark && markering().kandidat) markera(); const f = document.getElementById('ay-skriv'); try { sessionStorage.setItem('nwp-arbetsyta-utkast:' + A.slug, f.querySelector('textarea').value); } catch { /* */ } f.dataset.ritad = ''; ritaSkriv(); document.querySelector(`[data-fokus="a-${d.avsikt}"]`)?.focus(); return; }
    if (d.skicka === 'andring') { ev.preventDefault(); skickaAndring(); return; }
    if (d.anvandForslag) { const m = (A.partner?.meddelanden || []).find((x) => x.id === d.anvandForslag), o = m?.overlamning || {};
      if (o.kandidat && (A.lage.kandidater || []).some((k) => k.id === o.kandidat)) A.valdKandidat = o.kandidat;
      markera({ kandidat: A.valdKandidat, sida: o.sida || undefined, del: o.del || undefined });  // bunden till versionen du ser nu, inte förslagets
      A.avsikt = 'andring'; const f = document.getElementById('ay-skriv'); f.dataset.ritad = ''; ritaSkriv();
      document.getElementById('ay-text').value = [o.mal, o.avgransning ? 'Rör inte: ' + o.avgransning : null, o.forvantat ? 'Klart när: ' + o.forvantat : null].filter(Boolean).join('\n');
      if (o.sida) document.querySelector('[data-falt="sida"]').value = o.sida; if (o.del) document.querySelector('[data-falt="del"]').value = o.del;
      document.getElementById('ay-text').focus(); return; }
    if (d.handling) { if (t.getAttribute('aria-disabled') === 'true') return; handling(d.handling, d.bekraftad !== undefined); return; }
    if (d.avbrytBekraftelse !== undefined) { const id = A.bekrafta?.id; A.bekrafta = null; rita(); document.querySelector(`[data-fokus="h-${CSS.escape(id || '')}"]`)?.focus(); return; }  // fokus tillbaka till Stoppa, inte till sidan
    if (d.kodfil) { laddaKod(d.kodfil); return; }
    if (d.kodvisning) { A.kod.visning = d.kodvisning; ritaFil(); return; }
    if (d.oppnaFil) { postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/oppna', { kandidat: A.kod.kandidat, fil: d.oppnaFil }).then((r) => meddela('Öppnad i ' + r.program)).catch((err) => meddela('Kunde inte öppna: ' + err.message)); return; }
    if (d.loggLas !== undefined) { laddaLogg(true); return; }
    if (d.vflik) { A.vflik = d.vflik; const f = document.getElementById('ay-skriv'); if (f) f.dataset.ritad = ''; ritaVanster(); document.querySelector(`[data-fokus="vf-${d.vflik}"]`)?.focus(); if (d.vflik === 'meddelanden') laddaSamverkan(); return; }
    if (d.syfte) { A.syfte = d.syfte; const f = document.getElementById('ay-skriv'); const t = f?.querySelector('textarea')?.value; f.dataset.ritad = ''; ritaMeddelandeform(); const nt = document.getElementById('ay-mtext'); if (nt && t) nt.value = t; document.querySelector(`[data-fokus="sy-${d.syfte}"]`)?.focus(); return; }
    if (d.skrivTill) { A.vflik = 'meddelanden'; A.mottagareVald = 'session:' + d.skrivTill; const f = document.getElementById('ay-skriv'); if (f) f.dataset.ritad = ''; const ytan = document.getElementById('ay-ytan'); if (ytan) { ytan.dataset.omrade = 'samtal'; ytan.removeAttribute('data-vanster-dold'); } ritaVanster(); laddaSamverkan(); document.getElementById('ay-mtext')?.focus(); return; }
    if (d.beslutOm) { A.beslutOm = d.beslutOm; A.beslutVal = d.val; ritaVanster(); document.getElementById('ay-bt-' + d.beslutOm)?.focus(); return; }
    if (d.beslutaAvbryt !== undefined) { A.beslutOm = null; ritaVanster(); return; }
    if (d.besluta) { besluta(d.besluta, d.val); return; }
    if (d.mandatAterkalla) { postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/mandat/' + encodeURIComponent(d.mandatAterkalla) + '/aterkalla', {}).then(() => { meddela('Mandatet är återkallat.'); laddaSamverkan(); }).catch((err) => meddela('Kunde inte återkalla: ' + err.message)); return; }
    if (d.pausSession) { A.pausBekrafta = { session_id: d.pausSession }; rita(); document.querySelector(`[data-fokus="pj-${CSS.escape(d.pausSession)}"]`)?.focus(); return; }
    if (d.pausJa) { pausa('session', d.pausJa, false); return; }
    if (d.pausNej !== undefined) { const id = A.pausBekrafta?.session_id; A.pausBekrafta = null; rita(); document.querySelector(`[data-fokus="p-${CSS.escape(id || '')}"]`)?.focus(); return; }
    if (d.atertaSession) { pausa('session', d.atertaSession, true); return; }
    if (d.pausProjekt !== undefined) { A.projektPausBekrafta = true; rita(); document.querySelector('[data-fokus="paus-projekt-ja"]')?.focus(); return; }
    if (d.pausProjektJa !== undefined) { pausa('projekt', null, false); return; }
    if (d.pausProjektNej !== undefined) { A.projektPausBekrafta = false; rita(); document.querySelector('[data-fokus="paus-projekt"]')?.focus(); return; }
    if (d.atertaProjekt !== undefined) { pausa('projekt', null, true); return; }
    if (d.historik) { A.folj = null; laddaHistorik(d.historik); return; }
    if (d.historikSlut !== undefined) { const id = A.historik?.session_id; A.historik = null; clearInterval(A.grenTimer); rita(); document.querySelector(`[data-historik="${CSS.escape(id || '')}"]`)?.focus(); return; }
    if (d.beslut) { const k = (A.lage.kandidater || []).find((x) => x.id === A.valdKandidat); if (!k) return;
      const [text, knapp] = BESLUTSTEXT[d.beslut](k); const fyra = Boolean(k.snapshot['1440']);
      // versionen och bilden tas när du öppnar beslutet: ett senare läge byter aldrig tyst det du godkänner (A6)
      A.beslutBekrafta = { beslut: d.beslut, kandidat: k.id, text, knapp, version_hel: k.version_hel, version: k.version,
        bild: fyra ? k.snapshot['1440'] : k.snapshot['390'], bild_sha: fyra ? k.snapshot.sha?.['1440'] : k.snapshot.sha?.['390'] };
      A.beslutSvar = ''; rita(); document.querySelector('[data-fokus="beslutstext"]')?.focus() || document.querySelector('[data-fokus="beslut-ja"]')?.focus(); return; }
    if (d.valjVersion) { const k = (A.lage.kandidater || []).find((x) => x.id === A.valdKandidat); if (!k) return;
      const v12 = d.valjVersion.slice(0, 12), [text, knapp] = BESLUTSTEXT.valj_version(k, v12), b14 = k.snapshot['1440'] || k.snapshot['390'];
      A.beslutBekrafta = { beslut: 'valj', aldre: true, kandidat: k.id, text, knapp, version_hel: d.valjVersion, version: v12,
        bild: b14 ? String(b14).replace(/\/bilder\//, '/versioner/' + v12 + '/bilder/') : null, bild_sha: null };
      A.material = 'snapshot'; A.beslutSvar = ''; rita(); document.querySelector('[data-fokus="beslut-ja"]')?.focus(); return; }
    if (d.beslutJa !== undefined) { fattaBeslut(); return; }
    if (d.beslutNej !== undefined) { A.beslutBekrafta = null; A.beslutSvar = ''; rita(); return; }
    if (d.visaBeslut !== undefined) { A.material = 'snapshot'; const ytan = document.getElementById('ay-ytan'); if (ytan) ytan.dataset.omrade = 'resultat'; ritaMaterial(); document.querySelector('[data-fokus="b-valj"]')?.focus(); return; }
  });
  document.addEventListener('submit', (ev) => {
    if (ev.target.id === 'ay-skriv') { ev.preventDefault(); A.vflik === 'meddelanden' ? skickaMeddelande() : skickaPartner(); }
    if (ev.target.id === 'ay-mandatform') { ev.preventDefault(); geMandat(ev.target); }
    if (ev.target.id === 'ay-foljdform') { ev.preventDefault(); stallFoljdfraga(); }
  });
  document.addEventListener('change', (ev) => {
    if (ev.target.id === 'ay-kund' && ev.target.value) {
      if (A.vy !== 'sektion') location.hash = '#/arbetsyta/' + encodeURIComponent(ev.target.value) + (A.vy ? '/' + A.vy : '');
      else { bytKund(ev.target.value); const gen = ++A.generation; ritaFlikrad(); rita(); lasHuvud(gen); }
    }
    if (ev.target.id === 'ay-kodkand') { A.valdKandidat = ev.target.value; A.kod.fil = null; A.kod.mot = null; laddaKod(); ritaMaterial(); }
    if (ev.target.id === 'ay-kodmot') laddaKod(undefined, ev.target.value || null);
    if (ev.target.id === 'ay-mottagare') { A.mottagareVald = ev.target.value; const f = document.getElementById('ay-skriv'); const t = f?.querySelector('textarea')?.value; f.dataset.ritad = ''; ritaMeddelandeform(); const nt = document.getElementById('ay-mtext'); if (nt && t) nt.value = t; document.getElementById('ay-mottagare')?.focus(); }
    if (ev.target.dataset?.uppdrag === 'typ' || ev.target.dataset?.uppdrag === 'avsandare') { visaUppdragstext(); return; }
    if (ev.target.id === 'ay-jamformed') { A.jamforMed = ev.target.value; ritaMaterial(); document.getElementById('ay-jamformed')?.focus(); }
  });
  document.addEventListener('input', (ev) => { if (ev.target.id === 'ay-text' && A.avsikt === 'andring' && !A.mark && levande().kandidat) { markera(); ritaGaller(); uppdateraSkrivstatus(); }
    if (ev.target.dataset?.falt && A.mark) { A.mark[ev.target.dataset.falt] = ev.target.value; sparaMark(A.mark); } if (ev.target.id === 'ay-text') { try { sessionStorage.setItem('nwp-arbetsyta-utkast:' + A.slug, ev.target.value); } catch { /* */ } } });
  document.addEventListener('keydown', (ev) => { if (ev.target.id === 'ay-text' && ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); A.avsikt === 'andring' ? skickaAndring() : skickaPartner(); } });
  // delarnas menyer: en öppen åt gången; ett klick utanför eller Escape stänger, och fokus går tillbaka till knappen
  document.addEventListener('toggle', (ev) => { if (ev.target.classList?.contains('ay-meny') && ev.target.open) document.querySelectorAll('.ay-meny[open]').forEach((m) => { if (m !== ev.target) m.open = false; }); }, true);
  document.addEventListener('click', (ev) => {
    if (ev.target.closest?.('.ay-flikrad a')) A.fokusDel = true;  // delen som öppnas får fokus på sin rubrik
    document.querySelectorAll('.ay-meny[open]').forEach((m) => { if (!m.contains(ev.target) || ev.target.closest('.ay-menylista a')) m.open = false; });
  });
  document.addEventListener('focusout', (ev) => { const m = ev.target.closest?.('.ay-meny[open]'); if (m && ev.relatedTarget && !m.contains(ev.relatedTarget)) m.open = false; });
  document.addEventListener('keydown', (ev) => { if (ev.key !== 'Escape') return; const m = document.querySelector('.ay-meny[open]'); if (m) { const inne = m.contains(document.activeElement); m.open = false; if (inne) m.querySelector('summary')?.focus(); } });
  window.__arbetsyta = A;  // för proven: läget i vyn, aldrig något att skriva i
})();
