---
id: B-20261008-kompetenspassens-genomfort-status-ska-bygga-pa-o
status: klar
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#C4
skapad: 2026-10-08
prio: normal
steg: main: kontroller/kandidater.py, kontroller/kompetens.py, dashboard/index.html
commit: 20e4f61
andrad: 2026-10-09T08:16Z
---
# Kompetenspassens genomfört-status ska bygga på observerade anrop, inte bara läskvitto och sessionens egen lista

**Varför:** Skissens pass märks genomfört när kärnan är läst (ett läskvitto), och rörelse-/granskningspassen när sessionens egen lista beteende_provat är ifylld. Metodkartan lovar att en verktygs- eller MCP-uppgift är genomförd först genom ett faktiskt anrop med kontrollerat resultat. GR-20261008-r117-claude#C4 rättar ordvalet i vyn och kräver bilder för beteendena; kravet på minst ett observerat använt verktyg per pass återstår.

**Förslag:** genomford för rörelse/granskning kräver dessutom minst ett verktyg i rollens tilldelning med tillståndet använt med resultat (kompetens.verktygstillstand); skissens pass får ett eget fält (karnan_last) i stället för genomford.

**Klart när:** Ett pass utan observerat verktygsanrop är ej genomfört i STATUS.json, REDOVISNING.md och dashboarden; prov_rorelse och prov_skisskritik prövar det.

**Pagar (2026-10-09):** Återöppnad 2026-10-09: GR-20261009-metod-till-resultat-codex#F03 (Codex, reproducerat mekaniskt fel): när också sista specialistförsöket läste kärnan för sent blev dess ändringar kvar, kandidaten stod som förfinad och återupptagningen hoppade över passet på dess klar-tid. genomford=false var korrekt.

**Klar (2026-10-09):** F03 rättad (20e4f61, d2b880f): sista försöket återställs när kärnkravet brister, uppfyllt är skilt från avslutat, återupptagningen gör inte om ett misslyckat pass av sig självt, ett uttryckligt nytt försök inom budgeten två omgångar (kandidater.py --nytt-passforsok), och användningen i sex nivåer i posten. prov_metodglapp Specialistpass rött mot b427aa7 och grönt efter; attrapper vid sessionen och fotograferingen, ingen verklig session. Underlag för omgranskning: RAPPORT-2026-10-09-metod-till-resultat.
