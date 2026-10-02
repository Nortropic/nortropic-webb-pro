# Lärdomar — ägarens domar

Loop 3: ägaren tittar på en sajt och dess rapport och dömer med egna ord, i dashboardens frågeformulär eller direkt
här. Domen står ordagrant och blir automatiskt en vilande post i backloggen. Varje dom blir **en** textändring i rätt
fil (`.claude/skills/bygg-sajt/SKILL.md` eller en fil i `kunskap/`), liten nog att läsa på fem minuter. Ingen dom blir
ny mekanik.

Form:

```
## L<n> · ÅÅÅÅ-MM-DD · <slug>
**Ägarens ord:** "<ordagrant>"
**Bättre än deras?** ja/nej · **Nära referenserna?** ja/nej
**Ändring:** <fil> — <vad som ändrades> (commit <sha>)
```

## L0 · 2026-10-01 · norrglanta (historik)
**Ägarens ord:** "norrglänta är historik, den var undermålig, ai slope skit"
**Bättre än deras?** ej tillämpligt (fiktiv verksamhet) · **Nära referenserna?** nej
**Ändring:** `.claude/skills/bygg-sajt/SKILL.md` — skillen kräver "Bara de har" och en rad `Specifikt:` per sektion,
och pekar på den befintliga regeln mot slop (`kunskap/copy-kontroll.md`, `kunskap/redaktionellt-pass.md`,
`kunskap/referenser-professionella.md`).

## L1 · 2026-10-02 · lulea-snickaren

- **Skulle du sätta ditt namn på sajten och visa den för verksamheten?** Ja, efter små ändringar
- **Jämfört med verksamhetens nuvarande sajt är vår …** Mycket bättre
- **Känns den gjord för just den här verksamheten, eller som en mall?** 5
- **Om något känns som mall eller AI: peka på det. Var på sidan, och vad?** Nästan inget. Det enda som luktar mall: tjänstelistan 'Det här bygger vi' på startsidan (fyra rubriklänkar med en mening var i två spalter) och sidfotens tre spalter – korrekta men generiska mönster. Allt annat går inte att återanvända på en annan firma: byggdagboken med datum ur bilderna, '91 dagar'-axeln, loggans historia (domkyrkan och hamnkranen) på /om/, platsannonsen, omdömena ordagrant med plattform och månad. Verifierat genom att läsa all text på fem sidor + 404 och jämföra med diagnosen av nuvarande sajt i Underlag.
- **Efter fem sekunder på startsidan i mobilen: vad säger sajten till dig?** 'Tillbyggnader, nya hus, fasader och fönster i Luleå och Boden' – sedan 'firma på två personer, Dan Sandberg, snickare sedan 2009, ring och berätta, offerten kostar inget' och en röd knapp Ring 073-839 74 21. Vad, var, vem och nästa steg (A9.1) ryms i första vyn på 390 px, numret står dessutom i sidhuvudet. Det första vyn inte säger: hur jobben ser ut – inget foto syns förrän under knappen (bildens överkant ca 617 px ner, kontrollerat i 390 px-emulering). Första intrycket är 'tydlig och lugn, lite textig'.
- **Det bästa med sajten. Ett konkret ställe.** Startsidans byggdagbok 'Ett hus, från platta till tänt i fönstren': fem egna telefonbilder med datum ur bilderna (24 aug–23 nov 2021), '91 dagar'-axeln och en mening per bild. Det är bevis i stället för påstående (Fogg 2003 om trovärdighet, Cialdini socialt bevis) och svarar på 'har de gjort liknande?' utan adjektiv. Samma grepp bär /projekt/ (tre jobb med datum och klistrande textspalt på desktop). Tekniskt i samma klass: 0 kB JS, 4,3 kB CSS, en självhostad variabel font, lägsta kontrast 6,86:1, synlig fokusram 3 px på allt, CLS 0 – verifierat i webbläsaren.
- **Det sämsta med sajten. Ett konkret ställe.** Kontaktvägen utanför 07–16. Sajten har inget formulär alls, bara tel: och mailto: (verifierat: 0 <form> på fem sidor). Den som sitter med mobilen kl 21 och vill beskriva sitt jobb med en bild måste öppna en mejlklient – på en telefon utan konfigurerad mejlapp går mailto ingenstans och ingen bekräftelse ges. A6 och A9.2 förutsätter ett nästa steg som fungerar när Dan inte svarar; heuristik 7 (flexibilitet) och 1 (synlig status). Konkret småfel på samma sida: '(läst 1 oktober 2026).Läs dem på Hantverkskollen' saknar mellanslag efter punkten (startsidan, omdömessektionen, både desktop och mobil). På /om/ i 1280 px börjar h1 ca 415 px ner eftersom texten centreras mot ett stående porträtt – första vyn ser tom ut.
- **Låter texten som verksamheten?** Ja
- **rost_exempel** Håller: 'Vi kommer på avtalad tid och lämnar inte en kund innan jobbet är färdigt.' (deras egna ord). Enda som låter skrivet: 'Firman är två personer, och just nu letar den efter en tredje.' – Dan hade sagt 'vi är två och letar efter en till'.
- **De åtta dimensionerna (kunskap/referenser-professionella.md)** Hållning: Bra, Typografi: Bra, Färg: Bra, Luft och hierarki: Okej, Substans: Bra, Förtroende: Bra, Mobil ergonomi: Okej, Konsekvens: Bra
- **Hur nära referenserna som bygget valde är den?** 4
- **Var referenserna rätt valda? Vilken skulle du ha valt i stället?** I huvudsak ja: Wade Brothers (personen är firman), Bensonwood (bildtext med fakta under bilden), Vardehaugen (lugn typografi, varm bakgrund) och GOV.UK:s kontaktsida (nummer + vad man ringer om + när) besvarar de fyra frågorna, och sajten ligger i nivå med dem på bildtext och telefonmönster. Två saknas: (1) en svensk hantverkarreferens för förtroendeblocket – hur F-skatt, försäkring, org.nr och rotavdrag presenteras som kvitton utan att bli en märkesrad (t.ex. en profilsida på Hantverkskollen eller Offerta som mönster); (2) en referens för tidsaxel/byggdagbok på mobil (t.ex. en projekttråd på Byggahus) – det är sajtens bärande grepp men ingen referens prövade hur fem daterade bilder läses på 390 px.
- **Om du fick ändra en sak i hur vi bygger, vad skulle det vara?** Bygg alltid in en skriftlig förfrågningsväg som fungerar utan mejlklient: ett formulär med tre fält (namn, telefon, vad du vill bygga + valfri bild) som fungerar med vanlig POST utan JS, honeypot + tidsfälla, och en bekräftelse som säger när Dan ringer (A6.1–6.3, 6.5–6.7). Telefonen får förbli primär, men standarden ska inte tillåta att 'ring' är enda vägen. Småsaker att rätta före visning: mellanslaget ').Läs' på startsidan; favicon bara PNG (A2.3 kräver SVG + apple-touch-icon 180 px); tjänstelänkarna i 'Det här bygger vi' 21 px höga (A3.3 ≥ 24); försäkring nämns inte (A9.3 – antagande att den finns); 404-sidan har canonical mot /404/ i stället för noindex (A7.2); platsannonsen på /om/ blir inaktuell efter 30 nov 2026 (A9.4); en gemensam tjänstesida i stället för en sida per huvudtjänst (A7.5, medel). Nu-validatorn: 0 fel på fyra sidor + 404, 1 CSS-meddelande på startsidan (padding-inline med calc – troligen falskt positivt). Ej verifierat mot lokal adress: PSI, WAVE, securityheaders, produktionsheaders. Not: jämförelsen med nuvarande sajt bygger på diagnosen i Underlag (Lighthouse 41/83/96/85 mobil, axe 14 allvarliga, karusell med 'Learn More' → #, utgånget Instagramflöde), inte på eget besök av luleasnickaren.com (regel 1).
- **Hur säker är du på din dom?** Ganska säker
- **Jag valde byggdagboken (datum först, egna telefonbilder, tidsaxel) före riktningen 'Bilen' (svart linjeteckning som på skåpbilen, ingen färg, loggan uppförstorad över första vyn). Vilken hade du valt?** Byggdagboken, som den är
- **Accenten är rödfärg ur husen på bilderna, på knapp, länkar och tidsaxel. Skulle den hellre vara svart, som linjeteckningen på bilen?** Rödfärg
- **På mobil står rubriken och ringknappen först och Dans bild börjar längst ner i första vyn. Ska bilden av Dan ligga ovanför rubriken i stället?** Rubrik och knapp först, som nu
- **Startsidans byggdagbok har fem bilder och tar ungefär halva sidan på mobil. Fem eller tre?** Tre
- **Deras tio nästan identiska ortsidor (Snickare Boden, Fasadbyte Luleå …) syns i sök. Jag tog bort dem och föreslår 301 till de nya sidorna. Rätt?** Ja, ta bort och led vidare
- **Skulle du visa den här för Dan Sandberg som den är?** Ja, efter små ändringar

**Ändring:** väntar (backlog B-20261002-dom-l1-lulea-snickaren-bygg-alltid-in-en-skriftl)
