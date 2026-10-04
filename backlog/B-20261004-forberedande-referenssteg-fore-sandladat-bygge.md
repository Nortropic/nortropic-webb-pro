---
id: B-20261004-forberedande-referenssteg-fore-sandladat-bygge
status: vilande
kalla: bevakning
kallref: Codex R27-uppföljning 2026-10-04; bygge 3 i sandlådat läge (kopia3, 759a547); code.claude.com/docs/en/sandboxing
skapad: 2026-10-04
prio: hog
andrad: 2026-10-04T12:46Z
---
# Förberedande referenssteg före det sandlådade bygget: välj sajterna, tillåt deras resursdomäner, frys bilder och tillstånd

**Varför:** Med sandlådan på (NWP_SANDLADA=pa) når bygget bara domänlistan (verksamhetens domän, NWP_NAT_DOMANER och kontroller/sandlada-domaner.txt). Bygge 3 (2026-10-04) fick fem nekanden i referenssteget: inspektioner av www.lindbacks.se, www.gov.uk och www.dinesen.com, awwwards-sidan därför att assets.awwwards.com inte står i listan, och ett externt Lighthouse. Nekandena är rätt enligt policyn, men referensjakten (kunskap/referensjakt.md) och referensöverföringen (sektion och tillstånd följer med till ateljén och granskaren) blir tunnare än utan sandlåda, och det är just den visuella ribban ägaren sagt är otillräcklig. Claude Codes nätmodell tillåter värdar uttryckligen; jokertecken (*.awwwards.com) löser gallerierna, inte de valda referenssajterna.

**Förslag:** Ett eget steg före byggsessionen, utanför sandlådan men avgränsat som webbtjänsten (sluggen, byggets kataloger, läsande inspektion): (1) jakten väljer de faktiska referenssajterna (gallerierna i referensjakt.md plus ägarens luckor) och skriver REFERENSER.md med roll, sektion och tillstånd; (2) steget inspekterar dem en gång med inspektera.mjs (390/1440, hover/fokus/meny där det är utpekat) och fryser bilderna och de observerade tillstånden under underlag/<slug>/referenser/; (3) resursdomänerna som sajterna behöver (typsnitt, bilder, cdn) tillåts bara under den inspektionen, aldrig för bygget; (4) det sandlådade bygget, ateljén och granskaren läser de frysta bilderna och behöver inte nå sajterna. Gallerierna får jokertecken i sandlada-domaner.txt (*.awwwards.com och motsvarande) för att själva jakten ska fungera. Ordning enligt Codex: först bygge 3:s slutresultat (prov, granskning, stoppkrok och slutkod mot samma slutliga bygge), sedan detta steg, sedan designförbättringarna under samma frysta metod.

**Klart när:** Ett sandlådat bygge visar inga nekanden i referenssteget; REFERENSER.md och de frysta bilderna finns före byggsessionen och är det ateljén och granskaren ser; jokertecknen står i sandlada-domaner.txt med ett rökprovsfall; LARDOMAR.md noterar om referensbilderna gjorde skillnad i ägarens dom.
