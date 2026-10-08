---
id: B-20261007-helbygget-ett-kommando-som-faller-under-set-e-ge
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om2.md
fynd: GR-20261007-r101-om2#KAN-5
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Helbygget: ett kommando som faller under set -e ger en slutpost med skälet

**Varför:** Underförstådda set -e-utgångar ger ingen post. När mkdir -p prov föll slutade kor.sh med 1, utan någon rad på stdout och utan post, och nästa start säger bara "avbröts utan slutpost". Samma slag av utgång finns på flera rader. Alla är ovanliga.

**Förslag:** En ERR-fälla som skriver en kort post med kommandot och raden, eller uttryckliga stopp där det kan falla.

**Klart när:** Ett prov där mkdir faller ger en post med skälet.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, GR-20261007-r101-om2#KAN-5); README: slutkod 2 med skälet
