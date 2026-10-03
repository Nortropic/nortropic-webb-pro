// slugvakt.mjs — samma gräns som slugvakt.py för Node-verktygen: med NWP_SLUG satt får en utkatalog eller sajt bara ligga
// under kunder/<slug>/, underlag/<slug>/ eller det temporära området (revisionen 2026-10-03, F1).
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const ROOT = resolve(fileURLToPath(import.meta.url), '..', '..');

export function vakta(p, vad = 'utkatalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const r = resolve(String(p));
  const rotar = [resolve(ROOT, 'kunder', e), resolve(ROOT, 'underlag', e), '/tmp', '/private/tmp', tmpdir()].map((t) => resolve(t));
  if (!rotar.some((t) => r === t || r.startsWith(t + '/'))) {
    console.error(`slugvakten: ${vad} ${p} ligger inte i kunder/${e}/, underlag/${e}/ eller det temporära området (NWP_SLUG); vägrar`);
    process.exit(2);
  }
}
