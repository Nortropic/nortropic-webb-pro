#!/usr/bin/env python3
"""Beständig förbättring med syntetisk överlämningsstörning; inga modell-/nätanrop."""
import contextlib
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import kirurg_loop as kl
import kirurg_forsok as kf
import korregister


class Kirurg(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.tmp=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kirurg-','syntetisk förbättringskedja'))).resolve()
        self.root=self.tmp/'repo';self.root.mkdir();(self.root/'kontroller/rokprov').mkdir(parents=True)
        self.loop=kl.Loop(self.tmp/'kirurgen/forbattringar')
        self.bastext="def overfor(data):\n    return {'mal': data['mal']}\n"
        (self.root/'kontroller/overfor.py').write_text(self.bastext)
        self.facit=self.root/'kontroller/rokprov/prov.py'
        self.facit.write_text('''import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv.pop())/'kontroller'))
from overfor import overfor
class Fall(unittest.TestCase):
 def test_overlamning(self):
  data={'mal':'Syntetiskt mål','avstatt':'Ingen bokning'}
  self.assertEqual(overfor(data),data)
unittest.main()
''')
        for args in (['init','-q','-b','main'],['add','--all'],['-c','user.name=Prov','-c','user.email=prov@example.invalid','-c','core.hooksPath=/dev/null','commit','-qm','Syntetisk bas']):
            subprocess.run(['git','-C',str(self.root),*args],check=True,capture_output=True)
        self.bas=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        self.m={'klass':'isolerat_regressionsprov','max_forsok':2,'sekunder_per_variant':8,'giltig_till':time.time()+300,
                'filer':['kontroller/overfor.py'],'prov':'kontroller/rokprov/prov.py',
                'prov_sha256':hashlib.sha256(self.facit.read_bytes()).hexdigest(),'granskning':'oberoende','aterstallning':'kopian_kasseras','ansvarig':'Syntetisk provägare'}
        self.mfil=self.loop.rot.parent/'AGARMANDAT.json';self.spara_mandat()
        self.andringar={'kontroller/overfor.py':{'fore':hashlib.sha256(self.bastext.encode()).hexdigest(),'text':'def overfor(data):\n    return dict(data)\n'}}
        self.p=self.loop.signal('forlorad-uppgift','Uppgift tappades','forberedelse','syntetiskt lokalt prov','v1','Två uppgifter insamlades; en överfördes.','Kontrollerad teststörning, ingen riktig kund.')
    def spara_mandat(self):self.mfil.write_text(json.dumps({'schema':1,'mandat':{'provmandat':self.m}}))
    def planera(self):
        self.p=self.loop.diagnos(self.p['id'],self.p['revision'],'overlamningsfel','Insamlat svar finns redan.','Ny kundfråga tillför inget; rätta överföringen.','stor','reproducerat')
        self.p=self.loop.plan(self.p['id'],self.p['revision'],{'fraga':'Bevaras svaret?','jamforelse':'Samma syntetiska underlag före och efter.',
            'framgang':'Båda uppgifterna överförs.','forsamring':'Ingen påhittad ny uppgift.','provtyp':'regression','andel':'En överföringsfunktion.',
            'risk':'Lokal teststörning.','ansvarig':'Syntetisk provägare'})
    def kor(self,id='provforsok'):
        return kf.kor(self.loop,self.p['id'],self.p['revision'],'provmandat',id,self.root,self.bas,self.andringar)
    def test_signaldedupe_ny_version_delide_och_missade_signalers_stickprov(self):
        p=self.loop.signal('forlorad-uppgift','Uppgift tappades','forberedelse','syntetiskt lokalt prov','v1','Två uppgifter insamlades; en överfördes.','Kontrollerad teststörning, ingen riktig kund.')
        self.assertEqual(len(p['signaler']),1)
        p=self.loop.disposition(p['id'],p['revision'],'parkera','Provas senare.','Nytt belägg eller förändrat behov.')
        p=self.loop.signal('forlorad-uppgift','Samma problem','forberedelse','Äldre lågpopularitetskälla','v2','Delidé: bevara avstådda krav.','Lokalt jämförelseprov.','Endast denna delidé.')
        self.assertEqual(len(p['signaler']),2);self.assertTrue(p['nytt_underlag'])
        self.assertEqual(self.loop.stickprov('agarseed')[0]['id'],p['id'])
        with self.assertRaises(kl.Vagrad):self.loop.folj_upp(p['id'],p['revision'],'forbattrat','En positiv motivering.','Allt.','Försöket')
    def test_verkligt_lokalt_fore_efter_utan_inforande_eller_pahittad_effekt(self):
        self.planera();r=self.kor()
        self.assertEqual(r['utfall'],'regression_rattad',r)
        self.assertFalse(r['fore']['godkant']);self.assertTrue(r['efter']['godkant'])
        self.assertEqual(r['effekt'],'inte_observerad');self.assertEqual(r['inforande'],'inte_infort')
        self.assertEqual((self.root/'kontroller/overfor.py').read_text(),self.bastext)
        self.assertEqual(self.kor(),r,'samma operations-id ska bara läsa det gamla försöket')
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)
    def test_mandat_facit_paus_och_totalbudget(self):
        self.planera();self.loop.pausa(True)
        with self.assertRaises(kl.Vagrad):self.kor()
        self.loop.pausa(False);self.m['max_forsok']=1;self.spara_mandat();self.kor()
        self.p=self.loop.vy()['poster'][self.p['id']]
        with self.assertRaises(kl.Vagrad):self.kor('annatforsok')
        self.m['max_forsok']=2;self.m['giltig_till']=1;self.spara_mandat()
        with self.assertRaises(kl.Vagrad):self.kor('annatforsok')
        self.m['giltig_till']=time.time()+300;self.spara_mandat();self.facit.write_text('print("godkänd")')
        with self.assertRaises(kl.Vagrad):self.kor('annatforsok')
    def test_ett_forsok_och_omstart_nollstaller_inte_budget(self):
        self.planera()
        with kf.ensam(self.loop),self.assertRaises(kl.Vagrad):self.kor()
        with self.loop.trans() as d:
            d['forsok']['provforsok']={'id':'provforsok','post':self.p['id'],'status':'pagar',
                'begaran':kl.hash_({'post':self.p['id'],'mandat':'provmandat','bas':self.bas,'andringar':self.andringar})};d['forbrukat']['provmandat']=1
        r=self.kor();self.assertEqual(r['status'],'avbrutet')
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)
    def test_fil_utanfor_mandatet_nekas_fore_reservation(self):
        self.planera();self.andringar={'kontroller/annan.py':{'fore':None,'text':'# Syntetisk otillåten ändring\n'}}
        with self.assertRaises(kl.Vagrad):self.kor()
        self.assertEqual(self.loop.vy()['forsok'],{});self.assertEqual(self.loop.vy()['forbrukat'],{})

    def test_facit_mandat_och_aktiv_kod_faar_inte_skrivas(self):
        self.planera()
        attack='''def overfor(data):
 from pathlib import Path
 import os
 for p in ("%s","%s","%s"):
  try:Path(p).write_text("övertaget")
  except PermissionError:pass
  else:raise AssertionError("otillåten skrivning")
 try:os.kill(os.getppid(),15)
 except PermissionError:pass
 else:raise AssertionError("signal utanför försöket")
 return dict(data)
'''%(self.mfil,self.facit,self.root/'kontroller/overfor.py')
        self.andringar['kontroller/overfor.py']['text']=attack
        r=self.kor();self.assertTrue(r['efter']['godkant'],r)
        self.assertEqual(json.loads(self.mfil.read_text())['schema'],1)
        self.assertEqual((self.root/'kontroller/overfor.py').read_text(),self.bastext)
    def test_startfel_ar_inte_reproducerat_regressionsfel(self):
        self.planera();self.facit.write_text('raise SyntaxError("syntetiskt provfel")')
        self.m['prov_sha256']=hashlib.sha256(self.facit.read_bytes()).hexdigest();self.spara_mandat()
        r=self.kor();self.assertEqual(r['utfall'],'ofullstandigt',r)

    def test_facit_fryses_fran_de_validerade_byten(self):
        self.planera();original=self.facit.read_text()
        bytt=original.replace('self.assertEqual(overfor(data),data)',"self.assertEqual(Path(sys.path[0]).parent.name,'efter')")
        self.andringar['kontroller/overfor.py']['text']='def overfor(data):\n return {}\n'
        import kundstart_beredning as kb
        vanlig=kb.atomiskt
        def byt(p,b):
            if p.name=='ANDRINGAR.json':self.facit.write_text(bytt)
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=byt):r=self.kor()
        self.assertNotEqual(r['utfall'],'regression_rattad');self.assertFalse(r['efter']['godkant'])
        self.assertEqual(r['facit_sha256'],self.m['prov_sha256'])

    def test_verklig_looprot_olast(self):
        self.planera()
        self.andringar['kontroller/overfor.py']['text']='''def overfor(data):
 from pathlib import Path
 for p in (%r,%r):
  try:Path(p).read_text()
  except PermissionError:pass
  else:raise AssertionError('privat läsning')
 return dict(data)
'''%(str(self.mfil),str(self.loop.rot/'FORBATTRINGAR.json'))
        r=self.kor();self.assertTrue(r['efter']['godkant'],r)

    def test_provkopians_kallkod_och_metod_skrivskyddad(self):
        self.planera()
        self.andringar['kontroller/overfor.py']['text']='''def overfor(data):
 from pathlib import Path
 for p in (Path.cwd()/'kontroller/overfor.py',Path.cwd()/'kunskap/metodkarta.md'):
  try:
   p.parent.mkdir(parents=True,exist_ok=True);p.write_text('utanför skrivmandatet')
  except PermissionError:pass
  else:raise AssertionError('käll- eller metodfil skrivbar')
 return dict(data)
'''
        r=self.kor();self.assertTrue(r['efter']['godkant'],r)

    def test_styrprocessens_term_och_kill_lamnar_inga_levande_prov_utan_las(self):
        def vanta(test):
            slut=time.monotonic()+7
            while time.monotonic()<slut:
                if test():return
                time.sleep(.02)
            self.fail('processbarriären uteblev')
        def lever(pid):
            r=subprocess.run(['/bin/ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
            return bool(r.stdout.strip()) and not r.stdout.strip().startswith('Z')
        self.planera()
        self.facit.write_text('''import os,time,sys
from pathlib import Path
p=Path(sys.argv.pop())/'.tmp'
(p/'pid').write_text(str(os.getpid()))
for n in range(300):
 (p/'slag').write_text(str(n));time.sleep(.02)
''')
        self.m['prov_sha256']=hashlib.sha256(self.facit.read_bytes()).hexdigest();self.m['sekunder_per_variant']=10;self.spara_mandat()
        tmprot=self.tmp/'provens-tmp';tmprot.mkdir()
        for sig in (signal.SIGTERM,signal.SIGKILL):
            with self.subTest(sig=sig):
                ready=self.tmp/('redo-'+str(sig));op='avbrott-'+str(sig)
                data={'root':str(self.root),'loop':str(self.loop.rot),'id':self.p['id'],'revision':self.p['revision'],
                      'bas':self.bas,'andringar':self.andringar,'ready':str(ready),'op':op}
                spec=self.tmp/'start.json';spec.write_text(json.dumps(data))
                runner=self.tmp/'styr.py'
                runner.write_text('''import json,sys
from pathlib import Path
sys.path.insert(0,%r)
import kirurg_forsok as f,kirurg_loop as l
d=json.loads(Path(sys.argv[1]).read_text());vanlig=f.snapshot
def snapshot(root,commit,mal):
 vanlig(root,commit,mal);Path(d['ready']).write_text(str(mal))
f.snapshot=snapshot
f.kor(l.Loop(d['loop']),d['id'],d['revision'],'provmandat',d['op'],d['root'],d['bas'],d['andringar'])
'''%str(Path(kf.__file__).parent))
                proc=subprocess.Popen([sys.executable,'-B',str(runner),str(spec)],env=dict(os.environ,TMPDIR=str(tmprot)),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                barn=None
                try:
                    vanta(ready.exists);projekt=Path(ready.read_text());vanta(lambda:(projekt/'.tmp/pid').exists())
                    barn=int((projekt/'.tmp/pid').read_text());vanta(lambda:(projekt/'.tmp/slag').exists())
                    os.kill(proc.pid,sig);proc.wait(timeout=3)
                    def klart():
                        try:
                            with kf.ensam(self.loop):
                                self.assertFalse(lever(barn),'låset släpptes medan provet levde')
                                return True
                        except kl.Vagrad:return False
                    vanta(klart)
                    r=kf.kor(self.loop,self.p['id'],self.p['revision'],'provmandat',op,self.root,self.bas,self.andringar)
                    self.assertEqual(r['status'],'avbrutet')
                    self.p=self.loop.vy()['poster'][self.p['id']]
                finally:
                    if proc.poll() is None:proc.kill()
                    proc.communicate(timeout=3)
                    if barn and lever(barn):os.kill(barn,signal.SIGKILL)

    def test_loggtak_och_startfel_blir_ofullstandiga_med_budgeten_kvar(self):
        self.planera()
        self.andringar['kontroller/overfor.py']['text']='''def overfor(data):
 import sys
 sys.stdout.write('X'*4_000_000);sys.stdout.flush()
 return dict(data)
'''
        r=self.kor();self.assertEqual(r['utfall'],'ofullstandigt',r)
        self.assertLessEqual((self.loop.rot/'forsok/provforsok/efter.log').stat().st_size,1_000_000)
        self.p=self.loop.vy()['poster'][self.p['id']]
        p=self.loop.rot/'forsok/redan-finns';p.mkdir();(p/'orord').write_text('orörd')
        r=self.kor('redan-finns');self.assertEqual(r['status'],'fel');self.assertEqual(r['utfall'],'ofullstandigt')
        self.assertEqual((p/'orord').read_text(),'orörd');self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],2)

    def test_andrat_mandat_eller_paus_efter_reservation_stoppar_nasta_steg(self):
        import kundstart_beredning as kb
        self.planera();vanlig=kb.atomiskt
        def byt(p,b):
            if p.name=='ANDRINGAR.json':self.m['giltig_till']=1;self.spara_mandat()
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=byt):r=self.kor()
        self.assertEqual(r['status'],'fel');self.assertNotIn('fore',r)
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)
        self.m['giltig_till']=time.time()+300;self.spara_mandat();self.p=self.loop.vy()['poster'][self.p['id']]
        def paus(p,b):
            if p.name=='ANDRINGAR.json':self.loop.pausa(True)
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=paus):r=self.kor('pausat-forsok')
        self.assertEqual(r['status'],'fel');self.assertNotIn('fore',r)
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],2)

    def test_upptagen_kundkapacitet_reserverar_ingen_forsoksbudget(self):
        import kirurg_drift
        self.planera()
        with patch.object(kirurg_drift,'kapacitet',side_effect=kl.Vagrad('Kundarbete väntar.')):
            with self.assertRaises(kl.Vagrad):self.kor()
        self.assertEqual(self.loop.vy()['forsok'],{});self.assertEqual(self.loop.vy()['forbrukat'],{})

    def test_nytt_signalunderlag_efter_reservation_stoppar_innan_provet(self):
        import kundstart_beredning as kb
        self.planera();vanlig=kb.atomiskt
        def byt(p,b):
            if p.name=='ANDRINGAR.json':
                self.loop.signal('forlorad-uppgift','Uppgift tappades','forberedelse','Ny observation','v2','Annat underlag kräver ny diagnos.','Syntetiskt prov.')
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=byt):r=self.kor()
        self.assertEqual(r['status'],'fel');self.assertNotIn('fore',r)
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)

    def test_kallfel_efter_reservation_stoppar_beroende_prov(self):
        import kundstart_beredning as kb
        import kirurg_kallhalsa as h
        self.p=self.loop.signal('forlorad-uppgift','Uppgift tappades','forberedelse','spaning:prov','v1','Syntetisk källändring.','Kontrollerat prov.')
        span=self.loop.rot.parent/'spaning';span.mkdir()
        rapport={'id':'prov','namn':'Provkälla','fel':None}
        h.bokfor(span,[rapport],{'prov':{'hash':'v1'}},[])
        self.planera();vanlig=kb.atomiskt
        def byt(p,b):
            if p.name=='ANDRINGAR.json':h.bokfor(span,[rapport|{'fel':'Syntetiskt källfel'}],{},[])
            return vanlig(p,b)
        with patch.object(kb,'atomiskt',side_effect=byt):r=self.kor()
        self.assertEqual(r['status'],'fel');self.assertNotIn('fore',r)
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)

    def test_kundstart_som_kommer_under_provet_stoppar_och_vantar_in_barnet(self):
        import kirurg_drift
        self.facit.write_text('''import os,sys,time
from pathlib import Path
Path('.tmp/barnpid').write_text(str(os.getpid()))
time.sleep(30)
''');self.m['prov_sha256']=hashlib.sha256(self.facit.read_bytes()).hexdigest();self.spara_mandat()
        self.planera();vanlig=kf.snapshot;mal={};barn=[]
        def snapshot(root,commit,ut):vanlig(root,commit,ut);mal['ut']=ut
        def kapacitet(_):
            p=mal.get('ut')
            if p and (p/'.tmp/barnpid').exists():
                barn.append(int((p/'.tmp/barnpid').read_text()));raise kl.Vagrad('Kundarbete har företräde.')
        with patch.object(kf,'snapshot',side_effect=snapshot),patch.object(kirurg_drift,'kapacitet',side_effect=kapacitet):r=self.kor()
        self.assertTrue(barn,'det riktiga provbarnet ska ha startat före kapacitetsbytet')
        self.assertEqual(r['status'],'fel');self.assertNotIn('efter',r)
        with self.assertRaises(ProcessLookupError):os.kill(barn[0],0)
        self.assertEqual(self.loop.vy()['forbrukat']['provmandat'],1)


if __name__=='__main__':unittest.main()
