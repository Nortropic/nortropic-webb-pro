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

BILDER = {'.jpg', '.jpeg', '.webp', '.png'}
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
    elif data[:8] == b'\x89PNG\r\n\x1a\n':
        i = 8
        while i + 8 <= len(data):
            langd, namn = struct.unpack('>I', data[i:i + 4])[0], data[i + 4:i + 8]
            if namn == b'eXIf':
                return data[i + 8:i + 8 + langd]
            i += 12 + langd
    return None


def exif(tiff):
    """Taggarna som behövs: DateTimeOriginal, DateTimeDigitized, DateTime, kameramodell och om GPS finns."""
    if not tiff or tiff[:2] not in (b'II', b'MM'):
        return {}
    e = '<' if tiff[:2] == b'II' else '>'

    def ifd(offset):
        ut = {}
        if offset + 2 > len(tiff):
            return ut
        n = struct.unpack(e + 'H', tiff[offset:offset + 2])[0]
        for k in range(n):
            p = offset + 2 + 12 * k
            if p + 12 > len(tiff):
                break
            tagg, typ, antal = struct.unpack(e + 'HHI', tiff[p:p + 8])
            varde = tiff[p + 8:p + 12]
            if typ == 2:  # ASCII
                start = struct.unpack(e + 'I', varde)[0] if antal > 4 else p + 8
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
    except (OSError, struct.error, IndexError):
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
