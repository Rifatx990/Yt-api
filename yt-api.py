from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'
COOKIES_FILE = 'cookies.txt'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    format_code = data.get('format', 'best')  # e.g., 'bestaudio', 'bestvideo', 'best'

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    filename = f"{uuid.uuid4()}.%(ext)s"
    output_path = os.path.join(DOWNLOAD_DIR, filename)

    command = [
        'yt-dlp',
        '--cookies', COOKIES_FILE,
        '-f', format_code,
        '-o', output_path,
        url
    ]

    try:
        subprocess.run(command, check=True)
        # Find actual downloaded file
        downloaded_file = next(
            (os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)
             if f.startswith(filename.split('.')[0])), None
        )
        if downloaded_file:
            return send_file(downloaded_file, as_attachment=True)
        else:
            return jsonify({'error': 'Download failed'}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return "YouTube Downloader API is running!"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
