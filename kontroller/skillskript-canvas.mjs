// Betrodd statisk canvas-renderare. Körs endast genom skillskript.py och dess canvas-väg i webbtjänsten.
// Uppdraget är en redan validerad SVG + inbäddade typsnitt, aldrig JavaScript eller en URL.
import { readFileSync, writeFileSync, lstatSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { natgrans } from './webblasare/gemensamt.mjs';

if (process.argv.length !== 3 || process.argv[2] !== 'canvas.json') throw new Error('fast canvas-uppdrag krävs');
if (!lstatSync('canvas.json').isFile() || lstatSync('canvas.json').isSymbolicLink()) throw new Error('uppdraget är inte en vanlig fil');
if (!existsSync('.nwp-agare.json')) throw new Error('registrerad tillfällig katalog krävs');
const job = JSON.parse(readFileSync('canvas.json', 'utf8'));
if (![job.width, job.height].every(n => Number.isInteger(n) && n > 0 && n <= 4096)
  || !['png', 'pdf', 'both'].includes(job.format)) throw new Error('ogiltigt renderuppdrag');
const fonts = job.fonts.map(f => {
  if (!/^[A-Za-z0-9_-]+$/.test(f.family) || !/^[A-Za-z0-9+/=]+$/.test(f.data)) throw new Error('ogiltigt typsnitt');
  return `@font-face{font-family:"${f.family}";src:url(data:font/ttf;base64,${f.data}) format("truetype");font-display:block}`;
}).join('\n');
// Sidans skydd: SVG-vakt i Python, JavaScript avstängt, CSP och blockerade sidförfrågningar.
// natgrans är tjänstens befintliga domänpolicy, inte en OS-gräns som isolerar all browsertrafik.
const html = `<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'"><style>
  ${fonts}html,body{margin:0;padding:0;width:${job.width}px;height:${job.height}px;overflow:hidden}
  svg{display:block;width:${job.width}px;height:${job.height}px}
  </style></head><body>${job.svg}</body></html>`;
// Font-face ligger i det egna dokumentet så SVG-text får de medföljande typsnitten.
const grans = await natgrans([]);
let browser;
try {
  browser = await chromium.launch(grans ? grans.playwright : {});
  const ctx = await browser.newContext({ viewport: { width: job.width, height: job.height },
    deviceScaleFactor: 1, javaScriptEnabled: false, serviceWorkers: 'block' });
  const requests = [];
  await ctx.route('**/*', async r => { requests.push(r.request().resourceType()); await r.abort(); });
  const page = await ctx.newPage();
  await page.setContent(html, { waitUntil: 'load', timeout: 20000 });
  // evaluate kör bara denna betrodda funktion; modellen kan inte tillföra någon programtext.
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(i => i.decode()));
  });
  if (requests.length) throw new Error('canvas försökte hämta en extern resurs');
  if (job.format === 'png' || job.format === 'both') {
    const png = await page.screenshot({ omitBackground: true });
    writeFileSync(join(process.cwd(), 'canvas.png'), png, { flag: 'wx', mode: 0o600 });
  }
  if (job.format === 'pdf' || job.format === 'both') {
    const pdf = await page.pdf({ width: `${job.width}px`, height: `${job.height}px`, printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 } });
    writeFileSync(join(process.cwd(), 'canvas.pdf'), pdf, { flag: 'wx', mode: 0o600 });
  }
  console.log(JSON.stringify({ status: 'renderad', width: job.width, height: job.height, format: job.format,
    fonts: job.fonts.map(f => f.family), externa_anrop: requests.length }));
} finally {
  if (browser) await browser.close();
  if (grans) await grans.stang();
}
