// Ägarvy för det befintliga lokala ärendet. Startar inga modeller eller servrar.
let kundstartGeneration=0;
async function kundstartvy(eid='',besked='',personlig=null) {
  const generation=++kundstartGeneration, hash=eid?'#/kundstart/'+eid:'#/kundstart';
  const aktuell=()=>generation===kundstartGeneration && location.hash===hash;
  aktivNav('kundstart');
  const safe=esc, v=document.getElementById('vy');
  const fmt=s=>({utkast:'Utkast',forfragan:'Förfrågan för beredning',accepterad:'Accepterat erbjudande',inte_startad:'AI inte startad',ko:'Svar sparat, AI köad',pagar:'AI bearbetar',klar:'Färdigt inom angiven omfattning',fel:'Bearbetningsfel',avstangd:'AI avstängd'}[s]||s);
  function meddelande(text,fel=false){if(!aktuell())return;const p=document.getElementById('ks-status');p.textContent=text;p.className=fel?'meddelande fel':'meddelande';}
  function engang(data){if(!aktuell())return;const box=document.getElementById('ks-engang');box.replaceChildren();
    const p=document.createElement('p');p.textContent=data.text||'Personlig åtkomst. Länken visas endast nu och skickas inte automatiskt.';box.append(p);
    if(data.nyckel){const l=document.createElement('label');l.textContent='Lokal personlig ärendelänk';l.htmlFor='ks-lank';
      const t=document.createElement('textarea');t.id='ks-lank';t.readOnly=true;t.rows=3;t.value='http://127.0.0.1:4773/#arende='+encodeURIComponent(data.arende)+'&nyckel='+encodeURIComponent(data.nyckel);box.append(l,t);
      const b=document.createElement('button');b.type='button';b.textContent='Markera länken';b.onclick=()=>{t.focus();t.select();};box.append(b);}
    if(data.arende){const a=document.createElement('a');a.href='#/kundstart/'+data.arende;a.textContent='Öppna ärendet';box.append(a);}
    box.hidden=false;
  }
  function bindUtkast(f,revision){
    const key='nwp-kundstart-agare:'+ (eid||'nya')+':'+f.id;
    let sparat=null, fel=false;
    const lasVarden=()=>Object.fromEntries([...f.elements].filter(x=>x.name).map(x=>[x.name,x.type==='checkbox'?x.checked:x.value]));
    const felmeddelande=()=>meddelande('Webbläsaren kunde inte bevara utkastet. Ingen handling skickas; kopiera din text innan du försöker igen.',true);
    try{const raw=sessionStorage.getItem(key);if(raw){sparat=JSON.parse(raw);if(!sparat||typeof sparat.varden!=='object'||!Number.isInteger(sparat.revision))throw Error('Ogiltigt utkast');
      for(const [n,val] of Object.entries(sparat.varden)){const input=f.elements.namedItem(n);if(input){if(input.type==='checkbox')input.checked=val===true;else input.value=String(val);}}}}
    catch(e){fel=true;felmeddelande();}
    const status=document.createElement('p'), jamfor=document.createElement('button');jamfor.type='button';jamfor.textContent='Jag har jämfört detta utkast med den aktuella revisionen';
    f.append(status,jamfor);const submit=f.querySelector('button[type="submit"]'), varAvstangd=submit.disabled;
    const klar=()=>!fel&&(!sparat||sparat.revision===revision);
    function visa(){const gammal=sparat&&sparat.revision!==revision;status.textContent=fel?'Utkastet kunde inte bevaras.':gammal?'Ditt utkast gäller revision '+sparat.revision+'. Läs det aktuella ärendet och jämför innan du sparar.':'';jamfor.hidden=!gammal;submit.disabled=varAvstangd||!klar();}
    function spara(){try{sessionStorage.setItem(key,JSON.stringify(sparat));return true;}catch(e){fel=true;felmeddelande();visa();return false;}}
    function andrat(){sparat={...(sparat||{revision}),varden:lasVarden()};spara();visa();}
    f.addEventListener('input',andrat);f.addEventListener('change',andrat);
    jamfor.onclick=()=>{sparat={...(sparat||{}),revision,varden:lasVarden()};spara();visa();};visa();
    return {klar, revision:()=>sparat?.revision??revision,
      async operation(data){if(!sparat)andrat();if(fel)throw Error('Utkastet kunde inte bevaras.');
        const indata=JSON.stringify(data),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(indata))),b=>b.toString(16).padStart(2,'0')).join('');
        sparat.operationer=sparat.operationer||{};
        if(!sparat.operationer[digest]){
          if(Object.keys(sparat.operationer).length>=100)throw Error('Startjournalen är full. Följ upp tidigare starter innan en ny omgång skapas.');
          sparat.operationer[digest]=sparat.indata===indata&&sparat.operation?sparat.operation:crypto.randomUUID();
          delete sparat.indata;delete sparat.operation;if(!spara())throw Error('Utkastet kunde inte bevaras.');
        }return sparat.operationer[digest];},
      frys(){return sessionStorage.getItem(key);},
      klart(version){try{if(sessionStorage.getItem(key)===version){sessionStorage.removeItem(key);sparat=null;}}catch(e){fel=true;felmeddelande();}}};
  }
  const wrapper=body=>`<div class="dok kundstart-agare"><p><a href="#/kundstart">Kundstart</a></p>${body}<p id="ks-status" role="status" aria-live="polite"></p><section id="ks-engang" hidden aria-label="Personlig åtkomst"></section></div>`;
  if(!eid){const d=await api('/api/kundstart');if(!aktuell())return;v.innerHTML=wrapper(`<h1>Kundstart</h1><p class="under">Ett privat ärende från kundens svar till beredning. Att skapa ärendet startar varken AI, kundserver eller bygge.</p>
    <section><h2>Ärenden</h2>${d.arenden.length?d.arenden.map(x=>`<article class="ks-kort"><h3><a href="#/kundstart/${safe(x.id)}">${safe(x.slug)}</a></h3><p>${safe(fmt(x.bestallning.status))} · ${safe(fmt(x.modell))}${x.fiktiv?' · syntetiskt prov':''}</p><p>Revision ${x.revision} · ${x.fragor} frågor att följa upp</p></article>`).join(''):'<p>Inga ärenden har skapats.</p>'}</section>
    <details><summary>Skapa ett privat ärende</summary><form id="ks-skapa"><label for="ks-slug">Projektets slug</label><input id="ks-slug" name="slug" required pattern="[a-z0-9][a-z0-9-]{0,51}" autocomplete="off">
    <label for="ks-namn">Första beslutsfattarens namn</label><input id="ks-namn" name="namn" required maxlength="120" autocomplete="off">
    <label for="ks-budget">Högsta antal AI-anrop för hela ärendet</label><input id="ks-budget" name="modellbudget" type="number" min="0" max="100" value="0" required>
    <label><input id="ks-fiktiv" name="fiktiv" type="checkbox" checked> Syntetiskt provärende</label><p>0 håller AI-bearbetningen avstängd för ärendet. En verklig modellkoppling och godkänd personuppgiftshantering kräver separat aktivering.</p><button type="submit">Skapa ärendet</button></form></details>
    ${Object.keys(d.gallringar||{}).length?`<details><summary>Gallring som behöver uppföljning</summary>${Object.entries(d.gallringar).map(([id,p])=>`<p>${safe(id)}: ${safe(p.status)}${p.kvar.length?' · kvarvarande kopior behöver hanteras':''}</p>`).join('')}</details>`:''}`);
    const f=document.getElementById('ks-skapa'), utkast=bindUtkast(f,0);
    f.onsubmit=async e=>{e.preventDefault();if(!aktuell()||!utkast.klar())return;const b=f.querySelector('button[type="submit"]');b.disabled=true;
      try{const data={slug:f.elements.slug.value,namn:f.elements.namn.value,modellbudget:Number(f.elements.modellbudget.value),fiktiv:f.elements.fiktiv.checked};
        const operation=await utkast.operation(data), r=await post('/api/kundstart',{...data,operation});
        if(!aktuell())return;engang(r);meddelande('Ärendet finns. Ingen modell eller kundserver startades.');}
      catch(e){meddelande(e.message,true);}finally{if(aktuell())b.disabled=!utkast.klar();}};return;
  }
  const d=await api('/api/kundstart/'+encodeURIComponent(eid));if(!aktuell())return;const a=d.arende;
  // Funktioner och anslutningar (integrationskatalogen K01–K18): fyra skilda dimensioner per val, aldrig ett gemensamt
  // "klart": kundens läge, paketets färdighet, kundens anslutning och genomförandet. Valen görs manuellt av ägaren; ingen
  // AI-bedömning visas.
  const funktionsvy=fu=>{if(!fu||fu.fel)return `<section><h2>Funktioner och anslutningar</h2><p>${safe(fu?.fel||'Integrationskatalogen kunde inte läsas.')}</p></section>`;
    const lagen={kundval:'kundens val',onskemal:'önskemål, inte beställt',framtida:'framtida',avstatt:'avstått',okant:'okänt',inte_relevant:'inte relevant',grund:'ingår i grundleveransen'};
    const niva={forvaltning:'förvaltning',lank:'länk',inbaddning:'inbäddning',inbyggd:'inbyggd',api:'API',formedlad:'förmedlad anslutning',utreds:'utreds'};
    const fard={dokumenterat:'dokumenterat, ingen körväg',implementerat:'implementerat',kontraktsprovat:'kontraktsprovat lokalt',leverantorsprovat:'prövat mot leverantören',inaktuellt:'inaktuellt'};
    const paket=Object.fromEntries(fu.omraden.flatMap(o=>o.paket.map(p=>[p.id,{...p,omrade:o.namn}])));
    const behov=Object.fromEntries(fu.behov.map(b=>[b.id,b])), pl=fu.plan;
    const lageFor=v=>{const ia=pl.inaktuella_val.find(x=>x.val===v.id);if(ia)return 'inaktuellt: '+ia.skal;
      if(v.behov)return lagen[behov[v.behov]?.bestallning]||'okänt';return paket[v.paket]?.grund?lagen.grund:lagen.onskemal;};
    const anslutning=v=>{const b=v.behov&&behov[v.behov];if(!b)return 'inte ansluten';
      return 'utredning '+(b.anslutning.utredning||'saknas')+', konto '+(b.anslutning.konto||'okänt')+', prov '+(b.anslutning.prov||'inte provat');};
    const hinder=[...pl.hinder,...pl.konflikter.map(k=>k.paket.join(' och ')+': '+k.skal),...pl.saknade_beroenden.map(s=>s.paket+' kräver '+s.kraver),
      ...pl.inaktuella_val.map(x=>x.paket+': '+x.skal),...pl.andrade_paketversioner.map(x=>x.paket+': vald version '+x.vald+', katalogen har '+x.nu)];
    return `<section aria-labelledby="ks-funktioner-rubrik"><h2 id="ks-funktioner-rubrik">Funktioner och anslutningar</h2>
    <p>Katalog ${safe(fu.katalog)}. Manuella val av ägaren, ingen AI-bedömning. Ett val utan kundens behov är ett förslag; bara kundens eget val eller grundleveransen ingår i planen.</p>
    <p><strong>${pl.klar_for_bygge?'Planen kan gå vidare till bygget.':'Planen har hinder.'}</strong> ${pl.omfattning.length} i omfattningen, ${pl.ovriga.length} utanför.${pl.okand_kostnad.length?' Okänd kostnad: '+safe(pl.okand_kostnad.join(', '))+'.':''}</p>
    ${hinder.length?`<ul>${hinder.map(h=>`<li>${safe(h)}</li>`).join('')}</ul>`:''}
    ${fu.val.length?fu.val.map(v=>{const p=paket[v.paket]||{};return `<article class="ks-kort"><h3>${safe(v.omrade)} ${safe(p.omrade||'')}: ${safe(p.funktion||v.paket)}</h3>
      <dl><dt>Kundens läge</dt><dd>${safe(lageFor(v))}${v.behov&&behov[v.behov]?' · '+safe(behov[v.behov].behov):''}</dd>
      <dt>Paketet</dt><dd>${safe(v.paket)} ${safe(v.paketversion)} · ${safe(niva[p.niva]||p.niva||'')} · ${safe(fard[p.fardighet]||p.fardighet||'finns inte längre')}</dd>
      <dt>Anslutningen</dt><dd>${safe(anslutning(v))}</dd><dt>Genomförandet</dt><dd>inte startat</dd></dl>
      <p>${safe(v.motivering)}</p><button type="button" data-ks-avmarkera="${safe(v.id)}">Avmarkera</button></article>`;}).join(''):'<p>Inga funktioner är valda.</p>'}
    ${pl.manniska.length?`<details><summary>Handlingar som en människa gör (${pl.manniska.length})</summary><ul>${pl.manniska.map(m=>`<li>${safe(m.paket)}: ${safe(m.handling)}</li>`).join('')}</ul></details>`:''}
    <details><summary>Välj en funktion ur katalogen</summary><form id="ks-funktion"><label for="ks-omrade">Område</label><select id="ks-omrade" name="omrade">${fu.omraden.map(o=>`<option value="${safe(o.id)}">${safe(o.id)} ${safe(o.namn)}</option>`).join('')}</select>
    <label for="ks-paket">Paket</label><select id="ks-paket" name="paket"></select><p id="ks-paket-besked"></p>
    <label for="ks-behov">Kundens behov</label><select id="ks-behov" name="behov"><option value="">Inget: ett förslag eller grundleveransen</option>${fu.behov.map(b=>`<option value="${safe(b.id)}">${safe(b.behov)} (${safe(lagen[b.bestallning]||b.bestallning)})</option>`).join('')}</select>
    <label for="ks-motivering">Varför passar paketet?</label><textarea id="ks-motivering" name="motivering" required maxlength="2000"></textarea>
    <button type="submit">Välj paketet</button></form></details></section>`;};
  const amnen={A:'Verksamhet och mål',B:'Besökare och uppgifter',C:'Nuvarande lösning',D:'Uttryck',E:'Innehåll',F:'Funktioner',G:'Synlighet',H:'Förvaltning',I:'Ramar och ansvar',J:'Särskilda behov'};
  v.innerHTML=wrapper(`<h1>${safe(a.slug)}</h1><p class="under">Revision ${a.revision} · ${safe(fmt(a.bestallning.status))}${a.fiktiv?' · syntetiskt prov':''}</p>
    <p>${safe(a.modell.text||'AI har inte startats.')} ${safe(d.drift.text)}</p>
    <div class="ks-faser">${Object.entries(d.faser).map(([fas,f])=>`<section class="ks-kort"><h2>${safe({forberedelse:'Förberedelse',skiss:'Skiss',helbygge:'Helbygge',publicering:'Publicering'}[fas])}</h2><p>${f.kan_starta?'Underlag kan prövas i detta steg':'Villkor återstår'}</p><ul>${f.brister.map(x=>`<li>${safe(x)}</li>`).join('')}</ul><p>${safe(f.innebord||'')}</p></section>`).join('')}</div>
    <section><h2>Kundens aktuella uppgifter</h2>${Object.values(a.uppgifter).map(u=>`<article class="ks-kort"><h3>${safe(amnen[u.amne])}</h3><p>${safe(u.text)}</p><p>${safe(u.bestallning)} · ${safe(u.kunskap)}${u.motsagelse?' · motsägelse kvar':''}</p></article>`).join('')||'<p>Inga strukturerade uppgifter ännu.</p>'}
    <details><summary>Samtalet och öppna frågor</summary>${a.meddelanden.map(m=>`<article class="ks-kort"><strong>${m.roll==='kund'?'Kundens svar':'AI:s förslag'}</strong><p>${safe(m.text)}</p></article>`).join('')}${a.fragor.map(q=>`<p>${safe(q.text)} — ${safe(q.varfor)}</p>`).join('')}${Object.values(a.returfragor||{}).map(q=>`<article><p>${safe(q.text)} · ${safe(q.status)} · ${safe(q.varfor)}</p>${q.svar.length?`<p>${d.retursvar[q.id].klarlagd?'Svarsversionen är klarlagd.':'Svaret är mottaget och behöver intern bedömning inför det berörda steget.'}</p><form data-ks-svar="${safe(q.id)}"><label for="ks-bedomning-${safe(q.id)}">Bedömning av det aktuella svaret</label><textarea id="ks-bedomning-${safe(q.id)}" name="bedomning" required></textarea><label for="ks-bedomare-${safe(q.id)}">Ansvarig för bedömningen</label><input id="ks-bedomare-${safe(q.id)}" name="ansvarig" required maxlength="120"><button type="submit">Markera denna svarsversion som klarlagd</button></form>`:''}</article>`).join('')}</details></section>
    ${funktionsvy(d.funktioner)}
    <section><h2>Överlämning till webbflödet</h2><p>${a.overlamning?`${safe(a.overlamning.status)} · revision ${a.overlamning.revision} · ${a.overlamning.aktuell?'filer och källa är aktuella':'inaktuell eller ofullständig'}`:'Inget underlag har lämnats över.'}</p>
    <button id="ks-overlamna" type="button" ${d.faser.forberedelse.kan_starta?'':'disabled'}>Lämna aktuellt underlag till förberedelsen</button>
    ${a.overlamning?.status==='publicerar'?'<button id="ks-aterstall" type="button">Återställ den avbrutna överlämningen</button>':''}
    <p>Detta överför underlag. Det startar inte ett helbygge eller ger ett designgodkännande.</p><a href="#/arbetsyta/${safe(a.slug)}/forslag">Till projektets förslag i arbetsytan</a></section>
    <details><summary>Ge ett definierat erbjudande</summary><form id="ks-erbjudande"><label for="ks-omfattning">Omfattningen som erbjuds</label><textarea id="ks-omfattning" name="text" required></textarea><label for="ks-villkor">Faktiska villkor</label><textarea id="ks-villkor" name="villkor" required></textarea><label for="ks-ansvarig">Ansvarig för erbjudandet</label><input id="ks-ansvarig" name="ansvarig" required maxlength="120"><button type="submit">Lämna erbjudandet för kundens acceptans</button></form><p>Detta är inte kundens acceptans. Ett aktuellt inlämnat uppdrag krävs.</p></details>
    <details><summary>Be kunden komplettera</summary><form id="ks-fraga"><label for="ks-fragetext">Frågan till kunden</label><textarea id="ks-fragetext" name="text" required></textarea><label for="ks-varfor">Varför behövs svaret?</label><textarea id="ks-varfor" name="varfor" required></textarea><label for="ks-amne">Ämne</label><select id="ks-amne" name="amne">${Object.entries(amnen).map(([k,v])=>`<option value="${k}">${safe(v)}</option>`).join('')}</select><label for="ks-fas">Vilket steg påverkas?</label><select id="ks-fas" name="fas"><option value="forberedelse">Förberedelse</option><option value="skiss">Skiss</option><option value="helbygge">Helbygge</option><option value="publicering">Publicering</option></select><label><input name="kritisk" type="checkbox"> Måste klarläggas före det steget</label><button type="submit" ${a.overlamning?.status==='klar'?'':'disabled'}>Lägg kompletteringen i kundens ärende</button></form></details>
    <details><summary>Deltagare och personlig åtkomst</summary>${Object.entries(a.deltagare||{}).map(([id,p])=>`<p>${safe(p.namn)} · ${safe(p.roll)} · ${p.aktiv?'aktiv':'återkallad'} ${p.aktiv?`<button type="button" data-ks-aterkalla="${safe(id)}">Återkalla åtkomsten</button>`:''}</p>`).join('')}
    <form id="ks-deltagare"><label for="ks-person">Deltagarens namn</label><input id="ks-person" name="namn" required maxlength="120"><label for="ks-roll">Behörighet</label><select id="ks-roll" name="roll"><option value="medverkande">Medverkande — lämna och rätta uppgifter</option><option value="lasare">Läsare</option><option value="beslutsfattare">Beslutsfattare — kan också lämna förfrågan och acceptera erbjudande</option></select><label for="ks-dagar">Länkens giltighet i dagar</label><input id="ks-dagar" name="dagar" type="number" value="7" min="1" max="90" required><button type="submit">Skapa personlig åtkomst</button></form></details>
    <details><summary>Modellförsök och resursmått</summary><p>Försöksbudget: ${a.budget.anrop} av ${a.budget.max_anrop}. Begärda och observerade värden hålls isär. Kostnad och abonnemangsförbrukning är inte observerade.</p>
    ${(d.modellanrop||[]).map(m=>`<article class="ks-kort"><h3>Försök vid revision ${m.revision}</h3><p>${safe(m.status==='pagar'?'väntar på utfall':m.status)}${m.slag?' · '+safe(m.slag):''} · ${m.sekunder===null?'tid inte observerad':m.sekunder.toFixed(2)+' s'}</p><p>Modell begärd: ${safe(m.modell_begard||'okänd')}. Observerad: ${safe(m.modell_observerad||'okänd')}.</p><p>Indata: ${m.input_tokens??'okänt'} token · utdata: ${m.output_tokens??'okänt'} token. Förberedd systemtext, hash: ${safe(m.metod_sha256||'inte observerad')}.</p><p>${m.transportlage==='svar_mottaget'?'Transporten har lämnat ett svar.':m.transportlage==='forberedd'?'Transportförsöket är förberett; faktisk sändning är inte bekräftad.':'Ingen förberedd transport observerad.'}</p></article>`).join('')||'<p>Inga modellförsök är registrerade.</p>'}<p>Ett mottaget svar visar inte att intervjun håller rätt kvalitet.</p></details>
    <details><summary>Lagring och säkerhetskopia</summary><p>${a.lagring?.radera_efter?'Gallringsdatum: '+safe(new Date(a.lagring.radera_efter*1000).toLocaleString('sv-SE')):'Inget gallringsdatum fastställt. Ingen automatisk radering sker.'}</p>
    <form id="ks-lagring"><label for="ks-datum">Beslutat gallringsdatum</label><input id="ks-datum" name="datum" type="datetime-local" required><label for="ks-andamal">Lagringens ändamål</label><textarea id="ks-andamal" name="andamal" required></textarea><label for="ks-lagringsansvarig">Ansvarig för beslutet</label><input id="ks-lagringsansvarig" name="ansvarig" required maxlength="120"><button type="submit">Spara lagringsbeslutet</button></form><button id="ks-backup" type="button">Skapa lokal säkerhetskopia</button>
    <p>Gallring och återställning körs separat. Ändrade härledningar och externa kopior kräver egen hantering; gamla kundlänkar återkallas vid återställning.</p></details>`);
  async function anropa(n,data,{utkast=null,personlig=false,refresh=true}={}){
    if(!aktuell()||(utkast&&!utkast.klar()))return null;
    const sparversion=utkast?.frys();
    try{const r=await post(`/api/kundstart/${eid}/${n}`,data);utkast?.klart(sparversion);
      if(aktuell()){
        if(refresh)await kundstartvy(eid,'Handlingen är sparad.',personlig?r:null);
        else meddelande('Handlingen är sparad.');
      }return r;
    }catch(e){if(aktuell()){
      // Ett svar kan försvinna efter att servern sparat. Läs verkligt tillstånd;
      // övriga och misslyckade utkast behåller sin ursprungliga revision.
      try{await kundstartvy(eid,'Handlingen kunde inte bekräftas: '+e.message+'. Kontrollera aktuellt tillstånd innan du försöker igen.');}
      catch(_){meddelande(e.message,true);}
    }return null;}
  }
  const form=(id,n,bygg,personlig=false)=>{const f=document.getElementById(id),utkast=bindUtkast(f,a.revision);
    f.onsubmit=async e=>{e.preventDefault();if(!aktuell()||!utkast.klar())return;const b=f.querySelector('button[type="submit"]');b.disabled=true;
      try{await anropa(n,bygg(new FormData(f),utkast.revision()),{utkast,personlig});}finally{if(aktuell())b.disabled=!utkast.klar();}};};
  const bindFunktioner=fu=>{const f=document.getElementById('ks-funktion');if(!f||!fu||fu.fel)return;
    const fyll=()=>{const o=fu.omraden.find(x=>x.id===f.elements.omrade.value);const s=f.elements.paket;s.replaceChildren(...o.paket.map(p=>{const op=document.createElement('option');op.value=p.id;op.textContent=p.funktion;return op;}));visa();};
    const visa=()=>{const o=fu.omraden.find(x=>x.id===f.elements.omrade.value),p=o&&o.paket.find(x=>x.id===f.elements.paket.value);
      document.getElementById('ks-paket-besked').textContent=p?p.niva+' · '+p.fardighet+': '+p.fardighet_omfattning:'';};
    f.elements.omrade.addEventListener('change',fyll);f.elements.paket.addEventListener('change',visa);fyll();
    const valid=crypto.randomUUID();
    form('ks-funktion','integrationsval',(v,revision)=>({revision,val:{id:valid,omrade:v.get('omrade'),paket:v.get('paket'),motivering:v.get('motivering'),...(v.get('behov')?{behov:v.get('behov')}:{})}}));
    document.querySelectorAll('[data-ks-avmarkera]').forEach(b=>b.onclick=()=>anropa('avmarkera_integration',{revision:a.revision,val:b.dataset.ksAvmarkera}));};
  bindFunktioner(d.funktioner);
  const exportop=crypto.randomUUID();document.getElementById('ks-overlamna').onclick=()=>anropa('overlamna',{revision:a.revision,operation:exportop});
  document.getElementById('ks-aterstall')?.addEventListener('click',()=>anropa('aterstall_overlamning',{operation:a.overlamning.id}));
  form('ks-erbjudande','erbjudande',(f,revision)=>({revision,text:f.get('text'),villkor:f.get('villkor'),ansvarig:f.get('ansvarig')}));
  form('ks-deltagare','deltagare',(f,revision)=>({revision,namn:f.get('namn'),roll:f.get('roll'),dagar:Number(f.get('dagar'))}),true);
  form('ks-lagring','lagringsbeslut',(f,revision)=>({revision,radera_efter:new Date(f.get('datum')).getTime()/1000,andamal:f.get('andamal'),ansvarig:f.get('ansvarig')}));
  const fragaid=crypto.randomUUID();form('ks-fraga','returfraga',(f,revision)=>({revision,overlamning:a.overlamning?.id,fraga:{id:fragaid,amne:f.get('amne'),text:f.get('text'),varfor:f.get('varfor'),fas:f.get('fas'),kritisk:f.has('kritisk'),ansvarig:'kund'}}));
  document.querySelectorAll('[data-ks-aterkalla]').forEach(b=>b.onclick=()=>anropa('aterkalla_person',{revision:a.revision,person:b.dataset.ksAterkalla}));
  document.querySelectorAll('[data-ks-svar]').forEach(f=>{const q=f.dataset.ksSvar;f.id='ks-retursvar-'+q;
    form(f.id,'bedom_retursvar',(values,revision)=>({revision,fraga:q,svar_sha256:d.retursvar[q].svar_sha256,bedomning:values.get('bedomning'),ansvarig:values.get('ansvarig')}));});
  document.getElementById('ks-backup').onclick=async()=>{const r=await anropa('sakerhetskopia',{}, {refresh:false});if(r)meddelande('Lokal säkerhetskopia skapad: '+r.id+'. Ingen server eller återkommande process aktiverades.');};
  if(besked)meddelande(besked);if(personlig)engang(personlig);
}
