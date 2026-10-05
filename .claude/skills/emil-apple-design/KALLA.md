# Källa

- **Skill:** `apple-design` (mappen `emil-apple-design`). Apples principer för gränssnitt och fysisk, avbrytbar rörelse, översatta till webben.
- **Källa:** https://github.com/emilkowalski/skills, `skills/apple-design/`, commit `e8a175de22ae1e49370fc144c1f3bb9aeedf988d` (2026-10-02T06:43:31-04:00, standardgrenen main). Mappen ändrades senast i `85e8e2363b71` (2026-09-15T17:52:10+02:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Emil Kowalski), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 1 från upstream (1 i mappens rot): `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repots fjorton skills är alla intagna som `emil-<namn>`; `performance-cheatsheet.md` och README i repots rot hänvisas inte från någon skill.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** "Avoid CSS transitions and `@keyframes` for anything gesture-driven" (SKILL.md:69); "Default to the platform's system font" (:234) före referensens typsnitt.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser; bilder som visar verksamheten är dess egna, medan licensierat eller genererat material som inte utger sig för att visa verksamheten är tillåtet med källa; Astro med de förberedda, låsta beroendena (kunskap/beroenden.md); inget färgförbud; kunskap/metodkarta.md, Avgörandena).
