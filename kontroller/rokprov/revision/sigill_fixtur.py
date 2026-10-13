"""Provnyckeln för sigillet (kontroller/sigill.py): en egen registrerad tempkatalog med godkannande.nyckel och
dashboard-nyckel, och miljön som pekar dit (NWP_GODKANNANDE_NYCKEL och NWP_AGARBEVIS). Proven använder aldrig ägarens
riktiga nyckel och stänger aldrig av kontrollen: godkännandena förseglas genom provets egen portal (ägartoken prövas mot
provets dashboard-nyckel), och ett prov som prövar terminalen tar bort NWP_AGARBEVIS för sin egen process."""
import atexit
import os
import secrets
import shutil
from pathlib import Path



def _korregister():
    """korregister ur repots kontroller/, laddat under ett eget namn: sys.path rörs inte, så ett prov som kör en kopia av
    repot (KOPIA/kontroller först på sys.path) får fortfarande kopians moduler."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('_sigill_fixtur_korregister', Path(__file__).resolve().parents[2] / 'korregister.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def aktivera():
    """Sätter provnyckeln för processen och dess barn; samma katalog om den redan är satt. Ger katalogen."""
    if os.environ.get('NWP_GODKANNANDE_NYCKEL') and os.environ.get('NWP_AGARBEVIS'):
        return Path(os.environ['NWP_GODKANNANDE_NYCKEL']).parent
    d = Path(_korregister().egen_tmp('nwp-sigill-', 'provnyckeln för sigillet')).resolve()
    atexit.register(shutil.rmtree, str(d), True)
    n = d / 'godkannande.nyckel'
    fd = os.open(n, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as h:
        h.write(secrets.token_bytes(32))
    token = secrets.token_urlsafe(24)
    fd = os.open(d / 'dashboard-nyckel', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as h:
        h.write(token + '\n')
    os.environ['NWP_GODKANNANDE_NYCKEL'] = str(n)
    os.environ['NWP_AGARBEVIS'] = token
    return d


def utan_terminal(fn, utan_agartoken=True):
    """fn() i en gaffel av provets process som har lämnat sin styrande terminal (setsid), utan ägartoken: så som bandets
    drivare eller en session kör, oavsett om provet startats i en terminal. Provets attrapper och sökvägar följer med i
    gaffeln. Ger ('ok', repr av värdet) eller (felets klass, text)."""
    import json as _json
    import traceback
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:  # barnet
        try:
            os.close(r)
            os.setsid()
            if utan_agartoken:
                os.environ.pop('NWP_AGARBEVIS', None)
            os.environ.pop('CLAUDECODE', None)
            try:
                ut = ('ok', repr(fn())[:2000])
            except BaseException as e:  # noqa: BLE001 — utfallet går till föräldern
                ut = (type(e).__name__, str(e)[:2000] or traceback.format_exc()[-800:])
            os.write(w, _json.dumps(ut).encode())
        finally:
            os._exit(0)
    os.close(w)
    data = b''
    while True:
        b = os.read(r, 65536)
        if not b:
            break
        data += b
    os.close(r)
    os.waitpid(pid, 0)
    return tuple(_json.loads(data or b'["inget svar", ""]'))


def miljo():
    """Provnyckelns variabler, för ett prov som startar kor.sh eller ett verktyg med en egen, rensad miljö."""
    aktivera()
    return {k: os.environ[k] for k in ('NWP_GODKANNANDE_NYCKEL', 'NWP_AGARBEVIS')}


def forsegla_kandidat(slug, g, underlag_slug):
    """Ägarens sigill på en provfixtur av kandidatvägens godkännande (VINNARE.json: godkand), satt genom provets egen
    portal precis som atelje.godkannande sätter det; g får fälten sigill och kanal. underlag_slug: underlag/<slug>."""
    import sigill
    import skapande
    aktivera()
    g['sigill'], g['kanal'] = sigill.forsegla_agaren('kandidat', skapande.sigillfalt_kandidat(slug, g), underlag_slug, ['provfixtur'])
    return g
