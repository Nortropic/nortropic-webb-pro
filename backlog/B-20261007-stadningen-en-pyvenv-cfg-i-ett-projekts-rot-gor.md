---
id: B-20261007-stadningen-en-pyvenv-cfg-i-ett-projekts-rot-gor
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r100-om.md
fynd: GR-20261007-r100-om#KAN-B
skapad: 2026-10-07
prio: normal
steg: main: kontroller/stadning.py, kontroller/rokprov/revision/prov_stadning.py
commit: 9852f0a
andrad: 2026-10-08T21:28Z
---
# Städningen: en pyvenv.cfg i ett projekts rot gör inte projektets lib/ och bin/ oprövade

**Varför:** En pyvenv.cfg i ett projekts rot får städningen att behandla projektets egna lib/ och bin/ som en venv och hoppa över dem när den prövar om filerna är registrerade.

**Förslag:** Kräv en riktig venv: pyvenv.cfg tillsammans med bin/python, och bara när katalogen är en känd venv-plats.

**Klart när:** Ett prov med en falsk pyvenv.cfg prövar projektets filer; mutationen N-BÖR1a fälls.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08: riktig_venv och venv_harlett; provet med en falsk venv, ett projekt utan pyvenv.cfg och en venv i projektets rot (C11) är rött mot basen och grönt efter; N-BÖR1a på den nya koden och fyra mutanter till fälls (RAPPORT-2026-10-08-natt-codex-rester-backlog). Inte verifierad.
