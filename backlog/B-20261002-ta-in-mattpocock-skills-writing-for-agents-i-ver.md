---
id: B-20261002-ta-in-mattpocock-skills-writing-for-agents-i-ver
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · mattpocock/skills
skapad: 2026-10-02
prio: normal
steg: 8 Dom (hur en dom blir en textändring) och backlog-skillen
---
# Ta in mattpocock/skills writing-for-agents i verktygslådan och låt backlog-skillen använda den vid varje ändring i en skill eller kunskapsfil

**Varför:** Ta in: vi har ingen regel för hur en skilltext skrivs och rensas, och bygg-sajts SKILL.md växer med varje dom (333 rader, samma betydelse på flera ställen). writing-for-agents ger det vi saknar: tydliga slutvillkor per steg, det positiva målet i stället för förbud, en betydelse på ett ställe och rensning av no-ops och inaktuella lager.

**Förslag:** Klona mattpocock/skills @ d81f3a1 (MIT). Kopiera skills/productivity/writing-for-agents/SKILL.md och SKILL-MECHANICS.md till .claude/skills/writing-for-agents/ med repots LICENSE; ta bort agents/openai.yaml. Skriv om description: används när en session ändrar en skill (bygg-sajt, kirurg, backlog), CLAUDE.md eller en fil i kunskap/, särskilt när en dom eller backlogpost blir en textändring; inte av byggen (de rör inte .claude/ eller kunskap/). KALLA.md med källa, commit, licens, datum och vad som togs bort. I .claude/skills/backlog/SKILL.md steg 3, efter rad 26–27: en rad om att läsa writing-for-agents före en ändring i en skill eller kunskapsfil, och att ändringen prövas mot dubbletter och inaktuella rader i stycket den hamnar i. Krock att hantera: klass (c) i B-20261002-valj-formen-pa-en-domandring-efter-hur-bygget-br (förbud med undanflykter) skrivs som förbud plus det positiva målet, så som källan kräver för förbud.

**Klart när:** Mappen .claude/skills/writing-for-agents/ finns med SKILL.md, SKILL-MECHANICS.md, LICENSE och KALLA.md; granska_repo.py på kopian är inte HÖG; backlog-skillens steg 3 pekar på den
