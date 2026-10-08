---
id: B-20261007-kundvakten-namn-i-rubriker-och-forst-i-en-mening
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r104.md
fynd: GR-20261007-r104#B2
skapad: 2026-10-07
prio: hog
steg: main: kontroller/kundvakt.py, kontroller/rokprov/revision/prov_startkvitto.py
commit: a108560
andrad: 2026-10-08T14:09Z
---
# Kundvakten: namn i rubriker och först i en mening, och orter utan platsverb, stoppas

**Varför:** Ett namn utan kännetecken i en rubrik släpps, till exempel "## Möt …" eller "## Om …", liksom ett namn först i en mening utan personord och en ort utan platsverb. Felen går åt det osäkra hållet.

**Förslag:** Gör "möt", "träffa" och "om" till personord. Räkna par i rubriker under Om oss, Team och Omdömen som säkra namn. Räkna orter efter "i" eller "på" i en adressmening. Väg falsklarmen mot generiska frågor.

**Klart när:** Granskarens angrepp med rubriker, meningsbörjan och orter stoppas, och de 41 generiska frågorna släpps fortfarande.

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: a108560 (6d440de: r104#B2); prov_startkvitto 10e
