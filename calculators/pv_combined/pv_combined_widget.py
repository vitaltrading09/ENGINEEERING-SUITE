"""
pv_combined_widget.py
---------------------
Single sidebar entry that hosts both PV tools in two sub-tabs:

  Tab 0 — "String Sizing"        (PVStringWidget in a scroll area)
  Tab 1 — "Layout & Stringing"   (PVLayoutWidget, full-screen canvas)

"Send to Layout →" in the String Sizing tab pre-fills the Layout tab's
inverter table, panels-per-string, and stores the panel Wp for the
future string-count optimiser.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QVBoxLayout, QTabWidget, QScrollArea, QWidget, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
import qtawesome as qta

from calculators.base_calculator import BaseCalculator
from calculators.pv_stringing.pv_stringing_widget import PVStringWidget
from calculators.pv_layout.pv_layout_widget import PVLayoutWidget


_TAB_STYLE = """
QTabWidget::pane {
    border: 1px solid #30363d;
    background: #0d1117;
}
QTabBar::tab {
    background: #161b22;
    color: #8b949e;
    padding: 9px 22px;
    border: 1px solid #30363d;
    border-bottom: none;
    font-size: 12px;
    min-width: 160px;
}
QTabBar::tab:selected {
    background: #1f3a5f;
    color: #58a6ff;
    border-top: 2px solid #58a6ff;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background: #21262d;
    color: #e6edf3;
}
"""


class PVSystemWidget(BaseCalculator):
    """
    Combined PV System Design tool.
    Hosts String Sizing and Layout & Stringing in two sub-tabs.
    """
    calculator_name      = "PV System Design"
    sans_reference       = "IEC 62548  •  IEC 61215  •  Solareff Engineering"
    prefer_maximized     = True   # needed by the Layout tab
    tab_subtitle_changed = pyqtSignal(str)  # emits sub-tab name on switch

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(_TAB_STYLE)
        self._tabs.setDocumentMode(True)

        # ── Tab 0: String Sizing ──────────────────────────────────────────────
        self._str_widget = PVStringWidget()

        str_scroll = QScrollArea()
        str_scroll.setWidgetResizable(True)
        str_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        str_scroll.setStyleSheet("QScrollArea { border: none; background: #0d1117; }")
        str_scroll.setWidget(self._str_widget)

        self._tabs.addTab(
            str_scroll,
            qta.icon("fa5s.calculator", color="#8b949e"),
            "  String Sizing  ",
        )

        # ── Tab 1: Layout & Stringing ─────────────────────────────────────────
        self._layout_widget = PVLayoutWidget()

        self._tabs.addTab(
            self._layout_widget,
            qta.icon("fa5s.solar-panel", color="#8b949e"),
            "  Layout & Stringing  ",
        )

        root.addWidget(self._tabs)

        # ── Connect "Send to Layout" signal ───────────────────────────────────
        self._str_widget.sig_send_to_layout.connect(self._on_send_to_layout)

        # ── Emit subtitle when sub-tab switches ───────────────────────────────
        self._tabs.currentChanged.connect(self._on_subtab_changed)

    # ─────────────────────────────────────────────────────────────────────────
    # Sub-tab subtitle tracking
    # ─────────────────────────────────────────────────────────────────────────

    _SUBTAB_SUBTITLES = ["String Sizing", "Layout & Stringing"]

    def _on_subtab_changed(self, idx: int):
        """Emit the name of the newly active sub-tab for the header bar."""
        if 0 <= idx < len(self._SUBTAB_SUBTITLES):
            self.tab_subtitle_changed.emit(self._SUBTAB_SUBTITLES[idx])

    # ─────────────────────────────────────────────────────────────────────────
    # Cross-tab data transfer
    # ─────────────────────────────────────────────────────────────────────────

    def _on_send_to_layout(self, config: dict):
        """
        Pre-fill the Layout tab's inverter table, panels-per-string spinbox,
        and store panel Wp for future optimiser use.

        config keys (all optional with sensible fallbacks):
            inverter_count    int
            mppts_per_inverter int
            strings_per_mppt  int
            panels_per_string int
            panel_wp          float
            total_panels      int
        """
        lw = self._layout_widget

        inv_count  = int(config.get("inverter_count",    1))
        mppts      = int(config.get("mppts_per_inverter", 4))
        str_mppt   = int(config.get("strings_per_mppt",   2))
        pps        = int(config.get("panels_per_string",  lw._panels_per_str.value()))

        # Pre-fill panels per string
        lw._panels_per_str.setValue(pps)

        # Rebuild the inverter table
        lw._inv_table.setRowCount(0)
        for i in range(inv_count):
            lw._add_inverter_row(i + 1, mppts, str_mppt)

        # Store panel Wp on the layout widget for future optimiser
        lw._panel_wp = config.get("panel_wp", 0.0)

        # Update status label
        lw._status_lbl.setText(
            f"Pre-filled from String Sizing:  "
            f"{inv_count} inverter(s)  |  {mppts} MPPTs each  |  "
            f"{str_mppt} str/MPPT  |  {pps} panels/string"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # BaseCalculator interface — delegate to active tab
    # ─────────────────────────────────────────────────────────────────────────

    def get_inputs(self) -> dict:
        idx = self._tabs.currentIndex()
        if idx == 0:
            return self._str_widget.get_inputs()
        return self._layout_widget.get_inputs()

    def get_results(self) -> dict:
        idx = self._tabs.currentIndex()
        if idx == 0:
            return self._str_widget.get_results()
        return self._layout_widget.get_results()

    def reset(self):
        self._str_widget.reset()
        self._layout_widget.reset()
