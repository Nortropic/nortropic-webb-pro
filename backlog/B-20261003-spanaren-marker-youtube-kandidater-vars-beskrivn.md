---
id: B-20261003-spanaren-marker-youtube-kandidater-vars-beskrivn
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Jack Roberts, "Claude Code + TinyFish = Unlimited FREE Scraping" (YouTube qqRo3vwAoPw)
skapad: 2026-10-03
prio: normal
steg: spaningen (kontroller/spana.py, dashboarden)
---
# Spanaren märker YouTube-kandidater vars beskrivning anger betalt partnerskap

**Varför:** Domen över videon var nej: en 44 sekunders betald annons gick till kirurgen på fyra ordträffar. Spanaren läser hela beskrivningen ur flödet men letar inte efter YouTubes egen märkning av betalt innehåll, så ägaren kan inte sålla annonser före intag.

**Förslag:** kontroller/spana.py, rss(): efter att media:description lästs (rad 219–222) och före kandidat() kapar till 600 tecken, matcha den fulla texten mot ett mönster för 'Paid partnership', 'includes paid promotion', 'sponsored' och '#ad' (skiftlägesokänsligt) och lägg varningen 'betalt partnerskap' i kandidatens varning-lista via extra. Ingen kandidat avfärdas automatiskt; dashboarden visar varningen som de andra. Ett prov med en fixtur ur ett YouTube-Atom-flöde med raden 'Paid partnership with X.' sist i beskrivningen.

**Klart när:** Spaningen av Jack Roberts flöde ger kandidaten qqRo3vwAoPw varningen 'betalt partnerskap' i dashboarden, provet är grönt och kontroller/rokprov.sh slutar grönt.
