---
id: B-20261003-reddit-i-spaningen-slapp-igenom-reddit-com-med-p
status: vilande
kalla: bevakning
kallref: kunskap/REGISTER.md 2026-10-02 (Reddit-inlägget i r/ai_website_builder); ägaren 2026-10-03
skapad: 2026-10-03
prio: normal
steg: spaningen, kirurgen
andrad: 2026-10-05T06:55Z
---
# Reddit i spaningen: släpp igenom reddit.com med paus, och låt kirurgen läsa trådar via Reddits RSS

**Varför:** Ägaren 2026-10-03: "Reddit kan nog ha mycket på AI webb design också". Tre sammanslagna flöden står i kunskap/spaning-kallor.md med vikt 0: spana.py hoppar över reddit.com (HOPPA_VARD), eftersom kirurgen 2026-10-02 inte kunde läsa en Reddit-tråd (spärrsida, inloggning, WebFetch nekad). Reddits RSS fungerar utan inloggning, också per tråd, men gav 429 vid 10 s mellan anropen och fungerade vid 20 s.

**Förslag:** Efter A/B-kedjan. kontroller/spana.py: ta bort reddit ur HOPPA_VARD och håll minst 20 s mellan anrop till reddit.com. Kirurgen läser en tråd via <trådens adress>/.rss (inlägget och kommentarerna), med kontroller/sida_till_text.py eller en liten egen hjälpare, och en rad om det i .claude/skills/kirurg/SKILL.md. Sätt sedan vikterna till 0,9, 0,8 och 0,8.

**Klart när:** En spaning ger Reddit-kandidater utan 429, kirurgen bedömer en Reddit-tråd med belägg ur trådens RSS, och rokprov.sh är grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: allt återstår; rökprovet behöver ett fall som visar pausen per värd, inte bara att reddit släpps igenom.
