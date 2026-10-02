# Granskarförsök

A/B av granskaren mot ägarens egna fel i dömda byggen. Körs utanför flödet, när en ändring i
`kritik/GRANSKARE.md` eller `kontroller/granska.py` ska prövas innan den införs.

1. `forbered.py`: en isolerad repokopia per dömt bygge under `$NWP_FORSOK` (standard `/tmp/nwp-granskarforsok`), blind
   för byggets egen dom (LARDOMAR.md utan byggets block, ingen DOM.json, ingen backlog eller register), och ett färskt
   snabbprov med dagens kontroller. Armarnas texter ligger bredvid (`GRANSKARE-<arm>.md`).
2. `kor.py [parallellt]`: granskningarna per arm och bygge (`ARMAR` i skriptet), med läsning nekad i repona och minnet.
3. `doma.py [parallellt]`: en annan modell (Sonnet) matchar varje fynd mot `facit.json` och märker resten verkligt eller
   falskt, två gånger per granskning i ombytt ordning; bara eniga matchningar räknas.
4. `sammanstall.py`: tabellen per arm (träffar på omdömesfel och alla fel, falska blockerande, överensstämmelse,
   tokens, tid) och per facitfel.

`facit.json` är ägarens fel ur LARDOMAR.md L1–L3; `maskin` markerar de fel som standarden redan fångar. Resultatet
2026-10-02 står i backlogposten B-20261002-a-b-tva-isolerade-granskare-per-omgang-blockeran.
