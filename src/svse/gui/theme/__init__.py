from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

_THEME_DIR = Path(__file__).parent


def apply_theme(app: QApplication) -> None:
    for font_file in ("PixelifySans-Regular.ttf", "PixelifySans-Bold.ttf"):
        QFontDatabase.addApplicationFont(str(_THEME_DIR / "fonts" / font_file))

    qss_path = _THEME_DIR / "stardew.qss"
    app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
