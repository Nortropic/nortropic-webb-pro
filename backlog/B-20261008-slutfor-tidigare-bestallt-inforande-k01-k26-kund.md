---
id: B-20261008-slutfor-tidigare-bestallt-inforande-k01-k26-kund
status: pagar
kalla: dom
kallref: BESLUT.md
skapad: 2026-10-08
prio: hog
steg: efter backlogavstämningen; samordnat med B-20261008-ren-start-for-nortropic-2-0-och-samlad-startbesi; BESLUT.md; GR-20261008-bestallning-mot-leverans-codex.md
andrad: 2026-10-09T08:16Z
---
# Slutför tidigare beställt införande: K01–K26, kundrepon, Vercel, 21st, materialsteget, planprövningens återgång (ägarens uppdrag 2026-10-08 ~14:58Z, köat)

**Varför:** Ägarens uppdrag ~14:58Z: återstående arbete ur beställningarna 2026-10-07 (full verktygslåda, promptkedjan, automatiska kundrepon; BESLUT.md) och tidigare, inte en ny inriktning. Codex kravavstämning K01–K26 (underlag/granskningar/GR-20261008-bestallning-mot-leverans-codex.md med KALLOR.json) gäller 7f773165; varje rad stäms av mot aktuell kod, senare commits och prov innan något behandlas som kvarstående. Köat efter backlogavstämningen (uppdrag 2) och före nästa helbygge; startbesiktningen i ren start-uppdraget (del 3 och 5–7) bedömer den slutliga gemensamma versionen efter detta. Köläggningen ger inget mandat att starta nästa helbygge.

**Förslag:** 1) Avstämning K01–K26: ansvarig post, implementerat och inkopplat, bevis med omfattning, exakt återstår. 2) Körvägar som saknas: A automatiska kundrepon och projektkontext (K01–K04), B Vercel och leverans med commitbunden preview och kvitto (K05), C 21st i skaparsessionen (K09), D bild- och videomaterialsteget Higgsfield/Nano Banana/Seedance med Canvas, mekanik nu och konto senare (K10, K12), E planprövningens återgång (K08). 3) Övergångarna: K06 (ny session får inte beskedet att kärnan redan lästs), K07 (A3, rättad 6e09f70), nästlade sessioners MCP (E1, a97fc2c), kompetenskvitton och Motion (C4/C6, a97fc2c), tomma referenshämtningar. 4) Kompetensens faktiska användning (K11, K13, K15, K16, K26) och utvärderingen av Dynamic Workflows (K17; behålla är ett möjligt resultat; MotionSite.ai och Motion+ avvalda). 5) Kundstart (K18–K22) och Kirurgen (K23–K24). 6) Prov genom den riktiga ingången och en samlad aktuell leveransöversikt (beställt, implementerat, inkopplat, lokalt prövat, verkligt prövat, kvalitetsbedömt, återstår, bevislänk och version) i befintlig dokumentationsstruktur. Befintliga poster som knyts: A3, E1 och C4 (klara), D1/D3/D7/D8 (pågår i steg 2), steg 4-posterna om leveransövning, gräns på processnivå, jämförbara byggen och prototyp mot helbygge (K05, K25), och ren start-posten. Ordagrant i posten och i BESLUT.md.

**Klart när:** K01–K26 avstämda med belägg; delarna A–E har körväg genom den riktiga ingången med prov för fel-, avbrotts- och återförsöksvägar; leveransöversikten är aktuell; det som kräver externt konto, mandat eller deltagare är avgränsat som väntande genom ett befintligt ägarbeslut.

## Ägarens ord (ordagrant, 2026-10-08 ~14:58Z)

```text
KÖA: slutför tidigare beställt införande i Nortropic

Detta är återstående arbete från mina tidigare beställningar, inte en ny produktinriktning. Köa arbetet efter pågående arbete och före nästa helbygge. Starta inget nytt bygge nu och avbryt inte pågående rättningar.

Återanvänd befintlig backlog, dokumentationsstruktur och körmekanik. Skapa inte en parallell uppgiftstavla eller nya poster för sådant som redan har en ansvarig post.

1. Läs och stäm av innan du planerar arbetet

Läs:
- CLAUDE.md och README.md.
- Gällande ägarbeslut i BESLUT.md, särskilt uppdraget om full verktygslåda, promptkedjan och automatiska kundrepon.
- underlag/granskningar/GR-20261008-bestallning-mot-leverans-codex.md
- Rapportens KALLOR.json.
- underlag/granskningar/GR-20261008-motorinventering-codex.md
- underlag/rapporter/HANDOVER-codex-2026-10-07.md
- underlag/granskningar/GR-20261008-aterupptagning-codex/STATUS.md

Kravavstämningen gäller 7f773165. Kontrollera aktuell kod, arbetsändringar, senare commits och prov innan du behandlar ett fynd som kvarstående. Senare uttryckliga ägarbeslut gäller.

Stäm av samtliga K01–K26. För varje rad:
- länka befintlig arbetsuppgift;
- ange vad som faktiskt är implementerat och inkopplat;
- ange verifieringsbevis och deras omfattning;
- ange exakt vad som återstår.

Redan rättat arbete ska verifieras och återanvändas. Gör inte om det.

2. Slutför de beställda delar som saknar körväg

A. Automatiska kundrepon och projektkontext

Varje nytt kundprojekt ska få ett eget lokalt repo och ett privat GitHub-repo enligt redan beslutade namn- och organisationsregler.

Projektet ska ha:
- stabil identitet och koppling mellan lokal sökväg och fjärrrepo;
- samma repo vid fortsättning, nya kandidater och återförsök;
- säker hantering av samtidiga starter och delvis misslyckad provisionering;
- ett kort kundspecifikt CLAUDE.md;
- rätt arbetsrot, skills, MCP-konfiguration och projektunderlag i de verkliga arbetssessionerna.

Flytta och verifiera skydden tillsammans med arbetskontexten. Privat underlag och hemligheter får inte följa med i repo, commit, push eller otillåtna tjänsteanrop.

En senare lokal export är inte en ersättning för detta krav.

B. Vercel och leverans

Koppla kundrepot till rätt befintligt Vercel-team och projekt. Återanvänd projektet vid fortsatta körningar.

Preview ska:
- bindas till rätt commit och byggversion;
- visas i dashboarden;
- få ett beständigt kvitto med faktisk status och kvarstående hinder.

Skilj lokal export, fungerande preview och godkänd produktionsleverans. Bevara befintliga publiceringsbeslut. Återanvänd den beslutade CLI-vägen om GitHub-appen fortfarande saknas; anta inte aktuell åtkomst utan verifiering.

C. 21st

Inför 21st i den faktiska skaparsessionens körväg:
- aktuell officiell integration och verktygslista;
- korrekt projektspecifik MCP-konfiguration och behörighet;
- konkret uppgift för komponentresearch, hämtning och anpassning;
- spårbar källa, licens, beroenden och användning;
- verifiering i den session som ska använda resultatet.

Builder är redan valt. Kontrollera faktisk åtkomst och rättigheter separat. Installation på användarnivå eller dokumentation räcker inte.

D. Bild- och videomaterialsteget

Bygg den redan beställda mekaniken för Higgsfield/Nano Banana/Seedance:
visuellt uppdrag → generation eller redigering → versionshanterad tillgång → webboptimering → faktisk användning.

Hantera relevanta bildformat, video, posterbild, mobilvariant, prestanda och reducerad rörelse. Bevara skillnaden mellan illustrativt material och bilder som påstår sig visa kundens verkliga verksamhet.

Ägarbeslutet var mekanik nu, konto senare. Bygg därför mekaniken och ärliga kontraktsprov utan att låtsas att extern åtkomst fungerar. Koppla Canvas-resultat till detta steg.

E. Planprövningens återgång

Planprövningen ska kunna leda till omprövad hypotes, annan referens, kompletterande research och ny planprövning innan skapandet fortsätter.

Ett konstaterat problem får inte bara bokföras medan körningen fortsätter med samma låsta plan. Återanvänd befintliga identiteter, budgetar och tillstånd.

3. Rätta och slutför övergångarna

Kontrollera särskilt:
- nya sessioner som felaktigt får beskedet att kompetensen redan lästs i en tidigare session;
- verklig återupptagning kontra ny session med explicit överlämning;
- motsägelsen mellan att börja från steg 1 och fortsätta från en godkänd startsida;
- bevarande av det underlag och den designversion som godkänts;
- skill- och MCP-konfiguration i nästlade sessioner;
- saknade transkript och ofullständiga kompetenskvitton;
- Motion-resultat genom observation, kvitto och kompetenspass;
- hantering av tomma eller misslyckade referenshämtningar.

Återanvänd pågående rättningar där de löser detta. Markera inte en rättning som färdig enbart för att den finns i arbetsdiffen.

4. Slutför kompetensens faktiska användning och verifiering

Tilldelade skills ska aktiveras där skillsystemet stöder det. Referensfiler ska läsas enligt instruktionerna. Tilldelade verktygsuppgifter ska ge ett kontrollerat resultat som faktiskt kan användas.

Följ:
tillgänglig → aktiverad/läst → anropad → användbart resultat → använd i arbetet → resultat bedömt.

Verifiera Refero/Mobbin, Motion/GSAP, Canvas/HIG och referensinspektionen utifrån deras beställda uppgifter. Klargör DevTools manuella respektive integrerade roll.

Kräv inte meningslösa anrop till varje endpoint. Ett lyckat anrop eller läskvitto är inte designkvalitet. Saknad observation ska beskrivas som en observationslucka, inte automatiskt som uteblivet arbete.

Genomför den beställda utvärderingen av Dynamic Workflows. Införande är inte obligatoriskt; ett belagt beslut att behålla befintlig orkestrering är ett möjligt resultat.

MotionSite.ai och Motion+ är avvalda och ska inte återinföras som krav.

5. Slutför Kundstart och Kirurgens kvarstående beviskedja

Bevara redan införd lokal mekanik.

Kundstart:
- skilj det genomförda enstaka AI-varvet från verifierad flertursförmåga;
- pröva informationsförlust, felaktiga antaganden, upprepningar, rättelser och korrekt överlämning;
- håll utvecklingsfall och orörda bedömningsfall åtskilda.

Kedjan:
- gör det möjligt att följa insamlat, förstått, överfört, använt och levererat;
- redovisa det som fortfarande inte går att fastställa;
- använd inte filöverföring som bevis för förståelse eller användning.

Kirurgen:
- slutför den avsedda vägen från signal till prövad förändring, tillåtet införande och observerad effekt;
- återanvänd ordinarie granskning och Git;
- bevara negativa och ofullständiga utfall;
- beskriv inte registrerad effekt som automatiskt bevisat orsakssamband.

Ingen självaktivering, mandatändring eller automatisk publicering får smygas in. Mänsklig användarprövning kräver deltagare, samtycke och mandat.

6. Verifiering och leveransredovisning

För varje genomförd del behövs proportionerliga prov genom den riktiga ingången, inklusive relevanta fel-, avbrotts- och återförsöksvägar.

Stubbar verifierar mekanik. De verifierar inte extern åtkomst, modellförmåga eller designkvalitet.

Verkliga modell-, MCP- och driftprov görs inom befintligt mandat och budget. Avgränsa väntande åtkomst utan att stoppa oberoende arbete.

Respektera ett tungt rökprov åt gången, pågående arbete och repots arbetsregler.

Håll en samlad aktuell leveransöversikt i befintlig dokumentationsstruktur:
- beställt;
- implementerat;
- inkopplat;
- lokalt prövat;
- verkligt prövat;
- kvalitetsbedömt;
- kvarstående arbete eller uttryckligt uppskjutet beslut;
- bevislänk och granskad version.

Bevara historiska rapporter. Uppdatera den aktuella överblicken så att jag inte behöver pussla ihop verklig status ur gamla rapporter.

Kalla inte hela införandet färdigt förrän kraven är levererade eller tydligt avgränsade genom ett befintligt ägarbeslut.

Avsluta köläggningen med:
- var uppdraget finns;
- vilka befintliga poster det knyts till;
- beroendeordningen;
- vad som redan är rättat;
- vad som återstår före nästa helbygge.

Samordna med det redan köade arbetet för ren 2.0-start och samlad startkontroll. Startkontrollen ska bedöma den slutliga gemensamma versionen. Köläggningen i sig ger inget mandat att starta nästa helbygge.
```

**Pagar (2026-10-08):** Nattens uppdrag 2026-10-08: Codex fynd R01 (2E), R05 (2D), R06 (2A, mekaniken; av som förval), R07 (2B) och R08 (2A) rättade i 5a09fa8, med prov röda mot 06af6ff och gröna efter. Posten står kvar som pågår: det verkliga provet av arbetsroten i en riktig skaparsession, kundrepon på GitHub och Vercels förhandsvisning kräver ägarens start eller konton (nattrapporten, B).

**Pagar (2026-10-09):** Ägarens uppdrag 2026-10-09 ~04:54Z, Codex omgranskning GR-20261009-natt-omgranskning-codex: N01 (2E) planprövningen bunden till planversionen per kandidat; ett uppdrag som omplanerats vid återupptagningen prövas före skaparen, och ett oprövat stoppas (f7d94b6). N02 (2D) materialverktygets kandidatgräns: inga förkortade flaggor, den slutligt tolkade kandidaten prövas, registret visar och använder bara egna och uttryckligen gemensamma tillgångar, och skaparens Read nekas registret (efc70ee). N04 (2A) läckagekontrollen före push gäller hela historiken som skickas, också vid första fjärrskapningen (utan gh --push) och för ett återanvänt kundrepo, bunden till den commit som pushas; projektstarten committar bara sina egna filer (e4a95cb). R06 (2A) kundrepot som arbetsrot i alla fyra vägarna: kandidatskissen och kandidatförfiningen (slug), de äldre vägarna (arbetsslug) och helbygget genom kor.sh (kontroller/arbetsrot.py med projektets krokar); sessionerna skriver aldrig i kundrepot, och ett kundrepo med egna inställningar används inte (fcfd3e9, 920e441). Växeln är av som standard. Förmågeprovet för arbetsroten och blindningen är förberett (kontroller/formagoprov.py, 6eb592b), inte kört. Prov: prov_omgranskning och prov_material, röda mot 2c7aa5a och gröna efter (RAPPORT-2026-10-09-n01-n06-blindning-arbetsrot). Inte verifierat; posten står kvar som pågår: förmågeprovet, kundrepo i organisationen och en verklig förhandsvisning återstår.

**Pagar (2026-10-09):** 2026-10-09: GR-20261009-metod-till-resultat-codex#F01 rättad (5ad34aa): planprövningen stämplar bara uppdrag med en unik, användbar bedömning; dubbla, okända, ogiltiga och saknade lämnar uppdraget oprövat och stoppat före skaparen med skälet; omprövningen bevarar de oförändrades bedömning. prov_metodglapp Planprovningstackning (7 fall genom kor, falsk modell), rött mot b427aa7 och grönt efter.
