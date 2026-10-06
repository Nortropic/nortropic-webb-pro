#!/usr/bin/env python3
"""prov_flode.py — dashboardens flödesvy (ägarens tillägg 2026-10-06, punkt 4), syntetiskt:

- det tänkta flödet läses ur README:s tabell "Kedjan från kundunderlag till leverans"; en rad utan fyra celler gör
  tabellen oläslig i stället för att tappas;
- före ägarens första val i en körning visas bara neutral framdrift: varken planens titlar eller bristerna syns, och
  steget "Ditt val" väntar på ägaren; efter valet syns beslutet med etikett och version, och bristerna;
- en fil som finns är inte ett kontrollerat steg: ett grönt prov som stoppvakten släppt är kontrollerat, ett prov för en
  sajt som tagits bort är inaktuellt och ett rött prov är underkänt; leveransen visas aldrig som kontrollerad;
- Figma-pilotens poster visar bara kända statusar.

    .venv/bin/python kontroller/rokprov/revision/prov_flode.py <repo>

Allt skrivs i en temporär katalog; det riktiga underlaget rörs inte.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
TMP = Path(tempfile.mkdtemp(prefix='nwp-flode-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
sys.path.insert(0, str(ROOT / 'kontroller'))
sys.path.insert(0, str(ROOT / 'dashboard'))
import atelje  # noqa: E402
import kandidater  # noqa: E402
import server as dash  # noqa: E402
import skapande  # noqa: E402

U, K = TMP / 'underlag', TMP / 'kunder'
dash.ROOT, dash.UNDERLAG, dash.KUNDER = TMP, U, K
atelje.UNDERLAG, atelje.KUNDER = U, K
fel = []


def kontroll(villkor, text):
    if not villkor:
        fel.append(text)


# det tänkta flödet ur README
tabell = ('# Repot\n\n## Kedjan från kundunderlag till leverans\n\nText.\n\n| Steg | Vem startar | Resultat | Saknas i dag |\n'
          '|---|---|---|---|\n| 1. Underlaget | en session: `ny_sajt.py <slug>` | underlag | ett eget kommando |\n'
          '| 2. Prototypen | ägaren: `prototyp.py <slug>` | förslagen | – |\n\n## Nästa avsnitt\n\n| a | b |\n|---|---|\n')
(TMP / 'README.md').write_text(tabell)
k = dash.kedjan()
kontroll(not k.get('fel') and [r['steg'] for r in k['steg']] == ['1. Underlaget', '2. Prototypen'], ('kedjan', k))
kontroll('<code>ny_sajt.py &lt;slug&gt;</code>' in k['steg'][0]['vem'] and k['steg'][1]['saknas'] == '', ('kodspann och tom cell', k['steg']))
(TMP / 'README.md').write_text(tabell.replace('| 2. Prototypen | ägaren', '| 2. Prototypen | ägaren | extra'))
kontroll('fel' in dash.kedjan(), 'en rad med fem celler tappades tyst')
(TMP / 'README.md').write_text('# Repot\n')
kontroll('fel' in dash.kedjan(), 'README utan kedjan')

# en körning före ägarens första val: neutral framdrift
s = 'fl-kund'
a = U / s / 'atelje'
(a / 'kandidater' / 'k01').mkdir(parents=True); (a / 'kandidater' / 'k02').mkdir()
(U / s / 'BRIEF.md').write_text('# brief'); (U / s / 'RESEARCH.md').write_text('# research'); (U / s / 'TEXTUNDERLAG.md').write_text('# text')
(a / 'STATUS.json').write_text(json.dumps({'steg': 'klar_for_bedomning', 'startad': '2026-10-06T10:00:00Z', 'lage': 'ny', 'kandidatflode': True}))
(a / 'KANDIDATPLAN.json').write_text(json.dumps({'tid': '2026-10-06T10:05:00Z', 'kandidater': {'k01': {'titel': 'Hemlig titel ett'}, 'k02': {'titel': 'Hemlig titel två'}}}))
(a / 'kandidater' / 'k01' / 'STATUS.json').write_text(json.dumps({'status': 'klar', 'version': 'abcdef1234567890', 'titel': 'Hemlig titel ett', 'brister': ['en brist']}))
(a / 'kandidater' / 'k02' / 'STATUS.json').write_text(json.dumps({'status': 'under_arbete', 'titel': 'Hemlig titel två'}))
kontroll(dash.flode_slugar() == [s], dash.flode_slugar())
f = dash.flode(s)
text = json.dumps(f, ensure_ascii=False)
kontroll(f['blind'] and 'Hemlig titel' not in text and 'brist' not in text.replace('brister', ''), ('blindningen före första valet', text[:400]))
st = {x['nr']: x for x in f['steg']}
kontroll([x['nr'] for x in f['steg']] == list(range(1, 10)), 'nio steg')
kontroll(st[1]['status'] == 'skapat' and st[2]['status'] == 'skapat' and st[3]['status'] == 'väntar på ägaren', [(x['nr'], x['status']) for x in f['steg']])
kontroll(any('1 av 2 förslag' in x['text'] for x in st[2]['kontroller']), st[2]['kontroller'])
# efter ägarens val: beslutet med etikett och version, och bristerna
etikett = kandidater.etiketter(s, ['k01', 'k02'])['k01']
skapande.lagg_till_dom(s, 'ägaren', 'valj', 'Jag väljer den.', underlag=U, kandidater=[{'id': 'k01', 'version': 'abcdef1234567890', 'plan': '2026-10-06T10:05:00Z'}])
f = dash.flode(s)
st = {x['nr']: x for x in f['steg']}
kontroll(not f['blind'] and st[3]['status'] == 'beslutat' and etikett in st[3]['beslut'][-1]['text'] and 'abcdef123456' in st[3]['beslut'][-1]['text'], st[3])
kontroll(any('brister' in x for x in st[2]['brister']), ('bristerna efter valet', st[2]['brister']))
kontroll('förfiningen' in st[3]['nasta'].lower() or 'valda' in st[3]['nasta'], st[3]['nasta'])

# helbygget: grönt och släppt är kontrollerat, borttagen sajt inaktuellt, rött underkänt; leveransen aldrig kontrollerad
(K / s / 'prov').mkdir(parents=True); (K / s / 'sajt').mkdir()
(K / s / 'sajt' / 'package.json').write_text('{}')
(K / s / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': True, 'tid': '2026-10-06T12:00:00Z', 'dist_sha256': 'ab' * 32, 'grindar': {'a': {'ok': True}, 'b': {'ok': True}}}))
(K / s / 'prov' / 'STOPPVAKT.json').write_text(json.dumps({'slapp': True}))
st = {x['nr']: x for x in dash.flode(s)['steg']}
kontroll(st[6]['status'] == 'kontrollerat' and st[7]['status'] == 'väntar på ägaren', (st[6]['status'], st[7]['status']))
kontroll(any('godkännande' in b for b in st[6]['brister']), 'provet utan godkännande ska säga det')
(K / s / 'sajt' / 'package.json').unlink()
kontroll({x['nr']: x for x in dash.flode(s)['steg']}[6]['status'] == 'inaktuellt', 'ett prov för en borttagen sajt')
(K / s / 'sajt' / 'package.json').write_text('{}')
(K / s / 'prov' / 'STATUS.json').write_text(json.dumps({'ok': False, 'grindar': {'a': {'ok': False}}}))
kontroll({x['nr']: x for x in dash.flode(s)['steg']}[6]['status'] == 'underkänt', 'ett rött prov')
(K / s / 'kundrepo').mkdir(); (K / s / 'kundrepo' / 'package.json').write_text('{}')
st = {x['nr']: x for x in dash.flode(s)['steg']}
kontroll(st[8]['status'] == 'skapat' and st[9]['status'] != 'kontrollerat' and st[9]['brister'], (st[8]['status'], st[9]))

# Figma-pilotens poster: bara kända statusar
(U / 'figma-pilot' / 'moment-x').mkdir(parents=True)
(U / 'figma-pilot' / 'moment-x' / 'VERSION.json').write_text(json.dumps({'moment': 'X', 'status': 'påhittad'}))
(U / 'figma-pilot' / 'moment-y').mkdir()
(U / 'figma-pilot' / 'moment-y' / 'VERSION.json').write_text(json.dumps({'moment': 'Y', 'status': 'kontrollerat', 'figma': {'fil': 'f', 'noder': {'a': '1:2'}}}))
p = {m['id']: m for m in dash.figma_pilot()}
kontroll(p['moment-x']['status'] == 'inte observerat' and p['moment-y']['status'] == 'kontrollerat' and p['moment-y']['figma']['fil'] == 'f', p)
kontroll('figma-pilot' not in dash.flode_slugar(), 'pilotens katalog är ingen kund')

if fel:
    for x in fel:
        print('FEL:', x, file=sys.stderr)
    sys.exit(1)
print('flödesvyn ok: kedjan ur README, blindningen före första valet, statusarna och pilotens poster', file=sys.stderr)
