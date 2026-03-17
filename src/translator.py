import logging
import threading

import argostranslate.package
import argostranslate.translate

logger = logging.getLogger(__name__)


class Translator:
    """Translates English to Chinese using a local Argos Translate model.

    Initialization and warmup happen in a background thread so they
    never block the transcription pipeline.
    """

    def __init__(self):
        self._translator = None
        self._ready = threading.Event()
        self._init_thread = threading.Thread(target=self._init_model, daemon=True)
        self._init_thread.start()

    def _init_model(self):
        """Load model and warm up in background."""
        try:
            self._ensure_package_installed()
            self._translator = argostranslate.translate.get_translation_from_codes("en", "zh")
            if self._translator is None:
                logger.error("[TRANSLATOR] failed to load en->zh model")
                return
            # Warmup: first call is slow due to JIT compilation
            logger.info("[TRANSLATOR] warming up...")
            self._translator.translate("warmup")
            logger.info("[TRANSLATOR] ready")
        except Exception as e:
            logger.error(f"[TRANSLATOR] init error: {e}")
        finally:
            self._ready.set()

    def _ensure_package_installed(self):
        installed = argostranslate.package.get_installed_packages()
        for pkg in installed:
            if pkg.from_code == "en" and pkg.to_code == "zh":
                return

        logger.info("[TRANSLATOR] downloading en->zh model (~67MB)...")
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        for pkg in available:
            if pkg.from_code == "en" and pkg.to_code == "zh":
                argostranslate.package.install_from_path(pkg.download())
                logger.info("[TRANSLATOR] en->zh model installed")
                return
        raise RuntimeError("en->zh translation package not found")

    def translate(self, text: str) -> str:
        """Translate English to Chinese. Returns empty string if not ready yet."""
        if not text.strip():
            return ""
        if not self._ready.is_set():
            return ""  # Still warming up, skip translation
        if self._translator is None:
            return ""
        try:
            return self._translator.translate(text)
        except Exception:
            return text
