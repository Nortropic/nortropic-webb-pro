#!/usr/bin/env python3
"""Ägarens riktiga HTTP-ingång, ingen modell eller driftserver."""
import contextlib
import http.client
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'dashboard'))
import korregister
import server as dash
import kundstart as ks
import kundstart_agare as ka

class Agare(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-','ägarens HTTP-prov'))).resolve()
        self.stack.enter_context(patch.object(dash,'ROOT',self.root))
        self.server=dash.ThreadingHTTPServer(('127.0.0.1',0),dash.H)
        self.host='127.0.0.1:'+str(self.server.server_address[1])
        self.stack.enter_context(patch.dict(dash.VARD,{'tillatna':{self.host}}))
        t=threading.Thread(target=self.server.serve_forever,daemon=True);t.start()
        self.addCleanup(lambda:(self.server.shutdown(),self.server.server_close(),t.join(3)))
    def req(self,method,path,data=None,origin=True):
        c=http.client.HTTPConnection(self.host,timeout=10)
        try:
            h={'Content-Type':'application/json'}
            if origin:h['Origin']='http://'+self.host
            c.request(method,path,None if data is None else json.dumps(data),headers=h)
            r=c.getresponse();return r.status,json.loads(r.read())
        finally:c.close()
    def skapa(self):
        return self.req('POST','/api/kundstart',{'slug':'prov-agare','namn':'Syntetisk kund','fiktiv':True,'modellbudget':0,'operation':'samma-start'})
    def test_agaren_kan_skapa_och_se_men_ingen_modell_startar(self):
        status,d=self.skapa();self.assertEqual(status,200,d);self.assertTrue(d['nyckel'])
        status,rows=self.req('GET','/api/kundstart');self.assertEqual(status,200);self.assertEqual(len(rows['arenden']),1)
        self.assertNotIn(d['nyckel'],json.dumps(rows))
        status,detail=self.req('GET','/api/kundstart/'+d['arende']);self.assertEqual(status,200,detail)
        self.assertEqual(detail['arende']['modell']['status'],'inte_startad')
        self.assertIsNone(detail['drift']['kundserver_aktiverad']);self.assertIsNone(detail['drift']['modell_aktiverad'])
        self.assertFalse(detail['faser']['helbygge']['kan_starta'])
        again=self.skapa()[1];self.assertEqual(again['arende'],d['arende']);self.assertIsNone(again['nyckel'])
        self.assertEqual(len(self.req('GET','/api/kundstart')[1]['arenden']),1)
    def test_ny_operation_for_upptagen_slug_ar_en_begriplig_konflikt(self):
        d=self.skapa()[1]
        status,r=self.req('POST','/api/kundstart',{'slug':'prov-agare','namn':'Provroll','fiktiv':True,'modellbudget':0,'operation':'annan-start'})
        self.assertEqual(status,409);self.assertNotIn('IntegrityError',json.dumps(r))
        self.assertEqual(len(self.req('GET','/api/kundstart')[1]['arenden']),1)

    def test_ursprung_och_godtycklig_handling_nekas(self):
        st,d=self.req('POST','/api/kundstart',{'slug':'prov-agare'},origin=False);self.assertEqual(st,403)
        d=self.skapa()[1]
        for action in ('publicera','shell','mandat','godkann_design'):
            st,_=self.req('POST','/api/kundstart/'+d['arende']+'/'+action,{'revision':1,'kommando':'forbjudet'})
            self.assertEqual(st,404)
    def test_overlamning_fore_bekraftad_verksamhet_ar_inte_klar(self):
        d=self.skapa()[1]
        st,result=self.req('POST','/api/kundstart/'+d['arende']+'/overlamna',{'revision':1,'operation':'overlamning-prov'})
        self.assertEqual(st,400,result)
        self.assertNotIn('klar',json.dumps(result))
        st,detail=self.req('GET','/api/kundstart/'+d['arende'])
        self.assertIsNone(detail['arende']['overlamning']);self.assertFalse(detail['faser']['forberedelse']['kan_starta'])
    def test_ny_lank_ar_explicit_och_gammal_lank_gar_inte_att_lista(self):
        d=self.skapa()[1]
        st,new=self.req('POST','/api/kundstart/'+d['arende']+'/deltagare',{'revision':1,'namn':'Medverkande','roll':'medverkande','dagar':3})
        self.assertEqual(st,200,new);self.assertEqual(new['roll'],'medverkande')
        body=self.req('GET','/api/kundstart/'+d['arende'])[1]
        self.assertNotIn(new['nyckel'],json.dumps(body));self.assertNotIn(d['nyckel'],json.dumps(body))

    def grund(self,fragor=()):
        import kundstart_beredning as kb
        db=ka.lager(self.root);e,t=db.skapa('prov-fas','Provroll',modellbudget=10)
        def gor(n,data):return db.kundhandling(e,t,db.las(e,t)['revision'],ks.id_(),n,data)
        def bekrafta(q=()):
            j=db.ta_jobb('prov');mid=next(m['id'] for m in j['dokument']['meddelanden'] if m['roll']=='kund')
            v={'namn':'Syntetisk verkstad','kontaktvagar':[],'rackvidd':{'typ':'nationell'},'tjanster':['Syntetisk tjänst']}
            self.assertTrue(db.modellsvar(j,{'text':'Syntetiskt förslag','forslag':[],'fragor':list(q),'verksamhet':{'varden':v,'kallor':{n:[mid] for n in v}}}))
            return gor('bekrafta_verksamhet',{'sha256':db.las(e,t)['verksamhet_forslag']['sha256']})
        gor('meddelande',{'text':'Syntetisk verksamhet och tjänst.'});gor('uppgift',{'id':'mal','amne':'A','text':'Syntetiskt mål.'})
        bekrafta(fragor)
        return db,e,t,gor,bekrafta

    def test_kritisk_modellfraga_ar_olost_provning_inte_tyst_startbesked(self):
        q={'id':'kritisk','amne':'A','text':'Vilket mål gäller?','varfor':'Behövs för förberedelsen.','paverkar':'Förberedelse','kritisk':True}
        db,e,t,gor,bekrafta=self.grund([q]);st,d=self.req('GET','/api/kundstart/'+e)
        self.assertEqual(st,200)
        for fas in ('forberedelse','skiss','helbygge'):
            self.assertFalse(d['faser'][fas]['kan_starta'],fas)
            self.assertTrue(any('Vilket mål gäller?' in x for x in d['faser'][fas]['brister']))
        gor('meddelande',{'text':'Målet är nu preciserat.'});bekrafta()
        self.assertTrue(self.req('GET','/api/kundstart/'+e)[1]['faser']['forberedelse']['kan_starta'])

    def test_aktuellt_erbjudande_och_gammal_design_ersatter_inte_overlamning(self):
        import kundstart_beredning as kb
        import skapande
        db,e,t,gor,bekrafta=self.grund()
        def acceptera():
            d=gor('forfragan',{});p=db.erbjudande(e,d['revision'],'Syntetisk omfattning','Syntetiska villkor','Provroll')
            return gor('acceptera',{'erbjudande':p['id']})
        d=acceptera();kb.overlamna(db,e,d['revision'],'forsta',self.root)
        u=self.root/'underlag/prov-fas';kod=u/'atelje/vinnare/kod/index.astro';kod.parent.mkdir(parents=True);kod.write_text('<h1>Syntetisk skiss</h1>')
        tid='2026-10-08T00:00:00Z';g={'tid':tid,'sha_index':ks.sha(kod.read_bytes())}
        (u/'atelje/VINNARE.json').write_text(json.dumps({'godkand':g}))
        (u/'DESIGNDOMAR.jsonl').write_text(json.dumps({'kalla':'ägaren','beslut':'godkand','tid':tid,'text':'Syntetisk provdom.'})+'\n')
        self.assertTrue(skapande.godkand_giltig('prov-fas',self.root/'underlag',self.root/'kunder')[0])
        self.assertTrue(self.req('GET','/api/kundstart/'+e)[1]['faser']['helbygge']['kan_starta'])
        gor('uppgift',{'id':'mal','amne':'A','text':'Ett annat syntetiskt mål.'});bekrafta();acceptera()
        d=self.req('GET','/api/kundstart/'+e)[1]
        self.assertTrue(d['arende']['bestallning']['aktuell']);self.assertFalse(d['arende']['overlamning']['aktuell'])
        self.assertFalse(d['faser']['helbygge']['kan_starta'])
        self.assertTrue(any('överlämn' in x for x in d['faser']['helbygge']['brister']))

if __name__=='__main__':
    if '--provserver' in sys.argv:
        import signal
        def stopp(*_):raise SystemExit(0)
        signal.signal(signal.SIGTERM,stopp)
        with korregister.egen_tmp_med('nwp-kundstart-','ägarens webbläsarprov') as tmp:
            dash.ROOT=Path(tmp).resolve()
            dash.UNDERLAG,dash.KUNDER=dash.ROOT/'underlag',dash.ROOT/'kunder'  # arbetsytans ram läser kundlistan: provrotens, aldrig repots
            # handlingskön, nyckelintaget och aktiveringens torrkörning: provrotens kataloger, aldrig repots eller ägarens nycklar
            import atelje,exportera
            atelje.ROOT,atelje.UNDERLAG,atelje.KUNDER=dash.ROOT,dash.UNDERLAG,dash.KUNDER
            exportera.ROOT,exportera.UNDERLAG,exportera.KUNDER=dash.ROOT,dash.UNDERLAG,dash.KUNDER
            os.environ['NWP_NYCKELINTAG']=str(dash.ROOT/'nyckelintag');os.environ['NWP_CLOUDFLARE_FIL']=str(dash.ROOT/'saknas'/'cloudflare.env')
            s=dash.ThreadingHTTPServer(('127.0.0.1',0),dash.H)
            dash.VARD['tillatna']={'127.0.0.1:'+str(s.server_address[1])}
            print(json.dumps({'port':s.server_address[1]}),flush=True)
            try:s.serve_forever()
            finally:s.server_close()
    else:unittest.main()
