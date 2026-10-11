// Studion (designstudion 2026-10-11; kunskap/designstudio.md): arbetsytans vy för att bedöma och forma riktningarna. Riktig
// rendering i mitten (kandidatens arbetsversion i exakt viewport-bredd), riktningarna med sitt verkliga läge till vänster och
// kontextpanelen till höger: vad nästa ändring gäller, de fem områdena med källa och räckvidd ur motorns karta
// (kontroller/studio.py), provade värden som syns direkt och ett sparande som går genom flödets ordinarie väg. Vyn räknar
// ingen egen status: läget kommer ur arbetsytans ström, kartan ur motorn, och bryggan i förhandsvisningen bär bara id.
(() => {
  const AY = () => window.NortropicArbetsyta;
  const S = { kid: null, bredd: 1280, lage: 'valj', sida: '/', val: null, karta: null, kartNyckel: null, kartLaser: false, kartFel: null,
    provat: {}, sparar: null, senast: null, kommentar: null, struktur: null, visaStruktur: false, ref: false, uppdrag: null, kartad: null,
    dukNyckel: null, version: null, notis: null };
  const BREDDER = [[390, 'Mobil'], [768, 'Surfplatta'], [1280, 'Dator'], [1440, 'Bred']];
  const LAGEN = [['besok', 'Besök', 'sajten som vanligt: länkar och formulär fungerar'], ['markera', 'Markera', 'ett klick markerar en del åt samtalet'],
    ['kommentera', 'Kommentera', 'ett klick ger en kommentar bunden till elementet och versionen'], ['valj', 'Redigera', 'ett klick väljer elementet för kontrollerna']];
  const VISA = [['arbetsversion', 'Arbetsversion'], ['snapshot', 'Ögonblicksbild'], ['jamfor', 'Jämför'], ['kandidater', 'Kandidater'], ['underlag', 'Underlag']];
  // arbetsversionen visas i studions duk; de andra i arbetsytans material (samma ritning, beslutsrad och skydd som förut)
  const visaLage = () => (['snapshot', 'jamfor', 'kandidater', 'underlag'].includes(AY().A.material) ? AY().A.material : 'arbetsversion');
  const OMRADEN = [['typografi', 'Typografi'], ['text', 'Text'], ['bildregi', 'Bildregi'], ['mellanrum', 'Mellanrum'], ['komposition', 'Komposition'], ['farg', 'Färg och yta']];
  const STATUS = { koad: 'köad: väntar på att starta', pagar: 'skrivs i källan; kandidaten byggs om, fotograferas och kontrolleras', klar: 'klar',
    aterstalld: 'återställd', konflikt: 'inte gjord (konflikt)', fel: 'misslyckades', stoppad: 'stoppad', nekad: 'nekad' };
  const KLARA = ['klar', 'aterstalld', 'konflikt', 'fel', 'stoppad', 'nekad'];
  const RACKVIDD = { objekt: 'Detta objekt', forekomster: 'Alla förekomster', regel: 'Regel', designgrund: 'Designgrunden', arvd: 'Ärvt', sida: 'Sidan' };
  const e_ = (s) => AY().e_(s);
  const lager = () => 'nwp-studio:' + (AY().A.slug || '');
  function laddaLayout() { try { return JSON.parse(localStorage.getItem(lager()) || '{}') || {}; } catch { return {}; } }
  function sparaLayout(x) { try { localStorage.setItem(lager(), JSON.stringify(Object.assign(laddaLayout(), x))); } catch { /* bekvämlighet */ } }

  function kandidater() { return AY().A.lage?.kandidater || []; }
  function kandidat() { return kandidater().find((k) => k.id === S.kid) || null; }
  // kandidaterna vid sin gräns: kedjan är klar, och körningen skriver inte i dem (kandidater.VISBARA; DS4)
  const VID_GRANS = ['klar', 'vald', 'jamfors', 'forkastad', 'forfinad', 'godkand'];
  // varför studions kontroller inte ändrar den valda riktningen nu, eller null när de gör det
  function sparrskal() {
    const l = AY().A.lage || {}, k = kandidat();
    if (l.blind) return 'Gör ditt första val i körningen först (i Förslagen). Före det visas riktningarna blint, och studions kontroller ändrar inget.';
    if (k && k.status === 'bedombar') return 'Riktningen är bedömbar men granskas, och skaparens svar kan bli en ny version. Du kan jämföra, kommentera och gilla den nu; kontrollerna öppnas när den är klar.';
    if (k && !VID_GRANS.includes(k.status)) return `Riktningen arbetar (${k.statustext || k.status}). Kontrollerna öppnas när den är klar; de andra riktningarna går att ändra under tiden.`;
    return null;
  }
  const kanRedigera = () => !sparrskal();
  // en ny version får inte ta över det du håller på med: provade värden, en kommentar eller ett uppdrag som skrivs (DS-U07)
  const aktiv = () => Object.keys(S.provat).length > 0 || !!S.kommentar || !!S.uppdrag || !!document.getElementById('st-kontext')?.contains(document.activeElement);

  // --- ingången ---
  function rita(A) {
    const rot = document.getElementById('st-rot'); if (!rot || !A.lage) return;
    if (!rot.dataset.byggd) {
      const l = laddaLayout();
      S.bredd = BREDDER.some(([b]) => b === l.bredd) ? l.bredd : 1280;
      S.lage = LAGEN.some(([k]) => k === l.lage) ? l.lage : 'valj';
      // panelernas bredd och om de är hopfällda står kvar per kund (förr arbetsytans avdelare och fällknappar)
      if (Number(l.vanster) >= 160 && Number(l.vanster) <= 420) rot.style.setProperty('--st-vanster', l.vanster + 'px');
      if (Number(l.hoger) >= 280 && Number(l.hoger) <= 640) rot.style.setProperty('--st-hoger', l.hoger + 'px');
      if (l.vansterDold) rot.dataset.vansterDold = ''; if (l.hogerDold) rot.dataset.hogerDold = '';
      rot.innerHTML = `
        <aside class="st-vanster" aria-labelledby="st-riktningar-rubrik">
          <div class="st-panelhuvud"><h2 id="st-riktningar-rubrik">Riktningar</h2><span class="svag" id="st-antal"></span>
            <button class="ay-ikon st-fall" type="button" data-st-fall="vanster" aria-label="Fäll ihop riktningarna">‹</button></div>
          <ol class="st-remsa" id="st-remsa"></ol>
          <details class="st-ref" id="st-refruta"${l.ref ? ' open' : ''}><summary>Referensen</summary><div id="st-ref"></div></details>
        </aside>
        <div class="st-delare" data-st-delare="vanster" role="separator" aria-orientation="vertical" aria-label="Riktningarnas bredd" tabindex="0"></div>
        <section class="st-mitten" aria-labelledby="st-duk-rubrik">
          <h2 class="dolt" id="st-duk-rubrik">Förhandsvisning och material</h2>
          <div class="st-verktyg" id="st-verktyg"></div>
          <div class="st-dukbesked" id="st-dukbesked" role="status" aria-live="polite"></div>
          <div class="st-dukram" id="st-dukram"><div class="st-duk" id="st-duk" tabindex="0" role="region" aria-label="Förhandsvisningen"></div><div class="st-struktur" id="st-struktur" hidden></div></div>
          <section class="ay-panel ay-material st-material" aria-labelledby="ay-material-rubrik" id="ay-material" hidden></section>
          <p class="st-dukrad svag" id="st-dukrad" role="status" aria-live="polite"></p>
        </section>
        <div class="st-delare" data-st-delare="hoger" role="separator" aria-orientation="vertical" aria-label="Panelens bredd" tabindex="0"></div>
        <aside class="st-hoger" aria-label="Arbete med den valda riktningen">
          <div class="st-flikrad"><div class="st-flikar" role="tablist" aria-label="Ändra, samtal och arbete">${[['andra', 'Ändra'], ['samtal', 'Samtal'], ['arbete', 'Arbete']].map(([k, n]) =>
            `<button type="button" role="tab" id="st-tab-${k}" data-st-flik="${k}" aria-controls="st-flik-${k}" aria-selected="${(l.flik || 'andra') === k}" tabindex="${(l.flik || 'andra') === k ? 0 : -1}">${n}${k === 'samtal' ? ' <span class="ay-rakning" id="ay-oppna"></span>' : ''}</button>`).join('')}
            </div><button class="ay-ikon st-fall" type="button" data-st-fall="hoger" aria-label="Fäll ihop panelen">›</button></div>
          <div class="st-flik" id="st-flik-andra" role="tabpanel" aria-labelledby="st-tab-andra"${(l.flik || 'andra') === 'andra' ? '' : ' hidden'}>
            <div class="st-kontext" id="st-kontext"></div>
          </div>
          <div class="st-flik" id="st-flik-samtal" role="tabpanel" aria-labelledby="st-tab-samtal"${l.flik === 'samtal' ? '' : ' hidden'}>
            <section class="ay-panel ay-dialog st-dialog" aria-labelledby="ay-dialog-rubrik">
              <div class="ay-panelhuvud"><h2 id="ay-dialog-rubrik">Samtal</h2>
                <div class="ay-segment ay-flikar" role="tablist" aria-label="Samtal och meddelanden">${[['partner', 'Partnern'], ['meddelanden', 'Meddelanden']].map(([k, n]) =>
                  `<button type="button" role="tab" data-vflik="${k}" data-fokus="vf-${k}" aria-selected="${k === 'partner'}" aria-controls="ay-samtal">${n}</button>`).join('')}</div>
                <span id="ay-partnerchip"></span></div>
              <div class="ay-panelkropp" id="ay-samtal" aria-live="off"></div>
              <form class="ay-skriv" id="ay-skriv" autocomplete="off"></form>
            </section>
          </div>
          <div class="st-flik" id="st-flik-arbete" role="tabpanel" aria-labelledby="st-tab-arbete"${l.flik === 'arbete' ? '' : ' hidden'}>
            <div class="ay-remsa st-arbete" id="ay-remsa"></div>
            <section class="ay-panel ay-roller" aria-labelledby="ay-roller-rubrik" id="ay-roller"></section>
          </div>
        </aside>`;
      rot.dataset.byggd = '1';
      // ett nytt skelett (studion öppnas igen efter en annan vy): det som hörde till förra skelettets duk och ram gäller inte
      Object.assign(S, { dukNyckel: null, vantandeVersion: null, visaNy: false, kartad: null, visaStruktur: false, struktur: null });
      koppla(rot); kopplaDelare(rot);
      new ResizeObserver(() => skala()).observe(document.getElementById('st-duk'));
    }
    if (A.valdKandidat && A.valdKandidat !== S.kid && kandidater().some((k) => k.id === A.valdKandidat)) { S.kid = A.valdKandidat; S.val = null; S.karta = null; S.provat = {}; }
    if (!S.kid || !kandidater().some((k) => k.id === S.kid)) {
      const v = kandidater().find((k) => k.preview?.finns) || kandidater()[0];
      S.kid = A.valdKandidat && kandidater().some((k) => k.id === A.valdKandidat) ? A.valdKandidat : v?.id || null;
    }
    const k = kandidat();
    // en ny version av samma riktning: tas in direkt, utom när du håller på med något; då erbjuds den i duken (DS-U07)
    const ny = !!(k && S.version && S.versionKid === k.id && S.version !== k.version_hel);
    if (ny && aktiv() && !S.visaNy) S.vantandeVersion = k.version || '?';
    else { if (ny) nyVersion(k); S.version = k?.version_hel || null; S.versionKid = k?.id || null; }
    ritaRemsa(); ritaVerktyg(); ritaDuk(); ritaRef(); ritaKontext();
  }

  // en ny version av den valda kandidaten (ett sparande, ett svar på kritiken, ett uppdrag): duken laddas om, och det
  // markerade elementet väljs igen genom sitt id; ett provat värde som inte sparats står kvar som provat
  function nyVersion(k) {
    S.notis = `Ny version ${k.version}: förhandsvisningen visar den. ${Object.keys(S.provat).length ? 'Dina provade värden står kvar osparade.' : ''}`;
    S.karta = null; S.kartNyckel = null;
  }

  function ritaRemsa() {
    const el = document.getElementById('st-remsa'); if (!el) return;
    const l = AY().A.lage, ks = kandidater();
    const bedombara = ks.filter((k) => ['klar', 'bedombar', 'vald', 'forfinad', 'godkand', 'jamfors'].includes(k.status)).length;
    const begart = l.korning?.antal_begart || l.korning?.antal || null;
    document.getElementById('st-antal').textContent = ks.length ? `${bedombara} av ${begart || ks.length} bedömbara` : '';
    const h = ks.length ? ks.map((k) => {
      const bild = k.snapshot?.['1440'];
      return `<li><button type="button" class="st-riktning" data-st-kid="${e_(k.id)}"${k.id === S.kid ? ' aria-current="true"' : ''}>
        <span class="st-tumme">${bild ? `<img src="/fil/${e_(bild)}" alt="" loading="lazy">` : '<span aria-hidden="true"></span>'}</span>
        <span class="st-riktningstext"><strong>${e_(k.etikett)}</strong><span class="st-status" data-status="${e_(k.status)}">${e_(k.statustext || k.status)}</span>
        ${k.version ? `<span class="svag">version ${e_(k.version)}</span>` : ''}</span></button></li>`;
    }).join('') : '<li class="ay-tom">Inga riktningar i körningen än. De visas här när de blir bedömbara, en i taget.</li>';
    if (el.dataset.html !== h) { el.dataset.html = h; AY().behallFokus(el, () => { el.innerHTML = h; }); }
  }

  function ritaVerktyg() {
    const el = document.getElementById('st-verktyg'); if (!el) return;
    const k = kandidat();
    const visa = visaLage();
    const h = `<div class="ay-segment" role="group" aria-label="Vad som visas">${VISA.map(([v, n]) =>
        `<button type="button" data-st-visa="${v}" data-fokus="st-visa-${v}" aria-pressed="${visa === v}">${n}</button>`).join('')}</div>
      ${visa !== 'arbetsversion' ? '' : `<div class="ay-segment" role="group" aria-label="Klick i förhandsvisningen">${LAGEN.map(([v, n, om]) =>
        `<button type="button" data-st-lage="${v}" data-fokus="st-lage-${v}" aria-pressed="${S.lage === v}" title="${e_(om)}">${n}</button>`).join('')}</div>
      <div class="ay-segment" role="group" aria-label="Visningsbredd">${BREDDER.map(([b, n]) =>
        `<button type="button" data-st-bredd="${b}" data-fokus="st-bredd-${b}" aria-pressed="${S.bredd === b}" title="${b} px">${n}</button>`).join('')}</div>
      <button class="ay-knapp liten" type="button" data-st-struktur data-fokus="st-strukturknapp" aria-expanded="${S.visaStruktur}" aria-controls="st-struktur">Struktur</button>`}
      ${dold('vanster') ? '<button class="ay-knapp liten" type="button" data-st-visa-panel="vanster" data-fokus="st-visa-vanster">Visa riktningarna</button>' : ''}
      ${dold('hoger') ? '<button class="ay-knapp liten" type="button" data-st-visa-panel="hoger" data-fokus="st-visa-hoger">Visa panelen</button>' : ''}`;
    if (el.dataset.html !== h) { el.dataset.html = h; AY().behallFokus(el, () => { el.innerHTML = h; }); }
  }

  const dold = (sida) => document.getElementById('st-rot')?.hasAttribute(sida === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold');
  function fallPanel(sida, dolj) {
    const rot = document.getElementById('st-rot'); if (!rot) return;
    rot.toggleAttribute(sida === 'vanster' ? 'data-vanster-dold' : 'data-hoger-dold', dolj);
    sparaLayout({ [sida === 'vanster' ? 'vansterDold' : 'hogerDold']: dolj });
    ritaVerktyg(); skala();
    (dolj ? document.querySelector(`[data-st-visa-panel="${sida}"]`) : document.querySelector(`[data-st-fall="${sida}"]`))?.focus();
  }
  // avdelarna: dra, eller piltangenterna 24 px åt gången (WAI-ARIA separator med sitt värde från början)
  function kopplaDelare(rot) {
    rot.querySelectorAll('[data-st-delare]').forEach((d) => {
      const sida = d.dataset.stDelare, prop = sida === 'vanster' ? '--st-vanster' : '--st-hoger';
      const [min, max] = sida === 'vanster' ? [160, 420] : [280, 640];
      const nu = () => parseInt(getComputedStyle(rot).getPropertyValue(prop)) || (sida === 'vanster' ? 236 : 360);
      const satt = (px) => { px = Math.max(min, Math.min(max, Math.round(px))); rot.style.setProperty(prop, px + 'px'); d.setAttribute('aria-valuenow', px); sparaLayout({ [sida]: px }); skala(); };
      d.setAttribute('aria-valuemin', min); d.setAttribute('aria-valuemax', max); d.setAttribute('aria-valuenow', nu());
      d.addEventListener('pointerdown', (ev) => {
        ev.preventDefault(); d.setPointerCapture(ev.pointerId);
        const r = rot.getBoundingClientRect();
        const flytta = (e2) => satt(sida === 'vanster' ? e2.clientX - r.left : r.right - e2.clientX);
        d.addEventListener('pointermove', flytta);
        d.addEventListener('pointerup', () => d.removeEventListener('pointermove', flytta), { once: true });
      });
      d.addEventListener('keydown', (ev) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(ev.key)) return;
        ev.preventDefault();
        satt(nu() + ((ev.key === 'ArrowRight') === (sida === 'vanster') ? 24 : -24));
      });
    });
  }

  // duken: kandidatens arbetsversion i exakt den valda bredden; en smalare ruta visar den förminskad (skalan står under),
  // så att sajtens egna brytpunkter gäller och aldrig rutans bredd
  function ritaDuk() {
    const el = document.getElementById('st-duk'); if (!el) return;
    const visa = visaLage() === 'arbetsversion';
    document.getElementById('st-dukram').hidden = !visa;
    document.getElementById('ay-material').hidden = visa;
    const k = kandidat();
    // en riktning som granskas eller arbetar visas med sin bevarade bild: projektets bygge kan bära ett halvt svar
    const levande = !!(k?.preview?.finns && VID_GRANS.includes(k.status));
    const nyckel = JSON.stringify([AY().A.slug, k?.id, levande ? k?.preview?.byggd : k?.snapshot?.version, levande, levande ? 0 : S.bredd <= 768]);
    if (nyckel === S.dukNyckel) { skala(); ritaDukrad(); ritaDukbesked(); return; }
    const forra = S.dukNyckel ? JSON.parse(S.dukNyckel) : null;
    const forraKid = forra ? forra[1] : null;
    if (forra && forraKid === k?.id && forra[3] === levande && aktiv() && !S.visaNy) {  // samma riktning i en ny version: erbjud den
      S.vantandeVersion = k?.version || '?'; ritaDukbesked(); ritaDukrad(); return;
    }
    S.dukNyckel = nyckel; S.vantandeVersion = null; S.visaNy = false; ritaDukbesked();
    if (!k) { el.innerHTML = '<div class="ay-tom">Välj en riktning till vänster.</div>'; ritaDukrad(); return; }
    if (!levande) {
      const b = k.snapshot?.[S.bredd <= 768 ? '390' : '1440'];
      const varfor = k.status === 'bedombar' ? 'bedömbar version, granskningen pågår' : k.preview?.finns ? 'riktningen arbetar' : 'ingen byggd version just nu';
      el.innerHTML = b ? `<img class="st-bild" src="/fil/${e_(b)}" alt="Ögonblicksbild av ${e_(k.etikett)} (${e_(varfor)})">` : '<div class="ay-tom">Riktningen är inte byggd än.</div>';
      ritaDukrad(); return;
    }
    if (forraKid && forraKid !== k.id) { S.val = null; S.karta = null; S.kartNyckel = null; S.provat = {}; S.struktur = null; }
    AY().A.bryggNonce = null; S.kartad = null;
    el.innerHTML = `<iframe title="Förhandsvisning: ${e_(k.etikett)}" src="${e_(k.preview.url)}" sandbox="allow-scripts allow-forms allow-same-origin" referrerpolicy="no-referrer" style="width:${S.bredd}px"></iframe>`;
    skala(); ritaDukrad();
  }
  function ritaDukbesked() {
    const el = document.getElementById('st-dukbesked'); if (!el) return;
    const h = S.vantandeVersion ? `<div class="ay-notis"><b>Ny version ${e_(S.vantandeVersion)} finns.</b> Den visas inte förrän du vill, så att det du håller på med står kvar.
      <button class="ay-knapp liten" type="button" data-st-visa-ny data-fokus="st-visa-ny">Visa den nya versionen</button></div>` : '';
    if (el.dataset.html !== h) { el.dataset.html = h; AY().behallFokus(el, () => { el.innerHTML = h; }); }
  }
  function skala() {
    const el = document.getElementById('st-duk'); const f = el?.querySelector('iframe'); if (!f) return;
    const tillganglig = el.clientWidth - 2, s = Math.min(1, tillganglig / S.bredd);
    f.style.width = S.bredd + 'px'; f.dataset.bredd = String(S.bredd);
    f.style.height = Math.min(6000, Math.max(300, Math.floor((el.clientHeight - 2) / s))) + 'px';  // taket: en duk utan bestämd höjd växer aldrig utan gräns
    f.style.transform = s < 1 ? `scale(${s})` : '';
    S.skala = s; ritaDukrad();
  }
  function ritaDukrad() {
    const el = document.getElementById('st-dukrad'); if (!el) return;
    const k = kandidat();
    const levande = !!(k?.preview?.finns && VID_GRANS.includes(k.status));
    // K6: det som inte är den levande versionen säger varför; en kandidat som arbetar kan ha en arbetsversion som är äldre än arbetet
    const varfor = !k || levande ? '' : k.status === 'bedombar' ? ' · bevarad bild av den bedömbara versionen; granskningen och svaret pågår'
      : k.preview?.finns ? ' · bevarad bild: riktningen arbetar, och arbetsversionen kan vara äldre än arbetet; den levande förhandsvisningen öppnas när den är klar' : ' · ingen byggd version just nu';
    const t = !k ? '' : `${k.etikett}${k.version ? ', version ' + k.version : ''} · ${levande ? S.bredd + ' px' : 'bild'}${levande && S.skala && S.skala < 1 ? ` visas i ${Math.round(S.skala * 100)} %` : ''}${levande ? ' · ' + S.sida : ''}${varfor}`
      + (S.kartad === false ? ' · den här byggda versionen saknar källkarta: kontrollerna kommer när kandidaten byggts om' : '')
      + (S.notis ? ' · ' + S.notis : '');
    if (el.textContent !== t) el.textContent = t;
  }

  function ritaRef() {
    const el = document.getElementById('st-ref'); if (!el) return;
    const r = kandidat()?.referens;
    const h = !r ? '<p class="svag">Ingen huvudreferens är knuten till riktningen.</p>'
      : r.egen ? '<p class="svag">Riktningen bygger på en egen grund, ingen fångad referens.</p>'
      : r.saknas ? `<p class="svag">Referensens bild saknas: ${e_(r.saknas)}.</p>`
      : `<p>${e_(r.namn || 'Huvudreferensen')}, fångad startsida</p>${['1440', '390'].filter((b) => r[b]).map((b) =>
          `<a href="/fil/${e_(r[b])}" target="_blank" rel="noopener"><img src="/fil/${e_(r[b])}" alt="Referensens startsida i ${b} px" loading="lazy"></a><span class="svag">${b} px, bildens egen bredd</span>`).join('')}`;
    if (el.dataset.html !== h) { el.dataset.html = h; el.innerHTML = h; }
  }

  // --- kontextpanelen ---
  function ritaKontext() {
    const el = document.getElementById('st-kontext'); if (!el) return;
    const A = AY().A, l = A.lage || {}, k = kandidat();
    const v = S.val;
    const galler = `<dl class="st-galler">
      <div><dt>Kund</dt><dd>${e_(l.projekt?.namn || A.slug)}${l.projekt?.testdata ? ' <span class="ay-chip">testdata</span>' : ''}</dd></div>
      <div><dt>Körning</dt><dd>${e_(l.korning?.startad ? AY().kort(l.korning.startad) : '–')}</dd></div>
      <div><dt>Riktning</dt><dd>${k ? `${e_(k.etikett)}, version ${e_(k.version || '–')}` : '–'}</dd></div>
      <div><dt>Sida och bredd</dt><dd>${e_(v?.sida || S.sida)}, ${v?.bredd || S.bredd} px</dd></div>
      <div><dt>Markerat</dt><dd>${v ? `${e_(v.del)}${S.karta?.element ? `<br><span class="svag">${e_(S.karta.element.fil)}, rad ${e_(S.karta.element.rad)}${S.karta.element.antal > 1 ? `, ${S.karta.element.antal} förekomster` : ''}</span>` : ''}` : '<span class="svag">inget än: välj Redigera och klicka på en del, eller öppna Struktur</span>'}</dd></div></dl>`;
    let kropp = '';
    const sp = sparrskal();
    if (S.kommentar) kropp = kommentarsformular();
    else if (sp) kropp = `<div class="ay-notis">${e_(sp)}</div>`;
    else if (S.uppdrag) kropp = uppdragskort();
    else if (v && S.kartLaser) kropp = '<p class="svag" role="status">Motorn läser källan och prövar sidan…</p>';
    else if (v && S.kartFel) kropp = `<div class="ay-notis varn">${e_(S.kartFel)}</div>${aiKnapp()}`;
    else if (v && S.karta) kropp = omraden() + sparrad();
    else if (S.lage === 'valj') kropp = '<p class="svag">Klicka på en rubrik, en bild eller en sektion i förhandsvisningen. Kontrollerna visas bara där källan är känd; annat blir ett uppdrag.</p>';
    kropp += foljning();
    const gilla = k && k.snapshot?.['1440'] ? `<div class="ay-knapprad st-gilla"><button class="ay-knapp liten" type="button" data-st-gilla data-fokus="st-gilla"${S.gillar === k.id + k.version_hel ? ' aria-pressed="true"' : ''}>${S.gillar === k.id + k.version_hel ? 'Du gillar den här versionen' : 'Gilla riktningen'}</button>
      <span class="svag">Ett gillande startar inget och ändrar inte de andra riktningarna; det står som en kommentar till versionen.</span></div>` : '';
    const h = galler + gilla + kropp;
    if (el.dataset.html === h) return;
    el.dataset.html = h;
    AY().behallFokus(el, () => { el.innerHTML = h; });
  }
  const tal = (v) => { const m = String(v ?? '').match(/^(-?\d*\.?\d+)(px|rem|em|ch|%|vw|vh)?$/); return m ? { n: Number(m[1]), enhet: m[2] || '' } : null; };
  // färgrutans startvärde: källans hex, annars det beräknade värdet (rgb) som hex; genomskinligt ger ingen färg
  function hexAv(v) {
    if (/^#[0-9a-f]{6}$/i.test(String(v))) return String(v);
    const m = String(v || '').match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/);
    if (!m || (m[4] !== undefined && Number(m[4]) === 0)) return null;
    return '#' + [m[1], m[2], m[3]].map((x) => Number(x).toString(16).padStart(2, '0')).join('');
  }
  function falt(c) {
    const id = 'st-f-' + c.id.replace(/[^a-z0-9]/gi, '-');
    const nu = c.id in S.provat ? S.provat[c.id] : (c.varde ?? '');
    const etikett = `<label for="${id}">${e_(c.etikett)}</label>`;
    if (c.typ === 'ordning') {
      const ordning = S.provat[c.id] || c.varde.map((_, i) => i);
      return `<div class="st-falt st-ordning">${etikett}<ol>${ordning.map((i, p) => `<li><span>${e_(c.varde[i])}${c.markerad === i ? ' <span class="svag">(markerad)</span>' : ''}</span>
        <span class="st-flytta"><button class="ay-ikon" type="button" data-st-flytta="${p}" data-steg="-1" data-fokus="st-upp-${p}" aria-label="Flytta ${e_(c.varde[i])} upp"${p === 0 ? ' disabled' : ''}>↑</button>
        <button class="ay-ikon" type="button" data-st-flytta="${p}" data-steg="1" data-fokus="st-ned-${p}" aria-label="Flytta ${e_(c.varde[i])} ned"${p === ordning.length - 1 ? ' disabled' : ''}>↓</button></span></li>`).join('')}</ol>
        <input type="hidden" id="${id}"></div>`;
    }
    let input;
    if (c.val && c.val.length) {
      const tok = /^var\(/.test(String(nu)) ? `<option value="${e_(nu)}" selected>${e_(nu)} (token)</option>` : '';
      input = `<select id="${id}" data-st-kontroll="${e_(c.id)}" data-fokus="${id}">${(c.ny && !(c.id in S.provat) ? ['<option value="">(ingen egen)</option>'] : []).join('')}${tok}${c.val.map((x) =>
        `<option value="${e_(x)}"${String(nu) === String(x) ? ' selected' : ''}>${e_(x)}</option>`).join('')}</select>`;
    } else if (c.typ === 'farg') {
      const hex = hexAv(nu) || hexAv(c.berakn) || '';
      input = `<span class="st-farg"><input type="color" aria-label="${e_(c.etikett)}: välj färg" data-st-farg="${e_(c.id)}" value="${e_(hex || '#000000')}"${hex ? '' : ' data-tom'}>
        <input type="text" id="${id}" data-st-kontroll="${e_(c.id)}" data-fokus="${id}" value="${e_(nu)}" placeholder="${e_(c.berakn || '')}" spellcheck="false"></span>`;
    } else if (c.typ === 'fokus') {
      const m = String(nu).match(/^(\d+(?:\.\d)?)% (\d+(?:\.\d)?)%$/) || [null, 50, 50];
      input = `<span class="st-fokus"><label>X <input type="number" min="0" max="100" step="1" data-st-fokus="x" data-st-kontrollid="${e_(c.id)}" value="${e_(m[1])}" aria-label="Fokuspunkt vågrätt i procent"></label>
        <label>Y <input type="number" min="0" max="100" step="1" data-st-fokus="y" data-st-kontrollid="${e_(c.id)}" value="${e_(m[2])}" aria-label="Fokuspunkt lodrätt i procent"></label>
        <input type="hidden" id="${id}" data-st-kontroll="${e_(c.id)}" value="${e_(nu)}"></span>`;
    } else if (c.typ === 'text') {
      input = `<textarea id="${id}" data-st-kontroll="${e_(c.id)}" data-fokus="${id}" rows="2" maxlength="500">${e_(nu)}</textarea>`;
    } else {
      const t = tal(nu);
      const max = t ? (t.enhet === 'px' ? Math.max(200, t.n * 3) : t.enhet === 'rem' || t.enhet === 'em' ? Math.max(10, t.n * 3) : t.enhet === 'ch' ? 120 : 100) : 0;
      input = `<span class="st-langd"><input type="text" id="${id}" data-st-kontroll="${e_(c.id)}" data-fokus="${id}" value="${e_(nu)}" placeholder="${e_(c.berakn || '')}" spellcheck="false" inputmode="decimal">
        ${t ? `<input type="range" aria-label="${e_(c.etikett)}, dra eller använd piltangenterna" data-st-reglage="${e_(c.id)}" data-enhet="${e_(t.enhet)}" min="0" max="${max}" step="${t.enhet === 'px' ? 1 : 0.05}" value="${t.n}">` : ''}</span>`;
    }
    const osparat = c.id in S.provat;
    const kalla = c.kalla ? `<span class="st-kalla">${e_(c.kalla.fil)}${c.kalla.rad ? ', rad ' + e_(c.kalla.rad) : ''}${c.kalla.valjare ? ' · ' + e_(c.kalla.valjare) : ''}</span>` : '';
    const rv = c.rackvidd ? `<span class="st-rackvidd" data-slag="${e_(c.rackvidd.slag)}" title="${e_(c.rackvidd.text)}">${e_(RACKVIDD[c.rackvidd.slag] || c.rackvidd.slag)}${c.rackvidd.responsiv ? ' · ' + e_(c.rackvidd.responsiv) : ''}</span>` : '';
    return `<div class="st-falt${osparat ? ' st-osparat' : ''}">${etikett}${input}
      <div class="st-faltinfo">${rv}${kalla}${c.berakn && c.typ !== 'text' ? `<span class="svag">nu ${e_(c.berakn)}</span>` : ''}${osparat ? '<span class="st-osparad">Osparat</span>' : ''}</div>
      ${c.rackvidd?.slag && !['objekt', 'forekomster'].includes(c.rackvidd.slag) ? `<p class="svag st-rvtext">${e_(c.rackvidd.text)}</p>` : ''}</div>`;
  }
  function omraden() {
    const om = S.karta.omraden || {};
    const delar = OMRADEN.filter(([k]) => om[k]?.length).map(([k, namn]) => {
      const alla = om[k].filter((c) => c.stod);
      const alternativ = (c) => alla.filter((x) => x.id === c.id + '/token' || x.id === c.id + '/arvd');
      const ar_alt = (c) => /\/(token|arvd)$/.test(c.id) && alla.some((x) => x.id === c.id.replace(/\/(token|arvd)$/, ''));
      const st = alla.filter((c) => !ar_alt(c)), ej = om[k].filter((c) => !c.stod && !c.ai);
      const ai = om[k].some((c) => c.ai);
      const andrade = st.filter((c) => c.id in S.provat).length;
      return `<details class="st-omrade" data-omrade="${k}"${st.length ? ' open' : ''}><summary>${namn}${andrade ? ` <span class="st-osparad">${andrade} osparade</span>` : ''}${!st.length ? ' <span class="svag">ingen säker källa</span>' : ''}</summary>
        ${st.map((c) => falt(c) + alternativ(c).map((x) => `<details class="st-alt"${x.id in S.provat ? ' open' : ''}><summary>${x.rackvidd?.slag === 'arvd'
          ? 'Ändra där värdet ärvs i stället' : `Ändra i designgrunden i stället: ${e_(x.token || '')}`} <span class="svag">${e_(x.rackvidd?.text || '')}</span></summary>${falt(x)}</details>`).join('')).join('')}
        ${ej.length ? `<ul class="st-ejstod">${ej.map((c) => `<li><b>${e_(c.etikett)}</b>: ${e_(c.skal)}</li>`).join('')}</ul>` : ''}
        ${ai ? aiKnapp() : ''}</details>`;
    }).join('');
    const k = S.karta.element || {};
    const kontrast = k.kontrast?.kvot ? `<p class="svag">Kontrast mot ytan: ${e_(k.kontrast.kvot)}:1${k.kontrast.kvot < 4.5 ? ' — under 4,5:1 för brödtext' : ''}</p>` : '';
    return `<div class="st-omraden">${delar || '<p class="svag">Inget i det markerade har en säker källa för direkta ändringar.</p>' + aiKnapp()}</div>${kontrast}`;
  }
  const aiKnapp = () => '<div class="ay-knapprad"><button class="ay-knapp liten" type="button" data-st-ai data-fokus="st-ai">Be om en annan komposition (uppdrag)</button></div>';
  function sparrad() {
    const n = Object.keys(S.provat).length;
    if (!n && !S.sparar) return '';
    return `<div class="st-sparrad" role="group" aria-label="Provade värden">
      <p><b>${n} provade ${n === 1 ? 'värde' : 'värden'}</b>, osparade: de syns bara här i förhandsvisningen. Spara skriver dem i kandidatens källa; kandidaten byggs om, fotograferas och kontrolleras, och resultatet blir dess nästa version.</p>
      <div class="ay-knapprad"><button class="ay-knapp primar liten" type="button" data-st-spara data-fokus="st-spara"${S.sparar || !n ? ' aria-disabled="true"' : ''}>Spara i källan</button>
      <button class="ay-knapp liten" type="button" data-st-aterstall data-fokus="st-aterstall"${n ? '' : ' aria-disabled="true"'}>Återställ provade värden</button></div></div>`;
  }
  function foljning() {
    const lista = (AY().A.lage?.studio || []).filter((x) => x.kandidat === S.kid).slice(-3).reverse();
    if (!lista.length) return '';
    return `<section class="st-foljning" aria-labelledby="st-andringar"><h3 id="st-andringar">Dina ändringar</h3><ul>${lista.map((x) => `<li data-status="${e_(x.status)}">
      <b>${e_(STATUS[x.status] || x.status)}</b>: ${(x.andringar || []).map((a) => `${e_(a.etikett)} ${e_(Array.isArray(a.efter) ? a.efter.join(', ') : a.efter)}`).join('; ')}
      ${x.skal && x.status !== 'koad' ? `<br><span class="svag">${e_(x.skal)}</span>` : ''}</li>`).join('')}</ul></section>`;
  }
  function kommentarsformular() {
    const c = S.kommentar;
    return `<form class="st-kommentar" data-st-kommentarform>
      <h3>Kommentar på ${e_(c.del)}</h3>
      <p class="svag">Bunden till ${e_(kandidat()?.etikett)} version ${e_(kandidat()?.version)}, ${c.bredd} px, sidan ${e_(c.sida)}. En kommentar startar inget arbete; du samlar kommentarer till ett uppdrag när du vill.</p>
      <label for="st-kommentartext">Kommentar</label><textarea id="st-kommentartext" rows="3" maxlength="4000" required data-fokus="st-kommentartext">${e_(c.text || '')}</textarea>
      <div class="ay-knapprad"><button class="ay-knapp primar liten" type="submit" data-fokus="st-kommentarspara"${c.sparar ? ' aria-disabled="true"' : ''}>Spara kommentaren</button><button class="ay-knapp liten" type="button" data-st-kommentarstang>Avbryt</button></div>
      ${c.fel ? `<p class="ay-notis varn">${e_(c.fel)}</p>` : ''}${c.sparad ? '<p class="ay-notis">Sparad. Den står med sin version i Förslagen och i portalen.</p>' : ''}</form>`;
  }
  function uppdragskort() {
    const u = S.uppdrag;
    return `<form class="st-uppdrag" data-st-uppdragform>
      <h3>Uppdrag till utföraren</h3>
      <p class="svag">${e_(kandidat()?.etikett)} version ${e_(kandidat()?.version)}. Uppdraget sparas genom ändringsvägen och startas med flödets ordinarie start, med samma operations-id i båda.</p>
      <label for="st-utyp">Typ</label><select id="st-utyp" name="typ">${[['omarbeta', 'Omarbeta designen'], ['ratta', 'Rätta'], ['bygg_ut', 'Bygg ut']].map(([v, n]) => `<option value="${v}"${u.typ === v ? ' selected' : ''}>${n}</option>`).join('')}</select>
      <label for="st-uresultat">Önskat resultat</label><textarea id="st-uresultat" name="resultat" rows="3" required data-fokus="st-uresultat">${e_(u.resultat || '')}</textarea>
      <label for="st-uomfattning">Omfattning</label><textarea id="st-uomfattning" name="omfattning" rows="2" required>${e_(u.omfattning || '')}</textarea>
      <label for="st-ubevara">Det som ska bevaras</label><textarea id="st-ubevara" name="bevara" rows="2" required>${e_(u.bevara || '')}</textarea>
      <div class="ay-knapprad"><button class="ay-knapp primar liten" type="submit"${u.skickar ? ' aria-disabled="true"' : ''}>Spara och starta uppdraget</button><button class="ay-knapp liten" type="button" data-st-uppdragstang>Avbryt</button></div>
      ${u.fel ? `<p class="ay-notis varn">${e_(u.fel)}</p>` : ''}${u.klart ? `<p class="ay-notis">${e_(u.klart)}</p>` : ''}</form>`;
  }

  // --- kartan och de provade värdena ---
  async function hamtaKarta() {
    const A = AY().A, v = S.val, k = kandidat(); if (!v || !k) return;
    const q = new URLSearchParams({ kandidat: k.id, sida: v.sida, bredd: String(v.bredd), k: v.k, instans: String(v.instans || 0) });
    if (v.barn) q.set('barn', v.barn);
    const nyckel = q.toString() + '|' + k.version_hel;
    if (nyckel === S.kartNyckel && S.karta) return;
    S.kartNyckel = nyckel; S.kartLaser = true; S.kartFel = null; ritaKontext();
    try {
      const d = await AY().hamta('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/studio/karta?' + q);
      if (S.kartNyckel !== nyckel) return;
      if (!d.ok) { S.karta = null; S.kartFel = d.skal; } else { S.karta = d; }
    } catch (err) { if (S.kartNyckel === nyckel) S.kartFel = 'kartan kunde inte läsas: ' + err.message; }
    finally { if (S.kartNyckel === nyckel) { S.kartLaser = false; ritaKontext(); } }
  }
  function kontroller() { return Object.values(S.karta?.omraden || {}).flat(); }
  function provcss() {
    const ut = [];
    for (const c of kontroller()) {
      if (!(c.id in S.provat) || !c.prova?.valjare) continue;
      let v = S.provat[c.id];
      if (c.prova.varden) { const vals = [...c.prova.varden]; vals[c.prova.index] = v; v = vals.join(' '); }
      if (!/^[^;{}<>\\"`@]{1,120}$/.test(String(v))) continue;  // bara ett värde, som motorn senare prövar igen
      let css = `${c.prova.valjare}{${c.prova.egenskap}:${v} !important}`;
      for (const r of [...(c.prova.ram || [])].reverse()) css = `${r}{${css}}`;
      ut.push(css);
    }
    return ut.join('\n');
  }
  function provaNu() {
    const css = provcss();
    AY().brygga(css ? { typ: 'prova', css } : { typ: 'prova-rensa' });
  }
  function satt(id, v) {
    const c = kontroller().find((x) => x.id === id); if (!c) return;
    if (v === '' || v === null || (c.varde !== null && String(v) === String(c.varde) && c.typ !== 'ordning')) delete S.provat[id]; else S.provat[id] = v;
    provaNu(); ritaKontext();
  }

  async function spara() {
    const A = AY().A, k = kandidat(), v = S.val; if (!k || !v || S.sparar) return;
    const andringar = Object.entries(S.provat).map(([kontroll, varde]) => ({ kontroll, varde }));
    if (!andringar.length) return;
    const rid = await AY().innehallsId('s', [A.slug, k.id, k.version_hel, v.k, v.instans, v.barn, v.sida, v.bredd, andringar]);
    S.sparar = rid; ritaKontext();
    try {
      const svar = await AY().postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/studio', { andring_id: rid, kandidat: k.id, version: k.version_hel,
        korning: A.lage.korning?.startad || '', sida: v.sida, bredd: v.bredd, k: v.k, instans: v.instans || 0, barn: v.barn || null, del: v.del, andringar });
      S.senast = svar;
      // värdena står nu i begäran: de räknas inte längre som osparade, och duken visar dem tills den ombyggda versionen kommer
      S.provat = {};
      AY().meddela('Ändringen är begärd: den skrivs i källan, och kandidaten byggs om, fotograferas och kontrolleras.');
    } catch (err) {
      S.kartFel = (err.status === 409 ? 'Inaktuell: ' : err.status === 422 ? '' : 'Svaret gick inte att bekräfta: ') + err.message
        + (err.status && err.status < 500 ? '' : '. Försök igen: samma ändring ger samma id, så den görs inte två gånger.');
    } finally { S.sparar = null; ritaKontext(); }
  }

  // --- händelserna ---
  function koppla(rot) {
    rot.addEventListener('click', (ev) => {
      const t = ev.target.closest('button, a'); if (!t || t.getAttribute('aria-disabled') === 'true') return;
      if (t.dataset.stKid) { if (S.kid !== t.dataset.stKid) { S.kid = t.dataset.stKid; AY().A.valdKandidat = S.kid; S.val = null; S.karta = null; S.provat = {}; S.notis = null; } rita(AY().A); return; }
      if (t.dataset.stVisa) { AY().A.material = t.dataset.stVisa === 'arbetsversion' ? 'forhandsvisning' : t.dataset.stVisa; rita(AY().A); AY().ritaMaterial(); return; }
      if (t.dataset.stFlik) { valjFlik(t.dataset.stFlik); return; }
      if (t.dataset.stLage) { S.lage = t.dataset.stLage; sparaLayout({ lage: S.lage }); AY().brygga({ typ: 'lage', lage: S.lage }); ritaVerktyg(); ritaKontext(); return; }
      if (t.dataset.stBredd) { S.bredd = Number(t.dataset.stBredd); sparaLayout({ bredd: S.bredd }); if (S.val) S.val.bredd = S.bredd; S.kartNyckel = null; ritaVerktyg(); ritaDuk(); skala(); if (S.val) hamtaKarta(); document.querySelector(`[data-fokus="st-bredd-${S.bredd}"]`)?.focus(); return; }
      if (t.hasAttribute('data-st-struktur')) { S.visaStruktur = !S.visaStruktur; document.getElementById('st-struktur').hidden = !S.visaStruktur; if (S.visaStruktur) AY().brygga({ typ: 'struktur' }); ritaVerktyg(); return; }
      if (t.dataset.stValjK !== undefined) { AY().brygga({ typ: 'valj-k', k: t.dataset.k, instans: Number(t.dataset.instans), barn: t.dataset.barn || null }); return; }
      if (t.hasAttribute('data-st-spara')) { spara(); return; }
      if (t.hasAttribute('data-st-aterstall')) { S.provat = {}; AY().brygga({ typ: 'prova-rensa' }); ritaKontext(); AY().meddela('De provade värdena är återställda.'); return; }
      if (t.dataset.stFlytta !== undefined) {
        const c = kontroller().find((x) => x.typ === 'ordning'); if (!c) return;
        const o = [...(S.provat[c.id] || c.varde.map((_, i) => i))], p = Number(t.dataset.stFlytta), q = p + Number(t.dataset.steg);
        if (q < 0 || q >= o.length) return;
        [o[p], o[q]] = [o[q], o[p]];
        satt(c.id, o.join() === c.varde.map((_, i) => i).join() ? '' : o);
        document.querySelector(`[data-fokus="st-${Number(t.dataset.steg) < 0 ? 'upp' : 'ned'}-${q}"]`)?.focus();
        return;
      }
      if (t.hasAttribute('data-st-ai')) {
        const v = S.val; const k = kandidat();
        S.uppdrag = { typ: 'omarbeta', resultat: '', omfattning: v ? `${v.del} på sidan ${v.sida} (${k?.etikett} version ${k?.version})` : '', bevara: 'innehållet, kundens bilder och det som inte nämns här' };
        ritaKontext(); document.getElementById('st-uresultat')?.focus(); return;
      }
      if (t.hasAttribute('data-st-uppdragstang')) { S.uppdrag = null; ritaKontext(); return; }
      if (t.hasAttribute('data-st-kommentarstang')) { S.kommentar = null; ritaKontext(); return; }
      if (t.hasAttribute('data-st-visa-ny')) { S.visaNy = true; S.dukNyckel = null; rita(AY().A); document.getElementById('st-duk')?.focus(); return; }
      if (t.dataset.stFall) { fallPanel(t.dataset.stFall, true); return; }
      if (t.dataset.stVisaPanel) { fallPanel(t.dataset.stVisaPanel, false); return; }
      if (t.hasAttribute('data-st-gilla')) { gilla(); return; }
    });
    rot.addEventListener('input', (ev) => {
      const t = ev.target;
      if (t.dataset.stKontroll && t.type !== 'hidden') { satt(t.dataset.stKontroll, t.value.trim()); return; }
      if (t.dataset.stReglage) { const v = String(Math.round(Number(t.value) * 100) / 100) + (t.dataset.enhet || ''); const f = document.querySelector(`[data-st-kontroll="${CSS.escape(t.dataset.stReglage)}"]`); if (f) f.value = v; satt(t.dataset.stReglage, v); return; }
      if (t.dataset.stFarg) { const f = document.querySelector(`[data-st-kontroll="${CSS.escape(t.dataset.stFarg)}"]`); if (f) f.value = t.value; satt(t.dataset.stFarg, t.value); return; }
      if (t.dataset.stFokus) {
        const id = t.dataset.stKontrollid; const x = document.querySelector(`[data-st-fokus="x"][data-st-kontrollid="${CSS.escape(id)}"]`), y = document.querySelector(`[data-st-fokus="y"][data-st-kontrollid="${CSS.escape(id)}"]`);
        satt(id, `${Math.max(0, Math.min(100, Number(x.value) || 0))}% ${Math.max(0, Math.min(100, Number(y.value) || 0))}%`);
      }
    });
    rot.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      if (ev.target.matches('[data-st-kommentarform]')) await sparaKommentar();
      if (ev.target.matches('[data-st-uppdragform]')) await sparaUppdrag(new FormData(ev.target));
    });
    rot.addEventListener('keydown', (ev) => {
      const f = ev.target.closest?.('[data-st-flik]');
      if (f && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(ev.key)) {
        const alla = ['andra', 'samtal', 'arbete'], i = alla.indexOf(f.dataset.stFlik);
        valjFlik(alla[ev.key === 'Home' ? 0 : ev.key === 'End' ? 2 : (i + (ev.key === 'ArrowRight' ? 1 : 2)) % 3]); ev.preventDefault();
      }
    });
    rot.addEventListener('keydown', (ev) => {  // strukturlistan: piltangenter mellan elementen
      const t = ev.target; if (!t.dataset || t.dataset.stValjK === undefined || !['ArrowDown', 'ArrowUp'].includes(ev.key)) return;
      const alla = [...document.querySelectorAll('[data-st-valj-k]')]; const i = alla.indexOf(t);
      alla[Math.max(0, Math.min(alla.length - 1, i + (ev.key === 'ArrowDown' ? 1 : -1)))]?.focus(); ev.preventDefault();
    });
  }

  function valjFlik(k) {
    sparaLayout({ flik: k });
    document.querySelectorAll('[data-st-flik]').forEach((b) => { const ja = b.dataset.stFlik === k; b.setAttribute('aria-selected', String(ja)); b.tabIndex = ja ? 0 : -1; });
    ['andra', 'samtal', 'arbete'].forEach((x) => { const p = document.getElementById('st-flik-' + x); if (p) p.hidden = x !== k; });
    document.getElementById('st-tab-' + k)?.focus();
  }
  async function sparaKommentar() {
    const A = AY().A, c = S.kommentar, k = kandidat(); if (!c || !k || c.sparar) return;
    c.text = document.getElementById('st-kommentartext')?.value || '';
    c.sparar = true; c.fel = null; ritaKontext();
    try {
      await AY().postJson('/api/desktop/kommentarer/' + encodeURIComponent(A.slug), { handling: 'ny', id: c.id, kandidat: k.id, version: k.version_hel, text: c.text,
        element: { k: c.k, instans: c.instans || 0, barn: c.barn || null, sida: c.sida, bredd: c.bredd, del: c.del }, x: c.punkt?.x ?? null, y: c.punkt?.y ?? null });
      c.sparad = true; AY().meddela('Kommentaren är sparad med sin version.');
    } catch (err) { c.fel = err.message; } finally { c.sparar = false; ritaKontext(); }
  }
  // gilla: en kommentar på versionens bevarade bild i dator-bredd (desktop.kommentar), inget beslut och ingen start (DS-U28)
  async function gilla() {
    const A = AY().A, k = kandidat(); if (!k || !k.snapshot?.['1440'] || S.gillar === k.id + k.version_hel) return;
    try {
      await AY().postJson('/api/desktop/kommentarer/' + encodeURIComponent(A.slug), { handling: 'ny', id: crypto.randomUUID(), kandidat: k.id, version: k.version_hel,
        bredd: '1440', bild: k.snapshot['1440'], bild_sha: k.snapshot.sha?.['1440'], text: 'Jag gillar den här riktningen.' });
      S.gillar = k.id + k.version_hel; AY().meddela(`Du gillar ${k.etikett}. Det står som en kommentar till versionen; de andra riktningarna fortsätter som planerat.`);
    } catch (err) { AY().meddela('Gillandet sparades inte: ' + err.message); }
    ritaKontext();
  }
  async function sparaUppdrag(fd) {
    const A = AY().A, k = kandidat(), u = S.uppdrag; if (!k || !u || u.skickar) return;
    Object.assign(u, { typ: fd.get('typ'), resultat: String(fd.get('resultat') || '').trim(), omfattning: String(fd.get('omfattning') || '').trim(), bevara: String(fd.get('bevara') || '').trim() });
    u.skickar = true; u.fel = null; ritaKontext();
    try {
      const opid = await AY().innehallsId('g', [A.slug, k.id, k.version_hel, u.typ, u.resultat, u.omfattning, u.bevara]);
      await AY().postJson('/api/arbetsyta/' + encodeURIComponent(A.slug) + '/andring', { andring_id: opid, kandidat: k.id, version: k.version_hel, korning: A.lage.korning?.startad || '',
        text: u.resultat, beslut: 'uppdrag', uppdrag: { typ: u.typ, resultat: u.resultat, omfattning: u.omfattning, bevara: u.bevara }, vy: 'studio', sida: S.val?.sida, del: S.val?.del });
      await AY().postJson('/api/flode/' + encodeURIComponent(A.slug) + '/start', { handling: 'valda', start_id: opid });
      u.klart = 'Uppdraget är sparat och startat. Följ det under Byggflöde; den nya versionen visas här när den är bedömbar.';
    } catch (err) { u.fel = (err.status === 409 ? 'Inaktuell: ' : '') + err.message; } finally { u.skickar = false; ritaKontext(); }
  }

  // --- bryggan (arbetsyta.js tar emot meddelandena och prövar ram, ursprung och nonce först) ---
  function redo() { AY().brygga({ typ: 'lage', lage: S.lage }); }
  function kartad(b) {
    S.kartad = b; ritaDukrad();
    if (S.val) AY().brygga({ typ: 'visa-k', k: S.val.k, instans: S.val.instans, barn: S.val.barn });
    if (Object.keys(S.provat).length) provaNu();
    if (S.visaStruktur) AY().brygga({ typ: 'struktur' });
  }
  function meddelande(d) {
    const kalla = d.kalla && /^[0-9a-f]{12}$/.test(d.kalla.k || '') ? d.kalla : null;
    const del = `${d.tagg || 'element'} "${String(d.text || '').slice(0, 50)}"${d.rubrik ? ' under "' + String(d.rubrik).slice(0, 60) + '"' : ''}`;
    const sida = /^\/[a-z0-9/_-]{0,200}$/i.test(String(d.sida || '')) ? String(d.sida) : '/';
    if (d.typ === 'valt' && S.lage === 'valj' && kalla && !kanRedigera()) { ritaKontext(); return; }
    if (d.typ === 'valt' && S.lage === 'valj' && kalla) {
      if (Object.keys(S.provat).length && S.val && S.val.k !== kalla.k) { S.provat = {}; AY().brygga({ typ: 'prova-rensa' }); }
      S.val = { k: kalla.k, instans: Number(kalla.instans) || 0, barn: kalla.barn || null, sida, bredd: S.bredd, del };
      S.kommentar = null; S.uppdrag = null; S.notis = null; S.sida = sida;
      hamtaKarta(); return;
    }
    if (d.typ === 'kommentar-punkt' && S.lage === 'kommentera' && kalla) {
      S.kommentar = { id: crypto.randomUUID(), k: kalla.k, instans: kalla.instans, barn: kalla.barn, sida, bredd: S.bredd, del, punkt: d.punkt || null };
      S.uppdrag = null; ritaKontext(); document.getElementById('st-kommentartext')?.focus(); return;
    }
    if (d.typ === 'markerat' && S.lage === 'markera') {
      AY().markera({ kandidat: S.kid, sida, del });
      AY().meddela('Markerat i förhandsvisningen: ' + del + ' på ' + sida + '. Det står på raden Gäller i samtalet (fliken Samtal).');
      return;
    }
    if (d.typ === 'ej-kalla') { S.kartFel = 'Det du klickade på har ingen känd källa i kandidaten (till exempel en del som ett paket ritar). Välj ett element runt det, eller be om ett uppdrag.'; S.val = { k: '', sida, bredd: S.bredd, del }; S.karta = null; ritaKontext(); return; }
    if (d.typ === 'struktur' && Array.isArray(d.lista)) { S.struktur = d.lista.slice(0, 400); ritaStruktur(); return; }
    if (d.typ === 'provat' && d.ok === false) AY().meddela('Förhandsvisningen kunde inte visa det provade värdet.');
  }
  function ritaStruktur() {
    const el = document.getElementById('st-struktur'); if (!el) return;
    const lista = S.struktur || [];
    el.innerHTML = `<h3>Struktur <span class="svag">(piltangenterna flyttar, Enter väljer)</span></h3><ul>${lista.map((x) =>
      `<li style="--djup:${Number(x.djup) || 0}"><button type="button" data-st-valj-k data-k="${e_(x.k)}" data-instans="${Number(x.instans) || 0}"${x.bild ? ' data-barn="img:0"' : ''}>
        <span class="st-tagg">${e_(x.tagg)}</span> ${e_(x.text || '')}</button></li>`).join('')}</ul>`;
  }

  window.NortropicStudio = { rita, redo, kartad, meddelande, visaFlik: (k) => { if (document.getElementById('st-flik-' + k)) valjFlik(k); } };
})();
