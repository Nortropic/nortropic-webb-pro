#!/usr/bin/env python3
"""ren_designstart.py — den rena designstarten (ägarens uppdrag 2026-10-09 ~17:53Z, punkt 3; ordagrant i BESLUT.md,
tillägget samma dag, och kunskap/ren-designstart.md).

Gamla byggen, prototyper, kandidater, skärmbilder, designomdömen, kalibreringsankare, riktningar och referenspaket
slutar påverka den nya processen. De tas ur den aktiva miljön (repots arbetskatalog med underlag/ och kunder/, och
flödets tempkataloger) efter ett privat manifest och ett verifierat återställningsarkiv utanför agenternas läs- och
sökrötter. Vakten prövar sedan vid varje start att inget av det kommit tillbaka.

    .venv/bin/python kontroller/ren_designstart.py --inventera            # manifestet som det skulle bli; ändrar inget
    .venv/bin/python kontroller/ren_designstart.py --arkivera --ja        # manifest, flytt till arkivet och verifiering
    .venv/bin/python kontroller/ren_designstart.py --prova                # vakten: slutkod 0 när inget kommit tillbaka
    .venv/bin/python kontroller/ren_designstart.py --aterstall <sökväg>   # flytta tillbaka en post ur arkivet

Klassningen står i reglerna nedan, en rad per slag med skälet. Bevaras gör kundens verifierade fakta, originalmaterial
och rättigheter, aktuella uttryckliga kundönskemål, säkerhetsskydden (låsfilerna, kundrepot), de tekniska proven och
deras data, rapporterna och granskningarna (historik, som flödets sessioner nekas) och git-historiken. Ingen katalog tas
bort på sitt namn ensamt: varje kundkatalog klassas post för post. Okänt ursprung arkiveras och redovisas.

Arkiveringen flyttar varje post (samma volym, en namnändring, inget kopieras eller raderas) till arkivet och prövar att
varje fil har samma sha256 före och efter. Faller prövningen flyttas posten tillbaka. Arkivet ligger under ~/Arkiv,
utanför repot, där flödets sessioner inte har någon läsregel (dontAsk nekar allt utanför arbetskatalogen som inte
uttryckligen tillåts), och atelje.NEKAS nekar det dessutom uttryckligen.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARKIV = Path(os.environ.get('NWP_REN_ARKIV') or Path.home() / 'Arkiv' / 'nortropic-ren-designstart-20261009')
NAMN = 'REN-DESIGNSTART-20261009'
REGISTER = Path('underlag') / 'rensning' / (NAMN + '.json')  # privat: posterna, brytpunkten, arkivets plats
HASHAR = Path('underlag') / 'rensning' / (NAMN + '.sha256')  # privat: de arkiverade filernas sha256, utan innehåll
TMP = Path('/private/tmp') if Path('/private/tmp').is_dir() else Path('/tmp')

# Det som bevaras i en kunds underlag (underlag/<slug> med VERKSAMHET.json): fakta, kundens ord och önskemål, material,
# rättigheter (bilder/BILDER.md), källor, beställningar och låsfilerna. Allt annat där är designarbete och arkiveras.
KUND_UNDERLAG_BEVARAS = {
    'VERKSAMHET.json': 'verifierade grunduppgifter',
    'UPPDRAG.md': 'kundens uppdrag (kundens ord och önskemål)',
    'KUNDSTART.json': 'Kundstarts överlämning (kundens ord)',
    'RESEARCH.md': 'belagda fakta med källor och antaganden om målgrupperna',
    'BRIEF.md': 'kundens behov och önskemål; §7 beskriver förutsättningar, ingen vald riktning',
    'TEXTUNDERLAG.md': 'kundens texter och märkta utkast',
    'INNEHALL.md': 'äldre textunderlag (kundens texter)',
    'BESTALLNING.md': 'öppna frågor och beställt material',
    'DIAGNOS.md': 'mätningen av kundens nuvarande sajt (fakta om den, inte vår design)',
    'FRASER.txt': 'copykontrollens fraslista för kunden',
    'RESOR.json': 'besökarnas resor (kundens behov)',
    'bilder': 'kundens originalmaterial med rättigheter (BILDER.md)',
    'kalla': 'källmaterialet bakom fakta',
    'material': 'kundens materialregister',
    'kundstart': 'Kundstarts underlag',
    '.atelje-start.las': 'startlåset tas aldrig bort (skapandeflodet.md, Avbrott)',
    '.atelje-process.las': 'processlåset',
}
# Det som bevaras i en kunds byggkatalog (kunder/<slug>): leveransens identitet och låsen. Sajten, kandidaterna,
# körningarnas poster, ägarens domar över byggen och rapporterna arkiveras; sajten görs om ur mallen vid nästa körning.
KUND_KUNDER_BEVARAS = {
    'kundrepo': 'kundrepot (leveransens git-repo; innehåller ingen design)',
    'KUNDREPO.json': 'kundrepots identitet',
    'leverans': 'leveransens poster',
    '.bygglas': 'låsfil',
    '.kundrepo.las': 'låsfil',
}
# Hela kataloger och filer som är gamla designexperiment, bedömningar eller kalibrering.
EXPERIMENT = {
    'underlag/kalibrering': ('kalibreringsankare', 'kalibreringens ankare, ägarens domar över externa exempel och försöken; '
                             'gamla kalibreringsresultat verifierar inte den nya metoden'),
    'underlag/LARDOMAR-original.md': ('designomdömen', 'ägarens domar över tidigare byggen, ordagrant'),
    'underlag/figma-pilot': ('designexperiment', 'Figma-pilotens moment A–C med bilder'),
    'underlag/figma-prov': ('designexperiment', 'Figma-provets förhandsbilder'),
    'kunder/figma-prov': ('genererade sidor', 'Figma-provets sajt'),
    'kunder/figma-moment-a': ('genererade sidor', 'Figma-pilotens sajt, moment A'),
    'kunder/lulea-figma-pilot': ('genererade sidor', 'Figma-pilotens sajt'),
    'kunder/ab': ('designexperiment', 'A/B-skissförsökens lottning och resultat'),
}
# Flödets tempkataloger med gamla kandidatbyggen och kalibreringsförsök (cache).
TMP_POSTER = {
    'nwp-bygge-navet-cykelverkstad': ('cache', 'byggena av kandidaterna i kvalitetsprovet'),
    'nwp-bygge-lulea-snickaren-prototyp': ('cache', 'byggena av Luleå-kandidaterna'),
    'nwp-granskarforsok': ('cache', 'kalibreringsförsökets kopior med ankare och exempel'),
}
# Spårade filer som tas ur arbetsträdet i samma commit (git-historiken bevarar dem); arkivet får en kopia och hashen.
GIT_POSTER = {
    'kunskap/visuell-niva.md': ('kalibreringsankare', 'ribban i tre nivåer, destillerad ur de gamla kalibreringsankarna'),
    'LARDOMAR.md': ('designomdömen', 'ägarens domar över tidigare byggen och de gamla kalibreringsförsöken; ny fil från brytpunkten'),
}
# Bevaras helt: tekniska prov och deras data, drift, rapporter och granskningar (historik som flödets sessioner nekas).
TEKNISKT = {
    'underlag/rokprov-mall': 'rökprovets fixtur', 'kunder/rokprov-mall': 'rökprovets fixtur',
    'underlag/startkontroll': 'underhållet och startkontrollen', 'underlag/kundstart': 'Kundstarts ärenden',
    'underlag/prospekt': 'prospekt och spärrlista', 'underlag/rapporter': 'rapporterna (historik; nekas flödets sessioner)',
    'underlag/granskningar': 'granskningarna (historik; nekas flödets sessioner)', 'underlag/arbetsyta': 'arbetsytans uppdragsbevis',
    'underlag/vantar-pa-agaren': 'städningens väntande poster', 'underlag/rensning': 'den här rensningens register',
    'underlag/kirurgen': 'kirurgens spaning', 'underlag/formagoprov': 'förmågeprovet (tekniskt)',
}
TEKNISKA_MONSTER = (r'^underlag/formagoprov-.*', r'^kunder/formagoprov-.*', r'^underlag/.*\.log$', r'^kunder/.*\.log$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def kundslugs(root):
    """Kunderna: underlag/<slug> med VERKSAMHET.json, utom de tekniska."""
    u = Path(root) / 'underlag'
    if not u.is_dir():
        return []
    return sorted(p.name for p in u.iterdir() if p.is_dir() and not p.is_symlink() and (p / 'VERKSAMHET.json').is_file()
                  and not tekniskt('underlag/' + p.name))


def tekniskt(rel):
    return rel in TEKNISKT or any(re.match(m, rel) for m in TEKNISKA_MONSTER)


def klassa(root=None, med_tmp=False):
    """(poster, bevaras, oklassat): posterna att arkivera med kategori och skäl, det som bevaras med skäl, och det som
    varken är kund, experiment eller tekniskt (det redovisas och rörs inte). med_tmp: också flödets tempkataloger (bara i
    den verkliga miljön, aldrig i ett prov)."""
    root = Path(root or ROOT)
    poster, bevaras, oklassat = [], [], []

    def post(rel, kategori, skal, absolut=None):
        poster.append({'sokvag': rel, 'kategori': kategori, 'skal': skal, **({'absolut': str(absolut)} if absolut else {})})

    kunder = kundslugs(root)
    for slug in kunder:
        u = root / 'underlag' / slug
        for p in sorted(u.iterdir(), key=lambda x: x.name):
            rel = 'underlag/%s/%s' % (slug, p.name)
            if p.name in KUND_UNDERLAG_BEVARAS:
                bevaras.append({'sokvag': rel, 'skal': KUND_UNDERLAG_BEVARAS[p.name]})
            else:
                post(rel, *underlagets_slag(p.name))
        k = root / 'kunder' / slug
        if k.is_dir() and not k.is_symlink():
            for p in sorted(k.iterdir(), key=lambda x: x.name):
                rel = 'kunder/%s/%s' % (slug, p.name)
                if p.name in KUND_KUNDER_BEVARAS:
                    bevaras.append({'sokvag': rel, 'skal': KUND_KUNDER_BEVARAS[p.name]})
                else:
                    post(rel, *kundernas_slag(p.name))
    for rel, (kategori, skal) in EXPERIMENT.items():
        if (root / rel).exists() or (root / rel).is_symlink():
            post(rel, kategori, skal)
    for namn, (kategori, skal) in TMP_POSTER.items():
        p = TMP / namn
        if med_tmp and p.exists():
            post('tmp/' + namn, kategori, skal, absolut=p)
    for topp in ('underlag', 'kunder'):
        d = root / topp
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir(), key=lambda x: x.name):
            rel = '%s/%s' % (topp, p.name)
            if p.name in kunder or rel in EXPERIMENT:
                continue
            if tekniskt(rel):
                bevaras.append({'sokvag': rel, 'skal': TEKNISKT.get(rel) or 'tekniskt prov eller logg'})
            else:
                oklassat.append(rel)
    return poster, bevaras, oklassat


def underlagets_slag(namn):
    if namn == 'atelje':
        return 'prototyper och kandidater', ('körningarna: planer, uppdrag, kandidater, skisskritik, granskningar, '
                                              'vinnare, metodkopior (cache), urval och förberedelsens kvitto')
    if namn.startswith('DESIGNDOMAR'):
        return 'designomdömen', 'domloggen med ägarens och andras domar över de gamla kandidaterna'
    if namn == 'RIKTNINGSHISTORIK.json':
        return 'gamla riktningar', 'prövade grundidéer med utfall och kritik'
    if namn == 'referenser':
        return 'referenslås och referenspaket', ('fångade referenssajter, stilpaket och tjänsternas svar; gamla externa '
                                                  'referenser återanvänds bara efter ett nytt uttryckligt urval')
    if namn.startswith(('REFERENSUPPDRAG-', 'TJANSTEUPPDRAG-')) or namn == 'REFERENSER.md':
        return 'referenslås och referenspaket', 'tidigare referensuppdrag och urval'
    if namn in ('KONCEPT.md', 'UPPTAGNA-VAL.md', 'DESIGN.md'):
        return 'designfiler', 'tidigare riktning, koncept eller upptagna val'
    if namn in ('prototyp', 'omtag'):
        return 'prototyper och kandidater', 'tidigare prototyper och det ägaren bedömt före ett omtag'
    if namn == 'ateljestarter':
        return 'prototyper och kandidater', 'startjournalen för de gamla körningarna'
    if namn == 'arbetsyta':
        return 'designomdömen', 'arbetsytans meddelanden om de gamla kandidaterna'
    return 'okänt ursprung', 'inte kundens fakta eller material enligt reglerna; arkiveras och redovisas'


def kundernas_slag(namn):
    if namn in ('sajt', 'startsida-ersatt'):
        return 'genererade sidor', 'sajten och de ersatta startsidorna ur de gamla körningarna; görs om ur mallen'
    if namn == 'kandidater':
        return 'prototyper och kandidater', 'kandidaternas projekt, kod, bilder och förhandsvisningar'
    if namn == 'atelje':
        return 'prototyper och kandidater', 'körningarnas slutposter'
    if namn in ('DOM.json', 'RAPPORT.md', 'rapporter', 'prov', 'granskning'):
        return 'designomdömen', 'domar, rapporter och prov över gamla byggen'
    return 'okänt ursprung', 'inte leveransens identitet eller ett lås; arkiveras och redovisas'


def kalla(root, post):
    return Path(post['absolut']) if post.get('absolut') else Path(root) / post['sokvag']


def filer(p):
    """(relativ väg, sha256 eller 'lank:<mål>') för varje fil under p, utan att följa länkar."""
    p = Path(p)
    if p.is_symlink() or p.is_file():
        return [('', 'lank:' + os.readlink(p) if p.is_symlink() else sha256(p))]
    ut = []
    for r, ds, fs in os.walk(p):
        ds.sort()
        for n in sorted(fs) + [d for d in ds if os.path.islink(os.path.join(r, d))]:
            fp = Path(r) / n
            rel = str(fp.relative_to(p))
            ut.append((rel, 'lank:' + os.readlink(fp) if fp.is_symlink() else sha256(fp)))
    return ut


def sha256(f):
    h = hashlib.sha256()
    with open(f, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def storlek(p):
    p = Path(p)
    if p.is_symlink():
        return 0
    if p.is_file():
        return p.stat().st_size
    t = 0
    for r, _ds, fs in os.walk(p):
        for n in fs:
            fp = os.path.join(r, n)
            if not os.path.islink(fp):
                try:
                    t += os.path.getsize(fp)
                except OSError:
                    pass
    return t


def inventera(root=None, med_tmp=False):
    root = Path(root or ROOT)
    poster, bevaras, oklassat = klassa(root, med_tmp)
    for p in poster:
        p['bytes'] = storlek(kalla(root, p))
    return {'namn': NAMN, 'tid': nu(), 'arkiv': str(ARKIV), 'poster': poster, 'bevaras': bevaras, 'oklassat': oklassat,
            'summa_bytes': sum(p['bytes'] for p in poster)}


def arkivera(root=None, arkiv=None, brytpunkt=None, commit=None, med_tmp=False):
    """Flyttar varje post till arkivet och prövar sha256 före och efter. Ger manifestet; en post vars prövning faller
    flyttas tillbaka och står med felet."""
    root, arkiv = Path(root or ROOT), Path(arkiv or ARKIV)
    if root.resolve() in arkiv.resolve().parents or arkiv.resolve() == root.resolve():
        raise ValueError('arkivet måste ligga utanför repot: %s' % arkiv)
    man = inventera(root, med_tmp)
    man.update(brytpunkt=brytpunkt or nu(), commit=commit, arkiv=str(arkiv), metod='flytt inom samma volym, sha256 före och efter')
    arkiv.mkdir(parents=True, exist_ok=True)
    os.chmod(arkiv, stat.S_IRWXU)
    alla_hashar = set()
    with open(arkiv / 'SHA256SUMS', 'a', encoding='utf-8') as summor:
        for p in man['poster']:
            k = kalla(root, p)
            mal = arkiv / p['sokvag']
            if mal.exists() or mal.is_symlink():
                p['fel'] = 'målet finns redan i arkivet: %s' % mal
                continue
            t0 = time.monotonic()
            fore = filer(k)
            mal.parent.mkdir(parents=True, exist_ok=True)
            os.rename(k, mal)
            efter = filer(mal)
            if fore != efter:
                os.rename(mal, k)
                p['fel'] = 'sha256 skilde sig efter flytten; posten är tillbakaflyttad'
                continue
            p.update(filer=len(fore), verifierad=True, sekunder=round(time.monotonic() - t0, 1), arkiverad=nu())
            for rel, h in fore:
                summor.write('%s  %s\n' % (h, (p['sokvag'] + ('/' + rel if rel else ''))))
                if not h.startswith('lank:') and '/node_modules/' not in '/%s/' % rel:
                    alla_hashar.add(h)
    for rel, (kategori, skal) in GIT_POSTER.items():  # en kopia av den spårade filen; själva borttagningen är en commit
        f = root / rel
        if f.is_file() and not f.is_symlink() and not (arkiv / 'git' / rel).exists():
            (arkiv / 'git' / rel).parent.mkdir(parents=True, exist_ok=True)
            data = f.read_bytes()
            (arkiv / 'git' / rel).write_bytes(data)
            h = hashlib.sha256(data).hexdigest()
            alla_hashar.add(h)
            man['poster'].append({'sokvag': 'git/' + rel, 'kategori': kategori, 'skal': skal + ' (kopia; filen tas ur arbetsträdet i commit)',
                                  'bytes': len(data), 'filer': 1, 'verifierad': hashlib.sha256((arkiv / 'git' / rel).read_bytes()).hexdigest() == h,
                                  'arkiverad': nu()})
            with open(arkiv / 'SHA256SUMS', 'a', encoding='utf-8') as summor:
                summor.write('%s  git/%s\n' % (h, rel))
    (arkiv / 'MANIFEST.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (arkiv / 'LASMIG.md').write_text(LASMIG % {'namn': NAMN, 'tid': man['tid'], 'brytpunkt': man['brytpunkt'], 'commit': commit or '–'},
                                     encoding='utf-8')
    reg = root / REGISTER
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(json.dumps({k_: man[k_] for k_ in ('namn', 'tid', 'brytpunkt', 'commit', 'arkiv', 'metod', 'summa_bytes')}
                              | {'poster': [{k_: p.get(k_) for k_ in ('sokvag', 'kategori', 'skal', 'bytes', 'filer', 'verifierad', 'fel')}
                                            for p in man['poster']]}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gamla = set((root / HASHAR).read_text(encoding='utf-8').split()) if (root / HASHAR).is_file() else set()
    (root / HASHAR).write_text(''.join(h + '\n' for h in sorted(gamla | alla_hashar)), encoding='utf-8')
    return man


LASMIG = """# %(namn)s — återställningsarkivet

Den rena designstarten (ägarens uppdrag 2026-10-09 ~17:53Z). Arkiverat %(tid)s; brytpunkten %(brytpunkt)s; repots commit
%(commit)s. Allt här är gammalt designmaterial som tagits ur den aktiva miljön: det styr inga nya designsessioner och
verifierar inte den nya metoden.

- MANIFEST.json: varje post med kategori, skäl, storlek och antal filer.
- SHA256SUMS: varje fils sha256 med sin väg relativt repots rot (tmp/ för flödets tempkataloger).
- Återställ en post: `.venv/bin/python kontroller/ren_designstart.py --aterstall <sökväg>` från repots rot.
- Gamla externa referenser återanvänds bara efter ett nytt uttryckligt urval för ett aktuellt uppdrag; gamla
  kommentarer om hur de ska tillämpas följer inte med.
"""


def register(root=None):
    f = Path(root or ROOT) / REGISTER
    try:
        return json.loads(f.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def prova(root=None):
    """Vakten: fynd när arkiverat material kommit tillbaka i den aktiva miljön. En post som finns igen räknas bara när den
    innehåller en fil med samma sha256 som en arkiverad fil (utom mallens egna filer och node_modules), eller när den
    skapats före brytpunkten; en ny körnings sajt ur mallen är nytt material. Dessutom: inga länkar in i arkivet, inget
    arkiv inne i repot, ingen kalibrering eller visuell-niva.md, och LARDOMAR.md utan domar från före brytpunkten."""
    root = Path(root or ROOT)
    reg = register(root)
    ut = []
    if not reg:
        return [{'vad': 'registret saknas', 'detalj': 'ingen ren designstart registrerad i %s' % REGISTER}]
    arkiv = Path(reg.get('arkiv') or ARKIV)
    try:
        if root.resolve() in arkiv.resolve().parents:
            ut.append({'vad': 'arkivet ligger i repot', 'detalj': str(arkiv)})
    except OSError:
        pass
    hashar = set()
    try:
        hashar = set((root / HASHAR).read_text(encoding='utf-8').split())
    except OSError:
        ut.append({'vad': 'hashlistan saknas', 'detalj': str(HASHAR)})
    mall = set()
    mrot = root / 'mall' / 'astro'
    if mrot.is_dir():
        for r, ds, fs in os.walk(mrot):
            ds[:] = [d for d in ds if d != 'node_modules']
            mall.update(sha256(Path(r) / n) for n in fs if not os.path.islink(os.path.join(r, n)))
    bryt = reg.get('brytpunkt') or ''
    for p in reg.get('poster') or []:
        if p.get('fel') or not p.get('verifierad') or str(p.get('sokvag', '')).startswith(('tmp/', 'git/')):
            continue
        k = root / p['sokvag']
        if not (k.exists() or k.is_symlink()):
            continue
        skapad = datetime.fromtimestamp(k.lstat().st_birthtime if hasattr(k.lstat(), 'st_birthtime') else k.lstat().st_ctime,
                                        timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if skapad < bryt:
            ut.append({'vad': 'arkiverad post finns kvar', 'detalj': '%s (skapad %s, före brytpunkten %s)' % (p['sokvag'], skapad, bryt)})
            continue
        for rel, h in filer(k):
            if '/node_modules/' in '/%s/' % rel or h.startswith('lank:'):
                continue
            if h in hashar and h not in mall:
                ut.append({'vad': 'arkiverat material har kommit tillbaka', 'detalj': '%s/%s' % (p['sokvag'], rel)})
                break
    for topp in ('underlag', 'kunder'):
        d = root / topp
        if not d.is_dir():
            continue
        for r, ds, fs in os.walk(d):
            ds[:] = [x for x in ds if x != 'node_modules']
            for n in ds + fs:
                fp = Path(r) / n
                if fp.is_symlink():
                    try:
                        mal = (fp.parent / os.readlink(fp)).resolve()
                    except OSError:
                        continue
                    if mal == arkiv.resolve() or arkiv.resolve() in mal.parents:
                        ut.append({'vad': 'länk in i arkivet', 'detalj': str(fp.relative_to(root))})
    for rel in GIT_POSTER:  # en spårad fil i sin gamla version (den finns i git-historiken och i arkivet, aldrig i arbetsträdet)
        f = root / rel
        if f.is_file() and not f.is_symlink() and sha256(f) in hashar:
            ut.append({'vad': 'en gammal version är tillbaka i arbetsträdet', 'detalj': rel})
    try:
        lar = (root / 'LARDOMAR.md').read_text(encoding='utf-8')
        gamla = [m.group(0) for m in re.finditer(r'^## (?:L\d+|AB|Kalibrering) · (\d{4}-\d{2}-\d{2})', lar, re.M) if m.group(1) < bryt[:10]]
        if gamla:
            ut.append({'vad': 'domar från före brytpunkten i LARDOMAR.md', 'detalj': ', '.join(gamla[:4])})
    except OSError:
        pass
    return ut


def aterstall(sokvag, root=None):
    root = Path(root or ROOT)
    reg = register(root) or {}
    arkiv = Path(reg.get('arkiv') or ARKIV)
    p = next((x for x in reg.get('poster') or [] if x.get('sokvag') == sokvag), None)
    if not p:
        raise ValueError('%s finns inte i registret' % sokvag)
    mal = (TMP / sokvag[4:]) if sokvag.startswith('tmp/') else root / sokvag
    if mal.exists() or mal.is_symlink():
        raise ValueError('%s finns redan i den aktiva miljön; flytta undan den först' % sokvag)
    mal.parent.mkdir(parents=True, exist_ok=True)
    os.rename(arkiv / sokvag, mal)
    return mal


def main(argv=None):
    a = argparse.ArgumentParser(prog='ren_designstart', description=__doc__.split('\n\n')[0])
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument('--inventera', action='store_true')
    g.add_argument('--arkivera', action='store_true')
    g.add_argument('--prova', action='store_true')
    g.add_argument('--aterstall', metavar='SÖKVÄG')
    a.add_argument('--ja', action='store_true', help='bekräftar arkiveringen')
    a.add_argument('--rot', help='repots rot med underlag/ och kunder/ (standard: det här repot)')
    a.add_argument('--brytpunkt')
    a.add_argument('--commit')
    x = a.parse_args(argv)
    if x.inventera:
        man = inventera(x.rot, med_tmp=True)
        for p in man['poster']:
            print('arkiveras  %-70s %9.1f MB  %s: %s' % (p['sokvag'], p['bytes'] / 1e6, p['kategori'], p['skal']))
        for b in man['bevaras']:
            print('bevaras    %-70s %s' % (b['sokvag'], b['skal']))
        for o in man['oklassat']:
            print('oklassat   %s (rörs inte)' % o)
        print('%d poster, %.1f GB att arkivera till %s' % (len(man['poster']), man['summa_bytes'] / 1e9, man['arkiv']))
        return 0
    if x.arkivera:
        if not x.ja:
            print('arkiveringen kräver --ja (kör --inventera först)')
            return 2
        man = arkivera(x.rot, brytpunkt=x.brytpunkt, commit=x.commit, med_tmp=True)
        fel = [p for p in man['poster'] if p.get('fel')]
        for p in man['poster']:
            print('%s %s (%s filer, %.1f MB, %s s)%s' % ('FEL' if p.get('fel') else 'ok ', p['sokvag'], p.get('filer', '–'),
                                                       p['bytes'] / 1e6, p.get('sekunder', '–'), ': ' + p['fel'] if p.get('fel') else ''))
        print('%d av %d poster arkiverade och verifierade i %s' % (len(man['poster']) - len(fel), len(man['poster']), man['arkiv']))
        return 1 if fel else 0
    if x.prova:
        fynd = prova(x.rot)
        for f in fynd:
            print('%s: %s' % (f['vad'], f['detalj']))
        print('%d fynd' % len(fynd))
        return 1 if fynd else 0
    print(aterstall(x.aterstall, x.rot))
    return 0


if __name__ == '__main__':
    sys.exit(main())
