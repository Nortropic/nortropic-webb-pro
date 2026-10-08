// Riktig lokal dashboard och API; befintligt intag/spaning är nätlösa provsvar.
import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const root=resolve(process.argv[2]||'.');
const child=spawn(resolve(root,'.venv/bin/python'),['-B','kontroller/rokprov/revision/prov_kundstart_agare.py','--provserver'],{cwd:root,stdio:['ignore','pipe','pipe']});
let browser,stderr='';child.stderr.on('data',b=>stderr+=b);
try{
 const init=await new Promise((res,rej)=>{let s='';const timer=setTimeout(()=>rej(Error('Provservern startade inte')),10000);child.on('exit',()=>{clearTimeout(timer);rej(Error(stderr));});child.stdout.on('data',b=>{s+=b;if(s.includes('\n')){clearTimeout(timer);res(JSON.parse(s.split('\n')[0]));}});});
 const origin=`http://127.0.0.1:${init.port}`;
 browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
 await page.route('**/api/kirurg',r=>r.fulfill({json:{intag:[],register:[],overens:{}}}));
 await page.route('**/api/spaning',r=>r.fulfill({json:{kandidater:[],pagar:false,senast:null,av:true}}));
 await page.route('**/api/oversikt',r=>r.fulfill({json:{byggen:[],prospekt_vantar:0,backlog_vilande:0,intag_pagar:0,granskare:{}}}));
 await page.goto(origin+'/#/kirurgen');await page.getByRole('heading',{name:'Förbättringsarbete',exact:true}).waitFor();
 const box=page.locator('#kirurg-forbattring');
 await box.getByText('Lägg till en konkret observation',{exact:true}).click();
 for(const [name,val] of [['Gemensam problemnyckel','syntetisk-overforing'],['Kort beskrivning','Ett överfört fält saknas'],['Källans identitet','Kontrollerad teststörning'],['Källversion','v1'],['Vad har faktiskt observerats?','Ett redan insamlat fält tappades.'],['Var finns belägget?','Syntetiskt lokalt prov.']])await box.getByLabel(name,{exact:true}).fill(val);
 const submit=box.getByRole('button',{name:'Spara observationen',exact:true});await submit.focus();await page.keyboard.press('Enter');
 await box.getByRole('status').filter({hasText:'Sparat.'}).waitFor();
 const card=box.locator('details[data-kf-post]');await card.locator(':scope > summary').click();
 await card.getByText('Diagnostisera problemet',{exact:true}).click();
 await card.getByLabel('Varför denna diagnos?',{exact:true}).fill('Källan innehåller redan uppgiften.');
 await card.getByLabel('Alternativa förklaringar',{exact:true}).fill('Filen kan ha ändrats efter överlämningen.');
 await card.getByLabel('Problemtyp',{exact:true}).selectOption('overlamningsfel');
 await card.getByLabel('Beläggens styrka',{exact:true}).selectOption('observerat');
 await card.getByRole('button',{name:'Spara diagnosen',exact:true}).click();
 await box.getByRole('status').filter({hasText:'Sparat.'}).waitFor();
 await box.locator('details[data-kf-post] > summary').click();
 await box.getByText('Bestäm disposition',{exact:true}).click();
 await box.getByLabel('Skäl',{exact:true}).fill('Ett bevarat utkast.');
 await box.getByRole('button',{name:'Läs aktuellt tillstånd',exact:true}).click();
 await box.locator('details[data-kf-post] > summary').click();await box.getByText('Bestäm disposition',{exact:true}).click();
 assert.equal(await box.getByLabel('Skäl',{exact:true}).inputValue(),'Ett bevarat utkast.');
 await box.getByLabel('Disposition',{exact:true}).selectOption('parkera');
 await box.getByLabel('När ska detta omprövas?',{exact:true}).fill('När ett nytt belägg finns.');
 await box.getByRole('button',{name:'Spara dispositionen',exact:true}).click();
 await box.getByRole('status').filter({hasText:'Sparat.'}).waitFor();
 await box.getByRole('button',{name:'Pausa förbättringsförsök',exact:true}).click();
 await box.getByRole('status').filter({hasText:'Pausbeslutet'}).waitFor();
 const reg=await (await page.request.get(origin+'/api/kirurg/forbattringar')).json();assert(reg.paus);assert.equal(Object.keys(reg.forsok).length,0);
 await box.getByText('Stickprov bland parkerade och avslagna idéer',{exact:true}).click();
 await box.getByLabel('Urvalsnyckel för ett upprepningsbart urval',{exact:true}).fill('provseed');
 await box.getByRole('button',{name:'Visa fem poster',exact:true}).click();await box.locator('#kf-stickprov-resultat').getByText('Ett överfört fält saknas',{exact:false}).waitFor();
 // Rendering av ett syntetiskt versionsbundet införande; mekaniken prövas separat via verklig Git.
 const visa=structuredClone(reg),post=Object.values(visa.poster)[0];
 post.inforande='infort';post.effekt='oforandrat';post.inforanden=[{version:'a'.repeat(40),gren:'main',tid:1791429000,omfattning:'lokal Git-version, inte verifierad drift',granskning:'syntetisk-granskning'}];
 post.uppfoljning=[{utfall:'oforandrat',observator:'Provobservatör',tid:1791429000,omfattning:'Ett syntetiskt prov',bevis:'<img src=x onerror=alert(1)>',version:'a'.repeat(40)}];
 await page.route('**/api/kirurg/forbattringar',r=>r.fulfill({json:visa}));
 await box.getByRole('button',{name:'Läs aktuellt tillstånd',exact:true}).click();
 await box.locator('details[data-kf-post] > summary').click();
 await box.getByText('Införande: Verifierat i lokal Git-version.',{exact:false}).waitFor();
 assert.match(await box.innerText(),/inte verifierad drift/);assert.match(await box.innerText(),/Inrapporterad observation/);
 assert.equal(await box.locator('img').count(),0,'inrapporterat belägg ska visas som text');
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1000});
  const spill=await page.evaluate(()=>({ok:document.documentElement.scrollWidth<=innerWidth,
    element:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tagg:e.tagName,id:e.id,bredd:e.getBoundingClientRect().width,text:e.textContent.slice(0,80)})).slice(-20)}));
  assert(spill.ok,'spill '+width+' '+JSON.stringify(spill.element));
  await page.evaluate(()=>scrollTo(0,0));
  if(process.env.NWP_UI_BEVISET&&[390,1440].includes(width))await page.screenshot({path:process.env.NWP_UI_BEVISET.replace(/\.png$/,`-${width}.png`),fullPage:true});
 }
 await page.addScriptTag({content:await readFile(resolve(root,'kontroller/node_modules/axe-core/axe.min.js'),'utf8')});
 const axe=await page.evaluate(async()=>await axe.run(document.getElementById('kirurg-forbattring')));
 assert.deepEqual(axe.violations.map(v=>({id:v.id,n:v.nodes.length})),[]);
 assert.deepEqual(errors,[]);console.log('Kirurgens ägaryta: observation, diagnos, utkast, disposition, paus, stickprov, fyra bredder, tangentbord och axe OK');
}finally{
 if(browser)await browser.close();child.kill('SIGTERM');
 await new Promise((res,rej)=>{if(child.exitCode!==null)return res();child.once('exit',res);setTimeout(()=>{if(child.exitCode===null){child.kill('SIGKILL');rej(Error('provservern behövde hårdstopp'));}},5000).unref();});
}
