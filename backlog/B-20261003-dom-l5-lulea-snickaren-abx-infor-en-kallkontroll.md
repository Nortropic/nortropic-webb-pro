---
id: B-20261003-dom-l5-lulea-snickaren-abx-infor-en-kallkontroll
status: klar
kalla: dom
kallref: LARDOMAR.md L5
skapad: 2026-10-03
prio: normal
sar: L5
commit: 0ba099e
andrad: 2026-10-03T09:50Z
---
# Dom L5 (lulea-snickaren-abx): Inför en källkontroll för varje påstående som nämner en tredje part: ett omdöme får bara e

**Varför:** Skulle du sätta ditt namn på sajten och visa den för verksamheten?: Ja, efter små ändringar; Jämfört med verksamhetens nuvarande sajt är vår …: Mycket bättre; Känns den gjord för just den här verksamheten, eller som en mall?: 5; Det sämsta med sajten. Ett konkret ställe.: Omdömesraden på startsidan: 'Tre omdömen på Reco, alla 5 av 5 … Läs dem på Hantverkskollen' – två plattformar i en mening, och tre byggen av samma firma säger nu tre olika saker (Hantverkskollen / Reco / Hitta.se). Ett faktafel i förtroendesektionen är det värsta stället att ha det på (A9.4, heuristik 4). Näst sämst: mobilens sidhuvud på 160 px med fem menylänkar i två rader före det röda fältet, och inget foto förrän under vecket – jämfört med aby (87 px sidhuvud, foto i första vyn) kostar det en halv skärm. Saira på 99 kB är tyngst av byggenas fonter (A4.3).; Om något känns som mall eller AI: peka på det. Var på sidan, och vad?: Nästan inget. Det enda som kan kallas mönster är de tre tjänstesidornas identiska ordning (rött fält, daterad bildserie, ett avsnitt med bild, 'Vad det kostar', rött slutfält) – men formen bär tre olika jobb med egna datum och bilder, så jag räknar det som konsekvens, inte mall. Det som däremot inte låter som verksamheten är omdömesraden på startsidan: 'Tre omdömen på Reco, alla 5 av 5, läst 2 oktober 2026. Läs dem på Hantverkskollen' – två plattformar i samma mening ser ut som ett skarvfel i bygget. Verifierat genom att läsa all text på sju sidor + 404 (2 och 3 oktober, sajten oförändrad sedan 2 okt 14:17).; Om du fick ändra en sak i hur vi bygger, vad skulle det vara?: Inför en källkontroll för varje påstående som nämner en tredje part: ett omdöme får bara en plattform, och den ska stämma med länken (Reco, Hantverkskollen och Hitta.se säger nu olika saker i tre byggen av samma firma). Samma princip gäller adressen – där gjorde bygget rätt som dolde den och beställde svaret när deras sajt och Bolagsverket säger olika (och den ena är en hemadress); i A/B-valet i går räknade jag avsaknaden av adress mot A utan att känna till det, och med motiveringen här ändrar jag mig. Konkret före visning: rätta omdömesraden; korta mobilens sidhuvud (två rader menylänkar ger 160 px – ett ord per länk på en rad); låt det röda fältet sluta före Trundön-bilderna (femsekunderstestet såg att intro och exempel flöt ihop); subsetta eller byt Saira (99 kB); lägg in försäkring när svaret kommer (beställd, inte påhittad – rätt). Verifierat 2–3 okt: 0 valideringsfel på sju sidor + 404, CLS 0, kontrast lägst 5,73:1, inga tryckytor under 24 px, skip-länk och fokusram, formulär med honeypot + tidsfälla, integritetssida, 404 noindex, hash-CSP i meta, prefers-reduced-motion. Ej verifierat lokalt: PSI, WAVE, securityheaders, produktionsheaders, vilken plattform omdömena faktiskt ligger på (regel 1). Not: jämförelsen med nuvarande sajt bygger på diagnosen i Underlag (Lighthouse mobil 69, LCP 7 s, 3,6 MB, 107 konsolfel, 15 886 px lång mobilsida, 'Learn More' ×6), inte eget besök.

**Förslag:** Läs domen i LARDOMAR.md (L5) och kunder/lulea-snickaren-abx/DOM.json. Gör en textändring i skillen bygg-sajt eller en fil i kunskap/ som svarar mot det ägaren pekar på. En ändring, liten nog att läsa på fem minuter.

**Klart när:** Ändringen är committad och raden Ändring under L5 i LARDOMAR.md pekar på commiten.

**Klar (2026-10-03):** tredje part med källa och samma länk; adress.publik false när källorna säger olika
