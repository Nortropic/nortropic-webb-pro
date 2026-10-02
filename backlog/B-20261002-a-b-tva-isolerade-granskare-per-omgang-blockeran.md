---
id: B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · affaan-m/ECC
skapad: 2026-10-02
prio: normal
steg: steg 5.6 (oberoende granskning), kontroller/granska.py
commit: c49119f
andrad: 2026-10-02T18:21Z
---
# A/B: två isolerade granskare per omgång (blockerande fynd från någon av dem gäller) mot en granskare

**Varför:** Prova A/B: ECC:s santa-method låter två granskare med samma kriterier döma var för sig och räknar ett fynd som verkligt om en av dem hittar det. Litteraturen i teoretisk-grund.md:128-129 säger samma sak (en granskare hittar omkring 35 procent, tre till fem omkring 75), men granska.py kör en huvudgranskare per omgång, och ägaren hittade efter godkännandet konkreta fel i alla tre byggena (LARDOMAR.md:38, 63, 87).

**Förslag:** Ingen ändring i flödet förrän A/B:t avgjort. Provet: de tre dömda byggenas sista version (samma dist, samma underlag). Arm A: en granskare, tre körningar per bygge. Arm B: två isolerade granskare per körning, unionen av blockerande fynd, tre körningar per bygge. Facit: felen ägaren pekade ut i L1-L3 (LARDOMAR.md:32, 38, 57, 63, 81, 87). En domare av annan modell än granskaren (Sonnet), som inte vet armen, matchar varje fynd mot facit och märker resten verkligt eller falskt; ordningen på armarna byts mellan bedömningarna och oenighet räknas som ej träff. Mät träffar mot facit, falska blockerande fynd, granskarnas överensstämmelse i arm B, tokens och tid. Vinner B tydligt: granska.py kör två sessioner parallellt i varje omgång, godkänt kräver båda, och kritik/GRANSKARE.md rad 3-7 får en mening om det.

**Klart när:** Ett protokoll i backlogposten med tabellen per arm (träffar, falska blockerande, överensstämmelse, tokens, tid) och beslutet; vid B: granska.py kör två granskare per omgång och kontroller/rokprov.sh är grönt.

## Protokoll 2026-10-02

**Metod.** De tre dömda byggena (lulea-snickaren, paint-it-black-maleri, sundboms-el), var och en i en isolerad
repokopia vid main: LARDOMAR.md utan byggets eget domblock, ingen DOM.json, ingen backlog, inget register, läsning nekad
i repona och minnet, och ett färskt snabbprov med dagens kontroller. Granskare: Opus 5.5 (1M), effort high, dagens
uppdrag, originalitetsdomaren av. Arm A: dagens text, sex granskningar per bygge. Arm B: två isolerade granskare med
dagens text, unionen av fynden (A-1+A-4, A-2+A-5, A-3+A-6; som kontroll alla 15 par). Arm persona och arm c: de nya
texterna i steg 5, tre per bygge. Facit: 40 fel ur ägarens domar L1–L3, varav 22 kräver omdöme och 18 fångas redan av
standarden. Domare: Sonnet 5, blind för armen, två bedömningar per granskning med fynden i olika slumpad ordning; en
matchning räknas bara när båda är eniga. 36 granskningar och 72 domar, inga fel. Skripten: `kontroller/granskarforsok/`.

| Arm | n | Omdömesfel funna, snitt per bygge (av 7,3) | Alla fel (av 13,3) | Omdömesfel som blockerande | Falska blockerande | Blockerande per omgång | Verkliga fynd utanför facit | Nivå 0/1/2 | Överensstämmelse | Tokens per omgång | Tid |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A, en granskare | 9 | 3,3 | 8,8 | 2,4 | 0 | 4,2 | 8,2 | 0/9/0 | – | 4,2 M | 506 s |
| B, två granskare | 9 | 4,0 | 10,0 | 3,1 | 0 | 8,3 | 17,3 | 0/9/0 | 0,80 | 7,6 M | 528 s |
| persona | 9 | 3,3 | 9,0 | 2,4 | 0 | 3,6 | 7,7 | 0/8/1 | – | 3,7 M | 480 s |
| c, skärmrutor | 9 | 3,3 | 9,2 | 2,3 | 0 | 3,7 | 8,6 | 0/9/0 | – | 3,9 M | 540 s |

Per bygge, omdömesfel funna (A: alla sex enskilda; B: alla 15 par): lulea-snickaren 2,5 → 3,1; paint-it-black-maleri
3,7 → 4,3; sundboms-el 4,0 → 4,3. B fann oftare L1-12 (en sida per tjänst, 3 av 3 mot 1 av 3) och L2-3 (tapetsidan utan
bild, 3 av 3 mot 1 av 3). En granskning kostar 2,83 USD i listpris (kvot i praktiken), så B kostar en sådan till per
omgång; tiden är densamma eftersom de går parallellt. Inga falska blockerande fynd i någon arm.

Ingen arm hittade i någon körning: L1-2 (inget foto i första vyn på mobil), L1-5 (/om/ med h1 långt ned i desktop),
L1-6 och L2-9 (meningar som låter skrivna), L1-11 (platsannonsen blir inaktuell), L2-2 (omdömeslista med hårlinjer),
L3-8 (kryptisk rubrik). Det blir en egen vilande post.

**Beslut:** B vinner i alla tre byggen och införs: granska.py kör två granskare parallellt i varje omgång
(`NWP_GRANSKARE_ANTAL`, standard 2), domen tar lägsta betyget och varje blockerande fynd, godkänt kräver båda;
kritik/GRANSKARE.md säger det i inledningen.

**Klar (2026-10-02):** B vann i alla tre byggen; två parallella granskare införda; protokollet i posten
