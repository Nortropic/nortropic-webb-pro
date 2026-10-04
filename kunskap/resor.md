# Resor — briefens viktigaste besökaruppgifter som prov

Codex helhetsbedömning 2026-10-04, punkt 6: provet ska täcka kundresan, inte bara att formuläret går att skicka. Varje
toppuppgift i briefen blir en resa i `underlag/<slug>/RESOR.json`, och `kontroller/webblasare/resor.mjs` kör dem på
det slutliga bygget i provet (grinden `resor`). Normans principer är frågorna: syns handlingen, ger den återkoppling,
går ett fel att förstå och rätta.

En resa har:

- `id` (a–z, 0–9, bindestreck; versaler blir gemener) och `uppgift` i besökarens ord, ur briefens toppuppgifter.
- `niva`: `lokalt prov` (körs mot provets egen server och demomottagare), `testintegration` (mot en testmiljö hos
  tjänsten, till exempel bokningssystemets sandlåda) eller `verklig leverans` (en förfrågan som kommer fram till
  verksamheten). Bara `lokalt prov` körs i provet; de andra listas som kvar till lanseringen (`kunskap/lansering.md`).
  En okänd nivå eller vy är ett fel i filen och gör grinden röd.
- `start`: sidan resan börjar på, och `vy` (390 som standard; 768, 1440 eller 320).
- `steg`: `{"ga": "/väg"}`, `{"klicka": "väljare"}`, `{"fyll": {"väljare": "värde"}}`, `{"skicka": "formulärväljare"}`,
  `{"tangent": "Tab"}`, `{"vanta": "väljare"}`, och `{"forvanta": {…}}` för en kontroll mitt i resan. `klicka` följer
  länkar inom sajten i samma fönster; en `tel:`-, `mailto:`- eller `sms:`-länk, en länk till ett nytt fönster och en
  länk till en annan webbplats prövas med förväntan `lank`.
- `forvantat`: det synliga resultatet: `{"url": "/tack/"}` (sidans sökväg, med eller utan avslutande snedstreck),
  `{"text": "…"}` (synlig text, oavsett versaler), `{"lank": {"valjare": "…", "borjar": "tel:+46…"}}`,
  `{"synlig": "väljare"}`, `{"fel_vid_falt": "väljare"}` (fältet ogiltigt med ett synligt besked via
  aria-describedby), `{"fokus_synlig": true}`.

En väljare pekar på det första synliga elementet: en dold mobilmeny före en synlig länk fäller inte resan.
`{markering}` blir provets testmarkering, i `fyll` och i `text`. Väljarna beror på den byggda HTML:en (`#ff-namn`,
`nav a[href='/kontakt/']`): skriv resorna ur briefen i steg 2 och se över väljarna när sidorna finns.

Minst: den primära handlingen (ring, boka, offert, beställ) och den skriftliga vägen, med ett inmatningsfel och hur
besökaren rättar det. För bokning skiljs länken (lokalt: rätt adress till rätt tjänst) från en genomförd bokning
(testintegration); för kontakt skiljs formulärets godkännande (lokalt: tacksidan) från en mottagen förfrågan
(verklig leverans). Ett kontrollerat serverfel prövas där sajten har en felsida för det (byggstandarden 6.6).

Provet kör varje resa i Chromium och i WebKit, Safaris motor (390 px som Playwrights iPhone 14-profil). I WebKit
fäller sidled-spill på resans startsida resan, och i båda motorerna fäller ett JavaScript-fel under resan den.
Startsidan fotograferas i 390 px i båda motorerna (`startsida-<motor>-390.png`, med innehållets höjd, spill, laddade
typsnitt och konsolfel); granskaren får WebKit-bilden. Det är belägg för layout och JavaScript i Safaris motor, inte
för en riktig iPhone: kontrollen på riktig telefon före lansering består.

Provet skriver `prov/resor/RESOR.md` med varje steg, vad som inte höll (steget står med i skälet) och en skärmbild
per steg; granskaren får den. Resorna som står kvar till lanseringen förs in i RAPPORT.md (steg 7, punkt 12) och i
lanseringens checklista (`kunskap/lansering.md`, Före lanseringsdagen).
Rökprovets resor står i `kontroller/rokprov/RESOR.json`.
