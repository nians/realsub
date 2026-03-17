import logging
import queue
import time
from concurrent.futures import ThreadPoolExecutor

from faster_whisper import WhisperModel
from PyQt6.QtCore import QThread, pyqtSignal

from src.config import COMPUTE_TYPE, DEVICE, WHISPER_MODEL
from src.translator import Translator

logger = logging.getLogger(__name__)


class Transcriber(QThread):
    """Chunk-based transcriber: consumes audio chunks from a queue."""

    en_ready = pyqtSignal(str, bool)
    zh_ready = pyqtSignal(int, str)

    def __init__(self, chunk_queue: queue.Queue):
        super().__init__()
        self.chunk_queue = chunk_queue
        self.running = False
        self.model: WhisperModel | None = None
        self._line_id = 0
        self._translate_pool = ThreadPoolExecutor(max_workers=2)
        self.translator = Translator()

    def run(self):
        t0 = time.perf_counter()
        self.model = WhisperModel(WHISPER_MODEL, device=DEVICE, compute_type=COMPUTE_TYPE)
        logger.info(f"[MODEL] device={DEVICE}, compute_type={COMPUTE_TYPE}")
        logger.info(f"[MODEL] load={time.perf_counter() - t0:.2f}s")
        self.running = True

        while self.running:
            try:
                chunk, enqueue_time = self.chunk_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            queue_wait = time.perf_counter() - enqueue_time

            try:
                t1 = time.perf_counter()
                segments, _ = self.model.transcribe(
                    chunk,
                    language="en",
                    beam_size=1,
                    vad_filter=False,
                )
                en_text = " ".join(seg.text for seg in segments).strip()
                elapsed = time.perf_counter() - t1

                if not en_text:
                    continue

                logger.info(
                    f"[WHISPER] queue_wait={queue_wait:.3f}s "
                    f"transcribe={elapsed:.3f}s text='{en_text[:60]}'"
                )

                line_id = self._line_id
                self._line_id += 1
                self.en_ready.emit(en_text, True)
                self._translate_pool.submit(self._do_translate, line_id, en_text)

            except Exception as e:
                logger.error(f"[WHISPER] error: {e}")

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
