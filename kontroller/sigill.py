#!/usr/bin/env python3
"""sigill.py — sigillet över godkännandena och ägarens mandat (BESLUT.md, tilläggen 2026-10-13: "Yes, fix the things you
mention" och "Autonomous to build (Recommended)").

Ett godkännande som bygget litar på, och ett mandat för en release eller en aktivering, bär fältet sigill: HMAC-SHA256
(RFC 2104) med nyckeln i ~/.nortropic-hemligheter/webb-pro/godkannande.nyckel (32 slumpbyte, 0600, skapad vid det
första förseglade godkännandet) över en kanonisk JSON av fälten som binder posten. Utan nyckeln går ett sigill inte att
räkna fram, och godkand_giltig (kontroller/designfas.py och kontroller/skapande.py) och mandatens läsare prövar det med
hmac.compare_digest. En post utan sigill, eller med fel sigill, gäller aldrig.

Två slags avsändare sätter sigillet:
- Ägaren (forsegla_agaren): ägarens egen terminal, med en bekräftelse på /dev/tty där kommandot visar vad som godkänns
  och en kort slumpkod som ägaren skriver tillbaka, eller portalen, där anropet bär ägartoken (dashboardnyckeln, som
  bara ägarens webbläsare och Nortropic.app får; dashboard/server.py). Utan styrande terminal, och inifrån en Claude
  Code-session (CLAUDECODE), nekas terminalvägen. Kontrollen ligger här, i funktionen som sätter sigillet, så att ett
  anrop med python -c inte går runt den. Ägaren förseglar designgodkännanden, kandidatvägens godkännanden och
  mandaten för release och aktivering.
- Den autonoma godkännaren (forsegla_autonomt): bara designfasens godkännande (designfas.autogodkann, som prövar
  grinden först), utan terminal, av den Python-process som anropar den. Den förseglar aldrig ett mandat.

Gränsen: nyckeln skyddas av att flödets sessioner nekas hemlighetsmappen (nekanden(): Read, Edit, Write och
Bash-mönster; sandlådorna i kontroller/sandlada.py och processgrans.py nekar läsningen på processnivå). Claude Codes
nekanden gäller verktygen; en process som användaren kör med obegränsad Python kan läsa filen och räkna ett sigill.

NWP_GODKANNANDE_NYCKEL pekar om nyckelfilen i proven; portalens ägartoken prövas då mot dashboard-nyckel i samma
katalog, och NWP_AGARBEVIS bär ägartoken i provens processer. En provnyckel gäller aldrig ägarens kunder i
huvudutcheckningen (~/nortropic-repos/nortropic-webb-pro/underlag och kunder).

    .venv/bin/python kontroller/sigill.py agaren --vad TEXT     ägarens bekräftelse i terminalen (kor.sh:s nödväg)
"""
import argparse
import contextlib
import contextvars
import hashlib
import hmac
import json
import os
import pwd
import secrets
import select
import sys
from pathlib import Path

HEM = Path(pwd.getpwuid(os.getuid()).pw_dir)  # inte $HOME: en ändrad miljö flyttar aldrig nyckeln eller huvudutcheckningen
KATALOG = HEM / '.nortropic-hemligheter' / 'webb-pro'
NYCKELFIL = KATALOG / 'godkannande.nyckel'
DASHBOARDNYCKEL = 'dashboard-nyckel'  # portalens ägartoken (dashboard/server.py NYCKELFIL), i samma katalog som nyckeln
HUVUD = HEM / 'nortropic-repos' / 'nortropic-webb-pro'
AGARENS = ('designfas', 'kandidat', 'release', 'aktivering')
AUTONOMA = ('designfas',)  # den autonoma godkännaren förseglar aldrig ett mandat för release eller aktivering
KOD_TECKEN = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
SVARSTID = 300
PORTAL = contextvars.ContextVar('nwp_portal_agartoken', default=None)  # sätts av dashboard/server.py per skrivande anrop


class Nekad(Exception):
    pass


def nyckelfil():
    return Path(os.environ.get('NWP_GODKANNANDE_NYCKEL') or NYCKELFIL)


def provnyckel():
    return bool(os.environ.get('NWP_GODKANNANDE_NYCKEL'))


def vakt(vag):
    """En provnyckel gäller aldrig ägarens kunder: underlag/ och kunder/ i huvudutcheckningen."""
    if not provnyckel() or vag is None:
        return
    p = Path(vag).resolve()
    for d in (HUVUD / 'underlag', HUVUD / 'kunder'):
        if p == d.resolve() or p.is_relative_to(d.resolve()):
            raise Nekad('provnyckeln (NWP_GODKANNANDE_NYCKEL) gäller aldrig ägarens kunder i huvudutcheckningen')


def nyckel(skapa=False):
    """Nyckeln (32 byte), eller None när den inte finns och skapa är falskt. Skapas med 0600 i en katalog med 0700;
    en länk följs aldrig, och en fil med fel storlek eller rättigheter för andra godtas inte."""
    f = nyckelfil()
    try:
        fd = os.open(f, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        if not skapa:
            return None
        f.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        except FileExistsError:
            return nyckel(False)
        with os.fdopen(fd, 'wb') as h:
            h.write(secrets.token_bytes(32))
        os.chmod(f, 0o600)
        return nyckel(False)
    except OSError as e:
        raise Nekad('nyckelfilen %s kunde inte läsas (%s)' % (f, e.strerror or e))
    with os.fdopen(fd, 'rb') as h:
        b = h.read(65)
        st = os.fstat(h.fileno())
    if st.st_mode & 0o077:
        raise Nekad('nyckelfilen %s är läsbar för andra; rättigheterna ska vara 0600' % f)
    if len(b) != 32:
        raise Nekad('nyckelfilen %s ska vara 32 byte' % f)
    return b


def kanonisk(falt):
    return json.dumps(falt, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def _berakna(slag, falt, k):
    return hmac.new(k, b'nwp-sigill/1\n' + slag.encode() + b'\n' + kanonisk(falt), hashlib.sha256).hexdigest()


def prova(slag, falt, sigill, vag=None):
    """(giltigt, skäl) för ett sigill över fälten."""
    try:
        vakt(vag)
        k = nyckel()
    except Nekad as e:
        return False, str(e)
    if not sigill:
        return False, 'posten saknar sigill: bara ägaren (terminalen eller portalen) eller den autonoma godkännaren förseglar ett %s' % NAMN.get(slag, slag)
    if not k:
        return False, 'nyckeln saknas (%s): inget förseglat %s finns ännu' % (nyckelfil(), NAMN.get(slag, slag))
    if not isinstance(sigill, str) or not hmac.compare_digest(sigill, _berakna(slag, falt, k)):
        return False, 'sigillet stämmer inte: posten är inte förseglad av ägaren eller den autonoma godkännaren, eller ändrad efteråt'
    return True, 'förseglat'


NAMN = {'designfas': 'designgodkännande', 'kandidat': 'godkännande', 'release': 'mandat för release',
        'aktivering': 'mandat för aktivering'}


@contextlib.contextmanager
def portal(token):
    t = PORTAL.set(token)
    try:
        yield
    finally:
        PORTAL.reset(t)


def portal_ok(token):
    """Ägartoken mot dashboard-nyckel i nyckelns katalog (compare_digest)."""
    try:
        fil = (nyckelfil().parent / DASHBOARDNYCKEL).read_text(encoding='utf-8').strip()
    except OSError:
        return False
    return bool(fil) and hmac.compare_digest(str(token).strip().encode(), fil.encode())


def bekrafta_terminal(visning):
    """Ägarens bekräftelse i hans egen terminal: vad som godkänns och en slumpkod skrivs på /dev/tty, och ägaren skriver
    tillbaka koden. Nekas inifrån en Claude Code-session och utan styrande terminal."""
    if os.environ.get('CLAUDECODE'):
        raise Nekad('det här kräver ägarens egen terminal: inifrån en Claude Code-session (CLAUDECODE) godkänns ingenting')
    try:
        fd = os.open('/dev/tty', os.O_RDWR)
    except OSError:
        raise Nekad('det här kräver ägarens egen terminal: processen har ingen styrande terminal (/dev/tty)')
    try:
        kod = ''.join(secrets.choice(KOD_TECKEN) for _ in range(6))
        text = '\n'.join(['', '== Ägarens bekräftelse =='] + ['  ' + str(r) for r in visning] +
                         ['', 'Skriv koden %s och tryck retur för att bekräfta (annat avbryter): ' % kod])
        os.write(fd, text.encode('utf-8'))
        svar = b''
        while not svar.endswith(b'\n') and len(svar) < 64:
            r, _, _ = select.select([fd], [], [], SVARSTID)
            if not r:
                raise Nekad('ingen bekräftelse i terminalen inom %d sekunder; inget godkändes' % SVARSTID)
            b = os.read(fd, 64)
            if not b:
                break
            svar += b
        if not hmac.compare_digest(svar.decode('utf-8', 'replace').strip().upper().encode(), kod.encode()):
            os.write(fd, b'Koden stammer inte; inget godkandes.\n')
            raise Nekad('koden i terminalen stämde inte; inget godkändes')
        os.write(fd, b'Bekraftat.\n')
        return 'terminalen'
    finally:
        os.close(fd)


def agarkanal(visning):
    """'portalen' när anropet bär ägartoken (PORTAL, eller NWP_AGARBEVIS i provens processer), annars 'terminalen' efter
    bekräftelsen på /dev/tty. Nekad när ingen av dem håller."""
    token = PORTAL.get() or os.environ.get('NWP_AGARBEVIS')
    if token:
        if portal_ok(token):
            return 'portalen'
        raise Nekad('portalens ägartoken stämmer inte med %s; starta om dashboarden med ./dashboard.sh' % (nyckelfil().parent / DASHBOARDNYCKEL))
    return bekrafta_terminal(visning)


def forsegla_agaren(slag, falt, vag, visning):
    """Ägarens sigill: ägarens kanal först (agarkanal), sedan HMAC med nyckeln, som skapas vid behov. Ger (sigill, kanal)."""
    if slag not in AGARENS:
        raise Nekad('okänt slag %r' % slag)
    vakt(vag)
    kanal = agarkanal(visning)
    return _berakna(slag, falt, nyckel(skapa=True)), kanal


def forsegla_autonomt(slag, falt, vag):
    """Den autonoma godkännarens sigill: bara designfasens godkännande, efter grinden i designfas.autogodkann."""
    if slag not in AUTONOMA:
        raise Nekad('den autonoma godkännaren förseglar bara designfasens godkännande, aldrig %s' % NAMN.get(slag, slag))
    vakt(vag)
    return _berakna(slag, falt, nyckel(skapa=True))


def nekanden(hem=None):
    """Nekandena för flödets sessioner: hemlighetsmappen med nyckeln och portalens ägartoken (Read, Edit, Write och
    Bash-mönster som nämner den, nyckelfilen eller provens variabler)."""
    h = str(hem or HEM).strip('/')
    ut = ['%s(//%s/.nortropic-hemligheter/**)' % (v, h) for v in ('Read', 'Edit', 'Write')]
    ut += ['Bash(*nortropic-hemligheter*)', 'Bash(*godkannande.nyckel*)', 'Bash(*dashboard-nyckel*)', 'Bash(*NWP_GODKANNANDE_NYCKEL*)',
           'Bash(*NWP_AGARBEVIS*)']
    return ut


def main(argv=None):
    p = argparse.ArgumentParser(prog='sigill', description=__doc__.split('\n\n')[0])
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('agaren', help='ägarens bekräftelse i terminalen (eller portalens ägartoken); slutkod 0 bekräftat, 2 nekat')
    a.add_argument('--vad', required=True)
    x = p.parse_args(argv)
    try:
        print('bekräftat i %s' % agarkanal([x.vad]))
    except Nekad as e:
        print('sigill: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
