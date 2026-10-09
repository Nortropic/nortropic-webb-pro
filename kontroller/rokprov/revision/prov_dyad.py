#!/usr/bin/env python3
"""prov_dyad.py — Dyad-provet (ägarens uppdrag 2026-10-09, "bygg hela Dyad-provet"; idén ur Dyads fake-llm-server,
källgenomgången C, avsnitt 5): det som verkligen når modellen, per roll, fångat av en falsk Messages-server.

Steg 2, provläget (kontroller/nastlad.py): en nästlad session pekas mot den falska modellen bara med en lokal adress, en
provnyckel och en rot som inte är huvudutcheckningen; annars stoppas sessionen, och ingen driftväg sätter provläget.
Steg 3, rollerna: riktiga `claude -p`-sessioner genom flödets egna funktioner (kandidater.skisskritik, fore_efter och
uppdrag_session) i en kopia av repot, och för varje roll: modellen och ansträngningen, instruktionen ordagrant, varje
bild uppdraget nämner (sha256 lika filens, eller nedskalad av Claude Code med samma proportioner), att de blinda rollerna
nekas skaparens anteckningar och uppdrag medan skaparen läser dem, och att inga nyckelvärden står i dumparna.
Steg 3 kräver Claude Code (`claude`) och hoppas över utan det, med skälet.
"""
import json
import os
import secrets
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

HAR = Path(__file__).resolve()
sys.path.insert(0, str(HAR.parents[2]))
import korregister  # noqa: E402
import nastlad  # noqa: E402
import falsk_modell as fm  # noqa: E402

ROT = HAR.parents[3]
SLUG = 'dyad-prov'


def png(bredd, hojd, farg):
    """En hel PNG i en färg (filter 0 per rad, zlib), så att Claude Code kan läsa och skala den som en riktig bild."""
    rad = b'\x00' + bytes(farg) * bredd
    kropp = zlib.compress(rad * hojd, 9)
    bit = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)  # noqa: E731
    return b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', bredd, hojd, 8, 2, 0, 0, 0)) + bit(b'IDAT', kropp) + bit(b'IEND', b'')


class Provlaget(unittest.TestCase):
    """Steg 2: provläget gäller bara i prov, och aldrig i drift."""

    BAS = {'NWP_FALSK_MODELL': 'http://127.0.0.1:5123', 'NWP_FALSK_NYCKEL': 'sk-ant-prov-0123456789abcdef', 'PATH': '/bin',
           'ANTHROPIC_API_KEY': 'riktig-nyckel-i-skalet', 'ANTHROPIC_AUTH_TOKEN': 'riktig-token', 'ANTHROPIC_BASE_URL': 'https://annan'}

    def test_utan_provlage_folger_ingen_nyckel_eller_bas_url(self):
        bas = {k: v for k, v in self.BAS.items() if not k.startswith('NWP_FALSK')}
        self.assertIsNone(nastlad.provlage(bas, '/tmp/kopia'))
        m = nastlad.miljo(bas, rot='/tmp/kopia')
        self.assertFalse({'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL'} & set(m), m)

    def test_i_prov_den_falska_modellen_och_bara_provnyckeln(self):
        m = nastlad.miljo(self.BAS, rot='/tmp/kopia')
        self.assertEqual((m['ANTHROPIC_BASE_URL'], m['ANTHROPIC_API_KEY']), ('http://127.0.0.1:5123', 'sk-ant-prov-0123456789abcdef'))
        self.assertNotIn('ANTHROPIC_AUTH_TOKEN', m)
        self.assertFalse(any(k.startswith('NWP_') for k in m), 'provlägets egna variabler följer inte med in i sessionen')

    def test_aldrig_i_drift(self):
        for rot in (str(nastlad.HUVUD), None):
            with self.assertRaises(nastlad.ProvlageFel, msg=rot):
                nastlad.miljo(self.BAS, rot=rot)
        with self.assertRaises(nastlad.ProvlageFel):
            nastlad.miljo(self.BAS)  # en väg utan rot (granskarna, prospekten …) stoppar hellre än går mot prenumerationen

    def test_bara_lokal_adress_och_provnyckel(self):
        for andring in ({'NWP_FALSK_MODELL': 'https://api.anthropic.com'}, {'NWP_FALSK_MODELL': 'http://10.0.0.2:80'},
                        {'NWP_FALSK_MODELL': 'http://127.0.0.1'}, {'NWP_FALSK_NYCKEL': 'sk-ant-api03-riktig'}, {'NWP_FALSK_NYCKEL': ''},
                        {'NWP_FALSK_MODELL': ''}):
            with self.assertRaises(nastlad.ProvlageFel, msg=andring):
                nastlad.provlage(dict(self.BAS, **andring), '/tmp/kopia')

    def test_ingen_driftvag_satter_provlaget(self):
        """Bara nastlad.py läser provläget, och bara Dyad-provet sätter det: ingen kod i drift (kontroller, dashboarden,
        mallen, skalskripten) nämner variablerna."""
        tillatna = {'kontroller/nastlad.py', 'kontroller/falsk_modell.py', 'kontroller/rokprov/revision/prov_dyad.py'}
        filer = subprocess.run(['git', '-C', str(ROT), 'ls-files', '-z'], capture_output=True, text=True, check=True).stdout.split('\0')
        traffar = [f for f in filer if f and f.endswith(('.py', '.sh', '.js', '.mjs', '.html', '.json', '.astro')) and f not in tillatna
                   and (ROT / f).is_file() and 'NWP_FALSK_' in (ROT / f).read_text(encoding='utf-8', errors='replace')]
        self.assertEqual(traffar, [])

    def test_dumpen_sparar_inga_nycklar_och_bilderna_som_sha256(self):
        import base64
        import hashlib
        import http.client
        with korregister.egen_tmp_med('nwp-dyad-', 'Dyad-provets dump') as t:
            bild = png(4, 3, (1, 2, 3))
            with fm.Server(Path(t) / 'dump', t) as s:
                c = http.client.HTTPConnection('127.0.0.1', int(s.url.rsplit(':', 1)[1]), timeout=10)
                kropp = {'model': 'm', 'messages': [{'role': 'user', 'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': base64.b64encode(bild).decode()}},
                    {'type': 'text', 'text': 'hej'}]}], 'metadata': {'user_id': 'enhetens-id'}}
                c.request('POST', '/v1/messages', json.dumps(kropp), {'x-api-key': s.nyckel, 'authorization': 'Bearer sk-ant-oat01-hemlig',
                                                                       'Content-Type': 'application/json'})
                self.assertEqual(c.getresponse().status, 200)
            ra = ''.join(f.read_text() for f in (Path(t) / 'dump').glob('*.json'))
            for hemlig in (s.nyckel, 'sk-ant-oat01-hemlig', base64.b64encode(bild).decode(), 'enhetens-id'):
                self.assertNotIn(hemlig, ra)
            r = fm.dumpar(Path(t) / 'dump')[0]
            self.assertEqual((r['huvuden']['x-api-key'], r['huvuden']['authorization']), ('provets nyckel', 'ett annat värde (inte sparat)'))
            self.assertEqual(r['bilder'], [hashlib.sha256(bild).hexdigest()])

    def test_minsta_svaret_haller_flodets_scheman(self):
        sys.path.insert(0, str(ROT / 'kontroller'))
        import kandidater as kd
        for schema in (kd.SKISSKRITIK_SCHEMA, kd.FORE_EFTER_SCHEMA):
            svar = fm.minsta(schema)
            self.assertTrue(set(schema.get('required') or []) <= set(svar), schema.get('required'))


def kopiera_repo(fran, till):
    """Repots spårade och ospårade (ej ignorerade) filer, med beroendena som länkar: provläget gäller aldrig i
    huvudutcheckningen, så rollerna körs här."""
    filer = subprocess.run(['git', '-C', str(fran), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                           capture_output=True, text=True, check=True).stdout.split('\0')
    for f in filer:
        k = fran / f
        if not f or not (k.is_file() or k.is_symlink()):
            continue
        (till / f).parent.mkdir(parents=True, exist_ok=True)
        if k.is_symlink():
            os.symlink(os.readlink(k), till / f)
        else:
            shutil.copy2(k, till / f)
    for lank in ('.venv', 'kontroller/node_modules', 'mall/astro/node_modules'):
        if (till / lank).is_symlink() or (till / lank).exists():  # en ögonblicksbild har redan länken bland filerna
            continue
        if (fran / lank).exists():
            os.symlink((fran / lank).resolve(), till / lank)


@unittest.skipUnless(shutil.which('claude'), 'Claude Code (claude) saknas: rollerna kräver riktiga claude -p-sessioner')
class Rollerna(unittest.TestCase):
    """Steg 3: rollerna i en kopia av repot, mot den falska modellen."""

    def test_rollerna_i_kopian(self):
        with korregister.egen_tmp_med('nwp-dyad-', 'Dyad-provets kopia av repot') as t:
            kopia = Path(t) / 'repo'
            kopiera_repo(ROT, kopia)
            ut = Path(t) / 'ut'
            p = subprocess.run([str(kopia / '.venv' / 'bin' / 'python'), '-B', str(kopia / 'kontroller' / 'rokprov' / 'revision' / 'prov_dyad.py'),
                                '--i-kopian', str(ut)], cwd=str(kopia), capture_output=True, text=True, timeout=900,
                               env={k: v for k, v in os.environ.items() if not k.startswith(('CLAUDE', 'ANTHROPIC', 'NWP_'))})
            sys.stderr.write(p.stderr[-6000:])
            self.assertEqual(p.returncode, 0, p.stdout[-3000:] + p.stderr[-3000:])
            fakta = json.loads((ut / 'FAKTA.json').read_text(encoding='utf-8'))
            sys.stderr.write('Dyad-provet: %s\n' % json.dumps(fakta['sammanfattning'], ensure_ascii=False))


# --- i kopian: kundens fixtur och de tre rollerna ---

def i_kopian(ut):
    sys.path.insert(0, str(ROT / 'kontroller'))
    import atelje
    import kandidater as kd
    import skapande
    ut = Path(ut)
    ut.mkdir(parents=True, exist_ok=True)
    assert ROT.resolve() != nastlad.HUVUD, 'kopian får aldrig vara huvudutcheckningen'
    u = atelje.UNDERLAG / SLUG

    def skriv(p, x):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(x) if isinstance(x, bytes) else p.write_text(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False), encoding='utf-8')
        return p

    skriv(u / 'VERKSAMHET.json', {'schema': 1, 'fiktiv': True, 'namn': 'Exempelverkstaden', 'rackvidd': {'typ': 'nationell'}, 'kontaktvagar': [],
                                  'tjanster': ['Service']})
    skriv(u / 'BRIEF.md', '# Brief\n\n## §2 Målgrupper och toppuppgifter\n\n1. Boka service\n\n## §4 Primär handling\n\nBoka\n')
    skriv(kd.rot(SLUG) / 'KANDIDATPLAN.json', {'tid': '2026-10-09T20:00:00Z', 'lage': 'skiss', 'antal': 1,
                                                'kandidater': {'k01': {'titel': 'Förslaget', 'ide': 'Visa verkstaden', 'hypotes': 'prov',
                                                                       'uppgift': 'Boka service', 'referensbilder': []}}})
    d = kd.kdir(SLUG, 'k01')
    hemligt = {'riktning': 'HEMLIG-RIKTNING-' + secrets.token_hex(6), 'uppdrag': 'HEMLIGT-UPPDRAG-' + secrets.token_hex(6)}
    skriv(d / 'RIKTNING.md', '# Riktning\n\nSkaparens anteckning: %s\n' % hemligt['riktning'])
    skriv(d / 'UPPDRAG.md', '# Uppdrag\n\nSkaparens uppdrag: %s\n' % hemligt['uppdrag'])
    skapare = ['underlag/%s/atelje/kandidater/k01/%s' % (SLUG, n) for n in ('RIKTNING.md', 'UPPDRAG.md')]
    v0, v1 = 'a0' * 32, 'b1' * 32
    for b in (390, 768, 1280, 1440):  # skissens förhandsvarv: första vyn och hela sidan (hela sidan är längre än 2000 px)
        skriv(d / 'varv' / 'start' / 'varv-01' / ('vy-%d-forsta.png' % b), png(b, 800, (b % 251, 40, 90)))
        skriv(d / 'varv' / 'start' / 'varv-01' / ('vy-%d-hela.png' % b), png(b, 3000, (b % 251, 90, 40)))
    for mapp, farg in ((d / 'versioner' / v0[:12] / 'bilder' / 'start', (200, 30, 30)), (d / 'bilder' / 'start', (30, 200, 30))):
        for b in (390, 1440):
            skriv(mapp / ('vy-%d-forsta.png' % b), png(b, 800, farg))
            skriv(mapp / ('vy-%d-hela.png' % b), png(b, 2600, farg))
    kd.satt_status(SLUG, 'k01', 'klar', 'Dyad-provet', version=v1, axe={'allvarliga': 0})
    uppdrag = skapande.uppdrag_giltigt({'typ': 'ratta', 'resultat': 'RESULTATET-SOM-ÄGAREN-BAD', 'omfattning': ['första vyns rubrik'],
                                        'bevara': ['kompositionen']})
    dom = {'tid': '2026-10-09T21:00:00Z', 'kalla': 'ägaren', 'beslut': 'uppdrag', 'text': 'beställarens ord', 'kandidater': [{'id': 'k01', 'version': v1}],
           'uppdrag': uppdrag}

    roller = []

    def kor(namn, blind, modell, effort, fn):
        dumpkat = ut / 'dump' / namn
        with fm.Server(dumpkat, ROT, las_ocksa=skapare) as s:
            with patch.dict(os.environ, {'NWP_FALSK_MODELL': s.url, 'NWP_FALSK_NYCKEL': s.nyckel}):
                resultat = fn()
            roller.append({'namn': namn, 'blind': blind, 'modell': modell, 'effort': effort, 'resultat': resultat, 'dump': dumpkat, 'nyckel': s.nyckel})

    kor('skisskritiken', True, kd.GRANSKARE_MODELL, 'high', lambda: kd.skisskritik(SLUG, 'k01'))
    kor('fore_efter', True, kd.GRANSKARE_MODELL, 'high', lambda: kd.fore_efter(SLUG, 'k01', v0, v1))
    kor('skaparen', False, atelje.MODELL, atelje.EFFORT,
        lambda: kd.uppdrag_session(SLUG, 'k01', dom, uppdrag, d / 'svar-uppdrag-dyad.json'))

    instruktion = {'skisskritiken': 'Du är den kritiska granskaren av en designskiss', 'fore_efter': 'Du jämför två versioner, X och Y,',
                   'skaparen': 'Du utför ett uppdrag på kandidaten'}
    sammanfattning, fel = {}, []
    import hashlib
    for r in roller:
        reqs = fm.dumpar(r['dump'])
        sessioner = sorted({x['session'] for x in reqs})
        rad = {'forfragningar': len(reqs), 'sessioner': len(sessioner)}
        if not reqs:
            fel.append('%s: ingen förfrågan nådde den falska modellen' % r['namn'])
            continue
        # (a) modellen och ansträngningen
        vantad = r['modell'].split('[')[0]
        modeller = sorted({x['modell'] for x in reqs})
        rad['modell'] = modeller
        if modeller != [vantad]:
            fel.append('%s: modellen %s, väntad %s' % (r['namn'], modeller, vantad))
        if '[1m]' in r['modell'] and not all('context-1m' in (x['huvuden'].get('anthropic-beta') or '') for x in reqs):
            fel.append('%s: %s utan 1M-kontexten' % (r['namn'], r['modell']))
        efforts = sorted({str(x['effort']) for x in reqs})
        rad['effort'] = efforts
        if efforts != [r['effort']]:
            fel.append('%s: ansträngningen %s, väntad %s' % (r['namn'], efforts, r['effort']))
        # (b) instruktionen ordagrant i första förfrågan
        forsta = reqs[0]['text']
        if instruktion[r['namn']] and instruktion[r['namn']] not in forsta:
            fel.append('%s: rollens instruktion saknas i förfrågan' % r['namn'])
        if r['namn'] == 'skaparen' and 'RESULTATET-SOM-ÄGAREN-BAD' not in forsta:
            fel.append('skaparen: uppdragets önskade resultat står inte ordagrant i förfrågan')
        # (c) bilderna: varje bild uppdraget nämner nådde modellen, lika eller nedskalad med samma proportioner
        lasningar = [l_ for x in reqs for l_ in x['lasningar']]
        bilder = [l_ for l_ in lasningar if str(l_['fil']).endswith('.png') and Path(l_['fil']).is_file()]  # bilderna som finns
        nedskalade, lika = 0, 0
        for l_ in bilder:
            fil = Path(l_['fil'])
            if l_['nekad'] or not l_['bilder']:
                fel.append('%s: bilden %s nådde inte modellen' % (r['namn'], fil.name))
                continue
            data = fil.read_bytes()
            b_ = l_['bilder'][0]
            if b_['sha256'] == hashlib.sha256(data).hexdigest():
                lika += 1
            else:
                w, h = fm.matt(data)
                bw, bh = b_['matt'] or (0, 0)
                if not (bw and bh and max(bw, bh) <= max(w, h) and abs(bw / bh - w / h) < 0.02):
                    fel.append('%s: %s ändrad på vägen utan att vara samma bild nedskalad (%s mot %s)' % (r['namn'], fil.name, b_['matt'], (w, h)))
                nedskalade += 1
        rad['bilder'] = {'lasta': len(bilder), 'lika_sha256': lika, 'nedskalade': nedskalade}
        if r['namn'] in ('skisskritiken', 'fore_efter') and len(bilder) < 4:
            fel.append('%s: bara %d bilder lästa' % (r['namn'], len(bilder)))
        # (d) skaparens material: de blinda nekas, skaparen läser det (motprovet)
        ra = ''.join(x['ra'] for x in reqs)
        sedda = {k: v in ra for k, v in hemligt.items()}
        nekade = {Path(l_['fil']).name: l_['nekad'] for l_ in lasningar if str(l_['fil']).endswith(('RIKTNING.md', 'UPPDRAG.md'))}
        rad['skaparens_material'] = {'sett': sedda, 'nekat': nekade}
        if r['blind'] and (any(sedda.values()) or not nekade or not all(nekade.values())):
            fel.append('%s: en blind roll fick skaparens material (%s, %s)' % (r['namn'], sedda, nekade))
        if not r['blind'] and not all(sedda.values()):
            fel.append('skaparen: motprovet föll, skaparen nådde inte sitt eget material (%s)' % sedda)
        # inga nyckelvärden i dumparna; bara provets nyckel skickades
        if r['nyckel'] in ra or 'sk-ant-oat' in ra or 'sk-ant-api' in ra:
            fel.append('%s: ett nyckelvärde står i dumpen' % r['namn'])
        nycklar = sorted({x['huvuden'].get('x-api-key', '–') for x in reqs} | {x['huvuden'].get('authorization', '–') for x in reqs})
        rad['nycklar'] = nycklar
        if nycklar != ['provets nyckel', '–']:
            fel.append('%s: andra nycklar än provets: %s' % (r['namn'], nycklar))
        sammanfattning[r['namn']] = rad
    (ut / 'FAKTA.json').write_text(json.dumps({'sammanfattning': sammanfattning, 'fel': fel}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'sammanfattning': sammanfattning, 'fel': fel}, ensure_ascii=False, indent=1))
    return 1 if fel else 0


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--i-kopian':
        sys.exit(i_kopian(sys.argv[2]))
    unittest.main()
