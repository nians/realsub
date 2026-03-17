import logging
import queue
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtCore import QThread, pyqtSignal

from src.config import COMPUTE_TYPE, WHISPER_MODEL_DIR
from src.translator import Translator

logger = logging.getLogger(__name__)

# Add vendor path for whisper_streaming
sys.path.insert(0, "vendor/whisper_streaming")


class Transcriber(QThread):
    """Streaming transcriber using whisper_streaming's OnlineASRProcessor.

    Uses FasterWhisperASR backend with singlish model on CPU (int8),
    and local agreement policy for stable, non-fragmented output.
    """

    en_ready = pyqtSignal(str, bool)  # (text, is_final)
    zh_ready = pyqtSignal(int, str)   # (line_id, chinese_text)

    def __init__(self, chunk_queue: queue.Queue):
        super().__init__()
        self.chunk_queue = chunk_queue
        self.running = False
        self._line_id = 0
        self._translate_pool = ThreadPoolExecutor(max_workers=2)
        self.translator = Translator()

    def _create_asr(self):
        """Create FasterWhisperASR with CPU int8 for Apple Silicon."""
        from whisper_online import FasterWhisperASR

        class CpuFasterWhisperASR(FasterWhisperASR):
            def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
                from faster_whisper import WhisperModel
                path = model_dir if model_dir else modelsize
                return WhisperModel(
                    path, device="cpu", compute_type=COMPUTE_TYPE
                )

        return CpuFasterWhisperASR(
            lan="en", model_dir=WHISPER_MODEL_DIR
        )

    def run(self):
        from whisper_online import OnlineASRProcessor

        t0 = time.perf_counter()
        asr = self._create_asr()
        self.online = OnlineASRProcessor(asr, buffer_trimming=("segment", 15))
        logger.info(f"[MODEL] whisper_streaming load={time.perf_counter() - t0:.2f}s")

        # Warmup
        import numpy as np
        asr.transcribe(np.zeros(16000, dtype=np.float32))
        logger.info("[MODEL] warmup done")

        self.running = True

        while self.running:
            try:
                audio_chunk = self.chunk_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            t1 = time.perf_counter()
            self.online.insert_audio_chunk(audio_chunk)
            result = self.online.process_iter()
            elapsed = time.perf_counter() - t1

            beg, end, committed_text = result
            if committed_text:
                logger.info(
                    f"[WHISPER] process={elapsed:.3f}s "
                    f"committed='{committed_text[:60]}'"
                )
                line_id = self._line_id
                self._line_id += 1
                self.en_ready.emit(committed_text.strip(), True)
                self._translate_pool.submit(
                    self._do_translate, line_id, committed_text.strip()
                )

            # Emit incomplete buffer as interim preview
            incomplete = self.online.transcript_buffer.complete()
            if incomplete:
                interim_text = " ".join(w[2] for w in incomplete).strip()
                if interim_text:
                    self.en_ready.emit(interim_text, False)

        # Flush remaining text on stop
        result = self.online.finish()
        if result[2]:
            text = result[2].strip()
            if text:
                line_id = self._line_id
                self._line_id += 1
                self.en_ready.emit(text, True)
                self._translate_pool.submit(self._do_translate, line_id, text)

    def _do_translate(self, line_id: int, en_text: str):
        try:
            t0 = time.perf_counter()
            zh_text = self.translator.translate(en_text)
            logger.info(f"[TRANSLATE] time={time.perf_counter() - t0:.3f}s")
            if zh_text:
                self.zh_ready.emit(line_id, zh_text)
        except Exception as e:
            logger.error(f"[TRANSLATE] error: {e}")

    def stop(self):
        self.running = False
        self._translate_pool.shutdown(wait=False)
        self.wait()
