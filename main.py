# main.py
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont

from theme import APP_STYLE, DARK_BG, DARKER_BG, CARD_BG, ACCENT, BORDER


def _apply_dark_palette(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(DARK_BG))
    pal.setColor(QPalette.WindowText,      QColor("#cccccc"))
    pal.setColor(QPalette.Base,            QColor(DARKER_BG))
    pal.setColor(QPalette.AlternateBase,   QColor(CARD_BG))
    pal.setColor(QPalette.ToolTipBase,     QColor(CARD_BG))
    pal.setColor(QPalette.ToolTipText,     QColor("#cccccc"))
    pal.setColor(QPalette.Text,            QColor("#cccccc"))
    pal.setColor(QPalette.Button,          QColor(CARD_BG))
    pal.setColor(QPalette.ButtonText,      QColor("#cccccc"))
    pal.setColor(QPalette.BrightText,      QColor("white"))
    pal.setColor(QPalette.Link,            QColor(ACCENT))
    pal.setColor(QPalette.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("white"))
    app.setPalette(pal)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    _apply_dark_palette(app)
    app.setStyleSheet(APP_STYLE)

    from app import VpnCheckerApp
    window = VpnCheckerApp()
    window.show()
    sys.exit(app.exec_())
