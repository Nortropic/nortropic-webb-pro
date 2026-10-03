---
id: B-20261003-prova-json-ld-mot-schema-org-s-vokabular-okand-t
status: vilande
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · webstudio-is/webstudio
skapad: 2026-10-03
prio: normal
steg: 6 (prov: seo_kontroll.py, byggstandarden 7.3)
---
# Pröva JSON-LD mot schema.org:s vokabulär: okänd typ, okänd eller utgången egenskap, egenskap som inte hör till typen

**Varför:** Webstudios granskningsverktyg har reglerna unknown-schema-org-type, unknown-schema-org-property, deprecated-schema-org-type/-property och incompatible-schema-org-value. Vår seo_kontroll.py prövar bara att blocket är giltig JSON och har @type, och standard_kontroll.py att typen är lokal och att BreadcrumbList finns; en felstavad eller påhittad egenskap passerar tyst och ger inget i Google.

**Förslag:** kontroller/seo_kontroll.py: hämta schema.org:s vokabulär en gång till kontroller/data/schemaorg.jsonld (CC BY-SA 3.0, licensen bredvid), och pröva varje @type mot klasserna och varje egenskap mot typen och dess föräldrar (rdfs:subClassOf, schema:domainIncludes); okänd typ eller egenskap = fel, utgången (schema:supersededBy) = info. Lägg en rad i kunskap/byggstandard.md 7.3 om att egenskaperna prövas mot vokabulären.

**Klart när:** kontroller/rokprov.sh är grönt; ett JSON-LD-block med en påhittad egenskap (t.ex. telefonnummer) ger fel i seo_kontroll, och mallens BreadcrumbList och LocalBusiness-blocket passerar.
