# Källa

- **Skill:** `stitch-design-taste` (mappen `taste-stitch`). Regler för Google Stitch och en medföljande `DESIGN.md`-mall för semantiska designsystem.
- **Källa:** https://github.com/Leonxlnx/taste-skill, `skills/stitch-skill/`, commit `ce26fc25c0e5e8cab638f883de62d9a86ee5e45b` (2026-09-26T11:01:50+02:00, standardgrenen main, ingen tagg; plugin.json 1.0.0). Mappen ändrades senast i `84ff339312d2` (2026-06-09T23:06:12+03:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Leonxlnx), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 2 från upstream (2 i mappens rot): `DESIGN.md`, `SKILL.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen. Repot har tretton skills under `skills/`; alla är intagna som `taste` (huvudskillen skills/taste-skill) och `taste-<namn>`. Repots `skills/llms.txt` (en indexrad per skill), README, research/, examples/ och assets/ hör inte till någon skillmapp.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** kräver Google Stitch (:14); föreskriver Fraunces och Instrument Serif (:51), tvärtemot taste:180; picsum i DESIGN.md:117.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser; bilder som visar verksamheten är dess egna, medan licensierat eller genererat material som inte utger sig för att visa verksamheten är tillåtet med källa; Astro med de förberedda, låsta beroendena (kunskap/beroenden.md); inget färgförbud; kunskap/metodkarta.md, Avgörandena).
