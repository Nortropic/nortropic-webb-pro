---
id: B-20261002-gruppera-py-laser-granskarens-blockerande-fynd-p
status: pagar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · AI LABS, He Finally 10x Claude Code With This Method (YouTube qLfSDQ5NGh0)
skapad: 2026-10-02
prio: normal
steg: 8 och arbetssättet runt: kontroller/gruppera.py
andrad: 2026-10-03T00:01Z
---
# gruppera.py läser granskarens blockerande fynd per sparad omgång, inte bara slutfilen, så att fel som rättas i varje bygge men återkommer i nästa syns som en kategori

**Varför:** Dom: ta in. Videons andra slinga läser resultatet av varje omgång och hittar vanor som en färsk agent upprepar i varje funktion; vår gruppering läser bara kunder/<slug>/granskning/GRANSKNING.json (gruppera.py rad 43), alltså fynd som stod kvar vid godkännandet, och missar just de fel som varje bygge gör och rättar om igen (lulea-snickaren-abx omgång 1: egenritat märke i stället för loggan).

**Förslag:** kontroller/gruppera.py, granskningsfynd() rad 40–47: läs också varje kunder/<slug>/granskning/runda-NN/GRANSKNING.json och skriv varje blockerande fynd med omgångens nummer och om det var rättat i slutfilen; uppdragstexten rad 52–55 får en mening om att ett fel som rättas inom bygget men återkommer i nästa bygge räknas som en kategori, inte som löst; docstringen rad 2–4 nämner omgångarna.

**Klart när:** kontroller/rokprov.sh grönt, och .venv/bin/python kontroller/gruppera.py --torr visar fynd med omgångsnummer för de befintliga byggena, bland dem lulea-snickaren-abx omgång 1.
