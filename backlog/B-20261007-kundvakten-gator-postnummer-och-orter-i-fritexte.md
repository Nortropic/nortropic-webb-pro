---
id: B-20261007-kundvakten-gator-postnummer-och-orter-i-fritexte
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r104.md
fynd: GR-20261007-r104#B1
skapad: 2026-10-07
prio: hog
steg: main: kontroller/skapande.py (forbjudna_termer), kontroller/kundvakt.py, kontroller/rokprov/revision/prov_startkvitto.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Kundvakten: gator, postnummer och orter i fritexten i VERKSAMHET.json skyddas

**Varför:** Fritextfältet not i den verkliga kundens VERKSAMHET.json har två gatunamn som inte skyddas, och av två postnummerlika tal skyddas ett. Frågor med gatunamnet släpps igenom, både före och efter grenen kundvakt-namn-20261007; bristen är äldre. Adresser är kunduppgifter som aldrig ska nå externa tjänster.

**Förslag:** forbjudna_termer (skapande.py) läser också not och belagg. Gatunamn känns igen på suffix, postnummer läggs till siffrorna och orten efter postnumret till orden. På sikt kan en andra adress bli ett eget fält i schemat (ägarens beslut).

**Klart när:** Ett prov med en gata, ett postnummer och en ort i not stoppar frågor med dem, och de generiska frågorna släpps fortfarande. Görs före nästa designkörning.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (6d440de, BESLUT 2026-10-07 kundvaktens adresser, rubriker och orter: r104#B1); prov_startkvitto 10d
