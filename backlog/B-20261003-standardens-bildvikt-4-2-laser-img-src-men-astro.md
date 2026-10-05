---
id: B-20261003-standardens-bildvikt-4-2-laser-img-src-men-astro
status: vilande
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
andrad: 2026-10-05T06:55Z
---
# Standardens bildvikt (4.2) läser img src, men Astros Image lägger originalstorleken i src

**Varför:** Startsidans bild fick 271 kB i 4.2 fast webbläsaren hämtar 480- eller 720-varianten ur srcset; först med width satt på Image blev src den mindre filen.

**Förslag:** kontroller/standard_kontroll.py 4.2: mät den srcset-kandidat som motsvarar sizes vid 390 och 1440, eller mall/astro/README.md punkt 4: sätt width på första vyns Image.

**Klart när:** 4.2 mäter den srcset-kandidat som sizes väljer vid 390 och 1440 i stället för src; rökprovet har ett fall med srcset där src är störst.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; 4.2 mäter img src, som Astros Image fyller med originalstorleken. Kontrollvägen väljs (srcset-kandidaten), eftersom README redan nämner width utan att det hjälpte. Ingår i paketet före nästa helbygge. Färdigkriteriet tillagt i avstämningen (posten saknade det).
