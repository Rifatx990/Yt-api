from flask import Flask, request, jsonify
import os
import subprocess
import sys
import yt_dlp
from pathlib import Path
import time

# Flask app setup
app = Flask(__name__)

# Ensure the cookies directory exists
cookie_dir = Path(__file__).parent / 'cookies'
cookie_dir.mkdir(parents=True, exist_ok=True)
cookies_file_path = cookie_dir / 'cookies.txt'

# Function to ensure dependencies are installed and up-to-date
def ensure_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade dependencies: {e}")

# Function to download media (video/audio)
def download_media(url):
    try:
        if not os.path.exists(cookies_file_path):
            return {"error": "Cookies file not found, please provide a valid cookies.txt file."}

        output_dir = Path(__file__).parent / 'downloads'
        output_dir.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            'cookies': str(cookies_file_path),
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
            'quiet': False,
            'writethumbnail': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        video_file = None
        audio_file = None

        for file in output_dir.iterdir():
            if file.suffix in ['.mp4', '.webm']:
                video_file = file
            elif file.suffix in ['.mp3', '.m4a', '.aac']:
                audio_file = file

        time.sleep(180)  # Wait for 3 minutes before deleting

        # Delete downloaded files after 3 minutes
        if video_file and video_file.exists():
            os.remove(video_file)
        if audio_file and audio_file.exists():
            os.remove(audio_file)

        return {"status": "success", "video": str(video_file), "audio": str(audio_file)}

    except Exception as e:
        return {"error": str(e)}

# Flask route to handle download requests
@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    ensure_dependencies()
    result = download_media(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
