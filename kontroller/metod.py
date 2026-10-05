#!/usr/bin/env python3
"""metod.py — metodkartans utdrag, levererade och versionsbundna (synpunkterna på metodkartan 2026-10-05, punkt 7:
en gemensam, versionsbunden metoddefinition med kontrollerad leverans av relevanta utdrag).

`kunskap/metodkarta.md` har per steg block märkta ```utdrag före```, ```utdrag varv``` eller ```utdrag``` med en rad
per källa:

    <väg>[ rad a–b[, c–d …]][ # <rubrik>]
    @<avsnitt>                       (ett annat avsnitts block, till exempel @Text)

Vägen är relativ repots rot (kunskap/…, kritik/…) eller `.claude/skills/` (en skills fil). Utan rader och rubrik tas
hela filen; med en rubrik tas avsnittet från rubriken till nästa rubrik på samma eller högre nivå. Låset
`kunskap/metodkarta.lock.json` håller sha256 för varje källa: en källa som ändrats sedan utdragen prövades stoppar
leveransen tills kartan prövats om och låset skrivits (`--las`). Radnummer kan alltså aldrig tyst peka fel.

    .venv/bin/python kontroller/metod.py --prova          (varje utdrag finns och källorna är de låsta; slutkod 0/1)
    .venv/bin/python kontroller/metod.py --las            (skriv låset efter att utdragen prövats)
    .venv/bin/python kontroller/metod.py --visa skapa     (stegets leverans som text)

leverera(steg, katalog) skriver stegets filer (METOD-<steg>.md, och vid behov METOD-<steg>-varv.md och
METOD-<steg>-text.md) med kartans text för steget, avgörandena och utdragen med källa, rader och hash, och ger
{'filer', 'sha', 'kallor'}. En del som blir större än MAX_TECKEN delas i filer med -2, -3 … i namnet, så att varje fil
ryms i ett Read utan offset och limit (Claude Codes Read tar högst 25 000 token och 2 000 rader per läsning; granskning
2, N5). Prompterna pekar på filerna, och kandidaternas status och granskningar bär hashen.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KARTA = ROOT / 'kunskap' / 'metodkarta.md'
LAS = ROOT / 'kunskap' / 'metodkarta.lock.json'
SKILLS = ROOT / '.claude' / 'skills'
MAX_TECKEN = 30000  # per levererad fil: ett Read utan offset och limit, med god marginal till 25 000 token
MAX_RADER = 1500  # och under Reads 2 000 rader
STEG = {'forska': 'Research', 'plan': 'Plan', 'skapa': 'Skapa', 'skiss': 'Skiss', 'granska': 'Granska', 'forfina': 'Förfina', 'text': 'Text'}
RAD = re.compile(r'^(?P<vag>[A-Za-z0-9_./-]+\.(?:md|csv|txt))(?:\s+rad\s+(?P<rader>[0-9][0-9–\-, ]*))?(?:\s+#\s*(?P<rubrik>.+?))?\s*$')
BLOCK = re.compile(r'^```utdrag(?:[ \t]+(?P<del>före|varv|uppslag))?[ \t]*\n(?P<rader>.*?)^```[ \t]*$', re.M | re.S)


class MetodFel(Exception):
    pass


def sha(text):
    return hashlib.sha256(text.encode('utf-8') if isinstance(text, str) else text).hexdigest()


def kalla(vag):
    """Källans fil: repots egna (kunskap/, kritik/, mall/) eller en skills fil under .claude/skills/."""
    return ROOT / vag if vag.split('/', 1)[0] in ('kunskap', 'kritik', 'mall') else SKILLS / vag


def avsnitt(text, rubrik):
    """Avsnittet under '## <rubrik>' (nivå 2) i kartan, utan rubriken."""
    m = re.search(r'^## %s[ \t]*$' % re.escape(rubrik), text, re.M)
    if not m:
        raise MetodFel('metodkartan saknar avsnittet "%s"' % rubrik)
    slut = re.search(r'^## ', text[m.end():], re.M)
    return text[m.end():m.end() + slut.start()] if slut else text[m.end():]


def tolka(text):
    """{avsnitt: {'prosa': text utan block, 'block': {'före'|'varv': [rad, …]}}} för stegens avsnitt och Avgöranden."""
    ut = {}
    for rubrik in list(STEG.values()) + ['Avgöranden']:
        a = avsnitt(text, rubrik)
        block = {}
        for m in BLOCK.finditer(a):
            del_ = m.group('del') or 'före'
            block.setdefault(del_, []).extend(r.strip() for r in m.group('rader').splitlines() if r.strip())
        ut[rubrik] = {'prosa': BLOCK.sub('', a).strip(), 'block': block}
    return ut


def rubrikavsnitt(rader, rubrik):
    """(start, slut), 1-baserat och inklusive, för avsnittet under en rubrik i en markdownfil."""
    mal = rubrik.lstrip('#').strip()
    for i, r in enumerate(rader):
        m = re.match(r'^(#{1,6})\s+(.*?)\s*$', r)
        if m and m.group(2).strip() == mal:
            niva = len(m.group(1))
            for j in range(i + 1, len(rader)):
                n = re.match(r'^(#{1,6})\s', rader[j])
                if n and len(n.group(1)) <= niva:
                    return i + 1, j
            return i + 1, len(rader)
    raise MetodFel('rubriken "%s" finns inte' % mal)


def utdrag(rad):
    """{'vag', 'fil', 'intervall': [(a, b)], 'text', 'sha'} för en utdragsrad; MetodFel när den inte går att lösa."""
    m = RAD.match(rad)
    if not m:
        raise MetodFel('utdragsraden går inte att läsa: %r' % rad)
    vag = m.group('vag')
    f = kalla(vag)
    if not f.is_file() or f.is_symlink():
        raise MetodFel('%s finns inte' % vag)
    innehall = f.read_text(encoding='utf-8')
    rader = innehall.splitlines()
    intervall = []
    if m.group('rader'):
        for del_ in m.group('rader').split(','):
            a, _, b = del_.strip().replace('-', '–').partition('–')
            a, b = int(a), int(b or a)
            if not 1 <= a <= b <= len(rader):
                raise MetodFel('%s rad %d–%d finns inte (filen har %d rader)' % (vag, a, b, len(rader)))
            intervall.append((a, b))
    if m.group('rubrik'):
        try:
            intervall.append(rubrikavsnitt(rader, m.group('rubrik')))
        except MetodFel as e:
            raise MetodFel('%s: %s' % (vag, e))
    if not intervall:
        intervall = [(1, len(rader))]
    text = '\n\n[…]\n\n'.join('\n'.join(rader[a - 1:b]) for a, b in intervall)
    return {'vag': vag, 'fil': f, 'intervall': intervall, 'text': text, 'sha': sha(innehall)}


def las_lasfil():
    try:
        return json.loads(LAS.read_text(encoding='utf-8')).get('kallor') or {}
    except (OSError, ValueError, AttributeError):
        return {}


def stegets_rader(karta, rubrik, del_, sett=None, utom=()):
    """Utdragsraderna för ett avsnitts del, med @-hänvisningar upplösta (en gång var); utom: hänvisningar som levereras
    i en egen fil (@Text)."""
    sett = set() if sett is None else sett
    ut = []
    for r in karta[rubrik]['block'].get(del_, []):
        if r.startswith('@') and r[1:].strip() in utom:
            continue
        if r.startswith('@'):
            mal = r[1:].strip()
            if mal not in karta:
                raise MetodFel('%s hänvisar till ett avsnitt som inte finns: %s' % (rubrik, r))
            if mal not in sett:
                sett.add(mal)
                ut += stegets_rader(karta, mal, 'före', sett) + stegets_rader(karta, mal, 'varv', sett)
        else:
            ut.append(r)
    return ut


def prova(karta_text=None, las=None):
    """Fel i kartan: varje utdrag löses, varje källa har låst hash och är oförändrad. Ger (fel, kallor)."""
    text = KARTA.read_text(encoding='utf-8') if karta_text is None else karta_text
    las = las_lasfil() if las is None else las
    fel, kallor = [], {}
    try:
        karta = tolka(text)
    except MetodFel as e:
        return [str(e)], {}
    for rubrik in STEG.values():
        for del_ in ('före', 'varv', 'uppslag'):
            try:
                rader = stegets_rader(karta, rubrik, del_)
            except MetodFel as e:
                fel.append(str(e))
                continue
            for r in rader:
                try:
                    u = utdrag(r)
                except MetodFel as e:
                    fel.append('%s: %s' % (rubrik, e))
                    continue
                kallor[u['vag']] = u['sha']
    for vag, h in sorted(kallor.items()):
        if las.get(vag) != h:
            fel.append('%s %s sedan utdragen prövades: pröva raderna och skriv låset (metod.py --las)' % (vag, 'har ändrats' if vag in las else 'saknas i låset'))
    return fel, kallor


def packa(huvud, block, fortsattning):
    """Delarna av en fil: huvudet och utdragens block packade i ordning så att varje del håller sig under MAX_TECKEN och
    MAX_RADER (med marginal för filens titel); ett block som ensamt är för stort delas vid radgränser. Ger texterna."""
    def ryms(text):
        return len(text) <= MAX_TECKEN - 200 and text.count('\n') < MAX_RADER - 20
    bitar = []
    for b in block:
        if ryms(fortsattning + b):
            bitar.append(b)
            continue
        rubrikrad, _, kropp = b.partition('\n')
        bit = rubrikrad
        for r in kropp.split('\n'):
            if bit != rubrikrad and not ryms(fortsattning + bit + '\n' + r):
                bitar.append(bit)
                bit = rubrikrad + ' (fortsättning)\n' + r
            else:
                bit += '\n' + r
        bitar.append(bit)
    delar, nu_ = [], huvud
    for b in bitar:
        if nu_ != huvud and not ryms(nu_ + b):
            delar.append(nu_)
            nu_ = fortsattning
        nu_ += b + '\n\n'
    delar.append(nu_)
    return [d.rstrip() + '\n' for d in delar]


def leverera(steg, katalog):
    """Stegets metod som filer i katalogen: METOD-<steg>.md (läses före första ändringen), METOD-<steg>-varv.md (i
    varven), METOD-<steg>-text.md (texten) och METOD-<steg>-uppslag.md (utdrag att slå upp när uppgiften behöver dem,
    med en förteckning i METOD-<steg>.md), med kartans text för steget, avgörandena och utdragen; en del större än en
    läsning delas i -2, -3 …. MetodFel när kartan inte håller (prova)."""
    rubrik = STEG[steg]
    text = KARTA.read_text(encoding='utf-8')
    fel, kallor = prova(text)
    if fel:
        raise MetodFel('metodkartan håller inte: ' + '; '.join(fel[:6]))
    karta = tolka(text)
    katalog = Path(katalog)
    katalog.mkdir(parents=True, exist_ok=True)
    for gammal in katalog.glob('METOD-%s*.md' % steg):  # en tidigare leverans med fler delar lämnar inga gamla delar kvar
        if re.fullmatch(r'METOD-%s(?:-varv|-text|-uppslag)?(?:-\d+)?\.md' % re.escape(steg), gammal.name):
            gammal.unlink()
    regler = (ROOT / 'kunskap' / 'designregler.md').read_text(encoding='utf-8')
    hanv = [r[1:].strip() for d_ in ('före', 'varv') for r in karta[rubrik]['block'].get(d_, []) if r.startswith('@')]
    med_text = 'Text' in hanv and rubrik != 'Text'  # textens utdrag i en egen fil
    utom = ('Text',) if med_text else ()

    def block_for(rader):
        ut = []
        for r in rader:
            u = utdrag(r)
            ut.append(('### %s · %s · sha %s' % (u['vag'], ', '.join('rad %d–%d' % ab for ab in u['intervall']), u['sha'][:12]), u['text']))
        return ut

    def namn_for(stam, i, n):
        return '%s%s.md' % (stam, '-%d' % i if i > 1 else '')

    def titel_for(del_):
        return '# Metoden: %s%s' % (rubrik, {'varv': ' — i varven', 'text': ' — texten', 'uppslag': ' — att slå upp'}.get(del_, ''))

    def huvud_for(del_, titel, extra=()):
        h = [titel, '',
             'Levererad ur kunskap/metodkarta.md (sha %s) med designregler.md (sha %s). Utdragen nedan är exakt de avsnitt'
             % (sha(text)[:12], sha(regler)[:12]),
             'kartan anger, med källa, rader och källans hash. Där ett utdrag säger emot avgörandena gäller avgörandena.', '']
        if del_ == 'före':
            h += ['## Steget', '', karta[rubrik]['prosa'], '', '## Avgöranden', '', karta['Avgöranden']['prosa'], ''] + list(extra)
        elif del_ == 'text':
            h += ['## Texten', '', karta['Text']['prosa'], '']
        elif del_ == 'uppslag':
            h += ['Slå upp det avsnitt uppgiften behöver; filen läses inte i förväg.', '']
        return h + ['## Utdragen', '', '']

    texter, index = {}, []
    up_rader = stegets_rader(karta, rubrik, 'uppslag', utom=utom)
    if up_rader:  # uppslaget först: förteckningen i före-filen pekar på filen där varje utdrag står
        titel = titel_for('uppslag')
        delar = packa('\n'.join(huvud_for('uppslag', titel)), ['%s\n\n%s' % b for b in block_for(up_rader)], titel + '\n\n## Utdragen (fortsättning)\n\n')
        texter['uppslag'] = (titel, delar)
        for i, t_ in enumerate(delar, 1):
            for rubrikrad in re.findall(r'^### (.+?) · sha [0-9a-f]+$', t_, re.M):
                index.append('- %s → %s' % (rubrikrad, namn_for('METOD-%s-uppslag' % steg, i, len(delar))))
    for del_ in ('före', 'varv', 'text'):
        if del_ == 'text':
            if not med_text:
                continue
            rader = stegets_rader(karta, 'Text', 'före') + stegets_rader(karta, 'Text', 'varv')
        else:
            rader = stegets_rader(karta, rubrik, del_, utom=utom)
        if not rader and del_ != 'före':
            continue
        titel = titel_for(del_)
        extra = (['## Att slå upp', '', 'Utdragen ur skills och kunskapsfiler nedan slår du upp när uppgiften behöver dem; de läses inte i förväg:', '']
                 + index + ['']) if del_ == 'före' and index else ()
        texter[del_] = (titel, packa('\n'.join(huvud_for(del_, titel, extra)), ['%s\n\n%s' % b for b in block_for(rader)],
                                     titel + '\n\n## Utdragen (fortsättning)\n\n'))
    filer = []
    for del_, stam in (('före', 'METOD-%s' % steg), ('varv', 'METOD-%s-varv' % steg), ('text', 'METOD-%s-text' % steg), ('uppslag', 'METOD-%s-uppslag' % steg)):
        if del_ not in texter:
            continue
        titel, delar = texter[del_]
        for i, innehall in enumerate(delar, 1):
            if len(delar) > 1:
                innehall = innehall.replace(titel, '%s (fil %d av %d)' % (titel, i, len(delar)), 1)
            namn = namn_for(stam, i, len(delar))
            (katalog / namn).write_text(innehall, encoding='utf-8')
            filer.append({'fil': katalog / namn, 'del': del_, 'sha': sha(innehall)})
    return {'filer': filer, 'sha': sha(''.join(f['sha'] for f in filer)), 'karta': sha(text), 'kallor': kallor}


def main(argv=None):
    p = argparse.ArgumentParser(prog='metod', description=__doc__.split('\n\n')[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prova', action='store_true')
    g.add_argument('--las', action='store_true')
    g.add_argument('--visa', choices=sorted(STEG))
    a = p.parse_args(argv)
    if a.prova or a.las:
        fel, kallor = prova(las={} if a.las else None)
        if a.las:
            fel = [f for f in fel if 'sedan utdragen prövades' not in f]
            if fel:
                print('låset skrivs inte, kartan håller inte:\n' + '\n'.join('- ' + f for f in fel))
                return 1
            LAS.write_text(json.dumps({'kallor': dict(sorted(kallor.items()))}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print('låste %d källor i %s' % (len(kallor), LAS.relative_to(ROOT)))
            return 0
        print('\n'.join('- ' + f for f in fel) if fel else 'metodkartan håller: %d källor, alla låsta' % len(kallor))
        return 1 if fel else 0
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        try:
            res = leverera(a.visa, d)
        except MetodFel as e:
            print(e)
            return 1
        for f in res['filer']:
            print(f['fil'].read_text(encoding='utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
