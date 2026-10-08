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
              {'typ': 'rss', 'namn': 'Nere', 'url': 'https://nere.se/feed', 'varfor': '', 'vikt': 1.0, 'id': 'nere'}]
    sidtext = {'v': 1}
    def hamta(url, tak):
        if url.startswith('https://prov.se/'): return (FIX / 'rss.xml').read_bytes()
        if url.startswith('https://www.youtube.com/feeds'): return (FIX / 'atom-youtube.xml').read_bytes()
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
    senast, lista = s.spana(kallor, h, gh_json=gh, kanda=kanda)
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
    senast2, lista2 = s.spana(kallor, s.Hamtare(hamta=hamta), gh_json=gh, kanda=kanda)
    assert {k['id']: k['poang'] for k in lista2 if k['status'] == 'ny'} == p1, 'rankningen ska vara deterministisk'
    sidtext['v'] = 2
    senast3, lista3 = s.spana(kallor, s.Hamtare(hamta=hamta), gh_json=gh, kanda=kanda)
    andrad = [k for k in lista3 if k['kalla'] == 'Sidbevakning']; assert andrad and 'skills' in andrad[0]['sammanfattning'], andrad
    # avfärda och ta in
    k0 = nya[0]; s.satt(k0['id'], 'avfardad', avfardad='prov'); s.satt(nya[1]['id'], 'intagen', intag_id='intag-x')
    sedda = json.load(open(s.SPANING / 'SEDDA.json')); assert len(sedda) == 2 and any(v['status'] == 'intagen' for v in sedda.values())
    senast4, lista4 = s.spana(kallor, s.Hamtare(hamta=hamta), gh_json=gh, kanda={**kanda, **{kk: {'dom': v['status'], 'datum': v['tid'][:10]} for kk, v in sedda.items()}})
    assert not any(k['status'] == 'ny' and k['id'] in (k0['id'], nya[1]['id']) for k in lista4), 'avfärdade och intagna ska inte komma tillbaka'
    # anropstaket
    try:
        s.spana(kallor, s.Hamtare(max_anrop=2, hamta=hamta), gh_json=gh, kanda=kanda);
    except Exception as e: raise SystemExit('taket ska inte kasta: %s' % e)
    print('PROV OK')
