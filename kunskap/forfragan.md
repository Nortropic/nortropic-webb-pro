# Skriftlig förfrågan: formuläret och dess mottagare

Ägarens ord 2026-10-02, uttryckt som en regel för alla sajter: "Bygg alltid in en skriftlig förfrågningsväg som fungerar utan mejlklient: ett formulär
med tre fält (namn, telefon, vad du vill bygga + valfri bild) som fungerar med vanlig POST utan JS, honeypot +
tidsfälla, och en bekräftelse som säger när ägaren ringer (A6.1–6.3, 6.5–6.7). Telefonen får förbli primär, men
standarden ska inte tillåta att 'ring' är enda vägen." Domarna L2 och L3 sa samma sak. Byggstandardens avsnitt 6
gäller; teorin står i `kunskap/teoretisk-grund.md` (Jarrett & Gaffney, Wroblewski, GOV.UK).

## I varje bygge (demo)

- **Formuläret** är mallens `src/components/Forfragan.astro`, på kontaktsidan och gärna som en sektion där den
  primära handlingen står. Den primära handlingen följer briefen (ring, boka, begär offert, beställ); formuläret är den
  skriftliga vägen bredvid den, också när ingen svarar i telefon.
- **Fälten:** namn, telefon, meddelande med etiketten i verksamhetens ord ("Vad vill du bygga?"), och en valfri bild.
  Det valfria märks "(valfritt)"; resten krävs. Inga fler fält utan skäl ur briefen. Beskedet vid ett tomt fält och
  vid ett nummer med bokstäver är svenskt, i verksamhetens ord (mallens `felNamn`, `felTelefon`, `felTelefonFormat`,
  `felMeddelande`) och står som text vid fältet med `aria-describedby` när JavaScript körs (WCAG 3.3.1);
  utan JavaScript stoppar telefonfältets `pattern` bokstäverna med webbläsarens eget besked.
- **Fällorna** ändras inte: honeypoten `webbplats` (dold, `tabindex="-1"`) och tidsfällan `fylltid`, varaktigheten i
  millisekunder från laddning till inskick mätt på webbläsarens klocka (`kunskap/formularsakerhet.md`, princip b).
- **Integritetstexten** vid knappen länkar till `/integritet/`. Integritetssidan anger personuppgiftsansvarig
  (verksamhetens namn, org.nr och kontakt), ändamål (svara på förfrågan), rättslig grund (berättigat intresse eller
  avtal), lagringstid (vid lansering också för det sparade inskicket, se nedan), rättigheter och vart man vänder sig.
- **Tacksidan** `/tack/` har noindex och säger vad som händer härnäst och när, ur underlaget ("ägaren ringer upp inom en
  timme på vardagar" om omdömena belägger det). Är svarstiden okänd: beställ den (`underlag/<slug>/BESTALLNING.md`) och
  lova inget du inte vet.
- **Mottagaren i demon** är provets och dashboardens lokala server: den läser fälten, skickar en ifylld honeypot
  tyst till `/tack/`, skickar ett ofullständigt inskick tillbaka till `/kontakt/?saknas=1#forfragan-saknas` och ett
  giltigt till `/tack/`. Den sparar, loggar och skickar ingenting.
- **Felbeskedet** följer med mallen: `#forfragan-saknas` överst i formuläret visas med `:target` utan JavaScript, i
  verksamhetens ord och med telefonnumret som väg vidare (propen `telefon`). Det som skrevs försvinner; det är en känd
  begränsning tills mottagaren vid lansering kan rendera svaret med fälten ifyllda.
- **Citat som nämner formuläret** ("skickade förfrågan via hemsidan") får stå, eftersom formuläret nu finns. Ett citat
  får aldrig berömma något som sajten inte har.

## Vid lansering

En serverfunktion på `/api/forfragan/` (`mall/leverans/forfragan.js`, lagd i kundrepot av `kontroller/exportera.py`)
tar över. Produktionskontraktet är nu skilt från den enklare, osparande demomottagaren. Lokala prov kör den
verkliga funktionen och HTTP/Chromium, men Blob och mejltjänsten ersätts med testdubblar. Det bevisar
felhanteringen och ordningen, inte fungerande externa konton eller faktisk mottagning hos verksamheten.
Äldre driftprov från 2026-10-05 gällde tidigare 303-kontrakt och verifierar inte det nya beteendet.

- Valideringsfel: **422**, skyddad HTML-sida med bevarade textfält, fellista som länkar till fälten och
  fältnära besked. Den fungerar utan JavaScript och skriver inte fältvärden i URL, logg eller lokallagring.
- Bild över 4 MB: **413** med bevarad text när kroppen kunde läsas; fel bildtyp: **422**. Filfältet kan inte
  återfyllas av servern, så sidan säger att bilden måste väljas igen. Mottagaren har samma telefonteckenregel
  som formuläret. HTML escapas och felsidan får no-store, noindex, no-referrer och CSP utan skript.
- Oläsbar kropp: **400**. Begäran över 4,4 MB: **413**. Dessa svar säger uttryckligen att uppgifterna inte
  kunde återställas. Taket mäts också på strömmen, även utan Content-Length. Plattformen kan stoppa en för
  stor begäran före funktionen; det svaret och den faktiska plattformsgränsen måste prövas vid lansering.
- Saknat lagringskvitto, inklusive saknad lagerkonfiguration: **503** med texten kvar och beskedet att
  mottagningen inte kunde bekräftas. **Inget mejl försöks före lagringskvittot.**
- Lagringen bekräftad men mejlaviseringen inte bekräftad: **303** till den förrenderade `/mottagen/` (`X-Forfragan: sparad`),
  ett eget mottaget-besked utan omskicksknapp, aldrig ett svar på POST-adressen (GR-20261008-r117-claude#D1).
  Det lovar ingen svarstid och säger att förfrågan inte behöver skickas igen. Verksamheten behöver ha en
  faktisk rutin för att läsa lagrade ärenden; någon automatisk aviseringskö byggs inte av detta svar. Mottagningsfilen
  anger `avisering: inte_bekraftad`. Efter identifierad mejlacceptans försöks ett separat `avisering.json`
  med mottagningsfil och mejl-id. Saknat aviseringskvitto betyder okänt, eftersom kvittoskrivningen också kan
  falla efter mejlacceptans. Kundrepots README ger uppföljningsvägen via projektets behöriga Blob-verktyg och
  kontroll mot mejltjänstens logg före manuell omsändning.
- Både lagring och mejltjänstens acceptans bekräftade: **303** till `/tack/`. Acceptans hos mejltjänsten
  betyder inte leverans till inkorgen eller ett mänskligt läst ärende.

`kontroller/driftkoll.py --formular` prövar det aktuella HTTP-kontraktet med syntetiska ogiltiga inskick
samt giltigt demoinskick bara i förhandsvisning. Riktiga mottagningsprov görs uttryckligen med verksamhetens
adress inför lansering. Mottagaren skickar och sparar bara i produktionen (`VERCEL_ENV=production`); i en förhandsvisning
eller lokalt är den demo också när variablerna finns (GR-20261008-r117-claude#D2).

**Kvarstående återförsöksrisk (G05-R):** tappar besökaren hela svaret efter ett lyckat första POST kan samma
inskick sparas och aviseras igen vid ett omförsök. Den sparade men ej aviserade förfrågan svarar med 303 till den
förrenderade `/mottagen/` (rättat 2026-10-08, GR-20261008-r117-claude#D1), så en omladdning eller bakåt/framåt där är
ingen ny POST. Dagens förrenderade formulär saknar individuellt inskicks-id
före första POST. Ny slumpnyckel i mottagaren eller innehållsdeduplikering utan tids-/avsiktsgräns löser inte
kontraktet. Individuell serverrendering och beständig idempotens måste prövas tillsammans; ingen sådan garanti
ges här. Resends idempotensnycklar gäller 24 timmar och kräver samma payload, men ersätter inte mottagarens
identitet och lagringshantering: https://resend.com/changelog/idempotency-keys . Blob stöder nekad överskrivning
och villkorliga skrivningar: https://vercel.com/docs/vercel-blob/using-blob-sdk . Originalavsnitten lästa
2026-10-08; även https://resend.com/docs/api-reference/emails/send-email (svarets id) lästes.
Bilagan sparas som `bilaga/bild`, skilt från de interna JSON-filerna; klientens filnamn styr inte lagringsvägen.
Lagringen har en gemensam lokal tidsgräns på 10 s, mejlanrop inklusive JSON-kvitto 8 s och aviseringsfilen 2 s.
AbortSignal skickas till leverantörsanropen och sena svar startar inte nästa steg. En tidsgräns bevisar inte att
leverantören saknar sidoeffekt: lagrings-/mejlutfallet är fortfarande okänt utan kvitto. Det sista kvittots timeout
ändrar inte ett redan identifierat mejlacceptansbesked. Blob-SDK:ns abortSignal kontrollerad i källan ovan.
Lagringskvittots pathname måste vara just begärd fil (slumpmässigt suffix uttryckligen avstängt), och mejlkvittot
måste innehålla ett giltigt id utan felobjekt. HTTP 200 ensamt räcker inte. Ingen konfigurationsändring eller extern sändning gjordes.

1. Bara POST; multipart eller urlencoded; begäran högst 4,4 MB och bilden högst 4 MB (Vercels gräns för en funktions
   begäran är 4,5 MB, och demons mottagare har samma tak), bara bildtyper i `bild`; en bild som inte tas emot får ett eget fältnära besked.
2. Validera igen på servern: namn 1–100 tecken, telefon 6–40 tecken med minst en siffra och bara siffror, mellanslag, +, bindestreck eller parenteser, meddelande 1–4000 tecken.
3. Honeypot ifylld: svara 303 till `/tack/` utan att skicka. Tidsfälla: `fylltid` under 1500 ms: samma sak. Tomt
   eller 0 (ingen JavaScript, direkt POST) godtas; fältet är ett botfilter, inte autentisering. Jämför aldrig en
   klientstämpel med serverns klocka. Felsidan (422/413/503) skriver `fylltid` 0, så tidsfällan är avstängd för omskick
   därifrån; honeypoten gäller fortfarande (GR-20261008-r117-claude#D4).
4. Begränsning: högst 3 inskick per 10 minuter och IP-adress, som en regel i Vercels brandvägg på `/api/forfragan/`
   (läggs vid lanseringen; tillgången på Pro är inte prövad); Turnstile om spam ändå kommer igenom.
5. Spara varje giltigt inskick i ett privat Vercel Blob-lager (OIDC, i Stockholm) innan mejlet går, med fälten och
   bilden. Mejlet är den del som
   fallerar (leverantören har en dålig dag, en DNS-post ändras, mejlet hamnar i skräpposten), och utan lagring är
   förfrågan borta utan att någon vet att den fanns (kirurgens intag 2026-10-03, Websites for Normal People).
   Inskicket gallras när integritetssidans lagringstid har gått; ingen annan läser det.
6. Mejl till verksamheten via en dedikerad tjänst med SPF, DKIM och DMARC på domänen; allt innehåll escapas i mallen;
   bilden som bilaga.
7. Svara enligt de separata utfallen ovan. Fel loggas som fasta felkategorier utan råa leverantörsfel eller
   personuppgifter. Vid mejlfel finns inskicket kvar i lagringen; hanteringsrutinen ska vara klar före lansering.
8. Konverteringshändelser för skickad förfrågan och telefonklick, i kakfri mätning.
