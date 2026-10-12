#!/usr/bin/env python3
"""Kompetenskartan (ägarens tillägg 2026-10-11; kontroller/kompetenskarta.py): kartan ur den riktiga metodkartan och de
installerade skillsen, med syntetiska kompetenskvitton i en isolerad underlagskatalog.

- tilldelningen: stegen i flödets ordning täcker varje pass, varje roll och varje fil i blocken finns med;
- skillsen: varje installerad skill har en plats, och en ny skill utan roll eller skäl blir en lucka (samma regel som
  startkontrollens rad "skills utan roll eller skäl", kompetens.skillstatus);
- det observerade: kvittona från kandidaternas STATUS.json, FORSKNING.json och KRITIK.json (båda passen) räknas per
  roll med kvittots egna tillståndsord; kärnan läst delvis, ett blockerat anrop, ett MCP-krav utan resultat och ett
  tilldelat verktyg som inte användes blir luckor med källa;
- varje kvittokälla en gång: förberedelsen, planeringen med kompletteringen och omplaneringen, fördjupningens uppdrag,
  förbättringsrundan, före/efter och helbyggets slutpost räknas, och ett kvitto som står i två filer räknas en gång;
- utan kvitton står stegen som inte observerade, aldrig som inte gjorda.

    .venv/bin/python -B kontroller/rokprov/revision/prov_kompetenskarta.py
"""
import contextlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import andringar  # noqa: E402
import kompetens  # noqa: E402
import korregister  # noqa: E402
import kompetenskarta  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
T = kompetens.TILLSTAND


def kvitto(pass_, lasta_hela=True, mcp=None, verktyg=None, skill_anrop=()):
    """Ett kvitto i kompetens.kvitto:s form, med tillståndet per roll räknat av kompetens.tillstand (samma som flödet).
    Varje MCP-anrop fick ett svar med innehåll (observatörens utfall), som ett lyckat anrop i en verklig session."""
    k = kompetens.tolka()
    roller = kompetens.for_pass(pass_, k)
    karna = sorted({kompetens.vag(f) for x in roller for f in x['karna']})
    kv = {'verifierad': True, 'ofullstandig': False, 'sessioner': {'forvantade': 1, 'sedda': 1, 'saknade': []},
          'lasta': karna if lasta_hela else karna[:1], 'saknas': [] if lasta_hela else karna[1:], 'fore_forsta_andring': karna,
          'valda': [], 'skill_anrop': list(skill_anrop), 'skill_fel': [], 'mcp_anrop': mcp or {},
          'mcp_utfall': {a: {'anrop lyckades': n} for a, n in (mcp or {}).items()}, 'verktyg_anrop': verktyg or {}}
    kv['tillstand'] = kompetens.tillstand(kv, pass_, k)
    return kv


class Kompetenskartan(unittest.TestCase):
    def setUp(self):
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.tmpdir = Path(stack.enter_context(korregister.egen_tmp_med('nwp-kompetenskarta-', 'kompetenskartans prov')))
        self.underlag = self.tmpdir / 'underlag'
        self.underlag.mkdir()
        self.kunder = self.tmpdir / 'kunder'  # helbyggenas slutposter; aldrig repots egna kunder/

    def skriv(self, rel, data):
        p = self.underlag / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def test_01_tilldelningen_i_flodets_ordning(self):
        d = kompetenskarta.karta(ROOT, self.underlag, self.kunder)
        self.assertEqual(sorted(s['pass'] for s in d['steg']), sorted(kompetens.PASS), 'varje pass är ett steg, en gång')
        self.assertEqual([s['pass'] for s in d['steg']][:3], ['forbered', 'forska', 'planera'])
        k = kompetens.tolka()
        self.assertEqual(set(d['roller']), set(k))
        filer = {f['fil'] for f in d['filer']}
        self.assertEqual(filer, {f for x in k.values() for f in x['karna'] + x['efter'] + x['valj']})
        for f in d['filer']:  # varje fil har sina roller med rätt slag
            for roll, slag in f['roller'].items():
                self.assertIn(f['fil'], k[roll]['karna'] if slag == 'karna' else k[roll]['efter'] if slag == 'efter' else k[roll]['valj'])
        # guidens ordning (ägarens besked 2026-10-12): Emils granskning är skissens krav efter renderingen, inte ett alternativ
        self.assertEqual(d['filer'][[f['fil'] for f in d['filer']].index('emil-review-animations/SKILL.md')]['roller'].get('rorelseskiss'), 'efter')
        self.assertEqual(d['skills']['emil-review-animations']['roller'].get('rorelseskiss'), 'efter')
        self.assertTrue({'refero', 'mobbin', '21st', 'motion'} <= {t['id'] for t in d['tjanster']})
        self.assertEqual(set(d['skills']), {p.name for p in (ROOT / '.claude' / 'skills').iterdir() if p.is_dir()}, 'varje installerad skill')
        self.assertFalse([n for n, x in d['skills'].items() if x['plats'] == 'utan'], 'i repot har varje skill en roll eller ett skäl')
        a = next(x for x in d['agenter'] if x['id'] == 'andringar')
        self.assertIsNone(a['lucka'], 'ändringsagenten får motorns regler som kopior')
        self.assertTrue(all((ROOT / f).is_file() for f in andringar.MOTORNS_REGLER))

    def test_02_ny_skill_utan_plats_ar_en_lucka(self):
        skills = self.tmpdir / 'skills'
        for n in ('frontend-design', 'kirurg', 'slides', 'helt-ny-skill'):
            (skills / n).mkdir(parents=True)
            (skills / n / 'SKILL.md').write_text('---\nname: %s\n---\n' % n, encoding='utf-8')
        s = kompetens.skillstatus(skills)
        self.assertEqual({n: x['plats'] for n, x in s.items()},
                         {'frontend-design': 'roll', 'kirurg': 'process', 'slides': 'skal', 'helt-ny-skill': 'utan'})
        self.assertIn('helbygge', s['frontend-design']['roller'])
        lu = kompetenskarta.luckor(kompetens.tolka(), s, [], [], {}, [], T)
        self.assertEqual([l['slag'] for l in lu if l['slag'] == 'skill_utan_plats'], ['skill_utan_plats'])
        self.assertIn('helt-ny-skill', lu[0]['rubrik'])

    def test_03_det_observerade_och_luckorna(self):
        # rörelsen: kärnan läst delvis, Motion blockerad; researchen: MCP-kravet refero utan anrop; granskningens två pass
        rorelse = kvitto('rorelse', lasta_hela=False, mcp={'mcp__motion__search-motion-docs': 1})
        rorelse['mcp_utfall'] = {'mcp__motion__search-motion-docs': {'fel': 1}}
        rorelse['tillstand'] = kompetens.tillstand(rorelse, 'rorelse')
        self.skriv('kund-a/atelje/kandidater/k01/STATUS.json', {'kompetens': {'rorelse': {'pass': 'rorelse', 'kvitto': rorelse}}})
        self.skriv('kund-a/atelje/FORSKNING.json', {'kompetens': kvitto('forska', mcp={'mcp__mobbin__search_screens': 2})})
        self.skriv('kund-b/atelje/kandidater/k02/KRITIK.json', {'kompetens': {'a': kvitto('kritik_a'), 'b': kvitto('kritik_b')}})
        d = kompetenskarta.karta(ROOT, self.underlag, self.kunder)
        o = d['observerat']
        self.assertEqual(o['rorelse']['kvitton'], 1)
        self.assertEqual((o['rorelse']['karna_hel'], o['rorelse']['karna_sedd']), (0, 1))
        self.assertEqual(o['forska']['mcp']['mobbin'], {T['anvant']: 1})
        self.assertEqual(o['kritik']['kvitton'], 1, 'kritik_a ur KRITIK.json')
        self.assertEqual(o['motivering']['kvitton'], 1, 'kritik_b ur samma fil')
        self.assertEqual(o['forska']['kunder'], 1)
        slag = {(l['slag'], l['rubrik'].split(':')[0]) for l in d['luckor']}
        rnamn = lambda r: kompetens.tolka()[r]['namn']  # noqa: E731
        self.assertIn(('karna', rnamn('rorelse')), slag)
        self.assertIn(('mcp_krav', rnamn('forska')), slag, 'researchens krav refero utan anrop med resultat')
        self.assertIn(('mcp_blockerat', rnamn('rorelse')), slag)
        self.assertTrue(all(l['kalla'] and l['forslag'] for l in d['luckor']), 'varje lucka har källa och förslag')
        ej = next(l for l in d['luckor'] if l['slag'] == 'ej_observerat')
        self.assertNotIn(kompetens.PASSNAMN['rorelse'], ej['detalj'], 'ett observerat steg står inte bland de oobserverade')

    def test_04_utan_kvitton_ar_inget_observerat(self):
        d = kompetenskarta.karta(ROOT, self.underlag, self.kunder)
        self.assertEqual(d['observerat'], {})
        ej = [l for l in d['luckor'] if l['slag'] == 'ej_observerat']
        self.assertEqual(len(ej), 1)
        self.assertIn('Inte observerat, inte inte gjort', ej[0]['detalj'])
        self.assertFalse([l for l in d['luckor'] if l['slag'] in ('karna', 'mcp_krav', 'mcp_oanvant', 'verktyg_oanvant')],
                         'utan kvitton finns inget som säger att något inte gjordes')
        # en länkad kunds katalog och ett trasigt kvitto läses inte och fäller inte kartan
        (self.underlag / 'kund-c' / 'atelje').mkdir(parents=True)
        (self.underlag / 'kund-c' / 'atelje' / 'FORSKNING.json').write_text('{inte json', encoding='utf-8')
        (self.underlag / 'lank').symlink_to(self.underlag / 'kund-c')
        self.assertEqual(kompetenskarta.karta(ROOT, self.underlag, self.kunder)['observerat'], {})


    def test_05_varje_kvittokalla_en_gang(self):
        # granskningen 2026-10-11: kvitton som kartan inte läste. Planeringens kvitto står i PLANERING.json och samma i
        # KANDIDATPLAN.json, omplaneringens i OMPLANERING-kompetens.json och KANDIDATPLAN.json, och forfining är det
        # senaste av uppdragen: varje kvitto räknas en gång.
        plan, omplan = kvitto('planera'), kvitto('planera')
        self.skriv('kund-a/atelje/forberedelse/2026-10-11T080000Z-abcd1234/KOMPETENS.json', dict(kvitto('forbered'), kompetenskravbrister=[]))
        self.skriv('kund-a/atelje/PLANERING.json', {'kompetens': plan})
        self.skriv('kund-a/atelje/OMPLANERING-kompetens.json', {'kompetens': omplan})
        self.skriv('kund-a/atelje/KANDIDATPLAN.json', {'kompetens': plan, 'omplanering_kompetens': omplan,
                                                      'komplettering': {'kompetens': kvitto('planera')}})
        f1 = {'klar': '2026-10-11T08:00:00Z', 'dom': 'd1', 'kompetens': kvitto('fordjupa')}
        f2 = {'klar': '2026-10-11T09:00:00Z', 'dom': 'd2', 'kompetens': kvitto('fordjupa')}
        self.skriv('kund-a/atelje/kandidater/k01/STATUS.json', {'forfining': f2, 'uppdragen': [f1, f2], 'forbattrad': {'kompetens': kvitto('skapa')}})
        self.skriv('kund-a/atelje/kandidater/k02/STATUS.json', {'forfining': f1})  # äldre status utan uppdragen
        self.skriv('kund-a/atelje/kandidater/k01/fore-efter/01/FORE-EFTER.json', {'kompetens': kvitto('fore_efter')})
        for slug, korning, bevis in (('kund-a', 'r1', {'pass': 'helbygge', 'kvitto': kvitto('helbygge'), 'brister': []}),
                                     ('kund-b', 'r2', {'pass': 'helbygge', 'kvitto': None, 'brister': ['utan bevis']})):
            f = self.kunder / slug / 'korningar' / korning / 'SLUT.json'
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps({'kontroller': {'kompetens': bevis}}), encoding='utf-8')
        (self.kunder / 'lank').symlink_to(self.kunder / 'kund-a')  # en länkad kunds slutposter läses inte
        lista = kompetenskarta.kvitton(self.underlag, self.kunder)
        self.assertEqual(dict(Counter(k['pass'] for k in lista)),
                         {'forbered': 1, 'planera': 3, 'fordjupa': 3, 'skapa': 1, 'fore_efter': 1, 'helbygge': 1})
        self.assertIn('kunder/kund-a/korningar/r1/SLUT.json', [k['kalla'] for k in lista])
        self.assertEqual(kompetenskarta.kvitton(self.underlag), [k for k in lista if k['pass'] != 'helbygge'], 'utan kunder inga slutposter')
        k = kompetens.tolka()
        o = kompetenskarta.karta(ROOT, self.underlag, self.kunder)['observerat']
        for p_ in ('forbered', 'planera', 'fordjupa', 'fore_efter', 'helbygge'):
            for r in kompetens.for_pass(p_, k):
                self.assertIn(r['id'], o, 'rollen %s i %s är observerad' % (r['id'], p_))

if __name__ == '__main__':
    unittest.main(verbosity=2)
