# Byggstandard för småföretagssajter (praxis 2026)

Ägarens byggstandard (inklistrad 2026-10-02), anpassad till vår stack: statisk Astro, formulär vars inskick tas
emot av en demomottagare som inte sparar eller skickar något, ingen driftsättning förrän ägaren startar den. Varje punkt går att verifiera i webbläsaren (W) eller i koden
(K). Teorin och metoderna bakom punkterna står i `kunskap/teoretisk-grund.md`.

**Fas.** **D** gäller varje bygge och prövas innan bygget får avslutas. **L** gäller lanseringen och prövas först när
en sajt ska ut på riktigt; i demon står den som underlag.

**Prövas av.** `standard` är grinden `kontroller/standard_kontroll.py` i provet. `seo`, `axe`, `lighthouse`, `spill`,
`utan-js`, `design` och `resor` är provets övriga grindar. *info* betyder att provet rapporterar utan att stoppa. *granskaren* betyder
att den oberoende granskaren (`kritik/GRANSKARE.md`) bedömer det med egna ögon.

Rättelser mot originalet, med källa, står sist.

## 0. Principer

Mobilen först. Mindre JavaScript: innehåll och navigation fungerar utan JS. Allt mäts före lansering. Sajten ska
sälja: varje sida har ett tydligt nästa steg.

## 1. Grund och arkitektur (K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 1.1 Innehållssidor förrenderas; ingen klientrenderad text. Vi bygger helt statiskt (`output: 'static'`). | D | `bygge`, `utan-js` |
| 1.2 Låst lockfile, Node LTS. TypeScript strict och linter när sajten får egen kod utöver sidor. | D/L | mallen |
| 1.3 Hemligheter bara i miljön på servern, aldrig i klientkoden. Demon har inga hemligheter. | D | `prelaunch` (info) |
| 1.4 En gren per ändring, förhandsvisning per ändring, main är produktion, förhandsvisningen har noindex som svarshuvud. | L | Cloudflare-steget (`lansering.md`) |
| 1.5 Få beroenden; säkerhetspatchar inom en vecka, uppdateringsrunda varje månad. | L | drift |
| 1.6 README: stack, miljövariabler, driftsättning, DNS, vart formulärmejl går, vem som äger domän och konton; och en sida till verksamheten, Så ändrar du på sajten: vad som kan ändras utan ny beställning, hur man ber om det, svarstid, vem som äger domän och konton, i kundens ord utan tekniska termer. | L | lansering (`lansering.md`) |

## 2. HTML och semantik (W+K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 2.1 Landmärkena header, nav, main och footer på varje sida; exakt en h1; rubriknivåer utan hopp. | D | `standard`, `seo` |
| 2.2 Knapp är `<button>`, länk är `<a href>`; inga klickhändelser på div eller span, inga inline-händelser. | D | `standard` |
| 2.3 `lang="sv"`, viewport, unik title och description, favicon som SVG och 180×180 px apple-touch-icon, theme-color. | D | `standard`, `seo` |
| 2.4 Alt-text (tom för dekor), width och height på varje bild, lazy under första vyn; den största bilden i första vyn laddas direkt med `fetchpriority="high"`. | D | `standard`, `seo`, info |
| 2.5 Giltig HTML, prövad lokalt med html-validate. | D | `standard` |

## 3. CSS och design (W+K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 3.1 Designtokens för färg, typografi, avstånd och radie som CSS-variabler; en typografisk skala, ett avståndssystem. Stilrapporten visar typsnitt, färgfamiljer, radier, kort och modellernas namngivna standardval. | D | granskaren, stilrapporten (info) |
| 3.2 Mobilen först (min-width), flex och grid. Flytande typografi med clamp() blandar rem och cqi mot sidans omslag, som är en storleksbehållare (`container: omslag / inline-size`), så att texten slutar växa där omslaget slutar; vw bara utan ett omslag med maxbredd, och aldrig ensamt (zoom). | D | info, granskaren |
| 3.3 Ingen horisontell skroll mellan 320 och 1920 px. Träffytor minst 24×24 px, också länkar i listor och sidfot (WCAG 2.2 AA, 2.5.8; mätningen undantar länkar i löpande text men räknar inte kriteriets avståndsundantag, så den är strängare). Primära interaktiva kontroller minst 44×44 CSS-pixlar (Nortropics produktkrav, `kunskap/designregler.md`; inte WCAG:s minimum och inget krav på alla länkar). Fasta och klibbiga element bara i vyer minst 500 px höga (`@media (min-height: 31.25rem)`); i lägre vyer (400 % zoom, WCAG 1.4.10) står de i flödet. Sidan skrollar i rotskrollaren: html och body får ingen fast höjd med overflow; spill i sidled döljs med `overflow-x: clip`, inte `hidden`; `min-height: 100svh`, aldrig `height: 100vh`. | D | `spill`, `axe`; 24 px: `standard` (fel, mätt av stilrapporten); 44 px: stilrapporten listar knappar och ring-/mejllänkar under 44 px som information, granskaren avgör vilka som är primära |
| 3.4 Kontrast 4,5:1 för text (3:1 från 24 px, eller 18,66 px fet) och 3:1 för gränssnittets delar och fokusringen mot angränsande färger (WCAG 1.4.3, 1.4.11). Text och dess bakgrund har färdiga färgvärden (hex eller `oklch()`), inte `color-mix()`: axe ger då bara "incomplete" och grinden släpper igenom för svag text (mätt med axe-core 4.13.0, 2026-10-12). Synlig fokus med `:focus-visible` på varje Tab-stopp i 390 och 1440 (2.4.7), ringen minst 2 CSS-px (praxis ur 2.4.13, AAA). Knappar och primära länkar har synligt skilda lägen i vila, hovring, fokus och nedtryckt. | D | `axe`, designfasens rendering (fokus för de tio första tabbstegen; information), inspektionen, granskaren |
| 3.5 Rörelse (WCAG 2.2.2: rörelse som pågår mer än 5 s kan pausas eller stoppas, också marquees och loopar; 2.3.1; tekniken C39; ägarbeslutet mot karuseller). Med `prefers-reduced-motion: reduce` sker ingen förflyttning, skalning eller rotation vid laddning, skroll, hovring, fokus eller meny; opacitet och färg får stå kvar, så att ett tillståndsbyte fortfarande syns. Rörelse i skript (Motion, GSAP) läser preferensen och följer ett byte medan sidan är öppen (`gsap.matchMedia()`, `matchMedia`-lyssnare). Skrolldrivna CSS-animationer och övergångar mellan sidor står bara inom `@media (prefers-reduced-motion: no-preference)`, eftersom mallens återställning med 0,01 ms inte når dem (mätt 2026-10-12). Rörelse som startar när något skrollas in eller hovras räknas som automatisk start; ingenting på sidan förändras efter 5 s utan interaktion; ingen blinkning tre gånger per sekund eller oftare. Innehållet syns utan JS och utan att en animation körts (ingen text som börjar på `opacity: 0` i CSS). Återkommande banor (hovring, fokus, meny, skroll) animerar transform, opacity och färg, inte width, height, top, left, margin eller padding, och `transition: all` förekommer inte; `will-change` sätts bara medan något rör sig. Skrollningen följer webbläsaren (ingen skrollkapning). | D | `standard` (frasen), designfasens rendering (rörelse med och utan reducerad rörelse, förändring mellan 6 och 7 s; information), granskaren |
| 3.6 Ikoner som SVG, aldrig ikonfont. | D | `standard` |
| 3.7 Högst 200 kB JavaScript och 100 kB CSS per sida vid första rendering. | D | `standard` |
| 3.8 Webbläsarstöd: en funktion som är Baseline Widely available används utan reserv; Newly available bara som en förbättring som kan falla bort utan att något går sönder (text-wrap, view transitions inom samma dokument, `@starting-style`, popover, font-size-adjust) eller med en reserv; begränsat stöd aldrig för menyn, formuläret eller första vyn. Begränsat stöd 2026-10 (webstatus.dev, MDN): övergångar mellan dokument (`@view-transition`; Firefox saknar), skrolldrivna animationer (`animation-timeline`), `interpolate-size`/`calc-size()`, `popover="hint"` och `interestfor`; de får bara vara förbättringar i CSS, utan polyfill och utan Astros `<ClientRouter />`. Mallens faktiska golv är Safari och iOS 16.4 (Vite 8 och Tailwind 4 i låset). En meny med `popover` fungerar utan JS, men provverktygen läser `aria-expanded` eller `details`, så menyknappen har `aria-expanded`. Statusen kontrolleras mot MDN:s ruta för den egenskap som används, inte mot en guides egen rad (`.claude/skills/modern-web-guidance/`). | D | granskaren, WebKit-provet |

## 4. Prestanda (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 4.1 Labb: Lighthouse prestanda ≥ 90 i mobil och desktop, i mobil som median av tre mätningar på startsidan, kontaktsidan och den tyngsta övriga sidan (flest bilder i HTML:en), övriga mätningar en gång och under kravet tre (metoden i `prov/lighthouse/METOD.json`). Fält i mobil: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 vid 75:e percentilen (web.dev 2024-10-31, Search Central 2025-12-10; oförändrat 2026-10, och påståenden om en lägre INP-gräns saknar stöd i Googles källor). CrUX har bara data för sidor över en trafiktröskel som inte är offentlig, och bara från Chrome; saknas fältdata är labbet det enda beviset tills ägaren valt en fältmätning. | D labb, L fält | `lighthouse` |
| 4.2 Bilder i AVIF eller WebP, responsiva med srcset och sizes, rätt storlek; största bilden i första vyn under 200 kB; ingen publicerad bild bär GPS-läge i sin metadata (en personuppgift). | D | `standard`, info |
| 4.3 Typsnittsfamiljerna som den valda designen har (DESIGN.md; utan en godkänd DESIGN.md högst två), självhostade WOFF2 följda i stacken av ett reservtypsnitt med size-adjust, latin-subset med bara de axlar och vikter som används, sajtens typsnitt tillsammans högst 300 kB (en fil över 80 kB är information med råd; den verkliga prestandan prövar Lighthouse-grinden), `font-display: swap` med size-adjust-reserv, preload av typsnittet i första vyn. | D | `standard`, info |
| 4.4 Inga resurser från tredje part vid sidladdning; kartor som statisk bild och länk. | D | `standard` |
| 4.5 Hashade statiska filer med lång cache, CDN, kort cache för HTML. | L | Cloudflare-steget (`lansering.md`) |
| 4.6 Varje ändring mäts på förhandsvisningen; regression mot 4.1 stoppar. | L | Cloudflare-steget (`lansering.md`) |
| 4.7 Laddningen mätt i 390 och 1440 (Chromium): LCP-elementet läses ur PerformanceObserver; är det en bild har den `fetchpriority="high"`, ingen `loading="lazy"`, finns i HTML:en (inte en CSS-bakgrund eller insatt med JS) och har width och height. Högst två bilder per sida har `fetchpriority="high"`, och ingen lazy-bild har sin överkant i första vyn. Varje synlig bild över 64 px har en naturlig bredd på minst 0,75 × min(DPR, 2) × visad bredd (Lighthouse `image-size-responsive`). Layoutskiften under laddningen ≤ 0,05, halva fältgränsen som marginal (vår gräns). Lighthouse-insikterna lcp-discovery, image-delivery, unsized-images, non-composited-animations och bf-cache är godkända eller förklarade i rapporten. | D | designfasens rendering (LCP-kandidat, bildstorlekar, layoutskiften; information), `lighthouse`, granskaren |

## 5. Tillgänglighet, WCAG 2.2 AA (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 5.1 Allt går med tangentbord: skiplänk först, logisk tabbordning, inga fokusfällor, fokus döljs inte av klibbigt sidhuvud. | D | `standard`, inspektionen, granskaren |
| 5.2 Mobilmeny som disclosure (WAI-ARIA APG, Disclosure Navigation, 2026-01-20): en knapp med `aria-expanded` och `aria-controls`; vid öppning står fokus kvar på knappen och nästa Tab når första länken; Esc stänger och fokus står kvar på knappen; ingen `role="menu"`. En meny som täcker sidan (mer än halva vyn, eller bakgrunden dold) är en modal dialog: fokus in i dialogen, Tab stannar där, bakgrunden är `inert`, Esc stänger och fokus går tillbaka till knappen. Om menyn är dold eller synlig är riktningens val (designhypotes i `kunskap/designregler.md`). | D | designfasens rendering (`aria-expanded` efter klick), `axe` med menyn öppen, granskaren |
| 5.3 Länktexter begripliga utan sammanhang, även när de läses upp: "Ring 070-123 45 67", inte "Ring070-123 45 67"; ikonknappar har aria-label. | D | `axe`, `standard`, info |
| 5.4 Formulär: synliga etiketter ovanför fälten som ingår i fältets tillgängliga namn, `autocomplete` (`name`, `tel`, `email`; 1.3.5); fel i text som säger hur felet rättas (3.3.3), med `aria-invalid` och `aria-describedby` vid fältet; efter ett skick med fel går fokus till en felsammanfattning med länkar till fälten eller till första fel; giltiga värden står kvar efter serverns felsvar (3.3.7). | D om formulär | `axe` (med formuläret skickat tomt), granskaren |
| 5.5 Ingen autoplay med ljud (WCAG 1.4.2); inga karuseller (Nortropics ägarbeslut, inte ett WCAG-krav: WCAG kräver paus efter 5 s, 2.2.2). | D | `standard`, granskaren |
| 5.6 axe 0 allvarliga eller kritiska fel (serious, critical), också med menyn öppen och med formulärets felbesked framkallade. axe saknar regler för 2.4.7, 2.4.11, 1.4.10, 2.5.7, 3.2.6 och 3.3.7, så "axe utan fel" visar inte AA; de prövas med egna mätningar eller manuellt. Skärmläsarkoll av startsida och formulär görs av en människa före lansering, liksom en kontroll på riktig iPhone (provet kör WebKit, Safaris motor, men ingen riktig enhet); i demon läser granskaren tillgänglighetsträdet. | D axe, L skärmläsare och iPhone | `axe`, `resor`, granskaren |

| 5.7 Kontaktvägarna som återkommer på flera sidor (tel-länken, länken till formuläret) står i samma ordning i förhållande till sidhuvud, main och sidfot på alla sidor inom samma bredd (WCAG 3.2.6, nivå A). Var de står är riktningens val (9.2). | D | granskaren (en jämförelse av DOM-ordningen mellan sidorna är oprövad) |
| 5.8 Textavstånd: med radhöjd 1,5, styckeavstånd 2 em, teckenavstånd 0,12 em och ordavstånd 0,16 em klipps ingen text (1.4.12). Innehåll som visas vid hovring eller fokus går att avfärda med Esc och att föra pekaren över (1.4.13). Inget orienteringslås (1.3.4). En dragfunktion har ett alternativ med klick eller tryck (2.5.7). Ett fokuserat element är aldrig helt dolt av klibbigt innehåll (2.4.11). Reflow i 320 utan sidledsspill (1.4.10). | D | designfasens rendering (reflow 320; information), `spill`, granskaren; textavstånd, hovringsinnehåll och dragning manuellt |

## 6. Formulär (W+K)

Varje sajt har en skriftlig förfrågningsväg utöver telefonen (ägarens ord 2026-10-02 om alla sajter, `kunskap/forfragan.md`). Formuläret, tacksidan och
integritetssidan byggs i demon; mottagaren med mejl och spamspärr kommer vid lansering. Kontraktet står i
`kunskap/forfragan.md`.

| Punkt | Fas | Prövas av |
|---|---|---|
| 6.1 Ett formulär med få fält (namn, telefon, vad besökaren vill ha hjälp med, valfri bild); det valfria märks, resten krävs. Telefonen får inte vara enda vägen. Telefonfältet har en hjälptext om varför och när ni ringer, och bildfältet typ och storlek före valet (GOV.UK, Telephone numbers och File upload; mallens `telefonHjalp` och `bildHjalp`). | D | `standard`, granskaren |
| 6.2 `type="tel"`, inputmode, autocomplete och `pattern` (bokstäver går inte igenom); svenska felmeddelanden som text vid fältet med `aria-describedby`, inte bara webbläsarens bubbla (WCAG 3.3.1). | D | `standard`, `axe` |
| 6.3 Vanlig POST till `/api/forfragan/` fungerar utan JS; knappen låses under sändning; tacksidan säger vad som händer härnäst och när, och ger en kontaktväg om det brådskar (GOV.UK, Confirmation pages). | D formulär och tacksida, L mottagare | `standard`, demomottagaren |
| 6.4 Servern validerar allt igen, begränsar längd, escapar i mejlmallen. | L | lansering |
| 6.5 Spamskydd i lager: honeypot och tidsfälla i formuläret; rate limit och Turnstile i mottagaren. | D fällor, L resten | `standard`, lansering |
| 6.6 Inskicket sparas före sändning och gallras efter integritetssidans lagringstid; transaktionsmejl med SPF, DKIM och DMARC; "skickat" först när mejlet accepterats. Mottagningsbeskedet skiljer bekräftad lagring från okänd avisering; utan lagringskvitto påstås aldrig mottaget. Återhämtning och svar följer `kunskap/forfragan.md`, Vid lansering; mottagen-sidan (sparad, ej aviserad) är förrenderad och nås med 303, aldrig som svar på POST-adressen. | L | lansering |
| 6.7 Tacksidan `/tack/` med noindex; konverteringshändelse vid lansering. | D sida, L händelse | `standard` |
| 6.8 Integritetstext med länk vid knappen, integritetssida med ansvarig, ändamål, rättslig grund, lagringstid, rättigheter och kontakt; ingen förikryssad ruta. | D | `standard`, granskaren |

## 7. SEO och lokal synlighet (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 7.1 Unik, beskrivande title och relevant description, canonical, delningsbild `og:image` 1200×630 px. Metadata har ingen fast teckengräns; längdmätningen är information. | D | `seo`, `standard`, info |
| 7.2 sitemap.xml utan sidor med noindex (tacksidan) och robots.txt som inte blockerar CSS eller JS, 404-sida med väg vidare och noindex men ingen canonical, 301 från gamla adresser, ingen noindex i produktion utom på 404. | D, 301 L | `standard`, `seo` |
| 7.3 JSON-LD som matchar synligt innehåll (LocalBusiness kräver `address` enligt Google, Search Central 2026-09-08: utan publik adress, som hos ett serviceområdesföretag, ger märkningen inget Local Business-resultat men skadar inte): den mest specifika typen (Electrician, Plumber, RoofingContractor, HousePainter, GeneralContractor för snickare och byggare); BreadcrumbList bara med synliga brödsmulor, och när DESIGN.md:s struktur har brödsmulor (`"struktur": {"brodsmulor": true}`) finns båda på varje indexerbar undersida, mellan sidhuvudet och `<main>`. Brödsmulor är en designhypotes, inget krav. aggregateRating ur Google-omdömen ger inga rikresultat. Typer och egenskaper finns i schema.org:s vokabulär och hör till typen; en utgången term byts mot sin ersättare. | D | `standard`, `seo` (vokabulären), info |
| 7.4 Namn, adress och telefon identiska med Google-företagsprofilen; den gatuadress verksamheten själv visar, och som ingen annan källa motsäger, står på kontaktsidan och i JSON-LD (var den står i övrigt, till exempel sidfoten, är riktningens val); säger källorna olika står adressen ingenstans förrän verksamheten svarat; öppettider eller telefontid och serviceområde som text, eller beställda; länk till omdömena. | D | `seo`, `standard` (adressen), steg 6, granskaren |
| 7.5 En sida per huvudtjänst med egen h1, lokal koppling, riktiga jobbilder och nästa steg. | D | granskaren |
| 7.6 robots.txt blockerar inte sökrobotar, inte heller AI-sök, om kunden vill synas där, och sidor som ska synas har inget `nosnippet` eller `max-snippet:0`. llms.txt behövs inte (Googles guide om AI-funktioner i Sök, uppdaterad 2026-07-10, läst 2026-10-03; `kunskap/seo.md`, Generativ AI i Google Sök). | D | info |

## 8. Säkerhet och integritet (W+K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 8.1 HTTPS, HSTS, omdirigering till en kanonisk värd. | L | Cloudflare-steget (`lansering.md`) |
| 8.2 CSP: i demon som metatagg med hashar (Astro `security.csp`, se mallen); skript bara med hash, stilattribut tillåtna. Vid lansering som svarshuvud med frame-ancestors, plus nosniff, Referrer-Policy och Permissions-Policy. | D meta, L huvuden | `standard`, `prelaunch` |
| 8.3 API-vägar: bara avsedd metod, validerad indata, ingen öppen CORS. | L | lansering |
| 8.4 npm audit utan kända sårbarheter i produktion. | L | lansering |
| 8.5 Inga icke-nödvändiga kakor före samtycke; helst kakfri analys utan banner. | D, L | `standard` (inga tredjepartsresurser), juridik |
| 8.6 Integritetspolicy med ansvarig, ändamål, rättslig grund, lagringstid, rättigheter och kontakt. | L | lansering |
| 8.7 Inga fel i webbläsarens konsol och inga sidfel på någon sida i provets vyer: en CSP-överträdelse, ett skript, typsnitt eller en bild som inte laddas syns där. Typsnittsfiler bäddas inte in som data:-adresser (mallens `astro.config.mjs`). | D | `standard` (ur provets inspektion) |

## 9. Innehåll och konvertering (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 9.1 Första vyn säger vad, var, för vem och nästa steg. Ingen karusell. | D | femsekunderstestet, granskaren |
| 9.2 Nästa steg på varje indexerbar sida (tel-länk, formulär eller länk till kontaktvägen), med kundens kontaktvägar ur BRIEF.md §4: har kontaktmodellen telefonen finns numret som tel-länk på varje sida. Var vägarna står (sidhuvud, list, sektion) är riktningens val. | D | `standard` |
| 9.3 Förtroende: omdömen med källa, referensjobb med egna bilder, F-skatt, försäkring, certifikat, org.nr i sidfoten, ROT eller RUT där det gäller. Bara det som är belagt; det som saknas beställs av verksamheten (`underlag/<slug>/BESTALLNING.md`), minst fem egna bilder eller en beställning. | D | `standard` (bilderna), granskaren |
| 9.4 Konkret, aktiv text på kundens språk; inga platshållare eller kvarlämnade kastbara sidor (`/tvaan/`), inga meningar som löper ihop utan mellanslag ("förfrågan.Så"), inga stockbilder där egna finns, rätt årtal. | D | copykontrollen, `standard` (`/tvaan/`, mellanslag), granskaren |
| 9.5 Varje sida svarar på en fråga kunden faktiskt har: pris, tid, område eller process. | D | granskaren |

## 10. Analys, drift och lanseringsgrind (W+K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 10.1 Konverteringsmål (formulär skickat, telefonklick); sökkonsolen och företagsprofilen verifierade. | L | lansering |
| 10.2 Driftkoll, felövervakning, månatlig patchrunda, säkerhetskopia. | L | drift |
| 10.3 Definition of Done för lansering: alla W-punkter verifierade i produktion, Lighthouse prestanda ≥ 90 i mobil, axe 0 allvarliga eller kritiska fel och skärmläsarkollen gjord, säkerhetshuvuden på A-nivå, formuläret prövat hela vägen med mottaget mejl, noindex borta, sitemap inskickad, 301:or på plats. | L | lanseringsgrinden |

## 11. Astro i stället för Next.js

Originalets avsnitt om Next.js gäller inte vår stack. Motsvarigheterna i Astro: statiska sidor; `astro:assets` och
`<Image>` för bilder (width, height, WebP och srcset); självhostade typsnitt i `src/assets/fonts/` med Astros typsnitts-API (`fonts` i `astro.config.mjs`, `<Font preload />`), som ger reserv med size-adjust och preload; metadata i layouten;
`sitemap.xml.ts` och `robots.txt.ts` i mallen; CSP med `security.csp`. Formulär, säkerhetshuvuden och mätning på
förhandsvisningen hör till Cloudflare-steget (`kunskap/lansering.md`).

## Rättelser mot originalet (kontrollerade 2026-10-02)

- **FAQPage ger inga rikresultat.** Google slutade visa dem 7 maj 2026 och Rich Results Test prövar dem inte längre.
  Markeringen skadar inte men ger inget i Google.
  [Google](https://developers.google.com/search/docs/appearance/structured-data/faqpage)
- **clamp() måste blanda rem och en flytande enhet.** Med bara vw växer texten inte vid zoom och bryter WCAG 1.4.4.
  [Smashing Magazine](https://www.smashingmagazine.com/2023/11/addressing-accessibility-concerns-fluid-type/)
- **clamp() med vw växer förbi omslaget.** vw mäter mot fönstret: Holms h1 nådde sitt max vid 1 375 px fast omslaget
  stannade vid 1 152 px (aby 1 250 mot 1 200), och provets vyer 390/768/1440 ser inte glappet. cqi i en storleksbehållare
  (`container: omslag / inline-size` på omslaget) mäter mot omslaget; rem kvar för zoomen. `@property` (syntax `<length>`,
  `inherits: true`, satt om på omslagets direkta barn) bara när ett bygge inför container queries på kort.
  [Kevin Powell, Fixing fluid typography](https://www.youtube.com/watch?v=q-_cIlttYBc) (kirurgens intag 2026-10-04)
- **CSP med nonce kräver en server.** Statiska Astro-sajter har inbyggd CSP med hashar sedan Astro 6; vi kör 7.
  frame-ancestors fungerar inte i en metatagg och kommer med svarshuvudena vid lansering.
  [Astro 6](https://astro.build/blog/astro-6/)
- **Snickare saknar egen typ i schema.org.** Närmast är GeneralContractor; HousePainter, Electrician, Plumber och
  RoofingContractor finns. [schema.org](https://schema.org/HomeAndConstructionBusiness)
- **LCP 2,5 s gäller fortfarande** enligt [web.dev](https://web.dev/articles/lcp).
- **llms.txt behövs inte** för Googles AI-funktioner, och att blockera Google-Extended påverkar inte AI Overviews.
- **Tillgänglighetslagen (2023:254) undantar mikroföretag som tillhandahåller tjänster**: färre än tio anställda och
  omsättning eller balansomslutning högst två miljoner euro. Lagen gäller vissa konsumenttjänster, för våra kunder
  främst e-handelstjänster; om en informationssajt med offert- eller bokningsformulär räknas dit är inte verifierat.
  Lagen om tillgänglighet till digital offentlig service (2018:1937) jämställer privata utförare inom skola, hälso- och
  sjukvård, tandvård och socialtjänst med offentliga aktörer, oavsett storlek (tillgänglighetsredogörelse). För de
  flesta av våra hantverkare är WCAG 2.2 AA ett kvalitetskrav, inget lagkrav; briefen frågar efter storlek, försäljning
  på nätet och offentlig finansiering. EN 301 549 V4.1.1 (WCAG 2.2) publicerades 2026-09-02 men var inte citerad i EUT
  2026-10-12. (Kontrollerat 2026-10-12.)
  [PTS](https://pts.se/digital-inkludering/lagen-om-vissa-produkters-och-tjansters-tillganglighet/vanliga-fragor-och-svar-om-tillganglighetslagen/),
  [ETSI](https://www.etsi.org/deliver/etsi_en/301500_301599/301549/)
- **WCAG 3 är ett arbetsutkast** (2026-09-10) och ställs inte som krav; W3C: uppfyll WCAG 2.2 nu. WCAG-EM 2.0 (Group Note
  2026-07-23) låter en sajt med få sidor prövas hel i stället för med urval. [W3C](https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/)
- **Övergångar mellan dokument har begränsat stöd**: bara övergångar inom samma dokument är Baseline Newly (2025-10-14);
  `@view-transition` saknas i Firefox (webstatus.dev, 2026-10-12).
