#!/usr/bin/env python3
"""backlog.py — den vilande backloggen: en markdownfil per post i backlog/.

    .venv/bin/python kontroller/backlog.py ny --kalla kirurg|dom|bygge|bevakning|granskning --titel T --varfor V
        [--forslag F] [--klart K] [--steg S] [--sar S] [--kallref R] [--fynd RAPPORT#FYND] [--prio hog|normal]
    .venv/bin/python kontroller/backlog.py lista [--status vilande] [--json]
    .venv/bin/python kontroller/backlog.py visa ID
    .venv/bin/python kontroller/backlog.py status ID vilande|pagar|klar|avvisad|ersatt [--commit SHA] [--not TEXT]
    .venv/bin/python kontroller/backlog.py verifiera ID --rapport RAPPORT [--not TEXT]

Poster skapas alltid vilande, automatiskt av kirurgen (dom "ta in" eller "prova A/B"), av dashboarden när ägaren
dömer ett bygge, och av en byggkörning som hittar en brist i verktyg, skill eller kunskap. Ett granskningsfynd som inte
rättas i samma uppdrag blir en post med kalla granskning: kallref är rapportens id eller sökväg (förteckningens
sökvägar räknas från underlag/) och fynd är <rapportens id>#<fyndets id>. Ett fynd får en post: finns fyndet redan i
en post, oavsett status, skapas ingen ny, och ny ger den postens id (slutkod 0). Ingen post genomförs av sig själv:
ägaren startar en session och säger "implementera enligt backlog" (skillen backlog).

klar betyder genomförd och committad. Fältet verifierad (id för den rapport som verifierade rättelsen, en annan än den
som hittade fyndet) och verifierad_tid sätts bara med kommandot verifiera, aldrig av sig självt och aldrig för att kod
ändrats; ändras status eller commit tas fälten bort ur huvudet och en not säger varför (README.md, Var information
finns). Huvudets värden får inte innehålla radbrytningar eller andra kontrolltecken, och --commit är hex med 7–40
tecken, så att inget argument kan lägga in egna huvudrader. Varje skrivning sker under backloggens fillås
(verktygslada.las) med tempfil och os.replace, så att samtidiga sessioner inte skriver över varandras poster.
Exit 0 = klart; 2 = fel i anropet.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verktygslada as vl  # noqa: E402  (fillåset, samma som verktygslådans)

ROOT = Path(__file__).resolve().parents[1]
MAPP = ROOT / 'backlog'
STATUS = ('vilande', 'pagar', 'klar', 'avvisad', 'ersatt')  # ersatt: av ett senare beslut eller sammanförd i en annan post
KALLOR = ('kirurg', 'dom', 'bygge', 'bevakning', 'granskning')
FALT = ('id', 'status', 'kalla', 'kallref', 'fynd', 'korning', 'skapad', 'prio', 'steg', 'sar', 'commit', 'verifierad',
        'verifierad_tid', 'andrad')
RAPPORT_ID = r'\w[\w.-]{1,80}'  # en rapports id, till exempel GR-20261007-r97 (README.md, Var information finns)
FYND = re.compile(r'%s#\w[\w.-]{0,40}' % RAPPORT_ID)  # <rapportens id>#<fyndets id>, till exempel GR-20261006-r92#B1
COMMIT = re.compile(r'[0-9a-f]{7,40}')  # --commit: en commit, kort eller hel
# radbrytningar och andra kontrolltecken, också de som str.splitlines delar på (\x1c–\x1e, \x85, U+2028, U+2029): ett
# sådant tecken i ett huvudvärde blir en egen huvudrad när posten läses (granskningen av r97, BÖR 2)
KONTROLLTECKEN = re.compile(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]')
LAS = '.backlog.las'  # backloggens fillås, i MAPP; punktfilerna där ignoreras av git


def _slug(t):
    t = t.lower().translate(str.maketrans('åäöéü', 'aaoeu'))
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:48].strip('-') or 'post'


def las(p):
    text = Path(p).read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.S)
    meta, kropp = {}, text
    if m:
        for rad in m.group(1).splitlines():
            k, _, v = rad.partition(':')
            if k.strip():
                meta[k.strip()] = v.strip()
        kropp = m.group(2)
    titel = re.search(r'^# (.+)$', kropp, re.M)
    meta['titel'] = titel.group(1).strip() if titel else meta.get('id', Path(p).stem)
    meta['kropp'] = kropp
    meta['fil'] = str(Path(p).relative_to(ROOT))
    return meta


def _fillas():
    """Backloggens fillås: samma mekanism som verktygslådans (vl.las). Varje läs–ändra–skriv och varje ny post sker
    under det, så att två sessioner eller dashboardens trådar inte skriver över varandras poster."""
    return vl.las(MAPP / LAS)


def skriv(meta, kropp):
    """Atomiskt, som verktygslada.skriv_json: tempfil i samma katalog och os.replace. Ett avbrott mitt i skrivningen
    lämnar den förra posten hel. Ett huvudvärde med en radbrytning eller ett annat kontrolltecken skrivs aldrig
    (ValueError, inget ändras). Anroparen håller låset."""
    for k in FALT:
        if meta.get(k) not in (None, '') and KONTROLLTECKEN.search(str(meta[k])):
            raise ValueError('%s får inte innehålla radbrytningar eller andra kontrolltecken' % k)
    rader = ['---'] + ['%s: %s' % (k, meta[k]) for k in FALT if meta.get(k) not in (None, '')] + ['---', '']
    p = MAPP / (meta['id'] + '.md')
    tmp = MAPP / ('.%s.%d.tmp' % (p.name, os.getpid()))
    try:
        tmp.write_text('\n'.join(rader) + kropp.lstrip('\n'), encoding='utf-8')
        os.replace(tmp, p)
    finally:
        if tmp.exists():
            tmp.unlink()


def lista(status=None):
    if not MAPP.is_dir():
        return []
    poster = [las(p) for p in sorted(MAPP.glob('B-*.md'))]
    if status:
        poster = [p for p in poster if p.get('status') == status]
    return sorted(poster, key=lambda p: (p.get('prio') != 'hog', p.get('skapad', ''), p['id']))


def lage(meta):
    """Postens läge för läsaren: klar betyder genomförd och committad, och verifierad är den först när en rapport har
    verifierat rättelsen (fältet verifierad)."""
    s = meta.get('status') or '?'
    if s != 'klar':
        return s
    return ('klar, verifierad av %s' % meta['verifierad']) if meta.get('verifierad') else 'klar, inte verifierad'


def ny(kalla, titel, varfor, forslag=None, klart=None, steg=None, sar=None, kallref=None, prio='normal', fynd=None):
    if kalla not in KALLOR:
        raise ValueError('kalla ska vara en av ' + ', '.join(KALLOR))
    if not titel.strip() or not varfor.strip():
        raise ValueError('titel och varför krävs')
    fynd = (fynd or '').strip() or None
    if fynd and not FYND.fullmatch(fynd):
        raise ValueError('fynd ska vara <rapportens id>#<fyndets id>, till exempel GR-20261006-r92#B1')
    if kalla == 'granskning' and not ((kallref or '').strip() and fynd):
        raise ValueError('en post ur en granskning kräver --kallref (rapportens id eller sökväg; förteckningens sökvägar räknas '
                         'från underlag/) och --fynd <rapportens id>#<fyndets id>')
    MAPP.mkdir(exist_ok=True)
    with _fillas():  # id:t väljs och posten skrivs under låset: två poster med samma titel samma dag får var sitt id
        befintlig = _med_fynd(fynd) if fynd else None
        if befintlig:  # ett fynd följs i en post från upptäckt till verifiering (ägarens uppdrag 2026-10-06, punkt 9)
            print('fyndet %s finns redan i %s (%s); ingen ny post' % (fynd, befintlig['id'], befintlig.get('status')), file=sys.stderr)
            return befintlig['id']
        dag = datetime.now(timezone.utc).strftime('%Y%m%d')
        bas = 'B-%s-%s' % (dag, _slug(titel))
        pid, n = bas, 2
        while (MAPP / (pid + '.md')).exists():
            pid, n = '%s-%d' % (bas, n), n + 1
        meta = {'id': pid, 'status': 'vilande', 'kalla': kalla, 'kallref': kallref, 'fynd': fynd,
                'prio': prio if prio in ('hog', 'normal') else 'normal',
                'skapad': datetime.now(timezone.utc).strftime('%Y-%m-%d'), 'steg': steg, 'sar': sar,
                'korning': os.environ.get('NWP_KORNING') or None}  # byggets körning: efterkörningen publicerar bara dess egna poster (F3)
        kropp = '# %s\n\n**Varför:** %s\n' % (titel.strip(), varfor.strip())
        if forslag:
            kropp += '\n**Förslag:** %s\n' % forslag.strip()
        if klart:
            kropp += '\n**Klart när:** %s\n' % klart.strip()
        skriv(meta, kropp)
    return pid


def _post(pid):
    p = MAPP / (pid + '.md')
    if not re.fullmatch(r'B-[a-z0-9-]+', pid) or not p.is_file():
        raise ValueError('okänd post: ' + pid)
    return p


def _med_fynd(fynd):
    """Posten som redan bär fyndet, eller None. Anroparen håller låset; en post som inte går att läsa hoppas över."""
    for p in sorted(MAPP.glob('B-*.md')):
        try:
            meta = las(p)
        except (OSError, UnicodeDecodeError):
            continue
        if meta.get('fynd') == fynd:
            return meta
    return None


def satt_status(pid, status, commit=None, not_=None):
    if status not in STATUS:
        raise ValueError('status ska vara en av ' + ', '.join(STATUS))
    if commit and not COMMIT.fullmatch(commit):
        raise ValueError('commit ska vara en commit i hex, 7–40 tecken (gemener)')
    p = _post(pid)
    with _fillas():  # posten läses, ändras och skrivs under låset: en samtidig ändring går inte förlorad
        meta = las(p)
        kropp = meta.pop('kropp')
        fore = (meta.get('status'), meta.get('commit'))
        meta['status'] = status
        meta['andrad'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
        if commit:
            meta['commit'] = commit
        if not_:
            kropp = kropp.rstrip('\n') + '\n\n**%s (%s):** %s\n' % (status.capitalize(), meta['andrad'][:10], not_.strip())
        # verifieringen gällde läget den gjordes i: en ny status eller commit är inte verifierad (ägarens uppdrag 2026-10-06,
        # punkt 7: automatik markerar aldrig ett fynd verifierat för att kod ändrats)
        if meta.get('verifierad') and (meta['status'], meta.get('commit')) != fore:
            meta.pop('verifierad_tid', None)
            kropp = kropp.rstrip('\n') + '\n\n**Verifieringen gäller inte längre (%s):** %s verifierade status %s med commit %s.\n' % (
                meta['andrad'][:10], meta.pop('verifierad'), fore[0], fore[1] or 'ej angivet')
        skriv(meta, kropp)
    return meta


def verifiera(pid, rapport, not_=None):
    """Sätter verifierad: <rapport> och verifierad_tid på en klar post, när en senare granskning (rapporten) har verifierat
    rättelsen. Bara det här uttryckliga kommandot sätter fälten. Rapporten som hittade fyndet kan inte verifiera
    rättelsen av det, och andrad står kvar: skapad, ändrad och senast verifierad är skilda uppgifter."""
    rapport = (rapport or '').strip()
    if not re.fullmatch(RAPPORT_ID, rapport):
        raise ValueError('rapport ska vara id:t för rapporten som verifierade rättelsen, till exempel GR-20261007-r97')
    p = _post(pid)
    with _fillas():
        meta = las(p)
        kropp = meta.pop('kropp')
        if meta.get('status') != 'klar':
            raise ValueError('bara en klar post kan verifieras: %s är %s' % (pid, meta.get('status')))
        if (meta.get('fynd') or '').split('#', 1)[0] == rapport:
            raise ValueError('%s hittade fyndet %s och kan inte verifiera rättelsen av det; en senare granskning gör det' % (rapport, meta['fynd']))
        meta['verifierad'] = rapport
        meta['verifierad_tid'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
        kropp = kropp.rstrip('\n') + '\n\n**Verifierad (%s):** %s%s\n' % (meta['verifierad_tid'][:10], rapport,
                                                                       (': ' + not_.strip()) if (not_ or '').strip() else '')
        skriv(meta, kropp)
    return meta


def main(argv=None):
    p = argparse.ArgumentParser(prog='backlog', description=__doc__.split('\n\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    n = sub.add_parser('ny')
    n.add_argument('--kalla', required=True)
    n.add_argument('--titel', required=True)
    n.add_argument('--varfor', required=True)
    for f in ('forslag', 'klart', 'steg', 'sar', 'kallref', 'fynd'):
        n.add_argument('--' + f)
    n.add_argument('--prio', default='normal')
    l = sub.add_parser('lista')
    l.add_argument('--status')
    l.add_argument('--json', action='store_true')
    v = sub.add_parser('visa')
    v.add_argument('id')
    s = sub.add_parser('status')
    s.add_argument('id')
    s.add_argument('status')
    s.add_argument('--commit')
    s.add_argument('--not', dest='not_')
    ve = sub.add_parser('verifiera')
    ve.add_argument('id')
    ve.add_argument('--rapport', required=True)
    ve.add_argument('--not', dest='not_')
    a = p.parse_args(argv)
    try:
        if a.cmd == 'ny':
            print(ny(a.kalla, a.titel, a.varfor, a.forslag, a.klart, a.steg, a.sar, a.kallref, a.prio, a.fynd))
        elif a.cmd == 'lista':
            poster = lista(a.status)
            if a.json:
                print(json.dumps([dict({k: v for k, v in x.items() if k != 'kropp'}, lage=lage(x)) for x in poster], ensure_ascii=False, indent=1))
            else:
                for x in poster:
                    print('%-22s %-10s %-6s %s  %s' % (lage(x), x.get('kalla'), x.get('prio'), x['id'], x['titel']))
                if not poster:
                    print('(inga poster)')
        elif a.cmd == 'visa':
            print((MAPP / (a.id + '.md')).read_text(encoding='utf-8'))
        elif a.cmd == 'status':
            m = satt_status(a.id, a.status, a.commit, a.not_)
            print('%s: %s' % (m['id'], lage(m)))
        elif a.cmd == 'verifiera':
            m = verifiera(a.id, a.rapport, a.not_)
            print('%s: %s' % (m['id'], lage(m)))
    except (ValueError, OSError) as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
