"""Avgränsade material-API:er. Inga konton, SDK:er eller modeller aktiveras av import.

Anroparen måste först pröva kundgräns, exakt uppdrag och kostnadsmandat. Transporten
tar en nyckel i minnet, aldrig i URL:en. Ingen automatisk upprepning av POST.
Officiella kontrakt och avgränsningar: kunskap/materialtransport.md.
"""
import base64
import binascii
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request


class TransportFel(ValueError):
    """Bara fasta felkoder: leverantörssvar och adresser får inte läcka till loggen."""
    def __init__(self, text, *, terminal=False):
        super().__init__(text)
        self.terminal = terminal


GEMINI = 'https://generativelanguage.googleapis.com/v1beta/interactions'
HIGGSFIELD = 'https://api.higgsfield.ai'
SEEDANCE = 'https://operator.las.ap-southeast-1.bytepluses.com/api/v1/contents/generations/tasks'
STANDARD = {('nano-banana', 'bild'): 'gemini-nano-banana-2.1',
            ('higgsfield', 'bild'): 'higgsfield-ai/soul/standard',
            ('higgsfield', 'video'): 'bytedance/seedance-2.0/text-to-video',
            ('seedance', 'video'): 'dreamina-seedance-2-0-260128'}
FORMAT = ('1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3')
MAX_JSON = 48 * 1024 * 1024
MAX_FIL = 128 * 1024 * 1024


def uppdrag(leverantor, typ, prompt, modell=None, parametrar=None):
    """Tillåt bara dokumenterade parametrar för de fyra uttryckliga integrationerna."""
    modell = modell or STANDARD.get((leverantor, typ))
    if (leverantor, typ) not in STANDARD or modell != STANDARD[(leverantor, typ)]:
        raise TransportFel('modellen är inte införd för denna leverantör och materialtyp')
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 2000 or '\x00' in prompt:
        raise TransportFel('materialprompten måste vara 1–2000 tecken')
    p = dict(parametrar or {}) if isinstance(parametrar, (dict, type(None))) else None
    if p is None:
        raise TransportFel('parametrar ska vara ett objekt')
    if typ == 'bild':
        defaults = {'aspect_ratio': '16:9', 'image_size': '1K'} if leverantor == 'nano-banana' else {'aspect_ratio': '16:9', 'resolution': '1080p'}
        enums = {'aspect_ratio': FORMAT, 'image_size': ('1K', '2K', '4K')} if leverantor == 'nano-banana' else {'aspect_ratio': FORMAT, 'resolution': ('720p', '1080p')}
    else:
        ratio = 'ratio' if leverantor == 'seedance' else 'aspect_ratio'
        defaults = {ratio: '16:9', 'resolution': '720p', 'duration': 5, 'generate_audio': False}
        enums = {ratio: ('16:9', '4:3', '1:1', '3:4', '9:16', '21:9'), 'resolution': ('480p', '720p', '1080p', '4k')}
    if set(p) - set(defaults):
        raise TransportFel('okänd materialparameter; URL:er, filer och callbacks stöds inte')
    defaults.update(p)
    for key, values in enums.items():
        if defaults[key] not in values or not isinstance(defaults[key], str):
            raise TransportFel('ogiltigt format eller upplösning')
    if typ == 'video' and (type(defaults['duration']) is not int or not 4 <= defaults['duration'] <= 15 or type(defaults['generate_audio']) is not bool):
        raise TransportFel('video kräver 4–15 hela sekunder och ett booleskt ljudval')
    return {'leverantor': leverantor, 'typ': typ, 'modell': modell, 'prompt': prompt, 'parametrar': defaults}


def sha(uppdrag_):
    return hashlib.sha256(json.dumps(uppdrag_, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def url_ok(url):
    try:
        u = urllib.parse.urlsplit(url)
        return (isinstance(url, str) and len(url) <= 8192 and not re.search(r'[\x00-\x20\x7f]', url)
                and u.scheme == 'https' and bool(u.hostname) and not u.username and not u.password
                and u.port in (None, 443) and not u.fragment)
    except (TypeError, ValueError):
        return False


class HTTP:
    """DNS/adress kontrolleras i själva anslutningen. Inga omdirigeringar, inte ens med API-nyckel."""
    def __init__(self):
        import hamta_sajt
        self.opener = hamta_sajt.oppnare(folj=False)

    def las(self, url, *, headers=None, body=None, timeout=30, max_bytes=MAX_JSON):
        if not url_ok(url):
            raise TransportFel('ogiltig transportadress')
        req = urllib.request.Request(url, data=body, headers=headers or {}, method='POST' if body is not None else 'GET')
        try:
            with self.opener.open(req, timeout=timeout) as response:
                if response.status != 200 and not (body is not None and response.status in (201, 202)):
                    raise TransportFel('oväntad HTTP-status')
                length = response.headers.get('Content-Length')
                if length is not None and (not length.isdigit() or int(length) > max_bytes):
                    raise TransportFel('för stort eller ogiltigt transportsvar')
                slut = time.monotonic() + timeout
                blocks, size = [], 0
                while True:
                    if time.monotonic() >= slut:
                        raise TransportFel('transportens lästid tog slut')
                    block = response.read1(min(65536, max_bytes + 1 - size))
                    if not block:
                        break
                    blocks.append(block); size += len(block)
                    if size > max_bytes:
                        raise TransportFel('för stort transportsvar')
                data = b''.join(blocks)
                if len(data) > max_bytes:
                    raise TransportFel('för stort transportsvar')
                return data, response.headers.get_content_type()
        except urllib.error.HTTPError as e:
            e.close()
            raise TransportFel('leverantörens HTTP-status %d' % e.code) from None
        except TransportFel:
            raise
        except Exception:
            raise TransportFel('transporten avbröts; utfallet kan vara okänt') from None

    def json(self, url, headers, body=None, timeout=30):
        data, mime = self.las(url, headers=dict(headers, **{'Content-Type': 'application/json'}),
                              body=json.dumps(body).encode() if body is not None else None, timeout=timeout)
        try:
            d = json.loads(data)
            if mime != 'application/json' or not isinstance(d, dict):
                raise ValueError()
            return d
        except (UnicodeError, ValueError):
            raise TransportFel('ogiltigt JSON-svar från leverantören') from None


def fil(data, mime, typ):
    """Inga HTML-felsidor eller godtyckliga filer in i materialregistret."""
    if not isinstance(data, bytes) or not 12 <= len(data) <= MAX_FIL:
        raise TransportFel('tom eller för stor materialfil')
    if typ == 'bild':
        if data.startswith(b'\x89PNG\r\n\x1a\n') and mime == 'image/png':
            ext = '.png'
        elif data.startswith(b'\xff\xd8\xff') and mime == 'image/jpeg':
            ext = '.jpg'
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP' and mime == 'image/webp':
            ext = '.webp'
        else:
            raise TransportFel('materialsvaret är inte en stödd bild')
    elif typ == 'video' and data[4:8] == b'ftyp' and mime == 'video/mp4':
        ext = '.mp4'
    elif typ == 'video' and data[:4] == b'\x1aE\xdf\xa3' and mime == 'video/webm':
        ext = '.webm'
    else:
        raise TransportFel('materialsvaret är inte en stödd video')
    return {'data': data, 'ext': ext, 'mime': mime, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def jobbid(varde):
    if not isinstance(varde, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,128}', varde):
        raise TransportFel('leverantören gav inget giltigt jobb-id')
    return varde


def kor(job, nyckel, *, befintligt=None, registrera=None, http=None, timeout=180, clock=time.monotonic, sleep=time.sleep):
    """Ett POST, sedan GET. registrera(id) måste beständigt spara id:t före första pollningen.

    Återupptagning av ett accepterat asynkront jobb gör bara GET. Ett timeoutfel avbryter
    vår väntan, aldrig leverantörens jobb. Ingen automatisk ny generering vid fel.
    """
    rent = uppdrag(job['leverantor'], job['typ'], job['prompt'], job['modell'], job['parametrar'])
    if any(job.get(k) != v for k, v in rent.items()) or not isinstance(nyckel, str) or not nyckel or re.search(r'[\r\n]', nyckel):
        raise TransportFel('ogiltigt uppdrag eller konto')
    if type(timeout) not in (float, int) or not 1 <= timeout <= 600:
        raise TransportFel('ogiltig transporttidsgräns')
    http = http or HTTP()
    slut = clock() + timeout

    def kvar():
        t = slut - clock()
        if t <= 0:
            raise TransportFel('väntetiden tog slut; inget nytt jobb skickades')
        return min(t, 30)

    lev, p = rent['leverantor'], rent['parametrar']
    if lev == 'nano-banana':
        if befintligt:
            raise TransportFel('det synkrona bildanropet kan inte återupptas')
        d = http.json(GEMINI, {'x-goog-api-key': nyckel}, {'model': rent['modell'], 'input': [{'type': 'text', 'text': rent['prompt']}],
                      'store': False, 'stream': False, 'response_format': dict(p, type='image', delivery='inline')}, timeout=kvar())
        if d.get('status') != 'completed' or not isinstance(d.get('steps'), list):
            raise TransportFel('bildanropet blev inte fullständigt')
        images = [c for s in d['steps'] if isinstance(s, dict) and s.get('type') == 'model_output'
                  for c in (s.get('content') if isinstance(s.get('content'), list) else []) if isinstance(c, dict) and c.get('type') == 'image']
        if len(images) != 1 or not isinstance(images[0].get('data'), str):
            raise TransportFel('bildanropet gav inte exakt en infogad bild')
        try:
            data = base64.b64decode(images[0]['data'], validate=True)
        except (binascii.Error, ValueError):
            raise TransportFel('ogiltig bildkodning') from None
        return fil(data, images[0].get('mime_type'), rent['typ'])
    headers = {'Authorization': ('Key ' if lev == 'higgsfield' else 'Bearer ') + nyckel}
    if befintligt:
        rid = jobbid(befintligt)
    else:
        if registrera is None:
            raise TransportFel('beständig jobbregistrering saknas')
        if lev == 'higgsfield':
            url = HIGGSFIELD + '/' + rent['modell']
            body = dict(p, prompt=rent['prompt'])
            if rent['typ'] == 'bild':
                body['batch_size'] = 1
            submit_headers = dict(headers, **{'Idempotency-Key': sha(job)})
        else:
            url, submit_headers = SEEDANCE, headers
            body = dict(p, model=rent['modell'], content=[{'type': 'text', 'text': rent['prompt']}])
        d = http.json(url, submit_headers, body, timeout=kvar())
        rid = jobbid(d.get('request_id' if lev == 'higgsfield' else 'id'))
        registrera(rid)
    poll = HIGGSFIELD + '/requests/' + rid + '/status' if lev == 'higgsfield' else SEEDANCE + '/' + rid
    while True:
        d = http.json(poll, headers, timeout=kvar())
        if d.get('request_id' if lev == 'higgsfield' else 'id') != rid:
            raise TransportFel('statussvaret gäller ett annat jobb')
        status = d.get('status')
        if status == ('completed' if lev == 'higgsfield' else 'succeeded'):
            if lev == 'seedance':
                url = (d.get('content') or {}).get('video_url') if isinstance(d.get('content'), dict) else None
            elif rent['typ'] == 'bild':
                images = d.get('images')
                url = images[0].get('url') if isinstance(images, list) and len(images) == 1 and isinstance(images[0], dict) else None
            else:
                url = d['video'].get('url') if isinstance(d.get('video'), dict) else None
            if not url_ok(url):
                raise TransportFel('leverantören gav ingen giltig materialadress')
            # Ingen nyckel och inga leverantörshuvuden till bild-/videovärden.
            data, mime = http.las(url, timeout=kvar(), max_bytes=MAX_FIL)
            return dict(fil(data, mime, rent['typ']), jobb=rid)
        if status in ('failed', 'nsfw', 'canceled', 'cancelled', 'expired'):
            raise TransportFel('leverantören avslutade materialjobbet utan material', terminal=True)
        if status not in (('queued', 'in_progress') if lev == 'higgsfield' else ('queued', 'running')):
            raise TransportFel('materialjobbet avbröts eller gav okänd status')
        sleep(min(2, kvar()))
