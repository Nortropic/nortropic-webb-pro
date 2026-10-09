---
id: B-20261004-jamforbara-byggen-pa-varierade-kundfall-och-autonomins-matt
status: vilande
kalla: bevakning
kallref: Codex helhetsbedömning 2026-10-04 punkt 8 (byggförmågan), 9; rekommenderad ordning 5
skapad: 2026-10-04
prio: mellan
andrad: 2026-10-09T08:16Z
---
# Jämförbara byggen på varierade kundfall, och autonomins mått: acceptans utan omdesign, total kostnad, ägarens minuter, variation, bevarade kandidater

**Varför:** Flera omtag av samma snickarfirma kan inte belägga bredden; byggförmågan behöver varierade kundfall (innehållsmängd, bildkvalitet, kontaktvägar, designbehov) och både genomsnitt och hur ofta ett bygge blir tydligt dåligt. A/B-sammanställningen (ab.py:65) visar tid, turer och betyg men inte hela kostnaden för ett resultat ägaren faktiskt accepterar. Anthropic rapporterar att mellanversioner ibland var bättre än slutversionen; mer iteration är en hypotes som måste kontrolleras. Regressionsprov (rökprovet) och förmågeprov (kan systemet lösa en svår kunduppgift) ska hållas isär.

**Förslag:** Tre till fem fiktiva eller verkliga kundfall med olika förutsättningar som fast förmågeprov (kunskap/formageprov.md: fallen, färdigkriteriet, kostnadsramen). Kvittot per bygge får: accepterat utan mänsklig omdesign (ägarens dom), total körtid och kostnad inklusive underagenter och omtag, ägarens nedlagda minuter (ägaren anger), återkommande fel, och om iterationen förbättrade eller försämrade den bästa tidigare kandidaten (bevarade kandidater per omgång: dist-hash och granskning, aldrig bara sista). ab.py sammanställer dessa mått per arm.

**Klart när:** Tre till fem namngivna fall med färdigkriterium och kostnadsram i kunskap/autonomi.md; bästa kandidatens filer bevaras (inte bara hash); förmågeprovet med två körningar per fall är dömt blint av ägaren, och autonomi.py sammanställer.

**Vilande (2026-10-04):** väntar på bygge: måtten är klara (kontroller/autonomi.py, kunskap/autonomi.md, ägarens minuter i dashboarden); förmågeprovet körs när designprovet dömts och granskaren prövats på K14–K19

**Vilande (2026-10-05):** Avstämt 2026-10-05: måtten levererade (autonomi.py, autonomi.md, ägarens minuter i dashboarden); fallen är inte namngivna och kandidater bevaras bara som hash och dom. Körs efter K14–K19-försöket och ett godkänt skapandeflöde. Färdigkriteriet omskrivet i avstämningen; tidigare: "Förmågeprovet har körts på de varierade fallen med samma metod; sammanställningen visar acceptansandel, kostnad och variation per fall; de bästa kandidaterna är bevarade och jämförbara."

**Vilande (2026-10-09):** 2026-10-09: kvalitetsprovet förberett (kunskap/autonomi.md, Kvalitetsprovet; 6ef1de6, b7104e9): ett sammanhängande fall med H01 som första metodvariabel i det befintliga metodförsöket (ab.py forbered-skiss --variabel metodvariant). Inte kört: verkliga sessioner och helbygget kräver ägarens mandat. Ett fall är första belägget; varierade fall är denna posts uppgift.
