# Prelaunch — åtta grindar före lansering, som rapport med belägg

Ärvd från Digitala. Verktyg: `kontroller/prelaunch.py`, som provet (`kontroller/prova.py`) kör som information i
varje bygge (`prov/prelaunch.md`). Grind 2–4 avgörs i vårt flöde av provets egna grindar (lighthouse, spill, axe;
byggstandarden), inte av prelaunch: verktyget väntar sig ett mätkvitto i Runtimes format, som inte finns här, och
skriver därför EJ_MATT för dem med beskedet att provets grind avgör. Grind 0, 5 och 6 läses ur prelaunch,
grind 7 vid lansering med `--adress` mot den riktiga domänen. Varje grind får PASS, FAIL, EJ_MATT eller MANNISKA;
EJ_MATT är inte PASS; verktyget godkänner aldrig juridik. Gröna verktygsprov bevisar inte mänsklig användbarhet eller
affärsresultat.

| Grind | Vad som prövas | Belägg |
|---|---|---|
| 0 byggintegritet | bygget finns och renderar; inga platshållare (lorem ipsum, TODO-markörer, `[OSÄKER]`); inga hemligheter i bygget; `.env.example` dokumenterar miljövariabler | bygget, repot |
| 1 viktiga handlingar | varje handling ur briefen §4 prövad från början till slut (formulär → leverans till mottagare; länk → samtal; bokning → extern tjänst nådd); felväg visar alternativ | `HANDLINGAR.json` med provkvitton (manuellt prov med datum; inget formulär skickas på riktiga sajter) |
| 2 prestanda | Lighthouse per vy ur mätningens körkatalog (sämsta vyn gäller) mot kravnivån i briefen (standard: prestanda ≥ 90, tillgänglighet, best practices, SEO ≥ 95), LCP < 2,5 s, CLS < 0,1; i förhandsvisning (noindex) redovisas SEO-poängen men avgör inte — SEO-beredskapen prövas av grind 5 mot avsett läge; INP mäts inte av navigations-Lighthouse (EJ_MATT tills fältdata); en mätning som inte är klar ger EJ_MATT | provets grind lighthouse (`prov/lighthouse/`); prelaunch skriver EJ_MATT |
| 3 responsivitet | vyerna ur mätprofilen; horisontell spill per vy ur webbläsarverktygets inspektion (`--inspektion INSPEKTION.json`; inspektionen körs med de vyer fallet väljer, standard 390 och 1440, och mäter scrollWidth mot clientWidth — prelaunch läser spill-flaggan per vy); layout bedömd i skärmbilder | provets grind spill (`prov/inspektion/`) + skärmbilder |
| 4 tillgänglighet | axe utan violations i varje vy; manuella kontroller (tangentbord, fokus, kontrast, alt, formulärfel, rörelse) | provets grind axe (`prov/axe/`) + manuell notering |
| 5 SEO-beredskap | `seo_kontroll.py` utan fynd i rätt läge (förhandsvisning: noindex; lansering: index) | SEO-rapporten |
| 6 juridik | basen och satta flaggor (juridikflaggor.md); rapporteras, avgörs av människa | `JURIDIK.json` + människans beslut |
| 7 säkerhet | säkerhetsrubriker (CSP med frame-ancestors, HSTS, nosniff, Referrer-Policy), beroenden utan high/critical (`npm audit`), formulärskydd (formularsakerhet.md), inga nycklar i bunten | svarshuvuden (sparade eller live), auditfil |

Helheten är "redo" bara när grind 0–5 och 7 är PASS, JURIDIK.json är lämnad (människans genomgång av basen och
flaggorna) och juridiken saknar ohanterade flaggor. Ett underkännande
går till diagnos → åtgärd → omprov av den berörda grinden (stoppvaktens loop i bygget), inte till ett ägarstopp.

## Kompletteringar i verktyget (2026-09-30, ärvda från Digitala)

- Grind 2 visar `tbt_ms` per mätning, med sämsta vy och en anmärkning över 200 ms.
  [web.dev](https://web.dev/articles/tbt), läst 2026-09-30, beskriver TBT som en
  labbproxy som kan både missa och överindikera INP-problem. INP förblir EJ_MATT.
  `STANDARDKRAV.tbt_faller` är `false`: signalen fäller inte ensam grinden.
  En motiverad uppgift kan ange `true` i kravfilen; gränsen anges med `tbt_ms`.
- Grind 6 visar LPTT vid e-handel mot konsument och modellfria fynd ur kundbyggets
  `bilder/TYPSNITT-IKONER.json` (bild.md). Juridik avgörs fortfarande av människa.
- Grind 7 kontrollerar varje rutt i byggets sitemap:
  `urlset` med sidornas `url/loc`; bilders `loc` är inte sidrutter. Sitemapindex
  stöds inte här och ger EJ_MATT tills sidrutterna lämnats som urlset.
  Vid live-kontroll används måladressens ursprung och sitemapens sökvägar. Sparade huvuden för flera rutter
  anges som `{"rutter":{"/":{"content-security-policy":"…"},"/kontakt/":{…}}}`.
  En enda äldre textfil belägger endast en sajt med en sitemaprutt. Saknad mätning
  är EJ_MATT; saknad CSP eller för svag policy är FAIL med ruttpekare.
  [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP), omläst
  2026-09-30, ligger bakom kontrollen av `object-src`, `base-uri` och `unsafe-inline`
  i skriptdirektiv utan nonce/hash. Det är en avgränsad kontroll, ingen fullständig
  säkerhetsrevision av en CSP.
- HTML-prov utan JavaScript körs enligt webblasare.md; UTAN-JS.json bifogas
  handlings-/QA-underlaget. EJ_MATT vid uteblivet formulärinskick får inte beskrivas
  som ett fungerande formulär. Inget verkligt kundformulär skickas utan mandat.
