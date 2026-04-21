"""
voltage_drop_logic.py
---------------------
Pure calculation functions for voltage drop per SANS 10142-1 §6.2.7.
No Qt dependencies — easily unit-testable.
"""

import math
from typing import Optional

# Pass/Fail threshold per SANS 10142-1 §6.2.7 (5% of nominal supply voltage)
VDROP_THRESHOLD_PCT = 5.0


def calc_method1(mv_per_am: float, current_a: float, length_m: float,
                 system_type: str) -> float:
    """
    Method 1: SANS Tabulated Values (§6.2.7 formula).

    Formula:
        Vd = (mV × I × L) / 1000
    where mV is the SANS table value (base single-conductor mV/A/m).

    The system_type multiplier is applied here:
        DC / 1-phase AC : multiply base mV by 2 (out + return conductor)
        3-phase AC       : multiply base mV by √3

    Args:
        mv_per_am   : base mV/A/m from SANS table (single conductor)
        current_a   : design current in Amperes
        length_m    : one-way route length in metres
        system_type : 'dc' | '1phase' | '3phase'

    Returns:
        Voltage drop in Volts (float)
    """
    multiplier = _system_multiplier(system_type)
    effective_mv = mv_per_am * multiplier
    return (effective_mv * current_a * length_m) / 1000.0


def calc_method2(r_ohm_per_km: float, current_a: float, length_m: float,
                 system_type: str) -> float:
    """
    Method 2: Manual Impedance / Resistance entry.

    Formulas:
        DC / 1-phase AC : Vd = (2 × I × L × R) / 1000
        3-phase AC       : Vd = (√3 × I × L × R) / 1000

    where R is in Ω/km and L is in metres.

    Args:
        r_ohm_per_km : conductor resistance in Ω/km
        current_a    : design current in Amperes
        length_m     : one-way route length in metres
        system_type  : 'dc' | '1phase' | '3phase'

    Returns:
        Voltage drop in Volts (float)
    """
    multiplier = _system_multiplier(system_type)
    return (multiplier * current_a * length_m * r_ohm_per_km) / 1000.0


def vd_percent(vd_volts: float, supply_voltage: float) -> float:
    """
    Calculate voltage drop as a percentage of supply voltage.

    Args:
        vd_volts       : voltage drop in Volts
        supply_voltage : nominal supply voltage in Volts

    Returns:
        Voltage drop percentage (float)
    """
    if supply_voltage <= 0:
        return 0.0
    return (vd_volts / supply_voltage) * 100.0


def pass_fail(vd_pct: float, threshold: float = VDROP_THRESHOLD_PCT) -> bool:
    """
    Evaluate SANS 10142-1 §6.2.7 compliance.

    Returns:
        True  → PASS (vd_pct ≤ threshold)
        False → FAIL (vd_pct > threshold)
    """
    return vd_pct <= threshold


def _system_multiplier(system_type: str) -> float:
    """
    Return the appropriate circuit multiplier for the system type.
        DC         → 2  (two conductors: + and −)
        1-phase AC → 2  (two conductors: line and neutral)
        3-phase AC → √3 (line-to-line factor)
    """
    if system_type == "3phase":
        return math.sqrt(3)
    return 2.0  # dc or 1phase
