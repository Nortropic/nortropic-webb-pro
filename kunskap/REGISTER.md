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
- Utfall: —
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
- Utfall: —
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
