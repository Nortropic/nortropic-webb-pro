// Arbetsytan (ägarens uppdrag 2026-10-09; kunskap/arbetsyta.md): samtal, riktig förhandsvisning, rollsessioner, byggflöde och
// kod på ett ställe, över samma läge (dashboard/arbetsyta.py) och samma identiteter. Läget kommer som en ström; vyn räknar
// inga egna statusar, startar inget av sig själv och visar det som saknas som okänt. Skrivningar går med dashboardnyckeln
// (post i index.html): partnerns meddelanden, ägarens ändringar och flödets befintliga start (samma start-id som Flöde).
(() => {
  const A = { slug: null, vy: '', lage: null, projekt: [], strom: null, anslutning: 'ansluter', senastLast: null, avbrott: null,
    valdKandidat: null, material: null, enhet: 'dator', folj: null, partner: null, partnerNyckel: null, avsikt: 'fraga',
    kod: { kandidat: null, fil: null, mot: null, visning: 'diff', data: null, fildata: null }, logg: null, loggNyckel: null,
    bekrafta: null, svar: '', metod: null, generation: 0, inaktuellTimer: null, pollTimer: null };
  const LAGESNAMN = { ny: 'ny utforskning', om: 'ny körning', valda: 'förfining av valda', putsa: 'putsning', forbered: 'förberedelse', fortsatt: 'återupptagen' };
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
  const roll = (s) => s.roll === 'partner' ? 'Nortropic-partnern' : s.roll === 'helbygge' ? 'Helbygget' : (typeof rollnamn === 'function' ? rollnamn(s.roll) : s.roll) || 'roll inte observerad';
  const etikett = (kid) => ((A.lage?.kandidater || []).find((k) => k.id === kid) || {}).etikett || kid;
  const lagechip = (l, text) => `<span class="ay-lage" data-lage="${e_(l)}" title="${e_(text || '')}">${IKON[l] || IKON.okant}${e_(LAGEN[l] || l || 'okänt')}</span>`;
  const lager = (slug) => `nwp-arbetsyta:${slug}`;
  function layout(slug) { try { return JSON.parse(localStorage.getItem(lager(slug)) || '{}') || {}; } catch { return {}; } }
  function sparaLayout(andring) { if (!A.slug) return; const l = Object.assign(layout(A.slug), andring); try { localStorage.setItem(lager(A.slug), JSON.stringify(l)); } catch { /* bara en bekvämlighet */ } }
  function meddela(text) { const r = document.getElementById('ay-meddelande'); if (!r || !text) return; r.textContent = ''; setTimeout(() => { r.textContent = text; }, 60); }
  function nyttId(nyckel) { let id; try { id = sessionStorage.getItem(nyckel); } catch { id = null; } if (!id) { id = crypto.randomUUID(); try { sessionStorage.setItem(nyckel, id); } catch { /* utan lagring: ett nytt id per klick */ } } return id; }
  function slappId(nyckel, id) { try { if (sessionStorage.getItem(nyckel) === id) sessionStorage.removeItem(nyckel); } catch { /* inget att släppa */ } }
  async function postJson(url, body) {
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Nyckel': (typeof nyckel === 'function' ? nyckel() : '') }, body: JSON.stringify(body) });
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
    let lista;
    try { lista = await hamta('/api/arbetsyta'); } catch (err) { visaFel('Arbetsytan kunde inte läsa kunderna: ' + err.message); return; }
    if (gen !== A.generation) return;
    A.projekt = lista.projekt || [];
    if (!slug) {
      if (!A.projekt.length) { tomtLage(); return; }
      location.replace('#/arbetsyta/' + encodeURIComponent((A.projekt.find((p) => p.slug === localStorageSenaste()) || A.projekt[0]).slug));
      return;
    }
    if (!A.projekt.some((p) => p.slug === slug)) { visaFel(`Arbetsytan känner inte till kunden ${slug}. Välj en kund i listan.`); return; }
    const byte = A.slug !== slug;
    A.vy = ['flode', 'kod'].includes(vy) ? vy : '';
    if (byte) { stangStrom(); Object.assign(A, { slug, lage: null, valdKandidat: null, folj: null, partner: null, partnerNyckel: null, material: null, logg: null, loggNyckel: null, svar: '', kod: { kandidat: null, fil: null, mot: null, visning: 'diff', data: null, fildata: null } }); }
    try { localStorage.setItem('nwp-arbetsyta:senaste', slug); } catch { /* bekvämlighet */ }
    const l = layout(slug);
    A.enhet = l.enhet === 'mobil' ? 'mobil' : 'dator';
    ram();
    if (A.lage) rita(); else {
      try { tillampa(await hamta('/api/arbetsyta/' + encodeURIComponent(slug)), true); } catch (err) { visaFel('Läget kunde inte läsas: ' + err.message); }
    }
    if (!A.strom && !A.pollTimer) oppnaStrom(slug);
  };
  function localStorageSenaste() { try { return localStorage.getItem('nwp-arbetsyta:senaste'); } catch { return null; } }
  window.addEventListener('hashchange', () => { if (!location.hash.startsWith('#/arbetsyta')) { stangStrom(); document.body.classList.remove('ay-aktiv'); A.slug = null; A.lage = null; } });

  function tomtLage() {
    document.getElementById('vy').innerHTML = `<div class="ay">${huvudTom()}<div class="ay-tom" style="padding:40px 18px">Inga kunder med underlag än. Starta ett ärende i <a href="#/kundstart">Kundstart</a> eller förbered en kund i <a href="#/flode">Flöde</a>.</div></div>`;
  }
  function visaFel(text) {
    const v = document.getElementById('vy');
    if (!v.querySelector('.ay')) v.innerHTML = `<div class="ay">${huvudTom()}</div>`;
    const ruta = v.querySelector('.ay-felruta') || Object.assign(document.createElement('div'), { className: 'ay-felruta' });
    ruta.innerHTML = `<div class="ay-notis fel" role="alert" style="margin:12px 18px">${e_(text)}</div>`;
    v.querySelector('.ay').prepend(ruta);
  }
  const huvudTom = () => `<header class="ay-huvud"><div class="ay-marke">${SVG.marke}Nortropic arbetsyta</div><div class="ay-hoger-huvud"><a class="ay-knapp liten" href="#/">Klassisk vy</a></div></header>`;

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
    };
  }
  function stangStrom() { if (A.strom) { A.strom.close(); A.strom = null; } clearInterval(A.pollTimer); A.pollTimer = null; clearTimeout(A.inaktuellTimer); }
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
    const v = document.getElementById('vy');
    const l = layout(A.slug);
    v.innerHTML = `<div class="ay" data-vy="${e_(A.vy)}">
      <header class="ay-huvud" id="ay-huvud"></header>
      <div class="ay-flikrad">
        <nav aria-label="Arbetsytans vyer" style="display:flex;gap:4px">${[['', 'Arbetsyta'], ['flode', 'Byggflöde'], ['kod', 'Kod och preview']].map(([k, n]) =>
          `<a href="#/arbetsyta/${e_(A.slug)}${k ? '/' + k : ''}"${A.vy === k ? ' aria-current="page"' : ''}>${n}</a>`).join('')}</nav>
        <details class="ay-meny"><summary>Fler vyer</summary><nav aria-label="Dashboardens övriga vyer">
          <h4>Kundproduktion</h4><a href="#/flode/${e_(A.slug)}">Flöde (klassisk)</a><a href="#/prototyp/${e_(A.slug)}">Prototyp och ditt val</a><a href="#/kundstart">Kundstart</a><a href="#/ab">Jämförelser</a><a href="#/">Översikt och byggen</a><a href="#/starta">Starta</a>
          <h4>Systemförbättring</h4><a href="#/kirurgen">Kirurgen</a><a href="#/backlog">Backlog</a><a href="#/kalibrering">Kalibrering</a><a href="#/lardomar">Lärdomar</a><a href="#/designprov">Designprov</a><a href="#/prospekt">Prospekt</a>
          <h4>Rapporter</h4><a href="#/dokumentation">Dokumentation och rapporter</a></nav></details>
      </div>
      <p id="ay-meddelande" class="dolt" role="status" aria-live="polite" aria-atomic="true"></p>
      <div id="ay-innehall">${A.vy === 'flode' ? '<div class="ay-flode" id="ay-flode"></div>' : A.vy === 'kod' ? kodRam() : ytRam(l)}</div>
    </div>`;
    if (A.vy === '') kopplaDelare();
    if (A.vy === 'kod') laddaKod();
  }
  function ytRam(l) {
    return `<div class="ay-omraden"><div class="ay-segment" role="group" aria-label="Visa område">${[['samtal', 'Samtal'], ['resultat', 'Resultat'], ['sessioner', 'Sessioner']].map(([k, n]) =>
        `<button type="button" data-omrade="${k}" aria-pressed="${(l.omrade || 'resultat') === k}">${n}</button>`).join('')}</div></div>
      <div class="ay-ytan" id="ay-ytan" data-omrade="${e_(l.omrade || 'resultat')}"${l.vansterDold ? ' data-vanster-dold' : ''}${l.hogerDold ? ' data-hoger-dold' : ''}
        style="${l.vanster ? `--ay-vanster:${Number(l.vanster)}px;` : ''}${l.hoger ? `--ay-hoger:${Number(l.hoger)}px;` : ''}">
        <section class="ay-panel ay-dialog" aria-labelledby="ay-dialog-rubrik">
          <div class="ay-panelhuvud"><h2 id="ay-dialog-rubrik">Nortropic-partnern</h2><span id="ay-partnerchip"></span>
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
      <section class="ay-panel" aria-labelledby="ay-fil-rubrik"><div class="ay-panelhuvud" id="ay-filhuvud"><h2 id="ay-fil-rubrik">Fil</h2></div><div class="ay-panelkropp" id="ay-filvy" style="padding:0"></div></section>
      <section class="ay-panel ay-preview" aria-labelledby="ay-material-rubrik" id="ay-material"></section>
      <section class="ay-panel" aria-labelledby="ay-logg-rubrik"><div class="ay-panelhuvud"><h2 id="ay-logg-rubrik">Körningslogg</h2><button class="ay-knapp liten" type="button" data-logg-las>Läs om</button></div><div class="ay-panelkropp" id="ay-logg"></div></section>
      <section class="ay-panel" aria-labelledby="ay-akt-rubrik"><div class="ay-panelhuvud"><h2 id="ay-akt-rubrik">Sessionens aktivitet</h2></div><div class="ay-panelkropp" id="ay-kodaktivitet"></div></section>
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
    if (!A.lage || !document.querySelector('.ay')) return;
    const h = document.getElementById('ay-huvud');
    if (h && !h.contains(document.activeElement)) h.innerHTML = huvud();
    else ritaAnslutning();
    if (A.vy === '') { ritaMaterial(); behallFokus(document.getElementById('ay-remsa'), () => { document.getElementById('ay-remsa').innerHTML = remsa(); });
      behallFokus(document.getElementById('ay-roller'), () => { document.getElementById('ay-roller').innerHTML = roller(); }); ritaPartner(); ritaSkriv(); }
    if (A.vy === 'flode') behallFokus(document.getElementById('ay-flode'), () => { document.getElementById('ay-flode').innerHTML = flode(); });
    if (A.vy === 'kod') { ritaMaterial(); ritaKodaktivitet(); laddaLogg(); if (A.kod.kandidat !== kodKandidat()) laddaKod(); }
  }
  function huvud() {
    const l = A.lage, p = l.projekt || {}, k = l.korning || {}, kand = (l.kandidater || []).find((x) => x.id === A.valdKandidat);
    return `<div class="ay-marke">${SVG.marke}<span>Nortropic</span></div>
      <div class="ay-falt"><span><label for="ay-kund">Kund</label></span><select id="ay-kund" data-fokus="kund">${A.projekt.map((x) => `<option value="${e_(x.slug)}"${x.slug === A.slug ? ' selected' : ''}>${e_(x.namn || x.slug)}${x.testdata && !/testdata/i.test(x.namn || '') ? ' (testdata)' : ''}</option>`).join('')}</select></div>
      ${p.testdata ? '<span class="ay-testdata" title="Fiktiv verksamhet: testdata, aldrig en riktig kund">Testdata</span>' : ''}
      <div class="ay-falt mindre"><span>Uppdrag</span><span>${k.startad ? `Körning ${e_(kort(k.startad))}, ${e_(LAGESNAMN[k.lage] || k.lage || 'läge okänt')}` : 'Ingen körning'}</span></div>
      <div class="ay-falt mindre"><span>Kandidat och version</span><span>${kand ? `${e_(kand.etikett)} · ${kand.version ? 'version ' + e_(kand.version) : 'ingen version'}` : 'ingen vald'}</span></div>
      <div class="ay-falt"><span>Moment</span><span>${l.moment ? `${e_(l.moment.nr)}. ${e_(l.moment.namn)} · ${e_(l.moment.status)}` : 'okänt'}</span></div>
      <div class="ay-hoger-huvud">${anslutning()}<a class="ay-knapp liten" href="#/flode/${e_(A.slug)}">Klassisk vy</a></div>`;
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
    const pv = previewFor(), nyckel = JSON.stringify([val, pv?.url, A.enhet, A.valdKandidat, pv?.byggd, A.lage.blind]);
    const huvud_ = `<div class="ay-panelhuvud"><h2 id="ay-material-rubrik">${A.vy === 'kod' ? 'Förhandsvisning' : 'Resultat'}</h2>
      ${A.vy === 'kod' ? '' : `<div class="ay-segment" role="group" aria-label="Vad som visas">${[['forhandsvisning', 'Förhandsvisning'], ['snapshot', 'Ögonblicksbild'], ['kandidater', 'Kandidater'], ['underlag', 'Underlag']].map(([k, n]) =>
        `<button type="button" data-material="${k}" data-fokus="m-${k}" aria-pressed="${val === k}">${n}</button>`).join('')}</div>`}
      <div class="ay-segment" role="group" aria-label="Skärmbredd"><button type="button" data-enhet="dator" data-fokus="e-dator" aria-pressed="${A.enhet === 'dator'}">Dator</button><button type="button" data-enhet="mobil" data-fokus="e-mobil" aria-pressed="${A.enhet === 'mobil'}">Mobil</button></div>
      ${pv ? `<a class="ay-ikon" href="${e_(pv.url)}" target="_blank" rel="noopener" aria-label="Öppna förhandsvisningen i en ny flik">${SVG.lank}</a><button class="ay-ikon" type="button" data-ladda-om aria-label="Ladda om förhandsvisningen">${SVG.ladda}</button>` : ''}</div>`;
    if (el.dataset.nyckel === nyckel) { el.querySelector('.ay-panelhuvud').outerHTML = huvud_; return; }
    el.dataset.nyckel = nyckel;
    el.innerHTML = huvud_ + materialKropp(val, pv);
  }
  function previewFor() {
    const p = A.lage.preview || [];
    return p.find((x) => x.typ === 'arbetsversion' && x.kandidat === A.valdKandidat) || (A.valdKandidat ? null : p.find((x) => x.typ === 'arbetsversion' && x.kalla === 'helbygget'))
      || (A.vy === 'kod' ? p.find((x) => x.typ === 'arbetsversion') : null) || null;
  }
  function materialKropp(val, pv) {
    const l = A.lage;
    if (val === 'underlag') {
      const st = (l.steg || [])[0] || {}, filer = [...(st.utfall || [])];
      return `<div class="ay-adress"><span class="etikett">Kundunderlaget, läst ur körningens filer</span></div><div class="ay-scen"><div class="ay-underlagslista">${filer.length
        ? filer.map((f) => f.lank ? `<a href="${e_(f.lank)}" target="_blank" rel="noopener"><span>${e_(f.text)}</span><span class="svag">${e_(kort(f.tid))}</span></a>` : `<div class="ay-notis">${e_(f.text)}</div>`).join('')
        : '<div class="ay-tom">Inget kundunderlag än. Förbered det med handlingen under Kontroller.</div>'}</div></div>`;
    }
    if (val === 'kandidater') {
      const ks = l.kandidater || [];
      return `<div class="ay-adress"><span class="etikett">${l.blind ? 'Neutrala etiketter i slumpad ordning; bedömningar visas efter ditt första val (i Prototyp)' : 'Kandidaterna i körningen'}</span></div>
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
    const text = `${pv.kandidat ? etikett(pv.kandidat) : 'Helbygget'}, byggd ${kort(pv.byggd)}. Kan ändras medan arbetet pågår; den bevarade versionen visas under Ögonblicksbild.${exp ? ' ' + exp.etikett + '.' : ''}`;
    return `<div class="ay-adress"><span class="etikett" title="${e_(text)}"><b>Arbetsversion</b>: ${e_(text)}</span></div>
      <div class="ay-scen" data-enhet="${e_(A.enhet)}"><iframe title="Förhandsvisning: ${e_(pv.etikett)}" src="${e_(pv.url)}" sandbox="allow-scripts allow-forms allow-same-origin" referrerpolicy="no-referrer" loading="lazy"></iframe></div>`;
  }
  function remsa() {
    const l = A.lage, hs = (l.handlingar || []);
    const stopp = hs.filter((h) => ['stoppa', 'stoppa-overgang'].includes(h.id)), ovriga = hs.filter((h) => !['stoppa', 'stoppa-overgang'].includes(h.id));
    const kontroller = `<section class="ay-panel" aria-labelledby="ay-ktl"><div class="ay-panelhuvud"><h2 id="ay-ktl">Kontroller</h2></div><div class="ay-panelkropp ay-bekrafta">
      ${A.bekrafta ? `<p style="margin:0">${e_(A.bekrafta.text)}</p><div class="ay-knapprad"><button class="ay-knapp fara" type="button" data-handling="${e_(A.bekrafta.id)}" data-bekraftad data-fokus="bekrafta">Stoppa</button><button class="ay-knapp" type="button" data-avbryt-bekraftelse data-fokus="avbryt">Avbryt</button></div>`
        : `<div class="ay-knapprad">${ovriga.map((h) => `<button class="ay-knapp primar" type="button" data-handling="${e_(h.id)}" data-fokus="h-${e_(h.id)}"${h.hinder ? ' aria-disabled="true" title="' + e_(h.hinder) + '"' : ''}>${e_(h.text)}</button>`).join('')}
           ${stopp.map((h) => `<button class="ay-knapp fara" type="button" data-handling="${e_(h.id)}" data-fokus="h-${e_(h.id)}">Stoppa</button>`).join('')}
           ${hs.length ? '' : '<span class="dampad">Ingen handling är möjlig just nu.</span>'}</div>`}
      ${ovriga.filter((h) => h.hinder).map((h) => `<p class="svag" style="margin:0">${e_(h.text)} går inte att starta: ${e_(h.hinder)}</p>`).join('')}
      <p class="svag" style="margin:0" role="status" aria-live="polite" id="ay-handlingssvar">${e_(A.svar)}</p></div></section>`;
    const handelser = senasteHandelser(6);
    const obs = `<section class="ay-panel" aria-labelledby="ay-obs"><div class="ay-panelhuvud"><h2 id="ay-obs">Senast observerat</h2></div><div class="ay-panelkropp">
      ${handelser.length ? `<ul class="ay-handelser">${handelser.map((x) => `<li><time datetime="${e_(x.tid)}">${e_(klocka(x.tid).slice(0, 5))}</time><span>${e_(x.text)}</span></li>`).join('')}</ul>` : '<div class="ay-tom">Inga observerade händelser i körningen än.</div>'}
      ${(l.ofullstandig || []).length ? `<div class="ay-notis varn" style="margin-top:8px">Ofullständigt: ${e_(l.ofullstandig.join('; '))}</div>` : ''}</div></section>`;
    const k = l.korning || {}, b = l.besked || {};
    const beslut = `<section class="ay-panel" aria-labelledby="ay-besl"><div class="ay-panelhuvud"><h2 id="ay-besl">Nästa beslut</h2></div><div class="ay-panelkropp ay-bekrafta">
      ${k.vantar_pa_agaren ? `<p style="margin:0">Kandidaterna väntar på ditt val. Ditt val och godkännande görs i Prototyp; en avgränsad ändring skickar du från samtalet.</p><div class="ay-knapprad"><a class="ay-knapp primar" href="#/prototyp/${e_(A.slug)}">Öppna valet</a></div>`
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
      <div class="knappar"><button class="ay-knapp liten" type="button" data-folj="${e_(s.session_id || '')}" data-fokus="f-${e_(s.session_id || '')}"${s.session_id ? '' : ' disabled'}>Följ</button></div></article>`;
  }
  function roller() {
    const l = A.lage;
    if (A.folj) return foljvy();
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
        <p class="svag" style="margin:0">Följningen läser transkriptet; den startar ingen modell och skickar inget till sessionen. ${s.kalla === 'partnersamtalet' ? 'Partnern når du i samtalet.' : 'Motorns -p-arbetare tar inte emot meddelanden under arbetet: en ändring går genom ditt beslut och nästa handling.'}</p></div>`;
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
    const el = document.getElementById('ay-samtal'); if (!el) return;
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
            <div class="meta"><span>Partnern${anv ? ` · rapporterad användning ${e_(anv.in ?? '?')} in, ${e_(anv.ut ?? '?')} ut tokens` : ''}</span><time>${e_(klocka(m.slut).slice(0, 5))}</time></div></div>`
        : `<div class="ay-msg partnern"><div class="ay-notis fel">${e_(m.fel || 'Inget svar: processen lever inte och ingen svarsfil finns.')}</div></div>`}`;
  }
  function overlamningskort(m) {
    const o = m.overlamning;
    if (o['oläsligt']) return '<div class="ay-overlamning svag">Partnern föreslog en överlämning, men blocket gick inte att läsa.</div>';
    const rad = (n, v) => v ? `<dt>${n}</dt><dd>${e_(v)}</dd>` : '';
    return `<div class="ay-overlamning"><strong>Förslag till överlämning</strong><dl>${rad('Kandidat', o.kandidat ? etikett(o.kandidat) : null)}${rad('Version', o.version)}${rad('Sida', o.sida)}${rad('Del', o.del)}${rad('Mål', o.mal)}${rad('Avgränsning', o.avgransning)}${rad('Förväntat', o.forvantat)}</dl>
      <button class="ay-knapp liten" type="button" data-anvand-forslag="${e_(m.id)}">Använd som min ändring</button><span class="svag"> Du läser, ändrar och skickar själv.</span></div>`;
  }
  function markering() {
    const k = (A.lage?.kandidater || []).find((x) => x.id === A.valdKandidat);
    return { kandidat: k?.id || null, version: k?.version || null, version_hel: k?.version_hel || null, vy: { '': 'Arbetsyta', flode: 'Byggflöde', kod: 'Kod och preview' }[A.vy], korning: A.lage?.korning?.startad || null };
  }
  function ritaSkriv() {
    const f = document.getElementById('ay-skriv'); if (!f || !A.lage) return;
    if (f.contains(document.activeElement) && f.dataset.ritad) { uppdateraSkrivstatus(); return; }
    const utkast = f.querySelector('textarea')?.value ?? (sessionStorageLas('nwp-arbetsyta-utkast:' + A.slug) || '');
    const mk = markering(), kand = mk.kandidat ? etikett(mk.kandidat) : null;
    f.dataset.ritad = '1';
    f.innerHTML = `<div class="ay-segment" role="group" aria-label="Avsikt">${[['fraga', 'Fråga'], ['plan', 'Planförslag'], ['andring', 'Ändring']].map(([k, n]) => `<button type="button" data-avsikt="${k}" data-fokus="a-${k}" aria-pressed="${A.avsikt === k}">${n}</button>`).join('')}</div>
      <label class="dolt" for="ay-text">Meddelande</label>
      <textarea id="ay-text" data-fokus="text" placeholder="${A.avsikt === 'andring' ? 'Vad ska ändras, och var?' : A.avsikt === 'plan' ? 'Vad vill du ha en plan för?' : 'Skriv en fråga om läget'}">${e_(utkast)}</textarea>
      ${A.avsikt === 'andring' ? `<div class="ay-skrivrad"><label class="svag">Sida <input data-falt="sida" data-fokus="sida" style="width:110px" class="ay-knapp liten" placeholder="/ (startsidan)"></label><label class="svag">Del <input data-falt="del" data-fokus="del" style="width:140px" class="ay-knapp liten" placeholder="t.ex. första vyn"></label></div>` : ''}
      ${A.avsikt === 'andring' && A.lage.blind ? '<p class="ay-notis varn" style="margin:0">En ändring som du skickar är ditt val av kandidaten i körningen. Bedömningarna visas efter det.</p>' : ''}
      <div class="ay-markering" id="ay-markering">Gäller: <b>${e_(A.lage.projekt?.namn || A.slug)}</b>${kand ? `, <b>${e_(kand)}</b>${mk.version ? ' version ' + e_(mk.version) : ''}` : ', ingen kandidat vald'}, vy ${e_(mk.vy)}</div>
      <div class="ay-skrivrad"><span class="svag" id="ay-skrivsvar" role="status" aria-live="polite"></span><span class="ay-knapprad">
        ${A.avsikt === 'andring' ? `<button class="ay-knapp" type="submit" data-skicka="partner" data-fokus="s-partner">Be partnern formulera</button><button class="ay-knapp primar" type="button" data-skicka="andring" data-fokus="s-andring">Skicka ändring</button>`
          : `<button class="ay-knapp primar" type="submit" data-skicka="partner" data-fokus="s-partner">Skicka</button>`}</span></div>`;
    uppdateraSkrivstatus();
  }
  function sessionStorageLas(k) { try { return sessionStorage.getItem(k); } catch { return null; } }
  function uppdateraSkrivstatus() {
    const p = A.partner, upptagen = (p?.meddelanden || []).some((m) => m.lage === 'arbetar') || (p?.andra_processer || []).length;
    const knapp = document.querySelector('#ay-skriv [data-skicka="partner"]');
    if (knapp) knapp.disabled = Boolean(upptagen);
    const a = document.querySelector('#ay-skriv [data-skicka="andring"]');
    if (a) {
      const k = A.lage.korning || {}, mk = markering();
      const hinder = !mk.kandidat ? 'välj kandidaten ändringen gäller (under Kandidater)' : !['klar_for_bedomning', 'fel'].includes(k.steg) ? 'körningen väntar inte på ditt beslut' : null;
      a.disabled = Boolean(hinder); a.title = hinder || '';
      const m = document.getElementById('ay-markering'); if (m) m.dataset.hinder = hinder || '';
    }
    const s = document.getElementById('ay-skrivsvar');
    if (s && upptagen && !s.textContent) s.textContent = (p?.andra_processer || []).length ? 'Sessionen är öppen i en annan process.' : 'Partnern svarar…';
  }

  async function skickaPartner() {
    const t = document.getElementById('ay-text'), svar = document.getElementById('ay-skrivsvar');
    const text = t.value.trim(); if (!text) { svar.textContent = 'Skriv ett meddelande först.'; t.focus(); return; }
    const nyckel = 'nwp-arbetsyta-meddelande:' + A.slug, id = nyttId(nyckel), mk = markering();
    svar.textContent = 'Skickar…';
    try {
      await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/partner', { meddelande_id: id, text, avsikt: A.avsikt,
        kontext: { kandidat: mk.kandidat, version: mk.version, vy: mk.vy, korning: mk.korning, sida: document.querySelector('[data-falt="sida"]')?.value || null, del: document.querySelector('[data-falt="del"]')?.value || null } });
      slappId(nyckel, id); t.value = ''; try { sessionStorage.removeItem('nwp-arbetsyta-utkast:' + A.slug); } catch { /* */ }
      svar.textContent = 'Skickat. Partnern svarar i samma session.';
      await laddaPartner();
    } catch (err) { svar.textContent = (err.status === 409 ? '' : 'Svaret gick inte att bekräfta: ') + err.message + (err.status === 409 ? '' : '. Försök igen; samma meddelande-id används.'); }
  }
  async function skickaAndring() {
    const t = document.getElementById('ay-text'), svar = document.getElementById('ay-skrivsvar'), mk = markering();
    const text = t.value.trim(); if (!text) { svar.textContent = 'Skriv vad som ska ändras.'; t.focus(); return; }
    const k = (A.lage.kandidater || []).find((x) => x.id === mk.kandidat);
    const nyckel = 'nwp-arbetsyta-andring:' + A.slug, id = nyttId(nyckel);
    svar.textContent = 'Skickar ändringen…';
    try {
      await postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/andring', { andring_id: id, text, beslut: k && ['forfinad', 'vald'].includes(k.status) ? 'putsa' : 'valj',
        kandidat: mk.kandidat, version: mk.version_hel, korning: mk.korning, vy: mk.vy, sida: document.querySelector('[data-falt="sida"]')?.value || null, del: document.querySelector('[data-falt="del"]')?.value || null });
      slappId(nyckel, id); t.value = '';
      const nasta = (A.lage.handlingar || []).find((h) => ['valda', 'putsa'].includes(h.id));
      svar.textContent = 'Ändringen är sparad som ditt beslut i domloggen, bunden till kandidat och version. Inget arbete har startat: starta förfiningen under Kontroller.' + (nasta ? '' : ' Läs om läget om knappen inte syns.');
    } catch (err) { svar.textContent = err.status === 409 ? 'Inaktuell: ' + err.message : 'Svaret gick inte att bekräfta: ' + err.message + '. Försök igen; samma ändrings-id används.'; }
  }

  // --- handlingarna: flödets befintliga start, samma start-id som Flöde ---
  async function handling(id, bekraftad) {
    if (['stoppa', 'stoppa-overgang'].includes(id) && !bekraftad) {
      A.bekrafta = { id, text: id === 'stoppa' ? 'Stoppa arbetaren och dess sessioner? Det som är klart bevaras; körningen kan återupptas med Återuppta arbetet.' : 'Begär stopp av helbygget, exporten eller förhandsvisningen? Stoppet sparas före processen nås; arbetets slutpost säger vad som hann bli klart.' };
      rita(); document.querySelector('[data-fokus="bekrafta"]')?.focus(); return;
    }
    A.bekrafta = null;
    const nyckel = 'nwp-start:' + A.slug + ':' + id, startId = nyttId(nyckel);
    A.svar = 'Skickar begäran…'; rita();
    try {
      const r = await postJson('/api/flode/' + encodeURIComponent(A.slug) + '/start', { handling: id, start_id: startId });
      slappId(nyckel, startId);
      A.fokusStart = startId;
      A.svar = (r.besked || 'Begäran är registrerad.') + ` (start-id ${startId.slice(0, 8)})`;
    } catch (err) { A.svar = 'Svaret gick inte att bekräfta: ' + err.message + '. Läs läget eller försök igen; samma start-id används.'; }
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
        ${l.blind ? '<div class="ay-notis">Ditt första val i körningen är inte gjort: förslagen har neutrala etiketter, och bedömningar, skäl och sökvägar i aktiviteten visas efter valet.</div>' : ''}
        ${Object.keys(grupper).length ? Object.entries(grupper).map(([g, ss]) => `<section class="ay-panel ay-grupp" aria-label="${e_(g)}"><div class="ay-panelhuvud"><h2>${e_(g)}</h2><span class="svag">${ss.length} sessioner</span></div><div class="ay-panelkropp">${ss.map(sessionskort).join('')}</div></section>`).join('')
          : '<div class="ay-tom">Inga sessioner i körningen än. När en körning startar dyker dess sessioner upp här av sig själva.</div>'}
        ${vald ? `<section class="ay-panel" aria-labelledby="ay-detalj-rubrik"><div class="ay-panelhuvud"><h2 id="ay-detalj-rubrik">${e_(roll(vald))}${vald.kandidat ? ' · ' + e_(etikett(vald.kandidat)) : ''}</h2>${lagechip(vald.lage, vald.lage_text)}<button class="ay-knapp liten" type="button" data-folj-slut>Stäng</button></div><div class="ay-panelkropp ay-detalj">${detalj(vald)}</div></section>` : ''}
        <section class="ay-panel"><details class="metod"><summary>Så är flödet tänkt (metodkartan, README)</summary><div class="ay-panelkropp" id="ay-metod">${metod()}</div></details></section>
        <section class="ay-panel" aria-labelledby="ay-system"><div class="ay-panelhuvud"><h2 id="ay-system">Systemförbättring, skilt från kundproduktionen</h2></div><div class="ay-panelkropp ay-knapprad"><a class="ay-knapp liten" href="#/kirurgen">Kirurgen</a><a class="ay-knapp liten" href="#/backlog">Backlog</a><a class="ay-knapp liten" href="#/kalibrering">Kalibrering</a><a class="ay-knapp liten" href="#/dokumentation">Dokumentation och rapporter</a></div></section>
      </div>
      <section class="ay-panel" aria-labelledby="ay-tl"><div class="ay-panelhuvud"><h2 id="ay-tl">Sessionsflöde</h2>${anslutning()}</div><div class="ay-panelkropp">
        <ul class="ay-tidslinje">${tidslinje().map((x) => `<li><time datetime="${e_(x.tid)}">${e_(klocka(x.tid).slice(0, 5))}</time><span>${e_(x.text)}</span></li>`).join('') || '<li><span class="dampad">Inget observerat än.</span></li>'}</ul>
        ${(l.helbygge || []).length ? `<h3 style="margin:14px 0 6px">Helbyggets körningar (historik)</h3><ul class="ay-tidslinje">${l.helbygge.map((k) => `<li><time>${e_(k.id.slice(9, 13))}</time><span>${e_(k.id)}: ${e_(LAGEN[k.lage] || k.lage)}${k.slutkod != null ? ', slutkod ' + e_(k.slutkod) : ''}${k.uteblev ? ', slutposten uteblev' : ''}</span></li>`).join('')}</ul>` : ''}</div></section>`;
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
    for (const j of l.startjournal || []) ut.push({ tid: j.tid, text: `Begäran ${j.handling || '?'} (start-id ${String(j.start_id).slice(0, 8)}): ${j.status || 'okänd'}${j.stopp_begart ? ', stopp begärt' : ''}${j.slutkod != null ? ', slutkod ' + j.slutkod : ''}${j.process_lever ? ', processen lever' : ''}` });
    for (const s of l.sessioner || []) { if (s.start) ut.push({ tid: s.start, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: startade` }); if (s.slut) ut.push({ tid: s.slut, text: `${roll(s)}${s.kandidat ? ' (' + etikett(s.kandidat) + ')' : ''}: ${s.lage_text || LAGEN[s.lage]}` }); }
    for (const o of l.overlamningar || []) ut.push({ tid: o.tid, text: `Din ändring till ${etikett(o.kandidat)}: ${Object.keys(o.steg).join(' → ').replace(/_/g, ' ')}` });
    if (l.korning?.startad) ut.push({ tid: l.korning.startad, text: `Körningen startade (läge ${l.korning.lage || '?'})${l.korning.start_handling ? ' genom ' + l.korning.start_handling : ''}` });
    return ut.filter((x) => x.tid).sort((a, b) => String(b.tid).localeCompare(String(a.tid))).slice(0, 30);
  }
  function metod() {
    if (!A.metod) { hamta('/api/flode').then((d) => { A.metod = d.kedjan; const m = document.getElementById('ay-metod'); if (m) m.innerHTML = metod(); }).catch(() => {}); return '<p class="svag">Läser metodkartan…</p>'; }
    if (A.metod.fel) return `<p class="svag">${e_(A.metod.fel)}</p>`;
    return `<p class="svag">Arbetssättet, ur README.md; inte kundens förlopp.</p><ol style="margin:0;padding-left:18px;display:grid;gap:6px">${(A.metod.steg || []).map((s) => `<li><b>${e_(String(s.steg).replace(/<[^>]+>/g, ''))}</b><div class="svag">${e_(String(s.vem).replace(/<[^>]+>/g, '')).slice(0, 400)}</div></li>`).join('')}</ol>`;
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
    try { A.kod.data = await hamta('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/kod?' + q); } catch (err) { el.innerHTML = `<div class="ay-notis fel">${e_(err.message)}</div>`; return; }
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
    h.innerHTML = `<h2 id="ay-fil-rubrik" class="mono">${e_(sajtvag(f.fil))}</h2><div class="ay-segment" role="group" aria-label="Visning"><button type="button" data-kodvisning="diff" aria-pressed="${A.kod.visning === 'diff'}">Diff mot ${e_(A.kod.data.mot || '–')}</button><button type="button" data-kodvisning="hel" aria-pressed="${A.kod.visning === 'hel'}">Hela filen</button></div>${f.finns ? `<button class="ay-knapp liten" type="button" data-oppna-fil="${e_(f.fil)}">Öppna i editorn</button>` : ''}`;
    if (A.kod.visning === 'diff') {
      el.innerHTML = f.diff == null ? '<div class="ay-tom" style="padding:14px">Ingen bevarad version att jämföra med.</div>' : f.diff.length ? `<pre class="ay-kodtext">${f.diff.map((r) => `<span class="${r.startsWith('@@') ? 'hunk' : r.startsWith('+') ? 'plus' : r.startsWith('-') ? 'minus' : ''}">${e_(r)}</span>`).join('')}</pre>` : '<div class="ay-tom" style="padding:14px">Ingen skillnad mot den bevarade versionen.</div>';
    } else el.innerHTML = f.text == null ? '<div class="ay-tom" style="padding:14px">Filen finns inte i arbetsversionen.</div>' : `<pre class="ay-kodtext">${e_(f.text).split('\n').map((r) => `<span>${r || ' '}</span>`).join('')}</pre>`;
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

  // --- händelserna ---
  document.addEventListener('click', (ev) => {
    const ay = ev.target.closest('.ay'); if (!ay) return;
    const t = ev.target.closest('button, a'); if (!t) return;
    const d = t.dataset;
    if (d.material) { A.material = d.material; ritaMaterial(); document.querySelector(`[data-fokus="m-${d.material}"]`)?.focus(); return; }
    if (d.enhet) { A.enhet = d.enhet; sparaLayout({ enhet: d.enhet }); ritaMaterial(); document.querySelector(`[data-fokus="e-${d.enhet}"]`)?.focus(); return; }
    if (d.kandidat) { A.valdKandidat = d.kandidat; A.material = null; rita(); ritaSkriv(); return; }
    if (d.laddaOm !== undefined) { const f = ay.querySelector('#ay-material iframe'); if (f) f.src = f.src; return; }
    if (d.folj !== undefined) { A.folj = d.folj || null; if (A.vy === 'kod') ritaKodaktivitet(); else rita(); document.querySelector('[data-fokus="folj-slut"]')?.focus(); return; }
    if (d.foljSlut !== undefined) { const id = A.folj; A.folj = null; rita(); document.querySelector(`[data-fokus="f-${CSS.escape(id || '')}"]`)?.focus(); return; }
    if (d.falla) { const ytan = document.getElementById('ay-ytan'); ytan.toggleAttribute(d.falla === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold', true); sparaLayout({ [d.falla === 'vanster' ? 'vansterDold' : 'hogerDold']: true }); document.querySelector(`[data-visa="${d.falla}"]`)?.focus(); return; }
    if (d.visa) { const ytan = document.getElementById('ay-ytan'); ytan.removeAttribute(d.visa === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold'); sparaLayout({ [d.visa === 'vanster' ? 'vansterDold' : 'hogerDold']: false }); return; }
    if (d.omrade) { const ytan = document.getElementById('ay-ytan'); ytan.dataset.omrade = d.omrade; sparaLayout({ omrade: d.omrade }); ay.querySelectorAll('[data-omrade]').forEach((b) => b.tagName === 'BUTTON' && b.setAttribute('aria-pressed', String(b.dataset.omrade === d.omrade))); return; }
    if (d.avsikt) { A.avsikt = d.avsikt; const f = document.getElementById('ay-skriv'); try { sessionStorage.setItem('nwp-arbetsyta-utkast:' + A.slug, f.querySelector('textarea').value); } catch { /* */ } f.dataset.ritad = ''; ritaSkriv(); document.querySelector(`[data-fokus="a-${d.avsikt}"]`)?.focus(); return; }
    if (d.skicka === 'andring') { ev.preventDefault(); skickaAndring(); return; }
    if (d.anvandForslag) { const m = (A.partner?.meddelanden || []).find((x) => x.id === d.anvandForslag), o = m?.overlamning || {};
      if (o.kandidat && (A.lage.kandidater || []).some((k) => k.id === o.kandidat)) A.valdKandidat = o.kandidat;
      A.avsikt = 'andring'; const f = document.getElementById('ay-skriv'); f.dataset.ritad = ''; ritaSkriv();
      document.getElementById('ay-text').value = [o.mal, o.avgransning ? 'Rör inte: ' + o.avgransning : null, o.forvantat ? 'Klart när: ' + o.forvantat : null].filter(Boolean).join('\n');
      if (o.sida) document.querySelector('[data-falt="sida"]').value = o.sida; if (o.del) document.querySelector('[data-falt="del"]').value = o.del;
      document.getElementById('ay-text').focus(); return; }
    if (d.handling) { if (t.getAttribute('aria-disabled') === 'true') return; handling(d.handling, d.bekraftad !== undefined); return; }
    if (d.avbrytBekraftelse !== undefined) { A.bekrafta = null; rita(); return; }
    if (d.kodfil) { laddaKod(d.kodfil); return; }
    if (d.kodvisning) { A.kod.visning = d.kodvisning; ritaFil(); return; }
    if (d.oppnaFil) { postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/oppna', { kandidat: A.kod.kandidat, fil: d.oppnaFil }).then((r) => meddela('Öppnad i ' + r.program)).catch((err) => meddela('Kunde inte öppna: ' + err.message)); return; }
    if (d.loggLas !== undefined) { laddaLogg(true); return; }
  });
  document.addEventListener('submit', (ev) => { if (ev.target.id === 'ay-skriv') { ev.preventDefault(); skickaPartner(); } });
  document.addEventListener('change', (ev) => {
    if (ev.target.id === 'ay-kund') location.hash = '#/arbetsyta/' + encodeURIComponent(ev.target.value) + (A.vy ? '/' + A.vy : '');
    if (ev.target.id === 'ay-kodkand') { A.valdKandidat = ev.target.value; A.kod.fil = null; A.kod.mot = null; laddaKod(); ritaMaterial(); }
    if (ev.target.id === 'ay-kodmot') laddaKod(undefined, ev.target.value || null);
  });
  document.addEventListener('input', (ev) => { if (ev.target.id === 'ay-text') { try { sessionStorage.setItem('nwp-arbetsyta-utkast:' + A.slug, ev.target.value); } catch { /* */ } } });
  document.addEventListener('keydown', (ev) => { if (ev.target.id === 'ay-text' && ev.key === 'Enter' && (ev.metaKey || ev.ctrlKey)) { ev.preventDefault(); A.avsikt === 'andring' ? skickaAndring() : skickaPartner(); } });
  window.__arbetsyta = A;  // för proven: läget i vyn, aldrig något att skriva i
})();
