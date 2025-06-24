# ---- EchoScript.AI: utils/export_utils.py ----

import os
import json
from docx import Document
from fpdf import FPDF
from uuid import uuid4
from app.utils.logger import logger

# === Temporary In-Memory Transcript Store (Replace with DB/Redis Later) ===
TRANSCRIPTS = {
    "test123": {
        "title": "Meeting with Client",
        "text": "Hello, this is a sample transcript. Welcome to EchoScript.",
        "language": "en",
        "speakers": ["Speaker 1", "Speaker 2"],
        "summary": "Initial meeting with new client covering introductions and goals.",
    }
}

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# === Core Export Generator ===
def generate_export_file(transcript_id: str, format: str) -> str:
    if transcript_id not in TRANSCRIPTS:
        logger.error(f"[Export] ❌ Transcript ID '{transcript_id}' not found.")
        raise ValueError("Transcript not found.")

    transcript = TRANSCRIPTS[transcript_id]
    safe_id = f"{transcript_id}_{uuid4().hex[:6]}"
    filepath = os.path.join(EXPORT_DIR, f"{safe_id}.{format}")

    try:
        if format == "txt":
            _export_txt(filepath, transcript)
        elif format == "docx":
            _export_docx(filepath, transcript)
        elif format == "pdf":
            _export_pdf(filepath, transcript)
        elif format == "json":
            _export_json(filepath, transcript)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"[Export] ✅ File generated: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"[Export Error] {e}")
        raise RuntimeError("Failed to generate export file.")

# === Format-Specific Export Functions ===

def _export_txt(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {data['title']}\n\n")
        f.write(data["text"])

def _export_docx(path: str, data: dict):
    doc = Document()
    doc.add_heading(data["title"], level=1)
    if data.get("summary"):
        doc.add_paragraph(f"Summary: {data['summary']}", style='Intense Quote')
    doc.add_paragraph(data["text"])
    doc.add_paragraph("\n---")
    doc.add_paragraph(f"Language: {data.get('language', 'unknown')}")
    if data.get("speakers"):
        doc.add_paragraph("Speakers: " + ", ".join(data["speakers"]))
    doc.save(path)

def _export_pdf(path: str, data: dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 10, data["title"])
    pdf.ln()

    if data.get("summary"):
        pdf.set_font("Arial", "I", 12)
        pdf.multi_cell(0, 10, f"Summary: {data['summary']}")
        pdf.ln()

    pdf.set_font("Arial", size=12)
    for line in data["text"].splitlines():
        pdf.multi_cell(0, 10, line)
    pdf.output(path)

def _export_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
