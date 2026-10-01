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
