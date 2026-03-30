# theme.py
import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".vpn_checker" / "settings.json"

# ── Status / tier colors — constant across themes ──────────────────────────
COLOR_OK       = "#4CAF50"
COLOR_WARN     = "#FF9800"
COLOR_BAD      = "#F44336"
COLOR_CHECKING = "#5b6af5"
COLOR_MUTED    = "#555566"
ACCENT_TEXT    = "#e0e0e0"

TIER_COLORS = {
    "S": "#4CAF50",
    "A": "#42a5f5",
    "B": "#FFC107",
    "C": "#FF9800",
    "F": "#F44336",
}

# ── Theme presets ──────────────────────────────────────────────────────────
THEMES = {
    "Фиолетовая": {
        "DARK_BG":   "#16161f",
        "DARKER_BG": "#111118",
        "CARD_BG":   "#1a1a26",
        "BORDER":    "#2a2a3a",
        "ACCENT":    "#5b6af5",
    },
    "Синяя": {
        "DARK_BG":   "#0d1b2a",
        "DARKER_BG": "#08121e",
        "CARD_BG":   "#112233",
        "BORDER":    "#1a3045",
        "ACCENT":    "#2196F3",
    },
    "Зелёная": {
        "DARK_BG":   "#0f1a10",
        "DARKER_BG": "#0a120b",
        "CARD_BG":   "#131f14",
        "BORDER":    "#1e3020",
        "ACCENT":    "#43A047",
    },
    "Тёплая": {
        "DARK_BG":   "#1a1410",
        "DARKER_BG": "#120f0a",
        "CARD_BG":   "#201915",
        "BORDER":    "#302218",
        "ACCENT":    "#FF7043",
    },
    "Серая": {
        "DARK_BG":   "#1a1a1a",
        "DARKER_BG": "#111111",
        "CARD_BG":   "#222222",
        "BORDER":    "#333333",
        "ACCENT":    "#78909C",
    },
}

# ── Current theme values (mutable, updated by apply_theme) ─────────────────
DARK_BG         = "#16161f"
DARKER_BG       = "#111118"
CARD_BG         = "#1a1a26"
BORDER          = "#2a2a3a"
ACCENT          = "#5b6af5"
BADGE_CHECKING_BG = "#1e1e3a"
APP_STYLE       = ""   # rebuilt by apply_theme()


# ── Style builder ──────────────────────────────────────────────────────────

def _lighten(hex_color: str, amount: int = 28) -> str:
    r = min(255, int(hex_color[1:3], 16) + amount)
    g = min(255, int(hex_color[3:5], 16) + amount)
    b = min(255, int(hex_color[5:7], 16) + amount)
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_app_style_from_dict(c: dict) -> str:
    bg     = c["DARK_BG"]
    darker = c["DARKER_BG"]
    card   = c["CARD_BG"]
    border = c["BORDER"]
    accent = c["ACCENT"]
    hover  = _lighten(accent)
    return f"""
QWidget {{
    font-family: "Segoe UI";
    font-size: 12px;
    color: #cccccc;
}}
QMainWindow, QDialog {{
    background-color: {bg};
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {darker};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
    border: none;
}}
QScrollBar:horizontal {{ height: 0; }}
QPushButton {{
    background: {accent};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0 14px;
    font-weight: bold;
}}
QPushButton:hover {{ background: {hover}; }}
QPushButton:disabled {{ background: {border}; color: {COLOR_MUTED}; }}
QLineEdit {{
    background: {darker};
    color: #cccccc;
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: {accent};
}}
QLineEdit:focus {{ border-color: {accent}; }}
QComboBox {{
    background: {darker};
    color: #cccccc;
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{ width: 0; height: 0; }}
QComboBox QAbstractItemView {{
    background: {card};
    color: #cccccc;
    border: 1px solid {border};
    selection-background-color: {accent};
    selection-color: white;
    outline: none;
}}
QCheckBox {{ spacing: 6px; color: #cccccc; background: transparent; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border};
    border-radius: 3px;
    background: {darker};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent};
}}
QLabel {{ background: transparent; }}
"""


def _build_app_style() -> str:
    return _build_app_style_from_dict({
        "DARK_BG": DARK_BG, "DARKER_BG": DARKER_BG,
        "CARD_BG": CARD_BG, "BORDER": BORDER, "ACCENT": ACCENT,
    })


# ── Persistence ────────────────────────────────────────────────────────────

def load_theme_name() -> str:
    try:
        with open(_SETTINGS_PATH, encoding="utf-8") as f:
            return json.load(f).get("theme", "Фиолетовая")
    except Exception:
        return "Фиолетовая"


def save_theme_name(name: str) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    try:
        with open(_SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    data["theme"] = name
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── Theme application ──────────────────────────────────────────────────────

def apply_theme(name: str, save: bool = True) -> None:
    """Update all module-level color globals to the named theme."""
    global DARK_BG, DARKER_BG, CARD_BG, BORDER, ACCENT, BADGE_CHECKING_BG, APP_STYLE
    t = THEMES.get(name, THEMES["Фиолетовая"])
    DARK_BG           = t["DARK_BG"]
    DARKER_BG         = t["DARKER_BG"]
    CARD_BG           = t["CARD_BG"]
    BORDER            = t["BORDER"]
    ACCENT            = t["ACCENT"]
    BADGE_CHECKING_BG = f"{ACCENT}33"
    APP_STYLE         = _build_app_style()
    if save:
        save_theme_name(name)


def preview_theme(name: str) -> None:
    """Apply only QSS preview without touching globals or persisting."""
    from PyQt5.QtWidgets import QApplication
    t = THEMES.get(name, THEMES["Фиолетовая"])
    QApplication.instance().setStyleSheet(_build_app_style_from_dict(t))


# ── Initialize with saved theme on import ─────────────────────────────────
apply_theme(load_theme_name(), save=False)
