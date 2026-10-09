---
id: B-20261007-backloggen-ateroppningen-av-en-klar-post-ordnar
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#KAN-1
skapad: 2026-10-07
prio: normal
steg: main: kontroller/backlog.py, kontroller/rokprov/revision/prov_dokumentation.py
commit: 2a32952
andrad: 2026-10-09T05:48Z
---
# Backloggen: återöppningen av en klar post ordnar rapporterna efter tid, inte efter rundans nummer

**Varför:** ny --fynd öppnar inte en klar post i tre fall: GR-20261007-r96-om3 efter GR-20261007-r97 (senare i tiden men lägre runda), en rapport utan ÅÅÅÅMMDD i id:t (GRANSKNING-r98, RAPPORT-2026-10-08-x), och en post som verifierats av en sådan rapport. Det är dokumenterat, men ny slutar med 0 och säger det bara på stderr.

**Förslag:** Ordna efter rapporthuvudets datum och förteckningens registreringstid i stället för rundans nummer, och skriv utfallet också på stdout med kommandot för att öppna posten för hand.

**Klart när:** De tre fallen i GR-20261007-r99-om#KAN-1 har var sitt prov i prov_dokumentation.py, och det som inte kan avgöras säger ny tydligt i sin utdata.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08: ordningen efter registreringstid, rapporthuvudets datum och rundan bara samma dag och form; de tre fallen och N08 i prov_dokumentation, utfallet på stdout; rött mot basen, grönt efter, fem mutanter fälls. Inte verifierad.

**Klar (2026-10-09):** GR-20261009-natt-omgranskning-codex#N06: registreringstiderna tolkas som tidpunkter med tidszon (Z och +00:00, med bråksekunder; en annan zon räknas om); samma ögonblick är aldrig senare. prov_dokumentation fall 5 genom backlog.py ny, rött mot 2c7aa5a. Förteckningens rader orörda. Inte verifierad.
