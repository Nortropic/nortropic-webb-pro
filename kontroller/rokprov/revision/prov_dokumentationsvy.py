#!/usr/bin/env python3
"""prov_dokumentationsvy.py — dashboardens vy Dokumentation och rapporter (ägarens uppdrag 2026-10-06, punkt 8, och
2026-10-07, punkt 9), syntetiskt men i de riktiga filernas form:

- de fyra delarna (så fungerar Nortropic, pågående uppdrag, granskningar och resultat, beslut och historik), saknat
  underlag, platsen för kompetenskedjan och slutposten, och sammanfattningen först;
- filtren: serverns svar har fälten för uppdrag eller systemdel, typ, version eller commit, datum och utfall, och vyns
  filter (dokFiltrera i index.html, körd i node) hittar rätt rapporter med dem;
- en rapport utan huvud (förteckningens äldre rapporter) ger "ej angivet", med raden "registrerad med sha256";
- ett trasigt huvud (inget avslutande ---, en rad som inte går att tolka, inte UTF-8) fäller inte vyn och visar inga
  fält ur huvudet; tolken kastar aldrig;
- rapportstatus och utfall är två skilda fält, i svaret och i vyn, och ett historiskt godkännande bär sin version;
- BESLUT.md: statusraden, märkningen Delvis ersatt av, ej angivet, en oklar hänvisning, ersättaren och vad ett tillägg
  ersätter, Återstår och rubriker i kodblock; repots egen BESLUT.md läses också;
- blindningen: före ägarens första val i en körning är vyns svar detsamma med och utan de dolda fälten (titlar, brister,
  DESIGN.md-fel, skisskritik, riktning), och inget av dem syns; en arm i en blind jämförelse visas inte; det
  fil_tillaten döljer (kalibreringen) nämns inte;
- länkarna: varje filänk öppnas genom /fil/ och fil_tillaten, varje dokument genom /api/dokument, som aldrig visar något
  under underlag/ eller kunder/, en symlänk eller något platsregeln inte pekar på;
- saknade rapporter ur koden (granskningen av rNN utan registrerad rapport), integriteten som inte är verifiering,
  fynden och rättelserna ur backloggen, avsändaren (fältet avsandare, annars "avsändaren ej belagd"), uppdragets läge
  med senaste rapport, de pågående körningarna och det som väntar på ägaren.

    .venv/bin/python kontroller/rokprov/revision/prov_dokumentationsvy.py <repo>

Allt skrivs i en temporär katalog; repots egna filer läses men ändras inte, och inga privata data läses. Varje fall
redovisas för sig på stderr; slutkod 1 när något fall föll.
"""
import http.client
import http.server
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import traceback
import zlib
from pathlib import Path
from urllib.parse import quote

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-dokvy-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
import atelje  # noqa: E402
import backlog as bl  # noqa: E402
import granska  # noqa: E402
import korregister  # noqa: E402
import prova  # noqa: E402
import server as dash  # noqa: E402
import skapande  # noqa: E402

U, K = TMP / 'underlag', TMP / 'kunder'
U.mkdir()
K.mkdir()
dash.ROOT, dash.UNDERLAG, dash.KUNDER, dash.AB = TMP, U, K, K / 'ab'
atelje.ROOT, atelje.UNDERLAG, atelje.KUNDER = TMP, U, K
granska.UNDERLAG, granska.KUNDER = U, K
skapande.UNDERLAG = U
bl.ROOT, bl.MAPP = TMP, TMP / 'backlog'
korregister.KATALOG = TMP / 'korregister'
FEL = []


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:1500]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


def skriv(p, data):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        p.write_bytes(data)
    else:
        p.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    return p


def png():
    return b'\x89PNG\r\n\x1a\n' + b''.join(struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c)) for t, c in (
        (b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)), (b'IDAT', zlib.compress(b'\x00\xff\x00\x00')), (b'IEND', b'')))


def sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def huvud(**f):
    rader = ['---']
    for k, v in f.items():
        if isinstance(v, list):
            rader += ['%s:' % k] + ['  - %s' % x for x in v]
        else:
            rader.append('%s: %s' % (k, v))
    return '\n'.join(rader + ['---', '', '# Slutsats', '', 'Text.', ''])


# ===== fixturer: repots publika filer =====

skriv(TMP / 'README.md', """# Repot i provet

## Kedjan från kundunderlag till leverans

| Steg | Vem startar | Resultat | Saknas i dag |
|---|---|---|---|
| 1. Underlaget | en session: `ny_sajt.py <slug>` | underlag | – |
| 2. Prototypen | ägaren: `prototyp.py <slug>` | förslagen | – |

## Var information finns

Tabellen bestämmer var informationen hör hemma.

| Slag | Plats och namn | Skrivs av |
|---|---|---|
| Start och överblick | den här filen; `CLAUDE.md` för sessioner | agenten |
| Gällande arbetssätt | `kunskap/<ämne>.md`; skills i `.claude/skills/<namn>/SKILL.md`; kriterier i `kritik/`. En fil börjar med `Status: historik, ersatt av …` | agenten |
| Beslut | `BESLUT.md` med raden `**Status:**` | agenten |
| Förbättringsarbete | `backlog/B-ÅÅÅÅMMDD-<namn>.md` (`backlog/README.md`) | `kontroller/backlog.py` |
| Systemgranskningar | `underlag/granskningar/GR-ÅÅÅÅMMDD-<ämne>.md` och `FORTECKNING.jsonl` | sessionen |

Allt under `underlag/` är privat.

## Nästa avsnitt

Annat.
""")
skriv(TMP / 'CLAUDE.md', '# Sessioner\n\nDet som gäller: `kunskap/designregler.md` och `copy-kontroll.md` i `kunskap/`. Beslut: `BESLUT.md`.\n')
skriv(TMP / 'kunskap' / 'designregler.md', '# Designregler\n\nKraven som gäller.\n')
skriv(TMP / 'kunskap' / 'copy-kontroll.md', '# Copykontroll\n\nRegeln mot slop.\n')
skriv(TMP / 'kunskap' / 'gammal.md', 'Status: historik, ersatt av kunskap/designregler.md\n\n# Gammal metod\n\nHistorik.\n')
skriv(TMP / 'utanfor' / 'hemlig.md', '# HEMLIG-UTANFOR\n')
(TMP / 'kunskap' / 'lankad.md').symlink_to(TMP / 'utanfor' / 'hemlig.md')
skriv(TMP / 'kritik' / 'GRANSKARE.md', '# Granskaren\n\nKriterierna.\n')
skriv(TMP / '.claude' / 'skills' / 'prov-skill' / 'SKILL.md', '---\nname: prov-skill\ndescription: En skill i provet.\n---\n\n# Provskillen\n\nText.\n')
skriv(TMP / 'backlog' / 'README.md', '# Backloggen\n\nPosterna.\n')
skriv(TMP / 'BESLUT.md', """# Beslut i provet

## Ägarens ord

Text.

## Tillägg 2026-10-01: första beslutet

Inledning.

1. **Punkt ett.** Text. **Delvis ersatt av:** tillägget 2026-10-03 om andra saken (punkt 2). Övrigt gäller.
2. **Punkt två.** Text.

## Tillägg 2026-10-02: utan status

Text utan status och utan märkning.

## Tillägg 2026-10-02, kväll: tvetydig hänvisning

**Delvis ersatt av:** tillägget 2026-10-05, kväll. Övrigt gäller.

## Tillägg 2026-10-03: andra saken

**Status:** gäller.

Text.

## Tillägg 2026-10-03: en tredje sak

**Status:** ersatt av tillägget 2026-10-05, kväll: fjärde beslutet.

Text.

## Tillägg 2026-10-05, kväll: fjärde beslutet

**Status:** gäller.

Genomförs i steg:
5. **Återstår:**
   - vyn i dashboarden;
     två rader
   - ett prov

```md
## Tillägg 2026-10-07: i ett kodblock
```

## Tillägg 2026-10-05, kväll: femte beslutet

**Status:** delvis ersatt av tillägget 2026-10-06 om sjätte saken.

## Tillägg 2026-10-06: sjätte saken

**Status:** gäller.

## Tillägg 2026-10-07: konstig status

**Status:** oklart läge.

## Tillägg 2026-10-08: kvällsreferens

**Delvis ersatt av:** tillägget 2026-10-03, kväll (punkt 1). Övrigt gäller.

## Tillägg 2026-10-03, kväll: kvällens sak

**Status:** gäller.
""")
# koden som hänvisar till granskningar (gemena r är rundor, versala R är fynd)
skriv(TMP / 'kontroller' / 'exempel.py', """# granskningen av r55, B1: en rapport som inte finns
# (granskningen av r70, H2, och r71, N5)
# omgranskningen av r56b visade något
# granskningen av r90 och r72
x = 'R1'  # Granskningen av r57 med versal; granskningen av R2 räknas inte
""")

# ===== fixturer: granskningar, förteckningen, lägesrapporter och piloten =====

G = U / 'granskningar'
skriv(G / 'GR-20261005-r90.md', huvud(
    id='GR-20261005-r90', titel='Granskning av tolken (r90)', typ='systemgranskning (före sammanslagning)',
    systemdel='kontroller/tolk.py, dashboard/server.py', moment='ej angivet', forfattare='oberoende granskare i sessionen prov',
    datum='2026-10-05', granskad_identitet='nortropic-webb-pro, gren tolk-20261005, commit abc1234 (ovanpå main 1111111)',
    rapportstatus='färdig', bedomningsutfall='underkänt för sammanslagning: 1 blockerande', forhallande='första granskningen',
    foregaende='ej angivet', ersatt_av='ej angivet', underlag='granskningar/GR-20261005-r90/',
    beslut='ägarens beslut (BESLUT.md, tillägget 2026-10-03: andra saken)',
    atgarder=['GR-20261005-r90#B1: rättas i tolk-20261005', 'GR-20261005-r90#B2 och #B3: backlogposter']))
skriv(G / 'GR-20261005-r90' / 'bevis.txt', 'mutation 1 dödad\n')
skriv(G / 'GR-20261006-r90-om.md', huvud(
    id='GR-20261006-r90-om', titel='Omgranskning av tolken', typ='systemgranskning (omgranskning)', systemdel='kontroller/tolk.py',
    forfattare='huvudsessionen i provet', avsandare='en annan granskare (Codex), inklistrad av ägaren', datum='2026-10-06',
    granskad_identitet='nortropic-webb-pro, gren tolk-20261005, commit def5678', rapportstatus='färdig',
    bedomningsutfall='godkänt för sammanslagning (inga blockerande)', forhallande='verifierar rättelsen av GR-20261005-r90#B3',
    foregaende='GR-20261005-r90', beslut='ej angivet', atgarder=['sammanslagen']))
skriv(G / 'GR-20261006-utkast.md', huvud(
    id='GR-20261006-utkast', titel='Ett utkast', typ='systemgranskning (utkast)', systemdel='kor.sh', forfattare='session prov',
    datum='2026-10-06', granskad_identitet='commit 9a9a9a9', rapportstatus='utkast', bedomningsutfall='ej bedömt',
    beslut='tillägget 2026-10-06: sjätte saken'))
skriv(G / 'GR-20261006-utan-falt.md', huvud(id='GR-20261006-utan-falt', titel='Saknar fält', typ='systemgranskning', datum='2026-10-06'))
skriv(G / 'GR-20261006-trasig.md', '---\nid: GR-20261006-trasig\ntitel: HALV-RAPPORT\n\n# Rubrik\n\nText utan slut på huvudet.\n')
skriv(G / 'GR-20261006-konstig.md', '---\nid: GR-20261006-konstig\ntitel: HALV-RAPPORT två\ndetta är ingen nyckel\n---\n\nText.\n')
skriv(G / 'GR-20261006-binar.md', b'---\nid: GR-20261006-binar\ntitel: HALV-RAPPORT tre\n\xff\xfe\n---\n')
S = G / 'sessioner' / 'abc'
r70 = skriv(S / 'GRANSKNING-r70.md', '# Granskning r70\n\nEn äldre rapport utan huvud.\n').read_bytes()
r72 = skriv(S / 'GRANSKNING-r72.md', '# Granskning r72\n\nÄndrad efter registreringen.\n').read_bytes()
skriv(S / 'svar-codex-r20.md', '# Svar från Codex\n')
skriv(U / 'kalibrering' / 'K01' / 'HEMLIG-KAL.md', '# HEMLIG-KAL\n')
FORTECKNING = [
    {'fil': 'granskningar/sessioner/abc/GRANSKNING-r70.md', 'sha256': sha(r70), 'kopierad': '2026-10-06T22:41:00Z', 'slag': 'systemgranskning', 'session': 'abc-prov', 'bas': 'underlag/'},
    {'fil': 'granskningar/sessioner/abc/GRANSKNING-r71.md', 'sha256': sha(b'borta'), 'kopierad': '2026-10-06T22:41:00Z', 'slag': 'systemgranskning', 'bas': 'underlag/'},
    {'fil': 'granskningar/sessioner/abc/GRANSKNING-r72.md', 'sha256': sha(b'som det var'), 'kopierad': '2026-10-06T22:41:00Z', 'slag': 'systemgranskning', 'bas': 'underlag/'},
    {'fil': 'granskningar/sessioner/abc/svar-codex-r20.md', 'sha256': sha((S / 'svar-codex-r20.md').read_bytes()), 'kopierad': '2026-10-06T22:41:00Z', 'slag': 'extern granskning (Codex)', 'bas': 'underlag/'},
    {'fil': 'granskningar/GR-20261005-r90/bevis.txt', 'sha256': sha((G / 'GR-20261005-r90' / 'bevis.txt').read_bytes()), 'kopierad': '2026-10-06T23:00:00Z', 'slag': 'bevis till GR-20261005-r90', 'rapport': 'GR-20261005-r90', 'bas': 'underlag/'},
    {'fil': 'granskningar/GR-20261005-r90.md', 'sha256': sha((G / 'GR-20261005-r90.md').read_bytes()), 'kopierad': '2026-10-06T23:00:00Z', 'slag': 'systemgranskning (registrerad med rapporthuvud)', 'rapport': 'GR-20261005-r90', 'bas': 'underlag/'},
    {'fil': 'kalibrering/K01/HEMLIG-KAL.md', 'sha256': sha(b'# HEMLIG-KAL\n'), 'kopierad': '2026-10-06T23:00:00Z', 'slag': 'inventering', 'bas': 'underlag/'},
]
skriv(G / 'FORTECKNING.jsonl', ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in FORTECKNING) + '{trasig rad\n')
skriv(U / 'rapporter' / 'RAPPORT-2026-10-06-lage.md', huvud(
    id='RAPPORT-2026-10-06-lage', titel='Läget i provet', typ='lägesrapport till ägaren',
    uppdrag=['första uppdraget (ägaren 2026-10-01)', 'andra uppdraget'], systemdel='nortropic-webb-pro', forfattare='huvudsessionen i provet',
    datum='2026-10-06', granskad_identitet='main 7e7e7e7', rapportstatus='färdig', bedomningsutfall='ej bedömt (lägesrapport)',
    beslut='välj mellan A och B (avsnitt 5)', atgarder='se avsnitt 5'))
skriv(U / 'kalibrering' / 'RAPPORT-hemlig.md', huvud(id='RAPPORT-hemlig', titel='HEMLIG-KALIBRERING', rapportstatus='färdig', datum='2026-10-06'))
P = U / 'figma-pilot'
skriv(P / 'BESLUTSUNDERLAG.md', '---\nid: RAPPORT-2026-10-06-pilot\ntitel: Piloten\ntyp: projektrapport (pilot)\nkund: en pilot\n'
      'datum: 2026-10-06\ngranskad_identitet:\n  A: Figma prov, v5\n  C: version C5, dist i moment-c/VERSION.json\nrapportstatus: färdig\n'
      'bedomningsutfall: godkänt mot de mätbara kriterierna\n---\n\n# Slutsats\n')
skriv(P / 'BUDGET.md', '# Budget utan huvud\n')
skriv(P / 'moment-c' / 'VERSION.json', {'moment': 'C', 'aktuell': 'C5', 'status': 'underkänt', 'status_skal': 'ägarens dom: inte ännu',
                                         'agarens_dom': {'version': 'C5', 'utfall': 'inte ännu', 'avsandare': 'ägaren (bekräftat i provet)',
                                                         'beslutstyp': 'ägarens bilddom över C5', 'fil': 'bedomningar/AGARENS-DOM-C5.md'},
                                         'granskningar': [{'version': 'C5', 'fil': 'bedomningar/BILDDOM-C5.md', 'utfall': 'når över ribban'},
                                                          # en sökväg ut ur momentet: ingen fil, ingen länk
                                                          {'version': 'C4', 'fil': '../../kalibrering/RAPPORT-hemlig.md', 'utfall': 'äldre'}]})
skriv(P / 'moment-c' / 'bedomningar' / 'AGARENS-DOM-C5.md', '# Dom\n')
skriv(P / 'moment-c' / 'bedomningar' / 'BILDDOM-C5.md', '# Bilddom\n')
skriv(P / 'moment-d' / 'VERSION.json', {'moment': 'D', 'aktuell': 'v1', 'status': 'skapat', 'agarens_dom': {'version': 'v1', 'utfall': 'nästan'},
                                         'bedomningar': {'v1': 'en text om bedömningen'}})
skriv(P / 'moment-e' / 'VERSION.json', {'moment': 'E', 'aktuell': 'v1', 'status': 'skapat',
                                         'inklistrad_dom': {'version': 'v1', 'utfall': 'över', 'avsandare': 'avsändaren ej belagd'}})

# ===== fixturer: kunderna (en körning före ditt första val, en blind jämförelse, ett helbygge) =====


def underlag_(s):
    for n in ('BRIEF.md', 'RESEARCH.md', 'TEXTUNDERLAG.md'):
        skriv(U / s / n, '# %s\n' % n)


s = 'fl-blind'
underlag_(s)
skriv(U / s / 'atelje' / 'STATUS.json', {'slug': s, 'kandidatflode': True, 'lage': 'ny', 'pid': None, 'steg': 'klar_for_bedomning',
                                          'startad': '2026-10-06T10:00:00Z', 'klar': '2026-10-06T10:50:00Z'})
skriv(U / s / 'atelje' / 'KANDIDATPLAN.json', {'tid': '2026-10-06T10:05:00Z', 'lage': 'skiss', 'antal': 2,
                                                'kandidater': {k: {'titel': 'HEMLIG-TITEL %s' % k} for k in ('k01', 'k02')}})
for kid, status, extra in (('k01', 'klar', {'version': 'a1' * 32, 'varv': 3, 'brister': ['HEMLIG-BRIST ett'], 'design_fel': ['HEMLIG-DESIGNFEL ett']}),
                           ('k02', 'under_arbete', {})):
    d = U / s / 'atelje' / 'kandidater' / kid
    skriv(d / 'STATUS.json', dict({'id': kid, 'status': status, 'skal': '', 'tid': '2026-10-06T10:20:00Z', 'titel': 'HEMLIG-TITEL %s' % kid,
                                   'logg': [{'tid': '2026-10-06T10:20:00Z', 'status': status, 'skal': ''}]}, **extra))
d1 = U / s / 'atelje' / 'kandidater' / 'k01'
skriv(d1 / 'SKISSKRITIK.json', {'storsta_problem': 'HEMLIG-KRITIK'})
skriv(d1 / 'KRITIK.json', {'niva': 'nastan', 'forsta_intryck': 'HEMLIG-KRITIK första intrycket', 'version': 'a1' * 32})
skriv(d1 / 'RIKTNING.md', '# HEMLIG-TITEL riktning\n')
for vy in ('390', '1440'):
    skriv(d1 / 'bilder' / 'start' / ('vy-%s-forsta.png' % vy), png())


def utan_dolda(s):
    """Samma fixtur utan det som är dolt före ditt första val (som prov_flode.py): planens och kandidaternas titlar,
    brister, DESIGN.md-fel, skisskritik, granskning och riktning. Ger en funktion som lägger tillbaka filerna."""
    a_ = U / s / 'atelje'
    filer = [a_ / 'KANDIDATPLAN.json'] + sorted(a_.glob('kandidater/*/*'))
    spar = {p: p.read_bytes() for p in filer if p.is_file()}
    plan_ = json.loads(spar[a_ / 'KANDIDATPLAN.json'])
    for x in (plan_.get('kandidater') or {}).values():
        x.pop('titel', None)
    skriv(a_ / 'KANDIDATPLAN.json', plan_)
    for p in sorted(a_.glob('kandidater/*/STATUS.json')):
        skriv(p, {k_: v_ for k_, v_ in json.loads(spar[p]).items() if k_ not in ('titel', 'brister', 'design_fel', 'skisskritik', 'huvudreferens')})
    for p in sorted(a_.glob('kandidater/*/*')):
        if p.name in ('SKISSKRITIK.json', 'KRITIK.json', 'RIKTNING.md'):
            p.unlink()

    def tillbaka():
        for p, b in spar.items():
            p.write_bytes(b)
    return tillbaka


AB = 'ab-prov-20261006T000000Z'
skriv(K / 'ab' / ('%s.json' % AB), {'id': AB, 'byggen': ['ab-x', 'ab-y'], 'val': None, 'variabel': 'atelje', 'verksamhet': 'Prov'})


def bygge(s, stampel='20261006T090000Z', provtid='2026-10-06T09:30:00Z', rapport='Byggets rapport. '):
    k = K / s
    skriv(k / 'sajt' / 'package.json', '{}')
    skriv(k / 'sajt' / 'dist' / 'index.html', '<p>%s</p>' % s)
    h = prova.dist_hash(k / 'sajt' / 'dist')
    skriv(k / ('korning-%s.jsonl' % stampel), '{"type": "result", "subtype": "success", "num_turns": 1, "duration_ms": 1000}\n')
    skriv(k / 'RAPPORT.md', '# Rapport\n\n' + rapport * 20)
    skriv(k / 'prov' / 'PROV.md', '# Provet\n')
    skriv(k / 'prov' / 'STATUS.json', {'ok': True, 'tid': provtid, 'dist_sha256': h, 'grindar': {'bygge': {'ok': True}}})
    skriv(k / 'prov' / 'STOPPVAKT.json', {'tid': provtid, 'korning': stampel, 'dist_sha256': h, 'slapp': True,
                                          'skal': 'kontrollerna gröna, RAPPORT.md finns och granskningen är godkänd'})


for s, andra in (('ab-x', 'ab-y'), ('ab-y', 'ab-x')):
    underlag_(s)
    skriv(K / s / 'AB-SYSKON', andra + '\n')
    bygge(s, rapport='HEMLIG-RAPPORT %s. ' % s)
underlag_('k-bygge')
bygge('k-bygge')

# ===== fixturer: backloggen och körregistret =====

bl.MAPP.mkdir(exist_ok=True)
B1 = bl.ny('granskning', 'Tolken tappar en rad', 'Syntetiskt.', forslag='Rätta tolken i `kontroller/tolk.py`.',
           kallref='granskningar/GR-20261005-r90.md', fynd='GR-20261005-r90#B1')
B2 = bl.ny('granskning', 'Provet saknar ett fall', 'Syntetiskt.', kallref='granskningar/GR-20261005-r90.md', fynd='GR-20261005-r90#B2')
bl.satt_status(B2, 'klar', commit='abc1234')
B3 = bl.ny('granskning', 'Fel i läsningen', 'Syntetiskt.', kallref='granskningar/GR-20261005-r90.md', fynd='GR-20261005-r90#B3')
bl.satt_status(B3, 'klar', commit='bcd2345')
bl.verifiera(B3, 'GR-20261006-r90-om')
B4 = bl.ny('kirurg', 'En idé från kirurgen', 'Syntetiskt.', kallref='prov')
skriv(korregister.KATALOG / ('%d.json' % os.getpid()), {'pid': os.getpid(), 'vad': 'rokprov', 'slug': None, 'start': '2026-10-07T06:00:00Z',
                                                         'utcheckning': str(TMP), 'kommando': 'prov', 'pstart': korregister.startad(os.getpid())})

# ===== servern och hjälparna =====

srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), dash.H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
dash.VARD['tillatna'] = {'127.0.0.1:%d' % srv.server_port}


def hamta(vag):
    c = http.client.HTTPConnection('127.0.0.1', srv.server_port, timeout=60)
    c.request('GET', vag, headers={'Host': '127.0.0.1:%d' % srv.server_port})
    r = c.getresponse()
    data = r.read()
    c.close()
    return r.status, data


def svaret():
    kod, data = hamta('/api/dokumentation')
    assert kod == 200, (kod, data[:300])
    return json.loads(data)


def alla(d, nyckel):
    """Varje strängvärde under nyckeln, var som helst i svaret."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == nyckel and isinstance(v, str):
                yield v
            else:
                yield from alla(v, nyckel)
    elif isinstance(d, list):
        for x in d:
            yield from alla(x, nyckel)


def rapport(d, ident):
    return next(r for r in d['granskningar']['rapporter'] if r['id'] == ident or (r.get('fil') or {}).get('sokvag') == ident)


HEMLIGT = re.compile(r'HEMLIG-[A-ZÅÄÖ]+')
VY_JS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8'), data = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const filter = JSON.parse(process.argv[4]);
const a = html.indexOf('// <dokumentationsvyn>'), b = html.indexOf('// </dokumentationsvyn>');
if (a < 0 || b < 0) throw new Error('dokumentationsvyn saknas i index.html');
const rader = html.split('\n');
const rad = (borjan) => { const r = rader.find((x) => x.startsWith(borjan)); if (!r) throw new Error('saknas i index.html: ' + borjan); return r; };
const kod = [rad('const esc = '), rad('const tid = '), rad('const FLODESTATUS = '), rad('const flodechip = '), rad('const kodtext = '), html.slice(a, b)].join('\n');
const f = new Function('data', 'filter', kod + `
  return {
    filter: filter.map((x) => dokFiltrera(data.granskningar.rapporter, x).map((r) => dokNamn(r))),
    sammanfattning: dokSammanfattning(data), instruktioner: dokInstruktioner(data), pagaende: dokPagaende(data),
    granskningar: dokGranskningar(data, ''), beslut: dokBeslut(data, ''), saknat: dokSaknatKort(data, false), senare: dokSenare(data),
    rapporter: Object.fromEntries(data.granskningar.rapporter.map((r) => [dokNamn(r), dokRapport(r, true)])),
  };`);
process.stdout.write(JSON.stringify(f(data, filter)));
"""
FILTER = [{}, {'typ': 'systemgranskning'}, {'utfall': 'godkänt'}, {'utfall': 'underkänt'}, {'status': 'utkast'}, {'version': 'def5678'},
          {'version': 'abc1234'}, {'fran': '2026-10-06', 'till': '2026-10-06'}, {'till': '2026-10-05'}, {'uppdrag': 'kontroller/tolk.py'},
          {'uppdrag': 'andra uppdraget'}, {'q': 'GRANSKNING-r70'}, {'exakt': 'GR-20261005-r90'}, {'typ': 'lägesrapport till ägaren', 'status': 'färdig'}]


def vyn(d):
    (TMP / 'vy.js').write_text(VY_JS, encoding='utf-8')
    (TMP / 'vy.json').write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    r = subprocess.run(['node', str(TMP / 'vy.js'), str(ROOT / 'dashboard' / 'index.html'), str(TMP / 'vy.json'), json.dumps(FILTER)],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and r.stdout, r.stderr[-800:]
    return json.loads(r.stdout)


SVAR = {}


def svar():
    if 'd' not in SVAR:
        SVAR['d'] = svaret()
    return SVAR['d']


# ===== fallen =====

@fall('de fyra delarna, saknat underlag, platsen för kompetenskedjan och sammanfattningen först')
def _delarna():
    d = svar()
    assert {'sammanfattning', 'instruktioner', 'pagaende', 'granskningar', 'beslut', 'saknat', 'senare'} <= set(d), sorted(d)
    assert d['fel'] == {}, d['fel']
    s = d['sammanfattning']
    assert {'instruktioner', 'pagaende', 'granskningar', 'fynd', 'beslut', 'historik', 'saknat', 'vantar', 'senaste'} <= set(s), sorted(s)
    assert d['instruktioner']['grupper'] and d['instruktioner']['kedjan']['steg'] and d['beslut']['tillagg'], 'en del är tom'
    assert {k: s['granskningar'][k] for k in ('rapporter', 'med_huvud', 'utan_huvud', 'trasiga')} == {'rapporter': 13, 'med_huvud': 6, 'utan_huvud': 4, 'trasiga': 3}, s['granskningar']
    assert s['beslut']['tillagg'] == 11 and s['pagaende']['kunder'] == 4 and s['pagaende']['pilot'] == 3, (s['beslut'], s['pagaende'])
    assert d['senare'] == {'kompetenskedjan': None, 'slutposten': None}, d['senare']
    v = vyn(d)
    for rubrik in ('Väntar på dig', 'Senaste rapporterna', 'Fynd och rättelser', 'Historik och ersatta slutsatser', 'Saknat underlag',
                   'Kompetenskedjan och slutposten'):
        assert '<h2>%s</h2>' % rubrik in v['sammanfattning'], rubrik
    assert 'Datakällorna byggs i andra arbetsgrenar' in v['senare'] and 'Inget är gissat' in v['senare'], v['senare']
    html = (ROOT / 'dashboard' / 'index.html').read_text(encoding='utf-8')
    assert '<a href="#/dokumentation" data-v="dokumentation">' in html and "h.startsWith('dokumentation/')" in html, 'vyn saknas i navigeringen'


@fall('filtren: serverns svar har fälten för uppdrag eller systemdel, typ, version, datum och utfall, och vyns filter använder dem')
def _filtren():
    d = svar()
    r90 = rapport(d, 'GR-20261005-r90')
    falt = {'id', 'titel', 'typ', 'typgrupp', 'uppdrag', 'kund', 'systemdel', 'moment', 'datum', 'granskad_identitet', 'version',
            'rapportstatus', 'rapportstatus_klass', 'bedomningsutfall', 'utfall', 'avsandare', 'forhallande', 'foregaende', 'beslut', 'atgarder', 'fil'}
    assert all(falt <= set(r) for r in d['granskningar']['rapporter']), [sorted(falt - set(r)) for r in d['granskningar']['rapporter']][:2]
    assert (r90['typgrupp'], r90['datum'], r90['version'], r90['utfall'], r90['rapportstatus_klass']) == (
        'systemgranskning', '2026-10-05', 'abc1234', 'underkänt', 'färdig'), r90
    assert 'kontroller/tolk.py' in r90['systemdel'] and r90['atgarder'] == ['GR-20261005-r90#B1: rättas i tolk-20261005', 'GR-20261005-r90#B2 och #B3: backlogposter']
    utfall = vyn(d)['filter']
    alla_ = set(utfall[0])
    assert len(alla_) == 13 and 'underlag/granskningar/sessioner/abc/GRANSKNING-r70.md' in alla_, utfall[0]  # en rapport utan id heter som sin fil
    vantat = [None, {'GR-20261005-r90', 'GR-20261006-r90-om', 'GR-20261006-utkast', 'GR-20261006-utan-falt'},
              {'GR-20261006-r90-om', 'RAPPORT-2026-10-06-pilot'}, {'GR-20261005-r90'}, {'GR-20261006-utkast'}, {'GR-20261006-r90-om'},
              {'GR-20261005-r90'}, {'GR-20261006-r90-om', 'GR-20261006-utkast', 'GR-20261006-utan-falt', 'RAPPORT-2026-10-06-lage', 'RAPPORT-2026-10-06-pilot'},
              {'GR-20261005-r90'}, {'GR-20261005-r90', 'GR-20261006-r90-om'}, {'RAPPORT-2026-10-06-lage'},
              {'underlag/granskningar/sessioner/abc/GRANSKNING-r70.md'}, {'GR-20261005-r90'}, {'RAPPORT-2026-10-06-lage'}]
    for f, ut, vant in zip(FILTER, utfall, vantat):
        if vant is not None:
            assert set(ut) == vant, ('filtret %s' % f, sorted(ut), sorted(vant))


@fall('en rapport utan huvud ger "ej angivet", med raden "registrerad med sha256" och integriteten för sig')
def _utan_huvud():
    d = svar()
    r = rapport(d, 'underlag/granskningar/sessioner/abc/GRANSKNING-r70.md')
    for k in dash.RAPPORTFALT:
        assert r[k] == 'ej angivet', (k, r[k])
    assert (r['huvud'], r['utfall'], r['rapportstatus_klass'], r['avsandare']) == ('saknas', 'ej angivet', 'ej angivet', 'avsändaren ej belagd'), r
    fl = r['forteckning']
    assert fl['registrerad'] == 'registrerad med sha256 %s' % FORTECKNING[0]['sha256'][:12] and fl['slag'] == 'systemgranskning', fl
    assert fl['integritet'] == 'ok' and fl['integritet_text'] == 'filen finns och stämmer med förteckningens sha256', fl
    assert r['typgrupp'] == 'systemgranskning (förteckningens slag)', r['typgrupp']
    borta = rapport(d, 'underlag/granskningar/sessioner/abc/GRANSKNING-r71.md')
    assert borta['forteckning']['integritet'] == 'saknas' and borta['fil']['lank'] is None and borta['titel'] == 'ej angivet', borta
    html = vyn(d)['rapporter']['underlag/granskningar/sessioner/abc/GRANSKNING-r70.md']
    assert 'registrerad med sha256 %s' % FORTECKNING[0]['sha256'][:12] in html and '<dt>Titel</dt><dd>ej angivet</dd>' in html, html[:900]
    assert 'integritet, ingen verifiering av slutsatserna' in html, html[-600:]
    # bevis och rapporter som redan visas med sitt huvud blir inga egna rader
    assert not any((x.get('fil') or {}).get('sokvag', '').endswith('bevis.txt') for x in d['granskningar']['rapporter'])
    assert sum(1 for x in d['granskningar']['rapporter'] if (x.get('fil') or {}).get('sokvag') == 'underlag/granskningar/GR-20261005-r90.md') == 1


@fall('ett trasigt huvud fäller inte vyn och visar inga fält; tolken kastar aldrig')
def _trasigt():
    d = svar()
    for ident in ('underlag/granskningar/GR-20261006-trasig.md', 'underlag/granskningar/GR-20261006-konstig.md', 'underlag/granskningar/GR-20261006-binar.md'):
        r = rapport(d, ident)
        assert r['huvud'] == 'trasigt' and r['id'] == 'ej angivet' and r['titel'] == 'ej angivet' and r['fil']['lank'], (ident, r)
    assert 'HALV-RAPPORT' not in json.dumps(d, ensure_ascii=False), 'ett fält ur ett trasigt huvud visas'
    assert {x['sokvag'] for x in d['saknat']['trasiga_huvuden']} == {'underlag/granskningar/GR-20261006-%s.md' % n for n in ('trasig', 'konstig', 'binar')}
    assert d['granskningar']['forteckning']['trasiga_rader'] == 1, d['granskningar']['forteckning']
    for text, vantat in ((None, 'trasigt'), ('', 'saknas'), ('---', 'trasigt'), ('---\n', 'trasigt'), ('# rubrik\n', 'saknas'),
                         ('---\nid: x\n  - utan nyckel först\n---\n', 'ok'), ('---\n  - utan nyckel\n---\n', 'trasigt'),
                         ('---\nid: "citerad: med kolon"\nlista:\n  - a\n  - b\nidentitet:\n  A: x\n---\n', 'ok'), ('---\n' + 'a: b\n' * 500, 'trasigt')):
        f, lage = dash.rapporthuvud(text)
        assert lage == vantat, (text, lage, f)
    f, _ = dash.rapporthuvud('---\nid: "citerad: med kolon"\nlista:\n  - a\n  - b\nidentitet:\n  A: x\n---\n')
    assert f == {'id': 'citerad: med kolon', 'lista': ['a', 'b'], 'identitet': ['A: x']}, f
    pilot = rapport(d, 'RAPPORT-2026-10-06-pilot')
    assert pilot['granskad_identitet'] == ['A: Figma prov, v5', 'C: version C5, dist i moment-c/VERSION.json'] and pilot['slag'] == 'projektrapport', pilot


@fall('rapportstatus och utfall är två skilda fält, i svaret och i vyn')
def _status_och_utfall():
    d = svar()
    par = {r['id']: (r['rapportstatus_klass'], r['utfall']) for r in d['granskningar']['rapporter'] if r['id'] != 'ej angivet'}
    assert par['GR-20261005-r90'] == ('färdig', 'underkänt') and par['GR-20261006-r90-om'] == ('färdig', 'godkänt'), par
    assert par['GR-20261006-utkast'] == ('utkast', 'ej bedömt') and par['RAPPORT-2026-10-06-lage'] == ('färdig', 'ej bedömt'), par
    assert par['GR-20261006-utan-falt'] == ('ej angivet', 'ej angivet'), par
    g = d['sammanfattning']['granskningar']
    assert g['rapportstatus'] == {'färdig': 4, 'utkast': 1, 'ej angivet': 1}, g['rapportstatus']
    assert g['utfall'] == {'underkänt': 1, 'godkänt': 2, 'ej bedömt': 2, 'ej angivet': 1}, g['utfall']
    html = vyn(d)['rapporter']['GR-20261005-r90']
    assert '<span class="chip">rapport färdig</span>' in html and 'utfall underkänt · gällde abc1234</span>' in html, html[:700]
    assert '<dt>Rapportstatus</dt><dd>färdig</dd>' in html and '<dt>Bedömningsutfall</dt><dd>underkänt för sammanslagning: 1 blockerande' in html, html[:2000]


@fall('en historisk godkänd granskning bär den version den gällde och läses som historik')
def _historik():
    d = svar()
    om = rapport(d, 'GR-20261006-r90-om')
    assert om['utfall'] == 'godkänt' and om['version'] == 'def5678', om
    v = vyn(d)
    for html in [v['rapporter']['GR-20261006-r90-om'], v['sammanfattning'], v['pagaende']]:
        assert 'utfall godkänt · gällde def5678' in html, html[:400]
        assert not re.search(r'utfall godkänt</span>', html), 'ett godkännande utan version'
    assert 'Historik: utfallet gäller den granskade identiteten (gällde def5678)' in v['rapporter']['GR-20261006-r90-om']
    pilot = rapport(d, 'RAPPORT-2026-10-06-pilot')
    assert pilot['version'] is None and 'utfall godkänt · gällde: se granskad identitet' in v['rapporter']['RAPPORT-2026-10-06-pilot']


@fall('BESLUT.md: statusraden, märkningen, ej angivet, ersättaren och vad som ersatts, Återstår och kodblock; också repots egen')
def _beslut():
    t = svar()['beslut']['tillagg']
    assert [x['rubrik'][len('Tillägg '):] for x in t] == ['2026-10-01: första beslutet', '2026-10-02: utan status', '2026-10-02, kväll: tvetydig hänvisning',
                                                         '2026-10-03: andra saken', '2026-10-03: en tredje sak', '2026-10-05, kväll: fjärde beslutet',
                                                         '2026-10-05, kväll: femte beslutet', '2026-10-06: sjätte saken', '2026-10-07: konstig status',
                                                         '2026-10-08: kvällsreferens', '2026-10-03, kväll: kvällens sak'], [x['rubrik'] for x in t]
    assert [x['status'] for x in t] == ['delvis ersatt', 'ej angivet', 'delvis ersatt', 'gäller', 'ersatt', 'gäller', 'delvis ersatt', 'gäller', 'annat',
                                        'delvis ersatt', 'gäller'], [x['status'] for x in t]
    assert t[1]['statusrad'] == 'ej angivet' and t[4]['statusrad'] == 'ersatt av tillägget 2026-10-05, kväll: fjärde beslutet', (t[1]['statusrad'], t[4]['statusrad'])
    ref = lambda x: [(r['mal'], r['oklart']) for e in x['ersatt_av'] for r in e['ref']]  # noqa: E731
    assert ref(t[0]) == [([3], False)] and ref(t[2]) == [([5, 6], True)] and ref(t[4]) == [([5], False)] and ref(t[6]) == [([7], False)], [ref(x) for x in t]
    assert ref(t[9]) == [([10], False)], ref(t[9])  # tillägget efter datumet (kväll) avgör
    assert [x['ersatter'] for x in t] == [[], [], [], [0], [], [4], [], [6], [], [], [9]], [x['ersatter'] for x in t]
    assert t[5]['aterstar'] == ['vyn i dashboarden; två rader', 'ett prov'], t[5]['aterstar']
    assert t[0]['ersatt_av'][0]['text'].startswith('tillägget 2026-10-03 om andra saken'), t[0]['ersatt_av']
    s = svar()['sammanfattning']
    assert s['beslut']['status'] == {'delvis ersatt': 4, 'ej angivet': 1, 'gäller': 4, 'ersatt': 1, 'annat': 1}, s['beslut']
    assert [x['rubrik'] for x in svar()['saknat']['utan_status']] == ['Tillägg 2026-10-02: utan status']
    html = vyn(svar())['beslut']
    assert 'går inte att knyta till ett enda tillägg' in html and 'href="#/dokumentation/beslut/5"' in html, html[:400]
    # repots egen BESLUT.md: tilläggen från 2026-10-06, kväll har statusraden, och varje hänvisning till en ersättare hittar ett tillägg
    dash.ROOT = ROOT
    try:
        egen = dash.beslutslogg()
    finally:
        dash.ROOT = TMP
    tt = egen['tillagg']
    assert len(tt) >= 20 and not egen.get('fel'), (len(tt), egen.get('fel'))
    fran = next(i for i, x in enumerate(tt) if x['rubrik'].startswith('Tillägg 2026-10-06, kväll'))
    assert all(x['status'] != 'ej angivet' for x in tt[fran:]), [(x['rubrik'], x['status']) for x in tt[fran:]]
    tomma = [(x['rubrik'], e['text'][:60]) for x in tt for e in x['ersatt_av'] for r in e['ref'] if not r['mal']]
    assert not tomma and any(x['ersatt_av'] for x in tt), ('hänvisningar som inte hittar något tillägg', tomma)


@fall('blindningen: före ditt första val är svaret detsamma med och utan de dolda fälten, och inget dolt syns')
def _blindningen():
    assert HEMLIGT.findall('{"titel": "HEMLIG-TITEL k01"}'), 'detektorn ser inte en läcka'
    med = svaret()
    tillbaka = utan_dolda('fl-blind')
    try:
        utan = svaret()
    finally:
        tillbaka()
    for x in (med, utan):
        x.pop('tid', None)
    a, b = json.dumps(med, ensure_ascii=False, sort_keys=True), json.dumps(utan, ensure_ascii=False, sort_keys=True)
    assert a == b, 'svaret beror på det som är dolt före ditt första val'
    assert not HEMLIGT.findall(a) and not re.search(r'\d+ brister eller DESIGN\.md-fel', a), HEMLIGT.findall(a)
    k = {x['slug']: x for x in med['pagaende']['kunder']}
    assert k['fl-blind']['blind'] is True and k['fl-blind']['vantar'] == ['Ditt val'], k['fl-blind']
    # en arm i en blind jämförelse: inget om armen, lika för båda
    assert k['ab-x'] == dict(k['ab-y'], slug='ab-x', vy='#/flode/ab-x') and k['ab-x'].get('ab_dold') is True and set(k['ab-x']) == {'slug', 'ab_dold', 'vy'}, k['ab-x']
    assert 'kunder/ab-x/RAPPORT.md' not in a and 'kunder/ab-y' not in a, 'en arm i den blinda jämförelsen syns'
    # det fil_tillaten döljer nämns inte: kalibreringens rapport och förteckningens rad dit
    assert 'kalibrering' not in a and med['granskningar']['forteckning']['dolda'] == 1, med['granskningar']['forteckning']
    v = vyn(med)
    assert not HEMLIGT.findall(json.dumps(v, ensure_ascii=False)), 'vyn lägger till något dolt'


@fall('länkarna: varje fil öppnas genom /fil/ och fil_tillaten, varje dokument genom /api/dokument, och inget går förbi')
def _lankarna():
    d = svar()
    lankar = sorted(set(alla(d, 'lank')))
    assert len(lankar) >= 12, lankar
    for lank in lankar:
        assert lank.startswith('/fil/') and dash.fil_tillaten(lank[5:]), ('en länk förbi fil_tillaten', lank)
        assert hamta(quote(lank))[0] == 200, ('/fil/ öppnar inte länken', lank)
    doks = sorted(set(alla(d, 'dok')))
    assert {'README.md', 'CLAUDE.md', 'BESLUT.md', 'backlog/README.md', 'kunskap/designregler.md', 'kunskap/gammal.md', 'kritik/GRANSKARE.md',
            '.claude/skills/prov-skill/SKILL.md'} <= set(doks), doks
    for dok in doks:
        assert not dok.startswith(('underlag/', 'kunder/')) and hamta('/api/dokument?fil=' + quote(dok))[0] == 200, dok
    assert all(v.startswith('#/') for v in alla(d, 'vy')), [v for v in alla(d, 'vy') if not v.startswith('#/')]
    for fel_ in ('underlag/granskningar/GR-20261005-r90.md', 'kunder/k-bygge/RAPPORT.md', 'kunskap/lankad.md', '../README.md',
                 'kunskap/../BESLUT.md', 'underlag/fl-blind/atelje/kandidater/k01/RIKTNING.md', '/etc/hosts', 'dashboard/server.py', ''):
        kod, data = hamta('/api/dokument?fil=' + quote(fel_))
        assert kod == 404 and b'HEMLIG' not in data, (fel_, kod, data[:200])
    assert hamta('/api/dokument')[0] == 404
    # länkar i texten som servern renderar går inte till filer
    texter = [d['instruktioner']['platsregel_html']] + [x['html'] for x in d['beslut']['tillagg']]
    assert not any(re.search(r'href="(?!https?://)', t) for t in texter), 'en länk i den renderade texten'


@fall('instruktionerna: platsregelns tabell och CLAUDE.md, statusraden, flödeskartan och dokumentrutten')
def _instruktionerna():
    ins = svar()['instruktioner']
    g = {x['slag']: [f['dok'] for f in x['filer']] for x in ins['grupper']}
    assert list(g) == ['Start och överblick', 'Gällande arbetssätt', 'Beslut', 'Förbättringsarbete'], list(g)
    assert g['Start och överblick'] == ['README.md', 'CLAUDE.md'] and g['Beslut'] == ['BESLUT.md'] and g['Förbättringsarbete'] == ['backlog/README.md'], g
    assert g['Gällande arbetssätt'] == ['kunskap/copy-kontroll.md', 'kunskap/designregler.md', 'kunskap/gammal.md', '.claude/skills/prov-skill/SKILL.md',
                                      'kritik/GRANSKARE.md'], g['Gällande arbetssätt']
    f = {x['dok']: x for grupp in ins['grupper'] for x in grupp['filer']}
    assert f['kunskap/gammal.md']['status'] == 'historik, ersatt av kunskap/designregler.md' and f['kunskap/designregler.md']['status'] is None
    assert (f['kunskap/designregler.md']['i_claude'], f['kunskap/copy-kontroll.md']['i_claude'], f['kunskap/gammal.md']['i_claude']) == (True, True, False)
    assert (f['.claude/skills/prov-skill/SKILL.md']['titel'], f['.claude/skills/prov-skill/SKILL.md']['beskrivning']) == ('Provskillen', 'En skill i provet.')
    assert [s_['steg'] for s_ in ins['kedjan']['steg']] == ['1. Underlaget', '2. Prototypen'] and '<table>' in ins['platsregel_html'], ins['kedjan']
    assert 'Annat.' not in ins['platsregel_html'] and 'Allt under' in ins['platsregel_html'], 'avsnittet läses inte till nästa rubrik'
    kod, data = hamta('/api/dokument?fil=' + quote('.claude/skills/prov-skill/SKILL.md'))
    x = json.loads(data)
    assert kod == 200 and '<h2>Provskillen</h2>' in x['html'] and 'name: prov-skill' not in x['html'], x
    assert svar()['sammanfattning']['historik']['instruktioner_med_statusrad'] == 1


@fall('saknade rapporter: granskningar som koden nämner utan registrerad rapport, och inget återskapat')
def _saknade():
    d = svar()
    s = {x['runda']: x for x in d['saknat']['rapporter']}
    assert sorted(s, key=dash._rundnyckel) == ['r55', 'r56b', 'r57'], sorted(s)
    assert s['r55']['var'] == ['kontroller/exempel.py:1'] and s['r57']['antal'] == 1, s
    assert d['sammanfattning']['saknat']['rapporter'] == ['r55', 'r56b', 'r57']
    assert 'Innehållet återskapas inte' in vyn(d)['saknat']


@fall('integriteten är ingen verifiering: förteckningens filer räknas för sig, och verifierat är bara fältet verifierad')
def _integriteten():
    d = svar()
    fl = d['granskningar']['forteckning']
    assert fl['poster'] == 8 and fl['integritet'] == {'ok': 5, 'saknas': 1, 'fel_sha': 1, 'ej_kontrollerade': 1}, fl['integritet']
    assert fl['saknas'] == ['underlag/granskningar/sessioner/abc/GRANSKNING-r71.md'] and fl['fel_sha'] == ['underlag/granskningar/sessioner/abc/GRANSKNING-r72.md']
    assert 'Integritet, ingen verifiering' in fl['not'] and 'inte att historiken är fullständig' in fl['not'], fl['not']
    assert all('verifier' not in x for x in dash.INTEGRITET.values()), dash.INTEGRITET
    # en godkänd omgranskning verifierar ingenting av sig själv: bara posten med fältet verifierad räknas
    assert d['sammanfattning']['fynd'] == {'oppna': 1, 'klara_ej_verifierade': 1, 'verifierade': 1, 'ovriga': 0}, d['sammanfattning']['fynd']
    assert rapport(d, 'GR-20261006-r90-om')['fynd'] == {'oppna': [], 'klara': [], 'verifierade': []}


@fall('fynd och rättelser ur backloggen: öppna med sin åtgärd, klara men inte verifierade, verifierade')
def _fynden():
    d = svar()
    f = {p['id']: p for p in d['granskningar']['fynd']}
    assert set(f) == {B1, B2, B3}, sorted(f)
    assert (f[B1]['grupp'], f[B1]['rapport'], f[B1]['atgard']) == ('oppen', 'GR-20261005-r90', 'Rätta tolken i `kontroller/tolk.py`.'), f[B1]
    assert (f[B2]['grupp'], f[B2]['lage']) == ('klar', 'klar, inte verifierad') and (f[B3]['grupp'], f[B3]['verifierad']) == ('verifierad', 'GR-20261006-r90-om')
    assert rapport(d, 'GR-20261005-r90')['fynd'] == {'oppna': [B1], 'klara': [B2], 'verifierade': [B3]}
    assert d['pagaende']['backlog']['antal'] == {'vilande': 2, 'klar, inte verifierad': 1, 'klar, verifierad': 1}, d['pagaende']['backlog']
    html = vyn(d)['granskningar']
    assert 'Rätta tolken i <code>kontroller/tolk.py</code>.' in html and 'verifierad av GR-20261006-r90-om' in html, html[-1500:]


@fall('avsändaren: fältet avsandare, annars författaren, annars "avsändaren ej belagd"; aldrig gissad ur filnamnet')
def _avsandaren():
    d = svar()
    assert rapport(d, 'GR-20261005-r90')['avsandare'] == 'oberoende granskare i sessionen prov'
    assert rapport(d, 'GR-20261006-r90-om')['avsandare'] == 'en annan granskare (Codex), inklistrad av ägaren'
    assert rapport(d, 'GR-20261006-utan-falt')['avsandare'] == 'avsändaren ej belagd'
    assert rapport(d, 'underlag/granskningar/sessioner/abc/svar-codex-r20.md')['avsandare'] == 'avsändaren ej belagd'
    p = {m['id']: m['domar'] for m in d['pagaende']['pilot']}
    assert [(x['falt'], x['avsandare'], x['beslutstyp']) for x in p['moment-c']] == [
        ('agarens_dom', 'ägaren (bekräftat i provet)', 'ägarens bilddom över C5'), ('granskningar', 'avsändaren ej belagd', None),
        ('granskningar', 'avsändaren ej belagd', None)], p['moment-c']
    assert p['moment-c'][2]['fil'] is None, ('en fil utanför momentet', p['moment-c'][2])
    assert [(x['falt'], x['avsandare']) for x in p['moment-d']] == [('agarens_dom', 'avsändaren ej belagd'), ('bedomningar', 'avsändaren ej belagd')], p['moment-d']
    assert [(x['falt'], x['avsandare']) for x in p['moment-e']] == [('inklistrad_dom', 'avsändaren ej belagd')], p['moment-e']
    assert p['moment-c'][0]['fil']['lank'] == '/fil/underlag/figma-pilot/moment-c/bedomningar/AGARENS-DOM-C5.md', p['moment-c'][0]
    assert 'Avsändare: ägaren (bekräftat i provet) · beslutstyp: ägarens bilddom över C5' in vyn(d)['pagaende']


@fall('uppdragets läge: tillägget, rapporterna som anger det (också genom föregående), den senaste och fynden')
def _uppdraget():
    d = svar()
    u = {x['rubrik']: x for x in d['pagaende']['uppdrag']}
    assert set(u) == {'Tillägg 2026-10-03: andra saken', 'Tillägg 2026-10-05, kväll: fjärde beslutet', 'Tillägg 2026-10-06: sjätte saken'}, sorted(u)
    a = u['Tillägg 2026-10-03: andra saken']
    assert a['rapporter'] == ['GR-20261006-r90-om', 'GR-20261005-r90'] and a['senaste']['id'] == 'GR-20261006-r90-om', a
    assert (a['senaste']['utfall'], a['senaste']['version']) == ('godkänt', 'def5678') and a['fynd'] == {'oppna': [B1], 'klara': 1, 'verifierade': 1}, a
    assert u['Tillägg 2026-10-05, kväll: fjärde beslutet']['aterstar'] == ['vyn i dashboarden; två rader', 'ett prov']
    assert u['Tillägg 2026-10-06: sjätte saken']['rapporter'] == ['GR-20261006-utkast']
    s = [x['id'] for x in d['sammanfattning']['senaste']]
    assert s[:2] == ['RAPPORT-2026-10-06-pilot', 'RAPPORT-2026-10-06-lage'] and 'GR-20261005-r90' in s, s


@fall('pågående: körregistret, kundernas körningar och byggets rapporter, och det som väntar på dig')
def _pagaende():
    d = svar()
    k = d['pagaende']['korningar']
    assert [(x['vad'], x['pid']) for x in k] == [('rokprov', os.getpid())] and set(k[0]) == {'vad', 'slug', 'pid', 'start', 'utcheckning'}, k
    assert (korregister.KATALOG / ('%d.json' % os.getpid())).is_file(), 'vyn rensade körregistret'
    kb = next(x for x in d['pagaende']['kunder'] if x['slug'] == 'k-bygge')
    assert [x['text'] for x in kb['slutrapport']] == ['provets rapport', 'byggets rapport'] and all(x['lank'] for x in kb['slutrapport']), kb
    v = d['sammanfattning']['vantar']
    assert {'text': 'fl-blind: Ditt val väntar på dig', 'vy': '#/flode/fl-blind'} in v, v
    assert any(x['text'].startswith('Beslut enligt lägesrapporten RAPPORT-2026-10-06-lage (2026-10-06): välj mellan A och B') for x in v), v
    lage = d['pagaende']['lagesrapporter']
    assert [x['id'] for x in lage] == ['RAPPORT-2026-10-06-lage'] and lage[0]['uppdrag'] == ['första uppdraget (ägaren 2026-10-01)', 'andra uppdraget']


@fall('vyns delar renderas ur svaret, med de fyra delarna som flikar')
def _renderingen():
    v = vyn(svar())
    assert '<h2>Flödeskartan</h2>' in v['instruktioner'] and '<h2>Var information finns</h2>' in v['instruktioner'], v['instruktioner'][:300]
    assert 'href="#/dokumentation/las/kunskap%2Fdesignregler.md"' in v['instruktioner'] and 'nämnd i CLAUDE.md' in v['instruktioner']
    for rubrik in ('Körningar som pågår nu', 'Ägarens uppdrag', 'Kunder', 'Figma-metodprovet', 'Lägesrapporter', 'Backloggen'):
        assert '<h2>%s</h2>' % rubrik in v['pagaende'], rubrik
    assert 'id="df-typ"' in v['granskningar'] and 'id="df-utfall"' in v['granskningar'] and 'id="df-version"' in v['granskningar'], v['granskningar'][:500]
    html = (ROOT / 'dashboard' / 'index.html').read_text(encoding='utf-8')
    flikar = html[html.find('const DOKFLIKAR'):html.find('const DOK_EJ')]
    for namn in ('Så fungerar Nortropic', 'Pågående uppdrag', 'Granskningar och resultat', 'Beslut och historik'):
        assert namn in flikar, namn


srv.shutdown()
print('dokumentationsvyns prov: %d fel%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
