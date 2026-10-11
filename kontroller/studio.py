#!/usr/bin/env python3
"""studio.py — designstudions källbundna visuella kontroller (designstudion 2026-10-11, DS3; kunskap/designstudio.md).

Fem områden med en avgränsad, prövad räckvidd: typografi, bildregi, mellanrum, komposition och färg/yta. En kontroll finns
bara där källägaren är bevisad:
  - elementet hittas genom källkartans id (kontroller/studio/karta.mjs, insatt i kandidatens förhandsbygge och räknat fram
    ur källan igen här, tolka.mjs);
  - värdets ägare avgörs av motorns egen sond (studio/sond.mjs) i en egen webbläsare med sidans JavaScript avstängt: den
    deklaration vars provvärde slår igenom i det beräknade värdet, och dess källregel genom regelns id. Sidans eget
    påstående (bryggans markering) bär bara id:t, aldrig en fil eller ett kommando.
Allt annat (en regel utan källa, ett uttryck, en kortform som font, en tvetydig sektion) ändras aldrig direkt: kartan säger
varför och erbjuder AI-vägen (ett uppdrag).

Två hastigheter: arbetsytan provar ett värde direkt i förhandsvisningen (en tillfällig regel i bryggan, ingen modell,
inget bygge, märkt Osparat). Ett sparande går hit:
  karta(dash, slug, kid, fråga)  läser och ändrar ingenting: kontrollerna för det markerade elementet, med källa och räckvidd;
  begar(dash, slug, data)        prövar ändringarna mot en ny karta, gör små patchar med de förväntade bytes de ersätter,
                                 sparar begäran i underlag/<slug>/arbetsyta/studio/<id>.json och startar flödeshandlingen
                                 studio genom flodesstart (kundens startlås, journalen, stoppet);
  kor(slug, id)                  arbetaren: prövar allt igen under låset, bevarar grundversionen, skriver patcharna, bygger
                                 och fotograferar med kandidatens ordinarie fotografering och kontrollerar resultatet med
                                 sonden (det förväntade beräknade värdet, inget nytt sidled-spill i 390, en mellanbredd och
                                 1280, inga ändrade element utanför räckvidden); annars läggs originalet tillbaka när filen
                                 fortfarande är den som skrevs, och kandidaten fotograferas om.
Den nya koden blir kandidatens nästa version, bevarad som varje annan; det är den som godkänns, installeras i helbygget och
exporteras.

Kör: .venv/bin/python kontroller/studio.py <slug> --kor <id>   (bara av flodesstart, under startlåset)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atelje  # noqa: E402
import kandidater  # noqa: E402
import prova  # noqa: E402

STUDIO = Path(__file__).resolve().parent / 'studio'
NODE = shutil.which('node') or 'node'
ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
KID = re.compile(r'^[0-9a-f]{12}$')
MELLANBREDD = 900  # mellan 768 och 1024: en ändrad layoutregel prövas också mellan de fotograferade bredderna (DS-U20)
SIDA = re.compile(r'^/(?:[a-z0-9][a-z0-9-]{0,60}/){0,3}$')

TEXTTAGGAR = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'a', 'li', 'span', 'em', 'strong', 'blockquote', 'figcaption', 'label',
              'button', 'small', 'dt', 'dd', 'cite', 'q', 'td', 'th', 'address', 'time', 'b', 'i'}
BILDTAGGAR = {'img', 'video'}
OMRADEN = ('typografi', 'bildregi', 'mellanrum', 'komposition', 'farg')
EGENSKAPER = {
    'typografi': ('font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing', 'max-width'),
    'bildregi': ('object-position', 'aspect-ratio', 'object-fit'),
    'mellanrum': ('padding-top', 'padding-right', 'padding-bottom', 'padding-left', 'row-gap', 'column-gap', 'max-width'),
    'farg': ('color', 'background-color'),
}
ETIKETT = {'font-family': 'Typsnitt', 'font-size': 'Storlek', 'font-weight': 'Vikt', 'line-height': 'Radavstånd',
           'letter-spacing': 'Teckenavstånd', 'max-width': 'Bredd', 'object-position': 'Fokuspunkt', 'aspect-ratio': 'Förhållande',
           'object-fit': 'Beskärning', 'color': 'Textfärg', 'background-color': 'Yta', 'padding-top': 'Över', 'padding-bottom': 'Under',
           'padding-left': 'Vänster', 'padding-right': 'Höger', 'row-gap': 'Mellan rader', 'column-gap': 'Mellan kolumner'}
TYP = {'font-family': 'familj', 'font-size': 'langd', 'font-weight': 'vikt', 'line-height': 'radavstand', 'letter-spacing': 'langd',
       'max-width': 'langd', 'object-position': 'fokus', 'aspect-ratio': 'forhallande', 'object-fit': 'val', 'color': 'farg',
       'background-color': 'farg', 'padding-top': 'langd', 'padding-bottom': 'langd', 'padding-left': 'langd', 'padding-right': 'langd',
       'row-gap': 'langd', 'column-gap': 'langd'}
VAL = {'object-fit': ('cover', 'contain')}
FORHALLANDEN = ('16 / 9', '3 / 2', '4 / 3', '1 / 1', '4 / 5', '2 / 3', 'auto')
# kortformernas delar: (etikett, de längre formerna delen täcker), efter antalet värden i kortformen
KORTFORMER = {
    'padding': {1: [('alla sidor', ('padding-top', 'padding-right', 'padding-bottom', 'padding-left'))],
                2: [('över och under', ('padding-top', 'padding-bottom')), ('sidorna', ('padding-left', 'padding-right'))],
                3: [('över', ('padding-top',)), ('sidorna', ('padding-left', 'padding-right')), ('under', ('padding-bottom',))],
                4: [('över', ('padding-top',)), ('höger', ('padding-right',)), ('under', ('padding-bottom',)), ('vänster', ('padding-left',))]},
    'padding-block': {1: [('över och under', ('padding-top', 'padding-bottom'))], 2: [('över', ('padding-top',)), ('under', ('padding-bottom',))]},
    'padding-inline': {1: [('sidorna', ('padding-left', 'padding-right'))], 2: [('vänster', ('padding-left',)), ('höger', ('padding-right',))]},
    'gap': {1: [('rader och kolumner', ('row-gap', 'column-gap'))], 2: [('mellan rader', ('row-gap',)), ('mellan kolumner', ('column-gap',))]},
}
LANGD = re.compile(r'^-?(?:\d{1,4}(?:\.\d{1,3})?|\.\d{1,3})(?:px|rem|em|ch|vw|vh|svh|dvh|%)$|^0$')
FUNKTION = re.compile(r'^(?:clamp|min|max|calc)\([0-9a-z.%+\-*/ ,()]{1,100}\)$')
TOKEN = re.compile(r'^var\(\s*--[A-Za-z0-9_-]{1,60}\s*\)$')
FARG = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$|^(?:rgb|rgba|hsl|hsla|oklch|oklab)\([0-9.%, /a-z-]{1,60}\)$')
OTILLATET = re.compile(r'[;{}<>\\"\'`@\n\r]|/\*|\*/|url\s*\(|expression\s*\(|image-set|attr\s*\(')


class EjMappbar(ValueError):
    """Ändringen har ingen bevisad källägare: arbetsytan erbjuder AI-vägen (ett uppdrag) i stället (HTTP 422)."""


class Inaktuell(ValueError):
    """Körningen, kandidatens version eller källan har ändrats sedan ägaren såg elementet (HTTP 409)."""


def katalog(slug):
    return atelje.UNDERLAG / slug / 'arbetsyta' / 'studio'


def _dold(dash, slug):
    import importlib
    return importlib.import_module('arbetsyta').dold(dash, slug)


# --- motorns läsning av källan och sidan ---------------------------------------------------------------------------

def tolka(slug, kid):
    """Kandidatprojektets källkarta (studio/tolka.mjs): {filer: {väg: {sha256, element, stilblock, regler, props,
    importer}}, fel}. RuntimeError när läsningen inte går."""
    sajt = kandidater.ksajt(slug, kid)
    atelje.saker_vag(sajt, atelje.KUNDER / slug)
    p = subprocess.run([NODE, str(STUDIO / 'tolka.mjs'), str(sajt)], capture_output=True, text=True, timeout=120)
    if p.returncode:
        raise RuntimeError('källan kunde inte läsas: %s' % (p.stderr or p.stdout)[-400:])
    return json.loads(p.stdout)


def index(t):
    """Uppslagen: element-id → (fil, element), regel-id → (fil, regel)."""
    el, rg = {}, {}
    for rel, f in (t.get('filer') or {}).items():
        for e in f.get('element') or []:
            if e.get('k'):
                el[e['k']] = (rel, e)
        for r in f.get('regler') or []:
            rg[r['r']] = (rel, r)
        for b in f.get('stilblock') or []:
            for r in b.get('regler') or []:
                rg[r['r']] = (rel, r)
    return {'element': el, 'regler': rg}


def sonda(slug, kid, f, egenskaper=(), prova_css=None, alla=(), bredd=None, dist=None, bredder=None):
    """Motorns sond (studio/sond.mjs) mot kandidatens byggda sida, utan brygga: {egenskaper, tokens, egnaRegler, …}.
    Med bredder: {bredder: {<b>: före}, efter: {<b>: med prova_css}} ur en och samma webbläsare."""
    dist = dist or (kandidater.ksajt(slug, kid) / 'dist')
    if not (Path(dist) / 'index.html').is_file():
        return {'fel': 'kandidaten har ingen byggd sida'}
    kmd = [NODE, str(STUDIO / 'sond.mjs'), '--sida', f['sida'], '--bredd', str(bredd or f['bredd']), '--k', f['k'], '--instans', str(f['instans'])]
    if bredder:
        kmd += ['--bredder', ','.join(str(x) for x in bredder)]
    if f.get('barn'):
        kmd += ['--barn', f['barn']]
    if egenskaper:
        kmd += ['--egenskaper', ','.join(egenskaper)]
    if prova_css:
        kmd += ['--prova', json.dumps({'css': prova_css})]
    if alla:
        kmd += ['--alla', ','.join(alla)]
    with prova.Server(dist) as s:
        p = subprocess.run(kmd[:2] + ['--url', s.url + '/'] + kmd[2:], capture_output=True, text=True, timeout=120)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {'fel': 'sonden svarade inte (%s)' % (p.stderr or '')[-300:]}


def fraga_ur(data):
    """Den markerade delen som arbetsytan skickar: sida, bredd, id, förekomst och (för en bild i en komponent) barnet."""
    sida = str(data.get('sida') or '/')
    try:
        bredd = int(data.get('bredd') or 1280)
        instans = int(data.get('instans') or 0)
    except (TypeError, ValueError) as e:
        raise ValueError('bredden och förekomsten är heltal') from e
    k = str(data.get('k') or '')
    barn = data.get('barn') or None
    if not SIDA.fullmatch(sida) or not 280 <= bredd <= 2560 or not KID.fullmatch(k) or not 0 <= instans < 200:
        raise ValueError('markeringen ska ha sida, bredd och elementets id ur källkartan')
    if barn is not None and not re.fullmatch(r'(img|video):\d{1,2}', str(barn)):
        raise ValueError('ogiltigt barnelement')
    return {'sida': sida, 'bredd': bredd, 'k': k, 'instans': instans, 'barn': barn}


# --- värden ---------------------------------------------------------------------------------------------------------

def tokens_i(varde):
    return re.findall(r'var\(\s*(--[A-Za-z0-9_-]+)', str(varde or ''))


def validera(typ, varde, val=None):
    """Ett nytt värde för en kontroll av typen typ, eller ValueError. Bara korta, enkla CSS-värden; inga url(), kommentarer,
    semikolon eller klamrar, så att ett värde aldrig blir mer än ett värde i källan."""
    v = re.sub(r'\s+', ' ', str(varde or '')).strip()
    if not v or len(v) > 120 or OTILLATET.search(v):
        raise ValueError('värdet är tomt, för långt eller innehåller tecken som inte hör till ett värde')
    if TOKEN.fullmatch(v):
        return v
    if typ == 'langd':
        if LANGD.fullmatch(v) or FUNKTION.fullmatch(v) or v in ('auto', 'none', 'normal'):
            return v
    elif typ == 'vikt':
        if re.fullmatch(r'[1-9]00|1000', v) or v in ('normal', 'bold'):
            return v
    elif typ == 'radavstand':
        if re.fullmatch(r'(?:[0-3](?:\.\d{1,3})?|\.\d{1,3})', v) or LANGD.fullmatch(v) or v == 'normal':
            return v
    elif typ == 'farg':
        if FARG.fullmatch(v) or v in ('transparent', 'currentColor', 'white', 'black'):
            return v
    elif typ == 'fokus':
        m = re.fullmatch(r'(\d{1,3}(?:\.\d)?)% (\d{1,3}(?:\.\d)?)%', v)
        if m and all(0 <= float(x) <= 100 for x in m.groups()):
            return v
    elif typ == 'forhallande':
        if v in FORHALLANDEN:
            return v
    elif typ in ('val', 'familj', 'variant'):
        if val and v in val:
            return v
        raise ValueError('välj ett av de tillåtna värdena: %s' % ', '.join(val or [])[:300])
    raise ValueError('"%s" är inget giltigt värde här (%s)' % (v, typ))


def delar(varde):
    """Kortformens värden på toppnivå med lägen i texten: [(start, slut, text)], parenteser hålls ihop."""
    ut, djup, start = [], 0, None
    for i, c in enumerate(varde + ' '):
        if c == '(':
            djup += 1
        elif c == ')':
            djup -= 1
        if c.isspace() and djup == 0:
            if start is not None:
                ut.append((start, i, varde[start:i]))
                start = None
        elif start is None:
            start = i
    return ut


def familjer(t):
    """De typsnitt som redan finns i kandidaten: varje font-family-värde och varje token vars namn säger familj/font, med
    värdet som står i källan (ett tillåtet och laddat val; ett nytt webbtypsnitt installeras bara genom typsnitt.py och
    går därför AI-vägen)."""
    ut = []
    for _rel, f in (t.get('filer') or {}).items():
        lista = list(f.get('regler') or []) + [r for b in f.get('stilblock') or [] for r in b.get('regler') or []]
        for r in lista:
            for d in r.get('deklarationer') or []:
                p = d.get('egenskap') or ''
                if (p == 'font-family' or (p.startswith('--') and re.search(r'famil|font', p))) and not tokens_i(d.get('ra')):
                    v = re.sub(r'\s+', ' ', d.get('ra') or '').strip()
                    if v and v not in ut and not OTILLATET.search(v.replace('"', '').replace("'", '')):
                        ut.append(v)
    return ut[:12]


def sidfil(t, sida):
    """Sidans mall ur adressen: / → src/pages/index.astro, /om/ → src/pages/om.astro eller om/index.astro."""
    namn = sida.strip('/')
    for kand in (['src/pages/index.astro'] if not namn else ['src/pages/%s.astro' % namn, 'src/pages/%s/index.astro' % namn]):
        if kand in (t.get('filer') or {}):
            return kand
    return None


def radnummer(slug, kid, rel, pos):
    try:
        text = (kandidater.ksajt(slug, kid) / rel).read_text(encoding='utf-8')
        return text.count('\n', 0, pos) + 1
    except OSError:
        return None


# --- kartan över kontrollerna -----------------------------------------------------------------------------------------

def _rackvidd(kalla, antal_inst, rel, ram, token=None, anvandning=None):
    """Räckvidden i ägarens ord: detta objekt, alla förekomster av samma element, en regel som träffar fler, en delad
    komponent, en responsiv regel eller hela kundens designgrund."""
    responsiv = ' och '.join('%s' % x.get('villkor') for x in ram or [] if x.get('namn') == 'media') or None
    if token:
        return {'slag': 'designgrund', 'antal': anvandning, 'responsiv': responsiv,
                'text': 'hela kundens designgrund: token %s (används i %s regler)' % (token, anvandning if anvandning is not None else '?')}
    antal = (kalla or {}).get('antal')
    komponent = rel.startswith('src/components/') or rel.startswith('src/layouts/')
    if antal is not None and antal <= max(1, antal_inst):
        slag = 'objekt' if antal_inst <= 1 else 'forekomster'
        text = 'detta objekt' if antal_inst <= 1 else 'alla %d förekomster av elementet (samma källa)' % antal_inst
    else:
        slag, text = 'regel', 'regeln %s, som träffar %s element på sidan' % ((kalla or {}).get('valjare_kalla') or '?', antal)
    if komponent:
        text += '; komponenten %s (också på andra sidor som använder den)' % Path(rel).stem
    if responsiv:
        text += '; bara i bredder där %s gäller' % responsiv
    return {'slag': slag, 'antal': antal, 'komponent': komponent, 'responsiv': responsiv, 'text': text}


def _deklaration(regel, egenskap):
    """Regelns sista deklaration av egenskapen (den som gäller i regeln), eller None."""
    ds = [d for d in regel.get('deklarationer') or [] if d.get('egenskap') == egenskap]
    return ds[-1] if ds else None


def _prova(valjare, ram, egenskap, viktig=True):
    """Mallen för en tillfällig regel i förhandsvisningen: samma väljare och mediavillkor som regeln som äger värdet."""
    return {'valjare': valjare, 'ram': [x for x in ram or [] if str(x).startswith('@media')], 'egenskap': egenskap}


def kontroller_for(omrade, s, ix, el_rel, antal_inst, t, slug, kid, textelement=False):
    """Kontrollerna i ett område för det markerade elementet, ur sonden och källkartan. Ett ärvt värde (regeln äger en
    förfader) erbjuds först som en ny deklaration i elementets egen regel, och förfaderns regel bara med räckvidden att
    allt som ärver ändras. Avstånd mellan rader och kolumner bara i flex och grid; en textrad får inga nya mellanrum."""
    ut = []
    sett = set()
    display = ((s.get('egenskaper') or {}).get('display') or {}).get('berakn') or ''
    for egenskap in EGENSKAPER.get(omrade, ()):
        info = (s.get('egenskaper') or {}).get(egenskap)
        if not info:
            continue
        if egenskap in ('row-gap', 'column-gap') and 'flex' not in display and 'grid' not in display:
            continue
        kalla = info.get('kalla') or {}
        if info.get('arvd') and kalla.get('slag') == 'regel':
            # ärvt: elementets egen regel först, förfaderns regel med sin verkliga räckvidd
            egen = _egen_regel(s, ix, el_rel, antal_inst)
            if egen and not (textelement and omrade == 'mellanrum'):
                rel, regel = ix['regler'][egen['r']]
                ut.append(dict(_bas(omrade, egenskap, info), id='%s/%s' % (omrade, egenskap), varde=None, stod=True, ny=True,
                               kalla={'fil': rel, 'rad': radnummer(slug, kid, rel, regel['start']), 'slag': 'ny_deklaration',
                                      'valjare': regel['valjare'], 'ram': regel.get('ram')},
                               rackvidd=_rackvidd(dict(egen, valjare_kalla=regel['valjare']), antal_inst, rel, regel.get('ram')),
                               arvd=info['arvd'],
                               skriv={'slag': 'infoga', 'fil': rel, 'pos': regel['infoga'], 'foreSemikolon': regel.get('foreSemikolon'), 'egenskap': egenskap},
                               prova=_prova(egen.get('valjare'), egen.get('ram'), egenskap)))
                sett.add('%s/%s' % (omrade, egenskap))
            if kalla.get('r') in ix['regler']:
                rel, regel = ix['regler'][kalla['r']]
                d = _deklaration(regel, kalla.get('via') or egenskap)
                if d and not d.get('oklar') and (kalla.get('via') or egenskap) == egenskap:
                    tagg = (info['arvd'] or {}).get('tagg') or '?'
                    ut.append(dict(_bas(omrade, egenskap, info), id='%s/%s/arvd' % (omrade, egenskap),
                                   etikett='%s (ärvs från %s)' % (ETIKETT.get(egenskap, egenskap), tagg), varde=d['ra'], stod=True,
                                   kalla={'fil': rel, 'rad': radnummer(slug, kid, rel, d['start']), 'slag': 'regel', 'valjare': regel['valjare'], 'ram': regel.get('ram')},
                                   rackvidd={'slag': 'arvd', 'antal': kalla.get('antal'),
                                             'text': 'ärvs från %s genom regeln %s i %s: ändringen gäller allt som ärver värdet där' % (tagg, regel['valjare'], rel)},
                                   token=(tokens_i(d['ra']) or [None])[0],
                                   skriv={'slag': 'ersatt', 'fil': rel, 'start': d['vardeStart'], 'slut': d['vardeSlut'], 'vantat': d['ra']},
                                   prova=_prova(kalla.get('valjare'), kalla.get('ram'), egenskap)))
            continue
        bas = _bas(omrade, egenskap, info)
        slag = kalla.get('slag')
        if slag == 'regel' and kalla.get('r') in ix['regler']:
            rel, regel = ix['regler'][kalla['r']]
            via = kalla.get('via') or egenskap
            d = _deklaration(regel, via)
            if not d or d.get('oklar'):
                ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False, skal='deklarationen kunde inte läsas exakt i källan'))
                continue
            kalla_ut = {'fil': rel, 'rad': radnummer(slug, kid, rel, d['start']), 'slag': 'regel', 'valjare': regel['valjare'],
                        'ram': regel.get('ram'), 'valjare_kalla': regel['valjare']}
            rv = _rackvidd(dict(kalla, valjare_kalla=regel['valjare']), antal_inst, rel, regel.get('ram'))
            # background med ett enda värde (en färg eller en token) är ytans färg: ändras som en egen deklaration
            if via == 'background' and egenskap == 'background-color' and len(delar(d['ra'])) == 1 and (
                    TOKEN.fullmatch(d['ra'].strip()) or FARG.fullmatch(d['ra'].strip())):
                via = egenskap
            if via != egenskap:  # kortform: en kontroll per värde i den (padding: A B → över och under, sidorna)
                if via not in KORTFORMER:
                    ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False,
                                   skal='värdet står i kortformen %s (%s); ändra genom AI-vägen' % (via, d['ra'])))
                    continue
                vals = delar(d['ra'])
                schema = KORTFORMER[via].get(len(vals))
                if not schema:
                    ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False, skal='kortformen %s har %d värden' % (via, len(vals))))
                    continue
                for i, (etikett, tackt) in enumerate(schema):
                    kid_ = '%s/%s:%d' % (omrade, via, i)
                    if egenskap not in tackt or kid_ in sett:
                        continue
                    sett.add(kid_)
                    a, b, text = vals[i]
                    ut.append(dict(bas, id=kid_, etikett='%s (%s)' % (etikett.capitalize(), via), varde=text, stod=True, kalla=kalla_ut,
                                   rackvidd=rv, token=(tokens_i(text) or [None])[0], tacker=list(tackt),
                                   skriv={'slag': 'ersatt', 'fil': rel, 'start': d['vardeStart'] + a, 'slut': d['vardeStart'] + b, 'vantat': text},
                                   prova=dict(_prova(kalla.get('valjare'), kalla.get('ram'), via), varden=[x[2] for x in vals], index=i)))
                continue
            kid_ = '%s/%s' % (omrade, egenskap)
            if kid_ in sett:
                continue
            sett.add(kid_)
            tok = tokens_i(d['ra'])
            c = dict(bas, id=kid_, varde=d['ra'], stod=True, kalla=kalla_ut, rackvidd=rv, token=tok[0] if len(tok) == 1 else None,
                     skriv={'slag': 'ersatt', 'fil': rel, 'start': d['vardeStart'], 'slut': d['vardeSlut'], 'vantat': d['ra']},
                     prova=_prova(kalla.get('valjare'), kalla.get('ram'), egenskap))
            ut.append(c)
            # samma värde som token: ändra token i designgrunden (räckvidden visas), som eget val bredvid den lokala
            if len(tok) == 1 and d['ra'].strip() == 'var(%s)' % tok[0]:
                tinfo = (s.get('tokens') or {}).get(tok[0]) or {}
                tk = tinfo.get('kalla') or {}
                if tk.get('slag') == 'regel' and tk.get('r') in ix['regler']:
                    trel, tregel = ix['regler'][tk['r']]
                    td = _deklaration(tregel, tok[0])
                    if td and not td.get('oklar'):
                        ut.append(dict(bas, id=kid_ + '/token', etikett='%s (token %s)' % (bas['etikett'], tok[0]), varde=td['ra'], stod=True,
                                       kalla={'fil': trel, 'rad': radnummer(slug, kid, trel, td['start']), 'slag': 'token', 'valjare': tregel['valjare'],
                                              'ram': tregel.get('ram')},
                                       rackvidd=_rackvidd(None, antal_inst, trel, tregel.get('ram'), token=tok[0], anvandning=tk.get('anvandning')),
                                       token=tok[0],
                                       skriv={'slag': 'ersatt', 'fil': trel, 'start': td['vardeStart'], 'slut': td['vardeSlut'], 'vantat': td['ra']},
                                       prova=_prova(tk.get('valjare'), tk.get('ram'), tok[0])))
        elif slag == 'inline':
            ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False,
                           skal='värdet står i elementets style-attribut; inline-värden ändras genom AI-vägen i den här versionen'))
        elif slag == 'okand_regel':
            ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False,
                           skal='värdet kommer ur en regel utan källa i projektet (%s), till exempel en Tailwind-klass eller ett paket'
                           % (kalla.get('valjare') or '?')[:80]))
        else:
            # ingen deklaration sätter värdet på elementet: sätt in en i elementets egen regel när det finns en
            if textelement and omrade == 'mellanrum':
                continue  # en textrad får inga nya mellanrum här; sektionens mellanrum står på sektionen
            egen = _egen_regel(s, ix, el_rel, antal_inst)
            arvd = info.get('arvd')
            if egen and egenskap not in ('font-family',) and not (textelement and omrade == 'mellanrum'):
                rel, regel = ix['regler'][egen['r']]
                kid_ = '%s/%s' % (omrade, egenskap)
                if kid_ in sett:
                    continue
                sett.add(kid_)
                ut.append(dict(bas, id=kid_, varde=None, stod=True, ny=True,
                               kalla={'fil': rel, 'rad': radnummer(slug, kid, rel, regel['start']), 'slag': 'ny_deklaration',
                                      'valjare': regel['valjare'], 'ram': regel.get('ram')},
                               rackvidd=_rackvidd(dict(egen, valjare_kalla=regel['valjare']), antal_inst, rel, regel.get('ram')),
                               arvd=arvd,
                               skriv={'slag': 'infoga', 'fil': rel, 'pos': regel['infoga'], 'foreSemikolon': regel.get('foreSemikolon'),
                                      'egenskap': egenskap},
                               prova=_prova(egen.get('valjare'), egen.get('ram'), egenskap)))
            else:
                ut.append(dict(bas, id='%s/%s' % (omrade, egenskap), stod=False, arvd=arvd,
                               skal=('värdet ärvs från %s' % (arvd or {}).get('tagg')) if arvd else
                               'ingen regel i elementets egen fil träffar just det här elementet; ändra genom AI-vägen'))
    return ut


def _bas(omrade, egenskap, info):
    bas = {'omrade': omrade, 'egenskap': egenskap, 'etikett': ETIKETT.get(egenskap, egenskap), 'typ': TYP.get(egenskap, 'langd'),
           'berakn': info.get('berakn')}
    if egenskap == 'object-fit':
        bas['val'] = list(VAL['object-fit'])
    if egenskap == 'aspect-ratio':
        bas['val'] = list(FORHALLANDEN)
    return bas


def _egen_regel(s, ix, el_rel, antal_inst):
    """Elementets egen regel: en regel med källa i elementets egen fil, utan mediavillkor, som på sidan träffar exakt
    elementets förekomster. Där sätts en ny deklaration in. None när det inte finns en sådan."""
    for r in s.get('egnaRegler') or []:
        if r.get('r') in ix['regler'] and ix['regler'][r['r']][0] == el_rel and not r.get('ram') and r.get('antal') == max(1, antal_inst):
            return r
    return None


def komposition(s, ix, t, el_rel, el, f, slug, kid):
    """Komponentens varianter (Props med en union av strängar) där den används på sidan, och sektionsordningen i sidans
    huvudinnehåll, när båda kan knytas entydigt till källan. Allt friare går AI-vägen."""
    ut = []
    sf = sidfil(t, f['sida'])
    sidan = (t.get('filer') or {}).get(sf) if sf else None
    if not sidan:
        return [{'id': 'komposition/sida', 'omrade': 'komposition', 'etikett': 'Komposition', 'stod': False,
                 'skal': 'sidans mall hittades inte i källan'}]
    # 1. varianter: komponenten som elementet står i, använd en gång på sidan med en literal (eller standardvärdet)
    if el_rel.startswith('src/components/'):
        props = (t['filer'].get(el_rel) or {}).get('props') or []
        namn = None
        for imp in sidan.get('importer') or []:
            mal = os.path.normpath(os.path.join(os.path.dirname(sf), imp['kalla'])).replace(os.sep, '/')
            if mal == el_rel and imp.get('standard'):
                namn = imp['namn']
        anv = [e for e in sidan.get('element') or [] if e.get('komponent') and e.get('tagg') == namn]
        for p in props:
            if not p.get('varden'):
                continue
            c = {'id': 'komposition/prop:%s' % p['namn'], 'omrade': 'komposition', 'egenskap': 'prop', 'prop': p['namn'],
                 'etikett': 'Variant: %s (%s)' % (p['namn'], Path(el_rel).stem), 'typ': 'variant', 'val': p['varden']}
            if not namn or len(anv) != 1 or anv[0].get('iUttryck'):
                ut.append(dict(c, stod=False, skal='komponenten %s används %d gånger på sidan; varianten väljs genom AI-vägen' % (Path(el_rel).stem, len(anv))))
                continue
            a = [x for x in anv[0]['attribut'] if x.get('namn') == p['namn']]
            if any(x.get('spridning') for x in anv[0]['attribut']):
                ut.append(dict(c, stod=False, skal='komponenten får egenskaper genom {...spridning}; varianten väljs genom AI-vägen'))
                continue
            if a and a[0]['varde'].get('slag') != 'literal':
                ut.append(dict(c, stod=False, skal='varianten sätts av ett uttryck i sidan; ändra genom AI-vägen'))
                continue
            rv = {'slag': 'objekt', 'text': 'den här användningen av %s på sidan (%s)' % (Path(el_rel).stem, sf)}
            rot = next((e['k'] for e in (t['filer'].get(el_rel) or {}).get('element') or [] if e.get('vag') == '0' and e.get('k')), None)
            c['rot_k'] = rot  # komponentens rotelement: varianten prövas mot dess markup efter bygget
            if a:
                v = a[0]['varde']
                ut.append(dict(c, varde=v['text'], stod=True, kalla={'fil': sf, 'rad': radnummer(slug, kid, sf, a[0]['start']), 'slag': 'prop'},
                               rackvidd=rv, skriv={'slag': 'ersatt', 'fil': sf, 'start': v['start'] + 1, 'slut': v['slut'] - 1, 'vantat': v['text']}))
            else:
                op = anv[0]['oppning']
                ut.append(dict(c, varde=p.get('standard'), stod=True, ny=True,
                               kalla={'fil': sf, 'rad': radnummer(slug, kid, sf, op[0]), 'slag': 'prop'}, rackvidd=rv,
                               skriv={'slag': 'infoga_attribut', 'fil': sf, 'pos': anv[0]['oppning'][0] + 1 + len(namn), 'namn': p['namn']}))
    # 2. sektionsordningen: syskonen under sidans <main>, när varje syskon i källan är ett statiskt element eller en
    # komponent och sidans syskon motsvarar dem ett mot ett (sonden: föräldern och barnen)
    far = s.get('foralder') or {}
    main = [e for e in sidan.get('element') or [] if e.get('tagg') == 'main' and not e.get('iUttryck')]
    if main and far.get('tagg') == 'main':
        m = main[0]
        barn = [e for e in sidan['element'] if e['vag'].rsplit('/', 1)[0] == m['vag'] and e['vag'] != m['vag']]
        statiska = all(not e.get('iUttryck') for e in barn) and not any(x['typ'] == 'JSXExpressionContainer' for x in m.get('barn') or [])
        dom = far.get('barn') or []
        stammer = statiska and len(barn) == len(dom) and len(barn) >= 2
        if stammer:
            for e, d in zip(barn, dom):
                if e['komponent']:
                    hit = ix['element'].get(d.get('k') or '')
                    stammer = stammer and bool(hit) and hit[1]['vag'] == '0' and Path(hit[0]).stem == e['tagg']
                else:
                    stammer = stammer and d.get('k') == e.get('k')
        if stammer:
            mitt = next((i for i, d in enumerate(dom) if d.get('k') == f['k']), None)
            ut.append({'id': 'komposition/ordning', 'omrade': 'komposition', 'egenskap': 'ordning', 'etikett': 'Sektionsordning', 'typ': 'ordning',
                       'stod': True, 'varde': [e['tagg'] for e in barn], 'markerad': mitt,
                       'kalla': {'fil': sf, 'rad': radnummer(slug, kid, sf, m['start']), 'slag': 'ordning'},
                       'rackvidd': {'slag': 'sida', 'text': 'sektionernas ordning i %s; innehållet i varje sektion bevaras' % sf},
                       'skriv': {'slag': 'ordning', 'fil': sf, 'delar': [[e['start'], e['slut']] for e in barn], 'namn': [e['tagg'] for e in barn]}})
        else:
            ut.append({'id': 'komposition/ordning', 'omrade': 'komposition', 'egenskap': 'ordning', 'etikett': 'Sektionsordning', 'stod': False,
                       'skal': 'sektionerna i sidans main kan inte knytas en och en till källan (ett uttryck, en lista eller ett villkor); '
                               'en annan ordning går AI-vägen'})
    ut.append({'id': 'komposition/ai', 'omrade': 'komposition', 'egenskap': 'ai', 'etikett': 'Annan komposition', 'stod': False, 'ai': True,
               'skal': 'en friare omkomposition (innehållets prioritet, sektionernas form) är ett uppdrag: Omarbeta designen'})
    return ut


def bildval(s, ix, t, el_rel, el, f, slug, kid):
    """Kundens bildval: <Image src={X}> i elementets egen fil där X importeras direkt ur kundens bilder (src/assets/atelje/);
    importen byts mot en annan av kundens bilder. Originalfilerna rörs aldrig."""
    fil = (t.get('filer') or {}).get(el_rel) or {}
    bilder = [e for e in fil.get('element') or [] if e.get('tagg') in ('Image', 'Picture') and e['vag'].startswith(el.get('vag', '') + '/')]
    if len(bilder) != 1:
        return []
    src = [a for a in bilder[0]['attribut'] if a.get('namn') == 'src']
    if not src or src[0]['varde'].get('slag') != 'uttryck':
        return []
    namn = src[0]['varde']['ra'].strip('{} ')
    imp = [i for i in fil.get('importer') or [] if i.get('namn') == namn and i.get('standard')]
    sajt = kandidater.ksajt(slug, kid)
    egna = sorted(p.name for p in (sajt / 'src' / 'assets' / 'atelje').glob('*') if p.is_file() and not p.is_symlink()
                  and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp', '.avif'))
    c = {'id': 'bildregi/bild', 'omrade': 'bildregi', 'egenskap': 'bild', 'etikett': 'Bild', 'typ': 'val'}
    if not imp or not re.search(r'assets/atelje/[^/]+$', imp[0]['kalla']):
        return [dict(c, stod=False, skal='bilden kommer genom en egenskap eller ett uttryck; ett annat bildval går AI-vägen')]
    nu_namn = imp[0]['kalla'].rsplit('/', 1)[1]
    prefix = imp[0]['kalla'][:-len(nu_namn)]
    return [dict(c, stod=True, varde=nu_namn, val=egna, kalla={'fil': el_rel, 'rad': radnummer(slug, kid, el_rel, imp[0]['start']), 'slag': 'import'},
                 rackvidd={'slag': 'objekt', 'text': 'bilden %s i %s (originalfilerna ändras inte)' % (namn, Path(el_rel).name)},
                 skriv={'slag': 'ersatt', 'fil': el_rel, 'start': imp[0]['start'] + 1, 'slut': imp[0]['slut'] - 1,
                        'vantat': imp[0]['kalla'], 'prefix': prefix})]


def textkontroll(t, el_rel, el, f, slug, kid):
    """Elementets text med bevisad källa: en egen text i mallen (elementets enda barn är en textnod), eller ett känt
    prop-värde (elementets enda barn är {namn}, namn är en egenskap i komponentens Props, och komponenten används en gång
    på sidan med en literal). Allt annat, en lista, ett uttryck eller en text delad av taggar, går AI-vägen. Ingen global
    strängersättning: samma text på ett annat ställe berörs aldrig."""
    c = {'id': 'text/text', 'omrade': 'text', 'egenskap': 'text', 'etikett': 'Text', 'typ': 'text'}
    sajt = kandidater.ksajt(slug, kid)
    try:
        kod = (sajt / el_rel).read_text(encoding='utf-8')
    except OSError:
        return dict(c, stod=False, skal='källan kunde inte läsas')
    barn = [b for b in el.get('barn') or [] if not (b['typ'] == 'JSXText' and not kod[b['start']:b['slut']].strip())]
    if el.get('iUttryck'):
        return dict(c, stod=False, skal='elementet står i en lista eller ett villkor i källan; texten kommer ur data och ändras genom AI-vägen')
    if len(barn) == 1 and barn[0]['typ'] == 'JSXText':
        ra = kod[barn[0]['start']:barn[0]['slut']]
        a = barn[0]['start'] + (len(ra) - len(ra.lstrip()))
        b = barn[0]['slut'] - (len(ra) - len(ra.rstrip()))
        text = kod[a:b]
        if '\n' in text or '{' in text or '}' in text:
            return dict(c, stod=False, skal='texten går över flera rader i källan; ändra genom AI-vägen')
        return dict(c, stod=True, varde=text, kalla={'fil': el_rel, 'rad': radnummer(slug, kid, el_rel, a), 'slag': 'text'},
                    rackvidd={'slag': 'objekt', 'text': 'den här texten i %s (andra ställen med samma text berörs inte)' % el_rel},
                    skriv={'slag': 'ersatt', 'fil': el_rel, 'start': a, 'slut': b, 'vantat': text, 'kodning': 'mall'})
    if len(barn) == 1 and barn[0]['typ'] == 'JSXExpressionContainer':
        uttryck = kod[barn[0]['start']:barn[0]['slut']].strip('{} \n')
        props = {p['namn'] for p in (t['filer'].get(el_rel) or {}).get('props') or []}
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', uttryck) or uttryck not in props or not el_rel.startswith('src/components/'):
            return dict(c, stod=False, skal='texten byggs av uttrycket {%s}; ändra i datakällan genom AI-vägen' % uttryck[:40])
        sf = sidfil(t, f['sida'])
        sidan = (t.get('filer') or {}).get(sf) or {}
        namn = None
        for imp in sidan.get('importer') or []:
            if os.path.normpath(os.path.join(os.path.dirname(sf or ''), imp['kalla'])).replace(os.sep, '/') == el_rel and imp.get('standard'):
                namn = imp['namn']
        anv = [e for e in sidan.get('element') or [] if e.get('komponent') and e.get('tagg') == namn]
        if len(anv) != 1 or anv[0].get('iUttryck'):
            return dict(c, stod=False, skal='komponenten %s används %d gånger på sidan; texten ändras genom AI-vägen' % (Path(el_rel).stem, len(anv)))
        attr = [x for x in anv[0]['attribut'] if x.get('namn') == uttryck]
        if len(attr) != 1 or attr[0]['varde'].get('slag') != 'literal' or attr[0]['varde'].get('iUttryck'):
            return dict(c, stod=False, skal='egenskapen %s får sitt värde av ett uttryck i sidan; ändra genom AI-vägen' % uttryck)
        v = attr[0]['varde']
        return dict(c, stod=True, varde=v['text'], kalla={'fil': sf, 'rad': radnummer(slug, kid, sf, attr[0]['start']), 'slag': 'prop'},
                    rackvidd={'slag': 'objekt', 'text': 'egenskapen %s där %s används i %s' % (uttryck, Path(el_rel).stem, sf)},
                    skriv={'slag': 'ersatt', 'fil': sf, 'start': v['start'] + 1, 'slut': v['slut'] - 1, 'vantat': v['text'], 'kodning': 'attribut'})
    return dict(c, stod=False, skal='texten är delad av taggar eller uttryck; ändra genom AI-vägen')


def kodad_text(kodning, ny):
    """Den nya texten skriven för sin plats: mallens text med HTML-escape och klamrar som entiteter, eller ett attributs
    strängliteral (inga citattecken)."""
    import html as html_
    ny = re.sub(r'\s+', ' ', str(ny or '')).strip()
    if not 1 <= len(ny) <= 500 or re.search(r'[\x00-\x1f\x7f]', ny):
        raise ValueError('texten ska vara 1–500 tecken på en rad')
    if kodning == 'mall':
        return html_.escape(ny, quote=False).replace('{', '&#123;').replace('}', '&#125;')
    if '"' in ny or '{' in ny or '}' in ny:
        raise ValueError('texten står i ett attribut; den får inte innehålla ", { eller }')
    return ny


def _karta(slug, kid, f, t=None):
    """Kartan med skrivuppgifterna (bara för motorn): kontrollerna, elementet och sonden."""
    t = t or tolka(slug, kid)
    ix = index(t)
    hit = ix['element'].get(f['k'])
    if not hit:
        raise EjMappbar('elementet finns inte i kandidatens källa för den här versionen (läs om förhandsvisningen)')
    el_rel, el = hit
    tagg = (f['barn'] or '').split(':')[0] or el['tagg']
    egenskaper = ['display']
    for o in ('typografi', 'mellanrum', 'farg'):
        egenskaper += EGENSKAPER[o]
    if tagg in BILDTAGGAR:
        egenskaper = list(EGENSKAPER['bildregi'])
    s = sonda(slug, kid, f, list(dict.fromkeys(egenskaper)))
    if s.get('fel'):
        raise EjMappbar('motorns sond nådde inte elementet: %s' % s['fel'])
    if s.get('tagg') != tagg:
        raise EjMappbar('elementet på sidan (%s) är inte det källan anger (%s); läs om förhandsvisningen' % (s.get('tagg'), tagg))
    antal_inst = int(s.get('antal') or 1)
    omraden = {}
    if tagg in BILDTAGGAR:
        omraden['bildregi'] = kontroller_for('bildregi', s, ix, el_rel, antal_inst, t, slug, kid) + bildval(s, ix, t, el_rel, el, f, slug, kid)
    else:
        text = tagg in TEXTTAGGAR or bool(el.get('text'))
        if text:
            omraden['typografi'] = kontroller_for('typografi', s, ix, el_rel, antal_inst, t, slug, kid, textelement=True)
        omraden['mellanrum'] = [c for c in kontroller_for('mellanrum', s, ix, el_rel, antal_inst, t, slug, kid, textelement=text)
                                if not (c['egenskap'] == 'max-width' and text)]
        for c in omraden['mellanrum']:
            if c['egenskap'] == 'max-width':
                c['etikett'] = c['etikett'].replace('Bredd', 'Innehållsbredd', 1)
        omraden['farg'] = kontroller_for('farg', s, ix, el_rel, antal_inst, t, slug, kid, textelement=text)
    omraden['komposition'] = komposition(s, ix, t, el_rel, el, f, slug, kid)
    if tagg not in BILDTAGGAR and (tagg in TEXTTAGGAR or el.get('text')):
        omraden['text'] = [textkontroll(t, el_rel, el, f, slug, kid)]
    fam = familjer(t)
    for c in omraden.get('typografi') or []:
        if c['egenskap'] == 'font-family':
            c['val'] = fam
            if c.get('stod') and c.get('varde') and not c['varde'].startswith('var(') and c['varde'] not in fam:
                c['val'] = fam + [c['varde']]
    return {'element': {'k': f['k'], 'fil': el_rel, 'rad': radnummer(slug, kid, el_rel, el['start']), 'tagg': tagg, 'text': s.get('text'),
                        'antal': antal_inst, 'rekt': s.get('rekt'), 'bild': s.get('bild'), 'kontrast': s.get('kontrast'),
                        'typsnitt': s.get('typsnitt'), 'iUttryck': el.get('iUttryck')},
            'omraden': omraden, 'spill': s.get('spill'), 'filsha': {rel: v.get('sha256') for rel, v in (t.get('filer') or {}).items()}}


def offentlig(k):
    """Kartan som arbetsytan får: utan motorns skrivuppgifter (lägen i filerna), som aldrig kommer tillbaka från sidan."""
    k = json.loads(json.dumps(k))
    for lista in (k.get('omraden') or {}).values():
        for c in lista:
            c.pop('skriv', None)
    k.pop('filsha', None)
    return k


def _villkor(slug, kid, version, korning):
    """Samma villkor som direktredigeringen: kandidaten står vid sin gräns (körningen är den ägaren såg, kandidatens kedja
    är klar, versionen är den ägaren såg och projektet står i den); andra kandidater kan arbeta under tiden (DS4)."""
    import direktredigering
    try:
        direktredigering._villkor(slug, kid, version, korning)
    except direktredigering.Inaktuell as e:
        raise Inaktuell(str(e)) from e


def karta(dash, slug, kid, data):
    """Arbetsytans förhandsfråga för det markerade elementet: kontrollerna i de fem områdena med källa och räckvidd, eller
    {ok: False, skäl}. Ändrar ingenting."""
    kid = str(kid or '')
    if not kandidater.ID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    blind, ab = _dold(dash, slug)
    if ab:
        raise ValueError('kunden är en arm i en blind jämförelse som du inte valt i än')
    if blind:
        return {'ok': False, 'skal': 'studions kontroller ändrar kandidaten; gör ditt första val i körningen först', 'alternativ': 'uppdrag'}
    f = fraga_ur(data)
    st = kandidater.las_status(slug, kid)
    version = str(st.get('version') or '')
    if not version or kandidater.projektets_version(slug, kid) != version:
        return {'ok': False, 'skal': 'kandidatens projekt har ändringar som inte är fotograferade; kontrollerna visas när projektet och versionen stämmer',
                'alternativ': 'uppdrag'}
    try:
        k = _karta(slug, kid, f)
    except EjMappbar as e:
        return {'ok': False, 'skal': str(e), 'alternativ': 'uppdrag'}
    except (RuntimeError, OSError, subprocess.SubprocessError) as e:
        return {'ok': False, 'skal': 'kartan kunde inte läsas: %s' % str(e)[:300], 'alternativ': 'uppdrag'}
    return dict(offentlig(k), ok=True, kandidat=kid, version=version, korning=str((atelje.las_json(atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}).get('startad') or ''),
                **{x: f[x] for x in ('sida', 'bredd', 'k', 'instans', 'barn')})


# --- patcharna --------------------------------------------------------------------------------------------------------

def patch_for(c, varde):
    """[(fil, start, slut, väntat, nytt)] för kontrollen c med det nya värdet (motorns skrivuppgift, aldrig sidans)."""
    w = c['skriv']
    if w['slag'] == 'ersatt':
        ny = varde if 'prefix' not in w else w['prefix'] + varde
        if w.get('kodning'):
            ny = kodad_text(w['kodning'], varde)
        return [(w['fil'], w['start'], w['slut'], w['vantat'], ny)]
    if w['slag'] == 'infoga':
        text = ('; ' if w.get('foreSemikolon') else ' ') + '%s: %s%s' % (w['egenskap'], varde, '' if w.get('foreSemikolon') else ';')
        return [(w['fil'], w['pos'], w['pos'], '', text)]
    if w['slag'] == 'infoga_attribut':
        return [(w['fil'], w['pos'], w['pos'], '', ' %s="%s"' % (w['namn'], varde))]
    raise ValueError('okänd skrivning')


def ordningspatch(c, ny_ordning, kalltext):
    """Sektionerna i ny ordning: varje sektions exakta text flyttas, mellanrummen och kommentarerna mellan dem står kvar."""
    w = c['skriv']
    delar_ = w['delar']
    if sorted(ny_ordning) != list(range(len(delar_))) or ny_ordning == list(range(len(delar_))):
        raise ValueError('ordningen ska vara en annan ordning av samma %d sektioner' % len(delar_))
    start, slut = delar_[0][0], delar_[-1][1]
    gammal = kalltext[start:slut]
    texter = [kalltext[a:b] for a, b in delar_]
    mellan = [kalltext[delar_[i][1]:delar_[i + 1][0]] for i in range(len(delar_) - 1)]
    ny = ''.join(texter[j] + (mellan[i] if i < len(mellan) else '') for i, j in enumerate(ny_ordning))
    return [(w['fil'], start, slut, gammal, ny)]


def tillampa(text, patchar):
    """Patcharna i en fils text bakifrån, var och en först när de förväntade bytes står på sitt läge. ValueError annars."""
    for start, slut, vantat, ny in sorted(patchar, key=lambda p: p[0], reverse=True):
        if text[start:slut] != vantat:
            raise ValueError('källan har ändrats på läget %d (väntade %r, fann %r)' % (start, vantat[:60], text[start:slut][:60]))
        text = text[:start] + ny + text[slut:]
    return text


def provcss(c, varde):
    """Den tillfälliga regeln som visar värdet i förhandsvisningen och i motorns kontroll före sparandet."""
    p = c.get('prova') or {}
    if not p.get('valjare'):
        return None
    egenskap = p['egenskap']
    v = varde
    if p.get('varden') is not None:  # en del av en kortform: hela kortformen med det nya värdet på delens plats
        vals = list(p['varden'])
        vals[p['index']] = varde
        v = ' '.join(vals)
    css = '%s{%s:%s !important}' % (p['valjare'], egenskap, v)
    for ram in reversed(p.get('ram') or []):
        css = '%s{%s}' % (ram, css)
    return css


# --- begäran och arbetaren ----------------------------------------------------------------------------------------------

def begar(dash, slug, data):
    """Ägarens bestående ändring i studion: prövas mot en ny karta, sparas och startas som flödeshandlingen studio. Samma id
    ger samma begäran (dubbelklick, tappat svar, en andra flik). Ger begäran med dess läge."""
    import flodesstart
    if not isinstance(data, dict):
        raise ValueError('ändringen ska vara ett objekt')
    rid, kid = str(data.get('andring_id') or ''), str(data.get('kandidat') or '')
    version, korning = str(data.get('version') or ''), str(data.get('korning') or '')
    if not ID.fullmatch(rid):
        raise ValueError('ett ändrings-id behövs')
    d = katalog(slug)
    atelje.saker_vag(d, atelje.UNDERLAG / slug)
    fil = d / ('%s.json' % rid)
    if fil.is_file():
        return lage_for(slug, atelje.las_json(fil) or {}, upprepat=True)
    blind, ab = _dold(dash, slug)
    if ab or blind:
        raise ValueError('studions kontroller ändrar kandidaten; gör ditt första val i körningen först' if not ab else
                         'kunden är en arm i en blind jämförelse som du inte valt i än')
    if not kandidater.ID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    if not re.fullmatch(r'[0-9a-f]{64}', version) or not korning:
        raise ValueError('ändringen ska bära körningen och kandidatens hela version, som du såg dem')
    f = fraga_ur(data)
    andringar = data.get('andringar')
    if not isinstance(andringar, list) or not 1 <= len(andringar) <= 12:
        raise ValueError('en till tolv ändringar åt gången')
    _villkor(slug, kid, version, korning)
    k = _karta(slug, kid, f)
    kontroller = {c['id']: c for lista_ in k['omraden'].values() for c in lista_}
    plan, beskr, prov_css = [], [], []
    sajt = kandidater.ksajt(slug, kid)
    for a in andringar:
        if not isinstance(a, dict):
            raise ValueError('varje ändring ska vara ett objekt')
        c = kontroller.get(str(a.get('kontroll') or ''))
        if not c:
            raise EjMappbar('kontrollen %s finns inte för elementet i den här versionen' % str(a.get('kontroll'))[:80])
        if not c.get('stod'):
            raise EjMappbar('%s: %s' % (c.get('etikett'), c.get('skal')))
        if c.get('typ') == 'ordning':
            ny_ordning = a.get('varde')
            if not isinstance(ny_ordning, list) or not all(isinstance(x, int) for x in ny_ordning):
                raise ValueError('sektionsordningen är en lista av index')
            text = (sajt / c['skriv']['fil']).read_text(encoding='utf-8')
            plan += ordningspatch(c, ny_ordning, text)
            beskr.append({'kontroll': c['id'], 'etikett': c['etikett'], 'fore': c['varde'], 'efter': [c['varde'][i] for i in ny_ordning],
                          'rackvidd': c['rackvidd']['text']})
            continue
        if c.get('typ') == 'text':
            v = re.sub(r'\s+', ' ', str(a.get('varde') or '')).strip()
            kodad_text(c['skriv'].get('kodning'), v)  # ValueError före något sparas
            if v == c.get('varde'):
                raise ValueError('texten är redan "%s"' % v[:60])
            plan += patch_for(c, v)
            beskr.append({'kontroll': c['id'], 'etikett': 'Text', 'egenskap': 'text', 'fore': c.get('varde'), 'efter': v,
                          'rackvidd': c['rackvidd']['text'], 'kalla': c.get('kalla')})
            continue
        v = validera(c['typ'], a.get('varde'), c.get('val'))
        if v == c.get('varde'):
            raise ValueError('%s har redan värdet %s' % (c['etikett'], v))
        plan += patch_for(c, v)
        beskr.append({'kontroll': c['id'], 'etikett': c['etikett'], 'egenskap': c.get('egenskap'), 'fore': c.get('varde'), 'efter': v,
                      'rackvidd': c['rackvidd']['text'], 'kalla': c.get('kalla'), 'token': c.get('token')})
        css = provcss(c, v)
        if css:
            prov_css.append(css)
    # samma läge får inte skrivas två gånger i en begäran
    per_fil = {}
    for fil_, start, slut, vantat, ny in plan:
        for s2, e2 in per_fil.get(fil_, []):
            if start < e2 and s2 < slut or (start == slut == s2):
                raise ValueError('två ändringar skriver på samma ställe i %s; spara dem var för sig' % fil_)
        per_fil.setdefault(fil_, []).append((start, slut))
    # det förväntade: motorns sond med de provade värdena (samma regel som förhandsvisningen) i ägarens bredd, en
    # mellanbredd och 390, före och efter i samma webbläsare; strukturändringarna prövas mot markupen efter bygget
    tacker = []
    for b in beskr:
        c = kontroller[b['kontroll']]
        tacker += c.get('tacker') or ([c['egenskap']] if c.get('egenskap') in TYP else [])
    tacker = list(dict.fromkeys(tacker))
    bredder = sorted({f['bredd'], MELLANBREDD, 390})
    s = sonda(slug, kid, f, tacker or ['display'], prova_css='\n'.join(prov_css) or None, alla=tacker or ['display'], bredder=bredder)
    if s.get('fel'):
        raise EjMappbar('motorns kontroll av värdet nådde inte elementet: %s' % s['fel'])
    forvantat = {}
    for bredd in bredder:
        fore, efter = (s.get('bredder') or {}).get(str(bredd)) or {}, (s.get('efter') or {}).get(str(bredd)) or {}
        if fore.get('fel') or efter.get('fel'):
            raise EjMappbar('motorns kontroll av värdet nådde inte elementet i %d px: %s' % (bredd, fore.get('fel') or efter.get('fel')))
        forvantat[str(bredd)] = {'efter': {p: (efter.get('egenskaper') or {}).get(p, {}).get('berakn') for p in tacker} if prov_css else {},
                                 'fore': {p: (fore.get('egenskaper') or {}).get(p, {}).get('berakn') for p in tacker},
                                 'spill_fore': (fore.get('spill') or {}).get('spill'), 'alla_fore': fore.get('alla') if tacker else None}
    struktur = []
    fs = (s.get('bredder') or {}).get(str(f['bredd'])) or {}
    for b in beskr:
        c = kontroller[b['kontroll']]
        if c.get('typ') == 'ordning':
            barn = (fs.get('foralder') or {}).get('barn') or []
            ordning = [i for i in next(a['varde'] for a in andringar if a.get('kontroll') == c['id'])]
            struktur.append({'slag': 'ordning', 'barn_efter': [barn[i]['markup'] for i in ordning] if len(barn) == len(ordning) else None})
        elif c.get('egenskap') == 'text':
            struktur.append({'slag': 'text', 'text': next(x['efter'] for x in beskr if x['kontroll'] == c['id'])})
        elif c.get('egenskap') == 'prop' and c.get('rot_k'):
            rf = dict(f, k=c['rot_k'], instans=0, barn=None)
            r = sonda(slug, kid, rf, ['display'])
            if r.get('fel'):
                raise EjMappbar('komponentens rotelement nåddes inte: %s' % r['fel'])
            struktur.append({'slag': 'prop', 'markup_fore': r.get('markup'), 'fraga': rf})
    post = {'schema': 'studio/1', 'id': rid, 'tid': atelje.nu(), 'avsandare': 'ägaren', 'slug': slug, 'kandidat': kid, 'korning': korning,
            'fran_version': version, 'fraga': f, 'del': str(data.get('del') or '')[:200] or None, 'andringar': beskr,
            'patchar': [{'fil': p[0], 'start': p[1], 'slut': p[2], 'vantat': p[3], 'ny': p[4]} for p in plan],
            'filsha': {p[0]: k['filsha'].get(p[0]) for p in plan}, 'forvantat': forvantat, 'tacker': tacker, 'struktur': struktur,
            'status': 'begard'}
    d.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(fil, post)
    try:
        rc = flodesstart.starta(slug, 'studio', rid)
    except ValueError as e:
        atelje.skriv_json_atomiskt(fil, dict(post, status='nekad', skal=str(e)[:400], slut=atelje.nu()))
        raise Inaktuell('ändringen startades inte: %s' % e) from e
    return dict(lage_for(slug, atelje.las_json(fil) or post), slutkod=rc, upprepat=False)


def lage_for(slug, post, upprepat=None):
    """En begärans läge: köad, pågår, klar, återställd, konflikt, fel, stoppad eller nekad, ur posten och journalen."""
    import flodesstart
    ut = {k: post.get(k) for k in ('id', 'tid', 'kandidat', 'fran_version', 'till_version', 'del', 'andringar', 'skal', 'slut', 'status',
                                   'kontroll', 'fraga')}
    if post.get('status') == 'begard':
        try:
            _p, j = flodesstart.post(slug, post.get('id'))
        except ValueError:
            j = None
        if j and j.get('status') == 'slut':
            ut['status'] = 'stoppad' if j.get('slutkod') == 4 else 'fel'
            ut['skal'] = ut.get('skal') or ('stoppad i Byggflöde' if j.get('slutkod') == 4 else 'arbetet slutade utan besked (slutkod %s)' % j.get('slutkod'))
        else:
            ut['status'] = 'pagar' if j and j.get('status') == 'startad' else 'koad'
    if upprepat is not None:
        ut['upprepat'] = upprepat
    return ut


def lista(slug, korning=None, antal=8):
    """De senaste begärningarna (nyast sist), för arbetsytans läge."""
    d = katalog(slug)
    if not d.is_dir() or d.is_symlink():
        return []
    poster = [atelje.las_json(p) or {} for p in d.glob('*.json') if not p.is_symlink()]
    poster = sorted((p for p in poster if p.get('schema') == 'studio/1' and (korning is None or p.get('korning') == korning)),
                    key=lambda p: p.get('tid') or '')
    return [lage_for(slug, p) for p in poster[-antal:]]


def _skriv(p, text):
    tmp = p.with_name('.%s.nwp-studio.tmp' % p.name)
    tmp.write_text(text, encoding='utf-8')
    os.replace(tmp, p)


def verifiera(slug, kid, post):
    """Efter bygget: det förväntade beräknade värdet i varje prövad bredd, inget nytt sidled-spill och inga ändrade
    element utanför räckvidden. [] när allt stämmer, annars skälen."""
    fel = []
    f = post['fraga']
    tacker = post.get('tacker') or []
    bredder = sorted(int(x) for x in (post.get('forvantat') or {}))
    alla = sonda(slug, kid, f, tacker or ['display'], alla=tacker or ['display'], bredder=bredder) if bredder else {}
    if alla.get('fel'):
        return ['sonden nådde inte elementet efter bygget (%s)' % alla['fel']]
    for bredd, v in (post.get('forvantat') or {}).items():
        s = (alla.get('bredder') or {}).get(str(bredd)) or {}
        if s.get('fel') or not s:
            fel.append('%s px: sonden nådde inte elementet (%s)' % (bredd, s.get('fel')))
            continue
        for p, forv in (v.get('efter') or {}).items():
            nu_ = (s.get('egenskaper') or {}).get(p, {}).get('berakn')
            if forv is not None and nu_ != forv:
                fel.append('%s px: %s blev %s, väntat %s' % (bredd, p, nu_, forv))
        if (s.get('spill') or {}).get('spill') and not v.get('spill_fore'):
            fel.append('%s px: ändringen gav sidled-spill' % bredd)
        fore, efter = v.get('alla_fore') or {}, s.get('alla') or {}
        mal = '%s#' % f['k']
        andra = [x for x in efter if not x.startswith(mal) and x in fore and fore[x] != efter[x]]
        # en regel som träffar fler element (räckvidden regel, komponent eller designgrund) får ändra dem; ett objekt får inte
        bara_objekt = all((b.get('rackvidd') or '').startswith(('detta objekt', 'alla ')) for b in post.get('andringar') or [])
        if andra and bara_objekt:
            fel.append('%s px: %d element utanför räckvidden ändrades (%s)' % (bredd, len(andra), ', '.join(andra[:3])))
    fs = (alla.get('bredder') or {}).get(str(f['bredd'])) or {}
    for x in post.get('struktur') or []:
        if x['slag'] == 'ordning':
            nu_ = [b.get('markup') for b in (fs.get('foralder') or {}).get('barn') or []]
            if x.get('barn_efter') is None or nu_ != x['barn_efter']:
                fel.append('sektionerna står inte i den nya ordningen efter bygget')
        elif x['slag'] == 'text':
            if re.sub(r'\s+', ' ', fs.get('text') or '').strip() != x['text']:
                fel.append('texten på sidan blev "%s", väntat "%s"' % ((fs.get('text') or '')[:60], x['text'][:60]))
        elif x['slag'] == 'prop':
            r = sonda(slug, kid, x['fraga'], ['display'])
            if r.get('fel') or r.get('markup') == x.get('markup_fore'):
                fel.append('komponentens markup ändrades inte av varianten (%s)' % (r.get('fel') or 'samma markup'))
    return fel


def kor(slug, rid):
    """Flödesarbetaren (under kundens startlås och kandidatens skrivlås): pröva igen, bevara grundversionen, skriv
    patcharna, bygg och fotografera, kontrollera resultatet; annars originalet tillbaka. Slutkod 0 klar, 3 konflikt, fel
    eller återställd."""
    fil = katalog(slug) / ('%s.json' % rid)
    atelje.saker_vag(fil, atelje.UNDERLAG / slug)
    post = atelje.las_json(fil) or {}
    if post.get('schema') != 'studio/1' or post.get('status') != 'begard':
        print('ingen begärd studioändring med id %s' % rid, file=sys.stderr)
        return 2

    def slut(status, skal, **extra):
        atelje.skriv_json_atomiskt(fil, dict(post, status=status, skal=skal[:900], slut=atelje.nu(), **extra))
        print('%s: %s' % (status, skal))
        return 0 if status == 'klar' else 3
    kid = post['kandidat']
    try:  # en skrivare per kandidat (DS4): körningens kedja för kandidaten eller en annan ändring blir klar först
        with kandidater.skrivlas(slug, kid, vem='studions ändring %s' % rid):
            return _kor_last(slug, rid, post, kid, slut)
    except kandidater.Upptagen as e:
        return slut('konflikt', '%s; ändringen gjordes inte' % e)


def _kor_last(slug, rid, post, kid, slut):
    """kor under kandidatens skrivlås."""
    sajt = kandidater.ksajt(slug, kid)
    per_fil = {}
    for p in post['patchar']:
        per_fil.setdefault(p['fil'], []).append((p['start'], p['slut'], p['vantat'], p['ny']))
    original, nya = {}, {}
    try:
        _villkor(slug, kid, post['fran_version'], post['korning'])
        for rel, ps in per_fil.items():
            p = atelje.saker_vag(sajt / rel, sajt / 'src')
            text = p.read_text(encoding='utf-8')
            if hashlib.sha256(text.encode('utf-8')).hexdigest() != (post.get('filsha') or {}).get(rel):
                raise Inaktuell('filen %s har ändrats sedan ändringen knöts till den' % rel)
            original[rel] = text
            nya[rel] = tillampa(text, ps)
    except (Inaktuell, ValueError, OSError) as e:
        return slut('konflikt', str(e))
    fore_st = kandidater.las_status(slug, kid)
    kandidater.bevara_version(slug, kid, post['fran_version'], bilder=True)  # före/efter, och vägen tillbaka
    skrivna = []
    try:
        for rel, text in nya.items():
            _skriv(sajt / rel, text)
            skrivna.append(rel)
    except OSError as e:  # en fil som inte gick att skriva: de redan skrivna läggs tillbaka, inget anges som klart
        for rel in skrivna:
            if (sajt / rel).read_text(encoding='utf-8') == nya[rel]:
                _skriv(sajt / rel, original[rel])
        return slut('aterstalld', 'skrivningen föll (%s); de redan skrivna filerna är tillbaka' % e)
    forvantad = kandidater.projektets_version(slug, kid)
    st = kandidater.fotografera(slug, kid)
    v = str(st.get('version') or '')
    bygget_foll = 'bygget föll' in str(st.get('skal') or '')
    brister = [] if bygget_foll or v != forvantad else verifiera(slug, kid, post)
    if not bygget_foll and v == forvantad and not brister:
        # kandidatens kategori står kvar: en vald eller förfinad kandidat är fortfarande vald eller förfinad, i sin nya
        # version (ett godkännande gäller sin version och blir historiskt, DS-U30)
        fore = fore_st.get('status')
        if st.get('status') == 'klar' and fore in ('vald', 'forfinad', 'jamfors', 'godkand'):
            st = kandidater.satt_status(slug, kid, 'forfinad' if fore == 'godkand' else fore,
                                        'studions ändring %s; ny version %s' % (rid, v[:12]))
        return slut('klar', 'ändringen står i källan (%s), sajten är ombyggd, fotograferad och kontrollerad: version %s (kandidatens status: %s)'
                    % (', '.join(sorted(nya)), v[:12], st.get('status')), till_version=v, kandidatstatus=st.get('status'))
    skal = str(st.get('skal') or '')[:300] if bygget_foll else ('versionen blev inte den väntade' if v != forvantad else '; '.join(brister)[:500])
    osakra = []
    for rel in nya:  # originalet tillbaka bara där filen fortfarande är den som skrevs: en senare ändring skrivs aldrig över
        p = sajt / rel
        if p.read_text(encoding='utf-8') == nya[rel]:
            _skriv(p, original[rel])
        else:
            osakra.append(rel)
    st2 = kandidater.fotografera(slug, kid)
    if fore_st.get('status') in ('vald', 'forfinad', 'jamfors') and st2.get('status') == 'klar':
        kandidater.satt_status(slug, kid, fore_st['status'], 'studions ändring %s återställd' % rid)
    return slut('aterstalld', '%s; originalet är tillbaka (version %s)%s' % (
        skal, str(st2.get('version') or '?')[:12], ('; ändrade efter skrivningen och därför inte återställda: %s' % ', '.join(osakra)) if osakra else ''),
        till_version=st2.get('version'), osakra=osakra or None)


def main(argv=None):
    a = argparse.ArgumentParser(prog='studio', description=__doc__.split('\n\n')[0])
    a.add_argument('slug')
    a.add_argument('--kor', required=True, metavar='ID')
    v = a.parse_args(argv)
    if not atelje.SLUG.fullmatch(v.slug) or not ID.fullmatch(v.kor):
        return 2
    if not os.environ.get('NWP_FLODE_START_ID') == v.kor:
        print('studions ändringar körs av flodesstart under kundens startlås, inte för sig', file=sys.stderr)
        return 2
    return kor(v.slug, v.kor)


if __name__ == '__main__':
    sys.exit(main())
