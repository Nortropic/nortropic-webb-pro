---
id: B-20261002-granskarens-blinda-flackar-rost-i-enskilda-menin
status: pagar
kalla: kirurg
kallref: kontroller/granskarforsok/ · 2026-10-02
skapad: 2026-10-02
prio: normal
steg: granskaren (steg 5.6)
andrad: 2026-10-02T18:34Z
---
# Granskarens blinda fläckar: röst i enskilda meningar, första vyn på mobil, daterat innehåll, generiska listmönster

**Varför:** Granskarförsöket 2026-10-02 (36 granskningar, fyra armar) fann aldrig sju av ägarens 22 omdömesfel, oavsett text och antal granskare: L1-6 och L2-9 (meningar som låter skrivna, inte som verksamheten), L3-8 (kryptisk rubrik), L1-2 (inget foto i första vyn på mobil), L1-5 (/om/ med h1 långt ned i desktop), L1-11 (platsannons som blir inaktuell efter ett datum), L2-2 (omdömeslista med hårlinjer som generiskt mönster). Två granskare hjälper inte här: felen är systematiska, inte slumpmässiga.

**Förslag:** kritik/GRANSKARE.md, kriterium 5 och steg 3: (1) citera de två meningar på sajten som minst låter som verksamheten och de två rubriker som en besökare minst förstår, ordagrant, och döm dem; (2) läs stilrapportens avsnitt om mobilens första vy (sidhuvud, foto i första skärmen) och första skärmen på varje undersida i 1440; (3) leta datum och tidsbundna uppgifter (annonser, erbjudanden, säsong) som blir inaktuella; (4) listor och tabeller i två spalter eller med hårlinjer som skulle passa vilken firma som helst räknas som mallform. Pröva med kontroller/granskarforsok/ (arm A mot arm med texten, samma facit) innan texten införs.

**Klart när:** Granskarförsöket med den nya texten visar fler träffar på minst tre av de sju felen utan fler falska blockerande; då står texten i GRANSKARE.md

## Protokoll 2026-10-02

**Metod.** Samma uppsättning som i B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran, men nya kopior från main
b6f1889 (stilrapportens avsnitt om mobilens första vy och standardens nya kontroller med i båda armarna) och utan
försöket självt i kopiorna. Arm A: dagens kritik/GRANSKARE.md, tre granskningar per bygge. Arm blind: samma text med de
fyra tilläggen i förslaget, tre per bygge. En granskare per session, Opus 5.5 (1M), high. Sonnet 5 dömde blint två
gånger per granskning; bara eniga matchningar räknas. 18 granskningar och 36 domar, inga fel. L1-4 räknas nu som
maskinellt fångat (standarden 9.4).

| Arm | n | Omdömesfel funna, snitt per bygge (av 7,0) | Alla fel (av 13,3) | Omdömesfel som blockerande | Falska blockerande | Blockerande per omgång | Verkliga fynd utanför facit | Tokens | Tid |
|---|---|---|---|---|---|---|---|---|---|
| A, dagens text | 9 | 3,6 | 9,7 | 2,9 | 0 | 4,3 | 7,7 | 3,9 M | 475 s |
| blind, ny text | 9 | 3,9 | 9,9 | 2,7 | 0 | 4,4 | 8,9 | 3,6 M | 467 s |

De sju blinda fläckarna (A mot blind, av 3): L1-11 inaktuell platsannons 0 → 3; L3-8 kryptisk rubrik 0 → 2; L1-5 /om/
med h1 långt ned 0 → 1; L1-2, L1-6, L2-2, L2-9 0 → 0. Dessutom L3-1 (generisk tjänstelista) 0 → 2. Några andra fel föll
med en körning (L1-8, L1-9, L2-4, L2-8, L2-14, L3-5, L3-11), vilket ligger inom bruset vid tre körningar per arm.
L2-4 (kal första vy på mobil) fann dagens text nu i 3 av 3 mot 0 av 3 i förra försöket: stilrapportens nya avsnitt om
mobilens första vy gjorde det. Rösten i enskilda meningar (L1-6, L2-9) och omdömeslistan med hårlinjer (L2-2) hittar
ingen arm ännu. Förbehåll: texten skrevs ur samma byggens fel; om den hjälper på nya byggen visar nästa dom.

**Beslut:** kriteriet håller (fler träffar på tre av de sju, inga falska blockerande). Tilläggen står i
kritik/GRANSKARE.md: stilrapportens mobilavsnitt och första skärmen på undersidorna (steg 3), listor och tabeller som
mallform (originalitet), inaktuellt innehåll (funktion), och de två minst verksamhetstrogna meningarna och de två
minst begripliga rubrikerna citerade och dömda (text).
