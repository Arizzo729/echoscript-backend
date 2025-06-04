# ---- EchoScript.AI: utils/export_utils.py ----

import os
import json
from docx import Document
from fpdf import FPDF
from uuid import uuid4
from app.utils.logger import logger

# TEMP simulated transcript store (replace with DB or real storage)
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

def generate_export_file(transcript_id: str, format: str) -> str:
    if transcript_id not in TRANSCRIPTS:
        logger.error(f"Transcript not found for export: {transcript_id}")
        raise ValueError("Transcript not found.")

    transcript = TRANSCRIPTS[transcript_id]
    safe_id = f"{transcript_id}_{uuid4().hex[:6]}"
    path = os.path.join(EXPORT_DIR, f"{safe_id}.{format}")

    if format == "txt":
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {transcript['title']}\n\n")
            f.write(transcript["text"])

    elif format == "docx":
        doc = Document()
        doc.add_heading(transcript["title"], level=1)
        if "summary" in transcript:
            doc.add_paragraph(f"Summary: {transcript['summary']}\n", style='Intense Quote')
        doc.add_paragraph(transcript["text"])
        doc.add_paragraph("\n---")
        doc.add_paragraph(f"Language: {transcript.get('language', 'unknown')}")
        if transcript.get("speakers"):
            doc.add_paragraph("Speakers: " + ", ".join(transcript["speakers"]))
        doc.save(path)

    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 10, transcript["title"])
        pdf.ln()

        if "summary" in transcript:
            pdf.set_font("Arial", "I", 12)
            pdf.multi_cell(0, 10, f"Summary: {transcript['summary']}")
            pdf.ln()

        pdf.set_font("Arial", size=12)
        for line in transcript["text"].splitlines():
            pdf.multi_cell(0, 10, line)
        pdf.output(path)

    elif format == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, indent=2)

    else:
        raise ValueError(f"Unsupported export format: {format}")

    logger.info(f"✅ Generated export for {transcript_id} → {format.upper()} @ {path}")
    return path

