---
id: B-20261008-nastlade-sessioner-ska-bara-se-flodets-tre-mcp-t
status: vilande
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#E1
skapad: 2026-10-08
prio: normal
steg: main: kontroller/atelje.py, kontroller/mcp/, kontroller/verktygslada.py
---
# Nästlade sessioner ska bara se flödets tre MCP-tjänster, inte användarnivåns servrar

**Varför:** Det verkliga sessionsprovet 2026-10-08 (GR-20261008-r117-claude, sessionsprov/del1-init.json) visar att en skaparsession med flödets argument får 13 MCP-servrar: refero, mobbin och motion, och tio på användarnivå (claude.ai Github, Gmail, Resend, Trybloom, Notion, Google Drive, Jotform, Claude Docs, GitBook, Google Calendar), eftersom --mcp-config ges utan --strict-mcp-config för att projektets Refero ska stå kvar. dontAsk och --allowedTools hindrar anrop, men servrarna startas och skrivande verktyg syns i sessionens verktygslista; Trybloom används inte (ägarens ord 2026-10-05).

**Förslag:** Ge Referos konfiguration uttryckligen (kontroller/mcp/refero.json, med ${REFERO_MCP_TOKEN}) tillsammans med Mobbins och Motions och använd --strict-mcp-config i atelje.session_args; startkontrollens sessionsprov och sessionsprov.py verifierar att init-beskedet bara visar de tre.

**Klart när:** Init-beskedet i en verklig nästlad session visar exakt refero, mobbin och motion; rökprovets argumentprov asserterar --strict-mcp-config med tre filer.
