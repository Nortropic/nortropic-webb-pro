#!/usr/bin/env python3
"""Ändringsflikens sessioner i dashboarden (ägarens tillägg 2026-10-11; kunskap/andringar.md): dashboarden är det betrodda
lagret som äger webbplatsens ändringsagent, en Claude Code-process i en PTY (dashboard/terminal.py) som motorn startar
med sina egna argument (kontroller/andringar.py). Klienten väljer aldrig program, katalog eller argument.

- En levande session per webbplats. Att öppna fliken ansluter till den eller visar hur den kan startas; den startas
  först när ägaren ber om det. Finns en levande process för webbplatsen ansluter en ny vy till den, aldrig en andra
  skrivare med samma sessions-id (partner.andra_processer prövar också processer utanför dashboarden).
- Inmatningsägaren: en vy (klient-id) i taget skriver, ändrar storlek och stoppar; en annan vy ser utdata och kan ta över
  uttryckligen. Mottagaren prövas på servern: webbplats, sessions-id och klient i varje anrop.
- Skrivägarskapet: kundens startlås (kontroller/flodesstart.py, samma som exporten, förhandsvisningen, releasen,
  aktiveringen och studion tar) hålls av dashboarden åt sessionen från ägarens meddelande (kroken UserPromptSubmit) till
  turens slut (Stop), och släpps när processen slutar. Mellan turerna blockerar en öppen terminal ingenting. Ett
  avbrutet svar (Ctrl-C) behåller låset tills nästa meddelande eller processens slut: hellre kvar än släppt mitt i ett
  verktygsanrop.
- Utdataströmmen kräver en biljett som bara ett skrivande anrop ger (nyckeln eller appens session), så att terminalens
  innehåll inte går att läsa för andra processer på maskinen med en vanlig GET.
"""
import base64
import fcntl
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kontroller'))
import terminal  # noqa: E402

LAS = threading.RLock()
SESSIONER = {}   # slug -> post: session, sid, token, startad, ny
SKRIVLAS = {}    # slug -> {'fd', 'sid', 'tid'}: kundens startlås, hållet åt agenten under en tur
BILJETTER = {}   # biljett -> {'slug', 'giltig_till'}
BILJETT_TID = 30 * 60
KLIENT = re.compile(r'^[A-Za-z0-9_-]{8,64}$')


class Inaktuell(Exception):
    """Vyn talar till en session eller ett läge som inte längre gäller."""


class Upptagen(Exception):
    """En annan vy äger inmatningen, eller kundens lås hålls av ett annat arbete."""


def _andringar():
    import andringar
    return andringar


def _nu():
    import atelje
    return atelje.nu()


def sessionsfil(slug):
    return _andringar().privat(slug) / 'SESSION.json'


def _las_post(slug):
    import atelje
    return atelje.las_json(sessionsfil(slug)) or {}


def _spara_post(slug, **falt):
    import atelje
    p = sessionsfil(slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    post = dict(_las_post(slug), **falt)
    atelje.skriv_json_atomiskt(p, post)
    return post


def logga(slug, handelse, **data):
    p = _andringar().privat(slug) / 'LOGG.jsonl'
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps(dict({'tid': _nu(), 'handelse': handelse}, **data), ensure_ascii=False) + '\n')
    except OSError:
        pass


def _synk(slug):
    """Arbetskopians läge mot fjärren ur det senast hämtade (repoväljaren; inget nät), för flikens huvud."""
    import repovaljare
    try:
        return repovaljare.arbetskopians_lage(slug)
    except (OSError, ValueError, RuntimeError):
        return None


def kvittoforsok(slug):
    """Det senaste kvitteringsförsöket som inte gick ({tid, skal}), om inget lyckats efter det: den automatiska
    kvitteringen efter turen går i en egen tråd, så att skälet annars bara stod i loggen."""
    p = _andringar().privat(slug) / 'LOGG.jsonl'
    if not p.is_file() or p.is_symlink():
        return None
    senast = None
    for rad in p.read_text(encoding='utf-8', errors='replace').splitlines()[-400:]:
        try:
            h = json.loads(rad)
        except ValueError:
            continue
        if h.get('handelse') == 'kvitterad':
            senast = None
        elif h.get('handelse') == 'kvitto_ej':
            senast = {'tid': h.get('tid'), 'skal': str(h.get('skal') or '')[:300]}
    return senast


def _levande(slug):
    s = SESSIONER.get(slug)
    return s if s and s['session'].lever else None


def lage(slug):
    """Flikens läge: webbplatsen ur förkontrollen, sessionen (levande, avslutad eller möjlig att återuppta), skrivlåset,
    den senaste kontrollen och de senaste ändringarna i arbetskopian."""
    a = _andringar()
    k = a.forkontroll(slug)
    w = k['webbplats']
    with LAS:
        s = SESSIONER.get(slug)
        post = _las_post(slug)
        las = SKRIVLAS.get(slug)
        if s:
            ses = {'lever': s['session'].lever, 'sid': s['sid'], 'startad': s['startad'], 'pid': s['session'].pid, 'slutkod': s['session'].slutkod,
                   'stoppad': bool(s['session'].stoppad), 'agare': s['session'].agare, 'offset': s['session'].slut_offset, 'ny': s['ny']}
        else:
            ses = {'lever': False, 'sid': post.get('sid'), 'startad': post.get('senast_startad')}
        if not ses['lever']:
            ses['kan_aterupptas'] = bool(post.get('sid') and a.SESSION.match(str(post.get('sid'))))
            ses['senast'] = post.get('lage')
    historik = []
    if w['arbetskopia_finns']:
        import kundrepo
        r = kundrepo.git(Path(w['arbetskopia']), *a.SAKER_GIT, 'log', '-12', '--format=%H%x1f%cI%x1f%s')
        for rad in r.stdout.splitlines():
            delar = rad.split('\x1f')
            if len(delar) == 3:
                historik.append({'commit': delar[0], 'tid': delar[1], 'text': delar[2][:200]})
    bygge = None
    dist = Path(w['arbetskopia']) / 'dist' / 'index.html'
    if w['arbetskopia_finns'] and dist.is_file() and not dist.is_symlink():
        bygge = {'tid': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(dist.stat().st_mtime))}
    redovisning = ''
    p = a.privat(slug) / 'ANDRINGAR.md'
    if p.is_file() and not p.is_symlink():
        redovisning = p.read_text(encoding='utf-8', errors='replace')[:6000]
    return {'slug': slug, 'namn': w['namn'], 'fiktiv': w['fiktiv'], 'repo': w['identitet']['namn'], 'fjarr': w.get('fjarr'),
            'gren': w.get('gren'), 'huvud': w.get('huvud'), 'lokala_andringar': w.get('lokala_andringar') or [],
            'export': w.get('export'), 'forhandsvisning': w.get('forhandsvisning'), 'produktion': w.get('produktion'),
            'arbetskopia_finns': w['arbetskopia_finns'], 'hinder': k['hinder'], 'fragor': k['fragor'], 'fakta': k['fakta'],
            'session': ses, 'skrivlas': {'halls': bool(las), 'sedan': (las or {}).get('tid')}, 'kontroll': a.senaste_kontroll(slug), 'bygge': bygge,
            'kvittering': dict(zip(('kan', 'skal'), kan_kvitteras(slug)), forsok=kvittoforsok(slug)) if w['arbetskopia_finns'] else None,
            'synk': _synk(slug) if w['arbetskopia_finns'] and not w['fiktiv'] else None,
            'historik': historik, 'redovisning': redovisning, 'modell': a.MODELL, 'tid': _nu()}


def starta(slug, port, klient, ateruppta=False, cols=120, rows=34):
    """Starta webbplatsens agent, eller anslut till den som lever. ateruppta: samma konversation (claude --resume) efter
    att processen slutat; annars en ny session med kunskapsunderlaget. Ger läget."""
    import korregister
    import partner
    a = _andringar()
    if not KLIENT.match(str(klient or '')):
        raise ValueError('vyn saknar sitt klient-id')
    with LAS:
        s = _levande(slug)
        if s:  # återanslutning: samma process, aldrig en andra
            if s['session'].agare is None:
                s['session'].agare = klient
            return lage(slug)
        k = a.forkontroll(slug)
        if k['hinder']:
            raise ValueError('; '.join(k['hinder']))
        post = _las_post(slug)
        if ateruppta:
            sid = str(post.get('sid') or '')
            if not a.SESSION.match(sid):
                raise Inaktuell('det finns ingen tidigare session att återuppta')
        else:
            sid = a.nytt_session_id()
        andra = partner.andra_processer(sid)
        if andra:
            raise Upptagen('en annan process skriver redan med sessionen (pid %s); stäng den först' % ', '.join(str(x['pid']) for x in andra))
        token = secrets.token_urlsafe(32)
        argv = a.kommando(slug, sid, not ateruppta, port, kontroll=k)
        env = a.miljo(slug, token, port)
        sess = terminal.Session(slug, argv, a.arbetskopia(slug), env, cols=cols, rows=rows, vid_slut=lambda x: _slut(slug, x))
        sess.agare = klient
        SESSIONER[slug] = {'session': sess, 'sid': sid, 'token': token, 'startad': _nu(), 'ny': not ateruppta}
        _spara_post(slug, sid=sid, senast_startad=SESSIONER[slug]['startad'], modell=a.MODELL, pid=sess.pid, lage='lever',
                    **({} if ateruppta else {'skapad': SESSIONER[slug]['startad']}))
        korregister.registrera('ändringsagenten', slug, pid=sess.pid)
        logga(slug, 'start', sid=sid, aterupptagen=bool(ateruppta), pid=sess.pid)
    import repovaljare
    repovaljare.spara_senast_for(slug)  # Senast öppnade i repoväljaren, utanför flikens lås (låsordningen: flikens först)
    return lage(slug)


def _slut(slug, sess):
    import korregister
    with LAS:
        s = SESSIONER.get(slug)
        if s and s['session'] is sess:
            _slapp_las(slug, s['sid'])
            _spara_post(slug, lage='avslutad', slutkod=sess.slutkod, avslutad=_nu(), stoppad=bool(sess.stoppad))
    korregister.avregistrera(sess.pid)
    logga(slug, 'slut', slutkod=sess.slutkod, stoppad=bool(sess.stoppad))


def _post(slug, sid, klient, agare=True):
    s = _levande(slug)
    if not s:
        raise Inaktuell('agenten lever inte; starta eller återuppta den')
    if not hmac.compare_digest(str(sid or ''), s['sid']):
        raise Inaktuell('vyn talar till en annan session än den som lever; läs om fliken')
    if agare and s['session'].agare != klient:
        raise Upptagen('en annan vy skriver i terminalen; ta över för att skriva här')
    return s


def skriv(slug, sid, klient, data):
    if not isinstance(data, str) or len(data) > 64 * 1024:
        raise ValueError('inmatningen ska vara text, högst 64 kB åt gången')
    with LAS:
        s = _post(slug, sid, klient)
    s['session'].skriv(data.encode('utf-8'))
    return {'ok': True}


def storlek(slug, sid, klient, cols, rows):
    with LAS:
        s = _post(slug, sid, klient)
    s['session'].storlek(int(cols), int(rows))
    return {'ok': True}


def ta_over(slug, sid, klient):
    if not KLIENT.match(str(klient or '')):
        raise ValueError('vyn saknar sitt klient-id')
    with LAS:
        s = _post(slug, sid, klient, agare=False)
        s['session'].agare = klient
    logga(slug, 'ta_over', klient=klient[:8])
    return {'ok': True, 'agare': klient}


def stoppa(slug, sid, klient):
    with LAS:
        s = _post(slug, sid, klient, agare=False)
    logga(slug, 'stopp', klient=str(klient or '')[:8])  # begäran först; processens slut loggas när den har slutat
    ok = s['session'].stoppa()
    return {'ok': ok}


def biljett(slug):
    """En biljett för utdataströmmen (EventSource kan inte bära nyckeln). Ges bara till ett skrivande anrop."""
    b = secrets.token_urlsafe(24)
    with LAS:
        nu = time.time()
        for k in [k for k, v in BILJETTER.items() if v['giltig_till'] < nu]:
            BILJETTER.pop(k, None)
        BILJETTER[b] = {'slug': slug, 'giltig_till': nu + BILJETT_TID}
    return {'biljett': b, 'giltig_sekunder': BILJETT_TID}


def biljett_ok(slug, b):
    with LAS:
        v = BILJETTER.get(str(b or ''))
        return bool(v and v['slug'] == slug and v['giltig_till'] >= time.time())


def las_fran(slug, offset, vanta=10.0):
    """(sessionens id, från, bytes, slut) för strömmen; None när ingen session finns i dashboarden."""
    with LAS:
        s = SESSIONER.get(slug)
    if not s:
        return None
    fran, data, slut = s['session'].las_fran(int(offset), vanta)
    return s['sid'], fran, data, slut


# --- krokarna (kontroller/andringar.py krok …, med sessionens token) ---

def _ta_las(slug, sid):
    import atelje
    import flodesstart
    hall = SKRIVLAS.get(slug)
    if hall and hall['sid'] == sid:
        return True
    if hall:  # en annan, äldre session för webbplatsen höll det: den lever inte längre
        _slapp_las(slug, hall['sid'])
    fil = flodesstart.lasfil(atelje.ROOT, slug)
    fil.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(fil, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return False
    SKRIVLAS[slug] = {'fd': fd, 'sid': sid, 'tid': _nu()}
    return True


def _slapp_las(slug, sid):
    hall = SKRIVLAS.get(slug)
    if hall and hall['sid'] == sid:
        try:
            os.close(hall['fd'])
        except OSError:
            pass
        SKRIVLAS.pop(slug, None)


def _andrat_sedan(slug, a):
    """Det som ändrats i arbetskopian sedan förra turens slut: nya commits och filer som ändrats utanför agenten."""
    import kundrepo
    post = _las_post(slug)
    r = a.arbetskopia(slug)
    rader = []
    huvud, bas = kundrepo.huvud(r), post.get('bas_huvud')
    if bas and huvud and bas != huvud:
        logg = kundrepo.git(r, *a.SAKER_GIT, 'log', '--format=%h %s', '%s..%s' % (bas, huvud)).stdout.strip().splitlines()
        rader.append('Nya commits sedan förra turen (%d): %s' % (len(logg), '; '.join(logg[:8]) or 'historiken har skrivits om'))
    trad, bas_trad = a.tradtillstand(r), post.get('bas_trad')
    if bas_trad and trad and bas_trad != trad:
        filer = kundrepo.git(r, *a.SAKER_GIT, 'diff', '--name-only', bas_trad, trad).stdout.split()
        if filer:
            rader.append('Filer som ändrats sedan förra turen (av någon annan än du, eller av en commit ovan): %s' % ', '.join(filer[:20]))
    return rader


TA_VANTA = 20  # sekunder som ett meddelande väntar på kundens lås (kvitteringen efter förra turen håller det en stund)
POST_LAS = threading.Lock()  # sessionsposten läses och skrivs om av flera trådar


def _spara_post_last(slug, **falt):
    with POST_LAS:
        return _spara_post(slug, **falt)


def krok(slug, token, handling, data):
    """Krokens anrop: ger svaret till kroken. Token måste vara den levande sessionens. Flikens lås (LAS) hålls bara när
    sessionen prövas och skrivlåset tas eller släpps; git-arbetet och väntan på kundens lås sker utanför det, så att
    andra webbplatsers krokar och tangenter aldrig väntar på den här (granskningen 2026-10-11)."""
    a = _andringar()
    with LAS:
        s = _levande(slug)
        if not s or not hmac.compare_digest(str(token or ''), s['token']):
            raise PermissionError('kroken hör inte till webbplatsens levande session')
        sid = s['sid']
    if handling == 'start':
        k = a.forkontroll(slug)
        rader = ['Läget i webbplatsens arbetskopia nu (motorns förkontroll):'] + ['- %s' % f for f in k['fakta']]
        rader += ['- fråga: %s' % f for f in k['fragor']] + ['- %s' % x for x in _andrat_sedan(slug, a)]
        kontroll = a.senaste_kontroll(slug)
        if kontroll:
            rader.append('- senaste kontrollen: %s %s (%s)' % ('godkänd' if kontroll.get('ok') else 'inte godkänd', kontroll.get('tid'),
                                                               '; '.join(kontroll.get('brister') or [])[:300] or 'inga brister'))
        logga(slug, 'krok_start', kalla=str((data or {}).get('kalla') or '')[:20])
        return {'ok': True, 'kontext': '\n'.join(rader)}
    if handling == 'ta':
        slut_ = time.monotonic() + TA_VANTA
        while True:
            with LAS:
                fick = _ta_las(slug, sid)
            if fick or time.monotonic() >= slut_:
                break
            time.sleep(0.5)
        if not fick:
            logga(slug, 'las_upptaget')
            return {'ok': False, 'skal': 'ett annat arbete för kunden (export, förhandsvisning, release, aktivering, kvittering eller en '
                                           'ändring i studion) håller kundens lås just nu; skriv meddelandet igen när det är klart'}
        try:
            import kundrepo
            rader = ['Skrivlåset för webbplatsen är ditt under den här turen.'] + _andrat_sedan(slug, a)
            _spara_post_last(slug, tur_start_huvud=kundrepo.huvud(a.arbetskopia(slug)))
        except Exception:
            with LAS:  # meddelandet stoppas; låset får inte bli kvar hos en tur som aldrig började
                _slapp_las(slug, sid)
            raise
        logga(slug, 'las_tagen')
        return {'ok': True, 'kontext': '\n'.join(rader)}
    if handling == 'prova':
        with LAS:
            hall = SKRIVLAS.get(slug)
        if not hall or hall['sid'] != sid:
            return {'ok': False, 'skal': 'skrivlåset är inte agentens just nu (turen har slutat eller ett annat arbete håller kundens lås)'}
        return {'ok': True}
    if handling in ('slapp', 'slut'):
        import kundrepo
        with LAS:
            _slapp_las(slug, sid)
        r = a.arbetskopia(slug)
        start = _las_post(slug).get('tur_start_huvud')
        huvud = kundrepo.huvud(r)
        _spara_post_last(slug, bas_huvud=huvud, bas_trad=a.tradtillstand(r), senaste_tur=_nu())
        logga(slug, 'las_slappt' if handling == 'slapp' else 'session_slut')
        if handling == 'slapp' and huvud and huvud != start:  # en ny commit i turen: kvittot görs efter svaret, utan att hålla kroken
            threading.Thread(target=_kvittera_tyst, args=(slug,), daemon=True).start()
        return {'ok': True}
    raise ValueError('okänd krok')


def kan_kvitteras(slug):
    """(ja, skäl): kan arbetskopians HEAD bli kundens leverabel (exportera.fran_andring)? Ett rent träd, en ny commit
    efter den senaste exporten och en godkänd kontroll av exakt HEAD:s träd."""
    import exportera
    import kundrepo
    a = _andringar()
    r = a.arbetskopia(slug)
    if not kundrepo.ar_repo(r):
        return False, 'ingen arbetskopia'
    if kundrepo.git(r, *a.SAKER_GIT, 'status', '--porcelain').stdout.strip():
        return False, 'arbetskopian har ändringar som inte är committade'
    e = exportera.aktuell(slug) or {}
    huvud = kundrepo.huvud(r)
    if e.get('commit') == huvud:
        return False, 'kvitterad' if e.get('kalla') == 'andring' else 'samma som exporten'
    if not e.get('ok') or not e.get('commit'):  # samma villkor som fran_andring, med dess skäl
        return False, e.get('fel') or 'ingen lyckad export att bygga vidare på'
    k = a.senaste_kontroll(slug) or {}
    if not k.get('ok') or k.get('tillstand') != kundrepo.git(r, *a.SAKER_GIT, 'rev-parse', 'HEAD^{tree}').stdout.strip():
        return False, 'provvägen har inte godkänt exakt den här versionen'
    return True, None


def kvittera(slug, push=True):
    """Den verifierade ändringen som kundens leverabel, under kundens lås (inte medan agenten arbetar, en export eller en
    förhandsvisning pågår). Ger kvittot."""
    import atelje
    import exportera
    import flodesstart
    with LAS:
        if slug in SKRIVLAS:
            raise Upptagen('agenten arbetar just nu; kvittera när turen är klar')
    try:
        with flodesstart.las(atelje.ROOT, slug):
            res = exportera.fran_andring(slug, push=push)
    except ValueError as e:
        if 'Ett arbete pågår' in str(e):
            raise Upptagen('ett annat arbete håller kundens lås; försök igen strax') from e
        raise
    pu = res.get('push') or {}
    logga(slug, 'kvitterad', export=res['id'], commit=res['commit'], pushad=pu.get('ok') if pu else None)
    return {'ok': True, 'export': res['id'], 'commit': res['commit'],
            'push': None if not pu else {'ok': bool(pu.get('ok')), 'fel': pu.get('fel') or pu.get('hinder')}}


def _kvittera_tyst(slug):
    ja, skal = kan_kvitteras(slug)
    if not ja:
        logga(slug, 'kvitto_ej', skal=skal)
        return
    try:
        kvittera(slug, push=False)  # efter turen: kvitteras lokalt; pushen till fjärrepot är Johnnys handling
    except Exception as e:  # noqa: BLE001 — en egen tråd: felet ska stå i loggen och vyn, inte bara i serverns stderr
        logga(slug, 'kvitto_ej', skal=str(e)[:300])


def ta_in(slug):
    """Kundrepots ändringar in i sajten (andringar.ta_in_i_sajten), inte medan agenten arbetar."""
    with LAS:
        if slug in SKRIVLAS:
            raise Upptagen('agenten arbetar just nu; ta in ändringarna när turen är klar')
    try:
        ut = _andringar().ta_in_i_sajten(slug)
    except ValueError as e:
        if 'Ett arbete pågår' in str(e):
            raise Upptagen('ett annat arbete håller kundens lås; försök igen strax') from e
        raise
    logga(slug, 'intaget_i_sajten', intaget=len(ut['intaget']), konflikter=len(ut['konflikter']), genereras=len(ut['genereras']))
    return ut


def bilaga(slug, namn, data_b64):
    """En bilaga till webbplatsens uppdrag i den privata katalogen (bilagor/): bild (PNG, JPEG, WebP, GIF, SVG), PDF eller
    text, högst 20 MB. Ger sökvägen som agenten kan läsa."""
    a = _andringar()
    namn = re.sub(r'[^A-Za-z0-9._-]+', '-', str(namn or 'bilaga')).strip('.-')[:80] or 'bilaga'
    try:
        data = base64.b64decode(str(data_b64 or ''), validate=True)
    except ValueError as e:
        raise ValueError('bilagan ska vara base64') from e
    if not data or len(data) > 20 * 1024 * 1024:
        raise ValueError('bilagan ska vara 1 byte till 20 MB')
    signaturer = (b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff', b'RIFF', b'GIF87a', b'GIF89a', b'%PDF-')
    text = False
    if not data.startswith(signaturer):
        try:
            data.decode('utf-8')
            text = True
        except UnicodeDecodeError:
            raise ValueError('bilagan ska vara en bild (PNG, JPEG, WebP, GIF, SVG), en PDF eller text') from None
    if namn.lower().endswith('.svg') and b'<script' in data.lower():
        raise ValueError('en SVG med skript tas inte emot')
    d = a.forbered_privat(slug) / 'bilagor'
    mal = d / ('%s-%s' % (time.strftime('%Y%m%d-%H%M%S'), namn))
    i = 1
    while mal.exists():
        i += 1
        mal = d / ('%s-%d-%s' % (time.strftime('%Y%m%d-%H%M%S'), i, namn))
    mal.write_bytes(data)
    logga(slug, 'bilaga', fil=mal.name, storlek=len(data), text=text)
    return {'ok': True, 'sokvag': str(mal), 'namn': mal.name, 'storlek': len(data)}


def diff(slug):
    """Arbetskopians ändringar för sidopanelen: arbetsträdet mot HEAD, och commits sedan produktionen (eller sedan
    exporten när produktionen inte är känd), som text. Ändrar ingenting."""
    import kundrepo
    a = _andringar()
    r = a.arbetskopia(slug)
    if not kundrepo.ar_repo(r):
        return {'finns': False}
    w = a.webbplats(slug)
    bas = (w.get('produktion') or {}).get('commit') or (w.get('export') or {}).get('commit')
    trad = kundrepo.git(r, *a.SAKER_GIT, 'diff', '--stat', '--patch', '--no-color', 'HEAD').stdout
    # nya filer som inte är spårade syns inte i diff mot HEAD: de listas för sig (huvudets räknare tar med dem)
    nya = [x for x in kundrepo.git(r, *a.SAKER_GIT, 'ls-files', '--others', '--exclude-standard', '-z').stdout.split('\0') if x]
    if nya:
        trad = 'Nya filer, inte spårade (%d):\n%s\n\n%s' % (len(nya), '\n'.join('  ' + x for x in nya[:200]), trad)
    sedan = kundrepo.git(r, *a.SAKER_GIT, 'log', '--format=%h %cI %s', '%s..HEAD' % bas).stdout if bas else ''
    return {'finns': True, 'huvud': w.get('huvud'), 'bas': bas, 'bas_slag': 'produktionen' if (w.get('produktion') or {}).get('commit') else 'exporten',
            'arbetstrad': trad[:200000], 'avkortad': len(trad) > 200000, 'nya_filer': nya[:200], 'commits_sedan_bas': [x for x in sedan.splitlines() if x][:100]}


def stang_alla():
    """Dashboardens avslut: varje levande agent stoppas med processkontrollen och låsen släpps."""
    with LAS:
        poster = list(SESSIONER.items())
    for slug, s in poster:
        if s['session'].lever:
            s['session'].stoppa(frist=3)
        _slapp_las(slug, s['sid'])
