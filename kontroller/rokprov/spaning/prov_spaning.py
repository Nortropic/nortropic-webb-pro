#!/usr/bin/env python3
"""Rökprov för spanaren: fixturflöden i stället för nätet, GitHub-json i stället för gh, HN-json; normalisering,
rensning, rankning, sammanslagning och dedupe mot ett fixturregister. Skriver bara i en tillfällig katalog.

    .venv/bin/python -B kontroller/rokprov/spaning/prov_spaning.py <repots rot>
"""
import json, pathlib, sys
ROOT = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'kontroller'))
import spana as s, kallnyckel as kn
import korregister
FIX = ROOT / 'kontroller' / 'rokprov' / 'spaning'
with korregister.egen_tmp_med('nwp-rev-', 'spanarens syntetiska fixturer') as provrot:
    s.SPANING = pathlib.Path(provrot).resolve() / 'spaning'
    kallor = [{'typ': 'rss', 'namn': 'Provflöde', 'url': 'https://prov.se/feed.xml', 'varfor': '', 'vikt': 1.5, 'id': 'rss1'},
              {'typ': 'rss', 'namn': 'YouTube: prov', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=X', 'varfor': '', 'vikt': 1.0, 'id': 'yt1'},
              {'typ': 'github', 'namn': 'GitHub prov', 'url': 'astro theme --stars ">=50" --updated 90d', 'varfor': '', 'vikt': 1.2, 'id': 'gh1'},
              {'typ': 'hn', 'namn': 'HN prov', 'url': 'lighthouse', 'varfor': '', 'vikt': 1.1, 'id': 'hn1'},
              {'typ': 'sida', 'namn': 'Sidbevakning', 'url': 'https://docs.prov.se/best-practices', 'varfor': '', 'vikt': 1.5, 'id': 'sida1'},
              {'typ': 'rss', 'namn': 'Nere', 'url': 'https://nere.se/feed', 'varfor': '', 'vikt': 1.0, 'id': 'nere'},
              {'typ': 'rss', 'namn': 'Lighthouse releases', 'url': 'https://github.com/GoogleChrome/lighthouse/releases.atom', 'varfor': '', 'vikt': 1.0, 'id': 'ghr1', 'omrade': 'stacken'}]
    s.DOMSTYRDA_ROT = pathlib.Path(provrot)  # inga domstyrda ord förrän provet skriver dem
    s.PINNADE_CACHE = {'lighthouse': '13.5.0'}
    sidtext = {'v': 1}
    def hamta(url, tak):
        if url.startswith('https://prov.se/'): return (FIX / 'rss.xml').read_bytes()
        if url.startswith('https://www.youtube.com/feeds'): return (FIX / 'atom-youtube.xml').read_bytes()
        if url.startswith('https://github.com/GoogleChrome/lighthouse/releases.atom'): return (FIX / 'atom-github-releases.xml').read_bytes()
        if url.startswith('https://hn.algolia.com/'): return (FIX / 'hn.json').read_bytes()
        if url.startswith('https://docs.prov.se/'): return ('<html><head><title>Best practices</title></head><body><p>Use hooks to run Lighthouse on every build and keep accessibility in the loop.</p>' + ('<p>New: skills can declare allowed tools and the agent reads them before each session.</p>' if sidtext['v'] == 2 else '') + '</body></html>').encode()
        raise OSError('HTTP 503')
    gh = {'gh1': json.loads((FIX / 'github.json').read_text())}
    kanda = {kn.normalisera('https://github.com/obra/superpowers'): {'var': 'REGISTER.md', 'datum': '2026-10-02', 'dom': 'ta in'},
             kn.normalisera('https://github.com/nagon/awesome-web-design'): {'var': 'REGISTER-arkiv', 'datum': '2025-01-01', 'dom': 'nej'}}
    # normalisering
    n = kn.normalisera
    assert n('https://youtu.be/dQw4w9WgXcQ?si=x') == n('https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=12') == n('https://m.youtube.com/watch?v=dQw4w9WgXcQ')
    assert n('https://github.com/Obra/Superpowers/tree/main/skills') == n('github.com/obra/superpowers.git') == 'https://github.com/obra/superpowers'
    assert n('https://web.dev/articles/lcp/?utm_source=x#top') == 'https://web.dev/articles/lcp' and n('https://a.se/x/') != n('https://a.se/y/')
    # första spaningen: sidbevakningen sätter baslinje
    h = s.Hamtare(hamta=hamta)
    senast, lista = s.spana(kallor, h, max_per_kalla=20, gh_json=gh, kanda=kanda)
    nya = [k for k in lista if k['status'] == 'ny']
    titlar = {k['titel']: k for k in nya}
    assert 'Core Web Vitals 2026: LCP and INP in practice' in titlar, titlar.keys()
    cwv = titlar['Core Web Vitals 2026: LCP and INP in practice']
    assert '<' not in cwv['sammanfattning'] and cwv['nyckel'] == 'https://web.dev/articles/cwv-2026', cwv
    assert sorted(cwv['kallor']) == ['HN prov', 'Provflöde'], cwv['kallor']  # samma länk ur två källor slås ihop, flödet (1,5) vinner
    lista_ = titlar['10 best tools for devs']; assert 'text till agenter' in lista_['varning'] and 'dolda tecken' in lista_['varning'] and any('listicle' in v for v in lista_['varfor']) and any('medium.com' in v for v in lista_['varfor']), lista_
    yt = titlar['Accessibility audit with axe and WCAG']; assert yt['url'] == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' and yt['popularitet'] == 123456
    astro = titlar['exempel/astro-local-business']; assert any('500 stjärnor' in v for v in astro['varfor']) and astro['licens'] == 'MIT'
    zh = titlar['annan/skills-zh']; assert 'annat språk' in zh['varning']
    assert 'obra/superpowers' not in titlar and senast['redan_kanda'] >= 1, 'känd källa ska bort'
    aw = titlar.get('nagon/awesome-web-design'); assert aw and aw.get('ny_version') and 'ny version' in aw['varning'], aw  # nej 2025, nyare nu
    assert titlar['Lighthouse 14 released with new accessibility audits']['poang'] > titlar['Bokrecension']['poang']
    assert cwv['poang'] > lista_['poang']
    assert any(r['namn'] == 'Nere' and r['fel'] for r in senast['kallor']) and any(r['namn'] == 'Sidbevakning' and r['not'] == 'baslinje satt' for r in senast['kallor'])
    assert 'Ask HN: why are small business websites so bad?' not in titlar  # utan länk och under 200 poäng
    p1 = {k['id']: k['poang'] for k in nya}
    senast2, lista2 = s.spana(kallor, s.Hamtare(hamta=hamta), max_per_kalla=20, gh_json=gh, kanda=kanda)
    assert {k['id']: k['poang'] for k in lista2 if k['status'] == 'ny'} == p1, 'rankningen ska vara deterministisk'
    sidtext['v'] = 2
    senast3, lista3 = s.spana(kallor, s.Hamtare(hamta=hamta), max_per_kalla=20, gh_json=gh, kanda=kanda)
    andrad = [k for k in lista3 if k['kalla'] == 'Sidbevakning']; assert andrad and 'skills' in andrad[0]['sammanfattning'], andrad
    # avfärda och ta in
    k0 = nya[0]; s.satt(k0['id'], 'avfardad', avfardad='prov'); s.satt(nya[1]['id'], 'intagen', intag_id='intag-x')
    sedda = json.load(open(s.SPANING / 'SEDDA.json')); assert len(sedda) == 2 and any(v['status'] == 'intagen' for v in sedda.values())
    senast4, lista4 = s.spana(kallor, s.Hamtare(hamta=hamta), max_per_kalla=20, gh_json=gh, kanda={**kanda, **{kk: {'dom': v['status'], 'datum': v['tid'][:10]} for kk, v in sedda.items()}})
    assert not any(k['status'] == 'ny' and k['id'] in (k0['id'], nya[1]['id']) for k in lista4), 'avfärdade och intagna ska inte komma tillbaka'
    # anropstaket
    try:
        s.spana(kallor, s.Hamtare(max_anrop=2, hamta=hamta), max_per_kalla=20, gh_json=gh, kanda=kanda);
    except Exception as e: raise SystemExit('taket ska inte kasta: %s' % e)
    # --- backloggen 2026-10-03 (spanaren per område, titel ×2, negativa ord, allmänna ord, domstyrda ord, 14 dagar, releaser, betalt) ---
    assert all(k.get('omrade') for k in nya), 'varje kandidat har ett område'
    assert yt['omrade'] in ('form och typografi', 'tillgänglighet', 'provet') and titlar['Lighthouse in the title']['omrade'] in ('stacken', 'provet'), (yt['omrade'], titlar['Lighthouse in the title']['omrade'])
    topp5 = [k['titel'] for k in nya[:5]]
    for brus in ('Chess engine as a Claude Code skill', 'Whiteboard IDE for agents'):
        assert brus in titlar and brus not in topp5 and any('negativt ord' in v for v in titlar[brus]['varfor']), (brus, titlar.get(brus, {}).get('varfor'))
    allm = s.poang({'titel': 'A chess skill for Claude Code', 'sammanfattning': 'an mcp server and an agent', 'kalla_vikt': 1.0, 'url': 'https://example.org/a'})
    assert allm['poang'] == 0 and any('bara allmänna ord' in v for v in allm['varfor']) and allm['omrade'] == 'okänt', allm['varfor']
    hooks = s.poang({'titel': 'Claude Code hooks for Lighthouse audits', 'sammanfattning': 'mcp', 'kalla_vikt': 1.0, 'url': 'https://example.org/b'})
    assert hooks['poang'] > 0 and hooks['omraden'], 'med en områdesträff räknas de allmänna orden'
    assert titlar['Lighthouse in the title']['poang'] > titlar['Notes about audits']['poang'] and any('i titeln ×2' in v for v in titlar['Lighthouse in the title']['varfor']), 'titelträffar väger dubbelt'
    assert titlar['Contact form validation patterns'].get('svarar_mot') == [], 'utan domar svarar inget mot dem'
    assert 'betalt partnerskap' in titlar['Typography deep dive']['varning'], titlar['Typography deep dive']
    rel = [k for k in lista if k.get('release')]
    assert {r['release']['tagg']: r['status'] for r in rel} == {'13.5.0': 'redan i bruk', '13.6.0': 'ny'} and 'pinnad 13.5.0, release 13.6.0' in titlar['v13.6.0']['varning'], rel
    assert 'v13.5.0' not in titlar, 'en release som är pinnad står utanför kön'
    assert s.rensa('ett två tre fyra', 7)[0] == 'ett två…' and s.rensa('ettordsomärlångt x', 5)[0] == 'ettor…' and s.rensa('kort', 10)[0] == 'kort', 'kapning vid ett ord'
    # domstyrda ord: ägarens svar i LARDOMAR.md, en fallen standardpunkt och ett blockerande granskarfynd
    (pathlib.Path(provrot) / 'LARDOMAR.md').write_text('- **Om du fick ändra en sak i hur vi bygger, vad skulle det vara?** Bygg alltid in ett formulär som fungerar utan JS.\n', encoding='utf-8')
    (pathlib.Path(provrot) / 'kunder' / 'x' / 'prov').mkdir(parents=True); (pathlib.Path(provrot) / 'kunder' / 'x' / 'prov' / 'standard.json').write_text(json.dumps({'fel': [{'punkt': '7.4', 'sida': '/', 'text': 'x'}]}))
    (pathlib.Path(provrot) / 'kunder' / 'x' / 'granskning').mkdir(); (pathlib.Path(provrot) / 'kunder' / 'x' / 'granskning' / 'GRANSKNING.json').write_text(json.dumps({'blockerande': [{'kriterium': 'originalitet', 'allvarlighet': 8}]}))
    dom_ord = dict(s.domstyrda_ord(provrot))
    assert set(dom_ord) == {'skriftlig förfrågningsväg', 'byggstandarden 7.4 NAP', 'granskarnas originalitet'}, sorted(dom_ord)
    senast5, lista5 = s.spana(kallor, s.Hamtare(hamta=hamta), max_per_kalla=20, gh_json=gh, kanda=kanda)
    t5 = {k['titel']: k for k in lista5 if k['status'] == 'ny'}
    assert t5['Contact form validation patterns']['svarar_mot'] == ['skriftlig förfrågningsväg'] and any('svarar mot dom' in v for v in t5['Contact form validation patterns']['varfor']), t5['Contact form validation patterns']
    assert t5['Contact form validation patterns']['poang'] > titlar['Contact form validation patterns']['poang'], 'påslag för en träff mot ägarens dom'
    # 14 dagar utan beslut: utgången, kvar i listan men inte i kön
    kl = json.load(open(s.SPANING / 'KANDIDATER.json'))
    kl.append({'id': 'gammal01', 'nyckel': 'https://gammal.se/x', 'url': 'https://gammal.se/x', 'titel': 'Gammal kandidat', 'sammanfattning': '', 'kalla': 'prov', 'kalla_typ': 'rss', 'kallor': ['prov'], 'kalla_vikt': 1.0,
               'hittad': '2026-01-01T00:00:00Z', 'status': 'ny', 'varning': [], 'varfor': [], 'poang': 1.0})
    s.skriv_json(s.SPANING / 'KANDIDATER.json', kl)
    senast6, lista6 = s.spana(kallor, s.Hamtare(hamta=hamta), max_per_kalla=20, gh_json=gh, kanda=kanda)
    g6 = next(k for k in lista6 if k['id'] == 'gammal01'); assert g6['status'] == 'utgangen' and not any(k['id'] == 'gammal01' and k['status'] == 'ny' for k in lista6), g6
    # dashboardens vy: nytt sedan i går, de bästa per område, svarar mot domar, träffsäkerhet per källa
    sys.path.insert(0, str(ROOT / 'dashboard')); import server as dash
    dash.SPANING = s.SPANING
    d = dash.spaning_lista()
    assert d['nytt_sedan_igar'] and isinstance(d['basta_per_omrade'], dict) and all(len(v) <= 2 for v in d['basta_per_omrade'].values()) and d['svarar_mot_domar'] and d['utgangna'] == 1, {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items() if k != 'kandidater'}
    assert d['svarar_mot_domar'][0]['svarar_mot'] == ['skriftlig förfrågningsväg'] and isinstance(d['traffsakerhet'], list)
    # Reddit (backloggen 2026-10-03): reddit.com släpps igenom, värdens egen takt, och kirurgen läser tråden ur RSS:en
    assert not s.HOPPA_VARD.search('www.reddit.com') and not s.HOPPA_VARD.search('reddit.com') and s.HOPPA_VARD.search('x.com'), 'reddit släpps igenom, x inte'
    import time as _t
    s.PAUS_VARD = {'reddit.com': 0.3}
    ht = s.Hamtare(paus=0)
    t0 = _t.monotonic(); ht.fore('reddit.com'); ht.fore('x.se'); ht.fore('x.se'); assert _t.monotonic() - t0 < 0.2, 'andra värdar väntar inte'
    t0 = _t.monotonic(); ht.fore('www.reddit.com'); assert _t.monotonic() - t0 >= 0.25, 'minst PAUS_VARD mellan anrop till reddit.com'
    import reddit_trad
    txt = reddit_trad.till_text((FIX / 'reddit.xml').read_bytes())
    assert txt.startswith('# Why are small business sites so bad?') and 'no clear next step' in txt and '/u/kommentar' in txt and 'above the fold' in txt and '<' not in txt.split('\n')[4], txt
    print('PROV OK')
