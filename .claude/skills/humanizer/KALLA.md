# Källa

- **Skill:** humanizer, Hermes Agents port av blader/humanizer 2.5.1.
- **Källa:** https://github.com/NousResearch/hermes-agent, `skills/creative/humanizer/`, commit 0a374d1
  (2026-10-02). Upphov: https://github.com/blader/humanizer, byggd på Wikipedia "Signs of AI writing" (WikiProject AI
  Cleanup, CC BY-SA 4.0).
- **Licens:** MIT. `LICENSE` (Siqi Chen, 2025) och `LICENSE-nous-research` (Nous Research, 2025).
- **Intagen:** 2026-10-02 efter kirurgens dom "ta in" (kunskap/REGISTER.md · 2026-10-02 · NousResearch/hermes-agent).
- **Borttaget:** frontmatterns version, author, license, platforms och metadata; avsnittet "How to use it in Hermes";
  verktygsnamnen read_file, patch och write_file i Process; och Hermes-svansen i meningen "Also apply this skill to your
  own output…" (SKILL.md:44, kortad till den allmänna regeln). Inga allowed-tools eller hooks fanns. Källans HEAD
  9b6fc23 (kontrollerad 2026-10-05) ändrar inget i skillmappen.
- **Tillagt:** avsnittet "Så används skillen i nortropic-webb-pro" överst, en ny beskrivning, och en anmärkning före
  Full Example om att exemplet hittar på personer och studier.
- **Krockar som avsnittet överst löser:** svenska citattecken (mönster 19), engelskspecifika mönster (17, 26),
  rösten ur verksamhetens ord i stället för en påhittad personlighet, inget påhittat.
- **Förgranskning:** `kontroller/granska_repo.py` gav LÅG på källan.
- **Tillägg 2026-10-02:** tre punkter i förordet (tak per sektion, strängare kort text, skriv om ur sakuppgiften)
  med egna ord ur coreyhaines31/marketingskills `skills/copywriting/references/ai-tells.md` @ 13c3832 (MIT, Corey
  Haines 2025): skillnaden mellan förbud och tak, reglerna för kort text och rewrite-regel 8 (variera rättningarna).
  Inget kopierat ordagrant (kunskap/REGISTER.md · 2026-10-02 · coreyhaines31/marketingskills).
