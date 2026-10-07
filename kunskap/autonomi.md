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
