---
id: B-20261007-slutposten-avbrutna-skiljer-avbruten-korning-fra
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-6
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Slutposten: avbrutna() skiljer avbruten körning från utebliven post

**Varför:** avbrutna() säger "avbröts" också när posten bara uteblev.

**Förslag:** Skilj en död process med START.json från en körning som slutade men inte kunde skriva posten (slutkod 5).

**Klart när:** Ett prov för vardera fallet ger var sitt besked.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, #KAN-6); README: avbruten respektive UTEBLEV.json
