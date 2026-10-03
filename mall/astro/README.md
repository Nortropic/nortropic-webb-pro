# Mall: Astro, statisk

Kopieras till `kunder/<slug>/sajt/` i steg 5. Den bär bara teknik: språk, canonical, theme-color, favicon,
delningsbild, skiplänk, CSP, dämpad rörelse (`prefers-reduced-motion`), sitemap.xml, robots.txt, 404, och två
komponenter utan utseende (förfrågan och brödsmulor). Ingen design, inga typsnitt. Allt synligt skrivs för verksamheten. Byggstandarden som provet prövar står i `kunskap/byggstandard.md`.

1. Byt `site` i `astro.config.mjs` mot verksamhetens domän (ur `VERKSAMHET.json`, fältet `webb.doman`).
2. Skriv sidorna i `src/pages/` med `Bas.astro`: `titel` (50–60 tecken), `beskrivning` (120–155), `tema`
   (verksamhetens bärande färg som hex). Varje sida har `<header>` med `<nav>` och telefonnumret som tel-länk,
   `<main id="innehall">`, en h1 och `<footer>`. Skriv om `404.astro` med samma sidhuvud och sidfot.
3. Skapa `public/favicon.svg` ur verksamhetens märke. Kör sedan
   `node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <eget foto> --bakgrund '<hex>'`, som gör
   `public/apple-touch-icon.png` (180×180) och `public/delningsbild.png` (1200×630).
4. Bilder i `src/assets/` och `<Image>` från `astro:assets` (WebP, width och height, srcset). Den största bilden i
   första vyn får `loading="eager"` och `fetchpriority="high"`. Typsnitt självhostade som WOFF2 i `public/fonts/`,
   vart och ett följt i stacken av ett reservtypsnitt så att texten inte hoppar när det laddats (standarden 4.3):
   `@font-face { font-family: "Familj reserv"; src: local(Arial); size-adjust: 102%; ascent-override: 96%;
   descent-override: 26%; }` och `font-family: "Familj", "Familj reserv", sans-serif`. Måtten räknas ur typsnittets
   x-höjd och teckenbredd mot reserven.
5. Skriftlig förfrågan: `src/components/Forfragan.astro` på kontaktsidan, `src/pages/tack.astro` (noindex) och en
   integritetssida, enligt `kunskap/forfragan.md`. Provets och dashboardens server tar emot inskicket i demon.
6. Brödsmulor på varje undersida: `<Brodsmulor sida="Tillbyggnad" />`, eller med `steg` för en sida under en
   översikt. Komponenten ger synlig "Du är här" och BreadcrumbList; utseendet skrivs för verksamheten.
7. Strukturerad data: den mest specifika schema.org-typen (GeneralContractor, Electrician, HousePainter, Plumber,
   RoofingContractor …) som JSON-LD på startsidan, med uppgifter ur `VERKSAMHET.json`.
8. Skript och inline-händelser: CSP:n i `astro.config.mjs` släpper bara skript som Astro har hashat. Skriv skript
   som `<script>` i komponenten, aldrig `onclick=""`. Stilattribut (`style=""`) går bra.
9. `npm install` en gång, sedan `npm run build`. Provet bygger själv: `.venv/bin/python kontroller/prova.py <slug>`.

Demon skyddas vid driftsättning (lösenord och `X-Robots-Tag: noindex` som svarshuvud), aldrig med noindex i HTML:
då blir SEO-kontrollen och Lighthouse missvisande.
