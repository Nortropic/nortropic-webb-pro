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
