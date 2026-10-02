---
id: B-20261002-gatuadressen-visas-nar-verksamheten-sjalv-visar
status: pagar
kalla: dom
kallref: LARDOMAR.md · AB · 2026-10-02
skapad: 2026-10-02
prio: hog
steg: 1 och 6
andrad: 2026-10-02T16:56Z
---
# Gatuadressen visas när verksamheten själv visar den: i sidfoten, på kontaktsidan och i JSON-LD

**Varför:** Ägaren (AB 2026-10-02): B har fullständig NAP, Tallundsvägen 21 i sidfoten, på kontaktsidan och i JSON-LD, medan A saknar gatuadress överallt (7.4). A satte adress.publik=false och roll hemvist, fast verksamheten själv visar adressen på luleasnickaren.com och i platsannonsen.

**Förslag:** Villkor i bygg-sajt steg 1 punkt 3 och kunskap/research-underlag.md: publik=true när verksamheten själv visar gatuadressen (egen sajt, Google-profil, annons); false bara när den enbart finns i register. Standarden (7.4) med --verksamhet: när publik=true ska gatan stå i sidfoten på varje sida, på kontaktsidan och som streetAddress i JSON-LD.

**Klart när:** standard_kontroll fäller en sajt där den publika adressen saknas i sidfot, på kontaktsida eller i JSON-LD; rökprovet prövar det
