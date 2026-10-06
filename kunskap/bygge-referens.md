# Bygge — referens för produktion (val, inte fast stack)

Professionsfil (HELHET-20260927, avsnitt 4 "Produktion"), återvunnen ur det arkiverade repots stack- och initskills.
Läses i bygg-sajt steg 5 och i skapandeflödets förfining (`kunskap/metodkarta.md`). Ingen fast stack: valet motiveras i
briefen §9 av uppgiften, kundens förvaltning och driftmiljön. Det som följer är krav på resultatet och beprövade mönster.

## Krav på resultatet (oavsett stack)

- Semantisk HTML (landmärken, rubrikordning, listor, knappar som knappar, länkar som länkar); rätt `lang` för innehållets språk.
- Responsivt utan horisontell spill i 320–1920 px; layoutvyns bredd lika med fönstret på mobil.
- Tangentbord: allt nåbart och användbart; synligt fokus; hopp-länk; meny och dialoger stängs med Escape.
- Tillgänglighet WCAG 2.2 AA som krav (axe utan violations är nödvändigt, inte tillräckligt; manuella kontroller
  enligt `externa/addyosmani-accessibility-SKILL.md`).
- Prestanda: Core Web Vitals-mål (LCP < 2,5 s, CLS < 0,1, INP < 200 ms) på mobil; bilder med mått, AVIF/WebP,
  första vyns bild prioriterad; typsnitt med uppgiftsmotiverade roller och rimlig laddningskostnad, normalt självhostade; ingen tredjeparts-CDN för typsnitt.
- Säkerhet: säkerhetsrubriker (Content-Security-Policy, Strict-Transport-Security, X-Content-Type-Options,
  Referrer-Policy, frame-ancestors), inga hemligheter i klientbunten, servervalidering av varje formulärfält,
  formulärskydd enligt `formularsakerhet.md`, beroenden granskade (`npm audit` utan high/critical i produktion).
- Formulär: fält motiverade i briefen §4; fel-, tom- och laddningslägen; alternativ kontaktväg vid fel; leverans
  till mottagare ur miljövariabel (namn i briefen, aldrig värden i repot).
- Innehållsmodell efter behov: när kunden ska redigera själv, en innehållskälla (filer eller CMS) med dokumenterat
  redigeringsflöde; annars innehåll som data i repot, inte inbakat i komponenter.
- Sammanhängande övergångar och rörelse enligt briefens motion-nivå; `prefers-reduced-motion` respekteras alltid.
- Fel- och 404-sidor på aktuellt språk med fungerande nästa handling.
- **Layouten äger avståndet:** luften mellan delar sätts som `gap` på föräldern (stack, kluster, rutnät), inte som
  marginaler på barnen. Ett undantag skrivs på barnet, så att det syns i samma fil.
- **En skala för text och luft:** sektionsavstånd, radavstånd och rubrikstorlekar är steg ur samma bas och kvot,
  satta som CSS-variabler (byggstandarden 3.1), så att rytmen hänger ihop mellan sektionerna och inuti dem.
- **Varje del byter form vid sin egen tröskel:** container query eller `flex-basis` mot en bredd ur skalan, inte en
  brytpunkt för hela fönstret. Media queries används för besökarens preferenser (färgschema, rörelse, utskrift).
  Källa för de tre: Bell & Pickering (2019), Every Layout.

## Beprövade mönster (välj med skäl)

- **Statisk eller hybrid sajt** (t.ex. Next.js med statisk generering, Astro): innehåll som data, sidor genererade,
  formulär som serverfunktion. Passar de flesta informations- och kontaktsajter.
- **Innehållsmodell**: en typ per innehållsslag (tjänst, område, person, omdöme, fråga) med fält; varje sida byggs
  ur typerna; inga sidor utan genuint innehåll.
- **Formulärleverans**: serverfunktion → e-posttjänst med avsändare på verifierad domän, honeypot, tidsfälla på en
  klocka och servervalidering; leveransen är testet, inte svarskoden. Leveransens funktion och dess variabler:
  `kunskap/forfragan.md` och `kunskap/lansering.md` (Lanseringskonfigurationen).
- **Miljövariabler**: dokumenterade i `.env.example` med namn och ändamål (leveransens mall:
  `mall/leverans/env.example`); värden bara i värdplattformen.
- **Analys och samtycke**: kakfri analys utan samtyckesruta; GA4/pixlar bara efter samtycke (Consent Mode v2, nekat
  som standard); serverbaserad spårning är ingen genväg runt samtycket.
- **Förhandsvisning och lansering**: skyddad förhandsvisning och produktion ur samma bygge; skyddet, svaren och
  lanseringskonfigurationen står i `kunskap/lansering.md`.
- **GitHub-först** (planerat, inte implementerat: exporten gör i dag ett lokalt repo, `kunskap/lansering.md`):
  kundrepot privat under organisationen; huvudgren skyddad; driftsättning från huvudgren; förhandsvisning per gren.

## Designkontraktet (DESIGN.md)

Codex 2026-10-04 (glapp 1): en enda aktuell designspecifikation, med tydligt ansvar för varje artefakt.

| Artefakt | Ansvar |
|---|---|
| Referenspaketet (`underlag/<slug>/referenser/paket-vNN/`) | frysta observationer, bilder, mätvärden (EXTRAKT), källor och begränsningar |
| `underlag/<slug>/KONCEPT.md` | prövade alternativ, beslutet och varför de andra förkastades |
| `kunder/<slug>/sajt/DESIGN.md` | den aktuella designen: exakta värden, komposition, bildbehandling, responsiva regler och avsiktliga avvikelser från huvudreferensen |
| Den godkända vinnaren (`underlag/<slug>/atelje/vinnare/`) | körbar gestaltning som bygget tar vid från (en kandidats alla sidor, komponenter och DESIGN.md läggs i sajten: `atelje.installera_godkand`) |

DESIGN.md har prosa under fem rubriker (Komposition, Typografi, Bildbehandling, Responsiva regler, Avvikelser från
huvudreferensen) och exakt ett kodblock märkt `json design`:

```json design
{
  "schema": 1,
  "huvudreferens": "<den valda huvudreferensen: VINNARE.json efter ateljén, annars raden Huvudreferens: i REFERENSER.md>",
  "farger": {"yta": {"varde": "#f3eee6", "roll": "sidans bakgrund, största ytan", "kalla": "uppmätt: paket-v02/<namn>/01-start EXTRAKT 1440"},
             "text": {"varde": "#1d1b18", "roll": "brödtext och rubriker", "kalla": "valt: kontrast mot ytan"}},
  "typsnitt": {"rubrik": {"familj": "<typsnitt>", "reserv": "Georgia, serif", "vikt": 600, "storlek": "clamp(2.25rem, 1.2rem + 4.5vw, 4.75rem)",
                          "radavstand": "1.05", "teckenavstand": "-0.02em", "kalla": "uppskattat: ur huvudreferensens första vy"},
               "brodtext": {"familj": "<typsnitt>", "reserv": "system-ui, sans-serif", "vikt": 400, "storlek": "1.0625rem", "radavstand": "1.55",
                            "matt": "65ch", "kalla": "valt: läsbarhet på 390 px"}},
  "avstand": {"s": "0.5rem", "m": "1rem", "l": "2.5rem", "xl": "6rem"},
  "radier": {"knapp": "0"},
  "spalter": {"390": {"marginal": "1.25rem"}, "1440": {"antal": 12, "maxbredd": "1280px"}},
  "kontrast": [["text", "yta", 4.5]],
  "avvikelser": [{"fran": "huvudreferensens mörka helbild", "till": "ljus yta med kundens foto", "varfor": "kundens bilder är ljusa dagsljusfoton"}],
  "import": [{"fil": "src/styles/stil/<stil>.css", "kalla": "refero: <stilens namn> <id> (kontroller/stilpaket.py)", "sha256": "<originalets hash>"}],
  "tillstand": {"mork": {"villkor": "@media (prefers-color-scheme: dark)", "farger": {"yta": "#121212", "text": "#f3eee6"}, "kalla": "valt: kvällsläsning"}},
  "struktur": {"brodsmulor": true}
}
```

Valfria fält (Codex via ägaren 2026-10-05, punkt 6: kontraktet stödjer valda tillstånd och importerade stilvärden, så
att kontrollens förmåga aldrig avgör vad kunden får):

- **`import`:** stilexporter som sajten använder direkt, till exempel Referos CSS-variabler ur stilpaketet
  (`kontroller/stilpaket.py`). Originalet står orört (`sha256`); kundanpassningen skrivs i en egen fil. En färg eller
  typsnittsroll kan peka på exportens variabel med `"token": "--color-…"` och källan `importerat: …`; kontrollen prövar
  att variabeln finns i exporten med samma värde, och sidor som använder `var(--color-…)` räknas som att de använder
  kontraktet.
- **`tillstand`:** valda tillstånd, med `villkor` (`@media (prefers-color-scheme: dark)`) eller `valjare`
  (`.band--mork`, `[data-tema="mork"]`) och färgernas värden där. design.py skriver dem i design.css, och
  kontrastparen prövas också i varje tillstånd.
- **`struktur`:** informationsstrukturens val, i dag `brodsmulor` (byggstandarden 7.3 kräver dem bara när den är sann).

Varje värde har `kalla`: `uppmätt:` (var det mättes, ur referenspaketets EXTRAKT eller byggets egen mätning),
`uppskattat:` (ur en bild, utan mätning), `valt:` (för kunden, med skäl) eller `importerat:` (ur en stilexport, med
källan). En skärmbild visar en komposition
men ger inga säkra CSS-värden; märk därför ärligt. `.venv/bin/python kontroller/design.py <slug> --skriv` validerar
blocket (roller, hex, CSS-längder, typsnittsnamn, kontrastparen) och skriver `src/styles/design.css` med
CSS-variablerna (`--farg-<namn>`, `--typ-<roll>-familj|vikt|storlek|radavstand|teckenavstand|matt`,
`--avstand-<namn>`, `--radie-<namn>`, `--spalt-<bredd>-<namn>`), som `Bas.astro` importerar och sidornas CSS
använder. Layouten bor i koden (ateljéns vinnare), inte i variablerna. Variablerna definieras i design.css, med de
valda tillstånden; en omdefinition med ett värde som varken DESIGN.md eller ett deklarerat tillstånd har fäller
grinden. Provets grind `design` kräver att DESIGN.md
är giltig, att design.css är genererad ur den aktuella DESIGN.md, att färg- och typvariablerna används, och att
huvudreferensen är den valda (kontroller/referensval.py: VINNARE.json före REFERENSER.md); granskaren får DESIGN.md fryst och dömer avvikelser från den, men
en sajt som följer en svag DESIGN.md underkänns ändå. Googles DESIGN.md-format (`@google/design.md`, alpha) är
förebilden för att kombinera maskinläsbara värden med förklarande text; vi använder det inte som beroende, och dess
lint bedömer inte estetisk kvalitet.

## Browsergranskning under bygget

Rendera och interagera i riktig webbläsare medan du bygger, inte bara efteråt: första vyn i 390 och 1440,
tangentbordsväg genom menyn och formuläret, felvägar, konsol och nätverk (`kontroller/webblasare/`, webblasare.md).
Skärmbilder kompletterar interaktionen; ett textträd är inte bildseende. Kontrollera vilka typsnitt browsern
faktiskt renderar samt font-/bildladdningsfel innan en avvikelse förklaras som designval. Deklarerad
fontstack eller font-ready ensamt bevisar inte vilken familj som användes.

## Börja med den bärande upplevelsen

Bygg tidigt representativt riktigt innehåll och relevant interaktion (i skapandeflödet först skissen, sedan
förfiningen: `kunskap/skapandeflodet.md`), jämför med öppnade referenser och utveckla sedan helheten. Olika kundbehov
får ge olika visuella lösningar. Undersidor, språk, redaktörsytor och efterled håller samma hantverksnivå; tekniskt
fungerande är inte ensamt professionellt tillräckligt. För varje viktigt val ska behov, resurs och faktisk påverkan gå
att följa.

Hitta hit (OVL-20260930-ac1914-digitala): använd basvägen i `integrationer.md`.
Adress och vanlig länk fungerar utan JavaScript. Eventuell extern karta skapas
först efter besökarens val; statisk bild självhostas med kontrollerad licens och
attribution. CSP per sitemaprutt ska täcka den faktiskt valda kartlösningen.
