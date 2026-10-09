#!/usr/bin/env python3
"""forfragningar.py — läget för en kundsajts formulärärenden i D1 (kunskap/forfragan.md, Utkorgen; kunskap/drift.md):
antal per utkorgsstatus, ärenden vars avisering väntar eller har okänt utfall, fallna aviseringar och ärenden som har
passerat sitt gallringsdatum. Skriver bara id:n, tider och status, aldrig namn, telefon, meddelande eller bilagans namn.

Gallringen är en torrkörning tills `--utfor` anges: då tas utgångna ärenden bort ur D1 (utkorgsraden och ärendet i en
transaktion) och deras bilagor ur R2. Mot kundens riktiga D1 (`--remote`) är det en handling på kunddata som kräver
ägarens ja; inget schema kör den automatiskt.

    .venv/bin/python kontroller/forfragningar.py <kundrepo> --remote [--gallra [--utfor]]
    .venv/bin/python kontroller/forfragningar.py <kundrepo> --lokal <persist-katalog> [--gallra [--utfor]]
    .venv/bin/python kontroller/forfragningar.py <kundrepo> --remote --csv <fil>

`--csv` är katalogens K10-grundnivå (k10-csv-export): ärendena som CSV för verksamhetens befintliga kundregister, med
personuppgifter, därför bara till en privat fil (0600) utanför det publika repot eller i dess privata underlag/ och
kunder/. Celler som ett kalkylprogram skulle läsa som formel inleds med en apostrof. Det är ingen koppling till ett
kundregister: importen gör verksamheten.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

VANTA_MINUTER = 15  # en avisering som väntat längre har okänt eller uteblivet utfall
ISO = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z')


def iso(t):
    return t.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def lage(kor, nu=None):
    """kor(sql) → rader (dict). Ger läget utan personuppgifter."""
    nu = nu or datetime.now(timezone.utc)
    grans = iso(nu - timedelta(minutes=VANTA_MINUTER))
    nu_s = iso(nu)
    assert ISO.fullmatch(grans) and ISO.fullmatch(nu_s)
    status = {r['status'] or 'utan_utkorg': r['n'] for r in kor(
        'SELECT u.status AS status, count(*) AS n FROM forfragningar f LEFT JOIN utkorg u ON u.forfragan = f.id GROUP BY u.status')}
    oklara = kor("SELECT f.id AS id, f.mottagen AS mottagen, u.status AS status, u.uppdaterad AS uppdaterad, u.forsok AS forsok "
                 "FROM forfragningar f JOIN utkorg u ON u.forfragan = f.id WHERE u.status IN ('vantar', 'skickar') "
                 "AND u.uppdaterad < '%s' ORDER BY f.mottagen" % grans)
    fel = kor("SELECT f.id AS id, f.mottagen AS mottagen, u.forsok AS forsok, u.fel AS fel FROM forfragningar f "
              "JOIN utkorg u ON u.forfragan = f.id WHERE u.status = 'fel' ORDER BY f.mottagen")
    utgangna = kor("SELECT id, gallras, bilaga FROM forfragningar WHERE gallras < '%s' ORDER BY gallras" % nu_s)
    return {'tid': nu_s, 'status': status, 'totalt': sum(status.values()),
            'oklara': [{k: r[k] for k in ('id', 'mottagen', 'status', 'uppdaterad', 'forsok')} for r in oklara],
            'fel': [{k: r[k] for k in ('id', 'mottagen', 'forsok', 'fel')} for r in fel],
            'utgangna': [{'id': r['id'], 'gallras': r['gallras'], 'bilaga': bool(r['bilaga'])} for r in utgangna],
            '_bilagor': [r['bilaga'] for r in utgangna if r['bilaga']]}


def gallra(kor, ta_bort_bilaga, nu=None, utfor=False):
    """Utgångna ärenden: torrkörning, eller borttagning med utfor=True (bilagan först, sedan raderna i en sats)."""
    l = lage(kor, nu)
    plan = {'tid': l['tid'], 'antal': len(l['utgangna']), 'bilagor': len(l['_bilagor']), 'utfort': False, 'fel': []}
    if not utfor or not l['utgangna']:
        return plan
    for nyckel in l['_bilagor']:
        try:
            ta_bort_bilaga(nyckel)
        except (OSError, RuntimeError) as e:
            plan['fel'].append('bilagan kunde inte tas bort: %s' % type(e).__name__)
    if plan['fel']:
        return plan  # inga rader tas bort när en bilaga står kvar: avstämningen hittar den genom ärendet
    ids = [r['id'] for r in l['utgangna']]
    assert all(re.fullmatch(r'[0-9a-f-]{36}', i) for i in ids)
    lista = ', '.join("'%s'" % i for i in ids)
    kor('DELETE FROM utkorg WHERE forfragan IN (%s); DELETE FROM forfragningar WHERE id IN (%s)' % (lista, lista))
    plan['utfort'] = True
    return plan


FORMEL = ('=', '+', '-', '@', '\t', '\r')
REPO = Path(__file__).resolve().parents[1]


def csv_fil(fil):
    """Målet för en export med personuppgifter: aldrig en symlänk, aldrig i ett kundrepo (det pushas och driftsätts), och
    i ett git-arbetsträd (motorrepot och dess worktrees) bara en sökväg som git ignorerar, till exempel underlag/."""
    import subprocess
    f = Path(fil).absolute()
    if f.is_symlink() or (f.exists() and not f.is_file()):
        raise ValueError('exportens mål ska vara en ny eller vanlig fil')
    r = f.parent.resolve() / f.name
    if 'kundrepo' in r.parts or 'kundrepo-tidigare' in r.parts:
        raise ValueError('ärenden med personuppgifter skrivs aldrig i ett kundrepo')
    rot = next((d for d in (r.parent, *r.parent.parents) if (d / '.git').exists()), None)
    if rot is not None and subprocess.run(['git', '-C', str(rot), 'check-ignore', '-q', str(r)], capture_output=True).returncode != 0:
        raise ValueError('i ett git-arbetsträd skrivs ärenden med personuppgifter bara till en ignorerad sökväg (till exempel underlag/)')
    return f


def exportera_csv(kor, fil):
    """Ärendena som CSV (UTF-8 med BOM för kalkylprogram), filen 0600. Ger antalet rader."""
    import csv
    import io
    import os
    f = csv_fil(fil)
    rader = kor('SELECT f.id AS id, f.mottagen AS mottagen, f.namn AS namn, f.telefon AS telefon, f.meddelande AS meddelande, '
                'f.bilaga AS bilaga, u.status AS avisering FROM forfragningar f LEFT JOIN utkorg u ON u.forfragan = f.id ORDER BY f.mottagen')
    ut = io.StringIO()
    w = csv.writer(ut)
    w.writerow(['id', 'mottagen', 'namn', 'telefon', 'meddelande', 'bild', 'avisering'])
    def cell(v):
        v = '' if v is None else str(v)
        return "'" + v if v.startswith(FORMEL) else v
    for x in rader:
        w.writerow([cell(x['id']), cell(x['mottagen']), cell(x['namn']), cell(x['telefon']), cell(x['meddelande']),
                    'ja' if x['bilaga'] else 'nej', cell(x['avisering'] or 'okänd')])
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix='.export-', dir=str(f.parent))  # 0600 från början, sedan ett atomiskt byte
    try:
        with os.fdopen(fd, 'w', encoding='utf-8-sig', newline='') as h:
            h.write(ut.getvalue())
        os.replace(tmp, str(f))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return len(rader)


def wrangler_kor(kundrepo, plats, konto=None, tmp=None):
    """kor(sql) mot kundrepots D1 genom Wrangler: --remote med kontots miljö, eller --local med en persist-katalog."""
    import kundrepo as kr
    wr = str(Path(kundrepo) / 'node_modules' / '.bin' / 'wrangler')
    if plats == 'remote':
        miljo = kr.cloudflare_miljo(konto, tmp)
        flaggor = ['--remote']
    else:
        import os
        bas = Path(plats).parent  # Wranglers konfiguration och logg bredvid det lokala tillståndet, aldrig i hemkatalogen
        miljo = dict(os.environ, WRANGLER_SEND_METRICS='false', XDG_CONFIG_HOME=str(bas / 'xdg'), WRANGLER_LOG_PATH=str(bas / 'wrangler-logg'))
        flaggor = ['--local', '--persist-to', str(plats)]

    def kor(sql):
        r = kr.kommando([wr, 'd1', 'execute', 'DB', *flaggor, '--json', '--command', sql], kundrepo, frist=120, env=miljo)
        if r.returncode:
            raise RuntimeError('wrangler d1 execute: %s' % (r.stderr or r.stdout)[-200:])
        start = r.stdout.find('[')
        data = json.loads(r.stdout[start:]) if start >= 0 else []
        return [rad for block in data for rad in (block.get('results') or [])]

    konfig = (Path(kundrepo) / 'wrangler.jsonc').read_text(encoding='utf-8')
    bucket = re.search(r'"bucket_name":\s*"([^"]+)"', konfig).group(1)
    # en bucket med jurisdiktion nås bara med samma jurisdiktion hos Cloudflare
    jur = re.search(r'"jurisdiction":\s*"([a-z]+)"', konfig)
    r2flaggor = flaggor + (['--jurisdiction', jur.group(1)] if jur and plats == 'remote' else [])

    def ta_bort_bilaga(nyckel):
        r = kr.kommando([wr, 'r2', 'object', 'delete', '%s/%s' % (bucket, nyckel), *r2flaggor], kundrepo, frist=120, env=miljo)
        if r.returncode:
            raise RuntimeError('wrangler r2 object delete')
    return kor, ta_bort_bilaga


def main(argv=None):
    a = argparse.ArgumentParser(prog='forfragningar', description=__doc__.split('\n\n')[0])
    a.add_argument('kundrepo')
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument('--remote', action='store_true', help='kundens D1 hos Cloudflare (kontot ur cloudflare.env)')
    g.add_argument('--lokal', help='en lokal persist-katalog (wrangler dev --persist-to)')
    a.add_argument('--gallra', action='store_true')
    a.add_argument('--utfor', action='store_true', help='tar bort utgångna ärenden; mot --remote bara med ägarens ja')
    a.add_argument('--csv', help='ärendena som CSV till en privat fil (K10-grundnivån)')
    x = a.parse_args(argv)
    tmp = None
    konto = None
    if x.remote:
        import korregister
        import kundrepo as kr
        konto, hinder = kr.cloudflare_konto()
        if hinder:
            print(json.dumps({'ok': False, 'hinder': hinder}, ensure_ascii=False))
            return 1
        tmp = korregister.egen_tmp('nwp-preview-', 'formulärärendenas läge')
    try:
        kor, ta_bort = wrangler_kor(Path(x.kundrepo).resolve(), 'remote' if x.remote else Path(x.lokal).resolve(), konto, tmp)
        if x.csv:
            ut = {'csv': str(csv_fil(x.csv)), 'rader': exportera_csv(kor, x.csv)}
        else:
            ut = gallra(kor, ta_bort, utfor=x.utfor) if x.gallra else {k: v for k, v in lage(kor).items() if not k.startswith('_')}
        print(json.dumps(dict(ut, ok=True), ensure_ascii=False, indent=1))
        return 0
    except (OSError, RuntimeError, ValueError) as e:
        print(json.dumps({'ok': False, 'hinder': str(e)[:300]}, ensure_ascii=False))
        return 1
    finally:
        if tmp:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
