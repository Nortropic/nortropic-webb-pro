#!/usr/bin/env python3
"""Metodförsökets förberedelse och parameterkoppling, utan modellanrop."""
import contextlib
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import atelje
import kandidater as kd
import ab
import skapande


class Skissforsok(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kallgap-','A/B skissens mekanik'))).resolve()
        for m in (atelje,ab,skapande):
            for n,v in (('ROOT',self.root),('UNDERLAG',self.root/'underlag'),('KUNDER',self.root/'kunder')):
                if hasattr(m,n):self.stack.enter_context(patch.object(m,n,v))
        self.stack.enter_context(patch.object(ab,'AB',self.root/'kunder/ab'))
        self.slug='prov-skissforsok';self.u=atelje.UNDERLAG/self.slug
        def skriv(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(d)
        self.skriv=skriv
        for f in ('BRIEF.md','RESEARCH.md','TEXTUNDERLAG.md','REFERENSER.md'):
            skriv(self.u/f,'syntetiskt '+f)
        skriv(self.u/'VERKSAMHET.json',json.dumps({'schema':1,'fiktiv':True,'namn':'Exempelverkstad','rackvidd':{'typ':'nationell'},'kontaktvagar':[],'tjanster':['Service']}))
        skriv(self.u/'referenser/paket-v01/referens.png','syntetisk bildmarkör')
        plan={'tid':'2026-01-01T00:00:00Z','lage':'skiss','antal':1,'kandidater':{'k01':{'titel':'Samma uppgift','ide':'Visa tjänsten','hypotes':'Syntetisk','referensbilder':[]}}}
        skriv(kd.rot(self.slug)/'KANDIDATPLAN.json',json.dumps(plan))
        for f in ('FORSKNING.json','UPPDRAGSMATERIAL.json','PLANPROVNING.json'):
            skriv(kd.rot(self.slug)/f,json.dumps({'kandidater':{'k01':{'refero_stil':None,'mobbin':[]}}}))
        skriv(kd.rot(self.slug)/'FORSKNING.md','syntetisk forskning')
        skriv(kd.kdir(self.slug,'k01')/'UPPDRAG.md','# Samma uppdrag\nsyntetiskt innehåll\n')
        kd.satt_status(self.slug,'k01','planerad',forsok=0,titel='Samma uppgift')
        skriv(atelje.KUNDER/self.slug/'sajt/package.json','{}')
        skriv(atelje.KUNDER/self.slug/'sajt/src/pages/index.astro','<h1>Mall</h1>')
        skriv(self.root/'kontroller/mekanik.py','# syntetisk kod\n')

    def forbered(self):
        return ab.forbered_skiss(self.slug,'k01')

    def test_forbered_startar_inget_och_fryser_en_variabel(self):
        with patch.object(atelje,'session') as s,patch.object(atelje.subprocess,'Popen') as p:
            post=self.forbered()
        s.assert_not_called();p.assert_not_called()
        self.assertEqual(post['status'],'forberedd')
        self.assertEqual(len(post['kandidater']),2)
        self.assertEqual(set(post['varden'].values()),{'medium','high'})
        self.assertEqual(post['pass'],'skisskapare')
        self.assertEqual((kd.kdir(self.slug,'k01')/'UPPDRAG.md').read_bytes(),(kd.kdir(self.slug,'k02')/'UPPDRAG.md').read_bytes())
        self.assertNotIn('val',json.loads((kd.rot(self.slug)/'KANDIDATPLAN.json').read_text()))
        std=kd.skaparval()
        for kid in post['kandidater']:
            v=kd.skaparval(self.slug,kid)
            self.assertEqual(v['effort'],post['varden'][kid]);self.assertEqual(v['modell'],std['modell'])
        self.assertEqual(kd.skaparval(),std)

    def test_ny_kallversion_eller_metod_nekar(self):
        post=self.forbered()
        for fil in (self.u/'BRIEF.md',self.u/'referenser/paket-v01/referens.png',self.root/'kontroller/mekanik.py'):
            fore=fil.read_bytes();fil.write_bytes(fore+b' annan version')
            with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')
            fil.write_bytes(fore)
        self.assertEqual(kd.skaparval(self.slug,'k02')['effort'],post['varden']['k02'])

    def test_arbetad_kandidat_och_ny_forberedelse_nekar(self):
        kd.satt_status(self.slug,'k01','klar',forsok=1)
        with self.assertRaises(ValueError):self.forbered()
        kd.satt_status(self.slug,'k01','planerad',forsok=0)
        self.forbered()
        with self.assertRaises(ValueError):self.forbered()

    def test_andrad_budget_eller_ovriga_inställningar_nekar(self):
        self.forbered()
        with patch.object(kd,'FRIST_SKISS',kd.FRIST_SKISS+1):
            with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')
        with patch.object(atelje,'MODELL','annan-syntetisk-modell'):
            with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')

    def test_lasfel_och_symlank_far_inte_ge_standardval(self):
        post=self.forbered();fil=ab.AB/(post['id']+'.json');fil.write_text('{')
        with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')

    def test_symlank_till_kallor_och_post_nekar(self):
        post=self.forbered();fil=ab.AB/(post['id']+'.json');innehall=fil.read_bytes()
        annan=self.root/'annan.json';annan.write_bytes(innehall);fil.unlink();fil.symlink_to(annan)
        with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')
        fil.unlink();fil.write_bytes(innehall)
        ref=self.u/'referenser/paket-v01/referens.png';ref.unlink();ref.symlink_to(annan)
        with self.assertRaises(ValueError):kd.skaparval(self.slug,'k01')

    def test_tva_forberedelser_skapar_bara_ett_forsok(self):
        ut=[]
        def kor():
            try:ut.append(self.forbered()['id'])
            except ValueError:ut.append(None)
        ts=[threading.Thread(target=kor) for _ in range(2)]
        for t in ts:t.start()
        for t in ts:t.join(3)
        self.assertTrue(all(not t.is_alive() for t in ts))
        self.assertEqual(sum(x is not None for x in ut),1)
        self.assertEqual(len(list(ab.AB.glob('skiss-*.json'))),1)

    def test_armarna_doljs_fore_agarens_val(self):
        self.forbered()
        self.assertEqual(ab.main(['skissresultat',self.slug]),2)
        payload=json.dumps(kd.sammanstall(self.slug),ensure_ascii=False)
        self.assertNotIn('effort',payload);self.assertNotIn('medium',payload);self.assertNotIn('high',payload)
        with self.assertRaisesRegex(ValueError,'båda'):
            kd.prova_beslut(self.slug,'valj',[{'id':'k01','version':'syntetisk'}])

    def test_misslyckade_forsok_och_okanda_matt_finns_kvar(self):
        self.forbered();d=kd.kdir(self.slug,'k01')
        self.skriv(d/'forsok-1/svar-skiss-1.json',json.dumps({'duration_ms':60000,'num_turns':3,'is_error':True}))
        self.skriv(d/'svar-skiss-2.json',json.dumps({'duration_ms':120000,'num_turns':7,'total_cost_usd':0.2}))
        kd.satt_status(self.slug,'k01','ofullstandig','syntetiskt provfel',forsok=2,
                       forsok_tider=[{'forsok':1,'utfall':'avbruten'},{'forsok':2,'utfall':'ofullstandig'}])
        r=ab.skissresultat(self.slug);a=r['armar']['k01']
        self.assertEqual(len(a['forsok']),2);self.assertEqual(a['anvandning']['minuter'],3)
        self.assertIsNone(a['anvandning']['listpris_usd']);self.assertEqual(a['anvandning']['observerat']['total_cost_usd'],0.2)
        self.assertIsNone(a['observerad_effort']);self.assertIsNone(a['observerad_modell'])
        self.skriv(self.u/'BRIEF.md','ändrat')
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])

    def test_aldre_dom_och_deklarerad_mobbinbild_versionsbinds(self):
        dom=self.u/'DESIGNDOMAR.jsonl';self.skriv(dom,'{"tid":"2025-01-01T00:00:00Z","text":"Syntetiskt"}\n')
        bild=self.u/'arbetsmaterial/mobbin.png';self.skriv(bild,'syntetisk bild')
        mat=kd.rot(self.slug)/'UPPDRAGSMATERIAL.json';m=json.loads(mat.read_text())
        m['kandidater']['k01']['mobbin']=[{'fil':str(bild.relative_to(self.root))}];mat.write_text(json.dumps(m))
        self.forbered()
        for f in (dom,bild):
            fore=f.read_bytes();f.write_bytes(fore+' ändring'.encode())
            with self.assertRaises(ValueError):ab.skisskrav(self.slug)
            self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])
            f.write_bytes(fore)

    def test_kand_saknad_svarsfil_gor_totalen_okand(self):
        self.forbered();d=kd.kdir(self.slug,'k01')
        self.skriv(d/'svar-skiss-1.json',json.dumps({'duration_ms':60000,'num_turns':3,'total_cost_usd':.2}))
        kd.satt_status(self.slug,'k01','ofullstandig',forsok=2,sessioner=[{'svar':'svar-skiss-1.json'},{'svar':'svar-skiss-2.json'}])
        r=ab.skissresultat(self.slug)['armar']['k01']
        self.assertFalse(r['anvandning']['fullstandigt']);self.assertIsNone(r['anvandning']['minuter'])
        self.assertEqual(r['saknade_svar'],['svar-skiss-2.json'])
        self.assertEqual(r['anvandning']['observerat']['duration_ms'],60000)

    def test_andrad_tilldelning_nekar(self):
        p=self.forbered();f=ab.AB/(p['id']+'.json')
        p['varden']={k:('medium' if v=='high' else 'high') for k,v in p['varden'].items()};f.write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError,'tilldelning'):ab.skissresultat(self.slug)
        with self.assertRaisesRegex(ValueError,'tilldelning'):kd.skaparval(self.slug,'k01')

    def test_bokford_installning_och_artefakt_maste_stamma(self):
        p=self.forbered();k=p['kandidater'][0]
        kd.satt_status(self.slug,k,'klar',forsok=1,forsok_tider=[{'begard_installning':{'modell':'annan','effort':p['varden'][k]}}])
        with self.assertRaisesRegex(ValueError,'bokförda'):ab.skissresultat(self.slug)
        kd.satt_status(self.slug,k,'klar',forsok=1,forsok_tider=[],version='inte-den-faktiska-hashen')
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])

    def test_skrivfel_bevarar_original_och_ger_omforsok(self):
        filer=[kd.rot(self.slug)/'KANDIDATPLAN.json',kd.rot(self.slug)/'UPPDRAGSMATERIAL.json',kd.kdir(self.slug,'k01')/'UPPDRAG.md']
        fore={p:p.read_bytes() for p in filer}
        riktig=atelje.skriv_json_atomiskt
        def skriv(f,data):
            if f.name=='UPPDRAGSMATERIAL.json':raise OSError('syntetiskt skrivfel')
            return riktig(f,data)
        with patch.object(atelje,'skriv_json_atomiskt',skriv):
            with self.assertRaises(OSError):self.forbered()
        for p,b in fore.items():
            self.assertEqual(json.loads(p.read_bytes()),json.loads(b)) if p.suffix=='.json' else self.assertEqual(p.read_bytes(),b)
        self.assertEqual(kd.lista(self.slug),['k01'])
        self.assertEqual(json.loads(next(ab.AB.glob('skiss-*.json')).read_text())['status'],'forberedelsefel')
        self.assertEqual(self.forbered()['status'],'forberedd')

    def test_agarval_efter_kontrollerade_armar_ar_inte_nytt_skaparunderlag(self):
        self.forbered()
        for k in ('k01','k02'):
            kd.satt_status(self.slug,k,'ofullstandig',forsok=1)
            ab.skissavslutad(self.slug,k)
        self.skriv(self.u/'DESIGNDOMAR.jsonl',json.dumps({'tid':'2026-01-02T00:00:00Z','kalla':'ägaren',
                   'beslut':'forkasta','plan':kd.plan_tid(self.slug),'text':'Syntetiskt tekniskt prov, ingen mänsklig kvalitetsdom.'})+'\n')
        self.assertTrue(kd.domd(self.slug))
        self.assertTrue(ab.skissresultat(self.slug)['jamforbara_kallor'])
        self.skriv(self.u/'BRIEF.md','ändrat uppdrag')
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])

    def test_levererad_metod_ar_samma_kalla_som_prompten(self):
        kd.leverera_metod(self.slug)
        self.forbered()
        m=kd.metodinfo(self.slug,'skiss');f=self.root/m['delar']['före'][0]
        self.assertIn(str(f.relative_to(self.root)),kd.skiss_prompt(self.slug,'k01'))
        f.write_bytes(f.read_bytes()+b'\nSyntetiskt nytt krav.\n')
        with self.assertRaises(ValueError):ab.skisskrav(self.slug)
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])

    def test_senare_dom_far_inte_dolja_andrad_gammal_dom_eller_historik(self):
        dom=skapande.lagg_till_dom(self.slug,'ägaren','ny_riktning','Syntetisk tidigare dom',underlag=atelje.UNDERLAG,tid='2025-01-01T00:00:00Z')
        hist=self.u/skapande.HISTORIK;self.skriv(hist,'[]')
        self.forbered()
        for k in ('k01','k02'):
            kd.satt_status(self.slug,k,'ofullstandig',forsok=1);ab.skissavslutad(self.slug,k)
        skapande.lagg_till_dom(self.slug,'ägaren','forkasta','Syntetiskt, ingen kvalitetsdom.',underlag=atelje.UNDERLAG,tid='2026-01-02T00:00:00Z',plan=kd.plan_tid(self.slug))
        self.assertTrue(ab.skissresultat(self.slug)['jamforbara_kallor'])
        # Samma byteantal: det får inte vara ett trasigt JSON-snitt som råkar fälla ändringen.
        f=self.u/skapande.DOMLOGG;fore=f.read_bytes();f.write_bytes(fore.replace(b'tidigare',b'utbyttxx'))
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])
        f.write_bytes(fore);hist.write_text('[{"namn":"Syntetisk ändring"}]')
        self.assertFalse(ab.skissresultat(self.slug)['jamforbara_kallor'])

    def test_saknad_kritikersvar_redovisas_som_okand_resurs(self):
        self.forbered();d=kd.kdir(self.slug,'k01')
        self.skriv(d/'svar-skiss-1.json',json.dumps({'session_id':'skapare','duration_ms':60000,'num_turns':3,'total_cost_usd':.2}))
        session={'session_id':'kritiker','duration_ms':120000,'num_turns':4,'total_cost_usd':.3}
        kd.satt_status(self.slug,'k01','ofullstandig',sessioner=[{'svar':'svar-skiss-1.json','session_id':'skapare'}],skisskritik={'gjord':True,'session':session})
        self.skriv(d/'SKISSKRITIK.json',json.dumps({'svar':'svar-skisskritik-1.json','session':session}))
        a=ab.skissresultat(self.slug)['armar']['k01']
        self.assertFalse(a['anvandning']['fullstandigt']);self.assertIsNone(a['anvandning']['minuter'])
        self.assertIn('svar-skisskritik-1.json',a['saknade_svar'])

    def test_aterstallning_skriver_inte_over_frammande_andring(self):
        f=kd.kdir(self.slug,'k01')/'UPPDRAG.md';ny='Syntetisk oberoende ändring.\n';riktig=atelje.skriv_json_atomiskt
        def skriv(p,data):
            if p.name=='UPPDRAGSMATERIAL.json':
                f.write_text(ny);raise OSError('syntetiskt skrivfel')
            return riktig(p,data)
        with patch.object(atelje,'skriv_json_atomiskt',skriv):
            with self.assertRaises((ValueError,OSError)):self.forbered()
        self.assertEqual(f.read_text(),ny)
        with self.assertRaises(ValueError):self.forbered()

    def test_ofullstandig_sessionsreferens_matchar_inte_en_annan_fil(self):
        self.forbered();d=kd.kdir(self.slug,'k01')
        self.skriv(d/'svar-skiss-1.json',json.dumps({'session_id':'skapare','duration_ms':60000,'num_turns':3,'total_cost_usd':.2}))
        kd.satt_status(self.slug,'k01','ofullstandig',sessioner=[{'svar':'svar-skiss-1.json','session_id':'skapare'}, {'avbruten':'syntetiskt avbrott, okänd fil och identitet'}])
        a=ab.skissresultat(self.slug)['armar']['k01']
        self.assertFalse(a['anvandning']['fullstandigt']);self.assertTrue(a['saknade_svar'])


if __name__=='__main__':unittest.main()
