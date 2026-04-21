"""
short_circuit_widget.py
-----------------------
Prospective Short Circuit Current Calculator.
Reference: SANS 10142-1:2020 §5 / IEC 60909 simplified method.

Redesign features:
  - Include / Exclude dropdown for Grid, Transformer, and Cable sections
  - Cable type & size dropdowns auto-fill R/km from Aberdare datasheet
  - Full step-by-step calculation workings displayed after each calculation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QPushButton, QFrame, QSizePolicy, QFileDialog,
    QMessageBox, QScrollArea, QTextEdit,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.short_circuit.short_circuit_logic import (
    calc_short_circuit, build_detailed_workings, ShortCircuitResult,
    STANDARD_VK, STANDARD_ICU, CABLE_DATABASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Small UI helpers
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
    lbl.setFixedWidth(240)
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


def _action_btn(text, icon_name, obj_name, icon_color, height=42):
    btn = QPushButton(text)
    btn.setObjectName(obj_name)
    btn.setIcon(qta.icon(icon_name, color=icon_color))
    btn.setIconSize(QSize(14, 14))
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def _include_combo() -> QComboBox:
    """A compact Include / Exclude selector combo."""
    cb = QComboBox()
    cb.addItem("✔  Include", userData=True)
    cb.addItem("✗  Exclude", userData=False)
    cb.setFixedWidth(130)
    return cb


def _section_toggle_row(title: str, combo: QComboBox) -> QHBoxLayout:
    """Horizontal row: bold section title on the left, include/exclude combo on the right."""
    row = QHBoxLayout()
    lbl = QLabel(title)
    lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
    row.addWidget(lbl, 1)
    row.addWidget(combo)
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Result cards
# ─────────────────────────────────────────────────────────────────────────────

class IscCard(QWidget):
    def __init__(self, label: str, sublabel: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl = QLabel("—")
        self.value_lbl.setObjectName("result_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value_lbl)
        sub = QLabel(label.upper())
        sub.setObjectName("result_label")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        if sublabel:
            sub2 = QLabel(sublabel)
            sub2.setObjectName("header_subtitle")
            sub2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(sub2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(95)

    def set_value(self, text: str):
        self.value_lbl.setText(text)


# ─────────────────────────────────────────────────────────────────────────────
# Main widget
# ─────────────────────────────────────────────────────────────────────────────

class ShortCircuitWidget(BaseCalculator):
    calculator_name = "Prospective Short Circuit Current"
    sans_reference  = "SANS 10142-1:2020 §5  /  IEC 60909"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: ShortCircuitResult | None = None
        self._build_ui()

    # ─────────────────────────────────────────────────────────── UI Build ─────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 32)
        main.setSpacing(20)

        # ── Title ─────────────────────────────────────────────────────────────
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.bolt", color="#f85149").pixmap(28, 28))
        tr.addWidget(ico)
        tr.addSpacing(10)
        tc = QVBoxLayout()
        tc.setSpacing(2)
        h1 = QLabel("Prospective Short Circuit Current")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title")
        tc.addWidget(h1)
        tc.addWidget(_note(
            "SANS 10142-1:2020 §5  |  IEC 60909 Simplified Method  |  "
            "Grid + Transformer + Cable impedance"
        ))
        tr.addLayout(tc)
        tr.addStretch()
        main.addLayout(tr)
        main.addWidget(_sep())

        # ── Two-column body ───────────────────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(24)
        left  = QVBoxLayout()
        left.setSpacing(14)
        right = QVBoxLayout()
        right.setSpacing(14)

        # ═══════════════════════════════════════ LEFT COLUMN (inputs) ════════

        # ── System Voltage ────────────────────────────────────────────────────
        sg = QGroupBox("System Parameters")
        sl = QVBoxLayout(sg)
        sl.setSpacing(10)
        self.voltage_combo = QComboBox()
        for v in ["230 V (L-N Single Phase)", "400 V (3-Phase LV)", "11 000 V (MV)", "33 000 V (MV)"]:
            self.voltage_combo.addItem(v, userData=float(v.replace(" ", "").split("V")[0]))
        self.voltage_combo.setCurrentIndex(1)
        self.voltage_combo.currentIndexChanged.connect(self._update_z_preview)
        sl.addLayout(_input_row("System Voltage", self.voltage_combo))
        left.addWidget(sg)

        # ── Grid Source ───────────────────────────────────────────────────────
        gg = QGroupBox()
        gg.setFlat(True)
        gl = QVBoxLayout(gg)
        gl.setSpacing(10)
        gl.setContentsMargins(12, 8, 12, 12)

        self._grid_combo = _include_combo()
        self._grid_combo.currentIndexChanged.connect(self._toggle_grid)
        gl.addLayout(_section_toggle_row("Grid Source Impedance", self._grid_combo))
        gl.addWidget(_sep())

        self._grid_panel = QWidget()
        gpl = QVBoxLayout(self._grid_panel)
        gpl.setContentsMargins(0, 4, 0, 0)
        gpl.setSpacing(10)
        gpl.addWidget(_note(
            "Obtain the fault level (MVA) at the Point of Common Coupling (PCC) "
            "from the utility (Eskom / Municipality). Typical LV PCC: 5–15 MVA."
        ))
        self.fault_mva_spin = QDoubleSpinBox()
        self.fault_mva_spin.setRange(0.1, 5000)
        self.fault_mva_spin.setValue(10)
        self.fault_mva_spin.setDecimals(1)
        self.fault_mva_spin.setSingleStep(0.5)
        self.fault_mva_spin.valueChanged.connect(self._update_z_preview)
        gpl.addLayout(_input_row("Grid Fault Level (PCC)", self.fault_mva_spin, "MVA"))
        self.z_grid_lbl = QLabel("Z_grid = — mΩ")
        self.z_grid_lbl.setObjectName("header_subtitle")
        gpl.addWidget(self.z_grid_lbl)
        gl.addWidget(self._grid_panel)

        # Style the group to look like the others
        gg.setStyleSheet("QGroupBox { border: 1px solid #30363d; border-radius: 6px; }")
        left.addWidget(gg)

        # ── Transformer ───────────────────────────────────────────────────────
        tg = QGroupBox()
        tg.setFlat(True)
        tl = QVBoxLayout(tg)
        tl.setSpacing(10)
        tl.setContentsMargins(12, 8, 12, 12)

        self._trafo_combo = _include_combo()
        self._trafo_combo.currentIndexChanged.connect(self._toggle_trafo)
        tl.addLayout(_section_toggle_row("Transformer (MV/LV)", self._trafo_combo))
        tl.addWidget(_sep())

        self._trafo_panel = QWidget()
        tpl = QVBoxLayout(self._trafo_panel)
        tpl.setContentsMargins(0, 4, 0, 0)
        tpl.setSpacing(10)

        self.trafo_kva_combo = QComboBox()
        for label in STANDARD_VK:
            self.trafo_kva_combo.addItem(label, userData=float(label.replace(" kVA", "")))
        self.trafo_kva_combo.setCurrentIndex(5)  # 315 kVA
        self.trafo_kva_combo.currentIndexChanged.connect(self._auto_fill_vk)
        tpl.addLayout(_input_row("Transformer Rating", self.trafo_kva_combo, "kVA"))

        self.vk_spin = QDoubleSpinBox()
        self.vk_spin.setRange(0.1, 20)
        self.vk_spin.setValue(4.0)
        self.vk_spin.setDecimals(2)
        self.vk_spin.setSingleStep(0.5)
        self.vk_spin.valueChanged.connect(self._update_z_preview)
        tpl.addLayout(_input_row("Short Circuit Voltage (Vk%)", self.vk_spin, "%"))

        self.z_trafo_lbl = QLabel("Z_trafo = — mΩ")
        self.z_trafo_lbl.setObjectName("header_subtitle")
        tpl.addWidget(self.z_trafo_lbl)
        tl.addWidget(self._trafo_panel)
        self.trafo_kva_combo.currentIndexChanged.connect(self._update_z_preview)

        tg.setStyleSheet("QGroupBox { border: 1px solid #30363d; border-radius: 6px; }")
        left.addWidget(tg)

        # ── Cable to Fault Point ──────────────────────────────────────────────
        cg2 = QGroupBox()
        cg2.setFlat(True)
        c2l = QVBoxLayout(cg2)
        c2l.setSpacing(10)
        c2l.setContentsMargins(12, 8, 12, 12)

        self._cable_combo = _include_combo()
        self._cable_combo.currentIndexChanged.connect(self._toggle_cable)
        c2l.addLayout(_section_toggle_row("Cable to Fault Point", self._cable_combo))
        c2l.addWidget(_sep())

        self._cable_panel = QWidget()
        cpl = QVBoxLayout(self._cable_panel)
        cpl.setContentsMargins(0, 4, 0, 0)
        cpl.setSpacing(10)
        cpl.addWidget(_note(
            "Select a cable from the library (auto-fills R from Aberdare datasheet) "
            "or choose Manual Entry to type a resistance directly."
        ))

        # Cable type (library) selector
        self.cable_type_combo = QComboBox()
        for key in CABLE_DATABASE:
            self.cable_type_combo.addItem(key, userData=key)
        self.cable_type_combo.currentIndexChanged.connect(self._on_cable_type_changed)
        cpl.addLayout(_input_row("Cable Type / Library", self.cable_type_combo))

        # Cable size selector (hidden for Manual Entry)
        self._cable_size_row_widget = QWidget()
        csr = QHBoxLayout(self._cable_size_row_widget)
        csr.setContentsMargins(0, 0, 0, 0)
        sz_lbl = QLabel("Cable Size")
        sz_lbl.setFixedWidth(240)
        csr.addWidget(sz_lbl)
        self.cable_size_combo = QComboBox()
        self.cable_size_combo.currentIndexChanged.connect(self._on_cable_size_changed)
        csr.addWidget(self.cable_size_combo, 1)
        sz_unit = QLabel("mm²")
        sz_unit.setObjectName("result_label")
        sz_unit.setFixedWidth(60)
        csr.addWidget(sz_unit)
        cpl.addWidget(self._cable_size_row_widget)

        # R/km — auto-filled but editable
        self.cable_r_spin = QDoubleSpinBox()
        self.cable_r_spin.setRange(0.0001, 10000)
        self.cable_r_spin.setValue(0.3325)
        self.cable_r_spin.setDecimals(4)
        self.cable_r_spin.setSingleStep(0.01)
        self.cable_r_spin.valueChanged.connect(self._update_z_preview)
        cpl.addLayout(_input_row("R — Phase Conductor", self.cable_r_spin, "Ω/km"))

        # Cable source note
        self.cable_source_lbl = QLabel("")
        self.cable_source_lbl.setObjectName("header_subtitle")
        self.cable_source_lbl.setWordWrap(True)
        cpl.addWidget(self.cable_source_lbl)

        # Length
        self.cable_len_spin = QDoubleSpinBox()
        self.cable_len_spin.setRange(0.1, 100000)
        self.cable_len_spin.setValue(50)
        self.cable_len_spin.setDecimals(1)
        self.cable_len_spin.setSingleStep(5)
        self.cable_len_spin.valueChanged.connect(self._update_z_preview)
        cpl.addLayout(_input_row("Cable Length (one-way)", self.cable_len_spin, "m"))

        # Number of parallel cables
        self.parallel_cables_spin = QSpinBox()
        self.parallel_cables_spin.setRange(1, 10)
        self.parallel_cables_spin.setValue(1)
        self.parallel_cables_spin.setSingleStep(1)
        self.parallel_cables_spin.valueChanged.connect(self._update_z_preview)
        cpl.addLayout(_input_row("Cables in Parallel", self.parallel_cables_spin))

        self.z_cable_lbl = QLabel("Z_cable = — mΩ")
        self.z_cable_lbl.setObjectName("header_subtitle")
        cpl.addWidget(self.z_cable_lbl)
        c2l.addWidget(self._cable_panel)

        cg2.setStyleSheet("QGroupBox { border: 1px solid #30363d; border-radius: 6px; }")
        left.addWidget(cg2)

        # ── Protection Device ─────────────────────────────────────────────────
        pg = QGroupBox("Protection Device (OCPD)")
        pl = QVBoxLayout(pg)
        pl.setSpacing(10)
        pl.addWidget(_note(
            "Per SANS 10142-1 §5.3: Icu (breaking capacity) must be ≥ the prospective "
            "short circuit current at the device installation point."
        ))
        self.icu_combo = QComboBox()
        for ka in STANDARD_ICU:
            self.icu_combo.addItem(f"{ka} kA", userData=float(ka))
        self.icu_combo.setCurrentIndex(2)  # 16 kA default
        pl.addLayout(_input_row("Device Breaking Capacity (Icu)", self.icu_combo, "kA"))
        left.addWidget(pg)

        # ── Action buttons ────────────────────────────────────────────────────
        brow = QHBoxLayout()
        brow.setSpacing(10)
        self.calc_btn  = _action_btn("  Calculate",  "fa5s.calculator",  "primary_btn",   "white")
        self.pdf_btn   = _action_btn("  PDF",        "fa5s.file-pdf",    "secondary_btn", "#8b949e")
        self.excel_btn = _action_btn("  Excel",      "fa5s.file-excel",  "secondary_btn", "#8b949e")
        self.reset_btn = _action_btn("  Reset",      "fa5s.redo",        "danger_btn",    "#f85149")
        self.calc_btn.clicked.connect(self._calculate)
        self.pdf_btn.clicked.connect(self._export_pdf)
        self.excel_btn.clicked.connect(self._export_excel)
        self.reset_btn.clicked.connect(self.reset)
        for b in (self.calc_btn, self.pdf_btn, self.excel_btn, self.reset_btn):
            brow.addWidget(b)
        left.addLayout(brow)
        left.addStretch()

        # ═══════════════════════════════════════ RIGHT COLUMN (results) ═══════

        rg = QGroupBox("Fault Current Results")
        rl = QVBoxLayout(rg)
        rl.setSpacing(12)

        # Quick-read cards
        cards = QHBoxLayout()
        cards.setSpacing(8)
        self.card_3ph_max = IscCard("Isc 3-Phase (Max)", "c = 1.05")
        self.card_3ph_min = IscCard("Isc 3-Phase (Min)", "c = 0.95")
        self.card_ll      = IscCard("Isc Line-Line",     "L-L fault")
        self.card_ln      = IscCard("Isc Line-Neutral",  "L-N fault")
        for c in (self.card_3ph_max, self.card_3ph_min, self.card_ll, self.card_ln):
            cards.addWidget(c)
        rl.addLayout(cards)

        # Live impedance preview (updates as you type, before Calculate)
        rl.addWidget(_sep())
        iz_grp = QGroupBox("Live Impedance Preview")
        iz_lay = QVBoxLayout(iz_grp)
        iz_lay.setSpacing(4)
        self.z_live_lbl = QLabel("Enter values to see impedance breakdown.")
        self.z_live_lbl.setObjectName("header_subtitle")
        self.z_live_lbl.setWordWrap(True)
        iz_lay.addWidget(self.z_live_lbl)
        rl.addWidget(iz_grp)

        # Pass/Fail badge
        rl.addWidget(_sep())
        pf_row = QHBoxLayout()
        pf_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl = QLabel("AWAITING CALCULATION")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl.setMinimumWidth(340)
        pf_row.addStretch()
        pf_row.addWidget(self.pass_fail_lbl)
        pf_row.addStretch()
        rl.addLayout(pf_row)

        # ── Step-by-Step Workings (collapsible) ──────────────────────────────────
        rl.addWidget(_sep())

        # Header row with collapse/expand toggle
        wkr = QHBoxLayout()
        wkr_lbl = QLabel("Step-by-Step Calculation Workings")
        wkr_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        wkr.addWidget(wkr_lbl)
        wkr.addStretch()
        self._workings_toggle_btn = QPushButton("▶  Show Workings")
        self._workings_toggle_btn.setObjectName("secondary_btn")
        self._workings_toggle_btn.setFixedHeight(28)
        self._workings_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._workings_toggle_btn.clicked.connect(self._toggle_workings)
        wkr.addWidget(self._workings_toggle_btn)
        rl.addLayout(wkr)

        # Collapsible body — starts hidden, auto-expands after Calculate
        self._workings_container = QWidget()
        wcl = QVBoxLayout(self._workings_container)
        wcl.setContentsMargins(0, 6, 0, 0)
        wcl.setSpacing(4)
        wcl.addWidget(_note(
            "Full derivation showing formula → substitution → result for each step. "
            "Each step cites the relevant SANS / IEC clause."
        ))
        self.workings_edit = QTextEdit()
        self.workings_edit.setReadOnly(True)
        self.workings_edit.setFont(QFont("Consolas", 9))
        self.workings_edit.setMinimumHeight(400)
        self.workings_edit.setPlaceholderText(
            "Press  Calculate  to generate the full step-by-step workings here.\n\n"
            "Each step shows:\n"
            "  • The formula used (with SANS / IEC reference)\n"
            "  • All input values substituted\n"
            "  • The intermediate arithmetic\n"
            "  • The final result with units\n\n"
            "This allows any engineer to follow, verify, and audit the calculation."
        )
        self.workings_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        wcl.addWidget(self.workings_edit)
        self._workings_container.setVisible(False)   # collapsed by default
        rl.addWidget(self._workings_container)
        rl.addStretch()

        right.addWidget(rg)
        right.addStretch()

        cols.addLayout(left,  45)
        cols.addLayout(right, 55)
        main.addLayout(cols)

        # ── Initialise state ──────────────────────────────────────────────────
        self._on_cable_type_changed()
        self._update_z_preview()

    # ─────────────────────────────────────────── Workings panel toggle ──────

    def _toggle_workings(self):
        visible = not self._workings_container.isVisible()
        self._workings_container.setVisible(visible)
        self._workings_toggle_btn.setText(
            "▼  Hide Workings" if visible else "▶  Show Workings")

    # ─────────────────────────────────────────────────────────── Helpers ──────

    def _get_voltage(self) -> float:
        return self.voltage_combo.currentData() or 400.0

    def _grid_included(self) -> bool:
        return self._grid_combo.currentData() is True

    def _trafo_included(self) -> bool:
        return self._trafo_combo.currentData() is True

    def _cable_included(self) -> bool:
        return self._cable_combo.currentData() is True

    def _is_manual_cable(self) -> bool:
        return self.cable_type_combo.currentText() == "Manual Entry"

    # ─────────────────────────────────────────────────────── Toggle panels ────

    def _toggle_grid(self):
        self._grid_panel.setVisible(self._grid_included())
        self._update_z_preview()

    def _toggle_trafo(self):
        self._trafo_panel.setVisible(self._trafo_included())
        self._update_z_preview()

    def _toggle_cable(self):
        self._cable_panel.setVisible(self._cable_included())
        self._update_z_preview()

    # ─────────────────────────────────────────────────── Cable library ────────

    def _on_cable_type_changed(self):
        key = self.cable_type_combo.currentText()
        db  = CABLE_DATABASE.get(key, {})
        sizes = db.get("sizes", {})
        is_manual = (key == "Manual Entry")

        # Toggle the size selector
        self._cable_size_row_widget.setVisible(not is_manual)

        # Populate size combo
        self.cable_size_combo.blockSignals(True)
        self.cable_size_combo.clear()
        for mm2 in sorted(sizes.keys()):
            self.cable_size_combo.addItem(f"{mm2} mm²", userData=mm2)
        self.cable_size_combo.blockSignals(False)

        # Update source note
        src = db.get("source", "")
        self.cable_source_lbl.setText(f"Source: {src}" if src else "")

        if not is_manual and sizes:
            self._on_cable_size_changed()  # auto-fill R
        self._update_z_preview()

    def _on_cable_size_changed(self):
        if self._is_manual_cable():
            return
        key   = self.cable_type_combo.currentText()
        mm2   = self.cable_size_combo.currentData()
        sizes = CABLE_DATABASE.get(key, {}).get("sizes", {})
        r_val = sizes.get(mm2)
        if r_val is not None:
            self.cable_r_spin.blockSignals(True)
            self.cable_r_spin.setValue(r_val)
            self.cable_r_spin.blockSignals(False)
        self._update_z_preview()

    # ──────────────────────────────────────────────── Live Z preview ──────────

    def _auto_fill_vk(self):
        label = self.trafo_kva_combo.currentText()
        vk = STANDARD_VK.get(label, 4.0)
        self.vk_spin.setValue(vk)

    def _update_z_preview(self):
        import math
        vn = self._get_voltage()
        parts = []

        if self._grid_included():
            fl = self.fault_mva_spin.value()
            z_g = (vn ** 2 / (fl * 1e6)) * 1000
            self.z_grid_lbl.setText(f"Z_grid = {z_g:.3f} mΩ  (Vn={vn:.0f}V, {fl:.1f} MVA)")
            parts.append(f"Z_grid = {z_g:.3f} mΩ")
        else:
            parts.append("Z_grid = 0  (excluded)")

        if self._trafo_included():
            kva = self.trafo_kva_combo.currentData() or 315
            vk  = self.vk_spin.value()
            z_t = ((vk / 100) * (vn ** 2) / (kva * 1000)) * 1000
            self.z_trafo_lbl.setText(f"Z_trafo = {z_t:.3f} mΩ  ({kva:.0f} kVA, Vk={vk:.2f}%)")
            parts.append(f"Z_trafo = {z_t:.3f} mΩ")
        else:
            parts.append("Z_trafo = 0  (excluded)")

        if self._cable_included():
            r = self.cable_r_spin.value()
            l = self.cable_len_spin.value()
            n = max(1, self.parallel_cables_spin.value())
            z_c = 2 * r * l / 1000 * 1000 / n
            par_str = f" ÷ {n}" if n > 1 else ""
            self.z_cable_lbl.setText(f"Z_cable = {z_c:.3f} mΩ  (2 × {r:.4f} Ω/km × {l:.1f} m{par_str})")
            parts.append(f"Z_cable = {z_c:.3f} mΩ")
        else:
            parts.append("Z_cable = 0  (excluded)")

        # Total
        z_total = 0.0
        if self._grid_included():
            fl = self.fault_mva_spin.value()
            z_total += (vn ** 2 / (fl * 1e6)) * 1000
        if self._trafo_included():
            kva = self.trafo_kva_combo.currentData() or 315
            vk  = self.vk_spin.value()
            z_total += ((vk / 100) * (vn ** 2) / (kva * 1000)) * 1000
        if self._cable_included():
            r = self.cable_r_spin.value()
            l = self.cable_len_spin.value()
            n = max(1, self.parallel_cables_spin.value())
            z_total += 2 * r * l / 1000 * 1000 / n

        if z_total > 0:
            isc_est = (1.05 * vn) / (math.sqrt(3) * z_total / 1000) / 1000
            self.z_live_lbl.setText(
                "\n".join(parts) +
                f"\nZ_total = {z_total:.3f} mΩ"
                f"\n→ Isc_3φ_max ≈ {isc_est:.3f} kA  (estimate, press Calculate for full result)"
            )
        else:
            self.z_live_lbl.setText(
                "\n".join(parts) + "\nZ_total = 0  (all sections excluded — nothing to calculate)"
            )

    # ─────────────────────────────────────────────────── Calculation ──────────

    def _calculate(self):
        vn    = self._get_voltage()
        fl    = self.fault_mva_spin.value()
        kva   = self.trafo_kva_combo.currentData() or 315
        vk    = self.vk_spin.value()
        r     = self.cable_r_spin.value()
        l     = self.cable_len_spin.value()
        icu   = self.icu_combo.currentData() or 16

        cable_key  = self.cable_type_combo.currentText()
        cable_mm2  = self.cable_size_combo.currentData() or 0.0

        result = calc_short_circuit(
            system_voltage_v     = vn,
            fault_level_mva      = fl,
            trafo_kva            = kva,
            trafo_vk_pct         = vk,
            cable_r_ohm_per_km   = r,
            cable_length_m       = l,
            breaker_icu_ka       = icu,
            include_trafo        = self._trafo_included(),
            include_grid         = self._grid_included(),
            include_cable        = self._cable_included(),
            cable_type_label     = cable_key,
            cable_size_mm2       = cable_mm2 if not self._is_manual_cable() else 0.0,
            num_parallel_cables  = self.parallel_cables_spin.value(),
        )
        self._result = result

        # ── Update result cards ───────────────────────────────────────────────
        self.card_3ph_max.set_value(f"{result.isc_3ph_max_ka:.3f} kA")
        self.card_3ph_min.set_value(f"{result.isc_3ph_min_ka:.3f} kA")
        self.card_ll.set_value(f"{result.isc_ll_ka:.3f} kA")
        self.card_ln.set_value(f"{result.isc_ln_ka:.3f} kA")

        # ── Update live Z panel ───────────────────────────────────────────────
        self.z_live_lbl.setText(
            f"Z_grid  = {result.z_grid_mohm:.4f} mΩ\n"
            f"Z_trafo = {result.z_trafo_mohm:.4f} mΩ\n"
            f"Z_cable = {result.z_cable_mohm:.4f} mΩ\n"
            f"Z_total = {result.z_total_mohm:.4f} mΩ"
        )

        # ── Pass/fail badge ───────────────────────────────────────────────────
        if result.breaker_adequate:
            self.pass_fail_lbl.setObjectName("pass_badge")
            self.pass_fail_lbl.setText(
                f"✔  DEVICE ADEQUATE — Icu ({icu:.0f} kA) ≥ Isc ({result.isc_3ph_max_ka:.3f} kA)"
            )
        else:
            self.pass_fail_lbl.setObjectName("fail_badge")
            self.pass_fail_lbl.setText(
                f"✘  DEVICE INADEQUATE — Icu ({icu:.0f} kA) < Isc ({result.isc_3ph_max_ka:.3f} kA)"
            )
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)

        # ── Generate & display detailed workings ──────────────────────────────
        workings = build_detailed_workings(result)
        self.workings_edit.setPlainText(workings)
        # Auto-expand the workings panel on first calculation
        if not self._workings_container.isVisible():
            self._toggle_workings()

    # ─────────────────────────────────────────────────────────── Exports ──────

    def _export_pdf(self):
        if not self._result:
            QMessageBox.information(self, "No Results", "Run a calculation first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "ShortCircuit_Report.pdf", "PDF Files (*.pdf)"
        )
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_pdf(self, path)
                QMessageBox.information(self, "Saved", f"PDF saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_excel(self):
        if not self._result:
            QMessageBox.information(self, "No Results", "Run a calculation first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "ShortCircuit_Report.xlsx", "Excel Files (*.xlsx)"
        )
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_excel(self, path)
                QMessageBox.information(self, "Saved", f"Excel saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ──────────────────────────────────────────────── BaseCalculator API ──────

    def get_inputs(self) -> dict:
        d = {
            "System Voltage":            f"{self._get_voltage():.0f} V",
            "Include Grid Impedance":    "Yes" if self._grid_included() else "No",
            "Include Trafo Impedance":   "Yes" if self._trafo_included() else "No",
            "Include Cable Impedance":   "Yes" if self._cable_included() else "No",
        }
        if self._grid_included():
            d["Grid Fault Level"] = f"{self.fault_mva_spin.value()} MVA"
        if self._trafo_included():
            d["Transformer Rating"] = self.trafo_kva_combo.currentText()
            d["Transformer Vk%"]    = f"{self.vk_spin.value():.2f}%"
        if self._cable_included():
            if not self._is_manual_cable():
                d["Cable Type"] = self.cable_type_combo.currentText()
                d["Cable Size"] = f"{self.cable_size_combo.currentData()} mm²"
            d["Cable R"]             = f"{self.cable_r_spin.value():.4f} Ω/km"
            d["Cable Length"]        = f"{self.cable_len_spin.value():.1f} m"
            d["Cables in Parallel"]  = str(self.parallel_cables_spin.value())
        d["Device Breaking Cap (Icu)"] = f"{self.icu_combo.currentData():.0f} kA"
        return d

    def get_workings(self) -> str:
        """Return the detailed step-by-step calculation workings as plain text."""
        if not self._result:
            return ""
        return self.workings_edit.toPlainText()

    def get_results(self) -> dict:
        if not self._result:
            return {}
        r = self._result
        return {
            "Z_grid (mΩ)":              f"{r.z_grid_mohm:.4f}",
            "Z_trafo (mΩ)":             f"{r.z_trafo_mohm:.4f}",
            "Z_cable (mΩ)":             f"{r.z_cable_mohm:.4f}",
            "Z_total (mΩ)":             f"{r.z_total_mohm:.4f}",
            "Isc 3-phase max (c=1.05)": f"{r.isc_3ph_max_ka:.3f} kA",
            "Isc 3-phase min (c=0.95)": f"{r.isc_3ph_min_ka:.3f} kA",
            "Isc Line-Line":            f"{r.isc_ll_ka:.3f} kA",
            "Isc Line-Neutral":         f"{r.isc_ln_ka:.3f} kA",
            "Device Icu":               f"{r.breaker_icu_ka:.0f} kA",
            "Compliance Result":        "PASS — Device Adequate" if r.breaker_adequate else "FAIL — Device Inadequate",
        }

    def reset(self):
        self.voltage_combo.setCurrentIndex(1)
        self._grid_combo.setCurrentIndex(0)
        self._trafo_combo.setCurrentIndex(0)
        self._cable_combo.setCurrentIndex(0)
        self.fault_mva_spin.setValue(10)
        self.trafo_kva_combo.setCurrentIndex(5)
        self.vk_spin.setValue(4.0)
        self.cable_type_combo.setCurrentIndex(0)
        self.cable_len_spin.setValue(50)
        self.parallel_cables_spin.setValue(1)
        self.icu_combo.setCurrentIndex(2)
        self._result = None
        for c in (self.card_3ph_max, self.card_3ph_min, self.card_ll, self.card_ln):
            c.set_value("—")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setText("AWAITING CALCULATION")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)
        self.workings_edit.clear()
        if self._workings_container.isVisible():
            self._toggle_workings()
        self._on_cable_type_changed()
        self._update_z_preview()
