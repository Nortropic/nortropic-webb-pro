import type { APIRoute } from 'astro';

// Alla .astro-sidor utom 404, dynamiska rutter och sidor med noindex (tacksidan och andra som inte ska hittas;
// byggstandarden 7.2: en noindex-sida som /tack/ står aldrig i sitemap.xml). Lägg till sidor ur
// innehållssamlingar här om sajten får sådana.
const kallor = import.meta.glob('./**/*.astro', { query: '?raw', import: 'default', eager: true }) as Record<string, string>;
// noindex som egenskap på sidans ram (<Bas noindex>, <Ram noindex>); noindex={false} räknas inte.
const noindex = /<[A-Z][\w.]*\s[^>]*\bnoindex\b(?!\s*=\s*\{\s*false)/;

export const GET: APIRoute = ({ site }) => {
  const rutter = Object.entries(kallor)
    .filter(([, kod]) => !noindex.test(kod))
    .map(([f]) => f.replace(/^\.\//, '').replace(/\.astro$/, ''))
    .filter((f) => !f.startsWith('404') && !f.includes('['))
    .map((f) => (f === 'index' ? '/' : '/' + f.replace(/\/?index$/, '') + '/'));
  const rader = rutter.map((r) => `  <url><loc>${new URL(r, site).href}</loc></url>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rader}\n</urlset>\n`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
