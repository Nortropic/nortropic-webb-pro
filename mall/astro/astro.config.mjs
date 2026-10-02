import { defineConfig } from 'astro/config';

// site = verksamhetens riktiga domän. Canonical och sitemap pekar dit; demon skyddas vid driftsättning, inte i HTML.
export default defineConfig({
  site: 'https://ERSATT-MED-DOMAN.se',
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
  // CSP som metatagg med hashar (byggstandarden 8.2): skript bara med hash, allt från egen domän, stilattribut
  // tillåtna (style="" används för bildförhållanden och variabler). Provad 2026-10-02 på ett riktigt bygge: 0 överträdelser.
  security: {
    csp: {
      directives: ["default-src 'self'", "img-src 'self' data:", "object-src 'none'", "base-uri 'self'", "form-action 'self'"],
      styleDirective: { resources: ["'self'", { resource: "'unsafe-inline'", kind: 'attribute' }] },
    },
  },
});
