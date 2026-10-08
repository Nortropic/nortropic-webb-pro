#!/usr/bin/env python3
"""Avgränsad kundyta på loopback. Ingen administrativ endpoint eller modellstart.

Startas uttryckligen; live-AI körs av separat arbetare. Bearer-bevis finns i
länkens fragment, aldrig i URL-sökvägen, och prövas för varje ärendeoperation.
Detta är lokal drift, inte en färdig publik hosting-/autentiseringslösning.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import quote, urlsplit

import kundstart

YTAN = Path(__file__).resolve().parents[1] / 'kundstart'
MAX_BODY = 6 * 1024 * 1024
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' blob:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"


class Kundhandler(BaseHTTPRequestHandler):
    server_version = 'Kundstart'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *_args):
        pass  # inga URL:er, autentiseringsuppgifter eller kundsvar i serverlogg

    def _svara(self, status, body, typ='application/json; charset=utf-8', extra=None):
        raw=kundstart.jsontext(body).encode() if isinstance(body,(dict,list)) else body
        self.send_response(status)
        for k,v in {'Content-Type':typ,'Content-Length':str(len(raw)),'Cache-Control':'no-store',
                    'Content-Security-Policy':CSP,'Referrer-Policy':'no-referrer','X-Content-Type-Options':'nosniff',
                    'Connection':'close',**(extra or {})}.items():
            self.send_header(k,v)
        self.end_headers();self.close_connection=True
        if self.command!='HEAD':self.wfile.write(raw)

    def _ursprung(self):
        host=self.headers.get('Host')
        port=self.server.server_address[1]
        if len(self.headers.get_all('Host',[]))!=1 or host not in ('127.0.0.1:%d'%port,'localhost:%d'%port):
            raise kundstart.Obehorig('Fel ursprung.')
        origins=self.headers.get_all('Origin',[])
        if len(origins)>1 or (origins and origins[0]!='http://'+host) or (self.command=='POST' and not origins):
            raise kundstart.Obehorig('Fel ursprung.')

    def _token(self):
        values=self.headers.get_all('Authorization',[])
        if len(values)!=1 or not values[0].startswith('Bearer '):
            raise kundstart.Obehorig('Ärendet är inte tillgängligt.')
        return values[0][7:]

    def _body(self):
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length',[]))!=1:
            raise kundstart.Vagrad('Ogiltig överföring.')
        try:n=int(self.headers.get('Content-Length'))
        except (TypeError,ValueError) as e:raise kundstart.Vagrad('Ogiltig längd.') from e
        if not 0<n<=MAX_BODY or self.headers.get('Content-Type','').split(';')[0]!='application/json':
            raise kundstart.Vagrad('För stor eller okänd överföring.')
        raw=self.rfile.read(n)
        if len(raw)!=n:raise kundstart.Vagrad('Överföringen blev inte komplett.')
        return json.loads(raw)

    def _kor(self):
        self._ursprung()
        parts=urlsplit(self.path)
        if parts.query or parts.fragment:
            self._svara(404,{'fel':'Sidan finns inte.'});return
        path=parts.path
        static={'/':('index.html','text/html; charset=utf-8'), '/kundstart.js':('kundstart.js','text/javascript; charset=utf-8'),
                '/kundstart.css':('kundstart.css','text/css; charset=utf-8')}
        if self.command in ('GET','HEAD') and path in static:
            namn,typ=static[path]
            self._svara(200,(YTAN/namn).read_bytes(),typ);return
        m=re.fullmatch(r'/api/arende/([a-f0-9]{32})(?:/bilaga/([a-f0-9]{32}))?',path)
        if not m:
            self._svara(404,{'fel':'Sidan finns inte.'});return
        eid,bid=m.groups();token=self._token()
        if self.command=='GET' and bid:
            namn,typ,raw=self.server.lager.bilaga(eid,token,bid)
            self._svara(200,raw,'application/octet-stream',{'Content-Disposition':"attachment; filename*=UTF-8''"+quote(namn,safe='')})
        elif self.command=='GET':
            self._svara(200,self.server.lager.las(eid,token))
        elif self.command=='POST' and not bid:
            data=self._body()
            kundstart.falt(data,('revision','operation','handling','data'),('revision','operation','handling','data'))
            svar=self.server.lager.kundhandling(eid,token,data['revision'],data['operation'],data['handling'],data['data'])
            self._svara(200,svar)
        else:self._svara(405,{'fel':'Metoden stöds inte.'})

    def _saker_kor(self):
        try:self._kor()
        except kundstart.Obehorig:self._svara(403,{'fel':'Ärendet eller ursprunget är inte tillgängligt. Använd en aktuell ärendelänk.'})
        except kundstart.Konflikt as e:self._svara(409,{'fel':str(e)})
        except kundstart.Vagrad as e:self._svara(400,{'fel':str(e)})
        except (UnicodeError,ValueError,TypeError,KeyError):self._svara(400,{'fel':'Uppgifterna gick inte att läsa. Ditt lokala utkast finns kvar.'})
        except (OSError,sqlite3.Error,RuntimeError):self._svara(503,{'fel':'Det gick inte att bekräfta lagringen. Behåll ditt utkast och försök igen.'})

    do_GET = _saker_kor
    do_POST = _saker_kor
    do_HEAD = _saker_kor


def server(lager,port=4773):
    s=ThreadingHTTPServer(('127.0.0.1',port),Kundhandler)
    s.daemon_threads=True
    s.lager=lager
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port',type=int,default=4773)
    a=p.parse_args()
    if not 1024<=a.port<=65535 or a.port==4771:p.error('Välj en egen port mellan 1024 och 65535, aldrig dashboardens 4771.')
    s=server(kundstart.Lager(),a.port)
    print('Kundstart lokal på http://127.0.0.1:%d/ — ingen live-AI startas.'%a.port)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()


if __name__=='__main__':main()
