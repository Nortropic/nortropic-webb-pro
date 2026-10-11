// forhandsbrygga.js — arbetsytans och studions brygga i den lokala förhandsvisningen (E6, Nortropic.app 2026-10-10;
// designstudion 2026-10-11, kunskap/designstudio.md). Läggs bara in av dashboardens förhandsvisningsserver (prova.Server med
// brygga, server.visa_kandidat), aldrig i en byggd sajt, en ögonblicksbild, ett prov eller en export. Förhandsvisningen är
// kandidatens kod och räknas som obetrodd: bryggan tar bara emot meddelanden från arbetsytans ursprung (fönstret som ramar
// in den), skickar bara data dit och har inga rättigheter utöver sidans egna. En markering bär källkartans id (data-nwp-k,
// insatt av kandidatens förhandsbygge), förekomsten och, för en bild i en komponent, barnets index: aldrig en fil, en väg
// eller ett kommando. Motorn slår själv upp vad id:t betyder i källan och prövar sidan i sin egen webbläsare.
// Varje meddelande hit bär arbetsytans nonce för just den här laddningen (hej), så att ett sent meddelande från en äldre
// laddning eller en annan ram inte räknas.
// Lägen: besok (sajten som vanligt), markera (ett klick markerar ett element åt samtalet), kommentera (ett klick ger en
// kommentarspunkt på elementet), valj (studions Redigera: ett klick väljer elementet för kontrollerna) och redigera (den
// äldre textredigeringen: ett klick på en text frågar arbetsytan om texten kan ändras i källan).
(() => {
  const URSPRUNG = '__NWP_URSPRUNG__';
  if (window.parent === window) return;
  const NAMN = 'forhandsbrygga/1';
  const ATTR = 'data-nwp-k';
  const LAGEN = ['besok', 'markera', 'kommentera', 'valj', 'redigera'];
  let lage = 'besok', ram = null, markerad = null, redigeras = null, nonce = null, provark = null;

  const skicka = (typ, data) => window.parent.postMessage(Object.assign({ nwp: NAMN, typ, sida: location.pathname, nonce }, data || {}), URSPRUNG);
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
  // källkartans del: närmaste element med id (elementet självt eller en förfader), förekomsten bland element med samma id
  // och, för en bild eller video som komponenten ritar utan eget id, barnets index i det elementet
  function kalla(el) {
    let a = el;
    while (a && a.nodeType === 1 && !a.hasAttribute(ATTR)) a = a.parentElement;
    if (!a || a.nodeType !== 1) return null;
    const k = a.getAttribute(ATTR);
    if (!/^[0-9a-f]{12}$/.test(k)) return null;
    const instans = Array.from(document.querySelectorAll('[' + ATTR + '="' + k + '"]')).indexOf(a);
    let barn = null;
    if (a !== el && ['IMG', 'VIDEO'].includes(el.tagName)) {
      const i = Array.from(a.querySelectorAll(el.tagName.toLowerCase())).indexOf(el);
      if (i >= 0 && i < 100) barn = el.tagName.toLowerCase() + ':' + i;
    }
    return { k, instans, barn, egen: a === el || !!barn };
  }
  function beskriv(el) {
    const r = el.getBoundingClientRect();
    return { tagg: el.tagName.toLowerCase(), text: text(el).slice(0, 500), selektor: selektor(el), rubrik: rubrik(el),
      rekt: { x: Math.round(r.x), y: Math.round(r.y + scrollY), b: Math.round(r.width), h: Math.round(r.height) }, bredd: innerWidth,
      kalla: kalla(el) };
  }
  // en text att redigera: elementet självt när det bara har text (och radbrytningar), aldrig en behållare med fler element
  function textelement(el) {
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      if (Array.from(e.children).every((c) => c.tagName === 'BR') && text(e)) return e;
      if (e.children.length) return null;
    }
    return null;
  }
  // det som ett klick i valj- och kommentarsläget gäller: bilden själv, annars närmaste element med id
  function kallelement(el) {
    if (!el || el.nodeType !== 1) return null;
    if (['IMG', 'VIDEO'].includes(el.tagName)) return el;
    let a = el;
    while (a && a.nodeType === 1 && !a.hasAttribute(ATTR)) a = a.parentElement;
    return a && a.nodeType === 1 ? a : null;
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
  // studions provade värden: en egen stilmall ovanpå sidans (CSSOM, som innehållspolicyn inte stänger), som arbetsytan
  // fyller ur motorns karta; inget sparas, inget byggs, och rensa tar bort den
  function prova(css) {
    try {
      const ark = new CSSStyleSheet();
      ark.replaceSync(String(css || '').slice(0, 20000));
      document.adoptedStyleSheets = document.adoptedStyleSheets.filter((x) => x !== provark).concat([ark]);
      provark = ark;
      if (markerad) visaRam(markerad, 'osparad');
      return true;
    } catch (e) { return false; }
  }
  function rensa() {
    if (provark) document.adoptedStyleSheets = document.adoptedStyleSheets.filter((x) => x !== provark);
    provark = null;
    if (markerad) visaRam(markerad);
  }
  // strukturen: elementen med id i dokumentets ordning, för en lista som går att nå med tangentbordet (WCAG 2.5.7)
  function struktur() {
    const ut = [];
    const sedda = {};
    for (const el of document.querySelectorAll('[' + ATTR + ']')) {
      if (ut.length >= 400) break;
      const k = el.getAttribute(ATTR);
      const instans = sedda[k] = (sedda[k] ?? -1) + 1;
      let djup = 0;
      for (let p = el.parentElement; p; p = p.parentElement) if (p.hasAttribute?.(ATTR)) djup++;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      ut.push({ k, instans, tagg: el.tagName.toLowerCase(), text: text(el).slice(0, 60), djup: Math.min(djup, 12),
        bild: !!el.querySelector(':scope > img, :scope > picture img, :scope > video') });
    }
    return ut;
  }
  function valjK(k, instans, barn) {
    const a = document.querySelectorAll('[' + ATTR + '="' + String(k).replace(/[^0-9a-f]/g, '') + '"]')[Number(instans) || 0];
    if (!a) return null;
    let el = a;
    const m = String(barn || '').match(/^(img|video):(\d{1,2})$/);
    if (m) el = a.querySelectorAll(m[1])[Number(m[2])] || a;
    return el;
  }

  addEventListener('message', (ev) => {
    if (ev.source !== window.parent || ev.origin !== URSPRUNG) return;
    const d = ev.data; if (!d || d.nwp !== NAMN || typeof d.typ !== 'string') return;
    if (d.typ === 'hej') {  // arbetsytans nonce för den här laddningen; bara det första gäller
      if (!nonce && typeof d.nonce === 'string' && /^[0-9a-f]{16,64}$/.test(d.nonce)) { nonce = d.nonce; skicka('kartad', { kartad: !!document.querySelector('[' + ATTR + ']') }); }
      return;
    }
    if (!nonce || d.nonce !== nonce) return;
    if (d.typ === 'lage' && LAGEN.includes(d.lage)) {
      if (redigeras) slutaRedigera(false);
      lage = d.lage; visaRam(null);
      document.documentElement.style.cursor = lage === 'besok' ? '' : lage === 'redigera' ? 'text' : lage === 'kommentera' ? 'cell' : 'crosshair';
    }
    if (d.typ === 'redigera-start' && lage === 'redigera' && !redigeras) {
      const el = document.querySelector(String(d.selektor || ''));
      if (!el || text(el) !== d.text) { skicka('redigera-avbrutet', { selektor: d.selektor, skal: 'texten har ändrats på sidan' }); return; }
      const r = { el, selektor: d.selektor, gammal: d.text, original: el.textContent };
      r.tangent = (e) => { if (e.key === 'Enter') { e.preventDefault(); slutaRedigera(true); } else if (e.key === 'Escape') { e.preventDefault(); slutaRedigera(false); } };
      r.lamna = () => slutaRedigera(true);  // ett förslag, inget sparande: arbetsytan frågar innan källan ändras
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
    if (d.typ === 'visa-k') {  // studions markering ur listan eller efter en ombyggnad: samma id, ingen ny händelse
      markerad = valjK(d.k, d.instans, d.barn); visaRam(markerad);
      if (markerad && d.rulla) markerad.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }
    if (d.typ === 'valj-k') {  // tangentbordets väg: listan i arbetsytan väljer ett element som ett klick hade gjort
      const el = valjK(d.k, d.instans, d.barn);
      if (el) { markerad = el; visaRam(el); el.scrollIntoView({ block: 'center' }); skicka(lage === 'markera' ? 'markerat' : 'valt', beskriv(el)); }
    }
    if (d.typ === 'struktur') skicka('struktur', { lista: struktur() });
    if (d.typ === 'prova') skicka('provat', { ok: prova(d.css) });
    if (d.typ === 'prova-rensa') { rensa(); skicka('provat', { ok: true, rensat: true }); }
  });
  addEventListener('mousemove', (ev) => {
    if (lage === 'besok' || redigeras) return;
    const el = lage === 'redigera' ? (textelement(ev.target) || null) : lage === 'markera' ? ev.target : kallelement(ev.target);
    visaRam(el && el !== document.documentElement && el !== document.body ? el : null);
  }, true);
  addEventListener('click', (ev) => {
    if (lage === 'besok' || (redigeras && redigeras.el.contains(ev.target))) return;
    ev.preventDefault(); ev.stopPropagation();  // i alla lägen utom besök navigerar ett klick aldrig på sajten
    if (redigeras) { slutaRedigera(true); return; }
    const el = ev.target;
    if (!el || el === document.documentElement || el === document.body || !nonce) return;
    if (lage === 'markera') { markerad = el; skicka('markerat', beskriv(el)); visaRam(el); return; }
    if (lage === 'valj' || lage === 'kommentera') {
      const k = kallelement(el);
      if (!k) { skicka('ej-kalla', beskriv(el)); return; }
      markerad = k; visaRam(k);
      const r = k.getBoundingClientRect();
      const punkt = { x: Math.max(0, Math.min(1, (ev.clientX - r.left) / (r.width || 1))), y: Math.max(0, Math.min(1, (ev.clientY - r.top) / (r.height || 1))) };
      skicka(lage === 'valj' ? 'valt' : 'kommentar-punkt', Object.assign(beskriv(k), lage === 'kommentera' ? { punkt } : {}));
      return;
    }
    const t = textelement(el);
    if (!t) { skicka('ej-text', beskriv(el)); return; }
    skicka('redigera-val', beskriv(t));
  }, true);
  addEventListener('submit', (ev) => { if (lage !== 'besok') { ev.preventDefault(); ev.stopPropagation(); } }, true);
  skicka('redo', { titel: document.title.slice(0, 120) });
})();
