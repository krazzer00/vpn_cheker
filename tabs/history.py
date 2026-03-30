# tabs/history.py
import customtkinter as ctk
from engine.history import load_history, clear_history
from theme import DARK_BG, DARKER_BG, CARD_BG, BORDER, COLOR_MUTED, ACCENT, TIER_COLORS


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self._build()
        self.refresh()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=DARKER_BG, height=48, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="История проверок",
                     font=("Segoe UI", 14, "bold"),
                     text_color="#cccccc").pack(side="left", padx=16, pady=12)
        ctk.CTkButton(top, text="Очистить", width=90, height=28,
                      font=("Segoe UI", 11),
                      fg_color="#2e1a1a", hover_color="#4e2a2a",
                      text_color="#cc6666",
                      corner_radius=6,
                      command=self._clear).pack(side="right", padx=12, pady=10)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=14, pady=10)

    def refresh(self):
        """Reload and redraw history list."""
        for w in self._scroll.winfo_children():
            w.destroy()

        records = load_history()

        if not records:
            ctk.CTkLabel(
                self._scroll,
                text="Ещё не было ни одной проверки.\nЗапусти полную проверку и результаты появятся здесь.",
                font=("Segoe UI", 13),
                text_color=COLOR_MUTED,
                justify="center",
            ).pack(pady=60)
            return

        for record in records:
            self._add_row(record)

    def _add_row(self, record: dict):
        row = ctk.CTkFrame(self._scroll, fg_color=CARD_BG, corner_radius=10,
                           border_width=1, border_color=BORDER)
        row.pack(fill="x", pady=4)

        # Tier color accent strip
        tier_color = TIER_COLORS.get(record.get("tier", "F"), "#F44336")
        ctk.CTkFrame(row, fg_color=tier_color, width=4,
                     corner_radius=0).pack(side="left", fill="y")

        # Content
        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True,
                     padx=12, pady=10)

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        # Timestamp + message
        ts = record.get("timestamp", "?")
        ctk.CTkLabel(left, text=ts,
                     font=("Segoe UI", 10), text_color=COLOR_MUTED).pack(anchor="w")
        ctk.CTkLabel(left, text=record.get("message", ""),
                     font=("Segoe UI", 13, "bold"),
                     text_color=tier_color).pack(anchor="w", pady=(2, 0))
        accessible = record.get("accessible_count", 0)
        total = record.get("total_count", 0)
        ctk.CTkLabel(left,
                     text=f"Доступно {accessible} из {total} сервисов",
                     font=("Segoe UI", 11), text_color=COLOR_MUTED).pack(anchor="w")

        # Score on right
        ctk.CTkLabel(row,
                     text=f"{record.get('score', 0)}/10",
                     font=("Segoe UI", 28, "bold"),
                     text_color=tier_color).pack(side="right", padx=16)

    def _clear(self):
        clear_history()
        self.refresh()
