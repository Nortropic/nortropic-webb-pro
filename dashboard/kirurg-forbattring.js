// Befintliga Kirurgens privata förbättringsposter. Startar inga modeller eller försök.
let kirurgForbattringGeneration=0;
async function kirurgForbattring(sparbesked='') {
  const generation=++kirurgForbattringGeneration, host=document.getElementById('kirurg-forbattring');
  const aktuell=()=>generation===kirurgForbattringGeneration && location.hash==='#/kirurgen' && host===document.getElementById('kirurg-forbattring');
  if(!host)return;
  let d;
  try{d=await api('/api/kirurg/forbattringar');}catch(e){if(aktuell())host.innerHTML=`<section><h2>Förbättringsarbete</h2><p role="alert">Underlaget kunde inte läsas: ${esc(e.message)}</p></section>`;return;}
  if(!aktuell())return;
  const etikett=x=>({overlamningsfel:'Överlämningsfel',saknat_underlag:'Saknat underlag',kunskapsfel:'Kunskapsfel',metodkoppling:'Metodens tillämpning',verktygsatkomst:'Verktygsåtkomst',implementation:'Implementation',bedomning:'Bedömning',saknad_verifiering:'Saknad verifiering',mojlighet:'Möjlig förbättring',oppen:'Öppen',delide:'Delidé',forsok:'Försök föreslaget',parkera:'Parkerad',avslag:'Avslagen',regression_rattad:'Regressionsfelet rättat i kopian',oforandrat:'Oförändrat',forsamrat:'Försämrat',ofullstandigt:'Ofullständigt',pagar:'Pågår',avbrutet:'Avbrutet',klart:'Avslutat',fel:'Fel',inte_infort:'Inte infört',infort:'Verifierat i lokal Git-version',aterstallt:'Manuell återställning verifierad',forbattrat:'Rapporterad förbättring',blandat:'Blandat',inte_observerad:'Inte observerad',verifierad:'Överföringen verifierad',nytt_underlag:'Ny överlämning behövs',saknad_overlamning:'Ingen överlämning',overlamning_inte_klar:'Överlämningen är inte klar'}[x]||x||'Inte observerat');
  const tid=x=>typeof x==='number'?new Date(x*1000).toLocaleString('sv-SE'):'aldrig observerad';
  const rank={sanning_sakerhet:0,stor:1,begransad:2};
  const poster=Object.values(d.poster).sort((a,b)=>(rank[a.diagnoser.at(-1)?.konsekvens]??3)-(rank[b.diagnoser.at(-1)?.konsekvens]??3));
  const field=(id,name,label,type='textarea',value='')=>`<label for="${id}-${name}" style="display:block;margin-top:10px">${label}</label>${type==='textarea'?`<textarea id="${id}-${name}" name="${name}" required>${esc(value)}</textarea>`:`<input type="text" id="${id}-${name}" name="${name}" value="${esc(value)}" required>`}`;
  const select=(id,name,label,opts)=>`<label for="${id}-${name}" style="display:block;margin-top:10px">${label}</label><select id="${id}-${name}" name="${name}">${opts.map(([v,t])=>`<option value="${v}">${t}</option>`).join('')}</select>`;
  host.innerHTML=`<section aria-labelledby="kf-rubrik"><h2 id="kf-rubrik">Förbättringsarbete</h2>
    <p>Observation → diagnos → avgränsat försök → granskad ändring → uppföljning. Ett grönt lokalt prov är inte ett införande eller en observerad förbättring i kundarbetet.</p>
    <p id="kf-status" role="status" aria-live="polite"></p>
    <p id="kf-pausbesked">${d.paus?'Nya och pågående förbättringsförsök är pausade.':'Lokala försök kan beställas inom ett giltigt ägarmandat.'} Bevakning och analys kan fortsätta. Ingen ny schemaläggning är aktiverad.</p>
    <button class="knapp" type="button" id="kf-paus">${d.paus?'Häv försöks­pausen':'Pausa förbättringsförsök'}</button>
    <button class="knapp" type="button" id="kf-uppdatera">Läs aktuellt tillstånd</button>
    <details><summary>Källbevakningens hälsa</summary><p>Senaste försök och senaste lyckade hämtning visas var för sig. Oförändrat innehåll är inte samma sak som ett misslyckat anrop.</p>
    ${d.kallhalsa?.status==='lasfel'?'<p role="alert">Källhälsan kunde inte läsas. Beroende försök kan inte köras förrän underlaget har återställts.</p>':Object.values(d.kallhalsa?.kallor||{}).map(k=>`<article><h3>${esc(k.namn)}</h3><p>${k.status==='ok'?'Senaste hämtningen lyckades':'Senaste hämtningen misslyckades'} · försök ${esc(tid(k.forsok))} · senaste lyckade ${esc(tid(k.senast_lyckad))}</p>${k.fel?`<p>${esc(k.fel)}</p>`:''}</article>`).join('')||'<p>Ingen källhälsa har observerats ännu.</p>'}</details>
    <details><summary>Observerad överlämning från Kundstart</summary><p>Detta mäter bevarade uppgifter, inte design- eller intervjukvalitet. Använt och levererat är okänt tills de stegen har observerats.</p>
    ${Object.values(d.kundstart||{}).map(o=>`<p>${esc(etikett(o.status))} · revision ${o.revision} · insamlat ${o.insamlat} · överfört ${o.overfort??'inte verifierat'} · använt ${o.anvant??'inte observerat'} · levererat ${o.levererat??'inte observerat'}</p>`).join('')||'<p>Inga överlämningar har observerats.</p>'}</details>
    <details><summary>Lägg till en konkret observation</summary><form id="kf-signal" data-kf="signal" data-revision="0">
      ${field('kf-signal','problem','Gemensam problemnyckel','input')}${field('kf-signal','titel','Kort beskrivning','input')}
      ${select('kf-signal','fas','Berört steg',['kundstart','forberedelse','referenser','skiss','forfining','helbygge','granskning','leverans','forvaltning'].map(x=>[x,etikett(x)]))}
      ${field('kf-signal','kalla','Källans identitet','input')}${field('kf-signal','version','Källversion','input')}
      ${field('kf-signal','observation','Vad har faktiskt observerats?')}${field('kf-signal','belagg','Var finns belägget?')}
      <button class="knapp" type="submit">Spara observationen</button></form></details>
    <p>${poster.length} förbättringsposter. Ordningen följer bedömd konsekvens; källans ålder eller popularitet avgör inte nyttan.</p>
    ${poster.slice(0,100).map(p=>{const id=p.id,diag=p.diagnoser.at(-1),plan=p.planer.at(-1);return `<details class="post" data-kf-post="${id}"><summary><span class="titel">${esc(p.titel)}</span><span class="chip">${esc(etikett(p.disposition))}</span>${p.nytt_underlag?'<span class="chip">Nytt underlag för omprövning</span>':''}</summary><div class="innehall">
      <p>${esc(id)} · ${esc(p.fas)} · revision ${p.revision}</p>
      <p>Införande: ${esc(etikett(p.inforande))}. Eftereffekt: ${esc(etikett(p.effekt))}.</p>
      ${(p.inforanden||[]).map(b=>`<p>Införandebevis: <code>${esc(b.version)}</code> · ${esc(b.gren)} · ${esc(tid(b.tid))}. ${esc(b.omfattning)}. Granskning: ${esc(b.granskning)}.</p>`).join('')}
      ${(p.uppfoljning||[]).map(u=>`<p>Inrapporterad observation: ${esc(etikett(u.utfall))} · ${esc(u.observator)} · ${esc(tid(u.tid))}. Omfattning: ${esc(u.omfattning)}. Belägg: ${esc(u.bevis)}. Version: <code>${esc(u.version||'inte versionsbunden')}</code>.</p>`).join('')}
      ${(p.aterstallningar||[]).map(a=>`<p>Återställningsbevis: <code>${esc(a.version)}</code> · ${esc(tid(a.tid))}. ${esc(a.omfattning)}.</p>`).join('')}
      ${p.signaler.map(s=>`<article><h3>${esc(s.kalla)}</h3><p>${esc(s.version)} · ${esc(s.observation)}</p><p>Belägg: ${esc(s.belagg)}${s.del?' · delidé: '+esc(s.del):''}</p></article>`).join('')}
      <p>${diag?`Diagnos: ${esc(etikett(diag.slag))} · ${esc(diag.belaggsstyrka)}. ${esc(diag.skal)} Alternativ: ${esc(diag.alternativ)}`:'Ingen diagnos ännu.'}</p>
      ${p.skal?`<p>Dispositionens skäl: ${esc(p.skal)}. Omprövas när: ${esc(p.ateroppna||'ingen särskild tröskel angiven')}.</p>`:''}
      ${p.backlog?`<p>Befintlig backlogpost: ${esc(p.backlog)}</p>`:''}
      <details><summary>Diagnostisera problemet</summary><form id="${id}-diagnos" data-kf="diagnos" data-pid="${id}" data-revision="${p.revision}">
      ${select(id,'slag','Problemtyp',['saknat_underlag','overlamningsfel','kunskapsfel','metodkoppling','verktygsatkomst','implementation','bedomning','saknad_verifiering','mojlighet'].map(x=>[x,etikett(x)]))}
      ${field(id,'skal','Varför denna diagnos?')}${field(id,'alternativ','Alternativa förklaringar')}
      ${select(id,'konsekvens','Konsekvens',[['sanning_sakerhet','Sanning eller säkerhet'],['stor','Stor'],['begransad','Begränsad']])}
      ${select(id,'belaggsstyrka','Beläggens styrka',[['hypotes','Hypotes'],['observerat','Observerat'],['reproducerat','Reproducerat']])}
      <button class="knapp" type="submit">Spara diagnosen</button></form></details>
      <details><summary>Bestäm disposition</summary><form id="${id}-disposition" data-kf="disposition" data-pid="${id}" data-revision="${p.revision}">
      ${select(id+'-d','val','Disposition',['oppen','delide','forsok','parkera','avslag'].map(x=>[x,etikett(x)]))}
      ${field(id+'-d','skal','Skäl')}${field(id+'-d','ateroppna','När ska detta omprövas?')}
      <button class="knapp" type="submit">Spara dispositionen</button></form></details>
      <details><summary>Förhandsbestäm försöket</summary>${plan?`<p>Aktuell fråga: ${esc(plan.fraga)}. Framgång: ${esc(plan.framgang)}. Försämring: ${esc(plan.forsamring)}.</p>`:''}
      <form id="${id}-plan" data-kf="plan" data-pid="${id}" data-revision="${p.revision}">
      ${[['fraga','Fråga'],['jamforelse','Vad jämförs?'],['framgang','Vad räknas som framgång?'],['forsamring','Vad räknas som försämring?'],['andel','Avgränsning'],['risk','Risk'],['ansvarig','Ansvarig']].map(([k,t])=>field(id+'-p',k,t)).join('')}
      ${select(id+'-p','provtyp','Provtyp',[['regression','Regressionsprov'],['atkomst','Åtkomst'],['integration','Integration'],['design','Design'],['intervju','Intervju']])}
      <button class="knapp" type="submit">Spara planen</button></form><p>Planen ger inget körmandat. Den lokala försöksingången stöder regressionsprov; övriga provtyper kräver sin särskilda verifiering.</p></details>
      ${p.forsok.map(id=>{const f=d.forsok[id];return f?`<article><h3>Försök ${esc(id)}</h3><p>${esc(etikett(f.status))} · ${esc(etikett(f.utfall))} · ${esc(etikett(f.inforande))}</p><p>Före: ${f.fore?.godkant===true?'provet klarat':f.fore?.reproducerat?'regressionsfelet reproducerat':'ofullständigt eller inte kört'}. Efter: ${f.efter?.godkant===true?'provet klarat':'ofullständigt eller inte klarat'}.</p><p>Reserverad provtid ${f.budget_reserverad_sekunder??'okänd'} s. Verklig eftereffekt: ${esc(etikett(f.effekt))}.</p></article>`:'';}).join('')}
      </div></details>`;}).join('')||'<p>Inga förbättringsposter ännu. Befintligt intag, register och backlog finns kvar nedan.</p>'}
    <details><summary>Stickprov bland parkerade och avslagna idéer</summary><form id="kf-stickprov"><label for="kf-seed">Urvalsnyckel för ett upprepningsbart urval</label><input type="text" id="kf-seed" name="seed" required pattern="[a-zA-Z0-9_-]{1,100}"><button class="knapp" type="submit">Visa fem poster</button></form><div id="kf-stickprov-resultat"></div><p>Urvalet görs bland alla parkerade och avslagna poster, inte bara föreslagna vinnare.</p></details>
    <details><summary>Förbrukad mandatbudget</summary>${Object.entries(d.forbrukat).map(([m,n])=>`<p>${esc(m)}: ${n} operationer har reserverats enligt mandatets klass. Avbrott återställer inte budgeten.</p>`).join('')||'<p>Ingen försöksbudget har förbrukats.</p>'}</details></section>`;
  const besked=t=>{if(aktuell())document.getElementById('kf-status').textContent=t;};
  besked(sparbesked);
  document.getElementById('kf-paus').onclick=async e=>{const b=e.target;b.disabled=true;try{await post('/api/kirurg/forbattringar/paus',{paus:!d.paus});d.paus=!d.paus;if(!aktuell())return;b.textContent=d.paus?'Häv försöks­pausen':'Pausa förbättringsförsök';document.getElementById('kf-pausbesked').textContent=d.paus?'Förbättringsförsöken är pausade. Bevakning och analys fortsätter.':'Pausen är hävd. Ett giltigt mandat krävs fortfarande; inget nytt försök startades.';besked('Pausbeslutet är sparat.');}catch(e){besked(e.message);}finally{if(aktuell())b.disabled=false;}};
  document.getElementById('kf-uppdatera').onclick=()=>kirurgForbattring();
  for(const f of host.querySelectorAll('form[data-kf]')){
    const key='nwp-kirurg-utkast:'+f.id;let draft=null,lagringsfel=false;
    const button=f.querySelector('button[type="submit"]'),info=document.createElement('p'),jamfor=document.createElement('button');
    jamfor.type='button';jamfor.className='knapp';jamfor.textContent='Jag har jämfört utkastet med aktuell revision';f.append(info,jamfor);
    const values=()=>Object.fromEntries(new FormData(f));
    try{const raw=sessionStorage.getItem(key);if(raw){draft=JSON.parse(raw);if(!draft||!Number.isInteger(draft.revision)||typeof draft.varden!=='object')throw Error('ogiltigt utkast');for(const [n,v] of Object.entries(draft.varden)){if(f.elements.namedItem(n))f.elements.namedItem(n).value=v;}}}
    catch(e){lagringsfel=true;}
    const stale=()=>draft&&draft.revision!==Number(f.dataset.revision);
    const visa=()=>{button.disabled=lagringsfel||!!stale();jamfor.hidden=!stale();info.textContent=lagringsfel?'Utkastet kunde inte bevaras. Kopiera texten; ingen handling skickas.':stale()?'Detta utkast gäller en äldre revision. Jämför med observationen ovan före sparande.':'';};
    const spara=()=>{try{sessionStorage.setItem(key,JSON.stringify(draft));}catch(e){lagringsfel=true;}visa();};
    f.oninput=()=>{draft={revision:draft?.revision??Number(f.dataset.revision),varden:values()};spara();};
    f.onchange=f.oninput;
    jamfor.onclick=()=>{draft={revision:Number(f.dataset.revision),varden:values()};spara();};visa();
    f.onsubmit=async e=>{e.preventDefault();if(!aktuell()||lagringsfel||stale())return;button.disabled=true;
      const name=f.dataset.kf,vals=values(),data=name==='signal'?vals:{pid:f.dataset.pid,revision:Number(f.dataset.revision),...(name==='plan'?{plan:vals}:vals)};
      if(!draft){draft={revision:Number(f.dataset.revision),varden:vals};spara();if(lagringsfel)return;}
      const sent=JSON.stringify(draft);
      try{await post('/api/kirurg/forbattringar/'+name,data);if(sessionStorage.getItem(key)===sent)sessionStorage.removeItem(key);if(aktuell())await kirurgForbattring('Sparat. Ingen modell, försökskörning eller publicering startades.');}
      catch(e){besked('Kunde inte bekräfta sparningen: '+e.message+'. Texten finns kvar; läs aktuellt tillstånd innan du försöker igen.');if(aktuell())visa();}};
  }
  document.getElementById('kf-stickprov').onsubmit=async e=>{e.preventDefault();try{const r=await post('/api/kirurg/forbattringar/stickprov',{seed:new FormData(e.target).get('seed'),antal:5});if(aktuell())document.getElementById('kf-stickprov-resultat').innerHTML=r.poster.map(p=>`<p>${esc(p.titel)} · ${esc(p.id)} · ${esc(p.skal)}</p>`).join('')||'<p>Inga parkerade eller avslagna poster.</p>';}catch(e){besked(e.message);}};
}
