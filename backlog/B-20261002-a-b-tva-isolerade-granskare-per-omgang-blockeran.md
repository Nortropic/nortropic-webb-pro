---
id: B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · affaan-m/ECC
skapad: 2026-10-02
prio: normal
steg: steg 5.6 (oberoende granskning), kontroller/granska.py
---
# A/B: två isolerade granskare per omgång (blockerande fynd från någon av dem gäller) mot en granskare

**Varför:** Prova A/B: ECC:s santa-method låter två granskare med samma kriterier döma var för sig och räknar ett fynd som verkligt om en av dem hittar det. Litteraturen i teoretisk-grund.md:128-129 säger samma sak (en granskare hittar omkring 35 procent, tre till fem omkring 75), men granska.py kör en huvudgranskare per omgång, och ägaren hittade efter godkännandet konkreta fel i alla tre byggena (LARDOMAR.md:38, 63, 87).

**Förslag:** Ingen ändring i flödet förrän A/B:t avgjort. Provet: de tre dömda byggenas sista version (samma dist, samma underlag). Arm A: en granskare, tre körningar per bygge. Arm B: två isolerade granskare per körning, unionen av blockerande fynd, tre körningar per bygge. Facit: felen ägaren pekade ut i L1-L3 (LARDOMAR.md:32, 38, 57, 63, 81, 87). En domare av annan modell än granskaren (Sonnet), som inte vet armen, matchar varje fynd mot facit och märker resten verkligt eller falskt; ordningen på armarna byts mellan bedömningarna och oenighet räknas som ej träff. Mät träffar mot facit, falska blockerande fynd, granskarnas överensstämmelse i arm B, tokens och tid. Vinner B tydligt: granska.py kör två sessioner parallellt i varje omgång, godkänt kräver båda, och kritik/GRANSKARE.md rad 3-7 får en mening om det.

**Klart när:** Ett protokoll i backlogposten med tabellen per arm (träffar, falska blockerande, överensstämmelse, tokens, tid) och beslutet; vid B: granska.py kör två granskare per omgång och kontroller/rokprov.sh är grönt.
