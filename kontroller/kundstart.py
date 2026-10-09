#!/usr/bin/env python3
"""Privat Kundstart: ett transaktionellt ärende, ingen modell- eller byggsession.

Kund-API:t använder endast kundhandling/las/bilaga. Ägaroperationer exponeras
inte där. Modellarbetaren får ett versionsbundet jobb och lämnar förslag;
den kan inte skriva faktabekräftelse, offert, order eller filsystemsvägar.
Lokal SQLite kräver beständig privat disk. Ingen drift aktiveras vid import.
"""
import base64
import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import stat
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'[a-z0-9][a-z0-9-]{0,51}\Z')
IDENTITET = re.compile(r'[A-Za-z0-9_-]{1,80}\Z')
MAX_TEXT = 30000
MAX_BILAGA = 4 * 1024 * 1024
AMNEN = tuple('ABCDEFGHIJ')


class Vagrad(ValueError):
    pass


class Konflikt(Vagrad):
    pass


class Obehorig(Vagrad):
    pass


def id_():
    return uuid.uuid4().hex


def jsontext(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def sha(v):
    return hashlib.sha256(v if isinstance(v, bytes) else jsontext(v).encode()).hexdigest()


def text(v, maxlangd=MAX_TEXT):
    if not isinstance(v, str) or not v.strip() or len(v) > maxlangd or '\x00' in v:
        raise Vagrad('Texten saknas, är för lång eller innehåller otillåtna tecken.')
    # Samma detektor som commitvakten; ingen träfftext lämnar funktionen.
    spec = importlib.util.spec_from_file_location('kundstart_hemligheter', ROOT / '.claude/hooks/commitvakt.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if mod.hemlighet_i_text(v):
        raise Vagrad('Texten ser ut att innehålla en nyckel eller hemlighet. Ta bort den och försök igen.')
    return v


def nyckel(v):
    if not isinstance(v, str) or not IDENTITET.fullmatch(v):
        raise Vagrad('Ogiltig identitet.')
    return v


def falt(data, tillatna, krav=()):
    if not isinstance(data, dict) or set(data) - set(tillatna) or set(krav) - set(data):
        raise Vagrad('Handlingen har fel fält.')


def kundkallor(d):
    """Mottagna kundkällor; AI:s tidigare formulering är ingen oberoende källa."""
    return ({m['id'] for m in d['meddelanden'] if m['roll']=='kund'}
            | {u['kalla'] for u in d['uppgifter'].values()}
            | {i['kalla'] for i in d.get('integrationer',{}).values()})


def omfattning(d):
    # Samtal och servermetadata är inte nya omfattningsbeslut. En ändrad uppgift,
    # kundens val eller materialrätt påverkar däremot den accepterade versionen.
    o = {'uppgifter': d['uppgifter'], 'material': d['material'],
         'verksamhet':(d.get('verksamhet') or {}).get('varden'),
         'integrationer':{k:{n:v for n,v in i.items() if n not in ('utredning',)} for k,i in d.get('integrationer',{}).items()}}
    # Ägarens paketval ur integrationskatalogen (kundstart_integration.py) är också omfattning; ett ärende utan val
    # behåller sin tidigare hash.
    if d.get('integrationsval'):
        o['integrationsval'] = {k:{n:v for n,v in i.items() if n != 'tid'} for k,i in d['integrationsval'].items()}
    return sha(o)


def vy(d):
    d = json.loads(jsontext(d))
    d['bestallning']['aktuell'] = (d['bestallning'].get('status') == 'accepterad'
                                  and d['bestallning'].get('omfattning') == omfattning(d))
    d['beredskap'] = {a: 'underlag_finns' if any(x['amne'] == a for x in d['uppgifter'].values()) else 'okant' for a in AMNEN}
    d['beredskap']['innebord'] = 'Ämnestäckning, inte färdigprocent eller godkänd kvalitet.'
    return d


class Lager:
    def __init__(self, rot=None):
        if os.environ.get('NWP_SLUG'):
            raise Vagrad('Kundärenden får inte hanteras av en byggsession.')
        self.rot = Path(rot or ROOT / 'underlag/kundstart').absolute()
        for p in (self.rot, *self.rot.parents):
            if p.is_symlink():
                raise Vagrad('Ärendelagringen får inte gå genom en symbolisk länk.')
        self.rot.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.rot, 0o700)
        self.fil = self.rot / 'arenden.sqlite3'
        with self.trans() as c:
            c.executescript('''
                CREATE TABLE IF NOT EXISTS arenden(id TEXT PRIMARY KEY, slug TEXT UNIQUE NOT NULL, dokument TEXT NOT NULL,
                    revision INTEGER NOT NULL, uppdaterad REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS atkomst(hash TEXT PRIMARY KEY, arende TEXT NOT NULL REFERENCES arenden ON DELETE CASCADE,
                    person TEXT NOT NULL, utgang REAL NOT NULL, aterkallad INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS operationer(arende TEXT REFERENCES arenden ON DELETE CASCADE, id TEXT,
                    begaran TEXT NOT NULL, svar TEXT NOT NULL, PRIMARY KEY(arende,id));
                CREATE TABLE IF NOT EXISTS revisioner(arende TEXT REFERENCES arenden ON DELETE CASCADE, revision INTEGER,
                    dokument TEXT NOT NULL, PRIMARY KEY(arende,revision));
                CREATE TABLE IF NOT EXISTS jobb(id TEXT PRIMARY KEY, arende TEXT REFERENCES arenden ON DELETE CASCADE,
                    revision INTEGER NOT NULL, status TEXT NOT NULL, lease_id TEXT, lease_slut REAL, forsok INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS modellanrop(id TEXT PRIMARY KEY, arende TEXT REFERENCES arenden ON DELETE CASCADE, post TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS bilagor(id TEXT PRIMARY KEY, arende TEXT REFERENCES arenden ON DELETE CASCADE,
                    namn TEXT NOT NULL, typ TEXT NOT NULL, data BLOB NOT NULL);
                CREATE TABLE IF NOT EXISTS overlamningar(arende TEXT REFERENCES arenden ON DELETE CASCADE, id TEXT,
                    revision INTEGER NOT NULL, indata TEXT NOT NULL, post TEXT NOT NULL, PRIMARY KEY(arende,id));
                CREATE TABLE IF NOT EXISTS starter(id TEXT PRIMARY KEY, begaran TEXT NOT NULL, arende TEXT NOT NULL);
            ''')
            if 'roll' not in {r[1] for r in c.execute('PRAGMA table_info(atkomst)')}:
                # Äldre lokala prototyper hade en enda beslutsförare per ärende.
                c.execute("ALTER TABLE atkomst ADD COLUMN roll TEXT NOT NULL DEFAULT 'beslutsfattare'")

    @contextlib.contextmanager
    def trans(self):
        from kundstart_lagring import las
        with las(self), self._trans() as c:
            yield c

    @contextlib.contextmanager
    def _trans(self):
        for suffix in ('', '-wal', '-shm', '-journal'):
            p = Path(str(self.fil) + suffix)
            if p.is_symlink() or (p.exists() and not stat.S_ISREG(p.stat().st_mode)):
                raise Vagrad('Databasens mål är inte en vanlig fil.')
        c = sqlite3.connect(self.fil, timeout=10, isolation_level=None)
        os.chmod(self.fil, 0o600)
        c.row_factory = sqlite3.Row
        try:
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('PRAGMA secure_delete=ON')
            c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def _doc(self, c, eid):
        from kundstart_lagring import sparrad
        if sparrad(self,eid):raise Obehorig('Ärendet är inte tillgängligt.')
        row = c.execute('SELECT dokument FROM arenden WHERE id=?', (eid,)).fetchone()
        if not row:
            raise Obehorig('Ärendet är inte tillgängligt.')
        d = json.loads(row[0])  # trasig lagring blir aldrig ett nytt tomt ärende
        if not isinstance(d, dict) or d.get('id') != eid or type(d.get('revision')) is not int:
            raise RuntimeError('Ärendelagringen kunde inte valideras.')
        return d

    def _behorig(self, c, eid, token):
        from kundstart_lagring import sparrad
        if sparrad(self,eid):raise Obehorig('Ärendet är inte tillgängligt.')
        if not isinstance(token, str) or not 32 <= len(token) <= 200:
            raise Obehorig('Ärendet är inte tillgängligt.')
        row = c.execute('SELECT * FROM atkomst WHERE hash=? AND arende=?', (sha(token), eid)).fetchone()
        if not row or row['aterkallad'] or row['utgang'] <= time.time():
            raise Obehorig('Ärendet är inte tillgängligt.')
        return row['person']

    def _spara(self, c, d):
        d['revision'] += 1
        d['uppdaterad'] = time.time()
        c.execute("UPDATE jobb SET status='ersatt' WHERE arende=? AND revision<? AND status IN ('ko','pagar')", (d['id'],d['revision']))
        if d['modell']['status'] in ('ko','pagar'):
            aktiv=c.execute('SELECT status FROM jobb WHERE id=?',(d['modell'].get('jobb'),)).fetchone()
            if not aktiv or aktiv[0] not in ('ko','pagar'):
                d['modell']={'status':'foraldrat','text':'Uppdraget är ändrat. Fortsätt AI-samtalet från den nya versionen.'}
        c.execute('UPDATE arenden SET dokument=?, revision=?, uppdaterad=? WHERE id=?',
                  (jsontext(d), d['revision'], d['uppdaterad'], d['id']))
        c.execute('INSERT INTO revisioner VALUES(?,?,?)', (d['id'], d['revision'], jsontext(d)))

    def _ko(self, c, d):
        c.execute("UPDATE jobb SET status='ersatt' WHERE arende=? AND status IN ('ko','pagar')", (d['id'],))
        jid = id_()
        c.execute('INSERT INTO jobb(id,arende,revision,status) VALUES(?,?,?,?)', (jid, d['id'], d['revision'] + 1, 'ko'))
        d['modell'] = {'status':'ko', 'jobb':jid, 'text':'Svaret är sparat. AI-bearbetning är köad.'}

    def skapa(self, slug, person, dagar=7, modellbudget=0, fiktiv=True, operation=None):
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or type(dagar) is not int or not 1 <= dagar <= 90:
            raise Vagrad('Ogiltig slug eller giltighet.')
        if type(modellbudget) is not int or not 0 <= modellbudget <= 100:
            raise Vagrad('Ange en modellbudget mellan 0 och 100 anrop.')
        if type(fiktiv) is not bool:raise Vagrad('Ärendet behöver uttrycklig status för verklig eller fiktiv verksamhet.')
        namn = text(person, 120); person=id_()
        finger=sha([slug,namn,dagar,modellbudget,fiktiv])
        if operation is not None:nyckel(operation)
        eid, token = id_(), secrets.token_urlsafe(32)
        d = {'id':eid, 'slug':slug, 'revision':1, 'skapad':time.time(), 'uppdaterad':time.time(), 'meddelanden':[],
             'uppgifter':{}, 'forslag':{}, 'fragor':[], 'material':[], 'historik':[], 'erbjudanden':[],
             'bestallning':{'status':'utkast'}, 'modell':{'status':'inte_startad'},
             'budget':{'max_anrop':modellbudget, 'anrop':0}, 'overlamning':None,
             'fiktiv':fiktiv,'verksamhet':None,'verksamhet_forslag':None,'returfragor':{},'integrationer':{},
             'deltagare':{person:{'namn':namn,'roll':'beslutsfattare','aktiv':True}}}
        with self.trans() as c:
            if operation:
                row=c.execute('SELECT begaran,arende FROM starter WHERE id=?',(operation,)).fetchone()
                if row:
                    if row[0]!=finger:raise Konflikt('Startens id har använts för ett annat ärendeunderlag.')
                    return row[1],None  # rå kundnyckel lagras aldrig för återvisning
            if c.execute('SELECT 1 FROM arenden WHERE slug=?',(slug,)).fetchone():
                raise Konflikt('Ett ärende med denna slug finns redan. Öppna det befintliga ärendet eller välj en ny slug.')
            c.execute('INSERT INTO arenden VALUES(?,?,?,?,?)', (eid,slug,jsontext(d),1,d['uppdaterad']))
            c.execute('INSERT INTO revisioner VALUES(?,?,?)', (eid,1,jsontext(d)))
            c.execute('INSERT INTO atkomst(hash,arende,person,utgang) VALUES(?,?,?,?)',
                      (sha(token),eid,person,time.time()+dagar*86400))
            if operation:c.execute('INSERT INTO starter VALUES(?,?,?)',(operation,finger,eid))
        return eid, token  # rå token lämnas en gång, lagras aldrig

    def las(self, eid, token):
        with self.trans() as c:
            self._behorig(c,eid,token)
            import kundstart_behorighet as kh
            return self._vy(c,self._doc(c,eid))|{'din_roll':kh.roll(c,eid,token)}

    def internt(self, eid):
        """Ägar-/arbetaringång; exponeras aldrig i kundservern."""
        with self.trans() as c:
            return self._vy(c,self._doc(c,eid))

    def _vy(self,c,d):
        from kundstart_beredning import kvittovy
        d=vy(d)
        p=c.execute('SELECT post FROM overlamningar WHERE arende=? ORDER BY rowid DESC LIMIT 1',(d['id'],)).fetchone()
        if p:d['overlamning']=kvittovy(json.loads(p[0]),d)
        return d

    def aterkalla(self, eid):
        with self.trans() as c:
            c.execute('UPDATE atkomst SET aterkallad=1 WHERE arende=?', (eid,))

    def kundhandling(self, eid, token, revision, op, handling, data):
        nyckel(op)
        if type(revision) is not int or revision < 1:
            raise Vagrad('En aktuell revision behövs.')
        if not isinstance(data, dict):
            raise Vagrad('Ogiltig handling.')
        with self.trans() as c:
            person = self._behorig(c,eid,token)
            import kundstart_behorighet as kh
            roll=kh.tillat(c,eid,token,handling)
            fingerprint = sha([sha(token),revision,handling,data])
            fore = c.execute('SELECT begaran,svar FROM operationer WHERE arende=? AND id=?',(eid,op)).fetchone()
            if fore:
                if fore[0] != fingerprint:
                    raise Konflikt('Begärans id har redan använts för ett annat innehåll.')
                return json.loads(fore[1])
            d = self._doc(c,eid)
            if d['revision'] != revision:
                raise Konflikt('Uppdraget har ändrats. Hämta den senaste versionen; ditt utkast är kvar.')
            self._handling(c,d,person,handling,data)
            self._spara(c,d)
            svar = vy(d)|{'din_roll':roll}
            c.execute('INSERT INTO operationer VALUES(?,?,?,?)',(eid,op,fingerprint,jsontext(svar)))
            return svar

    def _handling(self, c, d, person, handling, data):
        if handling == 'meddelande':
            falt(data, ('text',), ('text',))
            if len(d['meddelanden']) >= 500:
                raise Vagrad('Ärendet behöver intern genomgång innan fler svar tas emot.')
            d['meddelanden'].append({'id':id_(),'roll':'kund','person':person,'text':text(data['text']),'tid':time.time()})
            self._ko(c,d)
        elif handling == 'besvara_fraga':
            import kundstart_fortsatt
            kundstart_fortsatt.svara(self,c,d,person,data)
        elif handling == 'integrationsbehov':
            import kundstart_fortsatt
            kundstart_fortsatt.behov(d,person,data)
            self._ko(c,d)
        elif handling == 'uppgift':
            falt(data, ('id','amne','text','lage'), ('id','amne','text'))
            kid=nyckel(data['id'])
            if data['amne'] not in AMNEN or data.get('lage','onskemal') not in ('onskemal','avstatt','framtida','okant','inte_relevant','kundval'):
                raise Vagrad('Okänt ämne eller önskemålsläge.')
            v = text(data['text'])
            fore=d['uppgifter'].get(kid)
            if fore and fore['text'] == v and fore['bestallning'] == data.get('lage','onskemal') and fore['amne'] == data['amne']:
                return  # en identisk rättelse ändrar inte omfattningens identitet
            if fore:
                d['historik'].append({'slag':'ersatt_uppgift','uppgift':fore,'tid':time.time()})
            d['uppgifter'][kid]={'id':kid,'amne':data['amne'],'text':v,'kunskap':'kunden_uppger',
                                'bestallning':data.get('lage','onskemal'),'person':person,'kalla':id_(),
                                'tid':time.time(),'motsagelse':bool(fore and (fore.get('motsagelse') or fore['person'] != person))}
            self._ko(c,d)
        elif handling == 'klarlagg_uppgift':
            import kundstart_behorighet
            kundstart_behorighet.klarlagg(d,person,data)
            self._ko(c,d)
        elif handling == 'bekrafta':
            falt(data, ('ids',), ('ids',))
            if not isinstance(data['ids'],list) or not data['ids'] or len(data['ids']) > 100:
                raise Vagrad('Välj uppgifterna som ska bekräftas.')
            for kid in data['ids']:
                nyckel(kid)
                u=d['uppgifter'].get(kid)
                if not u or u.get('motsagelse'):
                    raise Vagrad('Uppgiften saknas eller behöver klarläggas mellan deltagarna.')
                u['kunskap']='kunden_bekraftar'
                u['bekraftad_av']=person
        elif handling == 'forfragan':
            falt(data, ())
            if not d['uppgifter'] or any(u.get('motsagelse') for u in d['uppgifter'].values()):
                raise Vagrad('Uppdraget behöver uppgifter och eventuella motsägelser måste klarläggas.')
            d['bestallning']={'status':'forfragan','omfattning':omfattning(d),'person':person,'tid':time.time()}
        elif handling == 'bekrafta_verksamhet':
            import kundstart_beredning as kb
            falt(data,('sha256',),('sha256',))
            p=d.get('verksamhet_forslag')
            if not p or p.get('sha256')!=data['sha256'] or p['kundgrund']!=kb.grund(d):
                raise Vagrad('Grunduppgifterna behöver sammanställas ur de aktuella svaren före avstämningen.')
            d['verksamhet']={**p,'kunskap':'kunden_bekraftar','person':person,'tid':time.time()}
        elif handling == 'acceptera':
            falt(data, ('erbjudande',), ('erbjudande',))
            e=next((e for e in d['erbjudanden'] if e['id']==data['erbjudande']),None)
            if not e or e['omfattning'] != omfattning(d) or e != d['erbjudanden'][-1]:
                raise Vagrad('Det finns inget aktuellt definierat erbjudande att acceptera.')
            d['bestallning']={'status':'accepterad','omfattning':omfattning(d),'erbjudande':e['id'],'person':person,'tid':time.time()}
        elif handling == 'forsok_igen':
            falt(data, ())
            if d['modell']['status'] not in ('fel','avstangd','budget_slut','foraldrat'):
                raise Vagrad('Det finns inget misslyckat AI-försök att återuppta.')
            self._ko(c,d)
        elif handling == 'bilaga':
            falt(data, ('namn','typ','data'), ('namn','typ','data'))
            namn=text(data['namn'],120)
            if '/' in namn or '\\' in namn or namn in ('.','..') or any(ord(x)<32 for x in namn):
                raise Vagrad('Ogiltigt filnamn.')
            if not isinstance(data['data'],str) or len(data['data']) > MAX_BILAGA*4//3+8 or len(d['material']) >= 20:
                raise Vagrad('För mycket material. Högst 20 filer om 4 MB per ärende.')
            try: raw=base64.b64decode(data['data'],validate=True)
            except ValueError as e: raise Vagrad('Filens överföring är ogiltig.') from e
            typ=data['typ']
            if not isinstance(typ,str):
                raise Vagrad('Filtypen måste vara text.')
            if not raw or len(raw)>MAX_BILAGA:
                raise Vagrad('Filen är tom eller för stor.')
            signatur={'image/png':b'\x89PNG\r\n\x1a\n','image/jpeg':b'\xff\xd8\xff','application/pdf':b'%PDF-'}
            if typ=='text/plain':
                try: text(raw.decode('utf-8'), MAX_BILAGA)
                except UnicodeError as e: raise Vagrad('Textfilen är inte UTF-8.') from e
            elif typ not in signatur or not raw.startswith(signatur[typ]):
                raise Vagrad('Filtypen stöds inte eller stämmer inte med innehållet.')
            bid=id_()
            c.execute('INSERT INTO bilagor VALUES(?,?,?,?,?)',(bid,d['id'],namn,typ,raw))
            d['material'].append({'id':bid,'namn':namn,'typ':typ,'byte':len(raw),'sha256':sha(raw),
                                  'lasning':'inte_last','rattighet':'okand','person':person})
        elif handling == 'materialratt':
            falt(data, ('id','lage','grund'), ('id','lage','grund'))
            m=next((m for m in d['material'] if m['id']==data['id']),None)
            if not m or data['lage'] not in ('okand','kunden_uppger_ratt','saknar_ratt'):
                raise Vagrad('Material eller rättighetsläge saknas.')
            m.update(rattighet=data['lage'],rattighetsgrund=text(data['grund'],2000))
        else:
            raise Vagrad('Handlingen är inte tillåten i kundytan.')

    def erbjudande(self, eid, revision, omfattningstext, villkor, ansvarig):
        """Explicit intern operation med faktiskt erbjudande, aldrig modellens verktyg."""
        with self.trans() as c:
            d=self._doc(c,eid)
            if d['revision'] != revision:
                raise Konflikt('Ärendet har ändrats.')
            if d['bestallning']['status'] != 'forfragan' or d['bestallning']['omfattning'] != omfattning(d):
                raise Vagrad('Ett aktuellt inlämnat uppdrag behövs först.')
            e={'id':id_(),'omfattning':omfattning(d),'text':text(omfattningstext), 'villkor':text(villkor),
               'ansvarig':text(ansvarig,120),'tid':time.time()}
            d['erbjudanden'].append(e); self._spara(c,d)
            return e

    def bilaga(self,eid,token,bid):
        with self.trans() as c:
            self._behorig(c,eid,token)
            row=c.execute('SELECT namn,typ,data FROM bilagor WHERE arende=? AND id=?',(eid,bid)).fetchone()
            if not row: raise Obehorig('Materialet är inte tillgängligt.')
            return tuple(row)

    def ta_jobb(self, arbetare, lease=120, modell=None, bara_fiktiva=False):
        """bara_fiktiva: pilotens abonnemangstransport (ägarens beslut 2026-10-08) tar bara ärenden märkta fiktiva; ett
        verkligt ärendes jobb stängs av utan lease och utan förbrukad budget."""
        nyckel(arbetare)
        if type(lease) is not int or not 1<=lease<=300: raise Vagrad('Ogiltig lease.')
        with self.trans() as c:
            import kundstart_matt as matt
            matt.avbrutna(c)
            c.execute("UPDATE jobb SET status='ko' WHERE status='pagar' AND lease_slut<?",(time.time(),))
            rows=c.execute("SELECT * FROM jobb WHERE status='ko' ORDER BY rowid").fetchall()
            from kundstart_lagring import journal
            sparrade=journal(self)['arenden']
            for row in rows:
                if row['arende'] in sparrade:
                    c.execute("UPDATE jobb SET status='gallring' WHERE id=?",(row['id'],));continue
                d=self._doc(c,row['arende'])
                if row['revision'] != d['revision']:
                    c.execute("UPDATE jobb SET status='ersatt' WHERE id=?",(row['id'],)); continue
                if bara_fiktiva and d.get('fiktiv') is not True:
                    c.execute("UPDATE jobb SET status='avstangd' WHERE id=?",(row['id'],))
                    d['modell']={'status':'avstangd','text':'Dina svar är sparade. Pilotens AI-koppling gäller bara fiktiva ärenden; ett verkligt ärende kräver server-API.'}
                    self._spara(c,d)
                    return {'nekad':'verkligt ärende','id':row['id'],'arende':row['arende']}  # ingen lease, ingen budget
                if d['budget']['anrop']>=d['budget']['max_anrop'] or row['forsok']>=3:
                    c.execute("UPDATE jobb SET status='budget_slut' WHERE id=?",(row['id'],))
                    d['modell']={'status':'budget_slut','text':'Svaren är sparade. AI-budgeten behöver intern bedömning.'}
                    self._spara(c,d); continue
                lease_id=id_(); d['budget']['anrop']+=1
                d['modell']={'status':'pagar','jobb':row['id'],'text':'Dina svar är sparade. AI-bearbetningen pågår.'}
                # Jobbets interna lease ändrar inte kundens revisionsgrund.
                c.execute('UPDATE arenden SET dokument=? WHERE id=?',(jsontext(d),d['id']))
                c.execute("UPDATE jobb SET status='pagar',lease_id=?,lease_slut=?,forsok=forsok+1 WHERE id=?",
                          (lease_id,time.time()+lease,row['id']))
                jobb={'id':row['id'],'arende':row['arende'],'revision':row['revision'],'lease_id':lease_id,'arbetare':arbetare,
                      'dokument':vy(d)}
                jobb['matning']=matt.start(self,jobb,modell,c)
                return jobb
        return None

    def avstangd_modell(self):
        """Ingen transport startades: ge ett besked utan lease eller förbrukad anropsbudget."""
        with self.trans() as c:
            from kundstart_lagring import journal
            sparrade=journal(self)['arenden']
            rows=c.execute("SELECT * FROM jobb WHERE status='ko' ORDER BY rowid").fetchall()
            for r in rows:
                if r['arende'] in sparrade:c.execute("UPDATE jobb SET status='gallring' WHERE id=?",(r['id'],))
            row=next((r for r in rows if r['arende'] not in sparrade),None)
            if not row:return None
            d=self._doc(c,row['arende'])
            c.execute("UPDATE jobb SET status='avstangd' WHERE id=?",(row['id'],))
            if row['revision']==d['revision']:
                d['modell']={'status':'avstangd','text':'Dina svar är sparade. AI-kopplingen är inte aktiverad eller saknar konfiguration.'}
                self._spara(c,d)
            return row['id']

    def _jobb(self,c,jobb):
        row=c.execute('SELECT * FROM jobb WHERE id=?',(jobb['id'],)).fetchone()
        if (not row or row['arende'] != jobb['arende'] or type(jobb.get('revision')) is not int or row['revision'] != jobb['revision']
                or row['status'] != 'pagar' or row['lease_id'] != jobb['lease_id']
                or row['lease_slut']<=time.time()):
            return None
        d=self._doc(c,row['arende'])
        if row['revision']!=d['revision']:
            c.execute("UPDATE jobb SET status='ersatt' WHERE id=?",(row['id'],)); return None
        return d

    def modellfel(self,jobb,slag):
        if slag not in ('timeout','avstangd','kvot','ogiltigt_svar','transport','kontextgrans','metod_saknas'): slag='transport'
        with self.trans() as c:
            d=self._jobb(c,jobb)
            if d is None: return False
            c.execute("UPDATE jobb SET status='fel' WHERE id=?",(jobb['id'],))
            d['modell']={'status':'avstangd' if slag=='avstangd' else 'fel','slag':slag,
                         'text':'Dina svar är sparade. AI-bearbetningen kunde inte slutföras.'}
            self._spara(c,d)
            return True

    def modellsvar(self,jobb,svar):
        falt(svar, ('text','forslag','fragor','verksamhet','integrationsforslag'), ('text','forslag','fragor'))
        svartext=text(svar['text'])
        if not isinstance(svar['forslag'],list) or len(svar['forslag'])>30 or not isinstance(svar['fragor'],list) or len(svar['fragor'])>20:
            raise Vagrad('Modellsvaret är för stort eller ogiltigt.')
        with self.trans() as c:
            d=self._jobb(c,jobb)
            if d is None: return False
            if svar.get('verksamhet') is not None:
                import kundstart_beredning as kb
                d['verksamhet_forslag']=kb.forslag(d,svar['verksamhet'])
            kallor=kundkallor(d)
            for p in svar['forslag']:
                falt(p,('id','amne','text','kunskap','kallor'),('id','amne','text','kunskap','kallor'))
                nyckel(p['id']); text(p['text'])
                if (p['amne'] not in AMNEN or p['kunskap'] not in ('tolkning','hypotes','preferens','okant')
                        or not isinstance(p['kallor'],list) or not p['kallor'] or any(not isinstance(k,str) or k not in kallor for k in p['kallor'])):
                    raise Vagrad('Modellförslaget saknar giltig källkoppling eller status.')
                d['forslag'][p['id']]={**p,'bestallning':'forslag','revision':jobb['revision']}
            fragor=[]
            for q in svar['fragor']:
                falt(q,('id','amne','text','varfor','paverkar','kritisk'),('id','amne','text','varfor','paverkar','kritisk'))
                nyckel(q['id'])
                if q['amne'] not in AMNEN or type(q['kritisk']) is not bool: raise Vagrad('Ogiltig frågestatus.')
                for n in ('text','varfor','paverkar'): text(q[n],3000)
                fragor.append(q)
            d['fragor']=fragor
            if svar.get('integrationsforslag') is not None:
                import kundstart_integration
                d['integrationsforslag']=kundstart_integration.modellforslag(svar['integrationsforslag'],kallor,jobb['revision'])
            d['meddelanden'].append({'id':id_(),'roll':'assistent','text':svartext,'tid':time.time(),'bas_revision':jobb['revision']})
            d['modell']={'status':'klar','text':'AI-förslag finns. Du kan rätta och välja i Ditt uppdrag.'}
            c.execute("UPDATE jobb SET status='klar' WHERE id=?",(jobb['id'],))
            self._spara(c,d)
            return True
