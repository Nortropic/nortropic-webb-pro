"""Provfixtur för referenskontraktet (kontroller/referenskontrakt.py, version 1): ett syntetiskt, fångat referenspaket
och en plan vars genomgångar och kandidatkedjor uppfyller kontraktet. Äldre flödesprov som prövar annat än
referensunderlaget (profileringen, planprövningen, skisskritiken) använder den i stället för att kringgå startvillkoret;
fixturen bevisar mekaniken, aldrig en verklig research eller designkvalitet.

    plan = referensfixtur.uppfyll(underlag, slug, plan)       # paketet byggs, planen kompletteras (kandidaterna med)
    referensfixtur.logg()                                     # en sökning och ett Awwwards-besök i researchens form
"""
import json
from pathlib import Path

PNG = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000') + b'\x00' * 20
TEXT = 'Rubriken bär ett konkret erbjudande i första vyn med pris och nästa kurstillfälle synligt direkt'
BRANSCH = ('fixtur-bransch-a', 'fixtur-bransch-b', 'fixtur-bransch-c')
GALLERI = ('fixtur-galleri-a', 'fixtur-galleri-b')


def _sajt(paket, namn, roll, upptackt):
    kat = Path(paket) / namn / '01-start'
    kat.mkdir(parents=True, exist_ok=True)
    for b in ('390', '1440'):
        (kat / ('vy-%s-forsta.png' % b)).write_bytes(PNG)
    (kat / 'SEKTIONER.md').write_text('# Sektioner (fixtur)\n', encoding='utf-8')
    (kat / 'vy-390-aria.txt').write_text('- form "Boka": textbox "Namn", button "Skicka"\n', encoding='utf-8')  # funktionsbelägg
    return {'namn': namn, 'adress': 'https://%s.example/' % namn, 'roll': roll, 'ok': True, 'upptackt': upptackt, 'uppgift': ['komposition'],
            'sidor': [{'sida': '/', 'katalog': '%s/01-start' % namn, 'ok': True}]}


def paket(underlag, slug, namn='paket-v01'):
    p = Path(underlag) / slug / 'referenser' / namn
    if (p / 'PAKET.json').is_file():
        return p
    kand = [_sajt(p, n, 'bransch', {'vag': 'websok', 'kalla': 'fixturens sökning'}) for n in BRANSCH]
    kand += [_sajt(p, n, 'hantverk', {'vag': 'galleri', 'kalla': 'https://www.awwwards.com/sites/%s' % n}) for n in GALLERI]
    (p / 'PAKET.json').write_text(json.dumps({'schema': 2, 'version': namn, 'kandidater': kand}), encoding='utf-8')
    return p


def belagg(slug, namn, paketnamn='paket-v01'):
    return 'underlag/%s/referenser/%s/%s/01-start/vy-1440-forsta.png' % (slug, paketnamn, namn)


def bidrag(slug, paketnamn='paket-v01'):
    return [{'kalla': BRANSCH[0], 'roll': 'bransch', 'uppgift': 'kontakt', 'kundbehov': 'besökaren vill boka eller ringa snabbt',
             'observerad_kvalitet': TEXT, 'matbart': False, 'beslut': 'infor', 'designbeslut': 'kontaktvägen först med tydlig handling intill',
             'tillampning': 'den primära handlingen överst i första vyn i båda bredderna', 'bedomning': 'jämför 390 första vyn mot beläggets 390',
             'belagg': [belagg(slug, BRANSCH[0], paketnamn)]},
            {'kalla': GALLERI[0], 'roll': 'visuellt', 'uppgift': 'bildregi', 'kundbehov': 'visa arbetet och händerna i verkligt material',
             'observerad_kvalitet': TEXT, 'matbart': False, 'beslut': 'anpassar', 'designbeslut': 'stor beskuren arbetsbild med kort rubrik över',
             'tillampning': 'helbild i första vyn beskuren efter bildens uppgift', 'bedomning': 'jämför 1440 första vyn mot beläggets 1440',
             'belagg': [belagg(slug, GALLERI[0], paketnamn)]}]


def branschrad(slug, n, paketnamn='paket-v01'):
    return {'sajt': n, 'varfor_studera': TEXT, 'stark_for': 'stark webbplatsreferens för en tydlig bokningsväg i mobilen', 'evidens': 'egen_observation',
            'lokal_marknad': 'ej relevant för uppgiften', 'anseende': 'okänt', 'affarsframgang': 'okänt', 'erbjudande': TEXT, 'tjanster_priser': TEXT,
            'fortroende': TEXT, 'navigation_kontakt': TEXT, 'bilder_identitet': TEXT, 'mobil': TEXT, 'tillganglighet': 'fokus syns på länkarna',
            'styrkor': TEXT, 'svagheter': TEXT, 'mojligheter': TEXT, 'tar_med': 'kurslistan med datum överst', 'undviker': 'den täta sidfoten',
            'observation': TEXT, 'tolkning': 'besökaren hittar nästa kurstillfälle snabbt', 'belagg': [belagg(slug, n, paketnamn)]}


def forebild(slug, n, paketnamn='paket-v01'):
    return {'sajt': n, 'galleri': 'awwwards', 'stark_for': 'stark webbplatsreferens för bildregi med beskurna arbetsbilder', 'kvalitet': TEXT,
            'kundens_material': TEXT, 'tillganglighet': 'kontrasten i bildtexterna är låg', 'tar_med': 'helbilden i första vyn',
            'undviker': 'den skrollstyrda rörelsen', 'begransningar': 'en stillbild visar ingen rörelse', 'belagg': [belagg(slug, n, paketnamn)]}


def uppfyll(underlag, slug, plan):
    """Planen kompletterad till kontraktet: paketet, version, genomgångarna och varje kandidats bidrag (bara där de
    saknas, så att ett prov kan göra sin egen kedja)."""
    paket(underlag, slug)
    plan = dict(plan or {})
    plan.setdefault('paket', 'paket-v01')
    plan.setdefault('referenskontrakt', {'version': 1, 'brister': [], 'tid': '2026-10-10T00:00:00Z'})
    plan.setdefault('bransch', [branschrad(slug, n) for n in BRANSCH])
    plan.setdefault('forebilder_utanfor', [forebild(slug, n) for n in GALLERI])
    plan['kandidater'] = {kid: (dict(k, referensbidrag=bidrag(slug)) if isinstance(k, dict) and not k.get('referensbidrag') else k)
                          for kid, k in (plan.get('kandidater') or {}).items()}
    return plan


def logg():
    return [{'verktyg': 'WebSearch', 'fraga': 'fixturens bransch', 'url': None, 'fel': None, 'traffar': ['https://%s.example/' % BRANSCH[0]]},
            {'verktyg': 'WebFetch', 'fraga': None, 'url': 'https://www.awwwards.com/sites/%s' % GALLERI[0], 'fel': None,
             'traffar': ['https://%s.example/' % GALLERI[0]]}]


def forskning(underlag, slug, post=None):
    """En sparad research i kontraktets form (för prov som återupptar på en sparad FORSKNING.json)."""
    paket(underlag, slug)
    return dict(post or {}, sok=logg(), urvalsfragor=URVALSFRAGOR, tackning=TACKNING,
                referenskontrakt={'version': 1, 'brister': [], 'paket': 'paket-v01'})


URVALSFRAGOR = {'fragor': ['hur visar starka sajter nästa kurstillfälle'], 'kundbehov': ['boka en kursplats i mobilen'],
                'material': ['inga egna foton ännu'], 'kvaliteter': ['bokningsväg', 'bildregi']}
TACKNING = {'varfor_racker': 'tre fångade branschsajter och två galleriförebilder täcker bokning och bildregi', 'luckor': ['ingen sajt med prislista']}


def uppdrag(underlag, slug, plan, kid, forst=''):
    """UPPDRAG.md med provets egen text först och referensunderlaget ur planen (referenskontrakt.skaparunderlag), så att
    startvillkoret ser underlaget ur just den planen."""
    import referenskontrakt
    d = Path(underlag) / slug / 'atelje' / 'kandidater' / kid
    d.mkdir(parents=True, exist_ok=True)
    (d / 'UPPDRAG.md').write_text(forst + '\n' + '\n'.join(referenskontrakt.skaparunderlag(slug, underlag, plan, kid)[0]) + '\n', encoding='utf-8')


def webbhandelser():
    """Researchens webbsökning och Awwwards-besök som transkripthändelser (verktyg, indata, svar) för de prov som bygger
    transkript ur sådana tupler: en lyckad sökning som visar en branschsajt och en hämtad galleriobjektsida."""
    return [('WebSearch', {'query': 'fixturens bransch och tjänster'}, 'Links: [{"url":"https://%s.example/"}]' % BRANSCH[0]),
            ('WebFetch', {'url': 'https://www.awwwards.com/sites/%s' % GALLERI[0], 'prompt': 'vilken sajt och utmärkelse'},
             'Sajten är https://%s.example/ (Site of the Day)' % GALLERI[0])]


def komplettera_paket(underlag, slug, paketnamn='paket-v01', arv=None):
    """Lägger fixturens fångade sajter i ett befintligt eller nytt paket (PAKET.json behåller sina andra poster); arv märker
    dem som återanvända ur ett tidigare paket, så att provets egna nya sajter står ensamma som nya."""
    p = Path(underlag) / slug / 'referenser' / paketnamn
    try:
        d = json.loads((p / 'PAKET.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        d = {'schema': 2, 'version': paketnamn, 'kandidater': []}
    namn = {k.get('namn') for k in d.get('kandidater') or [] if isinstance(k, dict)}
    nya = [_sajt(p, n, 'bransch', {'vag': 'websok', 'kalla': 'fixturens sökning'}) for n in BRANSCH if n not in namn]
    nya += [_sajt(p, n, 'hantverk', {'vag': 'galleri', 'kalla': 'https://www.awwwards.com/sites/%s' % n}) for n in GALLERI if n not in namn]
    for k in nya:
        if arv:
            k['arv'] = arv
    d['kandidater'] = list(d.get('kandidater') or []) + nya
    (p / 'PAKET.json').write_text(json.dumps(d), encoding='utf-8')
    return p


def planfalt(slug, paketnamn='paket-v01'):
    """Planens genomgångar ur fixturens sajter i paketet (för prov som skriver planens svar själva)."""
    return {'bransch': [branschrad(slug, n, paketnamn) for n in BRANSCH], 'forebilder_utanfor': [forebild(slug, n, paketnamn) for n in GALLERI]}


def webbsteg():
    """Samma webbhändelser som webbhandelser(), som (verktyg, indata, fel, svar) för prov vars transkript tar ett fel och ett svar."""
    return [(n, i, False, t) for n, i, t in webbhandelser()]
