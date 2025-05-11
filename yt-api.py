from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_with_yt_dlp(url, download_type):
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
        'quiet': True,
        'format': 'bestaudio/best' if download_type == 'audio' else 'best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if download_type == 'audio' else [],
        'cookiefile': 'cookies.txt'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            return filename, info
        except yt_dlp.utils.DownloadError as e:
            return None, str(e)

@app.route('/')
def index():
    return 'YouTube Downloader API is Running.'

@app.route('/download', methods=['GET'])
def download_media():
    url = request.args.get('url')
    download_type = request.args.get('type', 'audio')

    if not url:
        return jsonify({'error': 'Please provide a valid URL.'}), 400

    filename, info = download_with_yt_dlp(url, download_type)
    if filename:
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({
            'details': info,
            'error': 'ভিডিওটি পাওয়া যায়নি বা অ্যাক্সেস করা যাচ্ছে না।'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
