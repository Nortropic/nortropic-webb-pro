"""Förberett experiment genom skissa och session_args; körs i skisskritikprovets kopia."""
def kor(g):
    import json
    import shutil
    from unittest.mock import patch
    import ab
    a, kd, slug = g['atelje'], g['kd'], g['SLUG']
    skriv, png = g['skriv'], g['png']
    g['kund'](); g['kritiker'](); g['SESSIONER'].clear()
    huvud = a.KUNDER / slug / 'sajt'
    shutil.copytree(kd.ksajt(slug, 'k01'), huvud)
    (huvud / 'node_modules').mkdir()
    shutil.rmtree(a.KUNDER / slug / 'kandidater')  # bara den registrerade syntetiska kopians fixtur
    shutil.rmtree(kd.rot(slug) / 'kandidater')
    plan = a.las_json(kd.rot(slug) / 'KANDIDATPLAN.json')
    del plan['kandidater']['k02']
    skriv(kd.rot(slug) / 'KANDIDATPLAN.json', json.dumps(plan))
    for n in ('FORSKNING.json', 'PLANPROVNING.json', 'UPPDRAGSMATERIAL.json'):
        skriv(kd.rot(slug) / n, json.dumps({'kandidater': {'k01': {}}}))
    skriv(kd.kdir(slug, 'k01') / 'UPPDRAG.md', '# Samma uppdrag\nSyntetisk webbskiss.')
    kd.satt_status(slug, 'k01', 'planerad', forsok=0)
    post = ab.forbered_skiss(slug, 'k01')
    riktig = kd.forbered_projekt
    def forbered(slug, kid):
        riktig(slug, kid)
        skriv(kd.ksajt(slug, kid) / 'src/pages/index.astro', '<h1>Syntetisk skiss</h1>')
        skriv(kd.kdir(slug, kid) / 'RIKTNING.md', 'Huvudreferens: egen — syntetisk komposition')
        for b in ('390', '1440'):
            for slag in ('forsta', 'hela'):
                skriv(kd.kdir(slug, kid) / 'varv/start/varv-01' / ('vy-%s-%s.png' % (b, slag)), png(int(b)))
    with patch.object(kd, 'forbered_projekt', forbered):
        for kid in post['kandidater']:
            g['SESSIONER'].clear()
            kd.behandla_skiss(slug, kid)
            skapare = [x for x in g['SESSIONER'] if x['schema'] is None]
            kritik = [x for x in g['SESSIONER'] if x['schema'] is kd.SKISSKRITIK_SCHEMA]
            assert len(skapare) == 2 and len(kritik) == 1, g['SESSIONER']
            for x in skapare:
                assert x['effort'] == post['varden'][kid]
                args = a.session_args([], modell=x['modell'], effort=x['effort'])
                assert args[args.index('--effort') + 1] == post['varden'][kid]
                assert args[args.index('--model') + 1] == kd.skaparval()['modell']
            assert kritik[0]['effort'] == 'high' and kritik[0]['modell'] == kd.GRANSKARE_MODELL
            assert kd.las_status(slug, kid)['forsok_tider'][0]['begard_installning']['effort'] == post['varden'][kid]
    assert ab.skissresultat(slug)['jamforbara_kallor']
    print('A/B: två separata kandidater, skapare och svar har medium/high; kritik och generella värden oförändrade. Modell och rendering är testdubblar.')
