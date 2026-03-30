# widgets/speed_bar.py
import tkinter as tk
import customtkinter as ctk
from theme import DARKER_BG, BORDER, COLOR_MUTED, COLOR_OK, COLOR_WARN, COLOR_BAD


def _speed_color(mbps, ok=50, warn=15):
    if mbps is None:
        return COLOR_MUTED
    if mbps >= ok:
        return COLOR_OK
    if mbps >= warn:
        return COLOR_WARN
    return COLOR_BAD


def _ping_color(ms):
    if ms is None:
        return COLOR_MUTED
    if ms < 60:
        return COLOR_OK
    if ms < 150:
        return COLOR_WARN
    return COLOR_BAD


class SpeedBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=DARKER_BG, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self._build()

    def _build(self):
        # Use tk.Frame for the inner layout row (no CTk redraw on resize)
        row = tk.Frame(self, bg=DARKER_BG)
        row.pack(fill="both", expand=True, padx=4)

        self.ping_val = self._item(row, "⊙  ПИНГ", "—", "мс")
        self._divider(row)
        self.dl_val = self._item(row, "↓  ЗАГРУЗКА", "—", "Мб/с")
        self._divider(row)
        self.ul_val = self._item(row, "↑  ВЫГРУЗКА", "—", "Мб/с")
        self._divider(row)
        self.loss_val = self._item(row, "◈  ПОТЕРИ", "—", "%")

    def _item(self, parent, label, value, unit):
        frame = tk.Frame(parent, bg=DARKER_BG)
        frame.pack(side="left", padx=22, pady=12)

        ctk.CTkLabel(frame, text=label,
                     font=("Segoe UI", 9, "bold"),
                     fg_color="transparent",
                     text_color=COLOR_MUTED).pack(anchor="w")

        # Value + unit on same line
        val_row = tk.Frame(frame, bg=DARKER_BG)
        val_row.pack(anchor="w")

        val = ctk.CTkLabel(val_row, text=value,
                           font=("Segoe UI", 22, "bold"),
                           fg_color="transparent",
                           text_color="#ccccdd")
        val.pack(side="left")

        ctk.CTkLabel(val_row, text=f" {unit}",
                     font=("Segoe UI", 11),
                     fg_color="transparent",
                     text_color="#44445a").pack(side="left", pady=(4, 0))
        return val

    def _divider(self, parent):
        tk.Frame(parent, bg=BORDER, width=1).pack(
            side="left", fill="y", pady=10)

    def update_speed(self, result: dict):
        dl = result.get("download_mbps")
        ul = result.get("upload_mbps")
        ping = result.get("ping_ms")

        if dl is not None:
            self.dl_val.configure(
                text=f"{dl}",
                text_color=_speed_color(dl, ok=50, warn=15),
            )
        else:
            self.dl_val.configure(text="N/A", text_color=COLOR_MUTED)

        if ul is not None:
            self.ul_val.configure(
                text=f"{ul}",
                text_color=_speed_color(ul, ok=20, warn=5),
            )
        else:
            self.ul_val.configure(text="N/A", text_color=COLOR_MUTED)

        if ping is not None:
            self.ping_val.configure(
                text=f"{ping}",
                text_color=_ping_color(ping),
            )

    def update_ping(self, ping_ms, loss_pct):
        if ping_ms is not None:
            self.ping_val.configure(
                text=f"{ping_ms}",
                text_color=_ping_color(ping_ms),
            )
        if loss_pct is not None:
            color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            self.loss_val.configure(text=f"{loss_pct:.1f}", text_color=color)
