# nortropic-webb-pro — för sessioner i det här repot

Bygger webbplatser åt riktiga verksamheter enligt litteraturens åtta steg. Ägaren dömer resultatet. Det som gäller nu,
med räckvidd: `kunskap/designregler.md` (kvalitetskraven och ägarens beslut) och kundens aktuella domar i
`underlag/<slug>/DESIGNDOMAR.jsonl`. Historiken bevaras och slås upp när den besvarar en konkret fråga: varför och vad
som beslutats i `BESLUT.md`, ägarens domar över tidigare byggen i `LARDOMAR.md` (publik, utan personuppgifter) och
ordagrant i `underlag/LARDOMAR-original.md` (privat). Domarna över tidigare byggen är historik: inget bygge hittills har
varit bra nog (ägaren 2026-10-05), så de styr inga agenter och är aldrig förebilder. Det aktiva urvalet per körning står
i `underlag/<slug>/atelje/URVAL.json` (`kontroller/urval.py`): andra byggens bilder i granskningen och tidigare byggens
upptagna val är av tills de väljs uttryckligen (ren start 2026-10-08).

## Skills

- `bygg-sajt`: helbygget åt en verksamhet, steg 1–7, från en startsida som ägaren godkänt i skapandeflödet. Startas
  obevakat av `./kor.sh <slug> "<verksamhet>"`; vem som startar vad i hela kedjan, från kundunderlag till leverans:
  `README.md`. Två oberoende granskare (`kontroller/granska.py`, kriterierna i `kritik/GRANSKARE.md`) dömer sajten var
  för sig i egna sessioner; stoppvakten släpper inte bygget förrän den godkänner eller taket nås.
- `kirurg`: bedömer ett repo, en skill, en artikel eller en YouTube-video (`/kirurg <url>`). Lägger aktuella fynd i
  backloggen automatiskt.
- `backlog`: genomför den vilande backloggen när ägaren säger "implementera enligt backlog".
- Övriga mappar i `.claude/skills/` är designkompetensen. Vilka roller i skapandeflödet som har vilka skills (kärna och
  alternativ), vilka skills som saknar uppgift och varför, och beslutet för varje verktyg hos Refero och Mobbin står i
  `kunskap/metodkarta.md`, avsnittet Kompetenserna (ägarens ord 2026-10-05: alla skills och MCP:er ska användas). Var
  och en har `KALLA.md` med källa, commit och licens. `writing-for-agents` är för sessioner som ändrar en skill,
  `CLAUDE.md` eller `kunskap/`, inte för byggena.

## Var saker finns

`kunskap/` professionstexter (regeln mot slop: `copy-kontroll.md`, `redaktionellt-pass.md`,
`referenser-professionella.md`; ribban i tre nivåer ur ägarens kalibrering: `visuell-niva.md`; designflödet för startsidan, ett för alla ingångar: `skapandeflodet.md`; byggstandarden med verifierbara punkter: `byggstandard.md`; litteraturen och
metoderna bakom den: `teoretisk-grund.md`) · `kontroller/` provet och verktygen · `backlog/` vilande poster · `dashboard/`
ägarens vy (`./dashboard.sh start`, http://127.0.0.1:4771; arbetsytan är startvyn, meddelandebussen och pausen: `kunskap/arbetsyta.md`) · `underlag/` och `kunder/` privat material och byggen,
utanför git · `underlag/prospekt/` kampanjer och spärrlista (privat); reglerna för prospekt och utskick:
`kunskap/prospekt-och-utskick.md`; spanarens källor: `kunskap/spaning-kallor.md` · var varje slag av information hör
hemma, rapporthuvudet och arbetsregeln om dokumentation: `README.md`, Var information finns.

## Arbetssätt

- Små ändringar. En ägardom klassas först: kundbeslut, smakpreferens, metodhypotes eller generell rättelse; bara en
  generell rättelse blir en gemensam regel (`.claude/skills/backlog/SKILL.md`, steg 3), och då som en textändring, inte
  en ny mekanik.
- Python med `.venv/bin/python`, Node med `node`. Kommandon från repots rot.
- Efter ändringar i `kontroller/` eller `mall/`: `kontroller/rokprov.sh` ska sluta grönt.
- Dokumentationen och spårbarheten följer ändringen i samma uppdrag (arbetsregeln: `README.md`, Var information finns).
- Verktygslådan hålls i den senaste versionen som klarat proven av det dagliga underhållet, och varje start bekräftas av
  startkontrollen med ett startkvitto (`kunskap/beroenden.md`, Underhåll). Installera aldrig något för hand vid sidan av.
- Arbetskopior, förhandsvisningar, tempkataloger och npm-cachen städas enligt städregeln i `BESLUT.md` (tilläggen
  2026-10-06 och 2026-10-07) av det dagliga underhållet och, under 15 % ledigt, av startkontrollen före starten
  (`kontroller/stadning.py`; `--torr` listar bara). Det som verkar värdefullt väntar på ägaren i underhållets rapport.
  En arbetskopia ska heta `kopia*`; körd utanför huvudutcheckningen och dess worktrees städar den ingenting. En
  tempkatalog skapas med `korregister.egen_tmp`, och bara en sådan raderas, när körningen som den är registrerad på har
  slutat (ägarens tolkning med exempel: `BESLUT.md`, tillägget 2026-10-07 om städningens villkor). En sessions arbetsyta
  tas bort först när varje fil i den är registrerad eller nåbar i git. Ett omtag sparar det ägaren bedömt innan något
  raderas, utom omgångarnas bilder i den äldre utforskningen med riktningar (samma tillägg).
- Commit direkt på `main` och `git push origin main`. Repot är publikt: inga hemligheter, inget ur `underlag/` eller
  `kunder/`, inga personuppgifter ur ägarens domar (privatpersoners namn, nummer, adresser, hälsa; BESLUT.md 2026-10-03).
- De gamla repona (Nortropic Runtime, nortropic-projektkontor, nortropic-digitala, kund-demo-norrglanta) är borttagna
  lokalt sedan 2026-10-02 (ägarens beslut, `BESLUT.md`). Det som pushades finns på GitHub.
