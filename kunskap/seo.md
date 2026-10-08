# SEO — sökintention, struktur, teknik och innehåll; inga rankningslöften

Professionsfil (HELHET-20260927, avsnitt 4 "SEO"), återvunnen och generaliserad ur det arkiverade repots lokala
SEO-skill. Laddas i steget `seo`. Metadata eller Lighthouse-SEO ensamt är ingen SEO-funktion; SEO-läget väljs i
briefen §5: `lokal`, `varumärke/portfölj`, `hybrid` eller `ingen`. Verktyg: `kontroller/seo_kontroll.py` (rapport).

## Sökintention och informationsstruktur

- Varje sida svarar på en sökavsikt ur research §15 (informations-, navigations-, transaktions- eller lokal
  avsikt); sidor utan genuint innehåll skapas inte ("fem verkliga sidor slår tjugofem spunna").
- Sidstruktur efter uppgifterna: tjänst per sida när tjänsterna söks var för sig; område per sida bara vid lokal
  räckvidd och genuint lokalt innehåll (verkliga arbeten, lokala förhållanden); frågor som kunder faktiskt ställer i
  ett FAQ-block på den sida de hör till.
- Intern länkning: start → tjänster; tjänst ↔ närliggande tjänst; område → tjänster; sidfot → områden och
  informationssidor; brödsmulor när djupet motiverar det.

## Teknisk SEO

- Crawlning och indexering: `robots.txt` med `Sitemap:`-rad; `sitemap.xml` ur sidorna; förhandsvisning bär
  `noindex` och `Disallow: /`, lanseringskonfigurationen tvärtom — de två hålls isär (lansering.md).
- Canonical absolut per sida; en kanonisk domänvariant (www eller apex), den andra omdirigerar 301.
- Metadata: unik `title` (omkring 60 tecken) och `description` (omkring 155) per sida, sanningsenliga, utan
  superlativ och utan ortstoppning; sociala metadata (Open Graph) med bild.
- `html lang`, en `h1` per sida, rubrikordning, alt-texter (bild.md), svenska filnamn på bilder.
- hreflang bara vid verkliga språkvarianter, bidirektionellt med `x-default`; ingen hreflang på enspråkig sajt.
- Omdirigeringar vid migrering: gamla adresser med trafik eller inkommande länkar får 301 till närmaste motsvarighet;
  listan prövas i förhandsvisning (`--omdirigeringar`).
- Prestanda och tillgänglighet är egna krav (bygge-referens.md); de mäts genom Runtimes mätprofil, inte här.

## Strukturerad data — bara sanning

- JSON-LD, ett skriptblock per objekt, serverrenderat. Typ efter verksamheten (`LocalBusiness`-undertyp bara vid
  lokal verksamhet; annars `Organization`, `Service`, `FAQPage`, `BreadcrumbList` efter innehåll).
- Fälten kommer ur `VERKSAMHET.json`: namn, telefon i E.164, adress bara när `adress.publik` är sann (annars
  `areaServed`), öppettider som på sajten, `priceRange` bara om pris anges; `aggregateRating` bara ur verklig
  plattformsdata med källa; `offers` bara vid verkligt fast pris.
- FAQ-frågor i schemat är samma som de synliga; inga platshållare får nå schemat.
- Validering: `seo_kontroll.py` prövar form och sanning mot verksamhetsuppgifterna; Googles Rich Results Test är en
  manuell kontroll efter lansering (extern).

## Innehållsmässig SEO

- Text som svarar på avsikten med kundens ord och verkliga uppgifter; ortnamn där de är sanna, aldrig som stoppning;
  interna länkar med beskrivande text; bilder med innehåll (bild.md); ingen text för sökmotorer som inte är för läsare.

## Generativ AI i Google Sök

Googles egen linje (guiden om optimering för generativ AI-sök, https://developers.google.com/search/docs/fundamentals/ai-optimization-guide,
publicerad 2026-05-15 och uppdaterad 2026-07-10; läst 2026-10-03 och 2026-10-08; den äldre sidan om AI-funktioner är
https://developers.google.com/search/docs/appearance/ai-features): "optimizing for generative AI search is optimizing for the
search experience, and thus still SEO"; GEO och AEO är samma sak som SEO, inte egna discipliner.
Samma grund gäller: genomsökbar, indexerbar, tydligt innehåll som svarar på avsikten med verkliga uppgifter.
llms.txt behövs inte, och inte heller särskild AI-märkning, uppstyckad text, omskrivning "för AI" eller sidor per
frågevariant; strukturerad data bara för rikresultat (Strukturerad data ovan). Sajten ska vara inkluderad i Googles
generativa AI-funktioner i Search Console (sokkonsol.md, Lanseringsdagen), och effekten läses i rapporten för generativ
AI (sokkonsol.md, Sökdata och tolkning). För lokala verksamheter pekar guiden på Google-företagsprofilen (och Merchant
Center för produkter) som vägen att synas både i AI-svaren och i vanliga sökresultat (lokal-synlighet.md; profilbladet i
rapportens punkt 14). AEO- och GEO-knep ur spaningens videor och artiklar tas inte in (kirurgens domar 2026-10-03).

## Vad SEO inte lovar

Ingen rankning, ingen indexering och inga positioner utlovas. Observationer efter lansering läses i sökkonsolen
(sokkonsol.md) och omsätts i innehålls- och strukturändringar (uppfoljning.md).
