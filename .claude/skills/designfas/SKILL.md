---
name: designfas
description: Utförarens arbetsinstruktion i Nortropics designfas - tre riktningar som lokala Astro-projekt genom ett produktionsband, där varje skill gör en synlig insats i sin station och varje version visas för ägaren i en privat artefakt. Används när ägaren startar ./design.sh <slug> eller ber om designarbete för en kund i riktningarnas Astro-projekt.
---

# Designfasen — bandet i Astro-projekten

Du är den utsedda utföraren för en kunds riktningar: den enda som skriver deras versioner. Varje riktning är ett riktigt
Astro-projekt i `kunder/<slug>/kandidater/kNN/sajt`, som kandidatflödet förberett efter researchen, planen och
planprövningen (ägarens beslut 2026-10-13 i `BESLUT.md`: formgivningen lokalt i Astro). Ägaren ser och kommenterar varje
version i riktningens privata artefakt. Code gör research, specialistbedömningar och kontroller och lämnar underlag.
Sidan skapas på ett band: varje station har sin fråga och sina skills, och dess insats ska synas på sidan. Läsning är
ingen insats. Bandet: `kunskap/metodkarta.md`, Bandet: stationerna; flödet runt det: `kunskap/skapandeflodet.md`,
Bandet i projekten.

Argumentet är kundens slug. Spåret: `.venv/bin/python kontroller/designfas.py status <slug>` (riktningarna med projekt
och artefakt, versionerna och bandets läge per riktning).

## Din grund (kort)

Läs `underlag/<slug>/KUNDFORSTAELSE.md`, `kunskap/designregler.md`, bandets tabell och varje riktnings uppdrag ur planen
(`underlag/<slug>/atelje/kandidater/kNN/UPPDRAG.md`). Mer läser du inte i förväg: varje station ger dig sina skills när
det är dess tur. Säger två skills emot varandra avgör metodkartans Avgöranden och designreglerna, aldrig vilken skill du
läste sist. Visar `status` inga riktningar, saknas researchen och planen: säg det och be ägaren köra
`.venv/bin/python kontroller/prototyp.py <slug>`; formge inte utan dem.

## En station i taget

För varje riktning går du bandet i tabellens ordning: underlag, innehåll och struktur, art direction, komposition,
detaljer, visuell form, interaktion, utvärdering, iteration (ramen ur processmodellerna, den inre ordningen praxis och vår
hypotes; metodkartan, Avvikelser och hypoteser). Mobilen först: bygg och pröva 390 först, med besökarens toppuppgift och
den primära handlingen i första skärmen. Tillgängligheten är ett krav i varje station från innehållet (rubrikordning,
länktexter, textalternativ) och från art direction (riktiga element, kontrast 4,5:1 och 3:1 för kontroller och fokus,
färg aldrig ensam, fokus som inte döljs, träffytor 24 px och 44 px för primära kontroller, reflow, reducerad rörelse).

1. `designfas.py station <slug> <station> --ritning <kNN>` ger stationens arbetsinstruktion: frågan, skills och
   tjänster bara för stationen, projektet, indata, utdata och kontroll, och riktningens senaste bilder och fynd. Ett
   radutdrag (`väg rad a–b`) läses bara i sina rader.
2. Gör stationen i riktningens projekt. En station som ändrar sidan görs helst av en underagent (Agent-verktyget) som får
   instruktionen, aktiverar stationens skills med Skill (en användaranropad skill läses hel med Read), ändrar bara det
   stationen gäller i det projektet och lämnar en kort redovisning. Du granskar ändringen mot frågan. Riktningens
   underlag, referenslåset, språket och skälen står i projektets `RIKTNING.md`.
3. Spara versionen: `designfas.py version <slug> --station <station> --ritning <kNN> --orsak "<vad stationen ändrade
   och varför>"`. Ett nytt paket: lägg till `--paket namn@version` (exakt version, inga skript, bara npm-registret).
   Versionen byggs, källan och den byggda sidan sparas, startsidan och undersidorna renderas i 390/768/1440 med menyn
   öppen, kontrollerna körs, och insatsen prövas mot förra versionen av riktningen (`insats`). Syns den inte: säg varför
   (stationen fann inget att göra, med skäl) eller gör om. Faller bygget blir det ingen version: rätta och spara igen.
4. Visa versionen för ägaren (se Visningen nedan).
5. En station som inte gäller sidan hoppas över med skälet på nästa version: `--hoppa <station>="<skäl>"`. Stationen
   rörelse gäller alltid: ingen rörelse är beslutet "stilla", med skäl i orsaken. Kritiken och tillgängligheten körs
   alltid och kan inte hoppas över.

**Innehåll och struktur** ger riktningens första version: strukturen med det verkliga innehållet (content first),
och **art** ger den sitt språk. **Detaljer** lyfter riktningen från basic till premium före valet: signaturrörelsen i
första vyn, tillstånd och övergångar på allt interaktivt, 21st-block där ett passande finns (porterat enligt
`kunskap/beroenden.md`, licensen ur komponentsidan), bilder som avtäcks eller lever där det bär, mikrotypografi och en
första polish; RIKTNING.md listar de block som prövades, valdes och valdes bort (id och licens) och beteendena som
lades till och varför. **Kritiken** är ett specialistpass som ser bilderna och briefen före din förklaring:
`designfas.py bestall <slug> --typ kritik --station kritik --version <v> --ritning <kNN> --uppgift "…"` och
`designfas.py specialist <slug> B00N`. Svaret säger om bandet ska gå tillbaka (`atergang`: underlaget, innehåll och
struktur, art direction, komposition eller detaljer); är helheten svag gör du omtaget innan du lägger varven på finputs,
med `bolder` eller `quieter` i kompositionen när kritiken fann sidan platt eller överlastad. **Tillgängligheten** utgår
från renderingens axe, fokus och reflow i versionens BILDER.json och kontroll/. Andra stationer kan också beställas som
pass (typen och stationen i tabellen) när du vill ha en oberoende insats; svaret förs in i en version med
`--bestallning B00N` och bedöms med `designfas.py infor`.

**Tre riktningar** (ägarens beslut 2026-10-12). De skiljer sig i minst två av makrostruktur, bildstrategi, typografisk
hierarki, innehållsordning och ton, aldrig bara i färg och typsnitt, och var och en visar i designen varför den passar
kunden. Varje riktning går underlag, innehåll och struktur, art, komposition och detaljer (ägarens beslut 2026-10-13:
"Ja, före valet"). När alla tre finns körs kritiken och jämförelsen samlat, med riktningarna sida vid sida (`--typ kritik
--station kritik` och `--typ jamforelse --station jamforelse`, med `--ritning '*'`, som ger passet varje riktnings senaste
version); gör inget omtag per riktning innan de andra finns, men pekar jämförelsen ut två som för lika gör du om den
svagare innan ägaren ser dem. Ber ägaren om fler (två åt gången), får de sina projekt med `designfas.py riktningar
<slug> <kNN> <kNN> --nya` (nästa lediga id), du skriver deras uppdrag i RIKTNING.md i underlagsstationen, och de går
samma följd och jämförs med de tidigare. Jämförelsen väljer riktningen i sitt svar (fältet `val`), och ägarens eget
val går före; den valda går resten av bandet: typografi, responsiv, rörelse, formulär, kritik, tillgänglighet och polish.
**Godkännandet** (BESLUT.md, tilläggen 2026-10-13) gäller riktningens senaste version: den autonoma godkännaren
(`designfas.autogodkann`, som bandets drivare anropar) godkänner när den senaste jämförelsen valde riktningen och den
senaste kritiken av just den versionen, ett eget `ds_kritik`-pass med sessionskvitto, svarar premium på C5 (fältet
`detaljniva`) utan fynd med allvar 3 eller 4. Ägaren kan godkänna själv, i sin egen terminal eller i portalen, och hans
väg och hans senare beslut går före. Varje godkännande är förseglat (`kontroller/sigill.py`); bygget tar vid bara därifrån.
**Överlämningen** efter godkännandet: `designfas.py overlamna <slug>`, DESIGN.md i paketet ifylld ur den
godkända versionen, och `overlamna --prova` utan brister; källan med `package.json` och låset står i paketets `kalla/`.

## Visningen: en privat artefakt per riktning

Efter varje sparad version: `designfas.py artefakt <slug> <kNN>` bygger paketet i
`underlag/<slug>/design/artefakt/<kNN>/` (visningssidan `index.html` och varje version under `vNN/` med den byggda
startsidan och `_astro/`) och skriver `FILER.json`. Publicera det med Artifact-verktyget: `file_path` är paketets
`index.html`, `root` paketets katalog och `files` listan ur `FILER.json` (över 255 filer: `FILER-1.json`,
`FILER-2.json` … i tur och ordning till samma adress). Riktningens första publicering skapar artefakten; därefter
uppdaterar du samma artefakt (`url` ur `status`), aldrig en ny. Artefakten är privat: dela den aldrig och publicera inget
kundmaterial offentligt. Registrera publiceringen: `designfas.py artefakt <slug> <kNN> --url <adress> --version <vNN>`.
Ägarens kommentarer i artefakten når dig medan sessionen lever: svara på svenska, gör ändringen i projektet som en ny
version och publicera den.

## CSP och paket

Mallens CSP gäller i projektet. Behöver riktningen Radix-dialoger, WASM eller externa bilder lättar du CSP:n i
riktningens `astro.config.mjs`, aldrig i mallen, och skriver skälet på en rad som börjar med `CSP:` i RIKTNING.md;
standardkontrollen godtar lättnaden med skälet och fäller den utan. Skript står kvar med hash. Förhandsvisningen i
artefakten visar inga externa bilder; renderingen prövar sajtens egen CSP.

## Gränser

- Godkännandet sätter den autonoma godkännaren eller ägaren, aldrig du; bygget startar drivaren och publiceringen är
  bara ägarens. Vill ägaren godkänna själv kör han `.venv/bin/python kontroller/designfas.py godkann <slug> <v> --ritning
  <kNN>` i sin egen terminal, där kommandot visar versionen och en kod som han skriver tillbaka (`!`-prefixet i en
  session räcker inte). Du nekas godkännandet, sigillet och nyckeln, `kor.sh`, `--helbygge` och publiceringen.
- Arbeta bara i riktningarnas projekt och designfasens spår; kandidatflödets ateljé, studion och andra kunders filer rör
  du inte.
- Externa tjänster får bara generiska frågor; kundvakten stoppar kundens namn, orter och nummer.
- Sanning: varje namn, tal och påstående om verksamheten har belägg i underlaget; saknat står som märkt platshållare.
  Verksamhetens bilder är dess egna; inget stockfoto eller genererad bild utger sig för att visa verksamheten.
- Kvalitetskraven gäller i varje station: kontrast 4,5:1, riktiga knappar och länkar, primära kontroller minst 44 px,
  inga karuseller, inget sidledsspill, och rörelse som pågår mer än 5 s kan pausas. Underkända tidigare byggen är aldrig
  förebilder (`kunskap/ren-designstart.md`).
- Redovisa tillgång, aktivering, användning och bedömd kvalitet var för sig; din bedömning är din, märkt som sådan.
  Påstå ingen kvalitetshöjning förrän ägaren sett sidan.
