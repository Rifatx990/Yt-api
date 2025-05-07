import os
import subprocess
import uuid
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

# Configuration
DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return jsonify({
        "endpoints": {
            "/download/video?url=": "Download YouTube video",
            "/download/audio?url=": "Download YouTube audio"
        },
        "status": "running"
    })

@app.route('/download/video', methods=['GET'])
def download_video():
    url = request.args.get('url')
    return download_media(url, 'bestvideo+bestaudio')

@app.route('/download/audio', methods=['GET'])
def download_audio():
    url = request.args.get('url')
    return download_media(url, 'bestaudio')

def download_media(url, format_code):
    if not url:
        return jsonify({'error': 'Missing URL parameter'}), 400

    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

    command = [
        'yt-dlp',
        '--cookies', COOKIES_FILE,
        '-f', format_code,
        '-o', output_template,
        url
    ]

    try:
        subprocess.run(command, check=True)

        # Find downloaded file
        downloaded_file = next(
            (os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)
             if f.startswith(unique_id)), None
        )

        if downloaded_file and os.path.isfile(downloaded_file):
            return send_file(downloaded_file, as_attachment=True)
        else:
            return jsonify({'error': 'Download failed or file not found'}), 500

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Download error: {str(e)}'}), 500

if __name__ == '__main__':
    # Install pip and dependencies if missing
    try:
        import pip
    except ImportError:
        os.system("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py")

    # Run Flask app
    app.run(host='0.0.0.0', port=5000)
