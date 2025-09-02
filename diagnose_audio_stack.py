import platform, sys
print("Python:", sys.version)
print("OS:", platform.platform())

try:
    import torch
    print("Torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("CUDA device count:", torch.cuda.device_count())
        print("Current device:", torch.cuda.get_device_name(0))
except Exception as e:
    print("Torch check error:", e)

try:
    import faster_whisper
    print("faster-whisper:", faster_whisper.__version__)
except Exception as e:
    print("faster-whisper check error:", e)
