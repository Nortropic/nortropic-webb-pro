---
id: B-20261009-slutpostens-skisser-granskade-raknar-inte-kritik
status: vilande
kalla: bygge
kallref: RAPPORT-2026-10-09-formagoprov-kvalitetsprov
skapad: 2026-10-09
prio: normal
steg: kontroller/ateljeslut.py (tillstanden)
---
# Slutpostens 'skisser granskade' räknar inte kritik av en tidigare version

**Varför:** Kvalitetsprovet 2026-10-09: skisskritiken bedömde båda armarnas första version, skaparna ändrade sedan skissen, och slutposten sade '0 av 2 skisser granskade'. Rätt enligt regeln, men missvisande.

**Förslag:** Säg 'kritik gjord av en tidigare version (n), ingen av den aktuella' i stället för 0.

**Klart när:** Slutposten skiljer en kritik av en tidigare version från ingen kritik.
