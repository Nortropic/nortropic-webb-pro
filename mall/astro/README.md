# Mall: Astro, statisk

Kopieras till `kunder/<slug>/sajt/` i steg 5. Den bär bara teknik: språk, canonical, theme-color, favicon,
delningsbild, skiplänk, CSP, sitemap.xml, robots.txt, 404. Ingen design, inga komponenter, inga typsnitt. Allt
synligt skrivs för verksamheten. Byggstandarden som provet prövar står i `kunskap/byggstandard.md`.

1. Byt `site` i `astro.config.mjs` mot verksamhetens domän (ur `VERKSAMHET.json`, fältet `webb.doman`).
2. Skriv sidorna i `src/pages/` med `Bas.astro`: `titel` (50–60 tecken), `beskrivning` (120–155), `tema`
   (verksamhetens bärande färg som hex). Varje sida har `<header>` med `<nav>` och telefonnumret som tel-länk,
   `<main id="innehall">`, en h1 och `<footer>`. Skriv om `404.astro` med samma sidhuvud och sidfot.
3. Skapa `public/favicon.svg` ur verksamhetens märke. Kör sedan
   `node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <eget foto> --bakgrund '<hex>'`, som gör
   `public/apple-touch-icon.png` (180×180) och `public/delningsbild.png` (1200×630).
4. Bilder i `src/assets/` och `<Image>` från `astro:assets` (WebP, width och height, srcset). Den största bilden i
   första vyn får `loading="eager"` och `fetchpriority="high"`. Typsnitt självhostade som WOFF2 i `public/fonts/`.
5. Strukturerad data: den mest specifika schema.org-typen (GeneralContractor, Electrician, HousePainter, Plumber,
   RoofingContractor …) som JSON-LD på startsidan, med uppgifter ur `VERKSAMHET.json`.
6. Skript och inline-händelser: CSP:n i `astro.config.mjs` släpper bara skript som Astro har hashat. Skriv skript
   som `<script>` i komponenten, aldrig `onclick=""`. Stilattribut (`style=""`) går bra.
7. `npm install` en gång, sedan `npm run build`. Provet bygger själv: `.venv/bin/python kontroller/prova.py <slug>`.

Demon skyddas vid driftsättning (lösenord och `X-Robots-Tag: noindex` som svarshuvud), aldrig med noindex i HTML:
då blir SEO-kontrollen och Lighthouse missvisande.
