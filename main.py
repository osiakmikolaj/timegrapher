"""
main.py
Punkt wejscia aplikacji Timegrapher - Acoustic Watch Analyzer.
"""

import sys
from PyQt6.QtWidgets import QApplication

from main_window import TimegrapherApp


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = TimegrapherApp()
    window.show()
    sys.exit(app.exec())
