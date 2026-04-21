"""
unbalanced_load_widget.py
-------------------------
GUI for the Unbalanced Three-Phase Load Calculator.

Per SANS 10142-1:2020 §6.2.7 — each phase is calculated independently;
neutral current is the phasor sum of the three phase currents.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QDoubleSpinBox, QGroupBox,
    QPushButton, QFrame, QCheckBox, QSizePolicy,
    QFileDialog, QMessageBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QBrush
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.unbalanced_load.unbalanced_load_logic import (
    compute_unbalanced, UnbalancedResult, VD_LIMIT_PCT
)
from calculators.voltage_drop.sans_tables import (
    get_impedance, get_available_sizes, STANDARD_SANS, STANDARD_SWA, ALL_STANDARDS
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sep() -> QFrame:
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine); f.setFrameShadow(QFrame.Shadow.Sunken)
    return f

def _note(t):
    l = QLabel(t); l.setObjectName("header_subtitle"); l.setWordWrap(True); return l

def _action_btn(text, icon, obj, color="white", h=42):
    b = QPushButton(text); b.setObjectName(obj)
    b.setIcon(qta.icon(icon, color=color)); b.setIconSize(QSize(14, 14))
    b.setFixedHeight(h); b.setCursor(Qt.CursorShape.PointingHandCursor); return b

def _spin(lo, hi, val, dec=2, step=1):
    s = QDoubleSpinBox()
    s.setRange(lo, hi); s.setValue(val); s.setDecimals(dec); s.setSingleStep(step)
    return s

def _lbl_val(v="—"):
    l = QLabel(v); l.setObjectName("result_value"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return l

def _lbl_sub(t):
    l = QLabel(t); l.setObjectName("result_label"); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return l

def _badge(text, obj):
    l = QLabel(text); l.setObjectName(obj); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    l.setMinimumWidth(120); return l

PHASE_COLORS = {
    "A": ("#1a3060", "#6ba3e8"),   # blue tint
    "B": ("#1a3a20", "#3fb950"),   # green tint
    "C": ("#3a1a10", "#f0883e"),   # orange tint
}


class PhaseInputGroup(QGroupBox):
    """Input card for a single phase (I, PF, optional separate R)."""
    def __init__(self, phase: str, voltage_ln: float, parent=None):
        label_colors = {"A": "#6ba3e8", "B": "#3fb950", "C": "#f0883e"}
        super().__init__(f"Phase {phase}", parent)
        self.phase = phase
        self.setObjectName("phaseGroup")

        lay = QVBoxLayout(self); lay.setSpacing(10)

        # Phase voltage display
        self.vln_lbl = QLabel(f"Vn (L-N): {voltage_ln:.1f} V")
        self.vln_lbl.setObjectName("header_subtitle")
        lay.addWidget(self.vln_lbl)

        # Current
        crow = QHBoxLayout()
        crow.addWidget(QLabel("Current (A):"))
        self.current_spin = _spin(0, 10000, 100 if phase == "A" else (80 if phase == "B" else 60), 2, 5)
        crow.addWidget(self.current_spin)
        lay.addLayout(crow)

        # Power Factor
        prow = QHBoxLayout()
        prow.addWidget(QLabel("Power Factor:"))
        self.pf_spin = _spin(0.01, 1.0, 0.95, 3, 0.01)
        prow.addWidget(self.pf_spin)
        lay.addLayout(prow)

    def values(self):
        return self.current_spin.value(), self.pf_spin.value()


# ─────────────────────────────────────────────────────────────────────────────
# Main calculator
# ─────────────────────────────────────────────────────────────────────────────

class UnbalancedLoadWidget(BaseCalculator):
    calculator_name = "Unbalanced 3-Phase Load"
    sans_reference  = "SANS 10142-1:2020 §6.2.7"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: UnbalancedResult | None = None
        self._build_ui()

    # ─────────────────────────────────────────────────────── Layout ───────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(32, 28, 32, 32)
        main.setSpacing(20)

        # Title
        tr = QHBoxLayout()
        ico = QLabel(); ico.setPixmap(qta.icon("fa5s.random", color="#f0883e").pixmap(28, 28))
        tr.addWidget(ico); tr.addSpacing(10)
        tc = QVBoxLayout(); tc.setSpacing(2)
        h1 = QLabel("Unbalanced Three-Phase Load Calculator")
        h1.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        h1.setObjectName("section_title"); tc.addWidget(h1)
        tc.addWidget(_note("SANS 10142-1:2020 §6.2.7  •  3-Phase 4-Wire (3P+N) Systems"))
        tr.addLayout(tc); tr.addStretch()
        main.addLayout(tr)
        main.addWidget(_sep())

        # ── System parameters ─────────────────────────────────────────────
        sg = QGroupBox("System Parameters")
        sl = QGridLayout(sg); sl.setSpacing(12); sl.setColumnStretch(1, 1); sl.setColumnStretch(3, 1)

        sl.addWidget(QLabel("Supply Voltage (L-L):"), 0, 0)
        self.voltage_spin = _spin(1, 200000, 400, 1, 10)
        self.voltage_spin.valueChanged.connect(self._on_voltage_changed)
        sl.addWidget(self.voltage_spin, 0, 1)
        sl.addWidget(QLabel("V"), 0, 2)

        self.vln_display = QLabel()
        self.vln_display.setObjectName("header_subtitle")
        sl.addWidget(self.vln_display, 0, 3)

        sl.addWidget(QLabel("Route Length (L):"), 1, 0)
        self.length_spin = _spin(0.1, 100000, 50, 1, 5)
        sl.addWidget(self.length_spin, 1, 1)
        sl.addWidget(QLabel("m"), 1, 2)

        main.addWidget(sg)
        self._on_voltage_changed()

        # ── Cable selection ───────────────────────────────────────────────
        cg = QGroupBox("Conductor / Cable Selection")
        cl = QVBoxLayout(cg); cl.setSpacing(10)

        # Standard
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Cable Standard:"))
        self.std_combo = QComboBox(); self.std_combo.addItems(ALL_STANDARDS)
        self.std_combo.currentTextChanged.connect(self._refresh_cable_sizes)
        r1.addWidget(self.std_combo); r1.addStretch()
        cl.addLayout(r1)

        # Material + size
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Material:"))
        self.mat_combo = QComboBox(); self.mat_combo.addItems(["Copper", "Aluminium"])
        self.mat_combo.currentTextChanged.connect(self._refresh_cable_sizes)
        r2.addWidget(self.mat_combo); r2.addSpacing(20)

        r2.addWidget(QLabel("Phase Conductor Size:"))
        self.size_combo = QComboBox()
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        r2.addWidget(self.size_combo); r2.addSpacing(20)

        r2.addWidget(QLabel("Neutral Conductor Size:"))
        self.neu_size_combo = QComboBox()
        self.neu_size_combo.currentIndexChanged.connect(self._on_neu_size_changed)
        r2.addWidget(self.neu_size_combo); r2.addStretch()
        cl.addLayout(r2)

        # R display
        rr = QHBoxLayout()
        self.r_display = QLabel("Phase R: —"); self.r_display.setObjectName("header_subtitle")
        self.rn_display = QLabel("Neutral R: —"); self.rn_display.setObjectName("header_subtitle")
        rr.addWidget(self.r_display); rr.addSpacing(30); rr.addWidget(self.rn_display); rr.addStretch()
        cl.addLayout(rr)

        # Manual override
        mo_row = QHBoxLayout()
        self.manual_r_chk = QCheckBox("Override — enter resistance manually")
        self.manual_r_chk.toggled.connect(self._toggle_manual_r)
        mo_row.addWidget(self.manual_r_chk)
        self.r_manual_spin  = _spin(0.0001, 1000, 1.15, 4, 0.01)
        self.rn_manual_spin = _spin(0.0001, 1000, 1.15, 4, 0.01)
        mo_row.addSpacing(10)
        mo_row.addWidget(QLabel("Phase R (Ω/km):")); mo_row.addWidget(self.r_manual_spin)
        mo_row.addSpacing(10)
        mo_row.addWidget(QLabel("Neutral R (Ω/km):")); mo_row.addWidget(self.rn_manual_spin)
        mo_row.addStretch()
        cl.addLayout(mo_row)
        self.r_manual_spin.setVisible(False); self.rn_manual_spin.setVisible(False)

        main.addWidget(cg)

        # ── Phase inputs + results ─────────────────────────────────────────
        phases_row = QHBoxLayout(); phases_row.setSpacing(16)
        self.phase_inputs = []
        for ph in ("A", "B", "C"):
            grp = PhaseInputGroup(ph, 400/math.sqrt(3))
            self.phase_inputs.append(grp)
            phases_row.addWidget(grp)
        main.addLayout(phases_row)

        # ── Action buttons ─────────────────────────────────────────────────
        brow = QHBoxLayout(); brow.setSpacing(10)
        self.calc_btn  = _action_btn("  Calculate", "fa5s.calculator", "primary_btn", "white")
        self.reset_btn = _action_btn("  Reset",     "fa5s.redo",       "danger_btn",  "#f85149")
        self.pdf_btn   = _action_btn("  Export PDF","fa5s.file-pdf",   "secondary_btn","#8b949e")
        self.xl_btn    = _action_btn("  Export Excel","fa5s.file-excel","secondary_btn","#8b949e")
        self.calc_btn.clicked.connect(self.calculate)
        self.reset_btn.clicked.connect(self.reset)
        self.pdf_btn.clicked.connect(self._export_pdf)
        self.xl_btn.clicked.connect(self._export_excel)
        for b in (self.calc_btn, self.reset_btn, self.pdf_btn, self.xl_btn):
            brow.addWidget(b)
        brow.addStretch()
        main.addLayout(brow)
        main.addWidget(_sep())

        # ── Results section ────────────────────────────────────────────────
        self._build_results(main)
        self._refresh_cable_sizes()

    def _build_results(self, parent_layout):
        rg = QGroupBox("Calculation Results")
        rl = QVBoxLayout(rg); rl.setSpacing(16)

        # Overall badge + neutral info
        top_row = QHBoxLayout()
        self.overall_badge = QLabel("AWAITING CALCULATION")
        self.overall_badge.setObjectName("neutral_badge")
        self.overall_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overall_badge.setMinimumWidth(280)
        top_row.addWidget(self.overall_badge)
        top_row.addSpacing(30)

        neutral_grp = QGroupBox("Neutral Current")
        neutral_lay = QHBoxLayout(neutral_grp)
        self.neutral_mag_lbl  = _lbl_val("—")
        self.neutral_mag_lbl.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.neutral_ang_lbl  = QLabel("—")
        self.neutral_ang_lbl.setObjectName("header_subtitle")
        self.neutral_vd_lbl   = QLabel("Vd neutral: —")
        self.neutral_vd_lbl.setObjectName("header_subtitle")
        neutral_lay.addWidget(_lbl_sub("IN (A)")); neutral_lay.addWidget(self.neutral_mag_lbl)
        neutral_lay.addSpacing(16)
        neutral_lay.addWidget(self.neutral_ang_lbl)
        neutral_lay.addSpacing(16)
        neutral_lay.addWidget(self.neutral_vd_lbl)
        top_row.addWidget(neutral_grp)
        top_row.addStretch()
        rl.addLayout(top_row)
        rl.addWidget(_sep())

        # Per-phase result cards
        cards_row = QHBoxLayout(); cards_row.setSpacing(16)
        self._phase_cards = {}
        for ph in ("A", "B", "C"):
            bg, fg = PHASE_COLORS[ph]
            card = QGroupBox(f"Phase {ph}")
            card_lay = QGridLayout(card); card_lay.setSpacing(8)
            card.setStyleSheet(f"""
                QGroupBox {{
                    border: 2px solid {fg};
                    border-radius: 8px;
                    margin-top: 8px;
                    padding: 10px;
                    background-color: {bg};
                }}
                QGroupBox::title {{
                    color: {fg}; font-weight: bold; font-size: 13px;
                    subcontrol-origin: margin; left: 10px;
                }}
            """)
            def _r(text, row, col, bold=False, color="#c9d1d9"):
                l = QLabel(text); l.setStyleSheet(f"color:{color}; font-weight:{'bold' if bold else 'normal'}")
                card_lay.addWidget(l, row, col)
                return l

            _r("Current (A):", 0, 0); v_curr = _r("—", 0, 1, True, "#e6edf3")
            _r("Power Factor:", 1, 0); v_pf   = _r("—", 1, 1)
            _r("Phase Vd (V):", 2, 0); v_vdph = _r("—", 2, 1)
            _r("Total Vd (V):", 3, 0); v_vdtot= _r("—", 3, 1, True, "#e6edf3")
            _r("Vd (%):", 4, 0);       v_pct  = _r("—", 4, 1, True)
            badge = _badge("—", "neutral_badge")
            card_lay.addWidget(badge, 5, 0, 1, 2)

            self._phase_cards[ph] = {
                "curr": v_curr, "pf": v_pf,
                "vd_ph": v_vdph, "vd_tot": v_vdtot,
                "pct": v_pct, "badge": badge
            }
            cards_row.addWidget(card)
        rl.addLayout(cards_row)

        # Summary text
        rl.addWidget(_sep())
        self.summary_lbl = QLabel(
            "Enter phase loads, select conductor, and press Calculate."
        )
        self.summary_lbl.setObjectName("header_subtitle")
        self.summary_lbl.setWordWrap(True)
        rl.addWidget(self.summary_lbl)
        parent_layout.addWidget(rg)

    # ─────────────────────────────────────────────────── Signals ─────────

    def _on_voltage_changed(self):
        vll  = self.voltage_spin.value()
        vln  = vll / math.sqrt(3)
        self.vln_display.setText(f"→  L-N: {vln:.1f} V")
        for grp in getattr(self, "phase_inputs", []):
            grp.vln_lbl.setText(f"Vn (L-N): {vln:.1f} V")

    def _refresh_cable_sizes(self):
        std = self.std_combo.currentText()
        mat = self.mat_combo.currentText()
        sizes = get_available_sizes(std, mat)
        for combo in (self.size_combo, self.neu_size_combo):
            combo.blockSignals(True); combo.clear()
            for s in sizes:
                combo.addItem(f"{s} mm²", userData=s)
            # Default phase to 16mm², neutral to 16mm² or first available
            default = next((i for i, s in enumerate(sizes) if s == 16.0), 0)
            combo.setCurrentIndex(default)
            combo.blockSignals(False)
        self._on_size_changed(); self._on_neu_size_changed()

    def _on_size_changed(self):
        r = self._get_r_phase()
        self.r_display.setText(f"Phase R:  {r} Ω/km" if r else "Phase R:  — (not in table)")

    def _on_neu_size_changed(self):
        r = self._get_r_neutral()
        self.rn_display.setText(f"Neutral R:  {r} Ω/km" if r else "Neutral R:  — (not in table)")

    def _toggle_manual_r(self, checked: bool):
        self.r_manual_spin.setVisible(checked); self.rn_manual_spin.setVisible(checked)
        self.size_combo.setEnabled(not checked); self.neu_size_combo.setEnabled(not checked)
        self.r_display.setVisible(not checked);  self.rn_display.setVisible(not checked)

    def _get_r_phase(self):
        if self.manual_r_chk.isChecked():
            return self.r_manual_spin.value()
        std = self.std_combo.currentText(); mat = self.mat_combo.currentText().lower()
        sz  = self.size_combo.currentData()
        return get_impedance(std, mat, sz) if sz else None

    def _get_r_neutral(self):
        if self.manual_r_chk.isChecked():
            return self.rn_manual_spin.value()
        std = self.std_combo.currentText(); mat = self.mat_combo.currentText().lower()
        sz  = self.neu_size_combo.currentData()
        return get_impedance(std, mat, sz) if sz else None

    # ─────────────────────────────────────────────────── Calculation ─────

    def calculate(self):
        r_ph  = self._get_r_phase()
        r_neu = self._get_r_neutral()
        if r_ph is None:
            QMessageBox.warning(self, "No Resistance",
                "Could not find the conductor resistance. Check cable selection or enable manual override.")
            return
        if r_neu is None:
            r_neu = r_ph   # fallback: neutral same as phase

        ia, pfa = self.phase_inputs[0].values()
        ib, pfb = self.phase_inputs[1].values()
        ic, pfc = self.phase_inputs[2].values()

        if ia + ib + ic == 0:
            QMessageBox.warning(self, "Zero Current",
                "All phase currents are zero — nothing to calculate."); return

        res = compute_unbalanced(
            voltage_ll=self.voltage_spin.value(),
            length_m=self.length_spin.value(),
            ia=ia, ib=ib, ic=ic,
            pfa=pfa, pfb=pfb, pfc=pfc,
            r_phase_ohm_per_km=r_ph,
            r_neutral_ohm_per_km=r_neu,
        )
        self._result = res
        self._show_results(res)

    def _show_results(self, r: UnbalancedResult):
        # Overall badge
        if r.all_pass:
            self.overall_badge.setObjectName("pass_badge")
            self.overall_badge.setText("✔  ALL PHASES PASS — SANS 10142-1 Compliant")
        else:
            self.overall_badge.setObjectName("fail_badge")
            txt = f"✘  FAIL — Worst phase: {r.worst_phase}  ({r.worst_vd_pct:.2f}%)"
            self.overall_badge.setText(txt)
        self.overall_badge.style().unpolish(self.overall_badge)
        self.overall_badge.style().polish(self.overall_badge)

        # Neutral
        self.neutral_mag_lbl.setText(f"{r.neutral_current_a:.3f} A")
        self.neutral_ang_lbl.setText(f"∠ {r.neutral_angle_deg:.1f}°")
        self.neutral_vd_lbl.setText(f"Vd neutral conductor:  {r.vd_neutral_v:.3f} V")

        # Per-phase cards
        for ph, pr in (("A", r.phase_a), ("B", r.phase_b), ("C", r.phase_c)):
            c = self._phase_cards[ph]
            passed = pr.passed
            c["curr"].setText(f"{pr.current_a:.2f}")
            c["pf"].setText(f"{pr.pf:.3f}")
            c["vd_ph"].setText(f"{pr.vd_phase_v:.3f} V")
            c["vd_tot"].setText(f"{pr.vd_total_v:.3f} V")
            pct_color = "#3fb950" if passed else "#f85149"
            c["pct"].setText(f"{pr.vd_pct:.2f}%")
            c["pct"].setStyleSheet(f"color:{pct_color}; font-weight:bold")
            badge = c["badge"]
            badge.setObjectName("pass_badge" if passed else "fail_badge")
            badge.setText("✔ PASS" if passed else "✘ FAIL")
            badge.style().unpolish(badge); badge.style().polish(badge)

        # Summary
        lines = [
            f"System:             {r.system_voltage_ll:.0f} V L-L  "
            f"(Vn L-N = {r.vnom_ln:.1f} V)",
            f"Route Length:       {r.length_m:.1f} m",
            f"Phase Conductor:    {r.r_phase_ohm_per_km} Ω/km",
            f"Neutral Conductor:  {r.r_neutral_ohm_per_km} Ω/km",
            "",
            f"Phase A:  I = {r.ia:.2f} A  |  PF = {r.pfa:.3f}  |  "
            f"Vd = {r.phase_a.vd_total_v:.3f} V  ({r.phase_a.vd_pct:.2f}%)  "
            f"→ {'PASS ✔' if r.phase_a.passed else 'FAIL ✘'}",
            f"Phase B:  I = {r.ib:.2f} A  |  PF = {r.pfb:.3f}  |  "
            f"Vd = {r.phase_b.vd_total_v:.3f} V  ({r.phase_b.vd_pct:.2f}%)  "
            f"→ {'PASS ✔' if r.phase_b.passed else 'FAIL ✘'}",
            f"Phase C:  I = {r.ic:.2f} A  |  PF = {r.pfc:.3f}  |  "
            f"Vd = {r.phase_c.vd_total_v:.3f} V  ({r.phase_c.vd_pct:.2f}%)  "
            f"→ {'PASS ✔' if r.phase_c.passed else 'FAIL ✘'}",
            "",
            f"Neutral Current:    {r.neutral_current_a:.3f} A  ∠ {r.neutral_angle_deg:.1f}°",
            f"Neutral Vd:         {r.vd_neutral_v:.3f} V",
            f"SANS Limit:         {VD_LIMIT_PCT}%  "
            f"(= {VD_LIMIT_PCT/100*r.vnom_ln:.2f} V L-N)",
        ]
        self.summary_lbl.setText("\n".join(lines))

    # ─────────────────────────────────────────────────── Export ──────────

    def _export_pdf(self):
        if not self._result:
            QMessageBox.information(self, "No Results", "Run a calculation first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF",
            "UnbalancedLoadReport.pdf", "PDF Files (*.pdf)")
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
            "UnbalancedLoadReport.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                from utils.exporter import Exporter
                Exporter.export_excel(self, path)
                QMessageBox.information(self, "Saved", f"Excel saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ─────────────────────────────────────────────────── BaseCalculator ──

    def get_inputs(self) -> dict:
        ia, pfa = self.phase_inputs[0].values()
        ib, pfb = self.phase_inputs[1].values()
        ic, pfc = self.phase_inputs[2].values()
        r = self._get_r_phase(); rn = self._get_r_neutral()
        return {
            "System Voltage (L-L)": f"{self.voltage_spin.value():.0f} V",
            "Voltage (L-N)":        f"{self.voltage_spin.value()/math.sqrt(3):.1f} V",
            "Route Length":         f"{self.length_spin.value():.1f} m",
            "Phase A Current":      f"{ia:.2f} A  (PF {pfa:.3f})",
            "Phase B Current":      f"{ib:.2f} A  (PF {pfb:.3f})",
            "Phase C Current":      f"{ic:.2f} A  (PF {pfc:.3f})",
            "Phase Conductor R":    f"{r} Ω/km" if r else "—",
            "Neutral Conductor R":  f"{rn} Ω/km" if rn else "—",
        }

    def get_results(self) -> dict:
        r = self._result
        if not r: return {}
        return {
            "Neutral Current (A)":    f"{r.neutral_current_a:.3f} A ∠ {r.neutral_angle_deg:.1f}°",
            "Neutral Conductor Vd":   f"{r.vd_neutral_v:.3f} V",
            "Phase A — Vd Total":     f"{r.phase_a.vd_total_v:.3f} V  ({r.phase_a.vd_pct:.2f}%)",
            "Phase A — Result":       "PASS" if r.phase_a.passed else "FAIL",
            "Phase B — Vd Total":     f"{r.phase_b.vd_total_v:.3f} V  ({r.phase_b.vd_pct:.2f}%)",
            "Phase B — Result":       "PASS" if r.phase_b.passed else "FAIL",
            "Phase C — Vd Total":     f"{r.phase_c.vd_total_v:.3f} V  ({r.phase_c.vd_pct:.2f}%)",
            "Phase C — Result":       "PASS" if r.phase_c.passed else "FAIL",
            "Overall Compliance":     "PASS" if r.all_pass else f"FAIL (worst: Ph {r.worst_phase})",
        }

    def reset(self):
        self.voltage_spin.setValue(400); self.length_spin.setValue(50)
        for i, (I, pf) in enumerate([(100, 0.95), (80, 0.95), (60, 0.95)]):
            self.phase_inputs[i].current_spin.setValue(I)
            self.phase_inputs[i].pf_spin.setValue(pf)
        self._result = None
        self.overall_badge.setObjectName("neutral_badge")
        self.overall_badge.setText("AWAITING CALCULATION")
        self.overall_badge.style().unpolish(self.overall_badge)
        self.overall_badge.style().polish(self.overall_badge)
        self.neutral_mag_lbl.setText("—")
        self.neutral_ang_lbl.setText("—")
        self.neutral_vd_lbl.setText("Vd neutral: —")
        for c in self._phase_cards.values():
            for key in ("curr","pf","vd_ph","vd_tot","pct"):
                c[key].setText("—")
            c["badge"].setObjectName("neutral_badge"); c["badge"].setText("—")
            c["badge"].style().unpolish(c["badge"]); c["badge"].style().polish(c["badge"])
        self.summary_lbl.setText("Enter phase loads, select conductor, and press Calculate.")
