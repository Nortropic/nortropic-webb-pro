---
id: B-20261007-kandidaternas-oberoende-byggets-processgrans-hin
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r107.md
fynd: GR-20261007-r107#K1
skapad: 2026-10-07
prio: hog
steg: main: kontroller/processgrans.py, kontroller/kandidater.py, kontroller/forhandsvisa.py, kontroller/rokprov/revision/prov_skisskritik.py
andrad: 2026-10-07T18:48Z
---
# Kandidaternas oberoende: byggets processgräns hindrar läsning av andra kandidater och skaparens underlag

**Varför:** Granskaren bekräftade under byggets sandlådeprofil (processgrans.py --skrivbar) att en sidas kod kan läsa en annan kandidats källkod och skaparens text i underlaget när sidan byggs. Profilen tillåter allt utom skrivning och hemligheter. Sessionernas skal är stängt, men byggets kod är en annan väg.

**Förslag:** Neka läsning (deny file-read*) av andra kandidaters kataloger och av underlaget utanför det kandidaten får läsa, per kandidat i processgränsen. Pröva att bygget fungerar och att en sida som försöker läsa en syskonkandidat stoppas.

**Klart när:** Ett prov där en sidas kod försöker läsa en annan kandidats fil vid bygget stoppas, och ett vanligt bygge går. Görs före nästa skarpa kandidatkörning.

**Genomförd på grenen (2026-10-07):** processgrans.lasgrans nekar kandidatbyggets läsning som standard och släpper det egna projektet, sajtens delade node_modules, kandidatens egen temp och de systemdelar bygget behöver. Underlag och övriga kandidater avgränsas; kritikens förhandsvisning använder samma gräns. Kandidatens identitet bevaras före länkupplösning och rötterna förankras, så en projektlänk, ett internt alias eller annan stavning inte väljer bort gränsen. Alias till själva reporoten fungerar fortfarande.

Prov_lasgrans.py prövar faktiska processer, ett syntetiskt Astro/Tailwind/React-bygge, bildbearbetning och fotografering. Bas 8cc786c med telemetri av: fem av sex fall röda, det vanliga bygget grönt. Efter rättelsen: sju fall gröna, också de två rotaliasfallen som tillkom efter separat granskning. Gemensam skrivbar cache i node_modules är fortfarande en begränsning; detta är inte fullständig kandidatisolering. Oberoende slutlig omgranskning och verkligt helbygge återstår. Prov, mutationer och slutligt rökprov redovisas i RAPPORT-2026-10-07-r109-codex; inga externa modell- eller MCP-anrop ingår.
