---
id: B-20261007-slutposten-en-dom-som-bygget-andrat-gor-inte-aga
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-3
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Slutposten: en dom som bygget ändrat gör inte ägarens tidigare domar obelagda för alltid

**Varför:** Har bygget ändrat DOM.json blir också ägarens tidigare domar i filen "ej belagda" för alltid.

**Förslag:** Jämför domarna rad för rad mot läget vid starten, och räkna de oförändrade som belagda.

**Klart när:** Ett prov där bygget lägger till en rad behåller ägarens äldre rader som belagda.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, #KAN-3); korslut.agaren_vid_slut: domarna i kopian från starten räknas
