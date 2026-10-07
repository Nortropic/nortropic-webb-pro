#!/usr/bin/env python3
"""youtube.py — en video som markdown för kirurgen: metadata, länkar ur beskrivningen, och en tidslinje där
transkriptet och bildrutor ur videon står flätade vid samma tidpunkt. Så ser kirurgen både vad som sägs och vad som
visas. Fungerar för YouTube och för de flesta andra videosajter som yt-dlp stöder (Vimeo, Loom, X med flera).
Körs lokalt (YouTube blockerar många moln-IP:n).

    .venv/bin/python kontroller/youtube.py 'URL' --ut FIL.md [--bilder 40] [--avsnitt 21:00-22:30 ...] [--sprak sv,en]

Bildrutor: videon hämtas utan ljud i högst 720p, N bildrutor tas jämnt över videon plus en vid varje kapitelstart,
skalas till 1280 px bredd och sparas som FIL-bilder/bild-MMmSSs.jpg. --avsnitt ger en bildruta varannan sekund i
ett avsnitt (högst 90 per avsnitt), för att se rörelse, animationer och flöden. Videofilen raderas efteråt.
--bilder 0 hoppar över de jämna bildrutorna. ffmpeg kommer ur paketet imageio-ffmpeg i repots .venv.
Transkript: YouTubes eget i första hand, annars undertexter (manuella eller automatiska) genom yt-dlp.
Exit 0 = filen skriven (transkript eller bildrutor kan saknas, då står det i filen); 2 = fel i anropet eller metadata.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slugvakt import krav_slug, krav_vag  # noqa: E402  (revisionen 2026-10-03, F1: bara det egna bygget)

LANK = re.compile(r'https?://\S+')


def video_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else (url if re.fullmatch(r'[A-Za-z0-9_-]{11}', url) else None)


def ytdlp():
    return shutil.which('yt-dlp', path=str(Path(sys.executable).parent)) or shutil.which('yt-dlp')


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which('ffmpeg')


def metadata(url):
    y = ytdlp()
    if not y:
        return None, 'yt-dlp saknas (.venv/bin/python -m pip install yt-dlp)'
    p = subprocess.run([y, '--skip-download', '--dump-single-json', '--no-warnings', url], capture_output=True, text=True, timeout=120)
    if p.returncode:
        return None, (p.stderr or p.stdout).strip()[-500:]
    return json.loads(p.stdout), None


def transkript(vid, sprak):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, None, 'youtube-transcript-api saknas'
    try:
        lista = YouTubeTranscriptApi().list(vid)
        valt = None
        for finder in (lista.find_manually_created_transcript, lista.find_generated_transcript, lista.find_transcript):
            try:
                valt = finder(sprak)
                break
            except Exception:
                continue
        if valt is None:
            valt = next(iter(lista))
        return [(s.start, s.text) for s in valt.fetch()], '%s (%s)' % (valt.language, 'autogenererat' if valt.is_generated else 'manuellt'), None
    except Exception as e:
        return None, None, '%s: %s' % (type(e).__name__, str(e).splitlines()[0][:300])


def undertexter(url, sprak):
    """Reserv: undertexter genom yt-dlp (manuella före automatiska), som [(sekund, text)] utan upprepningar."""
    y = ytdlp()
    if not y:
        return None, None, 'yt-dlp saknas'
    langs = ','.join('%s.*' % s for s in sprak) or 'en.*'
    import korregister
    with korregister.egen_tmp_med('nwp-sub-', 'youtube') as tmp:  # registrerad som körningens egen (städregeln, 2026-10-07)
        p = subprocess.run([y, '--skip-download', '--no-warnings', '--write-subs', '--write-auto-subs', '--sub-langs', langs,
                            '--sub-format', 'vtt', '-o', str(Path(tmp) / 'sub'), url], capture_output=True, text=True, timeout=180)
        filer = sorted(Path(tmp).glob('sub*.vtt'), key=lambda f: ('auto' in f.name, f.name))
        if not filer:
            return None, None, 'inga undertexter (%s)' % ((p.stderr or '').strip()[-200:] or 'videon har inga')
        rader, sett = [], set()
        for block in filer[0].read_text(encoding='utf-8', errors='replace').split('\n\n'):
            m = re.search(r'(\d+):(\d{2}):(\d{2})[.,](\d{3}) -->', block) or re.search(r'(\d{2}):(\d{2})[.,](\d{3}) -->', block)
            if not m:
                continue
            g = [int(x) for x in m.groups()]
            sek = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 4 else g[0] * 60 + g[1]
            for rad in block.split('\n')[1:]:
                if '-->' in rad:
                    continue
                text = re.sub(r'<[^>]+>', '', rad).strip()
                if text and text not in sett:
                    sett.add(text)
                    rader.append((sek, text))
        return (rader or None), 'undertexter via yt-dlp (%s)' % filer[0].name.split('.', 1)[-1].rsplit('.', 1)[0], (None if rader else 'tomma undertexter')


def avsnitt_tider(spec, langd):
    """'21:00-22:30' → sekunder varannan sekund, högst 90."""
    m = re.fullmatch(r'(?:(\d+):)?(\d+):(\d{2})-(?:(\d+):)?(\d+):(\d{2})', spec.strip())
    if not m:
        raise ValueError('avsnitt ska vara MM:SS-MM:SS eller H:MM:SS-H:MM:SS: ' + spec)
    h1, m1, s1, h2, m2, s2 = [int(x or 0) for x in m.groups()]
    a, b = h1 * 3600 + m1 * 60 + s1, min(h2 * 3600 + m2 * 60 + s2, langd or 10 ** 9)
    if b <= a:
        raise ValueError('avsnittets slut måste ligga efter början: ' + spec)
    steg = max(2.0, (b - a) / 90)
    ut, t = [], float(a)
    while t <= b:
        ut.append(t)
        t += steg
    return ut


def tid(s):
    s = int(s)
    return '%d:%02d:%02d' % (s // 3600, s % 3600 // 60, s % 60) if s >= 3600 else '%02d:%02d' % (s // 60, s % 60)


def tidpunkter(langd, antal, kapitel):
    """Jämnt över 3–97 % av videon, plus kapitelstarter (+2 s); dubbletter inom 12 s tas bort."""
    if langd <= 0 or antal <= 0:
        return []
    start, slut = langd * 0.03, langd * 0.97
    steg = (slut - start) / max(antal - 1, 1)
    punkter = [start + i * steg for i in range(antal)] + [c.get('start_time', 0) + 2 for c in kapitel or [] if c.get('start_time', 0) + 2 < langd]
    ut = []
    for t in sorted(punkter):
        if not ut or t - ut[-1] >= 12:
            ut.append(t)
    return ut


def bildrutor(url, langd, antal, kapitel, mapp, avsnitt=()):
    """Hämtar videon utan ljud (≤ 720p) och tar ut bildrutor. Returnerar [(sekund, sökväg)] och ett eventuellt fel."""
    y, f = ytdlp(), ffmpeg()
    if not f:
        return [], 'ffmpeg saknas (.venv/bin/python -m pip install imageio-ffmpeg)'
    mapp.mkdir(parents=True, exist_ok=True)
    import korregister
    with korregister.egen_tmp_med('nwp-yt-', 'youtube') as tmp:
        p = subprocess.run([y, '--no-playlist', '--no-warnings', '-f', 'bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]/b',
                            '--ffmpeg-location', f, '-o', str(Path(tmp) / 'video.%(ext)s'), url],
                           capture_output=True, text=True, timeout=900)
        filer = [x for x in Path(tmp).iterdir() if x.name.startswith('video.') and not x.name.endswith('.part')]
        if p.returncode or not filer:
            return [], 'nedladdningen misslyckades: ' + (p.stderr or p.stdout).strip()[-300:]
        video = filer[0]
        ut = []
        tider = tidpunkter(langd, antal, kapitel) + [t for spec in avsnitt for t in avsnitt_tider(spec, langd)]
        for t in sorted(set(int(x) for x in tider)):
            namn = mapp / ('bild-%02dm%02ds.jpg' % (t // 60, t % 60))
            r = subprocess.run([f, '-loglevel', 'error', '-y', '-ss', '%.2f' % t, '-i', str(video), '-frames:v', '1',
                                '-vf', 'scale=1280:-2', '-q:v', '3', str(namn)], capture_output=True, text=True, timeout=120)
            if r.returncode == 0 and namn.is_file():
                ut.append((t, namn))
    return ut, None


def main(argv=None):
    p = argparse.ArgumentParser(prog='youtube', description=__doc__.split('\n\n')[0])
    p.add_argument('url')
    p.add_argument('--ut', required=True)
    p.add_argument('--bilder', type=int, default=40)
    p.add_argument('--avsnitt', action='append', default=[], help='MM:SS-MM:SS, en bildruta varannan sekund; får upprepas')
    p.add_argument('--sprak', default='sv,en')
    a = p.parse_args(argv)
    krav_vag(a.ut, "--ut")
    for mal in (str(Path(a.ut).with_suffix('.md')), str(Path(a.ut).parent / (Path(a.ut).stem + '-bilder'))):  # de faktiska skrivmålen (omgång sex, F1)
        krav_vag(mal, "utfilen")
    vid = video_id(a.url)
    adress = 'https://www.youtube.com/watch?v=' + vid if vid else a.url
    meta, fel = metadata(adress)
    if meta is None:
        print('metadata: ' + fel, file=sys.stderr)
        return 2
    try:
        for spec in a.avsnitt:
            avsnitt_tider(spec, meta.get('duration') or 0)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    ut = Path(a.ut)
    # Utdata får aldrig hamna i repot: en styrd session ska inte kunna skriva över kod som sedan pushas.
    if ut.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
        print('--ut får inte ligga i repot; använd /tmp/kirurg/…', file=sys.stderr)
        return 2
    ut.parent.mkdir(parents=True, exist_ok=True)
    sprak_lista = [s.strip() for s in a.sprak.split(',') if s.strip()]
    rader, sprak, tfel = transkript(vid, sprak_lista) if vid else (None, None, 'inte YouTube')
    if not rader:
        r2, s2, f2 = undertexter(adress, sprak_lista)
        if r2:
            rader, sprak, tfel = r2, s2, None
        else:
            tfel = '%s; %s' % (tfel, f2)
    if a.bilder > 0 or a.avsnitt:
        rutor, bfel = bildrutor(adress, meta.get('duration') or 0, a.bilder, meta.get('chapters') if a.bilder > 0 else [], ut.parent / (ut.stem + '-bilder'), a.avsnitt)
    else:
        rutor, bfel = [], 'avstängt (--bilder 0)'
    beskr = meta.get('description') or ''
    lankar = sorted(set(LANK.findall(beskr)))
    md = ['# %s' % meta.get('title'), '',
          '- Kanal: %s' % (meta.get('channel') or meta.get('uploader')),
          '- Adress: %s' % (meta.get('webpage_url') or adress),
          '- Källa: %s' % (meta.get('extractor_key') or '?'),
          '- Avsnitt med täta bildrutor: %s' % (', '.join(a.avsnitt) or 'inga'),
          '- Publicerad: %s' % (meta.get('upload_date') or '?'),
          '- Längd: %s' % tid(meta.get('duration') or 0),
          '- Visningar: %s' % meta.get('view_count'),
          '- Transkript: %s' % (sprak or 'saknas (%s)' % tfel),
          '- Bildrutor: %s' % ('%d st i %s (läs varje bild med Read; tidsstämpeln står i filnamnet)' % (len(rutor), ut.stem + '-bilder/') if rutor else 'inga (%s)' % bfel), '']
    md += ['## Länkar i beskrivningen (läs dessa först: ett repo slår alltid en skärmdump)', '']
    md += ['- ' + l for l in lankar] or ['- inga']
    if meta.get('chapters'):
        md += ['', '## Kapitel', ''] + ['- %s %s' % (tid(c.get('start_time', 0)), c.get('title')) for c in meta['chapters']]
    md += ['', '## Beskrivning', '', beskr.strip() or '(tom)', '',
           '## Tidslinje: tal och bild', '',
           '`[MM:SS] text` är tal ur transkriptet. `[BILD MM:SS] sökväg` är en bildruta från samma tidpunkt: läs den och '
           'koppla ihop vad som sägs med vad som visas. Återge aldrig kod eller text ur en bild som du inte kan läsa säkert.', '']
    handelser = []
    if rader:
        stycke, start = [], 0
        for t, text in rader:
            if not stycke:
                start = t
            stycke.append(text.replace('\n', ' '))
            if t - start >= 30:
                handelser.append((start, 0, '[%s] %s' % (tid(start), ' '.join(stycke))))
                stycke = []
        if stycke:
            handelser.append((start, 0, '[%s] %s' % (tid(start), ' '.join(stycke))))
    for t, fil in rutor:
        handelser.append((t, 1, '[BILD %s] %s' % (tid(t), fil)))
    md += [h[2] for h in sorted(handelser)] or ['(varken transkript eller bildrutor)']
    ut.write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'ut': str(ut), 'titel': meta.get('title'), 'transkript': bool(rader), 'bildrutor': len(rutor),
                      'bildmapp': str(ut.parent / (ut.stem + '-bilder')) if rutor else None, 'lankar': len(lankar)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
