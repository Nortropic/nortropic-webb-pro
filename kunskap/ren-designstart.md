# Den rena designstarten 2026-10-09

Ägarens uppdrag 2026-10-09 ~17:53Z, punkt 3 (ordagrant i minnet, sammanfattat i `BESLUT.md`, tillägget samma dag):
gamla misslyckade byggen, prototyper och bedömningar ska sluta påverka den nya processen. Den här filen säger vad som
togs ur den aktiva miljön och varför, vad som bevarades, var återställningsarkivet ligger och hur vakten prövar att inget
kommer tillbaka. Det som ersattes i texterna står också i `kunskap/rensning-nortropic-2.md` (den förra rensningen,
2026-10-05) och i `BESLUT.md`.

## Brytpunkten

Brytpunkten är tiden då arkiveringen kördes, och den står i det privata registret
`underlag/rensning/REN-DESIGNSTART-20261009.json` med repots commit. Allt designmaterial som skapats före brytpunkten är
gammalt; allt efter den (nya körningar, nya domar, nya bevis och detta uppdrags resultat) bevaras och används. Taggen
`fore-ren-designstart-20261009` pekar på main före rensningens commits.

## Vad som togs ur den aktiva miljön

Verktyget är `kontroller/ren_designstart.py`. Klassningen står i dess regler, en rad per slag med skälet, och ingen
katalog tas bort på sitt namn ensamt: varje kunds katalog klassas post för post.

| Slag | Exempel |
|---|---|
| Prototyper och kandidater | `underlag/<slug>/atelje/` (planer, uppdrag, kandidater, skisskritik, vinnare, metodkopior, urval), `kunder/<slug>/kandidater/` och körningarnas slutposter |
| Genererade sidor och förhandsvisningar | `kunder/<slug>/sajt/` (görs om ur mallen), Figma-provens sajter, flödets tempkataloger med gamla kandidatbyggen |
| Skärmbilder, designjämförelser och experiment | Figma-piloten och Figma-provet, A/B-skissförsöken |
| Designomdömen | domloggarna `DESIGNDOMAR.jsonl`, arbetsytans meddelanden om de gamla kandidaterna, ägarens domar över tidigare byggen (`underlag/LARDOMAR-original.md`, de gamla posterna i `LARDOMAR.md`) |
| Kalibreringsankare och visuella lärdomar | `underlag/kalibrering/` (ankarna, domarna, försöken) och `kunskap/visuell-niva.md` (ribban ur ankarna) |
| Gamla riktningar och referenslås | `RIKTNINGSHISTORIK.json`, `underlag/<slug>/referenser/` (referenspaket, stilpaket, tjänsternas svar), referens- och tjänsteuppdragen |
| Härledda regler | designreglernas hypoteser ur gamla byggen (brödsmulor, upptagna val, tummen), skillkrockarnas avgöranden som vilade på gamla domar eller nivåfilen, minimiantalet tre varv |

Gamla externa referenser återanvänds bara efter ett nytt uttryckligt urval för ett aktuellt uppdrag, och gamla
kommentarer om hur de ska tillämpas följer inte med.

## Vad som bevarades

- Kundens verifierade fakta och ord: `VERKSAMHET.json`, `UPPDRAG.md`, `KUNDSTART.json`, `RESEARCH.md`, `BRIEF.md` (dess
  §7 beskriver förutsättningar, ingen vald riktning), `TEXTUNDERLAG.md`, `BESTALLNING.md`, diagnosen av kundens nuvarande
  sajt och fraslistan.
- Originalmaterial och rättigheter: `bilder/` med `BILDER.md`, `kalla/`, materialregistret.
- Säkerhetsskydd: start- och processlåsen (tas aldrig bort), byggets och kundrepots lås, kundrepot och dess identitet.
- Tekniska regressionstester och deras data: rökprovets fixtur, förmågeprovet, startkontrollen och underhållet.
- Rapporterna och granskningarna under `underlag/rapporter/` och `underlag/granskningar/`: historik, oförändrad, som
  flödets sessioner nekas att läsa (atelje.NEKAS, granskarna, helbygget och sandlådan).
- Git-historiken och äldre ägarbeslut i `BESLUT.md`, oförändrade. Ersatta designinstruktioner är märkta som historiska.

## Återställningsarkivet

`~/Arkiv/nortropic-ren-designstart-20261009/` (privat, mode 700, utanför repot och utanför flödets läs- och sökrötter:
dontAsk nekar allt utanför arbetskatalogen som inte tillåts uttryckligen, och atelje.NEKAS, granskarna, helbygget och
sandlådans `denyRead` nekar det dessutom). Där finns `MANIFEST.json` (varje post med kategori, skäl, storlek och antal
filer), `SHA256SUMS` (varje fils sha256) och `LASMIG.md`. Arkiveringen flyttade varje post inom samma volym och prövade
att varje fil hade samma sha256 före och efter; en post som inte stämde flyttades tillbaka. Återställ en post med
`.venv/bin/python kontroller/ren_designstart.py --aterstall <sökväg>`.

Licenserna: källgenomgången 2026-10-09 fann att Mobbins villkor (§3.2) kräver skriftligt medgivande för cache och arkiv,
och bland referenspaketen finns skärmar ur Mobbin. Ägaren har skriftliga godkännanden från Mobbin och 21st och fulla
godkännanden för alla verktyg, MCP:er, skills och källor (`BESLUT.md`, ägarens besked 2026-10-09 ~21Z), så skärmarna
ligger kvar i arkivet.

## Vakten

`kontroller/ren_designstart.py --prova` (startkontrollen kör den före varje start, raden "gammalt designmaterial i den
aktiva miljön"): en arkiverad post som finns igen räknas när den skapats före brytpunkten eller innehåller en fil med
samma sha256 som en arkiverad fil (utom mallens egna filer och node_modules); dessutom länkar in i arkivet, ett arkiv
inne i repot och en spårad fil i sin gamla version. `kontroller/styrning.py` fäller de ersatta reglerna i agenternas
texter (minimiantalet varv, nivåfilen, ett val som startar fördjupningen).

## Kalibreringen efter brytpunkten

Granskaren är okalibrerad, och det står i varje uppdrag och varje dom (`granska.kalibreringsstatus`). Gamla
kalibreringsresultat presenteras aldrig som verifiering av den nya metoden. En ny kalibrering kräver att ägaren dömer
nya externa exempel blint (dashboardens Kalibrering), att ankarna delas ut och att en ny nivåfil byggs ur dem;
`kontroller/granskarforsok/kalibrering.py` vägrar att köra utan nivåfilen. Kvalitetskraven består
(`kunskap/designregler.md`, Gemensamma kvalitetskrav).

## Sessionerna

Nya designsessioner startar alltid med ren kontext: flödet återupptar aldrig en session (`claude -p` per pass), och de
gamla sessionernas register låg i de arkiverade ateljéerna, så ingen följdfråga eller återupptagning kan nå dem.
Automatiskt minne är avstängt i nästlade sessioner (`kontroller/nastlad.py`).
