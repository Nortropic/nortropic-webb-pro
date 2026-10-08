#!/usr/bin/env python3
"""korvakt.py — helbyggets processvakt (granskningen GR-20261007-r101-om, BÖR 1, BÖR 2, KAN 2 och KAN 5).

kor.sh startar vakten när körningen fått sin identitet (START.json). Vakten lever i en egen session, utanför kor.sh:s
processgrupp, så att varken Ctrl-C, en signal till gruppen eller SIGKILL mot kor.sh når den. Den följer varje process som
kor.sh och bygget startar genom processernas unika id: macOS behåller förälderns unika id (p_puniqueid) när en process
byter förälder eller lämnar sin session (setsid). En process vars förälder vakten har sett hör alltså till körningen,
också när föräldern redan har avslutats. Vakten skannar processtabellen när en följd process förgrenar sig (kqueue,
NOTE_FORK) och annars varje halvsekund.

    kor.sh: korvakt.py --kor-pid <pid> --root <repo> --kund <kunder/slug> --korning <körning> --las <kunder/.bygge-pid>
                       --domlogg <fil> --domfil <fil> --fore <hashlista> --efter <hashlista> [--frist <s>]

kor.sh skriver en rad i taget på vaktens stdin, och vakten svarar på stdout:
- fore <sha256>, efter <sha256>, domstart <sha256|saknas>: hashlistorna och DOM.json vid starten, ur kor.sh:s minne;
- claude <pid>, wt <pid>: byggets session och webbtjänsten, de träd som stoppas;
- stoppa: en signal kom under bygget; träden får SIGTERM direkt (claudes processgrupp också) och SIGKILL efter fristen;
- slut <claudes kod>: samma stopp, och svaret är en JSON-rad med de stoppade processerna och de som finns kvar;
- bekrafta <sha256>: korslut skrev en färdig post; hashen binds till vaktens minne, aldrig till ett fält i posten;
- bekraftad: svarar med den oförändrade postens bekräftade hash, eller obekraftad;
- klar: kor.sh har gjort sitt avslut; vakten avslutas.
Vakten svarar "redo <pid>" när den följer kor.sh.

Dör kor.sh utan att ha skickat klar (SIGKILL eller krasch) stoppar vakten alla kor.sh:s processer och gör avslutet:
- efter bygget: hashlistan efter körningen med kor.sh:s egna funktioner (NWP_VAKT_SKYDDAT, lästa när kor.sh startade)
  och slutposten med korslut.py (slutkod 4, avbruten: kor.sh dog utan avslut);
- före bygget: en kort post (korslut.py --stopp).
En redan skriven post bevaras bara när korslut bekräftat dess hash genom det privata röret. Annars bevaras den som
SLUT-obestyrkt-<id>.json och avslutet räknas om. Byggsessionen och webbtjänsten ärver inte röret.
Sedan släpper vakten låsen: flaggan uchg på kunder/, underlag/, domloggen och DOM.json, och kunder/.bygge-pid. Under
avslutet håller vakten låset med sin egen pid, så att ingen ny körning startar förrän det är klart.

Gränsen: en process som startas utanför trädet (via launchd), en process som hinner byta förälder två gånger innan vakten
sett den mellersta, och ett eget skript som dödar vakten eller ändrar kontrollerna når förbi vakten. Det är gränsen på
processnivå (sandlådan, ett eget steg i backloggen).
"""
import argparse
import ctypes
import hashlib
import json
import os
import select
import signal
import stat
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

SZOMB = 5  # p_stat för en process som avslutats men inte skördats
PROC_PIDT_SHORTBSDINFO, PROC_PIDUNIQIDENTIFIERINFO = 13, 17
FRIST = 10  # sekunder mellan SIGTERM och SIGKILL (NWP_FRIST)

_lp = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
_lp.proc_listallpids.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lp.proc_pidinfo.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]


class _Uniq(ctypes.Structure):  # struct proc_uniqidentifierinfo (sys/proc_info.h)
    _fields_ = [('p_uuid', ctypes.c_uint8 * 16), ('p_uniqueid', ctypes.c_uint64), ('p_puniqueid', ctypes.c_uint64),
                ('p_idversion', ctypes.c_int32), ('p_reserve2', ctypes.c_uint32), ('p_reserve3', ctypes.c_uint64),
                ('p_reserve4', ctypes.c_uint64)]


class _Kort(ctypes.Structure):  # struct proc_bsdshortinfo (sys/proc_info.h)
    _fields_ = [('pid', ctypes.c_uint32), ('ppid', ctypes.c_uint32), ('pgid', ctypes.c_uint32), ('status', ctypes.c_uint32),
                ('comm', ctypes.c_char * 16), ('flags', ctypes.c_uint32), ('uid', ctypes.c_uint32), ('gid', ctypes.c_uint32),
                ('ruid', ctypes.c_uint32), ('rgid', ctypes.c_uint32), ('svuid', ctypes.c_uint32), ('svgid', ctypes.c_uint32),
                ('rfu', ctypes.c_uint32)]


class Proc:
    __slots__ = ('pid', 'uid', 'puid', 'pgid', 'zombie', 'namn')

    def __init__(self, pid, uid, puid, pgid, zombie, namn):
        self.pid, self.uid, self.puid, self.pgid, self.zombie, self.namn = pid, uid, puid, pgid, zombie, namn


def nu():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def logga(text):
    try:
        sys.stderr.write('%s %s\n' % (nu(), text))
        sys.stderr.flush()
    except (OSError, ValueError):
        pass


def alla_pid():
    n = _lp.proc_listallpids(None, 0)
    if n <= 0:
        return []
    buf = (ctypes.c_int * (n + 1024))()
    n = _lp.proc_listallpids(buf, ctypes.sizeof(buf))
    return [buf[i] for i in range(max(n, 0)) if buf[i] > 0]


def las_process(pid):
    """Processen med pid, eller None när den inte finns eller inte går att läsa."""
    u = _Uniq()
    if _lp.proc_pidinfo(pid, PROC_PIDUNIQIDENTIFIERINFO, 0, ctypes.byref(u), ctypes.sizeof(u)) != ctypes.sizeof(u):
        return None
    k = _Kort()
    if _lp.proc_pidinfo(pid, PROC_PIDT_SHORTBSDINFO, 0, ctypes.byref(k), ctypes.sizeof(k)) != ctypes.sizeof(k):
        return None
    return Proc(pid, u.p_uniqueid, u.p_puniqueid, k.pgid, k.status == SZOMB, k.comm.decode('utf-8', 'replace'))


class Trad:
    """Processerna under kor.sh, följda med unika id. foralder: unikt id -> förälderns unika id, också för processer som
    avslutats, så att en ättling vars förälder dött hittas."""

    def __init__(self, rot):
        self.rot = rot.uid
        self.foralder = {rot.uid: None}
        self.namn = {rot.uid: rot.namn}
        self.levande = {rot.uid: rot}

    def skanna(self):
        """Läser processtabellen och ger de processer som tillkommit i trädet sedan förra skanningen."""
        alla = [p for p in (las_process(x) for x in alla_pid()) if p]
        nya, andrat = [], True
        while andrat:  # en förälder kan stå efter sitt barn i listan
            andrat = False
            for p in alla:
                if p.uid not in self.foralder and p.puid in self.foralder:
                    self.foralder[p.uid] = p.puid
                    self.namn[p.uid] = p.namn
                    nya.append(p)
                    andrat = True
        self.levande = {p.uid: p for p in alla if p.uid in self.foralder and not p.zombie}
        return nya

    def under(self, rotter, utom=()):
        """De levande processerna under någon av rotterna (unika id), rotterna medräknade, utom de under utom."""
        ut = []
        for u, p in self.levande.items():
            x = u
            while x is not None and x not in rotter and x not in utom:
                x = self.foralder.get(x)
            if x is not None and x in rotter:
                ut.append(p)
        return ut


def signalera(p, sig):
    """Skickar sig till p, bara om pid:en fortfarande är samma process (samma unika id)."""
    q = las_process(p.pid)
    if not q or q.uid != p.uid or q.zombie:
        return False
    try:
        os.kill(p.pid, sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def sha_fil(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).is_file() and not Path(p).is_symlink() else None
    except OSError:
        return None


class Vakt:
    def __init__(self, a):
        self.a = a
        self.frist = a.frist
        self.kor_pid = a.kor_pid
        self.fore = self.efter = self.domstart = None
        self.rc = None
        self.claude = self.wt = None  # Proc
        self.klar = False
        self.publicerad_sha = None  # enbart bekräftad av korslut genom kor.sh:s privata rör
        self.stoppade = {}  # unikt id -> {pid, namn, signal}
        self.egen = None
        self.kq = select.kqueue()
        self.rest = b''

    # --- följningen ---
    def folj(self, procs):
        for p in procs:
            try:
                self.kq.control([select.kevent(p.pid, select.KQ_FILTER_PROC, select.KQ_EV_ADD,
                                               select.KQ_NOTE_FORK | select.KQ_NOTE_EXIT)], 0, 0)
            except OSError:
                pass  # avslutad redan; skanningen ser dess barn genom det unika id:t

    def skanna(self):
        self.folj(self.trad.skanna())

    def rotter_bygge(self):
        return {p.uid for p in (self.claude, self.wt) if p}

    def stoppa(self, rotter, utom=(), grupper=()):
        """SIGTERM till träden under rotterna (och till processgrupperna), SIGKILL efter fristen, och sedan letar vakten
        tills ingen process finns kvar. Ger {'stoppade', 'kvar', 'frist'}."""
        egen_grupp = os.getpgid(0)

        def grupp(sig):
            for g in grupper:
                if g and g > 1 and g != egen_grupp:
                    try:
                        os.killpg(g, sig)
                    except (ProcessLookupError, PermissionError):
                        pass
        slut = time.time() + self.frist
        grupp(signal.SIGTERM)
        while True:
            self.skanna()
            mal = self.trad.under(rotter, utom)
            if not mal:
                break
            for p in mal:
                if p.uid not in self.stoppade and signalera(p, signal.SIGTERM):
                    self.stoppade[p.uid] = {'pid': p.pid, 'namn': p.namn, 'signal': 'TERM'}
            if time.time() >= slut:
                break
            time.sleep(0.1)
        for _ in range(100):
            self.skanna()
            mal = self.trad.under(rotter, utom)
            if not mal:
                break
            grupp(signal.SIGKILL)
            for p in mal:
                if signalera(p, signal.SIGKILL):
                    self.stoppade.setdefault(p.uid, {'pid': p.pid, 'namn': p.namn})['signal'] = 'KILL'
            time.sleep(0.1)
        self.skanna()
        kvar = [{'pid': p.pid, 'namn': p.namn} for p in self.trad.under(rotter, utom)]
        return {'stoppade': sorted(self.stoppade.values(), key=lambda x: x['pid']), 'kvar': kvar, 'frist': self.frist,
                'foljda': len(self.trad.foralder)}

    def stoppa_bygget(self):
        grupper = [p.pid for p in (self.claude,) if p and p.pgid == p.pid]  # claude startas i en egen session
        return self.stoppa(self.rotter_bygge(), grupper=grupper)

    # --- kor.sh:s rader ---
    def rad(self, rad):
        delar = rad.strip().split()
        if not delar:
            return
        kmd, arg = delar[0], delar[1:]
        if kmd in ('fore', 'efter', 'domstart') and arg:
            setattr(self, kmd, arg[0])
        elif kmd in ('claude', 'wt') and arg and arg[0].isdigit():
            self.skanna()
            p = las_process(int(arg[0]))
            if p and p.uid in self.trad.foralder:  # bara en process ur kor.sh:s träd
                setattr(self, kmd, p)
            logga('%s %s %s' % (kmd, arg[0], 'följs' if getattr(self, kmd) else 'hittades inte i kor.sh:s träd'))
        elif kmd == 'stoppa':
            r = self.stoppa_bygget()
            logga('stoppa: %d stoppade, %d kvar' % (len(r['stoppade']), len(r['kvar'])))
        elif kmd == 'slut':
            self.rc = arg[0] if arg else None
            r = self.stoppa_bygget()
            logga('slut: %d stoppade, %d kvar' % (len(r['stoppade']), len(r['kvar'])))
            self.svara(json.dumps(r, ensure_ascii=False))
        elif kmd == 'bekrafta' and len(arg) == 1:
            post = Path(self.a.kund) / 'korningar' / self.a.korning / 'SLUT.json'
            if len(arg[0]) == 64 and sha_fil(post) == arg[0]:
                self.publicerad_sha = arg[0]
        elif kmd == 'bekraftad':
            post = Path(self.a.kund) / 'korningar' / self.a.korning / 'SLUT.json'
            self.svara('bekraftad ' + self.publicerad_sha if self.publicerad_sha and sha_fil(post) == self.publicerad_sha else 'obekraftad')
        elif kmd == 'klar':
            self.klar = True

    def svara(self, text):
        try:
            sys.stdout.write(text + '\n')
            sys.stdout.flush()
        except (OSError, ValueError):
            pass

    def las_rader(self):
        """Läser det som finns på stdin; ger False vid EOF."""
        try:
            data = os.read(0, 65536)
        except BlockingIOError:
            return True
        except OSError:
            return False
        if not data:
            return False
        self.rest += data
        while b'\n' in self.rest:
            r, self.rest = self.rest.split(b'\n', 1)
            self.rad(r.decode('utf-8', 'replace'))
        return True

    # --- avslutet när kor.sh dött ---
    def efterlista(self):
        """Hashlistan efter körningen med kor.sh:s egna funktioner skyddat() och grans(), lästa ur kor.sh:s minne när
        vakten startade (NWP_VAKT_SKYDDAT). Ger (sha256, fel)."""
        funk = os.environ.get('NWP_VAKT_SKYDDAT') or ''
        if 'skyddat ()' not in funk or 'grans ()' not in funk:
            return None, 'kor.sh:s funktioner saknas (NWP_VAKT_SKYDDAT)'
        kod = funk + '\nset -o pipefail\ncd "$ROOT" || exit 1\n{ skyddat; grans; }\n'
        try:
            r = subprocess.run(['/bin/bash', '-c', kod], capture_output=True, timeout=600, cwd=str(self.a.root),
                               env=dict(os.environ, ROOT=str(self.a.root), SLUG=Path(self.a.kund).name))
        except (OSError, subprocess.SubprocessError) as e:
            return None, 'hashlistan efter körningen gick inte att räkna: %s' % e
        efter = Path(self.a.efter)
        try:
            if efter.is_symlink() or efter.exists():
                efter.unlink()
            efter.write_bytes(r.stdout)
        except OSError as e:
            return None, 'hashlistan efter körningen gick inte att skriva: %s' % e
        return hashlib.sha256(r.stdout).hexdigest(), None if r.returncode == 0 else 'skyddat/grans gav kod %d' % r.returncode

    def ta_laset(self):
        las = Path(self.a.las)
        try:
            if not las.is_symlink() and las.read_text().strip() == str(self.kor_pid):
                las.write_text('%d\n' % os.getpid())
        except OSError:
            pass

    def slapp_lasen(self):
        for p in (self.a.domfil, self.a.domlogg, Path(self.a.domlogg).with_name('DESIGNDOMAR-belagg.jsonl'),
                  Path(self.a.kund).parent, Path(self.a.root) / 'underlag'):
            try:
                st = os.lstat(p)
                if not stat.S_ISLNK(st.st_mode) and st.st_flags & stat.UF_IMMUTABLE:
                    os.chflags(p, st.st_flags & ~stat.UF_IMMUTABLE)
            except OSError:
                pass
        las = Path(self.a.las)
        try:
            if not las.is_symlink() and las.read_text().strip() in (str(self.kor_pid), str(os.getpid())):
                las.unlink()
        except OSError:
            pass
        try:
            subprocess.run([str(Path(self.a.root) / '.venv' / 'bin' / 'python'), '-B', str(Path(self.a.root) / 'kontroller' / 'korregister.py'),
                            'ut', '--pid', str(self.kor_pid)], capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass

    def avslut_efter_dod(self):
        logga('kor.sh (pid %d) dog utan avslut; vakten stoppar körningens processer och gör avslutet' % self.kor_pid)
        self.ta_laset()
        r = self.stoppa({self.trad.rot}, utom={self.egen.uid}, grupper=[p.pid for p in (self.claude,) if p and p.pgid == p.pid])
        logga('stoppade %d, kvar %d' % (len(r['stoppade']), len(r['kvar'])))
        kund, korning = Path(self.a.kund), self.a.korning
        py = str(Path(self.a.root) / '.venv' / 'bin' / 'python')
        korslut = str(Path(self.a.root) / 'kontroller' / 'korslut.py')
        post = kund / 'korningar' / korning / 'SLUT.json'
        try:
            if self.publicerad_sha and sha_fil(post) == self.publicerad_sha:
                logga('slutposten är bekräftad av korslut och oförändrad; bara låsen släpps')
            elif self.fore:
                efter_sha = self.efter if self.efter and sha_fil(self.a.efter) == self.efter else None
                fel = None
                if not efter_sha:
                    efter_sha, fel = self.efterlista()
                self.bevara_obestyrkt(post)  # efter mätningen: planteringen ska synas i skyddskontrollen
                env = dict(os.environ, NWP_AVBRUTEN='KORSH', NWP_SKYDDAT_SHA256='%s %s' % (self.fore, efter_sha or 'saknas'),
                           NWP_PROCESSER=json.dumps(r, ensure_ascii=False), NWP_DOM_START_SHA256=self.domstart or '')
                if fel:
                    env['NWP_EFTER_FEL'] = fel
                p = subprocess.run([py, '-B', korslut, str(kund), self.rc or 'okänd', self.a.fore, self.a.efter, korning], env=env,
                                   capture_output=True, text=True, timeout=900)
                logga('korslut gav slutkod %d\n%s%s' % (p.returncode, p.stdout[-4000:], p.stderr[-2000:]))
            else:
                self.bevara_obestyrkt(post)
                p = subprocess.run([py, '-B', korslut, '--stopp', str(kund), korning,
                                    'kor.sh dog före bygget utan avslut (SIGKILL eller krasch); vakten stoppade dess processer och skrev posten'],
                                   capture_output=True, text=True, timeout=300, env=dict(os.environ, NWP_AVBRUTEN='KORSH'))
                logga('korslut --stopp gav %d\n%s%s' % (p.returncode, p.stdout[-2000:], p.stderr[-2000:]))
        except (OSError, subprocess.SubprocessError) as e:
            logga('avslutet föll: %s' % e)
        finally:
            self.slapp_lasen()
            logga('låsen släppta')

    def bevara_obestyrkt(self, post):
        """Filen ensam bevisar inget avslut. Bevara den utan att följa länkar, före omräkningen."""
        kund = Path(self.a.kund)
        for p in (kund, kund / 'korningar', post.parent):
            if p.is_symlink() or not p.is_dir():
                raise OSError('slutpostens katalog kan inte förankras: %s' % p)
        if post.exists() or post.is_symlink():
            os.rename(post, post.with_name('SLUT-obestyrkt-%s.json' % uuid.uuid4().hex))
            logga('obekräftad slutpost bevarad separat; körningens utfall räknas om')

    # --- huvudslingan ---
    def kor(self):
        try:
            os.setsid()
        except OSError:
            pass
        for s in (signal.SIGHUP, signal.SIGINT):
            signal.signal(s, signal.SIG_IGN)
        for namn in ('.vakt-in', '.vakt-ut'):  # rören är öppna i båda ändarna; ingen annan ska kunna öppna dem
            p = Path(self.a.kund) / 'korningar' / self.a.korning / namn
            try:
                if stat.S_ISFIFO(os.lstat(p).st_mode):
                    p.unlink()
            except OSError:
                pass
        rot = las_process(self.kor_pid)
        self.egen = las_process(os.getpid())
        if not rot or not self.egen:
            logga('kor.sh (pid %d) går inte att följa' % self.kor_pid)
            return 1
        self.trad = Trad(rot)
        dod = False
        try:
            self.kq.control([select.kevent(self.kor_pid, select.KQ_FILTER_PROC, select.KQ_EV_ADD, select.KQ_NOTE_EXIT | select.KQ_NOTE_FORK)], 0, 0)
        except OSError:
            dod = True
        self.kq.control([select.kevent(0, select.KQ_FILTER_READ, select.KQ_EV_ADD)], 0, 0)
        self.skanna()
        self.svara('redo %d' % os.getpid())
        logga('vakten följer kor.sh (pid %d), körningen %s' % (self.kor_pid, self.a.korning))
        senast = time.time()
        while not self.klar and not dod:
            skanna = False
            for e in self.kq.control(None, 64, 0.5):
                if e.filter == select.KQ_FILTER_READ and e.ident == 0:
                    if not self.las_rader():
                        try:  # EOF: kor.sh stängde röret; dödsfallet syns som NOTE_EXIT
                            self.kq.control([select.kevent(0, select.KQ_FILTER_READ, select.KQ_EV_DELETE)], 0, 0)
                        except OSError:
                            pass
                elif e.filter == select.KQ_FILTER_PROC:
                    if e.ident == self.kor_pid and e.fflags & select.KQ_NOTE_EXIT:
                        dod = True
                    if e.fflags & select.KQ_NOTE_FORK:
                        skanna = True
            if skanna or time.time() - senast >= 0.5:
                self.skanna()
                senast = time.time()
        if dod and not self.klar:  # det kor.sh hann skriva före döden, till exempel klar
            os.set_blocking(0, False)
            while select.select([0], [], [], 0)[0] and self.las_rader():
                pass
        if not self.klar:
            self.avslut_efter_dod()
        return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    for namn in ('--root', '--kund', '--korning', '--las', '--domlogg', '--domfil', '--fore', '--efter'):
        p.add_argument(namn, required=True)
    p.add_argument('--kor-pid', type=int, required=True)
    p.add_argument('--frist', type=int, default=int(os.environ.get('NWP_FRIST') or FRIST))
    a = p.parse_args(argv)
    return Vakt(a).kor()


if __name__ == '__main__':
    sys.exit(main())
