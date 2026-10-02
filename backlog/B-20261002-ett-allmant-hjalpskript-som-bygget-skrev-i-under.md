---
id: B-20261002-ett-allmant-hjalpskript-som-bygget-skrev-i-under
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · anthropics/skills
skapad: 2026-10-02
prio: normal
steg: 7 Rapport (Brister i verktygen)
---
# Ett allmänt hjälpskript som bygget skrev i underlag/<slug>/skript/ blir en backlogpost, så att upprepat arbete hamnar i kontroller/

**Varför:** Egen innovation ur skill-creator (dom nej): upprepat arbete i flera körningar är signalen att en skill ska få ett eget skript. Tre byggen skrev var sitt nästan likadant skript för LCP, CLS, TBT och sidvikt ur Lighthouse-filerna (sundboms-el lh.py, lulea-snickaren-abx lh.py, paint-it-black-maleri lh_sammandrag.py), eftersom kontroller/lighthouse.mjs bara skriver ut P/A/BP/SEO (rad 63) och inte sparar sidvikten (rad 37-44), men ingen av dem lade en backlogpost; bara kirurgen såg mönstret, i efterhand.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md steg 7, stycket Brister i verktygen (rad 313-315): lägg till en mening om att ett skript i underlag/<slug>/skript/ som inte är knutet till verksamheten (läser en kontrolls utdata, hämtar bilder, räknar något) också är en brist i verktygen, och att posten anger skriptets sökväg och vilken kontroll som borde ha gjort det. Inget annat ändras.

**Klart när:** Stycket Brister i verktygen i bygg-sajt/SKILL.md nämner allmänna skript i underlag/<slug>/skript/; nästa bygge som skriver ett sådant skript har en backlogpost med kalla bygge som anger dess sökväg
