#!/usr/bin/env python3
"""stilpaket.py — Referos stilpaket för en vald stil, till skaparen och in i CSS:en (ägarens uppdrag 2026-10-05 18:53Z,
punkt 2, ordagrant i minnet): originalexporten bevaras orörd och för sig, CSS-variablerna i Referos egna namn och ett
Tailwind-tema läggs i sajten, och kundanpassningen skrivs i en egen fil.

    .venv/bin/python kontroller/stilpaket.py <slug> --stil <uuid> [--kandidat k01] [--namn kort-namn]

Hämtar direkt ur Referos MCP-server (kontroller/refero_mcp.py, ingen modell). Bara stilens id och titel går till Referos
tjänst, aldrig kundens uppgifter.
- underlag/<slug>/referenser/stilar/<uuid>/: STIL.json och STIL.md (exporten ordagrant), preview_0..2 (förhandsbilderna)
  och ORIGINAL.json (filernas sha256, källan och tiden). Mappen skrivs aldrig över: har exporten ändrats hos Refero
  flyttas den förra till tidigare/<tid>/ först.
- <sajt>/src/styles/stil/<namn>.css: :root med Referos variabler ur exportens komponenter (--color-*, --font-*,
  --shadow-*) och de övriga tokens i samma namnform: färgerna ur tabellen, typskalan som --text-<roll> med
  --text-<roll>--line-height och --text-<roll>--letter-spacing, radierna som --radius-<del>, avstånden som --space-<del>.
  Filen är originalet för DESIGN.md:s import (sha256) och ändras aldrig.
- <sajt>/src/styles/stil/<namn>.tema.css: samma värden som ett @theme-block för Tailwind 4.
- <sajt>/src/styles/stil/<namn>.STILPAKET.md: vad paketet bär (färgernas roller, typsnitten och deras fria ersättare,
  typskalan, layout, bildspråk, gör och gör inte) och raden till DESIGN.md:s import.
Kundanpassningen skrivs i <namn>.anpassning.css, en egen fil som läser variablerna (kunskap/beroenden.md). Typsnitt med
källan custom är inte fria: paketet anger exportens fria ersättare, som installeras med kontroller/typsnitt.py.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refero_mcp  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
UNDERLAG = ROOT / 'underlag'
KUNDER = ROOT / 'kunder'
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode('utf-8')).hexdigest()


def slugga(text, standard='stil'):
    t = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:40] or standard


def forsta_tal(v, enhet='px'):
    """Ett CSS-värde ur exportens text: '16-24px' → '16px' (spannet står i kommentaren), 12 → '12px'."""
    if isinstance(v, (int, float)):
        return '%s%s' % (('%g' % v), enhet)
    m = re.search(r'(-?\d+(?:\.\d+)?)\s*(px|rem|em|%)?', str(v or ''))
    return ('%s%s' % (m.group(1), m.group(2) or enhet)) if m else None


def rotvariabler(stil):
    """Referos egna variabler ur komponenternas :root-block, i ordning; första förekomsten gäller."""
    ut = {}
    for c in stil.get('components') or []:
        for blk in re.finditer(r':root\s*\{(.*?)\}', str((c or {}).get('html') or ''), re.S):
            for m in re.finditer(r'(--[a-z0-9-]+)\s*:\s*([^;]+);', blk.group(1), re.I):
                ut.setdefault(m.group(1).lower(), ' '.join(m.group(2).split()))
    return ut


def tokens(stil):
    """[(variabel, värde, kommentar)] i Referos namnform: komponenternas :root först, sedan resten av exporten."""
    rot = rotvariabler(stil)
    ut = [(n, v, 'ur exportens komponenter') for n, v in rot.items()]
    finns = set(rot)

    def lagg(n, v, kom):
        if v and n not in finns:
            ut.append((n, v, kom))
            finns.add(n)
    for c in stil.get('colors') or []:
        if isinstance(c, dict) and re.fullmatch(r'#[0-9a-fA-F]{3,8}', str(c.get('hex') or '')):
            lagg('--color-' + slugga(c.get('name'), 'farg'), c['hex'].lower(), '%s: %s' % (c.get('name'), str(c.get('role') or '')[:90]))
    for t in stil.get('typeScale') or []:
        if not isinstance(t, dict) or not t.get('role'):
            continue
        r = slugga(t['role'])
        lagg('--text-%s' % r, forsta_tal(t.get('size')), 'typskalan: %s' % t['role'])
        if t.get('lineHeight') is not None:
            lagg('--text-%s--line-height' % r, '%g' % float(t['lineHeight']) if re.fullmatch(r'[\d.]+', str(t['lineHeight'])) else str(t['lineHeight']), '')
        if t.get('letterSpacing') is not None:
            lagg('--text-%s--letter-spacing' % r, forsta_tal(t.get('letterSpacing')), '')
    sp = stil.get('spacing') or {}
    for del_, v in (sp.get('radius') or {}).items():
        lagg('--radius-%s' % slugga(del_), forsta_tal(v), 'radie (exporten: %s)' % v)
    for nyckel, namn in (('sectionGap', 'section'), ('elementGap', 'element'), ('cardPadding', 'card'), ('baseUnit', 'unit')):
        if sp.get(nyckel) is not None:
            lagg('--space-%s' % namn, forsta_tal(sp[nyckel]), 'avstånd (exporten: %s)' % sp[nyckel])
    if sp.get('pageMaxWidth'):
        lagg('--width-page', forsta_tal(sp['pageMaxWidth']), 'sidans maxbredd')
    for i, e in enumerate(stil.get('elevation') or [], 1):
        if isinstance(e, dict) and e.get('style'):
            lagg('--shadow-%d' % i, ' '.join(str(e['style']).split()), 'skugga: %s' % str(e.get('element') or '')[:60])
    return [(n, v, k) for n, v, k in ut if v]


def css_text(stil, stil_id, tid, block=':root'):
    rader = ['/* Stilpaket ur Refero: %s (%s), hämtat %s med kontroller/stilpaket.py.' % (stil.get('title'), stil_id, tid),
             '   Originalet: ändra aldrig den här filen (DESIGN.md:s import prövar sha256); kundens anpassning skrivs i en egen fil. */',
             '%s {' % block]
    for n, v, k in tokens(stil):
        rader.append('  %s: %s;%s' % (n, v, ('  /* %s */' % k.replace('*/', '')) if k else ''))
    return '\n'.join(rader) + '\n}\n'


def beskrivning(stil, stil_id, namn, css_sha, url):
    def lista(xs):
        return ['- ' + ' '.join(str(x).split()) for x in xs or []]
    typo = []
    for t in stil.get('typography') or []:
        if isinstance(t, dict):
            fri = ' (fri ersättare: %s; exportens typsnitt är inte fritt)' % t.get('substitute') if str(t.get('source')).lower() == 'custom' and t.get('substitute') else ''
            typo.append('- **%s** %s, vikt %s, radavstånd %s; %s%s' % (t.get('family'), t.get('sizes') or '', t.get('weight') or '?', t.get('lineHeight') or '?',
                                                                     ' '.join(str(t.get('role') or '').split())[:220], fri))
    rader = ['# Stilpaket: %s' % stil.get('title'), '',
             'Referos stil `%s`%s, hämtad med `kontroller/stilpaket.py`. Det här är huvudreferensens material: variablerna i' % (stil_id, (' (%s)' % url) if url else ''),
             '`%s.css` (originalet, orört) och Tailwind-temat i `%s.tema.css`. Kundens anpassning skrivs i `%s.anpassning.css`.' % (namn, namn, namn), '',
             '**Riktningen:** %s' % ' '.join(str(stil.get('northStar') or '').split()), '', ' '.join(str(stil.get('description') or '').split()), '',
             '## Färgerna och deras roller', ''] + ['- `%s` %s: %s' % (c.get('hex'), c.get('name'), ' '.join(str(c.get('role') or '').split())) for c in stil.get('colors') or [] if isinstance(c, dict)]
    rader += ['', '## Typsnitten', ''] + typo
    rader += ['', '## Typskalan', ''] + ['- %s: %s px, radavstånd %s, teckenavstånd %s' % (t.get('role'), t.get('size'), t.get('lineHeight'), t.get('letterSpacing'))
                                         for t in stil.get('typeScale') or [] if isinstance(t, dict)]
    rader += ['', '## Layout', '', ' '.join(str(stil.get('layout') or '').split()), '', '## Bildspråk', '', ' '.join(str(stil.get('imagery') or '').split()),
              '', 'Bilder som visar verksamheten är bara dess egna (kunskap/bild.md); exportens bildspråk gäller form, beskärning och behandling.',
              '', '## Gör', ''] + lista(stil.get('dos')) + ['', '## Gör inte', ''] + lista(stil.get('donts'))
    rader += ['', '## Raden till DESIGN.md', '', '```json', json.dumps({'fil': 'src/styles/stil/%s.css' % namn,
                                                                     'kalla': 'refero: %s %s (kontroller/stilpaket.py)' % (stil.get('title'), stil_id),
                                                                     'sha256': css_sha}, ensure_ascii=False), '```', '',
              'Ett värde i DESIGN.md som kommer ur paketet får källan `importerat: refero %s` och kan peka på variabeln med `"token"`.' % stil_id, '']
    return '\n'.join(rader)


def sajtkatalog(slug, kandidat=None):
    return KUNDER / slug / ('kandidater/%s/sajt' % kandidat if kandidat else 'sajt')


def hamta(slug, stil_id, kandidat=None, namn=None, klient=None, underlag=None, sajt=None):
    """Hämtar stilen, bevarar originalet och lägger variablerna i sajten. Ger en dict med filerna och DESIGN.md-raden."""
    if not UUID.match(str(stil_id)):
        raise ValueError('stilens id ska vara Referos uuid')
    underlag = Path(underlag or UNDERLAG)
    sajt = Path(sajt or sajtkatalog(slug, kandidat))
    if not (sajt / 'package.json').is_file():
        raise ValueError('%s är ingen sajt (package.json saknas)' % sajt)
    k = klient or refero_mcp.Klient()
    if klient is None:
        k.starta()
    stil = k.json('refero_get_style', {'style_id': stil_id})
    md = k.kalla('refero_get_style', {'style_id': stil_id, 'response_format': 'md'})
    titel = stil.get('title') or stil_id
    preview, url = None, None
    try:
        for r in k.json('refero_search_styles', {'query': titel}).get('records') or []:
            if r.get('uuid') == stil_id:
                preview, url = r.get('preview_url'), r.get('url')
                break
    except refero_mcp.ReferoFel:
        pass
    tid = nu()
    rot = underlag / slug / 'referenser' / 'stilar' / stil_id
    stil_json = json.dumps(stil, ensure_ascii=False, indent=1) + '\n'
    gammal = (json.loads((rot / 'ORIGINAL.json').read_text(encoding='utf-8')) if (rot / 'ORIGINAL.json').is_file() else None)
    if gammal and gammal.get('filer', {}).get('STIL.json') != sha(stil_json):
        undan = rot / 'tidigare' / gammal.get('tid', 'okand').replace(':', '')
        undan.mkdir(parents=True, exist_ok=True)
        for p in list(rot.iterdir()):
            if p.name != 'tidigare':
                shutil.move(str(p), str(undan / p.name))
        gammal = None
    if not gammal:
        rot.mkdir(parents=True, exist_ok=True)
        (rot / 'STIL.json').write_text(stil_json, encoding='utf-8')
        (rot / 'STIL.md').write_text(md if md.endswith('\n') else md + '\n', encoding='utf-8')
        bilder = []
        if preview:
            for i in range(3):
                try:
                    bilder.append(refero_mcp.ladda_bild(re.sub(r'preview_\d', 'preview_%d' % i, preview), rot / ('preview_%d' % i)).name)
                except refero_mcp.ReferoFel:
                    break
        filer = {p.name: sha(p.read_bytes()) for p in sorted(rot.iterdir()) if p.is_file()}
        (rot / 'ORIGINAL.json').write_text(json.dumps({'stil': stil_id, 'titel': titel, 'url': url, 'preview_url': preview, 'tid': tid,
                                                       'kalla': 'Referos MCP-server (refero_get_style, json och md)', 'filer': filer},
                                                      ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        gammal = json.loads((rot / 'ORIGINAL.json').read_text(encoding='utf-8'))
    namn = slugga(namn or titel)
    stilkat = sajt / 'src' / 'styles' / 'stil'
    stilkat.mkdir(parents=True, exist_ok=True)
    css = css_text(stil, stil_id, gammal['tid'])
    (stilkat / ('%s.css' % namn)).write_text(css, encoding='utf-8')
    tema = css_text(stil, stil_id, gammal['tid'], block='@theme')
    (stilkat / ('%s.tema.css' % namn)).write_text(tema, encoding='utf-8')
    (stilkat / ('%s.STILPAKET.md' % namn)).write_text(beskrivning(stil, stil_id, namn, sha(css), url), encoding='utf-8')
    rad = {'fil': 'src/styles/stil/%s.css' % namn, 'kalla': 'refero: %s %s (kontroller/stilpaket.py)' % (titel, stil_id), 'sha256': sha(css)}
    return {'stil': stil_id, 'titel': titel, 'original': str(rot), 'css': str(stilkat / ('%s.css' % namn)), 'tema': str(stilkat / ('%s.tema.css' % namn)),
            'beskrivning': str(stilkat / ('%s.STILPAKET.md' % namn)), 'import': rad, 'tokens': len(tokens(stil)),
            'bilder': sorted(p.name for p in rot.glob('preview_*'))}


def main(argv=None):
    p = argparse.ArgumentParser(prog='stilpaket', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--stil', required=True, help='Referos stil-id (uuid)')
    p.add_argument('--kandidat', help='k01–k12: kandidatens sajt i stället för huvudsajten')
    p.add_argument('--namn', help='filnamnet i src/styles/stil/ (standard: stilens titel)')
    a = p.parse_args(argv)
    if not re.fullmatch(r'[a-z0-9-]{2,60}', a.slug) or (a.kandidat and not re.fullmatch(r'k\d{2}', a.kandidat)):
        print('slug a–z, 0–9, bindestreck; kandidaten som k01–k12', file=sys.stderr)
        return 2
    try:
        r = hamta(a.slug, a.stil, a.kandidat, a.namn)
    except (ValueError, refero_mcp.ReferoFel) as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
