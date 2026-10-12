// Kompetenskartan (ägarens tillägg 2026-10-11; kontroller/kompetenskarta.py): var skills, MCP:er och verktyg används i
// flödet, vad körningarnas kvitton faktiskt visar och var luckorna finns. Allt kommer ur motorns egna källor, och varje
// del säger sin källa; ett kvitto belägger läsning och anrop, aldrig tillämpning eller kvalitet.
(() => {
  const e_ = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const FLIKAR = [['luckor', 'Luckor'], ['flodet', 'Flödet'], ['kompetenser', 'Kompetenserna'], ['utanfor', 'Tjänster och agenter']];
  const SLAG = { skill_utan_plats: ['Skill utan plats', 'fel'], mcp_krav: ['MCP-krav', 'fel'], mcp_blockerat: ['Blockerat', 'fel'], karna: ['Kärnan', 'varn'],
    agent: ['Agent utan roll', 'varn'], mcp_oanvant: ['Tjänst oanvänd', 'varn'], verktyg_oanvant: ['Verktyg oanvänt', 'varn'], ej_observerat: ['Inte observerat', ''] };
  const PLATS = { roll: 'har roll', process: 'processkill', skal: 'ingen uppgift i flödet, med skäl', utan: 'varken roll eller skäl' };
  // stegens namn i kartan: motorns passnamn med stor bokstav; fördjupningen heter "uppdraget" i sessionernas uppdrag
  const stegnamn = (s) => s.pass === 'fordjupa' ? 'Fördjupningen efter ditt val' : s.namn.charAt(0).toUpperCase() + s.namn.slice(1);
  const S = { d: null, flik: 'luckor' };
  try { S.flik = sessionStorage.getItem('nwp-kompetenskarta:flik') || 'luckor'; } catch { /* bekvämlighet */ }

  const kort = (t) => { if (!t) return ''; const d = new Date(t); return isNaN(d) ? '' : d.toLocaleString('sv-SE', { dateStyle: 'medium', timeStyle: 'short' }); };
  const filnamn = (f) => f.replace(/\/SKILL\.md$/, '').replace(/^kunskap\//, 'kunskap: ').replace(/^kritik\//, 'kritik: ');
  const chip = (t, k = '', titel = '') => `<span class="kk-chip${k ? ' ' + k : ''}"${titel ? ` title="${e_(titel)}"` : ''}>${e_(t)}</span>`;

  window.kompetenskartavy = async function kompetenskartavy() {
    const vy = document.getElementById('vy');
    vy.innerHTML = '<p class="kk-under">Läser kompetenskartan …</p>';
    try {
      const r = await fetch('/api/kompetenskarta', { cache: 'no-store' });
      S.d = await r.json();
      if (!r.ok) throw new Error(S.d.fel || 'HTTP ' + r.status);
    } catch (err) { vy.innerHTML = `<p class="kk-fel">Kompetenskartan kunde inte läsas: ${e_(err.message)}</p>`; return; }
    rita();
  };

  function rita() {
    const d = S.d, vy = document.getElementById('vy');
    const plats = Object.values(d.skills).reduce((a, x) => (a[x.plats] = (a[x.plats] || 0) + 1, a), {});
    const obs = Object.keys(d.observerat).length;
    vy.innerHTML = `<div class="kk">
      <h1>Kompetenskartan</h1>
      <p class="kk-ingress">Var flödets skills, kunskapstexter, MCP:er och verktyg används, vad körningarnas kvitton faktiskt visar och var luckorna finns,
        så att AI:ns förståelse kan förstärkas där det behövs. Tilldelningen kommer ur metodkartan, det observerade ur kompetenskvittona: ett kvitto belägger
        läsning och anrop, inte tillämpning eller kvalitet. Det som inte observerats står som inte observerat.</p>
      <ul class="kk-summa" aria-label="Sammanfattning">
        <li><b>${d.steg.length}</b> steg och <b>${Object.keys(d.roller).length}</b> roller</li>
        <li><b>${Object.keys(d.skills).length}</b> skills: ${plats.roll || 0} med roll, ${plats.skal || 0} med skäl, ${plats.process || 0} process, <span class="${plats.utan ? 'kk-rod' : ''}">${plats.utan || 0} utan</span></li>
        <li><b>${d.tjanster.length}</b> MCP-tjänster och <b>${d.verktyg.length}</b> verktyg</li>
        <li><b>${obs}</b> av ${Object.keys(d.roller).length} roller observerade i kvitton</li>
        <li><b>${d.luckor.length}</b> luckor</li>
      </ul>
      <div class="kk-flikar" role="tablist" aria-label="Kompetenskartans delar">${FLIKAR.map(([k, n]) =>
        `<button type="button" role="tab" id="kk-tab-${k}" data-kk-flik="${k}" aria-selected="${S.flik === k}" aria-controls="kk-panel" tabindex="${S.flik === k ? 0 : -1}">${n}${k === 'luckor' ? ` <span class="kk-antal">${d.luckor.length}</span>` : ''}</button>`).join('')}</div>
      <section class="kk-panel" id="kk-panel" role="tabpanel" aria-labelledby="kk-tab-${S.flik}">${({ luckor, flodet, kompetenser, utanfor }[S.flik] || luckor)(d)}</section>
      <p class="kk-kalla">Källor: ${Object.values(d.kallor).map(e_).join('; ')}. Sammanställd ${e_(kort(d.tid))}.</p>
    </div>`;
    const v = vy.querySelector('.kk');
    v.addEventListener('click', (ev) => {
      const t = ev.target.closest('[data-kk-flik]'); if (!t) return;
      byt(t.dataset.kkFlik);
    });
    v.addEventListener('keydown', (ev) => {
      const t = ev.target.closest('[data-kk-flik]'); if (!t || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(ev.key)) return;
      const alla = FLIKAR.map(([k]) => k), i = alla.indexOf(t.dataset.kkFlik);
      byt(ev.key === 'Home' ? alla[0] : ev.key === 'End' ? alla[alla.length - 1] : alla[(i + (ev.key === 'ArrowRight' ? 1 : alla.length - 1)) % alla.length]);
      ev.preventDefault();
    });
  }
  function byt(k) {
    S.flik = k; try { sessionStorage.setItem('nwp-kompetenskarta:flik', k); } catch { /* bekvämlighet */ }
    rita(); document.getElementById('kk-tab-' + k)?.focus();
  }

  function luckor(d) {
    if (!d.luckor.length) return '<p class="kk-tomt">Inga luckor som går att belägga just nu.</p>';
    return `<p class="kk-under">Det som går att belägga ur metodkartan och kvittona, det tyngsta först. Varje lucka har sin källa och ett förslag.</p>
      <ul class="kk-luckor">${d.luckor.map((l) => { const [namn, k] = SLAG[l.slag] || [l.slag, '']; return `<li class="kk-lucka">
        <p class="kk-luckhuvud">${chip(namn, k)}<b>${e_(l.rubrik)}</b></p>
        <p>${e_(l.detalj)}</p>
        <p class="kk-forslag">Förslag: ${e_(l.forslag)}</p>
        <p class="kk-kalla">Källa: <code>${e_(l.kalla)}</code></p></li>`; }).join('')}</ul>`;
  }

  function observeradText(o, roll) {
    if (!o) return '<span class="kk-dov">inte observerat: inget sparat kvitto för rollen</span>';
    const mcp = Object.entries(o.mcp).map(([m, s]) => chip(`${m}: ${Object.entries(s).map(([t, n]) => `${t} ×${n}`).join(', ')}`, s['använt med resultat'] ? 'ok' : s['blockerat eller misslyckat'] ? 'fel' : 'varn')).join('');
    const vk = Object.entries(o.verktyg).map(([v, s]) => chip(`${v}: ${Object.entries(s).map(([t, n]) => `${t} ×${n}`).join(', ')}`, s['använt med resultat'] ? 'ok' : '')).join('');
    const akt = Object.entries(o.aktiverade).map(([s, n]) => `${s} ×${n}`).join(', ');
    return `${o.kvitton} kvitton från ${o.kunder} ${o.kunder === 1 ? 'kund' : 'kunder'}, senast ${e_(kort(o.senast))}. Kärnan läst hel i ${o.karna_hel} av ${o.karna_sedd} observerade.
      ${akt ? `Skillverktyget: ${e_(akt)}.` : `Skillverktyget: ${roll.karna.some((f) => f.endsWith('/SKILL.md')) ? 'inga aktiveringar i kvittona' : 'inga aktiverbara kärnskills'}.`}
      ${mcp || vk ? `<span class="kk-chips">${mcp}${vk}</span>` : ''}`;
  }
  function flodet(d) {
    return `<p class="kk-under">Stegen i flödets ordning, med rollerna som arbetar där. Kärnan läses hel innan rollen ändrar eller bedömer något; granskningen efter första renderingen läses hel och görs på sidan; alternativen väljs efter riktningen. MCP med krav måste anropas med resultat före nästa steg.</p>
      <ol class="kk-stegen">${d.steg.map((s) => `<li class="kk-steg"><h2 class="kk-h2">${e_(stegnamn(s))} <span class="kk-pass">${e_(s.pass)}</span></h2>
        ${s.roller.map((id) => { const r = d.roller[id]; return `<div class="kk-roll"><h3 class="kk-h3">${e_(r.namn)}</h3>
          <dl class="kk-dl">
            <dt>Kärna</dt><dd class="kk-chips">${r.karna.map((f) => chip(filnamn(f), 'karna', f)).join('')}</dd>
            ${(r.efter || []).length ? `<dt>Granskning</dt><dd class="kk-chips">${r.efter.map((f) => chip(filnamn(f), 'karna', f)).join('')}</dd>` : ''}
            ${r.valj.length ? `<dt>Alternativ</dt><dd><details><summary>${r.valj.length} att välja efter riktningen</summary><span class="kk-chips">${r.valj.map((f) => chip(filnamn(f), '', f)).join('')}</span></details></dd>` : ''}
            <dt>Verktyg</dt><dd class="kk-chips">${r.verktyg.length ? r.verktyg.map((v) => chip(v)).join('') : '<span class="kk-dov">inga</span>'}</dd>
            <dt>MCP</dt><dd class="kk-chips">${r.mcp.length ? r.mcp.map((m) => chip(m + (r.mcp_krav.includes(m) ? ' (krav)' : ''), r.mcp_krav.includes(m) ? 'krav' : '')).join('') : '<span class="kk-dov">inga</span>'}</dd>
            <dt>Observerat</dt><dd>${observeradText(d.observerat[id], r)}</dd>
          </dl></div>`; }).join('')}</li>`).join('')}</ol>`;
  }

  function kompetenser(d) {
    const roller = Object.values(d.roller);
    const aktiv = {}; Object.values(d.observerat).forEach((o) => Object.entries(o.aktiverade).forEach(([s, n]) => { aktiv[s] = (aktiv[s] || 0) + n; }));
    const skillrader = Object.entries(d.skills).sort((a, b) => (a[1].plats === 'roll' ? 0 : 1) - (b[1].plats === 'roll' ? 0 : 1) || a[0].localeCompare(b[0], 'sv'));
    const texter = d.filer.filter((f) => f.typ === 'kunskap' || f.typ === 'kritik');
    const huvud = `<tr><th scope="col" class="kk-namnkol">Kompetens</th>${roller.map((r) => `<th scope="col" class="kk-rollkol"><span title="${e_(r.namn)}">${e_(r.id)}</span></th>`).join('')}<th scope="col">Aktiverad</th></tr>`;
    const cell = (v) => v === 'karna' ? '<td class="kk-cell"><span class="kk-prick karna" title="kärna">●</span><span class="pt-dold-text">kärna</span></td>'
      : v === 'efter' ? '<td class="kk-cell"><span class="kk-prick karna" title="granskning efter renderingen">◆</span><span class="pt-dold-text">granskning</span></td>'
      : v === 'valj' ? '<td class="kk-cell"><span class="kk-prick" title="alternativ">○</span><span class="pt-dold-text">alternativ</span></td>' : '<td class="kk-cell"></td>';
    const rader = skillrader.map(([n, x]) => `<tr class="${x.plats === 'roll' ? '' : 'kk-utan-roll'}"><th scope="row" class="kk-namnkol">${e_(n)}${x.plats !== 'roll' ? `<span class="kk-plats ${x.plats === 'utan' ? 'kk-rod' : ''}">${e_(PLATS[x.plats])}</span>` : ''}</th>
      ${roller.map((r) => cell(x.roller[r.id])).join('')}<td class="kk-cell kk-akt">${aktiv[n] ? '×' + aktiv[n] : ''}</td></tr>`).join('');
    const textrader = texter.map((f) => `<tr><th scope="row" class="kk-namnkol">${e_(f.fil)}</th>${roller.map((r) => cell(f.roller[r.id])).join('')}<td class="kk-cell"></td></tr>`).join('');
    return `<p class="kk-under">Varje skill och kunskapstext mot rollerna: ● kärna, ◆ granskning efter renderingen, ○ alternativ. Aktiverad räknar skillverktygets observerade anrop i kvittona. En skill utan roll har antingen ett skäl i metodkartan eller saknar plats, och då är det en lucka.</p>
      <div class="kk-tabell" role="region" aria-label="Kompetenserna mot rollerna" tabindex="0"><table>
        <thead>${huvud}</thead>
        <tbody><tr class="kk-grupprad"><th scope="rowgroup" colspan="${roller.length + 2}">Skills</th></tr>${rader}
        <tr class="kk-grupprad"><th scope="rowgroup" colspan="${roller.length + 2}">Kunskapstexter och kriterier</th></tr>${textrader}</tbody></table></div>`;
  }

  function utanfor(d) {
    const tj = d.tjanster.map((t) => `<li class="kk-kort"><h3 class="kk-h3">${e_(t.namn)}</h3>
      <p>Roller: ${t.roller.length ? t.roller.map((r) => chip(r)).join('') : '<span class="kk-dov">ingen</span>'}${t.krav.length ? ` Krav i: ${t.krav.map((r) => chip(r, 'krav')).join('')}` : ''}</p>
      ${t.verktyg_med_uppgift.length || t.verktyg_utan_uppgift.length ? `<p>${t.verktyg_med_uppgift.length} verktyg med uppgift, ${t.verktyg_utan_uppgift.length} utan (beslut med skäl i metodkartan, Tjänsternas verktyg).</p>
      <details><summary>Verktygen</summary><p class="kk-chips">${t.verktyg_med_uppgift.map((v) => chip(v, 'ok', 'uppgift')).join('')}${t.verktyg_utan_uppgift.map((v) => chip(v, 'dov', 'ingen uppgift')).join('')}</p></details>` : '<p class="kk-dov">Verktygslistan kommer ur tjänsten när den ansluts.</p>'}</li>`).join('');
    const vk = d.verktyg.map((v) => `<li class="kk-kort"><h3 class="kk-h3">${e_(v.id)}</h3><p>Roller: ${v.roller.length ? v.roller.map((r) => chip(r)).join('') : '<span class="kk-dov">ingen</span>'}</p></li>`).join('');
    const ag = d.agenter.map((a) => `<li class="kk-kort"><h3 class="kk-h3">${e_(a.namn)}</h3>
      <dl class="kk-dl"><dt>Kunskap</dt><dd>${a.kunskap.map(e_).join('; ')}</dd><dt>Verktyg</dt><dd>${a.verktyg.length ? a.verktyg.map(e_).join('; ') : 'inga'}</dd>
      <dt>MCP och skills</dt><dd>${a.mcp.length || a.skills.length ? [...a.mcp, ...a.skills].map(e_).join(', ') : 'inga'}</dd></dl>
      ${a.not ? `<p class="kk-under">${e_(a.not)}</p>` : ''}${a.lucka ? `<p class="kk-rod">${e_(a.lucka)}</p>` : ''}<p class="kk-kalla">Källa: <code>${e_(a.kalla)}</code></p></li>`).join('');
    return `<h2 class="kk-h2">MCP-tjänsterna</h2><ul class="kk-rutnat">${tj}</ul>
      <h2 class="kk-h2">Verktygen</h2><ul class="kk-rutnat">${vk}</ul>
      <h2 class="kk-h2">Agenter utanför metodkartan</h2><p class="kk-under">Sessioner som motorn startar utan ett kompetensblock, med den kunskap de faktiskt får.</p><ul class="kk-rutnat">${ag}</ul>`;
  }
})();
