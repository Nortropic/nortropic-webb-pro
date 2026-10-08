---
id: B-20261007-flodesvyn-fixtur-for-blindningen-efter-en-stoppa
status: ersatt
kalla: granskning
kallref: granskningar/GR-20261007-r96-om3.md
fynd: GR-20261007-r96-om3#BÖR-2
skapad: 2026-10-07
prio: normal
steg: flodesvy-20261006: kontroller/rokprov/revision/prov_flode.py
andrad: 2026-10-08T14:09Z
---
# Flödesvyn: fixtur för blindningen efter en stoppad start över förslag som ingen valt i

**Varför:** Mutationen M3-5 överlever: en regression som häver blindningen där fångas inte. Koden håller blindningen.

**Förslag:** En fixtur med stoppad start och kandidater utan val, jämförd med och utan dolda fält.

**Klart när:** M3-5 blir röd. Görs efter ägarens sammanslagning av flodesvy-20261006.

**Ersatt (2026-10-08):** Backlogavstämningen 2026-10-08: sammanförd i B-20261007-flodesvyn-fixtur-for-att-en-vanlig-korning-i-ste (två fixturer i prov_flode.py (M3-2, M3-5))
