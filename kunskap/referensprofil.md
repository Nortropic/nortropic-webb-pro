# DevTools för valda referenssidor

Referensprofilen beställs efter planprövningen, i varje kandidats egen kedja före dess skiss (ägarens
förenklingsuppdrag 2026-10-10, D; förr i ett gemensamt steg före alla skapare, där en kandidats brist stoppade alla).
Den kompletterar referenspaketets bilder och SEKTIONER.md med prestandaspåret, Lighthouse, LCP-elementet och dess
regler och sidans nätresurser. Den bedömer inte referensens designkvalitet.

**Överlappet med fångsten.** Fångsten (`referens.py`, `inspektera.mjs`) har redan, per sektion, bilden, måtten, de
renderade typsnitten, de CSS-regler som träffar (CDP `CSS.getMatchedStylesForNode`), ett DOM-utdrag och resursernas
ursprung, i 390 och 1440. Det profilen ensam ger är prestandaspåret med insikterna, Lighthouse och LCP-elementet.
Profilen beställs ändå med sina obligatoriska verktygsgrupper (kvittot är oförändrat), och skaparen läser den
tillsammans med SEKTIONER.md; ett smalare uppdrag till DevTools-sessionen är en möjlig fortsättning som kräver ett
verkligt profilprov för att mäta vinsten.

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

## Kedjan per kandidat

`kandidater.referensprofil_klar` kör kandidatens beställning som egen process (`referensprofil.py <slug> --kandidat kNN
--metod <sha>`, genom referensstegets körväg `skapande.kor_trad`), så att DevTools-sessionens startskydd gäller i
processens huvudtråd och stoppet avslutar hela trädet. Rapporten skrivs atomiskt i kandidatens egen katalog
(`underlag/<slug>/atelje/kandidater/<id>/REFERENSPROFIL.json`) och bär uppdragets sha256. Låset gäller sidan
(bindningens identitet), inte hela beställningen: olika sidor profileras samtidigt, med egen nätgräns, egen isolerad
Chrome och egen session per profil, och samtidigheten begränsas av skaparpoolen (högst tre). En sida som en annan
kandidat profilerar väntas in och återanvänds. En kandidat vars referensval brister får bristen och ingen profil, och
de andra kandidaternas beställningar görs ändå. En brist är underlag, inte en spärr (ägarens uppdrag 2026-10-11 om
designflödet): den sparas i kandidatens status (`referensprofil` med `brister`), skaparen startar och får veta att
profilen är ofullständig, och arbetar från referensbilderna och SEKTIONER.md, som fångsten redan mätt. Kandidatprovet
2026-10-11 visade varför: ett prestandaspår som inte blev klart stoppade k02 två gånger fast CSS-reglerna var uppmätta.
En äldre starts spärr (status fel med `referensprofil_brister`) tas upp av nästa start och profileras en gång till, aldrig i
en slinga. Ett stopp under profileringen är ett avbrott. Ett prov med ett annat underlag än motorns startar aldrig en
verklig profilering (`kandidater.profilrapport`).

## Vad skaparen får

Kandidatens rapport sparas innan dess skapare startar. Skaparens prompt (`kandidater.profil_rader`) får bara
kandidatens egna giltiga profiler, bundna till uppdraget som det står i planen; UPPDRAG.md skrivs inte om av
profileringen. Skaparen läser profilen tillsammans med referensbilderna och SEKTIONER.md och redovisar vilka tekniska
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
