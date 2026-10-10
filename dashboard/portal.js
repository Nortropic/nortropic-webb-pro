// Portalen (kunskap/desktop.md, Portalen): ramen med mörk navigering, sök och kundens arbetsområden runt alla vyer, och
// portalens egna vyer: Hem (Ny kund, Kunder, Testkunder, fortsättning och uppmärksamhet), kundlistorna, kundens sida och
// den minsta vägen till ett nytt ärende. Samma frontend i Nortropic.app och i webbläsaren. Datan räknas fram av motorn ur
// befintliga källor (GET /api/desktop/oversikt: arbetsytans projekt, Kundstarts ärenden, flödets kundlägen, körregistret).
// Inget här startar en modell, ett bygge eller en leverantörsresurs; arbetsområdena leder till de befintliga vyerna.
(() => {
  'use strict';
  const e_ = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const EGNA = ['start', 'kunder', 'testkunder', 'ny-kund', 'ny-testkund', 'kund', 'intervju', 'leverans-kund', 'granska'];
  const P = { data: null, lastes: 0, desktop: null, filter: 'alla', sok: '', gen: 0, vgen: 0 };
  const IKON = {
    hem: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    kunder: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.6 3.3-5.5 6.5-5.5s5.9 1.9 6.5 5.5"/><circle cx="17" cy="9" r="2.6"/><path d="M16 14.6c2.8.1 4.9 1.8 5.5 4.9"/>',
    ny: '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    test: '<path d="M9 3h6M10 3v6l-5.5 9.5A1.6 1.6 0 0 0 5.9 21h12.2a1.6 1.6 0 0 0 1.4-2.5L14 9V3"/><path d="M7.5 15h9"/>',
    arbetsyta: '<rect x="3" y="4" width="18" height="14" rx="2"/><path d="M9 4v14M3 20h18"/>',
    system: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    las: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    sok: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  };
  const ikon = (n) => `<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${IKON[n]}</svg>`;

  async function hamta(url) {
    const r = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store' });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.fel || ('HTTP ' + r.status));
    return j;
  }
  async function skicka(url, body) {
    let k = ''; try { k = localStorage.getItem('nwp-dashboardnyckel') || ''; } catch { /* i appen räcker sessionen */ }
    const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Nyckel': k }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) { const f = new Error(j.fel || ('HTTP ' + r.status)); f.status = r.status; f.svar = j; throw f; }
    return j;
  }
  async function desktopLage() {
    if (P.desktop) return P.desktop;
    try { P.desktop = await hamta('/api/desktop/lage'); } catch { P.desktop = { session: false }; }
    if (P.desktop.session) document.documentElement.classList.add('i-appen');
    return P.desktop;
  }
  async function data(farsk) {
    if (!farsk && P.data && Date.now() - P.lastes < 8000) return P.data;
    const gen = ++P.gen;
    const d = await hamta('/api/desktop/oversikt');
    if (gen === P.gen) { P.data = d; P.lastes = Date.now(); }
    return d;
  }
  const tid = (iso) => {
    if (!iso) return 'okänd tid';
    const t = typeof iso === 'number' ? new Date(iso * 1000) : new Date(iso);
    if (isNaN(t)) return String(iso);
    const s = (Date.now() - t.getTime()) / 1000;
    if (s < 90) return 'nyss'; if (s < 3600) return Math.round(s / 60) + ' min sedan'; if (s < 86400) return Math.round(s / 3600) + ' tim sedan';
    return t.toLocaleDateString('sv-SE', { day: 'numeric', month: 'short' });
  };
  const initialer = (n) => String(n || '?').replace(/\(.*?\)/g, '').trim().split(/\s+/).slice(0, 2).map((x) => x[0] || '').join('').toUpperCase() || '?';

  // --- kundens arbetsområden: begripliga namn mappade till befintliga steg och vyer (ingen ny statusmaskin) ---
  function omraden(k) {
    const s = encodeURIComponent(k.slug), a = (k.arenden || [])[0];
    const ks = a ? '#/kundstart/' + encodeURIComponent(a.id) : null, p = k.projekt ? '#/arbetsyta/' + s : null;
    return [
      ['kundstart', 'Kundstart', a ? '#/intervju/' + encodeURIComponent(a.id) : null, 'intervjun: samtalet och det växande underlaget', null],
      ['underlag', 'Underlag', ks, 'källbundna uppgifter och material', 'underlag'],
      ['funktioner', 'Funktioner', ks, 'K01–K18: behov, val och plan', 'funktioner'],
      ['forslag', 'Förslag', p && p + '/forslag', 'skisserna och dina val', null],
      ['forfining', 'Förfining', p && '#/granska/' + s, 'kommentera den bevarade bilden och samla till ett uppdrag', null],
      ['bygge', 'Bygge', p && p + '/flode', 'helbygget och sessionerna', null],
      ['granskning', 'Granskning', p && p + '/kod', 'förhandsvisning, kod och kontroller', null],
      ['leverans', 'Leverans', '#/leverans-kund/' + s, 'publicering genom Cloudflare-vägen och leveransbeskedet', 'publicering'],
      ['forvaltning', 'Förvaltning', '#/leverans-kund/' + s, 'drift, ändringar och tillval', 'forvaltning'],
    ];
  }
  function aktivtOmrade(h) {
    if (h.startsWith('intervju/')) return 'kundstart';
    if (h.startsWith('kundstart/')) { try { return sessionStorage.getItem('nwp-portal:omrade') || 'kundstart'; } catch { return 'kundstart'; } }
    if (/^arbetsyta\/[^/]+\/forslag/.test(h)) return 'forslag';
    if (/^arbetsyta\/[^/]+\/flode/.test(h)) return 'bygge';
    if (/^arbetsyta\/[^/]+\/kod/.test(h)) return 'granskning';
    if (/^arbetsyta\/[^/]+/.test(h) || h.startsWith('granska/')) return 'forfining';
    if (h === 'leverans') return 'leverans';
    if (h.startsWith('leverans-kund/')) { try { return sessionStorage.getItem('nwp-portal:omrade') === 'forvaltning' ? 'forvaltning' : 'leverans'; } catch { return 'leverans'; } }
    return null;
  }
  function kundFor(h, d) {
    if (!d) return null;
    let m = h.match(/^(?:arbetsyta|kund|bygge|leverans-kund|granska)\/([^/]+)/);
    if (m) return d.kunder.find((k) => k.slug === decodeURIComponent(m[1])) || null;
    m = h.match(/^(?:kundstart|intervju)\/([a-f0-9]{32})/);
    if (m) return d.kunder.find((k) => (k.arenden || []).some((a) => a.id === m[1])) || null;
    if (h === 'leverans') { let s = ''; try { s = localStorage.getItem('nwp-portal:kund') || ''; } catch { /* */ } return d.kunder.find((k) => k.slug === s) || null; }
    return null;
  }

  // --- ramen ---
  function navlank(href, text, ik, aktiv, id) { return `<a href="${href}"${aktiv === id ? ' aria-current="page"' : ''}>${ikon(ik)}<span>${text}</span></a>`; }
  function ritaRam(h) {
    const aktiv = h === '' || h === 'start' ? 'start' : h.startsWith('ny-') ? 'ny-kund' : h.startsWith('testkunder') ? 'testkunder'
      : h.startsWith('kunder') || h.startsWith('kund/') || h.startsWith('kundstart') ? 'kunder' : h.startsWith('arbetsyta') ? 'arbetsyta'
      : ['underhall', 'kirurgen', 'backlog', 'kalibrering', 'lardomar', 'designprov'].includes(h.split('/')[0]) ? 'system' : null;
    let nav = document.getElementById('pt-nav');
    if (!nav) {
      nav = document.createElement('nav'); nav.id = 'pt-nav'; nav.className = 'pt-nav'; nav.setAttribute('aria-label', 'Nortropic');
      const topp = document.createElement('div'); topp.id = 'pt-topp'; topp.className = 'pt-topp';
      const steg = document.createElement('div'); steg.id = 'pt-steg';
      const rot = document.getElementById('rot');
      document.body.insertBefore(nav, rot); document.body.insertBefore(topp, rot); document.body.insertBefore(steg, rot);
      topp.innerHTML = `<form class="pt-sok" role="search" id="pt-sokform"><label for="pt-sokfalt" class="pt-dold-text">Sök kunder</label>${ikon('sok')}
          <input id="pt-sokfalt" type="search" placeholder="Sök kunder" autocomplete="off" list="pt-soklista"><datalist id="pt-soklista"></datalist></form>
        <div class="pt-toppstatus" id="pt-toppstatus"></div>`;
      document.getElementById('pt-sokform').addEventListener('submit', (e) => {
        e.preventDefault(); const q = document.getElementById('pt-sokfalt').value.trim(); P.sok = q;
        const k = (P.data?.kunder || []).find((x) => (x.namn || x.slug) === q || x.slug === q);
        location.hash = k ? '#/kund/' + encodeURIComponent(k.slug) : (k?.test ? '#/testkunder' : '#/kunder');
      });
    }
    nav.innerHTML = `<a class="pt-marke" href="#/start"><span>Nortropic</span></a>
      <div class="pt-grupp">${navlank('#/start', 'Hem', 'hem', aktiv, 'start')}${navlank('#/kunder', 'Kunder', 'kunder', aktiv, 'kunder')}${navlank('#/ny-kund', 'Ny kund', 'ny', aktiv, 'ny-kund')}${navlank('#/testkunder', 'Testkunder', 'test', aktiv, 'testkunder')}</div>
      <div class="pt-grupp">${navlank('#/arbetsyta', 'Arbetsytan', 'arbetsyta', aktiv, 'arbetsyta')}${navlank('#/underhall', 'Systemförbättring', 'system', aktiv, 'system')}</div>
      ${P.desktop?.session ? `<div class="pt-grupp pt-sist"><button type="button" class="pt-las" id="pt-las">${ikon('las')}<span>Lås Nortropic</span></button></div>` : ''}`;
    document.getElementById('pt-las')?.addEventListener('click', lasAppen);
    document.getElementById('pt-toppstatus').innerHTML = P.desktop?.session ? '<span class="pt-chip ok">Upplåst i Nortropic.app</span>' : '<span class="pt-chip">Webbläsaren</span>';
    ritaSteg(h);
  }
  function ritaSteg(h) {
    const el = document.getElementById('pt-steg'); if (!el) return;
    const k = kundFor(h, P.data);
    if (!k) { el.innerHTML = ''; el.className = ''; return; }
    try { localStorage.setItem('nwp-portal:kund', k.slug); } catch { /* bekvämlighet */ }
    const akt = aktivtOmrade(h);
    el.className = 'pt-steg';
    el.innerHTML = `<div class="pt-steg-kund"><a href="#/kund/${encodeURIComponent(k.slug)}">${e_(k.namn || k.slug)}</a>${k.test ? ' <span class="pt-test">Testkund</span>' : ''}</div>
      <ol class="pt-stegrad" aria-label="Kundens arbetsområden">${omraden(k).map(([id, namn, href, om, del], i) => `<li${akt === id ? ' class="aktiv"' : ''}>${href
        ? `<a href="${href}" data-omrade="${id}" data-del="${del || ''}" title="${e_(om)}"${akt === id ? ' aria-current="step"' : ''}><i>${i + 1}</i><span>${namn}</span></a>`
        : `<span class="pt-ej" title="${e_(om)}: inte påbörjat för kunden"><i>${i + 1}</i><span>${namn}</span></span>`}</li>`).join('')}</ol>`;
    el.querySelectorAll('[data-omrade]').forEach((a) => a.addEventListener('click', () => { try { sessionStorage.setItem('nwp-portal:omrade', a.dataset.omrade); sessionStorage.setItem('nwp-portal:del', a.dataset.del); } catch { /* */ } }));
  }
  async function lasAppen() {
    try { await skicka('/api/desktop/utloggning', {}); } catch { /* sessionen kan redan vara borta */ }
    location.href = '/desktop/last';  // Nortropic.app fångar adressen och visar sitt lås; webbläsaren får en utloggad sida
  }

  // Varje route går hit först: ramen ritas i appen alltid och i webbläsaren bara för portalens egna vyer, så att
  // arbetsytan i webbläsaren ser ut som förut.
  window.portalSkal = async function portalSkal(h) {
    const d = await desktopLage();
    const egen = EGNA.includes(String(h).split('/')[0]) || (h === '' && d.session);
    const visa = d.session || egen;
    document.documentElement.classList.toggle('pt-ram', visa);
    if (!visa) { ['pt-nav', 'pt-topp', 'pt-steg'].forEach((id) => document.getElementById(id)?.remove()); return false; }
    if (!P.data) { try { await data(); } catch { /* listan saknas; ramen ritas ändå */ } }
    ritaRam(h);
    const lista = document.getElementById('pt-soklista');
    if (lista && P.data) lista.innerHTML = P.data.kunder.map((k) => `<option value="${e_(k.namn || k.slug)}"></option>`).join('');
    return egen;
  };
  // Efter att en befintlig vy ritats: skrolla till den del av Kundstart som arbetsområdet pekade på.
  window.portalEfter = function portalEfter(h) {
    if (!h.startsWith('kundstart/')) return;
    let del = ''; try { del = sessionStorage.getItem('nwp-portal:del') || ''; sessionStorage.removeItem('nwp-portal:del'); } catch { /* */ }
    if (!del) return;
    const rubrik = [...document.querySelectorAll('#vy h2, #vy h3, #vy summary')].find((x) => x.textContent.toLowerCase().includes(del === 'funktioner' ? 'funktioner' : 'underlag'));
    rubrik?.scrollIntoView({ block: 'start' });
  };

  function kundkort(k) {
    const et = [];
    if (k.test) et.push('<span class="pt-test">Testkund</span>');
    if ((k.arenden || []).length) et.push('<span class="pt-etikett">Kundstart</span>');
    if (k.projekt) et.push('<span class="pt-etikett">Skapandeflödet</span>');
    if (k.blind) et.push('<span class="pt-etikett">blind jämförelse</span>');
    return `<li><a class="pt-kund" href="${e_(k.vy)}" data-kund="${e_(k.slug)}">
      <span class="pt-avatar" aria-hidden="true">${e_(initialer(k.namn || k.slug))}</span>
      <span class="pt-kund-text"><span class="pt-kund-namn">${e_(k.namn || k.slug)}</span><span class="pt-kund-nasta">${e_(k.nasta || 'Ingen handling väntar')}</span>
        <span class="pt-kund-meta">${et.join(' ')}</span></span>
      <span class="pt-kund-tid">${e_(tid(k.senast))}</span></a></li>`;
  }

  function senast() { try { return localStorage.getItem('nwp-arbetsyta:senaste') || localStorage.getItem('nwp-portal:kund') || ''; } catch { return ''; } }
  function yta(html) { const v = document.getElementById('rot'); v.innerHTML = `<main class="pt-yta" id="vy" tabindex="-1">${html}</main>`; }
  function fokus() { const h = document.querySelector('#vy h1'); if (h) { h.tabIndex = -1; h.focus({ preventScroll: true }); } }

  async function startvy() {
    yta('<p class="pt-under">Läser kunderna …</p>');
    let d; try { d = await data(true); } catch (e) { return fel(e); }
    const riktiga = d.kunder.filter((k) => !k.test), test = d.kunder.filter((k) => k.test);
    const fort = [d.kunder.find((k) => k.slug === senast()), ...d.kunder].filter(Boolean).filter((k, i, a) => a.indexOf(k) === i).slice(0, 3);
    const upp = d.uppmarksamhet.filter((u) => !u.test), testUpp = d.uppmarksamhet.filter((u) => u.test);
    yta(`<h1>Välkommen</h1><p class="pt-ingress">Vad vill du göra idag?</p>
      <div class="pt-primara">
        <a class="pt-primar" href="#/ny-kund"><span class="pt-p-ikon">${ikon('ny')}</span><span class="pt-p-titel">Ny kund</span><span class="pt-p-text">Börja med namnet, webbplatsen om den finns och vad de söker hjälp med.</span><span class="pt-knapp mjuk">Starta ny kund</span></a>
        <a class="pt-primar" href="#/kunder"><span class="pt-p-ikon gron">${ikon('kunder')}</span><span class="pt-p-titel">Kunder <b>${riktiga.length}</b></span><span class="pt-p-text">Påbörjade intervjuer, kunder i skapandeflödet och levererade sajter.</span><span class="pt-knapp mjuk">Visa kunder</span></a>
        <a class="pt-primar" href="#/testkunder"><span class="pt-p-ikon lila">${ikon('test')}</span><span class="pt-p-titel">Testkunder <b>${test.length}</b></span><span class="pt-p-text">Fiktiva kunder för att prova flödet, skilda från riktiga kunder.</span><span class="pt-knapp mjuk">Öppna testkunder</span></a>
      </div>
      <div class="pt-tva">
        <section class="pt-panel" aria-labelledby="pt-fort"><h2 id="pt-fort">Fortsätt där du slutade</h2>
          ${fort.length ? `<ul class="pt-kunder">${fort.map(kundkort).join('')}</ul>` : `<p class="pt-tomt">Inga kunder än. Börja med <a href="#/ny-kund">Ny kund</a> eller prova flödet med en <a href="#/ny-testkund">testkund</a>.</p>`}</section>
        <section class="pt-panel" aria-labelledby="pt-upp"><h2 id="pt-upp">Behöver din uppmärksamhet</h2>
          ${upp.length ? `<ul class="pt-kunder">${upp.map((u) => { const k = d.kunder.find((x) => x.slug === u.slug); return k ? kundkort({ ...k, nasta: 'Väntar på dig: ' + u.vad.join(', ') }) : ''; }).join('')}</ul>`
          : '<p class="pt-tomt">Inget hos riktiga kunder väntar på ditt beslut just nu.</p>'}
          ${testUpp.length ? `<p class="pt-under">Dessutom ${testUpp.length} testkund${testUpp.length > 1 ? 'er' : ''} (<a href="#/testkunder">Testkunder</a>).</p>` : ''}</section>
      </div>
      ${d.pagaende.length ? `<section class="pt-panel" aria-labelledby="pt-pag"><h2 id="pt-pag">Pågår i motorn</h2><ul class="pt-lista">${d.pagaende.map((p) => `<li><a href="#/arbetsyta/${encodeURIComponent(p.slug || '')}">${e_(p.slug || 'okänd kund')}</a> <span>${e_(p.vad)}, pid ${e_(p.pid)}</span></li>`).join('')}</ul></section>` : ''}
      ${d.kundstart_fel ? `<p class="pt-fel" role="alert">Kundstarts ärenden kunde inte läsas: ${e_(d.kundstart_fel)}</p>` : ''}
      <p class="pt-under pt-fot">Läst ${e_(tid(d.tid))} ur motorn. Listorna räknas fram ur arbetsytan, Kundstart och flödet; ingen modell körs för att visa dem.</p>`);
    fokus();
  }

  const FILTER = [['alla', 'Alla'], ['vantar', 'Väntar på dig'], ['intervju', 'Påbörjade intervjuer'], ['flode', 'I skapandeflödet'], ['pagar', 'Pågår']];
  function matchar(k) {
    const f = P.filter;
    if (f === 'vantar' && !(k.vantar || []).length) return false;
    if (f === 'intervju' && !((k.arenden || []).length && !k.projekt)) return false;
    if (f === 'flode' && !k.projekt) return false;
    if (f === 'pagar' && !(k.pagar || []).length) return false;
    const s = P.sok.trim().toLocaleLowerCase('sv');
    return !s || (k.namn || '').toLocaleLowerCase('sv').includes(s) || k.slug.includes(s);
  }
  async function listvy(test) {
    yta('<p class="pt-under">Läser kunderna …</p>');
    let d; try { d = await data(); } catch (e) { return fel(e); }
    const alla = d.kunder.filter((k) => Boolean(k.test) === test);
    yta(`<div class="pt-rubrikrad"><h1>${test ? 'Testkunder' : 'Kunder'}</h1><a class="pt-knapp primar" href="${test ? '#/ny-testkund' : '#/ny-kund'}">${test ? 'Skapa testkund' : 'Ny kund'}</a></div>
      ${test ? '<p class="pt-ingress">Fiktiva kunder, märkta i motorn hela vägen: ingen GitHub-remote, ingen skarp release, aktiveringen bara som torrkörning. De räknas aldrig bland riktiga kunder.</p>' : '<p class="pt-ingress">Alla riktiga kunder, också påbörjade intervjuer. Ett öppnande tar dig dit arbetet står; det startar inget.</p>'}
      <div class="pt-verktyg"><label class="pt-filtersok"><span class="pt-dold-text">Filtrera på namn</span><input type="search" id="pt-filtersok" placeholder="Filtrera på namn" value="${e_(P.sok)}" autocomplete="off"></label>
        <div class="pt-filter" role="group" aria-label="Urval">${FILTER.map(([k, n]) => `<button type="button" data-filter="${k}" aria-pressed="${P.filter === k}">${n}</button>`).join('')}</div></div>
      <p class="pt-under" id="pt-antal" role="status" aria-live="polite"></p>
      <ul class="pt-kunder pt-lista-stor" id="pt-lista"></ul>`);
    const rita = () => {
      const urval = alla.filter(matchar);
      document.getElementById('pt-lista').innerHTML = urval.map(kundkort).join('') || `<li class="pt-tomt">${alla.length ? 'Ingen kund matchar urvalet.' : test ? 'Inga testkunder än. Skapa en för att prova flödet.' : 'Inga kunder än. Börja med Ny kund.'}</li>`;
      document.getElementById('pt-antal').textContent = `${urval.length} av ${alla.length} ${test ? 'testkunder' : 'kunder'}`;
    };
    document.getElementById('pt-filtersok').addEventListener('input', (e) => { P.sok = e.target.value; rita(); });
    document.querySelectorAll('[data-filter]').forEach((b) => b.addEventListener('click', () => {
      P.filter = b.dataset.filter; document.querySelectorAll('[data-filter]').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); rita();
    }));
    rita(); fokus();
  }

  // Kundens sida: företagets identitet, uppdragen (Kundstarts ärenden och skapandeflödet) och arbetsområdena. Samma kund
  // får senare tillägg här (funktioner i det befintliga ärendet), aldrig en ny dubblettkund.
  async function kundvy(slug) {
    yta('<p class="pt-under">Läser kunden …</p>');
    let d; try { d = await data(true); } catch (e) { return fel(e); }
    const k = d.kunder.find((x) => x.slug === slug);
    if (!k) { yta(`<h1>Kunden finns inte</h1><p class="pt-tomt">Ingen kund med adressen ${e_(slug)} finns i motorn, eller så är den gallrad. <a href="#/kunder">Till kunderna</a></p>`); return fokus(); }
    ritaSteg('kund/' + slug);
    yta(`<div class="pt-rubrikrad"><h1>${e_(k.namn || k.slug)}</h1>${k.test ? '<span class="pt-test">Testkund</span>' : ''}</div>
      <p class="pt-ingress">${e_(k.nasta || 'Ingen handling väntar just nu.')}</p>
      <div class="pt-tva">
        <section class="pt-panel"><h2>Uppdrag</h2><ul class="pt-lista">
          ${(k.arenden || []).map((a) => `<li><a href="#/kundstart/${encodeURIComponent(a.id)}">Kundstart</a> <span>${a.aktuell_bestallning ? 'omfattningen accepterad' : 'intervju och underlag'} · uppdaterad ${e_(tid(a.uppdaterad))}${a.fragor ? ' · ' + a.fragor + ' frågor att följa upp' : ''}</span></li>`).join('')}
          ${k.projekt ? `<li><a href="#/arbetsyta/${encodeURIComponent(k.slug)}">Skapandeflödet</a> <span>senast aktivt ${e_(tid(k.projekt.senast_andrad))}${(k.pagar || []).length ? ' · pågår: ' + e_(k.pagar.join(', ')) : ''}</span></li>` : ''}
          ${!(k.arenden || []).length && !k.projekt ? '<li class="pt-tomt">Inga uppdrag.</li>' : ''}</ul></section>
        <section class="pt-panel"><h2>Väntar på dig</h2>${(k.vantar || []).length ? `<ul class="pt-lista">${k.vantar.map((v) => `<li>${e_(v)}</li>`).join('')}</ul>` : '<p class="pt-tomt">Inget beslut väntar.</p>'}
          <h2>Senare tillägg</h2><p class="pt-under">En ny funktion eller ändring för samma kund görs i kundens befintliga ärende (Funktioner) och får en egen konsekvensplan; ingen ny kund skapas.</p>
          ${(k.arenden || [])[0] ? `<a class="pt-knapp" href="#/kundstart/${encodeURIComponent(k.arenden[0].id)}" data-omrade="funktioner" data-del="funktioner">Öppna Funktioner</a>` : ''}</section>
      </div>`);
    document.querySelectorAll('#vy [data-omrade]').forEach((a) => a.addEventListener('click', () => { try { sessionStorage.setItem('nwp-portal:omrade', 'funktioner'); sessionStorage.setItem('nwp-portal:del', 'funktioner'); } catch { /* */ } }));
    fokus();
  }

  // Ny kund: minsta möjliga ärende. Samma operations-id följer ett dubbelklick, ett omförsök och en andra flik i samma
  // session, så att två klick aldrig blir två kunder; utkastet står kvar tills ärendet finns.
  function nykundvy(test) {
    const id = test ? 'ny-testkund' : 'ny-kund', lagring = 'nwp-portal:' + id;
    let u = {}; try { u = JSON.parse(localStorage.getItem(lagring) || '{}'); } catch { u = {}; }
    yta(`<h1>${test ? 'Skapa testkund' : 'Ny kund'}</h1>
      <p class="pt-ingress">${test ? 'En fiktiv kund för att prova flödet. Den märks som test i motorn, inte av något du skriver.' : 'Låt oss komma igång. Fyll i det grundläggande så tar intervjun över.'}</p>
      <div class="pt-tva pt-tva-form">
        <form id="pt-form" class="pt-panel pt-form" novalidate>
          <label for="pt-foretag">Företagets namn eller arbetsnamn</label>
          <input id="pt-foretag" name="foretag" required maxlength="120" autocomplete="off" value="${e_(u.foretag || '')}" aria-describedby="pt-foretag-fel" placeholder="${test ? 'Exempel: Provbageriet (test)' : ''}">
          <p id="pt-foretag-fel" class="pt-fel" hidden></p>
          <label for="pt-webb">Befintlig webbplats <span class="pt-valfri">(valfritt)</span></label>
          <input id="pt-webb" name="webbplats" type="url" inputmode="url" maxlength="300" placeholder="https://" value="${e_(u.webbplats || '')}" aria-describedby="pt-webb-fel">
          <p id="pt-webb-fel" class="pt-fel" hidden></p>
          <label for="pt-syfte">Vad vill kunden ha hjälp med?</label>
          <textarea id="pt-syfte" name="syfte" rows="4" maxlength="2000" placeholder="Med kundens egna ord om du har dem">${e_(u.syfte || '')}</textarea>
          <label for="pt-kontakt">Kontaktperson <span class="pt-valfri">(valfritt)</span></label>
          <input id="pt-kontakt" name="kontakt" maxlength="120" autocomplete="off" value="${e_(u.kontakt || '')}">
          <div class="pt-knapprad"><button type="submit" class="pt-knapp primar">Starta kundintervjun</button><a class="pt-knapp" href="${test ? '#/testkunder' : '#/start'}">Avbryt</a></div>
          <p id="pt-svar" role="status" aria-live="polite" class="pt-under"></p>
        </form>
        <aside class="pt-panel pt-bra"><h2>Bra att veta</h2><ul>
          <li>Du behöver inte ha alla svar nu; det som saknas står som okänt.</li>
          <li>Det du skriver här sparas som din anteckning, skild från kundens egna svar.</li>
          <li>Att skapa kunden startar ingen modell, inget bygge och inga konton, och accepterar inget erbjudande.</li>
          <li>${test ? 'Testkunden får aldrig en GitHub-remote, en skarp release eller en aktivering.' : 'Två klick eller ett omförsök blir samma kund.'}</li></ul></aside>
      </div>`);
    const f = document.getElementById('pt-form');
    const spara = () => { const v = Object.fromEntries(new FormData(f)); v.operation = u.operation; try { localStorage.setItem(lagring, JSON.stringify(v)); } catch { /* utan lagring */ } };
    f.addEventListener('input', spara);
    f.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const foretag = f.foretag.value.trim(), webb = f.webbplats.value.trim();
      let ok = true;
      const visaFel = (falt, text) => { const p = document.getElementById(falt + '-fel'); p.textContent = text; p.hidden = !text; document.getElementById(falt).setAttribute('aria-invalid', text ? 'true' : 'false'); if (text) ok = false; };
      visaFel('pt-foretag', foretag ? '' : 'Skriv företagets namn eller ett arbetsnamn.');
      visaFel('pt-webb', !webb || /^https?:\/\/[^\s/$.?#][^\s]*$/i.test(webb) ? '' : 'Skriv hela adressen, till exempel https://exempel.se, eller lämna fältet tomt.');
      if (!ok) { f.querySelector('[aria-invalid="true"]')?.focus(); return; }
      if (!u.operation) { u.operation = crypto.randomUUID(); spara(); }
      const knapp = f.querySelector('button[type=submit]'); knapp.disabled = true;
      const svar = document.getElementById('pt-svar'); svar.textContent = 'Skapar ärendet …';
      try {
        const r = await skicka('/api/desktop/ny-kund', { foretag, webbplats: webb, syfte: f.syfte.value.trim(), kontakt: f.kontakt.value.trim(), test, operation: u.operation });
        try { localStorage.removeItem(lagring); localStorage.setItem('nwp-portal:kund', r.slug); if (r.nyckel) sessionStorage.setItem('nwp-portal:engang:' + r.arende, JSON.stringify({ arende: r.arende, nyckel: r.nyckel })); } catch { /* */ }
        P.data = null;
        location.hash = '#/intervju/' + encodeURIComponent(r.arende);
      } catch (e) {
        if (e.status === 409 && e.svar?.arende) svar.innerHTML = `${e_(e.message)} <a href="#/kundstart/${encodeURIComponent(e.svar.arende)}">Öppna den befintliga kunden</a>`;
        else svar.textContent = e.message;
        knapp.disabled = false;
      }
    });
    f.foretag.focus();
  }

  // --- intervjun (P04): samtalet bredvid det växande, källmärkta underlaget ---
  const AMNEN = { A: 'Verksamhet och mål', B: 'Besökare och uppgifter', C: 'Nuvarande lösning', D: 'Uttryck', E: 'Innehåll', F: 'Funktioner', G: 'Synlighet', H: 'Förvaltning', I: 'Ramar och ansvar', J: 'Särskilda behov' };
  const KUNSKAP = { kunden_uppger: 'kundens ord', kunden_bekraftar: 'kunden bekräftar', agarens_rattelse: 'din rättelse', agarens_anteckning: 'din anteckning',
    tolkning: 'AI:s tolkning', hypotes: 'AI:s hypotes', preferens: 'AI: möjlig preferens', okant: 'AI: okänt' };
  const MODELL = { inte_startad: 'AI har inte tagit någon tur än.', ko: 'Svaret är sparat och väntar på en AI-tur.', pagar: 'AI arbetar med ditt senaste svar …', klar: 'AI har svarat. Rätta det som inte stämmer.',
    fel: 'AI-turen misslyckades; svaren är sparade.', avstangd: 'AI är inte aktiverad för ärendet; svaren sparas.', budget_slut: 'AI-budgeten för ärendet är slut; svaren är sparade.', foraldrat: 'Ärendet ändrades under AI-turen; den gamla turen ersattes.' };
  let intervjuPuls = null;
  async function intervjuvy(eid) {
    clearTimeout(intervjuPuls);
    const hash = location.hash, gen = ++P.vgen;
    let d; try { d = await hamta('/api/kundstart/' + encodeURIComponent(eid)); } catch (e) { return fel(e); }
    if (location.hash !== hash || gen !== P.vgen) return;
    const a = d.arende, namn = (a.anteckningar || []).find((x) => x.slag === 'foretag')?.text || a.slug;
    const utkastNyckel = 'nwp-portal:intervju:' + eid;
    let utkast = ''; try { utkast = localStorage.getItem(utkastNyckel) || ''; } catch { /* */ }
    const aktiv = document.activeElement?.id;
    const ai = a.fiktiv === true && a.budget.anrop < a.budget.max_anrop;
    const mstat = a.modell?.status || 'inte_startad';
    const rad = (m) => m.roll === 'kund'
      ? `<li class="pt-msg kund"><span class="pt-msg-vem">${m.via === 'agaren' ? 'Kundens svar, antecknat av dig' : 'Kundens svar'}</span>${e_(m.text)}<span class="pt-msg-tid">${e_(tid(m.tid))}</span></li>`
      : `<li class="pt-msg ai"><span class="pt-msg-vem">AI-assistenten</span>${e_(m.text)}<span class="pt-msg-tid">${e_(tid(m.tid))}</span></li>`;
    const SLAG = { foretag: 'Företaget', webbplats: 'Befintlig webbplats', syfte: 'Vad de söker hjälp med', kontakt: 'Kontaktperson' };
    const post = (x, slag) => `<li class="pt-post" data-slag="${slag}"><span class="pt-post-kunskap k-${e_(x.kunskap)}">${e_(KUNSKAP[x.kunskap] || x.kunskap)}</span>
        <span class="pt-post-text">${slag === 'anteckning' && SLAG[x.slag] ? `<b>${SLAG[x.slag]}:</b> ` : ''}${e_(x.text)}</span>${x.bestallning === 'rattat' ? '<span class="pt-etikett">rättad</span>' : ''}
        ${slag !== 'anteckning' && x.bestallning !== 'rattat' ? `<button type="button" class="pt-lank" data-ratta="${e_(x.id)}" data-slag="${slag}" data-amne="${e_(x.amne)}">Rätta</button>` : ''}</li>`;
    const perAmne = Object.keys(AMNEN).map((k) => {
      const upp = Object.values(a.uppgifter || {}).filter((u) => u.amne === k);
      const fs = Object.values(a.forslag || {}).filter((f) => f.amne === k && f.bestallning !== 'rattat');
      if (!upp.length && !fs.length) return '';
      return `<section class="pt-amne"><h3>${AMNEN[k]}</h3><ul>${upp.map((u) => post(u, 'uppgift')).join('')}${fs.map((f) => post(f, 'forslag')).join('')}</ul></section>`;
    }).join('');
    yta(`<div class="pt-rubrikrad"><h1>Kundintervju · ${e_(namn)}</h1>${a.fiktiv ? '<span class="pt-test">Testkund</span>' : ''}<a class="pt-knapp" href="#/kundstart/${encodeURIComponent(eid)}">Hela ärendet</a></div>
      <p class="pt-ingress" id="pt-ai-lage" role="status" aria-live="polite">${e_(MODELL[mstat] || a.modell?.text || '')} ${a.fiktiv ? `AI-turer ${a.budget.anrop} av ${a.budget.max_anrop} (testkund, pilotens transport).` : 'Verklig kund: AI-vägen kräver separat aktivering; du för samtalet och underlaget själv.'}
        ${mstat === 'ko' && ai ? '<button type="button" class="pt-knapp" id="pt-ai-nu">Låt AI ta en tur nu</button>' : ''}</p>
      <div id="pt-engang"></div>
      <div class="pt-intervju">
        <section class="pt-panel pt-samtal" aria-labelledby="pt-samtal-r"><h2 id="pt-samtal-r">Samtalet</h2>
          <ol class="pt-msgs" id="pt-msgs">${(a.meddelanden || []).map(rad).join('') || '<li class="pt-tomt">Inget sagt än. Börja med kundens egna ord om verksamheten och vad de vill uppnå.</li>'}</ol>
          ${(a.fragor || []).length ? `<div class="pt-fragor"><h3>AI:s frågor till nästa svar</h3><ul>${a.fragor.map((q) => `<li class="pt-kort" data-kort="fraga"><b>${e_(q.text)}</b><span>${e_(q.varfor)}${q.kritisk ? ' · behövs före nästa steg' : ''}</span>
            <button type="button" class="pt-lank" data-svara="${e_(q.text)}">Svara på frågan</button></li>`).join('')}</ul></div>` : ''}
          <form id="pt-svar-form" class="pt-form"><label for="pt-svar-text">Kundens svar (antecknas som kundens ord, via dig)</label>
            <textarea id="pt-svar-text" rows="3" maxlength="30000" placeholder="Skriv kundens svar här">${e_(utkast)}</textarea>
            <div class="pt-knapprad"><button type="submit" class="pt-knapp primar" name="ai" value="1"${ai ? '' : ' hidden'}>Spara svaret och låt AI fortsätta</button>
              <button type="submit" class="pt-knapp${ai ? '' : ' primar'}" name="ai" value="0">Spara svaret</button></div>
            <p class="pt-under" id="pt-svar-lage" role="status" aria-live="polite">${utkast ? 'Utkast sparat här på datorn, inte skickat.' : ''}</p></form>
        </section>
        <section class="pt-panel pt-underlag" aria-labelledby="pt-underlag-r"><h2 id="pt-underlag-r">Kundunderlag <span class="pt-under">uppdateras när samtalet sparas</span></h2>
          ${(a.anteckningar || []).length ? `<section class="pt-amne"><h3>Dina anteckningar</h3><ul>${a.anteckningar.map((x) => post(x, 'anteckning')).join('')}</ul></section>` : ''}
          ${perAmne || '<p class="pt-tomt">Inga uppgifter än. Det som saknas står som okänt.</p>'}
          ${(a.integrationsforslag || []).length ? `<section class="pt-amne"><h3>AI:s förslag till funktioner</h3><ul>${a.integrationsforslag.map((f) => `<li class="pt-kort" data-kort="integrationsval">
            <span class="pt-post-kunskap k-tolkning">AI:s förslag</span> <b>${e_(f.omrade)}${f.paket ? ' · ' + e_(f.paket) : ' · utreds'}</b>
            <span class="pt-post-text">${e_(f.nytta)}</span><span class="pt-under">Alternativ: ${e_(f.alternativ)} · Konsekvens: ${e_(f.konsekvens)} · Osäkert: ${e_(f.osakerhet)}${f.foljdfraga ? ' · Följdfråga: ' + e_(f.foljdfraga) : ''}</span>
            ${f.paket ? `<button type="button" class="pt-knapp" data-valj="${e_(f.id)}" data-omrade="${e_(f.omrade)}" data-paket="${e_(f.paket)}" data-nytta="${e_(f.nytta)}">Lägg i planen (inget konto ansluts)</button>` : '<span class="pt-under">Paket saknas i katalogen: utreds, ingen anslutning.</span>'}</li>`).join('')}</ul></section>` : ''}
          <section class="pt-amne"><h3>Material</h3>
            <div class="pt-slapp" id="pt-slapp"><p>Dra en fil hit från Finder, eller <label class="pt-lank" for="pt-fil">välj en fil</label>.</p>
              <input type="file" id="pt-fil" accept="image/png,image/jpeg,application/pdf,text/plain" class="pt-dold-text">
              <p class="pt-under">PNG, JPEG, PDF eller UTF-8-text, högst 4 MB och 20 filer. En fil är material, inget kommando; den läses och bedöms innan den används.</p>
              <p id="pt-fil-lage" class="pt-under" role="status" aria-live="polite"></p></div></section>
          ${(a.material || []).length ? `<section class="pt-amne"><h3>Uppladdat</h3><ul>${a.material.map((m) => `<li class="pt-post"><span class="pt-post-text">${e_(m.namn)}${m.person === 'agaren' ? ' <span class="pt-under">(från dig)</span>' : ''}</span><span class="pt-etikett">${m.lasning === 'inte_last' ? 'uppladdad, inte läst' : e_(m.lasning)}</span><span class="pt-etikett">rätt: ${e_(m.rattighet)}</span></li>`).join('')}</ul></section>` : ''}
          <p class="pt-under">Kundens ord, dina anteckningar och rättelser och AI:s tolkningar är märkta var för sig. En AI-tolkning är aldrig kundens bekräftade fakta.</p>
        </section>
      </div>`);
    try { const k = 'nwp-portal:engang:' + eid, e = JSON.parse(sessionStorage.getItem(k) || 'null'); if (e && e.nyckel) { sessionStorage.removeItem(k);
      document.getElementById('pt-engang').innerHTML = `<div class="pt-panel pt-engang"><b>Kunden är skapad.</b> Vill du att kunden svarar själv senare finns en personlig länk; den visas bara nu och skickas inte automatiskt.
        <label for="pt-lank">Kundens personliga länk (lokal)</label><input id="pt-lank" readonly value="${e_('http://127.0.0.1:4773/#arende=' + encodeURIComponent(e.arende) + '&nyckel=' + encodeURIComponent(e.nyckel))}"></div>`; } } catch { /* */ }
    const msgs = document.getElementById('pt-msgs'); msgs.scrollTop = msgs.scrollHeight;
    if (aktiv) document.getElementById(aktiv)?.focus({ preventScroll: true }); else fokus();
    const f = document.getElementById('pt-svar-form'), ta = document.getElementById('pt-svar-text');
    ta.addEventListener('input', () => { try { localStorage.setItem(utkastNyckel, ta.value); } catch { /* */ } document.getElementById('pt-svar-lage').textContent = ta.value ? 'Utkast sparat här på datorn, inte skickat.' : ''; });
    let opNyckel = 'nwp-portal:intervju-op:' + eid;
    f.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const text = ta.value.trim(); if (!text) { ta.focus(); return; }
      const medAi = ev.submitter?.value === '1';
      let op = null; try { const o = JSON.parse(localStorage.getItem(opNyckel) || 'null'); if (o && o.text === text && o.revision === a.revision) op = o.op; } catch { /* */ }
      if (!op) { op = crypto.randomUUID(); try { localStorage.setItem(opNyckel, JSON.stringify({ op, text, revision: a.revision })); } catch { /* */ } }
      f.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      const lage = document.getElementById('pt-svar-lage'); lage.textContent = 'Sparar …';
      try {
        await skicka('/api/desktop/intervju/' + eid + '/svar', { revision: a.revision, operation: op, text });
        try { localStorage.removeItem(utkastNyckel); localStorage.removeItem(opNyckel); } catch { /* */ }
        if (medAi) { try { await skicka('/api/desktop/intervju/' + eid + '/ai', {}); } catch (e) { lage.textContent = 'Svaret är sparat. AI startade inte: ' + e.message; } }
        intervjuvy(eid);
      } catch (e) { lage.textContent = e.status === 409 ? e.message : 'Inte sparat: ' + e.message + ' Texten finns kvar här.'; f.querySelectorAll('button').forEach((b) => { b.disabled = false; }); }
    });
    document.getElementById('pt-ai-nu')?.addEventListener('click', async (e) => {
      e.target.disabled = true;
      try { await skicka('/api/desktop/intervju/' + eid + '/ai', {}); intervjuvy(eid); }
      catch (err) { e.target.insertAdjacentHTML('afterend', ` <span class="pt-fel" role="alert">${e_(err.message)}</span>`); e.target.disabled = false; }
    });
    // material: filväljaren och Finder (HTML5-släpp; appen lämnar släppet till sidan), samma prövning som kundens bilaga
    const filLage = document.getElementById('pt-fil-lage');
    const laddaUpp = async (fil) => {
      if (!fil) return;
      if (fil.size > 4 * 1024 * 1024) { filLage.textContent = `${fil.name} är större än 4 MB och laddas inte upp.`; return; }
      filLage.textContent = `Laddar upp ${fil.name} …`;
      const b64 = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(String(r.result).split(',')[1] || ''); r.onerror = () => rej(r.error); r.readAsDataURL(fil); });
      try {
        await skicka('/api/desktop/intervju/' + eid + '/material', { revision: a.revision, operation: crypto.randomUUID(), namn: fil.name, typ: fil.type || 'application/octet-stream', data: b64 });
        intervjuvy(eid);
      } catch (e) { filLage.textContent = `${fil.name} laddades inte upp: ${e.message}`; }
    };
    document.getElementById('pt-fil').addEventListener('change', (e) => laddaUpp(e.target.files[0]));
    const slapp = document.getElementById('pt-slapp');
    slapp.addEventListener('dragover', (e) => { e.preventDefault(); slapp.classList.add('over'); });
    slapp.addEventListener('dragleave', () => slapp.classList.remove('over'));
    slapp.addEventListener('drop', (e) => { e.preventDefault(); slapp.classList.remove('over'); const f = [...(e.dataTransfer?.files || [])]; if (f.length > 1) filLage.textContent = 'En fil i taget.'; else laddaUpp(f[0]); });
    // frågekort: ingen sidoeffekt, bara skrivfältet
    document.querySelectorAll('[data-svara]').forEach((b) => b.addEventListener('click', () => { ta.focus(); ta.setAttribute('aria-description', 'Svar på: ' + b.dataset.svara); document.getElementById('pt-svar-lage').textContent = 'Svarar på: ' + b.dataset.svara; }));
    // funktionskort: samma väg och prövning som Funktioner i Kundstart (katalogen, revisionen); ett val ansluter inget konto
    document.querySelectorAll('[data-valj]').forEach((b) => b.addEventListener('click', async () => {
      b.disabled = true;
      try {
        await skicka('/api/kundstart/' + eid + '/integrationsval', { revision: a.revision, val: { id: 'ai-' + b.dataset.valj, omrade: b.dataset.omrade, paket: b.dataset.paket, motivering: 'Ur AI:s förslag i intervjun: ' + b.dataset.nytta } });
        intervjuvy(eid);
      } catch (e) { b.insertAdjacentHTML('afterend', `<p class="pt-fel" role="alert">${e_(e.message)}</p>`); b.disabled = false; }
    }));
    document.querySelectorAll('[data-ratta]').forEach((b) => b.addEventListener('click', () => {
      const li = b.closest('li'); if (li.querySelector('form')) return;
      const nu = li.querySelector('.pt-post-text').textContent;
      li.insertAdjacentHTML('beforeend', `<form class="pt-ratta"><label>Rätta till<textarea rows="2" maxlength="30000">${e_(nu)}</textarea></label><div class="pt-knapprad"><button class="pt-knapp primar" type="submit">Spara rättelsen</button><button class="pt-knapp" type="button" data-avbryt>Avbryt</button></div></form>`);
      const fr = li.querySelector('form'); fr.querySelector('textarea').focus();
      fr.querySelector('[data-avbryt]').onclick = () => fr.remove();
      fr.onsubmit = async (ev) => {
        ev.preventDefault();
        const text = fr.querySelector('textarea').value.trim(); if (!text) return;
        const data = { revision: a.revision, operation: crypto.randomUUID(), text, amne: b.dataset.amne };
        if (b.dataset.slag === 'forslag') data.forslag = b.dataset.ratta; else data.uppgift = b.dataset.ratta;
        try { await skicka('/api/desktop/intervju/' + eid + '/rattelse', data); intervjuvy(eid); }
        catch (e) { fr.insertAdjacentHTML('beforeend', `<p class="pt-fel" role="alert">${e_(e.message)}</p>`); }
      };
    }));
    // medan AI arbetar läses ärendet om; aldrig medan du skriver eller rättar (fokus och text står kvar)
    const folj = () => { if (location.hash !== hash) return; if (document.querySelector('.pt-ratta') || (document.activeElement === ta && ta.value)) { intervjuPuls = setTimeout(folj, 4000); return; } intervjuvy(eid); };
    if (['ko', 'pagar'].includes(mstat) && a.fiktiv) intervjuPuls = setTimeout(folj, 4000);
  }

  // --- leverans och förvaltning (P10–P12): läsvyer över de levererade kontrakten; publicering går genom Byggflödets
  // versionsbundna handling med ägarens klick som mandat, aldrig härifrån ---
  const STEGSTATUS = { ja: 'uppfyllt', nej: 'inte uppfyllt', inte_tillampligt: 'inte tillämpligt' };
  async function leveransvy(slug) {
    const hash = location.hash, gen = ++P.vgen;
    let d; try { d = await hamta('/api/desktop/leverans/' + encodeURIComponent(slug)); } catch (e) { return fel(e); }
    if (location.hash !== hash || gen !== P.vgen) return;
    const m = d.migrering || {}, akt = d.aktivering || {};
    const steg = (m.steg || []).map((x) => `<li class="pt-post"><span class="pt-post-kunskap ${x.status === 'ja' ? 'k-kunden_uppger' : x.status === 'nej' ? 'k-tolkning' : ''}">${e_(STEGSTATUS[x.status] || x.status)}</span><b>${e_(x.namn)}</b><span class="pt-post-text pt-under">${e_(x.belagg)}</span></li>`).join('');
    const AKT = { klar: 'klar', gors: 'görs vid aktiveringen', saknas: 'saknas', vantar: 'väntar' };
    const aktSteg = (akt.steg || []).slice(0, 14).map((x) => `<li class="pt-post"><span class="pt-post-kunskap">${e_(AKT[x.status] || x.status)}</span><span class="pt-post-text">${e_(x.text)}${x.varfor ? ' · ' + e_(x.varfor) : ''}</span></li>`).join('');
    const besked = m.fel
      ? `<div class="pt-panel pt-besked"><h2>Leveransläget kunde inte läsas</h2><p class="pt-fel">${e_(m.fel)}</p><p class="pt-under">Inget är observerat härifrån: varken publicerat eller inte publicerat. Försök igen, eller se Byggflöde.</p></div>`
      : d.publicerad
      ? `<div class="pt-panel pt-besked ok"><h2>Webbplatsen är publicerad</h2><p>${e_(m.besked)}</p><p class="pt-under">Produktionens Worker ${e_(d.worker.produktion)}, version ${e_(m.worker?.produktion_version || 'okänd')}. Kvarstående ansvar och kundens handlingar står i aktiveringen nedan.</p></div>`
      : `<div class="pt-panel pt-besked"><h2>Inte publicerad än</h2><p>${e_(m.besked || m.fel || 'Migreringsläget kunde inte läsas.')}</p><p class="pt-under">Leveransbeskedet visas först när en klar release finns och kundens egen adress har observerats svara från Workern. En förhandsvisning eller ett grönt prov är ingen publicering.</p></div>`;
    yta(`<div class="pt-rubrikrad"><h1>Leverans och förvaltning · ${e_(d.namn || slug)}</h1>${d.test ? '<span class="pt-test">Testkund: ingen skarp release, aktiveringen bara som torrkörning</span>' : ''}</div>
      ${besked}
      <div class="pt-tva">
        <section class="pt-panel" id="publicering" aria-labelledby="pt-pub"><h2 id="pt-pub">Publicering genom Cloudflare</h2>
          <p class="pt-under">Förhandsvisning: Worker ${e_(d.worker.forhandsvisning)}${m.worker?.forhandsvisning_version ? ', version ' + e_(m.worker.forhandsvisning_version) : ''}. Produktion: Worker ${e_(d.worker.produktion)}. Kundrepo: ${d.kundrepo ? 'finns' : 'inte skapat'}.</p>
          <ul class="pt-lista-steg">${steg || '<li class="pt-tomt">Inget migreringsläge.</li>'}</ul>
          <p class="pt-under">Releasen är versionsbunden (exportens commit) och kräver ditt klick i Byggflöde, som är dess mandat. Domänen, DNS och kundens konton ändras inte härifrån.</p>
          <a class="pt-knapp" href="#/arbetsyta/${encodeURIComponent(slug)}/flode">Till Byggflöde och releasen</a></section>
        <section class="pt-panel" aria-labelledby="pt-akt"><h2 id="pt-akt">Aktivering och kundens handlingar</h2>
          ${akt.fel ? `<p class="pt-fel">${e_(akt.fel)}</p>` : `<p class="pt-under">Torrkörning utan sidoeffekter: ${akt.kan_koras ? 'kan köras med ditt mandat' : 'kan inte köras än'}.</p><ul class="pt-lista-steg">${aktSteg || '<li class="pt-tomt">Inga steg.</li>'}</ul>`}</section>
      </div>
      <section class="pt-panel" id="forvaltning" aria-labelledby="pt-forv"><h2 id="pt-forv">Förvaltning</h2>
        <p><b>Besök och förfrågningar:</b> ${e_(d.forvaltning.analys.text)}</p>
        <h3>Versioner och kvitton</h3>${d.kvitton.length ? `<ul class="pt-lista">${d.kvitton.slice().reverse().map((k) => `<li>${e_(k.slag)} <span>${e_(k.status || '')} · ${e_(tid(k.tid))}${k.version ? ' · version ' + e_(k.version) : ''}${k.adress ? ' · ' + e_(k.adress) : ''}</span></li>`).join('')}</ul>` : '<p class="pt-tomt">Inga leveranskvitton än.</p>'}
        <h3>Ändringar och tillval</h3><p class="pt-under">En innehållsändring eller ett nytt tillval för samma kund börjar i kundens ärende (Funktioner) eller som ett uppdrag i arbetsytan (Rätta, Omarbeta designen, Bygg ut); ingen ny kund skapas.</p>
        <div class="pt-knapprad"><a class="pt-knapp" href="#/kund/${encodeURIComponent(slug)}">Kundens sida</a><a class="pt-knapp" href="#/arbetsyta/${encodeURIComponent(slug)}">Ge ett uppdrag i arbetsytan</a></div></section>
      <p class="pt-under pt-fot">Läst ${e_(tid(d.tid))} ur migreringsläget, aktiveringens torrkörning och leveranskvittona.</p>`);
    let del = ''; try { del = sessionStorage.getItem('nwp-portal:del') || ''; sessionStorage.removeItem('nwp-portal:del'); } catch { /* */ }
    if (del === 'forvaltning') document.getElementById('forvaltning')?.scrollIntoView(); else fokus();
  }

  // --- förfining (P07/E6): kommentarer på den bevarade ögonblicksbilden, versionsbundna, samlade till ett uppdrag ---
  const KSTATUS = { oppen: 'öppen', avvisad: 'avvisad', bestalld: 'beställd i ett uppdrag', lost_verifierad: 'verifierat löst' };
  const G = { kandidat: null, bredd: '1440', lage: 'visa', punkt: null };
  async function sha40(delar) {
    const h = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(JSON.stringify(delar))))).map((x) => x.toString(16).padStart(2, '0')).join('');
    return h.slice(0, 40);
  }
  async function granskavy(slug) {
    const hash = location.hash, gen = ++P.vgen;
    let d; try { d = await hamta('/api/desktop/kommentarer/' + encodeURIComponent(slug)); } catch (e) { return fel(e); }
    if (location.hash !== hash || gen !== P.vgen) return;  // bara den senaste läsningen ritar (inget ifyllt fält skrivs över)
    const ks = d.kandidater.filter((k) => Object.keys(k.bilder).length);
    if (!ks.find((k) => k.id === G.kandidat)) G.kandidat = ks[0]?.id || null;
    const k = ks.find((x) => x.id === G.kandidat);
    if (k && !k.bilder[G.bredd]) G.bredd = Object.keys(k.bilder)[0];
    const mina = d.kommentarer.filter((c) => k && c.kandidat === k.id);
    const aktuella = mina.filter((c) => !c.inaktuell && c.bredd === G.bredd), aldre = mina.filter((c) => c.inaktuell);
    const nr = new Map(aktuella.map((c, i) => [c.id, i + 1]));
    const kort = (c) => `<li class="pt-kommentar" id="pk-${e_(c.id)}" data-status="${e_(c.status)}">
        ${c.status === 'oppen' && !c.inaktuell ? `<label class="pt-valj"><input type="checkbox" data-valj-k="${e_(c.id)}"><span class="pt-dold-text">Ta med i uppdraget</span></label>` : ''}
        <span class="pt-nr" aria-hidden="true">${nr.get(c.id) || '·'}</span>
        <div><p class="pt-post-text">${e_(c.text)}</p>
        <p class="pt-under">${e_(KSTATUS[c.status] || c.status)} · ${c.x == null ? 'hela sidan' : 'punkt på bilden'} · ${e_(c.bredd)} px · version ${e_(c.version.slice(0, 12))}${c.inaktuell ? ' · <b>inaktuell: kandidaten har en nyare version</b>' : ''} · ${e_(tid(c.tid))}</p>
        ${(c.svar || []).map((x) => `<p class="pt-svar">${e_(x.text)} <span class="pt-under">${e_(tid(x.tid))}</span></p>`).join('')}
        <div class="pt-knapprad"><button type="button" class="pt-lank" data-svara-k="${e_(c.id)}">Svara</button>
          ${c.status === 'oppen' ? `<button type="button" class="pt-lank" data-status-k="${e_(c.id)}" data-till="avvisad">Avvisa</button>` : ''}
          ${['bestalld', 'oppen'].includes(c.status) && c.inaktuell ? `<button type="button" class="pt-lank" data-status-k="${e_(c.id)}" data-till="lost_verifierad">Verifierat löst i den nya versionen</button>` : ''}
          ${c.status === 'avvisad' ? `<button type="button" class="pt-lank" data-status-k="${e_(c.id)}" data-till="oppen">Öppna igen</button>` : ''}</div></div></li>`;
    yta(`<div class="pt-rubrikrad"><h1>Förfining · ${e_(d.namn || slug)}</h1>${d.blind ? '<span class="pt-etikett">neutrala etiketter före ditt första val</span>' : ''}<a class="pt-knapp" href="#/arbetsyta/${encodeURIComponent(slug)}">Arbetsytan: förhandsvisning och beslut</a></div>
      ${!ks.length ? '<p class="pt-tomt">Ingen kandidat har en bevarad ögonblicksbild än. Kommentarer sätts på den bevarade bilden, så att de alltid gäller en bestämd version.</p>' : `
      <div class="pt-verktyg" role="toolbar" aria-label="Kandidat, bredd och läge">
        <label>Kandidat <select id="pk-kandidat">${ks.map((x) => `<option value="${e_(x.id)}"${x.id === G.kandidat ? ' selected' : ''}>${e_(x.etikett)} · version ${e_(x.version.slice(0, 12))}</option>`).join('')}</select></label>
        <div class="pt-filter" role="group" aria-label="Bredd">${['1440', '390'].filter((b) => k.bilder[b]).map((b) => `<button type="button" data-bredd="${b}" aria-pressed="${G.bredd === b}">${b === '1440' ? 'Dator 1440' : 'Mobil 390'}</button>`).join('')}</div>
        <div class="pt-filter" role="group" aria-label="Läge">${[['visa', 'Visa'], ['kommentera', 'Kommentera en punkt']].map(([v, n]) => `<button type="button" data-lage="${v}" aria-pressed="${G.lage === v}">${n}</button>`).join('')}</div>
        <button type="button" class="pt-knapp" id="pk-hela">Kommentera hela sidan</button>
      </div>
      <p class="pt-under" id="pk-hjalp">${G.lage === 'kommentera' ? 'Klicka på bilden där kommentaren gäller. Ett klick väljer bara en punkt; ingenting på sajten händer.' : 'Visa: bilden är den bevarade ögonblicksbilden av versionen ovan. Välj Kommentera en punkt för att peka.'}</p>
      <div class="pt-granska">
        <figure class="pt-bildram${G.lage === 'kommentera' ? ' pt-pek' : ''}" id="pk-ram"><img id="pk-bild" src="/fil/${e_(k.bilder[G.bredd])}" alt="${e_(k.etikett)}, bevarad ögonblicksbild i ${e_(G.bredd)} px">
          ${aktuella.filter((c) => c.x != null).map((c) => `<button type="button" class="pt-nal" style="left:${(c.x * 100).toFixed(2)}%;top:${(c.y * 100).toFixed(2)}%" data-hopp="${e_(c.id)}" aria-label="Kommentar ${nr.get(c.id)}: ${e_(c.text.slice(0, 60))}">${nr.get(c.id)}</button>`).join('')}
          ${G.punkt ? `<span class="pt-nal ny" style="left:${(G.punkt.x * 100).toFixed(2)}%;top:${(G.punkt.y * 100).toFixed(2)}%" aria-hidden="true">+</span>` : ''}</figure>
        <section class="pt-panel" aria-labelledby="pk-rubrik"><h2 id="pk-rubrik">Kommentarer</h2>
          <form id="pk-ny" class="pt-form"${G.punkt || G.hela ? '' : ' hidden'}><label for="pk-text">${G.punkt ? 'Kommentar på punkten' : 'Kommentar på hela sidan'}</label>
            <textarea id="pk-text" rows="3" maxlength="4000"></textarea><div class="pt-knapprad"><button class="pt-knapp primar" type="submit">Spara kommentaren</button><button class="pt-knapp" type="button" id="pk-avbryt">Avbryt</button></div>
            <p class="pt-under">En kommentar är ingen ändringsorder. Samla flera och gör ett uppdrag när du är klar.</p></form>
          <ul class="pt-kommentarer">${aktuella.map(kort).join('') || '<li class="pt-tomt">Inga kommentarer på den här versionen och bredden.</li>'}</ul>
          <div class="pt-knapprad"><button type="button" class="pt-knapp" id="pk-samla" disabled>Gör ett uppdrag av de valda</button></div>
          <form id="pk-uppdrag" class="pt-form" hidden></form>
          <p id="pk-svar" class="pt-under" role="status" aria-live="polite"></p>
          ${aldre.length ? `<details><summary>Äldre versioner (${aldre.length})</summary><ul class="pt-kommentarer">${aldre.map(kort).join('')}</ul></details>` : ''}
        </section>
      </div>`}`);
    if (!ks.length) return fokus();
    const svar = document.getElementById('pk-svar');
    const rita = () => granskavy(slug);
    document.getElementById('pk-kandidat').onchange = (e) => { G.kandidat = e.target.value; G.punkt = null; G.hela = false; rita(); };
    document.querySelectorAll('[data-bredd]').forEach((b) => { b.onclick = () => { G.bredd = b.dataset.bredd; G.punkt = null; rita(); }; });
    document.querySelectorAll('[data-lage]').forEach((b) => { b.onclick = () => { G.lage = b.dataset.lage; G.punkt = null; rita(); }; });
    // punkten eller hela sidan väljs på plats, utan omläsning: det som skrivs i formuläret står kvar
    const visaForm = () => {
      const f = document.getElementById('pk-ny'), ram = document.getElementById('pk-ram');
      f.hidden = !(G.punkt || G.hela);
      f.querySelector('label').textContent = G.punkt ? 'Kommentar på punkten' : 'Kommentar på hela sidan';
      ram.querySelector('.pt-nal.ny')?.remove();
      if (G.punkt) ram.insertAdjacentHTML('beforeend', `<span class="pt-nal ny" style="left:${(G.punkt.x * 100).toFixed(2)}%;top:${(G.punkt.y * 100).toFixed(2)}%" aria-hidden="true">+</span>`);
      if (!f.hidden) document.getElementById('pk-text').focus();
    };
    document.getElementById('pk-hela').onclick = () => { G.punkt = null; G.hela = true; visaForm(); };
    document.getElementById('pk-bild').onclick = (e) => {
      if (G.lage !== 'kommentera') return;
      const r = e.target.getBoundingClientRect();
      G.punkt = { x: Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), y: Math.min(1, Math.max(0, (e.clientY - r.top) / r.height)) }; G.hela = false;
      visaForm();
    };
    document.getElementById('pk-avbryt')?.addEventListener('click', () => { G.punkt = null; G.hela = false; document.getElementById('pk-text').value = ''; visaForm(); });
    document.getElementById('pk-ny')?.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const t = document.getElementById('pk-text').value.trim(); if (!t) return;
      try {
        await skicka('/api/desktop/kommentarer/' + encodeURIComponent(slug), { handling: 'ny', id: crypto.randomUUID(), kandidat: k.id, version: k.version, bredd: G.bredd,
          bild: k.bilder[G.bredd], bild_sha: k.sha[G.bredd], x: G.punkt ? G.punkt.x : null, y: G.punkt ? G.punkt.y : null, text: t });
        G.punkt = null; G.hela = false; rita();
      } catch (e) { svar.textContent = (e.status === 409 ? 'Inaktuell: ' : 'Inte sparad: ') + e.message; }
    });
    document.querySelectorAll('[data-hopp]').forEach((b) => { b.onclick = () => document.getElementById('pk-' + b.dataset.hopp)?.scrollIntoView({ block: 'nearest' }); });
    document.querySelectorAll('[data-status-k]').forEach((b) => { b.onclick = async () => {
      try { await skicka('/api/desktop/kommentarer/' + encodeURIComponent(slug), { handling: 'status', id: b.dataset.statusK, status: b.dataset.till }); rita(); }
      catch (e) { svar.textContent = e.message; } }; });
    document.querySelectorAll('[data-svara-k]').forEach((b) => { b.onclick = () => {
      const li = b.closest('li'); if (li.querySelector('.pt-ratta')) return;
      li.insertAdjacentHTML('beforeend', '<form class="pt-ratta"><label>Svar<textarea rows="2" maxlength="4000"></textarea></label><div class="pt-knapprad"><button class="pt-knapp primar" type="submit">Spara svaret</button></div></form>');
      const f = li.querySelector('.pt-ratta'); f.querySelector('textarea').focus();
      f.onsubmit = async (ev) => { ev.preventDefault(); const t = f.querySelector('textarea').value.trim(); if (!t) return;
        try { await skicka('/api/desktop/kommentarer/' + encodeURIComponent(slug), { handling: 'svara', id: b.dataset.svaraK, text: t }); rita(); } catch (e) { svar.textContent = e.message; } };
    }; });
    const valda = () => [...document.querySelectorAll('[data-valj-k]:checked')].map((x) => x.dataset.valjK);
    document.querySelectorAll('[data-valj-k]').forEach((x) => { x.onchange = () => { document.getElementById('pk-samla').disabled = !valda().length; }; });
    document.getElementById('pk-samla').onclick = () => {
      const ids = valda(), texter = ids.map((id) => aktuella.find((c) => c.id === id)).map((c) => `${nr.get(c.id)}. ${c.text}${c.x == null ? '' : ` (punkt ${Math.round(c.x * 100)} % från vänster, ${Math.round(c.y * 100)} % uppifrån i ${c.bredd} px)`}`);
      const f = document.getElementById('pk-uppdrag'); f.hidden = false;
      f.innerHTML = `<label for="pk-typ">Uppdrag</label><select id="pk-typ"><option value="ratta">Rätta</option><option value="omarbeta">Omarbeta designen</option><option value="bygg_ut">Bygg ut</option></select>
        <label for="pk-res">Önskat resultat</label><textarea id="pk-res" rows="2">Rätta de kommenterade punkterna i ${e_(k.etikett)}.</textarea>
        <label for="pk-omf">Omfattning (en rad per punkt)</label><textarea id="pk-omf" rows="${Math.min(8, texter.length + 1)}">${e_(texter.join('\n'))}</textarea>
        <label for="pk-bev">Det som ska bevaras</label><textarea id="pk-bev" rows="2" placeholder="Till exempel: allt annat i layouten och texterna"></textarea>
        <div class="pt-knapprad"><button class="pt-knapp primar" type="submit">Spara uppdraget</button></div>
        <p class="pt-under">Uppdraget sparas i domloggen bundet till kandidat och version, som ett uppdrag i arbetsytan. Inget arbete startar: du startar det under Kontroller.</p>`;
      document.getElementById('pk-res').focus();
      f.onsubmit = async (ev) => {
        ev.preventDefault();
        const rad = (id) => document.getElementById(id).value.split('\n').map((x) => x.trim()).filter(Boolean);
        const uppdrag = { typ: document.getElementById('pk-typ').value, resultat: document.getElementById('pk-res').value.trim(), omfattning: rad('pk-omf'), bevara: rad('pk-bev') };
        if (!uppdrag.resultat || !uppdrag.omfattning.length || !uppdrag.bevara.length) { svar.textContent = 'Uppdraget behöver resultat, omfattning och vad som ska bevaras.'; return; }
        const text = 'Uppdrag ur portalens kommentarer: ' + uppdrag.omfattning.join(' · ');
        const andringId = 'p' + await sha40([slug, ids, uppdrag, k.version, d.korning]);
        try {
          await skicka('/api/arbetsyta/' + encodeURIComponent(slug) + '/andring', { andring_id: andringId, text, beslut: 'uppdrag', uppdrag, kandidat: k.id, version: k.version, korning: d.korning, vy: 'Portalen, kommentarer' });
          await skicka('/api/desktop/kommentarer/' + encodeURIComponent(slug), { handling: 'bestall', ids, andring_id: andringId });
          rita();
        } catch (e) { svar.textContent = (e.status === 409 ? 'Inaktuell: ' : 'Inte sparat: ') + e.message; }
      };
    };
    fokus();
  }

  function fel(e) {
    yta(`<h1>Kunderna kunde inte läsas</h1><p class="pt-fel" role="alert">${e_(e.message)}</p><p class="pt-under">Motorn svarade inte som väntat. Inget har ändrats. <a href="#/start">Försök igen</a></p>`);
    fokus();
  }

  window.portalvy = async function portalvy(h) {
    const [v, rest] = String(h || '').split('/');
    if (v === 'kunder') return listvy(false);
    if (v === 'testkunder') return listvy(true);
    if (v === 'ny-kund') return nykundvy(false);
    if (v === 'ny-testkund') return nykundvy(true);
    if (v === 'kund' && rest) return kundvy(decodeURIComponent(rest));
    if (v === 'intervju' && /^[a-f0-9]{32}$/.test(rest || '')) return intervjuvy(rest);
    if (v === 'leverans-kund' && rest) return leveransvy(decodeURIComponent(rest));
    if (v === 'granska' && rest) return granskavy(decodeURIComponent(rest));
    return startvy();
  };
  window.portalEgna = EGNA;
})();
