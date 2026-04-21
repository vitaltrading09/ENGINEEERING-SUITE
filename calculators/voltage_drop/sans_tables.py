"""
sans_tables.py
--------------
Cable lookup data for Method 1 calculations.

Two data sources are available, selectable via the UI:

  1. SANS_GENERAL  — SANS 10142-1:2020 Table 6
                     General PVC/XLPE insulated cables at 70 °C, resistive component.
                     Covers Copper & Aluminium.

  2. SWA_3PH      — Manufacturer SWA (Steel Wire Armoured) 3-Phase cable data.
                     Values are impedance in Ω/km (single conductor) extracted from
                     the manufacturer's "Impedance" column.
                     Copper:    1.5 mm² → 300 mm²
                     Aluminium: 25 mm²  → 240 mm²

Storage convention:
    All values are stored as SINGLE-CONDUCTOR resistance / impedance in Ω/km.
    This is numerically equal to mV/A/m.
    The formula layer applies the correct system multiplier:
        DC / Single-Phase AC  →  × 2   (out + return)
        Three-Phase AC        →  × √3

Note on SWA Volt-Drop column:
    The manufacturer's "Volt Drop (mV/A/m)" column = √3 × Impedance (Ω/km),
    i.e. it is the pre-computed 3-phase circuit drop.
    We store the raw Impedance here so the formula layer can correctly handle
    all three system types.
"""

from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. SANS 10142-1:2020 — Table 6 (General cables)
# ─────────────────────────────────────────────────────────────────────────────
# (material, size_mm2) → single-conductor r (mV/A/m  ≡  Ω/km)  at 70 °C

_SANS_BASE: dict[tuple[str, float], float] = {
    # Copper
    ("copper",  1.0):   18.10,
    ("copper",  1.5):   12.10,
    ("copper",  2.5):    7.41,
    ("copper",  4.0):    4.61,
    ("copper",  6.0):    3.08,
    ("copper", 10.0):    1.83,
    ("copper", 16.0):    1.15,
    ("copper", 25.0):    0.727,
    ("copper", 35.0):    0.524,
    ("copper", 50.0):    0.387,
    ("copper", 70.0):    0.268,
    ("copper", 95.0):    0.193,
    ("copper",120.0):    0.153,
    ("copper",150.0):    0.124,
    ("copper",185.0):    0.0991,
    ("copper",240.0):    0.0754,
    ("copper",300.0):    0.0601,
    ("copper",400.0):    0.0470,

    # Aluminium
    ("aluminium", 16.0): 1.91,
    ("aluminium", 25.0): 1.20,
    ("aluminium", 35.0): 0.868,
    ("aluminium", 50.0): 0.641,
    ("aluminium", 70.0): 0.443,
    ("aluminium", 95.0): 0.320,
    ("aluminium",120.0): 0.253,
    ("aluminium",150.0): 0.206,
    ("aluminium",185.0): 0.164,
    ("aluminium",240.0): 0.125,
    ("aluminium",300.0): 0.100,
    ("aluminium",400.0): 0.0778,
}

SANS_COPPER_SIZES    = [1.0,1.5,2.5,4.0,6.0,10.0,16.0,25.0,35.0,50.0,70.0,
                         95.0,120.0,150.0,185.0,240.0,300.0,400.0]
SANS_ALUMINIUM_SIZES = [16.0,25.0,35.0,50.0,70.0,95.0,120.0,150.0,185.0,
                         240.0,300.0,400.0]


# ─────────────────────────────────────────────────────────────────────────────
# 2. SWA Manufacturer Data — 3-Phase Copper & Aluminium Armoured Cable
#    Source: Manufacturer datasheet "Impedance (Ω/km)" column
# ─────────────────────────────────────────────────────────────────────────────
# (material, size_mm2) → Impedance in Ω/km (single conductor)
# Manufacturer Volt Drop (mV/A/m) = √3 × [values below]  (for direct 3-phase verification)

_SWA_BASE: dict[tuple[str, float], float] = {
    # ── SWA Copper ────────────────────────────────────
    ("copper",   1.5):  14.4800,
    ("copper",   2.5):   8.8700,
    ("copper",   4.0):   5.5200,
    ("copper",   6.0):   3.6900,
    ("copper",  10.0):   2.1900,
    ("copper",  16.0):   1.3800,
    ("copper",  25.0):   0.8749,
    ("copper",  35.0):   0.6335,
    ("copper",  50.0):   0.4718,
    ("copper",  70.0):   0.3325,
    ("copper",  95.0):   0.2460,
    ("copper", 120.0):   0.2012,
    ("copper", 150.0):   0.1698,
    ("copper", 185.0):   0.1445,
    ("copper", 240.0):   0.1220,
    ("copper", 300.0):   0.1090,

    # ── SWA Aluminium ─────────────────────────────────
    ("aluminium",  25.0):  1.4446,
    ("aluminium",  35.0):  1.0465,
    ("aluminium",  50.0):  0.7749,
    ("aluminium",  70.0):  0.5388,
    ("aluminium",  95.0):  0.3934,
    ("aluminium", 120.0):  0.3148,
    ("aluminium", 150.0):  0.2607,
    ("aluminium", 185.0):  0.2133,
    ("aluminium", 240.0):  0.1708,
}

# Pre-computed 3-phase Volt Drop (mV/A/m) = √3 × Impedance
# Stored separately for display purposes only — NOT used in calculation.
import math as _math
_SWA_VD: dict[tuple[str, float], float] = {
    k: round(v * _math.sqrt(3), 4) for k, v in _SWA_BASE.items()
}

SWA_COPPER_SIZES    = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0,
                        50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0]
SWA_ALUMINIUM_SIZES = [25.0, 35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0]

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

# Cable standard keys used across the codebase
STANDARD_SANS = "SANS General"
STANDARD_SWA  = "SWA Armoured (Manufacturer)"

ALL_STANDARDS = [STANDARD_SANS, STANDARD_SWA]


def get_impedance(standard: str, material: str, size_mm2: float) -> Optional[float]:
    """
    Return single-conductor impedance in Ω/km (= mV/A/m numerically).

    Args:
        standard  : STANDARD_SANS or STANDARD_SWA
        material  : 'copper' or 'aluminium'
        size_mm2  : conductor size in mm²

    Returns:
        float or None if not in table.
    """
    key = (material.lower(), float(size_mm2))
    if standard == STANDARD_SWA:
        return _SWA_BASE.get(key)
    return _SANS_BASE.get(key)


def get_swa_vd(material: str, size_mm2: float) -> Optional[float]:
    """
    Return the manufacturer's Volt Drop column value (mV/A/m, 3-phase circuit).
    Display only — equals √3 × impedance.
    """
    return _SWA_VD.get((material.lower(), float(size_mm2)))


def get_available_sizes(standard: str, material: str) -> list[float]:
    """Return sorted list of available conductor sizes for the given standard + material."""
    mat = material.lower()
    if standard == STANDARD_SWA:
        return SWA_COPPER_SIZES if mat == "copper" else SWA_ALUMINIUM_SIZES
    return SANS_COPPER_SIZES   if mat == "copper" else SANS_ALUMINIUM_SIZES


# ── Backwards-compatible alias (used by the single-result export) ────────────
def get_mv_per_am(material: str, size_mm2: float) -> Optional[float]:
    """Legacy alias — reads from SANS general table."""
    return get_impedance(STANDARD_SANS, material, size_mm2)
