// Ändringsfliken (ägarens tillägg 2026-10-11; kunskap/andringar.md): webbplatsens ändringsagent, en riktig Claude
// Code-session i kundrepot som dashboarden äger (dashboard/andringsflik.py, terminal.py). Vyn visar terminalen (xterm.js,
// dashboard/vendor/xterm/) och skickar tangenter, storlek och stopp; den väljer aldrig program, katalog eller argument.
// Förhandsvisningen, arbetskopians ändringar, historiken och bilagorna står bredvid. En vy i taget äger inmatningen;
// en annan ser utdata och kan ta över uttryckligen.
(() => {
  'use strict';
  const e_ = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const slumpId = () => { const b = new Uint8Array(16); crypto.getRandomValues(b); return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join(''); };
  // vyns klient-id: ett per flik, kvar när fliken laddas om (sessionStorage), så att en omladdad flik fortsätter skriva och
  // en ny flik får ta över uttryckligen
  const klientId = () => { try { let k = sessionStorage.getItem('nwp-andringar-klient'); if (!k) { k = slumpId(); sessionStorage.setItem('nwp-andringar-klient', k); } return k; } catch { return slumpId(); } };
  const T = { slug: null, lage: null, term: null, fit: null, sid: null, offset: 0, es: null, klient: klientId(), ko: '', kotimer: null, gen: 0,
    flik: 'forhand', bredd: 'dator', stoppBekrafta: false, notis: null, storlekTimer: null, ateranslut: 0, diff: null, bilagor: [] };
  const kort = (t) => { if (!t) return '–'; const d = new Date(t); return isNaN(d) ? String(t) : d.toLocaleString('sv-SE', { dateStyle: 'short', timeStyle: 'short' }); };
  async function hamta(url) {
    const r = await fetch(url, { cache: 'no-store', headers: { Accept: 'application/json' } });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { const f = new Error(j.fel || ('HTTP ' + r.status)); f.status = r.status; throw f; }
    return j;
  }
  async function posta(url, body) {
    let k = ''; try { k = localStorage.getItem('nwp-dashboardnyckel') || ''; } catch { /* i appen räcker sessionen */ }
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Nyckel': k }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { const f = new Error(j.fel || ('HTTP ' + r.status)); f.status = r.status; f.slag = j.slag; throw f; }
    return j;
  }
  const api = (del = '') => '/api/andringar/' + encodeURIComponent(T.slug) + del;
  const postaVal = (body) => posta('/api/repovaljaren', body);  // hämta och uppdatera går genom repoväljarens motor

  // xterm.js laddas när fliken öppnas första gången, från dashboardens egna filer
  let xtermLaddas = null;
  function laddaXterm() {
    if (window.Terminal && window.FitAddon) return Promise.resolve();
    if (xtermLaddas) return xtermLaddas;
    const skript = (src) => new Promise((ok, fel) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = () => fel(new Error('kunde inte ladda ' + src)); document.head.append(s); });
    if (!document.querySelector('link[href="/vendor/xterm/xterm.css"]')) document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="/vendor/xterm/xterm.css">');
    xtermLaddas = skript('/vendor/xterm/xterm.js').then(() => skript('/vendor/xterm/addon-fit.js'));
    return xtermLaddas;
  }

  window.andringarvy = async function andringarvy(slug) {
    const gen = ++T.gen;
    if (T.slug !== slug) { stangStrom(); if (T.term) { T.term.dispose(); T.term = null; } Object.assign(T, { slug, lage: null, sid: null, offset: 0, notis: null, diff: null, stoppBekrafta: false }); }
    try { localStorage.setItem('nwp-portal:kund', slug); } catch { /* bekvämlighet */ }
    const rot = document.getElementById('rot');
    rot.innerHTML = `<main class="an" id="vy" aria-labelledby="an-rubrik">
      <header class="an-huvud">
        <div class="an-id"><h1 id="an-rubrik">Ändringar</h1><span class="an-sajt" id="an-sajt"></span>${window.repovaljaren ? window.repovaljaren.knapp('Öppna kundrepo', 'pt-knapp an-repoknapp') : ''}</div>
        <div class="an-lage" id="an-lage" role="status" aria-live="polite"></div>
        <div class="an-knappar" id="an-knappar"></div>
      </header>
      <div class="an-notis" id="an-notis" role="status" aria-live="polite" hidden></div>
      <div class="an-yta">
        <section class="an-terminal" aria-label="Terminalen med webbplatsens ändringsagent">
          <div class="an-xterm" id="an-xterm"></div>
          <p class="an-tips">Tangenterna går till agenten när terminalen har fokus: Ctrl+C avbryter agentens svar, inklistring och flera rader fungerar. F6 flyttar fokus ut ur terminalen, Skift+F6 tillbaka till flikarna.</p>
        </section>
        <aside class="an-sida" aria-label="Förhandsvisning, ändringar, historik och bilagor">
          <div class="an-flikar" role="tablist" aria-label="Bredvid terminalen">${[['forhand', 'Förhandsvisning'], ['andringar', 'Ändringar'], ['historik', 'Historik'], ['bilagor', 'Bilagor']].map(([k, n]) =>
            `<button type="button" role="tab" id="an-tab-${k}" data-an-flik="${k}" aria-selected="${T.flik === k}" aria-controls="an-panel" tabindex="${T.flik === k ? 0 : -1}">${n}</button>`).join('')}</div>
          <div class="an-panel" id="an-panel" role="tabpanel"></div>
        </aside>
      </div>
    </main>`;
    koppla(rot.querySelector('main.an'));  // vyns eget element: ersätts vid nästa ritning, så lyssnarna blir aldrig dubbla
    try { await laddaXterm(); } catch (err) { visaNotis('Terminalkomponenten kunde inte laddas: ' + err.message); }
    if (gen !== T.gen) return;
    skapaTerminal();
    await lasLage(gen);
  };

  function skapaTerminal() {
    const el = document.getElementById('an-xterm'); if (!el || !window.Terminal) return;
    if (T.term) { T.term.dispose(); T.term = null; }
    const term = new window.Terminal({ cursorBlink: true, convertEol: false, scrollback: 8000, fontSize: 13, lineHeight: 1.15,
      // Option skriver tecken, som i macOS: på ett svenskt tangentbord kräver @ [ ] { } | \ och – Option, och som Meta blev
      // de ESC-sekvenser (fångat med verkliga tangenter i appens prov 2026-10-11); flera rader går med inklistring eller \ + Enter
      fontFamily: 'ui-monospace, "SF Mono", Menlo, monospace', allowProposedApi: false, macOptionIsMeta: false,
      theme: { background: '#171a2b', foreground: '#e6e7f1', cursor: '#b9b2ff', selectionBackground: '#4a4380' } });
    const fit = new window.FitAddon.FitAddon();
    term.loadAddon(fit);
    term.open(el);
    try { fit.fit(); } catch { /* utan storlek än */ }
    // F6 och Skift+F6 går aldrig till agenten: de flyttar fokus ut ur terminalen (WCAG 2.1.2, ingen tangentfälla)
    term.attachCustomKeyEventHandler((ev) => {
      if (ev.key !== 'F6' || ev.type !== 'keydown') return ev.key !== 'F6';
      const mal = ev.shiftKey ? document.querySelector('.an-flikar [aria-selected="true"]') : document.querySelector('#an-knappar button, .an-id button');
      ev.preventDefault(); mal?.focus(); return false;
    });
    term.onData((d) => { T.ko += d; if (!T.kotimer && !T.skickar) T.kotimer = setTimeout(skickaKo, 12); });
    term.onResize(({ cols, rows }) => { clearTimeout(T.storlekTimer); T.storlekTimer = setTimeout(() => skickaStorlek(cols, rows), 150); });
    new ResizeObserver(() => { try { fit.fit(); } catch { /* */ } }).observe(el);
    T.term = term; T.fit = fit; T.offset = 0;
    term.write('\x1b[2mDen här terminalen visar webbplatsens ändringsagent. Starta den med knappen ovanför när du vill ge ett uppdrag.\x1b[0m\r\n');
  }

  async function lasLage(gen = T.gen) {
    let l;
    try { l = await hamta(api()); } catch (err) { if (gen === T.gen) visaNotis('Läget kunde inte läsas: ' + err.message); return; }
    if (gen !== T.gen) return;
    T.lage = l;
    const levande = l.session?.lever;
    const processId = levande ? `${l.session.sid}:${l.session.pid}` : null;  // återupptagningen behåller sessions-id men är en ny process
    if (levande && processId !== T.process) { T.process = processId; T.sid = l.session.sid; T.offset = 0; T.term?.reset(); oppnaStrom(); }
    if (!levande) T.process = null;
    if (!levande && T.es) stangStrom();
    // knapparna ritas om när sessionens läge ändrats, annars bara när fokus inte står i dem (en knapp försvinner aldrig under ett klick)
    const lageNyckel = JSON.stringify([levande, l.session?.agare === T.klient, l.session?.kan_aterupptas, (l.hinder || []).length, l.kvittering?.kan,
      l.synk ? [l.synk.lage, l.synk.fore, l.synk.efter, l.synk.lokala, l.synk.pa_standardgren] : null]);
    if (lageNyckel !== T.lageNyckel || !document.getElementById('an-knappar')?.contains(document.activeElement)) { T.lageNyckel = lageNyckel; ritaHuvud(); }
    ritaPanel(false);
  }

  function ritaHuvud() {
    const l = T.lage; if (!l) return;
    const s = l.session || {};
    document.getElementById('an-sajt').innerHTML = `${e_(l.namn)}${l.fiktiv ? ' <span class="pt-test">Testkund</span>' : ''}`;
    const chip = (text, slag) => `<span class="an-chip${slag ? ' ' + slag : ''}">${e_(text)}</span>`;
    const delar = [chip(l.arbetskopia_finns ? `Repo ${l.repo}` : 'Ingen arbetskopia'), l.gren ? chip(`Gren ${l.gren}`) : '', l.huvud ? chip(`HEAD ${String(l.huvud).slice(0, 8)}`) : '',
      s.lever ? chip(s.agare === T.klient ? 'Agenten lever: du skriver' : 'Agenten lever: en annan vy skriver', 'ok') : chip(s.senast === 'avslutad' || s.sid ? 'Agenten är avslutad' : 'Ingen agent startad'),
      l.skrivlas?.halls ? chip('Skrivlåset: agenten arbetar', 'varn') : '',
      l.lokala_andringar?.length ? chip(`${l.lokala_andringar.length} ändrade filer i arbetskopian`, 'varn') : '',
      synkChip(l.synk),
      l.export?.kalla === 'andring' && l.export?.commit === l.huvud ? chip('Ändringen är kvitterad: förhandsvisa under Bygge', 'ok')
        // ett misslyckat kvitteringsförsök visas bara medan det finns något okvitterat att kvittera
        : l.kvittering?.forsok && !['kvitterad', 'samma som exporten', 'ingen arbetskopia'].includes(l.kvittering.skal) ? chip('Inte kvitterad: ' + l.kvittering.forsok.skal, 'varn') : ''];
    const oppen = document.querySelector('#an-lage details')?.open;  // de utfällda detaljerna står kvar när läget läses om
    document.getElementById('an-lage').innerHTML = delar.join('') + `<details class="an-detaljer"${oppen ? ' open' : ''}><summary>Tekniska detaljer</summary><ul>${[...l.fakta, ...(l.fragor || []).map((f) => 'Fråga: ' + f)].map((f) => `<li>${e_(f)}</li>`).join('')}
      <li>Modell: ${e_(l.modell)}</li><li>Sessions-id: ${e_(s.sid || '–')}${s.startad ? ', startad ' + e_(kort(s.startad)) : ''}</li></ul></details>`;
    let k = '';
    if ((l.hinder || []).length) k = `<p class="an-hinder">${l.hinder.map(e_).join('<br>')}</p>`;
    else if (!s.lever) {
      k = `<button class="pt-knapp" type="button" data-an-starta>Starta agenten</button>`
        + (s.kan_aterupptas ? `<button class="pt-knapp mjuk" type="button" data-an-ateruppta title="Samma konversation som förra gången (claude --resume), efter en kontroll av arbetskopian">Återuppta förra samtalet</button>` : '')
        + `<span class="an-forklaring">${s.kan_aterupptas ? 'Starta: en ny session som läser webbplatsens kunskap. Återuppta: förra samtalet fortsätter.' : 'Agenten startar först när du ber om det.'}</span>`;
    } else {
      k = (s.agare !== T.klient ? `<button class="pt-knapp" type="button" data-an-ta-over>Ta över inmatningen</button>` : '')
        + (T.stoppBekrafta ? `<span class="an-bekrafta">Stoppa agentprocessen? Ett pågående verktygsanrop avbryts; ändringar som redan skrivits står kvar.
            <button class="pt-knapp fara" type="button" data-an-stoppa-ja>Stoppa</button><button class="pt-knapp mjuk" type="button" data-an-stoppa-nej>Avbryt</button></span>`
          : `<button class="pt-knapp mjuk" type="button" data-an-stoppa>Stoppa agenten</button>`);
    }
    if (l.kvittering?.kan && !(l.hinder || []).length) k = `<button class="pt-knapp" type="button" data-an-kvittera title="Den prövade commiten blir kundens leverabel, som förhandsvisas och släpps under Bygge">Kvittera ändringen</button>` + k;
    // fjärren: hämta är alltid möjligt med ett fjärrepo; uppdatera bara framåt, på en ren arbetskopia på standardgrenen
    const y = l.synk;
    if (y?.origin && !(l.hinder || []).length) {
      k += `<button class="pt-knapp mjuk" type="button" data-an-hamta title="git fetch: hämtar fjärrens commits utan att ändra arbetskopian">Hämta</button>`;
      if (y.efter > 0 && !y.fore && !y.lokala && y.pa_standardgren) k += `<button class="pt-knapp mjuk" type="button" data-an-uppdatera title="Bara framåt (fast-forward) till origin/${e_(y.standardgren)}">Uppdatera (${y.efter})</button>`;
    }
    document.getElementById('an-knappar').innerHTML = k;
  }

  // panelen ritas om bara när det den visar har ändrats (förhandsvisningens ram laddas annars om vid varje läsning)
  function panelnyckel() {
    const l = T.lage || {};
    return JSON.stringify([T.flik, T.bredd, l.kontroll?.tid, l.bygge?.tid, T.flik === 'andringar' ? T.diff : null, T.flik === 'historik' ? [l.redovisning, l.historik] : null,
      T.flik === 'bilagor' ? T.bilagor.length : null, T.flik === 'historik' ? [l.export?.id, T.intag] : null]);
  }
  function ritaPanel(tvinga = true) {
    const el = document.getElementById('an-panel'); if (!el || !T.lage) return;
    const nyckel = panelnyckel();
    if (!tvinga && el.dataset.nyckel === nyckel) return;
    el.dataset.nyckel = nyckel;
    const l = T.lage;
    document.querySelectorAll('[data-an-flik]').forEach((b) => { const ja = b.dataset.anFlik === T.flik; b.setAttribute('aria-selected', String(ja)); b.tabIndex = ja ? 0 : -1; });
    el.setAttribute('aria-labelledby', 'an-tab-' + T.flik);
    if (T.flik === 'forhand') {
      const k = l.kontroll;
      const bilder = k && k.katalog ? Object.entries(k.bilder || {}) : [];
      el.innerHTML = `<div class="an-rad"><div class="an-segment" role="group" aria-label="Bredd">${[['mobil', 'Mobil'], ['dator', 'Dator']].map(([b, n]) =>
          `<button type="button" data-an-bredd="${b}" aria-pressed="${T.bredd === b}">${n}</button>`).join('')}</div>
        <button class="pt-knapp mjuk" type="button" data-an-ladda>Ladda om</button></div>
        <p class="an-under">${k ? `Senaste kontrollen ${e_(kort(k.tid))}: ${k.ok ? 'godkänd' : 'inte godkänd'}${(k.brister || []).length ? ' (' + e_(k.brister.slice(0, 3).join('; ')) + ')' : ''}. Förhandsvisningen visar arbetskopians senaste bygge; ändras arbetskopian efter kontrollen är bygget äldre än arbetet.` : 'Ingen kontroll än: agentens provväg bygger och fotograferar arbetskopian.'}</p>
        ${l.bygge ? `<p class="an-under">Arbetskopian byggd ${e_(kort(l.bygge.tid))}.</p><div class="an-scen" data-bredd="${T.bredd}"><iframe title="Förhandsvisning av arbetskopians bygge" src="/visa-andring/${e_(encodeURIComponent(T.slug))}" sandbox="allow-scripts allow-forms allow-same-origin" referrerpolicy="no-referrer"></iframe></div>`
          : '<div class="an-tom">Arbetskopian är inte byggd än. Agentens provväg bygger den; förhandsvisningen visas här efteråt.</div>'}
        ${bilder.length ? `<h2 class="an-h2">Kontrollens bilder</h2><div class="an-bilder">${bilder.flatMap(([sida, b]) => Object.entries(b).map(([vy, p]) => {
          const m = String(p).match(/kontroller\/(\d{8}T\d{6}Z)\/([a-z0-9-]+)\/(vy-(?:390|1440)-forsta\.png)$/);
          return m ? `<figure><a href="${api(`/kontroll/${m[1]}/${m[2]}/${m[3]}`)}" target="_blank" rel="noopener"><img src="${api(`/kontroll/${m[1]}/${m[2]}/${m[3]}`)}" alt="${e_(sida)} i ${vy} px" loading="lazy"></a><figcaption>${e_(sida)} · ${vy} px</figcaption></figure>` : '';
        })).join('')}</div>` : ''}`;
    } else if (T.flik === 'andringar') {
      const d = T.diff;
      el.innerHTML = !d ? '<p class="an-under">Läser arbetskopians ändringar …</p>' : !d.finns ? '<p class="an-under">Ingen arbetskopia.</p>'
        : `<p class="an-under">Commits sedan ${e_(d.bas_slag)}${d.bas ? ' (' + e_(String(d.bas).slice(0, 8)) + ')' : ''}: ${d.commits_sedan_bas.length || 'inga'}.</p>
          ${d.commits_sedan_bas.length ? `<ul class="an-lista">${d.commits_sedan_bas.map((c) => `<li><code>${e_(c)}</code></li>`).join('')}</ul>` : ''}
          <h2 class="an-h2">Ej committat i arbetskopian</h2>${d.arbetstrad ? `<pre class="an-diff">${d.arbetstrad.split('\n').map((r) => `<span class="${r.startsWith('+') && !r.startsWith('+++') ? 'plus' : r.startsWith('-') && !r.startsWith('---') ? 'minus' : r.startsWith('@@') ? 'hunk' : ''}">${e_(r)}</span>`).join('\n')}</pre>` : '<p class="an-under">Inget.</p>'}`;
      if (!d) laddaDiff();
    } else if (T.flik === 'historik') {
      el.innerHTML = `<h2 class="an-h2">Redovisningen (ANDRINGAR.md)</h2>${l.redovisning ? `<pre class="an-text">${e_(l.redovisning)}</pre>` : '<p class="an-under">Ingen redovisad ändring än.</p>'}
        <h2 class="an-h2">Arbetskopians senaste commits</h2><ul class="an-lista">${(l.historik || []).map((h) => `<li><code>${e_(h.commit.slice(0, 8))}</code> ${e_(kort(h.tid))} ${e_(h.text)}</li>`).join('') || '<li>inga</li>'}</ul>
        <p class="an-under">Leverabel: ${e_(l.export?.id || 'okänd')}${l.export?.kalla === 'andring' ? ' (en kvitterad ändring)' : ''} · Förhandsvisning: ${e_(l.forhandsvisning?.commit ? String(l.forhandsvisning.commit).slice(0, 8) : 'ingen')} · Produktion: ${e_(l.produktion?.commit ? String(l.produktion.commit).slice(0, 8) : 'okänd')}</p>
        <p class="an-under">Förhandsvisningen och releasen görs under <a href="#/arbetsyta/${e_(encodeURIComponent(T.slug))}/flode">Bygge</a>, med ditt beslut. En senare export från sajten skriver aldrig över ändringarna; ta in dem i sajten när designarbetet ska fortsätta där.</p>
        <div class="an-rad"><button class="pt-knapp mjuk" type="button" data-an-ta-in>Ta in ändringarna i sajten</button></div>
        ${T.intag ? `<p class="an-under">Intaget: ${e_(T.intag.intaget.join(', ') || 'inget')}${T.intag.konflikter.length ? '. Konflikt (sajten har ändrats sedan exporten): ' + e_(T.intag.konflikter.join(', ')) : ''}${T.intag.genereras.length ? '. Genereras av exporten: ' + e_(T.intag.genereras.join(', ')) : ''}.</p>` : ''}`;
    } else {
      el.innerHTML = `<p class="an-under">Bifoga bilder och dokument till uppdraget. De sparas privat hos webbplatsen (inte i repot), och agenten läser dem därifrån.</p>
        <label class="an-slapp" id="an-slapp"><input type="file" id="an-fil" multiple accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml,application/pdf,text/plain"> Välj filer eller släpp dem här</label>
        <ul class="an-lista" id="an-bilagelista">${T.bilagor.map((b, i) => `<li><span>${e_(b.namn)}</span> <button class="pt-knapp mjuk" type="button" data-an-infoga="${i}">Infoga sökvägen i terminalen</button></li>`).join('')}</ul>`;
    }
  }
  async function laddaDiff() { try { T.diff = await hamta(api('/diff')); } catch (err) { T.diff = { finns: false, fel: err.message }; } if (T.flik === 'andringar') ritaPanel(); }

  // --- strömmen ---
  async function oppnaStrom() {
    stangStrom();
    const slug = T.slug;
    let b;
    try { b = await posta(api('/terminal'), { handling: 'biljett' }); } catch (err) { visaNotis('Terminalens ström kunde inte öppnas: ' + err.message); return; }
    if (slug !== T.slug) return;
    const es = new EventSource(api('/terminal') + '?biljett=' + encodeURIComponent(b.biljett) + '&fran=' + T.offset);
    T.es = es;
    es.addEventListener('ut', (ev) => {
      if (T.es !== es) return;
      let d; try { d = JSON.parse(ev.data); } catch { return; }
      if (d.sid !== T.sid) return;
      const bytes = Uint8Array.from(atob(d.d), (c) => c.charCodeAt(0));
      let start = 0;
      if (d.o > T.offset) { T.term?.reset(); }  // bufferten har släppt det äldsta: vyn ritas om från det som finns
      else if (d.o < T.offset) start = T.offset - d.o;  // redan skrivet
      if (start < bytes.length) T.term?.write(bytes.subarray(start));
      T.offset = d.o + bytes.length;
      T.ateranslut = 0;
    });
    es.addEventListener('slut', () => { if (T.es !== es) return; stangStrom(); T.term?.write('\r\n\x1b[2m[agenten har avslutats]\x1b[0m\r\n'); lasLage(); });
    es.addEventListener('ingen', () => { if (T.es === es) stangStrom(); });
    es.onerror = () => {
      if (T.es !== es || es.readyState !== EventSource.CLOSED) return;
      stangStrom();
      if (T.ateranslut++ < 20) setTimeout(() => { if (slug === T.slug && T.lage?.session?.lever) oppnaStrom(); }, 1500);
    };
  }
  function stangStrom() { if (T.es) { T.es.close(); T.es = null; } }

  // --- inmatningen ---
  // ett anrop åt gången: nästa skickas först när förra har svarat, så att tangenterna aldrig kommer i fel ordning
  async function skickaKo() {
    T.kotimer = null;
    if (T.skickar) return;
    T.skickar = true;
    try {
      while (T.ko && T.sid) {
        const data = T.ko; T.ko = '';
        try { await posta(api('/terminal'), { handling: 'in', sid: T.sid, klient: T.klient, data }); }
        catch (err) {
          T.ko = '';
          if (err.slag === 'Upptagen') visaNotis('En annan vy skriver i terminalen. Ta över inmatningen för att skriva här.');
          else if (err.status === 409) { visaNotis(err.message); lasLage(); }
          else visaNotis('Inmatningen nådde inte agenten: ' + err.message);
          break;
        }
      }
    } finally { T.skickar = false; }
  }
  async function skickaStorlek(cols, rows) {
    if (!T.sid || T.lage?.session?.agare !== T.klient) return;
    try { await posta(api('/terminal'), { handling: 'storlek', sid: T.sid, klient: T.klient, cols, rows }); } catch { /* nästa storlek försöker igen */ }
  }
  async function starta(ateruppta) {
    visaNotis(ateruppta ? 'Återupptar förra samtalet …' : 'Startar agenten …');
    try {
      const l = await posta(api('/terminal'), { handling: 'starta', klient: T.klient, ateruppta, cols: T.term?.cols || 120, rows: T.term?.rows || 34 });
      T.lage = l; T.sid = l.session?.sid; T.offset = 0; T.term?.reset(); visaNotis(null);
      oppnaStrom(); ritaHuvud(); T.term?.focus();
    } catch (err) { visaNotis('Agenten startade inte: ' + err.message); }
  }
  function synkChip(y) {
    if (!y?.origin) return '';
    const s = y.standardgren || 'main';
    const text = y.efter == null || y.fore == null ? 'Fjärren inte hämtad' : y.fore === 0 && y.efter === 0 ? `I takt med origin/${s}`
      : [y.efter ? `${y.efter} efter` : '', y.fore ? `${y.fore} före` : ''].filter(Boolean).join(', ') + ` origin/${s}`;
    const gren = y.pa_standardgren === false ? ` · gren ${y.gren}, inte ${s}` : '';
    return `<span class="an-chip${y.efter || y.pa_standardgren === false ? ' varn' : y.fore === 0 && y.efter === 0 ? ' ok' : ''}" title="${y.hamtad ? 'Senast hämtat ' + e_(kort(y.hamtad)) : 'Aldrig hämtat på den här datorn'}">${e_(text + gren)}</span>`;
  }
  function commitrad(c) { return `${c.commit} ${c.text}`; }
  function visaNotis(text) { const n = document.getElementById('an-notis'); if (!n) return; n.hidden = !text; n.textContent = text || ''; }

  function koppla(rot) {
    rot.addEventListener('click', async (ev) => {
      const t = ev.target.closest('button'); if (!t) return;
      const d = t.dataset;
      if (d.anFlik) { T.flik = d.anFlik; if (T.flik === 'andringar') T.diff = null; ritaPanel(); document.getElementById('an-tab-' + T.flik)?.focus(); return; }
      if (d.anBredd) { T.bredd = d.anBredd; ritaPanel(); return; }
      if (d.anLadda !== undefined) { const f = rot.querySelector('.an-scen iframe'); if (f) f.src = f.src; lasLage(); return; }
      if (d.anStarta !== undefined) { starta(false); return; }
      if (d.anAteruppta !== undefined) { starta(true); return; }
      if (d.anStoppa !== undefined) { T.stoppBekrafta = true; ritaHuvud(); document.querySelector('[data-an-stoppa-ja]')?.focus(); return; }
      if (d.anStoppaNej !== undefined) { T.stoppBekrafta = false; ritaHuvud(); document.querySelector('[data-an-stoppa]')?.focus(); return; }
      if (d.anStoppaJa !== undefined) {
        T.stoppBekrafta = false;
        try { await posta(api('/terminal'), { handling: 'stoppa', sid: T.sid, klient: T.klient }); visaNotis('Agenten är stoppad.'); } catch (err) { visaNotis('Stoppet gick inte: ' + err.message); }
        lasLage(); return;
      }
      if (d.anTaOver !== undefined) {
        try { await posta(api('/terminal'), { handling: 'ta_over', sid: T.sid, klient: T.klient }); visaNotis(null); await lasLage(); if (T.term) skickaStorlek(T.term.cols, T.term.rows); T.term?.focus(); }
        catch (err) { visaNotis('Det gick inte att ta över: ' + err.message); }
        return;
      }
      if (d.anKvittera !== undefined) {
        try {
          const r = await posta(api('/terminal'), { handling: 'kvittera' });
          const pu = !r.push ? ' Fjärrepot är inte bundet, så inget pushades.' : r.push.ok ? ' Commiten är pushad till kundrepot på GitHub (ingen publicering).' : ` Pushen gick inte: ${r.push.fel || 'okänt fel'}.`;
          visaNotis(`Ändringen är kvitterad (${r.export}). Förhandsvisa den under Bygge.${pu}`);
        } catch (err) { visaNotis('Ändringen kvitterades inte: ' + err.message); }
        lasLage(); return;
      }
      if (d.anHamta !== undefined) {
        visaNotis('Hämtar från fjärren …');
        try {
          const r = await postaVal({ handling: 'hamta', slug: T.slug }), f = r.fore, e = r.efter;
          const lage_ = (x) => x.efter == null ? 'okänt läge' : `${x.efter} efter och ${x.fore} före`;
          visaNotis(e.efter == null ? `Hämtat, men fjärren har ingen gren origin/${e.standardgren} att jämföra med.` : `Hämtat från origin/${e.standardgren}: före hämtningen ${lage_(f)}, nu ${lage_(e)}.`
            + (r.inkommande.length ? ` Nytt att ta in: ${r.inkommande.slice(0, 3).map(commitrad).join('; ')}${r.inkommande.length > 3 ? ' …' : ''}.` : ' Inget nytt på fjärren.')
            + (e.lokala ? ` Arbetskopian har ${e.lokala} lokala ändringar; uppdatera går när den är ren.` : ''));
        } catch (err) { visaNotis('Hämtningen gick inte: ' + err.message); }
        lasLage(); return;
      }
      if (d.anUppdatera !== undefined) {
        visaNotis('Uppdaterar bara framåt …');
        try {
          const r = await postaVal({ handling: 'uppdatera', slug: T.slug });
          visaNotis(r.andrat ? `Uppdaterad till origin/${r.efter.standardgren} (${r.commits.length} commits): ${r.commits.slice(0, 3).map(commitrad).join('; ')}${r.commits.length > 3 ? ' …' : ''}.` : r.text);
        } catch (err) { visaNotis('Ingen uppdatering: ' + err.message); }
        lasLage(); return;
      }
      if (d.anTaIn !== undefined) {
        try { T.intag = await posta(api('/terminal'), { handling: 'ta_in' }); visaNotis(`Intaget i sajten: ${T.intag.intaget.length} filer.`); } catch (err) { visaNotis('Ändringarna togs inte in: ' + err.message); }
        ritaPanel(); return;
      }
      if (d.anInfoga !== undefined) { const b = T.bilagor[Number(d.anInfoga)]; if (b && T.sid) { T.ko += b.sokvag + ' '; skickaKo(); T.term?.focus(); } return; }
    });
    rot.addEventListener('keydown', (ev) => {
      const f = ev.target.closest?.('[data-an-flik]'); if (!f || !['ArrowLeft', 'ArrowRight'].includes(ev.key)) return;
      const alla = ['forhand', 'andringar', 'historik', 'bilagor'], i = alla.indexOf(f.dataset.anFlik);
      T.flik = alla[(i + (ev.key === 'ArrowRight' ? 1 : 3)) % 4]; ritaPanel(); document.getElementById('an-tab-' + T.flik)?.focus(); ev.preventDefault();
    });
    rot.addEventListener('change', (ev) => { if (ev.target.id === 'an-fil') laddaUpp([...ev.target.files]); });
    rot.addEventListener('dragover', (ev) => { if (ev.target.closest?.('#an-slapp')) { ev.preventDefault(); ev.target.closest('#an-slapp').classList.add('over'); } });
    rot.addEventListener('dragleave', (ev) => { ev.target.closest?.('#an-slapp')?.classList.remove('over'); });
    rot.addEventListener('drop', (ev) => { const z = ev.target.closest?.('#an-slapp'); if (!z) return; ev.preventDefault(); z.classList.remove('over'); laddaUpp([...ev.dataTransfer.files]); });
  }
  async function laddaUpp(filer) {
    for (const f of filer.slice(0, 10)) {
      if (f.size > 20 * 1024 * 1024) { visaNotis(`${f.name} är större än 20 MB.`); continue; }
      const data = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(',')[1] || ''); r.readAsDataURL(f); });
      try { const b = await posta(api('/bilaga'), { namn: f.name, data }); T.bilagor.push(b); visaNotis(`${f.name} är bifogad: ${b.sokvag}`); }
      catch (err) { visaNotis(`${f.name} togs inte emot: ${err.message}`); }
    }
    if (T.flik === 'bilagor') ritaPanel();
  }
  // läget följs medan fliken är öppen (sessionens läge, skrivlåset och kontrollen), utan att terminalen ritas om
  setInterval(() => { if (T.slug && document.getElementById('an-rubrik') && !document.hidden) lasLage(); }, 5000);
  window.__andringar = T;  // för proven: vyns läge, aldrig något att skriva i
})();
