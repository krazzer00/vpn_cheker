# widgets/service_card.py
import customtkinter as ctk
from theme import (CARD_BG, BORDER, COLOR_OK, COLOR_WARN, COLOR_BAD,
                   COLOR_CHECKING, COLOR_MUTED, BADGE_CHECKING_BG)


def _ping_color(ping_ms):
    if ping_ms is None:
        return COLOR_BAD
    if ping_ms < 100:
        return COLOR_OK
    if ping_ms < 200:
        return COLOR_WARN
    return COLOR_BAD


def _badge_bg(color: str) -> str:
    return {
        COLOR_OK: "#1a2e1a",
        COLOR_WARN: "#2e1f0a",
        COLOR_BAD: "#2e0a0a",
        COLOR_CHECKING: BADGE_CHECKING_BG,
    }.get(color, BADGE_CHECKING_BG)


class ServiceCard(ctk.CTkFrame):
    """
    Card widget for one service result.
    Layout: [4px colored accent strip] [content: top row + stats row]
    The accent strip color reflects service status.
    """

    def __init__(self, master, service: dict, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10,
                         border_width=0, **kwargs)
        self.service = service

        # Left accent strip (4px, full height)
        self._accent = ctk.CTkFrame(self, fg_color=COLOR_CHECKING,
                                     width=4, corner_radius=0)
        self._accent.pack(side="left", fill="y")
        self._accent.pack_propagate(False)

        # Content wrapper
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)

        self._build(content)

    def _build(self, parent):
        # Top row: icon+name on left, status badge on right
        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=(10, 12), pady=(10, 4))

        ctk.CTkLabel(
            top,
            text=self.service["icon"] + "  " + self.service["name"],
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            top, text="Ожидание",
            font=("Segoe UI", 10, "bold"),
            text_color=COLOR_CHECKING,
            fg_color=BADGE_CHECKING_BG,
            corner_radius=8,
            padx=8, pady=2,
        )
        self.status_badge.pack(side="right")

        # Stats row
        stats = ctk.CTkFrame(parent, fg_color="transparent")
        stats.pack(fill="x", padx=(10, 12), pady=(0, 10))

        self.ping_label = self._stat(stats, "ПИНГ", "—")
        self.loss_label = self._stat(stats, "ПОТЕРИ", "—")
        self.region_label = self._stat(stats, "РЕГИОН", "—")

    def _stat(self, parent, label_text: str, value_text: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=(0, 18))
        ctk.CTkLabel(frame, text=label_text,
                     font=("Segoe UI", 9), text_color=COLOR_MUTED).pack(anchor="w")
        val = ctk.CTkLabel(frame, text=value_text,
                           font=("Segoe UI", 13, "bold"), text_color="#cccccc")
        val.pack(anchor="w")
        return val

    def set_checking(self):
        self._accent.configure(fg_color=COLOR_CHECKING)
        self.status_badge.configure(text="Проверка...",
                                     text_color=COLOR_CHECKING,
                                     fg_color=BADGE_CHECKING_BG)
        self.ping_label.configure(text="—", text_color="#cccccc")
        self.loss_label.configure(text="—", text_color="#cccccc")
        self.region_label.configure(text="—", text_color="#cccccc")

    def update_result(self, result: dict):
        accessible = result.get("accessible", False)
        ping_ms = result.get("ping_ms")
        loss_pct = result.get("loss_pct")
        region = result.get("region_accessible")

        status_color = COLOR_OK if accessible else COLOR_BAD
        status_text = "Доступен" if accessible else "Недоступен"

        self._accent.configure(fg_color=status_color)
        self.status_badge.configure(
            text=status_text,
            text_color=status_color,
            fg_color=_badge_bg(status_color),
        )

        ping_col = _ping_color(ping_ms)
        self.ping_label.configure(
            text=f"{ping_ms:.0f} ms" if ping_ms is not None else "—",
            text_color=ping_col,
        )

        if loss_pct is None:
            self.loss_label.configure(text="н/п", text_color=COLOR_MUTED)
        else:
            lc = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            self.loss_label.configure(text=f"{loss_pct:.1f}%", text_color=lc)

        if region is None:
            self.region_label.configure(text="н/п", text_color=COLOR_MUTED)
        elif region:
            self.region_label.configure(text="✓", text_color=COLOR_OK)
        else:
            self.region_label.configure(text="✗", text_color=COLOR_BAD)
