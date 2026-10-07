---
id: B-20261007-blindningen-listan-i-kundens-underlag-galler-ock
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r107.md
fynd: GR-20261007-r107#K2
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kandidater.py (blind_nekas)
---
# Blindningen: listan i kundens underlag gäller också filer som uppstår efter starten

**Varför:** Listan i underlag/<slug> bygger på en uppräkning vid starten och på mönster. UPPTAGNA-VAL.md nekas bara om den finns vid starten. Det är en teoretisk lucka; inget skrivs dit under en skisskritik i dag utöver det mönstren täcker.

**Förslag:** Neka allt i underlag/<slug> utom listan med ett mönster som gäller också senare filer, om behörigheterna tillåter det.

**Klart när:** En fil som skapas i underlag/<slug> under kritikens session går inte att läsa.
