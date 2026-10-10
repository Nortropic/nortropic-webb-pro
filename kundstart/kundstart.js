'use strict';
const $=id=>document.getElementById(id), params=new URLSearchParams(location.hash.slice(1));
let eid=params.get('arende'), token=params.get('nyckel'), doc=null, busy=false;
let uppgiftsrevision=null,klarlagg=false;
const id=()=>crypto.randomUUID(), status=(s,fel=false)=>{$('status').textContent=s;$('status').classList.toggle('fel',fel);};
function lagra(k,v){try{sessionStorage.setItem(k,v);return true;}catch{status('Webbläsaren kan inte bevara utkastet i fliken. Kopiera din text innan du lämnar sidan.',true);return false;}}
function las(k){try{return sessionStorage.getItem(k);}catch{return null;}}
if(eid&&token){lagra('kundstart-lank',JSON.stringify({eid,token}));history.replaceState(null,'',location.pathname);}
else{try{({eid,token}=JSON.parse(las('kundstart-lank')||'{}'));}catch{}}
const draftKey='kundstart-utkast-'+eid, opKey='kundstart-operation-'+eid, fieldKey='kundstart-uppgift-'+eid;
const returKey='kundstart-retur-'+eid;let retur=null;
try{retur=JSON.parse(las(returKey)||'null');}catch{}
const ord={kunden_uppger:'Uppgift från er',kunden_bekraftar:'Bekräftad av er',tolkning:'AI:s tolkning',hypotes:'Antagande att pröva',preferens:'Önskat uttryck',okant:'Inte klarlagt',onskemal:'Önskemål',kundval:'Ert val',avstatt:'Bortvalt',framtida:'Längre fram',inte_relevant:'Inte aktuellt',forslag:'Förslag',olast:'Inte läst',okand:'Inte klarlagt',kunden_uppger_ratt:'Ni uppger att materialet får användas',saknar_ratt:'Användningsrätt saknas'};
ord.inte_last='Inte läst';
const benamning=v=>ord[v]||'Inte klarlagt';
const faser={forberedelse:'förberedelsen',skiss:'skisserna',helbygge:'hela webbplatsen',publicering:'publiceringen',forvaltning:'förvaltningen'};
const svarslagen={oppen:'Väntar på svar',svarad:'Svaret är mottaget',vet_inte:'Ni vill ha hjälp att avgöra',avstar:'Ni avstår',framtida:'Längre fram'};
function visaRetur(){const q=retur&&doc?.returfragor?.[retur.id];$('svarar-pa').hidden=!q;if(q){$('fragetext').textContent='Du svarar på: '+q.text;$('svarslage').value=retur.lage;}}
function valRetur(q){const val=q?{id:q.id,lage:'svarad'}:null;if(!lagra(returKey,JSON.stringify(val)))return;retur=val;visaRetur();$('svar').focus();}
const grundnamn={namn:'Verksamhetens namn',orgnr:'Organisationsnummer',kontaktvagar:'Kontaktvägar',typ:'Typ',varde:'Uppgift',belagg:'Källa',adress:'Adress',gata:'Gata',postnummer:'Postnummer',ort:'Ort',publik:'Får visas offentligt',roll:'Adressens användning',rackvidd:'Verksamhetsområde',orter:'Orter',oppettider:'Öppettider',dag:'Dag',oppnar:'Öppnar',stanger:'Stänger',kategorier:'Verksamhetskategorier',tjanster:'Tjänster',sprak:'Språk',webb:'Webbplats',doman:'Domän',e_post:'E-post',not:'Kommentar',sokkonsol_agare:'Ansvariga för sökuppföljning',omdomen_kalla:'Omdömeskälla',plattform:'Plattform',datum:'Datum',betyg:'Betyg',antal:'Antal',url:'Länk'};
function beskriv(v){if(Array.isArray(v))return v.length?v.map(beskriv).join('\n'):'Inte angivet';if(v&&typeof v==='object')return Object.entries(v).map(([k,x])=>(grundnamn[k]||k)+': '+beskriv(x)).join('\n');return v===true?'Ja':v===false?'Nej':String(v??'Inte angivet');}
function utkast(){return {id:$('uppgiftid').value,text:$('uppgifttext').value,amne:$('amne').value,lage:$('lage').value,klarlagg,skal:$('klarlaggningsskal').value};}
function sparaUtkast(){if(uppgiftsrevision===null&&doc&&($('uppgifttext').value||$('uppgiftid').value))uppgiftsrevision=doc.revision;return lagra(fieldKey,JSON.stringify({...utkast(),revision:uppgiftsrevision}));}
function fyllUtkast(u){klarlagg=u.klarlagg===true;$('klarlaggningsskal').value=u.skal||'';$('klarlaggningsfalt').hidden=!klarlagg;$('klarlaggningsskal').required=klarlagg;$('spara-uppgift').textContent=klarlagg?'Spara klarläggandet':'Spara uppgiften';$('uppgiftid').value=u.id||'';$('uppgifttext').value=u.text||'';if(u.amne)$('amne').value=u.amne;if(u.lage)$('lage').value=u.lage;uppgiftsrevision=u.revision??doc?.revision??null;$('jamfort-utkast').hidden=true;}
function tillgangsfel(e){if(e.http===403){doc=null;$('arbete').hidden=true;}status(e.message,true);}
function elm(tag,txt,cls){const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e;}
function knapp(txt,fn,skriv=true){const b=elm('button',txt);b.type='button';b.dataset.skriv=String(skriv);b.addEventListener('click',fn);return b;}
function kort(rubrik,txt,meta){const a=elm('article');a.append(elm('strong',rubrik),elm('p',txt));if(meta)a.append(elm('p',meta,'meta'));return a;}
async function api(method='GET',body){const r=await fetch('/api/arende/'+eid,{method,headers:{Authorization:'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store'});const data=await r.json();if(!r.ok){const e=new Error(data.fel||'Det gick inte att bekräfta svaret.');e.http=r.status;throw e;}return data;}
async function hamta(tyst=false){if(!eid||!token||busy)return;try{const next=await api();const andrad=!doc||doc.revision!==next.revision||JSON.stringify(doc.modell)!==JSON.stringify(next.modell);doc=next;if(andrad||!tyst)visa();if(!tyst)status('Senaste versionen är hämtad. Dina osparade utkast är kvar.');else if(andrad)status('Uppdraget har uppdaterats. Dina utkast är kvar.');}catch(e){tillgangsfel(e);}}
async function handling(n,data,revision=doc?.revision){if(busy||!doc)return false;busy=true;status('Sparar…');
 let digest;
 try{
 digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify([n,data])))),b=>b.toString(16).padStart(2,'0')).join('');
 const payload={handling:n,data,revision,operation:id()};let journal={};
 try{journal=JSON.parse(las(opKey)||'{}');}catch{}
 const fore=journal[digest];
 // Journalen bevarar identiteten, inte en extra kopia av text eller bilagor.
 if(fore){payload.operation=fore.operation;payload.revision=fore.revision;}
 journal[digest]={operation:payload.operation,revision:payload.revision};
 if(!lagra(opKey,JSON.stringify(journal)))return false;
 doc=await api('POST',payload);delete journal[digest];lagra(opKey,JSON.stringify(journal));visa();status('Sparat.');return true;
 }
 catch(e){if(e.http===409){let journal={};try{journal=JSON.parse(las(opKey)||'{}');}catch{}delete journal[digest];lagra(opKey,JSON.stringify(journal));try{doc=await api();visa();if(n==='uppgift'||n==='klarlagg_uppgift')$('jamfort-utkast').hidden=false;if(n==='integrationsbehov')$('jamfort-integration').hidden=false;if(n==='materialratt')$('jamfort-ratt').hidden=false;status('Uppdraget ändrades i en annan flik. Senaste versionen visas ovan. Jämför den med ditt bevarade utkast innan du sparar igen.',true);}catch(f){tillgangsfel(f);}}else tillgangsfel(e);return false;}
 finally{busy=false;}
}
function visa(){
 $('arbete').hidden=false;$('din-behorighet').textContent=doc.din_roll==='lasare'?'Din länk ger läsåtkomst.':doc.din_roll==='medverkande'?'Du kan lämna och rätta uppgifter. Beställningen hanteras av en beslutsfattare.':'Du kan lämna uppgifter och ta ställning till ett definierat erbjudande.';$('modellstatus').textContent=doc.modell.text||'AI är inte startad. Du kan spara svar och arbeta i Ditt uppdrag.';
 $('forsok').hidden=!['fel','avstangd','budget_slut','foraldrat'].includes(doc.modell.status);
 $('meddelanden').replaceChildren(...doc.meddelanden.map(m=>kort(m.roll==='kund'?'Du':'Nortropics AI-förslag',m.text,m.roll==='assistent'?'Förslag, inte beställning.':null)));
 $('uppgifter').replaceChildren(...Object.values(doc.uppgifter).map(u=>{const rubrik=Array.from($('amne').options).find(o=>o.value===u.amne)?.textContent||'Uppgift';const a=kort(rubrik,u.text,`${benamning(u.kunskap)} · ${benamning(u.bestallning)}${u.motsagelse?' · behöver klarläggas':''}`);a.append(knapp('Rätta uppgiften',()=>{fyllUtkast({...u,lage:u.bestallning});sparaUtkast();$('uppgifttext').focus();}),knapp('Bekräfta denna uppgift',()=>handling('bekrafta',{ids:[u.id]})));if(u.motsagelse&&doc.din_roll==='beslutsfattare')a.append(knapp('Klarlägg de motstridiga uppgifterna',()=>{fyllUtkast({...u,lage:u.bestallning,klarlagg:true,revision:doc.revision});sparaUtkast();$('uppgifttext').focus();}));return a;}));
 if(!Object.keys(doc.uppgifter).length)$('uppgifter').append(elm('p','Inga uppgifter är införda ännu. Du kan lägga till och rätta dem nedan.'));
 $('forslag').replaceChildren(...Object.values(doc.forslag).map(p=>{const a=kort('Förslag',p.text,benamning(p.kunskap));a.append(knapp('Använd som utgångspunkt för en uppgift',()=>{fyllUtkast({...p,lage:'onskemal',revision:doc.revision});sparaUtkast();$('uppgifttext').focus();}));return a;}));
 $('fragor').replaceChildren(...doc.fragor.map(q=>kort(q.text,q.varfor,`Påverkar: ${q.paverkar}${q.kritisk?' · behöver besvaras inför nästa berörda steg':''}`)));
 $('returfragor').replaceChildren(...Object.values(doc.returfragor||{}).map(q=>{const a=kort(q.text,q.varfor,`Komplettering inför ${faser[q.fas]||'nästa steg'} · ${svarslagen[q.status]||'Behöver klarläggas'}${q.kritisk?' · viktig för det steget':''}`);a.append(knapp('Svara på kompletteringen',()=>valRetur(q)));return a;}));
 visaRetur();
 const ilagen={okant:'inte kontrollerat',dokumenterat:'dokumenterat stöd',saknas:'stöd saknas',tillgang_bekraftad:'åtkomst bekräftad',inte_provat:'inte provad',lokalt_provat:'lokalt provad',skarpt_provat:'provad i den verkliga kopplingen',underkant:'provet underkänt'};
 $('integrationsstatus').replaceChildren(...Object.values(doc.integrationer||{}).map(i=>kort(i.behov,i.uppgift||'Användaruppgiften behöver klarläggas vidare.',
   `Leverantör: ${ilagen[i.utredning.leverantor.status]} · ert konto: ${ilagen[i.utredning.konto.status]} · kopplingen: ${ilagen[i.utredning.prov.status]}${i.utredning.status==='inaktuell'?' · behöver utredas igen efter ändrat behov':''}`)));
 // Detta behöver vi från er (handlingskön ur planen): status och ansvarig, aldrig beläggens detaljer eller ägarens handlingar
 const hk=doc.handlingsko||{},hstatus={vantar:'Väntar',klar:'Klar',inaktuell:'Inte längre aktuell'};
 $('handlingssammanfattning').textContent=hk.fel?hk.fel:hk.sammanfattning?`${hk.sammanfattning.vantar_pa_kunden} väntar på er. En punkt blir klar först när det finns ett belägg, till exempel att nyckeln har lämnats.`:'';
 $('handlingslista').replaceChildren(...(hk.poster||[]).filter(p=>p.status!=='inaktuell'||p.ansvarig==='kund').map(p=>kort(p.handling,`Varför: ${p.skal}. Under tiden kan detta fortsätta: ${p.under_vantan}.`,`${hstatus[p.status]||p.status} · ansvarig: ${p.ansvarig_text}`)));
 const nycklar=[...new Set((hk.poster||[]).filter(p=>p.nyckel&&p.status!=='inaktuell').map(p=>p.nyckel))];
 $('nyckeldel').hidden=!nycklar.length;
 if($('nyckellev').options.length!==nycklar.length)$('nyckellev').replaceChildren(...nycklar.map(n=>{const o=elm('option',n);o.value=n;return o;}));
 const grund=doc.verksamhet_forslag;$('grunduppgifter').hidden=!grund;
 $('grundvarden').replaceChildren(...Object.entries(grund?.varden||{}).filter(([k])=>!['schema','fiktiv'].includes(k)).map(([k,v])=>kort(grundnamn[k]||k,beskriv(v))));
 $('bekrafta-grund').textContent=doc.verksamhet?.sha256===grund?.sha256?'Stäm av verksamhetsuppgifterna igen':'Dessa verksamhetsuppgifter stämmer';
 $('material').replaceChildren(...doc.material.map(m=>{const a=kort(m.namn,`${benamning(m.lasning)} · ${benamning(m.rattighet)}`);a.append(knapp('Hämta filen',async()=>{try{const r=await fetch(`/api/arende/${eid}/bilaga/${m.id}`,{headers:{Authorization:'Bearer '+token}});if(!r.ok)throw Error('Filen kunde inte hämtas.');const url=URL.createObjectURL(await r.blob()),link=elm('a');link.href=url;link.download=m.namn;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){status(e.message,true);}},false),knapp('Beskriv användningsrätten',()=>valRatt(m)));return a;}));
 $('bestallningsstatus').textContent=doc.bestallning.status==='accepterad'?(doc.bestallning.aktuell?'Det definierade erbjudandet är accepterat.':'Underlaget har ändrats sedan acceptansen. Omfattningen behöver prövas igen.'):doc.bestallning.status==='forfragan'?'Din förfrågan är inlämnad för beredning.':'Du kan skicka en förfrågan när uppdraget är tillräckligt beskrivet.';
 $('erbjudande').replaceChildren();const offer=doc.erbjudanden.at(-1);if(offer){const a=kort('Definierat erbjudande',offer.text,offer.villkor);a.append(knapp('Acceptera detta erbjudande',()=>handling('acceptera',{erbjudande:offer.id})));$('erbjudande').append(a);}
 const lasare=doc.din_roll==='lasare';document.querySelectorAll('form input,form textarea,form select,form button,[data-skriv="true"]').forEach(e=>e.disabled=lasare);
 $('forfragan').disabled=doc.din_roll!=='beslutsfattare';$('nyckelknapp').disabled=doc.din_roll!=='beslutsfattare';$('forsok').disabled=lasare;$('bekrafta-grund').disabled=lasare;
 $('erbjudande').querySelectorAll('button').forEach(e=>e.disabled=doc.din_roll!=='beslutsfattare');
 visaRatt();
}
$('svar').value=las(draftKey)||'';$('svar').addEventListener('input',()=>lagra(draftKey,$('svar').value));
$('svarform').addEventListener('submit',async e=>{e.preventDefault();const v=$('svar').value;const q=retur&&doc?.returfragor?.[retur.id];
 if(retur&&!q){status('Kompletteringen kunde inte hittas. Ditt utkast är kvar; välj samtalet eller hämta senaste versionen.',true);return;}
 if(await handling(q?'besvara_fraga':'meddelande',q?{id:q.id,text:v,lage:retur.lage}:{text:v})){if($('svar').value===v){$('svar').value='';lagra(draftKey,'');}if(q)valRetur(null);$('svar').focus();}});
$('svarslage').addEventListener('change',()=>{if(retur){retur={...retur,lage:$('svarslage').value};lagra(returKey,JSON.stringify(retur));}});
$('lamna-fraga').addEventListener('click',()=>valRetur(null));
try{const sparat=JSON.parse(las(fieldKey)||'null');if(sparat)fyllUtkast(sparat);}catch{}
for(const name of ['uppgifttext','amne','lage','klarlaggningsskal'])$(name).addEventListener('input',sparaUtkast);
$('uppgiftsform').addEventListener('submit',async e=>{e.preventDefault();if(!$('uppgiftid').value)$('uppgiftid').value=id();if(!sparaUtkast())return;const u=utkast(),data=klarlagg?{id:u.id,text:u.text,skal:u.skal}:{id:u.id,text:u.text,amne:u.amne,lage:u.lage};if(await handling(klarlagg?'klarlagg_uppgift':'uppgift',data,uppgiftsrevision)){if(JSON.stringify(utkast())===JSON.stringify(u)){fyllUtkast({});uppgiftsrevision=null;sparaUtkast();}}});
$('jamfort-utkast').addEventListener('click',()=>{uppgiftsrevision=doc?.revision??null;sparaUtkast();$('jamfort-utkast').hidden=true;status('Utkastet är kvar. Spara uppgiften om det är den ändring du vill göra.');});
$('avbryt-rattning').addEventListener('click',()=>{fyllUtkast({});uppgiftsrevision=null;sparaUtkast();});
$('bilageform').addEventListener('submit',async e=>{e.preventDefault();const f=$('fil').files[0];if(!f)return;if(f.size>4*1024*1024){status('Filen är större än 4 MB.',true);return;}const bytes=new Uint8Array(await f.arrayBuffer());let str='';for(let i=0;i<bytes.length;i+=8192)str+=String.fromCharCode(...bytes.subarray(i,i+8192));if(await handling('bilaga',{namn:f.name,typ:f.type||'text/plain',data:btoa(str)}))$('fil').value='';});
$('forsok').addEventListener('click',()=>handling('forsok_igen',{}));$('hamta').addEventListener('click',()=>hamta());$('forfragan').addEventListener('click',()=>handling('forfragan',{}));
$('bekrafta-grund').addEventListener('click',()=>{if(doc?.verksamhet_forslag)handling('bekrafta_verksamhet',{sha256:doc.verksamhet_forslag.sha256});});
setInterval(()=>{if(!document.hidden&&!busy&&['ko','pagar'].includes(doc?.modell.status))hamta(true);},8000);
hamta();

// Separata utkast med ursprungsrevision för funktioner och materialbesked.
const intKey='kundstart-integration-'+eid,rattKey='kundstart-ratt-'+eid;
let intRev=null,rattRev=null;
function intData(){return {id:$('integrationid').value,behov:$('integrationsbehov').value,befintligt:$('befintligt-system').value||null,lage:$('integrationslage').value};}
function sparaInt(){if(intRev===null&&doc)intRev=doc.revision;return lagra(intKey,JSON.stringify({data:intData(),revision:intRev}));}
function rattData(){return {id:$('rattfil').value,lage:$('rattlage').value,grund:$('rattgrund').value};}
function sparaRatt(){return lagra(rattKey,JSON.stringify({data:rattData(),revision:rattRev}));}
function visaRatt(){const m=doc?.material.find(x=>x.id===$('rattfil').value);$('rattighetsform').hidden=!m;if(m)$('rattnamn').textContent=m.namn;}
function valRatt(m){$('rattfil').value=m.id;$('rattlage').value=m.rattighet;$('rattgrund').value=m.rattighetsgrund||'';rattRev=doc.revision;sparaRatt();visaRatt();$('rattlage').focus();}
try{const u=JSON.parse(las(intKey)||'null');if(u){$('integrationid').value=u.data.id;$('integrationsbehov').value=u.data.behov;$('befintligt-system').value=u.data.befintligt||'';$('integrationslage').value=u.data.lage;intRev=u.revision;}}catch{}
try{const u=JSON.parse(las(rattKey)||'null');if(u){$('rattfil').value=u.data.id;$('rattlage').value=u.data.lage;$('rattgrund').value=u.data.grund;rattRev=u.revision;}}catch{}
for(const n of ['integrationsbehov','befintligt-system','integrationslage'])$(n).addEventListener('input',sparaInt);
for(const n of ['rattlage','rattgrund'])$(n).addEventListener('input',sparaRatt);
$('integrationsform').addEventListener('submit',async e=>{e.preventDefault();if(!$('integrationid').value)$('integrationid').value=id();if(!sparaInt())return;const data=intData();if(await handling('integrationsbehov',data,intRev)){if(JSON.stringify(intData())===JSON.stringify(data)){$('integrationid').value='';$('integrationsbehov').value='';$('befintligt-system').value='';intRev=null;lagra(intKey,'null');}}});
$('rattighetsform').addEventListener('submit',async e=>{e.preventDefault();if(!sparaRatt())return;const data=rattData();if(await handling('materialratt',data,rattRev)){if(JSON.stringify(rattData())===JSON.stringify(data)){$('rattfil').value='';rattRev=null;lagra(rattKey,'null');visaRatt();}}});
$('jamfort-integration').addEventListener('click',()=>{intRev=doc.revision;sparaInt();$('jamfort-integration').hidden=true;});
$('jamfort-ratt').addEventListener('click',()=>{rattRev=doc.revision;sparaRatt();$('jamfort-ratt').hidden=true;});
// Nyckeln skickas direkt och fältet töms före svaret; den sparas aldrig i webbläsarens lagring (handling() sparar bara
// begärans id och revision, inte innehållet).
$('nyckelform').addEventListener('submit',async e=>{e.preventDefault();const nyckel=$('nyckelvarde').value.trim();$('nyckelvarde').value='';
 const falt=Object.fromEntries($('nyckelfalt').value.split('\n').map(r=>r.split('=')).filter(x=>x.length===2&&x[0].trim()).map(([k,v])=>[k.trim(),v.trim()]));
 const data={leverantor:$('nyckellev').value,...(nyckel?{nyckel}:{}),...(Object.keys(falt).length?{falt}:{})};
 if(await handling('nyckel',data)){$('nyckelfalt').value='';status('Lämnat. Nyckeln visas inte igen.');}});
