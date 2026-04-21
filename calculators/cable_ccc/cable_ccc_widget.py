"""
cable_ccc_widget.py
-------------------
SANS 10142-1:2020 Cable Current Carrying Capacity (CCC) & Derating Calculator.

Tables used:
  Table 1  — Base CCC for PVC insulated cables at 70°C (copper & aluminium)
  Table 2  — Base CCC for XLPE insulated cables at 90°C (copper & aluminium)
  Table 3  — Ambient temperature correction factors (Ca)
  Table 4  — Grouping / bunching correction factors (Cg)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QPushButton, QFrame, QSizePolicy, QFileDialog,
    QMessageBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.cable_ccc.cable_ccc_logic import (
    calc_ccc, suggest_minimum_size, get_base_ccc, get_ca, get_cg,
    INSTALL_METHODS, INSTALL_METHOD_KEYS, CABLE_ARRANGEMENTS,
    COPPER_SIZES, ALUMINIUM_SIZES, AMBIENT_TEMPS, AMBIENT_TEMPS_XLPE, GROUP_COUNTS,
    CCCResult,
)


def _sep() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _note(text: str) -> QLabel:
    lbl = QLabel(text); lbl.setObjectName("header_subtitle"); lbl.setWordWrap(True)
    return lbl


def _input_row(label: str, widget: QWidget, unit: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label); lbl.setFixedWidth(230)
    row.addWidget(lbl); row.addWidget(widget, 1)
    if unit:
        u = QLabel(unit); u.setObjectName("result_label"); u.setFixedWidth(60)
        row.addWidget(u)
    else:
        row.addSpacing(60)
    return row


def _action_btn(text, icon_name, obj_name, icon_color, height=42):
    btn = QPushButton(text); btn.setObjectName(obj_name)
    btn.setIcon(qta.icon(icon_name, color=icon_color))
    btn.setIconSize(QSize(14, 14)); btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class ResultCard(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4); lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl = QLabel("—"); self.value_lbl.setObjectName("result_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value_lbl)
        sub = QLabel(label.upper()); sub.setObjectName("result_label")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(90)

    def set_value(self, text: str):
        self.value_lbl.setText(text)


class CableCCCWidget(BaseCalculator):
    calculator_name = "Cable Current Carrying Capacity (CCC)"
    sans_reference  = "SANS 10142-1:2020 Tables 1–4"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: CCCResult | None = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 32)
        main.setSpacing(20)

        # ── Title ─────────────────────────────────────────────────────────
        tr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(qta.icon("fa5s.plug", color="#58a6ff").pixmap(28, 28))
        tr.addWidget(ico); tr.addSpacing(10)
        tc = QVBoxLayout(); tc.setSpacing(2)
        h1 = QLabel("Cable Current Carrying Capacity")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title"); tc.addWidget(h1)
        tc.addWidget(_note("SANS 10142-1:2020 — Tables 1, 2, 3 & 4  |  Derating for Ambient Temperature & Grouping"))
        tr.addLayout(tc); tr.addStretch()
        main.addLayout(tr)
        main.addWidget(_sep())

        # ── Two-column body ────────────────────────────────────────────────
        cols = QHBoxLayout(); cols.setSpacing(20)
        left = QVBoxLayout(); left.setSpacing(16)
        right = QVBoxLayout(); right.setSpacing(16)

        # ── Cable Parameters ───────────────────────────────────────────────
        cg = QGroupBox("Cable Parameters")
        cl = QVBoxLayout(cg); cl.setSpacing(12)

        # Insulation type
        ins_row = QHBoxLayout()
        self._ins_group = QButtonGroup(self)
        self.radio_pvc  = QRadioButton("PVC  (70°C conductor, SANS Table 1)")
        self.radio_xlpe = QRadioButton("XLPE  (90°C conductor, SANS Table 2)")
        self.radio_pvc.setChecked(True)
        self._ins_group.addButton(self.radio_pvc, 1)
        self._ins_group.addButton(self.radio_xlpe, 2)
        ins_row.addWidget(self.radio_pvc); ins_row.addSpacing(20)
        ins_row.addWidget(self.radio_xlpe); ins_row.addStretch()
        cl.addLayout(ins_row)
        cl.addWidget(_sep())

        # Material
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Copper", "Aluminium"])
        self.material_combo.currentTextChanged.connect(self._update_sizes)
        cl.addLayout(_input_row("Conductor Material", self.material_combo))

        # Installation method
        self.install_combo = QComboBox()
        for key, desc in INSTALL_METHODS.items():
            self.install_combo.addItem(desc, userData=key)
        self.install_combo.setCurrentIndex(4)  # default: C
        self.install_combo.currentIndexChanged.connect(self._update_base_display)
        cl.addLayout(_input_row("Installation Method", self.install_combo))

        # Cable size
        self.size_combo = QComboBox()
        cl.addLayout(_input_row("Conductor Size", self.size_combo, "mm²"))
        self.size_combo.currentIndexChanged.connect(self._update_base_display)

        # Design current
        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(0.1, 10000); self.current_spin.setValue(100)
        self.current_spin.setDecimals(2); self.current_spin.setSingleStep(5)
        cl.addLayout(_input_row("Design Current (Ib)", self.current_spin, "A"))

        left.addWidget(cg)

        # ── Derating Conditions ────────────────────────────────────────────
        dg = QGroupBox("Derating Conditions")
        dl = QVBoxLayout(dg); dl.setSpacing(12)

        dl.addWidget(_note(
            "Correction factors per SANS 10142-1:2020:\n"
            "  Ca — Ambient temperature (Table 3)  |  Cg — Cable grouping (Table 4)"
        ))

        # Ambient temperature
        self.ambient_combo = QComboBox()
        for t in AMBIENT_TEMPS:
            self.ambient_combo.addItem(f"{t} °C", userData=t)
        self.ambient_combo.setCurrentIndex(AMBIENT_TEMPS.index(30))  # default 30°C
        dl.addLayout(_input_row("Ambient Temperature", self.ambient_combo))

        # Number of grouped circuits
        self.group_spin = QSpinBox()
        self.group_spin.setRange(1, 20); self.group_spin.setValue(1)
        dl.addLayout(_input_row("No. of Grouped Circuits", self.group_spin))

        # Cable arrangement (touching vs. spaced)
        arr_row = QHBoxLayout()
        arr_lbl = QLabel("Cable Arrangement"); arr_lbl.setFixedWidth(230)
        arr_row.addWidget(arr_lbl)
        self._arr_group = QButtonGroup(self)
        self.radio_touching = QRadioButton("Touching")
        self.radio_spaced   = QRadioButton("Spaced  (≥ 1 cable Ø gap)")
        self.radio_touching.setChecked(True)
        self._arr_group.addButton(self.radio_touching, 1)
        self._arr_group.addButton(self.radio_spaced,   2)
        arr_row.addWidget(self.radio_touching)
        arr_row.addSpacing(16)
        arr_row.addWidget(self.radio_spaced)
        arr_row.addStretch()
        dl.addLayout(arr_row)
        dl.addWidget(_note(
            "  Touching: cables in contact — conservative (SANS Table 4).\n"
            "  Spaced: ≥ 1 cable diameter gap — less mutual heating, higher Cg."
        ))

        # Live derating display
        self.ca_lbl = QLabel("Ca = 1.00  (30°C reference)")
        self.ca_lbl.setObjectName("header_subtitle")
        self.cg_lbl = QLabel("Cg = 1.00  (single circuit, touching)")
        self.cg_lbl.setObjectName("header_subtitle")
        self.base_lbl = QLabel("Base CCC = —")
        self.base_lbl.setObjectName("header_subtitle")
        for w in (self.ca_lbl, self.cg_lbl, self.base_lbl):
            dl.addWidget(w)

        left.addWidget(dg)

        # ── Suggest minimum size ───────────────────────────────────────────
        sg = QGroupBox("Minimum Cable Size Finder")
        sl = QVBoxLayout(sg); sl.setSpacing(10)
        sl.addWidget(_note(
            "Find the smallest cable that can carry the design current "
            "under the conditions above."
        ))
        self.suggest_btn = _action_btn("  Find Minimum Size", "fa5s.search",
                                       "secondary_btn", "#8b949e", 36)
        self.suggest_btn.clicked.connect(self._suggest_size)
        self.suggest_lbl = QLabel("—")
        self.suggest_lbl.setObjectName("header_subtitle")
        sl.addWidget(self.suggest_btn)
        sl.addWidget(self.suggest_lbl)
        left.addWidget(sg)

        # ── Action buttons ─────────────────────────────────────────────────
        brow = QHBoxLayout(); brow.setSpacing(10)
        self.calc_btn    = _action_btn("  Calculate",  "fa5s.calculator", "primary_btn",   "white")
        self.pdf_btn     = _action_btn("  PDF",        "fa5s.file-pdf",   "secondary_btn", "#8b949e")
        self.excel_btn   = _action_btn("  Excel",      "fa5s.file-excel", "secondary_btn", "#8b949e")
        self.reset_btn   = _action_btn("  Reset",      "fa5s.redo",       "danger_btn",    "#f85149")
        self.calc_btn.clicked.connect(self._calculate)
        self.pdf_btn.clicked.connect(self._export_pdf)
        self.excel_btn.clicked.connect(self._export_excel)
        self.reset_btn.clicked.connect(self.reset)
        for b in (self.calc_btn, self.pdf_btn, self.excel_btn, self.reset_btn):
            brow.addWidget(b)
        left.addLayout(brow)
        left.addStretch()

        # ── Results ────────────────────────────────────────────────────────
        rg = QGroupBox("Calculation Results")
        rl = QVBoxLayout(rg); rl.setSpacing(12)
        rl.addWidget(_note(
            "SANS 10142-1:2020 — Cable passes when Ib ≤ Iz (derated CCC).\n"
            "Final Iz = Base CCC × Ca × Cg"
        ))
        rl.addWidget(_sep())

        cards = QHBoxLayout(); cards.setSpacing(12)
        self.card_base   = ResultCard("Base CCC (A)")
        self.card_derate = ResultCard("Derated CCC — Iz (A)")
        self.card_util   = ResultCard("Utilisation (%)")
        for c in (self.card_base, self.card_derate, self.card_util):
            cards.addWidget(c)
        rl.addLayout(cards)

        # Pass/fail badge
        pf = QHBoxLayout(); pf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl = QLabel("AWAITING CALCULATION")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_fail_lbl.setMinimumWidth(260)
        pf.addStretch(); pf.addWidget(self.pass_fail_lbl); pf.addStretch()
        rl.addLayout(pf)

        rl.addWidget(_sep())
        self.summary_lbl = QLabel(
            "Select cable parameters and derating conditions,\n"
            "then press Calculate to check CCC compliance."
        )
        self.summary_lbl.setObjectName("header_subtitle")
        self.summary_lbl.setWordWrap(True)
        self.summary_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        rl.addWidget(self.summary_lbl)

        rl.addWidget(_sep())
        fgrp = QGroupBox("Applied Formula Reference")
        fl = QVBoxLayout(fgrp)
        self.formula_lbl = QLabel(
            "Iz  =  Base CCC  ×  Ca  ×  Cg\n\n"
            "  Base CCC — SANS 10142-1 Table 1 (PVC) or Table 2 (XLPE)\n"
            "  Ca       — Ambient temperature correction (Table 3)\n"
            "  Cg       — Grouping correction (Table 4)\n"
            "             • Touching: cables in contact (conservative)\n"
            "             • Spaced:   ≥ 1 cable diameter gap (less derating)\n\n"
            "Pass criterion:  Ib  ≤  Iz"
        )
        self.formula_lbl.setObjectName("header_subtitle")
        self.formula_lbl.setWordWrap(True)
        fl.addWidget(self.formula_lbl)
        rl.addWidget(fgrp)
        rl.addStretch()

        right.addWidget(rg); right.addStretch()
        cols.addLayout(left, 50); cols.addLayout(right, 50)
        main.addLayout(cols)

        # ── Wire up signals ────────────────────────────────────────────────
        self.radio_pvc.toggled.connect(self._on_insulation_changed)
        self.radio_xlpe.toggled.connect(self._on_insulation_changed)
        self.ambient_combo.currentIndexChanged.connect(self._update_derating_display)
        self.group_spin.valueChanged.connect(self._update_derating_display)
        self.radio_touching.toggled.connect(self._update_derating_display)
        self.radio_spaced.toggled.connect(self._update_derating_display)
        self.material_combo.currentTextChanged.connect(self._update_sizes)

        self._update_sizes("Copper")
        self._update_derating_display()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _insulation(self) -> str:
        return "XLPE" if self.radio_xlpe.isChecked() else "PVC"

    def _arrangement(self) -> str:
        return "spaced" if self.radio_spaced.isChecked() else "touching"

    def _install_key(self) -> str:
        return self.install_combo.currentData()

    def _on_insulation_changed(self):
        ins = self._insulation()
        # Update ambient temperature options
        temps = AMBIENT_TEMPS_XLPE if ins == "XLPE" else AMBIENT_TEMPS
        current_temp = self.ambient_combo.currentData()
        self.ambient_combo.blockSignals(True)
        self.ambient_combo.clear()
        for t in temps:
            self.ambient_combo.addItem(f"{t} °C", userData=t)
        # Restore previous temp if available
        idx = next((i for i, t in enumerate(temps) if t == current_temp), 
                   temps.index(30) if 30 in temps else 0)
        self.ambient_combo.setCurrentIndex(idx)
        self.ambient_combo.blockSignals(False)
        self._update_sizes(self.material_combo.currentText())
        self._update_derating_display()

    def _update_sizes(self, material: str = ""):
        mat = self.material_combo.currentText()
        sizes = COPPER_SIZES if mat.lower() == "copper" else ALUMINIUM_SIZES
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        for s in sizes:
            self.size_combo.addItem(f"{s} mm²", userData=s)
        # Default to 16mm²
        idx = next((i for i, s in enumerate(sizes) if s == 16.0), 0)
        self.size_combo.setCurrentIndex(idx)
        self.size_combo.blockSignals(False)
        self._update_base_display()

    def _update_base_display(self):
        mat     = self.material_combo.currentText()
        method  = self._install_key()
        size    = self.size_combo.currentData()
        ins     = self._insulation()
        if size is None:
            return
        base = get_base_ccc(ins, mat, method, size)
        self.base_lbl.setText(
            f"Base CCC = {base} A  ({ins}, Method {method}, {size} mm²)"
            if base else f"Base CCC = Not available for this combination"
        )

    def _update_derating_display(self):
        ins  = self._insulation()
        temp = self.ambient_combo.currentData() or 30
        n    = self.group_spin.value()
        arr  = self._arrangement()
        ca   = get_ca(ins, temp)
        cg   = get_cg(n, arr)
        arr_label = "touching" if arr == "touching" else "spaced 1Ø"
        self.ca_lbl.setText(f"Ca = {ca:.3f}  (ambient {temp}°C, {ins} insulation)")
        self.cg_lbl.setText(
            f"Cg = {cg:.3f}  ({n} grouped circuit{'s' if n > 1 else ''}, {arr_label})"
        )
        self._update_base_display()

    # ── Calculation ────────────────────────────────────────────────────────

    def _calculate(self):
        ins     = self._insulation()
        mat     = self.material_combo.currentText()
        method  = self._install_key()
        size    = self.size_combo.currentData()
        temp    = self.ambient_combo.currentData() or 30
        n       = self.group_spin.value()
        ib      = self.current_spin.value()
        arr     = self._arrangement()

        result = calc_ccc(ins, mat, method, size, temp, n, ib, arr)
        if result is None:
            QMessageBox.warning(self, "Lookup Error",
                f"No CCC data found for {ins} / {mat} / Method {method} / {size} mm².\n"
                "Try a different installation method or insulation type.")
            return

        self._result = result
        self.card_base.set_value(f"{result.base_ccc:.0f} A")
        self.card_derate.set_value(f"{result.derated_ccc:.1f} A")
        self.card_util.set_value(f"{result.utilisation_pct:.1f}%")

        if result.passed:
            self.pass_fail_lbl.setObjectName("pass_badge")
            self.pass_fail_lbl.setText("✔  PASS — Cable adequately rated")
        else:
            self.pass_fail_lbl.setObjectName("fail_badge")
            self.pass_fail_lbl.setText("✘  FAIL — Cable undersized for conditions")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)

        margin = result.derated_ccc - result.design_current
        arr_display = "Touching" if result.arrangement == "touching" else "Spaced (≥ 1 cable Ø)"
        self.summary_lbl.setText(
            f"Insulation:         {result.insulation} ({('70°C' if result.insulation=='PVC' else '90°C')} conductor)\n"
            f"Material:           {result.material}\n"
            f"Installation:       Method {result.install_method}\n"
            f"Cable Size:         {result.size_mm2} mm²\n"
            f"Ambient Temp:       {result.ambient_temp}°C\n"
            f"Grouped Circuits:   {result.num_circuits}\n"
            f"Cable Arrangement:  {arr_display}\n\n"
            f"Base CCC (SANS):    {result.base_ccc} A\n"
            f"Ca (temp factor):   {result.ca:.3f}\n"
            f"Cg (group factor):  {result.cg:.3f}  [{arr_display}]\n"
            f"Derated CCC (Iz):   {result.derated_ccc:.1f} A\n"
            f"Design Current (Ib):{result.design_current:.2f} A\n"
            f"Margin:             {margin:+.1f} A\n"
            f"Utilisation:        {result.utilisation_pct:.1f}%\n"
            f"Result:             {'PASS ✔' if result.passed else 'FAIL ✘'}"
        )

    def _suggest_size(self):
        ins    = self._insulation()
        mat    = self.material_combo.currentText()
        method = self._install_key()
        temp   = self.ambient_combo.currentData() or 30
        n      = self.group_spin.value()
        ib     = self.current_spin.value()
        arr    = self._arrangement()

        size = suggest_minimum_size(ins, mat, method, temp, n, ib, arr)
        arr_label = "touching" if arr == "touching" else "spaced 1Ø"
        if size:
            self.suggest_lbl.setText(
                f"Minimum size: {size} mm²  ({ins} / {mat} / Method {method} / "
                f"{temp}°C / {n} circuit{'s' if n>1 else ''} / {arr_label})"
            )
            # Auto-select in combo
            idx = next((i for i in range(self.size_combo.count())
                        if self.size_combo.itemData(i) == size), -1)
            if idx >= 0:
                self.size_combo.setCurrentIndex(idx)
        else:
            self.suggest_lbl.setText(
                "No standard cable size can carry this current under the given conditions. "
                "Consider parallel cables or different installation method."
            )

    # ── Exports ────────────────────────────────────────────────────────────

    def _export_pdf(self):
        if not self._result:
            QMessageBox.information(self, "No Results", "Run a calculation first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF",
            "CableCCC_Report.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_pdf(self, path)
                QMessageBox.information(self, "Saved", f"PDF saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_excel(self):
        if not self._result:
            QMessageBox.information(self, "No Results", "Run a calculation first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel",
            "CableCCC_Report.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_excel(self, path)
                QMessageBox.information(self, "Saved", f"Excel saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ── BaseCalculator interface ───────────────────────────────────────────

    def get_inputs(self) -> dict:
        arr = self._arrangement()
        return {
            "Insulation Type":    self._insulation(),
            "Conductor Material": self.material_combo.currentText(),
            "Installation Method": self.install_combo.currentText(),
            "Conductor Size":     f"{self.size_combo.currentData()} mm²",
            "Design Current (Ib)":f"{self.current_spin.value():.2f} A",
            "Ambient Temperature":f"{self.ambient_combo.currentData()} °C",
            "Grouped Circuits":   str(self.group_spin.value()),
            "Cable Arrangement":  "Touching" if arr == "touching" else "Spaced (≥ 1 cable Ø)",
        }

    def get_results(self) -> dict:
        if not self._result:
            return {}
        r = self._result
        arr_display = "Touching" if r.arrangement == "touching" else "Spaced (≥ 1 cable Ø)"
        return {
            "Base CCC (SANS Table)":    f"{r.base_ccc:.0f} A",
            "Ca (Ambient Factor)":      f"{r.ca:.3f}",
            "Cg (Grouping Factor)":     f"{r.cg:.3f}  [{arr_display}]",
            "Derated CCC (Iz)":         f"{r.derated_ccc:.1f} A",
            "Design Current (Ib)":      f"{r.design_current:.2f} A",
            "Utilisation":              f"{r.utilisation_pct:.1f}%",
            "Compliance Result":        "PASS" if r.passed else "FAIL",
        }

    def reset(self):
        self.radio_pvc.setChecked(True)
        self.radio_touching.setChecked(True)
        self.material_combo.setCurrentIndex(0)
        self.install_combo.setCurrentIndex(4)
        self.current_spin.setValue(100)
        self.group_spin.setValue(1)
        self._result = None
        self.card_base.set_value("—")
        self.card_derate.set_value("—")
        self.card_util.set_value("—")
        self.pass_fail_lbl.setObjectName("neutral_badge")
        self.pass_fail_lbl.setText("AWAITING CALCULATION")
        self.pass_fail_lbl.style().unpolish(self.pass_fail_lbl)
        self.pass_fail_lbl.style().polish(self.pass_fail_lbl)
        self.summary_lbl.setText(
            "Select cable parameters and derating conditions,\n"
            "then press Calculate to check CCC compliance."
        )
        self.suggest_lbl.setText("—")
        self._update_sizes("Copper")
        self._update_derating_display()
