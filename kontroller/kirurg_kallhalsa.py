#!/usr/bin/env python3
"""Beständig källhälsa vid den befintliga spaningen, ingen ny klocka eller hämtare."""
import json
from pathlib import Path
import time
from kirurg_loop import Loop,Vagrad,fil,hash_
import kundstart_beredning as kb


def las(rot):
    p=fil(Path(rot)/'HALSA.json',Path(rot))
    try:
        if p.stat().st_size>1_000_000:raise ValueError()
        d=json.loads(p.read_text())
        if d.get('schema')!=1 or not isinstance(d.get('kallor'),dict):raise ValueError()
        return d
    except FileNotFoundError:return {'schema':1,'kallor':{}}
    except (OSError,ValueError,TypeError,AttributeError):raise Vagrad('Källhälsan kunde inte läsas. Den skrivs inte över.') from None


def bokfor(rot,rapporter,snapshots,kandidater,aktuella=None):
    """Anropas under spanarens befintliga flock före nya snapshots kvitteras.

    Hela källans hämtning räknas; ett tomt men lyckat svar är inte ett fel.
    Oförändrad version skapar ingen ny signal. Signaltexten är data för analys,
    aldrig en instruktion att exekvera eller ett automatiskt införandemandat.
    """
    rot=Path(rot);d=las(rot);nu=time.time()
    for r in rapporter:
        kid=r.get('id') or hash_(r['namn'])[:20]
        gammal=d['kallor'].get(kid,{})
        d['kallor'][kid]={'id':kid,'namn':r['namn'],'forsok':nu,'senast_lyckad':gammal.get('senast_lyckad'),
                         'status':'fel' if r.get('fel') else 'ok','fel':r.get('fel'),
                         'version':snapshots.get(kid,{}).get('hash',gammal.get('version'))}
        if not r.get('fel'):d['kallor'][kid]['senast_lyckad']=nu
    # En källa som tagits bort ur registret står inte kvar som frisk eller fallen (2026-10-09: PTS och Konsumentverket
    # byttes till officiella flöden, och de gamla raderna stod kvar som fel). aktuella ges bara vid en hel körning.
    if aktuella is not None:d['kallor']={k:v for k,v in d['kallor'].items() if k in aktuella}
    # Hälsan får inte ligga kvar som frisk bara för att ett efterföljande
    # förslagsregister eller kandidatlista inte går att skriva.
    kb.atomiskt(rot/'HALSA.json',(json.dumps(d,ensure_ascii=False,sort_keys=True)+'\n').encode())
    loop=Loop(rot.parent/'forbattringar')
    for k in kandidater:
        if not k.get('materiell_andring') or not k.get('version'):continue
        kid=k.get('kalla_id')
        if not kid:continue
        loop.signal('kalla-'+hash_(k['dokument'])[:20],'Ändrad källa att jämföra med arbetssättet','forberedelse',
                    'spaning:'+kid,k['version'],k['sammanfattning'],k['dokument'])
    return d


def krav(rot,signaler):
    """Bara försök som bygger på spaningssignaler beror på denna källhälsa."""
    behov={s['kalla'].split(':',1)[1]:s['version'] for s in signaler if s['kalla'].startswith('spaning:')}
    if not behov:return
    d=las(rot)
    for kid,version in behov.items():
        k=d['kallor'].get(kid)
        if not k or k.get('status')!='ok' or k.get('version')!=version:
            raise Vagrad('Försökets källa är fallen eller har en annan observerad version. Samla aktuellt underlag först.')
