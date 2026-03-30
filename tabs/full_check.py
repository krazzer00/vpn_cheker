# tabs/full_check.py
import queue
import threading
from typing import Optional, Callable

import theme
from theme import COLOR_MUTED, TIER_COLORS

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QGridLayout,
                              QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt

from engine.checker import run_checks
from engine.config import load_services as _load_services_from_config
from widgets.service_card import ServiceCard
from widgets.speed_bar import SpeedBar


class FullCheckTab(QWidget):
    def __init__(self, result_queue: queue.Queue,
                 on_check_complete: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self.result_queue = result_queue
        self._on_check_complete = on_check_complete
        self.all_services: list[dict] = []
        self.cards: dict[str, ServiceCard] = {}
        self._selected: set[str] = set()
        self._running = False
        self._service_results: list[dict] = []

        self._load_services()
        self._build()
        self._build_all_cards()

    # ── Service loading ────────────────────────────────────────────────────────

    def _load_services(self) -> None:
        self.all_services = [s for s in _load_services_from_config()
                             if s.get("enabled", True)]
        self._selected = {s["id"] for s in self.all_services}

    def reload_services(self) -> None:
        self._load_services()
        self._populate_sidebar()
        self._build_all_cards()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"QFrame {{ background: {theme.DARKER_BG};"
            f" border-right: 1px solid {theme.BORDER}; border-radius: 0; }}"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self._sidebar_scroll = QScrollArea()
        self._sidebar_scroll.setWidgetResizable(True)
        self._sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._sidebar_scroll.setStyleSheet(
            f"QScrollArea {{ background: {theme.DARKER_BG}; border: none; }}"
        )
        self._sidebar_scroll.viewport().setStyleSheet(f"background: {theme.DARKER_BG};")
        sidebar_layout.addWidget(self._sidebar_scroll, 1)

        self.run_btn = QPushButton("▶  Запустить")
        self.run_btn.setFixedHeight(40)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.ACCENT}; color: white; border: none;
                border-radius: 9px; font-size: 13px; font-weight: bold;
                margin: 10px;
            }}
            QPushButton:hover {{ background: {theme._lighten(theme.ACCENT)}; }}
            QPushButton:disabled {{ background: {theme.BORDER}; color: {COLOR_MUTED}; margin: 10px; }}
        """)
        self.run_btn.clicked.connect(self._start_check)
        sidebar_layout.addWidget(self.run_btn)

        layout.addWidget(sidebar)

        # ── Right panel ───────────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet(f"background: {theme.DARK_BG};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(8)

        self.speed_bar = SpeedBar()
        right_layout.addWidget(self.speed_bar)

        self._cards_scroll = QScrollArea()
        self._cards_scroll.setWidgetResizable(True)
        self._cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cards_scroll.setStyleSheet(
            f"QScrollArea {{ background: {theme.DARK_BG}; border: none; }}"
        )
        self._cards_scroll.viewport().setStyleSheet(f"background: {theme.DARK_BG};")
        right_layout.addWidget(self._cards_scroll, 1)

        self._build_verdict(right_layout)
        layout.addWidget(right, 1)

        self._populate_sidebar()

    def _populate_sidebar(self) -> None:
        old = self._sidebar_scroll.takeWidget()
        if old:
            old.deleteLater()

        content = QWidget()
        content.setStyleSheet(f"background: {theme.DARKER_BG};")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(8, 8, 8, 8)
        vlay.setSpacing(2)

        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        self._checkboxes: dict[str, QCheckBox] = {}
        for cat, services in categories.items():
            lbl = QLabel(cat.upper())
            lbl.setStyleSheet(
                f"font-size: 9px; font-weight: bold; color: {COLOR_MUTED};"
                f" background: transparent; padding: 8px 4px 2px 4px;"
            )
            vlay.addWidget(lbl)
            for svc in services:
                cb = QCheckBox(svc["icon"] + "  " + svc["name"])
                cb.setChecked(svc["id"] in self._selected)
                cb.setStyleSheet(f"""
                    QCheckBox {{
                        font-size: 12px; color: #cccccc;
                        background: transparent; spacing: 6px; padding: 2px 4px;
                    }}
                    QCheckBox::indicator {{
                        width: 16px; height: 16px;
                        border: 1px solid {theme.BORDER}; border-radius: 3px;
                        background: {theme.DARKER_BG};
                    }}
                    QCheckBox::indicator:checked {{
                        background: {theme.ACCENT}; border-color: {theme.ACCENT};
                    }}
                """)
                sid = svc["id"]
                cb.toggled.connect(lambda checked, s=sid: self._toggle(s, checked))
                vlay.addWidget(cb)
                self._checkboxes[sid] = cb

        vlay.addStretch()
        self._sidebar_scroll.setWidget(content)

    def _build_verdict(self, parent_layout: QVBoxLayout) -> None:
        self.verdict_frame = QFrame()
        self.verdict_frame.setStyleSheet(
            f"QFrame {{ background: {theme.CARD_BG}; border: 1px solid {theme.BORDER};"
            f" border-radius: 10px; }}"
        )
        self.verdict_frame.setFixedHeight(80)

        vf_layout = QHBoxLayout(self.verdict_frame)
        vf_layout.setContentsMargins(18, 10, 18, 10)
        vf_layout.setSpacing(0)

        self.verdict_icon = QLabel("🛡")
        self.verdict_icon.setStyleSheet("font-size: 28px; background: transparent;")
        vf_layout.addWidget(self.verdict_icon)

        vt = QVBoxLayout()
        vt.setSpacing(2)
        vt.setContentsMargins(10, 0, 0, 0)

        self.verdict_title = QLabel("Нажми Запустить")
        self.verdict_title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        self.verdict_sub = QLabel("Выбери сервисы и запусти проверку")
        self.verdict_sub.setStyleSheet(
            f"font-size: 11px; color: {COLOR_MUTED}; background: transparent;"
        )
        vt.addWidget(self.verdict_title)
        vt.addWidget(self.verdict_sub)
        vf_layout.addLayout(vt, 1)

        self.verdict_score = QLabel("")
        self.verdict_score.setStyleSheet(
            "font-size: 34px; font-weight: bold; background: transparent;"
        )
        self.verdict_score.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        vf_layout.addWidget(self.verdict_score)

        parent_layout.addWidget(self.verdict_frame)

    # ── Cards ──────────────────────────────────────────────────────────────────

    def _build_all_cards(self) -> None:
        old = self._cards_scroll.takeWidget()
        if old:
            old.deleteLater()

        content = QWidget()
        content.setStyleSheet(f"background: {theme.DARK_BG};")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        self.cards.clear()
        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        self._grid_widgets: list[tuple[QWidget, QGridLayout]] = []

        for cat, services in categories.items():
            lbl = QLabel(cat.upper())
            lbl.setStyleSheet(
                f"font-size: 10px; font-weight: bold; color: {COLOR_MUTED};"
                " background: transparent; padding: 8px 0 4px 0;"
            )
            vlay.addWidget(lbl)

            grid_w = QWidget()
            grid_w.setStyleSheet(f"background: {theme.DARK_BG};")
            grid = QGridLayout(grid_w)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(8)

            for i, svc in enumerate(services):
                card = ServiceCard(svc)
                grid.addWidget(card, i // 3, i % 3)
                self.cards[svc["id"]] = card

            for col in range(3):
                grid.setColumnStretch(col, 1)

            vlay.addWidget(grid_w)
            self._grid_widgets.append((grid_w, grid))

        vlay.addStretch()
        self._cards_scroll.setWidget(content)
        self._refresh_card_visibility()
        self._update_card_sizes()

    def _refresh_card_visibility(self) -> None:
        for svc in self.all_services:
            card = self.cards.get(svc["id"])
            if card:
                card.setVisible(svc["id"] in self._selected)

    # ── Responsive card scaling ────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_card_sizes()

    def _update_card_sizes(self) -> None:
        if not self.cards:
            return
        # right panel = total width - sidebar (220) - right panel margins (14+14)
        content_w = max(120, self.width() - 220 - 28)
        # 3 columns with 8px gap on each side of gaps = 2×8=16px total gap
        col_w = max(120, (content_w - 16) // 3)
        # Grow subtly with window but cap so cards never dominate the screen
        card_h = min(130, max(100, int(col_w * 0.30)))
        for card in self.cards.values():
            card.setFixedHeight(card_h)

    # ── Interaction ────────────────────────────────────────────────────────────

    def _toggle(self, service_id: str, checked: bool) -> None:
        if checked:
            self._selected.add(service_id)
        else:
            self._selected.discard(service_id)
        self._refresh_card_visibility()

    def _start_check(self) -> None:
        if self._running or not self._selected:
            return
        self._running = True
        self._service_results = []
        self.run_btn.setEnabled(False)
        self.run_btn.setText("Проверка...")

        for sid in self._selected:
            card = self.cards.get(sid)
            if card:
                card.set_checking()

        services = [s for s in self.all_services if s["id"] in self._selected]
        threading.Thread(
            target=run_checks, args=(services, self.result_queue), daemon=True
        ).start()

    def handle_result(self, msg: dict) -> None:
        msg_type = msg.get("type")

        if msg_type == "service":
            card = self.cards.get(msg["id"])
            if card:
                card.update_result(msg)
            self._service_results.append(msg)

        elif msg_type == "speed":
            self.speed_bar.update_speed(msg)

        elif msg_type == "verdict":
            self._running = False
            self.run_btn.setEnabled(True)
            self.run_btn.setText("▶  Запустить снова")
            color = TIER_COLORS.get(msg["tier"], "#e0e0e0")
            self.verdict_title.setText(msg["message"])
            self.verdict_title.setStyleSheet(
                f"font-size: 15px; font-weight: bold; color: {color}; background: transparent;"
            )
            self.verdict_sub.setText(
                f"Доступно {msg['accessible_count']} из {msg['total_count']} сервисов"
            )
            self.verdict_score.setText(f"{msg['score']}/10")
            self.verdict_score.setStyleSheet(
                f"font-size: 34px; font-weight: bold; color: {color}; background: transparent;"
            )
            if self._on_check_complete:
                self._on_check_complete(msg, list(self._service_results))
