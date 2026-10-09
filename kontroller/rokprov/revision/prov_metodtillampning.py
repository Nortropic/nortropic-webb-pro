#!/usr/bin/env python3
"""P4/P5: aktiv prompt och tillåtelse, inte ett bevis för modellens tillämpning."""
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import atelje
import bildkedja
import kompetens
import korregister
import metod
import sandlada


class Metodtillampning(unittest.TestCase):
    def test_vantande_skill_far_read_aven_i_rollens_karnrad(self):
        skills, las = kompetens.aktiverbara(['emil-animate/SKILL.md','frontend-design/SKILL.md'])
        self.assertEqual(skills,['frontend-design'])
        self.assertEqual(las,['emil-animate/SKILL.md'])
        text='\n'.join(kompetens.prompt_rader('granskning','prov-metod','k01'))
        self.assertNotIn('emil-apple-design aktiveras med Skill-verktyget',text)

    def test_faktiskt_read_kvitto_kraver_inte_en_nekad_skillaktivering(self):
        with korregister.egen_tmp_med('nwp-kallgap-','integrerat Read-kvitto') as td:
            for ps, roll, valt in [('rorelse','rorelse',[]),('granskning','granskning',['.claude/skills/emil-apple-design/SKILL.md'])]:
                with self.subTest(pass_=ps):
                    rader=[]
                    for i,rel in enumerate(kompetens.lasfiler(ps)+valt):
                        p=kompetens.ROOT/rel; delar=Path(rel).parts
                        normal=len(delar)==4 and delar[:2]==('.claude','skills') and delar[3]=='SKILL.md' and not delar[2].startswith('emil-')
                        name='Skill' if normal else 'Read'
                        data={'skill':delar[2]} if normal else {'file_path':str(p)}
                        rader.extend([{'type':'assistant','message':{'content':[{'type':'tool_use','id':f't{i}','name':name,'input':data}]}},
                                      {'type':'user','message':{'content':[{'type':'tool_result','tool_use_id':f't{i}','content':p.read_text()}]}}])
                    p=Path(td)/(ps+'.jsonl');p.write_text(''.join(json.dumps(x)+'\n' for x in rader))
                    with patch.object(bildkedja,'transkript',return_value=p):kv=kompetens.kvitto(['syntetisk-'+ps],ps)
                    rad=next(x for x in kv['tillstand'] if x['roll']==roll)
                    self.assertFalse(kv['saknas'])
                    self.assertNotIn('delvis',rad['nivaer']['aktivering'])
                    self.assertNotIn('utan aktivering',rad['nivaer']['aktivering'])
                    self.assertFalse(any(x.startswith('emil-') for x in rad['skillverktyget']['anrop']))
                    self.assertEqual(rad['tillampning'],'inte observerat')

    def test_vantande_skill_lases_med_read_i_alla_pass(self):
        for pass_ in kompetens.PASS:
            with self.subTest(pass_=pass_):
                text='\n'.join(kompetens.prompt_rader(pass_,'prov-metod','k01'))
                self.assertIn('Initial Response',text)
                self.assertIn('bara med Read',text)
                self.assertIn('ingen svarar',text)

    def test_mappnamn_och_metadatanamn_nekas_vid_verklig_argumentgenerering(self):
        args=atelje.session_args(['Read','Skill'],slug=None)
        nekade=args[args.index('--disallowedTools')+1:]
        for n in ('emil-animate','animate','emil-mobile-native','mobile-native'):
            self.assertIn('Skill(%s)'%n,nekade)
            self.assertIn('Skill(%s *)'%n,nekade)
        self.assertNotIn('Skill(frontend-design)',nekade)
        self.assertNotIn('Read(./.claude/skills/emil-animate/**)',nekade)

    def test_samma_nekande_i_helbyggets_installningar_med_och_utan_sandlada(self):
        for pa in (False,True):
            d=sandlada.installningar('prov-metod',sandlada=pa)
            self.assertIn('Skill(animate)',d.get('permissions',{}).get('deny',[]))
            self.assertIn('Skill(emil-animate *)',d['permissions']['deny'])

    def test_varven_motsager_inte_den_befintliga_kvoten(self):
        for pass_ in ('skapa','fordjupa'):
            text='\n'.join(kompetens.prompt_rader(pass_,'prov-metod','k01'))
            self.assertNotIn('bekräfta högst en gång',text)
            # inget minsta antal varv i något läge (ägarens uppdrag 2026-10-09, punkt 10): de tre varven är borttagna
            self.assertIn('inget minsta antal i något läge',text)
            self.assertNotIn('minst tre',text)
        self.assertIn('bekräfta högst en gång','\n'.join(kompetens.prompt_rader('rorelse','prov-metod','k01')))

    def test_css_radets_begransning_foljer_med_metodleveransen(self):
        with korregister.egen_tmp_med('nwp-kallgap-','metodens leveransprov') as td:
            for steg in ('skiss','skapa','forfina','granska'):
                r=metod.leverera(steg,Path(td)/steg)
                text='\n'.join(Path(f['fil']).read_text() for f in r['filer'] if f['del']=='före')
                self.assertIn('CSS garanterar inte',text)
                self.assertIn('layout, paint och compositing',text)


if __name__=='__main__':unittest.main()
