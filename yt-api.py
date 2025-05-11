import os
import uuid
import time
from flask import Flask, send_file, request, abort, jsonify
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

def check_cookies():
    if not os.path.exists('cookies.txt'):
        app.logger.warning("cookies.txt not found – age-restricted content might fail")

def cleanup_old_files():
    now = time.time()
    temp_root = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(temp_root):
        return

    for dir_name in os.listdir(temp_root):
        dir_path = os.path.join(temp_root, dir_name)
        if os.path.isdir(dir_path):
            dir_time = os.path.getmtime(dir_path)
            if (now - dir_time) > 180:
                try:
                    for root, dirs, files in os.walk(dir_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(dir_path)
                    app.logger.info(f"Deleted old temp dir: {dir_path}")
                except Exception as e:
                    app.logger.error(f"Error deleting {dir_path}: {str(e)}")

scheduler.add_job(cleanup_old_files, 'interval', minutes=1)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "usage": "/download?url=YOUTUBE_URL&type=audio|video"
    })

@app.route('/download', methods=['GET'])
def download_media():
    check_cookies()

    url = request.args.get('url')
    if not url:
        abort(400, description="Missing 'url' parameter")

    media_type = request.args.get('type', 'audio').lower()
    quality = request.args.get('quality', 'best')

    temp_dir = os.path.join('temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True
    }

    if media_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best' if quality != 'best' else 'best'

    try:
        # Delay before download (3 seconds)
        time.sleep(3)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            ydl.download([url])

            if not os.path.exists(filename):
                abort(500, description="Download failed. File not found.")

            return send_file(filename, as_attachment=True)

    except Exception as e:
        abort(500, description=f"Download error: {str(e)}")

@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": time.time()})

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    check_cookies()
    app.run(host='0.0.0.0', port=5000)
