# app/services/transcription.py
from __future__ import annotations

import os
from dataclasses import dataclass

# (optional) repeat guards here in case this module is imported first by tests
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("ORT_DISABLE_GPU", "1")

try:
    from pyannote.audio import Pipeline as PyannotePipeline

    _HAS_PYANNOTE = True
except Exception:
    PyannotePipeline = None  # type: ignore
    _HAS_PYANNOTE = False


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None


class FasterWhisperTranscriber:
    """
    Transcription via faster-whisper (CTranslate2).
    Optional diarization via pyannote.audio when available.
    """

    def __init__(
        self, model_name: str = "base", compute_type: str | None = None
    ) -> None:
        self.model_name = model_name
        # Safe CPU defaults on Windows. If you ever add a GPU, change device="cuda".
        self.compute_type = compute_type or "int8"
        self._model = None
        self._dia = None

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # lazy import

            # 🔒 Explicit CPU to avoid any CUDA/cudnn DLL loading
            self._model = WhisperModel(
                self.model_name, device="cpu", compute_type=self.compute_type
            )
        return self._model

    def _ensure_diarizer(self):
        if not _HAS_PYANNOTE:
            return None
        if self._dia is None:
            checkpoint = os.getenv(
                "PYANNOTE_PIPELINE", "pyannote/speaker-diarization-3.1"
            )
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            kwargs = {"use_auth_token": hf_token} if hf_token else {}
            self._dia = PyannotePipeline.from_pretrained(checkpoint, **kwargs)
        return self._dia

    def transcribe(
        self,
        audio_path: str,
        language: str | None = None,
        vad: bool = False,
    ) -> tuple[str, list[Segment]]:
        model = self._ensure_model()
        segments_it, info = model.transcribe(
            audio=audio_path,
            language=language,
            vad_filter=vad,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        lang = info.language or (language or "unknown")
        segments = [Segment(start=s.start, end=s.end, text=s.text) for s in segments_it]
        return lang, segments

    def diarize(self, audio_path: str) -> list[tuple[float, float, str]]:
        dia = self._ensure_diarizer()
        if dia is None:
            return []
        ann = dia(audio_path)
        return [
            (float(seg.start), float(seg.end), str(label))
            for seg, label in ann.itertracks(yield_label=True)
        ]

    @staticmethod
    def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
        return max(0.0, min(a_end, b_end) - max(a_start, b_start))

    def assign_speakers(
        self, segments: list[Segment], turns: list[tuple[float, float, str]]
    ) -> list[Segment]:
        if not turns:
            return segments
        out: list[Segment] = []
        for s in segments:
            best = None
            best_overlap = 0.0
            for ts, te, lab in turns:
                ov = self._overlap(s.start, s.end, ts, te)
                if ov > best_overlap:
                    best_overlap = ov
                    best = lab
            out.append(Segment(start=s.start, end=s.end, text=s.text, speaker=best))
        return out
