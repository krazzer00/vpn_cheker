# tabs/full_check.py
import queue
import threading
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from engine.checker import run_checks
from engine.config import load_services as _load_services_from_config
from widgets.service_card import ServiceCard
from widgets.speed_bar import SpeedBar
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT, COLOR_MUTED, TIER_COLORS, CARD_BG
from widgets.smooth_scroll import apply_smooth_scroll


class FullCheckTab(ctk.CTkFrame):
    def __init__(
        self,
        master,
        result_queue: queue.Queue,
        on_check_complete: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self.result_queue = result_queue
        self._on_check_complete = on_check_complete
        self.all_services: list[dict] = []
        self.cards: dict[str, ServiceCard] = {}
        self._selected: set[str] = set()
        self._running = False
        self._service_results: list[dict] = []

        self._load_services()
        self._build()
        self._build_all_cards()

    # ── Service loading ────────────────────────────────────────────────────────

    def _load_services(self):
        self.all_services = [
            s for s in _load_services_from_config() if s.get("enabled", True)
        ]
        self._selected = {s["id"] for s in self.all_services}

    def reload_services(self):
        """Called by app.py after settings are saved."""
        self._load_services()
        self._rebuild_sidebar_checkboxes()
        self._build_all_cards()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=DARKER_BG, width=220,
                                     corner_radius=0, border_width=1,
                                     border_color=BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar,
                                                        fg_color="transparent")
        self._sidebar_scroll.pack(fill="both", expand=True, padx=8, pady=8)
        apply_smooth_scroll(self._sidebar_scroll)
        self._checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self._populate_sidebar(self._sidebar_scroll)

        self.run_btn = ctk.CTkButton(
            self.sidebar, text="▶  Запустить",
            font=("Segoe UI", 13, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            corner_radius=9, height=40,
            command=self._start_check,
        )
        self.run_btn.pack(fill="x", padx=10, pady=10)

        # Right panel
        right = tk.Frame(self, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        self.speed_bar = SpeedBar(right)
        self.speed_bar.pack(fill="x", padx=14, pady=(14, 8))

        # Cards area (scrollable)
        self._cards_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._cards_container.pack(fill="both", expand=True, padx=14)
        apply_smooth_scroll(self._cards_container)

        # Verdict panel
        self._build_verdict(right)

    def _populate_sidebar(self, scroll):
        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        for cat, services in categories.items():
            ctk.CTkLabel(scroll, text=cat.upper(),
                         font=("Segoe UI", 9, "bold"),
                         text_color=COLOR_MUTED).pack(anchor="w", padx=4, pady=(10, 2))
            for svc in services:
                var = ctk.BooleanVar(value=svc["id"] in self._selected)
                cb = ctk.CTkCheckBox(
                    scroll, text=svc["icon"] + "  " + svc["name"],
                    variable=var, font=("Segoe UI", 12),
                    checkbox_width=16, checkbox_height=16,
                    fg_color=ACCENT, hover_color="#7b8ef5",
                    command=lambda sid=svc["id"], v=var: self._toggle(sid, v),
                )
                cb.pack(anchor="w", pady=2)
                self._checkboxes[svc["id"]] = cb

    def _rebuild_sidebar_checkboxes(self):
        for w in self._sidebar_scroll.winfo_children():
            w.destroy()
        self._checkboxes.clear()
        self._populate_sidebar(self._sidebar_scroll)

    def _build_verdict(self, parent):
        self.verdict_frame = ctk.CTkFrame(parent, fg_color=CARD_BG,
                                           corner_radius=10, border_width=1,
                                           border_color=BORDER)
        self.verdict_frame.pack(fill="x", padx=14, pady=(8, 14))

        self.verdict_icon = ctk.CTkLabel(self.verdict_frame, text="🛡",
                                          font=("Segoe UI", 30))
        self.verdict_icon.pack(side="left", padx=18, pady=14)

        vt = tk.Frame(self.verdict_frame, bg=CARD_BG)
        vt.pack(side="left", fill="both", expand=True, pady=10)

        self.verdict_title = ctk.CTkLabel(vt, text="Нажми Запустить",
                                           font=("Segoe UI", 15, "bold"),
                                           text_color="#cccccc")
        self.verdict_title.pack(anchor="w")
        self.verdict_sub = ctk.CTkLabel(vt,
                                         text="Выбери сервисы и запусти проверку",
                                         font=("Segoe UI", 11),
                                         text_color=COLOR_MUTED)
        self.verdict_sub.pack(anchor="w", pady=(2, 0))

        self.verdict_score = ctk.CTkLabel(self.verdict_frame, text="",
                                           font=("Segoe UI", 34, "bold"))
        self.verdict_score.pack(side="right", padx=18)

    # ── Cards (pre-created, hidden/shown) ─────────────────────────────────────

    def _build_all_cards(self):
        """Create all service cards once. Called at init and after settings save."""
        for w in self._cards_container.winfo_children():
            w.destroy()
        self.cards.clear()

        categories: dict[str, list] = {}
        for svc in self.all_services:
            categories.setdefault(svc["category"], []).append(svc)

        self._category_labels: dict[str, ctk.CTkLabel] = {}
        self._category_grids: dict[str, ctk.CTkFrame] = {}

        for cat, services in categories.items():
            lbl = ctk.CTkLabel(self._cards_container, text=cat.upper(),
                               font=("Segoe UI", 10, "bold"), text_color=COLOR_MUTED)
            lbl.pack(anchor="w", pady=(8, 4))
            self._category_labels[cat] = lbl

            grid = ctk.CTkFrame(self._cards_container, fg_color="transparent")
            grid.pack(fill="x")
            self._category_grids[cat] = grid

            for i, svc in enumerate(services):
                card = ServiceCard(grid, svc)
                card.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="nsew")
                grid.grid_columnconfigure(i % 3, weight=1)
                self.cards[svc["id"]] = card

        self._refresh_card_visibility()

    def _refresh_card_visibility(self):
        """Show/hide cards and category labels based on selection."""
        for svc in self.all_services:
            card = self.cards.get(svc["id"])
            if card:
                if svc["id"] in self._selected:
                    card.grid()
                else:
                    card.grid_remove()

    # ── Interaction ────────────────────────────────────────────────────────────

    def _toggle(self, service_id: str, var: ctk.BooleanVar):
        if var.get():
            self._selected.add(service_id)
        else:
            self._selected.discard(service_id)
        self._refresh_card_visibility()

    def _start_check(self):
        if self._running or not self._selected:
            return
        self._running = True
        self._service_results = []
        self.run_btn.configure(state="disabled", text="Проверка...")

        for sid in self._selected:
            card = self.cards.get(sid)
            if card:
                card.set_checking()

        services = [s for s in self.all_services if s["id"] in self._selected]
        threading.Thread(
            target=run_checks, args=(services, self.result_queue), daemon=True
        ).start()

    def handle_result(self, msg: dict):
        msg_type = msg.get("type")

        if msg_type == "service":
            card = self.cards.get(msg["id"])
            if card:
                card.update_result(msg)
            self._service_results.append(msg)

        elif msg_type == "speed":
            self.speed_bar.update_speed(msg)

        elif msg_type == "verdict":
            self._running = False
            self.run_btn.configure(state="normal", text="▶  Запустить снова")
            color = TIER_COLORS.get(msg["tier"], "#e0e0e0")
            self.verdict_title.configure(text=msg["message"], text_color=color)
            self.verdict_sub.configure(
                text=f"Доступно {msg['accessible_count']} из {msg['total_count']} сервисов"
            )
            self.verdict_score.configure(text=f"{msg['score']}/10", text_color=color)
            if self._on_check_complete:
                self._on_check_complete(msg, list(self._service_results))
