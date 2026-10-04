---
id: B-20261004-skillkandidater-dembrandt-extract-design-md-skill-creator-dogfood
status: vilande
kalla: bevakning
kallref: Codex tillägg 2026-10-04 (skillkandidater)
skapad: 2026-10-04
prio: mellan
andrad: 2026-10-04T21:06Z
---
# Skillkandidater i prioritetsordning: Dembrandt extract-design, Google extract-design-md, skill-creator, dogfood, performance, customer-research

**Varför:** Codex fann kandidater som gör referenser användbara i koden, bevarar den valda designen och verifierar hela kundupplevelsen. Dembrandt extract-design extraherar beräknade CSS-värden (färger, typografi, avstånd, komponenttillstånd) från levande sajter och exporterar tokens och DESIGN.md; ett tidigare avslag gällde ett annat verktyg med en äldre Dembrandt-motor och vilade på det upphävda kopieringsförbudet (REGISTER.md:5081). Google Labs extract-design-md läser frontendkod och beskriver dess designsystem, rätt för steget från vinnande prototyp till designspecifikation. Skill-creator prövar när skills aktiveras och jämför mot en baslinje; den sköts upp tills verktygslådan var större (REGISTER.md:933), och den förutsättningen har ändrats. Vercel dogfood utforskar användarresor och dokumenterar reproducerbara fel; Addy Osmani performance har kedjan mätning, orsak, ändring, ommätning; Corey Haines customer-research bearbetar stora underlag. Inför lanseringar: Coreys analytics och marketing-loops.

**Förslag:** Ordning: (1) prototypens kodöverföring (ateljén, levererad 2026-10-04); (2) Dembrandt prövas på referensunderlaget genom det avgränsade referenssteget, jämfört med vår egen extraktion (kontroller/webblasare/extrahera.mjs) och kontrollerat mot skärmbilderna, och kravet är att extraktionen leder till valda roller, CSS och komponenter i bygget; (3) extract-design-md körs på en accepterad prototyp (ateljéns vinnare) och kontrolleras mot renderingen; aldrig på ett svagt bygge; (4) dogfood med egna testbyggen och testmottagare, täckning av besökaruppgifterna, utan originalets 5–10 fynd (en fyndkvot styr granskaren fel); (5) performance med mätmetodens stödmaterial; (6) customer-research när underlaget är stort. Skill-creator används parallellt utanför kundbyggena för aktiveringstester mot baslinje, med blindningen kvar. Varje kandidat följer intagskraven (posten om intagsmetoden).

**Klart när:** Dembrandt och extract-design-md har körts i var sitt avgränsat försök med belägg (vad som extraherades, vad som valdes, vad som fanns kvar i bygget); dogfood-resor finns som prov; skill-creator har mätt aktiveringen av minst de installerade better-* och humanizer mot baslinjen.
