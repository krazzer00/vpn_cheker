# tabs/settings.py
from typing import Callable, Optional

import theme
from theme import COLOR_OK, COLOR_MUTED

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QScrollArea, QLineEdit,
                              QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer

from engine.config import load_services, save_services

_CATEGORIES  = ["AI", "Media", "Social", "Other"]
_CHECK_TYPES = ["http", "ai_region"]


class SettingsTab(QWidget):
    def __init__(self,
                 on_save: Optional[Callable] = None,
                 on_theme_change: Optional[Callable[[str], None]] = None,
                 parent=None):
        super().__init__(parent)
        self._on_save = on_save
        self._on_theme_change = on_theme_change
        self._rows: list[dict] = []
        self._current_theme_name = theme.load_theme_name()
        self._build()
        self._load()

    # ── Build ──────────────────────────────────────────────────────────────────

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
        tl = QHBoxLayout(top)
        tl.setContentsMargins(16, 0, 12, 0)
        tl.setSpacing(8)

        title = QLabel("Настройки сервисов")
        title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        tl.addWidget(title)
        tl.addStretch()

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
        tl.addWidget(add_btn)

        self._save_btn = QPushButton("💾 Сохранить")
        self._save_btn.setFixedSize(120, 30)
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {theme._lighten(theme.ACCENT)}; }}
        """)
        self._save_btn.clicked.connect(self._save)
        tl.addWidget(self._save_btn)
        layout.addWidget(top)

        # ── Theme selector row ────────────────────────────────────────────────
        theme_bar = QFrame()
        theme_bar.setFixedHeight(52)
        theme_bar.setStyleSheet(
            f"QFrame {{ background: {theme.CARD_BG};"
            f" border-bottom: 1px solid {theme.BORDER}; border-radius: 0; }}"
        )
        theme_layout = QHBoxLayout(theme_bar)
        theme_layout.setContentsMargins(16, 0, 16, 0)
        theme_layout.setSpacing(12)

        theme_icon = QLabel("🎨")
        theme_icon.setStyleSheet("font-size: 16px; background: transparent;")
        theme_lbl = QLabel("Тема оформления")
        theme_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #cccccc; background: transparent;"
        )
        theme_layout.addWidget(theme_icon)
        theme_layout.addWidget(theme_lbl)
        theme_layout.addStretch()

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(list(theme.THEMES.keys()))
        idx = self._theme_combo.findText(self._current_theme_name)
        self._theme_combo.setCurrentIndex(max(idx, 0))
        self._theme_combo.setFixedWidth(150)
        self._theme_combo.setStyleSheet(f"""
            QComboBox {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 4px 10px; font-size: 12px;
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
        """)
        # Live QSS preview on selection change
        self._theme_combo.currentTextChanged.connect(theme.preview_theme)
        theme_layout.addWidget(self._theme_combo)

        layout.addWidget(theme_bar)

        # ── Column headers ────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(28)
        hdr.setStyleSheet(f"background: {theme.DARK_BG};")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(14, 0, 14, 0)
        hdr_layout.setSpacing(4)
        for text, w in [("Вкл", 52), ("Иконка", 60), ("Название", 140),
                        ("URL", 240), ("Категория", 100), ("Тип", 90), ("", 40)]:
            lbl = QLabel(text)
            lbl.setFixedWidth(w)
            lbl.setStyleSheet(
                f"font-size: 10px; font-weight: bold; color: {COLOR_MUTED};"
                f" background: transparent;"
            )
            hdr_layout.addWidget(lbl)
        hdr_layout.addStretch()
        layout.addWidget(hdr)

        # ── Services scroll area ──────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {theme.DARK_BG}; border: none; }}"
        )
        self._scroll.viewport().setStyleSheet(f"background: {theme.DARK_BG};")
        layout.addWidget(self._scroll, 1)

    # ── Services CRUD ──────────────────────────────────────────────────────────

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
        content.setStyleSheet(f"background: {theme.DARK_BG};")
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
            f"QFrame {{ background: {theme.CARD_BG}; border: 1px solid {theme.BORDER};"
            f" border-radius: 8px; }}"
        )

        rl = QHBoxLayout(row_frame)
        rl.setContentsMargins(8, 6, 8, 6)
        rl.setSpacing(4)

        enabled_cb = QCheckBox()
        enabled_cb.setChecked(svc.get("enabled", True))
        enabled_cb.setFixedWidth(44)
        enabled_cb.setStyleSheet(f"""
            QCheckBox {{ background: transparent; spacing: 0; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1px solid {theme.BORDER}; border-radius: 4px;
                background: {theme.DARKER_BG};
            }}
            QCheckBox::indicator:checked {{
                background: {theme.ACCENT}; border-color: {theme.ACCENT};
            }}
        """)
        rl.addWidget(enabled_cb)

        icon_e = QLineEdit(svc.get("icon", ""))
        icon_e.setFixedSize(52, 36)
        icon_e.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 2px 6px; font-size: 16px;
            }}
        """)
        rl.addWidget(icon_e)

        name_e = QLineEdit(svc.get("name", ""))
        name_e.setFixedSize(136, 36)
        name_e.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 12px;
            }}
        """)
        rl.addWidget(name_e)

        url_e = QLineEdit(svc.get("url", ""))
        url_e.setFixedSize(236, 36)
        url_e.setStyleSheet(f"""
            QLineEdit {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(url_e)

        cat_dd = QComboBox()
        cat_dd.addItems(_CATEGORIES)
        cat_dd.setCurrentIndex(max(cat_dd.findText(svc.get("category", "Other")), 0))
        cat_dd.setFixedSize(96, 36)
        cat_dd.setStyleSheet(f"""
            QComboBox {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(cat_dd)

        type_dd = QComboBox()
        type_dd.addItems(_CHECK_TYPES)
        type_dd.setCurrentIndex(max(type_dd.findText(svc.get("check_type", "http")), 0))
        type_dd.setFixedSize(86, 36)
        type_dd.setStyleSheet(f"""
            QComboBox {{
                background: {theme.DARKER_BG}; color: #cccccc;
                border: 1px solid {theme.BORDER}; border-radius: 6px;
                padding: 2px 8px; font-size: 11px;
            }}
        """)
        rl.addWidget(type_dd)

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
        self._add_row({
            "id":         f"custom_{len(self._rows)}",
            "name":       "Новый сервис",
            "icon":       "🌐",
            "category":   "Other",
            "url":        "https://",
            "check_type": "http",
            "enabled":    True,
        })

    def _delete_row(self, frame: QFrame) -> None:
        self._rows = [r for r in self._rows if r["frame"] is not frame]
        frame.deleteLater()

    def _save(self) -> None:
        # Save services
        services = []
        for r in self._rows:
            url = r["url"].text().strip()
            services.append({
                "id":         r["id"] or r["name"].text().lower().replace(" ", "_"),
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

        # Handle theme change
        selected_theme = self._theme_combo.currentText()
        theme_changed = selected_theme != self._current_theme_name
        if theme_changed:
            self._current_theme_name = selected_theme
            # Apply and persist; schedule rebuild so this click handler returns first
            theme.apply_theme(selected_theme, save=True)
            if self._on_theme_change:
                QTimer.singleShot(50, lambda: self._on_theme_change(selected_theme))
                return  # rebuild will recreate this tab; skip button reset

        # Flash save button
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
                background: {theme.ACCENT}; color: white;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {theme._lighten(theme.ACCENT)}; }}
        """)
