# widgets/service_card.py
import tkinter as tk
import customtkinter as ctk
from theme import (CARD_BG, COLOR_OK, COLOR_WARN, COLOR_BAD,
                   COLOR_CHECKING, COLOR_MUTED, BADGE_CHECKING_BG)

_DIVIDER = "#232333"


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


class ServiceCard(ctk.CTkFrame):
    """
    Dashboard-style card for one service.
    Layout: [4px accent] [icon+name / status] [big metrics: ping · loss · region]
    Uses plain tk.Frame for layout containers to reduce CTk redraw overhead.
    """

    def __init__(self, master, service: dict, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=10,
                         border_width=0, **kwargs)
        self.service = service

        # 4px accent strip — keep as CTkFrame so we can configure fg_color
        self._accent = ctk.CTkFrame(self, fg_color=COLOR_CHECKING,
                                     width=4, corner_radius=0)
        self._accent.pack(side="left", fill="y")
        self._accent.pack_propagate(False)

        # Content area — plain tk.Frame (no CTk redraw on resize)
        content = tk.Frame(self, bg=CARD_BG)
        content.pack(side="left", fill="both", expand=True)

        self._build(content)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self, parent):
        # ── Top row: icon + name  /  status ──────────────────────────────────
        top = tk.Frame(parent, bg=CARD_BG)
        top.pack(fill="x", padx=(12, 14), pady=(11, 6))

        ctk.CTkLabel(
            top,
            text=self.service["icon"] + "  " + self.service["name"],
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent",
            text_color="#c8c8dc",
        ).pack(side="left")

        # Status: colored dot + text, no box
        self.status_badge = ctk.CTkLabel(
            top, text="● Ожидание",
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            text_color="#3a3a55",
        )
        self.status_badge.pack(side="right")

        # ── Metrics row ───────────────────────────────────────────────────────
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", padx=(12, 14), pady=(0, 12))

        # Ping
        self.ping_val, self.ping_unit = self._metric(row, "—", "мс  пинг")
        self._vdivider(row)

        # Loss
        self.loss_val, _ = self._metric(row, "—", "потери")
        self._vdivider(row)

        # Region
        self.region_val, _ = self._metric(row, "—", "регион")

    def _metric(self, parent, value: str, caption: str):
        """Big number + small caption below."""
        block = tk.Frame(parent, bg=CARD_BG)
        block.pack(side="left", padx=(0, 6))

        val = ctk.CTkLabel(block, text=value,
                           font=("Segoe UI", 21, "bold"),
                           fg_color="transparent",
                           text_color=COLOR_MUTED)
        val.pack(anchor="w")

        cap = ctk.CTkLabel(block, text=caption,
                           font=("Segoe UI", 9),
                           fg_color="transparent",
                           text_color="#3a3a52")
        cap.pack(anchor="w")
        return val, cap

    def _vdivider(self, parent):
        tk.Frame(parent, bg=_DIVIDER, width=1).pack(
            side="left", fill="y", padx=10, pady=2)

    # ── State updates ──────────────────────────────────────────────────────────

    def set_checking(self):
        self._accent.configure(fg_color=COLOR_CHECKING)
        self.status_badge.configure(text="● Проверка", text_color=COLOR_CHECKING)
        self.ping_val.configure(text="…", text_color=COLOR_CHECKING)
        self.loss_val.configure(text="…", text_color=COLOR_CHECKING)
        self.region_val.configure(text="…", text_color=COLOR_CHECKING)

    def update_result(self, result: dict):
        accessible = result.get("accessible", False)
        ping_ms = result.get("ping_ms")
        loss_pct = result.get("loss_pct")
        region = result.get("region_accessible")

        status_color = COLOR_OK if accessible else COLOR_BAD
        self._accent.configure(fg_color=status_color)
        self.status_badge.configure(
            text="● Доступен" if accessible else "● Недоступен",
            text_color=status_color,
        )

        # Ping
        if ping_ms is not None:
            self.ping_val.configure(
                text=f"{ping_ms:.0f}",
                text_color=_ping_color(ping_ms),
            )
        else:
            self.ping_val.configure(text="—", text_color=COLOR_MUTED)

        # Loss
        if loss_pct is None:
            self.loss_val.configure(text="н/п", text_color=COLOR_MUTED)
        else:
            self.loss_val.configure(
                text=f"{loss_pct:.1f}%",
                text_color=_loss_color(loss_pct),
            )

        # Region
        if region is None:
            self.region_val.configure(text="—", text_color=COLOR_MUTED)
        elif region:
            self.region_val.configure(text="✓", text_color=COLOR_OK)
        else:
            self.region_val.configure(text="✗", text_color=COLOR_BAD)
