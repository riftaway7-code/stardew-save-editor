from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from svse.gui.main_window import MainWindow
from svse.gui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Stardew Valley Save Editor")
    apply_theme(app)
    window = MainWindow()
    window.show()
    window.device_bar.refresh_devices()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
