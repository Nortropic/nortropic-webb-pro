---
id: B-20261007-dokumentationsvyn-agarens-del-i-ett-sammansatt-u
status: klar
kalla: granskning
kallref: granskningar/GR-20261007-r99-om.md
fynd: GR-20261007-r99-om#BÖR-1
skapad: 2026-10-07
prio: normal
steg: main: dashboard/server.py (utfallet), dashboard/index.html, kontroller/rokprov/revision/prov_dokumentationsvy.py
commit: 7dfb8e3
andrad: 2026-10-08T22:15Z
---
# Dokumentationsvyn: ägarens del i ett sammansatt utfall visas som ägarens bara när ett fält belägger avsändaren

**Varför:** utfallet() ger avsändaren "ägaren" för varje del som börjar med "ägarens dom", "ägarens beslut" eller "ägarens bedömning", utan belägg. "ägarens dom: godkänt" i en rapport blir ett grönt chip med raden "Ägarens dom (avsändare: ägaren)", fast det är rapportens författare som skrivit det. Det är fallet bakom punkt 7 i uppdraget 2026-10-07. I dag är den enda sådana domen belagd (C5, bekräftad 05:12Z), så inget visas fel nu.

**Förslag:** Märk raden "ägarens dom enligt rapporten" och visa avsändaren som ej belagd. Som belagd visas den bara när ett fält belägger den, som avsandare i VERSION.json, på samma sätt som _pilotdomar.

**Klart när:** Ett prov där en rapport skriver "ägarens dom: godkänt" utan belägg visar avsändaren ej belagd och inget ägarchip, och C5-domen visas fortfarande som ägarens med sitt belägg.

**Klar (2026-10-08):** Nattens uppdrag 2026-10-08/09: ägarens dom bara med belägg i VERSION.json, annars enligt rapporten med avsändaren ej belagd; C5 belagd i moment-c/VERSION.json; prov_dokumentationsvy rött mot 03fab0e, grönt efter (RAPPORT-2026-10-08-natt-codex-rester-backlog). Inte verifierad.
