import yt_dlp
import sys
import os

def download_media(url, media_type):
    options = {
        'outtmpl': os.path.join('downloads', '%(title)s.%(ext)s'),
        'quiet': True,
    }

    if media_type == 'audio':
        options['format'] = 'bestaudio/best'
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    elif media_type == 'video':
        options['format'] = 'bestvideo+bestaudio/best'
    elif media_type == 'image':
        options['format'] = 'best[ext=jpg]/best'

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        return str(e)