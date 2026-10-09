# Dyad-provet: det som når modellen, per roll

Ägarens uppdrag 2026-10-09 (ordagrant i `BESLUT.md`, beskedet om Dyad-provet): "bygg hela Dyad-provet. Steg 1
genomförbarhet (claude -p mot falsk server, stanna och redovisa om det inte går). Steg 2 provläge låst till prov, med
prov att det aldrig gäller i drift. Steg 3 prov per roll: modell, instruktion, bildernas sha256 och att blinda roller
saknar skaparens material. Inga riktiga nycklar i dumparna." Idén kommer från Dyads fake-llm-server, som dumpar hela
förfrågan till modellen (källgenomgången 2026-10-09, avsnitt 5).

## Vad provet visar och inte visar

Provet visar vad flödets roller faktiskt skickar till modellen: modellen och ansträngningen, rollens instruktion, varje
bild uppdraget nämner och att de blinda rollerna nekas skaparens material. Det prövar vägen genom Claude Code, flödets
inställningar, förbud och krokar, inte modellens omdöme: den falska modellen är skriptad. Den läser varje bild uppdraget
nämner och de filer provet ber om, och svarar sedan med ett minsta giltigt svar ur rollens schema.

## Delarna

- `kontroller/falsk_modell.py`: en lokal Messages-server på 127.0.0.1 som svarar med SSE som Anthropics API. Varje
  förfrågan sparas som en dump. Bilderna sparas som media_type, byte, mått och sha256 av de avkodade byten, aldrig som
  base64. Nyckel- och tokenvärden sparas aldrig, bara om headern var provets egen nyckel. Enhetens id i metadata tas
  bort. `dumpar()` sammanfattar per förfrågan: modell, ansträngning, systemprompt, användarens text, läsningarna (fil,
  nekad, bilder) och verktygen.
- **Provläget** (`nastlad.provlage`, `nastlad.miljo(rot=…)`): en nästlad session får `ANTHROPIC_BASE_URL` och
  `ANTHROPIC_API_KEY` bara när `NWP_FALSK_MODELL` är en lokal http-adress med port, `NWP_FALSK_NYCKEL` börjar med
  `sk-ant-prov-` och repots rot inte är huvudutcheckningen. Är en variabel satt utan att villkoren håller stoppas
  sessionen (`ProvlageFel`): ett prov går aldrig tyst mot prenumerationen, och drift går aldrig mot en falsk modell.
  Vägar utan rot (granskarna, prospekten) stoppas också. Utan variablerna gäller det vanliga: ingen nyckel och ingen
  bas-URL följer med, och sessionerna går på prenumerationen.
- `kontroller/rokprov/revision/prov_dyad.py`, i rökprovets lista:
  - **Provlaget**: reglerna ovan, att inga andra filer än provet, servern och nastlad.py nämner variablerna (ingen
    driftväg sätter provläget), att dumpen inte sparar nycklar eller bilddata, och att minsta svaret håller flödets
    scheman.
  - **Rollerna**: kopierar repot, eftersom provläget aldrig gäller i huvudutcheckningen, och kör tre riktiga
    `claude -p`-sessioner genom flödets egna funktioner. Varje roll har en egen falsk server och en egen dump:
    skisskritiken (`kandidater.skisskritik`), före/efter-granskaren (`kandidater.fore_efter`) och skaparen i ett
    uppdrag (`kandidater.uppdrag_session`, samma anrop som `forfina_kandidat`).

## Påståendena per roll

| Påstående | Skisskritiken och före/efter (blinda) | Skaparen |
|---|---|---|
| Modellen | `GRANSKARE_MODELL` (med 1M-kontextens beta-header när modellen har `[1m]`) | `atelje.MODELL` |
| Ansträngningen | high | `atelje.EFFORT` |
| Instruktionen | rollens inledning ordagrant i förfrågan | uppdragets inledning och det önskade resultatet ordagrant |
| Bilderna | varje bild uppdraget nämner nådde modellen: sha256 lika filens, eller samma bild nedskalad med samma proportioner | – |
| Skaparens material | RIKTNING.md och UPPDRAG.md nekas, och deras unika markörer finns inte i någon förfrågan | motprovet: skaparen läser dem, och markörerna finns i förfrågan |
| Nycklarna | bara provets nyckel skickades, och inget nyckelvärde står i dumparna | samma |

## Utfallet 2026-10-10

Steg 1, genomförbarheten: `claude -p` (Claude Code 2.1.290) går mot den falska servern med en provnyckel, också med
den vanliga konfigurationskatalogen. Bara `x-api-key` med provnyckeln skickas, och ingen OAuth-token. Steg 2 och 3:
alla påståenden höll. Varje roll gjorde två förfrågningar i en session.

Fynd om bilderna: Claude Code skickar en bild oförändrad när dess längsta sida är högst 2000 px. En större bild skalas
ned till 2000 px på den längsta sidan innan den når modellen. Uppmätt 2026-10-10: 1440 × 2400 blev 1200 × 2000,
390 × 3000 blev 260 × 2000 och 390 × 8000 blev 98 × 2000, medan 1440 × 900 gick oförändrad. En lång helsidesbild i
mobilbredd når alltså modellen kraftigt förminskad. Skärmhöga rutor, som granskarens förhandsvisning redan ger, är det
som bär detaljerna.

## Köra

```sh
.venv/bin/python kontroller/rokprov/revision/prov_dyad.py            # båda delarna (rollerna kräver claude)
.venv/bin/python kontroller/rokprov/revision/prov_dyad.py Provlaget  # bara provläget
```

Rollerna tar omkring 30 sekunder och kräver Claude Code. Utan `claude` hoppas de över, och skälet skrivs ut.
