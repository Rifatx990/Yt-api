from flask import Flask, request, send_file, jsonify
import subprocess
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return 'YouTube Downloader is running!'

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    download_type = request.args.get('type', 'audio')

    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")

    command = [
        'yt-dlp',
        '--no-warnings',
        '--cookies', 'cookies.txt',
        '-o', output_template
    ]

    if download_type == 'audio':
        command += ['-x', '--audio-format', 'mp3']
    else:
        command += ['-f', 'mp4']

    command.append(url)

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return jsonify({'error': 'ডাউনলোড করতে সমস্যা হয়েছে', 'details': result.stderr.strip()}), 500

        for filename in os.listdir(DOWNLOAD_FOLDER):
            if file_id in filename:
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                response = send_file(filepath, as_attachment=True)
                os.remove(filepath)
                return response

        return jsonify({'error': 'ফাইল পাওয়া যায়নি'}), 404

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'ডাউনলোড করতে অনেক সময় লেগে গেছে'}), 504

    except Exception as e:
        return jsonify({'error': 'সার্ভারে একটি ত্রুটি ঘটেছে', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
