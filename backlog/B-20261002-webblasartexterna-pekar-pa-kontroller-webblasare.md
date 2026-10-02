---
id: B-20261002-webblasartexterna-pekar-pa-kontroller-webblasare
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · browser-use/browser-use
skapad: 2026-10-02
prio: normal
steg: 6 (provet läser kunskap/webblasare.md) och lansering
commit: 3239130
andrad: 2026-10-02T15:36Z
---
# Webbläsartexterna pekar på kontroller/webblasare/ och säger att besökarverktyget besok.mjs saknas här

**Varför:** Egen innovation vid bedömningen av browser-use (nej): kunskap/webblasare.md, som bygget läser i steg 6 (bygg-sajt/SKILL.md rad 242), anger verktygen under verktyg/webblasare/ och beskriver en avskärmad besökare i besok.mjs; i det här repot ligger verktygen i kontroller/webblasare/ och besok.mjs finns inte. Samma döda sökväg står i bygge-referens.md rad 55, formularsakerhet.md rad 37, lansering.md rad 68 och tre hjälptexter i kontroller/prelaunch.py (rad 141, 241, 496), så bygget kan leta efter verktyg som inte finns.

**Förslag:** kunskap/webblasare.md: verktyg/webblasare/ byts mot kontroller/webblasare/ (rad 4, 76, 91); i tabellen rad 15-16 och stycket Körbevis (rad 57-72) skrivs att besok.mjs och test_webblasare.py hörde till Digitala och inte finns här, och att den avskärmade uppgiftsvägen i det här repot är femsekunderstestet och granskarens kognitiva genomgång. Samma sökvägsbyte i kunskap/bygge-referens.md rad 55, kunskap/formularsakerhet.md rad 37, kunskap/lansering.md rad 68 och hjälptexterna i kontroller/prelaunch.py rad 141, 241, 496 (bara strängar, ingen logik); rökprovet grönt.

**Klart när:** grep -rn 'verktyg/webblasare' kunskap kontroller --include='*.md' --include='*.py' ger inga träffar, webblasare.md nämner inte besok.mjs som ett verktyg här, och kontroller/rokprov.sh slutar grönt.

**Klar (2026-10-02):** sökvägar rättade, besok.mjs märkt som Digitalas
