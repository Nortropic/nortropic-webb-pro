# Källa

- **Skill:** `prototype` (mappen `emil-prototype`). Bygger flera olika versioner av en UI-del bakom en väljare (med `PICKER.md`); körs bara på uttryckligt anrop.
- **Källa:** https://github.com/emilkowalski/skills, `skills/prototype/`, commit `e8a175de22ae1e49370fc144c1f3bb9aeedf988d` (2026-10-02T06:43:31-04:00, standardgrenen main). Mappen ändrades senast i `85e8e2363b71` (2026-09-15T17:52:10+02:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Emil Kowalski), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 2 från upstream (2 i mappens rot): `PICKER.md`, `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repots fjorton skills är alla intagna som `emil-<namn>`; `performance-cheatsheet.md` och README i repots rot hänvisas inte från någon skill.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** en route i `/prototypes/<slug>` (SKILL.md:62), som Astro publicerar från src/pages; "plausible names and numbers" (:29).
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser, inga stock- eller genererade bilder, statiska Astro-sajter, inget färgförbud). `disable-model-invocation: true`: modellen kan inte själv ladda skillen via Skill-verktyget; den startas med /prototype i prompten.
