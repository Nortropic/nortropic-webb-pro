---
id: B-20261001-lighthouse-grinden-faller-samma-bygge-nar-datorn
status: klar
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 6
commit: 636cf33
andrad: 2026-10-01T23:19Z
---
# Lighthouse-grinden fäller samma bygge när datorn är belastad

**Varför:** Luleå-Snickaren: bygge b2eee682cf9b gav lägst P 93 kl 21:24Z och P 77 i stoppvaktens körning kl 21:30Z utan ändring; total blocking time 500–845 ms på sidor utan JavaScript vid belastning 8. Sidan som föll varierade mellan körningarna.

**Förslag:** kontroller/prova.py: skriv systemets belastning (os.getloadavg) i STATUS.json och PROV.md vid varje Lighthouse-körning, och mät om en sida som hamnar under kravet innan grinden blir röd.

**Klar (2026-10-01):** genomförd natten 2026-10-01/02
