---
id: B-20261001-prelaunch-grind-0-kraver-env-example-som-en-obev
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
---
# Prelaunch grind 0 kräver .env.example som en obevakad körning inte får skriva

**Varför:** Luleå-Snickaren är statisk utan miljövariabler. Grind 0 blev FAIL för att .env.example saknas, och sessionens behörigheter nekar skrivning av .env*-filer, så grinden kan aldrig bli PASS i ett bygge.

**Förslag:** mall/astro/: lägg en .env.example med raden att sajten saknar miljövariabler, så att den följer med när mallen kopieras i steg 5.
