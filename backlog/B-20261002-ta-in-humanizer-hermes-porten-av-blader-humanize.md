---
id: B-20261002-ta-in-humanizer-hermes-porten-av-blader-humanize
status: klar
kalla: kirurg
kallref: kunskap/REGISTER.md · 2026-10-02 · NousResearch/hermes-agent
skapad: 2026-10-02
prio: normal
steg: 4
commit: 547a1df
andrad: 2026-10-02T15:38Z
---
# Ta in humanizer (Hermes-porten av blader/humanizer) i verktygslådan för byggets text i steg 4

**Varför:** Ta in: ägaren pekade i L1–L3 ut rytm och register (slagfrasrubriken, byråmeningen, det skrivna i stället för sagda) som fraslistan i copy-kontroll inte fångar. Humanizer är en katalog över 34 mönster med före och efter, röstkalibrering mot ett eget textprov och ett självprov, och tappar värde om den kokas ned.

**Förslag:** .claude/skills/humanizer/: SKILL.md ur skills/creative/humanizer/ @ 0a374d1, båda LICENSE (Siqi Chen, Nous Research), KALLA.md med källa, commit, Wikipedia Signs of AI writing (CC BY-SA 4.0) och krockarna (svenska citattecken, mönster 26 gäller engelska, rösten ur verksamhetens och kundernas ord, inget påhittat; exemplet på rad 602 hittar på en person). Ta bort avsnittet How to use it in Hermes och frontmatterns platforms/metadata; beskrivningen säger: används i steg 4 på INNEHALL.md efter copykontrollen, med briefens fem formuleringar som röstprov. En halv mening i .claude/skills/bygg-sajt/SKILL.md rad 171–172 pekar på den.

**Klart när:** Skillen finns med LICENSE och KALLA.md, rokprov grönt, och nästa byggrapport nämner den under Verktygslådan.

**Klar (2026-10-02):** i verktygslådan med svenskt förord; steg 4 pekar på den
