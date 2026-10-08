---
id: B-20261007-kandidaternas-status-sparar-mcp-utfallen-och-til
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r102-om.md
fynd: GR-20261007-r102-om#K2
skapad: 2026-10-07
prio: normal
steg: gren C2: kontroller/kandidater.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Kandidaternas status sparar MCP-utfallen och tillståndet och visar dem i redovisningen

**Varför:** Kompetenskvittot räknar ut mcp_utfall, mcp_lage och tillstand, men kandidaternas status sparar dem inte. Ett tomt Mobbin-svar från en skapare syns därför i redovisningen som "mobbin ×1", utan utfall.

**Förslag:** Spara fälten i kandidaternas status och visa dem i REDOVISNING.md (gren C2 i uppdraget 2026-10-07).

**Klart när:** Ett prov med ett tomt och ett lyckat anrop visar utfallen var för sig i redovisningen.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (c7c39b7 Motion/GSAP, BESLUT 2026-10-07 gren H2); kandidater.py kvitto med mcp_utfall/mcp_lage; prov_rorelse fall 11
