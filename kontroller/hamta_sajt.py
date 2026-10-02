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
"""
import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

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
HOPPA = {"script", "style", "noscript", "svg", "template", "iframe"}
VIKTIG = re.compile(r"(kontakt|contact|om-oss|om_oss|omoss|om/|about|tjanster|tj%C3%A4nster|services)", re.I)


def antal(n, en, flera):
    return f"{n} {en if n == 1 else flera}"


def kortlista(sidor, n=5):
    if len(sidor) <= n:
        return "sidor: " + ", ".join(sidor)
    return f"på {len(sidor)} sidor, t.ex. " + ", ".join(sidor[:n])


def doman(host):
    return (host or "").lower().removeprefix("www.")


def hamta(url, timeout=20):
    """En GET. Svarar med status, slutadress efter omdirigering, innehållstyp och kropp (högst MAX_BYTE)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5",
        "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(MAX_BYTE + 1)
            return {"status": r.status, "url": r.geturl(), "typ": r.headers.get_content_type(),
                    "charset": r.headers.get_content_charset(), "data": data[:MAX_BYTE], "kapad": len(data) > MAX_BYTE}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "url": url, "typ": None, "charset": None, "data": b"", "kapad": False}
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

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
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


def filnamn(url, tagna):
    vag = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    vag = re.sub(r"\.(html?|php|aspx?)$", "", vag.strip("/"), flags=re.I)
    namn = re.sub(r"[^a-z0-9åäö]+", "-", vag.lower()).strip("-")[:80] or "start"
    kandidat, n = namn, 2
    while kandidat in tagna:
        kandidat, n = f"{namn}-{n}", n + 1
    tagna.add(kandidat)
    return kandidat


def las_robots(bas):
    """robots.txt enligt RFC 9309: 4xx = allt tillåtet, 5xx eller nätverksfel = inget tillåtet."""
    rp = urllib.robotparser.RobotFileParser()
    svar = hamta(urllib.parse.urljoin(bas, "/robots.txt"))
    if svar["status"] == 200:
        rp.parse(avkoda(svar).splitlines())
        return rp, "hittad"
    if svar["status"] and 400 <= svar["status"] < 500:
        rp.parse([])
        rp.allow_all = True
        return rp, f"saknas ({svar['status']}), allt tillåtet"
    rp.disallow_all = True
    return rp, f"kunde inte läsas ({svar['status'] or svar.get('fel')}), inget hämtas"


def sitemapadresser(bas, rp, logg, max_filer=10):
    """Adresserna i sitemap.xml, sitemap-index och robots.txt:s Sitemap-rader. Sidkartor med 'page' läses först."""
    gissade = [urllib.parse.urljoin(bas, v) for v in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml")]
    ko = deque(rp.site_maps() or gissade)
    lasta, adresser = set(), []
    while ko and len(lasta) < max_filer:
        karta = ko.popleft()
        if karta in lasta or doman(urllib.parse.urlsplit(karta).hostname) != doman(urllib.parse.urlsplit(bas).hostname):
            continue
        lasta.add(karta)
        if not rp.can_fetch(UA_NAMN, karta):
            logg.append(f"{karta}: nekad av robots.txt")
            continue
        svar = hamta(karta)
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
    rp, robotslage = las_robots(start)
    vantan = max(paus, min(float(rp.crawl_delay(UA_NAMN) or 0), 5.0))
    egen = doman(urllib.parse.urlsplit(start).hostname)
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
        if sidor or fel:
            time.sleep(vantan)
        svar = hamta(url)
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
            post = bilder.setdefault(abs_, {"sida": namn, "alt": alt, "kalla": kalla, "sidor": set()})
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
            kartan = sitemapadresser(slut, rp, kartlogg)
            for u in meny:
                ko.append(u)
            vag = lambda u: urllib.parse.urlsplit(u).path.strip("/")
            for u in sorted(kartan, key=lambda u: (bool(ARKIV.search(vag(u))), vag(u).count("/"))):
                lagg_till(u)

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
        (ut / f"{namn}.txt").write_text("\n".join(rader) + "\n", encoding="utf-8")
        sidor.append({"fil": namn, "url": slut, "status": svar["status"], "ord": len(re.findall(r"\w+", text)),
                      "titel": " ".join(p.titel.split())})

    kvar = list(ko)
    md = [f"# Sidor hämtade från {start} ({tid})", "",
          f"Verktyg: `kontroller/hamta_sajt.py`, bara GET, samma domän, högst {max_sidor} sidor, "
          f"{vantan:g} s mellan anropen. robots.txt: {robotslage}. Sidkarta: "
          + ("; ".join(kartlogg) if kartlogg else "ingen hittad") + ".",
          f"Hämtade {antal(len(sidor), 'sida', 'sidor')}" + (f"; {antal(len(kvar), 'adress', 'adresser')} kvar i kön när taket nåddes (listade sist)."
                                           if kvar else "; inga adresser kvar i kön."), "",
          "| Fil | Adress | Status | Ord | Titel |", "|---|---|---|---|---|"]
    md += [f"| {s['fil']} | {s['url']} | {s['status']} | {s['ord']} | {s['titel'].replace('|', '/')} |" for s in sidor]
    md += ["", f"## Bilder ({len(bilder)} unika)", "",
           "Alla bildadresser som sidorna pekar på, med första sida och alt. Ladda ner verksamhetens egna med curl;",
           "ikoner, logotyper från andra och stockbilder hör inte till bildunderlaget.", "",
           "| Bild | Första sida | Sidor | Alt | Källa |", "|---|---|---|---|---|"]
    md += [f"| {u} | {b['sida']} | {len(b['sidor'])} | {b['alt'].replace('|', '/')} | {b['kalla']} |"
           for u, b in bilder.items()]
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
            "sidlista": [{"fil": x["fil"], "url": x["url"], "status": x["status"]} for x in sidor]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("start", help="startadress, t.ex. https://deras-doman.se")
    ap.add_argument("--ut", required=True, help="katalog, t.ex. underlag/<slug>/kalla")
    ap.add_argument("--max", type=int, default=40, help="högst så många sidor (40)")
    a = ap.parse_args()
    if a.max > 40:
        sys.exit("högst 40 sidor")
    r = hamta_sajt(a.start, a.ut, a.max)
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["sidor"] else 1)


if __name__ == "__main__":
    main()
