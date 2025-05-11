from flask import Flask, request, jsonify, send_file
import subprocess
import os
import re

app = Flask(__name__)

def clean_url(url):
    return re.sub(r'[\?&]si=[^&]+', '', url)

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    dl_type = request.args.get('type', 'audio')
    
    if not url:
        return jsonify({"error": "ভিডিও লিংক প্রদান করুন।"}), 400

    # Clean URL
    url = clean_url(url)

    output_file = "output.%(ext)s"
    command = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "-f", "bestaudio/best" if dl_type == "audio" else "best",
        "-o", output_file,
        url
    ]

    try:
        subprocess.run(command, check=True)
        
        # Find downloaded file
        for ext in ['mp3', 'm4a', 'webm', 'mp4']:
            filename = f"output.{ext}"
            if os.path.exists(filename):
                response = send_file(filename, as_attachment=True)
                os.remove(filename)
                return response

        return jsonify({"error": "ফাইল ডাউনলোড করা গেল না।"}), 500

    except subprocess.CalledProcessError as e:
        error_output = e.output.decode("utf-8") if e.output else str(e)
        return jsonify({
            "error": "ডাউনলোড করতে সমস্যা হয়েছে",
            "details": error_output
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
