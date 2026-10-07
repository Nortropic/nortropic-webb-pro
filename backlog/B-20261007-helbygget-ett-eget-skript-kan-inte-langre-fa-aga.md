---
id: B-20261007-helbygget-ett-eget-skript-kan-inte-langre-fa-aga
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#BÖR-1
skapad: 2026-10-07
prio: hog
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py, .claude/hooks/stoppvakt.py
---
# Helbygget: ett eget skript kan inte längre få ägarens godkännande räknat

**Varför:** Hashlistan kunder/<slug>/prov/.skyddat-fore går att skriva, och egna skript får köras. Granskaren fick "ägaren godkänner: ja" på två sätt: genom att kopiera in en DOM.json och förfalska listan, och genom att ta bort låset med os.chflags, skriva om filen och förfalska listan. Samma förfalskning döljer en ändrad kritik/GRANSKARE.md, så luckan gäller hela skyddet från F10. En process som lever kvar efter sessionen kan också skriva DOM.json efteråt.

**Förslag:** kor.sh håller hashlistans sha256 i minnet, som DOMSHA redan görs, och ger den till korslut. Neka Write och Edit för .skyddat-*. Stoppa byggets processgrupp efter körningen.

**Klart när:** Granskarens två vägar och den kvarlevande processen ger slutkod 3 eller "ej belagd", aldrig "ägaren godkänner: ja", och en verklig ägardom räknas fortfarande.
