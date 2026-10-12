# Källa

- **Skill:** humanizer, blader/humanizer v3.1.0 (Siqi Chen). Ersätter sedan 2026-10-13 Hermes Agents port av 2.5.1.
- **Källa:** https://github.com/blader/humanizer, repots rot (skillen är repots SKILL.md), commit
  `225a6f39ac85f76ee48dbad772ea4abe4ed6c9d8` (2026-09-27T22:54:38-07:00, alltså 2026-09-28T05:54:38Z; tagg v3.1.0,
  standardgrenen main; källans HEAD är samma commit, kontrollerat 2026-10-13). Byggd på Wikipedia "Signs of AI writing"
  (WikiProject AI Cleanup).
- **Karenstid:** 225a6f3 var vid intaget 2026-10-13 den senaste commit i källan som var äldre än karenstiden (tre dygn;
  `kunskap/beroenden.md`, Skydden runt en ny version). Ingen nyare commit togs.
- **Licens:** MIT. `LICENSE` (Siqi Chen, 2025), repots licensfil, byte för byte. Wikipedia-underlaget: CC BY-SA 4.0.
- **Intagen:** 2026-10-13 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-13 · blader/humanizer), på
  ägarens mandat att genomföra valideringens åtgärder. Porten den ersätter kom ur https://github.com/NousResearch/hermes-agent
  (`skills/creative/humanizer/` @ 0a374d1, intagen 2026-10-02); `LICENSE-nous-research` togs bort med den, eftersom
  ingen text ur Hermes finns kvar.
- **Ordagrant:** `SKILL.md` (utom två ändringar, nästa punkt), `LICENSE` och `agents/openai.yaml` (metadata för
  OpenAI-kompatibla agenter; Claude Code läser den inte; med på ägarens beslut 2026-10-05 att skillsen ska vara i sin
  fullo, som för better-*).
- **Ändrat i SKILL.md:** frontmatterns beskrivning (svensk; säger var bygget använder skillen och att `NORTROPIC.md`
  läses först) och en rad direkt efter frontmattern som pekar på `NORTROPIC.md`, så att också en aktivering med
  Skill-verktyget ser förordet. Resten, `license` och `metadata.version` inräknade, är byte för byte upstream.
  Trevägssammanslagningen prövad 2026-10-13: samma två ändringar på v3.0.0, ihopslagna till v3.1.0 med
  `git merge-file`, gav ingen krock och blev lika med v3.1.0 med ändringarna.
- **Tillagt:** `NORTROPIC.md`, förordet "Så används humanizer i nortropic-webb-pro", i en egen fil i stället för överst i
  SKILL.md. Tre av dess punkter (tak per sektion, strängare kort text, skriv om ur sakuppgiften) är med egna ord ur
  coreyhaines31/marketingskills `skills/copywriting/references/ai-tells.md` @ 13c3832 (MIT, Corey Haines 2025),
  tillagda 2026-10-02 (kunskap/REGISTER.md · 2026-10-02 · coreyhaines31/marketingskills); inget kopierat ordagrant.
- **Utelämnat:** `scripts/validate-package.py`, som prövar repots paketering (README:s mönstertabell, plugin-manifesten
  och versionen i fyra filer): inget av det finns här, och flödet kör det aldrig. `README.md`, `CHANGELOG.md`,
  `AGENTS.md`, `.claude-plugin/`, `.cursor-plugin/` och `.github/`: repots dokumentation, paketering och arbetsflöden,
  inte skillen.
- **Mönstrens nummer:** portens 1–29 är upphovets 2.5.1, och upphovets CHANGELOG (3.0.0) ger de nya: 1→13, 2→17, 3→15,
  4→16, 5→17, 6→13, 7→12, 8→18, 9→1, 10→6, 13→11, 14→8, 15→19, 16→19, 17→20, 18→20, 19→21, 20→22, 21→23, 22→22,
  24→9, 25→13, 26→10, 27→3, 28→4, 29→24. Utgick: 11 (synonymväxling) och 12 (falska spann), som Wikipedia nu räknar
  som mänskliga eller historiska, och 23 (utfyllnadsfraser). Hermes egna 30–34: 31 är §2; 30 (påtvingade metaforer)
  finns delvis i §3, 32 (retorisk fråga) och 33 (öppningsfraser) delvis i §4, 34 (lugnande slutrepliker) inte alls.
  Nya i v3: §5, §7, §14, §25 och §26.
- **Krockar med våra beslut:** §21 vill ha raka citattecken, men svenska ” ” är rätt; §8 vill ha en slutlig text utan
  tankstreck, men hos oss gäller ett tak och tankstreck i intervall står kvar; §10 gäller engelska; *Voice* låter
  provet upphäva mönstren och skrivaren lägga till åsikter och reaktioner, men hos oss upphäver röstprovet inte taket
  eller reglerna för kort text, och inga egna åsikter läggs till; steg 2 säger "ask for it", men ingen svarar i flödets
  sessioner, så uppgiften beställs. `NORTROPIC.md` löser alla och hänvisar till mönstren med nummer och rubrik:
  numrerar en ny version om mönstren, skrivs NORTROPIC.md om i samma intag.
- **Förgranskning 2026-10-13:** `kontroller/granska_repo.py` på en kopia av klonen gav LÅG: inga dolda tecken, ingen
  text riktad till agenter, inga behörigheter, hookar eller MCP-servrar, ett skript (det utelämnade). Mappen här: LÅG,
  inga skript.
- **Underhållet:** källans väg är repots rot, och då jämför `plan_for_skill` (`kontroller/underhall.py`) hela repot.
  Prövat 2026-10-13 med den här mappen på v3.0.0 mot v3.1.0: SKILL.md slogs ihop rent, men README.md, AGENTS.md,
  plugin-manifesten och scripts/validate-package.py blev krockar, och nya filer (CHANGELOG.md, .github/, ett nytt
  plugin-manifest) hade lagts i mappen. Nästa version tas därför in genom en granskad ändring för hand, tills
  underhållet följer bara de intagna filerna (backlog B-20261012-underhallet-foljer-bara-de-intagna-filerna-nar-e).
- **Så används skillen här:** kärna i bandets innehållsstation, alternativ (välj) i kompetensblocken innehall (med
  ds_innehall), forberedelse och helbygge, och i bygg-sajt steg 4 på INNEHALL.md efter copykontrollen. Metodkartan
  listar `NORTROPIC.md` före `SKILL.md` överallt där skillen står.
