# Kundstart — lokal ärendehantering och överlämning

## Från överlämning till ett aktuellt bygge

`kundstart_kalla.py` prövar den levande källan före förberedelse, start och publicering samt när ett
designgodkännande eller slutbesked används. En senare kundrättelse gör den gamla överlämningen inaktuell även om
dess filer är oförändrade. En borttagen KUNDSTART-markör blir inte ett manuellt underlag när ett ärende med sluggens
identitet finns. Filmanifestet måste täcka hela överlämningen; tomma, trasiga och förkortade manifest godkänns inte.

Det befintliga lagringslåset hålls bara under kontroll och kort publicering, aldrig under modellarbete. Låset släpps
också vid oväntade undantag. Källkontrollen öppnar inte en ny databas och använder inte `immutable`, som skulle
kunna missa aktuella WAL-data. Lagrets nuvarande rollback-format stöds; WAL eller kvarvarande journalfiler ger ett
tydligt stopp utan att kontrollen skapar sidofiler. En framtida WAL-övergång behöver eget samtidighetsprov.
Det följer av [SQLite-filformatets läs-/skrivversion](https://www.sqlite.org/fileformat.html) och
[WAL:s krav vid läsande öppning](https://www.sqlite.org/wal.html), kontrollerade 2026-10-08.

Det gemensamma ärendelagret är förbjudet för sessionens filverktyg och processgränsens barn. Helbygge med ett
befintligt ärendelager kräver `NWP_SANDLADA=pa`; enbart Read-regler skyddar inte mot egna skript. Den överlämnade
kundens snapshot går fortfarande att läsa. Lokala prov av argument, tidig vägran och `sandbox-exec` visar denna
mekanik; verklig Claude Code-tillämpning ska verifieras innan skarp aktivering.

Ett sammanhängande syntetiskt förlopp ingår i skisskritikens prov: Kundstart, förberedelse, skiss, stopp och nytt
försök, ny kritik, val, förfining, startsidesgodkännande, helbyggkedjans slutkod och intern export. Testbeslut finns
bara i egna kopior. Modellsvar, rendering och bilder är dubblar; provet bevisar inte design- eller intervjukvalitet.
Fem flertursfall täcker service, bokning, beställning, migrering och liten ändring. De prövar källstatus och
versionsbindning genom verkligt ärendelager, inte en autonom intervjuares förmåga eller verkliga användares beteende.

**Status:** implementerad på arbetsgren, inte driftsatt som publik kundtjänst. Inga verkliga kunddialoger,
AI-anrop eller obevakade arbetare har aktiverats genom detta utvecklingsuppdrag. Kirurgens förbättringsloop
är en separat del av samma uppdrag; denna text beskriver inte den som färdig.

## Var delarna körs

| Del | Faktisk väg | Tillit och tillstånd |
|---|---|---|
| Kunden | `kundstart/`, server `kontroller/kundstart_server.py` på loopback | personlig ärendelänk, kontrollerad vid varje läsning och ändring |
| Ärendet | `kontroller/kundstart.py`, privat SQLite på beständig lokal disk | mottagna ord, uppgifter, källor, revisioner, roller, material, kö och operationer |
| AI | `kontroller/kundstart_modell.py` | en beständig lease åt gången per jobb; två uttryckliga transporter: server-API (skarp kunddrift) och pilotens nästlade Claude Code-session på det lokala abonnemanget (bara fiktiva ärenden), båda utan fria verktyg |
| Ägaren | befintliga dashboardens Kundstart-flik, `kontroller/kundstart_agare.py` | separata handlingar för erbjudande, personlig åtkomst, överlämning, komplettering och lagring |
| Webbflödet | `kontroller/kundstart_beredning.py` och `kontroller/kundstart_fortsatt.py` | fil- och källbundna kvitton, verkligt material, returfrågor och integrationsbelägg |
| Behörighet | `kontroller/kundstart_behorighet.py` | läsare, medverkande och beslutsfattare; återkallad länk nekas även vid omförsök |
| Lagring | `kontroller/kundstart_lagring.py` | explicit gallringsbeslut, avbrottstålig journal, kontrollerad backup och återställning till ny rot |
| Mått | `kontroller/kundstart_matt.py` | privata metadata per försök; ingen råprompt, nyckel eller antagen fakturakostnad |

Lokal SQLite passar den valda, beständiga maskinen; den flyttas inte oförändrad till en serverlös hosts tillfälliga
disk. Kundservern exponerar inte dashboardens administration, kundkataloger eller modellstart. Dashboarden är fortsatt
en lokal administrativ yta, inte en extern fleranvändarprodukt. Tjänsterna startar inte vid import.

## Start och prov

Från reporoten kan en behörig operatör uttryckligen starta kundservern:

```sh
.venv/bin/python kontroller/kundstart_server.py --port 4773
```

Kundstart-fliken i dashboarden skapar ärenden och personliga länkar. Den startar inte kundservern. Länken pekar i
första versionen på den lokala standardporten 4773. Ingen kundkontakt, publik adress eller tunnel ingår. Rånyckeln
visas en gång och skickas inte automatiskt. Tappas svaret kan ärendet återfinnas, men ny personlig åtkomst måste
skapas uttryckligen. Rånycklar förekommer inte i API-listningar, ärendebilder eller loggar.

AI är avstängd som standard. Kundärendets anropsbudget är 0 vid skapande i ägarvyn. Server-API är inte privat
Claude Code-abonnemang; modell, konto, kostnadsmandat och tillåten databehandling behöver verifieras före riktig
kundtrafik. Ingen nyckelfil läses. Vid uttryckligen tillåten aktivering används miljön NWP_KUNDSTART_API_KEY,
vid behov NWP_KUNDSTART_API_WORKSPACE och ett aktuellt modell-id. Följande kommando tar **ett** köjobb:

```sh
.venv/bin/python kontroller/kundstart_modell.py --modell MODELL_ID --live-api
```

**Piloten (ägarens beslut 2026-10-08):** intervjun går på det lokala Claude Code-abonnemanget, eftersom piloten inte riktar
sig mot faktiska kunder. `--live-cli` kör en nästlad session per köjobb (`ClaudeCLI`): samma metodtext och kontext som
server-API-vägen, en tur och svaret i ett JSON-schema (`--json-schema`), utan verktyg, MCP:er eller API-nycklar i miljön
(`nastlad.miljo`), i en registrerad tempkatalog så att varken repots CLAUDE.md, inställningar eller hookar laddas. Lagret
lämnar bara jobb för ärenden märkta fiktiva till den transporten (`ta_jobb(bara_fiktiva=True)`); ett verkligt ärendes jobb
stängs av utan lease och utan förbrukad budget, med beskedet att det kräver server-API.

```sh
.venv/bin/python kontroller/kundstart_modell.py --modell claude-sonnet-5-5 --live-cli [--effort medium] [--antal 1]
```

`--antal` tar högst så många köjobb i samma körning; ingen schemaläggare startas. Mätningen bokför begärd och observerad
modell, tokens ur sessionens `usage` och metodhashen; kostnaden står som inte observerad (listpris är inte abonnemangskvot).

Utan `--live-api` eller `--live-cli` sker inget nätanrop och jobbet får ett ärligt avstängningsbesked. Kommandot är ingen
aktiverad schemaläggare; stängd webbläsare kör inte modellen. Totaltak i ärendet och försökstak i kön består vid omförsök.
`kunskap/kundintervju.md` läses i sin helhet till metodstödet. Frågor och källkopplade förslag valideras av appen;
modellen kan inte acceptera en beställning eller ge design- och publiceringsmandat.

De lokala automatiska proven har syntetiska ärenden, egna registrerade kataloger, OS-valda portar och
transportdubblar. De finns som `prov_kundstart*.py` och `prov_kundstart*_webb.mjs` under
`kontroller/rokprov/revision/` och körs av `kontroller/rokprov.sh`. En dubbel bevisar mekanik, aldrig adaptiv AI,
kontots åtkomst, driftsättning eller mänsklig användbarhet. En provserver ersätter aldrig :4771.

## Ärendets kontrakt

Kundens meddelande sparas före AI-arbetet. Operations-id och revisionskontroll skyddar omförsök och samtidighet;
en gammal modelllease kan inte skriva över en senare rättelse. Kundens ord sparas separat från AI-förslagen.
Kunskapsstatus, beställningsstatus och genomförandeläge är separata. Ämnestäckning är ingen färdigprocent.

Kunden kan korrigera uppgifter, välja framtida eller bortvalt behov, beskriva funktioner utan API-kunskap och lämna
material utan att hävda läsning eller rättighet. Olika deltagares motstridiga uppgifter behåller konflikten tills en
beslutsfattare uttryckligen klarlägger den med skäl. Verksamhetsgrund stäms av separat från förfrågan och erbjudande.
En accepterad omfattning gäller bara sin sakliga version; samtalsmetadata är inte en ny beställning.

Kundens och ägarens utkast stannar i den aktuella webbläsarsessionen. De behåller sin grundrevision. En senare
serverrevision kräver synlig jämförelse, inte tyst omskrivning av utkastets grund. Sena ägarsvar binds till ärende
**och** vyinstans och kan inte visa en personlig länk under ett annat ärende. Begränsad startjournal bevarar tidigare
operations-id; vid fullt lagringsutrymme skickas ingen obekräftad ny start.

## Kvalificering och överlämning

Verksamhetsförslaget binds till aktuella kundkällor, inte till AI:s formuleringar. Bekräftelsen gäller förslaget och
kundgrunden. Överlämning skriver VERKSAMHET.json och KUNDSTART.json; UPPDRAG.md tillkommer bara för aktuellt accepterad
omfattning. Det är inte automatisk research, brief, text eller godkänd design. Dessa bereds i befintligt webbflöde.

Varje export reserveras före filändringar. Kvittot prövar exakt underlagsrot, aktuell ärendekälla och varje filhash.
Ett avbrott är publicerar, inte klar. Samma operation kan återupptas, eller återställas endast när de egna filerna
fortfarande är oförändrade; främmande ändringar skrivs inte över. Bygg- och ateljélåsen prövas före överföringen.

Kompletteringar återvänder till samma ärende med skäl, fas och den överlämning frågan uppstod ur. Ett mottaget svar
är inte automatiskt en löst kritisk fråga. Intern klarläggning binds till exakt svarsversion; ett nytt svar gör
bedömningen inaktuell. Kritiska modellfrågor redovisas som olöst prövning, aldrig som tyst ägarbeslut. Helbyggbesked
kräver aktuell överlämning, accepterad omfattning och befintligt giltigt designkontrakt. Byggstarten måste ändå
utföra sina egna kontroller. Publicering är en separat gräns.

Integrationsbehovets kundkälla, leverantörens dokumenterade förmåga, kontots åtkomst och genomfört prov hålls isär.
Leverantörsuppgiften innehåller källadress/datum/hash, men första versionen hämtar inte själv källans bytes för att
verifiera den angivna hashen. Konto- och provbesked kräver lokala bevis med verifierad filhash. Okänt är okänt;
produktens funktionslista blir inte kundens kontoåtkomst. Ingen teknisk rekommendation blir beställd automatiskt.

**Funktioner och anslutningar** (ägarens vy i ärendet; `kontroller/kundstart_integration.py`, uppdraget 2026-10-09):
ägaren väljer paket ur integrationskatalogen (`kontroller/integrationer/katalog.json`, områdena K01–K18) för kundens
behov. Valet sparas med katalogens och paketets version och, när det pekar på ett behov, behovets hash. Kundens läge
styr beställningen: ett val som pekar på ett behov får behovets läge, ett val utan behov är ett förslag, och bara
grundleveransens paket (hosting, formuläret och dess avisering; katalogens `grund`) ingår utan att kunden kryssar i
dem. Ändras behovet blir valet inaktuellt och står utanför planen tills ägaren väljer igen; historiken bevaras. Ett nytt
eller ändrat val är en materiell ändring av den accepterade omfattningen. Planen räknas fram ur valen utan modell
(`integrationskatalog.planera`) och visar beroenden, konflikter, utredningsvägar, okänd kostnad och de handlingar en
människa gör. Fyra dimensioner står var för sig: kundens läge, paketets färdighet, anslutningen (utredningens belägg)
och genomförandet. Valen är manuella; AI-förslag till valen finns inte än.

## Skydd och lagring

Privat lagring ligger under `underlag/kundstart/`: arenden.sqlite3, GALLRING.json, egna säkerhetskopior och begränsade
bevis. Härledd överlämning ligger under `underlag/<slug>/`, inklusive privata kopior i kundstart/overlamningar/.
Inget av detta förs till det publika repot. Personliga länkar har roller, utgång och återkallelse. Fragmentet tas bort
ur adressfältet efter inläsning; sidan laddar inga externa resurser. Bilagor hämtas som nedladdning, inte exekverad HTML.

Gallring kräver explicit ändamål, ansvarig och datum, inget påhittat generellt lagringsintervall. Journalen spärrar
åtkomst först, även om raderingen avbryts. Oförändrade ägda härledningar och kontrollerade säkerhetskopior rensas;
ändrade eller andra härledningar redovisas som kvar och ger ofullständig gallring. Externa kopior ligger utanför
mekaniken och måste hanteras separat. En backup är SQLite onlinebackup, inte kopiering av en öppen databasfil.
Återställning skapar en ny rot, tillämpar den aktuella gallringsjournalen och återkallar alla gamla länkar. Den
startar aldrig tjänster eller modelljobb. Integritets-, leverantörs- och rättsliga beslut för riktig kundtrafik återstår.

Nyckelfilter återanvänder commitvaktens mönster. Det är ingen garanti att godtyckliga känsliga uppgifter upptäcks.
Filer kan vara uppladdade men olästa; ingen automatisk extraktion eller allmän filanalys påstås. Kunder ska inte
lämna hemligheter, kortuppgifter eller onödigt känsliga personuppgifter i samtalet.

## Bevis och kvarstående driftfrågor

Lokala prov omfattar källstatus, roller, samtidighet, återupptagning, avbrott, material, överlämning, returfrågor,
lagring/återställning och faktiska webbläsarflöden. Försökens begärda/observerade modell, metodhash, svarstid, fel och
uppgivna tokenmått sparas separat; saknade värden är null, kostnaden okänd. Budgetens antal försök är inte en faktura.

Lease, budget och försöksrad bokförs i en transaktion. En utgången lease blir ett avbrutet försök när arbetaren
återtar kön; faktisk sluttid och varaktighet efter ett hårt avbrott är okända. En senare återkomst kan inte skriva
om detta till ett lyckat försök. Hashen gäller den exakt förberedda systemtexten. `transportlage=forberedd` är
inget sändningskvitto: processen kan dö mellan bokföring och anrop. `svar_mottaget` kräver att transporten svarat,
också när svaret är ett HTTP-fel. Tokenvärden kräver ett läsbart modellsvar och bevisar ingen intervjukvalitet.

Modelltransport och gallring delar ett separat ärendelås, taget före databaslåset. Gallring som vinner först
hindrar anropet; en redan påbörjad transport får avslutas innan gallringen blir klar. Kundens rättelser kan
fortfarande sparas under anropet. Ingen råtext eller nyckel ligger i transportlåsets kvarvarande tomma fil.

Äkta flerturs-AI, driftövervakning med aktiverad arbetare, offentlig autentisering/hosting, externa integrationer,
användarprövning och slutlig samkörning med övriga arbetsgrenar har separata beviskrav. Varken grön rökprovssvit
eller läst professionsfil innebär att kundintervjun eller designen når ribban.

Primärkällor: [Claude API overview](https://platform.claude.com/docs/en/api/overview) för serverkopplingens kontrakt,
[SQLite onlinebackup](https://www.sqlite.org/backup.html) för konsekvent backup. Verifierade 2026-10-08. Databehandling
och kontoavtal är inte styrkta av dessa tekniska dokument.
