# Autonomins mått och förmågeprovet

Codex helhetsbedömning 2026-10-04, punkt 8 och 9 (rekommenderad ordning 5): kvalitet, tillförlitlighet och
modellanvändning optimeras tillsammans, och tre frågor behöver egna belägg: känner granskaren igen ägarens ribba
(kalibreringen, `kontroller/granskarforsok/kalibrering.py`), kan byggaren återkommande nå den (förmågeprovet nedan), och
kan verkliga besökare använda sajterna (människor, aldrig en modell; NN/g: syntetiska användare ger hypoteser).

## Måtten

`.venv/bin/python kontroller/autonomi.py` skriver `kunder/AUTONOMI.md` och `kunder/AUTONOMI.json` (privata). Det läser
byggens loggar och domar och ändrar ingenting:

- **Accepterade:** andelen dömda byggen som ägaren skulle visa för verksamheten utan större ändringar (namnsvaret
  "Ja, som den är" eller "Ja, efter små ändringar"), och hur många som blev tydligt dåliga (namnsvaret "Nej").
  Namnsvaret gäller ribban när domen gavs; äldre domar gavs innan ägaren sa att de egna byggena inte håller
  (2026-10-03). En sparad dom utan ett giltigt svar på ribbans fråga räknas inte som bedömd. Inventerade uppdrag,
  belagda starter, giltigt bedömda, accepterade, underkända och ännu utan giltig dom redovisas skilt; en startad
  förberedelse räknas även när någon sajt ännu inte finns.
- **Modelltid, turer och listpris** per bygge: byggets sessioner med omtag, granskarnas omgångar och ateljén.
  Listpriset (`total_cost_usd`) är modellverktygets rapporterade listpris, inte fakturerad kostnad eller uppmätt
  abonnemangskvot. Råvärden summeras före avrundning. Identifierade kopior av samma resultat räknas en gång;
  återupptagna sessioner med olika resultat-id räknas var för sig. Anonyma svar kan inte säkert dedupliceras.
  Saknade, ogiltiga eller motstridiga värden gör totalen okänd. Den observerade delsumman finns separat och får
  inte presenteras som total. Ofullständiga byggen ligger utanför medianerna. Täckningen gäller hittade resultat
  och kända försök; helt ospårade anrop kan rapporten inte bevisa något om.
- **Väggtid till ägarens dom:** från att byggets sida öppnades i dashboarden till att domen sparades, inte aktiv
  arbetstid (sparas med domen sedan
  2026-10-05). I designprovet räknas minuterna per förslag från att vyn öppnades eller förra domen sparades; måttet
  i `autonomi.py` gäller domarna över byggen.
- **Återkommande fel:** hur ofta varje grind var röd över provets körningar.
- **Iterationens effekt:** om en granskningsomgång försämrade den bästa tidigare (godkänd före underkänd, färre
  blockerande fynd, högre betyg) och om den sista omgången var den bästa. Mer iteration är en hypotes om förbättring;
  ateljén bevarar redan sin vinnare, och en sista omgång som är sämre än den bästa är ett fynd.
- **Variation:** två körningar av samma verksamhet (A/B-paren) bredvid varandra.

## Inställningen måste nå det prövade passet

`ab.py starta --variabel effort` ändrar `NWP_EFFORT` i helbyggets process. Det är inte skisskaparens effort.
`NWP_ATELJE_EFFORT` är ateljéns standard för pass utan eget värde, medan `NWP_KANDIDAT_EFFORT` används av flera
pass i skissflödet, inklusive research och plan. Ett försök med bara skisskaparen använder i stället
`NWP_SKISSSKAPARE_EFFORT` (och vid ett separat modellförsök `NWP_SKISSSKAPARE_MODELL`). De gäller skapandet
och skaparens svar på kritik inom samma skissförsök; granskaren och andra pass är oförändrade. Utan dessa
variabler gäller tidigare standarder. Detta är en försöksmöjlighet, inte en ändrad standard.

Kandidatens status skriver vad som begärdes. Observerad modell/effort är okända tills sessionsbevis finns;
ett lokalt prov av startargument visar parameterkopplingen, aldrig vilken modell tjänsten faktiskt körde.
En A/B-arms mått läser loggen för slutpostens körning. Saknad logg eller mätvärde ersätts inte av en annan
körnings data. Kontextens andel räknas bara när ett enhetligt fönster faktiskt rapporterats.

Det prioriterade metodförsöket är medium mot high för skisskaparen, med en gemensam fryst brief, uppgift,
forsknings- och kandidatplan, referenspaket, verktygstillgång, övriga modellval, budget och kriterier. Båda
armar ska börja i separata rena kontexter från samma plan. Alla försök och omarbete räknas. Ingen skillnad
i kvalitet eller tidsvinst är belagd ännu; verkliga körningar och ägarens blinda bedömning återstår.

### Körklar mekanik, inget körmandat

`ab.py forbered-skiss <slug> --kandidat k01` förbereder just medium/high i **skisskaparen och dess svar på kritik**.
Kräver en ensam ännu inte arbetad kandidat i skissläge, gemensam forskning, prövad plan, uppdragsmaterial och
basprojekt. Ingen aktiv körning eller tidigare ägardom får finnas. Planen klonas till två egna kandidater med
identisk designbrief, separata sessioner och samma befintliga tids-/omförsöksbudget. Inga standardvärden ändras.
Förberedelsen gör inga modellanrop och ersätter inte forskningen, planeringen eller kundens startkontroll.

Posten ligger privat i befintliga `kunder/ab/skiss-<slug>-<id>.json`. Den bevarar ursprunglig plan och uppdrag,
lottad tilldelning och hashar över fakta, referenser, deklarerat material, kriterier, uppdrag, basprojekt, metod
och effektiv begärd budget. Källorna kontrolleras före och efter arbetet. Detta är ett **identitetslås**: filerna
skrivskyddas inte av mekanismen. Ändrade gemensamma förutsättningar nekar jämförelsen. Externa tjänsters nya svar
kan fortfarande variera; de redovisas i det befintliga observationsspåret, inte som identiska experimentindata.
En miljö med `CLAUDE_CODE_EFFORT_LEVEL` vägras för detta försök för att undvika konkurrerande inställningar.

Efter uttryckligt mandat för underlag och budget körs det befintliga `prototyp.py <slug> --fortsatt` från samma
version och miljö. Båda armarna ska ha avslutats innan ägaren väljer blint i Prototyp. Inget vanligt designval
startar ett metodförsök. En teknisk stubb visar argumentkopplingen till `--model`/`--effort`, inte tjänstens
effektiva inställning. Efter valet läser `ab.py skissresultat <slug>` försök, fel och rapporterad användning ur
samma kandidater, också arkiverade misslyckade försök. Kända saknade svar gör totalen okänd; observerad delsumma
står separat. Listpris är inte abonnemangskostnad. Modell/effort utan oberoende observation förblir okända.

Försökets första dom får tillkomma efter två avslutade källkontroller; den omskriver inte vilket underlag
skaparna fick. En ändrad kandidat eller andra ändrade källor gör fortfarande jämförelsen inaktuell. Visuellt
val, kritikeromdöme, tekniska kontroller och verklig användbarhet är olika belägg. Ett par ger ingen generell
effektskattning. Fullständiga versionsbundna rapporter krävs före beslut om nya standarder.

Vid skrivfel under förberedelsen sparas den nya kandidatens material åt sidan vid A/B-posten och originalplanen
återställs, så att kommandot kan prövas igen. Om även återställningens skrivning misslyckas står markören kvar
som ofullständig och start nekas. Inspektera då den privata postens `ursprung` innan något återställs; ta aldrig
bort arbetade kandidater för att komma runt spärren. Ingen automatisk städning av tidigare försöksbevis sker.

Källkontroll 2026-10-08: [Claude Code, Model configuration](https://code.claude.com/docs/en/model-config),
avsnitten om effort, prioritet och organisationsgränser. Begärd flagga kan begränsas och en skill kan påverka
effort. Därför likställer försöket inte begärt och observerat. Detta leverantörsdokument visar produktbeteende,
inte att högre effort ger bättre webbdesign i Nortropic.

## Förmågeprovet

Rökprovet (`kontroller/rokprov.sh`) är ett regressionsprov: det visar att kända beteenden håller. Förmågeprovet visar
om flödet kan lösa en svår kunduppgift, och redovisas för sig.

- **Varierade kundfall**, inte flera omtag av samma firma: olika innehållsmängd (få sidor eller många tjänster),
  bildunderlag (egna bra foton, få eller svaga foton), kontaktvägar (telefon, bokningssystem, offertformulär,
  beställning) och designbehov (hantverk, skönhet, mat, teknik och företagskunder).
- **Orörda fall:** några kundfall används aldrig för att ändra instruktionerna under utvecklingen; de körs bara för
  mätningen, som kalibreringens orörda exempel.
- **Två körningar per fall** med samma modell, brief och material, så att variationen syns.
- **Ägarens blinda dom** i dashboarden; kvalitet, fel, rapporterad tid och listpris redovisas var för sig ur `autonomi.py`.
- **När:** först när designprovet visat att ateljévägen håller (ägarens blinda dom i dashboarden) och granskaren
  prövats på de orörda exemplen K14–K19. Annars mäts en väg som ändå ska ändras. (Skrivet när ateljévägen var
  standard; normalflödet är nu kandidatflödet, och villkoret är inte omprövat.)

## Kvalitetsprovet: ett sammanhängande fall

Ägarens uppdrag 2026-10-09 om metod, utförande och kvalitet (punkt 8) och om ett källförankrat arbetssätt (punkt 9).
Ett avgränsat fall följs genom hela kedjan: referensavsikt, kundanpassning, renderad webb, oberoende bildbedömning och
ägarens dom. Den första metodvariabeln är H01, ett preliminärt visuellt mål före kod (`kunskap/metodregler.md`). Allt
annat hålls fast. Provet är förberett, inte kört: verkliga sessioner och helbygget kräver ägarens mandat.

- **Material:** en fiktiv verksamhet med ett skrivet underlag och licensierat eller tydligt illustrativt bildmaterial
  med källa, eller material som ägaren uttryckligen tillåtit. Kalibreringens undanhållna exempel (K14–K19) används
  aldrig.
- **Underlag och plan:** kundunderlaget med `prototyp.py <slug> --forbered`, sedan skapandeflödet till en planprövad
  plan med en kandidat, i skissläget: `NWP_KANDIDATER=1 NWP_KANDIDAT_STOPP_EFTER=planprovning .venv/bin/python
  kontroller/prototyp.py <slug>` stannar efter planprövningen, före skaparna (läget `planprovad`, slutkod 0).
- **Två armar:** `ab.py forbered-skiss <slug> --kandidat k01 --variabel metodvariant` lottar grund och h01 på två
  kandidater med samma uppdrag, material, modell, effort, budget och metod i övrigt. Det kräver att k01:s uppdrag är
  planprövat i sin nuvarande version, och klonen bär samma prövning (`PLANPROVNING.json`, `klonade`), så att ingen arm
  prövas om för sig. Identitetslåset nekar jämförelsen om något gemensamt ändras. Efter mandatet kör `prototyp.py <slug>
  --fortsatt` båda armarna.
- **Bedömningen börjar med bilderna:** ägaren väljer blint i dashboardens Prototyp, före skaparnas förklaringar. Valet
  får vara ingen av dem, och en arm som bytt grundkomposition med skäl är inte felaktig.
- **Var kvaliteten bevaras eller försvagas:** efter domen ställs referensbilderna, det visuella målet (h01), referenslåset
  och skissens bilder bredvid varandra i de fyra relationerna (bildens beskärning mot rubriken, de typografiska
  storlekarna och hierarkin, täta och luftiga sektioner och rytmen, navigation och interaktion mot innehållet). Det som
  syns i bilderna står som observation, och förklaringar av orsaken som hypotes.
- **Vidare till webben:** den godkända kandidaten fördjupas och helbyggs (ägaren startar). Provets jämförelse mot
  prototypen, granskarnas `visuell_jamforelse` och ägarens dom visar om det godkända bevarades.
- **Bevaras vid varje övergång:** kandidaternas versioner och bilder (arkiverade försök), A/B-posten med källornas
  identitet, VINNARE.json med hasharna, byggets dist-sha, granskningen med metodberoendena och jämförelsens besked, och
  slutposten SLUT.json.
- **Färdigt när:** båda armarna är avslutade och kontrollerade (`ab.py skissresultat <slug>` utan fel), ägaren har dömt
  båda blint, skillnaden står som observation med bilderna, och helbygget från det godkända har en jämförelse som är
  `verifierad`, eller en redovisad brist.

Ett fall är det första belägget, inte generell förmåga: varierade kundfall (förmågeprovet ovan) och oberoende
kalibrering behövs sedan. Når modellen inte ribban trots korrekt underlag och fungerande överlämningar prövas modellvalet,
uppgiftens svårighet och behovet av mänsklig art direction, inte fler regler eller fler agenter.
