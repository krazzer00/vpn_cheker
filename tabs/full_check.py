# tabs/full_check.py
import json
import queue
import threading
from pathlib import Path

import customtkinter as ctk

from engine.checker import run_checks
from widgets.service_card import ServiceCard
from widgets.speed_bar import SpeedBar
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT, COLOR_MUTED

_SERVICES_PATH = Path(__file__).parent.parent / "services.json"

TIER_COLORS = {
    "S": "#4CAF50",
    "A": "#42a5f5",
    "B": "#FFC107",
    "C": "#FF9800",
    "F": "#F44336",
}


def _load_services():
    with open(_SERVICES_PATH, encoding="utf-8") as f:
        return json.load(f)["services"]


class FullCheckTab(ctk.CTkFrame):
    def __init__(self, master, result_queue: queue.Queue, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.result_queue = result_queue
        self.all_services = _load_services()
        self.cards: dict[str, ServiceCard] = {}
        self._selected: set[str] = {s["id"] for s in self.all_services}
        self._running = False

        self._build()

    def _build(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=DARKER_BG, width=210,
                                     corner_radius=0, border_width=1,
                                     border_color=BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        right = ctk.CTkFrame(self, fg_color=DARK_BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

    def _build_sidebar(self):
        scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        for cat, services in categories.items():
            ctk.CTkLabel(scroll, text=cat.upper(), font=("Segoe UI", 9, "bold"),
                         text_color=COLOR_MUTED).pack(anchor="w", padx=4, pady=(10, 2))
            for svc in services:
                var = ctk.BooleanVar(value=True)
                cb = ctk.CTkCheckBox(
                    scroll, text=svc["icon"] + "  " + svc["name"],
                    variable=var, font=("Segoe UI", 12),
                    checkbox_width=16, checkbox_height=16,
                    fg_color=ACCENT, hover_color="#7b8ef5",
                    command=lambda sid=svc["id"], v=var: self._toggle(sid, v)
                )
                cb.pack(anchor="w", pady=2)
                self._checkboxes[svc["id"]] = cb

        self.run_btn = ctk.CTkButton(
            self.sidebar, text="▶  Запустить",
            font=("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            corner_radius=9, height=38,
            command=self._start_check
        )
        self.run_btn.pack(fill="x", padx=8, pady=8)

    def _build_right(self, parent):
        self.speed_bar = SpeedBar(parent)
        self.speed_bar.pack(fill="x", padx=12, pady=(12, 8))

        self.cards_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.cards_scroll.pack(fill="both", expand=True, padx=12)

        self._build_cards()

        self.verdict_frame = ctk.CTkFrame(parent, fg_color="#1a1a26",
                                           corner_radius=10, border_width=1,
                                           border_color=BORDER)
        self.verdict_frame.pack(fill="x", padx=12, pady=(8, 12))
        self.verdict_icon = ctk.CTkLabel(self.verdict_frame, text="🛡",
                                          font=("Segoe UI", 28))
        self.verdict_icon.pack(side="left", padx=16, pady=12)
        verdict_text_frame = ctk.CTkFrame(self.verdict_frame, fg_color="transparent")
        verdict_text_frame.pack(side="left", fill="both", expand=True)
        self.verdict_title = ctk.CTkLabel(verdict_text_frame,
                                           text="Нажми Запустить",
                                           font=("Segoe UI", 15, "bold"))
        self.verdict_title.pack(anchor="w")
        self.verdict_sub = ctk.CTkLabel(verdict_text_frame,
                                         text="Выбери сервисы и запусти проверку",
                                         font=("Segoe UI", 11), text_color=COLOR_MUTED)
        self.verdict_sub.pack(anchor="w")
        self.verdict_score = ctk.CTkLabel(self.verdict_frame, text="",
                                           font=("Segoe UI", 32, "bold"))
        self.verdict_score.pack(side="right", padx=16)

    def _build_cards(self):
        for widget in self.cards_scroll.winfo_children():
            widget.destroy()
        self.cards.clear()

        categories: dict[str, list] = {}
        for svc in self.all_services:
            if svc["id"] in self._selected:
                categories.setdefault(svc["category"], []).append(svc)

        for cat, services in categories.items():
            ctk.CTkLabel(self.cards_scroll, text=cat.upper(),
                         font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_MUTED).pack(anchor="w", pady=(8, 4))
            grid = ctk.CTkFrame(self.cards_scroll, fg_color="transparent")
            grid.pack(fill="x")
            for i, svc in enumerate(services):
                card = ServiceCard(grid, svc)
                card.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
                grid.grid_columnconfigure(i % 3, weight=1)
                self.cards[svc["id"]] = card

    def _toggle(self, service_id: str, var: ctk.BooleanVar):
        if var.get():
            self._selected.add(service_id)
        else:
            self._selected.discard(service_id)

    def _start_check(self):
        if self._running:
            return
        self._running = True
        self.run_btn.configure(state="disabled", text="Проверка...")

        self._build_cards()
        for card in self.cards.values():
            card.set_checking()

        services = [s for s in self.all_services if s["id"] in self._selected]
        thread = threading.Thread(
            target=run_checks, args=(services, self.result_queue), daemon=True
        )
        thread.start()

    def handle_result(self, msg: dict):
        if msg["type"] == "service":
            card = self.cards.get(msg["id"])
            if card:
                card.update_result(msg)
                if msg.get("ping_ms") is not None:
                    self.speed_bar.update_ping(msg["ping_ms"], msg.get("loss_pct"))

        elif msg["type"] == "speed":
            self.speed_bar.update_speed(msg)

        elif msg["type"] == "verdict":
            self._running = False
            self.run_btn.configure(state="normal", text="▶  Запустить снова")
            color = TIER_COLORS.get(msg["tier"], "#e0e0e0")
            self.verdict_title.configure(text=msg["message"], text_color=color)
            self.verdict_sub.configure(
                text=f"Доступно {msg['accessible_count']} из {msg['total_count']} сервисов"
            )
            self.verdict_score.configure(
                text=f"{msg['score']}/10", text_color=color
            )
