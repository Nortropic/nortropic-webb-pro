---
id: B-20261001-prova-py-skriver-brokenpipe-tracebacks-fran-sin
status: klar
kalla: bygge
kallref: kunder/paint-it-black-maleri/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
commit: 636cf33
andrad: 2026-10-01T23:19Z
---
# prova.py skriver BrokenPipe-tracebacks från sin testserver före resultatet

**Varför:** Varje körning i paint-it-black-maleri gav 1–5 tracebacks (BrokenPipeError, ConnectionResetError) från http.server när webbläsaren avbröt en hämtning. De är ofarliga men drunknar PROV-tabellen och ser ut som fel.

**Förslag:** kontroller/prova.py, klassen Server: sätt ThreadingHTTPServer.handle_error till en tyst metod för BrokenPipeError och ConnectionResetError.

**Klar (2026-10-01):** genomförd natten 2026-10-01/02
