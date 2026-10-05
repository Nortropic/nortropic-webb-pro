---
id: B-20261003-a-b-med-alternativet-ingen-nar-min-ribba-och-ett
status: vilande
kalla: bevakning
kallref: Codex bedömning av den visuella nivån, 2026-10-03
skapad: 2026-10-03
prio: normal
andrad: 2026-10-05T06:55Z
---
# A/B med alternativet 'ingen når min ribba' och ett jämförande försök på tre befintliga kundfall

**Varför:** Codex 2026-10-03: jämför dagens flöde med en version med kalibrerade ankare, starkare prototyper och möjlighet att förkasta alla riktningar, på tre befintliga fall med samma material och budget, blindat och i slumpad ordning. Utfallet pekar på flaskhalsen: underlaget, urvalet, överföringen till bygget eller kundmaterialet.

**Ordning (Codex 2026-10-03):** steg 4, blind jämförelse på undanhållna kundfall, efter referensöverföringen, prototyperna och överlämningen; före fler referenstjänster och plattformsprov.

**Förslag:** Dashboardens Jämförelser får valet 'ingen når min ribba' bredvid A, B och lika, och LARDOMAR.md skriver det. När kalibreringen och ateljéns lägstanivå är införda körs tre befintliga fall som A/B (kontroller/ab.py) med en variabel i taget; mät godkännandegrad, granskarnas falska godkännanden och kostnad per godkänt bygge. Ordningen i metodprovet (Codex 2026-10-03): först referensöverföringen, sedan överföringen prototyp till bygge. Två eller tre kundfall hålls undan och används aldrig när instruktionerna justeras; förbättringen ska hålla också på dem (Anthropic om mänsklig kalibrering och upprepade försök: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

**Klart när:** Jämförelser har valet "ingen når min ribba" och LARDOMAR-raden bär det; tre blinda jämförelser med en variabel i taget, på fall byggda genom skapandeflödet, är dömda i dashboarden.

**Vilande (2026-10-05):** Avstämt 2026-10-05: valet saknas i Jämförelser (dashboard/server.py ab_val godtar bara A, B eller lika); ateljén och vyn Prototyp kan redan förkasta. Implementationen ingår i paketet före nästa helbygge; jämförelserna görs på fall byggda genom skapandeflödet (de tre gamla fallen är arkiverade), och måtten tas ur autonomi.py och kalibrering.py. Färdigkriteriet omskrivet i avstämningen; tidigare: "Valet finns i dashboarden och sparas; tre jämförelser är körda och dömda; LARDOMAR.md har måtten och ett beslut om vilken ändring som behålls."
