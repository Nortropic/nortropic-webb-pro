# Källa

- **Skill:** `frontend-design` (mappen `frontend-design`). Anthropics skill för distinkt, avsiktlig visuell design: estetisk riktning, typografi, färg och val som inte ser ut som mallar.
- **Källa:** https://github.com/anthropics/skills, `skills/frontend-design/`, commit `8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4` (2026-09-28T19:20:03-07:00, standardgrenen main). Mappen ändrades senast i `41bbe19d1a1a` (2026-09-03T09:37:13-07:00).
- **Licens:** Apache-2.0. `LICENSE.txt` ligger i upstream-mappen (frontmatterns `license: Complete terms in LICENSE.txt`); ingen extra kopia behövs.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 2 från upstream (2 i mappens rot): `LICENSE.txt`, `SKILL.md`. Våra tillägg: `KALLA.md`.
- **Utelämnat:** inget.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** "not mistaken for anyone else's" (SKILL.md:9) och "confirmed the relative uniqueness" (:53) drar mot kopiering av referenser; "Avoid these default typographic treatments" (:25) och fem färgkluster med hex (:39–43) är kalibrering, inte förbud ("All traits are legitimate for some briefs", :45; briefens ord vinner). "confirm with the client" (:13) och påhittad platshållartext (:34) passar inte en autonom session.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser, inga stock- eller genererade bilder, statiska Astro-sajter, inget färgförbud).
