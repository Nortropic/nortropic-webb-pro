#!/usr/bin/env python3
"""Riktig processgräns för flödeshandlingar. Export-/byggkommandot är en lokal attrapp."""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister


class Flodesstarter(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-','syntetiska långa flödeshandlingar'))).resolve()
        self.slug='prov-flodesstart';self.u=self.root/'underlag'/self.slug;self.k=self.root/'kunder'/self.slug
        (self.u/'atelje').mkdir(parents=True);(self.k/'sajt/src/pages').mkdir(parents=True)
        (self.k/'sajt/src/pages/index.astro').write_text('<h1>Syntetiskt</h1>');(self.k/'sajt/package.json').write_text('{}')
        controls=Path(__file__).resolve().parents[2]
        (self.root/'kontroller').mkdir()
        for p in controls.glob('*.py'):shutil.copyfile(p,self.root/'kontroller'/p.name)
        self.counter=self.root/'anrop.jsonl'
        (self.root/'kontroller/exportera.py').write_text('''import json,os,signal,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with (root/'anrop.jsonl').open('a') as f:f.write(json.dumps({'argv':sys.argv[1:],'pid':os.getpid()})+'\\n')
def stopp(*a):(root/'child-stopp').write_text('stopp');sys.exit(4)
signal.signal(signal.SIGTERM,stopp)
time.sleep(15)
''')
        self.env=dict(os.environ);self.env.pop('NWP_SLUG',None)
        self.addCleanup(self.stada_arbetare)

    def journal(self):
        return [json.loads(p.read_text()) for p in (self.u/'ateljestarter').glob('*.json')]

    def kor(self,*args):
        return subprocess.run([sys.executable,'-B',str(self.root/'kontroller/prototyp.py'),self.slug,*args],cwd=self.root,env=self.env,capture_output=True,text=True,timeout=8)

    def vanta(self,villkor):
        slut=time.monotonic()+6
        while time.monotonic()<slut:
            if villkor():return
            time.sleep(.02)
        self.fail('barriären nåddes inte: '+repr(self.journal()))

    def stada_arbetare(self):
        for p in self.journal():
            if p.get('status')=='startad' and p.get('pid'):
                try:os.kill(p['pid'],signal.SIGTERM)
                except ProcessLookupError:pass
        slut=time.monotonic()+6
        while time.monotonic()<slut and any(p.get('status')=='startad' for p in self.journal()):time.sleep(.02)
        if any(p.get('status')=='startad' for p in self.journal()):raise AssertionError('provets egen arbetare avslutades inte')

    def test_start_omforsok_las_stopp_genom_cli(self):
        r=self.kor('--exportera','--start-id','prov-operation-a');self.assertEqual(r.returncode,5,r.stdout+r.stderr)
        self.vanta(self.counter.exists)
        r=self.kor('--exportera','--start-id','prov-operation-a');self.assertEqual(r.returncode,5,r.stdout+r.stderr)
        r=self.kor('--exportera','--start-id','prov-operation-b');self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertEqual(len(self.counter.read_text().splitlines()),1)
        self.assertEqual(json.loads(self.counter.read_text())['argv'],[self.slug,'--git'])
        r=self.kor('--stoppa-overgang');self.assertEqual(r.returncode,5,r.stdout+r.stderr)
        self.vanta(lambda:all(x['status']=='slut' for x in self.journal()))
        self.assertTrue((self.root/'child-stopp').is_file())
        self.assertEqual(self.journal()[0]['slutkod'],4)
        r=self.kor('--exportera','--start-id','prov-operation-a');self.assertEqual(r.returncode,4)
        self.assertEqual(len(self.counter.read_text().splitlines()),1)

    def test_saknat_godkannande_startar_inget_helbygge(self):
        (self.root/'kor.sh').write_text('exit 97\n')
        r=self.kor('--helbygge','--start-id','prov-operation-h')
        self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertFalse(self.journal());self.assertFalse(self.counter.exists())

    def test_paende_atelje_eller_olast_status_stoppar_fore_reservation(self):
        for text in ('{"steg":"divergera","pid":123456}', '{trasigt', '[]'):
            (self.u/'atelje/STATUS.json').write_text(text)
            r=self.kor('--exportera','--start-id','prov-operation-c')
            self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertFalse(self.journal())

    def test_startlaset_stoppas_av_lank_utan_att_lanka_skrivs(self):
        target=self.root/'annan';target.write_text('orörd')
        (self.u/'.atelje-start.las').symlink_to(target)
        r=self.kor('--exportera','--start-id','prov-operation-d')
        self.assertEqual(r.returncode,2,r.stdout+r.stderr);self.assertEqual(target.read_text(),'orörd');self.assertFalse(self.journal())

    def barriar(self,operation):
        runner=self.root/'barriar.py'
        runner.write_text('''import sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'kontroller'))
import flodesstart as f
orig=f.subprocess.Popen
def popen(*a,**kw):
 (root/'redo').write_text('redo')
 while not (root/'slapp').exists():time.sleep(.01)
 return orig(*a,**kw)
f.subprocess.Popen=popen
sys.exit(f.starta(sys.argv[1],'exportera',sys.argv[2]))
''')
        p=subprocess.Popen([sys.executable,'-B',str(runner),self.slug,operation],cwd=self.root,env=self.env)
        def stada():
            if p.poll() is None:p.terminate()
            p.wait(timeout=5)
        self.addCleanup(stada);self.vanta(lambda:(self.root/'redo').exists())
        return p

    def test_stopp_fore_processstart_bestaar(self):
        p=self.barriar('prov-reserverad-stopp')
        r=self.kor('--stoppa-overgang');self.assertEqual(r.returncode,5,r.stdout+r.stderr)
        (self.root/'slapp').write_text('släpp');p.wait(timeout=5)
        self.vanta(lambda:self.journal()[0]['status']=='slut')
        self.assertEqual(self.journal()[0]['slutkod'],4);self.assertFalse(self.counter.exists())

    def test_avbruten_reservation_far_slutstatus_utan_nystart(self):
        p=self.barriar('prov-reserverad-avbrott');p.terminate();p.wait(timeout=5)
        r=self.kor('--exportera','--start-id','prov-reserverad-avbrott')
        self.assertEqual(r.returncode,4,r.stdout+r.stderr)
        self.assertEqual(self.journal()[0]['status'],'slut');self.assertFalse(self.counter.exists())

    def test_stopp_vantar_pa_exportens_barn_aven_ny_session(self):
        (self.root/'hjartslag.py').write_text('''import signal,time,os
from pathlib import Path
r=Path(__file__).resolve().parent
signal.signal(signal.SIGTERM,signal.SIG_IGN)
(r/'barn-pid').write_text(str(os.getpid()))
while True:
 with (r/'slag').open('a') as f:f.write('x')
 time.sleep(.02)
''')
        p=self.root/'kontroller/exportera.py'
        p.write_text('''import subprocess,sys,time
from pathlib import Path
r=Path(__file__).resolve().parents[1]
subprocess.Popen([sys.executable,str(r/'hjartslag.py')],start_new_session=True)
time.sleep(60)
''')
        self.assertEqual(self.kor('--exportera','--start-id','prov-exportbarn-stopp').returncode,5)
        self.vanta(lambda:(self.root/'barn-pid').exists())
        barn=int((self.root/'barn-pid').read_text())
        def stada_barn():
            try:os.kill(barn,signal.SIGKILL)
            except ProcessLookupError:pass
        self.addCleanup(stada_barn)
        self.assertEqual(self.kor('--stoppa-overgang').returncode,5)
        self.vanta(lambda:self.journal()[0]['status']=='slut')
        n=len((self.root/'slag').read_text());time.sleep(.12)
        self.assertEqual(len((self.root/'slag').read_text()),n,'barnet arbetar efter terminalstatus')
        import korvakt
        q=korvakt.las_process(barn);self.assertTrue(q is None or q.zombie)


if __name__=='__main__':unittest.main()
