from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from src.config import (
    FONT_SIZE,
    OVERLAY_MARGIN_BOTTOM,
    OVERLAY_OPACITY,
    OVERLAY_WIDTH_RATIO,
    SUBTITLE_LINES,
)


class SubtitleOverlay(QWidget):
    """Transparent, always-on-top bilingual subtitle overlay."""

    def __init__(self):
        super().__init__()
        self._lines: dict[int, tuple[str, str]] = {}
        self._line_order: list[int] = []
        self._next_line_id = 0
        self._interim_text = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        zh_font_size = int(FONT_SIZE * 0.9)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, {OVERLAY_OPACITY});
                padding: 12px 20px;
                border-radius: 10px;
            }}
        """)

        self._en_font_size = FONT_SIZE
        self._zh_font_size = zh_font_size

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self._position_overlay()

    def on_en_ready(self, text: str, is_final: bool):
        """Handle English text — committed (final) or interim preview."""
        if is_final:
            line_id = self._next_line_id
            self._next_line_id += 1
            self._lines[line_id] = (text, "")
            self._line_order.append(line_id)
            self._interim_text = ""
            while len(self._line_order) > SUBTITLE_LINES:
                old_id = self._line_order.pop(0)
                self._lines.pop(old_id, None)
        else:
            self._interim_text = text
        self._refresh()

    def on_zh_ready(self, line_id: int, zh_text: str):
        """Fill in Chinese translation for a finalized line."""
        if line_id in self._lines:
            en, _ = self._lines[line_id]
            self._lines[line_id] = (en, zh_text)
            self._refresh()

    def clear_text(self):
        self._lines.clear()
        self._line_order.clear()
        self._interim_text = ""
        self.label.setText("")

    def _refresh(self):
        html_parts = []

        for lid in self._line_order:
            en, zh = self._lines[lid]
            html_parts.append(
                f'<div style="color:#FFFFFF; font-size:{self._en_font_size}px;">{en}</div>'
            )
            zh_display = zh if zh else "&nbsp;"
            html_parts.append(
                f'<div style="color:#FFD700; font-size:{self._zh_font_size}px;">{zh_display}</div>'
            )

        if self._interim_text:
            html_parts.append(
                f'<div style="color:#AAAAAA; font-size:{self._en_font_size}px; '
                f'font-style:italic;">{self._interim_text}...</div>'
            )

        self.label.setText("".join(html_parts))
        self.label.adjustSize()
        self._position_overlay()

    def _position_overlay(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        screen_geo = screen.geometry()
        width = int(screen_geo.width() * OVERLAY_WIDTH_RATIO)
        self.setFixedWidth(width)
        self.adjustSize()
        x = (screen_geo.width() - width) // 2
        y = screen_geo.height() - OVERLAY_MARGIN_BOTTOM - self.height()
        self.move(x, y)
