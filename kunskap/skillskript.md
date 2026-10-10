# Körbara skillfunktioner i den egna kandidaten

När `brand`, `design-system`, `ui-styling` eller `canvas-design` behöver ett medföljande skript: skriv ett JSON-uppdrag
i `underlag/<slug>/atelje/kandidater/<kNN>/kompetens/skriptuppdrag/` och kör:

```sh
.venv/bin/python kontroller/skillskript.py <slug> --kandidat <kNN> --uppdrag underlag/<slug>/atelje/kandidater/<kNN>/kompetens/skriptuppdrag/uppdrag.json
```

`id` är ett nytt namn per försök. Utdata och `RESULTAT.json` hamnar i kandidatens `kompetens/skillskript/<id>/`.
En befintlig version ersätts aldrig. Ange filer relativt motorns reporot eller med dess absoluta sökväg, som uppdraget
använder när arbetsroten är kundrepot: egen kandidat under ateljén eller egen `kunder/<slug>/kandidater/<kNN>/sajt/src/`.
Punktled och länkar nekas i båda formerna. Gemensamt kundmaterial måste först väljas och kopieras in genom det ordinarie
materialsteget. Läs färdiga utdata innan du för över något till sajtens kod.

| Uppgift | `action` | Fält utöver `id` och `action` | Vad funktionen faktiskt gör |
|---|---|---|---|
| Varumärkessammanhang | `brand-context` | `input`: Markdown | Extraherar färg, typografi och tonalitet till JSON i `stdout.txt`. |
| Dokumenterad palett | `brand-palette` | `input`: Markdown | Läser hexvärden ur varumärkesfilen. Ingen färganalys av bildpixlar. |
| Tillgångskontroll | `brand-asset` | `input`: bildfil | Rapporterar det medföljande skriptets namn-, storleks- och metadataregler. |
| Färgunderlag till tokens | `brand-tokens` | `input`: Markdown; `tokens`: befintlig JSON, valfri | Genererar `design-tokens.json` och `.css` på kopior. Resultatet är ett utkast. |
| Tokenexport | `tokens-css` eller `tokens-tailwind` | `input`: token-JSON | Genererar `tokens.css` eller `tokens.tailwind.cjs` (konfigurationsutdrag). |
| Inbäddningsbar CSS | `tokens-embed` | `input`: token-CSS; `minimal`: bool, valfri | Kopierar/filtrerar token-CSS till `tokens.css`. |
| Hårdkodade värden | `tokens-validate` | `files`: 1–64 egna webbkällfiler | Söker enligt skriptets tokenregler; ändrar inte filerna. |
| Tailwind-utkast | `tailwind-config` | `framework`; `colors`, `fonts`, `spacing`, `breakpoints`: objekt med strängvärden | Skriver `tailwind.config.ts`, installerar inget och exekverar inte konfigurationen. |
| Grafiskt koncept | `canvas` | `input`: statisk SVG; `width`, `height`; `format`: `png`, `pdf` eller `both`; `fonts`: valfri lista | Renderar `canvas.png`/`.pdf` med befintligt Playwright. |

Varumärkesskripten känner igen engelska avsnittsnamn som `Primary Colors`. Bevara kundens innehåll men använd skriptets
fältstruktur när ett maskinläsbart färgunderlag behövs. En lyckad körning med tom palett visar inte att paletten är klar.
Validerarnas egna konventioner är rådgivande underlag, inte nya Nortropic-krav och inte ett visuellt godkännande.
`tokens-validate` läser varje angiven fil som råtext, även HTML/Astro. Rapportens `src/00.css`, `src/01.css` och vidare
är uppdragets filer i ordning; de tillfälliga namnen undviker originalskriptets tysta filnamns- och formatundantag.

Tailwind-generatorns ramverk är `react`, `vue`, `svelte` och `nextjs`. Välj och anpassa konfigurationen till projektets
faktiska Tailwind-version; utkastet är inte ett versionsprov eller färdig Astro-konfiguration. Installation av shadcn
eller rekommenderade pluginpaket går genom `kunskap/beroenden.md`, inte genom den här bryggan. Presentation-,
slide-sök- och bakgrundsskripten i `design-system` har ingen webbygguppgift i bryggan.

## Canvas till en faktisk bild

Skriv kompositionen i kandidatens `koncept/`, som statisk SVG med former, text, gradienter och eventuellt inbäddade PNG/JPEG/WebP-bilder.
Använd SVG-attribut för typografi och färg, inte HTML, JavaScript eller stilmallar. `fonts` anger medföljande TTF-filnamn
från `.claude/skills/canvas-design/canvas-fonts/`; SVG:s `font-family` är filnamnet utan `.ttf`. Formgivningen bedöms
efter rendering; att bilden kan öppnas bevisar inte att den når ribban.

```json
{
  "id": "komposition-01",
  "action": "canvas",
  "input": "underlag/<slug>/atelje/kandidater/k01/koncept/komposition.svg",
  "width": 1440,
  "height": 900,
  "format": "both",
  "fonts": ["WorkSans-Regular.ttf"]
}
```

I sandlådan går canvas genom webbtjänstens `skillskript-canvas`. Tjänsten läser och prövar uppdraget igen och kör bara
den fasta renderaren. Den behöver varken Pillow eller reportlab. Sidans externa förfrågningar blockeras; bilder och typsnitt
måste först komma in genom materialflödet. JavaScript är avstängt och sidan har en begränsad CSP. Browserprocessen har
tjänstens befintliga nätpolicy, ingen ny OS-isolering. Bredd och höjd är högst 4096 px och sammanlagt högst 16 miljoner pixlar.

När PNG/PDF är bedömd och ska ingå i materialet: registrera den med befintliga `material.py <slug> --kandidat <kNN>
--canvas <fil> --bestall "<bildens uppgift>"`. Materialstegets ägarskap, rättigheter och användningskvitto gäller även här.
Renderaren genererar ingen fotografisk AI-bild; sådant beställs genom materialstegets leverantörer.

## Bevis och gränser

`RESULTAT.json` binder uppdrag, lästa filer, betrodda skript och utdata till SHA-256. `status: kord` kräver slutkod 0
och förväntade utdata; `visuell_kvalitet` är alltid `ej_bedomd`. `stdout.txt` och `stderr.txt` ligger privat bredvid.
Ett skriptfynd ger slutkod 1, ett vägrat eller trasigt anrop 2. Ett fel före färdigt kvitto lämnar en ofärdig egen
jobbkatalog som inte får räknas som genomförd. SIGTERM stoppar skriptets processgrupp, städar arbetskopian och ger 143.

Bryggan kopierar avgränsad indata till en registrerad temporär katalog utanför kandidaten och kör fasta repo-skript
med fasta argument. Det förankrade slutmålets identitet kontrolleras igen före publicering.
Symlänkar, hårdlänkade indata, andra kandidater, godtyckliga program och egna utdataadresser nekas. Ett lyckat anrop
bevisar funktionen för just de filerna; det ersätter varken skillens tillämpning, sidans granskning eller ett verkligt
sessionsprov av verktygstillgången.
