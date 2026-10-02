---
id: B-20261002-provets-skarmrutor-vy-bredd-ruta-01-png-borjar-m
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren-abx/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 5-6
---
# Provets skärmrutor vy-<bredd>-ruta-01.png börjar mitt på sidan, inte överst

**Varför:** I lulea-snickaren-abx visade hem/vy-390-ruta-01.png tjänstebilderna och Dan-sektionen, inte sidhuvudet och h1. Granskaren skrev i alla tre omgångarna att ruta-01 börjar mitt på sidan och fick ta egna skärmbilder med sida.mjs för att bedöma första vyn.

**Förslag:** kontroller/webblasare/inspektera.mjs (eller den del av prova.py som delar helsidan i rutor): numrera rutorna uppifrån och ned från scrollY 0, och pröva att ruta-01 innehåller sidans h1 på startsidan.
