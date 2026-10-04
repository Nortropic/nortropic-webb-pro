// slugvakt.mjs — samma gräns som slugvakt.py för Node-verktygen: med NWP_SLUG satt får en utkatalog eller sajt bara ligga
// under kunder/<slug>/, underlag/<slug>/, körningens eget tmp-område /tmp/nwp-bygge-<slug>/ eller granskarnas
// arbetskataloger /tmp/nwp-granskning/<slug>-… (revisionen 2026-10-03,
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

// Den verkliga sökvägen, led för led som filsystemet gör det: inget förenklas i förväg. Varje led prövas med lstat; en
// symlänk byts mot sitt innehålls led (absolut: från roten; relativ: från länkens katalog) och . och .. hanteras först
// när de nås, efter föregående symlänk (omgång sju, F1: resolve() tog bort .. innan länkarna följts, så upp/../annat
// såg ut att stanna i katalogen). Målet behöver inte finnas (omgång sex: hängande länkar).
function led(p) {
  return String(p).split(sep).filter((x) => x.length > 0);
}

function verklig(p) {
  const s = String(p);
  let kvar = isAbsolute(s) ? led(s) : led(process.cwd()).concat(led(s));
  let cur = sep;
  let lankar = 0;
  while (kvar.length) {
    const namn = kvar.shift();
    if (namn === '.') continue;
    if (namn === '..') { cur = cur === sep ? sep : dirname(cur); continue; }
    const nxt = cur === sep ? sep + namn : cur + sep + namn;
    if (arLank(nxt)) {
      if (++lankar > MAX_LANKAR) throw new Error('för många symlänkar i ' + p);
      const mal = readlinkSync(nxt);
      if (isAbsolute(mal)) { cur = sep; kvar = led(mal).concat(kvar); } else { kvar = led(mal).concat(kvar); }
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

function iGranskningsrot(r, e) {
  let g = null; try { g = verklig(join('/tmp', 'nwp-granskning', e)); } catch { return false; }
  return r === g || r.startsWith(g + sep);
}

/** Som vakta, men utan genomgång av innehållet: för en katalog som bara ska ligga rätt (en sajt med node_modules). */
export function inom(p, vad = 'katalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const neka = (skal) => { console.error(`slugvakten: ${vad} ${p} ${skal} (NWP_SLUG=${e}); vägrar`); process.exit(2); };
  const rotar = forankrade(e);
  if (!rotar) neka('kan inte prövas: kunder/, underlag/ eller slugkatalogen är en symlänk');
  let r;
  try { r = verklig(p); } catch (err) { neka('kan inte lösas upp: ' + err.message); }
  if (!rotar.some((t) => r === t || r.startsWith(t + sep)) && !iGranskningsrot(r, e)) neka(`ligger inte i kunder/${e}/, underlag/${e}/, /tmp/nwp-bygge-${e}/ eller /tmp/nwp-granskning/${e}/`);
}

export function vakta(p, vad = 'utkatalogen') {
  const e = process.env.NWP_SLUG;
  if (!e || !p) return;
  const neka = (skal) => { console.error(`slugvakten: ${vad} ${p} ${skal} (NWP_SLUG=${e}); vägrar`); process.exit(2); };
  const rotar = forankrade(e);
  if (!rotar) neka('kan inte prövas: kunder/, underlag/ eller slugkatalogen är en symlänk');
  let r;
  try { r = verklig(p); } catch (err) { neka('kan inte lösas upp: ' + err.message); }
  // granskarnas arbetskataloger /tmp/nwp-granskning/<slug>/… (granska.ARBETSROT) hör också till bygget; sluggen är ett eget
  // led så att eget och eget-annat aldrig överlappar (Codex R24 F28, R25)
  const iGranskning = iGranskningsrot(r, e);
  if (!rotar.some((t) => r === t || r.startsWith(t + sep)) && !iGranskning) neka(`ligger inte i kunder/${e}/, underlag/${e}/, /tmp/nwp-bygge-${e}/ eller /tmp/nwp-granskning/${e}/`);
  let dir = false;
  try { dir = lstatSync(r).isDirectory(); } catch { dir = false; }
  if (dir) {
    const g = genomgang(r, iGranskning ? [...rotar, r] : rotar);
    if (g.status === 'ut') neka('innehåller symlänken ' + g.var + ' som leder ut');
    if (g.status === 'ofullständig') neka('är för stor att gå igenom (över ' + MAX_POSTER + ' poster); peka på en mindre katalog');
    if (g.status === 'fel') neka('gick inte att gå igenom vid ' + g.var);
  }
}
