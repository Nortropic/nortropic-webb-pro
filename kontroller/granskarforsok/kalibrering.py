#!/usr/bin/env python3
"""Kalibreringsförsöket: granskaren prövas på de undanhållna kalibreringsexemplen (externa sajter som ägaren dömt blint i
tre nivåer; backlogposten om kalibrering av visuell nivå) med dagens kritik/GRANSKARE.md och kalibreringsankarna. Måttet:
falska godkännanden (granskaren godkänner det ägaren kallade nästan eller generisk) och falska underkännanden (granskaren
underkänner tydligt över ribban).

    .venv/bin/python kontroller/granskarforsok/kalibrering.py [--torr] [--parallellt N] [--modell M] [--effort E] [--frist S]

Utdata utanför repot, under $NWP_FORSOK eller /tmp/nwp-granskarforsok, i kalibrering/: per exempel de frysta bilderna,
ankarna, PROMPT.txt och svar.json; RAPPORT.json och RAPPORT.md med måtten. Återupptagbart: exempel med giltigt svar hoppas
över. Granskaren får bara se exemplets frysta bilder, ankarna och mekaniken; underlag/, kunder/, LARDOMAR.md och hemmets
.claude nekas. Siffran (utan sajternas namn) skrivs av sessionen i LARDOMAR.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import granska as gr  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
HEM = str(Path.home())
G = Path(os.environ.get('NWP_FORSOK') or '/tmp/nwp-granskarforsok') / 'kalibrering'
VYER = ('vy-390-forsta.png', 'vy-1440-forsta.png', 'vy-390-hela.png')
NEKAS_EXTRA = ['Read(./underlag/**)', 'Read(./kunder/**)', 'Read(./LARDOMAR.md)', 'Read(%s/.claude/**)' % HEM]


def undanhallna(underlag=None):
    return [e for e in gr.kalibreringsexempel(underlag) if not e['ankare'] and e['bilder']]


def forbered(e, ut, underlag=None):
    """Exemplets bilder (start och undersida: första vyn 390/1440, hela 390, rutorna) och tillgänglighetsträd kopierade till
    ut/sajt/, ankarna frysta i ut/ (som i en omgång). Ger (bilder, aria, ankare)."""
    rot = Path(underlag or gr.UNDERLAG) / 'kalibrering'
    ut = Path(ut)
    bilder, aria = [], []
    for sida in ('start', 'undersida'):
        kalla = rot / e['id'] / sida
        if not kalla.is_dir():
            continue
        mal = ut / 'sajt' / sida
        mal.mkdir(parents=True, exist_ok=True)
        for fil in sorted(kalla.iterdir()):
            if fil.suffix == '.png' and (fil.name in VYER or '-ruta-' in fil.name) or fil.name.endswith('-aria.txt'):
                shutil.copy2(gr.sakert_original(fil, rot), mal / fil.name)
                (aria if fil.suffix == '.txt' else bilder).append(mal / fil.name)
    return bilder, aria, gr.frysta_ankare(ut, underlag)


def uppdrag(e, ut, bilder, aria, ankare):
    rad = lambda p: '- ' + str(p)  # noqa: E731
    trosklar = ', '.join('%s ≥ %d' % (k, gr.TROSKEL[k]) for k in gr.KRITERIER)
    delar = [
        'Du är granskaren. Läs %s först och följ den. Du ändrar inga filer.' % gr.INSTRUKTION, '',
        'Det här är ett kalibreringsförsök: sajten är en befintlig extern webbplats, inte vårt bygge, och den finns inte live',
        'här. Döm den från skärmbilderna och tillgänglighetsträden nedan, som ägaren gjorde, på samma fem kriterier. Inget',
        'underlag om verksamheten finns; döm verksamhetens egen närvaro ur sajten. Skriv "ej tillämpligt" under likhet_tidigare.', '',
        'Din arbetskatalog: %s' % ut,
        'Trösklar för godkänt: %s, och inga blockerande fynd. Godkännandet räknas ut av verktyget.' % trosklar, '',
        'Ribban är professionell nivå enligt kalibreringsankarna och exemplaren i kunskap/referenser-professionella.md.', '',
        *(['Kalibreringsankare: externa sajter som ägaren dömt blint (%s). Ägarens ord om vad som skiljer, ordagrant: %s' % (gr.KALIBRERING_SKALA, ankare[0]),
           'Första vyn 390 och 1440 per sajt (läs varje, med ägarens ord bredvid):', *[rad(p) + ' — ' + t for p, t in ankare[1]], '']
          if ankare else []),
        'Sajtens skärmbilder: startsidan och en undersida, första vyn i 390 och 1440, hela sidan i 390 och skärmhöga rutor (läs varje):',
        *[rad(p) for p in bilder], '',
        'Tillgänglighetsträd:', *([rad(p) for p in aria] or ['- saknas']), '',
        'Måttstockar:', *['- %s: %s' % (namn, f) for namn, f in gr.MATTSTOCKAR if (ROOT / f).is_file()],
    ]
    return '\n'.join(delar) + '\n'


def kor_en(e, ut, modell, effort, frist, claude):
    prompt = (ut / 'PROMPT.txt').read_text(encoding='utf-8')
    args = [claude, '-p', '--max-turns', '120', '--permission-mode', 'dontAsk', '--output-format', 'json',
            '--setting-sources', 'project,local', '--strict-mcp-config', '--model', modell, '--effort', effort,
            '--json-schema', gr.SCHEMA.read_text(encoding='utf-8'), '--add-dir', str(ut),
            '--allowedTools', 'Read', 'Glob', 'Grep', 'Bash(ls *)', '--disallowedTools', *gr.NEKAS, *NEKAS_EXTRA]
    t0 = time.time()
    with open(ut / 'svar.json', 'wb') as sv, open(ut / 'stderr.log', 'wb') as err:
        try:
            subprocess.run(args, input=prompt.encode(), stdout=sv, stderr=err, cwd=str(ROOT), env=gr.ren_miljo(), timeout=frist)
        except subprocess.TimeoutExpired:
            pass
    return e['id'], round(time.time() - t0)


def jamfor(exempel, svar):
    """Granskarens utfall mot ägarens nivå. svar: {id: structured_output}. Ger (rader, sammanfattning)."""
    rader = []
    for e in exempel:
        res = svar.get(e['id'])
        if not isinstance(res, dict) or not isinstance(res.get('kriterier'), dict):
            rader.append({'id': e['id'], 'agaren': e['niva'], 'granskaren': None, 'utfall': 'inget giltigt svar'})
            continue
        godk = gr.godkand(res)
        betyg = {k: (res['kriterier'].get(k) or {}).get('betyg') for k in gr.KRITERIER}
        if godk and e['niva'] != 'over':
            utfall = 'falskt godkännande'
        elif not godk and e['niva'] == 'over':
            utfall = 'falskt underkännande'
        else:
            utfall = 'rätt'
        rader.append({'id': e['id'], 'agaren': e['niva'], 'granskaren': 'godkänd' if godk else 'underkänd', 'niva': gr.niva(res),
                      'betyg': betyg, 'blockerande': len(res.get('blockerande') or []), 'utfall': utfall})
    ej_over = [r for r in rader if r['agaren'] != 'over' and r['granskaren']]
    over = [r for r in rader if r['agaren'] == 'over' and r['granskaren']]
    s = {'undanhallna': len(exempel), 'svar': sum(1 for r in rader if r['granskaren']),
         'falska_godkannanden': sum(1 for r in ej_over if r['utfall'] == 'falskt godkännande'), 'av_ej_over': len(ej_over),
         'falska_underkannanden': sum(1 for r in over if r['utfall'] == 'falskt underkännande'), 'av_over': len(over)}
    return rader, s


def rapport(rader, s, mal, modell, effort):
    (mal / 'RAPPORT.json').write_text(json.dumps({'tid': gr.nu(), 'modell': modell, 'effort': effort, 'rader': rader, 'sammanfattning': s},
                                                 ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    txt = ['# Kalibreringsförsöket %s · %s %s' % (gr.nu(), modell, effort), '',
           'Undanhållna exempel: %d, svar: %d. Falska godkännanden: %d av %d (ägaren: nästan eller generisk). Falska underkännanden: %d av %d (ägaren: tydligt över ribban).' % (
               s['undanhallna'], s['svar'], s['falska_godkannanden'], s['av_ej_over'], s['falska_underkannanden'], s['av_over']), '',
           '| id | ägaren | granskaren | nivå | betyg | blockerande | utfall |', '|---|---|---|---|---|---|---|']
    for r in rader:
        b = r.get('betyg') or {}
        txt.append('| %s | %s | %s | %s | %s | %s | %s |' % (r['id'], gr.KALIBRERING_NIVAER[r['agaren']], r.get('granskaren') or '–', r.get('niva', '–'),
                                                           ' '.join(str(b.get(k, '?')) for k in gr.KRITERIER) if b else '–', r.get('blockerande', '–'), r['utfall']))
    (mal / 'RAPPORT.md').write_text('\n'.join(txt) + '\n', encoding='utf-8')
    return mal / 'RAPPORT.md'


def main(argv=None):
    p = argparse.ArgumentParser(prog='kalibrering', description=__doc__.split('\n\n')[0])
    p.add_argument('--torr', action='store_true', help='förbered och skriv uppdragen, starta ingen granskare')
    p.add_argument('--parallellt', type=int, default=2)
    p.add_argument('--modell', default=os.environ.get('NWP_GRANSKARE_MODELL') or 'opus[1m]')
    p.add_argument('--effort', default=os.environ.get('NWP_GRANSKARE_EFFORT') or 'high')
    p.add_argument('--frist', type=int, default=1500)
    p.add_argument('--ut', default=None, help='utdatakatalog (standard $NWP_FORSOK/kalibrering)')
    p.add_argument('--underlag', default=None, help=argparse.SUPPRESS)
    a = p.parse_args(argv)
    mal = Path(a.ut) if a.ut else G
    exempel = undanhallna(a.underlag)
    if not exempel:
        print('inga undanhållna exempel med dom och bilder (underlag/kalibrering/DOMAR.json, ANKARE.txt)')
        return 2
    mal.mkdir(parents=True, exist_ok=True)
    klara, att_kora = [], []
    for e in exempel:
        ut = mal / e['id']
        res = (gr.las_json(ut / 'svar.json') or {}).get('structured_output')
        if isinstance(res, dict) and isinstance(res.get('kriterier'), dict):
            klara.append(e)
            continue
        if ut.is_dir():
            shutil.rmtree(ut)
        ut.mkdir(parents=True)
        bilder, aria, ankare = forbered(e, ut, a.underlag)
        (ut / 'PROMPT.txt').write_text(uppdrag(e, ut, bilder, aria, ankare), encoding='utf-8')
        att_kora.append(e)
    print('undanhållna: %s; ankare: %d; redan klara: %d; att köra: %d' % (
        ', '.join('%s (%s)' % (e['id'], gr.KALIBRERING_NIVAER[e['niva']]) for e in exempel),
        sum(1 for x in gr.kalibreringsexempel(a.underlag) if x['ankare']), len(klara), len(att_kora)))
    if a.torr:
        print('Torrkörning: uppdragen ligger i %s. Ingen granskare startades.' % mal)
        return 0
    claude = shutil.which('claude') or str(Path.home() / '.local' / 'bin' / 'claude')
    with ThreadPoolExecutor(max_workers=max(1, a.parallellt)) as pool:
        for ident, sek in pool.map(lambda e: kor_en(e, mal / e['id'], a.modell, a.effort, a.frist, claude), att_kora):
            print('%s klar efter %d s' % (ident, sek), flush=True)
    svar = {e['id']: (gr.las_json(mal / e['id'] / 'svar.json') or {}).get('structured_output') for e in exempel}
    rader, s = jamfor(exempel, svar)
    f = rapport(rader, s, mal, a.modell, a.effort)
    print('Falska godkännanden: %d av %d · falska underkännanden: %d av %d · svar %d av %d · %s' % (
        s['falska_godkannanden'], s['av_ej_over'], s['falska_underkannanden'], s['av_over'], s['svar'], s['undanhallna'], f))
    return 0 if s['svar'] == s['undanhallna'] else 1


if __name__ == '__main__':
    sys.exit(main())
