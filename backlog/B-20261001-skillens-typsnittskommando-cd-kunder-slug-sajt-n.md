---
id: B-20261001-skillens-typsnittskommando-cd-kunder-slug-sajt-n
status: vilande
kalla: bygge
kallref: kunder/paint-it-black-maleri/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 5
---
# Skillens typsnittskommando 'cd kunder/<slug>/sajt && npm install' strider mot regeln om ett kommando per anrop

**Varför:** I paint-it-black-maleri körde jag npm install utan cd för att följa regeln om ett enkelt kommando, och det hamnade i repots rot: package.json, package-lock.json och node_modules/ skapades där. ta_bort.py får inte ta bort dem utanför kunder/ och underlag/, så de ligger kvar ospårade tills ägaren tar bort dem.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md, raden Typsnitt: skriv 'npm install --prefix kunder/<slug>/sajt @fontsource-variable/<namn>' i stället för cd-kedjan.
