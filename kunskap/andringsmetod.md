# Ändringsmetoden: en ändring på en levererad webbplats

Den kanoniska metoden för webbplatsens ändringsagent (ägarens tillägg 2026-10-11; `kunskap/andringar.md`). Startvägen
(`kontroller/andringar.py`) lägger den i agentens startinstruktion med sin version; webbplatsens egen kunskap står i dess
privata KUNSKAP.md, inte här.

## Varje uppdrag

1. **Förstå.** Läs uppdraget, bilagorna och det läget säger om arbetskopian. Klart när du kan säga i en mening vad som
   ska vara annorlunda för besökaren och vad som ska stå kvar. En läsande fråga ("var står öppettiderna?") besvaras och
   slutar där.
2. **Hitta källan.** Sök upp varje ställe där uppgiften eller elementet bor: sidan, komponenten, innehållsfilen, delade
   uppgifter (sidfot, metadata, strukturerad data) och upprepningar. Klart när varje träff är bedömd: ändras, står
   kvar med skäl, eller ligger utanför uppdraget.
3. **Ändra avgränsat.** Ändra källan, aldrig den byggda filen. Följdändringar som uppdraget kräver ingår; en omdesign,
   ett beroendebyte eller en ny integration är utvidgad omfattning, som du säger och väntar med. Filerna som Nortropics
   export skriver (CLAUDE.md, README, paketfilerna, Workern, wrangler.jsonc, public/_headers, src/verifiering.json)
   skrivs om vid nästa export: en ändring i dem står under **kvarstår** i redovisningen, och det som ska bestå skrivs i
   KUNSKAP.md.
4. **Prova.** Kör provvägen (startinstruktionen ger kommandot) och läs bilderna i 390 och 1440 px. Klart när bygget är
   grönt, kontrollen godkänd och det ändrade syns rätt i båda bredderna; en brist rättas och provet körs igen.
5. **Dokumentera.** En bestående lärdom (var en uppgift bor, ett specialfall, kundens designregel) skrivs i KUNSKAP.md
   med källa och version. Ett tillfälligt fel blir ingen regel, och inget om den här kunden gäller någon annan.
6. **Redovisa och lämna.** Committa de filer uppdraget ändrade genom motorns commitväg (startinstruktionen ger
   kommandot; främmande ändringar i arbetskopian står kvar utanför commiten) med ett meddelande som börjar med
   "Ändring: ", och kör provvägen en sista gång om något ändrats efter förra körningen: motorn kvitterar commiten som
   kundens leverabel först när provvägen godkänt exakt dess innehåll. Skriv överst i ANDRINGAR.md: datum, uppdragets
   ord, **ändrat**, **prövat**, **kvarstår**, commit och publiceringsläge. Samma redovisning, kort, i terminalen.

## Bedömningen per slag

| Ändring | Det som ska vara gjort |
|---|---|
| Text och sakuppgifter | Rätt källa och språk; uppgiften ur kunden eller verifierat underlag, inga påhittade meriter eller löften; upprepningar bedömda; adresser och metadata rörs bara när uppdraget gäller dem. |
| Bilder | Rätt bildplats; originalet bevarat; storlek och format som sajtens övriga bilder; beskärningen prövad i mobil och dator; alternativtext efter bildens funktion (en dekorativ bild får tom alt). |
| Layout och stil | Kundens uttryck och responsiva regler bevarade; textflöde, kontrast, fokus och spill prövade i de bredder ändringen berör. |
| Navigation och formulär | Länkarna, tangentbordet, valideringen och fel- och lyckatillstånden prövade lokalt; inget riktigt utskick. |
| Kod och funktion | Repots egna bygg- och provkommandon; den ändrade användarvägen prövad; proven står kvar som de var. |

## Tillstånden

En ändring i arbetskopian, en commit, en kvitterad leverabel, en förhandsvisning och produktionen är fem olika
tillstånd. Säg vilket resultatet står i. Förhandsvisningen och releasen görs av motorn och Johnny i appen, med Johnnys
mandat; "publicerat" sägs först när motorns kvitto säger det.
