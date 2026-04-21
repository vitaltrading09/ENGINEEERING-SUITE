"""
sidebar.py
----------
Collapsible navigation sidebar built from the calculator registry.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont
import qtawesome as qta


SIDEBAR_EXPANDED_W = 210
SIDEBAR_COLLAPSED_W = 60


class SidebarButton(QPushButton):
    """A single navigation button that supports expanded/collapsed display."""

    def __init__(self, icon_name: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_button")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._icon = qta.icon(icon_name, color="#8b949e")
        self._icon_active = qta.icon(icon_name, color="#58a6ff")
        self._text = text
        self._expanded = True
        self._update_display()

    def _update_display(self):
        if self._expanded:
            self.setIcon(self._icon_active if self.isChecked() else self._icon)
            self.setIconSize(QSize(16, 16))
            self.setText(f"  {self._text}")
        else:
            self.setIcon(self._icon_active if self.isChecked() else self._icon)
            self.setIconSize(QSize(18, 18))
            self.setText("")

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._update_display()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_display()


class Sidebar(QWidget):
    """Collapsible sidebar with animated width transitions."""

    calculator_selected = pyqtSignal(int)  # emits index of selected calculator

    def __init__(self, calculators: list, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIDEBAR_EXPANDED_W)
        self._expanded = True
        self._buttons: list[SidebarButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 12, 10, 12)
        root.setSpacing(4)

        # Toggle button (collapse/expand)
        self.toggle_btn = QPushButton()
        self.toggle_btn.setObjectName("sidebar_toggle")
        self.toggle_btn.setIcon(qta.icon("fa5s.bars", color="#8b949e"))
        self.toggle_btn.setIconSize(QSize(16, 16))
        self.toggle_btn.setFixedHeight(36)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setToolTip("Toggle sidebar")
        self.toggle_btn.clicked.connect(self._toggle_sidebar)
        root.addWidget(self.toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)

        root.addSpacing(8)

        # Section labels — built dynamically from registry "category" fields.
        # A new QLabel is inserted whenever the category changes to a non-empty value.
        self._section_labels: list[QLabel] = []
        _current_category = None

        for i, calc in enumerate(calculators):
            cat = calc.get("category", "")
            if cat and cat != _current_category:
                _current_category = cat
                if i > 0:
                    root.addSpacing(6)          # visual gap before new section
                lbl = QLabel(cat)
                lbl.setObjectName("result_label")
                lbl.setContentsMargins(8, 0, 0, 4)
                lbl.setFont(QFont("Segoe UI", 9))
                root.addWidget(lbl)
                self._section_labels.append(lbl)

            btn = SidebarButton(calc["icon"], calc["name"])
            btn.setToolTip(calc.get("subtitle", calc["name"]))
            btn.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self._buttons.append(btn)
            root.addWidget(btn)

        root.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Version label at bottom
        self._version_lbl = QLabel("v1.0.0  •  SANS 10142-1")
        self._version_lbl.setObjectName("result_label")
        self._version_lbl.setContentsMargins(8, 0, 0, 0)
        self._version_lbl.setWordWrap(True)
        self._version_lbl.setFont(QFont("Segoe UI", 8))
        root.addWidget(self._version_lbl)

        # Select first by default
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_button_clicked(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self.calculator_selected.emit(index)

    def _toggle_sidebar(self):
        self._expanded = not self._expanded
        target_width = SIDEBAR_EXPANDED_W if self._expanded else SIDEBAR_COLLAPSED_W

        self._anim = QPropertyAnimation(self, b"minimumWidth")
        self._anim.setDuration(200)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target_width)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._anim2 = QPropertyAnimation(self, b"maximumWidth")
        self._anim2.setDuration(200)
        self._anim2.setStartValue(self.width())
        self._anim2.setEndValue(target_width)
        self._anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._anim.start()
        self._anim2.start()

        for lbl in self._section_labels:
            lbl.setVisible(self._expanded)
        self._version_lbl.setVisible(self._expanded)
        for btn in self._buttons:
            btn.set_expanded(self._expanded)
