# widgets/speed_bar.py
import customtkinter as ctk
from theme import DARKER_BG, BORDER, COLOR_MUTED, COLOR_OK, COLOR_WARN, COLOR_BAD

ACCENT_TEXT = "#e0e0e0"


class SpeedBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=DARKER_BG, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self._build()

    def _build(self):
        self.ping_val = self._item("ПИНГ", "—")
        self._divider()
        self.dl_val = self._item("ЗАГРУЗКА", "—")
        self._divider()
        self.ul_val = self._item("ВЫГРУЗКА", "—")
        self._divider()
        self.loss_val = self._item("ПОТЕРИ", "—")

    def _item(self, label, value):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 9),
                     text_color=COLOR_MUTED).pack(anchor="w")
        val = ctk.CTkLabel(frame, text=value, font=("Segoe UI", 20, "bold"),
                            text_color=ACCENT_TEXT)
        val.pack(anchor="w")
        return val

    def _divider(self):
        ctk.CTkFrame(self, fg_color=BORDER, width=1).pack(
            side="left", fill="y", pady=8)

    def update_speed(self, result: dict):
        dl = result.get("download_mbps")
        ul = result.get("upload_mbps")
        ping = result.get("ping_ms")
        self.dl_val.configure(text=f"{dl} Мбит/с" if dl is not None else "N/A")
        self.ul_val.configure(text=f"{ul} Мбит/с" if ul is not None else "N/A")
        if ping is not None:
            self.ping_val.configure(text=f"{ping} ms")

    def update_ping(self, ping_ms, loss_pct):
        if ping_ms is not None:
            self.ping_val.configure(text=f"{ping_ms} ms")
        if loss_pct is not None:
            color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            self.loss_val.configure(text=f"{loss_pct}%", text_color=color)
