"""
header.py
---------
Top header bar: app branding, active calculator title, theme toggle.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
import qtawesome as qta


class HeaderBar(QWidget):
    theme_toggled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(0)

        # App icon + title
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("fa5s.bolt", color="#58a6ff").pixmap(20, 20))
        layout.addWidget(icon_lbl)

        layout.addSpacing(10)

        title = QLabel("⚡ Engineering Suite")
        title.setObjectName("header_title")
        layout.addWidget(title)

        layout.addSpacing(16)

        # Separator
        sep = QLabel("|")
        sep.setObjectName("header_subtitle")
        layout.addWidget(sep)

        layout.addSpacing(16)

        # Active calculator name
        self.subtitle_lbl = QLabel("Select a calculator")
        self.subtitle_lbl.setObjectName("header_subtitle")
        layout.addWidget(self.subtitle_lbl)

        layout.addStretch()

        # Company label
        company_lbl = QLabel("Solareff Engineering")
        company_lbl.setObjectName("header_subtitle")
        layout.addWidget(company_lbl)

        layout.addSpacing(20)

        # Theme toggle button
        self._dark = True
        self.theme_btn = QPushButton("☀  Light Mode")
        self.theme_btn.setObjectName("theme_toggle_btn")
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

    def set_active_calculator(self, name: str, subtitle: str = ""):
        text = name
        if subtitle:
            text += f"  —  {subtitle}"
        self.subtitle_lbl.setText(text)

    def _toggle_theme(self):
        self._dark = not self._dark
        self.theme_btn.setText("🌙  Dark Mode" if not self._dark else "☀  Light Mode")
        self.theme_toggled.emit()
