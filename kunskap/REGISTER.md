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

### 2026-10-02 · obra/superpowers · ta in
- Källa: https://github.com/obra/superpowers @ 8ca22db (ur klonens `.git/shallow`; senaste push 2026-09-27T02:37Z),
  MIT. Läst: README, AGENTS.md, förgranskningen, och SKILL.md för brainstorming, verification-before-completion,
  receiving-code-review, systematic-debugging, diagnosing-superpowers och writing-skills med
  `testing-skills-with-subagents.md`. Övriga nio skills (TDD, planer, worktrees, grenar, parallella agenter,
  subagentdriven utveckling) bara i README:s sammanfattning och filförteckningen. Repot har inga bilder i skills-mapparna
  och ingen demosajt; inget att se.
- Steg: steg 8 (hur ägarens dom blir en textändring, alltså backlog-skillen); i övrigt inget av de åtta.
- Jämfört med i dag: superpowers är en metod för programvaruutveckling som injiceras i varje session via en
  SessionStart-krok [REPO hooks/hooks.json] och gör det till tvång att använda dess skills [REPO README.md rad 323].
  Sak mot sak: (1) brainstorming kräver ägarens godkännande av designen före allt bygge [REPO
  skills/brainstorming/SKILL.md rad 38–56]; våra byggen körs utan människa och märker antaganden i stället
  (`.claude/skills/bygg-sajt/SKILL.md:20–24`). Krock. (2) verification-before-completion kräver färskt belägg före
  varje påstående om att något är klart [REPO skills/verification-before-completion/SKILL.md rad 16–20]; vi har det som
  mekanik, stoppvakten kör provet och granskaren själv och släpper inte avslutet (`bygg-sajt/SKILL.md:324–326`). Vårt
  är starkare. (3) receiving-code-review: pröva varje invändning mot verkligheten och säg emot med skäl [REPO
  skills/receiving-code-review/SKILL.md rad 67–84]; samma som vårt steg 5.6, där förbättringar är valfria och en fel
  invändning motiveras i rapporten (`bygg-sajt/SKILL.md:229–232`). Lika. (4) writing-skills: beskrivningen ska säga när
  skillen används, inte sammanfatta arbetsgången [REPO skills/writing-skills/SKILL.md rad 150–158]; samma som
  backlog-skillens regel för verktygslådan (`.claude/skills/backlog/SKILL.md:35`). Lika. (5) Samma fil har en tabell
  "Match the Form to the Failure" [REPO skills/writing-skills/SKILL.md rad 461–476]: klassa först hur agenten brast,
  sedan formen. Utelämnade den något blir det en obligatorisk plats i det den redan fyller i; fel form på resultatet
  blir en beskrivning av resultatet; bröt den en känd regel blir det förbud med de undanflykter den använde; beror det
  på läget blir det ett villkor på något observerbart. Inga brasklappar. Vår backlog-skill säger bara att en dom blir
  en textändring (`backlog/SKILL.md:26–27`) och prövar ändringen på att sökvägarna finns (`:39–40`), inte på formen.
  Våra bästa domändringar råkar redan följa tabellen: L2/L3 blev BESTALLNING.md (`bygg-sajt/SKILL.md:130–134`) och L1
  blev en färdig formulärkomponent (`:209–212`), båda platser och inte påminnelser. Källans sätt är smartare: det gör
  regel av det som hittills varit tur. (6) Mikroprov av formuleringar mot en kontroll utan ändringen, minst fem
  körningar per variant och varje träff läst för hand [REPO skills/writing-skills/SKILL.md rad 579–587]; vi har ingen
  motsvarighet, en domändring syns först i nästa bygge. Ställt mot litteraturen är det Design Science Researchs
  "utvärdera artefakten" (`kunskap/teoretisk-grund.md:26–27`) tillämpat på våra egna skilltexter. (7) diagnosing-
  superpowers läser sessionsloggen med en analytiker per dimension och kräver fil och rad för varje fynd, men börjar med
  intervju och stannar om människan är borta [REPO skills/diagnosing-superpowers/SKILL.md rad 104–109] och gäller
  superpowers egna felrapporter. Inget för oss nu.
- Skäl: som paket är det fel verktyg: en metod för kod med testdriven utveckling, grenar och godkännandegrindar,
  injicerad i varje session, krockar med obevakade byggen och tillför inget till sajtens kvalitet. Men författarna har
  prövat hur agenter tar emot skilltexter, och två lärdomar gäller just vår slinga där en dom blir en textändring:
  välj formen efter hur bygget brast, och pröva formuleringen mot en kontroll. Belägget för att förbud slår bakut på
  formfel är källans eget påstående om parvisa ordtester ("fully separated distributions") utan publicerade data [REPO
  skills/writing-skills/SKILL.md rad 472]; det är rimligt men obelagt här, och därför tas klassningen in som text
  (billig, och den stämmer med våra egna lyckade ändringar) medan mikroprovet blir en egen prövning. README säljer
  kommersiell support [REPO README.md rad 48–50] och stjärnantalet (cirka 294 000) säger inget om metoden.
  Källkritik: innehåller instruktioner till agenter, AGENTS.md rad 3–20 ("If You Are an AI Agent"), riktade till
  agenter som vill öppna PR mot repot; de gällde inte kirurgen och följdes inte.
- Kostnad: förslaget är cirka sex rader i backlog-skillen, som laddas bara när backloggen genomförs; noll i varje
  session. Mikroprovet kostar minst tio subagentkörningar per domändring; kostnaden redovisas bredvid utfallet. Inga
  beroenden. Hela källan är cirka 360 000 tokens text; inget av den kopieras.
- Säkerhet: förgranskningen HÖG: inga dolda tecken; fyra ställen med text till agenter (AGENTS.md och planer/skills som
  säger "execute this"); en SessionStart-krok som kör ett skript i varje session; 69 skript, bland dem brainstormings
  webbserver med nätanrop och eval/exec; och telemetri, brainstormings visuella följeslagare hämtar en logga från
  upphovsmannens sajt med versionsnummer [REPO README.md rad 397–399]. Inget kördes, inget installeras; bara två
  principer tas in med egna ord.
- Förslag: `.claude/skills/backlog/SKILL.md` steg 3 (efter rad 26–27): ett stycke om att klassa domen i fyra klasser
  (utelämnat → plats i mall eller fil; fel form → beskriv resultatet; bruten regel → förbud med byggets egna
  undanflykter; lägesberoende → villkor på något observerbart), inga brasklappar, klassen skrivs på raden Ändring i
  LARDOMAR.md. Egen innovation: steg 4 får ett mikroprov för domändringar, gamla mot nya texten, minst fem färska
  subagenter per arm, blind läsning av en annan modell, behåll vid minst fyra av fem.
- Utfall: —
- Backlog: B-20261002-valj-formen-pa-en-domandring-efter-hur-bygget-br (ta in);
  B-20261002-mikroprova-en-domandring-mot-en-kontroll-utan-an (prova A/B, egen innovation)

### 2026-10-02 · mattpocock/skills · ta in
- Källa: https://github.com/mattpocock/skills @ d81f3a1 (ur klonens `.git/shallow`; senaste push 2026-09-29T12:38Z),
  MIT enligt LICENSE. Läst: README, förgranskningen, och hela SKILL.md för writing-for-agents med
  `SKILL-MECHANICS.md`, retro, prototype med `UI.md`, to-questionnaire, code-review, research, writing-shape och
  writing-fragments. Övriga 29 av 37 skills (TDD, triage, spec, tickets, wayfinder, wizard, handoff, teach m.fl.) bara i
  README:s sammanfattning och förgranskningens storlekstabell. Repot har inga bilder; README:s banner ligger på en
  extern bildtjänst och visar bara namnet. Ingen demosajt.
- Steg: steg 8 och backlog-skillen (hur en dom blir text); steg 5.1 och frågorna till ägaren (den egna innovationen).
- Jämfört med i dag: källan är en verktygslåda för programmerare som arbetar med agenter: intervju före arbete,
  gemensam ordlista, TDD, granskning i två axlar [REPO README.md rad 88–178]. Sak mot sak: (1) writing-for-agents är
  en referens för att skriva texter som agenter läser: ordalydelsen i en pekare avgör när materialet nås, varje steg
  slutar i ett slutvillkor som är tydligt och krävande, styr med det positiva målet i stället för förbud, en betydelse
  på ett ställe, och rensa no-ops och inaktuella lager ("sediment") [REPO
  skills/productivity/writing-for-agents/SKILL.md rad 10–18, 45–52, 74, 76–81]. Vi har ingen sådan regel: backlog-
  skillen säger att en dom blir en textändring, så liten som posten kräver (`.claude/skills/backlog/SKILL.md:26–27`),
  och prövar bara att sökvägarna finns (`:39–40`). Följden syns i `bygg-sajt/SKILL.md`, 333 rader som växer med varje
  dom: beställningen beskrivs både i ramarna och i steg 3 (`:20–24`, `:130–134`), copy-kontroll.md läses både i
  uppstarten och i steg 4 (`:56–57`, `:155`), och slutvillkoren är ojämna, "tills den svarar exit 0" (`:76`) bredvid
  "läs texten högt … skriv om den" (`:171–172`). Källans sätt är smartare: det ger den som genomför backloggen en
  måttstock vi saknar. (2) prototype/UI.md bygger flera strukturellt olika varianter på den riktiga sidan med riktigt
  innehåll, eftersom "every variant looks fine in isolation" [REPO skills/engineering/prototype/UI.md rad 16]. Vårt
  steg 5.1 kräver fyra riktningar och en namngiven axel (`bygg-sajt/SKILL.md:187–197`), men bara den valda byggs; i
  alla tre byggen visade riktningsfrågan bara den byggda sajtens skärmbild och beskrev alternativet i ord
  (`kunder/*/FRAGOR.json` post 1; dashboarden visar en bild per fråga, `dashboard/index.html:255`), och ägaren valde
  "som byggd" alla tre gånger (`LARDOMAR.md:40, 65, 89`). Källans sätt är bättre för ägarens dom; det blir den egna
  innovationen. (3) to-questionnaire (syfte, viktigast först, en idé per fråga, "vet inte" är ett svar) [REPO
  skills/productivity/to-questionnaire/SKILL.md rad 20–40] mot vår BESTALLNING.md, en rad per sak med vad, varför och
  var, svarbar på fem minuter (`bygg-sajt/SKILL.md:130–134`). Lika. (4) retro klassar ett fel och bygger hellre en
  kontroll än skriver en regel [REPO skills/engineering/retro/SKILL.md rad 19]; det krockar med vårt val att en dom
  blir en textändring, inte ny mekanik (`CLAUDE.md`, Arbetssätt), och byggets brister blir redan backlogposter
  (`bygg-sajt/SKILL.md:313–319`). (5) code-review håller standard och spec isär i två subagenter [REPO
  skills/engineering/code-review/SKILL.md rad 6–11, 80–87]; vi har samma delning mellan provets grindar och
  granskaren, som prövar briefens EARS-krav (`bygg-sajt/SKILL.md:119–121`). Lika. (6) writing-shape och
  writing-fragments förutsätter en människa i samtalet [REPO skills/in-progress/writing-shape/SKILL.md rad 23–26];
  våra byggen körs utan. Inget för oss.
- Skäl: som paket är det verktyg för kodprojekt med en människa vid tangentbordet, och det mesta (intervjuer, ärenden,
  TDD, PR) hjälper inte en obevakad sajtbyggare. Men writing-for-agents är en sammanhängande lära om just det vi gör
  vid varje dom: ändra en skilltext så att nästa bygge beter sig annorlunda. Den tappar värde om den kokas ned till
  några rader, så den tas in som skill och backlog-skillen pekar på den. Den kompletterar superpowers-intaget (form
  efter brist, mikroprov) med rensningen som saknas där; en krock finns: källan vill ha förbud bara som hårda
  skyddsräcken, ihopparade med det positiva målet [REPO skills/productivity/writing-for-agents/SKILL.md rad 74],
  medan superpowers-postens klass (c) är förbud med undanflykter, så klass (c) skrivs som förbud plus målet.
  Källkritik: principerna är upphovsmannens erfarenhet utan publicerade mätningar; att no-ops avgörs "by running the
  document, not by debate" (rad 81) stämmer med vår mikroprovspost. README säljer ett nyhetsbrev [REPO README.md rad
  21–23], och cirka 274 000 stjärnor säger inget om metoden.
- Kostnad: skillen kostar cirka 30 tokens i varje session (beskrivningen) och cirka 3 400 när den används (SKILL.md
  2 683 plus SKILL-MECHANICS.md) enligt förgranskningen; bara i sessioner som ändrar texter, aldrig i byggen. Inga
  beroenden, inga skript. Underhåll: kopian följer inte källan. Den egna innovationen kostar en extra förstavy och två
  skärmbilder per bygge.
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text riktad till agenter, inga hookar eller MCP; 22 skills
  har bara `disable-model-invocation`. Sju skript, bland dem `scripts/link-skills.sh` som skriver utanför repot och
  wizardmallen som hanterar hemligheter; inget av dem följer med. writing-for-agents har inga skript och inga
  behörigheter; `agents/openai.yaml` (visningsnamn för Codex) tas bort. Inget kördes.
- Förslag: `.claude/skills/writing-for-agents/` (SKILL.md, SKILL-MECHANICS.md, LICENSE, KALLA.md) med en beskrivning som
  säger att den används när en session ändrar en skill, CLAUDE.md eller en kunskapsfil, inte av byggen; en rad i
  `.claude/skills/backlog/SKILL.md` steg 3 (efter rad 26–27) som pekar på den och prövar ändringen mot dubbletter och
  inaktuella rader. Egen innovation: steg 5.1 bygger tvåan-riktningens första vy som kastbar sida och riktningsfrågan
  får en skärmbild per alternativ (`dashboard/index.html:255` tar en lista).
- Utfall: writing-for-agents intagen 2026-10-02 i `.claude/skills/writing-for-agents/`; backlog-skillens steg 3
  pekar på den och klass (c) skrivs som förbud plus målet. Rendera tvåan införd 2026-10-02: steg 5.4 bygger tvåans
  första vy som kastbar sida, riktningsfrågan får en bild per alternativ (dashboarden visar listan), standarden fäller
  en kvarlämnad `/tvaan/`. Prövningen: nästa två byggen mot de tre tidigare, där ägaren valde "som byggd" varje gång.
- Backlog: B-20261002-ta-in-mattpocock-skills-writing-for-agents-i-ver (ta in);
  B-20261002-rendera-tvaan-den-nast-starkaste-riktningens-for (prova A/B, egen innovation)

### 2026-10-02 · affaan-m/ECC · ta in
- Källa: https://github.com/affaan-m/ECC @ ef648e0 (ur klonens `.git/shallow`; senaste push 2026-10-02T02:01Z), MIT,
  cirka 271 000 stjärnor, inte arkiverat. Bedömd förut med de gamla reglerna (`REGISTER-arkiv-20261001.md:567`, nej);
  arkivet ligger utanför registret, så det här är en ny bedömning med dagens regler (storlek och tokens är inget
  nej-skäl). Förgranskat. Läst själv: README rad 1–170, hjältebilden `assets/hero.png`, `hooks/hooks.json` (händelserna),
  `workflows/orch-review.workflow.js` rad 110–139 och de rader ur santa-method och loop-design-check som citeras nedan.
  Läst i helhet av tre subagenter med belägg (domen är min): 35 skills, nämligen designen (frontend-design-direction,
  make-interfaces-feel-better, design-system, taste, liquid-glass-design, motion-foundations/-patterns/-advanced,
  inherit-legacy-style, ui-demo), prov och utvärdering (loop-design-check, browser-qa, click-path-audit, frontend-a11y,
  accessibility, seo, production-audit, canary-watch, verification-loop, gan-style-harness, santa-method, council,
  eval-harness), samt innehåll, varumärke och kunder (brand-voice, brand-discovery, article-writing, content-engine,
  product-lens, competitive-platform-analysis, benchmark-methodology, competitive-report-structure, lead-intelligence,
  marketing-campaign, deep-research, search-first). Övriga cirka 258 skills bara som namn och beskrivning (språk- och
  ramverksmönster, finans, hälsovård, sociala medier). Ingen demosajt; ecc.tools öppnades inte. Ägarens not: ingen
- Steg: 5.6 (oberoende granskning) och ramarna för körningen (`kor.sh`, stoppvakten); i övrigt inget av de åtta
- Jämfört med i dag: (1) Design: frontend-design-direction och make-interfaces-feel-better är kortare upplagor av det
  steg 5 redan läser (`bygg-sajt/SKILL.md:177–180`): Anthropics frontend-design, Emil och Vercels riktlinjer. Skillen
  säger själv att den inte buntar Anthropics [REPO skills/frontend-design-direction/SKILL.md rad 13–18]. Sämre:
  den tillåter "real or generated visual assets" [REPO samma fil rad 53] mot "Inga stockbilder" (`bygg-sajt/SKILL.md:70`);
  design-system hämtar tokens ur "3 competitor sites" [REPO skills/design-system/SKILL.md rad 27] mot referenser som
  inte kopieras (`:223`). Rörelseskillsen kräver React och `motion/react` och utesluter ren CSS, mot "ingen JavaScript
  som inte behövs" (`:202`). (2) Innehåll: marketing-campaigns test om texten skulle fungera oförändrad hos en
  konkurrent [REPO skills/marketing-campaign/SKILL.md rad 95] har vi redan, i steg 4 (`bygg-sajt/SKILL.md:171–172`) och
  i granskarens originalitet (`kritik/GRANSKARE.md:80`). Femsekunderstestet har vi avskärmat (`bygg-sajt/SKILL.md:259–264`).
  brand-voice bygger rösten ur X-inlägg och mejl [REPO skills/brand-voice/SKILL.md rad 21–26]; vår ton kommer ur
  verksamhetens och kundernas ord (`:127`). Lika eller sämre. (3) Granskaren: gan-style-harness (design, originalitet,
  hantverk, funktion med förankrade betyg och tröskel 7) [REPO skills/gan-style-harness/SKILL.md rad 119–148] bygger på
  samma Anthropic-artikel som vår granskare och är det vi har (`kritik/GRANSKARE.md:12–14, 67–95`). Lika. Men
  santa-method låter två granskare med samma kriterier döma isolerat, var för sig, och ett fynd räknas som verkligt om
  en av dem hittar det, med nya granskare varje omgång [REPO skills/santa-method/SKILL.md rad 79–84, 162–174, 204]. Vi
  kör en huvudgranskare per omgång (`kontroller/granska.py:266–273`) och en originalitetsdomare i skugga (`:302–304`).
  Litteraturen står på källans sida: en ensam granskare hittar omkring 35 procent av problemen, tre till fem omkring 75
  (`kunskap/teoretisk-grund.md:128–129`). Ägaren hittade efter godkännandet konkreta fel i alla tre byggena
  (`LARDOMAR.md:32, 57, 81`). Kanske bättre; det syns först i ett prov. (4) Gränsen för byggaren: loop-design-check
  säger att byggaren aldrig får ändra sina acceptansvillkor, och att en slinga som bara grindar på "allt grönt" får
  agenten att ta bort proven [REPO skills/loop-design-check/SKILL.md rad 85, 105]. Hos oss står förbudet bara som text
  (`bygg-sajt/SKILL.md:47`), medan `kor.sh:40` ger bygget Write och Edit utan sökvägsgräns; stoppvakten kör
  `kontroller/prova.py` ur samma arbetsträd (`.claude/hooks/stoppvakt.py:51`) och granskaren läser `kritik/GRANSKARE.md`
  därifrån (`kontroller/granska.py:219, 272`). Källans sätt är smartare och kostar några rader i `kor.sh`, där samma
  slags nekanden redan står (`:51–52`)
- Skäl: som paket är ECC fel verktyg: en plugin för kodprojekt med krokar i sex händelser [REPO hooks/hooks.json rad 3,
  92, 103, 123, 166, 240] och en inlärningsslinga som gör om sessioner till nya skills, vilket krockar med att en dom
  blir en textändring av ägarens hand. Designdelarna tillför inget utöver det vi läser och drar på två ställen åt fel
  håll (genererade bilder, konkurrenters tokens). Men två metoder för utvärdering bär: byggaren ska inte kunna nå
  provet den döms av, och två oberoende granskare hittar mer än en. Den första är en liten ändring av ett medvetet val
  vi redan har ("ingen agent som ändrar systemet obevakat") och tas in direkt. Den andra följer litteraturen men dubblar
  granskarens kostnad, så den prövas mot ägarens facit först. Källkritik: README:n säljer ECC Pro från 19 dollar per
  plats och månad och visar sponsorer [REPO README.md rad 79–83, 104–122]; hjältebilden är själv ett vanligt mönster
  (nästan svart botten, orangeröd accent på rubrikens sista ord, spärrad versal eyebrow, monospace-etiketter) och visar
  261 skills mot README:ns 293 [BILD assets/hero.png; REPO README.md rad 142]. Santa-methods påstående att en flagga
  från en granskare är verklig är upphovsmannens resonemang utan mätningar; stödet för det här kommer från NN/g, inte
  från källan. Inget försök att styra granskaren hittades i det lästa
- Kostnad: inget kopieras; ingen skill tas in. Gränsen kostar inga tokens. A/B:t kostar cirka 18 granskarsessioner
  (4–15 minuter var, `bygg-sajt/SKILL.md:227`) och en domare; vinner arm B dubblas granskarens kostnad per omgång men
  inte tiden (sessionerna går parallellt). Hela källan är cirka 3,9 miljoner tokens text
- Säkerhet: förgranskningen HÖG, inga dolda tecken. HÖG kommer av 1 003 skript, bland dem installatörer som skriver
  utanför repot (`.codebuddy/install.sh`, `.trae/install.sh`, `.kiro/install.sh`), krokar med eval och miljövariabler,
  en MCP-server via npx (`.mcp.json`) och inherit-legacy-style med breda `allowed-tools`. De 48 ställena med text till
  agenter är i sitt sammanhang säkerhetsguider, testfixturer för en promptinjektionsvakt och granskningsprompter som
  varnar för injektion (`workflows/orch-review.workflow.js:119, 134`). Inget kördes eller installerades
- Förslag: (a) `kor.sh` rad 51–52: Edit- och Write-nekanden för `kontroller/`, `kritik/`, `kunskap/`, `mall/`,
  `.claude/` och `LARDOMAR.md`; sammanfattningen efter körningen säger till om de sökvägarna inte är rena i git;
  `bygg-sajt/SKILL.md:47` får en halv mening om det. (b) A/B på de tre dömda byggena: en granskare mot två isolerade
  (unionen av blockerande fynd), tre körningar per arm och bygge, ägarens fel i L1–L3 som facit, en Sonnet-domare som
  inte vet armen och byter ordning, träffar, falska blockerande fynd, överensstämmelse, tokens och tid
- Utfall: kor.sh nekar Edit och Write i kontroller/, kritik/, kunskap/, mall/, .claude/ och LARDOMAR.md (prövat
  2026-10-02 med en provsession: sju försök nekade, även med absolut sökväg; kunder/ och underlag/ skrivbara).
  Sammanfattningen varnar om de skyddade filerna ändrats under körningen (Bash når förbi reglerna). Två granskare
  vann granskarförsöket 2026-10-02 i alla tre dömda byggen (omdömesfel 3,3 → 4,0 per bygge, alla fel 8,8 → 10,0, inga
  falska blockerande) och körs nu i varje omgång; protokollet i den posten.
- Backlog: B-20261002-byggsessionen-nekas-att-skriva-i-kontroller-krit (ta in);
  B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran (prova A/B)

### 2026-10-02 · react/react · nej
- Källa: https://github.com/react/react @ 7c6ac13 (senaste push 2026-10-01), MIT; cirka 251 000 stjärnor, inte
  arkiverat. Läst: README.md (79 rader), `.claude/instructions.md`, `.claude/skills/verify/SKILL.md`,
  `.claude/skills/fix/SKILL.md`, början av `compiler/.claude/skills/compiler-orchestrator/SKILL.md`, förgranskningens
  rapport och de flaggade ställena. Bilder: README visar bara märken; repot har ikoner och fixturlogor, ingen skärmbild
  eller demo att se. Ägarens not: ingen. Bedömd en gång förut med de gamla reglerna, samma commit och samma dom
  (`kunskap/REGISTER-arkiv-20261001.md:624`); här bedömd på meriter
- Steg: 5 (bygge), i så fall; i arbetssättet de egna verifieringsskillsen
- Jämfört med i dag: (1) Bygget: mallen är statisk Astro med `astro` och `sharp` som enda beroenden
  (`mall/astro/package.json:10–13`), steg 5 kräver "ingen JavaScript som inte behövs" (`bygg-sajt/SKILL.md:202`), och
  byggstandarden säger mindre JavaScript, innehåll och navigation utan JS, förrenderat (`kunskap/byggstandard.md:18,
  25`). Alla tre dömda byggena levererade 0 kB JS, och ägaren räknade det till det bästa (`LARDOMAR.md:31, 56, 87`).
  React är ett klientbibliotek för interaktiva gränssnitt med tillstånd [REPO README.md rad 3–7]; på en
  informationssajt för en hantverkare lägger det på runtime och hydrering utan att något i sajten blir bättre. Sämre.
  (2) Arbetssättet: repots agentskills är bidragsverktyg för React-kärnan, Prettier och lint i följd och sedan Flow
  och tester parallellt via yarn [REPO .claude/skills/verify/SKILL.md rad 15–22], och en Rust-portering av kompilatorn
  [REPO compiler/.claude/skills/compiler-orchestrator/SKILL.md rad 1–8]. Vi har redan ett prov som stoppvakten kör
  och en oberoende granskare (`kontroller/prova.py`, `kontroller/granska.py`); källan har inget utvärderingssteg vi
  saknar. Lika eller inte tillämpligt
- Skäl: källan är källkoden till ett UI-bibliotek, inte en metod, regel eller skill för att bygga bättre sajter
  [REPO README.md rad 3]. Litteraturen står på vår sida: "rule of least power", HTML före JS, och progressive
  enhancement (`kunskap/teoretisk-grund.md:47–48, 119–120`). React skulle krocka med ett medvetet val som ägarens
  domar bekräftat, och ingen dom i `LARDOMAR.md` pekar på en brist som ett klientramverk löser; formulär, bilder och
  tidsaxlar fungerar utan det. Behöver en framtida sajt verklig interaktivitet (bokning med tillstånd, kalkylator)
  är det en enskild ö i Astro, och den frågan tas då, inte nu. Källkritik: README:n beskriver produkten men belägger
  inget mot något vi mäter; den säljer inget utöver sig själv
- Kostnad: inget tas in. Cirka 1,1 miljoner tokens text i repot; som beroende skulle det betyda React, en renderare
  och en Astro-integration i varje bygge, med versionsunderhåll och större JavaScript-last på varje sida
- Säkerhet: förgranskningen HÖG, av mängden: 4 349 skript med eval/exec, nätanrop och miljövariabler i ett stort
  kompilator- och testträd. Sju dolda tecken (nollbredd U+200B) i
  `packages/react-reconciler/src/__tests__/ReactPerformanceTrack-test.js` rad 97 m.fl.; läst i sitt sammanhang står
  tecknet först i förväntade mätnamn i ett test, inte i text till en agent. De tio ställena med text till agenter är
  byggrader i DevTools-README:er och utvecklarskript. Repots egen `.claude/settings.json` har en SessionStart-krok och
  tillåtna yarn-kommandon som bara gäller sessioner startade inne i repot; inget startades där. Inget försök att styra
  granskaren hittades. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · NousResearch/hermes-agent · ta in
- Källa: https://github.com/NousResearch/hermes-agent @ 0a374d1 (ur klonens `.git/shallow`; senaste push
  2026-10-02T12:10Z), MIT (© Nous Research), cirka 251 000 stjärnor, inte arkiverat; cirka 5,2 miljoner tokens text,
  ungefär 210 skills. Förgranskat. Läst själv: README, banner (`assets/banner.png`, bara namnet i pixeltypsnitt), hela
  SKILL.md för humanizer med dess LICENSE och för adversarial-ux-test, samt `scrollcraft/references/uniqueness.md` rad
  1–60, 230–259 och 400–449. Läst i helhet av två subagenter med belägg (domen är min): auteur, claude-design,
  popular-web-designs (SKILL.md och tre av 54 referenser), design-md, impeccable, sketch, scrollcraft, creative-ideation,
  dogfood, grounded-citations, blocked-page-recovery, darwinian-evolver, decision-questionnaire, simple-english,
  hermes-agent-skill-authoring och koden bakom inlärningsslingan. Övriga skills bara som namn och beskrivning
  (finans, ML, spel, hemautomation, blockkedjor). Ingen demosajt; produkten är ett program. Ägarens not: ingen
- Steg: 4 (innehåll), 5.1 (riktning och upptagna val); egen innovation i 5.6 (granskarens kognitiva genomgång)
- Jämfört med i dag: Hermes är en personlig agent med gateway till chattkanaler och en inlärningsslinga som skriver
  egna skills [REPO README.md rad 19, 26], samma slags plattform som openclaw (nej, ovan). Slingan startar en kopia av
  agenten var tionde verktygsiteration och skriver skills utan godkännande [REPO agent/background_review.py rad 1–4,
  440–443; website/docs/user-guide/features/skills.md rad 674–683]; det krockar rakt med att ägarens dom blir en
  textändring av ägarens hand (`LARDOMAR.md:3–6`). Tre delar bär, sak mot sak:
  (1) **humanizer** (Siqi Chen, blader/humanizer v2.5.1, portad med fem tillägg) är en katalog över 34 mönster i
  AI-text med före och efter, byggd på Wikipedias "Signs of AI writing" [REPO skills/creative/humanizer/SKILL.md rad
  18, 645]. Vår regel mot slop är en fraslista med åtta strukturtyper (hälsningsrubrik, tankstreck, utropstecken,
  spegelöppningar m.fl., `kunskap/copy-kontroll.md:12–20`, `kunskap/redaktionellt-pass.md:25`), och "humanisering … är
  en läsning av texten högt, inte en regel om vissa ord" (`copy-kontroll.md:31–32`, steg 4 `bygg-sajt/SKILL.md:171–172`).
  Det ägaren pekade ut i L1–L3 är just det fraslistan inte fångar: rytm och register. "Dagen efter, tre timmar senare"
  som rubrik låter som en copywriter (`LARDOMAR.md:83, 92`), "Firman är två personer, och just nu letar den efter en
  tredje" låter skrivet (`:34`), BRF-meningen låter som en byrå (`:59`). Källan namnger mönstren: dramatisk
  fragmentering och slagfraser [SKILL.md rad 498–508], negationssvansar [rad 218–232], falska spann [rad 257–265],
  kopulaundvikande [rad 205–215], och ett avslutande självprov, "What makes the below so obviously AI generated?"
  [rad 51, 563–566]. Röstkalibreringen mot ett prov av personens egen text [rad 54–68] motsvarar briefens fem
  formuleringar ur deras egna ord (`bygg-sajt/SKILL.md:127`) men gör dem till måttstock för omskrivningen. Smartare och
  sannolikt bättre: en metod för hela texten, inte en lista över ord.
  (2) **scrollcrafts strukturaxel** (Nate Herk, MIT): fyra byggen i fyra branscher fick samma skelett, för att
  "The world changes how a page LOOKS. The grammar changes what a page IS." [REPO
  optional-skills/web-development/scrollcraft/references/uniqueness.md rad 5–24, 26]. Varje bygge skrivs in med sex
  strukturdimensioner (navigering, första vy, sektionsföljd, avslut, signatur) och nästa måste skilja sig på minst fyra
  mot varje tidigare rad, och planen ändras, aldrig loggen [rad 413–435]. Vår `kontroller/upptagna_val.py` visar bara
  typsnitt, färger och toppsektion (`:95`) och en lista över modellens stilval (`:26–37`). Ägarens mall-lukt i alla
  tre byggena var strukturell, inte stilistisk: tjänstelistan som två spalter med rubrik och en mening (`LARDOMAR.md:29,
  78`), sidfotens tre spalter (`:29`), undersidornas sektioner i exakt samma form, rubrik vänster och text höger, och
  omdömeslistan med hårlinjer (`:54`). Riktningarna i steg 5.1 skiljer sig på färg, typsnitt och toppsektion
  (`bygg-sajt/SKILL.md:187–197`), aldrig på resten av sidans form. Källans sätt är bättre och kostar några rader.
  (3) **adversarial-ux-test** (Omni @ Comelse, MIT) går igenom sajten som en namngiven, besvärlig användare med en enda
  uppgift och en situation [REPO optional-skills/dogfood/adversarial-ux-test/SKILL.md rad 43–59] och sorterar sedan
  klagomålen med ett pragmatiskt filter: skulle en kompetent men upptagen besökare ha samma problem är det ett verkligt
  fel [rad 111–128]. Vår granskare gör den kognitiva genomgången som "en förstagångsbesökare i mobilen"
  (`kritik/GRANSKARE.md:50–53`), utan vem eller när. Ägarens sämsta fynd i L1 var en sådan situation, den som sitter med
  mobilen kl 21 och vill skicka en bild (`LARDOMAR.md:32`), efter att granskaren godkänt. Wharton m.fl. (1994) börjar
  genomgången med en beskrivning av användarna (`kunskap/teoretisk-grund.md:133–136` har bara de fyra frågorna). Det
  blir den egna innovationen. Övrigt: popular-web-designs är 54 varumärkens exakta tokens att klistra in, mot "kopiera
  aldrig layout, palett eller typsnitt" (`bygg-sajt/SKILL.md:223`); sämre. auteur och scrollcraft som skills kräver JS,
  genererade bilder eller stockvideo och en intervju (krock med `:20, 70, 202`); auteurs rangordnade jämförelse med
  referensen i gråskala [REPO optional-skills/creative/auteur/references/verify.md rad 132–134] är ett möjligt tillägg
  till JAMFORELSE.md senare. claude-design, design-md, sketch, creative-ideation, dogfood, decision-questionnaire och
  skill-authoring är lika det vi har eller redan intaget. grounded-citations kräver att ett citat kopieras ur den
  sparade sidtexten, aldrig skrivs om [REPO skills/research/grounded-citations/SKILL.md rad 171]; vi kräver omdömen
  ordagrant med källa (`bygg-sajt/SKILL.md:77–78`) men inget prövar det mot källan. Ingen dom visar ett felcitat, så det
  registreras här och föreslås inte nu. impeccable är bara en pekare till ett annat repo och bedöms inte här
- Skäl: som plattform är Hermes fel verktyg av samma skäl som openclaw: en ersättning för vår körmiljö, med
  installation via `curl | bash` [REPO README.md rad 40] och en slinga som ändrar skills obevakat. Men två delar träffar
  exakt det ägaren dömt i alla tre byggena. Humanizer ger byggets steg 4 en metod för rytm och register som fraslistan
  saknar, och den är en sammanhängande katalog som tappar värde om den kokas ned, så den tas in som skill. Krockar att
  namnge: mönster 19 vill ha raka citattecken, men svensk typografi använder ”…”; mönster 26 om bindestreck gäller
  engelska; "Have opinions" och "Let some mess in" [rad 87–99] gäller inte en sajt i verksamhetens röst, och
  exempelomskrivningen hittar på en intervjuad person [rad 602], mot "Hitta aldrig på" (`bygg-sajt/SKILL.md:20–21`).
  Strukturaxeln är en liten textändring i steg 5.1 och i en lista vi redan har, och den följer litteraturens
  designsystemtänkande (`kunskap/teoretisk-grund.md:34–35`) åt rätt håll: formen ska vara ett beslut. Källkritik:
  humanizers mönster är observationer från Wikipedias städprojekt, inte mätningar; exemplen ser ut att vara hämtade ur
  Wikipedia-sidan (CC BY-SA 4.0), så KALLA.md anger den. Scrollcrafts belägg är en anekdot om fyra egna byggen, men den
  stämmer med vår egen erfarenhet i tre. README:n säljer Nous Portal som prenumeration [REPO README.md rad 126–141].
  Inget i det lästa försökte styra kirurgen; agentriktad text i källan är Hermes egna promptar
- Kostnad: humanizer cirka 14 tokens i varje session, cirka 8 500 när bygget använder den i steg 4 och 270 vid behov
  enligt förgranskningen; inga skript, inga beroenden. Kopian följer inte källan. Strukturaxeln kostar några rader i
  `bygg-sajt/SKILL.md` och listan i `upptagna_val.py`, inga tokens utöver det. Den egna innovationen kostar en mening i
  granskarens uppdrag och ett A/B på cirka 18 granskarsessioner
- Säkerhet: förgranskningen HÖG, av mängden: 11 327 skript, 285 ställen med text till agenter och 123 dolda tecken. De
  dolda tecknen ligger, enligt listan, i arabiska lokaliseringsfiler (riktningsstyrning, `locales/ar.yaml`,
  `apps/desktop/src/i18n/ar_boot.ts`), i en indexcache (`skills/index-cache/lobehub_index.json`, nollbreddsfogar) och i
  modelldokumentation för unsloth; inget av det följer med. Text till agenter är i stickproven Hermes egna promptar
  (`agent/background_review.py`). Humanizer har inga skript, inga behörigheter och ingen krok; frontmatterns
  Hermes-fält tas bort. Inget kördes eller installerades
- Förslag: (a) `.claude/skills/humanizer/` med SKILL.md ur `skills/creative/humanizer/` @ 0a374d1, båda licenserna
  (Siqi Chens LICENSE och Nous Researchs) och KALLA.md (källa, commit, Wikipedia-sidan CC BY-SA 4.0, de fem
  Hermes-tilläggen). Ta bort avsnittet "How to use it in Hermes" och frontmatterns `platforms` och `metadata`.
  Beskrivningen säger att bygget använder den i steg 4 på INNEHALL.md efter copykontrollen, och i rapporten. KALLA.md
  namnger krockarna: svenska citattecken ”…”, mönster 26 gäller inte svenska, rösten kommer ur verksamhetens och
  kundernas ord, inget påhittat. En halv mening i `bygg-sajt/SKILL.md:171–172` pekar på den. (b)
  `bygg-sajt/SKILL.md` steg 5.1 (rad 187–197): varje riktning anger också sidans form (hur tjänsterna, beviset,
  undersidornas sektioner, sidfoten och avslutet visas), och den valda formen skrivs i specifikationen med skäl mot de
  upptagna. `kontroller/upptagna_val.py:26–37` får de fyra strukturmönstren ur L1–L3 i listan. Egen innovation (c):
  granskarens kognitiva genomgång (`kritik/GRANSKARE.md:50–53`) görs som en namngiven besökare ur briefens målgrupper,
  med situation, apparat och tid på dygnet, och varje fynd sorteras med frågan om en kompetent men upptagen besökare
  hade fastnat på samma ställe. A/B på de tre dömda byggena mot ägarens fynd i L1–L3 som facit
- Utfall: humanizer intagen 2026-10-02 (547a1df) i `.claude/skills/humanizer/`; bygg-sajt steg 4 pekar på den.
  Prövas i nästa bygge. Granskarens namngivna besökare (egen innovation) prövades i granskarförsöket 2026-10-02: ingen
  skillnad mot dagens text (3,3 mot 3,3 omdömesfel per bygge); avvisad.
- Backlog: B-20261002-ta-in-humanizer-hermes-porten-av-blader-humanize (ta in);
  B-20261002-riktningarna-i-steg-5-1-skiljer-sig-ocksa-pa-sid (ta in);
  B-20261002-a-b-granskarens-kognitiva-genomgang-som-namngive (prova A/B, egen innovation)

### 2026-10-02 · trimstray/the-book-of-secret-knowledge · nej
- Källa: https://github.com/trimstray/the-book-of-secret-knowledge @ 7d37069 (ur klonens `.git/shallow`; senaste push
  2024-11-19, alltså samma revision som förra bedömningen), MIT, cirka 247 000 stjärnor, inte arkiverat. Repot är en
  README på drygt 4 400 rader plus licens, bidragsregler och en bild. Läst: inledningen (rad 1–108), alla
  kapitelrubriker, och i sin helhet Web Tools (rad 443–710), Manuals (rad 835–1015) och Inspiring Lists (rad
  1017–1094). Övriga kapitel (CLI- och GUI-verktyg, system, nät, containrar, bloggar, pentest, enradare för skalet) bara
  som rubriker, och en sökning över hela filen efter design, typografi, UX, tillgänglighet, CSS, SEO, typsnitt och färg
  gav bara träffar i skal-, nät- och säkerhetsposter. Sedd: den enda bilden, en tecknad uppslagen bok med titeln [BILD
  static/img/the-book-of-secret-knowledge-preview.png]. Ingen demo. Bedömd förut med de gamla reglerna
  (`REGISTER-arkiv-20261001.md:655`, nej); arkivet ligger utanför registret, så detta är en ny bedömning med dagens
  regler.
- Steg: inget av de åtta; närmast steg 6 (prov) och lanseringen (fas L i byggstandarden).
- Jämfört med i dag: källan är en länklista med en mening per länk, uttryckligen för systemadministratörer, DevOps och
  pentestare [REPO README.md rad 28, 32]. Det webbnära prövat sak mot sak. (1) Säkerhetshuvuden: securityheaders.com,
  Mozilla Observatory och webhint [rad 491–493] betygsätter svarshuvuden; vi har CSP med hashar i demon
  (`kunskap/byggstandard.md:109`, prövad av `kontroller/standard_kontroll.py:328–335`), rubrikerna i
  `kontroller/prelaunch.py:31` och "säkerhetshuvuden på A-nivå" i lanseringsgrinden (`byggstandard.md:131`), alltså
  redan betygsskalan från securityheaders. Lika; deras tjänster mäter bara en levande adress, och den har vi först vid
  lansering. (2) Prestanda: PageSpeed Insights, web.dev och Lighthouse [rad 588–590] mot `kontroller/lighthouse.mjs` och
  kravet 4.1 (`byggstandard.md:58`). Lika. (3) E-post och DNS: MX Toolbox, DKIM-validatorn och Zonemaster [rad 503,
  524, 528] mot `kunskap/lansering.md:49–64`, som läser SPF, DKIM och DMARC men säger själv att den inte prövar syntax,
  signering eller leverans (rad 59–62). Där vore en extern tjänst ett andra kvitto vid lansering; litet, och inget som
  kräver den här listan. (4) Litteraturen: header-skanning och OWASP ASVS står redan som metoder
  (`kunskap/teoretisk-grund.md:95–99`); källans OWASP-länkar [rad 938–946] pekar på samma ställen. (5) Generatorerna
  föreslår AI-genererade ansikten [rad 641–642], mot "Inga stockbilder" (`.claude/skills/bygg-sajt/SKILL.md:70`) och
  ägarens "hellre inga foton än stock" (`LARDOMAR.md:90`). Sämre.
- Skäl: inget i listan rör det ägarens domar L1–L3 pekar på: förfrågningsvägen, bildunderlaget, förtroendet och
  rösten. Det som rör en lokal verksamhets sajt är mätverktyg för krav vi redan har och mäter, i flera fall med samma
  verktyg, och flera poster är döda eller föråldrade (xip.io och Panopticlick [rad 450, 513], Netcraft märkt otillgänglig
  [rad 546]; senaste push för snart två år sedan). Den kan inte få oss att bygga bättre sajter, och den gör inget
  smartare än det vi gör: den länkar till tjänster som en människa kör för hand. Källkritik: källan säljer inget utom en
  Open Collective-insamling [rad 65–74]; stjärnorna är räckvidd, inte belägg, och urvalet är en persons bokmärken
  [rad 28].
- Kostnad: ingen; inget tas in. Hela källan är cirka 54 500 tokens text enligt förgranskningen; inga skills, skript
  eller beroenden.
- Säkerhet: förgranskningen LÅG över fem textfiler: inga dolda tecken, ingen text riktad till agenter, inga
  behörigheter, krokar eller skript. Innehållet länkar till exploit-, läck- och skanningstjänster, men som listor, inte
  som instruktioner till en agent. Inget kördes eller installerades.
- Förslag: inget
- Utfall: — (behöver en lansering ett andra kvitto på e-postposterna eller säkerhetshuvudena, är MX Toolbox eller
  securityheaders.com ett handkvitto mot den levande adressen enligt `lansering.md` och `prelaunch.md`, inte en ny
  kontroll)
- Backlog: ingen

### 2026-10-02 · deepseek-ai/deepseek-harness · nej
- Källa: https://github.com/deepseek-ai/deepseek-harness @ 639ed01 (ur klonens `.git/shallow`; senaste push
  2026-09-29T09:41Z), MIT, cirka 242 000 stjärnor, inte arkiverat; 14 104 filer, cirka 6,6 miljoner tokens text.
  Förgranskat. Läst: README, SAFETY.md, BENCHMARK.md, AGENTS.md rad 1–60, beskrivningarna för alla 15 skills i
  `.agents/skills/`, hela SKILL.md för dsh-prose-standard (med `references/examples.md` rad 1–50), dsh-trim-cot-leakage
  (med `references/examples.md` rad 1–60), dsh-client-ui-ux, record-browser-gif och agent-experience, samt README för
  `packages/experimental/auto-review`. Bild: `docs/user/guide/providers-models-page.png` (en av fyra; de andra är samma
  inställningsvy i formulär och på kinesiska). Ingen demosajt; produkten är ett program. Ägarens not: ingen
- Steg: inget av de åtta; närmast steg 4 (texten) och backlog-skillen (hur en dom blir text)
- Jämfört med i dag: DeepSeek Harness är en agentkörmiljö där allt är ett tillägg, med webbgränssnitt, sandlåda,
  underagenter och krokar [REPO README.md rad 5–7; AGENTS.md rad 17–60], samma slags ersättning för vår körmiljö som
  openclaw och Hermes (nej respektive bara enskilda skills, ovan). Skillsen i `.agents/skills/` är underhållsverktyg för
  just det kodförrådet (PR-staplar, översättning, CI, prestanda, uppgraderingsguider). Fem delar prövades sak mot sak.
  (1) dsh-prose-standard: räkna upp varje påstående (vem, villkor, ordning, måste/får/aldrig, undantag, följd) innan en
  text kortas, eftersom "A smaller word count alone is not an improvement." [REPO
  .agents/skills/dsh-prose-standard/SKILL.md rad 28–38]. Det gäller kod, JSDoc och agenttexter, och för våra skilltexter
  täcks samma sak av writing-for-agents (en betydelse på ett ställe, rensa sediment) och klassningen av domändringar,
  båda redan vilande poster (mattpocock/skills och obra/superpowers ovan). För sajtens text står strykprovet i
  `bygg-sajt/SKILL.md:224–225`, och ingen dom i `LARDOMAR.md` visar att en strykning tappat en sakuppgift. Lika. (2)
  dsh-trim-cot-leakage: text vars synvinkel är skrivsessionens, inte läsarens (döda hänvisningar, "används inte längre",
  svar till en granskare) [REPO .agents/skills/dsh-trim-cot-leakage/SKILL.md rad 10–23]. För kundtext har vi motsvarande
  fråga, ord som beskriver oss själva eller vår planering (`kunskap/redaktionellt-pass.md:26`); i de byggda sajterna
  finns ingen sådan läcka, bara daterade källrader för omdömen ("läst 1 oktober 2026",
  `kunder/lulea-snickaren/sajt/src/pages/index.astro:100`) som är kvitton enligt `kunskap/copy-kontroll.md:29–30`.
  Lika. (3) dsh-client-ui-ux: tokens, få textstorlekar, båda färgteman, toast mot notis i ett appgränssnitt [REPO
  .agents/skills/dsh-client-ui-ux/SKILL.md rad 12–16, 25–32]; för en statisk sajt täcker byggstandarden 3.1 tokens och
  skala (`kunskap/byggstandard.md:46`), resten gäller appar. Lika eller inte tillämpligt. (4) record-browser-gif spelar
  in en GIF ur en riktig körning till varje PR [REPO .agents/skills/record-browser-gif/SKILL.md rad 12–16]; våra sajter
  har ingen JavaScript och nästan ingen rörelse, och ägaren dömer i dashboarden med skärmbilder. Inget för oss. (5)
  auto-review låter modellen själv godkänna varje verktygsanrop med full åtkomst och säger att den "can allow unsafe
  actions" [REPO packages/experimental/auto-review/README.md rad 12]; vi kör byggen med vitlista och fasta nekanden
  (`kor.sh:38–51`). Sämre
- Skäl: källan hjälper inte oss att bygga bättre sajter. Som plattform krockar den med två medvetna val, att kod ur
  källor inte körs (installation via `npx` eller `pnpm install` [REPO README.md rad 23–39]) och att ingen agent ändrar
  systemet obevakat; projektet säger självt att det är en förhandsversion utan säkerhetsgranskning som kan skada
  värddatorn [REPO SAFETY.md rad 7–9]. Skillsen är välskrivna och ärliga om sina gränser, men de som går att föra över
  (fullständiga påståenden vid strykning, skrivsessionens synvinkel, kontextsnål agenttext) är redan intagna i
  verktygslådan genom tidigare poster eller står i `redaktionellt-pass.md`; ingen av dem rör det ägarens domar L1–L3
  pekar på (förfrågan, bildunderlag, förtroende, rösten). Källkritik: README:n säljer inget; stjärnantalet är räckvidd,
  inte belägg, och BENCHMARK.md hänvisar bara till ett SDK utan resultat [REPO BENCHMARK.md rad 3]
- Kostnad: ingen; inget tas in. Skillsen skulle kosta 52–147 tokens i varje session och 446–4 452 vid användning
  enligt förgranskningen
- Säkerhet: förgranskningen HÖG, av mängden: 4 879 skript (CI, testfixturer, GIF-kodaren med eval/exec, skript med
  nätanrop och miljövariabler). Tio dolda tecken (nollbredd U+200B); läst i sitt sammanhang (`scripts/jsdoc.ts:14`,
  `packages/client/ui-schedule/src/client/task-cron.ts:55`) bryter tecknet `*/` inne i en JSDoc-kommentar, de övriga
  ligger i testfixturer för matematisk markdown. De 100 ställena med text till agenter (60 listade och lästa som sökväg) är källans egen
  systemprompt och dess ögonblicksbilder ("You are an AI"), tester, och säkerhetsnoter om exfiltrering. Krokfilerna
  ligger i provmappar under `snapshots/`. Inget i det lästa försökte styra kirurgen. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · multica-ai/andrej-karpathy-skills · nej
- Källa: https://github.com/multica-ai/andrej-karpathy-skills @ 2c60614 (ur klonens packed-refs; senaste push
  2026-04-20), MIT enligt README och skillens frontmatter men ingen licensfil (`gh` visar ingen licens); cirka 217 000
  stjärnor, inte arkiverat. Läst allt: README, CLAUDE.md, `skills/karpathy-guidelines/SKILL.md`, EXAMPLES.md, CURSOR.md
  och Cursor-regeln är samma text i andra former. Repot har inga bilder och ingen demo. Ägarens not: ingen
- Steg: inget av de åtta direkt; arbetssättet runt dem (hur byggsessionen och backlogsessionen beter sig)
- Jämfört med i dag: källan är en enda regelfil med fyra principer för en kodagent, skriven av en tredje part utifrån
  ett X-inlägg av Karpathy [REPO README.md rad 7, 13–19]. Sak mot sak: (1) "Think before coding" säger: skriv ut
  antagandena, och fråga när något är oklart [REPO SKILL.md rad 17–21]. Våra byggen körs utan människa; saknas en
  uppgift märks den `antagande` och det kunden letar efter beställs i BESTALLNING.md (`.claude/skills/bygg-sajt/SKILL.md:20–24`,
  `:129–134`), och flera tolkningar blir fyra riktningar med en vald (`:187–197`). Antagandedelen är lika; "fråga och
  stanna" krockar med obevakade byggen. (2) "Simplicity first": ingen funktion utöver det som bes om, inga abstraktioner
  för engångskod [REPO SKILL.md rad 25–33]. Vi har det för systemet ("Små ändringar … inte en ny mekanik",
  `CLAUDE.md:27`; `.claude/skills/backlog/SKILL.md:26–27`) och för sajten (så få sidor som toppuppgifterna kräver,
  ingen JavaScript som inte behövs, `bygg-sajt/SKILL.md:122`, `:202`); de tre dömda byggena levererade 0 kB JS
  (`LARDOMAR.md:31`, `:56`). Lika. (3) "Surgical changes": rör bara det som måste, varje ändrad rad ska gå att härleda
  till uppdraget [REPO SKILL.md rad 35–49]. Samma som backlogens "så liten som posten kräver" (`backlog/SKILL.md:26`);
  källans regel att inte städa befintligt dött material säger emot rensningen av inaktuella rader i den intagna
  writing-for-agents (registret ovan, mattpocock/skills). Lika, med en krock. (4) "Goal-driven execution": gör om
  uppgiften till verifierbara mål och slinga tills de håller [REPO SKILL.md rad 51–67]. Vi har det som mekanik:
  EARS-krav som granskaren prövar (`bygg-sajt/SKILL.md:119–121`), provets grindar och granskaren tills godkänt
  (`:226–232`), stoppvakten som inte släpper avslutet (`:324–326`), och varje backlogpost har "Klart när"
  (`kontroller/backlog.py:81–82`). Vårt är starkare
- Skäl: källan är allmänna riktlinjer för en kodagent med en människa vid tangentbordet, och den tillför ingen metod
  vi saknar: tre av fyra principer har vi redan, två av dem som mekanik i stället för text, och den fjärde ("fråga när
  du är osäker") krockar med att våra byggen körs obevakat, där vi medvetet valt antagande plus beställning. Inget i den
  rör det som ägarens domar L1–L3 pekar på (förfrågan, bildunderlag, förtroende, rösten). Källkritik: namnet lånar
  Karpathys auktoritet, men han är inte upphovsman; texten är en tredje parts tolkning av tre citat [REPO README.md rad
  7, 13–19], och README:n gör reklam för upphovsmannens plattform Multica [REPO README.md rad 3]. Effekten är obelagd:
  "How to know it's working" listar bara tecken att själv lägga märke till, inga mätningar [REPO README.md rad 140–147].
  Stjärnantalet är räckvidd, inte belägg
- Kostnad: ingen; inget tas in. Skillen skulle kosta cirka 59 tokens i varje session och 556 vid användning enligt
  förgranskningen
- Säkerhet: förgranskningen LÅG: inga dolda tecken, ingen text riktad till agenter, inga behörigheter, hookar eller
  skript. README:n föreslår installation genom att hämta CLAUDE.md med curl till projektet; inget kördes eller
  installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · vuejs/vue · nej
- Källa: https://github.com/vuejs/vue @ 9e88707 (ur klonens `.git/shallow`; senaste push 2024-10-10), MIT; cirka
  213 000 stjärnor, inte arkiverat men nedlagt: Vue 2.7.16, slut på underhåll 2023-12-31 [REPO README.md rad 1–5;
  package.json rad 3]. Läst: README, förgranskningens rapport och de flaggade ställena i listan. Bilder: README visar
  bara logga, märken och sponsorer; repots enda bild är en testfixtur i server-renderer. Demon sedd som webbsida
  (https://v2.vuejs.org/v2/examples/): första vyn i mobil och desktop, en Markdown-editor och en lista med
  widgetexempel [BILD vue2-examples/desktop-forsta.png, mobil-forsta.png]. Ägarens not: ingen
- Steg: 5 (bygge), i så fall
- Jämfört med i dag: mallen är statisk Astro med `astro` och `sharp` som enda beroenden (`mall/astro/package.json:10–13`),
  steg 5 kräver "ingen JavaScript som inte behövs" (`.claude/skills/bygg-sajt/SKILL.md:202`), och byggstandarden säger
  innehåll och navigation utan JS, förrenderat, helt statiskt (`kunskap/byggstandard.md:18, 25`). De tre dömda byggena
  levererade 0 kB JS, och ägaren räknade det till det bästa (`LARDOMAR.md:31, 56, 87`). Vue 2 är ett klientramverk
  för gränssnitt och ensidesappar [REPO README.md rad 44]; demon visar just det, interaktiva widgetar (editor,
  rutnät, träd) och ingenting om hur en sida för en verksamhet ska se ut eller läsas [BILD desktop-forsta.png]. Dess
  serverrendering löser ett problem vi inte har, eftersom Astro redan förrenderar allt. Sämre för oss, och dessutom
  utan underhåll
- Skäl: källan är källkoden till ett nedlagt UI-ramverk, inte en metod, regel eller skill för att bygga bättre sajter
  eller arbeta smartare. Litteraturen står på vår sida: "rule of least power", HTML före JS, progressive enhancement,
  statisk förrendering och minimal klient-JS (`kunskap/teoretisk-grund.md:47–48, 119`). Att ta in det skulle krocka
  med ett medvetet val som ägarens domar bekräftat, och ingen dom i `LARDOMAR.md` pekar på en brist som ett
  klientramverk löser. Samma bedömning som react/react ovan; skulle en framtida sajt behöva en interaktiv ö (kalkylator,
  bokning med tillstånd) är det en enskild Astro-ö, och då vore Vue 3 (vuejs/core) frågan, inte Vue 2. README:n själv
  avråder från Vue 2 för nya projekt [REPO README.md rad 7]. Källkritik: README:n säljer inget utöver ramverket och en
  betald förlängd support för den som fastnat på Vue 2 [REPO README.md rad 7]
- Kostnad: inget tas in. Cirka 48 000 tokens text (md/txt) enligt förgranskningen; som beroende vore det runtime och
  hydrering på varje sida plus ett ramverk som inte längre får säkerhetsrättelser
- Säkerhet: förgranskningen MEDEL, av mängden: 423 skript, bland dem eval/exec i kompilatorn och serverrenderaren,
  miljövariabler i byggskript och ett nätanrop i ett klassiskt exempel (`examples/classic/commits/app.js`). Inga
  dolda tecken, ingen text riktad till agenter, inga skills, hookar eller behörigheter. Inget försök att styra
  kirurgen. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · anomalyco/opencode · nej
- Källa: https://github.com/anomalyco/opencode @ 1ddb087 (grenen `dev`, ur klonens `.git/refs/heads/dev`; senaste push
  2026-10-02T14:03Z), MIT; cirka 211 000 stjärnor, inte arkiverat; 6 646 filer, cirka 2,1 miljoner tokens text.
  Förgranskat. Läst: README, AGENTS.md, alla åtta kommandon i `.opencode/command/` som namn och i helhet `rmslop.md`
  och `learn.md`, båda skills i `.opencode/skills/` (rtl-aware-development i helhet, effect som beskrivning),
  Anthropic-prompten `packages/opencode/src/session/prompt/anthropic.txt` och namnen på de övriga promptarna. Bild:
  README:ns skärmbild av terminalgränssnittet [BILD packages/web/src/assets/lander/screenshot.png]. Ingen demosajt;
  produkten är ett program. Ägarens not: ingen
- Steg: inget av de åtta; närmast arbetssättet runt dem (körmiljön i `kor.sh`, granskaren, bristposterna)
- Jämfört med i dag: OpenCode är en kodagent i terminalen, på skrivbordet och i webbläsaren, med en agent för bygge med
  full åtkomst och en skrivskyddad för planering [REPO README.md rad 10, 102–110], och med valfri modelleverantör
  (skärmbilden kör Claude Opus genom deras egen tjänst Zen [BILD screenshot.png]). Det är samma slags ersättning för
  Claude Code som openclaw, Hermes och DeepSeek Harness (alla nej som plattform, ovan). Anthropic-prompten är i allt
  väsentligt Claude Codes egen hållning i omskrivning [REPO packages/opencode/src/session/prompt/anthropic.txt rad
  14–21, 70–96]; ingenting nytt för oss. Tre delar prövades sak mot sak. (1) `learn` låter agenten efter en session
  skriva in icke-uppenbara lärdomar direkt i AGENTS.md-filer [REPO .opencode/command/learn.md rad 5–30]. Vi fångar
  samma sak, brister i kontroller, skill eller kunskap, som vilande backlogposter som ägaren släpper
  (`.claude/skills/bygg-sajt/SKILL.md:313–321`), och bygget rör aldrig `kunskap/`, `kontroller/` eller `.claude/`
  (`:47`). Lika i fångst, säkrare i vägen; källans sätt krockar med att ingen agent ändrar systemet obevakat. (2)
  `rmslop` städar AI-slop i kod (överflödiga kommentarer, defensiva kontroller, `any`-omvandlingar, emoji) [REPO
  .opencode/command/rmslop.md rad 5–13], samma sak som openclaws `deslop` (`kunskap/REGISTER.md:74–76`); vår regel
  mot slop gäller sajtens text (`kunskap/copy-kontroll.md`), som den inte berör. Inget för oss. (3)
  rtl-aware-development ger regler för höger-till-vänster: logiska CSS-egenskaper, `dir` och `<bdi>`, spegla bara
  riktad betydelse [REPO .opencode/skills/rtl-aware-development/SKILL.md rad 8–14, 30–36]. Våra sajter är svenska och
  vänster-till-höger, byggstandarden har ingen punkt om skriftriktning (`kunskap/byggstandard.md`, enda träffen på
  "logisk" är tabbordningen rad 69), och ingen dom i `LARDOMAR.md` pekar dit. Skillen gäller dessutom deras
  Electron-app (titelrad, fönsterkontroller) lika mycket som webben
- Skäl: källan hjälper oss inte att bygga bättre sajter. Som körmiljö krockar den med två medvetna val: kod ur källor
  körs inte (installation med `curl | bash`, märkt "YOLO" [REPO README.md rad 48–50]) och ingen agent ändrar systemet
  obevakat (byggagenten har full åtkomst som standard [REPO README.md rad 104]; vi kör med vitlista och nekanden,
  `kor.sh:36–52`). Det som går att lyfta ur repot gör vi redan, säkrare (`learn`), eller rör kod och inte sajtens text
  (`rmslop`), eller gäller en skrift våra kunder inte använder (RTL), och inget rör det ägarens domar L1–L3 pekar på
  (förfrågan, bildunderlag, förtroende, rösten). En tanke som källan väcker, utan ny post: OpenCode är
  leverantörsneutral, och vår granskare kör samma modell som byggaren (`kor.sh:57`, `kontroller/granska.py:546`, båda
  `opus[1m]`) medan A/B-regeln kräver en annan modell som domare (`.claude/skills/kirurg/SKILL.md:161`). Det prövas
  bäst som en tredje arm i den vilande A/B:n om två granskare (B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran)
  med `NWP_GRANSKARE_MODELL`, utan OpenCode och utan ny nyckel. Källkritik: README:n säljer inget direkt men leder till
  den egna betaltjänsten Zen [BILD screenshot.png]; stjärnantalet är räckvidd, inte belägg
- Kostnad: ingen; inget tas in. Skillsen skulle kosta 17–56 tokens i varje session och 674–960 vid användning enligt
  förgranskningen
- Säkerhet: förgranskningen HÖG, av mängden: 2 748 skript (CI, infrastruktur, prestandaprov med eval/exec, nätanrop),
  `curl | sh` i arbetsflöden och översatta README:er. 589 dolda tecken; läst i sitt sammanhang är de nollbreddsfogar i
  persiska översättningar (`packages/app/src/i18n/fa.ts`), dubblerade U+200B ur maskinöversättning i danska och thailändska
  dokument (`packages/web/src/content/docs/da/permissions.mdx:83`, `th/config.mdx:204`) och en emojifog i
  `packages/web/README.md:14`; inget gömmer text. De 30 ställena med text till agenter är källans egna promptar och
  exempel i dokumentationen ("You are an AI" i gitlab-sidorna). Inga behörigheter eller krokar i skillsen. Inget i det
  lästa försökte styra kirurgen. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · n8n-io/n8n · nej
- Källa: https://github.com/n8n-io/n8n @ huvudgrenen klonad 2026-10-02 (senaste push 2026-10-02T14:14Z; commit-id inte
  läst, `git log` nekades i körmiljön), Sustainable Use License 1.0 plus n8n Enterprise License för filer märkta `.ee`;
  cirka 206 000 stjärnor, inte arkiverat; 30 132 filer, cirka 1,06 miljoner tokens text. Förgranskat. Läst: README,
  LICENSE.md i helhet, content-design-skillen i helhet, de flaggade ställena i sitt sammanhang (bland dem
  `post-build-flow/SKILL.md:449`) och namnen och storlekarna på alla 44 skills. Bild: README:ns skärmbild av
  arbetsflödesredigeraren [BILD assets/n8n-screenshot-readme.png]. Licens-FAQ:n på docs.n8n.io gav 404 i både
  `sida.mjs` och WebFetch; tolkningen nedan bygger bara på licenstexten. Ingen demosajt; produkten är en server.
  Ägarens not: ingen
- Steg: inget av de åtta direkt; närmast förfrågans mottagare vid lansering (byggstandard 6.3–6.6) och integrationer
  efter formuläret (bokning, kundregister)
- Jämfört med i dag: n8n är en plattform för arbetsflöden och AI-agenter som man kör själv eller i deras moln, med en
  visuell duk och över 1 500 integrationer [REPO README.md rad 3–16]. Skärmbilden visar en duk där ett chattmeddelande
  går till en AI-agent, sedan till ett villkor och vidare till Slack [BILD n8n-screenshot-readme.png]. Hos oss är det
  enda flöde en sajt behöver i dag förfrågan: en serverfunktion på `/api/forfragan` som validerar, stoppar spam och
  skickar ett mejl, med samma kontrakt som demomottagaren (`kunskap/forfragan.md:28–41`). För kontaktformulär är
  standardvägen en befintlig formtjänst eller Tally (`kunskap/integrationer-standardvagar.md:23`), och regeln är att
  välja lägsta nivå som uppfyller behovet (`kunskap/integrationer.md:26–27`). Med n8n skulle samma sju steg bli en
  webhook till en n8n-server som någon måste köra, uppdatera och säkerhetskopiera, eller ett betalt molnkonto. Det är
  fler delar för samma mejl, och kunden får en ny tjänst att ansvara för. Sämre för våra kunder, som är små
  hantverksfirmor. Content-design-skillen har bra regler för text i gränssnitt: ett felmeddelande säger vad som hände
  och vad man gör nu, det skyller inte på användaren, och knappar börjar med ett verb [REPO
  .agents/skills/content-design/SKILL.md rad 210–227]. Men reglerna gäller amerikansk engelska och n8n:s egen ordlista
  (Oxfordkomma, sammandragningar, "n8n" med gemener) [rad 118, 137–143, 254–278]. Det som går att använda för en svensk
  sajt med tre fält bygger på GOV.UK, som vi redan läser (`kunskap/teoretisk-grund.md:84–86`). Lika i sak, och ingen
  dom pekar på en brist i formulärets text
- Skäl: n8n är en bra produkt för den som behöver automatisera många system, men det hjälper oss inte att bygga bättre
  sajter, och det är inte smartare för oss. Det skulle göra förfrågan, vårt enda flöde, tyngre än den lösning som redan
  är bestämd, och för en tvåmannafirma innebär det en server att driva. Det går emot vår regel om lägsta nivå och om
  kundens befintliga system (`kunskap/integrationer.md:26–27, 46–50`). Licensen tillåter bruk "only for your own
  internal business purposes or for non-commercial or personal use" [REPO LICENSE.md rad 32], och vidarespridning bara
  utan avgift och utan kommersiellt syfte [rad 33–34]. Därför går det varken att ta in en skill i vårt publika repo
  eller att köra n8n åt kunder som en del av en betald leverans, utan att först få licensen klarlagd. Kör en kund redan
  n8n, är det ett befintligt system som integrationsreglerna redan täcker. Ingen dom i `LARDOMAR.md` pekar på
  automation. Källkritik: README:n säljer molntjänsten och "Enterprise-Ready AI" [REPO README.md rad 5, 15]; 1 500
  integrationer och 9 000 mallar är antal och säger inget om kvalitet
- Kostnad: ingen; inget tas in. Som väg för mottagaren vore det en server eller ett molnabonnemang per kund, med
  uppdateringar, säkerhetskopior och licensfrågan, i stället för en serverfunktion
- Säkerhet: förgranskningen HÖG, av mängden: 22 352 skript, med `curl | sh` i README och `docker/get-n8n.sh`, nätanrop och
  hemligheter i codespaces-skripten, och en krok i `.claude/settings.json` som kör ett node-skript efter varje
  skillanrop. De 1 499 dolda tecknen är nollbreddsfogar i emojidata (`N8nIconPicker/emojiData.ts`) och avsiktliga
  testfall för sanering och trunkering (`sanitize-web-content.test.ts`, `truncate.test.ts`). De 84 ställena med text
  till agenter är n8n:s egna produktpromptar och provfall för skydd mot promptinjektion ("IGNORE PREVIOUS
  INSTRUCTIONS" i `sanitize-mcp-schemas.test.ts`). Inget av det gömmer text eller riktar sig till kirurgen. Sex skills
  ger sig själva behörigheter i frontmatter (Bash för gh, git, node). Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · ultraworkers/claw-code · nej
- Källa: https://github.com/ultraworkers/claw-code @ 08106b0 (ur klonens `.git/shallow`; senaste push
  2026-08-16T06:18Z), MIT; cirka 195 000 stjärnor, inte arkiverat; 277 textfiler, cirka 540 000 tokens text, ingen
  SKILL.md. Förgranskat. Läst: README, PHILOSOPHY.md, CLAUDE.md, `docs/anti-slop-triage.md` i helhet, USAGE.md:s
  avsnitt om skills (rad 493–533), det flaggade stället i ROADMAP.md (rad 3068–3079) och namnen på alla dokument i
  `docs/`. Bild: README:ns hjältebild [BILD assets/claw-hero.jpeg], en röd pixelfigur utan information. Ingen
  demosajt; produkten är ett kommandoradsprogram. Ägarens not: ingen
- Steg: inget av de åtta; närmast arbetssättet runt dem (körmiljön i `kor.sh`, kirurgens domklasser)
- Jämfört med i dag: claw-code är en omskrivning i Rust av en kodagent i terminalen i Claude Codes form, med en
  Python-arbetsyta för paritetskontroll bredvid [REPO README.md rad 96–111], och kräver en API-nyckel, inte en
  prenumeration [rad 129–130, 261]. README:n kallar själv repot en museiutställning, inte det seriösa projektet, och
  skickar den som vill arbeta vidare till två andra verktyg [REPO README.md rad 54–60]. Filosofin är att människan
  styr från en Discord-kanal och att agenterna planerar, kodar, granskar och pushar utan att någon tittar [REPO
  PHILOSOPHY.md rad 19–25]. Det är samma slags ersättning för Claude Code som opencode, openclaw, Hermes och DeepSeek
  Harness (alla nej som plattform, ovan). Vi kör Claude Code med vitlista och nekanden (`kor.sh:38–51`), och en
  oberoende granskare dömer innan stoppvakten släpper bygget (CLAUDE.md, `kontroller/granska.py`). Det enda som gick
  att pröva sak mot sak är triagelistan mot slop i ärenden och PR:er: nio klasser, var och en med krav på belägg,
  och regeln att automatiken inte stänger eller slår ihop något, bara föreslår [REPO docs/anti-slop-triage.md rad
  7–29]. Kirurgen har redan fyra domklasser med samma skärpa (`.claude/skills/kirurg/SKILL.md:135`), krav på belägg
  för varje påstående och fil och rad för "redan har" (`:164–167`), och backloggen genomförs bara när ägaren släpper
  den. Lika; listan rör kodärenden, inte sajter
- Skäl: källan hjälper oss inte att bygga bättre sajter eller arbeta smartare. Som körmiljö krockar den med två
  medvetna val: kod ur källor körs inte (bygge ur källkod med cargo, och en installatör med `curl | sh`
  [förgranskningen, install.sh]) och ingen agent ändrar systemet obevakat (filosofin är just människan utanför
  slingan [REPO PHILOSOPHY.md rad 23–25]). Den byter dessutom prenumerationen mot API-nyckel utan att ge något vi
  saknar. Triagelistan är välgjord men överlappar kirurgens domklasser och beläggregel, och ingen dom i
  `LARDOMAR.md` pekar dit. Källkritik: stjärnorna speglar uppmärksamhet kring en omskrivning av Claude Code, inte
  kvalitet; README:n säger själv att det är en utställning och leder vidare till syskonprojekt och Discord
- Kostnad: ingen; inget tas in
- Säkerhet: förgranskningen HÖG, av mängden och av `install.sh` (`curl | sh`, nätanrop, skriver utanför repot) samt
  skript med eval/exec för paritetsprov. Inga dolda tecken. Det enda stället med text till agenter
  ("exfiltrat", ROADMAP.md:3074) är en felbeskrivning om hur en krok i arbetsytans inställningar kan läcka verktygsanrop,
  inte en instruktion. Två exempelpluginer har krokar före och efter verktygsanrop
  (`rust/crates/plugins/bundled/*/.claude-plugin/plugin.json`). Inget i det lästa försökte styra kirurgen. Inget
  kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · firecrawl/firecrawl · nej
- Källa: https://github.com/firecrawl/firecrawl @ 2ffb1ab (ur klonens `.git/shallow`; senaste push 2026-10-02T14:19Z),
  AGPL-3.0 för tjänsten, MIT för SDK:erna; cirka 188 000 stjärnor, inte arkiverat; 1 649 textfiler, cirka 167 000 tokens
  text. Förgranskat. Läst: README i helhet, `skills/firecrawl-build/SKILL.md` i helhet och namnen på alla fem skills,
  typerna för varumärkesutdragningen (`apps/api/src/lib/branding/types.ts`), skyddet mot promptinjektion
  (`apps/api/src/scraper/scrapeURL/lib/promptInjectionGuard.ts`) och tjänstelistan i `docker-compose.yaml`. Bild:
  jämförelsen öppen källkod mot moln [BILD img/open-source-cloud.png]. Ingen demosajt; produkten är ett API. Ägarens
  not: ingen
- Steg: 1 (hämta det publika, innehållsinventering) och 2 (diagnos av nuvarande sajt)
- Jämfört med i dag: Firecrawl gör en webbsida till markdown, JSON eller skärmbild, hittar alla adresser på en sajt
  (map), hämtar en hel sajt (crawl) och söker på webben [REPO README.md rad 67–82]. Det körs som molntjänst med
  API-nyckel och krediter [rad 88, 447–448] eller självhostat som sju tjänster: api, playwright, redis, rabbitmq,
  postgres och två för foundationdb [REPO docker-compose.yaml rad 63–215]. Robotskydd, proxyrotation och klick finns
  bara i molnet [BILD open-source-cloud.png]. Varumärkesutdragningen samlar färger, typsnitt, knappar och
  logotypkandidater och låter en språkmodell välja [REPO apps/api/src/lib/branding/types.ts rad 47–103]. Hos oss
  hämtar steg 1 deras sajt med WebFetch och curl (`.claude/skills/bygg-sajt/SKILL.md:64–69`), steg 2 mäter med axe,
  Lighthouse och vår inspektion i 390 och 1440 px (`:87–91`), och kirurgen ser en sida med `kontroller/sida.mjs`
  (text, skärmbilder, designfakta). Våra kunder är små firmor med få sidor (sundboms-el: 16 sidor i
  `underlag/sundboms-el/kalla/`). Det Firecrawl gör bättre än oss är att hitta alla
  adresser själv och ge samma utdata varje gång. I dag skriver varje bygge sina egna hämt- och lässkript: sundboms-el
  med en handskriven sidlista (`underlag/sundboms-el/skript/hamta.py:4–8`), paint-it-black med en egen HTML-läsare
  (`underlag/paint-it-black-maleri/skript/las.py`), lulea-snickaren-abx och -aby med var sin `hamta.py` och `las.py`,
  och sundboms-el med egna skript för logotypens färg och typsnitt (`farg.mjs`, `typsnitt.py`). Som verktyg är Firecrawl sämre för oss än det vi har, men det pekar på
  något vi gör onödigt omständligt
- Skäl: Firecrawl löser problem vi inte har (robotskydd, proxyer, tusentals sidor, data till appar), och det skulle
  antingen skicka kundens sajt och en nyckel till en betald tredjepart eller kräva en server med sju tjänster för att
  läsa en hantverkares tio sidor. Det krockar med "kod ur källor körs inte" och ger inget vi saknar i kvalitet; ingen dom
  i `LARDOMAR.md` pekar på att underlaget missat något. Skyddet mot promptinjektion är välskrivet (sidinnehåll är
  aldrig instruktioner, slumpad tagg runt det), men kirurgen har samma regel i text och `granska_repo.py` som verktyg.
  Lärdomen som är värd något är metoden, inte verktyget: hitta sajtens adresser via sitemap och interna länkar och
  hämta dem med ett gemensamt verktyg, så att innehållsinventeringen i steg 1 (Halvorson & Rach 2012,
  `kunskap/teoretisk-grund.md:29–31`) blir densamma i varje bygge; det ligger som egen post i backloggen. Källkritik:
  README:n säljer molnet ("Covers 96% of the web", "P95 latency of 3.4s" [REPO README.md rad 54–55], belagt bara med
  egen blogg). Den innehåller också text till agenter som ber dem registrera användaren och hämta en API-nyckel [rad
  302–308]; noterad, inte följd
- Kostnad: ingen; inget tas in. Som verktyg vore det API-krediter per bygge eller en självhostad tjänstestack att
  underhålla
- Säkerhet: förgranskningen HÖG, av mängden: 1 332 skript med nätanrop, eval och miljövariabler, och `curl | sh` i
  `apps/api/Dockerfile` och två exempel. De tre dolda tecknen är riktningsmarkörer i landsnamn
  (`apps/api/src/lib/validate-country.ts:204, 583, 1225`). De elva ställena med text till agenter är installationsrader i
  README:er, testfall för injektionsskyddet och skyddets egen systemprompt; inget riktar sig till kirurgen utom README:ns
  uppmaning till agenter ovan. Skills utan behörigheter i frontmatter, inga hookar. Inget kördes eller installerades
- Förslag: inget för Firecrawl. Egen innovation: ett gemensamt hämtverktyg för steg 1 (se backlog)
- Utfall: `kontroller/hamta_sajt.py` 2026-10-02; på sundbomsel.se 40 sidor (alla 15 i byggets handskrivna lista, plus
  start, gdpr och en jobbannons), 72 bilder och fem kontaktvägar på 1 min 37 s. bygg-sajt steg 1 pekar på verktyget.
- Backlog: B-20261002-ett-gemensamt-hamtverktyg-for-kundens-nuvarande (egen innovation)

### 2026-10-02 · avelino/awesome-go · nej
- Källa: https://github.com/avelino/awesome-go @ c4657b2 (ur klonens packed-refs; senaste push 2026-10-02T13:24Z),
  MIT. Läst: README:ns innehållsförteckning (cirka 140 avsnitt, 4 100 rader) och i detalj de webbnära avsnitten
  (Email, Forms, Images, Template Engines, Selenium and browser control tools, länkkontrollen muffet och de statiska
  sajtbyggarna hugo och zs), AGENTS.md, CONTRIBUTING.md och huvudet i `.github/scripts/check-quality/main.go`;
  sökning i `.github/` efter kontrollen mot säljande beskrivningar. Inga skills. awesome-go.com sedd med `sida.mjs`:
  första vyn i mobil och desktop och skrollbild 2 av 8 lästa.
- Steg: inget av de åtta; närmast steg 5 (bygget) och kontrollerna.
- Jämfört med i dag: samma sorts källa som vinta/awesome-python (posten ovan, dömd nej, ägaren höll med
  `kunskap/KIRURG-OMDOMEN.md:15–18`), men för Go: en lista över Go-bibliotek för den som skriver Go-program. Vi
  bygger statisk Astro med Node-kontroller och Python-verktyg (`kunskap/byggstandard.md:3–4`, avsnitt 11 rad 133).
  Sak mot sak i de webbnära delarna: formulärbiblioteken och CSRF-skydden [REPO README.md rad 1328–1343] gäller en
  Go-server, våra formulär tas emot av en demomottagare (`kunskap/byggstandard.md:3–4`, punkt 6.1 rad 84); bildverktygen
  [rad 1582–1630] ersätts hos oss av `astro:assets` (punkt 4.2 rad 59, avsnitt 11 rad 135); länkkontrollen muffet [rad
  608] gör det `kontroller/seo_kontroll.py:6` redan gör (interna länkar som löser); webbläsarstyrning [rad 2770–2777]
  har vi i Playwright via `kontroller/sida.mjs` och `kontroller/webblasare/`. Inget av det är bättre eller smartare för
  vår stack; att byta språk för ett enskilt verktyg vore sämre. Det enda metodnära är listans regel att beskrivningar
  ska vara korta och utan säljord [REPO CONTRIBUTING.md rad 35, 100]; vår regel mot slop är skarpare och gäller svensk
  kundtext (`kunskap/copy-kontroll.md:12–13, 19`). Lika eller sämre
- Skäl: listan svarar på "vilket Go-bibliotek ska jag använda", en fråga våra byggen aldrig ställer, och ingen post
  hjälper med det ägarens domar L1–L3 pekar på (skriftlig förfrågan, bildunderlag, förtroendekvitton). Hantverket runt
  listan är granskning av inskickade bidrag (en post per PR, alfabetisk ordning, krav på licens, release och
  testtäckning [REPO CONTRIBUTING.md rad 28–40, 72–88]), alltså förvaltning av en öppen lista, inte sajtbygge. Sajten
  är en lång rå lista med märken, Product Hunt-ruta och sponsorband först [BILD desktop-forsta.png; BILD
  mobil-forsta.png]; som designreferens säger den oss inget. Källkritik: CONTRIBUTING.md listar en automatisk varning för
  säljande beskrivningar [rad 100], men ingen sådan kontroll finns i `.github/`, och en post som "The simplest but
  powerful way" syns på sajten [BILD desktop-skroll-02.png]; regeln står i text men verkställs för hand. AGENTS.md
  riktar sig till agenter men gäller bara bidrag till repot själv och försökte inte styra kirurgen
- Kostnad: ingen; inget tas in. Hela källan är cirka 113 000 tokens text enligt förgranskningen; inga skills
- Säkerhet: förgranskningen LÅG: inga dolda tecken, ingen text riktad till agenter utöver AGENTS.md, inga behörigheter,
  hookar eller skills. Förgranskningen räknar inte Go-filer som skript; det finns två Go-program i `.github/scripts/`
  som anropar GitHub, pkg.go.dev och Go Report Card, och en sajtbyggare i `main.go`. Inget kördes
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · getify/You-Dont-Know-JS · nej
- Källa: https://github.com/getify/You-Dont-Know-JS @ 044120e (grenen 2nd-ed, ur klonens `.git/shallow`; senaste push
  2026-02-15), CC BY-NC-ND 4.0 [REPO LICENSE.txt; README.md rad 63–65]. Läst: README, förordet `preface.md`,
  innehållsförteckningarna för alla sex böcker, förgranskningens flaggade ställen i sitt sammanhang
  (`objects-classes/ch3.md:1078–1104`, `types-grammar/ch1.md:481–488`, `types-grammar/ch2.md:256`). Kapiteltexten
  (cirka 236 000 tokens) lästes inte i sin helhet; innehållsförteckningarna räckte för att se vad den handlar om. Två
  bilder sedda: `get-started/images/fig1.png` och `fixed-it-for-you.png`. Inga skills, ingen demosajt.
- Steg: inget av de åtta; närmast steg 5 (bygget), och där bara den lilla del som är JavaScript.
- Jämfört med i dag: en bokserie för yrkesprogrammerare om JavaScript-språkets inre (räckvidd och closures,
  prototyper, `this`, klasser, typer och typomvandling [REPO get-started/toc.md, scope-closures/toc.md,
  objects-classes/toc.md, types-grammar/toc.md]), skriven för den som redan har 6–9 månaders JS-erfarenhet [REPO
  preface.md rad 10]. Våra sajter är statisk Astro där innehåll och navigation fungerar utan JS
  (`kunskap/byggstandard.md:18`, punkt 1.1 rad 25), bygget lägger "ingen JavaScript som inte behövs"
  (`.claude/skills/bygg-sajt/SKILL.md:202`) och de dömda byggena hade 0 kB JS (`LARDOMAR.md:31`). Den enda JS i
  mallen är nio rader för tidsfällan och den låsta knappen i förfrågningsformuläret
  (`mall/astro/src/components/Forfragan.astro:42–52`). Boken kan inte göra den bättre; den handlar om språkets
  mekanik, inte om webben, tillgänglighet eller konvertering. Inte jämförbart med något vi gör; för vår stack lika
  eller sämre än det vi redan har
- Skäl: källan svarar på "hur fungerar JavaScript under huven", en fråga våra byggen medvetet undviker att behöva ställa
  genom att hålla JS borta ("rule of least power", `kunskap/teoretisk-grund.md:47–48`). Inget i ägarens domar L1–L3
  (skriftlig förfrågan, bildunderlag, förtroendekvitton, träffytor, og:image) har med språkkunskap att göra. Principen
  om minsta exponering för räckvidd [REPO scope-closures/toc.md rad 37, 49] är god programmering men tillför inget som
  inte redan följer av att vi nästan inte skriver JS. Licensen (ingen bearbetning, inget kommersiellt bruk) utesluter
  dessutom att boken kokas ned till en text eller skill i verktygslådan. Källkritik: välrenommerad och ärlig om sig
  själv (två av sex böcker inställda, två är utkast [REPO README.md rad 17–23]); README:n gör reklam för sponsorn
  [rad 47–57] men säljer inget till oss. Ägarens tidigare domar över språk- och ramverkskällor utan koppling till
  sajtbygget (react/react, vuejs/vue, vinta/awesome-python, `kunskap/KIRURG-OMDOMEN.md:15–18, 35–38, 60–63`) var nej
  och höll
- Kostnad: ingen; inget tas in. Hela källan är cirka 236 000 tokens text enligt förgranskningen; inga skills
- Säkerhet: förgranskningen HÖG, men alla fynd är ofarliga i sitt sammanhang: de nio dolda tecknen är nollbreddsfogar
  (U+200D) inuti familje-emojin som boken använder för att förklara grafemkluster (`types-grammar/ch1.md:481, 488`,
  `ch2.md:256`), och de tre träffarna "text till agenter" är ordet "exfiltration" i ett avsnitt om privata klassfält
  (`objects-classes/ch3.md:1078–1100`). Inga skript, hookar, behörigheter eller skills; inget försök att styra
  kirurgen. Inget kördes
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · anthropics/skills · nej
- Källa: https://github.com/anthropics/skills @ 8a1541c (ur klonens `.git/shallow`; senaste push 2026-09-29T02:20Z),
  Apache-2.0 per skill (`skills/*/LICENSE.txt`; docx, pdf, pptx och xlsx är "source-available", inte öppen källkod
  [REPO README.md rad 20]); `gh` visar ingen licens för repot som helhet; cirka 179 000 stjärnor, inte arkiverat.
  Förgranskat. Läst: README, hela SKILL.md för frontend-design, skill-creator (med `agents/comparator.md`,
  `grader.md`, `analyzer.md`), webapp-testing, theme-factory, discernment-nudge, academy-guide och canvas-design.
  Övriga elva (docx, pdf, pptx, xlsx, claude-api, mcp-builder, brand-guidelines, internal-comms, doc-coauthoring,
  slack-gif-creator, algorithmic-art, web-artifacts-builder) bara som namn, beskrivning och storlek i förgranskningen.
  Repot har inga bilder och ingen demosajt. Ägarens not: ingen
- Steg: 5 (frontend-design läses redan där); i arbetssättet hur skilltexter prövas (backlog-skillen, A/B) och steg 7
  (brister i verktygen, den egna innovationen)
- Jämfört med i dag: källan är Anthropics exempelsamling för skills [REPO README.md rad 16–18], uttryckligen för
  demonstration och utbildning [rad 24]. Sak mot sak: (1) **frontend-design** är ordagrant samma text som
  `kunskap/externa/anthropic-frontend-design-SKILL.md` (alla 72 rader jämförda), som steg 5 redan läser
  (`.claude/skills/bygg-sajt/SKILL.md:177`); vår kopia är alltså aktuell. Lika. (2) **skill-creator** är en slinga för
  att skriva och mäta skills: varje testfråga körs med och utan skillen i samma tur, en betygsättare prövar påståenden,
  ett resultat visas för människan i en webbvy och hennes återkoppling styr nästa version [REPO
  skills/skill-creator/SKILL.md rad 10–20, 169–186, 236–251]. Vår A/B-regel kräver samma indata, flera körningar per
  arm, blind parvis jämförelse med ombytt ordning där oenighet blir oavgjort, och en annan modell som domare
  (`.claude/skills/kirurg/SKILL.md:159–162`), och mikroprovet av domändringar (gamla mot nya texten, fem subagenter per
  arm) ligger redan i backloggen (B-20261002-mikroprova-en-domandring-mot-en-kontroll-utan-an). Källans blinda
  jämförare är valfri [SKILL.md rad 325–329], byter inte ordning och ska undvika oavgjort ("ties should be rare")
  [REPO agents/comparator.md rad 85]; vår regel är strängare. Betygsättarens krav att också döma själva provet, så att
  ett påstående som skulle passera även för fel utfall flaggas [REPO agents/grader.md rad 9, 68–79], är samma sak som
  mikroprovets regel att en kontroll där gamla texten inte visar felet inte bevisar något. Lika. Beskrivnings-
  optimeringen (20 frågor som ska och inte ska utlösa skillen, 60/40 tränings- och testdelning, tre körningar per
  fråga [SKILL.md rad 333–404]) blir värdefull den dag verktygslådan har många skills som byggen hittar på
  beskrivningen (`bygg-sajt/SKILL.md:44–45`); i dag finns inga där, och de två som ska in pekas ut uttryckligen.
  (3) **webapp-testing** skriver Playwright-skript från fall till fall [REPO skills/webapp-testing/SKILL.md rad 9–33];
  vi har färdiga kontroller för samma sak (`kontroller/webblasare/inspektera.mjs`, `axe.mjs`, `lighthouse.mjs`, provet).
  Sämre för oss. (4) **theme-factory** applicerar ett av tio färdiga teman [REPO skills/theme-factory/SKILL.md rad
  28–41], **canvas-design** gör affischkonst ur en påhittad "rörelse" [REPO skills/canvas-design/SKILL.md rad 35–51];
  båda krockar med att formen härleds ur verksamhetens eget material (`bygg-sajt/SKILL.md:187–189`). **discernment-
  nudge** och **academy-guide** gäller svar till en användare i chatten. Inget för oss.
- Skäl: det som bär i källan har vi redan: frontend-design ordagrant i steg 5, och skill-creators mätslinga i en
  strängare form i A/B-regeln och mikroprovsposten. Resten är dokumentverktyg, API-referens, konst och chattbeteende,
  eller krockar med medvetna val: en människa i slingan [SKILL.md rad 143, 251], skript som körs ur källan
  (`run_eval.py`, `run_loop.py` [SKILL.md rad 382–388]) och färdiga teman i stället för verksamhetens egna färger. Men
  en princip i skill-creator gäller oss direkt: läs körningarna, och skriver flera körningar var sitt likadant
  hjälpskript är det signalen att verktyget ska ha det [SKILL.md rad 304]. Hos oss har det redan hänt: tre byggen
  skrev var sitt skript för LCP, CLS, TBT och sidvikt ur Lighthouse-filerna (`underlag/sundboms-el/skript/lh.py`,
  `underlag/lulea-snickaren-abx/skript/lh.py`, `underlag/paint-it-black-maleri/skript/lh_sammandrag.py`), eftersom
  `kontroller/lighthouse.mjs` bara skriver ut P, A, BP och SEO (rad 63) och inte sparar sidvikten (rad 37–44). Inget
  av byggena lade en post; stycket Brister i verktygen nämner bara kontroller, skillen och kunskapsfiler
  (`bygg-sajt/SKILL.md:313–315`). Det blir den egna innovationen. Källkritik: Anthropics egen samling, ärlig om att den
  är exempel [README.md rad 24]; README:n ber läsaren installera repot som plugin [rad 33–49], vilket inte gjordes.
  skill-creators betoning ("billions a year in economic value" [SKILL.md rad 306], versaler i Cowork-avsnittet [rad
  451]) är prompthantverk, inte belägg
- Kostnad: inget tas in. frontend-design kostar redan cirka 2 300 tokens per bygge i steg 5 enligt förgranskningen.
  Hela källan är cirka 577 000 tokens text, varav claude-api ensam cirka 440 000 vid behov. Den egna innovationen är
  en mening i `bygg-sajt/SKILL.md`, och en backlogpost per allmänt skript ett bygge skriver
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, inga behörigheter i frontmatter, inga hookar eller MCP. Sju
  ställen med text till agenter, alla ofarliga i sitt sammanhang: säkerhetsregeln i skill-creator ("Principle of Lack
  of Surprise", SKILL.md rad 113), dess egen mall för subagenternas uppgift (rad 176), en API-guide som avråder från
  instruktioner som åsidosätter användaren (`claude-api/shared/model-migration.md:858`), ett råd om att inte tvinga på
  användaren ett format (`claude-api/shared/evals/build-eval.md:227`) och exfiltrationsvarningar i säkerhetsavsnitt.
  77 skript (Office-validerare, eval-körare med `claude -p`, en serverhanterare med exec); inget kördes eller
  installerades. Inget försök att styra kirurgen
- Förslag: inget ur källan. Egen innovation: `.claude/skills/bygg-sajt/SKILL.md` steg 7, Brister i verktygen (rad
  313–315): ett skript i `underlag/<slug>/skript/` som inte är knutet till verksamheten (läser en kontrolls utdata,
  hämtar bilder, räknar något) är också en brist i verktygen; posten anger skriptets sökväg och vilken kontroll som
  borde ha gjort det
- Utfall: —
- Backlog: B-20261002-ett-allmant-hjalpskript-som-bygget-skrev-i-under (egen innovation)

### 2026-10-02 · github/gitignore · nej
- Källa: https://github.com/github/gitignore @ 62f3997 (main, senaste push 2026-09-28), CC0-1.0; läste README,
  förgranskningen och de mallar som rör vår stack (`Node.gitignore` helt), resten som fillista. Inga bilder eller demo
  i repot
- Steg: inget av de åtta; möjligen arbetssättet runt dem (repots egen `.gitignore`) och lanseringen (kundrepot)
- Jämfört med i dag: vår `.gitignore` håller redan det byggena faktiskt skapar: `underlag/` och `kunder/` (rad 2–3),
  `.venv/`, `node_modules/`, `dist/`, `.astro/` (rad 6–9), `.DS_Store` och Python-cache (rad 12–14). Källans
  `Node.gitignore` täcker samma sak [REPO Node.gitignore rad 41, 83, 146] plus ett fyrtiotal verktyg vi inte använder
  (Next, Nuxt, Gatsby, Yarn, Firebase m.fl.). Det enda den har som vi saknar är `.env`-mönstren [REPO Node.gitignore
  rad 68–71], men inget i repot läser en `.env` (sökningen träffar bara `.env.example`-kravet i `kunskap/prelaunch.md:10`,
  `kunskap/bygge-referens.md:35` och `kontroller/prelaunch.py:57`), och byggena, där en formulärnyckel skulle kunna
  hamna, ligger redan i ignorerade `kunder/`. Lika för vårt bruk, inte bättre
- Skäl: en mallsamling för GitHubs väljare när man skapar ett repo [REPO README.md rad 3–5], inte en metod. Den gör
  inga sajter bättre och sparar inget steg: vårt repo ignorerar redan det vi producerar, och den dag ett kundrepo skapas
  enligt "GitHub-först" (`kunskap/bygge-referens.md:41`) erbjuder GitHub samma Node-mall direkt när repot skapas, så
  inget behöver tas in i förväg. Källan är saklig och säljer inget
- Kostnad: ingen; källan är cirka 4 100 tokens text enligt förgranskningen, inga beroenden
- Säkerhet: förgranskningen LÅG: inga dolda tecken, ingen text till agenter, inga skript, hookar eller behörigheter.
  Inget kördes
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · twbs/bootstrap · nej
- Källa: https://github.com/twbs/bootstrap @ c1f9b9d (main, senaste push 2026-10-01), MIT (dokumentationen CC BY 3.0);
  läste README, förgranskningen, fillistan för `scss/`, standardvärdena i `scss/_variables.scss` och de flaggade
  ställena i `js/src/`. Såg exempelsidan getbootstrap.com/docs/5.3/examples/ med `sida.mjs`: mobilens första vy och
  två av åtta skrollägen på desktop
- Steg: 5 (koncept och bygge); möjligen mallen `mall/astro/`
- Jämfört med i dag: vår mall har medvetet ingen design: `mall/astro/src/layouts/Bas.astro` rad 2–3 säger att all
  design, typografi och struktur skrivs för just den verksamheten, och steg 5 härleder fyra riktningar ur verksamheten,
  "aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md` rad 187–188). Bootstrap ger färdiga komponenter och
  standardval: blå `$primary`, radie .375rem, systemtypsnitt [REPO scss/_variables.scss rad 301, 547, 606], och
  exempelsidan säljer just de sektionsmallar (Headers, Heroes, Features, Jumbotrons) som byggena ska undvika [BILD
  desktop-skroll-02.png, desktop-skroll-03.png]. Ägaren har dömt byggena 4–5 på "gjord för verksamheten" och pekat ut
  just generiska mönster som det som luktar mall (`LARDOMAR.md` rad 29, 54, 78); de byggena väger 4–10 kB CSS och 0 kB
  JS (rad 31, 56, 87). Sämre för oss
- Skäl: Bootstrap är ett välskött och tillgängligt ramverk för appar och snabba MVP:er, men att bygga med det drar
  sajten mot biblioteksstandard, som granskaren uttryckligen straffar under originalitet (`kritik/GRANSKARE.md` rad
  79), och mot byggstandardens 3.1 (egna designtokens per verksamhet), 3.7 (CSS-budget) och 5.5 (ingen karusell; källan
  levererar en, `scss/_carousel.scss`). Det krockar alltså med ett medvetet val, inte med en text vi bara råkar ha.
  Taste-skillen vi läser i steg 5 rekommenderar Bootstrap för lokala småföretag [kunskap/externa/leonxlnx-taste-SKILL-
  ce26fc25.md rad 97], men bygg-sajt läser medvetet bara dess principer, "inte dess stack eller skelett"
  (`bygg-sajt/SKILL.md` rad 178); den raden står sig. Det enda som kunde vara värt något, komponenternas
  tillgänglighetsbeteende (fokusfälla, Esc i meny), täcks redan av byggstandardens 5.1–5.2 och prövas av granskaren
  utan beroendet. Källan säljer inget utöver sin README:s egna superlativ
- Kostnad: inget tas in. Som beroende i varje bygge vore det hela ramverkets CSS och, för meny eller modal, dess JS med
  Popper; källans text är cirka 261 000 tokens enligt förgranskningen
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text till agenter, inga skills, hookar eller behörigheter.
  109 skript; flaggorna "eval/exec" gäller en hjälpfunktion som heter `execute` och anropar callbacks [REPO
  js/src/util/index.js rad 225], "hemligheter/miljö" byggkonfiguration och komponenternas datanycklar. Inget kördes
  eller installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · huggingface/transformers · nej
- Källa: https://github.com/huggingface/transformers @ 9d8c3a2 (ur klonens `.git/shallow`; senaste push
  2026-10-02T14:26Z), Apache-2.0; cirka 167 000 stjärnor, inte arkiverat. Förgranskat. Läst: README helt, hela
  agentdelen (`.ai/AGENTS.md`, `.ai/review-rules.md`, `.ai/skills/add-or-fix-type-checking/SKILL.md`), Makefile-målen
  som länkar skillen, förgranskningens rapport och ett urval av de flaggade ställena. Resten (cirka 6 500 textfiler,
  modellkod, översatt dokumentation) bara som fillista. Bilder: repots enda bilder är fyra testfixturer (COCO);
  README:s bilder ligger på huggingface.co och är logga och ett schema. Ingen demosajt. Ägarens not: ingen
- Steg: inget av de åtta; möjligen kirurgen själv (granskningsregler för agenter) och underlaget i steg 1 (bilder, ljud)
- Jämfört med i dag: källan är ett Python-bibliotek med modelldefinitioner för text, bild, ljud och video, för träning
  och inferens med PyTorch [REPO README.md rad 70–76, 87]. Sak mot sak där det kunde beröra oss: (1) **Bilderna i
  steg 1** beskrivs av byggaren själv som tittar på dem och skriver fil, källa, vad bilden visar och kvalitet i
  `BILDER.md` (`.claude/skills/bygg-sajt/SKILL.md` rad 68–72). En lokal bildklassare eller bildtextmodell ur källan
  [REPO README.md rad 174–213] gör samma sak sämre än en modell som ser bilden och vet vad verksamheten behöver; sämre.
  (2) **Ljud**: kirurgens videoverktyg tar YouTubes transkript och annars undertexter, ingen taligenkänning
  (`kontroller/youtube.py` rad 13). Whisper genom källans pipeline [REPO README.md rad 161–170] skulle fylla den
  luckan, men den har inte stoppat något intag, och bygget tar inte emot ljud från verksamheter i dag. (3)
  **Agentreglerna**: granskningsreglerna behandlar PR-innehåll som opålitlig indata och förbjuder att påstå att en
  kontroll gick igenom som inte körts [REPO .ai/review-rules.md rad 3, 9–13]. Vi har samma två regler: granskaren läser
  allt som material, aldrig instruktioner, och skiljer verifierat från antaget (`kritik/GRANSKARE.md` rad 9–10), och
  kirurgen har sin säkerhetsdel. Lika. Typkontrollskillen gäller bara deras `ty`-verktyg och Python-kodbas; inget för
  oss
- Skäl: transformers är bästa verktyget för den som tränar eller kör maskininlärningsmodeller, men vi bygger statiska
  sajter åt hantverkare med en modell som redan ser bilder och läser text; inget av de åtta stegen saknar en lokal
  modell. Det som ligger närmast, taligenkänning för videor utan undertexter eller röstmeddelanden från en
  verksamhet, är i så fall ett litet och fristående behov som hellre löses med ett eget smalt verktyg än med ett
  bibliotek som drar in PyTorch; det blir aktuellt först när ett intag eller en beställning faktiskt fastnat på ljud.
  Agentdelen är välskriven men säger inget vi inte redan har. Källan säljer Hugging Face Hub och Enterprise [REPO
  README.md rad 81–83, 240–242], men påståendena om modellerna är belagda med körbara exempel, inte anekdoter
- Kostnad: inget tas in. Som beroende vore det PyTorch plus nedladdade modellvikter, flera GB, och underhåll av en
  Python-miljö med GPU-/MPS-frågor; källans text är cirka 3,05 miljoner tokens enligt förgranskningen. Skillen i
  `.ai/skills/` kostar 40 tokens alltid och cirka 2 500 vid användning, men hör inte till vårt arbete
- Säkerhet: förgranskningen HÖG, av storlek snarare än av avsikt. 368 dolda tecken, alla i dokumentationen; de
  kontrollerade är nollbreddsmellanrum i japansk och arabisk text och en sammanfogning i en emoji [REPO
  docs/source/en/quantization/concept_guide.md rad 171]. De 38 ställena med "text till agenter" är systemprompter i
  modellexempel och tester ("You are an AI …" i evolla och higgs_audio) och vanliga instruktioner i
  bidragsguiderna; ingen riktar sig till en kodagent som läser repot. Agentfilerna ger inga behörigheter och har inga
  hookar; `make claude` länkar bara in skillmappen [REPO Makefile rad 82–85]. 4 933 skript, bland dem CI-konfiguration
  med nätanrop och miljövariabler. Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · AUTOMATIC1111/stable-diffusion-webui · nej
- Källa: https://github.com/AUTOMATIC1111/stable-diffusion-webui @ 82a973c (ur klonens `.git/refs/heads/master`;
  senaste push 2026-03-02, senaste version i CHANGELOG 1.10.1), AGPL-3.0; cirka 165 000 stjärnor, inte arkiverat.
  Förgranskat. Läst: README helt, början av CHANGELOG, förgranskningens rapport och de flaggade ställena för
  modellnedladdning och -inläsning (`modules/modelloader.py`, `modules/realesrgan_model.py`, `modules/sd_models.py`,
  `modules/safe.py`). Övriga omkring 240 skript bara som fillista. Bilder: repots enda skärmbild (`screenshot.png`);
  övriga fem bilder är testfixturer och en platshållare. Ingen demosajt; funktionsvisningen ligger i wikin och
  öppnades inte. Ägarens not: ingen
- Steg: inget av de åtta; närmast bilderna i steg 1 och bildbehandlingen i steg 5 (`kunskap/bild.md`)
- Jämfört med i dag: källan är ett webbgränssnitt i Gradio för att generera och redigera bilder med Stable Diffusion:
  text till bild, bild till bild, inmålning och utmålning [REPO README.md rad 2, 8–13], plus en flik för uppskalning och
  ansiktsrestaurering med GFPGAN, CodeFormer och ESRGAN-familjen [REPO README.md rad 26–32]. Sak mot sak: (1)
  **Genererade bilder** som ersättning för egna: vi tar verksamhetens egna bilder och beställer det som saknas
  (`.claude/skills/bygg-sajt/SKILL.md` rad 68–72, byggstandarden 9.3 och 9.4, `kunskap/byggstandard.md` rad 121–122),
  ägaren dömde "hellre inga foton än stock" (`LARDOMAR.md` rad 90), och genererade bilder får aldrig framställas som
  kundens arbete eller personer (`kunskap/bild.md` rad 16–19). Generering via fal.ai valdes medvetet bort ur
  bildverktygen (`kunskap/bild.md` rad 5–8). Källans kärna går rakt emot det; sämre för oss. (2) **Uppskalning av
  kundens små bilder**: vi normaliserar, beskär och komprimerar med `sharp` (`kunskap/bild.md` rad 49–55) och visar en
  liten bild i den storlek den håller. En neural uppskalare hittar på detaljer som inte fanns i fotot, och
  ansiktsrestaurering ritar om ansikten; på en bild med anspråket `depicts_client_work` eller `depicts_client_people`
  blir det bevis som inte längre är kundens. Sämre. (3) **Inmålning** för att städa bort skräp ur ett jobbfoto: samma
  invändning, ett ändrat bevis
- Skäl: källan är det mest spridda verktyget för att generera bilder lokalt, och det gör det den säger, men vår regel
  bygger på motsatsen: förtroendet bärs av verksamhetens egna bilder (Fogg m.fl. 2003, byggstandarden 9.3), och det
  som saknas beställs i stället för att fyllas. Skärmbilden visar själv vad verktyget gör: en prompt med
  "photorealistic" och fyra genererade bilder av en planta [BILD screenshot.png]. Den enda del som kunde verka nyttig,
  uppskalningen, ändrar beviset och kräver dessutom PyTorch, ett grafikkort (NVidia rekommenderas, Python 3.10.6
  [REPO README.md rad 98, 114]) och nedladdade modellvikter; körningen kan inte bedömas utan att köra källans kod.
  Källkritik: README säljer inget, och funktionerna är verkliga, men utvecklingen har avstannat (ingen push sedan
  mars 2026)
- Kostnad: inget tas in. Som beroende vore det en Python 3.10-miljö med PyTorch, flera GB modellvikter, ett lokalt
  webbgränssnitt och AGPL-3.0, som kräver att källkoden lämnas ut om verktyget görs tillgängligt över nätet.
  Källans text är cirka 37 600 tokens enligt förgranskningen; ingen skill
- Säkerhet: förgranskningen MEDEL, inga dolda tecken. Den enda "text till agenter" är en installationsanvisning till
  människor [REPO README.md rad 148]. 246 skript, bland dem eval/exec och nätanrop. Verktyget laddar ner modellvikter
  från nätet [REPO modules/modelloader.py rad 20–40; modules/realesrgan_model.py rad 71–101] och läser checkpoints
  med `torch.load` [REPO modules/sd_models.py rad 323], skyddat av en begränsad unpickler [REPO modules/safe.py rad
  23] som går att stänga av [REPO modules/safe.py rad 136]; README nämner också att godtycklig Python kan köras från
  gränssnittet med en flagga [REPO README.md rad 49]. Inget kördes eller installerades. Inget försök att styra
  kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · langgenius/dify · nej
- Källa: https://github.com/langgenius/dify @ 63094c9 (ur klonens `.git/shallow`; senaste push 2026-10-02T14:02Z),
  "Dify Open Source License", en ändrad Apache 2.0 med tilläggsvillkor; cirka 158 000 stjärnor, inte arkiverat.
  Förgranskat. Läst: README och LICENSE i helhet, `.claude/settings.json`, namnen och storlekarna på alla sju skills,
  frontend-code-review-skillens SKILL.md och dess tillgänglighetsregler i helhet. Bild: README:ns omslagsbild [BILD
  images/GitHub_README_if.png]. Ingen demosajt; produkten är en server eller deras molntjänst. Ägarens not: ingen
- Steg: inget av de åtta; närmast steg 5–6 (tillgänglighet och formulär i bygget och provet)
- Jämfört med i dag: Dify är en plattform för att bygga AI-appar: arbetsflöden på en visuell duk, RAG över dokument,
  agenter, modellhantering och loggar, självkörd med Docker (minst 2 kärnor och 4 GiB) eller i deras moln [REPO
  README.md rad 64–84, 92–114]. Sak mot sak: (1) **En AI-chatt på kundens sajt**, det enda en Dify-app kunde bli hos
  oss: våra sajter laddar inget från tredje part och håller sig under 200 kB JS (`kunskap/byggstandard.md` rad 52, 61),
  och de dömda byggena har 0 kB JS (`LARDOMAR.md` rad 31, 56, 87). En chatt för en tvåmannafirma vore en server att
  driva, eller ett molnkonto, för något ingen dom efterfrågat; vägen för frågor är telefonen och formuläret
  (byggstandarden 6.1, rad 84). Sämre för oss. (2) **Tillgänglighetsreglerna i frontend-code-review** [REPO
  .agents/skills/frontend-code-review/references/accessibility-ui.md rad 16–131] är en välskriven granskningslista,
  men varje punkt som gäller en statisk sajt finns redan hos oss: synlig fokus (byggstandarden 3.4, rad 49), reducerad
  rörelse (3.5, rad 50), begripliga länknamn och ikonknappar (5.3, rad 71), etiketter och fel kopplade till fältet (5.4,
  rad 72), `type`, inputmode och autocomplete (6.2, rad 85). Listan hänvisar själv till Vercels Web Interface
  Guidelines som bredare referens [rad 14, 135], och den har bygget redan (`.claude/skills/bygg-sajt/SKILL.md` rad 243).
  Resten är bundet till deras React-komponenter, Tailwind och Base UI [rad 9, 120]. Lika i sak, inget nytt
- Skäl: Dify är en kompetent plattform för den som bygger AI-appar, men det hjälper oss inte att bygga bättre sajter åt
  små verksamheter eller att arbeta smartare: bygget behöver ingen RAG eller visuell agentduk, och en chatt på sajten
  krockar med våra gränser för tredjepartsresurser och JS. Den enda läsbara delen för webbyggen,
  tillgänglighetslistan, täcks redan punkt för punkt av byggstandarden och Vercels riktlinjer. Licensen kräver
  kommersiell licens för drift med flera arbetsytor och förbjuder att logga och upphovsinfo tas bort ur gränssnittet
  [REPO LICENSE rad 5–11], och anger att gränssnittets design är skyddad av mönsterpatent [rad 20]; att köra den åt
  flera kunder vore alltså en licensfråga. Ingen dom i `LARDOMAR.md` pekar på AI-funktioner på sajten. Källkritik:
  README och omslagsbilden säljer, "Build Production-ready Agentic AI Solutions" [BILD GitHub_README_if.png], och
  "Describe the agent you want and it builds itself" [REPO README.md rad 108] är ett påstående utan belägg i repot
- Kostnad: ingen; inget tas in. Som beroende vore det en server med databas, Redis och vektorlager per kund, eller ett
  molnabonnemang, plus licensfrågan. Källans text är cirka 570 000 tokens enligt förgranskningen; skillsen är små
  (74–88 tokens alltid) men gäller Difys egen kodbas
- Säkerhet: förgranskningen HÖG, av mängden: 6 891 skript med nätanrop, hemligheter i miljövariabler och eval/exec,
  `curl | sh` i `cli/scripts/install-cli.sh`, och en krok i `.claude/settings.json` som kör `npx` på ett paket före
  varje Bash-anrop. 4 750 dolda tecken; de rapporten listar är nollbreddstecken i persiska översättningar
  (`web/i18n/locales/fa-IR/`), översättningsdokument och emojisekvenser i testfall, inget som gömmer text till
  kirurgen. De sex ställena med text till agenter är produktens egna promptmallar
  (`api/constants/pipeline_templates.json`), ett testfall och installationsanvisningar till människor. Inga
  behörigheter i skillsens frontmatter. Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · msitarzewski/agency-agents · prova A/B
- Källa: https://github.com/msitarzewski/agency-agents @ d3f71c4 (ur klonens `.git/refs/heads/main`; senaste push
  2026-10-01T19:35Z), MIT; cirka 156 000 stjärnor, inte arkiverat. Förgranskat. Läst: README (rollistan, exempelteam,
  designfilosofin, statistiken), LICENSE och i helhet de sex agenter som rör webbyggen: design-ui-finish-gate-reviewer,
  design-persona-walkthrough, testing-reality-checker, marketing-aeo-foundations, samt de relevanta styckena i
  testing-evidence-collector och design-ux-researcher. Övriga drygt 220 agenter (spel, Kina-marknad, ekonomi, juridik
  m.m.) bara i README:s tabeller. Repot har inga bilder; appen och sajten som README säljer öppnades inte. Ägarens not:
  ingen
- Steg: 5–6 och den oberoende granskaren (kognitiv genomgång, slutgrind); 7.6 i byggstandarden (AI-sök)
- Jämfört med i dag: källan är en samling rollprompter ("agenter med personlighet") för alla tänkbara yrken, att
  installera i Claude Code och andra verktyg [REPO README.md rad 21–28, 46–57]. Inga skills, inga referenser eller data.
  Sak mot sak för det som rör oss: (1) **Persona Walkthrough**: en simulerad besökare med sökfras, ankomstväg, sajter
  sedda innan, rädslor och kontakttröskel [REPO design/design-persona-walkthrough.md rad 63–91] går igenom sidan
  skärm för skärm, med besökarens egen röst och analytikerns bedömning åtskilda [rad 46, 99–112, 161–188]. Vår
  granskare går igenom som en anonym förstagångsbesökare i mobilen (`kritik/GRANSKARE.md` rad 50–53), och idén att göra
  besökaren namngiven med situation ligger redan som vilande A/B (backlog
  B-20261002-a-b-granskarens-kognitiva-genomgang-som-namngive, från hermes-agent). Källan lägger till två saker den
  posten saknar: sökfrasen och jämförelseramen (vad besökaren såg innan), och genomgång per skärmruta. Möjligen
  bättre; syns först i provet. (2) **UI Finish-Gate Reviewer**: designkontrakt med förbjudna standardval och
  PASS/HOLD med verifieringsvillkor [REPO design/design-ui-finish-gate-reviewer.md rad 108–123, 143–165]. Vi har
  samma sak i starkare form: exakt specifikation och visuell tes i KONCEPT.md (`.claude/skills/bygg-sajt/SKILL.md` rad
  187–197), upptagna val (rad 182–185), och granskarens blockerande fynd med acceptanskriterium i EARS-form och
  stoppvakten (`kritik/GRANSKARE.md` rad 113–122). Lika eller sämre. (3) **Reality Checker**: utgår från "NEEDS WORK"
  och behandlar ett första bygge som ofullständigt per automatik [REPO testing/testing-reality-checker.md rad 47–50]
  och kör ett skript som inte finns i repot (`qa-playwright-capture.sh`, rad 63). Vår granskare är sträng men
  kalibrerad mot ägarens domar och ankare (`kritik/GRANSKARE.md` rad 5–7, 69–75), och bygget varnar uttryckligen för
  granskare som alltid hittar något (`bygg-sajt/SKILL.md` rad 229–231). Sämre. (4) **AEO Foundations**: llms.txt,
  token-budgetar, FAQPage-schema på alla lämpliga sidor och "Allow (drives citations)" för träningsrobotar [REPO
  marketing/marketing-aeo-foundations.md rad 26–28, 205, 217–218]. Byggstandarden säger med källa att llms.txt inte
  behövs och att FAQPage inte längre ger rikresultat (`kunskap/byggstandard.md` rad 102, 142–144, 153). Sämre
- Skäl: som helhet hjälper samlingen oss inte: rollprompter med emoji och "personlighet" ersätter inte våra metoder,
  som redan är förankrade i litteraturen (`kunskap/teoretisk-grund.md` rad 16–21), och de delar som rör webbyggen är
  lika bra eller sämre än det vi har; AEO-agenten säger dessutom emot dokumenterade källor. Ett undantag:
  persona-genomgångens jämförelseram och skärmruta-för-skärmruta, där besökarens ord hålls isär från analysen, kan
  skärpa den A/B som redan väntar; ägarens sämsta fynd i L1 var just en sådan situation (mobilen kl 21,
  `LARDOMAR.md` rad 32), och L3:s citat om ett formulär som inte fanns (rad 81) är något en besökare som jämför med
  den gamla sajten kan snubbla på. Väg det försiktigt: källan säger själv att det är en kvalitativ simulering, inte
  statistiskt belägg [REPO design/design-persona-walkthrough.md rad 51], vår grund säger att en modellbaserad besökare
  inte är en människa (`kunskap/teoretisk-grund.md` rad 20), och agenten bygger också på anknytningsteori för
  besökare (rad 85) och obelagda tal ("fewer than 20% of visitors" efter sjätte skärmen, rad 220) och föreslår
  chattfönster och skrollutlösta uppmaningar (rad 151, 270), som krockar med regeln mot slop och sajter utan JS. Det
  tas inte med. Källkritik: README säljer en app och sponsring [REPO README.md rad 8–15] och påstår "Battle-tested in
  production environments" utan belägg [rad 732]; README:s citat om att alltid hitta "3-5 issues" (rad 709) stämmer
  inte längre med agentfilen, som nu säger att noll fynd är ett giltigt utfall [REPO
  testing/testing-evidence-collector.md rad 27–30]
- Kostnad: inget kopieras. Tillägget är några meningar i `kritik/GRANSKARE.md` om A/B:n vinner; i varje granskning
  någon minut och några tusen tokens till för skärmrutorna. A/B:n körs i samma omgång som den befintliga posten, som
  en extra arm. Källans text är cirka 1,1 miljoner tokens enligt förgranskningen; ingen skill
- Säkerhet: förgranskningen MEDEL, inga dolda tecken, inga behörigheter eller krokar. De 15 ställena med text till
  agenter är oskyldiga i sitt sammanhang: rollprompternas "You are …" och ordet "exfiltration" i säkerhetsagenterna;
  "Ignore all previous instructions" (engineering-prompt-engineer.md rad 169) är ett exempel på injektion att testa
  mot, inte riktat till läsaren. 34 skript, bland dem en installatör som skriver utanför repot och eval/exec i två
  kontrollskript. Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: `kritik/GRANSKARE.md` steg 5 (rad 50–53), som tillägg till den namngivna besökaren i den vilande posten:
  sökfras och vad besökaren såg innan som jämförelseram; genomgång per skärmruta i 390 px med besökarens ord och en
  analytikerrad (förtroende upp eller ner, Fogg 2009: motivation, förmåga, trigger, kan hen ta kontakt härifrån) hållna
  isär; slut med var hen nästan lämnade och om hen skulle ringa eller skriva. Prövas som arm C i samma A/B: ägarens fel
  i L1–L3 som facit, tre körningar per arm och bygge, blind domare av en annan modell med ombytt ordning, oenighet
  räknas som oavgjort, tokens och tid redovisas bredvid
- Utfall: arm c i granskarförsöket 2026-10-02 (sökfras, jämförelseram, skärmruta för skärmruta med två röster): ingen
  skillnad mot dagens text (3,3 mot 3,3 omdömesfel per bygge, 9,2 mot 8,8 av alla fel) och något dyrare; avvisad.
- Backlog: B-20261002-a-b-tillagg-granskarens-namngivna-besokare-far-s (prova A/B, körs ihop med
  B-20261002-a-b-granskarens-kognitiva-genomgang-som-namngive)

### 2026-10-02 · open-webui/open-webui · nej
- Källa: https://github.com/open-webui/open-webui @ 8bd8b4f (ur klonens `.git/shallow`; senaste push
  2026-10-02T04:50Z), "Open WebUI License", en BSD-licens med ett tillägg om varumärket; cirka 154 000 stjärnor, inte
  arkiverat. Förgranskat. Läst: README och LICENSE i helhet, förgranskningens rapport och de flaggade ställena
  (`backend/open_webui/utils/files.py`, `src/lib/utils/index.ts`, `Dockerfile`, `backend/open_webui/utils/plugin.py`)
  och utvärderingens Elo-beräkning (`backend/open_webui/routers/evaluations.py` rad 86–133). Övriga omkring 370 skript
  bara som fillista. Bilder: README:ns demobild och banderollen; övriga bilder i repot är ikoner, favicons och
  kartmarkörer. Demon kräver en egen server och öppnades inte. Ägarens not: ingen
- Steg: inget av de åtta; närmast steg 5 (en AI-chatt på kundens sajt) och kirurgens A/B-metod (modellarenan)
- Jämfört med i dag: källan är ett självkört chattgränssnitt för språkmodeller, lokala via Ollama eller via
  OpenAI-kompatibla API:er, med RAG, webbsök, bildgenerering, kalender, automationer och företagsinloggning [REPO
  README.md rad 13, 24–86]. Sak mot sak: (1) **En AI-chatt på kundens sajt**: våra sajter laddar inget från tredje
  part och håller sig under 200 kB JS (`kunskap/byggstandard.md` rad 52, 61), de dömda byggena har 0 kB JS
  (`LARDOMAR.md` rad 31, 56, 87), och besökarens väg är telefonen och formuläret (byggstandarden 6.1, rad 84). Open
  WebUI är dessutom ett internt verktyg för inloggade användare, inte en widget för besökare [BILD demo.png: sidomeny
  med chattar, mappar och kanaler, inloggad användare nere till vänster]. Samma slutsats som för Dify (posten
  2026-10-02 · langgenius/dify ovan); sämre för oss. (2) **Modellarenan med A/B och Elo** [REPO README.md rad 68]: när
  en användare röstar fram en vinnare uppdateras ett Elo-tal med K = 32, i den ordning rösterna kom, och bara vinst
  eller förlust räknas [REPO backend/open_webui/routers/evaluations.py rad 100, 108–124]. Vår A/B jämför två armar
  blint parvis med ombytt ordning, räknar oenighet som oavgjort och använder en annan modell som domare än den som
  byggde (`.claude/skills/kirurg/SKILL.md` rad 159–162). För två armar och några körningar är en ordningsberoende
  Elo-summa utan oavgjort sämre än vår räkning, och den mäter vad en människa i chatten tycker om ett svar, inte en
  sajt. Sämre. (3) **Ägarens arbete** (att fråga, döma, mata kirurgen): det gör ägaren redan i Claude Code och
  dashboarden; en egen chattserver lägger till drift utan nytt i sak
- Skäl: Open WebUI är ett välskött och aktivt projekt för den som vill driva ett eget chattgränssnitt, men det hjälper
  oss inte att bygga bättre sajter åt små verksamheter eller att arbeta smartare: bygget behöver ingen chattserver,
  och en chatt på sajten krockar med våra gränser för JS och tredjepartsresurser och efterfrågas av ingen dom i
  `LARDOMAR.md`. Det enda med metodvärde, arenans röstning, är svagare än A/B-regeln vi redan har. Licensen förbjuder
  att "Open WebUI"-märket tas bort eller ändras i en driftsättning med fler än 50 användare på 30 dagar utan
  företagslicens [REPO LICENSE rad 20–34], så en kundvänd driftsättning vore också en licensfråga. Källkritik: README
  säljer, med en ruta om företagsplan och säljteam överst [REPO README.md rad 19–20] och "a home for AI" [rad 13];
  funktionslistan är verklig men belägg för kvalitet visas inte, och demobilden visar ett tomt startläge
- Kostnad: ingen; inget tas in. Som beroende vore det en Python 3.11-server eller Docker-behållare med databas,
  eventuellt vektorlager och Ollama, per installation, plus varumärkesvillkoret. Källans text är cirka 344 000 tokens
  enligt förgranskningen; ingen skill
- Säkerhet: förgranskningen HÖG, av mängden: 370 skript med nätanrop, hemligheter i miljövariabler och eval/exec,
  och `curl | sh` för Ollamas installatör i `Dockerfile` rad 194. Pluginsystemet kör användarens Python-kod med
  `exec` [REPO backend/open_webui/utils/plugin.py rad 241, 291], vilket är produktens avsikt. 30 dolda tecken, alla
  nollbreddsfogar (U+200D) i emojisekvenser: i CHANGELOG och i en kodkommentar som visar familjeemoji [REPO
  src/lib/utils/index.ts rad 1016]; inget som gömmer text. De tre ställena med text till agenter är en
  installationsanvisning till människor [REPO README.md rad 115] och två texter om en rättad läcka mellan användare,
  en rad i CHANGELOG och kodkommentaren vid rättelsen [REPO CHANGELOG.md rad 1246; backend/open_webui/utils/files.py
  rad 214]. Inga skills, krokar eller behörigheter. Inget kördes eller
  installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · DietrichGebert/ponytail · nej
- Källa: https://github.com/DietrichGebert/ponytail @ 3436438 (ur klonens `.git/shallow`; senaste push
  2026-10-02T14:49Z), MIT; cirka 151 000 stjärnor, inte arkiverat. Förgranskat. Läst: README, de sex skillsen
  (`skills/ponytail`, `-review`, `-audit`; de övriga tre är hjälp, skuldlista och resultattavla),
  `docs/platform-native.md`, `examples/modal-dialog.md`, den agentiska mätningen
  `benchmarks/results/2026-06-18-agentic.md` i helhet, krokfilen `hooks/claude-codex-hooks.json` och
  `hooks/ponytail-activate.js`. Övriga exempel, mätrapporter och adaptrar för andra verktyg bara som fillista. Bilder:
  delningsbilden och väntelistebanderollen (en tecknad figur, ingen produkt att se); ingen demo. Ägarens not: ingen
- Steg: 5 (bygget av sajtens kod) och arbetssättet runt stegen (backlogsessionernas kodändringar i `kontroller/`)
- Jämfört med i dag: källan är en regelskill som får en kodagent att stanna på första hållbara steget i en stege:
  behövs det, finns det redan, standardbiblioteket, plattformens inbyggda funktion, ett installerat beroende, en rad,
  först sist egen kod; aldrig på bekostnad av validering, felhantering, säkerhet eller tillgänglighet [REPO
  skills/ponytail/SKILL.md rad 32–42, 90–95]. Sak mot sak: (1) **Sajtens kod.** Källans största vinster är att ta
  webbläsarens inbyggda kontroll i stället för en komponent (datumväljare 404 → 23 rader) [REPO
  benchmarks/results/2026-06-18-agentic.md rad 85, 105–108]. Våra byggen är redan där: ingen JavaScript som inte
  behövs (`.claude/skills/bygg-sajt/SKILL.md` rad 202), formuläret är vanlig POST utan JS (`kunskap/byggstandard.md`
  rad 86), och de tre dömda byggena har 0 kB JS, 4–10 kB CSS och FAQ i inbyggt `<details>` (`LARDOMAR.md` rad 31, 56,
  80, 87). Lika. (2) **Plattformstabellen** [REPO docs/platform-native.md] är bred men säger på två ställen emot
  byggstandarden: flytande typsnitt med bara vw som önskat värde [rad 36] mot vår rättelse att clamp() ska blanda rem
  och vw för att växa med zoom (`kunskap/byggstandard.md` rad 47, 145), och en karusell med scroll-snap [rad 44] mot
  inga karuseller (rad 73, 119); `title` som verktygstips [rad 23] når inte pekskärm eller tangentbord. Sämre för oss.
  (3) **Systemets kod.** "Små ändringar. En dom blir en textändring, inte en ny mekanik" (`CLAUDE.md` rad 27) och "så
  liten som posten kräver … Ny mekanik bara när … inget enklare räcker" (`.claude/skills/backlog/SKILL.md` rad 26–27)
  är samma hållning. Lika. (4) **Granskning av överbyggnad** (`ponytail-review`, `-audit`) [REPO
  skills/ponytail-review/SKILL.md rad 13–27]: Claude Code har redan en inbyggd förenklingsgranskning av ändrad kod
  (`simplify`), och våra byggens kod är redan liten. Lika
- Skäl: ponytail är ovanligt ärligt mätt för sin genre: den agentiska mätningen bygger om en tidigare uppblåst siffra
  efter extern kritik, isolerar armarna, redovisar var skillen inte vinner och att säkerhetsskillnaden är en enda miss
  på tjugo [REPO benchmarks/results/2026-06-18-agentic.md rad 9–24, 40–47, 109–111, 149–151, 186–198]. Men effekten
  den mäter är kodrader på en React- och FastAPI-app med Haiku 4.5, och det problemet har vi inte: våra sajter är
  statisk Astro utan JS, och ingen av ägarens domar L1–L3 pekar på överbyggd kod, utan på förfrågningsväg,
  bildunderlag, förtroende och röst. Det den kunde tillföra har vi redan som regel, och dess plattformslista säger på
  två punkter emot byggstandarden. Samma slutsats som för andrej-karpathy-skills ovan, som ägaren höll med om
  (`kunskap/KIRURG-OMDOMEN.md` rad 55–58). Källkritik: README säljer med "100% safe" och en väntelista för en kommande
  produkt [REPO README.md rad 33, 44]; "100% safe" gäller sex uppgifter med deterministiska prov, vilket rapporten
  själv kallar ett golv, inte ett bevis [rad 190–191]. Stjärnantalet är räckvidd, inte belägg
- Kostnad: ingen; inget tas in. Huvudskillen vore cirka 208 tokens i varje session och 1 420 vid användning enligt
  förgranskningen; pluginvägen lägger dessutom regeltexten i varje session och varje underagent via krokar
- Säkerhet: förgranskningen HÖG, av mängden: 57 skript, bland dem mätskript med nätanrop och eval/exec och krokar som
  skriver utanför repot. Inga dolda tecken, inga behörigheter i skillsens frontmatter. Pluginen registrerar tre krokar
  (SessionStart, SubagentStart, UserPromptSubmit) som kör Node vid varje session, skriver en flaggfil i
  Claude-katalogen och ber agenten att självmant erbjuda en ändring i användarens `settings.json` för en statusrad
  [REPO hooks/claude-codex-hooks.json; hooks/ponytail-activate.js rad 63–95]. Det är riktat till agenten efter
  installation, inte till kirurgen, men är just den sortens obevakade inställningsändring vi inte vill ha. Inget
  kördes eller installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · garrytan/gstack · ta in
- Källa: https://github.com/garrytan/gstack @ df89475 (ur klonens `.git/shallow`; senaste push 2026-10-01T20:59Z), MIT,
  cirka 135 000 stjärnor, inte arkiverat. Bedömd förut med de gamla reglerna (`REGISTER-arkiv-20261001.md:761`, nej);
  arkivet ligger utanför registret, så det här är en ny bedömning med dagens regler, som för ECC. Förgranskat. Läst
  själv: README rad 1–70 och raderna citerade nedan, `lib/design-catalog.ts` rad 1–154 och 440–640,
  `design-review/SKILL.md` rad 1130–1260, 1440–1447 och 1778–1789, de flaggade dolda tecknen. Läst i helhet av två
  subagenter med belägg (domen är min): design-review, plan-design-review, design-consultation, design-html,
  DESIGN.md, ETHOS.md, qa, qa-only, office-hours, benchmark, review, learn, retro, spec, scrape, careful, freeze,
  deslop-shared-libs och landing-report. Övriga skills (ship, cso, ios-*, gbrain m.fl.) bara som namn i
  förgranskningen. Bilder: som förra gången, bara aktivitetsgrafer och ikoner; ingen demo. Ägarens not: ingen
- Steg: 6 (provets stilrapport) och granskaren i 5.6; inget annat
- Jämfört med i dag: (1) **Slopkatalogen.** Förra bedömningen såg elva mönster; katalogen har nu ett sextiotal, med
  kategori, säkerhet och ofta en mätbar tröskel, delvis hämtade ur pbakaus/impeccable (Apache-2.0) [REPO
  lib/design-catalog.ts rad 1–2, 77–640]. Vår `kontroller/stil.mjs` prövar omkring tio: färgfamiljer, gradient,
  accentord, numrerade och spärrade etiketter, monospace, piller, kort i kort, kortrader och nästa sektion (rad 74–81,
  137–146). Sex mönster i katalogen går att läsa ur den renderade sidan och saknas hos oss: innehåll dolt i vila till
  en skrollanimation [rad 488–491], radlängd utanför 45–75 tecken [rad 531–536], radhöjd under 1,4 i brödtext [rad
  550–553], marginaljusterad text [rad 570–573], mer än 60 procent centrerade textblock [rad 102–105] och en enda radie
  på 16 px eller mer på mer än 80 procent av elementen [rad 109–112]. Smartare: billigt, mätt i stället för bedömt, och
  litteraturen bakom radlängden (byggstandarden 3.1, typografisk skala) står redan hos oss utan mätning. Rubriknivåer
  utan hopp har vi redan (`kunskap/byggstandard.md:36`). (2) **Granskaren lovar ett mått som saknas.**
  `kritik/GRANSKARE.md:45` säger att `sida.mjs` ger radlängder; den mäter bara radhöjd (`kontroller/sida.mjs:113`).
  (3) **design-review** har en trunk test med sex frågor per sida [REPO design-review/SKILL.md rad 1137–1148] och ett
  mått på "happy talk" i procent av orden [rad 1249–1251]. Vi har Nielsens heuristiker och den kognitiva genomgången
  (`kritik/GRANSKARE.md:50–58`), rubriktestet (`bygg-sajt/SKILL.md:265–268`) och regeln mot välkomstfraser
  (`kunskap/copy-kontroll.md:15`). Lika för en sajt på fem sidor; frågan om sökruta passar inte oss. (4) **qa,
  benchmark, office-hours:** qa och design-review rättar och committar själva, en commit per fynd [REPO
  design-review/SKILL.md rad 1780–1788; README rad 225, 229], mot vår åtskillnad mellan byggare och domare
  (`kritik/GRANSKARE.md:3–9`). Benchmark har vi i Lighthouse-grinden och byggstandardens budgetar
  (`kunskap/byggstandard.md:52, 58`). office-hours är frågor till en grundare som svarar, för startups; våra byggen har
  ingen som svarar (`bygg-sajt/SKILL.md:20`). Sämre eller lika. (5) Bieffekt: `kunskap/kundintervju.md:4` pekar på
  `verktyg/intervju.py`, som inte finns i det här repot (kvar från Digitala)
- Skäl: som paket är gstack fel verktyg: ett interaktivt programvarukontor för grundare [REPO README.md rad 23, 29–32]
  som rättar och committar sin egen kod, låter AI-slop väga 5 procent av designbetyget [REPO design-review/SKILL.md
  rad 1444], tar fram skisser med OpenAI:s bildmodell och skriver i användarens CLAUDE.md och `settings.json`. Inget
  av det ska in. Men designkatalogen har vuxit sedan förra bedömningen och har sex mönster som vår stilrapport kan mäta
  på den renderade sidan, som information och aldrig som grind, i samma form som rapporten redan har. Det är en liten
  ändring i en befintlig kontroll, och den rättar samtidigt ett löfte i granskaren om ett mått som inte finns. Därför
  ta in, avgränsat till det. Källkritik: README säljer med produktivitetstal, "~810× my 2013 pace" [REPO README.md rad
  9], och aktivitetsgrafer, inte med något byggt resultat. office-hours slutar med en personlig vädjan och öppnar
  ansökan till Y Combinator med en ref-parameter [REPO office-hours/sections/design-and-handoff.md rad 374–377].
  Källan innehåller instruktioner till agenter: installationsprompten ska klistras in i Claude Code och skriva i
  CLAUDE.md [REPO README.md rad 51–53], och skillsen ber agenten att självmant välja dem. Det följdes inte
- Kostnad: inget kopieras; ingen skill tas in. Ändringen är ett sextiotal rader i `stil.mjs` och en rad i
  `GRANSKARE.md`; några millisekunder per sida i provet, inga tokens. Hela källan är cirka 2,1 miljoner tokens text
- Säkerhet: förgranskningen HÖG: 23 dolda tecken, 85 ställen med text riktad till agenter, 1 655 skript, krokar i
  frontmatter i autoplan, careful, freeze, guard och investigate. De dolda tecknen jag öppnade är teckenklasser i
  reguljära uttryck som rensar bort nollbreddstecken [REPO browse/src/server.ts rad 122; lib/redact-engine.ts rad 100];
  de agentriktade träffarna är mest testfixturer för repots eget skydd mot promptinjektion, och "Don't tell the user"
  är en kodkommentar om ett felbesked [REPO lib/gbrain-local-status.ts rad 516]. Varje skill startar med en ingress
  som söker uppdateringar över nätet och frågar om telemetri. Inget kördes eller installerades. Inget försök att styra
  kirurgen
- Förslag: `kontroller/stil.mjs`: de sex mönstren som varningar i STIL.md och radlängden per sida och vy;
  `kritik/GRANSKARE.md:45` pekar på stilrapporten för radlängd. Trösklarna med egna ord, källan i filhuvudet.
  Rökprovet grönt
- Utfall: —
- Backlog: B-20261002-stilrapporten-mater-sex-renderade-monster-ur-gst (ta in)

### 2026-10-02 · nextlevelbuilder/ui-ux-pro-max-skill · nej
- Källa: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill @ 09170ee (ur klonens `.git/refs/heads/main`; senaste
  push 2026-09-27T11:30Z, samma commit som arkivets två bedömningar), MIT; cirka 132 500 stjärnor, inte arkiverat.
  Bedömd två gånger med de gamla reglerna (`REGISTER-arkiv-20261001.md:8` prova A/B, `:181` nej); arkivet ligger utanför
  registret, så det här är en ny bedömning med dagens regler, där en skill som ger bygget en förmåga vi saknar går in i
  verktygslådan. Förgranskat. Läst: README i helhet, huvudskillens SKILL.md i helhet, `references/quick-reference.md`
  i helhet (alla regler i tio kategorier), huvudet och de rader i `ui-reasoning.csv` som gäller hantverk och bygg,
  fem rader ur `landing.csv`, huvudet i `google-fonts.csv`, `stack/README.md`, beskrivningarna av de sex övriga
  skillsen och de rader i `design/SKILL.md` som rör bildmodeller. Övriga data, skript och översättningar bara som
  fillista. Sett: `screenshots/website.png`, och demosajten uupm.cc öppnad på nytt i dag i 390 och 1440 (första vyn i
  båda, skrolllägena 04, 05 och 08 av åtta). Ägarens not: ingen
- Steg: 5 (riktning, typografi, färg, sektionsordning), 6 (UX-riktlinjer och leveranschecklista); de sex sidoskillsen
  (logo, varumärke, banderoller, presentationer, tokens, shadcn/Tailwind) ligger utanför de åtta stegen
- Jämfört med i dag: (1) **Designsystem-generatorn**, skillens kärna, krävs för varje ny sida [REPO
  .claude/skills/ui-ux-pro-max/SKILL.md rad 73–81] och slår upp bransch → mönster, stil, palett och typsnitt. För
  hantverkare ger regeln "Home Services (Plumber/Electrician)" Trust Blue, Safety Orange och grått i platt stil [REPO
  data/ui-reasoning.csv rad 56], och "Construction/Architecture" 3D-modellvisare och tidslinjeanimationer [rad 52]. Vi
  härleder fyra riktningar ur verksamheten själv, "aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md` rad
  187–189), och kopierar aldrig palett eller typsnitt (rad 223). Ägaren valde i L3 Sundboms gult och svart ur ordmärket
  framför marinblått från den gamla sajten (`LARDOMAR.md` rad 89), alltså mot just det som branschregeln hade gett.
  Sämre, och krockar med ett medvetet val. (2) **Landningsmönstren** bygger in en karusell för omdömen och parallax i
  toppen [REPO data/landing.csv rad 2–3] mot inga karuseller (`kunskap/byggstandard.md` rad 73, 119). Sämre. (3)
  **UX-reglerna**, 119 stycken: de som gäller en statisk sajt står redan i byggstandarden och mäts i provet: träffytor
  (3.3, rad 48), kontrast och synlig fokus (3.4, rad 49), reducerad rörelse (3.5, rad 50), fokus som inte döljs (5.1,
  rad 69), fel vid fältet (5.4, rad 72), `type` och autocomplete (6.2, rad 85), bildformat och srcset (4.2, rad 57).
  Resten gäller appar (Apple HIG, Material: haptik, flikrad, bottennavigation, diagram) eller går emot vår hållning:
  cursor-pointer och fjädrande animationer på allt, toastar som försvinner efter 3–5 sekunder [REPO
  references/quick-reference.md rad 42, 145, 169]. Lika, inget nytt att lägga till. (4) **Typsnittskatalogen** med
  1 934 Google-typsnitt, kategori, nyckelord och popularitet [REPO README.md rad 531–533; data/google-fonts.csv rad 1]:
  bygget installerar redan valfritt typsnitt via Fontsource och registrerar licensen (`bygg-sajt/SKILL.md` rad 38–42),
  och `kontroller/upptagna_val.py` håller vanevalen borta (rad 182–185). En katalog sorterad på popularitet drar åt de
  vanliga valen. Lika eller sämre. (5) **`stack/`** är ett annat projekt (YMungerDev/claude-website-design-stack)
  inlagt i repot [REPO stack/README.md rad 26]: skärmbilder i flera bredder, granskare i sju faser, frontend-design som
  smaklager. Vi har samma kedja med en oberoende granskare och stoppvakt (`bygg-sajt/SKILL.md` rad 217–232) och
  frontend-design som läsning (rad 177). Lika. (6) **Sidoskillsen**: logo, företagsprofil och ikoner tas fram med
  Googles bildmodeller och en API-nyckel [REPO .claude/skills/design/SKILL.md rad 114, 312]; vi använder
  verksamhetens eget märke och egna bilder och beställer det som saknas (`bygg-sajt/SKILL.md` rad 20–24, 213). Sämre
  för oss
- Skäl: dagens regel säger att en större verktygslåda sällan är dålig, men den här skillen kan inte ligga i lådan utan
  att krocka: dess beskrivning gör att den väljs för allt som rör gränssnitt, och dess första instruktion är att
  hämta riktningen ur en branschtabell. Det är motsatsen till "Bara de har" och till ägarens val i L3. Bilderna visar
  vad generatorn gör när den gör det den säljs för. Demosajten är mörk med blå och orange glöd, gradienttext i
  rubrikerna och sex lika statistikkort [BILD uupm-20261002/desktop-forsta], och slutar med en raketemoji över
  rubriken [BILD desktop-skroll-08] trots att den egna checklistan kräver "SVG icons (no emoji)" [BILD
  desktop-skroll-04]. Galleriet kallar påhittade verksamheter "real-world website demos": PawSpa med brickan "#1 Pet Spa
  in Town", stockfoto av en hund och siffrorna 5,000+, 4.9 och 10+ [BILD desktop-skroll-04, -05]. I mobil visar
  sidhuvudet logotypens ikon, mörkt läge, stjärnantalet och Premium men ingen meny, verktygsraden är logotyper utan
  namn, och under sidhuvudet står ett
  tomt band [BILD mobil-forsta]. Siffrorna i första vyn (57 stilar, 95 paletter, 56 typsnittspar, 8 stackar) [BILD
  desktop-forsta] motsäger README:s 79, 192, 74 och 22 [REPO README.md rad 191–195]. Det som inte krockar, UX-reglerna
  och checklistan, har vi redan punkt för punkt i byggstandarden med en kontroll bakom varje punkt. Källkritik: repot
  säljer en premiumversion och tar donationer [REPO README.md rad 23, 232–249], och stjärnantalet är räckvidd, inte
  belägg för kvalitet
- Kostnad: ingen; inget tas in. Som skill vore det 127 tokens i varje session och 3 845 vid användning, men drygt
  890 000 tokens data vid behov enligt förgranskningen, plus Python-skript för sökningen; sidoskillsen kräver
  API-nycklar till bildtjänster
- Säkerhet: förgranskningen HÖG. Inga dolda tecken. De två agentriktade träffarna (`design/scripts/cip/generate.py` rad
  434, och samma fil under `cli/assets/`) är en utskrift till användaren om att köra om kommandot, ingen instruktion
  till kirurgen. HÖG kommer av 152 skript, bland dem nätanrop och miljövariabler i logo- och bakgrundsskripten, och
  av `stack/.claude/settings.json` och `stack/.mcp.json`, som tillåter `npx playwright` och tre MCP-servrar som hämtas
  med `npx -y …@latest`. Inga behörigheter i skillsens frontmatter. Inget kördes eller installerades. Inget försök att
  styra kirurgen
- Förslag: inget ur källan. Egen innovation, inspirerad av källans regler om felsammanfattning och återhämtning [REPO
  references/quick-reference.md rad 180, 187–188]: demomottagaren skickar ett ofullständigt inskick tillbaka till
  `/kontakt/?saknas=1#forfragan` (`kontroller/prova.py` rad 170), men varken mallens `Forfragan.astro`,
  `kunskap/forfragan.md` (rad 22–24) eller bygg-sajt säger vad sidan ska visa då. Av de två byggen som har mallens
  formulär visar bara lulea-snickaren-abx ett besked, och det med JavaScript. Ett felbesked i mallen som visas med
  CSS `:target` fungerar utan JS
- Utfall: —
- Backlog: B-20261002-mallens-formular-visar-ett-felbesked-utan-javasc (egen innovation; en första version av posten
  med ett felaktigt antal byggen sattes till avvisad)

### 2026-10-02 · shadcn-ui/ui · nej
- Källa: https://github.com/shadcn-ui/ui @ 295a1f1 (ur klonens `.git/shallow`; senaste push 2026-10-02T11:32Z), MIT;
  cirka 125 000 stjärnor, inte arkiverat; cirka 542 000 tokens text. Bedömd förut med de gamla reglerna
  (`REGISTER-arkiv-20261001.md:810`, nej, @ d75a96a); arkivet ligger utanför registret, så det här är en ny bedömning
  med dagens regler, som för gstack. Förgranskat. Läst: README, `skills/shadcn/SKILL.md` i helhet,
  `skills/shadcn/rules/forms.md` i helhet, det nya `typeset.css` (rad 1–490) och dess dokumentation
  `apps/v4/content/docs/(root)/typeset.mdx` i helhet. Skillen `migrate-radix-to-base`, övriga regelfiler, registerkoden
  och mallarna bara som namn i förgranskningen. Sett: `apps/v4/public/opengraph-image.png`, och demon
  https://ui.shadcn.com öppnad i dag (desktop hela sidan, mobil första vyn). Ägarens not: ingen
- Steg: 5 (bygge: komponenter, formulär, typografi för löptext); inget annat
- Jämfört med i dag: (1) **Komponentbiblioteket och skillen.** Komponenterna är React med Tailwind som kopieras in med
  ett CLI, och skillen är en bruksanvisning för just det: komponera Card, Badge, FieldGroup och semantiska färgklasser,
  hämta allt via `npx shadcn@latest` [REPO skills/shadcn/SKILL.md rad 10–28, 177–186]. Vår mall har `astro` och `sharp`
  som enda beroenden (`mall/astro/package.json` rad 10–13), byggstandarden kräver att innehåll och navigation fungerar
  utan JS (`kunskap/byggstandard.md:18`) och bygget skriver typsnitt, skala, radie och avstånd som en egen
  specifikation per verksamhet (`.claude/skills/bygg-sajt/SKILL.md:193–195`). Sämre för oss, och krockar med ett
  medvetet val. (2) **Formulärreglerna:** etikett per fält, `aria-invalid` på kontrollen och felbeskedet vid fältet
  [REPO skills/shadcn/rules/forms.md rad 14–29, 173–192]. Mallens `Forfragan.astro` har etikett per fält (rad 14–29),
  byggstandarden kräver fel vid fältet (5.4), och felbeskedet utan JS ligger redan som vilande post
  (B-20261002-mallens-formular-visar-ett-felbesked-utan-javasc). Lika. (3) **Typeset**, nytt sedan förra bedömningen:
  en CSS-fil utan JS som sätter rytmen för löptext ur tre värden, storlek, radhöjd och flöde [REPO typeset.mdx rad
  10, 33–35; typeset.css rad 7–14], byggd för renderad markdown och strömmande chatt [typeset.mdx rad 6–8, 215–221].
  Våra sajter renderar ingen markdown; löptexten på integritets- och tjänstesidor sätts av riktningens egen skala. Att
  lägga in en färdig rytm (radhöjd 1,75, rubriker i vikt 600, rundade bilder [typeset.css rad 12, 59, 349]) vore ett
  standardutseende ovanpå riktningen, och radlängden lämnar den uttryckligen åt layouten [typeset.mdx rad 95]. Lika
  eller sämre
- Skäl: shadcn/ui är ett komponentbibliotek för appar i React och Tailwind [REPO README.md rad 3; SKILL.md rad 10],
  och det syns. Demon är fortfarande en vägg av likformiga rundade kort i gråskala med dollarbelopp, sparmål och
  inloggningsfält [BILD shadcn-sida-20261002/desktop-hela.png], förhandsbilden en mörk instrumentpanel för "Acme Inc."
  [BILD opengraph-image.png], och i 390 px skärs kortens tredje kolumn av i högerkanten [BILD mobil-forsta.png]. Det är
  det SaaS-kortkit som vi räknar som generiskt, inte något som gör en hantverkarsajt mer deras egen; ägarens domar
  L1–L3 berömmer det som är härlett ur verksamheten och pekar ut de generiska mönstren som det svaga (`LARDOMAR.md`
  rad 29, 78). Dagens regel att en större verktygslåda sällan är dålig ändrar inte domen: skillen gäller bara projekt
  med en `components.json` [SKILL.md rad 3] och skulle aldrig väljas av ett Astro-bygge utan React, och det enda nya
  som passar vår stack, Typeset, löser ett problem vi inte har. Källkritik: "beautifully designed" och "thoughtful
  defaults" [REPO README.md rad 3; TEXT] är omdömen, inte belägg, och källan säljer bara sig själv
- Kostnad: ingen; inget tas in. Som skill vore det 104 tokens i varje session, 4 713 vid användning och 18 358 vid
  behov, plus ett CLI-anrop mot npm varje gång den laddas; som beroende React, React DOM, Tailwind och ett CLI med
  versionsunderhåll i varje bygge
- Säkerhet: förgranskningen HÖG, av mängden: 633 skript (eval/exec i release- och registerskript, miljövariabler i
  v0- och registerkod, nätanrop i registerhämtningen). Inga dolda tecken. De 27 agentriktade träffarna är
  installationsrader i dokumentationen och mallarnas README. Skillen ger sig själv rätt att köra paketets CLI via
  `npx`, `pnpm dlx` och `bunx` och kör ett sådant anrop redan när den laddas [REPO skills/shadcn/SKILL.md rad 5 och
  17]; `.cursor-plugin/plugin.json` startar en MCP-server via `npx`, och `.claude/settings.local.json` tillåter bland
  annat `npm test`, `cat` och WebSearch. Inget försök att styra kirurgen. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · browser-use/browser-use · nej
- Källa: https://github.com/browser-use/browser-use @ 302d8fc (ur klonens `.git/shallow`; senaste push
  2026-10-02T02:56Z), MIT; cirka 117 000 stjärnor, inte arkiverat; cirka 134 000 tokens text. Inte bedömd förut.
  Förgranskat. Läst: README i helhet, `skills/browser-use/SKILL.md` i helhet, `skills/qa/SKILL.md` i helhet och
  `skills/qa/references/methodology.md` i helhet. Biblioteket (`browser_use/`), skillsen cloud, open-source,
  remote-browser och x402 bara som namn och storlek i förgranskningen. Sett: `static/hard_benchmark_v2.jpg` och
  `static/NiceHack69.png`; README:s demo är en extern animation och öppnades inte. Ägarens not: ingen
- Steg: 6 (prov i riktig webbläsare) och granskaren i 5.6; inget annat
- Jämfört med i dag: (1) **Biblioteket** är en agent som styr en webbläsare åt en språkmodell, i Python med egen
  API-nyckel (OpenAI, Anthropic eller deras egen modell) och gärna deras molnwebbläsare [REPO README.md rad 95–150,
  219]. Vi har redan Playwright-vägen: provet kör `kontroller/webblasare/utforska.mjs` på upp till tolv sidor
  (`kontroller/prova.py:374`), som räknar konsolfel per sida (`utforska.mjs:91, 118`), och granskaren har sajten live,
  `sida.mjs` och `inspektera.mjs` för tillstånd (`kritik/GRANSKARE.md:22, 44–49`). Ett andra webbläsarramverk med egen
  modellnyckel ger inget som Claude-sessionen med bildseende och Playwright inte redan gör. Lika, med ett beroende
  till. (2) **qa-skillen** kör ett flöde i en riktig webbläsare och ger betyg 1–5, förankrat i om uppgiften gick att
  slutföra, med det svagaste kritiska flödet som totalbetyg och konsol- och nätverksfel som belägg [REPO
  skills/qa/references/methodology.md rad 81–125]. Granskaren gör samma sak med litteraturens metod: kognitiv genomgång
  av den primära handlingen och varje toppuppgift i mobilen med Whartons fyra frågor (`kritik/GRANSKARE.md:50–53`), och
  kriteriet Funktion frågar om varje toppuppgift går att lösa (rad 89–92). Lika eller sämre: källans rubrik är
  utvecklarens röktest, vår är förankrad i Wharton m.fl. 1994 (`kunskap/teoretisk-grund.md:38–39`). (3) **Kraven runt
  qa-skillen:** den får bara köras i deras molnwebbläsare, aldrig lokalt [REPO skills/qa/SKILL.md rad 39, 67], och en
  lokal sajt ska ut på internet genom en ngrok-tunnel [REPO methodology.md rad 7–9, 32–44]. Våra förhandsvisningar är
  privata. Sämre för oss
- Skäl: browser-use är byggt för att låta en agent utföra uppgifter på andras sajter (boka, fylla i, skrapa) [REPO
  README.md rad 50–52], inte för att bygga eller pröva en sajt, och den del som liknar provning, qa-skillen, har vi
  redan i granskarens kognitiva genomgång och i utforskningen. Det som skulle följa med är det vi medvetet håller
  borta: qa-skillen installerar själv med `curl | sh` och uv utan att fråga [REPO skills/qa/SKILL.md rad 49–55] och
  skaffar en API-nyckel genom att agenten själv registrerar sig hos tjänsten [REPO methodology.md rad 16], alltså
  installation och kontoskapande obevakat. browser-use-skillen låter agenten klicka bort Chromes egen fråga om
  fjärrstyrning via macOS hjälpmedelsbehörighet [REPO skills/browser-use/SKILL.md rad 120–135], att godkänna en
  säkerhetsfråga åt användaren. Källkritik: riktmärket är deras eget, en delmängd på 60 uppgifter, och bilden visar att
  den bästa modellen klarar cirka 77 procent och Claude Opus 5 cirka 50 [BILD static/hard_benchmark_v2.jpg]; det
  säger något om svåra uppgifter på främmande sajter, inget om provning av en egen statisk sajt. README säljer
  molnkrediter [REPO README.md rad 81] och vänder sig till agenter: läs deras llms.txt [rad 60] och klistra in en
  installationsprompt i Claude Code [rad 87–91]. Det följdes inte
- Kostnad: ingen; inget tas in. Som skills vore det 31–206 tokens i varje session och upp till 3 571 vid användning
  (qa 2 149, med 6 911 vid behov), plus Python-paket, uv, ngrok eller cloudflared och ett konto med API-nyckel
- Säkerhet: förgranskningen HÖG. Inga dolda tecken. De åtta agentriktade träffarna är bibliotekets egna systemprompter
  ("You are an AI" i `browser_use/agent/system_prompts/`) och kod och test för skydd av känsliga data, inte riktade
  till kirurgen. HÖG kommer av 414 skript med nätanrop, eval/exec och miljövariabler, `curl | sh` i `bin/setup.sh`,
  `CLOUD.md` och qa-skillen, och behörigheter i frontmatter: qa (Bash, Read, Task), x402 (Bash, Read, Write, Edit),
  remote-browser (Bash för sitt CLI). Källan innehåller instruktioner till agenter (README rad 60 och 87–91, qa-skillens
  självinstallation och självregistrering). Inget kördes eller installerades. Inget försök att styra kirurgen utöver
  README:s uppmaningar till agenter i allmänhet
- Förslag: inget ur källan. Egen innovation: under jämförelsen syntes att `kunskap/webblasare.md`, som bygget läser i
  steg 6 (`.claude/skills/bygg-sajt/SKILL.md:242`), anger verktygen under `verktyg/webblasare/` (rad 4, 76, 91) och
  beskriver en avskärmad besökare i `besok.mjs` (rad 16); här ligger verktygen i `kontroller/webblasare/` och
  `besok.mjs` finns inte. Samma döda sökväg står i `kunskap/bygge-referens.md:55`, `kunskap/formularsakerhet.md:37`,
  `kunskap/lansering.md:68` och tre hjälptexter i `kontroller/prelaunch.py` (rad 141, 241, 496)
- Utfall: —
- Backlog: B-20261002-webblasartexterna-pekar-pa-kontroller-webblasare (egen innovation)

### 2026-10-02 · mrdoob/three.js · nej
- Källa: https://github.com/mrdoob/three.js @ f0f1455 (ur klonens `.git/shallow`; senaste push 2026-10-02T13:18Z),
  MIT; cirka 116 000 stjärnor, inte arkiverat; version 0.186.0 (r186); cirka 750 000 tokens text. Inte bedömd förut.
  Förgranskat. Läst: README i helhet, `docs/llms.txt` i helhet, `package.json` (version och ingångar), förgranskningens
  dolda tecken och riskmönster. Biblioteket (`src/`), exemplen, editorn och manualen bara som fillista. Sett:
  https://threejs.org öppnad i dag, desktop första vyn och skrolläge 4 av 8, mobil första vyn. Bibliotekets storlek
  mättes inte (mätkommandot nekades i den här körningen). Ägarens not: ingen
- Steg: 5 (bygge: rörelse och 3D i sidan); inget annat
- Jämfört med i dag: three.js är ett JavaScript-bibliotek som ritar 3D i en canvas med WebGL eller WebGPU [REPO
  README.md rad 9–11]; README:s grundexempel är en kub som snurrar i en animationsloop över hela fönstret [rad 44–55].
  Hos oss är principen att innehåll och navigation fungerar utan JS (`kunskap/byggstandard.md:18`), med budget 200 kB
  JS per sida (3.7, rad 52) och krav på `prefers-reduced-motion` när sidan har rörelse (3.5, rad 50); bygget skriver
  "ingen JavaScript som inte behövs" (`.claude/skills/bygg-sajt/SKILL.md:202`), och litteraturen bakom är HTML före JS
  (`kunskap/teoretisk-grund.md:47–48`, 119). De tre dömda byggena hade 0 kB JS och inga tredjepartsanrop (`LARDOMAR.md`
  rad 31, 56, 63, 87). Klonen har ingen träff på `prefers-reduced-motion` utanför minifierade filer, så hänsynen till
  rörelse vore helt vårt eget arbete. Ingen motsvarighet hos oss att jämföra mot sak för sak, eftersom vi medvetet inte
  har klientritad grafik; för oss sämre
- Skäl: three.js är ett utmärkt bibliotek för det det gör, men det gör spel, portfolior, konstprojekt och
  produktkonfiguratorer: galleriet på threejs.org är just det, lerfigurer, bilspel, en snookerbana, en "Design the next
  iPhone", en smyckesvisare och en kamera [BILD threejs-sida-20261002/desktop-forsta.png, desktop-skroll-04.png]. Våra
  verksamheter är lokala hantverkare där ägaren dömt det härledda och verkliga som det bästa (byggdagbok med egna
  telefonbilder, ordagranna omdömen) och bristen på egna bilder som det sämsta (`LARDOMAR.md` L1–L3). En 3D-scen
  kräver en modell som ingen av dem har, ger ingen text till sök eller skärmläsare, drar JS och GPU på mobilen och
  löser inget av de gap ägaren pekat på; det är dekoration, och krockar med ett medvetet val (minimal klient-JS). Det
  enda läge där domen kunde ändras är en framtida kund vars vara är ett föremål med färdig 3D-modell (till exempel
  trappor eller kök på beställning); det bedöms då med det fallet framför sig. Källkritik: källan säljer inget;
  README:s "lightweight" och "easy-to-use" [REPO README.md rad 11] är egna omdömen. `docs/llms.txt` har ett avsnitt med
  instruktioner till språkmodeller som skriver three.js-kod [REPO docs/llms.txt rad 5–81], bland annat att hämta
  biblioteket från ett CDN; det gäller kodgenerering, inte kirurgen, och följdes inte
- Kostnad: ingen; inget tas in. Som beroende vore det biblioteket och eventuella tillägg i varje sida som använder det,
  plus modeller och texturer, och versionsuppföljning (r186 i dag, med en egen migreringsguide [REPO README.md rad 17])
- Säkerhet: förgranskningen HÖG, av mängden: 1 737 skript (eval/exec i editorn och dess vendorbibliotek, nätanrop i
  laddare och dekodrar, base64-klumpar i WASM-dekodrar). Tolv dolda tecken: nollbredds- och BOM-tecken i fem
  typsnitts-JSON under `examples/fonts/droid/`, där de är glyfnycklar i en teckentabell, och U+200C/U+200D på en lång
  rad i den medföljande parsern `editor/js/libs/acorn/acorn.js:879`, som förtecknar tillåtna identifierartecken; inget
  gömmer text. Inga skills, hookar eller behörigheter. Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · Reddit-inlägget "My opinionated guide to building a website with …" (r/ai_website_builder) · parkera
- Källa: https://www.reddit.com/r/ai_website_builder/comments/1wuzspa/my_opinionated_guide_to_building_a_website_with/
  @ 2026-10-02, licens okänd. Inte bedömd förut. Inlägget gick inte att läsa: `kontroller/sida.mjs` fick Reddits
  robotkontroll "Prove your humanity" med reCAPTCHA i både mobil och desktop [BILD
  reddit-opinionated/desktop-forsta.png]; old.reddit skickade till inloggning; WebFetch nekas för reddit.com;
  webbsökning på rubriken gav ingen träff, och sökning begränsad till reddit.com vägras. Ingenting av inläggets text,
  bilder eller kommentarer är sett. Det enda kända är subredditen och rubrikens början ur adressen; resten av rubriken
  (vilket verktyg guiden gäller) är avkapad. Ägarens not: ingen
- Steg: okänt; rubriken antyder steg 4–5 (design och bygge), men det är en gissning ur adressen
- Jämfört med i dag: ingen jämförelse möjlig utan innehållet. Samma spärr mötte "How I Sold 200 Websites" 2026-10-01
  (`kunskap/REGISTER-arkiv-20261001.md` rad 153–154), som bedömdes först när ägaren laddade upp skärmbilder
- Skäl: domen gäller åtkomsten, inte meriterna; jag påstår inget om en text jag inte sett. Parkerad tills inlägget
  finns i läsbar form, till exempel som skärmbilder eller inklistrad text från dashboardens uppladdning, och bedöms då
  som en ny post. Källkritik i förväg: r/ai_website_builder är ett forum kring AI-sajtbyggare där guider ofta pekar
  på ett visst verktyg; det vägs när texten är läst
- Kostnad: ingen; inget tas in
- Säkerhet: förgranskningen av den hämtade texten (robotkontrollens 367 tecken) gav inga fynd; ingen källtext lästes
- Förslag: inget
- Utfall: —
- Backlog: ingen
