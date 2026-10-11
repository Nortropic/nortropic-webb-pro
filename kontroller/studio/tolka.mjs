// Motorns läsning av en kandidats källa för studion (kunskap/designstudio.md, Källkartan): samma karta som
// förhandsbygget lägger in (karta.mjs), räknad ur filerna på disken, med lägen i varje fil. Studion slår upp sondens id
// här och skriver aldrig på ett läge som inte kommer ur den här läsningen.
//
//     node kontroller/studio/tolka.mjs <projekt>     → JSON på stdout: {filer: {<väg i projektet>: {...}}, fel: {...}}
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, lstatSync, realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { element, stilblock, props, regler } from './karta.mjs';

const projekt = realpathSync(process.argv[2] || '.');
const krav = createRequire(path.join(projekt, 'package.json'));
const astroVag = krav.resolve('astro');
const { parse } = await import(pathToFileURL(createRequire(astroVag).resolve('@astrojs/compiler-rs')).href);
const postcss = (await import(pathToFileURL(createRequire(krav.resolve('vite')).resolve('postcss')).href)).default;

const ut = { projekt, filer: {}, fel: {} };
const src = path.join(projekt, 'src');
const besok = (kat) => {
  for (const namn of readdirSync(kat).sort()) {
    const p = path.join(kat, namn);
    const st = lstatSync(p);
    if (st.isSymbolicLink()) continue;
    if (st.isDirectory()) { besok(p); continue; }
    if (!/\.(astro|css)$/.test(namn)) continue;
    const rel = path.relative(projekt, p).split(path.sep).join('/');
    const kod = readFileSync(p, 'utf8');
    const post = { sha256: createHash('sha256').update(kod).digest('hex'), langd: kod.length };
    try {
      if (namn.endsWith('.css')) {
        post.regler = regler(kod, rel, 'css', postcss);
      } else {
        const el = element(kod, rel, parse);
        if (!el) { ut.fel[rel] = 'filen kunde inte tolkas av Astros kompilator'; continue; }
        post.element = el;
        post.props = props(kod, parse);
        post.stilblock = (stilblock(kod, parse) || []).map((b, i) => {
          const blk = { ...b, nr: i };
          if (b.lang === 'css') {
            try { blk.regler = regler(kod.slice(b.start, b.slut), rel, 's' + i, postcss, b.start); } catch (e) { blk.fel = String(e.message || e).slice(0, 200); }
          }
          return blk;
        });
        post.importer = importer(kod, parse);
      }
      ut.filer[rel] = post;
    } catch (e) {
      ut.fel[rel] = String(e && e.message || e).slice(0, 300);
    }
  }
};

// Frontmatterns importer: namn → källa, med läget för källans sträng (bildbyte skriver där).
function importer(kod, parse) {
  const r = parse(kod);
  const ast = typeof r.ast === 'string' ? JSON.parse(r.ast) : r.ast;
  const prog = ast && ast.frontmatter && ast.frontmatter.program ? ast.frontmatter.program.body || [] : [];
  const lista = [];
  for (const s of prog) {
    if (s.type !== 'ImportDeclaration' || !s.source) continue;
    for (const sp of s.specifiers || []) {
      lista.push({ namn: sp.local && sp.local.name, standard: sp.type === 'ImportDefaultSpecifier', kalla: s.source.value,
        start: s.source.start, slut: s.source.end, ra: kod.slice(s.source.start, s.source.end) });
    }
  }
  return lista;
}

try { besok(src); } catch (e) { ut.fel['src'] = String(e && e.message || e).slice(0, 300); }
process.stdout.write(JSON.stringify(ut));
