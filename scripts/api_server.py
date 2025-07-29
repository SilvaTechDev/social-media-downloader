import os
import re
import time
import threading
import atexit
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from yt_dlp import YoutubeDL

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', '/tmp/downloads'))
DOWNLOAD_DIR.mkdir(exist_ok=True, parents=True)

# Cleanup on exit
@atexit.register
def cleanup():
    """Remove all downloads when server stops"""
    for item in DOWNLOAD_DIR.glob('*'):
        try:
            if item.is_file():
                item.unlink()
        except Exception as e:
            print(f"Error deleting {item}: {e}")

download_progress = {}

def sanitize_filename(filename):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_media(url, media_type, download_id):
    try:
        options = {
            'outtmpl': str(DOWNLOAD_DIR / f'{download_id}_%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: update_progress(d, download_id)],
            'quiet': True,
            'nooverwrites': True,
            'continuedl': True,
            'nopart': True,  # Critical for Render's ephemeral storage
            'no_cache_dir': True,
        }

        if media_type == 'audio':
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }]
            })
        elif media_type == 'video':
            options['format'] = 'bestvideo+bestaudio/best'
        elif media_type == 'image':
            options['format'] = 'best[ext=jpg]/best'

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return sanitize_filename(os.path.basename(filename))
            
    except Exception as e:
        print(f"Download error for {url}: {str(e)}")
        return None

def update_progress(data, download_id):
    if data['status'] == 'downloading':
        progress = data.get('_percent_str', '0%').replace('%', '')
        download_progress[download_id] = float(progress) if progress.replace('.', '').isdigit() else 0

@app.route('/download', methods=['POST'])
def handle_download():
    data = request.json
    if not data or 'url' not in data or 'type' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    download_id = str(time.time_ns())
    threading.Thread(
        target=process_download,
        args=(data['url'], data['type'], download_id)
    ).start()
    
    return jsonify({
        'download_id': download_id,
        'status': 'started'
    })

def process_download(url, media_type, download_id):
    filename = download_media(url, media_type, download_id)
    if filename:
        download_progress[download_id] = 100
    else:
        download_progress[download_id] = -1  # Error state

@app.route('/progress/<download_id>')
def check_progress(download_id):
    progress = download_progress.get(download_id, 0)
    files = list(DOWNLOAD_DIR.glob(f'{download_id}_*'))
    return jsonify({
        'progress': progress,
        'completed': progress >= 100,
        'error': progress == -1,
        'filename': files[0].name if files else None
    })

@app.route('/file/<filename>')
def serve_file(filename):
    filepath = DOWNLOAD_DIR / filename
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
        
    if not filepath.is_file():
        return jsonify({'error': 'Invalid file'}), 400
        
    return send_file(filepath, as_attachment=True)

@app.route('/healthcheck')
def healthcheck():
    return jsonify({
        'status': 'healthy',
        'download_dir': str(DOWNLOAD_DIR),
        'free_space': f"{shutil.disk_usage(DOWNLOAD_DIR).free / (1024**2):.2f} MB"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
