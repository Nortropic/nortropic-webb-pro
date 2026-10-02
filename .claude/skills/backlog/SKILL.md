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
   för domposter, `kunder/<slug>/RAPPORT.md` för byggposter.
3. **Gör ändringen**, så liten som posten kräver, i den fil posten pekar på. En dom blir en textändring i skillen
   `bygg-sajt` eller en fil i `kunskap/`. Ny mekanik bara när posten uttryckligen kräver det och inget enklare räcker.
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
     bygge i stället. Armarnas utfall, domarmodellen och kostnaden står på Ändring-raden.
5. **Bokför:** för domposter skriv commit och vad som ändrades på raden `**Ändring:**` i `LARDOMAR.md`; för
   kirurgposter fyll i `Utfall:` i `kunskap/REGISTER.md`.
6. **Commit** med postens id först i meddelandet, sedan
   `.venv/bin/python kontroller/backlog.py status <id> klar --commit <kort sha> --not "<vad som gjordes>"` och en
   commit till för statusen (eller båda i samma commit om du sätter statusen före).

Säger posten emot något som ägaren beslutat (`BESLUT.md`, `LARDOMAR.md`): genomför den inte. Sätt
`status <id> vilande --not "<krocken>"` och ta upp det i slutrapporten.

## Efter sista posten

`git push origin main`. Svara ägaren kort: vilka poster som blev klara och med vilka commits, vilka som står kvar och
varför.

## Aldrig

Starta byggkörningar mot verksamheter, skicka något till någon, ändra de frysta repona (Runtime, kontoret, Digitala),
radera poster. Avvisade poster ligger kvar.
