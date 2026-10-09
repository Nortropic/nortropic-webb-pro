#!/usr/bin/env python3
"""nastlad.py — miljön för en nästlad Claude-session (granskarna, ateljén, prototypen, brevet, prospektjobben,
grupperingen och referenstjänsterna).

En egen session ärver inga variabler från en omgivande Claude-session eller från bygget (NWP_SLUG väcker stoppvakten),
och skriver aldrig i ägarens automatiska minne (~/.claude/memory): prototypens skapare skrev 2026-10-05 om ägarens
minnesindex och lade till ett felaktigt minne, eftersom Claude Code har automatiskt minne på i varje session som inte
stänger av det (CLAUDE_CODE_DISABLE_AUTO_MEMORY, Claude Code 2.1.280).
"""
import os
import signal
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

AV = {'CLAUDE_CODE_DISABLE_AUTO_MEMORY': '1'}


API = ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL')  # de nästlade sessionerna går på prenumerationen


# Provläget (Dyad-provet, ägarens uppdrag 2026-10-09, steg 2): en nästlad session mot den falska modellen i
# kontroller/falsk_modell.py, aldrig i drift. Det gäller bara när båda variablerna är satta, adressen är en lokal
# http-adress med port, nyckeln är en provnyckel och repots rot inte är huvudutcheckningen. Är en variabel satt utan att
# villkoren håller stoppas sessionen (ProvlageFel), så att ett prov aldrig tyst går mot prenumerationen och drift aldrig
# mot en falsk modell.
PROV_URL, PROV_NYCKEL, PROV_PREFIX = 'NWP_FALSK_MODELL', 'NWP_FALSK_NYCKEL', 'sk-ant-prov-'
HUVUD = (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve()  # drift: huvudutcheckningen


class ProvlageFel(RuntimeError):
    pass


def provlage(bas=None, rot=None):
    """Den falska modellens miljö (bas-URL, provnyckel, inget icke nödvändigt nätverk) eller None utan provläge."""
    bas = os.environ if bas is None else bas
    url, nyckel = str(bas.get(PROV_URL) or ''), str(bas.get(PROV_NYCKEL) or '')
    if not url and not nyckel:
        return None
    skal = []
    try:
        u = urlsplit(url)
        lokal = u.scheme == 'http' and u.hostname in ('127.0.0.1', 'localhost') and bool(u.port)
    except ValueError:
        lokal = False
    if not lokal:
        skal.append('%s är ingen lokal http-adress med port' % PROV_URL)
    if not nyckel.startswith(PROV_PREFIX) or len(nyckel) < len(PROV_PREFIX) + 8:
        skal.append('%s är ingen provnyckel (%s…)' % (PROV_NYCKEL, PROV_PREFIX))
    try:
        drift = rot is None or Path(rot).resolve() == HUVUD
    except OSError:
        drift = True
    if drift:
        skal.append('repots rot är huvudutcheckningen eller okänd: provläget gäller aldrig i drift')
    if skal:
        raise ProvlageFel('provläget gäller bara i prov: ' + '; '.join(skal))
    return {'ANTHROPIC_BASE_URL': url, 'ANTHROPIC_API_KEY': nyckel, 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
            'DISABLE_TELEMETRY': '1'}


def miljo(bas=None, behall=None, rot=None):
    """bas (os.environ) utan CLAUDECODE, CLAUDE_CODE_* och NWP_* (utom det behall(k) godtar), med automatiskt minne av.
    API-nyckel, token och bas-URL följer aldrig med: en nästlad session byter aldrig själv till API-debitering (ägarens
    uppdrag 2026-10-05 16:25Z, punkt 7). Det enda undantaget är provläget (provlage, rot är repots rot), som pekar
    sessionen mot den falska modellen med en provnyckel."""
    bas = os.environ if bas is None else bas
    prov = provlage(bas, rot)
    return {k: v for k, v in bas.items()
            if k not in API and ((behall and behall(k)) or (k != 'CLAUDECODE' and not k.startswith(('CLAUDE_CODE_', 'NWP_'))))} | AV | (prov or {})


def efterkommande(pid):
    """Alla ättlingar till pid, hittade via ppid: också de som ligger i egna processgrupper (Claude Code kör varje
    Bash-kommando i en egen grupp, så förhandsvisningen, npm och node nås inte av en killpg på sessionens grupp)."""
    try:
        out = subprocess.run(['ps', '-A', '-o', 'pid=,ppid='], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    barn = {}
    for rad in out.splitlines():
        d = rad.split()
        if len(d) == 2 and d[0].isdigit() and d[1].isdigit():
            barn.setdefault(int(d[1]), []).append(int(d[0]))
    ut, ko = [], [int(pid)]
    while ko:
        for c in barn.get(ko.pop(), []):
            if c not in ut:
                ut.append(c)
                ko.append(c)
    return ut


def lever(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def ar_session(pid):
    """Är pid en nästlad Claude-session ur flödet (claude -p med flödets flaggor)? Ett pid ur en äldre körning kan ha
    återanvänts av en annan process; den avslutas aldrig."""
    try:
        c = subprocess.run(['ps', '-o', 'command=', '-p', str(int(pid))], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        return False
    return 'claude' in c and ' -p ' in c + ' ' and '--allowedTools' in c


def doda_trad(pid):
    """Avslutar en process och alla dess ättlingar med SIGKILL. Ättlingarna listas före det första stoppet, så att ingen
    hinner byta förälder. Ger de avslutade pid:en (granskning 3, S3: tidsgränsen och avbrottet når underprocesserna)."""
    if not pid or not lever(pid):
        return []
    alla = [int(pid)] + efterkommande(pid)
    for x in alla:
        try:
            os.kill(x, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    return alla
