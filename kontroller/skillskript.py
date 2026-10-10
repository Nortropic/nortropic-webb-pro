#!/usr/bin/env python3
"""Kör avgränsade skillfunktioner med kopior av den egna kandidatens filer.

Anrop: skillskript.py <slug> --kandidat k01 --uppdrag <egen JSON-fil>.
Åtgärder och uppdragsformat: kunskap/skillskript.md. Ingen fri skriptsökväg,
installation eller användarkod körs. Canvas delegeras till webbtjänsten vid behov.
"""
import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

import korregister
import slugvakt

ROOT = Path(__file__).resolve().parents[1]
MAX_FIL = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
SCRIPTS = {
    'brand-context': 'brand/scripts/inject-brand-context.cjs',
    'brand-palette': 'brand/scripts/extract-colors.cjs',
    'brand-asset': 'brand/scripts/validate-asset.cjs',
    'brand-tokens': 'brand/scripts/sync-brand-to-tokens.cjs',
    'tokens-css': 'design-system/scripts/generate-tokens.cjs',
    'tokens-tailwind': 'design-system/scripts/generate-tokens.cjs',
    'tokens-embed': 'design-system/scripts/embed-tokens.cjs',
    'tokens-validate': 'design-system/scripts/validate-tokens.cjs',
    'tailwind-config': 'ui-styling/scripts/tailwind_config_gen.py',
}
FALT = {
    **{a: {'input'} for a in SCRIPTS},
    'brand-tokens': {'input', 'tokens'},
    'tokens-embed': {'input', 'minimal'},
    'tokens-validate': {'files'},
    'tailwind-config': {'framework', 'colors', 'fonts', 'spacing', 'breakpoints'},
    'canvas': {'input', 'width', 'height', 'fonts', 'format'},
}
SVG_TAGGAR = set('svg g defs path rect circle ellipse line polyline polygon text tspan image '
                 'linearGradient radialGradient stop clipPath mask pattern title desc'.split())
SVG_ATTRIBUT = set('id x y x1 y1 x2 y2 cx cy r rx ry width height viewBox preserveAspectRatio '
                  'd points transform fill fill-opacity fill-rule stroke stroke-width stroke-opacity '
                  'stroke-linecap stroke-linejoin stroke-dasharray stroke-dashoffset opacity '
                  'font-family font-size font-weight font-style letter-spacing word-spacing '
                  'text-anchor dominant-baseline dx dy rotate textLength lengthAdjust '
                  'gradientUnits gradientTransform offset stop-color stop-opacity spreadMethod '
                  'clip-path clip-rule mask maskUnits maskContentUnits patternUnits patternContentUnits '
                  'patternTransform href'.split())


class Nekat(ValueError):
    pass


class Avbruten(BaseException):
    def __init__(self, signum):
        self.signum = signum


def sha(data):
    return hashlib.sha256(data).hexdigest()


def delar(vag):
    """Repo-relativa led även från kundrepots absolut omskrivna uppdrag; lös aldrig bort punktled eller länkar."""
    if not isinstance(vag, str) or not vag or any(ord(c) < 32 for c in vag) or '\\' in vag:
        raise Nekat('sökvägen ska vara en filsökväg under motorns rot')
    p = PurePosixPath(vag)
    raw = vag[1:] if p.is_absolute() else vag
    if any(x in ('', '.', '..') for x in raw.split('/')):
        raise Nekat('tomma sökvägsled och punktled tillåts inte')
    led = p.parts
    if p.is_absolute():
        bas = PurePosixPath(str(ROOT)).parts
        if led[:len(bas)] != bas or len(led) <= len(bas):
            raise Nekat('absoluta sökvägar måste ligga under motorns rot')
        led = led[len(bas):]
    return led


@contextlib.contextmanager
def katalog(rot, led, skapa=False):
    """Förankrat kataloghandtag: varje led öppnas utan att följa länkar."""
    fd = os.open(str(rot), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for namn in led:
            if skapa:
                try:
                    os.mkdir(namn, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            ny = os.open(namn, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = ny
        yield fd
    finally:
        os.close(fd)


def las_fil(rot, led, tak=MAX_FIL):
    with katalog(rot, led[:-1]) as fd:
        fil = os.open(led[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(fil, 'rb') as f:
            s = os.fstat(f.fileno())
            if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_size > tak:
                raise Nekat('indata ska vara en vanlig, olänkad fil inom storleksgränsen')
            data = f.read(tak + 1)
            if len(data) > tak:
                raise Nekat('indata överskrider storleksgränsen')
            return data


def skriv(fd, namn, data):
    if '/' in namn or namn in ('.', '..'):
        raise Nekat('ogiltigt utdatanamn')
    fil = os.open(namn, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    with os.fdopen(fil, 'wb') as f:
        f.write(data)


def kandidatrot(slug, kandidat):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,59}', slug or ''):
        raise Nekat('ogiltig slug')
    if not re.fullmatch(r'k[0-9]{2,3}', kandidat or ''):
        raise Nekat('ogiltig kandidat')
    slugvakt.krav_slug(slug)
    return ('underlag', slug, 'atelje', 'kandidater', kandidat)


def eget_input(slug, kandidat, vag):
    led = delar(vag)
    tillatna = (kandidatrot(slug, kandidat), ('kunder', slug, 'kandidater', kandidat, 'sajt', 'src'))
    if not any(led[:len(rot)] == rot and len(led) > len(rot) for rot in tillatna):
        raise Nekat('indata måste ligga i den egna kandidatens underlag eller sajt/src')
    return las_fil(ROOT, led)


def las_uppdrag(slug, kandidat, vag):
    led = delar(vag)
    bas = kandidatrot(slug, kandidat)
    if led[:len(bas)] != bas or len(led) <= len(bas):
        raise Nekat('uppdraget måste ligga i den egna kandidatens underlag')
    raw = las_fil(ROOT, led, 65536)
    def inga_dubbletter(par):
        d = {}
        for k, v in par:
            if k in d:
                raise Nekat('uppdraget har dubblerade nycklar')
            d[k] = v
        return d
    job = json.loads(raw, object_pairs_hook=inga_dubbletter)
    if not isinstance(job, dict) or not isinstance(job.get('action'), str) or job['action'] not in FALT:
        raise Nekat('okänd åtgärd; inga installations- eller fria skriptanrop tillåts')
    if not isinstance(job.get('id'), str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,59}', job['id']):
        raise Nekat('id ska vara ett nytt kort namn med små bokstäver, siffror och bindestreck')
    if set(job) - (FALT[job['action']] | {'id', 'action'}):
        raise Nekat('uppdraget har okända fält')
    return job, sha(raw)


def statisk_svg(raw):
    """Tillåt statisk SVG-geometri/text samt inbäddade rasterbilder; ingen HTML, CSS eller kod."""
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)', raw, re.I):
        raise Nekat('DTD och entiteter tillåts inte i canvas')
    try:
        svg = ET.fromstring(raw)
    except ET.ParseError as e:
        raise Nekat('canvas kräver giltig SVG') from e
    antal = 0
    for nod in svg.iter():
        antal += 1
        tag = nod.tag.removeprefix('{http://www.w3.org/2000/svg}')
        if tag not in SVG_TAGGAR or antal > 20000:
            raise Nekat('canvas innehåller ett otillåtet element eller för många element')
        for attribut, v in nod.attrib.items():
            namn = attribut.removeprefix('{http://www.w3.org/1999/xlink}')
            if namn not in SVG_ATTRIBUT:
                raise Nekat('canvas innehåller ett otillåtet attribut')
            if namn == 'href':
                lokal = re.fullmatch(r'#[A-Za-z_][\w.-]*', v)
                data = re.fullmatch(r'data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/=\s]+)', v)
                if not lokal and not (tag == 'image' and data):
                    raise Nekat('canvas får bara använda lokala id:n eller inbäddade rasterbilder')
                if data:
                    try:
                        bild = base64.b64decode(re.sub(r'\s+', '', data[2]), validate=True)
                    except ValueError as e:
                        raise Nekat('ogiltig inbäddad bild') from e
                    giltig = {'png': bild.startswith(b'\x89PNG\r\n\x1a\n'),
                              'jpeg': bild.startswith(b'\xff\xd8\xff'),
                              'webp': bild.startswith(b'RIFF') and bild[8:12] == b'WEBP'}
                    if not giltig[data[1]]:
                        raise Nekat('bildens deklarerade format stämmer inte')
            elif ('url' in v.lower() and not re.fullmatch(r'url\(#[A-Za-z_][\w.-]*\)', v)) \
                    or any(c in v for c in ('\\', '<', '>')):
                raise Nekat('canvas får inte hämta externa resurser')
    if svg.tag.removeprefix('{http://www.w3.org/2000/svg}') != 'svg':
        raise Nekat('canvas roten måste vara SVG')
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(svg, encoding='unicode')


def forbered(job, slug, kandidat, tmp):
    """Returnerar betrodd skriptväg, fasta argument, förväntade filer och indatahashar."""
    a = job['action']
    hashes = {}
    total = 0
    def kopia(vag, namn):
        nonlocal total
        data = eget_input(slug, kandidat, vag)
        total += len(data)
        if total > MAX_TOTAL:
            raise Nekat('indata överskrider den samlade storleksgränsen')
        mal = tmp / namn
        mal.parent.mkdir(parents=True, exist_ok=True)
        mal.write_bytes(data)
        hashes[vag] = sha(data)
        return data
    if a == 'canvas':
        w, h = job.get('width'), job.get('height')
        if any(type(n) is not int or not 1 <= n <= 4096 for n in (w, h)) or w * h > 16000000:
            raise Nekat('canvas bredd/höjd ska vara 1–4096 och tillsammans högst 16 miljoner pixlar')
        fmt = job.get('format', 'png')
        if fmt not in ('png', 'pdf', 'both'):
            raise Nekat('canvas format ska vara png, pdf eller both')
        svg = statisk_svg(kopia(job.get('input'), 'source.svg'))
        fonts = job.get('fonts', [])
        if not isinstance(fonts, list) or len(fonts) > 8:
            raise Nekat('canvas fonts ska vara en lista med högst åtta medföljande TTF-filnamn')
        fontdata = []
        for f in fonts:
            if not isinstance(f, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.ttf', f):
                raise Nekat('ogiltigt typsnittsnamn')
            led = ('.claude', 'skills', 'canvas-design', 'canvas-fonts', f)
            raw = las_fil(ROOT, led)
            fontdata.append({'family': f[:-4], 'data': base64.b64encode(raw).decode('ascii')})
            hashes['/'.join(led)] = sha(raw)
        (tmp / 'canvas.json').write_text(json.dumps({'svg': svg, 'width': w, 'height': h,
                                                   'fonts': fontdata, 'format': fmt}), encoding='utf-8')
        files = ['canvas.png', 'canvas.pdf'] if fmt == 'both' else ['canvas.' + fmt]
        return ROOT / 'kontroller' / 'skillskript-canvas.mjs', ['canvas.json'], files, hashes
    script = ROOT / '.claude' / 'skills' / SCRIPTS[a]
    if a == 'tailwind-config':
        framework = job.get('framework', 'react')
        if framework not in ('react', 'vue', 'svelte', 'nextjs'):
            raise Nekat('Tailwind-generatorn har bara react, vue, svelte och nextjs')
        args = ['--framework', framework, '--output', 'tailwind.config.ts']
        for field in ('colors', 'fonts', 'spacing', 'breakpoints'):
            values = job.get(field, {})
            if not isinstance(values, dict) or len(values) > 128:
                raise Nekat('Tailwind-värden ska vara små objekt med namn och strängvärden')
            for key, value in values.items():
                if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]{0,63}', key) \
                        or not isinstance(value, str) or not value or len(value) > 512 \
                        or any(ord(c) < 32 for c in value):
                    raise Nekat('ogiltigt Tailwind-värde')
            if values:
                args += ['--' + field] + [k + ':' + v for k, v in values.items()]
        return script, args, ['tailwind.config.ts'], hashes
    if a == 'tokens-validate':
        files = job.get('files')
        if not isinstance(files, list) or not 1 <= len(files) <= 64 \
                or any(not isinstance(f, str) for f in files) or len(set(files)) != len(files):
            raise Nekat('tokens-validate kräver 1–64 olika filer')
        for i, f in enumerate(files):
            suffix = PurePosixPath(f).suffix
            if suffix not in ('.css', '.html', '.jsx', '.tsx', '.js', '.ts', '.vue', '.svelte', '.astro'):
                raise Nekat('tokenkontrollen kräver textfiler för webb')
            # Väljaren i originalskriptet saknar HTML/Astro och hoppar över vissa namn.
            # Uppdragets uttryckliga filurval granskas som råtext i ordning, utan dessa tysta bortfall.
            kopia(f, 'src/%02d.css' % i)
        return script, ['--dir', 'src'], [], hashes
    fil = job.get('input')
    if a in ('brand-context', 'brand-palette', 'brand-tokens'):
        kopia(fil, 'docs/brand-guidelines.md')
        if a == 'brand-context':
            return script, ['docs/brand-guidelines.md', '--json'], [], hashes
        if a == 'brand-palette':
            return script, ['--palette', '--brand-file', 'docs/brand-guidelines.md', '--json'], [], hashes
        if job.get('tokens'):
            kopia(job['tokens'], 'assets/design-tokens.json')
        return script, ['--force'], ['assets/design-tokens.json', 'assets/design-tokens.css'], hashes
    if a == 'brand-asset':
        namn = PurePosixPath(fil).name if isinstance(fil, str) else ''
        if not namn or namn.startswith('-'):
            raise Nekat('ogiltigt tillgångsnamn')
        kopia(fil, 'assets/' + namn)
        return script, ['assets/' + namn, '--json'], [], hashes
    if a in ('tokens-css', 'tokens-tailwind'):
        kopia(fil, 'tokens.json')
        fmt = a.split('-')[1]
        ut = 'tokens.css' if fmt == 'css' else 'tokens.tailwind.cjs'
        return script, ['--config', 'tokens.json', '--format', fmt, '--output', ut], [ut], hashes
    kopia(fil, 'assets/design-tokens.css')
    if type(job.get('minimal', False)) is not bool:
        raise Nekat('minimal ska vara bool')
    return script, (['--minimal'] if job.get('minimal') else []), [], hashes


def kor_subprocess(script, args, tmp):
    # Betrodd repo-kod och fast interpreter; inga Node/Python-startflaggor från miljön.
    led = script.relative_to(ROOT).parts
    las_fil(ROOT, led)
    node = shutil.which('node')
    if not node:
        raise Nekat('Node saknas i körmiljön')
    python = ROOT / '.venv' / 'bin' / 'python'
    executable = str(python) if script.suffix == '.py' else node
    # brand-tokens startar själv generate-tokens med node: endast den funna nodens katalog och systemverktyg.
    env = {'PATH': str(Path(node).parent) + ':/usr/bin:/bin', 'LANG': 'en_US.UTF-8',
           'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    # Browserns befintliga nätgräns behöver tjänstens policy, aldrig nycklar/proxy från skaparen.
    for key in ('NWP_I_TJANSTEN', 'NWP_NAT_TILLATNA', 'NWP_SLUG'):
        if os.environ.get(key):
            env[key] = os.environ[key]
    with (tmp / 'stdout.txt').open('wb') as out, (tmp / 'stderr.txt').open('wb') as err:
        def avbryt(signum, _frame):
            raise Avbruten(signum)
        gammal = signal.signal(signal.SIGTERM, avbryt)
        p = None
        try:
            p = subprocess.Popen([executable, str(script), *args], cwd=tmp, env=env, stdout=out, stderr=err,
                                 start_new_session=True)
            try:
                rc = p.wait(timeout=60)
            except BaseException:
                # Även barnskriptet i brand-tokens avslutas vid SIGTERM, Ctrl-C eller timeout.
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                p.wait()
                raise
        finally:
            signal.signal(signal.SIGTERM, gammal)
    return rc


def kor(slug, kandidat, uppdrag, bara_canvas=False):
    job, jobsha = las_uppdrag(slug, kandidat, uppdrag)
    if bara_canvas and job['action'] != 'canvas':
        raise Nekat('webbtjänstens canvas-väg tillåter bara canvas')
    if job['action'] == 'canvas' and not bara_canvas:
        import webbtjanst
        if webbtjanst.delegeras():
            return webbtjanst.via_tjanst('skillskript-canvas', [slug, '--kandidat', kandidat, '--uppdrag', uppdrag], timeout=120)
        if os.environ.get('NWP_SANDLADA') == 'pa' and not os.environ.get('NWP_I_TJANSTEN'):
            raise Nekat('canvas i sandlådan kräver webbtjänsten')
    bas = kandidatrot(slug, kandidat) + ('kompetens', 'skillskript')
    # Kataloghandtaget binds före jobbstart och behålls vid alla slutliga skrivningar.
    with katalog(ROOT, bas, skapa=True) as fd:
        os.mkdir(job['id'], mode=0o700, dir_fd=fd)  # exklusiv version, aldrig överskrivning
        outfd = os.open(job['id'], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            def samma_utkatalog():
                with katalog(ROOT, (*bas, job['id'])) as aktuell:
                    a, b = os.fstat(aktuell), os.fstat(outfd)
                    if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                        raise Nekat('utkatalogen byttes under körningen')
            # Modellen får skriva i kandidaten; leverantörsskriptens cwd får därför aldrig ligga där.
            # Korregister skapar en exklusiv katalog i processens temporära område, utanför kandidaten.
            with korregister.egen_tmp_med('nwp-skill-', 'skillskript ' + job['action']) as td:
                tmp = Path(td)
                script, args, files, inputs = forbered(job, slug, kandidat, tmp)
                sourcehash = sha(las_fil(ROOT, script.relative_to(ROOT).parts))
                sources = {str(script.relative_to(ROOT)): sourcehash}
                if job['action'] == 'brand-tokens':
                    sibling = ('.claude', 'skills', 'design-system', 'scripts', 'generate-tokens.cjs')
                    sources['/'.join(sibling)] = sha(las_fil(ROOT, sibling))
                rc = kor_subprocess(script, args, tmp)
                samma_utkatalog()
                outputs = {}
                for f in ['stdout.txt', 'stderr.txt', *files]:
                    data = las_fil(tmp, PurePosixPath(f).parts, MAX_TOTAL)
                    if f in files and not data:
                        raise Nekat('det betrodda skriptet gav en tom utdatafil')
                    namn = PurePosixPath(f).name
                    skriv(outfd, namn, data)
                    outputs[namn] = {'sha256': sha(data), 'bytes': len(data)}
                if job['action'] == 'tokens-embed' and rc == 0:
                    data = las_fil(tmp, ('stdout.txt',))
                    if not data.strip():
                        raise Nekat('tokeninbäddningen gav ingen CSS')
                    skriv(outfd, 'tokens.css', data)
                    outputs['tokens.css'] = {'sha256': sha(data), 'bytes': len(data)}
                # Valideringsskriptens fynd är råd enligt deras egna regler, inget sajtgodkännande.
                kvitto = {'schema': 1, 'slug': slug, 'kandidat': kandidat, 'action': job['action'],
                          'id': job['id'], 'uppdrag_sha256': jobsha, 'script': str(script.relative_to(ROOT)),
                          'script_sha256': sourcehash, 'sources': sources, 'inputs': inputs, 'outputs': outputs, 'rc': rc,
                          'status': 'kord' if rc == 0 else 'underkand', 'visuell_kvalitet': 'ej_bedomd'}
                skriv(outfd, 'RESULTAT.json', (json.dumps(kvitto, ensure_ascii=False, indent=2) + '\n').encode())
                samma_utkatalog()
                print(json.dumps({'ok': rc == 0, 'resultat': '/'.join((*bas, job['id'], 'RESULTAT.json'))}, ensure_ascii=False))
                return 0 if rc == 0 else 1
        finally:
            os.close(outfd)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    bara = args[:1] == ['--bara-canvas']
    if bara:
        args.pop(0)
    # Literal prefix i allowedTools är kandidatmandatet. Alternativa/duplicerade flaggor kan inte ändra det.
    if len(args) != 5 or args[1] != '--kandidat' or args[3] != '--uppdrag':
        print('användning: skillskript.py <slug> --kandidat <kNN> --uppdrag <egen JSON-fil>', file=sys.stderr)
        return 2
    try:
        return kor(args[0], args[2], args[4], bara)
    except Avbruten as e:
        print('skillskript: avbruten av signal %d; egen arbetskopia städad' % e.signum, file=sys.stderr)
        return 128 + e.signum
    except (ValueError, OSError, subprocess.TimeoutExpired) as e:
        print('skillskript: %s' % str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
