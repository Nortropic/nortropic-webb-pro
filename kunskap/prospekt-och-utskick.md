# Prospekt och utskick

Referens för prospektflödet: vad som samlas in om verksamheter, vem som får ett brev, och vem som avgör vad. Beslutet
och ägarens ord: `BESLUT.md`, tillägget 2026-10-02. Verktygen: `kontroller/prospekt.py` (register, sajter, analys,
poäng), `kontroller/brev.py` (utkast), `kontroller/utskick.py` (grinden och sändningen), `dashboard/prospekt.py`.

## Ändamål och rättslig grund

Ändamålet är att välja ut verksamheter i en bransch och kommun, mäta deras nuvarande webbplats och erbjuda ett möte
där vi visar en skiss. Den rättsliga grunden för att behandla kontaktuppgifter är berättigat intresse
(dataskyddsförordningen artikel 6.1 f). Intresseavvägningen: uppgifterna är verksamhetens egna och publika (SCB:s
register, deras webbplats); behandlingen är en kontakt per verksamhet; invändning är ett ord i ett svar; och inget
lagras längre än tolv månader utan kundrelation. Informationen enligt artikel 13 och 14 står i sidfoten som
`utskick.py` lägger till varje brev; sidfoten är den enda källan till den texten.

## Marknadsföringslagen

19 §: e-post och sms till en fysisk person kräver samtycke i förväg. En enskild näringsidkare är en fysisk person
även i näringsverksamheten (förarbetena). Därför går brev bara till juridiska personer; en enskild firma får ett
ringmanus i dashboarden, och ägaren ringer eller skriver brev. 20 §: brevet säger vem avsändaren är, har en giltig
svarsadress och en tydlig väg att säga nej (sidfoten).

Juridiska former som får e-post, SCB:s kod och klartext ur `underlag/prospekt/KODER.json` (`jurformkoder`):
31 handelsbolag och kommanditbolag · 41 bankaktiebolag · 42 försäkringsaktiebolag · 49 övriga aktiebolag ·
51 ekonomisk förening · 53 bostadsrättsförening. Listan läses av grinden i `utskick.py`; en kod vars klartext inte
stämmer med tabellen räknas som okänd, och okänd nekar. Enskild näringsidkare (10), enkelt bolag och dödsbon är
fysiska personer.

En namngiven adress hos ett företag (fornamn@firma.se) är en gråzon. Rolladresser (info@, kontakt@, hej@ …) går
direkt; en namngiven adress kräver att ägaren kryssar i "jag bedömer att adressen är verksamhetens" på brevkortet.

## SCB:s spärrar

Registret bär tre flaggor per verksamhet: reklamspärr, e-postspärr och telefonspärr. Pipelinen gör dem till
`sparr{reklam, telefon, epost}` med sanning ur kodtabellerna; en okänd kod blir spärr. Reklamspärr gör posten
`avvisad` redan i svepet, så den varken analyseras eller kontaktas. E-postspärr stoppar brev; telefonspärr tar bort
telefonnumret ur registret.

## Vad som lagras, och inte

Per verksamhet: organisationsnummer, namn, juridisk form, postnummer och postort, kommun, SNI-koder,
anställdaklass, status, startdatum, spärrflaggor, telefon (utan telefonspärr), e-post (bara juridiska personer utan
e-postspärr; för fysiska personer bara domänen), webbadress med hur den hittades, poäng och signaler ur mätningen,
skärmbilder av den publika webbplatsen, status i flödet och tider. Aldrig: gatuadress, co-adress, personnamn
utöver det registrerade firmanamnet, innehåll från Google Places, sidtext utöver titel, anteckningar om personer.
Allt ligger under `underlag/`, som är utanför git; repot är publikt.

Gallring: `prospekt.py gallra` tar bort poster vars senaste kontakt (skapad, uppdaterad, utskick, svar) är äldre än
tolv månader (`NWP_PROSPEKT_GALLRING_MANADER`) och som inte blivit kund. Det är det brevet lovar; inga permanenta
undantag för vald, demo, utkast, skickat eller svar (Codex 2026-10-03, F35). Avvisade och nej-poster krymps till
organisationsnummer, status och datum, så att de aldrig läggs till igen.

## Spärrlistan

`underlag/prospekt/SPARR.json` är sanningen: poster med `typ` (e-post, domän eller organisationsnummer), `varde`,
`skal`, `tid` och `kalla` (manuell eller svar). Den som svarar "avregistrera" stryks samma dag: knappen "Stryk" på
kortet skriver posten, sätter status `nej` och speglar adressen till Resends spärrlista. En misslyckad spegling
sparas som `resend_fel` på posten och syns i dashboarden.

## Vem avgör vad

- Verktygen rapporterar: mätningen ger siffror och "varför" per signal, copykontrollen ger fynd, aldrig ett beslut.
- Grinden nekar: `far_skickas` i `utskick.py` släpper ett brev bara när status är utkast, ägaren godkänt exakt den
  texten, mottagaren är en juridisk person i listan utan spärr och utan post i spärrlistan, adressen är en
  rolladress eller bekräftad, inget redan skickats till verksamheten och Resend-nyckeln finns. Första nej vinner och
  visas som skäl på knappen.
- Ägaren godkänner varje brev och gör alla juridiska bedömningar; `kunskap/juridikflaggor.md` gäller. Ett brev
  bygger bara på det som mätts och setts: faktalistan i `PROSPEKT.json` och skärmbilderna. `brev.py` avvisar ett
  utkast med en siffra utanför faktalistan.

## Vad som inte görs

Ingen sändning utan ägarens godkännande. Inga sms. Inga brev till fysiska personer. Inga länkar till demosajter
(de publiceras inte). Inga betaltjänster för leads eller analys. Inget innehåll från Google Places i registret.
