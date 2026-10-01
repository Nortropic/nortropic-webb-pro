---
id: B-20261001-overvag-en-karantanlasare-for-text-ur-frammande
status: vilande
kalla: bevakning
kallref: Omvärldsbevakning 2026-10-01: Simon Willison, prompt injection design patterns (dual LLM, 2025-06-13); OpenAI agent builder safety
skapad: 2026-10-01
prio: normal
steg: kirurgen
---
# Överväg en karantänläsare för text ur främmande repon

**Varför:** Kirurgen läser främmande innehåll och kan committa. Commitvakten, vitlistan och förgranskningen begränsar skadan, men forskningen rekommenderar också att en läsare utan skrivverktyg läser råtexten och lämnar ett fast schema till den som dömer.

**Förslag:** Bara om förgranskningen eller ägaren ser verkliga försök att styra kirurgen: en egen agent (.claude/agents/lasare.md, bara Read, Glob, Grep) som läser repotexten och lämnar ett fast schema. Bilder och sidor ses fortfarande direkt av kirurgen.

**Klart när:** Beslut taget och bokfört; byggt om beslutet blev ja.
