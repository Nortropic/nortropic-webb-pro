---
id: B-20261003-referenstjanster-i-befintligt-flode-inspo-a-b-fo
status: vilande
kalla: bevakning
kallref: Codex kartläggning av referenskällor och byggverktyg, 2026-10-03
skapad: 2026-10-03
prio: normal
---
# Referenstjänster i befintligt flöde: Inspo-A/B först, sedan Refero som variabel och Mobbin på ett fall med flerstegsflöde (ägarbeslut om betald åtkomst)

**Varför:** Codex 2026-10-03: Inspo-anslutningen finns redan kontrollerat i kor.sh och A/B pågår; Mobbin och Refero har officiella Claude Code-anslutningar men kräver betald åtkomst; Refero skiljer sökresultat från hämtning av själva skärmbilden, och visuell bedömning kräver bilden. Antal hittade bilder är inget utfallsmått.

**Precisering (Codex 2026-10-03):** sist i ordningen, efter metodproven. Mobbin (prissidan läst 2026-10-03, https://mobbin.com/pricing): gratisplanen har begränsat urval av appar och sajter och ingen MCP; Pro ger alla appar och sajter, flöden, Deep Search och MCP ("Connect Mobbin to AI agents & tools like Claude, Codex, and Cursor") för 100 kr per månad vid årsbetalning, Team 160 kr per medlem och månad. Refero: MCP kräver Pro enligt Codex; sidan https://refero.design/mcp är en JavaScript-app som inte gick att läsa utan webbläsare, så priset är inte verifierat av oss. Referos mest relevanta bidrag är arbetssättet i deras exempelprocess (visuell riktning, konkreta skärmlösningar, användarflöden, implementationsplan; https://github.com/referodesign/refero_skill/blob/master/skills/refero-design/references/example-workflow.md), inte tjänsten i sig. Exempelprocessen (läst 2026-10-03): fas 0 brief; fas 1 stilar med refero_get_style, 3–4 referenser ur närliggande domäner till en "reference lock" (palett, typografi, kanter); fas 2 skärmar med refero_get_screen (konkreta mönster, strukturbeslut); fas 3 flöden med refero_get_flow; fas 4 en beslutsliggare där varje val pekar på sin källa och briefen; fas 5 tokens och sidstruktur med en kvalitetsgrind mot generiska mallar. Det motsvarar vår referensjakt, REFERENSER.md och KONCEPT.md, med liggaren som den del vi saknar.

**Ägarbeslut 2026-10-03:** "jag tänker att jag skaffar refero mcp pro och mobbin mcp pro". Anslutning (kontrollerat samma dag): Mobbin MCP är hostad på https://api.mobbin.com/mcp, OAuth i webbläsaren vid första anslutningen, ingen nyckel, Pro eller högre, verktygen search_screens, search_flows och search_sections, 60 anrop per minut (docs.mobbin.com/mcp). Refero MCP är hostad på https://api.refero.design/mcp, OAuth vid första anslutningen, betald plan (README i github.com/referodesign/refero_skill). Ingen av dem kräver npx eller lokal kod. Verifierat 2026-10-03 kväll: Refero ansluts med personlig nyckel ur ~/.nortropic-hemligheter/webb-pro/refero.env (anslutningsfilen bär ${REFERO_MCP_TOKEN}; headless prov gav 1003 träffar), Mobbin med OAuth som ägaren gjorde i /mcp (headless prov gav 20 träffar). Båda går att använda obevakat som NWP_MCP_CONFIG-variabel; kvar är själva A/B-körningarna när kedjan startas om.

**Förslag:** Vänta in Inspo-A/B (therese-hundvard, hundsalong-julia). Är referensunderlaget fortfarande svagt: Refero som NWP_MCP_CONFIG-variabel i ab.py på samma sätt som Inspo (hostad ändpunkt, bara lässverktyg, bilden hämtas med bildverktyget och öppnas som alla referenser med inspektera.mjs). Mobbin bara för ett uppdrag med bokning eller annat flerstegsflöde. Måttet: relevans i valda referenser och ägarens blinda val.

**Klart när:** Ägaren har beslutat om betald åtkomst; en A/B per tjänst är körd och dömd; LARDOMAR.md säger vilken tjänst som behålls, eller att ingen gör sajterna bättre.
