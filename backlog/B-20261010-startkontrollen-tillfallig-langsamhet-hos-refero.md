---
id: B-20261010-startkontrollen-tillfallig-langsamhet-hos-refero
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F9
skapad: 2026-10-10
prio: normal
steg: startkontrollen, MCP
---
# Startkontrollen: tillfällig långsamhet hos Refero stoppar hela starten

**Varför:** 2026-10-10 12:19Z stoppade startkontrollen två starter eftersom Referos verktygslista inte svarade (claude mcp list: tools fetch failed — Request timed out; direktklienten: initialize 16 s, tools/list timeout efter 150 s). Grinden gjorde rätt, eftersom researchens obligatoriska Refero-undersökning inte kan göras, men ett tillfälligt fel hos tjänsten stoppar då hela körningen utan nytt försök.

**Förslag:** Ett begränsat nytt försök med längre väntan innan startkontrollen stoppar på en MCP-timeout, och ett besked om att det är tjänsten som är långsam. Grindens regel ändras inte.

**Klart när:** Startkontrollen gör ett nytt försök vid timeout, med prov för att en kvarstående timeout fortfarande stoppar och att ett lyckat andra försök släpper starten.
