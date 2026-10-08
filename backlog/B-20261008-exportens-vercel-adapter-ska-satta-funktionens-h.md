---
id: B-20261008-exportens-vercel-adapter-ska-satta-funktionens-h
status: vilande
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#D3
skapad: 2026-10-08
prio: normal
steg: main: kontroller/exportera.py, kunskap/lansering.md
---
# Exportens Vercel-adapter ska sätta funktionens högsta körtid så att formulärets tidsbudget ryms

**Varför:** forfragan.js budgeterar 10+8+2 s plus kroppsläsning; varken vercel.json eller adaptern sätter maxDuration. Utan Fluid compute kan plattformens förval (15 s) avbryta efter att mejlet gått men före svaret: besökaren får 504 och texten är borta (GR-20261008-r117-claude#D3, inte prövat mot plattformen). lansering.md kräver nu kontrollen för hand.

**Förslag:** adapter: vercel({ maxDuration: 30 }) i exportera.med_adapter när optionen verifierats i den låsta @astrojs/vercel-versionen, och prov_revision som läser den exporterade konfigurationen.

**Klart när:** Den exporterade astro.config.mjs bär en verifierad körtidsgräns på minst 30 s, prövad i exportens byggprov.
