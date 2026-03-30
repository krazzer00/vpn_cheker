# tabs/settings.py
from typing import Callable, Optional

import customtkinter as ctk

from engine.config import load_services, save_services
from widgets.smooth_scroll import apply_smooth_scroll
from theme import (DARK_BG, DARKER_BG, CARD_BG, BORDER,
                   COLOR_OK, COLOR_BAD, COLOR_MUTED, ACCENT)

_CATEGORIES = ["AI", "Media", "Social", "Other"]
_CHECK_TYPES = ["http", "ai_region"]


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, on_save: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color=DARK_BG, **kwargs)
        self._on_save = on_save
        self._services: list[dict] = []
        self._rows: list[dict] = []  # per-row widget refs
        self._build()
        self._load()

    def _build(self):
        # Top bar
        top = ctk.CTkFrame(self, fg_color=DARKER_BG, height=48, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkLabel(top, text="Настройки сервисов",
                     font=("Segoe UI", 14, "bold"),
                     text_color="#cccccc").pack(side="left", padx=16)
        self._save_btn = ctk.CTkButton(
            top, text="💾 Сохранить", width=120, height=30,
            font=("Segoe UI", 12, "bold"),
            fg_color=ACCENT, hover_color="#7b8ef5",
            corner_radius=8,
            command=self._save,
        )
        self._save_btn.pack(side="right", padx=12, pady=9)
        ctk.CTkButton(
            top, text="+ Добавить", width=100, height=30,
            font=("Segoe UI", 12),
            fg_color="#1e2e1e", hover_color="#2e4e2e",
            text_color=COLOR_OK,
            corner_radius=8,
            command=self._add_service,
        ).pack(side="right", padx=4, pady=9)

        # Column headers
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 2))
        for text, w in [("Вкл", 44), ("Иконка", 60), ("Название", 140),
                        ("URL", 240), ("Категория", 100), ("Тип", 90), ("", 40)]:
            ctk.CTkLabel(hdr, text=text, width=w,
                         font=("Segoe UI", 10, "bold"),
                         text_color=COLOR_MUTED,
                         anchor="w").pack(side="left", padx=2)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._rebind = apply_smooth_scroll(self._scroll)

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        self._services = load_services()
        for svc in self._services:
            self._add_row(svc)
        self._rebind(self._scroll)

    def _add_row(self, svc: dict):
        row_frame = ctk.CTkFrame(self._scroll, fg_color=CARD_BG,
                                  corner_radius=8, border_width=1,
                                  border_color=BORDER)
        row_frame.pack(fill="x", pady=3)

        # Enabled switch
        enabled_var = ctk.BooleanVar(value=svc.get("enabled", True))
        sw = ctk.CTkSwitch(row_frame, text="", variable=enabled_var,
                           width=44, onvalue=True, offvalue=False,
                           fg_color="#2a2a3a", progress_color=ACCENT)
        sw.pack(side="left", padx=(8, 4), pady=8)

        # Icon entry
        icon_e = ctk.CTkEntry(row_frame, width=52, font=("Segoe UI", 16),
                               fg_color=DARKER_BG, border_color=BORDER)
        icon_e.insert(0, svc.get("icon", ""))
        icon_e.pack(side="left", padx=4, pady=8)

        # Name entry
        name_e = ctk.CTkEntry(row_frame, width=136, font=("Segoe UI", 12),
                               fg_color=DARKER_BG, border_color=BORDER)
        name_e.insert(0, svc.get("name", ""))
        name_e.pack(side="left", padx=4, pady=8)

        # URL entry
        url_e = ctk.CTkEntry(row_frame, width=236, font=("Segoe UI", 11),
                              fg_color=DARKER_BG, border_color=BORDER)
        url_e.insert(0, svc.get("url", ""))
        url_e.pack(side="left", padx=4, pady=8)

        # Category dropdown
        cat_var = ctk.StringVar(value=svc.get("category", "Other"))
        cat_dd = ctk.CTkOptionMenu(row_frame, values=_CATEGORIES,
                                    variable=cat_var, width=96,
                                    fg_color=DARKER_BG,
                                    button_color=ACCENT,
                                    font=("Segoe UI", 11))
        cat_dd.pack(side="left", padx=4, pady=8)

        # Check type dropdown
        type_var = ctk.StringVar(value=svc.get("check_type", "http"))
        type_dd = ctk.CTkOptionMenu(row_frame, values=_CHECK_TYPES,
                                     variable=type_var, width=86,
                                     fg_color=DARKER_BG,
                                     button_color=ACCENT,
                                     font=("Segoe UI", 11))
        type_dd.pack(side="left", padx=4, pady=8)

        # Delete button
        svc_id = svc.get("id", "")
        ctk.CTkButton(
            row_frame, text="✕", width=32, height=28,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2e0a0a", hover_color="#4e1a1a",
            text_color=COLOR_BAD, corner_radius=6,
            command=lambda f=row_frame: self._delete_row(f),
        ).pack(side="left", padx=(4, 8), pady=8)

        self._rows.append({
            "frame": row_frame,
            "id": svc_id,
            "enabled": enabled_var,
            "icon": icon_e,
            "name": name_e,
            "url": url_e,
            "category": cat_var,
            "check_type": type_var,
        })

    def _add_service(self):
        new_svc = {
            "id": f"custom_{len(self._rows)}",
            "name": "Новый сервис",
            "icon": "🌐",
            "category": "Other",
            "url": "https://",
            "check_url": "https://",
            "check_type": "http",
            "port": 443,
            "enabled": True,
        }
        self._add_row(new_svc)

    def _delete_row(self, frame: ctk.CTkFrame):
        self._rows = [r for r in self._rows if r["frame"] is not frame]
        frame.destroy()

    def _save(self):
        services = []
        for r in self._rows:
            url = r["url"].get().strip()
            services.append({
                "id": r["id"] or r["name"].get().lower().replace(" ", "_"),
                "name": r["name"].get().strip(),
                "icon": r["icon"].get().strip() or "🌐",
                "category": r["category"].get(),
                "url": url,
                "check_url": url,
                "check_type": r["check_type"].get(),
                "port": 443,
                "enabled": r["enabled"].get(),
            })
        save_services(services)
        self._save_btn.configure(text="✓ Сохранено", text_color=COLOR_OK)
        self.after(2000, lambda: self._save_btn.configure(
            text="💾 Сохранить", text_color="white"))
        if self._on_save:
            self._on_save()
