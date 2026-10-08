#!/usr/bin/env python3
"""Hämtar verksamhetens nuvarande sajt till underlag/<slug>/kalla/ i steg 1.

Bara GET, bara samma domän (med och utan www.), högst 40 sidor, robots.txt respekteras (RFC 9309). Adresserna kommer
ur startsidans interna länkar, sitemap.xml (och robots.txt:s Sitemap-rader) och länkarna på varje hämtad sida, i den
ordningen. Per sida sparas <namn>.html och <namn>.txt: titel, meta, text med rubrikmarkeringar, länkar med länktext,
kontaktvägar, bilder (src, data-src, srcset, <picture>, CSS-bakgrunder, og:image) och JSON-LD. SIDOR.md listar varje
adress med status och ordantal, bilderna med första sida och alt (listan att ladda ner ur), kontaktvägarna och de
externa domäner sajten länkar till (kanaler, kataloger, andra domäner).

  .venv/bin/python kontroller/hamta_sajt.py https://deras-doman.se --ut underlag/<slug>/kalla [--max 40]

En andra domän hämtas till en egen katalog: --ut underlag/<slug>/kalla/<domän>.
  --bilder underlag/<slug>/bilder     laddar ned bilderna märkta foto och okänd, och provar närliggande filnamn;
                                      ett inbäddat Instagramflöde (Smash Balloon) hamnar i bilder/instagram/ med inläggstexten som alt
  --prova-domaner "Namn, Ort"          provar namnets .se, .com och .nu (hopskrivet, med bindestreck, med ort)
Båda skriver sitt resultat sist i SIDOR.md.
"""
import argparse
import html
import http.client
import ipaddress
import json
import os
import re
import socket
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

UA = "Mozilla/5.0 (compatible; nortropic-webb-pro/1; +https://github.com/Nortropic/nortropic-webb-pro)"
UA_NAMN = "nortropic-webb-pro"
MAX_BYTE = 3_000_000
INTE_SIDA = re.compile(r"\.(pdf|jpe?g|png|gif|webp|avif|svg|ico|zip|rar|7z|docx?|xlsx?|pptx?|odt|mp4|mov|webm|mp3|"
                       r"wav|css|js|mjs|json|xml|txt|rss|woff2?|ttf|otf|eot)$", re.I)
FALLA = re.compile(r"/(wp-admin|wp-json|wp-login\.php|xmlrpc\.php|feed|cart|checkout|kassa|varukorg|my-account|"
                   r"mitt-konto|login|logga-in)(/|$)", re.I)
BLOCK = {"p", "div", "section", "article", "header", "footer", "main", "nav", "aside", "li", "ul", "ol", "tr",
         "table", "br", "blockquote", "figure", "figcaption", "address", "form", "label", "dt", "dd"}
# arkiv-, tagg- och författarsidor upprepar annat innehåll; de hämtas sist så att taket räcker till riktiga sidor
ARKIV = re.compile(r"(^|/)(author|tags?|categor(y|ies)|kategori|etikett|arkiv|archives?|page/\d+)(/|$)|_(category|tag)(/|$)",
                   re.I)
DOKUMENT = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|odt)$", re.I)
TOMMA = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
LOGGA_IKON = re.compile(r"(icon|ikon|logo|logga|button|knapp|sprite|favicon|emoji|avatar|badge|arrow|pil|social|flagga|"
                        r"payment|betal|swish|klarna|visa-|mastercard|trustpilot|rating|star|stjarn)", re.I)
HOPPA = {"script", "style", "noscript", "svg", "template", "iframe"}
VIKTIG = re.compile(r"(kontakt|contact|om-oss|om_oss|omoss|om/|about|tjanster|tj%C3%A4nster|services)", re.I)
# Adresser i det egna nätet (loopback, privata, länklokala) hämtas aldrig, inte heller via omdirigering: en sajt kunde
# annars peka om hämtaren mot dashboarden eller en annan lokal tjänst (revisionen 2026-10-03, F5). Kontrollen sker i
# själva anslutningen: namnet slås upp en gång, adressen prövas och anslutningen görs till just den adressen (ett namn som
# svarar olika vid kontroll och anslutning kan inte peka om, OWASP om SSRF). Proven kör mot 127.0.0.1 och sätter
# NWP_HAMTA_LOKALT=1: då tillåts bokstavliga lokala adresser (127.0.0.1, localhost), men ett värdnamn som pekar in i det
# egna nätet nekas fortfarande.
TILLAT_LOKALT = os.environ.get("NWP_HAMTA_LOKALT") == "1"
# Sandlådat bygge (kor.sh NWP_SANDLADA=pa): inne i Claude Codes sandlåda kan namn inte slås upp och direkta anslutningar
# nekas; all trafik går genom sandlådans proxy, som är nätgränsen (byggets domänlista, kontroller/sandlada.py, och Claude
# Codes kontroll av värdnamn som pekar på lokala adresser). Bara en proxy på den egna maskinen (loopback) räknas som
# betrodd transport: då går öppnaren via den för allt som inte undantas av NO_PROXY, och adresskontrollen behålls för
# undantagen (loopback-adresser kräver fortfarande NWP_HAMTA_LOKALT). En godtycklig proxyvariabel som pekar någon
# annanstans stänger inte av något: hämtaren ansluter då direkt med adresskontroll som förut (Codex R24, F5).


def _betrodda_proxyer():
    """(proxykarta, godkända (värd, port)) när varje satt proxyvariabel (http/https, versaler och gemener) pekar på
    loopback; annars (None, tom). Kartan ges uttryckligen till ProxyHandler, så transporten använder exakt de validerade
    adresserna och inte vad miljön råkar innehålla vid anropet (Codex R25: HTTPS_PROXY på loopback och HTTP_PROXY någon
    annanstans, eller versal mot gemen)."""
    karta, par = {}, set()
    for proto in ("http", "https"):
        vald = None
        for namn in (proto + "_proxy", proto.upper() + "_PROXY"):  # urllib läser gemener först; alla satta måste vara loopback
            w = os.environ.get(namn)
            if not w:
                continue
            u = w if "://" in w else "http://" + w
            s = urllib.parse.urlsplit(u)
            vard = (s.hostname or "").lower()
            if vard not in ("localhost", "127.0.0.1", "::1"):
                return None, set()
            try:
                port = s.port or 80
            except ValueError:
                return None, set()
            par.add((vard, port))
            if vald is None:
                vald = u
        if vald:
            karta[proto] = vald
    return (karta or None), par


PROXYKARTA, BETRODDA_PAR = _betrodda_proxyer()
VIA_PROXY = PROXYKARTA is not None


def _bypass(vard):
    """Går värden förbi proxyn (NO_PROXY)? Då gäller adresskontrollen som utan proxy."""
    try:
        return bool(urllib.request.proxy_bypass(vard or ""))
    except (OSError, ValueError):
        return False
MAX_VANTAN = 10.0  # längsta crawl-delay vi följer (sekunder); längre än så ryms inte 40 sidor i ett byggsteg
_adresser = {}


class NekadAdress(Exception):
    pass


def _upplos(vard):
    """Adresserna ett värdnamn pekar på; tom mängd när uppslaget misslyckas. Patchbar i prov."""
    try:
        return {ai[4][0] for ai in socket.getaddrinfo(vard, None)}
    except (socket.gaierror, UnicodeError):
        return set()


def adress_for(vard):
    """Adressen att ansluta till för värden, eller NekadAdress. Bokstavlig IP prövas direkt; ett värdnamn slås upp en gång
    per process och alla dess adresser måste vara publika. Ett uppslag som misslyckas nekas (ett namn som inte går att slå
    upp vid kontrollen men vid anslutningen är ett ompekningsförsök)."""
    vard = (vard or "").strip().strip("[]").lower()
    if not vard:
        raise NekadAdress("adress utan värdnamn")
    try:
        ip = ipaddress.ip_address(vard)
    except ValueError:
        ip = None
    if ip is not None:
        if ip.is_global or (TILLAT_LOKALT and (ip.is_loopback or ip.is_private)):
            return str(ip)
        raise NekadAdress(f"{vard} är en adress i det egna nätet (loopback, privat eller länklokal); hämtas inte")
    if vard == "localhost" and TILLAT_LOKALT:
        return "127.0.0.1"
    if vard not in _adresser:
        adresser = _upplos(vard)
        if not adresser:
            _adresser[vard] = NekadAdress(f"{vard} gick inte att slå upp; hämtas inte")
        else:
            try:
                publika = all(ipaddress.ip_address(a).is_global for a in adresser)
            except ValueError:
                publika = False
            if publika:
                # IPv4 först: den vanligaste vägen; samma adress används sedan hela anslutningen
                _adresser[vard] = sorted(adresser, key=lambda a: (":" in a, a))[0]
            else:
                _adresser[vard] = NekadAdress(f"{vard} pekar in i det egna nätet (loopback, privat eller länklokal adress); hämtas inte")
    svar = _adresser[vard]
    if isinstance(svar, NekadAdress):
        raise svar
    return svar


def adress_ok(url):
    """Schema och värd i en adress före anropet; själva adresskontrollen görs i anslutningen (adress_for)."""
    s = urllib.parse.urlsplit(url)
    if s.scheme not in ("http", "https"):
        raise NekadAdress(f"bara http och https hämtas, inte {s.scheme or 'tom'}:")
    if not s.hostname:
        raise NekadAdress("adress utan värdnamn")
    return True


def _anslutningsadress(host, port):
    """Adressen att ansluta till: en av de betrodda proxyerna själva (loopback, bokstavligen) eller den validerade adressen."""
    if VIA_PROXY and ((host or "").lower(), int(port)) in BETRODDA_PAR:
        return "::1" if (host or "").lower() == "::1" else "127.0.0.1"
    return adress_for(host)


class _Anslutning(http.client.HTTPConnection):
    """HTTP-anslutning som ansluter till den validerade adressen, inte till ett nytt uppslag."""

    def connect(self):
        ip = _anslutningsadress(self.host, self.port)
        self.sock = socket.create_connection((ip, self.port), self.timeout, self.source_address)
        if self._tunnel_host:
            self._tunnel()


class _SakerAnslutning(http.client.HTTPSConnection):
    """Som _Anslutning, med TLS mot värdnamnet (SNI och certifikatkontroll gäller namnet, inte adressen)."""

    def connect(self):
        ip = _anslutningsadress(self.host, self.port)
        sock = socket.create_connection((ip, self.port), self.timeout, self.source_address)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
            sock = self.sock
        self.sock = self._context.wrap_socket(sock, server_hostname=self._tunnel_host or self.host)


class _HttpHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(_Anslutning, req)


class _HttpsHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(_SakerAnslutning, req, context=self._context)


class Omdirigeringsvakt(urllib.request.HTTPRedirectHandler):
    """Varje omdirigeringsmål prövas innan det hämtas: schema, samma domän när egen är satt (sidor hämtas bara från
    verksamhetens egen domän; bilder får ligga på en annan), robots.txt när rp är satt, och takten (fore) hålls också
    mellan hoppen. Adressen prövas i anslutningen. Ett nekat mål följs inte; svaret blir 3xx med målet."""

    def __init__(self, egen=None, rp=None, fore=None, folj=True, bas=None):
        self.egen, self.rp, self.fore, self.folj, self.nekad = egen, rp, fore, folj, None
        self.bas, self.robots = bas, {}  # startens ursprung och robots per annat ursprung (omgång elva, F24)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not self.folj:
            self.nekad = "omdirigeringar följs inte"
            return None
        try:
            adress_ok(newurl)
            vard = urllib.parse.urlsplit(newurl).hostname
            if not VIA_PROXY or _bypass(vard):  # via den betrodda proxyn slås inget upp här (Codex R24); undantagen prövas som förut
                adress_for(vard)  # före hoppet, så att målet loggas; anslutningen prövar igen
        except NekadAdress as e:
            self.nekad = f"omdirigering till {newurl} följs inte: {e}"
            return None
        if self.egen and doman(urllib.parse.urlsplit(newurl).hostname) != self.egen:
            self.nekad = f"omdirigering till annan domän följs inte: {newurl}"
            return None
        if self.rp is not None:
            s = urllib.parse.urlsplit(newurl)
            malbas = f"{s.scheme}://{s.netloc}"
            rp = self.rp if (self.bas is None or malbas == self.bas) else self.robots.get(malbas)
            if rp is None:  # ursprungsbyte: målets egna regler gäller (omgång elva, F24)
                rp = self.robots[malbas] = las_robots(malbas, self.egen)[0]
            if not rp.can_fetch(UA_NAMN, newurl):
                self.nekad = f"omdirigering till {newurl} följs inte: nekad av robots.txt"
                return None
        if self.fore:
            self.fore()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def oppnare(egen=None, rp=None, fore=None, folj=True, bas=None):
    """Öppnare med adresskontroll i anslutningen och omdirigeringsvakt. Används av varje extern hämtning i repot
    (hamta_sajt, sida_till_text, standardkontrollens länkar, prospekt, Bokadirekt)."""
    vakt = Omdirigeringsvakt(egen, rp, fore, folj, bas)
    if VIA_PROXY:
        # de betrodda proxyerna på loopback är nätgränsen, givna uttryckligen (inte miljön på nytt); de validerande
        # anslutningarna behålls (proxyn själv släpps bokstavligen, allt som NO_PROXY undantar prövas som utan proxy)
        o = urllib.request.build_opener(urllib.request.ProxyHandler(dict(PROXYKARTA)), _HttpHandler(), _HttpsHandler(), vakt)
    else:
        # ProxyHandler({}): aldrig miljöns eller systemets proxy; en proxy skulle slå upp och ansluta till målet utanför
        # adresskontrollen (revisionen 2026-10-03, F5 omgång tre). Hämtaren ansluter alltid direkt.
        o = urllib.request.build_opener(urllib.request.ProxyHandler({}), _HttpHandler(), _HttpsHandler(), vakt)
    o.vakt = vakt
    return o


def antal(n, en, flera):
    return f"{n} {en if n == 1 else flera}"


def instagram_kallor(a):
    """Bildadresserna i full upplösning ur Smash Balloons attribut: data-full-res, och den största i data-img-src-set
    ({"d": standard, "150"/"320"/"640": bredder})."""
    ut = []
    if a.get("data-full-res"):
        ut.append(a["data-full-res"].strip())
    try:
        s = json.loads(a.get("data-img-src-set") or "{}")
    except ValueError:
        s = {}
    if isinstance(s, dict):
        v = s.get("d") or next((s[k] for k in sorted((k for k in s if str(k).isdigit()), key=int, reverse=True)), None)
        if isinstance(v, str) and v.strip() and v.strip() not in ut:
            ut.append(v.strip())
    return ut


def trolig_typ(url, alt, kalla, tecken):
    """Foto, logga/ikon eller okänd ur billiga tecken i HTML (crawl4ai-intaget): namn och klass med icon, logo, button
    och liknande, svg, angivna mått under 150 px, och srcset, picture eller en jpg/webp-adress som tecken på foto."""
    t = tecken or {}
    vag = urllib.parse.urlsplit(url).path.lower()
    if kalla == "instagram":
        return "foto"  # inläggsbilderna i ett Instagramflöde är verksamhetens egna foton
    if LOGGA_IKON.search(vag.rsplit("/", 1)[-1]) or LOGGA_IKON.search(t.get("klass", "")) or LOGGA_IKON.search(alt or ""):
        return "logga/ikon"
    if vag.endswith((".svg", ".ico", ".gif")):
        return "logga/ikon"
    try:
        if t.get("bredd") and t.get("hojd") and int(t["bredd"]) < 150 and int(t["hojd"]) < 150:
            return "logga/ikon"
    except ValueError:
        pass
    if t.get("ram"):
        return "logga/ikon"  # i sidhuvud, meny eller sidfot: sajtens ram
    if vag.endswith((".jpg", ".jpeg", ".webp", ".avif", ".heic")):
        return "foto"
    if t.get("srcset") and not vag.endswith(".png"):  # WordPress sätter srcset på alla bilder, också PNG-loggor
        return "foto"
    return "okänd"


def kortlista(sidor, n=5):
    if len(sidor) <= n:
        return "sidor: " + ", ".join(sidor)
    return f"på {len(sidor)} sidor, t.ex. " + ", ".join(sidor[:n])


def doman(host):
    return (host or "").lower().removeprefix("www.")


def hamta(url, timeout=20, max_byte=MAX_BYTE, egen=None, rp=None, fore=None):
    """En GET. Svarar med status, slutadress efter omdirigering, innehållstyp och kropp (högst max_byte). Anslutningen går
    till en validerad publik adress; omdirigeringsmål prövas före varje hopp (schema, egen domän, robots när rp ges,
    takten fore). En nekad omdirigering ger svarets 3xx-status med målet som url, så att anroparen kan logga den."""
    try:
        adress_ok(url)
    except NekadAdress as e:
        return {"status": None, "url": url, "typ": None, "charset": None, "data": b"", "kapad": False, "fel": f"nekad: {e}"[:200]}
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
        "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.5"})
    s0 = urllib.parse.urlsplit(url)
    opener = oppnare(egen, rp, fore, bas=f"{s0.scheme}://{s0.netloc}")
    try:
        with opener.open(req, timeout=timeout) as r:
            data = r.read(max_byte + 1)
            return {"status": r.status, "url": r.geturl(), "typ": r.headers.get_content_type(),
                    "charset": r.headers.get_content_charset(), "data": data[:max_byte], "kapad": len(data) > max_byte}
    except urllib.error.HTTPError as e:
        if opener.vakt.nekad and 300 <= e.code < 400:
            return {"status": e.code, "url": e.headers.get("Location") or url, "typ": None, "charset": None, "data": b"",
                    "kapad": False, "fel": opener.vakt.nekad[:200]}
        return {"status": e.code, "url": url, "typ": None, "charset": None, "data": b"", "kapad": False}
    except NekadAdress as e:
        return {"status": None, "url": url, "typ": None, "charset": None, "data": b"", "kapad": False, "fel": f"nekad: {e}"[:200]}
    except Exception as e:  # nätverksfel, tidsgräns, certifikat
        return {"status": None, "url": url, "typ": None, "charset": None, "data": b"", "kapad": False,
                "fel": f"{type(e).__name__}: {e}"[:200]}


def avkoda(svar):
    data = svar["data"]
    cs = svar["charset"]
    if not cs:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", data[:4096], re.I)
        cs = m.group(1).decode("ascii", "replace") if m else "utf-8"
    try:
        return data.decode(cs, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def storsta_i_srcset(srcset):
    """Största kandidaten i en srcset ("a.jpg 480w, b.jpg 1024w" → b.jpg)."""
    bast, mest = None, -1.0
    for kandidat in re.split(r",\s+(?=\S)", srcset.strip()):
        bitar = kandidat.strip().split()
        if not bitar:
            continue
        matt = 0.0
        if len(bitar) > 1:
            m = re.match(r"([\d.]+)([wx])", bitar[1])
            if m:
                matt = float(m.group(1)) * (1 if m.group(2) == "w" else 1000)
        if matt >= mest:
            bast, mest = bitar[0], matt
    return bast


class Sida(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titel, self.i_titel, self.hoppa = "", False, 0
        self.text, self.lankar, self.bilder, self.meta, self.jsonld = [], [], [], {}, []
        self.lank = None
        self.lang = self.kanonisk = None
        self.i_jsonld = False
        self.css = []
        self.i_style = False
        self.stack = []        # öppna element med klass, för förälderns klass vid en bild
        self.bildtecken = {}   # bildadress → klasser, mått och srcset, för den troliga typen i SIDOR.md

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag in ("img", "source"):
            foralder = next((c for _, c in reversed(self.stack) if c), "")
            ram = any(tg in ("header", "nav", "footer") for tg, _ in self.stack)
            for k in ("src", "data-src", "data-lazy-src", "data-original", "srcset", "data-srcset", "data-lazy-srcset"):
                if a.get(k):
                    src = storsta_i_srcset(a[k]) if "srcset" in k else a[k]
                    if src:
                        self.bildtecken.setdefault(src, {"klass": (a.get("class", "") + " " + foralder + " " + a.get("id", "")).lower(),
                                                         "bredd": a.get("width", ""), "hojd": a.get("height", ""),
                                                         "srcset": bool(a.get("srcset") or a.get("data-srcset")) or tag == "source",
                                                         "ram": ram})
        elif tag not in TOMMA:
            self.stack.append((tag, a.get("class", "")))
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.i_titel = True
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.i_jsonld = True
            self.jsonld.append("")
        if tag == "style":
            self.i_style = True
        if tag in HOPPA:
            self.hoppa += 1
        if tag == "meta":
            namn = (a.get("name") or a.get("property") or "").lower()
            if namn and a.get("content") and (namn in ("description", "robots", "generator", "keywords")
                                              or namn.startswith(("og:", "twitter:"))):
                self.meta[namn] = a["content"].strip()
        if tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.kanonisk = a.get("href")
        if tag == "a" and a.get("href"):
            self.lank = [a["href"].strip(), []]
        if tag == "img" and (a.get("data-full-res") or a.get("data-img-src-set")):
            # ett inbäddat Instagramflöde (Smash Balloon): bilden i full upplösning och inläggets text som alt; platshållaren
            # i src är inte bilden (Holm 2026-10-03, backloggen)
            for src in instagram_kallor(a):
                self.bilder.append((src, a.get("alt", ""), "instagram"))
                self.bildtecken.setdefault(src, {"klass": "instagram", "bredd": "", "hojd": "", "srcset": True, "ram": False})
        if tag == "img":
            for k in ("src", "data-src", "data-lazy-src", "data-original"):
                if a.get(k):
                    self.bilder.append((a[k], a.get("alt", ""), "img " + k))
            for k in ("srcset", "data-srcset", "data-lazy-srcset"):
                if a.get(k) and storsta_i_srcset(a[k]):
                    self.bilder.append((storsta_i_srcset(a[k]), a.get("alt", ""), "img " + k))
        if tag == "source" and (a.get("srcset") or a.get("data-srcset")):
            s = storsta_i_srcset(a.get("srcset") or a.get("data-srcset"))
            if s:
                self.bilder.append((s, "", "picture source"))
        if a.get("style") and "url(" in a["style"]:
            self.css.append(a["style"])
        if a.get("data-bg") or a.get("data-background"):
            self.bilder.append((a.get("data-bg") or a.get("data-background"), "", "data-bg"))
        if self.hoppa:
            return
        if tag in BLOCK:
            self.text.append("\n")
        if re.fullmatch(r"h[1-6]", tag):
            self.text.append(f"\n[{tag}] ")

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag == "title":
            self.i_titel = False
        if tag == "script":
            self.i_jsonld = False
        if tag == "style":
            self.i_style = False
        if tag in HOPPA and self.hoppa:
            self.hoppa -= 1
        if tag == "a" and self.lank:
            self.lankar.append((self.lank[0], " ".join("".join(self.lank[1]).split())))
            self.lank = None
        if re.fullmatch(r"h[1-6]", tag) or tag in BLOCK:
            self.text.append("\n")

    def handle_data(self, d):
        if self.i_titel:
            self.titel += d
            return
        if self.i_jsonld and self.jsonld:
            self.jsonld[-1] += d
        if self.i_style:
            self.css.append(d)
        if self.hoppa:
            return
        self.text.append(d)
        if self.lank:
            self.lank[1].append(d)

    def ren_text(self):
        t = re.sub(r"[ \t\r\f\v\u00a0]+", " ", "".join(self.text))
        return re.sub(r"\n\s*\n+", "\n", "\n".join(r.strip() for r in t.split("\n"))).strip()


def textfil(slut, svar, p, text, lankar, kontakter, sidbilder):
    """Sidans .txt: källa, metadata, text med rubrikmarkeringar, länkar, kontaktvägar, bilder och JSON-LD."""
    rader = [f"KÄLLA: {slut}", f"STATUS: {svar['status']}", f"TITEL: {' '.join(p.titel.split())}",
             f"SPRÅK: {p.lang or ''}", f"KANONISK: {p.kanonisk or ''}"]
    rader += [f"META {k}: {v}" for k, v in sorted(p.meta.items())]
    if svar["kapad"]:
        rader.append(f"OBS: sidan kapad vid {MAX_BYTE} byte")
    rader += ["---TEXT---", text, "---LÄNKAR---"]
    rader += [f"{u}  \"{t}\"" if t else u for u, t in dict.fromkeys(lankar)]
    rader += ["---KONTAKT---", *dict.fromkeys(kontakter), "---BILDER---"]
    rader += [f"{u}  alt=\"{a}\"  ({k})" for u, a, k in dict.fromkeys(sidbilder)]
    rader += ["---JSON-LD---", *[j.strip()[:6000] for j in p.jsonld if j.strip()]]
    return "\n".join(rader) + "\n"


def filnamn(url, tagna):
    vag = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    vag = re.sub(r"\.(html?|php|aspx?)$", "", vag.strip("/"), flags=re.I)
    namn = re.sub(r"[^a-z0-9åäö]+", "-", vag.lower()).strip("-")[:80] or "start"
    kandidat, n = namn, 2
    while kandidat in tagna:
        kandidat, n = f"{namn}-{n}", n + 1
    tagna.add(kandidat)
    return kandidat


class Robots:
    """robots.txt enligt RFC 9309 (urllib.robotparser kan inte * och $; revisionen 2026-10-03, F24): grupper per
    user-agent, den grupp som nämner vårt produktnamn gäller, annars *; i mönstren betyder * vad som helst och $ slutet;
    den längsta matchande regeln vinner, och Allow vinner när Allow och Disallow är lika långa. Sitemap och Crawl-delay
    läses också (Crawl-delay är en konvention utanför RFC:n)."""

    def __init__(self):
        self.grupper, self.sitemaps, self.allow_all, self.disallow_all = {}, [], False, False

    def parse(self, rader):
        # En grupp är user-agent-rader följda av regler; bara allow och disallow avslutar user-agent-raderna (crawl-delay
        # och andra poster delar inte gruppen).
        aktiva, ny_grupp = [], True
        for rad in rader:
            rad = rad.split("#", 1)[0].strip()
            if not rad or ":" not in rad:
                continue
            falt, _, varde = rad.partition(":")
            falt, varde = falt.strip().lower(), varde.strip()
            if falt == "user-agent":
                if ny_grupp:
                    aktiva = []
                    ny_grupp = False
                namn = varde.lower()
                aktiva.append(self.grupper.setdefault(namn, {"regler": [], "delay": None}))
            elif falt == "sitemap":
                self.sitemaps.append(varde)
            elif falt == "crawl-delay":
                for g in aktiva:
                    try:
                        g["delay"] = float(varde.replace(",", "."))
                    except ValueError:
                        pass
            elif falt in ("allow", "disallow"):
                ny_grupp = True
                for g in aktiva:
                    if varde or falt == "allow":
                        g["regler"].append((falt == "allow", varde))
                    # tom Disallow betyder allt tillåtet och ger ingen regel

    def grupp(self, ua):
        ua = (ua or "").lower()
        for namn, g in self.grupper.items():
            if namn == ua:
                return g
        return self.grupper.get("*")

    ORES = set(string.ascii_letters + string.digits + "-._~")

    @classmethod
    def _normalisera(cls, vag, uri=False):
        """RFC 9309 2.2.2–2.2.3: procentkodade oreserverade tecken avkodas, reserverade (och %2A, %24) behålls kodade med
        versaler, och tecken utanför ASCII eller icke skrivbara kodas. I en URI kodas dessutom bokstavliga * och $ till
        %2A och %24, så att mönstrets jokertecken och slutmarkör bara matchar som sådana (Disallow: /file%2A.html ska
        träffa /file*.html; omgång tre, F24)."""
        ut, i = [], 0
        while i < len(vag):
            c = vag[i]
            if c == "%" and re.match(r"[0-9A-Fa-f]{2}", vag[i + 1:i + 3]):
                tecken = chr(int(vag[i + 1:i + 3], 16))
                ut.append(tecken if tecken in cls.ORES else "%" + vag[i + 1:i + 3].upper())
                i += 3
                continue
            if uri and c in "*$":
                ut.append("%%%02X" % ord(c))
            else:
                ut.append(c if 0x21 <= ord(c) <= 0x7E else urllib.parse.quote(c, safe=""))
            i += 1
        return "".join(ut)

    @staticmethod
    def _matchar(monster, vag):
        slut = monster.endswith("$")
        delar = [re.escape(d) for d in monster.rstrip("$").split("*")]
        rx = "^" + ".*".join(delar) + ("$" if slut else "")
        return re.match(rx, vag) is not None

    def can_fetch(self, ua, url):
        s = urllib.parse.urlsplit(url)
        if (s.path or "/") == "/robots.txt":
            return True  # RFC 9309 2.3: robots.txt är underförstått tillåten
        if self.disallow_all:
            return False
        if self.allow_all:
            return True
        g = self.grupp(ua)
        if not g:
            return True
        vag = self._normalisera((s.path or "/") + (("?" + s.query) if s.query else ""), uri=True)
        bast = None  # (längd, allow)
        for allow, monster in g["regler"]:
            m = self._normalisera(monster)
            if self._matchar(m, vag):
                kand = (len(m), allow)
                if bast is None or kand[0] > bast[0] or (kand[0] == bast[0] and allow and not bast[1]):
                    bast = kand
        return True if bast is None else bast[1]

    def crawl_delay(self, ua):
        g = self.grupp(ua)
        return g["delay"] if g else None

    def site_maps(self):
        return self.sitemaps or None


def las_robots(bas, egen=None):
    """robots.txt enligt RFC 9309: 4xx = allt tillåtet, 5xx eller nätverksfel = inget tillåtet. Omdirigeringar av
    robots.txt följs också till en annan värd (RFC 9309 2.3.1.2), med adresskontrollen kvar; egen används inte här."""
    rp = Robots()
    svar = hamta(urllib.parse.urljoin(bas, "/robots.txt"))
    if svar["status"] == 200:
        rp.parse(avkoda(svar).splitlines())
        return rp, "hittad"
    if svar["status"] and 400 <= svar["status"] < 500:
        rp.allow_all = True
        return rp, f"saknas ({svar['status']}), allt tillåtet"
    rp.disallow_all = True
    return rp, f"kunde inte läsas ({svar['status'] or svar.get('fel')}), inget hämtas"


def sitemapadresser(bas, rp, logg, max_filer=10, vanta=None):
    """Adresserna i sitemap.xml, sitemap-index och robots.txt:s Sitemap-rader. Sidkartor med 'page' läses först.
    vanta() anropas före varje hämtning så att sidkartorna följer samma takt som sidorna."""
    gissade = [urllib.parse.urljoin(bas, v) for v in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml")]
    ko = deque(rp.site_maps() or gissade)
    lasta, adresser = set(), []
    egen = doman(urllib.parse.urlsplit(bas).hostname)
    while ko and len(lasta) < max_filer:
        karta = ko.popleft()
        if karta in lasta or doman(urllib.parse.urlsplit(karta).hostname) != egen:
            continue
        lasta.add(karta)
        if not rp.can_fetch(UA_NAMN, karta):
            logg.append(f"{karta}: nekad av robots.txt")
            continue
        if vanta:
            vanta()
        svar = hamta(karta, egen=egen, rp=rp, fore=vanta)
        data = svar["data"]
        if data[:2] == b"\x1f\x8b":
            import gzip
            try:
                data = gzip.decompress(data)
            except OSError:
                data = b""
        text = data.decode("utf-8", errors="replace")
        locs = [html.unescape(x) for x in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)]
        if svar["status"] != 200 or not locs:
            if svar["status"] == 200 or karta not in gissade:
                logg.append(f"{karta}: {svar['status'] or svar.get('fel')}, {len(locs)} adresser")
            continue
        if "<sitemapindex" in text:
            barn = sorted(locs, key=lambda u: (0 if "page" in u.lower() else 1, u))
            ko.extendleft(reversed(barn))
            logg.append(f"{karta}: index med {len(locs)} sidkartor")
        else:
            adresser += locs
            logg.append(f"{karta}: {len(locs)} adresser")
        ko = deque(u for u in ko if u not in gissade)  # en fungerande gissad sidkarta räcker
    return adresser


def hamta_sajt(start, ut, max_sidor=40, paus=0.5):
    ut = Path(ut)
    ut.mkdir(parents=True, exist_ok=True)
    tid = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    if not urllib.parse.urlsplit(start).scheme:
        start = "https://" + start
    egen = doman(urllib.parse.urlsplit(start).hostname)
    rp, robotslage = las_robots(start, egen=egen)
    vantan = max(paus, min(float(rp.crawl_delay(UA_NAMN) or 0), MAX_VANTAN))
    senaste = {"tid": time.monotonic()}  # robots.txt räknas: takten gäller alla anrop mot värden, sidkartor också

    def vanta():
        kvar = senaste["tid"] + vantan - time.monotonic()
        if kvar > 0:
            time.sleep(kvar)
        senaste["tid"] = time.monotonic()
    kartlogg = []
    sidor, bilder, kontakt, externa, dokument = [], {}, {}, {}, {}
    nekade, fel, fragestrangar, andra = [], [], set(), []
    sedda, tagna = set(), set()
    ko = deque()
    kartan = None
    generator = None

    def nyckel(u):
        s = urllib.parse.urlsplit(u)
        return doman(s.hostname), (s.path.rstrip("/") or "/")

    def lagg_till(u, forst=False):
        u = urllib.parse.urldefrag(u)[0]
        s = urllib.parse.urlsplit(u)
        if s.scheme not in ("http", "https") or doman(s.hostname) != egen:
            return
        if s.query:
            fragestrangar.add(u)
            return
        if INTE_SIDA.search(s.path) or FALLA.search(s.path) or nyckel(u) in sedda:
            return
        sedda.add(nyckel(u))
        (ko.appendleft if forst else ko.append)(u)

    lagg_till(start)
    anrop = 0
    while ko and len(sidor) < max_sidor and anrop < 2 * max_sidor:
        url = ko.popleft()
        if not rp.can_fetch(UA_NAMN, url):
            nekade.append(url)
            continue
        vanta()
        svar = hamta(url, egen=egen, rp=rp, fore=vanta)
        anrop += 1
        slut = svar["url"]
        if doman(urllib.parse.urlsplit(slut).hostname) != egen:
            andra.append(f"{url} → {slut}")
            continue
        if svar["status"] != 200 or (svar["typ"] or "") not in ("text/html", "application/xhtml+xml"):
            fel.append(f"{url}: {svar['status'] or svar.get('fel')} {svar['typ'] or ''}".strip())
            continue
        if slut != url and nyckel(slut) != nyckel(url):
            if nyckel(slut) in {nyckel(s["url"]) for s in sidor}:
                continue  # omdirigering till en sida som redan hämtats
            sedda.add(nyckel(slut))
        kod = avkoda(svar)
        p = Sida()
        p.feed(kod)
        text = p.ren_text()
        namn = filnamn(slut, tagna)
        (ut / f"{namn}.html").write_bytes(svar["data"])

        lankar, kontakter, sidbilder = [], [], []
        for href, ltext in p.lankar:
            if href.lower().startswith(("tel:", "mailto:", "sms:")):
                kontakter.append(urllib.parse.unquote(href))
                kontakt.setdefault(urllib.parse.unquote(href), []).append(namn)
                continue
            abs_ = urllib.parse.urldefrag(urllib.parse.urljoin(slut, href))[0]
            s = urllib.parse.urlsplit(abs_)
            if s.scheme not in ("http", "https"):
                continue
            lankar.append((abs_, ltext))
            if doman(s.hostname) == egen and DOKUMENT.search(s.path):
                dokument.setdefault(abs_, (namn, ltext))
            elif doman(s.hostname) == egen:
                lagg_till(abs_)
            else:
                externa.setdefault(doman(s.hostname), []).append(abs_)
        css = "\n".join(p.css)
        kandidater = list(p.bilder) + [(u, "", "css url()") for u in re.findall(r"url\(\s*['\"]?([^'\")]+)", css)]
        for k in ("og:image", "twitter:image"):
            if p.meta.get(k):
                kandidater.append((p.meta[k], "", k))
        for src, alt, kalla in kandidater:
            src = src.strip()
            if not src or src.startswith("data:") or src.startswith("#"):
                continue
            abs_ = urllib.parse.urljoin(slut, src)
            if not re.search(r"\.(jpe?g|png|webp|avif|gif|svg)(\?|$)", abs_, re.I) and not kalla.startswith(("img", "picture", "og", "twitter")):
                continue  # CSS-url() till typsnitt och liknande
            sidbilder.append((abs_, alt, kalla))
            post = bilder.setdefault(abs_, {"sida": namn, "alt": alt, "kalla": kalla, "sidor": set(),
                                            "typ": trolig_typ(abs_, alt, kalla, p.bildtecken.get(src))})
            post["sidor"].add(namn)
            if alt and not post["alt"]:
                post["alt"] = alt

        if not sidor:
            generator = p.meta.get("generator")
            # startsidans länkar (oftast menyn) först, sedan sidkartan, sedan länkarna på varje sida i tur och ordning;
            # kontakt, om oss och tjänster främst i menyn, så att de ryms inom ett lågt tak (prospektanalysen hämtar 8 sidor)
            vag_ = lambda u: urllib.parse.urlsplit(u).path
            meny = sorted(ko, key=lambda u: 0 if VIKTIG.search(vag_(u)) else 1)
            ko.clear()
            kartan = sitemapadresser(slut, rp, kartlogg, vanta=vanta)
            for u in meny:
                ko.append(u)
            vag = lambda u: urllib.parse.urlsplit(u).path.strip("/")
            for u in sorted(kartan, key=lambda u: (bool(ARKIV.search(vag(u))), vag(u).count("/"))):
                lagg_till(u)

        (ut / f"{namn}.txt").write_text(textfil(slut, svar, p, text, lankar, kontakter, sidbilder), encoding="utf-8")
        sidor.append({"fil": namn, "url": slut, "status": svar["status"], "ord": len(re.findall(r"\w+", text)),
                      "titel": " ".join(p.titel.split())})

    kvar = list(ko)
    delay = rp.crawl_delay(UA_NAMN)
    md = [f"# Sidor hämtade från {start} ({tid})", "",
          f"Verktyg: `kontroller/hamta_sajt.py`, bara GET, samma domän, högst {max_sidor} sidor, "
          f"{vantan:g} s mellan anropen" + (f" (robots.txt begär {delay:g} s; vi följer högst {MAX_VANTAN:g})" if delay and delay > MAX_VANTAN else "")
          + f". robots.txt: {robotslage}. Sidkarta: "
          + ("; ".join(kartlogg) if kartlogg else "ingen hittad") + ".",
          f"Hämtade {antal(len(sidor), 'sida', 'sidor')}" + (f"; {antal(len(kvar), 'adress', 'adresser')} kvar i kön när taket nåddes (listade sist)."
                                           if kvar else "; inga adresser kvar i kön."), "",
          "| Fil | Adress | Status | Ord | Titel |", "|---|---|---|---|---|"]
    md += [f"| {s['fil']} | {s['url']} | {s['status']} | {s['ord']} | {s['titel'].replace('|', '/')} |" for s in sidor]
    md += ["", f"## Bilder ({len(bilder)} unika)", "",
           "Alla bildadresser som sidorna pekar på, med första sida och alt. Ladda ner verksamhetens egna med curl;",
           "ikoner, logotyper från andra och stockbilder hör inte till bildunderlaget.", "",
           "Sorterad efter trolig typ: foto först, okänd sedan, logga/ikon sist (gissat ur namn, klass, mått och filtyp).",
           "Ladda ner ur raderna märkta foto och titta på dem märkta okänd.", "",
           "| Bild | Trolig typ | Första sida | Sidor | Alt | Källa |", "|---|---|---|---|---|---|"]
    ordning = {"foto": 0, "okänd": 1, "logga/ikon": 2}
    for b in bilder.values():  # en bild på nästan varje sida hör till sajtens ram (logga, märke), inte till jobben
        if len(sidor) >= 3 and len(b["sidor"]) >= 0.8 * len(sidor):
            b["typ"] = "logga/ikon"
    md += [f"| {u} | {b['typ']} | {b['sida']} | {len(b['sidor'])} | {b['alt'].replace('|', '/')} | {b['kalla']} |"
           for u, b in sorted(bilder.items(), key=lambda x: (ordning[x[1]['typ']], -len(x[1]['sidor'])))]
    md += ["", "## Dokument på sajten", ""]
    md += [f"- {u} (sida {s}, \"{lt}\")" for u, (s, lt) in dokument.items()] or ["- inga"]
    md += ["", "## Kontaktvägar på sajten", ""]
    md += [f"- {k} ({kortlista(list(dict.fromkeys(v)))})" for k, v in kontakt.items()] or ["- inga tel:- eller mailto:-länkar"]
    md += ["", "## Externa domäner som sajten länkar till", "",
           "Kanaler, kataloger och andra domäner: läs dem som egna källor i steg 1.", ""]
    md += [f"- {d} ({antal(len(v), 'länk', 'länkar')}, t.ex. {v[0]})" for d, v in sorted(externa.items(), key=lambda x: -len(x[1]))] or ["- inga"]
    md += ["", "## Inte hämtade", ""]
    md += [f"- nekad av robots.txt: {u}" for u in nekade]
    md += [f"- fel: {f}" for f in fel]
    md += [f"- omdirigerad till annan domän: {a}" for a in andra]
    if fragestrangar:
        md.append(f"- {antal(len(fragestrangar), 'adress', 'adresser')} med frågesträng överhoppade, t.ex. {sorted(fragestrangar)[0]}")
    md += [f"- över taket: {u}" for u in kvar]
    if md[-1] == "":
        md.append("- inget")
    (ut / "SIDOR.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"ut": str(ut), "sidor": len(sidor), "bilder": len(bilder), "kvar": len(kvar), "nekade": len(nekade),
            "fel": len(fel), "robots": robotslage, "sidkarta": kartlogg, "generator": generator,
            "bildlista": [{"url": u, "typ": b["typ"], "alt": b["alt"], "kalla": b["kalla"]} for u, b in bilder.items()],
            "sidlista": [{"fil": x["fil"], "url": x["url"], "status": x["status"]} for x in sidor]}


BILD_MAX = 15_000_000
NUMMER = re.compile(r"^(.*?)(\d{1,3})(\.(?:jpe?g|png|webp|avif))$", re.I)


def ladda_bilder(bildlista, katalog, paus=0.5, max_prov=24):
    """Laddar ned bilderna märkta foto eller okänd till katalogen och provar närliggande filnamn i samma mapp (k1, k3
    … ger k2): salongens bästa bild låg på servern utan att vara länkad (salong-kreativ 2026-10-03). Bara GET,
    robots.txt för varje värd, högst max_prov gissade adresser. Svarar med en rad per bild. Bilder ur ett inbäddat
    Instagramflöde (källan instagram) hamnar i instagram/ med inläggets text som alt."""
    katalog = Path(katalog)
    katalog.mkdir(parents=True, exist_ok=True)
    robots, rader, tagna = {}, [], {f.name for f in katalog.iterdir()}

    def robots_for(u):
        s = urllib.parse.urlsplit(u)
        bas = f"{s.scheme}://{s.netloc}"
        if bas not in robots:
            robots[bas] = las_robots(bas)[0]
        return robots[bas]

    def spara(u, typ, gissad, undermapp="", alt=""):
        rp = robots_for(u)
        if not rp.can_fetch(UA_NAMN, u):
            rader.append({"url": u, "typ": typ, "fil": "", "status": "nekad av robots.txt", "gissad": gissad, "alt": alt})
            return False
        svar = hamta(u, max_byte=BILD_MAX, rp=rp)  # policyn följer med genom omdirigeringarna (omgång elva, F24)
        time.sleep(paus)
        if svar["status"] != 200 or not (svar["typ"] or "").startswith("image/"):
            if not gissad:
                rader.append({"url": u, "typ": typ, "fil": "", "status": str(svar["status"] or svar.get("fel")), "gissad": gissad, "alt": alt})
            return False
        namn = urllib.parse.unquote(urllib.parse.urlsplit(u).path.rsplit("/", 1)[-1]) or "bild"
        namn = re.sub(r"[^\w.\-]+", "-", namn)
        stam, _, ext = namn.rpartition(".")
        kandidat, n = namn, 2
        if undermapp:
            (katalog / undermapp).mkdir(parents=True, exist_ok=True)
            tagna.update(f.name for f in (katalog / undermapp).iterdir())
        while kandidat in tagna:
            kandidat, n = f"{stam or namn}-{n}.{ext}" if stam else f"{namn}-{n}", n + 1
        tagna.add(kandidat)
        rel = f"{undermapp}/{kandidat}" if undermapp else kandidat
        (katalog / rel).write_bytes(svar["data"])
        rader.append({"url": u, "typ": typ, "fil": rel, "status": f"{len(svar['data'])} byte", "gissad": gissad, "alt": alt})
        return True

    grupper = {}
    for b in bildlista:
        u = b["url"]
        if b["typ"] not in ("foto", "okänd") or re.search(r"\.svg(\?|$)", u, re.I):
            continue
        if b.get("kalla") == "instagram":
            spara(u, b["typ"], False, "instagram", b.get("alt", ""))
            continue
        if spara(u, b["typ"], False, "", b.get("alt", "")):
            mapp, _, fil = urllib.parse.urlsplit(u)._replace(query="", fragment="").geturl().rpartition("/")
            m = NUMMER.match(fil)
            if m and not re.search(r"-\d+x\d+$", m.group(1)):  # WordPress storleksvarianter är inte en serie
                grupper.setdefault((mapp, m.group(1), m.group(3), len(m.group(2))), set()).add(int(m.group(2)))
    prov = 0
    for (mapp, forled, ext, bredd), kanda in grupper.items():
        if len(kanda) < 2:
            continue  # en ensam numrerad bild är ingen serie
        for n in range(1, max(kanda) + 3):
            if n in kanda or prov >= max_prov:
                continue
            prov += 1
            spara(f"{mapp}/{forled}{str(n).zfill(bredd) if bredd > 1 else n}{ext}", "gissad", True)
    return rader


def domankandidater(namn, egen=""):
    """Namnets vanliga domäner: hopskrivet och med bindestreck, med och utan ort, .se, .com och .nu."""
    namn, _, ort = namn.partition(",")
    tr = str.maketrans("åäöéü", "aaoeu")
    ord_ = [w for w in re.findall(r"[a-z0-9]+", namn.lower().translate(tr)) if w not in ("ab", "hb", "kb", "aktiebolag")]
    ort_ = re.findall(r"[a-z0-9]+", ort.lower().translate(tr))
    baser = ["".join(ord_), "-".join(ord_)]
    if ort_:
        baser += ["".join(ord_ + ort_), "-".join(ord_ + ort_)]
    ut = []
    for b in dict.fromkeys(baser):
        for tld in ("se", "com", "nu"):
            if b and f"{b}.{tld}" not in ut:
                ut.append(f"{b}.{tld}")
    return [d for d in ut if d != doman(egen)]


def prova_domaner(namn, egen="", paus=0.3):
    """Svarar med en rad per kandidat: domän, status, slutadress och titel. Bara en GET mot startsidan."""
    rader = []
    for d in domankandidater(namn, egen):
        svar = hamta(f"https://{d}/", timeout=10)
        if svar["status"] is None:
            svar = hamta(f"http://{d}/", timeout=10)
        titel = ""
        if svar["status"] == 200:
            m = re.search(r"<title[^>]*>(.*?)</title>", avkoda(svar), re.S | re.I)
            titel = " ".join(html.unescape(m.group(1)).split())[:80] if m else ""
        rader.append({"doman": d, "status": svar["status"] or svar.get("fel", "")[:60], "slut": svar["url"], "titel": titel})
        time.sleep(paus)
    return rader


def lagg_till_i_sidor(ut, bilder=None, domaner=None):
    md = []
    if bilder is not None:
        md += ["", f"## Nedladdade bilder (--bilder, {sum(1 for r in bilder if r['fil'])} filer)", "",
               "Gissad = hittad genom att pröva närliggande filnamn i samma mapp; den är inte länkad från sajten.", "",
               "| Fil | Adress | Typ | Alt | Svar |", "|---|---|---|---|---|"]
        md += [f"| {r['fil'] or '–'} | {r['url']} | {r['typ']} | {str(r.get('alt') or '').replace('|', '/')} | {r['status']} |" for r in bilder] or ["| – | – | – | – | inga |"]
    if domaner is not None:
        md += ["", "## Andra domäner (--prova-domaner)", "",
               "Svarar en domän med 200 och en egen titel är den en källa: hämta den med --ut kalla/<domän>.", "",
               "| Domän | Svar | Slutadress | Titel |", "|---|---|---|---|"]
        md += [f"| {r['doman']} | {r['status']} | {r['slut']} | {r['titel'].replace('|', '/')} |" for r in domaner]
    with open(Path(ut) / "SIDOR.md", "a", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("start", help="startadress, t.ex. https://deras-doman.se")
    ap.add_argument("--ut", required=True, help="katalog, t.ex. underlag/<slug>/kalla")
    ap.add_argument("--max", type=int, default=40, help="högst så många sidor (40)")
    ap.add_argument("--bilder", metavar="KATALOG", help="ladda ned foto och okänd hit, t.ex. underlag/<slug>/bilder")
    ap.add_argument("--prova-domaner", metavar="NAMN", help='pröva namnets domäner, t.ex. "Salong Kreativ, Luleå"')
    a = ap.parse_args()
    krav_vag(a.ut, "--ut")
    krav_vag(a.bilder, "--bilder")
    if a.max > 40:
        sys.exit("högst 40 sidor")
    r = hamta_sajt(a.start, a.ut, a.max)
    bilder = ladda_bilder(r["bildlista"], a.bilder) if a.bilder else None
    domaner = prova_domaner(a.prova_domaner, urllib.parse.urlsplit(a.start if "//" in a.start else "https://" + a.start).hostname) if a.prova_domaner else None
    if bilder is not None or domaner is not None:
        lagg_till_i_sidor(a.ut, bilder, domaner)
        r["nedladdade"] = sum(1 for x in bilder or [] if x["fil"])
        r["gissade"] = sum(1 for x in bilder or [] if x["fil"] and x["gissad"])
        r["domaner"] = [x["doman"] for x in domaner or [] if x["status"] == 200]
    r.pop("bildlista", None)
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["sidor"] else 1)


if __name__ == "__main__":
    main()
