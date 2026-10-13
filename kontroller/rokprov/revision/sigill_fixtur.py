"""Provnyckeln för sigillet (kontroller/sigill.py): en egen registrerad tempkatalog med godkannande.nyckel och
dashboard-nyckel, och miljön som pekar dit (NWP_GODKANNANDE_NYCKEL och NWP_AGARBEVIS). Proven använder aldrig ägarens
riktiga nyckel och stänger aldrig av kontrollen: godkännandena förseglas genom provets egen portal (ägartoken prövas mot
provets dashboard-nyckel), och ett prov som prövar terminalen tar bort NWP_AGARBEVIS för sin egen process."""
import atexit
import os
import secrets
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import korregister  # noqa: E402


def aktivera():
    """Sätter provnyckeln för processen och dess barn; samma katalog om den redan är satt. Ger katalogen."""
    if os.environ.get('NWP_GODKANNANDE_NYCKEL') and os.environ.get('NWP_AGARBEVIS'):
        return Path(os.environ['NWP_GODKANNANDE_NYCKEL']).parent
    d = Path(korregister.egen_tmp('nwp-sigill-', 'provnyckeln för sigillet')).resolve()
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
