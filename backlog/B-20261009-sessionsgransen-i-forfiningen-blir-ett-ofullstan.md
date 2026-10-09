---
id: B-20261009-sessionsgransen-i-forfiningen-blir-ett-ofullstan
status: vilande
kalla: bygge
kallref: RAPPORT-2026-10-09-formagoprov-kvalitetsprov
skapad: 2026-10-09
prio: normal
steg: kontroller/kandidater.py (forfina_kandidat), kontroller/atelje.py
---
# Sessionsgränsen i förfiningen blir ett ofullständigt resultat, inte ett tekniskt avbrott

**Varför:** Kvalitetsprovet 2026-10-09: förfiningens första försök stoppades av abonnemangets sessionsgräns ("You've hit your session limit"); kedjan återställde den valda versionen och avslutade körningen normalt, så --valda krävde en ny dom för att ta om samma förfining.

**Förslag:** Känn igen sessionsgränsen (is_error med den texten) som ett tekniskt avbrott: körningen står som avbruten och --fortsatt tar om förfiningen från den valda versionen.

**Klart när:** Ett prov med ett sådant svar ger en avbruten körning som --fortsatt tar om, utan ny dom.
