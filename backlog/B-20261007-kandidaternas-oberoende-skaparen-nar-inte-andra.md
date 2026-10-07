---
id: B-20261007-kandidaternas-oberoende-skaparen-nar-inte-andra
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r103.md
fynd: GR-20261007-r103#B1
skapad: 2026-10-07
prio: hog
steg: main: kontroller/kandidater.py (verktyg, andra_nekas), kontroller/rokprov/revision/prov_skisskritik.py
andrad: 2026-10-07T12:49Z
---
# Kandidaternas oberoende: skaparen når inte andra kandidaters kod via skalet

**Varför:** Skaparens sessioner kan läsa andra kandidaters kod med läsande skalkommandon i en pipe (granskaren bekräftade med echo|grep och echo|head med skaparens behörigheter). andra_nekas nekar bara Read. Förslagen ska vara verkligt olika, och en skapare som läser en annans kod kan göra dem lika. Luckan fanns före skisskritikens gren.

**Förslag:** Neka de läsande skalkommandona (LASANDE_SKAL) i skaparens sessioner mot andra kandidaters kataloger, utan att röra skaparens egna verktyg (förhandsvisning, typsnitt, Write, Edit och Read i det egna projektet).

**Klart när:** Ett prov med skaparens behörigheter når inte en annan kandidats kod på något av granskarens sätt, och skaparens eget arbete går som förut. Görs före nästa skarpa kandidatkörning.

**Klar (2026-10-07):** andra_nekas nekar de läsande skalkommandona (LASANDE_SKAL, skal_nekas) i varje session som arbetar med en kandidat; prövat i prov_skisskritik fall 9 och i en verklig session utan kunddata (gren kandidatskydd-20261007). Inte verifierad.
