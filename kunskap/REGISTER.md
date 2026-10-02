# Register — vad som finns i kunskap/ och allt kirurgen har bedömt

## Ursprung (2026-10-01)

Kopierat när repot skapades, utan ändringar i innehållet:

- **Egna texter** ur `Nortropic/nortropic-digitala` @ `69e0b01`, `kunskap/*.md`. Utelämnade: `REGISTER.md` (ersatt av
  den här filen), `MOTTAGARPROV.md`, `bevis-och-fortsattning.md` och `konsekvensgranskning.md` (hörde till kontorets
  beviskedja). Digitalas lärdomar ligger kvar som historik i `LARDOMAR-digitala.md`.
- **Externa texter** ur samma revision, `kunskap/externa/`, bara de med licensfil:

| Text | Källa | Licens |
|---|---|---|
| `anthropic-frontend-design-SKILL.md` | anthropics/claude-plugins-official | Apache-2.0 |
| `vercel-web-interface-guidelines-command-e3d624ba.md` | vercel-labs/web-interface-guidelines | MIT |
| `addyosmani-web-quality-audit-SKILL.md`, `addyosmani-accessibility-SKILL.md` | addyosmani/web-quality-skills | MIT |
| `emil-emil-design-eng-SKILL.md`, `emil-mobile-native-SKILL.md`, `emil-prototype-SKILL.md`, `emil-prototype-PICKER-d16ebe60.md` | emilkowalski/skills | MIT |
| `leonxlnx-taste-SKILL-ce26fc25.md` | Leonxlnx/taste-skill | MIT |

  Utelämnade för att licensfil saknas: hallmark, canvas-design, google design.md README.
- **Kontroller** (`kontroller/`): `seo_kontroll.py`, `copy_kontroll.py`, `verksamhetsuppgifter.py`, `prelaunch.py`,
  `stegbevis.py` och `webblasare/*.mjs` ur nortropic-digitala @ `69e0b01`. `axe.mjs` och `lighthouse.mjs` är generella
  omskrivningar av `kund-demo-norrglanta/scripts/prov/` @ `200d604` (sidorna som argument, inga kundspecifika
  selektorer, Playwright i stället för puppeteer-core). `prova.py` och `youtube.py` är nya.
- **Kritikmallar** (`kritik/`) ur nortropic-digitala @ `69e0b01`, används som vanliga prompter.

## Intag

Kirurgens domar, äldst först. Formen står i `.claude/skills/kirurg/SKILL.md`.

Tidigare bedömningar, gjorda med de gamla reglerna, ligger i `REGISTER-arkiv-20261001.md`.

### 2026-10-02 · codecrafters-io/build-your-own-x · nej
- Källa: https://github.com/codecrafters-io/build-your-own-x @ aa17439 (senaste push 2026-07-14), CC0 enligt README
  (ingen licensfil, `gh` visar ingen licens); läst hela README (506 rader), ISSUE_TEMPLATE.md och den enda bilden
  (`codecrafters-banner.png`). Inga länkade handledningar öppnade: listan pekar ut, den innehåller inget eget.
- Steg: inget av de åtta; möjligen steg 5 (bygge) i teorin.
- Jämfört med i dag: källan är en kurerad länklista med handledningar för att bygga om programvara från grunden i
  lärosyfte (renderare, databaser, kompilatorer, git, webbservrar) [TEXT README rad 5–9, 11–40]. Inträdeskravet är
  handledningar som bygger något "from scratch", uttryckligen inga ramverk [REPO ISSUE_TEMPLATE.md rad 2]. Det
  närmaste vår verksamhet är kategorierna Front-end Framework, Template Engine, Web Server och en statisk
  sajtgenerator på 40 rader [TEXT README rad 180–195, 387–393, 418–430, 470]. Vi bygger med en färdig, underhållen
  stack: statisk Astro ur `mall/astro/` (`.claude/skills/bygg-sajt/SKILL.md:199–204`, `kunskap/byggstandard.md:25`,
  avsnitt 11 rad 133). Att ersätta den med något hemsnickrat vore sämre, och ingen post i listan handlar om det som
  ägarens domar L1–L3 pekar på (förfrågan, bildunderlag, förtroende, copy).
- Skäl: källan är en studiekatalog för programmerare som vill förstå tekniken inifrån, inte en metod för att bygga
  bättre sajter åt verksamheter eller arbeta smartare. Den tillför ingen utvärderingsmetod, ingen designprincip och
  inget verktyg som våra steg saknar; de webbnära länkarna lär ut hur en mallmotor eller webbserver fungerar, vilket
  Astro redan löser åt oss. Bannern säljer CodeCrafters kurser [BILD codecrafters-banner.png], men listan är i sig
  ofarlig och fri att använda. Värdet för oss är noll i dag och inget i vår plan gör det aktuellt senare.
- Kostnad: ingen; ungefär 12 000 tokens text om den lästes, men inget tas in.
- Säkerhet: förgranskningen LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript, inga hookar.
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · openclaw/openclaw · nej
- Källa: https://github.com/openclaw/openclaw @ d1d4342 (senaste push 2026-10-02), MIT enligt LICENSE (`gh` visar
  "Other", troligen för THIRD_PARTY_NOTICES); 51 637 filer, cirka 9,3 miljoner tokens text. Läst: README rad 1–137
  (resten är bidragsgivarlistan och licensraden), VISION.md, AGENTS.md rad 1–40, beskrivningarna för alla 51 skills i
  `.agents/skills/` och de tio mest webbnära i `skills/`, samt hela SKILL.md för `deslop`, `technical-documentation`,
  `control-ui-e2e` och `spike`. Bild: `docs/assets/openclaw-banner-dark.png`. Ingen demosajt finns; produkten är ett
  program, inte ett utfall att se.
- Steg: inget av de åtta; närmast steg 4–6 (galleriet i `control-ui-e2e`) och hur ägaren dömer.
- Jämfört med i dag: openclaw är en självhostad AI-assistent med en lokal gateway som ägaren når via WhatsApp,
  Telegram, Slack, iMessage och tjugo andra kanaler, med utbytbara modeller och en plugin- och skillmarknad (ClawHub)
  [REPO README.md rad 18–20, 68–75]. Det är en ersättning för vår körmiljö (Claude Code, `kor.sh`, dashboarden), inte
  en metod för att bygga sajter. Tre delar prövades sak mot sak. (1) `control-ui-e2e` låter agenten bygga ett
  HTML-galleri med komponentens lägen (tom, fel, laddar, lång text) och en sparad kommentarsruta per exempel som ägaren
  kopierar tillbaka [REPO .agents/skills/control-ui-e2e/SKILL.md rad 10–41]. Vi har redan samma slinga för det som
  gäller en webbplats: fyra riktningar i KONCEPT.md och parvisa frågor med skärmbild i FRAGOR.json som dashboarden
  visar och sparar (`.claude/skills/bygg-sajt/SKILL.md:187–197`, `:299–307`); felmeddelanden och tacksida prövas av
  standardgrinden (`kunskap/byggstandard.md:85`, `.claude/skills/bygg-sajt/SKILL.md:209–212`). Lika, inte bättre. Deras
  galleri är byggt för en app med många lägen; en statisk sajt har få. (2) `deslop` städar AI-slop i kod (kommentarer,
  defensiva kontroller, typkonverteringar) [REPO .agents/skills/deslop/SKILL.md rad 13–19]; vår regel mot slop gäller
  sajtens text (`kunskap/copy-kontroll.md:10–20`), som `deslop` inte berör. (3) `spike` har en domform
  (VALIDATED/PARTIAL/INVALIDATED) och kräver lika indata vid A/B [REPO skills/spike/SKILL.md rad 28–45]; vår A/B-regel i
  kirurgskillen kräver dessutom flera körningar, blind parvis jämförelse och en annan domare. Sämre än vår.
- Skäl: källan hjälper inte oss att bygga bättre sajter. Den är en plattform för en personlig assistent i chatten, och
  det som ligger närmast vårt flöde gör vi redan lika bra eller bättre. Att byta körmiljö skulle krocka med två medvetna
  val: ingen agent som ändrar systemet obevakat (deras verktyg körs på värden om man inte själv sätter upp en sandlåda
  [REPO README.md rad 81]) och att kod ur källor inte körs (installationen är ett `curl | bash`-skript [REPO README.md
  rad 28–31]). Projektet är väl skött och ärligt om sina risker: stiftelse, MIT-licens, inga betalnivåer [REPO README.md
  rad 20, 108–110]. Påståendena om 391 000 stjärnor och "the AI that really does things" [BESKRIVNING] säger inget om
  nyttan för oss. Kanalerna (att nå ägaren eller en kund i WhatsApp) kan bli aktuella den dag vi har kunder att nå, men
  då genom verksamhetens egna kanaler och en tjänst som inte drivs av ägarens Claude-prenumeration, inte genom den här
  plattformen.
- Kostnad: ingen; inget tas in. En enskild skill därifrån skulle kosta 20–130 tokens alltid och 200–14 500 vid
  användning enligt förgranskningen, men ingen bär sin vikt för oss.
- Säkerhet: förgranskningen HÖG. 2 642 dolda tecken, vid stickprov riktningsstyrning och nollbredd i
  översättningsfiler för arabiska och persiska (`apps/.i18n/native/ar.json`, `fa.json`), alltså legitim skrift. 226
  träffar på text riktad till agenter: i stickproven hotmodeller och säkerhetsdokument som beskriver promptinjektion
  (`docs/gateway/security/prompt-injection.md`, `docs/security/THREAT-MODEL-ATLAS*`) och en egen prompt i ett skript
  (`.agents/skills/agent-transcript/scripts/agent-transcript`); inget i det som lästes försökte styra kirurgen. 43 481
  skript, med installatör via `curl | bash` och skills som anropar externa tjänster. Inget kördes.
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · vinta/awesome-python · nej
- Källa: https://github.com/vinta/awesome-python @ 0d43beb (ur klonens packed-refs; senaste push
  2026-10-02T12:01Z), CC BY 4.0 enligt LICENSE (`gh` visar "Other"). Läst: README (1 205
  rader, 77 avsnitt; i detalj de webbnära: Template Engines, Web Asset Management, Static Site Generators, Web Scraping,
  HTML Manipulation, Image Processing), DESIGN.md, CLAUDE.md, CONTEXT.md, `docs/adr/0001-shortlist-not-catalog.md` och
  alla tre skills i `.claude/skills/` (audit-the-list, preview-verdicts, review-prs). Repot har inga bilder; sajten
  awesome-python.com sedd med `sida.mjs`: första vyn i mobil och desktop och skrollbild 2 av 8 lästa.
- Steg: inget av de åtta; närmast steg 5 (designspecifikationen) och hur ägaren dömer (granskningssidan).
- Jämfört med i dag: källan är en kurerad lista över Python-bibliotek som sedan 2026 skärs ned till högst fem poster
  per användningsfall, med nedladdningar från PyPI som främsta belägg [REPO docs/adr/0001-shortlist-not-catalog.md rad
  7, 11]. Vi bygger i statisk Astro med Node-kontroller (`kunskap/byggstandard.md:3–5`, avsnitt 11 rad 133–138); de
  webbnära posterna (pelican, nikola, jinja, whitenoise, trafilatura, pillow [REPO README.md rad 314–327, 366–371,
  388–401, 954–966]) ersätter eller tillför inget i den stacken. Tre delar runt listan prövades sak mot sak. (1)
  DESIGN.md är sajtens designkontrakt i Google Stitch-form: tokens med roller, anti-referenser, förbjudna grepp och en
  revisionslista i sex punkter efter varje ändring [REPO DESIGN.md rad 43–47, 85–90, 182–198, 207–216]. Vår
  motsvarighet är den exakta specifikationen i KONCEPT.md (färger med roller, skala, radie, avstånd, sektionsordning) och
  UPPTAGNA-VAL.md mot vanevalen (`.claude/skills/bygg-sajt/SKILL.md:182–197`); deras regel att accenten bara får bära
  det klickbara står redan som dimension 3 (`kunskap/referenser-professionella.md:22, 53`) och deras
  syskonkontroll är dimension 8 (`:30`). Lika för ett bygge i en session; deras form lönar sig för en sajt som
  förvaltas genom många sessioner, vilket inte är vårt läge i dag. (2) preview-verdicts bygger en HTML-sida med
  behåll/stryk per rad och en knapp som kopierar ägarens ändringar som JSON tillbaka till chatten [REPO
  .claude/skills/preview-verdicts/SKILL.md rad 8, 18, 22]. Vi har samma slinga inbyggd i dashboarden: frågeformuläret
  och FRAGOR.json sparas direkt till LARDOMAR.md (`.claude/skills/bygg-sajt/SKILL.md:299–307`, `LARDOMAR.md:3–6`) och
  kirurgens domar överprövas i KIRURG-OMDOMEN.md. Vårt är smartare: ägaren klistrar inget. (3) Ägarens rättelser blir
  hårda regler ("corrected sizes upward 11+ times") [REPO DESIGN.md rad 118; CLAUDE.md rad 22]; det är vår L-dom som
  blir en textändring (`LARDOMAR.md:3–6`). Lika.
- Skäl: listan svarar på "vilket Python-bibliotek ska jag använda", en fråga våra byggen inte ställer; ingen post i den
  hjälper med det som ägarens domar L1–L3 pekar på (förfrågan, bildunderlag, förtroende, copy). Det intressanta i repot
  är hantverket runt listan, och där gör vi redan samma sak: designkontrakt, ägarens domar som text och en sida där
  ägaren dömer rad för rad. Sajten är omsorgsfullt gjord (serif i omslagsstorlek, varm palett, tät tabell [BILD
  desktop-forsta.png; BILD desktop-skroll-02.png]) men modellerad på en tät referenslista för utvecklare [REPO
  DESIGN.md rad 38]; som referens för en hantverkarsajt säger den lite, och referenser väljs per bygge i steg 3. Källan
  säljer inget utöver ett sponsorband och är ärlig om sina belägg; dess regel att aldrig installera eller köra det som
  bedöms [REPO CLAUDE.md rad 12] är samma som vår.
- Kostnad: ingen; inget tas in. Hela källan är cirka 116 000 tokens text; de tre skillsen kostar 62–92 tokens alltid
  och 756–1 691 vid användning enligt förgranskningen, men de gäller underhåll av just den listan.
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text riktad till agenter, inga behörigheter eller hookar.
  Tio skript för sajtbygget, med eval/exec och miljövariabler (`website/build.py`, `fetch_*`, testerna), som hämtar
  stjärnor och nedladdningar. Inget kördes; inget i det som lästes försökte styra kirurgen.
- Förslag: inget
- Utfall: —
- Backlog: ingen
