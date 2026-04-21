"""
pv_layout_widget.py
-------------------
PV Layout & String Designer — main widget.

Left panel  : Inverter setup, Roof Sections, String list + action buttons
Right panel : Interactive LayoutCanvas with toolbar

Workflow:
  1. Configure inverters (number of MPPTs, strings/MPPT) and panels per string
  2. Import DXF file → panels appear on canvas
  3. Draw roof section polygons on canvas (optional — sets same-MPPT rule)
  4. Click "Auto-String" to run the algorithm
      OR click "Manual String" then click panels in order
  5. Export to Excel
"""
from __future__ import annotations

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSizePolicy, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QListWidgetItem, QSpinBox, QFrame, QSplitter, QScrollArea,
    QDialog, QDialogButtonBox, QLineEdit, QDoubleSpinBox,
    QAbstractItemView, QInputDialog,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.pv_layout.canvas_view import (
    LayoutCanvas, PANEL_COLORS,
    MODE_SELECT, MODE_ROOF_DRAW, MODE_MANUAL,
)
from calculators.pv_layout.stringing_algo import (
    auto_string, InverterConfig, StringResult, AssignmentResult,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper widgets
# ─────────────────────────────────────────────────────────────────────────────

def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _btn(text, icon_name, obj_name, icon_color="#8b949e", height=34):
    b = QPushButton(text)
    b.setObjectName(obj_name)
    b.setIcon(qta.icon(icon_name, color=icon_color))
    b.setIconSize(QSize(14, 14))
    b.setFixedHeight(height)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


# ─────────────────────────────────────────────────────────────────────────────
# Section-name + angle dialog
# ─────────────────────────────────────────────────────────────────────────────

class _SectionDialog(QDialog):
    def __init__(self, default_name="Section 1", default_angle=20.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Roof Section")
        self.setMinimumWidth(300)
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Section name:"))
        self.name_edit = QLineEdit(default_name)
        lay.addWidget(self.name_edit)

        lay.addWidget(QLabel("Roof angle (°):"))
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(0, 90)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setValue(default_angle)
        lay.addWidget(self.angle_spin)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def values(self):
        return self.name_edit.text().strip() or "Section", self.angle_spin.value()


# ─────────────────────────────────────────────────────────────────────────────
# CloudConvert API key dialog
# ─────────────────────────────────────────────────────────────────────────────

class _CloudKeyDialog(QDialog):
    """Enter / clear a CloudConvert API key."""

    def __init__(self, current_key: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CloudConvert API Key")
        self.setMinimumWidth(420)
        self._action  = "cancel"
        self._new_key = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        # Info label
        info = QLabel(
            "CloudConvert converts DWG files online — no local software needed.\n"
            "Free plan: 25 conversions / day\n\n"
            "Get your API key (v2) at:\n"
            "https://cloudconvert.com/dashboard/api/v2/keys"
        )
        info.setObjectName("header_subtitle")
        info.setWordWrap(True)
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(info)

        lay.addWidget(_sep())

        # Current status
        if current_key:
            masked = current_key[:6] + "..." + current_key[-4:] if len(current_key) > 10 else "***"
            status_txt = f"Current key: {masked}  (saved)"
            status_color = "#3fb950"
        else:
            status_txt  = "No key saved"
            status_color = "#8b949e"
        status_lbl = QLabel(status_txt)
        status_lbl.setStyleSheet(f"color: {status_color}; font-style: italic;")
        lay.addWidget(status_lbl)

        # Key input row
        key_row = QHBoxLayout()
        key_row.addWidget(QLabel("API Key:"))
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setPlaceholderText("Paste your v2 API key here...")
        if current_key:
            self._key_edit.setText(current_key)
        key_row.addWidget(self._key_edit, 1)

        # Show / hide toggle
        self._show_btn = QPushButton("Show")
        self._show_btn.setFixedWidth(54)
        self._show_btn.setCheckable(True)
        self._show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_btn.toggled.connect(self._toggle_visibility)
        key_row.addWidget(self._show_btn)
        lay.addLayout(key_row)

        lay.addWidget(_sep())

        # Buttons
        btn_row = QHBoxLayout()
        save_btn  = QPushButton("Save Key")
        clear_btn = QPushButton("Clear Key")
        cancel_btn = QPushButton("Cancel")
        save_btn.setObjectName("primary_btn")
        clear_btn.setObjectName("danger_btn")
        save_btn.clicked.connect(self._on_save)
        clear_btn.clicked.connect(self._on_clear)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _toggle_visibility(self, checked: bool):
        self._key_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self._show_btn.setText("Hide" if checked else "Show")

    def _on_save(self):
        key = self._key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Empty Key", "Please paste your API key first.")
            return
        self._action  = "save"
        self._new_key = key
        self.accept()

    def _on_clear(self):
        self._action = "clear"
        self.accept()

    def result_values(self) -> tuple[str, str]:
        """Returns (action, key) where action is 'save', 'clear', or 'cancel'."""
        return self._action, self._new_key


# ─────────────────────────────────────────────────────────────────────────────
# "No converter found" dialog — explains options AND lets user enter a
# CloudConvert key inline so they can convert in one step.
# ─────────────────────────────────────────────────────────────────────────────

class _NoConverterDialog(QDialog):
    """
    Shown when no DWG converter is detected.
    Combines install instructions with an inline CloudConvert key entry.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DWG Converter Required")
        self.setMinimumWidth(480)
        self._key = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        # ── Local converter options ──────────────────────────────────────────
        local_lbl = QLabel("No local DWG converter was found.")
        local_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        lay.addWidget(local_lbl)

        local_note = QLabel(
            "Install a free local converter and restart, then re-import:\n\n"
            "  ODA File Converter (Windows installer):\n"
            "  https://www.opendesign.com/guestfiles/oda_file_converter\n\n"
            "  LibreDWG  (open-source, command-line):\n"
            "  https://www.gnu.org/software/libredwg/"
        )
        local_note.setObjectName("header_subtitle")
        local_note.setWordWrap(True)
        local_note.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(local_note)

        lay.addWidget(_sep())

        # ── CloudConvert inline entry ────────────────────────────────────────
        cc_title = QLabel("Or convert online right now with CloudConvert:")
        cc_title.setStyleSheet("font-weight: bold; color: #58a6ff; font-size: 13px;")
        lay.addWidget(cc_title)

        cc_note = QLabel(
            "Free plan: 25 conversions / day  |  No software to install\n"
            "Get your free API v2 key at:\n"
            "https://cloudconvert.com/dashboard/api/v2/keys"
        )
        cc_note.setObjectName("header_subtitle")
        cc_note.setWordWrap(True)
        cc_note.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(cc_note)

        # Key input row
        key_row = QHBoxLayout()
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setPlaceholderText("Paste CloudConvert API v2 key here...")
        self._key_edit.textChanged.connect(self._on_key_changed)
        key_row.addWidget(self._key_edit, 1)

        self._show_btn = QPushButton("Show")
        self._show_btn.setFixedWidth(52)
        self._show_btn.setCheckable(True)
        self._show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_btn.toggled.connect(self._toggle_vis)
        key_row.addWidget(self._show_btn)
        lay.addLayout(key_row)

        lay.addWidget(_sep())

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._convert_btn = QPushButton("Save Key & Convert")
        self._convert_btn.setObjectName("primary_btn")
        self._convert_btn.setEnabled(False)
        self._convert_btn.setFixedHeight(34)
        self._convert_btn.clicked.connect(self._on_convert)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(34)
        cancel_btn.clicked.connect(self.reject)

        btn_row.addWidget(self._convert_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        lay.addLayout(btn_row)

    def _toggle_vis(self, checked: bool):
        self._key_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self._show_btn.setText("Hide" if checked else "Show")

    def _on_key_changed(self, text: str):
        self._convert_btn.setEnabled(bool(text.strip()))

    def _on_convert(self):
        self._key = self._key_edit.text().strip()
        self.accept()

    def get_key(self) -> str:
        return self._key


# ─────────────────────────────────────────────────────────────────────────────
# Main widget
# ─────────────────────────────────────────────────────────────────────────────

class PVLayoutWidget(BaseCalculator):
    calculator_name  = "PV Layout & Stringing"
    sans_reference   = "IEC 62548  •  Solareff Engineering"
    prefer_maximized = True

    # Palette for roof sections (cycles)
    _SEC_COLORS = [
        "#58a6ff", "#3fb950", "#f0883e", "#d2a8ff",
        "#ffa657", "#79c0ff", "#56d364", "#ff7b72",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── State ──────────────────────────────────────────────────────────────
        self._panels:        list = []   # list[ParsedPanel]
        self._strings:       list = []   # list[StringResult]
        self._roof_sections: list = []   # list[dict] id,name,angle,color,points
        self._next_sec_id:   int  = 1
        self._manual_active: bool = False

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        root.addWidget(splitter)

        splitter.addWidget(self._build_left())
        splitter.addWidget(self._build_right())
        splitter.setSizes([300, 900])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(310)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        inner = QWidget()
        lay   = QVBoxLayout(inner)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        lay.addWidget(self._build_inverter_group())
        lay.addWidget(self._build_roof_group())
        lay.addWidget(self._build_string_list())
        lay.addWidget(_sep())
        lay.addLayout(self._build_action_buttons())

        # Status label
        self._status_lbl = QLabel("Panels: 0  |  Assigned: 0  |  Strings: 0")
        self._status_lbl.setObjectName("header_subtitle")
        self._status_lbl.setWordWrap(True)
        lay.addWidget(self._status_lbl)

        lay.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _build_inverter_group(self) -> QGroupBox:
        grp = QGroupBox("Inverter Setup")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        # Panels per string
        row = QHBoxLayout()
        row.addWidget(QLabel("Panels per string:"))
        self._panels_per_str = QSpinBox()
        self._panels_per_str.setRange(1, 100)
        self._panels_per_str.setValue(10)
        row.addWidget(self._panels_per_str)
        lay.addLayout(row)

        # Inverter table
        self._inv_table = QTableWidget(0, 3)
        self._inv_table.setHorizontalHeaderLabels(["Inv #", "MPPTs", "Str/MPPT"])
        self._inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._inv_table.setFixedHeight(130)
        self._inv_table.verticalHeader().setVisible(False)
        self._inv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        lay.addWidget(self._inv_table)
        self._add_inverter_row(1, 2, 2)   # default: 1 inverter, 2 MPPTs, 2 strings/MPPT

        btn_row = QHBoxLayout()
        b_add = _btn("Add Inverter",    "fa5s.plus",  "secondary_btn")
        b_rem = _btn("Remove",          "fa5s.minus", "danger_btn")
        b_add.clicked.connect(self._add_inverter)
        b_rem.clicked.connect(self._remove_inverter)
        btn_row.addWidget(b_add)
        btn_row.addWidget(b_rem)
        lay.addLayout(btn_row)
        return grp

    def _build_roof_group(self) -> QGroupBox:
        grp = QGroupBox("Roof Sections")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        note = QLabel("Panels in same section share one MPPT tracker.")
        note.setObjectName("header_subtitle")
        note.setWordWrap(True)
        lay.addWidget(note)

        self._sec_table = QTableWidget(0, 3)
        self._sec_table.setHorizontalHeaderLabels(["Name", "Angle°", "Colour"])
        self._sec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._sec_table.setFixedHeight(130)
        self._sec_table.verticalHeader().setVisible(False)
        self._sec_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._sec_table.cellDoubleClicked.connect(self._sec_table_double_click)
        lay.addWidget(self._sec_table)

        btn_row = QHBoxLayout()
        b_draw = _btn("✏  Draw on Canvas", "fa5s.draw-polygon", "secondary_btn", "#58a6ff")
        b_rem  = _btn("Remove",            "fa5s.minus",        "danger_btn")
        b_draw.clicked.connect(self._start_draw_section)
        b_rem.clicked.connect(self._remove_section)
        btn_row.addWidget(b_draw)
        btn_row.addWidget(b_rem)
        lay.addLayout(btn_row)
        return grp

    def _build_string_list(self) -> QGroupBox:
        grp = QGroupBox("Strings")
        lay = QVBoxLayout(grp)
        lay.setSpacing(4)

        self._str_list = QListWidget()
        self._str_list.setFixedHeight(180)
        self._str_list.setStyleSheet(
            "QListWidget { background: #0d1117; border: 1px solid #30363d; }"
            "QListWidget::item { padding: 3px 6px; border-bottom: 1px solid #21262d; }"
            "QListWidget::item:selected { background: #1f3a5f; }"
        )
        self._str_list.itemClicked.connect(self._on_string_clicked)
        lay.addWidget(self._str_list)
        return grp

    def _build_action_buttons(self) -> QVBoxLayout:
        lay = QVBoxLayout()
        lay.setSpacing(6)

        self._btn_import     = _btn("🔍  Import DXF / DWG",   "fa5s.file-import",  "secondary_btn", "#8b949e", 36)
        self._btn_cloud_key  = _btn("☁  Cloud API Key...",   "fa5s.key",          "secondary_btn", "#58a6ff", 28)
        self._btn_auto       = _btn("⚡  Auto-String",        "fa5s.magic",        "primary_btn",   "#ffffff",  36)
        self._btn_manual     = _btn("✋  Manual String",      "fa5s.hand-pointer", "secondary_btn", "#f0883e",  36)
        self._btn_clear      = _btn("🗑  Clear Strings",      "fa5s.trash",        "danger_btn",    "#f85149",  36)
        self._btn_export     = _btn("📊  Export Excel",       "fa5s.file-excel",   "secondary_btn", "#3fb950",  36)

        self._btn_export.setEnabled(False)
        self._btn_cloud_key.setToolTip(
            "Configure a CloudConvert API key for online DWG conversion\n"
            "(no local software required).\n"
            "Get a free key at: https://cloudconvert.com/dashboard/api/v2/keys"
        )

        self._btn_import.clicked.connect(self._import_dxf)
        self._btn_cloud_key.clicked.connect(self._set_cloudconvert_key)
        self._btn_auto.clicked.connect(self._auto_string)
        self._btn_manual.clicked.connect(self._toggle_manual_string)
        self._btn_clear.clicked.connect(self._clear_strings)
        self._btn_export.clicked.connect(self._export_excel)

        for b in [self._btn_import, self._btn_cloud_key, self._btn_auto,
                  self._btn_manual, self._btn_clear, self._btn_export]:
            lay.addWidget(b)

        return lay

    # ── Right panel ───────────────────────────────────────────────────────────

    def _build_right(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        b_fit  = _btn("Fit",      "fa5s.expand-arrows-alt", "secondary_btn", "#8b949e", 30)
        b_zin  = _btn("+",        "fa5s.search-plus",       "secondary_btn", "#8b949e", 30)
        b_zout = _btn("−",        "fa5s.search-minus",      "secondary_btn", "#8b949e", 30)

        b_fit.setFixedWidth(60)
        b_zin.setFixedWidth(40)
        b_zout.setFixedWidth(40)

        b_fit.clicked.connect(lambda: self._canvas.fit_view())
        b_zin.clicked.connect(lambda: self._canvas.scale(1.2, 1.2))
        b_zout.clicked.connect(lambda: self._canvas.scale(1/1.2, 1/1.2))

        self._mode_lbl = QLabel("Mode: Select  |  Scroll to zoom  |  Middle-drag or Space+drag to pan")
        self._mode_lbl.setObjectName("header_subtitle")

        toolbar.addWidget(b_fit)
        toolbar.addWidget(b_zin)
        toolbar.addWidget(b_zout)
        toolbar.addWidget(_sep_v())
        toolbar.addWidget(self._mode_lbl)
        toolbar.addStretch()
        lay.addLayout(toolbar)

        # Canvas
        self._canvas = LayoutCanvas()
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay.addWidget(self._canvas)

        # Connect canvas signals
        self._canvas.sig_roof_section_drawn.connect(self._on_roof_section_drawn)
        self._canvas.sig_manual_string_done.connect(self._on_manual_string_done)
        self._canvas.sig_selection_changed.connect(self._on_selection_changed)

        return container

    # ─────────────────────────────────────────────────────────────────────────
    # Inverter table helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _add_inverter_row(self, inv_num: int, mppts: int, strings_per_mppt: int):
        r = self._inv_table.rowCount()
        self._inv_table.insertRow(r)

        num_item = QTableWidgetItem(str(inv_num))
        num_item.setFlags(num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._inv_table.setItem(r, 0, num_item)

        for col, val in [(1, mppts), (2, strings_per_mppt)]:
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._inv_table.setItem(r, col, item)

    def _add_inverter(self):
        n = self._inv_table.rowCount() + 1
        self._add_inverter_row(n, 2, 2)

    def _remove_inverter(self):
        row = self._inv_table.currentRow()
        if row >= 0:
            self._inv_table.removeRow(row)
            # Re-number
            for r in range(self._inv_table.rowCount()):
                self._inv_table.item(r, 0).setText(str(r + 1))

    def _read_inverter_configs(self) -> list[InverterConfig]:
        configs = []
        for r in range(self._inv_table.rowCount()):
            try:
                inv_id = int(self._inv_table.item(r, 0).text())
                mppts  = max(1, int(self._inv_table.item(r, 1).text() or "1"))
                s_mppt = max(1, int(self._inv_table.item(r, 2).text() or "1"))
                configs.append(InverterConfig(id=inv_id, num_mppts=mppts, strings_per_mppt=s_mppt))
            except (ValueError, AttributeError):
                pass
        return configs

    # ─────────────────────────────────────────────────────────────────────────
    # Roof section table helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _add_section_row(self, sec_id: int, name: str, angle: float, color: str):
        r = self._sec_table.rowCount()
        self._sec_table.insertRow(r)

        # Store sec_id in user data of first item
        n_item = QTableWidgetItem(name)
        n_item.setData(Qt.ItemDataRole.UserRole, sec_id)
        self._sec_table.setItem(r, 0, n_item)

        a_item = QTableWidgetItem(str(angle))
        a_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sec_table.setItem(r, 1, a_item)

        c_item = QTableWidgetItem("  " + color)
        c_item.setBackground(QColor(color))
        c_item.setForeground(QColor(color))
        c_item.setFlags(c_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._sec_table.setItem(r, 2, c_item)

    def _sec_table_double_click(self, row, col):
        """Double-click colour cell to change colour."""
        if col != 2:
            return
        from PyQt6.QtWidgets import QColorDialog
        item = self._sec_table.item(row, 2)
        current = QColor(item.background())
        new_col = QColorDialog.getColor(current, self, "Pick Section Colour")
        if new_col.isValid():
            hex_c = new_col.name()
            item.setBackground(new_col)
            item.setForeground(new_col)
            item.setText("  " + hex_c)
            # Update stored section
            sec_id = self._sec_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for sec in self._roof_sections:
                if sec["id"] == sec_id:
                    sec["color"] = hex_c
                    # Re-draw section on canvas
                    self._canvas.remove_roof_section(sec_id)
                    self._canvas.add_roof_section(
                        sec_id, sec["points"], sec["name"], sec["angle"], new_col)
                    break

    def _remove_section(self):
        row = self._sec_table.currentRow()
        if row < 0:
            return
        item = self._sec_table.item(row, 0)
        if not item:
            return
        sec_id = item.data(Qt.ItemDataRole.UserRole)
        self._sec_table.removeRow(row)
        self._canvas.remove_roof_section(sec_id)
        self._roof_sections = [s for s in self._roof_sections if s["id"] != sec_id]

    def _start_draw_section(self):
        if not self._panels:
            QMessageBox.information(self, "Import First",
                "Import a DXF file first so you can draw sections over the panels.")
            return
        self._canvas.set_mode(MODE_ROOF_DRAW)
        self._mode_lbl.setText(
            "Mode: Draw Roof Section  |  Click points  |  Double-click to finish  |  Esc to cancel")

    def _on_roof_section_drawn(self, scene_pts: list):
        """Called when user finishes drawing a polygon on the canvas."""
        self._canvas.set_mode(MODE_SELECT)
        self._mode_lbl.setText("Mode: Select")

        n = len(self._roof_sections) + 1
        dlg = _SectionDialog(f"Section {n}", 20.0, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name, angle = dlg.values()
        sec_id = self._next_sec_id
        self._next_sec_id += 1
        color = self._SEC_COLORS[(sec_id - 1) % len(self._SEC_COLORS)]

        self._roof_sections.append({
            "id":     sec_id,
            "name":   name,
            "angle":  angle,
            "color":  color,
            "points": scene_pts,   # scene coords
        })
        self._add_section_row(sec_id, name, angle, color)
        self._canvas.add_roof_section(sec_id, scene_pts, name, angle, QColor(color))

    def _reapply_sections(self):
        """Re-add section overlays to canvas (called after DXF reload)."""
        self._canvas.clear_roof_sections()
        for sec in self._roof_sections:
            self._canvas.add_roof_section(
                sec["id"], sec["points"], sec["name"], sec["angle"], QColor(sec["color"]))

    # ─────────────────────────────────────────────────────────────────────────
    # Panel → section assignment (point-in-polygon)
    # ─────────────────────────────────────────────────────────────────────────

    def _assign_panel_sections(self):
        """Set roof_section_id on each ParsedPanel based on which section contains it."""
        if not self._roof_sections:
            for p in self._panels:
                p.roof_section_id = -1
            return

        # We need section polygons in SCENE coordinates.
        # Canvas stores DXF→scene transform parameters in _dxf_bounds and _scale.
        # We re-use the same transform: scene_x = (cx - w/2 - minx)*s, scene_y = (maxy - (cy+h/2))*s
        # Panel scene centre = scene_x + w*s/2, scene_y + h*s/2

        canvas = self._canvas
        if not hasattr(canvas, '_dxf_bounds'):
            for p in self._panels:
                p.roof_section_id = -1
            return

        minx, miny, maxx, maxy = canvas._dxf_bounds
        s = canvas._scale

        for p in self._panels:
            # Compute scene centre of this panel
            scene_cx = (p.cx - minx) * s
            scene_cy = (maxy - p.cy) * s

            assigned = -1
            for sec in self._roof_sections:
                if _point_in_polygon(scene_cx, scene_cy, sec["points"]):
                    assigned = sec["id"]
                    break
            p.roof_section_id = assigned

    # ─────────────────────────────────────────────────────────────────────────
    # DXF import
    # ─────────────────────────────────────────────────────────────────────────

    def _import_dxf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Layout File", "",
            "Layout Files (*.dxf *.DXF *.dwg *.DWG);;"
            "DXF Files (*.dxf *.DXF);;"
            "DWG Files (*.dwg *.DWG)"
        )
        if not path:
            return

        # ── DWG → DXF conversion ──────────────────────────────────────────────
        dxf_path = path
        if path.lower().endswith(".dwg"):
            from calculators.pv_layout.dwg_converter import (
                convert as _dwg_convert, detect_converter, INSTALL_HELP,
            )
            from PyQt6.QtWidgets import QApplication

            available, method = detect_converter()
            if not available:
                # Show combined dialog: install instructions + inline key entry
                dlg = _NoConverterDialog(self)
                if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.get_key():
                    return   # user cancelled
                # User entered a key — save it and re-detect
                from calculators.pv_layout.dwg_converter import save_cloudconvert_key
                save_cloudconvert_key(dlg.get_key())
                available, method = detect_converter()
                if not available:
                    return  # shouldn't happen, but guard anyway

            _method_labels = {
                "oda":          "ODA File Converter",
                "libredwg":     "LibreDWG",
                "cloudconvert": "CloudConvert",
            }
            method_label = _method_labels.get(method, method)
            self._status_lbl.setText(f"Converting DWG via {method_label}...")
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            # Progress callback: updates status label and pumps the event loop
            def _on_progress(msg: str):
                self._status_lbl.setText(msg)
                QApplication.processEvents()

            try:
                ok, dxf_path, msg = _dwg_convert(path, progress_fn=_on_progress)
            finally:
                QApplication.restoreOverrideCursor()

            if not ok:
                self._update_status()
                QMessageBox.critical(self, "DWG Conversion Failed", msg)
                return

        # ── Parse DXF ─────────────────────────────────────────────────────────
        try:
            from calculators.pv_layout.dxf_parser import parse_dxf
            panels, meta = parse_dxf(dxf_path)
        except ImportError as e:
            QMessageBox.critical(self, "Missing Library", str(e))
            return
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))
            return

        if not panels:
            QMessageBox.warning(
                self, "No Panels Found",
                f"Could not detect panels in this file.\n\n"
                f"Reason: {meta.get('error', 'Unknown')}\n\n"
                "Tips:\n"
                "• Export from AutoCAD as DXF R2010 format\n"
                "• Panels should be block inserts or closed 4-vertex polylines\n"
                "• Ensure the file contains panel geometry (not just dimensions)"
            )
            return

        self._panels  = panels
        self._strings = []
        self._canvas.load_panels(panels)
        self._reapply_sections()
        self._update_status()
        self._btn_export.setEnabled(False)
        self._str_list.clear()

        source_label = "DWG (converted)" if path.lower().endswith(".dwg") else "DXF"
        QMessageBox.information(
            self, "Layout Loaded",
            f"Detected {len(panels)} panels from {source_label}.\n"
            f"Source: {meta.get('source', '?')} entities"
            + (f"\nBlock: '{meta.get('block_name', '')}'" if meta.get('block_name') else "")
        )

    # ─────────────────────────────────────────────────────────────────────────
    # CloudConvert API key dialog
    # ─────────────────────────────────────────────────────────────────────────

    def _set_cloudconvert_key(self):
        """Open a dialog to save/clear the CloudConvert API key."""
        from calculators.pv_layout.dwg_converter import (
            get_cloudconvert_key, save_cloudconvert_key,
        )

        current_key = get_cloudconvert_key() or ""

        dlg = _CloudKeyDialog(current_key, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        action, new_key = dlg.result_values()
        if action == "save":
            save_cloudconvert_key(new_key)
            masked = new_key[:6] + "..." + new_key[-4:] if len(new_key) > 10 else "***"
            QMessageBox.information(
                self, "API Key Saved",
                f"CloudConvert API key saved ({masked}).\n\n"
                "DWG files will now be converted online automatically."
            )
        elif action == "clear":
            save_cloudconvert_key(None)
            QMessageBox.information(
                self, "API Key Cleared",
                "CloudConvert API key has been removed."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Auto-stringing
    # ─────────────────────────────────────────────────────────────────────────

    def _auto_string(self):
        if not self._panels:
            QMessageBox.information(self, "No Panels", "Import a DXF file first.")
            return

        configs = self._read_inverter_configs()
        if not configs:
            QMessageBox.warning(self, "No Inverters", "Add at least one inverter in the setup table.")
            return

        self._assign_panel_sections()

        sec_dicts = [{"id": s["id"], "name": s["name"], "angle": s["angle"]}
                     for s in self._roof_sections]

        result: AssignmentResult = auto_string(
            self._panels,
            sec_dicts,
            configs,
            self._panels_per_str.value(),
        )

        if result.warnings:
            QMessageBox.warning(self, "Stringing Warnings",
                "\n\n".join(result.warnings))

        self._strings = result.strings
        self._canvas.apply_strings(self._strings, self._panels)
        self._update_string_list()
        self._update_status()
        self._btn_export.setEnabled(bool(self._strings))

    # ─────────────────────────────────────────────────────────────────────────
    # Manual stringing
    # ─────────────────────────────────────────────────────────────────────────

    def _toggle_manual_string(self):
        if not self._manual_active:
            # Enter manual mode
            if not self._panels:
                QMessageBox.information(self, "No Panels", "Import a DXF file first.")
                return
            self._manual_active = True
            self._canvas.set_mode(MODE_MANUAL)
            self._btn_manual.setText("✅  Confirm String")
            self._btn_manual.setObjectName("primary_btn")
            self._btn_manual.style().unpolish(self._btn_manual)
            self._btn_manual.style().polish(self._btn_manual)
            self._mode_lbl.setText(
                "Mode: Manual String  |  Click panels in order (+→−)  |  Confirm or Esc to cancel")
        else:
            # Confirm
            self._canvas.confirm_manual_string()   # emits sig_manual_string_done

    def _on_manual_string_done(self, panel_ids: list):
        """Canvas confirmed a manual string — ask for name, add it."""
        self._manual_active = False
        self._canvas.set_mode(MODE_SELECT)
        self._btn_manual.setText("✋  Manual String")
        self._btn_manual.setObjectName("secondary_btn")
        self._btn_manual.style().unpolish(self._btn_manual)
        self._btn_manual.style().polish(self._btn_manual)
        self._mode_lbl.setText("Mode: Select")

        if not panel_ids:
            return

        # Suggest next available string name
        default_name = self._next_string_name()
        name, ok = QInputDialog.getText(
            self, "Name this String",
            "String name (e.g. 1-A-1):",
            text=default_name,
        )
        if not ok or not name.strip():
            return

        name = name.strip()
        color_idx = len(self._strings) % len(PANEL_COLORS)

        # Determine roof section from first panel
        sec_id = -1
        if self._panels:
            pid_map = {p.id: p for p in self._panels}
            first   = pid_map.get(panel_ids[0])
            if first:
                sec_id = first.roof_section_id

        # Parse inverter/mppt/num from name like "1-A-1"
        parts = name.split("-")
        inv_id     = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 1
        mppt_ltr   = parts[1].upper() if len(parts) > 1 else "A"
        str_num    = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1

        sr = StringResult(
            name=name,
            inverter_id=inv_id,
            mppt_letter=mppt_ltr,
            string_num=str_num,
            panels=panel_ids,
            roof_section_id=sec_id,
            color_index=color_idx,
        )
        self._strings.append(sr)
        self._canvas.apply_strings(self._strings, self._panels)
        self._update_string_list()
        self._update_status()
        self._btn_export.setEnabled(True)

    def _next_string_name(self) -> str:
        """Suggest the next string name based on existing strings."""
        if not self._strings:
            return "1-A-1"
        last = self._strings[-1]
        inv   = last.inverter_id
        mppt  = last.mppt_letter
        num   = last.string_num + 1

        # Check if we need to move to next MPPT
        configs  = self._read_inverter_configs()
        cfg_map  = {c.id: c for c in configs}
        cfg      = cfg_map.get(inv)
        max_s    = cfg.strings_per_mppt if cfg else 99
        max_m    = cfg.num_mppts        if cfg else 26

        if num > max_s:
            num   = 1
            mppt_i = ord(mppt) - ord('A') + 1
            if mppt_i >= max_m:
                mppt_i = 0
                inv   += 1
            mppt = chr(ord('A') + mppt_i)

        return f"{inv}-{mppt}-{num}"

    # ─────────────────────────────────────────────────────────────────────────
    # Clear strings
    # ─────────────────────────────────────────────────────────────────────────

    def _clear_strings(self):
        if not self._strings:
            return
        reply = QMessageBox.question(
            self, "Clear All Strings",
            "Remove all string assignments?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._strings = []
        self._canvas.clear_strings()
        self._str_list.clear()
        self._update_status()
        self._btn_export.setEnabled(False)

    # ─────────────────────────────────────────────────────────────────────────
    # String list widget
    # ─────────────────────────────────────────────────────────────────────────

    def _update_string_list(self):
        self._str_list.clear()
        sec_map = {s["id"]: s for s in self._roof_sections}
        for sr in self._strings:
            sec  = sec_map.get(sr.roof_section_id, {})
            sec_label = f"  [{sec.get('name', '?')}  {sec.get('angle', '?')}°]" \
                if sec else ""
            item = QListWidgetItem(f"{sr.name}  ×{len(sr.panels)} panels{sec_label}")
            item.setData(Qt.ItemDataRole.UserRole, sr.name)
            color = QColor(PANEL_COLORS[sr.color_index % len(PANEL_COLORS)])
            item.setForeground(color)
            self._str_list.addItem(item)

    def _on_string_clicked(self, item: QListWidgetItem):
        name = item.data(Qt.ItemDataRole.UserRole)
        for sr in self._strings:
            if sr.name == name:
                self._canvas.highlight_string(sr.panels)
                break

    def _on_selection_changed(self, panel_ids: list):
        pass   # could highlight in string list — future enhancement

    # ─────────────────────────────────────────────────────────────────────────
    # Status bar
    # ─────────────────────────────────────────────────────────────────────────

    def _update_status(self):
        total    = len(self._panels)
        assigned = sum(len(sr.panels) for sr in self._strings)
        n_str    = len(self._strings)
        self._status_lbl.setText(
            f"Panels: {total}  |  Assigned: {assigned}  |  Strings: {n_str}")

    # ─────────────────────────────────────────────────────────────────────────
    # Excel export
    # ─────────────────────────────────────────────────────────────────────────

    def _export_excel(self):
        if not self._strings:
            QMessageBox.information(self, "No Strings", "Run Auto-String or draw strings first.")
            return

        fpath, _ = QFileDialog.getSaveFileName(
            self, "Save Excel Report",
            f"PV_Layout_Stringing_{datetime.date.today():%Y%m%d}.xlsx",
            "Excel Workbook (*.xlsx)",
        )
        if not fpath:
            return

        try:
            from calculators.pv_layout.excel_export import export_layout
            export_layout(
                strings=self._strings,
                panels=self._panels,
                roof_sections=[{"id": s["id"], "name": s["name"], "angle": s["angle"]}
                               for s in self._roof_sections],
                filepath=fpath,
                metadata={
                    "project":     "",
                    "client":      "",
                    "location":    "",
                    "prepared_by": "",
                    "date":        datetime.date.today().strftime("%d %B %Y"),
                },
            )
            QMessageBox.information(self, "Exported", f"Saved to:\n{fpath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # BaseCalculator interface
    # ─────────────────────────────────────────────────────────────────────────

    def get_inputs(self) -> dict:
        configs = self._read_inverter_configs()
        return {
            "Panels per string": self._panels_per_str.value(),
            "Inverter count":    len(configs),
            "Total MPPTs":       sum(c.num_mppts for c in configs),
            "Roof sections":     len(self._roof_sections),
            "Panels loaded":     len(self._panels),
        }

    def get_results(self) -> dict:
        assigned = sum(len(sr.panels) for sr in self._strings)
        return {
            "Total strings":     len(self._strings),
            "Assigned panels":   assigned,
            "Unassigned panels": len(self._panels) - assigned,
        }

    def reset(self):
        self._panels        = []
        self._strings       = []
        self._roof_sections = []
        self._next_sec_id   = 1
        self._manual_active = False

        self._canvas._scene.clear()
        self._canvas._panels.clear()
        self._canvas._path_items.clear()
        self._canvas._section_items.clear()

        self._str_list.clear()
        self._sec_table.setRowCount(0)
        self._inv_table.setRowCount(0)
        self._add_inverter_row(1, 2, 2)
        self._panels_per_str.setValue(10)
        self._update_status()
        self._btn_export.setEnabled(False)

        self._btn_manual.setText("✋  Manual String")
        self._btn_manual.setObjectName("secondary_btn")
        self._canvas.set_mode(MODE_SELECT)
        self._mode_lbl.setText("Mode: Select")


# ─────────────────────────────────────────────────────────────────────────────
# Utility — vertical separator
# ─────────────────────────────────────────────────────────────────────────────

def _sep_v() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.VLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


# ─────────────────────────────────────────────────────────────────────────────
# Utility — ray-casting point-in-polygon
# ─────────────────────────────────────────────────────────────────────────────

def _point_in_polygon(px: float, py: float, polygon: list) -> bool:
    """
    Returns True if point (px, py) is inside the polygon.
    polygon: list of (x, y) tuples.
    Uses the ray-casting algorithm.
    """
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside
