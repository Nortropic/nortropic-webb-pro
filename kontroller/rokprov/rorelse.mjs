// Lokalt beteendeprov på den byggda GSAP-sidan. Ingen modell eller extern tjänst.
// Playwright Clock driver animationens klocka; vi mäter DOM/CSS, inte kodens markörer ensamma.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const adress = new URL('/rorelse/', process.argv[2]).href;
const b = await chromium.launch();
const ut = {};
const nara = (a, b) => Math.abs(a - b) < 0.05;
const klar = s => nara(s.opacity, 1) && nara(s.x, 0);
try {
  for (const rm of ['reduce', 'no-preference', 'byte']) {
    const c = await b.newContext({ reducedMotion: rm === 'reduce' ? 'reduce' : 'no-preference' });
    try {
      const p = await c.newPage(); const fel = [];
      p.on('console', m => { if (m.type() === 'error') fel.push(m.text()); });
      p.on('pageerror', e => fel.push(String(e)));
      await p.clock.install({ time: new Date('2030-01-01T00:00:00Z') });
      await p.clock.pauseAt(new Date('2030-01-01T00:00:01Z'));
      await p.goto(adress, { waitUntil: 'load' });
      const las = () => p.evaluate(() => {
        const s = getComputedStyle(document.getElementById('ruta'));
        return { tillstand: document.documentElement.dataset.rorelse || '', opacity: Number(s.opacity),
          x: s.transform === 'none' ? 0 : new DOMMatrix(s.transform).m41 };
      });
      // GSAP:s första render sker på animationens första requestAnimationFrame.
      await p.clock.runFor(16);
      const start = await las();
      await p.clock.runFor(200);
      const mellan = await las();
      if (rm === 'byte') await p.emulateMedia({ reducedMotion: 'reduce' });
      await p.clock.runFor(800);
      const slut = await las();
      ut[rm] = { start, mellan, slut, fel };
      assert.deepEqual(fel, [], 'konsolfel');
      if (rm === 'reduce') {
        assert([start, mellan, slut].every(s => klar(s) && s.tillstand === 'stilla'), JSON.stringify(ut[rm]));
      } else {
        assert(start.x < -30 && start.opacity < 0.25, 'rörelsen saknar startläge: ' + JSON.stringify(ut[rm]));
        assert(mellan.x > start.x && mellan.x < -0.05 && mellan.opacity > 0 && mellan.opacity < 1,
          'inget mellanläge: ' + JSON.stringify(ut[rm]));
        assert(klar(slut), 'fel slutposition: ' + JSON.stringify(ut[rm]));
        assert.equal(slut.tillstand, rm === 'byte' ? 'stilla' : 'gsap');
      }
    } finally { await c.close(); }
  }
  const c = await b.newContext({ javaScriptEnabled: false });
  try {
    const p = await c.newPage(); await p.goto(adress);
    const s = await p.locator('#ruta').evaluate(e => { const s = getComputedStyle(e); return {opacity: Number(s.opacity), transform: s.transform}; });
    assert(s.opacity === 1 && s.transform === 'none', 'innehållet försvinner utan JavaScript');
    ut.utan_js = s;
  } finally { await c.close(); }
  console.log(JSON.stringify(ut));
} finally { await b.close(); }
