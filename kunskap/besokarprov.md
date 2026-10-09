# Besökarprov med verkliga deltagare — protokoll

Ägarens uppdrag 2026-10-09, punkt 5 (`BESLUT.md`, tillägget samma dag): förbered nu, genomför vid rätt tillfälle.
Källa: GOV.UK Service Manual, "Using moderated usability testing" (läst 2026-10-09). Provet visar om besökare kan göra
sina viktigaste uppgifter på sajten och var de tvekar. Ägarens estetiska dom och den automatiska bildjämförelsen mot den
godkända prototypen (`kontroller/prova.py`, `vinnarjamforelse`) är andra frågor. Granskarens kognitiva genomgång och
webbläsarvägens simulerade besökare (`kunskap/webblasare.md`) är AI-bedömningar, inga observationer av verkliga besökare.

**När:** när en användbar prototyp finns (en godkänd kandidat eller ett helbygge) och före en skarp lansering.
Rekrytering, deltagarnas medverkan, samtycke och eventuell inspelning kräver ägarens mandat per prov; protokollet ger
inget sådant mandat. I en prospektdemo står besökarbeteendet som "ännu inte observerat".

## Förbered

1. **Uppgifterna** skrivs ur `underlag/<slug>/BRIEF.md`, toppuppgifterna och den primära handlingen: en uppgift per
   toppuppgift, högst fem. Varje uppgift är besökarens mål i en trovärdig situation och nämner varken sidor, rubriker,
   knappar eller sajtens egna ord. Neutral: "Elcentralen löser ut varje kväll och du vill få hjälp i veckan. Använd
   sajten för att se om och hur det går." Ledande, och därför fel: "Tryck på Boka elektriker." Klar när varje uppgift
   har ett mål och en situation, och ingen uppgift ger bort svaret.
2. **Deltagarna:** tre till fem personer som hör till kundens besökare enligt briefen. Ingen från Nortropic och ingen
   från verksamheten. De betecknas D1, D2 …; namn och kontaktuppgifter står aldrig i rapporten.
3. **Samtalsguiden:** introduktionen ("vi prövar sajten, inte dig"), uppgifterna i ordning och vad som är version under
   prov: kandidatens version eller byggets commit med `dist`-sha. 30–60 minuter per person.

## Genomför

Moderatorn läser uppgiften, tittar och lyssnar. Hen frågar bara klargörande ("vad får dig att säga det?") och hjälper
bara när deltagaren har kört fast helt. Hjälpen antecknas, och uppgiften räknas då som klarad med hjälp.

För varje uppgift och deltagare antecknas:
- **utfallet:** klarad, klarad med hjälp, eller inte klarad;
- **vägen:** vilka sidor och vilka delar deltagaren använde, i ordning;
- **tvekan:** var deltagaren stannade, gick tillbaka eller letade, och hur länge;
- **missförstånd:** vad deltagaren trodde, med egna ord ordagrant;
- **stoppet:** var deltagaren körde fast, och vilken uppgift som saknades.

## Efter provet

Varje fynd skrivs som en rad: vad som observerades och hos hur många (till exempel "3 av 5"), hur allvarligt det är
(hindrar uppgiften, fördröjer, stör), ändringen som beslutas och vem som beslutar (ägaren eller kunden), var ändringen
gjordes (kandidatens version eller commit), och om den är prövad igen med nya deltagare. Fem personer räcker för att
hitta problem, inte för att mäta hur vanliga de är.

## Var resultatet står

Ett prov är en rapport: `underlag/rapporter/BESOKARPROV-<slug>-<ÅÅÅÅMMDD>.md`, med rapporthuvudet (`README.md`, Var
information finns). Huvudet bär `typ: besökarprov`, `kund`, `granskad_identitet` (versionen under prov),
`rapportstatus` och `bedomningsutfall`. Dashboardens vy Dokumentation och rapporter visar den bland lägesrapporterna.
Inspelningar och anteckningar med personuppgifter ligger utanför repot enligt mandatet för provet.
