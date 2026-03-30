# app.py
import queue
import threading
import tkinter as tk

import customtkinter as ctk
import requests

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TAB_NAMES = [
    "🛡  Полная проверка",
    "🔍  Кастомная",
    "📋  История",
    "⚙️  Настройки",
]


class VpnCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Checker")
        self.geometry("1440x920")
        self.minsize(1024, 680)
        self.configure(fg_color=DARK_BG)

        self.result_queue: queue.Queue = queue.Queue()
        self._current_ip_info: str = ""
        self._resize_job = None
        self._polling = True

        self._build_titlebar()
        self._build_tabs()
        self._poll_queue()
        self.bind("<Configure>", self._on_resize)
        self.after(200, self._fetch_ip_async)

    # ── Titlebar ───────────────────────────────────────────────────────────────

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=DARKER_BG, height=44)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Traffic light dots
        dots = tk.Frame(bar, bg=DARKER_BG)
        dots.pack(side="left", padx=14, pady=14)
        for color in ("#FF5F57", "#FEBC2E", "#28C840"):
            tk.Frame(dots, bg=color, width=13, height=13).pack(side="left", padx=3)

        tk.Label(bar, text="VPN Checker", bg=DARKER_BG, fg="#888899",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=6)

        # IP badge (right side) — CTkFrame for rounded corners
        self.ip_badge = ctk.CTkFrame(bar, fg_color="#1e1e2e",
                                      corner_radius=20,
                                      border_width=1, border_color=BORDER)
        self.ip_badge.pack(side="right", padx=14, pady=10)
        self.ip_dot = ctk.CTkLabel(self.ip_badge, text="●", width=12,
                                    font=("Segoe UI", 10), text_color="#333344")
        self.ip_dot.pack(side="left", padx=(10, 2))
        self.ip_label = ctk.CTkLabel(self.ip_badge, text="Определение IP...",
                                      font=("Segoe UI", 11), text_color="#555566")
        self.ip_label.pack(side="left", padx=(0, 10))

    # ── Tabs — place()+lift() so switching never triggers Configure cascade ────

    def _build_tabs(self):
        # Tab button bar
        bar = tk.Frame(self, bg=DARKER_BG, height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self._tab_btns: dict[str, ctk.CTkButton] = {}
        for name in _TAB_NAMES:
            btn = ctk.CTkButton(
                bar, text=name,
                fg_color=ACCENT, hover_color="#7b8ef5",
                text_color="white",
                font=("Segoe UI", 12),
                corner_radius=0, height=38, border_spacing=0,
                command=lambda n=name: self._switch_tab(n),
            )
            btn.pack(side="left", padx=(0, 1))
            self._tab_btns[name] = btn

        # Content area — plain tk.Frame, no CTk redraw
        content = tk.Frame(self, bg=DARK_BG)
        content.pack(fill="both", expand=True)

        # All tab frames stacked via place() — lift() to switch, zero Configure cascade
        self._tab_frames: dict[str, tk.Frame] = {}
        for name in _TAB_NAMES:
            f = tk.Frame(content, bg=DARK_BG)
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._tab_frames[name] = f

        # Build tab content
        self.full_tab = FullCheckTab(
            self._tab_frames[_TAB_NAMES[0]],
            self.result_queue,
            on_check_complete=self._on_check_complete,
        )
        self.full_tab.pack(fill="both", expand=True)

        self.custom_tab = CustomCheckTab(
            self._tab_frames[_TAB_NAMES[1]],
            self.result_queue,
        )
        self.custom_tab.pack(fill="both", expand=True)

        from tabs.history import HistoryTab
        from tabs.settings import SettingsTab

        self.history_tab = HistoryTab(self._tab_frames[_TAB_NAMES[2]])
        self.history_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(
            self._tab_frames[_TAB_NAMES[3]],
            on_save=self._on_settings_saved,
        )
        self.settings_tab.pack(fill="both", expand=True)

        # Activate first tab
        self._current_tab = _TAB_NAMES[0]
        self._update_tab_btns(_TAB_NAMES[0])
        self._tab_frames[_TAB_NAMES[0]].lift()

    def _switch_tab(self, name: str):
        if name == self._current_tab:
            return
        self._tab_frames[name].lift()
        self._current_tab = name
        self._update_tab_btns(name)

    def _update_tab_btns(self, active: str):
        for name, btn in self._tab_btns.items():
            btn.configure(
                fg_color=ACCENT if name == active else DARKER_BG,
                text_color="white" if name == active else "#666677",
            )

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _on_check_complete(self, verdict: dict, service_results: list[dict]):
        from engine.history import save_result
        save_result(verdict, service_results, ip_info=self._current_ip_info)
        self.history_tab.refresh()

    def _on_settings_saved(self):
        self.full_tab.reload_services()

    # ── IP fetch ───────────────────────────────────────────────────────────────

    def _fetch_ip_async(self):
        threading.Thread(target=self._fetch_ip, daemon=True).start()

    def _fetch_ip(self):
        try:
            r = requests.get("https://ipapi.co/json/", timeout=6,
                             headers={"User-Agent": "VPNChecker/1.0"})
            d = r.json()
            ip = d.get("ip", "?")
            city = d.get("city", "")
            country = d.get("country_name", "?")
            location = f"{city}, {country}" if city else country
            text = f"{ip} — {location}"
            self._current_ip_info = text
            self.after(0, lambda: (
                self.ip_label.configure(text=text, text_color="#9090cc"),
                self.ip_dot.configure(text_color="#4CAF50"),
            ))
        except Exception:
            self.after(0, lambda: (
                self.ip_label.configure(text="IP не определён", text_color="#664444"),
                self.ip_dot.configure(text_color="#F44336"),
            ))

    # ── Resize debounce ────────────────────────────────────────────────────────

    def _on_resize(self, event):
        if event.widget is not self:
            return
        self._polling = False
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._resume_polling)

    def _resume_polling(self):
        self._resize_job = None
        self._polling = True

    # ── Queue poll ─────────────────────────────────────────────────────────────

    def _poll_queue(self):
        if self._polling:
            try:
                while True:
                    msg = self.result_queue.get_nowait()
                    self.full_tab.handle_result(msg)
                    self.custom_tab.handle_result(msg)
            except queue.Empty:
                pass
        self.after(100, self._poll_queue)
