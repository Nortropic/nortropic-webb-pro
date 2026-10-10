#!/usr/bin/env python3
"""direktredigering.py — ägarens direktredigering av en entydig text i en kandidat (E6/U23; Nortropic.app, 2026-10-10).

Räckvidd (det som stöds, inget annat): en sammanhängande text på en rad, 2–500 tecken, som står exakt en gång i
kandidatens källa (sidorna i src/pages och komponenterna, layouterna och data i resten av src/, utom kundens bilder):
  - i en .astro- eller .html-mall som en egen text mellan taggar (inte i ett attribut, ett uttryck, <script> eller <style>),
  - i frontmatter som en hel strängliteral ('…', "…" eller `…` utan ${}),
  - i en .json-fil som ett helt strängvärde, eller i brödtexten i en .md-fil.
En text som inte går att knyta så (ingen träff, flera träffar, delad av taggar, ett uttryck) ändras aldrig: arbetsytan
erbjuder ett uppdrag (Rätta) med texten i stället (EjMappbar).

Vägen: arbetsytan begär ändringen (begar) bunden till körningen och kandidatens hela version; begäran sparas i
underlag/<slug>/arbetsyta/redigeringar/<id>.json och startas som flödeshandlingen `redigera` genom flodesstart, som håller
kundens startlås under hela arbetet och journalför det (samma start som helbygget och exporten; Byggflöde visar det som
pågående och kan stoppa det). Arbetaren (kor) prövar allt igen under låset, bevarar grundversionen, skriver texten i
kandidatens projekt (kunder/<slug>/kandidater/<kid>/sajt/src), och bygger och fotograferar om med kandidatens
ordinarie fotografering (kandidater.fotografera): den nya koden blir kandidatens nästa version, bevarad som varje annan,
och det är den som godkänns, installeras i helbygget (atelje.installera_godkand) och exporteras. Föll bygget läggs den
ursprungliga texten tillbaka och kandidaten fotograferas om.

Ingen AI skriver samtidigt: en körning som arbetar eller inte väntar på ägaren nekar begäran, och startlåset håller
arbetaren och ateljén isär. Ägarens direktredigeringar följer med i kommande uppdrag (skapande.direktredigeringar i
kritikrader), så att en
senare plan inte skriver tillbaka den gamla texten utan att ett beslut säger det.

Kör: .venv/bin/python kontroller/direktredigering.py <slug> --kor <id>   (bara av flodesstart, under startlåset)
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atelje  # noqa: E402
import kandidater  # noqa: E402

ID = re.compile(r'^[A-Za-z0-9_-]{8,80}$')
TEXTFILER = ('.astro', '.html', '.json', '.md')
MIN_TEXT, MAX_TEXT = 2, 500
SPARRAD_NY = re.compile(r'[\x00-\x1f\x7f]')


class EjMappbar(ValueError):
    """Texten kan inte knytas entydigt till kandidatens källa: arbetsytan erbjuder ett uppdrag i stället (HTTP 422)."""


class Inaktuell(ValueError):
    """Körningen, kandidatens version eller källan har ändrats sedan ägaren såg texten (HTTP 409)."""


def katalog(slug):
    return atelje.UNDERLAG / slug / 'arbetsyta' / 'redigeringar'


def normalisera(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def kallfiler(slug, kid):
    """Kandidatprojektets textfiler som en version räknas över (kandidater.projektets_version): [(väg i projektet, sökväg)]."""
    sajt = kandidater.ksajt(slug, kid)
    atelje.saker_vag(sajt, atelje.KUNDER / slug)
    ut = []
    for bas, ta_med in ((sajt / 'src' / 'pages', lambda relp: relp.parts[0] not in kandidater.MALLSIDOR), (sajt / 'src', kandidater.src_ovrigt)):
        if not bas.is_dir() or bas.is_symlink():
            continue
        for rot, kataloger, filer in os.walk(bas, followlinks=False):
            kataloger[:] = sorted(k for k in kataloger if not (Path(rot) / k).is_symlink())
            for fn in sorted(filer):
                p = Path(rot) / fn
                if p.is_symlink() or not p.is_file() or p.suffix not in TEXTFILER:
                    continue
                relp = p.relative_to(bas)
                if bas.name == 'src' and relp.parts[:1] == ('pages',):
                    continue  # sidorna räknas en gång, ur src/pages
                if ta_med(relp):
                    ut.append((str(p.relative_to(sajt)), p))
    return ut


def _monster(text):
    """Ett mönster för texten som den står i källan: blanktecken som valfria blanktecken, och tecken som en mall eller en
    sträng skriver som entitet eller escape."""
    delar = []
    for t in re.split(r'(\s+)', text):
        if not t:
            continue
        if t.isspace():
            delar.append(r'\s+')
            continue
        for c in t:
            delar.append({'&': '(?:&amp;|&)', '"': '(?:&quot;|\\\\"|")', "'": "(?:&#39;|&apos;|\\\\'|')", '<': '(?:&lt;)', '>': '(?:&gt;)'}.get(c, re.escape(c)))
    return re.compile(''.join(delar))


def _frontmatter(innehall):
    """(start, slut) för en .astro-fils frontmatter (mellan de två ---), eller None."""
    if not innehall.startswith('---'):
        return None
    m = re.search(r'\n---[ \t]*(?:\n|$)', innehall[3:])
    return (3, 3 + m.start()) if m else None


def _kontext(sokvag, innehall, start, slut):
    """Var träffen står, eller None när den inte är en egen text: mall, js (med citattecknet), json eller md."""
    fore, efter = innehall[:start], innehall[slut:]
    if sokvag.suffix == '.json':
        return ('json', '"') if fore.endswith('"') and efter.startswith('"') and not fore.endswith('\\"') else None
    if sokvag.suffix == '.md':
        fm = _frontmatter(innehall)
        if fm and start < fm[1]:
            return None
        return ('md', None) if '\n' not in innehall[start:slut] and not re.search(r'[<>{}`]', innehall[start:slut]) else None
    fm = _frontmatter(innehall) if sokvag.suffix == '.astro' else None
    if fm and fm[0] <= start < fm[1]:
        q = fore[-1:] if fore[-1:] in ('"', "'", '`') else None
        if not q or not efter.startswith(q) or fore[-2:-1] == '\\':
            return None
        if q == '`' and '${' in innehall[start:slut]:
            return None
        return ('js', q)
    # mallen: närmaste tecken av <>{} före ska stänga en tagg eller ett uttryck, och närmaste efter ska öppna ett
    sista = max((fore.rfind(c), c) for c in '<>{}')
    forsta = min(((efter.find(c) if efter.find(c) >= 0 else len(efter) + 1), c) for c in '<>{}')
    if sista[0] >= 0 and sista[1] not in '>}':
        return None
    if forsta[0] <= len(efter) and forsta[1] not in '<{':
        return None
    if re.search(r'<(script|style)\b[^>]*(?<!/)>(?:(?!</\1\s*>).)*$', fore, re.S | re.I):  # en självstängande <script … /> öppnar inget
        return None
    if fm and start < fm[0]:
        return None
    return ('mall', None)


def kartlagg(slug, kid, gammal):
    """Var texten står i kandidatens källa: {fil, kontext, citat, start, slut, kallans_text, kallsha}. EjMappbar med
    skälet när den inte står exakt en gång som en egen text."""
    text = normalisera(gammal)
    if not MIN_TEXT <= len(text) <= MAX_TEXT:
        raise EjMappbar('texten ska vara %d–%d tecken på en rad för att kunna ändras direkt' % (MIN_TEXT, MAX_TEXT))
    if re.search(r'[<>{}]', text):
        raise EjMappbar('texten innehåller tecken som hör till koden (<, >, { eller })')
    m_ = _monster(text)
    egna, andra = [], []
    for rel, p in kallfiler(slug, kid):
        try:
            innehall = p.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for m in m_.finditer(innehall):
            k = _kontext(p, innehall, m.start(), m.end())
            (egna if k else andra).append((rel, p, m, k, innehall))
    if len(egna) != 1:
        if not egna and not andra:
            raise EjMappbar('texten finns inte ordagrant i kandidatens källa (den kan vara delad av taggar, byggd av ett uttryck eller '
                            'komma ur en mall)')
        if not egna:
            raise EjMappbar('texten står bara i kod (%s), inte som en egen text' % ', '.join(sorted({x[0] for x in andra}))[:300])
        raise EjMappbar('texten står på %d ställen (%s); välj en mer avgränsad text eller gör ett uppdrag' % (
            len(egna), ', '.join(sorted({x[0] for x in egna}))[:300]))
    rel, p, m, (kontext, citat), innehall = egna[0]
    return {'fil': rel, 'kontext': kontext, 'citat': citat, 'start': m.start(), 'slut': m.end(), 'kallans_text': m.group(0),
            'kallsha': hashlib.sha256(innehall.encode('utf-8')).hexdigest(), 'text': text}


def ersattning(karta, ny):
    """Den nya texten skriven för sin plats i källan, eller ValueError med skälet."""
    ny = str(ny or '').strip()
    if not MIN_TEXT <= len(ny) <= MAX_TEXT or SPARRAD_NY.search(ny):
        raise ValueError('den nya texten ska vara %d–%d tecken på en rad' % (MIN_TEXT, MAX_TEXT))
    k, q = karta['kontext'], karta.get('citat')
    if k == 'mall':
        return html.escape(ny, quote=False).replace('{', '&#123;').replace('}', '&#125;')
    if k == 'json':
        return json.dumps(ny, ensure_ascii=False)[1:-1]
    if k == 'js':
        if '\\' in ny or q in ny or (q == '`' and '${' in ny):
            raise ValueError('texten står i en sträng i koden; den nya texten får inte innehålla %s eller \\' % q)
        return ny
    if re.search(r'[<>{}`*_#\[\]]', ny):
        raise ValueError('texten står i markdown; den nya texten får inte innehålla <, >, {, }, `, *, _, #, [ eller ]')
    return ny


def _dold(dash, slug):
    import importlib
    arbetsyta = importlib.import_module('arbetsyta')
    return arbetsyta.dold(dash, slug)


def _villkor(slug, kid, version, korning):
    """Körningen väntar på ägaren och ingen arbetare lever; kandidatens version är den ägaren såg, och projektet står i
    den versionen (ingen ofotograferad ändring). Inaktuell med skälet annars."""
    st = atelje.las_json(atelje.UNDERLAG / slug / 'atelje' / 'STATUS.json') or {}
    if korning != str(st.get('startad') or ''):
        raise Inaktuell('körningen har bytts sedan du såg texten (din %s, nu %s)' % (korning, st.get('startad')))
    if st.get('pid') and atelje.lever(st['pid']) and st.get('steg') not in atelje.AVSLUTADE:
        raise Inaktuell('en arbetare skriver i kandidaterna just nu; vänta tills körningen väntar på dig')
    if st.get('steg') not in ('klar_for_bedomning', 'fel'):
        raise Inaktuell('körningen väntar inte på ditt beslut (steg %s); texten ändras inte' % st.get('steg'))
    nu_v = str(kandidater.las_status(slug, kid).get('version') or '')
    if version != nu_v:
        raise Inaktuell('kandidaten har en ny version sedan du såg texten (din %s, nu %s)' % (version[:12], nu_v[:12]))
    if kandidater.projektets_version(slug, kid) != nu_v:
        raise Inaktuell('kandidatens projekt har ändringar som inte är fotograferade; texten ändras inte förrän projektet och versionen stämmer')


def karta(dash, slug, kid, text):
    """Arbetsytans förhandsfråga: kan texten ändras direkt? {ok, fil, kontext} eller {ok: False, skal}. Ändrar ingenting."""
    if not kandidater.ID.fullmatch(str(kid or '')) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    blind, ab = _dold(dash, slug)
    if ab:
        raise ValueError('kunden är en arm i en blind jämförelse som du inte valt i än')
    if blind:
        return {'ok': False, 'skal': 'direktredigering ändrar kandidaten; gör ditt första val i körningen först', 'alternativ': 'uppdrag'}
    try:
        k = kartlagg(slug, kid, text)
    except EjMappbar as e:
        return {'ok': False, 'skal': str(e), 'alternativ': 'uppdrag'}
    return {'ok': True, 'fil': k['fil'], 'kontext': k['kontext'], 'text': k['text']}


def begar(dash, slug, data):
    """Ägarens direktredigering: prövas, sparas som begäran och startas som flödeshandlingen redigera (flodesstart). Samma
    id ger samma begäran (dubbelklick, tappat svar). Ger begäran med dess läge."""
    import flodesstart
    if not isinstance(data, dict):
        raise ValueError('redigeringen ska vara ett objekt')
    rid, kid = str(data.get('redigering_id') or ''), str(data.get('kandidat') or '')
    version, korning = str(data.get('version') or ''), str(data.get('korning') or '')
    if not ID.fullmatch(rid):
        raise ValueError('ett redigerings-id behövs')
    d = katalog(slug)
    atelje.saker_vag(d, atelje.UNDERLAG / slug)
    fil = d / ('%s.json' % rid)
    if fil.is_file():
        return lage_for(slug, atelje.las_json(fil) or {}, upprepat=True)
    blind, ab = _dold(dash, slug)
    if ab or blind:
        raise ValueError('direktredigering ändrar kandidaten; gör ditt första val i körningen först' if not ab else
                         'kunden är en arm i en blind jämförelse som du inte valt i än')
    if not kandidater.ID.fullmatch(kid) or kid not in kandidater.lista(slug):
        raise ValueError('okänd kandidat')
    if not re.fullmatch(r'[0-9a-f]{64}', version) or not korning:
        raise ValueError('redigeringen ska bära körningen och kandidatens hela version, som du såg dem')
    _villkor(slug, kid, version, korning)
    k = kartlagg(slug, kid, data.get('gammal'))
    ny = str(data.get('ny') or '').strip()
    ersattning(k, ny)  # ValueError före något sparas
    if normalisera(ny) == k['text']:
        raise ValueError('den nya texten är samma som den gamla')
    post = {'schema': 'redigering/1', 'id': rid, 'tid': atelje.nu(), 'avsandare': 'ägaren', 'slug': slug, 'kandidat': kid, 'korning': korning,
            'fran_version': version, 'sida': str(data.get('sida') or '')[:200] or None, 'del': str(data.get('del') or '')[:200] or None,
            'gammal': k['text'], 'ny': ny, 'karta': k, 'status': 'begard'}
    d.mkdir(parents=True, exist_ok=True)
    atelje.skriv_json_atomiskt(fil, post)
    try:
        rc = flodesstart.starta(slug, 'redigera', rid)
    except ValueError as e:
        atelje.skriv_json_atomiskt(fil, dict(post, status='nekad', skal=str(e)[:400], slut=atelje.nu()))
        raise Inaktuell('redigeringen startades inte: %s' % e) from e
    return dict(lage_for(slug, atelje.las_json(fil) or post), slutkod=rc, upprepat=False)


def lage_for(slug, post, upprepat=None):
    """En begärans läge ur posten och flödets journal: köad, pågår, klar, återställd, konflikt, fel, stoppad eller nekad."""
    import flodesstart
    ut = {k: post.get(k) for k in ('id', 'tid', 'kandidat', 'fran_version', 'till_version', 'sida', 'del', 'gammal', 'ny', 'skal', 'slut', 'status')}
    ut['fil'] = (post.get('karta') or {}).get('fil')
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


def lista(slug, korning=None, antal=5):
    """De senaste begärningarna (nyast sist), för arbetsytans läge."""
    d = katalog(slug)
    if not d.is_dir() or d.is_symlink():
        return []
    poster = [atelje.las_json(p) or {} for p in d.glob('*.json') if not p.is_symlink()]
    poster = sorted((p for p in poster if p.get('schema') == 'redigering/1' and (korning is None or p.get('korning') == korning)), key=lambda p: p.get('tid') or '')
    return [lage_for(slug, p) for p in poster[-antal:]]


def i_dist(slug, kid, karta_, ny):
    """Står den nya texten i den byggda sajten (dist/)? Det som ombyggnaden visar."""
    dist = kandidater.ksajt(slug, kid) / 'dist'
    nal = [html.escape(ny, quote=False), ny]
    for p in dist.rglob('*.html') if dist.is_dir() and not dist.is_symlink() else []:
        try:
            t = p.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        t = re.sub(r'\s+', ' ', t)
        if any(normalisera(n) in t for n in nal):
            return True
    return False


def kor(slug, rid):
    """Flödesarbetaren (under kundens startlås): pröva igen, bevara grundversionen, skriv texten, bygg och fotografera om.
    Ger slutkod 0 (klar), 3 (konflikt eller fel, inget ändrat eller återställt)."""
    fil = katalog(slug) / ('%s.json' % rid)
    atelje.saker_vag(fil, atelje.UNDERLAG / slug)
    post = atelje.las_json(fil) or {}
    if post.get('schema') != 'redigering/1' or post.get('status') != 'begard':
        print('ingen begärd redigering med id %s' % rid, file=sys.stderr)
        return 2

    def slut(status, skal, **extra):
        atelje.skriv_json_atomiskt(fil, dict(post, status=status, skal=skal[:600], slut=atelje.nu(), **extra))
        print('%s: %s' % (status, skal))
        return 0 if status == 'klar' else 3
    kid, k = post['kandidat'], post['karta']
    try:
        _villkor(slug, kid, post['fran_version'], post['korning'])
        sajt = kandidater.ksajt(slug, kid)
        p = atelje.saker_vag(sajt / k['fil'], sajt)
        innehall = p.read_text(encoding='utf-8')
        if hashlib.sha256(innehall.encode('utf-8')).hexdigest() != k['kallsha'] or innehall[k['start']:k['slut']] != k['kallans_text']:
            raise Inaktuell('filen %s har ändrats sedan texten knöts till den' % k['fil'])
        ny_kod = ersattning(k, post['ny'])
    except (Inaktuell, ValueError, OSError) as e:
        return slut('konflikt', str(e))
    kandidater.bevara_version(slug, kid, post['fran_version'], bilder=True)  # före/efter, och vägen tillbaka
    nytt = innehall[:k['start']] + ny_kod + innehall[k['slut']:]
    tmp = p.with_name('.%s.nwp-redigering.tmp' % p.name)
    tmp.write_text(nytt, encoding='utf-8')
    os.replace(tmp, p)
    forvantad = kandidater.projektets_version(slug, kid)
    st = kandidater.fotografera(slug, kid)
    v = str(st.get('version') or '')
    bygget_foll = 'bygget föll' in str(st.get('skal') or '')
    if v == forvantad and not bygget_foll and i_dist(slug, kid, k, post['ny']):
        return slut('klar', 'texten står i källan (%s), sajten är ombyggd och fotograferad: version %s (kandidatens status: %s)' % (
            k['fil'], v[:12], st.get('status')), till_version=v, kandidatstatus=st.get('status'))
    # bygget föll eller den nya texten syns inte: den ursprungliga texten tillbaka, och kandidaten fotograferas om
    skal = str(st.get('skal') or '')[:300] if bygget_foll else 'den nya texten syns inte i den byggda sajten'
    t = p.with_name('.%s.nwp-aterstall.tmp' % p.name)
    t.write_text(innehall, encoding='utf-8')
    os.replace(t, p)
    st2 = kandidater.fotografera(slug, kid)
    return slut('aterstalld', '%s; den ursprungliga texten är tillbaka (version %s)' % (skal, str(st2.get('version') or '?')[:12]),
                till_version=st2.get('version'))


def main(argv=None):
    a = argparse.ArgumentParser(prog='direktredigering', description=__doc__.split('\n\n')[0])
    a.add_argument('slug')
    a.add_argument('--kor', required=True, metavar='ID')
    v = a.parse_args(argv)
    if not atelje.SLUG.fullmatch(v.slug) or not ID.fullmatch(v.kor):
        return 2
    if not os.environ.get('NWP_FLODE_START_ID') == v.kor:
        print('direktredigeringen körs av flodesstart under kundens startlås, inte för sig', file=sys.stderr)
        return 2
    return kor(v.slug, v.kor)


if __name__ == '__main__':
    sys.exit(main())
