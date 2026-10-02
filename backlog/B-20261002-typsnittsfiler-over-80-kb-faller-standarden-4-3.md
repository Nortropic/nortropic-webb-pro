---
id: B-20261002-typsnittsfiler-over-80-kb-faller-standarden-4-3
status: klar
kalla: dom
kallref: LARDOMAR.md · AB · 2026-10-02
skapad: 2026-10-02
prio: hog
steg: 5
commit: b79ae56
andrad: 2026-10-02T17:09Z
---
# Typsnittsfiler över 80 kB fäller standarden 4.3: latin-subset och bara de axlar som används

**Varför:** Ägaren (AB 2026-10-02): B:s font är 47 kB mot A:s 99 kB, ett av skälen till B. 4.3 kräver latin-subset men ingen kontroll mäter storleken.

**Förslag:** standard_kontroll: en WOFF2-fil över 80 kB i dist är fel 4.3 med filnamn, storlek och rättningen (latin-subset, bara de axlar som används).

**Klart när:** Standarden fäller en för stor WOFF2; rökprovet prövar det

**Klar (2026-10-02):** över 120 kB, eller över 80 kB utan bredd-axel = fel; med bredd-axel information (L2 godtog Archivo i smal bredd); abx 96 kB får information
