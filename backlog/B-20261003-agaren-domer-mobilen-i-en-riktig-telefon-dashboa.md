---
id: B-20261003-agaren-domer-mobilen-i-en-riktig-telefon-dashboa
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS, Every Level Of Claude Code Loop Engineering Explained (YouTube PLyRe6Zk--8)
skapad: 2026-10-03
prio: normal
steg: steg 8 (ägarens dom), dashboarden
---
# Ägaren dömer mobilen i en riktig telefon: dashboardens visning av sajten får en adress på det egna nätverket, som QR-kod bredvid knappen Öppna vår sajt

**Varför:** Domen över videon är nej, men en sak är bättre där: ägaren ser prototypen i en riktig telefon [SKÄRM 22:36]. Våra tre domar bedömde mobilen i 390 px-emulering (LARDOMAR.md rad 30, 55, 79) och gav Mobil ergonomi Okej i två av tre (rad 35, 60); teoretisk-grund.md rad 20 listar riktiga användare som vårt gap, och ägaren i en telefon är det närmaste vi har.

**Förslag:** dashboard/server.py visa() (rad 714–722): visningen av kunder/<slug>/sajt/dist startas med provets Server (kontroller/prova.py rad 142–143) bunden också till datorns adress på det lokala nätverket, bara för den statiska visningen; dashboarden själv och alla POST förblir på 127.0.0.1 (rad 9, 855). Svaret från /visa/<slug> får med nätverksadressen, och dashboard/index.html visar den som QR-kod (ritad lokalt, inget tredjepartsanrop) bredvid knappen Öppna vår sajt (rad 212) och i A/B-vyn (rad 447). Frågeformulärets mobilfrågor (server.py rad 57) får en rad som ber ägaren svara ur telefonen. Kräver ägarens ja: den statiska visningen blir nåbar för andra på samma nätverk medan dashboarden kör.

**Klart när:** Dashboarden visar en QR-kod vid Öppna vår sajt; en telefon på samma Wi-Fi öppnar sajten via den; dashboardens egna sidor och POST svarar fortfarande bara på 127.0.0.1 (prövat med curl mot nätverksadressen: sajten svarar 200, dashboardens / svarar inte); kontroller/rokprov.sh grönt.
