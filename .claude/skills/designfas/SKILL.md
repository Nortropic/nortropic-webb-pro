---
name: designfas
description: Utförarens arbetsinstruktion i Nortropics designfas i Claude Design - riktningar, förfining och överlämning på en Design-duk för en kund, med Nortropics skills, tjänster och specialistpass. Används när ägaren startar ./design.sh <slug> eller ber om designarbete för en kund i Claude Design.
---

# Designfasen i Claude Design — utförarens instruktion

Du är den utsedda utföraren för en kunds duk i Claude Design: den enda som skriver dukens versioner. Ägaren ser,
jämför, kommenterar och väljer på duken. Code gör research, material, specialistbedömningar och kontroller och lämnar
underlag; ingen annan session gör en konkurrerande kunddesign. Hela flödet, miljön och reglerna: `kunskap/claude-design.md`.
Placeringen av varje metod och kompetens: `kunskap/metodkarta.md`, Designfasen i Claude Design.

Argumentet är kundens slug. Arbetsfilerna ligger privat i `underlag/<slug>/design/`; `designfas.py` håller spåret
(`.venv/bin/python kontroller/designfas.py status <slug>`).

## Före duken

1. Läs `underlag/<slug>/KUNDFORSTAELSE.md` först, sedan `BRIEF.md`, `VERKSAMHET.json`, `bilder/BILDER.md`, kundens
   domar (`DESIGNDOMAR.jsonl`), `kunskap/designregler.md` och researchen (`atelje/FORSKNING.md`, referenspaketet
   `referenser/paket-vNN/` med SEKTIONER.md och EXTRAKT.md, tjänsternas svar i `referenser/tjanster/`). Saknas
   KUNDFORSTAELSE.md eller researchen: säg det och be ägaren köra förberedelsen eller researchen; formge inte utan dem.
2. Läs duken om den finns (`designfas.py status`; Artifact `read` av `project/canvas.json`). Finns ingen: skapa den med
   Artifact-verktyget och Design-typen (`https://claude.ai/artifact/QKN21svewxgyPb6SYRqWnd`, titel "<Verksamhet> –
   designfas"), aldrig med `/design` (repots skill med samma namn skuggar kommandot). Registrera den:
   `designfas.py ny <slug> --kanvas <url> --release <typens release>`. Läs typens `artifact-type/dc-runtime.js` med
   Artifact `read` och spara den: `designfas.py runtime <slug> --fil <sparad fil> --release <release>`.
3. Ladda upp kundens bilder som tillgångar (Artifact `publish` med `asset: true`) och registrera varje:
   `designfas.py tillgang <slug> --blob <id> --fil underlag/<slug>/bilder/<fil> --kalla "<rad ur BILDER.md>"`.

## Steg och kompetens

Aktivera skills med Skill-verktyget innan du gör det steget gäller (en användaranropad skill läses hel med Read);
skriv vad du aktiverade, valde och varför i dukens anteckning för riktningen eller i ditt svar. En aktivering som
misslyckas står som det den är.

- **D4 Underlag på duken.** En sida "Underlag" med en ritning eller anteckningar: besökarnas viktigaste uppgifter,
  det som bara verksamheten har, och referenserna i tre perspektiv (bransch, visuell inspiration, implementationsgrund)
  med bild, vad de visar och varför de valdes. Observation, rekommendation och belagd effekt hålls isär; en känd sajt är
  ingen belagd effekt. Skills: refero-design.
- **D5 Riktningarna.** Omkring tio riktningar på sidan "Riktningar", en ritning per riktning (sida: `expand: "fill"`),
  med kundens verkliga innehåll: första vyn, den viktigaste sektionen och navigationen, i mobil och dator. De skiljer sig
  i komposition, bildstrategi, typografisk hierarki, innehållsordning eller interaktion, aldrig bara färg och typsnitt.
  Varje riktning har en anteckning: idé, förebild och de egenskaper den prövar att föra över, implementationsgrund,
  besökarens uppgift och primära handling, antaganden. Kärnan före ritningen: taste (rattarna), frontend-design,
  impeccable `reference/shape.md` och `craft-floor.md`, `kunskap/bild.md`, typeset, clarify och better-writing,
  better-layout och adapt; planen med hallmark `references/macrostructures.md`. Alternativen efter riktningen
  (metodkartan, rollerna komposition, typografi, innehall, responsiv, rorelseskiss). Den första riktningen görs, sparas
  och prövas hel innan de andra (ägarens krav: en representativ riktning före större körningar).
- **D6 Granskning efter renderingen.** Efter varje version: läs bilderna i `versioner/<v>/bilder/` (390, 768, 1440,
  menyn öppen) och kontrollerna i `versioner/<v>/kontroll/`, och granska i ordningen impeccable critique (med Referos
  visuella kontroll mot referensbilderna), audit, layout, typeset och colorize med better-typography och better-colors,
  Emils rörelsepass och polish. Beställ ds_kritik på varje riktning och ds_jamforelse när alla finns. Gör om
  kompositionen när helheten är svag; lägg inte varven på marginaler medan bildregi, innehåll eller hierarki brister.
- **D7 Ägarens val.** Ägaren väljer, kommenterar eller underkänner alla. Skriv ägarens ord ordagrant i ditt svar och
  i versionens orsak; inget val görs åt ägaren.
- **D8 Förfining.** Den valda riktningen fördjupas: hela startsidan, tillstånden (meny, fokus, formulärfel) som
  interaktiva ritningar (`is_interactive`), rörelsen med syfte. Specialistinsatser beställs (nedan) och förs in i nästa
  version med bedömningen före och efter.
- **D10 Överlämningen**, efter ägarens godkännande: `designfas.py overlamna <slug>`, fyll i `DESIGN.md` i paketet ur
  den godkända versionen (varje värde `uppmätt:` ur renderingen eller `valt:` i designen), och formalisera kundens
  designsystem med Design System-typen (`kunskap/claude-design.md`, Designsystemet). `designfas.py overlamna <slug>
  --prova` ska sluta utan brister.

## Varje version

Efter varje publicering: läs tillbaka dukens filer (Artifact `read` med `paths: ["project/canvas.json", "project/<ritning>.dc.html", …]`
och `out_dir` i scratchpaden) och spara versionen:
`designfas.py version <slug> --fran <out_dir> --artifact-version <versions-id ur publiceringen> --orsak "<vad den svarar på>" [--bestallning B00N]`.
Den kopierar filerna oförändrade, renderar dem med Design-typens körmiljö i 390/768/1440 och med menyn öppen, och kör
axe och stilrapporten. Har ägaren redigerat på duken sedan förra versionen: läs om filerna, och spara ägarens ändring
som en egen version med `--av agaren` innan du ändrar något.

## Specialistinsatser

En insats som kräver den lokala verktygslådan beställs, utförs i Code och förs in av dig:
`designfas.py bestall <slug> --typ <typ> --version <v> --ritning <fil> --uppgift "<vad och varför>" [--material <fil>]`,
sedan `designfas.py specialist <slug> B00N` (ett pass i repot med rollens kompetensblock och kvitto; svaret i
`svar/B00N/SVAR.md`). Typerna: referenser, komponent (21st), typografi, innehall, responsiv, rorelse, granskning
(t.ex. ett formulär), kritik, bild (bildurval), jamforelse. Läs svaret och bilderna, för in det du bedömer bär i nästa
version med `--bestallning B00N`, och skriv bedömningen: `designfas.py infor <slug> B00N --version <v> --bedomning "…"`.
Parallella pass lämnar underlag; bara du ändrar duken.

## Gränser

- Godkännandet är ägarens: säg till ägaren att köra `! .venv/bin/python kontroller/designfas.py godkann <slug> <v>
  --ritning <fil>` (du nekas kommandot). Designgodkännande, byggstart och publicering är tre beslut; du startar inget bygge.
- Externa tjänster (Refero, Mobbin, 21st, Motion, webben) får bara generiska frågor; kundvakten stoppar kundens namn,
  orter och nummer.
- Sanning: varje namn, tal och påstående om verksamheten har belägg i underlaget; saknat står som märkt platshållare.
  Verksamhetens bilder är dess egna; inget stockfoto eller genererad bild utger sig för att visa verksamheten.
- Underkända tidigare Nortropic-byggen och ersatta domar är aldrig förebilder (`kunskap/ren-designstart.md`).
- Dukens ritningar följer Design-typens format (läs `artifact-type/reference/format.md` och `craft.md` på duken) och
  våra kvalitetskrav (kontrast 4,5:1, riktiga knappar och länkar, primära kontroller minst 44 px, inget sidledsspill).
- Skriv till ägaren vad som händer på duken, inte mekaniken; redovisa tillgång, aktivering, användning, belagd
  tillämpning och bedömd kvalitet var för sig, och märk din egen bedömning som din.
