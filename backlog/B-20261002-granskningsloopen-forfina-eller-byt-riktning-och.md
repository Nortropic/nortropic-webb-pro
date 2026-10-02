---
id: B-20261002-granskningsloopen-forfina-eller-byt-riktning-och
status: klar
kalla: bevakning
kallref: code.claude.com/docs/en/best-practices, Add an adversarial review step; Harness design for long-running application development
skapad: 2026-10-02
prio: normal
steg: 5
commit: 6a4f777
andrad: 2026-10-02T12:09Z
---
# Granskningsloopen: förfina eller byt riktning, och jämför bästa mot sista omgången

**Varför:** Claude Code best practices: en granskare som ombeds hitta brister rapporterar nästan alltid några, och att jaga varje fynd leder till överarbete. Anthropics harness-artikel: författaren föredrog ofta en mellanomgång framför den sista, och generatorn ska välja mellan att förfina och att byta estetik.

**Förslag:** bygg-sajt steg 5.6: efter varje granskning en rad i rapporten: förfina eller byt riktning, och varför. Efter två omgångar med originalitet under 7 byter byggaren till nästa av de fyra riktningarna. granska.py sparar redan rutorna per omgång; loopen avslutas med en parvis jämförelse, med ombytt ordning, mellan bästa och sista omgången.

**Klart när:** Rapporten i nästa bygge har en rad per granskning och jämförelsens utfall.

**Klar (2026-10-02):** granska.py --jamfor, GRANSKNINGSLOGG och byt riktning i steg 5.6
