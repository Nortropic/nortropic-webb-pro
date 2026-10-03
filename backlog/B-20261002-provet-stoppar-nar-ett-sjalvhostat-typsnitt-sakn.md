---
id: B-20261002-provet-stoppar-nar-ett-sjalvhostat-typsnitt-sakn
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · withastro/astro
skapad: 2026-10-02
prio: normal
steg: 6 (provet): kontroller/standard_kontroll.py punkt 4.3
andrad: 2026-10-03T00:12Z
---
# Provet stoppar när ett självhostat typsnitt saknar reservtypsnitt med size-adjust (byggstandarden 4.3)

**Varför:** Egen innovation ur Astro-intaget: byggstandarden 4.3 kräver font-display swap med size-adjust-reserv, men provet hoppar bara över local()-block (standard_kontroll.py rad 378–379) och kräver aldrig att de finns. Tre av de fem byggena (lulea-snickaren, sundboms-el, paint-it-black-maleri) saknar reserven helt och gick ändå grönt; de två i A/B-paret har handgissade mått.

**Förslag:** kontroller/standard_kontroll.py efter rad 386: för varje @font-face med url() i all_css kräv ett @font-face-block i samma CSS med local() och size-adjust eller ascent-override (Astros fonts-API ger block med namnet '<familj> fallback: <systemtypsnitt>' som också matchar); annars F('4.3', '(alla)', 'typsnittet <familj> saknar reservtypsnitt med size-adjust; se mallen'). Ett provfall i rökprovet för varje utfall.

**Klart när:** kontroller/rokprov.sh grönt; ett bygge utan reserv faller på 4.3 och ett med handskriven reserv eller Astros fonts-API går igenom.
