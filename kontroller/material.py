#!/usr/bin/env python3
"""material.py — bild- och videomaterialsteget (ägarens uppdrag 2026-10-07, punkt 5, och 2026-10-08, 2D): visuellt uppdrag →
generation eller redigering → versionshanterad tillgång → webboptimering → faktisk användning.

Mekaniken byggs nu, kontona senare (ägarens beslut 2026-10-07): Higgsfield, Nano Banana (Gemini) och Seedance är
leverantörsgränssnitt som kräver en nyckel i ~/.nortropic-hemligheter/webb-pro/<leverantör>.env; utan den står tillgången
som saknar_konto, och inget anrop görs. Med nyckel står den som fel tills anropet införts och provats mot ett riktigt konto
(status 'anrop ej infört'): ingen extern åtkomst låtsas. Attrappen (stubb) ger en tydligt märkt platshållare (SVG) för
mekanikens prov och får aldrig användas i en sida. En tillgång som ägaren genererat i leverantörens egen tjänst importeras
med --fil (källan och rättigheterna skrivs då in). Ett koncept ur canvas-design registreras som tillgång med --canvas.

Registret: underlag/<slug>/material/MATERIAL.json (privat). Varje tillgång: id, uppdrag, typ (bild|video), roll
(illustrativ|koncept; aldrig verksamhet: materialet påstår aldrig att det visar kundens verkliga verksamhet,
kunskap/bild.md), leverantör, status (stubb|genererad|saknar_konto|fel), versioner (varje generation en ny version
under material/<id>/vNN.<ext>; inget skrivs över), prompt, källa, rättigheter, webb (bilder: astro:assets gör format
och bredder vid bygget; video: posterbild, mobilvariant och reducerad rörelse som poster) och anvand (kandidat, plats, tid).
Användningen lägger filen i kandidatens projekt under src/assets/material/ och en rad i kandidatens material/MATERIAL.md
med Egen nej och påstår verksamhet nej; atelje.egna_bilder tar aldrig med den.

    material.py <slug> --bestall "<uppdrag>" [--typ bild|video] [--leverantor stubb|higgsfield|nano-banana|seedance] [--igen <id>]
    material.py <slug> --fil <väg> --leverantor higgsfield --kalla "<var>" --rattigheter "<vad>" --bestall "<uppdrag>" [--typ video]
    material.py <slug> --canvas <png|pdf> --kandidat k01 --bestall "<vad konceptet visar>"
    material.py <slug> --anvand <id> --kandidat k01 --plats hero [--poster <bild-id>]
    material.py <slug> --kandidat k01 --anvandning   # vad som är kopierat, importerat i källan och renderat i bygget
    material.py <slug> --visa

Skaparens session når verktyget bara kandidatavgränsat (kompetens.VERKTYG['material'], R05 i
GR-20261008-06af6ff-omgranskning-codex): kommandot börjar med `<slug> --kandidat <id>`, --kandidat får stå en gång, och en
fil som importeras (--fil, --canvas) måste ligga i kandidatens egen katalog under ateljén; allt annat vägras.
Kandidatgränsen prövas på de slutligt tolkade argumenten (N02 i GR-20261009-natt-omgranskning-codex): inga förkortade
flaggor (--kand tolkades som --kandidat), och den kandidat som kommandot börjar med är den som verktyget arbetar för.
Ägarskapet: en tillgång som en kandidat skapat (--canvas, --fil eller --bestall med --kandidat) är kandidatens privata
(fältet kandidat); en tillgång som ägaren lagt in utan --kandidat är uttryckligen gemensamt kundmaterial (gemensam: true;
en äldre rad utan kandidat räknas så). Med --kandidat ser --visa bara kandidatens egna och de gemensamma, och användningen,
posterbilden och en ny version (--igen) vägras för en annan kandidats tillgång, med samma besked som för en okänd; en ny
version av gemensamt material görs bara av ägaren. Registret och tillgångarnas filer nekas skaparens Read
(kandidater.andra_nekas): verktyget är vägen dit. Tre nivåer
hålls isär: lokal import och beredning (registret), leverantörsanrop (inte infört; konto krävs) och en tillgång som
faktiskt används i renderingen (anvandning: kopierad, importerad i källan, med i bygget).
Slutkod 0 när det begärda gjordes, 1 vid ett hinder (står i svaret), 2 vid ogiltigt anrop.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402

HEM = Path.home() / '.nortropic-hemligheter' / 'webb-pro'
LEVERANTORER = {
    'stubb': {'env': None, 'typer': ('bild', 'video'), 'namn': 'attrapp (mekanikprov)'},
    'higgsfield': {'env': 'higgsfield.env', 'var': 'HIGGSFIELD_API_KEY', 'typer': ('bild', 'video'), 'namn': 'Higgsfield'},
    'nano-banana': {'env': 'gemini.env', 'var': 'GEMINI_API_KEY', 'typer': ('bild',), 'namn': 'Nano Banana (Gemini)'},
    'seedance': {'env': 'seedance.env', 'var': 'SEEDANCE_API_KEY', 'typer': ('video',), 'namn': 'Seedance'},
    'canvas-design': {'env': None, 'typer': ('bild',), 'namn': 'canvas-design (skillen)'},
}
ROLLER = ('illustrativ', 'koncept')
TYPER = ('bild', 'video')
BILDFORMAT = ('.png', '.jpg', '.jpeg', '.webp', '.avif', '.svg', '.pdf')
VIDEOFORMAT = ('.mp4', '.webm', '.mov')
nu = atelje.nu


class Hinder(Exception):
    pass


def katalog(slug):
    return atelje.UNDERLAG / slug / 'material'


def registerfil(slug):
    return katalog(slug) / 'MATERIAL.json'


def las(slug):
    p = registerfil(slug)
    try:
        d = json.loads(p.read_text(encoding='utf-8')) if p.is_file() and not p.is_symlink() else None
    except (OSError, ValueError):
        d = None
    return d if isinstance(d, dict) and isinstance(d.get('tillgangar'), dict) else {'schema': 1, 'slug': slug, 'tillgangar': {}}


def skriv(slug, d):
    katalog(slug).mkdir(parents=True, exist_ok=True)
    d['uppdaterad'] = nu()
    atelje.skriv_json_atomiskt(registerfil(slug), d)


def tillhor(t, kandidat):
    """Får kandidaten se och använda tillgången? Kandidatens egen eller uttryckligen gemensam; utan kandidat (ägaren) allt."""
    if not kandidat:
        return True
    if not isinstance(t, dict):
        return False
    agare = t.get('kandidat')
    return agare == kandidat or (not agare and t.get('gemensam', True) is not False)


def synliga(d, kandidat):
    """Registret som kandidaten får se: bara egna och gemensamma tillgångar, och i de gemensamma bara kandidatens egen
    användning (var en annan kandidat lagt materialet är dess val; ägaren utan kandidat ser allt)."""
    if not kandidat:
        return d
    return dict(d, tillgangar={k: dict(t, anvand=[a for a in t.get('anvand') or [] if a.get('kandidat') == kandidat])
                               for k, t in d['tillgangar'].items() if tillhor(t, kandidat)})


def nytt_id(d):
    n = 1 + max([int(k[1:]) for k in d['tillgangar'] if re.fullmatch(r'm\d{3,}', k)] or [0])
    return 'm%03d' % n


def nyckel_finns(leverantor):
    lev = LEVERANTORER[leverantor]
    if not lev.get('env'):
        return True
    p = HEM / lev['env']
    try:
        return any(rad.startswith(lev['var'] + '=') and rad.split('=', 1)[1].strip() for rad in p.read_text(encoding='utf-8').splitlines())
    except OSError:
        return False


def version_fil(slug, tid, n, ext):
    d = katalog(slug) / tid['id']
    d.mkdir(parents=True, exist_ok=True)
    return d / ('v%02d%s' % (n, ext))


def stubb_svg(uppdrag, typ):
    text = re.sub(r'[<>&"]', '', uppdrag)[:120]
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-label="stubb">'
            '<rect width="1200" height="675" fill="#e8e3da"/><text x="60" y="120" font-family="sans-serif" font-size="40" fill="#5a4a3a">'
            'STUBB — mekanikprov, inget material (%s)</text><text x="60" y="200" font-family="sans-serif" font-size="26" fill="#5a4a3a">%s</text></svg>\n'
            % (typ, text))


def webb(typ, ext):
    """Webboptimeringens kontrakt: bilder får format och bredder av astro:assets vid bygget (kunskap/bild.md); video kräver
    posterbild och mobilvariant, och visas som poster när besökaren bett om mindre rörelse. Utan ffmpeg görs ingen
    omkodning här: posterbilden är en egen bildtillgång, mobilvarianten kommer från leverantören."""
    if typ == 'bild':
        return {'optimering': 'astro:assets vid bygget (format och bredder); SVG och PDF läggs som de är' if ext in ('.svg', '.pdf') else 'astro:assets vid bygget (format och bredder)',
                'kalla_format': ext, 'hinder': []}
    return {'optimering': 'ingen omkodning i flödet (ffmpeg saknas): posterbild som egen bildtillgång, mobilvariant från leverantören',
            'kalla_format': ext, 'poster': None, 'mobil': None, 'reducerad_rorelse': 'posterbilden visas; ingen autouppspelning',
            'hinder': ['posterbild krävs före användning (--poster <bild-id>)', 'mobilvariant saknas: leverantörens eller egen']}


def bestall(slug, uppdrag, typ='bild', leverantor='stubb', roll='illustrativ', igen=None, prompt=None, kandidat=None):
    """Ett visuellt uppdrag blir en tillgång (ny, eller en ny version av igen) hos leverantören. Ger tillgången. kandidat:
    kandidatens privata tillgång, och en ny version bara av kandidatens egen (N02); utan kandidat ägarens, gemensam."""
    if typ not in TYPER or roll not in ROLLER or leverantor not in LEVERANTORER:
        raise ValueError('typ, roll eller leverantör är okänd')
    if typ not in LEVERANTORER[leverantor]['typer']:
        raise ValueError('%s gör inte %s' % (leverantor, typ))
    d = las(slug)
    if igen:
        t = d['tillgangar'].get(igen)
        if not t or (kandidat and t.get('kandidat') != kandidat):  # en annan kandidats, eller gemensamt material: ägarens
            raise ValueError('okänd tillgång %s' % igen + (' för kandidaten %s' % kandidat if kandidat else ''))
    else:
        t = {'id': nytt_id(d), 'skapad': nu(), 'versioner': [], 'kandidat': kandidat, 'gemensam': not kandidat}
    t.update({'uppdrag': str(uppdrag)[:1000], 'typ': typ, 'roll': roll, 'leverantor': leverantor, 'prompt': (prompt or uppdrag)[:2000],
              'pastar_verksamhet': False})
    n = len(t['versioner']) + 1
    v = {'version': n, 'tid': nu(), 'leverantor': leverantor}
    if leverantor == 'stubb':
        f = version_fil(slug, t, n, '.svg' if typ == 'bild' else '.svg')
        f.write_text(stubb_svg(uppdrag, typ), encoding='utf-8')
        v.update(status='stubb', fil='material/%s/%s' % (t['id'], f.name), kalla='attrapp: kontroller/material.py (mekanikprov)', rattigheter='inget material')
    elif not nyckel_finns(leverantor):
        v.update(status='saknar_konto', fil=None, hinder='%s kräver nyckeln %s i %s; kontot är ägarens beslut (2026-10-07: mekanik nu, konto senare)' % (
            LEVERANTORER[leverantor]['namn'], LEVERANTORER[leverantor]['var'], HEM / LEVERANTORER[leverantor]['env']))
    else:
        v.update(status='fel', fil=None, hinder='%s: anropet är inte infört; det införs och provas när kontot finns (ingen extern åtkomst låtsas)' % LEVERANTORER[leverantor]['namn'])
    t['versioner'].append(v)
    t['status'] = v['status']
    t['webb'] = webb(typ, Path(v['fil']).suffix if v.get('fil') else '')
    d['tillgangar'][t['id']] = t
    skriv(slug, d)
    return t


def importera(slug, fil, leverantor, uppdrag, kalla, rattigheter, typ=None, roll='illustrativ', kandidat=None):
    """En färdig tillgång (genererad i leverantörens egen tjänst, eller ett koncept ur canvas-design) blir en versionerad
    tillgång med källa och rättigheter; filen kopieras, originalet rörs inte."""
    p = Path(fil)
    if not p.is_file() or p.is_symlink():
        raise ValueError('filen finns inte: %s' % fil)
    ext = p.suffix.lower()
    typ = typ or ('video' if ext in VIDEOFORMAT else 'bild')
    if (typ == 'bild' and ext not in BILDFORMAT) or (typ == 'video' and ext not in VIDEOFORMAT):
        raise ValueError('filformatet %s passar inte typen %s' % (ext, typ))
    if leverantor not in LEVERANTORER or roll not in ROLLER:
        raise ValueError('okänd leverantör eller roll')
    if typ not in LEVERANTORER[leverantor]['typer']:
        raise ValueError('%s gör inte %s' % (leverantor, typ))
    d = las(slug)
    t = {'id': nytt_id(d), 'skapad': nu(), 'versioner': [], 'uppdrag': str(uppdrag)[:1000], 'typ': typ, 'roll': roll, 'leverantor': leverantor,
         'prompt': None, 'pastar_verksamhet': False, 'kandidat': kandidat, 'gemensam': not kandidat}
    f = version_fil(slug, t, 1, ext)
    shutil.copyfile(p, f)
    v = {'version': 1, 'tid': nu(), 'leverantor': leverantor, 'status': 'genererad', 'fil': 'material/%s/%s' % (t['id'], f.name),
         'kalla': str(kalla)[:300], 'rattigheter': str(rattigheter)[:300], 'importerad_fran': p.name}
    t['versioner'].append(v)
    t['status'] = 'genererad'
    t['webb'] = webb(typ, ext)
    d['tillgangar'][t['id']] = t
    skriv(slug, d)
    return t


def canvas(slug, fil, kandidat, uppdrag):
    """Ett koncept ur canvas-design (PNG/PDF i kandidatens konceptkatalog) som tillgång: roll koncept, källa skillens commit
    ur KALLA.md (kunskap/metodkarta.md, Grafiska koncept ur canvas-design)."""
    commit = 'okänd'
    try:
        m = re.search(r'\b[0-9a-f]{7,40}\b', (atelje.ROOT / '.claude' / 'skills' / 'canvas-design' / 'KALLA.md').read_text(encoding='utf-8'))
        commit = m.group(0)[:12] if m else commit
    except OSError:
        pass
    return importera(slug, fil, 'canvas-design', uppdrag, 'canvas-design @ %s, kandidat %s' % (commit, kandidat), 'Apache-2.0 (skillen); konceptet är Nortropics, typsnitten OFL-1.1',
                     typ='bild', roll='koncept', kandidat=kandidat)


def anvand(slug, tid, kandidat, plats, poster=None):
    """Den faktiska användningen: tillgångens senaste version in i kandidatens projekt (src/assets/material/) och en rad i
    kandidatens material/MATERIAL.md med Egen nej och påstår verksamhet nej. En stubb, en tillgång utan konto och en video
    utan posterbild används aldrig. En annan kandidats tillgång, också som posterbild, är okänd för kandidaten (N02).
    Ger {'ok', 'fil' | 'hinder'}."""
    import kandidater
    d = las(slug)
    t = d['tillgangar'].get(tid)
    if not t or not tillhor(t, kandidat):
        return {'ok': False, 'hinder': 'okänd tillgång %s för kandidaten %s' % (tid, kandidat)}
    v = t['versioner'][-1] if t.get('versioner') else {}
    if v.get('status') != 'genererad' or not v.get('fil'):
        return {'ok': False, 'hinder': 'tillgången %s är %s (%s) och används inte' % (tid, v.get('status') or 'utan version', v.get('hinder') or 'bara genererat material används')}
    if not re.fullmatch(r'k\d\d', kandidat or '') or not re.fullmatch(r'[a-z0-9-]{2,40}', plats or ''):
        return {'ok': False, 'hinder': 'kandidat (kNN) och plats (små bokstäver, siffror, bindestreck) behövs'}
    posterrad = ''
    if t['typ'] == 'video':
        p = d['tillgangar'].get(poster or '')
        p = p if tillhor(p, kandidat) else None
        pv = p['versioner'][-1] if p and p.get('versioner') else {}
        if not p or p.get('typ') != 'bild' or pv.get('status') != 'genererad':
            return {'ok': False, 'hinder': 'en video kräver en genererad posterbild (--poster <bild-id>); den visas också vid reducerad rörelse'}
        t['webb']['poster'] = poster
        posterrad = ' · poster %s' % poster
    kalla = katalog(slug) / Path(v['fil']).relative_to('material')
    sajt = kandidater.ksajt(slug, kandidat)
    if not (sajt / 'src').is_dir():
        return {'ok': False, 'hinder': 'kandidatens projekt saknar src/: %s' % sajt}
    mal = sajt / 'src' / 'assets' / 'material'
    mal.mkdir(parents=True, exist_ok=True)
    namn = '%s__%s-v%02d%s' % (plats, tid, v['version'], Path(v['fil']).suffix)
    shutil.copyfile(kalla, mal / namn)
    if t['typ'] == 'video' and poster:
        pv = d['tillgangar'][poster]['versioner'][-1]
        shutil.copyfile(katalog(slug) / Path(pv['fil']).relative_to('material'), mal / ('%s__%s-poster%s' % (plats, tid, Path(pv['fil']).suffix)))
    md = kandidater.kdir(slug, kandidat) / 'material' / 'MATERIAL.md'
    md.parent.mkdir(parents=True, exist_ok=True)
    if not md.is_file():
        md.write_text('# Material i kandidaten (materialsteget, kontroller/material.py)\n\nIllustrativt material och koncept: aldrig bilder som påstår sig visa verksamheten (kunskap/bild.md).\n\n'
                      '| fil | roll | typ | leverantör | version | källa | rättigheter | plats | Egen | påstår verksamhet | reducerad rörelse |\n|---|---|---|---|---|---|---|---|---|---|---|\n', encoding='utf-8')
    with open(md, 'a', encoding='utf-8') as fh:
        fh.write('| %s | %s | %s | %s | v%02d | %s | %s | %s | nej | nej | %s |\n' % (
            namn, t['roll'], t['typ'], LEVERANTORER[t['leverantor']]['namn'], v['version'], v.get('kalla', ''), v.get('rattigheter', ''), plats,
            ('posterbilden visas; ingen autouppspelning' + posterrad) if t['typ'] == 'video' else 'gäller inte'))
    t.setdefault('anvand', []).append({'kandidat': kandidat, 'plats': plats, 'fil': 'src/assets/material/' + namn, 'version': v['version'], 'tid': nu()})
    skriv(slug, d)
    return {'ok': True, 'fil': 'src/assets/material/' + namn, 'md': str(md)}


def i_kandidaten(slug, kid, fil):
    """Filen ligger i kandidatens egen katalog under ateljén (aldrig en länk, aldrig utanför): skaparens import är
    kandidatavgränsad. Ger den upplösta vägen eller ValueError."""
    import kandidater
    rot = kandidater.kdir(slug, kid).resolve()
    p = Path(fil)
    p = (atelje.ROOT / p) if not p.is_absolute() else p
    if p.is_symlink() or not p.resolve().is_relative_to(rot):
        raise ValueError('filen ligger utanför kandidatens katalog (%s): skaparen importerar bara sitt eget material' % kandidater.rel(rot))
    return p.resolve()


def anvandning(slug, kid):
    """Varje tillgång som lagts i kandidaten, i tre nivåer: kopierad (filen finns i src/assets/material/), importerad i
    källan (en annan fil i src/ nämner filnamnet) och renderad (byggets dist/ har en fil eller en HTML-referens som bär
    filens namn; astro:assets behåller namnet i den hashade filen). Att filen kopierats bevisar inte att den används."""
    import kandidater
    sajt = kandidater.ksajt(slug, kid)
    src, dist = sajt / 'src', sajt / 'dist'
    kallor = [p for p in src.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix in ('.astro', '.md', '.mdx', '.ts', '.js', '.jsx', '.tsx', '.css')
              and 'assets' not in p.relative_to(src).parts[:1]] if src.is_dir() else []
    texter = {p: p.read_text(encoding='utf-8', errors='replace') for p in kallor}
    html = [p.read_text(encoding='utf-8', errors='replace') for p in dist.rglob('*.html')] if dist.is_dir() else []
    distfiler = [p.name for p in dist.rglob('*') if p.is_file()] if dist.is_dir() else []
    ut = []
    for t in las(slug)['tillgangar'].values():
        for a in t.get('anvand') or []:
            if a.get('kandidat') != kid:
                continue
            namn = Path(a['fil']).name
            stam = Path(namn).stem
            ut.append({'id': t['id'], 'fil': a['fil'], 'plats': a.get('plats'), 'version': a.get('version'), 'roll': t.get('roll'),
                       'kopierad': (sajt / a['fil']).is_file(),
                       'i_kallan': any(namn in x for x in texter.values()),
                       'renderad': dist.is_dir() and (any(f.startswith(stam + '.') or f.startswith(stam + '_') for f in distfiler)
                                                      or any(stam in h for h in html))})
    return ut


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv.count('--kandidat') > 1 or sum(1 for x in argv if x.startswith('--kandidat=')) + argv.count('--kandidat') > 1:
        print(json.dumps({'ok': False, 'hinder': '--kandidat får stå en gång'}, ensure_ascii=False))
        return 2
    # N02: inga förkortningar (argparse tolkade --kand som --kandidat), och kandidaten i kommandots början (skaparens
    # tillåtna form `<slug> --kandidat <id> …`) prövas mot den slutligt tolkade
    bunden = argv[2] if len(argv) > 2 and argv[1] == '--kandidat' else None
    p = argparse.ArgumentParser(prog='material', description=__doc__.split('\n\n')[0], allow_abbrev=False)
    p.add_argument('slug')
    p.add_argument('--bestall', help='det visuella uppdraget')
    p.add_argument('--typ', choices=TYPER, default=None)
    p.add_argument('--roll', choices=ROLLER, default='illustrativ')
    p.add_argument('--leverantor', choices=sorted(LEVERANTORER), default='stubb')
    p.add_argument('--igen', help='ny version av en befintlig tillgång')
    p.add_argument('--fil', help='importera en färdig tillgång')
    p.add_argument('--kalla', default='')
    p.add_argument('--rattigheter', default='')
    p.add_argument('--canvas', help='ett koncept ur canvas-design (png/pdf)')
    p.add_argument('--kandidat')
    p.add_argument('--anvand', help='tillgångens id')
    p.add_argument('--plats')
    p.add_argument('--poster')
    p.add_argument('--visa', action='store_true')
    p.add_argument('--anvandning', action='store_true')
    try:
        a = p.parse_args(argv)
    except SystemExit:
        return 2
    if not atelje.SLUG.match(a.slug):
        print('ogiltig slug', file=sys.stderr)
        return 2
    if bunden is not None and a.kandidat != bunden:
        print(json.dumps({'ok': False, 'hinder': 'kandidaten ändrades efter kommandots början (%s); verktyget arbetar bara för den' % bunden}, ensure_ascii=False))
        return 2
    try:
        if a.kandidat is not None and not re.fullmatch(r'k\d\d', a.kandidat):
            raise ValueError('kandidaten anges som kNN')
        if a.visa:
            ut = synliga(las(a.slug), a.kandidat)
        elif a.anvandning:
            if not a.kandidat:
                raise ValueError('--anvandning kräver --kandidat')
            ut = {'ok': True, 'anvandning': anvandning(a.slug, a.kandidat)}
        elif a.canvas:
            if not a.kandidat or not a.bestall:
                raise ValueError('--canvas kräver --kandidat och --bestall')
            ut = canvas(a.slug, i_kandidaten(a.slug, a.kandidat, a.canvas), a.kandidat, a.bestall)
        elif a.fil:
            if not a.bestall or not a.kalla or not a.rattigheter:
                raise ValueError('--fil kräver --bestall, --kalla och --rattigheter')
            fil = i_kandidaten(a.slug, a.kandidat, a.fil) if a.kandidat else a.fil  # ägarens import utan --kandidat; skaparens bara ur kandidaten
            ut = importera(a.slug, fil, a.leverantor, a.bestall, a.kalla, a.rattigheter, typ=a.typ, roll=a.roll, kandidat=a.kandidat)
        elif a.anvand:
            ut = anvand(a.slug, a.anvand, a.kandidat, a.plats, a.poster)
        elif a.bestall:
            ut = bestall(a.slug, a.bestall, a.typ or 'bild', a.leverantor, a.roll, a.igen, kandidat=a.kandidat)
        else:
            p.print_usage()
            return 2
    except ValueError as e:
        print(json.dumps({'ok': False, 'hinder': str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0 if ut.get('ok', True) and ut.get('status') not in ('saknar_konto', 'fel') else 1


if __name__ == '__main__':
    sys.exit(main())
