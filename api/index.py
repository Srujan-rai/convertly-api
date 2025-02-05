from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import subprocess
import time
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document
from threading import Thread

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests

UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ✅ Auto-delete old files every 1 hour
def delete_old_files():
    while True:
        current_time = time.time()
        for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # Deletes files older than 1 hour
                        os.remove(file_path)
                        print(f"Deleted old file: {file_path}")
        time.sleep(3600)  # Runs every 1 hour

# Start cleanup thread
cleanup_thread = Thread(target=delete_old_files, daemon=True)
cleanup_thread.start()


# ✅ Function to Download YouTube/Instagram Videos
def download_video(url, platform):
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


# ✅ Route for YouTube Download
@app.route("/youtube", methods=["POST"])
def youtube_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_video(url, "YouTube")

    if filename and os.path.exists(filename):
        response = send_file(filename, as_attachment=True)
        os.remove(filename)  # ✅ Delete after sending
        return response

    return jsonify({"error": "YouTube download failed"}), 500


# ✅ Route for Instagram Download
@app.route("/instagram", methods=["POST"])
def instagram_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_video(url, "Instagram")

    if filename and os.path.exists(filename):
        response = send_file(filename, as_attachment=True)
        os.remove(filename)  # ✅ Delete after sending
        return response

    return jsonify({"error": "Instagram download failed"}), 500


# ✅ Function to Convert PDF to Word
def pdf_to_word(pdf_path):
    """Convert a PDF file to a Word document."""
    doc = Document()
    reader = PdfReader(pdf_path)

    for page in reader.pages:
        doc.add_paragraph(page.extract_text())

    word_path = pdf_path.replace(".pdf", ".docx")
    doc.save(word_path)
    return word_path


# ✅ Function to Convert Word to PDF (Linux Version Using LibreOffice)
def word_to_pdf(docx_path):
    """Convert a Word document to a PDF file using LibreOffice (Linux)"""
    pdf_path = docx_path.replace(".docx", ".pdf")

    try:
        subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", UPLOAD_FOLDER], check=True)
        return pdf_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting Word to PDF: {e}")
        return None


# ✅ Route to Handle File Conversion
@app.route("/convert", methods=["POST"])
def convert_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    conversion_type = request.form.get("conversion_type")

    if not file or not conversion_type:
        return jsonify({"error": "Missing file or conversion type"}), 400

    # Save the uploaded file
    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    # Convert based on requested type
    if conversion_type == "pdf-to-doc":
        if not filename.endswith(".pdf"):
            return jsonify({"error": "Invalid file format. Expected PDF."}), 400
        output_path = pdf_to_word(input_path)
    elif conversion_type == "doc-to-pdf":
        if not filename.endswith(".docx"):
            return jsonify({"error": "Invalid file format. Expected DOCX."}), 400
        output_path = word_to_pdf(input_path)
        if output_path is None:
            return jsonify({"error": "Word to PDF conversion failed"}), 500
    else:
        return jsonify({"error": "Invalid conversion type"}), 400

    if not os.path.exists(output_path):
        return jsonify({"error": "Conversion failed"}), 500

    response = send_file(output_path, as_attachment=True)

    os.remove(input_path)  # ✅ Remove the original uploaded file
    os.remove(output_path)  # ✅ Remove the converted file

    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
