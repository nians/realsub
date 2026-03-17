import numpy as np

from src.config import SAMPLE_RATE, SILENCE_DURATION, SILENCE_THRESHOLD


class VoiceActivityDetector:
    """Simple energy-based voice activity detection.

    Detects transitions from speech to silence to determine
    natural chunk boundaries for transcription.
    """

    def __init__(self):
        self.silence_samples = int(SILENCE_DURATION * SAMPLE_RATE)
        self.consecutive_silence = 0
        self.has_speech = False

    def reset(self):
        self.consecutive_silence = 0
        self.has_speech = False

    def process(self, audio_frame: np.ndarray) -> bool:
        """Process an audio frame and return True if a chunk boundary is detected.

        A boundary is detected when speech is followed by sufficient silence.
        """
        rms = np.sqrt(np.mean(audio_frame.astype(np.float32) ** 2))

        if rms > SILENCE_THRESHOLD:
            # Speech detected
            self.has_speech = True
            self.consecutive_silence = 0
            return False

        # Silence detected
        self.consecutive_silence += len(audio_frame)

        if self.has_speech and self.consecutive_silence >= self.silence_samples:
            # Speech followed by enough silence -> chunk boundary
            self.has_speech = False
            self.consecutive_silence = 0
            return True

        return False
