#!/usr/bin/env python3
"""Införande observeras ur verklig Git i en egen syntetisk kopia, ingen aktiv kod ändras av observatören."""
import hashlib,json,os,shutil,subprocess,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import kirurg_loop as kl
from prov_kirurg_loop import Kirurg
try:import kirurg_uppfoljning as ku
except ImportError:ku=None


class Uppfoljning(Kirurg):
    # Bara den nya avgränsningen; den ärvda fixturen, inte de gamla testmetoderna.
    def setUp(self):
        super().setUp();self.assertIsNotNone(ku,'väg från godkänt regressionsprov till verifierat Git-införande saknas')
        self.planera();self.r=self.kor();self.assertEqual(self.r['utfall'],'regression_rattad')
        self.p=self.loop.vy()['poster'][self.p['id']]
        self.obs={'klass':'observera_gitinförande','gren':'main','filer':list(self.andringar),'granskare':['oberoende-provgranskare'],
                  'max_registreringar':2,'giltig_till':time.time()+600,'ansvarig':'Syntetisk provägare'}
        self.mfil.write_text(json.dumps({'schema':1,'mandat':{'provmandat':self.m,'observera':self.obs}}))
        for n,v in self.andringar.items():(self.root/n).write_text(v['text'])
        self.commit('Syntetisk rättelse');self.version=self.head()
        self.g={'forsok':'provforsok','version':self.version,'andringar':self.r['andringar'],'plan':self.r['plan']['sha256'],
                'skapare':'syntetisk-provskapare','granskare':'oberoende-provgranskare','utfall':'godkand','tid':time.time()}
        self.gfil=self.loop.rot.parent/'GRANSKNINGAR.json';self.spara_granskning()
    def commit(self,text):
        subprocess.run(['git','-C',str(self.root),'add','--all'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Prov','-c','user.email=prov@example.invalid','-c','core.hooksPath=/dev/null','commit','-qm',text],check=True,capture_output=True)
    def head(self):return subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
    def spara_granskning(self):self.gfil.write_text(json.dumps({'schema':1,'granskningar':{'granskning1':self.g}}))
    def registrera(self):return ku.registrera(self.loop,self.root,self.p['id'],self.p['revision'],'provforsok','observera','granskning1',self.version)
    def test_ny_registrering_bevisar_git_inte_drift_eller_nytta(self):
        fore=self.head();p=self.registrera();self.assertEqual(self.head(),fore)
        self.assertEqual(p['inforande'],'infort');self.assertEqual(p['effekt'],'inte_observerad')
        b=p['inforanden'][-1];self.assertEqual(b['version'],self.version);self.assertEqual(b['omfattning'],'lokal Git-version, inte verifierad drift')
        self.assertEqual(self.loop.vy()['forsok']['provforsok']['inforande'],'infort')
    def test_mandat_saknas_utgatt_eller_utanför_filer_nekar(self):
        original=self.mfil.read_bytes()
        for change in (None,{'giltig_till':1},{'filer':['kontroller/annan.py']},{'gren':'annan'},{'max_registreringar':0}):
            data=json.loads(original)
            if change is None:data['mandat'].pop('observera')
            else:data['mandat']['observera'].update(change)
            self.mfil.write_text(json.dumps(data))
            with self.assertRaises(kl.Vagrad):self.registrera()
        self.mfil.write_bytes(original);self.assertEqual(self.loop.vy()['poster'][self.p['id']]['inforande'],'inte_infort')
    def test_granskning_kravs_av_annan_identitet_for_exakt_version_och_patch(self):
        original=dict(self.g)
        for change in ({'skapare':self.g['granskare']},{'version':self.bas},{'andringar':'0'*64},{'utfall':'underkand'},{'plan':'0'*64},{'granskare':'obekant'}):
            self.g=original|change;self.spara_granskning()
            with self.assertRaises(kl.Vagrad):self.registrera()
        self.g=original;self.spara_granskning();self.gfil.unlink()
        with self.assertRaises(kl.Vagrad):self.registrera()
    def test_andrad_arbetskopia_annan_commit_och_annan_patch_nekar(self):
        p=self.root/'kontroller/overfor.py';after=p.read_bytes();p.write_text('# inte provat\n')
        with self.assertRaises(kl.Vagrad):self.registrera()
        self.commit('Syntetisk annan version');self.version=self.head();self.g['version']=self.version;self.spara_granskning()
        with self.assertRaises(kl.Vagrad):self.registrera()
        p.write_bytes(after)
    def test_bytt_patchfil_eller_forbattrad_diagnos_nekar(self):
        f=self.loop.rot/'forsok/provforsok/ANDRINGAR.json';b=f.read_bytes();f.write_text('{}')
        with self.assertRaises(kl.Vagrad):self.registrera()
        f.write_bytes(b)
        self.loop.signal('forlorad-uppgift','Nytt belägg','forberedelse','syntetiskt lokalt prov','v2','Nytt faktaunderlag.','Syntetiskt.')
        with self.assertRaises(kl.Vagrad):self.registrera()
    def test_ingen_eftereffekt_fore_inforande_eller_fran_annan_version(self):
        with self.assertRaises(kl.Vagrad):ku.folj_upp(self.loop,self.root,self.p['id'],self.p['revision'],self.version,'forbattrat','Syntetiskt lokalt prov','Endast provet','Provobservatör')
        p=self.registrera()
        with self.assertRaises(kl.Vagrad):ku.folj_upp(self.loop,self.root,p['id'],p['revision'],self.bas,'forbattrat','Syntetiskt lokalt prov','Endast provet','Provobservatör')
        p=ku.folj_upp(self.loop,self.root,p['id'],p['revision'],self.version,'oforandrat','Syntetiskt lokalt prov','Endast provet','Provobservatör')
        self.assertEqual(p['effekt'],'oforandrat');self.assertEqual(p['uppfoljning'][-1]['kalltyp'],'inrapporterad observation')
    def test_dubbel_registrering_forbrukar_inte_ny_budget_och_paus_nekar(self):
        p=self.registrera();self.p=p;self.assertEqual(self.registrera(),p)
        self.assertEqual(self.loop.vy()['forbrukat']['observera'],1)
        self.loop.pausa(True)
        with self.assertRaises(kl.Vagrad):self.registrera()
    def test_cli_registrerar_och_vanta_pa_uppfoljning_men_http_far_inte_gora_det(self):
        import io,contextlib,kirurg_forbattring as kfb
        data={'pid':self.p['id'],'revision':self.p['revision'],'forsok':'provforsok','mid':'observera','granskning':'granskning1','version':self.version}
        # CLI:s ordinarie handler läser stdin; bara fixture-rötterna flyttas.
        with patch.object(kfb,'ROOT',self.root),patch.object(kfb,'loop',return_value=self.loop),patch('sys.stdin',io.StringIO(json.dumps(data))):
            ut=io.StringIO()
            with contextlib.redirect_stdout(ut):rc=kfb.main(['registrera-inforande'])
        self.assertEqual(rc,0,ut.getvalue());self.assertEqual(json.loads(ut.getvalue())['inforande'],'infort')
        self.assertNotIn('registrera-inforande',kfb.HANDLINGAR)
    def test_dold_arbetsfil_lankat_kvitto_och_ny_diagnos_nekar(self):
        f=self.root/'kontroller/overfor.py';after=f.read_bytes()
        subprocess.run(['git','-C',str(self.root),'update-index','--assume-unchanged','kontroller/overfor.py'],check=True)
        f.write_text('# dolt från status\n')
        with self.assertRaises(kl.Vagrad):self.registrera()
        f.write_bytes(after)
        riktig=self.tmp/'kvitto.json';riktig.write_bytes(self.gfil.read_bytes());self.gfil.unlink();self.gfil.symlink_to(riktig)
        with self.assertRaises(kl.Vagrad):self.registrera()
        self.gfil.unlink();self.gfil.write_bytes(riktig.read_bytes())
        self.p=self.loop.diagnos(self.p['id'],self.p['revision'],'metodkoppling','Annan diagnos.','Nytt försök behövs.','stor','hypotes')
        with self.assertRaises(kl.Vagrad):self.registrera()
    def test_gitdiff_far_inte_innehalla_oprovade_extraandringar(self):
        (self.root/'kontroller/annan.py').write_text('# extra, inte provat\n');self.commit('Syntetisk extraändring')
        self.version=self.head();self.g['version']=self.version;self.spara_granskning()
        with self.assertRaisesRegex(kl.Vagrad,'andra ändringar'):self.registrera()
    def test_ofullstandigt_eller_oforandrat_forsok_ger_inget_inforande(self):
        for status,utfall in [('fel','ofullstandigt'),('klart','oforandrat'),('klart','forsamrat')]:
            with self.loop.trans() as d:d['forsok']['provforsok'].update(status=status,utfall=utfall)
            with self.assertRaisesRegex(kl.Vagrad,'slutfört lyckat'):self.registrera()
    def test_dold_fil_utanfor_patch_nekar_hela_gitidentiteten(self):
        f=self.facit;fore=f.read_bytes()
        for flagga in ('--assume-unchanged','--skip-worktree'):
            subprocess.run(['git','-C',str(self.root),'update-index',flagga,'kontroller/rokprov/prov.py'],check=True)
            f.write_text('Dold orelaterad arbetsändring.\n')
            self.assertFalse(subprocess.check_output(['git','-C',str(self.root),'status','--porcelain','--untracked-files=no']).strip())
            with self.assertRaises(kl.Vagrad):self.registrera()
            f.write_bytes(fore)
            subprocess.run(['git','-C',str(self.root),'update-index',flagga.replace('--','--no-',1),'kontroller/rokprov/prov.py'],check=True)
    def test_gitmiljo_kan_inte_byta_repo(self):
        annan=self.tmp/'annat-repo';shutil.copytree(self.root,annan)
        subprocess.run(['git','-C',str(annan),'-c','user.name=Prov','-c','user.email=prov@example.invalid','-c','core.hooksPath=/dev/null','commit','--allow-empty','-qm','Syntetisk annan kopia'],check=True,capture_output=True)
        annan_version=subprocess.check_output(['git','-C',str(annan),'rev-parse','HEAD'],text=True).strip();egen=self.version
        with patch.dict(os.environ,{'GIT_DIR':str(annan/'.git'),'GIT_WORK_TREE':str(annan),'GIT_INDEX_FILE':str(annan/'.git/index')}):
            self.version=annan_version;self.g['version']=annan_version;self.spara_granskning()
            with self.assertRaises(kl.Vagrad):self.registrera()
            self.version=egen;self.g['version']=egen;self.spara_granskning()
            self.assertEqual(self.registrera()['inforanden'][-1]['version'],egen)
    def test_aterstallning_och_nytt_inforande_far_inte_arva_effekt(self):
        p=self.registrera();gammal=self.version
        p=ku.folj_upp(self.loop,self.root,p['id'],p['revision'],gammal,'forbattrat','Endast första versionens prov.','Lokalt syntetiskt prov','Provobservatör')
        (self.root/'kontroller/overfor.py').write_text(self.bastext);self.commit('Syntetisk manuell återställning')
        p=ku.aterstallning(self.loop,self.root,p['id'],p['revision'],self.head(),'observera')
        self.assertEqual(p['effekt'],'inte_observerad');self.assertEqual(self.loop.vy()['forsok']['provforsok']['effekt'],'inte_observerad')
        (self.root/'kontroller/overfor.py').write_text(self.andringar['kontroller/overfor.py']['text']);self.commit('Syntetiskt nytt införande')
        self.version=self.head();self.g.update(version=self.version,tid=time.time());self.spara_granskning();self.p=p
        p=self.registrera();x=self.loop.vy()['forsok']['provforsok']
        self.assertEqual(p['effekt'],'inte_observerad');self.assertEqual(x['effekt'],'inte_observerad')
        self.assertEqual(p['uppfoljning'][-1]['version'],gammal);self.assertEqual(len(p['uppfoljning']),1)
        self.assertEqual(x['inforande_id'],p['inforanden'][-1]['id'])
    def test_nytt_gitid_nollstaller_forsoekets_effekt_utan_aterstallning(self):
        p=self.registrera();gammal=self.version
        p=ku.folj_upp(self.loop,self.root,p['id'],p['revision'],gammal,'forbattrat','Första versionens prov.','Lokalt syntetiskt prov','Provobservatör')
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Prov','-c','user.email=prov@example.invalid','-c','core.hooksPath=/dev/null','commit','--allow-empty','-qm','Syntetisk ny Git-identitet'],check=True,capture_output=True)
        self.version=self.head();self.g.update(version=self.version,tid=time.time());self.spara_granskning();self.p=p
        p=self.registrera();self.assertEqual(p['effekt'],'inte_observerad')
        self.assertEqual(self.loop.vy()['forsok']['provforsok']['effekt'],'inte_observerad')
        self.assertEqual(p['uppfoljning'][-1]['version'],gammal)
    def test_gitkorbit_galler_filagaren(self):
        f=self.root/'kontroller/overfor.py';f.chmod(0o755);self.commit('Syntetisk körbar fil')
        self.version=self.head();self.g.update(version=self.version,tid=time.time());self.spara_granskning()
        subprocess.run(['git','-C',str(self.root),'config','core.filemode','false'],check=True)
        f.chmod(0o654)
        self.assertFalse(subprocess.check_output(['git','-C',str(self.root),'status','--porcelain','--untracked-files=no']).strip())
        with self.assertRaises(kl.Vagrad):self.registrera()
        f.chmod(0o754);self.assertEqual(self.registrera()['inforande'],'infort')
    def test_verifierad_aterstallning_skadar_inte_senare_filer(self):
        p=self.registrera()
        with self.assertRaises(kl.Vagrad):ku.aterstallning(self.loop,self.root,p['id'],p['revision'],self.version,'observera')
        (self.root/'kontroller/overfor.py').write_text(self.bastext)
        (self.root/'README.md').write_text('Senare orelaterad ändring.\n');self.commit('Syntetisk manuell återställning')
        fore=self.head();p=ku.aterstallning(self.loop,self.root,p['id'],p['revision'],fore,'observera')
        self.assertEqual(self.head(),fore);self.assertEqual(p['inforande'],'aterstallt')
        self.assertEqual((self.root/'README.md').read_text(),'Senare orelaterad ändring.\n')
        with self.assertRaises(kl.Vagrad):ku.folj_upp(self.loop,self.root,p['id'],p['revision'],fore,'forbattrat','Prov','Prov','Prov')

# Skippa ärvda testmetoder; samma fixtur prövas redan i prov_kirurg_loop.py.
for name in list(Kirurg.__dict__):
    if name.startswith('test_') and name not in Uppfoljning.__dict__:setattr(Uppfoljning,name,None)
if __name__=='__main__':unittest.main(defaultTest='Uppfoljning')
