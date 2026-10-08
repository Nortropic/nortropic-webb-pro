#!/usr/bin/env python3
"""Gallring och återställning av enbart provets registrerade syntetiska ärenden."""
import json
from pathlib import Path
import sqlite3
import sys
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import prov_kundstart_beredning as grundprov
import kundstart as ks
import kundstart_beredning as kb
import kundstart_lagring as kl


class Lagring(unittest.TestCase):
    gor=grundprov.Beredning.gor
    forslag=grundprov.Beredning.forslag
    bekrafta=grundprov.Beredning.bekrafta
    def setUp(self):
        grundprov.Beredning.setUp(self);self.bekrafta();self.repo=self.rot/'repo';self.repo.mkdir()
        self.gor('bilaga',{'namn':'syntetiskt.txt','typ':'text/plain','data':'c3ludGV0aXNrdA=='})
        d=self.db.internt(self.e);kb.overlamna(self.db,self.e,d['revision'],'export-for-gallring',self.repo)
        self.u=self.repo/'underlag'/d['slug']

    def gallringsdatum(self,dag):
        d=self.db.internt(self.e)
        return kl.lagringsbeslut(self.db,self.e,d['revision'],dag,'Avgränsat syntetiskt prov.','Provets ägare')

    def test_uteblivet_beslut_och_framtida_datum_raderar_inget(self):
        d=self.db.internt(self.e)
        with self.assertRaises(ks.Vagrad):kl.gallra(self.db,self.e,d['revision'])
        d=self.gallringsdatum(time.time()+86400)
        with self.assertRaises(ks.Vagrad):kl.gallra(self.db,self.e,d['revision'])
        self.assertTrue((self.u/'KUNDSTART.json').exists());self.assertTrue(self.db.las(self.e,self.token))

    def test_onlinekopia_gallring_och_aterstallning_aterupplivar_inte_arendet(self):
        annat,tok=self.db.skapa('prov-bevarad','Annan syntetisk deltagare')
        copy=kl.sakerhetskopiera(self.db)
        d=self.gallringsdatum(time.time()-10);out=kl.gallra(self.db,self.e,d['revision'])
        self.assertEqual(out['status'],'klar',out)
        self.assertFalse((self.u/'KUNDSTART.json').exists())
        self.assertFalse(any(self.u.rglob('syntetiskt.txt')))
        with self.assertRaises(ks.Obehorig):self.db.las(self.e,self.token)
        with sqlite3.connect(self.db.fil) as c:
            for tab in ('arenden','revisioner','operationer','atkomst','bilagor','jobb','overlamningar'):
                f='id' if tab=='arenden' else 'arende'
                self.assertEqual(c.execute('SELECT count(*) FROM '+tab+' WHERE '+f+'=?',(self.e,)).fetchone()[0],0,tab)
        restored=kl.aterstall(self.db,copy['id'],self.rot/'aterstalld')
        with self.assertRaises(ks.Obehorig):restored.internt(self.e)
        self.assertEqual(restored.internt(annat)['slug'],'prov-bevarad')
        with self.assertRaises(ks.Obehorig):restored.las(annat,tok)
        with self.assertRaises(ks.Vagrad):kl.aterstall(self.db,copy['id'],self.rot/'aterstalld')

    def test_avbrott_efter_spärr_lamnar_atkomst_nekad_och_kan_aterupptas(self):
        copy=kl.sakerhetskopiera(self.db);d=self.gallringsdatum(time.time()-10)
        with patch.object(kl,'rensa_kopior',side_effect=OSError('syntetiskt avbrott')):
            with self.assertRaises(OSError):kl.gallra(self.db,self.e,d['revision'])
        with self.assertRaises(ks.Obehorig):self.db.las(self.e,self.token)
        # Äldre backup finns kvar efter felet. Nuvarande spärr ska filtrera den.
        restored=kl.aterstall(self.db,copy['id'],self.rot/'efter-avbrott')
        with self.assertRaises(ks.Obehorig):restored.internt(self.e)
        out=kl.gallra(self.db,self.e,d['revision']);self.assertEqual(out['status'],'klar',out)

    def test_främmande_filer_och_senare_byten_redovisas_utan_radering(self):
        target=self.u/'VERKSAMHET.json';target.write_text('{"främmande":"byte"}')
        extra=self.u/'RESEARCH.md';extra.write_text('Ett senare härlett syntetiskt underlag.')
        d=self.gallringsdatum(time.time()-10);out=kl.gallra(self.db,self.e,d['revision'])
        self.assertEqual(out['status'],'ofullstandig');self.assertTrue(target.exists());self.assertTrue(extra.exists())
        self.assertTrue(any('VERKSAMHET.json' in x for x in out['kvar']));self.assertTrue(any('RESEARCH.md' in x for x in out['kvar']))
        with self.assertRaises(ks.Obehorig):self.db.las(self.e,self.token)

    def test_symlankad_eller_andrad_backup_nekas_utan_andrat_aterstallningsmal(self):
        copy=kl.sakerhetskopiera(self.db);b=self.db.rot/'sakerhetskopior'/copy['id']/'arenden.sqlite3'
        with b.open('ab') as f:f.write(b'forandrad')
        mal=self.rot/'oforandrad'
        with self.assertRaises(ks.Vagrad):kl.aterstall(self.db,copy['id'],mal)
        self.assertFalse(mal.exists())
        b.unlink();b.symlink_to(self.db.fil)
        with self.assertRaises(ks.Vagrad):kl.aterstall(self.db,copy['id'],mal)
        self.assertFalse(mal.exists())

    def test_backuparkiv_sparas_utan_raderat_id_och_spärren_foljer_med(self):
        copy=kl.sakerhetskopiera(self.db);d=self.gallringsdatum(time.time()-1)
        kl.gallra(self.db,self.e,d['revision'])
        b=self.db.rot/'sakerhetskopior'/copy['id']/'arenden.sqlite3'
        with sqlite3.connect(b) as c:self.assertEqual(c.execute('SELECT count(*) FROM arenden WHERE id=?',(self.e,)).fetchone()[0],0)
        restored=kl.aterstall(self.db,copy['id'],self.rot/'ny')
        self.assertIn(self.e,kl.journal(restored)['arenden'])
        # En lagringsjournal som inte går att tolka betyder inte att allt får läsas.
        (restored.rot/'GALLRING.json').write_text('{')
        with self.assertRaises(ks.Vagrad):kl.journal(restored)

    def test_privat_kontobelagg_gallras_ocksa(self):
        f=self.db.rot/'bevis'/self.e/'kontoprov.txt';f.parent.mkdir(parents=True);f.write_text('Syntetiskt kontobelägg.')
        d=self.gallringsdatum(time.time()-1);out=kl.gallra(self.db,self.e,d['revision'])
        self.assertEqual(out['status'],'klar',out);self.assertFalse(f.exists())

    def test_sparrat_arende_i_kon_stoppar_inte_andra_arenden(self):
        self.gor('meddelande',{'text':'Köa det första ärendet.'})
        d=self.gallringsdatum(time.time()-1)
        # Nytt svar ger en aktuell köpost även efter ägarens lagringsbeslut.
        d=self.gor('meddelande',{'text':'Syntetiskt sista svar.'})
        other,tok=self.db.skapa('prov-kovar','Syntetisk deltagare',modellbudget=2)
        self.db.kundhandling(other,tok,1,ks.id_(),'meddelande',{'text':'Andra ärendet ska kunna fortsätta.'})
        with patch.object(kl,'rensa_kopior',side_effect=OSError('avbrott')):
            with self.assertRaises(OSError):kl.gallra(self.db,self.e,d['revision'])
        job=self.db.ta_jobb('prov');self.assertEqual(job['arende'],other)
        self.db.modellfel(job,'timeout')
        old=self.db.las(other,tok)
        self.db.kundhandling(other,tok,old['revision'],ks.id_(),'forsok_igen',{})
        self.assertIsNotNone(self.db.avstangd_modell())

    def test_backupens_manifestfel_kan_aterupptas_utan_att_annat_arende_forloras(self):
        other,tok=self.db.skapa('prov-bevarad-kopia','Syntetisk deltagare')
        copy=kl.sakerhetskopiera(self.db);d=self.gallringsdatum(time.time()-1)
        real=kb.atomiskt
        def fel(p,b):
            if p.name=='MANIFEST.json':raise OSError('syntetiskt avbrott efter db-byte')
            return real(p,b)
        with patch.object(kb,'atomiskt',side_effect=fel):
            out=kl.gallra(self.db,self.e,d['revision'])
        self.assertEqual(out['status'],'ofullstandig')
        out=kl.gallra(self.db,self.e,d['revision']);self.assertEqual(out['status'],'klar',out)
        restored=kl.aterstall(self.db,copy['id'],self.rot/'aterhamtad-backup')
        self.assertEqual(restored.internt(other)['slug'],'prov-bevarad-kopia')
        with self.assertRaises(ks.Obehorig):restored.internt(self.e)

if __name__=='__main__':unittest.main()
