import os
import uuid
import time
from flask import Flask, send_file, request, abort, jsonify
import yt_dlp
from urllib.parse import unquote, urlparse
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def check_cookies():
    """Check if cookies.txt exists"""
    if not os.path.exists('cookies.txt'):
        app.logger.warning("No cookies.txt found - age-restricted content might not work")

def cleanup_old_files():
    """Clean up files older than 3 minutes"""
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
                    app.logger.info(f"Cleaned up: {dir_path}")
                except Exception as e:
                    app.logger.error(f"Cleanup error: {str(e)}")

# Run cleanup every minute
scheduler.add_job(cleanup_old_files, 'interval', minutes=1)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoints": {
            "/download": "Download YouTube audio/video",
            "/health": "Health check"
        },
        "params": {
            "url": "YouTube URL",
            "type": "[audio|video] (default: audio)",
            "quality": "Video quality (default: best)"
        }
    })

@app.route('/download', methods=['GET'])
def download_media():
    check_cookies()
    
    url = request.args.get('url')
    media_type = request.args.get('type', 'audio').lower()
    quality = request.args.get('quality', 'best')

    if not url:
        abort(400, description="Missing 'url' parameter")
    
    # Decode and sanitize URL
    url = unquote(url.strip())
    parsed = urlparse(url)
    if not parsed.netloc or not ('youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc):
        abort(400, description="Invalid YouTube URL")

    # Clean URL (remove query params like ?si=...)
    clean_url = f"https://{parsed.netloc}{parsed.path}"

    # Prepare temp dir
    temp_dir = os.path.join('temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'outtmpl': output_template,
        'restrictfilenames': True,
        'quiet': True,
        'no_warnings': True,
    }

    if media_type == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best' if quality != 'best' else 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            filename = ydl.prepare_filename(info)
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

            if not os.path.exists(filename):
                abort(500, description="Failed to download media")

            response = send_file(filename, as_attachment=True)

            # Optional: delete file after serving
            @response.call_on_close
            def remove_temp_files():
                try:
                    for root, dirs, files in os.walk(temp_dir, topdown=False):
                        for f in files:
                            os.remove(os.path.join(root, f))
                        for d in dirs:
                            os.rmdir(os.path.join(root, d))
                    os.rmdir(temp_dir)
                except Exception as e:
                    app.logger.warning(f"Cleanup after send failed: {str(e)}")

            return response

    except Exception as e:
        abort(500, description=f"Download error: {str(e)}")

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    check_cookies()
    app.run(host='0.0.0.0', port=5000)
