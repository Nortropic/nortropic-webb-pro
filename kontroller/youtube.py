#!/usr/bin/env python3
"""youtube.py — en YouTube-video som markdown för kirurgen: metadata, beskrivning (med länkar först) och transkript
med tidsstämplar. Ingen nedladdning av själva videon. Körs lokalt (YouTube blockerar många moln-IP:n).

    .venv/bin/python kontroller/youtube.py URL --ut FIL.md [--sprak sv,en]

Bildrutor ingår inte: de kräver ffmpeg och behövs bara när kod eller gränssnitt bara syns i bild och inte finns i ett
länkat repo (se manualen i Nortropic/verkstadsgolvet, content/youtube-research/MANUAL-VIDEO-DESTILLERING.md).
Exit 0 = filen skriven (transkriptet kan saknas, då står det i filen); 2 = fel i anropet eller metadata gick inte att hämta.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

LANK = re.compile(r'https?://\S+')


def video_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else (url if re.fullmatch(r'[A-Za-z0-9_-]{11}', url) else None)


def metadata(url):
    ytdlp = shutil.which('yt-dlp', path=str(Path(sys.executable).parent)) or shutil.which('yt-dlp')
    if not ytdlp:
        return None, 'yt-dlp saknas (.venv/bin/python -m pip install yt-dlp)'
    p = subprocess.run([ytdlp, '--skip-download', '--dump-single-json', '--no-warnings', url], capture_output=True, text=True, timeout=120)
    if p.returncode:
        return None, (p.stderr or p.stdout).strip()[-500:]
    return json.loads(p.stdout), None


def transkript(vid, sprak):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, None, 'youtube-transcript-api saknas'
    try:
        api = YouTubeTranscriptApi()
        lista = api.list(vid)
        valt = None
        for finder in (lista.find_manually_created_transcript, lista.find_generated_transcript, lista.find_transcript):
            try:
                valt = finder(sprak)
                break
            except Exception:
                continue
        if valt is None:
            valt = next(iter(lista))
        data = valt.fetch()
        return [(s.start, s.text) for s in data], '%s (%s)' % (valt.language, 'autogenererat' if valt.is_generated else 'manuellt'), None
    except Exception as e:
        return None, None, '%s: %s' % (type(e).__name__, str(e).splitlines()[0][:300])


def tid(s):
    s = int(s)
    return '%d:%02d:%02d' % (s // 3600, s % 3600 // 60, s % 60) if s >= 3600 else '%02d:%02d' % (s // 60, s % 60)


def main(argv=None):
    p = argparse.ArgumentParser(prog='youtube', description=__doc__.split('\n\n')[0])
    p.add_argument('url')
    p.add_argument('--ut', required=True)
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
    rader, sprak, tfel = transkript(vid, [s.strip() for s in a.sprak.split(',') if s.strip()])
    beskr = meta.get('description') or ''
    lankar = sorted(set(LANK.findall(beskr)))
    md = ['# %s' % meta.get('title'), '',
          '- Kanal: %s' % (meta.get('channel') or meta.get('uploader')),
          '- Adress: https://www.youtube.com/watch?v=%s' % vid,
          '- Publicerad: %s' % (meta.get('upload_date') or '?'),
          '- Längd: %s' % tid(meta.get('duration') or 0),
          '- Visningar: %s' % meta.get('view_count'),
          '- Transkript: %s' % (sprak or 'saknas (%s)' % tfel), '']
    md += ['## Länkar i beskrivningen (läs dessa först: ett repo slår alltid en skärmdump)', '']
    md += ['- ' + l for l in lankar] or ['- inga']
    if meta.get('chapters'):
        md += ['', '## Kapitel', ''] + ['- %s %s' % (tid(c.get('start_time', 0)), c.get('title')) for c in meta['chapters']]
    md += ['', '## Beskrivning', '', beskr.strip() or '(tom)', '', '## Transkript', '']
    if rader:
        stycke, start = [], 0
        for t, text in rader:
            if not stycke:
                start = t
            stycke.append(text.replace('\n', ' '))
            if t - start >= 30:
                md.append('[%s] %s' % (tid(start), ' '.join(stycke)))
                stycke = []
        if stycke:
            md.append('[%s] %s' % (tid(start), ' '.join(stycke)))
    else:
        md.append('(inget transkript: %s)' % tfel)
    Path(a.ut).parent.mkdir(parents=True, exist_ok=True)
    Path(a.ut).write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'ut': a.ut, 'titel': meta.get('title'), 'transkript': bool(rader), 'lankar': len(lankar)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
