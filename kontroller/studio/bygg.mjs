// Kandidatens förhandsbygge med studions källkarta (kunskap/designstudio.md, Källkartan): samma bygge som `astro build`
// (Astros JavaScript-API, build, med projektets egen konfiguration och produktionsläge) plus ett load-steg som ger mallens
// element opaka id (karta.mjs). Körs av prova.bygg_inom_grans innanför processgränsen; läser bara kandidatens projekt,
// sajtens delade node_modules och den här katalogen. Helbygget och exporten bygger aldrig så här.
//
//     node kontroller/studio/bygg.mjs <projekt>
import path from 'node:path';
import { realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { kartaPlugin } from './karta.mjs';

const projekt = realpathSync(process.argv[2] || '.');
const krav = createRequire(path.join(projekt, 'package.json'));
// Astro och dess kompilator ur projektets egna beroenden, samma instanser som bygget använder
const astroVag = krav.resolve('astro');
const astro = await import(pathToFileURL(astroVag).href);
const kompilator = await import(pathToFileURL(createRequire(astroVag).resolve('@astrojs/compiler-rs')).href);
// postcss ur Vites beroenden (samma version som läser stilarna i bygget); saknas den får bara elementen id
let postcss = null;
try { postcss = (await import(pathToFileURL(createRequire(krav.resolve('vite')).resolve('postcss')).href)).default; } catch { postcss = null; }
process.chdir(projekt);
await astro.build({ root: projekt, vite: { plugins: [kartaPlugin({ root: projekt, parse: kompilator.parse, postcss })] } });
