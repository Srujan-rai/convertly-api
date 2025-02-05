from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document

app = Flask(__name__)
CORS(app)  # Enable CORS

DOWNLOAD_FOLDER = "downloads"
UPLOAD_FOLDER = "uploads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def download_video(url, platform):
    """Generic function to download video from YouTube or Instagram"""
    try:
        options = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit('.', 1)[0] + ".mp4"

        return filename
    except Exception as e:
        print(f"Error downloading from {platform}: {e}")
        return None

@app.route("/youtube", methods=["POST"])
def youtube_download():
    data = request.get_json()
    url = data.get("link")
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_video(url, "YouTube")
    
    if filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True)

    return jsonify({"error": "YouTube download failed"}), 500

@app.route("/instagram", methods=["POST"])
def instagram_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_video(url, "Instagram")

    if filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True)

    return jsonify({"error": "Instagram download failed"}), 500

def pdf_to_word(pdf_path):
    """Convert PDF to Word document."""
    doc = Document()
    pdf_reader = PdfReader(pdf_path)

    for page in pdf_reader.pages:
        doc.add_paragraph(page.extract_text())

    word_filename = pdf_path.rsplit(".", 1)[0] + ".docx"
    doc.save(word_filename)
    return word_filename

def word_to_pdf(docx_path):
    """Convert Word document to PDF (returns same file since python-docx doesn't support PDF conversion)."""
    return docx_path  # For actual conversion, you need LibreOffice or another tool.

@app.route("/convert", methods=["POST"])
def convert_document():
    """Handles PDF to Word and Word to PDF conversions."""
    if "files" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    print("Request files: ", request.files)
    file = request.files["files"]
    conversion_type = request.form.get("conversionType")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    if conversion_type == "pdf-to-doc":
        converted_file = pdf_to_word(file_path)
    elif conversion_type == "doc-to-pdf":
        converted_file = word_to_pdf(file_path)
    else:
        return jsonify({"error": "Invalid conversion type"}), 400

    if os.path.exists(converted_file):
        return send_file(converted_file, as_attachment=True)

    return jsonify({"error": "Conversion failed"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
