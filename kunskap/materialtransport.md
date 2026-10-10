# Materialtransport: från beställning till användbar fil

Läs detta när materialsteget ska generera en illustrativ bild eller video. Lokal import,
canvas-koncept och användning i kandidaten finns fortsatt i `kontroller/material.py`.

## Skaparens väg

Skaparen beskriver bildens eller videons uppgift och beställer genom den kandidatbundna
ingången `material.py <slug> --kandidat <kNN> --bestall …`. Välj leverantör och typ;
`--parametrar` kan ange dokumenterade format, upplösning och videoegenskaper. Förvalen och
den exakta modellen sparas tillsammans med prompten i versionens `bestallning`.

Resultatet är `vantar_mandat_konto`, med en `uppdrag_sha`. Inga kontofiler läses och inget
material genereras vid beställningen. Skaparen använder befintligt material eller redovisar
det saknade materialets konsekvens tills ett genererat resultat finns. En beställning är
inget belägg för generering eller visuell kvalitet.

## Betrodd körning

Ägaren eller en betrodd process med mandat för det exakta uppdraget granskar den sparade
beställningen och kör, från repots rot:

```sh
.venv/bin/python kontroller/material.py <slug> --generera <id> --uppdrag-sha <sha256> --godkann-kostnad --rattigheter '<rättighetsbelägg>'
```

Detta är en separat ingång utan `--kandidat` eller `NWP_SLUG`. Den ändrar inte beställningen.
Hashen binder slug, kandidat, material-id, version, roll, leverantör, modell, prompt och
parametrar. Medgivandet gäller ett uppdrag, inte kommande generationer. Abonnemang hos en
webbtjänst innebär inte automatiskt åtkomst eller betalningsmandat för dess API.

Nyckeln läses först här, ur befintlig privat nyckelfil med enbart ägarbehörighet. Den skickas
bara i autentiseringshuvudet till leverantörens fasta API-värd. För `seedance` avses BytePlus
LAS-kontots API-nyckel, inte en godtycklig tjänst med samma modellnamn. Seedance via Higgsfield
beställs i stället med `--leverantor higgsfield --typ video` och använder Higgsfields konto.

Utgående prompt prövas med kundvaktens identifieringsregler. Endast generell text skickas;
kundbilder, kundfiler, URL:er och callbacks är inte införda som indata. Materialet har rollen
`illustrativ` eller `koncept` och påstår aldrig att det visar kundens verkliga verksamhet.

Transporten gör ett POST. Asynkrona jobb sparar jobb-id före första statuskontrollen. Ett
avbrott efter accepterat jobb ger `vantar_resultat`: samma kommando fortsätter med GET utan
en ny beställning. Ett tvetydigt POST-fel utan jobb-id ger `oklart`; samma version skickas
inte igen. Kontrollera då leverantörens konto innan en uttrycklig ny version beställs.
En tidsgräns avbryter den lokala väntan, inte leverantörens redan accepterade jobb.

Filen får en ny versionsväg, formatkontroll och SHA-256. Svarstexter, autentiseringsuppgifter
och signerade medieadresser skrivs inte i registret eller felmeddelandena. Hämtningen använder
repots DNS- och adresskontroller i anslutningen och följer inga omdirigeringar. Formatkontrollen
prövar MIME och filsignatur; den är inte en visuell bedömning eller fullständig mediaavkodning.

Vid `genererad` kan skaparen använda samma `--anvand <id> --plats <plats>` som för importerad
media. Video kräver fortsatt en separat posterbild. Webboptimering och visuell bedömning
ligger kvar i byggflödet. Varken en godkänd HTTP-respons eller ett grönt transportprov visar
att materialet passar sidan.

Import och användning förankrar katalogleden med kataloghandtag. Kandidatrot, källfil,
kopierad bild, posterbild och materialförteckning får inte följa symboliska länkar eller
hårdlänkar. Nya versioner publiceras exklusivt; användningens egna vanliga filer byts atomiskt.

## Redigering och bild till video ur eget material

Ägarens uppdrag 2026-10-07 (punkt 5B) gäller bildgenerering och redigering med Nano Banana, video med Seedance och kedjan
Nano Banana → bild → Seedance. Den lokala delen är införd: `--bestall "<ändringen>" --leverantor nano-banana --fran
<id>[@vN]` redigerar en bild, och `--bestall "<rörelsen>" --leverantor seedance --typ video --fran <id>[@vN]` gör video
med bilden som första bildruta. Källbilden binds i uppdragets hash med material-id, version, typ, storlek och sha256;
vid verkställandet läses den ur registret igen och måste vara samma byte.

Tillåten uppladdning är definierad för sig, skild från Refero- och Mobbin-sökningarna: bara materialregistrets egna
illustrativa bilder (PNG, JPEG eller WebP i en färdig version, kandidatens egen eller gemensam) kan bli källbild.
Kundens egna bilder står inte i registret och når aldrig vägen. Gemini får bilden som ett objekt i `input` (högst 15 MiB
här; dokumentationens tak för infogad data är 20 MB per anrop). BytePlus LAS får den som `data:`-URL med rollen
`first_frame` (högst 30 MiB per bild enligt dokumentationen), så ingen publik adress skapas. Higgsfields bild till
video kräver en uppladdning som ger en publik adress (`/files/generate-upload-url`, `public_url`); den är inte införd,
eftersom en publik kopia är ett eget beslut även för eget material.

## Materialkön

`material.py <slug> --ko` listar varje version som väntar på mandat, konto, resultat eller kontroll av ett okänt utfall,
med exakt uppdragshash, modell, parametrar och källbild. Kön verkställer ingenting: ett kostnadsmedgivande gäller en
version, och befintliga beslut ger inget stående mandat för automatisk generering. Ett sådant mandat (belopp, period,
leverantörer) är ägarens beslut; utan det är kön ägarens arbetslista för `--generera`.

## Härdning efter dokumentationskontrollen 2026-10-10

- Geminis bildanrop är synkront med `store: false`; vår väntan är högst 90 sekunder (dokumentationen: HTTP-anrop stängs
  normalt efter ungefär 60 sekunder). Ett avbrott ger `oklart`: kostnaden kan ha uppstått och bilden kan inte hämtas
  igen, så samma version skickas inte om.
- Ett färdigt jobb vars resultatadress har gått ut (BytePlus LAS behåller videon i 24 timmar och jobbet i sju dagar,
  Higgsfield adresserna i minst sju dagar) svarar 403, 404 eller 410. Det blir ett slutgiltigt fel, inte en evig väntan,
  och en ny version beställs uttryckligen.
- En lagringsvärd som svarar `application/octet-stream` får typen ur filsignaturen; en uttrycklig typ som strider mot
  signaturen nekas som förut.
- Statusfrågorna glesas ut från 2 till högst 10 sekunder med slumpad spridning. Statusadressen byggs mot den fasta
  API-värden, också när Higgsfields svar anger en `status_url`; nyckeln följer aldrig en adress som leverantörens svar
  pekar ut.
- Higgsfields idempotensnyckel skickas per version. Dokumentationen tillåter att samma anrop skickas om med samma nyckel
  efter ett tvetydigt fel; flödet gör det inte automatiskt, och `oklart` kontrolleras i kontot före en ny version.

## Införda kontrakt och primärkällor

Verifierade mot leverantörernas dokumentation 2026-10-10. Modellvalen är uttryckliga i
`material_transport.STANDARD`; andra modeller kräver en granskad kontraktsändring.

| Leverantör och funktion | Infört kontrakt | Primärkälla |
| --- | --- | --- |
| Nano Banana, text till bild | Gemini Interactions, en infogad bild, `store: false` | [Bildgenerering](https://ai.google.dev/gemini-api/docs/image-generation), [REST-kontrakt](https://ai.google.dev/api/interactions-api) |
| Higgsfield, text till bild | Soul Standard, en bild | [Soul API](https://open.higgsfield.ai/models/higgsfield-ai/soul/standard/api-reference), [autentisering och jobb](https://open.higgsfield.ai/quick-start) |
| Higgsfield, text till video | Seedance 2.0 text-to-video | [Modellens API](https://open.higgsfield.ai/models/bytedance/seedance-2.0/text-to-video/api-reference) |
| Seedance, separat API-konto | BytePlus LAS, text till video | [Officiellt kontrakt för uppgifter och status](https://docs.byteplus.com/en/docs/Byteplus_LAS/video_gen_enhanced) |
| Nano Banana, redigering | Samma Interactions-anrop med källbilden som `{"type": "image", "data", "mime_type"}` före texten | [Bildgenerering](https://ai.google.dev/gemini-api/docs/image-generation) |
| Seedance, bild till video | BytePlus LAS med `{"type": "image_url", "role": "first_frame"}` som `data:`-URL | [Videouppgifter](https://docs.byteplus.com/en/docs/Byteplus_LAS/video_gen_enhanced) |

## Verifieringsgräns

Regressionsproven använder syntetiska HTTP-svar och privata tempkonton. De prövar transport,
kund- och kandidatgräns, uppdragets identitet, status, återupptagning och filens användningsväg.
Verklig kontoåtkomst, pris, tillgänglig modell, genereringsresultat och designkvalitet återstår
att pröva under separat befintligt mandat. Ingen nyckel eller tjänst har aktiverats genom detta
införande. Webbtjänstens automatiska vidarebefordran är inte införd; den betrodda CLI-vägen
och funktionsingången är införda. Redigering och bild till video med registrets egna bilder är införda lokalt
(ovan); med kundens egna bilder kräver de ett eget avgränsat datakontrakt och ingår inte.
