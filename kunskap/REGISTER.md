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
