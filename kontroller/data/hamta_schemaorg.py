#!/usr/bin/env python3
"""Hämtar schema.org:s vokabulär och skriver den kompakta formen som seo_kontroll.py prövar JSON-LD mot:
klasser med föräldrar, egenskaper med de typer de hör till, utgångna termer med ersättare och termer som ännu är
förslag (pending). Vokabulären är CC BY-SA 3.0 (LICENS-schemaorg.md). Körs för hand när schema.org släpper en ny
version; byggena och provet läser bara den sparade filen.

    .venv/bin/python kontroller/data/hamta_schemaorg.py
"""
import datetime
import json
import urllib.request
from pathlib import Path

URL = 'https://schema.org/version/latest/schemaorg-current-https.jsonld'
UT = Path(__file__).with_name('schemaorg.json')


def ider(v):
    v = v if isinstance(v, list) else [v] if v else []
    return sorted(x['@id'].removeprefix('schema:') for x in v if isinstance(x, dict) and str(x.get('@id', '')).startswith('schema:'))


def kompakt(graf):
    klasser, egenskaper, ersatt, pending = {}, {}, {}, []
    for x in graf:
        namn = str(x.get('@id', '')).removeprefix('schema:')
        typer = x.get('@type') if isinstance(x.get('@type'), list) else [x.get('@type')]
        if 'rdfs:Class' in typer:
            klasser[namn] = ider(x.get('rdfs:subClassOf'))
        elif 'rdf:Property' in typer:
            egenskaper[namn] = ider(x.get('schema:domainIncludes'))
        else:
            continue
        if x.get('schema:supersededBy'):
            ersatt[namn] = ', '.join(ider(x['schema:supersededBy']))
        if (x.get('schema:isPartOf') or {}).get('@id') == 'https://pending.schema.org':
            pending.append(namn)
    return {'klasser': klasser, 'egenskaper': egenskaper, 'ersatt': ersatt, 'pending': sorted(pending)}


def main():
    req = urllib.request.Request(URL, headers={'User-Agent': 'nortropic-webb-pro/hamta_schemaorg'})
    with urllib.request.urlopen(req, timeout=60) as r:
        graf = json.load(r)['@graph']
    data = {'kalla': URL, 'hamtad': datetime.date.today().isoformat(), 'licens': 'CC BY-SA 3.0, se LICENS-schemaorg.md'}
    data.update(kompakt(graf))
    UT.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
    print('%s: %d klasser, %d egenskaper, %d utgångna' % (UT.name, len(data['klasser']), len(data['egenskaper']), len(data['ersatt'])))


if __name__ == '__main__':
    main()
