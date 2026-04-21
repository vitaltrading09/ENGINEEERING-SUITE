"""
base_calculator.py
------------------
Abstract base class all calculators must inherit from.
Defines the interface consumed by the export utility.
"""

from PyQt6.QtWidgets import QWidget
from abc import abstractmethod
from typing import Any


class BaseCalculator(QWidget):
    """
    All calculators inherit from this class.

    Required overrides:
      - get_inputs()  → dict of {label: value} for export
      - get_results() → dict of {label: value} for export
      - reset()       → restore all fields to defaults
      - calculator_name (class attr)
      - sans_reference (class attr)
    """

    calculator_name: str = "Calculator"
    sans_reference: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)

    @abstractmethod
    def get_inputs(self) -> dict[str, Any]:
        """Return a dict of input parameter names → values for the exporter."""
        ...

    @abstractmethod
    def get_results(self) -> dict[str, Any]:
        """Return a dict of result names → values for the exporter."""
        ...

    @abstractmethod
    def reset(self):
        """Reset all fields to their default state."""
        ...
