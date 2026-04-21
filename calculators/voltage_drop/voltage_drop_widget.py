"""
voltage_drop_widget.py
----------------------
SANS 10142-1 §6.2.7 Voltage Drop Calculator.

Calculation Methods:
  Method 1 — SANS 10142-1 Table 6 (pure SANS lookup, no external data)
  Method 2 — Manual conductor resistance entry (Ω/km)
  Method 3 — Cable Data Sources:
                Sub-option A: Excel/CSV datasheet file upload
                Sub-option B: SWA Armoured pre-loaded manufacturer table
"""

import math
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDoubleSpinBox, QGroupBox,
    QPushButton, QFrame, QRadioButton, QButtonGroup, QCheckBox,
    QSizePolicy, QSpacerItem, QFileDialog, QMessageBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QTabWidget,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QBrush
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.voltage_drop.voltage_drop_logic import (
    calc_method2, vd_percent, pass_fail, VDROP_THRESHOLD_PCT
)
from calculators.voltage_drop.sans_tables import (
    get_impedance, get_swa_vd, get_available_sizes, get_mv_per_am,
    STANDARD_SANS, STANDARD_SWA,
    SWA_COPPER_SIZES, SWA_ALUMINIUM_SIZES
)
from calculators.unbalanced_load.unbalanced_load_logic import (
    compute_unbalanced, VD_LIMIT_PCT
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _note(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("header_subtitle")
    lbl.setWordWrap(True)
    return lbl


def _input_row(label: str, widget: QWidget, unit: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(210)
    row.addWidget(lbl)
    row.addWidget(widget, 1)
    if unit:
        u = QLabel(unit)
        u.setObjectName("result_label")
        u.setFixedWidth(60)
        row.addWidget(u)
    else:
        row.addSpacing(60)
    return row


def _action_btn(text: str, icon_name: str, obj_name: str, icon_color: str,
                height: int = 42) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName(obj_name)
    btn.setIcon(qta.icon(icon_name, color=icon_color))
    btn.setIconSize(QSize(14, 14))
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class ResultCard(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl = QLabel("—")
        self.value_lbl.setObjectName("result_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value_lbl)
        sub = QLabel(label.upper())
        sub.setObjectName("result_label")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(90)

    def set_value(self, text: str):
        self.value_lbl.setText(text)


# ─────────────────────────────────────────────────────────────────────────────
# Table column indices
# ─────────────────────────────────────────────────────────────────────────────
COL_NUM, COL_LABEL, COL_SYSTEM, COL_METHOD = 0, 1, 2, 3
COL_CABLE, COL_LENGTH, COL_CURR, COL_VDV, COL_VDPCT, COL_RESULT = 4, 5, 6, 7, 8, 9

TABLE_HEADERS = ["#", "Cable Label", "System", "Method",
                 "Cable / R", "Length (m)", "Current (A)",
                 "Vd (V)", "Vd (%)", "Result"]


# ─────────────────────────────────────────────────────────────────────────────
# Main widget
# ─────────────────────────────────────────────────────────────────────────────

class VoltageDropWidget(BaseCalculator):
    calculator_name = "Voltage Drop Calculator"
    sans_reference  = "SANS 10142-1:2020 §6.2.7"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vd_volts: float | None = None
        self._vd_pct:   float | None = None
        self._passed:   bool  | None = None
        self._unbalanced_result = None
        self._datasheet_cables: list[dict] = []
        self._table_row_counter: int = 0
        self._last_cable_desc  = "—"
        self._last_method_desc = "—"
        self._build_ui()
        self._generate_template_if_missing()

    # ─────────────────────────────────────────────── UI build ────────────────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 32)
        main.setSpacing(20)

        # Title row
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.bolt", color="#58a6ff").pixmap(28, 28))
        tr.addWidget(ico); tr.addSpacing(10)
        tc = QVBoxLayout(); tc.setSpacing(2)
        h1 = QLabel("Voltage Drop Calculator")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title")
        tc.addWidget(h1)
        tc.addWidget(_note("SANS 10142-1:2020 — Section 6.2.7"))
        tr.addLayout(tc); tr.addStretch()
        main.addLayout(tr)
        main.addWidget(_sep())

        # Two-column body
        cols = QHBoxLayout(); cols.setSpacing(20)
        left = QVBoxLayout(); left.setSpacing(16)
        right = QVBoxLayout(); right.setSpacing(16)

        # ── System Parameters ──────────────────────────────────────────────
        sg = QGroupBox("System Parameters")
        sl = QVBoxLayout(sg); sl.setSpacing(12)

        # Load type toggle
        lt_row = QHBoxLayout()
        self._load_type_grp = QButtonGroup(self)
        self.radio_balanced   = QRadioButton("Balanced Load")
        self.radio_unbalanced = QRadioButton("Unbalanced 3-Phase Load (3P+N)")
        self.radio_balanced.setChecked(True)
        self._load_type_grp.addButton(self.radio_balanced,   1)
        self._load_type_grp.addButton(self.radio_unbalanced, 2)
        lt_row.addWidget(self.radio_balanced)
        lt_row.addSpacing(20)
        lt_row.addWidget(self.radio_unbalanced)
        lt_row.addStretch()
        sl.addLayout(lt_row)
        sl.addWidget(_sep())

        self.system_combo = QComboBox()
        self.system_combo.addItems(["DC", "Single-Phase AC", "Three-Phase AC"])
        sl.addLayout(_input_row("System Type", self.system_combo))

        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(0.1, 100000); self.voltage_spin.setValue(400)
        self.voltage_spin.setDecimals(1); self.voltage_spin.setSingleStep(10)
        sl.addLayout(_input_row("Supply Voltage (V)", self.voltage_spin, "V"))

        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.1, 100000); self.length_spin.setValue(50)
        self.length_spin.setDecimals(1); self.length_spin.setSingleStep(5)
        sl.addLayout(_input_row("Route Length (L)", self.length_spin, "m"))

        # Balanced current (hidden when unbalanced)
        self._balanced_panel = QWidget()
        bp = QVBoxLayout(self._balanced_panel); bp.setContentsMargins(0,0,0,0); bp.setSpacing(8)
        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(0.001, 10000); self.current_spin.setValue(40)
        self.current_spin.setDecimals(2); self.current_spin.setSingleStep(1)
        bp.addLayout(_input_row("Design Current (I)", self.current_spin, "A"))
        sl.addWidget(self._balanced_panel)

        # Unbalanced phase inputs (A / B / C  separate current + PF)
        self._unbal_panel = QWidget()
        up = QVBoxLayout(self._unbal_panel); up.setContentsMargins(0,0,0,0); up.setSpacing(8)
        up.addWidget(_note(
            "SANS 10142-1 §6.2.7: Total Vd (each phase) = Phase conductor drop + Neutral conductor drop. "
            "Neutral current = phasor sum (IA + IB + IC)."
        ))
        self._phase_spins = {}  # {ph: (I_spin, PF_spin)}
        PHASE_LABELS = {"A": "Phase A  (ref 0°)", "B": "Phase B  (ref −120°)", "C": "Phase C  (ref +120°)"}
        for ph, lbl in PHASE_LABELS.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(lbl))
            i_sp = QDoubleSpinBox()
            i_sp.setRange(0, 10000); i_sp.setDecimals(2); i_sp.setSingleStep(5)
            i_sp.setValue({"A":100,"B":80,"C":60}[ph])
            pf_sp = QDoubleSpinBox()
            pf_sp.setRange(0.01, 1.0); pf_sp.setDecimals(3); pf_sp.setSingleStep(0.01); pf_sp.setValue(0.95)
            row.addWidget(QLabel("I (A):")); row.addWidget(i_sp)
            row.addSpacing(12)
            row.addWidget(QLabel("PF:")); row.addWidget(pf_sp)
            row.addStretch()
            up.addLayout(row)
            self._phase_spins[ph] = (i_sp, pf_sp)
        # Neutral conductor R override
        nrow = QHBoxLayout()
        self._same_neutral_chk = QCheckBox("Neutral same size as phase")
        self._same_neutral_chk.setChecked(True)
        self._same_neutral_chk.toggled.connect(self._toggle_neutral_r)
        self._neutral_r_spin = QDoubleSpinBox()
        self._neutral_r_spin.setRange(0.0001,1000); self._neutral_r_spin.setDecimals(4)
        self._neutral_r_spin.setValue(1.15); self._neutral_r_spin.setVisible(False)
        nrow.addWidget(self._same_neutral_chk); nrow.addSpacing(12)
        nrow.addWidget(QLabel("Neutral R (Ω/km):")); nrow.addWidget(self._neutral_r_spin)
        nrow.addStretch()
        up.addLayout(nrow)
        self._unbal_panel.setVisible(False)
        sl.addWidget(self._unbal_panel)
        left.addWidget(sg)

        # ── Calculation Method ─────────────────────────────────────────────
        mg = QGroupBox("Calculation Method")
        ml = QVBoxLayout(mg)
        ml.setSpacing(6)
        ml.setContentsMargins(8, 8, 8, 8)

        self._method_tabs = QTabWidget()

        # ── Tab 0: SANS Tables ─────────────────────────────────────────────
        self.m1_panel = QWidget()
        m1l = QVBoxLayout(self.m1_panel)
        m1l.setContentsMargins(8, 10, 8, 8)
        m1l.setSpacing(10)
        m1l.addWidget(_note(
            "Uses SANS 10142-1:2020 Table 6 — resistive mV/A/m values "
            "at 70 °C conductor temperature."
        ))
        self.m1_material = QComboBox()
        self.m1_material.addItems(["Copper", "Aluminium"])
        self.m1_material.currentTextChanged.connect(self._m1_update_sizes)
        m1l.addLayout(_input_row("Conductor Material", self.m1_material))
        self.m1_size = QComboBox()
        m1l.addLayout(_input_row("Cable Size", self.m1_size, "mm²"))
        self.m1_display = QLabel("SANS mV/A/m: —")
        self.m1_display.setObjectName("header_subtitle")
        m1l.addWidget(self.m1_display)
        m1l.addStretch()
        self._method_tabs.addTab(self.m1_panel, "  SANS Tables  ")

        # ── Tab 1: Manual R ────────────────────────────────────────────────
        self.m2_panel = QWidget()
        m2l = QVBoxLayout(self.m2_panel)
        m2l.setContentsMargins(8, 10, 8, 8)
        m2l.setSpacing(10)
        m2l.addWidget(_note(
            "Enter the conductor resistance in Ω/km from the cable "
            "manufacturer's datasheet."))
        self.resistance_spin = QDoubleSpinBox()
        self.resistance_spin.setRange(0.0001, 1000)
        self.resistance_spin.setValue(1.15)
        self.resistance_spin.setDecimals(4)
        self.resistance_spin.setSingleStep(0.01)
        m2l.addLayout(_input_row("Conductor Resistance (R)", self.resistance_spin, "Ω/km"))
        self.formula_m2_lbl = QLabel()
        self.formula_m2_lbl.setObjectName("header_subtitle")
        self.formula_m2_lbl.setWordWrap(True)
        m2l.addWidget(self.formula_m2_lbl)
        m2l.addStretch()
        self._method_tabs.addTab(self.m2_panel, "  Manual R (Ω/km)  ")

        # ── Tab 2: Cable Data Sources ──────────────────────────────────────
        self.m3_panel = QWidget()
        m3l = QVBoxLayout(self.m3_panel)
        m3l.setContentsMargins(8, 10, 8, 8)
        m3l.setSpacing(12)

        # Sub-option radio buttons (File upload vs SWA pre-loaded)
        sub_row = QHBoxLayout()
        self._m3_group = QButtonGroup(self)
        self.radio_m3a = QRadioButton("File Upload (Excel / CSV)")
        self.radio_m3b = QRadioButton("SWA Armoured — Pre-loaded Manufacturer Table")
        self.radio_m3a.setChecked(True)
        self._m3_group.addButton(self.radio_m3a, 1)
        self._m3_group.addButton(self.radio_m3b, 2)
        sub_row.addWidget(self.radio_m3a)
        sub_row.addSpacing(20)
        sub_row.addWidget(self.radio_m3b)
        sub_row.addStretch()
        m3l.addLayout(sub_row)
        m3l.addWidget(_sep())

        # M3-A: File upload panel
        self.m3a_panel = QWidget()
        m3al = QVBoxLayout(self.m3a_panel)
        m3al.setContentsMargins(0, 0, 0, 0)
        m3al.setSpacing(10)
        m3al.addWidget(_note(
            "Load an Excel (.xlsx) or CSV cable datasheet. "
            "Select a cable — resistance auto-fills. "
            "Click 'Get Template' to download the blank template."
        ))
        frow = QHBoxLayout()
        self.ds_path_edit = QLineEdit()
        self.ds_path_edit.setPlaceholderText("No file loaded…")
        self.ds_path_edit.setReadOnly(True)
        frow.addWidget(self.ds_path_edit, 1)
        self.browse_btn = _action_btn("  Browse…", "fa5s.folder-open", "secondary_btn", "#8b949e", 36)
        self.browse_btn.clicked.connect(self._browse_datasheet)
        frow.addWidget(self.browse_btn)
        self.template_btn = _action_btn("  Get Template", "fa5s.file-excel", "secondary_btn", "#8b949e", 36)
        self.template_btn.clicked.connect(self._open_template)
        frow.addWidget(self.template_btn)
        m3al.addLayout(frow)
        self.ds_cable_combo = QComboBox()
        self.ds_cable_combo.setEnabled(False)
        self.ds_cable_combo.setPlaceholderText("Load a datasheet first…")
        self.ds_cable_combo.currentIndexChanged.connect(self._on_ds_cable_selected)
        m3al.addLayout(_input_row("Select Cable", self.ds_cable_combo))
        self.ds_r_display = QLabel("R (Ω/km): —")
        self.ds_r_display.setObjectName("header_subtitle")
        self.ds_mv_display = QLabel("mV/A/m: —")
        self.ds_mv_display.setObjectName("header_subtitle")
        self.ds_notes_display = QLabel("Notes: —")
        self.ds_notes_display.setObjectName("header_subtitle")
        for w in (self.ds_r_display, self.ds_mv_display, self.ds_notes_display):
            m3al.addWidget(w)
        m3l.addWidget(self.m3a_panel)

        # M3-B: SWA pre-loaded panel
        self.m3b_panel = QWidget()
        m3bl = QVBoxLayout(self.m3b_panel)
        m3bl.setContentsMargins(0, 0, 0, 0)
        m3bl.setSpacing(10)
        m3bl.addWidget(_note(
            "Pre-loaded SWA (Steel Wire Armoured) manufacturer impedance data. "
            "Copper: 1.5 – 300 mm²  |  Aluminium: 25 – 240 mm²"
        ))
        self.swa_material = QComboBox()
        self.swa_material.addItems(["Copper", "Aluminium"])
        self.swa_material.currentTextChanged.connect(self._swa_update_sizes)
        m3bl.addLayout(_input_row("Conductor Material", self.swa_material))
        self.swa_size = QComboBox()
        m3bl.addLayout(_input_row("Cable Size", self.swa_size, "mm²"))
        self.swa_size.currentIndexChanged.connect(self._swa_update_display)
        self.swa_display = QLabel("Impedance: —")
        self.swa_display.setObjectName("header_subtitle")
        m3bl.addWidget(self.swa_display)
        m3l.addWidget(self.m3b_panel)
        self.m3b_panel.setVisible(False)

        m3l.addStretch()
        self._method_tabs.addTab(self.m3_panel, "  Cable Data Sources  ")

        ml.addWidget(self._method_tabs)
        left.addWidget(mg)

        # ── Cable label + action buttons ───────────────────────────────────
        lrow = QHBoxLayout()
        ll = QLabel("Cable Label / Description:")
        ll.setFixedWidth(210); lrow.addWidget(ll)
        self.cable_label_edit = QLineEdit()
        self.cable_label_edit.setPlaceholderText("e.g.  Cable 1 — DB to Panel A")
        lrow.addWidget(self.cable_label_edit, 1)
        left.addLayout(lrow)

        brow = QHBoxLayout(); brow.setSpacing(10)
        self.calc_btn = _action_btn("  Calculate",    "fa5s.calculator",  "primary_btn",   "white")
        self.add_table_btn = _action_btn("  Add to Table","fa5s.plus",    "secondary_btn", "#8b949e")
        self.export_pdf_btn = _action_btn("  PDF",    "fa5s.file-pdf",    "secondary_btn", "#8b949e")
        self.export_xl_btn  = _action_btn("  Excel",  "fa5s.file-excel",  "secondary_btn", "#8b949e")
        self.reset_btn      = _action_btn("  Reset",  "fa5s.redo",        "danger_btn",    "#f85149")
        self.calc_btn.clicked.connect(self._calculate)
        self.add_table_btn.clicked.connect(self._add_to_table)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        self.export_xl_btn.clicked.connect(self._export_excel)
        self.reset_btn.clicked.connect(self.reset)
        for b in (self.calc_btn, self.add_table_btn, self.export_pdf_btn,
                  self.export_xl_btn, self.reset_btn):
            brow.addWidget(b)
        left.addLayout(brow)
        left.addStretch()

        # ── Results panel ──────────────────────────────────────────────────
        rg = QGroupBox("Calculation Results")
        rl = QVBoxLayout(rg); rl.setSpacing(12)
        rl.addWidget(_note("SANS 10142-1:2020 §6.2.7 — Max allowable Vd = 5 % of Vn"))
        rl.addWidget(_sep())
        cards = QHBoxLayout(); cards.setSpacing(12)
        self.card_vd_v   = ResultCard("Voltage Drop (V)")
        self.card_vd_pct = ResultCard("Voltage Drop (%)")
        cards.addWidget(self.card_vd_v); cards.addWidget(self.card_vd_pct)
        rl.addLayout(cards)
        pf = QHBoxLayout()
        pf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl = QLabel("AWAITING CALCULATION")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl.setMinimumWidth(220)
        pf.addStretch(); pf.addWidget(self.pass_fail_lbl); pf.addStretch()
        rl.addLayout(pf)
        rl.addWidget(_sep())
        self.summary_lbl = QLabel(
            "Enter system parameters and press Calculate to evaluate\n"
            "voltage drop compliance per SANS 10142-1 §6.2.7."
        )
        self.summary_lbl.setObjectName("header_subtitle")
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        rl.addWidget(self.summary_lbl)
        rl.addWidget(_sep())
        fgrp = QGroupBox("Applied Formula Reference")
        fl = QVBoxLayout(fgrp)
        self.formula_ref_lbl = QLabel()
        self.formula_ref_lbl.setObjectName("header_subtitle")
        self.formula_ref_lbl.setWordWrap(True)
        fl.addWidget(self.formula_ref_lbl)
        rl.addWidget(fgrp); rl.addStretch()
        right.addWidget(rg); right.addStretch()

        cols.addLayout(left, 55); cols.addLayout(right, 45)
        main.addLayout(cols)

        # ── Comparison table ───────────────────────────────────────────────
        main.addWidget(_sep())
        self._build_comparison_table(main)

        # ── Wire up signals ────────────────────────────────────────────────
        self._method_tabs.currentChanged.connect(self._toggle_method_panels)
        self.radio_m3a.toggled.connect(self._toggle_m3_sub)
        self.radio_m3b.toggled.connect(self._toggle_m3_sub)
        self.radio_balanced.toggled.connect(self._toggle_load_type)
        self.radio_unbalanced.toggled.connect(self._toggle_load_type)
        self.system_combo.currentTextChanged.connect(self._update_formula_display)
        self.m1_size.currentTextChanged.connect(self._m1_update_display)
        self.m1_material.currentTextChanged.connect(self._m1_update_sizes)

        self._m1_update_sizes("Copper")
        self._swa_update_sizes("Copper")
        self._update_formula_display()

    def _build_comparison_table(self, parent_layout: QVBoxLayout):
        tg = QGroupBox("Multi-Cable Comparison Table")
        tl = QVBoxLayout(tg); tl.setSpacing(10)

        tbr = QHBoxLayout(); tbr.setSpacing(8)
        rm_btn = _action_btn("  Remove Selected", "fa5s.trash-alt",    "danger_btn",    "#f85149", 36)
        cl_btn = _action_btn("  Clear All",       "fa5s.times-circle", "secondary_btn", "#8b949e", 36)
        tp_btn = _action_btn("  Export Table → PDF",   "fa5s.file-pdf",   "secondary_btn", "#8b949e", 36)
        tx_btn = _action_btn("  Export Table → Excel", "fa5s.file-excel", "secondary_btn", "#8b949e", 36)
        rm_btn.clicked.connect(self._remove_selected_row)
        cl_btn.clicked.connect(self._clear_table)
        tp_btn.clicked.connect(self._export_table_pdf)
        tx_btn.clicked.connect(self._export_table_excel)
        tbr.addWidget(rm_btn); tbr.addWidget(cl_btn)
        tbr.addStretch(); tbr.addWidget(tp_btn); tbr.addWidget(tx_btn)
        tl.addLayout(tbr)

        self.result_table = QTableWidget(0, len(TABLE_HEADERS))
        self.result_table.setHorizontalHeaderLabels(TABLE_HEADERS)
        self.result_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setMinimumHeight(200)
        hdr = self.result_table.horizontalHeader()
        hdr.setSectionResizeMode(COL_NUM,    QHeaderView.ResizeMode.Fixed);          self.result_table.setColumnWidth(COL_NUM, 36)
        hdr.setSectionResizeMode(COL_LABEL,  QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_SYSTEM, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_METHOD, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_CABLE,  QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_LENGTH, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_CURR,   QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_VDV,    QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_VDPCT,  QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_RESULT, QHeaderView.ResizeMode.Fixed);          self.result_table.setColumnWidth(COL_RESULT, 110)
        self.result_table.setStyleSheet("""
            QTableWidget {
                background-color: #0d1117; alternate-background-color: #161b22;
                color: #c9d1d9; gridline-color: #30363d;
                border: 1px solid #30363d; border-radius: 6px; font-size: 12px;
            }
            QTableWidget::item { padding: 6px 8px; }
            QTableWidget::item:selected { background-color: #1f3a5f; color: #e6edf3; }
            QHeaderView::section {
                background-color: #1f3a5f; color: #e6edf3;
                font-weight: 600; font-size: 11px; padding: 6px 8px;
                border: none; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d;
            }
        """)
        self._table_empty_lbl = QLabel("No cables added yet. Calculate a cable then click  'Add to Table'.")
        self._table_empty_lbl.setObjectName("header_subtitle")
        self._table_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl.addWidget(self._table_empty_lbl)
        tl.addWidget(self.result_table)
        self.result_table.setVisible(False)
        parent_layout.addWidget(tg)

    # ─────────────────────────────────────────────── Signal handlers ─────────

    def _method_idx(self) -> int:
        """0 = SANS Tables, 1 = Manual R, 2 = Cable Data Sources."""
        return self._method_tabs.currentIndex()

    def _toggle_load_type(self):
        unbal = self.radio_unbalanced.isChecked()
        self._balanced_panel.setVisible(not unbal)
        self._unbal_panel.setVisible(unbal)
        if unbal:
            self.system_combo.setCurrentText("Three-Phase AC")
            self.system_combo.setEnabled(False)
        else:
            self.system_combo.setEnabled(True)

    def _toggle_neutral_r(self, same: bool):
        self._neutral_r_spin.setVisible(not same)

    def _toggle_method_panels(self):
        # Tabs handle panel visibility automatically — just refresh the formula.
        self._update_formula_display()

    def _toggle_m3_sub(self):
        a = self.radio_m3a.isChecked()
        self.m3a_panel.setVisible(a)
        self.m3b_panel.setVisible(not a)

    # Method 1
    def _m1_update_sizes(self, material: str = ""):
        mat = self.m1_material.currentText()
        sizes = get_available_sizes(STANDARD_SANS, mat)
        self.m1_size.blockSignals(True)
        self.m1_size.clear()
        for s in sizes:
            self.m1_size.addItem(f"{s} mm²", userData=s)
        default = next((i for i, s in enumerate(sizes) if s == 16.0), 0)
        self.m1_size.setCurrentIndex(default)
        self.m1_size.blockSignals(False)
        self._m1_update_display()

    def _m1_update_display(self):
        mat  = self.m1_material.currentText().lower()
        size = self.m1_size.currentData()
        if size is None:
            return
        mv = get_mv_per_am(mat, size)
        self.m1_display.setText(
            f"SANS Table value:  {mv} mV/A/m  (≡ {mv} Ω/km, single conductor at 70 °C)"
            if mv else "Not found in SANS 10142-1 table."
        )

    # Method 3-B (SWA)
    def _swa_update_sizes(self, material: str = ""):
        mat   = self.swa_material.currentText()
        sizes = SWA_COPPER_SIZES if mat.lower() == "copper" else SWA_ALUMINIUM_SIZES
        self.swa_size.blockSignals(True)
        self.swa_size.clear()
        for s in sizes:
            self.swa_size.addItem(f"{s} mm²", userData=s)
        default = next((i for i, s in enumerate(sizes) if s == 16.0), 0)
        self.swa_size.setCurrentIndex(default)
        self.swa_size.blockSignals(False)
        self._swa_update_display()

    def _swa_update_display(self):
        mat  = self.swa_material.currentText().lower()
        size = self.swa_size.currentData()
        if size is None:
            return
        r    = get_impedance(STANDARD_SWA, mat, size)
        vd3  = get_swa_vd(mat, size)
        if r:
            self.swa_display.setText(
                f"Impedance: {r} Ω/km   │   "
                f"Mfr. Volt Drop (3Ph): {vd3} mV/A/m   │   "
                f"Source: SWA Manufacturer Datasheet"
            )
        else:
            self.swa_display.setText("Not found in SWA table.")

    # Formula reference
    def _update_formula_display(self):
        three = "Three" in self.system_combo.currentText()
        mult  = "√3 ×" if three else "2 ×"
        is_m1 = (self._method_idx() == 0)
        formula = f"Vd = ({mult} mV × I × L) / 1000" if is_m1 else f"Vd = ({mult} I × L × R) / 1000"
        note    = "mV = SANS Table 6 mV/A/m (≡ Ω/km)" if is_m1 else "R = Ω/km, L in metres"
        self.formula_m2_lbl.setText(f"Formula: {formula}\n{note}")
        self.formula_ref_lbl.setText(
            f"Active formula:  {formula}\n{note}\n\n"
            f"Pass criterion:  Vd% ≤ {VDROP_THRESHOLD_PCT}% of nominal supply voltage (Vn)"
        )

    # ─────────────────────────────────────────────── Method 3A: File ─────────

    def _browse_datasheet(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Cable Datasheet", str(os.path.expanduser("~")),
            "Cable Datasheets (*.xlsx *.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            from calculators.voltage_drop.datasheet_loader import load_datasheet
            cables = load_datasheet(path)
            self._datasheet_cables = cables
            self.ds_path_edit.setText(path)
            self.ds_cable_combo.blockSignals(True)
            self.ds_cable_combo.clear()
            for c in cables:
                label = c["cable_name"]
                if c.get("size_mm2"):
                    label += f"  ({c['size_mm2']} mm²)"
                self.ds_cable_combo.addItem(label)
            self.ds_cable_combo.setEnabled(True)
            self.ds_cable_combo.blockSignals(False)
            self.ds_cable_combo.setCurrentIndex(0)
            self._on_ds_cable_selected(0)
            QMessageBox.information(self, "Datasheet Loaded",
                f"Loaded {len(cables)} cable(s) from:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Datasheet Error",
                f"Could not load datasheet:\n\n{e}\n\n"
                "Make sure the file uses the correct template format.")

    def _on_ds_cable_selected(self, idx: int):
        if idx < 0 or idx >= len(self._datasheet_cables):
            return
        c = self._datasheet_cables[idx]
        r  = c.get("resistance_ohm_per_km")
        mv = c.get("mv_per_am")
        self.ds_r_display.setText(f"R (Ω/km):  {r:.4f}" if r else "R (Ω/km): —")
        self.ds_mv_display.setText(f"mV/A/m:    {mv}" if mv else "mV/A/m:   not provided")
        self.ds_notes_display.setText(f"Notes:     {c.get('notes','')}" if c.get("notes") else "Notes: —")

    def _open_template(self):
        path = self._template_path()
        if not os.path.exists(path):
            self._generate_template_if_missing()
        os.startfile(path)

    def _template_path(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "cable_datasheet_template.xlsx"
        )

    def _generate_template_if_missing(self):
        path = self._template_path()
        if not os.path.exists(path):
            try:
                from calculators.voltage_drop.datasheet_loader import generate_template
                generate_template(path)
            except Exception:
                pass

    # ─────────────────────────────────────────────── Calculation ─────────────

    def _get_system_type(self) -> str:
        t = self.system_combo.currentText()
        if "Three" in t: return "3phase"
        if "Single" in t: return "1phase"
        return "dc"

    def _get_r_from_method(self):
        """Return (r_phase_ohm_per_km, desc, cable_desc) from active method, or None on error."""
        if self._method_idx() == 0:
            mat  = self.m1_material.currentText().lower()
            size = self.m1_size.currentData()
            r    = get_mv_per_am(mat, size)
            if r is None:
                QMessageBox.warning(self, "Lookup Error",
                    f"{self.m1_size.currentText()} {self.m1_material.currentText()} not in SANS table.")
                return None, None, None
            return (r,
                    f"Method 1 — SANS ({self.m1_material.currentText()}, {self.m1_size.currentText()}, r={r})",
                    f"{self.m1_material.currentText()} {self.m1_size.currentText()} [SANS]")
        elif self._method_idx() == 1:
            r = self.resistance_spin.value()
            return r, f"Method 2 — Manual (R={r} Ω/km)", f"R={r} Ω/km"
        else:
            if self.radio_m3a.isChecked():
                idx = self.ds_cable_combo.currentIndex()
                if not self._datasheet_cables or idx < 0:
                    QMessageBox.warning(self, "No Datasheet", "Please load a cable datasheet first."); return None,None,None
                cable = self._datasheet_cables[idx]
                r = cable.get("resistance_ohm_per_km")
                if r is None:
                    QMessageBox.warning(self, "Missing Data", "Selected cable has no resistance."); return None,None,None
                return r, f"Method 3A — File ({cable['cable_name']}, R={r})", cable["cable_name"]
            else:
                mat  = self.swa_material.currentText().lower()
                size = self.swa_size.currentData()
                r    = get_impedance(STANDARD_SWA, mat, size)
                if r is None:
                    QMessageBox.warning(self, "Lookup Error",
                        f"{self.swa_size.currentText()} {self.swa_material.currentText()} not in SWA table."); return None,None,None
                desc = f"{self.swa_material.currentText()} {self.swa_size.currentText()} [SWA]"
                return r, f"Method 3B — SWA ({desc}, R={r})", desc

    def _calculate(self):
        voltage = self.voltage_spin.value()
        length  = self.length_spin.value()

        if self.radio_unbalanced.isChecked():
            self._calculate_unbalanced(voltage, length)
        else:
            self._calculate_balanced(voltage, length)

        if not self.cable_label_edit.text().strip():
            self.cable_label_edit.setText(f"Cable {self.result_table.rowCount() + 1}")

    def _calculate_balanced(self, voltage, length):
        sys_type = self._get_system_type()
        current  = self.current_spin.value()
        r, method_desc, cable_desc = self._get_r_from_method()
        if r is None: return
        self._last_method_desc = method_desc
        self._last_cable_desc  = cable_desc
        vd_v   = calc_method2(r, current, length, sys_type)
        vd_pct = vd_percent(vd_v, voltage)
        passed = pass_fail(vd_pct)
        self._vd_volts = vd_v; self._vd_pct = vd_pct; self._passed = passed
        self._unbalanced_result = None

        self.card_vd_v.set_value(f"{vd_v:.3f} V")
        self.card_vd_pct.set_value(f"{vd_pct:.2f}%")
        if passed:
            self.pass_fail_lbl.setObjectName("pass_badge")
            self.pass_fail_lbl.setText("✔  PASS — Compliant with SANS 10142-1")
        else:
            self.pass_fail_lbl.setObjectName("fail_badge")
            self.pass_fail_lbl.setText("✘  FAIL — Exceeds SANS 10142-1 limit")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)
        self.summary_lbl.setText(
            f"System:          {self.system_combo.currentText()}\n"
            f"Supply Voltage:  {voltage:.1f} V\n"
            f"Route Length:    {length:.1f} m\n"
            f"Design Current:  {current:.2f} A\n"
            f"Method:          {self._last_method_desc}\n\n"
            f"Voltage Drop:    {vd_v:.3f} V  ({vd_pct:.2f}%)\n"
            f"Threshold:       {VDROP_THRESHOLD_PCT}%  ({VDROP_THRESHOLD_PCT/100*voltage:.2f} V)\n"
            f"Result:          {'PASS ✔' if passed else 'FAIL ✘'}"
        )

    def _calculate_unbalanced(self, voltage, length):
        r_ph, method_desc, cable_desc = self._get_r_from_method()
        if r_ph is None: return

        # Neutral R — same as phase or manual override
        r_neu = r_ph if self._same_neutral_chk.isChecked() else self._neutral_r_spin.value()

        ia, pfa = self._phase_spins["A"][0].value(), self._phase_spins["A"][1].value()
        ib, pfb = self._phase_spins["B"][0].value(), self._phase_spins["B"][1].value()
        ic, pfc = self._phase_spins["C"][0].value(), self._phase_spins["C"][1].value()

        if ia + ib + ic == 0:
            QMessageBox.warning(self, "Zero Current", "All phase currents are zero."); return

        res = compute_unbalanced(
            voltage_ll=voltage, length_m=length,
            ia=ia, ib=ib, ic=ic,
            pfa=pfa, pfb=pfb, pfc=pfc,
            r_phase_ohm_per_km=r_ph,
            r_neutral_ohm_per_km=r_neu,
        )
        self._unbalanced_result = res
        self._last_cable_desc   = cable_desc
        self._last_method_desc  = method_desc

        # Use worst-phase values for the summary cards
        worst = max([res.phase_a, res.phase_b, res.phase_c], key=lambda p: p.vd_pct)
        self._vd_volts = worst.vd_total_v
        self._vd_pct   = worst.vd_pct
        self._passed   = res.all_pass

        self.card_vd_v.set_value(f"Ph {worst.name}: {worst.vd_total_v:.3f} V")
        self.card_vd_pct.set_value(f"Ph {worst.name}: {worst.vd_pct:.2f}%")
        if res.all_pass:
            self.pass_fail_lbl.setObjectName("pass_badge")
            self.pass_fail_lbl.setText("✔  ALL PHASES PASS — SANS 10142-1")
        else:
            self.pass_fail_lbl.setObjectName("fail_badge")
            self.pass_fail_lbl.setText(f"✘  FAIL — Worst: Phase {worst.name} ({worst.vd_pct:.2f}%)")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)

        vnom_ln = res.vnom_ln
        lines = [
            f"UNBALANCED 3-PHASE — SANS 10142-1 §6.2.7",
            f"Supply:   {voltage:.0f} V L-L  (Vn = {vnom_ln:.1f} V L-N)   Route: {length:.1f} m",
            f"Cable:    {cable_desc}   R_phase={r_ph} Ω/km   R_neutral={r_neu} Ω/km",
            f"",
            f"Phase A: I={ia:.1f}A  PF={pfa:.3f}  |  Vd_phase={res.phase_a.vd_phase_v:.3f}V  + "
            f"Vd_neutral={res.vd_neutral_v:.3f}V  = {res.phase_a.vd_total_v:.3f}V "
            f"({res.phase_a.vd_pct:.2f}%)  ➜ {'PASS ✔' if res.phase_a.passed else 'FAIL ✘'}",
            f"Phase B: I={ib:.1f}A  PF={pfb:.3f}  |  Vd_phase={res.phase_b.vd_phase_v:.3f}V  + "
            f"Vd_neutral={res.vd_neutral_v:.3f}V  = {res.phase_b.vd_total_v:.3f}V "
            f"({res.phase_b.vd_pct:.2f}%)  ➜ {'PASS ✔' if res.phase_b.passed else 'FAIL ✘'}",
            f"Phase C: I={ic:.1f}A  PF={pfc:.3f}  |  Vd_phase={res.phase_c.vd_phase_v:.3f}V  + "
            f"Vd_neutral={res.vd_neutral_v:.3f}V  = {res.phase_c.vd_total_v:.3f}V "
            f"({res.phase_c.vd_pct:.2f}%)  ➜ {'PASS ✔' if res.phase_c.passed else 'FAIL ✘'}",
            f"",
            f"Neutral:  IN = {res.neutral_current_a:.3f} A  ∠{res.neutral_angle_deg:.1f}°  |  "
            f"Vd_neutral_conductor = {res.vd_neutral_v:.3f} V",
            f"Limit:    {VD_LIMIT_PCT}%  (= {VD_LIMIT_PCT/100*vnom_ln:.2f} V L-N)",
        ]
        self.summary_lbl.setText("\n".join(lines))

    # ─────────────────────────────────────────────── Table ───────────────────

    def _add_to_table(self):
        if self._vd_volts is None:
            QMessageBox.information(self, "No Result", "Run a calculation first."); return
        self._table_row_counter += 1
        r = self.result_table.rowCount()
        self.result_table.insertRow(r)
        label = self.cable_label_edit.text().strip() or f"Cable {self._table_row_counter}"
        if   self._method_idx() == 0:          ms = "SANS Table"
        elif self._method_idx() == 1:          ms = "Manual R"
        elif self.radio_m3a.isChecked():       ms = "File"
        else:                                  ms = "SWA"

        cells = [str(self._table_row_counter), label,
                 self.system_combo.currentText(), ms,
                 self._last_cable_desc,
                 f"{self.length_spin.value():.1f}",
                 f"{self.current_spin.value():.2f}",
                 f"{self._vd_volts:.3f}", f"{self._vd_pct:.2f}%",
                 "PASS" if self._passed else "FAIL"]
        pc = QColor("#1a3a2a"); pt = QColor("#3fb950")
        fc = QColor("#3a1a1a"); ft = QColor("#f85149")
        for ci, val in enumerate(cells):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if ci == COL_RESULT:
                item.setBackground(QBrush(pc if self._passed else fc))
                item.setForeground(QBrush(pt if self._passed else ft))
                item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            elif ci == COL_VDPCT:
                item.setForeground(QBrush(pt if self._passed else ft))
            elif ci == COL_LABEL:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.result_table.setItem(r, ci, item)
        self._table_empty_lbl.setVisible(False)
        self.result_table.setVisible(True)
        self.cable_label_edit.clear()

    def _remove_selected_row(self):
        rows = sorted({i.row() for i in self.result_table.selectedIndexes()}, reverse=True)
        for r in rows: self.result_table.removeRow(r)
        self._refresh_row_numbers()
        if self.result_table.rowCount() == 0:
            self._table_empty_lbl.setVisible(True); self.result_table.setVisible(False)

    def _clear_table(self):
        if QMessageBox.question(self, "Clear Table", "Remove all rows?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
            self.result_table.setRowCount(0); self._table_row_counter = 0
            self._table_empty_lbl.setVisible(True); self.result_table.setVisible(False)

    def _refresh_row_numbers(self):
        for r in range(self.result_table.rowCount()):
            it = self.result_table.item(r, COL_NUM)
            if it: it.setText(str(r + 1))

    def _get_table_data(self):
        return [[self.result_table.item(r, c).text() if self.result_table.item(r, c) else ""
                 for c in range(len(TABLE_HEADERS))]
                for r in range(self.result_table.rowCount())]

    def _export_table_pdf(self):
        if not self.result_table.rowCount():
            QMessageBox.information(self, "Empty Table", "Add cables first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save Table PDF",
            "CableComparisonTable.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_table_pdf(TABLE_HEADERS, self._get_table_data(), path)
                QMessageBox.information(self, "Saved", f"PDF saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_table_excel(self):
        if not self.result_table.rowCount():
            QMessageBox.information(self, "Empty Table", "Add cables first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save Table Excel",
            "CableComparisonTable.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_table_excel(TABLE_HEADERS, self._get_table_data(), path)
                QMessageBox.information(self, "Saved", f"Excel saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_pdf(self):
        if self._vd_volts is None:
            QMessageBox.information(self, "No Results", "Run a calculation first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "VoltageDropReport.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_pdf(self, path)
                QMessageBox.information(self, "Saved", f"PDF saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_excel(self):
        if self._vd_volts is None:
            QMessageBox.information(self, "No Results", "Run a calculation first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "VoltageDropReport.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_excel(self, path)
                QMessageBox.information(self, "Saved", f"Excel saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────── BaseCalculator ──────────

    def get_inputs(self) -> dict:
        d = {"System Type": self.system_combo.currentText(),
             "Supply Voltage": f"{self.voltage_spin.value():.1f} V",
             "Route Length": f"{self.length_spin.value():.1f} m",
             "Design Current": f"{self.current_spin.value():.2f} A"}
        if self._method_idx() == 0:
            d["Method"] = "Method 1 — SANS Tables"
            d["Material"] = self.m1_material.currentText()
            d["Cable Size"] = self.m1_size.currentText()
            mv = get_mv_per_am(self.m1_material.currentText().lower(), self.m1_size.currentData())
            d["SANS mV/A/m"] = str(mv) if mv else "N/A"
        elif self._method_idx() == 1:
            d["Method"] = "Method 2 — Manual R"
            d["R (Ω/km)"] = f"{self.resistance_spin.value():.4f}"
        else:
            if self.radio_m3a.isChecked():
                d["Method"] = "Method 3A — File Upload"
                idx = self.ds_cable_combo.currentIndex()
                if 0 <= idx < len(self._datasheet_cables):
                    c = self._datasheet_cables[idx]
                    d["Cable"] = c["cable_name"]
                    d["R (Ω/km)"] = f"{c['resistance_ohm_per_km']:.4f}"
            else:
                d["Method"] = "Method 3B — SWA Table"
                d["Material"] = self.swa_material.currentText()
                d["Cable Size"] = self.swa_size.currentText()
                r = get_impedance(STANDARD_SWA,
                                  self.swa_material.currentText().lower(),
                                  self.swa_size.currentData())
                d["Impedance (Ω/km)"] = str(r) if r else "N/A"
        return d

    def get_results(self) -> dict:
        if self._vd_volts is None: return {}
        return {"Voltage Drop (V)": f"{self._vd_volts:.3f} V",
                "Voltage Drop (%)": f"{self._vd_pct:.2f}%",
                "SANS 10142-1 Limit": f"{VDROP_THRESHOLD_PCT}%",
                "Compliance Result": "PASS" if self._passed else "FAIL"}

    def reset(self):
        self.system_combo.setCurrentIndex(0)
        self.voltage_spin.setValue(400); self.length_spin.setValue(50)
        self.current_spin.setValue(40);  self._method_tabs.setCurrentIndex(0)
        self.m1_material.setCurrentIndex(0); self.resistance_spin.setValue(1.15)
        self.cable_label_edit.clear()
        self._vd_volts = self._vd_pct = self._passed = None
        self.card_vd_v.set_value("—"); self.card_vd_pct.set_value("—")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setText("AWAITING CALCULATION")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)
        self.summary_lbl.setText(
            "Enter system parameters and press Calculate to evaluate\n"
            "voltage drop compliance per SANS 10142-1 §6.2.7."
        )
        self._update_formula_display()
        self._m1_update_display()
