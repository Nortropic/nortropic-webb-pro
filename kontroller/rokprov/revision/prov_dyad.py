#!/usr/bin/env python3
"""prov_dyad.py — Dyad-provet (ägarens uppdrag 2026-10-09, "bygg hela Dyad-provet"; idén ur Dyads fake-llm-server,
källgenomgången C, avsnitt 5): det som verkligen når modellen, per roll, fångat av en falsk Messages-server.

Steg 2, provläget (kontroller/nastlad.py): en nästlad session pekas mot den falska modellen bara med en lokal adress, en
provnyckel och en rot som inte är huvudutcheckningen; annars stoppas sessionen, och ingen driftväg sätter provläget.
Steg 3, rollerna: riktiga `claude -p`-sessioner genom flödets egna funktioner (kandidater.skisskritik, fore_efter och
uppdrag_session) i en kopia av repot, och för varje roll: modellen och ansträngningen, instruktionen ordagrant, varje
bild uppdraget nämner (sha256 lika filens, eller nedskalad av Claude Code med samma proportioner), att de blinda rollerna
nekas skaparens anteckningar och uppdrag medan skaparen läser dem, och att inga nyckelvärden står i dumparna.
Attrappen aktiverar och läser respektive rolls aktuella kärna genom riktiga Skill/Read-anrop före svaret. De vanliga
kompetenskraven prövas också för skaparrollen, vars uppdrag_session i sig bara kör transporten. Detta visar laddningen,
inte att en verklig modell kan förstå eller tillämpa kompetensen.
Steg 3 kräver Claude Code (`claude`) och macOS sandbox-exec; saknas någon hoppas det över med skälet.

Testskydd: egen HOME och CLAUDE_CONFIG_DIR, tomma MCP-konfigurationer bara i repokopian, och en CLI-wrapper som
med OS-regler nekar nät utom attrappens exakta loopbackport samt läsning/skrivning i användarens riktiga Claude- och
hemlighetsmappar. Provet visar Messages-transport, bilder och läsgränser, aldrig verklig MCP-åtkomst eller modellkvalitet.
"""
import contextlib
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
from urllib.parse import urlsplit
from unittest.mock import patch

HAR = Path(__file__).resolve()
sys.path.insert(0, str(HAR.parents[2]))
import korregister  # noqa: E402
import nastlad  # noqa: E402
import falsk_modell as fm  # noqa: E402

ROT = HAR.parents[3]
SLUG = 'dyad-prov'


SANDBOX = '/usr/bin/sandbox-exec'
MCP_PROV = ('refero.json', 'mobbin.json', 'motion.json', '21st.json')


def prov_miljo(bas, hem, bin_, tmp):
    """Ett explicit barn-env, aldrig en ändring av förälderns HOME eller Claude-konfiguration.

    Inga auth-, proxy-, modell-, NWP- eller globala Claude-inställningar ärvs. Konfigurationsvägen
    sätts EFTER filtreringen och överlever nastlad.miljo (CLAUDE_CONFIG_DIR har inte CODE_-prefixet).
    """
    env = {k: bas[k] for k in ('LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TERM') if k in bas}
    env.update(HOME=str(hem), CLAUDE_CONFIG_DIR=str(Path(hem) / '.claude'),
               XDG_CONFIG_HOME=str(Path(hem) / '.config'), XDG_CACHE_HOME=str(Path(hem) / '.cache'),
               TMPDIR=str(tmp), PATH=str(bin_) + os.pathsep + bas.get('PATH', '/usr/bin:/bin'))
    return env


def tomma_prov_mcp(kopia):
    """Messages-transporten prövas här, inte MCP-start/åtkomst. Bara den egna kopians konfig ändras."""
    for namn in MCP_PROV:
        fil = Path(kopia) / 'kontroller' / 'mcp' / namn
        if fil.is_symlink():
            raise RuntimeError('provkopians MCP-konfiguration får inte vara en länk')
        fil.parent.mkdir(parents=True, exist_ok=True)
        fil.write_text('{"mcpServers": {}}\n', encoding='utf-8')


def cli_plan(manifest, argument, miljo):
    """Argv/env för verklig CLI med OS-gräns: endast attrappens exakta loopbackport.

    Ingen kontoinloggning eller global CLI-konfiguration krävs. Även --help körs med skyddet.
    Detta är en ren funktion så att vägar, miljö och nekanden kan prövas utan att starta Claude.
    """
    eget = Path(manifest['eget']).resolve()
    hem = Path(manifest['hem']).resolve()
    konfig = hem / '.claude'
    if not hem.is_relative_to(eget) or hem == eget:
        raise RuntimeError('provhemmet ligger utanför den egna katalogen')
    if Path(miljo.get('HOME', '')).resolve() != hem or Path(miljo.get('CLAUDE_CONFIG_DIR', '')).resolve() != konfig:
        raise RuntimeError('provets HOME eller CLAUDE_CONFIG_DIR försvann före CLI-starten')
    if argument == ['--help']:
        port = None
    else:
        u = urlsplit(miljo.get('ANTHROPIC_BASE_URL', ''))
        if (u.scheme != 'http' or u.hostname != '127.0.0.1' or not u.port or u.username or u.password
                or u.path not in ('', '/') or u.query or u.fragment):
            raise RuntimeError('CLI tillåts bara mot attrappens exakta loopbackadress')
        if not str(miljo.get('ANTHROPIC_API_KEY', '')).startswith(fm.PREFIX):
            raise RuntimeError('CLI saknar provnyckeln; inget återfall till ett konto tillåts')
        port = u.port
    q = lambda x: json.dumps(str(x), ensure_ascii=False)
    profil = ['(version 1)', '(allow default)', '(deny network-outbound)', '(deny network-bind)', '(deny network-inbound)',
              '(deny file-write*)', '(allow file-write* (subpath %s))' % q(eget),
              '(allow file-write* (literal "/dev/null") (literal "/dev/zero") (regex #"^/dev/fd/") (regex #"^/dev/tty"))']
    if port:
        profil.append('(allow network-outbound (remote ip "localhost:%d"))' % port)
    # HOME styr de normala vägarna; OS-gränsen skyddar även mot hårdkodade verkliga användarvägar.
    for namn in ('.claude', '.claude.json', '.nortropic-hemligheter'):
        p = Path(manifest['verkligt_hem']) / namn
        for vag in dict.fromkeys((str(p), str(p.resolve()))):
            profil.append('(deny file-read* file-write* (subpath %s) (literal %s))' % (q(vag), q(vag)))
    env = {k: v for k, v in miljo.items() if k in (
        'HOME', 'CLAUDE_CONFIG_DIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'TMPDIR', 'PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TERM')}
    env.update(CLAUDE_CODE_DISABLE_AUTO_MEMORY='1', CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
               DISABLE_TELEMETRY='1', DISABLE_AUTOUPDATER='1', DISABLE_ERROR_REPORTING='1')
    if port:
        env.update(ANTHROPIC_BASE_URL=miljo['ANTHROPIC_BASE_URL'], ANTHROPIC_API_KEY=miljo['ANTHROPIC_API_KEY'])
    return [SANDBOX, '-p', '\n'.join(profil) + '\n', manifest['claude'], *argument], env


def skyddad_cli(manifestfil, argument):
    manifest = json.loads(Path(manifestfil).read_text(encoding='utf-8'))
    if not Path(SANDBOX).is_file():
        raise RuntimeError('sandbox-exec saknas: ingen oskyddad Claude-start tillåts')
    argv, env = cli_plan(manifest, argument, os.environ)
    os.execve(SANDBOX, argv, env)


def forbered_cli(eget, kopia, claude_bin, bas):
    """Egen wrapper, hem och config för provets barnprocess. Inga filer ur ägarens hem kopieras."""
    eget = Path(eget).resolve()
    hem, bin_, tmp = eget / 'hem', eget / 'bin', eget / 'tmp'
    for p in (hem / '.claude', bin_, tmp):
        p.mkdir(parents=True)
    manifest = eget / 'cli-isolering.json'
    manifest.write_text(json.dumps({'eget': str(eget), 'hem': str(hem), 'verkligt_hem': bas.get('HOME', str(Path.home())),
                                   'claude': str(Path(claude_bin).resolve())}), encoding='utf-8')
    wrapper = bin_ / 'claude'
    wrapper.write_text('#!' + sys.executable + '\nimport runpy, sys\n' +
                       'prov = runpy.run_path(' + repr(str(Path(kopia) / 'kontroller/rokprov/revision/prov_dyad.py')) + ')\n' +
                       'prov["skyddad_cli"](' + repr(str(manifest)) + ', sys.argv[1:])\n', encoding='utf-8')
    wrapper.chmod(0o700)
    tomma_prov_mcp(kopia)
    return prov_miljo(bas, hem, bin_, tmp)


def png(bredd, hojd, farg):
    """En hel PNG i en färg (filter 0 per rad, zlib), så att Claude Code kan läsa och skala den som en riktig bild."""
    rad = b'\x00' + bytes(farg) * bredd
    kropp = zlib.compress(rad * hojd, 9)
    bit = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)  # noqa: E731
    return b'\x89PNG\r\n\x1a\n' + bit(b'IHDR', struct.pack('>IIBBBBB', bredd, hojd, 8, 2, 0, 0, 0)) + bit(b'IDAT', kropp) + bit(b'IEND', b'')


def kompetensplan(pass_):
    """Skriptets faktiska verktygsanrop ur rollens aktuella kärna, aldrig ett syntetiskt godkänt kvitto."""
    import bildkedja
    import kompetens
    filer = list(dict.fromkeys(f for roll in kompetens.for_pass(pass_) for f in roll['karna']))
    skills, las = kompetens.aktiverbara(filer)
    namn = [bildkedja.skillkommando(s) for s in skills]
    if any(n is None for n in namn):
        raise RuntimeError('provrollen har ett olöst Skill-namn')
    return {'skills': namn, 'las_fore': [kompetens.vag(f) for f in las]}


class AttrappensArbete(unittest.TestCase):
    """Attrappen måste utföra kompetensplanen via verktyg; kräver varken CLI, modell eller nät."""

    def test_aktivering_och_hela_karnan_fore_bilder_och_svar(self):
        with korregister.egen_tmp_med('nwp-dyad-', 'Dyad-attrappens anropsföljd') as t:
            rot = Path(t)
            (rot / 'karna.md').write_text('syntetisk rad\n' * 205, encoding='utf-8')
            server = fm.Server(rot / 'dump', rot, skills=['prov-skill'], las_fore=['karna.md'], las_ocksa=['nekad.md'])
            body = {'tools': [{'name': n, 'input_schema': {'type': 'object'}} for n in ('Skill', 'Read', 'StructuredOutput')],
                    'messages': [{'role': 'user', 'content': 'Bilden bilder/prov.png'}]}
            alla_id = []

            def ta_anrop():
                typ, block = server.drag(body)
                self.assertEqual(typ, 'anrop')
                alla_id.extend(b['id'] for b in block)
                body['messages'].append({'role': 'assistant', 'content': block})
                body['messages'].append({'role': 'user', 'content': [
                    {'type': 'tool_result', 'tool_use_id': b['id'], 'content': 'syntetiskt verktygssvar'} for b in block]})
                return block

            self.assertEqual([(b['name'], b['input']) for b in ta_anrop()], [('Skill', {'skill': 'prov-skill'})])
            las = ta_anrop()
            self.assertEqual([b['name'] for b in las], ['Read'] * 3)
            self.assertEqual([b['input']['offset'] for b in las], [1, 101, 201])
            self.assertTrue(all(b['input']['limit'] == 100 and b['input']['file_path'] == str(rot / 'karna.md') for b in las))
            bilder = ta_anrop()
            self.assertEqual([b['input'] for b in bilder], [{'file_path': str(rot / 'bilder/prov.png')}, {'file_path': str(rot / 'nekad.md')}])
            self.assertEqual(server.drag(body)[0], 'svar')
            self.assertEqual(len(alla_id), len(set(alla_id)), 'faserna får inte återanvända tool_use-id')

    def test_saknat_verktyg_ger_inte_fardigt_svar(self):
        with korregister.egen_tmp_med('nwp-dyad-', 'Dyad-attrappens saknade verktyg') as t:
            server = fm.Server(Path(t) / 'dump', t, skills=['prov-skill'])
            typ, svar = server.drag({'tools': [{'name': 'StructuredOutput'}], 'messages': []})
            self.assertEqual(typ, 'text')
            self.assertIn('PROV-FEL', svar)
            self.assertIn('Skill', svar)

    def test_rollernas_plan_anvander_de_riktiga_karnorna(self):
        import bildkedja
        import kompetens
        for pass_ in ('skisskritik', 'fore_efter', 'fordjupa'):
            with self.subTest(pass_=pass_):
                plan = kompetensplan(pass_)
                laddade = ['.claude/skills/%s/SKILL.md' % bildkedja.skillnamn(s) for s in plan['skills']]
                self.assertEqual(set(plan['las_fore'] + laddade), set(kompetens.lasfiler(pass_)))
                self.assertTrue(all((ROT / f).is_file() for f in plan['las_fore']))


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


@unittest.skipUnless(shutil.which('claude') and Path(SANDBOX).is_file(),
                     'Claude Code eller sandbox-exec saknas: lokalt transportprov körs aldrig oskyddat')
class Rollerna(unittest.TestCase):
    """Steg 3: rollerna i en kopia av repot, mot den falska modellen."""

    def test_rollerna_i_kopian(self):
        with korregister.egen_tmp_med('nwp-dyad-', 'Dyad-provets kopia av repot') as t:
            kopia = Path(t) / 'repo'
            kopiera_repo(ROT, kopia)
            ut = Path(t) / 'ut'
            env = forbered_cli(t, kopia, shutil.which('claude'), os.environ)
            p = subprocess.run([str(kopia / '.venv' / 'bin' / 'python'), '-B', str(kopia / 'kontroller' / 'rokprov' / 'revision' / 'prov_dyad.py'),
                                '--i-kopian', str(ut)], cwd=str(kopia), capture_output=True, text=True, timeout=900,
                               env=env)
            sys.stderr.write(p.stderr[-6000:])
            self.assertEqual(p.returncode, 0, p.stdout[-3000:] + p.stderr[-3000:])
            fakta = json.loads((ut / 'FAKTA.json').read_text(encoding='utf-8'))
            sys.stderr.write('Dyad-provet: %s\n' % json.dumps(fakta['sammanfattning'], ensure_ascii=False))


class Isolering(unittest.TestCase):
    """Skyddets mekanik prövas utan Claude. Barnmiljöfallet kan köras mot sparad förekod."""

    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-dyad-', 'Dyad-provets isoleringskontrakt'))).resolve()
        self.hem, self.bin = self.tmp / 'hem', self.tmp / 'bin'
        self.manifest = {'eget': str(self.tmp), 'hem': str(self.hem), 'verkligt_hem': '/syntetiskt/agare', 'claude': '/syntetiskt/claude'}
        self.env = prov_miljo({'PATH': '/usr/bin:/bin', 'HOME': '/syntetiskt/agare'}, self.hem, self.bin, self.tmp / 'tmp')
        self.env.update(ANTHROPIC_BASE_URL='http://127.0.0.1:5123', ANTHROPIC_API_KEY=fm.PREFIX + '1234567890')

    def test_barnets_miljo_isoleras_efter_filtrering_genom_riktiga_testingangen(self):
        # Föreprov: kör förekodens Rollerna.test_rollerna_i_kopian med bara CLI-processen ersatt.
        # Ingen verklig CLI, inget gammalt kundmaterial och ingen grindsfunktion ersätts.
        basfil = os.environ.get('NWP_DYAD_ISOLERING_BAS')
        ns = globals()
        if basfil:
            ns = {'__name__': 'dyad_forekod', '__file__': str(HAR)}
            exec(compile(Path(basfil).read_text(encoding='utf-8'), str(HAR), 'exec'), ns)
        calls = []
        def process(args, **kw):
            calls.append((args, kw))
            ut = Path(args[-1]); ut.mkdir(parents=True)
            (ut / 'FAKTA.json').write_text('{"sammanfattning": {}}')
            return subprocess.CompletedProcess(args, 0, '', '')
        eget = self.tmp / 'ingang'; eget.mkdir()
        def kopia(fran, till):
            (Path(till) / 'kontroller/rokprov/revision').mkdir(parents=True)
        with patch.object(korregister, 'egen_tmp_med', return_value=contextlib.nullcontext(str(eget))), \
                patch.dict(ns, {'kopiera_repo': kopia}), patch.object(subprocess, 'run', side_effect=process), \
                patch.object(shutil, 'which', return_value='/syntetiskt/claude'):
            ns['Rollerna']('test_rollerna_i_kopian').test_rollerna_i_kopian()
        env = calls[0][1]['env']
        self.assertEqual(Path(env['HOME']).resolve(), eget / 'hem', 'testet ärvde ägarens HOME')
        self.assertEqual(Path(env.get('CLAUDE_CONFIG_DIR', '')).resolve(), eget / 'hem/.claude', 'konfigurationsvägen tappades i filtret')
        self.assertEqual(Path(env['PATH'].split(os.pathsep)[0]), eget / 'bin', 'CLI går förbi provets OS-wrapper')
        self.assertFalse({'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_API_KEY', 'HTTP_PROXY', 'HTTPS_PROXY'} & env.keys())

    def test_configdir_overlever_nastlad_miljo_utan_agarens_variabler(self):
        bas = {'HOME': '/syntetiskt/agare', 'PATH': '/usr/bin:/bin', 'CLAUDE_CONFIG_DIR': '/syntetiskt/gammal',
               'ANTHROPIC_AUTH_TOKEN': 'hemligt', 'HTTP_PROXY': 'http://127.0.0.1:9999', 'CLAUDE_CODE_USE_BEDROCK': '1'}
        fore = dict(bas)
        env = prov_miljo(bas, self.hem, self.bin, self.tmp / 'tmp')
        env.update(NWP_FALSK_MODELL='http://127.0.0.1:5123', NWP_FALSK_NYCKEL=fm.PREFIX + '1234567890')
        m = nastlad.miljo(env, rot=self.tmp / 'repo')
        self.assertEqual(m['CLAUDE_CONFIG_DIR'], str(self.hem / '.claude'))
        self.assertEqual(m['HOME'], str(self.hem))
        self.assertEqual(m['ANTHROPIC_API_KEY'], fm.PREFIX + '1234567890')
        self.assertFalse({'ANTHROPIC_AUTH_TOKEN', 'HTTP_PROXY', 'CLAUDE_CODE_USE_BEDROCK'} & m.keys())
        self.assertEqual(bas, fore, 'förälderns miljö ändrades')

    def test_os_gransen_slipper_bara_attrappens_exakta_port(self):
        argv, env = cli_plan(self.manifest, ['-p', 'syntetiskt'], dict(self.env, HTTP_PROXY='http://127.0.0.1:9999'))
        self.assertEqual(argv[:2], [SANDBOX, '-p'])
        profil = argv[2]
        self.assertIn('(deny network-outbound)', profil)
        self.assertIn('(allow network-outbound (remote ip "localhost:5123"))', profil)
        self.assertEqual(profil.count('(allow network-outbound'), 1)
        self.assertNotIn('localhost:*', profil)
        self.assertIn('(deny file-write*)', profil)
        self.assertIn('/syntetiskt/agare/.claude', profil)
        self.assertIn('/syntetiskt/agare/.nortropic-hemligheter', profil)
        self.assertEqual(argv[3:], ['/syntetiskt/claude', '-p', 'syntetiskt'])
        self.assertNotIn('HTTP_PROXY', env)

    def test_cli_nekar_tappad_isolering_eller_extern_modell(self):
        for andring in ({'HOME': '/syntetiskt/agare'}, {'CLAUDE_CONFIG_DIR': '/syntetiskt/agare/.claude'},
                        {'ANTHROPIC_BASE_URL': 'https://api.anthropic.com'}, {'ANTHROPIC_BASE_URL': 'http://127.0.0.1:5123/?annan=1'},
                        {'ANTHROPIC_API_KEY': ''}):
            with self.subTest(andring=andring), self.assertRaises(RuntimeError):
                cli_plan(self.manifest, ['-p'], dict(self.env, **andring))

    def test_help_far_inget_nat_och_ingen_nyckel(self):
        argv, env = cli_plan(self.manifest, ['--help'], self.env)
        self.assertNotIn('(allow network-outbound', argv[2])
        self.assertNotIn('ANTHROPIC_API_KEY', env)
        self.assertIn('(deny network-outbound)', argv[2])

    def test_tomma_mcp_galler_bara_provkopian(self):
        kopia, granne = self.tmp / 'repo', self.tmp / 'annat'
        for rot in (kopia, granne):
            for namn in MCP_PROV:
                f = rot / 'kontroller/mcp' / namn; f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text('{"mcpServers": {"syntetisk": {"url": "https://exempel.invalid"}}}')
        tomma_prov_mcp(kopia)
        for namn in MCP_PROV:
            self.assertEqual(json.loads((kopia / 'kontroller/mcp' / namn).read_text()), {'mcpServers': {}})
            self.assertIn('syntetisk', json.loads((granne / 'kontroller/mcp' / namn).read_text())['mcpServers'])

    def test_wrapper_startar_sandbox_och_inte_cli_direkt(self):
        manifest = self.tmp / 'isolering.json'; manifest.write_text(json.dumps(self.manifest))
        with patch.dict(os.environ, self.env, clear=True), patch.object(Path, 'is_file', return_value=True), \
                patch.object(os, 'execve') as start:
            skyddad_cli(manifest, ['-p', 'syntetiskt'])
        self.assertEqual(start.call_args.args[0], SANDBOX)
        self.assertEqual(start.call_args.args[1][3], '/syntetiskt/claude')


# --- i kopian: kundens fixtur och de tre rollerna ---

def i_kopian(ut):
    sys.path.insert(0, str(ROT / 'kontroller'))
    import atelje
    import kandidater as kd
    import skapande
    import kompetens
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

    def kor(namn, pass_, blind, modell, effort, fn):
        dumpkat = ut / 'dump' / namn
        with fm.Server(dumpkat, ROT, las_ocksa=skapare, **kompetensplan(pass_)) as s:
            with patch.dict(os.environ, {'NWP_FALSK_MODELL': s.url, 'NWP_FALSK_NYCKEL': s.nyckel}):
                resultat = fn()
            kv = resultat.get('kompetens') or kompetens.kvitto([resultat], pass_)
            roller.append({'namn': namn, 'blind': blind, 'modell': modell, 'effort': effort, 'resultat': resultat,
                           'kompetensbrister': kompetens.kravbrister(kv, pass_), 'dump': dumpkat, 'nyckel': s.nyckel})

    kor('skisskritiken', 'skisskritik', True, kd.GRANSKARE_MODELL, 'high', lambda: kd.skisskritik(SLUG, 'k01'))
    kor('fore_efter', 'fore_efter', True, kd.GRANSKARE_MODELL, 'high', lambda: kd.fore_efter(SLUG, 'k01', v0, v1))
    kor('skaparen', 'fordjupa', False, atelje.MODELL, atelje.EFFORT,
        lambda: kd.uppdrag_session(SLUG, 'k01', dom, uppdrag, d / 'svar-uppdrag-dyad.json'))

    instruktion = {'skisskritiken': 'Du är den kritiska granskaren av en designskiss', 'fore_efter': 'Du jämför två versioner, X och Y,',
                   'skaparen': 'Du utför ett uppdrag på kandidaten'}
    sammanfattning, fel = {}, []
    import hashlib
    for r in roller:
        reqs = fm.dumpar(r['dump'])
        sessioner = sorted({x['session'] for x in reqs})
        rad = {'forfragningar': len(reqs), 'sessioner': len(sessioner), 'kompetensbrister': r['kompetensbrister']}
        fel += ['%s: %s' % (r['namn'], brist) for brist in r['kompetensbrister']]
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
