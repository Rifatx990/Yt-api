import os
from flask import Flask, request, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/download/video', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    
    if not video_url:
        return "Error: No URL provided"
    
    # Prepare output path for the downloaded video file
    output_path = "downloads/video.mp4"  # Or any other format you want
    
    # Download video using yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,  # Specify output path
        'quiet': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Send the video file to the user
        return send_file(output_path, as_attachment=True, download_name="video.mp4")
    
    except Exception as e:
        return f"Error downloading video: {str(e)}"
    
    finally:
        # Delete the file after sending
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route('/download/audio', methods=['GET'])
def download_audio():
    video_url = request.args.get('url')
    
    if not video_url:
        return "Error: No URL provided"
    
    # Prepare output path for the downloaded audio file
    output_path = "downloads/audio.mp3"  # Or any other format you want
    
    # Download audio using yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,  # Specify output path
        'quiet': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Send the audio file to the user
        return send_file(output_path, as_attachment=True, download_name="audio.mp3")
    
    except Exception as e:
        return f"Error downloading audio: {str(e)}"
    
    finally:
        # Delete the file after sending
        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == '__main__':
    app.run(debug=True)
