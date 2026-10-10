// forhandsbrygga.js — arbetsytans brygga i den lokala förhandsvisningen (E6; Nortropic.app, 2026-10-10).
// Läggs bara in av dashboardens förhandsvisningsserver (prova.Server med brygga, server.visa_kandidat), aldrig i en byggd
// sajt, en ögonblicksbild, ett prov eller en export. Förhandsvisningen är kandidatens kod och räknas som obetrodd: bryggan
// tar bara emot lägen från arbetsytans ursprung (fönstret som ramar in den), skickar bara data dit (text, väg och en
// beskrivning av elementet) och har inga rättigheter utöver sidans egna. Arbetsytan sparar ingenting utan ägarens klick.
// Lägen: besok (sajten som vanligt), markera (ett klick markerar ett element åt samtalet) och redigera (ett klick på en
// text frågar arbetsytan om texten kan ändras i källan; först då blir den redigerbar här, och Enter skickar förslaget).
(() => {
  const URSPRUNG = '__NWP_URSPRUNG__';
  if (window.parent === window) return;
  const NAMN = 'forhandsbrygga/1';
  let lage = 'besok', ram = null, markerad = null, redigeras = null;

  const skicka = (typ, data) => window.parent.postMessage(Object.assign({ nwp: NAMN, typ, sida: location.pathname }, data || {}), URSPRUNG);
  const text = (el) => (el?.textContent || '').replace(/\s+/g, ' ').trim();
  function selektor(el) {
    const delar = [];
    for (let e = el; e && e.nodeType === 1 && e !== document.body && delar.length < 10; e = e.parentElement) {
      const tagg = e.tagName.toLowerCase();
      const syskon = e.parentElement ? Array.from(e.parentElement.children).filter((x) => x.tagName === e.tagName) : [];
      delar.unshift(syskon.length > 1 ? `${tagg}:nth-of-type(${syskon.indexOf(e) + 1})` : tagg);
    }
    return 'body > ' + delar.join(' > ');
  }
  function rubrik(el) {  // närmaste rubrik före elementet: sammanhanget som en människa känner igen
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      const h = e.matches?.('h1,h2,h3') ? e : e.querySelector?.(':scope > h1, :scope > h2, :scope > h3');
      if (h && h !== el) return text(h).slice(0, 80);
    }
    return null;
  }
  function beskriv(el) {
    const r = el.getBoundingClientRect();
    return { tagg: el.tagName.toLowerCase(), text: text(el).slice(0, 500), selektor: selektor(el), rubrik: rubrik(el),
      rekt: { x: Math.round(r.x), y: Math.round(r.y + scrollY), b: Math.round(r.width), h: Math.round(r.height) }, bredd: innerWidth };
  }
  // en text att redigera: elementet självt när det bara har text (och radbrytningar), aldrig en behållare med fler element
  function textelement(el) {
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      if (Array.from(e.children).every((c) => c.tagName === 'BR') && text(e)) return e;
      if (e.children.length) return null;
    }
    return null;
  }
  function visaRam(el, slag) {
    if (!ram) {
      ram = document.createElement('div');
      ram.setAttribute('aria-hidden', 'true');
      ram.style.cssText = 'position:absolute;pointer-events:none;z-index:2147483647;border:2px solid #6d5dfc;border-radius:3px;background:rgba(109,93,252,.08);transition:all .05s';
      document.documentElement.appendChild(ram);
    }
    if (!el) { ram.style.display = 'none'; return; }
    const r = el.getBoundingClientRect();
    Object.assign(ram.style, { display: 'block', left: (r.left + scrollX - 2) + 'px', top: (r.top + scrollY - 2) + 'px', width: (r.width + 4) + 'px', height: (r.height + 4) + 'px',
      borderStyle: slag === 'osparad' ? 'dashed' : 'solid', borderColor: slag === 'osparad' ? '#c2410c' : '#6d5dfc' });
  }
  function slutaRedigera(skicka_) {
    const r = redigeras; if (!r) return;
    redigeras = null;
    r.el.removeAttribute('contenteditable');
    r.el.removeEventListener('keydown', r.tangent, true);
    r.el.removeEventListener('blur', r.lamna, true);
    const ny = text(r.el);
    if (!skicka_ || ny === r.gammal) { r.el.textContent = r.original; visaRam(null); skicka('redigera-avbrutet', { selektor: r.selektor }); return; }
    visaRam(r.el, 'osparad');  // förslaget syns här tills arbetsytan sparat det i källan och sidan byggts om, eller ångrat det
    skicka('redigerat', { selektor: r.selektor, gammal: r.gammal, ny });
  }

  addEventListener('message', (ev) => {
    if (ev.source !== window.parent || ev.origin !== URSPRUNG) return;
    const d = ev.data; if (!d || d.nwp !== NAMN) return;
    if (d.typ === 'lage' && ['besok', 'markera', 'redigera'].includes(d.lage)) {
      if (redigeras) slutaRedigera(false);
      lage = d.lage; visaRam(null);
      document.documentElement.style.cursor = lage === 'besok' ? '' : lage === 'markera' ? 'crosshair' : 'text';
    }
    if (d.typ === 'redigera-start' && lage === 'redigera' && !redigeras) {
      const el = document.querySelector(String(d.selektor || ''));
      if (!el || text(el) !== d.text) { skicka('redigera-avbrutet', { selektor: d.selektor, skal: 'texten har ändrats på sidan' }); return; }
      const r = { el, selektor: d.selektor, gammal: d.text, original: el.textContent };
      r.tangent = (e) => { if (e.key === 'Enter') { e.preventDefault(); slutaRedigera(true); } else if (e.key === 'Escape') { e.preventDefault(); slutaRedigera(false); } };
      r.lamna = () => slutaRedigera(true);
      redigeras = r;
      try { el.contentEditable = 'plaintext-only'; } catch { el.contentEditable = 'true'; }
      el.addEventListener('keydown', r.tangent, true);
      el.addEventListener('blur', r.lamna, true);
      el.focus();
      const s = getSelection(); const omr = document.createRange(); omr.selectNodeContents(el); s.removeAllRanges(); s.addRange(omr);
      visaRam(el);
    }
    if (d.typ === 'aterstall') {  // arbetsytan sparade inte: sidans text tillbaka
      const el = document.querySelector(String(d.selektor || ''));
      if (el && typeof d.text === 'string') el.textContent = d.text;
      visaRam(null);
    }
    if (d.typ === 'visa-markering') { markerad = d.selektor ? document.querySelector(String(d.selektor)) : null; visaRam(markerad); markerad?.scrollIntoView({ block: 'center' }); }
  });
  addEventListener('mousemove', (ev) => {
    if (lage === 'besok' || redigeras) return;
    const el = lage === 'redigera' ? (textelement(ev.target) || null) : ev.target;
    visaRam(el && el !== document.documentElement && el !== document.body ? el : null);
  }, true);
  addEventListener('click', (ev) => {
    if (lage === 'besok' || (redigeras && redigeras.el.contains(ev.target))) return;
    ev.preventDefault(); ev.stopPropagation();  // i markera och redigera navigerar ett klick aldrig på sajten
    if (redigeras) { slutaRedigera(true); return; }
    const el = ev.target;
    if (!el || el === document.documentElement || el === document.body) return;
    if (lage === 'markera') { skicka('markerat', beskriv(el)); visaRam(el); return; }
    const t = textelement(el);
    if (!t) { skicka('ej-text', beskriv(el)); return; }
    skicka('redigera-val', beskriv(t));
  }, true);
  addEventListener('submit', (ev) => { if (lage !== 'besok') { ev.preventDefault(); ev.stopPropagation(); } }, true);
  skicka('redo', { titel: document.title.slice(0, 120) });
})();
