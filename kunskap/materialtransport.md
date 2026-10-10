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

## Införda kontrakt och primärkällor

Verifierade mot leverantörernas dokumentation 2026-10-10. Modellvalen är uttryckliga i
`material_transport.STANDARD`; andra modeller kräver en granskad kontraktsändring.

| Leverantör och funktion | Infört kontrakt | Primärkälla |
| --- | --- | --- |
| Nano Banana, text till bild | Gemini Interactions, en infogad bild, `store: false` | [Bildgenerering](https://ai.google.dev/gemini-api/docs/image-generation), [REST-kontrakt](https://ai.google.dev/api/interactions-api) |
| Higgsfield, text till bild | Soul Standard, en bild | [Soul API](https://open.higgsfield.ai/models/higgsfield-ai/soul/standard/api-reference), [autentisering och jobb](https://open.higgsfield.ai/quick-start) |
| Higgsfield, text till video | Seedance 2.0 text-to-video | [Modellens API](https://open.higgsfield.ai/models/bytedance/seedance-2.0/text-to-video/api-reference) |
| Seedance, separat API-konto | BytePlus LAS, text till video | [Officiellt kontrakt för uppgifter och status](https://docs.byteplus.com/en/docs/Byteplus_LAS/video_gen_enhanced) |

## Verifieringsgräns

Regressionsproven använder syntetiska HTTP-svar och privata tempkonton. De prövar transport,
kund- och kandidatgräns, uppdragets identitet, status, återupptagning och filens användningsväg.
Verklig kontoåtkomst, pris, tillgänglig modell, genereringsresultat och designkvalitet återstår
att pröva under separat befintligt mandat. Ingen nyckel eller tjänst har aktiverats genom detta
införande. Webbtjänstens automatiska vidarebefordran är inte införd; den betrodda CLI-vägen
och funktionsingången är införda. Bildredigering och bild-till-video med uppladdade kundbilder
kräver ett eget avgränsat datakontrakt och ingår inte.
