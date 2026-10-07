---
id: B-20261007-kompetensprovet-jamforelsen-mellan-metodkartan-o
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r103.md
fynd: GR-20261007-r103#K2
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kompetens.py
---
# Kompetensprovet: jämförelsen mellan metodkartan och koden går inte att lura med ett alias

**Varför:** Jämförelsen mellan metodkartans lista över sessioner utan block och koden (kompetens.py) är syntaktisk och kan luras av ett alias för atelje.session. Ingen kod gör det i dag.

**Förslag:** Registrera sessionernas pass vid anropet (till exempel ett obligatoriskt pass-argument i atelje.session) och jämför mot registreringen.

**Klart när:** Ett alias för atelje.session fälls av provet.
