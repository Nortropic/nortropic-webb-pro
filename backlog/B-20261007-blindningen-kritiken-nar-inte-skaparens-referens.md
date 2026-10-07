---
id: B-20261007-blindningen-kritiken-nar-inte-skaparens-referens
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r103.md
fynd: GR-20261007-r103#B2
skapad: 2026-10-07
prio: hog
steg: main: kontroller/kandidater.py (blind_nekas), kontroller/rokprov/revision/prov_skisskritik.py
andrad: 2026-10-07T12:49Z
---
# Blindningen: kritiken når inte skaparens referensskäl i kundens underlag

**Varför:** blind_nekas nekar referenspaketet, REFERENSER.md och atelje/FORSKNING.md, men REFERENSUPPDRAG-*.json, TJANSTEUPPDRAG-*.json (skaparens referensskäl) och RESEARCH.md i underlag/<slug> går att läsa. Inget läckte i granskarens verkliga session, men luckan finns.

**Förslag:** Neka filerna i blind_nekas, eller vänd regeln så att kritiken bara får läsa en uttrycklig lista i underlag/<slug>.

**Klart när:** Ett prov med kritikens behörigheter når inte filerna, och kritikens eget arbete går som förut.

**Klar (2026-10-07):** blind_nekas är en uttrycklig lista (BLIND_LASBART) med mönster för det som uppstår under sessionen (BLIND_MONSTER), kunder/<slug> nekas, och historiken och domloggen nekas som filer (BLIND_HISTORIK, K4, Claudes beslut i väntan på ägaren); prövat i prov_skisskritik fall 10 och i en verklig session (gren kandidatskydd-20261007). Inte verifierad.
