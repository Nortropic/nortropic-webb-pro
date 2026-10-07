---
id: B-20261007-stadningen-raknade-commitar-som-ersatts-av-amend
status: klar
kalla: granskning
kallref: granskningar/GR-20261006-r94-slut.md
fynd: GR-20261006-r94-slut#BÖR-1
skapad: 2026-10-07
prio: normal
steg: kontroller/stadning.py (onada_commits)
commit: 0a4d7b6
verifierad: GR-20261006-r98
verifierad_tid: 2026-10-07T02:03Z
andrad: 2026-10-07T02:03Z
---
# Städningen räknade commitar som ersatts av amend eller rebase som onåbara

**Varför:** Verifieringen av r94 (17e4b51): en worktree som amendats eller rebasats, slagits samman och pushats väntade alltid på ägaren med skälet att commitarna "försvinner med den", fast de står kvar i grenens reflogg.

**Förslag:** Räkna grenarnas, stashens och huvudutcheckningens refloggar som kvar, men inte worktreens egen HEAD-reflogg.

**Klart när:** En amendad och en rebasad worktree tas bort och de ersatta commitarna nås efteråt; en commit på frikopplad HEAD väntar fortfarande på ägaren.

**Klar (2026-10-07):** Rättat i stadning-foljd-20261007 (git log --single-worktree --reflog), sammanslagen i main lokalt.

**Verifierad (2026-10-07):** GR-20261006-r98: Verifieringen GR-20261006-r98: fall A, B och R tas bort och de ersatta commitarna nås; fall D och G väntar; mutationerna Ba–Bg röda.
