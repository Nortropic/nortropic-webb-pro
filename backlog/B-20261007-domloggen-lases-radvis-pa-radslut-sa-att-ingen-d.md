---
id: B-20261007-domloggen-lases-radvis-pa-radslut-sa-att-ingen-d
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-A
skapad: 2026-10-07
prio: hog
steg: gren C1: kontroller/skapande.py, .claude/hooks/stoppvakt.py, kontroller/atelje.py
commit: a108560de54c571e182e585e4a24f93cf950d14f
andrad: 2026-10-08T13:39Z
---
# Domloggen läses radvis på radslut, så att ingen dom med U+2028 försvinner tyst

**Varför:** skapande.domar och stoppvaktens agarens_senare_dom läser domloggen med splitlines(), som också delar på U+2028 och U+2029. En dom vars text innehåller tecknet, till exempel inklistrad, blir två rader som inte går att läsa och hoppas över tyst, så ägarens senaste beslut kan försvinna. r100:s rättelse av KAN-4 ärver det, och kvittots radnummer blir fel efter tecknet. Kontrollerat 2026-10-07: de riktiga domloggarna har inga sådana tecken, så ingen dom har gått förlorad.

**Förslag:** Läs JSONL-filerna radvis på \n överallt där domloggen läses, och låt en oläsbar rad synas med antal och plats (uppgift 5 i gren C1).

**Klart när:** En dom med U+2028 i texten räknas av skapande, stoppvakten och atelje, och kvittots radnummer stämmer.

**Pagar (2026-10-07):** gren C1 (grenen ateljeslut-20261007): domloggen och de andra JSONL-filerna läses på radslut, en oläsbar rad syns med plats och skäl, och kvittots radnummer stämmer (prov_ateljeslut.py); klar med commit vid sammanslagningen
