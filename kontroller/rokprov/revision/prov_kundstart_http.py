#!/usr/bin/env python3
"""Kundgränsen genom riktig lokal HTTP, med syntetiska privata ärenden."""
import contextlib
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import korregister
import kundstart
import kundstart_server


class Kundapi(unittest.TestCase):
    def setUp(self):
        self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close)
        self.root=Path(self.stack.enter_context(korregister.egen_tmp_med('nwp-kundstart-','kund-API-prov'))).resolve()
        self.lager=kundstart.Lager(self.root/'privat')
        self.e,self.token=self.lager.skapa('prov-webb','Provperson')
        self.server=kundstart_server.server(self.lager,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.stack.callback(self.server.server_close);self.stack.callback(self.thread.join,3);self.stack.callback(self.server.shutdown)
        self.port=self.server.server_address[1];self.host='127.0.0.1:%d'%self.port

    def anrop(self,path,method='GET',data=None,token=True,**head):
        headers={'Host':self.host,'Origin':'http://'+self.host}
        if token:headers['Authorization']='Bearer '+self.token
        headers.update(head)
        body=json.dumps(data).encode() if data is not None else None
        if body:headers['Content-Type']='application/json'
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        try:
            c.request(method,path,body,headers);r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
        finally:c.close()

    def test_egen_yta_utan_admin_och_ingen_atergiven_html(self):
        status,h,body=self.anrop('/')
        self.assertEqual(status,200)
        self.assertIn('Ditt uppdrag',body.decode())
        self.assertIn("default-src 'none'",h['Content-Security-Policy'])
        for path in ('/api/status','/fil/CLAUDE.md','/../CLAUDE.md','/api/kundstart'):
            self.assertEqual(self.anrop(path)[0],404)

    def test_host_origin_och_behorighet(self):
        path='/api/arende/'+self.e
        self.assertEqual(self.anrop(path)[0],200)
        self.assertEqual(self.anrop(path,token=False)[0],403)
        self.assertEqual(self.anrop(path,Host='evil.example')[0],403)
        self.assertEqual(self.anrop(path,Origin='https://'+self.host)[0],403)
        self.assertEqual(self.anrop(path,Origin='http://evil.example')[0],403)
        e,t=self.lager.skapa('prov-annat','Annan')
        self.assertEqual(self.anrop('/api/arende/'+e)[0],403)
        self.assertNotIn(self.token,self.anrop(path)[2].decode())

    def test_spara_konflikt_och_nekad_agarroll(self):
        path='/api/arende/'+self.e
        data={'revision':1,'operation':kundstart.id_(),'handling':'meddelande','data':{'text':'<script>alert(1)</script>'}}
        status,h,body=self.anrop(path,'POST',data)
        self.assertEqual(status,200)
        self.assertTrue(h['Content-Type'].startswith('application/json'))
        self.assertEqual(self.anrop(path,'POST',data)[2],body)
        data['operation']=kundstart.id_()
        self.assertEqual(self.anrop(path,'POST',data)[0],409)
        data.update(revision=2,handling='erbjudande',data={})
        self.assertEqual(self.anrop(path,'POST',data)[0],400)


if __name__=='__main__':
    if '--provserver' in sys.argv:
        import signal
        def stoppa(*_):raise SystemExit(0)
        signal.signal(signal.SIGTERM,stoppa)
        with korregister.egen_tmp_med('nwp-kundstart-','syntetiskt webbläsarprov') as temp:
            lager=kundstart.Lager(Path(temp).resolve()/'privat')
            eid,token=lager.skapa('prov-webblasare','Syntetisk deltagare')
            e2,t2=lager.skapa('prov-webblasare-forslag','Syntetisk deltagare',modellbudget=1)
            d=lager.kundhandling(e2,t2,1,kundstart.id_(),'meddelande',{'text':'Vi vill tydliggöra erbjudandet.'})
            jobb=lager.ta_jobb('provmodell')
            lager.modellsvar(jobb,{'text':'Pröva denna sammanfattning.','forslag':[{'id':'erbjudande','amne':'A','text':'Ett tydligare erbjudande.',
                'kunskap':'tolkning','kallor':[d['meddelanden'][0]['id']]}],'fragor':[]})
            # Returfrågan kommer från en verklig lokal överlämning, ingen fristående UI-stubb.
            import kundstart_beredning as kb
            import kundstart_fortsatt as kf
            with lager.trans() as c:
                doc=lager._doc(c,e2)
                v={'namn':'Exempelverkstaden','rackvidd':{'typ':'nationell'},'tjanster':['Reparationer'],'kontaktvagar':[]}
                doc['verksamhet_forslag']=kb.forslag(doc,{'varden':v,'kallor':{k:[d['meddelanden'][0]['id']] for k in v}})
                lager._spara(c,doc)
            doc=lager.las(e2,t2)
            doc=lager.kundhandling(e2,t2,doc['revision'],kundstart.id_(),'bekrafta_verksamhet',{'sha256':doc['verksamhet_forslag']['sha256']})
            repo=Path(temp).resolve()/'repo';repo.mkdir()
            p=kb.overlamna(lager,e2,doc['revision'],'webbprov-overlamning',repo)
            kf.returfraga(lager,e2,doc['revision'],p['id'],{'id':'mottagare','amne':'F','text':'Vem tar emot förfrågningar?',
                'varfor':'Mottagaren behövs för formuläret.','fas':'helbygge','kritisk':True,'ansvarig':'kund'})
            import kundstart_behorighet as kh
            e3,t3=lager.skapa('prov-motsagelse','Första provrollen')
            d3=lager.kundhandling(e3,t3,1,kundstart.id_(),'uppgift',{'id':'mal','amne':'A','text':'Första uppgiften.'})
            annan=kh.bjud_in(lager,e3,d3['revision'],'Andra provrollen','medverkande')
            d3=lager.las(e3,t3)
            lager.kundhandling(e3,annan['nyckel'],d3['revision'],kundstart.id_(),'uppgift',{'id':'mal','amne':'A','text':'En motsägande uppgift.'})
            d3=lager.las(e3,t3);lasare=kh.bjud_in(lager,e3,d3['revision'],'Läsande provroll','lasare')
            s=kundstart_server.server(lager,port=0)
            print(json.dumps({'port':s.server_address[1],'arende':eid,'nyckel':token,'forslag_arende':e2,'forslag_nyckel':t2,'konflikt_arende':e3,'konflikt_nyckel':t3,'lasare_nyckel':lasare['nyckel']}),flush=True)
            try:s.serve_forever()
            finally:s.server_close()
    else:unittest.main()
