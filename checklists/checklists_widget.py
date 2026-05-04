"""
checklists_widget.py
--------------------
Interactive HTML checklist viewer.

Renders interactive HTML/JS checklists (FAT, commissioning, inspection forms)
using QWebEngineView so checkboxes, progress bars and info panels all work.

If PyQt6-WebEngine is not installed, falls back gracefully to an "Open in
Browser" button so the checklist still works — just in the system browser.
"""

import os
import glob
import webbrowser
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QFrame, QSplitter, QSizePolicy,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
import qtawesome as qta

# ── Optional WebEngine ────────────────────────────────────────────────────────
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


# Human-readable names for checklist files
_DISPLAY_NAMES = {
    "FAT_Checklist_RMU_Transformer.html":
        "FAT — MV RMU & Distribution Transformer",
}


class ChecklistsWidget(QWidget):
    """Sidebar panel that lists and renders interactive HTML checklists."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files_dir = Path(__file__).parent / "files"
        self._current_path: Path | None = None
        self._build_ui()
        self._load_list()

    # ─────────────────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 32)
        root.setSpacing(20)

        # ── Title row ─────────────────────────────────────────────────────────
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.clipboard-check", color="#58a6ff").pixmap(28, 28))
        tr.addWidget(ico)
        tr.addSpacing(10)
        tc = QVBoxLayout()
        tc.setSpacing(2)
        h1 = QLabel("Checklists")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title")
        tc.addWidget(h1)
        sub = QLabel("FAT, Commissioning & Inspection Checklists")
        sub.setObjectName("header_subtitle")
        tc.addWidget(sub)
        tr.addLayout(tc)
        tr.addStretch()
        root.addLayout(tr)
        root.addWidget(_sep())

        # ── Body splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left — list
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Available Checklists")
        lbl.setStyleSheet("font-weight:bold;color:#c9d1d9;font-size:14px;")
        ll.addWidget(lbl)

        self._list = QListWidget()
        self._list.setStyleSheet("""
            QListWidget {
                background:#0d1117; border:1px solid #30363d;
                border-radius:6px; padding:5px;
            }
            QListWidget::item {
                padding:10px; border-bottom:1px solid #21262d; color:#c9d1d9;
            }
            QListWidget::item:selected {
                background:#1f3a5f; border-radius:4px; color:#e6edf3;
            }
        """)
        self._list.itemSelectionChanged.connect(self._on_selected)
        ll.addWidget(self._list)

        splitter.addWidget(left)

        # Right — viewer
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        if _HAS_WEBENGINE:
            self._view = QWebEngineView()
            self._view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            self._view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            self._view.setStyleSheet(
                "border:1px solid #30363d; border-radius:6px;")
            rl.addWidget(self._view, 1)

            # Open-in-browser shortcut button
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            self._browser_btn = QPushButton(
                "  Open in Browser  (for printing / PDF export)")
            self._browser_btn.setIcon(
                qta.icon("fa5s.external-link-alt", color="#8b949e"))
            self._browser_btn.setObjectName("secondary_btn")
            self._browser_btn.setFixedHeight(30)
            self._browser_btn.clicked.connect(self._open_in_browser)
            self._browser_btn.setVisible(False)
            btn_row.addWidget(self._browser_btn)
            rl.addLayout(btn_row)

        else:
            # ── Fallback: no WebEngine installed ──────────────────────────────
            fallback = QWidget()
            fl = QVBoxLayout(fallback)
            fl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            warn_ico = QLabel()
            warn_ico.setPixmap(
                qta.icon("fa5s.info-circle", color="#58a6ff").pixmap(48, 48))
            warn_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fl.addWidget(warn_ico)

            fl.addSpacing(12)
            msg = QLabel(
                "The embedded checklist viewer requires the\n"
                "<b>PyQt6-WebEngine</b> package.\n\n"
                "Run the following in your virtual environment,\n"
                "then restart the app:\n\n"
                "<code>pip install PyQt6-WebEngine</code>"
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setObjectName("header_subtitle")
            msg.setWordWrap(True)
            fl.addWidget(msg)

            fl.addSpacing(20)
            self._fallback_btn = QPushButton("  Open Selected Checklist in Browser")
            self._fallback_btn.setIcon(
                qta.icon("fa5s.external-link-alt", color="white"))
            self._fallback_btn.setObjectName("primary_btn")
            self._fallback_btn.setFixedHeight(40)
            self._fallback_btn.setMinimumWidth(280)
            self._fallback_btn.clicked.connect(self._open_in_browser)
            fl.addWidget(self._fallback_btn, 0, Qt.AlignmentFlag.AlignCenter)

            rl.addWidget(fallback, 1)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)   # list  ~20%
        splitter.setStretchFactor(1, 4)   # viewer ~80%
        root.addWidget(splitter, 1)

    # ─────────────────────────────────────────────────────────────────────────
    # List population
    # ─────────────────────────────────────────────────────────────────────────

    def _load_list(self):
        self._list.clear()
        html_files = sorted(self._files_dir.glob("*.html"))
        for path in html_files:
            display = _DISPLAY_NAMES.get(path.name, path.stem.replace("_", " "))
            item = QListWidgetItem(
                qta.icon("fa5s.clipboard-check", color="#58a6ff"), display)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self._list.addItem(item)

        if self._list.count():
            self._list.setCurrentRow(0)

    # ─────────────────────────────────────────────────────────────────────────
    # Selection handler
    # ─────────────────────────────────────────────────────────────────────────

    def _on_selected(self):
        items = self._list.selectedItems()
        if not items:
            return
        path = items[0].data(Qt.ItemDataRole.UserRole)
        self._current_path = Path(path)

        if _HAS_WEBENGINE:
            self._view.setUrl(QUrl.fromLocalFile(path))
            self._browser_btn.setVisible(True)

    # ─────────────────────────────────────────────────────────────────────────
    # Open in system browser
    # ─────────────────────────────────────────────────────────────────────────

    def _open_in_browser(self):
        if self._current_path and self._current_path.exists():
            webbrowser.open(self._current_path.as_uri())
