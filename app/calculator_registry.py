"""
calculator_registry.py — Central registry of all sidebar panels.
To add: 1) create widget, 2) import here, 3) add dict entry.
scrollable=False means no QScrollArea wrapper.
category = sidebar section heading shown above this entry.
"""

from calculators.voltage_drop.voltage_drop_widget import VoltageDropWidget
from calculators.pv_combined.pv_combined_widget import PVSystemWidget
from calculators.cable_ccc.cable_ccc_widget import CableCCCWidget
from calculators.short_circuit.short_circuit_widget import ShortCircuitWidget
from calculators.gland_size.gland_size_widget import GlandSizeWidget
from calculators.screen_report.screen_report_widget import ScreenReportWidget
from datasheet_library.library_widget import DatasheetLibraryWidget
from guides.guides_widget import GuidesWidget

CALCULATORS = [
    {
        "name":         "Voltage Drop",
        "subtitle":     "SANS 10142-1 §6.2.7  •  Balanced & Unbalanced",
        "icon":         "fa5s.bolt",
        "widget_class": VoltageDropWidget,
        "scrollable":   True,
        "category":     "CALCULATORS",
    },
    {
        "name":         "Cable CCC & Derating",
        "subtitle":     "SANS 10142-1 Tables 1–4  •  Ambient Temp & Grouping",
        "icon":         "fa5s.plug",
        "widget_class": CableCCCWidget,
        "scrollable":   True,
        "category":     "",
    },
    {
        "name":         "Short Circuit Current",
        "subtitle":     "SANS 10142-1 §5  •  IEC 60909  •  Grid + Trafo + Cable",
        "icon":         "fa5s.exclamation-triangle",
        "widget_class": ShortCircuitWidget,
        "scrollable":   True,
        "category":     "",
    },
    {
        "name":         "Gland Size & BOQ",
        "subtitle":     "CCG BW (SWA)  •  CCG A2 (H07RN-F)  •  Lugs  •  BOQ",
        "icon":         "fa5s.wrench",
        "widget_class": GlandSizeWidget,
        "scrollable":   True,
        "category":     "",
    },
    {
        "name":         "PV System Design",
        "subtitle":     "String Sizing  •  DXF Layout  •  Auto-stringing  •  Excel export",
        "icon":         "fa5s.solar-panel",
        "widget_class": PVSystemWidget,
        "scrollable":   False,   # handles scrolling internally per tab
        "category":     "",
    },
    {
        "name":         "Screen Report Builder",
        "subtitle":     "Capture screens  •  Add captions  •  Export PDF / Word",
        "icon":         "fa5s.camera",
        "widget_class": ScreenReportWidget,
        "scrollable":   False,   # handles scrolling internally per tab
        "category":     "TOOLS",
    },
    {
        "name":         "Datasheet Library",
        "subtitle":     "Documents & Catalogues",
        "icon":         "fa5s.book-open",
        "widget_class": DatasheetLibraryWidget,
        "scrollable":   False,
        "category":     "RESOURCES",
    },
    {
        "name":         "Engineering Guides",
        "subtitle":     "SOPs & Industry Guidelines",
        "icon":         "fa5s.chalkboard-teacher",
        "widget_class": GuidesWidget,
        "scrollable":   False,
        "category":     "",
    },
]
