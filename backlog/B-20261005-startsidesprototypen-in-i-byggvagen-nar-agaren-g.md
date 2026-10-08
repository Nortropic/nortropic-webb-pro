---
id: B-20261005-startsidesprototypen-in-i-byggvagen-nar-agaren-g
status: klar
kalla: bevakning
kallref: Codex via ägaren 2026-10-05: designprovet underkänt, börja om med en startsidesprototyp
skapad: 2026-10-05
prio: hog
steg: bygg-sajt steg 5; kontroller/prototyp.py
commit: b7bf1c5
andrad: 2026-10-08T14:09Z
---
# Startsidesprototypen in i byggvägen när ägaren godkänt en: prototypen före resten av sajten, skaparen ser sitt arbete i varje steg

**Varför:** Designprovet förkastades i två omgångar och Codex underkände alla förslag; orsaken var att skaparen aldrig såg sina sidor. Prototypen (kontroller/prototyp.py) låter skaparen rendera, läsa och rätta i varv, och ägaren dömer en startsida innan något helt bygge startas.

**Förslag:** När ägaren godkänt en prototyp: bygg-sajt steg 5 börjar med prototypen (eller tar ägarens godkända prototyp som startsida och DESIGN.md ur den), undersidorna byggs med samma förhandsvisning varv för varv, och granskaren jämför startsidan med prototypen. Underkänner ägaren prototypen: en ny prototypkörning med ägarens ord som kritik, aldrig ett helt bygge på en underkänd grund.

**Klart när:** Ägaren har godkänt en startsida i vyn Prototyp, och ett bygge (kor.sh) har tagit vid från den med kod, DESIGN.md, bilder och godkännande; granskaren jämför startsidan med vinnaren.

**Vilande (2026-10-05):** Avstämt 2026-10-05: överlämningen byggs i skapandeflödet: ägarens dom i vyn Prototyp går till domloggen, godkänt till VINNARE.json (godkand), kor.sh tar vid utan ny ateljé, och DESIGN.md och bilderna följer vinnaren. Utan sandlåda kör ett bygge utan godkänd startsida skapandeflödet själv (panelen väljer); med sandlåda vägras det. Kvar: verifiering. Färdigkriteriet omskrivet i avstämningen; tidigare: "Ägaren har godkänt en prototyp i dashboardens vy Prototyp, och skillen säger hur ett bygge tar vid därifrån; ett bygge som startar utan godkänd prototyp vägras eller frågar."

**Vilande (2026-10-05):** Överlämningen är byggd och granskad i fyra omgångar: ägarens godkännande prövas innan domen skrivs (atelje.doma, också för domar via Codex), gäller bara med oförändrade hashar (skapande.godkand_giltig), och kor.sh bygger aldrig på en startsida som domloggen inte tillåter (prototyp.bygget_nekas). Kvar: ägarens godkännande av en körning och ett bygge som tar vid. (b7bf1c5)

**Klar (2026-10-08):** Backlogavstämningen 2026-10-08 (RAPPORT-2026-10-08-backlogavstamning): rättat i main; belägg: commit b7bf1c5 (godkännandets livscykel) och 31a1cc0 (kandidatflödet); kor.sh tar vid från atelje/vinnare (README, kedjan steg 5–6; flodesstart.krav)
