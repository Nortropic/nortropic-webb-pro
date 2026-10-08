# Redaktionellt pass — svenskt arbetsunderlag (P2)

Härlett arbetsunderlag (2026-09-26). Källor: webbgrundens `references/copy-blocklist.md` @ `e4c8c52`, rad 26–40,
`agents/content-designer.md`, rad 23–31, samt frontend-designs "More on writing in design"
(`externa/anthropic-frontend-design-SKILL.md`). Stöd för struktur, kundnytta, aktiv röst, enhetliga begrepp och
begripliga fel. Universella krav på org.nr, F-skatt och upprepad ort följer inte med; kundens belagda uppgifter styr.

**Allt nedan är bedömningsstöd, inte språkförbud.** Sammanhanget avgör, inte antalet upprepningar. Kedjedrivaren läser
varje sida som besökare efter bygget, före slutgranskningen, och rapporterar två saker separat:

- **Faktatrohet** — `faktakontroll.mjs` och källtaggarna avgör; passet ändrar inget här.
- **Redaktionell kvalitet** — passets egen fråga.

## Del 1: läs varje sida som besökare

För varje sida, skriv en rad per avsnitt: *vad tillför avsnittet besökaren?* Ett avsnitt som bara upprepar löftet,
beskriver oss själva eller planen, eller fyller ut, är ett fynd.

Frågor att ställa (svara med ställe och förslag, inte med räkning):
- Löftet återkommer N gånger på sidan: tillför varje förekomst något i sitt sammanhang?
- Spegelöppnare ("Vi … Vi … Vi …") eller tre likadana fyllnadsled i rad?
- Ord som beskriver oss själva eller vår planering i kundtext ("målgrupp", "upplägg", "segment", "vår process")?
- Passar tonen mottagaren (en villaägare eller en förening, inte en byrå)?
- Aktiv röst? Samma namn på samma sak genom hela flödet (tjänstens namn, tillvalets namn, knappens etikett)?
- Förklarar felmeddelanden vad som hände och vad besökaren kan göra?
- Ställer FAQ frågor som besökare faktiskt ställer, och svarar den på dem?
- Utropstecken, "Välkommen till", tomma superlativ?

## Del 2: erbjudandets innebörd genom kedjan

Följ varje tjänst och varje tillval genom: **tjänst → FAQ → interaktivt val → formulär → slutbesked**. Tabell per tillval
med kolumnerna: valt / bortvalt · vad som *ingår* · vad besökaren *önskar* · vad som faktiskt *avtalas* (inget före
offert) · vad som *händer efter en handling* (slutbeskedets löfte). Ett led som säger något annat än de andra är ett fynd.

Skilj två kontroller: **strängprovet** (fallets `kedja.mjs`, matchar bestämda formuleringar och fältvärden; är
regression för det fallet och bevisar inget om nästa sajt) och **läsningen** (denna del; den generella kontrollen).
Vid nästa fall skrivs ett nytt strängprov för det fallets kedja.

## Utdata

`REDAKTIONELLT-PASS-<fall>.md` i fallets mapp: fynd med sida och ställe, förslag, och vad som medvetet lämnas (med skäl).
Fynd som ändrar godkänt innehåll blir förslag till ägaren eller en egen commit inom gällande mandat, aldrig en tyst
ändring. Slutgranskaren (D) får underlaget som fråga, inte som facit.

## Prövning av metoden

Ett **seedat fall** (planterade avvikelser i en arbetskopia, blind läsning) är kalibrering; ett nytt fall är den riktiga
prövningen. Gamla rättade ställen är regressionsfall.
