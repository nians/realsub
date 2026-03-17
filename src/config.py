# Whisper model settings
WHISPER_MODEL = "models/whisper-small-singlish-ct2"


def _detect_device():
    """Auto-detect: NVIDIA GPU → cuda/float16, otherwise → cpu/int8."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


DEVICE, COMPUTE_TYPE = _detect_device()

# Audio capture settings
SAMPLE_RATE = 16000
CHANNELS = 1

# Chunking settings
CHUNK_DURATION = 2.0
SILENCE_THRESHOLD = 0.03
SILENCE_DURATION = 0.8
MAX_CHUNK_DURATION = 5.0

# Subtitle overlay settings
SUBTITLE_LINES = 3
FONT_SIZE = 28
OVERLAY_OPACITY = 180
OVERLAY_MARGIN_BOTTOM = 80
OVERLAY_WIDTH_RATIO = 0.7
