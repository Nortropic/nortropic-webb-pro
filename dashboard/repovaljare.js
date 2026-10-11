// Repoväljaren (ägarens tillägg 2026-10-11; kunskap/andringar.md, Repoväljaren): Nortropics kundrepon i en lista som VS
// Codes Quick Pick, öppnad med en knapp eller ⌘O, och valet öppnas i fliken Ändringar. Motorn (dashboard/repovaljare.py)
// hämtar listan, klonar, hämtar och uppdaterar; här finns ingen mappväljare, ingen sökvägsruta och ingen tokenruta.
(() => {
  const e_ = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const MAC = /Mac/.test(navigator.platform || '') || /Mac OS X/.test(navigator.userAgent || '');
  const GENVAG = MAC ? '⌘O' : 'Ctrl+Alt+O';
  const ARIA_GENVAG = MAC ? 'Meta+O' : 'Control+Alt+O';
  // sökningen bortser från skiftläge och diakritiska tecken (å, ä, ö som a och o); längden står kvar för förkomponerad text
  const norm = (s) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const S = { oppen: false, d: null, steg: 'lista', filter: '', aktiv: 0, synliga: [], valt: null, kund: null, lever: null, oppnare: null, arbetar: false, besked: null, gen: 0 };

  const klientId = () => { try { let k = sessionStorage.getItem('nwp-andringar-klient'); if (!k) { k = Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, '0')).join(''); sessionStorage.setItem('nwp-andringar-klient', k); } return k; } catch { return 'klient-' + Date.now(); } };
  async function hamta(url) {
    const r = await fetch(url, { cache: 'no-store' }); const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.fel || `HTTP ${r.status}`); return j;
  }
  async function posta(url, body) {
    let k = ''; try { k = localStorage.getItem('nwp-dashboardnyckel') || ''; } catch { /* i appen räcker sessionen */ }
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Nyckel': k }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.fel || `HTTP ${r.status}`); return j;
  }
  const aktuellSlug = () => (location.hash.match(/^#\/(?:andringar|kund|studio)\/([a-z0-9-]{2,60})/) || [])[1] || null;
  const datum = (t) => { if (!t) return ''; const d = new Date(t); return isNaN(d) ? '' : d.toLocaleDateString('sv-SE', { day: 'numeric', month: 'short', year: d.getFullYear() === new Date().getFullYear() ? undefined : 'numeric' }); };

  // --- raderna ---
  function lagetext(a) {
    if (!a?.finns) return null;
    const s = a.standardgren || 'main', delar = [];
    if (a.lokala) delar.push([`${a.lokala} lokala ändringar`, 'varn']);
    if (a.lage === 'ej hämtat') delar.push(['fjärren inte hämtad', '']);
    else if (a.fore === 0 && a.efter === 0) { if (!a.lokala) delar.push([`i takt med origin/${s}`, 'ok']); }
    else {
      if (a.efter) delar.push([`${a.efter} efter origin/${s}`, 'varn']);
      if (a.fore) delar.push([`${a.fore} före (inte pushat)`, '']);
    }
    return delar;
  }
  function repoPost(p, lever) {
    const kund = p.kund ? p.kund.namn : null;
    const chips = [];
    if (p.oppnas === 'oppna') {
      chips.push([`arbetskopia på ${p.arbetskopia.gren || '?'}${p.arbetskopia.pa_standardgren === false ? ` (inte ${p.arbetskopia.standardgren})` : ''}`, '']);
      chips.push(...(lagetext(p.arbetskopia) || []));
    } else if (p.oppnas === 'klona') chips.push(['ingen arbetskopia: klonas när du väljer det', '']);
    else if (p.oppnas === 'koppla') chips.push([p.forslag ? `inte kopplad till någon kund (namnförslag: ${p.forslag})` : 'inte kopplad till någon kund', 'varn']);
    else chips.push([`kan inte öppnas: ${p.kort || 'se skälet när du väljer det'}`, 'fel']);  // hela skälet står i beskedet vid valet
    if (lever) chips.push(['agenten lever', 'ok']);
    if (p.varning) chips.push([p.varning, 'fel']);
    if (p.privat === false) chips.push(['publikt repo', 'varn']);
    if (p.senast_push) chips.push([`senaste push ${datum(p.senast_push)}`, '']);
    return { typ: 'repo', id: 'r:' + p.namn, etikett: p.namn, beskrivning: kund || (p.oppnas === 'koppla' ? 'Inte kopplad' : ''), chips, data: p,
      sok: norm([p.namn, kund, p.kund?.slug, p.forslag].filter(Boolean).join(' ')) };
  }
  function grupper() {
    const d = S.d || { repon: [], senast: [], levande: [], kunder: [] };
    if (S.steg === 'koppla') {
      const kunder = [...d.kunder].sort((a, b) => (b.slug === S.valt.forslag) - (a.slug === S.valt.forslag) || a.namn.localeCompare(b.namn, 'sv'));
      return [['Befintliga kunder', kunder.map((k) => ({ typ: 'kund', id: 'k:' + k.slug, etikett: k.namn, beskrivning: k.slug,
        chips: k.slug === S.valt.forslag ? [['namnförslag ur repots namn: bekräfta själv', 'varn']] : [], data: k, sok: norm(k.namn + ' ' + k.slug) }))],
        ['Ingen av dem', [{ typ: 'nykund', id: 'ny', etikett: 'Ny kund', beskrivning: 'det vanliga flödet för en ny kund', chips: [], sok: norm('ny kund') }]]];
    }
    const lever = new Set((d.levande || []).map((x) => x.slug));
    const alla = d.repon.map((p) => repoPost(p, p.kund && lever.has(p.kund.slug)));
    const senast = (d.senast || []).map((x) => alla.find((r) => r.data.namn === x.repo)).filter(Boolean);
    const ovriga = alla.filter((r) => !senast.includes(r)).sort((a, b) => a.etikett.localeCompare(b.etikett, 'sv'));
    return [['Senast öppnade', senast], [`Kundrepon i ${d.org || 'Nortropic'}`, ovriga]];
  }
  function traffar(text) {
    const ord = norm(S.filter).split(/\s+/).filter(Boolean), n = norm(text);
    if (!ord.length || n.length !== String(text).length) return e_(text);
    const marke = new Array(n.length).fill(false);
    for (const w of ord) { let i = n.indexOf(w); while (i >= 0) { for (let j = i; j < i + w.length; j++) marke[j] = true; i = n.indexOf(w, i + w.length); } }
    let ut = '', i = 0;
    while (i < n.length) { let j = i; while (j < n.length && marke[j] === marke[i]) j++; const bit = e_(String(text).slice(i, j)); ut += marke[i] ? `<mark class="rv-traff">${bit}</mark>` : bit; i = j; }
    return ut;
  }

  // --- ritningen ---
  function rot() { return document.getElementById('rv'); }
  function rita() {
    const r = rot(); if (!r) return;
    const lista = S.steg === 'lista' || S.steg === 'koppla';
    r.querySelector('#rv-rubrik').textContent = S.steg === 'koppla' || S.steg === 'koppla_ja' ? `Koppla ${S.valt.namn} till en kund` : 'Öppna kundrepo';
    const sok = r.querySelector('#rv-sok');
    sok.hidden = !lista; sok.placeholder = S.steg === 'koppla' ? 'Sök bland kunderna' : 'Sök på repo eller kund';
    if (sok.value !== S.filter) sok.value = S.filter;
    const besked = r.querySelector('#rv-besked');
    besked.innerHTML = beskedHtml(); besked.hidden = !besked.innerHTML;
    const yta = r.querySelector('#rv-yta');
    if (!lista) {
      const hadeFokus = r.contains(document.activeElement);
      yta.innerHTML = stegHtml();
      // en knapp som ersätts tappar fokus till sidan: då fångar dialogen det igen, så att Esc och Tab fortsätter fungera
      if (hadeFokus && !r.contains(document.activeElement)) (r.querySelector('.rv-steg .pt-knapp:not([disabled])') || r).focus();
      for (const a of ['role', 'aria-label', 'tabindex', 'aria-activedescendant']) yta.removeAttribute(a);
      sok.setAttribute('aria-expanded', 'false'); sok.removeAttribute('aria-activedescendant');
      return;
    }
    const ord = norm(S.filter).split(/\s+/).filter(Boolean);
    S.synliga = [];
    let html = '';
    grupper().forEach(([namn, poster]) => {
      const syns = poster.filter((p) => ord.every((w) => p.sok.includes(w)));
      if (!syns.length) return;
      html += `<div role="group" aria-label="${e_(namn)}" class="rv-grupp"><div class="rv-grupprubrik" aria-hidden="true">${e_(namn)}</div>`;
      for (const p of syns) {
        const i = S.synliga.push(p) - 1;
        html += `<div role="option" id="rv-alt-${i}" class="rv-alt" data-i="${i}" aria-selected="false">
          <span class="rv-rad1"><span class="rv-etikett">${traffar(p.etikett)}</span>${p.beskrivning ? `<span class="rv-beskrivning">${traffar(p.beskrivning)}</span>` : ''}</span>
          ${p.chips.length ? `<span class="rv-rad2">${p.chips.map(([t, k]) => `<span class="rv-chip${k ? ' ' + k : ''}">${e_(t)}</span>`).join('')}</span>` : ''}</div>`;
      }
      html += '</div>';
    });
    if (!S.synliga.length) {  // en tom lista är ingen listruta: beskedet står som text
      yta.innerHTML = `<p class="rv-tomt">${S.d ? (S.filter ? `Inga ${S.steg === 'koppla' ? 'kunder' : 'kundrepon'} matchar ”${e_(S.filter)}”.` : S.steg === 'koppla' ? 'Det finns ingen befintlig kund att koppla till.' : 'Inga kundrepon att visa.') : 'Läser kundrepona …'}</p>`;
      for (const a of ['role', 'aria-label', 'tabindex', 'aria-activedescendant']) yta.removeAttribute(a);
      sok.setAttribute('aria-expanded', 'false'); sok.removeAttribute('aria-activedescendant');
      antal(0);
      return;
    }
    // listrutan går också att nå med Tab (pilarna och Enter fungerar där som i sökrutan)
    yta.innerHTML = html; yta.setAttribute('role', 'listbox'); yta.setAttribute('aria-label', S.steg === 'koppla' ? 'Kunder' : 'Kundrepon'); yta.tabIndex = 0;
    antal(S.synliga.length);
    sok.setAttribute('aria-expanded', 'true');
    S.aktiv = Math.max(0, Math.min(S.aktiv, S.synliga.length - 1));
    markera();
  }
  // antalet träffar läses upp (som VS Codes "{0} Results"), bara när det ändrats
  function antal(n) {
    const el = document.getElementById('rv-antal'); if (!el || S.d === null) return;
    const t = n === 1 ? '1 träff' : `${n} träffar`;
    if (el.textContent !== t) el.textContent = t;
  }
  function markera() {
    const r = rot(); if (!r) return;
    r.querySelectorAll('.rv-alt[aria-selected="true"]').forEach((el) => el.setAttribute('aria-selected', 'false'));
    const el = r.querySelector(`#rv-alt-${S.aktiv}`);
    for (const x of [r.querySelector('#rv-sok'), r.querySelector('#rv-yta[role="listbox"]')].filter(Boolean)) {
      if (el) x.setAttribute('aria-activedescendant', el.id); else x.removeAttribute('aria-activedescendant');
    }
    if (el) { el.setAttribute('aria-selected', 'true'); el.scrollIntoView({ block: 'nearest' }); }
  }
  function beskedHtml() {
    const d = S.d, ut = [];
    if (S.besked) ut.push(`<p class="rv-rad ${S.besked.slag || ''}">${e_(S.besked.text)}</p>`);
    if (d && d.inloggning && d.inloggning.slag !== 'ok' && S.steg === 'lista') {
      ut.push(`<div class="rv-rad fel"><b>${e_(d.inloggning.besked)}</b> ${e_(d.inloggning.atgard)}${d.repon.length ? ' Under tiden visas arbetskopiorna som redan finns på datorn.' : ''}</div>`);
    }
    if (S.arbetar) ut.push(`<p class="rv-rad">${e_(S.arbetar)}</p>`);
    return ut.join('');
  }
  function stegHtml() {
    const p = S.valt;
    if (S.steg === 'klona') {
      return `<div class="rv-steg" role="group" aria-labelledby="rv-steg-text"><p id="rv-steg-text"><b>${e_(p.namn)}</b> hör till <b>${e_(p.kund.namn)}</b> men har ingen arbetskopia på datorn.
        Repot klonas med din GitHub-inloggning till <code>kunder/${e_(p.kund.slug)}/kundrepo</code>, och sedan öppnas Ändringar.</p>
        <div class="rv-knappar"><button type="button" class="pt-knapp primar" data-rv-ja="klona"${S.arbetar ? ' disabled' : ''}>Klona och öppna</button><button type="button" class="pt-knapp" data-rv-tillbaka>Tillbaka</button></div></div>`;
    }
    if (S.steg === 'koppla_ja') {
      return `<div class="rv-steg" role="group" aria-labelledby="rv-steg-text"><p id="rv-steg-text">Koppla <b>${e_(p.namn)}</b> till <b>${e_(S.kund.namn)}</b> (${e_(S.kund.slug)})?
        Kundens kvitto får repots projekt-id, repot klonas till <code>kunder/${e_(S.kund.slug)}/kundrepo</code>, och Ändringar öppnas. Kopplingen gäller sedan i alla vyer.</p>
        <div class="rv-knappar"><button type="button" class="pt-knapp primar" data-rv-ja="koppla"${S.arbetar ? ' disabled' : ''}>Koppla, klona och öppna</button><button type="button" class="pt-knapp" data-rv-tillbaka>Tillbaka</button></div></div>`;
    }
    if (S.steg === 'byte') {
      const namn = (S.d.repon.find((r) => r.kund?.slug === S.lever.slug)?.kund?.namn) || S.lever.slug;
      return `<div class="rv-steg" role="group" aria-labelledby="rv-steg-text"><p id="rv-steg-text">Agenten för <b>${e_(namn)}</b> arbetar i terminalen. Vad ska hända med den när du öppnar ${e_(S.valt.kund?.namn || S.kund?.namn || S.valt.namn)}?</p>
        <ul class="rv-forklaring"><li>Stoppa: agentprocessen avslutas (ett pågående verktygsanrop avbryts; det som redan skrivits står kvar), och samtalet kan återupptas senare.</li>
        <li>Låt den arbeta: den fortsätter i bakgrunden i sitt eget repo, och du ser den när du öppnar ${e_(namn)} igen. Två agenter skriver aldrig i samma repo.</li></ul>
        <div class="rv-knappar"><button type="button" class="pt-knapp fara" data-rv-ja="stoppa"${S.arbetar ? ' disabled' : ''}>Stoppa agenten och öppna</button><button type="button" class="pt-knapp" data-rv-ja="bakgrund"${S.arbetar ? ' disabled' : ''}>Låt den arbeta och öppna</button><button type="button" class="pt-knapp" data-rv-tillbaka>Tillbaka</button></div></div>`;
    }
    return '';
  }

  // --- öppna, stänga och läsa ---
  async function las(lasOm) {
    const gen = ++S.gen;
    rot()?.setAttribute('aria-busy', 'true');  // listan läses om; den förra står kvar under tiden
    try {
      const d = lasOm ? await posta('/api/repovaljaren', { handling: 'las_om' }) : await hamta('/api/repovaljaren');
      if (gen !== S.gen) return;
      // "omläst" bara när GitHub svarade: annars står inloggningens besked ensamt
      S.d = d; S.besked = lasOm && d.inloggning?.slag === 'ok' ? { text: `Listan är omläst ${new Date().toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}.`, slag: 'ok' } : (lasOm ? null : S.besked);
    } catch (err) { if (gen === S.gen) S.besked = { text: 'Listan kunde inte läsas: ' + err.message, slag: 'fel' }; }
    if (gen === S.gen) rot()?.removeAttribute('aria-busy');
    if (S.oppen) rita();
  }
  function oppna() {
    if (S.oppen) { rot()?.querySelector('#rv-sok:not([hidden])')?.focus(); return; }
    S.instans = (S.instans || 0) + 1;
    Object.assign(S, { oppen: true, steg: 'lista', filter: '', aktiv: 0, valt: null, kund: null, lever: null, besked: null, arbetar: false, oppnare: document.activeElement });
    const wrap = document.createElement('div');
    wrap.id = 'rv-ram';
    wrap.innerHTML = `<div class="rv-bakgrund" data-rv-stang></div>
      <div class="rv" id="rv" role="dialog" aria-modal="true" aria-labelledby="rv-rubrik" tabindex="-1">
        <div class="rv-topp"><h2 id="rv-rubrik" class="rv-rubrik">Öppna kundrepo</h2><span class="rv-kalla">Nortropics kundrepon på GitHub</span></div>
        <input id="rv-sok" class="rv-sok" type="text" role="combobox" aria-expanded="true" aria-controls="rv-yta" aria-autocomplete="list" aria-label="Sök på repo eller kund" autocomplete="off" spellcheck="false">
        <div class="rv-besked" id="rv-besked" role="status" aria-live="polite"></div>
        <div class="pt-dold-text" id="rv-antal" aria-live="polite"></div>
        <div class="rv-yta" id="rv-yta"></div>
        <div class="rv-fot"><span class="rv-tangenter"><kbd>↑</kbd><kbd>↓</kbd> välj <kbd>Enter</kbd> öppna <kbd>Esc</kbd> stäng</span><button type="button" class="rv-lank" data-rv-las-om>Läs om listan</button></div>
      </div>`;
    document.body.appendChild(wrap);
    koppla(wrap);
    rita();
    wrap.querySelector('#rv-sok').focus();
    las(false);
  }
  function stang() {
    if (!S.oppen) return;
    S.oppen = false; S.gen++; S.instans = (S.instans || 0) + 1;
    document.getElementById('rv-ram')?.remove();
    const o = S.oppnare; S.oppnare = null;
    if (o && document.contains(o)) o.focus?.();
  }
  function tillbaka() {
    S.besked = null;
    if (S.steg === 'koppla_ja') { S.steg = 'koppla'; } else { S.steg = 'lista'; S.valt = null; S.kund = null; }
    S.filter = ''; S.aktiv = 0; rita(); rot()?.querySelector('#rv-sok')?.focus();
  }

  // --- valen ---
  async function valj(p) {
    if (!p) return;
    S.besked = null;
    if (p.typ === 'nykund') { stang(); location.hash = '#/ny-kund'; return; }
    if (p.typ === 'kund') { S.kund = p.data; return fortsatt('koppla_ja'); }
    const r = p.data;
    if (r.oppnas === 'nej') { S.besked = { text: `${r.namn} kan inte öppnas: ${r.skal}`, slag: 'fel' }; rita(); return; }
    S.valt = r;
    if (r.oppnas === 'koppla') { S.steg = 'koppla'; S.filter = ''; S.aktiv = 0; rita(); rot()?.querySelector('#rv-sok')?.focus(); return; }
    return fortsatt(r.oppnas === 'klona' ? 'klona' : null);
  }
  // byte medan en agent lever i den vy du lämnar: fråga först, sedan bekräftelsen för klon och koppling, sedan öppningen
  function fortsatt(steg, bytOk) {
    const mal = S.kund?.slug || S.valt?.kund?.slug, nu = aktuellSlug();
    const lever = (S.d?.levande || []).find((x) => x.slug === nu);
    if (!bytOk && lever && mal && mal !== nu) { S.lever = lever; S.efterByte = steg; S.steg = 'byte'; rita(); fokusSteg(); return; }
    if (steg) { S.steg = steg; rita(); fokusSteg(); return; }
    return gor({ handling: 'oppna', namn: S.valt.namn });
  }
  function fokusSteg() { rot()?.querySelector('.rv-steg .pt-knapp')?.focus(); }
  async function gor(body) {
    const instans = S.instans;  // ett svar som kommer efter att väljaren stängts eller öppnats om gäller inte längre
    S.arbetar = body.bekraftat ? (body.slug && S.steg === 'koppla_ja' ? 'Kopplar och klonar …' : 'Klonar repot …') : 'Öppnar …'; rita();
    try {
      const svar = await posta('/api/repovaljaren', body);
      if (!S.oppen || instans !== S.instans) return;
      S.arbetar = false;
      if (svar.vy) {
        if (S.d && svar.slug) S.d.senast = [{ repo: body.namn, slug: svar.slug }, ...(S.d.senast || []).filter((x) => x.repo !== body.namn && x.slug !== svar.slug)];
        stang();
        if (location.hash === svar.vy) window.dispatchEvent(new HashChangeEvent('hashchange')); else location.hash = svar.vy;
        return;
      }
      if (svar.bekrafta === 'klona') { S.steg = 'klona'; rita(); fokusSteg(); return; }
      if (svar.bekrafta === 'koppla') { S.steg = 'koppla'; rita(); return; }
    } catch (err) { S.arbetar = false; S.besked = { text: err.message, slag: 'fel' }; rita(); fokusSteg(); }
  }
  async function stoppaOchOppna() {
    const l = S.lever; S.arbetar = 'Stoppar agenten …'; rita();
    try {
      await posta(`/api/andringar/${encodeURIComponent(l.slug)}/terminal`, { handling: 'stoppa', sid: l.sid, klient: klientId() });
      for (let i = 0; i < 40; i++) {  // processkontrollen: vänta tills processen verkligen har avslutats
        const x = await hamta(`/api/andringar/${encodeURIComponent(l.slug)}`);
        if (!x.session?.lever) break;
        await new Promise((ok) => setTimeout(ok, 250));
      }
      S.d.levande = (S.d.levande || []).filter((x) => x.slug !== l.slug);
      S.arbetar = false; S.besked = { text: 'Agenten är stoppad; processen har avslutats.', slag: 'ok' };
      return fortsatt(S.efterByte, true);
    } catch (err) { S.arbetar = false; S.besked = { text: 'Agenten stoppades inte: ' + err.message, slag: 'fel' }; rita(); fokusSteg(); }
  }

  // --- händelserna ---
  function koppla(wrap) {
    wrap.addEventListener('click', (ev) => {
      if (ev.target.closest('[data-rv-stang]')) { stang(); return; }
      const alt = ev.target.closest('.rv-alt');
      if (alt) { S.aktiv = Number(alt.dataset.i); markera(); valj(S.synliga[S.aktiv]); return; }
      const b = ev.target.closest('button'); if (!b) return;
      if (b.dataset.rvLasOm !== undefined) { las(true); return; }
      if (b.dataset.rvTillbaka !== undefined) { tillbaka(); return; }
      const ja = b.dataset.rvJa;
      if (ja === 'klona') gor({ handling: 'oppna', namn: S.valt.namn, slug: S.valt.kund.slug, bekraftat: true });
      else if (ja === 'koppla') gor({ handling: 'oppna', namn: S.valt.namn, slug: S.kund.slug, bekraftat: true });
      else if (ja === 'stoppa') stoppaOchOppna();
      else if (ja === 'bakgrund') fortsatt(S.efterByte, true);
    });
    wrap.addEventListener('mousemove', (ev) => {
      const alt = ev.target.closest('.rv-alt'); if (!alt || Number(alt.dataset.i) === S.aktiv) return;
      S.aktiv = Number(alt.dataset.i); markera();
    });
    wrap.addEventListener('input', (ev) => { if (ev.target.id === 'rv-sok') { S.filter = ev.target.value; S.aktiv = 0; S.besked = null; rita(); } });
    wrap.addEventListener('keydown', (ev) => {
      const n = S.synliga.length;
      const lista = S.steg === 'lista' || S.steg === 'koppla';
      if (ev.key === 'Escape') { ev.preventDefault(); if (S.steg === 'lista') stang(); else tillbaka(); return; }
      if (ev.key === 'Tab') {  // fokus stannar i dialogen
        const f = [...rot().querySelectorAll('input:not([hidden]), #rv-yta[tabindex="0"], button:not([disabled])')];
        const i = f.indexOf(document.activeElement);
        if (ev.shiftKey && i <= 0) { f[f.length - 1]?.focus(); ev.preventDefault(); } else if (!ev.shiftKey && i === f.length - 1) { f[0]?.focus(); ev.preventDefault(); }
        return;
      }
      if (!lista || !['rv-sok', 'rv-yta'].includes(ev.target.id)) return;
      if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') { if (n) { S.aktiv = (S.aktiv + (ev.key === 'ArrowDown' ? 1 : n - 1)) % n; markera(); } ev.preventDefault(); }
      else if (ev.key === 'PageDown' || ev.key === 'PageUp') { if (n) { S.aktiv = Math.max(0, Math.min(n - 1, S.aktiv + (ev.key === 'PageDown' ? 8 : -8))); markera(); } ev.preventDefault(); }
      else if ((ev.key === 'Home' || ev.key === 'End') && (ev.ctrlKey || ev.metaKey)) { if (n) { S.aktiv = ev.key === 'Home' ? 0 : n - 1; markera(); } ev.preventDefault(); }  // vanliga Home/End flyttar i texten
      else if (ev.key === 'Enter') { ev.preventDefault(); valj(S.synliga[S.aktiv]); }
    });
  }
  // genvägen fångas före terminalen (xterm), så att den aldrig når agenten
  window.addEventListener('keydown', (ev) => {
    const traff = ev.code === 'KeyO' && (MAC ? ev.metaKey && !ev.ctrlKey && !ev.altKey && !ev.shiftKey : ev.ctrlKey && ev.altKey && !ev.metaKey && !ev.shiftKey);
    if (!traff) return;
    ev.preventDefault(); ev.stopPropagation();
    oppna();
  }, true);
  document.addEventListener('click', (ev) => { if (ev.target.closest?.('[data-rv-oppna]')) { ev.preventDefault(); oppna(); } });
  window.repovaljaren = { oppna, stang, genvag: GENVAG, ariaGenvag: ARIA_GENVAG, knapp: (text = 'Öppna kundrepo', klass = 'pt-knapp') =>
    `<button type="button" class="${klass} rv-oppna" data-rv-oppna aria-keyshortcuts="${ARIA_GENVAG}">${e_(text)}<kbd class="rv-kbd">${GENVAG}</kbd></button>`, __S: S };
})();
