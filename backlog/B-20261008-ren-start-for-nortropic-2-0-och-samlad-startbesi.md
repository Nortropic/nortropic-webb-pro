---
id: B-20261008-ren-start-for-nortropic-2-0-och-samlad-startbesi
status: pagar
kalla: dom
kallref: BESLUT.md
skapad: 2026-10-08
prio: hog
steg: efter backlogavstämningen; BESLUT.md; underlag/granskningar/GR-20261008-motorinventering-codex.md
andrad: 2026-10-08T21:28Z
---
# Ren start för Nortropic 2.0 och samlad startbesiktning (ägarens uppdrag 2026-10-08 ~14:35Z, köat)

**Varför:** Ägarens uppdrag ~14:35Z, klistrat mitt i backlogavstämningen: nästa bygge ska få rätt underlag, kedjans delar fungera tillsammans och det ska gå att följa var kvalitet eller information försvinner. Köat efter det pågående arbetet (backlogavstämningen 2026-10-08, steg 1–3 och slutrapporten) och före nästa ordinarie helbygge. Codex motorinventering (underlag/granskningar/GR-20261008-motorinventering-codex.md, commit 062a930) jämförs fynd för fynd med aktuell kod först; inga dubbla fynd; genomfört skilt från verifierat.

**Förslag:** Sju delar i ägarens ordning: 1) köa och stäm av; 2) avgränsad nollställning av designhistoriken (klassning aktivt/historiskt/omprövas, historiken bevaras privat, läsvägarna kontrolleras); 3) besiktning av hela kedjan och överlämningarna; 4) rätta och verifiera F01–F08 med befintliga poster; 5) förnyad kalibrering med tydlig bevisgräns; 6) bevisa kedjan stegvis (rökprov, förmågeprov med fiktivt material, exempel genom research–förfining, helförloppet genom Flöde, lokal export); 7) samlat besked som börjar med de tre JA/NEJ-raderna. Ordagrant i posten och i BESLUT.md, tillägget 2026-10-08 om uppdraget.

**Klart när:** Slutrapporten lämnad enligt del 7 (Redo för kontrollerat pilotbygge, Verkligt slutbygge godkänt, Driftsatt leverans verifierad), rättelserna committade med prov, rökprovet grönt på den färdiga versionen, och väntande verkliga prov redovisade som väntande.

## Ägarens ord (ordagrant, 2026-10-08 ~14:35Z)

```text
Köa detta uppdrag efter ditt pågående arbete i nortropic-webb-pro. Avbryt inte en pågående provkörning och skapa inte ett parallellt, överlappande förbättringsprojekt. När det pågående arbetet är avslutat ska du genomföra uppdraget nedan före nästa ordinarie helbygge.

UPPDRAG: Ren start för Nortropic 2.0 och samlad startbesiktning

Målet är att nästa bygge får rätt underlag, att hela kedjans delar fungerar tillsammans och att vi kan följa var kvalitet eller information eventuellt försvinner.

Vi ska behålla kompetensen, verktygslådan och tillämpliga kvalitetsskydd. Äldre estetiska slutsatser ska inte automatiskt begränsa nya byggen. Fler dokument, regler eller lyckade verktygsanrop är inte i sig ett bättre resultat.

1. Köa och stäm av mot det pågående arbetet

Lägg uppdraget i befintlig uppdrags-/backlogstruktur och ange ordningen. Återanvänd befintliga poster där de täcker samma problem.

Läs:
- CLAUDE.md och README.md, särskilt kedjan och dokumentationsreglerna.
- Aktuella ägarbeslut och kunskap/designregler.md.
- underlag/granskningar/GR-20261008-motorinventering-codex.md
- Inventeringsbilagan i katalogen med samma namn.
- underlag/rapporter/RAPPORT-2026-10-08-backlogavstamning.md
- Senare rättelser, granskningar och provresultat.

Codex inventering gäller commit 062a930. Jämför varje fynd med den aktuella koden innan du rättar något. Något kan redan vara åtgärdat av ditt pågående arbete. Skilj genomfört från verifierat och skapa inga dubbla fynd.

2. Gör en avgränsad nollställning av designhistoriken

Klassificera befintligt styrande material som:
- aktivt och tillämpligt;
- historiskt;
- behöver omprövas.

Bevara historiken privat. Radera inte prototyper, kalibreringsoriginal, tidigare domar eller lärdomar permanent inom detta uppdrag. Koppla bort dem från automatiska arbetsunderlag där de inte längre ska styra.

Behåll:
- aktuella kundfakta och uttryckliga beslut inom rätt omfattning;
- relevant professionell kunskap och skills;
- verifierade tekniska lärdomar och regressionsprov;
- tillämpliga säkerhets-, integritets- och tillgänglighetskrav.

Avaktivera som generella designregler:
- äldre prototypers färg-, typsnitts- och layoutval;
- agenternas generaliseringar från tidigare misslyckanden;
- äldre modellbetyg som kvalitetsbevis för den nya motorn.

Kontrollera alla faktiska läsvägar, inklusive:
- riktningshistorik och aktuella domutdrag;
- UPPTAGNA-VAL och dess omgenerering;
- tidigare byggbilder i granskningen;
- automatiskt ärvda referenspaket och tjänsterapporter;
- härledda instruktioner i kunskapstexter och genererade uppdrag.

En ny riktning, en ny slug eller flyttade filer är inte ensamt bevis för en ren arbetskontext. Använd ett uttryckligt aktivt urval och återanvänd befintliga manifest och körningsidentiteter.

Bra externa referenser får återväljas uttryckligen. Kundfakta och aktuella sakbeslut får inte försvinna i rensningen.

3. Besiktiga hela kedjan och dess överlämningar

Gå igenom:
- miljö, beroenden, versionsunderhåll och startkontroll;
- Kundstart, research, brief, innehåll och material;
- referensfångst, Refero, Mobbin och övriga tilldelade tjänster;
- planering, skills, prototyper och specialistpass;
- ägarval, förfining, kalibrering och granskning;
- helbyggstart, stopp, fortsätt och felåterhämtning;
- tekniska kontroller, slutpost, export och kundrepo;
- leverans, dokumentation, observation och förbättringsloop.

För varje del redovisar du:
- verklig ingång och ansvar;
- indata och utdata;
- vilken version resultatet gäller;
- befintligt prov och vad det faktiskt bevisar;
- kvarstående fel eller obevisad förmåga;
- nästa konkreta kontroll.

Undersök särskilt överlämningarna: material som hämtats ska nå rätt uppdrag; det skaparen använder ska kunna observeras; godkännandet ska gälla det slutliga bygget.

4. Rätta och verifiera fynden

Hantera rapportens F01–F08 tillsammans med befintliga backlogposter. Prioritera:
- ren historik- och referensavgränsning;
- komplett identitet för granskningsunderlag och kalibrering;
- Motion-resultat som tappas i observationskedjan;
- saknade transkript som döljs i sammanvägda kvitton;
- skillernas föreskrivna läsordning och faktisk verktygsanvändning;
- nästlade sessioners avsedda MCP-konfiguration;
- misslyckad referensleverans som annars kan följas av planering;
- rätt sandlådemiljö genom den verkliga Flöde-ingången;
- bevarat godkänt underlag när helbygget tar vid.

Varje tilldelad kompetens ska få ett konkret arbete och användas enligt uppdraget. Skilj installerat, tilldelat, läst, anropat, returnerat material och visad tillämpning. Räkna inte ritualanrop eller skaparens egen redovisning som bevis på kvalitet.

Använd små rättelser och riktade negativa och positiva prov. Följ repots regler för regressioner, dokumentation och granskning. Kör ett tungt prov i taget på hela maskinen och redigera aldrig ett skalskript medan det körs.

5. Förnya kalibreringen med tydlig bevisgräns

Bekräfta vilka externa exempel som fortfarande motsvarar ägarens ribba. Skilj ankare från orörda utvärderingsexempel. Material som påverkat instruktionerna får inte samtidigt kallas oberoende slutprov.

Bind återanvända domar till den aktiva kalibreringen och det faktiska bedömningsunderlaget.

Mät särskilt om granskaren godkänner sådant ägaren underkänner. Hitta inte på ägardomar och sänk inte ribban för att få grönt.

6. Bevisa kedjan stegvis

Efter rättelserna:
- kör hela rökprovet på den färdiga versionen;
- gör avgränsade verkliga förmågeprov inom redan givet mandat, med fiktivt material;
- verifiera faktisk sessionskonfiguration, verktygsåtkomst, mottagna bilder och överföringen till uppdraget;
- låt ett bedömbart exempel gå genom research, plan, skiss och förfining.

Ägaren bedömer bilderna före skaparens förklaring. Nästa helbygge ska utgå från en faktiskt godkänd version.

Pröva därefter det riktiga helförloppet genom Flöde, inklusive stopp/fortsätt och normal avslutning, samt byggverifierad lokal export. Teknik, granskning, ägardom och export ska vara bundna till rätt slutversion.

Verkliga modell- eller tjänsteprov som saknar mandat redovisas som väntande. Aktivera inte externa tjänster, köp, publicering eller kundkontakt genom att tolka detta som ett nytt sådant mandat.

7. Leverera ett samlat besked

Återanvänd befintlig dokumentationsstruktur och dashboard. Håll dokumentationen aktuell i samma arbete och bevara äldre rapporter som historik.

Slutrapporten ska börja med:
- Redo för kontrollerat pilotbygge: JA/NEJ och skäl.
- Verkligt slutbygge godkänt: JA/NEJ/EJ PRÖVAT.
- Driftsatt leverans verifierad: JA/NEJ/EJ PRÖVAT.

Redovisa vad som rättats, vad som redan var gjort, exakta versioner och provresultat samt vad som återstår.

Lokalt fungerande mekanik, verklig extern åtkomst och professionell designkvalitet är tre olika saker. Ingen grön markering får betyda mer än sitt belägg.

Börja med att köa uppdraget och bekräfta dess plats efter det pågående arbetet. Genomför sedan arbetet i ordningen ovan inom befintligt mandat.
```

**Pagar (2026-10-08):** Nattens uppdrag 2026-10-08: Codex fynd R02 (F05, K06), R03 (F04, F05) och R04 (F01) rättade i 5a09fa8, med prov röda mot 06af6ff och gröna efter. Posten står kvar som pågår: startbesiktningens verkliga del kräver en verklig körning, som ägaren startar (nattrapporten, B).
