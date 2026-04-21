"""canvas_view.py — Interactive PV panel layout canvas."""
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPolygonItem,
    QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QPainter, QPainterPath, QPolygonF, QFont, QTransform
)

MODE_SELECT    = "select"
MODE_ROOF_DRAW = "roof_draw"
MODE_MANUAL    = "manual_string"

# 16 distinct string colours
PANEL_COLORS = [
    "#58a6ff","#3fb950","#f0883e","#d2a8ff","#ffa657","#79c0ff",
    "#56d364","#ff7b72","#e3b341","#bc8cff","#39d353","#ff6e6e",
    "#4ac26b","#f78166","#9ecbff","#70e2ff",
]


class PanelItem(QGraphicsRectItem):
    def __init__(self, panel_id, x, y, w, h, rotation=0.0):
        super().__init__(0, 0, w, h)
        self.panel_id = panel_id
        self.string_name = None
        self.order_in_string = None
        self.is_start = False
        self.is_end   = False
        self._base_color = QColor("#2d333b")
        self._str_color  = QColor("#2d333b")
        self.setPos(x, y)
        if rotation:
            self.setRotation(rotation)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor("#30363d"), 1.0))
        self.setBrush(QBrush(self._base_color))

    def setAssignment(self, string_name, order, is_start, is_end, color: QColor):
        self.string_name  = string_name
        self.order_in_string = order
        self.is_start = is_start
        self.is_end   = is_end
        self._str_color = color
        self.setBrush(QBrush(color))
        self.update()

    def clearAssignment(self):
        self.string_name = None
        self.order_in_string = None
        self.is_start = False
        self.is_end   = False
        self._str_color = self._base_color
        self.setBrush(QBrush(self._base_color))
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        # Fill
        painter.fillRect(rect, self._str_color if self.string_name else self._base_color)
        # Border
        border_color = QColor("#58a6ff") if self.isSelected() else QColor("#404040")
        painter.setPen(QPen(border_color, 1.5 if self.isSelected() else 0.8))
        painter.drawRect(rect)
        # Label
        if self.string_name:
            painter.setPen(QPen(QColor("#ffffff"), 1))
            font = QFont("Segoe UI", max(4, min(8, int(rect.height() * 0.35))))
            font.setBold(True)
            painter.setFont(font)
            if self.is_start:
                label = "+"
                painter.setPen(QPen(QColor("#3fb950"), 1))
            elif self.is_end:
                label = "\u2212"
                painter.setPen(QPen(QColor("#f85149"), 1))
            else:
                label = str(self.order_in_string) if self.order_in_string else ""
                painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def hoverEnterEvent(self, event):
        self.setToolTip(
            f"Panel {self.panel_id}" +
            (f"\nString: {self.string_name}" if self.string_name else "\nUnassigned")
        )
        super().hoverEnterEvent(event)


class RoofSectionItem(QGraphicsPolygonItem):
    def __init__(self, section_id, points, name, angle, color: QColor):
        poly = QPolygonF([QPointF(p[0], p[1]) for p in points])
        super().__init__(poly)
        self.section_id = section_id
        self.name = name
        self.angle = angle
        fill = QColor(color)
        fill.setAlpha(45)
        self.setBrush(QBrush(fill))
        border = QColor(color)
        border.setAlpha(200)
        self.setPen(QPen(border, 2))
        self.setZValue(-1)  # behind panels

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        # Draw label at centroid
        pts = self.polygon()
        if pts.count() == 0:
            return
        cx = sum(p.x() for p in pts) / pts.count()
        cy = sum(p.y() for p in pts) / pts.count()
        painter.setPen(QPen(QColor("#e6edf3"), 1))
        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(cx - 60, cy - 20, 120, 40),
                         Qt.AlignmentFlag.AlignCenter,
                         f"{self.name}\n{self.angle}\u00b0")


class StringPathItem(QGraphicsPathItem):
    def __init__(self, points, color: QColor):
        path = QPainterPath()
        if points:
            path.moveTo(points[0])
            for pt in points[1:]:
                path.lineTo(pt)
        super().__init__(path)
        pen = QPen(color, 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 3])
        self.setPen(pen)
        self.setZValue(1)


class LayoutCanvas(QGraphicsView):
    sig_panel_clicked      = pyqtSignal(int)
    sig_manual_string_done = pyqtSignal(list)
    sig_roof_section_drawn = pyqtSignal(list)
    sig_selection_changed  = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QBrush(QColor("#0d1117")))
        self.setStyleSheet("border: 1px solid #30363d;")

        self._mode = MODE_SELECT
        self._panels: dict = {}          # panel_id -> item
        self._path_items: list = []
        self._section_items: dict = {}
        self._scale = 1.0

        # Roof-draw state
        self._draw_pts: list = []        # scene coords
        self._draw_dots: list = []
        self._draw_lines: list = []

        # Manual string state
        self._manual_pending: list = []  # panel ids in order
        self._manual_overlays: list = [] # temp number text items

        # Pan state
        self._panning = False
        self._pan_start = None
        self._space_held = False

    # -- Data loading --

    def load_panels(self, panels):
        """Load ParsedPanel list. Auto-scales from DXF to scene coords."""
        self._scene.clear()
        self._panels.clear()
        self._path_items.clear()
        self._section_items.clear()
        if not panels:
            return

        # Compute DXF bounding box
        minx = min(p.cx - p.width/2  for p in panels)
        miny = min(p.cy - p.height/2 for p in panels)
        maxx = max(p.cx + p.width/2  for p in panels)
        maxy = max(p.cy + p.height/2 for p in panels)
        dxf_w = maxx - minx or 1.0
        dxf_h = maxy - miny or 1.0

        # Target scene size ~1200 x 900
        sx = 1200.0 / dxf_w
        sy =  900.0 / dxf_h
        self._scale = min(sx, sy)
        s = self._scale

        for p in panels:
            # Flip Y: scene_y = (maxy - cy) * s  so top of DXF maps to top of screen
            scene_x = (p.cx - p.width/2  - minx) * s
            scene_y = (maxy - (p.cy + p.height/2)) * s
            w = p.width  * s
            h = p.height * s
            item = PanelItem(p.id, scene_x, scene_y, w, h, 0)
            self._scene.addItem(item)
            self._panels[p.id] = item

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-20, -20, 20, 20))
        self._dxf_bounds = (minx, miny, maxx, maxy)
        self.fit_view()

    def apply_strings(self, strings, panels):
        """Colour panels and draw connection paths."""
        # Clear old
        for item in self._path_items:
            self._scene.removeItem(item)
        self._path_items.clear()
        for item in self._panels.values():
            item.clearAssignment()

        for sr in strings:
            color = QColor(PANEL_COLORS[sr.color_index % len(PANEL_COLORS)])
            pts = []
            for i, pid in enumerate(sr.panels):
                item = self._panels.get(pid)
                if not item:
                    continue
                is_start = (i == 0)
                is_end   = (i == len(sr.panels) - 1)
                item.setAssignment(sr.name, i + 1, is_start, is_end, color)
                r = item.mapToScene(item.rect().center())
                pts.append(r)
            if len(pts) > 1:
                path_item = StringPathItem(pts, color)
                self._scene.addItem(path_item)
                self._path_items.append(path_item)

    def clear_strings(self):
        for item in self._path_items:
            self._scene.removeItem(item)
        self._path_items.clear()
        for item in self._panels.values():
            item.clearAssignment()

    def add_roof_section(self, section_id, scene_points, name, angle, color: QColor):
        item = RoofSectionItem(section_id, scene_points, name, angle, color)
        self._scene.addItem(item)
        self._section_items[section_id] = item

    def clear_roof_sections(self):
        for item in self._section_items.values():
            self._scene.removeItem(item)
        self._section_items.clear()

    def remove_roof_section(self, section_id):
        item = self._section_items.pop(section_id, None)
        if item:
            self._scene.removeItem(item)

    def fit_view(self):
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == MODE_ROOF_DRAW:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif mode == MODE_MANUAL:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def get_selected_panel_ids(self):
        return [item.panel_id for item in self._scene.selectedItems()
                if isinstance(item, PanelItem)]

    def highlight_string(self, panel_ids):
        for item in self._panels.values():
            item.setSelected(item.panel_id in panel_ids)

    def confirm_manual_string(self):
        ids = list(self._manual_pending)
        self._clear_manual_overlays()
        self._manual_pending.clear()
        if ids:
            self.sig_manual_string_done.emit(ids)

    def cancel_manual_string(self):
        self._clear_manual_overlays()
        self._manual_pending.clear()
        # un-highlight
        for pid, item in self._panels.items():
            if item.string_name is None:
                item.setBrush(QBrush(item._base_color))

    # -- Mouse / keyboard --

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._space_held = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif event.key() == Qt.Key.Key_Escape:
            if self._mode == MODE_ROOF_DRAW:
                self._cancel_roof_draw()
            elif self._mode == MODE_MANUAL:
                self.cancel_manual_string()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._mode == MODE_MANUAL:
                self.confirm_manual_string()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self._space_held = False
            if not self._panning:
                self.set_mode(self._mode)  # restore cursor
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton or (
            self._space_held and event.button() == Qt.MouseButton.LeftButton
        ):
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if self._mode == MODE_ROOF_DRAW and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.pos())
            self._draw_pts.append((sp.x(), sp.y()))
            dot = QGraphicsEllipseItem(sp.x()-3, sp.y()-3, 6, 6)
            dot.setBrush(QBrush(QColor("#f0883e")))
            dot.setPen(QPen(Qt.PenStyle.NoPen))
            dot.setZValue(5)
            self._scene.addItem(dot)
            self._draw_dots.append(dot)
            if len(self._draw_pts) > 1:
                p1 = self._draw_pts[-2]
                p2 = self._draw_pts[-1]
                ln = QGraphicsLineItem(p1[0], p1[1], p2[0], p2[1])
                ln.setPen(QPen(QColor("#f0883e"), 1.5, Qt.PenStyle.DashLine))
                ln.setZValue(5)
                self._scene.addItem(ln)
                self._draw_lines.append(ln)
            event.accept()
            return

        if self._mode == MODE_MANUAL and event.button() == Qt.MouseButton.LeftButton:
            sp = self.mapToScene(event.pos())
            for item in self._scene.items(sp):
                if isinstance(item, PanelItem):
                    pid = item.panel_id
                    if pid in self._manual_pending:
                        # toggle off
                        self._manual_pending.remove(pid)
                    else:
                        self._manual_pending.append(pid)
                    self._refresh_manual_overlays()
                    self.sig_panel_clicked.emit(pid)
                    break
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._mode == MODE_ROOF_DRAW and event.button() == Qt.MouseButton.LeftButton:
            if len(self._draw_pts) >= 3:
                pts = list(self._draw_pts)
                self._cancel_roof_draw()
                self.sig_roof_section_drawn.emit(pts)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning:
            self._panning = False
            self._pan_start = None
            if not self._space_held:
                self.set_mode(self._mode)
            event.accept()
            return

        if self._mode == MODE_SELECT:
            # Emit selection changed after rubber-band or single click
            ids = self.get_selected_panel_ids()
            self.sig_selection_changed.emit(ids)

        super().mouseReleaseEvent(event)

    # -- Internal helpers --

    def _cancel_roof_draw(self):
        for item in self._draw_dots + self._draw_lines:
            self._scene.removeItem(item)
        self._draw_dots.clear()
        self._draw_lines.clear()
        self._draw_pts.clear()

    def _clear_manual_overlays(self):
        for item in self._manual_overlays:
            self._scene.removeItem(item)
        self._manual_overlays.clear()
        # reset panel colours for unassigned
        for pid in self._manual_pending:
            item = self._panels.get(pid)
            if item and item.string_name is None:
                item.setBrush(QBrush(item._base_color))

    def _refresh_manual_overlays(self):
        self._clear_manual_overlays()
        for i, pid in enumerate(self._manual_pending):
            item = self._panels.get(pid)
            if not item:
                continue
            # Highlight the panel
            item.setBrush(QBrush(QColor("#f0883e")))
            # Number overlay
            r = item.sceneBoundingRect()
            txt = self._scene.addText(str(i + 1))
            txt.setDefaultTextColor(QColor("#ffffff"))
            f = QFont("Segoe UI", max(6, int(r.height() * 0.4)))
            f.setBold(True)
            txt.setFont(f)
            txt.setPos(r.center().x() - txt.boundingRect().width()/2,
                       r.center().y() - txt.boundingRect().height()/2)
            txt.setZValue(10)
            self._manual_overlays.append(txt)
