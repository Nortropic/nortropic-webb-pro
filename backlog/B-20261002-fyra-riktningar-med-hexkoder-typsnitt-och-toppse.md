---
id: B-20261002-fyra-riktningar-med-hexkoder-typsnitt-och-toppse
status: klar
kalla: bevakning
kallref: Prompting Claude Opus 4.8 och Prompting Claude Sonnet 5, Design and frontend defaults (platform.claude.com)
skapad: 2026-10-02
prio: hog
steg: 5
commit: 58d6321
andrad: 2026-10-02T11:45Z
---
# Fyra riktningar med hexkoder, typsnitt och toppsektion, och en exakt specifikation före koden

**Varför:** Steg 5.1 kräver två riktningar; i alla tre byggen var den andra en halmgubbe. Anthropics promptsidor för Opus 4.8 och Sonnet 5 rekommenderar fyra olika riktningar med bakgrund, accent och typsnitt för att få verkligt olika utfall, och en exakt specifikation eftersom modellen följer uttryckliga specifikationer precist.

**Förslag:** bygg-sajt steg 5.1: fyra riktningar, var och en med bakgrundshex, accenthex, namngivet typsnitt, toppsektionens komposition i en mening och den sak ur Bara de har som den bygger på; minst två typsnittskategorier; riktningarna skiljer sig på en namngiven axel. Den valda skrivs som exakt specifikation i KONCEPT.md (hex, typsnitt, radie, sektionsordning) innan kod skrivs. De två starkaste kan bli en parvis fråga i FRAGOR.json.

**Klart när:** KONCEPT.md i nästa bygge har fyra riktningar och en specifikation, och granskarens originalitetsbetyg jämförs med nattbyggenas.

**Klar (2026-10-02):** steg 5.1: fyra riktningar + exakt specifikation
