# Arbetsytan

Ägarens arbetsplats och dashboardens startvy: samtalet med Nortropic-partnern, meddelanden till och från sessionerna
som arbetar, kundens riktiga förhandsvisning, besluten, byggflödet och koden, för en kund i taget och över samma läge.
Varför den finns och hur huvudvägarna valdes: `BESLUT.md`, tilläggen 2026-10-09 om den visuella arbetsytan och om den
kompletta arbetsplatsen. Arbetet: `backlog/B-20261009-visuella-arbetsytan-samtal-preview-sessioner-och.md` och
`backlog/B-20261009-komplett-arbetsplats-samverkande-sessioner.md`.

## Starta och gå tillbaka

```sh
./dashboard.sh start [kund]         # tjänsten i bakgrunden om den inte kör, sedan arbetsytan; startar inget arbete
./dashboard.sh arbetsyta [kund]     # som förut: dashboarden i terminalen (Ctrl-C stoppar) och arbetsytan
./dashboard.sh genvag               # engångsinstallation: Mac-appen ~/Applications/Nortropic arbetsyta.app (anropar start)
```

Arbetsytan öppnas på dashboardens rot (`#/`); Översikten ligger på `#/oversikt`, och alla tidigare vyer finns under
Fler vyer och i menyn. Startgenvägen startar inga modellsessioner. Mac-appen kör `dashboard.sh start` genom
inloggningsskalet (`/bin/zsh -l`), så att claude och node hittas som i terminalen; ett dubbelklick startar en tjänst,
och den andra starten öppnar den körande med dess nyckel. Genvägen skapas från huvudutcheckningen, eftersom appen pekar
på den utcheckning där den skapades. Appens logg: `~/Library/Logs/nortropic-arbetsyta-app.log`. Dashboardens timklocka kör i huvudutcheckningen som
förut spanaren (ingen modell) och det dagliga underhållet, som en gång per dygn prövar verktygslådan med en kort
kontrollsession (tre turer; `kontroller/underhall.py`). Tjänstens logg i bakgrunden: `~/Library/Logs/nortropic-dashboard.log`.
Att gå tillbaka: Översikten och Flöde finns kvar, och en revert av arbetsytans commits lämnar motorn, domloggen och
bevisen orörda; meddelandebussen och löparen stängs av med `NWP_MEDDELANDEN=av` i arbetarens miljö (sessionerna körs
då exakt som före 2026-10-09).

Claude-panelen i Claude Code: `claude --plugin-dir mod/nortropic-arbetsyta`, och `/nortropic` öppnar panelen.

## Vyerna

Tre vyer över samma läge och samma identiteter (kund, körning, kandidat och version, roll, sessions-id). Det som syns
direkt är läget, nästa handling och det som väntar på dig; resten ligger ett steg ned bakom etiketter som säger vad de
visar (successiv fördjupning, högst två nivåer).

- **Arbetsyta**: projekthuvudet (kund med testmärkning, körningen, kandidaten och versionen, momentet, anslutningen),
  till vänster **Samtal** med flikarna Partnern och Meddelanden (med antalet meddelanden som väntar på ditt beslut),
  huvudmaterialet i mitten och rollsessionerna till höger, med Kontroller, Senast observerat och Nästa beslut under
  materialet. Huvudmaterialet: Förhandsvisning (arbetsversionen), Ögonblicksbild (den bevarade versionen, med
  beslutsraden när körningen väntar på dig), Jämför, Kandidater och Underlag. Panelerna fälls ihop och dras i bredd;
  under 900 px visas ett område i taget (Samtal, Resultat, Sessioner).
- **Byggflöde**: kundens nio observerade steg, sessionerna per moment och kandidat med detaljvy, Sessionsflödet och
  helbyggets körningar; bevakningen och systemförbättringen i en egen del, skild från kundproduktionen: bevakningens
  läge (aktiv först efter en schemalagd körning; senaste och nästa körning i Europe/Stockholm), dagens besked och nya
  fynd med belägg, kontroller som inte lyckades, täckningen per område med luckorna, förbättringsloopens steg och det
  som väntar på ditt beslut (`GET /api/bevakning`, `kontroller/bevakning.py`; registret: `kunskap/spaning-kallor.md`,
  Bevakningsfrågor), och länkarna till Kirurgen, backloggen, kalibreringen och rapporterna.
- **Kod och preview**: kandidatens filer, diff mot en namngiven bevarad version, Markera för en ändring, förhandsvisningen,
  körningsloggen och sessionens aktivitet. Kod redigeras inte i webbläsaren: en ändring är en ändringsinstruktion till
  utföraren eller ditt beslut (se Meddelanden och Beslut), aldrig en andra skrivare i kandidatens filer. Öppna i editorn
  finns kvar men behövs inte i det vanliga arbetet.

Versionerna, var för sig: **arbetsversionen** är det levande bygget i `dist/` och kan ändras medan arbetet pågår;
**ögonblicksbilden** är den fotograferade versionen (`versioner/<v12>/`, med bild, version och tid); den **godkända**
versionen är den bevarade version och bild som ditt godkännande binds till (`VINNARE.json`, `atelje.godkannande`);
**exporten** är kundrepots commit. Mobil och Dator ändrar bredden, inte versionen.

## Läget (kontraktet `arbetsyta/1`)

`dashboard/arbetsyta.py` `lage(slug)` samlar läget ur det som redan finns (`flode()`, ateljéns `STATUS.json`,
`kandidater.sammanstall`, observatörens förteckning och transkript, startjournalen, helbygget, domloggen, partnern,
meddelandebussen och löparnas lägen). Inget i läget är en egen status: det räknas fram vid läsningen, och en del som
inte går att läsa står i `ofullstandig` med skälet. Läsningen startar inget och gör inga modellanrop.

Varje session bär kund, körning, kandidat, roll, ansvar, sessions-id, förälder och ett av åtta lägen; liv avgörs av
processen, aldrig av hur nyligen något hände:

| Läge | Betyder |
|---|---|
| väntar på start (`vantar`) | ansvaret har ingen session i körningen |
| start pågår (`startar`) | processen lever men transkriptet syns inte än |
| arbetar (`aktiv`) | processen lever |
| väntar på verktyg (`verktyg`) | processen lever och senaste verktygsanropet har inget svar än |
| väntar på ditt beslut (`beslut`) | körningen är klar för din bedömning och inget utförande lever |
| avslutad (`avslutad`) | kod 0 och inget fel i svarsfilen; ett avslut är inget godkännande |
| avbruten (`avbruten`) | stopp, tidsgräns, signal, annan slutkod, `is_error`, eller en process som inte lever utan observerat slut |
| okänt läge (`okant`) | pid saknas eller tillhör en annan process |

Dessutom per session: `styrning` (löparens läge: om sessionen går att nå med meddelanden och pausa, paus begärd eller
pausad, verktyg som fortfarande arbetar) och `kompetens` i fyra nivåer (se Kompetensen). Läget bär också `samverkan`
(bussens antal, öppna meddelanden till dig, projektets paus) och bildernas sha256 för besluten.

Ansvaren: **arbetsledning** är partnersamtalet; **utförande** är research, plan, skaparna, förfiningen och helbygget;
**granskning** är kritikerna, panelen, jämförelsen och planprövningen.

**Strömmen** (`GET /api/arbetsyta/<slug>/strom`): en signatur över källorna prövas varje sekund (statusfiler,
förteckningar, transkript, processernas liv, bussens meddelanden, löparnas lägen, pauserna och mandaten) och hela läget
skickas när något ändrats. En ny anslutning får hela läget först; en stängd flik avslutar bara strömmen, aldrig arbetet,
och en återöppnad flik visar det faktiska läget. Högst tolv strömmar, var och en i högst 30 minuter.

## Meddelanden (bussen)

`kontroller/meddelanden.py` är den enda huvudvägen för meddelanden mellan dig, motorns sessioner och externa
granskare; `dashboard/samverkan.py` är dashboardens del och `kontroller/lopare.py` leveransen till sessionerna.

- **Avsändaren** sätts av den kod som tar emot meddelandet, aldrig av texten: dashboarden med din nyckel (du), löparen
  som äger sessionens stdin (sessionen, med roll och kandidat ur förteckningen) eller granskarnyckeln (en extern
  granskare). En agent som skriver "jag är ägaren" är fortfarande sessionen.
- **Syftet**: fråga, förslag, granskningsfynd, ändringsinstruktion, ägarbeslut och svar. Ett ägarbeslut skrivs bara av
  beslutstjänsten när du fattat beslutet. En ändringsinstruktion kommer från dig eller från en granskare inom ditt
  mandat, märkt som granskarens. Ett granskningsfynd kommer från en granskande session eller en extern granskare och
  har belägg (bild, del, mått, version). Ett svar går bara till den som frågade, och en agent besvarar inte ett svar.
- **Mottagaren**: en session som arbetar och tar emot meddelanden, kandidatens utförare (sessionen som arbetar med
  kandidaten nu eller härnäst), dig eller en extern granskare. En session som slutat nekas; skriv till kandidatens
  utförare i stället. Varje meddelande bär projekt, körning och, när det gäller en kandidat, kandidat och hel
  version. En ändringsinstruktion utan den version du såg nekas; en annan körning eller en nyare version svarar
  Inaktuell (409), och inget vidarebefordras blint.
- **Leveranslägen**, med tid och belägg: sparat (registrerat i bussen), köat (en löpare har tagit det för sin session),
  levererat (skrivet till sessionens inmatning), mottaget (Claude Code ekade meddelandet med dess id,
  `--replay-user-messages`), besvarat (mottagaren kvitterade meddelandet i
  turen efter ekot; turens text står som underlag) och, för en ändringsinstruktion, genomfört: bara när mottagaren
  kvitterat den och kandidatens fotograferade version ändrats efter mottagandet; annars står genomförandet som påstått
  eller okänt. En fråga, ett fynd eller en instruktion som turen inte kvitterade blir okänt, med turens text; ett
  förslag eller svar stannar på mottaget. Okänt också när sessionen slutade utan belägg för ett svar; köat igen när en
  paus lade tillbaka det; inte levererat när sessionen det gällde slutade innan det togs, eller när kandidaten fått en
  nyare version än meddelandet gäller (prövas vid leveransen). Ett skickat meddelande är inget bevis för att något är
  utfört. En omsändning efter okänt eller inte levererat blir ett nytt meddelande, kopplat till det förra.
- **Idempotens**: ditt meddelandes id är en hash av mottagaren, syftet, texten, kandidaten, versionen och körningen;
  ett dubbelklick, ett omförsök efter ett tappat svar eller en andra flik blir samma meddelande, och samma id med en
  annan text nekas. En agents id är en hash av avsändaren och innehållet. Löparen tar ett meddelande under kundens lås,
  så två sessioner med samma adress får aldrig samma meddelande.
- **Dina beslut över agenternas förslag och fynd**: Godta (blir din ändringsinstruktion till kandidatens utförare, med
  dig som avsändare och förslaget som underlag), Diskutera (din fråga tillbaka till avsändaren) eller Avvisa.
- **Rundgång** hålls borta med regler: högst `NWP_MEDDELANDEN_PER_AGENT` (6) meddelanden per agent och körning och
  `NWP_MEDDELANDEN_PER_EXTERN` (30) per extern granskare, samma text två gånger blir samma meddelande, inget svar på ett
  svar, och sessionernas egna uppgifter, gränser och avslut är motorns som förut.
- **Kanalerna**: varje session med löpare har en kanal (`meddelanden.kanal`). **Öppen** tar emot och lämnar
  meddelanden. **Ut** gäller en session med strukturerat svar (kritiken, panelen): den lämnar fynd men tar inga, så att
  dess svar alltid är uppgiftens. **Stängd** gäller blinda sessioner och de oberoende bedömarna (domarna,
  planprövningen, jämförelsen): utanför bussen åt båda håll, med varken protokoll eller meddelanden; de kan bara pausas
  och stoppas. Ingen session får sitt eget meddelande.
- **Blindningen**: före ditt första val i körningen visas inte agenternas text, belägg, svar och kvitton, inte heller
  deras syfte och kandidat eller rollerna (bara ansvaret), och historik, följdfrågor och beslut över agenternas förslag
  öppnas efter valet. En arm i en blind jämförelse visar ingenting.

**Hur ett meddelande når en arbetare.** Motorns sessioner startas genom `atelje.session`; när bussen är på och
`claude --help` listar `--input-format` och `--replay-user-messages` (samma fråga som observationens) körs sessionen i
strömmande läge (`--input-format stream-json --output-format stream-json --verbose --replay-user-messages`) genom
löparen, med samma verktyg, regler, skills, MCP:er, kundvakt och svarsfil som förut. Uppgiften går in som första
meddelandet; ditt meddelande går in med `origin: human` och andras med `origin: peer` och en ram som säger avsändaren
(`meddelanden.ramtext`), där andras text står citerad rad för rad med `> `, så att en förfalskad rubrik aldrig står
först på en rad. Varje meddelande går in för sig med sitt eget ursprung. Claude Code läser meddelandet mellan
verktygsanropen i samma tur (prövat 2026-10-09). `crossSessionInbound: refuse` i sessionens inställningar gör bussen
till sessionens enda väg in: ingen annan session når den med SendMessage, och bussens katalog
(`underlag/<kund>/arbetsyta/`) är nekad för sessionernas Read, Edit och Write. Sessionens egna meddelandeblock
(`` ```meddelande {...}``` ``, protokollet för kanalen i systemprompten, `lopare.protokoll`) registreras i bussen med
sessionen som avsändare; ett block som bryter mot reglerna står bland löparens avvisade. När en tur slutar utan något
att leverera, utan paus och utan meddelanden som skrivits men inte ekats stängs stdin och processen avslutas som en
vanlig `claude -p` (ekas ett skrivet meddelande inte inom `NWP_EKO_TAK` sekunder utan händelser, 15, stängs den ändå
och meddelandet blir okänt). Svarsfilen är uppgiftens: resultatet av den senaste turen som bar uppgiften eller en
återupptagning, i samma form som förut, med sessionens sammanlagda turer och listpris; en tur som bara bar meddelanden
ersätter den aldrig. `--max-turns` gäller varje tur, och löparen levererar inget mer när sessionens turer sammanlagt
nått motorns tak; fristen räknar aktiv tid.

Agent Teams används inte: det är experimentellt och startar inga lagkamrater i `-p`. Agent View (`--bg`) går inte ihop
med `-p` och är inte motorns sessionsmodell. Claudes egna meddelanden mellan sessioner (SendMessage) är stängda för
motorns sessioner, så att samma instruktion aldrig går två vägar.

## Följa, meddela, pausa, stoppa och återuppta

| Handling | Var | Vad den gör | Vad den inte gör |
|---|---|---|---|
| **Följ** | sessionens kort | sessionens observerade händelser ur transkriptet | skickar inget |
| **Skriv** | sessionens kort, Meddelanden | en fråga eller ändringsinstruktion till sessionen som arbetar, eller till kandidatens utförare | ändrar inget själv; utföraren gör det i sin session |
| **Historik** | sessionens kort (efter ditt första val) | sessionens samtal ur transkriptet, maskerat och avkortat, med verktygens namn | visar inga verktygssvar |
| **Fortsätta arbetet** | Meddelanden, Kontroller | en ändringsinstruktion till kandidatens utförare (sessionen som arbetar med kandidaten nu eller härnäst) och Förfina under Kontroller: motorns egen förfiningssession med dess behörigheter genomför den | ingen förgrening skriver i kandidatens filer, och två aktörer skriver aldrig samtidigt |
| **Följdfråga** | Historik, för en avslutad session | en förgrening (`--resume <id> --fork-session`) med eget id, registrerad med föräldern och ansvaret, som bara läser (Read, Glob, Grep; dontAsk) i en egen tom katalog | förgrenar aldrig en session som arbetar; föräldern får aldrig en andra process |
| **Pausa** | sessionens kort (en session), Kontroller (körningen) | se Paus och återupptagning | återställer inga filändringar eller externa handlingar |
| **Återuppta** | samma ställen | fortsätter samma process från känt läge med det som kom under pausen | startar inget nytt |
| **Stoppa** | Kontroller, två steg | flödets stoppväg (`prototyp.py --stoppa`): arbetaren och dess sessioner med processträd | det som är klart bevaras |
| **Återuppta arbetet** | Kontroller | `--fortsatt` genom samma ingång | gör inget klart om |
| **Partnern** | Samtal → Partnern | en tur i partnerns egen session (se Partnern) | ändrar inget, startar inget |

Start, förfining, stopp och export går genom `POST /api/flode/<slug>/start` med samma start-id som Flöde
(`nwp-start:<kund>:<handling>`): ett dubbelklick skickar en begäran, ett tappat svar försöks igen med samma id, och en
andra flik nekas av servern.

## Paus och återupptagning

- **En session**: löparen skickar ett avbrott (`control_request` `interrupt` med `cancel_queued`); turen och verktygen
  som kör stoppas, och meddelanden som var köade i processen läggs tillbaka i bussen. Läget är **paus begärd** tills
  turens resultat kommit; då **pausad**, med de processer under sessionen som ändå lever (redovisas, inte avslutade).
  Under pausen hålls stdin öppen, inget levereras och fristen står still; högst `NWP_PAUS_TAK` sekunder (sex timmar),
  sedan stoppas sessionen. Resten av körningen fortsätter.
- **Hela körningen**: ingen ny session startar och varje levande session pausas som ovan. Spärren gäller före varje
  modellsession för kunden: i `atelje.session` (också utan löpare och med bussen av) och före Referos och Mobbins
  tjänstesessioner (`referenstjanster.kor_session`). Vyn säger hur många starter som väntar. Pausad först när inga
  sessioner arbetar och ingen claude-process under arbetaren lever utanför en pausad löpare; arbetarens egna steg
  utanför sessionerna (ett bygge, en fotografering) redovisas men avbryts inte. En paus från en tidigare körning
  gäller inte, och stoppet tar bort kundens pauser när arbetet har stannat.
- **Tiden**: sessionens frist står still under pausen, och skissförsökets budget räknar bort pausen
  (`atelje.pausad_tid`, `kandidater.gatt`). Övriga steg i motorn räknar pausen som vanlig tid. Vyn visar när en pausad
  session når taket och stoppas.
- **Återupptagning**: ett eget meddelande från dig med uppmaningen att slutföra den ursprungliga uppgiften utan att
  vänta, och därefter det som köats eller kommit under pausen, var för sig med sitt eget ursprung (meddelandet med
  uppmaningen prövat med en verklig session 2026-10-09: den kvitterade meddelandena, körde om kommandot som avbrutits och
  slutförde uppgiften). Har sessionen nått motorns turtak slutar den i stället. Filändringar före pausen står kvar; en
  paus återställer ingenting.
- En stängd flik pausar eller stoppar ingenting. Löparen bor i arbetarens process, inte i webbläsaren eller dashboarden.

## Mandat och extern granskare

**Mandatet** (Meddelanden → Mandat för granskare): du ger en granskare (motorns granskare, en bestämd session eller en
extern granskare) rätt att lämna de åtgärder du kryssar i (förslag, granskningsfynd, begäran om rättelse) till en
kandidats utförare, i den körning du ser och inom en omfattning du skriver. Åtgärderna anges alltid uttryckligen; ett
äldre mandat utan dem gäller bara begäran om rättelse, och ett mandat från en annan körning gäller aldrig. Utföraren hanterar dem inom sitt eget uppdrag; ramen säger
mandatet och omfattningen, och omfattningen prövas inte maskinellt. Utan mandat går en granskares fynd och förslag
till dig. Ett mandat återkallas när som helst; det gäller inte i nästa körning.

**Extern granskare (Codex).** Inkopplat och prövat mot den riktiga hanteraren: dashboardens externa väg
(`/api/extern/<kund>/underlag|bild|fynd|aterkoppling`) med en egen granskarnyckel (`Authorization: Bearer`, filen
`~/.nortropic-hemligheter/webb-pro/granskare/<namn>.nyckel`, 0600); avsändaren är nyckelns namn. Vägen tar inga anrop
från en webbläsare (`Origin` eller `Sec-Fetch-Site` ger 403), ger bara kandidaterna med neutrala etiketter, versionerna,
bilderna och granskarens egna mandat (aldrig kandidaternas status eller dina val), och tar emot fynd, förslag, frågor,
svar och, med mandat, poster till utföraren. En nyckelfil som andra än du kan läsa gäller inte. Återkopplingen ger
dina egna meddelanden och svar, maskerade, och leveransläget och ditt beslut för granskarens poster; andra sessioners
text lämnas aldrig ut.
`kontroller/extern_granskare.py` gör nyckeln, granskningspaketet (AGENTS.md, `fynd-schema.json`, underlaget och
bilderna, ingen nyckel och ingen `.codex/`) och postningen. Granskaren skriver aldrig i skaparens filer och når aldrig
dashboarden själv.

Codex kör `exec` skrivskyddat och utan nät som standard (Codex dokumentation, non-interactive mode och sandboxing), så
det läser paketet och lämnar fynden i en fil som skriptet postar. Prövat 2026-10-09 med den riktiga Codex i en
provinstans med fiktiva testdata: posterna registrerades till dig och till kandidatens utförare med rätt avsändare och
körning (privat rapport `RAPPORT-2026-10-09-codex-observation-h01`). Inte prövat: leveransen av en Codex-post in i en
arbetande session och vägen i huvudutcheckningens dashboard.

```sh
kontroller/extern_granskare.py nyckel codex                       # en gång
kontroller/extern_granskare.py paket codex <kund> /tmp/granska-<kund>
codex exec --ignore-user-config -s read-only -C /tmp/granska-<kund> --output-schema /tmp/granska-<kund>/fynd-schema.json \
    -o /tmp/granska-<kund>/fynd.json "Granska kandidaterna enligt AGENTS.md och svara enligt schemat."
kontroller/extern_granskare.py posta codex <kund> /tmp/granska-<kund>/fynd.json
kontroller/extern_granskare.py aterkoppling codex <kund>          # svaren och dina beslut över fynden
```

Claude Mods omfattar inte Codex; integrationen är den här vägen och inget annat.

## Beslut och godkännande

Besluten (Välj vidare, Godkänn denna version, Underkänn alla, Ny riktning) fattas under den bevarade bilden
(Ögonblicksbild eller Jämför; aldrig under arbetsversionens förhandsvisning) och går genom samma tjänst och samma skydd
som vyn Prototyp: `server.spara_kandidatbeslut` → `atelje.doma` → `kandidater.prova_beslut` och, för ett godkännande,
`forbered_vinnare`, som nekar om kandidatens filer ändrats sedan den fotograferade versionen. Arbetsytan binder
dessutom beslutet till det du såg när du öppnade det: versionen och bildens väg och sha256 tas vid klicket och skickas
med. Servern nekar ett godkännande (Inaktuell) när versionen inte längre är kandidatens eller bilden har ändrats, och
när bilden inte är kandidatens ögonblicksbild; beslutet står i domloggen under `arbetsyta.sedd`. En ögonblicksbild
vars sida inte svarade 200 med HTML (en fotograferad felsida, `forhandsvisa.ogiltig_sida` ur fotograferingens
INSPEKTION.json) går inte att välja eller godkänna; en sida som svarar 200 men visar ett fel upptäcks inte av den
kontrollen. Ett godkännande lämnar över till helbygget men startar det inte. Ett ägarbeslut speglas i
bussen som en rad med syftet ägarbeslut och domens tid.

**Jämför** visar den valda kandidatens bevarade bild bredvid en annan kandidats eller en tidigare bevarad version
(efter ditt första val), i samma bredd; referensen sida vid sida finns i Prototyp. Kodens diff mot en bevarad version
finns under Kod och preview.

## Partnern (arbetsledningen)

`dashboard/partner.py`. En riktig Claude Code-session: första meddelandet `claude -p --session-id <id>`, senare
`--resume <id>`; ett meddelande i taget, och en interaktiv `claude --resume` på samma id gör att nästa meddelande nekas.

- **Bunden till körningen och blindläget**: en sparad session återupptas bara i samma körning, och i ett blint läge bara
  om den startades blind; annars arkiveras den orörd under `tidigare` och nästa meddelande startar en ny session. En ny
  blind körning ärver alltså aldrig ett samtal där tidigare bedömningar eller försöksarmar kan stå (att dölja det senaste
  meddelandet rensar inte sessionens minne). Det tidigare samtalet visas först när läget inte är blint. En arm i en blind
  jämförelse ger varken samtal eller tur (409), på partnerns egna vägar som på läsvägen.
- **Arbetskatalog och läsrätt:** en egen tom katalog, Read med dontAsk och en tillåtelselista (repots `README.md`,
  `CLAUDE.md`, `BESLUT.md`, `kunskap/`, `kritik/`, `backlog/` och kundens underlag); dontAsk nekar inte läsningar inom
  arbetskatalogen, därför är den tom. Inga MCP:er, inget Bash, inget Write.
- **Läget i varje meddelande:** arbetsytans läge ur samma läsväg som vyn, blindat, och din markering.
- **Överlämning:** ett `overlamning`-block blir ett förslag i vyn; du skickar själv. Partnerns svar blir aldrig ett beslut.
- **Lagring (privat):** `underlag/<kund>/arbetsyta/PARTNER.json` och svarsfilerna i `partner/`. Frist per tur
  `NWP_PARTNER_FRIST` (600 s).

## Modellprofilen och kompetensen

Arbetsledningen kör `claude-fable-5-1` på medium (`NWP_PARTNER_MODELL`, `NWP_PARTNER_EFFORT`), en hypotes som inte är
prövad mot alternativ. Utförandet och granskningen följer motorns standarder (`NWP_ATELJE_MODELL`,
`NWP_KANDIDAT_GRANSKARE`). Användningen står som Claude Codes rapporterade tokens och listpris, inte fakturerad
kostnad: prenumerationen räknar kvot. Sessionerna körs lokalt genom Claude Code och prenumerationen som förut; inget
i bussen eller löparen byter till API-drift.

**Kompetensen i fyra nivåer**, var för sig i sessionskortet: **erbjuden** (skills i sessionens lista och MCP-servrarnas
anslutning, ur transkriptet), **laddad** (skills aktiverade med skillverktyget och lästa skillfiler), **anropad**
(MCP- och skillanrop) och **påverkan**, som inte syns i en session: den bedöms i kandidatens kompetenskvitto och
granskning. Löparen sparar dessutom init-händelsens förteckning (verktyg, skills, MCP-servrar med status, förmågor)
som belägg för att den nya startvägen laddar samma kompetens.

## Observationen och dess gräns

Följvyn läser observatörens läsläge och lagrar inget nytt: verktygets namn, tid, utfall, sökvägen för Read och de
skrivande verktygen och skillens namn; aldrig promptar, övriga argument, svar eller skrivet innehåll. Historiken visar
sessionens egna texter och de meddelanden den fått, maskerade (`arbetsyta.maskera`) och avkortade, efter ditt första
val. Löparens läge (`underlag/<kund>/arbetsyta/styrning/<id>.json`) bär inga promptar eller verktygssvar. Underagenters
egna anrop syns inte.

## Säkerhet och åtkomstgränser

- **Skrivningar** (meddelanden, beslut, mandat, paus, följdfrågor, partnern, starter och stopp) kräver dashboardnyckeln
  och samma ursprung. **Läsningar** är öppna för andra processer som samma användare kör, som förut.
- **Den externa granskaren** har en egen nyckel per namn, ingen webbläsare och bara sina vägar; den kan inte ge sig
  själv mandat, besluta eller nå kandidatens filer.
- **Strömmen** nekas från ett annat ursprung; **förhandsvisningen** körs på en egen port i en sandlådad iframe; sidan
  ramas aldrig in (`X-Frame-Options: DENY`, `frame-ancestors 'none'`).
- **Kod-, logg- och historikvyerna** visar bara text ur kandidatens kod, loggarna och sessionernas transkript, maskerat;
  en maskering är ett skyddsnät, inget löfte.
- **Blindningen** gäller på servervägen genom hela arbetsytan (läget, strömmen, partnern, bussen, historiken,
  följdfrågorna, besluten över förslag, koden och loggarna); se Meddelanden och Partnern.
- **Mods** kör med dina rättigheter utanför Bash-sandlådan; Claude-panelen läser bara och är ingen väg runt nyckeln,
  beslutstjänsten eller kundvakten.
- **Kvarstående:** dashboardnyckeln ligger som förut i adressens fragment när sidan öppnas och i webbläsarens lagring.

## Claude-panelen

`mod/nortropic-arbetsyta`: en rad ovanför prompten (kund, moment, utförande, granskning, paus och meddelanden som
väntar på dig) och panelen `/nortropic`, ur dashboardens `GET /api/arbetsyta` på `http://localhost:<NWP_DASHBOARD_PORT,
4771>` var femtonde sekund, med en avisering när körningen väntar på ditt beslut, en session avbryts eller ett nytt
meddelande väntar på dig. Den startar inget, skickar inget och beslutar inget. Kräver Claude Code 2.1.287 i terminalen;
kör `claude plugin validate` och `claude plugin test` på modden efter varje uppdatering. Bildstöd i en mod (kitty-grafik,
till exempel i Ghostty) är ingen interaktiv webbläsare och behövs inte: arbetsytan fungerar fullt utan den.

## Prov

| Prov | Vad | Hur |
|---|---|---|
| `kontroller/rokprov/revision/prov_arbetsyta.py` | läsvägen, sessionernas lägen, blindningen (också partnerns A/B-spärr och sessionsbindning), koden, ändringarna, partnern, bussens HTTP-vägar, den externa granskaren och dess kommandoradsverktyg, mandatet, pausen, historiken och följdfrågan, beslutet bundet till bilden | i rökprovet |
| `kontroller/rokprov/revision/prov_meddelanden.py` | bussen och löparen med en falsk strömmande claude: leveranslägena, origin, avsändaren, mandatet, paus och återupptagning, projektets paus, blinda sessioner, inaktuella versioner, okänt, turtaket; klassen Granskning prövar fynden i GR-20261009-arbetsplats-oberoende (svarsfilen, kanalerna, pausens spärr och kvitton, förfalskade rubriker, mandatet, kvittot för besvarat, versionen vid leveransen, omsändning, bussens katalog, sena avbrottskvitton) | i rökprovet |
| `kontroller/rokprov/revision/prov_arbetsyta_webb.mjs` | vyerna med syntetiska svar: bredder, axe, tangentbord, start-id, stopp, återanslutning, menyn | i rökprovet |
| `mod/nortropic-arbetsyta/tests/` | modden | `claude plugin test mod/nortropic-arbetsyta` |
| `kontroller/rokprov/revision/prov_arbetsplats_verklig.mjs` | användarresan med verkliga sessioner i en provinstans med fiktivt material (se nedan) | för hand; kostar modellanrop |

**Provinstansen**: en dashboard ur en worktree (`NWP_DASHBOARD_NYCKEL=<nyckel> .venv/bin/python -B dashboard/server.py
--port <annan port>`) skriver sin nyckel i worktreens `kunder/.dashboard-nyckel` och har timklockan av; testprojektet
skapas med `arbetsyta_fixtur.py <worktree> --slug <testdata-…>`, aldrig i huvudutcheckningen. Modellerna styrs med
`NWP_ATELJE_MODELL`, `NWP_ATELJE_EFFORT` och `NWP_KANDIDAT_GRANSKARE` i dashboardens miljö, som arbetaren ärver.

## Felsökning

- Inga sessioner syns: körningen startade före observationen, `NWP_OBSERVATION=av`, eller `claude --help` listade inte
  `--session-id`.
- En session har ingen Skriv eller Pausa: den startades utan löpare (bussen av, en claude utan strömflaggorna, eller
  före 2026-10-09), den är blind, eller den arbetar inte längre. Stoppa finns alltid.
- Ett meddelande står kvar som sparat: ingen session med den adressen arbetar; det levereras till nästa session för
  kandidaten, eller när mottagaren är du, väntar det på ditt beslut.
- Ett meddelande står som okänt: sessionen slutade utan ett resultat efter ekot, eller turen kvitterade det inte; turens
  text står vid meddelandet. Skicka det igen (ett nytt meddelande) eller fråga i historiken.
- Inaktuell (409): körningen eller kandidatens version har bytts sedan läget lästes; läs om och skriv om.
- Partnern svarar 409: en tur pågår, sessionen är öppen i en terminal, eller kunden är en dold arm.
- Panelen säger att dashboarden inte svarar: `./dashboard.sh start`, eller sätt `NWP_DASHBOARD_PORT`.
