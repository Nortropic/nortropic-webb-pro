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
`backlog/README.md` en gång innan första posten.

## Per post

1. `.venv/bin/python kontroller/backlog.py status <id> pagar`
2. **Läs posten och källan:** `kunskap/REGISTER.md` för kirurgposter, `kunder/<slug>/DOM.json` och `LARDOMAR.md`
   för domposter, `kunder/<slug>/RAPPORT.md` för byggposter.
3. **Gör ändringen**, så liten som posten kräver, i den fil posten pekar på. En dom blir en textändring i skillen
   `bygg-sajt` eller en fil i `kunskap/`. Ny mekanik bara när posten uttryckligen kräver det och inget enklare räcker.
   Gäller posten ett kommande bygge (en A/B-prövning) och inget bygge finns än: låt den stå vilande med en not
   (`status <id> vilande --not "väntar på bygge"`) och gå vidare.
4. **Pröva:**
   - Ändrades något i `kontroller/` eller `mall/`: kör `kontroller/rokprov.sh`. Den ska sluta grönt.
   - Ändrades en skill eller kunskapsfil: läs igenom hela den ändrade delen och kontrollera att varje sökväg och
     kommando den nämner finns.
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
