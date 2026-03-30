# tabs/history.py
import theme
from theme import COLOR_MUTED, TIER_COLORS

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea)
from PyQt5.QtCore import Qt

from engine.history import load_history, clear_history


class HistoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self) -> None:
        self.setStyleSheet(f"background: {theme.DARK_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top = QFrame()
        top.setFixedHeight(48)
        top.setStyleSheet(
            f"QFrame {{ background: {theme.DARKER_BG};"
            f" border-bottom: 1px solid {theme.BORDER}; border-radius: 0; }}"
        )
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 0, 12, 0)

        title = QLabel("История проверок")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        top_layout.addWidget(title)
        top_layout.addStretch()

        clear_btn = QPushButton("Очистить")
        clear_btn.setFixedSize(90, 28)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #2e1a1a; color: #cc6666;
                border: none; border-radius: 6px; font-size: 11px;
            }
            QPushButton:hover { background: #4e2a2a; }
        """)
        clear_btn.clicked.connect(self._clear)
        top_layout.addWidget(clear_btn)
        layout.addWidget(top)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {theme.DARK_BG}; border: none; }}"
        )
        self._scroll.viewport().setStyleSheet(f"background: {theme.DARK_BG};")
        layout.addWidget(self._scroll, 1)

    def refresh(self) -> None:
        old = self._scroll.takeWidget()
        if old:
            old.deleteLater()

        content = QWidget()
        content.setStyleSheet(f"background: {theme.DARK_BG};")
        vlay = QVBoxLayout(content)
        vlay.setContentsMargins(14, 10, 14, 10)
        vlay.setSpacing(4)

        records = load_history()

        if not records:
            empty = QLabel(
                "Ещё не было ни одной проверки.\n"
                "Запусти полную проверку и результаты появятся здесь."
            )
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"font-size: 13px; color: {COLOR_MUTED}; background: transparent;"
            )
            vlay.addStretch()
            vlay.addWidget(empty, alignment=Qt.AlignCenter)
            vlay.addStretch()
        else:
            for record in records:
                vlay.addWidget(self._make_row(record))
            vlay.addStretch()

        self._scroll.setWidget(content)

    def _make_row(self, record: dict) -> QFrame:
        tier_color = TIER_COLORS.get(record.get("tier", "F"), "#F44336")

        row = QFrame()
        row.setFixedHeight(88)
        row.setStyleSheet(
            f"QFrame {{ background: {theme.CARD_BG}; border: 1px solid {theme.BORDER};"
            f" border-radius: 10px; }}"
        )

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 16, 0)
        row_layout.setSpacing(0)

        # Tier color accent strip
        accent = QFrame()
        accent.setFixedWidth(4)
        accent.setStyleSheet(
            f"QFrame {{ background: {tier_color}; border: none; border-radius: 0; }}"
        )
        row_layout.addWidget(accent)

        # Content
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(12, 10, 0, 10)
        cl.setSpacing(3)

        ts = record.get("timestamp", "?")
        ip_info = record.get("ip_info", "")
        header_text = f"{ts}   •   {ip_info}" if ip_info else ts

        header_lbl = QLabel(header_text)
        header_lbl.setStyleSheet(
            f"font-size: 10px; color: {COLOR_MUTED}; background: transparent;"
        )
        msg_lbl = QLabel(record.get("message", ""))
        msg_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {tier_color}; background: transparent;"
        )
        accessible = record.get("accessible_count", 0)
        total      = record.get("total_count", 0)
        count_lbl  = QLabel(f"Доступно {accessible} из {total} сервисов")
        count_lbl.setStyleSheet(
            f"font-size: 11px; color: {COLOR_MUTED}; background: transparent;"
        )

        cl.addWidget(header_lbl)
        cl.addWidget(msg_lbl)
        cl.addWidget(count_lbl)
        row_layout.addWidget(content, 1)

        score_lbl = QLabel(f"{record.get('score', 0)}/10")
        score_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {tier_color}; background: transparent;"
        )
        score_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row_layout.addWidget(score_lbl)

        return row

    def _clear(self) -> None:
        clear_history()
        self.refresh()
