---
id: B-20261003-prelaunch-py-s-besked-om-saknat-matkvitto-pekar
status: vilande
kalla: bygge
kallref: kunder/salong-kreativ/prov/prelaunch.md
skapad: 2026-10-03
prio: normal
steg: steg 6 (provet)
---
# prelaunch.py:s besked om saknat mätkvitto pekar på verktyg/kor_profil.py, som inte finns

**Varför:** prov/prelaunch.md i varje bygge skriver "inget mätkvitto (--matning ur verktyg/kor_profil.py matning)"; verktyget fanns i Digitala och Runtime. kunskap/prelaunch.md säger sedan b0b3233 att grind 2–4 avgörs av provets lighthouse, spill och axe.

**Förslag:** Efter A/B-kedjan. kontroller/prelaunch.py: beskeden för grind 2–4 säger att provets grindar lighthouse, spill och axe avgör i vårt flöde; inga hänvisningar till verktyg/.

**Klart när:** grep efter verktyg/ i kontroller/prelaunch.py ger noll träffar, och rokprov.sh är grönt.
