---
id: B-20261007-korregistret-en-gammal-vantefil-far-inte-se-ut-s
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-D
skapad: 2026-10-07
prio: normal
steg: main: kontroller/korregister.py, kontroller/startkontroll.py
commit: 2f4fe7a
andrad: 2026-10-08T21:28Z
---
# Körregistret: en gammal väntefil får inte se ut som en start som väntar

**Varför:** Sedan EPERM räknas som levande tror start_vantar att en start väntar när det bara finns en gammal väntefil. Granskaren fick False med a303a2c och True nu.

**Förslag:** Pröva starttiden för pid:en också vid EPERM, och räkna en väntefil vars process inte stämmer som gammal.

**Klart när:** Ett prov med en gammal väntefil och en främmande pid ger False.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08: väntefilen bär starttiden; prov_startkontroll med en gammal väntefil och en främmande pid (pid 1, EPERM) ger False, rött mot basen och grönt efter. Inte verifierad.
