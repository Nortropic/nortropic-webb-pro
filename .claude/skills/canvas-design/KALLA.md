# Källa

- **Skill:** `canvas-design` (mappen `canvas-design`). Anthropics skill för grafiska koncept som statiska bilder: först
  en designfilosofi (en .md-fil), sedan en komposition uttryckt visuellt som .png eller .pdf, "90 % visuellt, 10 %
  text", med egna typsnitt i `canvas-fonts/`.
- **Källa:** https://github.com/anthropics/skills, `skills/canvas-design/`, commit
  `683bc88e56f3e09ba94f7055977f3d3aa499f202` (2026-10-05T06:46:42-07:00, standardgrenen main). Mappen ändrades senast
  i `b9e19e6f` (2026-04-20T21:38:16Z).
- **Licens:** Apache-2.0. `LICENSE.txt` ligger i upstream-mappen (frontmatterns `license: Complete terms in
  LICENSE.txt`), kontrollerad 2026-10-07: hela Apache License 2.0-texten med licensnotisen sist. Typsnitten i
  `canvas-fonts/` är OFL-1.1, var familj med sin egen `<Familj>-OFL.txt` i samma mapp.
- **Intagen:** 2026-10-07 på ägarens uppdrag samma dag (punkt 5D): "Gör skillen tillgänglig för grafiska koncept,
  illustrationer och statiska kompositionsstudier. Koppla dess resultat till det faktiska material- och designarbetet.
  Beskriv inte en PNG/PDF som en fungerande responsiv prototyp." Ordagrant: filerna är kontrollerade byte för byte mot
  upstreams blobbar (`git hash-object` mot GitHubs trädlistning, 77 filer); inget omskrivet. Kirurgen bedömde repot
  2026-10-02 (`kunskap/REGISTER.md`) och tog då inte in canvas-design ("affischkonst ur en påhittad rörelse"); registrets
  ursprungsnot 2026-10-01 utelämnade texten för att licensfil saknades i den kopia som fanns då. Båda noterna står kvar,
  med utfallet.
- **Filer:** 77 från upstream: `SKILL.md`, `LICENSE.txt` och `canvas-fonts/` med 48 typsnittsfiler (.ttf) i 27
  familjer och deras 27 OFL-filer. Våra tillägg: `KALLA.md`.
- **Utelämnat:** sex typsnittsfiler ur `canvas-fonts/` vars familj saknar OFL-fil i upstream-mappen:
  `IBMPlexSerif-Regular.ttf`, `IBMPlexSerif-Italic.ttf`, `IBMPlexSerif-Bold.ttf`, `IBMPlexSerif-BoldItalic.ttf`,
  `InstrumentSerif-Regular.ttf` och `InstrumentSerif-Italic.ttf`. OFL 1.1 kräver att licensen och
  copyrightinformationen följer typsnittet (`kunskap/bild.md`, Typsnitt och ikonuppsättningar), och repots regel sedan
  2026-10-01 är att bara ta in det som har licensfil. De tas in när licensfilen följer med upstream eller hämtas från
  typsnittets egen källa med sin licensfil.
- **Förgranskning 2026-10-07:** `kontroller/granska_repo.py` på klonen gav LÅG: inga dolda tecken, ingen text riktad
  till agenter, inga behörigheter i frontmatter, inga hookar, inga skript. Storlek: 75 tokens i varje session
  (beskrivningen), cirka 2 900 när skillen används (SKILL.md), cirka 32 500 vid behov (OFL-texterna).
- **Beroenden (prövat 2026-10-07):** skillen namnger inga bibliotek; implementationen överlåts till sessionen. En PNG
  eller PDF ur Python förutsätter i praktiken Pillow (raster) respektive reportlab (PDF). Inget av dem finns i `.venv`
  (`requirements-lock.txt`; prövat med import), och inget låses här: ett intag följer `kunskap/beroenden.md` (raden
  Python-paketen: egen venv ur färdiga hjul, pip check, OSV, regressionsfallen i en worktree). Utan nya paket: en
  komposition skriven som SVG eller HTML och renderad till PNG med Playwrights Chromium i `kontroller/node_modules`,
  förhandsvisningens väg. "Download and use whatever fonts are needed" (SKILL.md) går inte i flödets sessioner, som
  saknar nät; typsnitten i `canvas-fonts/` räcker.
- **Nästlad session (prövat 2026-10-07):** se raden "Prövat i nästlad session" sist i filen.
- **Krockar med våra beslut:** (1) "Keep the design philosophy generic without mentioning the intention" och
  filosofin som en egen "rörelse" drar mot form utan verksamhet; hos oss kommer riktningen ur uppdraget,
  huvudreferensen och kundens material, och filosofin är arbetssättet för en kompositionsstudie, inte sanningskällan
  (Avgörandena, Process). (2) "Anchor the piece with simple phrase(s)", "sparse, clinical typography and systematic
  reference markers": varje ord i ett koncept kommer ur underlaget, och markörer som ser ut som mätvärden är påhittade
  siffror och används inte (Sanning, K10). (3) "as if it were a scientific bible … an imaginary discipline": ett
  koncept läses som bild, aldrig som bevis, och utger sig aldrig för att visa verksamheten (`kunskap/bild.md`).
  (4) Den upprepade retoriken om "countless hours" och "master-level execution" är prompthantverk, inget belägg
  (kirurgen 2026-10-02). (5) "The user ALREADY said 'It isn't perfect enough'": ingen svarar i flödets sessioner;
  det andra passet görs ändå som skillens egen regel. (6) Nedladdning av typsnitt: inget nät i sessionerna.
- **Så används skillen här:** som alternativ (välj) i rollen komposition för grafiska koncept, illustrationer och
  statiska kompositionsstudier (`kunskap/metodkarta.md`, Kompetenserna, Grafiska koncept ur canvas-design). En PNG
  eller PDF ur skillen är ett koncept och ett material- och designunderlag, aldrig en fungerande responsiv prototyp:
  kandidaten är den byggda sidan i 390, 768, 1280 och 1440. Ett koncept som används registreras i kandidatens
  `koncept/BILDER.md`, under `underlag/<slug>/atelje/kandidater/<id>/`, med källa
  (`canvas-design @ 683bc88`) och version och får `Egen: nej` (formen i `kunskap/metodkarta.md`, Grafiska koncept ur
  canvas-design; `kunskap/bild.md` bär regeln och hänvisar dit); materialsteget (gren H4 i ägarens uppdrag 2026-10-07)
  tar koncepten som ingång till ett konkret visuellt uppdrag. Filosofi, studier och skapartext stannar i samma
  kandidatkatalog, aldrig i gemensamma `bilder/`, så blindkritiken inte får studier eller förklaringar.
- **Prövat i nästlad session 2026-10-07** (flödets egna argument, `atelje.session_args`, utan kund, modellen
  `claude-haiku-4-5-20251001`): init-beskedet listade skillen bland 73 projektskills; en session aktiverade den med
  Skill-verktyget (8 turer, 29 s) och rapporterade första rubriken, 48 typsnittsfiler, inga namngivna bibliotek och
  formaten .md, .pdf och .png. I en andra session (6 turer, 17 s) syntes aktiveringen i kompetenskvittot som
  `skill_anrop` och som valt alternativ, medan en aktivering av en skill som inte finns gav `Unknown skill` och sedan
  rättelsen i `kontroller/bildkedja.py` inte räknas; samma session läste de injicerade instruktionerna ("Output only
  .md … .pdf … .png") som ett nytt uppdrag och stannade, så kvittots aktivering säger inget om användning eller
  kvalitet (`kunskap/metodkarta.md`, Aktivering, användning och bedömning).
