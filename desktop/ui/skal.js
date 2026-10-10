// Skalet: det appen visar innan motorns arbetsyta öppnas och när den inte kan öppnas (kunskap/desktop.md, Skalet).
// Allt går genom appens namngivna kommandon; skalet når aldrig motorn själv.
'use strict';
const { invoke } = window.__TAURI__.core;
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let D = null, vald = null, puls = null;

const MOTORTEXT = {
  verifierad: 'Motorn är verifierad',
  stoppad: 'Motorn är stoppad',
  fel_instans: 'Fel process på porten',
  inkompatibel: 'Motorn har en annan version',
  rot_saknas: 'Motorn hittas inte',
  ej_registrerad: 'Ingen motor vald',
};
const ORSAK = {
  last: 'Nortropic är låst. Lås upp för att fortsätta arbetet.',
  utloggad: 'Du har loggat ut. Lås upp för att fortsätta.',
  tidsgrans: 'Nortropic låstes efter en stund utan aktivitet. Arbetet i motorn fortsätter som förut.',
  vila: 'Nortropic låstes efter vila: datorn sov längre än låstiden. Arbetet i motorn fortsätter som förut.',
};

function visaVy(namn) {
  document.querySelectorAll('.vy').forEach((v) => { v.hidden = v.dataset.vy !== namn; });
  if (vald !== namn) { vald = namn; document.querySelector(`[data-vy="${namn}"] h1`)?.focus?.(); $('#yta').focus({ preventScroll: true }); }
}

function prick(klass, text) { return `<span><i class="prick ${klass}" aria-hidden="true"></i>${esc(text)}</span>`; }

function statusrad(d) {
  const m = d.motor || {}; const ok = m.lage === 'verifierad';
  return prick(ok ? 'ok' : m.lage === 'stoppad' ? 'av' : 'fel', MOTORTEXT[m.lage] || 'Motorns läge okänt')
    + (d.natet?.nar == null ? prick('av', 'Internet prövas') : prick(d.natet.nar ? 'ok' : 'fel', d.natet.nar ? 'Internet nås' : 'Internet nås inte (motorn kan ändå visa sparat arbete)'))
    + prick(d.upplast ? 'ok' : 'av', d.upplast ? 'Upplåst' : 'Låst');
}

function ritaRail(d) { $('#rail-status').innerHTML = statusrad(d); }

async function diagnosLas() { D = await invoke('diagnos'); ritaRail(D); return D; }

async function borja() {
  clearInterval(puls);
  let d;
  try { d = await diagnosLas(); } catch (e) { $('#t-laddar').textContent = 'Appen kunde inte läsa sitt läge'; return; }
  const h = location.hash;
  if (!d.installningar.rot) return forsta(d);
  if (h.startsWith('#diagnos') || h.startsWith('#hjalp')) return diagnos(d);
  if (!d.upplast) return last(d, decodeURIComponent((h.match(/^#last=([^&]*)/) || [])[1] || 'last'));
  if (d.motor.lage === 'verifierad' && !h.startsWith('#franKopplad')) {
    try { const r = await invoke('oppna_arbetsytan', { till: null }); if (r.oppnad) return; } catch (e) { $('#motor-svar').textContent = String(e); }
  }
  return motorvy(d);
}

function forsta(d) {
  visaVy('forsta');
  const rot = d.rotforslag || '';
  $('#forsta-rot').textContent = rot || 'Ingen motor hittades på standardplatsen (~/nortropic-repos/nortropic-webb-pro).';
  $('#forsta-rot').dataset.rot = rot;
  const v = d.upptackta_verktyg || {};
  $('#forsta-verktyg').innerHTML = [['claude', 'Claude Code'], ['node', 'Node']].map(([k, n]) =>
    `<li><span class="etikett">${n}</span>${v[k] ? `<span class="sokvag">${esc(v[k])}</span>` : '<span class="fel">hittades inte på de kända platserna</span>'}</li>`).join('');
  $('#registrera').disabled = !rot;
}

$('#valj-rot').addEventListener('click', async () => {
  $('#forsta-rotfel').hidden = true;
  try { const r = await invoke('valj_motorrot'); if (r) { $('#forsta-rot').textContent = r; $('#forsta-rot').dataset.rot = r; $('#registrera').disabled = false; } }
  catch (e) { $('#forsta-rotfel').textContent = String(e); $('#forsta-rotfel').hidden = false; }
});

$('#registrera').addEventListener('click', async () => {
  const knapp = $('#registrera'); knapp.disabled = true; $('#forsta-svar').textContent = 'Registrerar…';
  try {
    await invoke('registrera_motor', { rot: $('#forsta-rot').dataset.rot, port: Number($('#forsta-port').value) });
    $('#forsta-svar').textContent = 'Motorn är registrerad.';
    location.hash = '#last=last'; await borja();
  } catch (e) { $('#forsta-svar').textContent = String(e); knapp.disabled = false; }
});

function last(d, orsak) {
  visaVy('last');
  $('#last-orsak').textContent = ORSAK[orsak] || ORSAK.last;
  $('#last-status').innerHTML = statusrad(d);
  puls = setInterval(async () => { try { $('#last-status').innerHTML = statusrad(await diagnosLas()); } catch { /* nästa gång */ } }, 5000);
}

$('#las-upp').addEventListener('click', async () => {
  const k = $('#las-upp'); k.disabled = true; $('#last-svar').hidden = true;
  try {
    const r = await invoke('las_upp');
    if (!r.oppnad) { clearInterval(puls); location.hash = '#motor'; await diagnosLas(); motorvy(D); }
  } catch (e) { $('#last-svar').textContent = String(e); $('#last-svar').hidden = false; }
  k.disabled = false;
});

async function motorvy(d) {
  visaVy('motor');
  const m = d.motor || {};
  const text = {
    stoppad: 'Den lokala motorn är stoppad. Det påverkar inte internet eller kundernas publicerade sajter, som körs hos Cloudflare.',
    fel_instans: `Porten ${d.installningar.port} hålls av något som inte är den registrerade motorn: ${m.orsak || ''}. Appen skickar inget dit och stoppar det inte.`,
    inkompatibel: `Motorn svarar men med en version appen inte kan använda säkert: ${m.orsak || ''}. Skrivningar är spärrade tills motorn är uppdaterad.`,
    rot_saknas: `Den registrerade motorn hittas inte: ${m.orsak || ''}. Inga kunddata har flyttats; välj var motorn finns.`,
    verifierad: 'Motorn är verifierad. Öppnar arbetsytan…',
  }[m.lage] || 'Motorns läge är okänt.';
  $('#motor-text').textContent = text;
  const h = [];
  if (m.lage === 'stoppad') h.push('<button class="knapp primar" id="starta" type="button">Starta motorn</button>');
  if (m.lage === 'verifierad') h.push('<button class="knapp primar" id="oppna" type="button">Öppna arbetsytan</button>');
  h.push('<button class="knapp" id="forsok" type="button">Pröva igen</button>', '<button class="knapp" id="till-diagnos" type="button">Motor och diagnos</button>');
  $('#motor-handlingar').innerHTML = h.join('');
  $('#motor-status').innerHTML = statusrad(d);
  $('#starta')?.addEventListener('click', async (e) => {
    e.target.disabled = true; $('#motor-svar').textContent = 'Startar motorn genom dashboard.sh start…';
    try { await invoke('starta_motor'); location.hash = ''; await borja(); } catch (err) { $('#motor-svar').textContent = String(err); e.target.disabled = false; }
  });
  $('#oppna')?.addEventListener('click', async () => { try { await invoke('oppna_arbetsytan', { till: null }); } catch (err) { $('#motor-svar').textContent = String(err); } });
  $('#forsok').addEventListener('click', async () => { location.hash = ''; await borja(); });
  $('#till-diagnos').addEventListener('click', async () => { location.hash = '#diagnos'; await borja(); });
  try {
    const s = await invoke('senast_kanda');
    const kunder = (s.oversikt?.kunder || []).slice(0, 12);
    $('#senast').hidden = false;
    $('#senast-tid').textContent = `Hämtat ${new Date(s.sparad * 1000).toLocaleString('sv-SE')}. Det kan vara inaktuellt; inget här skickas eller ändras förrän motorn svarar.`;
    $('#senast-lista').innerHTML = kunder.length ? kunder.map((k) => `<li><span class="etikett">${esc(k.namn || k.slug)}</span><span class="under">${esc(k.senaste || '')}${k.test ? ' · testkund' : ''}</span></li>`).join('') : '<li class="under">Inga kunder i det sparade läget.</li>';
  } catch { $('#senast').hidden = true; }
}

function diagnos(d) {
  visaVy('diagnos');
  const m = d.motor || {}, id = m.identitet || {};
  const rader = [
    ['Appen', `${d.app.version}${d.app.prov ? ' (provbygge)' : ''}`],
    ['Kontrakt appen stöder', d.app.kontrakt],
    ['Motorns kontrakt', id.kontrakt || '—'],
    ['Motorns commit vid start', id.commit ? id.commit.slice(0, 12) : '—'],
    ['Commit på disk nu', id.commit_pa_disk ? id.commit_pa_disk.slice(0, 12) + (id.utdaterad ? ' (ändrad sedan start: starta om motorn när inget arbete pågår)' : '') : '—'],
    ['Arbetsytans UI', id.ui ? id.ui.slice(0, 12) : '—'],
    ['Motorns läge', `${MOTORTEXT[m.lage] || m.lage}${m.orsak ? ': ' + m.orsak : ''}`],
  ];
  $('#diag-komp').innerHTML = rader.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('');
  const v = d.installningar.verktyg || {};
  $('#diag-motor').innerHTML = [['Rot', d.installningar.rot], ['Port', `127.0.0.1:${d.installningar.port}`], ['claude', v.claude || 'saknas'], ['node', v.node || 'saknas'], ['Process', id.pid ? `pid ${id.pid}, startad ${id.startad}` : '—']]
    .map(([k, x]) => `<dt>${esc(k)}</dt><dd class="sokvag">${esc(x)}</dd>`).join('');
  if (location.hash.includes('uppdatering')) { $('#uppdatering').scrollIntoView(); sokUppdatering(); }
  $('#inst-behall').checked = d.installningar.avslut === 'behall';
  $('#inst-avisera').checked = d.installningar.aviseringar === true;
  $('#inst-las').value = d.installningar.las_efter_min;
}

async function sokUppdatering() {
  const svar = $('#uppd-svar'), h = $('#uppd-handlingar');
  svar.textContent = 'Söker i motorns utgåvor …';
  try {
    const r = await invoke('sok_uppdatering');
    const knappar = ['<button class="knapp" id="sok-uppd" type="button">Sök igen</button>'];
    if (r.forra_finns) knappar.push('<button class="knapp" id="ga-tillbaka" type="button">Gå tillbaka till föregående version</button>');
    if (!r.utgava) { svar.textContent = `Du har den senaste versionen (${r.nuvarande}).`; }
    else if (r.platsfel) { svar.textContent = `Version ${r.utgava.version} finns, men ${r.platsfel}. Installera med desktop/installera.sh.`; }
    else {
      const pag = (r.pagaende || []).length;
      svar.textContent = `Version ${r.utgava.version} finns (du har ${r.nuvarande}). ${r.utgava.noter || ''} Signaturen prövas före installationen.${pag ? ` ${pag} arbete pågår i motorn; det påverkas inte av en uppdatering av appen, men du kan vänta.` : ''}`;
      knappar.unshift(`<button class="knapp primar" id="installera-uppd" type="button" data-version="${esc(r.utgava.version)}" data-pag="${pag}">${pag ? 'Installera ändå och starta om' : 'Installera och starta om'}</button>`, '<button class="knapp" id="senare-uppd" type="button">Senare</button>');
    }
    h.innerHTML = knappar.join('');
    $('#sok-uppd')?.addEventListener('click', sokUppdatering);
    $('#senare-uppd')?.addEventListener('click', () => { svar.textContent = 'Uppdateringen väntar tills du söker igen.'; h.innerHTML = '<button class="knapp" id="sok-uppd" type="button">Sök efter uppdatering</button>'; $('#sok-uppd').addEventListener('click', sokUppdatering); });
    $('#installera-uppd')?.addEventListener('click', async (e) => {
      e.target.disabled = true; svar.textContent = 'Hämtar och prövar signaturen …';
      try { const x = await invoke('installera_uppdatering', { version: e.target.dataset.version, avenUnderArbete: e.target.dataset.pag !== '0' });
        if (x.uppskjuten) svar.textContent = 'Uppskjuten: arbete pågår.'; }
      catch (err) { svar.textContent = 'Inte installerad: ' + err; e.target.disabled = false; }
    });
    $('#ga-tillbaka')?.addEventListener('click', async (e) => { e.target.disabled = true; try { await invoke('ga_tillbaka_version'); } catch (err) { svar.textContent = String(err); e.target.disabled = false; } });
  } catch (e) { svar.textContent = 'Kunde inte söka: ' + e; }
}
$('#sok-uppd').addEventListener('click', sokUppdatering);

$('#spara-inst').addEventListener('click', async () => {
  try {
    await invoke('installning', { nyckel: 'avslut', varde: $('#inst-behall').checked ? 'behall' : 'fraga' });
    await invoke('installning', { nyckel: 'las_efter_min', varde: String($('#inst-las').value || 0) });
    await invoke('installning', { nyckel: 'aviseringar', varde: $('#inst-avisera').checked ? 'pa' : 'av' });
    $('#inst-svar').textContent = 'Sparat.';
  } catch (e) { $('#inst-svar').textContent = String(e); }
});
$('#byt-rot').addEventListener('click', async () => {
  try { const r = await invoke('valj_motorrot'); if (r) { await invoke('registrera_motor', { rot: r, port: D.installningar.port }); location.hash = ''; await borja(); } }
  catch (e) { $('#inst-svar').textContent = String(e); }
});
$('#tillbaka').addEventListener('click', async () => { location.hash = ''; await borja(); });
window.addEventListener('hashchange', () => { if (!['#motor', ''].includes(location.hash)) borja(); });
borja();
