# Så används skillen i nortropic-webb-pro

Husets tillämpning av build-design: läsvägen ur kundens egen Figmafil. Den gäller före skillens `SKILL.md` och
`figma.md`, som står ordagrant som källan (commit, licens och vad som är vårt: `KALLA.md`). Var skillen används:
`kunskap/metodkarta.md`, bandets stationer `underlag` och `overlamning` och designfas-kartans rader `skill:build-design`
och `mcp:figma` (ägarens beslut 2026-10-13).

- **När:** kundunderlaget har en länk till kundens egen Figmafil, till exempel identitet, logotyp eller ett
  designsystem från en tidigare byrå. Utan Figmafil används skillen inte.
- **Vad filen är för oss:** kundens etablerade identitet, inte sidan. Riktningarna formges på bandet; filens variabler,
  stilar, komponenter och logotyp är låsta värden i riktningarna (underlagets fråga om etablerad identitet) och grunden
  för kundens designsystem i överlämningen. "The design decides" (SKILL.md:10) gäller de värdena. Har kunden ritat en
  skärm som en riktning ska bygga gäller skillen hel för den skärmen.
- **Läsvägen** (Figmas MCP; anropen och vad de ger: `figma.md`). Läs Figmas skill `figma-design-to-code` före första
  `get_design_context` (serverns villkor). Filnyckeln och nod-id:t tas ur länken, en ram åt gången.
  - `get_variable_defs`: variablerna med namn och värden, till färgroller, typskala, mellanrum och radier.
  - `search_design_system`: kundens komponenter, variabler och stilar, med generiska frågor ("button", "primary").
  - `get_design_context`: exakta värden, bundna variabler, komponentinstanser och tillgångarnas adresser, med
    skärmbilden i samma anrop. Koden är en referens i React och Tailwind och kopieras aldrig.
  - `get_screenshot`: ramens bild när design context inte gav någon; den är jämförelsemålet, aldrig en tillgång.
- **Vart värdena går:** i underlaget till riktningens anteckning under den låsta identiteten, varje värde med variabelns
  namn och källan (`Figma <fileKey>, nod <id>, läst <datum>`). Logotypen och andra tillgångar laddas ned till
  `underlag/<slug>/bilder/` med en rad i BILDER.md, eftersom Figmas adresser upphör (figma.md:27); en ritning eller sida
  har aldrig en Figma-adress. I överlämningen mappas variablerna på kundens designsystem enligt SKILL.md steg 2:
  variabelns namn före råvärdet, varje avrundning listad, och en avrundning som syns (mer än 2 px, eller en färg som
  hamnar på ett annat steg) står som öppen fråga i DESIGN.md.
- **Ingen svarar i flödets sessioner.** Där skillen ber användaren (logga in :16, en saknad komponent :34, en synlig
  avrundning :37) skrivs frågan i versionens orsak eller under öppna frågor i DESIGN.md, och arbetet fortsätter med det
  som har belägg.
- **Når inte Figma sessionen:** i dag startar flödets sessioner med `--strict-mcp-config` och bara Refero, Mobbin,
  Motion och 21st, och kundvakten prövar inte Figma-anrop. Underlaget säger då att kundens Figmafil finns och inte är
  läst, och riktningarna tar identiteten ur det övriga materialet. Inkopplingen är backlogposten
  `B-20261013-figma-mcp-n-i-flodets-sessioner-bakom-kundvakten`.
- **Kunduppgifter:** sökfrågorna är generiska, som till alla externa tjänster; filnyckeln och nod-id:t pekar ut kundens
  egen fil och bär inga andra uppgifter.
- **Kontot är Pro.** Code Connect (figma.md:25) kräver Figmas Organization- eller Enterprise-plan och finns inte här.
- **Grannarnas namn** (SKILL.md:12): `interface-review`, `variant` och `break` heter här better-interface-review,
  better-variant och better-break. Ägarens golv för kontrast, fokus och träffytor står i metodkartans Avgöranden.
