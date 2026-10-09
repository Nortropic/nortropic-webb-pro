---
id: B-20261009-typsnitt-per-kandidat-typsnitt-py-har-ingen-kand
status: vilande
kalla: bygge
kallref: RAPPORT-2026-10-09-formagoprov-kvalitetsprov
skapad: 2026-10-09
prio: normal
steg: kontroller/typsnitt.py, kontroller/kandidater.py (forbered_projekt)
---
# Typsnitt per kandidat: typsnitt.py har ingen --kandidat

**Varför:** Kvalitetsprovet 2026-10-09: båda armarna försökte typsnitt.py --kandidat, föll tillbaka på basprojektet och delade sedan typsnitten genom node_modules. Låset tål det sedan ebe3d2b, men en arm kan se den andras typsnitt.

**Förslag:** En --kandidat som lägger beroendet i kandidatens egen package.json, eller som åtminstone bokför vilken kandidat som installerade vad.

**Klart när:** Två kandidater installerar var sitt typsnitt utan att den andras package.json ändras, eller posten säger vem som installerade vad.
