#!/usr/bin/env python3
"""material.py — bild- och videomaterialsteget (ägarens uppdrag 2026-10-07, punkt 5, och 2026-10-08, 2D): visuellt uppdrag →
generation eller redigering → versionshanterad tillgång → webboptimering → faktisk användning.

Beställning läser inga nycklar och gör inga anrop. Higgsfield, Nano Banana (Gemini) och Seedance får ett exakt,
hashbundet uppdrag med status vantar_mandat_konto. Betrodd --generera verkställer det efter uttryckligt
kostnadsmedgivande och rättighetsuppgift, via material_transport.py. API-konto och verkligt prov krävs fortfarande;
ett webbprenumerationskonto är inte ett API-mandat. Attrappen (stubb) ger en tydligt märkt platshållare (SVG) för
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
    material.py <slug> --generera <id> --uppdrag-sha <sha256> --godkann-kostnad --rattigheter "<belägg>"
    material.py <slug> --bestall "<ändringen>" --leverantor nano-banana --fran <id>[@vN]          # redigering av egen bild
    material.py <slug> --bestall "<rörelsen>" --leverantor seedance --typ video --fran <id>[@vN]  # bild till video
    material.py <slug> --ko     # materialkön: det som väntar på mandat, konto eller resultat (verkställer inget)

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
hålls isär: lokal import och beredning (registret), leverantörsanrop (konto och avgränsat mandat krävs) och en tillgång som
faktiskt används i renderingen (anvandning: kopierad, importerad i källan, med i bygget).
Slutkod 0 när det begärda gjordes, 1 vid ett hinder (står i svaret), 2 vid ogiltigt anrop.
"""
import argparse
import contextlib
import fcntl
import functools
import json
import os
import re
import stat
import sys
import threading
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402
import material_transport as transport  # noqa: E402

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
_LAS = threading.RLock()


class Hinder(Exception):
    pass


@contextlib.contextmanager
def _katalog_fd(root, led=(), skapa=False):
    """Bind varje katalogled; varken befintliga länkar eller senare katalogbyten följs."""
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for namn in led:
            if not isinstance(namn, str) or namn in ('', '.', '..') or '/' in namn or '\\' in namn:
                raise ValueError('ogiltigt materialled')
            if skapa:
                try:
                    os.mkdir(namn, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            nxt = os.open(namn, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = nxt
        yield fd
    finally:
        os.close(fd)


def _las_fd(fd, namn, valfri=False):
    try:
        f = os.open(namn, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        if valfri:
            return None
        raise
    with os.fdopen(f, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > transport.MAX_FIL:
            raise ValueError('materialfilen ska vara en vanlig fil utan hårdlänkar inom storleksgränsen')
        data = stream.read(transport.MAX_FIL + 1)
        if len(data) > transport.MAX_FIL:
            raise ValueError('materialfilen är för stor')
        return data


def _las_inom(root, led):
    with _katalog_fd(root, led[:-1]) as fd:
        return _las_fd(fd, led[-1])


def _skriv_fd(fd, namn, data, ersatt=False):
    """Atomiskt byte av en egen vanlig fil, eller exklusiv publicering av en ny version."""
    if '/' in namn or '\\' in namn or namn in ('', '.', '..'):
        raise ValueError('ogiltigt materialfilnamn')
    _las_fd(fd, namn, valfri=True)  # nekar även en befintlig hårdlänk; byte följer aldrig målfilen
    tmp = '.' + namn + '-' + uuid.uuid4().hex + '.tmp'
    f = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    try:
        with os.fdopen(f, 'wb') as out:
            out.write(data); out.flush(); os.fsync(out.fileno())
        if ersatt:
            os.replace(tmp, namn, src_dir_fd=fd, dst_dir_fd=fd)
        else:
            os.link(tmp, namn, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
    finally:
        try:
            os.unlink(tmp, dir_fd=fd)
        except FileNotFoundError:
            pass


def _version_skriv(slug, tid, n, ext, data, aterhamtning=False):
    f = version_fil(slug, tid, n, ext)
    with _katalog_fd(atelje.UNDERLAG, (slug, 'material', tid['id'])) as fd:
        old = _las_fd(fd, f.name, valfri=True)
        if old is not None and aterhamtning and old == data:
            return f
        _skriv_fd(fd, f.name, data)
    return f


def _version_las(slug, tid, v):
    if not re.fullmatch(r'm\d{3,}', tid or '') or type(v.get('version')) is not int:
        raise ValueError('ogiltig materialversion')
    p = Path(v.get('fil') or '')
    if p.parts != ('material', tid, 'v%02d%s' % (v['version'], p.suffix)) or p.suffix not in BILDFORMAT + VIDEOFORMAT:
        raise ValueError('materialfilen tillhör inte den bokförda versionen')
    return _las_inom(atelje.UNDERLAG, (slug, *p.parts))


def katalog(slug):
    if not isinstance(slug, str) or not atelje.SLUG.fullmatch(slug):
        raise ValueError('ogiltig slug')
    root = atelje.UNDERLAG
    for p in (root, root / slug, root / slug / 'material'):
        if p.is_symlink():
            raise ValueError('materialets rot får inte vara en symbolisk länk')
    return root / slug / 'material'


@contextlib.contextmanager
def registerlas(slug):
    """Samma lås vid beställning, import, användning och betrodd generering."""
    with _LAS:
        katalog(slug)
        with _katalog_fd(atelje.UNDERLAG, (slug, 'material'), skapa=True) as kd:
            fd = os.open('.material.las', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=kd)
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError('materiallåset ska vara en vanlig olänkad fil')
                fcntl.flock(fd, fcntl.LOCK_EX)
                yield
            finally:
                os.close(fd)


def last(f):
    @functools.wraps(f)
    def inne(slug, *args, **kwargs):
        with registerlas(slug):
            return f(slug, *args, **kwargs)
    return inne


def registerfil(slug):
    return katalog(slug) / 'MATERIAL.json'


def las(slug):
    p = registerfil(slug)
    if not p.exists() and not p.is_symlink():
        return {'schema': 1, 'slug': slug, 'tillgangar': {}}
    try:
        if p.is_symlink() or not p.is_file():
            raise ValueError()
        d = json.loads(_las_inom(atelje.UNDERLAG, (slug, 'material', 'MATERIAL.json')))
    except (OSError, ValueError):
        raise ValueError('materialregistret kunde inte läsas; inget skrivs över') from None
    if not isinstance(d, dict) or d.get('slug') != slug or not isinstance(d.get('tillgangar'), dict):
        raise ValueError('ogiltigt materialregister; inget skrivs över')
    return d


def skriv(slug, d):
    katalog(slug)
    d['uppdaterad'] = nu()
    with _katalog_fd(atelje.UNDERLAG, (slug, 'material'), skapa=True) as fd:
        _skriv_fd(fd, 'MATERIAL.json', (json.dumps(d, ensure_ascii=False, indent=1) + '\n').encode(), ersatt=True)


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


def las_nyckel(leverantor):
    """Bara den betrodda körvägen når denna läsning. Ingen nyckel återges i kvittot."""
    lev = LEVERANTORER[leverantor]
    p = HEM / lev['env']
    try:
        if p.is_symlink() or HEM.is_symlink() or not stat.S_ISREG(p.lstat().st_mode):
            raise ValueError()
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd) as f:
            if os.fstat(f.fileno()).st_mode & 0o077:
                raise ValueError()
            text = f.read(65537)
        if len(text) > 65536:
            raise ValueError()
        values = [r.split('=', 1)[1].strip().strip('"\'') for r in text.splitlines() if r.startswith(lev['var'] + '=')]
        if len(values) != 1 or not values[0] or re.search(r'[\r\n]', values[0]):
            raise ValueError()
        return values[0]
    except (OSError, UnicodeError, ValueError):
        raise ValueError('leverantörens API-konto saknas eller nyckelfilen är inte privat och läsbar') from None


def version_fil(slug, tid, n, ext):
    if not re.fullmatch(r'm\d{3,}', tid.get('id', '')) or type(n) is not int or n < 1:
        raise ValueError('ogiltig materialidentitet')
    d = katalog(slug) / tid['id']
    if d.is_symlink():
        raise ValueError('tillgångens katalog får inte vara en länk')
    with _katalog_fd(atelje.UNDERLAG, (slug, 'material', tid['id']), skapa=True):
        pass
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


KALLMIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}


def kallbild(slug, d, ref, kandidat):
    """--fran <id>[@vN]: en genererad eller importerad illustrativ version i materialregistret som källbild för redigering
    eller bild till video (ägarens uppdrag 2026-10-07, punkt 5B: Nano Banana → bild → Seedance). Tillåten uppladdning är
    bara registrets egna material (roll illustrativ eller koncept, påstår aldrig verksamheten), som kandidaten själv äger
    eller som är gemensamt; kundens egna bilder står inte i registret och kan aldrig skickas den här vägen. Ger
    identiteten (aldrig bilden) som uppdraget binder med sha256."""
    import hashlib
    m = re.fullmatch(r'(m\d{3,})(?:@v?(\d+))?', ref or '')
    t = d['tillgangar'].get(m.group(1)) if m else None
    if not isinstance(t, dict) or not tillhor(t, kandidat):
        raise ValueError('okänd källbild %s' % ref + (' för kandidaten %s' % kandidat if kandidat else ''))
    if t.get('roll') not in ROLLER or t.get('pastar_verksamhet') is not False or t.get('typ') != 'bild':
        raise ValueError('källbilden måste vara registrets egen illustrativa bild')
    kandidater_ = [v for v in t.get('versioner') or [] if v.get('status') == 'genererad' and v.get('fil')]
    v = next((x for x in kandidater_ if x.get('version') == int(m.group(2))), None) if m.group(2) else (kandidater_[-1] if kandidater_ else None)
    if not v:
        raise ValueError('källbilden %s har ingen färdig version' % ref)
    mime = KALLMIME.get(Path(v['fil']).suffix.lower())
    if not mime:
        raise ValueError('källbilden måste vara PNG, JPEG eller WebP')
    data = _version_las(slug, t['id'], v)
    return {'material': t['id'], 'version': v['version'], 'mime': mime, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def ko(slug, kandidat=None):
    """Materialkön: varje beställd version som väntar på ägarens mandat, ett konto, ett resultat eller en kontroll av ett
    okänt utfall, med exakt uppdragshash. Kön verkställer ingenting: varje generation kräver --generera med hashen,
    kostnadsmedgivandet och rättigheterna (ett mandat gäller en version)."""
    d = las(slug)
    ut = []
    for t in d['tillgangar'].values():
        if not tillhor(t, kandidat):
            continue
        for v in t.get('versioner') or []:
            if v.get('status') in ('vantar_mandat_konto', 'saknar_konto', 'vantar_resultat', 'oklart', 'skickar'):
                job = v.get('bestallning') or {}
                ut.append({'id': t['id'], 'version': v.get('version'), 'status': v.get('status'), 'leverantor': t.get('leverantor'),
                           'modell': job.get('modell'), 'typ': t.get('typ'), 'kandidat': t.get('kandidat'), 'uppdrag': t.get('uppdrag'),
                           'parametrar': job.get('parametrar'), 'kalla_bild': job.get('kalla_bild'), 'uppdrag_sha': v.get('uppdrag_sha'),
                           'hinder': v.get('hinder'), 'tid': v.get('tid')})
    return {'ok': True, 'ko': sorted(ut, key=lambda x: (x.get('tid') or '', x['id']))}


@last
def bestall(slug, uppdrag, typ='bild', leverantor='stubb', roll='illustrativ', igen=None, prompt=None, kandidat=None, modell=None, parametrar=None,
            fran=None):
    """Ett visuellt uppdrag blir en tillgång (ny, eller en ny version av igen) hos leverantören. Ger tillgången. kandidat:
    kandidatens privata tillgång, och en ny version bara av kandidatens egen (N02); utan kandidat ägarens, gemensam.
    fran: en egen bild i registret som källbild (kallbild) för Nano Bananas redigering eller Seedance-videons första ruta."""
    if typ not in TYPER or roll not in ROLLER or leverantor not in LEVERANTORER:
        raise ValueError('typ, roll eller leverantör är okänd')
    if typ not in LEVERANTORER[leverantor]['typer']:
        raise ValueError('%s gör inte %s' % (leverantor, typ))
    if fran and leverantor == 'stubb':
        raise ValueError('attrappen tar ingen källbild')
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
        f = _version_skriv(slug, t, n, '.svg', stubb_svg(uppdrag, typ).encode())
        v.update(status='stubb', fil='material/%s/%s' % (t['id'], f.name), kalla='attrapp: kontroller/material.py (mekanikprov)', rattigheter='inget material')
    else:
        job = transport.uppdrag(leverantor, typ, prompt or uppdrag, modell, parametrar, kallbild(slug, d, fran, kandidat) if fran else None)
        job.update(slug=slug, kandidat=kandidat, id=t['id'], version=n, roll=roll)
        v.update(status='vantar_mandat_konto', fil=None, bestallning=job, uppdrag_sha=transport.sha(job),
                 hinder='beställningen är sparad; betrodd --generera kräver exakt uppdragshash, kostnadsmedgivande, rättigheter och API-konto; inget konto har lästs')
    t['versioner'].append(v)
    t['status'] = v['status']
    t['webb'] = webb(typ, Path(v['fil']).suffix if v.get('fil') else '')
    d['tillgangar'][t['id']] = t
    skriv(slug, d)
    return t


def kundgranser(slug, prompt):
    """Samma identifieringsregler som kundvakten; bara generisk text får skickas, inga kundfiler."""
    import skapande
    import kundvakt
    try:
        forbjudna = skapande.forbjudna_termer(slug, atelje.UNDERLAG)
        if not forbjudna.get('ord') and not forbjudna.get('siffror'):
            raise ValueError()
        uppgifter = kundvakt.underlagets_uppgifter(slug, atelje.UNDERLAG)
        forbjudna['siffror'] |= uppgifter['siffror']
        text = kundvakt.avkoda(prompt)
        if (skapande.namner_kunden(text, forbjudna) or kundvakt.namner_person(text, uppgifter['personer'])
                or kundvakt.namner_person(text, uppgifter['orter']) or skapande.SPARRAD_FORM.search(text)):
            raise ValueError()
    except Exception:
        raise ValueError('kundvakten kunde inte godkänna den utgående materialprompten') from None


def generera(slug, tid, uppdrag_sha, godkann_kostnad=False, rattigheter='', *, kandidat=None, http=None, timeout=180):
    """Betrodd ägaringång, även användbar av en framtida mandatkontrollerad tjänst.

    Kandidatens Bash-form når aldrig denna väg: inget --kandidat och inget NWP_SLUG.
    Exakt uppdragshash + kostnadsmedgivande gäller en version, inte framtida generationer.
    """
    if kandidat is not None or os.environ.get('NWP_SLUG') or not godkann_kostnad or not isinstance(rattigheter, str) or not rattigheter.strip():
        raise ValueError('generering kräver betrodd ägaringång utan kandidatbindning, uttryckligt kostnadsmedgivande och rättigheter')
    if not isinstance(uppdrag_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', uppdrag_sha):
        raise ValueError('generering kräver den sparade beställningens exakta hash')
    with registerlas(slug):
        d = las(slug)
        t = d['tillgangar'].get(tid)
        if not isinstance(t, dict) or not t.get('versioner'):
            raise ValueError('okänd tillgång')
        v = t['versioner'][-1]
        job = v.get('bestallning')
        if (not isinstance(job, dict) or transport.sha(job) != uppdrag_sha or v.get('uppdrag_sha') != uppdrag_sha
                or any(job.get(k) != value for k, value in {'slug': slug, 'id': tid, 'version': v.get('version'),
                    'kandidat': t.get('kandidat'), 'roll': t.get('roll'), 'typ': t.get('typ'), 'leverantor': t.get('leverantor')}.items())):
            raise ValueError('beställningen ändrades eller saknar verifierbar identitet')
        if v.get('status') == 'genererad':
            return t  # upprepat medgivande köper aldrig en ny generation
        if v.get('status') not in ('vantar_mandat_konto', 'saknar_konto', 'vantar_resultat'):
            raise ValueError('utfallet kan vara okänt; samma version skickas inte igen, kontrollera leverantörens jobb')
        kundgranser(slug, job['prompt'])
        try:
            key = las_nyckel(job['leverantor'])
        except ValueError as e:
            v.update(status='saknar_konto', hinder=str(e))
            t['status'] = v['status']; skriv(slug, d)
            return t
        v.update(status='vantar_resultat' if v.get('jobb') else 'skickar', mandat={'uppdrag_sha': uppdrag_sha, 'tid': nu(), 'kostnad_godkand': True},
                 rattigheter=rattigheter[:300])
        t['status'] = v['status']; skriv(slug, d)

        def registrera(rid):
            v.update(jobb=rid, status='vantar_resultat')
            t['status'] = v['status']; skriv(slug, d)

        try:
            bilddata = None
            kb = job.get('kalla_bild')
            if kb:  # källbilden läses ur registret igen och måste vara samma byte som beställningen band
                kt = d['tillgangar'].get(kb.get('material'))
                kv_ = next((x for x in (kt or {}).get('versioner') or [] if x.get('version') == kb.get('version')), None)
                if not kt or not kv_ or not tillhor(kt, job.get('kandidat')):
                    raise transport.TransportFel('källbilden finns inte längre i registret', terminal=True)
                bilddata = _version_las(slug, kt['id'], kv_)
            resultat = transport.kor(job, key, befintligt=v.get('jobb'), registrera=registrera, http=http, timeout=timeout, bilddata=bilddata)
            f = _version_skriv(slug, t, v['version'], resultat['ext'], resultat['data'], aterhamtning=True)
            v.update(status='genererad', fil='material/%s/%s' % (tid, f.name), sha256=resultat['sha256'], bytes=resultat['bytes'],
                     mime=resultat['mime'], kalla='%s / %s (API)' % (job['leverantor'], job['modell']), genererad=nu())
            v.pop('hinder', None)
            t['webb'] = webb(t['typ'], resultat['ext'])
        except (transport.TransportFel, OSError) as e:
            # Ingen nyckel, prompt, leverantörstext eller signerad adress i felet.
            terminal = isinstance(e, transport.TransportFel) and e.terminal
            v.update(status='fel' if terminal else ('vantar_resultat' if v.get('jobb') else 'oklart'),
                     hinder='leverantören avslutade jobbet utan material; samma version skickas inte igen' if terminal else
                     'materialanropet slutfördes inte lokalt; sparat jobb-id kan följas upp utan nytt POST' if v.get('jobb') else
                     'utfallet kan vara okänt; inget automatiskt nytt anrop, kontrollera leverantörens konto')
        finally:
            key = None
        t['status'] = v['status']; skriv(slug, d)
        return t


@last
def importera(slug, fil, leverantor, uppdrag, kalla, rattigheter, typ=None, roll='illustrativ', kandidat=None):
    """En färdig tillgång (genererad i leverantörens egen tjänst, eller ett koncept ur canvas-design) blir en versionerad
    tillgång med källa och rättigheter; filen kopieras, originalet rörs inte."""
    p = Path(fil)
    if kandidat:
        p = i_kandidaten(slug, kandidat, fil)
        data = _las_inom(atelje.UNDERLAG, p.relative_to(atelje.UNDERLAG).parts)
    else:
        with _katalog_fd(p.absolute().parent) as fd:
            data = _las_fd(fd, p.name)
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
    f = _version_skriv(slug, t, 1, ext, data)
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


@last
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
    data = _version_las(slug, tid, v)
    sajt = kandidater.ksajt(slug, kandidat)
    if not (sajt / 'src').is_dir():
        return {'ok': False, 'hinder': 'kandidatens projekt saknar src/: %s' % sajt}
    namn = '%s__%s-v%02d%s' % (plats, tid, v['version'], Path(v['fil']).suffix)
    bilder = [(namn, data)]
    if t['typ'] == 'video' and poster:
        pv = d['tillgangar'][poster]['versioner'][-1]
        bilder.append(('%s__%s-poster%s' % (plats, tid, Path(pv['fil']).suffix), _version_las(slug, poster, pv)))
    md = kandidater.kdir(slug, kandidat) / 'material' / 'MATERIAL.md'
    with _katalog_fd(atelje.KUNDER, (slug, 'kandidater', kandidat, 'sajt', 'src', 'assets', 'material'), skapa=True) as bildfd, \
            _katalog_fd(atelje.UNDERLAG, (slug, 'atelje', 'kandidater', kandidat, 'material'), skapa=True) as mdfd:
        # Pröva alla befintliga skrivmål före första filändringen.
        for bnamn, _ in bilder:
            _las_fd(bildfd, bnamn, valfri=True)
        text = _las_fd(mdfd, 'MATERIAL.md', valfri=True)
        if text is None:
            text = ('# Material i kandidaten (materialsteget, kontroller/material.py)\n\nIllustrativt material och koncept: aldrig bilder som påstår sig visa verksamheten (kunskap/bild.md).\n\n'
                    '| fil | roll | typ | leverantör | version | källa | rättigheter | plats | Egen | påstår verksamhet | reducerad rörelse |\n|---|---|---|---|---|---|---|---|---|---|---|\n').encode()
        rad = '| %s | %s | %s | %s | v%02d | %s | %s | %s | nej | nej | %s |\n' % (
            namn, t['roll'], t['typ'], LEVERANTORER[t['leverantor']]['namn'], v['version'], v.get('kalla', ''), v.get('rattigheter', ''), plats,
            ('posterbilden visas; ingen autouppspelning' + posterrad) if t['typ'] == 'video' else 'gäller inte')
        for bnamn, bdata in bilder:
            _skriv_fd(bildfd, bnamn, bdata, ersatt=True)
        _skriv_fd(mdfd, 'MATERIAL.md', text + rad.encode(), ersatt=True)
    t.setdefault('anvand', []).append({'kandidat': kandidat, 'plats': plats, 'fil': 'src/assets/material/' + namn, 'version': v['version'], 'tid': nu()})
    skriv(slug, d)
    return {'ok': True, 'fil': 'src/assets/material/' + namn, 'md': str(md)}


def i_kandidaten(slug, kid, fil):
    """Filen ligger i kandidatens egen katalog under ateljén (aldrig en länk, aldrig utanför): skaparens import är
    kandidatavgränsad. Ger den upplösta vägen eller ValueError."""
    import kandidater
    if not re.fullmatch(r'k\d\d', kid or ''):
        raise ValueError('ogiltig kandidat')
    rot = kandidater.kdir(slug, kid)
    p = Path(fil)
    p = (atelje.ROOT / p) if not p.is_absolute() else p
    try:
        led = p.relative_to(rot).parts
        if not led or any(x in ('', '.', '..') for x in led):
            raise ValueError()
        _las_inom(atelje.UNDERLAG, (slug, 'atelje', 'kandidater', kid, *led))
    except (OSError, ValueError):
        raise ValueError('filen ska ligga i kandidatens förankrade katalog och vara utan symboliska länkar eller hårdlänkar') from None
    return p


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
    p.add_argument('--modell', help='exakt införd leverantörsmodell; förvalet sparas i beställningen')
    p.add_argument('--parametrar', help='JSON med dokumenterade format-/videoegenskaper, inga adresser eller filer')
    p.add_argument('--generera', help='betrodd ägaringång: verkställ den sparade beställningens id')
    p.add_argument('--uppdrag-sha', help='sha256 från beställningens senaste version')
    p.add_argument('--godkann-kostnad', action='store_true', help='kostnadsmedgivande för just denna uppdragshash')
    p.add_argument('--fil', help='importera en färdig tillgång')
    p.add_argument('--kalla', default='')
    p.add_argument('--rattigheter', default='')
    p.add_argument('--canvas', help='ett koncept ur canvas-design (png/pdf)')
    p.add_argument('--kandidat')
    p.add_argument('--anvand', help='tillgångens id')
    p.add_argument('--plats')
    p.add_argument('--poster')
    p.add_argument('--visa', action='store_true')
    p.add_argument('--fran', help='källbild ur registret (<id> eller <id>@vN) för redigering eller videons första ruta')
    p.add_argument('--ko', action='store_true', help='materialkön: beställningar som väntar på mandat, konto eller resultat')
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
        if a.generera:
            if any((a.bestall, a.typ, a.igen, a.fil, a.canvas, a.anvand, a.visa, a.anvandning, a.modell, a.parametrar, a.fran, a.ko)):
                raise ValueError('--generera verkställer bara befintlig beställning; andra åtgärder får inte kombineras')
            ut = generera(a.slug, a.generera, a.uppdrag_sha, a.godkann_kostnad, a.rattigheter, kandidat=a.kandidat)
        elif a.visa:
            ut = synliga(las(a.slug), a.kandidat)
        elif a.ko:
            ut = ko(a.slug, a.kandidat)
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
            try:
                parametrar = json.loads(a.parametrar) if a.parametrar else None
            except ValueError:
                raise ValueError('--parametrar måste vara giltig JSON') from None
            ut = bestall(a.slug, a.bestall, a.typ or 'bild', a.leverantor, a.roll, a.igen, kandidat=a.kandidat, modell=a.modell, parametrar=parametrar,
                         fran=a.fran)
        else:
            p.print_usage()
            return 2
    except (ValueError, OSError) as e:
        text = str(e) if isinstance(e, ValueError) else 'materialets filer kunde inte läsas eller skrivas'
        print(json.dumps({'ok': False, 'hinder': text}, ensure_ascii=False))
        return 1
    print(json.dumps(ut, ensure_ascii=False, indent=1))
    return 0 if ut.get('ok', True) and ut.get('status') not in ('vantar_mandat_konto', 'saknar_konto', 'skickar', 'vantar_resultat', 'oklart', 'fel') else 1


if __name__ == '__main__':
    sys.exit(main())
