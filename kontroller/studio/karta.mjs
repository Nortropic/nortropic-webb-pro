// Studions källkarta (designstudion, DS3; kunskap/designstudio.md, Källkartan).
//
// Varje HTML-element i en .astro-mall får ett opakt id, data-nwp-k, som bara beror på filens väg relativt projektet och
// elementets plats i mallens träd: index bland syskonelementen, genom komponenter och uttryck. Ett id ändras alltså
// inte av att en text, ett attribut eller en stilregel ändras, men av att elementen flyttas. Samma kod används av
// kandidatens förhandsbygge (bygg.mjs, som lägger in attributen) och av motorn (studio.py genom tolka.mjs, som räknar fram
// kartan ur källan igen): sidans eget påstående om ett id är aldrig ett belägg för vilken fil som äger elementet.
//
// Kompilatorn är Astros egen (@astrojs/compiler-rs, parse med positioner), samma som bygget. En fil som den inte kan
// tolka utan fel får inga id och byggs som den är; elementet kan då inte redigeras direkt (studion erbjuder AI-vägen).
// Modulen importerar bara Nodes egna moduler, så att den kan läsas innanför byggets processgräns.
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';

export const ATTRIBUT = 'data-nwp-k';
// Element som aldrig får id: dokumentets ram, huvudets innehåll och sådant vars innehåll inte är mall.
const UTAN = new Set(['html', 'head', 'body', 'meta', 'link', 'title', 'base', 'style', 'script', 'noscript', 'template', 'slot']);

export function nyckel(rel, vag) {
  return createHash('sha256').update(rel + '\0' + vag).digest('hex').slice(0, 12);
}

export function tolka(kod, parse) {
  const r = parse(kod);
  const ast = typeof r.ast === 'string' ? JSON.parse(r.ast) : r.ast;
  const fel = (r.diagnostics || []).filter((d) => String(d.severity).toLowerCase() === 'error');
  return fel.length || !ast || ast.type !== 'AstroRoot' ? null : ast;
}

function elementnamn(nod) {
  const n = nod.openingElement && nod.openingElement.name;
  return n && n.type === 'JSXIdentifier' ? n.name : null;
}

// Elementbarnen under x utan att gå igenom ett annat element: fragment är genomskinliga, och det som står i ett uttryck
// ({lista.map(...)}, {villkor && <p/>}) märks, eftersom det kan visas noll eller flera gånger.
function elementbarn(x, iUttryck = false, ut = []) {
  if (!x || typeof x !== 'object') return ut;
  if (Array.isArray(x)) { for (const y of x) elementbarn(y, iUttryck, ut); return ut; }
  if (x.type === 'JSXElement') { ut.push([x, iUttryck]); return ut; }
  if (x.type === 'JSXFragment') return elementbarn(x.children, iUttryck, ut);
  if (x.type === 'JSXExpressionContainer') return elementbarn(x.expression, true, ut);
  if (x.type === 'JSXText' || x.type === 'AstroComment' || x.type === 'Literal') return ut;
  for (const [k, v] of Object.entries(x)) if (k !== 'type' && v && typeof v === 'object') elementbarn(v, iUttryck, ut);
  return ut;
}

function attributnamn(a) {
  if (!a || a.type !== 'JSXAttribute' || !a.name) return null;
  if (a.name.type === 'JSXIdentifier') return a.name.name;
  if (a.name.type === 'JSXNamespacedName') return a.name.namespace.name + ':' + a.name.name.name;
  return null;
}

function attribut(oppning, kod) {
  return (oppning.attributes || []).map((a) => {
    if (a.type !== 'JSXAttribute') return { spridning: true, start: a.start, slut: a.end };
    const v = a.value;
    const varde = !v ? { slag: 'tom' }
      : v.type === 'Literal' ? { slag: 'literal', text: v.value, start: v.start, slut: v.end, ra: kod.slice(v.start, v.end) }
      : v.type === 'JSXExpressionContainer' && v.expression && v.expression.type === 'Literal' && typeof v.expression.value === 'string'
        ? { slag: 'literal', text: v.expression.value, start: v.expression.start, slut: v.expression.end, ra: kod.slice(v.expression.start, v.expression.end), iUttryck: true }
        : { slag: 'uttryck', start: v.start, slut: v.end, ra: kod.slice(v.start, v.end) };
    return { namn: attributnamn(a), start: a.start, slut: a.end, varde };
  });
}

// Alla element i mallen, i källordning: id (bara HTML-element som får ett), väg, tagg, komponent eller inte, positioner,
// attribut och om elementet står i ett uttryck. null när filen inte går att tolka.
export function element(kod, rel, parse) {
  const ast = tolka(kod, parse);
  if (!ast) return null;
  const ut = [];
  const besok = (lista, vag, iUttryck) => {
    lista.forEach(([nod, u], i) => {
      const seg = (u ? 'u' : '') + i;
      const v = vag ? vag + '/' + seg : seg;
      const namn = elementnamn(nod);
      const komponent = !!namn && /^[A-Z]/.test(namn);
      const html = !!namn && !komponent && !namn.includes('.');
      const op = nod.openingElement;
      const barnlista = nod.children || [];
      ut.push({
        k: html && !UTAN.has(namn.toLowerCase()) ? nyckel(rel, v) : null,
        vag: v, tagg: namn, komponent, start: nod.start, slut: nod.end,
        oppning: [op.start, op.end], namnSlut: op.name.end, sjalvstangd: !!op.selfClosing,
        iUttryck: iUttryck || u, attribut: attribut(op, kod),
        barn: barnlista.map((b) => ({ typ: b.type, start: b.start, slut: b.end })),
        // egen text: en textnod som inte bara är blanktecken, eller ett uttryck bland barnen ({rubrik})
        text: barnlista.some((b) => (b.type === 'JSXText' && /\S/.test(b.value || '')) || b.type === 'JSXExpressionContainer'),
      });
      besok(elementbarn(nod.children), v, iUttryck || u);
    });
  };
  besok(elementbarn(ast.body), '', false);
  return ut;
}

// Källan med data-nwp-k insatt direkt efter taggens namn; bara insättningar, inget annat i filen skrivs om.
export function annotera(kod, rel, parse) {
  const lista = element(kod, rel, parse);
  if (!lista) return null;
  const ins = lista.filter((e) => e.k).map((e) => [e.namnSlut, ` ${ATTRIBUT}="${e.k}"`]).sort((a, b) => b[0] - a[0]);
  let ut = kod;
  for (const [pos, text] of ins) ut = ut.slice(0, pos) + text + ut.slice(pos);
  return ut;
}

// Mallens <style>-block: innehållets läge, is:global och lang.
export function stilblock(kod, parse) {
  const ast = tolka(kod, parse);
  if (!ast) return null;
  const ut = [];
  const sok = (x) => {
    if (!x || typeof x !== 'object') return;
    if (Array.isArray(x)) { x.forEach(sok); return; }
    if (x.type === 'JSXElement' && elementnamn(x) === 'style') {
      const attr = attribut(x.openingElement, kod);
      const text = (x.children || []).filter((b) => b.type === 'JSXText');
      const start = text.length ? text[0].start : x.openingElement.end;
      const slut = text.length ? text[text.length - 1].end : x.openingElement.end;
      ut.push({ start, slut, global: attr.some((a) => a.namn === 'is:global'), lang: (attr.find((a) => a.namn === 'lang') || {}).varde?.text || 'css',
        inline: attr.some((a) => a.namn === 'is:inline') });
      return;
    }
    for (const [k, v] of Object.entries(x)) if (k !== 'type' && v && typeof v === 'object') sok(v);
  };
  sok(ast.body);
  return ut;
}

// Komponentens Props: namn, valfri, och de tillåtna literalvärdena när typen är en union av strängar (variant?: 'a' | 'b'),
// med standardvärdet ur `const { … = '…' } = Astro.props`.
export function props(kod, parse) {
  const ast = tolka(kod, parse);
  if (!ast || !ast.frontmatter || !ast.frontmatter.program) return [];
  const prog = ast.frontmatter.program.body || [];
  const ut = new Map();
  for (const s of prog) {
    const dekl = s.type === 'ExportNamedDeclaration' ? s.declaration : s;
    if (!dekl || dekl.type !== 'TSInterfaceDeclaration' || !dekl.id || dekl.id.name !== 'Props') continue;
    for (const p of dekl.body.body || []) {
      if (p.type !== 'TSPropertySignature' || !p.key || p.key.type !== 'Identifier') continue;
      const t = p.typeAnnotation && p.typeAnnotation.typeAnnotation;
      const varden = t && t.type === 'TSUnionType' && t.types.every((x) => x.type === 'TSLiteralType' && typeof x.literal.value === 'string')
        ? t.types.map((x) => x.literal.value) : null;
      ut.set(p.key.name, { namn: p.key.name, valfri: !!p.optional, varden, typ: t ? t.type : null });
    }
  }
  for (const s of prog) {
    if (s.type !== 'VariableDeclaration') continue;
    for (const d of s.declarations) {
      const init = d.init;
      const arProps = init && init.type === 'MemberExpression' && init.object && init.object.name === 'Astro' && init.property && init.property.name === 'props';
      if (!arProps || !d.id || d.id.type !== 'ObjectPattern') continue;
      for (const p of d.id.properties) {
        const namn = p.key && p.key.name;
        if (namn && ut.has(namn) && p.value && p.value.type === 'AssignmentPattern' && p.value.right && p.value.right.type === 'Literal') ut.get(namn).standard = p.value.right.value;
      }
    }
  }
  return [...ut.values()];
}

// --- Stilreglerna ---------------------------------------------------------------------------------------------------
// Varje stilregel i källan (en .css-fil under src/ eller ett <style>-block i en mall) får ett eget id, insatt som den
// första deklarationen i regeln: --nwp-r:"<id>". Bygget (Astros skopning, Lightning CSS) skriver om väljare och värden,
// men deklarationen följer regeln, så att motorns webbläsare kan läsa vilken källregel som vinner kaskaden för en
// egenskap utan att jämföra omskriven text. Egenskapen ändrar inget som syns.
export const REGELATTRIBUT = '--nwp-r';
const UTAN_REGLER = new Set(['keyframes', '-webkit-keyframes', 'font-face', 'property', 'counter-style', 'page', 'theme']);

// Reglerna i en stilmall: id, väg (index genom at-regler och nästling), väljare, at-reglerna runt, deklarationerna med
// lägen, och var den första deklarationen sätts in. bas är stilmallens läge i filen (ett <style>-blocks början).
export function regler(css, rel, del, postcss, bas = 0) {
  const rot = postcss.parse(css);
  const ut = [];
  const besok = (nod, vag, ram) => {
    (nod.nodes || []).forEach((b, i) => {
      const v = vag ? vag + '/' + i : String(i);
      if (b.type === 'atrule') {
        if (UTAN_REGLER.has(String(b.name).toLowerCase())) return;
        besok(b, v, ram.concat([{ namn: b.name, villkor: b.params }]));
      } else if (b.type === 'rule') {
        const oppnar = css.indexOf('{', b.source.start.offset);
        const decls = (b.nodes || []).filter((d) => d.type === 'decl').map((d) => {
          // Deklarationens text som den står (postcss återger en orörd nod exakt) och värdets läge utan omgivande
          // blanktecken: egenskap + mellanrum (":" med blanktecken) + värdet. Stämmer texten inte med källan på
          // läget märks deklarationen oklar och skrivs aldrig.
          const start = d.source.start.offset;
          const text = d.toString();
          const mellan = (d.raws && typeof d.raws.between === 'string') ? d.raws.between : ':';
          const ra = d.raws && d.raws.value && typeof d.raws.value.raw === 'string' ? d.raws.value.raw : d.value;
          const vs = start + d.prop.length + mellan.length + (ra.length - ra.trimStart().length);
          return { egenskap: d.prop, varde: d.value, ra: ra.trim(), viktig: !!d.important, start: bas + start, slut: bas + start + text.length,
            vardeStart: bas + vs, vardeSlut: bas + vs + ra.trim().length, oklar: css.slice(start, start + text.length) !== text };
        });
        // En ny deklaration sätts in efter regelns sista deklaration, så att den kommer efter kortformer i samma regel:
        // efter dess semikolon när det finns, annars med ett eget semikolon före. Utan deklarationer: direkt efter {.
        const sistaDekl = decls[decls.length - 1];
        let infoga = bas + oppnar + 1, foreSemikolon = false;
        if (sistaDekl) {
          const m = /^\s*;/.exec(css.slice(sistaDekl.slut - bas));
          if (m) infoga = sistaDekl.slut + m[0].length; else { infoga = sistaDekl.slut; foreSemikolon = true; }
        }
        ut.push({ r: nyckel(rel + '#' + del, v), vag: v, valjare: b.selector, ram, deklarationer: decls,
          start: bas + b.source.start.offset, oppnar: bas + oppnar,
          infoga, foreSemikolon, harNastlade: (b.nodes || []).some((x) => x.type === 'rule') });
        besok(b, v, ram.concat([{ namn: '&', villkor: b.selector }]));
      }
    });
  };
  besok(rot, '', []);
  return ut;
}

function annoteraRegler(css, rel, del, postcss) {
  const lista = regler(css, rel, del, postcss).filter((r) => r.oppnar >= 0).sort((a, b) => b.oppnar - a.oppnar);
  let ut = css;
  for (const r of lista) ut = ut.slice(0, r.oppnar + 1) + `${REGELATTRIBUT}:"${r.r}";` + ut.slice(r.oppnar + 1);
  return ut;
}

// En .astro-fil med elementens id och stilblockens regel-id; blocken numreras i källordning.
export function annoteraMall(kod, rel, parse, postcss) {
  const block = postcss ? (stilblock(kod, parse) || []) : [];
  let ut = kod;
  // blocken bakifrån, så att lägena framför står still; elementens id sätts in efteråt i den tolkade nya källan
  block.map((b, i) => [b, i]).sort((x, y) => y[0].start - x[0].start).forEach(([b, i]) => {
    if (b.lang !== 'css') return;
    try {
      ut = ut.slice(0, b.start) + annoteraRegler(ut.slice(b.start, b.slut), rel, 's' + i, postcss) + ut.slice(b.slut);
    } catch { /* ett block som postcss inte kan läsa byggs som det är */ }
  });
  // elementens id beror bara på vägen i trädet, så den nya källan ger samma id som originalet
  return annotera(ut, rel, parse) ?? null;
}

// Vite-steget i kandidatens förhandsbygge: varje .astro- och .css-fil under projektets src/ läses med id insatta. Allt
// annat (node_modules, virtuella moduler, frågor som ?astro&type=style) lämnas åt Astro och Vite.
export function kartaPlugin({ root, parse, postcss }) {
  const rot = realpathSync(root);
  const src = path.join(rot, 'src') + path.sep;
  return {
    name: 'nwp-karta',
    enforce: 'pre',
    load(id) {
      if (id.includes('\0') || id.includes('?') || !/\.(astro|css)$/.test(id)) return null;
      let fil;
      try { fil = realpathSync(id); } catch { return null; }
      if (!fil.startsWith(src)) return null;
      try {
        const kod = readFileSync(fil, 'utf8');
        const rel = path.relative(rot, fil).split(path.sep).join('/');
        if (fil.endsWith('.css')) return postcss ? annoteraRegler(kod, rel, 'css', postcss) : null;
        return annoteraMall(kod, rel, parse, postcss);
      } catch {
        return null;
      }
    },
  };
}
