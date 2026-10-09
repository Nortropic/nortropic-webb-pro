---
id: B-20261009-kompetenskvittots-bildfalt-flera-sokvagar-eller
status: vilande
kalla: dom
kallref: RAPPORT-2026-10-09-formagoprov-kvalitetsprov
skapad: 2026-10-09
prio: normal
steg: kontroller/kandidater.py (kompetenspass, bild_finns)
---
# Kompetenskvittots bildfält: flera sökvägar eller förklarande text ger en falsk lucka

**Varför:** Kvalitetsprovet 2026-10-09, förfiningen av B/k02: granskningspasset blev genomford false enbart för att två prövade beteenden hade bildfältet 'varv-14/vy-390-fokus.png; varv-14/vy-1440-fokus.png' och 'varv-15/FORHAND.md (Sidled-spill: inget, Konsolfel: inga)'. Filerna finns. Ägarens bedömning pekade ut det; den verkliga luckan (fokustillståndet, kontaktformuläret) var en annan.

**Förslag:** Låt passets schema bära bild som en lista med vägar, eller dela fältet på ; och , och skär bort text efter en giltig väg; skilj i posten ett formfel i fältet från en bild som saknas.

**Klart när:** Ett prov där 'a.png; b.png' och 'x.md (text)' räknas som funna när filerna finns och som saknade när de inte finns; k02:s post ger samma utfall som bilderna.
