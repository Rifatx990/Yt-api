import os
import uuid
import time
import traceback
from flask import Flask, send_file, request, abort, jsonify
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def check_cookies():
    """Warn if cookies.txt is missing"""
    if not os.path.exists('cookies.txt'):
        app.logger.warning("Warning: cookies.txt not found. Age-restricted videos may fail.")

def cleanup_old_files():
    """Clean up files older than 3 minutes"""
    now = time.time()
    temp_root = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(temp_root):
        return

    for dir_name in os.listdir(temp_root):
        dir_path = os.path.join(temp_root, dir_name)
        if os.path.isdir(dir_path):
            if (now - os.path.getmtime(dir_path)) > 180:
                try:
                    for root, dirs, files in os.walk(dir_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(dir_path)
                    app.logger.info(f"Deleted old temp folder: {dir_path}")
                except Exception as e:
                    app.logger.error(f"Cleanup error: {str(e)}")

# Schedule temp file cleanup every minute
scheduler.add_job(cleanup_old_files, 'interval', minutes=1)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "usage": "/download?url=<YouTube URL>&type=[audio|video]&quality=[best|360|720...]",
        "health": "/health"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "temp_files": len(os.listdir('temp')) if os.path.exists('temp') else 0
    })

@app.route('/download', methods=['GET'])
def download_media():
    check_cookies()

    url = request.args.get('url')
    media_type = request.args.get('type', 'audio').lower()
    quality = request.args.get('quality', 'best')

    if not url:
        abort(400, description="Missing required parameter: url")

    # Normalize youtu.be links
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={video_id}"

    # Delay to avoid throttling or race issues
    time.sleep(1)

    # Create unique temp directory
    temp_dir = os.path.join('temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    # yt-dlp options
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

            # For audio conversion
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

            ydl.download([url])

            if not os.path.exists(filename):
                abort(500, description="Download failed")

            # Send the file and delete after sending
            response = send_file(filename, as_attachment=True)

            @response.call_on_close
            def cleanup():
                try:
                    os.remove(filename)
                    os.rmdir(temp_dir)
                    app.logger.info(f"Cleaned downloaded: {filename}")
                except Exception as e:
                    app.logger.warning(f"Failed cleanup: {str(e)}")

            return response

    except Exception as e:
        traceback.print_exc()
        abort(500, description=f"Download error: {str(e)}")

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    check_cookies()
    app.run(host='0.0.0.0', port=5000)
