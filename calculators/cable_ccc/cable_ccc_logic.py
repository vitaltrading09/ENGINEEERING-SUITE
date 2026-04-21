"""
cable_ccc_logic.py
------------------
Current Carrying Capacity (CCC) & derating calculations.
Reference: SANS 10142-1:2020 Tables 1–5, Appendix B.

All base CCC values are taken directly from SANS 10142-1:2020 Table 1
(PVC insulated) and Table 2 (XLPE insulated), for copper and aluminium
conductors at the reference ambient temperatures.

Derating factors applied (multiplicative):
  Ca  — ambient temperature correction       (Table 3)
  Cg  — grouping / bunching correction       (Table 4)
  Ci  — installation method correction       (embedded in base values or Table 1/2)

Final CCC = Base_CCC × Ca × Cg
Cable passes if: Design current (Ib) ≤ Final CCC
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# SANS 10142-1:2020 — Table 1 & 2 Base CCC values [A]
# Key: (insulation, material, installation_method, size_mm2)
# Installation methods:
#   'A1' — enclosed in conduit in thermally insulating wall
#   'A2' — enclosed in conduit in thermally insulating wall (multi-core)
#   'B1' — enclosed in conduit on wall / in trunking
#   'B2' — enclosed in conduit on wall (multi-core)
#   'C'  — clipped direct / on wall surface
#   'D1' — in duct in ground (single-core)
#   'D2' — direct buried
#   'E'  — in free air (single-core trefoil)
#   'F'  — in free air (single-core flat)
# ─────────────────────────────────────────────────────────────────────────────

# Base CCC for PVC insulated cables (70°C conductor), SANS Table 1
# Values are for single-phase (2-conductor) or three-phase (3-conductor) as noted
_PVC_CCC: dict[tuple, float] = {
    # (material, install_method, size_mm2): Amps
    # ── Copper PVC ──────────────────────────────────────────────────────────
    ("copper", "A1", 1.0): 11, ("copper", "A1", 1.5): 13.5, ("copper", "A1", 2.5): 18,
    ("copper", "A1", 4.0): 24, ("copper", "A1", 6.0): 31,   ("copper", "A1", 10.0): 42,
    ("copper", "A1", 16.0): 56, ("copper", "A1", 25.0): 73, ("copper", "A1", 35.0): 89,
    ("copper", "A1", 50.0): 108,("copper", "A1", 70.0): 136,("copper", "A1", 95.0): 164,
    ("copper", "A1", 120.0): 188,("copper", "A1", 150.0): 216,("copper", "A1", 185.0): 245,
    ("copper", "A1", 240.0): 286,

    ("copper", "A2", 1.0): 10.5,("copper", "A2", 1.5): 13, ("copper", "A2", 2.5): 17.5,
    ("copper", "A2", 4.0): 23,  ("copper", "A2", 6.0): 29, ("copper", "A2", 10.0): 39,
    ("copper", "A2", 16.0): 52, ("copper", "A2", 25.0): 68,("copper", "A2", 35.0): 83,
    ("copper", "A2", 50.0): 99, ("copper", "A2", 70.0): 125,("copper", "A2", 95.0): 150,
    ("copper", "A2", 120.0): 172,("copper", "A2", 150.0): 196,("copper", "A2", 185.0): 223,
    ("copper", "A2", 240.0): 261,

    ("copper", "B1", 1.0): 13.5,("copper", "B1", 1.5): 16.5,("copper", "B1", 2.5): 22,
    ("copper", "B1", 4.0): 30,  ("copper", "B1", 6.0): 38,  ("copper", "B1", 10.0): 52,
    ("copper", "B1", 16.0): 69, ("copper", "B1", 25.0): 90, ("copper", "B1", 35.0): 111,
    ("copper", "B1", 50.0): 133,("copper", "B1", 70.0): 168,("copper", "B1", 95.0): 201,
    ("copper", "B1", 120.0): 232,("copper", "B1", 150.0): 258,("copper", "B1", 185.0): 294,
    ("copper", "B1", 240.0): 344,

    ("copper", "B2", 1.0): 12,  ("copper", "B2", 1.5): 15,  ("copper", "B2", 2.5): 20,
    ("copper", "B2", 4.0): 27,  ("copper", "B2", 6.0): 34,  ("copper", "B2", 10.0): 46,
    ("copper", "B2", 16.0): 62, ("copper", "B2", 25.0): 80, ("copper", "B2", 35.0): 99,
    ("copper", "B2", 50.0): 118,("copper", "B2", 70.0): 149,("copper", "B2", 95.0): 179,
    ("copper", "B2", 120.0): 206,("copper", "B2", 150.0): 225,("copper", "B2", 185.0): 259,
    ("copper", "B2", 240.0): 305,

    ("copper", "C", 1.0): 15,   ("copper", "C", 1.5): 19.5, ("copper", "C", 2.5): 27,
    ("copper", "C", 4.0): 36,   ("copper", "C", 6.0): 46,   ("copper", "C", 10.0): 63,
    ("copper", "C", 16.0): 85,  ("copper", "C", 25.0): 112, ("copper", "C", 35.0): 138,
    ("copper", "C", 50.0): 168, ("copper", "C", 70.0): 213, ("copper", "C", 95.0): 258,
    ("copper", "C", 120.0): 299,("copper", "C", 150.0): 344,("copper", "C", 185.0): 392,
    ("copper", "C", 240.0): 461,("copper", "C", 300.0): 530,

    ("copper", "E", 1.5): 22,   ("copper", "E", 2.5): 30,   ("copper", "E", 4.0): 40,
    ("copper", "E", 6.0): 51,   ("copper", "E", 10.0): 70,  ("copper", "E", 16.0): 94,
    ("copper", "E", 25.0): 119, ("copper", "E", 35.0): 148, ("copper", "E", 50.0): 180,
    ("copper", "E", 70.0): 232, ("copper", "E", 95.0): 282, ("copper", "E", 120.0): 328,
    ("copper", "E", 150.0): 379,("copper", "E", 185.0): 434,("copper", "E", 240.0): 514,
    ("copper", "E", 300.0): 593,

    # ── Aluminium PVC ────────────────────────────────────────────────────────
    ("aluminium", "A1", 16.0): 44,  ("aluminium", "A1", 25.0): 57,  ("aluminium", "A1", 35.0): 70,
    ("aluminium", "A1", 50.0): 84,  ("aluminium", "A1", 70.0): 107, ("aluminium", "A1", 95.0): 129,
    ("aluminium", "A1", 120.0): 148,("aluminium", "A1", 150.0): 169,("aluminium", "A1", 185.0): 193,
    ("aluminium", "A1", 240.0): 225,

    ("aluminium", "B1", 16.0): 53,  ("aluminium", "B1", 25.0): 70,  ("aluminium", "B1", 35.0): 86,
    ("aluminium", "B1", 50.0): 104, ("aluminium", "B1", 70.0): 131, ("aluminium", "B1", 95.0): 157,
    ("aluminium", "B1", 120.0): 181,("aluminium", "B1", 150.0): 201,("aluminium", "B1", 185.0): 230,
    ("aluminium", "B1", 240.0): 269,

    ("aluminium", "B2", 16.0): 49,  ("aluminium", "B2", 25.0): 63,  ("aluminium", "B2", 35.0): 77,
    ("aluminium", "B2", 50.0): 92,  ("aluminium", "B2", 70.0): 116, ("aluminium", "B2", 95.0): 139,
    ("aluminium", "B2", 120.0): 160,("aluminium", "B2", 150.0): 176,("aluminium", "B2", 185.0): 202,
    ("aluminium", "B2", 240.0): 238,

    ("aluminium", "C", 16.0): 66,   ("aluminium", "C", 25.0): 87,   ("aluminium", "C", 35.0): 107,
    ("aluminium", "C", 50.0): 131,  ("aluminium", "C", 70.0): 166,  ("aluminium", "C", 95.0): 201,
    ("aluminium", "C", 120.0): 233, ("aluminium", "C", 150.0): 269, ("aluminium", "C", 185.0): 306,
    ("aluminium", "C", 240.0): 361, ("aluminium", "C", 300.0): 415,

    ("aluminium", "E", 16.0): 73,   ("aluminium", "E", 25.0): 93,   ("aluminium", "E", 35.0): 115,
    ("aluminium", "E", 50.0): 141,  ("aluminium", "E", 70.0): 182,  ("aluminium", "E", 95.0): 220,
    ("aluminium", "E", 120.0): 256, ("aluminium", "E", 150.0): 296, ("aluminium", "E", 185.0): 339,
    ("aluminium", "E", 240.0): 401, ("aluminium", "E", 300.0): 461,
}

# Base CCC for XLPE insulated cables (90°C conductor), SANS Table 2
# XLPE values are approximately 20–25% higher than PVC equivalents
_XLPE_CCC: dict[tuple, float] = {
    ("copper", "A1", 1.0): 13,  ("copper", "A1", 1.5): 16.5,("copper", "A1", 2.5): 22,
    ("copper", "A1", 4.0): 30,  ("copper", "A1", 6.0): 38,  ("copper", "A1", 10.0): 52,
    ("copper", "A1", 16.0): 70, ("copper", "A1", 25.0): 91, ("copper", "A1", 35.0): 111,
    ("copper", "A1", 50.0): 133,("copper", "A1", 70.0): 168,("copper", "A1", 95.0): 201,
    ("copper", "A1", 120.0): 232,("copper", "A1", 150.0): 258,("copper", "A1", 185.0): 294,
    ("copper", "A1", 240.0): 344,

    ("copper", "B1", 1.5): 20,  ("copper", "B1", 2.5): 26,  ("copper", "B1", 4.0): 35,
    ("copper", "B1", 6.0): 45,  ("copper", "B1", 10.0): 61, ("copper", "B1", 16.0): 81,
    ("copper", "B1", 25.0): 106,("copper", "B1", 35.0): 131,("copper", "B1", 50.0): 158,
    ("copper", "B1", 70.0): 200,("copper", "B1", 95.0): 241,("copper", "B1", 120.0): 278,
    ("copper", "B1", 150.0): 318,("copper", "B1", 185.0): 362,("copper", "B1", 240.0): 424,
    ("copper", "B1", 300.0): 486,

    ("copper", "C", 1.5): 24,   ("copper", "C", 2.5): 32,   ("copper", "C", 4.0): 43,
    ("copper", "C", 6.0): 54,   ("copper", "C", 10.0): 75,  ("copper", "C", 16.0): 100,
    ("copper", "C", 25.0): 133, ("copper", "C", 35.0): 164, ("copper", "C", 50.0): 198,
    ("copper", "C", 70.0): 253, ("copper", "C", 95.0): 306, ("copper", "C", 120.0): 354,
    ("copper", "C", 150.0): 407,("copper", "C", 185.0): 464,("copper", "C", 240.0): 546,
    ("copper", "C", 300.0): 628,

    ("copper", "E", 1.5): 26,   ("copper", "E", 2.5): 36,   ("copper", "E", 4.0): 49,
    ("copper", "E", 6.0): 63,   ("copper", "E", 10.0): 86,  ("copper", "E", 16.0): 115,
    ("copper", "E", 25.0): 149, ("copper", "E", 35.0): 185, ("copper", "E", 50.0): 225,
    ("copper", "E", 70.0): 289, ("copper", "E", 95.0): 352, ("copper", "E", 120.0): 410,
    ("copper", "E", 150.0): 473,("copper", "E", 185.0): 542,("copper", "E", 240.0): 641,
    ("copper", "E", 300.0): 741,

    ("aluminium", "B1", 16.0): 63,  ("aluminium", "B1", 25.0): 83,  ("aluminium", "B1", 35.0): 102,
    ("aluminium", "B1", 50.0): 124, ("aluminium", "B1", 70.0): 156, ("aluminium", "B1", 95.0): 188,
    ("aluminium", "B1", 120.0): 216,("aluminium", "B1", 150.0): 245,("aluminium", "B1", 185.0): 279,
    ("aluminium", "B1", 240.0): 327,("aluminium", "B1", 300.0): 376,

    ("aluminium", "C", 16.0): 78,   ("aluminium", "C", 25.0): 103,  ("aluminium", "C", 35.0): 127,
    ("aluminium", "C", 50.0): 155,  ("aluminium", "C", 70.0): 196,  ("aluminium", "C", 95.0): 238,
    ("aluminium", "C", 120.0): 276, ("aluminium", "C", 150.0): 319, ("aluminium", "C", 185.0): 364,
    ("aluminium", "C", 240.0): 430, ("aluminium", "C", 300.0): 497,

    ("aluminium", "E", 16.0): 87,   ("aluminium", "E", 25.0): 114,  ("aluminium", "E", 35.0): 141,
    ("aluminium", "E", 50.0): 173,  ("aluminium", "E", 70.0): 222,  ("aluminium", "E", 95.0): 270,
    ("aluminium", "E", 120.0): 314, ("aluminium", "E", 150.0): 363, ("aluminium", "E", 185.0): 415,
    ("aluminium", "E", 240.0): 492, ("aluminium", "E", 300.0): 569,
}

# ─────────────────────────────────────────────────────────────────────────────
# SANS 10142-1 Table 3 — Ambient Temperature Correction Factors (Ca)
# Reference temperature: 30°C (PVC), 30°C (XLPE)
# ─────────────────────────────────────────────────────────────────────────────

_CA_PVC: dict[int, float] = {
    10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06,
    30: 1.00, 35: 0.94, 40: 0.87, 45: 0.79,
    50: 0.71, 55: 0.61, 60: 0.50,
}

_CA_XLPE: dict[int, float] = {
    10: 1.15, 15: 1.12, 20: 1.08, 25: 1.04,
    30: 1.00, 35: 0.96, 40: 0.91, 45: 0.87,
    50: 0.82, 55: 0.76, 60: 0.71, 65: 0.65,
    70: 0.58, 75: 0.50, 80: 0.41,
}

# ─────────────────────────────────────────────────────────────────────────────
# SANS 10142-1 Table 4 — Grouping / Bunching Correction Factors (Cg)
# Number of circuits / multi-core cables: factor
#
# Two arrangements are tabulated:
#   'touching' — cables in contact with each other (more conservative)
#   'spaced'   — cables separated by ≥ 1 cable diameter (less derating)
#
# Source: SANS 10142-1:2020 Table 4 / IEC 60364-5-52:2009 Table B.52.17
# ─────────────────────────────────────────────────────────────────────────────
_CG_TOUCHING: dict[int, float] = {
    1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65,
    5: 0.60, 6: 0.57, 7: 0.54, 8: 0.52,
    9: 0.50, 10: 0.48, 12: 0.45, 14: 0.43,
    16: 0.41, 20: 0.38,
}

# Cables spaced ≥ 1 cable diameter apart — less mutual heating, higher Cg
_CG_SPACED: dict[int, float] = {
    1: 1.00, 2: 0.90, 3: 0.82, 4: 0.77,
    5: 0.75, 6: 0.73, 7: 0.68, 8: 0.65,
    9: 0.63, 10: 0.61, 12: 0.57, 14: 0.54,
    16: 0.52, 20: 0.49,
}

# Keep backward-compatible alias (touching is the default)
_CG = _CG_TOUCHING

# ─────────────────────────────────────────────────────────────────────────────
# Installation method descriptions (for UI display)
# ─────────────────────────────────────────────────────────────────────────────
INSTALL_METHODS = {
    "A1": "A1 — Single-core in conduit in insulating wall",
    "A2": "A2 — Multi-core in conduit in insulating wall",
    "B1": "B1 — Single-core in conduit on wall / in trunking",
    "B2": "B2 — Multi-core in conduit on wall",
    "C":  "C  — Clipped direct to wall / surface",
    "E":  "E  — Free air (perforated cable tray / ladder)",
}

INSTALL_METHOD_KEYS = list(INSTALL_METHODS.keys())

COPPER_SIZES = [1.0, 1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0,
                70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0]
ALUMINIUM_SIZES = [16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0]

AMBIENT_TEMPS = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
AMBIENT_TEMPS_XLPE = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
GROUP_COUNTS = sorted(_CG_TOUCHING.keys())

CABLE_ARRANGEMENTS = {
    "touching": "Touching — cables in contact (SANS Table 4, conservative)",
    "spaced":   "Spaced — ≥ 1 cable diameter gap (SANS Table 4, less derating)",
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CCCResult:
    """Full result set for a CCC calculation."""
    insulation: str          # 'PVC' or 'XLPE'
    material: str            # 'copper' or 'aluminium'
    install_method: str      # e.g. 'C'
    size_mm2: float
    ambient_temp: int        # °C
    num_circuits: int
    arrangement: str         # 'touching' or 'spaced'

    base_ccc: float          # A — from SANS table
    ca: float                # ambient correction factor
    cg: float                # grouping correction factor
    derated_ccc: float       # A — final after all derating
    design_current: float    # A — user's Ib

    passed: bool             # Ib ≤ derated_ccc
    utilisation_pct: float   # (Ib / derated_ccc) × 100


def get_base_ccc(insulation: str, material: str,
                 install_method: str, size_mm2: float) -> Optional[float]:
    """Look up base CCC from SANS tables."""
    key = (material.lower(), install_method.upper(), float(size_mm2))
    if insulation.upper() == "XLPE":
        return _XLPE_CCC.get(key)
    return _PVC_CCC.get(key)


def get_ca(insulation: str, ambient_temp: int) -> float:
    """Return ambient temperature correction factor."""
    table = _CA_XLPE if insulation.upper() == "XLPE" else _CA_PVC
    # Find nearest temperature
    temps = sorted(table.keys())
    closest = min(temps, key=lambda t: abs(t - ambient_temp))
    return table[closest]


def get_cg(num_circuits: int, arrangement: str = "touching") -> float:
    """Return grouping correction factor for given number of circuits and arrangement.

    Args:
        num_circuits: number of circuits/cables in the group.
        arrangement:  'touching' (cables in contact) or 'spaced' (≥ 1 cable diameter gap).
    """
    table = _CG_SPACED if arrangement == "spaced" else _CG_TOUCHING
    counts = sorted(table.keys())
    if num_circuits <= 1:
        return 1.0
    if num_circuits >= counts[-1]:
        return table[counts[-1]]
    closest = min(counts, key=lambda c: abs(c - num_circuits))
    return table[closest]


def calc_ccc(
    insulation: str,
    material: str,
    install_method: str,
    size_mm2: float,
    ambient_temp: int,
    num_circuits: int,
    design_current: float,
    arrangement: str = "touching",
) -> Optional[CCCResult]:
    """
    Compute derated CCC and compliance check.

    Args:
        arrangement: 'touching' or 'spaced' (cables separated by ≥ 1 cable diameter).

    Returns:
        CCCResult or None if lookup fails.
    """
    base = get_base_ccc(insulation, material, install_method, size_mm2)
    if base is None:
        return None

    ca = get_ca(insulation, ambient_temp)
    cg = get_cg(num_circuits, arrangement)
    derated = round(base * ca * cg, 2)
    util = round((design_current / derated * 100) if derated > 0 else 0, 1)

    return CCCResult(
        insulation=insulation.upper(),
        material=material.capitalize(),
        install_method=install_method.upper(),
        size_mm2=size_mm2,
        ambient_temp=ambient_temp,
        num_circuits=num_circuits,
        arrangement=arrangement,
        base_ccc=base,
        ca=ca,
        cg=cg,
        derated_ccc=derated,
        design_current=design_current,
        passed=design_current <= derated,
        utilisation_pct=util,
    )


def suggest_minimum_size(
    insulation: str,
    material: str,
    install_method: str,
    ambient_temp: int,
    num_circuits: int,
    design_current: float,
    arrangement: str = "touching",
) -> Optional[float]:
    """
    Return the smallest cable size that passes for the given conditions.
    Returns None if even the largest size fails.
    """
    sizes = COPPER_SIZES if material.lower() == "copper" else ALUMINIUM_SIZES
    for size in sizes:
        result = calc_ccc(insulation, material, install_method, size,
                          ambient_temp, num_circuits, design_current, arrangement)
        if result and result.passed:
            return size
    return None
