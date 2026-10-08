// Ägarens faktiska dashboard och Kundstart-API i provrot; ingen modell eller drift.
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const root=resolve(process.argv[2]||'.');
const child=spawn(resolve(root,'.venv/bin/python'),['-B','kontroller/rokprov/revision/prov_kundstart_agare.py','--provserver'],{cwd:root,stdio:['ignore','pipe','pipe']});
let browser,stderr='';child.stderr.on('data',b=>stderr+=b);
try{
 const init=await new Promise((res,rej)=>{let s='';const timer=setTimeout(()=>rej(Error('Provservern startade inte')),10000);child.on('exit',()=>{clearTimeout(timer);rej(Error(stderr));});child.stdout.on('data',b=>{s+=b;if(s.includes('\n')){clearTimeout(timer);try{res(JSON.parse(s.split('\n')[0]));}catch(e){rej(e);}}});});
 const origin=`http://127.0.0.1:${init.port}`;
 browser=await chromium.launch({headless:true});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
 await page.goto(origin+'/#/kundstart');await page.getByRole('heading',{name:'Kundstart',exact:true}).waitFor();
 await page.getByText('Skapa ett privat ärende',{exact:true}).click();
 await page.getByLabel('Projektets slug',{exact:true}).fill('prov-agaryta');
 await page.getByLabel('Första beslutsfattarens namn',{exact:true}).fill('Syntetisk beslutsfattare');
 const b=page.getByRole('button',{name:'Skapa ärendet',exact:true});await b.focus();await page.keyboard.press('Enter');
 await page.getByRole('status').filter({hasText:'Ärendet finns'}).waitFor();
 const link=await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).inputValue();assert(link.includes('#arende=')&&link.includes('&nyckel='));
 await page.getByRole('link',{name:'Öppna ärendet',exact:true}).click();
 await page.getByRole('heading',{name:'prov-agaryta',exact:true}).waitFor();
 assert(await page.getByRole('button',{name:'Lämna aktuellt underlag till förberedelsen',exact:true}).isDisabled());
 assert(!(await page.locator('#vy').innerText()).includes(link));
 for(const width of [320,390,768,1440]){
  await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'spill '+width);
  await page.evaluate(()=>scrollTo(0,0));
  if(process.env.NWP_UI_BEVISET&&[390,1440].includes(width))await page.screenshot({path:process.env.NWP_UI_BEVISET.replace(/\.png$/,`-agare-${width}.png`),fullPage:true});
 }
 if(!await page.getByLabel('Deltagarens namn',{exact:true}).isVisible())await page.getByText('Deltagare och personlig åtkomst',{exact:true}).click();
 await page.getByLabel('Deltagarens namn',{exact:true}).fill('Syntetisk medverkande');
 await page.getByRole('button',{name:'Skapa personlig åtkomst',exact:true}).click();
 await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).waitFor();
 assert.notEqual(await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).inputValue(),link);
 // AG2: en ny inbjudan måste använda den nu bekräftade revisionen.
 if(!await page.getByLabel('Deltagarens namn',{exact:true}).isVisible())await page.getByText('Deltagare och personlig åtkomst',{exact:true}).click();
 await page.getByLabel('Deltagarens namn',{exact:true}).fill('Andra provdeltagaren');
 await page.getByRole('button',{name:'Skapa personlig åtkomst',exact:true}).click();
 await page.getByText('Andra provdeltagaren · medverkande · aktiv',{exact:false}).waitFor({timeout:6000,state:'attached'});
 // AG2: nytt ärende i samma formulär är en ny avsikt, samma omförsök är inte det.
 await page.goto(origin+'/#/kundstart');await page.getByText('Skapa ett privat ärende',{exact:true}).click();
 for(const slug of ['prov-agare-b','prov-agare-c']){
   await page.getByLabel('Projektets slug',{exact:true}).fill(slug);
   await page.getByLabel('Första beslutsfattarens namn',{exact:true}).fill('Provroll');
   const fore=await page.locator('#ks-lank').count()?await page.locator('#ks-lank').inputValue():'';
   await page.getByRole('button',{name:'Skapa ärendet',exact:true}).click();
   await page.waitForFunction(old=>document.getElementById('ks-lank')?.value&&document.getElementById('ks-lank').value!==old,fore);
   await page.getByRole('status').filter({hasText:'Ärendet finns'}).waitFor();
   const eid=new URLSearchParams((await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).inputValue()).split('#')[1]).get('arende');
   const d=await page.request.get(origin+'/api/kundstart/'+eid);assert.equal((await d.json()).arende.slug,slug);
 }
 // AG2 omprov: A:s mottagna svar försvinner, B skapas, sidan laddas om,
 // och A ska fortfarande ha sitt ursprungliga operations-id utan ny rånyckel.
 const starter=[];let tappa=true;
 const tappaStart=async route=>{const data=route.request().postDataJSON();starter.push(data);
   if(data.slug==='prov-journal-a'&&tappa){tappa=false;await route.fetch();return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({fel:'Syntetiskt tappat startsvar'})});}
   return route.continue();};
 await page.route('**/api/kundstart',tappaStart);
 for(const slug of ['prov-journal-a','prov-journal-b']){
   await page.getByLabel('Projektets slug',{exact:true}).fill(slug);
   await page.getByRole('button',{name:'Skapa ärendet',exact:true}).click();
   if(slug.endsWith('-a'))await page.getByRole('status').filter({hasText:'Syntetiskt tappat'}).waitFor();
   else await page.waitForFunction(()=>document.getElementById('ks-status').textContent.startsWith('Ärendet finns'));
 }
 await page.unroute('**/api/kundstart',tappaStart);await page.reload();
 await page.getByText('Skapa ett privat ärende',{exact:true}).click();
 await page.route('**/api/kundstart',tappaStart);
 await page.getByLabel('Projektets slug',{exact:true}).fill('prov-journal-a');
 await page.getByRole('button',{name:'Skapa ärendet',exact:true}).click();
 await page.getByText('Ärendet skapades redan. Nyckeln sparas inte; skapa en ny personlig länk om första svaret försvann.',{exact:true}).waitFor();
 assert.equal(starter.filter(x=>x.slug==='prov-journal-a')[0].operation,starter.at(-1).operation);
 assert.equal(await page.locator('#ks-lank').count(),0);
 await page.unroute('**/api/kundstart',tappaStart);
 const rows=(await (await page.request.get(origin+'/api/kundstart')).json()).arenden;
 const A=rows.find(x=>x.slug==='prov-agaryta').id,B=rows.find(x=>x.slug==='prov-agare-b').id;
 const visa=async(id,slug)=>{await page.goto(origin+'/#/kundstart/'+id);await page.getByRole('heading',{name:slug,exact:true}).waitFor();};
 // AG3: ett äldre GET-svar får inte ersätta en senare vald vy.
 let slapp,kom;const vant=new Promise(r=>kom=r);const sparr=new Promise(r=>slapp=r);
 const hall=async route=>{const result=await route.fetch();kom();await sparr;await route.fulfill({response:result});};
 await page.route('**/api/kundstart/'+A,hall);
 await page.goto(origin+'/#/kundstart/'+A);await vant;
 await visa(B,'prov-agare-b');slapp();await page.unroute('**/api/kundstart/'+A,hall);
 await page.waitForFunction(()=>document.querySelector('#vy h1')?.textContent==='prov-agare-b');
 await page.waitForTimeout(150);assert.equal(await page.locator('#vy h1').innerText(),'prov-agare-b');
 // AG3: ett sent inbjudningssvar kan inte visa A:s åtkomst under B:s rubrik.
 await visa(A,'prov-agaryta');if(!await page.getByLabel('Deltagarens namn',{exact:true}).isVisible())await page.getByText('Deltagare och personlig åtkomst',{exact:true}).click();
 await page.getByLabel('Deltagarens namn',{exact:true}).fill('Sen provdeltagare');
 let slappPost,komPost;const vantPost=new Promise(r=>komPost=r),sparrPost=new Promise(r=>slappPost=r);
 const hallPost=async route=>{const result=await route.fetch();komPost();await sparrPost;await route.fulfill({response:result});};
 await page.route('**/api/kundstart/'+A+'/deltagare',hallPost);
 await page.getByRole('button',{name:'Skapa personlig åtkomst',exact:true}).click();await vantPost;
 await visa(B,'prov-agare-b');slappPost();await page.unroute('**/api/kundstart/'+A+'/deltagare',hallPost);
 await page.waitForTimeout(150);assert.equal(await page.locator('#vy h1').innerText(),'prov-agare-b');
 assert.equal(await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).count(),0);
 // Utkast i andra formulär finns kvar efter en lyckad handling och omladdning.
 await page.getByText('Ge ett definierat erbjudande',{exact:true}).click();
 await page.getByLabel('Omfattningen som erbjuds',{exact:true}).fill('Syntetiskt osparat utkast');
 if(!await page.getByLabel('Deltagarens namn',{exact:true}).isVisible())await page.getByText('Deltagare och personlig åtkomst',{exact:true}).click();
 await page.getByLabel('Deltagarens namn',{exact:true}).fill('Ytterligare provroll');
 await page.getByRole('button',{name:'Skapa personlig åtkomst',exact:true}).click();
 await page.getByLabel('Lokal personlig ärendelänk',{exact:true}).waitFor();
 await page.reload();await page.getByRole('heading',{name:'prov-agare-b',exact:true}).waitFor();
 await page.getByText('Ge ett definierat erbjudande',{exact:true}).click();
 assert.equal(await page.getByLabel('Omfattningen som erbjuds',{exact:true}).inputValue(),'Syntetiskt osparat utkast');
 assert(await page.getByRole('button',{name:'Lämna erbjudandet för kundens acceptans',exact:true}).isDisabled());
 await page.getByRole('button',{name:'Jag har jämfört detta utkast med den aktuella revisionen',exact:true}).click();
 assert(!(await page.getByRole('button',{name:'Lämna erbjudandet för kundens acceptans',exact:true}).isDisabled()));
 // Endast vår nya yta kontrolleras: gamla dashboardvyer har egna befintliga prov.
 await page.addScriptTag({content:await readFile(resolve(root,'kontroller/node_modules/axe-core/axe.min.js'),'utf8')});
 const axe=await page.evaluate(()=>window.axe.run(document.querySelector('#vy'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}}));
 assert.deepEqual(axe.violations.map(v=>({id:v.id,n:v.nodes.map(x=>x.target)})),[]);assert.deepEqual(errors,[]);
 console.log(JSON.stringify({api:'riktig ägarserver i provrot',bredder:[320,390,768,1440],tangentbord:true,axe_fynd:0,ingen_ai:true}));
}finally{await browser?.close();child.kill('SIGTERM');if(child.exitCode===null){const timer=setTimeout(()=>child.kill('SIGKILL'),3000);try{await once(child,'exit');}finally{clearTimeout(timer);}}}
