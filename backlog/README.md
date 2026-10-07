# Backloggen

En vilande lista över förbättringar som är aktuella för oss. En fil per post (`B-ÅÅÅÅMMDD-namn.md`), alltid skapad
med status `vilande`. Ingenting här genomförs av sig självt.

## Var posterna kommer ifrån

| Källa | När | Hur |
|---|---|---|
| kirurg | kirurgen dömer något "ta in" eller "prova A/B" | skillen `kirurg`, från en session eller dashboardens intagsfält |
| dom | ägaren skickar frågeformuläret efter ett bygge | dashboarden skapar posten ur svaren |
| bygge | en byggkörning hittar en brist i verktyg, skill eller kunskap | steg 7 i skillen `bygg-sajt` |
| bevakning | en session hittar något aktuellt i leverantörernas dokumentation eller annan omvärldsbevakning | sessionen; `--kallref` källan och när den lästes |
| granskning | en systemgranskning har ett fynd som inte rättas i samma uppdrag | den session som tar hand om granskningen; `--kallref` rapportens id eller sökväg (förteckningens sökvägar räknas från `underlag/`) och `--fynd <rapportens id>#<fyndets id>`, en post per fynd |

De tre första skapas automatiskt. Alla skriver genom `kontroller/backlog.py ny`, så formen är densamma, och varje
skrivning sker under backloggens fillås med en tempfil som byts in atomiskt. Ett huvudvärde med en radbrytning eller ett
annat kontrolltecken avvisas. Ett fynd får en post: finns `--fynd` redan i en post, oavsett status, skapas ingen ny,
och `ny` ger den postens id.

## Så genomförs den

Starta en Claude Code-session i repots rot och säg **"implementera enligt backlog"**. Skillen `backlog` tar de
vilande posterna en i taget (hög prio först, sedan äldst), gör den lilla ändringen, prövar, committar och sätter
posten till `klar` med commit. Ägaren kan också namnge vilka poster som ska tas.

```sh
.venv/bin/python kontroller/backlog.py lista --status vilande
```

## Status

`vilande` väntar · `pagar` en session arbetar med den · `klar` genomförd (commit står i posten; verifierad är den
först när en senare granskning säger det, `README.md`, Var information finns) · `avvisad` ägaren
sa nej (i dashboarden eller i en session) · `ersatt` ersatt av ett senare beslut eller sammanförd i en annan post (noten
säger vilken). Avvisade och ersatta poster ligger kvar, så att samma idé inte kommer tillbaka.

**Verifierad** är ett fält, ingen status: `verifierad: <rapportens id>` och `verifierad_tid` på en klar post, satta med
`.venv/bin/python kontroller/backlog.py verifiera <id> --rapport <rapportens id>` när en senare granskning har
verifierat rättelsen. Rapporten som hittade fyndet kan inte verifiera det, och `andrad` står kvar. Inget sätter fälten
av sig självt, och en kodändring verifierar ingenting. `lista` och dashboarden visar en klar post utan fältet som
"klar, inte verifierad". Ändras postens status eller commit tas fälten bort ur huvudet, och en not säger vilken rapport
som verifierade det förra läget.
