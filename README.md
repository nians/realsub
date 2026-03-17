# RealSub - Real-time Bilingual Subtitle for Lectures

Real-time speech-to-text subtitle overlay for English lectures, designed for university students whose English is not strong. Captures microphone audio, transcribes English speech, and displays bilingual (English + Chinese) subtitles on screen.

## Features

- **Real-time transcription** — English speech recognized via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2)
- **Bilingual subtitles** — English (white) + Chinese translation (gold) displayed simultaneously
- **Local & offline** — All models run locally, no network required after setup
- **Always-on-top overlay** — Transparent, frameless subtitle window that stays on top of any application
- **Auto device detection** — NVIDIA GPU (`cuda/float16`) or CPU (`int8`) selected automatically
- **Async translation** — English appears immediately, Chinese fills in asynchronously via [Argos Translate](https://github.com/argosopentech/argos-translate)
- **VAD chunking** — Energy-based voice activity detection splits audio at natural pauses (2–5s chunks)

## Architecture

```
Microphone → sounddevice (16kHz mono)
           → Audio buffer + VAD silence detection
           → Chunk queue (2–5s per chunk)
           → faster-whisper transcription (worker thread)
           → English subtitle displayed immediately
           → Argos Translate (async thread pool)
           → Chinese subtitle filled in
           → PyQt6 transparent overlay
```

## Requirements

- Python 3.10+
- macOS (Apple Silicon) or Windows/Linux (NVIDIA GPU recommended)
- PortAudio (`brew install portaudio` on macOS)

## Setup

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/nians/realsub.git
cd realsub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Convert Whisper model to CTranslate2 format (first time only)
pip install transformers torch
ct2-transformers-converter \
  --model jensenlwt/whisper-small-singlish-122k \
  --output_dir models/whisper-small-singlish-ct2 \
  --quantization int8

# Download Argos Translate en→zh model (auto-downloaded on first run, ~67MB)
```

## Usage

```bash
./run.sh
```

Or manually:

```bash
source venv/bin/activate
python3 -m src.main
```

The subtitle overlay appears at the bottom of the screen. Use the **system tray icon** to:
- **Stop/Start** recording
- **Clear** subtitles
- **Quit** the application

## Project Structure

```
├── run.sh                # Launch script
├── requirements.txt      # Python dependencies
├── models/               # CTranslate2 model files (not in git)
└── src/
    ├── main.py           # Entry point, logging config
    ├── app.py            # QApplication lifecycle, system tray, signal wiring
    ├── audio_capture.py  # Microphone capture, VAD chunking, chunk queue
    ├── vad.py            # Energy-based voice activity detection
    ├── transcriber.py    # faster-whisper transcription worker thread
    ├── translator.py     # Argos Translate en→zh (background init + warmup)
    ├── overlay.py        # PyQt6 transparent always-on-top subtitle overlay
    └── config.py         # All configurable parameters + device auto-detection
```

## Configuration

Edit `src/config.py` to tune parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WHISPER_MODEL` | `models/whisper-small-singlish-ct2` | Path to CTranslate2 model |
| `CHUNK_DURATION` | `2.0` | Min seconds before VAD can trigger |
| `SILENCE_DURATION` | `0.8` | Seconds of silence to trigger chunk boundary |
| `MAX_CHUNK_DURATION` | `5.0` | Force chunk split even without silence |
| `SUBTITLE_LINES` | `3` | Number of bilingual lines visible |
| `FONT_SIZE` | `28` | Subtitle font size (px) |

## Using a Different Whisper Model

Any Whisper model on HuggingFace can be converted:

```bash
# Example: use standard small.en model
ct2-transformers-converter \
  --model openai/whisper-small.en \
  --output_dir models/whisper-small-en-ct2 \
  --quantization int8
```

Then update `WHISPER_MODEL` in `src/config.py`.

## License

MIT
