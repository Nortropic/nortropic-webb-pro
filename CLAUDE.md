# nortropic-webb-pro — för sessioner i det här repot

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg. Ägaren dömer resultatet. Det som gäller nu,
med räckvidd: `kunskap/designregler.md` (kvalitetskraven och ägarens beslut) och kundens aktuella domar i
`underlag/<slug>/DESIGNDOMAR.jsonl`. Historiken bevaras och slås upp när den besvarar en konkret fråga: varför och vad
som beslutats i `BESLUT.md`, ägarens domar över tidigare byggen i `LARDOMAR.md` (publik, utan personuppgifter) och
ordagrant i `underlag/LARDOMAR-original.md` (privat). En äldre smakdom är ett exempel, ingen regel för en ny kund.

## Skills

- `bygg-sajt`: ett bygge åt en verksamhet, steg 1–7. Startas obevakat av `./kor.sh <slug> "<verksamhet>"`.
  Två oberoende granskare (`kontroller/granska.py`, kriterierna i `kritik/GRANSKARE.md`) dömer sajten var för sig i
  egna sessioner; stoppvakten släpper inte bygget förrän den godkänner eller taket nås.
- `kirurg`: bedömer ett repo, en skill, en artikel eller en YouTube-video (`/kirurg <url>`). Lägger aktuella fynd i
  backloggen automatiskt.
- `backlog`: genomför den vilande backloggen när ägaren säger "implementera enligt backlog".
- Övriga mappar i `.claude/skills/` är designkompetensen, fördelad på rollerna i skapandeflödet: varje roll har en kärna
  som läses hel och alternativ som väljs efter riktningen (`kunskap/metodkarta.md`, avsnittet Kompetenserna; ägarens ord
  2026-10-05: alla skills och MCP:er ska användas). Var och en har `KALLA.md` med källa, commit och licens.
  `writing-for-agents` är för sessioner som ändrar en skill, `CLAUDE.md` eller `kunskap/`, inte för byggena.

## Var saker finns

`kunskap/` professionstexter (regeln mot slop: `copy-kontroll.md`, `redaktionellt-pass.md`,
`referenser-professionella.md`; ribban i tre nivåer ur ägarens kalibrering: `visuell-niva.md`; designflödet för startsidan, ett för alla ingångar: `skapandeflodet.md`; byggstandarden med verifierbara punkter: `byggstandard.md`; litteraturen och
metoderna bakom den: `teoretisk-grund.md`) · `kontroller/` provet och verktygen · `backlog/` vilande poster · `dashboard/`
ägarens vy (`./dashboard.sh`, http://127.0.0.1:4771) · `underlag/` och `kunder/` privat material och byggen,
utanför git · `underlag/prospekt/` kampanjer och spärrlista (privat); reglerna för prospekt och utskick:
`kunskap/prospekt-och-utskick.md`; spanarens källor: `kunskap/spaning-kallor.md`.

## Arbetssätt

- Små ändringar. En ägardom klassas först: kundbeslut, smakpreferens, metodhypotes eller generell rättelse; bara en
  generell rättelse blir en gemensam regel (`.claude/skills/backlog/SKILL.md`, steg 3), och då som en textändring, inte
  en ny mekanik.
- Python med `.venv/bin/python`, Node med `node`. Kommandon från repots rot.
- Efter ändringar i `kontroller/` eller `mall/`: `kontroller/rokprov.sh` ska sluta grönt.
- Commit direkt på `main` och `git push origin main`. Repot är publikt: inga hemligheter, inget ur `underlag/` eller
  `kunder/`, inga personuppgifter ur ägarens domar (privatpersoners namn, nummer, adresser, hälsa; BESLUT.md 2026-10-03).
- De gamla repona (Nortropic Runtime, nortropic-projektkontor, nortropic-digitala, kund-demo-norrglanta) är borttagna
  lokalt sedan 2026-10-02 (ägarens beslut, `BESLUT.md`). Historiken finns på GitHub och som git-bundles i
  `~/Arkiv/nortropic-gamla-20261002/`.
