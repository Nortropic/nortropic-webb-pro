#!/usr/bin/env python3
"""prov_dokumentation.py — dokumentationen och spårbarheten (ägarens uppdrag 2026-10-06 om dokumentations- och
rapportstrukturen; regeln står i README.md, Var information finns):

- platsregeln i README.md har en tabell över de åtta slagen, och de sökvägar i repot som avsnittet nämner finns;
- CLAUDE.md, backlog/README.md och backlog-skillen hänvisar till regeln;
- arbetsregelns första mening står i README.md och i ingen annan instruktionsfil (CLAUDE.md, backlog/README.md,
  kunskap/, .claude/skills/, kritik/); BESLUT.md är beslutsloggen och citerar ägaren, så den undantas;
- varje "## Tillägg 2026-10-06, kväll" och senare i BESLUT.md har en rad "**Status:**";
- backloggen (syntetiska poster i en temporär katalog): källan granskning med kallref och fynd, verifierad bara med
  kommandot verifiera, "klar, inte verifierad" i listan, en ny commit som tar bort en verifiering, låset som
  verktygslådan använder och den atomiska skrivningen;
- startkontrollens informationsrad om dokumentationen: rätt antal poster, saknade filer och fel sha256 i en syntetisk
  förteckning, och platsregeln som finns eller saknas.

    .venv/bin/python kontroller/rokprov/revision/prov_dokumentation.py <repo>

Repots egna filer läses men ändras inte; allt som skrivs hamnar i en temporär katalog, och inga privata data läses.
Varje fall redovisas för sig på stderr; slutkod 1 när något fall föll.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
K = ROOT / 'kontroller'
TMP = Path(tempfile.mkdtemp(prefix='nwp-dokumentation-')).resolve()
if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(shutil.rmtree, TMP, True)
sys.path.insert(0, str(K))

# ägarens åtta slag (uppdraget 2026-10-06, punkt 2), i ordning; README får förtydliga efter namnet
SLAG = ('Start och överblick', 'Gällande arbetssätt', 'Beslut', 'Förbättringsarbete', 'Projekt- och körningsrapporter',
        'Systemgranskningar', 'Bevismaterial', 'Historik och tillfällig')
ARBETSREGELN = ('Varje förändring i Nortropic ska hålla berörd dokumentation och spårbarhet aktuell som en del av samma '
                'uppdrag.')
HANVISNING = 'README.md, Var information finns'
INGANGAR = ('CLAUDE.md', 'backlog/README.md', '.claude/skills/backlog/SKILL.md')
INSTRUKTIONER = ('kunskap', '.claude/skills', 'kritik')  # kataloger; därtill CLAUDE.md och backlog/README.md
REPO_KATALOGER = ('backlog', 'kontroller', 'kunskap', 'kritik', '.claude', 'mall', 'dashboard')
ROTFILER = ('README.md', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', 'kor.sh', 'dashboard.sh', 'requirements.txt',
            'requirements-lock.txt')
MASTE_PROVAS = {'CLAUDE.md', 'BESLUT.md', 'backlog/README.md', 'kritik/'}  # annars kan sökvägsprovet bli grönt utan att pröva
STATUSVARDEN = ('gäller', 'delvis ersatt av', 'ersatt av')
FEL = []


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, e), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def norm(t):
    """Utan citattecken (>), kodtecken och radbrytningar: en mening som brutits över rader eller citerats känns igen."""
    return ' '.join(re.sub(r'(?m)^\s*>\s?', '', t).replace('`', '').split())


def avsnitt(t, rubrik):
    m = re.search(r'(?ms)^%s[ \t]*\n(.*?)(?=^## |\Z)' % re.escape(rubrik), t)
    assert m, 'avsnittet %s saknas' % rubrik
    return m.group(1)


README_AVSNITT = {}


def platsregeln():
    if 'a' not in README_AVSNITT:
        README_AVSNITT['a'] = avsnitt(text('README.md'), '## Var information finns')
    return README_AVSNITT['a']


# ===== platsregeln i README.md =====

@fall('README: avsnittet "## Var information finns" med en tabell över de åtta slagen')
def _tabellen():
    rader = []
    for rad in platsregeln().splitlines():
        if rad.startswith('|'):
            rader.append(rad)
        elif rader:
            break
    assert len(rader) >= 2, 'ingen tabell i avsnittet'
    celler = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rader]
    assert celler[0][0] == 'Slag' and set(''.join(celler[1])) <= set('-: '), celler[:2]
    data = [c[0] for c in celler[2:]]
    assert len(data) == len(SLAG), 'tabellen har %d slag, inte %d: %s' % (len(data), len(SLAG), data)
    for i, (cell, slag) in enumerate(zip(data, SLAG)):
        assert cell.startswith(slag), 'rad %d är "%s", väntade "%s"' % (i + 1, cell, slag)


@fall('README: de sökvägar i repot som avsnittet nämner finns')
def _sokvagarna():
    provade, saknas = set(), []
    for t in re.findall(r'`([^`]+)`', platsregeln()):
        if re.search(r'\s', t) or t.startswith(('/', 'underlag/', 'kunder/')):
            continue  # inga sökvägar, eller privat material utanför git
        topp = t.split('/', 1)[0]
        if not (('/' in t and topp in REPO_KATALOGER) or t in ROTFILER):
            continue  # relativt något annat (prov/, VERSION.json)
        provade.add(t)
        m = re.sub(r'<[^>]*>', '*', t).replace('ÅÅÅÅMMDD', '*').replace('ÅÅÅÅ-MM-DD', '*').replace('…', '*')
        if '*' in m:
            if not any(ROOT.glob(m.rstrip('/'))):
                saknas.append(t)
        elif not ((ROOT / t).is_dir() if t.endswith('/') else (ROOT / t).is_file()):
            saknas.append(t)
    assert MASTE_PROVAS <= provade, 'avsnittet nämner inte %s (prövat: %s)' % (sorted(MASTE_PROVAS - provade), sorted(provade))
    assert not saknas, 'finns inte i repot: %s' % saknas
    assert (ROOT / '.claude' / 'skills' / 'backlog' / 'SKILL.md').is_file(), '.claude/skills/backlog/SKILL.md saknas'


@fall('ingångarna CLAUDE.md, backlog/README.md och backlog-skillen hänvisar till "README.md, Var information finns"')
def _hanvisningarna():
    utan = [f for f in INGANGAR if HANVISNING not in norm(text(f))]
    assert not utan, 'utan hänvisning: %s' % utan


@fall('arbetsregelns första mening står i README.md och i ingen annan instruktionsfil (BESLUT.md undantas)')
def _arbetsregeln():
    assert ARBETSREGELN in norm(platsregeln()), 'arbetsregeln saknas i README.md, Var information finns'
    filer = [ROOT / 'CLAUDE.md', ROOT / 'backlog' / 'README.md'] + sorted(p for d in INSTRUKTIONER for p in (ROOT / d).rglob('*') if p.is_file())
    lasta, traffar = 0, []
    for p in filer:
        try:
            t = p.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue  # typsnitt och bilder
        lasta += 1
        if ARBETSREGELN in norm(t):
            traffar.append(str(p.relative_to(ROOT)))
    assert lasta > 100, 'bara %d instruktionsfiler lästes' % lasta
    assert not traffar, 'arbetsregeln upprepas i %s; hänvisa till README.md, Var information finns' % traffar


@fall('BESLUT.md: varje "## Tillägg 2026-10-06, kväll" och senare har en rad "**Status:**"')
def _statusraderna():
    delar = re.split(r'(?m)^(?=## )', text('BESLUT.md'))
    efter, kraver, utan = False, 0, []
    for d in delar:
        rubrik = d.splitlines()[0] if d.strip() else ''
        m = re.match(r'## Tillägg (\d{4}-\d\d-\d\d)', rubrik)
        if not m:
            continue
        efter = efter or rubrik.startswith('## Tillägg 2026-10-06, kväll')
        if not (efter or m.group(1) > '2026-10-06'):
            continue
        kraver += 1
        status = re.findall(r'(?m)^\*\*Status:\*\*\s*(.+)$', d)
        if not status or not status[0].strip().lower().startswith(STATUSVARDEN):
            utan.append(rubrik)
    assert kraver >= 1, 'inget tillägg från 2026-10-06, kväll eller senare hittades'
    assert not utan, 'utan statusrad (gäller, delvis ersatt av … eller ersatt av …): %s' % utan


# ===== backloggen, med syntetiska poster =====

import backlog as bl  # noqa: E402
import verktygslada as vl  # noqa: E402

BL_ROT = TMP / 'backlog-rot'
bl.ROOT, bl.MAPP = BL_ROT, BL_ROT / 'backlog'
bl.MAPP.mkdir(parents=True)
LASFIL = bl.MAPP / getattr(bl, 'LAS', '.backlog.las')


def cli(*args, markor=None):
    """backlog.py:s kommandorad mot den temporära backloggen, i en egen process."""
    kod = ('import sys; from pathlib import Path; sys.path.insert(0, %r); import backlog as bl; '
           'bl.ROOT, bl.MAPP = Path(%r), Path(%r); %s sys.exit(bl.main(%r))') % (
        str(K), str(bl.ROOT), str(bl.MAPP), ('Path(%r).write_text("x");' % str(markor)) if markor else '', list(args))
    return [sys.executable, '-B', '-c', kod]


def kommando(*args):
    r = subprocess.run(cli(*args), capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def meta(pid):
    return bl.las(bl.MAPP / (pid + '.md'))


@fall('backloggen: källan granskning godtas med kallref och fynd <rapportens id>#<fyndets id>')
def _granskning():
    rc, ut = kommando('ny', '--kalla', 'granskning', '--titel', 'Ett fynd ur granskningen', '--varfor', 'Syntetiskt.',
                      '--kallref', 'GR-20261007-prov', '--fynd', 'GR-20261007-prov#B1')
    assert rc == 0, ut
    m = meta(ut.strip())
    assert (m['kalla'], m['kallref'], m.get('fynd')) == ('granskning', 'GR-20261007-prov', 'GR-20261007-prov#B1'), m
    assert 'verifierad' not in m and m['status'] == 'vilande', m
    for fel_, args in (('utan fynd', ('--kallref', 'GR-20261007-prov')), ('utan kallref', ('--fynd', 'GR-20261007-prov#B2')),
                       ('fynd utan #', ('--kallref', 'GR-20261007-prov', '--fynd', 'GR-20261007-prov-B3'))):
        rc, ut = kommando('ny', '--kalla', 'granskning', '--titel', 'Ett till', '--varfor', 'x', *args)
        assert rc == 2, '%s gick igenom: %s' % (fel_, ut)


@fall('backloggen: verifierad sätts bara med kommandot verifiera, och listan visar "klar, inte verifierad"')
def _verifierad():
    pid = bl.ny('kirurg', 'En post som blir klar', 'Syntetiskt.', kallref='prov')
    rc, ut = kommando('verifiera', pid, '--rapport', 'GR-20261008-prov')
    assert rc == 2 and 'verifierad' not in meta(pid), 'en vilande post verifierades: %s' % ut
    rc, ut = kommando('status', pid, 'klar', '--commit', 'abc1234', '--not', 'gjort')
    assert rc == 0 and 'verifierad' not in meta(pid), 'status klar satte verifierad: %s' % meta(pid)
    rc, ut = kommando('lista', '--status', 'klar')
    rad = next((r for r in ut.splitlines() if pid in r), '')
    assert rc == 0 and rad.startswith('klar, inte verifierad'), ut
    rc, ut = kommando('verifiera', pid, '--rapport', 'GR-20261008-prov', '--not', 'omprövad')
    assert rc == 0 and meta(pid).get('verifierad') == 'GR-20261008-prov', (ut, meta(pid))
    rc, ut = kommando('lista', '--json')
    x = next(p for p in json.loads(ut) if p['id'] == pid)
    assert x['verifierad'] == 'GR-20261008-prov' and x['lage'] == 'klar, verifierad av GR-20261008-prov', x
    # en ny commit är inte verifierad: fältet tas bort ur huvudet, och noten säger vad som verifierades
    rc, ut = kommando('status', pid, 'klar', '--commit', 'def5678')
    m = meta(pid)
    assert rc == 0 and 'verifierad' not in m and 'GR-20261008-prov verifierade status klar med commit abc1234' in m['kropp'], m
    rc, ut = kommando('lista')
    assert next(r for r in ut.splitlines() if pid in r).startswith('klar, inte verifierad'), ut


@fall('backloggen: varje skrivning sker under fillåset (vl.las), också en ny post')
def _laset():
    pid = bl.ny('kirurg', 'En post att ändra under låset', 'Syntetiskt.', kallref='prov')
    for vad, args in (('status', ('status', pid, 'pagar')),
                      ('ny', ('ny', '--kalla', 'kirurg', '--titel', 'En post att ändra under låset', '--varfor', 'x'))):
        markor = TMP / ('markor-' + vad)
        fore = (meta(pid)['status'], sorted(p.name for p in bl.MAPP.glob('B-*.md')))
        with vl.las(LASFIL):
            p = subprocess.Popen(cli(*args, markor=markor), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            slut = time.time() + 60
            while not markor.exists() and time.time() < slut and p.poll() is None:
                time.sleep(0.05)
            time.sleep(1.0)  # processen har nått skrivningen: utan lås är den klar nu
            vantar = p.poll() is None
            orord = (meta(pid)['status'], sorted(x.name for x in bl.MAPP.glob('B-*.md'))) == fore
        ut, fel_ = p.communicate(timeout=60)
        assert markor.exists() and vantar and orord, '%s skrev medan låset hölls (väntade %s, orört %s): %s' % (vad, vantar, orord, ut + fel_)
        assert p.returncode == 0, ut + fel_
    assert meta(pid)['status'] == 'pagar' and len(list(bl.MAPP.glob('B-*-en-post-att-andra-under-laset*.md'))) == 2
    if (ROOT / '.git').exists():  # låset och tempfilerna hamnar aldrig i git (gruppera.py lägger till hela backlog/)
        for f in ('backlog/.backlog.las', 'backlog/.B-x.md.123.tmp'):
            r = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', f], capture_output=True)
            assert r.returncode == 0, '%s ignoreras inte av git' % f


@fall('backloggen: en skrivning som avbryts mitt i lämnar posten hel och ingen tempfil kvar')
def _atomiskt():
    pid = bl.ny('kirurg', 'En post som ska överleva', 'Syntetiskt.', kallref='prov')
    p = bl.MAPP / (pid + '.md')
    fore = p.read_bytes()
    original = Path.write_text

    def halv(self, data, *a, **k):
        original(self, data[:len(data) // 2], *a, **k)
        raise OSError(28, 'disken full (provets)')
    Path.write_text = halv
    try:
        try:
            bl.satt_status(pid, 'pagar', not_='en lång not ' * 20)
            raise AssertionError('skrivningen föll inte')
        except OSError:
            pass
    finally:
        Path.write_text = original
    assert p.read_bytes() == fore, 'posten skrevs halvt'
    kvar = [x.name for x in bl.MAPP.iterdir() if x.name.endswith('.tmp')]
    assert not kvar, 'tempfiler kvar: %s' % kvar


# ===== startkontrollens informationsrad om dokumentationen =====

@fall('startkontrollen: förteckningen ger rätt antal poster, saknade filer och fel sha256')
def _forteckningen():
    import startkontroll as sk
    rot = TMP / 'fixtur'
    g = rot / 'underlag' / 'granskningar'
    (g / 'sessioner').mkdir(parents=True)
    (rot / 'README.md').write_text('# x\n\n## Var information finns\n\nTabellen.\n')
    filer = {'sessioner/GR-a.md': b'a\n', 'sessioner/GR-b.md': b'b\n', 'sessioner/GR-c.md': b'c, ny\n', 'sessioner/GR-d.md': b'd, ny\n'}
    for n, b in filer.items():
        (g / n).write_bytes(b)
    poster = [{'fil': 'granskningar/sessioner/GR-a.md', 'sha256': vl.sha(b'a\n')},
              {'fil': 'granskningar/sessioner/GR-b.md', 'sha256': vl.sha(b'b\n').upper()},
              {'fil': 'granskningar/sessioner/GR-c.md', 'sha256': vl.sha(b'c\n')},  # ändrad efter kopieringen
              {'fil': 'granskningar/sessioner/GR-d.md', 'sha256': vl.sha(b'd\n')},  # ändrad efter kopieringen
              {'fil': 'granskningar/sessioner/GR-borta.md', 'sha256': vl.sha(b'e\n')},  # saknas
              {'fil': '../README.md', 'sha256': vl.sha(b'x')}]  # utanför underlag/: kontrolleras inte
    (g / 'FORTECKNING.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in poster) + '\n{trasig rad\n')
    d = sk.dokumentationen(rot)
    assert d == {'platsregel': True, 'forteckning': {'poster': 7, 'saknas': 1, 'fel_sha': 2, 'ej_kontrollerade': 2}}, d
    t = sk.dokumentation_text(d)
    assert 'platsregeln finns' in t and '7 poster, 1 filer saknas, 2 med fel sha256; 2 poster kunde inte kontrolleras' in t, t
    (g / 'FORTECKNING.jsonl').unlink()
    (rot / 'README.md').write_text('# x\n\n## Något annat\n')
    d = sk.dokumentationen(rot)
    assert d == {'platsregel': False, 'forteckning': None}, d
    assert 'platsregeln saknas' in sk.dokumentation_text(d) and 'ingen privat förteckning' in sk.dokumentation_text(d)


print('dokumentationens prov: %d fel%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
