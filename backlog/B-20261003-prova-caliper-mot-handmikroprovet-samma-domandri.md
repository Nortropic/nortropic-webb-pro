---
id: B-20261003-prova-caliper-mot-handmikroprovet-samma-domandri
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane GitHub Repos That 10x Your Codex And Claude Code Setup (YouTube Ua0APTMVcb8) + edonadei/caliper
skapad: 2026-10-03
prio: normal
steg: 8 Dom; backlog-skillen steg 4 (mikroprov av verktygslådans skills och domändringar)
andrad: 2026-10-05T06:55Z
---
# Prova Caliper mot handmikroprovet: samma domändring mäts en gång för hand och en gång med caliper run --ablate, med aktivering, kontroll och tokens bredvid domen

**Varför:** Prova: Caliper gör det backlog-skillens mikroprov gör för hand (k försök per uppgift, domare på annan modell) och mäter två saker vi saknar: om bygget alls aktiverar skillen ur dess beskrivning, och vad skillen tillför mot kontrollen utan den. Om det är smartare än handprovet syns först när ett mikroprov körs på båda sätten; Caliper är ett Python-paket som kör Claude Code ur kvoten och försöken är ingen säkerhetsgräns (docs/adr/0027).

**Förslag:** Vid nästa dompost som ändrar en skill i .claude/skills/ eller en text i bygg-sajt: skriv <skill>.eval.yaml bredvid skillen enligt edonadei/caliper @ 0f94c3f (docs/spec-reference.md): skills: [./SKILL.md], user_customizations: false, setup: som kopierar de kunskapsfiler uppgiften behöver, tre uppgifter med expect: och activates:, en tystnadsprob activates: []. Installera caliper-eval i en egen venv (pipx eller .venv-kirurg), kör caliper validate, caliper run --k 1, caliper run --k 3 --ablate <skill>, caliper run --k 3, caliper compare, med --judge-model på en annan modell än byggarens. Kör samma uppgift för hand enligt backlog-skillen steg 4. Jämför domen, aktiveringen, tokens och tid; skriv utfallet på Ändring-raden i LARDOMAR.md och i registrets Utfall. Faller Caliper väl ut: backlog-skillen steg 4 blir ett stycke som pekar på specfilen och kommandona, och skills/evaluate-skill kopieras till .claude/skills/evaluate-skill/ utan allowed-tools, med KALLA.md (MIT) och en description som säger att den används av sessioner som ändrar skills, aldrig av bygget.

**Klart när:** En dompost har körts på båda sätten och utfallet (dom, aktivering, tokens, tid) står på dess Ändring-rad; beslutet om backlog-skillen steg 4 och evaluate-skill är taget och registrets Utfall ifyllt

**Vilande (2026-10-05):** Avstämt 2026-10-05: inget påbörjat. Aktiveringen mäts ur loggen (posten om Skill-anrop, baslinjen); Caliper prövas när en dompost finns igen.
