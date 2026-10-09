#!/usr/bin/env python3
"""blindvakt.py — PreToolUse-krok för de blinda sessionerna (kompetens.BLINDA: skisskritiken och granskningens första
pass): varje läsning med Read, Glob eller Grep prövas när den görs, mot sessionens tillåtelselista (blindningens
beställning, B-20261007-blindningen-listan-i-kundens-underlag-galler-ock; GR-20261009-natt-omgranskning-codex).

    .venv/bin/python -B kontroller/blindvakt.py <tillåtelselista.json>     (läser krokens JSON på stdin)

Tillåtelselistan skrivs när sessionen startar (kandidater.blind_tillatet): de namngivna filerna och katalogerna som den
blinda sessionen får läsa, med absoluta vägar; allt annat nekas. Det som inte står på listan blir aldrig läsbart av att
det saknades vid starten: en fil som tillkommer under sessionen i kundens underlag, i kandidatens katalog eller i ateljén
nekas när den läses, om den inte ligger i en tillåten katalog. Vägen prövas efter realpath, så en länk i en tillåten
katalog till något utanför nekas. Glob och Grep tillåts bara med en väg i en tillåten katalog (utan väg söker de i hela
arbetskatalogen och nekas), och ett Glob-mönster får inte gå uppåt eller vara absolut.

Vakten stoppar en läsning utanför listan med slutkod 2 och skälet på stderr, och den stoppar också när den inte kan
pröva läsningen (listan saknas eller är trasig, ett okänt verktyg, egen frist) eller inte startar alls (kommandots
`|| exit 2`). Inom sessionens arbetskatalog är vaktens slutkod 2 den enda spärren: dontAsk nekar inte Read där, också
när Read inte står i --allowedTools (ett verkligt prov 2026-10-09 av en parallell session, Claude Code 2.1.290). Slår
Claude Codes egen tidsgräns för kroken till först räknas det som ett fel som inte blockerar, och läsningen går igenom.
Därför är krokens tidsgräns (KROK_FRIST) klart längre än vaktens egen frist (FRIST): vakten hinner alltid svara 2 själv.
En krok som hänger längre än KROK_FRIST (processen startar aldrig klart) släpper fortfarande igenom en läsning i
arbetskatalogen; det är en kvarstående begränsning som kräver ett verkligt sessionsprov (kontroller/formagoprov.py, S3)
och, om den ska stängas helt, blinda sessioner i en arbetskatalog utan något hemligt.
"""
import json
import os
import signal
import sys
from pathlib import Path

FRIST = 20  # vaktens egen frist: när den tar slut stoppas läsningen (slutkod 2)
KROK_FRIST = 60  # Claude Codes tidsgräns för kroken: klart över FRIST, annars kan en långsam vakt släppa igenom en läsning
VERKTYG = ('Read', 'Glob', 'Grep')
MATCH = 'Read|Glob|Grep'


def las_lista(fil):
    """{'filer': [...], 'kataloger': [...]} med upplösta absoluta vägar, eller ValueError."""
    d = json.loads(Path(fil).read_text(encoding='utf-8'))
    if not isinstance(d, dict) or not isinstance(d.get('filer'), list) or not isinstance(d.get('kataloger'), list):
        raise ValueError('tillåtelselistan har fel form')
    ut = {'filer': set(), 'kataloger': []}
    for nyckel in ('filer', 'kataloger'):
        for v in d[nyckel]:
            if not isinstance(v, str) or not os.path.isabs(v):
                raise ValueError('tillåtelselistan har en väg som inte är absolut')
            (ut['filer'].add if nyckel == 'filer' else ut['kataloger'].append)(os.path.realpath(v))
    return ut


def _upplost(v, cwd):
    v = os.path.expanduser(str(v))
    return os.path.realpath(v if os.path.isabs(v) else os.path.join(cwd, v))


def _i_katalog(p, kataloger):
    return any(p == k or p.startswith(k.rstrip(os.sep) + os.sep) for k in kataloger)


def provning(lista, anrop):
    """None när läsningen får göras, annars skälet."""
    namn = anrop.get('tool_name')
    inn = anrop.get('tool_input') if isinstance(anrop.get('tool_input'), dict) else {}
    cwd = anrop.get('cwd') if isinstance(anrop.get('cwd'), str) and os.path.isabs(anrop.get('cwd')) else None
    if namn not in VERKTYG:
        return 'blindvakten prövar bara Read, Glob och Grep (fick %s); anropet stoppas' % namn
    if namn == 'Read':
        v = inn.get('file_path')
        if not isinstance(v, str) or not v or (not os.path.isabs(v) and not cwd):
            return 'läsningen saknar en prövbar väg; den stoppas'
        p = _upplost(v, cwd)
        if p in lista['filer'] or _i_katalog(p, lista['kataloger']):
            return None
        return 'den blinda sessionen får inte läsa %s: den står inte på sessionens tillåtelselista' % v
    v = inn.get('path')
    if not isinstance(v, str) or not v:
        return '%s utan väg söker i hela arbetskatalogen; ange en tillåten katalog' % namn
    if not os.path.isabs(v) and not cwd:
        return '%s saknar en prövbar väg; den stoppas' % namn
    p = _upplost(v, cwd)
    if namn == 'Glob':
        monster = str(inn.get('pattern') or '')
        if os.path.isabs(monster) or '..' in Path(monster).parts or monster.startswith('~'):
            return 'Glob-mönstret får inte gå utanför vägen; det stoppas'
        if _i_katalog(p, lista['kataloger']):
            return None
    elif p in lista['filer'] or _i_katalog(p, lista['kataloger']):
        return None
    return 'den blinda sessionen får inte söka i %s: vägen står inte på sessionens tillåtelselista' % v


def krok(listfil, rot=None, timeout=KROK_FRIST):
    """Krokens post i --settings (PreToolUse) för en blind session. rot: motorns rot som absolut väg i kommandot, när
    sessionen har en annan arbetsrot (R06); annars $CLAUDE_PROJECT_DIR. Startar vakten inte, stoppas läsningen (exit 2).
    timeout måste vara klart längre än vaktens egen frist, så att vakten själv hinner stoppa läsningen."""
    if timeout < FRIST + 15:
        raise ValueError('krokens tidsgräns (%s s) måste vara klart längre än vaktens frist (%d s)' % (timeout, FRIST))
    bas = str(rot) if rot else '$CLAUDE_PROJECT_DIR'
    kommando = ('"%s/.venv/bin/python" -B "%s/kontroller/blindvakt.py" "%s" '
                "|| { echo 'blindvakten kunde inte pröva läsningen' >&2; exit 2; }") % (bas, bas, listfil)
    return {'matcher': MATCH, 'hooks': [{'type': 'command', 'timeout': timeout, 'command': kommando}]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    def frist_ute(*_):
        raise TimeoutError('vaktens frist (%d s) tog slut' % FRIST)
    try:
        signal.signal(signal.SIGALRM, frist_ute)
        signal.alarm(FRIST)
        lista = las_lista(argv[0])
        data = sys.stdin.read()
        if not data.strip():
            raise ValueError('tom indata')
        anrop = json.loads(data)
        if not isinstance(anrop, dict):
            raise ValueError('indata är inget objekt')
        skal = provning(lista, anrop)
        signal.alarm(0)
    except Exception as e:  # noqa: BLE001 — vakten stänger vid fel
        skal = 'blindvakten kunde inte pröva läsningen (%s: %s); den stoppas' % (type(e).__name__, str(e)[:200])
    if skal:
        print(skal, file=sys.stderr)
        return 2
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow',
                                             'permissionDecisionReason': 'blindvakten: vägen står på sessionens tillåtelselista'}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
