# Källa

- **Skill:** `break` (mappen `better-break`). Användaranropad: renderar en vald komponent i alla tillstånd och scenarier på en temporär sida och stresstestar den (med `scenarios.md`).
- **Källa:** https://github.com/jakubkrehel/skills, `skills/break/`, commit `267330e1adfc66a718fb65fa6918c1f06d0a689e` (2026-08-29T19:01:47+02:00, standardgrenen main, plugin.json 1.6.3; samma commit som de sju better-skills som togs in 2026-10-03). Mappen ändrades senast i `267330e1adfc` (2026-08-29T19:01:47+02:00).
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Jakub Krehel), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-05 på ägarens beslut samma dag: "vi behöver säkerställa att alla skills är i sin fullo. installera de även ui ux pro max." Ordagrant: alla git-spårade filer i skillmappen, kontrollerade byte för byte mot upstreams blobbar; inget omskrivet eller borttaget.
- **Filer:** 3 från upstream (2 i mappens rot, 1 i agents/): `SKILL.md`, `agents/openai.yaml`, `scenarios.md`. Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget. `agents/openai.yaml` (Codex-metadata: visningsnamn och `allow_implicit_invocation: false`) följer med ordagrant; Claude Code läser den inte. Mappnamnet har prefixet better- som de övriga Jakub-skillsen här; skillens namn (frontmatter) är oförändrat.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` (körd på en kopia) gav LÅG. Inga dolda tecken, ingen text riktad till agenter, inga skript, inga hemligheter, inga nätanrop vid laddning.
- **Krockar med våra beslut:** en scratch route i appen (SKILL.md:35) med `"use client"` för Next (:37); sidan lämnas kvar tills användaren ber om att den tas bort (:66–68), och i Astro publiceras den om den ligger i src/pages.
- **Så används skillen här:** Läses av skaparsessionerna i skapandeflödet som stöd; ägarens beslut och kundens behov går före skillens standardförslag (hos oss: layout, palett och typografi får kopieras från referenser, inga stock- eller genererade bilder, statiska Astro-sajter, inget färgförbud). `disable-model-invocation: true`: modellen kan inte själv ladda skillen via Skill-verktyget; den startas med /break i prompten.
