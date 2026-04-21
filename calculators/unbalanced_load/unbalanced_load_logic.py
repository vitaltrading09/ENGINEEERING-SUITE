"""
unbalanced_load_logic.py
------------------------
Pure-Python calculation engine for unbalanced three-phase, four-wire (3P+N) systems.

Theory:
    In an unbalanced 3-phase system each phase carries a different load current.
    The phase currents are displaced by 120° relative to their respective phase
    voltages. With a common neutral the residual neutral current is the phasor
    (vector) sum of all three phase currents.

    Per SANS 10142-1 the voltage drop for each phase is calculated separately,
    treating each phase as a single-phase circuit from line to neutral:

        Vd_phase  = R_phase  × I_phase × L / 1000   [V, single conductor, Ω/km, A, m]
        Vd_neutral = R_neutral × I_neutral × L / 1000 [V]
        Vd_total_A = Vd_A  + Vd_N     (voltage seen by load on phase A)
        Vd_%       = Vd_total / Vnom_LN × 100

    Pass criterion: SANS 10142-1 §6.2.7 → total Vd% ≤ 5 % of Vn (line-to-neutral).

Phasor convention (with configurable per-phase power factors):
    IA = IA_mag ∠ φA,      φA = arccos(pfA)  lagging
    IB = IB_mag ∠ (−120° + φB)
    IC = IC_mag ∠ (+120° + φC)
    IN = IA + IB + IC  (complex phasor sum)
"""

from __future__ import annotations
import cmath
import math
from dataclasses import dataclass

# SANS 10142-1 §6.2.7 — max voltage drop (% of nominal)
VD_LIMIT_PCT = 5.0


@dataclass
class PhaseResult:
    """Results for a single phase."""
    name: str          # "A", "B", "C"
    current_a: float   # magnitude [A]
    pf: float          # power factor (lagging)
    r_ohm_per_km: float
    vd_phase_v: float  # phase conductor drop
    vd_total_v: float  # phase + neutral share
    vd_pct: float      # vd_total / Vnom_LN × 100
    passed: bool       # ≤ VD_LIMIT_PCT


@dataclass
class UnbalancedResult:
    """Complete result set for an unbalanced 3-phase load."""
    system_voltage_ll: float    # line-to-line [V]
    vnom_ln: float              # = Vll / √3
    length_m: float
    r_phase_ohm_per_km: float   # conductor R (assumed same all phases unless overridden)
    r_neutral_ohm_per_km: float

    ia: float; ib: float; ic: float          # magnitudes [A]
    pfa: float; pfb: float; pfc: float       # power factors

    # Phasor neutral current
    neutral_current_a: float   # magnitude
    neutral_angle_deg: float   # angle

    # Per-phase results
    phase_a: PhaseResult
    phase_b: PhaseResult
    phase_c: PhaseResult

    # Neutral conductor drop
    vd_neutral_v: float

    # Worst-case phase
    worst_phase: str
    worst_vd_pct: float
    all_pass: bool


def compute_unbalanced(
    voltage_ll: float,
    length_m:   float,
    ia: float, ib: float, ic: float,
    pfa: float = 1.0, pfb: float = 1.0, pfc: float = 1.0,
    r_phase_ohm_per_km: float = 1.15,
    r_neutral_ohm_per_km: float | None = None,
) -> UnbalancedResult:
    """
    Compute unbalanced three-phase voltage drop.

    Args:
        voltage_ll          : Line-to-line supply voltage [V]
        length_m            : One-way route length [m]
        ia, ib, ic          : Phase current magnitudes [A]
        pfa, pfb, pfc       : Power factors per phase (lagging, 0 < pf ≤ 1)
        r_phase_ohm_per_km  : Phase conductor resistance [Ω/km]
        r_neutral_ohm_per_km: Neutral conductor resistance [Ω/km].
                              Defaults to same as phase conductor.

    Returns:
        UnbalancedResult
    """
    if r_neutral_ohm_per_km is None:
        r_neutral_ohm_per_km = r_phase_ohm_per_km

    vnom_ln = voltage_ll / math.sqrt(3)

    # ── Phase angle references (lagging pf = positive angle lag) ──────────
    def _lag(pf: float) -> float:
        """Lagging angle in radians for given power factor."""
        return -math.acos(max(-1.0, min(1.0, pf)))

    # Phase reference angles (voltage angles): 0°, −120°, +120°
    theta_a = _lag(pfa)
    theta_b = math.radians(-120.0) + _lag(pfb)
    theta_c = math.radians(+120.0) + _lag(pfc)

    # Phasor currents
    Ia = cmath.rect(ia, theta_a)
    Ib = cmath.rect(ib, theta_b)
    Ic = cmath.rect(ic, theta_c)

    # Neutral current (phasor sum)
    In = Ia + Ib + Ic
    in_mag   = abs(In)
    in_angle = math.degrees(cmath.phase(In))

    # ── Voltage drops ──────────────────────────────────────────────────────
    def _vd_phase(i_mag: float, r: float) -> float:
        """Phase conductor voltage drop magnitude [V].
        Single conductor, one-way: Vd = I × R × L / 1000"""
        return i_mag * r * length_m / 1000.0

    def _vd_neutral() -> float:
        return in_mag * r_neutral_ohm_per_km * length_m / 1000.0

    vd_n = _vd_neutral()

    # Per-phase total voltage drop = phase drop + neutral drop
    # (neutral carries the unbalance, so each phase load path includes
    # its share of the neutral conductor drop)
    def _pct(vd: float) -> float:
        return (vd / vnom_ln * 100.0) if vnom_ln > 0 else 0.0

    def _build_phase(name, i_mag, pf, r_ph):
        vd_ph  = _vd_phase(i_mag, r_ph)
        vd_tot = vd_ph + vd_n
        pct    = _pct(vd_tot)
        return PhaseResult(
            name=name, current_a=i_mag, pf=pf,
            r_ohm_per_km=r_ph,
            vd_phase_v=round(vd_ph, 4),
            vd_total_v=round(vd_tot, 4),
            vd_pct=round(pct, 3),
            passed=pct <= VD_LIMIT_PCT,
        )

    pa = _build_phase("A", ia,  pfa, r_phase_ohm_per_km)
    pb = _build_phase("B", ib,  pfb, r_phase_ohm_per_km)
    pc = _build_phase("C", ic,  pfc, r_phase_ohm_per_km)

    phases = [pa, pb, pc]
    worst  = max(phases, key=lambda p: p.vd_pct)

    return UnbalancedResult(
        system_voltage_ll=voltage_ll,
        vnom_ln=round(vnom_ln, 3),
        length_m=length_m,
        r_phase_ohm_per_km=r_phase_ohm_per_km,
        r_neutral_ohm_per_km=r_neutral_ohm_per_km,
        ia=ia, ib=ib, ic=ic,
        pfa=pfa, pfb=pfb, pfc=pfc,
        neutral_current_a=round(in_mag, 4),
        neutral_angle_deg=round(in_angle, 2),
        phase_a=pa, phase_b=pb, phase_c=pc,
        vd_neutral_v=round(vd_n, 4),
        worst_phase=worst.name,
        worst_vd_pct=worst.vd_pct,
        all_pass=all(p.passed for p in phases),
    )
