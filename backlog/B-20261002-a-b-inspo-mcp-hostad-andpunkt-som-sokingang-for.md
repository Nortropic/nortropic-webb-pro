---
id: B-20261002-a-b-inspo-mcp-hostad-andpunkt-som-sokingang-for
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS Ow_z94c3wKk + Nutlope/inspo
skapad: 2026-10-02
prio: normal
steg: 3 (referenser, hantverksrollen); kor.sh (anslutningar i bygget)
andrad: 2026-10-03T00:53Z
---
# A/B: Inspo MCP (hostad ändpunkt) som sökingång för referenser i steg 3, mot dagens egna referensjakt

**Varför:** Kirurgens dom är prova A/B: Inspo är ett kuraterat arkiv om 832 riktiga sajter med mobil och desktop parvis, sökbart med briefen och med normer mätta ur arkivet, en metod vi saknar och som gör referensjämförelsen billigare. Mot det står att arkivet saknar hantverkare och lokala tjänster, att agentens egna exempelsajter delar ett och samma mönster i första vyn, och att kor.sh medvetet laddar inga anslutningar i ett bygge; bara ett bygge på en riktig verksamhet visar om referenserna gör sajten bättre.

**Förslag:** A-armen: kor.sh rad 62 får, när NWP_MCP_CONFIG är satt, --mcp-config "$NWP_MCP_CONFIG" bredvid --strict-mcp-config; ny fil kontroller/mcp/inspo.json med den hostade HTTP-ändpunkten https://inspomcp.dev/api/mcp (ingen npx, ingen lokal kod). .claude/skills/bygg-sajt/SKILL.md steg 3, efter rad 153: ett stycke om att recommend, search_screens och get_screen används för hantverksrollen och mobilparen som sökingång när Inspo är anslutet; varje vald referens öppnas ändå med inspektera.mjs och skrivs i REFERENSER.md med källa Inspo; get_reference_jsx, paletteSuggestion och heroGuidance används aldrig (rad 252 och mobilen först gäller). B-armen: som i dag. Två körningar per arm på samma verksamhet; blind parvis jämförelse i dashboarden med ombytt ordning; en annan modell än byggaren som domare; oenighet = oavgjort; tokens, minuter och antal Inspo-anrop ur korning-*.jsonl redovisas bredvid kvaliteten.

**Klart när:** Fyra körningar klara (två per arm), AB-post i LARDOMAR.md med ägarens blinda val och domarens, kostnad per arm redovisad, och beslut om stycket i steg 3 och NWP_MCP_CONFIG står kvar eller tas bort.
