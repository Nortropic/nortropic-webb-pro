---
id: B-20261001-skillens-kopieringskommando-for-mallen-nekas-i-d
status: vilande
kalla: bygge
kallref: kunder/lulea-snickaren/RAPPORT.md
skapad: 2026-10-01
prio: normal
steg: 5
---
# Skillens kopieringskommando för mallen nekas i don't-ask-läget

**Varför:** Luleå-Snickaren: 'cp -R mall/astro/. kunder/<slug>/sajt/' (och mkdir && cp) nekades; mallens sex filer fick skrivas för hand. Heredocs och sammansatta skalkommandon nekades också, enkla kommandon och .venv/bin/python med skriptfil gick.

**Förslag:** .claude/skills/bygg-sajt/SKILL.md steg 5.2: kopiera med .venv/bin/python -c "import shutil; shutil.copytree('mall/astro', 'kunder/<slug>/sajt', dirs_exist_ok=True)" och skriv att hjälpskript läggs som filer i underlag/<slug>/verktyg/ i stället för heredocs.
