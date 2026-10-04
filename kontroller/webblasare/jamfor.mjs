#!/usr/bin/env node
// jamfor.mjs — pixeljämförelse mellan två PNG-bilder: byggets bild mot ateljévinnarens (designprovet, Codex 2026-10-04 steg 4:
// behåll den godkända koden och upptäck försämringar under utbyggnaden). Mäter förändring, inte skönhet: andelen pixlar som
// skiljer sig mer än toleransen över den gemensamma ytan (övre vänstra hörnet linjerat) och storleksskillnaden. JSON på
// stdout; --ut skriver en skillnadsbild (olika pixlar röda över en blek kopia av a). Ingen beroende utöver Playwrights
// medföljande pngjs.
//   node jamfor.mjs --a vinnare.png --b bygget.png [--ut skillnad.png] [--tolerans 24]
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
const require = createRequire(import.meta.url);
const { PNG } = require('playwright-core/lib/utilsBundle');

function arg(namn, standard) { const i = process.argv.indexOf('--' + namn); return i >= 0 && process.argv[i + 1] !== undefined ? process.argv[i + 1] : standard; }
const a = arg('a'), b = arg('b'), ut = arg('ut'), tolerans = Number(arg('tolerans', '24'));
if (!a || !b || !Number.isFinite(tolerans)) { console.error('användning: jamfor.mjs --a A.png --b B.png [--ut skillnad.png] [--tolerans 24]'); process.exit(2); }
let A, B;
try { A = PNG.sync.read(readFileSync(a)); B = PNG.sync.read(readFileSync(b)); } catch (e) { console.log(JSON.stringify({ fel: String(e && e.message || e) })); process.exit(1); }
const w = Math.min(A.width, B.width), h = Math.min(A.height, B.height);
let olika = 0;
const D = ut ? new PNG({ width: w, height: h }) : null;
for (let y = 0; y < h; y++) {
  for (let x = 0; x < w; x++) {
    const ia = (y * A.width + x) * 4, ib = (y * B.width + x) * 4;
    const d = Math.max(Math.abs(A.data[ia] - B.data[ib]), Math.abs(A.data[ia + 1] - B.data[ib + 1]), Math.abs(A.data[ia + 2] - B.data[ib + 2]));
    const skiljer = d > tolerans;
    if (skiljer) olika++;
    if (D) {
      const id = (y * w + x) * 4;
      if (skiljer) { D.data[id] = 220; D.data[id + 1] = 30; D.data[id + 2] = 30; }
      else { const g = Math.round(255 - (255 - (0.3 * A.data[ia] + 0.59 * A.data[ia + 1] + 0.11 * A.data[ia + 2])) * 0.35); D.data[id] = D.data[id + 1] = D.data[id + 2] = g; }
      D.data[id + 3] = 255;
    }
  }
}
if (D) writeFileSync(ut, PNG.sync.write(D));
console.log(JSON.stringify({ a: { bredd: A.width, hojd: A.height }, b: { bredd: B.width, hojd: B.height }, gemensam: { bredd: w, hojd: h },
  olika, andel: w * h ? olika / (w * h) : null, hojdskillnad: B.height - A.height, breddskillnad: B.width - A.width, tolerans }));
