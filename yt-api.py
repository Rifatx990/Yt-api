import os
from flask import Flask, request, send_file, jsonify
import yt_dlp
import uuid

app = Flask(__name__)

def download_media(url, media_type):
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.%(ext)s"
    outtmpl = os.path.join("downloads", filename)

    # Path to the cookies.txt file
    cookies_path = os.path.join(os.getcwd(), 'cookies.txt')

    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': True,
        'noplaylist': True,
        'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',
        'postprocessors': [],
        'cookiefile': cookies_path,  # Add cookies.txt file for authentication
    }

    if media_type == 'audio':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = 'mp3' if media_type == 'audio' else info['ext']
        file_path = os.path.join("downloads", f"{unique_id}.{ext}")
        return file_path

@app.route('/')
def home():
    return jsonify({"message": "YouTube Downloader API is live."})

@app.route('/download/<media_type>')
def download(media_type):
    url = request.args.get('url')
    if not url or media_type not in ['video', 'audio']:
        return jsonify({'error': 'Missing URL or invalid media type (video/audio)'}), 400

    try:
        file_path = download_media(url, media_type)
        response = send_file(file_path, as_attachment=True)
        os.remove(file_path)
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
