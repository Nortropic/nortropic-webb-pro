// slugvakt.mjs — samma gräns som slugvakt.py för Node-verktygen: med NWP_SLUG satt får en utkatalog eller sajt bara ligga
// under kunder/<slug>/, underlag/<slug>/ eller det temporära området (revisionen 2026-10-03, F1).
import { resolve, dirname, basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { realpathSync, existsSync } from 'node:fs';

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

export function vakta(p, vad = 'utkatalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const r = verklig(p);
  const rotar = [resolve(ROOT, 'kunder', e), resolve(ROOT, 'underlag', e), join('/tmp', 'nwp-' + e), join(tmpdir(), 'nwp-' + e)].map(verklig);
  if (!rotar.some((t) => r === t || r.startsWith(t + '/'))) {
    console.error(`slugvakten: ${vad} ${p} ligger inte i kunder/${e}/, underlag/${e}/ eller /tmp/nwp-${e}/ (NWP_SLUG); vägrar`);
    process.exit(2);
  }
}
