---
id: B-20261003-ateljen-far-svara-ingen-riktning-haller-lagstani
status: vilande
kalla: bevakning
kallref: Codex bedömning av den visuella nivån, 2026-10-03
skapad: 2026-10-03
prio: hog
---
# Ateljén får svara 'ingen riktning håller': lägstanivå före bygge, nya försök med tak

**Varför:** Codex 2026-10-03: panelen räknar ihop rangordningarna och väljer en vinnare; den bästa av tre svaga riktningar blir ändå vinnare och byggtid läggs på den. Rangordning och tillräcklig kvalitet är två beslut.

**Stöd:** Anthropics evalartikel (2026-01-09) råder att ge domaren en utväg när underlaget inte räcker och att döma dimensioner isolerat; "ingen riktning håller" är den utvägen.

**Förslag:** Varje domare svarar utöver rangordningen ja/nej på om den bästa riktningen når den kalibrerade lägstanivån (kunskap/visuell-niva.md). Nej från majoriteten ger en ny divergens med uttryckligt krav på annan komposition, innehållshierarki och bildanvändning (inte bara typsnitt och accent), högst två omgångar. Når ingen ribban redovisas det i VAL.md, RAPPORT.md och som chip i dashboarden; bygget får fortsätta med bästa riktningen för lärandets skull, men leveransen räknas då som visuellt underkänd i måtten (ägarens godkännandegrad, falska AI-godkännanden, kostnad per godkänt bygge), aldrig som ett genomfört bygge (Codex 2026-10-03: annars ökar antalet byggen medan kvaliteten står still). Höj inte tröskeln 7 först: betygen måste betyda rätt sak.

**Klart när:** VAL.json har 'haller' per domare och 'forsok'; ett regressionsfall i rökprovet där alla domare säger nej ger ny omgång och sedan märkt leverans; atelje.py:s panel och bygg-sajt steg 5.1 beskriver de två besluten.
