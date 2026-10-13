# Granskningsfrågor för den kritiska granskaren

Frågorna som ds_kritik (designfasen, `kunskap/claude-design.md`) och den blinda kritiken besvarar ur bilderna av en
version i 390, 768 och 1440, efter kvalitetskraven (`kunskap/designregler.md`) och byggstandarden. Underlaget är
researchpasset 2026-10-12 (ägarens tillägg om best practice; källorna med datum står där och i slutrapporten). En
modells blick på bilder är en expertbedömning, inte en mätning av hur människor uppfattar sidan på 50 ms, och domen är
en AI-bedömning, aldrig ägarens. Ägarens kvalitetsribba går före (`underlag/niva/MATTSTOCK.md`, privat): nivån är satt
genom ägarens Apple/Nike-besked 2026-10-12, precisionen på den nivån och inte ägarens stil.

**K** = källan säger det. **T** = vår tolkning av källan.

1. Första vyn i 1440 och 390: hur många element konkurrerar (bilder, rubriker, knappar, märken, färgfält)? Ange antalet
   och bedöm lugn mot rörighet. (Tuch m.fl. 2012, Lindgaard m.fl. 2006; räkningen som mått: T)
2. Känns första vyn igen som en sajt för den här sortens verksamhet, eller måste besökaren lära sig en ovan struktur? Vad
   vinner verksamheten i så fall? (Tuch m.fl. 2012, prototypikalitet: T)
3. Sitter särprägeln i verksamhetens eget material, ord, typografi och bild, eller i en ovan struktur? (Tuch m.fl. 2012;
   Awwwards Creativity: T)
4. Finns ytslarv: stavfel, ojämn linjering, avhuggen text, oskarpa eller felbeskurna bilder, knappar som skiljer sig
   mellan bredderna? (Fogg m.fl. 2003; NN/g, Trustworthiness in Web Design 2016: K)
5. Syns namn, område, telefon, org.nr, omdömen med källa och egna bilder av arbetet och personerna utan att man letar? I
   vilken ruta syns de först? (Fogg & Tseng 1999; NN/g 2016: K; ordningen: T)
6. Står pris, prisexempel eller hur priset sätts, och svarstiden? (NN/g 2016; GOV.UK, Contact a department: K)
7. Går märken, sigill och omdömen att verifiera (utfärdare, länk, källa)? Baymards nyare studie fann att även ett
   hemgjort sigill gav förtroende, så bedöm verifierbarheten och sanningen, inte bara utseendet. (Baymard, Site seal
   trust, den nyare studien; marknadsföringslagen: T)
8. Formuläret i 390: står en synlig etikett ovanför varje fält, utan platshållare som etikett? Är det valfria märkt
   ("valfritt", GOV.UK; NN/g märker det obligatoriska och Baymard båda), står ett fält per rad, säger telefonfältet
   varför och när ni ringer, och säger knappen vad som händer? (GOV.UK Text input och Question pages; NN/g; Baymard: K)
9. Formuläret med felen framkallade: finns en sammanfattning med länkar, text vid varje fält och mer än bara färg?
   (GOV.UK Error summary och Error message; NN/g; WCAG 1.4.1: K)
10. Går sidan att förstå genom att bara läsa rubriker och fetstil? Finns textväggar? (NN/g, F-mönstret 2017; Krug 2014: K)
11. Ser tel-länken och knappen ut som handlingar i 390? (Norman 2013; Krug 2014: K)
12. Håller den typografiska hierarkin, linjeringen, rytmen och bildbehandlingen samma nivå i 768 som i 390 och 1440?
    (Awwwards Design: T)
13. Är navigationen nåbar, klickytorna stora nog och sidan utan sidledsspill i 768? (Awwwards Usability: T; WCAG 2.5.8
    och Nortropics 44 px: K)
14. Om sidan är vacker: finns ändå en funktionsbrist? Döm estetik och funktion var för sig. (Hassenzahl & Monk 2010;
    NN/g, The Aesthetic-Usability Effect 2024, efter Kurosu & Kashimura 1995: K)
15. Är första vyn lugn för en besökare med ett akut problem, eller drar dekoren uppmärksamheten? (Norman 2004: T)
16. Känns sidan premium eller basic? Peka ut var detaljer saknas: interaktiva element utan läge och övergång, en
    första vy utan signatur, bilder som står stilla där de kunnat leva, sektioner som kunnat utgå från ett 21st-block,
    och mikrotypografi. Apple och Nike är ribban för detaljtätheten, inte för stilen. (Ägarens dom 2026-10-13 i
    `underlag/niva/MATTSTOCK.md`; frågorna D1–D6 i `kunskap/precision.md`: K)

## Vad forskningen visar och inte visar

| Källa | Visade | Visar inte |
|---|---|---|
| Lindgaard m.fl. 2006 | Bedömningen av hur tilltalande en hemsida är korrelerade högt mellan 50 och 500 ms visning | Något om uppgifter, interaktion eller kontakt |
| Lindgaard m.fl. 2011 | Trovärdighet och användbarhet bedöms också snabbt men stabiliseras långsammare; tilltalandet färgar dem | Fulltexten är inte läst |
| Tuch m.fl. 2012 | Låg visuell komplexitet och hög prototypikalitet (känns igen i sin kategori) bedömdes vackrast, redan vid 17–50 ms | Något annat än estetiska betyg |
| Fogg m.fl. 2003 | 46 % av deltagarnas kommentarer om trovärdighet gällde design och utseende | En effektstorlek eller köp; webben 2002 |
| Hassenzahl 2003–2010 | Pragmatisk och hedonisk kvalitet är skilda; skönhet påverkar upplevd användbarhet indirekt | Tjänstesajter; instrumentet kräver verkliga användare |
| Kurosu & Kashimura 1995 (via NN/g) | Upplevd användbarhet följde skönheten mer än den faktiska användbarheten | Orsakssamband |

**Awwwards** (bedömningssidan, läst 2026-10-12): design 40 %, användbarhet 30 %, kreativitet 20 %, innehåll 10 %;
minst 18 jurymedlemmar, de tre mest avvikande betygen stryks. Kriterierna definieras inte närmare där, och priset säger
inget om affärseffekt. Vår tolkning (T): "Awwwards-nivå" betyder hantverket i design och användbarhet med verksamhetens
eget material; kreativitet betyder egna, motiverade beslut, inte nyhet för sin egen skull, och Tuchs fynd om
prototypikalitet talar emot ett oreflekterat nyhetskrav. Ägaren avgör ribban.
