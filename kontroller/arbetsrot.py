#!/usr/bin/env python3
"""arbetsrot.py — helbyggets arbetsrot i kundrepot (R06; beställningen 2026-10-07 punkt 3 och 4, och 2026-10-08, 2A):
med växeln NWP_ARBETSROT=kundrepo startar kor.sh byggsessionen i kunder/<slug>/kundrepo, som skapandeflödets sessioner
(atelje.arbetsrot), med samma omvandling: motorns filer nås genom --add-dir och absoluta vägar, varje relativ regel blir
absolut, och sessionen skriver aldrig i kundrepot. Projektets krokar (stoppvakten och commitvakten i
.claude/settings.json) laddas bara från sessionens projekt; i kundrepot följer de därför med i --settings, med motorns
rot i stället för $CLAUDE_PROJECT_DIR. Standard är motorns rot tills ett verkligt sessionsprov visat vad Claude Code
laddar i kundrepots rot (kontroller/formagoprov.py).

    .venv/bin/python kontroller/arbetsrot.py rot <slug>       # arbetsroten: kundrepot med växeln och ett repo, annars motorns rot
    .venv/bin/python kontroller/arbetsrot.py bygge <slug>     # byggsessionens argument, NUL-avgränsade på stdin och stdout
    .venv/bin/python kontroller/arbetsrot.py prompt <slug>    # byggets uppdrag med absoluta vägar (stdin → stdout)

Ett kundrepo med egna Claude Code-inställningar (.claude/settings.json eller settings.local.json) används aldrig som
arbetsrot: de skulle laddas i sessionen (--setting-sources project,local). Slutkod 0, och 2 när något inte går.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atelje  # noqa: E402

REGELFLAGGOR = ('--allowedTools', '--disallowedTools')


def rot(slug):
    """(arbetsroten, i_kundrepo) för byggsessionen: samma val som skapandeflödets sessioner (atelje.arbetsrot)."""
    return atelje.arbetsrot(slug)


def motorns_krokar(rot_=None):
    """Krokarna ur motorns .claude/settings.json, med motorns rot i stället för $CLAUDE_PROJECT_DIR."""
    r = Path(rot_ or atelje.ROOT)
    d = json.loads((r / '.claude' / 'settings.json').read_text(encoding='utf-8'))
    return json.loads(json.dumps(d.get('hooks') or {}).replace('$CLAUDE_PROJECT_DIR', str(r)))


def bygge_args(slug, args):
    """Byggsessionens argument i kundrepot: absoluta regler, --add-dir med motorns rot, skrivförbud i kundrepot, och
    motorns krokar sammanslagna i --settings (före en sandlådas inställningar, som behålls; med sandlådan nekas också
    Bash skrivning i kundrepot)."""
    vag, i_kundrepo = rot(slug)
    if not i_kundrepo:
        return list(args)
    ut, flagga = [], None
    for a in args:
        if a.startswith('--'):
            flagga = a
            ut.append(a)
        elif flagga in REGELFLAGGOR:
            ut.append(atelje.regel_absolut(a))
        else:
            ut.append(a)
    i = ut.index('--disallowedTools') + 1
    ut[i:i] = ['%s(//%s/**)' % (v, str(vag).strip('/')) for v in ('Write', 'Edit')]
    krokar = motorns_krokar()
    if '--settings' in ut:
        j = ut.index('--settings') + 1
        d = json.loads(ut[j])
        for namn, poster in krokar.items():
            d.setdefault('hooks', {}).setdefault(namn, [])
            d['hooks'][namn] = poster + d['hooks'][namn]
        fs = (d.get('sandbox') or {}).get('filesystem')
        if isinstance(fs, dict):  # sandlådan skriver annars hela arbetskatalogen; kundrepot nekas också Bash och barnen
            fs['denyWrite'] = list(fs.get('denyWrite') or []) + [str(vag)]
        ut[j] = json.dumps(d, ensure_ascii=False)
    else:
        ut += ['--settings', json.dumps({'hooks': krokar}, ensure_ascii=False)]
    k = ut.index('--setting-sources') if '--setting-sources' in ut else 0
    ut[k:k] = ['--add-dir', str(atelje.ROOT)]
    return ut


def bygge_prompt(slug, text):
    vag, i_kundrepo = rot(slug)
    if not i_kundrepo:
        return text
    return atelje.text_absolut(text) + (
        '\n\nArbetskatalogen är kundens eget repo (%s) med dess korta CLAUDE.md; motorns skills, kunskap och verktyg ligger i '
        '%s. Varje relativ väg i skillen och kunskapen (kontroller/, underlag/, kunder/, kunskap/, .venv/ …) gäller den roten: '
        'skriv den absolut. Kundrepot skrivs aldrig i bygget; exporten lägger sajten där efteråt.' % (vag, atelje.ROOT))


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) != 2 or a[0] not in ('rot', 'bygge', 'prompt') or not atelje.SLUG.match(a[1]):
        print(__doc__.split('\n\n')[1], file=sys.stderr)
        return 2
    try:
        if a[0] == 'rot':
            print(rot(a[1])[0])
        elif a[0] == 'bygge':
            data = sys.stdin.buffer.read()
            args = [x.decode('utf-8') for x in data.split(b'\0')[:-1]] if data.endswith(b'\0') else []
            if not args:
                raise ValueError('inga argument på stdin')
            sys.stdout.buffer.write(b''.join(x.encode('utf-8') + b'\0' for x in bygge_args(a[1], args)))
        else:
            sys.stdout.write(bygge_prompt(a[1], sys.stdin.read()))
    except (OSError, ValueError, RuntimeError) as e:
        print('arbetsroten: %s: %s' % (type(e).__name__, str(e)[:300]), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
