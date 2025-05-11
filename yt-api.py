from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download_media():
    url = request.args.get("url")
    media_type = request.args.get("type", "audio")

    if not url:
        return jsonify({"error": "URL প্রদান করুন"}), 400

    filename = f"{uuid.uuid4()}.%(ext)s"
    output_path = os.path.join("downloads", filename)

    ydl_opts = {
        'format': 'bestaudio/best' if media_type == "audio" else 'best',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'cookiefile': "cookies.txt",  # যদি কুকিজ দরকার হয়
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if media_type == "audio" else [],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if media_type == "audio":
                file_path = file_path.rsplit('.', 1)[0] + ".mp3"
    except yt_dlp.utils.DownloadError as e:
        return jsonify({
            "error": "ভিডিওটি পাওয়া যায়নি বা অ্যাক্সেস করা যাচ্ছে না।",
            "details": str(e)
        }), 404

    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True)
