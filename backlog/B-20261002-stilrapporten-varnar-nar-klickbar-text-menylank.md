---
id: B-20261002-stilrapporten-varnar-nar-klickbar-text-menylank
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS, "How To Use Claude Code To Build Amazing Sites With Opus 5.5" (YouTube DP7mgLUKN_U)
skapad: 2026-10-02
prio: normal
steg: 6 (prov); kontroller/stil.mjs
andrad: 2026-10-03T00:17Z
---
# Stilrapporten varnar när klickbar text (menylänk, knapp, sidfotslänk, brödsmula) bryts på två rader i 390 px

**Varför:** Kirurgens dom om AI LABS-videon är nej, men Hallmarks grind 49 (klickbar text på två rader läses av besökaren som ett fel, inte som avsikt) saknar motsvarighet hos oss: spillgrinden mäter horisontellt spill och stilrapporten klickytor under 24 px, men ingen kontroll mäter radbrytning i klickbar text. Ägaren pekade i A/B 2026-10-02 ut A:s menylänkar i två rader som det som gjorde första vyn sämre (LARDOMAR.md rad 102).

**Förslag:** kontroller/stil.mjs, i matPaSidan() bredvid mätningen av små klickytor: för varje synlig a och button i 390 px, räkna antalet rader (getClientRects().length för inline-element, annars höjd delad med radhöjd); fler än en rad ger en varning per sida med elementets text, i samma form som varningarna på rad 201–204. Information, ingen grind; standardkontrollen rörs inte.

**Klart när:** STIL.md för ett bygge med en avsiktligt lång menylänk i 390 px visar varningen med länktexten; ett bygge utan brutna länkar visar ingen; kontroller/rokprov.sh slutar grönt.
