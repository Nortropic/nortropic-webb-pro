import type { APIRoute } from 'astro';

// Alla .astro-sidor utom 404 och dynamiska rutter. Lägg till sidor ur innehållssamlingar här om sajten får sådana.
const sidor = Object.keys(import.meta.glob('./**/*.astro'));

export const GET: APIRoute = ({ site }) => {
  const rutter = sidor
    .map((f) => f.replace(/^\.\//, '').replace(/\.astro$/, ''))
    .filter((f) => !f.startsWith('404') && !f.includes('['))
    .map((f) => (f === 'index' ? '/' : '/' + f.replace(/\/?index$/, '') + '/'));
  const rader = rutter.map((r) => `  <url><loc>${new URL(r, site).href}</loc></url>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${rader}\n</urlset>\n`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
