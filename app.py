# app.py
import queue
import threading

import customtkinter as ctk
import requests

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VpnCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Checker")
        self.geometry("1440x920")
        self.minsize(1024, 680)
        self.configure(fg_color=DARK_BG)

        self.result_queue: queue.Queue = queue.Queue()
        self._tab_refs: dict = {}  # keep refs to avoid GC
        self._current_ip_info: str = ""
        self._resize_job = None
        self._polling = True

        self._build_titlebar()
        self._build_tabs()
        self._poll_queue()
        self.bind("<Configure>", self._on_resize)
        # Fetch IP after window is shown
        self.after(200, self._fetch_ip_async)

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=DARKER_BG, height=44, corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Traffic light dots (macOS style)
        dots = ctk.CTkFrame(bar, fg_color="transparent")
        dots.pack(side="left", padx=14, pady=14)
        for color in ("#FF5F57", "#FEBC2E", "#28C840"):
            ctk.CTkFrame(dots, width=13, height=13, corner_radius=7,
                         fg_color=color).pack(side="left", padx=3)

        ctk.CTkLabel(bar, text="VPN Checker",
                     font=("Segoe UI", 13, "bold"),
                     text_color="#aaaaaa").pack(side="left", padx=8)

        # IP badge (right side)
        self.ip_badge = ctk.CTkFrame(bar, fg_color="#1e1e2e",
                                      corner_radius=20,
                                      border_width=1, border_color=BORDER)
        self.ip_badge.pack(side="right", padx=14, pady=10)
        self.ip_dot = ctk.CTkLabel(self.ip_badge, text="●", width=12,
                                    font=("Segoe UI", 10),
                                    text_color="#555566")
        self.ip_dot.pack(side="left", padx=(10, 2))
        self.ip_label = ctk.CTkLabel(self.ip_badge,
                                      text="Определение IP...",
                                      font=("Segoe UI", 11),
                                      text_color="#7c7caa")
        self.ip_label.pack(side="left", padx=(0, 10))

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self, fg_color=DARK_BG,
            segmented_button_fg_color=DARKER_BG,
            segmented_button_selected_color=ACCENT,
            segmented_button_unselected_color=DARKER_BG,
        )
        self.tabview.pack(fill="both", expand=True)

        for name in ("🛡  Полная проверка", "🔍  Кастомная",
                     "📋  История", "⚙️  Настройки"):
            self.tabview.add(name)

        self.full_tab = FullCheckTab(
            self.tabview.tab("🛡  Полная проверка"),
            self.result_queue,
            on_check_complete=self._on_check_complete,
        )
        self.full_tab.pack(fill="both", expand=True)

        self.custom_tab = CustomCheckTab(
            self.tabview.tab("🔍  Кастомная"),
            self.result_queue,
        )
        self.custom_tab.pack(fill="both", expand=True)

        # History and Settings tabs imported lazily to avoid circular at module level
        from tabs.history import HistoryTab
        from tabs.settings import SettingsTab

        self.history_tab = HistoryTab(self.tabview.tab("📋  История"))
        self.history_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(
            self.tabview.tab("⚙️  Настройки"),
            on_save=self._on_settings_saved,
        )
        self.settings_tab.pack(fill="both", expand=True)

    def _on_check_complete(self, verdict: dict, service_results: list[dict]):
        """Called by FullCheckTab after a check finishes. Saves to history."""
        from engine.history import save_result
        save_result(verdict, service_results, ip_info=self._current_ip_info)
        self.history_tab.refresh()

    def _on_settings_saved(self):
        """Called by SettingsTab after services are saved."""
        self.full_tab.reload_services()

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

    def _on_resize(self, event):
        if event.widget is not self:
            return
        # Pause queue polling during active resize to reduce contention
        self._polling = False
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._resume_polling)

    def _resume_polling(self):
        self._resize_job = None
        self._polling = True

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
