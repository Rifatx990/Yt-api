import os
import uuid
import time
from flask import Flask, send_file, request, abort, jsonify
import yt_dlp
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
            if (now - dir_time) > 180:  # 3 minutes
                try:
                    for root, dirs, files in os.walk(dir_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(dir_path)
                    app.logger.info(f"Cleaned up old directory: {dir_path}")
                except Exception as e:
                    app.logger.error(f"Error cleaning {dir_path}: {str(e)}")

# Schedule cleanup job every minute
scheduler.add_job(cleanup_old_files, 'interval', minutes=1)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "endpoints": {
            "/download": "Download YouTube media",
            "/health": "Service health check"
        },
        "parameters": {
            "url": "YouTube URL (required)",
            "type": "[audio|video] (default: audio)",
            "quality": "Video quality (default: best)"
        }
    })

@app.route('/download', methods=['GET'])
def download_media():
    check_cookies()
    
    url = request.args.get('url')
    if not url:
        abort(400, description="Missing required parameter: url")

    media_type = request.args.get('type', 'audio').lower()
    quality = request.args.get('quality', 'best')

    temp_dir = os.path.join(os.getcwd(), 'temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
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
            }],
        })
    else:
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best' if quality != 'best' else 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            ydl.download([url])
            
            if not os.path.exists(filename):
                abort(500, description="Failed to download file")

            return send_file(filename, as_attachment=True)

    except yt_dlp.utils.DownloadError as e:
        app.logger.error(f"Download error for {url}: {str(e)}")
        return jsonify({
            "error": "ভিডিওটি পাওয়া যায়নি বা অ্যাক্সেস করা যাচ্ছে না।",
            "details": str(e)
        }), 404

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "error": "অন্যান্য ত্রুটি ঘটেছে, অনুগ্রহ করে আবার চেষ্টা করুন।",
            "details": str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "temp_files": len(os.listdir('temp')) if os.path.exists('temp') else 0
    })

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    check_cookies()
    app.run(host='0.0.0.0', port=5000)
