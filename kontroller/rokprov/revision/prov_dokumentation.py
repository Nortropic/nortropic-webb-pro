#!/usr/bin/env python3
"""prov_dokumentation.py — dokumentationen och spårbarheten (ägarens uppdrag 2026-10-06 om dokumentations- och
rapportstrukturen; regeln står i README.md, Var information finns; granskningen GR-20261007-r97):

- platsregeln i README.md har en tabell över de åtta slagen, och de sökvägar i repot som avsnittet nämner finns och har
  en känd toppkatalog;
- CLAUDE.md, backlog/README.md och skillen backlog hänvisar till regeln, och bygg-sajt (steg 7), kirurg (Utdata) och
  kunskap/skapandeflodet.md (Körspåret) gör det i avsnittet där de skriver rapporter och poster;
- arbetsregelns tre meningar står en gång i README.md, i avsnittet, och i ingen annan instruktionsfil (CLAUDE.md,
  backlog/README.md, kunskap/, .claude/skills/, kritik/); BESLUT.md är beslutsloggen och citerar ägaren, så den undantas;
- varje "## Tillägg 2026-10-06, kväll" och senare i BESLUT.md har raden "**Status:**" direkt under rubriken;
- backloggen (syntetiska poster i en temporär katalog): källan granskning med kallref och fynd, ett fynd får en post,
  en senare rapport som anmäler fyndet igen öppnar en klar post utan verifiering (inte en avvisad eller ersatt, och
  inte rapporten som hittade fyndet), och bara en rapport som är senare än varje rapport som posten nämner, en gång
  (idempotent; inte den som verifierade, inte en äldre, inte en post som pågår), huvudvärden utan radbrytningar och kontrolltecken och --commit som hex, verifierad bara med kommandot verifiera och från
  en annan rapport än fyndets, verifierad_tid utan att andrad ändras, "klar, inte verifierad" i listan, verifieringen
  borta när status eller commit ändras och kvar annars, låset som verktygslådan använder (också för läsningen före en
  ändring) och den atomiska skrivningen;
- startkontrollen: repots identitet (hel commit, gren eller fristående HEAD, ocommittade filer, indexet orört) och
  informationsraden om dokumentationen (rätt antal poster, saknade filer och fel sha256, ingen förteckningsrad som
  kastar, rubriken bara utanför kodblock);
- dashboarden: backloggvyn, renderad i node ur index.html, visar om en klar post är verifierad, och fyndet.

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
import korregister  # noqa: E402
korregister.registrera_tmp(TMP, 'prov_dokumentation')  # provets egen katalog, registrerad som körningens (städregeln, 2026-10-07)

# ägarens åtta slag (uppdraget 2026-10-06, punkt 2), i ordning; README får förtydliga efter namnet
SLAG = ('Start och överblick', 'Gällande arbetssätt', 'Beslut', 'Förbättringsarbete', 'Projekt- och körningsrapporter',
        'Systemgranskningar', 'Bevismaterial', 'Historik och tillfällig')
ARBETSREGELN = ('Varje förändring i Nortropic ska hålla berörd dokumentation och spårbarhet aktuell som en del av samma uppdrag.',
                'Ägaren ska inte behöva påminna om dokumentationen.',
                'Ett arbete redovisas inte som färdigt förrän berörda instruktioner, rapportkopplingar och statusuppgifter är '
                'uppdaterade, eller en konkret kvarstående begränsning har redovisats.')
HANVISNING = 'README.md, Var information finns'
# ingångarna, och för arbetsflödena det avsnitt där de skriver rapporter, bevis och poster (granskningen av r97, BÖR 6)
INGANGAR = (('CLAUDE.md', None), ('backlog/README.md', None), ('.claude/skills/backlog/SKILL.md', None),
            ('.claude/skills/bygg-sajt/SKILL.md', '## Steg 7'), ('.claude/skills/kirurg/SKILL.md', '## Utdata'),
            ('kunskap/skapandeflodet.md', '## Körspåret'))
INSTRUKTIONER = ('kunskap', '.claude/skills', 'kritik')  # kataloger; därtill CLAUDE.md och backlog/README.md
REPO_KATALOGER = ('backlog', 'kontroller', 'kunskap', 'kritik', '.claude', 'mall', 'dashboard')
ROTFILER = ('README.md', 'CLAUDE.md', 'BESLUT.md', 'LARDOMAR.md', 'kor.sh', 'dashboard.sh', 'requirements.txt',
            'requirements-lock.txt')
RELATIVA = ('prov/', 'bilder/', 'matning/', 'VERSION.json', 'FORTECKNING.jsonl', 'KVITTO.json')  # i ett uppdrags, byggs eller omtags katalog
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
    """Texten under den första rubriken som börjar med rubrik, till nästa rubrik på samma nivå (## )."""
    m = re.search(r'(?ms)^%s[^\n]*\n(.*?)(?=^## |\Z)' % re.escape(rubrik), t)
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


@fall('README: de sökvägar i repot som avsnittet nämner finns, och ingen har en okänd toppkatalog')
def _sokvagarna():
    provade, saknas, okanda = set(), [], []
    for t in re.findall(r'`([^`]+)`', platsregeln()):
        if re.search(r'\s', t) or t.startswith(('/', 'underlag/', 'kunder/')) or t in RELATIVA:
            continue  # inga sökvägar, privat material utanför git, eller relativt ett uppdrags katalog
        if '/' not in t and not re.search(r'\.(md|py|sh|json|jsonl|mjs|js|txt)$', t):
            continue  # fältnamn och värden i rapporthuvudet
        if ('/' in t and t.split('/', 1)[0] not in REPO_KATALOGER) or ('/' not in t and t not in ROTFILER):
            okanda.append(t)  # en felstavad toppkatalog eller rotfil prövas annars inte alls (granskningen av r97, D16)
            continue
        provade.add(t)
        m = re.sub(r'<[^>]*>', '*', t).replace('ÅÅÅÅMMDD', '*').replace('ÅÅÅÅ-MM-DD', '*').replace('…', '*')
        if '*' in m:
            if not any(ROOT.glob(m.rstrip('/'))):
                saknas.append(t)
        elif not ((ROOT / t).is_dir() if t.endswith('/') else (ROOT / t).is_file()):
            saknas.append(t)
    assert not okanda, 'sökvägar med okänd toppkatalog eller rotfil: %s' % okanda
    assert MASTE_PROVAS <= provade, 'avsnittet nämner inte %s (prövat: %s)' % (sorted(MASTE_PROVAS - provade), sorted(provade))
    assert not saknas, 'finns inte i repot: %s' % saknas
    assert (ROOT / '.claude' / 'skills' / 'backlog' / 'SKILL.md').is_file(), '.claude/skills/backlog/SKILL.md saknas'


@fall('ingångarna och arbetsflödena hänvisar till "README.md, Var information finns"')
def _hanvisningarna():
    utan = [(f, rubrik) for f, rubrik in INGANGAR if HANVISNING not in norm(avsnitt(text(f), rubrik) if rubrik else text(f))]
    assert not utan, 'utan hänvisning: %s' % utan


@fall('arbetsregelns tre meningar står en gång i README.md, i avsnittet, och i ingen annan instruktionsfil (BESLUT.md undantas)')
def _arbetsregeln():
    hela, sek = norm(text('README.md')), norm(platsregeln())
    for s in ARBETSREGELN:
        assert s in sek, 'saknas i README.md, Var information finns: %s' % s[:60]
        assert hela.count(s) == 1, 'står %d gånger i README.md: %s' % (hela.count(s), s[:60])
    filer = [ROOT / 'CLAUDE.md', ROOT / 'backlog' / 'README.md'] + sorted(p for d in INSTRUKTIONER for p in (ROOT / d).rglob('*') if p.is_file())
    lasta, traffar = 0, []
    for p in filer:
        try:
            t = norm(p.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            continue  # typsnitt och bilder
        lasta += 1
        traffar += ['%s (mening %d)' % (p.relative_to(ROOT), i + 1) for i, s in enumerate(ARBETSREGELN) if s in t]
    assert lasta > 100, 'bara %d instruktionsfiler lästes' % lasta
    assert not traffar, 'arbetsregeln upprepas i %s; hänvisa till README.md, Var information finns' % traffar


@fall('BESLUT.md: varje "## Tillägg 2026-10-06, kväll" och senare har raden "**Status:**" direkt under rubriken')
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
        forsta = next((r for r in d.splitlines()[1:] if r.strip()), '')
        status = re.match(r'\*\*Status:\*\*\s*(.+)$', forsta)
        if not status or not status.group(1).strip().lower().startswith(STATUSVARDEN):
            utan.append(rubrik)
    assert kraver >= 1, 'inget tillägg från 2026-10-06, kväll eller senare hittades'
    assert not utan, 'utan statusrad (gäller, delvis ersatt av … eller ersatt av …) direkt under rubriken: %s' % utan


# ===== backloggen, med syntetiska poster =====

import backlog as bl  # noqa: E402
import verktygslada as vl  # noqa: E402

BL_ROT = TMP / 'backlog-rot'
bl.ROOT, bl.MAPP = BL_ROT, BL_ROT / 'backlog'
bl.MAPP.mkdir(parents=True)
LASFIL = bl.MAPP / getattr(bl, 'LAS', '.backlog.las')


def cli(*args, markor=None, start=None):
    """backlog.py:s kommandorad mot den temporära backloggen, i en egen process. markor: filen skrivs precis före anropet;
    start: processen väntar tills filen finns, så att flera processer anropar samtidigt."""
    kod = ['import sys, time', 'from pathlib import Path', 'sys.path.insert(0, %r)' % str(K), 'import backlog as bl',
           'bl.ROOT, bl.MAPP = Path(%r), Path(%r)' % (str(bl.ROOT), str(bl.MAPP))]
    if start:
        kod.append('while not Path(%r).exists(): time.sleep(0.005)' % str(start))
    if markor:
        kod.append('Path(%r).write_text("x")' % str(markor))
    kod.append('sys.exit(bl.main(%r))' % list(args))
    return [sys.executable, '-B', '-c', '\n'.join(kod)]


def kommando(*args):
    r = subprocess.run(cli(*args), capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout + r.stderr


def meta(pid):
    return bl.las(bl.MAPP / (pid + '.md'))


def poster():
    return sorted(p.name for p in bl.MAPP.glob('B-*.md'))


def samtidigt(argument, markorer=None, start=None):
    """Startar en process per argumentlista och väntar ut dem: [(slutkod, stdout, stderr)]."""
    ps = [subprocess.Popen(cli(*a, markor=(markorer[i] if markorer else None), start=start), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True) for i, a in enumerate(argument)]
    return ps


@fall('kunskapen: Googles linje för generativ AI-sök i seo.md, sokkonsol.md, lansering.md och byggstandarden 7.6; llms.txt bara som avfärdat; sökkonsolens API-villkor')
def _ai_sok_i_kunskapen():
    seo = (ROOT / 'kunskap' / 'seo.md').read_text(encoding='utf-8')
    assert '## Generativ AI i Google Sök' in seo and 'developers.google.com/search/docs/appearance/ai-features' in seo and '2026-07-10' in seo, 'seo.md saknar stycket med källa och datum'
    sok = (ROOT / 'kunskap' / 'sokkonsol.md').read_text(encoding='utf-8')
    assert 'generativa AI-funktioner' in sok and 'Rapporten för generativ AI' in sok, 'sokkonsol.md saknar inkluderingen och rapporten'
    assert 'webmasters.readonly' in sok and 'servicekonto' in sok and 'mcp-gsc' in sok, 'sokkonsol.md saknar API-verktygets villkor'
    dag = (ROOT / 'kunskap' / 'lansering.md').read_text(encoding='utf-8').split('## Lanseringsdagen', 1)[1].split('\n## ', 1)[0]
    assert 'företagsprofil' in dag and '7.4' in dag, 'lansering.md: företagsprofilen uppdateras på lanseringsdagen'
    rad76 = next(r for r in (ROOT / 'kunskap' / 'byggstandard.md').read_text(encoding='utf-8').splitlines() if r.startswith('| 7.6'))
    assert 'seo.md' in rad76 and '2026-07-10' in rad76, rad76
    for p in sorted((ROOT / 'kunskap').glob('*.md')):
        if not p.name.startswith('REGISTER'):
            for r in p.read_text(encoding='utf-8').splitlines():
                assert 'llms.txt' not in r or 'behövs inte' in r, (p.name, r[:120])


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


@fall('backloggen: ett fynd får en post, också när flera sessioner skapar den samtidigt')
def _ett_fynd():
    args = ('ny', '--kalla', 'granskning', '--varfor', 'Syntetiskt.', '--kallref', 'GR-20261007-prov', '--fynd', 'GR-20261007-prov#B4')
    r1 = subprocess.run(cli(*args, '--titel', 'Fyndet första gången'), capture_output=True, text=True, timeout=120)
    fore = poster()
    r2 = subprocess.run(cli(*args, '--titel', 'Samma fynd en gång till'), capture_output=True, text=True, timeout=120)
    assert r1.returncode == 0 and r2.returncode == 0 and r1.stdout.strip() and r2.stdout.strip() == r1.stdout.strip(), (r1, r2)
    assert poster() == fore and 'finns redan' in r2.stderr, ('en ny post för samma fynd', r2.stderr)
    bl.satt_status(r1.stdout.strip(), 'avvisad', not_='avvisad i provet')  # en avvisad post bär också fyndet: ingen ny
    rc, ut = kommando(*args, '--titel', 'Fyndet efter avvisningen')
    assert rc == 0 and ut.split()[0] == r1.stdout.strip() and poster() == fore, ut
    start = TMP / 'start-fynd'
    ps = samtidigt([args[:-1] + ('GR-20261007-prov#B6', '--titel', 'Samtidigt %d' % i) for i in range(6)], start=start)
    time.sleep(1.5)
    start.write_text('x')
    ut = [p.communicate(timeout=120) for p in ps]
    idn = {o.strip() for o, _e in ut}
    med = [f for f in poster() if meta(f[:-3]).get('fynd') == 'GR-20261007-prov#B6']
    assert all(p.returncode == 0 for p in ps) and len(idn) == 1 and len(med) == 1, (sorted(idn), med, [e[-200:] for _o, e in ut])


@fall('backloggen: en senare rapport som anmäler ett fynd igen öppnar dess klara post, utan verifiering; en avvisad öppnas inte')
def _aterkommet_fynd():
    # granskningen av r97-om, BÖR-1: efter verifiera gav ny --fynd samma id, och posten stod kvar som klar och verifierad
    def anmal(kallref, fynd, titel='Ett fynd som kommer tillbaka'):
        rc, ut = kommando('ny', '--kalla', 'granskning', '--titel', titel, '--varfor', 'Syntetiskt.', '--kallref', kallref, '--fynd', fynd)
        assert rc == 0, ut
        return ut.split()[0], ut
    pid, _ = anmal('granskningar/GR-20261007-prov.md', 'GR-20261007-prov#B8')
    bl.satt_status(pid, 'klar', commit='abc1234')
    bl.verifiera(pid, 'GR-20261008-prov')
    fore = poster()
    # samma rapport som hittade fyndet registrerar det en gång till: ingenting ändras
    assert anmal('granskningar/GR-20261007-prov.md', 'GR-20261007-prov#B8')[0] == pid and poster() == fore
    m = meta(pid)
    assert m['status'] == 'klar' and m.get('verifierad') == 'GR-20261008-prov', ('samma rapport öppnade posten', m)
    # en senare rapport säger att fyndet består: posten blir vilande med en not om rapporten, och verifieringen tas bort
    andra, ut = anmal('granskningar/GR-20261009-prov.md', 'GR-20261007-prov#B8', titel='Fyndet består')
    m = meta(pid)
    assert andra == pid and poster() == fore, ('en ny post för samma fynd', andra, ut)
    assert m['status'] == 'vilande' and 'verifierad' not in m and 'verifierad_tid' not in m, ('posten står kvar som klar', m)
    assert 'GR-20261009-prov anmälde fyndet GR-20261007-prov#B8 igen (granskningar/GR-20261009-prov.md)' in m['kropp'] and 'består' in m['kropp'], m['kropp']
    assert 'GR-20261008-prov verifierade status klar med commit abc1234' in m['kropp'], m['kropp']
    rc, ut = kommando('lista')
    assert next(r for r in ut.splitlines() if pid in r).startswith('vilande '), ut
    # också en klar post som inte verifierats öppnas
    pid2, _ = anmal('GR-20261007-prov', 'GR-20261007-prov#B9')
    bl.satt_status(pid2, 'klar', commit='def5678')
    assert anmal('GR-20261009-prov', 'GR-20261007-prov#B9')[0] == pid2 and meta(pid2)['status'] == 'vilande', meta(pid2)
    # en avvisad eller ersatt post öppnas inte
    for i, status in enumerate(('avvisad', 'ersatt')):
        fynd = 'GR-20261007-prov#B1%d' % i
        p3, _ = anmal('GR-20261007-prov', fynd)
        bl.satt_status(p3, status, not_='i provet')
        assert anmal('GR-20261009-prov', fynd)[0] == p3 and meta(p3)['status'] == status, (status, meta(p3))


@fall('backloggen: återöppningen är idempotent, och bara en rapport som är senare än varje rapport som posten nämner öppnar den')
def _ateroppningens_regler():
    # granskningen av r99, BÖR-5: samma rapport efter en ny rättelse, rapporten som verifierade, en äldre rapport och fyndets
    # egen rapport i en annan form öppnade posten; en post som pågår ska inte öppnas
    def anmal(kallref, fynd):
        rc, ut = kommando('ny', '--kalla', 'granskning', '--titel', 'Ett fynd med regler', '--varfor', 'Syntetiskt.', '--kallref', kallref, '--fynd', fynd)
        assert rc == 0, ut
        return ut.split()[0]

    def klar_post(fynd, verifierad=None):
        pid = anmal(fynd.split('#')[0], fynd)
        bl.satt_status(pid, 'klar', commit='abc1234')
        if verifierad:
            bl.verifiera(pid, verifierad)
        return pid

    def orord(pid, kallref, vad):
        fore = (bl.MAPP / (pid + '.md')).read_bytes()
        assert anmal(kallref, meta(pid)['fynd']) == pid
        assert (bl.MAPP / (pid + '.md')).read_bytes() == fore, ('%s ändrade posten' % vad, meta(pid)['status'], meta(pid)['kropp'][-300:])
    # 1. samma senare rapport efter en ny rättelse ändrar ingenting (idempotent), men en ännu senare rapport öppnar
    pid = klar_post('GR-20261007-prov#R1')
    anmal('GR-20261009-prov', 'GR-20261007-prov#R1')
    assert meta(pid)['status'] == 'vilande', meta(pid)
    bl.satt_status(pid, 'klar', commit='def5678')  # en ny rättelse efter GR-20261009-prov
    orord(pid, 'GR-20261009-prov', 'samma rapport en gång till')
    orord(pid, 'granskningar/GR-20261009-prov.md', 'samma rapport som sökväg')
    anmal('GR-20261010-prov', 'GR-20261007-prov#R1')
    m = meta(pid)
    assert m['status'] == 'vilande' and m['kropp'].count('anmälde fyndet') == 2, ('en senare rapport öppnar inte', m['status'], m['kropp'][-400:])
    # 2. rapporten som verifierade rättelsen öppnar inte, och verifieringen står kvar
    pid = klar_post('GR-20261007-prov#R2', verifierad='GR-20261008-prov')
    orord(pid, 'GR-20261008-prov', 'rapporten som verifierade')
    assert meta(pid).get('verifierad') == 'GR-20261008-prov'
    # 3. en rapport från före fyndets och en mellan fyndets och verifieringens öppnar inte
    pid = klar_post('GR-20261007-prov#R3', verifierad='GR-20261009-prov')
    orord(pid, 'GR-20261006-prov', 'en äldre rapport än fyndets')
    orord(pid, 'GR-20261008-prov', 'en rapport från före verifieringen')
    # 4. fyndets egen rapport i en annan form öppnar inte
    pid = klar_post('GR-20261007-prov#R4')
    for form in ('GR-20261007-prov.MD', 'granskningar/GR-20261007-prov.md#R4', 'granskningar/GR-20261007-prov/', 'gr-20261007-prov'):
        orord(pid, form, 'fyndets egen rapport som %s' % form)
    # 5. en rapport utan datum i id:t går inte att ordna: posten öppnas inte, och utdatan säger hur den öppnas för hand
    pid = klar_post('GR-20261007-prov#R5')
    orord(pid, 'R5-utan-datum', 'en rapport utan datum')
    rc, ut = kommando('ny', '--kalla', 'granskning', '--titel', 'x', '--varfor', 'x', '--kallref', 'R5-utan-datum', '--fynd', 'GR-20261007-prov#R5')
    assert rc == 0 and 'öppnas inte' in ut and 'status %s vilande' % pid in ut, ut
    # 6. en post som pågår eller väntar öppnas inte om igen
    for status in ('pagar', 'vilande'):
        fynd = 'GR-20261007-prov#R6%s' % status
        pid = anmal('GR-20261007-prov', fynd)
        if status != 'vilande':
            bl.satt_status(pid, status)
        orord(pid, 'GR-20261009-prov', 'en senare rapport mot en post som är %s' % status)


@fall('backloggen: huvudvärden utan radbrytningar och kontrolltecken, och --commit som hex med 7–40 tecken')
def _huvudvarden():
    fore = poster()
    for falt, varde in (('--kallref', 'REGISTER.md\nstatus: klar\nverifierad: GR-ingen'), ('--steg', 'x\u2028verifierad: GR-ingen'),
                        ('--sar', 'x\ry'), ('--kallref', 'x\ty'), ('--kallref', 'x\x85verifierad: GR-ingen')):
        rc, ut = kommando('ny', '--kalla', 'kirurg', '--titel', 'Injektion', '--varfor', 'x', falt, varde)
        assert rc == 2 and poster() == fore, ('%s %r gick igenom' % (falt, varde), ut)
    pid = bl.ny('kirurg', 'En post att stänga', 'Syntetiskt.', kallref='prov')
    fil = bl.MAPP / (pid + '.md')
    innan = fil.read_bytes()
    for commit in ('abc1234\nverifierad: GR-ingen', 'abc123', 'xyz1234', 'ABC1234', 'a' * 41, 'abc1234 def5678'):
        rc, ut = kommando('status', pid, 'klar', '--commit', commit)
        assert rc == 2 and fil.read_bytes() == innan, ('--commit %r gick igenom' % commit, ut)
    for commit in ('abc1234', 'f' * 40):
        rc, ut = kommando('status', pid, 'klar', '--commit', commit)
        assert rc == 0 and meta(pid)['commit'] == commit and 'verifierad' not in meta(pid), (commit, ut)
    rc, ut = kommando('lista')
    assert next(r for r in ut.splitlines() if pid in r).startswith('klar, inte verifierad'), ut


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


@fall('backloggen: verifieringen tas bort när status eller commit ändras, och står kvar annars')
def _verifieringens_livslangd():
    pid = bl.ny('kirurg', 'En verifierad post', 'Syntetiskt.', kallref='prov')
    bl.satt_status(pid, 'klar', commit='abc1234')
    bl.verifiera(pid, 'GR-20261008-prov')
    for args in ((pid, 'klar'), (pid, 'klar', '--not', 'bara en not'), (pid, 'klar', '--commit', 'abc1234')):
        rc, ut = kommando('status', *args)
        m = meta(pid)
        assert rc == 0 and m.get('verifierad') == 'GR-20261008-prov' and m.get('verifierad_tid'), (
            'samma status och commit tog bort verifieringen (%s)' % ' '.join(args[1:]), m)
    rc, ut = kommando('status', pid, 'pagar')
    m = meta(pid)
    assert rc == 0 and 'verifierad' not in m and 'verifierad_tid' not in m, ('status klar → pagar behöll verifieringen', m)
    assert 'GR-20261008-prov verifierade status klar med commit abc1234' in m['kropp'], m['kropp']
    rc, ut = kommando('lista')
    assert next(r for r in ut.splitlines() if pid in r).startswith('pagar '), ut


@fall('backloggen: verifiera kräver ett giltigt rapport-id från en annan rapport än fyndets, och sätter verifierad_tid men inte andrad')
def _verifiera_rapporten():
    pid = bl.ny('granskning', 'Ett fynd att verifiera', 'Syntetiskt.', kallref='GR-20261007-prov', fynd='GR-20261007-prov#B7')
    bl.satt_status(pid, 'klar', commit='abc1234')
    for rapport in ('GR 20261008', 'underlag/granskningar/GR-x.md', '', 'x', 'GR-20261007-prov'):
        rc, ut = kommando('verifiera', pid, '--rapport', rapport)
        assert rc == 2 and 'verifierad' not in meta(pid), ('rapport %r godtogs' % rapport, ut)
    fore = meta(pid)
    rc, ut = kommando('verifiera', pid, '--rapport', 'GR-20261008-prov')
    m = meta(pid)
    assert rc == 0 and m.get('verifierad') == 'GR-20261008-prov', (ut, m)
    assert re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\dZ', m.get('verifierad_tid') or '') and m.get('andrad') == fore.get('andrad'), (
        'skapad, ändrad och verifierad ska vara skilda uppgifter', m)


@fall('backloggen: varje skrivning sker under fillåset (vl.las), också en ny post')
def _laset():
    pid = bl.ny('kirurg', 'En post att ändra under låset', 'Syntetiskt.', kallref='prov')
    for vad, args in (('status', ('status', pid, 'pagar')),
                      ('ny', ('ny', '--kalla', 'kirurg', '--titel', 'En post att ändra under låset', '--varfor', 'x'))):
        markor = TMP / ('markor-' + vad)
        fore = (meta(pid)['status'], poster())
        with vl.las(LASFIL):
            p = subprocess.Popen(cli(*args, markor=markor), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            slut = time.time() + 60
            while not markor.exists() and time.time() < slut and p.poll() is None:
                time.sleep(0.05)
            time.sleep(1.0)  # processen har nått skrivningen: utan lås är den klar nu
            vantar = p.poll() is None
            orord = (meta(pid)['status'], poster()) == fore
        ut, fel_ = p.communicate(timeout=60)
        assert markor.exists() and vantar and orord, '%s skrev medan låset hölls (väntade %s, orört %s): %s' % (vad, vantar, orord, ut + fel_)
        assert p.returncode == 0, ut + fel_
    assert meta(pid)['status'] == 'pagar' and len(list(bl.MAPP.glob('B-*-en-post-att-andra-under-laset*.md'))) == 2
    if (ROOT / '.git').exists():  # låset och tempfilerna hamnar aldrig i git (gruppera.py lägger till hela backlog/)
        for f in ('backlog/.backlog.las', 'backlog/.B-x.md.123.tmp'):
            r = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--no-index', f], capture_output=True)
            assert r.returncode == 0, '%s ignoreras inte av git' % f


@fall('backloggen: samtidiga statusändringar på samma post går inte förlorade (posten läses under låset)')
def _samtidiga_noter():
    pid = bl.ny('kirurg', 'En post med många noter', 'Syntetiskt.', kallref='prov')
    n = 6
    markorer = [TMP / ('not-markor-%d' % i) for i in range(n)]
    with vl.las(LASFIL):  # alla processer når låset medan provet håller det; läser de posten före låset ser alla samma läge
        ps = samtidigt([('status', pid, 'pagar', '--not', 'not-%d' % i) for i in range(n)], markorer=markorer)
        slut = time.time() + 60
        while not all(m.exists() for m in markorer) and time.time() < slut:
            time.sleep(0.05)
        time.sleep(1.5)
    ut = [p.communicate(timeout=120) for p in ps]
    assert all(p.returncode == 0 for p in ps), [e[-200:] for _o, e in ut]
    kropp = meta(pid)['kropp']
    forlorade = [i for i in range(n) if 'not-%d' % i not in kropp]
    assert not forlorade, 'noter som gick förlorade: %s av %d' % (forlorade, n)


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


# ===== startkontrollen: repots identitet och informationsraden om dokumentationen =====

@fall('startkontrollen: repots identitet med hel commit, gren eller fristående HEAD och ocommittade filer, utan att indexet skrivs om')
def _repot():
    import startkontroll as sk
    r = TMP / 'repo-prov'
    r.mkdir()
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}

    def git(*a):
        return subprocess.run(['git', '-C', str(r), '-c', 'user.name=prov', '-c', 'user.email=prov@exempel.se',
                               '-c', 'commit.gpgsign=false', *a], capture_output=True, text=True, env=env, check=True).stdout.strip()
    git('init', '-q', '-b', 'main')
    (r / 'a.txt').write_text('a\n')
    git('add', 'a.txt')
    git('commit', '-q', '-m', 'a')
    huvud = git('rev-parse', 'HEAD')
    # en spårad fil med ny tidsstämpel men samma innehåll: git status skriver då om indexet, utom med --no-optional-locks
    # (granskningen av r97, KAN 1: startkontrollen ska inte ta indexlåset i en utcheckning där någon committar)
    os.utime(r / 'a.txt', (946684800, 946684800))
    index = (r / '.git' / 'index').read_bytes()
    i = sk.repo_identitet(r)
    assert i == {'commit': huvud, 'gren': 'main', 'ocommittade': 0}, i
    assert (r / '.git' / 'index').read_bytes() == index, 'repots identitet skrev om indexet'
    (r / 'b.txt').write_text('b\n')
    assert sk.repo_identitet(r)['ocommittade'] == 1, sk.repo_identitet(r)
    git('checkout', '-q', '--detach')
    assert sk.repo_identitet(r)['gren'] == 'ingen (fristående HEAD)', sk.repo_identitet(r)


@fall('startkontrollen: förteckningen ger rätt antal poster, saknade filer och fel sha256, och ingen rad kastar')
def _forteckningen():
    import startkontroll as sk
    rot = TMP / 'fixtur'
    g = rot / 'underlag' / 'granskningar'
    (g / 'sessioner' / 'stangd').mkdir(parents=True)
    (rot / 'README.md').write_text('# x\n\n## Var information finns\n\nTabellen.\n')
    filer = {'sessioner/GR-a.md': b'a\n', 'sessioner/GR-b.md': b'b\n', 'sessioner/GR-c.md': b'c, ny\n', 'sessioner/GR-d.md': b'd, ny\n',
             'sessioner/stangd/GR-e.md': b'e\n'}
    for n, b in filer.items():
        (g / n).write_bytes(b)
    poster_ = [{'fil': 'granskningar/sessioner/GR-a.md', 'sha256': vl.sha(b'a\n')},
               {'fil': 'granskningar/sessioner/GR-b.md', 'sha256': vl.sha(b'b\n').upper()},
               {'fil': 'granskningar/sessioner/GR-c.md', 'sha256': vl.sha(b'c\n')},  # ändrad efter kopieringen
               {'fil': 'granskningar/sessioner/GR-d.md', 'sha256': vl.sha(b'd\n')},  # ändrad efter kopieringen
               {'fil': 'granskningar/sessioner/GR-borta.md', 'sha256': vl.sha(b'e\n')},  # saknas
               {'fil': '../README.md', 'sha256': vl.sha(b'x')},  # utanför underlag/: kontrolleras inte
               # filer som inte går att nå kastar OSError i pathlib: de räknas, och starten påverkas inte (granskningen av r97, B1)
               {'fil': 'granskningar/' + 'x' * 300 + '.md', 'sha256': vl.sha(b'x')},
               {'fil': 'granskningar/' + '/'.join(['y' * 200] * 10), 'sha256': vl.sha(b'y')},
               {'fil': 'granskningar/sessioner/stangd/GR-e.md', 'sha256': vl.sha(b'e\n')}]
    (g / 'FORTECKNING.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in poster_) + '\n{trasig rad\n')
    os.chmod(g / 'sessioner' / 'stangd', 0)
    try:
        d = sk.dokumentationen(rot)
    finally:
        os.chmod(g / 'sessioner' / 'stangd', 0o755)
    assert d == {'platsregel': True, 'forteckning': {'poster': 10, 'saknas': 1, 'fel_sha': 2, 'ej_kontrollerade': 5}}, d
    t = sk.dokumentation_text(d)
    assert 'platsregeln finns' in t and '10 poster, 1 filer saknas, 2 med fel sha256; 5 poster kunde inte kontrolleras' in t, t
    os.chmod(g, 0)  # förteckningens egen katalog utan läsrätt: en rad om felet, inget undantag
    try:
        d = sk.dokumentationen(rot)
    finally:
        os.chmod(g, 0o755)
    assert d['platsregel'] is True and 'PermissionError' in (d['forteckning'] or {}).get('fel', ''), d
    (g / 'FORTECKNING.jsonl').unlink()
    (rot / 'README.md').write_text('# x\n\n## Något annat\n')
    d = sk.dokumentationen(rot)
    assert d == {'platsregel': False, 'forteckning': None}, d
    assert 'platsregeln saknas' in sk.dokumentation_text(d) and 'ingen privat förteckning' in sk.dokumentation_text(d)
    # rubriken räknas bara utanför kodblock (granskningen av r97, KAN 8)
    for readme, vantat in (('# x\n\n```\n## Var information finns\n```\n', False), ('# x\n\n~~~md\n## Var information finns\n~~~\n', False),
                           ('# x\n\n```\nkod\n```\n\n## Var information finns\n', True)):
        (rot / 'README.md').write_text(readme)
        assert sk.dokumentationen(rot)['platsregel'] is vantat, (readme, vantat)


# ===== dashboarden: backloggvyn =====

VY_JS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8'), data = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const a = html.indexOf('async function backlogvy() {'), b = html.indexOf('\nasync function ', a + 1);
if (a < 0 || b < 0) throw new Error('backlogvy saknas i index.html');
const escKod = html.split('\n').find((r) => r.startsWith('const esc = '));
const vy = { innerHTML: '' };
const stubbar = {
  aktivNav: () => {}, kommando: () => '', raknare: () => {}, post: async () => ({}),
  api: async (u) => (u === '/api/backlog' ? data : {}),
  $: (s) => (s === '#vy' ? vy : { hidden: false, textContent: '' }),
  document: { querySelectorAll: () => [] },
};
const f = new Function(...Object.keys(stubbar), escKod + '\n' + html.slice(a, b) + '\nreturn backlogvy();');
f(...Object.values(stubbar)).then(() => process.stdout.write(vy.innerHTML), (e) => { console.error(e); process.exit(1); });
"""


@fall('dashboarden: backloggvyn visar om en klar post är verifierad, och fyndet')
def _dashboarden():
    sys.path.insert(0, str(ROOT / 'dashboard'))
    import server as dash
    assert dash.bl is bl, 'dashboarden läser en annan backlogmodul'
    spara = bl.MAPP
    bl.MAPP = BL_ROT / 'dashboard-backlog'  # under bl.ROOT, som postens fil räknas från
    bl.MAPP.mkdir()
    try:
        a = bl.ny('granskning', 'Klar och verifierad', 'Syntetiskt.', kallref='GR-20261007-prov', fynd='GR-20261007-prov#B5')
        bl.satt_status(a, 'klar', commit='abc1234')
        bl.verifiera(a, 'GR-20261008-prov')
        b = bl.ny('kirurg', 'Klar men inte verifierad', 'Syntetiskt.', kallref='prov')
        bl.satt_status(b, 'klar', commit='def5678')
        c = bl.ny('kirurg', 'Vilande', 'Syntetiskt.', kallref='prov')
        lista = dash.backloggen()
    finally:
        bl.MAPP = spara
    lagen = {p['id']: p.get('lage') for p in lista}
    assert lagen == {a: 'klar, verifierad av GR-20261008-prov', b: 'klar, inte verifierad', c: 'vilande'}, lagen
    (TMP / 'vy.js').write_text(VY_JS)
    (TMP / 'backlog.json').write_text(json.dumps(lista, ensure_ascii=False))
    r = subprocess.run(['node', str(TMP / 'vy.js'), str(ROOT / 'dashboard' / 'index.html'), str(TMP / 'backlog.json')],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout, r.stderr[-400:]
    poster_ = {m.group(1): m.group(0) for m in re.finditer(r'<details class="post">.*?<code>(B-[^<]+)</code>.*?</details>', r.stdout, re.S)}
    assert set(poster_) == {a, b, c}, sorted(poster_)
    assert '<span class="chip ok">Klar, verifierad av GR-20261008-prov</span>' in poster_[a], poster_[a][:600]
    assert 'fynd GR-20261007-prov#B5' in poster_[a] and '<span class="chip">Granskning</span>' in poster_[a], poster_[a][:600]
    assert 'Klar, inte verifierad</span>' in poster_[b] and 'chip ok' not in poster_[b], poster_[b][:600]
    assert '>Vilande</span>' in poster_[c], poster_[c][:600]


print('dokumentationens prov: %d fel%s' % (len(FEL), (': ' + '; '.join(FEL)) if FEL else ''), file=sys.stderr)
sys.exit(1 if FEL else 0)
