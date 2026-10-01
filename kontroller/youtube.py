#!/usr/bin/env python3
"""youtube.py — en YouTube-video som markdown för kirurgen: metadata, länkar ur beskrivningen, och en tidslinje där
transkriptet och bildrutor ur videon står flätade vid samma tidpunkt. Så ser kirurgen både vad som sägs och vad som
visas. Körs lokalt (YouTube blockerar många moln-IP:n).

    .venv/bin/python kontroller/youtube.py 'URL' --ut FIL.md [--bilder 40] [--sprak sv,en]

Bildrutor: videon hämtas utan ljud i högst 720p, N bildrutor tas jämnt över videon plus en vid varje kapitelstart,
skalas till 1280 px bredd och sparas som FIL-bilder/bild-MMmSSs.jpg. Videofilen raderas efteråt. --bilder 0 hoppar
över bildrutorna (bara transkript). ffmpeg kommer ur paketet imageio-ffmpeg i repots .venv.
Exit 0 = filen skriven (transkript eller bildrutor kan saknas, då står det i filen); 2 = fel i anropet eller metadata.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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


def bildrutor(vid, langd, antal, kapitel, mapp):
    """Hämtar videon utan ljud (≤ 720p) och tar ut bildrutor. Returnerar [(sekund, sökväg)] och ett eventuellt fel."""
    y, f = ytdlp(), ffmpeg()
    if not f:
        return [], 'ffmpeg saknas (.venv/bin/python -m pip install imageio-ffmpeg)'
    mapp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='nwp-yt-') as tmp:
        p = subprocess.run([y, '--no-playlist', '--no-warnings', '-f', 'bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]/b',
                            '--ffmpeg-location', f, '-o', str(Path(tmp) / 'video.%(ext)s'), 'https://www.youtube.com/watch?v=' + vid],
                           capture_output=True, text=True, timeout=900)
        filer = [x for x in Path(tmp).iterdir() if x.name.startswith('video.') and not x.name.endswith('.part')]
        if p.returncode or not filer:
            return [], 'nedladdningen misslyckades: ' + (p.stderr or p.stdout).strip()[-300:]
        video = filer[0]
        ut = []
        for t in tidpunkter(langd, antal, kapitel):
            namn = mapp / ('bild-%02dm%02ds.jpg' % (int(t) // 60, int(t) % 60))
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
    p.add_argument('--sprak', default='sv,en')
    a = p.parse_args(argv)
    vid = video_id(a.url)
    if not vid:
        print('kunde inte läsa video-id ur adressen', file=sys.stderr)
        return 2
    meta, fel = metadata('https://www.youtube.com/watch?v=' + vid)
    if meta is None:
        print('metadata: ' + fel, file=sys.stderr)
        return 2
    ut = Path(a.ut)
    ut.parent.mkdir(parents=True, exist_ok=True)
    rader, sprak, tfel = transkript(vid, [s.strip() for s in a.sprak.split(',') if s.strip()])
    rutor, bfel = bildrutor(vid, meta.get('duration') or 0, a.bilder, meta.get('chapters'), ut.parent / (ut.stem + '-bilder')) if a.bilder > 0 else ([], 'avstängt (--bilder 0)')
    beskr = meta.get('description') or ''
    lankar = sorted(set(LANK.findall(beskr)))
    md = ['# %s' % meta.get('title'), '',
          '- Kanal: %s' % (meta.get('channel') or meta.get('uploader')),
          '- Adress: https://www.youtube.com/watch?v=%s' % vid,
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
