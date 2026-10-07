---
id: B-20261007-dokumentationsvyn-en-fil-med-tva-forteckningsrad
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#KAN-4
skapad: 2026-10-07
prio: normal
steg: main: dashboard/server.py, kontroller/rokprov/revision/prov_dokumentationsvy.py
---
# Dokumentationsvyn: en fil med två förteckningsrader visas en gång i listan över ändrade och saknade filer

**Varför:** Två förteckningsrader för samma fil (med ./, i NFC och NFD) ger samma sökväg två gånger i listan över ändrade eller saknade filer (server.py, granskningsrapporter). Rapporten själv visas en gång.

**Förslag:** Normalisera sökvägen (NFC, utan ./) innan raderna slås ihop.

**Klart när:** Ett prov med två sådana rader visar sökvägen en gång.
