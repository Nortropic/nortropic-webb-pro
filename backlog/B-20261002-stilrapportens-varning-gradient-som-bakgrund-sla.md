---
id: B-20261002-stilrapportens-varning-gradient-som-bakgrund-sla
status: klar
kalla: bygge
kallref: kunder/lulea-snickaren-abx/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 5
commit: 06dafb5
andrad: 2026-10-02T15:34Z
---
# Stilrapportens varning 'gradient som bakgrund' slår till på en hård övergång mellan två platta färger

**Varför:** I lulea-snickaren-abx används linear-gradient med två stopp på samma position för att låta det röda fältet sluta mitt i en bildserie. Det är ingen toning, men stilrapporten varnade 'gradient som bakgrund' i varje prov och varningen måste motiveras i rapporten.

**Förslag:** Stilkontrollen i kontroller/ (stilrapporten, prov/stil/STIL.md): räkna inte en gradient där varje färg börjar där den förra slutar (hårda stopp) som toning; varna bara när två intilliggande stopp har olika färg och olika position.

**Klar (2026-10-02):** bara toning varnas; hårda stopp ignoreras
