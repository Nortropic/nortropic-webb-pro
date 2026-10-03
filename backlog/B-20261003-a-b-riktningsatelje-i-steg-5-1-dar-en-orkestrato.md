---
id: B-20261003-a-b-riktningsatelje-i-steg-5-1-dar-en-orkestrato
status: vilande
kalla: dom
kallref: ägaren 2026-10-03 (samtal om Claude Design)
skapad: 2026-10-03
prio: hog
steg: 5.1 (riktning)
---
# A/B: riktningsateljé i steg 5.1, där en orkestrator (Fable 5.1, max) tar fram 3–4 riktningar som style tiles och första vyer med riktigt innehåll och en fristående domare väljer före bygget

**Varför:** Ägaren 2026-10-03 om Claude Design: "jag gillar det värdefulla i idén och tanken att claude i webbläsaren med fable 5.1 max får styra som en slags orcestraaor claude design, ta fram flera riktningar enligt best practices" och "ja, gör detta". Claude i Chrome kan inte styra Claude Design (inget API, claude.ai blockerat för tillägget, kräver övervakning), men det värdefulla, divergens med flera riktningar sida vid sida och ett val med omdöme före bygget, går att göra obevakat i flödet. I dag skrivs fyra riktningar men bara den valda byggs (sedan 2026-10-02 renderas också tvåan); ägaren valde som byggd i alla tre domar när alternativet bara fanns i ord.

**Förslag:** kontroller/atelje.py <slug>, bakom NWP_ATELJE (av som standard): (1) divergera: en session med NWP_ATELJE_MODELL (Fable 5.1) och effort max skriver 3–4 riktningar som ser och känns olika längs en namngiven axel, var och en som kastbar sida src/pages/atelje-N/ med style tile (färger, typsnitt, knappar, bildbehandling) och första vy ur INNEHALL.md och verksamhetens bilder, och underlag/<slug>/atelje/RIKTNINGAR.md; (2) verktyget bygger och fotograferar varje sida i 390 och 1440; (3) konvergera: en fristående domare (samma modell, eget sammanhang) jämför bilderna mot toppuppgifterna, ägarens domar och originalitet och skriver VAL.md med vald riktning och vad som lånas från de andra; (4) sidorna tas bort och riktningsfrågan i FRAGOR.json får en bild per riktning. bygg-sajt steg 5.1 kör verktyget när NWP_ATELJE är på och skriver KONCEPT.md ur valet; tvåan behövs då inte. ab.py får variabeln atelje.

**Klart när:** A/B körd (minst två par på samma sorts verksamhet med och utan ateljé, blinda val i dashboarden) och redovisad med ägarens val, om ägaren valde bort den byggda riktningen, granskarnas originalitet och kostnad i Fable- och Opus-kvot per bygge; beslut om NWP_ATELJE blir standard eller tas bort
