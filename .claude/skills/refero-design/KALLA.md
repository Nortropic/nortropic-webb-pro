# Källa

- **Skill:** `refero-design` (mappen `refero-design`). Referos officiella designskill: forskning först i Referos tre
  lager (stilar för visuell riktning, skärmar för konkreta mönster, flöden för resor), ett referenslås och en
  beslutsliggare före implementationen, ingen medelvärdesbildning mellan referenser, tokenroller och bildroller som
  bevaras, och visuell kontroll av det renderade resultatet mot låset (P0–P3). Hantverksreferenser för typografi, färg,
  rörelse, ikoner, formulär och detaljer, copy och anti-AI-slop.
- **Källa:** https://github.com/referodesign/refero_skill, `skills/refero-design/`, commit
  `a9b54a3e62a6391f5f5ab7a20e4ddb32fb79a27d` (2026-09-05T14:11:03+02:00, standardgrenen master), VERSION 1.0.2.
- **Licens:** MIT (`LICENSE` ur repots rot, kopierad till mappen).
- **Intagen:** 2026-10-05 på ägarens uppdrag 18:53Z, punkt 2: "Kontrollera även Referos officiella skill och hur dess
  relevanta arbetsmetod kan användas i vårt befintliga flöde. Installera inte överlappande verktyg utan att först
  kontrollera vad vi redan har." Ordagrant: alla 12 filer i skillmappen, oförändrade. Våra tillägg: `KALLA.md`,
  `LICENSE`.
- **Utelämnat:** repots MCP-manifest (`.mcp.json`, `mcp.json`, `server.json`; Refero MCP har vi redan, med nyckeln i
  ägarens hemlighetsmapp), pluginmanifesten, `gemini-extension.json`, `scripts/check-release` och `assets/`.
- **Förgranskning 2026-10-05:** `kontroller/granska_repo.py` gav LÅG: inga dolda tecken, ingen text riktad till agenter,
  inga behörigheter, hookar eller skript.
- **Överlapp, prövat mot det vi har:** arbetsmetoden (forskning först, referenslås, beslutsliggare, visuell kontroll mot
  låset) finns inte i någon annan skill här och är kärnan i rollerna planprövning och design och komposition
  (`kunskap/metodkarta.md`, Kompetenserna). Hantverksreferenserna överlappar impeccable (typeset, colorize, animate),
  better-typography, better-colors, emil-* och better-writing; de står därför som alternativ, inte kärna.
  `references/visual-workflow.md` är kärna i granskningen.
- **Krockar med våra beslut:** "Do not use generic frontend/product design skills as a parallel design authority" —
  här fördelar metodkartan rollerna, och Avgörandena avgör krockar. "Default to three reference-locked options and ask
  the user to choose" — kandidatflödet gör omkring tio och ägaren väljer i dashboarden. "Ask only for missing
  information" — ingen svarar i flödets sessioner; antaganden skrivs i RIKTNING.md. Bildgenerering: flödets sessioner
  har ingen bildgenerator; material som saknas beställs. Listan över "calm editorial"-risker (krämvit yta, serif,
  kursivt ord) är en granskningsfråga, inget förbud (ägarbeslutet 2026-10-03).
- **Så används skillen här:** referenslåset (Primary reference, Preserve, Borrow only, Role rules, Media strategy,
  Reject, Token commitments) och beslutsliggaren skrivs i kandidatens RIKTNING.md; stilpaketet ur Refero
  (`kontroller/stilpaket.py`: originalexporten, CSS-variablerna och förhandsbilderna) är huvudreferensens material.
  Forskningen i Refero och Mobbin görs gemensamt före skaparna; skaparen kompletterar avgränsat genom tjänsten.
