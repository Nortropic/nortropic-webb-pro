#!/usr/bin/env python3
"""forhandsvisa.py — skaparens egen förhandsvisning: bygg sajten, fotografera en sida i 390 och 1440 och lägg bilderna
där skaparen läser dem.

Codex via ägaren 2026-10-05: formgivaren kunde inte se sina egna sidor innan panelen dömde dem; designloopen rendera →
titta → upptäck svagheten → rätta → titta igen saknades inom skaparsessionen. Det här är det steget, som ett kommando
skaparen själv får köra.

    .venv/bin/python kontroller/forhandsvisa.py <slug> [--kandidat kNN] [--sida /] [--mellan] [--bara-bygg]
        [--tillstand tangentbord,reflow,reducerad] [--meny SEL] [--hover SEL] [--fokus SEL] [--granskare]

Bygger kunder/<slug>/sajt (npm run build innanför processgränsen, kontroller/processgrans.py), serverar dist/ lokalt och kör inspektera.mjs i 390 och 1440 med mätningen av
typografi, färger, rytm och bilder (EXTRAKT.md). Bilderna hamnar i underlag/<slug>/forhand/<sida>/varv-NN/ (sidan
"start" för /, annars vägen med bindestreck; nästa lediga nummer), så att prototypens och ateljéns varv hålls isär.
Med --kandidat byggs och fotograferas kandidatens eget projekt (kunder/<slug>/kandidater/<id>/sajt), och varven hamnar
hos kandidaten (underlag/<slug>/atelje/kandidater/<id>/varv/<sida>/varv-NN/). --mellan tar också mellanbredderna 768 och
1280 (ägarens uppdrag 2026-10-06: pröva mellanbredder).
Skriver ut vägarna att läsa med Read, mobil först, och konsolfel och sidled-spill. Ändrar ingenting i sajten.

Interaktionsvägen (Codex via ägaren 2026-10-05, punkt 9; granskning 4, G10): --tillstand prövar tangentbordet (steg och
steg utan synlig fokus), reflow i 320 och reducerad rörelse (animationer som löper med prefers-reduced-motion: reduce),
och --meny, --hover och --fokus fotograferar elementet som CSS-väljaren pekar ut (klickad meny, hovring, fokus).
Resultaten står i FORHAND.md med bildernas vägar. En bild som saknas eller är tom (giltig_bild) står där som inte
bedömbar, så att ingen läsare tror sig ha sett den bredden.

Granskarens förhandsvisning (--granskare, med --kandidat; ägarens ord 2026-10-07: "Du behöver ju fixa luckan där med de
verktyg vi har tillgängliga"): bilderna hamnar i kritikens egen katalog,
underlag/<slug>/atelje/kandidater/<id>/granskare/<sida>/varv-NN/, aldrig i skaparens varv/, så att skaparens
varvräkning och bilderna skaparen läser är orörda. Utan andra val tar den 390, 768, 1280 och 1440, menyn klickad med
flödets menyväljare (MENYKNAPP), tangentbordet och reflow 320. Den ger ingen kod: ett bygge eller en fotografering som
faller säger bara att det föll (loggen kan visa källkod), spårfilerna (vy-*-spar.zip, med sidans byggda kod) tas bort, och
mätningen tas i granskarens form (inspektera.mjs --extrakt-utan-kod: inga CSS-regler, DOM-utdrag eller SEKTIONER.md).
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
KANDIDAT = re.compile(r'^k\d{2}$')
LAS = ('vy-390-forsta.png', 'vy-390-hela.png', 'vy-1440-forsta.png', 'vy-1440-hela.png')
BREDDER = ('390', '768', '1280', '1440')  # mobil, mellanbredderna och dator (metodkartan: proven tar de fyra)
GRANSKARE = 'granskare'  # kritikens egen katalog under kandidatens (--granskare)
# menyns stängda knapp i sidhuvudet eller navigationen, med aria-expanded eller details och summary: samma väljare i
# skissens snabba kontroll (kandidater.fotografera) och i granskarens förhandsvisning
MENYKNAPP = ', '.join(('header button[aria-expanded="false"]', 'nav button[aria-expanded="false"]',
                       'header details:not([open]) > summary', 'nav details:not([open]) > summary'))
PNG = b'\x89PNG\r\n\x1a\n'


def giltig_bild(p):
    """Är filen en hel PNG med mått: signaturen och ett IHDR med bredd och höjd över noll? En tom, avkortad eller annan fil
    är ingen bild att bedöma, och en länk följs inte (ägarens ord 2026-10-07 om skisskritiken: en tom 768-bild räknas
    aldrig som sedd)."""
    p = Path(p)
    try:
        if p.is_symlink() or not p.is_file():
            return False
        with open(p, 'rb') as f:
            huvud = f.read(24)
    except OSError:
        return False
    if len(huvud) < 24 or huvud[:8] != PNG or huvud[12:16] != b'IHDR':
        return False
    return int.from_bytes(huvud[16:20], 'big') > 0 and int.from_bytes(huvud[20:24], 'big') > 0


def sajt_for(slug, kandidat=None):
    """Projektet som byggs: sajten, eller en kandidats eget projekt i skapandeflödet."""
    return KUNDER / slug / 'kandidater' / kandidat / 'sajt' if kandidat else KUNDER / slug / 'sajt'


def varvrot(slug, sida, kandidat=None, granskare=False):
    """Varvens katalog: kandidatens varv/<sida>/, granskarens granskare/<sida>/, eller prototypens forhand/<sida>/."""
    if kandidat:
        return UNDERLAG / slug / 'atelje' / 'kandidater' / kandidat / (GRANSKARE if granskare else 'varv') / sidnamn(sida)
    return UNDERLAG / slug / 'forhand' / sidnamn(sida)


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


TILLSTAND = ('tangentbord', 'reflow', 'reducerad')
VALJARE = re.compile(r'^[A-Za-z0-9 _#.\-\[\]="\':>()*+~^$|,]{1,120}$')


def forhandsvisa(slug, sida='/', ut=None, bara_bygg=False, kandidat=None, mellan=False, tillstand=(), meny=None, hover=None, fokus=None,
                 granskare=False):
    """Bygg, fotografera och mät. Ger (rc, rapporttext, katalog). rc 0 när bilderna finns, 2 när bygget eller
    fotograferingen föll (texten säger varför). tillstand, meny, hover och fokus: interaktionsvägen. granskare: kritikens
    förhandsvisning av en kandidat, i kritikens egen katalog, med alla fyra bredderna, menyn, tangentbordet och reflow när
    inget annat anges, och utan kod i det som ges tillbaka (modulens beskrivning)."""
    if granskare and not kandidat:
        return 2, '--granskare gäller en kandidats sida: ange --kandidat kNN', None
    if granskare:
        mellan, meny, tillstand = True, meny or MENYKNAPP, tuple(tillstand) or ('tangentbord', 'reflow')
    sajt = sajt_for(slug, kandidat)
    if not (sajt / 'package.json').is_file():
        return 2, '%s saknas; %s' % (sajt.relative_to(ROOT) if sajt.is_relative_to(ROOT) else sajt,
                                     'kandidatens projekt förbereds av kontroller/kandidater.py' if kandidat else
                                     'skapa den med kontroller/ny_sajt.py %s --installera' % slug), None
    rc, out = prova.bygg_inom_grans(sajt)  # innanför processgränsen: sidornas kod körs vid bygget (omgranskningen, fynd 8)
    if rc:
        if granskare:  # byggloggen kan visa sidans källkod, som kritiken aldrig ser
            return 2, ('bygget föll (rc %d). Granskaren får inte byggloggen, eftersom den kan visa källkod; bedöm skaparens '
                       'senaste bilder och skriv att bygget föll.' % rc), None
        return 2, 'bygget föll (rc %d); rätta och kör igen:\n%s' % (rc, prova.svans(out, 30)), None
    if bara_bygg:
        return 0, 'bygget gick igenom (innanför processgränsen)', None
    if not (sajt / 'dist' / sida.strip('/') / 'index.html').is_file():
        return 2, 'sidan %s finns inte i bygget (dist%sindex.html saknas)' % (sida, sida), None
    ut = Path(ut) if ut else nasta_varv(varvrot(slug, sida, kandidat, granskare))
    ut.mkdir(parents=True, exist_ok=True)
    insp = str(prova.KONTROLLER / 'webblasare' / 'inspektera.mjs')
    with prova.Server(sajt / 'dist') as srv:
        rc, out = prova.kor([prova.NODE, insp, '--adress', srv.url + sida, '--ut', str(ut), '--vyer', ','.join(BREDDER) if mellan else '390,1440',
                             '--tillstand', ','.join(tillstand) or 'inga', '--extrahera', 'standard']
                            + (['--extrakt-utan-kod'] if granskare else [])  # kritiken får måtten, aldrig regler, DOM-utdrag eller SEKTIONER.md
                            + sum((['--%s' % n, v] for n, v in (('meny', meny), ('hover', hover), ('fokus', fokus)) if v), []), timeout=420)
    if granskare:  # spåret bär sidans byggda kod (nätverkets resurser och DOM:en); kritiken behöver det inte
        for z in ut.glob('vy-*-spar.zip'):
            z.unlink()
    saknas = [n for n in LAS if not (ut / n).is_file()]
    if saknas:
        if granskare:  # webbläsarens logg kan bära sidans skript och fel med källkod
            return 2, 'fotograferingen gav inte %s (rc %d); loggen visas inte för granskaren.' % (', '.join(saknas), rc), ut
        return 2, 'fotograferingen gav inte %s (rc %d):\n%s' % (', '.join(saknas), rc, prova.svans(out, 15)), ut
    ins = las_json(ut / 'INSPEKTION.json') or {}
    fel, spill = [], []
    for vy, r in sorted((ins.get('vyer') or {}).items()):
        fel += ['%s: %s' % (vy, str(x.get('text', ''))[:160]) for x in r.get('konsol') or [] if x.get('typ') == 'error']
        fel += ['%s sidfel: %s' % (vy, str(x.get('text', ''))[:160]) for x in r.get('sidfel') or []]
        if (r.get('spill') or {}).get('spill'):
            spill.append('%s px: scrollWidth %s' % (vy, r['spill'].get('scrollWidth')))
    beteende = []
    for vy, r in sorted((ins.get('vyer') or {}).items()):
        t = r.get('tillstand') or {}
        if 'tangentbord' in t:
            beteende.append('%s px tangentbord: %d steg, %s utan synlig fokus' % (vy, len(t.get('tangentbord') or []), t.get('tangentbord_utan_synlig_fokus')))
        if 'reflow_320' in t:
            beteende.append('%s px reflow 320: spill %s; bild %s' % (vy, (t.get('reflow_320') or {}).get('spill'), 'vy-%s-reflow320.png' % vy))
        if 'reducerad' in t:
            x = t['reducerad']
            beteende.append('%s px reducerad rörelse: %d animationer löper utan, %d med reduce%s; bild %s' % (
                vy, x.get('lopande_utan', 0), x.get('lopande_med_reduce', 0),
                (' (' + ', '.join(map(str, x.get('namn_med_reduce') or [])) + ')') if x.get('lopande_med_reduce') else '', Path(x.get('bild', '')).name))
        if 'meny' in t:  # bilden finns bara när menyn öppnades; annars skälet (inspektera.mjs, provaMeny)
            m = t['meny']
            beteende.append('%s px meny: klickad %s, expanded %s; %s' % (vy, m.get('klickad'), m.get('expanded'),
                                                                        ('bild ' + Path(m['bild']).name) if m.get('bild') else 'ingen bild: %s' % m.get('skal')))
        for n in ('hover', 'fokus'):
            if t.get(n):
                beteende.append('%s px %s: bild %s%s' % (vy, n, Path(t[n]).name, (' (fel: %s)' % t.get(n + '_fel')) if t.get(n + '_fel') else ''))
    rutor = sorted(p.name for p in ut.glob('vy-*-ruta-*.png'))
    rel = lambda p: str(Path(p).relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p)  # noqa: E731
    bild = lambda p: rel(p) if giltig_bild(p) else '%s (saknas eller är tom: inte bedömbar)' % rel(p)  # noqa: E731
    rader = ['# Förhandsvisning %s%s · %s%s' % ('(granskarens) ' if granskare else '', ut.name, slug, sida), '',
             'Läs med Read, i den här ordningen: mobilens första vy, mobilens hela sida, datorns första vy, datorns hela sida.',
             '(Ge kommandot tidsgränsen 600000 ms: bygget och fotograferingen tar en till två minuter.)',
             *['- ' + bild(ut / n) for n in LAS],
             *(['Mellanbredderna 768 och 1280 (en dator som är smalare än 1440): ' + ', '.join(bild(ut / ('vy-%s-%s.png' % (v, n))) for v in ('768', '1280')
                                                                                             for n in ('forsta', 'hela'))] if mellan else []),
             'Skärmhöga rutor uppifrån och ned (läs dem för detaljerna): ' + (', '.join(rutor) or 'inga'),
             'Mätningen (typografi, färger, rytm, bilder och beskärning): ' + rel(ut / 'EXTRAKT.md'),
             'Konsolfel: ' + ('; '.join(fel[:5]) if fel else 'inga'),
             'Sidled-spill: ' + ('; '.join(spill) if spill else 'inget'),
             *(['Interaktionsvägen (bilderna i samma katalog; läs dem med Read):'] + ['- ' + x for x in beteende] if beteende else []), '']
    (ut / 'FORHAND.md').write_text('\n'.join(rader), encoding='utf-8')
    return 0, '\n'.join(rader), ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='forhandsvisa', description=__doc__.split('\n\n')[0], allow_abbrev=False)  # --kand k02 är ingen annan kandidat (granskning 2, N8)
    p.add_argument('slug')
    p.add_argument('--sida', default='/')
    p.add_argument('--kandidat', default=None, help='en kandidats eget projekt i skapandeflödet (k01–k12)')
    p.add_argument('--mellan', action='store_true', help='också mellanbredderna 768 och 1280')
    p.add_argument('--bara-bygg', action='store_true', help='bygg sajten innanför processgränsen utan att fotografera')
    p.add_argument('--tillstand', default='', help='interaktionsvägen: tangentbord, reflow, reducerad (kommaseparerat)')
    p.add_argument('--meny', help='CSS-väljare för menyns knapp: klickas och fotograferas')
    p.add_argument('--hover', help='CSS-väljare: hovring fotograferas')
    p.add_argument('--fokus', help='CSS-väljare: fokus fotograferas')
    p.add_argument('--granskare', action='store_true', help='kritikens förhandsvisning av en kandidat: egen katalog, fyra bredder, ingen kod')
    ra = list(sys.argv[1:] if argv is None else argv)
    if any(sum(1 for x in ra if x == f or x.startswith(f + '=')) > 1 for f in ('--kandidat', '--sida', '--tillstand', '--meny', '--hover', '--fokus')):
        # en skapare får bara bygga sin egen kandidat: argparse tar den sista av upprepade flaggor (granskningen M2)
        print('--kandidat och --sida får anges en gång', file=sys.stderr)
        return 2
    a = p.parse_args(argv)
    if not SLUG.fullmatch(a.slug) or not SIDA.fullmatch(a.sida) or (a.kandidat and not KANDIDAT.fullmatch(a.kandidat)):
        print('slug a–z, 0–9, bindestreck; sidan som /väg/ med snedstreck sist; kandidaten som k01–k12', file=sys.stderr)
        return 2
    if a.granskare and not a.kandidat:
        print('--granskare gäller en kandidats sida: ange --kandidat kNN', file=sys.stderr)
        return 2
    tillstand = tuple(x for x in a.tillstand.split(',') if x)
    if any(x not in TILLSTAND for x in tillstand) or any(v is not None and not VALJARE.fullmatch(v) for v in (a.meny, a.hover, a.fokus)):
        print('tillstand: %s (kommaseparerat); --meny, --hover och --fokus: en CSS-väljare utan semikolon eller klamrar' % ', '.join(TILLSTAND), file=sys.stderr)
        return 2
    rc, text, _ = forhandsvisa(a.slug, a.sida, bara_bygg=a.bara_bygg, kandidat=a.kandidat, mellan=a.mellan,
                               tillstand=tillstand, meny=a.meny, hover=a.hover, fokus=a.fokus, granskare=a.granskare)
    print(text)
    return rc


if __name__ == '__main__':
    sys.exit(main())
