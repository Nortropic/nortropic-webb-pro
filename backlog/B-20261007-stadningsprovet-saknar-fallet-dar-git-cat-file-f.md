---
id: B-20261007-stadningsprovet-saknar-fallet-dar-git-cat-file-f
status: klar
kalla: granskning
kallref: granskningar/GR-20261006-r98.md
fynd: GR-20261006-r98#KAN-A
skapad: 2026-10-07
prio: normal
steg: kontroller/rokprov/revision/prov_stadning.py
commit: 425af7a
andrad: 2026-10-08T21:28Z
---
# Städningsprovet saknar fallet där git cat-file faller för en sammanslagen worktree med commit på frikopplad HEAD

**Varför:** Mutationen K1d (return [] i felgrenen i onada_commits) ger 49 gröna fall; koden gör rätt, provet håller det inte.

**Förslag:** Ett fall i KAN-1-injektionen där cat-file faller för en sådan worktree.

**Klart när:** K1d blir röd.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08: worktreen catfel och en injektion som fäller git cat-file bara för dess HEAD-reflogg; mutanten K1d är röd. Inte verifierad.
