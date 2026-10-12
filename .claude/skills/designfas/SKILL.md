---
name: designfas
description: Utförarens arbetsinstruktion i Nortropics designfas i Claude Design - riktningar och förfining på en Design-duk som ett produktionsband, där varje skill gör en synlig insats i sin station. Används när ägaren startar ./design.sh <slug> eller ber om designarbete för en kund i Claude Design.
---

# Designfasen i Claude Design — bandet

Du är den utsedda utföraren för en kunds duk i Claude Design: den enda som skriver dukens versioner. Ägaren ser,
jämför, kommenterar och väljer på duken. Code gör research, specialistbedömningar och kontroller och lämnar underlag.
Sidan skapas på ett band: varje station har sin fråga och sina skills, och dess insats ska synas på sidan. Läsning är
ingen insats. Hela flödet: `kunskap/claude-design.md`. Bandet: `kunskap/metodkarta.md`, Bandet: stationerna.

Argumentet är kundens slug. Spåret: `.venv/bin/python kontroller/designfas.py status <slug>` (versionerna och bandets
läge per riktning).

## Din grund (kort)

Läs `underlag/<slug>/KUNDFORSTAELSE.md`, `kunskap/designregler.md` och bandets tabell. Mer läser du inte i förväg:
varje station ger dig sina skills när det är dess tur. Säger två skills emot varandra avgör metodkartans Avgöranden och
designreglerna, aldrig vilken skill du läste sist. Saknas KUNDFORSTAELSE.md eller researchen (`atelje/FORSKNING.md`,
referenspaketet): säg det och be ägaren köra dem; formge inte utan dem.

## Före bandet

1. Läs duken om den finns (`designfas.py status`). Finns ingen: skapa den med Artifact-verktyget och Design-typen
   (`https://claude.ai/artifact/QKN21svewxgyPb6SYRqWnd`, titel "<Verksamhet> – designfas"), aldrig med `/design`
   (repots skill med samma namn skuggar kommandot). Registrera den: `designfas.py ny <slug> --kanvas <url> --release
   <typens release>`. Läs typens `artifact-type/dc-runtime.js` och spara den: `designfas.py runtime <slug> --fil <fil>
   --release <release>`. Läs typens `artifact-type/reference/format.md` och `craft.md`.
2. Ladda upp kundens bilder som tillgångar och registrera varje: `designfas.py tillgang <slug> --blob <id> --fil
   underlag/<slug>/bilder/<fil> --kalla "<rad ur BILDER.md>"`.

## En station i taget

För varje riktning (en ritning, en sida med `expand: "fill"`) går du bandet i tabellens ordning, som följer
processmodellen: förstå (underlag), innehåll och struktur, art direction, komposition, visuell form, interaktion,
utvärdering, iteration. Mobilen bär formen från första ritningen: rita och pröva 390 först. Tillgängligheten är ett
krav i varje station från art direction och framåt (riktiga element, kontrast, fokus, 44 px, reflow, reducerad rörelse).

1. `designfas.py station <slug> <station> --ritning <fil>` ger stationens arbetsinstruktion: frågan, skills och
   tjänster bara för stationen, indata, utdata och kontroll.
2. Gör stationen. En station som ändrar ritningen görs helst av en underagent (Agent-verktyget) som får
   instruktionen, aktiverar stationens skills med Skill (en användaranropad skill läses hel med Read), ändrar bara det
   stationen gäller och lämnar en ändrad ritning och en kort redovisning. Du granskar ändringen mot frågan.
3. Publicera och lägg en anteckning på duken med versionens id (`status` visar nästa), till exempel
   `"v04":{"x":…,"y":…,"text":"v04 · Typografi: rubrikskalan 1,25 → 1,33, radlängd 66 tecken","w":360,"fill":"blue"}`
   intill ritningen.
4. Läs tillbaka dukens filer (Artifact `read` med `paths` och `out_dir`) och spara versionen:
   `designfas.py version <slug> --fran <out_dir> --artifact-version <id> --station <station> --ritning <fil> --orsak
   "<vad stationen ändrade och varför>"`. Den renderar i 390/768/1440 med menyn öppen, kör kontrollerna och prövar om
   insatsen syns mot förra versionen av ritningen (`insats`). Syns den inte: säg varför (stationen fann inget att göra,
   med skäl) eller gör om.
5. En station som inte gäller sidan hoppas över med skälet på nästa version: `--hoppa <station>="<skäl>"`. Stationen
   rörelse gäller alltid: ingen rörelse är beslutet "stilla", med skäl i orsaken. Kritiken och tillgängligheten körs
   alltid och kan inte hoppas över.

**Innehåll och struktur** ger riktningens första version: strukturen med det verkliga innehållet (content first),
och **art** ger den sitt språk. **Kritiken** är ett specialistpass som ser bilderna och briefen före din förklaring:
`designfas.py bestall <slug> --typ kritik --station kritik --version <v> --ritning <fil> --uppgift "…"` och
`designfas.py specialist <slug> B00N`. Svaret säger om bandet ska gå tillbaka (`atergang`: innehåll och struktur, art
direction eller komposition); är helheten svag gör du omtaget innan du lägger varven på detaljer. **Tillgängligheten** utgår från renderingens axe, fokus och reflow i
versionens BILDER.json och kontroll/. Andra stationer kan också beställas som pass (typen och stationen i tabellen) när
du vill ha en oberoende insats; svaret förs in i en version med `--bestallning B00N` och bedöms med `designfas.py infor`.

**Omkring tio riktningar.** Varje riktning går underlag, innehåll och struktur, art, komposition och kritik innan
ägaren väljer; den valda går resten av bandet. När flera riktningar finns körs jämförelsen (`--typ jamforelse --station jamforelse`).
**Överlämningen** efter ägarens godkännande: `designfas.py overlamna <slug>`, DESIGN.md i paketet ifylld ur den
godkända versionen, kundens designsystem med Design System-typen, och `overlamna --prova` utan brister.

## Gränser

- Godkännandet är ägarens: säg till ägaren att köra `! .venv/bin/python kontroller/designfas.py godkann <slug> <v>
  --ritning <fil>` (du nekas kommandot). Designgodkännande, byggstart och publicering är tre beslut.
- Ägarens kommentarer på duken (Send to Claude) når dig medan sessionen lever: svara på svenska i tråden med vad du
  gör, gör ändringen som en ny version och stäng tråden när den är åtgärdad.
- Externa tjänster får bara generiska frågor; kundvakten stoppar kundens namn, orter och nummer.
- Sanning: varje namn, tal och påstående om verksamheten har belägg i underlaget; saknat står som märkt platshållare.
  Verksamhetens bilder är dess egna; inget stockfoto eller genererad bild utger sig för att visa verksamheten.
- Kvalitetskraven gäller i varje station: kontrast 4,5:1, riktiga knappar och länkar, primära kontroller minst 44 px,
  inga karuseller, inget sidledsspill. Underkända tidigare byggen är aldrig förebilder (`kunskap/ren-designstart.md`).
- Redovisa tillgång, aktivering, användning och bedömd kvalitet var för sig; din bedömning är din, märkt som sådan.
  Påstå ingen kvalitetshöjning förrän ägaren sett sidan.
