# Arbetsytan

Ägarens interna arbetsstation i dashboarden: samtalet med Nortropic-partnern, kundens riktiga förhandsvisning, de
sessioner som arbetar, byggflödet och koden, för en kund i taget och över samma läge. Varför den finns och varför
huvudvägen är den befintliga dashboarden: `BESLUT.md`, tillägget 2026-10-09 om den visuella arbetsytan. Arbetet:
`backlog/B-20261009-visuella-arbetsytan-samtal-preview-sessioner-och.md`.

## Starta och gå tillbaka

```sh
./dashboard.sh arbetsyta [kund]     # http://127.0.0.1:4771/#/arbetsyta/<kund>; utan kund den senast aktiva
```

Arbetsytan är också första valet i dashboardens meny. `./dashboard.sh` utan argument öppnar Översikten som förut, och
alla tidigare vyer finns kvar, med länkar under Fler vyer och Klassisk vy (Flöde) i arbetsytans huvud. Arbetsytan är
en extra rutt (`#/arbetsyta`) med egna filer; ingen motorfil beror på den. Läget räknas fram vid varje läsning, så
att sluta använda den, eller ta bort den med en revert av dess commits, lämnar motorn, domloggen och bevisen orörda.

Claude-panelen i Claude Code (terminalen och Desktops Code-flik): `claude --plugin-dir mod/nortropic-arbetsyta`, och
`/nortropic` öppnar panelen; se Claude-panelen nedan.

## Vyerna

Tre vyer över samma läge och samma identiteter (kund, körning, kandidat och version, roll, sessions-id):

- **Arbetsyta**: projekthuvudet (kund med testmärkning, körningen, kandidaten och versionen, momentet, senaste
  observation och anslutningen), partnerns samtal till vänster, huvudmaterialet i mitten och rollsessionerna till
  höger, med Kontroller, Senast observerat och Nästa beslut under materialet. Huvudmaterialet följer momentet:
  kundunderlaget före prototypen, kandidaterna med neutrala etiketter vid valet, förhandsvisningen under arbete och
  bygge. Panelerna fälls ihop och dras i bredd; valet sparas per kund i webbläsaren. Under 900 px visas ett område i
  taget (Samtal, Resultat, Sessioner).
- **Byggflöde**: kundens nio observerade steg (samma som Flöde), sessionerna grupperade per moment och kandidat med en
  detaljvy (aktivitet, lästa filer, laddade skills, resultat), Sessionsflödet (startbegäranden, sessioners start och
  slut, dina ändringar, körningar) och helbyggets körningar som historik. Metodkartan (README:s kedja) står för sig;
  Kirurgen, backloggen, kalibreringen och rapporterna står i en egen del, skild från kundproduktionen.
- **Kod och preview**: kandidatens filer med projektets egna vägar, diff mot en namngiven bevarad version
  (`versioner/<v12>/`, den fotograferade förvald), Öppna i editorn (Visual Studio Code, annars textredigeraren),
  förhandsvisningen, Körningsloggen och sessionens aktivitet. Kod redigeras inte i webbläsaren.

Förhandsvisningen är märkt efter vad den är: **arbetsversion** (det levande bygget i `dist/`, kan ändras medan arbetet
pågår), **ögonblicksbild** (den bevarade fotograferade versionen, med version och tid) och **export** (kundrepots
commit). Mobil och Dator ändrar bredden, inte versionen. Saknas bygget visas den senaste fungerande ögonblicksbilden
märkt Äldre, aldrig som aktuell.

## Läget (kontraktet `arbetsyta/1`)

`dashboard/arbetsyta.py` `lage(slug)` ger ett läge per kund, samlat ur det som redan finns: `flode()` (steg, besked,
handlingar, startmiljö och blindning), ateljéns `STATUS.json`, `kandidater.sammanstall`, observatörens förteckning och
transkript, startjournalen, helbyggets `START.json`, stream-json-logg och `SLUT.json`, domloggen och partnersamtalets
koppling. Inget i läget är en egen status: det räknas fram vid läsningen, och en del som inte går att läsa står i
`ofullstandig` med skälet. Läsningen startar inget och gör inga modellanrop.

Varje session i läget bär kund, körning, kandidat, roll, ansvar, sessions-id, förälder (ateljéns arbetare, kor.sh eller
dashboardens partnertur, med pid och start-id) och ett av åtta lägen. Liv avgörs av processen (en levande nästlad
claude-session), aldrig av hur nyligen något hände:

| Läge | Betyder |
|---|---|
| väntar på start (`vantar`) | ansvaret har ingen session i körningen; en konfigurerad men inte startad granskare står här |
| start pågår (`startar`) | processen lever men transkriptet syns inte än, eller partnerns meddelande är journalfört utan process |
| arbetar (`aktiv`) | processen lever |
| väntar på verktyg (`verktyg`) | processen lever och senaste verktygsanropet har inget svar än |
| väntar på ditt beslut (`beslut`) | körningen är klar för din bedömning och inget utförande lever (står på utförandet; granskningen utan session står kvar som väntar på start) |
| avslutad (`avslutad`) | sessionen slutade med kod 0 och utan fel i sin svarsfil, eller partnerns tur är besvarad; ett avslut är inget godkännande |
| avbruten (`avbruten`) | stopp, tidsgräns, en signal, en annan slutkod, `is_error` i sessionens svarsfil, eller en process som inte lever utan observerat slut |
| okänt läge (`okant`) | pid saknas eller tillhör en annan process |

Ansvaren: **arbetsledning** är partnersamtalet; **utförande** är research, plan, skaparna, förfiningen och helbygget;
**granskning** är kritikerna, panelen, jämförelsen och planprövningen. Ett verktygsanrop är inget resultat; resultatet
är kandidatens version och förhandsvisning, slutposternas besked och det du beslutar.

**Strömmen** (`GET /api/arbetsyta/<slug>/strom`, text/event-stream): servern prövar en billig signatur över källorna
varje sekund (ändringstider, storlekar, processernas liv) och skickar hela läget när något ändrats, en puls var tionde
sekund och ett läsfel som en egen händelse. Varje ny anslutning får hela läget först, så en tappad anslutning lämnar ingen
lucka i läget, bara i tiden: vyn visar Återansluter och sedan Inaktuellt efter tolv sekunder, och luckans tider när den
är tillbaka. Delvis skrivna rader, roterade loggar och dubbla händelser hanteras av observatörens stegvisa läsning
(`observation.las_session`) och av att vyn ersätter läget i stället för att lägga ihop händelser. Högst tolv strömmar
samtidigt, var och en i högst 30 minuter. En stängd flik avslutar bara strömmen.

## Följa, meddela, ansluta, stoppa och återuppta

| Handling | Vad den gör | Vad den inte gör |
|---|---|---|
| **Följ** (sessionens kort) | visar sessionens observerade händelser ur transkriptet: verktyg, tid, utfall, lästa och skrivna filers sökvägar, skillnamn | startar ingen modell och skickar inget till sessionen |
| **Meddela** partnern (samtalet) | en ny tur i partnerns egen session | ändrar inget, startar inget arbete |
| **Skicka ändring** (samtalet, avsikt Ändring) | ditt beslut i domloggen genom samma väg som vyn Prototyp, bundet till körningen, kandidaten och versionen i din markering, med vy, sida, del och fil | startar inget; nästa handling (Förfina de valda förslagen) startas uttryckligen under Kontroller |
| **Anslut** interaktivt | bara partnern: `claude --resume <id>` i en terminal, kommandot under Fortsätt i terminalen | motorns `claude -p`-arbetare tar inga meddelanden under arbetet (se nedan) |
| **Stoppa** (Kontroller, två steg) | flödets stoppväg (`prototyp.py --stoppa`, `--stoppa-overgang`): arbetaren och dess sessioner med deras processträd | ingen paus finns; det som är klart bevaras |
| **Återuppta** (Kontroller) | `--fortsatt` genom samma ingång | gör inget klart om |

Start, förfining, stopp, återupptagning och export går genom `POST /api/flode/<slug>/start`, samma väg och samma
start-id i fliken som Flöde (`nwp-start:<kund>:<handling>`, släppt först när svaret bekräftats och läget lästs om):
ett dubbelklick skickar en begäran, ett tappat svar försöks igen med samma start-id, och en andra flik får ett eget
start-id men nekas av servern, eftersom handlingen inte längre är nästa steg eller kundens startlås är upptaget. Ett
start-id som redan slutat svarar med sin slutkod. När en start tagits emot visar
arbetsytan den körningen (huvudet märker den som din start), och dess sessioner dyker upp när de startar; en körning som startats från
terminalen syns på samma sätt.

**Varför inga meddelanden till arbetarna.** Claude Codes meddelanden mellan sessioner (2.1.290) når en `claude -p`-
session, men ett meddelande från en annan process hålls där i fem minuter och släpps sedan om inte arbetaren startats
med `crossSessionInbound: accept`, och ett meddelande mitt i en skapares arbete binds varken till kandidatens version,
startjournalen eller domloggen. En ändring går därför genom ditt beslut och nästa handling, som motorn genomför i sina
egna sessioner.

**Markeringen.** Det en ändring gäller fryses när du markerar: när du väljer Ändring, väljer en kandidat medan
Ändring är vald, eller trycker Markera för en ändring vid en fil i kodvyn. Markeringen bär kund, körning, kandidat och
hel version, vyn där den gjordes, och sida, del och fil; den följer med när du byter flik och står kvar tills du
skickar eller rensar den. Har körningen eller kandidatens version bytts sedan dess står den som inaktuell, och Skicka
ändring är spärrad tills du stämt av mot den aktuella versionen. Servern prövar samma sak: en ändring utan hel version
och körning nekas, och en som inte stämmer med läget nu svarar Inaktuell (409); ingenting vidarebefordras blint.
Ändringens och partnermeddelandets id är en hash av innehållet och markeringen, så samma ändring från ett dubbelklick,
ett omförsök efter ett tappat svar eller en andra flik blir en rad, och en ändrad text blir en ny.

I domloggen är din text domens text, ordagrant, och markeringen står i fältet `arbetsyta`. Skaparen läser markeringen
som en egen rad ("ändringen gäller (ägarens markering i arbetsytan …)", `skapande.kritikrader`), skild från det du
gillade i en kandidat.

## Partnern (arbetsledningen)

`dashboard/partner.py`. En riktig Claude Code-session per kund: första meddelandet `claude -p --session-id <id>`, varje
senare `claude -p --resume <id>`; samtalet fortsätter i samma session och samma minne (prövat: andra turen bar samma id
och mindes förra svaret). Ett meddelande i taget: en tur som pågår, eller en levande claude-process med sessionens id i
sina argument (en interaktiv `claude --resume` i en terminal), gör att nästa meddelande nekas med 409. Samma
meddelande-id ger samma post.

- **Arbetskatalog och läsrätt:** en egen tom katalog, `underlag/<kund>/arbetsyta/partner/rum/`, verktyget Read och
  `--permission-mode dontAsk` med en tillåtelselista: repots `README.md`, `CLAUDE.md`, `BESLUT.md`, `kunskap/`, `kritik/`,
  `backlog/` och kundens `VERKSAMHET.json`, `UPPDRAG.md`, `BRIEF.md`, `RESEARCH.md`, `TEXTUNDERLAG.md`, `INNEHALL.md` och
  `BESTALLNING.md`. Allt annat utanför arbetskatalogen nekas (prövat: `atelje/STATUS.json` nekades, `BRIEF.md` lästes).
  Läsningar inom arbetskatalogen nekas inte av dontAsk, därför är den tom. Inga MCP:er, inget Bash, inget Write.
- **Läget i varje meddelande:** arbetsytans läge ur samma läsväg som vyn, blindat, och din markering (kund, körning,
  kandidat och version, vy, sida, del). Partnern ser alltså bara det du ser.
- **Överlämning:** när du ber om en ändring avslutar partnern med ett `overlamning`-block (kandidat, version, sida, del,
  mål, avgränsning, förväntat). Vyn visar det som ett förslag; Använd som min ändring lägger det i ditt fält, och du
  skickar själv. Partnerns svar blir aldrig ett beslut.
- **Lagring (privat):** `underlag/<kund>/arbetsyta/PARTNER.json` (sessions-id, modell, meddelandenas id, avsikt,
  markering, din text och processens pid) och Claude Codes egen svarsfil per tur i `partner/`. Transkriptet sparar
  Claude Code som vanligt. Ingen annan status. Ingen automatisk gallring: filerna ligger med kundens övriga underlag
  och tas bort med det; transkriptet följer Claude Codes egen `cleanupPeriodDays`.
- **Frist:** en tur stoppas med hela sitt processträd efter `NWP_PARTNER_FRIST` sekunder (600). Startas dashboarden om
  mitt i en tur stoppas den i stället vid nästa meddelande, när fristen gått ut. En `claude --continue` i
  arbetskatalogen syns inte som en annan process (den bär inget sessions-id i sina argument); använd `--resume <id>`.

## Modellprofilen

En hypotes som görs provbar, ingen kvalitetssanning. Arbetsledningen kör `claude-fable-5-1` på effort medium
(`NWP_PARTNER_MODELL`, `NWP_PARTNER_EFFORT`); utförandet och granskningen följer motorns egna standarder, som arbetsytan
inte ändrar: ateljéns skapare `claude-fable-5-1` på `max` (`NWP_ATELJE_MODELL`), kandidatgranskarna
`claude-sonnet-5-5[1m]`, helbygget `opus[1m]`. Vyn visar konfigurerad och observerad modell per session; observerad är
modellen i transkriptet. Att Fable 5.1 ger bättre arbetsledning än en annan modell är inte prövat. Användningen per tur
står vid svaret som Claude Codes rapporterade tokens och listpris (`total_cost_usd`), vilket inte är fakturerad
kostnad: prenumerationen räknar kvot.

## Observationen och dess gräns

Följvyn läser samma läsläge som observatören (`observation.aktivitet`) och lagrar inget nytt. Ur ett anrop visas
verktygets namn, tiden, utfallets klass, för Read och de skrivande verktygen (Edit, Write, MultiEdit, NotebookEdit)
sökvägen och för skillverktyget skillens namn; aldrig promptar, övriga argument (inte Bash-kommandon), svar, skrivet
innehåll eller bilddata. Sökvägen för skrivna filer är en utvidgning av observatörens gräns 2026-10-09, för följvyn.
Underagenters egna anrop syns inte (bara Agent-anropet). Partnerns samtal visas ur dess svarsfiler, inte ur andra
sessioners transkript. Helbyggets session identifieras ur stream-json-loggens första rad.

## Säkerhet och åtkomstgränser

- **Skrivningar** (partnerns meddelanden, ändringar, starter och stopp, öppning i editorn) kräver dashboardnyckeln och
  samma ursprung, som all skrivning i dashboarden. **Läsningar** är öppna för andra processer som samma användare kör,
  som förut. Arbetsytan gör mer läsbart genom API:t än förut (partnersamtalet, kandidatens kod och körningsloggarna),
  men inget som samma användare inte redan når direkt på disken.
- **Strömmen** nekas när webbläsaren anger ett annat ursprung (`Sec-Fetch-Site` annat än same-origin, eller ett annat
  `Origin`), så att en förhandsvisad sajt på en annan port inte kan prenumerera.
- **Förhandsvisningen** körs på provets statiska server på en egen port (ett annat ursprung än kontrollytan), i en
  iframe med `sandbox="allow-scripts allow-forms allow-same-origin"` (ingen toppnavigering, inga popup-fönster) och
  `referrerpolicy="no-referrer"`. Sajtens kod når inte dashboardnyckeln i kontrollytans lagring och kan inte läsa
  kontroll-API:ts svar. Det finns ingen proxy. Dashboardens sida svarar `X-Frame-Options: DENY` och `frame-ancestors
  'none'`, så att en sida inte kan rama in kontrollytan.
- **Kod- och loggvyerna** visar bara textfiler som hör till kandidatens kod (sökvägen prövas del för del: ingen länk,
  inget `..`, inget utanför projektets verkliga väg, högst 512 kB) och visar allt som text, aldrig som HTML. Körningsloggen
  maskerar värden efter ord som nyckel, token och lösenord, efter `Authorization` och `Bearer`, i `sk-`-nycklar och
  i parametrar som `?key=`; en maskering är ett skyddsnät, inget löfte om att en hemlighet aldrig kan stå i en logg.
- **Blindningen** gäller på servervägen, före ditt första val i körningen: läget, strömmen, partnerns kontext, följvyn
  och kodvyn bär inga bedömningar, skäl eller sökvägar i sessionernas aktivitet, körningsloggens text visas inte,
  DESIGN.md döljs och bara kandidatens aktuella version kan väljas och jämföras (föreversionen före en förbättringsrunda
  och diffen mot den visas efter valet, som i vyn Prototyp). En kund som är en arm i en blind jämförelse som du inte
  valt i än visas inte alls: läget, strömmen, partnerns kontext, modden, koden, loggarna och ändringen är stängda tills
  du valt i Jämförelser, och om jämförelsen inte går att pröva räknas den som oavgjord. En ändring som du skickar är
  ditt val av kandidaten; vyn säger det innan du skickar.
- **Kvarstående:** dashboardnyckeln ligger, som förut, i adressens fragment när `dashboard.sh` öppnar sidan och i
  webbläsarens lagring på dashboardens ursprung. Andra processer som samma användare kör kan läsa filerna och
  läs-API:t direkt; ingen isolering finns mellan ägarens egna processer. En mod körs utan sandlåda med användarens
  rättigheter.

## Claude-panelen

`mod/nortropic-arbetsyta`: en rad ovanför prompten (kund, moment, utförande, granskning, när det lästes; andra moddars
rader står kvar under den) och panelen
`/nortropic` (rollerna, nästa handling, länken Öppna arbetsytan). Den läser dashboardens `GET /api/arbetsyta` på
`http://localhost:<NWP_DASHBOARD_PORT, 4771>` var femtonde sekund, kunden ur `NWP_ARBETSYTA_KUND` eller den senast
aktiva, och visar en avisering bara när körningen börjar vänta på ditt beslut eller en session avbryts. Den ser inte
motorns processer själv, skriver inget, godkänner inget, skriver inte om prompter och anropar ingen modell
(`claude plugin validate` listar dess krokar och anrop).

Kräver Claude Code 2.1.287 i terminalen eller 2.1.286 i Desktop (mods-dokumentationen); validerad och prövad med
`claude plugin test` i 2.1.290, och laddad i en verklig `claude -p --plugin-dir` där den hämtade läget från dashboarden.
Ladda den med `claude --plugin-dir <repo>/mod/nortropic-arbetsyta`. Mods API:t är i tidig åtkomst: kör `claude plugin
validate` och `claude plugin test` på modden efter varje uppdatering av Claude Code. Ingen förhandsvisning kan bäddas in
i Claude Code (ingen webbvy bland elementen); länken öppnar arbetsytan i webbläsaren, utan nyckel i adressen, så
skrivningar kräver att dashboarden öppnats en gång via `./dashboard.sh`.

## Prov

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_arbetsyta.py` | läsvägen, sessionernas lägen, blindningen, koden och sökvägarna, ändringarna, partnern med en attrapp i stället för claude, HTTP-gränserna | i rökprovet |
| `kontroller/rokprov/revision/prov_arbetsyta_webb.mjs` | vyerna med syntetiska svar: bredder, axe, tangentbord, start-id, stopp i två steg, återanslutning och lucka, reducerad rörelse | i rökprovet |
| `mod/nortropic-arbetsyta/tests/` | modden på terminal och Desktop, en dashboard som inte svarar | `claude plugin test mod/nortropic-arbetsyta` |
| `kontroller/rokprov/revision/prov_arbetsyta_verklig_webb.mjs` | verkliga sessioner (Opus 5.5 på low, Haiku) i testprojektet genom motorns sessionsväg, i webbläsaren: att de dyker upp, följs, lämnar resultat, syns efter omladdning och stoppas | för hand, mot en dashboard ur en worktree; kostar modellanrop |

Testprojektet (`arbetsyta_fixtur.py`, `testdata-provverkstaden`) är en fiktiv verksamhet med en riktig byggd sajt ur
mallen; det skapas aldrig i huvudutcheckningen. En dashboard ur en worktree eller kopia (`NWP_DASHBOARD_NYCKEL=<nyckel>
.venv/bin/python -B dashboard/server.py --port <annan port>`) skriver sin nyckel i `kunder/.dashboard-nyckel` och har
spanarens och underhållets timklocka av; i huvudutcheckningen gäller hemlighetsmappen och klockan som förut
(`--nyckelfil`, `--klockor pa|av` ändrar det).

**Vad det verkliga provet visar och inte visar.** `prov_arbetsyta_verklig.py` ersätter ateljéns orkestrering i provet:
det skriver körningens status och startjournal som arbetaren gör, och kandidatens nya version som fotograferingen gör
(utan skärmbilder). Sessionerna, deras förteckningsposter, transkripten, observationen, förhandsvisningens bygge och
stoppvägen är motorns egna. Stoppet träffade därför den levande sessionen genom `atelje.stoppa`, men ingen riktig
arbetare: i en ateljékörning får arbetaren också signalen och skriver "avbruten vid stoppet". Provet säger inget om
designkvalitet eller om hur arbetsytan fungerar för en människa.

## Felsökning

- Inga sessioner syns: körningen startade före observationen, `NWP_OBSERVATION=av`, eller `claude --help` listade inte
  `--session-id` (samma skäl som i Prototypens observation). Helbyggets session syns när dess stream-json-logg har en
  init-rad.
- Anslutningen står på Återansluter: dashboarden svarar inte; arbetet påverkas inte. Läs läget igen med omladdning.
- Partnern svarar 409: en tur pågår eller sessionen är öppen i en terminal (`ps` visar en claude-process med sessionens id).
- Skicka ändring svarar Inaktuell: körningen eller kandidatens version har bytts; läs läget och skriv om ändringen.
- Panelen säger att dashboarden inte svarar: starta `./dashboard.sh`, eller sätt `NWP_DASHBOARD_PORT`.
