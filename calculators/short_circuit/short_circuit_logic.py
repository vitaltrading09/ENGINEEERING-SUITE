"""
short_circuit_logic.py
----------------------
Prospective Short Circuit Current (Isc) calculations.
Reference: SANS 10142-1:2020 §5 / IEC 60909 (simplified method for LV systems).

Method:
    For LV systems, the simplified IEC 60909 method is used:

        Isc = (c × Vn) / (√3 × Ztotal)    [Three-phase fault, L-L-L]
        Isc = (c × Vn/√3) / Ztotal        [Single-phase fault, L-N, assumes Zn = Zph]

    where:
        c   = voltage factor (1.05 for max Isc / 0.95 for min Isc, IEC 60909 Table 1)
        Vn  = nominal line-to-line voltage [V]
        Z   = total impedance of supply + transformer + cable to fault point [Ω]

    Transformer impedance:
        Ztrafo = (Vk% / 100) × (Vn² / Sn)   [Ω, referred to LV side]

    Cable impedance (resistive only for LV, reactance neglected):
        Zcable = 2 × R × L / 1000           [both conductors: phase + return]

    Supply (grid) impedance at PCC:
        Zgrid = Vn² / (Fault_Level_MVA × 10⁶)

Fault types:
    - Three-phase symmetrical (L-L-L)  — produces maximum fault current
    - Single-phase to neutral (L-N)    — simplified (assumes Zn = Zph)
    - Line-to-line (L-L)               — = (√3/2) × Isc_3ph

Protection check:
    Breaking capacity (Icu) of OCPD ≥ Prospective Isc
    Per SANS 10142-1 §5.3: Device must be rated for the available fault current.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


# Voltage factor per IEC 60909 / SANS
C_MAX = 1.05   # for maximum fault current (equipment rating check)
C_MIN = 0.95   # for minimum fault current (protection sensitivity check)

SQRT3 = math.sqrt(3)


# ─────────────────────────────────────────────────────────────────────────────
# Cable resistance database
# Sourced from: Aberdare Low Voltage Armoured Cables datasheet (SANS 1507-3)
# Values are conductor DC resistance at 70°C [Ω/km] — phase conductor only.
# For short circuit calculations use Z_cable = 2 × R × L/1000 (phase + return).
# ─────────────────────────────────────────────────────────────────────────────

CABLE_DATABASE: dict[str, dict] = {
    "Manual Entry": {
        "description": "Enter resistance manually",
        "source": "",
        "sizes": {},  # empty — user types value directly
    },
    "Aberdare SWA Cu 3c/4c  (SANS 1507-3, 600/1000V)": {
        "description": "PVC/SWA/PVC Copper, 3 & 4 core, 600/1000 V",
        "source": "Aberdare datasheet — aberdare-low-voltage-cables-section.pdf",
        "conductor": "copper",
        "sizes": {
            1.5:  14.480,
            2.5:   8.870,
            4.0:   5.520,
            6.0:   3.690,
           10.0:   2.190,
           16.0:   1.380,
           25.0:   0.8749,
           35.0:   0.6335,
           50.0:   0.4718,
           70.0:   0.3325,
           95.0:   0.2460,
          120.0:   0.2012,
          150.0:   0.1698,
          185.0:   0.1445,
          240.0:   0.1220,
          300.0:   0.1090,
        },
    },
    "Aberdare SWA Al 3c/4c  (SANS 1507-3, 600/1000V)": {
        "description": "PVC/SWA/PVC Aluminium, 3 & 4 core, 600/1000 V",
        "source": "Aberdare datasheet — aberdare-low-voltage-cables-section.pdf",
        "conductor": "aluminium",
        "sizes": {
           25.0:   1.4446,
           35.0:   1.0465,
           50.0:   0.7749,
           70.0:   0.5388,
           95.0:   0.3934,
          120.0:   0.3148,
          150.0:   0.2607,
          185.0:   0.2133,
          240.0:   0.1708,
        },
    },
    "Aberdare AWA Cu Single Core  (SANS 1507-3, 600/1000V)": {
        "description": "PVC/AWA/PVC Copper, single core, 600/1000 V",
        "source": "Aberdare datasheet — aberdare-low-voltage-cables-section.pdf",
        "conductor": "copper",
        "sizes": {
           25.0:   0.879,
           35.0:   0.639,
           50.0:   0.479,
           70.0:   0.339,
           95.0:   0.257,
          120.0:   0.213,
          150.0:   0.182,
          185.0:   0.157,
          240.0:   0.134,
          300.0:   0.123,
          400.0:   0.113,
          500.0:   0.106,
          630.0:   0.099,
        },
    },
}


@dataclass
class ShortCircuitResult:
    """Results for a short circuit calculation — includes all intermediate values
    needed to generate a full step-by-step calculation report."""

    # ── Flags ─────────────────────────────────────────────────────────────────
    include_grid:  bool
    include_trafo: bool
    include_cable: bool

    # ── Inputs ────────────────────────────────────────────────────────────────
    system_voltage_v:    float
    fault_level_mva:     float
    trafo_kva:           float
    trafo_vk_pct:        float
    cable_r_ohm_per_km:  float
    cable_length_m:      float
    breaker_icu_ka:      float
    cable_type_label:    str = ""   # e.g. "Aberdare SWA Cu 3c/4c …"
    cable_size_mm2:      float = 0.0
    num_parallel_cables: int   = 1

    # ── Impedances [Ω] (stored in mΩ for display convenience) ─────────────────
    z_grid_mohm:  float = 0.0
    z_trafo_mohm: float = 0.0
    z_cable_mohm: float = 0.0
    z_total_mohm: float = 0.0

    # ── Fault currents [kA] ───────────────────────────────────────────────────
    isc_3ph_max_ka: float = 0.0   # c = 1.05
    isc_3ph_min_ka: float = 0.0   # c = 0.95
    isc_ll_ka:      float = 0.0   # Line-to-line
    isc_ln_ka:      float = 0.0   # Line-to-neutral

    # ── Protection ────────────────────────────────────────────────────────────
    breaker_adequate: bool = False

    # ── Intermediate values (for detailed workings display) ───────────────────
    vn_sq:           float = 0.0  # Vn²
    z_grid_ohm:      float = 0.0
    z_trafo_ohm:     float = 0.0
    z_cable_ohm:     float = 0.0
    z_total_ohm:     float = 0.0
    sn_va:           float = 0.0  # Transformer VA
    trafo_ratio:     float = 0.0  # Vk%/100
    trafo_vn_sq_sn:  float = 0.0  # Vn²/Sn
    cable_r_one_way: float = 0.0  # R × L/1000 one conductor [Ω]
    isc_3ph_max_a:   float = 0.0  # in Amps
    isc_3ph_min_a:   float = 0.0
    isc_ll_a:        float = 0.0
    isc_ln_a:        float = 0.0


def calc_short_circuit(
    system_voltage_v:   float,
    fault_level_mva:    float,
    trafo_kva:          float,
    trafo_vk_pct:       float,
    cable_r_ohm_per_km: float,
    cable_length_m:     float,
    breaker_icu_ka:     float,
    include_trafo:      bool  = True,
    include_grid:       bool  = True,
    include_cable:      bool  = True,
    cable_type_label:    str   = "",
    cable_size_mm2:      float = 0.0,
    num_parallel_cables: int   = 1,
) -> ShortCircuitResult:
    """
    Calculate prospective short circuit current at end of cable run.

    Args:
        system_voltage_v    : Nominal line-to-line voltage [V]
        fault_level_mva     : Grid fault level at PCC [MVA]
        trafo_kva           : Transformer rating [kVA]
        trafo_vk_pct        : Transformer short circuit voltage [%]
        cable_r_ohm_per_km  : Cable resistance [Ω/km] (single conductor)
        cable_length_m      : One-way cable length [m]
        breaker_icu_ka      : Breaker/fuse breaking capacity [kA]
        include_grid/trafo/cable: Toggle impedance contributions
        cable_type_label    : Label string for report (e.g. cable database key)
        cable_size_mm2      : Cable size in mm² (for report display)
    """
    vn    = system_voltage_v
    vn_sq = vn ** 2

    # ── Grid source impedance ─────────────────────────────────────────────────
    if include_grid and fault_level_mva > 0:
        z_grid = vn_sq / (fault_level_mva * 1e6)
    else:
        z_grid = 0.0

    # ── Transformer impedance (referred to LV side) ───────────────────────────
    sn_va        = trafo_kva * 1000.0
    trafo_ratio  = trafo_vk_pct / 100.0
    trafo_vn2_sn = vn_sq / sn_va if sn_va > 0 else 0.0
    if include_trafo and trafo_kva > 0 and trafo_vk_pct > 0:
        z_trafo = trafo_ratio * trafo_vn2_sn
    else:
        z_trafo = 0.0

    # ── Cable impedance (resistive only, both conductors) ─────────────────────
    # Z_cable = 2 × R × L/1000 / N  (phase+return, divided by parallel cables)
    n_par = max(1, num_parallel_cables)
    cable_r_one_way = cable_r_ohm_per_km * cable_length_m / 1000.0
    if include_cable and cable_r_ohm_per_km > 0 and cable_length_m > 0:
        z_cable = 2.0 * cable_r_one_way / n_par
    else:
        z_cable = 0.0

    # ── Total impedance ───────────────────────────────────────────────────────
    z_total = z_grid + z_trafo + z_cable
    if z_total <= 0:
        z_total = 1e-9  # prevent division by zero

    # ── Fault currents ────────────────────────────────────────────────────────
    isc_3ph_max = (C_MAX * vn) / (SQRT3 * z_total)
    isc_3ph_min = (C_MIN * vn) / (SQRT3 * z_total)
    isc_ll      = (SQRT3 / 2.0) * isc_3ph_max
    isc_ln      = (C_MAX * vn / SQRT3) / z_total  # simplified, Zn = Zph assumed

    def _ka(i: float) -> float:
        return round(i / 1000.0, 3)

    return ShortCircuitResult(
        include_grid=include_grid,
        include_trafo=include_trafo,
        include_cable=include_cable,

        system_voltage_v=vn,
        fault_level_mva=fault_level_mva,
        trafo_kva=trafo_kva,
        trafo_vk_pct=trafo_vk_pct,
        cable_r_ohm_per_km=cable_r_ohm_per_km,
        cable_length_m=cable_length_m,
        breaker_icu_ka=breaker_icu_ka,
        cable_type_label=cable_type_label,
        cable_size_mm2=cable_size_mm2,
        num_parallel_cables=n_par,

        z_grid_mohm=round(z_grid * 1000, 4),
        z_trafo_mohm=round(z_trafo * 1000, 4),
        z_cable_mohm=round(z_cable * 1000, 4),
        z_total_mohm=round(z_total * 1000, 4),

        isc_3ph_max_ka=_ka(isc_3ph_max),
        isc_3ph_min_ka=_ka(isc_3ph_min),
        isc_ll_ka=_ka(isc_ll),
        isc_ln_ka=_ka(isc_ln),

        breaker_adequate=(breaker_icu_ka >= _ka(isc_3ph_max)),

        # Intermediate (for detailed report)
        vn_sq=vn_sq,
        z_grid_ohm=round(z_grid, 6),
        z_trafo_ohm=round(z_trafo, 6),
        z_cable_ohm=round(z_cable, 6),
        z_total_ohm=round(z_total, 6),
        sn_va=sn_va,
        trafo_ratio=trafo_ratio,
        trafo_vn_sq_sn=round(trafo_vn2_sn, 6),
        cable_r_one_way=round(cable_r_one_way, 6),
        isc_3ph_max_a=round(isc_3ph_max, 1),
        isc_3ph_min_a=round(isc_3ph_min, 1),
        isc_ll_a=round(isc_ll, 1),
        isc_ln_a=round(isc_ln, 1),
    )


def build_detailed_workings(r: ShortCircuitResult) -> str:
    """
    Generate a full step-by-step calculation narrative from a ShortCircuitResult.
    Shows formula → substitution → result for every step, so the engineer can
    follow and verify the calculation manually.
    """
    vn   = r.system_voltage_v
    sqrt3_str = f"{SQRT3:.4f}"
    lines: list[str] = []

    def h(txt: str):
        lines.append(f"\n{'─' * 60}")
        lines.append(f"  {txt}")
        lines.append(f"{'─' * 60}")

    def sub(label: str, val: str):
        lines.append(f"    {label:<28s} {val}")

    def eq(label: str, val: str):
        lines.append(f"    {label:<28s} = {val}")

    lines.append("PROSPECTIVE SHORT CIRCUIT CURRENT — STEP-BY-STEP WORKINGS")
    lines.append(f"Reference: SANS 10142-1:2020 §5 / IEC 60909 (simplified LV method)")
    lines.append(f"Date calculated: see report header")

    # ──────────────────────────────────────────────────────────────────────────
    h("SYSTEM PARAMETERS")
    eq("System Voltage (Vn)", f"{vn:.0f} V  (nominal line-to-line)")
    eq("Vn²", f"{vn:.0f}² = {r.vn_sq:,.0f} V²")

    step = 1

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Grid Source Impedance (Z_grid)")
    step += 1
    if r.include_grid:
        lines.append(
            "\n    The utility provides a fault level (MVA) at the Point of Common\n"
            "    Coupling (PCC). We convert this to an equivalent source impedance:\n"
        )
        lines.append("    Formula:")
        lines.append("        Z_grid  =  Vn²  ÷  (Fault_MVA × 10⁶)")
        lines.append("\n    Derivation:")
        lines.append("        Isc_grid = Fault_MVA × 10⁶  ÷  (√3 × Vn)   [fault current from MVA]")
        lines.append("        Z_grid   = Vn  ÷  (√3 × Isc_grid)           [Thévenin impedance]")
        lines.append("                 = Vn  ÷  (√3 × Fault_MVA × 10⁶ / (√3 × Vn))")
        lines.append("                 = Vn²  ÷  (Fault_MVA × 10⁶)        [simplified]")
        lines.append("\n    Values:")
        sub("Vn²", f"{r.vn_sq:,.0f} V²")
        sub("Fault Level (utility PCC)", f"{r.fault_level_mva:.1f} MVA  =  {r.fault_level_mva * 1e6:,.0f} VA")
        lines.append("\n    Calculation:")
        lines.append(f"        Z_grid  =  {r.vn_sq:,.0f}  ÷  ({r.fault_level_mva:.1f} × 1,000,000)")
        lines.append(f"                =  {r.vn_sq:,.0f}  ÷  {r.fault_level_mva * 1e6:,.0f}")
        lines.append(f"                =  {r.z_grid_ohm:.6f} Ω")
        lines.append(f"                =  {r.z_grid_mohm:.4f} mΩ  ✓")
    else:
        lines.append("\n    Grid source impedance EXCLUDED from this calculation.")
        lines.append("    Z_grid = 0.000 mΩ")
        lines.append("    (Use this when the calculation starts at the LV busbar of a transformer,")
        lines.append("     and the grid impedance has already been absorbed into Vk%.)")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Transformer Impedance (Z_trafo)")
    step += 1
    if r.include_trafo:
        lines.append(
            "\n    The transformer's short-circuit voltage percentage (Vk%) tells us\n"
            "    what fraction of rated voltage would be needed to drive rated current\n"
            "    through a short circuit on the LV side. This is converted to ohms:\n"
        )
        lines.append("    Formula:")
        lines.append("        Z_trafo  =  (Vk% ÷ 100)  ×  (Vn²  ÷  Sn)")
        lines.append("\n    Values:")
        sub("Vk% (short circuit voltage)", f"{r.trafo_vk_pct:.2f} %")
        sub("Vk% ÷ 100", f"{r.trafo_ratio:.4f}")
        sub("Transformer rating (Sn)", f"{r.trafo_kva:.0f} kVA  =  {r.sn_va:,.0f} VA")
        sub("Vn²", f"{r.vn_sq:,.0f} V²")
        sub("Vn² ÷ Sn", f"{r.trafo_vn_sq_sn:.6f} Ω")
        lines.append("\n    Calculation:")
        lines.append(f"        Z_trafo  =  {r.trafo_ratio:.4f}  ×  {r.trafo_vn_sq_sn:.6f}")
        lines.append(f"                 =  {r.z_trafo_ohm:.6f} Ω")
        lines.append(f"                 =  {r.z_trafo_mohm:.4f} mΩ  ✓")
        lines.append(f"\n    Physical meaning: with Vk = {r.trafo_vk_pct:.1f}%, a {r.trafo_kva:.0f} kVA transformer")
        lines.append(f"    at {vn:.0f} V LV side has a short-circuit impedance of {r.z_trafo_mohm:.2f} mΩ.")
    else:
        lines.append("\n    Transformer impedance EXCLUDED from this calculation.")
        lines.append("    Z_trafo = 0.000 mΩ")
        lines.append("    (Use this when calculating downstream of a known impedance point,")
        lines.append("     e.g. from a main distribution board with a known fault level.)")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Cable Impedance (Z_cable)")
    step += 1
    if r.include_cable:
        lines.append(
            "\n    For LV cables, reactance (X) is small compared to resistance (R)\n"
            "    and is typically neglected in the simplified method. Only DC resistance\n"
            "    at operating temperature is used.\n"
        )
        lines.append("    For a fault at the end of the cable, current flows through both")
        lines.append("    the phase conductor and the return conductor (neutral or earth),")
        lines.append("    so the total loop resistance is 2 × R_phase.\n")
        n_par = r.num_parallel_cables
        if n_par > 1:
            lines.append("    Formula:")
            lines.append("        Z_cable  =  2  ×  R  ×  (L ÷ 1000)  ÷  N")
            lines.append("        [R in Ω/km, L in metres, N = number of parallel cables]")
            lines.append("\n    Parallel cables: When N cables are run in parallel between the")
            lines.append("    same two points, each cable carries 1/N of the fault current,")
            lines.append("    so the equivalent impedance is Z_single ÷ N.")
        else:
            lines.append("    Formula:")
            lines.append("        Z_cable  =  2  ×  R  ×  (L ÷ 1000)")
            lines.append("        [R in Ω/km, L in metres → L/1000 converts to km]")
        lines.append("\n    Values:")
        cable_src = r.cable_type_label if r.cable_type_label and r.cable_type_label != "Manual Entry" else "Manual entry"
        if r.cable_size_mm2 > 0:
            sub("Cable type", cable_src)
            sub("Cable size", f"{r.cable_size_mm2} mm²")
        sub("R (phase conductor, 70°C)", f"{r.cable_r_ohm_per_km:.4f} Ω/km")
        sub("L (one-way route length)", f"{r.cable_length_m:.1f} m  =  {r.cable_length_m/1000:.4f} km")
        sub("R × L/1000 (one conductor)", f"{r.cable_r_ohm_per_km:.4f} × {r.cable_length_m/1000:.4f}  =  {r.cable_r_one_way:.6f} Ω")
        if n_par > 1:
            sub("Number of parallel cables (N)", f"{n_par}")
        z_cable_single = 2.0 * r.cable_r_one_way
        lines.append("\n    Calculation:")
        if n_par > 1:
            lines.append(f"        Z_single =  2  ×  {r.cable_r_one_way:.6f}  =  {z_cable_single:.6f} Ω")
            lines.append(f"        Z_cable  =  {z_cable_single:.6f}  ÷  {n_par}")
        else:
            lines.append(f"        Z_cable  =  2  ×  {r.cable_r_one_way:.6f}")
        lines.append(f"                 =  {r.z_cable_ohm:.6f} Ω")
        lines.append(f"                 =  {r.z_cable_mohm:.4f} mΩ  ✓")
    else:
        lines.append("\n    Cable impedance EXCLUDED from this calculation.")
        lines.append("    Z_cable = 0.000 mΩ")
        lines.append("    (Fault is assumed at the transformer LV terminals / main busbar.)")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Total Impedance at Fault Point")
    step += 1
    parts = []
    vals  = []
    if r.include_grid:
        parts.append("Z_grid"); vals.append(f"{r.z_grid_mohm:.4f}")
    if r.include_trafo:
        parts.append("Z_trafo"); vals.append(f"{r.z_trafo_mohm:.4f}")
    if r.include_cable:
        parts.append("Z_cable"); vals.append(f"{r.z_cable_mohm:.4f}")

    formula_parts = " + ".join(parts) if parts else "0"
    lines.append("\n    Formula:")
    lines.append(f"        Z_total  =  {formula_parts}")
    lines.append("\n    Calculation:")
    lines.append(f"        Z_total  =  {' + '.join(vals) if vals else '0'}  [mΩ]")
    lines.append(f"                 =  {r.z_total_mohm:.4f} mΩ")
    lines.append(f"                 =  {r.z_total_ohm:.6f} Ω  ✓")

    if r.z_total_mohm > 0:
        # Show contribution percentages
        lines.append("\n    Contribution breakdown:")
        total_m = r.z_total_mohm
        if r.include_grid:
            lines.append(f"        Z_grid   =  {r.z_grid_mohm:7.4f} mΩ  ({r.z_grid_mohm/total_m*100:.1f}%)")
        if r.include_trafo:
            lines.append(f"        Z_trafo  =  {r.z_trafo_mohm:7.4f} mΩ  ({r.z_trafo_mohm/total_m*100:.1f}%)")
        if r.include_cable:
            lines.append(f"        Z_cable  =  {r.z_cable_mohm:7.4f} mΩ  ({r.z_cable_mohm/total_m*100:.1f}%)")
        lines.append(f"        Z_total  =  {r.z_total_mohm:7.4f} mΩ  (100%)")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Three-Phase Symmetrical Fault Current (Isc_3φ)")
    step += 1
    lines.append(
        "\n    The three-phase symmetrical fault (L-L-L) produces the MAXIMUM fault\n"
        "    current for a balanced system. This is the primary value used for\n"
        "    rating protective devices (Icu / Ics).\n"
    )
    lines.append("    Formula (IEC 60909 / SANS 10142-1 §5):")
    lines.append("        Isc_3φ  =  (c × Vn)  ÷  (√3 × Z_total)")
    lines.append("\n    Voltage factor c (IEC 60909 Table 1 / SANS):")
    lines.append("        c = 1.05 → Maximum Isc (for device rating / withstand checks)")
    lines.append("        c = 0.95 → Minimum Isc (for protection sensitivity / reach checks)")
    lines.append("\n    ── Maximum (c = 1.05) ──────────────────────────────────────────")
    lines.append(f"        Numerator   =  c × Vn  =  1.05 × {vn:.0f}  =  {C_MAX * vn:.1f} V")
    lines.append(f"        Denominator =  √3 × Z_total")
    lines.append(f"                     =  {sqrt3_str} × {r.z_total_ohm:.6f}")
    lines.append(f"                     =  {SQRT3 * r.z_total_ohm:.6f} Ω")
    lines.append(f"        Isc_3φ_max  =  {C_MAX * vn:.1f}  ÷  {SQRT3 * r.z_total_ohm:.6f}")
    lines.append(f"                     =  {r.isc_3ph_max_a:,.1f} A")
    lines.append(f"                     =  {r.isc_3ph_max_ka:.3f} kA  ✓")
    lines.append("\n    ── Minimum (c = 0.95) ──────────────────────────────────────────")
    lines.append(f"        Numerator   =  c × Vn  =  0.95 × {vn:.0f}  =  {C_MIN * vn:.1f} V")
    lines.append(f"        Isc_3φ_min  =  {C_MIN * vn:.1f}  ÷  {SQRT3 * r.z_total_ohm:.6f}")
    lines.append(f"                     =  {r.isc_3ph_min_a:,.1f} A")
    lines.append(f"                     =  {r.isc_3ph_min_ka:.3f} kA  ✓")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Line-to-Line Fault Current (Isc_LL)")
    step += 1
    lines.append(
        "\n    A line-to-line (L-L) fault involves two phases. It produces 86.6% of\n"
        "    the three-phase fault current. Uses the maximum Isc_3φ as the basis.\n"
    )
    lines.append("    Formula:")
    lines.append("        Isc_LL  =  (√3 ÷ 2) × Isc_3φ_max  =  0.8660 × Isc_3φ_max")
    lines.append(f"\n        Isc_LL  =  0.8660  ×  {r.isc_3ph_max_a:,.1f}")
    lines.append(f"                 =  {r.isc_ll_a:,.1f} A")
    lines.append(f"                 =  {r.isc_ll_ka:.3f} kA  ✓")
    lines.append(f"\n    Verify: {r.isc_ll_ka:.3f} / {r.isc_3ph_max_ka:.3f} = "
                 f"{r.isc_ll_ka/r.isc_3ph_max_ka:.3f}  (should equal 0.866)")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Line-to-Neutral Fault Current (Isc_LN)")
    step += 1
    lines.append(
        "\n    A single-phase to neutral (L-N) fault. The simplified IEC 60909 method\n"
        "    for LV TN systems assumes neutral impedance Zn ≈ Zph (equal conductors).\n"
        "    For accurate L-N calculations, use the actual loop impedance (Zs).\n"
    )
    lines.append("    Formula (simplified — assumes Zn = Zph):")
    lines.append("        Isc_LN  =  (c × Vn / √3)  ÷  Z_total")
    lines.append("        [Vn/√3 = phase-to-neutral voltage]")
    vn_phase = vn / SQRT3
    lines.append(f"\n        Vn / √3  =  {vn:.0f} / {sqrt3_str}  =  {vn_phase:.3f} V (phase voltage)")
    lines.append(f"        c × Vn/√3  =  1.05 × {vn_phase:.3f}  =  {C_MAX * vn_phase:.3f} V")
    lines.append(f"        Isc_LN   =  {C_MAX * vn_phase:.3f}  ÷  {r.z_total_ohm:.6f}")
    lines.append(f"                  =  {r.isc_ln_a:,.1f} A")
    lines.append(f"                  =  {r.isc_ln_ka:.3f} kA  ✓")
    lines.append("\n    NOTE: For TN-S systems, use actual neutral conductor R if different from")
    lines.append("    phase conductor. For TN-C systems, PEN conductor carries fault current.")

    # ──────────────────────────────────────────────────────────────────────────
    h(f"STEP {step} — Protection Device Adequacy Check")
    step += 1
    lines.append(
        "\n    Per SANS 10142-1:2020 §5.3 and IEC 60898 / IEC 60947:\n"
        "    The device's breaking capacity (Icu for MCCBs, Icn for MCBs)\n"
        "    must be ≥ the maximum prospective fault current at its installation point.\n"
    )
    lines.append("    Criterion:")
    lines.append("        Icu  ≥  Isc_3φ_max  (device is adequate)")
    lines.append("        Icu  <  Isc_3φ_max  (device is INADEQUATE — must upgrade)")
    lines.append(f"\n    Check:")
    lines.append(f"        Icu (selected device) =  {r.breaker_icu_ka:.0f} kA")
    lines.append(f"        Isc_3φ_max            =  {r.isc_3ph_max_ka:.3f} kA")
    if r.breaker_adequate:
        lines.append(f"\n    RESULT:  {r.breaker_icu_ka:.0f} kA  ≥  {r.isc_3ph_max_ka:.3f} kA  →  DEVICE ADEQUATE  ✔")
    else:
        lines.append(f"\n    RESULT:  {r.breaker_icu_ka:.0f} kA  <  {r.isc_3ph_max_ka:.3f} kA  →  DEVICE INADEQUATE  ✘")
        lines.append(f"    ACTION:  Select a device with Icu ≥ {r.isc_3ph_max_ka:.3f} kA")
        # Find next standard rating
        std = [6, 10, 16, 25, 36, 50, 63, 80, 100, 125, 150]
        recommended = next((x for x in std if x >= r.isc_3ph_max_ka), None)
        if recommended:
            lines.append(f"             Next standard rating: {recommended} kA")

    # ──────────────────────────────────────────────────────────────────────────
    h("SUMMARY OF RESULTS")
    lines.append(f"\n    {'Parameter':<36s} {'Value':>12s}")
    lines.append(f"    {'─'*50}")
    if r.include_grid:
        lines.append(f"    {'Z_grid':<36s} {r.z_grid_mohm:>10.4f} mΩ")
    if r.include_trafo:
        lines.append(f"    {'Z_trafo':<36s} {r.z_trafo_mohm:>10.4f} mΩ")
    if r.include_cable:
        lines.append(f"    {'Z_cable':<36s} {r.z_cable_mohm:>10.4f} mΩ")
    lines.append(f"    {'Z_total':<36s} {r.z_total_mohm:>10.4f} mΩ")
    lines.append(f"    {'─'*50}")
    lines.append(f"    {'Isc 3-phase MAX (c=1.05)':<36s} {r.isc_3ph_max_ka:>10.3f} kA")
    lines.append(f"    {'Isc 3-phase MIN (c=0.95)':<36s} {r.isc_3ph_min_ka:>10.3f} kA")
    lines.append(f"    {'Isc Line-to-Line':<36s} {r.isc_ll_ka:>10.3f} kA")
    lines.append(f"    {'Isc Line-to-Neutral':<36s} {r.isc_ln_ka:>10.3f} kA")
    lines.append(f"    {'─'*50}")
    lines.append(f"    {'Device Icu':<36s} {r.breaker_icu_ka:>10.0f} kA")
    lines.append(f"    {'Protection adequacy':<36s} {'ADEQUATE ✔' if r.breaker_adequate else 'INADEQUATE ✘':>12s}")
    lines.append(f"\n    Standard: SANS 10142-1:2020 §5  /  IEC 60909 (simplified LV method)")
    lines.append(f"    {'─'*50}")

    return "\n".join(lines)


# Standard LV transformer Vk% values per SANS 780 / IEC 60076
STANDARD_VK = {
    "50 kVA":   4.0, "100 kVA":  4.0, "160 kVA":  4.0,
    "200 kVA":  4.0, "250 kVA":  4.0, "315 kVA":  4.0,
    "400 kVA":  4.0, "500 kVA":  4.0, "630 kVA":  6.0,
    "800 kVA":  6.0, "1000 kVA": 6.0, "1250 kVA": 6.0,
    "1600 kVA": 6.0, "2000 kVA": 6.0, "2500 kVA": 6.0,
}

# Standard breaker Icu ratings [kA]
STANDARD_ICU = [6, 10, 16, 25, 36, 50, 63, 80, 100, 125, 150]
