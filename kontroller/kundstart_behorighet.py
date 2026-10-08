#!/usr/bin/env python3
"""Ägarstyrda deltagare och roller, aldrig modell- eller kundverktyg."""
import secrets
import time
import kundstart as ks

ROLLER=('lasare','medverkande','beslutsfattare')
BESLUT=('forfragan','acceptera','klarlagg_uppgift')


def roll(c,eid,token):
    row=c.execute('SELECT roll FROM atkomst WHERE arende=? AND hash=?',(eid,ks.sha(token))).fetchone()
    if not row or row[0] not in ROLLER:raise ks.Obehorig('Ärendets behörighet kunde inte fastställas.')
    return row[0]


def tillat(c,eid,token,handling):
    r=roll(c,eid,token)
    if r=='lasare' or (handling in BESLUT and r!='beslutsfattare'):
        raise ks.Obehorig('Din ärendelänk ger inte behörighet för den handlingen.')
    return r


def bjud_in(lager,eid,revision,namn,r,dagar=7):
    if r not in ROLLER or type(dagar) is not int or not 1<=dagar<=90:raise ks.Vagrad('Ange deltagarens roll och giltighet.')
    ks.text(namn,120)
    with lager.trans() as c:
        d=lager._doc(c,eid)
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades före inbjudan.')
        if len(d.get('deltagare',{}))>=20:raise ks.Vagrad('Fler deltagare behöver intern bedömning.')
        person=ks.id_();token=secrets.token_urlsafe(32)
        d.setdefault('deltagare',{})[person]={'namn':namn,'roll':r,'aktiv':True}
        c.execute('INSERT INTO atkomst(hash,arende,person,utgang,roll) VALUES(?,?,?,?,?)',(ks.sha(token),eid,person,time.time()+dagar*86400,r))
        lager._spara(c,d)
        return {'arende':eid,'person':person,'nyckel':token,'roll':r,'revision':d['revision']}


def aterkalla_person(lager,eid,revision,person):
    with lager.trans() as c:
        d=lager._doc(c,eid)
        if type(revision) is not int or d['revision']!=revision:raise ks.Konflikt('Ärendet ändrades före återkallelsen.')
        p=d.get('deltagare',{}).get(person)
        if not p:raise ks.Vagrad('Deltagaren finns inte i ärendet.')
        c.execute('UPDATE atkomst SET aterkallad=1 WHERE arende=? AND person=?',(eid,person))
        p['aktiv']=False;lager._spara(c,d)
        return lager._vy(c,d)


def klarlagg(d,person,data):
    ks.falt(data,('id','text','skal'),('id','text','skal'));ks.nyckel(data['id'])
    u=d['uppgifter'].get(data['id'])
    if not u or not u.get('motsagelse'):raise ks.Vagrad('Uppgiften saknar en motsägelse att klarlägga.')
    ks.text(data['text']);ks.text(data['skal'],3000)
    d['historik'].append({'slag':'klarlagd_uppgift','uppgift':u,'skal':data['skal'],'person':person,'tid':time.time()})
    d['uppgifter'][u['id']]={**u,'text':data['text'],'person':person,'kalla':ks.id_(),
                           'motsagelse':False,'kunskap':'kunden_uppger','tid':time.time()}
