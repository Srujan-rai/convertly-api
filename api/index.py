from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import subprocess
from werkzeug.utils import secure_filename
from pypdf import PdfReader
from docx import Document

app = Flask(__name__)

# ✅ Allow CORS for both localhost (development) & Vercel frontend (production)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://convertly-lovat.vercel.app"]}})

UPLOAD_FOLDER = "/tmp/uploads"
DOWNLOAD_FOLDER = "/tmp/downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ✅ Function to Download YouTube Videos
def download_youtube_video(url):
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

        return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        return None

# ✅ Function to Download Instagram Videos
def download_instagram_video(url):
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

        return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"Error downloading Instagram video: {e}")
        return None

# ✅ Route for YouTube Download
@app.route("/youtube", methods=["POST"])
def youtube_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_youtube_video(url)

    if filename:
        response = send_file(filename, as_attachment=True)
        os.remove(filename)  # ✅ Cleanup immediately after sending
        return response

    return jsonify({"error": "YouTube download failed"}), 500

# ✅ Route for Instagram Download
@app.route("/instagram", methods=["POST"])
def instagram_download():
    data = request.get_json()
    url = data.get("link")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    filename = download_instagram_video(url)

    if filename:
        response = send_file(filename, as_attachment=True)
        os.remove(filename)  # ✅ Cleanup immediately after sending
        return response

    return jsonify({"error": "Instagram download failed"}), 500

# ✅ Function to Convert PDF to Word
def pdf_to_word(pdf_path):
    doc = Document()
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        doc.add_paragraph(page.extract_text())
    word_path = pdf_path.replace(".pdf", ".docx")
    doc.save(word_path)
    return word_path

# ✅ Function to Convert Word to PDF
def word_to_pdf(docx_path):
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
    print("🔹 Request received")
    print("🔹 Files:", request.files)
    print("🔹 Form Data:", request.form)

    

    file = request.files["files"]
    conversion_type = request.form.get("conversionType")

    if not file or not conversion_type:
        return jsonify({"error": "Missing file or conversion type"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    if conversion_type == "pdf-to-doc":
        if not filename.endswith(".pdf"):
            os.remove(input_path)  # ✅ Cleanup
            return jsonify({"error": "Invalid file format. Expected PDF."}), 400
        output_path = pdf_to_word(input_path)
    elif conversion_type == "doc-to-pdf":
        if not filename.endswith(".docx"):
            os.remove(input_path)  # ✅ Cleanup
            return jsonify({"error": "Invalid file format. Expected DOCX."}), 400
        output_path = word_to_pdf(input_path)
        if output_path is None:
            os.remove(input_path)  # ✅ Cleanup
            return jsonify({"error": "Word to PDF conversion failed"}), 500
    else:
        os.remove(input_path)  # ✅ Cleanup
        return jsonify({"error": "Invalid conversion type"}), 400

    if not os.path.exists(output_path):
        os.remove(input_path)  # ✅ Cleanup
        return jsonify({"error": "Conversion failed"}), 500

    response = send_file(output_path, as_attachment=True)
    os.remove(input_path)  # ✅ Remove input file immediately
    os.remove(output_path)  # ✅ Remove converted file immediately
    return response



if __name__ == "__main__":
    app.run(debug=True, port=5000)
