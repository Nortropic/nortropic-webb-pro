---
id: B-20261001-skillen-sager-inte-att-typsnittsregistret-ska-li
status: vilande
kalla: bygge
kallref: kunder/paint-it-black-maleri/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 5
---
# Skillen säger inte att typsnittsregistret ska ligga i public/bilder/TYPSNITT-IKONER.json

**Varför:** prelaunch.py grind 6 läser bilder/TYPSNITT-IKONER.json relativt dist/, men skillen nämner inte registret och bild.md säger bara 'kundbygget'. I paint-it-black-maleri hittade jag platsen först genom att läsa prelaunch.py.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md, raden Typsnitt: lägg till 'registrera varje typsnittsfil i kunder/<slug>/sajt/public/bilder/TYPSNITT-IKONER.json (form i kunskap/bild.md) och kopiera licensen bredvid filen'.
