import logging
import queue

import numpy as np
import sounddevice as sd

from src.config import CHANNELS, CHUNK_INTERVAL, SAMPLE_RATE

logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from the microphone and streams fixed-interval chunks."""

    def __init__(self, chunk_queue: queue.Queue):
        self.chunk_queue = chunk_queue
        self.stream: sd.InputStream | None = None
        self.blocksize = int(SAMPLE_RATE * CHUNK_INTERVAL)

    def start(self):
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._audio_callback,
            blocksize=self.blocksize,
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        audio = indata[:, 0].copy()
        self.chunk_queue.put(audio)
