# app.py
import queue
import threading

import theme

from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                              QPushButton, QLabel, QFrame, QStackedWidget,
                              QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
import requests

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab
from tabs.history import HistoryTab
from tabs.settings import SettingsTab

_TAB_NAMES = [
    "🛡  Полная проверка",
    "🔍  Кастомная",
    "📋  История",
    "⚙️  Настройки",
]


def _btn_style(active: bool) -> str:
    if active:
        return f"""
            QPushButton {{
                background: {theme.ACCENT}; color: white; border: none;
                border-radius: 0; padding: 0 16px;
                font-size: 12px; font-weight: bold; height: 38px;
            }}
        """
    return f"""
        QPushButton {{
            background: transparent; color: #666677; border: none;
            border-radius: 0; padding: 0 16px;
            font-size: 12px; height: 38px;
        }}
        QPushButton:hover {{ background: {theme.DARKER_BG}; color: #cccccc; }}
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
        self._ip_fetching: bool = False

        self._ip_ready.connect(self._update_ip_ok)
        self._ip_failed.connect(self._update_ip_fail)

        self._build()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_queue)
        self._poll_timer.start(100)

        QTimer.singleShot(200, self._fetch_ip_async)

    # ── Layout ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background: {theme.DARK_BG};")
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
            f"QFrame {{ background: {theme.DARKER_BG};"
            f" border-bottom: 1px solid {theme.BORDER}; border-radius: 0; }}"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(4, 3, 12, 3)
        hl.setSpacing(1)

        self._tab_btns: dict[str, QPushButton] = {}
        for name in _TAB_NAMES:
            btn = QPushButton(name)
            btn.setFixedHeight(38)
            btn.setStyleSheet(_btn_style(False))
            btn.clicked.connect(lambda checked, n=name: self._switch_tab(n))
            hl.addWidget(btn)
            self._tab_btns[name] = btn

        hl.addStretch()

        # ── IP badge ──────────────────────────────────────────────────────────
        ip_badge = QFrame()
        ip_badge.setStyleSheet(
            f"QFrame {{ background: #1e1e2e; border: 1px solid {theme.BORDER};"
            f" border-radius: 12px; }}"
        )
        ip_bl = QHBoxLayout(ip_badge)
        ip_bl.setContentsMargins(10, 3, 6, 3)
        ip_bl.setSpacing(4)

        self._ip_dot = QLabel("●")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #333344; background: transparent;")

        self._ip_label = QLabel("Определение IP...")
        self._ip_label.setStyleSheet("font-size: 11px; color: #555566; background: transparent;")

        # Manual refresh button
        self._ip_refresh_btn = QPushButton("⟳")
        self._ip_refresh_btn.setFixedSize(22, 22)
        self._ip_refresh_btn.setToolTip("Обновить IP")
        self._ip_refresh_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #555566;
                border: none; border-radius: 4px;
                font-size: 13px; padding: 0;
            }
            QPushButton:hover { color: #aaaacc; background: #2a2a3a; }
        """)
        self._ip_refresh_btn.clicked.connect(self._fetch_ip_async)

        ip_bl.addWidget(self._ip_dot)
        ip_bl.addWidget(self._ip_label)
        ip_bl.addWidget(self._ip_refresh_btn)
        hl.addWidget(ip_badge)

        return header

    def _build_content(self) -> QStackedWidget:
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {theme.DARK_BG};")
        self._create_tabs()
        self._switch_tab(_TAB_NAMES[0])
        return self._stack

    def _create_tabs(self) -> None:
        self.full_tab = FullCheckTab(
            self.result_queue, on_check_complete=self._on_check_complete
        )
        self.custom_tab   = CustomCheckTab(self.result_queue)
        self.history_tab  = HistoryTab()
        self.settings_tab = SettingsTab(
            on_save=self._on_settings_saved,
            on_theme_change=self._on_theme_change,
        )

        for widget in (self.full_tab, self.custom_tab,
                       self.history_tab, self.settings_tab):
            self._stack.addWidget(widget)

        self._tab_widgets = {
            _TAB_NAMES[0]: self.full_tab,
            _TAB_NAMES[1]: self.custom_tab,
            _TAB_NAMES[2]: self.history_tab,
            _TAB_NAMES[3]: self.settings_tab,
        }

    # ── Tab switching ──────────────────────────────────────────────────────────

    def _switch_tab(self, name: str) -> None:
        widget = self._tab_widgets.get(name)
        if widget:
            self._stack.setCurrentWidget(widget)
        for n, btn in self._tab_btns.items():
            btn.setStyleSheet(_btn_style(n == name))
        self._current_tab = name

    # ── Theme rebuild ──────────────────────────────────────────────────────────

    def _on_theme_change(self, name: str) -> None:
        """Called after theme.apply_theme() already ran in SettingsTab._save()."""
        # Update application-wide styles
        app = QApplication.instance()
        app.setStyleSheet(theme.APP_STYLE)

        # Update palette to match new accent
        pal = app.palette()
        pal.setColor(QPalette.Highlight,       QColor(theme.ACCENT))
        pal.setColor(QPalette.Window,          QColor(theme.DARK_BG))
        pal.setColor(QPalette.Base,            QColor(theme.DARKER_BG))
        pal.setColor(QPalette.AlternateBase,   QColor(theme.CARD_BG))
        pal.setColor(QPalette.Button,          QColor(theme.CARD_BG))
        app.setPalette(pal)

        # Rebuild all tabs with new theme colors
        current_name = getattr(self, "_current_tab", _TAB_NAMES[0])

        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()

        self._create_tabs()
        # Restore to settings tab so user can see the result
        restore = current_name if current_name in self._tab_widgets else _TAB_NAMES[3]
        self._switch_tab(restore)

        # Update header styling
        central = self.centralWidget()
        if central and central.layout():
            header_item = central.layout().itemAt(0)
            if header_item and header_item.widget():
                header_item.widget().setStyleSheet(
                    f"QFrame {{ background: {theme.DARKER_BG};"
                    f" border-bottom: 1px solid {theme.BORDER}; border-radius: 0; }}"
                )

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _on_check_complete(self, verdict: dict, service_results: list) -> None:
        from engine.history import save_result
        save_result(verdict, service_results, ip_info=self._current_ip_info)
        self.history_tab.refresh()
        # Refresh IP/location after each check (VPN may have changed)
        self._fetch_ip_async()

    def _on_settings_saved(self) -> None:
        self.full_tab.reload_services()

    # ── IP fetch ───────────────────────────────────────────────────────────────

    def _fetch_ip_async(self) -> None:
        if self._ip_fetching:
            return
        self._ip_fetching = True
        self._ip_label.setText("Обновление...")
        self._ip_label.setStyleSheet("font-size: 11px; color: #555566; background: transparent;")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #333344; background: transparent;")
        threading.Thread(target=self._fetch_ip, daemon=True).start()

    def _fetch_ip(self) -> None:
        try:
            r = requests.get("https://ipapi.co/json/", timeout=6,
                             headers={"User-Agent": "VPNChecker/1.0"})
            d = r.json()
            ip      = d.get("ip", "?")
            city    = d.get("city", "")
            country = d.get("country_name", "?")
            location = f"{city}, {country}" if city else country
            text = f"{ip} — {location}"
            self._current_ip_info = text
            self._ip_ready.emit(text)
        except Exception:
            self._ip_failed.emit()

    def _update_ip_ok(self, text: str) -> None:
        self._ip_fetching = False
        self._ip_label.setText(text)
        self._ip_label.setStyleSheet("font-size: 11px; color: #9090cc; background: transparent;")
        self._ip_dot.setStyleSheet("font-size: 10px; color: #4CAF50; background: transparent;")

    def _update_ip_fail(self) -> None:
        self._ip_fetching = False
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
