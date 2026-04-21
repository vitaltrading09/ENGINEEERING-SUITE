"""
main_window.py
--------------
Main application window: sidebar + header + stacked content area.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from app.sidebar import Sidebar
from app.header import HeaderBar
from app.theme import DARK_THEME, LIGHT_THEME
from app.calculator_registry import CALCULATORS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Engineering Calculator Suite — Solareff")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self._dark_mode = True

        # Apply default font
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        self._build_ui()
        self._apply_theme()

        # Select first calculator on launch
        if CALCULATORS:
            self._switch_calculator(0)

    def _build_ui(self):
        # Root widget
        root_widget = QWidget()
        root_widget.setObjectName("central_widget")
        self.setCentralWidget(root_widget)

        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        self.header = HeaderBar(self)
        self.header.theme_toggled.connect(self._toggle_theme)
        root_layout.addWidget(self.header)

        # Body (sidebar + content)
        body = QWidget()
        body.setObjectName("central_widget")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(CALCULATORS, self)
        self.sidebar.calculator_selected.connect(self._switch_calculator)
        body_layout.addWidget(self.sidebar)

        # Content stack
        content_container = QWidget()
        content_container.setObjectName("content_area")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")

        # Instantiate each panel — wrap in QScrollArea if scrollable=True (default)
        self._calc_widgets = []
        for calc_def in CALCULATORS:
            widget = calc_def["widget_class"]()
            self._calc_widgets.append(widget)

            if calc_def.get("scrollable", True):
                scroll = QScrollArea()
                scroll.setObjectName("content_area")
                scroll.setWidget(widget)
                scroll.setWidgetResizable(True)
                scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.stack.addWidget(scroll)
            else:
                widget.setObjectName("content_area")
                self.stack.addWidget(widget)

        content_layout.addWidget(self.stack)
        body_layout.addWidget(content_container)

        root_layout.addWidget(body)

        # ── Connect optional sub-tab subtitle signals ─────────────────────────
        # Widgets that expose tab_subtitle_changed (e.g. PVSystemWidget) emit
        # the active sub-tab name so the header subtitle stays in sync.
        for i, widget in enumerate(self._calc_widgets):
            if hasattr(widget, "tab_subtitle_changed"):
                widget.tab_subtitle_changed.connect(
                    self._make_subtitle_handler(i))

    def _make_subtitle_handler(self, calc_idx: int):
        """Return a slot that updates the header subtitle for *calc_idx*."""
        def _handler(subtitle: str):
            if self.stack.currentIndex() == calc_idx:
                calc = CALCULATORS[calc_idx]
                self.header.set_active_calculator(calc["name"], subtitle)
        return _handler

    def _switch_calculator(self, index: int):
        self.stack.setCurrentIndex(index)
        calc = CALCULATORS[index]
        self.header.set_active_calculator(calc["name"], calc.get("subtitle", ""))

        # Some panels (e.g. Screen Report Builder) request a maximised window.
        widget = self._calc_widgets[index]
        if getattr(widget, "prefer_maximized", False):
            QTimer.singleShot(0, self.showMaximized)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _apply_theme(self):
        stylesheet = DARK_THEME if self._dark_mode else LIGHT_THEME
        self.setStyleSheet(stylesheet)
