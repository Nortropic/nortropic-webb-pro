#!/usr/bin/env python3
"""Ändringsflikens terminal (ägarens tillägg 2026-10-11; kunskap/andringar.md): en riktig PTY med en Claude Code-process
som dashboarden äger, det betrodda lagret. Klienten (xterm.js i portalen) får utdata som bytes med löpande offset och
skickar tangenter, storlek och stopp; den kan aldrig starta något annat än det kommando som motorn själv byggt
(kontroller/andringar.py), och när processen slutar finns ingen terminal kvar att skriva i: ingen shell tar över.

Processen startas genom en egen, enkeltrådad startare (det här skriptet med --starta), som gör PTY:n till processens
styrande terminal (setsid och TIOCSCTTY) innan den byter till kommandot. Dashboarden är flertrådad och gör därför ingen
fork med Python-kod själv. Utdata hålls i en ringbuffert (BUFFERT byte) med absoluta offset, så att en vy som tappar
förbindelsen eller öppnas igen fortsätter där den var, eller ritas om från bufferten när luckan är äldre än den.
Processträdet följs med korvakt.Trad (unika process-id), så att stoppet når agentens barn också när de bytt
processgrupp.

    python3 -I -B dashboard/terminal.py --starta <arbetskatalog> -- <kommando> [argument …]   (bara för Session)
"""
import os
import select
import signal
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

BUFFERT = 4 * 1024 * 1024
STARTARE = Path(__file__).resolve()


def _storlek(fd, cols, rows):
    import fcntl
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', max(2, min(int(rows), 500)), max(10, min(int(cols), 1000)), 0, 0))


class Session:
    """En PTY-session. argv körs i cwd med env (inget av klientens val: motorn bygger dem). vid_slut(session) anropas en
    gång när processen har slutat och all utdata är läst."""

    def __init__(self, nyckel, argv, cwd, env, cols=120, rows=34, vid_slut=None):
        import pty
        self.nyckel = nyckel
        self.argv = list(argv)
        self.cwd = str(cwd)
        self.startad = time.time()
        self.slutkod = None
        self.slutad = None
        self.stoppad = None
        self.agare = None  # klientens id som får skriva (inmatningsägaren)
        self._vid_slut = vid_slut
        self._buf = bytearray()
        self._bas = 0
        self._cond = threading.Condition()
        master, slave = pty.openpty()
        _storlek(slave, cols, rows)
        try:
            self.proc = subprocess.Popen([sys.executable, '-I', '-B', str(STARTARE), '--starta', self.cwd, '--', *self.argv], env=env,
                                         stdin=slave, stdout=slave, stderr=slave, close_fds=True)
        except BaseException:
            os.close(master)
            os.close(slave)
            raise
        os.close(slave)
        os.set_blocking(master, False)
        self.fd = master
        self.pid = self.proc.pid
        self.trad = None
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kontroller'))
            import korvakt
            p = korvakt.las_process(self.pid)
            self.trad = korvakt.Trad(p) if p else None
        except Exception:  # noqa: BLE001 — utan trädet stoppas processgruppen
            self.trad = None
        threading.Thread(target=self._las, daemon=True, name='terminal-%s' % nyckel).start()

    # --- utdata ---
    def _las(self):
        senast_skanning = 0.0
        while True:
            try:
                r, _w, _x = select.select([self.fd], [], [], 1.0)
            except (OSError, ValueError):
                break
            if self.trad and time.monotonic() - senast_skanning > 2:
                senast_skanning = time.monotonic()
                try:
                    self.trad.skanna()
                except Exception:  # noqa: BLE001
                    pass
            if not r:
                if self.proc.poll() is not None:
                    break
                continue
            try:
                data = os.read(self.fd, 65536)
            except BlockingIOError:
                continue
            except OSError:  # EIO: slavsidan är stängd, processen har slutat
                break
            if not data:
                break
            with self._cond:
                self._buf += data
                if len(self._buf) > BUFFERT:
                    over = len(self._buf) - BUFFERT
                    del self._buf[:over]
                    self._bas += over
                self._cond.notify_all()
        try:
            self.slutkod = self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.slutkod = None
        with self._cond:
            self.slutad = time.time()
            self._cond.notify_all()
        try:
            os.close(self.fd)
        except OSError:
            pass
        if self._vid_slut:
            try:
                self._vid_slut(self)
            except Exception:  # noqa: BLE001
                pass

    @property
    def slut_offset(self):
        with self._cond:
            return self._bas + len(self._buf)

    @property
    def lever(self):
        return self.slutad is None

    def las_fran(self, offset, vanta=25.0):
        """(från, bytes, slutat): utdata från offset; väntar högst vanta sekunder på något nytt. En offset som bufferten
        redan släppt ger det som finns kvar, från buffertens början (vyn ritar om)."""
        slut = time.monotonic() + vanta
        with self._cond:
            while True:
                hela = self._bas + len(self._buf)
                if offset < hela or self.slutad is not None:
                    fran = max(offset, self._bas)
                    return fran, bytes(self._buf[fran - self._bas:]), self.slutad is not None
                kvar = slut - time.monotonic()
                if kvar <= 0:
                    return offset, b'', False
                self._cond.wait(kvar)

    # --- inmatning ---
    def skriv(self, data):
        if self.slutad is not None:
            raise ProcessLookupError('agenten har avslutats; ingen terminal finns att skriva i')
        vy, slut = memoryview(bytes(data)), time.monotonic() + 5
        while vy:
            try:
                n = os.write(self.fd, vy)
                vy = vy[n:]
            except BlockingIOError:  # agenten läser inte just nu: kort väntan, aldrig ett låst anrop
                if time.monotonic() > slut:
                    raise TimeoutError('agenten tar inte emot inmatning just nu') from None
                time.sleep(0.01)

    def storlek(self, cols, rows):
        if self.slutad is None:
            _storlek(self.fd, cols, rows)

    # --- stoppet ---
    def stoppa(self, frist=8.0):
        """Verklig processkontroll: SIGTERM till agenten och dess processträd (också barn i egna grupper), sedan SIGKILL
        efter fristen. Ger True när processen har slutat."""
        if self.slutad is not None:
            return True
        self.stoppad = time.time()
        self._signalera(signal.SIGTERM)
        slut = time.monotonic() + frist
        while time.monotonic() < slut and self.proc.poll() is None:
            time.sleep(0.1)
        if self.proc.poll() is None:
            self._signalera(signal.SIGKILL)
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            return False
        if self.trad:  # barn som lever kvar efter agenten
            try:
                self.trad.skanna()
                import korvakt
                for p in self.trad.under({self.trad.rot}):
                    korvakt.signalera(p, signal.SIGKILL)
            except Exception:  # noqa: BLE001
                pass
        return True

    def _signalera(self, sig):
        try:
            os.killpg(self.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        if self.trad:
            try:
                self.trad.skanna()
                import korvakt
                for p in self.trad.under({self.trad.rot}):
                    korvakt.signalera(p, sig)
            except Exception:  # noqa: BLE001
                pass


def _starta(argv):
    """Startaren: en ny session med PTY:n (fd 0) som styrande terminal, arbetskatalogen och kommandot. Ingen shell."""
    import fcntl
    import termios
    i = argv.index('--')
    cwd, cmd = argv[i - 1], argv[i + 1:]
    if not cmd:
        os._exit(2)
    os.setsid()
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)
    os.chdir(cwd)
    os.execvpe(cmd[0], cmd, os.environ)


if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[1] == '--starta':
        _starta(sys.argv)
    sys.exit(2)
