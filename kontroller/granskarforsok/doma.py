"""Blind domare för granskarförsöket: en annan modell (Sonnet) matchar varje fynd mot ägarens facit och märker resten
verkligt eller falskt. Varje granskning döms två gånger med fynden i olika slumpad ordning och nya id; domaren vet
aldrig armen. Återupptagbart: redan dömda hoppas över.
"""
import json
import os
import random
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HEM = str(Path.home())
REPOS = str(Path(__file__).resolve().parents[3])  # mappen med repona: granskaren och domaren får inte läsa där
G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok')  # utdata, utanför repot
KOD = Path(__file__).resolve().parent
FACIT = json.loads((KOD / 'facit.json').read_text(encoding='utf-8'))
PARALLELLT = int(sys.argv[1]) if len(sys.argv) > 1 else 6
SCHEMA = {
    'type': 'object', 'required': ['bedomningar'], 'additionalProperties': False,
    'properties': {'bedomningar': {'type': 'array', 'items': {
        'type': 'object', 'required': ['fynd', 'facit', 'verkligt', 'skal'], 'additionalProperties': False,
        'properties': {'fynd': {'type': 'string'}, 'facit': {'type': 'array', 'items': {'type': 'string'}},
                       'verkligt': {'type': 'boolean'}, 'skal': {'type': 'string'}}}}}}
NEKAS = ['Write', 'Edit', 'NotebookEdit', 'WebFetch', 'WebSearch', 'Task', 'Bash',
         'Read(/' + REPOS + '/**)', 'Read(/' + HEM + '/.claude/**)']


def fynd_i(g):
    ut = []
    for b in g.get('blockerande') or []:
        ut.append(('blockerande', '[blockerande, grad %s, %s] Var: %s. Observation: %s Konsekvens: %s Rättning: %s' % (
            b.get('allvarlighet'), b.get('kriterium'), b.get('var'), b.get('observation'), b.get('konsekvens'), b.get('rattning'))))
    for f in g.get('forbattringar') or []:
        ut.append(('forbattring', '[förbättring] %s' % f))
    return ut


def ren_miljo():
    env = {k: v for k, v in os.environ.items() if not (k == 'CLAUDECODE' or k.startswith('CLAUDE_CODE_') or k.startswith('NWP_'))}
    return env


def doma(rdir, slug, omgang):
    ut = rdir / ('DOM-%d.json' % omgang)
    if ut.is_file():
        return
    g = json.loads((rdir / 'GRANSKNING.json').read_text(encoding='utf-8'))
    fynd = fynd_i(g)
    ordning = list(range(len(fynd)))
    random.Random('%s-%s-%d' % (slug, rdir.name, omgang)).shuffle(ordning)
    karta = {'f%d' % (i + 1): j for i, j in enumerate(ordning)}
    facit = '\n'.join('- %s: %s' % (f['id'], f['fel']) for f in FACIT[slug])
    lista = '\n'.join('- %s: %s' % (fid, fynd[j][1]) for fid, j in karta.items())
    prompt = f"""Du är domare i ett försök med granskare av webbplatser. Sajten är {slug}, byggd åt en riktig verksamhet.

Ägarens facit, felen ägaren själv hittade på sajten:
{facit}

Fynd från en granskning av samma sajt, i slumpad ordning. Du vet inte vilken granskare eller vilken metod de kommer
från, och det spelar ingen roll.
{lista}

Bedöm varje fynd för sig:
1. `facit`: id för de facitfel fyndet pekar ut, alltså samma problem på samma ställe eller med samma orsak. Ett
   allmänt fynd som bara nuddar ett facitfel räknas inte; ett fynd kan peka ut flera facitfel. Tom lista om inget.
2. `verkligt`: är fyndet ett verkligt problem på sajten som en kunnig ägare skulle vilja rätta? Falskt betyder att
   påståendet inte stämmer, eller att det är smak och inget fel. När du är osäker: titta i skärmbilderna i
   kunder/{slug}/prov/inspektion/<sida>/ (vy-390-ruta-NN.png, vy-1440-ruta-NN.png) eller i sidornas HTML i
   kunder/{slug}/sajt/dist/.
3. `skal`: en mening.

Svara med en bedömning per fynd, med fyndets id (f1, f2 …)."""
    args = ['claude', '-p', '--max-turns', '40', '--permission-mode', 'dontAsk', '--output-format', 'json',
            '--setting-sources', 'project,local', '--strict-mcp-config', '--model', 'sonnet',
            '--json-schema', json.dumps(SCHEMA), '--allowedTools', 'Read', 'Glob', 'Grep', '--disallowedTools', *NEKAS]
    start = time.time()
    r = subprocess.run(args, input=prompt.encode(), capture_output=True, cwd=str(G / slug / 'rot'), env=ren_miljo(), timeout=1800)
    try:
        svar = json.loads(r.stdout.decode())
        res = svar['structured_output']
        res['karta'] = karta
        res['fynd'] = [{'typ': t, 'text': x} for t, x in fynd]
        res['session'] = {k: svar.get(k) for k in ('num_turns', 'duration_ms', 'total_cost_usd', 'usage', 'modelUsage')}
        ut.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
        status = 'klar'
    except Exception as e:  # noqa: BLE001
        status = 'FEL %s %s' % (type(e).__name__, (r.stderr or r.stdout).decode(errors='replace')[-300:])
    with open(G / 'logg-doma.txt', 'a') as f:
        f.write('%s %s %s %s %d %.0f s\n' % (time.strftime('%H:%M:%S', time.gmtime()), status, slug, rdir.name, omgang, time.time() - start))


def main():
    jobb = []
    for slug in FACIT:
        for rdir in sorted((G / slug / 'rot' / 'kunder' / slug / 'ab-granskare').glob('*')):
            if (rdir / 'GRANSKNING.json').is_file():
                jobb += [(rdir, slug, 1), (rdir, slug, 2)]
    with ThreadPoolExecutor(PARALLELLT) as ex:
        list(ex.map(lambda j: doma(*j), jobb))


if __name__ == '__main__':
    main()
