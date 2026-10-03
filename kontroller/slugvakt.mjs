// slugvakt.mjs — samma gräns som slugvakt.py för Node-verktygen: med NWP_SLUG satt får en utkatalog eller sajt bara ligga
// under kunder/<slug>/, underlag/<slug>/ eller körningens eget tmp-område /tmp/nwp-bygge-<slug>/ (revisionen 2026-10-03,
// F1, omgång fem och sex). Symlänkar följs led för led, också länkar vars mål inte finns än; en utkatalog med en symlänk
// som leder ut vägras; en genomgång som inte hinner klart eller inte går att läsa räknas som misslyckad, inte ren; och
// rötterna är betrodda bara när varken de eller deras föräldrar är symlänkar.
import { resolve, dirname, basename, join, isAbsolute, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';
import { readdirSync, lstatSync, readlinkSync } from 'node:fs';

const ROOT = resolve(fileURLToPath(import.meta.url), '..', '..');
const MAX_POSTER = 20000;
const MAX_LANKAR = 40;

function arLank(p) {
  try { return lstatSync(p).isSymbolicLink(); } catch { return false; }
}

// Den verkliga sökvägen: varje led prövas med lstat; en symlänk byts mot sitt innehåll (relativt sin katalog) och
// upplösningen fortsätter därifrån, också när målet inte finns (omgång sex, F1: existsSync såg en hängande länk som ett
// nytt namn). path.resolve följer inga symlänkar alls.
function verklig(p) {
  let kvar = resolve(String(p)).split(sep).filter(Boolean);
  let cur = sep;
  let lankar = 0;
  while (kvar.length) {
    const led = kvar.shift();
    const nxt = join(cur, led);
    if (arLank(nxt)) {
      if (++lankar > MAX_LANKAR) throw new Error('för många symlänkar i ' + p);
      const mal = readlinkSync(nxt);
      const absolut = isAbsolute(mal) ? mal : join(cur, mal);
      kvar = resolve(absolut).split(sep).filter(Boolean).concat(kvar);
      cur = sep;
      continue;
    }
    cur = nxt;
  }
  return cur;
}

// Genomgång av katalogen: 'ren', 'ut' (med länken), 'ofullständig' (taket nått) eller 'fel' (något gick inte att läsa).
// Varje post prövas som symlänk; inget hoppas över.
function genomgang(katalog, rotar, raknare = { n: 0 }) {
  let poster;
  try { poster = readdirSync(katalog, { withFileTypes: true }); } catch (e) { return { status: 'fel', var: katalog }; }
  for (const d of poster) {
    if (++raknare.n > MAX_POSTER) return { status: 'ofullständig' };
    const v = join(katalog, d.name);
    if (d.isSymbolicLink()) {
      let mal;
      try { mal = verklig(v); } catch { return { status: 'fel', var: v }; }
      if (!rotar.some((t) => mal === t || mal.startsWith(t + sep))) return { status: 'ut', var: v };
    } else if (d.isDirectory()) {
      const r = genomgang(v, rotar, raknare);
      if (r.status !== 'ren') return r;
    }
  }
  return { status: 'ren' };
}

function forankrade(e) {
  const kedjor = [[join(ROOT, 'kunder'), join(ROOT, 'kunder', e)], [join(ROOT, 'underlag'), join(ROOT, 'underlag', e)]];
  const rotar = [];
  for (const kedja of kedjor) {
    for (const led of kedja) if (arLank(led)) return null;
    rotar.push(resolve(kedja[kedja.length - 1]));
  }
  for (const t of [join('/tmp', 'nwp-bygge-' + e), join(tmpdir(), 'nwp-bygge-' + e)]) {
    if (arLank(t)) return null;  // själva området; föräldern är systemets tmp (en symlänk på macOS) och betrodd
    rotar.push(verklig(t));
  }
  return rotar;
}

export function vakta(p, vad = 'utkatalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const neka = (skal) => { console.error(`slugvakten: ${vad} ${p} ${skal} (NWP_SLUG=${e}); vägrar`); process.exit(2); };
  const rotar = forankrade(e);
  if (!rotar) neka('kan inte prövas: kunder/, underlag/ eller slugkatalogen är en symlänk');
  let r;
  try { r = verklig(p); } catch (err) { neka('kan inte lösas upp: ' + err.message); }
  if (!rotar.some((t) => r === t || r.startsWith(t + sep))) neka(`ligger inte i kunder/${e}/, underlag/${e}/ eller /tmp/nwp-bygge-${e}/`);
  let dir = false;
  try { dir = lstatSync(r).isDirectory(); } catch { dir = false; }
  if (dir) {
    const g = genomgang(r, rotar);
    if (g.status === 'ut') neka('innehåller symlänken ' + g.var + ' som leder ut');
    if (g.status === 'ofullständig') neka('är för stor att gå igenom (över ' + MAX_POSTER + ' poster); peka på en mindre katalog');
    if (g.status === 'fel') neka('gick inte att gå igenom vid ' + g.var);
  }
}
