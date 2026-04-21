"""dxf_parser.py — Parse DXF file and return list of ParsedPanel objects."""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from collections import Counter


@dataclass
class ParsedPanel:
    id: int
    cx: float        # centre x in DXF coords
    cy: float        # centre y in DXF coords
    width: float
    height: float
    rotation: float  # degrees
    layer: str
    source_block: str = ""
    roof_section_id: int = -1   # assigned later


def parse_dxf(filepath: str):
    """
    Returns (panels: List[ParsedPanel], meta: dict)
    meta keys: source, block_name, panel_count, bounds (minx,miny,maxx,maxy), error
    """
    try:
        import ezdxf
    except ImportError:
        raise ImportError("ezdxf is not installed. Run: pip install ezdxf")

    try:
        doc = ezdxf.readfile(filepath)
    except Exception as e:
        return [], {"error": str(e)}

    msp = doc.modelspace()
    panels = []

    # -- Strategy A: INSERT block entities --
    inserts = list(msp.query('INSERT'))
    if inserts:
        counts = Counter(e.dxf.name for e in inserts)
        # Most common block appearing more than once is the panel block
        candidates = [(n, c) for n, c in counts.most_common() if c > 1]
        if candidates:
            block_name = candidates[0][0]
            # Get block bounding box
            bw, bh = _block_bbox(doc, block_name)
            pid = 0
            for ins in inserts:
                if ins.dxf.name != block_name:
                    continue
                pos = ins.dxf.insert
                sx = float(ins.dxf.get('xscale', 1.0))
                sy = float(ins.dxf.get('yscale', 1.0))
                rot = float(ins.dxf.get('rotation', 0.0))
                w = bw * sx
                h = bh * sy
                # insert point is lower-left of block; centre offset
                cx = float(pos.x) + w / 2.0
                cy = float(pos.y) + h / 2.0
                panels.append(ParsedPanel(
                    id=pid, cx=cx, cy=cy, width=w, height=h,
                    rotation=rot, layer=ins.dxf.get('layer', '0'),
                    source_block=block_name
                ))
                pid += 1
            if panels:
                return panels, _meta(panels, "INSERT", block_name)

    # -- Strategy B: LWPOLYLINE closed rectangles --
    plines = list(msp.query('LWPOLYLINE'))
    rects = []
    for pl in plines:
        pts = list(pl.get_points())
        if len(pts) < 4:
            continue
        xs = [p[0] for p in pts[:4]]
        ys = [p[1] for p in pts[:4]]
        w = round(max(xs) - min(xs), 2)
        h = round(max(ys) - min(ys), 2)
        if w > 0 and h > 0:
            rects.append((w, h, (min(xs)+max(xs))/2, (min(ys)+max(ys))/2))

    if rects:
        # Find most common (w, h) within 10% tolerance
        wh_counts = Counter((r[0], r[1]) for r in rects)
        pw, ph = wh_counts.most_common(1)[0][0]
        pid = 0
        for w, h, cx, cy in rects:
            if abs(w - pw) / max(pw, 0.001) < 0.15 and abs(h - ph) / max(ph, 0.001) < 0.15:
                panels.append(ParsedPanel(
                    id=pid, cx=cx, cy=cy, width=pw, height=ph,
                    rotation=0.0, layer='0', source_block=""
                ))
                pid += 1
        if panels:
            return panels, _meta(panels, "POLYLINE", "")

    return [], {"error": "No panel entities detected", "panel_count": 0}


def _block_bbox(doc, block_name) -> Tuple[float, float]:
    """Return (width, height) of a block by scanning its entities."""
    try:
        block = doc.blocks.get(block_name)
        xs, ys = [], []
        for e in block:
            try:
                t = e.dxftype()
                if t == 'LINE':
                    xs += [e.dxf.start.x, e.dxf.end.x]
                    ys += [e.dxf.start.y, e.dxf.end.y]
                elif t == 'LWPOLYLINE':
                    for pt in e.get_points():
                        xs.append(pt[0]); ys.append(pt[1])
                elif t in ('SOLID', 'TRACE'):
                    for attr in ('vtx0','vtx1','vtx2','vtx3'):
                        v = e.dxf.get(attr)
                        if v:
                            xs.append(v.x); ys.append(v.y)
                elif hasattr(e.dxf, 'insert'):
                    xs.append(e.dxf.insert.x); ys.append(e.dxf.insert.y)
            except Exception:
                pass
        if xs and ys:
            return max(xs) - min(xs), max(ys) - min(ys)
    except Exception:
        pass
    return 1.0, 2.0   # sensible default for a 1m x 2m panel


def _meta(panels, source, block_name):
    xs = [p.cx for p in panels]; ys = [p.cy for p in panels]
    return {
        "source": source,
        "block_name": block_name,
        "panel_count": len(panels),
        "bounds": (min(xs), min(ys), max(xs), max(ys)),
        "error": None,
    }
