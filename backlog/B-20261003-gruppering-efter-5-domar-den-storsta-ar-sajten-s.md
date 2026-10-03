---
id: B-20261003-gruppering-efter-5-domar-den-storsta-ar-sajten-s
status: pagar
kalla: dom
kallref: kunskap/GRUPPERING.md 2026-10-03
skapad: 2026-10-03
prio: hog
andrad: 2026-10-03T09:06Z
---
# Gruppering efter 5 domar: Den största är sajten som säger mer än underlaget belägger (11 fynd). Byggstanda

**Varför:** Den största kategorin i ägarens domar och granskarens fynd (kunskap/GRUPPERING.md).

**Förslag:** .claude/skills/bygg-sajt/SKILL.md, steg 4 (Innehåll före form, rad 177–193): Lägg till en rad `Belägg:` under raden `Specifikt:` i varje sektion av INNEHALL.md. Ungefär så här i skillen: "Under `Specifikt:` står raden `Belägg:`. Den anger källan i underlaget (fil och avsnitt, URL eller omdömets namn och datum) för varje mening som säger hur verksamheten arbetar (vem som kommer, hembesök, pris, öppettider), vad den gjorde i ett jobb, vem som gör vad, eller vad en kund sagt. Det gäller också ord som 'senast', 'alltid', 'två gånger' och 'nyckelfärdigt'. Saknas källan skriver du det källan faktiskt säger, eller stryker meningen och beställer uppgiften i BESTALLNING.md. En hänvisning ('se Bokadirekt') ersätter aldrig en uppgift som saknas." Ändra också sista meningen i steg 4, efter humanizer-passet, till: "…och kör copykontrollen igen. Gå igenom Belägg-raderna en sista gång: rösten får ändra orden, aldrig vad som påstås." Det är fyra till fem rader text i en befintlig fil. Inget nytt skript och ingen ny grind.

**Klart när:** I nästa bygge har underlag/<slug>/INNEHALL.md en rad `Belägg:` under varje sektion (`grep -c 'Belägg:'` ger samma tal som `grep -c 'Specifikt:'`), och varje rad pekar på en källa som finns i underlaget. Granskarnas utlåtanden har inget blockerande textfynd av sorten 'saknar stöd i underlaget' i omgång 1, och inget i sista omgången. Ägarens nästa dom pekar inte på någon mening som säger mer än underlaget. I SKILL.md syns ändringen som en ny mening intill `Specifikt:` i steg 4 och ett tillägg i stegets sista mening.
