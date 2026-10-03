---
id: B-20261003-mellanslagskontrollen-9-4-fangar-inte-en-mening
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
---
# Mellanslagskontrollen (9.4) fångar inte en mening som löper ihop med en länk efter radbrytning i Astro

**Varför:** Text som slutar på rad N och en <a> på rad N+1 renderades utan mellanslag (Luleå.info@…, på[numret], ellerskriv); granskaren hittade det, standarden inte.

**Förslag:** kontroller/standard_kontroll.py: pröva synlig text där ett ord eller en punkt direkt följs av länktext utan mellanslag; mall/astro/README.md: skriv {' '} före en länk på ny rad.
