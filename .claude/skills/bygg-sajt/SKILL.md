---
name: bygg-sajt
description: Bygg en webbplats åt en riktig verksamhet enligt litteraturens åtta steg (upptäckt, definition, innehåll före form, design, bygge, prov, rapport, dom) med Nortropics kunskap och kontroller. Använd när kor.sh startar en körning, eller när ägaren ber om ett bygge, en ombyggnad eller en ny omgång åt en verksamhet i det här repot.
---

# Bygg en sajt åt en verksamhet

**Målet** är en sajt som ägaren vill sätta sitt namn på och visa för verksamheten. Två ribbor avgör:
1. Den är tydligt bättre än verksamhetens nuvarande sajt (eller än att inte ha någon).
2. Den står sig mot referenserna i `referenser/REFERENSER.md`.

**Slop uppstår när modellen saknar något specifikt att säga.** Allt i den här skillen finns för att få fram det
specifika ur en riktig verksamhet och låta det bära sajten. Ägarens domar i `LARDOMAR.md` och reglerna i
`regler/antislop.md` gäller före allt annat här.

## Ramar för körningen

- **Ingen människa svarar under körningen.** Saknas en uppgift: märk den `antagande` och fortsätt. Hitta aldrig på
  fakta, omdömen, siffror, priser eller certifieringar.
- **Sökvägar** (`<slug>` står i uppdraget):
  - `underlag/<slug>/` råmaterial och arbetsfiler (privat, utanför git)
  - `kunder/<slug>/sajt/` Astro-projektet
  - `kunder/<slug>/RAPPORT.md` rapporten
  - `kunder/<slug>/prov/` provets utdata; skrivs bara av `kontroller/prova.py`, aldrig av dig
- **Verktyg:** Python körs med `.venv/bin/python`, Node-kontroller med `node kontroller/...`. Kommandon körs från
  repots rot.
- **Rör inte** `kontroller/`, `regler/`, `kunskap/`, `referenser/`, `mall/`, `.claude/` eller `LARDOMAR.md` under en
  körning. Verkar en kontroll fel: skriv det i rapporten under "Kontroller som verkar fel".
- **Inget skickas ut.** Inga formulär skickas, inga mejl, inga kontakter med verksamheten eller någon annan.
- **Personuppgifter:** bara det som behövs för sajten och som verksamheten själv visar publikt.

## Uppstart

Läs, i den här ordningen: `LARDOMAR.md` (varje dom), `regler/antislop.md`, `referenser/REFERENSER.md`. Är
referenslistan tom: skriv i rapporten att ribba 2 saknas och använd `kunskap/referenser-professionella.md` som
ersättning. Lägg upp de åtta stegen som uppgifter med TaskCreate och bocka av dem med TaskUpdate.

## Steg 1 — Underlag (upptäckt)

Läs `kunskap/kundintervju.md` (frågorna är din checklista) och `kunskap/research-underlag.md`.

1. **Hämta det publika:** deras webbplats (alla sidor som spelar roll), Google-profil och omdömen, sociala kanaler,
   företagsregister för grunduppgifter, två eller tre konkurrenter i samma ort. WebFetch och WebSearch.
2. **Bilder:** ladda ner verksamhetens egna bilder (från deras sajt och kanaler) med
   `curl -sSL -o underlag/<slug>/bilder/<namn> <url>`. För en lista i `underlag/<slug>/bilder/BILDER.md`: fil, källa,
   vad bilden visar, kvalitet. Inga stockbilder.
3. **`underlag/<slug>/VERKSAMHET.json`:** formen står i `validera()` i `kontroller/verksamhetsuppgifter.py`
   (`schema: 1`, `namn`, `fiktiv: false`, `kontaktvagar` med `typ`/`varde`/`belagg`, `rackvidd`, `tjanster` och de
   valfria fälten). Sätt `webb: {"doman": "deras-doman.se"}`. Kör `.venv/bin/python
   kontroller/verksamhetsuppgifter.py kontrollera underlag/<slug>/VERKSAMHET.json` tills den svarar exit 0.
4. **`underlag/<slug>/RESEARCH.md`:** svar på kundintervjuns frågor ur underlaget. Varje påstående har källa (URL)
   eller är märkt `antagande`. Kundernas omdömen ordagrant med källa. Konkurrenterna: vad de gör och vad som skiljer.
5. **Det specifika:** avsluta RESEARCH.md med en lista "Bara de har": minst tio konkreta saker som ingen konkurrent
   kan säga om sig själv (namn, år, plats, metod, material, citat, siffra, bild). Det är råvaran för allt som följer.
   Hittar du färre än fem: skriv det rakt, det är ett fynd.

## Steg 2 — Diagnos av nuvarande sajt

Har de en sajt:

```sh
node kontroller/axe.mjs --url=https://DERAS-DOMAN --sidor=/,/SIDA/ --ut=underlag/<slug>/diagnos/axe
node kontroller/lighthouse.mjs --url=https://DERAS-DOMAN --sidor=/,/SIDA/ --ut=underlag/<slug>/diagnos/lighthouse
node kontroller/webblasare/inspektera.mjs --adress https://DERAS-DOMAN/ --ut underlag/<slug>/diagnos/inspektion --vyer 390,1440
```

Inspektionen spärrar andra ursprung. Ser deras sajt trasig ut i skärmbilderna: läs blockerade adresser i
`INSPEKTION.json` och kör om med `--tillat 'https://cdn.exempel.se;https://fonts.exempel.com'`.

Skriv `underlag/<slug>/DIAGNOS.md`: siffrorna per sida, vad första vyn på mobil säger och inte säger, vad som hindrar
toppuppgifterna, och vad som fungerar och ska behållas (ord, bilder, struktur). Titta på skärmbilderna med Read.

Har de ingen sajt: skriv det, och att ribba 1 då är deras Google-profil och sociala kanaler.

## Steg 3 — Brief (definition)

Läs `kunskap/brief-mall.md`, `kunskap/beredning.md` och `kunskap/juridikflaggor.md`. Skriv `underlag/<slug>/BRIEF.md`:

- verksamhetsmål och vad sajten ska ändra
- målgrupper, med belägg ur omdömen och underlag
- tre till fem toppuppgifter i besökarens ord, rangordnade (ur omdömena och frågorna kunderna ställer)
- en primär handling och hur den fungerar utan JavaScript (telefon, mejl eller deras befintliga bokningssystem)
- framgångsmått
- sajtkarta: så få sidor som toppuppgifterna kräver, oftast tre till sju
- vilka saker ur "Bara de har" som bär vilken sida
- ton: fem formuleringar ur deras egna ord eller kundernas
- juridikflaggor (cookies, personuppgifter, bilder)
- antaganden som behöver bekräftas av verksamheten

Skriv också `underlag/<slug>/FRASER.txt`: en rad per fras som konkurrenterna i branschen använder och som vi därför
inte ska använda. Briefen är en hypotes; den prövas när ägaren och verksamheten ser resultatet.

## Steg 4 — Innehåll före form

Läs `kunskap/copy-kontroll.md`, `kunskap/redaktionellt-pass.md`, `kunskap/seo.md` och, om verksamheten är lokal,
`kunskap/seo-lokal.md`.

Skriv all text i `underlag/<slug>/INNEHALL.md` innan något ritas: per sida title (högst 60 tecken), description
(högst 155), h1, sektioner, knappar. Under varje sektion: raden `Specifikt:` med den sak ur "Bara de har" som
sektionen bär (antislop regel 1). Saknas den, stryk sektionen.

Kontrollera texten och rätta tills den har noll fynd:

```sh
.venv/bin/python kontroller/copy_kontroll.py --kalla underlag/<slug>/INNEHALL.md --fraser underlag/<slug>/FRASER.txt --ut underlag/<slug>/copy-innehall.json --md underlag/<slug>/copy-innehall.md
```

Läs fraslistan i `regler/antislop.md` och ta bort varje träff. Läs sedan texten högt för dig själv som en kund i
orten: kunde någon mening stå hos en konkurrent? Skriv om den.

## Steg 5 — Koncept och bygge (design)

Läs `kunskap/externa/anthropic-frontend-design-SKILL.md`, `kunskap/externa/leonxlnx-taste-SKILL-ce26fc25.md`
(principerna i §0 och §4, inte dess stack eller skelett), `kunskap/bygge-referens.md`, `kunskap/bild.md`,
`kunskap/externa/emil-mobile-native-SKILL.md`, och `kunskap/formularsakerhet.md` om sajten får formulär.

1. **Riktning.** Skriv `underlag/<slug>/KONCEPT.md`: två visuella riktningar härledda ur verksamheten själv (deras
   bilder, material, plats, ton) och referenserna, aldrig ur en branschmall. Per riktning typografi, färg, rytm och
   vad som dominerar första vyn. Välj en med skäl.
2. **Projekt.** `cp -R mall/astro/. kunder/<slug>/sajt/`, sätt `site` i `astro.config.mjs` till deras domän,
   `cd kunder/<slug>/sajt && npm install`. Läs `mall/astro/README.md`.
3. **Bygg** sidorna ur INNEHALL.md: mobil först, semantisk HTML, en h1 per sida, självhostade typsnitt eller
   systemtypsnitt, verksamhetens bilder via `astro:assets`, ingen JavaScript som inte behövs, JSON-LD
   (LocalBusiness eller rätt undertyp) sanningsenligt ur VERKSAMHET.json. Formulär skickar ingenting i demon; den
   primära handlingen går via telefon, mejl eller deras befintliga bokning.
4. **Snabbprov ofta:** `.venv/bin/python kontroller/prova.py <slug> --snabb`. Läs `kunder/<slug>/prov/PROV.md`.
5. **Titta.** Läs skärmbilderna `kunder/<slug>/prov/inspektion/*/vy-390-forsta.png`, `vy-1440-forsta.png` och
   `-hela.png` med Read. Ställ dem bredvid referenserna och antislop-reglerna. Rätta det som ser generiskt ut: där allt
   är lika stort, där en sektion inte bär något specifikt, där första vyn inte säger vad de gör och vad man gör härnäst.

## Steg 6 — Prov

Läs `kunskap/prelaunch.md` och `kunskap/webblasare.md`.

1. **Hela provet:** `.venv/bin/python kontroller/prova.py <slug>`. Rätta tills alla grindar är gröna. Grindarna och
   kraven står överst i `kontroller/prova.py`.
2. **Utforskning:** läs `kunder/<slug>/prov/utforska/UTFORSKNING.md` och rätta verkliga fynd.
3. **Renderingsläsning:** läs `kritik/FRAGA-renderingslasning.md` och gör läsningen själv mot skärmbilderna. Skriv
   svaret i `underlag/<slug>/RENDERINGSLASNING.md`. Rätta det du hittar.
4. **Femsekunderstest, avskärmat:** starta en subagent med Task-verktyget. Ge den bara texten i
   `kritik/FRAGA-femsekunderstest.md` och sökvägarna till första-vyn-bilderna för startsidan i 390 och 1440. Ingen
   brief, inget underlag, ingen kod. Spara svaret i `underlag/<slug>/FEMSEK.md`. Kan läsaren inte säga vad
   verksamheten gör och vad besökaren ska göra härnäst: rätta och testa igen.
5. Kör hela provet igen efter sista ändringen.

## Steg 7 — Rapport

Skriv `kunder/<slug>/RAPPORT.md` för ägaren, kort och ärligt, utan säljton:

1. **Verksamheten** i två meningar, med källa.
2. **Vad som byggdes:** sidorna, den primära handlingen, riktningen i en mening, tre beslut som syns.
3. **Det specifika:** vilka saker ur "Bara de har" som bär vilken sida.
4. **Före och efter**, en tabell: deras sajt (DIAGNOS.md) mot vår (`prov/STATUS.json`): axe allvarliga, Lighthouse
   P/A/BP/SEO mobil, SEO-fynd.
5. **Antaganden** och vad verksamheten skulle behöva bekräfta.
6. **Svagheter du själv ser** och det som inte gick.
7. **Kontroller som verkar fel**, om några.
8. **Femsekunderstestets svar**, ordagrant.
9. **Så tittar ägaren:** `cd kunder/<slug>/sajt && npx astro preview`, samt skärmbilderna i `prov/inspektion/`.

Avsluta sedan. Stoppvakten (`.claude/hooks/stoppvakt.py`) kör hela provet själv och släpper inte avslutet förrän
grindarna är gröna och rapporten finns. Blockerar den: läs skälet, rätta, försök igen.

## Steg 8 — Dom (ägaren, utanför körningen)

Ägaren tittar på sajten och rapporten och skriver sin dom ordagrant i `LARDOMAR.md`: bättre än deras? nära
referenserna? vad är fel? I en senare session blir varje dom en textändring i rätt fil (`regler/antislop.md`, den här
skillen, en kunskapsfil eller referenslistan). En ändring per dom, så att ägaren kan läsa den på fem minuter.
