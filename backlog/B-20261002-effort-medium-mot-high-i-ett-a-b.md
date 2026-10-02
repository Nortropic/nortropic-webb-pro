---
id: B-20261002-effort-medium-mot-high-i-ett-a-b
status: klar
kalla: bevakning
kallref: Prompting Claude Opus 5.5, Calibrate effort (platform.claude.com, läst 2026-10-02)
skapad: 2026-10-02
prio: normal
steg: kor.sh
commit: 9fd7008
andrad: 2026-10-02T11:57Z
---
# Effort medium mot high i ett A/B

**Varför:** Anthropics sida för Opus 5.5: börja på medium, som på Opus 5.5 matchar eller slår Opus 5 på high, och spara xhigh och max för uppmätt vinst. kor.sh och granskaren kör high utan att det är mätt.

**Förslag:** Samma verksamhet byggd två gånger, NWP_EFFORT=medium och high. Ägaren väljer parvis utan att veta vilken som är vilken; tid, turer och granskarens betyg redovisas bredvid.

**Klart när:** Ägarens val och siffrorna står i LARDOMAR.md, och kor.sh har den effort som vann.

**Klar (2026-10-02):** mekanismen klar (ab.py + vyn Jämförelser); själva körningen startar ägaren, två fulla byggen
