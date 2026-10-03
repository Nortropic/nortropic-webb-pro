---
id: B-20261003-standardens-bildvikt-4-2-laser-img-src-men-astro
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
---
# Standardens bildvikt (4.2) läser img src, men Astros Image lägger originalstorleken i src

**Varför:** Startsidans bild fick 271 kB i 4.2 fast webbläsaren hämtar 480- eller 720-varianten ur srcset; först med width satt på Image blev src den mindre filen.

**Förslag:** kontroller/standard_kontroll.py 4.2: mät den srcset-kandidat som motsvarar sizes vid 390 och 1440, eller mall/astro/README.md punkt 4: sätt width på första vyns Image.
