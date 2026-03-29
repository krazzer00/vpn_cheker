# widgets/service_card.py
import customtkinter as ctk
from theme import CARD_BG, BORDER, COLOR_OK, COLOR_WARN, COLOR_BAD, COLOR_CHECKING, COLOR_MUTED


def _ping_color(ping_ms):
    if ping_ms is None:
        return COLOR_BAD
    if ping_ms < 100:
        return COLOR_OK
    if ping_ms < 200:
        return COLOR_WARN
    return COLOR_BAD


def _alpha_color(hex_color: str) -> str:
    """Return a darkened bg color for status badges."""
    mapping = {
        COLOR_OK: "#1a2e1a",
        COLOR_WARN: "#2e1f0a",
        COLOR_BAD: "#2e0a0a",
        COLOR_CHECKING: "#1a1e3a",
    }
    return mapping.get(hex_color, "#1a1a26")


class ServiceCard(ctk.CTkFrame):
    def __init__(self, master, service: dict, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self.service = service
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(top, text=self.service["icon"] + "  " + self.service["name"],
                     font=("Segoe UI", 13, "bold")).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            top, text="Ожидание...",
            font=("Segoe UI", 10, "bold"),
            text_color=COLOR_CHECKING,
            fg_color="#1e1e3a", corner_radius=10
        )
        self.status_badge.pack(side="right", padx=(4, 0))

        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=12, pady=(0, 10))

        self.ping_label = self._stat(stats, "ПИНГ", "—")
        self.loss_label = self._stat(stats, "ПОТЕРИ", "—")
        self.region_label = self._stat(stats, "РЕГИОН", "—")

    def _stat(self, parent, label_text, value_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(frame, text=label_text, font=("Segoe UI", 9),
                     text_color=COLOR_MUTED).pack(anchor="w")
        val = ctk.CTkLabel(frame, text=value_text, font=("Segoe UI", 13, "bold"))
        val.pack(anchor="w")
        return val

    def set_checking(self):
        self.status_badge.configure(text="Проверка...", text_color=COLOR_CHECKING,
                                    fg_color="#1e1e3a")
        self.ping_label.configure(text="—", text_color="white")
        self.loss_label.configure(text="—", text_color="white")
        self.region_label.configure(text="—", text_color="white")
        self.configure(border_color=BORDER)

    def update_result(self, result: dict):
        accessible = result["accessible"]
        ping_ms = result.get("ping_ms")
        loss_pct = result.get("loss_pct")
        region = result.get("region_accessible")

        if accessible:
            self.status_badge.configure(text="Доступен", text_color=COLOR_OK,
                                        fg_color=_alpha_color(COLOR_OK))
            self.configure(border_color=COLOR_OK)
        else:
            self.status_badge.configure(text="Недоступен", text_color=COLOR_BAD,
                                        fg_color=_alpha_color(COLOR_BAD))
            self.configure(border_color=COLOR_BAD)

        ping_text = f"{ping_ms} ms" if ping_ms is not None else "—"
        self.ping_label.configure(text=ping_text, text_color=_ping_color(ping_ms))

        if loss_pct is None:
            self.loss_label.configure(text="н/п", text_color=COLOR_MUTED)
        else:
            loss_color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            self.loss_label.configure(text=f"{loss_pct}%", text_color=loss_color)

        if region is None:
            self.region_label.configure(text="н/п", text_color=COLOR_MUTED)
        elif region:
            self.region_label.configure(text="✓", text_color=COLOR_OK)
        else:
            self.region_label.configure(text="✗", text_color=COLOR_BAD)
