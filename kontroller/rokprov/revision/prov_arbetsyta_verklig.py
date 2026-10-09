#!/usr/bin/env python3
"""Arbetsytans verkliga sessionsprov (etapp 2, 4 och 5 i ägarens uppdrag 2026-10-09): riktiga Claude-sessioner i ett
testprojekt (arbetsyta_fixtur.py, märkt testdata), startade genom motorns egen sessionsväg (atelje.session: --session-id,
förteckningen och observationen), så att arbetsytan ska hitta dem av sig själv. Körs för hand, inte i rökprovet: det kostar
riktiga modellanrop.

    .venv/bin/python -B kontroller/rokprov/revision/prov_arbetsyta_verklig.py <slug> arbete     # en utförare ändrar och bygger om
    .venv/bin/python -B kontroller/rokprov/revision/prov_arbetsyta_verklig.py <slug> stopprov   # en session som väntar tills den stoppas

Provet ersätter ateljéns orkestrering, inte dess delar: det skriver körningens status som arbetaren gör (läge valda, steg
forfina, egen pid, en post i startjournalen) och efter utförarens session kandidatens nya version som fotograferingen gör
(kod/, kod-src/ och versionshashen, utan skärmbilder). Sessionen, dess förteckningspost, transkriptet, observationen och
stoppvägen (prototyp.py --stoppa genom dashboardens POST) är motorns egna. Bara i en worktree eller tempkatalog, aldrig i
huvudutcheckningen, och bara för en kund märkt fiktiv.
"""
import calendar
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import atelje  # noqa: E402
import kandidater  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arbetsyta_fixtur  # noqa: E402


def nu():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def skriv(p, d):
    tmp = Path(str(p) + '.tmp%d' % os.getpid())
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    os.replace(tmp, p)


def main(slug, vad):
    if atelje.ROOT.resolve() == (Path.home() / 'nortropic-repos' / 'nortropic-webb-pro').resolve():
        raise SystemExit('provet körs aldrig i huvudutcheckningen')
    v = atelje.las_json(atelje.UNDERLAG / slug / 'VERKSAMHET.json') or {}
    if not v.get('fiktiv'):
        raise SystemExit('provet körs bara för en kund märkt fiktiv')
    rot = atelje.UNDERLAG / slug / 'atelje'
    st = atelje.las_json(rot / 'STATUS.json') or {}
    start_id = 'prov-%s-%s' % (vad, time.strftime('%H%M%S'))
    startad = nu()
    (atelje.UNDERLAG / slug / 'ateljestarter').mkdir(parents=True, exist_ok=True)
    skriv(atelje.UNDERLAG / slug / 'ateljestarter' / (start_id + '.json'), {'handling': 'valda', 'tid': startad, 'status': 'startad', 'pid': os.getpid(),
                                                                             'prov': 'arbetsytans verkliga sessionsprov'})
    st.update(lage='valda', steg='forfina', pid=os.getpid(), startad=startad, start_id=start_id, start_handling='valda', fel=None, klar=None,
              tider=dict(st.get('tider') or {}, forfina=startad))
    skriv(rot / 'STATUS.json', st)
    sajt = kandidater.ksajt(slug, 'k01')
    ut_rot = rot / 'kandidater' / 'k01'
    resultat = {'start_id': start_id, 'startad': startad}
    try:
        if vad == 'arbete':
            prompt = ('Du arbetar i ett testprojekt (fiktiv verksamhet, testdata). Projektets sajt ligger i %s.\n'
                      'Uppgift: ändra huvudrubriken (h1) i %s/src/pages/index.astro så att den lyder exakt: Reparationer i Testby. '
                      'Ändra inget annat. Bygg och fotografera sedan med flödets förhandsvisning, med Bash, exakt så här: '
                      '.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 '
                      '(npm och node är nekade; förhandsvisningen bygger innanför processgränsen). Svara med en mening om vad du ändrade '
                      'och om bygget gick igenom.' % (sajt, sajt, slug))
            svar = atelje.session(prompt, ['Read(//%s/**)' % str(sajt).strip('/'), 'Edit(//%s/src/**)' % str(sajt).strip('/'),
                                           'Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01)' % slug,
                                           'Bash(.venv/bin/python kontroller/forhandsvisa.py %s --kandidat k01 *)' % slug],
                                  ut_rot / 'svar-forfina-arbetsprov.json', max_turer=14, modell='claude-opus-5-5', effort='low', frist=900)
            resultat['svar'] = str(svar.get('result') or '')[:400]
            dist = sajt / 'dist' / 'index.html'  # resultatet räknas bara när bygget verkligen skrevs om efter starten, med den nya rubriken
            if not dist.is_file() or dist.stat().st_mtime < calendar.timegm(time.strptime(startad, '%Y-%m-%dT%H:%M:%SZ')) \
                    or 'Reparationer i Testby' not in dist.read_text(encoding='utf-8', errors='replace'):
                raise RuntimeError('bygget skrevs inte om med den nya rubriken (dist/index.html)')
            # fotograferingens del i provet: kandidatens kod och version ur projektet som det står nu
            for n in ('kod', kandidater.KODSRC):
                import shutil
                shutil.rmtree(ut_rot / n, ignore_errors=True)
            arbetsyta_fixtur._kopiera_kod(sajt, ut_rot, kandidater)
            ny = kandidater.version_av(ut_rot)
            ks = atelje.las_json(ut_rot / 'STATUS.json') or {}
            ks.update(status='forfinad', version=ny, fotograferad=nu(), skal='testdata: provets fotografering utan skärmbilder')
            skriv(ut_rot / 'STATUS.json', ks)
            resultat['version'] = ny[:12]
        elif vad == 'stopprov':
            svar = atelje.session('Kör kommandot sleep 240 med Bash-verktyget och svara sedan ordet klart. Gör inget annat.', ['Bash(sleep 240)'],
                                  ut_rot / 'svar-forfina-stopprov.json', max_turer=4, modell='claude-haiku-4-5-20251001', effort='low', frist=400)
            resultat['svar'] = str(svar.get('result') or '')[:200]
        else:
            raise SystemExit('okänt prov: %s' % vad)
        st = atelje.las_json(rot / 'STATUS.json') or st
        st.update(steg='klar_for_bedomning', klar=nu(), pid=None)
        resultat['utfall'] = 'klar'
    except Exception as e:  # noqa: BLE001 — ett stopp eller fel blir körningens fel, som hos arbetaren
        st = atelje.las_json(rot / 'STATUS.json') or st
        st.update(steg='fel', fel='%s: %s' % (type(e).__name__, str(e)[:300]), pid=None,
                  avbrott={'slag': 'stopp' if 'kod -' in str(e) or 'signal' in str(e) else 'fel', 'tid': nu(), 'steg': 'forfina'})
        resultat['utfall'] = 'fel: %s' % str(e)[:300]
    skriv(rot / 'STATUS.json', st)
    j = atelje.UNDERLAG / slug / 'ateljestarter' / (start_id + '.json')
    skriv(j, dict(atelje.las_json(j) or {}, status='slut', slut=nu(), slutkod=0 if resultat['utfall'] == 'klar' else 4))
    print(json.dumps(resultat, ensure_ascii=False))
    return 0 if resultat['utfall'] == 'klar' else 4


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
