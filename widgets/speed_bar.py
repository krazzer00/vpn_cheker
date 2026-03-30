# widgets/speed_bar.py
import theme
from theme import COLOR_MUTED, COLOR_OK, COLOR_WARN, COLOR_BAD

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


def _speed_color(mbps, ok=50, warn=15):
    if mbps is None:
        return COLOR_MUTED
    return COLOR_OK if mbps >= ok else (COLOR_WARN if mbps >= warn else COLOR_BAD)


def _ping_color(ms):
    if ms is None:
        return COLOR_MUTED
    return COLOR_OK if ms < 60 else (COLOR_WARN if ms < 150 else COLOR_BAD)


class SpeedBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: {theme.DARKER_BG}; border: 1px solid {theme.BORDER};"
            f" border-radius: 10px; }}"
        )
        self.setFixedHeight(76)
        self._build()

    def _build(self) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(0)

        self.ping_val = self._item(row, "⊙  ПИНГ",    "—", "мс")
        self._divider(row)
        self.dl_val   = self._item(row, "↓  ЗАГРУЗКА", "—", "Мб/с")
        self._divider(row)
        self.ul_val   = self._item(row, "↑  ВЫГРУЗКА", "—", "Мб/с")
        self._divider(row)
        self.loss_val = self._item(row, "◈  ПОТЕРИ",   "—", "%")
        row.addStretch()

    def _item(self, layout, label: str, value: str, unit: str) -> QLabel:
        block = QVBoxLayout()
        block.setSpacing(1)
        block.setContentsMargins(22, 10, 0, 10)

        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            f"font-size: 9px; font-weight: bold; color: {COLOR_MUTED}; background: transparent;"
        )

        val_row = QHBoxLayout()
        val_row.setSpacing(0)
        val_row.setContentsMargins(0, 0, 0, 0)

        val = QLabel(value)
        val.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #ccccdd; background: transparent;"
        )
        unit_lbl = QLabel(f" {unit}")
        unit_lbl.setStyleSheet("font-size: 11px; color: #44445a; background: transparent;")
        unit_lbl.setAlignment(Qt.AlignBottom)

        val_row.addWidget(val)
        val_row.addWidget(unit_lbl)

        block.addWidget(title_lbl)
        block.addLayout(val_row)
        layout.addLayout(block)
        return val

    def _divider(self, layout) -> None:
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setFixedWidth(1)
        div.setStyleSheet(f"background: {theme.BORDER}; border: none;")
        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(8, 10, 0, 10)
        wrapper.addWidget(div)
        layout.addLayout(wrapper)

    def update_speed(self, result: dict) -> None:
        """Update only the fields present in result; None values are skipped
        so live partial updates never overwrite already-shown values."""
        dl   = result.get("download_mbps")
        ul   = result.get("upload_mbps")
        ping = result.get("ping_ms")
        loss = result.get("loss_pct")

        if dl is not None:
            self.dl_val.setText(str(dl))
            self.dl_val.setStyleSheet(
                f"font-size: 22px; font-weight: bold;"
                f" color: {_speed_color(dl, ok=50, warn=15)}; background: transparent;"
            )

        if ul is not None:
            self.ul_val.setText(str(ul))
            self.ul_val.setStyleSheet(
                f"font-size: 22px; font-weight: bold;"
                f" color: {_speed_color(ul, ok=20, warn=5)}; background: transparent;"
            )

        if ping is not None:
            self.ping_val.setText(str(ping))
            self.ping_val.setStyleSheet(
                f"font-size: 22px; font-weight: bold;"
                f" color: {_ping_color(ping)}; background: transparent;"
            )

        if loss is not None:
            lc = COLOR_OK if loss == 0 else (COLOR_WARN if loss < 10 else COLOR_BAD)
            self.loss_val.setText(f"{loss:.1f}")
            self.loss_val.setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {lc}; background: transparent;"
            )
