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

### 2026-10-01 · ui-ux-pro-max-skill · prova A/B (avgränsat till steg 6)
- Källa: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill @ `09170ee` (v2.13.0, 2026-09-27), MIT
- Steg: 4–5 (visuell riktning, stackguider) och 6 (checklista, tillgänglighet)
- Sår: Norrglänta-domen "ai slope skit" (LARDOMAR.md L0)
- Överlapp: de 119 UX-riktlinjerna täcker i huvudsak Vercels gränssnittsregler och Osmanis två texter; stil- och
  typsnittsvalet gör samma jobb som Taste och frontend-design, fast som uppslagstabell
- Skäl: kärnan är en designsystem-generator som slår upp bransch → mönster, stil, palett och typsnitt (varje spa får
  Hero, Services, Testimonials, Booking, Contact i rosa och guld). Det är samma mekanism som gör sajter utbytbara, och
  den tar inte in något från den specifika verksamheten. Antimönsterlistan tar bort de grövsta slopmarkörerna, så
  resultatet blir polerad slop. Låg kontextkostnad (16 KB skill plus BM25-sökning över CSV), aktivt underhållen.
  Checklistan och UX-riktlinjerna kan fånga något i steg 6 som våra texter missar.
- Förslag: inget nu. Efter första bygget: kör dess UX-riktlinjer och leveranschecklista mot byggets fynd. De regler som
  fångar något Vercel och Osmani missar tas in som rader i vår egen text, inte verktyget.
- Utfall: väntar på första bygget
- Backlog: B-20261001-prova-ui-ux-pro-max-s-ux-riktlinjer-och-leverans
- Ersatt av: 2026-10-01 · ui-ux-pro-max-skill med förgranskning, repots bilder och uupm.cc

### 2026-10-01 · vercel-web-interface-guidelines · parkera
- Källa: https://github.com/vercel-labs/web-interface-guidelines (lokal kopia
  `kunskap/externa/vercel-web-interface-guidelines-command-e3d624ba.md`, kopierad utan ändring vid repots skapande), MIT
- Steg: 5 (bygge), 6 (prov)
- Sår: inget namngivet i LARDOMAR.md (L0 gäller generiskt innehåll, inte kodnivåns UI-detaljer) och ingen faktisk
  JAMFORELSE.md/RAPPORT.md finns ännu som pekar på det den täcker
- Överlapp: tillgänglighetsavsnittet görs djupare och WCAG-citerat av `addyosmani-accessibility-SKILL.md` (redan i
  kunskap/externa, redan läst via bygge-referens.md); touch-detaljerna (touch-action, tap-highlight-color,
  overscroll-behavior) görs djupare av `emil-mobile-native-SKILL.md` (redan läst i steg 5); prestanda, säkerhet,
  formulärens fel-/tom-/laddningslägen och prefers-reduced-motion står redan i `bygge-referens.md`
- Skäl: ett terse 190-rads kodgranskningskommando skrivet för Vercels egna React/Next-produkter (hydrering,
  URL-synkad state, kontrollerade inputs, listvirtualisering) — de flesta reglerna möter inte mallens Astro-stack
  med minimal klient-JS. En regel krockar rakt med ett medvetet val: "Title Case for headings/buttons (Chicago
  style)" mot copy-kontroll.md:s "rubriker i satsform, inte versaler". Det genuint nya (autocomplete/inputmode/
  spellcheck på formulärfält, placeholders som slutar på "…", varning vid osparad navigering, textöverflöde med
  truncate/line-clamp/min-w-0) är smått men adresserar inget namngivet sår eller gap ännu.
- Förslag: inget nu.
- Utfall: aktualiseras av ett fynd i en riktig byggs renderingsläsning, femsekunderstest eller JAMFORELSE.md
  (dimension 7, mobil ergonomi) som pekar på trasig formulär-UX eller textöverflöde — då tas bara de rader som
  fångar det specifika fyndet in i `bygge-referens.md` eller `formularsakerhet.md`, inte källan som helhet.
- Backlog: ingen
- Not: kopplingsprov av dashboardens intagsfält 2026-10-01, kört med Sonnet 5. Länken skickades av Claude, inte av
  ägaren. Bedömningen står kvar eftersom den är sakligt riktig.
- Ersatt av: 2026-10-01 · vercel-web-interface-guidelines med förgranskning och vercel.com/design/guidelines

### 2026-10-01 · AI LABS-video: sex steg till vackra sajter med Claude Code (Hallmark, design.md, scroll-world, CodeRabbit) · nej
- Källa: https://www.youtube.com/watch?v=DP7mgLUKN_U @ 2026-09-30 (AI LABS, 25:26, autogenererat transkript, sponsrad
  av CodeRabbit). Länkarna lästa i original: nutlope/hallmark @ `13ac0ec` (v1.1.0, MIT) och oso95/scroll-world @
  `71cc36d` (MIT); aura.build och CodeRabbit är kommersiella tjänster
- Steg: 1 och 3 (planläge, affärskontext i CLAUDE.md), 5 (Hallmark, design.md, scroll-world), 6 (CodeRabbit)
- Sår: videon säger sig lösa det som L0 dömer ("ai slope skit"), att AI-sajter ser likadana ut [TAL]; ingen
  JAMFORELSE.md finns ännu
- Överlapp: planläget och affärskontexten gör steg 1 och 3 tunnare än RESEARCH.md med "Bara de har" och BRIEF.md;
  påståendet att Opus alltid väljer krämvitt [TAL] står redan i `anthropic-frontend-design-SKILL.md` (rad 39) och i
  Tastes palettregel (rad 193–207); Hallmarks slop-test (58 grindar) täcks i huvudsak av Taste (eyebrows, Inter,
  lila gradienter, tre lika kort), frontend-design (betonat ord i rubrik, numrerade markörer), Osmanis
  tillgänglighetstext (kontrast, fokus) och bygg-sajts "Hitta aldrig på fakta" (Hallmarks grind 46); design.md som
  format står i `bygge-referens.md`; granskningen är `kontroller/prova.py` och stoppvakten
- Skäl: en nybörjarguide med sponsor och egen betaltjänst (AI LABS Pro) [BESKRIVNING], och beviset för "ser inte
  AI-genererad ut" är berättarens eget omdöme om en enda fiktiv arkitektbyrå [TAL]. Varje grepp finns redan eller
  krockar med ett medvetet val. Hallmark väljer som standard ett av 21 katalogteman och roterar mellan byggen [REPO,
  SKILL.md steg 2.6]; det är samma mekanism som ui-ux-pro-max fick kritik för, och bygg-sajt kräver riktningar
  härledda ur verksamheten, aldrig ur en mall. En nedladdad design.md från aura.build [TAL] är en färdig palett och
  ett färdigt typsnittspar ur ett galleri, rakt emot "Kopiera aldrig layout, palett eller typsnitt". scroll-world
  bygger sidan på AI-genererade dioramor och videoklipp från betaltjänster (Monid eller Higgsfield, ca 27 USD för
  sex scener i 1080p [REPO, README]): ny mekanism, bilder som inte är verksamhetens egna och en skrollmotor i
  JavaScript, mot "Inga stockbilder" och "ingen JavaScript som inte behövs". CodeRabbit granskar pull requests, och
  vi committar direkt på main. Hallmark har nu en licensfil (MIT), så skälet att den utelämnades när repot skapades
  gäller inte längre; domen blir ändå densamma.
- Förslag: inget.
- Utfall: ingen åtgärd. Hallmarks layoutgrindar som saknar motsvarighet hos oss (49 klickbar text på två rader, 50
  `minmax(0, 1fr)` för bildspår, 51 `overflow-wrap` på rubriker, 55 versala rubriker med radhöjd under 1) blir
  aktuella på samma villkor som vercel-posten ovan: när ett riktigt bygge visar textöverflöde eller felbrytning. Då
  tas bara de raderna in i `bygge-referens.md`.
- Backlog: ingen
- Ersatt av: 2026-10-01 · AI LABS-video med bildrutor (Hallmark, design.md, scroll-world, CodeRabbit)

### 2026-10-01 · AI LABS-video med bildrutor (Hallmark, design.md, scroll-world, CodeRabbit) · nej
- Källa: https://www.youtube.com/watch?v=DP7mgLUKN_U @ 2026-09-30 (AI LABS, 25:26, autogenererat transkript, sponsrad
  av CodeRabbit [BESKRIVNING]). Ny bedömning på ägarens begäran, den förra gjordes bara på transkriptet. Sedda: alla 44
  bildrutor i standardkörningen och 24 av 83 i en tätare körning kring resultaten efter steg 1, 3, 4 och 6. Länkarna
  oförändrade sedan förra posten: nutlope/hallmark @ `13ac0ec` och oso95/scroll-world @ `71cc36d`, båda MIT [REPO]
- Steg: 1 och 3 (planläge, affärskontext i CLAUDE.md), 5 (Hallmark, design.md, scroll-world), 6 (CodeRabbit)
- Sår: L0 ("ai slope skit"); videon säger sig lösa just det [TAL 00:00]. Ingen JAMFORELSE.md finns ännu
- Överlapp: som i den ersatta posten. Det resultatet faller på står redan som regel hos oss: krämvit grund med serif
  och lerfärgad accent (`anthropic-frontend-design-SKILL.md` rad 39), versal eyebrow (rad 43; Taste rad 253), Inter
  (Taste rad 169), "Hitta aldrig på fakta" och "Inga stockbilder" (bygg-sajt rad 20 och 47), riktningar härledda ur
  verksamheten (rad 133–135) och "Kopiera aldrig layout, palett eller typsnitt" (rad 148)
- Skäl: bilderna fäller videon på dess egen fråga. Första versionen är krämvit med serif och ett stockfoto av en soffa
  märkt som projektet "Larch Apartment, Portland, Oregon. 2024" [SKÄRM 07:49]; Forma är fiktiv, men processen fyller
  luckor med påhittade verk och stockbilder i stället för att märka dem. Efter Hallmark: benvit grund, stor grotesk
  och ett portföljfilter över sex projekt i sex kategorier (Hospitality, Cultural …) [SKÄRM 11:35] åt en enmanspraktik
  med bostäder som huvudsak [SKÄRM 09:20]. Den design.md som lades in hette `neurosync-master-your-mind-1-DESIGN.md`,
  ett system gjort för en annan produkt ("NeuroSync | Master Your Mind"); Claude noterade bytet och tillämpade det
  [SKÄRM 13:23, 13:41], och sidan blev vit med Inter, pillerfilter och ett stockfoto av ett sovrum [SKÄRM 13:59].
  Slutsajten efter scroll-world är krämvit igen med serifrubrik, versal eyebrow ("IT STARTS WITH THE GROUND"), tre
  pillerchips, mörk pillerknapp och terrakotta aktiv flik [SKÄRM 21:12, 25:07], och accenten `#6f7a5e` [SKÄRM 24:03]
  är första planens moss [SKÄRM 06:53]. Det är exakt det standardval som videon säger att design.md låser bort [TAL
  11:44]. CodeRabbits sammanfattning säger att PR:en "replaces the previous TypeScript project site with a JavaScript
  Next.js site" (78 filer) [SKÄRM 23:26], och repot har en commit "Replace site with the current Forma build" [SKÄRM
  16:42]: slutsajten byggde inte vidare på steg 3–4 utan ersatte dem, så kedjan som säljs syns inte i resultatet. Mot
  de åtta dimensionerna: dioramorna ger en igenkännbar hållning (1) och mobilen får egna 9:16-klipp (7) [SKÄRM
  21:36], men typografi och färg (2, 3) är modellens standard, första vyn är en skrollfilm före allt innehåll (5), och
  förtroendet (6) bärs av AI-genererade hus och en påhittad arkitekt vid ritbordet [SKÄRM 25:07], aldrig av byråns
  egna verk. Konstriktningen väljs ur en meny ("Flat papercraft", "Fly through the world (Recommended for
  dioramas)") [SKÄRM 20:36], inte ur verksamheten. Interaktionen går inte att bedöma ur stillbilder.
- Förslag: inget.
- Utfall: ingen åtgärd. Villkoret i den ersatta posten för Hallmarks layoutgrindar 49–51 och 55 gäller oförändrat.
- Backlog: ingen
- Ersatt av: 2026-10-01 · AI LABS-video med förgranskade repon, usehallmark.com och aura.build

### 2026-10-01 · AI LABS-video: Shopifys Helix-flöde (checkpoints, fyra grindar, orkestrerare) · nej
- Källa: https://www.youtube.com/watch?v=bBMp5tLxShQ @ 2026-09-24 (AI LABS, 14:51, autogenererat transkript, sponsrad
  av Hedra [TAL 06:36]); alla 41 bildrutor sedda. Förlagan läst i original: shopify.engineering/helix (Talha Naqvi,
  2026-09-21). Helix är internt; AI LABS skills ligger bakom deras betalgemenskap [TAL 14:21] och gick inte att läsa
- Steg: 5 och 6 (grindarna), 7–8 (mänsklig granskning, lärdomsfil); orkestreringen berör hela körningen
- Sår: L0 ("ai slope skit"). Ingen JAMFORELSE.md finns ännu
- Överlapp: kroken som säger exit 2 när agenten vill sluta [TAL 05:29, SKÄRM 06:10], videons "change that fixes that
  problem entirely" [TAL 00:32], är vår stoppvakt (`.claude/hooks/stoppvakt.py`, med tak 4 så att ägaren ser ett rött
  avslut). Lärdomsfilen som varje agent läser först [TAL 13:15] är `LARDOMAR.md`. De två UI-granskarna som inte ser
  projektets instruktioner [TAL 11:34, SKÄRM 11:32] är femsekunderstestet i steg 6. Checkpoints i stigande
  svårighet [SKÄRM 03:18] är de åtta stegen i ordning, och jämförelsen mot öppnade referenser i steg 5 gör UI-grindens
  jobb utan en egen mekanik
- Skäl: Helix grindar mäter överensstämmelse med ett känt mål. Hos Shopify är målet den gamla appen, skärm för skärm
  [Shopify-artikeln]; hos AI LABS är det agentens egen HTML-prototyp [TAL 09:54, SKÄRM 10:49]. Vårt sår är att
  målet självt är generiskt, och en grind som jämför sajten med en prototyp den själv ritat släpper igenom det.
  Bilderna visar det: DESIGN.md för "Personnel Ledger" sätter yta `#FBF9F3`, neutral `#F1EDE2` och primär `#2E5A46`
  [SKÄRM 10:28], och resultatet är krämvitt med mörkgrön knapp, versala etiketter över siffror och kolumner
  ("ACTIVE EMPLOYEES", "PERIOD", "STATUS"), monospace-belopp och metasträngar med mittpunkt ("Head of People ·
  People", "STEP 7 · DONE") [SKÄRM 07:34, 10:06, 11:53, 13:41]. Det är punkt 5 och den krämvita grunden ur punkt 1 i
  `anthropic-frontend-design-SKILL.md` rad 39–43, och alla grindar passerades. Kodgranskningsloopen visas bara när
  kritikern godkänner i första rundan utan ändringar [SKÄRM 12:58], och vår sajt är Astro med minimal JavaScript,
  så den adresserar inget vi har sett gå fel. Resten krockar med medvetna val: planen stannar för människans
  godkännande [SKÄRM 14:02] mot "Ingen människa svarar under körningen", och en orkestrerare med fem agenter, egna
  skills och en planvisare är ny mekanik. Källkritik: beviset är en intern demo-app i en sponsrad video, körd med
  `--dangerously-skip-permissions` [SKÄRM 08:40]. Videon säger att Shopify "released their whole setup" [TAL
  02:12], men artikeln beskriver bara metoden och nämner inga misslyckanden.
- Förslag: inget.
- Utfall: ingen åtgärd. Aktuellt på ett villkor: att ägarens dom över ett riktigt bygge pekar på något som
  sessionens egen renderingsläsning (steg 6.3) borde ha sett. Då är grindtanken "granskaren ser inte bygget
  inifrån" värd en rad i steg 6, så att renderingsläsningen görs avskärmad som femsekunderstestet. Ingen ny mekanik.
- Backlog: ingen
- Ersatt av: 2026-10-01 · AI LABS-video om Helix med artikeln sedd som webbsida och ailabspro.io

### 2026-10-01 · Reddit-inlägget "How I Sold 200 Websites in 12 Months" (via Instagram) · nej
- Källa: fyra uppladdade skärmbilder (`kirurgen/uppladdat/20261001T192233Z/01–04`, 2026-10-01 18:29–18:30 lokal
  tid): en Instagram-karusell från kontot artificialintelligenceee som återger r/AI_Agents-inlägget av
  Murky_Explanation_73 ("4mo ago", flair Tutorial). Sedda: bildtexten och karusellens bild 2, 3 och 4 av 4; bild 1
  laddades inte upp. Originalet gick inte att läsa: Reddit skickar både `kontroller/sida.mjs` och WebFetch till
  inloggning, och webbsökningen hittade inte inlägget. Ingen licens
- Steg: 2 (diagnos av nuvarande sajt), 5 (bygge); resten, alltså kundjakt, utskick och SEO-blogg, ligger före och
  efter kedjan
- Sår: inget. L0 gäller kvaliteten i det som byggs, och inlägget säger inget om kvalitet utöver att "clients care way
  more about the final result than how the website was actually made" [BILD 03, 04]
- Överlapp: att leta upp företag och mäta deras sajt för "slow speeds, weak SEO and poor mobile design" [BILD 01] är
  vårt steg 2 (`.claude/skills/bygg-sajt/SKILL.md` rad 60–76: axe, Lighthouse och inspektion i 390 och 1440 px,
  sedan DIAGNOS.md), och före/efter-tabellen i steg 7 (rad 175–176) är det "actual issues on their site" som deras
  utskick bygger på [BILD 03]. "Claude Code for building websites" [BILD 02] är vad bygg-sajt redan är. Tanken att
  göra varje sajt till ett upprepbart system i stället för ett eget projekt [BILD 01] är ägarens egen vision, ordagrant
  i `BESLUT.md` rad 10
- Skäl: det som berör kedjan har vi redan, och det övriga krockar med medvetna val. Automatiserade utskick till
  skrapade företag [BILD 03] går emot "Inget utskick till verksamheterna" (`BESLUT.md` rad 75) och emot ägarens ordning
  att produkten ska vara klar innan vi går till kunder (rad 12). Automatiserad SEO-blogg [BILD 03] är text i volym,
  alltså det L0 dömer, och ingen av våra SEO-texter (`kunskap/seo*.md`) föreslår bloggande. Källkritik: inlägget är
  andrahandsåtergivet av ett Instagramkonto som lever på räckvidd (1 086 gillningar, 699 delningar [BILD 02]).
  Påståendet om 200 sajter av två personer, ungefär fyra i veckan, är obelagt: inga sajter, kunder eller priser visas.
  Inlägget säljer en tes ("The best web designer in the world will eventually lose to some random teenager using AI"
  [BILD 04]) och nämner verktyg för leads, utskick och blogg (Apollo, Swokei, Soro [BILD 02]) som jag inte har
  granskat. Att det rör sig om dold reklam för något av dem kan jag inte belägga. Leveransen mäts i antal sålda sajter,
  inte i om de blev bättre än kundernas gamla, och det är vår ribba 1 (bygg-sajt rad 9).
- Förslag: inget.
- Utfall: ingen åtgärd. När piloten är klar och ägaren vänder sig mot kunder finns underlaget till ett ärligt första
  besked redan: DIAGNOS.md och före/efter-tabellen. Något utskicksverktyg behövs inte för det.
- Backlog: ingen
- Ersatt av: 2026-10-01 · Reddit-inlägget "How I Sold 200 Websites in 12 Months" med swokei.com sedd som webbsida

### 2026-10-01 · ui-ux-pro-max-skill med förgranskning, repots bilder och uupm.cc · nej
- Källa: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill @ `09170ee` (samma commit som den ersatta posten,
  senast pushad 2026-09-27), MIT, 132 297 stjärnor. Ny bedömning på ägarens begäran; den förra gjordes för hand utan
  förgranskning och utan bilder. Läst: README, `.claude/skills/ui-ux-pro-max/SKILL.md`, de 40 första raderna av 119 i
  `ux-guidelines.csv`, `stack/README.md` och exemplet `stack/examples/juniper-audit/` (README och report.md). Sedda:
  `screenshots/website.png`, Juniper-exemplets bilder i 1440 och 390, och demosajten uupm.cc i 390 och 1440 (första
  vyn och sju av åtta skrollägen; läget 0 % är samma som första vyn)
- Steg: 4–5 (designsystem-generatorn: mönster, stil, palett, typsnitt) och 6 (UX-riktlinjer, leveranschecklista,
  `stack/`-delens skärmbildsgranskning)
- Sår: L0 ("ai slope skit"); källan säger sig lösa det ("kills 'AI slop' defaults" [REPO stack/README.md]). Ingen
  JAMFORELSE.md finns ännu
- Överlapp: riktningen ur verksamheten, aldrig ur en branschmall (`.claude/skills/bygg-sajt/SKILL.md` rad 135–136),
  "Kopiera aldrig layout, palett eller typsnitt" (rad 150), "Hitta aldrig på" (rad 20), "Inga stockbilder" (rad 49).
  Det demon faller på står redan som regel: stor siffra med statistik och gradientaccent som standardval
  (`anthropic-frontend-design-SKILL.md` rad 17), likadana kort med gradienttvätt (rad 42), mörk mesh, tre lika kort
  (Taste rad 39), emoji (Taste rad 147–148), gradienttext i stora rubriker (Taste rad 603), påhittade exakta siffror
  (Taste rad 327, 618). UX-riktlinjerna jag läste (fokus, kontrast, alt-text, rubrikordning, träffytor, reduced-motion,
  overflow) står i `bygge-referens.md` rad 11 och 23, i Osmanis två texter och i Vercels regler, och axe och Lighthouse
  mäter dem i `kontroller/prova.py`. `stack/`-delens skärmbilder i flera bredder plus granskare motsvarar steg 5.5 och
  steg 6.3–6.4 (rad 145–150, 160–165)
- Skäl: bilderna fäller källan på dess egen fråga. Demosajten är mörk med blå och orange glöd, gradienttext i varje
  rubrik, sex lika statistikkort och tre lika funktionskort med pillerbrickor [BILD uupm desktop-forsta,
  desktop-skroll-02], och avslutas med en raketemoji över rubriken [BILD desktop-skroll-08] trots att den egna
  checklistan kräver "SVG icons (no emoji)" [BILD desktop-skroll-04]. Siffrorna i första vyn (57 stilar, 95 paletter,
  56 typsnittspar, 8 stackar) [BILD desktop-forsta] motsäger README:s 79, 192, 74 och 22 [REPO README.md rad
  191–197]. Galleriets "real-world website demos" är påhittade verksamheter: PawSpa har en bricka "#1 Pet Spa in
  Town", ett ord i annan färg i rubriken, ett stockfoto av en hund och siffrorna 5,000+, 4.9 och 10+ [BILD
  desktop-skroll-04, -05]; "Transform Data Into Actionable Insights" och "Learn Anything, Anytime, Anywhere!" är
  likadana. Det är generatorns resultat när den gör det den säljs för, och det är L0. Den nya `stack/`-delen påstår
  att en sajt som granskats är "genuinely well-built" och att granskningen hittade det en människa missar vid en
  snabb titt [REPO
  stack/examples/juniper-audit/README.md], men helsidesbilderna har tre tomma band under de två första sektionerna
  [BILD juniper desktop-1440, mobile-390]; rapporten listar fokus, träffytor och kontrast och nämner inte banden [REPO
  report.md], och README:n kallar det ett verktygsfel. Leveranschecklistan bockar av det som syns, inte om sidan
  hör till verksamheten, så den hade släppt igenom demon. Den ersatta postens förhoppning, att riktlinjerna och
  checklistan fångar något i steg 6 som våra texter missar, håller inte: de 40 raderna jag läste är allmän webbpraxis
  vi redan har, och några är tveksamma som regel (mjuk skroll som "High" [REPO ux-guidelines.csv rad 2]). Källkritik:
  repot säljer en premiumversion och betaltjänster via uupm.cc [REPO README.md rad 243–249; BILD desktop-forsta],
  och stjärnantalet är räckvidd, inte belägg.
- Kostnad: SKILL.md, 215 rader, laddas per session, plus referensfiler vid behov; hela repot är ungefär 271 000 tokens text och 152 skript; Python krävs för
  sökningen; `stack/` vill ha tre MCP-servrar via npx
- Säkerhet: förgranskningen gav HÖG. Inga dolda tecken. De två agentriktade träffarna (`cip/generate.py` rad 434) är en
  utskriftsrad till användaren, inte en instruktion. HÖG kommer av skript med nätanrop och miljövariabler i logo-,
  bakgrunds- och katalogskripten och av `stack/.claude/settings.json`, som tillåter `npx playwright` och tre
  MCP-servrar som hämtas med `npx -y …@latest`. Inget kördes
- Förslag: inget
- Utfall: den vilande posten B-20261001-prova-ui-ux-pro-max-s-ux-riktlinjer-och-leverans satt till avvisad ("ersatt av
  ny bedömning 2026-10-01"). Posten B-20261001-rattvis-a-b-provning-med-claude-plugin-eval-pa-s hänvisar fortfarande
  till den avvisade posten i sitt förslag; den hänvisningen gäller inte längre. Juniper-exemplet visar en sak att
  hålla ögonen på: innehåll som tonas in vid skroll syns inte i en helsidesbild. Blir det ett fynd i ett riktigt
  bygge (tomma band i `-hela.png`), hör det hemma som en rad i steg 6.3, inte som det här verktyget
- Backlog: ingen

### 2026-10-01 · vercel-web-interface-guidelines med förgranskning och vercel.com/design/guidelines · parkera
- Källa: https://github.com/vercel-labs/web-interface-guidelines @ `e3d624b` (senast pushad 2026-08-18), MIT, 917
  stjärnor. Ny bedömning på ägarens begäran; den förra var ett kopplingsprov med Sonnet. Läst i sin helhet: README.md
  (198 rader), command.md (190), AGENTS.md (155) och install.sh (144). Sedda: vercel.com/design/guidelines i 390 och
  1440 (första vyn) och ett skrolläge av åtta; sidan är README:n renderad, mörk Geist-typografi utan bilder [BILD
  desktop-forsta, mobil-forsta, desktop-skroll-04]. Upstreams command.md är samma commit som vår lokala kopia
  (filnamnets `e3d624ba`)
- Steg: 5 (bygge) och 6 (prov); command.md är ett granskningskommando för kod, AGENTS.md samma regler i MUST/SHOULD-form
- Sår: inget. L0 ("ai slope skit") gäller generiskt innehåll och generisk form; källan handlar om hantverket i
  komponenterna och säger inget om huruvida sajten hör till verksamheten. Ingen JAMFORELSE.md finns ännu
- Överlapp: tillgänglighet och fokus i `bygge-referens.md` rad 9–13 (WCAG 2.2 AA, synligt fokus, hopp-länk, Escape)
  och Osmanis text som den pekar på; bilder med mått, prioriterad första bild, självhostade typsnitt rad 14–15;
  formulärens fel-, tom- och laddningslägen rad 19; `prefers-reduced-motion` rad 23; 404 med nästa handling rad 24.
  Mobilreglerna (16 px i fält, `touch-action`, tap-highlight, `overscroll-behavior`, safe areas, `type` och
  `inputmode`) står djupare i `emil-mobile-native-SKILL.md` rad 44–51, 102–128 och 118, som steg 5 läser
  (`.claude/skills/bygg-sajt/SKILL.md` rad 133). Spill mäts som grind i 390, 768 och 1440 (`kontroller/prova.py`
  rad 11), axe och Lighthouse rad 9–10. Vår kopia av källan, `kunskap/externa/vercel-web-interface-guidelines-command-e3d624ba.md`,
  laddas däremot inte av något steg: utanför registret nämns den bara i `.claude/skills/kirurg/SKILL.md` rad 104
- Skäl: källan är god, saklig och gratis, men den svarar på en annan fråga än vårt sår. Den är skriven för Vercels
  egna React- och Next-produkter (hydrering, URL-synkad state, kontrollerade fält, virtualiserade listor, `POST`
  under 500 ms [REPO command.md rad 95–100, 130–134; README.md rad 117]), och mallen är Astro med minimal JavaScript
  (`mall/astro/src/layouts/Bas.astro`). Det som gäller en informationssajt har vi redan i texter som laddas. Två
  rättelser av den ersatta posten: krocken med "rubriker i satsform" (`kunskap/copy-kontroll.md` rad 30) finns bara i
  command.md ("Title Case for headings/buttons" [REPO command.md rad 144]); README:n märker copyreglerna som
  Vercel-specifika och skriver "On marketing pages, use sentence case." [REPO README.md rad 145, 151], så för våra
  sajter finns ingen krock. Och `type`/`inputmode` är inte nytt, det står i Emil rad 118. Det som verkligen saknas
  hos oss är småt: `autocomplete` och meningsfulla `name` på formulärfält, `spellcheck` av på mejlfält, placeholder
  som exempel, `text-wrap: balance` på rubriker, `scroll-margin-top` under en klistrad meny och `min-w-0` på
  flexbarn [REPO command.md rad 39–47, 69, 25, 74]. Inget av det har ett bygge ännu visat fel på. Källkritik:
  källan säljer inget utom en rekryteringsrad [REPO README.md rad 191–193]; reglerna är praxis, inte belagda med
  mätningar, och några hänvisar till tweets som belägg [REPO README.md rad 23, 42, 53].
- Kostnad: command.md 190 rader om den skulle laddas i steg 6; hela repot ungefär 8 700 tokens text. Inga beroenden.
  Installationsvägarna (install.sh, `npx skills add`) behövs inte; vi har redan texten
- Säkerhet: förgranskningen gav MEDEL, enbart för install.sh: den hämtar command.md med curl och skriver i
  användarens kataloger för sju agentverktyg, bland annat `~/.claude/commands/` och Windsurfs globala regler [REPO
  install.sh rad 35–41, 59–76]. Inga dolda tecken, ingen text riktad till agenter; sidtexten fick LÅG. Inget kördes
- Förslag: inget
- Utfall: villkoret i den ersatta posten gäller, preciserat. Visar ett riktigt bygge trasig formulär-UX (autofyll
  som inte fungerar, fel tangentbord, fel som inte syns vid fältet) eller dåliga radbrytningar i rubriker, tas
  bara de raderna ur listan ovan in i `kunskap/bygge-referens.md` rad 19 respektive i formulärkravet i
  `kunskap/formularsakerhet.md`, med svenska ord. Att vår kopia ligger oläst är ingen brist i sig; den är
  uppslagsmaterial för kirurgen, inte byggets text
- Backlog: ingen

### 2026-10-01 · AI LABS-video med förgranskade repon, usehallmark.com och aura.build · nej
- Källa: https://www.youtube.com/watch?v=DP7mgLUKN_U @ 2026-09-30 (AI LABS, 25:26, autogenererat transkript, sponsrad
  av CodeRabbit [BESKRIVNING]). Ny bedömning på ägarens begäran med den uppgraderade kirurgen; de två tidigare
  posterna saknade förgranskning och sidorna sedda som webbsidor. Sedda: hela tidslinjen och alla 44 bildrutor.
  Repona förgranskade och lästa: nutlope/hallmark @ `13ac0ec` (v1.1.0, senast pushad 2026-08-06, MIT, 29 394
  stjärnor; SKILL.md i sin helhet, slop-test.md grind 49–55) och oso95/scroll-world @ `71cc36d` (senast pushad
  2026-07-29, MIT, 9 624 stjärnor; README). Sidor sedda i 390 och 1440: usehallmark.com (första vyn och sju av åtta
  skrollägen), aura.build (första vyn och tre skrollägen) och dess design.md-galleri aura.build/design-systems (första
  vyn och ett skrolläge). Videons slutsajt forma-site-flame.vercel.app svarade 503 `DEPLOYMENT_PAUSED` [BILD forma
  desktop-forsta], så den kunde inte ses på riktigt; ailabspro.io, theroundup.so och CodeRabbit öppnades inte
- Steg: 1 och 3 (planläge, affärskontext i CLAUDE.md), 4–5 (Hallmark, design.md, scroll-world), 6 (CodeRabbit)
- Sår: L0 ("ai slope skit"); videon säger sig lösa just det [TAL 00:00]. Ingen JAMFORELSE.md finns ännu
- Överlapp: som i de ersatta posterna. Det resultatet faller på står redan som regel: krämvit grund med serif och
  lerfärgad accent samt versal eyebrow och mittpunktssträngar (`kunskap/externa/anthropic-frontend-design-SKILL.md`
  rad 39 och 43), Inter som standardval (Taste rad 39 och 169), riktningar härledda ur verksamheten och aldrig ur en
  branschmall (`.claude/skills/bygg-sajt/SKILL.md` rad 135–136), "Kopiera aldrig layout, palett eller typsnitt" (rad
  150), "Hitta aldrig på" (rad 20) och "Inga stockbilder" (rad 49). Hallmarks mobilgolv i fyra bredder motsvaras av
  spillgrinden i 390, 768 och 1440 px (`kontroller/prova.py` rad 11)
- Skäl: de nya källorna fäller verktygen på deras egna regler. usehallmark.com har numrerade versala monospace-etiketter
  över varje rubrik ("02 / EXAMPLES" till "07 / INSTALL") [BILD usehallmark desktop-forsta, desktop-skroll-03, -06,
  -07], fast skillen säger att sådana etiketter är av som standard [REPO SKILL.md rad 450]. Sidans exempel på
  Hallmarks resultat har ett kursivt betonat ord i rubriken ("after dark.", "at a price", "made") [BILD desktop-skroll-07,
  -04], fast skillen kallar just det ett av de säkraste AI-tecknen [REPO SKILL.md rad 56]; bildtexten "Real bottle, real
  grape, real region" står under en utvecklarkonferens [BILD desktop-skroll-07]. Sidan säger 20 teman och 57 grindar
  [BILD desktop-forsta, -08], skillen 21 och 58 [REPO SKILL.md rad 38, 344]. Kärnan är oförändrad: ett av 21
  katalogteman väljs tyst och roteras mellan byggen [REPO SKILL.md rad 38, 240], mekanismen som ger utbytbara sajter.
  aura.build är en mallbutik med betalmallar ($24.99–$39) [BILD aura desktop-skroll-06], och design.md-galleriet visar
  Inter i både rubrik och brödtext på de flesta kort [BILD aura-ds desktop-skroll-04] och säljer att man gör en
  design.md av någon annans sajt [TEXT aura-ds], rakt emot rad 150 ovan; Hallmarks egen study-verb vägrar mallbutiker
  [REPO SKILL.md rad 28]. Videon själv: den design.md som lades in var `neurosync-master-your-mind-1-DESIGN.md`, ett
  system för en annan produkt [SKÄRM 13:38]. Slutsajten är krämvit med serifrubrik, versal eyebrow ("BUILT TO
  BELONG"), "05 / 05" och mörka pillerknappar [SKÄRM 21:36], och accenten `#6f7a5e` [SKÄRM 24:03] är första planens
  moss bredvid Fraunces och Inter [SKÄRM 06:53]: modellens standardval, inte verksamhetens. Förtroendet bärs av en
  AI-genererad arkitekt vid ritbordet [SKÄRM 25:07]. Flera bilder är animerade illustrationer, inte inspelningar
  [SKÄRM 05:35, 12:24, 18:18], och de motsäger inspelningarna: den ritade PR:en ändrar två filer [SKÄRM 22:49], den
  riktiga 78 filer, +1 609 −1 608 rader, och ersätter hela den tidigare sajten [SKÄRM 23:26]; körningen av "första
  versionen" serverar redan scroll-worlds `/world/scrub-engine.js` [SKÄRM 07:30]. Inspelningarna körs med "bypass
  permissions on" [SKÄRM 04:26, 17:55]. CodeRabbit granskar pull requests, och vi committar direkt på main.
  scroll-world kräver betalda bild- och videotjänster (Monid eller Higgsfield, ca 27 USD för sex scener [REPO
  README.md]) och ger AI-genererade bilder i stället för verksamhetens egna.
- Kostnad: Hallmarks SKILL.md, 559 rader, laddas per session, plus sex regelfiler per bygge och slop-testet (omkring
  7 000 tokens enligt skillen själv [REPO SKILL.md rad 381]); hela repot ungefär 203 000 tokens text. scroll-world
  ungefär 21 000 tokens, ffmpeg, Pillow och krediter per klipp. aura.build och CodeRabbit är betaltjänster
- Säkerhet: förgranskningen gav MEDEL för båda repona, inga dolda tecken och ingen text riktad till agenter. Hallmarks
  träffar är falsklarm: `curl | sh` står som synlig text i en exempelsida för ett påhittat CLI
  (`site/_tests/02-streampipe-cli/index.html`), och "miljö" i `custom-05/script.js` är en funktion som heter
  envelope. scroll-world ger sig själv Bash, Write, Edit och Skill i frontmatter; `knockout.py` läser en tröskel ur
  miljön och `scrub-engine.js` hämtar videofiler med fetch. Sidtexterna fick LÅG. Inget kördes
- Förslag: inget
- Utfall: ingen åtgärd. Villkoret för Hallmarks grindar 49–51 och 55 (klickbar text på två rader, `minmax(0, 1fr)` för
  bildspår, `overflow-wrap` på rubriker, versala rubriker med radhöjd under 1) gäller oförändrat: visar ett riktigt
  bygge felbrytning eller överflöd, tas bara de raderna in i `kunskap/bygge-referens.md`
- Backlog: ingen

### 2026-10-01 · AI LABS-video om Helix med artikeln sedd som webbsida och ailabspro.io · nej
- Källa: https://www.youtube.com/watch?v=bBMp5tLxShQ @ 2026-09-24 (AI LABS, 14:51, autogenererat transkript, sponsrad
  av Hedra [BESKRIVNING]). Ny bedömning på ägarens begäran med den uppgraderade kirurgen; den förra posten hade inte
  sett artikeln som webbsida och var inte förgranskad. Sedda: hela tidslinjen och alla 41 bildrutor; 14 av dem är
  skärminspelningar av editor och terminal, resten animerade illustrationer, sponsorklipp och en bild av artikeln.
  Sidor sedda i 390 och 1440: shopify.engineering/helix (Talha Naqvi, 2026-09-21; första vyn och sju av åtta
  skrollägen, hela texten) och ailabspro.io (första vyn, texten). Helix är internt och AI LABS skills ligger bakom
  betalgemenskapen, så det fanns inget repo att läsa. Ingen licens
- Steg: 5 och 6 (grindarna), 7–8 (mänsklig granskning, lärdomsfil); orkestreringen berör hela körningen
- Sår: L0 ("ai slope skit"). Ingen JAMFORELSE.md finns ännu
- Överlapp: kroken som svarar exit 2 när agenten vill sluta [TAL 05:29, SKÄRM 06:10], videons ändring som "fixes that
  problem entirely" [TAL 00:32], är vår stoppvakt (`.claude/hooks/stoppvakt.py` rad 6–7; `.claude/skills/bygg-sajt/SKILL.md`
  rad 210–211). Minnet där ingenjörens återkoppling förbättrar varje senare checkpoint [TEXT shopify, Gate 4] är
  `LARDOMAR.md` och steg 8 (bygg-sajt rad 215–217). De två UI-granskarna som inte ser projektets instruktioner [TAL
  11:34] motsvaras av femsekunderstestet (rad 162–165). Checkpoints i stigande svårighet [SKÄRM 03:18; TEXT shopify,
  "Checkpoints that can be reviewed at a glance"] är de åtta stegen i ordning, och artikelns "one decision they can
  make as opposed to ten pages they will skim" [TEXT shopify] står hos oss som rapporten "kort och ärligt" (rad 170) och
  ägarens frågor som parvisa val (rad 187–188)
- Skäl: Helix grindar mäter överensstämmelse med ett känt mål, och vårt sår är att målet självt är generiskt. Hos
  Shopify är målet den gamla appen: "The reference is the spec", och UI-grinden är skälet till att resultatet blir
  "so close to 1:1" [TEXT shopify]. Vi ska tvärtom aldrig kopiera layout, palett eller typsnitt (bygg-sajt rad 150).
  Hos AI LABS är målet agentens egen HTML-prototyp ur samma DESIGN.md [TAL 09:54, 10:28; SKÄRM 10:49], och bilderna
  visar vad det släpper igenom. DESIGN.md beskriver systemet som "a well-kept personnel office, not a SaaS dashboard"
  och sätter yta `#FBF9F3` och primär `#2E5A46` [SKÄRM 10:28]; appen har fyra statistikrutor med stora siffror under
  versala etiketter, ikonmeny och mörkgrön knapp [SKÄRM 10:06], versala tabellrubriker, monospace-belopp och
  "STEP 6 · IN PROGRESS" [SKÄRM 11:53], och UI-grinden är bockad som "Looks right" [SKÄRM 11:53]. Det är punkt 1 och 5 i
  `kunskap/externa/anthropic-frontend-design-SKILL.md` rad 39 och 43 och versala etiketter på rad 27. Grinden jämför
  appen med prototypen, inte med avsikten, så avsteget från filens egen mening syns aldrig. Kodgranskningsloopen visas
  bara i ett fall där kritikern godkänner i första rundan utan ändringar och UI-grinden är "n/a" [SKÄRM 12:58], och vår
  sajt är Astro med minimal JavaScript. Resten krockar med medvetna val: planen stannar för människans godkännande
  ("Approve the plan?" [SKÄRM 05:05]) mot "Ingen människa svarar under körningen" (bygg-sajt rad 20), och en
  orkestrerare med fem agenter och sex skills [SKÄRM 03:40, 11:10] är ny mekanik. Artikeln säger att grindarna inte
  slappnar när ingen tittar och att agenten får försöka hur många gånger som helst [TEXT shopify]; vår stoppvakt släpper
  medvetet efter fyra försök så att ägaren ser ett rött avslut (stoppvakt.py rad 7 och 72). Källkritik: artikeln är en
  rekryteringstext ("We're hiring" vid sidan av hela texten [BILD shopify desktop-skroll-02]) utan siffror för
  kvalitet, tid eller antal omförsök och utan ett enda misslyckande. Videon säger att Shopify "released their whole
  setup" [TAL 02:12], men artikeln beskriver bara metoden. Inspelningarna körs med `--dangerously-skip-permissions`
  [SKÄRM 05:05, 09:02, 12:58]. Videon säljer sina skills genom AI Labs Pro [TAL 14:21], kr200 i månaden [TEXT
  ailabspro], och bilden av att man bara ber Claude skriva orkestreraren är en animation, inte en inspelning [SKÄRM 14:24].
  Två rättelser av den ersatta posten: flaggan syns inte vid 08:40 (där visas test-planners SKILL.md) och
  godkännandestoppet visas vid 05:05, inte 14:02
- Kostnad: inget att ladda; Helix går inte att få. AI LABS uppsättning är fem agenter, sex skills och en krok, bakom
  betalvägg; en egen motsvarighet vore ny mekanik med underhåll
- Säkerhet: förgranskningen av artikelns och ailabspro.io:s text gav LÅG, inga dolda tecken och ingen text riktad till
  agenter. Inget repo att förgranska. Inget kördes
- Förslag: inget
- Utfall: ingen åtgärd. Villkoret i den ersatta posten gäller oförändrat: pekar ägarens dom över ett riktigt bygge på
  något som renderingsläsningen i steg 6.3 (bygg-sajt rad 160–161) borde ha sett, blir "granskaren ser inte bygget
  inifrån" en rad i steg 6, så att läsningen görs avskärmad som femsekunderstestet. Personnel Ledger-exemplet visar
  också en sak att hålla ögonen på: KONCEPT.md kan säga en sak och sajten en annan. Blir det ett fynd i ett riktigt
  bygge, hör det hemma som en rad i steg 5.5 (jämför sajten med KONCEPT.md:s egna ord), inte som en grind
- Backlog: ingen

### 2026-10-01 · Reddit-inlägget "How I Sold 200 Websites in 12 Months" med swokei.com sedd som webbsida · nej
- Källa: fyra uppladdade skärmbilder (`kirurgen/uppladdat/20261001T195500Z/01–04`, samma som i den ersatta posten): en
  Instagram-karusell från artificialintelligenceee som återger r/AI_Agents-inlägget av Murky_Explanation_73 ("4mo
  ago", flair Tutorial). Sedda: bildtexten [BILD 01] och karusellens bild 2, 3 och 4 av 4 [BILD 04, 03, 02]; bild 1
  laddades inte upp. Originalet hittades inte: webbsökning på rubriken gav inget, och Reddit spärrade förra gången med
  inloggning. Ny i den här bedömningen: swokei.com, det enda verktyget i inlägget som beskrivs i detalj, sedd som
  webbsida 2026-10-01 (omdirigerad till den svenska versionen /sv): första vyn i 390 och 1440, skrolläge 2, 4 och 7 av
  8, och hela texten. Ingen licens
- Steg: 2 (diagnos av nuvarande sajt), 5 (bygge); kundjakt, utskick och SEO-blogg ligger utanför kedjan
- Sår: inget. L0 gäller kvaliteten i det som byggs, och inlägget säger bara att "clients care way more about the final
  result than how the website was actually made" [BILD 03, 02]
- Överlapp: att hitta företag och mäta deras sajt för "slow speeds, weak SEO and poor mobile design" [BILD 01] är steg 2
  (`.claude/skills/bygg-sajt/SKILL.md` rad 60–74: axe, Lighthouse och inspektion i 390 och 1440, sedan DIAGNOS.md med
  "vad som hindrar toppuppgifterna"). Swokeis analys, "design och layout till laddningstid, mobil och SEO, läses sida
  för sida i en riktig webbläsare" [TEXT swokei], är samma sak. Exempelmejlets fynd, att offertdelen ligger långt ner
  på mobilen och att bilderna laddas i full storlek [TEXT swokei], är just den sortens rad som DIAGNOS.md redan ska
  innehålla. Före/efter-tabellen i steg 7 (rad 175–176) är vårt "actual issues on their site" [BILD 03]. "Claude Code
  for building websites" [BILD 02] är bygg-sajt. Ett upprepbart system i stället för ett eget projekt per sajt [BILD 01]
  är ägarens egen vision (`BESLUT.md` rad 10)
- Skäl: det som berör kedjan har vi redan, och resten krockar med medvetna val. Automatiserade utskick till skrapade
  företag [BILD 03] går emot "Inget utskick till verksamheterna" (`BESLUT.md` rad 75), mot "Inget skickas ut" (bygg-sajt
  rad 30) och mot ägarens ordning att produkten ska vara klar innan vi går till kunder (`BESLUT.md` rad 12).
  Automatiserad SEO-blogg [BILD 03] är text i volym, alltså det L0 dömer; inget i `kunskap/seo*.md` eller
  `kunskap/lokal-synlighet.md` föreslår bloggande. Swokeis sajt visar dessutom vad "personalized outreach" betyder i
  praktiken: varje exempelmejl öppnar med en påhittad personlig förevändning, till exempel att avsändaren letade efter
  en födelsedagstårta på South Congress och fastnade på bageriets sida [TEXT swokei]. Det är motsatsen till "Hitta aldrig
  på fakta" (bygg-sajt rad 20–21). Källkritik: inlägget är andrahandsåtergivet av ett räckviddskonto (1 086
  gillningar, 699 delningar [BILD 02]), och 200 sajter av två personer på ett år är obelagt: inga sajter, kunder eller
  priser visas. Inlägget räknar upp fem verktyg [BILD 02], men det längsta stycket beskriver i detalj det som Swokei
  står för, "website analysis and outreach campaigns" [BILD 02, 03], och med nästan samma uppräkning som Swokeis egen
  sajt (design, layout, mobil, laddningstid, SEO). Det tyder på produktplacering men bevisar
  den inte. Swokei säljer abonnemang för 42–212 dollar i månaden [BILD swokei desktop-skroll-07] och påstår "Älskad av
  1 000+ webbyråer · 31,7M skickade mejl" [BILD swokei desktop-forsta] utan belägg; siffrorna i panelen är en
  demopanel. Leveransen mäts i sålda sajter, inte i om de blev bättre än kundernas gamla, och det är vår ribba 1
  (bygg-sajt rad 9)
- Kostnad: inget att ladda. Swokei, Apollo och Soro är betaltjänster med e-post och leadlistor, alltså ny mekanik och
  personuppgifter om tredje part
- Säkerhet: förgranskningen av swokei.com:s text gav LÅG, inga dolda tecken och ingen text riktad till agenter. Inget
  repo att förgranska. Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd. Villkoret i den ersatta posten står kvar: när piloten är klar och ägaren vänder sig mot kunder
  finns underlaget till ett ärligt första besked redan i DIAGNOS.md och före/efter-tabellen. Blir det aktuellt ska
  beskedet bygga på det vi faktiskt har mätt och sett, aldrig på en påhittad förevändning
- Backlog: ingen

### 2026-10-01 · AI LABS-video: sju sätt att använda beslutsmodellen Jev i Claude Code · nej
- Källa: https://www.youtube.com/watch?v=2nc_QMuNp18 @ 2026-09-28 (AI LABS, 12:37, autogenererat transkript, sponsrad
  av Zapier [BESKRIVNING]). Sedda: hela tidslinjen och alla 41 bildrutor; nio av dem är skärminspelningar av editor,
  terminal och webbläsare, resten animerade illustrationer, sponsorklipp och en svart övergång. Repot i beskrivningen,
  tamaratran/fast-jev-compaction (MIT, 7 300 stjärnor, senast ändrat 2026-09-18), gick inte att läsa: klonen hängde
  och stoppades, så bara metadata och de delar av plugin.json som syns i bild [SKÄRM 04:01] är sedda. Skills och krokar
  ur videon ligger bakom AI Labs Pro [TAL 12:02] och gick inte att läsa. ailabspro.io och theroundup.so öppnades inte
- Steg: inget av de åtta direkt. Det är verktyg kring agentens arbete (komprimering, val av skill, filsökning,
  granskning, klickval i webbläsaren, regelkrok); närmast ligger steg 6 (utforskning i webbläsaren) och loop 1
- Sår: inget. L0 dömer innehållet i det som byggs; videons löfte är att agenten blir "way faster and cheaper to run"
  [TAL 00:00], inte att resultatet blir bättre
- Överlapp: webbläsartestet där en modell väljer nästa klick mot ett mål [TAL 10:25, SKÄRM 10:43] motsvaras av
  utforskningen i provet (`kontroller/prova.py` rad 265, `kontroller/webblasare/utforska.mjs`; bygg-sajt rad 158–159).
  Kroken som håller agenten till reglerna "because a hook runs every single time" [TAL 11:30] är vår stoppvakt
  (`.claude/hooks/stoppvakt.py` rad 2 och 6). Granskning av en annan modell än byggarens [TAL 08:46] står i kirurgens
  A/B-krav och i femsekunderstestet som görs avskärmat (bygg-sajt rad 162–165). Skillväljaren [SKÄRM 06:27] löser ett
  problem vi inte har: repot har tre skills
- Skäl: inget av de sju fallen rör det som gör våra sajter generiska, och flera går mot medvetna val. Varje fall är en
  ny krok eller skill med en extern nyckel via Vercel AI Gateway [TAL 02:44, SKÄRM 03:06], alltså ny mekanik och ett
  nytt beroende mot "Inga nya mekaniker" (`BESLUT.md` rad 74). Förhandsgallringen före granskningen ger ändringar som
  bedöms som små "one quick round" [TAL 09:20], vilket byter kvalitet mot tid; vi har valt kvalitet. Regelkroken
  blockerar en ändring när Jev är minst 80 % säker [TAL 11:30], men vår regel mot slop ska vara rapport, inte grind
  (`BESLUT.md` rad 57). Källkritik: det enda inspelade komprimeringsfallet visar att pluginet föll tillbaka till den
  vanliga sammanfattningen, "below 25% minimum: 0% reduction" [SKÄRM 04:38], så "less than a second" [TAL 04:23] syns
  aldrig. Filrankningen visas på riktigt, men de två översta får 0,40 och 0,39 [SKÄRM 08:53], alltså ingen tydlig
  skillnad; skillväljarens säkra 0,93–0,98 [SKÄRM 06:45] och rollmatrisen [SKÄRM 11:01] är animationer, inte
  inspelningar. Bildrutan vid 00:38 visar en spelare med längden 18:05 och andra kapiteltider än den här videon, så
  materialet tycks klippt ur en längre version. Inspelningarna körs med `--dangerously-skip-permissions` [SKÄRM 08:53]
  och "bypass permissions on" [SKÄRM 04:38]. Videon säljer AI Labs Pro [TAL 12:02] och Zapier [TAL 06:35]
- Kostnad: inget att ladda. Ett genomförande vore flera krokar och skills, en API-nyckel via en betald gateway och
  underhåll av kod vi inte kan läsa (betalvägg)
- Säkerhet: förgranskningen kunde inte köras, eftersom klonen hängde och ingen text hämtades. Inget kördes eller
  installerades. Pluginet ersätter Claude Codes egen komprimering genom en krok och skickar sessionens innehåll till en
  extern tjänst [TAL 03:50; SKÄRM 04:01]
- Förslag: inget
- Utfall: ingen åtgärd. Blir körtid eller kvot ett namngivet problem i ett riktigt bygge (till exempel att stoppvakten
  eller utforskningen tar för lång tid), kan en snabb klassificerare prövas där, som A/B och utan att ersätta någon
  granskning
- Backlog: ingen

### 2026-10-01 · AI LABS-video om Inspo (referensarkiv över MCP, av Hallmarks upphovsperson) · nej
- Källa: https://www.youtube.com/watch?v=Ow_z94c3wKk @ 2026-09-18 (AI LABS, 12:35, autogenererat transkript,
  sponsrad [TAL 06:00]). Sedda: hela tidslinjen och alla 41 bildrutor; nio är skärminspelningar (Inspos sajt,
  installationen, `/mcp`, Claude Codes svar och den byggda sidan i 1440 och 402), resten animerade illustrationer,
  sponsorklipp och kanalreklam. Repot förgranskat och läst: Nutlope/inspo @ `647c3b1` (senast pushad 2026-10-01, MIT,
  815 stjärnor): README.md, `apps/mcp/README.md`, serverinstruktionerna och kompositionsreglerna i
  `apps/mcp/src/tools.ts` (rad 127–151, 1717–1747), branschlistan i `packages/taxonomy/src/index.ts` (rad 36–61) och
  den egna användningsmätningen `apps/mcp/bench/results/2026-09-10-agent-usage.md`. Sedda bilder i repot: README:ns
  med- och utan-jämförelse (`docs/img/with-inspo.jpg`, `without-inspo.jpg`). inspomcp.dev öppnades inte som webbsida;
  den syns i videon [SKÄRM 04:01, 07:02]. ui-skills.com, monid.ai, ailabspro.io och theroundup.so öppnades inte
- Steg: 3 (referenser) och 5 (riktning, bygge)
- Sår: L0 ("ai slope skit"); videon säger att varje designskill lämnar ett gap som gör att resultatet "still feel
  generated" [TAL 00:00]. Ingen JAMFORELSE.md finns ännu
- Överlapp: att ge agenten riktiga sajter att se i stället för textregler är redan vårt steg 3: referenser i tre roller
  som agenten själv söker fram och öppnar i riktig webbläsare i 390 och 1440 (`.claude/skills/bygg-sajt/SKILL.md` rad
  96–108, `kunskap/referensjakt.md` rad 13–21 och 31–32). Gallerier står där redan som "möjliga sökingångar, inte en
  stilhierarki" (`referensjakt.md` rad 25–27), och Inspos arkiv kan användas så utan att något installeras. Mobil- och
  desktopbilder per referens motsvaras av `inspektera.mjs --vyer 390,1440` (bygg-sajt rad 102). Inspos hero-regel,
  att första vyn ska rymma rubrik, stödrad och primär handling [REPO tools.ts rad 139], är femsekunderstestet i steg 6.4
  (bygg-sajt rad 162–165) och kravet i steg 5.5 att första vyn säger vad de gör och vad man gör härnäst (rad 149–150)
- Skäl: källans egna bilder fäller den på dess egen fråga. README:ns med-och-utan-jämförelse, "That gap is the
  product" [REPO README.md rad 18], går från ett standardval till ett annat: utan Inspo nästan svart med en enda
  syragrön accent [REPO docs/img/without-inspo.jpg], alltså punkt 2 i `anthropic-frontend-design-SKILL.md` rad 40;
  med Inspo varmt papper, ett ord i rubriken markerat med accentfärg, en versal eyebrow med mittpunkt ("A GUIDED TOUR
  · FIVE STEPS"), monospace-etiketter och mörk pillerknapp [REPO docs/img/with-inspo.jpg], alltså rad 26–27, 39 och
  43 i samma fil. Inspos egen sajt har ett ord i accentfärg i rubriken ("inspiration") [SKÄRM 07:02]. I videons
  bygge härleds riktningen ur "category gravity" bland 24 modesajter, och valet är "Maharishi's exact move" [SKÄRM
  08:52]; agenten säger sedan att maharishistore "did most of the work", att grunden `#c9b49e` kommer därifrån och att
  accenten är Maharishis overshirtfärg mörkad [SKÄRM 09:46]. Det är att kopiera layout och palett ur en referens,
  rakt emot bygg-sajt rad 150 och referensjakt rad 53, och riktningen kommer ur branschen, inte ur verksamheten (rad
  135–136). Bilderna är stockbilder: agenten lägger en varm ton över "stock shots in five different colour
  temperatures" [SKÄRM 09:10] och kallar alla nio för platshållare [SKÄRM 09:46], mot "Inga stockbilder" (rad 49).
  Mobilens första vy är bara ett foto med en versal etikett, utan rubrik eller handling [SKÄRM 10:19], så den hade
  fallit på femsekunderstestet. Arkivet passar dessutom inte våra verksamheter: branschlistans 24 kategorier har SaaS,
  krypto, AI, typsnittsgjuterier och utvecklarverktyg men ingen för lokala tjänster, hantverk eller vård [REPO
  taxonomy/src/index.ts rad 36–61], och videon visar själv att sökningen gav fel bransch två gånger [TAL 10:53, SKÄRM
  11:17]. Källkritik: beviset i videon är en fiktiv butik och berättarens omdöme; den sponsrade delen säger
  "Manifold" [TAL 06:00] medan bilden och beskrivningen visar Monid [SKÄRM 06:26; BESKRIVNING]. Inspelningarna körs
  med `--dangerously-skip-permissions` [SKÄRM 08:52] och "bypass permissions on" [SKÄRM 11:17]. Repots egen mätning
  är ärlig och talar emot det: av 25–56 hämtade sajter per bygge citerades 4 eller 5, och 13 % av de returnerade
  sajterna användes [REPO 2026-09-10-agent-usage.md rad 45–47]
- Kostnad: 15 verktyg i en MCP-server i användarnivå [SKÄRM 07:39, 07:57]; enligt repot omkring 37 000 tokens
  verktygssvar per bygge före en omläggning, uppskattat till 12 000–14 000 efter, inte prövat på nya byggen [REPO
  2026-09-10-agent-usage.md rad 13–14, 97–102]. Den hostade vägen skickar briefen till en extern tjänst
  (inspomcp.dev); vår brief bygger på verksamhetens underlag
- Säkerhet: förgranskningen gav MEDEL, inga dolda tecken och ingen text riktad till agenter. MEDEL kommer av skript
  med nätanrop och miljövariabler, och av `apps/mcp/src/install.ts`, som skriver i andra verktygs konfiguration utanför
  repot (Claude Code i användarnivå, Codex, Claude Desktop [SKÄRM 07:39]). Träffen `curl … | sh` är synlig text i en
  exempelsida för ett påhittat CLI (`apps/web/public/examples/ferrite-terminal/page.html` rad 289). Serverinstruktionerna
  säger själva att projektets egna konventioner vinner över Inspo [REPO tools.ts rad 1727–1732]. Inget kördes eller
  installerades
- Förslag: inget
- Utfall: ingen åtgärd. Arkivet på inspomcp.dev är en galleriingång bland andra och får användas som sådan enligt
  `referensjakt.md` rad 25–27, med samma krav: följ till den riktiga sajten och öppna den. Visar ett riktigt byggs
  REFERENSER.md att hantverksreferenser var svåra att hitta, är det fyndet som ska åtgärdas, i `referensjakt.md`, inte
  genom en MCP-server
- Backlog: ingen

### 2026-10-01 · Paul J Lipsky-video: "How To Create Stunning Websites With Claude Design" · nej
- Källa: https://www.youtube.com/watch?v=IjdkFhpxw7o @ 2026-08-24 (Paul J Lipsky, 14:10, autogenererat transkript,
  ingen sponsor angiven, YouTubes standardvillkor). Sedda: hela tidslinjen och alla 41 bildrutor; sju är talaren i
  bild, resten skärminspelningar av Claude Design, ChatGPT, Gemini, land-book.com, onepagelove.com och de byggda
  sidorna. Den enda länken, claude.ai/design, kräver inloggning och öppnades inte; inga referenssajter öppnades.
  Scrollanimationerna syns bara som lägen i stillbilder, inte som rörelse
- Steg: 3 (brief, referenser), 5 (riktning, bygge) och bildanskaffning i steg 1
- Sår: L0 ("ai slope skit"); videon lovar att lyfta en sida som är "extremely generic" [TAL 03:52]. Ingen
  JAMFORELSE.md finns ännu
- Överlapp: tipset att alltid ange utseende, målgrupp och mål [TAL 01:42, SKÄRM 02:07] är vår brief: mål, målgrupper
  med belägg och toppuppgifter (`.claude/skills/bygg-sajt/SKILL.md` rad 82–84) och riktningen i KONCEPT.md (rad
  135–137). Att bifoga verksamhetens filer som sammanhang [TAL 02:47] är steg 1 och "Bara de har" (rad 45–58). Att
  bygga ett designsystem ur skärmbilder från gallerier [TAL 05:34] motsvaras av referensjakten, som redan nämner One
  Page Love som sökingång och kräver att man följer till den riktiga sajten (`kunskap/referensjakt.md` rad 25–27,
  31–32). Scrollavslöjanden med respekt för minskad rörelse [SKÄRM 12:43] står i `kunskap/bygge-referens.md` rad 23
- Skäl: det som videon visar som lyft är det som våra regler förbjuder. Designsystemet byggs ur två skärmbilder av
  Le Petit Bleu [SKÄRM 06:54] och tar med sig referensens egen adress och öppettid, "1427 Washington Ave" och "7:00
  AM – 7:00 PM", in i bageriets komponenter [SKÄRM 07:56, 08:16], och dess turkos på kräm blir bageriets palett
  [SKÄRM 07:56, 08:57]; det är att kopiera palett och identitet, mot bygg-sajt rad 150 och referensjakt rad 53, och
  ett moodboard av färg, serif och rundningar, som referensjakt rad 52 säger inte räcker. Talaren ber därtill uttryckligen
  om layouten från Gaia Masala & Burger [TAL 11:10, SKÄRM 10:19]. "Personaliseringen" är ChatGPT-bilder av påhittade
  bakverk och ett påhittat bord [TAL 04:27, SKÄRM 04:51], och sidan märker den genererade bilden "Our table, last
  Saturday, 7:40 AM" [SKÄRM 09:18], alltså en genererad bild framställd som verksamhetens egen, mot `kunskap/bild.md` rad
  16 och 19 och "Inga stockbilder" (bygg-sajt rad 49). Gemini-videon i hjälteytan visar en surdegslimpa [SKÄRM 10:40,
  12:02] fast menyn har kakor, muffins, scones, bullar och bananbröd, ingen limpa [SKÄRM 04:10, 11:41]. Med egna ögon är slutresultatet [SKÄRM
  12:02, 12:43] ett vanligt mönster: versal eyebrow med spärrning, tunn serif i accentfärg på kräm, tvåkolumnshjälte,
  pillerknappar och en nedräkning; den "fun, colorful" riktning briefen bad om [SKÄRM 02:48] försvann när
  referenspaletten tog över. Restaurangexemplet har gatuadressen "123 Pearl Street" och "9 partner farms" [SKÄRM
  13:03] utan att någon källa till uppgifterna visas. Källkritik: allt bevis är fiktiva verksamheter och talarens
  omdöme ("looks so much better" [TAL 08:23]); ingen jämförelse görs mot något annat än hans egen första version
- Kostnad: inget att ladda. Claude Design är ett webbgränssnitt med inloggning och ingen väg för ett obevakat bygge;
  arbetssättet kräver dessutom två externa genereringstjänster (ChatGPT, Gemini)
- Säkerhet: ej tillämpligt; ingen kod eller text riktad till agenter. Inget kördes eller installerades. Talarens
  egna kontaktuppgifter syns i prompten [SKÄRM 02:28] och är inte återgivna här
- Förslag: inget
- Utfall: ingen åtgärd. Det enda nya för oss, Claude Designs kommentarsverktyg för att peka på en del av sidan
  [TAL 09:30], är ett gränssnitt för människor och bär inget sår
- Backlog: ingen

### 2026-10-01 · ECC (affaan-m, "operating system for AI agent harnesses") · nej
- Källa: https://github.com/affaan-m/ECC @ `c70874f` (senast pushad 2026-10-01, MIT, 270 621 stjärnor, inte
  arkiverat). Förgranskat. Paketet har 293 skills, 68 agenter och 94 kommandon [REPO README.md rad 142], och
  förgranskningen räknade cirka 3,9 miljoner tokens text. Läst därför ett urval: README.md (rad 1–160), hjältebilden
  `assets/hero.png`, och de skills som berör webbygge och slop: `frontend-design-direction`,
  `make-interfaces-feel-better`, `design-system`, `brand-voice`, `loop-design-check`, `seo` (rad 1–60) och
  `taste-distillation`. Läst även `continuous-learning-v2` (rad 1–50), krokarnas händelser i `hooks/hooks.json` och de
  flaggade ställena. Övriga cirka 285 skills är bara sedda som namn och beskrivning (mest språk- och ramverksmönster,
  sociala medier, finans, hälsovård). ecc.tools öppnades inte
- Steg: 4 (copy), 5 (riktning och bygge) och 6 (prov); resten av paketet ligger utanför kedjan
- Sår: L0 ("ai slope skit"). Ingen JAMFORELSE.md finns ännu
- Överlapp: designdelarna är en tunnare upplaga av det vi redan läser. `frontend-design-direction` förbjuder lila
  gradienter, dekorativa blobbar, stora kort och vag hjältetext [REPO skills/frontend-design-direction/SKILL.md rad
  69–70]. Det står redan i Taste (`kunskap/externa/leonxlnx-taste-SKILL-ce26fc25.md` rad 39) och i frontend-design
  (`kunskap/externa/anthropic-frontend-design-SKILL.md` rad 17 och 42). Skillen säger själv att den inte buntar
  Anthropics frontend-design [REPO rad 15–18], och den har vi redan. `make-interfaces-feel-better` (inget
  `transition: all`, `text-wrap: balance`, `tabular-nums`, träffytor 40–44 px) [REPO
  skills/make-interfaces-feel-better/SKILL.md rad 50–55, 107, 123] motsvaras av Vercels riktlinjer
  (`kunskap/externa/vercel-web-interface-guidelines-command-e3d624ba.md` rad 55, 68–69), Emil
  (`kunskap/externa/emil-emil-design-eng-SKILL.md` rad 44) och Osmani
  (`kunskap/externa/addyosmani-accessibility-SKILL.md` rad 255–258). Slopkontrollen i `design-system` är sju rader
  [REPO skills/design-system/SKILL.md rad 59–66], alla redan i Taste rad 39 och 187. `loop-design-check` kräver en
  oberoende domare och att människan ger slutgodkännandet [REPO skills/loop-design-check/SKILL.md rad 85, 110]. Det
  har vi redan: det avskärmade femsekunderstestet (`.claude/skills/bygg-sajt/SKILL.md` rad 162–165), stoppvakten som
  kör provet själv (rad 210–211) och ägarens dom i steg 8 (rad 213–217)
- Skäl: inget i urvalet adresserar L0 bättre än det vi redan har, och flera delar drar åt fel håll.
  `frontend-design-direction` säger att man ska använda "real or generated visual assets"
  [REPO skills/frontend-design-direction/SKILL.md rad 53]. Det skiljer inte på anspråk som `kunskap/bild.md` rad
  12–19 gör, och det går emot "Inga stockbilder" (bygg-sajt rad 49). `design-system` hämtar inspiration från "3
  competitor sites" [REPO skills/design-system/SKILL.md rad 27] och skapar ett tokensystem ur dem. Våra referenser
  ska i stället ha tre roller och får inte kopieras (bygg-sajt rad 96–108, 150). `brand-voice` bygger en röst ur
  X-inlägg och mejl för sociala kanaler [REPO skills/brand-voice/SKILL.md rad 23–26, 92–96]. Vår ton hämtas ur
  verksamhetens och kundernas egna ord (bygg-sajt rad 89). Kärnan i paketet är mekanik: sex krokhändelser från
  PreToolUse till SessionEnd [REPO hooks/hooks.json rad 3, 92, 103, 123, 166, 240] och ett system som observerar
  sessioner och själv gör om "instincts" till skills, kommandon och agenter [REPO
  skills/continuous-learning-v2/SKILL.md rad 3]. Det strider mot "en dom blir en textändring, inte en ny mekanik"
  och mot ägarens domar som enda källa till ändrade regler. `taste-distillation` mäter färgton och klipprytm i video
  och ligger utanför webbygge. Källkritik: README:n säljer ECC Pro från 19 dollar per plats och månad [REPO README.md
  rad 79–83] och visar sponsorer. Hjältebilden är själv ett vanligt mönster: nästan svart botten med en enda
  orangeröd accent, accentfärg på rubrikens sista ord, en versal spärrad eyebrow med mittpunkt och
  monospace-etiketter [BILD assets/hero.png]. Det är samma drag som frontend-design rad 26–27, 40 och 43 pekar ut. Påståendet att ECC gör agenten bättre är inte belagt med någon
  jämförelse i det jag läste
- Kostnad: hela paketet ligger på flera miljoner tokens text. Det installeras som plugin med krokar i sex händelser,
  regler som alltid laddas och en bakgrundsagent för inlärning. Det betyder underhåll av en kodbas som släpper varje
  vecka över sju verktyg [REPO README.md rad 104]
- Säkerhet: förgranskningen gav HÖG, inga dolda tecken. HÖG kommer av 1 003 skript, bland dem installatörer som
  skriver utanför repot (`.codebuddy/install.sh`, `.trae/install.sh`, `.kiro/install.sh`), krokar med `eval` och
  miljövariabler, en MCP-server via `npx` (`.mcp.json`) och nätanrop (bland annat `skills/taste-application/scripts/falapi.py`).
  De 48 ställena med text riktad till agenter är i sitt sammanhang ofarliga: säkerhetsguider som beskriver
  exfiltrering, testfixturer för en promptinjektionsvakt och en exempelfil för användarens CLAUDE.md
  (`examples/user-CLAUDE.md` rad 14). Inget försök att styra granskaren hittades i det lästa. Inget kördes eller
  installerades
- Förslag: inget
- Utfall: ingen åtgärd. Visar ett riktigt byggs JAMFORELSE.md att detaljfinishen brister (radbrytning i rubriker,
  siffror, övergångar), finns reglerna redan i Vercels riktlinjer och Emil. Då ska steg 5 peka dit, inte ta in ECC
- Backlog: ingen

### 2026-10-01 · React (react/react) · nej
- Källa: https://github.com/react/react @ 7c6ac13e, MIT. Läst: README.md, CLAUDE.md, `.claude/instructions.md`,
  `.claude/skills/verify/SKILL.md`, förgranskningens rapport och de flaggade ställena. Bilder: repot har bara ikoner
  och logotyper (DevTools-ikoner, fixturlogor), inga skärmbilder eller demo att se; README visar bara märken.
  Ägarens not: ingen
- Steg: 5 (bygge), i så fall
- Sår: inget. L0 gäller copy och slop, inte vilket ramverk sidorna renderas med. Ingen JAMFORELSE.md finns ännu
- Överlapp: mallen är Astro med `astro` och `sharp` som enda beroenden (`mall/astro/package.json` rad 10–13), och
  steg 5 kräver "ingen JavaScript som inte behövs" och att den primära handlingen fungerar utan JavaScript
  (`.claude/skills/bygg-sajt/SKILL.md` rad 85 och 141). Registret har redan två gånger avfärdat React-specifika regler
  för att de inte möter mallens stack (rad 58–59 och 276–278)
- Skäl: det här är källkoden till själva biblioteket, ingen metod, regel eller skill för att bygga bättre sajter
  [REPO README.md rad 3–7]. Det som repot innehåller för agenter är bidragsverktyg för React-kärnan: Prettier, lint,
  Flow och tester via yarn [REPO .claude/skills/verify/SKILL.md rad 15–22; .claude/instructions.md rad 37–46]. Att
  bygga kundsajterna i React skulle lägga ett klientbibliotek och hydrering på informationssajter för lokala
  verksamheter, vilket går emot steg 5:s minimala JavaScript och inte adresserar något sår. Källan säljer inget
  utöver sig själv; påståendena i README är allmän produktbeskrivning, inte belagda mot något vi mäter
- Kostnad: ungefär 1,1 miljoner tokens text i repot; som beroende i mallen skulle det betyda React, en renderare och
  en Astro-integration i varje bygge, med underhåll av versioner och större JavaScript-last på varje sida
- Säkerhet: förgranskningen gav HÖG, av mängden: 4 349 skript med eval/exec, nätanrop och miljövariabler i ett stort
  kompilator- och testträd. Sju dolda tecken (nollbredd U+200B) i
  `packages/react-reconciler/src/__tests__/ReactPerformanceTrack-test.js` rad 97 m.fl.; jag läste rad 97 och tecknet
  står först i ett förväntat mätnamn i ett test, inte i text till en agent. De tio ställena med text riktad till
  agenter är byggrader i DevTools-README:er och utvecklarskript. Repot har egen `.claude/settings.json` med en
  SessionStart-krok och tillåtna yarn-kommandon; den gäller bara sessioner startade inne i repot, och inget startades
  där. Inget försök att styra granskaren hittades. Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd. Skulle ett bygge kräva riktig interaktivitet (till exempel en bokningsvy som deras system inte
  redan ger) prövas det som en Astro-ö i steg 5, inte som byte av mall
- Backlog: ingen

### 2026-10-01 · the-book-of-secret-knowledge (trimstray) · nej
- Källa: https://github.com/trimstray/the-book-of-secret-knowledge @ `7d37069` (senast pushad 2024-11-19), MIT, 247 262
  stjärnor. Repot är en enda README.md på drygt 4 400 rader plus licens och bidragsregler. Läst: inledningen och
  innehållsförteckningen, alla avsnittsrubriker, och i sin helhet de avsnitt som rör webbsajter: Web Tools (rad
  443–591: webbläsare, SSL/säkerhet, HTTP-rubriker och webblinters, DNS, e-post, prestanda) och Manuals "Web Apps",
  "All-in-one" och "Other" (rad 935–1015). Resten (CLI-verktyg, nätverk, containrar, pentest, skal-enradare) lästes
  bara som rubriker. Sedd: den enda bilden, `static/img/the-book-of-secret-knowledge-preview.png`, en tecknad bok med
  titeln [BILD]. Ingen demo. Ägarens not: ingen
- Steg: 6 (prov) och lanseringen efter 7, i så fall
- Sår: inget. L0 ("ai slope skit") gäller generiskt innehåll och generisk form; källan handlar om drift, nät och
  säkerhet. Ingen JAMFORELSE.md finns ännu
- Överlapp: det webbrelevanta är länkar till mätverktyg vars mått vi redan har som krav och prov. Säkerhetsrubrikerna
  som securityheaders.com och Mozilla Observatory betygsätter [REPO README.md rad 491–492] står i
  `kunskap/bygge-referens.md` rad 16–18 och prövas i `kunskap/prelaunch.md` rad 17 (grind 7). Lighthouse och
  PageSpeed Insights [REPO rad 588–590] körs av `kontroller/lighthouse.mjs` och mäts mot kravnivån i prelaunch.md rad
  12, och Core Web Vitals-målen står i bygge-referens.md rad 14. SPF/DKIM-kontrollen som e-postverktygen gör [REPO rad
  523–528] står i `kunskap/lansering.md` rad 52–62
- Skäl: en länksamling för systemadministratörer, DevOps och pentestare, som författaren själv säger [REPO README.md
  rad 32], utan regler eller metod att ta in, bara en mening om varje länk. Det lilla som rör en lokal verksamhets
  sajt är kontrollverktyg för det vi redan kräver och mäter, och flera av dem är föråldrade eller nere (xip.io,
  Panopticlick, Netcraft märkt som otillgänglig [REPO rad 450, 513, 546]; senast pushad för snart två år sedan). Inget
  i den adresserar att sajten ska höra till verksamheten. Källkritik: källan säljer inget utom en Open
  Collective-insamling [REPO rad 65–74]; stjärnantalet är räckvidd, inte belägg, och urvalet är en persons bokmärken
- Kostnad: ungefär 54 500 tokens text om den skulle laddas; inga beroenden. Inget att underhålla, men inget att vinna
- Säkerhet: förgranskningen gav LÅG över fem textfiler: inga dolda tecken, ingen text riktad till agenter, inga skript
  eller krokar. Innehållet länkar till exploit-, lösenords- och skanningsverktyg, men som listor, inte som
  instruktioner till en agent. Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd. Skulle prelaunch grind 7 i ett riktigt bygge behöva ett oberoende andra utlåtande om
  rubrikerna, är securityheaders.com eller Mozilla Observatory ett manuellt kvitto mot den levande adressen, inte en
  ny kontroll
- Backlog: ingen

### 2026-10-01 · DigitalPlatDev/FreeDomain · nej
- Källa: https://github.com/DigitalPlatDev/FreeDomain @ `9c7c541`, AGPL-3.0; läst README, FAQ, handledningens
  översikt (1.0) och avsnittet om godtagbar användning (5.6), plus förgranskningen över alla 79 textfiler. Sett
  logotypen och två av nio skärmbilder (DigitalPlats registreringsruta, Cloudflares namnserversida). Övriga sju är
  panelbilder av samma slag och lästes inte. Ingen demo; länken går till en inloggningspanel. Ägarens not: ingen
- Steg: lanseringen efter 7 (domän och DNS), i så fall
- Sår: inget. L0 gäller generiskt innehåll och generisk form; källan är en gratistjänst för underdomäner och en
  DNS-handledning. Ingen JAMFORELSE.md finns ännu
- Överlapp: steg 5 sätter sajtens adress till verksamhetens egen domän (`.claude/skills/bygg-sajt/SKILL.md` rad 138).
  Det handledningen lär ut om delegering, TTL, namnserverbyte och e-postposter [REPO documents/tutorial/] står redan
  som procedur i `kunskap/lansering.md` rad 11–17 (TTL och namnserverbyte), 19–37 (DNS-bild före och efter) och
  49–62 (SPF, DKIM, DMARC), och där gör ingen session DNS-ändringar (rad 16)
- Skäl: tjänsten ger gratis namn under fem delade ändelser som .us.kg och .dpdns.org [REPO README.md rad 25–29], högst
  ett per konto [REPO documents/domains/faq.md rad 5], och kontot kan stängas utan förvarning efter tjänstens eget
  gottfinnande [BILD digitalplat-domain-registration.jpg]. En riktig verksamhet ska stå på sin egen domän; ett lånat
  namn i en namnrymd som tjänsten själv beskriver som utsatt för missbruk [REPO faq.md rad 7] är fel signal och en
  driftsrisk. Handledningen är en ordentlig DNS-bok men lär ut det vi redan har som procedur. Källkritik: README:n
  säljer tjänsten, ber om stjärnor [REPO faq.md rad 23–26] och anger både "500,000 domains" [REPO README.md rad 53]
  och 400 000 användare (i den länkade artikelns adress) [REPO README.md rad 96] utan belägg; stjärnantalet (drygt 202 000) är räckvidd, inte kvalitet
- Kostnad: ungefär 63 700 tokens text om handledningen skulle laddas; inga beroenden. Inget att vinna
- Säkerhet: förgranskningen gav LÅG över 79 textfiler: inga dolda tecken, ingen text riktad till agenter, inga skript
  eller krokar. Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd
- Backlog: ingen

### 2026-10-01 · Next.js (vercel/next.js) · nej
- Källa: https://github.com/vercel/next.js @ `d5d747e` (gren canary, senast pushad 2026-10-01), MIT, knappt 143 000
  stjärnor, inte arkiverat. Förgranskat. Läst: README.md, AGENTS.md (rad 1–40 och 280–309), listan över repots 20
  agentskills under `.agents/skills/` (namnen), `packages/next-codemod/lib/agents-md.ts` (rad 1–60),
  `packages/next/src/cli/internal/agent-feedback-instructions.ts` (rad 50–73) och de flaggade ställena. Bilder: repot
  har bara exempelappars favicons, författarfoton och omslagsbilder, ingen skärmbild av ramverket; README visar logga
  och märken. README:ns galleri nextjs.org/showcase öppnat som webbsida och tre skärmbilder lästa (desktop första vyn,
  mobil första vyn, desktop skrollad 34 %). Övriga nio lästes inte. Ägarens not: ingen
- Steg: 5 (bygge), i så fall
- Sår: inget. L0 ("ai slope skit") gäller generisk copy och form, inte vilket ramverk sidorna genereras med. Ingen
  JAMFORELSE.md finns ännu
- Överlapp: mallen är Astro med `astro` och `sharp` som enda beroenden (`mall/astro/package.json` rad 10–13). Steg 5
  kopierar den (`.claude/skills/bygg-sajt/SKILL.md` rad 142) och kräver "ingen JavaScript som inte behövs" (rad 145).
  Den primära handlingen ska fungera utan JavaScript (rad 89). `kunskap/bygge-referens.md` rad 28 nämner redan Next.js
  med statisk generering som ett beprövat mönster bredvid Astro, och rad 36 har dess `NEXT_PUBLIC_`-regel. React, som
  Next.js bygger på, är redan avfärdat med samma skäl (posten "React (react/react)" ovan)
- Skäl: det här är källkoden till ett React-ramverk för fullstack-appar [REPO README.md rad 19], inte en metod, regel
  eller skill för att bygga bättre sajter. Repots agentmaterial gäller bidrag till ramverket självt: monorepots
  struktur, PR-regler, fork-adoption och skills som `react-sync`, `backport-pr` och `v8-jit` [REPO AGENTS.md rad 1–40;
  .agents/skills/]. Det enda som riktar sig till den som bygger med Next.js är en generator som lägger in ett
  dokumentationsindex i projektets AGENTS.md [REPO packages/next-codemod/lib/agents-md.ts rad 1–6], och den gäller
  bara Next.js-projekt. Att byta mall till Next.js skulle ge React-körning och hydrering på informationssajter för
  lokala verksamheter, vilket går emot steg 5:s minimala JavaScript och inte adresserar något sår. Källkritik: README
  säljer med "Used by some of the world's largest companies" [REPO README.md rad 19] och galleriet bekräftar det:
  Sonos, Nike, ChatGPT, Claude och Netflix [BILD desktop-skroll-04.png], inga verksamheter i vår storlek. Galleriet
  visar ramverkets räckvidd, inte hur bra sajterna är för deras besökare. Sidan själv öppnade en integritetsruta som
  täckte innehållet i båda vyerna [BILD desktop-forsta.png, mobil-forsta.png]. Källan innehåller instruktioner till
  agenter: en dold HTML-kommentar ber AI-assistenter som skriver PR-beskrivningar att lägga in en markör
  [REPO contributing/repository/pull-request-descriptions.md rad 9–14]. Den gäller bidrag till deras repo, angick inte
  granskningen och följdes inte
- Kostnad: ungefär 1,6 miljoner tokens text i repot. Som mall skulle det betyda Next.js, React och en Rust-baserad
  verktygskedja i varje bygge, med versionsunderhåll och större JavaScript-last på varje sida
- Säkerhet: förgranskningen gav HÖG, av mängden: 16 835 skript med eval/exec, nätanrop och miljövariabler i ett stort
  ramverks-, test- och CI-träd, och 1 102 dolda tecken. Utanför katalogerna `compiled/` finns de bara i tre filer.
  I `packages/next/src/cli/internal/static-routes-info.ts` rad 687 hindrar ett nollbreddstecken att `*/` i en
  kommentar avslutar kommentaren. I `crates/next-core/src/next_manifests/encode_uri_component.rs` rad 74 och 76 är
  det sammanfogningstecken i emoji i testdata. Den tredje är en byggd bunt
  (`.github/actions/validate-docs-links/dist/index.js`). Resten ligger i förkompilerade tredjepartsbuntar under
  `packages/next/src/compiled/` (acorn, babel, json5 m.fl.); dem öppnade jag inte. En sökning efter nollbredds- och
  riktningstecken i alla md-, mdx- och txt-filer gav noll träffar. Av de 47 ställena med text riktad till agenter är
  nästan alla installationsrader i dokumentation och exempel. AGENTS.md rad 298 är en säkerhetsvarning om att
  adopterade fork-PR:er kan läcka hemligheter. Undantaget är PR-markören ovan. Inga krokar eller MCP-servrar i
  konfigurationen. Inget kördes eller installerades
- Förslag: inget
- Utfall: ingen åtgärd. Skulle ett bygge kräva riktig interaktivitet prövas den som en Astro-ö i steg 5, som för React
- Backlog: ingen

### 2026-10-01 · gstack (garrytan/gstack) · nej
- Källa: https://github.com/garrytan/gstack @ `df89475` (senast pushad 2026-10-01), MIT, knappt 135 000 stjärnor,
  inte arkiverat. Förgranskat. Läst: README.md rad 1–525 av 678, `agents-digest/gstack-AGENTS.md`, designgranskningens
  metod i `scripts/resolvers/design.ts` rad 340–586, `scripts/resolvers/constants.ts`, slopkatalogens elva
  grundmönster i `lib/design-catalog.ts` rad 77–154, och de flaggade ställena nedan. Övriga ett trettiotal skills
  (office-hours, ship, cso, ios-qa m.fl.) lästes bara i README:ns tabell. Bilder: repot har två skärmbilder av
  GitHub-aktivitet (den för 2026 läst), tilläggets ikoner och testfixturer; ingen skärmbild av något byggt. README
  länkar ingen demo. Ägarens not: ingen
- Steg: 5 (koncept och bygge) och 6 (prov), i så fall
- Sår: L0 ("ai slope skit") i allmänhet. Ingen JAMFORELSE.md finns ännu, så inget namngivet gap mot referenserna
- Överlapp: slopmönstren står redan i det vi läser i steg 5. Taste rad 39 (lila gradienter, centrerad hjälte, tre
  lika kort), rad 147–148 (emoji), rad 217 (en hörnradie), rad 251 (samma sektionslayout högst en gång), rad 296
  (gradientblobb som hjälte) och frontend-design rad 42 (SaaS-kortkit med samma radie och dekorgradienter)
  (`kunskap/externa/leonxlnx-taste-SKILL-ce26fc25.md`, `kunskap/externa/anthropic-frontend-design-SKILL.md`). Generisk
  hjältetext ("Välkommen till") står i `kunskap/copy-kontroll.md` rad 15 och `kunskap/redaktionellt-pass.md` rad 31.
  Bedömningen mot dimensioner har vi som de åtta jämförelsedimensionerna mot öppnade referenser
  (`kunskap/referenser-professionella.md` rad 18–30, `.claude/skills/bygg-sajt/SKILL.md` rad 149–154), och frågan om
  första vyn säger vad de gör som det avskärmade femsekunderstestet (`bygg-sajt/SKILL.md` rad 166–169). "Varje
  sektion har ett jobb" motsvaras av raden `Specifikt:` per sektion (`bygg-sajt/SKILL.md` rad 120–121)
- Skäl: gstack är en uppsättning slash-kommandon för att bygga mjukvaruprodukter i sprintar (tänk, planera, bygg,
  granska, testa, släpp) [REPO README.md rad 207–211], skriven för grundare och tekniska ledare [REPO README.md rad
  29–32]. Det som berör oss är designgranskningen: tio kategorier med bokstavsbetyg och ett separat betyg för
  AI-slop [REPO scripts/resolvers/design.ts rad 521–550], elva svartlistade mönster [REPO lib/design-catalog.ts rad
  77–154] och sju ja/nej-frågor hämtade ur en OpenAI-text [REPO scripts/resolvers/constants.ts rad 17–37]. Nästan
  allt i listan har vi redan i text (se Överlapp). Betygen är egna viktningar utan belägg, och slop väger bara 5 %
  av designbetyget [REPO design.ts rad 546], medan vårt sår L0 är just slop. Tre rader saknas hos oss: färgad
  vänsterkant på kort, systemtypsnitt som enda röst [REPO lib/design-catalog.ts rad 129–153] och om sidan går att
  förstå på rubrikerna enbart [REPO constants.ts rad 32]. Ingen av dem är ett sår ännu, och den andra krockar med
  att steg 5 medvetet tillåter systemtypsnitt (`bygg-sajt/SKILL.md` rad 145). Visar ett bygge något av dem kan raden
  hämtas härifrån. Resten krockar med medvetna val: `/design-shotgun` tar fram skisser med GPT Image [REPO README.md
  rad 399], inte verksamhetens egna bilder, och `/design-review` rättar själv och committar [REPO README.md rad 225].
  Källkritik: README:n säljer med produktivitetstal som "~810× my 2013 pace" [REPO README.md rad 9] och
  aktivitetsgrafer [BILD docs/images/github-2026.png], inte med något byggt resultat att titta på. Källan innehåller
  instruktioner till agenter: en installationsprompt att klistra in i Claude Code, som också skriver i CLAUDE.md
  [REPO README.md rad 51–53]. Den följdes inte
- Kostnad: ungefär 2,1 miljoner tokens text i repot. Att installera kräver Bun, bygger en egen webbläsare,
  registrerar en Stop-krok i `~/.claude/settings.json` och en automatisk uppdatering vid varje sessionsstart [REPO
  README.md rad 45, 63, 359–361]; det strider mot att inte installera något och mot små textändringar
- Säkerhet: förgranskningen gav HÖG: 23 dolda tecken, 85 ställen med text riktad till agenter, 1 655 skript (många
  med nätanrop, eval/exec och miljövariabler), krokar i flera skills frontmatter (autoplan, careful, freeze, guard,
  investigate). De två dolda tecknen jag öppnade är delar av reguljära uttryck som rensar bort nollbreddstecken [REPO
  browse/src/server.ts rad 122, lib/redact-engine.ts rad 100]. De flesta agentriktade träffarna är testfixturer för
  repots eget försvar mot promptinjektion; "Don't tell the user" är en kodkommentar om ett felbesked [REPO
  lib/gbrain-local-status.ts rad 516]. Ingen krok eller MCP-server i repots egen konfiguration. Inget kördes eller
  installerades
- Förslag: inget
- Utfall: ingen åtgärd
- Backlog: ingen
