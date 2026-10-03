---
id: B-20261003-mobilvyn-390-px-provas-ocksa-i-webkit-playwright
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Frontend Focus 759 (nyhetsbrev 2026-09-23) + Polypane, Matuzovic, WebKit Safari 27 (egen innovation)
skapad: 2026-10-03
prio: normal
steg: bygg-sajt steg 6 (prov); kontroller/webblasare/, kontroller/stil.mjs
---
# Mobilvyn 390 px prövas också i WebKit (Playwrights webkit), eftersom iPhone är Safari och alla våra webbläsarprov i dag körs i Chromium

**Varför:** Egen innovation ur Safari 27-noterna (Safari MCP låter agenten se sin kod i Safari). Alla våra prov (sida.mjs, stil.mjs, inspektera via gemensamt.mjs, axe.mjs, lighthouse.mjs) renderar i Chromium, och ordet Safari eller WebKit finns inte i byggstandarden, GRANSKARE.md eller bygg-sajt; byggena är mobil-först och mobilen är i praktiken Safari, så ett typsnitt, en details-meny eller en hash-CSP som bara prövats i Chromium kan se annorlunda ut hos kunden. Playwright 1.63.0 (redan pinnad) bär WebKit utan nya npm-beroenden; Safari MCP kräver Safari-inställningar och en inloggad Mac-session och passar inte obevakade byggen.

**Förslag:** kontroller/webblasare/gemensamt.mjs rad 74: motorn väljs med --motor webkit|chromium (standard chromium); inspektera.mjs tar vy-390-forsta i båda motorerna när webkit finns installerad och skriver vy-390-forsta-webkit.png bredvid; PROV.md listar skillnader i sidhöjd, horisontellt spill, konsolfel och typsnitt (document.fonts) mellan motorerna som information. kunskap/webblasare.md rad 4–6: WebKit-binären hämtas en gång av ägaren med Playwrights install-kommando för webkit (ingen körning i bygget); saknas den hoppar provet över passet och säger det. GRANSKARE.md: granskaren läser webkit-bilden när den finns. Mät först på ett dömt bygge (lulea-snickaren-aby) om passet hittar något Chromium inte visar; gör det inte det, stanna vid skärmbilden.

**Klart när:** prova.py --snabb på ett bygge ger vy-390-forsta-webkit.png och en skillnadsrad i PROV.md när webkit är installerad, och ett tydligt 'webkit saknas, passet hoppat över' annars; kontroller/rokprov.sh slutar grönt i båda lägena.
