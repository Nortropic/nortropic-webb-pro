---
id: B-20261007-korregistret-en-gammal-vantefil-far-inte-se-ut-s
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-D
skapad: 2026-10-07
prio: normal
steg: main: kontroller/korregister.py, kontroller/startkontroll.py
---
# Körregistret: en gammal väntefil får inte se ut som en start som väntar

**Varför:** Sedan EPERM räknas som levande tror start_vantar att en start väntar när det bara finns en gammal väntefil. Granskaren fick False med a303a2c och True nu.

**Förslag:** Pröva starttiden för pid:en också vid EPERM, och räkna en väntefil vars process inte stämmer som gammal.

**Klart när:** Ett prov med en gammal väntefil och en främmande pid ger False.
