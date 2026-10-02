---
id: B-20261002-mallens-tidsfalla-skickar-klientens-date-now-som
status: klar
kalla: bygge
kallref: kunder/lulea-snickaren-abx/RAPPORT.md
skapad: 2026-10-02
prio: normal
steg: 5
commit: f5abe90
andrad: 2026-10-02T15:32Z
---
# Mallens tidsfälla skickar klientens Date.now() som mottagaren jämför mot sin egen klocka, i strid med formularsakerhet.md

**Varför:** mall/astro/src/components/Forfragan.astro sätter fältet laddad till Date.now() i webbläsaren, och kunskap/forfragan.md säger att mottagaren svarar tyst om laddad är satt och mindre än 3 sekunder sedan. kunskap/formularsakerhet.md (princip b) förbjuder just att jämföra en klientstämpel med serverns tid: klockskillnad tappar riktiga förfrågningar tyst. Bygget fick inte ändra fällorna.

**Förslag:** mall/astro/src/components/Forfragan.astro: mät tiden på klienten med performance.now() från sidladdning till inskick och skicka varaktigheten i ms; kunskap/forfragan.md punkt 3: mottagaren jämför varaktigheten mot 3000 ms och godtar tomt värde (fail-open).

**Klar (2026-10-02):** fylltid med performance.now(), 1500 ms, fail-open
