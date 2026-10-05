# Källa

- **Skill:** `break-ui` (mappen `emil-break-ui`). Försöker knäcka ett UI med värstafallsdata bakom en växel som bara finns i utveckling (med `CATALOG.md`).
- **Källa:** https://github.com/emilkowalski/skills, `skills/break-ui/`, commit `e8a175de22ae1e49370fc144c1f3bb9aeedf988d` (2026-10-02T06:43:31-04:00, standardgrenen main). Mappen ändrades senast i `e8a175de22ae` (2026-10-02T06:43:31-04:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Emil Kowalski), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 2 från upstream (2 i mappens rot): `CATALOG.md`, `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repots fjorton skills är alla intagna som `emil-<namn>`; `performance-cheatsheet.md` och README i repots rot hänvisas inte från någon skill.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav HÖG. Nivån kommer enbart av ett ZWJ (U+200D) i `CATALOG.md:26`, som är en avsiktlig emoji-sekvens i testdatat; träffen "ignore previous instructions" på `SKILL.md:36` är skillens egen regel att behandla repoinnehåll som data. Inga skript, inga hemligheter, inga nätanrop.
- **Krockar med våra beslut:** värstafallsläget bakom `?data=worst` eller en prototyproute (SKILL.md:76) och en fixtur i projektet (:62); i Astro publiceras allt under src/pages.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser; bilder som visar verksamheten är dess egna, medan licensierat eller genererat material som inte utger sig för att visa verksamheten är tillåtet med källa; Astro med de förberedda, låsta beroendena (kunskap/beroenden.md); inget färgförbud; kunskap/metodkarta.md, Avgörandena).
