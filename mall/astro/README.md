# Mall: Astro, statisk

Kopieras till `kunder/<slug>/sajt/` i steg 5. Den bär bara teknik: språk, canonical, theme-color, favicon,
delningsbild, skiplänk, CSP, dämpad rörelse (`prefers-reduced-motion`), sitemap.xml, robots.txt, 404, två
komponenter utan utseende (förfrågan och brödsmulor) och en tom `src/styles/design.css` som designkontraktet fyller.
Ingen design, inga typsnitt. Allt synligt skrivs för verksamheten. Byggstandarden som provet prövar står i `kunskap/byggstandard.md`.

1. Byt `site` i `astro.config.mjs` mot verksamhetens domän (ur `VERKSAMHET.json`, fältet `webb.doman`).
2. Skriv sidorna i `src/pages/` med `Bas.astro`: `titel` (50–60 tecken), `beskrivning` (120–155), `tema`
   (verksamhetens bärande färg som hex). Varje sida har `<header>` med `<nav>` och telefonnumret som tel-länk,
   `<main id="innehall">`, en h1 och `<footer>`. Skriv om `404.astro` med samma sidhuvud och sidfot.
3. Skapa `public/favicon.svg` ur verksamhetens märke. Kör sedan
   `node kontroller/ikoner.mjs --sajt kunder/<slug>/sajt --foto <eget foto> --bakgrund '<hex>'`, som gör
   `public/apple-touch-icon.png` (180×180) och `public/delningsbild.png` (1200×630).
4. Bilder i `src/assets/` och `<Image>` från `astro:assets` (WebP, width och height, srcset). Den största bilden i
   första vyn får `loading="eager"` och `fetchpriority="high"`. Typsnitt med Astros typsnitts-API: woff2-filen
   (latin-subset, bara axlarna som används) i `src/assets/fonts/`, blocket `fonts` i `astro.config.mjs` (exemplet står
   bortkommenterat), `import { Font } from 'astro:assets'` och `<Font cssVariable="--typsnitt" preload />` i head, och
   `font-family: var(--typsnitt)` i CSS:en. API:t skriver @font-face, preload och ett reservtypsnitt med size-adjust
   uträknat ur filen, så att texten inte hoppar (standarden 4.3).
5. Skriftlig förfrågan: `src/components/Forfragan.astro` på kontaktsidan, `src/pages/tack.astro` (noindex) och en
   integritetssida, enligt `kunskap/forfragan.md`. Provets och dashboardens server tar emot inskicket i demon.
6. Brödsmulor på varje undersida: `<Brodsmulor sida="Tillbyggnad" />`, eller med `steg` för en sida under en
   översikt, mellan sidhuvudet och `<main>`. Komponenten ger synlig "Du är här" och BreadcrumbList; utseendet
   skrivs för verksamheten.
7. Strukturerad data: den mest specifika schema.org-typen (GeneralContractor, Electrician, HousePainter, Plumber,
   RoofingContractor …) som JSON-LD på startsidan, med uppgifter ur `VERKSAMHET.json`.
8. Skript och inline-händelser: CSP:n i `astro.config.mjs` släpper bara skript som Astro har hashat. Skriv skript
   som `<script>` i komponenten, aldrig `onclick=""`. Stilattribut (`style=""`) går bra.
   En länk på egen rad i källan klistras ihop med texten runt ("på<a", "</a>eller"): skriv `{' '}` före och
   efter länken, eller håll den på samma rad som texten; byggstandarden 9.4 prövar det.
9. Designen: skriv `DESIGN.md` i sajtens rot (kontraktet i `kunskap/bygge-referens.md`) och kör
   `.venv/bin/python kontroller/design.py <slug> --skriv`, som gör `src/styles/design.css` med CSS-variablerna
   (`Bas.astro` importerar den). Sidornas CSS använder variablerna (`var(--farg-…)`, `var(--typ-…)`); provets grind
   `design` kräver att filen är genererad ur den aktuella DESIGN.md och att variablerna används.
10. `npm install` en gång, sedan `npm run build`. Provet bygger själv: `.venv/bin/python kontroller/prova.py <slug>`.

Demon skyddas vid driftsättning (lösenord och `X-Robots-Tag: noindex` som svarshuvud), aldrig med noindex i HTML:
då blir SEO-kontrollen och Lighthouse missvisande.
