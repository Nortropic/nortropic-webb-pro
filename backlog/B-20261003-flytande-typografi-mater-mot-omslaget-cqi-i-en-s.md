---
id: B-20261003-flytande-typografi-mater-mot-omslaget-cqi-i-en-s
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-04 · Kevin Powell, Fixing fluid typography + Ana Tudor
skapad: 2026-10-03
prio: normal
steg: steg 5, byggstandarden 3.2, kontroller/standard_kontroll.py
andrad: 2026-10-05T06:55Z
---
# Flytande typografi mäter mot omslaget (cqi i en storleksbehållare), inte mot fönstret (vw)

**Varför:** Dom ta in: clamp() med vw växer vidare efter att omslaget nått sin maxbredd; Holms h1 når max vid 1 375 px medan omslaget stannar vid 1 152 px, aby 1 250 mot 1 200 px, och provets vyer 390/768/1440 ser aldrig glappet. Kevin Powells lösning är två rader: omslaget blir container inline-size och clamp() använder cqi med rem kvar för zoomen; @property på typskalans steg bara när ett bygge inför container queries på kort.

**Förslag:** kunskap/byggstandard.md rad 47 (3.2): clamp() blandar rem och cqi mot sidans omslag som är en storleksbehållare (container: omslag / inline-size); vw bara utan omslag med maxbredd. Rättelsen rad 145–146: en mening om glappet (Holms 1 152–1 375 px) och en rad om @property (syntax <length>, inherits true, satt om på omslagets direkta barn) när container queries används på kort. kontroller/standard_kontroll.py rad 390–393: godta cqi som flytande del; information när vw används och CSS:en har ett omslag med max-width eller width: min() i rem. Mallens README om den beskriver omslaget.

**Klart när:** byggstandarden 3.2 och rättelsen nämner cqi och behållaren; standard_kontroll flaggar inte clamp(1rem, 0.5rem + 3cqi, 3rem) och ger information för rem + vw med ett omslag i rem; kontroller/rokprov.sh grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord (byggstandard 3.2 säger rem och vw; standard_kontroll prövar bara vw utan rem). Brytbreddsposten (clamp) är sammanförd hit som kontrollsteget i standard_kontroll.py; dess verifieringsexempel ligger i försöksarkivet.
