---
id: B-20261013-figma-mcp-n-i-flodets-sessioner-bakom-kundvakten
status: vilande
kalla: bevakning
kallref: ägarens beslut 2026-10-13, punkt 6 och 8 (underlag/uppdrag/PROMPT-Nortropic-Astro-artefakt-resten-20261013.md); Figmas MCP-dokumentation, Tools and prompts (developers.figma.com, läst 2026-10-12 i valideringen); pluginens .mcp.json 2.2.120
skapad: 2026-10-13
prio: normal
steg: flödets sessioner (kontroller/designfas.py start, kontroller/atelje.py, kontroller/kundvakt.py, kontroller/kompetens.py)
---
# Figma-MCP:n i flödets sessioner bakom kundvakten: läsvägen och generate_image

**Varför:** Ägarens beslut 2026-10-13 ger Figma två uppgifter: läsvägen ur kundens egen Figmafil (get_variable_defs, get_design_context, search_design_system, get_screenshot) i bandets stationer underlag och overlamning, och generate_image för illustrativt material inom Pro-krediterna. Texterna har uppgifterna (build-design/NORTROPIC.md, kunskap/bild.md, metodkartans rad mcp:figma), men ingen av flödets sessioner når Figma: utföraren (designfas.start), ateljén och helbygget startar med --strict-mcp-config och bara Refero, Mobbin, Motion och 21st, kundvakt.MATCH prövar inte mcp__figma__, och dontAsk nekar då anropen. Figma finns i dag bara som pluginen på användarnivån (figma@claude-plugins-official 2.2.120, http https://mcp.figma.com/mcp med OAuth). Om samma inloggning räcker för en server ur --mcp-config, eller om pluginen kan slås på i sessionens --settings under --strict-mcp-config (Figma-piloten 2026-10-06 slog på den utan strict), är oprövat.

**Förslag:** 1) kontroller/mcp/figma.json (type http, https://mcp.figma.com/mcp) och ett sessionsprov som visar verktygslistan under --strict-mcp-config; räcker inte pluginens OAuth loggar ägaren in en gång med /mcp i en interaktiv session. 2) kompetens.MCP['figma'] med get_variable_defs, get_design_context, search_design_system, get_screenshot, get_metadata och generate_image, MCPNAMN och ett block tjanstverktyg figma i metodkartan med ett beslut per verktyg (use_figma, upload_assets, html_to_figma, generate_figma_design, Code Connect och Weave: ingen uppgift, med skäl). 3) kundvakt.MATCH med mcp__figma__.*: fileKey bara kundens egen fil (registrerad i kundunderlaget), nodeId och planKey som id-fält, search_design_system och generate_image genom samma namn- och ortprövning som Refero och Mobbin, generate_image bara med planKey ur kontots team. 4) Figmas konfiguration i designfas.start, och i ateljén där stationen körs som pass; aldrig i helbyggets byggmcp. 5) Bandets tabell får mcp:figma i underlag, komposition och overlamning när verktygen når sessionen, och designfas-kartans rad får provdatum. Ändringen rör kundvakten och sessionernas argument och granskas som en säkerhetsändring.

**Klart när:** En utförarsession startad med designfas.py start listar Figmas verktyg; kundvakten släpper get_variable_defs på kundens registrerade fil och stoppar en annan fileKey och en generate_image-prompt med kundens namn (prov i kontroller/rokprov, provfilen i rökprovets lista); rökprovet slutar grönt.
