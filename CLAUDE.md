# nortropic-webb-pro — för sessioner i det här repot

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg. Ägaren dömer resultatet. Varför och vad
som beslutats: `BESLUT.md`. Ägarens domar: `LARDOMAR.md`; de gäller före allt annat.

## Skills

- `bygg-sajt`: ett bygge åt en verksamhet, steg 1–7. Startas obevakat av `./kor.sh <slug> "<verksamhet>"`.
- `kirurg`: bedömer ett repo, en skill, en artikel eller en YouTube-video (`/kirurg <url>`). Lägger aktuella fynd i
  backloggen automatiskt.
- `backlog`: genomför den vilande backloggen när ägaren säger "implementera enligt backlog".

## Var saker finns

`kunskap/` professionstexter (regeln mot slop: `copy-kontroll.md`, `redaktionellt-pass.md`,
`referenser-professionella.md`) · `kontroller/` provet och verktygen · `backlog/` vilande poster · `dashboard/`
ägarens vy (`./dashboard.sh`, http://127.0.0.1:4771) · `underlag/` och `kunder/` privat material och byggen,
utanför git.

## Arbetssätt

- Små ändringar. En dom blir en textändring, inte en ny mekanik.
- Python med `.venv/bin/python`, Node med `node`. Kommandon från repots rot.
- Efter ändringar i `kontroller/` eller `mall/`: `kontroller/rokprov.sh` ska sluta grönt.
- Commit direkt på `main` och `git push origin main`. Repot är publikt: inga hemligheter, inget ur `underlag/` eller
  `kunder/`.
- De gamla repona (Nortropic Runtime, nortropic-projektkontor, nortropic-digitala) är frysta och rörs inte.
