import { defineConfig } from 'astro/config';

// site = verksamhetens riktiga domän. Canonical och sitemap pekar dit; demon skyddas vid driftsättning, inte i HTML.
export default defineConfig({
  site: 'https://ERSATT-MED-DOMAN.se',
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
});
