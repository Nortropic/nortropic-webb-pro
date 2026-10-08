---
id: B-20261007-helbygget-slutkoden-vid-sighup-stammer-med-poste
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-1
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Helbygget: slutkoden vid SIGHUP stämmer med postens

**Varför:** När terminalen stängs (SIGHUP) slutar kor.sh med 120, fast posten säger 4.

**Förslag:** Låt fällan avsluta med postens slutkod.

**Klart när:** Ett prov med SIGHUP ger samma slutkod i processen och i posten.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, slutbeskedet #KAN-1); prov_slutpost rad 1028 (SIGHUP ger postens slutkod)
