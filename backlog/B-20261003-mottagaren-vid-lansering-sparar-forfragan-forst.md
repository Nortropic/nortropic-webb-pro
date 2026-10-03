---
id: B-20261003-mottagaren-vid-lansering-sparar-forfragan-forst
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-03 · Websites for Normal People (Sebastian Koning), via ägarens genomgång
skapad: 2026-10-03
prio: normal
steg: Formuläret vid lansering (byggstandarden 6.6; kunskap/forfragan.md, Vid lansering)
commit: bab673e
andrad: 2026-10-03T09:50Z
---
# Mottagaren vid lansering sparar förfrågan först och mejlar sedan, så att ett mejlfel aldrig tappar en förfrågan

**Varför:** Kirurgen dömde Websites for Normal People ta in för en enda princip: spara inskicket innan mejlet går, för e-posten är den del som fallerar (leverantören har en dålig dag, en DNS-post ändras, mejlet hamnar i spam), och utan lagring är förfrågan borta utan att någon vet att den fanns. Vår text säger 303 till /tack/ först när mejlet accepterats och vid fel 303 till /fel/ med telefonnumret (forfragan.md rad 46–47; byggstandarden 6.6), så att den skriftliga väg ägaren gjorde obligatorisk i L1–L3 kan tappa just den kund som skrev kl 21 när ingen svarar.

**Förslag:** kunskap/forfragan.md, avsnittet Vid lansering, punkt 5–6: (a) varje giltigt inskick sparas i värdens egen lagring före mejlet, med fälten och bilden, lagringstid som integritetssidan anger och gallring när tiden gått; (b) mejlet skickas sedan som i dag; (c) vid mejlfel: 303 till /fel/ som säger att förfrågan är mottagen och att verksamheten hör av sig, med telefonnumret som väg vidare, och verksamheten kan hämta sparade inskick; punkt 2 i avsnittet I varje bygge: integritetssidans lagringstid gäller också det sparade inskicket. kunskap/byggstandard.md rad 89, punkt 6.6: 'Inskicket sparas före sändning; "skickat" först när mejlet accepterats; vid fel visas telefonnumret och inskicket finns kvar.' Demon ändras inte: mottagaren sparar och skickar ingenting (forfragan.md rad 25–27) och ingen egen databas införs där (formularsakerhet.md rad 19); lagringen hör till Vercel-steget och skrivs in i lansering.md när den posten tas (B-20261003-skriv-om-kunskap-lansering-md-for-var-stack-den).

**Klart när:** forfragan.md och byggstandard.md säger spara först, mejla sedan, med lagringstid och gallring och /fel/-sidans besked; integritetssidans krav nämner det sparade inskicket; kontroller/rokprov.sh grönt

**Klar (2026-10-03):** spara först, mejla sedan; 6.6
