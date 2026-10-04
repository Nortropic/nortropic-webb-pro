# Lansering: procedur, kontroll, oåterkalleligt och återgång

Gäller när en verksamhet har sagt ja till sajten och ägaren beslutar att den ska ut. Inget bygge har lanserats än,
och Vercel väntar tills en kund ska ut (ägarens beslut, `BESLUT.md`). Privat förhandsvisning och slutrapport kommer
alltid först. Verktygen i repot: `kontroller/prova.py` (provet, också mot en förhandsvisning),
`kontroller/seo_kontroll.py --lage lansering`, `kontroller/webblasare/arkivera.mjs` (arkiv av den gamla sajten).
Det som inget verktyg gör står som **människa**: ägaren eller verksamheten gör det, ingen session.

## Vercel-steget

Byggstandardens L-punkter 1.4, 4.5, 4.6 och 8.1 pekar hit. Stacken är Astro med statisk utdata; Vercel bygger
`npm run build` och serverar `dist/`.

- **Projekt och skydd (människa):** ett Vercel-projekt per verksamhet, kopplat till sajtens eget repo. Skydd för alla
  driftsättningar slås på innan den första går ut, och lösenordet lämnas bara till verksamheten och ägaren.
- **Grenar (1.4):** en gren per ändring; varje gren får en egen förhandsvisning; `main` är produktion. Förhandsvisningen
  svarar med `X-Robots-Tag: noindex`. Pröva med `curl -sI <förhandsvisningens adress> | grep -i x-robots-tag`; saknas
  huvudet läggs det i `vercel.json` under `headers` för allt utom produktionsdomänen.
- **Cache (4.5):** filerna under `/_astro/` har hash i namnet och får `Cache-Control: public, max-age=31536000,
  immutable`; HTML får kort cache eller `must-revalidate`, så att en rättelse syns direkt. Pröva båda med `curl -sI`.
- **Mätning per ändring (4.6):** varje förhandsvisning prövas innan den slås ihop: `kontroller/prova.py` mot bygget,
  och Lighthouse mot förhandsvisningens adress. En regression mot 4.1 stoppar sammanslagningen.
- **HTTPS och värd (8.1):** Vercel ger certifikatet. En variant (med eller utan www) är kanonisk och den andra
  omdirigerar med 308; canonical, sitemap och `site` i `astro.config.mjs` pekar på den kanoniska. HSTS
  (`Strict-Transport-Security: max-age=63072000; includeSubDomains`) och `frame-ancestors 'none'` sätts som
  svarshuvuden i `vercel.json`, eftersom meta-CSP:n i mallen inte kan bära `frame-ancestors`.
- **Formuläret:** serverfunktionen på `/api/forfragan` enligt `kunskap/forfragan.md`, Vid lansering: spara först,
  mejla sedan, `/fel/` vid mejlfel. Hemligheter (mejltjänstens nyckel) ligger i Vercels miljövariabler, aldrig i repot.
- **Återgång:** föregående produktionsdriftsättning befordras tillbaka i Vercel (människa, eller Vercels CLI med
  ägarens ja). Det återställer inte DNS.

## Före lanseringsdagen

**Resorna som står kvar.** `prov/resor/RESOR.md` listar under "Kvar till lanseringen" de resor som provet inte kan
köra lokalt (`kunskap/resor.md`): nivån testintegration (till exempel en genomförd bokning i tjänstens testmiljö) och
verklig leverans (en förfrågan som kommer fram till verksamheten). Var och en genomförs och kvitteras, med datum och
vem som såg resultatet, innan lanseringen.

**DNS (människa).** Först sänker en behörig människa TTL för posterna som ska ändras, till exempel till 300 s, minst
en gammal TTL före bytet. TTL för delegeringens NS-poster sätts av registret och går inte att sänka i kundens zon.
Har kunden e-post på domänen är standardvägen att bara ändra webbposterna hos nuvarande DNS-värd. Ett
namnserverbyte kräver att hela zonen återskapas ur en zonexport, också namn som ingen kontroll räknar upp. Ingen
session ändrar DNS. Spara posterna före bytet (NS, MX, TXT, CAA, A och AAAA på domänen; A, AAAA och CNAME på www;
TXT på `_dmarc`) med `dig +noall +answer <namn> <typ>` i en fil i kundmappen, och läs samma poster igen när den
gamla TTL:en har löpt ut. Ändrad eller saknad MX, TXT eller `_dmarc` är ett fynd; webbposterna och NS ska ha
ändrats. När bytet är bekräftat höjer den behöriga människan TTL igen.

**E-postdomänen.** Domänen som formulärets mejl skickas från: SPF (`dig TXT <domän>`), DKIM under mejltjänstens
selektor (`dig TXT <selektor>._domainkey.<domän>`) och DMARC (`dig TXT _dmarc.<domän>`). Saknas både SPF och DKIM är
det ett fynd; saknad DMARC en anmärkning; flera SPF-poster ett fynd. Det prövar att posterna finns, inte att
signeringen fungerar; läs också mejltjänstens eget verifieringsbesked. Gmail kräver SPF eller DKIM av alla avsändare.

**Arkiv av den gamla sajten.** Före omdirigeringar och DNS-byte:

```sh
node kontroller/webblasare/arkivera.mjs --adress https://gamla-domanen.se --kund <kundmapp utanför repot> \
  --intervju ADRESSER.json --ut <ny katalog i kundmappen>
```

Verktyget vägrar kataloger inuti repot; arkivet läggs därför utanför, till exempel i `~/Arkiv/<slug>/`.
`ADRESSER.json` är `{"migrering_adresser": ["https://gamla-domanen.se/sida/", ...]}` med de gamla adresserna som
ska omdirigeras. Verktyget förenar dem med sidkartan och sparar HTML, HAR och helsidesbild per sida; `MANIFEST.json`
anger varje adress, status, fel och SHA-256. Läs alla fel innan den gamla sajten försvinner. Arkivet är privat
kundmaterial.

**Lanseringskonfigurationen** är skild från förhandsvisningen: noindex och `Disallow: /` bara i förhandsvisningen,
kanonisk värd vald, omdirigeringar från gamla adresser i `vercel.json` (301 eller 308), sökkonsolens verifieringstagg
renderad, provet grönt mot lanseringsbygget och `kontroller/seo_kontroll.py --lage lansering` utan fynd.

## Lanseringsdagen

1. Driftsätt `main`; startsidan svarar 200 med rätt innehåll.
2. Läsande kontroll mot den riktiga domänen: noindex borta (`curl -sI` och meta), sitemap 200, robots tillåter,
   kanonisk variant, och varje gammal adress ger 301 eller 308 och landar på sitt mål med 200 inom fem hopp
   (`curl -sIL <gammal adress>`). Formulärets riktiga väg prövas med ett inskick från verksamheten själv, inte från oss.
3. Sökkonsol och Bing Webmaster Tools: verifiera och lämna sitemap (människa, `kunskap/sokkonsol.md`).
4. Mätning: konverteringshändelserna syns på produktionsdomänen.
5. Verksamheten får sidan **Så ändrar du på sajten** (nedan).

## Så ändrar du på sajten

En sida till verksamheten, skriven i deras ord utan tekniska termer, överlämnad på lanseringsdagen tillsammans med
utvecklarens README (byggstandarden 1.6). Den säger:

- **vad som kan ändras utan ny beställning:** öppettider, telefon, priser, en bild, ett omdöme, en text som blivit fel;
- **hur man ber om det:** till vem, på vilket sätt, och vad som behövs (texten eller bilden, och var den ska stå);
- **svarstid:** när ändringen syns;
- **vem som äger domän och konton:** domänen, Vercel-projektet, mejltjänsten, sökkonsolen, och hur de lämnas över om
  verksamheten vill byta leverantör.

Sajten är statisk utan redigeringsverktyg, så kunden kan inte ändra själv; sidan ska säga det rakt.

## Oåterkalleligt

Första indexeringen av fel innehåll; ägarskap i sökkonsolen; omdirigeringar som ändrat inkommande länkars mål; mejl
som skickats till verkliga mottagare. Därför: noindex-kontrollen före sökkonsolen, och testdata bara i
förhandsvisningen.

## Återgång

Driftsättning: befordra föregående produktionsdriftsättning i Vercel; återställ noindex om innehållet inte får
indexeras. DNS: en behörig människa återställer posterna till filen från före bytet. Ingen session ändrar DNS.
Återgången kan ta upp till den TTL som gällde innan; vid namnserverbyte räknas också delegeringens TTL. En återgång av
driftsättningen återställer inte DNS. Skriv tid, orsak, vem som beslutade och vad som återställdes i kundmappen, och
kör provet igen före nästa försök.

Källor: [RFC 1034 §3.6 och §4.2](https://datatracker.ietf.org/doc/html/rfc1034),
[Gmail Email sender guidelines](https://support.google.com/a/answer/81126?hl=en) (lästa 2026-09-30).

## Efter lansering

Veckorna 1–2: sökkonsolens indexeringsrapport var 2–3 dag; driftkontrollen enligt `kunskap/drift.md`; månadsrutinen
enligt `kunskap/uppfoljning.md`. Lanseringen redovisas i slutrapporten med tid, driftsättning och kontrollerna ovan.
