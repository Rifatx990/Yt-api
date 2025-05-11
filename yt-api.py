from flask import Flask, request, render_template, send_file, jsonify
import os
import yt_dlp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    media_type = request.args.get('type', 'audio')

    if not url:
        return jsonify({"error": "URL is missing."})

    try:
        ydl_opts = {
            'outtmpl': 'downloaded.%(ext)s',
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
            ydl_opts.update({'format': 'best'})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Change extension if audio
        if media_type == 'audio':
            filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)

    except yt_dlp.utils.DownloadError as e:
        return jsonify({
            "details": str(e),
            "error": "ভিডিওটি পাওয়া যায়নি বা ডাউনলোড সম্ভব নয়।"
        })

if __name__ == '__main__':
    app.run(debug=True)
