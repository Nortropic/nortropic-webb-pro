#!/usr/bin/env node
// Modellfritt HTML-prov. Inga formulär skickas utan explicit tillåtelse och testmarkering.
import { args, oppna, origin, skriv, nu, lasUndantag, viaTjanst } from './gemensamt.mjs';
import { vakta } from '../slugvakt.mjs';
await viaTjanst('utan-js', process.argv.slice(2));
const a = args(process.argv.slice(2));
vakta(a.ut);
if (!a.adress || !a.ut || (a['formular-far-skickas'] && !a.testmarkering)) {
  console.error('--adress URL --ut DIR [--formular SELECTOR --formular-far-skickas --testmarkering TEXT]');
  process.exit(2);
}
const b = await oppna({ tillat: [origin(a.adress)], mal: a.adress, lasande: !a['formular-far-skickas'],  // skrivande bara med uttrycklig tillåtelse (F36)
  undantag: lasUndantag(a['undantag-fil']), extra: { javaScriptEnabled: false } });
const r = { schema: 1, verktyg: 'utan-js', tid: nu(), javaScriptEnabled: false, sidor: [], fynd: [],
  not: 'HTML, synligt huvudinnehåll och angivna formulär; ingen allmän användbarhetsbedömning. Inskick kräver uttrycklig tillåtelse och testmarkering.' };
try {
  // Sista registrerade route kör först. Förhindra sidoeffekter även från en oväntad navigation.
  await b.ctx.route('**/*', async route => {
    if (!['GET', 'HEAD'].includes(route.request().method()) && !a['formular-far-skickas']) return route.abort();
    return route.fallback();
  });
  const urls = [a.adress, ...(a.sidor ? String(a.sidor).split(';').map(p => new URL(p, a.adress).href) : [])];
  for (const url of [...new Set(urls)]) {
    if (origin(url) !== origin(a.adress)) throw new Error('sida utanför målets ursprung');
    const res = await b.page.goto(url, { waitUntil: 'load', timeout: 30000 });
    const row = { url, status: res?.status() ?? null, formular: [] };
    if (!res?.ok() || !(await b.page.locator('body').innerText()).trim() || !await b.page.locator('h1').first().isVisible()) {
      r.fynd.push({ sida: url, vad: 'sidan saknar fungerande synligt HTML-huvudinnehåll utan JavaScript' });
    }
    const forms = b.page.locator(a.formular || 'form');
    const count = await forms.count();
    if (a.formular && !count) r.fynd.push({ sida: url, vad: 'viktigt formulär saknas utan JavaScript', selector: a.formular });
    for (let i = 0; i < count; i++) {
      // Efter inskick återställs sidan inför nästa formulär.
      await b.page.goto(url, { waitUntil: 'load' });
      const form = b.page.locator(a.formular || 'form').nth(i);
      const submit = form.locator('button[type=submit], button:not([type]), input[type=submit]').first();
      // DOM-egenskaperna följer HTML:s standardmål, base och knappens eventuella överstyrning.
      const effective = await form.evaluate((el, selector) => {
        const button = el.querySelector(selector);
        return { action: button?.hasAttribute('formaction') ? button.formAction : el.action,
          method: button?.hasAttribute('formmethod') ? button.formMethod : el.method };
      }, 'button[type=submit], button:not([type]), input[type=submit]');
      const { action, method } = effective;
      const f = { index: i, method, action, skickat: false, status: 'EJ_MATT' };
      row.formular.push(f);
      const target = action ? new URL(action) : null;
      if (!target || target.origin !== origin(url) || method !== 'post' || !await form.isVisible()
          || !await submit.count() || !await submit.isEnabled() || !await submit.isVisible()) {
        f.status = 'FAIL'; r.fynd.push({ sida: url, formular: i, vad: 'formuläret saknar användbar vanlig form-POST utan JavaScript' });
        continue;
      }
      if (!a['formular-far-skickas']) continue;
      for (const field of await form.locator('input:not([type=hidden]):not([type=submit]):not([type=checkbox]):not([type=radio]), textarea').all()) {
        if (!await field.isVisible() || !await field.isEnabled()) continue;
        // honeypot: fält utanför vyn, utanför tabbordningen eller dolda för hjälpmedel fylls aldrig (omgång tolv, F31); isVisible
        // räcker inte, Playwright räknar ett element utanför vyn som synligt
        if (await field.evaluate(e => e.tabIndex < 0 || e.getAttribute('aria-hidden') === 'true' || (() => { const r = e.getBoundingClientRect(); return r.right <= 0 || r.bottom <= 0 || r.left >= window.innerWidth; })())) continue;
        const type = (await field.getAttribute('type') || 'text').toLowerCase();
        if (!['text', 'email', 'tel', 'search', 'url'].includes(type)) continue;
        // telefonfältet har pattern (byggstandarden 6.2): ett giltigt provnummer, annars stoppar webbläsarens validering inskicket
        await field.fill(type === 'email' ? 'test@example.invalid' : type === 'url' ? 'https://example.invalid' : type === 'tel' ? '070-123 45 67' : String(a.testmarkering));
      }
      const fallor = await form.evaluate(f => [...f.querySelectorAll('input,textarea')].filter(e => e.tabIndex < 0 || e.getAttribute('aria-hidden') === 'true').map(e => ({ namn: e.name, tom: !e.value })));
      if (fallor.some(x => !x.tom)) { f.status = 'FAIL'; r.fynd.push({ sida: url, formular: i, vad: 'ett honeypot-fält är ifyllt före inskick; provet avbryts' }); continue; }
      const response = b.page.waitForResponse(x => x.request().method() === 'POST' && x.url() === target.href, { timeout: 10000 });
      const [outcome] = await Promise.all([response.catch(() => null), submit.click({ timeout: 5000 }).catch(() => null)]);
      f.skickat = !!outcome; f.http_status = outcome?.status() ?? null;
      await b.page.waitForLoadState('load', { timeout: 10000 }).catch(() => {});
      f.landning = b.page.url();
      f.tacksida = /\/tack\/?$/.test(new URL(f.landning).pathname);  // mottagaren svarar 303 till /tack/ när fälten håller (omgång elva, F31)
      // Kvittot är ett funktionellt HTTP-prov, inte bevis på leverans till människa.
      f.status = outcome && outcome.status() >= 200 && outcome.status() < 400 && f.tacksida ? 'PASS' : 'FAIL';
      if (f.status === 'FAIL') r.fynd.push({ sida: url, formular: i, vad: outcome && f.skickat && !f.tacksida ? 'inskicket ledde inte till tacksidan (landade på ' + f.landning + ')' : 'vanlig form-POST gav inget lyckat svar utan JavaScript' });
    }
    r.sidor.push(row);
  }
} catch (error) {
  r.fynd.push({ vad: b.red(String(error.message)).slice(0, 300) });
} finally {
  r.blockerade = b.logg.blockerade; await b.stang();
}
r.status = r.fynd.length ? 'FAIL' : r.sidor.some(s => s.formular.some(f => f.status === 'EJ_MATT')) ? 'EJ_MATT' : 'PASS';
skriv(a.ut, 'UTAN-JS.json', JSON.stringify(r, null, 2) + '\n');
console.log(r.status); process.exitCode = r.status === 'FAIL' ? 1 : 0;
