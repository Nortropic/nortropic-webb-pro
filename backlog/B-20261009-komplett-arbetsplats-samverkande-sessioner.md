---
id: B-20261009-komplett-arbetsplats-samverkande-sessioner
status: pagar
kalla: dom
kallref: BESLUT.md
skapad: 2026-10-09
prio: hog
steg: BESLUT.md 2026-10-09 (den kompletta arbetsplatsen); kunskap/arbetsyta.md; kontroller/meddelanden.py, kontroller/lopare.py, dashboard/
andrad: 2026-10-09T17:40Z
---
# Den kompletta arbetsplatsen: samverkande sessioner, paus, beslut och extern granskare i arbetsytan (ägarens uppdrag 2026-10-09 ~11:22Z)

**Varför:** Ägarens uppdrag 2026-10-09 (ordagrant i BESLUT.md, tillägget om den kompletta arbetsplatsen): sköta
Nortropic genom arbetsytan utan VS Code eller terminalsteg i det normala arbetet; skriva till en arbetare medan den
arbetar; arbetare och granskare som lämnar fynd till varandra inom sina uppdrag; ägarinstruktioner skilda från
agenternas fynd; Codex som granskare; paus, stopp och återupptagning med tydlig betydelse; sessioner som går att läsa
och fråga; förhandsvisning och beslut samlade; blindningen bevarad; lokal körning och befintlig kompetens.

**Förslag:** En registrerad meddelandebuss i motorn (kontroller/meddelanden.py) som enda huvudväg, levererad till
motorns sessioner genom strömmande inmatning i en löpare (kontroller/lopare.py) med paus som avbrott och
återupptagning som meddelande; dashboardens del i dashboard/samverkan.py (meddelanden, beslut över förslag, mandat,
paus, historik, följdfrågor som förgreningar, beslut bundna till bilden, extern granskares väg); arbetsytan som startvy
med vyerna för detta; kontroller/extern_granskare.py för Codex; partnerns A/B-spärr och sessionsbindning.

**Klart när:** Användarresans nio punkter i uppdraget är verifierade i ett verkligt avgränsat prov med fiktivt material
i en provinstans, med VS Code stängt och utan terminalsteg i resan; rökprovet är grönt på den exakta versionen; en
oberoende granskning är redovisad; dokumentationen säger vad som är inkopplat, prövat med attrapper, verifierat med
riktiga sessioner och inte verifierat i ägarens arbetsflöde; aktiveringen är gjord efter huvudsessionens kvalitetsprov.
Varje del av dashboarden finns i arbetsytan, med dess ram och navigering, och knappen Klassisk vy, menyn Fler vyer och
den klassiska topplisten är borta, utan att någon funktion försvunnit (ägarens besked 2026-10-09 ~17:11Z: "allt ska ju
in i det här nya vyn").

**Läget 2026-10-09 ~17:40Z:** Användarresan godkändes i försök 6 och aktiverades i a787bc5 efter fullprovet. Ägaren
påpekade därefter att de klassiska vyerna fanns kvar: inte klart. Flytten in i arbetsytan pågår i grenen
claude/arbetsplats-20261009.

**Pagar (2026-10-09):** Byggt och prövat med attrapper och med verkliga Haiku-sessioner genom atelje.session (meddelande
under arbetet, paus och återupptagning); vyerna i en provinstans. Kvar: det verkliga provet av hela användarresan
(efter ~14Z, ett tungt prov åt gången), fullprovet, den oberoende granskningen och aktiveringen.
