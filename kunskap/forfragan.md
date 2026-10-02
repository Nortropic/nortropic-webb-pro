# Skriftlig förfrågan: formuläret och dess mottagare

Ägarens dom L1 (2026-10-02): "Bygg alltid in en skriftlig förfrågningsväg som fungerar utan mejlklient: ett formulär
med tre fält (namn, telefon, vad du vill bygga + valfri bild) som fungerar med vanlig POST utan JS, honeypot +
tidsfälla, och en bekräftelse som säger när Dan ringer (A6.1–6.3, 6.5–6.7). Telefonen får förbli primär, men
standarden ska inte tillåta att 'ring' är enda vägen." Domarna L2 och L3 sa samma sak. Byggstandardens avsnitt 6
gäller; teorin står i `kunskap/teoretisk-grund.md` (Jarrett & Gaffney, Wroblewski, GOV.UK).

## I varje bygge (demo)

- **Formuläret** är mallens `src/components/Forfragan.astro`, på kontaktsidan och gärna som en sektion där den
  primära handlingen står. Telefonen förblir den primära handlingen; formuläret är vägen när ingen svarar.
- **Fälten:** namn, telefon, meddelande med etiketten i verksamhetens ord ("Vad vill du bygga?"), och en valfri bild.
  Det valfria märks "(valfritt)"; resten krävs. Inga fler fält utan skäl ur briefen.
- **Fällorna** ändras inte: honeypoten `webbplats` (dold, `tabindex="-1"`) och tidsfällan `fylltid`, varaktigheten i
  millisekunder från laddning till inskick mätt på webbläsarens klocka (`kunskap/formularsakerhet.md`, princip b).
- **Integritetstexten** vid knappen länkar till `/integritet/`. Integritetssidan anger personuppgiftsansvarig
  (verksamhetens namn, org.nr och kontakt), ändamål (svara på förfrågan), rättslig grund (berättigat intresse eller
  avtal), lagringstid, rättigheter och vart man vänder sig.
- **Tacksidan** `/tack/` har noindex och säger vad som händer härnäst och när, ur underlaget ("Lars ringer upp inom en
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

## Vid lansering (Vercel-steget, väntar)

En serverfunktion på `/api/forfragan` tar över med samma kontrakt:

1. Bara POST; multipart eller urlencoded; högst 10 MB, bara bildtyper i `bild`.
2. Validera igen på servern: namn 1–100 tecken, telefon 6–40 tecken med siffror, meddelande 1–4000 tecken.
3. Honeypot ifylld: svara 303 till `/tack/` utan att skicka. Tidsfälla: `fylltid` under 1500 ms: samma sak. Tomt
   eller 0 (ingen JavaScript, direkt POST) godtas; fältet är ett botfilter, inte autentisering. Jämför aldrig en
   klientstämpel med serverns klocka.
4. Begränsning: högst 3 inskick per 10 minuter och IP-adress; Turnstile om spam ändå kommer igenom.
5. Mejl till verksamheten via en dedikerad tjänst med SPF, DKIM och DMARC på domänen; allt innehåll escapas i mallen;
   bilden som bilaga.
6. Svara 303 till `/tack/` först när tjänsten har accepterat mejlet. Vid fel: 303 till `/fel/`, som visar telefonnumret
   som väg vidare. Fel loggas utan personuppgifter.
7. Konverteringshändelser för skickad förfrågan och telefonklick, i kakfri mätning.
