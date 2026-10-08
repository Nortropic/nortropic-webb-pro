---
id: B-20261007-slutposten-visa-raknar-agarens-senare-dom-ocksa
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-4
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Slutposten: --visa räknar ägarens senare dom också efter en avbruten körning

**Varför:** Efter en körning som avbrutits utan slutpost räknar --visa aldrig ägarens senare dom över det föregående bygget.

**Förslag:** Låt --visa gå till den senaste posten med slutpost när den senaste körningen saknar en.

**Klart när:** Ett prov med en avbruten körning efter ett godkänt bygge visar ägarens senare dom.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, #KAN-4); korslut.aktuell: vakten skriver posten, ägarens senare dom räknas
