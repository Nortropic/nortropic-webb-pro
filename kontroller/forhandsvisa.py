#!/usr/bin/env python3
"""forhandsvisa.py — skaparens egen förhandsvisning: bygg sajten, fotografera en sida i 390 och 1440 och lägg bilderna
där skaparen läser dem.

Codex via ägaren 2026-10-05: formgivaren kunde inte se sina egna sidor innan panelen dömde dem; designloopen rendera →
titta → upptäck svagheten → rätta → titta igen saknades inom skaparsessionen. Det här är det steget, som ett kommando
skaparen själv får köra.

    .venv/bin/python kontroller/forhandsvisa.py <slug> [--sida /] [--bara-bygg]

Bygger kunder/<slug>/sajt (npm run build innanför processgränsen, kontroller/processgrans.py), serverar dist/ lokalt och kör inspektera.mjs i 390 och 1440 med mätningen av
typografi, färger, rytm och bilder (EXTRAKT.md). Bilderna hamnar i underlag/<slug>/forhand/<sida>/varv-NN/ (sidan
"start" för /, annars vägen med bindestreck; nästa lediga nummer), så att prototypens och ateljéns varv hålls isär.
Skriver ut vägarna att läsa med Read, mobil först, och konsolfel och sidled-spill. Ändrar ingenting i sajten.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prova  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KUNDER = ROOT / 'kunder'
UNDERLAG = ROOT / 'underlag'
SLUG = re.compile(r'^[a-z0-9-]{2,60}$')
SIDA = re.compile(r'^/(?:[a-z0-9-]+/)*$')
LAS = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')


def las_json(p):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def sidnamn(sida):
    return 'start' if sida == '/' else sida.strip('/').replace('/', '-')


def varv(rot):
    """Varvens kataloger i nummerordning (varv-01, varv-02 … varv-100)."""
    nr = [(int(m.group(1)), p) for p in Path(rot).glob('varv-*') if p.is_dir() and (m := re.match(r'^varv-(\d{2,})$', p.name))]
    return [p for _, p in sorted(nr)]


def hela(kat):
    """Varvet har alla fyra bilderna (en fotografering som föll lämnar en halv katalog)."""
    return all((Path(kat) / n).is_file() for n in LAS)


def nasta_varv(rot):
    nr = [int(p.name.split('-')[1]) for p in varv(rot)]
    return Path(rot) / ('varv-%02d' % (max(nr or [0]) + 1))


def forhandsvisa(slug, sida='/', ut=None, bara_bygg=False):
    """Bygg, fotografera och mät. Ger (rc, rapporttext, katalog). rc 0 när bilderna finns, 2 när bygget eller
    fotograferingen föll (texten säger varför)."""
    sajt = KUNDER / slug / 'sajt'
    if not (sajt / 'package.json').is_file():
        return 2, 'kunder/%s/sajt saknas; skapa den med kontroller/ny_sajt.py %s --installera' % (slug, slug), None
    rc, out = prova.bygg_inom_grans(sajt)  # innanför processgränsen: sidornas kod körs vid bygget (omgranskningen, fynd 8)
    if rc:
        return 2, 'bygget föll (rc %d); rätta och kör igen:\n%s' % (rc, prova.svans(out, 30)), None
    if bara_bygg:
        return 0, 'bygget gick igenom (innanför processgränsen)', None
    if not (sajt / 'dist' / sida.strip('/') / 'index.html').is_file():
        return 2, 'sidan %s finns inte i bygget (dist%sindex.html saknas)' % (sida, sida), None
    ut = Path(ut) if ut else nasta_varv(UNDERLAG / slug / 'forhand' / sidnamn(sida))
    ut.mkdir(parents=True, exist_ok=True)
    insp = str(prova.KONTROLLER / 'webblasare' / 'inspektera.mjs')
    with prova.Server(sajt / 'dist') as srv:
        rc, out = prova.kor([prova.NODE, insp, '--adress', srv.url + sida, '--ut', str(ut), '--vyer', '390,1440',
                             '--tillstand', 'inga', '--extrahera', 'standard'], timeout=300)
    saknas = [n for n in LAS if not (ut / n).is_file()]
    if saknas:
        return 2, 'fotograferingen gav inte %s (rc %d):\n%s' % (', '.join(saknas), rc, prova.svans(out, 15)), ut
    ins = las_json(ut / 'INSPEKTION.json') or {}
    fel, spill = [], []
    for vy, r in sorted((ins.get('vyer') or {}).items()):
        fel += ['%s: %s' % (vy, str(x.get('text', ''))[:160]) for x in r.get('konsol') or [] if x.get('typ') == 'error']
        fel += ['%s sidfel: %s' % (vy, str(x.get('text', ''))[:160]) for x in r.get('sidfel') or []]
        if (r.get('spill') or {}).get('spill'):
            spill.append('%s px: scrollWidth %s' % (vy, r['spill'].get('scrollWidth')))
    rutor = sorted(p.name for p in ut.glob('vy-*-ruta-*.png'))
    rel = lambda p: str(Path(p).relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p)  # noqa: E731
    rader = ['# Förhandsvisning %s · %s%s' % (ut.name, slug, sida), '',
             'Läs med Read, i den här ordningen: mobilens första vy, mobilens hela sida, datorns första vy, datorns hela sida.',
             '(Ge kommandot tidsgränsen 600000 ms: bygget och fotograferingen tar en till två minuter.)',
             *['- ' + rel(ut / n) for n in LAS],
             'Skärmhöga rutor uppifrån och ned (läs dem för detaljerna): ' + (', '.join(rutor) or 'inga'),
             'Mätningen (typografi, färger, rytm, bilder och beskärning): ' + rel(ut / 'EXTRAKT.md'),
             'Konsolfel: ' + ('; '.join(fel[:5]) if fel else 'inga'),
             'Sidled-spill: ' + ('; '.join(spill) if spill else 'inget'), '']
    (ut / 'FORHAND.md').write_text('\n'.join(rader), encoding='utf-8')
    return 0, '\n'.join(rader), ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='forhandsvisa', description=__doc__.split('\n\n')[0])
    p.add_argument('slug')
    p.add_argument('--sida', default='/')
    p.add_argument('--bara-bygg', action='store_true', help='bygg sajten innanför processgränsen utan att fotografera')
    a = p.parse_args(argv)
    if not SLUG.match(a.slug) or not SIDA.match(a.sida):
        print('slug a–z, 0–9, bindestreck; sidan som /väg/ med snedstreck sist', file=sys.stderr)
        return 2
    rc, text, _ = forhandsvisa(a.slug, a.sida, bara_bygg=a.bara_bygg)
    print(text)
    return rc


if __name__ == '__main__':
    sys.exit(main())
