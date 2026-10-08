---
id: B-20261007-helbygget-lasen-efter-en-dodad-korning-hindrar-i
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-2
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py, dashboard/server.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Helbygget: låsen efter en dödad körning hindrar inte ägarens dom

**Varför:** Efter SIGKILL är DOM.json, kunder/ och underlag/ låsta tills nästa start, så dashboardens dom kan inte sparas under tiden.

**Förslag:** korslut --avbrutna eller dashboarden släpper låsen för en körning vars process är död och vars START.json saknar slutpost.

**Klart när:** Efter en SIGKILL kan ägarens dom sparas utan att någon ny körning startas.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, vakten #KAN-2); README: ägarens dom kan sparas efter att vakten släppt låsen
