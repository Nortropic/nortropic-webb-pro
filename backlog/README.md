# Backloggen

En vilande lista över förbättringar som är aktuella för oss. En fil per post (`B-ÅÅÅÅMMDD-namn.md`), alltid skapad
med status `vilande`. Ingenting här genomförs av sig självt.

## Var posterna kommer ifrån (automatiskt)

| Källa | När | Hur |
|---|---|---|
| kirurg | kirurgen dömer något "ta in" eller "prova A/B" | skillen `kirurg`, från en session eller dashboardens intagsfält |
| dom | ägaren skickar frågeformuläret efter ett bygge | dashboarden skapar posten ur svaren |
| bygge | en byggkörning hittar en brist i verktyg, skill eller kunskap | steg 7 i skillen `bygg-sajt` |

Alla tre skriver genom `kontroller/backlog.py ny`, så formen är densamma.

## Så genomförs den

Starta en Claude Code-session i repots rot och säg **"implementera enligt backlog"**. Skillen `backlog` tar de
vilande posterna en i taget (hög prio först, sedan äldst), gör den lilla ändringen, prövar, committar och sätter
posten till `klar` med commit. Ägaren kan också namnge vilka poster som ska tas.

```sh
.venv/bin/python kontroller/backlog.py lista --status vilande
```

## Status

`vilande` väntar · `pagar` en session arbetar med den · `klar` genomförd (commit står i posten) · `avvisad` ägaren
sa nej (i dashboarden eller i en session). Avvisade poster ligger kvar, så att samma idé inte kommer tillbaka.
