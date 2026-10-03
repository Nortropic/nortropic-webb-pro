// slugvakt.mjs — samma gräns som slugvakt.py för Node-verktygen: med NWP_SLUG satt får en utkatalog eller sajt bara ligga
// under kunder/<slug>/, underlag/<slug>/ eller det temporära området (revisionen 2026-10-03, F1).
import { resolve, dirname, basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { realpathSync, existsSync, readdirSync, lstatSync } from 'node:fs';

const ROOT = resolve(fileURLToPath(import.meta.url), '..', '..');

// Den verkliga sökvägen: symlänkar följs i de delar som finns, resten läggs till som de är (path.resolve följer inga
// symlänkar; en länk under ett tillåtet område kunde annars leda skrivningen ut; omgång fyra, F1).
function verklig(p) {
  let kvar = [];
  let bas = resolve(String(p));
  while (!existsSync(bas)) {
    kvar.unshift(basename(bas));
    const upp = dirname(bas);
    if (upp === bas) break;
    bas = upp;
  }
  try { bas = realpathSync.native(bas); } catch { /* lämna som den är */ }
  return kvar.length ? join(bas, ...kvar) : bas;
}

const HOPPA = new Set(['node_modules', '.git', '.astro']);
const MAX_POSTER = 20000;

// Första symlänk under katalogen vars mål ligger utanför rötterna (en planterad länk skulle leda skrivningen ut).
function symlankUt(katalog, rotar, raknare = { n: 0 }) {
  let poster;
  try { poster = readdirSync(katalog, { withFileTypes: true }); } catch { return null; }
  for (const d of poster) {
    if (++raknare.n > MAX_POSTER) return null;
    const v = join(katalog, d.name);
    if (d.isSymbolicLink()) {
      const mal = verklig(v);
      if (!rotar.some((t) => mal === t || mal.startsWith(t + '/'))) return v;
    } else if (d.isDirectory() && !HOPPA.has(d.name)) {
      const hit = symlankUt(v, rotar, raknare);
      if (hit) return hit;
    }
  }
  return null;
}

export function vakta(p, vad = 'utkatalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const r = verklig(p);
  const rotar = [resolve(ROOT, 'kunder', e), resolve(ROOT, 'underlag', e), join('/tmp', 'nwp-bygge-' + e), join(tmpdir(), 'nwp-bygge-' + e)].map(verklig);
  const inne = rotar.some((t) => r === t || r.startsWith(t + '/'));
  let lank = null;
  if (inne) { try { if (lstatSync(r).isDirectory()) lank = symlankUt(r, rotar); } catch { /* finns inte än */ } }
  if (!inne || lank) {
    console.error(`slugvakten: ${vad} ${p} ligger inte i kunder/${e}/, underlag/${e}/ eller /tmp/nwp-bygge-${e}/ (NWP_SLUG)${lank ? ', eller innehåller symlänken ' + lank + ' som leder ut' : ''}; vägrar`);
    process.exit(2);
  }
}
