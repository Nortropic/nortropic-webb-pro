#!/usr/bin/env python3
"""Avgränsade anropsmått i samma privata ärendelagring. Inga råpromptar eller nycklar."""
import json
import time
import kundstart as ks


def namn(v):
    try:return ks.text(v,120)
    except ks.Vagrad:return None


def tal(v):
    return v if type(v) is int and 0<=v<=10**10 else None


def start(lager,jobb,modell,c):
    p={'schema':1,'id':jobb['lease_id'],'jobb':jobb['id'],'revision':jobb['revision'],
       'start':time.time(),'slut':None,'sekunder':None,'status':'pagar','slag':None,
       'modell_begard':namn(modell),'modell_observerad':None,'metod_sha256':None,'transportlage':'inte_startad',
       'input_tokens':None,'output_tokens':None,'cache_read_input_tokens':None,'cache_creation_input_tokens':None,
       'kostnad':None,'kostnadsbesked':'Inte observerad. Ingen prisschablon eller abonnemangskvot antas.'}
    # Samma SQL-transaktion som lease och budget: inget hårt avbrott får skapa ett glapp.
    c.execute('INSERT INTO modellanrop VALUES(?,?,?)',(p['id'],jobb['arende'],ks.jsontext(p)))
    return p


def avbrutna(c):
    for row in c.execute("SELECT m.id,m.post FROM modellanrop m JOIN jobb j ON j.lease_id=m.id WHERE j.lease_slut<=?",(time.time(),)).fetchall():
        p=json.loads(row['post'])
        if p['status']!='pagar':continue
        p.update(status='avbruten',slag='lease_utgangen',slut=None,sekunder=None)
        c.execute('UPDATE modellanrop SET post=? WHERE id=?',(ks.jsontext(p),row['id']))


def observation(lager,jobb,data):
    with lager.trans() as c:
        lager._doc(c,jobb['arende'])
        row=c.execute('SELECT post FROM modellanrop WHERE id=?',(jobb['lease_id'],)).fetchone()
        if not row:return
        p=json.loads(row[0])
        if p['status']!='pagar':return
        p.update({k:data[k] for k in ('metod_sha256','transportlage') if k in data})
        c.execute('UPDATE modellanrop SET post=? WHERE id=?',(ks.jsontext(p),p['id']))


def slut(lager,jobb,p,utfall,sekunder,observation):
    tillatna=('modell_observerad','metod_sha256','transportlage','input_tokens','output_tokens','cache_read_input_tokens','cache_creation_input_tokens')
    p.update(status=utfall['status'],slag=utfall.get('slag'),slut=time.time(),sekunder=sekunder)
    p.update({k:observation[k] for k in tillatna if k in observation})
    with lager.trans() as c:
        # Gallring under anropet får aldrig återskapa ett ärende eller dess mätdata.
        from kundstart_lagring import journal
        if jobb['arende'] in journal(lager)['arenden']:return
        row=c.execute('SELECT post FROM modellanrop WHERE id=?',(p['id'],)).fetchone()
        if not row or json.loads(row[0])['status']!='pagar':return  # en utgången lease kan inte bli klar sent
        c.execute('UPDATE modellanrop SET post=? WHERE id=? AND arende=?',(ks.jsontext(p),p['id'],jobb['arende']))


def lista(lager,eid):
    with lager.trans() as c:
        lager._doc(c,eid)
        return [json.loads(x[0]) for x in c.execute('SELECT post FROM modellanrop WHERE arende=? ORDER BY rowid',(eid,))]
