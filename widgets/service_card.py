# widgets/service_card.py
import itertools

from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                              QSizePolicy)
from PyQt5.QtCore import Qt

from theme import CARD_BG, BORDER, COLOR_MUTED, COLOR_OK, COLOR_WARN, COLOR_BAD, COLOR_CHECKING

_counter = itertools.count()


def _ping_color(ping_ms):
    if ping_ms is None:
        return COLOR_MUTED
    if ping_ms < 80:
        return COLOR_OK
    if ping_ms < 180:
        return COLOR_WARN
    return COLOR_BAD


def _loss_color(loss_pct):
    if loss_pct is None or loss_pct == 0:
        return COLOR_OK
    if loss_pct < 10:
        return COLOR_WARN
    return COLOR_BAD


class ServiceCard(QFrame):
    """
    Dashboard-style card for one service.
    Layout: accent-left-border + icon/name/status + metrics (ping · loss · region)
    """

    def __init__(self, service: dict, parent=None):
        super().__init__(parent)
        self._service = service
        self._oid = f"scard_{next(_counter)}"
        self.setObjectName(self._oid)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._set_accent(COLOR_CHECKING)
        self._build()

    # ── Accent border ──────────────────────────────────────────────────────────

    def _set_accent(self, color: str) -> None:
        self.setStyleSheet(f"""
            #{self._oid} {{
                background: {CARD_BG};
                border-top: 1px solid {BORDER};
                border-right: 1px solid {BORDER};
                border-bottom: 1px solid {BORDER};
                border-left: 4px solid {color};
                border-radius: 10px;
            }}
        """)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 14, 10)
        outer.setSpacing(6)

        # Top row: icon + name  /  status
        top = QHBoxLayout()
        top.setSpacing(6)

        self._name_lbl = QLabel(
            self._service.get("icon", "🌐") + "  " + self._service.get("name", "")
        )
        self._name_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #c8c8dc;")

        self._status_lbl = QLabel("● Ожидание")
        self._status_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: #3a3a55;")
        self._status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        top.addWidget(self._name_lbl, 1)
        top.addWidget(self._status_lbl)
        outer.addLayout(top)

        # Metrics row
        metrics = QHBoxLayout()
        metrics.setSpacing(0)
        metrics.setContentsMargins(0, 0, 0, 0)

        self._ping_val, self._ping_cap = self._make_metric("—", "мс  пинг")
        metrics.addLayout(self._metric_col(self._ping_val, self._ping_cap))
        metrics.addWidget(self._vdivider())

        self._loss_val, self._loss_cap = self._make_metric("—", "потери")
        metrics.addLayout(self._metric_col(self._loss_val, self._loss_cap))
        metrics.addWidget(self._vdivider())

        self._region_val, self._region_cap = self._make_metric("—", "регион")
        metrics.addLayout(self._metric_col(self._region_val, self._region_cap))
        metrics.addStretch()

        outer.addLayout(metrics)

    def _make_metric(self, value: str, caption: str):
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_MUTED};")
        cap = QLabel(caption)
        cap.setStyleSheet("font-size: 9px; color: #3a3a52;")
        return val, cap

    def _metric_col(self, val_lbl: QLabel, cap_lbl: QLabel) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(0)
        col.setContentsMargins(0, 0, 10, 0)
        col.addWidget(val_lbl)
        col.addWidget(cap_lbl)
        return col

    def _vdivider(self) -> QFrame:
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setFixedWidth(1)
        div.setStyleSheet(f"background: #232333; border: none;")
        return div

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_checking(self) -> None:
        self._set_accent(COLOR_CHECKING)
        self._status_lbl.setText("● Проверка")
        self._status_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {COLOR_CHECKING};")
        for lbl in (self._ping_val, self._loss_val, self._region_val):
            lbl.setText("…")
            lbl.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_CHECKING};")

    def update_result(self, result: dict) -> None:
        accessible = result.get("accessible", False)
        ping_ms = result.get("ping_ms")
        loss_pct = result.get("loss_pct")
        region = result.get("region_accessible")

        color = COLOR_OK if accessible else COLOR_BAD
        self._set_accent(color)
        self._status_lbl.setText("● Доступен" if accessible else "● Недоступен")
        self._status_lbl.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {color};")

        # Ping
        if ping_ms is not None:
            self._ping_val.setText(f"{ping_ms:.0f}")
            self._ping_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {_ping_color(ping_ms)};")
        else:
            self._ping_val.setText("—")
            self._ping_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_MUTED};")

        # Loss
        if loss_pct is None:
            self._loss_val.setText("н/п")
            self._loss_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_MUTED};")
        else:
            self._loss_val.setText(f"{loss_pct:.1f}%")
            self._loss_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {_loss_color(loss_pct)};")

        # Region
        if region is None:
            self._region_val.setText("—")
            self._region_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_MUTED};")
        elif region:
            self._region_val.setText("✓")
            self._region_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_OK};")
        else:
            self._region_val.setText("✗")
            self._region_val.setStyleSheet(f"font-size: 21px; font-weight: bold; color: {COLOR_BAD};")
