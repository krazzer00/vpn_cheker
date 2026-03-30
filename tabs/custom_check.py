# tabs/custom_check.py
import queue
import threading
from urllib.parse import urlparse

import theme
from theme import COLOR_OK, COLOR_BAD, COLOR_WARN, COLOR_MUTED

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal

from engine.ping import ping_host
from engine.http_check import http_check


class CustomCheckTab(QWidget):
    _check_done = pyqtSignal(dict, dict, str)

    def __init__(self, result_queue: queue.Queue, parent=None):
        super().__init__(parent)
        self.result_queue = result_queue
        self._running = False
        self._build()
        self._check_done.connect(self._on_done)

    def _build(self) -> None:
        self.setStyleSheet(f"background: {theme.DARK_BG};")
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        center = QWidget()
        center.setFixedWidth(540)
        center.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(center)
        cl.setAlignment(Qt.AlignCenter)
        cl.setSpacing(0)

        title = QLabel("Проверить ресурс")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Введи URL или hostname")
        subtitle.setStyleSheet(
            f"font-size: 12px; color: {COLOR_MUTED}; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)

        cl.addWidget(title)
        cl.addSpacing(4)
        cl.addWidget(subtitle)
        cl.addSpacing(20)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("https://example.com или example.com")
        self.url_entry.setFixedHeight(40)
        self.url_entry.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.CARD_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 8px;
                padding: 4px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {theme.ACCENT}; }}
        """)
        self.url_entry.returnPressed.connect(self._start_check)

        self.check_btn = QPushButton("Проверить")
        self.check_btn.setFixedSize(120, 40)
        self.check_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.ACCENT}; color: white; border: none;
                border-radius: 8px; font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {theme._lighten(theme.ACCENT)}; }}
            QPushButton:disabled {{ background: {theme.BORDER}; color: {COLOR_MUTED}; }}
        """)
        self.check_btn.clicked.connect(self._start_check)

        input_row.addWidget(self.url_entry, 1)
        input_row.addWidget(self.check_btn)
        cl.addLayout(input_row)
        cl.addSpacing(20)

        # Result card
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet(
            f"QFrame {{ background: {theme.CARD_BG}; border: 1px solid {theme.BORDER};"
            f" border-radius: 12px; }}"
        )
        self.result_frame.setMinimumHeight(80)
        self._result_layout = QVBoxLayout(self.result_frame)
        self._result_layout.setContentsMargins(16, 14, 16, 14)
        self._result_layout.setSpacing(8)
        cl.addWidget(self.result_frame)

        outer.addWidget(center)

    # ── Check logic ────────────────────────────────────────────────────────────

    def _start_check(self) -> None:
        if self._running:
            return
        raw = self.url_entry.text().strip()
        if not raw:
            return
        if not raw.startswith("http"):
            raw = "https://" + raw

        self._running = True
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Проверка...")

        url_copy = raw

        def worker():
            host = urlparse(url_copy).hostname or url_copy
            ping_result = ping_host(host)
            http_result = http_check(url_copy)
            self._check_done.emit(ping_result, http_result, url_copy)

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, ping_result: dict, http_result: dict, url: str) -> None:
        self._show_result(ping_result, http_result, url)
        self._running = False
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Проверить")

    def _show_result(self, ping_result: dict, http_result: dict, url: str) -> None:
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        accessible = http_result["accessible"]
        ping_ms    = ping_result.get("ping_ms")
        loss_pct   = ping_result.get("loss_pct")

        color = COLOR_OK if accessible else COLOR_BAD

        top_row = QHBoxLayout()
        url_lbl = QLabel(url)
        url_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        status_lbl = QLabel("Доступен ✓" if accessible else "Недоступен ✗")
        status_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {color}; background: transparent;"
        )
        top_row.addWidget(url_lbl, 1)
        top_row.addWidget(status_lbl)

        top_w = QWidget()
        top_w.setStyleSheet("background: transparent;")
        top_w.setLayout(top_row)
        self._result_layout.addWidget(top_w)

        stats = QHBoxLayout()
        stats.setAlignment(Qt.AlignLeft)
        stats.setSpacing(0)

        ping_color = (COLOR_OK if ping_ms and ping_ms < 100
                      else (COLOR_WARN if ping_ms else COLOR_BAD))
        self._add_stat(stats, "ПИНГ",
                       f"{ping_ms:.0f} ms" if ping_ms is not None else "—", ping_color)

        if loss_pct is None:
            self._add_stat(stats, "ПОТЕРИ", "н/п", COLOR_MUTED)
        else:
            lc = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            self._add_stat(stats, "ПОТЕРИ", f"{loss_pct:.1f}%", lc)

        sc = http_result.get("status_code")
        self._add_stat(stats, "HTTP", str(sc) if sc else "—")

        rt = http_result.get("response_ms")
        self._add_stat(stats, "ОТВЕТ", f"{rt:.0f} ms" if rt is not None else "—")

        stats_w = QWidget()
        stats_w.setStyleSheet("background: transparent;")
        stats_w.setLayout(stats)
        self._result_layout.addWidget(stats_w)

    def _add_stat(self, layout, label: str, value: str, color: str = "#e0e0e0") -> None:
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setContentsMargins(0, 0, 24, 0)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 9px; color: {COLOR_MUTED}; background: transparent;")
        val = QLabel(value)
        val.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color}; background: transparent;"
        )
        col.addWidget(lbl)
        col.addWidget(val)

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setLayout(col)
        layout.addWidget(w)

    def handle_result(self, msg: dict) -> None:
        pass
