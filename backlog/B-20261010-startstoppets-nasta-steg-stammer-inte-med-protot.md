---
id: B-20261010-startstoppets-nasta-steg-stammer-inte-med-protot
status: vilande
kalla: granskning
kallref: GR-20261010-kompetens-integration
fynd: GR-20261010-kompetens-integration#F8
skapad: 2026-10-10
prio: normal
steg: startkontrollen, prototyp.py
---
# Startstoppets nästa steg stämmer inte med prototyp.py efter en fallen körning

**Varför:** När startkontrollen stoppade kandidatkörningen 2026-10-10 sa beskedet och slutposten: starta igen med prototyp.py <slug>. prototyp.py utan flagga vägrade sedan (förra körningen föll) och anvisade --fortsatt eller --om. Ägaren får två olika besked om samma läge. Samma dag, efter att kontraktet underkänt en sparad research, föreslog beskedet först --fortsatt, som tar vid efter researchen och stoppar på samma underkända research igen, och först därefter --om.

**Förslag:** Startstoppets nästa steg ska nämna flaggan som prototyp.py kräver efter ett startstopp (--fortsatt), eller så ska prototyp.py behandla ett startstopp utan utfört arbete som en ny start. Efter en underkänd sparad research ska --om stå först. Prov på texterna.

**Klart när:** Beskedet efter ett startstopp och prototyp.py:s läge anger samma kommando, med ett prov i prov_ateljeslut eller prov_startkontroll.
