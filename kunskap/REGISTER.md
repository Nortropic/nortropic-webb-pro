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
