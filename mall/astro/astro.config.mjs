import { defineConfig, fontProviders } from 'astro/config';

// site = verksamhetens riktiga domän. Canonical och sitemap pekar dit; demon skyddas vid driftsättning, inte i HTML.
export default defineConfig({
  site: 'https://ERSATT-MED-DOMAN.se',
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
  // Typsnitt (byggstandarden 4.3): Astros typsnitts-API skriver @font-face, hashad fil, preload, CSP-källa och ett
  // reservtypsnitt med size-adjust uträknat ur filen. Lägg woff2-filen i src/assets/fonts/, byt namn och fil, ta bort
  // kommentaren och lägg <Font cssVariable="--typsnitt" preload /> i sidans head (se README). Systemtypsnitt: låt stå.
  // Provat 2026-10-03 på rökprovets sajt: provet grönt, 0 CSP-överträdelser, CLS 0.
  // fonts: [{
  //   provider: fontProviders.local(), name: 'Familj', cssVariable: '--typsnitt', fallbacks: ['sans-serif'],
  //   options: { variants: [{ src: ['./src/assets/fonts/familj-latin-wght-normal.woff2'], weight: '400 900', style: 'normal' }] },
  // }],
  // Typsnittsfiler bäddas aldrig in som data:-adresser i CSS: CSP:n nedan (default-src 'self') vägrar dem, och en liten
  // delmängd (latin-ext, kyrilliska) laddas ändå bara när sidan använder de tecknen. Designprovet 2026-10-05: två av
  // ateljéns tre riktningar fick konsolfel av inbäddade delmängder ur @fontsource (byggstandarden 8.7).
  vite: { build: { assetsInlineLimit: (fil) => (/\.(woff2?|ttf|otf|eot)$/i.test(fil) ? false : undefined) } },
  // CSP som metatagg med hashar (byggstandarden 8.2): skript bara med hash, allt från egen domän, stilattribut
  // tillåtna (style="" används för bildförhållanden och variabler). Provad 2026-10-02 på ett riktigt bygge: 0 överträdelser.
  security: {
    csp: {
      directives: ["default-src 'self'", "img-src 'self' data:", "object-src 'none'", "base-uri 'self'", "form-action 'self'"],
      styleDirective: { resources: ["'self'", { resource: "'unsafe-inline'", kind: 'attribute' }] },
    },
  },
});
