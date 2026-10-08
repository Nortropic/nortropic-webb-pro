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
| 1.4 En gren per ändring, förhandsvisning per ändring, main är produktion, förhandsvisningen har noindex som svarshuvud. | L | Vercel-steget (`lansering.md`) |
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
| 3.3 Ingen horisontell skroll mellan 320 och 1920 px; träffytor minst 24×24 px, primära knappar 44×44. Länkar i listor och sidfot räknas, inte bara knappar. | D | `spill`, `axe`; 24 px: `standard` (fel, mätt av stilrapporten); 44 px: stilrapporten listar knappar och ring-/mejllänkar under 44 px som information, granskaren avgör vilka som är primära |
| 3.4 Kontrast 4,5:1 för text och 3:1 för gränssnitt; synlig fokus med `:focus-visible`. | D | `axe`, inspektionen, info |
| 3.5 `prefers-reduced-motion` respekteras när sidan har rörelse, också övergångar (mallens `Bas.astro` har blocket); inget rullar av sig självt. | D | `standard` |
| 3.6 Ikoner som SVG, aldrig ikonfont. | D | `standard` |
| 3.7 Högst 200 kB JavaScript och 100 kB CSS per sida vid första rendering. | D | `standard` |

## 4. Prestanda (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 4.1 Labb: Lighthouse prestanda ≥ 90 i mobil och desktop, i mobil som median av tre mätningar på startsidan, kontaktsidan och den tyngsta övriga sidan (flest bilder i HTML:en), övriga mätningar en gång och under kravet tre (metoden i `prov/lighthouse/METOD.json`). Fält i mobil: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 vid 75:e percentilen. | D labb, L fält | `lighthouse` |
| 4.2 Bilder i AVIF eller WebP, responsiva med srcset och sizes, rätt storlek; största bilden i första vyn under 200 kB; ingen publicerad bild bär GPS-läge i sin metadata (en personuppgift). | D | `standard`, info |
| 4.3 Typsnittsfamiljerna som den valda designen har (DESIGN.md; utan en godkänd DESIGN.md högst två), självhostade WOFF2 följda i stacken av ett reservtypsnitt med size-adjust, latin-subset med bara de axlar och vikter som används, sajtens typsnitt tillsammans högst 300 kB (en fil över 80 kB är information med råd; den verkliga prestandan prövar Lighthouse-grinden), `font-display: swap` med size-adjust-reserv, preload av typsnittet i första vyn. | D | `standard`, info |
| 4.4 Inga resurser från tredje part vid sidladdning; kartor som statisk bild och länk. | D | `standard` |
| 4.5 Hashade statiska filer med lång cache, CDN, kort cache för HTML. | L | Vercel-steget (`lansering.md`) |
| 4.6 Varje ändring mäts på förhandsvisningen; regression mot 4.1 stoppar. | L | Vercel-steget (`lansering.md`) |

## 5. Tillgänglighet, WCAG 2.2 AA (W)

| Punkt | Fas | Prövas av |
|---|---|---|
| 5.1 Allt går med tangentbord: skiplänk först, logisk tabbordning, inga fokusfällor, fokus döljs inte av klibbigt sidhuvud. | D | `standard`, inspektionen, granskaren |
| 5.2 Mobilmeny: aria-expanded, stängs med Esc, fokus in och tillbaka. Helst ingen gömd meny när punkterna ryms. | D | granskaren |
| 5.3 Länktexter begripliga utan sammanhang, även när de läses upp: "Ring 070-123 45 67", inte "Ring070-123 45 67"; ikonknappar har aria-label. | D | `axe`, `standard`, info |
| 5.4 Formulär: kopplade etiketter, fel i text, aria-describedby eller aria-live för fel. | D om formulär | `axe`, granskaren |
| 5.5 Ingen autoplay med ljud; inga karuseller. | D | `standard`, granskaren |
| 5.6 axe 0 allvarliga fel, också med menyn öppen och med formulärets felbesked framkallade. Skärmläsarkoll av startsida och formulär görs av en människa före lansering, liksom en kontroll på riktig iPhone (provet kör WebKit, Safaris motor, men ingen riktig enhet); i demon läser granskaren tillgänglighetsträdet. | D axe, L skärmläsare och iPhone | `axe`, `resor`, granskaren |

## 6. Formulär (W+K)

Varje sajt har en skriftlig förfrågningsväg utöver telefonen (ägarens ord 2026-10-02 om alla sajter, `kunskap/forfragan.md`). Formuläret, tacksidan och
integritetssidan byggs i demon; mottagaren med mejl och spamspärr kommer vid lansering. Kontraktet står i
`kunskap/forfragan.md`.

| Punkt | Fas | Prövas av |
|---|---|---|
| 6.1 Ett formulär med få fält (namn, telefon, vad besökaren vill ha hjälp med, valfri bild); det valfria märks, resten krävs. Telefonen får inte vara enda vägen. | D | `standard`, granskaren |
| 6.2 `type="tel"`, inputmode, autocomplete och `pattern` (bokstäver går inte igenom); svenska felmeddelanden som text vid fältet med `aria-describedby`, inte bara webbläsarens bubbla (WCAG 3.3.1). | D | `standard`, `axe` |
| 6.3 Vanlig POST till `/api/forfragan/` fungerar utan JS; knappen låses under sändning; tacksidan säger vad som händer härnäst och när. | D formulär och tacksida, L mottagare | `standard`, demomottagaren |
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
| 7.3 JSON-LD som matchar synligt innehåll: den mest specifika typen (Electrician, Plumber, RoofingContractor, HousePainter, GeneralContractor för snickare och byggare); BreadcrumbList bara med synliga brödsmulor, och när DESIGN.md:s struktur har brödsmulor (`"struktur": {"brodsmulor": true}`) finns båda på varje indexerbar undersida, mellan sidhuvudet och `<main>`. Brödsmulor är en designhypotes, inget krav. aggregateRating ur Google-omdömen ger inga rikresultat. Typer och egenskaper finns i schema.org:s vokabulär och hör till typen; en utgången term byts mot sin ersättare. | D | `standard`, `seo` (vokabulären), info |
| 7.4 Namn, adress och telefon identiska med Google-företagsprofilen; den gatuadress verksamheten själv visar, och som ingen annan källa motsäger, står på kontaktsidan och i JSON-LD (var den står i övrigt, till exempel sidfoten, är riktningens val); säger källorna olika står adressen ingenstans förrän verksamheten svarat; öppettider eller telefontid och serviceområde som text, eller beställda; länk till omdömena. | D | `seo`, `standard` (adressen), steg 6, granskaren |
| 7.5 En sida per huvudtjänst med egen h1, lokal koppling, riktiga jobbilder och nästa steg. | D | granskaren |
| 7.6 robots.txt blockerar inte sökrobotar, inte heller AI-sök, om kunden vill synas där. llms.txt behövs inte (Googles guide om AI-funktioner i Sök, uppdaterad 2026-07-10, läst 2026-10-03; `kunskap/seo.md`, Generativ AI i Google Sök). | D | info |

## 8. Säkerhet och integritet (W+K)

| Punkt | Fas | Prövas av |
|---|---|---|
| 8.1 HTTPS, HSTS, omdirigering till en kanonisk värd. | L | Vercel-steget (`lansering.md`) |
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
| 10.3 Definition of Done för lansering: alla W-punkter verifierade i produktion, Lighthouse prestanda ≥ 90 i mobil, axe 0 fel, säkerhetshuvuden på A-nivå, formuläret prövat hela vägen med mottaget mejl, noindex borta, sitemap inskickad, 301:or på plats. | L | lanseringsgrinden |

## 11. Astro i stället för Next.js

Originalets avsnitt om Next.js gäller inte vår stack. Motsvarigheterna i Astro: statiska sidor; `astro:assets` och
`<Image>` för bilder (width, height, WebP och srcset); självhostade typsnitt i `src/assets/fonts/` med Astros typsnitts-API (`fonts` i `astro.config.mjs`, `<Font preload />`), som ger reserv med size-adjust och preload; metadata i layouten;
`sitemap.xml.ts` och `robots.txt.ts` i mallen; CSP med `security.csp`. Formulär, säkerhetshuvuden och mätning på
förhandsvisningen hör till Vercel-steget (`kunskap/lansering.md`).

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
- **Tillgänglighetslagen (2023:254) undantar mikroföretag**, färre än tio anställda och högst två miljoner euro i
  omsättning. För våra hantverkare är WCAG 2.2 AA ett kvalitetskrav, inget lagkrav.
  [PTS](https://pts.se/digital-inkludering/lagen-om-vissa-produkters-och-tjansters-tillganglighet/vanliga-fragor-och-svar-om-tillganglighetslagen/)
