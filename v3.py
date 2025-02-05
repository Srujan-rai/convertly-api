from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_youtube_video(url):
    try:
        options = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',  # Ensure MP4 output
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit('.', 1)[0] + ".mp4"  # Ensure correct file extension

        return filename
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route("/youtube", methods=["POST"])
def youtube_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_youtube_video(url)
    
    if filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True)

    return jsonify({"error": "Download failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
