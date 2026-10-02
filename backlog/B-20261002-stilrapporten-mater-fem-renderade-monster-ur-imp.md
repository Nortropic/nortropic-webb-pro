---
id: B-20261002-stilrapporten-mater-fem-renderade-monster-ur-imp
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · pbakaus/impeccable
skapad: 2026-10-02
prio: normal
steg: 6 (provets stilrapport) och 5.1 (upptagna val)
---
# Stilrapporten mäter fem renderade mönster ur impeccables detektorregister (rubrikrytm, enformig luft, platt typskala, färgad sidkant, liten brödtext) och upptagna-valen namnger modellernas standardtypsnitt

**Varför:** Ta in, avgränsat: impeccables detektor har 61 regler med trösklar i kod (crates/foundation/src/registry.rs), och fem av dem som vår stil.mjs saknar går att läsa ur den renderade sidan och träffar luft och hierarki, den dimension ägaren satte Okej på i alla tre domarna (LARDOMAR.md L1–L3). Källan namnger också typsnitt som modellerna faller tillbaka på (17 i constants.rs rad 85–105, 16 i reference/new-work.md rad 67), medan vår UPPTAGNA-VAL.md bara beskriver standardval utan typsnittsnamn.

**Förslag:** kontroller/stil.mjs, i matPaSidan() och varningarna (info, aldrig grind), trösklarna skrivna med egna ord och källan i filhuvudet som för gstack: (1) rubrikrytm: för h2 och h3 i main, luften ovanför rubriken (avstånd från föregående blocks nederkant) mindre än luften under (till eget innehåll) med minst 12 px, varning när minst två rubriker på sidan bryter; (2) enformig luft: vertikala margin, padding och gap på main-block avrundade till 4 px, varning när ett värde står för över 60 procent av minst tio mätningar och högst tre unika värden finns; (3) platt typskala: storlekarna för h1–h3, p och li sorterade, varning när största steget mellan två grannar är under 1,25; (4) färgad sidkant: kant på en sida av ett element, minst 2 px med radie eller 3 px utan, minst dubbelt mot övriga sidor och inte neutral färg (klassiska citat- och kortlister); (5) liten brödtext: p, li eller dd under 12 px. Radlängd 45–75 och radhöjd 1,4 behålls som de är. kontroller/upptagna_val.py MODELLENS_STANDARDVAL (rad 26–37): en rad 'typsnitt modellerna faller tillbaka på' med namnen Inter, Roboto, Open Sans, Lato, Montserrat, Arial, Helvetica, Fraunces, Instrument Sans, Instrument Serif, Geist, Mona Sans, Plus Jakarta Sans, Space Grotesk, Recoleta, Playfair Display, Cormorant, Lora, Crimson, Newsreader, Syne, Space Mono, IBM Plex, DM Sans, DM Serif, Outfit. Ingen kod kopieras.

**Klart när:** STIL.md varnar för de fem mönstren på en provsida som har dem och är tyst på mallens tomma sajt; UPPTAGNA-VAL.md visar typsnittsraden; kontroller/rokprov.sh grönt.
