"""
gland_size_logic.py
-------------------
Cable gland selection logic.

Gland types:
  - CCG BW  Captive Cone Gland  → SWA / Aluminium Armoured cable  (CCG GI010214)
  - CCG A2  Compression Gland   → H07RN-F / Unarmoured cable       (CCG GI020816)

Selection criterion: cable OD must fall within gland Min 'B' … Max 'B' (mm).
Best-fit = smallest OD range that fully covers the cable OD.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# CCG BW Captive Cone Gland — SWA / Aluminium Armoured  (all dims mm)
# ─────────────────────────────────────────────────────────────────────────────
BW_GLANDS: list[dict] = [
    {"code": "0503-0",  "size_ref": "0-20s",   "thread": "M20x1.5",  "od_min": 11.5, "od_max": 16.0},
    {"code": "050301",  "size_ref": "1-20",     "thread": "M20x1.5",  "od_min": 14.5, "od_max": 20.5},
    {"code": "050302",  "size_ref": "2-25",     "thread": "M25x1.5",  "od_min": 20.5, "od_max": 26.5},
    {"code": "050303",  "size_ref": "3-32",     "thread": "M32x1.5",  "od_min": 26.5, "od_max": 33.5},
    {"code": "050304",  "size_ref": "4-40",     "thread": "M40x1.5",  "od_min": 33.0, "od_max": 42.5},
    {"code": "050305",  "size_ref": "5-50",     "thread": "M50x1.5",  "od_min": 42.5, "od_max": 52.5},
    {"code": "050306",  "size_ref": "6-63",     "thread": "M63x1.5",  "od_min": 52.5, "od_max": 65.5},
    {"code": "050307",  "size_ref": "7-75",     "thread": "M75x1.5",  "od_min": 65.5, "od_max": 78.0},
    {"code": "050308",  "size_ref": "8-80",     "thread": "M80x2.0",  "od_min": 78.0, "od_max": 82.0},
    {"code": "050309",  "size_ref": "9-90",     "thread": "M90x2.0",  "od_min": 82.0, "od_max": 91.0},
    {"code": "050310",  "size_ref": "10-100",   "thread": "M100x2.0", "od_min": 90.0, "od_max": 100.0},
    {"code": "050311",  "size_ref": "11-110",   "thread": "M110x2.0", "od_min": 100.0, "od_max": 114.0},
    {"code": "050312",  "size_ref": "12-120",   "thread": "M120x2.0", "od_min": 103.0, "od_max": 118.0},
    {"code": "050313",  "size_ref": "13-130",   "thread": "M130x2.0", "od_min": 113.0, "od_max": 124.0},
]

# ─────────────────────────────────────────────────────────────────────────────
# CCG A2 Compression Gland — Unarmoured / H07RN-F  (all dims mm)
# ─────────────────────────────────────────────────────────────────────────────
A2_GLANDS: list[dict] = [
    {"code": "053500-16S", "size_ref": "00-16S",  "thread": "M16x1.5",  "od_min": 1.0,   "od_max": 6.0},
    {"code": "053500-16",  "size_ref": "00-16ss", "thread": "M16x1.5",  "od_min": 3.0,   "od_max": 8.5},
    {"code": "053500",     "size_ref": "00-20ss", "thread": "M20x1.5",  "od_min": 3.0,   "od_max": 8.5},
    {"code": "0535-0",     "size_ref": "0-20s",   "thread": "M20x1.5",  "od_min": 7.0,   "od_max": 11.5},
    {"code": "053501",     "size_ref": "1-20",    "thread": "M20x1.5",  "od_min": 11.0,  "od_max": 15.0},
    {"code": "053522",     "size_ref": "2s-25s",  "thread": "M25x1.5",  "od_min": 11.5,  "od_max": 17.5},
    {"code": "053502",     "size_ref": "2-25",    "thread": "M25x1.5",  "od_min": 15.0,  "od_max": 20.0},
    {"code": "053533",     "size_ref": "3s-32s",  "thread": "M32x1.5",  "od_min": 16.0,  "od_max": 22.0},
    {"code": "053503",     "size_ref": "3-32",    "thread": "M32x1.5",  "od_min": 20.0,  "od_max": 26.5},
    {"code": "053544",     "size_ref": "4s-40s",  "thread": "M40x1.5",  "od_min": 22.0,  "od_max": 31.5},
    {"code": "053504",     "size_ref": "4-40",    "thread": "M40x1.5",  "od_min": 26.0,  "od_max": 34.0},
    {"code": "053555",     "size_ref": "5s-50s",  "thread": "M50x1.5",  "od_min": 29.0,  "od_max": 38.0},
    {"code": "053505",     "size_ref": "5-50",    "thread": "M50x1.5",  "od_min": 34.0,  "od_max": 44.5},
    {"code": "053566",     "size_ref": "6s-63s",  "thread": "M63x1.5",  "od_min": 38.0,  "od_max": 50.0},
    {"code": "053506",     "size_ref": "6-63",    "thread": "M63x1.5",  "od_min": 44.5,  "od_max": 56.5},
    {"code": "053577",     "size_ref": "7s-75s",  "thread": "M75x1.5",  "od_min": 50.0,  "od_max": 62.0},
    {"code": "053507",     "size_ref": "7-75",    "thread": "M75x1.5",  "od_min": 56.0,  "od_max": 67.5},
    {"code": "053588",     "size_ref": "8s-80s",  "thread": "M80x2.0",  "od_min": 54.0,  "od_max": 69.0},
    {"code": "053508",     "size_ref": "8-80",    "thread": "M80x2.0",  "od_min": 65.0,  "od_max": 74.0},
    {"code": "053599",     "size_ref": "9s-90s",  "thread": "M90x2.0",  "od_min": 60.0,  "od_max": 75.0},
    {"code": "053509",     "size_ref": "9-90",    "thread": "M90x2.0",  "od_min": 73.0,  "od_max": 81.5},
    {"code": "053510",     "size_ref": "10-100",  "thread": "M100x2.0", "od_min": 81.0,  "od_max": 91.0},
    {"code": "053511",     "size_ref": "11-110",  "thread": "M110x2.0", "od_min": 91.0,  "od_max": 101.0},
    {"code": "053512",     "size_ref": "12-120",  "thread": "M120x2.0", "od_min": 101.0, "od_max": 109.0},
    {"code": "053513",     "size_ref": "13-130",  "thread": "M130x2.0", "od_min": 109.0, "od_max": 119.0},
]

# ─────────────────────────────────────────────────────────────────────────────
# Cable outer diameters [mm] — 3-core and 4-core separated
# Source: Aberdare BS5467 / SANS1507 (SWA), IEC 60245 (H07RN-F)
# Nominal values at 70 °C — verify against your specific cable batch.
# ─────────────────────────────────────────────────────────────────────────────
CABLE_OD: dict[str, dict[float, float]] = {

    # ── SWA Copper 3-core ─────────────────────────────────────────────────────
    "SWA Copper 3c": {
        1.5: 14.8,   2.5: 16.5,   4.0: 18.5,   6.0: 20.3,   10.0: 23.5,
        16.0: 27.0,  25.0: 31.0,  35.0: 34.0,  50.0: 38.5,  70.0: 44.0,
        95.0: 50.0,  120.0: 54.5, 150.0: 60.0, 185.0: 66.5, 240.0: 75.5,
        300.0: 83.0, 400.0: 95.0, 630.0: 114.0,
    },

    # ── SWA Copper 4-core ─────────────────────────────────────────────────────
    "SWA Copper 4c": {
        1.5: 15.4,   2.5: 17.2,   4.0: 19.3,   6.0: 21.2,   10.0: 24.5,
        16.0: 28.2,  25.0: 32.5,  35.0: 35.7,  50.0: 40.5,  70.0: 46.2,
        95.0: 52.5,  120.0: 57.2, 150.0: 63.0, 185.0: 69.5, 240.0: 79.0,
        300.0: 87.0, 400.0: 99.0,
    },

    # ── SWA Aluminium 3-core ──────────────────────────────────────────────────
    "SWA Aluminium 3c": {
        25.0: 30.5,  35.0: 33.5,  50.0: 37.5,  70.0: 43.5,
        95.0: 49.5,  120.0: 54.0, 150.0: 59.0, 185.0: 65.5,
        240.0: 73.5, 300.0: 82.0,
    },

    # ── SWA Aluminium 4-core ──────────────────────────────────────────────────
    "SWA Aluminium 4c": {
        25.0: 32.0,  35.0: 35.2,  50.0: 39.5,  70.0: 45.5,
        95.0: 51.5,  120.0: 56.5, 150.0: 62.0, 185.0: 68.5,
        240.0: 77.5, 300.0: 86.5,
    },

    # ── H07RN-F 3-core ────────────────────────────────────────────────────────
    "H07RN-F 3c": {
        1.5: 11.0,   2.5: 12.5,   4.0: 14.0,   6.0: 16.0,   10.0: 19.5,
        16.0: 23.0,  25.0: 27.5,  35.0: 31.0,  50.0: 35.5,  70.0: 41.0,
        95.0: 47.0,  120.0: 52.0, 150.0: 57.0, 185.0: 64.0,
        240.0: 73.0, 300.0: 82.0,
    },

    # ── H07RN-F 4-core ────────────────────────────────────────────────────────
    "H07RN-F 4c": {
        1.5: 12.0,   2.5: 13.5,   4.0: 15.0,   6.0: 17.5,   10.0: 21.0,
        16.0: 25.0,  25.0: 30.0,  35.0: 34.0,  50.0: 38.5,  70.0: 44.5,
        95.0: 51.0,  120.0: 56.5, 150.0: 62.0, 185.0: 70.0,
        240.0: 79.0, 300.0: 88.0,
    },

    # ── H07RN-F Single Core ───────────────────────────────────────────────────
    "H07RN-F Single Core": {
        1.5: 6.5,    2.5: 7.5,    4.0: 8.5,    6.0: 9.5,    10.0: 12.0,
        16.0: 14.0,  25.0: 16.0,  35.0: 18.0,  50.0: 20.5,  70.0: 23.5,
        95.0: 27.0,  120.0: 30.0, 150.0: 33.0, 185.0: 37.0,
        240.0: 43.0, 300.0: 48.0,
    },
}

# Gland family per cable type
CABLE_GLAND_TYPE: dict[str, str] = {
    "SWA Copper 3c":     "BW",
    "SWA Copper 4c":     "BW",
    "SWA Aluminium 3c":  "BW",
    "SWA Aluminium 4c":  "BW",
    "H07RN-F 3c":        "A2",
    "H07RN-F 4c":        "A2",
    "H07RN-F Single Core": "A2",
}

# Default conductor count (for lug qty auto-fill)
CABLE_CORES: dict[str, int] = {
    "SWA Copper 3c":     3,
    "SWA Copper 4c":     4,
    "SWA Aluminium 3c":  3,
    "SWA Aluminium 4c":  4,
    "H07RN-F 3c":        3,
    "H07RN-F 4c":        4,
    "H07RN-F Single Core": 1,
}

# Standard lug options
LUG_SIZES_MM2: list[int] = [6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400]
LUG_BOLT_SIZES: list[str] = ["M5", "M6", "M8", "M10", "M12", "M16", "M20"]


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GlandMatch:
    """Gland selection result for one cable end."""
    cable_od:       float
    gland_type:     str
    matched:        bool
    product_code:   str        = ""
    size_ref:       str        = ""
    thread:         str        = ""
    od_min:         float      = 0.0
    od_max:         float      = 0.0
    all_candidates: list[dict] = field(default_factory=list)


@dataclass
class BOQItem:
    item_no:      int
    description:  str
    product_code: str
    qty:          int
    unit:         str = "No."


@dataclass
class GlandCalcResult:
    cable_type:       str
    cable_size_mm2:   float
    cable_od:         float
    cable_qty:        int
    gland_type:       str
    # Per-cable selections: list of (gland_a, gland_b) booleans
    selections:       list[tuple[bool, bool]]
    # Gland match (same spec for all cables, only qty varies)
    gland_match:      Optional[GlandMatch]
    total_glands_a:   int
    total_glands_b:   int
    boq:              list[BOQItem]


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

def find_gland(cable_od: float, gland_type: str) -> GlandMatch:
    """Find best-fitting gland for a given cable OD.
    Best-fit = smallest range that still covers the OD.
    """
    db = BW_GLANDS if gland_type == "BW" else A2_GLANDS
    candidates = [g for g in db if g["od_min"] <= cable_od <= g["od_max"]]
    if not candidates:
        return GlandMatch(cable_od=cable_od, gland_type=gland_type, matched=False)
    best = min(candidates, key=lambda g: g["od_max"] - g["od_min"])
    return GlandMatch(
        cable_od=cable_od,
        gland_type=gland_type,
        matched=True,
        product_code=best["code"],
        size_ref=best["size_ref"],
        thread=best["thread"],
        od_min=best["od_min"],
        od_max=best["od_max"],
        all_candidates=candidates,
    )


def calc_gland(
    cable_type:    str,
    cable_size_mm2: float,
    # Per-cable list of (need_gland_a, need_gland_b)
    selections:    list[tuple[bool, bool]],
    include_lugs:  bool  = False,
    lug_size_mm2:  float = 0.0,
    lug_bolt:      str   = "",
    lug_cores:     int   = 3,
) -> GlandCalcResult:
    """Main calculation — select gland and build BOQ for individual cable selections."""
    cable_od   = CABLE_OD.get(cable_type, {}).get(cable_size_mm2, 0.0)
    gland_type = CABLE_GLAND_TYPE.get(cable_type, "BW")
    cable_qty  = len(selections)

    gland_match  = find_gland(cable_od, gland_type) if cable_od > 0 else None
    total_a      = sum(1 for (a, _) in selections if a)
    total_b      = sum(1 for (_, b) in selections if b)
    total_glands = total_a + total_b

    boq: list[BOQItem] = []
    item = 1

    # Glands
    if total_glands > 0:
        if gland_match and gland_match.matched:
            gland_name = "BW Captive Cone Gland" if gland_type == "BW" else "A2 Compression Gland"
            desc = (f"CCG {gland_name}  —  Size {gland_match.size_ref}"
                    f"  ({gland_match.thread})"
                    f"  [{cable_type}  {cable_size_mm2:.0f}mm²  OD {cable_od:.1f}mm]"
                    f"  ({total_a} End-A  +  {total_b} End-B)")
            boq.append(BOQItem(item, desc, gland_match.product_code, total_glands))
            item += 1
        else:
            boq.append(BOQItem(
                item,
                f"Gland  —  NO MATCH  [{cable_type} {cable_size_mm2:.0f}mm²"
                f"  OD {cable_od:.1f}mm]  check manufacturer data",
                "—", total_glands,
            ))
            item += 1

    # Lugs
    if include_lugs and lug_size_mm2 > 0 and lug_bolt:
        lug_ends = total_a + total_b
        if lug_ends == 0:
            lug_ends = cable_qty * 2
        lug_qty  = lug_ends * lug_cores
        lug_desc = (f"Copper Compression Cable Lug"
                    f"  {lug_size_mm2:.0f}mm²  ×  {lug_bolt}  hole"
                    f"  ({lug_ends} ends  ×  {lug_cores} cores)")
        boq.append(BOQItem(item, lug_desc, f"LUG-{lug_size_mm2:.0f}-{lug_bolt}", lug_qty))

    return GlandCalcResult(
        cable_type=cable_type,
        cable_size_mm2=cable_size_mm2,
        cable_od=cable_od,
        cable_qty=cable_qty,
        gland_type=gland_type,
        selections=selections,
        gland_match=gland_match,
        total_glands_a=total_a,
        total_glands_b=total_b,
        boq=boq,
    )
