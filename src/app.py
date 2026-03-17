import queue
import sys

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.audio_capture import AudioCapture
from src.overlay import SubtitleOverlay
from src.transcriber import Transcriber


class SubtitleApp:
    """Main application: wires audio capture, transcriber, and overlay together."""

    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.overlay = SubtitleOverlay()
        self.chunk_queue: queue.Queue = queue.Queue()
        self.audio_capture = AudioCapture(self.chunk_queue)
        self.transcriber = Transcriber(self.chunk_queue)

        self.transcriber.en_ready.connect(self.overlay.on_en_ready)
        self.transcriber.zh_ready.connect(self.overlay.on_zh_ready)

        self.is_running = False

        self.tray = QSystemTrayIcon()
        self._setup_tray()

    def _setup_tray(self):
        menu = QMenu()

        self.toggle_action = QAction("Stop")
        self.toggle_action.triggered.connect(self.toggle)
        menu.addAction(self.toggle_action)

        clear_action = QAction("Clear Subtitles")
        clear_action.triggered.connect(self.overlay.clear_text)
        menu.addAction(clear_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Real-time Subtitle")
        self.tray.show()

    def toggle(self):
        if self.is_running:
            self.audio_capture.stop()
            self.transcriber.stop()
            self.overlay.hide()
            self.toggle_action.setText("Start")
            self.tray.setToolTip("Real-time Subtitle (Paused)")
        else:
            self.overlay.show()
            self.transcriber.start()
            self.audio_capture.start()
            self.toggle_action.setText("Stop")
            self.tray.setToolTip("Real-time Subtitle (Running)")
        self.is_running = not self.is_running

    def _quit(self):
        if self.is_running:
            self.audio_capture.stop()
            self.transcriber.stop()
        self.tray.hide()
        self.qt_app.quit()

    def run(self):
        self.toggle()  # auto-start
        sys.exit(self.qt_app.exec())
