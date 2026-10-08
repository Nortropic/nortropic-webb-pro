#!/usr/bin/env python3
"""prov_lasgrans.py — byggets läsgräns per kandidat (GR-20261007-r107#K1; backlogposten
B-20261007-kandidaternas-oberoende-byggets-processgrans-hin; BESLUT.md, tillägget 2026-10-07: byggets läsgräns per
kandidat). Verkliga byggen innanför processgränsen (prova.bygg_inom_grans och kontroller/processgrans.py, sandbox-exec)
av en syntetisk kund i en egen tempkatalog, med node_modules ur rökprovets sajt (kunder/rokprov-mall/sajt):

1. en sida vars kod vid bygget försöker läsa syskonkandidatens källkod, lista dess sidor och kandidaterna, läsa
   skaparnas text i underlaget (den egna och syskonets RIKTNING.md), briefen, domloggen, sajtens grund, en fil i repots
   rot, en fil utanför repot och en hemlighet i det egna projektet: allt nekas, det egna projektet och den egna temp går,
   och bygget går igenom;
2. ett vanligt bygge (Tailwind, en React-ö och en bild genom sharp) går, och läsgränsen ändrar inte vad bygget ger: samma
   filer, och samma innehåll utom sidornas HTML, som sajtens eget bygge (utan läsgräns) av samma källor;
3. kritikens förhandsvisning (forhandsvisa --granskare) bygger kandidaten innanför samma gräns och fotograferar den:
   bygget når varken skaparens text eller syskonet, och bilderna i de fyra bredderna finns i kritikens katalog;
4. ett barn under kandidatens profil når inte syskonet genom en symlänk, en hård länk, en klon, en kopia, /.vol, ett annat
   skiftläge eller en länkad väg (/var), listar inte kandidaterna och når inte syskonets temp; den egna temp är egen;
5. profilen: en väg i kandidater/ utan id, en node_modules-länk som pekar bort från sajtens och ett program utanför
   läsgränsen vägras, ingen tillåtelse att läsa är villkorslös, och sajtens eget bygge har ingen läsgräns (gränsen gäller
   kandidaterna);
6. kandidatens identitet bevaras vid länkar och skiftläge: en länk till huvudbygget eller en annan kandidat vägras,
   medan ett annat namn på själva reporoten fortfarande ger kandidatens läsgräns;
7. länkade kund- och kandidatrötter får inte göra ett internt kandidatalias till ett huvudbygge utan läsgräns.

    .venv/bin/python kontroller/rokprov/revision/prov_lasgrans.py <repo>

Fall 1 och 3–5 var röda mot 8cc786c (före läsgränsen), fall 2 grönt både där och efter. Varje fall redovisas för sig på
stderr; slutkod 1 när något fall föll. Ingenting skrivs i repots underlag/ eller kunder/ utom byggets cacher (.vite,
.astro) i rökprovets node_modules, som rökprovets andra byggen, och inga privata data läses.
"""
import hashlib
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback
import zlib
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'kontroller'))
import korregister  # noqa: E402
import forhandsvisa  # noqa: E402
import processgrans  # noqa: E402
import prova  # noqa: E402

EGNA = []


def stada_egna():
    fel = []
    while EGNA:
        p = EGNA.pop()
        try:
            shutil.rmtree(p)
        except OSError as e:
            fel.append('%s: %s' % (p, e))
    if fel:
        raise RuntimeError('provets städning föll: ' + '; '.join(fel))


if not os.environ.get('NWP_PROV_BEHALL'):
    import atexit
    atexit.register(stada_egna)
TMP = Path(tempfile.mkdtemp(prefix='nwp-lasgrans-')).resolve()
EGNA.append(TMP)
korregister.registrera_tmp(TMP, 'prov_lasgrans')
SLUG = 'lg-prov-%d' % os.getpid()
BYGGTEMP = Path('/tmp/nwp-bygge-' + SLUG)
BYGGTEMP.mkdir()  # exklusivt: en befintlig katalog adopteras aldrig, inte heller för städning
EGNA.append(BYGGTEMP)
korregister.registrera_tmp(BYGGTEMP, 'prov_lasgrans')
PY = sys.executable
FEL = []
NM = ROOT / 'kunder' / 'rokprov-mall' / 'sajt' / 'node_modules'  # rökprovets beroenden (rokprov.sh installerar dem)
T = TMP / 'repo'  # provets repo: repots .gitignore och en .git-hänvisning som i en worktree, som Tailwinds källsökning läser
KUND, UNDER = T / 'kunder' / SLUG, T / 'underlag' / SLUG
HUVUD = KUND / 'sajt'
MALLSIDOR = ('404.astro', 'tack.astro', 'fel.astro', 'mottagen.astro', 'robots.txt.ts', 'sitemap.xml.ts')


def fall(namn):
    def kor_fallet(f):
        try:
            f()
            print('ok: ' + namn, file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — varje fall redovisas för sig
            FEL.append(namn)
            print('FEL: %s: %s: %s' % (namn, type(e).__name__, str(e)[:1500]), file=sys.stderr)
            print(''.join(traceback.format_exc().splitlines(True)[-4:]), file=sys.stderr)
        return f
    return kor_fallet


def skriv(p, text):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    (p.write_bytes if isinstance(text, bytes) else p.write_text)(text)
    return p


def png(b, h):
    """En riktig bild för sharp: en färgad yta b × h."""
    rader = b''.join(b'\x00' + bytes(v for x in range(b) for v in (x * 255 // b, y * 255 // h, (x * y) >> 6 & 0xff)) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', b, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rader, 6))
            + chunk(b'IEND', b''))


def ksajt(kid):
    return KUND / 'kandidater' / kid / 'sajt'


VANLIG = """---
// KOD-SYSKON: kandidatens egen kod
import { Image } from 'astro:assets';
import Bas from '../layouts/Bas.astro';
import Rakna from '../components/Rakna.jsx';
import jobb from '../assets/atelje/jobb-1.png';
import '../styles/sida.css';
---
<Bas titel="Vanligt bygge" beskrivning="En syntetisk kandidat som prövar byggets läsgräns." tema="#0b57d0">
  <main id="innehall" class="mx-auto max-w-3xl p-6">
    <h1 class="text-4xl font-bold tracking-tight text-slate-900">Vanligt bygge</h1>
    <Image src={jobb} alt="Ett jobb" widths={[320, 640]} sizes="(max-width: 640px) 100vw, 640px" class="mt-6 rounded" />
    <div class="mt-6"><Rakna client:visible /></div>
  </main>
</Bas>
"""
RAKNA = """import { useState } from 'react';
export default function Rakna() {
  const [n, satt] = useState(0);
  return <button type="button" className="rounded bg-blue-700 px-4 py-2 text-white" onClick={() => satt(n + 1)}>Räknat {n}</button>;
}
"""


def provsida(vagar):
    """k01:s startsida: koden försöker vid bygget läsa vägarna och skriver utfallet i sidan (LAST, LISTAD eller NEKAD med
    felkoden). 'temp' skriver och läser en fil i byggets TMPDIR."""
    return """---
import fs from 'node:fs';
import Bas from '../layouts/Bas.astro';
const vagar = %s;
const prov = { tmpdir: process.env.TMPDIR || '' };
for (const [namn, [typ, p]] of Object.entries(vagar)) {
  try {
    if (typ === 'lista') prov[namn] = 'LISTAD ' + fs.readdirSync(p).length;
    else if (typ === 'temp') { const f = process.env.TMPDIR + '/provfil.txt'; fs.writeFileSync(f, 'x'); prov[namn] = 'LAST ' + fs.readFileSync(f, 'utf8'); }
    else prov[namn] = 'LAST ' + fs.readFileSync(p, 'utf8').slice(0, 40).replace(/\\s+/g, ' ');
  } catch (e) { prov[namn] = 'NEKAD ' + e.code; }
}
---
<Bas titel="Läsgränsens prov" beskrivning="En syntetisk kandidat vars kod försöker läsa utanför sitt projekt." tema="#0b57d0">
  <main id="innehall"><h1>Läsgränsens prov</h1><pre id="prov">{JSON.stringify(prov)}</pre></main>
</Bas>
""" % json.dumps(vagar, ensure_ascii=False)


VAGAR = {  # namn: (typ, väg) — vad sidans kod försöker läsa vid bygget
    'syskon_kod': ('las', str(ksajt('k02') / 'src' / 'pages' / 'index.astro')),
    'syskon_lista': ('lista', str(ksajt('k02') / 'src' / 'pages')),
    'kandidater_lista': ('lista', str(KUND / 'kandidater')),
    'syskon_riktning': ('las', str(UNDER / 'atelje' / 'kandidater' / 'k02' / 'RIKTNING.md')),
    'egen_riktning': ('las', str(UNDER / 'atelje' / 'kandidater' / 'k01' / 'RIKTNING.md')),  # skaparens text
    'brief': ('las', str(UNDER / 'BRIEF.md')),
    'domlogg': ('las', str(UNDER / 'DESIGNDOMAR.jsonl')),
    'sajtens_grund': ('las', str(HUVUD / 'DESIGN.md')),
    'repo_fil': ('las', str(T / 'BESLUT.md')),
    'utanfor': ('las', str(TMP / 'utanfor' / 'privat.txt')),
    'hemlighet': ('las', str(ksajt('k01') / '.env')),
    'egen_sida': ('las', str(ksajt('k01') / 'src' / 'pages' / 'index.astro')),
    'egen_temp': ('temp', ''),
}
OPPNA = ('egen_sida', 'egen_temp')  # det enda sidan får läsa här


def projekt(mal, sida):
    """Ett projekt som kandidater.forbered_projekt gör det: mallens filer och sidor, kundens bild i src/assets/atelje/,
    node_modules som länk till sajtens verkliga katalog."""
    mal.mkdir(parents=True)
    for namn in ('package.json', 'astro.config.mjs', 'tsconfig.json'):
        shutil.copyfile(ROOT / 'mall' / 'astro' / namn, mal / namn)
    cfg = mal / 'astro.config.mjs'
    cfg.write_text(cfg.read_text().replace('https://ERSATT-MED-DOMAN.se', 'https://exempel-lasgrans.se'))
    shutil.copytree(ROOT / 'mall' / 'astro' / 'src', mal / 'src', ignore=lambda d, n: [x for x in n if Path(d).name == 'pages' and x not in MALLSIDOR])
    skriv(mal / 'src' / 'assets' / 'atelje' / 'jobb-1.png', BILD)
    skriv(mal / 'src' / 'styles' / 'sida.css', '@import "tailwindcss";\n')
    skriv(mal / 'src' / 'components' / 'Rakna.jsx', RAKNA)
    skriv(mal / 'src' / 'pages' / 'index.astro', sida)
    os.symlink(os.path.realpath(HUVUD / 'node_modules'), mal / 'node_modules')


def provets_kund():
    if not NM.is_dir():
        raise SystemExit('rökprovets node_modules saknas (%s): kör kontroller/rokprov.sh' % NM)
    skriv(T / '.gitignore', (ROOT / '.gitignore').read_text())
    skriv(T / '.git', 'gitdir: %s\n' % (TMP / 'git-finns-inte'))
    skriv(T / 'BESLUT.md', '# REPOTS-FIL\n')
    skriv(TMP / 'utanfor' / 'privat.txt', 'UTANFOR-REPOT\n')
    skriv(UNDER / 'BRIEF.md', '# Brief BRIEF-MARKOR\n')
    skriv(UNDER / 'DESIGNDOMAR.jsonl', '{"text": "DOMLOGG-MARKOR"}\n')
    for kid in ('k01', 'k02'):
        skriv(UNDER / 'atelje' / 'kandidater' / kid / 'RIKTNING.md', 'Huvudreferens: egen — prov\n\nSKAPARTEXT-%s\n' % kid.upper())
    HUVUD.mkdir(parents=True)
    os.symlink(os.path.realpath(NM), HUVUD / 'node_modules')
    skriv(HUVUD / 'DESIGN.md', '# Design SAJTENS-GRUND\n')
    projekt(ksajt('k01'), provsida(VAGAR))
    skriv(ksajt('k01') / '.env', 'HEMLIG=1\n')
    projekt(ksajt('k02'), VANLIG)
    skriv(BYGGTEMP / 'tmp-k02' / 'syskonets.txt', 'SYSKONETS-TEMP\n')  # ett syskonbygges temp


def provutfall(sajt):
    m = re.search(r'<pre id="prov">(.*?)</pre>', (Path(sajt) / 'dist' / 'index.html').read_text(), re.S)
    return json.loads(html.unescape(m.group(1)))


def filer(dist):
    return {str(p.relative_to(dist)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(dist).rglob('*')) if p.is_file()}


BILD = png(480, 300)
provets_kund()


# ===== 1. sidans kod vid bygget =====
@fall('1 en sidas kod vid bygget når varken syskonkandidaten, skaparnas text, underlaget, sajtens grund, repot eller hemligheterna; det egna projektet och den egna temp går, och bygget går igenom')
def _sidans_kod():
    rc, ut = prova.bygg_inom_grans(ksajt('k01'))
    assert rc == 0 and (ksajt('k01') / 'dist' / 'index.html').is_file(), (rc, ut[-1500:])
    u = provutfall(ksajt('k01'))
    lackt = {k: v for k, v in u.items() if k in VAGAR and k not in OPPNA and v != 'NEKAD EPERM'}
    assert not lackt, 'sidans kod nådde: %s' % lackt
    assert all(u[k].startswith('LAST ') for k in OPPNA), {k: u[k] for k in OPPNA}
    assert u['tmpdir'].endswith('/tmp-k01'), 'kandidatens egen temp: %s' % u['tmpdir']


# ===== 2. ett vanligt bygge =====
@fall('2 ett vanligt bygge går (Tailwind, en React-ö, en bild genom sharp), och läsgränsen ändrar inte vad bygget ger: samma filer och samma innehåll utom sidornas HTML som sajtens eget bygge av samma källor')
def _vanligt():
    rc, ut = prova.bygg_inom_grans(ksajt('k02'))
    assert rc == 0 and (ksajt('k02') / 'dist' / 'index.html').is_file(), (rc, ut[-1500:])
    for under in ('src', 'astro.config.mjs', 'package.json', 'tsconfig.json'):  # sajtens eget projekt med samma källor
        kalla = ksajt('k02') / under
        (shutil.copytree(kalla, HUVUD / under, dirs_exist_ok=True) if kalla.is_dir() else shutil.copyfile(kalla, HUVUD / under))
    rc, ut = prova.bygg_inom_grans(HUVUD)
    assert rc == 0, ('sajtens eget bygge', rc, ut[-1500:])
    k, s = filer(ksajt('k02') / 'dist'), filer(HUVUD / 'dist')
    assert sorted(k) == sorted(s), sorted(set(k) ^ set(s))
    olika = [n for n in k if k[n] != s[n] and not n.endswith('.html')]
    assert not olika, 'läsgränsen ändrade bygget: %s' % olika
    css = [n for n in k if n.endswith('.css')]
    assert css and any('.text-4xl' in (ksajt('k02') / 'dist' / n).read_text() for n in css), 'Tailwinds klasser saknas i %s' % css
    assert any(n.endswith('.webp') for n in k) and any(n.startswith('_astro/Rakna') and n.endswith('.js') for n in k), sorted(k)


# ===== 3. kritikens förhandsvisning =====
@fall('3 kritikens förhandsvisning (--granskare) bygger kandidaten innanför samma gräns och fotograferar den: bygget når varken skaparens text eller syskonet, och de fyra bredderna finns i kritikens katalog')
def _kritiken():
    spara = (forhandsvisa.KUNDER, forhandsvisa.UNDERLAG)
    forhandsvisa.KUNDER, forhandsvisa.UNDERLAG = T / 'kunder', T / 'underlag'
    try:
        shutil.rmtree(ksajt('k01') / 'dist', ignore_errors=True)
        rc, text, ut = forhandsvisa.forhandsvisa(SLUG, kandidat='k01', granskare=True)
    finally:
        forhandsvisa.KUNDER, forhandsvisa.UNDERLAG = spara
    assert rc == 0, text[-1500:]
    assert ut == UNDER / 'atelje' / 'kandidater' / 'k01' / forhandsvisa.GRANSKARE / 'start' / 'varv-01', ut
    for b in forhandsvisa.BREDDER:
        assert forhandsvisa.giltig_bild(ut / ('vy-%s-forsta.png' % b)), 'bredden %s saknas: %s' % (b, sorted(x.name for x in ut.iterdir()))
    u = provutfall(ksajt('k01'))
    for k in ('egen_riktning', 'syskon_kod', 'syskon_riktning', 'brief'):
        assert u[k] == 'NEKAD EPERM', 'kritikens bygge nådde %s: %s' % (k, u[k])


# ===== 4. ett barn under kandidatens profil =====
BARN = r"""
const fs = require('node:fs');
const [syskon, syskonKat, kandidater, egen, vol, versaler, varlank, syskonTemp] = process.argv.slice(1);
const ut = {};
const prova = (namn, f) => { try { ut[namn] = 'GICK ' + String(f()).slice(0, 30); } catch (e) { ut[namn] = 'NEKAD ' + e.code; } };
prova('las', () => fs.readFileSync(syskon, 'utf8'));
prova('stat', () => fs.statSync(syskon).size);
prova('lista_syskon', () => fs.readdirSync(syskonKat).length);
prova('lista_kandidater', () => fs.readdirSync(kandidater).length);
prova('symlank', () => { fs.symlinkSync(syskon, egen + '/sym.txt'); return fs.readFileSync(egen + '/sym.txt', 'utf8'); });
prova('hard_lank', () => { fs.linkSync(syskon, egen + '/hard.txt'); return fs.readFileSync(egen + '/hard.txt', 'utf8'); });
prova('klon', () => { fs.copyFileSync(syskon, egen + '/klon.txt', fs.constants.COPYFILE_FICLONE_FORCE); return fs.readFileSync(egen + '/klon.txt', 'utf8'); });
prova('kopia', () => { fs.copyFileSync(syskon, egen + '/kopia.txt'); return fs.readFileSync(egen + '/kopia.txt', 'utf8'); });
prova('vol', () => fs.readFileSync(vol, 'utf8'));
prova('versaler', () => fs.readFileSync(versaler, 'utf8'));
prova('varlank', () => fs.readFileSync(varlank, 'utf8'));
prova('syskonets_temp', () => fs.readFileSync(syskonTemp, 'utf8'));
prova('egen_skriv', () => { fs.writeFileSync(egen + '/egen.txt', 'egen'); return fs.readFileSync(egen + '/egen.txt', 'utf8'); });
prova('egen_temp', () => { fs.writeFileSync(process.env.TMPDIR + '/t.txt', 't'); return process.env.TMPDIR.split('/').pop(); });
console.log(JSON.stringify(ut));
"""


@fall('4 ett barn under kandidatens profil når inte syskonet genom symlänk, hård länk, klon, kopia, /.vol, skiftläge eller en länkad väg, listar inte kandidaterna och når inte syskonets temp; den egna temp är egen')
def _barnet():
    syskon = ksajt('k02') / 'src' / 'pages' / 'index.astro'
    st = os.stat(syskon)
    versaler = str(syskon).replace('/kandidater/k02/', '/KANDIDATER/K02/')
    varlank = str(syskon).replace('/private/var/', '/var/', 1) if str(syskon).startswith('/private/var/') else str(syskon).replace('/private/tmp/', '/tmp/', 1)
    assert varlank != str(syskon) and os.path.exists(varlank) and os.path.exists(versaler), (varlank, versaler)
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar', str(ksajt('k01')), '--',
                        'node', '-e', BARN, str(syskon), str(syskon.parent), str(KUND / 'kandidater'), str(ksajt('k01')), '/.vol/%d/%d' % (st.st_dev, st.st_ino),
                        versaler, varlank, str(BYGGTEMP / 'tmp-k02' / 'syskonets.txt')], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and r.stdout.strip(), (r.returncode, r.stdout[-500:], r.stderr[-800:])
    u = json.loads(r.stdout.strip().splitlines()[-1])
    egna = ('egen_skriv', 'egen_temp')
    lackt = {k: v for k, v in u.items() if k not in egna and v.startswith('GICK')}
    assert not lackt, 'barnet nådde: %s' % lackt
    assert u['egen_skriv'] == 'GICK egen' and u['egen_temp'] == 'GICK tmp-k01', u
    for n in ('hard.txt', 'klon.txt', 'kopia.txt'):  # inget av syskonets innehåll hamnade i det egna projektet
        assert not (ksajt('k01') / n).exists(), n


# ===== 5. profilen =====
@fall('5 profilen: kandidater/ utan id, en node_modules-länk som pekar bort från sajtens och ett program utanför läsgränsen vägras, ingen tillåtelse att läsa är villkorslös, och sajtens eget bygge har ingen läsgräns')
def _profilen():
    for fel_vag, skal in ((KUND / 'kandidater', 'hela kandidater/'), (KUND / 'kandidater' / 'ovrigt', 'ett namn som inte är en kandidat')):
        fel_vag.mkdir(parents=True, exist_ok=True)
        try:
            processgrans.profil(SLUG, root=str(T), nat=False, skrivbar=str(fel_vag))
        except SystemExit:
            continue
        raise AssertionError('%s ska vägras som kandidatens projekt' % skal)
    k03 = ksajt('k03')
    k03.mkdir(parents=True)
    os.symlink(TMP / 'utanfor', k03 / 'node_modules')  # en sida i ett tidigare bygge kan ha bytt länken
    try:
        processgrans.profil(SLUG, root=str(T), nat=False, skrivbar=str(k03))
        raise AssertionError('en node_modules-länk som pekar bort från sajtens ska vägras')
    except SystemExit:
        pass
    p = processgrans.profil(SLUG, root=str(T), nat=False, skrivbar=str(ksajt('k01')))
    rader = p.splitlines()
    assert rader.count('(deny file-read*)') == 1, 'läsning nekas som standard'
    for r_ in rader:
        if r_.startswith('(allow file-read'):
            assert re.fullmatch(r'\(allow file-read[\w*-]* (\((literal|subpath) "[^"]+"\) ?)+\)', r_), 'en tillåtelse utan villkor: %s' % r_[:160]
            assert '(subpath "/")' not in r_ and '(subpath "%s")' % T not in r_ and '(subpath "%s")' % os.path.expanduser('~') not in r_, r_[:200]
    sajtens = processgrans.profil(SLUG, root=str(T), nat=False, skrivbar=str(HUVUD))
    assert '(deny file-read*)' not in sajtens.splitlines(), 'sajtens eget bygge har ingen läsgräns'
    # ett program som läsgränsen inte släpper vägras före starten: innanför gränsen fastnar det i kärnan (UE)
    prog = skriv(TMP / 'utanfor' / 'prog.sh', '#!/bin/sh\ntouch "%s"\n' % (TMP / 'utanfor' / 'korde'))
    prog.chmod(0o755)
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar', str(ksajt('k01')), '--',
                        str(prog)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 2 and 'utanför byggets läsgräns' in r.stderr and not (TMP / 'utanfor' / 'korde').exists(), (r.returncode, r.stderr[-300:])
    # också node, som npm och paketens skript startar genom PATH
    skriv(TMP / 'utanfor' / 'bin' / 'node', '#!/bin/sh\nexit 0\n').chmod(0o755)
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar', str(ksajt('k01')), '--',
                        '/bin/echo', 'KORDE'], capture_output=True, text=True, timeout=60,
                       env=dict(os.environ, PATH='%s:%s' % (TMP / 'utanfor' / 'bin', os.environ.get('PATH', ''))))
    assert r.returncode == 2 and 'utanför byggets läsgräns' in r.stderr and 'KORDE' not in r.stdout, (r.returncode, r.stdout[-200:], r.stderr[-300:])


@fall('6 kandidatens identitet bevaras före länkupplösning: en projektlänk till huvudbygget eller en annan kandidat vägras genom CLI, medan rotens /tmp-alias fungerar')
def _kandidatidentitet():
    markor = ksajt('k02') / 'syskonmarkor.txt'
    markor.write_text('SYNTETISK-SYSKONMARKOR')
    k04 = ksajt('k04')
    k04.parent.mkdir(parents=True)
    k04.symlink_to(HUVUD, target_is_directory=True)
    (KUND / 'kandidater' / 'k05').symlink_to(ksajt('k02').parent, target_is_directory=True)
    (KUND / 'alias').symlink_to(ksajt('k01'), target_is_directory=True)
    barn = "const fs=require('node:fs');try{console.log(fs.readFileSync(process.argv[1],'utf8'))}catch(e){console.log('NEKAD '+e.code)}"
    fel = []
    for p in (k04, ksajt('k05'), KUND / 'KANDIDATER' / 'k01' / 'sajt', KUND / 'alias',
              ksajt('k01') / '..' / '..' / '..' / 'sajt'):
        r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar', str(p),
                            '--', 'node', '-e', barn, str(markor)], capture_output=True, text=True, timeout=30)
        if r.returncode == 0 or 'SYNTETISK-SYSKONMARKOR' in r.stdout or 'kandidat' not in r.stderr.lower():
            fel.append((str(p), r.returncode, r.stdout, r.stderr))
    assert not fel, fel
    alias = str(ksajt('k01')).replace('/private/var/', '/var/', 1).replace('/private/tmp/', '/tmp/', 1)
    assert alias != str(ksajt('k01')) and Path(alias).is_dir(), alias
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar', alias,
                        '--', 'node', '-e', barn, str(markor)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout.strip() == 'NEKAD EPERM', (r.returncode, r.stdout, r.stderr)
    rotalias = TMP / 'repo-alias'
    rotalias.symlink_to(T, target_is_directory=True)
    r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat', '--skrivbar',
                        str(rotalias / 'kunder' / SLUG / 'kandidater' / 'k01' / 'sajt'), '--', 'node', '-e', barn, str(markor)],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0 and r.stdout.strip() == 'NEKAD EPERM', (r.returncode, r.stdout, r.stderr)


@fall('7 länkade kund- och kandidatrötter med internt kandidatalias nekas före barnstart')
def _forankrade_rotter():
    markor = ksajt('k02') / 'syskonmarkor.txt'
    barn = "const fs=require('node:fs');try{console.log(fs.readFileSync(process.argv[1],'utf8'))}catch(e){console.log('NEKAD '+e.code)}"
    fel = []
    for rot in (KUND, KUND / 'kandidater'):
        flyttad = (T if rot == KUND else KUND) / ('lagrad-' + rot.name)
        rot.rename(flyttad)
        rot.symlink_to(flyttad, target_is_directory=True)
        try:
            r = subprocess.run([PY, '-B', str(ROOT / 'kontroller' / 'processgrans.py'), SLUG, '--root', str(T), '--utan-nat',
                                '--skrivbar', str(KUND / 'alias'), '--', 'node', '-e', barn, str(markor)],
                               capture_output=True, text=True, timeout=30)
            if r.returncode == 0 or 'SYNTETISK-SYSKONMARKOR' in r.stdout or 'kandidat' not in r.stderr.lower():
                fel.append((rot.name, r.returncode, r.stdout, r.stderr))
        finally:
            rot.unlink()
            flyttad.rename(rot)
    assert not fel, fel


if not os.environ.get('NWP_PROV_BEHALL'):
    stada_egna()  # städfel ger felkod också när alla sakprov gick igenom; atexit är reserv för tidigare undantag
print('läsgränsens prov: %d fall, %d föll' % (7, len(FEL)), file=sys.stderr)
sys.exit(1 if FEL else 0)
