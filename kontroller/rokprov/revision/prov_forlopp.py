"""Sammanhängande syntetiskt förlopp, anropat av prov_skisskritik i dess repokopia.

Verkliga: ärendelager, överlämning, förberedelsepublicering, kandidatens arkiv,
kritikidentitet, val, förfining, designkontrakt, vinnaröverföring, kor.sh med
processvakt/slutpost och teknisk export. Dubblar: modellernas svar, rendering,
bilder och axe. Ingen bedömning av verklig design eller extern leverantörsåtkomst.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import fcntl
from unittest.mock import patch


def kor(g):
    import kundstart as ks
    import kundstart_beredning as kb
    import forberedelse as fb
    import skapande
    import design
    import exportera
    import korslut
    import flodesstart

    a, kd, slug = g['atelje'], g['kd'], g['SLUG']
    root, tmp, skriv, png = g['KOPIA'], g['TMP'], g['skriv'], g['png']
    assert root.is_relative_to(tmp), 'förloppsprovet får bara röra sin registrerade kopia'
    u = g['kund']()
    fixture = tmp / 'forlopp-fixtur'; u.rename(fixture)
    # Kundens uppgifter och bekräftelse går genom samma API som Kundstart använder.
    db = ks.Lager(root / 'underlag/kundstart')
    eid, token = db.skapa(slug, 'Syntetisk beslutsfattare', modellbudget=8)
    def handling(slag, data):
        d = db.las(eid, token)
        return db.kundhandling(eid, token, d['revision'], ks.id_(), slag, data)
    handling('meddelande', {'text': 'Exempelverkstaden erbjuder service nationellt. Visa tjänsten och en kontaktväg.'})
    jobb = db.ta_jobb('syntetisk-beredare')
    mid = jobb['dokument']['meddelanden'][0]['id']
    v = {'namn': 'Exempelverkstaden', 'rackvidd': {'typ': 'nationell'}, 'kontaktvagar': [], 'tjanster': ['Service']}
    db.modellsvar(jobb, {'text': 'Stäm av förslaget.', 'forslag': [], 'fragor': [],
        'verksamhet': {'varden': v, 'kallor': {k: [mid] for k in v}}})
    d = db.las(eid, token)
    d = handling('bekrafta_verksamhet', {'sha256': d['verksamhet_forslag']['sha256']})
    kb.overlamna(db, eid, d['revision'], 'forlopp-overlamning', root)
    assert kb.aktuell(db, u)
    g['kritiker'](); g['SESSIONER'].clear()
    def bered(p, s):
        paket = next((u / 'atelje/forberedelse').iterdir())
        for namn in fb.FILER:
            skriv(paket / namn, '# Syntetiskt arbetsunderlag\nService, nationell räckvidd. Öppna materialfrågor kvar.\n')
        return {'klar': True, 'saknas': []}, None
    g['SVAR'][lambda p, s: s is fb.SCHEMA] = bered
    status = {'fas': 'forberedelse'}
    fb.kor(slug, status, lambda: a.skriv_status(u / 'atelje', status))
    assert fb.giltig(slug) and status['steg'] == 'forberedd'
    # Plan och externa förlagor är också syntetiska modellresultat. Kundkällorna
    # och förberedelsekvittot ersätts aldrig av den gamla testfixturen.
    shutil.copytree(fixture / 'atelje', u / 'atelje', dirs_exist_ok=True)
    shutil.rmtree(u / 'atelje/kandidater/k02')
    shutil.rmtree(a.KUNDER / slug / 'kandidater/k02')
    shutil.copytree(fixture / 'referenser', u / 'referenser')
    shutil.copyfile(fixture / 'REFERENSER.md', u / 'REFERENSER.md')
    plan = a.las_json(u / 'atelje/KANDIDATPLAN.json')
    plan['kandidater'] = {'k01': plan['kandidater']['k01']}
    a.skriv_json_atomiskt(u / 'atelje/KANDIDATPLAN.json', plan)
    assert len(kd.lista(slug)) == 1
    huvud = a.KUNDER / slug / 'sajt'
    shutil.copytree(kd.ksajt(slug, 'k01'), huvud)
    (huvud / 'node_modules').mkdir()
    skriv(huvud / 'astro.config.mjs', "import { defineConfig } from 'astro/config';\nexport default defineConfig({ output: 'static', });\n")
    g['kritiker']()
    anrop = 0
    fordjupning = False
    def skapare(p, s):
        nonlocal anrop
        anrop += 1
        sajt = kd.ksajt(slug, 'k01')
        skriv(kd.kdir(slug, 'k01') / 'RIKTNING.md', 'Huvudreferens: Xref — syntetisk komposition för teknikprov\n')
        css = ''
        if fordjupning:
            md = (root / 'kontroller/rokprov/DESIGN.md').read_text()
            obj, fel = design.las(md); assert not fel
            obj['huvudreferens'] = 'Xref'
            md = '# Syntetiskt designkontrakt\n\n```json design\n' + json.dumps(obj) + '\n```\n'
            css = design.css(obj)
            skriv(sajt / 'DESIGN.md', md)
            skriv(sajt / 'src/styles/design.css', css)
            skriv(sajt / 'src/pages/service/index.astro', '<h1>Service, syntetisk undersida</h1>')
        html = '<!doctype html><html lang="sv"><title>Syntetisk service</title><style>' + css + '\nh1{color:var(--farg-text);font-size:var(--typ-rubrik-storlek)}</style><h1>Exempelverkstadens service</h1></html>'
        skriv(sajt / 'src/pages/index.astro', html)
        skriv(sajt / 'public/illustration.svg', '<svg><!-- syntetisk överföringsmarkör --></svg>')
        nr = max(kd.varvnummer(slug, 'k01') or [0]) + 1
        vd = kd.kdir(slug, 'k01') / ('varv/start/varv-%02d' % nr)
        for b in ('390', '1440'):
            for slag in ('forsta', 'hela'): skriv(vd / ('vy-%s-%s.png' % (b, slag)), png(int(b)))
        skriv(vd / 'FORHAND.md', '# Syntetiskt renderingskvitto\n')
        if anrop == 2:
            a.STOPP.set()  # stoppet infaller efter första kritiken, under skaparens svar
        return None, None
    g['SVAR'][lambda p, s: s is None] = skapare
    kd.satt_status(slug, 'k01', 'planerad', forsok=0)
    try:
        kd.behandla_skiss(slug, 'k01')
        raise AssertionError('stoppet ignorerades')
    except a.Stoppad:
        pass
    finally:
        a.STOPP.clear()
    d = kd.kdir(slug, 'k01')
    assert (d / 'SKISSKRITIK.json').is_file()
    fore = (d / 'SKISSKRITIK.json').read_bytes()
    assert kd.las_status(slug, 'k01')['status'] == 'under_arbete'
    kd.behandla_skiss(slug, 'k01')
    st = kd.las_status(slug, 'k01')
    assert st['status'] == 'klar', st
    assert (d / 'forsok-1/SKISSKRITIK.json').read_bytes() == fore
    kritik = a.las_json(d / 'SKISSKRITIK.json')
    assert kritik['identitet']['forsok'] == 2
    assert len([s for s in g['SESSIONER'] if s['schema'] is kd.SKISSKRITIK_SCHEMA]) == 2
    version = st['version']
    status = {'kandidatflode': True, 'steg': 'klar_for_bedomning', 'fas': 'skiss'}
    a.skriv_status(u / 'atelje', status)
    dom = a.doma(slug, 'ägaren', 'valj', 'Syntetiskt teknikprov: förfina tjänstesidan.',
        kandidater=[{'id': 'k01', 'version': version}], belagg='endast isolerat teknikprov')
    assert not skapande.godkand_giltig(slug)[0], 'ett val blev ett godkännande'
    fordjupning = True
    g['SVAR'][lambda p, s: s is kd.PASS_SCHEMA] = lambda p, s: ({
        'kod_andrad': [], 'beteende_provat': [], 'visuell_bedomning': {'fore': '', 'efter': '', 'omdome': 'ej_bedomd', 'skal': 'Syntetiskt prov.'},
        'ingen_andring': 'Prov av passets övergång, ingen verklig modell.', 'valda': [], 'passade_inte': [], 'kvarstar': []}, None)
    valda = kd.forfina_valda(slug, status, lambda: a.skriv_status(u / 'atelje', status))
    assert valda == ['k01'], (valda, kd.las_status(slug, 'k01'))
    st = kd.las_status(slug, 'k01')
    assert not st['design_fel'], st['design_fel']
    assert st['version'] != version and st['forfining']['fran'] == version
    pass_ = [x for x in st['kompetens'].values() if x.get('pass') in kd.KOMPETENSPASS]
    assert {x['pass'] for x in pass_} == set(kd.KOMPETENSPASS), st['kompetens']
    assert all(x['genomford'] is None for x in pass_), 'attrapper blev kompetensbevis'
    a.doma(slug, 'ägaren', 'godkand', 'Syntetiskt godkännande enbart av startsidans testversion.',
        kandidater=[{'id': 'k01', 'version': st['version']}], belagg='endast isolerat teknikprov')
    assert skapande.godkand_giltig(slug)[0]
    # F07 (motorinventeringen): med Kundstarts ärendelager kräver Flöde-ingången sandlådan redan före starten, som kor.sh nedan
    sparad_sandlada = os.environ.pop('NWP_SANDLADA', None)
    try:
        try:
            flodesstart.krav(slug, 'helbygge')
            raise AssertionError('helbygget fick starta utan sandlåda fast Kundstarts ärendelager finns (F07)')
        except ValueError as e_:
            assert 'sandlådan' in str(e_) and 'NWP_SANDLADA=pa' in str(e_), e_
        assert flodesstart.startmiljo()['kundstart_lager'] and flodesstart.startmiljo()['hinder']
        os.environ['NWP_SANDLADA'] = 'pa'
        assert flodesstart.startmiljo()['hinder'] is None
        flodesstart.krav(slug, 'helbygge')
    finally:
        os.environ.pop('NWP_SANDLADA', None)
        if sparad_sandlada is not None:
            os.environ['NWP_SANDLADA'] = sparad_sandlada
    a.installera_godkand(slug)
    assert (huvud / 'public/illustration.svg').read_bytes() == (kd.ksajt(slug, 'k01') / 'public/illustration.svg').read_bytes()
    # Riktig kor.sh/processvakt i kopian. Körbart lokalt program med namnet claude
    # är en deklarerad testdubbel och startar ingen Claude-session.
    bin_ = tmp / 'forlopp-bin'; bin_.mkdir()
    script = '#!/bin/sh\ncat >/dev/null\nprintf \'%s\\n\' \'{"type":"result","subtype":"success","is_error":false,"num_turns":1,"duration_ms":1}\'\n'
    skriv(bin_ / 'claude', script); (bin_ / 'claude').chmod(0o700)
    env = dict(os.environ, PATH=str(bin_) + os.pathsep + os.environ['PATH'], NWP_STARTKONTROLL='av', NWP_SANDLADA='av', NWP_ATELJE='pa', NWP_MCP_CONFIG='av', NWP_STADNING='av', NWP_FRIST='1')
    env.pop('NWP_SLUG', None)
    neka = subprocess.run(['bash', str(root / 'kor.sh'), slug, 'Syntetisk serviceverksamhet'], cwd=root, env=env, capture_output=True, text=True, timeout=10)
    assert neka.returncode == 2 and 'Kundstarts ärendelager kräver sandlådan' in neka.stdout, (neka.stdout, neka.stderr)
    env['NWP_SANDLADA'] = 'pa'
    r = subprocess.run(['bash', str(root / 'kor.sh'), slug, 'Syntetisk serviceverksamhet'], cwd=root, env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 1, (r.returncode, r.stdout[-5000:], r.stderr[-1000:])
    fil, slut = korslut.senaste_slutpost(a.KUNDER / slug)
    assert fil and slut['slutkod'] == 1
    assert slut['tillstand']['sessionen_avslutad']['varde'] is True, slut['tillstand']
    assert slut['tillstand']['designgranskaren_godkanner']['varde'] is not True
    assert slut['tillstand']['klart_for_leverans']['varde'] is not True
    # kor.sh har lämnat slutposten; processvakten släpper startlåset när den
    # också avslutat sina barn. Prova det verkliga låset före nästa handling.
    frist = time.monotonic() + 5
    with (u / '.atelje-start.las').open('rb') as las:
        while True:
            try:
                fcntl.flock(las, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= frist: raise
                time.sleep(.03)
    with patch.multiple(exportera, ROOT=root, UNDERLAG=a.UNDERLAG, KUNDER=a.KUNDER):
        export = exportera.exportera(slug, bygg=False)
        assert export['ok'] and export['klart_for_leverans'] is False, export
        assert exportera.aktuell(slug)['aktuell']
        skriv(huvud / 'public/illustration.svg', '<svg><!-- senare ändring --></svg>')
        assert not exportera.aktuell(slug)['aktuell']
    handling('meddelande', {'text': 'Nytt behov efter det syntetiska godkännandet.'})
    assert not skapande.godkand_giltig(slug)[0]
    assert not fb.giltig(slug)
    print('FÖRLOPP: Kundstart → förberedelse → skiss → stopp → nytt försök/kritik → val → förfining → syntetiskt startsidesgodkännande → kor.sh → slutkod 1 → intern export; senare kundändring nekar fortsatt godkännande.')
    print('DUBBLAR: modeller, rendering/bilder/axe; ingen verklig AI-, design-, användar- eller leverantörsbedömning.')
