import sys
from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    print("Usage: python scripts/asr_smoketest.py <path-to-audio.(wav|mp3|mp4|m4a)>")
    sys.exit(1)

audio_path = sys.argv[1]

# compute_type fallback ladder:
# - "float16" (best on modern GPUs)
# - "int8_float16" (good speed/VRAM balance on GPUs)
# - "int8" (CPU-friendly)
preferred = ["float16", "int8_float16", "int8"]

last_err = None
for ctype in preferred:
    try:
        print(f"Loading model (large-v3) with compute_type={ctype} ...")
        model = WhisperModel("large-v3", compute_type=ctype)
        break
    except Exception as e:
        last_err = e
        print(f"Failed with compute_type={ctype}: {e}")
else:
    raise RuntimeError(f"Could not load model with any compute_type. Last error: {last_err}")

# Basic VAD helps trim long silences; tweak if your clips are choppy.
segments, info = model.transcribe(
    audio=audio_path,
    vad_filter=True,
    vad_parameters={"min_silence_duration_ms": 500},
)

print("Detected language:", info.language)
out = []
for s in segments:
    out.append({"start": s.start, "end": s.end, "text": s.text})

print(f"\nSegments: {len(out)}")
for i, seg in enumerate(out[:12]):  # preview first 12 lines
    print(f"[{i:02d}] {seg['start']:.2f}–{seg['end']:.2f}  {seg['text']}")

print("\nOK ✅  If this looks good, we’ll wire this into EchoScript next.")
