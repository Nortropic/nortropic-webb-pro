---
id: B-20261003-andra-domaner-och-extern-text-kontrolleras-med-e
status: vilande
kalla: bygge
kallref: kunder/salong-kreativ/RAPPORT.md
skapad: 2026-10-03
prio: normal
steg: 1
---
# Andra domäner och extern text kontrolleras med egna skript

**Varför:** Steg 1 kräver att verksamhetens andra domäner (.se, .com, .nu, namn med ort) prövas. Bygget skrev underlag/salong-kreativ/skript/domaner.py för det och till_text.py för att göra en arkiverad tidningsartikel (web.archive.org) läsbar som text.

**Förslag:** kontroller/hamta_sajt.py får --pröva-domaner som provar namnets vanliga domäner och skriver resultatet i SIDOR.md; en liten kontroll kontroller/sida_till_text.py <url> <ut> för enstaka externa sidor (artiklar, arkiv) med samma textformat som hamta_sajt.
