# app/routes/subtitles.py
import pathlib
import tempfile
import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1", tags=["subtitles"])


def to_webvtt(segments):
    def ts(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        # VTT uses a dot for milliseconds
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    lines = ["WEBVTT", ""]
    for seg in segments:
        lines.append(f"{ts(seg['start'])} --> {ts(seg['end'])}")
        lines.append(seg["text"])
        lines.append("")
    return "\n".join(lines)


@router.post("/subtitles")
async def make_subtitles(file: UploadFile = File(...)):
    tmpdir = pathlib.Path(tempfile.mkdtemp())
    inpath = tmpdir / f"in_{uuid.uuid4().hex}_{file.filename}"
    with inpath.open("wb") as f:
        f.write(await file.read())

    # TODO: replace with real transcription that returns segments with timestamps
    segments = [
        {"start": 0.0, "end": 3.2, "text": "Example line one."},
        {"start": 3.3, "end": 6.7, "text": "Example line two."},
    ]

    vtt_text = to_webvtt(segments)
    vtt_path = tmpdir / "subtitles.vtt"
    vtt_path.write_text(vtt_text, encoding="utf-8")

    return FileResponse(vtt_path, media_type="text/vtt", filename="subtitles.vtt")
