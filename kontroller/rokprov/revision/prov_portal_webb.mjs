// Portalens vyer (dashboard/portal.js; kunskap/desktop.md, Portalen) i Chromium mot motorns riktiga hanterare i en provrot
// (prov_desktop.py --provserver): Hem utan riktiga kunder och med en ny testkund, Ny testkund med fel nära fälten och tangentbordet, kundlistan
// med urval, intervjun med ett sparat svar, Förfiningens kommentarer samlade till ett uppdrag, bredderna 320–1440 utan spill och axe (WCAG 2.2 AA) i varje vy. Ingen modell,
// ingen app: appens WKWebView prövas av desktop/prov/prov_app.py.
import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const root = resolve(process.argv[2] || '.');
const child = spawn(resolve(root, '.venv/bin/python'), ['-B', 'kontroller/rokprov/revision/prov_desktop.py', '--provserver'], {cwd: root, stdio: ['ignore', 'pipe', 'pipe']});
let browser, stderr = ''; child.stderr.on('data', (b) => { stderr += b; });
const axeKod = await readFile(resolve(root, 'kontroller/node_modules/axe-core/axe.min.js'), 'utf8');
try {
  const init = await new Promise((res, rej) => { let s = ''; const t = setTimeout(() => rej(Error('provservern startade inte: ' + stderr)), 15000);
    child.on('exit', () => { clearTimeout(t); rej(Error(stderr)); });
    child.stdout.on('data', (b) => { s += b; const i = s.indexOf('\n'); if (i >= 0) { clearTimeout(t); res(JSON.parse(s.slice(0, i))); } }); });
  const origin = `http://127.0.0.1:${init.port}`;
  browser = await chromium.launch({headless: true});
  const page = await browser.newPage();
  const fel = []; page.on('pageerror', (e) => fel.push(e.message)); page.on('console', (m) => { if (m.type() === 'error') fel.push(m.text()); });
  await page.route('**/*', (r) => new URL(r.request().url()).origin === origin ? r.continue() : r.abort());
  const granska = async (namn) => {
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({width, height: 900});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `spill i ${namn} vid ${width}`);
    }
    await page.setViewportSize({width: 1440, height: 900});
    await page.addScriptTag({content: axeKod});
    const r = await page.evaluate(() => window.axe.run(document.body, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}}));
    assert.deepEqual(r.violations.map((v) => ({id: v.id, n: v.nodes.map((x) => x.target)})), [], 'axe i ' + namn);
  };
  // Hem, tomt läge
  await page.goto(origin + '/#/start');
  await page.getByRole('heading', {name: 'Välkommen', exact: true}).waitFor();
  for (const t of ['Ny kund', 'Kunder 0', 'Testkunder 1', 'Fortsätt där du slutade', 'Behöver din uppmärksamhet', 'Inget hos riktiga kunder väntar']) assert((await page.locator('#vy').innerText()).includes(t), t);
  assert.equal(await page.locator('#pt-nav a[aria-current="page"]').innerText(), 'Hem');
  await granska('Hem (inga riktiga kunder)');
  // Ny testkund: felet står vid fältet och fokus flyttas dit; tangentbordet räcker
  await page.goto(origin + '/#/ny-testkund');
  await page.getByRole('heading', {name: 'Skapa testkund', exact: true}).waitFor();
  await page.getByRole('button', {name: 'Starta kundintervjun', exact: true}).click();
  await page.getByText('Skriv företagets namn eller ett arbetsnamn.', {exact: true}).waitFor();
  assert.equal(await page.evaluate(() => document.activeElement.id), 'pt-foretag', 'fokus till fältet med felet');
  await page.getByLabel('Befintlig webbplats').fill('inte en adress');
  await page.getByLabel('Företagets namn eller arbetsnamn').fill('Provcykel Umeå (test)');
  await page.getByRole('button', {name: 'Starta kundintervjun', exact: true}).click();
  await page.getByText(/Skriv hela adressen/).waitFor();
  await page.getByLabel('Befintlig webbplats').fill('https://exempel.se');
  await page.getByLabel('Vad vill kunden ha hjälp med?').fill('Fler bokningar av service.');
  await granska('Ny testkund');
  await page.getByRole('button', {name: 'Starta kundintervjun', exact: true}).focus();
  await page.keyboard.press('Enter');
  await page.waitForURL(/#\/intervju\/[a-f0-9]{32}$/);
  await page.getByRole('heading', {name: /Kundintervju · Provcykel Umeå \(test\)/}).waitFor();
  assert((await page.locator('#vy').innerText()).includes('Dina anteckningar'));
  // intervjun: spara ett svar utan AI; svaret står som kundens ord, antecknat av dig
  await page.getByLabel(/Kundens svar/).fill('Vi lagar cyklar och säljer begagnade.');
  await page.getByRole('button', {name: 'Spara svaret', exact: true}).click();
  await page.getByText('Kundens svar, antecknat av dig').waitFor();
  assert((await page.locator('.pt-stegrad li.aktiv').innerText()).includes('Kundstart'), 'stegraden visar Kundstart');
  await granska('Intervjun');
  // Kunder och Testkunder: testkunden står bara bland testkunderna
  await page.goto(origin + '/#/kunder');
  await page.getByRole('heading', {name: 'Kunder', exact: true}).waitFor();
  assert((await page.locator('#pt-antal').innerText()).startsWith('0 av 0'));
  await page.goto(origin + '/#/testkunder');
  await page.getByRole('heading', {name: 'Testkunder', exact: true}).waitFor();
  assert((await page.locator('#pt-lista').innerText()).includes('Provcykel Umeå (test)'));
  await page.getByRole('button', {name: 'Påbörjade intervjuer', exact: true}).click();
  assert.equal(await page.getByRole('button', {name: 'Påbörjade intervjuer', exact: true}).getAttribute('aria-pressed'), 'true');
  await granska('Testkunder');
  // Förfining: en kommentar på en punkt och en på hela sidan, samlade till ett uppdrag genom arbetsytans ändringsväg
  await page.goto(origin + '/#/granska/testdata-kommentarer');
  await page.getByRole('heading', {name: /Förfining/}).waitFor();
  await page.getByRole('button', {name: 'Kommentera en punkt', exact: true}).click();
  const bild = page.locator('#pk-bild'); await bild.waitFor();
  const r = await bild.boundingBox();
  await bild.click({position: {x: r.width * 0.25, y: r.height * 0.5}});
  await page.getByLabel('Kommentar på punkten').fill('Rubriken behöver mer luft.');
  await page.getByRole('button', {name: 'Spara kommentaren', exact: true}).click();
  await page.locator('.pt-nal[data-hopp]').first().waitFor();
  await page.getByRole('button', {name: 'Kommentera hela sidan', exact: true}).click();
  await page.getByLabel('Kommentar på hela sidan').fill('Kontaktvägen syns för sent.');
  await page.getByRole('button', {name: 'Spara kommentaren', exact: true}).click();
  await page.getByText('Kontaktvägen syns för sent.').waitFor();
  assert.equal(await page.locator('.pt-kommentar').count(), 2);
  for (const c of await page.locator('[data-valj-k]').all()) await c.check();
  await page.getByRole('button', {name: 'Gör ett uppdrag av de valda', exact: true}).click();
  assert((await page.getByLabel('Omfattning (en rad per punkt)').inputValue()).includes('Rubriken behöver mer luft.'));
  await page.getByLabel('Det som ska bevaras').fill('Allt annat i layouten och texterna.');
  await granska('Förfining');
  await page.getByRole('button', {name: 'Spara uppdraget', exact: true}).click();
  await page.waitForFunction(() => document.querySelectorAll('.pt-kommentar[data-status="bestalld"]').length === 2);
  // Hem, fyllt läge
  await page.goto(origin + '/#/start');
  await page.getByRole('heading', {name: 'Välkommen', exact: true}).waitFor();
  assert((await page.locator('#vy').innerText()).includes('Provcykel Umeå (test)'));
  await granska('Hem (fyllt)');
  assert.deepEqual(fel, []);
  console.log(JSON.stringify({api: 'motorns riktiga hanterare i provrot', vyer: ['Hem utan riktiga kunder', 'Ny testkund', 'Intervjun', 'Testkunder', 'Förfining', 'Hem fyllt'], forfining: {kommentarer: 2, bestallda_i_ett_uppdrag: 2}, bredder: [320, 390, 768, 1440], axe_fynd: 0, tangentbord: true, ingen_ai: true}));
} finally {
  await browser?.close();
  child.kill('SIGTERM');
}
