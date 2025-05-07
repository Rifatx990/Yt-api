import os
from flask import Flask, request, send_file, jsonify
import yt_dlp
import uuid

app = Flask(__name__)

# Ensure that the downloads folder exists
os.makedirs("downloads", exist_ok=True)

# Function to download media (video or audio)
def download_media(url, media_type):
    unique_id = str(uuid.uuid4())
    filename = f"{unique_id}.%(ext)s"
    outtmpl = os.path.join("downloads", filename)

    # Path to the cookies.txt file (ensure it's in the same directory as this script)
    cookies_path = os.path.join(os.getcwd(), 'cookies.txt')

    # yt-dlp options for downloading the media
    ydl_opts = {
        'outtmpl': outtmpl,
        'quiet': False,  # Set to False for debugging, it can be True in production
        'noplaylist': True,
        'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',
        'cookiefile': cookies_path,  # Add cookies.txt for authentication
    }

    if media_type == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = 'mp3' if media_type == 'audio' else info['ext']
            file_path = os.path.join("downloads", f"{unique_id}.{ext}")
            return file_path
    except Exception as e:
        raise Exception(f"Error downloading media: {str(e)}")

# Route to handle the home page
@app.route('/')
def home():
    return jsonify({"message": "YouTube Downloader API is live."})

# Route to download the requested media (video or audio)
@app.route('/download/<media_type>', methods=['GET'])
def download(media_type):
    # Get URL from request arguments
    url = request.args.get('url')
    
    # Check if URL and media_type are provided
    if not url or media_type not in ['video', 'audio']:
        return jsonify({'error': 'Missing URL or invalid media type (video/audio)'}), 400

    try:
        # Download the media and get the file path
        file_path = download_media(url, media_type)

        # Send the file to the user as an attachment
        response = send_file(file_path, as_attachment=True)

        # After sending the file, remove it from the server
        os.remove(file_path)

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Main entry point to run the Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Run the app on all interfaces to allow remote access
    app.run(debug=True, host="0.0.0.0", port=port)
