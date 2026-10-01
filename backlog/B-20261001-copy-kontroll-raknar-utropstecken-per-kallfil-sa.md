---
id: B-20261001-copy-kontroll-raknar-utropstecken-per-kallfil-sa
status: klar
kalla: bygge
kallref: kunder/sundboms-el/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
commit: 636cf33
andrad: 2026-10-01T23:19Z
---
# copy_kontroll räknar utropstecken per källfil, så ordagranna kundcitat i en datafil flaggas

**Varför:** I sundboms-el låg 30 kundomdömen ordagrant i src/data/omdomen.ts. Kontrollen rapporterade 20 utropstecken för den filen, trots att ingen sida hade ett eget utropstecken och citaten inte får ändras.

**Förslag:** kontroller/copy_kontroll.py: räkna utropstecken per renderad sida (dist/**/index.html) och hoppa över text inuti blockquote/q, eller rapportera citat separat som 'i citat'.

**Klar (2026-10-01):** genomförd natten 2026-10-01/02
