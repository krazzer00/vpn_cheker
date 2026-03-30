# VPN Checker v2 — Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add UV build, history tab, settings/services editor, IP display, larger window, faster UI rendering, and design polish matching the approved mockup.

**Architecture:** New tabs (History, Settings) added to app.py; services.json gains `enabled` field managed by a config module; cards pre-created once for performance; IP fetched in background thread on startup; UV replaces pip for dependency management and builds.

**Tech Stack:** Python 3.11+, customtkinter, uv, requests, pillow, pyinstaller

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `pyproject.toml` | Create | uv project manifest, replaces requirements.txt |
| `build.bat` | Modify | Use `uv run pyinstaller` instead of direct call |
| `engine/config.py` | Create | services.json path resolution (dev vs frozen), load/save |
| `engine/history.py` | Create | Save/load check history to `~/.vpn_checker/history.json` |
| `tabs/history.py` | Create | History tab UI — scrollable list of past checks |
| `tabs/settings.py` | Create | Settings tab UI — services CRUD |
| `app.py` | Modify | Add History+Settings tabs, IP fetch on startup, larger window, titlebar polish |
| `tabs/full_check.py` | Modify | Pre-create cards (perf), use config module, save history after verdict |
| `widgets/service_card.py` | Modify | Left accent strip, better visual design |
| `services.json` | Modify | Add `enabled: true` to all services |
| `theme.py` | Modify | Add TIER_COLORS dict (currently duplicated in full_check.py) |

---

## Task 1: UV migration

**Files:**
- Create: `pyproject.toml`
- Modify: `build.bat`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "vpn-checker"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "customtkinter>=5.2.0",
    "ping3>=4.0.0",
    "requests>=2.31.0",
    "pillow>=10.0.0",
]

[project.optional-dependencies]
build = [
    "pyinstaller>=6.0.0",
]
dev = [
    "pytest>=8.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
]
```

- [ ] **Step 2: Install uv if not present and sync**

```bash
cd /c/Users/krazz/Desktop/vpn_cheker
pip install uv --quiet 2>/dev/null || true
uv sync --extra build --extra dev
```

Expected: uv creates `.venv`, installs all deps. Should complete without errors.

- [ ] **Step 3: Verify tests pass under uv**

```bash
uv run pytest tests/ -v
```
Expected: 21 PASSED.

- [ ] **Step 4: Update build.bat**

```bat
@echo off
echo Building VPN Checker portable exe...
uv sync --extra build
uv run pyinstaller --onefile --windowed --name VPN-Checker ^
  --add-data "services.json;." ^
  --icon icon.ico ^
  main.py
echo.
echo Done! Executable: dist\VPN-Checker.exe
pause
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml build.bat
git commit -m "build: migrate to uv, add pyproject.toml"
```

---

## Task 2: Config module + services.json enabled field

**Files:**
- Create: `engine/config.py`
- Modify: `services.json` (add `enabled` field)
- Modify: `tabs/full_check.py` (use config module)

- [ ] **Step 1: Write failing test**

```python
# tests/test_config.py
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from engine.config import load_services, save_services, get_services_path

def test_load_services_returns_list():
    services = load_services()
    assert isinstance(services, list)
    assert len(services) > 0
    assert "id" in services[0]
    assert "enabled" in services[0]

def test_save_and_reload(tmp_path):
    path = tmp_path / "services.json"
    services = [{"id": "test", "name": "Test", "icon": "🔥",
                 "category": "Other", "url": "https://test.com",
                 "check_url": "https://test.com", "check_type": "http",
                 "port": 443, "enabled": True}]
    save_services(services, path=path)
    loaded = load_services(path=path)
    assert loaded[0]["id"] == "test"
    assert loaded[0]["enabled"] is True

def test_disabled_services_have_enabled_false(tmp_path):
    path = tmp_path / "services.json"
    services = [{"id": "x", "name": "X", "icon": "X", "category": "Other",
                 "url": "https://x.com", "check_url": "https://x.com",
                 "check_type": "http", "port": 443, "enabled": False}]
    save_services(services, path=path)
    loaded = load_services(path=path)
    assert loaded[0]["enabled"] is False
```

- [ ] **Step 2: Run to verify fail**

```bash
uv run pytest tests/test_config.py -v
```
Expected: ERROR — module not found.

- [ ] **Step 3: Add `enabled: true` to all services in services.json**

Open `services.json` and add `"enabled": true` to every service entry. Result should look like:
```json
{
  "services": [
    {
      "id": "claude",
      "name": "Claude AI",
      "icon": "🤖",
      "category": "AI",
      "url": "https://api.anthropic.com",
      "check_url": "https://api.anthropic.com/v1/messages",
      "check_type": "ai_region",
      "port": 443,
      "enabled": true
    },
    ...
  ]
}
```
(Add `"enabled": true` to all 12 services.)

- [ ] **Step 4: Create engine/config.py**

```python
# engine/config.py
import json
import sys
from pathlib import Path
from typing import Optional


def get_services_path() -> Path:
    """
    Resolve services.json path.
    - Frozen exe: next to the .exe (writable), falling back to MEIPASS default.
    - Dev: project root.
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        user_path = exe_dir / "services.json"
        if user_path.exists():
            return user_path
        # First run: copy default from MEIPASS to exe directory
        default_path = Path(sys._MEIPASS) / "services.json"
        import shutil
        shutil.copy(default_path, user_path)
        return user_path
    return Path(__file__).parent.parent / "services.json"


def load_services(path: Optional[Path] = None) -> list[dict]:
    """Load services list. Missing `enabled` field defaults to True."""
    p = path or get_services_path()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    services = data["services"]
    for svc in services:
        svc.setdefault("enabled", True)
    return services


def save_services(services: list[dict], path: Optional[Path] = None) -> None:
    """Persist services list to disk."""
    p = path or get_services_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"services": services}, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 5: Run tests to verify pass**

```bash
uv run pytest tests/test_config.py -v
```
Expected: 3 PASSED.

- [ ] **Step 6: Update full_check.py to use config module**

In `tabs/full_check.py`, replace the `_get_services_path()` function and `_load_services()` with:

```python
from engine.config import load_services as _load_services_from_config

# Remove: _get_services_path(), _SERVICES_PATH, _load_services()
# Replace _load_services() calls with _load_services_from_config()
```

In `FullCheckTab.__init__`, change:
```python
self.all_services = _load_services()
```
To:
```python
self.all_services = [s for s in _load_services_from_config() if s.get("enabled", True)]
```

Add a `reload_services()` method to `FullCheckTab` (called by settings save):
```python
def reload_services(self):
    """Reload services list after settings change."""
    self.all_services = [s for s in _load_services_from_config() if s.get("enabled", True)]
    self._selected = {s["id"] for s in self.all_services}
    self._rebuild_sidebar_checkboxes()
    self._build_all_cards()
```

Also add `_rebuild_sidebar_checkboxes()`:
```python
def _rebuild_sidebar_checkboxes(self):
    """Rebuild sidebar after service list changes."""
    for w in self._sidebar_scroll.winfo_children():
        w.destroy()
    self._checkboxes.clear()
    self._populate_sidebar(self._sidebar_scroll)
```

Extract the sidebar population into `_populate_sidebar(scroll)` so it can be called both on init and on reload. (Refactor `_build_sidebar` to call `_populate_sidebar`.)

- [ ] **Step 7: Run all tests**

```bash
uv run pytest tests/ -v
```
Expected: 24 PASSED.

- [ ] **Step 8: Commit**

```bash
git add engine/config.py services.json tabs/full_check.py tests/test_config.py
git commit -m "feat: config module, services enabled field, reload_services"
```

---

## Task 3: IP/location display + window size + titlebar polish

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Implement changes in app.py**

Replace the entire `app.py` with:

```python
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
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=DARK_BG)

        self.result_queue: queue.Queue = queue.Queue()
        self._tab_refs: dict = {}  # keep refs to avoid GC

        self._build_titlebar()
        self._build_tabs()
        self._poll_queue()
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
        save_result(verdict, service_results)
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
            self.after(0, lambda: (
                self.ip_label.configure(text=text, text_color="#9090cc"),
                self.ip_dot.configure(text_color="#4CAF50"),
            ))
        except Exception:
            self.after(0, lambda: (
                self.ip_label.configure(text="IP не определён", text_color="#664444"),
                self.ip_dot.configure(text_color="#F44336"),
            ))

    def _poll_queue(self):
        try:
            while True:
                msg = self.result_queue.get_nowait()
                self.full_tab.handle_result(msg)
                self.custom_tab.handle_result(msg)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)
```

Note: `FullCheckTab` now accepts `on_check_complete` callback. This will be wired in Task 5.

- [ ] **Step 2: Verify import (stubs for missing tabs are OK for now)**

Create minimal stubs if history/settings tabs don't exist yet:

```bash
# Only run if tabs/history.py doesn't exist yet
python -c "
import sys; sys.path.insert(0, '.')
# Just check app.py syntax
import ast
ast.parse(open('app.py', encoding='utf-8').read())
print('app.py syntax OK')
"
```

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: larger window, IP/location display, titlebar traffic lights, new tab slots"
```

---

## Task 4: ServiceCard redesign with left accent strip

**Files:**
- Modify: `widgets/service_card.py`
- Modify: `theme.py` (add TIER_COLORS)

- [ ] **Step 1: Add TIER_COLORS to theme.py**

Add to `theme.py`:
```python
TIER_COLORS = {
    "S": "#4CAF50",
    "A": "#42a5f5",
    "B": "#FFC107",
    "C": "#FF9800",
    "F": "#F44336",
}
```

Remove `TIER_COLORS` dict from `tabs/full_check.py` and import from `theme` instead:
```python
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT, COLOR_MUTED, TIER_COLORS
```

- [ ] **Step 2: Rewrite widgets/service_card.py**

```python
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
```

- [ ] **Step 3: Verify import**

```bash
uv run python -c "from widgets.service_card import ServiceCard; print('OK')"
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest tests/ -v
```
Expected: All pass.

- [ ] **Step 5: Commit**

```bash
git add widgets/service_card.py theme.py tabs/full_check.py
git commit -m "feat: ServiceCard left accent strip, TIER_COLORS in theme"
```

---

## Task 5: FullCheckTab performance + history callback

**Files:**
- Modify: `tabs/full_check.py`

Key change: pre-create ALL cards once. On run, show/hide with `grid()` / `grid_remove()` instead of destroy+recreate.

- [ ] **Step 1: Rewrite tabs/full_check.py**

```python
# tabs/full_check.py
import queue
import threading
from typing import Callable, Optional

import customtkinter as ctk

from engine.checker import run_checks
from engine.config import load_services as _load_services_from_config
from widgets.service_card import ServiceCard
from widgets.speed_bar import SpeedBar
from theme import DARK_BG, DARKER_BG, BORDER, ACCENT, COLOR_MUTED, TIER_COLORS, CARD_BG


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
        right = ctk.CTkFrame(self, fg_color=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        self.speed_bar = SpeedBar(right)
        self.speed_bar.pack(fill="x", padx=14, pady=(14, 8))

        # Cards area (scrollable)
        self._cards_container = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self._cards_container.pack(fill="both", expand=True, padx=14)

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

        vt = ctk.CTkFrame(self.verdict_frame, fg_color="transparent")
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
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/ -v
```
Expected: All pass.

- [ ] **Step 3: Commit**

```bash
git add tabs/full_check.py
git commit -m "perf: pre-create cards, extract populate_sidebar, history callback"
```

---

## Task 6: History engine + tab

**Files:**
- Create: `engine/history.py`
- Create: `tabs/history.py`
- Create: `tests/test_history.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_history.py
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from engine.history import save_result, load_history, clear_history, _HISTORY_PATH

def _tmp_path(tmp_path):
    return tmp_path / "history.json"

def test_save_and_load(tmp_path):
    p = _tmp_path(tmp_path)
    verdict = {"score": 8.5, "tier": "A", "message": "Норм",
               "accessible_count": 10, "total_count": 12}
    service_results = [{"id": "github", "name": "GitHub", "accessible": True,
                         "ping_ms": 30.0, "loss_pct": 0.0}]
    with patch("engine.history._HISTORY_PATH", p):
        save_result(verdict, service_results)
        records = load_history()

    # load_history reads from real path, so mock it too
    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) == 1
    assert records[0]["score"] == 8.5
    assert records[0]["tier"] == "A"
    assert len(records[0]["services"]) == 1

def test_newest_first(tmp_path):
    p = _tmp_path(tmp_path)
    with patch("engine.history._HISTORY_PATH", p):
        for i in range(3):
            save_result({"score": float(i), "tier": "F", "message": "x",
                         "accessible_count": 0, "total_count": 1}, [])
        records = load_history()

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert records[0]["score"] == 2.0  # newest first

def test_max_100_records(tmp_path):
    p = _tmp_path(tmp_path)
    with patch("engine.history._HISTORY_PATH", p):
        for i in range(110):
            save_result({"score": 0.0, "tier": "F", "message": "x",
                         "accessible_count": 0, "total_count": 1}, [])
        records = load_history()

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) <= 100

def test_clear_history(tmp_path):
    p = _tmp_path(tmp_path)
    with patch("engine.history._HISTORY_PATH", p):
        save_result({"score": 5.0, "tier": "B", "message": "x",
                     "accessible_count": 5, "total_count": 10}, [])
        clear_history()
        records = load_history()

    with patch("engine.history._HISTORY_PATH", p):
        records = load_history()

    assert len(records) == 0
```

- [ ] **Step 2: Run to verify fail**

```bash
uv run pytest tests/test_history.py -v
```
Expected: ERROR — module not found.

- [ ] **Step 3: Create engine/history.py**

```python
# engine/history.py
import json
from datetime import datetime
from pathlib import Path

_HISTORY_DIR = Path.home() / ".vpn_checker"
_HISTORY_PATH = _HISTORY_DIR / "history.json"
_MAX_RECORDS = 100


def _ensure_dir():
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    """Load check history. Returns list newest-first."""
    if not _HISTORY_PATH.exists():
        return []
    try:
        with open(_HISTORY_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_result(verdict: dict, service_results: list[dict]) -> None:
    """Prepend a new check record. Truncates to _MAX_RECORDS."""
    _ensure_dir()
    records = load_history()
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "score": verdict["score"],
        "tier": verdict["tier"],
        "message": verdict["message"],
        "accessible_count": verdict["accessible_count"],
        "total_count": verdict["total_count"],
        "services": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "accessible": r.get("accessible", False),
                "ping_ms": r.get("ping_ms"),
                "loss_pct": r.get("loss_pct"),
            }
            for r in service_results
        ],
    }
    records.insert(0, record)
    records = records[:_MAX_RECORDS]
    with open(_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def clear_history() -> None:
    """Delete all history records."""
    if _HISTORY_PATH.exists():
        _HISTORY_PATH.unlink()
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_history.py -v
```
Expected: 4 PASSED.

- [ ] **Step 5: Create tabs/history.py**

```python
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

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="Ещё не было ни одной проверки.\nЗапусти «Полную проверку» и результаты появятся здесь.",
            font=("Segoe UI", 13),
            text_color=COLOR_MUTED,
            justify="center",
        )

    def refresh(self):
        """Reload and redraw history list."""
        for w in self._scroll.winfo_children():
            w.destroy()

        records = load_history()

        if not records:
            self._empty_label = ctk.CTkLabel(
                self._scroll,
                text="Ещё не было ни одной проверки.\nЗапусти полную проверку и результаты появятся здесь.",
                font=("Segoe UI", 13),
                text_color=COLOR_MUTED,
                justify="center",
            )
            self._empty_label.pack(pady=60)
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
```

- [ ] **Step 6: Run all tests**

```bash
uv run pytest tests/ -v
```
Expected: All pass (28 tests).

- [ ] **Step 7: Commit**

```bash
git add engine/history.py tabs/history.py tests/test_history.py
git commit -m "feat: history engine + history tab UI"
```

---

## Task 7: Settings tab

**Files:**
- Create: `tabs/settings.py`

- [ ] **Step 1: Create tabs/settings.py**

```python
# tabs/settings.py
from typing import Callable, Optional

import customtkinter as ctk

from engine.config import load_services, save_services
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

    def _load(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        self._services = load_services()
        for svc in self._services:
            self._add_row(svc)

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
```

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from tabs.settings import SettingsTab; print('OK')"
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest tests/ -v
```
Expected: All pass.

- [ ] **Step 4: Commit**

```bash
git add tabs/settings.py
git commit -m "feat: settings tab with services CRUD"
```

---

## Task 8: Wire everything — final integration

**Files:**
- Modify: `app.py` (verify new tabs load correctly, no import errors)

- [ ] **Step 1: Verify app.py imports all tabs correctly**

```bash
uv run python -c "
import customtkinter as ctk
from tabs.full_check import FullCheckTab
from tabs.custom_check import CustomCheckTab
from tabs.history import HistoryTab
from tabs.settings import SettingsTab
from engine.history import save_result, load_history
from engine.config import load_services, save_services
print('All imports OK')
"
```
Expected: `All imports OK`

- [ ] **Step 2: Run complete test suite**

```bash
uv run pytest tests/ -v --tb=short
```
Expected: All 28+ tests pass.

- [ ] **Step 3: Syntax check all modified files**

```bash
uv run python -c "
import ast, os
files = [
    'app.py', 'theme.py',
    'tabs/full_check.py', 'tabs/custom_check.py',
    'tabs/history.py', 'tabs/settings.py',
    'widgets/service_card.py', 'widgets/speed_bar.py',
    'engine/config.py', 'engine/history.py',
    'engine/checker.py', 'engine/verdict.py',
]
for f in files:
    ast.parse(open(f, encoding='utf-8').read())
    print(f'  OK {f}')
print('All syntax checks passed')
"
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: wire all tabs, full integration"
```

---

## Task 9: Build exe + push to master

- [ ] **Step 1: Run the build**

```bash
cd /c/Users/krazz/Desktop/vpn_cheker
uv sync --extra build
uv run pyinstaller --onefile --windowed --name VPN-Checker \
  --add-data "services.json;." \
  --icon icon.ico \
  main.py
```
Expected: `dist/VPN-Checker.exe` created, size > 15 MB.

- [ ] **Step 2: Verify exe exists**

```bash
ls -lh dist/VPN-Checker.exe
```
Expected: File exists.

- [ ] **Step 3: Commit and push to master**

```bash
git add -A
git commit -m "build: rebuild portable exe with uv, v2 features"
git checkout master
git merge feature/implementation --no-ff -m "feat: VPN Checker v2 - history, settings, IP display, design polish"
git push origin master
git checkout feature/implementation
git push origin feature/implementation
```
