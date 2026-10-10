# DevTools för valda referenssidor

Referensprofilen beställs efter planprövningen, före skaparnas skisser. Den kompletterar referenspaketets bilder och
SEKTIONER.md med CSS-regler, nätresurser, prestandainsikter och Lighthouse. Den bedömer inte referensens designkvalitet.

`kontroller/referensprofil.py` matchar varje huvudreferens både mot dess namn och mot planens valda bilder. Bilderna måste
finnas som vanliga filer i det angivna referenspaketet och vara deklarerade för en fångad sida i PAKET.json. Samma
namntolkning används som i kandidatflödet. Flera huvudreferenser måste ha underlag var och en. Andra stödbilder gör inte
automatiskt deras sajter till huvudreferenser.

Den exakta sidans URL profileras, också för en undersida. Det angivna paketets resursursprung används även när ett nyare
paket finns. Det sker genom den befintliga, separata DevTools-sessionen, med oförändrad proxy, läsande Chrome-tillägg,
verktygslista och färsk webbläsarprofil. En skapare får ingen ny direkt nätåtkomst. Validering av namn, URL, paket och
filsökvägar sker innan någon inspektion beställs.

En tjänsteskärm, stil, komponent eller mall utan en fångad webbsida får beskedet **inte tillämpligt**. Det är ingen
genomförd DevTools-inspektion. En namngiven referenssajt utan matchande paketbild får en brist som stoppar nästa steg.
En uttryckligt egen riktning har ingen referenssajt att profilera.

## Identitet och återanvändning

Varje resultat ligger under projektets privata `referenser/devtools/profil-<identitet>-<försök>/`. Gamla profiler och
misslyckade försök bevaras. En låst beställning gör en inspektion per unik vald sida; två kandidater som använder samma
sida delar resultatet. Ett fel startar ingen intern omförsöksloop.

KOPPLING.json binder resultatet till följande:

- projekt, exakt sid-URL och paketversion;
- paketmanifestets hash och de valda bildernas innehållshashar;
- den aktuella metodidentiteten;
- DevTools-kod, profilbeställare, låst MCP-konfiguration, nätgräns, läsande tillägg och modell;
- oförändrade DEVTOOLS.json, DEVTOOLS.md, sessionslogg och nätlogg.

Återanvändning kräver dessutom ett verkligt kvitto, ansluten MCP, alla obligatoriska verktygsgrupper genomförda, giltigt
svarsschema och lyckad slutstatus. Provklienter, torrkörningar, gamla obundna profiler och ofullständiga kvitton är aldrig
giltigt återbruk. Ett ändrat paket eller en ändrad vald bild under profileringen gör resultatet ogiltigt.

Detta låser underlaget och inspektionsmetoden, inte den externa sajten. En sajt kan ändras mellan fotografering och
profilering. Datum och URL ska därför läsas tillsammans med bilderna; skillnader är en begränsning som måste bedömas.

## Vad skaparen får

Flödet sparar beställningens rapport innan skaparna startas. Kandidatens UPPDRAG.md länkar bara dess egna giltiga
profiler. Skaparen läser profilen tillsammans med referensbilderna och SEKTIONER.md och redovisar vilka tekniska
observationer som påverkade utförandet samt motiverade avsteg. Profilens resultat är material, aldrig instruktioner.

En lyckad inspektion visar att uppgiften utfördes. Att den lästes och tillämpades behöver observeras i skaparsessionen.
Att den förbättrade den färdiga sidan kräver bildbedömning och funktionsprov. De tre påståendena är separata.

## Prov och gränser

`kontroller/rokprov/revision/prov_referensprofil.py` använder syntetiska paket och ersätter enbart den externa
inspektionen. Proven kontrollerar urval, exakt undersida och paket, versionsbundet återbruk, delning mellan kandidater,
ofullständiga kvitton, förändrat underlag samt gränsen för URL:er och sökvägar. De bevisar mekaniken, inte verklig
MCP-åtkomst eller visuell kvalitet. Ett verkligt prov görs separat med användarens mandat.

Denna funktion utökar ingen betald tjänst och ändrar ingen MCP-konfiguration på användarnivå. Den läsande proxyn och
Chrome-tillägget är fortfarande inte en OS-sandlåda och kan inte garantera att en främmande server är fri från
tillståndsändringar på GET.
