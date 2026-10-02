---
id: B-20261002-dom-l1-lulea-snickaren-bygg-alltid-in-en-skriftl
status: klar
kalla: dom
kallref: LARDOMAR.md L1
skapad: 2026-10-02
prio: normal
sar: L1
commit: bc5360f
andrad: 2026-10-02T12:10Z
---
# Dom L1 (lulea-snickaren): Bygg alltid in en skriftlig förfrågningsväg som fungerar utan mejlklient: ett formulär med

**Varför:** Skulle du sätta ditt namn på sajten och visa den för verksamheten?: Ja, efter små ändringar; Jämfört med verksamhetens nuvarande sajt är vår …: Mycket bättre; Känns den gjord för just den här verksamheten, eller som en mall?: 5; Det sämsta med sajten. Ett konkret ställe.: Kontaktvägen utanför 07–16. Sajten har inget formulär alls, bara tel: och mailto: (verifierat: 0 <form> på fem sidor). Den som sitter med mobilen kl 21 och vill beskriva sitt jobb med en bild måste öppna en mejlklient – på en telefon utan konfigurerad mejlapp går mailto ingenstans och ingen bekräftelse ges. A6 och A9.2 förutsätter ett nästa steg som fungerar när Dan inte svarar; heuristik 7 (flexibilitet) och 1 (synlig status). Konkret småfel på samma sida: '(läst 1 oktober 2026).Läs dem på Hantverkskollen' saknar mellanslag efter punkten (startsidan, omdömessektionen, både desktop och mobil). På /om/ i 1280 px börjar h1 ca 415 px ner eftersom texten centreras mot ett stående porträtt – första vyn ser tom ut.; Om något känns som mall eller AI: peka på det. Var på sidan, och vad?: Nästan inget. Det enda som luktar mall: tjänstelistan 'Det här bygger vi' på startsidan (fyra rubriklänkar med en mening var i två spalter) och sidfotens tre spalter – korrekta men generiska mönster. Allt annat går inte att återanvända på en annan firma: byggdagboken med datum ur bilderna, '91 dagar'-axeln, loggans historia (domkyrkan och hamnkranen) på /om/, platsannonsen, omdömena ordagrant med plattform och månad. Verifierat genom att läsa all text på fem sidor + 404 och jämföra med diagnosen av nuvarande sajt i Underlag.; Om du fick ändra en sak i hur vi bygger, vad skulle det vara?: Bygg alltid in en skriftlig förfrågningsväg som fungerar utan mejlklient: ett formulär med tre fält (namn, telefon, vad du vill bygga + valfri bild) som fungerar med vanlig POST utan JS, honeypot + tidsfälla, och en bekräftelse som säger när Dan ringer (A6.1–6.3, 6.5–6.7). Telefonen får förbli primär, men standarden ska inte tillåta att 'ring' är enda vägen. Småsaker att rätta före visning: mellanslaget ').Läs' på startsidan; favicon bara PNG (A2.3 kräver SVG + apple-touch-icon 180 px); tjänstelänkarna i 'Det här bygger vi' 21 px höga (A3.3 ≥ 24); försäkring nämns inte (A9.3 – antagande att den finns); 404-sidan har canonical mot /404/ i stället för noindex (A7.2); platsannonsen på /om/ blir inaktuell efter 30 nov 2026 (A9.4); en gemensam tjänstesida i stället för en sida per huvudtjänst (A7.5, medel). Nu-validatorn: 0 fel på fyra sidor + 404, 1 CSS-meddelande på startsidan (padding-inline med calc – troligen falskt positivt). Ej verifierat mot lokal adress: PSI, WAVE, securityheaders, produktionsheaders. Not: jämförelsen med nuvarande sajt bygger på diagnosen i Underlag (Lighthouse 41/83/96/85 mobil, axe 14 allvarliga, karusell med 'Learn More' → #, utgånget Instagramflöde), inte på eget besök av luleasnickaren.com (regel 1).

**Förslag:** Läs domen i LARDOMAR.md (L1) och kunder/lulea-snickaren/DOM.json. Gör en textändring i skillen bygg-sajt eller en fil i kunskap/ som svarar mot det ägaren pekar på. En ändring, liten nog att läsa på fem minuter.

**Klart när:** Ändringen är committad och raden Ändring under L1 i LARDOMAR.md pekar på commiten.

**Klar (2026-10-02):** formulär, tacksida, integritetssida och demomottagare i varje bygge; mottagaren vid lansering i kunskap/forfragan.md
