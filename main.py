"""
main.py
-------
Entry point for the Engineering Calculator Suite.
Run with:  python main.py   (or double-click — auto-boots into .venv)
"""

import sys
import os
from pathlib import Path

# ── Auto-bootstrap ────────────────────────────────────────────────────────────
# If launched with the system Python (double-click, wrong IDE interpreter, etc.)
# re-launch using the project's .venv so all dependencies are available.
_HERE = Path(__file__).resolve().parent
_VENV_PY = (
    _HERE / ".venv" / "Scripts" / "python.exe"   # Windows
    if sys.platform == "win32" else
    _HERE / ".venv" / "bin" / "python"            # Linux / macOS
)
if _VENV_PY.exists() and Path(sys.executable).resolve() != _VENV_PY.resolve():
    import subprocess
    sys.exit(subprocess.call([str(_VENV_PY), str(Path(__file__).resolve())] + sys.argv[1:]))
# ─────────────────────────────────────────────────────────────────────────────

# Ensure the project root is on sys.path so all imports resolve
sys.path.insert(0, str(_HERE))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt

from app.main_window import MainWindow


def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Engineering Calculator Suite")
    app.setOrganizationName("Solareff Engineering")
    app.setApplicationVersion("1.0.0")

    # Global font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
