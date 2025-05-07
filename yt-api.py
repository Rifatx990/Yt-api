from flask import Flask, request, send_file, jsonify
import os
import subprocess
import uuid

app = Flask(__name__)

@app.route('/download', methods=['GET'])
def download_media():
    url = request.args.get('url')
    media_type = request.args.get('type', 'video')  # default to video

    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    file_id = str(uuid.uuid4())
    cookies_path = 'cookies.txt'

    if media_type == 'audio':
        ytdlp_format = 'bestaudio[filesize<26M]'
        ext = 'm4a'
    else:
        ytdlp_format = 'best[filesize<83M]'
        ext = 'mp4'

    filename = f'{file_id}.{ext}'

    command = [
        'yt-dlp',
        '-f', ytdlp_format,
        '--cookies', cookies_path,
        '-o', filename,
        url
    ]

    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error downloading media: {e.output.decode()}'})

    try:
        return send_file(filename, as_attachment=True)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
