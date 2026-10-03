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

### 2026-10-02 · JuliusBrussee/caveman · nej
- Källa: https://github.com/JuliusBrussee/caveman @ b39c908 (ur klonens `.git/refs/heads/main`; senaste push
  2026-10-01T19:57Z), Apache-2.0 från version 3.0.0; cirka 109 000 stjärnor, inte arkiverat; 946 textfiler, cirka
  337 000 tokens text. Inte bedömd förut. Förgranskat. Läst: README (655 rader), CLAUDE.md, AGENTS.md,
  SECURITY.md rad 1–80, `docs/HONEST-NUMBERS.md`, `.codex/hooks.json`, och hela SKILL.md för caveman,
  caveman-compress, caveman-review, cavecrew, caveman-learn, caveman-evidence-review, investigate-first, lean-build
  och verify-and-stop; de flaggade raderna i `benchmarks/run.py` och `caveman-compress/scripts/compress.py` i sitt
  sammanhang. Övriga åtta skills (commit, help, stats, setup, discover, manage, optimize, explore, surgical-patch,
  safe-refactor, migration) bara som namn och beskrivning i förgranskningen. Bilder: `docs/assets/learn-report.png`,
  `docs/assets/pixel-sample.png`, `docs/assets/caveman-logo-banner.png`, `extension/store-assets/screenshot-2-compare.png`.
  Proxyn, motorn och webbläsardelen (Go och TypeScript) lästes inte i kod; demon är ett program, inte en sajt att se.
  Ägarens not: ingen
- Steg: inget av de åtta; ramarna för körningen (`kor.sh`, modellens kontext) och hur A/B:n mäts (`kontroller/ab.py`)
- Jämfört med i dag: källan är tre saker som alla sparar tokens åt den som kör en kodagent: en skill som gör agentens
  prosa kortfattad, en lokal proxy som krymper det agenten läser (loggar, JSON, diffar, testutdata), och ett
  mellanlager för egna appar [REPO README.md rad 84–86]. Sak mot sak. (1) **Skillen** styr agentens svar till
  människan: stryk artiklar, utfyllnad och artighet, inga berättande rader mellan verktygsanrop, tillsammans med
  Simplified Technical English (en idé per mening, högst 20 ord, aktiv form) [REPO skills/caveman/SKILL.md rad 19,
  25, 27]. Allt som sparas utanför chatten (kod, dokument, commits, minnesfiler) skrivs i vanlig prosa [rad 89], och
  kod, kommandon och felmeddelanden rörs aldrig [REPO README.md rad 70]. Hos oss läser ingen människa byggets
  löpande svar: körningen är obevakad (`.claude/skills/bygg-sajt/SKILL.md:20`, `kor.sh:36`) och det som ska läsas
  (RAPPORT.md, INNEHALL.md, registret) är just det källan undantar. Sajtens text får aldrig skrivas så: utan artiklar
  och i fragment vore den inte verksamhetens röst (`bygg-sajt/SKILL.md:138`, `kunskap/copy-kontroll.md:27–29`), och
  klarspråk och korta meningar står redan hos oss med Språkrådet och LIX som måttstock (`kunskap/teoretisk-grund.md:
  107–108`). Inte tillämpligt för sajten; för agentens svar sparar den tokens som ingen läser ändå. JetBrains mätte
  8,5 procent färre utdatatokens och ingen mätbar kvalitetsändring på 86 kodningsuppgifter [REPO README.md rad 205];
  källan skriver själv att reglerna kostar indatatokens i varje anrop och att nettot beror på arbetslasten, med en
  Cursor-mätning där tokens blev fyra gånger fler [REPO docs/HONEST-NUMBERS.md rad 30–38]. (2) **Proxyn** sitter
  mellan Claude Code och Anthropic, krymper verktygsresultat förlustfritt för agenten (originalet sparas lokalt och kan
  hämtas tillbaka) och släpper igenom Max-inloggningen [REPO README.md rad 108, 364]. Vinsten mättes till 33 procent
  färre indatatokens på sex uppgifter med CSV, loggar, YAML och JSON, men HTML-fallet blev 9,9 procent dyrare [rad
  224–238]. Våra byggen läser skärmbilder (bilder krymps inte), HTML och markdownrapporter, alltså källans svagaste
  fall. Att sätta en proxy mellan bygget och modellen krockar med två medvetna val: inget installeras och ingen kod ur
  källor körs (`.claude/skills/kirurg/SKILL.md`, Säkerhet; `kor.sh:61–62` laddar inte ens MCP-anslutningar i bygget), och
  det som bygget läser (provets PROV.md, copyrapporten, granskarens fynd) ska nå det oavkortat. CLI:n skickar dessutom
  användningsstatistik med installations-id och IP-adress tills man stänger av den [REPO README.md rad 259, 597–599].
  Sämre för oss. (3) **caveman-compress** skickar en skilltext till Anthropics API och skriver tillbaka den utan
  artiklar och utfyllnad, 46 procent mindre på fem fixturer utan påstående om bevarad betydelse [REPO
  skills/caveman-compress/SKILL.md rad 12, 24–33; README.md rad 245]. Vi tog 2026-10-02 in writing-for-agents för samma
  behov (`.claude/skills/writing-for-agents/`, registret ovan): rensa dubbletter, inaktuella lager och no-ops med
  bibehållen mening, i den som ändrar textens hand. Det är bättre än en mekanisk förkortning, och ägaren har sagt att
  kvalitet går före tokens. Sämre. (4) **caveman-review** ger en rad per fynd, plats, problem, rättning [REPO
  skills/caveman-review/SKILL.md rad 12]; vår granskare kräver observation, konsekvens, standardpunkt, omfattning,
  rättning och ett acceptanskriterium i EARS-form per blockerande fynd (`kritik/GRANSKARE.md:116–125`), för att
  byggaren ska kunna rätta och nästa granskning pröva. Sämre. (5) **Arbetsmönstren** investigate-first, lean-build och
  verify-and-stop är omärkta, generella regler på cirka 120 tokens för kodarbete [REPO CLAUDE.md rad 128]:
  verify-and-stop säger "bevisa acceptansvillkoren och sluta" [REPO skills/verify-and-stop/SKILL.md rad 8–16], vilket
  stoppvakten gör som mekanik hos oss (`bygg-sajt/SKILL.md:359–361`). Lika eller inte tillämpligt. (6) **caveman
  learn** mäter var en agents tokens går, lokalt ur sessionsloggarna: setupfiler som laddas i varje tur, återklistrad
  kontext, och hur djupt sessionerna går i modellens fönster, med regeln "past half the window answers tend to get
  worse (a common rule of thumb)" [REPO README.md rad 427–447; BILD docs/assets/learn-report.png: 6 av 41 sessioner
  över halva fönstret]. Varje rättning godkänns en i taget och ångras om mätningen inte sjunker [REPO
  skills/caveman-learn/SKILL.md rad 46–53]. Vår A/B mäter turer, minuter och granskarens betyg ur samma slags logg
  (`kontroller/ab.py:45–62`), men inte kontextdjupet. Våra loggar visar att byggen går djupt: i det blinda effortparet
  nådde A (effort high) 813 339 tokens läst kontext och låg över 500 000 i 238 av 653 meddelanden
  (`kunder/lulea-snickaren-abx/korning-20261002T122340Z.jsonl` rad 2252), B (effort medium) nådde drygt 500 000 i de
  sista 77 av 562 (`kunder/lulea-snickaren-aby/korning-20261002T142113Z.jsonl` rad 1309, 1548), och ägaren valde B
  blint (`LARDOMAR.md:99–104`). Ett par bevisar inget, men variabeln är värd att skriva upp. Det blir den egna
  innovationen
- Skäl: källan hjälper oss inte bygga bättre sajter och inte arbeta smartare. Dess hela värde är färre tokens hos
  en människa som läser agentens svar och betalar per token; våra byggen körs obevakade på ägarens abonnemang, och
  ägaren har sagt att kvalitet går före tokens. Det som skulle kunna spara i ett bygge, proxyn, krockar med att inget
  installeras och ingen kod ur källor körs, är svagast på just det våra byggen läser, och ringer hem tills den tystas.
  Att kortfatta agentens svar är ofarligt men meningslöst när ingen läser dem, och får aldrig nå sajtens text eller
  skilltexterna, där vi redan har bättre metoder. Källkritik: projektet är ovanligt ärligt, med en röd rad som står kvar
  i tabellen, en egen sida över när det förlorar och ett maskinskrivet förbud mot påhittade siffror [REPO README.md rad
  238; docs/HONEST-NUMBERS.md; CLAUDE.md rad 406]; de starkaste talen (65 procent i beskrivningen) motsägs av dess
  egen sida ("not published"). README:n säljer en väntelista till Caveman Cloud [REPO README.md rad 589] och
  stjärnorna säger inget om nyttan. Källan innehåller instruktioner till agenter som en del av produkten: AGENTS.md
  laddar fyra skills i varje session [REPO AGENTS.md rad 12–15], en Codex-krok skriver "CAVEMAN MODE ACTIVE" vid
  sessionsstart [REPO .codex/hooks.json rad 9] och pluginens SessionStart-krok skjuter in regelverket som dold
  systemtext [REPO CLAUDE.md rad 263]; inget av det gällde kirurgen och inget följdes
- Kostnad: inget tas in. Skillen vore 59 tokens i varje session och 1 649 vid användning enligt förgranskningen;
  proxyn ett npm-paket, en Go-binär, en SQLite-fil och en process som ska startas före varje bygge. Den egna
  innovationen kostar några rader i `kontroller/ab.py` och inga tokens
- Säkerhet: förgranskningen HÖG, inga dolda tecken. HÖG kommer av 497 skript: installation via `curl | bash`
  (`install.sh`, README), en installatör på 2 120 rader som skriver utanför repot (`bin/install.js`), krokar i
  SessionStart och UserPromptSubmit (`.claude-plugin/plugin.json`, `.codex/hooks.json`), binärnedladdare med nätanrop
  och telemetri på som standard. De fem ställena med text till agenter är i sitt sammanhang en kommentar om att inte
  exportera hela `.env.local` (`benchmarks/run.py` rad 30–35), en vägran att komprimera filer som ser ut att
  innehålla hemligheter (`compress.py` rad 601–611) och testfixturer för promptinjektion. Inget kördes eller
  installerades
- Förslag: inget för källan. Egen innovation: `kontroller/ab.py` `matt()` (rad 45–62) läser redan körningens logg;
  lägg till `kontext_max` (största summan av input, cache_creation och cache_read i ett meddelande) och
  `over_halva` (antal meddelanden över halva modellens fönster), så att de står i A/B-posten och i LARDOMAR.md:s
  AB-rad bredvid turer och minuter. Ingen regel, bara mätning: när fem par finns syns om ägarens val följer djupet
- Utfall: ab.py mäter kontext_max och over_halva 2026-10-03; paret lulea-snickaren-abx/-aby 694 131/243 och 563
  203/79 ur loggarna.
- Backlog: ingen för källan; egen innovation: B-20261002-mat-kontextdjupet-per-bygge-i-a-b-posten-storsta

### 2026-10-02 · pbakaus/impeccable · ta in
- Källa: https://github.com/pbakaus/impeccable @ 508d7e8 (ur klonens `.git/shallow`; senaste push 2026-10-02T07:05Z;
  tagg skill-v4.5.0), Apache-2.0 (Paul Bakaus), cirka 74 000 stjärnor, inte arkiverat. Cirka 2,6 miljoner tokens text
  i 2 806 filer; skillen finns i tjugo kopior, en per verktyg, var och en 226 tokens alltid, cirka 2 700 vid
  användning och cirka 536 000 vid behov (nästan allt är `scripts/data/font-index.json` och `live-browser.js`).
  Förgranskat. Använd i Digitala 2026-09 (`kunskap/LARDOMAR-digitala.md:145`, `kunskap/skapandeunderlag.md:153`) men
  aldrig bedömd i registret; hermes-posten ovan (rad 435) sköt upp den. Läst själv: README, `.claude/skills/impeccable/
  SKILL.md`, `reference/craft-floor.md`, `critique.md`, `new-work.md`, `typeset.md`, `layout.md`, `polish.md`,
  `mode-persuade.md`, `init.md` rad 25–54, `doctor.md` rad 25–31, `hooks.md` rad 1–25, launchern `scripts/impeccable`,
  `.claude/settings.json`, `.agent/skills/impeccable/SKILL.md` rad 1–9, `crates/foundation/src/registry.rs` rad
  30–120, 240–270, 410–500 och 840–845, `constants.rs` rad 83–107, `crates/core/src/checks/rules.rs` rad 35–90 och
  864–871, `html_patterns.rs` rad 468–513, `crates/core/src/browser/page_checks.rs` rad 306–311, `quality.rs` rad
  658–675, `crates/context/src/concept_seed.rs` rad 130–190, `context_cli.rs` rad 468–491, `docs/CLI-CONTRACT.md`
  rad 436–440, `tests/live-e2e/agent.mjs` rad 1524–1528. Läst i helhet av två subagenter med belägg (domen är min):
  alla 45 referensfiler, `docs/`, detektorregistret och koden bakom varje regel. Demon: impeccable.style/cases/
  neo-mirai som webbsida; läst 6 av 12 bilder (mobil och desktop första vy, båda helsidor, skroll 03 och 05) och
  texten. Bilderna i repot är testfixturer och ikoner (26 filer), inte lästa. Ägarens not: ingen
- Steg: 6 (provets stilrapport) och 5.1 (upptagna val); egen innovation i 5.6 (granskarens läsordning)
- Jämfört med i dag: (1) **Som paket.** Impeccable är en harness: 24 kommandon bakom ett `/impeccable`, en
  Rust-binär som launchern laddar ner från GitHub-releaser första gången [REPO .claude/skills/impeccable/scripts/
  impeccable rad 121–125, 149–180] och som SKILL.md kör i varje session [REPO SKILL.md rad 19], krokar vid
  SessionStart, PostToolUse och Stop [REPO .claude/settings.json rad 4–40], en lokal beslutssida, comp-ledd byggväg
  med bildgenerering mot OpenAI [REPO reference/new-work.md rad 53, 55, 101; crates/context/src/generate_image.rs rad
  249] och ett live-läge. Metoden tillåter påhittat demonstrationsmaterial märkt syntetiskt: "Refusing a bold
  direction because its demonstration data does not exist yet is the timidity reflex wearing honesty's clothes" [REPO
  reference/new-work.md rad 59, 127]. Demon Neo Mirai är en fiktiv konferens byggd ur två AI-genererade bilder [TEXT
  rad 15, 26; BILD desktop-hela.png]. Vårt: steg 1–7 med egna kontroller, inga krokar som kör nedladdad kod, bara
  verksamhetens egna bilder och ord, "Hitta aldrig på" (`bygg-sajt/SKILL.md:20–22, 77`). Krockar rakt. (2)
  **Detektorn.** 61 regler, 32 slop och 29 kvalitet, i ett register med trösklar i kod [REPO crates/foundation/src/
  registry.rs rad 32–643, antalet prövat rad 843]. gstack-intaget tog sex av dem via gstacks katalog
  (`B-20261002-stilrapporten-mater-sex-renderade-monster-ur-gst`, `kontroller/stil.mjs:85–98`), och stil.mjs prövar nu
  ett tjugotal mönster (rad 111–118, 174–200). Fem till går att läsa ur den renderade sidan och saknas hos oss, och de
  träffar luft och hierarki, den enda dimension ägaren satte "Okej" på i alla tre domarna (`LARDOMAR.md:35, 60, 84`):
  rubrik som sitter närmare blocket ovanför än sitt eget innehåll [REPO registry.rs rad 464–469; page_checks.rs rad
  307–311: minst två överträdelser, underskott 12 px], enformig luft med ett avståndsvärde över 60 procent av minst tio
  och högst tre unika [REPO html_patterns.rs rad 475–496], platt typskala utan något steg på 1,25 mellan grannar
  [REPO rules.rs rad 869–871], färgad kant på en sida av kort eller citat, 2 px med radie eller 3 px utan, minst
  dubbelt mot övriga sidor, "the most recognizable tell of AI-generated UIs" [REPO rules.rs rad 50–87; registry.rs rad
  34–39], och brödtext under 12 px [REPO quality.rs rad 661]. Källans radlängd (80, utlöst över 85) och radhöjd (1,3)
  är slappare än våra 45–75 och 1,4 (`stil.mjs:186–187`, byggstandarden 3.1); vi behåller våra. Tryckytor, som README
  lovar [REPO README.md rad 466], finns inte som regel; vi mäter dem (`stil.mjs:72–84`). Smartare: mätt i stället för
  bedömt, information aldrig grind. (3) **Typsnitt.** Två namngivna listor: detektorns 17 överanvända, Inter till
  Recoleta [REPO constants.rs rad 85–105], och sexton "training-data defaults" för säljande ytor, Fraunces till
  Instrument Sans, med regeln att ett av dem kräver "a reason no other face could satisfy" [REPO reference/new-work.md
  rad 67]. Vår `kontroller/upptagna_val.py:26–37` beskriver tio standardval utan ett enda typsnittsnamn, och Anthropics
  frontend-design hos oss namnger inga (`kunskap/externa/anthropic-frontend-design-SKILL.md:21`). Byggena valde
  Schibsted Grotesk och Archivo (`underlag/lulea-snickaren-aby/JAMFORELSE.md:9`, `underlag/sundboms-el/
  JAMFORELSE.md:16`), inga på listorna, men valet var oinformerat. Smartare: byggaren ser namnen före valet, och
  regeln "ett upptaget val är tillåtet när verksamhetens material motiverar det" (`bygg-sajt/SKILL.md:196–198`) gäller
  oförändrad. (4) **Riktning.** new-work tar sju kandidater ur publikens kulturella värld, håller "the page this
  category always ships and its predictable opposite" utanför listan och självprovar: "if someone could guess your
  aesthetic from the category alone, or from category-plus-avoidance, rework" [REPO reference/new-work.md rad 45–46,
  69]. Vårt steg 5.1 kräver fyra riktningar ur verksamheten själv, aldrig ur en branschmall, med namngiven axel och
  UPPTAGNA-VAL (`bygg-sajt/SKILL.md:200–212`). Lika i sak; källans tärning kräver binären och ett anrop till
  impeccable.style/api/roll [REPO concept_seed.rs rad 80, 117] och förbjuder att hoppa över [rad 48]: nej till den.
  Kalibreringslistan (kräm plus serif plus terrakotta, svart plus neon, tidningshårlinjer) [rad 69] står redan hos
  oss (`anthropic-frontend-design-SKILL.md:38–45`); impeccable utgår från den skillen [REPO README.md rad 9]. (5)
  **Granskning.** critique.md kör två isolerade bedömningar och släpper inte in detektorns fynd förrän
  designbedömningen är klar: "Detector output is deterministic, but it still anchors judgment" [REPO reference/
  critique.md rad 8–10]. Vår granskare får stilrapporten och copykontrollen i uppdraget från början med rådet att inte
  pröva det igen (`kritik/GRANSKARE.md:30–32`) och sätter originalitetsbetyget med varningslistan i hand. Det blir den
  egna innovationen. Nielsen 0–4 per heuristik med n/a för 7 och 10 på säljande ytor [rad 120] gäller inte oss, som
  inte betygsätter per heuristik (`GRANSKARE.md:57–61, 70–98`). Personerna Jordan och Casey [rad 664, 746, 779] är
  vår namngivna besökare i den kognitiva genomgången, redan intagen
  (`B-20261002-a-b-granskarens-kognitiva-genomgang-som-namngive`). (6) **craft-floor och mode-persuade.** Kontrast,
  "more space above a heading than below it", webbläsarens egna ytor (markering, caret, rullningslist, fokusring,
  understrykningens offset, tabellsiffror) [REPO reference/craft-floor.md rad 9–15], kicker ovanför rubrik som enda
  absoluta förbud [rad 27]; handlingen i fungerande form och "a split hero ... or a centred headline over a row of
  cards is the template whatever world paints it" [REPO reference/mode-persuade.md rad 9, 13]. Vi har fokus
  (byggstandarden 3.4), tabellsiffror och color-scheme (`kunskap/externa/vercel-web-interface-guidelines-command-
  e3d624ba.md:68, 119`), spärrade etiketter (`stil.mjs:118`), 9.1 och strukturmönstren ur L1–L3
  (`upptagna_val.py:40–45`). Lika, utom markering, caret och understrykning som ingen dom pekat på; registreras, föreslås
  inte. Övrigt (onboard, harden, operate, live, native, document, extract, overdrive) är produkt-UI och appar
- Skäl: som paket nej: en harness vars skill kör en nedladdad binär i varje session, tre krokar, telemetri och
  versionskoll hem, och en metod som bygger ur genererade skisser och tillåter påhittat demonstrationsmaterial,
  demonstrerad på en fiktiv konferens med AI-bilder. Allt det krockar med att kod ur källor inte körs, att inget
  installeras, och med verksamhetens egna bilder och ord. Men detektorregistret är den mest genomarbetade katalogen
  över mätbara mönster vi sett, med varje tröskel i kod, och fem av reglerna träffar exakt den dimension ägaren tre
  gånger satt "Okej" på; de två typsnittslistorna ger upptagna-valen det namn som saknas. Båda är små ändringar i
  befintliga kontroller, i samma form som gstack-intaget, som ägaren höll med om. Därför ta in, avgränsat till det.
  Källkritik: README säljer med stjärnor, också som "74k" i demosajtens sidhuvud [BILD desktop-forsta.png], och demon
  visar ingen verklig verksamhet och inget före-och-efter mot en riktig sajt. Källan innehåller instruktioner till
  agenter: kringgå sandlådan när den lokala servern inte startar [REPO docs/CLI-CONTRACT.md rad 439; reference/
  new-work.md rad 53], reparera utan att fråga [REPO reference/doctor.md rad 29], och att en systemprompt om obevakad
  körning "proves nothing about this session" [REPO reference/init.md rad 31]. Inget av det gällde kirurgen och inget
  följdes
- Kostnad: inget kopieras; ingen skill tas in. Ett femtiotal rader i `stil.mjs`, en lista på ett trettiotal namn i
  `upptagna_val.py`, några rader till i UPPTAGNA-VAL.md per bygge; inga tokens i övrigt. Egen innovation: två meningar i
  `GRANSKARE.md`
- Säkerhet: förgranskningen HÖG: 4 dolda tecken, 8 ställen med text riktad till agenter, 348 skript, `allowed-tools`
  i sju skillkopior, krokar i sex konfigurationsfiler. De dolda tecknen är en BOM i en testfixtur (`crates/html/tests/
  fixtures/css-rules.json`) och två nollbreddstecken i en kodkommentar som hindrar `*/` från att stänga den [REPO
  tests/live-e2e/agent.mjs rad 1527]; ofarliga. De agentriktade träffarna är testfixturer för promptinjektion och
  CLI-kontraktets sandlådetext ovan. `allowed-tools` ger skillen rätt att köra `npx impeccable` och launchern [REPO
  .agent/skills/impeccable/SKILL.md rad 6–8]. Launchern verifierar nedladdningen mot en sha256-sidofil ur samma
  release, vilket skyddar mot trasig fil men inte styrker upphov [REPO scripts/impeccable rad 149–180]; `live-browser.js`
  är 13 511 rader med nätanrop och eval. Nätanrop utöver binären: telemetri som POST till impeccable.style/api/chosen,
  avstängbar med DO_NOT_TRACK [REPO crates/context/src/concept_seed.rs rad 135–137, 187], versionskoll mot
  impeccable.style/api/version som skjuter in en UPDATE_AVAILABLE-text till agenten [REPO context_cli.rs rad 480,
  489–491], och bildgenerering mot api.openai.com [REPO generate_image.rs rad 249]. Inget kördes eller installerades.
  Inget försök att styra kirurgen
- Förslag: `kontroller/stil.mjs`, i `matPaSidan()` och varningarna, information aldrig grind, trösklarna med egna ord
  och källan i filhuvudet som för gstack: (1) rubrikrytm: h2 och h3 i main där luften ovanför är minst 12 px mindre än
  luften under, varning när minst två rubriker på sidan bryter; (2) enformig luft: vertikala margin, padding och gap på
  main-block avrundade till 4 px, varning när ett värde står för över 60 procent av minst tio mätningar och högst tre
  unika finns; (3) platt typskala: storlekarna för h1–h3, p och li sorterade, varning när största steget mellan två
  grannar är under 1,25; (4) färgad sidkant: kant på en sida, minst 2 px med radie eller 3 px utan, minst dubbelt mot
  övriga sidor och inte neutral färg; (5) brödtext under 12 px i p, li eller dd. `kontroller/upptagna_val.py`
  `MODELLENS_STANDARDVAL` (rad 26–37): en rad "typsnitt modellerna faller tillbaka på" med de 17 och 16 namnen utan
  dubbletter. Rökprovet grönt. Egen innovation: `kritik/GRANSKARE.md` "Så granskar du": betygen på designkvalitet och
  originalitet sätts innan stilrapporten och copykontrollens rapport öppnas; de läses sist och lägger bara till fynd
- Utfall: fem renderade mönster i stilrapporten och modellernas standardtypsnitt i UPPTAGNA-VAL.md 2026-10-03.
  Betygsordningen (egen innovation) prövad i granskarförsöket: omdömesfel 4,1 → 4,3 per bygge, inga falska
  blockerande; införd i GRANSKARE.md.
- Backlog: B-20261002-stilrapporten-mater-fem-renderade-monster-ur-imp; egen innovation:
  B-20261002-granskaren-satter-originalitetsbetyget-innan-hen

### 2026-10-02 · coreyhaines31/marketingskills · ta in
- Källa: https://github.com/coreyhaines31/marketingskills @ 13c3832 (ur klonens `.git/logs/HEAD`; senaste push
  2026-10-02T18:32Z; tagg v2.11.11), MIT (Corey Haines), cirka 52 000 stjärnor, inte arkiverat. 473 textfiler, cirka
  710 000 tokens text, 50 skills. Inte bedömd förut. Förgranskat. Läst själv: README (349 rader), AGENTS.md,
  CONTRIBUTING.md, `tools/PARTNERS.md`, `.claude-plugin/plugin.json`, `.github/workflows/validate-skill.yml`, början
  av `.github/scripts/sync-skills.js` och `tools/clis/resend.js`, och hela SKILL.md för de tolv skills som kan röra
  en sajt åt en verksamhet: copywriting, copy-editing, cro, seo-audit, schema, site-architecture, customer-research,
  marketing-psychology, product-marketing, image, ai-seo och marketing-council (rad 1–70). Referenser lästa i helhet:
  `copywriting/references/ai-tells.md` och `copy-frameworks.md`, `copy-editing/references/checklist.md`,
  `cro/references/form.md`, `seo-audit/references/ai-writing-detection.md`, `schema/references/schema-examples.md`,
  `site-architecture/references/site-type-templates.md`, `copywriting/evals/evals.json`, `cro/references/
  experiments.md` rad 1–80, och den flaggade raden i `ads/references/audit-guardrails.md` i sitt sammanhang. Övriga 38
  skills (annonser, ASO, churn, kalla mejl, paywalls, prissättning, referral, RevOps, SMS, sociala medier, video,
  events, lanseringar …) bara som beskrivning i README och förgranskningen. Repot har inga bilder och ingen demosajt;
  inget att se. Ägarens not: ingen
- Steg: 4 (innehåll före form, humanizer-passet); berör också 1, 3, 5 och 6 där det visade sig lika eller sämre
- Jämfört med i dag: källan är ett bibliotek för marknadsförare på SaaS- och B2B-bolag: 50 skills som alla först
  läser en kontextfil om produkten [REPO README.md rad 31; product-marketing/SKILL.md rad 12], 60-talet CLI-skript mot
  marknadsföringstjänsters API:er med nycklar ur miljön [REPO AGENTS.md rad 24; tools/clis/resend.js rad 3–8], ett
  partnerprogram där verktyg köper disklad placering [REPO tools/PARTNERS.md rad 12, 45–50] och en Claude
  Code-marknadsplats [REPO .claude-plugin/plugin.json]. Vi bygger sajter åt hantverkare och skickar ingenting
  (`.claude/skills/bygg-sajt/SKILL.md:50–51`); kampanjer, utskick, prissättning och annonser finns inte i våra åtta
  steg. Sak mot sak för det som ändå rör sajten. (1) **ai-tells.md** (copywriting) är en katalog över AI-mönster i
  säljtext, byggd på samma Wikipedia-lista som vår humanizer plus Kobak m.fl., Juzek & Ward och EQ-Bench [REPO
  ai-tells.md rad 248–259]. Mönstren finns redan hos oss: kontrastvändning, negationslista, tre-i-rad, tankstreck,
  retorisk fråga, fragment (`.claude/skills/humanizer/SKILL.md:215–233, 278–286, 495–518`; `kunskap/copy-kontroll.md:
  17`). Tre saker saknas hos oss. För det första skiljer källan **förbud** från **tak**: ett fragment och en lista på
  tre per sektion är hantverk, två är tic [REPO ai-tells.md rad 5–9, 92–102]; humanizer säger bara "overuse" utan
  gräns (`humanizer/SKILL.md:232–240, 495–505`). För det andra ett eget **register för kort text**: rubriker,
  underrubriker, knappar och ingress, där tankstreck och vändningar inte får förekomma alls [REPO ai-tells.md rad
  12–15, 104–108]; hos oss gäller samma regel för all text, och ägaren pekade i L3 ut just en rubrik ("Dagen efter,
  tre timmar senare") som det som lät skrivet (`LARDOMAR.md:83, 92`). För det tredje regeln **variera rättningarna**:
  blir varje vändning ", eftersom" och varje negationslista "det finns inget att", är det de nya ticen; skriv om ur
  sakuppgiften, aldrig med synonym [REPO ai-tells.md rad 220–231]. Vi kör humanizer på hela INNEHALL.md i varje bygge
  (`bygg-sajt/SKILL.md:184–185`) och har ingen sådan vakt mot att passet själv lämnar ett mönster. Smartare, och
  det är tre rader i humanizerns förord. Källans bytestest, "fungerar raden oförändrad hos en konkurrent, skriv om"
  [REPO ai-tells.md rad 224], har vi redan som läsning och FRASER.txt (`bygg-sajt/SKILL.md:147, 183`). Lika. Källans
  `[NEED: proof]` i stället för påhitt [rad 226] är vår beställning (`bygg-sajt/SKILL.md:20–24`). Lika. (2) **Resten
  av copywriting** är rubrikformler ("Never X again", "The {category} for {audience}"), knapptexter som "Start Free
  Trial" och en sidstruktur med logotyprad, "10,000+ teams" och garantier [REPO copywriting/SKILL.md rad 147–151,
  185–201; copy-frameworks.md rad 18–99, 229–243]. Det är mallar för SaaS; hos oss ska varje sektion bära en sak ur
  "Bara de har" och rubriken vara verksamhetens namn eller ett bokstavligt erbjudande (`bygg-sajt/SKILL.md:170–172,
  284–285`), och ägaren valde "Ring Dan" och "Ring Yoel" med numret utskrivet (`LARDOMAR.md:30, 54`). Formlerna är
  slopens råvara för oss. Sämre. Siffrorna "+81 % konvertering, −38 % säljcykel" saknar källa [REPO copywriting/SKILL.md
  rad 44; copy-frameworks.md rad 423–428]. (3) **copy-editing** gör sju pass i tur och ordning med återgång
  (klarhet, röst, "so what", bevis, specifikt, känsla, noll risk) och ett expertpanelsbetyg 1–10 av tre till fem
  personer i samma session tills alla ger 7+ [REPO copy-editing/SKILL.md rad 27–29, 259–269]. Bevis- och
  specifikpassen är vår kvittoregel och "Specifikt:" (`kunskap/copy-kontroll.md:29–31`, `bygg-sajt/SKILL.md:170–172`);
  passet "känsla" ("paint the before state vividly", "fear of missing out") [rad 198–211] krockar med lugn, konkret
  svenska (`copy-kontroll.md:27–28`). Panelen i samma kontext är svagare än våra två isolerade granskare
  (`bygg-sajt/SKILL.md:255–262`). Lika eller sämre. (4) **cro** och **form.md**: värdebudskap på fem sekunder, en
  primär handling, förtroende nära knappen, få fält, synliga etiketter, svarstid vid formuläret [REPO cro/SKILL.md rad
  29–60; form.md rad 36–45, 116, 218–224]. Vårt: byggstandarden 9.1 och 6.1–6.8, femsekunderstestet, tacksidan som
  säger när (`kunskap/byggstandard.md:84–91, 119`; `kunskap/forfragan.md:13–22`; `bygg-sajt/SKILL.md:289–294`). Lika.
  Källan vill göra telefonen valfri [REPO form.md rad 73–77]; ägaren kräver den (`LARDOMAR.md:47`). Krock, ägaren
  gäller. (5) **seo-audit, schema, site-architecture**: lokalavsnittet säger samma NAP, lokalt schema, en sida per
  tjänst [REPO seo-audit/SKILL.md rad 414–419; site-type-templates.md rad 258–293]; schema-skillen listar FAQPage som
  rikresultat och en generisk LocalBusiness [REPO schema/SKILL.md rad 60–63; schema-examples.md rad 263–297], där vår
  standard kräver den mest specifika typen och vet att FAQPage slutade ge rikresultat i maj 2026
  (`kunskap/byggstandard.md:99, 142–144`; `kunskap/seo-lokal.md:9–14`). Lika eller vårt mer aktuellt. (6)
  **customer-research**: ordagranna citat, aldrig parafras, inga påhittade detaljer, säkerhetsnivå efter antal
  oberoende källor [REPO customer-research/SKILL.md rad 77–80, 97–103, 259]; vårt steg 1 kräver källa eller
  `antagande` per påstående och omdömen ordagrant med tjänsten de är skrivna hos (`bygg-sajt/SKILL.md:86–92`). Lika.
  (7) **marketing-psychology**: Fogg, Cialdini och Hicks lag står hos oss (`kunskap/teoretisk-grund.md:103–109`);
  källans knapphet, ankring, lockbete och 9-priser [REPO marketing-psychology/SKILL.md rad 247–250, 262–275, 293–296]
  är tekniker vi inte använder på en hantverkares sajt. Sämre. (8) **image** räknar stockfoto som ett alternativ
  [REPO image/SKILL.md rad 46]; hos oss aldrig (`bygg-sajt/SKILL.md:77`). Krock. (9) **ai-seo**, 7 310 tokens om
  AI-citeringar, llms.txt och prisfiler för SaaS; vår standard 7.6 säger att llms.txt inte behövs
  (`kunskap/byggstandard.md:102, 153`). Inte tillämpligt. (10) Källan har **evals** per skill, prompt med påståenden
  att pröva [REPO copywriting/evals/evals.json], men ingen körare i repot, bara CI:s formvalidering [REPO
  .github/workflows/validate-skill.yml rad 63–66]; vår mikroprövning av domändringar är redan i backloggen
  (`B-20261002-mikroprova-en-domandring-mot-en-kontroll-utan-an`). Lika. Att hitta och nå kunder senare: cold-email,
  prospecting och directory-submissions gäller SaaS-listor och B2B-utskick och är inte aktuella
- Skäl: som bibliotek nej: 50 skills för SaaS-marknadsföring, varav kanske tolv rör en sajt alls, och de tolv är
  antingen det vi redan har i våra egna ord, mallar som skulle ge oss just den slop vi bygger bort, eller tekniker
  som krockar med ägarens val (telefon krävs, inga stockbilder, lugn svenska). Men ai-tells.md är den skarpaste
  formuleringen vi sett av det humanizer gör, och tre regler där saknas hos oss: tak per sektion i stället för
  "overuse", ett strängare register för rubriker och knappar, och vakten mot att rättningen blir ett nytt mönster.
  Den sista träffar en risk vi själva infört genom att köra humanizer i varje bygge, och ägaren har i L3 pekat på
  rubriken som det stället där texten lät skriven. Tre rader i en fil vi redan laddar, därför ta in, avgränsat till
  det. Källkritik: README säljer upphovsmannens byrå, nyhetsbrev, kurs och en AI-marknadschef [REPO README.md rad 5]
  och två betalande partner står i README med disklad markering [rad 15–20]; partnerreglerna är ovanligt tydliga om
  att pengar köper placering men inte rekommendation [REPO tools/PARTNERS.md rad 12, 33–39]. Konverteringssiffrorna
  är obelagda; ai-tells.md:s källor är däremot verkliga och namngivna. Källan innehåller instruktioner till agenter:
  AGENTS.md ber agenten hämta VERSIONS.md från GitHub en gång per session och köra `git pull` när användaren säger
  "update skills" [REPO AGENTS.md rad 220–241], och rekommenderar skalkommandon som körs när skillen laddas [rad
  251–278]; inget av det gällde kirurgen och inget följdes. Den flaggade raden i audit-guardrails.md är tvärtom en
  vakt mot injektion i hämtade sidor [REPO ads/references/audit-guardrails.md rad 77]
- Kostnad: inget kopieras, ingen skill tas in. Tre rader, cirka 120 tokens, i humanizerns förord, som laddas bara i
  steg 4. Hade copywriting tagits in som skill: 239 tokens alltid, 2 477 vid användning, 11 740 vid behov enligt
  förgranskningen. Inga beroenden, inget underhåll
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ett ställe med text till agenter (vakten ovan), inga
  behörigheter i frontmatter, inga hookar. 69 skript: 60-talet CLI:er i `tools/clis/` som läser API-nycklar ur
  miljön och anropar marknadsföringstjänster (Resend, Mailchimp, Google Ads, Meta Ads …), `check-versions.mjs` kör
  `git` via `execFileSync` (förgranskningens eval/exec) och `sync-skills.js` skriver om README och marketplace.json.
  Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: `.claude/skills/humanizer/SKILL.md`, avsnittet "Så används skillen i nortropic-webb-pro" (rad 10–20),
  tre punkter efter rad 18, med egna ord: (1) tak, inte förbud, för mönster 10, 14 och 31: högst ett fragment och
  högst en lista på tre per sektion, högst ett tankstreck per stycke i löptext; (2) kort text är strängare: i h1,
  h2, ingress, knappar, title och description inga tankstreck, ingen "inte X utan Y", ingen fråga som besvaras i
  nästa mening; (3) variera rättningarna: skriv om ur sakuppgiften i underlaget, aldrig med synonym, och blir samma
  konstruktion rättning två gånger på en sida är den ett nytt mönster. `KALLA.md` får en rad om källan och
  commiten. Ingen ny mekanik i `copy_kontroll.py`
- Utfall: tre regler i humanizerns förord 2026-10-03 (tak per sektion, strängare kort text, skriv om ur
  sakuppgiften); KALLA.md nämner ai-tells @ 13c3832.
- Backlog: B-20261002-tre-regler-ur-ai-tells-i-humanizerns-forord-tak

### 2026-10-02 · gohugoio/hugo · nej
- Källa: https://github.com/gohugoio/hugo @ 6b3ba3a (ur klonens packed-refs; senaste push 2026-10-01T17:33Z),
  Apache-2.0; cirka 90 000 stjärnor, inte arkiverat. Nämnd en gång förut som post i awesome-go-listan
  (`kunskap/REGISTER.md:838`), aldrig bedömd i sig. Förgranskad. Läst: README i helhet, AGENTS.md, CLAUDE.md,
  docs/AGENTS.md, raderna med dolda tecken i `docs/data/homepagetweets.toml`, dokumentationens `about/features.md`,
  `content-management/image-processing/index.md`, `methods/resource/Meta.md` och `Exif.md`, `templates/embedded.md`,
  och temaskelettet `create/skeletons/theme/` (baseof, head, home, main.css). Av 1 352 textfiler och cirka 544 000
  tokens är det ett urval; Go-koden lästes inte. Sett: gohugo.io i mobil och desktop, första vyn och skrollbild 3 av 8
  [BILD gohugo-io/mobil-forsta.png, desktop-forsta.png, desktop-skroll-03.png]; temagalleriet themes.gohugo.io i mobil
  och desktop, första vyn och skrollbild 2 av 8 [BILD hugo-themes/mobil-forsta.png, desktop-forsta.png,
  desktop-skroll-02.png]. Repots egna bilder är hostingskärmdumpar och logotyper. Ägarens not: ingen
- Steg: 5 (bygge: generatorn och mallen); 1 (bildernas metadata) för den egna innovationen
- Jämfört med i dag: (1) **Generatorn.** Hugo är en statisk sajtgenerator i Go, optimerad för byggtid, med
  Go-templates, taxonomier, flerspråk och egna pipelines för CSS, bilder, JS, Sass och Tailwind [REPO README.md rad
  45–64; docs about/features.md rad 81–96]. Vi bygger statiskt i Astro: mallen har `astro` och `sharp` som enda
  beroenden (`mall/astro/package.json:10–13`), `ny_sajt.py` skapar varje bygge ur den (`bygg-sajt/SKILL.md:213–215`),
  och byggstandardens avsnitt 11 binder stacken till Astro (`kunskap/byggstandard.md:133–138`); den teoretiska
  grunden säger att statisk förrendering är en tillämpning av principerna, inte en egen princip, och att
  leverantörsdokumentationen för oss är Astro och Vercel (`kunskap/teoretisk-grund.md:119–120`). Sak mot sak för en
  sajt på fem till sju sidor: båda ger förrenderad HTML utan klient-JS (standarden 1.1, rad 25). Hugos byggtid i
  millisekunder [REPO docs/data/homepagetweets.toml rad 11, 53] löser ett problem vi inte har; vår byggtid är
  försumbar mot granskningens 4–15 minuter (`bygg-sajt/SKILL.md:257`). Hugos bildpipeline (konvertera, skala,
  beskära, cache) [REPO docs image-processing/index.md rad 8, 106–116] gör det `astro:assets` redan gör (standarden
  4.2, `kunskap/byggstandard.md:59, 135`). Att byta generator vore samma sajt med ny verktygskedja: `mall/`,
  `ny_sajt.py`, provet och kontrollerna omskrivna, och ingen dom i `LARDOMAR.md` pekar på en brist som generatorn
  orsakar. Lika i resultat, sämre i kostnad. (2) **Temaskelettet och galleriet.** `hugo new theme` ger landmärkena
  header, main och footer [REPO create/skeletons/theme/layouts/baseof.html rad 7–15] men ett head utan description,
  canonical, theme-color eller ikoner [head.html rad 1–5] och CSS med sans-serif, #222 och blå länkar
  [assets/css/main.css rad 4–15]; vår mall bär canonical, theme-color, favicon, delningsbild, skiplänk, CSP, dämpad
  rörelse, sitemap, robots, 404, förfrågan och brödsmulor (`mall/astro/README.md:3–5`). Galleriet är 237 bloggteman,
  182 "minimal", 30 "company" och 11 "contact" [BILD hugo-themes/desktop-forsta.png]; sidorna som visas är
  porträtt-i-mitten-mallar och dokumentationssajter [BILD hugo-themes/mobil-forsta.png, desktop-skroll-02.png].
  Ägaren dömde våra byggen 4–5 på "gjord för verksamheten" och pekade på generiska mönster som mall-lukt
  (`LARDOMAR.md:29, 54, 78`); steg 5 härleder riktningen ur verksamheten, "aldrig ur en branschmall"
  (`bygg-sajt/SKILL.md:200–201`). Sämre. (3) **Inbyggda mallar.** Open Graph, X-kort, schema som mikrodata, Disqus
  och Google Analytics [REPO docs templates/embedded.md rad 10–101, 103–110, 206–213]. Vår standard kräver og:image
  per sida och JSON-LD med den mest specifika typen ur VERKSAMHET.json (`kunskap/byggstandard.md:97, 99`), inga
  tredjepartsresurser (4.4, rad 61) och helst kakfri analys (8.5, rad 112); Hugos schema är generiska mikrodata med
  datum och ordantal, inte LocalBusiness. Lika eller sämre. (4) **Bildmetadata.** Hugos `Meta` läser skapandedatum,
  GPS och orientering ur EXIF, IPTC och XMP som rutin [REPO docs methods/resource/Meta.md rad 16–18, 41–51]. Ägaren
  räknade i L1 byggdagboken "med datum ur bilderna" som det bästa på sajten (`LARDOMAR.md:31`), men steg 1 ber bara
  om fil, källa, vad bilden visar och kvalitet (`bygg-sajt/SKILL.md:75–77`); byggena löste det var för sig: EXIF i
  ett, filnamn i ett, "datum okänt" i ett (`underlag/*/bilder/BILDER.md`). Smartare som rutin; inget skäl att ta in
  Hugo, men ett förslag till steg 1 (egen innovation, backlog)
- Skäl: källan är en sajtgenerator, inte en metod, regel eller skill för bättre sajter, och vi har redan en generator
  som gör samma arbete med färre beroenden för våra sajter. Byggstandarden binder stacken till Astro, ett medvetet val
  som tre dömda byggen hållit med 0 kB JS (`LARDOMAR.md:31, 56, 87`), och litteraturen avgör inte mellan två statiska
  generatorer (`kunskap/teoretisk-grund.md:119`). Det Hugo har mer av, byggtid, flerspråk, taxonomier,
  innehållsadaptrar, löser problem en hantverkarsajt inte har, och temagalleriet drar åt det ägaren kallat mall.
  Källkritik: README:n och startsidan säljer "världens snabbaste" med byggtider ur citat från 2013–2019 [REPO
  docs/data/homepagetweets.toml] och stjärnräkning [BILD gohugo-io/desktop-skroll-03.png]; inget belagt mot något vi
  mäter. Källan innehåller instruktioner till agenter: AGENTS.md och CLAUDE.md är kodregler för bidragsgivare i Go
  (korthet, tester, `check.sh`) [REPO AGENTS.md rad 2–19], docs/AGENTS.md ger en Tailwind-roll för
  dokumentationssajten [REPO docs/AGENTS.md rad 4–9]; inget riktade sig till kirurgen och inget följdes. De fem
  dolda tecknen är U+200F sist i tre namn i citatdatan [REPO docs/data/homepagetweets.toml rad 9, 72, 79], troligen
  klistrade ur X, utan instruktion
- Kostnad: inget tas in. Som generator vore det en Go-binär (Go 1.27 för bygge ur källa [REPO README.md rad 107]),
  ett nytt mallspråk och omskrivning av `mall/`, `ny_sajt.py`, provet och kontrollerna; deploy-utgåvan drar in AWS-,
  Azure- och GCP-SDK:er [REPO README.md rad 192–365]. Källans text är cirka 544 000 tokens enligt förgranskningen.
  Förslaget i backloggen är en kolumn i steg 1 och en mening i `kunskap/bild.md`
- Säkerhet: förgranskningen HÖG på grund av fem dolda tecken (U+200F i `docs/data/homepagetweets.toml`, se ovan) och
  tolv ställen med text till agenter, alla "run the following command" i installations- och bidragsdokumentation;
  inga skills, hookar eller behörigheter. 35 skript: livereload (nätanrop, eval), dokumentationens sökning (nätanrop),
  KaTeX-bundlen (eval) och byggskript för wasm, väntat för en generator med utvecklingsserver. Inget kördes eller
  installerades
- Förslag: inget för Hugo. Egen innovation: fotodatum med källa per bild i steg 1 (se backlog)
- Utfall: kontroller/bilddatum.py 2026-10-03 (EXIF DateTimeOriginal, telefonens filnamn, GPS-notering) och
  datumkolumn i BILDER.md; standarden 4.2 fäller publicerade bilder med GPS-läge.
- Backlog: B-20261002-bilder-md-anger-nar-varje-egen-bild-togs-ur-exif (egen innovation)

### 2026-10-02 · unclecode/crawl4ai · nej
- Källa: https://github.com/unclecode/crawl4ai @ e5d2e78 (ur klonens `.git/shallow`; senaste push 2026-09-25T06:37Z),
  Apache-2.0, men README:n kräver därutöver en attributionsbadge eller textrad [REPO README.md rad 376–377]; version
  0.9.4 (23 sep 2026), cirka 84 600 stjärnor, inte arkiverat; 836 textfiler, cirka 1 020 000 tokens text. Inte bedömd
  förut. Förgranskat. Läst: README i helhet, `README-first.md` (den äldre README:n), `MISSION.md`, `pyproject.toml`,
  `SECURITY.md` rad 140–169, `.claude/commands/c4ai-check.md` och `.claude/settings.local.json`; i dokumentationen
  `advanced/lazy-loading.md`, `core/link-media.md`, `core/fit-markdown.md` i helhet och `core/url-seeding.md` rad
  1–120; i koden `js_snippet/remove_consent_popups.js` rad 1–319, `js_snippet/update_image_dimensions.js`,
  `content_scraping_strategy.py` rad 410–480, standardvärdena för robots och stealth i `async_configs.py`, och
  `deploy/docker/job.py` rad 1–80. Bild: missionsdiagrammet [BILD docs/assets/pitch-dark.png]. Ingen demosajt;
  README:ns banner länkar till molntjänsten. Ägarens not: ingen
- Steg: 1 (hämta det publika, bilderna) och 2 (diagnos); inget annat
- Jämfört med i dag: Crawl4ai hämtar sidor i en Playwright-webbläsare och ger markdown, "fit markdown" som rensar
  menyer och sidfötter med textdensitet eller BM25 [REPO docs/md_v2/core/fit-markdown.md rad 37–38], djupkrypning
  BFS/DFS/best-first, adressupptäckt ur sidkarta och Common Crawl, LLM-extraktion via en egen litellm-fork,
  stealth-läge och "undetected browser", proxyer, en Docker-server med REST och MCP, och ett betalt moln [REPO
  README.md rad 24, 72–77, 106–175]. Hos oss gör `kontroller/hamta_sajt.py` (byggt 2026-10-02 ur Firecrawl-posten
  ovan) steg 1: bara GET, samma domän, högst 40 sidor, robots.txt enligt RFC 9309 (`hamta_sajt.py:4–9`), adresser ur
  sidkarta och interna länkar (`:221–256, 356–365`), bilder inklusive data-src, srcset, picture, CSS-bakgrunder och
  og:image (`:139–153, 339–350`), JSON-LD och kontaktvägar, och det körde sundbomsel.se till 40 sidor med alla 15
  handlistade (posten om Firecrawl, raden Utfall). Diagnosen i steg 2 mäter med axe, Lighthouse och inspektionen i
  390 och 1440 px (`.claude/skills/bygg-sajt/SKILL.md:99–101`); crawl4ai har inget av det. Sak mot sak: (1)
  **webbläsare mot GET.** Crawl4ai ser text och bilder som bara finns efter JavaScript eller skroll [REPO
  docs/md_v2/advanced/lazy-loading.md rad 3–7]; vårt verktyg läser HTML:en som servern skickar. Våra kunders sajter
  är WordPress med Divi eller Elementor (`underlag/sundboms-el/RESEARCH.md:107`, `underlag/lulea-snickaren-abx/RESEARCH.md:6–7`,
  `underlag/paint-it-black-maleri/RESEARCH.md:20`), som renderas på servern, och ingen av ägarens tre domar saknar
  något ur underlaget (`LARDOMAR.md` L1–L3). Behövs en webbläsare har kirurgen `kontroller/sida.mjs` och bygget
  `inspektera.mjs`. Lika för våra sajter. (2) **robots och artighet.** Crawl4ai läser robots.txt bara om man ber om
  det, standard av [REPO crawl4ai/async_configs.py rad 1681, 1808], och erbjuder stealth [rad 941]; vårt verktyg
  respekterar robots alltid och väntar mellan anropen. Vårt är bättre för det vi gör: vi läser en blivande kunds
  sajt, inte en motståndares. (3) **Kakrutor.** Crawl4ais skript klickar "acceptera alla" i ett långt register av
  kända samtyckesverktyg, med textfallback och CMP-API:er [REPO crawl4ai/js_snippet/remove_consent_popups.js rad 10–11,
  14–165, 198–230, 304–318]; vår `sida.mjs` väljer "neka" före "acceptera" (`kontroller/sida.mjs:4, 33`). Vårt är
  rätt för oss: ingen ska samtycka till spårning i någon annans namn. Listan över selektorer är dock bredare än vårt
  textmönster. (4) **Bilder.** Crawl4ai sållar bort ikoner, logotyper och knappbilder på förälderns class och adressen
  och poängsätter resten på width/height över 150, alt, srcset och picture innan de räknas [REPO
  crawl4ai/content_scraping_strategy.py rad 428–466]; vår SIDOR.md listar alla bildadresser platt och ber bygget
  sortera själv (`hamta_sajt.py:390–395`). Smartare hos källan, och den enda metoden värd att låna (egen innovation,
  backlog). Mot litteraturen: steg 1 är innehållsinventeringen (Halvorson & Rach 2012,
  `kunskap/teoretisk-grund.md:29–31`); båda gör den, och för tio till fyrtio serverrenderade sidor gör vårt
  430-raders verktyg utan beroenden samma inventering
- Skäl: Crawl4ai är byggt för RAG, agenter och datapipelines i stor skala [REPO README.md rad 24] och löser, som
  Firecrawl (dömd nej, ägaren höll med, `kunskap/KIRURG-OMDOMEN.md:80–83`) och browser-use (nej, `:155–158`), problem
  vi inte har: robotväggar, proxyer, tusentals adresser, LLM-extraktion ur sidor. Att ta in det är 34
  körtidsberoenden, däribland en litellm-fork, patchright, playwright-stealth, numpy, nltk och shapely [REPO
  pyproject.toml rad 15–50], ett installationsskript för webbläsaren och en Docker-server som i juni 2026 hade
  förautentiserad fjärrkörning, hårdkodad JWT-hemlighet och SSRF som kritiska fynd [REPO SECURITY.md rad 162–168].
  Det krockar med två medvetna val: kod ur källor körs inte, och vi hämtar som en artig besökare (robots alltid,
  inga stealth-lägen, "neka" före "acceptera"). Det vi saknar i sajtkvalitet, enligt ägarens domar, är bilder,
  telefontid och formulär från verksamheten (`LARDOMAR.md:63, 87`), inte fler hämtade sidor. Källkritik: README:n
  säljer molnet i banner, badge och en rad som ber agenten lägga till deras MCP-server i Claude Code [REPO README.md
  rad 15–20, 51–68]; `MISSION.md` handlar om "data capitalization" och en datamarknad [REPO MISSION.md rad 5–33],
  långt från en hantverkares sajt. Källan innehåller text till agenter: `.claude/commands/c4ai-check.md` är ett
  testflöde för bidragsgivare (skriv provfall, kör pytest, radera filen) [REPO .claude/commands/c4ai-check.md rad
  9–89], "You are an AI" i `llms-full.txt` är promptexempel i dokumentationen; inget riktade sig till kirurgen och
  inget följdes. Två av de tre dolda tecknen är nollbreddsmellanslag mitt i ordet "LLM" i en docstring och en
  kommentar [REPO deploy/docker/job.py rad 2, 67], utan instruktion men utan rimligt skäl; det tredje är en
  emojisammanfogare i sponsorrubriken [REPO README.md rad 494]
- Kostnad: inget tas in. Som verktyg vore det 34 beroenden, en webbläsarinstallation och ett setup-skript, eller en
  Docker-tjänst att hålla patchad; källans text är cirka 1 020 000 tokens enligt förgranskningen. Förslaget i
  backloggen är en kolumn i `hamta_sajt.py` och två rader i steg 1
- Säkerhet: förgranskningen HÖG: tre dolda tecken (se ovan), 22 ställen med text till agenter (promptexempel i
  `llms-full.txt` och `extraction-*.txt`, "run the following command" i installationsdokumentation, "exfiltrat" i
  säkerhetsnoter, "Execute this" i webbläsartilläggets kodgenerator), och 547 skript med nätanrop, eval och
  miljövariabler, väntat för en crawler med LLM-anrop och server. `.claude/settings.local.json` ger breda
  Bash-tillstånd (rm, curl, chmod, docker) för författarens egen maskin [REPO .claude/settings.local.json rad 4–24];
  inga hookar, inga MCP-servrar, ingen SKILL.md. Inget kördes eller installerades
- Förslag: inget för crawl4ai. Egen innovation: SIDOR.md sorterar bildlistan med källans billiga regler, foton först
  (se backlog)
- Utfall: SIDOR.md sorterar bildlistan efter trolig typ 2026-10-03 (foto, okänd, logga/ikon); luleasnickaren.se 16
  foto, 1 okänd, 6 logga/ikon.
- Backlog: B-20261002-sidor-md-sorterar-bildlistan-troliga-foton-forst (egen innovation)

### 2026-10-02 · sdmg15/Best-websites-a-programmer-should-visit · nej
- Källa: https://github.com/sdmg15/Best-websites-a-programmer-should-visit @ 3f13b07 (ur klonens `.git/logs/HEAD`;
  senaste push 2025-09-16), MIT, cirka 76 000 stjärnor, **arkiverat** enligt `gh repo view`. Repot är en README på
  979 rader med 33 avdelningar länkar, plus bidragsregler, uppförandekod, ett `package.json` som bara kör
  awesome-lint, en Travis-fil och en vitlista på 30 domäner för länkkontrollen. Läst: hela README:n, alla övriga
  textfiler och förgranskningen. Repot har inga egna bilder (bara awesome-loggan från ett annat repo [REPO README.md
  rad 3]) och ingen demo.
- Steg: inget av de åtta; närmast steg 3 (referensjakten) och steg 5 (riktning, färg, ikoner).
- Jämfört med i dag: källan är en allmän länklista för programmerare: nyheter, intervjuträning, jobb, kurser,
  tävlingsprogrammering, poddar, kryptovaluta, "när du blir uttråkad" [REPO README.md rad 16–52]. Samma sorts källa
  som vinta/awesome-python, avelino/awesome-go och the-book-of-secret-knowledge, alla dömda nej med ägarens
  medhåll (`kunskap/KIRURG-OMDOMEN.md:15–18, 45–48, 85–88`). De webbnära posterna prövades sak mot sak. (1)
  Palettgeneratorer Coolors och Branition Colors [REPO README.md rad 489, 500]: hos oss härleds färgen ur
  verksamheten själv, "aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md:200–201`), "aldrig kopiering av
  layout, palett eller typsnitt" (`kunskap/referenser-professionella.md:61`), och ägaren valde gult och svart ur
  Sundboms ordmärke före en färdig palett (`LARDOMAR.md:89`). Sämre. (2) Figma-mallar, Tailwind-sidbyggare,
  Open Source Web Design-mallar och UI Design Daily [REPO README.md rad 249, 501, 503, 913]: mallformen var det
  ägaren luktade sig till i L1–L3 (`SKILL.md:204`), och våra referenser är verkliga verksamhetssajter valda för
  kundens uppgift i tre roller (`kunskap/referensjakt.md:13–21`), där ens prisgallerier bara är sökingångar
  (`:25–27`). Sämre. (3) Iconscout och LottieFiles [REPO README.md rad 502, 504] är marknadsplatser; vår regel är
  ikoner som SVG, aldrig ikonfont (`kunskap/byggstandard.md:51`), inga tredjepartsresurser (`:61`), och
  ikonuppsättningar registreras med licens i `bilder/TYPSNITT-IKONER.json` (`kunskap/bild.md:70–81`). Lika i sak,
  men listan tillför ingen regel. (4) Can I use och MDN [REPO README.md rad 494, 715]: primärkällor vi redan läser
  (`kunskap/prelaunch.md:39`, `kunskap/byggstandard.md:152` mot web.dev). Lika. (5) CSS-Tricks, ShopTalk Show,
  Flexbox Froggy, en promptguide [REPO README.md rad 610, 657, 674, 837] är läsning och övning, ingen metod.
  Mot litteraturen: steget Designa går från innehåll och informationsarkitektur till form (`kunskap/teoretisk-grund.md:34–35`);
  listan erbjuder ingen metod, ingen utvärderingsteknik och ingen princip, bara adresser.
- Skäl: listan svarar på "vilka sajter bör en programmerare känna till", en fråga inget av våra steg ställer; det
  som ägarens domar pekar på (förfrågan, bildunderlag, telefontid, förtroendekvitton, `LARDOMAR.md:47, 71, 95`)
  finns inte i den. De få webbnära posterna krockar med medvetna val (färg och form ur verksamheten, inga mallar) eller
  är källor vi redan använder. Källan är dessutom arkiverad och åldrad: ingen push sedan 2025-09, Google Codes
  projekthosting listas som levande [REPO README.md rad 907], ett Mozilla-program från 2016 [rad 914] och en
  MITRE-lista från 2022 [rad 190]; bidragsreglerna tillåter en länk per PR och inga nya avdelningar [REPO
  CONTRIBUTING.md rad 7, 16]. Källkritik: README:n ber om stjärnor [REPO README.md rad 977]; beskrivningarna är
  sajternas egna slogans, inte observerad kvalitet. Det enda som är smartare än vårt är arbetssättet runt listan:
  en CI-körning som kontrollerar varje länk och vitlistar de domäner som stoppar roboten [REPO .travis.yml rad
  15–16; white_listed_sites.txt]. Vårt prov följer bara interna adresser (`kontroller/standard_kontroll.py:118`)
  fast punkt 7.4 kräver länk till omdömena (`kunskap/byggstandard.md:100`) och ägaren i A/B-domen inte kunde se
  vilken plattform omdömena låg på (`LARDOMAR.md:102`). Det blir en egen innovationspost, inte ett intag.
- Kostnad: inget tas in. Källans text är cirka 25 700 tokens enligt förgranskningen. Innovationsposten är en
  info-rad i `standard_kontroll.py` och en tabell i rapporten; nätanrop i provet, avstängda i rökprovet.
- Säkerhet: förgranskningen HÖG på grund av tre dolda tecken; alla tre är nollbreddsfogar (U+200D) inuti sammansatta
  emojis i avdelningsrubriker [REPO README.md rad 408, 645, 879], läst i sitt sammanhang, ingen instruktion. Ingen
  text till agenter, inga skript med nätanrop, inga hookar, ingen SKILL.md. `.travis.yml` klonar nvm och installerar
  gem och npm-paket i CI [REPO .travis.yml rad 9–13]; inget kördes eller installerades.
- Förslag: inget för källan. Egen innovation: provet listar sajtens utgående länkar och om de svarar, med vitlista
  (se backlog).
- Utfall: provet listar utgående länkar och deras svar 2026-10-03 (standard.md, STATUS.json, rapportens punkt 14).
- Backlog: B-20261002-provet-listar-sajtens-utgaende-lankar-och-om-de (egen innovation)

### 2026-10-02 · withastro/astro · prova
- Källa: https://github.com/withastro/astro @ 4c1470a (ur klonens `.git/packed-refs`; senaste push 2026-10-02T15:20Z),
  MIT, med MIT-delar ur sveltejs/kit och vitejs/vite [REPO LICENSE rad 1–3, 23–36]; cirka 63 000 stjärnor, inte
  arkiverat. Monorepo med 4 485 textfiler, cirka 980 000 tokens. Det här är vår egen stack: mallen kör astro 7.3.5
  (`mall/astro/package.json:11`) och repots paket är 7.3.5 [REPO packages/astro/package.json rad 3]; nämnt som vår
  stack i ett tjugotal registerposter, aldrig bedömt i sig. Förgranskat. Läst: README i helhet, LICENSE,
  `.agents/skills/astro-developer/SKILL.md` och `constraints.md`, `.agents/skills/astro-code-review/SKILL.md` rad 1–60,
  `.agents/evals/README.md`; typsnitts-API:t i `packages/astro/src/types/public/config.ts` rad 3019–3243,
  `assets/fonts/providers/local.ts`, `assets/fonts/core/optimize-fallbacks.ts`,
  `assets/fonts/infra/capsize-font-metrics-resolver.ts`, `assets/fonts/vite-plugin-fonts.ts` rad 188–210 och
  `components/Font.astro`; dev-toolbarens granskningsregler `audit/rules/perf.ts` i helhet och rubrikerna i
  `a11y.ts`; CSP-koden `core/csp/common.ts` rad 54–104; och de dolda tecknens rader. Ett urval: kompilatorn,
  integrationerna, exemplens kod och testerna lästes inte. Bild: README-bannern är en logotypbild, "Build the web
  you want" på rosa-lila ringar [BILD .github/assets/banner.jpg], ingen designreferens. Ingen demosajt i repot;
  docs.astro.build och astro.new länkas [REPO README.md rad 33–39] men öppnades inte. Ägarens not: ingen
- Steg: 5 (bygge: mallen och typsnitten) och 6 (provet, punkt 4.3)
- Jämfört med i dag: (1) **Ramverket.** Lika per definition: byggstandardens avsnitt 11 binder stacken till Astro
  (`kunskap/byggstandard.md:133–138`), `ny_sajt.py` skapar varje bygge ur mallen (`bygg-sajt/SKILL.md:213–215`), och
  den teoretiska grunden kallar Astros dokumentation vår leverantörsdokumentation (`kunskap/teoretisk-grund.md:119–120`).
  Samma version i mallen som i repot; inget att byta. (2) **Typsnitten.** I dag skriver bygget allt för hand:
  byggstandarden 4.3 kräver självhostad WOFF2, `font-display: swap` med size-adjust-reserv och preload av typsnittet i
  första vyn (`kunskap/byggstandard.md:60`), filen ska ligga i `public/fonts/` (`:136`, `mall/astro/README.md:15`),
  och typsnittet installeras från fontsource med npm och kopieras (`bygg-sajt/SKILL.md:38–42`). Utfallet i de fem
  byggena: tre saknar reserven helt, enda träffen på "size-adjust" är `-webkit-text-size-adjust`
  (`kunder/lulea-snickaren/sajt/src/styles/global.css:31`, `kunder/sundboms-el/sajt/src/styles/global.css:29`,
  `kunder/paint-it-black-maleri/sajt/src/styles/sajt.css:30`); A/B-paret har reserven med handgissade mått,
  "ungefär samma bredd och höjd": 103 %, 96 %, 32 %, 0 % (`kunder/lulea-snickaren-abx/sajt/src/styles/sajt.css:13–20`)
  och 102 %, 96 %, 26 % (`kunder/lulea-snickaren-aby/sajt/src/layouts/Sida.astro:107–113`). Provet hoppar över
  `local()`-block utan att kräva dem (`kontroller/standard_kontroll.py:378–379`), och saknad preload är bara info
  (`:255–257`). Källan har sedan 6.0 ett stabilt `fonts`-fält i konfigurationen [REPO config.ts rad 3019–3035]:
  den lokala leverantören läser vikt och stil ur filen när de inte anges [REPO providers/local.ts rad 107–146];
  `optimizeFallbacks` skriver ett reserv-`@font-face` per systemtypsnitt bakom den generiska familjen [REPO
  core/optimize-fallbacks.ts rad 25–107] med size-adjust, ascent-, descent- och line-gap-override räknade ur
  typsnittets xWidthAvg, ascent, descent, lineGap och unitsPerEm [REPO capsize-font-metrics-resolver.ts rad 71–106];
  `<Font cssVariable preload />` skriver `<style>` och preload-länkarna [REPO components/Font.astro rad 25–28];
  display är swap som standard [REPO config.ts rad 3200–3212]; när `security.csp` är på hashas den genererade
  stilen och font-src fylls i automatiskt [REPO vite-plugin-fonts.ts rad 197–207; core/csp/common.ts rad 54–84].
  Källan avråder från `public/` för lokala filer, eftersom de då dubbleras i bygget [REPO providers/local.ts rad
  31–32], vilket krockar med vår text på de två ställena ovan. Bättre: måtten kommer ur filen i stället för en
  gissning, och reserven kommer alltid. Smartare: fyra handgrepp (font-face, reserv, preload, CSP-hash) blir en
  konfigurationspost och en rad. Inte verifierat utan ett bygge: att provets 4.3-räkning hittar den hashade filen i
  `dist/_astro` (rglob över dist, `standard_kontroll.py:367`, så det borde) och att CSP:n i vår form med metatagg
  och stilattribut får hashen rätt. Mot litteraturen: CLS ≤ 0,1 (byggstandarden 4.1, `kunskap/teoretisk-grund.md`
  avsnitt 4); en reserv med rätt mått är metoden mot layoutskift vid typsnittsbyte, och källan länkar Chrome-teamets
  text om det [REPO config.ts rad 3104]. (3) **Dev-toolbarens granskning.** Regler för tillgänglighet (tomt href,
  label utan kontroll, redundanta ARIA-roller, positivt tabindex) och prestanda (Image-komponenten, lazy under
  vecket och eager över, GIF som video) [REPO audit/rules/a11y.ts rad 267–686; perf.ts rad 7–103] körs bara i `astro
  dev` i webbläsaren. Vi mäter den byggda sajten med axe (5.6) och standardens 2.4 (lazy under första vyn,
  fetchpriority). Lika eller täckt. (4) **`.agents/skills/`.** Tio skills för att utveckla Astro-monorepot: triage,
  changeset, merge, PR-text, granskning av Astro-PR [REPO .agents/skills/astro-developer/SKILL.md rad 3, 8;
  astro-code-review/SKILL.md rad 3]. Ingen handlar om att bygga sajter med Astro; inget för verktygslådan. Deras
  skill-evals med manifest per skill, en subjektmodell och en domarmodell i en tillfällig arbetsyta [REPO
  .agents/evals/README.md rad 3, 20–22] liknar vårt A/B-upplägg med annan domare; inget nytt. (5) i18n, env-schema,
  incrementalBuild, svgOptimizer [REPO config.ts rad 2901–3017, 3485–3594]: problem vi inte har
- Skäl: Astro är vår stack, så frågan är inte om, utan vilka delar av ramverket vi lämnar oanvända. En: det inbyggda
  typsnitts-API:t gör exakt det byggstandardens 4.3 kräver och som byggena missar eller gissar, med mått ur
  typsnittsfilen och CSP-hash på köpet, utan nya beroenden. Det syns först i ett bygge om provet och CSP:n håller,
  så prova, inte ta in; ingen blind parjämförelse behövs, provet och mätningen avgör (ägarens kalibrering för
  agency-agents, `kunskap/KIRURG-OMDOMEN.md:125–127`). Resten av repot är leverantörsdokumentation vi redan följer,
  verktyg för Astros egna utvecklare, eller funktioner för större sajter. Källkritik: README:n ber om stjärnor i
  beskrivningen och visar sponsorer [REPO README.md rad 93–103]; påståendena om API:t är kontrollerade i koden, inte
  i marknadsföringen
- Kostnad: inga nya beroenden; API:t ligger i astro 7.3.5 som mallen redan har, och capsize och unifont är Astros
  egna beroenden. Vid användning: en konfigurationspost och en rad i layouten per bygge, och bygget slipper skriva
  font-face, reserv och preload. Underhåll: följer Astros version. Källans text är cirka 980 000 tokens enligt
  förgranskningen; inget av den tas in
- Säkerhet: förgranskningen HÖG: 16 dolda tecken, alla U+200D, emojisammanfogare i astronautemojin i exemplens
  README-rad "Seasoned astronaut?" [REPO examples/basics/README.md rad 15 med flera], i emojilistan i
  `.github/workflows/congrats.yml` rad 16, i VS Code-tilläggets README och i tre testfiler som prövar just sådana
  tecken; ingen instruktion. 12 ställen "run the following command" i CONTRIBUTING, upgrade-paketet och
  CLI-källkoden är användarmeddelanden, inte riktade till kirurgen. 2 804 skript är väntat för ett ramverk;
  `.gitpod/gitpod-setup.sh` har nätanrop; inga hookar, MCP-servrar eller behörigheter i skill-frontmatter.
  `.agents/evals` kräver en Anthropic-nyckel i miljön [REPO .agents/evals/README.md rad 5]. Inget kördes eller
  installerades
- Förslag: mallen: `fonts` med `fontProviders.local()` i `mall/astro/astro.config.mjs` och `<Font cssVariable preload />`
  i `Bas.astro`; texten: `mall/astro/README.md` rad 15, `kunskap/byggstandard.md` rad 136 och
  `.claude/skills/bygg-sajt/SKILL.md` rad 38–42 flyttar filen till `src/assets/fonts/` och låter API:t skriva reserv
  och preload. Prövas i nästa bygge mot provet, CSP-konsolen och Lighthouse-CLS (se backlog). Egen innovation: provet
  stoppar när ett självhostat typsnitt saknar reserv med size-adjust (se backlog)
- Utfall: standarden 4.3 kräver reservtypsnitt med size-adjust i stacken, och mallen använder Astros typsnitts-API
  2026-10-03 (provbygge grönt, CSP 0, CLS 0, reserv 104,5 % ur filen).
- Backlog: B-20261002-prova-astros-inbyggda-typsnitts-api-fonts-i-astr (prova),
  B-20261002-provet-stoppar-nar-ett-sjalvhostat-typsnitt-sakn (egen innovation)

### 2026-10-02 · DavidHDev/react-bits · nej
- Källa: https://github.com/DavidHDev/react-bits @ e1bbb69 (ur klonens `.git/logs/HEAD`, klonad 2026-10-02; senaste push
  2026-09-30T11:19Z), MIT + Commons Clause (får användas i en sajt, komponenterna får inte säljas eller spridas vidare
  [REPO LICENSE.md rad 8, 15]); cirka 48 400 stjärnor, inte arkiverat; cirka 27 500 tokens text i 1 600 textfiler.
  Inte bedömd förut. Förgranskat. Läst: README i helhet, `LICENSE.md`, `package.json`, `src/constants/Pro.js` rad
  1–140, `src/constants/Showcase.js`, `scripts/generateLlmsText.js` rad 1–80, komponenterna `BlurText.jsx` i helhet,
  `Aurora.jsx` rad 1–60 och `CallChip.jsx` i helhet, och de två ställena för `prefers-reduced-motion` i
  `WarpText.jsx`. Övriga komponenter (fem kategorier: text, animationer, komponenter, mikro, bakgrunder) bara som
  fillista. Sett: `gh-showcase.png`, `tools-readme.webp`, två av arton Pro-förhandsbilder (`skill-corporate-trust.webp`,
  `prompt-agency.webp`), och demosajten reactbits.dev öppnad i dag i 390 och 1440: mobilens och desktops första vy
  och skrollägena 3, 5 och 7 av åtta. Ägarens not: ingen
- Steg: 5 (bygge: rörelse, bakgrunder och textanimationer i sidan); inget annat
- Jämfört med i dag: react-bits är cirka 210 React-komponenter som kopieras in som källkod via ett CLI, i fyra
  varianter (JS/TS, CSS/Tailwind) [REPO README.md rad 13, 42, 63–67; BILD reactbits-dev/mobil-forsta.png]. De bygger
  på React plus motion, GSAP, ogl, three och matter-js [REPO package.json rad 25, 28–31, 39, 46, 49, 62]: BlurText
  animerar varje ord med motion [REPO BlurText.jsx rad 3, 87–97], Aurora ritar en bakgrund i WebGL-shaders via ogl
  [REPO Aurora.jsx rad 3, 8–15]. Hos oss: mallen har astro och sharp som enda beroenden
  (`mall/astro/package.json` rad 10–13), innehåll och navigation ska fungera utan JS (`kunskap/byggstandard.md:18`),
  bygget skriver "ingen JavaScript som inte behövs" (`.claude/skills/bygg-sajt/SKILL.md:217`), och litteraturen bakom
  är HTML före JS och minimal klient-JS (`kunskap/teoretisk-grund.md:47–48`, 119). De tre dömda byggena hade 0 kB JS
  (`LARDOMAR.md` rad 31, 56, 87). Astro stöds via React-öar [BILD reactbits-dev/desktop-skroll-05.png "Works with Vite,
  Next.js, Astro and Remix"], så det går tekniskt, men varje använd komponent drar in React och ett
  animationsbibliotek på sidan. Det enda som är bättre än vårt: 104 av komponentfilerna tar hänsyn till
  `prefers-reduced-motion` i koden, till exempel att shadern stannar [REPO WarpText.jsx rad 305, 441–444]; vår mall
  gör samma sak globalt i CSS (`mall/astro/src/layouts/Bas.astro` rad 47–51, standarden 3.5). Lika på den punkten,
  sämre i övrigt, och krockar med ett medvetet val
- Skäl: Källan är ett bibliotek för att få en sajt att "stand out" med rörliga bakgrunder, glänsande text, kuber,
  partiklar och markörer [REPO README.md rad 11, 33; BILD reactbits-dev/desktop-skroll-03.png: ShapeGrid,
  MagicRings, ShinyText, Dock], och dess egen sajt är det mörklila SaaS-uttrycket med Geist, 66 px rubrik och
  "Get Pro"-knapp [BILD reactbits-dev/desktop-forsta.png; TEXT SIDA.md designfakta]. Sajterna som visar upp det är
  utvecklarportföljer och inloggningssidor för appar [REPO Showcase.js rad 3–31]. Våra verksamheter är lokala
  hantverkare där ägaren dömt det härledda och verkliga som det bästa (byggdagbok med egna telefonbilder, ordagranna
  omdömen, gulmarkerad konkret del av citatet) och de generiska mönstren som det som luktar mall (`LARDOMAR.md` rad 29,
  54, 78); riktningen ska härledas ur verksamheten, "aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md:
  200–201`). En aurora bakom "Elektriker i Luleå" gör inte sajten mer Sundboms, den gör den mer reactbits. Mikro-
  kategorin, som är ny, är gjord för AI-appar: CallChip visar ett verktygsanrop med "bash npm test" och
  status running/done/failed [REPO CallChip.jsx rad 18–19, 26–28], inte en ringknapp. Pro-delen säljer dessutom en
  "Agent Kit" med stilskills för Claude Code [REPO Pro.js rad 120–137], och förhandsbilderna är exakt det vi inte vill
  ha: fintech-mallen "Bastion" med SOC 2-märken och tre nyckeltal [BILD skill-corporate-trust.webp] och byrån
  "Kilter" i serif på crème [BILD prompt-agency.webp]; snyggt, men utbytbart. Samma dom som för shadcn/ui, Bootstrap
  och three.js (ovan), och ägaren höll med i alla tre (`kunskap/KIRURG-OMDOMEN.md`). Källkritik: "largest & most
  creative" och "ship stunning interfaces faster" [REPO README.md rad 11, 33] är egna omdömen; källan säljer Pro
  (765 poster [REPO Pro.js rad 29–36]) och sponsorplatser till shadcn-ekosystemet [REPO README.md rad 116; BILD
  reactbits-dev/desktop-skroll-07.png]. Komponenterna är i sig välgjorda (rörelsehänsyn, aria-live i CallChip rad
  151–152, 208), så nej gäller passformen, inte hantverket. Ändras om en framtida kund säljer något där rörelsen är
  varan (en byrå, en spelstudio); bedöms då med det fallet framför sig
- Kostnad: ingen; inget tas in. Som beroende vore det React, React DOM och per komponent motion, GSAP eller ogl i
  varje sida som använder den, mot vår budget 200 kB JS (standarden 3.7), plus versionsuppföljning av fem
  animationsbibliotek
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text riktad till agenter, inga hookar, MCP-servrar eller
  skill-frontmatter. 302 skript: `scripts/generateOgImages.js` har nätanrop, eval/exec och miljövariabler (bygger
  OG-bilder för deras sajt), `src/constants/Information.js` nätanrop, `src/utils/aiExport.js` eval/exec; allt hör till
  deras dokumentationssajt, inte komponenterna. `scripts/generateLlmsText.js` skriver en `llms.txt` med UTM-märkta
  länkar till Pro för agenter [REPO rad 15–19]; gäller kodgenererande agenter, inte kirurgen. Inget kördes eller
  installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · CorentinTh/it-tools · nej
- Källa: https://github.com/CorentinTh/it-tools @ d505845 (ur klonens `.git/refs/heads/main`, klonad 2026-10-02; senaste
  push 2026-09-30T18:31Z), GPL-3.0 [REPO LICENSE rad 1–2; README.md rad 133]; cirka 40 700 stjärnor, inte arkiverat;
  cirka 15 900 tokens text i 324 textfiler. Inte bedömd förut. Förgranskat. Läst: README i helhet, `package.json`,
  `src/tools/index.ts` i helhet (verktygslistan), `src/tools/meta-tag-generator/` (alla tre filer),
  `src/tools/svg-placeholder-generator/index.ts`, `src/plugins/plausible.plugin.ts`, och titel och beskrivning för
  varje verktyg i `locales/en.yml` rad 75–394. Övriga verktygskataloger bara som fillista. Sett: `public/banner.png`,
  `.github/logo-dark.png`, och demosajten it-tools.tech öppnad i dag i 390 och 1440: mobilens och desktops första vy,
  desktop-skrolläge 4 av 8 och mobil-skrolläge 3 av 6. Ägarens not: ingen
- Steg: inget av de åtta. Närmast steg 5 (metataggar, slug, färgkonvertering, delningsbild) och steg 6 (kontroll av
  title och description), men som handverktyg i en webbläsare, inte som något bygget kan använda
- Jämfört med i dag: it-tools är en Vue-app med 86 små verktyg i tio kategorier (Crypto, Converter, Web, Images and
  videos, Development, Network, Math, Measurement, Text, Data) [REPO src/tools/index.ts rad 91–192; BILD
  it-tools-sida/desktop-forsta.png: sidomeny och kort], där en människa klistrar in text och får ett resultat: hash,
  UUID, JSON till YAML, chmod, crontab, JWT-parser, IBAN-kontroll [REPO locales/en.yml rad 83–394]. De fyra som rör
  en sajt gör vi redan i kod: Open Graph-taggarna [REPO en.yml rad 309–310; meta-tag-generator.vue rad 2, 49] skriver
  mallen själv (`mall/astro/src/layouts/Bas.astro` rad 25, 31–35: theme-color, og:title, og:image 1200×630);
  delningsbilden och apple-touch-icon gör `kontroller/ikoner.mjs` (rad 1–4, 40) ur verksamhetens eget foto; title
  och description prövas av `kontroller/seo_kontroll.py` (rad 77–87, längd och unikhet); slug [REPO en.yml rad
  149–150] och färgkonvertering [rad 121–122] är engångsrader i Astro. Kontrast, som är det som faktiskt avgör en
  färg hos oss (standarden 3.4), finns inte som verktyg i källan. Två verktyg krockar: "SVG placeholder generator"
  [REPO en.yml rad 101–102] och "Lorem ipsum generator" [rad 249–250] gör det byggstandarden 9.4 förbjuder
  (`kunskap/byggstandard.md:122`, "inga platshållare") och det copykontrollen flaggar (`kunskap/copy-kontroll.md:14`,
  "lorem ipsum"). QR-koden [REPO en.yml rad 253–254] hör till verksamhetens egen vardag (be om omdömen via QR,
  `kunskap/lokal-synlighet.md:38`), inte till sajten. Lika eller sämre på varje punkt som rör oss
- Skäl: Källan är "handy online tools for developers" [REPO README.md rad 8; BILD it-tools-sida/desktop-forsta.png
  rubriken "Handy tools for developers"]: ett gränssnitt för människor som behöver avkoda en JWT eller räkna ut ett
  subnät. Vår arbetsmodell är en agent som skriver sajten som kod och prövar den med egna kontroller; allt it-tools
  kan göra som berör en sajt gör agenten med en rad i mallen, och en webbläsarsida att klicka i är ett steg till,
  inte ett färre. Det är varken bättre sajter eller smartare arbete. Den egna sajten är dessutom en appvy, inte en
  referens för våra verksamheter: hamburgare, sökfält och "Buy me a coffee" i första vyn på mobil, sedan ett kort
  "You like it-tools? Give us a star on GitHub" före innehållet [BILD it-tools-sida/mobil-forsta.png], systemtypsnitt
  och 0 bilder [TEXT SIDA.md rad 8, 31]. Två verktyg (platshållarbilder och lorem ipsum) står emot regeln mot slop.
  GPL-3.0 gör dessutom att kod ur repot inte kan kopieras in i en kunds sajt utan att hela sajten omfattas av
  licensen; vi skulle ändå inte kopiera, men det stänger också dörren för "några rader ur källan". Samma slag av dom
  som för awesome-listorna och the-book-of-secret-knowledge (ovan): en bra samling för en utvecklare, utan plats i
  bygg-sajts åtta steg. Källkritik: "with great UX" [REPO package.json rad 6] är eget omdöme; sajten säljer inget men
  ber om stjärnor och donationer [BILD mobil-forsta.png]; inget försöker styra agenter
- Kostnad: ingen; inget tas in. Som självhostat verktyg vore det en Docker-container [REPO README.md rad 23–30] med
  67 npm-beroenden [REPO package.json rad 39–106] att hålla uppdaterade, för uppgifter mallen redan löser
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text riktad till agenter, inga hookar, MCP-servrar eller
  skill-frontmatter. 279 skript; mönstren "hemligheter/miljö" i bcrypt-, JWT-, OTP- och lösenordsverktygen är
  verktygens egna ämnen, "eval/exec" i `regex-tester.service.ts` är regex-provaren och i `scripts/shared/commits.mjs`
  deras släpp-skript. `plausible.plugin.ts` kopplar in Plausible-analys när konfigurationen tillåter det [REPO rad
  24–26]; gäller deras sajt. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · JCodesMore/ai-website-cloner-template · nej
- Källa: https://github.com/JCodesMore/ai-website-cloner-template @ f50066d (ur klonens `.git/shallow`, tagg v0.5.1;
  senaste push 2026-09-27T04:51Z), MIT [REPO LICENSE; package.json rad 7]; cirka 35 500 stjärnor, inte arkiverat;
  cirka 17 500 tokens text i 39 textfiler. Inte bedömd förut. Förgranskat. Läst i helhet: README, AGENTS.md,
  CLAUDE.md, `.claude/commands/clone-website.md`, `.agents/skills/clone-website/SKILL.md` (507 rader) och
  `references/inspection-guide.md`, package.json. Sett: `docs/design-references/comparison.png` (original mot klon av
  instruct.ai) och demovideon "Claude Code website cloner demo" (1:14, inget transkript, inga undertexter): alla sex
  bildrutor. Ägarens not: ingen
- Steg: inget av de åtta. Närmast steg 2 (den tar isär en befintlig sajt) och steg 5 (den bygger), men med ett annat
  mål: återskapa någon annans sajt pixel för pixel i Next.js
- Jämfört med i dag: Källan är en Next.js 16-mall med shadcn och Tailwind 4 [REPO package.json rad 37–57] plus en
  skill som läser en adress i webbläsaren, hämtar text, bilder och beräknad CSS per sektion, skriver en specfil per
  komponent, skickar parallella byggagenter i worktrees och jämför klonen mot originalet sida vid sida [REPO SKILL.md
  rad 148–459]. Målet står på rad 18–21: "Pixel-perfect — exact match in colors, spacing, typography, animations",
  och utanför ramen står "SEO optimization, accessibility audit". Vi gör motsatsen på varje punkt. (1) Vi härleder
  sajten ur verksamheten själv, aldrig ur någon annans sajt eller en mall (`.claude/skills/bygg-sajt/SKILL.md` rad
  200–201, 252 "Kopiera aldrig layout, palett eller typsnitt"; ägarens mall-lukt i L1–L3 satt i formen, `LARDOMAR.md`
  rad 29, 54, 78). Verksamhetens nuvarande sajt är ribba 1, det vi ska slå (SKILL.md rad 9, 115), inte något att
  återskapa: de tre dömda byggena hade Lighthouse mobil 41–60 och 14–18 allvarliga axe-fel att lämna bakom sig
  (`LARDOMAR.md` rad 38, 63, 87). (2) Stacken: statisk Astro utan JavaScript, högst 200 kB JS och 100 kB CSS
  (`kunskap/byggstandard.md` rad 25, 52, 133–138 "Astro i stället för Next.js"; rule of least power i
  `kunskap/teoretisk-grund.md` rad 47–50); de tre byggena levererade 0 kB JS (`LARDOMAR.md` rad 31, 56, 87). (3) Det
  källan gör bra som hantverk har vi redan: "Spec Files Are the Source of Truth" [REPO SKILL.md rad 138–142]
  motsvaras av KONCEPT.md:s exakta specifikation före kod (SKILL.md rad 207–210); "Visual QA Diff" sida vid sida
  [REPO rad 445–459] av JAMFORELSE.md mot referenserna i åtta dimensioner (SKILL.md rad 246–252); beräknade
  designfakta (typsnitt, storlek, färg) ur `getComputedStyle` [REPO rad 269–311] tar `kontroller/sida.mjs` fram för
  varje referens (rad 3, 113, 121) och `hamta_sajt.py` hämtar text och bildlista ur deras sajt (SKILL.md rad 66–68);
  "Build Must Always Compile" är snabbprovet (SKILL.md rad 237). (4) Interaktionssvepet (scroll, klick, hover,
  tillstånd) [REPO rad 168–194] löser ett problem vi inte har: våra sajter har inga tillstånd att återskapa, och vår
  diagnos av deras sajt använder heuristisk utvärdering och kognitiv genomgång ur litteraturen (SKILL.md rad
  109–114), inte en inventering av animationer. Sämre på det som rör oss, lika på hantverket
- Skäl: Källan svarar på frågan "hur kopierar jag en sajt exakt", och hela vårt arbetssätt är byggt för att aldrig
  behöva ställa den: slop uppstår när modellen saknar något specifikt att säga (SKILL.md rad 12–13), och ett pixelkopierat
  original är det minst specifika en hantverkare i Luleå kan få. Källans egna legitima fall, flytt av en sajt man
  äger till ny stack [REPO README.md rad 94–96], är inte vårt erbjudande: vi ersätter deras sajt eftersom den är
  sämre, inte flyttar den. Den krockar alltså med två medvetna val (verksamhetens egna bilder och ord; statisk Astro
  utan JS) och hjälper oss varken bygga bättre sajter eller arbeta smartare: byggtiden hos oss går till
  granskningsrundor, inte till att skriva kod (`LARDOMAR.md` rad 100–101: 117–126 minuter, 3–5 omgångar), så
  parallella byggagenter i worktrees [REPO rad 405–432] skulle lägga till sammanslagningar utan att korta det som tar
  tid. Resultatet är dessutom inte vad det lovar: i källans egen jämförelsebild har originalets kort miniatyrbilder
  och klonens bara ikoner, och första vyns vertikala placering skiljer [BILD docs/design-references/comparison.png;
  BILD 00:02]; mitt i körningen stannar bygget på ett saknat typsnitt ("Font file not found") [BILD 00:39]; sektionen
  "Just describe the work" ligger nära men inte lika [BILD 00:14]. Källkritik: videon visar körningen med Opus 4.6 i
  Claude Code [BILD 00:27, läsbart i terminalen] medan README rekommenderar Opus 5.5 [REPO README.md rad 9]; "No
  guessing" [rad 90] och "nails it every time" [REPO SKILL.md rad 73] är egna omdömen utan belägg. README innehåller en
  färdig uppmaning avsedd att klistras in i en agent (klona, installera, kör `npm run check`) [REPO README.md rad
  33–41]; den följdes inte. Samma dom som för firecrawl och crawl4ai (ovan): ett verktyg för att hämta andras sajter,
  utan plats i bygg-sajts åtta steg. Ägaren höll med om nej för dem och om nej för ui-ux-pro-max och shadcn-ui
  (`kunskap/KIRURG-OMDOMEN.md`)
- Kostnad: ingen; inget tas in. Skillen vore 115 tokens alltid, 8 931 vid användning och 913 vid behov, plus Next.js 16,
  React 19, shadcn, Tailwind 4, Node 24 och en webbläsar-MCP som krav [REPO SKILL.md rad 53; README.md rad 68–78]
- Säkerhet: förgranskningen LÅG: inga dolda tecken, ingen text riktad till agenter, inga hookar, MCP-servrar eller
  skill-frontmatter med behörigheter; fyra skript (eslint, next, postcss, `cn()`), inga riskmönster. AGENTS.md
  inleds med ett block som Next.js själv skriver in och som ber agenten läsa `node_modules/next/dist/docs/` [REPO
  AGENTS.md rad 1–9]; ofarligt, hör till deras stack. Inget kördes eller installerades
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · lissy93/web-check · parkera
- Källa: https://github.com/lissy93/web-check @ 0690bb3 (ur klonens `.git/refs/heads/master`; senaste push
  2026-10-02T19:06Z), MIT, cirka 35 000 stjärnor, inte arkiverat, version 2.3.0 [REPO package.json rad 4]. Läst: README,
  alla 48 API-kontroller som lista och i sin helhet `api/mail-config.js`, `api/http-security.js`, `api/trackers.js`,
  `api/tech-stack.js`, `api/quality.js`, `api/cookies.js`, `api/ports.js`, `api/_common/middleware.js`, samt
  regelmotorn `src/client/analysis/registry.ts` och reglerna för e-post, svarshuvuden och delningstaggar. Sett: 3 av 47
  bilder, de tre helsidesskärmbilderna av instrumentpanelen för github.com, news.ycombinator.com och stackoverflow.com
  [BILD .github/screenshots/web-check-screenshot1.png, -screenshot2.png, -screenshot10.png]. Demon web-check.xyz
  öppnades inte: skärmbilderna visar samma vy, och verktyget skannar en domän på riktigt.
- Steg: 2 (diagnos av nuvarande sajt) och lanseringen (fas L i byggstandarden: 6.6, 8.1, 10.3). Inget av stegen 3–7.
- Jämfört med i dag: källan är en instrumentpanel som kör ett 40-tal uppslag mot en levande domän och visar dem som
  kort: serverplats, certifikat, whois, DNS, svarshuvuden, HSTS, teknikstack, PageSpeed, kakor, spårare, e-postposter,
  delningstaggar, robots, sitemap, öppna portar, traceroute, hotlistor, arkivhistorik [BILD web-check-screenshot1.png;
  REPO registry.ts rad 33–59]. Sak mot sak. (1) Diagnosen av deras sajt: vi kör axe, Lighthouse och inspektionen i 390
  och 1440 px och gör heuristisk utvärdering och kognitiv genomgång (`.claude/skills/bygg-sajt/SKILL.md` rad 99–114);
  `hamta_sajt.py` läser generator-taggen (rad 132) och inspektionen loggar varje blockerad tredjepartsförfrågan
  (`kontroller/webblasare/gemensamt.mjs` rad 84, `inspektera.mjs` rad 61). De tre dömda byggena fann WordPress/Divi,
  WordPress/Elementor, cookiebanner och utgånget Instagramflöde den vägen (`LARDOMAR.md` rad 38, 63, 87;
  `underlag/sundboms-el/DIAGNOS.md` rad 3). Källans Wappalyzer [REPO api/tech-stack.js rad 26] och Ghosterys
  spårardatabas [REPO api/trackers.js rad 3–4] ger namngivna produkter i stället för domänlistor: lite bättre
  som inventering, men inget som ändrar ribba 1, som sätts av Lighthouse, axe och första vyn. Lika i sak.
  (2) Svarshuvuden: källan svarar bara ja eller nej per huvud [REPO api/http-security.js rad 5–23], medan
  `kontroller/prelaunch.py` läser CSP:ns innehåll (object-src, base-uri, unsafe-inline utan hash, rad 398–409) och
  kräver frame-ancestors och nosniff (rad 443–449). Sämre. (3) E-postposter: `kunskap/lansering.md` rad 49–64 läser SPF,
  DKIM under en angiven selektor och DMARC och säger "saknas både SPF och DKIM blir det fynd; saknad DMARC blir
  anmärkning; flera SPF-poster är ett fynd" (rad 59–60). Källan provar 17 vanliga DKIM-selektorer [REPO
  api/mail-config.js rad 17–35], räknar SPF-uppslag mot gränsen 10 (rad 83–101) och dömer policyn: SPF utan -all
  eller ~all, DMARC p=none som "monitor-only", pct under 100, sp som släpper underdomäner, DKIM-nyckel under 1 024
  bitar [REPO src/client/analysis/rules/mail-config.ts rad 44–166]. Bättre regler än våra, på en punkt
  (byggstandarden 6.6, `kunskap/byggstandard.md` rad 89) som prövas först vid lansering, och verktyget lansering.md
  pekar på (`verktyg/lansering.py`, rad 20, 51) finns inte i det här repot. (4) Delningstaggar: källan flaggar saknad
  og:image [REPO rules/social-tags.ts rad 3–8]; `seo_kontroll` och standarden prövar 7.1 på vår sajt
  (`byggstandard.md` rad 97). Lika. (5) Litteraturen: header-skanning och OWASP står redan som metoder
  (`kunskap/teoretisk-grund.md` rad 95–99); källan tillför ingen utvärderingsmetod, bara fler uppslag. Samma slutsats
  som för the-book-of-secret-knowledge ovan (rad 517–519): ett andra kvitto på den levande adressen vid lansering, inte
  en ny kontroll; ägaren höll med om den domen (`kunskap/KIRURG-OMDOMEN.md`).
- Skäl: Inget i källan rör det ägarens domar L1–L3 pekar på: förfrågningsvägen, bildunderlaget, förtroendet och
  rösten. Den kan inte få oss att bygga bättre sajter, och i byggena gör den inget smartare än det vi mäter
  (`lighthouse.mjs` rad 35–42 ger samma PageSpeed-poäng som källans quality-kort, som dessutom kräver en Google-nyckel
  [REPO api/quality.js rad 6, README rad 175]). Det som är bättre, e-postreglerna, hör till lanseringen, som inte har
  ägt rum för något bygge och vars L-punkter inte redovisas (`SKILL.md` rad 319). Därför parkera, inte nej: när den
  första lanseringen planeras är reglerna i `mail-config.ts` värda några rader i `lansering.md`, och en driftad
  instans (web-check.xyz eller egen) är ett handkvitto på den levande adressen bredvid securityheaders.com. Att ta in
  den nu vore fel på tre sätt: den är en tjänst att driftsätta (Astro + React + Svelte + Puppeteer + Chromium +
  Wappalyzer + Express, [REPO package.json rad 23–63; README rad 213–214]), inte en skill eller en textrad, och kod ur
  källor körs inte; den skannar portar och kör traceroute mot kundens värd [REPO api/ports.js rad 6–9,
  api/trace-route.js] och presenterar sig som ett verktyg för att "uncover potential attack vectors" [REPO README.md
  rad 70], vilket går utöver "bara läsning" i steg 2 (`SKILL.md` rad 114–115) och vore fel att rikta mot en
  hantverkares webbhotell utan deras uttryckliga ja; och svarshuvudkontrollen är grundare än vår. Källkritik: README
  bär tre sponsorer och Hostinger-länkarna är affiliate-länkar [REPO README.md rad 14–40, 128]; stjärnorna är räckvidd,
  inte belägg; koden är välskriven och nyligen underhållen (push samma dag), och reglerna i mail-config.ts stämmer med
  vad Gmail och DMARC-standarden kräver (`lansering.md` rad 62–64 säger samma sak om Gmail).
- Kostnad: ingen; inget tas in. Hela källans text är cirka 9 100 tokens enligt förgranskningen; 140 skript; inga
  skills. Vid lansering: fem till åtta rader i `lansering.md` och ett manuellt kvitto, inga beroenden.
- Säkerhet: förgranskningen MEDEL över 171 textfiler: inga dolda tecken, ingen text riktad till agenter, inga hookar,
  MCP-servrar eller skill-frontmatter. Riskmönstren är verktygets natur: nätanrop i sju skript, miljönycklar i tolv
  (API-nycklar till Google, Shodan, Cloudmersive, Tranco, GitHub, CertSpotter [REPO README.md rad 173–181]), eval/exec
  i skärmbilds- och traceroute-kontrollen. Portskanning, subdomänsökning, läckkontroll och Shodan är OSINT mot andras
  domäner; inget kördes eller installerades. README:s installationsrader följdes inte.
- Förslag: inget nu. Vid första planerade lansering: (a) lägg källans e-postregler som rader i `kunskap/lansering.md`
  efter rad 60 (DMARC p=none är bara övervakning, pct under 100, sp som släpper underdomäner, SPF utan -all/~all,
  fler än 10 SPF-uppslag, DKIM under 1 024 bitar, prova de vanliga selektorerna när leverantörens är okänd); (b) kör
  en driftad web-check mot den levande adressen som handkvitto på e-postposter och svarshuvuden, med portskanning och
  traceroute avstängda (`API_DISABLED_CHECKS` [REPO README.md rad 191]).
- Utfall: — (aktuellt först när en sajt ska lanseras på riktigt; se `LARDOMAR.md` för om någon nått dit)
- Backlog: ingen

### 2026-10-02 · jackwener/OpenCLI · nej
- Källa: https://github.com/jackwener/OpenCLI @ 2413694 (ur klonens `.git/packed-refs`; senaste push
  2026-09-24T18:55Z), Apache-2.0; cirka 29 800 stjärnor, inte arkiverat; 2 541 textfiler, cirka 294 000 tokens text.
  Inte bedömd förut. Förgranskat. Läst: README i helhet, `PRIVACY.md`, `extension/manifest.json`,
  `skills/opencli-browser/SKILL.md` i helhet, `skills/opencli-adapter-author/SKILL.md` i helhet (kinesiska),
  `skills/opencli-usage/SKILL.md` rad 1–60, `skills/smart-search/SKILL.md` i helhet, de flaggade raderna i
  `references/deep-recon.md` och `docs/advanced/cdp.md`, och adapterlistan i `docs/adapters/index.md` som sökning.
  Sett: den enda bilden, butiksbilden för tillägget [BILD extension/store-assets/screenshot-1280x800.png]: terminalen
  kör ett kommando mot Zhihu och får en tabell, bredvid samma lista i Chrome. Ingen demosajt. Ägarens not: ingen
- Steg: 6 (prov) och granskaren, i teorin; i praktiken inget av de åtta
- Jämfört med i dag: OpenCLI gör webbplatser till kommandon och låter en agent styra användarens inloggade Chrome
  genom ett tillägg och en lokal daemon [REPO README.md rad 3, 15, 41–43]. Tillägget begär debugger, cookies och alla
  adresser [REPO extension/manifest.json rad 6–17], läser kakor för den inloggade sajten så att kommandon kan agera
  som användaren [REPO PRIVACY.md rad 23], och de inbyggda adaptrarna är Xiaohongshu, Bilibili, Zhihu, Twitter,
  LinkedIn, Reddit, Amazon och liknande [REPO README.md rad 178–200]. Sak mot sak: (1) **Styra en sida ad hoc**
  (`state`, `click`, `fill`, `wait`, `network`, strukturerade svar med `match_level`) [REPO
  skills/opencli-browser/SKILL.md rad 53–71, 121–216]. Hos oss gör Playwright samma arbete utan daemon eller tillägg:
  provet kör `kontroller/webblasare/utforska.mjs` på upp till tolv sidor (`kontroller/prova.py:378`) och
  `inspektera.mjs` i tre vyer (`:331`), och granskaren ser tillstånd med `inspektera.mjs` och sidor med `sida.mjs`
  (`kritik/GRANSKARE.md:48–54`). Lika i förmåga, med ett globalt npm-paket, ett Chrome-tillägg och en daemon på
  localhost:19825 till [REPO README.md rad 33–51, 279]. (2) **Formulär.** Källans recept fyller i inloggningar och
  skickar [REPO skills/opencli-browser/SKILL.md rad 317–328]; vårt verktyg skickar aldrig ett formulär utan uttrycklig
  flagga och testmarkering (`kontroller/webblasare/utforska.mjs:2–4, 36–38`) och bygget får inte skicka något alls
  (`.claude/skills/bygg-sajt/SKILL.md:50–51`). Sämre för oss. (3) **Skärmbilder.** Källan säger att skärmbilder är
  för människor, inte agenter, och att textträdet ska användas [REPO skills/opencli-browser/SKILL.md rad 133, 414].
  Hos oss är det tvärtom ett medvetet val: granskaren tittar på varje skärmbild i 390 och 1440 och dömer designen med
  egna ögon (`kritik/GRANSKARE.md:44–47`), eftersom de åtta dimensionerna i `kunskap/referenser-professionella.md`
  inte syns i ett DOM-träd. Sämre. (4) **Skriva adaptrar** för nya sajter, med rekognoscering, API-upptäckt och
  strategival [REPO skills/opencli-adapter-author/SKILL.md rad 31–64, 145–214]: handlar om att hämta data ur andras
  sajter, inte om att bygga en. Inget steg hos oss. (5) **Hitta kunder senare.** Adaptrarna är kinesiska och
  amerikanska plattformar; ingen svensk katalog, ingen kartjänst [REPO docs/adapters/index.md, sökning på maps,
  hitta, eniro, allabolag: inga träffar]. LinkedIn-adaptern kan söka, läsa profiler och skicka [REPO README.md rad
  186], men det är skrapning genom en inloggad session, vilket inte är vår väg till kunder
- Skäl: OpenCLI är byggt för att låta en agent agera som användaren på andras sajter: läsa flöden, publicera, följa,
  skicka meddelanden, ladda ned [REPO README.md rad 178–200]. Ingenting i det bygger en bättre sajt, och det som
  liknar vårt prov, att styra en sida och läsa dess tillstånd, har vi redan med Playwright utan inloggad session.
  Det krockar med tre medvetna val: inget skickas ut, kod ur källor körs inte (skillsen förutsätter ett installerat
  `opencli` i `allowed-tools` [REPO skills/opencli-browser/SKILL.md rad 4] och installation via npm och tillägg [REPO
  README.md rad 36–51, 106]), och granskaren dömer design med ögonen. Dokumentationen visar dessutom hur Chromes
  felsökningsport exponeras på internet via ngrok [REPO docs/advanced/cdp.md rad 64–74]. Smart i källan: det
  strukturerade svaret med `matches_n` och `match_level` efter varje klick, och regeln att verifiera skrivningar med
  `get value` [REPO skills/opencli-browser/SKILL.md rad 54, 67]; det är god agentergonomi, men vår utforskning är ett
  skript som redan har tillgång till Playwrights egna locators och behöver inte kuvertet. Källkritik: inga
  mätningar, bara påståenden om tillförlitlighet ("fix-frekvens 7–8 gånger" för interna API:er [REPO
  skills/opencli-adapter-author/SKILL.md rad 62]) utan data i repot. README och skills riktar sig till agenter
  (installera skills med `npx skills add` [REPO README.md rad 106]); det följdes inte
- Kostnad: ingen; inget tas in. Som skills vore det 10–95 tokens var i varje session (sex skills, cirka 380 tillsammans),
  379–7 183 vid användning och upp till 27 541 vid behov, plus Node 20, ett globalt npm-paket, ett Chrome-tillägg med
  debugger- och cookiebehörighet och en daemon
- Säkerhet: förgranskningen HÖG. Nio dolda tecken, alla i testdata: U+200E i kinesiska filmtitlar
  (`clis/douban/utils.test.js` rad 192, 199, 226–227), U+200B i ett span i en fixtur som prövar filtret mot
  skrapskydd (`clis/facebook/feed.test.js` rad 259) och U+200C i en Wikipedia-fixtur; inga instruktioner. De tre
  agentriktade träffarna är användardokumentation ("Run this command" om ssh och ngrok i `docs/advanced/cdp.md` rad
  56, 68) och en regel mot att exfiltrera hemligheter (`references/deep-recon.md` rad 84). HÖG kommer av 2 219 skript
  med nätanrop, eval/exec och miljövariabler, en `curl | bash`-rad i `CHANGELOG.md` rad 238, och `allowed-tools` med
  Bash i fyra skills. Tillägget läser kakor och använder debugger-API:et mot alla adresser [REPO extension/manifest.json
  rad 6–17]. Inget kördes eller installerades. Inget försök att styra kirurgen utöver installationsraderna
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-02 · foundation/yeti · nej
- Källa: https://github.com/foundation/yeti @ f52d1e8 (ur klonens `.git/shallow`; senaste push 2026-09-25T18:02Z),
  FSL-1.1-MIT (Functional Source License, blir MIT två år efter varje release) [REPO LICENSE rad 5, 87–92]; cirka
  29 800 stjärnor (repot är det gamla foundation-sites, Foundation 6 lever på grenen `v6` [REPO README.md rad 5]), inte
  arkiverat. 507 textfiler, cirka 290 000 tokens. Förgranskat. Läst i helhet: README, LICENSE, `package.json`,
  `docs/guides/layouts.md`, `docs/guides/install.md`, `docs/guides/stability.md`, `docs/guides/theming.md`,
  `src/starter/index.html`, `src/starter/theme.css`; `src/guides/responsive.md` rad 1–60; `src/components/nav/nav.css`
  bara som sökning på popover. Sett sju av skärmbilderna i `test/browser/screenshots/`: starter, hero-receptet, nav,
  card, base, sidebar och de två temana (light). Komponenternas CSS, manifesten, `bin/`-skripten och testerna lästes
  inte. Ingen demosajt öppnad: README länkar bara till foundationcss.com, och paketet är inte släppt [REPO
  docs/guides/install.md rad 41]. Ägarens not: ingen
- Steg: 5 (koncept och bygge); möjligen mallen `mall/astro/`
- Jämfört med i dag: (1) **Stilmallen.** Vår mall bär medvetet ingen design: `mall/astro/src/layouts/Bas.astro` rad
  2–3 och `mall/astro/README.md` rad 3–5 säger att allt synligt skrivs för verksamheten, och steg 5 härleder fyra
  riktningar ur verksamhetens material, "aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md` rad 200–201).
  Yeti är en hel stilmall med standardval: blå primärton 250, systemtypsnitt, radie 0,5 rem på kort [REPO
  src/starter/theme.css rad 19, 41, 72], och startsidan är "rubrik + ingress + två knappar + bild, tre likadana kort,
  en Om-text" [REPO src/starter/index.html rad 44–91; BILD starter-light.png]. Det är ordagrant de mönster granskaren
  straffar under originalitet: "likadana kort i rad, samma sektionsmall sektion efter sektion" (`kritik/GRANSKARE.md`
  rad 84–88), och det ägaren pekade ut som det enda mall-luktande i L1 och L3 (`LARDOMAR.md` rad 29, 78). Sämre.
  (2) **Meny och karusell.** Navkomponenten viker menyn bakom en hamburgare under tröskeln, med popover [REPO
  src/starter/index.html rad 31–39; src/components/nav/nav.css rad 2]; ägaren valde synliga länkar utan hamburgare
  (`LARDOMAR.md` rad 69) och skillen kräver det (`bygg-sajt/SKILL.md` rad 222). Källan levererar en karusell
  (`src/components/carousel/`), som byggstandarden 5.5 förbjuder. Krockar med medvetna val. (3) **Vikt.** De tre dömda
  byggena väger 4–10 kB CSS och 0 kB JS (`LARDOMAR.md` rad 31, 56, 87). Yeti är en stilmall för 49 komponenter och 17
  layouter med valfri bantning via egen `@import`-lista och esbuild [REPO docs/guides/install.md rad 77–106], och
  dess CSS skulle läggas under byggstandardens 3.7 (100 kB) men över allt vi levererat. Sämre. (4) **Metoden.**
  Det Yeti gör bra är inte stilmallen utan grammatiken: layouten äger avståndet och barnen bär inga marginaler [REPO
  docs/guides/layouts.md rad 12, 172], en skala för text och luft ur bas och kvot [REPO docs/guides/theming.md rad
  65–76], och tröskel per komponent i stället för viewport-brytpunkt, med media queries bara för besökarens
  preferenser [REPO docs/guides/layouts.md rad 16–24; src/guides/responsive.md rad 31–49]. Det är Every Layout (Bell &
  Pickering 2019), som `kunskap/teoretisk-grund.md` rad 64–65 och 154 redan namnger som princip, men som
  `kunskap/bygge-referens.md` inte gör något av: dess enda layoutrad är "responsivt utan horisontell spill" (rad 10).
  Byggstandarden 3.1 kräver en typografisk skala och ett avståndssystem, men säger inget om vem som äger avståndet.
  Metoden är lika i litteraturen och bättre formulerad hos källan än hos oss
- Skäl: Yeti är Foundation 6:s efterträdare, ett välbyggt CSS-ramverk med rätt instinkter: ingen byggkedja, cascade
  layers, container queries, `light-dark()`, tokens som data och ett manifest som dokumentation, typer och `llms.txt`
  genereras ur [REPO README.md rad 19–24; docs/guides/install.md rad 179–204]. Men att bygga våra sajter på det drar
  dem mot biblioteksstandard, samma dom som för twbs/bootstrap och shadcn-ui/ui i det här registret: startsidans
  skelett [BILD starter-light.png] och hero-receptets åtta varianter av "text på ena sidan, bild på den andra" [BILD
  recipes-hero-light.png] är just det granskaren och ägaren straffar, och menyn med hamburgare och karusellen krockar
  med två medvetna val. Till det kommer att paketet inte är släppt och att README säger beta medan `package.json`
  säger alpha [REPO README.md rad 9; package.json rad 3]: ytorna är frysta enligt stabilitetssidan [REPO
  docs/guides/stability.md rad 12–23], men standardvärdena får flytta. Licensen tillåter professionella tjänster [REPO
  LICENSE rad 51–52] och är inget hinder, men varje kundsajt skulle bära en licenstext som inte är MIT på två år.
  Smart i källan, och värt att ta med som idé, är layoutgrammatiken i (4); den kräver inget ramverk, bara tre rader i
  vår egen text, och träffar den dimension ägaren dömt lägst i alla tre byggen: "Luft och hierarki: Okej"
  (`LARDOMAR.md` rad 35, 60, 84). Källkritik: README:n gör påståenden utan mätningar ("coherent site fast",
  "accessible by default, checked in CI" [REPO README.md rad 13, 23]); axe körs i deras Playwright-svit
  (`@axe-core/playwright` i `package.json` rad 54) men inga tal redovisas. Skärmbilderna är fixturer med platshållare,
  inte sajter [BILD components-card-light.png, base-light.png], så ingen färdig sajt gick att döma
- Kostnad: inget tas in ur källan. Som beroende i varje bygge vore det ett npm-paket som inte finns ännu, en stilmall
  på tiotals kB före bantning, nio valfria JS-moduler (cirka 9 kB komprimerat [REPO docs/guides/install.md rad 149])
  och Node 24 för källans egen byggkedja [REPO package.json rad 12]; källans text är cirka 290 000 tokens. Egen
  innovation: tre rader i `kunskap/bygge-referens.md`, inga beroenden
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text till agenter, inga skills, hookar eller
  behörigheter. 124 skript; flaggorna "eval/exec" och "hemligheter/miljö" ligger i `bin/` (bygge, release,
  skärmbilder, validering), i komponenternas JS och i Playwright-testerna, och lästes inte i detalj. README:s
  kloningsrader och `npx playwright install` [REPO README.md rad 46–52] är användardokumentation, inte riktade till
  kirurgen; inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: inget ur källan. Egen innovation: `kunskap/bygge-referens.md`, efter rad 10 under "Krav på resultatet",
  tre punkter: avståndet ägs av layouten (gap på föräldern, aldrig marginaler på barnen; undantaget skrivs på barnet);
  text och luft delar en skala ur bas och kvot som CSS-variabler (byggstandarden 3.1); en sektion byter form vid sin
  egen tröskel (container query eller flex-basis mot en bredd ur skalan), media queries bara för besökarens
  preferenser. Källa i raden: Bell & Pickering (2019), Every Layout
- Utfall: tre layoutregler ur Every Layout i kunskap/bygge-referens.md 2026-10-03.
- Backlog: B-20261002-skriv-tre-layoutregler-i-bygge-referens-md-layou (egen innovation; domen om källan är nej)

### 2026-10-02 · react-hook-form/react-hook-form · nej
- Källa: https://github.com/react-hook-form/react-hook-form @ 7d1bce1 (ur klonens `.git/shallow`; senaste push
  2026-10-02T08:16Z), MIT; version 7.89.0, cirka 44 900 stjärnor, inte arkiverat; 318 textfiler, cirka 59 500 tokens
  text. Inte bedömd förut. Förgranskat. Läst: README i helhet, `package.json` i helhet, `src/form.tsx` i helhet,
  `src/index.react-server.ts`, `src/logic/validateField.ts` rad 1–120, `examples/V7/basicValidation.tsx` i helhet,
  fillistorna för `src/` och `examples/`. Övriga `src/logic/`, testerna och e2e bara som namn i förgranskningen.
  Sett: `docs/logo.png` och `docs/ads-1.jpeg` (en annonsbanner), och demosajten react-hook-form.com öppnad i dag med
  `sida.mjs`: mobilens första vy, desktops första vy och skrolläge 3 av 8. Ägarens not: ingen
- Steg: 5 (bygge: kontaktsidans formulär); inget annat
- Jämfört med i dag: (1) **Beroendet.** Paketet kräver React 16.8 eller senare som peer-beroende [REPO package.json
  rad 118–121]; vår mall har `astro` och `sharp` som enda beroenden (`mall/astro/package.json` rad 10–13), steg 5
  säger "ingen JavaScript som inte behövs" (`.claude/skills/bygg-sajt/SKILL.md` rad 217), och ägaren räknade 0 kB JS
  till det bästa i alla tre dömda byggen (`LARDOMAR.md` rad 31, 56, 87). Samma krock som react/react i det här
  registret. Sämre. (2) **Inskicket.** Källans `Form`-komponent skickar med `fetch` från JavaScript och sätter
  `noValidate` på formuläret så fort det är monterat, så webbläsarens egen validering stängs av och biblioteket tar
  över [REPO src/form.tsx rad 75–85, 146–150]. Mallens `Forfragan.astro` är en vanlig POST med `required`, `maxlength`
  och `type="tel"` som fungerar utan JavaScript (rad 17, 22, 26, 30), vilket byggstandarden 6.3 kräver
  (`kunskap/byggstandard.md` rad 86) och litteraturen motiverar: progressive enhancement, HTML före JS
  (`kunskap/teoretisk-grund.md` rad 47–48). Källans väg är motsatsen. Sämre. (3) **Valideringsreglerna.** Källans
  regler är desamma som HTML:s attribut: required, minLength, maxLength, min, max, pattern [REPO src/logic/validateField.ts
  rad 42–56; README rad 27], alltså en omskrivning i JavaScript av det webbläsaren redan gör åt vår form. Lika i sak,
  dyrare i väg. Ett grepp i källan är värt att låna utan biblioteket: med `shouldUseNativeValidation` skriver den
  felbeskedet in i webbläsarens eget via `setCustomValidity` och `reportValidity` [REPO src/logic/validateField.ts
  rad 62–76]. Byggstandarden 6.2 kräver svenska felmeddelanden vid fältet (rad 85), men mallen lämnar texten åt
  webbläsaren, vars besked följer gränssnittsspråket, och `kontroller/standard_kontroll.py` prövar bara `type` och
  `autocomplete` (rad 289–297, 445–455). Här är källan smartare än vi, i en detalj
- Skäl: react-hook-form är ett formulärbibliotek för React-appar med tillstånd: hooks, kontrollerade fält, fältlistor,
  omrenderingar [REPO README rad 1–3, 24–30; fillistan i `src/`], och demosajten säljer just det med
  "Render Count" och "Isolate Re-renders" bredvid en kodruta [BILD rhf-sajt/desktop-skroll-03.png]. Vår kontaktsida har
  ett formulär med tre fält och en bild; det behöver ingen tillståndsmotor, och det som biblioteket gör bättre än
  HTML (fältlistor, asynkron validering, scheman med Zod) gäller inte ett sådant formulär. Att ta in det skulle kräva
  React i varje bygge och flytta inskicket till JavaScript, vilket krockar med två medvetna val som ägarens domar
  bekräftat (0 kB JS; POST utan JS, dom L1 i `kunskap/forfragan.md` rad 3–6). Litteraturen står på vår sida: rule of
  least power och progressive enhancement (`kunskap/teoretisk-grund.md` rad 47–48, 119–120). Demosajten säger
  inget om design för våra sajter: mörkblå bakgrund, systemtypsnitt, rosa accent, en dokumentationssajt för
  utvecklare [BILD rhf-sajt/mobil-forsta.png; SIDA.md designfakta]. Källkritik: README:s påståenden om prestanda och
  storlek belägger sig med en storleksgräns i CI (15 kB för CJS-paketet [REPO package.json rad 110–116]) och en
  bundlephobia-länk; inget är anekdot, men inget mäter något vi mäter. README innehåller en annonsbanner och
  sponsorrutor [REPO README rad 61–84; BILD docs/ads-1.jpeg], vilket är finansiering, inte vilseledning
- Kostnad: inget tas in ur källan. Som beroende: React, en renderare och en Astro-integration per bygge, plus cirka
  15 kB bibliotek och Reacts runtime på kontaktsidan. Egen innovation: några rader i mallens befintliga skript och en
  rad i `kunskap/forfragan.md`, inga beroenden
- Säkerhet: förgranskningen MEDEL: inga dolda tecken, ingen text till agenter, inga skills, hookar eller behörigheter.
  251 skript; flaggorna "eval/exec" sitter i `src/logic/` och `src/utils/` (funktionskontroller, lästa i
  `validateField.ts` utan att något körs dynamiskt) och i tester; "hemligheter/miljö" i Playwright- och Jest-konfig,
  inte lästa i detalj. README:s installationsrad är användardokumentation. Inget försök att styra kirurgen; inget
  kördes eller installerades
- Förslag: inget ur källan. Egen innovation: `mall/astro/src/components/Forfragan.astro`, i det befintliga skriptet
  (rad 50–65): för varje fält med `required`, lyssna på `invalid` och `input` och sätt `setCustomValidity` till ett
  svenskt besked ur ett data-attribut på fältet när `validity.valueMissing`, annars tomt; bygget skriver beskeden i
  verksamhetens ord. `kunskap/forfragan.md` efter rad 18: en rad om att felmeddelandena vid fältet är svenska med
  JavaScript och webbläsarens egna utan. POST utan JS påverkas inte
- Utfall: mallens formulär ger svenska besked vid tomt fält med setCustomValidity 2026-10-03, prövat i engelsk
  webbläsare med och utan JavaScript.
- Backlog: B-20261002-mallens-formular-ger-svenska-felmeddelanden-vid (egen innovation; domen om källan är nej)

### 2026-10-02 · AI LABS, "He Finally 10x Claude Code With This Method" (YouTube qLfSDQ5NGh0) · ta in
- Källa: https://www.youtube.com/watch?v=qLfSDQ5NGh0 @ publicerad 2026-10-02, 12:51, kanalen AI LABS, 13 701
  visningar; YouTubes standardlicens. Läst hela det autogenererade transkriptet och alla 41 bildrutor. Länkarna i
  beskrivningen är kanalens betalgemenskap (ailabspro.io), sponsorn Upstash och ett nyhetsbrev; skillarna som visas
  finns bara i betalgemenskapen [TAL 12:11; BESKRIVNING], så inget repo fanns att läsa. Rörelse spelar ingen roll i
  videon: bildrutorna är stillbilder av terminaler, filer och diagram. Ägarens not: ingen
- Steg: 5 och 6 (granskningsloopen), 8 (ägarens dom och vad som lärs mellan byggen); arbetssättet runt dem
  (stoppvakten, `kontroller/gruppera.py`, backloggen)
- Jämfört med i dag: videon beskriver två slingor. **Slinga ett** är Karpathys: agenten ändrar en fil, en låst fil
  sätter poäng, en instruktionsfil styr varje omgång, och en ändring behålls bara om poängen stiger [TAL 01:04–01:38;
  SKÄRM 01:18 låst poängfil med poäng; SKÄRM 01:37 instruktionsfil]. Kanalens egen version: en skill skriver
  kontrollerna före bygget, människan godkänner dem [SKÄRM 05:20 "the human approves the checks"], ett program
  flyttar dem till en låst mapp som en nekaregel i Claude Codes inställningar skyddar [SKÄRM 05:57], de committas, och
  en färsk byggagent per funktion bygger tills kontrollerna passerar [SKÄRM 06:16, kontext 58 %]. Sak mot sak: (1)
  Låsta kontroller har vi starkare: `kor.sh` nekar Edit och Write i `kontroller/`, `kritik/`, `kunskap/`, `mall/`,
  `.claude/` och `LARDOMAR.md` (rad 55–57) och jämför dessutom filerna före och efter körningen, eftersom Bash kan gå
  förbi Edit-reglerna (rad 72–74, 81–86); videons skydd är bara nekaregeln, och körningen sker med alla behörigheter
  avstängda [SKÄRM 07:30]. (2) Kontroller före bygget: våra EARS-krav i briefen som granskaren prövar
  (`.claude/skills/bygg-sajt/SKILL.md` rad 130–132), provets grindar och byggstandarden; videons kontroller godkänns
  av en människa före bygget, vilket krockar med att våra byggen körs utan människa (rad 20). Lika i sak, olika av
  medvetet val. (3) Behåll bara det som blev bättre: `granska.py --jamfor` jämför bästa mot sista omgången och
  GRANSKNINGSLOGG.md är vår resultatfil per omgång (rad 263–268; `underlag/lulea-snickaren-aby/GRANSKNINGSLOGG.md`
  rad 5–8), mot videons resultatfil med behållen/ångrad, försök och kvarvarande fel per omgång [SKÄRM 09:40]. Lika.
  (4) Stoppvakten är vår slinga ett i mekanik: provet och granskningen körs av kroken själv tills de är gröna
  (`.claude/hooks/stoppvakt.py` rad 2–8). Lika eller starkare. **Slinga två** är videons egen idé: en färsk agent per
  funktion gör samma fel i varje funktion, eftersom instruktionerna är desamma [TAL 08:38–09:03]; därför läser en
  andra skill resultatfilen efter varje funktion, letar vanor som återkommer, och skriver om avsnittet "How to work"
  i instruktionsfilen, utan att få röra kontrollerna [TAL 09:03–09:40; SKÄRM 06:34 avsnittet "the coach rewrites this
  section"; SKÄRM 11:13 vana ur två funktioner blir version 2 av instruktionerna]. Hos oss är den slingan delad i två:
  ägaren dömer och domen blir en textändring (`LARDOMAR.md` rad 3–6; `bygg-sajt/SKILL.md` rad 363–367), och
  `kontroller/gruppera.py` grupperar efter var femte dom ägarens domar och granskarens blockerande fynd i kategorier
  och lägger den största som vilande backlogpost (`gruppera.py` rad 2–9, 50–60; `dashboard/server.py` rad 492).
  Skillnaden i sak: gruppera.py läser bara slutfilen `kunder/<slug>/granskning/GRANSKNING.json` (rad 43), alltså
  fynden som stod kvar när bygget godkändes. Det som granskaren fällde i omgång ett och bygget rättade syns aldrig,
  fast det är precis videons "vana": samma fel i varje bygge, rättat varje gång, aldrig i instruktionerna. Byggena
  visar mönstret: lulea-snickaren-abx fälldes i omgång ett för ett egenritat märke i stället för verksamhetens logga
  (`underlag/lulea-snickaren-abx/GRANSKNINGSLOGG.md` rad 5) och skillen själv konstaterar att tre byggen skrev var
  sitt Lighthouse-skript innan någon såg mönstret (`bygg-sajt/SKILL.md` rad 348–349). Omgångarna finns sparade med
  blockerande fynd i `kunder/*/granskning/runda-NN/GRANSKNING.json` (14 filer i dag). Här är videon smartare.
  Videons automatiska omskrivning av instruktionerna tar vi inte: ägaren har beslutat "Ingen agent som arbetar
  obevakat på systemet" (`BESLUT.md` rad 82), och vår form för det är backlogposten som ägaren släpper. (5) Färsk
  agent per funktion med liten kontext [SKÄRM 06:16]: vi kör en session per bygge med subagenter bara för
  femsekunders- och rubriktestet (`bygg-sajt/SKILL.md` rad 289–298); en sajt är ett sammanhängande stycke, inte en
  lista funktioner, och kontextdjupet mäts redan i en vilande post (B-20261002-mat-kontextdjupet-per-bygge). Inte
  bättre för oss. Litteraturen: build–measure–learn (Ries 2011) är vårt steg 8 (`kunskap/teoretisk-grund.md` rad 21,
  42); videons slinga två är samma princip körd mot varje omgång i stället för mot slutresultatet
- Skäl: det mesta i videon har vi redan som mekanik, ofta starkare (låsta kontroller med hashjämförelse, stoppvakt,
  bästa mot sista). Det som är nytt för oss är en liten sak med stor hävstång: vanor syns i omgångarna, inte i
  slutresultatet. Vår gruppering läser bara slutresultatet och missar därför just de fel som varje bygge gör och
  rättar om igen. Att låta gruppera.py läsa varje sparad omgång är en ändring i en funktion, ingen ny mekanik, och
  gör ägarens arbete mindre: mönstret kommer som en backlogpost i stället för att ägaren ska se det själv över fem
  domar. Källkritik: videon säljer en betalgemenskap och har en sponsor [SKÄRM 06:53–07:11; TAL 12:11]; siffrorna
  om Karpathys 700 experiment och Shopifys 19 % är återgivna i andra hand [TAL 01:38–02:11]; det egna beviset är
  terminalutskrifter ur kanalens egna appar [SKÄRM 11:50, 12:09], som visar att vanorna hittades men inte att
  nästa funktion blev bättre än den hade blivit utan. Det räcker inte för en metod i bygget, men förslaget här
  prövas gratis på data vi redan har. Videon innehåller inga instruktioner riktade till agenter
- Kostnad: inga tokens i byggsessionen. gruppera.py körs redan efter var femte dom; uppdraget får ett tiotal rader
  mer per bygge (fynden per omgång). Inga beroenden, inget underhåll utöver funktionen
- Säkerhet: ej tillämpligt (video, inget hämtat utöver transkript och bildrutor; inget kördes eller installerades)
- Förslag: `kontroller/gruppera.py`, funktionen `granskningsfynd()` (rad 40–47): läs utöver slutfilen varje
  `kunder/<slug>/granskning/runda-NN/GRANSKNING.json` och skriv varje blockerande fynd med omgångens nummer och om
  det var rättat i slutfilen; uppdragstexten (rad 52–55) får en mening om att ett fel som rättas inom bygget men
  återkommer i nästa bygge räknas som en kategori, inte som löst. Docstringen (rad 2–4) nämner omgångarna.
  Rökprovet ska sluta grönt, och `--torr` ska visa omgångsfynden för de befintliga byggena
- Utfall: gruppera.py läser varje omgångs blockerande fynd 2026-10-03, med omgång och om felet rättades före sista
  omgången.
- Backlog: B-20261002-gruppera-py-laser-granskarens-blockerande-fynd-p

### 2026-10-03 · AI LABS, "How To Use Claude Code To Build Amazing Sites With Opus 5.5" (YouTube DP7mgLUKN_U) · nej
- Källa: https://www.youtube.com/watch?v=DP7mgLUKN_U @ publicerad 2026-09-30 (AI LABS, 25:26, autogenererat engelskt
  transkript, sponsrad av CodeRabbit och med länk till kanalens betalgemenskap [BESKRIVNING]). Fjärde bedömningen av
  länken; de tre tidigare står i `REGISTER-arkiv-20261001.md` och räknas inte (gamla reglerna). Läst och sett: hela
  tidslinjen; 15 bildrutor ur den tätare serien från 2026-10-01 (83 rutor) vid resultaten efter varje steg, och 1 ur
  dagens körning (44 rutor; första försöket fick HTTP 403 från YouTube, andra gick). Repona förgranskade och lästa:
  nutlope/hallmark (senast pushad 2026-08-06, MIT, 29 428 stjärnor; `skills/hallmark/SKILL.md` 559 rader i sin
  helhet, `references/slop-test.md` grind 46–56) och oso95/scroll-world (senast pushad 2026-07-29, MIT, 9 644
  stjärnor; `skills/scroll-world/SKILL.md` 763 rader i sin helhet). Sidor sedda i 390 och 1440: usehallmark.com (första
  vyn och skrolläge 4) och aura.build (första vyn). Videons slutsajt forma-site-flame.vercel.app svarar fortfarande
  503 `DEPLOYMENT_PAUSED` [BILD forma desktop-forsta, mobil-forsta]; ailabspro.io, theroundup.so och CodeRabbit
  öppnades inte
- Steg: 1–3 (planläge och CLAUDE.md), 5 (Hallmark, design.md, scroll-world), 6 (CodeRabbit), lanseringen (GitHub och
  Vercel)
- Jämfört med i dag, steg för steg i videons sex stadier: (1) **Planläge.** Claude frågar om stack, sektioner, stil
  och innehåll [TAL 06:00–06:32]; sektionsfrågan är en meny med Hero, Portfolio, Services och About [SKÄRM 06:37], så
  skelettet väljs före innehållet. Vi: RESEARCH.md med "Bara de har" (`.claude/skills/bygg-sajt/SKILL.md` rad 90–92),
  diagnos med heuristisk utvärdering och kognitiv genomgång (rad 109–115), brief med toppuppgifter och EARS-krav
  (rad 125–132), innehåll före form (rad 164–172). Sämre. (2) **CLAUDE.md med affärskontext** så att avsikten
  överlever omtag [TAL 09:16–09:50]. Vi: VERKSAMHET.json och BRIEF.md per bygge (rad 80–85, 123–145), lästa i varje
  steg. Lika. (3) **Hallmark.** Kärnan är oförändrad sedan arkivposterna: ett av 21 katalogteman väljs tyst och
  roteras mellan byggen [REPO SKILL.md rad 38, 240, 251]; det nya som skillen själv kallar sin skillnad är
  strukturell variation via 21 makrostrukturer och en katalog av nav- och sidfotsarketyper, med regeln bort från
  "fyra spalter länkar + social rad" som AI-fingeravtryck [REPO rad 13, 290–294]. Vi: fyra riktningar härledda ur
  verksamheten med sidans form specificerad (bygg-sajt rad 200–212), UPPTAGNA-VAL.md med strukturmönstren ur
  ägarens domar, bland annat "sidfot i tre spalter (L1)" (`kontroller/upptagna_val.py` rad 40–45), och
  stilrapportens varningar för namngivna standardval (`kontroller/stil.mjs` rad 180–204). Hallmarks grind 46 (inga
  påhittade siffror) är bygg-sajt rad 20–21. Grind 49–51 och 55 (klickbar text på två rader, `minmax(0, 1fr)` för
  bildspår, `overflow-wrap` på rubriker, versala rubriker med radhöjd under 1) [REPO slop-test.md rad 164–182] saknar
  motsvarighet; vi mäter symptomet (inget spill 320–1920, `kunskap/bygge-referens.md` rad 10; byggstandarden 3.3),
  inte orsaken. Hallmarks självkritik på sex axlar före leverans [REPO rad 46] mot våra två oberoende granskare
  (bygg-sajt rad 255–262): litteraturen ger oberoende granskare (`kunskap/teoretisk-grund.md` rad 128–129).
  Resultatet i videon: benvit grund, grotesk och ett portföljfilter med sex kategorier åt en enmanspraktik [SKÄRM
  11:35]; usehallmark.com bär själv numrerade versala etiketter ("02 / EXAMPLES") [BILD usehallmark desktop-forsta]
  och visar ett kursivt betonat ord i rubriken ("look *made*, not generated") [BILD desktop-skroll-04], två saker
  skillen själv förbjuder [REPO rad 56, 450]. Ägarens betyg på "gjord för verksamheten" med vår metod är 5, 4 och 4
  (`LARDOMAR.md` rad 28, 53, 77). Lika eller sämre; grind 49 är en liten sak som är smartare, se förslaget. (4)
  **design.md från aura.build** låser färg, typsnitt och luft så att modellens standard inte smyger tillbaka [TAL
  11:44–12:35]. Vi: exakt specifikation i KONCEPT.md före kod (bygg-sajt rad 207–210), tokens som CSS-variabler
  (byggstandarden 3.1), stilrapporten mäter renderade typsnitt och färger i varje prov (`stil.mjs` rad 1–3),
  DESIGN.md som riktningsfil (`bygge-referens.md` rad 44–50). I videon var filen gjord för en annan produkt,
  "NeuroSync | Master Your Mind", och Claude noterade bytet och tillämpade den ändå [SKÄRM 13:41]; sidan blev vit med
  Inter och pillerfilter [SKÄRM 13:59]. aura.build är en mallbutik vars egen sida sätter Inter i h1 [BILD aura
  desktop-forsta; SIDA.md]. Krock med "Kopiera aldrig layout, palett eller typsnitt" (bygg-sajt rad 252). Sämre.
  (5) **GitHub, Vercel och CLI:erna** [TAL 14:13–18:01]: lanseringsfasen, `bygge-referens.md` rad 39–42 och
  `kunskap/lansering.md`. Lika; inget för demon. (6) **scroll-world.** AI-genererade stillbilder och videoklipp, N
  stillbilder plus 2N−1 klipp, en kedja med sex scener i 1080p omkring 27 USD [REPO SKILL.md rad 28, 49, 171], en
  skrubbmotor i JavaScript som bygger sin egen DOM [REPO rad 37–39], klipp om ungefär 8 MB vardera [REPO rad 534],
  konstriktning och kamera ur en meny ("Flat papercraft", "Fly through the world") [SKÄRM 20:36]. Vi: egna bilder
  eller en beställning (bygg-sajt rad 20–24, 76–79; L3 "hellre inga foton än stock", `LARDOMAR.md` rad 90),
  innehåll utan JS (byggstandarden 0 och 1.1, provets `utan-js`), högst 200 kB JS (3.7), LCP 2,5 s (4.1).
  Resultatet är dioramor och en påhittad arkitekt vid ritbordet [SKÄRM 21:12, 21:30, 25:07]. Krockar med fyra
  medvetna val. (7) **CodeRabbit** granskar pull requesten, 11 fynd [SKÄRM 23:19]; samma vy visar att PR:en ersatte
  hela sajten, 78 filer, "replaces the previous TypeScript project site". Vi committar på main (`CLAUDE.md`) och
  granskningen är provet och de två granskarna. Betaltjänst och sponsor. Inte för oss
- Skäl: videons egen fråga är om sajten slutar se AI-gjord ut [TAL 00:00], och bilderna svarar nej: första versionen
  krämvit med stockfoto av en soffa märkt som ett eget projekt [SKÄRM 07:49], efter Hallmark benvit grotesk med
  portföljfilter, efter design.md vit Inter ur en annan produkts system, och slutsajten krämvit serif med versal
  eyebrow och AI-genererade hus. Varje stadium ersätter det förra i stället för att bygga vidare, och slutsajten
  bärs av bilder som inte är verksamhetens. Sak för sak gör vi samma saker med mer av verksamheten i: upptäckt
  och brief i stället för en sektionsmeny, specifikation och mätning i stället för en nedladdad design.md, egna
  bilder eller beställning i stället för dioramor, två oberoende granskare i stället för självkritik. Det är inte
  längre bara text hos oss: tre dömda byggen fick 5, 4 och 4 på frågan om sajten är gjord för verksamheten, och
  ägaren höll med om nej för ui-ux-pro-max (`kunskap/KIRURG-OMDOMEN.md` rad 145–147), som bygger på samma
  katalogmekanism som Hallmark. Hallmarks katalog av sidfots- och navformer skulle kunna vidga byggarens
  ordförråd mot ägarens mall-lukt i L1–L3, men formen ska härledas ur verksamheten (bygg-sajt rad 200–201), och
  UPPTAGNA-VAL.md gör redan jobbet att namnge de former som gått igen. Källkritik: sponsor, betalgemenskap och
  egen betald design.md-planerare [TAL 12:35–13:09]; beviset för "ser inte AI-genererad ut" är berättarens omdöme
  om en fiktiv byrå [TAL 11:27]; slutsajten går inte att öppna. Videon innehåller inga instruktioner riktade till
  agenter
- Kostnad: inget tas in ur källan. Förgranskningens mått, om de hade tagits in: hallmark 66 tokens alltid, 16 568
  vid användning, 154 009 vid behov; scroll-world 232, 11 982 och 15 054, plus betal-CLI:er (monid, higgsfield) och
  videokostnad per bygge. Det egna förslaget är några rader i `stil.mjs` utan byggkostnad
- Säkerhet: förgranskningen MEDEL för båda repona, inget HÖG. hallmark: inga dolda tecken, ingen text riktad till
  agenter, inga behörigheter i frontmatter; rör-till-skal i `site/_tests/02-streampipe-cli/index.html` och
  miljöläsning i `site/examples/custom-05/script.js`, båda i exempelsajterna, inte i skillen. scroll-world: inga
  dolda tecken, ingen text riktad till agenter; `allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Skill`;
  nätanrop och miljöläsning i `references/scrub-engine.js` och `references/knockout.py`; skillen förutsätter
  betal-CLI:er med inloggning. Inget kördes eller installerades
- Förslag: inget ur källan. Eget förslag, inspirerat av Hallmarks grind 49: `kontroller/stil.mjs`, i `matPaSidan()`
  bredvid mätningen av små klickytor, räkna raderna i varje synlig länk och knapp i 390 px och varna med elementets
  text när de är fler än en, i samma form som varningarna på rad 201–204. Information, ingen grind. Ägaren pekade i
  A/B 2026-10-02 ut A:s menylänkar i två rader som det som gjorde första vyn sämre (`LARDOMAR.md` rad 102); skillen
  säger nu "menyn på en rad" (bygg-sajt rad 222) men inget mäter det, och ingen kontroll ser en knapptext eller
  brödsmula som bryts
- Utfall: stilrapporten varnar för klickbar text på två rader i 390 2026-10-03.
- Backlog: B-20261002-stilrapporten-varnar-nar-klickbar-text-menylank (eget förslag; ingen post för källan)

### 2026-10-03 · AI LABS, "Insane Jev Use Cases You Need To Use Right Now" (YouTube 2nc_QMuNp18) · nej
- Källa: https://www.youtube.com/watch?v=2nc_QMuNp18 @ publicerad 2026-09-28 (AI LABS, 12:37, 60 005 visningar,
  autogenererat engelskt transkript, sponsrad av Zapier och med länk till kanalens betalgemenskap [BESKRIVNING]).
  Andra bedömningen av länken; den första (2026-10-01) står i `REGISTER-arkiv-20261001.md` och räknas inte (gamla
  reglerna). Läst och sett: hela tidslinjen och alla 41 bildrutor. Nio är inspelningar av terminal, editor eller
  webbläsare, resten animerade illustrationer, sponsorklipp och en svart övergång. Repot i beskrivningen,
  tamaratran/fast-jev-compaction (MIT, 7 330 stjärnor, senast pushat 2026-09-18, klonen läst i sin helhet: README,
  `hooks/fast-jev.ts`, `hooks/README.md`, `src/compact.ts`, `.claude-plugin/plugin.json`). Övriga skills och krokar
  i videon ligger i betalgemenskapen [TAL 12:02] och syns bara som utsnitt i bild. ailabspro.io, theroundup.so och
  Zapier öppnades inte. Ägarens not: ingen
- Steg: inget av de åtta direkt; arbetssättet runt dem: körningens kontext (kor.sh), verktygslådan, granskningen
  (`kontroller/granska.py`), provets utforskning (steg 6) och stoppvakten
- Jämfört med i dag, fall för fall: (1) **Komprimering utan sammanfattning.** Pluginet byter Claude Codes
  sammanfattning mot en beskärning: varje verktygsanrop får två ja/nej-frågor till beslutsmodellen Jev, och det som
  behålls står ordagrant [REPO README rad 8–15, 39–51; `src/compact.ts` rad 56–66]. Argumentet är sakligt: en
  sammanfattning kan tappa en sökväg, ett exakt fel eller en regel [REPO README rad 10–12]. Vi: en session per bygge
  i opus[1m] (`kor.sh` rad 62) och ingen egen komprimering. Ingen av de fem körningsloggarna i `kunder/*/korning-*.jsonl`
  innehåller en komprimeringshändelse (ordet förekommer bara i kommandolistan), och kontextdjupet mäts av en vilande
  post (B-20261002-mat-kontextdjupet-per-bygge-i-a-b-posten-storsta). Problemet som pluginet löser är alltså inte
  påvisat hos oss. Tillståndet som skickas till Jev är hela samtalet med texter och verktygsindata ordagrant [REPO
  README rad 26–28]; i ett bygge är det verksamhetens underlag, som `CLAUDE.md` håller utanför git som privat. Kräver
  nyckel hos TypeSafe, där registreringen är pausad [SKÄRM 02:12], eller via OpenRouter eller Vercel AI Gateway
  [TAL 02:10–02:44], och Claude Codes funktionskrokar i förhandsläge, med en typreferens på 11 268 rader som ska
  genereras om efter varje uppgradering [REPO `hooks/README.md` rad 26–28, 79–82]. (2) **Jev som domare över att
  varje regel har ett prov** [SKÄRM 05:32 PostToolUse-krok efter ändring i rättighetsfiler]. Vi: byggstandardens
  kolumn "Prövas av" namnger kontrollen för varje punkt (`kunskap/byggstandard.md` rad 10–12), och granskaren prövar
  varje EARS-krav i briefen (`kritik/GRANSKARE.md` rad 58; `granska.py` rad 218 ger BRIEF.md till granskaren). Lika.
  (3) **Skillväljare** vid varje prompt [SKÄRM 06:09 UserPromptSubmit; SKÄRM 06:45 säkerheter 0,93–0,98,
  animation]. Vi: fem skills i `.claude/skills/`, och bygget väljer ur verktygslådan på beskrivningen (`bygg-sajt`
  rad 44–46). Kroken fyrar vid prompten; vårt bygge har en enda prompt (`kor.sh` rad 27–34) och väljer skills under
  400 turer, så kroken träffar aldrig valet. Inte tillämpligt. (4) **Filsökning med rankning** [SKÄRM 08:53: 35
  filer på 1,6 s, topp två 0,40 och 0,39]. Ett bygge är ett litet Astro-projekt med ett tiotal sidor; sökning är inte
  en kostnad hos oss, och de två toppfilerna skiljer sig med en hundradel. Inte för oss. (5) **Billig gallring före
  granskningen**: sju ja/nej-frågor, små ändringar får "one quick round" [TAL 09:20; SKÄRM 09:48]. Vi: två
  oberoende granskare dömer alltid hela sajten (`granska.py` rad 2–6), samma bygge granskas aldrig två gånger
  (hashjämförelse, rad 592–597) och körningen har ett tak om fem omgångar (rad 49, 599–603). Vår gallring är
  deterministisk (ändrades bygget eller inte); videons byter granskningsdjup mot tid, och ägaren har satt kvalitet
  före tokens (kirurgens siktfrågor, 2026-10-02). Litteraturen: en ensam granskare hittar omkring 35 procent av
  problemen, flera oberoende omkring 75 (`kunskap/teoretisk-grund.md` rad 128–129); en snabbrunda går åt fel håll.
  Sämre. (6) **Webbläsartest där Jev väljer nästa klick mot ett mål** [SKÄRM 10:43 "Change Priya's role",
  numrerade länkar; SKÄRM 11:01 rollmatris, animation; SKÄRM 12:14 skillen kör Playwright per roll]. Vi:
  `kontroller/webblasare/utforska.mjs` väljer själv vägar, provar formulär och felvägar utan att skicka (rad 2–5;
  `prova.py` rad 374–384), och granskaren gör en kognitiv genomgång av den primära handlingen steg för steg
  (`GRANSKARE.md` rad 55–58). Videons mål är rollbaserad åtkomst i en app; våra sajter är statiska med ett formulär.
  Lika för vårt behov. (7) **Regelkrok som blockerar en ändring när Jev är minst 80 procent säker** [TAL 11:30;
  SKÄRM 11:37 rules.md per mapp]. Vi: deterministiska nekanden av Edit och Write i skyddade mappar och
  hashjämförelse före och efter (`kor.sh` rad 55–57, 72–74, 81), stoppvakten som kör prov och granskning innan
  avslutet släpps (`.claude/hooks/stoppvakt.py` rad 2–8), och copykontrollen som rapport, inte grind (`BESLUT.md` rad
  57). En sannolikhetsgrind på innehållsregler krockar med det valet; på filskydd är vårt starkare
- Skäl: videons löfte är att agenten blir "way faster and cheaper to run" [TAL 00:00], och sex av sju fall är
  tids- och kostnadsverktyg där vi antingen inte har kostnaden (sökning, skillval, komprimering) eller har valt bort
  att byta kvalitet mot tid (granskningen). Det enda fallet med ett kvalitetsargument, beskärning i stället för
  sammanfattning, löser ett problem som inte är påvisat i något av våra fem byggen, och skulle skicka verksamhetens
  privata underlag till en tredje part genom en förhandskrok som kan ändras med varje Claude Code-version. Varje
  fall är ny mekanik med en extern nyckel, mot "Inga nya mekaniker" och "Ingen agent som arbetar obevakat på
  systemet" (`BESLUT.md` rad 81–82). Källkritik: det enda inspelade komprimeringsfallet föll tillbaka till den
  vanliga sammanfattningen, "below 25% minimum: 0% reduction" [SKÄRM 04:38], så "less than a second" [TAL 04:23]
  syns aldrig; snabbheten 0,18 s mot 2,40 s [SKÄRM 00:02], säkerheterna [SKÄRM 06:45] och rollmatrisen [SKÄRM 11:01]
  är animationer; den enda riktiga rankningen skiljer topp två med en hundradel [SKÄRM 08:53]. Inspelningarna körs med
  alla behörigheter avstängda [SKÄRM 04:38, 08:53]. Bildrutan vid 00:38 visar en spelare på 18:05 med andra
  kapiteltider, så materialet är klippt ur en längre version. Videon säljer betalgemenskapen [TAL 12:02] och Zapier
  [SKÄRM 07:04–07:40]. Repots egen begränsning: "a probability is not a proof that a result is safe to delete"
  [REPO README rad 123–124]. Videon innehåller inga instruktioner riktade till agenter
- Kostnad: inget tas in. Hade det tagits in: Jev 0,042 USD per miljon tokens via gateway [SKÄRM 01:53], en nyckel
  till i miljön, funktionskrokar i förhandsläge och underhåll av en typreferens per Claude Code-version
- Säkerhet: förgranskningen MEDEL för fast-jev-compaction: inga dolda tecken, inga behörigheter i frontmatter, inga
  hookar i konfiguration (pluginets krok registreras i `hooks/hooks.json` som modul, inte som kommando); 13 skript med
  miljöläsning, nätanrop i `hooks/fast-jev.ts` och i typreferensen. Det enda fyndet "riktad till agenter" är en
  dokumentationskommentar i `types/claude-code.d.ts` rad 10397 ("run this command in the background"), inget till
  oss. Krokens återfall till den inbyggda sammanfattningen vid fel är korrekt byggt (`hooks/fast-jev.ts` rad
  263–290). Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd. Visar den vilande kontextdjupsmätningen att byggena komprimerar och att granskarens betyg
  faller efter det, kan beskärning i stället för sammanfattning prövas som A/B, med Jev eller med egen regel, utan
  att underlaget lämnar maskinen
- Backlog: ingen

### 2026-10-03 · AI LABS, "Github #1 Trending Skill's Author Just Fixed Claude's Design Problem" (YouTube Ow_z94c3wKk) + Nutlope/inspo · prova A/B
- Källa: https://www.youtube.com/watch?v=Ow_z94c3wKk @ publicerad 2026-09-18 (AI LABS, 12:35, 47 637 visningar,
  autogenererat engelskt transkript, sponsrad av Manifold/Monid [TAL 06:05–06:58] och med länk till kanalens
  betalgemenskap [TAL 12:02]). Läst och sett: hela tidslinjen och alla 41 bildrutor; ungefär tolv är inspelningar av
  terminal, webbläsare eller GitHub, resten animerade illustrationer, sponsorklipp och en svart övergång [SKÄRM
  09:28]. Repot i beskrivningen: Nutlope/inspo @ 647c3b1 (klon; senast pushat 2026-10-01T22:31Z), MIT med copyright
  Together AI, 822 stjärnor, inte arkiverat. Förgranskat. Läst: README, `apps/mcp/README.md`, `SEEDING.md`,
  `apps/mcp/src/tools.ts` rad 125–190, 1596–1665 och 1717–1747 (vägledningstexterna, recommend-svaret och
  serverinstruktionerna), `packages/taxonomy/src/index.ts` rad 36–89 (branschlistan),
  `apps/mcp/bench/results/2026-09-10-agent-usage.md` (författarnas egen mätning av 30 byggen), README:s med/utan-bilder
  och tre av exempelsajternas förhandsbilder (`apps/web/public/examples/{camera-repair,chalkline-gym,city-library}/thumb.jpg`).
  Sajten inspomcp.dev sedd i 390 och 1440 (första vyn och skrolläge 4). ui-skills.com, ailabspro.io, theroundup.so och
  Monid öppnades inte. Ägarens not: ingen
- Steg: 3 (referenserna, rollen hantverk), 5.1 (riktning) och 5.5 (JAMFORELSE.md); runt stegen: `kor.sh`
  (anslutningar i bygget) och stilrapporten
- Jämfört med i dag: (1) **Referensjakten.** Bygget söker själv (WebSearch, gallerier som sökingångar), öppnar varje
  vald referens i 390 och 1440 och skriver REFERENSER.md (`.claude/skills/bygg-sajt/SKILL.md` rad 150–162;
  `kunskap/referensjakt.md` rad 13–27, 29–32). Inspo är ett arkiv om 832 riktiga sajter och 2 320 fångade sidor,
  varje sajt i desktop och mobil, taggad med bransch, sidform och ljust/mörkt, sökbart med en brief: `recommend`
  ger fem exempel med samma sidform, ett bevispaket över de matchade sajterna och tre miniatyrer direkt i svaret
  [REPO README rad 22–26; `apps/mcp/README.md` rad 16–17; TAL 04:39–05:13; SKÄRM 05:13]. För hantverksrollen
  (komposition, typografi, mobilversion av samma sida) är det smartare än vår jakt: färre steg och mobilparet finns
  redan. För branschrollen är det sämre: branschlistan har 24 värden och ingen för hantverkare, lokala tjänster eller
  bygg [REPO `packages/taxonomy/src/index.ts` rad 36–61]; arkivets första sida är SaaS, startups och byråer [BILD
  inspomcp desktop-forsta]; de referenser ägaren saknade i L1–L3 var svenska hantverkarkvitton, en tidsaxel på mobil
  och resultat med få bilder (`LARDOMAR.md` rad 37, 62, 86), som inget här täcker. Videon visar själv två felträffar på
  bransch [TAL 11:10–11:35; SKÄRM 11:17] och fångster täckta av kakrutor [TAL 11:35–11:59]. (2) **DESIGN.md per sajt**
  med palett, typsnitt, typskala och avstånd ur DOM:en [TAL 03:50–04:19; SKÄRM 04:01, 04:19]. Vår `kontroller/sida.mjs`
  och inspektionen beräknar samma designfakta för varje sida vi öppnar (SIDA.md: typsnitt, storlekar, färger). Lika.
  Det `recommend` också ger, `paletteSuggestion` och färdiga JSX-komponenter via `get_reference_jsx` [REPO
  `tools.ts` rad 1644–1645; README rad 23], krockar med "Kopiera aldrig layout, palett eller typsnitt" (bygg-sajt rad
  252) och tas inte med. (3) **Mätta kompositionsregler.** Avstånd mellan sektioner 80–160 px, medianens största steg
  96 px, mätt över 671 sajter, och en första vy som ryms i 1280×800 [REPO `tools.ts` rad 132–151]. Vi: stilrapporten
  mäter att nästa sektion skymtar (`kontroller/stil.mjs` rad 69, 207) och två vilande poster om rytmen (impeccables
  "enformig luft", B-20261002-stilrapporten-mater-fem-renderade-monster-ur-imp; Every Layout,
  B-20261002-skriv-tre-layoutregler-i-bygge-referens-md-layou). Inspos tal är belagda och kan bli trösklarna i den
  första posten; regeln om första vyn är skriven för desktop, medan vår första vy är 390 px (bygg-sajt rad 221–224).
  (4) **Mekaniken.** En MCP-server i byggsessionen. `kor.sh` rad 61–62 kör `--strict-mcp-config` utan `--mcp-config`
  just för att inga anslutningar ska laddas i ett bygge: ett medvetet val som en A/B-arm måste göra ett uttryckligt
  undantag från. Den hostade ändpunkten kräver ingen nyckel och inget konto, är läsande, har hastighetsgräns per IP
  och hämtar bara källsidor server-side med SSRF-skydd [REPO `apps/mcp/README.md` rad 206–211]; ingen kod behöver
  köras lokalt. Serverinstruktionerna läses in i varje session som har den ansluten [REPO `tools.ts` rad
  1717–1747]. Kontextkostnad enligt författarnas egen mätning: 10,8 anrop och omkring 37 000 tokens svar per bygge
  före bantningen, uppskattat 12 000–14 000 efter; ett `recommend` med miniatyrer omkring 41 KB [REPO
  `bench/results/2026-09-10-agent-usage.md` rad 11–16, 97–99; `apps/mcp/README.md` rad 145–147]
- Skäl: det här är den första källan sedan nystarten som för in en metod vi saknar snarare än en regel vi redan har:
  en kuraterad samling riktiga sajter med mobil och desktop parvis, sökbar med briefen, och normer mätta ur arkivet i
  stället för ur tycke. Teorin bakom våra referenser är jämförelse med öppnade exempel i jämförbara vyer
  (`kunskap/referenser-professionella.md` rad 40–45), och det är precis det arkivet gör billigare. Det är gratis,
  MIT och läsande. Mot det står tre saker som bara ett bygge kan väga: arkivet är inte vår marknad; agentens egna
  exempelsajter, byggda av Fable 5.1 med Inspo som enda verktyg [REPO bench rad 3–6], delar ett och samma mönster i
  första vyn, märkesrad över rubriken, ett färgat eller kursivt ord i h1, stycke, två knappar, tre siffror med etikett,
  bild till höger [BILD camera-repair, chalkline-gym, city-library thumb.jpg], alltså ett eget fingeravtryck av det
  slag ägaren kallade mall i L1–L3; och README:s med/utan-par visar två varianter av samma delade första vy [BILD
  docs/img/with-inspo.jpg, without-inspo.jpg]. Videons resultat FORMWORK är kompetent, delad första vy, monoetiketter,
  nedräkning, och fungerar i 402 px [SKÄRM 10:04, 10:19, 10:59], men det är en fiktiv butik med nio platshållarfoton
  som agenten själv tonade ihop för att de hade "fem olika färgtemperaturer" [SKÄRM 09:10, 09:46]; beviset för "ser
  inte genererad ut" är berättarens omdöme [TAL 09:14–09:28]. Källkritik: sponsor och betalgemenskap; videons
  berättare säger att Inspo är gjort av Hallmarks upphovsperson [TAL 00:00–00:31], vilket stämmer med repots ägare,
  och att andra sådana verktyg kostar [TAL 00:31]. Videon innehåller inga instruktioner riktade till agenter; repots
  serverinstruktioner är riktade till agenter per konstruktion och säger bland annat att projektets egna konventioner
  vinner vid konflikt [REPO `tools.ts` rad 1731–1732]
- Kostnad: hostad ändpunkt, inget installerat; i A-armen 12 000–41 000 tokens per bygge i verktygssvar enligt
  källans egen mätning, plus miniatyrerna i kontexten; underhåll: en JSON-fil och ett stycke i skillen; beroende av
  en tredje parts drift under bygget (faller tjänsten är armen bara ett vanligt bygge)
- Säkerhet: förgranskningen MEDEL, inga dolda tecken, ingen text riktad till agenter i md-filerna, inga behörigheter i
  frontmatter, inga hookar. 163 skript: eval/exec i `apps/mcp/src/tools.ts`, `install.ts`, `smoke.ts` och
  `format.ts`; nätanrop i `format.ts` och `inline-images.ts`; `install.ts` skriver utanför repot (det är
  installationskommandot, som vi inte använder); rör-till-skal i exempelsajten
  `apps/web/public/examples/ferrite-terminal/page.html`, inte i servern. Inget kördes eller installerades; den
  hostade ändpunkten anropades inte
- Förslag: A/B på samma verksamhet. **A-armen:** `kor.sh` rad 62 får, när miljövariabeln `NWP_MCP_CONFIG` är satt,
  `--mcp-config "$NWP_MCP_CONFIG"` bredvid `--strict-mcp-config`; filen `kontroller/mcp/inspo.json` pekar på den
  hostade ändpunkten `https://inspomcp.dev/api/mcp` (HTTP-transport, ingen npx, ingen lokal kod). I
  `.claude/skills/bygg-sajt/SKILL.md` steg 3, efter rad 153 ("Öppna varje vald referens på riktigt"), ett stycke:
  är Inspo anslutet används `recommend`, `search_screens` och `get_screen` för hantverksrollen och mobilparen som
  sökingång; varje vald referens öppnas ändå på riktigt med inspektera.mjs och skrivs i REFERENSER.md med källa
  "Inspo"; `get_reference_jsx`, `paletteSuggestion` och `heroGuidance` används aldrig (bygg-sajt rad 252 och
  mobilen först gäller). **B-armen:** som i dag. Två körningar per arm på samma verksamhet, blind parvis jämförelse i
  dashboarden med ombytt ordning, en annan modell än byggaren som domare, oenighet räknas som oavgjort; bredvid
  kvaliteten redovisas tokens och minuter ur `korning-*.jsonl` och antalet Inspo-anrop. Avgörs av ägarens val och
  JAMFORELSE.md under 1 och 4. Eget förslag ur källan utan egen post: de mätta talen (80–160 px mellan sektioner,
  median 96) blir trösklarna i den vilande impeccable-posten när den genomförs
- Utfall: reglaget NWP_MCP_CONFIG och variabeln inspo i ab.py 2026-10-03 (av som standard, tre läsande verktyg);
  A/B:n väntar på ägaren.
- Backlog: B-20261002-a-b-inspo-mcp-hostad-andpunkt-som-sokingang-for

### 2026-10-03 · AI LABS, "Insane Claude Design Skills You Need To Actually Build Beautiful Sites" (YouTube Ysr7oNDajJI) + jakubkrehel/skills · ta in
- Källa: https://www.youtube.com/watch?v=Ysr7oNDajJI @ publicerad 2026-08-24 (AI LABS, 12:55, 277 796 visningar,
  autogenererat engelskt transkript, sponsrad av Make/Maia [TAL 06:29–07:27; SKÄRM 06:55, 07:14] och med länk till
  kanalens betalgemenskap [TAL 11:57–12:31; SKÄRM 12:13]). Läst och sett: hela tidslinjen och alla 41 bildrutor;
  ungefär 25 är inspelningar av Claude Design, editor, GitHub, webbläsare eller sponsorn, resten animerade
  illustrationer. Sju repon ur beskrivningen, alla MIT, alla klonade grunt, förgranskade och lästa (commit ur
  `.git/shallow`; `git log` nekades av behörigheten): emilkowalski/skills @ e8a175d (pushad 2026-10-02, 42 859
  stjärnor): `skills/animate/SKILL.md` helt, `emil-design-eng/SKILL.md` rad 1–60 och de flaggade raderna;
  ConardLi/garden-skills @ aaf9a82 (2026-07-12, 12 716): `skills/web-design-engineer/SKILL.md` helt (493 rader),
  `references/critique-guide.md` rad 1–80, `style-recipes/INDEX.md` rad 1–45; elayadesign/ai-design-skills @ 1c1e97c
  (2026-07-29, 2 345): `skills/landing-page-design/SKILL.md` helt (404 rader); MengTo/Skills @ d5bd3a7 (2026-10-01,
  6 574): `agent-skills/web-design/build-awwwards-quality-sites/SKILL.md`, `ui/no-ai-design-slop/SKILL.md` och
  `ui/audit-ai-design-slop/SKILL.md` helt, de två flaggade raderna; jakubkrehel/skills @ 267330e (2026-08-29,
  7 426): README, AGENTS.md, CLAUDE.md, LICENSE, åtta av elva SKILL.md (inte explain-interface, break, variant),
  `better-layout/grouping-and-alignment.md` och `spacing-and-adaptivity.md` helt; codeswithroh/tastemaker @ e39b4bf
  (2026-09-29, 431): `skills/tastemaker/SKILL.md` helt (250 rader); Owl-Listener/designer-skills @ 9a6930c
  (2026-09-05, 2 820): `ui-design/skills/law-of-proximity/SKILL.md` och
  `visual-critique/skills/critique-visual-hierarchy/SKILL.md` helt. ailabspro.io, theroundup.so och Make öppnades
  inte. Ägarens not: ingen
- Steg: 5 (5.1 riktning, 5.3 bygg, 5.5 Titta och JAMFORELSE.md, 5.6 granskning); runt stegen: verktygslådan
  (`.claude/skills/bygg-sajt/SKILL.md` rad 44–46)
- Jämfört med i dag, källa för källa: (1) **Emil Kowalski.** Videons två mest använda är emil-design-eng och
  animate [TAL 01:35–02:09; SKÄRM 02:15]. emil-design-eng finns redan hos oss, `kunskap/externa/
  emil-emil-design-eng-SKILL.md` (REGISTER rad 17), läses i steg 5 (bygg-sajt rad 192), och de första 60 raderna
  är ordagrant lika repots nuvarande fil [REPO skills/emil-design-eng/SKILL.md rad 1–60]. animate är en
  byggsekvens för UI-rörelse: ska det alls animeras (frekvenstabell), vilket syfte, vilket verktyg, bara transform
  och opacity, ease-out, UI under 300 ms, reduced motion och hover-grind, och en lista "Never ship" [REPO
  skills/animate/SKILL.md rad 39–50, 85–86, 104–110, 132, 150–169, 175–193]. Vi: ingen JavaScript som inte behövs
  (bygg-sajt rad 217), 0 kB JS i alla tre dömda byggen (`LARDOMAR.md` rad 31, 56, 87), dämpad rörelse i mallen
  (`mall/astro/src/layouts/Bas.astro` rad 47–50; byggstandarden 3.5, rad 50), rörelse enligt briefens motion-nivå
  (`kunskap/bygge-referens.md` rad 23). Ingen dom har pekat på rörelse. Videons eget resultat: efter Animate på
  restaurangsidan säger berättaren själv att det "isn't that different from what Claude normally produces" [TAL
  02:42–03:14]; det som syns är en krämvit grotesksida med Menu, Visit och Reserve [SKÄRM 02:34, 02:52]. Lika för
  vårt behov; animate registreras, tas inte in. (2) **garden-skills web-design-engineer.** Sätter agenten som
  "top-tier design engineer" med ribban "stunning" och Dribbble/Behance-nivå [REPO SKILL.md rad 8–10, 461; SKÄRM
  04:26], tre stoppunkter som väntar på användarens bekräftelse [rad 148, 160, 166], 25 stilrecept knutna till
  namngivna varumärken (Apple, Linear, Aesop, MUJI) vars palett, typografi och avstånd klistras in i
  designsystemet [rad 68, 146; references/style-recipes/INDEX.md rad 3, 28–30; SKÄRM 04:44], React via CDN och en
  Tweaks-panel [rad 236–246, 410–419], och en självkritik i fem dimensioner med poäng [rad 176–186;
  critique-guide.md rad 9–80]. Vi: ingen människa svarar under körningen (bygg-sajt rad 20), riktning ur
  verksamheten och "Kopiera aldrig layout, palett eller typsnitt" (rad 200–201, 252;
  `kunskap/referenser-professionella.md` rad 61), statisk Astro utan JS, två oberoende granskare i stället för
  självkritik (rad 255–262; `kunskap/teoretisk-grund.md` rad 128). Dess anti-klichétabell och placeholder-regel
  [rad 283–317] är i sak anthropic-frontend-design hos oss. Sämre: receptbiblioteket är samma katalogmekanism som
  ui-ux-pro-max, som ägaren höll med om nej för (`kunskap/KIRURG-OMDOMEN.md` rad 145–147). (3) **elayadesign
  landing-page-design.** En fil med hårda regler: bara Geist, Manrope, Geist Mono eller Poppins, ett typsnitt per
  sajt, aldrig kursiv [REPO rad 154–160]; Tailwinds typskala och en avståndstabell [rad 170–219]; gradient på
  rubriktexten i hero [rad 249–252]; glas-pillernav, 700 ms-övergångar, "Elements never appear statically on load",
  800 ms blur-fade [rad 269–295]; en obligatorisk "tagline reveal"-sektion där orden tänds ett i taget vid skroll
  [rad 341–357]; strukturen trial, demo, logotyper, riskvändning och FAQ med 6–12 frågor [rad 54–70, 97]; cookie
  consent "where the jurisdiction requires it" [rad 334]. Vi: typsnitt ur verksamheten med UPPTAGNA-VAL (bygg-sajt
  rad 195–198), innehåll utan JS (byggstandarden 1.1), ingen JS som inte behövs, kakfritt (bygge-referens rad 37).
  Videons resultat är en SaaS-formad växtbutik: versal eyebrow "GROWN IN HUDSON, NY", två knappar och raden
  "11,428 boxes shipped since 2019. 98.6%" med fyra avatarcirklar [SKÄRM 06:18], samma delade första vy som
  Inspo-posten ovan pekade ut. För en hantverkare i Luleå går varje regel åt fel håll. Sämre. (4) **MengTo/Skills.**
  167 skills, de flesta 3D, WebGL, GSAP, spel och Codex-arbetsflöden (förgranskningens tabell).
  build-awwwards-quality-sites kräver GSAP som primärt system, exakt en mjukskrollmotor (Lenis eller Locomotive),
  genererad hero-bild, Three.js "med syfte" och foton på alla avatarer [REPO SKILL.md rad 20–22, 28–29, 35–36].
  Krockar med 0 kB JS, högst 200 kB JS (byggstandarden 3.7) och egna bilder eller beställning (bygg-sajt rad 75–79;
  L3 "hellre inga foton än stock"). Videons resultat: en svart modesida "Nocturne" [SKÄRM 08:28].
  no-ai-design-slop och audit-ai-design-slop är däremot sakliga: slop är "a choice made by reflex rather than for
  the product", borttagningsprovet (namnge, säg jobbet, ta bort mentalt), ingen gissning om AI och ingen
  smakpoäng [REPO ui/no-ai-design-slop/SKILL.md rad 10–22, 89–95, 118; audit-ai-design-slop rad 12–17, 88–98]. Vi:
  regeln mot slop som text, granskarens originalitetskriterium med AI-mönstren uppräknade (`kritik/GRANSKARE.md`
  rad 84–91, "dekor utan funktion" rad 87), "blir sidan bättre av att stryka en tredjedel av texten, stryk"
  (bygg-sajt rad 253–254), och impeccables fem mätningar vilande. Lika i sak. Nej till samlingen. (5)
  **jakubkrehel/skills.** Elva skills, bara text, inga skript, LÅG. Sju domänskills med regler i exakta värden och
  ett Före/Efter/Varför-format, och fyra användaranropade verb [REPO README.md rad 13–23; AGENTS.md rad 45–52].
  better-layout: gruppera med luft före linjer, avståndet mellan grupper minst dubbelt mot inom (8 px inom, 16 px
  och mer mellan), kontroller skilda från innehåll, delade kanter med ett indragssteg, 12 px mellan kantade
  kontroller och 24 runt kantlösa, knappar indragna 16 px från kanten på mobil, innehåll blöder men kontroller
  flyter innanför marginal och safe-area, brytpunkter där innehållet slutar få plats, inga fasta bredder på text
  [REPO skills/better-layout/SKILL.md rad 14–56; grouping-and-alignment.md rad 13, 51–54;
  spacing-and-adaptivity.md rad 9–15, 36–55, 117–123]. better-typography: rubriknivåer i fallande steg, radhöjd
  per roll (1,1 rubrik, 1,5–1,6 brödtext, minst 1,4 vid tre rader), spärrning efter storlek, radlängd 60–75, fyra
  wrap-deklarationer, understrykning ur typsnittets mått, 16 px i fält på mobil [REPO rad 44–71, 93–106].
  better-colors: ramper med en roll per steg, primitiv mot semantisk token, en färg en betydelse inom 15°, en fylld
  handling per vy, mät det renderade paret och ändra inte färgen [REPO rad 20–61]. better-accessibility, better-ui
  (koncentrisk radie, optisk justering, scale 0.96 vid tryck, ikonstreck efter textvikt, rörelse aldrig enda
  återkoppling) [REPO rad 18–24, 54–56, 74–86] och better-writing (verb först i knappar, länktext som bär utanför
  sammanhanget, fel som säger hur, placeholder aldrig etikett) [REPO rad 44–57, 69–99]. better-interface
  samordnar: skop först, domänskills som sanningskälla i ordning, belägg med fil och rad, HIGH-utlösare på sikt,
  billigaste rättningen först (ta bort, plattformen, återanvänd, rätta värdet, lägg till), högst 15 fynd, aldrig
  Approve för det som inte inspekterats [REPO rad 14–18, 46–109]. Vi: dimension 4 är en fråga utan regel
  (`kunskap/referenser-professionella.md` rad 24–25), teoretisk-grund namnger Gestaltlagarna, CRAP, Fitts och Hick
  som princip (rad 62–63) utan att någon fil gör dem till byggregler, bygge-referens har inga avståndsregler (rad
  7–24), stil.mjs mäter träffytor, radlängd, radhöjd och kortmönster (rad 2, 73–74, 229) men ingen gruppering, och
  granskarens hantverkskriterium nämner luft utan mått (`kritik/GRANSKARE.md` rad 92–94). Ägaren satte "Luft och
  hierarki: Okej" i alla tre domarna medan de övriga dimensionerna fick Bra (`LARDOMAR.md` rad 35, 60, 84). Två
  vilande poster angriper samma dimension med mätning efteråt (impeccables fem mönster,
  B-20261002-stilrapporten-mater-fem-renderade-monster-ur-imp) och tre principer (Every Layout,
  B-20261002-skriv-tre-layoutregler-i-bygge-referens-md-layou); ingen av dem ger byggaren regler med värden att
  bygga efter i steg 5.3. Videon visar skillen göra just det: en tabell Location, Before, After, Why där ett
  datumfält i bokningsflödet behöver 113 px men får 99 på 360 px och 79 på 320 [SKÄRM 10:02; TAL 09:45–10:02].
  Bättre och smartare: närhetslagen ur litteraturen som byggregel med tröskel, i den dimension som bevisligen är
  svagast. Krockar: better-typography säger 60–75 tecken mot våra 45–75 (referenser-professionella rad 20–21),
  better-ui:s Motion-recept gäller inte utan JS, better-colors får inte bli nya paletter (bygg-sajt rad 252),
  better-writing:s regler om "we" gäller engelska; alla löses med avsnittet överst i kopian som för humanizer.
  interface-review kräver git-diff (`kunder/` ligger utanför git) och variant och break skriver kastbara sidor: tas
  inte med. (6) **tastemaker.** En harness om 16 080 tokens vid användning och 124 120 vid behov, 33 skript:
  hämtar stockfoton från Openverse automatiskt ("every section that needs a photo has a real photo"),
  illustrationer ur ett lokalt unDraw-bibliotek, ikoner ur Iconify och logotypväggar [REPO
  skills/tastemaker/SKILL.md rad 111–132], "A finished page with zero motion is a skipped step" och GSAP i varje
  bygge [rad 133, 146–150], palett genererad per stämning med skript [rad 92], makrostruktur roterad mot
  projektminne i `~/.tastemaker/` utanför repot [rad 96–106, 164], Inspo-MCP som förstahandskälla [rad 69]. Krockar
  med egna bilder eller beställning (bygg-sajt rad 20–24, 75–79; L3), 0 kB JS, riktning ur verksamheten, och
  skript som skriver utanför repot. Det sakliga, pixelextraktion ur en referens i stället för ordbeskrivning [rad
  17, 91], används hos oss aldrig för att kopiera (rad 252), och sida.mjs och inspektionen ger redan designfakta
  för varje öppnad referens. Videons resultat är en Japanresesida med ett kimonofoto som ser ut som stock [SKÄRM
  11:17]. Nej; Inspo har sin egen A/B-post. (7) **designer-skills.** 111 mikroskills om 200–1 500 tokens var:
  processmallar (persona, journey map, sprintplan, handoff), designlagar (Fitts, Hick, Miller, Gestalt) och sju
  kritikskills. Videons `screen-critique` och `perception-laws` [SKÄRM 11:35, 11:54] finns inte i repot under de
  namnen (sökt); närmast är visual-critique och ui-design/law-of-*. law-of-proximity säger samma sak som
  better-layout men utan värde, "there is no fixed pixel value" [REPO ui-design/skills/law-of-proximity/SKILL.md
  rad 17]; critique-visual-hierarchy frågar efter ingångspunkt, ögonväg, vikt (minst 1,5× mellan nivåer) och
  betoning [REPO rad 10–29]. Vi: teoretisk-grund rad 62–63 namnger lagarna, granskaren kör kognitiv genomgång och
  heuristisk utvärdering (`GRANSKARE.md` rad 55–63). Videons resultat efter perception-laws: "EVERY possible
  FUTURE, ALPHABETISED." i versal serif med ett kursivt betonat ord [SKÄRM 11:54], det AI-mönster Hallmark-posten
  pekade ut (rad 2714–2715). Lika eller sämre; nej
- Skäl: videons tes är att skills ska styra modellen bort från dess eget mönster [TAL 00:00–00:32], men fem av sju
  källor byter ett mönster mot ett annat: receptbibliotek med lånade paletter, obligatoriska skrollanimationer,
  GSAP och genererade bilder, stockfoton hämtade automatiskt, och resultaten i bild är krämvit grotesk, mörkgrön
  serif med bestick, svart mode och versal serif med kursivt ord [SKÄRM 02:34, 03:30, 08:28, 11:54], alla för
  fiktiva verksamheter. Det krockar med verksamhetens egna bilder och ord, 0 kB JS och riktning ur verksamheten,
  och ägaren har sagt nej till samma katalogmekanism förut. Emils design-eng har vi redan. Jakub Krehels sju
  domänskills är något annat: ren text utan skript, regler med exakta värden och krav på belägg, och better-layout
  gör Gestaltlagen om närhet, som vår litteratur namnger men ingen fil omsätter, till en byggregel i den enda
  dimension ägaren satt Okej på tre gånger. Det ger bygget en förmåga vi saknar utan krock, och går in i
  verktygslådan. Källkritik: sponsor och betalgemenskap; beviset för varje skill är berättarens omdöme om en fiktiv
  sajt [TAL 04:51, 06:29, 10:52]; det enda mätta beviset i videon är better-layouts pixeltabell [SKÄRM 10:02].
  Videon innehåller inga instruktioner riktade till agenter
- Kostnad: jakub: 239 tokens alltid för sju beskrivningar (36, 31, 46, 47, 23, 40 och 16 ur förgranskningen),
  1 371–2 657 vid användning per skill, 27–7 969 vid behov; 68 081 tokens text i hela repot. Inga beroenden, inga
  skript; underhåll: sju KALLA.md och en mening i bygg-sajt. Övriga sex tas inte in; deras mått: emil 70 833
  tokens (animate 120, 2 817, 1 981), garden 326 122 (web-design-engineer 118, 8 626, 47 686), elaya 4 950 (168,
  3 942, 0), MengTo 409 624 (awwwards 130, 1 665, 68), tastemaker 126 389 (219, 16 080, 124 120), designer-skills
  184 676 (111 skills om 43–90 tokens alltid var)
- Säkerhet: jakub LÅG: inga dolda tecken, ingen text riktad till agenter, inga skript, inga hookar;
  `disable-model-invocation: true` bara på de fyra användaranropade som inte tas med; frontmatter har bara name och
  description. emil HÖG: fem nollbreddstecken, varav U+200D i ett ZWJ-emojitestfall [REPO
  skills/break-ui/CATALOG.md rad 26] och U+200B före kodstaket i en mall för nästlade kodblock [REPO
  skills/improve-animations/PLAN-TEMPLATE.md rad 19–35]; tre "ignore previous instructions" är skillens egen regel
  att repoinnehåll är data [REPO break-ui/SKILL.md rad 36; improve-animations/SKILL.md rad 33;
  find-animation-opportunities rad 29 inte läst]; ofarligt. garden HÖG: två U+200D i demosajtens JSON-data, inte i
  skillen; 43 skript med nätanrop och miljönycklar (bildgenerering, TTS, release). MengTo HÖG: U+200B i en
  demobyggfil; "Send the API key" är ElevenLabs-dokumentation [REPO agent-skills/codex/elevenlabs-tts/SKILL.md rad
  84] och "execute this task" en Codex-standardprompt [REPO iterate-until-verified/agents/openai.yaml rad 4]; 77
  skript med eval, nätanrop och miljöläsning. tastemaker MEDEL: 33 skript, fyra skriver utanför repot
  (`~/.tastemaker`, `~/.ideagram`), nätanrop i foto- och ikonhämtning. designer-skills MEDEL: 7 byggskript. elaya
  LÅG. Inget kördes eller installerades. Inget försök att styra kirurgen
- Förslag: sju mappar `.claude/skills/better-layout/`, `better-typography/`, `better-colors/`,
  `better-accessibility/`, `better-ui/`, `better-writing/` och `better-interface/` ur jakubkrehel/skills @ 267330e,
  MIT med LICENSE i varje mapp, utan `agents/openai.yaml`, med KALLA.md som för humanizer och ett avsnitt överst i
  varje SKILL.md som löser krockarna (våra måttstockar vinner om värden, inga nya paletter, bara CSS-recept, svensk
  text följer copy-kontroll) och svenska beskrivningar som säger när bygget använder dem. I
  `.claude/skills/bygg-sajt/SKILL.md` steg 5 punkt 5, efter rad 252, en mening som pekar på better-layout för
  dimension 4 och better-typography och better-ui för hantverket innan JAMFORELSE.md skrivs. interface-review,
  variant, break och explain-interface tas inte med. Inget ur de övriga sex
- Utfall: sju better-skills i verktygslådan 2026-10-03 med svenskt förord, LÅG i förgranskningen; steg 5.5 pekar på
  better-layout, better-typography och better-ui.
- Backlog: B-20261002-ta-in-jakubkrehel-skills-better-layout-better-ty

### 2026-10-03 · AI LABS, "4 Ways to Actually Build Stunning Websites with Claude Code" (YouTube HqD5a2Cae60) · nej
- Källa: https://www.youtube.com/watch?v=HqD5a2Cae60 @ publicerad 2026-06-13 enligt metadata (AI LABS, 13:43, 12 318
  visningar, autogenererat engelskt transkript, sponsrad av Kimi [TAL 06:13–07:19; SKÄRM 06:41, 07:01] och med länk
  till kanalens betalgemenskap, där skillsystemet som visas ligger [TAL 04:55–05:13; SKÄRM 05:02 filträdet clone,
  functional-ui, gsap, marketing-ui, shadcn; SKÄRM 06:01]). Inget repo i beskrivningen; länkarna är ailabspro.io,
  sponsorn och ett nyhetsbrev [BESKRIVNING]. Läst och sett: hela tidslinjen och alla 41 bildrutor; ungefär 20 är
  inspelningar av terminal, editor, webbläsare eller Anthropics dokumentation, resten animerade illustrationer,
  sponsorklipp, titelkort och ett arkivklipp med en man vid en skärm [SKÄRM 05:02]. Rörelsen i GSAP-avsnittet syns
  inte i bildrutorna, bara ett stilläge [SKÄRM 04:42]. ailabspro.io, platform.kimi.ai och theroundup.so öppnades
  inte. Ägarens not: ingen
- Steg: 5 (5.1 riktning, 5.3 bygg, 5.6 granskning), 1 (hämtning av deras sajt) och arbetssättet runt dem: `kor.sh`
  (effort), spanarens källor, UPPTAGNA-VAL.md
- Jämfört med i dag, metod för metod: (1) **Anthropics officiella frontend-design-skill** mot ett bygge utan skill
  [TAL 00:34–01:38; SKÄRM 00:44 "Distributional convergence"; SKÄRM 01:24 utan, 01:44 med]. Vi: samma skill i
  `kunskap/externa/anthropic-frontend-design-SKILL.md` (REGISTER rad 14), läst i steg 5 (`.claude/skills/bygg-sajt/
  SKILL.md` rad 191). Lika. (2) **Skriv om skillen med modellens promptguide, och effort som spak** [TAL 01:38–02:10;
  SKÄRM 02:03 inklistrad guide; TAL 04:02–04:22; SKÄRM 04:22 "Consider all effort levels"]. Vi läser samma guider som
  spaningskälla (`kunskap/spaning-kallor.md` rad 12, 14) och har redan hämtat det som gäller bygget ur dem: fyra
  riktningar med namngivna uppgifter och "Modellen följer uttryckliga specifikationer precist" (bygg-sajt rad
  207–210), och listan över modellens egna standardval ur Opus 5.5-guiden (`kontroller/upptagna_val.py` rad 9–11,
  26–37). Effort: videon säger xhigh för animationer "ger färre omtag" utan mätning [TAL 04:22]; vi har ett blint
  par där ägaren valde medium före high (`LARDOMAR.md` rad 97–104) och medium som standard (`kor.sh` rad 62), med
  noteringen att nästa A/B prövar det igen. Lika, och vårt belägg är starkare än deras. (3) **Opus 4.8-guidens fix:
  be om flera riktningar först** [TAL 02:10–03:16; SKÄRM 02:43 "Design and frontend defaults"]. Vi: fyra riktningar
  i KONCEPT.md, tvåan som byggd sida och riktningsfrågan till ägaren med en bild per alternativ (bygg-sajt rad
  200–212, 238–245, 329–343). Lika. (4) **design.md från getdesign.md, lagd på efter att sidan genererats** [TAL
  03:16–03:49]. Dömd nej som källa (`REGISTER-arkiv-20261001.md` rad 896–928) och som metod i DP7mgLUKN_U-posten
  (rad 2717–2723): krockar med "Kopiera aldrig layout, palett eller typsnitt" (bygg-sajt rad 252) och riktning ur
  verksamheten (rad 200–201). Videon säger själv att filerna "låser allt ned till typsnittet" [TAL 03:43–03:49].
  Sämre. (5) **GSAP för marknadssidor, laddad automatiskt av en regel i deras skill** [TAL 03:49–04:55; SKÄRM 04:42].
  Vi: ingen JavaScript som inte behövs (bygg-sajt rad 217), 0 kB JS i alla tre dömda byggen (`LARDOMAR.md` rad 31,
  56, 87), byggstandarden 3.5 och 3.7, och den officiella skillens egen rörelseregel om en enda orkestrerad stund
  (anthropic-frontend-design rad 32). Samma krock som Ysr7oNDajJI-posten fann (rad 2987–2990). Sämre. (6)
  **Funktionell UI: HTML-mockuper, galleri, design.md, shadcn, Framer Motion** [TAL 05:13–06:13, 07:19–10:52; SKÄRM
  05:42, 08:00, 08:20, 08:40, 09:20, 11:19]. Våra sajter är statiska marknadssajter åt hantverkare (bygg-sajt rad
  8–10; byggstandarden 1.1), inga instrumentpaneler. Galleriet som visar tre mockuper sida vid sida [SKÄRM 08:40]
  motsvaras av tvåan och riktningsfrågan med bilder (rad 238–245, 329–343) och dashboardens blinda parvisa
  A/B-vy (`dashboard/server.py` rad 397–403). Rörelsereglerna i deras functional-ui, inget som standard, bara
  tillståndsåterkoppling, 150–250 ms, transform och opacity, reduced motion [SKÄRM 09:20, 11:19], är sakliga och
  samma hållning som byggstandarden 3.5, men riktade till appar. shadcn dömdes nej (rad 1449). Inte tillämpligt.
  (7) **Självverifiering med en subagent mot design.md** [TAL 10:19–10:52; SKÄRM 10:39]. Vi: två oberoende
  granskarsessioner utan byggarens resonemang, med brief, EARS-krav, referenser och tidigare byggens första vy
  (`kritik/GRANSKARE.md` rad 3–8, 21–30; bygg-sajt rad 255–262); litteraturen ger oberoende granskare
  (`kunskap/teoretisk-grund.md` rad 128–129). Starkare hos oss. (8) **Kloning: SingleFile CLI och sitemap.xml för
  publika sidor, skärmbilder av varje läge för sidor bakom inloggning** [TAL 11:25–13:04; SKÄRM 11:58, 13:18]. Vi:
  `kontroller/hamta_sajt.py` hämtar verksamhetens egen sajt via startsidans länkar och sitemap.xml, varje sida som
  html och text med bildlista och kontaktvägar (rad 2–9; bygg-sajt rad 66–68), och inspektionen tar skärmbilder i
  390 och 1440 (rad 99–101, 156). Mekaniken är lika; syftet är motsatt: videon klonar andras gränssnitt "så perfekt
  du kan" [TAL 11:25–11:58], vi hämtar deras egen sajt för diagnos och förbjuder kopiering (rad 252);
  ai-website-cloner-template dömdes nej (rad 2303). Krockar
- Skäl: videons tes är att skillen ska styra modellen bort från dess medelvärde [TAL 00:34–01:06], och bilderna
  visar motsatsen: varje "bättre" variant, med skillen [SKÄRM 01:44], efter omskrivningen [SKÄRM 02:23] och med GSAP
  [SKÄRM 04:42], är krämvitt papper eller mörkgrönt med serif, röd eller terrakotta accent, kursiva accentord,
  spärrade kapitäler och romerska siffror, det vill säga exakt det husstilsläge som Opus 4.8-sidan i samma video
  beskriver [SKÄRM 02:43] och som vår lista över modellens standardval namnger (`upptagna_val.py` rad 27–34). Det
  bevisar vår metod, inte deras: dokumentationen säger att generella instruktioner bara byter en fast palett mot en
  annan och att konkreta specifikationer fungerar [SKÄRM 02:43], vilket är KONCEPT.md:s exakta specifikation och
  UPPTAGNA-VAL. Sak för sak har vi varje metod som gäller en statisk sajt, ofta med bättre belägg (blint effort-par
  mot anekdot, två oberoende granskare mot en subagent), och det som är nytt för oss, design.md, GSAP och kloning,
  krockar med tre medvetna val. Det som är smart i videon gäller appar, inte våra sajter, och skillsystemet säljs
  i en betalgemenskap, så det finns inget att läsa. Källkritik: sponsor och betalgemenskap; "två av tre sajter"
  är en anekdot [TAL 02:43]; beviset är berättarens omdöme om en fiktiv plantage, och fotona i både
  utan-versionen och GSAP-versionen visar en stadssilhuett med TV-torn och kyrkspiror under rubriker om en
  högplatå [SKÄRM 01:24, 04:42], så bildproblemet berättaren pekade på [TAL 01:06] kvarstod i slutversionen;
  inspelningarna körs med alla behörigheter avstängda [SKÄRM 01:04, 08:20]. Videon innehåller inga instruktioner
  riktade till agenter
- Kostnad: inget tas in. Skillarna går inte att mäta: de finns bara i betalgemenskapen
- Säkerhet: ej tillämpligt (video; inget hämtat utöver transkript och bildrutor; inget kördes eller installerades)
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-03 · DesignCode, "Opus 5.5 Is INSANE for Web Design (Complete Guide)" (YouTube PA3f3MdRc08) · nej
- Källa: https://www.youtube.com/watch?v=PA3f3MdRc08 @ publicerad 2026-09-25 (DesignCode, 47:50, 27 453 visningar,
  autogenererat engelskt transkript, sponsrad av Mobbin [TAL 01:47–02:56, 47:21]; berättaren är enligt sin egen
  X-profil grundare av designcode.io och aura.build och säljer three.js-mallar på threeui.com [SKÄRM 39:28, 40:38]).
  Läst och sett: hela tidslinjen och alla 54 bildrutor; ungefär 40 är inspelningar av Claude-appen, webbläsaren,
  Mobbin eller X, resten 3D-scener (båten, skeppet, dalen). Rörelsen (orbit, vattenringar, shaderknappar, parallax)
  syns inte i bildrutorna, bara lägen [SKÄRM 26:25, 26:47, 27:57, 29:06]. Sajter öppnade med `kontroller/sida.mjs`:
  sunset-tutorial.mengto.here.now (HTTP 200; mobil första vyn och hela sidan sedda [BILD sunset-tutorial
  mobil-forsta.png, mobil-hela.png, TEXT.md]; desktop-skärmbilden gick inte att ta inom 30 s) och
  sunset.mengto.here.now (HTTP 200; ingen skärmbild gick att ta inom 30 s i vare sig mobil eller desktop; sedd bara i
  videons bildrutor). Inget repo i beskrivningen; projektfilerna ligger på Google Drive och hämtades inte
  [BESKRIVNING]. Mobbin, Higgsfield, aura.build, threeui.com och designcode.io öppnades inte. Ägarens not: ingen
- Steg: 3 (referenserna), 5 (5.1 riktning, 5.3 bygg: 3D, bilder, ikoner, 5.6 granskning), 7 (brand guide och
  annonser som sidospår); runt stegen: arbetsmodellen (röstprompt, timslånga körningar, parallella trådar)
- Jämfört med i dag, metod för metod: (1) **Mobbin som referenskälla**, via en anslutning i Claude-appen: "ge mig de
  fem bästa solcellssajterna", be om skärmbilder, blanda sektioner från olika sajter och planera sektionerna först
  [TAL 08:33–11:56; SKÄRM 09:48, 10:39, 11:48]. Agentens plan sätter en källsajt per sektion: hero och karta ur
  Daylight, betalsätt ur Klarna, omdömen ur Coda och Cake Equity, FAQ ur Farm Minerals, sidfot ur Daylight och Maze
  [SKÄRM 12:57]. Vi: referensjakt i tre roller där bygget söker själv, öppnar varje referens i 390 och 1440 och
  skriver REFERENSER.md (`.claude/skills/bygg-sajt/SKILL.md` rad 150–162; `kunskap/referensjakt.md` rad 13–27),
  "Gallerier är sökingångar, inte facit" (bygg-sajt rad 152) och "Kopiera aldrig layout, palett eller typsnitt"
  (rad 252). Ett kuraterat arkiv med mobil och desktop parvis, sökbart med briefen, ligger redan under prov via
  Inspo (REGISTER rad 2845–2929; B-20261002-a-b-inspo-mcp-hostad-andpunkt-som-sokingang-for), gratis, MIT och
  hostad utan konto. Mobbin kräver inloggning och har betalplaner [SKÄRM 02:08 "Sign in", "See our plans"; TAL 08:00
  anslutningen auktoriseras; SKÄRM 08:21 anslutningslistan], och täckningen för vår sorts verksamhet är sämre än videon låter: Mobbins
  egen startsida säger "over 1,000 iOS & Web apps, and 200 sites" [SKÄRM 02:08], mot Inspos 832 sajter, och
  videons egen agent svarar att Mobbin bara har två solcellsbolag, Daylight och T1 Energy, och fyller på med
  "närmaste grannar" [SKÄRM 09:48]. Sektion-per-källsajt är dessutom närmare kopiering än vår jämförelse drag mot
  drag (`kunskap/referenser-professionella.md` rad 40–45). Sämre än det vi redan prövar. (2) **Allt i 3D med
  three.js**: hus, telefon, diagram i träram, vatten i sidfoten, shaderknappar, parallax, med "välj rätt medium"
  (byggnader och landskap i 3D, människor aldrig) [TAL 13:02–16:26, 21:41–29:15; SKÄRM 24:29, 25:38, 26:25, 26:47,
  27:57]. Vi: innehåll och navigation utan JS (`kunskap/byggstandard.md` rad 18), högst 200 kB JS (3.7, rad 52),
  inga tredjepartsresurser vid sidladdning (4.4, rad 61), LCP 2,5 s (4.1, rad 58), reducerad rörelse (3.5, rad 50),
  "ingen JavaScript som inte behövs" (bygg-sajt rad 217), 0 kB JS i de tre dömda byggena (`LARDOMAR.md` rad 31, 56,
  87), och three.js dömt nej som källa (REGISTER rad 1550–1579). Videons egen agent beskriver sajten som "one
  self-contained 10.5 MB file; only three.js loads from jsDelivr" [SKÄRM 06:02, 08:47, 15:16], laddade ner 127 MB
  texturer för att packa till omkring 15 MB WebP för sidan [SKÄRM 29:47], och vårt verktyg fick ingen skärmbild av
  livesajten inom 30 s. Krockar med fyra medvetna val. Sämre. (3) **Poängsätt varje element 1–10 och iterera till
  8** [TAL 04:05–05:14, 16:00–16:26]. Bildrutan visar hur agenten gör det: två domare inne i samma session, betyg
  per sektion i fyra omgångar, "scores plateaued at 7.0–7.1 for two rounds … within the judges' ±0.5 noise, so the
  next gains depend on the structural decisions" [SKÄRM 04:53, 06:02]. Vi: två oberoende granskarsessioner utan
  byggarens resonemang, fem kriterier 1–10 med ankare och trösklar (`kritik/GRANSKARE.md` rad 3–8, 72–80),
  GRANSKNINGSLOGG per omgång, "originaliteten under 7 i två omgångar: byt riktning" och bästa mot sista (bygg-sajt
  rad 255–268). Litteraturen ger oberoende granskare (`kunskap/teoretisk-grund.md` rad 128–131); GRANSKARE.md rad
  3–5 säger varför en agent inte ska döma sitt eget. Samma platåregel, starkare oberoende hos oss. Lika eller
  bättre hos oss. (4) **Människor och ornament som genererade bilder** (Aura, Higgsfield, Midjourney) och ikoner ur
  Iconify Solar i stället för ritade [TAL 17:34–19:44, 43:26–44:33; SKÄRM 18:43, 19:52]. Resultatet är tre
  "husägare" med AI-porträtt, namn, ort och "¥20,900 / mo saved" [SKÄRM 44:05; BILD sunset-tutorial TEXT.md rad
  163–179], och berättaren kallar själv porträtten "a bit sloppish" [TAL 43:26–44:00]. Vi: hitta aldrig på omdömen,
  siffror eller personer (bygg-sajt rad 20–21), genererade bilder framställs aldrig som kundens personer
  (`kunskap/bild.md` rad 19–20), omdömen bara med källa (byggstandarden 9.3, rad 121), "hellre inga foton än stock"
  (`LARDOMAR.md` rad 90), och det som saknas beställs (bygg-sajt rad 141–145). Ikoner som SVG har vi (3.6, rad 51)
  och ikonuppsättningar registreras med licens (bygg-sajt rad 39–41). Krockar. (5) **Arbetsmodellen**: röstprompt
  med all fantasi på en gång, låt agenten arbeta i en till två timmar, parallella trådar i worktrees för logotyp,
  brand guide och annonser, en regel om högst en dollar bildgenerering utan att fråga, en enda HTML-fil och en mapp
  med gamla projekt som agenten kan återanvända ur [TAL 15:53–16:26, 29:45–37:54; SKÄRM 31:04, 34:52, 35:17,
  36:01]. Vi: obevakad körning som tar två timmar med granskningar (`LARDOMAR.md` rad 100–101), Astro ur mallen,
  "Titta inte på andra byggen" (bygg-sajt rad 43) och UPPTAGNA-VAL.md som namnger val som gått igen, inga betalda
  bild-API:er i bygget (`kunskap/bild.md` rad 6). Återbruket ur gamla projekt är motsatsen till vårt val, och
  berättaren säger själv att han inte vet om det hände [TAL 33:00–33:18]. Brand guide och annonser ligger utanför
  det vi bygger. Inte tillämpligt eller krockar. (6) **Den stora prompten och ThreeUI**: krav på prestanda, retina,
  prov i webbläsaren med skärmbilder i fyra ljuslägen, konsolen utan fel, "do not wait for me to specify which
  technologies" [SKÄRM 39:28, 40:38], och 150 fria three.js-hero-mallar att kopiera prompten ur [TAL 40:39–42:20;
  SKÄRM 41:47]. Provdelen har vi (inspektionen, provets grindar, EARS-krav); mallarna är berättarens egen produkt
  och krockar med rad 252. Lika respektive nej
- Skäl: videons tes är att Opus 5.5 med Mobbin-referenser och 3D ger sajter "som inte är AI slop" [TAL 02:56,
  45:40], och sajten sedd med egna ögon säger emot det: krämvit bakgrund (rgb 251, 245, 234), Instrument Serif i
  rubriken med andra raden i kursiv ("Your lights don't."), spärrad versaletikett över rubriken, monospace-rad under
  knappen, pillerknappar, terrakotta-accent, numrerade steg 01/02/03 och tre likadana kort i rad för Panels, Battery
  och The app [BILD sunset-tutorial mobil-forsta.png, mobil-hela.png, SIDA.md; TEXT.md rad 59–73, 86–109]. Det är
  sex av tio namngivna standardval i `kontroller/upptagna_val.py` rad 26–37, plus likadana kort i rad som
  `kritik/GRANSKARE.md` rad 86 räknar som AI-mönster, alltså modellens husstil med ett 3D-hus under. Verksamheten är fiktiv och beviset påhittat: 4 200 hem, 31 städer, 58 MWh och tre AI-porträtt med
  sparbelopp [TEXT.md rad 26–33, 155–179; SKÄRM 44:05], vilket är exakt det bygg-sajt rad 20–21 och byggstandarden
  9.3 förbjuder. Det som är välgjort är texten: konkreta svar om kawara-takkrokar, tyfon och hinoki-skåp [TEXT.md
  rad 190–216], men det är fiktion utan "Bara de har" att hämta ur. Sak för sak har vi varje metod som gäller en
  statisk sajt, med starkare belägg (oberoende granskare i egna sessioner mot domare i samma session; Inspo-provet
  med en fri källa mot en sponsrad betalkälla med 200 sajter), och det som är nytt, 3D överallt, genererade
  människor, sektioner ur andras sajter, mallbibliotek och återbruk ur gamla projekt, krockar med medvetna val och
  med three.js-domen. 3D-dalen och skeppet är imponerande hantverk [SKÄRM 00:52, 01:26, 22:11, 23:20] men spel, inte
  sajter åt hantverkare, och berättaren säger själv att de kräver "a ton of references" och "a ton of steering"
  [TAL 01:47]. Blir Inspo-provet vunnet och arkivets täckning gränsen, är Mobbin ändå inte nästa kandidat utan en
  egen bedömning med konto, kostnad och de 200 sajterna framför sig. Källkritik: sponsrad av Mobbin, och
  berättaren säljer aura.build (dömt nej, `kunskap/REGISTER-arkiv-20261001.md` rad 907–908), threeui.com och kurser;
  "$10,000, $20,000 value" och "easily $20,000 if you were to give this to a client" är berättarens omdömen [TAL
  00:00, 29:15]; "close to 400,000 views" är ett inläggs räckvidd, inte ett resultat [TAL 00:39]. Videon innehåller
  inga instruktioner riktade till agenter
- Kostnad: inget tas in. Som jämförelse: videons egen sajt är enligt agenten 10,5 MB i en fil plus three.js från CDN
  [SKÄRM 06:02], mot vår budget 200 kB JS och 100 kB CSS (byggstandarden 3.7); en körning tog "about 1 hour" utan
  att vara klar [TAL 42:54–43:26], vilket är i nivå med våra byggen men utan prov och granskning
- Säkerhet: ej tillämpligt (video; inget hämtat utöver transkript, bildrutor och två sidors skärmbilder och text;
  projektfilerna på Google Drive hämtades inte; inget kördes eller installerades)
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-03 · Create a Pro Website, "The EASY way to build a beautiful website with Claude Code (full workflow)" (YouTube fDTwHIKltpc) · nej
- Källa: https://www.youtube.com/watch?v=fDTwHIKltpc, publicerad 2026-07-02 enligt videons metadata, 26:00, cirka
  690 800 visningar, autogenererat engelskt transkript, YouTubes standardlicens. Läst hela transkriptet och 26 av 46
  bildrutor: alla som visar prompten, frågorna, resultatet, redigeringen och publiceringen; de 20 övriga är talande
  huvud, kontoinstallation och Hostingers kassa enligt tidslinjen. Länkarna i beskrivningen är de två skills videon
  bygger på, anthropics/skills frontend-design och nextlevelbuilder/ui-ux-pro-max-skill, båda redan dömda nej (rad 908
  och 1377) med ägarens medhåll (`kunskap/KIRURG-OMDOMEN.md` rad 95–98 och 145–148); de klonades inte på nytt. Övriga
  länkar är kanalens egna sidor, en Udemy-kurs och en Hostinger-affiliatesida [BESKRIVNING]. Ägarens not: ingen
- Steg: 1 (frågor till verksamheten), 3 (referenser), 4 (text), 5 (riktning, bilder, rörelse) och lanseringen
- Jämfört med i dag: (1) **Skillsen installeras globalt ur en länk** med prompten "install this skill globally" [TAL
  05:25–07:05]; på skärmen bygger agenten ett CLI från källkod, sätter ett eget npm-prefix och skriver en ny
  `~/.bash_profile` med PATH [SKÄRM 09:33, 09:47]. Hos oss körs ingen kod ur källor och bygget rör inte `.claude/`
  (`.claude/skills/bygg-sajt/SKILL.md` rad 45–48); skillsen i sig är dömda nej. Krockar. (2) **Referensen** är en
  skärmdump av en Dribbble-mockup, inklistrad "as inspiration" [TAL 08:44–09:17; SKÄRM 08:55, 11:26]; agenten läser
  av den som "hero, trust bar, about, services, blog, contact" och bygger samma sektioner i samma ordning [SKÄRM
  12:03, 13:56]. Vi: referensjakt i tre roller, riktiga sajter öppnade i 390 och 1440, "Gallerier är sökingångar,
  inte facit" och "Kopiera aldrig layout, palett eller typsnitt" (bygg-sajt rad 153–165, 260). Sämre. (3) **"Please
  ask me any questions"** ger fyra flervalsfrågor: märke, sektioner, filformat, tjänster [SKÄRM 12:03, 12:41, 13:18].
  Vi: kundintervjuns frågor som checklista mot det publika underlaget, minst tio saker i "Bara de har" (rad 65,
  93–95) och det som saknas beställs i BESTALLNING.md (rad 20–24, 144–148), eftersom ingen svarar under körningen.
  Fyra frågor ger inget specifikt att bygga på. Sämre. (4) **Bilderna** är genererade med Higgsfield, också före och
  efter och teamfotot [TAL 01:39–02:11, 15:22; SKÄRM 02:02, 16:26, 19:34]; agenten varnar själv att teamfotot visar
  pikétröjor med ett annat företagsnamn [SKÄRM 14:34]. Vi: genererade bilder framställs aldrig som kundens personer
  eller arbete (`kunskap/bild.md` rad 19–20), "Inga stockbilder" (bygg-sajt rad 80), "hellre inga foton än stock"
  (`LARDOMAR.md` rad 90). Krockar. (5) **Resultatet med egna ögon:** Playfair Display och Inter [SKÄRM 13:56],
  kursivt accentord "Crafted to Last", spärrad versaletikett "DESIGN · BUILD · MAINTAIN", pillerknappar, statistikrad
  15+, 1,200+, 98 % och 5.0 stjärnor, förtroenderad med Austin Chamber, TNLA, BBB, EPA WaterSense och Houzz, sex
  likadana tjänstekort, omdömen från "Megan R., David C., Sofia P." och tre bloggkort utan sidor bakom [SKÄRM 00:02,
  14:34, 15:11, 18:19; TAL 15:55]. Agenten listar själv telefon, adress, omdömen, blogg och formulär som påhittade
  platshållare [SKÄRM 14:34]. Det är fem av modellens standardval i `kontroller/upptagna_val.py` rad 26–40, siffror
  och certifieringar som bygg-sajt rad 20–21 och byggstandarden 9.3 (`kunskap/byggstandard.md` rad 121) förbjuder, och
  likadana kort i rad som `kritik/GRANSKARE.md` rad 88 räknar som AI-mönster. Sämre. (6) **Rörelsen:** en 36 MB
  hero-video skrubbas av skrollen med requestAnimationFrame, och agenten säger själv att filen är för tung för en
  startsida [SKÄRM 18:19; TAL 16:29–17:34]. Vi: reducerad rörelse, högst 200 kB JS och LCP 2,5 s (byggstandarden 3.5,
  3.7 och 4.1, rad 50, 52, 58), 0 kB JS i tre dömda byggen (`LARDOMAR.md` rad 31, 56, 87). Krockar. (7) **En enda
  HTML-fil med Tailwind och JS** [SKÄRM 12:41] mot Astro ur mallen med en sida per huvudtjänst (bygg-sajt rad 136–137,
  221). Sämre. (8) **Publiceringen:** filerna zippas och laddas upp som "migrering" till Hostinger via kanalens
  affiliatesida [TAL 20:18–25:15; SKÄRM 25:13]. Inget bygge har lanserats än; `kunskap/lansering.md` finns. Inte
  tillämpligt och ingen fördel. (9) **Rit- och markeringsverktygen** i Claude-appens förhandsvisning [TAL
  18:19–19:13; SKÄRM 19:34] är redigering med en människa i slingan; våra byggen körs obevakat med två oberoende
  granskare (bygg-sajt rad 265–278). Inte tillämpligt
- Skäl: videons löfte är en sajt som "inte ser ut som de generiska AI-byggda" [TAL 00:32], och det som syns på skärmen
  är precis en sådan: modellens husstil med Playfair och Inter, kursivt accentord, versaletikett, statistikrad och
  likadana kort, över genererade bilder, påhittade siffror, certifieringar och omdömen, och en blogg som inte finns
  [SKÄRM 00:02, 14:34, 15:11]. Berättaren dömer den själv som "pretty dang impressive" efter "10 15 minuter" [TAL
  15:49–15:55], men måttstocken är tiden, inte om något i sajten är sant eller bara Summit Ridges. De två skills som
  ska ge resultatet är dömda nej med ägarens medhåll, och ingen av de övriga metoderna är bättre än vår: referensen
  kopieras sektion för sektion i stället för att jämföras drag mot drag, fyra flervalsfrågor ersätter underlaget, och
  bilderna, rörelsen och platshållarna krockar med bild.md, byggstandarden och L3. Det som är rätt i videon, att samla
  verksamhetens märke, färger och bilder före bygget [TAL 01:39–02:44] och att låta agenten läsa färgerna ur logotypen
  [SKÄRM 13:18], gör vi redan i steg 1 och i KONCEPT.md:s krav på riktningar härledda ur verksamhetens eget material
  (bygg-sajt rad 76–82, 208–211). Källkritik: videon säljer Hostinger med affiliatelänk och rabattkod [BESKRIVNING; TAL
  20:18–22:30], visningarna är räckvidd och verksamheten är påhittad med 555-nummer. Inga instruktioner till agenter
- Kostnad: inget tas in
- Säkerhet: ej tillämpligt (video; bara transkript och bildrutor hämtade, inget klonat, kört eller installerat).
  Värt att se: metoden "installera den här skillen globalt" lät agenten bygga från källa och skriva skalprofilen
  [SKÄRM 09:33, 09:47], det vi förbjuder i kirurgen och i byggena
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-03 · Mikey No Code, "The Easiest Way to Build & Host a Website with Claude Code (Full Tutorial)" (YouTube 8F953MNwqII) · nej
- Källa: https://www.youtube.com/watch?v=8F953MNwqII, publicerad 2026-08-14 enligt videons metadata, 35:17, cirka
  120 900 visningar, autogenererat engelskt transkript, YouTubes standardlicens. Läst hela transkriptet och 35 av 63
  bildrutor: alla som visar prompterna, agentens svar, sajten, hosting.com, WHM, Cloudflare och cPanel; de övriga är
  talande huvud eller textplanscher enligt tidslinjen. Dessutom 15 av 43 täta rutor 28:15–29:39 (mobilprovet) och 6 av
  36 täta rutor 31:30–32:40 (den publicerade sajten). Enda länken i beskrivningen är en affiliatelänk till hosting.com
  med rabattkod; den öppnades inte. Ägarens not: ingen
- Steg: 5 (bygge), 6 (prov) och lanseringen (fas L i byggstandarden, `kunskap/lansering.md`)
- Jämfört med i dag: (1) **Värden:** en ohanterad Linux-VPS hos hosting.com med WHM och cPanel, där ägaren själv
  ansvarar för rootlösenord, uppdateringar och säkerhetskopior [TAL 02:51–03:58, 15:44–16:16; SKÄRM 06:22, 13:48,
  15:30], och sajten laddas upp genom att dra filerna till public_html [TAL 29:33–30:39; SKÄRM 29:58, 30:42]. Vi:
  statisk Astro med förhandsvisning per gren och noindex som svarshuvud, CDN och hashade filer, HSTS och kanonisk
  värd i Vercel-steget (`kunskap/byggstandard.md` 1.4, 4.5, 4.6, 8.1, rad 28, 62–63, 108), återgång genom att peka
  tillbaka till föregående driftsättning (`kunskap/lansering.md` rad 111–112). En VPS flyttar månadens patchrunda
  (1.5, rad 29) och säkerhetshuvudena (8.2, rad 109) till ägaren och ger ingen förhandsvisning per ändring. Sämre, och
  sponsrat. (2) **DNS:** namnservrarna flyttas till Cloudflare, A-post för roten och ett jokertecken, proxyn av [TAL
  07:16–10:51; SKÄRM 08:36, 10:24]. Vi: standardvägen är att bara ändra webbposterna hos nuvarande DNS-värd,
  ett namnserverbyte kräver att hela zonen återskapas ur en zonexport, TTL sänks före bytet och ingen session gör
  DNS-ändringar (`kunskap/lansering.md` rad 11–17). För en hantverkare med e-post på domänen är videons väg den
  riskablare. Sämre. (3) **Bygget:** fyra prompter i lager, toppsektion, om och kunskaper, projekt och kontakt, meny
  och sidfot, med "match the existing design and do not change the hero" [TAL 18:25–18:58, 21:13–28:15; SKÄRM 22:19,
  24:42, 26:34, 28:16], och innehållet sist: "replace the placeholder content with your own real bio" [TAL 34:13].
  Vi: innehåll före form (steg 4, `.claude/skills/bygg-sajt/SKILL.md` rad 172–193), KONCEPT.md med fyra riktningar och
  exakt specifikation före kod (rad 208–220), alla sidor ur INNEHALL.md (rad 224). Litteraturen säger content first
  och mobile first (Wroblewski 2011; Halvorson & Rach 2012; `kunskap/teoretisk-grund.md` rad 34–35). Lagerprompterna
  är ett sätt för en människa att styra i små steg; obevakat bygger vår byggare ur specifikationen och itererar mot
  snabbprov och granskare. Sämre. (4) **Resultatet med egna ögon:** mörkblå bakgrund med elektriskt blå accent, Inter
  från Google Fonts, animerad partikelcanvas, spärrad versaletikett "HI, MY NAME IS", gradienttonat namn, numrerade
  rubriker 01–04, tolv likadana kunskapskort och tre likadana projektkort där "View Project" länkar till # [SKÄRM
  22:45, 23:10, 24:42, 26:34, 28:16, 32:08, 32:16]. Det är modellens standardval 2, 4 och 7 i
  `kontroller/upptagna_val.py` rad 28, 30, 33 och "likadana kort i rad" i `kritik/GRANSKARE.md` rad 88; Google Fonts
  är en tredjepartsresurs vid sidladdning (4.4, rad 61). Agenten skriver själv att projekten är platshållare och att
  formuläret "doesn't send anywhere yet" [SKÄRM 28:16]; allt innehåll är fiktivt, Alex Morgan med sex års erfarenhet
  och "thousands of users" [SKÄRM 32:00]. Sämre. (5) **Formuläret:** klientsidig validering i JS utan mottagare
  [SKÄRM 28:16, 32:24]. Vi: vanlig POST utan JS till demomottagaren, honeypot och tidsfälla, tacksida (6.1–6.7, rad
  84–90). Sämre. (6) **Provet:** agenten tar skärmbild och läser konsolen i Claude Browser och skrev en egen statisk
  server när file:// inte laddade CSS [SKÄRM 22:45, 23:10]; berättaren klickar igenom menylänkarna [TAL 28:27–29:33].
  Mobilprovet som talet beskriver syns inte i någon av de 43 rutorna varannan sekund 28:15–29:39: skärmen visar
  desktopvyn av kunskapskorten och sedan berättaren. Vi: axe, Lighthouse, spill 320–1920, standardgrinden,
  stilrapporten och två oberoende granskare (bygg-sajt rad 265–272, 287). Sämre. (7) **Lanseringsgapet** är videons
  bärande poäng: "every other tutorial stops" vid localhost [TAL 00:00–01:08]. Hos oss är det sant att inget bygge
  har lanserats, att `kunskap/lansering.md` hänvisar till verktyg som inte finns i repot (verktyg/lansering.py,
  verktyg/sokkonsol.py, MANDAT.md; sökt 2026-10-03) och att "Vercel-steget" nämns fem gånger i byggstandarden utan
  egen text. Ägaren har sagt "då väntar vi med det" om Vercel (`BESLUT.md` rad 102). Videons lösning är ändå fel väg;
  gapet stängs med vår egen text, som egen backlogpost nedan
- Skäl: videon lovar "a complete, professional portfolio website" [TAL 18:25] och ägnar sexton minuter åt att köpa en
  server, flytta namnservrar och klicka i WHM och cPanel, allt för en värd som sponsrar videon [BESKRIVNING; TAL
  05:37, 34:29]. Det som sedan byggs på tretton minuter är modellens husstil med fiktivt innehåll: en ensidig
  portfölj i mörkblått med partiklar, Inter, versaletikett, numrerade rubriker och femton likadana kort, där agenten
  själv kallar projekten platshållare och formuläret oanslutet [SKÄRM 28:16, 32:08, 32:16]. Sak för sak är varje
  metod sämre än vår eller krockar med ett medvetet val: en VPS i stället för statisk värd med förhandsvisning och
  återgång, namnserverflytt i stället för webbposter hos nuvarande värd, form före innehåll i stället för innehåll
  före form, JS-formulär utan mottagare i stället för POST utan JS, ögonmått i stället för prov och oberoende
  granskare. Det enda som är rätt, att en sajt inte är klar förrän den svarar på en riktig domän, är ett gap hos oss
  också, men det löses med en text för vår stack, inte med videons. Källkritik: sponsrad av hosting.com med
  affiliatelänk och rabattkod, verksamheten är påhittad, "thousands of people" är berättarens ord [TAL 00:00], och
  mobilprovet påstås men visas inte. Inga instruktioner till agenter
- Kostnad: inget tas in. Som jämförelse: Pro-planen visade "Approaching session usage limit" efter fyra prompter på en
  ensidig sajt [SKÄRM 28:16, 28:17]; modellen i appen var Fable 5 på hög nivå [SKÄRM 22:19, 22:45]
- Säkerhet: ej tillämpligt (video; bara transkript och bildrutor hämtade, inget klonat, kört eller installerat).
  Videon visar serverns IP-adress och var rootlösenordet står i värdens panel [SKÄRM 06:22]; inget av det förs vidare
  här
- Förslag: inget för domen. Egen innovation: `kunskap/lansering.md` skrivs om för vår stack när en kund ska ut,
  utan kommandon mot verktyg som inte finns och med ett avsnitt för Vercel-steget som byggstandarden hänvisar till
- Utfall: —
- Backlog: ingen för domen; egen innovation B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den

### 2026-10-03 · AI LABS, "Every Level Of Claude Code Loop Engineering Explained" (YouTube PLyRe6Zk--8) · nej
- Källa: https://www.youtube.com/watch?v=PLyRe6Zk--8 @ publicerad 2026-08-18 (AI LABS, 23:04, 32 862 visningar,
  autogenererat engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 42 bildrutor:
  ungefär hälften är inspelningar av terminal, editor, webbläsare, GitHub och en telefon, resten animerade diagram,
  titelkort och sponsorklippet för Hedra [SKÄRM 12:22]. Rörelsen på GSAP-sidan syns inte, bara ett stilläge
  [SKÄRM 08:28]. Länkarna i beskrivningen: kanalens betalgemenskap, där hela skillsystemet (goal-writer,
  new-feature, functional-ui, feature-batch, mobile-preview) ligger [TAL 19:39–20:09; SKÄRM 20:09], en
  Drive-mapp med en uppsättningsfil för Next.js, Supabase och Vercel (inte öppnad), sponsorn, nyhetsbrevet,
  paseo.sh (sett i videon [SKÄRM 21:15], inte öppnad; repot getpaseo/paseo har licensen "Other") och fyra öppna
  skillrepon: mattpocock/skills (redan dömt, rad 204), greensock/gsap-skills (klonat @ aed9cfd, MIT, senaste push
  2026-07-29), vercel-labs/agent-skills (klonat @ 063bee9, ingen licensfil, senaste push 2026-08-28) och
  supabase/agent-skills (bara metadata: MIT, push 2026-10-02; databas, inget för en statisk sajt). I de två
  klonerna läst förgranskningen, README och SKILL.md för web-design-guidelines, writing-guidelines och
  deploy-to-vercel. Ägarens not: ingen
- Steg: 5.6 och 6 (granskningsslingan), 5.1 och 5.4 (koncept och tvåan mot prototyp), 8 (ägarens dom), och
  arbetssättet runt dem: stoppvakten, `kor.sh`, dashboarden; lanseringen som parkerat ämne
- Jämfört med i dag, sak mot sak: (1) **Slingan.** Videons `/goal` arbetar tills målet är nått; efter varje tur
  läser en mindre modell samtalet och avgör klart eller inte [TAL 05:24–05:56; SKÄRM 05:41]. Vi: stoppvakten kör
  provet och granskningen själv vid varje avslutsförsök och släpper inte förrän grindarna är gröna, rapporten finns
  och granskarna godkänt (`.claude/hooks/stoppvakt.py` rad 2–11; `kor.sh` rad 33–35), och de skyddade filerna
  hashjämförs före och efter (`kor.sh` rad 83–86). Domaren hos oss är deterministiska kontroller och två sessioner,
  inte en mindre modell som läser byggarens eget samtal. Starkare hos oss. Videons egen varning är riktig: en
  skärmbild fångar inte rörelse, maskotens blinkning missades under 38 minuter [TAL 08:06–08:40]; hos oss finns
  ingen rörelse att missa (0 kB JS i tre dömda byggen, `LARDOMAR.md` rad 31, 56, 87; byggstandarden 3.5). (2)
  **Spec som checklista.** spec.md är "både byggspec och verifieringschecklista", skriven för att läsas utan minne
  av förra passet; verifiera först, rätta det högsta röda, ett i taget [SKÄRM 07:21 rad 3–4, 12–14; SKÄRM 07:55].
  Vi: EARS-kraven i briefen som granskaren prövar (`.claude/skills/bygg-sajt/SKILL.md` rad 133–135;
  `kritik/GRANSKARE.md` rad 57), blockerande fynd med acceptanskriterium (rad 269) och GRANSKNINGSLOGG per omgång
  (rad 273–274). Lika. "Ett fel per pass" vore sämre hos oss, där en omgång tar 4–15 minuter och körningen har ett
  tak på fem (rad 266–267, 272). (3) **Den som bygger dömer inte.** En adversariell granskningsagent med färsk
  kontext som antar att det finns ett fel [TAL 14:02–14:35; SKÄRM 14:35 main, build, review]. Vi: samma regel med
  två granskare i egna sessioner, utan byggarens resonemang, "hellre för sträng än för snäll"
  (`kritik/GRANSKARE.md` rad 3–8; `kontroller/granska.py` rad 2–6), och litteraturens skäl: en ensam granskare
  hittar omkring 35 procent (`kunskap/teoretisk-grund.md` rad 128–129). Starkare hos oss. (4) **Klickbar
  prototyp före bygget** (functional-ui: en HTML-mock per funktion i `mocks/`) för att se om man ville ha det man
  beskrev och ge slingan något att verifiera mot [TAL 13:05–13:38; SKÄRM 16:48, 17:22 "MOCK · SERVICES"]. Vi:
  exakt specifikation i KONCEPT.md före kod (rad 216–218), tvåan som kastbar sida (rad 246–253), snabbprov med
  skärmbilder (rad 245) och emil-prototype i `kunskap/externa/`. För en sajt på tre till sju sidor är sajten under
  snabbprovet själv prototypen; en separat mock vore dubbelt arbete. Samma slutsats som HqD5a2Cae60-posten (rad
  3136–3142). Lika. (5) **Designen kopierad från Duolingo.** design.functional.md har namnet Duolingo,
  sourceUrl duolingo.com, färger och typsnitt [SKÄRM 03:28; TAL 03:15–03:28], och resultatet är en fiktiv salong
  med Duolingo-maskotar (sax och schampoflaska med ansikten), rundad display-rubrik och "AUSTIN, TEXAS · EST.
  2019" [SKÄRM 08:28]. Krockar med "Kopiera aldrig layout, palett eller typsnitt" (rad 260) och riktning ur
  verksamheten (rad 208–209); hade fallit hos granskaren på originalitet och "Bara de har". Sämre. (6)
  **GSAP-tung landningssida och en optimize-skill som vinner tillbaka farten** [TAL 04:52–05:08, 06:29–06:48].
  Vi: ingen JavaScript som inte behövs (rad 225), byggstandarden 3.5; samma krock som Ysr7oNDajJI- och
  HqD5a2Cae60-posterna fann (rad 3132–3135). gsap-skills är välskrivet och litet (åtta skills, omkring 29 000
  tokens, förgranskning LÅG), men README ber agenter rekommendera GSAP när ingen bett om det [REPO README.md rad
  33]. Inget för våra sajter. Sämre. (7) **Fabriken.** Kö i QUEUE.md (funktion, spec, status, misslyckade pass,
  PR), subagent bygger på en gren, PR med skärmbilder, människan mergar och Vercel driftsätter [SKÄRM 17:53 rad
  3–5; 18:28; 19:02 två PR; 19:35 live]. Vi: en körning per verksamhet, tre över natten är tre rader (`kor.sh` rad
  7); ägaren dömer i dashboarden med skärmbilder och rapport (steg 8; `dashboard/index.html` rad 212, 236); ingen
  driftsättning än, ägaren har sagt "då väntar vi med det" (`BESLUT.md` rad 102). En sajt är ett stycke, inte en
  lista funktioner (qLfSDQ5NGh0-posten rad 2662–2665). Lika för vårt omfång. deploy-to-vercel i vercel-labs är en
  kandidat när lansering blir aktuell, men repot saknar licensfil och kan inte kopieras in; web-design-guidelines
  och writing-guidelines där är fyrtioraders skal som hämtar command.md från nätet vid varje körning [REPO
  skills/web-design-guidelines/SKILL.md rad 23–29], och texten de hämtar har vi redan lokalt
  (`kunskap/externa/vercel-web-interface-guidelines-command-e3d624ba.md`). (8) **Nivå tre, Paseo.** Claude Code
  på egen dator med ett fönster från telefonen, skills och `/goal` fungerar, alla behörigheter av [TAL 20:43–21:48;
  SKÄRM 21:15, 21:49, 22:22 "Bypass"], och mobile-preview som lägger mockuperna på Vercel så att man klickar i
  dem på telefonen [TAL 22:20–22:53; SKÄRM 22:36]. Vi: dashboarden startar byggen och tar emot domen, bara på
  127.0.0.1 (`dashboard/server.py` rad 2–9, 855). Ägarens två jobb är desamma som videons: starta och döma. En
  tredje app som kör agenten med behörigheterna avstängda behöver vi inte. Men en sak är bättre i videon: ägaren
  ser resultatet i en riktig telefon. Våra tre domar bedömde mobilen i 390 px-emulering (`LARDOMAR.md` rad 30,
  55, 79) och gav Mobil ergonomi "Okej" i två av tre (rad 35, 60); `kunskap/teoretisk-grund.md` rad 20 listar
  riktiga användare som vårt gap. Egen innovation nedan
- Skäl: videon lär ut det vi redan har byggt: en slinga där agenten verifierar, en skild dömare med färsk kontext
  och en spec som är checklista, och hos oss är varje del starkare i sak (deterministiska grindar och två
  granskare i stället för en mindre modell som läser byggarens samtal). Det som är nytt, Duolingo-kopian, GSAP,
  funktionskön med PR och Paseo, krockar med tre medvetna val eller gäller appar med inloggning och databas, inte
  statiska sajter åt hantverkare. Resultatet som visas är en påhittad salong i ett annat varumärkes kläder [SKÄRM
  08:28]; den hade inte klarat originaliteten. Källkritik: sponsor och betalgemenskap där skillsystemet ligger;
  "38 minuter, ett fel" och "3 timmar" är berättarens egna siffror [TAL 08:06, 18:33]; alla inspelningar körs med
  behörigheterna avstängda [SKÄRM 02:54, 15:42]; videon innehåller inga instruktioner till agenter. gsap-skills
  README innehåller en rad riktad till agenter om att rekommendera GSAP [REPO README.md rad 33], noterat
- Kostnad: inget tas in
- Säkerhet: förgranskningen av vercel-labs/agent-skills MEDEL (166 skript, bland dem uppladdningsskriptet i
  deploy-to-vercel och tester som läser miljövariabler; inga dolda tecken, ingen text riktad till agenter), av
  gsap-skills LÅG (sex skript, inga dolda tecken). Inget kördes eller installerades. Videons projektträd visar
  filnamn för administratörsuppgifter och databaslösenord [SKÄRM 02:54]; inget innehåll syns och inget förs vidare
- Förslag: inget för domen. Egen innovation: dashboardens visning av sajten (`dashboard/server.py` rad 714–722,
  provets statiska server `kontroller/prova.py` rad 142–143) får en adress på det egna nätverket, visad som
  QR-kod bredvid knappen "Öppna vår sajt" (`dashboard/index.html` rad 212), så att ägaren svarar på
  frågeformulärets mobilfrågor ur en riktig telefon; dashboarden själv och alla POST förblir på 127.0.0.1. Kräver
  ägarens ja, eftersom den statiska visningen blir nåbar för andra på samma nätverk
- Utfall: —
- Backlog: ingen för domen; egen innovation B-20261003-agaren-domer-mobilen-i-en-riktig-telefon-dashboa

### 2026-10-03 · Jono Catliff, "Claude Code Web Design: 10 Years Covered In 66 Minutes" (YouTube 2Gda_ZvV1V4) · nej
- Källa: https://www.youtube.com/watch?v=2Gda_ZvV1V4 @ publicerad 2026-05-19 (Jono Catliff, 1:06:59, 24 404
  visningar, autogenererat engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 63
  bildrutor: omkring 20 är berättarens egen bildspelspresentation ("Part 1–9", 32 sidor), resten inspelningar av
  Claude Design, Antigravity med Claude Code, den byggda sajten på localhost, Google Fonts, Spline, Higgsfield,
  GitHub och Vercel. Rörelsen (hover, skrollavslöjanden, marquee, räknare, 3D-scenen) syns inte i bildrutorna, bara
  lägen. Beskrivningens 30 länkar: kanalens betalgemenskap på Skool, en "free blueprint" bakom Skool-konto, sexton
  affiliatelänkar märkta "some of these make me money", en förkortad Higgsfield-länk, byrån automatable.co,
  konsultbokning, sociala konton och tre egna videor [BESKRIVNING]; inget repo. Inget öppnades, klonades eller
  kördes. Ägarens not: ingen
- Steg: 3 (referenser), 4 (innehåll före form), 5 (5.1 riktning, 5.3 bygg, 5.5 Titta), 6 (prov); lanseringen som
  parkerat ämne
- Jämfört med i dag, metod för metod: (1) **"Steal from Stripe":** skärmdumpar av stripe.com in i Claude Design som
  designsystem, tokens ur getdesign.md:s design.md och en Dribbble-skärmdump för sidstrukturen [TAL 00:32–03:52,
  06:36–07:45; SKÄRM 01:01, 02:00, 03:06, 03:37, 06:51]. Vi: fyra riktningar "härledda ur verksamheten själv …
  aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md` rad 208–209), referensjakt i tre roller med riktiga
  sajter öppnade i 390 och 1440 och "Gallerier är sökingångar, inte facit" (rad 153–165), "Kopiera aldrig layout,
  palett eller typsnitt" (rad 260; `kunskap/referenser-professionella.md` rad 61). getdesign.md är dömt nej som källa
  (`REGISTER-arkiv-20261001.md` rad 896–928) och som metod (HqD5a2Cae60-posten, rad 3128–3132); en
  Dribbble-skärmdump som struktur dömdes sämre i fDTwHIKltpc-posten (rad 3282–3286). Resultatet bär det: Stripes
  indigo, Inter och gradientmesh på en fiktiv SEO-byrå [SKÄRM 08:04, 55:17]. Krockar. (2) **Prototyp först, "pixel
  for pixel":** fem sidor ur en prompt i Claude Design, lämnade till Claude Code med Next.js och Tailwind [TAL
  05:30–06:04, 13:41–14:33; SKÄRM 05:39, 13:43, 14:55]. Texten skrivs av modellen in i formen; Claude Designs egen
  sidopanel listar "Real client logos … (currently text marks)", "Swap placeholder team initials for photos" och
  "Wire the contact form to a real endpoint" som nästa steg [SKÄRM 09:24, 10:04], och efter layoutpasset skriver
  agenten att bilden i första vyn fortfarande är ett platshållarblock [SKÄRM 21:22]. Vi: innehåll före form i
  INNEHALL.md med `Specifikt:` per sektion (rad 172–193), exakt specifikation i KONCEPT.md före kod (rad 215–218),
  inga platshållare (`kunskap/byggstandard.md` 9.4, rad 122), Astro ur mallen (rad 221). Litteraturen: content first
  och progressive enhancement (`kunskap/teoretisk-grund.md` rad 34, 47–48). Sämre. (3) **CLAUDE.md som "senior UI
  designer"** med "premium, modern, elegant interfaces … No emoji icons. No generic gradients" [SKÄRM 13:11; TAL
  12:49–13:09] och front-end-design-pluginet [TAL 13:09–13:41]. Vi: samma officiella skill i
  `kunskap/externa/anthropic-frontend-design-SKILL.md` (rad 198) och, viktigare, modellens standardval uppräknade
  så att bygget väljer bort dem (`kontroller/upptagna_val.py` rad 26–40). Videons sajt är just de valen: Inter,
  färgat accentord "searching", pilleretikett "FREE AUDIT", likadana kort, tre omdömen i rad [SKÄRM 00:32, 14:55,
  59:34, 61:44]; typsnitten som prompten ber om och Claude Design svarar med är Inter, Inter Tight och JetBrains
  Mono [SKÄRM 21:22, 53:40], tre familjer mot byggstandardens högst två (4.3, rad 60). Trots raden "No generic
  gradients" lägger videon sedan på gradienttext, "purple, magenta, and ruby blobs", prickraster, rutnät och glas
  [TAL 25:08–25:43, 31:48–33:28; SKÄRM 30:02, 32:41]. Lika i verktyg, sämre i utfall. (4) **Designordlistan:** sex
  layoutbeslut (riktning, spaltförhållande, bredd, sektionsrytm, padding mot margin, linjering), tre textslag med
  olika typsnittsfamilj per slag, mörkare rubrik och ljusare brödtext, radie, kant och skugga [TAL 17:01–20:44,
  22:56–24:36, 33:28–35:42; SKÄRM 18:09, 19:46, 22:59, 24:36, 33:29, 34:17]. Vi: better-layout, better-typography
  och better-ui på varje sida före JAMFORELSE.md (rad 260–262), dimensionerna 2 och 4 i referenser-professionella
  (rad 20–25), Gestalt och CRAP i teoretisk-grund (rad 62–66). Lika; "olika familj per textslag" säger emot 4.3.
  (5) **Bilder:** stockfoton hämtade av agenten ur Pixabay (bildspelet säger Pexels), också stockansikten på
  omdömena, med berättarens egen brasklapp att man inte ska göra så [TAL 27:54–29:10; SKÄRM 26:29, 29:27, 59:34],
  illustrationer ur Freepik/Magnific [TAL 27:19]. Vi: "Inga stockbilder" (rad 80), det som saknas beställs (rad
  20–24, 235–237; byggstandarden 9.3, rad 121), "hellre inga foton än stock" (`LARDOMAR.md` rad 90), genererade
  eller köpta bilder aldrig som kundens personer (`kunskap/bild.md` rad 19). Krockar. (6) **"The expensive-feeling
  layer" och "make it feel alive":** gradienter, brus, blobbar, glas, hover med skala 1,1 och inverterade färger på
  300 ms, klibbig frostad meny med rullgardin och hamburgare, mörkt läge med knapp, skrollavslöjanden, marquee,
  räknare, shimmer, sidövergångar, en Spline-scen på omkring 5 MB i första vyn och en AI-video på en exploderande
  telefon via Higgsfield-MCP [TAL 30:00–33:28, 37:31–49:38, 49:51–59:08; SKÄRM 31:04, 37:31, 42:22, 45:00, 46:59,
  47:12, 48:49, 53:40, 55:17, 58:30, 59:34]. Vi: ingen JavaScript som inte behövs (rad 225), 0 kB JS i tre dömda
  byggen (`LARDOMAR.md` rad 31, 56, 87), inget rullar av sig självt och reducerad rörelse (byggstandarden 3.5, rad
  50; `mall/astro/src/layouts/Bas.astro` rad 48), högst 200 kB JS (3.7, rad 52), LCP 2,5 s (4.1, rad 58), inga
  tredjepartsresurser (4.4, rad 61), inga karuseller (5.5, rad 73); three.js dömt nej (rad 1550), samma krock som
  PA3f3MdRc08- och Ysr7oNDajJI-posterna fann (rad 3203–3212, 2996–3000). Fokusringen med offset [SKÄRM 40:45] är
  `:focus-visible` hos oss (3.4, rad 49): lika. Krockar med fem medvetna val. (7) **Mobilen sist:** berättaren säger
  att 70 procent kommer på mobil och att man ska designa mobilen först, och gör den som näst sista steg med en
  prompt; mellanvarianten visar menyn ovanpå rubriken i 509 px [TAL 43:33–44:07, 59:44–1:01:23; SKÄRM 43:59,
  60:07], och efteråt "I'm not going to say this is perfect". Vi: mobilen först (rad 224; byggstandarden 3.2, rad
  47), mobilens första vy ur ägarens domar (rad 229–232), inget spill 320–1920 (3.3, rad 48). Litteraturen:
  Wroblewski (2011). Sämre. (8) **Provet:** ögonmått i webbläsaren, "Bypass permissions" på i varje inspelning
  [SKÄRM 21:22, 39:08, 45:36, 59:34]; i sista devtools-bilden visar varningsräknaren ett tresiffrigt tal [SKÄRM
  61:44]. Vi: axe, Lighthouse, standarden, stilrapporten och två oberoende granskare (rad 265–269;
  `kunskap/teoretisk-grund.md` rad 128–129). Starkare hos oss. (9) **Lanseringen:** privat GitHub-repo,
  Vercel-import med Next.js-preset, domän via Vercel eller Namecheap [TAL 1:01:57–1:05:17; SKÄRM 63:21, 64:58].
  Samma väg som byggstandardens Vercel-steg (4.5–4.6, rad 62–63); ägaren har sagt "då väntar vi med det"
  (`BESLUT.md` rad 102) och texten skrivs om i B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den. Inget
  nytt. (10) **Påhittat bevis:** logotyprad med Linear, Ramp, Vercel, Retool, Supabase och Notion, "Compound
  38,047+ search visits a month" som räknare, "Domain Rating +14", fem stjärnor och namn som Emma Reyes och
  Charlotte Voss [SKÄRM 29:27, 48:49, 55:17, 59:34]. Vi: hitta aldrig på fakta, omdömen eller siffror (rad 20–21),
  omdömen bara med källa (9.3), likadana kort i rad som AI-mönster (`kritik/GRANSKARE.md` rad 88). Krockar
- Skäl: videon är en verktygsrundtur och en grundordlista, inte en metod: välj ett varumärkes kläder, låt Claude
  Design rita, be Claude Code kopiera pixel för pixel, lägg på lager av effekter och gör mobilen sist. Det som visas
  är en påhittad SEO-byrå i Stripes indigo med stockansikten, påhittade kunder och siffror, en 3D-scen på fem
  megabyte och en AI-video på en exploderande telefon mitt bland omdömena [SKÄRM 55:17, 59:34]; den hade fallit hos
  granskaren på originalitet, förtroende och substans, och hos ägaren på "känns den gjord för verksamheten". Varje
  metod är antingen redan hos oss (designordlistan, fokusringen, Vercel-vägen), sämre (prototyp före innehåll,
  mobilen sist, ögonmått i stället för prov) eller krockar med ett medvetet val (kopiera Stripe, stock, JS-effekter,
  påhittat bevis). Källkritik: sexton affiliatelänkar, betalgemenskap, byrå och konsultbokning i beskrivningen;
  "10 years, 50 websites" och "20 hours" är berättarens ord [TAL 00:00–00:32, 14:33]; verksamheten är fiktiv;
  beskrivningen säger själv att Antigravity tagit bort Claude Code-tillägget sedan inspelningen [BESKRIVNING].
  Inga instruktioner till agenter i källan
- Kostnad: inget tas in. Berättaren själv: Claude Designs veckokvot tar slut snabbt [TAL 09:25–09:59], Spline-scener
  väger omkring 5 MB per sida [TAL 54:42], Higgsfield kostar från 15 dollar i månaden [TAL 55:19–55:50]
- Säkerhet: ej tillämpligt (video; bara transkript och bildrutor hämtade, inget klonat, kört eller installerat).
  Noterat: körningarna går med behörigheterna avstängda och Higgsfield-anslutningen sätts till "always allow" på
  allt [TAL 57:29–58:03]; inget förs vidare
- Förslag: inget
- Utfall: —
- Backlog: ingen

### 2026-10-03 · Jack Roberts, "Opus 5.5 Just 10X'd Claude Design…" (YouTube HOXrLsVqinY) + ItsssssJack/SlopMonster · nej
- Källa: https://www.youtube.com/watch?v=HOXrLsVqinY @ publicerad 2026-09-24 (Jack Roberts, 22:19, 51 644 visningar,
  autogenererat engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 48 bildrutor:
  berättarens egen sammanställningssida på localhost (sju "levels" med flikar för story, idé, prompt och resultat),
  Firecrawls lekplats, Notion-guiden "The RISE method" (bara rubriker syns), den egna appen "Agentic OS" med Motion
  Library, savee.com, Instagram och GitHub. Rörelsen (loopar, logotypanimationer, jinglar) syns inte i bildrutorna,
  bara lägen; omdömet om rörelsen är berättarens. Beskrivningens nio länkar: tre bit.ly (Firecrawl, "the vault",
  betalsystem med Motion Library), claude.ai, dribbble, savee, pinterest, Glaido (berättarens egen produkt) och ett
  repo [BESKRIVNING]. Repot klonat och förgranskat: https://github.com/ItsssssJack/SlopMonster @ 3fc9787 (senaste
  push 2026-09-26, MIT, 582 stjärnor; videon visar 526 stjärnor och 14 commits [SKÄRM 17:20]); läst README, SKILL.md,
  references/ (tre filer), prompts/cleanse.txt, tools/deslop.py och tools/cleanse.sh i helhet,
  examples/ridgeline-roofing.md, början av examples/jasper-live-run.md och .github/workflows/slop.yml. Inget kört.
  Firecrawl är dömt nej 2026-10-02 (rad 787) och ägaren höll med (`kunskap/KIRURG-OMDOMEN.md` rad 80–83). Ägarens
  not: ingen
- Steg: 4 (innehåll före form), 5 (5.3 bygg), 3 (referenser); bildspel och sociala medier ligger utanför de åtta
  stegen
- Jämfört med i dag, nivå för nivå: (1) **Animerade bildspel** [TAL 00:46–02:14; SKÄRM 00:40, 01:12, 01:44]: en loop
  på tio sekunder att exportera till PowerPoint. Inte en webbplats; inget hos oss motsvarar det och inget behöver
  det. (2) **Varumärke ur en URL med Firecrawl** [TAL 02:28–04:04; SKÄRM 02:49, 03:21, 10:53]: logga, favicon,
  delningsbild, knappar, färger som hex, typsnitt, basenhet, radie och en "personality" med ton och målgrupp. Vi:
  `kontroller/hamta_sajt.py` hämtar deras sidor, `farg.mjs` och `typsnitt.py` läser logotypens färg och typsnitt
  (Firecrawl-posten rad 805–809). Lika i sak; "personality" är en modells gissning om verksamheten, och riktningen
  ska komma "ur verksamheten själv … aldrig ur en branschmall" (`.claude/skills/bygg-sajt/SKILL.md` rad 208–209).
  (3) **Sajter som "kommer till liv"** [TAL 04:04–06:16; SKÄRM 04:26, 04:58, 05:30, 06:02, 07:07, 07:32]: en animerad
  hero på Glaidos sajt med en påhittad blå figur vars tal blir fåglar som blir text, en sidfot som bygger sig själv
  och en produktdemo på 25 sekunder med jingel. Det är dekor i första vyn, en genererad figur i stället för
  verksamhetens egna bilder, och rörelse som startar av sig själv. Vi: första vyn säger vad, var, för vem och nästa
  steg (`kunskap/byggstandard.md` 9.1, rad 119), verksamhetens eget foto i första skärmen (SKILL.md rad 229–231),
  "hellre inga foton än stock" (`LARDOMAR.md` rad 90), genererade bilder aldrig som kundens (`kunskap/bild.md` rad
  19), inget rullar av sig självt och reducerad rörelse (byggstandarden 3.5, rad 50; `mall/astro/src/layouts/Bas.astro`
  rad 48), ingen JavaScript som inte behövs (SKILL.md rad 225). Krockar med fyra medvetna val; ägarens L0 ("ai slope
  skit", `LARDOMAR.md` rad 18) gäller just sådant. Glaidos egen hero-text "Save 20+ hours a month" [SKÄRM 07:07] är
  för övrigt precis det tal utan kvitto som repots bevisregel flaggar (punkt 6). (4) **Reels, B-roll i alla format,
  animerade logotyper med jingel** [TAL 08:13–15:17; SKÄRM 09:16, 09:48, 11:25, 11:57, 12:30, 13:34, 14:07, 14:39]:
  innehåll för Instagram och TikTok, och Notions, Duolingos, Spotifys och Nikes logotyper animerade. Berättaren om
  sitt eget resultat: "I don't like how crowded it is" och typsnittet "has got the clawed fingerprints all over it"
  [TAL 09:16–09:49]. Inte webbplatser. En animerad logotyp vid presentationen för kunden är en tanke för steg 7, men
  våra kunder är en snickare, en målare och en elfirma med ordmärken; en roterande kub av Notions logga [SKÄRM 14:07]
  säger inget om vad Sundboms gula skugga skulle bli, och ägaren dömer sajten, inte presentationen. (5)
  **Stilreferens från Savee till rörelse** [TAL 15:17–18:57; SKÄRM 15:43, 16:16, 16:48, 17:52, 18:25]: en bild ur ett
  galleri och regeln "Borrow the style, never the picture" [SKÄRM 16:48]. Resultaten: ett orange typografiskt kort
  där bokstäverna i RISE faller [SKÄRM 16:48], en 80-talssol som berättaren kallar "goodish, good enough, but not
  perfect" [TAL 17:52–18:00], och en rosa surfplatta med Glaidos adress [SKÄRM 18:25]. Vi: referensjakt med riktiga
  sajter öppnade, "Gallerier är sökingångar, inte facit" (SKILL.md rad 155), "Kopiera aldrig layout, palett eller
  typsnitt" (rad 260; `kunskap/referenser-professionella.md` rad 61). Lika i princip, sämre i utfall. (6)
  **SlopMonster** [TAL 16:55–17:24; SKÄRM 17:20]: en Python-regex över fem kategorier (ordlista, konstruktioner,
  tankstreck och bindestreckskedjor, tretal, tal intill kundsubstantiv) som ger poäng av 5 och avslutar med fel under
  5, och ett skalskript som skickar texten till en annan modellfamilj via Codex- eller Claude-CLI för en andra
  redigering [REPO README.md rad 5–16, 91–101; tools/deslop.py rad 25–45, 76–100, 113–127; tools/cleanse.sh rad
  2–20]. Katalogen är Wikipedias "Signs of AI writing" plus blader/humanizer, samma rot som vår `humanizer`
  (`.claude/skills/humanizer/KALLA.md` rad 3–6; [REPO references/sources.md rad 10–21]). Reglerna är engelska utan
  språkdetektering, "Text in another language can score 5/5" [REPO README.md rad 140–141], så verktyget ser
  ingenting i en svensk sajt. Vi: `kontroller/copy_kontroll.py` med svenska fraser och engelskt läckage (rad 20–39),
  strukturer och saknade element (`kunskap/copy-kontroll.md` rad 10–21), humanizer med röstprov i steg 4 (SKILL.md
  rad 182–193), och fynden är en rapport, aldrig en grind (copy-kontroll.md rad 37–38): ett medvetet val mot
  SlopMonsters felkod. Krockar på grinden, sämre på språket. Två saker i repot är bra: regeln att ett tal intill
  "customers" är det enda felet utan återväg [REPO tools/deslop.py rad 102–104; SKILL.md rad 112–117], och exemplet
  Ridgeline Roofing där en specifikation ("Six nails per shingle") ersätter tre adjektiv [REPO
  examples/ridgeline-roofing.md rad 10–13], vilket är vår "Bara de har" och `Specifikt:` (SKILL.md rad 177–179; L0).
  Den andra modellfamiljen: repot säger självt att det "does not establish that a second model will produce a better
  edit" [REPO references/sources.md rad 44–45]; hos oss går bygge och granskning i samma modell (`kor.sh` rad 8–9)
  men i två granskarsessioner som inte ser varandra (`kritik/GRANSKARE.md` rad 7), och A/B-protokollet kräver redan
  en annan modell som domare (`.claude/skills/kirurg/SKILL.md` steg 6). En andra modellfamilj som copyredaktör
  vore ett A/B, men kedjan i kor.sh har ingen sådan, och källan har inget belägg för att det hjälper; inte nu. (7)
  **Hundra sajter in, hundra filmer ut** och Agentic OS med 103 stilar [TAL 19:08–21:50; SKÄRM 06:18, 06:35, 19:10,
  19:29, 20:02, 20:34, 21:55]: en vägg av logotyper med varsin färgexplosion, och en betald app som skriver prompten
  och öppnar Claude eller Codex. Vi bygger en sajt i taget med dom (kvalitet före volym, kirurgens SKILL.md rad 127);
  en stilkatalog att välja ur är en mall. Krockar
- Skäl: videon handlar om rörlig grafik för bildspel, sociala medier och logotyper, inte om webbplatser åt riktiga
  verksamheter; den enda sajtnivån är en genererad figur som animeras i första vyn på berättarens egen produkt, och
  det är precis det ägaren kallat slop och det byggstandarden stänger ute. Varumärkesuttaget går via Firecrawl som
  redan är dömt nej. SlopMonster är en engelsk regexgrind över samma Wikipedia-katalog som vår humanizer bygger på,
  blind för svenska och med en grindmekanik vi medvetet valt bort. Källkritik: tre affiliatelänkar och en betalprodukt
  i beskrivningen, berättaren använder sin egen produkt Glaido som exempel genom hela videon, "40% cheaper and 30%
  faster" och "one shot" är berättarens ord [TAL 00:00–01:08], och de svagaste resultaten bedöms av honom själv
  ("needs a little bit of work" [TAL 09:16]). Inga instruktioner till agenter i källan; repots SKILL.md är vanlig
  skilltext
- Kostnad: inget tas in. Berättaren: "hundreds of dollars worth of credits" [TAL 00:00–00:34]; Firecrawl-kontot visar
  5 334 krediter kvar [SKÄRM 02:49]. SlopMonster: 66 token i beskrivningen, 1 430 vid användning, 18 774 vid behov
  (förgranskningen); inga beroenden utöver Python
- Säkerhet: videon ej tillämpligt (transkript och bildrutor hämtade, inget kört). SlopMonster förgranskat: MEDEL; inga
  dolda tecken, ingen text riktad till agenter, inga behörigheter eller hookar; fyra skript, varav cleanse.sh läser
  miljön och startar en extern CLI utanför repot, och test_deslop.py använder exec. GitHub-workflowen kör bara
  testerna och lintern. Inget fört vidare
- Förslag: inget för videon eller repot. Egen innovation (backlog nedan): en fyndtyp "siffra" i copykontrollen som
  listar varje tal intill kunder, jobb, år, omdömen och procent med rad, så att det redaktionella passet kan kräva
  kvitto; ingen poäng, ingen grind, egna ord och ingen kod ur källan
- Utfall: —
- Backlog: B-20261003-copykontrollen-rapporterar-varje-siffra-bredvid (egen innovation; för videon och repot: ingen)

### 2026-10-03 · RoboNuggets, "25 Tricks to Level Up Claude Design in 13 Mins" (YouTube _SVU3oC4JX8) · nej
- Källa: https://www.youtube.com/watch?v=_SVU3oC4JX8 @ publicerad 2026-09-27 (Jay E | RoboNuggets, 13:32, 125 944
  visningar, autogenererat engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 41
  bildrutor: omkring 30 är berättarens egna animerade illustrationer med titel, en kort text och en skärmdump i en
  ram (Claude Design, Claude Code, galleri- och biblioteksajter, exempelprompter), fem är berättaren ensam, tre är
  suddiga övergångar [SKÄRM 03:40, 10:50, 11:49], en är en renderingsstörd rubrik [SKÄRM 05:37] och två är sponsorns
  Skool-sidor [SKÄRM 04:38, 04:58]. Rörelsen (SVG-animationen, Lottie, GSAP, motion graphics) syns inte i rutorna,
  bara lägen. Beskrivningens 14 länkar är fem affiliatelänkar (Blotato, n8n, Make, ElevenLabs, Apify), berättarens
  betalgemenskap och en gratisgrupp där PDF-guiden ligger bakom inloggning, den egna produkten Rubric
  (getrubric.app), byråsajten och sociala kanaler [BESKRIVNING]; ingen pekar på ett repo, och ingen öppnades. De
  sajter videon visar (styles.refero.design, 21st.dev, reactbits.dev, canvasui.dev, lordicon.com,
  creatorstoolbox.com, Iconify, Fontshare) öppnades inte heller; reactbits är redan dömt nej (rad 2202). Ägarens
  not: ingen
- Steg: 3 (referenser), 4 (innehåll före form), 5 (5.1 riktning, 5.3 bygg), och arbetssättet runt dem: UPPTAGNA-VAL,
  verktygslådan, "Titta inte på andra byggen"
- Jämfört med i dag, trick för trick i fem grupper: (1) **Designsystem ur andras** (1, 2, 3, 4, 7, 9, 25): Claude
  Design gör ett designsystem av ett deck, en sajt eller en skärmdump [TAL 00:32–01:06; SKÄRM 01:03], ett galleri
  med "2000+ real design systems" från Mercury, Linear och Apple att klistra in [TAL 01:06–01:39; SKÄRM 01:23
  paletter och typskala; SKÄRM 02:02 fyra gallerisajter], låt Claude välja tre ur galleriet för din nisch [TAL
  01:39–02:12; SKÄRM 02:21 Olipop, Graza, sweetgreen med hexkoder], en skill per varumärke ("/Duolingo") [TAL
  02:12–02:45], blanda två system [TAL 03:52–04:25; SKÄRM 04:19 en grön vaneapp], återanvänd förra projektets
  system [TAL 05:30–06:04; SKÄRM 06:16], och sist ett "design operating system" där varje färdig design, bild och
  ikon indexeras för återbruk [TAL 12:28–13:07; SKÄRM 12:48 Rubric Generations, 13:07 Rubric Elements]. Vi: fyra
  riktningar "härledda ur verksamheten själv … aldrig ur en branschmall" och en exakt specifikation i KONCEPT.md
  (`.claude/skills/bygg-sajt/SKILL.md` rad 208–220), "Kopiera aldrig layout, palett eller typsnitt" (rad 260;
  `kunskap/referenser-professionella.md` rad 61), "Titta inte på andra byggen … Varje sajt härleds ur sin egen
  verksamhet" (rad 44), och UPPTAGNA-VAL som visar tidigare val för att inte upprepa dem (rad 203–206). Ägaren
  höll med om nej för samma katalogmekanik i ui-ux-pro-max (`kunskap/KIRURG-OMDOMEN.md` rad 145–147), och
  Duolingo-kopian är redan avfärdad i Jono Catliff-posten (rad 3466). Videons egna resultat visar varför: den
  "blandade" appen är grön med rundade kort och streak-räknare, det vill säga Duolingo [SKÄRM 04:19], och
  biblioteksexemplet är en SaaS-hero med lila knapp och rosa-orange gradientblob [SKÄRM 06:36], ett av de
  standardval stilrapporten varnar för. Krockar med tre medvetna val. (2) **Typsnitt, ikoner och SVG** (5, 16, 17):
  "the fastest way to spot a vibe-coded design is the font", hämta från Fontshare eller Fontesk och namnge i
  prompten [TAL 02:45–03:19; SKÄRM 03:00 Switzer på en kaffesajt]; ladda ner en hel ikonuppsättning i en stil från
  Iconify [TAL 08:18–08:51; SKÄRM 08:33 Lucide, ISC]; be om SVG så att ikoner skalar och kan animeras [TAL
  08:51–09:25; SKÄRM 09:12]. Vi: typsnitt ur verksamheten, självhostade via fontsource med licens bredvid filen och
  registrerade i TYPSNITT-IKONER.json (bygg-sajt rad 38–43; `kunskap/bild.md` rad 74–85), modellens standardtypsnitt
  namngivna så att bygget inte faller tillbaka på dem (`kontroller/upptagna_val.py` rad 37–39), byggstandarden 4.3
  och 3.6 "Ikoner som SVG, aldrig ikonfont" (`kunskap/byggstandard.md` rad 51, 60), favicon.svg ur märket (bygg-sajt
  rad 242). Samma princip, hos oss med mätning i provet. Lika. (3) **Text** (6, 12): be Claude studera "the top five
  players in your niche", lägga deras mönster som copyregler och skriva om sidan [TAL 03:19–03:52; SKÄRM 03:20];
  en tonskill med förbjudna ord plus färdiga regler ur ASD-STE100, Googles utvecklardokumentation och Apples
  stilguide [TAL 06:38–07:10; SKÄRM 06:55]. Vi gör motsatsen på första punkten: FRASER.txt listar branschens
  fraser "som vi därför inte ska använda" (bygg-sajt rad 150–151), "Bara de har" kräver tio saker ingen konkurrent
  kan säga (rad 93–95), och "kunde någon mening stå hos en konkurrent? Skriv om den" (rad 191–192). Tonen: fem
  formuleringar ur deras och kundernas ord som röstprov i humanizer (rad 141, 192–193) och copykontrollen. De
  färdiga guiderna är engelsk teknisk dokumentation; vår måttstock är klarspråk (`kunskap/teoretisk-grund.md` rad
  107). Sämre på nischmönstren, lika på tonen. (4) **Bilder, komponenter och rörelse** (8, 13, 14, 15, 18, 21, 24):
  koppla Claude till en bildgenerator [TAL 05:08–05:30; SKÄRM 05:17 "Hero image placeholder"], 21st.dev-komponenter
  "made to be handed straight to an agent" [TAL 07:10–07:43; SKÄRM 07:34 "Animated Shader Hero", React och WebGL,
  "Trusted by forward-thinking teams"], React Bits [SKÄRM 07:54], Canvas UI med liquid glass, shatter och
  partiklar [TAL 07:43–08:18], Lottie-ikoner [TAL 09:12–09:32], GSAP [TAL 10:31–11:05; SKÄRM 10:50], och
  transkript till motion graphics med Whisper och Hyperframes [TAL 11:49–12:28; SKÄRM 12:08]. Vi: egna bilder eller
  en beställning (bygg-sajt rad 20–24, 76–82), "hellre inga foton än stock" (`LARDOMAR.md` rad 90), genererade
  bilder aldrig som kundens (`kunskap/bild.md` rad 19–20), ingen JavaScript som inte behövs (rad 225), 0 kB JS i
  alla dömda byggen (`LARDOMAR.md` rad 31, 56, 87), byggstandarden 3.5 och 3.7 (rad 50, 52). React Bits är dömt nej
  med ägarens medhåll (rad 2202; KIRURG-OMDOMEN rad 205–208), GSAP tre gånger (rad 3132, 3444), Lottie som
  marknadsplats (rad 2087). Motion graphics gäller video, inte webbplatser. Krockar med fyra medvetna val. (5)
  **Verktyg runt arbetet** (10, 11, 19, 20, 22, 23): ett eget referensbibliotek med skärmdump och not per sparad
  sida, som Claude kan läsa i senare byggen [TAL 06:04–06:38; SKÄRM 06:16 Dribbble, 06:36]; Impeccable [TAL
  06:38–06:55]; Creators Toolbox med 162 resurser [SKÄRM 09:51 Inspova, Camera Shake, BlenderBuddy]; Apples Human
  Interface Guidelines som skill "keep every number" [TAL 09:58–10:31; SKÄRM 10:31]; /design i Claude Code som
  öppnar artboards och känner CLAUDE.md och minnet [TAL 11:05–11:38; SKÄRM 11:29]; en /tweak-skill som lägger
  reglagepanel på en HTML-sida och bakar in värdena [TAL 11:38–11:49; SKÄRM 11:49]. Vi: referensjakt per bygge där
  uppgiften styr urvalet och gallerier är sökingångar (`kunskap/referensjakt.md` rad 7–11, 25–27; bygg-sajt rad
  153–165), REFERENSER.md med vad som faktiskt sågs; Impeccable är taget in och fem mönster mäts i stilrapporten
  (rad 1701; `kontroller/stil.mjs` rad 119–160); träffytor 24 och 44 px, kontrast och WCAG 2.2 AA ur litteraturen
  (byggstandarden 3.3–3.4, rad 48–49) och better-accessibility och better-ui i verktygslådan (rad 3091–3100);
  Creators Toolbox är en länksamling av samma slag som Best-websites, dömd nej (rad 2068). /design och /tweak
  förutsätter en människa som drar i reglage under bygget; hos oss svarar ingen under körningen (bygg-sajt rad 20)
  och ägaren väljer mellan två byggda skärmbilder i riktningsfrågan (rad 340–344); garden-skills Tweaks-panel
  avvisades på samma grund (rad 2978–2980). HIG gäller Apples plattformar och är Apples upphovsrättsskyddade text.
  Lika eller inte tillämpligt. Referensbiblioteket är den enda idén som pekar på något vi saknar, se förslaget
- Skäl: videon är en lista över genvägar för den som designar ensam i Claude Design med en människa vid reglagen, och
  nästan varje genväg är det vi medvetet valt bort: andras designsystem som utgångspunkt, konkurrenternas copy som
  regel, genererade bilder, React- och WebGL-komponenter, GSAP och Lottie, och ett bibliotek där förra kundens
  element återanvänds. Resultaten i bild är Duolingo i grönt och en gradientblob-hero [SKÄRM 04:19, 06:36], alltså
  de standardval vår stilrapport varnar för. Det sakliga, rätt typsnitt, en ikonuppsättning i en stil, SVG, Impeccable,
  har vi redan med mätning i provet. Källkritik: fem affiliatelänkar, betalgemenskap med sponsorblock mitt i [TAL
  04:25–05:08], PDF-guiden bakom inloggning, och Rubric är berättarens egen betalprodukt som bär trick 10 och 25;
  inget resultat är mätt, allt är berättarens omdöme om fiktiva varumärken (hearth, Nexora, Summit, northwind).
  Exempelprompterna i bild [SKÄRM 03:20, 10:31, 11:49] riktar sig till tittaren, inte till kirurgen; videon innehåller
  inga instruktioner riktade till agenter
- Kostnad: inget tas in. Det egna förslaget är några rader i `kunskap/referensjakt.md` utan byggkostnad
- Säkerhet: ej tillämpligt (video; transkript och bildrutor hämtade, inget kört eller installerat, inga länkar
  öppnade)
- Förslag: inget ur källan. Egen innovation, inspirerad av trick 10 (ett referensbibliotek som överlever bygget):
  ägaren har i alla tre domarna pekat ut samma saknade referens, en svensk hantverkarreferens för förtroendeblocket
  (profil på Hantverkskollen, Reco eller Offerta; Elsäkerhetsverkets "Kolla elföretaget" för elfirmor) och två gånger
  en referens för en bärande form (daterad bildserie på mobil, resultat med få bilder) (`LARDOMAR.md` rad 37, 62,
  86), och ingen fil i `kunskap/` eller bygg-sajt nämner dem (sökt). Lägg i `kunskap/referensjakt.md`, efter rad 27,
  ett stycke "Luckor ägaren pekat ut" med de tre, som sökingångar bygget ska pröva i rollen UX/funktion, inte som
  kvot eller facit; bygget öppnar dem som alla andra och skriver vad det såg
- Utfall: —
- Backlog: B-20261003-referensjakt-md-far-ett-stycke-luckor-agaren-pek (egen innovation; för videon: ingen)

### 2026-10-03 · Websites for Normal People (Sebastian Koning), via ägarens genomgång i Google Docs · ta in
- Källa: https://docs.google.com/document/d/1JCZ9XB3wpij6xP1fMPOuX0hANezDWJeYLUy1sHy_brc/edit?usp=sharing, ägarens
  egen genomgång "Websites for Normal People – genomgång av flödet", daterad 2 oktober 2026, "@Johnny" [BILD
  gdoc-html/desktop-forsta.png]; hämtad som mobilebasic-vy med `kontroller/sida.mjs` (77 783 tecken, cirka 19 400
  tokens), hela texten läst och de åtta skrollbilderna sedda (löptext, tabeller och en flödesbild). Originalet:
  https://websitesfornormalpeople.com/ (2026 edition, "Free to read, free to follow", ingen uttrycklig licens [TEXT
  /]), startsidan sedd i mobil och desktop med alla tolv bilder, kapitlen /guide/path-a-the-site (brief och byggprompt)
  och /guide/go-live (lanseringsprompt) lästa i original via WebFetch; de övriga 16 kapitlen, bilagorna och de tre
  jämförelsesidorna bara genom ägarens genomgång. Ägarens not: ingen
- Steg: 3 (brief), 4–5 (innehåll, koncept, bygge), 6 (prov), lanseringen och driften (fas L; `kunskap/forfragan.md`
  "Vid lansering", `kunskap/lansering.md`), och arbetssättet runt dem: kor.sh:s modell, effort och behörighetsläge,
  och hur vi når kunder senare
- Jämfört med i dag, del för del: (1) **Nycklarna och behörigheterna** bär boken: ett valv (Bitwarden Secrets
  Manager) som agenten läser och skriver, en bootstrap-token som låter agenten skapa sin egen Cloudflare-token med
  Edit på alla zoner i ett år, GitHub-inloggning med delete_repo, "Bypass permissions, ja, YOLO-läget" eftersom
  frågandet är "friktion, inte säkerhet", och en sektion i den globala `~/.claude/CLAUDE.md` som varje framtida
  session läser [TEXT kap 04–06; TEXT Bilaga A]. Vi: byggsessionen körs med `--permission-mode dontAsk` (`kor.sh` rad
  47), får inte röra `kontroller/`, `kunskap/`, `kritik/`, `mall/` eller `.claude/` (`.claude/skills/bygg-sajt/SKILL.md`
  rad 48), skickar ingenting ut (rad 51–52), "Ingen agent som arbetar obevakat på systemet" och demosajterna
  publiceras inte (`BESLUT.md` rad 82), och "Ingen session gör DNS-ändringar" (`kunskap/lansering.md` rad 11–17).
  Litteraturen: least privilege och fail-safe defaults (Saltzer & Schroeder 1975; `kunskap/teoretisk-grund.md` rad
  95–101). Ägarens egen genomgång ser samma sak: "en stor sprickradie", "DNS-poster och Cloudflare-resurser har ingen
  ångra-knapp" [TEXT Reflektioner]. Krockar med fyra medvetna val. (2) **Stacken:** Next.js på Cloudflare Workers med
  OpenNext, Payload CMS på D1 och R2, Stripe, GA4 och Tag Manager [TEXT kap 01, 09–11]. Vi: statisk Astro utan
  klientrenderad text, högst 200 kB JS, inga tredjepartsresurser vid sidladdning (`kunskap/byggstandard.md` 1.1 rad
  25, 3.7 rad 52, 4.4 rad 61, avsnitt 11 rad 133–138); 0 kB JS i alla tre dömda byggen (`LARDOMAR.md` rad 31, 56,
  87). Bokens eget råd om CMS, "behöver du verkligen ett? Var ärlig" [TEXT kap 09], säger vi redan i briefen
  (`kunskap/brief-mall.md` §3 rad 32–36). Sämre för hantverkarsajter, lika om CMS. (3) **Briefen** är ett formulär som
  verksamheten fyller i själv: BUSINESS, VISITORS med "the ONE thing you want them to do" och "the questions they
  always ask you before buying", PAGES, THE FEEL med tre ord som inte får vara "modern" och "clean", tre sajter man
  älskar "and what exactly you love about each", MOTION, LANGUAGES, MATERIAL [TEXT /guide/path-a-the-site]. Vi:
  BRIEF.md ur belägg i omdömen och underlag med toppuppgifter i besökarens ord, en primär handling, krav i EARS-form,
  ton som fem formuleringar ur deras egna ord (bygg-sajt rad 126–148), "Bara de har" med tio saker ingen konkurrent
  kan säga (rad 93–95), FRASER.txt (rad 150–151), referenser vi hittar och öppnar själva (rad 153–165), och en
  Visuell tes (rad 219–220). Samma frågor; hos oss besvaras de ur bevis i stället för ur ägarens självbild, för ingen
  människa svarar under körningen (rad 20–24). Lika i sak, vår väg passar vårt flöde. (4) **Byggprompten:** "you're the
  designer here, not just the developer", "take a big swing", skriv DESIGN.md före bygget; hårda nej (gradient-hero,
  "Welcome to", tre likadana kort med ikoner, emoji, stockmänniskor, falska omdömen, lorem ipsum, copy som kunde stå
  hos en konkurrent); saknad fakta blir TODO, "Don't invent them"; innehåll i datafiler skilt från designen; CLS under
  0,1 och 90+ i Lighthouse på staging; reduced motion; "open the staging site yourself, check every page on desktop
  and phone sizes, and fix anything that looks off before you show me" [TEXT /guide/path-a-the-site]. Vi: KONCEPT.md
  med fyra riktningar och exakt specifikation före kod (rad 208–220), hälsningsrubrik och platshållare i copykontrollen
  (`kunskap/copy-kontroll.md` rad 14, 16), "kunde någon mening stå hos en konkurrent? Skriv om den" (rad 191–192),
  mall-lukten i L1 "fyra rubriklänkar med en mening var i två spalter" (`LARDOMAR.md` rad 29), `antagande` och
  BESTALLNING.md i stället för påhitt (rad 20–24), INNEHALL.md före något ritas (rad 177–180), 4.1, 3.5 och 9.4 i
  standarden (rad 58, 50, 122), Titta med skärmbilder i 390 och 1440 (rad 254–264) och två oberoende granskare (rad
  265–278). Samma regler; hos oss mäts de i provet. Lika. (5) **Granska som en kund:** mobilen först, specifik
  återkoppling med varför, i batch, två–tre rundor, och "ny riktning: skriv om DESIGN.md först" när grunden är fel [TEXT
  kap 07]. Vi: ägarens dom i dashboarden med "Efter fem sekunder på startsidan i mobilen" och frågorna parvis med
  skärmbilder (rad 340–344, 374–378), femsekunderstestet avskärmat (rad 299–304), och "Förfina eller byt riktning"
  efter två omgångar under 7 (rad 273–278). Lika. (6) **Formulär och e-post:** Turnstile, "varje inskick sparas i D1
  FÖRST, sedan skickas mejlet, och misslyckas mejlet ska inskicket ändå vara sparat", för "e-post är delen som
  fallerar … Om formuläret bara mejlar är leadet borta och du vet aldrig att det fanns"; befintliga SPF- och
  DMARC-poster slås ihop, aldrig en andra [TEXT kap 08]. Vi: honeypot, tidsfälla, rate limit och Turnstile vid
  lansering (`kunskap/forfragan.md` rad 43, byggstandarden 6.5 rad 88), SPF, DKIM och DMARC (6.6 rad 89), flera
  SPF-poster är ett fynd (`kunskap/lansering.md` rad 59–60). Men vår mottagare svarar "303 till /tack/ först när
  tjänsten har accepterat mejlet. Vid fel: 303 till /fel/, som visar telefonnumret" (forfragan.md rad 46–47; 6.6 rad
  89): förfrågan som skrevs är då borta. Litteraturen: stabilitetsmönster och fail-safe defaults
  (`kunskap/teoretisk-grund.md` rad 52–55), felåterhämtning och försvar i djupled i formulär (rad 80–86). **Bättre**,
  och det är den enda punkten. (7) **Analys:** GA4, Tag Manager, Consent Mode v2 med banner bara i strikta regioner,
  service account via gcloud, Search Console via API [TEXT kap 11]. Vi: "helst kakfri analys utan banner" (8.5 rad
  112), inga tredjepartsresurser (4.4), konverteringsmål och sökkonsol vid lansering (10.1 rad 129). Bokens egen
  startsida visar en kakbanner för Google Analytics över innehållet i mobilens första vy [BILD wfnp/mobil-forsta.png].
  Krockar med ett medvetet val; Search Console lika. (8) **Lanseringen:** custom domains, HTTPS, en lanseringskontroll
  (brutna länkar, unik title och description, en h1, og:image, sitemap och robots för live-domänen, 375 px utan
  horisontell skroll, tangentbord och kontrast, Lighthouse 90+, formuläret skickar, analytics avfyras, schema.org) och
  301 från varje gammal adress [TEXT /guide/go-live]. Vi: 10.3 Definition of Done (rad 131), 7.1–7.3 (rad 97–99),
  301 prövade live med högst fem hopp (`kunskap/lansering.md` rad 92–95), 404 från de gamla ortsidorna i aby
  (`LARDOMAR.md` rad 103). Lika; vår lista är längre men hänvisar till verktyg som inte finns, redan i backloggen
  (B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den). (9) **Modell och effort:** Opus 5.5, "Effort: High för
  setup och första bygget", "Långsammare, men värt det" [TEXT kap 06]. Vi: opus[1m] och effort medium som standard
  efter ägarens blinda A/B där medium vann (`kor.sh` rad 8, 72; `LARDOMAR.md` rad 97–105). Bokens påstående är obelagt,
  vårt är ett mätt par. Lika eller sämre. (10) **Erbjudandet:** 2 000 dollar för allt i boken, en revisionsrunda
  ingår, 500 dollar per extra runda, "gillar du det inte, betala inte" [TEXT kap 14]. Vi har ingen text om pris eller
  revisionsrundor (`kunskap/prospekt-och-utskick.md` nämner bara mötet, rad 9); det är ägarens beslut och noteras
  här, utan förslag
- Skäl: boken är den bästa källan i sitt slag vi sett, en genomtänkt, ärlig och fullständig väg för en ensam
  icke-programmerare som vill ge Claude Code nycklarna och själv kliva åt sidan, och ägarens genomgång har redan gjort
  jobbet att se var den knärrar. Men nästan allt den gör bra gör vi redan, mätt i provet och dömt av ägaren: brief
  före bygge, designriktning före kod, de hårda nejen, inget påhitt, mobilen först, agenten tittar själv, staging före
  produktion, lanseringskontroll och 301. Det som skiljer är medvetna val åt andra hållet: bred åtkomst och
  bypass-läge mot vår låsta session, Next.js på Workers mot statisk Astro utan JS, GA4 med banner mot kakfri mätning,
  effort high mot vårt mätta medium. En princip har vi inte, och den är viktig just för oss: ägaren gjorde den
  skriftliga förfrågan obligatorisk i L1–L3, och vår egen text låter den förfrågan försvinna om mejlet fallerar.
  "Spara först, mejla sedan" är en liten textändring, följer litteraturen om stabilitet och felåterhämtning, och
  rör inte demon. Bokens egen sajt, sedd med egna ögon: hållningen är total (gul-svart parodi på nybörjarböckerna,
  maskoten Keysie [BILD wfnp/desktop-forsta.png]), men brödtexten är satt i displaytypsnittet Luckiest Guy i 20 px
  (`wfnp/SIDA.md` rad 31), mobilens första vy är knapp, skämt och maskot med kakbannern över innehållet [BILD
  wfnp/mobil-forsta.png], och den avsiktliga pastischen är "the big swing" för en bok, inte för en elfirma i Luleå.
  Källkritik: boken säljer ett bygge för 2 000 dollar och Claude Pro, Cloudflare och Bitwarden är valda utan
  jämförelse ("ett verktyg per jobb, inga jämförelsetabeller") [TEXT kap 01]; bevisen för resultaten är författarens
  egna ("en kväll", "40 minuter") [TEXT kap 00, 07]; "14 klick" är 16 rader och "17 prompts" är 16 plus ett
  kommando, som genomgången själv påpekar [TEXT Bilaga A–B]. Inga instruktioner till agenter i något av det lästa;
  bokens prompter riktar sig till läsaren och återges inte här
- Kostnad: några rader i `kunskap/forfragan.md` och en punkt i `kunskap/byggstandard.md`; inga tokens i bygget, ingen
  ny kod förrän Vercel-steget byggs, då lagring och gallring av inskick tillkommer hos värden
- Säkerhet: förgranskningen av genomgångens text och bokens startsida: LÅG, inga dolda tecken, ingen text riktad till
  agenter, inga skript (två körningar av `granska_repo.py`). Genomgången nämner hemligheternas namn men inga värden;
  inget fört vidare
- Förslag: `kunskap/forfragan.md`, "Vid lansering" punkt 5–6: varje giltigt inskick sparas i värdens egen lagring före
  mejlet, med lagringstid som integritetssidan anger och gallring; vid mejlfel säger `/fel/` att förfrågan är
  mottagen och sparad, med telefonnumret som väg vidare, och verksamheten kan hämta sparade inskick. `kunskap/byggstandard.md`
  rad 89, punkt 6.6: "Inskicket sparas före sändning; 'skickat' först när mejlet accepterats; vid fel visas
  telefonnumret och inskicket finns kvar." Demon ändras inte (mottagaren sparar och skickar ingenting, forfragan.md
  rad 25–27; ingen egen databas, `kunskap/formularsakerhet.md` rad 19); lagringen hör till Vercel-steget. Ingen egen
  innovation den här gången
- Utfall: —
- Backlog: B-20261003-mottagaren-vid-lansering-sparar-forfragan-forst

### 2026-10-03 · Jack Roberts, "Claude Design Now Builds Beautiful $10,000 Websites (NO AI Slop)" (YouTube VwGrXe2ricE) + mshumer/Claude-of-Duty · nej
- Källa: https://www.youtube.com/watch?v=VwGrXe2ricE @ publicerad 2026-08-17 (Jack Roberts, 22:17, 241 548 visningar,
  autogenererat engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 53 bildrutor:
  berättarens egen sammanställningssida på localhost:4402 (sex "levels" med tecknade plattor), Refero Styles med
  Duolingos DESIGN.md, Claude Desktop med Opus 5 och Fable 5, den byggda sajten "Neuro" i tre versioner på
  file://, duolingo.com/log-in, Higgsfields MCP-sida, Skool-klassrummet, en Notion-sida "The Design Loop: Free
  Guide", fontsinuse.com och berättarens Hermes-app. Rörelsen (loopande figurer, videor) syns inte i rutorna, bara
  lägen. Beskrivningens tio länkar: fem bit.ly (Glaido med rabattkod, Higgsfield, "how I generated the images", "ALL
  Systems", "Free Skill From Video"), claude.ai, fontsinuse.com, github.com, nousresearch.com och
  styles.refero.design [BESKRIVNING]; förkortningarna gick inte att slå upp (uppslagningen nekades) och Skool-sidan
  kräver medlemskap [SKÄRM 07:56], så skillen "design loop" finns inte att läsa. Notion-sidan hämtad med WebFetch:
  tom (bara rubriken "Notion"). Loopens ursprung enligt Notion-sidan är Matt Shumers "Gauntlet loop" [SKÄRM 08:11];
  originalrepot klonat och förgranskat: https://github.com/mshumer/Claude-of-Duty @ senaste push 2026-07-25 (MIT,
  3 446 stjärnor; commit-id gick inte att läsa, git log nekades), läst prompt.md, README.md rad 70–126 och
  ARCHITECTURE.md rad 168. Inget kört. Ägarens not: ingen
- Steg: 3 (referenser), 4 (innehåll före form), 5 (5.1 riktning, 5.3 bygg, 5.6 granskning), och arbetssättet runt
  dem: granskarna, humanizer, UPPTAGNA-VAL
- Jämfört med i dag, nivå för nivå: (1) **"Hand it a design system, not an adjective"** [SKÄRM 01:31]: hämta en
  annan sajts DESIGN.md ur Refero Styles ("2,000+ real product design systems", [SKÄRM 02:16]) och be Claude bygga
  "the Duolingo of AI" med den [TAL 04:21–05:27; SKÄRM 04:25 Duolingos tokens och typsnitt; SKÄRM 04:57 "risks
  reading as a Duolingo clone"]. Resultatet, sett med egna ögon: utkast ett är duolingo.com/log-in med annat namn,
  samma komposition (illustration vänster, rubrik och två staplade knappar höger, språkremsa i botten), samma rubrik
  "The most fun way to learn …", tomma rutor "HERO ILLUSTRATION" och "SUPER MASCOT ART", och gradienttexten "POWER UP
  WITH SUPER NEURO" [SKÄRM 05:30, 05:47 mot 08:53, 09:15]. Vi: fyra riktningar "härledda ur verksamheten själv …
  aldrig ur en branschmall" och en exakt specifikation i KONCEPT.md (`.claude/skills/bygg-sajt/SKILL.md` rad
  208–217), "Kopiera aldrig layout, palett eller typsnitt" (rad 260), och granskaren straffar mallar och "kunde ett
  annat företagsnamn sättas dit" (`kritik/GRANSKARE.md` rad 86–88). Samma mekanik dömd nej i Jono Catliff-posten
  (rad 3437–3441) och RoboNuggets-posten (rad 3684–3700), med ägarens medhåll om katalogmekaniken i ui-ux-pro-max
  (`kunskap/KIRURG-OMDOMEN.md` rad 145–147). Krockar. Principen bakom, specifikation före kod, har vi redan: "Modellen
  följer uttryckliga specifikationer precist" (rad 217). (2) **Genererade figurer och videor via Higgsfield**
  [TAL 07:03–12:56; SKÄRM 07:39, 10:52 "≈$2/video", 11:07 figurkast]. Slutsajten: tecknade 3D-barn med mobiler,
  en robotuggla, eldflammor och ädelstenar [SKÄRM 11:56, 12:28, 21:04], och i första vyn "4.8 out of 5" samt
  "TRUSTED BY LEARNERS AT" med IBM:s, OpenAI:s, Anthropics, Nvidias och Googles logotyper [SKÄRM 11:56, 21:04], för
  en app som inte finns. Vi: hitta aldrig på omdömen eller siffror (SKILL.md rad 20–22), genererade bilder aldrig
  som kundens (`kunskap/bild.md` rad 19–20), "hellre inga foton än stock" (`LARDOMAR.md` rad 90), förtroende bara
  belagt (`kunskap/byggstandard.md` 9.3, rad 121), "förtroendemärken utan källa" sänker originaliteten och ett
  påstående utan stöd är blockerande (`kritik/GRANSKARE.md` rad 89, 103–104). Berättaren om samma bild: "I'm about
  to get my credit card out" [TAL 15:44]; hos oss hade den fallit på två blockerande fynd. Higgsfield är dömt nej
  två gånger (rad 3220–3223, 3290). Krockar. (3) **Design loop / Gauntlet loop** [TAL 07:54–10:51; SKÄRM 08:11]:
  "Claude Design has taste. It just can't judge its own work", så domarna körs i färska kontexter mot ett "gold
  standard"-exempel tills de godkänner. Shumers original är en prompt på tre stycken: subagenter per del, en "really
  harsh critic" som jämför "side by side blind" med riktiga Call of Duty, loopa tills den är "utterly wowed" [REPO
  prompt.md rad 6–10]. Vi: två granskare i egna sessioner utan byggarens resonemang, "en agent som bedömer sitt eget
  arbete berömmer det även när det är medelmåttigt" (`kritik/GRANSKARE.md` rad 3–8), de får referenserna med
  skärmbilder (rad 27) och betyget 9 betyder "i nivå med de starkaste referenserna" (rad 81); stoppvakten släpper
  inte förrän de godkänt (SKILL.md rad 370–372); litteraturen: en ensam granskare hittar omkring 35 procent, flera
  oberoende omkring 75 (`kunskap/teoretisk-grund.md` rad 128–131). Lika; samma slutsats som loop-posterna (rad
  3414–3431). Shumers egen rapport väger dessutom mot metoden: elva kritiker gav 3,59 till 5,05 av 10, "every critic
  in every round picked the real Call of Duty frame", och "Sequential single-owner passes beat parallel fan-out
  decisively" eftersom isolerade agenter bröt varandras antaganden [REPO README.md rad 89–94, 114–119]. Det stöder
  vårt val av en session per bygge (qLfSDQ5NGh0-posten rad 2662–2665). (4) **Typsnitt** [TAL 13:01–15:29]: "fonts
  change everything", sex fria förslag (Instrument Serif, Switzer, Gambarino, Bricolage Grotesque, Cabinet Grotesk,
  PP Editorial New) och "what the default gives you: Inter, Poppins, Montserrat, Space Grotesk, Playfair Display,
  Roboto" [SKÄRM 13:21]; en väljare i det egna designsystemet med poäng per typsnitt och "RECOMMENDED" [SKÄRM 14:37,
  15:10]; fontsinuse.com som sökingång [SKÄRM 14:05]. Vi: typsnitt ur verksamheten, självhostade med licens
  (SKILL.md rad 38–43; byggstandarden 4.3, rad 60), och modellens standardtypsnitt namngivna så att bygget inte
  faller tillbaka på dem (`kontroller/upptagna_val.py` rad 37–38), en lista som också innehåller videons eget
  förslag Instrument Serif. Ägaren gav Typografi "Bra" i alla tre domarna (`LARDOMAR.md` rad 35, 60, 84). Lika;
  ingen lucka att fylla. (5) **Copysystemet** [TAL 16:49–20:26; SKÄRM 17:19, 17:51, 18:14, 19:27, 20:00]: Wikipedias
  "Signs of AI writing" plus blader/humanizer och harshaneel/humanize [SKÄRM 16:11], en regexlint med "65 words · 8
  shapes" som "exits red below 5/5", en andra modellfamilj (GPT 5.6) som "cleanse", "world-class copy benchmarked
  live against the category's best, headlines quoted verbatim", och fem principer: Don't make me think, name the
  pain first (Priestley), specific or silent, one ask per screen, under five minutes. Före och efter per rad: "Get
  started" → "Start free", "five minutes, wherever you are" → "five minutes on the train counts" [SKÄRM 19:27, 20:00].
  Vi: samma rot i humanizer (`.claude/skills/humanizer/KALLA.md` rad 3–6) med röstprov ur verksamhetens ord (SKILL.md
  rad 192–193), copykontrollen som rapport, aldrig grind (`kunskap/copy-kontroll.md` rad 37–38), Krug i
  måttstocken (`kunskap/teoretisk-grund.md` rad 103), "specific or silent" är vår `antagande`-regel och "Bara de
  har" (SKILL.md rad 20–22, 93–95). Motsatt på en punkt: konkurrenternas rubriker som förlaga mot vår FRASER.txt
  med branschens fraser "som vi därför inte ska använda" (rad 150–151) och "kunde någon mening stå hos en
  konkurrent? Skriv om den" (rad 191–192). Den andra modellfamiljen är redan vägd i SlopMonster-posten (rad
  3638–3642): inget belägg, inte nu. Lika eller krockar. (6) **"One section, one screen, one thought"** [SKÄRM
  20:28; TAL 18:55–19:27]: sektioner i skärmhöjd med en handling var. Videons eget verktyg säger emot: "stretching
  them to a full viewport opens a dead void on tall screens" [SKÄRM 20:28, 08:40]. Vi prövar att nästa sektion
  skymtar i första vyn så att besökaren ser att sidan fortsätter (SKILL.md rad 295–296). Sämre. (7) Hermes-appen
  och "Agentic Operating System" [SKÄRM 16:46; TAL 16:16–16:46] är berättarens betalkurs; inte webbplatser
- Skäl: videons fyra nivåer är var och en antingen redan dömd nej (ett annat varumärkes designsystem som
  utgångspunkt, Higgsfield-genererade figurer), lika med det vi har (oberoende dömare i färsk kontext mot
  referenser, humanizer ur samma Wikipedia-katalog, specifikation före kod) eller motsatt ett medvetet val
  (konkurrenternas copy som förlaga, grind på copypoäng, skärmhöga sektioner). Resultatet sett med egna ögon fäller
  det: utkast ett är Duolingos inloggningssida med nytt namn [SKÄRM 05:30 mot 09:15], och slutsajten har genererade
  figurer, ett betyg utan källa och fem storbolagslogotyper som förtroendemärken för en app som inte finns [SKÄRM
  21:04]; det är precis det ägaren kallade "ai slope skit" (L0, `LARDOMAR.md` rad 18) och det granskaren fäller.
  Källkritik: titelns "$10,000" har inget belägg i videon; fem förkortade länkar varav Glaido är berättarens egen
  produkt och Higgsfield ger rabattkod; skillen ligger bakom Skool-medlemskap; allt omdöme om resultatet är
  berättarens eget ("I'm really, really impressed", "Honestly, I'm 2 seconds away from buying it" [TAL 11:58, 15:44]).
  Loopens upphovsman redovisar själv att metoden förlorade varje blind jämförelse och att parallella agenter gjorde
  resultatet sämre [REPO README.md rad 89–94, 114–119]. Inga instruktioner till agenter i videon; prompt.md i repot är
  en prompt till läsaren, inte till kirurgen
- Kostnad: inget tas in. Berättaren: Higgsfield "≈$2/video" [SKÄRM 10:52]; "lean pilot" 8 generationer, full
  animationspass "20+" [SKÄRM 10:52]
- Säkerhet: videons transkript förgranskat: LÅG, inga dolda tecken, ingen text riktad till agenter. Claude-of-Duty
  förgranskat: MEDEL (173 skript, varav aicost.mjs och bootframes.mjs med eval/exec; inga dolda tecken, ingen text
  riktad till agenter, inga skills, hookar eller behörigheter). Inget kört eller installerat; inget fört vidare
- Förslag: inget. Ingen egen innovation den här gången: de två luckor videon rör (typsnittsval, oberoende dömare)
  har ägaren dömt "Bra" respektive vi har starkare i mekanik
- Utfall: —
- Backlog: ingen

### 2026-10-03 · Self-Made Web Designer (Chris Misterek), "Give Me 7 Minutes & Your Web Design Skills Will Take Off" (YouTube 1NTKwpAVcHg) · nej
- Källa: https://www.youtube.com/watch?v=1NTKwpAVcHg @ publicerad 2025-02-13 (7:14, 467 742 visningar, manuellt
  engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 22 bildrutor: 16 är berättaren i
  bild framför en bokhylla, med textplattor "STOP USING GHOST BUTTONS" [SKÄRM 01:57], "ACCESSIBILITY" [SKÄRM 02:18]
  och "① Clarity ② Scanability" [SKÄRM 05:26]; tre visar andra sajter (SLR:s startsida med serifrubrik, grön yta och
  liten limegrön knapp [SKÄRM 00:33]; Showits startsida med fylld grön knapp "CREATE YOUR SITE" och textlänken "VIEW
  TEMPLATES" under [SKÄRM 04:03]; en vit sida med blå streckillustrationer och ett textstycke [SKÄRM 04:24]); sex
  visar berättarens egen sajt "How to become a web designer fast" på hans skärm, för liten för att läsa knapptexterna
  [SKÄRM 00:54, 01:36, 02:39, 03:42, 05:47, 06:02]. Inget bygge, ingen process, inget resultat att bedöma. De 14
  länkarna i beskrivningen: väntelista för berättarens kurs, hans sajt, sex affiliatelänkar till inspelningsutrustning,
  Showit (affiliate), podcast, Instagram och två egna videor [BESKRIVNING]; ingen öppnad, ingen leder till ett repo.
  Ägarens not: ingen
- Steg: 5 (5.1 riktning, 5.3 bygg, 5.5 titta), 6 (prov), och granskaren
- Jämfört med i dag, punkt för punkt: (1) **Visuell hierarki i stället för F-mönstret** [TAL 00:34–01:43; SKÄRM
  01:15 "YOU'LL READ THIS FIRST / this next / you'll read this last"]: "forcing them to pay attention in an F pattern
  might actually cause them to miss important information" [TAL 00:34]. Vi: luft och hierarki är dimension 4
  (`kunskap/referenser-professionella.md` rad 24–25), varje sida gås igenom med better-layout före JAMFORELSE.md och
  "där allt är lika stort" rättas (`.claude/skills/bygg-sajt/SKILL.md` rad 258–262), gestaltlagar och CRAP i
  måttstocken (`kunskap/teoretisk-grund.md` rad 62–64). F-mönstret står hos oss som skanningsbeteende (Nielsen 2006;
  Redish 2012, rad 89–90), inte som layoutmall; videons "bogus" gäller en halmgubbe och ges inget belägg. Lika i
  sak; källan säger emot litteraturen utan belägg. (2) **Knappen med hög kontrast, inga spökknappar** [TAL
  01:08–01:57]. Vi: better-colors "one primary action gets it and peers stay neutral … A filled button reads as
  primary across the room" (`.claude/skills/better-colors/SKILL.md` rad 71), kontrast 3:1 för gränssnitt
  (`kunskap/byggstandard.md` 3.4, rad 49), primära knappar 44 px (3.3, rad 48), nästa steg på varje sida (9.2, rad
  120). Ägarens tre domar beskriver fyllda knappar: röd, svart, vit på gult (`LARDOMAR.md` rad 30, 55, 79). Lika.
  (3) **Kontrast med coolors.co** [TAL 02:18–02:54]. Vi: axe och inspektionen mäter kontrasten i den byggda sidan
  (byggstandarden 3.4), och lägsta uppmätta kontrast stod i alla tre domarna, 6,86:1, 7,38:1 och 7,5:1
  (`LARDOMAR.md` rad 31, 56, 87). Att pröva paletten i ett externt verktyg före bygget är ett steg mindre exakt än att
  mäta den renderade sidan. Sämre. (4) **60-30-10-regeln** [TAL 02:54–03:29]: 60 procent neutralt, 30 brand, 10
  accent, "especially when you're first getting started". Vi: färgen härleds ur verksamheten med roller som hex i
  KONCEPT.md (SKILL.md rad 208–217), dimension 3 frågar om "varje färgad yta en funktion" och om en accent bär
  handlingarna konsekvent (`kunskap/referenser-professionella.md` rad 22–23), better-colors "one neutral ramp, one
  accent ramp" (rad 38). Ett procenttal är en nybörjarregel; vår fråga är strängare och gäller per yta. Lika eller
  sämre. (5) **Typografi: h1, h2, brödtext utan dekorativt typsnitt** [TAL 03:29–04:24]. Vi: exakt en h1 och
  rubriknivåer utan hopp (byggstandarden 2.1, rad 36), typskala och radlängd i better-typography, dimension 2 "bär
  typsnittens roller hierarkin" (rad 20–21); Typografi "Bra" i alla tre domarna (`LARDOMAR.md` rad 35, 60, 84).
  Lika. (6) **Konvertering: clarity, scannability, motivating** [TAL 04:42–05:47; SKÄRM 05:26]. Vi: första vyn säger
  vad, var, för vem och nästa steg (byggstandarden 9.1, rad 119), femsekunderstestet och Krugs självklara sidor i
  måttstocken (`kunskap/teoretisk-grund.md` rad 103–109), Foggs motivation × förmåga × trigger (rad 105–106). Videons
  anekdot om sajten där "sales plummeted" [TAL 04:38] har ingen uppgift om vad som ändrades. Lika; vi har
  litteraturen bakom, källan en anekdot. (7) **Designa för målgruppen, inte för dig eller kunden** [TAL 05:47–06:21].
  Vi: briefen bygger på kundernas och verksamhetens egna ord och omdömena ersätter JTBD-intervjuer
  (`kunskap/teoretisk-grund.md` rad 16). Lika. (8) **"Never stop learning"** [TAL 06:21–06:55] är ett råd till
  frilansare, inte en metod
- Skäl: videon är sju minuters nybörjarråd utan ett enda byggt resultat att döma, och varje råd finns redan hos oss i
  mer prövbar form: hierarki som dimension och skillgenomgång, fylld primärknapp med mätt kontrast, färgroller per
  yta i stället för procent, rubriknivåer som standardpunkt, första vyn som femsekunderstest. Det enda videon lägger
  till, att F-mönstret är "bogus" [TAL 00:34], säger emot Nielsen (2006) och Redish (2012) i vår måttstock utan
  belägg, och träffar inte oss eftersom vi inte använder F-mönstret som layout. Det som syns på skärmen är tre
  främmande sajter och berättarens egen i oläslig storlek [SKÄRM 00:33, 04:03, 04:24, 00:54], så det finns inget
  att pröva mot de åtta dimensionerna. Källkritik: beskrivningen säljer en väntelista, ett kursbibliotek och
  Showit med affiliatelänk, och sex av fjorton länkar är affiliatelänkar till inspelningsutrustning [BESKRIVNING];
  påståendena är berättarens erfarenhet, inga mätningar. Inga instruktioner till agenter
- Kostnad: inget tas in
- Säkerhet: transkriptet förgranskat: HÖG på grund av ett nollbreddstecken (U+200D) på rad 64 i beskrivningen; läst i
  sammanhang är det fogtecknet i emojin "👨🏼‍💻" före "My favorite website builder", ingen gömd text. Ingen text
  riktad till agenter, inga skript. Inget kört eller installerat; inget fört vidare
- Förslag: inget. Ingen egen innovation: de två ställen videon rör (primärknappens synlighet, hierarki per sida) har
  ägaren redan dömt "Bra" respektive "Okej" i tre byggen, och better-layout är redan inlagd för dimension 4
- Utfall: —
- Backlog: ingen

### 2026-10-03 · Self-Made Web Designer (Chris Misterek), "Complete Web Design Process: What Took Me 10 Years to Learn in 12 Minutes [Free Trello Template]" (YouTube T5JglDcd54A) · nej
- Källa: https://www.youtube.com/watch?v=T5JglDcd54A @ publicerad 2025-02-20 (12:13, 152 273 visningar, manuellt
  engelskt transkript); YouTubes standardlicens. Läst hela tidslinjen och sett alla 41 bildrutor: 27 är berättaren
  framför bokhyllan eller vid sin skärm (tavlan med miniatyrer på skärmen är oläslig [SKÄRM 03:36, 05:57, 07:43, 10:00,
  11:15]); sex är textplattor: processens fyra kolumner "Onboarding · Design & Dev · Launch · Offboarding" med tre
  punkter var [SKÄRM 00:21], "Ask about: their business, hopes & dreams, frustrations with website, frustrations with
  freelancers" [SKÄRM 01:14], "Signed contract, first payment" [SKÄRM 01:50], "24 hours to respond" [SKÄRM 03:18],
  lanseringslistan "Filling out forms, Buying products, Signing up for lead magnets, Checking all links, 100%
  dogfooding" [SKÄRM 09:29] och "Offboarding" [SKÄRM 09:47]; fem är stockfilm (handslag, hoprullade papper, raket,
  hand, kalender [SKÄRM 00:39, 05:22, 09:12, 09:47, 10:58]). Två bilder visar arbete: en Loom-genomgång av en
  startsida för en biståndsorganisation, rubriken "Sometimes hope looks like a telehealth appointment", grön knapp
  "GET INVOLVED", tre foton, berättaren i en bubbla nere till vänster [SKÄRM 06:33]; och ett Google-dokument "Help Docs
  and Training" med Loom-länkar och ett tjugotal länkar till Showits hjälpartiklar grupperade under blogg, länkar,
  bilder, text och PDF [SKÄRM 10:22]. De 17 länkarna i beskrivningen [BESKRIVNING]: Trello-mallen och
  frågeformuläret leder båda till Flodesk-formulär som kräver förnamn och e-post [BILD smwd-trello/desktop-forsta.png,
  smwd-questionnaire/desktop-forsta.png]; inget skickat, så artefakterna är osedda. Episodsidan
  (free-web-design-project-management-template) öppnad och läst: samma innehåll som videon i text, plus verktygen
  Trello, Zoom, Loom och Ruttl och en lanseringslista "Test all forms and buttons, Check for broken links, Run speed
  and SEO audits, Ensure mobile responsiveness, Verify integrations" [TEXT]. Övriga länkar: väntelista, kurs,
  podcast, Instagram, Showit (affiliate), sex affiliatelänkar till inspelningsutrustning, och videon 1NTKwpAVcHg som
  redan är dömd nej (posten ovan, 2026-10-03). Ägarens not: ingen
- Steg: 1 (underlag), 3 (beställningen), 4 (innehåll före form), 5 (startsidan först), 7 (rapporten), lanseringen (L)
  och förvaltningen, samt kundvägen efter prospektmötet
- Jämfört med i dag, punkt för punkt: (1) **Upptäcktssamtalet** [TAL 00:35–01:31; SKÄRM 01:14]: fråga om
  verksamheten, drömmarna, vad som stör med nuvarande sajt och med tidigare frilansare. Vi: ingen människa svarar under
  körningen; underlaget är det publika och kundernas omdömen (`.claude/skills/bygg-sajt/SKILL.md` rad 20–24, 67–95),
  frågebanken i `kunskap/kundintervju.md` täcker åtta områden A–H (rad 48–57), och diagnosen av deras sajt är ribba 1
  (rad 97–118). Lika i sak; vår lista är bredare, videons är tre frågor. (2) **Kontrakt och första betalning före
  arbete, kickoff med tidsfrister åt båda håll, "24 hours to respond" med konsekvens** [TAL 01:45–03:31; SKÄRM 01:50,
  03:18]. Vi: ingen text om pris, avtal eller revisionsrundor; det noterades som ägarens beslut redan vid Websites for
  Normal People (posten 2026-10-03, punkt 10), och prospektflödet slutar vid inbjudan till femton minuter
  (`kunskap/prospekt-och-utskick.md` rad 9; `BESLUT.md` rad 127). Det som verksamheten ska leverera har vi som
  beställning utan frist: `BESTALLNING.md` "skrivet så att verksamheten kan svara på fem minuter" och sajten "inte
  klar att lanseras förrän beställningen är levererad" (SKILL.md rad 144–148, 330–332). Ägarens affärsvillkor, inte
  vårt flöde. (3) **Sajtkarta och "låg lo-fi"-skisser utan designbeslut, eftersom kunden fäster sig vid platshållarens
  typsnitt** [TAL 03:31–05:47; SKÄRM 05:22]. Vi: all text per sida och sektion skrivs i INNEHALL.md innan något ritas,
  med `Specifikt:` per sektion (SKILL.md rad 177–180), sedan KONCEPT.md med fyra riktningar och exakt specifikation
  före kod (rad 208–220). Samma metod, content first (Wroblewski 2011; `kunskap/teoretisk-grund.md` rad 34); hos oss
  ser ägaren riktningarna som skärmbilder parvis (rad 340–344), inte kunden. Lika. (4) **Startsidan först, sektioner
  återanvänds** [TAL 05:47–06:20]. Vi: tvåan byggs "när startsidan står första gången" (rad 246–253), så startsidan
  går först hos oss också. Lika. (5) **Skicka aldrig bara en URL: en Loom som förklarar varför** [TAL 06:20–07:08;
  SKÄRM 06:33]. Vi: rapporten till ägaren med "tre beslut som syns" och frågor parvis med skärmbild och `varfor`
  (SKILL.md rad 316, 340–351). Lika för ägaren; för en kund finns inget ännu. (6) **En revisionsrunda per steg,
  stängda rundor** [TAL 07:08–08:35]. Vi: ägarens affär, se punkt 2; vår egen granskningsloop har ett tak per körning
  (rad 272). Ej jämförbart. (7) **Lansering: fyll i formulären, köp, klicka alla länkar, låg trafik** [TAL
  08:35–09:09; SKÄRM 09:29]. Vi: Definition of Done 10.3 "formuläret prövat hela vägen med mottaget mejl"
  (`kunskap/byggstandard.md` rad 131), demomottagaren 6.3 (rad 86), tabellen Utgående länkar i rapporten (SKILL.md rad
  334–335), 301 prövade live (`kunskap/lansering.md` rad 90–95). Lika; vår lista är mätt, videons är manuell.
  Tidpunkten vid låg trafik saknar vi; liten praktisk regel, ägarens när en lansering kommer. (8) **Offboarding: FAQ
  och Loom per sajt, en nådeperiod, uppföljning för återköp** [TAL 09:09–11:51; SKÄRM 10:22, 10:58]. Vi: README vid
  lansering är utvecklarens (byggstandarden 1.6, rad 30), och underhållsformen i `kunskap/drift.md` (rad 88–100) anger
  vad kunden kan be om efter leverans, men den texten är ärvd från Digitala och pekar på verktyg som inte finns här.
  Videons FAQ-dokument [SKÄRM 10:22] är länkar till Showits hjälpartiklar: kunden redigerar själv i en byggare. Våra
  sajter är statiska utan CMS; motsvarigheten är en kundvänd text om vad som kan ändras och hur man ber om det. Det är
  en lucka, men den ligger i fas L som ägaren väntar med (`BESLUT.md` rad 102), och den är redan i backloggen för
  lanseringstexten (B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den). Uppföljning för återköp är en
  kundvårdsvana, ingen metod. Mot litteraturen: processen följer A.6 "Lansera och lära" i grova drag
  (`kunskap/teoretisk-grund.md` rad 42–43), men utan mätning, DoD eller SUS vid överlämning (rad 114–115); inget i
  videon säger emot måttstocken, inget tillför en metod. Det enda byggda som syns, startsidan vid 06:33, är en
  kompetent men generisk mönstersida (grotesk rubrik, grön knapp, fotokollage); första vyn säger vad och nästa steg,
  mobil osedd. Inget att pröva mot de åtta dimensionerna
- Skäl: videon är en frilansares kundprocess, inte en byggmetod. Allt som rör själva bygget gör vi redan i samma form
  eller strängare: innehåll före form i stället för lo-fi-skisser, startsidan först, förklaringen av besluten i
  rapporten, formulär och länkar prövade i provet. Det som återstår är affärsvillkor (kontrakt, betalning, frister,
  revisionsrundor, uppföljning) som är ägarens beslut och som redan noterats utan förslag, och en kundvänd
  överlämning som hör till lanseringen, där backloggen redan har en post. De två artefakterna som skulle kunnat väga
  tyngre, Trello-mallen och frågeformuläret, står bakom e-postformulär och är inte sedda. Källkritik: beskrivningen
  säljer en väntelista, en kurs och Showit med affiliatelänk, sex av sjutton länkar är affiliatelänkar till
  utrustning [BESKRIVNING]; "double or even triple the lifelong revenue" [TAL 00:00] och "nearly a decade" [TAL
  10:57] är berättarens erfarenhet utan mätning. Inga instruktioner till agenter
- Kostnad: inget tas in. Innovationsposten nedan är några rader i byggstandarden vid lansering, inga tokens i bygget
- Säkerhet: transkriptet förgranskat: tre nollbreddstecken (U+200D) på rad 53, 56 och 71 i beskrivningen; lästa i
  sammanhang är de fogtecknen i emojierna "🙋🏼‍♂️", "👨🏼‍🎨" och "👨🏼‍💻", ingen gömd text. Episodsidans text
  förgranskad: LÅG, inga dolda tecken. Ingen text riktad till agenter, inga skript. Sidverktyget stängde en kakruta med
  "Accept All" på episodsidan; de två Flodesk-sidorna fick inget ifyllt. Inget kört eller installerat; inget fört vidare
- Förslag: inget. Egen innovation, inspirerad av punkt 8: vid lansering får verksamheten en egen sida "Så ändrar du på
  sajten" (vad de kan be om, hur, svarstid, vem som äger domän och konton i kundens ord), som en rad i
  `kunskap/byggstandard.md` 1.6 bredvid utvecklarens README; görs tillsammans med lanseringstextens omskrivning
- Utfall: —
- Backlog: ingen för domen; innovationspost B-20261003-vid-lansering-far-verksamheten-en-egen-sida-sa-a
