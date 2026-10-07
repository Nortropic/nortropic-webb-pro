---
id: B-20261007-kandidaternas-oberoende-byggets-processgrans-hin
status: vilande
kalla: granskning
kallref: granskningar/GR-20261007-r107.md
fynd: GR-20261007-r107#K1
skapad: 2026-10-07
prio: hog
steg: main: kontroller/processgrans.py, kontroller/kandidater.py, kontroller/forhandsvisa.py, kontroller/rokprov/revision/prov_skisskritik.py
---
# Kandidaternas oberoende: byggets processgräns hindrar läsning av andra kandidater och skaparens underlag

**Varför:** Granskaren bekräftade under byggets sandlådeprofil (processgrans.py --skrivbar) att en sidas kod kan läsa en annan kandidats källkod och skaparens text i underlaget när sidan byggs. Profilen tillåter allt utom skrivning och hemligheter. Sessionernas skal är stängt, men byggets kod är en annan väg.

**Förslag:** Neka läsning (deny file-read*) av andra kandidaters kataloger och av underlaget utanför det kandidaten får läsa, per kandidat i processgränsen. Pröva att bygget fungerar och att en sida som försöker läsa en syskonkandidat stoppas.

**Klart när:** Ett prov där en sidas kod försöker läsa en annan kandidats fil vid bygget stoppas, och ett vanligt bygge går. Görs före nästa skarpa kandidatkörning.
