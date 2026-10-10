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
# Källbild för redigering (Nano Banana: bilden som objekt i input) och bild till video (BytePlus LAS: första bildrutan som
# data-URL). Bara materialregistrets egna illustrativa versioner kan bli källbild; kundens bilder når aldrig vägen
# (material.bestall, --fran). Higgsfields bild till video kräver en publik uppladdningsadress och är inte infört.
KALLBILD = {('nano-banana', 'bild'): 15 * 1024 * 1024, ('seedance', 'video'): 30 * 1024 * 1024}
BILDMIME = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff', 'image/webp': b'RIFF'}
SYNKRON_BILD = 90  # s: Interactions-anropet är synkront; HTTP-anrop stängs normalt efter ungefär 60 s (Geminis dokumentation)
MAX_JSON = 48 * 1024 * 1024
MAX_FIL = 128 * 1024 * 1024


def kallbild(leverantor, typ, kalla):
    """Källbildens identitet i uppdraget (aldrig själva bilden): material-id, version, mime, storlek och sha256."""
    if kalla is None:
        return None
    if (leverantor, typ) not in KALLBILD:
        raise TransportFel('källbild stöds bara för Nano Bananas bildredigering och Seedance via BytePlus (första bildrutan); '
                           'Higgsfields bild till video kräver en publik uppladdning och är inte infört')
    if (not isinstance(kalla, dict) or set(kalla) != {'material', 'version', 'mime', 'bytes', 'sha256'}
            or kalla['mime'] not in BILDMIME or not isinstance(kalla['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', kalla['sha256'])
            or type(kalla['bytes']) is not int or not 12 <= kalla['bytes'] <= KALLBILD[(leverantor, typ)]
            or type(kalla['version']) is not int or not isinstance(kalla['material'], str) or not re.fullmatch(r'm\d{3,}', kalla['material'])):
        raise TransportFel('ogiltig eller för stor källbild')
    return dict(kalla)


def uppdrag(leverantor, typ, prompt, modell=None, parametrar=None, kalla=None):
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
    ut = {'leverantor': leverantor, 'typ': typ, 'modell': modell, 'prompt': prompt, 'parametrar': defaults}
    if kalla is not None:
        ut['kalla_bild'] = kallbild(leverantor, typ, kalla)
    return ut


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
    """Inga HTML-felsidor eller godtyckliga filer in i materialregistret. En lagringsvärd som svarar med en allmän binär
    typ (application/octet-stream) får sin typ ur filsignaturen; en annan uttrycklig typ som strider mot signaturen nekas."""
    if not isinstance(data, bytes) or not 12 <= len(data) <= MAX_FIL:
        raise TransportFel('tom eller för stor materialfil')
    if mime in ('application/octet-stream', 'binary/octet-stream'):
        mime = ('image/png' if data.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if data.startswith(b'\xff\xd8\xff')
                else 'image/webp' if data[:4] == b'RIFF' and data[8:12] == b'WEBP' else 'video/mp4' if data[4:8] == b'ftyp'
                else 'video/webm' if data[:4] == b'\x1aE\xdf\xa3' else mime)
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


def kor(job, nyckel, *, befintligt=None, registrera=None, http=None, timeout=180, clock=time.monotonic, sleep=time.sleep,
        bilddata=None, slump=None):
    """Ett POST, sedan GET. registrera(id) måste beständigt spara id:t före första pollningen.

    Återupptagning av ett accepterat asynkront jobb gör bara GET. Ett timeoutfel avbryter
    vår väntan, aldrig leverantörens jobb. Ingen automatisk ny generering vid fel.
    bilddata: källbildens byte när uppdraget har kalla_bild; samma sha256 och signatur krävs.
    """
    rent = uppdrag(job['leverantor'], job['typ'], job['prompt'], job['modell'], job['parametrar'], job.get('kalla_bild'))
    if any(job.get(k) != v for k, v in rent.items()) or not isinstance(nyckel, str) or not nyckel or re.search(r'[\r\n]', nyckel):
        raise TransportFel('ogiltigt uppdrag eller konto')
    kb = rent.get('kalla_bild')
    if kb is not None:
        if (not isinstance(bilddata, bytes) or hashlib.sha256(bilddata).hexdigest() != kb['sha256'] or len(bilddata) != kb['bytes']
                or not bilddata.startswith(BILDMIME[kb['mime']]) or (kb['mime'] == 'image/webp' and bilddata[8:12] != b'WEBP')):
            raise TransportFel('källbilden stämmer inte med uppdragets sha256 eller format')
    elif bilddata is not None:
        raise TransportFel('uppdraget har ingen källbild')
    if type(timeout) not in (float, int) or not 1 <= timeout <= 600:
        raise TransportFel('ogiltig transporttidsgräns')
    http = http or HTTP()
    slut = clock() + timeout

    def kvar(tak=30):
        t = slut - clock()
        if t <= 0:
            raise TransportFel('väntetiden tog slut; inget nytt jobb skickades')
        return min(t, tak)

    lev, p = rent['leverantor'], rent['parametrar']
    if lev == 'nano-banana':
        if befintligt:
            raise TransportFel('det synkrona bildanropet kan inte återupptas')
        inmatning = [{'type': 'text', 'text': rent['prompt']}]
        if kb is not None:  # redigering: källbilden som objekt före instruktionen (Interactions, image input)
            inmatning.insert(0, {'type': 'image', 'data': base64.b64encode(bilddata).decode('ascii'), 'mime_type': kb['mime']})
        d = http.json(GEMINI, {'x-goog-api-key': nyckel}, {'model': rent['modell'], 'input': inmatning,
                      'store': False, 'stream': False, 'response_format': dict(p, type='image', delivery='inline')}, timeout=kvar(SYNKRON_BILD))
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
            if kb is not None:  # bild till video: första bildrutan som data-URL (BytePlus LAS, role first_frame)
                body['content'].append({'type': 'image_url', 'role': 'first_frame', 'image_url': {
                    'url': 'data:%s;base64,%s' % (kb['mime'], base64.b64encode(bilddata).decode('ascii'))}})
        d = http.json(url, submit_headers, body, timeout=kvar())
        rid = jobbid(d.get('request_id' if lev == 'higgsfield' else 'id'))
        registrera(rid)
    poll = HIGGSFIELD + '/requests/' + rid + '/status' if lev == 'higgsfield' else SEEDANCE + '/' + rid
    vantan = 2.0
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
            try:
                data, mime = http.las(url, timeout=kvar(), max_bytes=MAX_FIL)
            except TransportFel as e:
                # Resultatadresser lever en begränsad tid (BytePlus LAS 24 h, Higgsfield minst sju dagar): ett nekande efter
                # färdigt jobb fastnar inte som väntande, och ingen ny generation beställs automatiskt.
                if re.search(r'HTTP-status (403|404|410)\b', str(e)):
                    raise TransportFel('resultatets adress har gått ut eller nekas; en ny version beställs uttryckligen', terminal=True) from None
                raise
            return dict(fil(data, mime, rent['typ']), jobb=rid)
        if status in ('failed', 'nsfw', 'canceled', 'cancelled', 'expired'):
            raise TransportFel('leverantören avslutade materialjobbet utan material', terminal=True)
        if status not in (('queued', 'in_progress') if lev == 'higgsfield' else ('queued', 'running')):
            raise TransportFel('materialjobbet avbröts eller gav okänd status')
        # Higgsfield: börja på 2 s och öka mot 10 s med slumpad spridning (leverantörens råd); samma för BytePlus
        sleep(min(vantan * (0.8 + 0.4 * (slump() if slump else __import__('random').random())), kvar()))
        vantan = min(10.0, vantan * 1.5)
