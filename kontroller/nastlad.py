#!/usr/bin/env python3
"""nastlad.py — miljön för en nästlad Claude-session (granskarna, ateljén, prototypen, brevet, prospektjobben,
grupperingen och referenstjänsterna).

En egen session ärver inga variabler från en omgivande Claude-session eller från bygget (NWP_SLUG väcker stoppvakten),
och skriver aldrig i ägarens automatiska minne (~/.claude/memory): prototypens skapare skrev 2026-10-05 om ägarens
minnesindex och lade till ett felaktigt minne, eftersom Claude Code har automatiskt minne på i varje session som inte
stänger av det (CLAUDE_CODE_DISABLE_AUTO_MEMORY, Claude Code 2.1.280).
"""
import os

AV = {'CLAUDE_CODE_DISABLE_AUTO_MEMORY': '1'}


API = ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL')  # de nästlade sessionerna går på prenumerationen


def miljo(bas=None, behall=None):
    """bas (os.environ) utan CLAUDECODE, CLAUDE_CODE_* och NWP_* (utom det behall(k) godtar), med automatiskt minne av.
    API-nyckel, token och bas-URL följer aldrig med: en nästlad session byter aldrig själv till API-debitering (ägarens
    uppdrag 2026-10-05 16:25Z, punkt 7)."""
    bas = os.environ if bas is None else bas
    return {k: v for k, v in bas.items()
            if k not in API and ((behall and behall(k)) or (k != 'CLAUDECODE' and not k.startswith(('CLAUDE_CODE_', 'NWP_'))))} | AV
