---
id: B-20261007-dokumentationsvyn-en-fil-med-tva-forteckningsrad
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#KAN-4
skapad: 2026-10-07
prio: normal
steg: main: dashboard/server.py, kontroller/rokprov/revision/prov_dokumentationsvy.py
commit: 7dfb8e3
andrad: 2026-10-08T22:15Z
---
# Dokumentationsvyn: en fil med två förteckningsrader visas en gång i listan över ändrade och saknade filer

**Varför:** Två förteckningsrader för samma fil (med ./, i NFC och NFD) ger samma sökväg två gånger i listan över ändrade eller saknade filer (server.py, granskningsrapporter). Rapporten själv visas en gång.

**Förslag:** Normalisera sökvägen (NFC, utan ./) innan raderna slås ihop.

**Klart när:** Ett prov med två sådana rader visar sökvägen en gång.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08/09: en fil räknas efter sin verkliga sökväg i NFC; prov_dokumentationsvy rött mot 03fab0e, grönt efter (RAPPORT-2026-10-08-natt-codex-rester-backlog). Inte verifierad.
