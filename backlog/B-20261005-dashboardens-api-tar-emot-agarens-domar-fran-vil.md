---
id: B-20261005-dashboardens-api-tar-emot-agarens-domar-fran-vil
status: klar
kalla: bevakning
kallref: granskning 4 av skapandeflödet 2026-10-05, iakttagelse utanför uppdraget
skapad: 2026-10-05
prio: hog
commit: b075827
andrad: 2026-10-08T15:11Z
---
# Dashboardens API tar emot ägarens domar från vilken lokal process som helst

**Varför:** Den fjärde granskningen av skapandeflödet (2026-10-05) noterade att dashboarden på 127.0.0.1:4771 tar emot ägarens domar (prototypen, byggena, kalibreringen, A/B) med Origin=Host som enda kontroll. En lokal process som inte är en webbläsare sätter Origin fritt: ett bygge (curl i byggets verktyg), en sidas byggkod eller ett skript kan skriva en dom i ägarens namn. Skapandeflödet är skyddat sedan 9e59942: skaparens byggen går utan nät (processgrans.py --utan-nat) och domloggen är låst under bygget (kor.sh, chflags uchg). Kalibreringens DOMAR.json, A/B-valen och byggdomarna saknar motsvarande skydd, och ingen av dem står i korsluts skyddade filer.

**Förslag:** En nyckel per dashboardstart som bara ägarens webbläsare får: dashboard.sh öppnar adressen med nyckeln i fragmentet (#nyckel=…), sidan skickar den som rubrik, och servern kräver den för varje skrivande anrop. Pröva också om ett sandlådat bygge når 127.0.0.1:4771, och lägg kalibreringens domar bland de skyddade filerna i kor.sh.

**Klart när:** Varje skrivande API-anrop kräver nyckeln, och ett prov visar att ett anrop utan den nekas (curl från en annan process); ett sandlådat bygge når inte dashboarden; kunskapen säger var ägarens domar kan skrivas.
