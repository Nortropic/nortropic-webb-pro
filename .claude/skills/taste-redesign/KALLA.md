# Källa

- **Skill:** `redesign-existing-projects` (mappen `taste-redesign`). Granskar en befintlig sajt, hittar generiska AI-mönster och lyfter den utan att bryta funktion.
- **Källa:** https://github.com/Leonxlnx/taste-skill, `skills/redesign-skill/`, commit `ce26fc25c0e5e8cab638f883de62d9a86ee5e45b` (2026-09-26T11:01:50+02:00, standardgrenen main, ingen tagg; plugin.json 1.0.0). Mappen ändrades senast i `3206dd44fce9` (2026-03-20T17:16:40+01:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Leonxlnx), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 1 från upstream (1 i mappens rot): `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repot har tretton skills under `skills/`; alla är intagna som `taste` (huvudskillen skills/taste-skill) och `taste-<namn>`. Repots `skills/llms.txt` (en indexrad per skill), README, research/, examples/ och assets/ hör inte till någon skillmapp.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** "Randomize dates to appear real" (:86), mot inget påhittat; byter bort Inter (:22); picsum (:43).
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser, inga stock- eller genererade bilder, statiska Astro-sajter, inget färgförbud).
