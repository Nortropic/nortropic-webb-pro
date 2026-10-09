#!/usr/bin/env python3
"""Kalibreringsförsöket: granskaren prövas på de undanhållna kalibreringsexemplen (externa sajter som ägaren dömt blint i
tre nivåer; backlogposten om kalibrering av visuell nivå) med dagens kritik/GRANSKARE.md och kalibreringsankarna. Måttet:
falska godkännanden (granskaren godkänner det ägaren kallade nästan eller generisk) och falska underkännanden (granskaren
underkänner tydligt över ribban).

    .venv/bin/python kontroller/granskarforsok/kalibrering.py [--torr] [--parallellt N] [--modell M] [--effort E] [--frist S]

Utdata utanför repot, under $NWP_FORSOK eller /tmp/nwp-granskarforsok, i kalibrering/: per exempel de frysta bilderna,
ankarna, PROMPT.txt, MANIFEST.json (modell, effort och hashar av uppdraget, bedömningsreglerna, bilderna och ankarna),
KORNING.json (anropets slutkod) och svar.json; RAPPORT.json och RAPPORT.md med måtten. Återupptagbart: ett svar återanvänds
bara när manifestet är identiskt och svaret validerar mot hela schemat (Codex R30). Anropsfel och ofullständiga svar räknas
aldrig som domar: de redovisas separat som ofullständigt försök och ger slutkod 1. Granskaren får bara se exemplets frysta
bilder, ankarna och mekaniken; underlag/, kunder/, LARDOMAR.md och hemmets .claude nekas. Siffran (utan sajternas namn)
skrivs av sessionen i LARDOMAR.md. Måttstocken kunskap/visuell-niva.md byggs enbart ur ankarhalvan; ett oberoende slutmått
kräver ett nytt, orört urval (Codex R30: testdata får inte påverka reglerna som utvärderas). Metoden fryses med bilderna
(Codex R31): granskartexten, schemana och måttstockarna kopieras till <exempel>/metod/ och granskaren körs därifrån, med
schemat ur kopian och det riktiga repot oläsbart, så att manifestet beskriver exakt det granskaren såg. Svaret valideras
mot hela schemat (typer, obligatoriska fält, enum, gränser, nästlade objekt); ett oläsbart schema är ett försöksfel.

Rapporten (ägarens uppdrag 2026-10-07, punkt 8) anger nivåfilens sha256 och läckageprovets utfall. Exemplen kallas
undanhållna bara när läckageprovet faktiskt prövat texter, nivåfilen bland dem, och inte funnit några ordagranna spår;
annars är siffran utvecklingsdata (fältet giltighet i RAPPORT.json). Provet fångar inte en omskriven destillering, och
rapporten säger det. En äldre rapport rättas med ett daterat block överst och giltigheten i RAPPORT.json;
ursprungsresultatet står kvar, och den ursprungliga RAPPORT.json sparas ordagrant i rättelsen:

    .venv/bin/python kontroller/granskarforsok/kalibrering.py --ratta <katalog> --datum ÅÅÅÅ-MM-DD --skal "…" \
        [--giltighet utvecklingsdata] [--hanvisning "…"]… [--uppdrag "…"] [--atgard "…"]…

Frysningen före domarna (ägarens uppdrag 2026-10-09, punkt 2: frys modell, instruktioner, kriterier, ankare och bilder före
utvärderingen, och använd inte domarna för att ändra måttstocken före det oberoende försöket):

    .venv/bin/python kontroller/granskarforsok/kalibrering.py --frys --bara K14,K15,K16,K17,K18,K19 [--modell M] [--effort E]

skriver underlag/kalibrering/FRYSNING-<id>.json med modell, effort, sha256 för granskarens metodfiler, ankarna, exemplens
bilder och tillgänglighetsträd, undersidans anteckning och koden som skriver det granskaren läser. En frysning skrivs inte om. Försöket med
samma --bara jämför läget med frysningen: har något ändrats sedan dess, eller saknas frysningen, stannar det med listan,
och med --trots-frysning körs det men räknas som utvecklingsdata. Ägarens domar ingår aldrig i frysningen.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import granska as gr  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HEM = str(Path.home())
EJ_ANGIVET = 'ej angivet'
G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok') / 'kalibrering'
VYER = ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png')
NEKAS_EXTRA = ['Read(%s/**)' % ROOT, 'Read(%s/.claude/**)' % HEM]  # granskaren ser bara sin katalog: bilderna, ankarna och metodkopian
METODFILER_MONSTER = r'(?:kunskap|kritik)/[A-Za-z0-9_./-]+\.(?:md|json)'
NIVAFIL = 'kunskap/visuell-niva.md'
LACKAGE_ORD = 8  # så många ord i följd ur ägarens dom över ett prövat exempel, i det granskaren läser, är läckage
LACKAGE_GRANS = ('Provet fångar bara ordagranna spår av de prövade exemplen (id och ordföljder ur ägarens domar) i det '
                 'granskaren läser, inte en omskriven destillering av domarna, som den som fällde försöket 2026-10-04 '
                 '(Codex R30). Ett oberoende slutmått kräver dessutom ett orört urval som döms efter att metoden frysts.')


def undanhallna(underlag=None):
    return [e for e in gr.kalibreringsexempel(underlag) if not e['ankare'] and e['bilder']]


def forbered(e, ut, underlag=None):
    """Exemplets bilder (start och undersida: första vyn 390/1440, hela 390, rutorna) och tillgänglighetsträd kopierade till
    ut/sajt/, ankarna frysta i ut/ (som i en omgång). Ger (bilder, aria, ankare)."""
    rot = Path(underlag or gr.UNDERLAG) / 'kalibrering'
    ut = Path(ut)
    bilder, aria = [], []
    for sida in ('start', 'undersida'):
        kalla = rot / e['id'] / sida
        if not kalla.is_dir():
            continue
        mal = ut / 'sajt' / sida
        mal.mkdir(parents=True, exist_ok=True)
        for fil in sorted(kalla.iterdir()):
            if fil.suffix == '.png' and (fil.name in VYER or '-ruta-' in fil.name) or fil.name.endswith('-aria.txt'):
                shutil.copy2(gr.sakert_original(fil, rot), mal / fil.name)
                (aria if fil.suffix == '.txt' else bilder).append(mal / fil.name)
    return bilder, aria, gr.frysta_ankare(ut, underlag)


def undersidans_not(ident, underlag=None):
    """Anteckningen i underlag/kalibrering/<id>/UNDERSIDA.txt: undersidans adress, eller "ingen: …" för en ensidig sajt."""
    try:
        return (Path(underlag or gr.UNDERLAG) / 'kalibrering' / ident / 'UNDERSIDA.txt').read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def uppdrag(e, ut, bilder, aria, ankare, underlag=None):
    rad = lambda p: '- ' + str(p)  # noqa: E731
    med_undersida = any('/sajt/undersida/' in str(p) for p in bilder)
    not_ = undersidans_not(e['id'], underlag)
    trosklar = ', '.join('%s ≥ %d' % (k, gr.TROSKEL[k]) for k in gr.KRITERIER)
    delar = [
        'Du är granskaren. Läs %s först och följ den. Du ändrar inga filer.' % gr.INSTRUKTION, '',
        'Det här är ett kalibreringsförsök: sajten är en befintlig extern webbplats, inte vårt bygge, och den finns inte live',
        'här. Döm den från skärmbilderna och tillgänglighetsträden nedan, som ägaren gjorde, på samma fem kriterier. Inget',
        'underlag om verksamheten finns; döm verksamhetens egen närvaro ur sajten. Skriv "ej tillämpligt" under likhet_tidigare,',
        'och i prototypjamforelse status ingen_prototyp: det finns ingen godkänd prototyp att jämföra med.', '',
        'Din arbetskatalog: %s. Metoden (granskartexten, måttstockarna, schemat) ligger fryst i %s, som är din arbetsrot;' % (ut, Path(ut) / 'metod'),
        'läs den därifrån och ingenting utanför din arbetskatalog.',
        'Trösklar för godkänt: %s, och inga blockerande fynd. Godkännandet räknas ut av verktyget.' % trosklar, '',
        'Ribban är professionell nivå enligt kalibreringsankarna och exemplaren i kunskap/referenser-professionella.md.', '',
        *(['Kalibreringsankare: externa sajter som ägaren dömt blint (%s). Ägarens ord om vad som skiljer, ordagrant: %s' % (gr.KALIBRERING_SKALA, ankare[0]),
           'Första vyn 390 och 1440 per sajt (läs varje, med ägarens ord bredvid):', *[rad(p) + ' — ' + t for p, t in ankare[1]], '']
          if ankare else []),
        ('Sajtens skärmbilder: startsidan och en undersida, första vyn i 390 och 1440, hela sidan i 390 och skärmhöga rutor (läs varje):'
         if med_undersida else 'Sajtens skärmbilder: startsidan, första vyn i 390 och 1440, hela sidan i 390 och skärmhöga rutor (läs varje). '
         'Sajten har ingen undersida att döma%s:' % ((' (' + not_.split(':', 1)[1].strip() + ')') if not_.lower().startswith('ingen:') else '')),
        *[rad(p) for p in bilder], '',
        'Tillgänglighetsträd:', *([rad(p) for p in aria] or ['- saknas']), '',
        'Måttstockar:', *['- %s: %s' % (namn, f) for namn, f in gr.MATTSTOCKAR if (ROOT / f).is_file()],
    ]
    return '\n'.join(delar) + '\n'


def hash_fil(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def metodfiler():
    """Granskartexten, schemana, måttstockarna och de kunskaps- och kritikfiler de pekar på (ett led): det granskaren
    får läsa om metoden, alla relativt repots rot."""
    ut = [gr.INSTRUKTION, 'kritik/' + gr.SCHEMA.name, 'kritik/' + gr.SCHEMA_ORIGINALITET.name] + [f for _, f in gr.MATTSTOCKAR]  # schemana ligger i kritik/ (namnen ur granska, vägarna relativt repot)
    for f in list(ut):
        p = ROOT / f
        if p.is_file() and p.suffix == '.md':
            ut += [m for m in re.findall(METODFILER_MONSTER, p.read_text(encoding='utf-8', errors='replace'))]
    return [f for f in dict.fromkeys(ut) if (ROOT / f).is_file()]


def frys_metod(ut):
    """Metoden kopierad till ut/metod/ med samma relativa vägar som i repot: granskaren körs med den katalogen som
    arbetsrot, läser 'kritik/GRANSKARE.md' därifrån och får schemat ur kopian. Ger {relativ väg: fryst Path}."""
    mal = Path(ut) / 'metod'
    frysta = {}
    for f in metodfiler():
        kopia = mal / f
        kopia.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gr.sakert_original(ROOT / f, ROOT), kopia)
        frysta[f] = kopia
    return frysta


def fryst_schema(ut):
    return Path(ut) / 'metod' / 'kritik' / gr.SCHEMA.name


def las_schema(p):
    """Schemat som ett objekt; oläsbart eller ogiltigt schema är ett försöksfel, aldrig ett godkänt svar (Codex R31)."""
    try:
        schema = json.loads(Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise RuntimeError('schemat %s går inte att läsa: %s' % (p, e))
    if not isinstance(schema, dict) or not isinstance(schema.get('required'), list) or 'properties' not in schema:
        raise RuntimeError('schemat %s saknar required/properties' % p)
    return schema


TYPER = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'null': type(None)}


def schemafel(schema, varde, rot=None, vag='$'):
    """Första avvikelsen från schemat (type, required, properties, additionalProperties, items, maxItems, enum,
    minimum, maximum, $ref till #/$defs/…), eller None. Täcker det SCHEMA-granskning.json använder."""
    rot = schema if rot is None else rot
    if '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/'):
            return '%s: okänd referens %s' % (vag, ref)
        mal = rot
        for led in ref[2:].split('/'):
            mal = mal.get(led) if isinstance(mal, dict) else None
        if not isinstance(mal, dict):
            return '%s: referensen %s saknas' % (vag, ref)
        return schemafel(mal, varde, rot, vag)
    typ = schema.get('type')
    if typ is not None:
        typer = typ if isinstance(typ, list) else [typ]
        ok = False
        for t in typer:
            if t == 'integer':
                ok = ok or (isinstance(varde, int) and not isinstance(varde, bool))
            elif t == 'number':
                ok = ok or (isinstance(varde, (int, float)) and not isinstance(varde, bool))
            elif t in TYPER:
                ok = ok or isinstance(varde, TYPER[t])
        if not ok:
            return '%s: fel typ (väntade %s)' % (vag, typ)
    if 'enum' in schema and varde not in schema['enum']:
        return '%s: värdet ingår inte i %s' % (vag, schema['enum'])
    if isinstance(varde, (int, float)) and not isinstance(varde, bool):
        if 'minimum' in schema and varde < schema['minimum']:
            return '%s: under %s' % (vag, schema['minimum'])
        if 'maximum' in schema and varde > schema['maximum']:
            return '%s: över %s' % (vag, schema['maximum'])
    if isinstance(varde, dict):
        for k in schema.get('required', []):
            if k not in varde:
                return '%s: fältet %s saknas' % (vag, k)
        egenskaper = schema.get('properties', {})
        for k, v in varde.items():
            if k in egenskaper:
                fel = schemafel(egenskaper[k], v, rot, '%s.%s' % (vag, k))
                if fel:
                    return fel
            elif schema.get('additionalProperties') is False:
                return '%s: okänt fält %s' % (vag, k)
    if isinstance(varde, list):
        if 'maxItems' in schema and len(varde) > schema['maxItems']:
            return '%s: fler än %d poster' % (vag, schema['maxItems'])
        if 'minItems' in schema and len(varde) < schema['minItems']:
            return '%s: färre än %d poster' % (vag, schema['minItems'])
        if isinstance(schema.get('items'), dict):
            for i, v in enumerate(varde):
                fel = schemafel(schema['items'], v, rot, '%s[%d]' % (vag, i))
                if fel:
                    return fel
    return None


def manifest(ut, modell, effort, prompt, bilder, aria, ankare, frysta):
    """Det ett svar är bundet till: modell, effort och hashar av uppdraget, den frysta metoden (granskartexten, schemana,
    måttstockarna som kopierats till ut/metod och som granskaren faktiskt läser), exemplets bilder och ankarna. Bara ett
    identiskt manifest får återanvända ett svar (Codex R30/R31)."""
    ut = Path(ut)
    regler = {f: hash_fil(p) for f, p in sorted(frysta.items())}
    ank = {}
    if ankare:
        ank[str(ankare[0].relative_to(ut))] = hash_fil(ankare[0])
        ank.update({str(p.relative_to(ut)): hash_fil(p) for p, _ in ankare[1]})
    return {'modell': modell, 'effort': effort, 'prompt': hashlib.sha256(prompt.encode('utf-8')).hexdigest(), 'regler': regler,
            'bilder': {str(p.relative_to(ut)): hash_fil(p) for p in list(bilder) + list(aria)}, 'ankare': ank}


def validera(svar, schema):
    """Hela svaret prövas före återanvändning och jämförelse: anropet lyckat (ingen is_error, subtype success) och ett
    strukturerat svar som följer hela schemat (typer, obligatoriska fält, enum, gränser, nästlade objekt, inga okända fält),
    plus de fem kriterierna med betyg 1–10 som granskningen räknar på. Ger (structured_output, None) eller (None, fel)."""
    if not isinstance(svar, dict):
        return None, 'inget svar'
    if svar.get('is_error') or svar.get('subtype') not in (None, 'success'):
        return None, 'anropet misslyckades (%s)' % (svar.get('subtype') or 'is_error')
    res = svar.get('structured_output')
    if not isinstance(res, dict):
        return None, 'inget strukturerat svar'
    fel = schemafel(schema, res)
    if fel:
        return None, 'svaret följer inte schemat: ' + fel
    k = res.get('kriterier') or {}
    for n in gr.KRITERIER:
        b = k.get(n)
        if (not isinstance(b, dict) or not isinstance(b.get('betyg'), int) or isinstance(b.get('betyg'), bool)
                or not 1 <= b['betyg'] <= 10 or not isinstance(b.get('visa'), bool) or not isinstance(b.get('motivering'), str)):
            return None, 'kriteriet %s är ofullständigt' % n
    return res, None


def giltigt_svar(ut):
    """Exemplets svar om anropet lyckades (KORNING.json: slutkod 0) och svaret validerar mot det frysta schemat; annars
    (None, fel). Ett oläsbart fryst schema är ett försöksfel (RuntimeError)."""
    korning = gr.las_json(Path(ut) / 'KORNING.json') or {}
    if korning.get('slutkod') != 0:
        return None, 'anropet gav slutkod %s' % korning.get('slutkod', 'okänd')
    return validera(gr.las_json(Path(ut) / 'svar.json'), las_schema(fryst_schema(ut)))


def claude_args(ut, modell, effort, claude):
    """Granskarens anrop: schemat ur den frysta kopian, arbetsroten metodkopian (cwd), bara exemplets katalog läsbar."""
    return [claude, '-p', '--max-turns', '120', '--permission-mode', 'dontAsk', '--output-format', 'json',
            '--setting-sources', 'project,local', '--strict-mcp-config', '--model', modell, '--effort', effort,
            '--json-schema', fryst_schema(ut).read_text(encoding='utf-8'), '--add-dir', str(ut),
            '--allowedTools', 'Read', 'Glob', 'Grep', 'Bash(ls *)', '--disallowedTools', *gr.NEKAS, *NEKAS_EXTRA]


def kor_en(e, ut, modell, effort, frist, claude):
    prompt = (ut / 'PROMPT.txt').read_text(encoding='utf-8')
    args = claude_args(ut, modell, effort, claude)
    t0 = time.time()
    slutkod = None
    with open(ut / 'svar.json', 'wb') as sv, open(ut / 'stderr.log', 'wb') as err:
        try:
            slutkod = subprocess.run(args, input=prompt.encode(), stdout=sv, stderr=err, cwd=str(ut / 'metod'), env=gr.ren_miljo(), timeout=frist).returncode
        except subprocess.TimeoutExpired:
            slutkod = 'tidsgräns'
    (ut / 'KORNING.json').write_text(json.dumps({'slutkod': slutkod, 'sekunder': round(time.time() - t0), 'tid': gr.nu()}) + '\n', encoding='utf-8')
    return e['id'], round(time.time() - t0)


FRYSNING = 'FRYSNING-%s.json'


def frysningens_lage(ids, modell, effort, underlag=None):
    """Det som frysningen binder, räknat nu: modell, effort, granskarens metodfiler, ankarna (bilder och ägarens ord om
    dem), exemplens bilder och tillgänglighetsträd, undersidans anteckning och koden som skriver det granskaren läser
    (uppdraget, ankarnas text, kriterierna och trösklarna). Aldrig ägarens domar över de prövade exemplen."""
    rot = Path(underlag or gr.UNDERLAG) / 'kalibrering'
    ex = {}
    for ident in ids:
        filer = {}
        for sida in ('start', 'undersida'):
            for fil in sorted((rot / ident / sida).iterdir()) if (rot / ident / sida).is_dir() else []:
                if fil.suffix == '.png' and (fil.name in VYER or '-ruta-' in fil.name) or fil.name.endswith('-aria.txt'):
                    filer['%s/%s' % (sida, fil.name)] = hash_fil(fil)
        ex[ident] = {'filer': filer, 'undersida': undersidans_not(ident, underlag)}
    ank = {e['id']: {'skiljer': hashlib.sha256(e['skiljer'].encode('utf-8')).hexdigest(), 'niva': e['niva'],
                     'bilder': {b.name: hash_fil(b) for b in e['bilder']}}
           for e in gr.kalibreringsexempel(underlag) if e['ankare']}
    import inspect
    sha = lambda t: hashlib.sha256(t.encode('utf-8')).hexdigest()  # noqa: E731
    kod = {'kalibrering.uppdrag': sha(inspect.getsource(uppdrag)), 'kalibrering.forbered': sha(inspect.getsource(forbered)),
           'granska.frysta_ankare': sha(inspect.getsource(gr.frysta_ankare)),
           'granska.kriterier': sha(json.dumps([list(gr.KRITERIER), gr.TROSKEL, gr.KALIBRERING_SKALA, gr.KALIBRERING_NIVAER, str(gr.INSTRUKTION),
                                                [list(x) for x in gr.MATTSTOCKAR]], ensure_ascii=False, sort_keys=True, default=str))}
    return {'id': list(ids), 'modell': modell, 'effort': effort, 'regler': {f: hash_fil(ROOT / f) for f in metodfiler()},
            'ankare': ank, 'exempel': ex, 'kod': kod}


def frysningsfil(ids, underlag=None):
    return Path(underlag or gr.UNDERLAG) / 'kalibrering' / (FRYSNING % '-'.join(ids))


def frys(ids, modell, effort, underlag=None):
    """Skriver frysningen före ägarens domar; en befintlig frysning skrivs aldrig om. Ger filen."""
    f = frysningsfil(ids, underlag)
    if f.exists():
        raise ValueError('frysningen finns redan (%s) och skrivs inte om' % f.name)
    domar = gr.las_json(f.parent / 'DOMAR.json') or {}
    domda = [i for i in ids if i in domar]
    lage = dict(frysningens_lage(ids, modell, effort, underlag), tid=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                domda_vid_frysningen=domda)
    f.write_text(json.dumps(lage, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return f


def frysningsbrott(ids, modell, effort, underlag=None):
    """None när läget är det frysta, annars listan med det som skiljer (en saknad frysning är ett brott)."""
    f = frysningsfil(ids, underlag)
    fryst = gr.las_json(f) if f.is_file() else None
    if not isinstance(fryst, dict):
        return ['ingen frysning före domarna (%s)' % f.name]
    nu_ = frysningens_lage(ids, modell, effort, underlag)
    ut = []
    for nyckel in ('modell', 'effort', 'regler', 'ankare', 'exempel', 'kod'):
        if fryst.get(nyckel) != nu_.get(nyckel):
            if isinstance(nu_.get(nyckel), dict) and isinstance(fryst.get(nyckel), dict):
                andrade = sorted(k for k in set(fryst[nyckel]) | set(nu_[nyckel]) if fryst[nyckel].get(k) != nu_[nyckel].get(k))
                ut.append('%s: %s' % (nyckel, ', '.join(andrade[:8])))
            else:
                ut.append('%s: %s fryst, %s nu' % (nyckel, fryst.get(nyckel), nu_.get(nyckel)))
    if fryst.get('domda_vid_frysningen'):
        ut.append('frysningen gjordes efter domar över %s' % ', '.join(fryst['domda_vid_frysningen']))
    return ut or None


def jamfor(exempel, svar, schema=None):
    """Granskarens utfall mot ägarens nivå. svar: {id: hela svaret från claude (eller (structured_output, fel))}. Ett svar som
    inte validerar mot schemat räknas som ofullständigt försök, aldrig som dom. Ger (rader, sammanfattning)."""
    rader = []
    for e in exempel:
        v = svar.get(e['id'])
        res, fel = v if isinstance(v, tuple) else validera(v, schema if schema is not None else las_schema(gr.SCHEMA))
        if fel:
            rader.append({'id': e['id'], 'agaren': e['niva'], 'granskaren': None, 'utfall': 'ofullständigt: ' + fel})
            continue
        godk = gr.godkand(res)
        betyg = {k: (res['kriterier'].get(k) or {}).get('betyg') for k in gr.KRITERIER}
        if godk and e['niva'] != 'over':
            utfall = 'falskt godkännande'
        elif not godk and e['niva'] == 'over':
            utfall = 'falskt underkännande'
        else:
            utfall = 'rätt'
        rader.append({'id': e['id'], 'agaren': e['niva'], 'granskaren': 'godkänd' if godk else 'underkänd', 'niva': gr.niva(res),
                      'betyg': betyg, 'blockerande': len(res.get('blockerande') or []), 'utfall': utfall})
    ej_over = [r for r in rader if r['agaren'] != 'over' and r['granskaren']]
    over = [r for r in rader if r['agaren'] == 'over' and r['granskaren']]
    s = {'undanhallna': len(exempel), 'svar': sum(1 for r in rader if r['granskaren']), 'ofullstandiga': sum(1 for r in rader if not r['granskaren']),
         'falska_godkannanden': sum(1 for r in ej_over if r['utfall'] == 'falskt godkännande'), 'av_ej_over': len(ej_over),
         'falska_underkannanden': sum(1 for r in over if r['utfall'] == 'falskt underkännande'), 'av_over': len(over)}
    return rader, s


def _ord(text):
    return re.findall(r'[0-9a-zåäöéüæø]+', str(text or '').lower())


def lackageprov(exempel, texter, n=LACKAGE_ORD):
    """Läckageprovet: har de prövade exemplens facit nått det granskaren läser? texter är {namn: text} för metoden och de
    frysta ankarna. Prövar varje exempels id (K01 …) och varje följd om n ord ur ägarens dom över exemplet. Det går igenom
    bara när det faktiskt prövat något: minst ett exempel, minst en text och nivåfilen bland texterna; annars är det ej
    prövat (granskningen av r101, BÖR 8). Ett exempel utan så många ord i domen kan inte prövas, och då går provet inte
    igenom. Provet fångar bara ordagranna spår, inte en omskriven destillering (begransning). Ger {'ok', 'status',
    'provat', 'texter', 'traffar', 'ej_provade', 'begransning'}."""
    traffar, ej = [], []
    norm = {namn: ' %s ' % ' '.join(_ord(x)) for namn, x in texter.items()}
    for e in exempel:
        for namn, x in texter.items():
            if re.search(r'(?<![0-9A-Za-z])%s(?![0-9A-Za-z])' % re.escape(e['id']), x or ''):
                traffar.append({'id': e['id'], 'fil': namn, 'fynd': 'exemplets id'})
        ord_ = _ord(e.get('skiljer'))
        if len(ord_) < n:
            ej.append(e['id'])
            continue
        for i in range(len(ord_) - n + 1):
            fras = ' '.join(ord_[i:i + n])
            namn = next((m for m, x in norm.items() if ' %s ' % fras in x), None)
            if namn:
                traffar.append({'id': e['id'], 'fil': namn, 'fynd': 'ordföljd ur ägarens dom'})
                break
    saknas = [x for x, brist in (('inga exempel', not exempel), ('inga texter', not texter), ('nivåfilen %s saknas bland texterna' % NIVAFIL,
                                                                                               NIVAFIL not in texter)) if brist]
    status = 'ej prövat (%s)' % ', '.join(saknas) if saknas else 'spår' if traffar else 'ofullständigt' if ej else 'inga ordagranna spår'
    return {'ok': not saknas and not traffar and not ej, 'status': status, 'texter': len(texter), 'traffar': traffar, 'ej_provade': ej,
            'begransning': LACKAGE_GRANS,
            'provat': 'id och följder om %d ord ur ägarens domar över %d exempel mot %d texter (%s)' % (n, len(exempel), len(texter), ', '.join(sorted(texter)))}


def lackagetexter(fryst):
    """Det granskaren läste i ett exempels frysta katalog: metodfilerna i metod/ (bland dem nivåfilen) och ankarnas ord
    (kalibrering.md). Läckageprovet prövas mot dem."""
    fryst = Path(fryst)
    texter = {f: (fryst / 'metod' / f).read_text(encoding='utf-8', errors='replace') for f in metodfiler() if (fryst / 'metod' / f).is_file()}
    if (fryst / 'kalibrering.md').is_file():
        texter['kalibrering.md (ankarna)'] = (fryst / 'kalibrering.md').read_text(encoding='utf-8', errors='replace')
    return texter


def nivafilen(rot):
    """Nivåfilen som granskaren läste (rot: den frysta metoden, eller repot) med sha256; None när den saknas."""
    f = Path(rot) / NIVAFIL
    return {'fil': NIVAFIL, 'sha256': hash_fil(f)} if f.is_file() else None


def giltighet(lackage):
    """(giltighet, skäl) ur läckageprovet: undanhållna bara när provet faktiskt prövat texter och gått igenom, annars
    utvecklingsdata. Etiketten säger att bara ordagranna spår prövats."""
    if lackage and lackage.get('ok') and lackage.get('texter'):
        return ('undanhållna, inga ordagranna spår (omskriven destillering ej prövad)',
                'läckageprovet fann inga ordagranna spår av de prövade exemplen i det granskaren läste. ' + LACKAGE_GRANS)
    if not lackage:
        varfor = 'läckageprovet gjordes inte'
    elif str(lackage.get('status') or '').startswith('ej prövat') or not lackage.get('texter'):
        varfor = 'läckageprovet är ej prövat (%s)' % (lackage.get('status') or 'inga texter')
    elif lackage.get('traffar'):
        varfor = 'läckageprovet fann spår av de prövade exemplen i det granskaren läste (%s)' % '; '.join(
            '%s i %s: %s' % (x['id'], x['fil'], x['fynd']) for x in lackage['traffar'][:6])
    else:
        varfor = 'läckageprovet kunde inte pröva %s (ägarens ord saknas eller är för korta)' % (', '.join(lackage.get('ej_provade') or []) or 'något exempel')
    return 'utvecklingsdata', ('%s, så exemplen räknas inte som undanhållna: siffran är utvecklingsdata och inget oberoende mått '
                               'på granskarens träffsäkerhet.' % varfor)


def rapport(rader, s, mal, modell, effort, lackage=None, nivafil=None, frysning=None):
    """RAPPORT.json och RAPPORT.md med måtten, nivåfilens sha256, läckageprovet, frysningen och giltigheten. "Undanhållna"
    står bara när läckageprovet gått igenom och (för ett nytt urval) frysningen före domarna höll; annars heter exemplen
    prövade och siffran är utvecklingsdata. frysning: None (inget nytt urval), [] (höll) eller listan med brotten."""
    galler, skal = giltighet(lackage)
    if frysning:
        galler, skal = 'utvecklingsdata', ('frysningen före domarna höll inte (%s), så siffran är utvecklingsdata och inget oberoende '
                                           'mått.' % '; '.join(frysning[:6]))
    belagt = galler != 'utvecklingsdata'
    summa = dict(s)
    if not belagt:
        summa['provade'] = summa.pop('undanhallna')
    (mal / 'RAPPORT.json').write_text(json.dumps({'tid': gr.nu(), 'modell': modell, 'effort': effort, 'rader': rader, 'sammanfattning': summa,
                                                  'giltighet': galler, 'giltighet_skal': skal, 'nivafil': nivafil, 'lackageprov': lackage,
                                                  'frysning': None if frysning is None else ('höll' if not frysning else frysning)},
                                                 ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    lp = ('inte gjort' if not lackage else '%s; %d spår, %d exempel kunde inte prövas; %s. %s' % (
        lackage.get('status') or ('inga ordagranna spår' if lackage.get('ok') else 'ej godkänt'), len(lackage.get('traffar') or []),
        len(lackage.get('ej_provade') or []), lackage.get('provat') or EJ_ANGIVET, lackage.get('begransning') or LACKAGE_GRANS))
    txt = ['# Kalibreringsförsöket %s · %s %s' % (gr.nu(), modell, effort), '',
           '%s: %d, giltiga svar: %d, ofullständiga: %d. Falska godkännanden: %d av %d (ägaren: nästan eller generisk). Falska underkännanden: %d av %d (ägaren: tydligt över ribban).' % (
               'Undanhållna exempel utan ordagranna spår i det granskaren läste' if belagt else 'Prövade exempel', s['undanhallna'], s['svar'],
               s['ofullstandiga'], s['falska_godkannanden'], s['av_ej_over'],
               s['falska_underkannanden'], s['av_over']),
           '**Giltighet: %s.** %s' % (galler, skal),
           'Nivåfilen %s: %s. Läckageprovet: %s.' % (NIVAFIL, 'sha256 %s' % nivafil['sha256'] if nivafil else 'ej angiven', lp),
           ('Försöket är ofullständigt: %s.' % ', '.join('%s (%s)' % (r['id'], r['utfall']) for r in rader if not r['granskaren'])) if s['ofullstandiga'] else 'Försöket är fullständigt.',
           'Måttet gäller en enskild granskare som dömer från bilder med dagens granskartext och ankare, inte produktionsgrinden med två granskare och levande funktioner.', '',
           '| id | ägaren | granskaren | nivå | betyg | blockerande | utfall |', '|---|---|---|---|---|---|---|']
    for r in rader:
        b = r.get('betyg') or {}
        txt.append('| %s | %s | %s | %s | %s | %s | %s |' % (r['id'], gr.KALIBRERING_NIVAER[r['agaren']], r.get('granskaren') or '–', r.get('niva', '–'),
                                                           ' '.join(str(b.get(k, '?')) for k in gr.KRITERIER) if b else '–', r.get('blockerande', '–'), r['utfall']))
    (mal / 'RAPPORT.md').write_text('\n'.join(txt) + '\n', encoding='utf-8')
    return mal / 'RAPPORT.md'


def slutrapport(exempel, mal, modell, effort, frysning=None):
    """Försökets rapport ur exemplens svar: jämförelsen, läckageprovet mot det granskaren läste (den frysta metoden och de
    frysta ankarna i det första exemplets katalog; ägarens uppdrag 2026-10-07, punkt 8) och nivåfilens sha256. Ger
    (RAPPORT.md, rader, sammanfattning)."""
    mal = Path(mal)
    svar = {e['id']: giltigt_svar(mal / e['id']) for e in exempel}
    rader, s = jamfor(exempel, svar)
    fryst = mal / exempel[0]['id']
    return rapport(rader, s, mal, modell, effort, lackage=lackageprov(exempel, lackagetexter(fryst)), nivafil=nivafilen(fryst / 'metod'),
                   frysning=frysning), rader, s


def ratta(mal, datum, galler, skal, hanvisningar=(), uppdrag=None, atgarder=()):
    """Rättar en äldre försöksrapport i katalogen mal (ägarens uppdrag 2026-10-07, punkt 8): ett daterat block överst i
    RAPPORT.md, med rapporthuvudet (README.md, Var information finns) och rättelsen i klartext, och giltigheten med skäl i
    RAPPORT.json. Ursprungsrapporten står kvar byte för byte under blocket, och siffrorna och raderna i RAPPORT.json ändras
    inte: de är historik. Samma rättelse en gång till ändrar ingenting. Ger {'RAPPORT.md': (sha före, sha efter),
    'RAPPORT.json': (sha före, sha efter)}."""
    mal = Path(mal)
    md, js = mal / 'RAPPORT.md', mal / 'RAPPORT.json'
    for f in (md, js):
        if f.is_symlink() or not f.is_file():
            raise ValueError('%s saknas eller är en symlänk' % f)
    if not re.fullmatch(r'\d{4}-\d\d-\d\d', str(datum)):
        raise ValueError('datum ska vara ÅÅÅÅ-MM-DD')
    fore = {f.name: hash_fil(f) for f in (md, js)}
    original = md.read_text(encoding='utf-8')
    original_json = js.read_text(encoding='utf-8')  # ordagrant, så att ursprunget går att läsa byte för byte
    data = json.loads(original_json)
    if not isinstance(data, dict):
        raise ValueError('RAPPORT.json är inget objekt')
    markor = '**Rättelse %s:' % datum
    if markor not in original:
        if original.startswith('---'):
            raise ValueError('rapporten har redan ett huvud; en senare rättelse förs in i huvudet för hand')
        rubrik = original.split('\n', 1)[0].lstrip('# ').strip() or EJ_ANGIVET
        ids = [str(r.get('id')) for r in data.get('rader') or [] if isinstance(r, dict)]

        def falt(namn, varden):  # rapporthuvudets lista: en rad per värde, eller ej angivet
            return ['%s:' % namn] + ['  - %s' % x for x in varden] if varden else ['%s: %s' % (namn, EJ_ANGIVET)]
        huvud = ['---', 'id: KAL-%s' % mal.name, 'titel: %s' % rubrik, 'typ: kalibreringsförsök',
                 'uppdrag: %s' % (uppdrag or EJ_ANGIVET), 'systemdel: granskaren (kritik/GRANSKARE.md)',
                 'forfattare: kontroller/granskarforsok/kalibrering.py; rättelsen %s med kalibrering.py --ratta' % datum,
                 'datum: %s' % (str(data.get('tid') or '')[:10] or EJ_ANGIVET),
                 'granskad_identitet: %s %s, exemplen %s (RAPPORT.json)' % (data.get('modell') or EJ_ANGIVET, data.get('effort') or EJ_ANGIVET,
                                                                            ', '.join(ids) or EJ_ANGIVET),
                 'rapportstatus: färdig, rättad %s' % datum,
                 'bedomningsutfall: ofullständigt: %s, inget oberoende mått på granskarens träffsäkerhet' % galler,
                 'giltighet: %s' % galler,
                 'forhallande: rättelse %s av rapportens egen slutsats; ursprungsresultatet står kvar under rättelsen som historik' % datum,
                 'foregaende: %s' % EJ_ANGIVET, 'ersatt_av: %s' % EJ_ANGIVET,
                 *falt('underlag', ['RAPPORT.json'] + list(hanvisningar)), 'beslut: %s' % EJ_ANGIVET, *falt('atgarder', list(atgarder)), '---', '']
        block = '\n'.join(huvud) + '\n%s %s, inte ett oberoende mått.** %s%s Resultatet nedan står kvar oförändrat som historik.\n\n' % (
            markor, galler, skal.rstrip() + ' ', ('Rättelsen står också i %s.' % '; '.join(hanvisningar)) if hanvisningar else '')
        md.write_text(block + original, encoding='utf-8')
    if (data.get('rattelse') or {}).get('datum') != datum:
        data.update(giltighet=galler, giltighet_skal=skal,
                    rattelse={'datum': datum, 'skal': skal, 'hanvisningar': list(hanvisningar), 'sha256_fore': fore,
                              'original_json': original_json})
        js.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return {f.name: (fore[f.name], hash_fil(f)) for f in (md, js)}


def main(argv=None):
    p = argparse.ArgumentParser(prog='kalibrering', description=__doc__.split('\n\n')[0])
    p.add_argument('--torr', action='store_true', help='förbered och skriv uppdragen, starta ingen granskare')
    p.add_argument('--parallellt', type=int, default=2)
    p.add_argument('--modell', default=os.environ.get('NWP_GRANSKARE_MODELL') or 'opus[1m]')
    p.add_argument('--effort', default=os.environ.get('NWP_GRANSKARE_EFFORT') or 'high')
    p.add_argument('--frist', type=int, default=1500)
    p.add_argument('--ut', default=None, help='utdatakatalog (standard $NWP_FORSOK/kalibrering)')
    p.add_argument('--underlag', default=None, help=argparse.SUPPRESS)
    p.add_argument('--bara', default=None, help='bara dessa exempel, kommaseparerade id (K14,K15,…): ett nytt orört urval prövas för sig')
    p.add_argument('--frys', action='store_true', help='frys metoden, ankarna och exemplen (--bara) före ägarens domar')
    p.add_argument('--trots-frysning', action='store_true', help='kör fast frysningen saknas eller bröts: resultatet är utvecklingsdata')
    p.add_argument('--ratta', default=None, help='rätta en äldre rapport i katalogen: daterat block överst, giltigheten i RAPPORT.json')
    p.add_argument('--datum', default=None)
    p.add_argument('--giltighet', default='utvecklingsdata')
    p.add_argument('--skal', default=None)
    p.add_argument('--hanvisning', action='append', default=[])
    p.add_argument('--uppdrag', default=None)
    p.add_argument('--atgard', action='append', default=[])
    a = p.parse_args(argv)
    if a.ratta:
        if not (a.datum and a.skal):
            print('--ratta kräver --datum och --skal')
            return 2
        for namn, (fore, efter) in ratta(a.ratta, a.datum, a.giltighet, a.skal, a.hanvisning, a.uppdrag, a.atgard).items():
            print('%s: sha256 före %s, efter %s' % (namn, fore, efter))
        return 0
    mal = Path(a.ut) if a.ut else G
    if a.frys:
        ids = [x.strip() for x in (a.bara or '').split(',') if x.strip()]
        if not ids or not all(re.fullmatch(r'K\d{2}', x) for x in ids):
            print('--frys kräver --bara med id som K14,K15')
            return 2
        try:
            f = frys(ids, a.modell, a.effort, a.underlag)
        except ValueError as e:
            print(e)
            return 2
        print('Fryst före domarna: %s (modell %s, effort %s)' % (f, a.modell, a.effort))
        return 0
    exempel = undanhallna(a.underlag)
    brott = None
    if a.bara:  # ett oberoende mått: bara det orörda urvalet, aldrig blandat med utvecklingsexemplen (Codex helhetsbedömning, ordning 3)
        onskade = [x.strip() for x in a.bara.split(',') if x.strip()]
        if not all(re.fullmatch(r'K\d{2}', x) for x in onskade):
            print('--bara tar id som K14,K15')
            return 2
        saknas = [x for x in onskade if x not in {e['id'] for e in exempel}]
        if saknas:
            print('saknar dom, bilder eller är ankare: %s (ägaren dömer i dashboardens Kalibrering)' % ', '.join(saknas))
            return 2
        exempel = [e for e in exempel if e['id'] in onskade]
        brott = frysningsbrott(onskade, a.modell, a.effort, a.underlag)
        if brott and a.torr:  # en torrkörning dömer inget: bristen skrivs ut
            print('Frysningen före domarna håller inte: ' + '; '.join(brott))
        elif brott and not a.trots_frysning:
            print('Frysningen före domarna håller inte, så försöket är inget oberoende mått:\n- ' + '\n- '.join(brott)
                  + '\nKör med --trots-frysning för utvecklingsdata.')
            return 2
    if not exempel:
        print('inga undanhållna exempel med dom och bilder (underlag/kalibrering/DOMAR.json, ANKARE.txt)')
        return 2
    mal.mkdir(parents=True, exist_ok=True)
    klara, att_kora = [], []
    for e in exempel:
        ut = mal / e['id']
        # det gamla svaret och dess manifest läses före ombyggnaden; svaret återanvänds bara om det nya manifestet är identiskt
        gammalt = {n: (ut / n).read_bytes() for n in ('svar.json', 'KORNING.json', 'MANIFEST.json', 'stderr.log') if (ut / n).is_file()}
        gammalt_manifest = gr.las_json(ut / 'MANIFEST.json') if 'MANIFEST.json' in gammalt else None
        if ut.is_dir():
            shutil.rmtree(ut)
        ut.mkdir(parents=True)
        bilder, aria, ankare = forbered(e, ut, a.underlag)
        frysta = frys_metod(ut)
        las_schema(fryst_schema(ut))  # oläsbart schema är ett försöksfel, före varje anrop
        prompt = uppdrag(e, ut, bilder, aria, ankare, a.underlag)
        (ut / 'PROMPT.txt').write_text(prompt, encoding='utf-8')
        nytt = manifest(ut, a.modell, a.effort, prompt, bilder, aria, ankare, frysta)
        (ut / 'MANIFEST.json').write_text(json.dumps(nytt, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        if gammalt_manifest == nytt and 'svar.json' in gammalt and 'KORNING.json' in gammalt:
            for n in ('svar.json', 'KORNING.json', 'stderr.log'):
                if n in gammalt:
                    (ut / n).write_bytes(gammalt[n])
            if giltigt_svar(ut)[1] is None:
                klara.append(e)
                continue
            for n in ('svar.json', 'KORNING.json', 'stderr.log'):  # ogiltigt gammalt svar körs om
                (ut / n).unlink(missing_ok=True)
        att_kora.append(e)
    print('undanhållna: %s; ankare: %d; återanvända (identiskt manifest, giltigt svar): %d; att köra: %d' % (
        ', '.join('%s (%s)' % (e['id'], gr.KALIBRERING_NIVAER[e['niva']]) for e in exempel),
        sum(1 for x in gr.kalibreringsexempel(a.underlag) if x['ankare']), len(klara), len(att_kora)))
    if a.torr:
        print('Torrkörning: uppdragen och manifesten ligger i %s. Ingen granskare startades.' % mal)
        return 0
    claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
    with ThreadPoolExecutor(max_workers=max(1, a.parallellt)) as pool:
        for ident, sek in pool.map(lambda e: kor_en(e, mal / e['id'], a.modell, a.effort, a.frist, claude), att_kora):
            print('%s klar efter %d s' % (ident, sek), flush=True)
    f, rader, s = slutrapport(exempel, mal, a.modell, a.effort, frysning=(brott or []) if a.bara else None)
    print('Falska godkännanden: %d av %d · falska underkännanden: %d av %d · giltiga svar %d av %d (ofullständiga %d) · %s' % (
        s['falska_godkannanden'], s['av_ej_over'], s['falska_underkannanden'], s['av_over'], s['svar'], s['undanhallna'], s['ofullstandiga'], f))
    return 0 if s['ofullstandiga'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
