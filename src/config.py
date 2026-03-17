# Whisper model settings (faster-whisper CTranslate2 backend via whisper_streaming)
WHISPER_MODEL_DIR = "models/whisper-small-singlish-ct2"  # Fine-tuned for Singapore English
COMPUTE_TYPE = "int8"           # int8 is fast on Apple Silicon

# Audio capture settings
SAMPLE_RATE = 16000             # 16kHz required by Whisper
CHANNELS = 1                    # Mono
CHUNK_INTERVAL = 1.0            # Seconds per audio chunk fed to whisper_streaming

# Subtitle overlay settings
SUBTITLE_LINES = 3              # Number of lines visible on overlay
FONT_SIZE = 28                  # Subtitle font size in pixels
OVERLAY_OPACITY = 180           # Background opacity (0-255)
OVERLAY_MARGIN_BOTTOM = 80      # Pixels from bottom of screen
OVERLAY_WIDTH_RATIO = 0.7       # Width as fraction of screen width
