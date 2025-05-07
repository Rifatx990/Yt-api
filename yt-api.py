# app.py
import os
import uuid
from flask import Flask, send_file, request, abort
import yt_dlp

app = Flask(__name__)

def cleanup_temp(temp_dir):
    """Clean up temporary directory and its contents"""
    try:
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(temp_dir)
    except Exception as e:
        app.logger.error(f"Error cleaning up temp directory: {str(e)}")

@app.route('/download', methods=['GET'])
def download_media():
    # Get request parameters
    url = request.args.get('url')
    if not url:
        abort(400, description="Missing required parameter: url")

    media_type = request.args.get('type', 'audio').lower()
    quality = request.args.get('quality', 'best')

    # Create temporary directory
    temp_dir = os.path.join(os.getcwd(), 'temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)

    # Configure yt-dlp options
    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
        'quiet': True,
        'no_warnings': True,
    }

    # Set format based on media type
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
        ydl_opts['format'] = f'bestvideo[height<={quality}]+bestaudio/best' if quality != 'best' else 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get filename
            info = ydl.extract_info(url, download=False)
            filename = ydl.prepare_filename(info)
            
            # Check if we need to change extension for audio
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Download the file
            ydl.download([url])
            
            # Verify file exists
            if not os.path.exists(filename):
                abort(500, description="Failed to download file")

            # Setup cleanup after response
            @request.after_this_request
            def remove_file(response):
                try:
                    os.remove(filename)
                    cleanup_temp(temp_dir)
                except Exception as e:
                    app.logger.error(f"Error cleaning up files: {str(e)}")
                return response

            return send_file(filename, as_attachment=True)

    except yt_dlp.utils.DownloadError as e:
        abort(500, description=f"Download error: {str(e)}")
    except Exception as e:
        abort(500, description=f"Server error: {str(e)}")
    finally:
        cleanup_temp(temp_dir)

if __name__ == '__main__':
    os.makedirs('temp', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error downloading media: {e.output.decode()}'})

    try:
        return send_file(filename, as_attachment=True)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
