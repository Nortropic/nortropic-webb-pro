#!/usr/bin/env python3
"""Bilddatum: när varje egen bild togs, för datumkolumnen i underlag/<slug>/bilder/BILDER.md (steg 1 punkt 2).

Källa per bild, i den ordningen: EXIF DateTimeOriginal (eller DateTimeDigitized), EXIF DateTime (senast ändrad),
telefonkamerans filnamn (20210824_141203, IMG_20210824_141203, PXL_…, 2021-08-24) märkt tolkning, annars okänt.
Läser JPEG, WebP och PNG med standardbiblioteket. Noterar om bilden bär GPS-läge: det är en personuppgift som stannar i
underlaget; astro:assets tar bort metadata i de publicerade filerna (kunskap/bild.md).

    .venv/bin/python kontroller/bilddatum.py underlag/<slug>/bilder [--json]
"""
import json
import re
import struct
import sys
from pathlib import Path

BILDER = {'.jpg', '.jpeg', '.webp', '.png', '.avif'}
FILNAMN = [
    (re.compile(r'((?:19|20)\d{2})(\d{2})(\d{2})[_-]?(\d{2})(\d{2})(\d{2})'), lambda m: '%s-%s-%s %s:%s' % m.group(1, 2, 3, 4, 5)),
    (re.compile(r'((?:19|20)\d{2})-(\d{2})-(\d{2})(?:[ _at.]+(\d{2})[.:](\d{2}))?'),
     lambda m: '%s-%s-%s' % m.group(1, 2, 3) + (' %s:%s' % m.group(4, 5) if m.group(4) else '')),
]


def tiff_block(data):
    """TIFF-datat med EXIF ur en JPEG (APP1 'Exif'), WebP (chunk EXIF) eller PNG (chunk eXIf), annars None."""
    if data[:2] == b'\xff\xd8':
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF:
            markor, langd = data[i + 1], struct.unpack('>H', data[i + 2:i + 4])[0]
            if markor == 0xE1 and data[i + 4:i + 10] == b'Exif\x00\x00':
                return data[i + 10:i + 2 + langd]
            if markor in (0xDA, 0xD9):
                break
            i += 2 + langd
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        i = 12
        while i + 8 <= len(data):
            namn, langd = data[i:i + 4], struct.unpack('<I', data[i + 4:i + 8])[0]
            if namn == b'EXIF':
                block = data[i + 8:i + 8 + langd]
                return block[6:] if block.startswith(b'Exif\x00\x00') else block
            i += 8 + langd + (langd & 1)
    elif data[4:8] == b'ftyp':  # AVIF/HEIF (ISOBMFF): EXIF ligger som ett Exif-objekt i meta (omgång elva, F33)
        lage, varde = avif_metadata(data)
        return varde if lage == 'tiff' else None
    elif data[:8] == b'\x89PNG\r\n\x1a\n':
        i = 8
        while i + 8 <= len(data):
            langd, namn = struct.unpack('>I', data[i:i + 4])[0], data[i + 4:i + 8]
            if namn == b'eXIf':
                return data[i + 8:i + 8 + langd]
            i += 12 + langd
    return None


def _isobmff_boxar(data, start=0, slut=None):
    """(typ, innehållsstart, innehållsslut) för boxarna i ett ISOBMFF-intervall (AVIF/HEIF)."""
    slut = len(data) if slut is None else slut
    i = start
    while i + 8 <= slut:
        storlek, typ = struct.unpack('>I4s', data[i:i + 8])
        huvud = 8
        if storlek == 1:
            if i + 16 > slut:
                return
            storlek, huvud = struct.unpack('>Q', data[i + 8:i + 16])[0], 16
        elif storlek == 0:
            storlek = slut - i
        if storlek < huvud or i + storlek > slut:
            return
        yield typ, i + huvud, i + storlek
        i += storlek


def avif_poster(data):
    """Objekten i en AVIF/HEIF-fil ur meta (iinf och iloc): {id: {'typ', 'metod', 'extents': [(offset, längd)]}}."""
    poster = {}
    for typ, a, b in _isobmff_boxar(data):
        if typ != b'meta':
            continue
        for t2, c, d in _isobmff_boxar(data, a + 4, b):  # meta är en FullBox: version och flaggor först
            if t2 == b'iinf':
                v = data[c]
                p = c + 6 if v == 0 else c + 8
                for t3, e, f in _isobmff_boxar(data, p, d):
                    if t3 != b'infe' or data[e] < 2:
                        continue
                    if data[e] == 2:
                        iid, typ4 = struct.unpack('>H', data[e + 4:e + 6])[0], data[e + 8:e + 12]
                    else:
                        iid, typ4 = struct.unpack('>I', data[e + 4:e + 8])[0], data[e + 10:e + 14]
                    poster.setdefault(iid, {})['typ'] = typ4
            elif t2 == b'iloc':
                v, p = data[c], c + 4
                os_, ls_ = data[p] >> 4, data[p] & 15
                bos, isz = data[p + 1] >> 4, (data[p + 1] & 15 if v in (1, 2) else 0)
                p += 2

                def tal(storlek, pos):
                    return (int.from_bytes(data[pos:pos + storlek], 'big') if storlek else 0), pos + storlek
                n, p = tal(2 if v < 2 else 4, p)
                for _ in range(n):
                    iid, p = tal(2 if v < 2 else 4, p)
                    metod = 0
                    if v in (1, 2):
                        m_, p = tal(2, p)
                        metod = m_ & 15
                    _, p = tal(2, p)  # data_reference_index
                    bas, p = tal(bos, p)
                    antal, p = tal(2, p)
                    ext = []
                    for _ in range(antal):
                        if isz:
                            _, p = tal(isz, p)
                        o, p = tal(os_, p)
                        l_, p = tal(ls_, p)
                        ext.append((bas + o, l_))
                    poster.setdefault(iid, {}).update(metod=metod, extents=ext)
    return poster


def avif_metadata(data):
    """('ingen', None) när AVIF-filen saknar EXIF och GPS-bärande XMP; ('tiff', tiff) när EXIF-blocket gick att läsa
    (konstruktionsmetod 0, filoffset); ('oklar', skäl) när metadata är deklarerad men inte går att verifiera, eller XMP
    med GPS-fält finns. Omgång elva, F33: AVIF hoppades över trots att byggstandarden rekommenderar formatet."""
    if data[4:8] != b'ftyp':
        return 'ingen', None
    tiffs, oklar = [], None  # alla EXIF-objekt: ett senare rent objekt får inte dölja ett tidigare med GPS (omgång fjorton, F33)
    for iid, post in avif_poster(data).items():
        if post.get('typ') not in (b'Exif', b'mime'):
            continue
        if post.get('metod', 0) != 0 or not post.get('extents'):
            oklar = 'metadataobjekt %s som inte går att läsa (konstruktionsmetod %s)' % (post.get('typ', b'?').decode('ascii', 'replace'), post.get('metod'))
            continue
        block = b''  # alla dataintervall, med gränskontroll: GPS kan ligga i det andra (omgång tretton, F33)
        for o, l_ in post['extents']:
            if o < 0 or l_ < 0 or o + l_ > len(data):
                block = None
                break
            block += data[o:o + l_]
        if block is None:
            oklar = 'metadataobjektet pekar utanför filen (trunkerad)'
            continue
        if post['typ'] == b'mime':
            if b'GPS' in block:
                oklar = 'XMP-metadata med GPS-fält'
            continue
        if len(block) < 4:
            oklar = 'EXIF-objektet är tomt eller trunkerat'
            continue
        skift = struct.unpack('>I', block[:4])[0]
        if 4 + skift >= len(block):
            oklar = 'EXIF-objektet är trunkerat'
            continue
        kandidat = block[4 + skift:]
        if kandidat[:2] in (b'II', b'MM'):
            try:  # ett deklarerat block som inte går att tolka är inte rent (omgång tretton, F33)
                info = exif(kandidat)
            except Exception:  # noqa: BLE001
                oklar = 'EXIF-blocket går inte att tolka (trunkerat eller skadat)'
                continue
            tiffs.append((bool(info.get('gps')), kandidat))
        else:
            oklar = 'EXIF-objektet saknar TIFF-huvud'
    if oklar:  # GPS i XMP eller overifierbar metadata väger tyngre än ett rent EXIF-block i samma fil (omgång tolv, F33)
        return 'oklar', oklar
    if not tiffs:
        return 'ingen', None
    med_gps = [t for gps, t in tiffs if gps]  # GPS i något av objekten gäller för hela filen
    return 'tiff', (med_gps[0] if med_gps else tiffs[0][1])


def exif(tiff):
    """Taggarna som behövs: DateTimeOriginal, DateTimeDigitized, DateTime, kameramodell och om GPS finns."""
    if not tiff or tiff[:2] not in (b'II', b'MM'):
        return {}
    e = '<' if tiff[:2] == b'II' else '>'

    def ifd(offset):
        ut = {}
        if offset + 2 > len(tiff):  # en ofullständig deklarerad tabell är ett parserfel, inte en tom tabell (omgång fjorton, F33)
            raise ValueError('IFD-pekaren %d ligger utanför blocket (%d byte)' % (offset, len(tiff)))
        n = struct.unpack(e + 'H', tiff[offset:offset + 2])[0]
        for k in range(n):
            p = offset + 2 + 12 * k
            if p + 12 > len(tiff):
                raise ValueError('IFD:n deklarerar %d poster men blocket slutar efter %d' % (n, k))
            tagg, typ, antal = struct.unpack(e + 'HHI', tiff[p:p + 8])
            varde = tiff[p + 8:p + 12]
            if typ == 2:  # ASCII
                start = struct.unpack(e + 'I', varde)[0] if antal > 4 else p + 8
                if start + antal > len(tiff):
                    raise ValueError('ASCII-värdet för tagg %#x ligger utanför blocket' % tagg)
                ut[tagg] = tiff[start:start + antal].split(b'\x00')[0].decode('ascii', 'replace').strip()
            elif typ == 4:
                ut[tagg] = struct.unpack(e + 'I', varde)[0]
        return ut

    noll = ifd(struct.unpack(e + 'I', tiff[4:8])[0])
    under = ifd(noll[0x8769]) if 0x8769 in noll else {}
    return {'original': under.get(0x9003) or under.get(0x9004), 'andrad': noll.get(0x0132),
            'modell': noll.get(0x0110), 'gps': 0x8825 in noll}


def datum(fil):
    try:
        e = exif(tiff_block(Path(fil).read_bytes()))
    except (OSError, struct.error, IndexError, ValueError):  # datumet är en upplysning; ett parserfel lämnar det okänt
        e = {}
    norm = lambda s: re.sub(r'^(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}).*$', r'\1-\2-\3 \4:\5', s)  # noqa: E731
    if e.get('original') and re.match(r'\d{4}:\d{2}:\d{2}', e['original']):
        d, kalla = norm(e['original']), 'EXIF DateTimeOriginal'
    elif e.get('andrad') and re.match(r'\d{4}:\d{2}:\d{2}', e['andrad']):
        d, kalla = norm(e['andrad']), 'EXIF DateTime (senast ändrad, inte nödvändigtvis tagen)'
    else:
        d, kalla = None, 'okänt'
        for monster, form in FILNAMN:
            m = monster.search(Path(fil).name)
            if m:
                d, kalla = form(m), 'filnamn (tolkning)'
                break
    return {'fil': Path(fil).name, 'datum': d, 'kalla': kalla, 'modell': e.get('modell'), 'gps': bool(e.get('gps'))}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip().split('\n\n')[-1], file=sys.stderr)
        return 2
    rot = Path(argv[0])
    filer = sorted(f for f in (rot.iterdir() if rot.is_dir() else [rot]) if f.suffix.lower() in BILDER)
    rader = [datum(f) for f in filer]
    if '--json' in argv:
        print(json.dumps(rader, ensure_ascii=False, indent=1))
        return 0
    print('| Fil | Datum | Källa för datumet | Kamera | GPS |\n|---|---|---|---|---|')
    for r in rader:
        print('| %s | %s | %s | %s | %s |' % (r['fil'], r['datum'] or 'okänt', r['kalla'], r['modell'] or '', 'ja (stannar i underlaget)' if r['gps'] else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
