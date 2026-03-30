# theme.py
DARK_BG = "#16161f"
DARKER_BG = "#111118"
CARD_BG = "#1a1a26"
BORDER = "#2a2a3a"
ACCENT = "#5b6af5"

COLOR_OK = "#4CAF50"
COLOR_WARN = "#FF9800"
COLOR_BAD = "#F44336"
COLOR_CHECKING = "#5b6af5"
COLOR_MUTED = "#555566"

BADGE_CHECKING_BG = "#1e1e3a"
ACCENT_TEXT = "#e0e0e0"

TIER_COLORS = {
    "S": "#4CAF50",
    "A": "#42a5f5",
    "B": "#FFC107",
    "C": "#FF9800",
    "F": "#F44336",
}

APP_STYLE = f"""
QWidget {{
    font-family: "Segoe UI";
    font-size: 12px;
    color: #cccccc;
}}
QMainWindow, QDialog {{
    background-color: {DARK_BG};
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {DARKER_BG};
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #3a3a4a;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
    border: none;
}}
QScrollBar:horizontal {{
    height: 0;
}}
QPushButton {{
    background: {ACCENT};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0 14px;
    font-weight: bold;
}}
QPushButton:hover {{ background: #7b8ef5; }}
QPushButton:disabled {{ background: #2a2a3a; color: {COLOR_MUTED}; }}
QLineEdit {{
    background: {DARKER_BG};
    color: #cccccc;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox {{
    background: {DARKER_BG};
    color: #cccccc;
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox::down-arrow {{ width: 0; height: 0; }}
QComboBox QAbstractItemView {{
    background: {CARD_BG};
    color: #cccccc;
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: white;
    outline: none;
}}
QCheckBox {{ spacing: 6px; color: #cccccc; background: transparent; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 3px;
    background: {DARKER_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QLabel {{ background: transparent; }}
"""
