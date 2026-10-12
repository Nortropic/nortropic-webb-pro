# Designstudion

Designstudion i portalen (ägarens uppdrag 2026-10-11 med byggpaketet `Nortropic-Designstudio-byggpaket-v1`, ordagrant i
`BESLUT.md`): riktningarna, den levande förhandsvisningen och återkopplingen på ett ställe, med källbunden visuell
redigering och strukturella ändringar genom AI-vägen. Studion bygger på skapandeflödet (`kunskap/skapandeflodet.md`):
Astro, riktningarna (tre sedan ägarens beslut 2026-10-12, förr omkring tio), portalen och leveransvägen består. Claude Design och Lovable var förebilder, inga
tjänster. Den gamla mörka arbetsytan finns inte längre som egen vy (ägarens besked samma dag); portalen är den enda
ramen, och varje funktion därifrån finns i portalen och studion (`kunskap/arbetsyta.md`).

Adressen är `#/studio/<slug>` (`#/arbetsyta/<slug>` leder dit). Vyn har riktningarna, duken med förhandsvisningen och
lägena Visa, Markera, Kommentera och Redigera, och flikarna Ändra, Samtal och Arbete (`dashboard/studio.js`).

## Tidiga bedömbara förslag (DS2)

En kandidat är **bedömbar** så snart dess första fotografering klarat bedömbarheten (`forhandsvisa.ej_bedombar`: ingen
felsida, ingen tom sida, en h1, inga brutna bilder i första vyn; `inspektera.mjs` mäter det i sidan), också medan
granskningen, svaret och de andra kandidaterna arbetar (`kandidater.fotografera(..., tidig=…)`, status `bedombar`).
Versionens bilder bevaras, så att det Johnny bedömer står kvar när kandidaten fortsätter, och skaparens kompetenskvitto
för versionen sparas samtidigt. En körning som stoppas eller dör behåller en bedömbar kandidat med markeringen
`bedombar_avbruten`. Vid återupptagningen (`kandidater.ta_upp_bedombar`) står skaparens version som klar, prövad mot
det kvittot som en sparad skiss; granskningen och försöket görs inte om. Markeringar som typsnitt som inte laddats
eller en tom main visas men stoppar inte.

## Källbunden visuell redigering (DS3)

Fem områden: typografi, bildregi, mellanrum, komposition och färg/yta, plus text (`kontroller/studio.py`). En kontroll
finns bara där källan är bevisad:

- **Källkartan:** kandidatens förhandsbygge för studion sätter ett element-id (`data-nwp-k`) och ett regel-id
  (`--nwp-r`) ur källan (`kontroller/studio/karta.mjs`, `bygg.mjs`); `tolka.mjs` räknar fram samma id:n ur källan igen.
  Helbygget och exporten bygger som förut (`npm run build`), utan markörerna.
- **Sonden:** motorns egen webbläsare med sidans JavaScript avstängt avgör vilken deklaration som äger ett värde (den
  vars provvärde slår igenom i det beräknade värdet) och dess källregel (`studio/sond.mjs`). Sidans egen markering bär
  bara ett id, aldrig en fil eller ett kommando.
- **Två hastigheter:** ett värde provas direkt i förhandsvisningen (en tillfällig regel i bryggan, ingen modell, inget
  bygge, märkt Osparat); ett sparande blir en begäran (`studio.begar`) med små patchar och de förväntade bytes de
  ersätter, och arbetaren (`studio.kor`) prövar allt igen, skriver, bygger, fotograferar och kontrollerar med sonden
  (det förväntade värdet, inget nytt spill i 390, en mellanbredd och 1280, inget ändrat utanför räckvidden). Annars
  läggs originalet tillbaka när filen fortfarande är den som skrevs.
- Det som inte är bevisat (en regel utan källa, ett uttryck, en kortform, en tvetydig sektion) ändras aldrig direkt:
  kartan säger varför och erbjuder AI-vägen, ett uppdrag i Samtal. Strukturella ändringar går alltid den vägen.

Den nya koden blir kandidatens nästa version, bevarad som varje annan; det är den som godkänns, installeras i helbygget
och exporteras.

## Samverkan medan körningen arbetar (DS4)

Varje kandidat har ett eget skrivlås (`kandidater.skrivlas`, `.skrivare.las` i kandidatens katalog). Körningens pool,
studions arbetare, direktredigeringen och en omfotografering tar det, så en ändring i en kandidat väntar aldrig på
hela körningen. En redigering kräver att kandidaten står vid en säker gräns (bedömbar eller senare, `VISBARA`), och
flödesstarten släpper `studio` och `redigera` utan att ateljén är ledig (`flodesstart.krav`). Återkopplingen är
kandidatspecifik: kommentarer har elementankare (`desktop.kommentar`), och blindningen gäller som förut.

## Bevarad design genom helbygget (DS5)

Exporten skannar att studions markörer (`data-nwp-k`, `--nwp-r`) aldrig når den byggda sajten
(`exportera.studions_spar`, i verifieringen av bygget). Installationen av godkänd kod (`installera_godkand`) tar
kandidatens bevarade version; mallsidorna är som förut. Vinnarjämförelsen i helbygget (`prova.vinnarjamforelse`) jämför
mot samma version.

## Proven

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_designstudio.py` | källkartan, sonden, de fem områdena med patchar och återställning, negativa fall, bedömbar tidigt, avbrott med bevarad bedömbar, skrivlåset per kandidat, ändring vid gränsen medan körningen arbetar, exportskanningen | i rökprovet (`studio_fixtur.py`, syntetisk kund) |
| `…/prov_arbetsyta_webb.mjs`, `prov_flodeshandling_webb.mjs` | studion och flödeshandlingarna i portalen i Chromium | i rökprovet |

## Begränsningar

- Ett mänskligt användbarhetsprov med Johnny och en jämförelse mot målbildens paneler med riktiga kunder återstår.
- Studions direkta kontroller gäller den representativa Astro-koden i mallen; ett okänt mönster får AI-vägen.
