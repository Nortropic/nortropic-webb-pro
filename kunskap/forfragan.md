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
  `felMeddelande`) och står som text vid fältet med `aria-describedby`, med och utan JavaScript (WCAG 3.3.1): CSS
  (`:user-invalid`) visar beskedet när besökaren lämnat fältet eller försökt skicka, och med JavaScript får det första
  felet fokus och beskeden fylls först vid fel; utan JavaScript visar webbläsaren dessutom sin egen bubbla, och
  telefonfältets `pattern` stoppar bokstäverna med formatbeskedet synligt vid fältet.
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

Kundsajtens Worker på Cloudflare Workers tar över (ägarens beslut 2026-10-09, `BESLUT.md`): `mall/leverans/worker/index.js`,
lagd i kundrepot av `kontroller/exportera.py`. Sidorna är förrenderade och serveras som Static Assets; bara vägarna
under `/api/` kör Workern (`wrangler.jsonc`, `run_worker_first`). Ärendet sparas i D1 (schemat
`mall/leverans/migrations/`) och en bilaga privat i R2. Demomottagaren ovan är oförändrad och sparar ingenting.

Proven och vad de bevisar:

- `kontroller/rokprov/revision/prov_formularfel.py` kör Workern ur exporten i Node mot D1 som riktig SQLite med mallens
  migreringar, R2 och mejlbindningen som märkta attrapper med felinjektion (lagret faller, kvittot stämmer inte, fristen
  går ut, bindningen nekar med en felkod), och samma Worker i Chromium utan JavaScript. Det bevisar felhanteringen,
  ordningen och idempotensen.
- `kontroller/workersprov.py` (i rökprovet via `prov_workers.py`) kör den exporterade Workern i Cloudflares runtime
  (workerd) med lokal D1 och R2 och Wranglers simulering av `send_email`, låst till provets adresser: mejlet sparas i
  simuleringens lager och skickas inte.
- Inget av dem bevisar ett fungerande Cloudflare-konto, en verifierad mottagare eller faktisk mottagning hos
  verksamheten; det är fjärrprovet och det riktiga inskicket vid lanseringen (`kunskap/lansering.md`).

Utfallen:

- Valideringsfel: **422**, skyddad HTML-sida med bevarade textfält, fellista som länkar till fälten och fältnära
  besked. Den fungerar utan JavaScript och skriver inte fältvärden i URL, logg eller lokallagring. Inskicks-id:t följer
  med, så att ett nytt försök därifrån blir samma ärende.
- Bild över 4 MB: **413** med bevarad text; fel bildtyp: **422**. Filfältet kan inte återfyllas av servern, så sidan
  säger att bilden måste väljas igen. Mottagaren har samma telefonteckenregel som formuläret. HTML escapas och felsidan
  får no-store, noindex, CSP utan skript och `Referrer-Policy: same-origin`: med no-referrer skickar webbläsaren
  `Origin: null` på felsidans nya försök (Chromium-provet 2026-10-10).
- Oläsbar kropp: **400**. Begäran över 4,4 MB: **413**. Dessa svar säger uttryckligen att uppgifterna inte kunde
  återställas. Taket mäts också på strömmen, även utan Content-Length.
- Från en annan webbplats: **403**. Webbläsarens `Sec-Fetch-Site` avgör (bara `same-origin` och `none` tas emot);
  utan det huvudet ett `Origin` som inte är webbplatsens.
- Saknat lagringskvitto, också en produktion utan D1-bindning: **503** med texten kvar och beskedet att mottagningen
  inte kunde bekräftas. **Inget mejl försöks före lagringskvittot.** Ärendet och dess utkorgsrad skrivs i en
  transaktion; en bilaga som lagrats tas bara bort när ärendet bevisligen inte sparades (ett tvetydigt fel kan ha sparat
  det).
- Lagringen bekräftad men mejlet inte bekräftat: **303** till den förrenderade `/mottagen/` (`X-Forfragan: sparad`),
  ett eget mottaget-besked utan omskicksknapp, aldrig ett svar på POST-adressen (GR-20261008-r117-claude#D1). Det
  lovar ingen svarstid och säger att förfrågan inte behöver skickas igen. Utkorgsraden står kvar som `fel` (mejlet
  nekades), `skickar` (okänt utfall) eller `vantar` (ingen mejlmottagare) för uppföljning.
- Både lagring och mejltjänstens acceptans bekräftade: **303** till `/tack/`, och utkorgen `accepterad` med mejl-id.
  Acceptans hos mejltjänsten betyder inte leverans till inkorgen eller ett mänskligt läst ärende.
- Samma inskick igen: **303** `dubblett`, till `/tack/` om det första ärendet aviserades, annars `/mottagen/`. Inget
  nytt ärende och inget nytt mejl.

**Utkorgen** (D1-tabellen `utkorg`): `vantar` → `skickar` → `accepterad` | `fel`. Avsikten skrivs före nätanropet, så
`skickar` utan slutläge är ett osäkert utfall, inte ett skäl att skicka igen i blindo. `fel` betyder bara att
bindningen nekade mejlet med en felkod som är ett slutligt besked (till exempel `E_RECIPIENT_NOT_ALLOWED`,
`E_SENDER_NOT_VERIFIED`, `E_VALIDATION_ERROR`; listan `NEKADE` i Workern); en tidsgräns, `E_INTERNAL_SERVER_ERROR`, ett
fel utan kod eller ett kvitto utan meddelande-id lämnar raden som `skickar` (granskningspasset 2026-10-10: ett mejl som
accepterats men vars svar kom sent får aldrig se ut som ett fel). Bindningen har ingen idempotensnyckel
(https://developers.cloudflare.com/email-service/api/send-emails/workers-api/, läst 2026-10-10), så ett osäkert utfall
stäms av i utkorgen och skickas aldrig om automatiskt. Lokalt simulerar `wrangler dev` bindningen och skickar inget så
länge bindningen saknar `remote: true` (https://developers.cloudflare.com/email-service/local-development/sending/, läst
2026-10-10); mallen sätter det aldrig. Loggen och utkorgen får bara Workerns egna orsaker och felkoden, aldrig en
leverantörs feltext. Läget och gallringen sköts med `kontroller/forfragningar.py` (`kunskap/drift.md`,
Formulärets ärenden); ett automatiskt nytt försök och en schemalagd gallring körs inte, eftersom de väntar på
beslutet om schemalagd körning (Cron Triggers är 5 per konto på gratisnivån).

**Idempotensen (G05-R):** formuläret sätter ett inskicks-id (`crypto.randomUUID()`) när sidan laddas. Ärendets nyckel är
id:t tillsammans med innehållet (namn, telefon, meddelande och bildens typ och storlek), så att ett nytt meddelande med
ett id som webbläsaren återställt efter bakåt eller omladdning blir ett nytt ärende; utan JavaScript är nyckeln
innehållet i ett tiominutersfönster. Varje ärende bär också innehållets fönsternyckel, och samma innehåll inom fönstret
eller det föregående är samma ärende, med eller utan id. Samma innehåll skickat igen mer än tio till tjugo minuter
senare utan id blir alltså ett nytt ärende, och två olika personer kan inte skicka exakt samma text samtidigt utan att
den andra räknas som samma ärende. Två samtidiga inskick med samma nyckel blir ett ärende (D1:s unika nyckel).

**Frister:** varje lagringssteg (kontrollen av tidigare inskick, bilagan, ärendet, utkorgen) har 10 s, mejlanropet
inklusive kvittot 8 s. Ett steg som inte bekräftas inom fristen räknas som obekräftat; det kan ändå bli klart senare,
och därför tas en bilaga aldrig bort efter en frist (ärendet kan peka på den). En frist bevisar inte att leverantören
saknar sidoeffekt. Bindningens kvitto måste innehålla ett giltigt `messageId`; ett svar utan det räknas som obekräftat.

`kontroller/driftkoll.py --formular` prövar HTTP-kontraktet mot en driftsatt adress med syntetiska ogiltiga inskick,
och ett giltigt demoinskick bara i förhandsvisningen (bakom Cloudflare Access med `--access-fil`). Riktiga
mottagningsprov görs uttryckligen med verksamhetens adress inför lansering. Workern sparar och skickar bara i
produktionen (`MILJO=produktion` i `wrangler.jsonc`); förhandsvisningen (`--env forhandsvisning`) har varken D1, R2
eller mejlbindning och är demo också om en variabel skulle finnas (GR-20261008-r117-claude#D2).

1. Bara POST; multipart eller urlencoded; begäran högst 4,4 MB och bilden högst 4 MB (Workerns egna tak, långt under
   plattformens gräns för en begärans storlek), bara bildtyper i `bild`; en bild som inte tas emot får ett eget
   fältnära besked.
2. Validera igen på servern: namn 1–100 tecken, telefon 6–40 tecken med minst en siffra och bara siffror, mellanslag, +, bindestreck eller parenteser, meddelande 1–4000 tecken.
3. Honeypot ifylld: svara 303 till `/tack/` utan att spara eller skicka. Tidsfälla: `fylltid` under 1500 ms: samma
   sak. Tomt eller 0 (ingen JavaScript, direkt POST) godtas; fältet är ett botfilter, inte autentisering. Jämför aldrig
   en klientstämpel med serverns klocka. Felsidan (422/413/503) skriver `fylltid` 0, så tidsfällan är avstängd för
   omskick därifrån; honeypoten gäller fortfarande (GR-20261008-r117-claude#D4).
4. Begränsning: högst 3 inskick per 10 minuter och IP-adress, med Cloudflares hastighetsbegränsning på
   `/api/forfragan/` (regel på kundens zon eller Workers egen begränsning; väljs och prövas vid lanseringen, inte
   prövad än); Turnstile om spam ändå kommer igenom.
5. Spara varje giltigt inskick i D1, och bilden privat i R2 under `forfragningar/<datum>/<ärende>/bilaga` (klientens
   filnamn är bara en etikett), innan mejlet går. Mejlet är den del som fallerar (leverantören har en dålig dag, en
   DNS-post ändras, mejlet hamnar i skräpposten), och utan lagring är förfrågan borta utan att någon vet att den fanns
   (kirurgens intag 2026-10-03, Websites for Normal People). Ärendet bär `gallras` (integritetssidans lagringstid,
   `GALLRING_DAGAR`); ingen annan än verksamheten och Nortropic läser det.
6. Mejl till verksamheten genom Cloudflares e-post från Workern (`send_email`-bindningen `EMAIL`; ägarens beslut
   2026-10-10, `BESLUT.md`); texten som ren text, bilden som bilaga. Avsändaren ligger på Nortropics routing-domän
   `notis.nortropic.se` (Email Routing påslaget 2026-10-10; SPF och DKIM sköts av Cloudflare), och mottagaren är
   verksamhetens brevlåda, verifierad i Nortropics konto. Mejl till verifierade mottagare är gratis på alla planer;
   högst 200 verifierade adresser per konto och 25 MiB per meddelande
   (https://developers.cloudflare.com/email-service/platform/limits/, läst 2026-10-10). Bindningen är låst till
   kundens mottagare och avsändaren (`allowed_destination_addresses`, `allowed_sender_addresses`), som exporten skriver
   in ur `underlag/<slug>/CLOUDFLARE.json`. Var Cloudflare behandlar mejlets innehåll anges inte i källorna;
   integritetstexten nämner Cloudflare som mottagare av förfrågan. D1 och R2 skapas med EU-jurisdiktion. Resend är
   ersatt för formuläret och står kvar i katalogen som historik.
7. Svara enligt de separata utfallen ovan. Vid mejlfel finns ärendet kvar i D1; hanteringsrutinen ska vara klar före
   lansering.
8. Konverteringshändelser för skickad förfrågan och telefonklick, i kakfri mätning.
