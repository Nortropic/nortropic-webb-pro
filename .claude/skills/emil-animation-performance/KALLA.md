# Källa

- **Skill:** `animation-performance` (mappen `emil-animation-performance`). Diagnos när en animation tappar bildrutor:
  vilka egenskaper som animeras (layout, paint, composite), var rörelsen körs (huvudtråden, CSS, WAAPI,
  requestAnimationFrame), React-omritning per bildruta, ärvda CSS-variabler, blur och när `will-change` hjälper.
- **Källa:** https://github.com/emilkowalski/skills, `skills/animation-performance/`, commit
  `2d228630ba1446365f614a108cb8252f1feda202` (2026-10-11T15:58:32+02:00, standardgrenen main). Mappen ändrades senast i
  samma commit.
- **Licens:** MIT. `LICENSE` (Copyright (c) 2026 Emil Kowalski), repots licensfil, kopierad till mappen.
- **Intagen:** 2026-10-13 på valideringen av skillsen 2026-10-12 (del 2, åtgärd E1), inom ägarens nattmandat samma dag
  ("genomför valideringarnas och regelinventeringens åtgärder") och ägarens ord 2026-10-05: "vi behöver säkerställa att
  alla skills är i sin fullo". Ordagrant: skillmappens enda git-spårade fil, `SKILL.md`, med samma blob som upstream
  (`d688dd7c3ba143c6ae17efd2bc665380d5252c5a`); inget omskrivet eller borttaget.
- **Filer:** 1 från upstream (`SKILL.md`). Våra tillägg: `KALLA.md`, `LICENSE`.
- **Utelämnat:** inget ur skillmappen.
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py`, körd på en kopia, gav LÅG: inga dolda tecken, ingen text
  riktad till agenter, inga skript, inga behörigheter, omkring 3 760 tokens (207 alltid, 3 275 vid användning).
- **Krockar med våra beslut:** inga funna. Skillen har `## Initial Response`; som Emils övriga skills aktiveras den med Skill (`kompetens.SLAPPTA_VANTANDE`), och
  promptens villkor att ingen svarar ersätter väntesvaret. Den säger
  "Framer Motion", som hos oss är `motion/react` (`kunskap/beroenden.md`, Motion). Delningen "CSS för enkel rörelse,
  Motion för fjädrar och gester" är samma som metodkartans Avgöranden Teknik.
- **Så används skillen här:** alternativ i bandets stationer rorelse och polish och i rörelseblocken, när en rörelse
  hackar eller tekniken väljs av prestandaskäl. Den kvalificerar emil-animate:s generella råd (metodkartan, Avgörandena:
  Rörelserådets räckvidd). En prestandabrist rättas med namngiven orsak, och mätningen på en riktig enhet redovisas som
  oprövad när den inte gjorts.
