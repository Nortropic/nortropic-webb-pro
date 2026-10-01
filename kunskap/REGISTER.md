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
