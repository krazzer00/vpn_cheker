# tabs/settings.py
from typing import Callable, Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QLineEdit,
                              QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer

from engine.config import load_services, save_services
from theme import DARK_BG, DARKER_BG, CARD_BG, BORDER, COLOR_OK, COLOR_BAD, COLOR_MUTED, ACCENT

_CATEGORIES = ["AI", "Media", "Social", "Other"]
_CHECK_TYPES = ["http", "ai_region"]


class SettingsTab(QWidget):
    def __init__(self, on_save: Optional[Callable] = None, parent=None):
        super().__init__(parent)
        self._on_save = on_save
        self._rows: list[dict] = []
        self._build()
        self._load()

    def _build(self) -> None:
        self.setStyleSheet(f"background: {DARK_BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        top = QFrame()
        top.setFixedHeight(48)
        top.setStyleSheet(
            f"QFrame {{ background: {DARKER_BG}; border-bottom: 1px solid {BORDER};"
            f" border-radius: 0; }}"
        )
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 0, 12, 0)
        top_layout.setSpacing(8)

        title = QLabel("Настройки сервисов")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        top_layout.addWidget(title)
        top_layout.addStretch()

        add_btn = QPushButton("+ Добавить")
        add_btn.setFixedSize(100, 30)
        add_btn.setStyleSheet("""
            QPushButton {
                background: #1e2e1e; color: #4CAF50;
                border: none; border-radius: 8px; font-size: 12px;
            }
            QPushButton:hover { background: #2e4e2e; }
        """)
        add_btn.clicked.connect(self._add_service)
        top_layout.addWidget(add_btn)

        self._save_btn = QPushButton("💾 Сохранить")
        self._save_btn.setFixedSize(120, 30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #7b8ef5; }}
        """)
        self._save_btn.clicked.connect(self._save)
        top_layout.addWidget(self._save_btn)
        layout.addWidget(top)

        # Column headers
        hdr = QWidget()
        hdr.setFixedHeight(28)
        hdr.setStyleSheet(f"background: {DARK_BG};")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(14, 0, 14, 0)
        hdr_layout.setSpacing(4)
        for text, w in [("Вкл", 52), ("Иконка", 60), ("Название", 140),
                        ("URL", 240), ("Категория", 100), ("Тип", 90), ("", 40)]:
            lbl = QLabel(text)
            lbl.setFixedWidth(w)
            lbl.setStyleSheet(
                f"font-size: 10px; font-weight: bold; color: {COLOR_MUTED}; background: transparent;"
            )
            hdr_layout.addWidget(lbl)
        hdr_layout.addStretch()
        layout.addWidget(hdr)

        # Scroll area for rows
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {DARK_BG}; border: none; }}"
        )
        self._scroll.viewport().setStyleSheet(f"background: {DARK_BG};")
        layout.addWidget(self._scroll, 1)

    def _load(self) -> None:
        self._rows.clear()
        services = load_services()
        self._rebuild_scroll(services)

    def _rebuild_scroll(self, services: list[dict]) -> None:
        old = self._scroll.takeWidget()
        if old:
            old.deleteLater()
        self._rows.clear()

        content = QWidget()
        content.setStyleSheet(f"background: {DARK_BG};")
        self._vlay = QVBoxLayout(content)
        self._vlay.setContentsMargins(14, 10, 14, 10)
        self._vlay.setSpacing(4)
        self._vlay.addStretch()

        self._scroll.setWidget(content)
        for svc in services:
            self._add_row(svc)

    def _add_row(self, svc: dict) -> None:
        row_frame = QFrame()
        row_frame.setFixedHeight(52)
        row_frame.setStyleSheet(
            f"QFrame {{ background: {CARD_BG}; border: 1px solid {BORDER};"
            f" border-radius: 8px; }}"
        )

        rl = QHBoxLayout(row_frame)
        rl.setContentsMargins(8, 6, 8, 6)
        rl.setSpacing(4)

        # Enabled checkbox
        enabled_cb = QCheckBox()
        enabled_cb.setChecked(svc.get("enabled", True))
        enabled_cb.setFixedWidth(44)
        enabled_cb.setStyleSheet(f"""
            QCheckBox {{ background: transparent; spacing: 0; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1px solid {BORDER}; border-radius: 4px;
                background: {DARKER_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {ACCENT}; border-color: {ACCENT};
            }}
        """)
        rl.addWidget(enabled_cb)

        # Icon entry
        icon_e = QLineEdit(svc.get("icon", ""))
        icon_e.setFixedSize(52, 36)
        icon_e.setStyleSheet(f"""
            QLineEdit {{
                background: {DARKER_BG}; color: #cccccc;
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 2px 6px; font-size: 16px;
            }}
        """)
        rl.addWidget(icon_e)

        # Name entry
        name_e = QLineEdit(svc.get("name", ""))
        name_e.setFixedSize(136, 36)
        name_e.setStyleSheet(f"""
            QLineEdit {{
                background: {DARKER_BG}; color: #cccccc;
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 12px;
            }}
        """)
        rl.addWidget(name_e)

        # URL entry
        url_e = QLineEdit(svc.get("url", ""))
        url_e.setFixedSize(236, 36)
        url_e.setStyleSheet(f"""
            QLineEdit {{
                background: {DARKER_BG}; color: #cccccc;
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(url_e)

        # Category dropdown
        cat_dd = QComboBox()
        cat_dd.addItems(_CATEGORIES)
        idx = cat_dd.findText(svc.get("category", "Other"))
        cat_dd.setCurrentIndex(max(idx, 0))
        cat_dd.setFixedSize(96, 36)
        cat_dd.setStyleSheet(f"""
            QComboBox {{
                background: {DARKER_BG}; color: #cccccc;
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(cat_dd)

        # Check type dropdown
        type_dd = QComboBox()
        type_dd.addItems(_CHECK_TYPES)
        idx = type_dd.findText(svc.get("check_type", "http"))
        type_dd.setCurrentIndex(max(idx, 0))
        type_dd.setFixedSize(86, 36)
        type_dd.setStyleSheet(f"""
            QComboBox {{
                background: {DARKER_BG}; color: #cccccc;
                border: 1px solid {BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(type_dd)

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(32, 28)
        del_btn.setStyleSheet("""
            QPushButton {
                background: #2e0a0a; color: #F44336;
                border: none; border-radius: 6px;
                font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #4e1a1a; }
        """)
        del_btn.clicked.connect(lambda: self._delete_row(row_frame))
        rl.addWidget(del_btn)
        rl.addStretch()

        # Insert before the trailing stretch
        self._vlay.insertWidget(self._vlay.count() - 1, row_frame)

        self._rows.append({
            "frame":      row_frame,
            "id":         svc.get("id", ""),
            "enabled":    enabled_cb,
            "icon":       icon_e,
            "name":       name_e,
            "url":        url_e,
            "category":   cat_dd,
            "check_type": type_dd,
        })

    def _add_service(self) -> None:
        new_svc = {
            "id": f"custom_{len(self._rows)}",
            "name": "Новый сервис",
            "icon": "🌐",
            "category": "Other",
            "url": "https://",
            "check_type": "http",
            "enabled": True,
        }
        self._add_row(new_svc)

    def _delete_row(self, frame: QFrame) -> None:
        self._rows = [r for r in self._rows if r["frame"] is not frame]
        frame.deleteLater()

    def _save(self) -> None:
        services = []
        for r in self._rows:
            url = r["url"].text().strip()
            services.append({
                "id": r["id"] or r["name"].text().lower().replace(" ", "_"),
                "name":       r["name"].text().strip(),
                "icon":       r["icon"].text().strip() or "🌐",
                "category":   r["category"].currentText(),
                "url":        url,
                "check_url":  url,
                "check_type": r["check_type"].currentText(),
                "port":       443,
                "enabled":    r["enabled"].isChecked(),
            })
        save_services(services)
        self._save_btn.setText("✓ Сохранено")
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: #1e3e1e; color: {COLOR_OK};
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }}
        """)
        QTimer.singleShot(2000, self._reset_save_btn)
        if self._on_save:
            self._on_save()

    def _reset_save_btn(self) -> None:
        self._save_btn.setText("💾 Сохранить")
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #7b8ef5; }}
        """)
