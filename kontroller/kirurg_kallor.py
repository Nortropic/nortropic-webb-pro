#!/usr/bin/env python3
"""Versionsmedveten textbevakning för den befintliga spanaren.

Ingen semantisk AI-bedömning: synlig dokumenttext jämförs. Bara fristående,
uttryckligt märkta uppdateringsdatum undantas; datum i rekommendationer består.
Källidentitet, dokument och innehållsversion hålls isär. Inget ur källan körs.
"""
import hashlib
import difflib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import kallnyckel


class Kallfel(ValueError):
    pass


def identitet(url):
    s=urlsplit(url.strip())
    if s.scheme not in ('http','https') or not s.hostname or s.username or s.password:
        raise Kallfel('Källan saknar en vanlig http-/https-adress.')
    # Den äldre repo-normaliseringen används fortsatt vid intag av hela repos.
    # Här är en konkret dokumentväg meningsbärande och får inte försvinna.
    q=sorted((k,v) for k,v in parse_qsl(s.query,keep_blank_values=True) if not kallnyckel.SPARNING.fullmatch(k))
    return urlunsplit((s.scheme.lower(),s.netloc.lower(),s.path or '/',urlencode(q),''))


class Text(HTMLParser):
    block={'p','li','div','section','article','main','h1','h2','h3','h4','h5','h6','tr','br','pre'}
    dolda={'script','style','nav','footer','head'}
    def __init__(self):
        super().__init__(convert_charrefs=True);self.rader=[];self.delar=[];self.ignorera=[]
    def rad(self):
        if self.delar:self.rader.append(' '.join(self.delar));self.delar=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.dolda:self.ignorera.append(tag)
        if not self.ignorera and tag in self.block:self.rad()
    def handle_endtag(self,tag):
        if self.ignorera:
            if tag==self.ignorera[-1]:self.ignorera.pop()
        elif tag in self.block:self.rad()
    def handle_data(self,data):
        if not self.ignorera:self.delar.append(data)


DATUM=re.compile(r'^(?:last updated|updated|senast uppdaterad|uppdaterad|publicerad)\s*:?\s*\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)?\.?$',re.I)


def rader(html,rensa):
    p=Text();p.feed(html);p.close();p.rad()
    ut=[]
    for raw in p.rader:
        text,_=rensa(raw,200001,html_kalla=False)
        if len(text)>200000:raise Kallfel('Dokumentets textdel är större än bevakningens gräns.')
        if not text or DATUM.fullmatch(text):continue
        ut.extend(x.strip() for x in re.split(r'(?<=[.!?])\s+',text) if x.strip())
    if len(ut)>5000 or sum(map(len,ut))>200000:raise Kallfel('Dokumentet ryms inte i fullständig textbevakning.')
    if not ut:raise Kallfel('Källan saknar läsbar dokumenttext; ingen tom ersättning sparas.')
    return ut


def las_snapshot(fil):
    p=Path(fil)
    if p.is_symlink():raise Kallfel('Källans tidigare mätning är en länk.')
    try:
        with p.open() as f:text=f.read(2_000_001)
    except FileNotFoundError:return None
    except OSError:raise Kallfel('Källans tidigare mätning kunde inte läsas.') from None
    try:
        if len(text)>2_000_000:raise ValueError()
        d=json.loads(text)
        if not isinstance(d,dict) or not isinstance(d.get('rader'),list) or any(not isinstance(x,str) for x in d['rader']):raise ValueError()
        return d
    except (ValueError,TypeError):raise Kallfel('Källans tidigare mätning är ogiltig; ny baslinje antas inte.') from None


def jamfor(nya,gammal):
    gamla=gammal['rader'] if gammal else []
    till,bort=[],[]
    for tag,a,b,c,d in difflib.SequenceMatcher(a=gamla,b=nya,autojunk=False).get_opcodes():
        if tag!='equal':bort.extend(gamla[a:b]);till.extend(nya[c:d])
    return {'tillagda':till,'borttagna':bort,
            'tolkning':'Textskillnad, inte verifierad ändring av produktförmåga eller metodens kvalitet.'}


def hashtext(rader):
    return hashlib.sha256('\n'.join(rader).encode()).hexdigest()
