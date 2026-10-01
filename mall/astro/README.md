# Mall: Astro, statisk

Kopieras till `kunder/<slug>/sajt/` i steg 5. Den bär bara teknik: språk, canonical, sitemap.xml, robots.txt, 404.
Ingen design, inga komponenter, inga typsnitt. Allt synligt skrivs för verksamheten.

1. Byt `site` i `astro.config.mjs` mot verksamhetens domän (ur `VERKSAMHET.json`, fältet `webb.doman`).
2. Skriv sidorna i `src/pages/` med `Bas.astro` (titel ≤ 60 tecken, beskrivning ≤ 155, en h1 per sida).
3. Bilder i `src/assets/` och `<Image>` från `astro:assets` (sharp optimerar). Typsnitt självhostade i `public/fonts/`.
4. `npm install` en gång, sedan `npm run build`. Provet bygger själv: `.venv/bin/python kontroller/prova.py <slug>`.

Demon skyddas vid driftsättning (lösenord och `X-Robots-Tag: noindex` som svarshuvud), aldrig med noindex i HTML:
då blir SEO-kontrollen och Lighthouse missvisande.
