# app.py
import customtkinter as ctk
import queue

from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG = "#16161f"
DARKER_BG = "#111118"
BORDER = "#2a2a3a"
ACCENT = "#5b6af5"


class VpnCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VPN Checker")
        self.geometry("960x620")
        self.minsize(800, 560)
        self.configure(fg_color=DARK_BG)

        self.result_queue: queue.Queue = queue.Queue()

        self._build_titlebar()
        self._build_tabs()
        self._start_queue_poll()

    def _build_titlebar(self):
        bar = ctk.CTkFrame(self, fg_color=DARKER_BG, height=40, corner_radius=0)
        bar.pack(fill="x", side="top")
        ctk.CTkLabel(bar, text="VPN Checker", font=("Segoe UI", 13, "bold"),
                     text_color="#aaaaaa").pack(side="left", padx=16, pady=8)
        self.ip_label = ctk.CTkLabel(bar, text="● Определение IP...",
                                      font=("Segoe UI", 11), text_color="#7c7caa")
        self.ip_label.pack(side="right", padx=16)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, fg_color=DARK_BG,
                                       segmented_button_fg_color=DARKER_BG,
                                       segmented_button_selected_color=ACCENT,
                                       segmented_button_unselected_color=DARKER_BG)
        self.tabview.pack(fill="both", expand=True, padx=0, pady=0)

        self.tabview.add("🛡  Полная проверка")
        self.tabview.add("🔍  Кастомная")

        self.full_tab = FullCheckTab(
            self.tabview.tab("🛡  Полная проверка"),
            self.result_queue
        )
        self.full_tab.pack(fill="both", expand=True)

        self.custom_tab = CustomCheckTab(
            self.tabview.tab("🔍  Кастомная"),
            self.result_queue
        )
        self.custom_tab.pack(fill="both", expand=True)

    def _start_queue_poll(self):
        self._poll_queue()

    def _poll_queue(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                self.full_tab.handle_result(msg)
                self.custom_tab.handle_result(msg)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)
