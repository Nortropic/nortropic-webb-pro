// Ändringsflikens webbläsarprov (kunskap/andringar.md, Proven), kört av prov_andringar_webb.py mot den riktiga
// dashboardservern i en isolerad rot. Med provagenten (verkligt=0): xterm i portalen, svenska tecken, inklistring,
// storlek, Ctrl+C, omladdning med samma utdata, en andra vy som tar över, bilagor, stopp utan kvarvarande skal, axe och
// spill. Med en riktig Claude Code-session (verkligt=1, manuellt): förtroendet, ett text- och öppettidsuppdrag, en
// följdfråga i samma sammanhang och en bild, och att arbetskopian faktiskt ändrats.
import { resolve } from 'node:path';
import { writeFileSync, mkdirSync } from 'node:fs';
import assert from 'node:assert/strict';
const [url, nyckel, slug, slug2, verkligt, bevis, rot] = process.argv.slice(2);
const root = resolve('.');
const { chromium } = await import(resolve(root, 'kontroller/node_modules/playwright/index.mjs'));
const sov = (ms) => new Promise((r) => setTimeout(r, ms));
const sammanfattning = { verkligt: verkligt === '1' };
const browser = await chromium.launch({ headless: true });
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  // som Nortropic.app (freezePrototype i tauri.conf.json): en tilldelning som skuggar en prototypegenskap kastar då
  await ctx.addInitScript(() => Object.freeze(Object.prototype));
  const page = await ctx.newPage();
  const sidfel = []; page.on('pageerror', (e) => sidfel.push(e.message));
  const origin = new URL(url).origin;
  await page.route((u) => u.origin !== origin && !u.hostname.startsWith('127.0.0.1'), (r) => r.abort());
  // terminalens text ur xterm:s buffert; en rad som terminalen brutit (isWrapped) fogas till raden före
  const text = (p = page) => p.evaluate(() => { const t = window.__andringar?.term; if (!t) return ''; const b = t.buffer.active, ut = [];
    for (let i = 0; i < b.length; i++) { const l = b.getLine(i); if (!l) continue; const s = l.translateToString(true);
      if (l.isWrapped && ut.length) ut[ut.length - 1] += s; else ut.push(s); } return ut.join('\n'); });
  const vantaText = async (s, ms = 15000, p = page) => { const slut = Date.now() + ms; while (Date.now() < slut) { if ((await text(p)).includes(s)) return true; await sov(150); } throw new Error(`terminalen visade aldrig "${s}"; sista raderna:\n${(await text(p)).split('\n').filter(Boolean).slice(-12).join('\n')}`); };
  const bild = async (namn) => { if (bevis) { mkdirSync(bevis, { recursive: true }); await page.screenshot({ path: `${bevis}/andringar-${namn}.png`, fullPage: true }); } };

  await page.goto(`${url}/#nyckel=${nyckel}&till=andringar/${slug}`);
  await page.locator('#an-rubrik').waitFor();
  await page.locator('[data-an-starta]').waitFor();
  assert.equal(await page.evaluate(() => location.hash), `#/andringar/${slug}`);
  assert.equal((await page.locator('.pt-stegrad a[aria-current="step"]').textContent()).replace(/^\d+/, '').trim(), 'Ändringar', 'stegraden står på Ändringar');
  assert.match(await page.locator('#an-lage').textContent(), new RegExp(`Repo kund-${slug}`));
  assert.match(await page.locator('#an-lage').textContent(), /Gren main/);
  await page.locator('[data-an-starta]').click();

  if (verkligt !== '1') {
    await vantaText('redo.');
    const info = JSON.parse((await text()).split('fejkclaude:')[1].split('\n')[0]);
    assert(info.argv.includes('--restricted') && info.tty && info.styrande, 'agenten startad av motorn i en riktig terminal');
    sammanfattning.start = true;
    // svenska tecken med tangentbordet
    await page.locator('#an-xterm').click();
    await page.keyboard.type('byt öppettiderna till 07–16, åäö ÅÄÖ');
    await page.keyboard.press('Enter');
    await vantaText('fick: byt öppettiderna till 07–16, åäö ÅÄÖ');
    // inklistring med flera rader (xterm gör om radbrytningen till Enter)
    await page.evaluate(() => window.__andringar.term.paste('rad ett\nrad två'));
    await page.keyboard.press('Enter');
    await vantaText('fick: rad två');
    assert((await text()).includes('fick: rad ett'), 'den första inklistrade raden');
    // storleken följer vyn
    await page.setViewportSize({ width: 1100, height: 760 });
    await sov(1200);  // fit och den fördröjda storleken till agenten
    const { cols, rows } = await page.evaluate(() => ({ cols: window.__andringar.term.cols, rows: window.__andringar.term.rows }));
    await vantaText(`storlek: ${cols}x${rows}`);
    await page.setViewportSize({ width: 1440, height: 900 });
    // Ctrl+C är avbrottet, som en signal till agenten
    await page.locator('#an-xterm').click();
    await page.keyboard.press('Control+C');
    await vantaText('avbrott mottaget');
    sammanfattning.terminal = { svenska: true, inklistring: true, storlek: `${cols}x${rows}`, avbrott: true };
    await bild('terminal-1440');
    // omladdning: samma process, samma utdata, och fliken skriver vidare (samma klient-id i fliken)
    const pid = (await page.evaluate(() => window.__andringar.lage.session.pid));
    await page.reload();
    await page.locator('#an-rubrik').waitFor();
    await vantaText('fick: rad två');
    assert.equal(await page.evaluate(() => window.__andringar.lage.session.pid), pid, 'samma agentprocess efter omladdningen');
    await page.locator('#an-xterm').click();
    await page.keyboard.type('efter omladdning'); await page.keyboard.press('Enter');
    await vantaText('fick: efter omladdning');
    // en andra vy: ser utdata, skriver först efter att ha tagit över; den första får då vänta
    const p2 = await ctx.newPage();
    p2.on('pageerror', (e) => sidfel.push('andra vyn: ' + e.message));
    await p2.goto(`${url}/#/andringar/${slug}`);
    await p2.locator('[data-an-ta-over]').waitFor();
    await vantaText('fick: efter omladdning', 15000, p2);
    await p2.locator('#an-xterm').click();
    await p2.keyboard.type('x');
    await p2.locator('#an-notis').filter({ hasText: 'En annan vy skriver' }).waitFor();
    await p2.locator('[data-an-ta-over]').click();
    await p2.locator('#an-xterm').click();
    await p2.keyboard.type('från andra vyn'); await p2.keyboard.press('Enter');
    await vantaText('fick: från andra vyn', 15000, p2);
    await page.locator('#an-xterm').click();
    await page.keyboard.type('y');
    await page.locator('#an-notis').filter({ hasText: 'En annan vy skriver' }).waitFor();
    await p2.close();
    await page.locator('[data-an-ta-over]').click();
    sammanfattning.vyer = { samma_process_efter_omladdning: true, andra_vyn_tar_over: true };
    // bilagor: en bild bifogas privat, och sökvägen skrivs i terminalen på begäran
    await page.locator('[data-an-flik="bilagor"]').click();
    const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=', 'base64');
    await page.locator('#an-fil').setInputFiles({ name: 'ny huvudbild.png', mimeType: 'image/png', buffer: png });
    await page.locator('#an-notis').filter({ hasText: 'är bifogad' }).waitFor();
    await page.locator('[data-an-infoga="0"]').click();
    await page.locator('#an-xterm').click(); await page.keyboard.press('Enter');
    await vantaText('ny-huvudbild.png');
    assert.match(await text(), /andringar\/bilagor\/\d{8}-\d{6}-ny-huvudbild\.png/);
    // sidopanelen: ändringar och historik ur arbetskopian
    await page.locator('[data-an-flik="historik"]').click();
    await page.locator('#an-panel').getByText('Export 000000000001-prov').waitFor();
    await page.locator('[data-an-flik="andringar"]').click();
    await page.locator('#an-panel').getByText('Ej committat i arbetskopian').waitFor();
    // axe och spill (xterm:s egen yta prövas av komponentens projekt; här vyn runt den)
    await page.addScriptTag({ path: resolve(root, 'kontroller/node_modules/axe-core/axe.min.js') });
    const fynd = await page.evaluate(async () => (await axe.run(document.querySelector('#vy'), { exclude: [['.xterm']], runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa'] } }))
      .violations.map((v) => `${v.id}: ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`));
    assert.deepEqual(fynd, [], 'axe i ändringsfliken');
    for (const w of [390, 1440]) {
      await page.setViewportSize({ width: w, height: 900 }); await sov(300);
      // terminalen anpassar sig efter den nya bredden (ResizeObserver och fit): högst två sekunder för layouten att sätta
      // sig; vid spill därefter står elementen som går utanför i felet
      for (let i = 0; i < 20 && !(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); i++) await sov(100);
      const spill = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth ? [] : [...document.querySelectorAll('body *')]
        .filter((e) => e.getBoundingClientRect().right > innerWidth + 1)
        .slice(0, 8).map((e) => `${e.tagName.toLowerCase()}${e.id ? '#' + e.id : ''}${[...e.classList].map((c) => '.' + c).join('')} ${Math.round(e.getBoundingClientRect().right)}`));
      assert.deepEqual(spill, [], `sidledes spill vid ${w} px`);
      await bild(`vy-${w}`);
    }
    await page.setViewportSize({ width: 1440, height: 900 });
    // stoppet: processkontroll, och efteråt finns inget skal att skriva i
    await page.locator('[data-an-stoppa]').click();
    await page.locator('[data-an-stoppa-ja]').click();
    await vantaText('[agenten har avslutats]');
    await page.locator('[data-an-starta]').waitFor();
    await page.locator('[data-an-ateruppta]').waitFor();
    await page.locator('#an-xterm').click(); await page.keyboard.type('ls'); await page.keyboard.press('Enter'); await sov(500);
    assert(!(await text()).includes('fick: ls'), 'inget tar emot inmatning efter agentens slut');
    sammanfattning.stopp = { processkontroll: true, inget_skal_efter: true };
    // en annan webbplats: egen vy, ingen session från den första
    await page.goto(`${url}/#/andringar/${slug2}`);
    await page.locator('[data-an-starta]').waitFor();
    assert.equal(await page.evaluate(() => window.__andringar.lage.session.lever), false, 'den andra webbplatsen har ingen levande agent');
  } else {
    // en riktig Claude Code-session: förtroendet för arbetskopian (en gång per sökväg), sedan uppdragen
    const slut = Date.now() + 90000;
    while (Date.now() < slut && !/trust this folder|❯\s*$/m.test(await text())) await sov(500);
    if ((await text()).includes('trust this folder')) { await page.locator('#an-xterm').click(); await sov(1200); await page.keyboard.press('ArrowDown'); await sov(600); await page.keyboard.press('Enter'); }
    await sov(4000);
    // Claude Codes behörighetsfrågor besvaras som Johnny skulle: ett skalkommando eller en filändring godkänns, allt
    // annat (till exempel en webbhämtning) avböjs; varje fråga räknas och står i sammanfattningen
    const fragor = [];
    const svaraPaFraga = async () => {
      const sista = (await text()).split('\n').filter((r) => r.trim()).slice(-18).join('\n');
      if (!/Do you want to /.test(sista) || !/❯\s*1\.\s*Yes/.test(sista)) return;
      const godkann = /Bash command|Edit file|Create file|Write file/.test(sista);
      fragor.push({ godkand: godkann, text: sista.split('\n').filter((r) => /Do you want|Bash\(|Fetch|command|file/i.test(r)).slice(-4).join(' | ').slice(0, 400) });
      await page.locator('#an-xterm').click();
      await page.keyboard.press(godkann ? 'Enter' : 'Escape');
      await sov(2500);
    };
    const uppdrag = async (s, klar, ms = 900000) => {
      await page.locator('#an-xterm').click();
      await page.keyboard.type(s); await sov(400); await page.keyboard.press('Enter');
      const slut2 = Date.now() + ms;
      while (Date.now() < slut2) { if ((await text()).includes(klar)) return; await svaraPaFraga(); await sov(2000); }
      throw new Error('uppdraget blev inte klart: ' + s);
    };
    const vantaKlar = async (klar, ms = 900000) => {
      const slut2 = Date.now() + ms;
      while (Date.now() < slut2) { if ((await text()).includes(klar)) return; await svaraPaFraga(); await sov(2000); }
      throw new Error('uppdraget blev inte klart: ' + klar);
    };
    // uppdrag 1, text och bild (acceptansprov 3): bilden bifogas i fliken och sökvägen infogas i terminalen
    const duk = await page.evaluate(() => { const c = document.createElement('canvas'); c.width = 1600; c.height = 900; const g = c.getContext('2d');
      const f = g.createLinearGradient(0, 0, 1600, 900); f.addColorStop(0, '#2f5d50'); f.addColorStop(1, '#c9b48a'); g.fillStyle = f; g.fillRect(0, 0, 1600, 900);
      g.fillStyle = '#7a5230'; g.fillRect(200, 560, 1200, 60); for (let x = 220; x < 1400; x += 120) g.fillRect(x, 620, 24, 200); return c.toDataURL('image/png').split(',')[1]; });
    await page.locator('[data-an-flik="bilagor"]').click();
    await page.locator('#an-fil').setInputFiles({ name: 'altan.png', mimeType: 'image/png', buffer: Buffer.from(duk, 'base64') });
    await page.locator('#an-notis').filter({ hasText: 'är bifogad' }).waitFor();
    await page.locator('#an-xterm').click();
    // markören står inte i uppdragets text (terminalen visar inmatningen också): RAPPORT, bindestreck och siffran
    await page.keyboard.type('Kunden vill ändra öppettiderna på startsidan till vardagar 07–16, lägga till att de även bygger altaner och ha bilden jag bifogar som huvudbild överst på startsidan, med en alternativtext efter bildens funktion. Behåll övrig design. Gör ändringen, kör provvägen, committa och avsluta med en rad som är ordet RAPPORT, ett bindestreck och siffran 1. Bilden: ');
    await page.locator('[data-an-infoga="0"]').click();
    await sov(800);
    await page.locator('#an-xterm').click(); await page.keyboard.press('Enter');
    await vantaKlar('RAPPORT-1');
    await bild('verkligt-1');
    // en följdfråga i samma sammanhang (acceptansprov 2)
    await uppdrag('Bra, men beskär bilden så att den inte blir högre än 360 px i mobilen, och kontrollera det i 390 px. Avsluta med en rad som är ordet RAPPORT, ett bindestreck och siffran 2.', 'RAPPORT-2');
    await bild('verkligt-2');
    await page.locator('[data-an-stoppa]').click();
    await page.locator('[data-an-stoppa-ja]').click();
    await vantaText('[agenten har avslutats]', 60000);
    // acceptansprov 7 och 8: en annan dator flyttar öppettiderna till en komponent; en helt ny session (Starta, inte
    // Återuppta) ska hitta den nya källan genom sin kunskap och arbetskopian, inte följa det gamla minnet
    const { execFileSync } = await import('node:child_process');
    const { readFileSync: las, writeFileSync: skriv } = await import('node:fs');
    const repo = resolve(rot, 'kunder', slug, 'kundrepo'), sida = resolve(repo, 'src/pages/index.astro');
    const text0 = las(sida, 'utf-8'), rad = text0.split('\n').find((r) => r.includes('07–16'));
    if (!rad) throw new Error('startsidan har ingen rad med 07–16 att flytta');
    mkdirSync(resolve(repo, 'src/components'), { recursive: true });
    skriv(resolve(repo, 'src/components/Oppettider.astro'), `---\n// öppettiderna på ett ställe (flyttade hit 2026-10-11)\n---\n${rad.trim()}\n`);
    skriv(sida, text0.replace(rad, '    <Oppettider />').replace(/^---\n/, "---\nimport Oppettider from '../components/Oppettider.astro';\n"));
    const git = (...a) => execFileSync('git', ['-c', 'user.name=Annan dator', '-c', 'user.email=annan@exempel.se', '-c', 'core.hooksPath=/dev/null', ...a], { cwd: repo, encoding: 'utf-8' });
    git('add', 'src/components/Oppettider.astro', 'src/pages/index.astro');
    git('commit', '-q', '-m', 'Struktur: öppettiderna i en egen komponent');
    sammanfattning.extern_struktur = git('rev-parse', '--short', 'HEAD').trim();
    await page.reload();
    await page.locator('[data-an-starta]').waitFor();
    await page.locator('[data-an-starta]').click();
    const slut3 = Date.now() + 90000;
    while (Date.now() < slut3 && !/❯\s*$/m.test(await text())) await sov(500);
    await sov(3000);
    await uppdrag('Kunden vill ha öppettiderna vardagar 08–16 i stället. Gör ändringen, kör provvägen, committa och avsluta med en rad som är ordet RAPPORT, ett bindestreck och siffran 3.', 'RAPPORT-3');
    await bild('verkligt-3');
    sammanfattning.verkliga_uppdrag = 3;
    sammanfattning.behorighetsfragor = fragor;
    await page.locator('[data-an-stoppa]').click();
    await page.locator('[data-an-stoppa-ja]').click();
    await vantaText('[agenten har avslutats]', 60000);
  }
  assert.deepEqual(sidfel, [], 'inga sidfel');
  sammanfattning.sidfel = 0;
  console.log(JSON.stringify(sammanfattning));
} finally {
  await browser.close();
}
