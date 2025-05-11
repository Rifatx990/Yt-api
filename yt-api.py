from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
COOKIES_FILE = "cookies.txt"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route("/download", methods=["GET"])
def download_video():
    url = request.args.get("url")
    media_type = request.args.get("type", "audio")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    filename = str(uuid.uuid4())
    output_path = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    if media_type == "audio":
        ytdlp_command = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--cookies", COOKIES_FILE,
            "--user-agent", USER_AGENT,
            "-o", output_path,
            url
        ]
    else:
        ytdlp_command = [
            "yt-dlp",
            "--cookies", COOKIES_FILE,
            "--user-agent", USER_AGENT,
            "-f", "best[filesize<83M]",
            "-o", output_path,
            url
        ]

    try:
        subprocess.run(ytdlp_command, check=True)
        downloaded_files = os.listdir(DOWNLOAD_DIR)
        target_file = next((f for f in downloaded_files if f.startswith(filename)), None)
        if target_file:
            file_path = os.path.join(DOWNLOAD_DIR, target_file)
            response = send_file(file_path, as_attachment=True)
            os.remove(file_path)
            return response
        else:
            return jsonify({"error": "ফাইল ডাউনলোড হয়নি"}), 500

    except subprocess.CalledProcessError as e:
        return jsonify({"details": str(e), "error": "ভিডিওটি পাওয়া যায়নি বা অ্যাক্সেস করা যায় না।"}), 500
    except Exception as ex:
        return jsonify({"error": f"অপ্রত্যাশিত ত্রুটি: {str(ex)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
