# tabs/custom_check.py
import queue
import threading
from urllib.parse import urlparse

import customtkinter as ctk

from engine.ping import ping_host
from engine.http_check import http_check
from theme import DARK_BG, BORDER, ACCENT, COLOR_OK, COLOR_BAD, COLOR_WARN, COLOR_MUTED

CARD_BG = "#1a1a26"


class CustomCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.result_queue = result_queue
        self._running = False
        self._build()

    def _build(self):
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="Проверить ресурс",
                     font=("Segoe UI", 18, "bold")).pack(pady=(0, 4))
        ctk.CTkLabel(center, text="Введи URL или hostname",
                     font=("Segoe UI", 12), text_color=COLOR_MUTED).pack(pady=(0, 20))

        input_row = ctk.CTkFrame(center, fg_color="transparent")
        input_row.pack()

        self.url_entry = ctk.CTkEntry(
            input_row, width=380, height=40,
            placeholder_text="https://example.com или example.com",
            font=("Segoe UI", 13),
            fg_color=CARD_BG, border_color=BORDER
        )
        self.url_entry.pack(side="left", padx=(0, 8))

        self.check_btn = ctk.CTkButton(
            input_row, text="Проверить", width=110, height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            command=self._start_check
        )
        self.check_btn.pack(side="left")

        self.result_frame = ctk.CTkFrame(
            center, fg_color=CARD_BG, corner_radius=12,
            border_width=1, border_color=BORDER
        )
        self.result_frame.pack(pady=20, fill="x")

    def _show_result(self, ping_result: dict, http_result: dict, url: str):
        for w in self.result_frame.winfo_children():
            w.destroy()

        accessible = http_result["accessible"]
        ping_ms = ping_result.get("ping_ms")
        loss_pct = ping_result.get("loss_pct")

        color = COLOR_OK if accessible else COLOR_BAD
        status_text = "Доступен ✓" if accessible else "Недоступен ✗"

        top = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(top, text=url, font=("Segoe UI", 13, "bold"),
                     text_color="#cccccc").pack(side="left")
        ctk.CTkLabel(top, text=status_text, font=("Segoe UI", 12, "bold"),
                     text_color=color).pack(side="right")

        stats = ctk.CTkFrame(self.result_frame, fg_color="transparent")
        stats.pack(fill="x", padx=16, pady=(0, 14))

        def stat(label, value, col="#e0e0e0"):
            f = ctk.CTkFrame(stats, fg_color="transparent")
            f.pack(side="left", padx=(0, 24))
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 9),
                         text_color=COLOR_MUTED).pack(anchor="w")
            ctk.CTkLabel(f, text=value, font=("Segoe UI", 16, "bold"),
                         text_color=col).pack(anchor="w")

        ping_color = COLOR_OK if ping_ms and ping_ms < 100 else (COLOR_WARN if ping_ms else COLOR_BAD)
        stat("ПИНГ", f"{ping_ms:.0f} ms" if ping_ms is not None else "—", ping_color)

        if loss_pct is None:
            stat("ПОТЕРИ", "н/п", COLOR_MUTED)
        else:
            loss_color = COLOR_OK if loss_pct == 0 else (COLOR_WARN if loss_pct < 10 else COLOR_BAD)
            stat("ПОТЕРИ", f"{loss_pct:.1f}%", loss_color)

        sc = http_result.get("status_code")
        stat("HTTP", str(sc) if sc else "—")

        rt = http_result.get("response_ms")
        stat("ОТВЕТ", f"{rt:.0f} ms" if rt is not None else "—")

    def _start_check(self):
        if self._running:
            return
        raw = self.url_entry.get().strip()
        if not raw:
            return

        if not raw.startswith("http"):
            raw = "https://" + raw

        self._running = True
        self.check_btn.configure(state="disabled", text="Проверка...")

        def worker():
            host = urlparse(raw).hostname or raw
            ping_result = ping_host(host)
            http_result = http_check(raw)
            self.after(0, lambda: self._on_done(ping_result, http_result, raw))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self, ping_result, http_result, url):
        self._show_result(ping_result, http_result, url)
        self._running = False
        self.check_btn.configure(state="normal", text="Проверить")

    def handle_result(self, msg: dict):
        pass  # custom tab uses its own worker thread, not the shared queue
