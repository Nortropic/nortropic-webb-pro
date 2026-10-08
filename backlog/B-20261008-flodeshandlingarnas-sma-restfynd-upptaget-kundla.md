---
id: B-20261008-flodeshandlingarnas-sma-restfynd-upptaget-kundla
status: vilande
kalla: granskning
kallref: granskningar/GR-20261008-r117-claude.md
fynd: GR-20261008-r117-claude#B5
skapad: 2026-10-08
prio: normal
steg: main: kontroller/flodesstart.py, kontroller/atelje.py, dashboard/index.html
---
# Flödeshandlingarnas små restfynd: upptaget kundlås utan journalpost, nyckeln i fliken, exportens frist, borttagen låsfil

**Varför:** GR-20261008-r117-claude B5, B7, B9 och B10: atelje.main ger 5 när kundlåset är upptaget utan att något bokförs (servern svarar 202 registrerad); fliken tar bort start-id-nyckeln före omläsningen; exportens hela träd får 2 s TERM→KILL medan kor.sh får NWP_FRIST; en raderad .atelje-start.las låser en ny inod fritt. Inget av dem ger dubbla starter; alla är PLAUSIBLE eller låga.

**Förslag:** B5: egen slutkod eller kräv journalpost före 202. B7: ta bort nyckeln efter lyckad omläsning. B9: NWP_FRIST för exportera-processen, 2 s bara för ättlingarna. B10: notering i skapandeflodet.md; ingen kod raderar filen i dag.

**Klart när:** Varje punkt har ett prov eller en notering i kunskapstexten.
