---
id: B-20261003-provets-lighthouse-grind-ger-byggaren-titel-matv
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Chrome for Developers, Lighthouse audits with DevTools for agents
skapad: 2026-10-03
prio: normal
steg: 6 Prov (kontroller/lighthouse.mjs och prova.py)
andrad: 2026-10-05T06:55Z
---
# Provets Lighthouse-grind ger byggaren titel, mätvärde och de första träffarna för varje underkänd audit, inte bara dess id

**Varför:** Egen innovation ur videon (dom nej): källans enda bärande poäng är att agenten får auditens råd direkt och rättar utan att någon klistrar in rapporten [TAL 01:41]. Hos oss listar lighthouse.mjs rad 42 bara id:n för underkända audits och prova.py rad 389 skriver dem i PROV.md; vad som brast och var står bara i hem-mobil.json på 3 000–5 000 rader, och tre byggen har redan skrivit egna skript för att läsa de filerna (B-20261002-ett-allmant-hjalpskript).

**Förslag:** kontroller/lighthouse.mjs rad 42: underkanda blir en lista av objekt med id, title, displayValue och de första tre items-raderna (url eller node.snippet, högst 120 tecken), i stället för bara id. kontroller/prova.py rad 389: raden per underkänd sida skriver id, title och displayValue; items under grindens detalj. Inget annat ändras: kraven, omgångarna och lighthouse.json:s övriga fält som förut. kontroller/rokprov.sh ska sluta grönt; prospekt_poang.py läser inte underkanda (kontrollera med grep).

**Klart när:** lighthouse.mjs ger per underkänd audit id, titel, mätvärde och tre träffar, också i unionen över medianmätningarna; PROV.md visar titel och mätvärde; rökprovet visar en underkänd audit med titel och mätvärde.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; pekarna i posten är inaktuella efter medianmetoden (lighthouse.mjs rad 68 och 93, prova.py rad 490), och unionen över mätningarna måste bära objekt. Ingår i paketet före nästa helbygge. Färdigkriteriet omskrivet i avstämningen; tidigare: "En sida som hamnar under kravet ger i PROV.md en rad per underkänd audit med titel och mätvärde (till exempel render-blocking-insight: Render blocking requests, Est savings of 310 ms) och de första träffarna i detaljen; rökprovet grönt."
