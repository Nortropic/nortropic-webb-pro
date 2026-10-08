---
id: B-20261003-fasta-lister-och-klibbiga-sidhuvuden-star-i-flod
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Frontend Focus 759 (nyhetsbrev 2026-09-23) + Polypane, Matuzovic, WebKit Safari 27
skapad: 2026-10-03
prio: normal
steg: bygg-sajt steg 5.3 och 6; byggstandarden 3.3 och 4.2; kontroller/webblasare/inspektera.mjs
commit: dd60841
andrad: 2026-10-08T15:30Z
---
# Fasta lister och klibbiga sidhuvuden står i flödet när vyn är lägre än 500 px (400 % zoom), rotskrollaren bevaras, och lata bilder får sizes="auto" med reserv

**Varför:** Kirurgens dom: ta in. Vid 400 % zoom (WCAG 1.4.10) är den inre vyn 320×180 px på en vanlig skärm, och vår fasta list med Ring och Skriv (48–63 px i byggena) täcker då upp till en tredjedel av skärmen; provet ser det inte eftersom reflow prövas i 320×640. Matuzovic visar lösningen (fixed bara i @media (min-height: 31.25rem)), Polypane visar hur html/body med height: 100 % och overflow tyst flyttar skrollningen från rotskrollaren (förlorad skrollposition, tangentbordsskroll, adressfält, utskrift), och Safari 27 gör sizes="auto" på lata bilder gångbart i Chrome och Safari.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md rad 279–281, efter 'skymmer inte sidfotens sista länk': 'Listen och ett klibbigt sidhuvud är fasta bara när vyn är minst 500 px hög, @media (min-height: 31.25rem); i lägre vyer (400 % zoom) står de i flödet.' kunskap/byggstandard.md 3.3 (rad 48), tillägg: 'Fasta och klibbiga element bara i vyer minst 500 px höga. Sidan skrollar i rotskrollaren: html och body får ingen fast höjd med overflow; spill i sidled döljs med overflow-x: clip, inte hidden; min-height: 100svh, aldrig height: 100vh.' Prövas av: standard (K: grep i CSS efter html/body med height och overflow, info) och inspektionen: kontroller/webblasare/inspektera.mjs rad 60 tar en andra reflowbild i 320×180 (vy-<vy>-reflow320x180.png) och mäter andelen av höjden som fasta element täcker; stilrapporten varnar över 25 %. kunskap/byggstandard.md 4.2 (rad 59), tillägg: 'Bilder under första vyn med loading="lazy" får sizes="auto, <lista>" så att webbläsaren mäter bredden själv (Chrome 126, Safari 27; Firefox kontrolleras mot MDN) och äldre webbläsare använder listan.' Mallens README rad 14–15 får samma mening. Skriv med writing-for-agents.

**Klart när:** SKILL.md och byggstandarden har raderna; inspektionen skriver reflow320x180-bilden och måttet; stilrapporten varnar på ett bygge där listen är fast i 320×180 och tiger när den står i flödet; standard_kontroll ger info när html eller body har height tillsammans med overflow; kontroller/rokprov.sh slutar grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord i alla delar (text, inspektion, stilrapport, standard). Tas efter paketet; textdelarna kan läggas på byggstandarden tillsammans med cqi-posten.
