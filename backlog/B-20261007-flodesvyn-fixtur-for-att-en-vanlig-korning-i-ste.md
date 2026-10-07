---
id: B-20261007-flodesvyn-fixtur-for-att-en-vanlig-korning-i-ste
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r96-om3.md
fynd: GR-20261007-r96-om3#BÖR-1
skapad: 2026-10-07
prio: normal
steg: flodesvy-20261006: kontroller/rokprov/revision/prov_flode.py
---
# Flödesvyn: fixtur för att en vanlig körning i steg fel inte räknas som en stoppad start

**Varför:** Mutationen M3-2 överlever; med den skulle det riktiga läget få fel Nästa. Koden gör rätt.

**Förslag:** En fixtur med steg fel utan startkontrollens besked.

**Klart när:** M3-2 blir röd. Görs efter ägarens sammanslagning av flodesvy-20261006.
