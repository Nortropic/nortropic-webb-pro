---
name: backlog
description: Genomför poster ur den vilande backloggen (backlog/B-*.md) när ägaren säger "implementera enligt backlog", "börja på backloggen", "ta backloggen" eller namnger en post. Tar posterna en i taget, gör den lilla ändringen, prövar, committar och sätter posten till klar.
---

# Genomför backloggen

Ägaren har startat den här sessionen och pekat på backloggen. Det är uppdraget: genomför vilande poster tills de är
slut eller ägaren säger stopp. Fråga inte om lov för varje post; ägarens ord är mandatet.

## Ordning

```sh
.venv/bin/python kontroller/backlog.py lista --status vilande
```

Hög prio först, sedan äldst. Har ägaren namngett poster: bara de, i den ordningen. Läs `CLAUDE.md` och
`backlog/README.md` en gång innan första posten, och `kunskap/teoretisk-grund.md` och `kunskap/byggstandard.md`: en
ändring ska följa litteraturen och standarden, eller säga varför den avviker.

## Per post

1. `.venv/bin/python kontroller/backlog.py status <id> pagar`
2. **Läs posten och källan:** `kunskap/REGISTER.md` för kirurgposter, `kunder/<slug>/DOM.json` och `LARDOMAR.md`
   för domposter, `kunder/<slug>/RAPPORT.md` för byggposter, och för granskningsposter rapporten i `kallref`
   (sökvägar räknade från `underlag/`) och fyndet i `fynd`. En post som en senare rapport öppnat igen har den
   rapporten i en not: läs den också, eftersom fyndet bestod efter den förra rättelsen.
3. **Klassa domen först** (Codex via ägaren 2026-10-05, punkt 10: en synpunkt på en kund ska inte bli nästa kunds
   instruktion). En ägardom är ett av fyra slag, och slaget avgör var ändringen hamnar:
   - **kundbeslut:** gäller den kunden; det står i domloggen (`underlag/<slug>/DESIGNDOMAR.jsonl`) och i kundens
     underlag, aldrig i en gemensam regel;
   - **smakpreferens:** ett exempel i `LARDOMAR.md` och kalibreringen, som slås upp; aldrig ett krav för nästa bygge;
   - **metodhypotes:** en rad i `kunskap/metodregler.md` med status oprövad och hur den prövas, och i
     `kunskap/designregler.md` bland designhypoteserna;
   - **generell rättelse:** ett fel som gäller varje bygge (ett påhittat påstående, en trasig länk, ett kvalitetskrav
     som brast). Bara den blir en ändring i skillen `bygg-sajt`, en fil i `kunskap/` eller en kontroll.
   Skriv slaget på Ändring-raden. Är slaget oklart: kundbeslut eller smakpreferens, inte en gemensam regel.
   **Gör ändringen**, så liten som posten kräver, i den fil slaget pekar på. Ny mekanik bara när posten uttryckligen
   kräver det och inget enklare räcker.
   Ändras en skill, `CLAUDE.md`, `kritik/GRANSKARE.md` eller en fil i `kunskap/`: läs skillen `writing-for-agents`
   först, och pröva stycket där ändringen hamnar mot dubbletter, inaktuella rader och no-ops.
   **Välj formen efter hur bygget brast.** Läs först vad bygget gjorde och klassa felet:
   - **utelämnade något:** en obligatorisk plats i något bygget redan fyller i (mallen, en rubrik i BRIEF eller
     INNEHALL, en fil som BESTALLNING.md), inte en påminnelse i löptext;
   - **rätt delar, fel form:** beskriv hur resultatet ska se ut, delarna i ordning, inte en lista med förbud;
   - **kände regeln men hoppade över den:** förbudet ihop med det positiva målet, och de undanflykter bygget
     faktiskt använde, ur rapporten eller granskningen;
   - **ska bero på läget:** ett villkor på något som syns i underlaget (finns X, gör Y).
   Skriv klassen på Ändring-raden. Inga brasklappar som "om möjligt" eller "vid behov": de gör regeln valfri.
   Gäller posten ett kommande bygge (en A/B-prövning) och inget bygge finns än: låt den stå vilande med en not
   (`status <id> vilande --not "väntar på bygge"`) och gå vidare.
   **En skill till verktygslådan:**
   - Klona källan vid den commit posten anger, till `/tmp/kirurg/`.
   - Kopiera skillens mapp till `.claude/skills/<namn>/` med licensfilen.
   - Ta bort det posten säger. Ta alltid bort `allowed-tools` och `hooks` ur frontmatter.
   - Skriv `KALLA.md` i mappen: källa, commit, licens, datum och vad som togs bort.
   - Låt `description` säga när skillen används och av vem: bygget, eller sessionen som ändrar repots texter.
   - Kör `.venv/bin/python kontroller/granska_repo.py .claude/skills/<namn>` på kopian. Den får inte bli HÖG.
4. **Pröva:**
   - Ändrades något i `kontroller/` eller `mall/`: kör `kontroller/rokprov.sh`. Den ska sluta grönt.
   - Ändrades en skill eller kunskapsfil: läs igenom hela den ändrade delen och kontrollera att varje sökväg och
     kommando den nämner finns.
   - **Mikroprov av en domändring** i bygg-sajt eller en kunskapsfil: skriv en liten uppgift som frestar till felet
     domen pekar på (till exempel ett underlag med en enda egen bild, och be om sektionen och beställningen). Arm A
     får den gamla texten, arm B den nya; samma uppgift och samma indata, minst fem färska subagenter per arm
     (Task-verktyget, hela skillen som sammanhang). En annan modell än byggarens läser svaren blint i ombytt
     ordning och räknar per svar om felet finns; oenighet räknas som oavgjort. Behåll ändringen när A visar felet
     och B tar bort det i minst fyra av fem. Visar A inte felet: skriv det på Ändring-raden och pröva i nästa
     bygge i stället. Armarnas utfall, domarmodellen och kostnaden står på Ändring-raden. Mikroprovet belägger bara den
     lokala rättningen: att B tar bort felet i uppgiften. Det säger inget om att sajterna blev bättre; generell
     förbättring döms enbart i blind A/B av hela byggen (ägarens beslut 2026-10-03, BESLUT.md).
5. **Bokför:** för domposter skriv lärdomen på raden `**Lärdom:**` under domen i `LARDOMAR.md`, utan personuppgifter
   (läs domen ordagrant i `underlag/LARDOMAR-original.md`; företagsnamn får stå, inte privatpersoners namn, nummer,
   adresser eller hälsa; BESLUT.md 2026-10-03), och commit och vad som ändrades på raden `**Ändring:**`; för
   kirurgposter fyll i `Utfall:` i `kunskap/REGISTER.md`.
6. **Commit** med postens id först i meddelandet, sedan
   `.venv/bin/python kontroller/backlog.py status <id> klar --commit <kort sha> --not "<vad som gjordes>"` och en
   commit till för statusen (eller båda i samma commit om du sätter statusen före). Dokumentationen som ändringen
   berör uppdateras i samma commit (arbetsregeln: `README.md`, Var information finns). Posten står då som klar, inte
   verifierad: fältet `verifierad` sätter den senare granskning som prövar rättelsen (`backlog/README.md`, Status).

Säger posten emot ett gällande ägarbeslut (`BESLUT.md`, besluten med räckvidd i `kunskap/designregler.md`): genomför
den inte. Ägarens domar över byggen före rensningen 2026-10-05 (`LARDOMAR.md`, `kunskap/rensning-nortropic-2.md`) är
historik: de fäller ingen post, och en post vars enda skäl är en sådan dom genomförs inte heller. Detsamma gäller allt
designmaterial från före den rena designstarten 2026-10-09 (`kunskap/ren-designstart.md`): gamla prototyper, domar,
kalibreringsankare och regler som härletts ur dem motiverar ingen post. Sätt
`status <id> vilande --not "<krocken eller skälet>"` och ta upp det i slutrapporten.

## Efter sista posten

`git push origin main`. Svara ägaren kort: vilka poster som blev klara och med vilka commits, vilka som står kvar och
varför.

## Aldrig

Starta byggkörningar mot verksamheter, skicka något till någon, ändra de gamla repona på GitHub (Runtime, kontoret, Digitala),
radera poster. Avvisade poster ligger kvar.
