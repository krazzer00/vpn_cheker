# app.py
import queue
import threading

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QPushButton, QLabel, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import requests

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab
from tabs.history import HistoryTab
from tabs.settings import SettingsTab
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT

_TAB_NAMES = [
    "🛡  Полная проверка",
    "🔍  Кастомная",
    "📋  История",
    "⚙️  Настройки",
]

_BTN_ACTIVE = f"""
    QPushButton {{
        background: {ACCENT}; color: white; border: none;
        border-radius: 0; padding: 0 16px;
        font-size: 12px; font-weight: bold; height: 38px;
    }}
"""
_BTN_INACTIVE = f"""
    QPushButton {{
        background: transparent; color: #666677; border: none;
        border-radius: 0; padding: 0 16px;
        font-size: 12px; height: 38px;
    }}
    QPushButton:hover {{ background: #1e1e2e; color: #cccccc; }}
"""


class VpnCheckerApp(QMainWindow):
    _ip_ready  = pyqtSignal(str)
    _ip_failed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPN Checker")
        self.resize(1440, 920)
        self.setMinimumSize(1024, 680)

        self.result_queue: queue.Queue = queue.Queue()
        self._current_ip_info: str = ""

        self._ip_ready.connect(self._update_ip_ok)
        self._ip_failed.connect(self._update_ip_fail)

        self._build()

        # Poll result queue every 100 ms
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_queue)
        self._poll_timer.start(100)

        # Fetch IP in background
        QTimer.singleShot(200, self._fetch_ip_async)

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background: {DARK_BG};")
        self.setCentralWidget(central)

        main = QVBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._build_header())
        main.addWidget(self._build_content(), 1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(44)
        header.setStyleSheet(
            f"QFrame {{ background: {DARKER_BG}; border-bottom: 1px solid {BORDER}; border-radius: 0; }}"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(4, 3, 12, 3)
        hl.setSpacing(1)

        self._tab_btns: dict[str, QPushButton] = {}
        for name in _TAB_NAMES:
            btn = QPushButton(name)
            btn.setFixedHeight(38)
            btn.setStyleSheet(_BTN_INACTIVE)
            btn.clicked.connect(lambda checked, n=name: self._switch_tab(n))
            hl.addWidget(btn)
            self._tab_btns[name] = btn

        hl.addStretch()

        # IP badge
        ip_badge = QFrame()
        ip_badge.setStyleSheet(
            f"QFrame {{ background: #1e1e2e; border: 1px solid {BORDER}; border-radius: 12px; }}"
        )
        ip_bl = QHBoxLayout(ip_badge)
        ip_bl.setContentsMargins(10, 3, 10, 3)
        ip_bl.setSpacing(4)

        self._ip_dot = QLabel("●")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #333344; background: transparent;")

        self._ip_label = QLabel("Определение IP...")
        self._ip_label.setStyleSheet("font-size: 11px; color: #555566; background: transparent;")

        ip_bl.addWidget(self._ip_dot)
        ip_bl.addWidget(self._ip_label)
        hl.addWidget(ip_badge)

        return header

    def _build_content(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {DARK_BG};")

        self.full_tab     = FullCheckTab(self.result_queue,
                                         on_check_complete=self._on_check_complete)
        self.custom_tab   = CustomCheckTab(self.result_queue)
        self.history_tab  = HistoryTab()
        self.settings_tab = SettingsTab(on_save=self._on_settings_saved)

        for widget in (self.full_tab, self.custom_tab,
                       self.history_tab, self.settings_tab):
            self._stack.addWidget(widget)

        self._tab_widgets = {
            _TAB_NAMES[0]: self.full_tab,
            _TAB_NAMES[1]: self.custom_tab,
            _TAB_NAMES[2]: self.history_tab,
            _TAB_NAMES[3]: self.settings_tab,
        }

        self._switch_tab(_TAB_NAMES[0])
        return self._stack

    # ── Tab switching ──────────────────────────────────────────────────────────

    def _switch_tab(self, name: str) -> None:
        self._stack.setCurrentWidget(self._tab_widgets[name])
        for n, btn in self._tab_btns.items():
            btn.setStyleSheet(_BTN_ACTIVE if n == name else _BTN_INACTIVE)

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _on_check_complete(self, verdict: dict, service_results: list) -> None:
        from engine.history import save_result
        save_result(verdict, service_results, ip_info=self._current_ip_info)
        self.history_tab.refresh()

    def _on_settings_saved(self) -> None:
        self.full_tab.reload_services()

    # ── IP fetch ───────────────────────────────────────────────────────────────

    def _fetch_ip_async(self) -> None:
        threading.Thread(target=self._fetch_ip, daemon=True).start()

    def _fetch_ip(self) -> None:
        try:
            r = requests.get("https://ipapi.co/json/", timeout=6,
                             headers={"User-Agent": "VPNChecker/1.0"})
            d = r.json()
            ip   = d.get("ip", "?")
            city = d.get("city", "")
            country = d.get("country_name", "?")
            location = f"{city}, {country}" if city else country
            text = f"{ip} — {location}"
            self._current_ip_info = text
            self._ip_ready.emit(text)
        except Exception:
            self._ip_failed.emit()

    def _update_ip_ok(self, text: str) -> None:
        self._ip_label.setText(text)
        self._ip_label.setStyleSheet("font-size: 11px; color: #9090cc; background: transparent;")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #4CAF50; background: transparent;")

    def _update_ip_fail(self) -> None:
        self._ip_label.setText("IP не определён")
        self._ip_label.setStyleSheet("font-size: 11px; color: #664444; background: transparent;")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #F44336; background: transparent;")

    # ── Queue poll ─────────────────────────────────────────────────────────────

    def _poll_queue(self) -> None:
        try:
            while True:
                msg = self.result_queue.get_nowait()
                self.full_tab.handle_result(msg)
                self.custom_tab.handle_result(msg)
        except queue.Empty:
            pass
