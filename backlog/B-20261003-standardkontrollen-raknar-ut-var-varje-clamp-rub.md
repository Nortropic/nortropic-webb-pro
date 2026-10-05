---
id: B-20261003-standardkontrollen-raknar-ut-var-varje-clamp-rub
status: ersatt
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-04 · Kevin Powell, Fixing fluid typography + Ana Tudor
skapad: 2026-10-03
prio: normal
steg: steg 6, kontroller/standard_kontroll.py (3.2)
andrad: 2026-10-05T06:55Z
---
# Standardkontrollen räknar ut var varje clamp()-rubrik når sitt max och jämför med omslagets maxbredd

**Varför:** Egen innovation ur Kevin Powells video: glappet mellan rubrikens maxpunkt och omslagets maxbredd går att räkna ut ur CSS:en (Holms 1 375 mot 1 152 px) men ingen kontroll gör det, och provets vyer 390/768/1440 ligger utanför zonen. Gäller både vw-byggen (zonen finns) och cqi-byggen (ett max över omslagets bredd nås aldrig).

**Förslag:** kontroller/standard_kontroll.py efter rad 393: för varje font-size: clamp(min, a rem + b vw|cqi, max) lös brytbredden (max − a) / b i px med 16 px per rem, läs omslagets bredd ur den största max-width eller width: min(…, N rem) i CSS:en, och ge information 3.2 när brytbredden skiljer sig mer än 5 % från omslaget, med båda talen i texten. Rökprovet får ett fall med h1 vars max nås 200 px efter omslaget.

**Klart när:** Rökprovets fall ger informationen med båda talen; Holms CSS ger den (1 375 mot 1 152); Luleå-Snickarens (1 150 mot 1 152) ger ingen; kontroller/rokprov.sh grönt.

**Ersatt (2026-10-05):** Sammanförd i B-20261003-flytande-typografi-mater-mot-omslaget-cqi-i-en-s som dess kontrollsteg (avstämningen 2026-10-05); verifieringsexemplen ligger i försöksarkivet ~/Arkiv/nortropic-webb-pro-forsok-20261005/.
