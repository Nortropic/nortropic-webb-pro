---
id: B-20261003-rakna-i-korning-jsonl-vilka-av-verktygsladans-sk
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · AI LABS, Insane GitHub Repos That 10x Your Codex And Claude Code Setup (YouTube Ua0APTMVcb8) + edonadei/caliper
skapad: 2026-10-03
prio: normal
steg: runt stegen: verktygslådan, ab.py:s mått och dashboardens handlingar
commit: b7bf1c5
andrad: 2026-10-05T10:59Z
---
# Räkna i korning-*.jsonl vilka av verktygslådans skills bygget faktiskt anropade och visa det i ab.py:s mått och dashboarden

**Varför:** Egen innovation ur Caliper-intaget: verktygslådans nio skills används 'när beskrivningen passar' men ingen mäter om bygget någonsin anropar dem. Loggen har redan svaret: varje Skill-anrop är ett tool_use med namnet Skill och fältet skill i input. Det är ett mått utan ny mekanik och ger underlag för vilka skills som ska mikroprovas.

**Förslag:** kontroller/ab.py matt(): räkna per bygge tool_use med name == 'Skill' ur korning-*.jsonl och lägg {'skills': {namn: antal}} i måtten (kontrollera formen i en riktig logg först). dashboard/server.py rad 219–222: ta med inp.get('skill') i mal så att handlingen visar vilken skill som anropades. Rapportera i rokprov om ab.py:s prov rör måtten.

**Klart när:** ab.py:s mått för ett avslutat bygge innehåller skills: {namn: antal} (tomt objekt när inget anropades) och dashboardens handlingar visar skillnamnet; rokprov.sh grönt

**Vilande (2026-10-05):** Avstämt 2026-10-05: formen är belagd (tool_use Skill, input.skill); ett arkiverat bygge anropade bara bygg-sajt och humanizer. Skapandeflödets metodkvitto räknar Skill-anrop och lästa metodfiler i sina sessioner (bildkedja.metodlasning). Kvar (paketet före nästa helbygge): samma räkning i byggets korning-*.jsonl, i ab.py:s mått och med skillnamnet i dashboardens handlingar; fixturlogg i rökprovet.

**Klar (2026-10-05):** Klar: ab.skillanrop räknar Skill-anropen i byggets korning-*.jsonl och står i A/B-måtten och i Jämförelser; dashboardens handlingar visar skillens namn; skapandeflödets metodkvitto gör samma sak för sina sessioner. Prov med fixturlogg. (b7bf1c5)
