"""stringing_algo.py — Auto-stringing algorithm for PV panel layouts."""
import math
from dataclasses import dataclass, field
from typing import List, Dict
from collections import defaultdict


@dataclass
class InverterConfig:
    id: int
    num_mppts: int
    strings_per_mppt: int


@dataclass
class StringResult:
    name: str           # e.g. "1-A-1"
    inverter_id: int
    mppt_letter: str    # "A", "B", "C" ...
    string_num: int     # 1, 2, 3 ...
    panels: List[int]   # panel ids in order from + to -
    roof_section_id: int
    color_index: int = 0    # index into PANEL_COLORS


@dataclass
class AssignmentResult:
    strings: List[StringResult]
    unassigned: List[int]   # panel ids not in any string
    warnings: List[str]


def auto_string(panels, roof_sections, inverter_configs, panels_per_string) -> AssignmentResult:
    """
    panels: list of ParsedPanel (with .roof_section_id set)
    roof_sections: list of dicts {id, name, angle}
    inverter_configs: list of InverterConfig
    panels_per_string: int
    """
    warnings = []
    unassigned = []

    if not panels:
        return AssignmentResult([], [], ["No panels loaded."])
    if not inverter_configs:
        return AssignmentResult([], [p.id for p in panels], ["No inverters configured."])

    # Group panels by section
    section_panels: Dict[int, list] = defaultdict(list)
    for p in panels:
        if p.roof_section_id == -1:
            unassigned.append(p.id)
        else:
            section_panels[p.roof_section_id].append(p)

    if not section_panels:
        # No sections defined -- treat all panels as one section
        section_panels[-99] = list(panels)
        unassigned = []
        warnings.append("No roof sections defined — all panels treated as one section.")

    # Form strings within each section
    section_string_groups: Dict[int, List[List[int]]] = {}
    for sec_id, sec_panels in section_panels.items():
        strings_here = _form_strings(sec_panels, panels_per_string)
        section_string_groups[sec_id] = strings_here

    # Compute centroid of each section for geographic sorting
    sec_centroids = {}
    for sec_id, sec_panels in section_panels.items():
        sec_centroids[sec_id] = sum(p.cx for p in sec_panels) / len(sec_panels)

    # Sort sections by centroid_x -- geographic left-to-right
    sorted_sec_ids = sorted(section_string_groups.keys(), key=lambda s: sec_centroids.get(s, 0))

    # Build list of (section_id, [panels_list]) for all strings
    all_section_strings = []
    for sec_id in sorted_sec_ids:
        for str_panels in section_string_groups[sec_id]:
            all_section_strings.append((sec_id, str_panels))

    # Determine total MPPT capacity
    total_cap = sum(cfg.num_mppts * cfg.strings_per_mppt for cfg in inverter_configs)
    if len(all_section_strings) > total_cap:
        warnings.append(
            f"{len(all_section_strings)} strings generated but inverter capacity is "
            f"{total_cap} strings. Excess panels will be unassigned."
        )

    # Assign strings to inverters and MPPTs
    # Strategy: interleave sections across inverters (deal-like), same section -> same MPPT
    # Build MPPT slots: list of (inverter_id, mppt_letter, capacity)
    mppt_slots = []
    for cfg in inverter_configs:
        for m in range(cfg.num_mppts):
            letter = chr(ord('A') + m)
            mppt_slots.append({
                "inv_id": cfg.id,
                "letter": letter,
                "cap": cfg.strings_per_mppt,
                "used": 0,
                "sec_id": None,   # locked to first section assigned
            })

    # Assign strings to MPPT slots in round-robin order.
    # Same section fills an existing slot first; new sections get fresh slots.
    slot_idx = 0

    result_strings = []
    color_idx = 0

    for sec_id, pan_ids in all_section_strings:
        # Find a valid slot for this string.
        # Rule: same section MAY span multiple MPPT slots, but each slot only holds
        # one section (so each MPPT only ever has panels from one roof angle).
        slot = _find_slot(sec_id, mppt_slots, slot_idx)
        if slot == -1:
            unassigned.extend(pan_ids)
            continue
        # Advance round-robin pointer past the chosen slot
        slot_idx = (slot + 1) % len(mppt_slots)
        slot_data = mppt_slots[slot]
        slot_data["sec_id"] = sec_id

        inv_id  = slot_data["inv_id"]
        letter  = slot_data["letter"]
        str_num = slot_data["used"] + 1
        name    = f"{inv_id}-{letter}-{str_num}"

        result_strings.append(StringResult(
            name=name,
            inverter_id=inv_id,
            mppt_letter=letter,
            string_num=str_num,
            panels=pan_ids,
            roof_section_id=sec_id,
            color_index=color_idx % 16,
        ))
        slot_data["used"] += 1
        color_idx += 1

    return AssignmentResult(strings=result_strings, unassigned=unassigned, warnings=warnings)


def _find_slot(sec_id: int, mppt_slots: list, slot_idx: int) -> int:
    """
    Return the index of the best available MPPT slot for this section.
    A slot is available if:
      - it is not yet full (used < cap), AND
      - it is not locked to a DIFFERENT section.
    Prefer slots already locked to sec_id first (fill them up before opening new slots).
    Fall back to any unlocked slot in round-robin order.
    Returns -1 if no slot is available.
    """
    n = len(mppt_slots)
    # Pass 1: find an existing slot already assigned to this section that still has room
    for i in range(n):
        sd = mppt_slots[i]
        if sd["sec_id"] == sec_id and sd["used"] < sd["cap"]:
            return i
    # Pass 2: round-robin through unlocked slots
    for attempt in range(n):
        s = (slot_idx + attempt) % n
        sd = mppt_slots[s]
        if sd["sec_id"] is None and sd["used"] < sd["cap"]:
            return s
    return -1


def _form_strings(sec_panels, panels_per_string) -> List[List[int]]:
    """Cluster panels into rows, snake through, cut into strings."""
    if not sec_panels:
        return []

    avg_h = sum(p.height for p in sec_panels) / len(sec_panels)
    tolerance = avg_h * 0.6

    # Cluster into rows by cy
    rows: List[List] = []
    sorted_panels = sorted(sec_panels, key=lambda p: p.cy)
    for panel in sorted_panels:
        placed = False
        for row in rows:
            if abs(panel.cy - _row_mean(row)) <= tolerance:
                row.append(panel)
                placed = True
                break
        if not placed:
            rows.append([panel])

    # Sort rows top-to-bottom (in screen coords, larger y = lower on screen in DXF = invert later)
    # In DXF, Y increases upward, so sort descending -> top of roof first
    rows.sort(key=_row_mean, reverse=True)

    # Snake left-right-left within rows
    panel_order = []
    for i, row in enumerate(rows):
        row_sorted = sorted(row, key=lambda p: p.cx, reverse=(i % 2 == 1))
        panel_order.extend(row_sorted)

    # Cut into strings of panels_per_string
    panel_ids = [p.id for p in panel_order]
    strings = []
    for i in range(0, len(panel_ids), panels_per_string):
        chunk = panel_ids[i:i + panels_per_string]
        strings.append(chunk)
    return strings


def _row_mean(row):
    return sum(p.cy for p in row) / len(row)
