---
id: B-20261007-slutbeskedets-prov-tacker-int-hup-avslutsfasen-l
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r101-om.md
fynd: GR-20261007-r101-om#KAN-8
skapad: 2026-10-07
prio: normal
steg: main: kor.sh, kontroller/korslut.py, kontroller/rokprov/revision/prov_slutpost.py
commit: dcfde6a
andrad: 2026-10-08T22:15Z
---
# Slutbeskedets prov täcker INT, HUP, avslutsfasen, låset efter avbrott, raden Posten: och uppdraget

**Varför:** Mutanterna N08, N19, N20, N22, N44 och N47 överlever prov_slutpost.py. Beteendet stämmer i granskarens scenarier, men proven saknas.

**Förslag:** Ett fall per mutant, efter granskarens skript i underlag/granskningar/GR-20261007-r101-om/.

**Klart när:** De sex mutanterna fälls.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08/09: fallen fanns sedan dcfde6a; nattens körning mot den aktuella koden fäller mutanterna N08, N19, N20, N22, N44 och N47 (RAPPORT-2026-10-08-natt-codex-rester-backlog). Inte verifierad.
