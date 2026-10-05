# Källa

- **Skill:** `image-to-code` (mappen `taste-image-to-code`). Skriven för Codex: genererar först designbilder, analyserar dem och bygger sedan sajten efter dem.
- **Källa:** https://github.com/Leonxlnx/taste-skill, `skills/image-to-code-skill/`, commit `ce26fc25c0e5e8cab638f883de62d9a86ee5e45b` (2026-09-26T11:01:50+02:00, standardgrenen main, ingen tagg; plugin.json 1.0.0). Mappen ändrades senast i `c0f6c6ad3f49` (2026-04-25T01:05:52+02:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Leonxlnx), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 1 från upstream (1 i mappens rot): `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repot har tretton skills under `skills/`; alla är intagna som `taste` (huvudskillen skills/taste-skill) och `taste-<namn>`. Repots `skills/llms.txt` (en indexrad per skill), README, research/, examples/ och assets/ hör inte till någon skillmapp.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** "must first generate the design image(s) yourself" (:55) och gör bilden till "primary visual source of truth" (:61), mot inga genererade bilder och referenser ur Refero/Mobbin.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser, inga stock- eller genererade bilder, statiska Astro-sajter, inget färgförbud).
