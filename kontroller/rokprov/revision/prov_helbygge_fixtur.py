"""Syntetisk helbyggarsession för prov som prövar andra beteenden.

Skriver bara i provets uttryckliga hem och kundkatalog. Kompetensgrinden och
observatören används oförändrade; inga riktiga modell- eller MCP-anrop görs.
"""
import json
import os
from pathlib import Path
import subprocess
import uuid

KOMPETENS_FIXTUR = r'''
import json, os, sys
from pathlib import Path
root, hem, slug, sid = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
sys.path.insert(0, str(root / 'kontroller'))
import kompetens, bildkedja
roller = kompetens.for_pass('helbygge')
skills, _ = kompetens.aktiverbara([f for r in roller for f in r['karna']])
steg = [('Skill', {'skill': bildkedja.skillkommando(s) or s}) for s in skills]
steg += [('Read', {'file_path': str(root / f)}) for f in kompetens.lasfiler('helbygge')]
steg += [('Write', {'file_path': str(root / 'kunder' / slug / 'sajt/src/pages/index.astro')})]
rader = []
for i, (namn, inp) in enumerate(steg):
    rader.append({'type':'assistant','message':{'content':[{'type':'tool_use','id':str(i),'name':namn,'input':inp}]}})
    rader.append({'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':str(i),'content':'syntetiskt kompetensbevis'}]}})
p = hem / '.claude/projects/prov'; p.mkdir(parents=True, exist_ok=True)
(p / (sid + '.jsonl')).write_text('\n'.join(json.dumps(x) for x in rader) + '\n')
print(json.dumps({'type':'system','subtype':'init','session_id':sid}))
'''


def skapa_bevis(rot, hem, kund, korning, python):
    rot, hem, kund = Path(rot), Path(hem), Path(kund)
    sid = str(uuid.uuid4())
    start = kund / 'korningar' / korning / 'START.json'
    fore = json.loads(start.read_text()) if start.is_file() else {}
    start.parent.mkdir(parents=True, exist_ok=True)
    start.write_text(json.dumps(dict(fore, korning=korning, session_id=sid)))
    logg = kund / ('korning-%s.jsonl' % korning)
    rader = []
    if logg.is_file():
        for rad in logg.read_text().splitlines():
            try:
                d = json.loads(rad)
            except ValueError:
                rader.append(rad); continue
            if isinstance(d, dict) and d.get('type') == 'system' and d.get('subtype') == 'init':
                continue
            if isinstance(d, dict) and d.get('type') == 'result':
                d['session_id'] = sid
            rader.append(json.dumps(d))
    env = dict(os.environ, HOME=str(hem))
    r = subprocess.run([str(python), '-B', '-c', KOMPETENS_FIXTUR, str(rot), str(hem), kund.name, sid],
                       capture_output=True, text=True, timeout=30, env=env)
    assert r.returncode == 0, r.stderr
    if not any(isinstance(d, dict) and d.get('type') == 'result' for d in (json.loads(x) for x in rader)):
        rader.append(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'session_id': sid}))
    logg.write_text(r.stdout + '\n'.join(rader) + '\n')
    return env
