---
id: B-20261003-ab-py-bokfor-harnessversion-och-modell-ur-loggen
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · anthropics/claude-code, release v2.1.280
skapad: 2026-10-03
prio: normal
steg: A/B-mätningen (kontroller/ab.py)
commit: b7bf1c5
andrad: 2026-10-05T10:59Z
---
# ab.py bokför harnessversion och modell ur loggens init-rad för varje arm

**Varför:** Domen för release v2.1.280 blev nej: vi kör redan den versionen. Men noten visar att effort-hanteringen i -p har ändrats mellan versioner, och ab.py läser bara result-raden, så två armar körda på olika Claude Code-versioner jämförs i dag som lika.

**Förslag:** kontroller/ab.py matt() rad 58–79: hämta första raden med type system och subtype init ur loggen och lägg claude_code_version och model i resultatet; visa dem bredvid turer och minuter i dashboardens vy Jämförelser; LARDOMAR-stycket AB får raden med.

**Klart när:** ab.py:s resultat för en körning innehåller version och model, och dashboardens jämförelsevy visar dem per arm; rokprov.sh grönt.

**Vilande (2026-10-05):** Avstämt 2026-10-05: ogjord; ab.py läser bara result-raden, och init-raden bär claude_code_version och model (formen belagd i en arkiverad logg). Ingår i paketet före nästa helbygge, med en fixturlogg i rökprovet.

**Klar (2026-10-05):** Klar: ab.py:s mått bär modell och Claude Code-version ur loggens init-rad och skills ur Skill-anropen; Jämförelser visar dem per arm; prov med fixturlogg. Nästa körda jämförelse visar dem skarpt. (b7bf1c5)
