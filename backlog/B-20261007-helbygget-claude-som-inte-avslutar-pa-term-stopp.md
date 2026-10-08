---
id: B-20261007-helbygget-claude-som-inte-avslutar-pa-term-stopp
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-5
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Helbygget: claude som inte avslutar på TERM stoppas med KILL

**Varför:** Det finns ingen eskalering om claude inte avslutar på TERM.

**Förslag:** KILL efter en frist, tillsammans med BÖR-2.

**Klart när:** En attrapp som ignorerar TERM stoppas inom fristen.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (BESLUT 2026-10-07 skyddet…, #KAN-5: NWP_FRIST, SIGKILL); prov_slutpost rad 980
