---
id: B-20261009-forbrukning-mot-kvot-listpris-och-tokens-mats-kv
status: vilande
kalla: bevakning
kallref: ägarbeslutet 2026-10-09 ~14:25Z, punkt 3 och 4; bevakningsfrågan forbrukning-och-vantan
skapad: 2026-10-09
prio: normal
steg: drift, bevakningen
---
# Förbrukning mot kvot: listpris och tokens mäts, kvoten exponeras inte

**Varför:** Bevakningens inventering 2026-10-09: listpris (total_cost_usd, costBasis list) och tokens finns i sessionernas svarsfiler och i Codex utdata, men abonnemangens kvot (Claude och ChatGPT) exponeras inte maskinläsbart; veckobeskedet om förbrukning i kunskap/drift.md har inget verktyg. Ett uppmätt anrop (till exempel Codex 59 720 tokens 2026-10-09) är ingen fast kostnad per fråga och ingen kvotmätning.

**Förslag:** Bevakningens kontroll forbrukning redovisar veckovis uppmätt listpris, tokens, turer och tid per modell och Codex-granskningarnas tokens, och anger kvoten som saknat mätvärde; när en leverantör exponerar kvoten maskinläsbart kopplas den in.

**Klart när:** Bevakningens veckorapport om förbrukning körs i drift; kvoten mäts eller står uttryckligen som omätbar med skäl; drift.md beskriver det som finns.
