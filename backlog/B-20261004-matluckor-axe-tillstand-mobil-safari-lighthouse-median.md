---
id: B-20261004-matluckor-axe-tillstand-mobil-safari-lighthouse-median
status: klar
kalla: bevakning
kallref: Codex helhetsbedömning 2026-10-04 punkt 7
skapad: 2026-10-04
prio: mellan
commit: 1058556
andrad: 2026-10-04T23:25Z
---
# Mätluckor: axe på interaktionstillstånd, belägg för mobil Safari, Lighthouse med fastställd metod och representativ mätning

**Varför:** Axe körs efter sidnavigation utan att menyn öppnas eller formulärfel framkallas (axe.mjs:39). Webbläsarvägen är Chromium med emulerade mobilvyer och ger inget belägg för verklig mobil Safari (gemensamt.mjs:4). Lighthouse mäts om vid underkänt och bästa prestandamätningen gäller (lighthouse.mjs:62), vilket kan ge en optimistisk bild.

**Förslag:** Axe körs också med menyn öppen och med framkallade formulärfel (tillstånden finns redan i inspektera.mjs). Lighthouse: metoden fastställs före körningen (antal mätningar, median av prestandan, spridningen redovisad), inte bästa av flera. Mobil Safari: WebKit via Playwright som andra motor för startsidan och formuläret (belägg för layout och JavaScript, inte för riktig iOS), och den mänskliga kontrollen på riktig iPhone före lansering behålls som gräns; W3C: ett verktyg ensamt avgör inte full tillgänglighet.

**Klart när:** Provet redovisar axe per tillstånd, Lighthouse som median med spridning, och ett WebKit-pass; metoden står i kvittot före körningen.

**Klar (2026-10-04):** axe --tillstand=meny,formularfel; Lighthouse METOD.json och median av tre i mobil på representativa sidor med spridning; resor i Chromium och WebKit; oberoende granskning, 5 defekter rättade
