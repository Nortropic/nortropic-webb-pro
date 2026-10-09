---
id: B-20261009-prova-en-lasande-observatorsmod-i-motorns-claude
status: vilande
kalla: bevakning
kallref: https://code.claude.com/docs/en/plugins/mods/reference (läst 2026-10-09, Claude Code 2.1.290)
skapad: 2026-10-09
prio: normal
steg: kunskap/arbetsyta.md; kontroller/atelje.py session_args; mod/
---
# Pröva en läsande observatörsmod i motorns claude -p-arbetare: exakt kontextandel och underagenternas händelser

**Varför:** Arbetsytan (2026-10-09) följer arbetarna genom transkripten. Två luckor står kvar: kontextens andel av fönstret (transkriptet anger inte fönstret; $.session.usage() i en mod ger Claude Codes egen siffra) och underagenternas anrop (bara Agent-anropet syns). En mod körs i varje process som laddar den, utan sandlåda, så den måste laddas i arbetarna med --plugin-dir; beslutet 2026-10-06 var ingen mod.

**Förslag:** En liten mod i kontroller/mcp/ eller mod/ som bara lyssnar (session.measure, agent.spawn, tool.call med next(e) oförändrat) och skriver valda metadatafält till sessionens förteckningspost eller en egen privat logg; laddas med --plugin-dir i atelje.session_args bakom en växel som är av; prövas med attrapp och ett verkligt sessionsprov innan växeln slås på.

**Klart när:** Ett verkligt sessionsprov visar exakt kontextandel och underagenternas anrop i arbetsytan, med växeln av som standard, oförändrade verktygsdata och behörigheter, och ägarens beslut om att slå på den.
