# Skapandeflödet

Ett designflöde för startsidan, samma kod och samma text vid varje ingång (Codex via ägaren 2026-10-05: tre designflöden,
där förbättringarna inte följde med mellan dem, blev ett). Orkestratorn är `kontroller/atelje.py`; de delar som alla
steg använder står i `kontroller/skapande.py`. Ingångarna:

- **Ägarens prototyp:** `.venv/bin/python kontroller/prototyp.py <slug>`, utanför bygget. Läget följer ägarens senaste
  dom i domloggen. Ägaren dömer i dashboardens vy Prototyp.
- **Byggets steg 5.1:** `kor.sh` har ateljévägen som standard. En startsida som ägaren godkänt tas över utan ny ateljé.
  `NWP_ATELJE=av` är nödvägen, där byggaren skriver KONCEPT.md själv.

Sammanhållningen följer ett välgrundat val, och iterationen får ändra grundidén. Därför utforskas skilda grundidéer
först, och huvudreferensen blir den valda riktningens referens efteråt.

## Stegen

1. **Underlag.** Verksamhetens fakta gäller och ändras aldrig: VERKSAMHET.json, RESEARCH.md med belägg, `kalla/`,
   egna bilder och textens sakuppgifter. Designbesluten är grundidé, referensurval, palett, typografi, komposition,
   bildurval och beskärning, och rubrikernas form. De prövas mot ägarens domar (domloggen) och mot de prövade
   grundidéerna (historiken). Prompterna får båda som text.
2. **Utforska.** Skaparen läser metoden först och tar fram tre riktningar som är olika grundidéer: komposition,
   typografiskt system, bildstrategi och palettens källa. Varje riktning bygger på sin egen huvudreferens, och
   RIKTNINGAR.md anger den med raden `Huvudreferens N: <rubrik i REFERENSER.md> — <vad den bär>`. Per riktning byggs
   hela startsidan, början av en undersida och en stiltavla, och skaparen förhandsvisar minst två varv per riktning.
   Två riktningar på samma referens är ingen utforskning: den andra blir ofullständig. En referens som en förkastad,
   underkänd eller lämnad riktning redan byggt på (historiken) märks prövad, och en riktning på den kräver raden
   `Återanvänd: <skäl ur verksamhetens material som svarar på kritiken>`; annars är den ofullständig.
   När urvalet saknas, till exempel efter ett omtag, väljer skaparen ur referenspaketet och skriver REFERENSER.md med en
   rad `Huvudreferenskandidat: <rubrik> — <vad den bär>` per grundidé.
3. **Välj.** Tre isolerade domare (formgivning, funktion och kunden, med andra modeller än skaparen) dömer varje riktning
   mot ägarens kalibreringsankare, ägarens domar, historiken och riktningens egen referens. En riktning är godkänd bara
   när en strikt majoritet säger ja med nivån over. Förkastar panelen alla görs en ny omgång med kritiken, och därefter
   stannar flödet: bäst av undermåliga blir aldrig vald. Vid ett val bevaras vinnaren (`atelje/vinnare/`), och
   VINNARE.json bär den valda huvudreferensen, som `kontroller/referensval.py` läser före REFERENSER.md. Startsidan
   förs över till `src/pages/index.astro`.
4. **Förfina.** En ny session bearbetar den överförda startsidan i minst tre förhandsvarv. Skaparen läser metoden och
   panelens svagheter, och huvudreferensens bilder i varje varv. FORFINING.md anger per varv de synliga bristerna och
   regeln som rättade dem. Bär grundidén inte med verksamhetens material skriver skaparen TILLBAKA.md, och en ny
   utforskning startar med det som kritik.
5. **Slutdom.** Samma panel dömer startsidan före förfiningen mot efter, blint. Före är den panelen valde, eller vid
   putsning versionen ägaren dömde. Domen svarar på två frågor: håller den ribban, och blev den synligt bättre
   (SLUTDOM.md). Vinnaren blir den förfinade, med DESIGN.md om förfiningen skrev den.
6. **Ägaren.** Vyn Prototyp visar före och efter bredvid huvudreferensen och riktningarna som prövades. Vilken riktning
   som förfinades syns, eftersom ägaren dömer den synliga förbättringen. Panelens skäl, poäng och slutdom, förfiningens
   logg och redovisningen visas först när ägaren dömt, så att ägarens dom är oberoende av dem. Domen går till domloggen.
7. **Överlämning.** Ägarens godkännande skrivs i VINNARE.json (`godkand`, med hashen för den dömda startsidan och
   DESIGN.md som vinnaren bevarar i `atelje/vinnare/`; sajtens filer måste vara samma när ägaren godkänner).
   Bygget tar vid därifrån som från en ateljévinnare: startsidan och koden, bilderna, och DESIGN.md (bygg-sajt steg 5.1).
   Godkännandet gäller bara när ägarens senaste dom i domloggen, direkt eller via Codex, är just det och vinnarens
   filer är oförändrade (`skapande.godkand_giltig`). Bygget skriver sedan om sajtens egna filer utan att godkännandet
   upphör, så ett nytt bygge kan ta vid igen. En senare dom och en ny förfining drar tillbaka det. Tillåter domloggen
   inget bygge, startar inget i skapandeflödets väg (kor.sh, `prototyp.bygget_nekas`): det gäller putsa eller ny
   riktning efter körningen, en dom som inte gäller någon körning, och ett godkännande som inte gäller. Nästa steg är
   då prototyp.py. Nödvägen `NWP_ATELJE=av` påverkas inte.

## Domloggen och vad en dom återöppnar

`underlag/<slug>/DESIGNDOMAR.jsonl` har en rad per dom: tid, källa (ägaren, ägaren via Codex, panelen), beslut och text
ordagrant. Loggen arkiveras aldrig. Nästa körning läser den själv, och prompterna börjar med de senaste domarna. Vyn
Prototyp skriver ägarens dom. En dom som kom på annat sätt, via Codex eller i en session, förs in ordagrant med
`.venv/bin/python kontroller/skapande.py dom <slug> --kalla … --beslut … --fil <text>`. Båda går genom samma väg
(`atelje.doma`): bara en klar körning kan godkännas, en pågående körning döms inte, ett godkännande prövas innan
domen skrivs, och en annan dom från ägaren drar tillbaka det. Under ett
bygge är loggen låst (kor.sh, `chflags uchg`), så domen skrivs när bygget är klart; en ändring under bygget ger
slutkod 3. Finns tidigare designbeslut utan dom, eller en dom som inte gäller någon körning i skapandeflödet, vägrar
prototypen att gissa läget.

- `ny_riktning` återöppnar alla designbeslut, aldrig fakta. `kontroller/atelje.py <slug> --ny-riktning` (eller
  prototyp.py) flyttar REFERENSER.md, KONCEPT.md, ateljén, äldre prototyper, förhandsvarven och hela
  `kunder/<slug>/sajt` till `~/Arkiv/nortropic-webb-pro-skapande/`. Inget raderas. Sajten görs om ur mallen, och den
  dömda riktningen förs in i historiken med domen.
- `putsa` behåller riktningen: förfiningen och slutdomen körs igen, med domen som kritik. Förra slutdomen och
  redovisningen arkiveras först.
- `godkand` lämnar över till bygget.

Ett tidigare designval, till exempel en färg, är inget förbud. Ett drag ur en underkänd grundidé behöver ett skäl ur
verksamhetens material, och skälet ska också svara på kritiken mot den.

`underlag/<slug>/RIKTNINGSHISTORIK.json` samlar prövade grundidéer: namn, huvudreferens, drag, utfall (vald eller
förkastad av panelen, lämnad av skaparen, underkänd av ägaren) och kritiken. Ateljén skriver efter varje panel och vid
TILLBAKA; omtaget skriver ägarens dom.

## Avbrott

Föll en körning tar `.venv/bin/python kontroller/atelje.py <slug> --fortsatt` vid efter den senaste klara fasen: i
utforskningen vid omgången som föll, med samma kritik som första gången (skaparens TILLBAKA.md eller panelens VAL.md),
och i en putsning vid förfiningen eller slutdomen mot samma före. En avslutad körning (klar, förkastad, tillbaka) tas
aldrig upp igen, och varken `--fortsatt` eller `--bara-domare` körs när ägaren dömt efter körningen; där avgör
ägarens dom nästa steg. Det som flyttas undan, äldre riktningsbilder och en tidigare vinnare, hamnar i `atelje/foregaende/`. Inget
raderas.

## Research på begäran

Skaparen skriver `underlag/<slug>/atelje/KOMPLETTERING.json` (varför, och ett referensuppdrag och/eller frågor till
Refero och Mobbin) och avslutar sessionen. Orkestratorn kör det befintliga referenssteget: `kontroller/referens.py` ger
en ny, komplett paketversion som ärver den förra, och `kontroller/referenstjanster.py` söker i tjänsterna med belägg.
Sedan startar en ny session med resultatet. Det får ske högst två gånger per omgång och fas. Skaparens egna sessioner
har inget eget nät, så begäran är deras enda kanal ut, och dess form begränsas (`skapande.kanal_fel`): högst tre
kandidater med ursprungsadresser i korta etiketter (å, ä, ö i punycode), högst fyra sidvägar per kandidat med högst
fyra led (å, ä, ö procentkodade) utan frågesträng, och högst tre frågor på högst 160 tecken utan adresser. Kanalen är
smal, inte stängd: värdnamnet och vägarna går ut. Skaparens egna sidor når inget nät när de fotograferas
(inspektionen släpper bara sidans eget ursprung).

## Metoden per steg

`skapande.METOD` är listan, och prompterna räknar upp den:

- utforska: frontend-design, taste (§0 och §4), emil-design-eng, bild.md, referenser-professionella.md, visuell-niva.md,
  better-layout och better-typography;
- förfina: referenser-professionella.md, bild.md, copy-kontroll.md, better-layout, better-typography, better-ui,
  better-colors, better-writing och humanizer;
- research: referensjakt.md.

En installerad skill finns inte i kontexten förrän den laddas. Skaparen läser den med Read eller anropar den med Skill.

## Körspåret

REDOVISNING.md i ateljén skrivs ur sessionernas transkript (`kontroller/bildkedja.py`):

- metodkvittot: vilka metodfiler och skills som lästes före första skrivningen;
- läsningen per förhandsvarv i ordning: varvets fyra bilder och minst en referensbild, lästa efter varvets
  förhandsvisning och före nästa ändring;
- researchen;
- panelernas domar med läsning;
- slutdomen före mot efter.

Claude Codes medietak (omkring 24 MiB bilddata per anrop) tränger undan de äldsta bilderna ur kontexten. Därför läses
huvudreferensen om i varje varv. Ett räknat antal bildläsningar är inget belägg för en jämförelse.

## Sandlådan

Skapandeflödets sessioner har ingen egen sandlåda än: flödet körs utanför den, före bygget. Sessionerna har bara sina
namngivna verktyg och inget eget nät, och sandlådans lista över hemligheter nekas dem (`atelje.NEKAS`; ägarens egna
regler läses inte i en nästlad session). Paket installeras bara med `kontroller/typsnitt.py` (Fontsource, namnen prövade,
`--ignore-scripts`). Research går genom referenssteget. Utforskningen skriver med sina verktyg bara sidorna,
RIKTNINGAR.md, KOMPLETTERING.json och urvalet, och förfiningen bara sajtens src/, DESIGN.md och sina tre filer. Det är
en gräns för verktygen, inte för koden: sidorna är kod som körs när sajten byggs (Astros frontmatter). Därför körs varje
bygge av skaparens sidor innanför processgränsen (`kontroller/processgrans.py`): förhandsvisningen, fotograferingen och
slutdomen. Där skrivs bara i byggets egna kataloger, och bygget når inget nät, inte heller localhost, där
dashboarden tar emot ägarens domar (`processgrans.py --utan-nat`). Ett sandlådat bygge (`NWP_SANDLADA=pa`)
kräver därför en godkänd startsida och tar vid från den. Nästlade sessioner skriver aldrig i ägarens automatiska minne
(`kontroller/nastlad.py`).
