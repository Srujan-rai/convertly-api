from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import subprocess
from pypdf import PdfReader
from docx import Document
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ✅ YouTube/Instagram Video Downloader
def download_video(url: str, platform: str) -> Optional[str]:
    """Download a YouTube or Instagram video."""
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
        print(f"Error downloading from {platform}: {e}")
        return None


# ✅ Route to Download YouTube Videos
@app.post("/youtube")
async def youtube_download(url: str):
    filename = download_video(url, "YouTube")
    if filename:
        return FileResponse(filename, media_type="video/mp4", filename=os.path.basename(filename))
    raise HTTPException(status_code=500, detail="YouTube download failed")


# ✅ Route to Download Instagram Videos
@app.post("/instagram")
async def instagram_download(url: str):
    filename = download_video(url, "Instagram")
    if filename:
        return FileResponse(filename, media_type="video/mp4", filename=os.path.basename(filename))
    raise HTTPException(status_code=500, detail="Instagram download failed")


# ✅ PDF to Word Converter
def pdf_to_word(pdf_path: str) -> str:
    """Convert a PDF file to a Word document."""
    doc = Document()
    reader = PdfReader(pdf_path)

    for page in reader.pages:
        doc.add_paragraph(page.extract_text())

    word_path = pdf_path.replace(".pdf", ".docx")
    doc.save(word_path)
    return word_path


# ✅ Word to PDF Converter (Linux & Vercel Compatible)
def word_to_pdf(docx_path: str) -> Optional[str]:
    """Convert a Word document to a PDF file using LibreOffice (Linux-compatible)."""
    pdf_path = docx_path.replace(".docx", ".pdf")
    try:
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", UPLOAD_FOLDER],
            check=True
        )
        return pdf_path if os.path.exists(pdf_path) else None
    except subprocess.CalledProcessError as e:
        print(f"Error converting Word to PDF: {e}")
        return None


# ✅ File Conversion Route (PDF ⇄ Word)
@app.post("/convert")
async def convert_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    conversion_type: str = Form(...)
):
    filename = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(filename, "wb") as f:
        f.write(await file.read())

    if conversion_type == "pdf-to-doc":
        if not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Invalid file format. Expected PDF.")
        output_path = pdf_to_word(filename)
    elif conversion_type == "doc-to-pdf":
        if not filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Invalid file format. Expected DOCX.")
        output_path = word_to_pdf(filename)
        if output_path is None:
            raise HTTPException(status_code=500, detail="Word to PDF conversion failed.")
    else:
        raise HTTPException(status_code=400, detail="Invalid conversion type.")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=500, detail="Conversion failed.")

    return FileResponse(output_path, filename=os.path.basename(output_path))


@app.get("/")
def health_check():
    return {"status": "FastAPI is running"}
