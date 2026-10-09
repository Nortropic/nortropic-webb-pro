---
id: B-20261007-blindningen-listan-i-kundens-underlag-galler-ock
status: pagar
kalla: granskning
kallref: granskningar/GR-20261007-r107.md
fynd: GR-20261007-r107#K2
skapad: 2026-10-07
prio: normal
steg: main: kontroller/kandidater.py (blind_nekas)
commit: fcfd3e9
andrad: 2026-10-09T10:06Z
---
# Blindningen: listan i kundens underlag gäller också filer som uppstår efter starten

**Varför:** Listan i underlag/<slug> bygger på en uppräkning vid starten och på mönster. UPPTAGNA-VAL.md nekas bara om den finns vid starten. Det är en teoretisk lucka; inget skrivs dit under en skisskritik i dag utöver det mönstren täcker.

**Förslag:** Neka allt i underlag/<slug> utom listan med ett mönster som gäller också senare filer, om behörigheterna tillåter det.

**Klart när:** En fil som skapas i underlag/<slug> under kritikens session går inte att läsa.

**Vilande (2026-10-08):** Nattens uppdrag 2026-10-08/09, delvis i 3a1e19b: det systemet självt kan skriva i underlag/<slug>/ under en blind session nekas också när det uppstår efter starten (prov_skisskritik fall 10, rött mot 03fab0e). Kvar: en fil som något annat lägger dit under sessionen; behörigheterna kan inte säga allt utom listan. Väntar på ägarens beslut: en krok som prövar varje läsning, med ett verkligt sessionsprov, eller att täckningen räcker (RAPPORT-2026-10-08-natt-codex-rester-backlog).

**Klar (2026-10-09):** Ägarens uppdrag 2026-10-09 (GR-20261009-natt-omgranskning-codex): den lokala mekaniken. Read, Glob och Grep står inte i de blinda sessionernas --allowedTools, och blindvakten (kontroller/blindvakt.py) prövar varje läsning när den görs mot sessionens tillåtelselista (kandidater.blind_tillatet); en okänd fil som tillkommer efter starten nekas, och en vakt som faller öppnar ingenting. Skisskritiken och granskningens första pass. prov_omgranskning Blindning, rött mot 2c7aa5a på den sena filen. Att Claude Code verkställer det (krokens tillåtelse, dontAsk när kroken dör) kräver förmågeprovet S2 och S3 (kontroller/formagoprov.py), som är förberett men inte kört. Inte verifierad.

**Pagar (2026-10-09):** Återöppnad 2026-10-09: ett verkligt prov av en parallell session (elinhaggstrom-b3, 07:43Z, Claude Code 2.1.290, session 0c6e6c50…) visade att dontAsk inte nekar Read i arbetskatalogen och att en krok vars tidsgräns slår till inte blockerar. Rättat lokalt (a063099): krokens tidsgräns 60 s mot vaktens egna 20 s, och texterna säger vad som spärrar. Kvar: en krok som hänger helt släpper igenom en läsning i arbetskatalogen; att stänga det kräver blinda sessioner i en arbetskatalog utan hemligt, och ett verkligt sessionsprov (formagoprov.py S3, som väntas falla i dag).

**Pagar (2026-10-09):** Förmågeprovet kört på main bcfb70e 10:04Z (ägarens mandat ~09:40Z; underlag/formagoprov/20261009t1004, claude-sonnet-5-5): S2 godkänt (blindvakten tillät briefen och nekade den sena filen med Read, Glob och Grep, och RIKTNING.md), S3 underkänt som väntat: med en krok som inte svarar lästes briefen och den sena filen, och Glob och Grep hittade den; bara RIKTNING.md stoppades, av en nekanderegel. Rättat lokalt (4d055ee): de blinda sessionerna startar i en egen tom arbetskatalog utanför motorns rot (atelje.blind_arbetsyta), där dontAsk nekar det som vakten inte tillåtit; reglerna och kommandona absoluta, också i kundrepoläget. Förmågeprovet får S2.arbetsyta, S2.skill och S3.arbetsyta. Inte verifierat förrän förmågeprovet körts om på den pushade rättelsen.
