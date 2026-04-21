"""
pv_stringing_widget.py
----------------------
PV String Sizing calculator widget.

Inputs:
  - Panel STC datasheet values (Voc, Vmp, Isc, Imp, Pmax)
  - Temperature coefficients (β_Voc, β_Vmp, α_Isc  in %/°C)
  - Site temperatures (T_min ambient, T_max cell)
  - Inverter / MPPT limits (V_max, V_mppt_min, V_mppt_max, I_mppt_max)

Outputs:
  - Temperature-corrected Voc (cold) / Vmp (hot) / Isc (hot)
  - Max / min / recommended series count
  - Max parallel strings per MPPT
  - Array totals (Voc string, Vmp string, kWp)
  - Export to Excel (.xlsx)
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QGroupBox, QPushButton, QFrame, QSizePolicy, QFileDialog,
    QMessageBox, QLineEdit, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.pv_stringing.pv_stringing_logic import calc_string_sizing, export_to_excel


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _note(text):
    lbl = QLabel(text)
    lbl.setObjectName("header_subtitle")
    lbl.setWordWrap(True)
    return lbl


def _input_row(label: str, widget: QWidget, unit: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(260)
    row.addWidget(lbl)
    row.addWidget(widget, 1)
    if unit:
        u = QLabel(unit)
        u.setObjectName("result_label")
        u.setFixedWidth(55)
        row.addWidget(u)
    else:
        row.addSpacing(55)
    return row


def _dbl(val, lo, hi, decimals=3, step=0.001):
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSingleStep(step)
    s.setValue(val)
    return s


def _action_btn(text, icon_name, obj_name, icon_color, height=42):
    btn = QPushButton(text)
    btn.setObjectName(obj_name)
    btn.setIcon(qta.icon(icon_name, color=icon_color))
    btn.setIconSize(QSize(16, 16))
    btn.setFixedHeight(height)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class ResultCard(QWidget):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_lbl = QLabel("—")
        self.value_lbl.setObjectName("result_value")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value_lbl)
        sub = QLabel(label.upper())
        sub.setObjectName("result_label")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        lay.addWidget(sub)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(90)

    def set_value(self, text: str, pass_fail: str = "neutral"):
        self.value_lbl.setText(text)
        self.value_lbl.setObjectName(
            "result_value" if pass_fail == "neutral"
            else ("pass_badge" if pass_fail == "pass" else "fail_badge")
        )
        self.value_lbl.style().unpolish(self.value_lbl)
        self.value_lbl.style().polish(self.value_lbl)


# ─────────────────────────────────────────────────────────────────────────────
# Main Widget
# ─────────────────────────────────────────────────────────────────────────────

class PVStringWidget(BaseCalculator):
    calculator_name = "PV String Sizing"
    sans_reference  = "IEC 62548 / IEC 61215  •  Solareff Engineering"

    # Emitted when user clicks "Send to Layout"
    sig_send_to_layout = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result = None
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Title
        title = QLabel("PV String Sizing")
        title.setObjectName("section_title")
        root.addWidget(title)
        root.addWidget(_note(
            "IEC 62548 temperature-corrected string sizing — "
            "calculates series & parallel counts to fit your inverter MPPT window."
        ))
        root.addWidget(_sep())

        # ── Two-column layout ─────────────────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(16)
        left  = QVBoxLayout(); left.setSpacing(12)
        right = QVBoxLayout(); right.setSpacing(12)
        cols.addLayout(left,  1)
        cols.addLayout(right, 1)
        root.addLayout(cols)

        # ── LEFT: Panel Specs ─────────────────────────────────────────────────
        grp_panel = QGroupBox("Panel Datasheet (STC)")
        gl = QVBoxLayout(grp_panel); gl.setSpacing(8)
        gl.addWidget(_note(
            "Enter values from the panel datasheet at Standard Test Conditions "
            "(1000 W/m², 25 °C, AM 1.5)."
        ))

        self._voc   = _dbl(41.40, 1, 999, 3, 0.01)
        self._vmp   = _dbl(34.60, 1, 999, 3, 0.01)
        self._isc   = _dbl(10.05, 0.1, 99, 3, 0.01)
        self._imp   = _dbl(9.50,  0.1, 99, 3, 0.01)
        self._pmax  = _dbl(330.0, 1, 9999, 1, 1.0)

        for lbl, w, unit in [
            ("Open-circuit voltage (Voc)",    self._voc,  "V"),
            ("Max power voltage (Vmp)",        self._vmp,  "V"),
            ("Short-circuit current (Isc)",    self._isc,  "A"),
            ("Max power current (Imp)",        self._imp,  "A"),
            ("Peak power (Pmax)",              self._pmax, "W"),
        ]:
            gl.addLayout(_input_row(lbl, w, unit))

        left.addWidget(grp_panel)

        # ── LEFT: Temperature Coefficients ───────────────────────────────────
        grp_tc = QGroupBox("Temperature Coefficients (%/°C)")
        tl = QVBoxLayout(grp_tc); tl.setSpacing(8)
        tl.addWidget(_note(
            "From datasheet — typically Voc & Vmp are negative, Isc is positive."
        ))

        self._beta_voc  = _dbl(-0.300, -5.0, 5.0, 4, 0.001)
        self._beta_vmp  = _dbl(-0.350, -5.0, 5.0, 4, 0.001)
        self._alpha_isc = _dbl( 0.050, -5.0, 5.0, 4, 0.001)

        for lbl, w in [
            ("β Voc  (voltage temp. coeff.)",   self._beta_voc),
            ("β Vmp  (Vmp temp. coeff.)",        self._beta_vmp),
            ("α Isc  (current temp. coeff.)",    self._alpha_isc),
        ]:
            tl.addLayout(_input_row(lbl, w, "%/°C"))

        left.addWidget(grp_tc)

        # ── LEFT: Site Temperatures ───────────────────────────────────────────
        grp_temp = QGroupBox("Site Temperatures")
        tmpl = QVBoxLayout(grp_temp); tmpl.setSpacing(8)
        tmpl.addWidget(_note(
            "T_min = lowest expected ambient (e.g. winter night).  "
            "T_max = highest expected cell temperature (ambient + ~25–35 °C irradiance rise)."
        ))

        self._t_min = _dbl(-5.0,  -40.0, 40.0, 1, 1.0)
        self._t_max = _dbl( 70.0,  20.0, 100.0, 1, 1.0)

        tmpl.addLayout(_input_row("Minimum ambient temp (T_min)", self._t_min, "°C"))
        tmpl.addLayout(_input_row("Maximum cell temp (T_max)",    self._t_max, "°C"))

        left.addWidget(grp_temp)
        left.addStretch()

        # ── RIGHT: Inverter / MPPT ────────────────────────────────────────────
        grp_inv = QGroupBox("Inverter / MPPT Limits")
        il = QVBoxLayout(grp_inv); il.setSpacing(8)
        il.addWidget(_note(
            "From the inverter datasheet.  "
            "V_max = absolute max DC input voltage.  "
            "MPPT window = voltage range where MPPT tracks.  "
            "I_mppt_max = max current per MPPT input."
        ))

        self._v_inv_max  = _dbl(1000.0, 100, 1500, 1, 10.0)
        self._v_mppt_min = _dbl(200.0,   50,  999, 1, 10.0)
        self._v_mppt_max = _dbl(800.0,  100, 1500, 1, 10.0)
        self._i_mppt_max = _dbl(25.0,    1,   200, 1,  0.5)

        for lbl, w, unit in [
            ("Max DC input voltage (V_max)",       self._v_inv_max,  "V"),
            ("MPPT window — lower limit",           self._v_mppt_min, "V"),
            ("MPPT window — upper limit",           self._v_mppt_max, "V"),
            ("Max MPPT input current (I_mppt_max)", self._i_mppt_max, "A"),
        ]:
            il.addLayout(_input_row(lbl, w, unit))

        right.addWidget(grp_inv)

        # ── RIGHT: System Configuration (for Send to Layout) ─────────────────
        grp_sys = QGroupBox("System Configuration  (for Layout tool)")
        sl = QVBoxLayout(grp_sys); sl.setSpacing(8)
        sl.addWidget(_note(
            "Enter project totals so the Layout tool can be pre-filled "
            "with the correct inverter & MPPT configuration."
        ))

        self._inv_count      = QSpinBox(); self._inv_count.setRange(1, 50);  self._inv_count.setValue(1)
        self._mppts_per_inv  = QSpinBox(); self._mppts_per_inv.setRange(1, 50); self._mppts_per_inv.setValue(4)
        self._total_panels   = QSpinBox(); self._total_panels.setRange(1, 100000); self._total_panels.setValue(100)
        self._total_panels.setSingleStep(10)

        for lbl, w, unit in [
            ("Number of inverters",   self._inv_count,     ""),
            ("MPPTs per inverter",     self._mppts_per_inv, ""),
            ("Total panels on roof",   self._total_panels,  "panels"),
        ]:
            sl.addLayout(_input_row(lbl, w, unit))

        right.addWidget(grp_sys)

        # ── RIGHT: Project Metadata ───────────────────────────────────────────
        grp_meta = QGroupBox("Project Info  (for Excel export)")
        ml = QVBoxLayout(grp_meta); ml.setSpacing(8)

        self._project     = QLineEdit(); self._project.setPlaceholderText("Project name")
        self._client      = QLineEdit(); self._client.setPlaceholderText("Client")
        self._location    = QLineEdit(); self._location.setPlaceholderText("Site / location")
        self._prepared_by = QLineEdit(); self._prepared_by.setPlaceholderText("Engineer name")

        for lbl, w in [
            ("Project",      self._project),
            ("Client",       self._client),
            ("Location",     self._location),
            ("Prepared by",  self._prepared_by),
        ]:
            row = QHBoxLayout()
            l = QLabel(lbl); l.setFixedWidth(120)
            row.addWidget(l); row.addWidget(w, 1)
            ml.addLayout(row)

        right.addWidget(grp_meta)

        # ── RIGHT: Results ────────────────────────────────────────────────────
        grp_res = QGroupBox("Results")
        rl = QVBoxLayout(grp_res); rl.setSpacing(10)

        # Row 1 — corrected values
        row1 = QHBoxLayout(); row1.setSpacing(8)
        self._card_voc_cold = ResultCard("Voc  cold  (V)")
        self._card_vmp_hot  = ResultCard("Vmp  hot   (V)")
        self._card_isc_hot  = ResultCard("Isc  hot   (A)")
        for c in [self._card_voc_cold, self._card_vmp_hot, self._card_isc_hot]:
            row1.addWidget(c)
        rl.addLayout(row1)

        # Row 2 — series counts
        row2 = QHBoxLayout(); row2.setSpacing(8)
        self._card_max_series  = ResultCard("Max series\n(Voc limit)")
        self._card_min_series  = ResultCard("Min series\n(MPPT lower)")
        self._card_rec_series  = ResultCard("Recommended\nseries")
        for c in [self._card_max_series, self._card_min_series, self._card_rec_series]:
            row2.addWidget(c)
        rl.addLayout(row2)

        # Row 3 — parallel + totals
        row3 = QHBoxLayout(); row3.setSpacing(8)
        self._card_max_par    = ResultCard("Max parallel\nstrings")
        self._card_voc_str    = ResultCard("Voc per\nstring (V)")
        self._card_kwp        = ResultCard("Array total\n(kWp STC)")
        for c in [self._card_max_par, self._card_voc_str, self._card_kwp]:
            row3.addWidget(c)
        rl.addLayout(row3)

        # Warning label
        self._warn_lbl = QLabel("")
        self._warn_lbl.setObjectName("fail_badge")
        self._warn_lbl.setWordWrap(True)
        self._warn_lbl.setVisible(False)
        rl.addWidget(self._warn_lbl)

        right.addWidget(grp_res)
        right.addStretch()

        # ── Buttons ───────────────────────────────────────────────────────────
        root.addWidget(_sep())
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self._btn_calc   = _action_btn("Calculate Stringing",  "fa5s.solar-panel",   "primary_btn",   "#ffffff")
        self._btn_reset  = _action_btn("Reset",                "fa5s.undo",          "secondary_btn", "#8b949e")
        self._btn_export = _action_btn("Export to Excel",      "fa5s.file-excel",    "secondary_btn", "#3fb950")
        self._btn_send   = _action_btn("Send to Layout  →",    "fa5s.arrow-right",   "secondary_btn", "#58a6ff")
        self._btn_export.setEnabled(False)
        self._btn_send.setEnabled(False)
        self._btn_send.setToolTip(
            "Pre-fills the Layout & Stringing tab with inverter count, "
            "MPPTs, strings per MPPT and panels per string from the calc result."
        )
        btn_row.addWidget(self._btn_calc)
        btn_row.addWidget(self._btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_export)
        btn_row.addWidget(self._btn_send)
        root.addLayout(btn_row)

        # ── Signals ───────────────────────────────────────────────────────────
        self._btn_calc.clicked.connect(self._calculate)
        self._btn_reset.clicked.connect(self.reset)
        self._btn_export.clicked.connect(self._export_excel)
        self._btn_send.clicked.connect(self._emit_send_to_layout)

    # ── Calculation ───────────────────────────────────────────────────────────

    def _calculate(self):
        try:
            res = calc_string_sizing(
                voc_stc   = self._voc.value(),
                vmp_stc   = self._vmp.value(),
                isc_stc   = self._isc.value(),
                pmax_stc  = self._pmax.value(),
                beta_voc  = self._beta_voc.value(),
                beta_vmp  = self._beta_vmp.value(),
                alpha_isc = self._alpha_isc.value(),
                t_min     = self._t_min.value(),
                t_max     = self._t_max.value(),
                v_inv_max  = self._v_inv_max.value(),
                v_mppt_min = self._v_mppt_min.value(),
                v_mppt_max = self._v_mppt_max.value(),
                i_mppt_max = self._i_mppt_max.value(),
            )
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", str(e))
            return

        self._result = res

        # Populate result cards
        self._card_voc_cold.set_value(f"{res.voc_cold:.2f} V")
        self._card_vmp_hot.set_value(f"{res.vmp_hot:.2f} V")
        self._card_isc_hot.set_value(f"{res.isc_hot:.2f} A")

        self._card_max_series.set_value(str(res.max_series_voc))
        self._card_min_series.set_value(str(res.min_series_mppt))
        pf = "pass" if res.valid else "fail"
        self._card_rec_series.set_value(str(res.recommended_series), pf)

        self._card_max_par.set_value(str(res.max_parallel))
        self._card_voc_str.set_value(f"{res.voc_string:.1f} V")
        self._card_kwp.set_value(f"{res.power_stc_array/1000:.2f} kWp")

        if res.warnings:
            self._warn_lbl.setText("⚠  " + "  |  ".join(res.warnings))
            self._warn_lbl.setVisible(True)
        else:
            self._warn_lbl.setVisible(False)

        self._btn_export.setEnabled(True)
        self._btn_send.setEnabled(True)

    def _emit_send_to_layout(self):
        """Emit the config dict so the combined widget can pre-fill the Layout tab."""
        self.sig_send_to_layout.emit(self.get_layout_config())

    def get_layout_config(self) -> dict:
        """Return inverter/string config suitable for pre-filling the Layout tool."""
        config = {
            "inverter_count":    self._inv_count.value(),
            "mppts_per_inverter": self._mppts_per_inv.value(),
            "total_panels":      self._total_panels.value(),
            "panel_wp":          self._pmax.value(),
        }
        if self._result:
            config["strings_per_mppt"]  = self._result.max_parallel
            config["panels_per_string"] = self._result.recommended_series
        return config

    # ── Excel export ──────────────────────────────────────────────────────────

    def _export_excel(self):
        if not self._result:
            return

        fpath, _ = QFileDialog.getSaveFileName(
            self, "Save Excel Report", "PV_String_Sizing.xlsx",
            "Excel Workbook (*.xlsx)"
        )
        if not fpath:
            return

        inputs = {
            "Panel Datasheet (STC)": [
                ("Open-circuit voltage (Voc)",  self._voc.value(),  "V"),
                ("Max power voltage (Vmp)",     self._vmp.value(),  "V"),
                ("Short-circuit current (Isc)", self._isc.value(),  "A"),
                ("Max power current (Imp)",     self._imp.value(),  "A"),
                ("Peak power (Pmax)",           self._pmax.value(), "W"),
            ],
            "Temperature Coefficients": [
                ("β Voc  (%/°C)", self._beta_voc.value(),  "%/°C"),
                ("β Vmp  (%/°C)", self._beta_vmp.value(),  "%/°C"),
                ("α Isc  (%/°C)", self._alpha_isc.value(), "%/°C"),
            ],
            "Site Temperatures": [
                ("Minimum ambient temp (T_min)", self._t_min.value(), "°C"),
                ("Maximum cell temp (T_max)",    self._t_max.value(), "°C"),
            ],
            "Inverter / MPPT Limits": [
                ("Max DC input voltage",    self._v_inv_max.value(),  "V"),
                ("MPPT lower limit",        self._v_mppt_min.value(), "V"),
                ("MPPT upper limit",        self._v_mppt_max.value(), "V"),
                ("Max MPPT input current",  self._i_mppt_max.value(), "A"),
            ],
        }

        try:
            export_to_excel(
                self._result,
                fpath,
                project     = self._project.text(),
                client      = self._client.text(),
                location    = self._location.text(),
                prepared_by = self._prepared_by.text(),
                inputs      = inputs,
            )
            QMessageBox.information(
                self, "Export Complete",
                f"Excel report saved to:\n{fpath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    # ── BaseCalculator interface ──────────────────────────────────────────────

    def get_inputs(self) -> dict:
        return {
            "Voc (STC)":          f"{self._voc.value()} V",
            "Vmp (STC)":          f"{self._vmp.value()} V",
            "Isc (STC)":          f"{self._isc.value()} A",
            "Pmax (STC)":         f"{self._pmax.value()} W",
            "β Voc":              f"{self._beta_voc.value()} %/°C",
            "β Vmp":              f"{self._beta_vmp.value()} %/°C",
            "α Isc":              f"{self._alpha_isc.value()} %/°C",
            "T_min":              f"{self._t_min.value()} °C",
            "T_max":              f"{self._t_max.value()} °C",
            "V_inv_max":          f"{self._v_inv_max.value()} V",
            "V_mppt_min":         f"{self._v_mppt_min.value()} V",
            "V_mppt_max":         f"{self._v_mppt_max.value()} V",
            "I_mppt_max":         f"{self._i_mppt_max.value()} A",
        }

    def get_results(self) -> dict:
        if not self._result:
            return {}
        r = self._result
        return {
            "Voc cold":              f"{r.voc_cold} V",
            "Vmp hot":               f"{r.vmp_hot} V",
            "Isc hot":               f"{r.isc_hot} A",
            "Max series (Voc)":      r.max_series_voc,
            "Min series (MPPT)":     r.min_series_mppt,
            "Max series (MPPT)":     r.max_series_mppt,
            "Recommended series":    r.recommended_series,
            "Max parallel strings":  r.max_parallel,
            "Voc per string":        f"{r.voc_string} V",
            "Vmp per string":        f"{r.vmp_string} V",
            "Array power (STC)":     f"{r.power_stc_array/1000:.2f} kWp",
        }

    def reset(self):
        self._voc.setValue(41.40)
        self._vmp.setValue(34.60)
        self._isc.setValue(10.05)
        self._imp.setValue(9.50)
        self._pmax.setValue(330.0)
        self._beta_voc.setValue(-0.300)
        self._beta_vmp.setValue(-0.350)
        self._alpha_isc.setValue(0.050)
        self._t_min.setValue(-5.0)
        self._t_max.setValue(70.0)
        self._v_inv_max.setValue(1000.0)
        self._v_mppt_min.setValue(200.0)
        self._v_mppt_max.setValue(800.0)
        self._i_mppt_max.setValue(25.0)
        self._project.clear()
        self._client.clear()
        self._location.clear()
        self._prepared_by.clear()
        for card in [
            self._card_voc_cold, self._card_vmp_hot,  self._card_isc_hot,
            self._card_max_series, self._card_min_series, self._card_rec_series,
            self._card_max_par,  self._card_voc_str,  self._card_kwp,
        ]:
            card.set_value("—")
        self._warn_lbl.setVisible(False)
        self._btn_export.setEnabled(False)
        self._btn_send.setEnabled(False)
        self._inv_count.setValue(1)
        self._mppts_per_inv.setValue(4)
        self._total_panels.setValue(100)
        self._result = None
