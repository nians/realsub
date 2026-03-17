import logging
import queue
import threading
import time

import numpy as np
import sounddevice as sd

from src.config import CHANNELS, CHUNK_DURATION, MAX_CHUNK_DURATION, SAMPLE_RATE
from src.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from the microphone and produces chunks for transcription."""

    def __init__(self, chunk_queue: queue.Queue):
        self.chunk_queue = chunk_queue
        self.stream: sd.InputStream | None = None
        self.vad = VoiceActivityDetector()

        self.max_samples = int(MAX_CHUNK_DURATION * SAMPLE_RATE)
        self.min_samples = int(CHUNK_DURATION * SAMPLE_RATE)
        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.write_pos = 0
        self._lock = threading.Lock()
        self._chunk_start_time = 0.0

    def start(self):
        self.vad.reset()
        self.write_pos = 0
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._audio_callback,
            blocksize=int(SAMPLE_RATE * 0.1),
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        with self._lock:
            if self.write_pos > 0:
                self._emit_chunk()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        audio = indata[:, 0]

        with self._lock:
            if self.write_pos == 0:
                self._chunk_start_time = time.perf_counter()

            remaining = self.max_samples - self.write_pos
            to_write = min(len(audio), remaining)
            self.buffer[self.write_pos : self.write_pos + to_write] = audio[:to_write]
            self.write_pos += to_write

            should_emit = False
            if self.write_pos >= self.max_samples:
                should_emit = True
            elif self.write_pos >= self.min_samples:
                should_emit = self.vad.process(audio)

            if should_emit:
                self._emit_chunk()

    def _emit_chunk(self):
        if self.write_pos == 0:
            return
        chunk = self.buffer[: self.write_pos].copy()
        duration = self.write_pos / SAMPLE_RATE
        wait_time = time.perf_counter() - self._chunk_start_time
        logger.info(f"[AUDIO] chunk={duration:.1f}s, accumulate_wait={wait_time:.2f}s")
        self.write_pos = 0
        self.vad.reset()
        self.chunk_queue.put((chunk, time.perf_counter()))
