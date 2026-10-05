---
id: B-20261003-mellanslagskontrollen-9-4-fangar-inte-en-mening
status: klar
kalla: bygge
kallref: kunder/holms-konditori-abx/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 6
commit: b7bf1c5
andrad: 2026-10-05T10:59Z
---
# Mellanslagskontrollen (9.4) fångar inte en mening som löper ihop med en länk efter radbrytning i Astro

**Varför:** Text som slutar på rad N och en <a> på rad N+1 renderades utan mellanslag (Luleå.info@…, på[numret], ellerskriv); granskaren hittade det, standarden inte.

**Förslag:** kontroller/standard_kontroll.py: pröva synlig text där ett ord eller en punkt direkt följs av länktext utan mellanslag; mall/astro/README.md: skriv {' '} före en länk på ny rad.

**Klart när:** standard_kontroll 9.4 fångar en textnod som slutar med bokstav eller skiljetecken direkt före en länk, och en länk som följs direkt av en bokstav (fall i rökprovet); mallens README har raden om {' '} före en länk på ny rad.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; 9.4 fångar bara punkt följd av versal, inte ord mot länk utan mellanslag. Ingår i paketet före nästa helbygge. Färdigkriteriet tillagt i avstämningen (posten saknade det).

**Klar (2026-10-05):** Klar (paketet före nästa helbygge): 9.4 fångar ord mot länk utan mellanslag i HTML-källan ("på<a", "</a>eller"); hårt mellanslag räknas som mellanslag och span, small, time och data som egen post (flex, rutnät); rökprovet har fallen åt båda hållen, och mallens README säger hur länken skrivs. Prövat mot elva arkiverade och sandlådade byggen: bara det äkta fallet fälls ("2026).Läs dem"). (b7bf1c5)
