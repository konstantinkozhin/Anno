"""
ImageViewer — canvas widget with zoom, pan, box editing and selection modes.
"""
import math
from typing import List, Optional, Dict, Tuple

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QPoint, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QPainter, QPixmap, QPen, QColor, QFont, QMouseEvent, QKeyEvent,
    QBrush, QWheelEvent, QFontMetrics, QPolygonF, QPainterPath,
)

from ..models.data import Box, Line, Block
from ..theme import palette


class ImageViewer(QWidget):
    """Main image canvas with zoom/pan and annotation editing."""

    zoom_changed = pyqtSignal(int)
    box_changed = pyqtSignal()
    box_selected = pyqtSignal(int)
    selection_cleared = pyqtSignal()
    multi_selection_changed = pyqtSignal(list)

    HANDLE_SIZE = 8

    def __init__(self):
        super().__init__()
        self.image: Optional[QPixmap] = None
        self.boxes: List[Box] = []
        self.lines: List[Line] = []
        self.blocks: List[Block] = []
        self.default_line_ids: set = set()

        # Selection (Space-mode for creating lines) — REMOVED
        # Ctrl+click multi-selection (also used for line creation via Enter)
        self.multi_selected_boxes: List[int] = []
        self.is_ctrl_selection = False

        # Display toggles (persist across page switches)
        self.dim_non_boxes = False      # darken areas outside boxes
        self.show_labels = True         # show text labels on boxes

        # Highlight
        self.hover_box_id: Optional[int] = None
        self.current_line_id: Optional[int] = None
        self.current_block_id: Optional[int] = None

        # Paint-selection (drag to select/deselect via Ctrl+LMB)
        self.painted_boxes: set = set()
        self._painting_add_mode = True

        # Box editing
        self.edit_box_id: Optional[int] = None
        self.active_handle: Optional[str] = None
        self.is_resizing = False
        self.is_moving_box = False
        self.is_creating_box = False
        self.create_start_pos: Optional[Tuple[float, float]] = None
        self.new_box_data: Optional[Tuple[float, float, float, float]] = None
        self.wants_text_edit = False

        # Navigation
        self.zoom_level = 1.0
        self.pan_pos = QPoint(0, 0)
        self.last_mouse_pos = QPoint()
        self.is_panning = False

        self.setMouseTracking(True)
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Blink
        self.blink_timer = 0
        self.blink_visible = True

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def set_image(self, pixmap: QPixmap, boxes: List[Box], lines: List[Line],
                  blocks: List[Block] = None, preserve_view: bool = False):
        self.image = pixmap
        self.boxes = boxes
        self.lines = lines
        self.blocks = blocks or []
        self.default_line_ids = {ln.id for ln in self.lines if getattr(ln, 'is_default', False)}
        self.current_line_id = None
        self.current_block_id = None
        self.edit_box_id = None
        self.active_handle = None
        if not preserve_view:
            self.zoom_level = 1.0
            self.pan_pos = QPoint(0, 0)
        self.update()

    def adjust_zoom(self, factor: float):
        new = self.zoom_level * factor
        if 0.1 < new < 10.0:
            self.zoom_level = new
            self.update()
            self.zoom_changed.emit(int(self.zoom_level * 100))

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.pan_pos = QPoint(0, 0)
        self.update()
        self.zoom_changed.emit(100)

    # ------------------------------------------------------------------
    #  Coordinate helpers
    # ------------------------------------------------------------------

    def get_transform(self) -> Tuple[float, float, float]:
        if not self.image:
            return 1.0, 0.0, 0.0
        w_w, h_w = self.width(), self.height()
        w_i, h_i = self.image.width(), self.image.height()
        base = min(w_w / w_i, h_w / h_i)
        s = base * self.zoom_level
        dx = (w_w - w_i * s) / 2 + self.pan_pos.x()
        dy = (h_w - h_i * s) / 2 + self.pan_pos.y()
        return s, dx, dy

    def screen_to_image(self, pos: QPoint) -> Tuple[float, float]:
        s, dx, dy = self.get_transform()
        if s == 0:
            return -1, -1
        return (pos.x() - dx) / s, (pos.y() - dy) / s

    def image_to_screen(self, ix: float, iy: float) -> QPoint:
        s, dx, dy = self.get_transform()
        return QPoint(int(ix * s + dx), int(iy * s + dy))

    def get_handle_rects(self, box: Box) -> Dict[str, QRectF]:
        if not self.image:
            return {}
        r = box.get_rect(self.image.width(), self.image.height())
        s, dx, dy = self.get_transform()
        hs = self.HANDLE_SIZE
        corners = {
            "tl": (r.left(), r.top()), "tr": (r.right(), r.top()),
            "bl": (r.left(), r.bottom()), "br": (r.right(), r.bottom()),
        }
        return {
            n: QRectF(ix * s + dx - hs / 2, iy * s + dy - hs / 2, hs, hs)
            for n, (ix, iy) in corners.items()
        }

    def get_handle_at(self, pos: QPoint) -> Optional[str]:
        if self.edit_box_id is None:
            return None
        box = next((b for b in self.boxes if b.id == self.edit_box_id), None)
        if not box:
            return None
        for name, rect in self.get_handle_rects(box).items():
            if rect.contains(float(pos.x()), float(pos.y())):
                return name
        return None

    def get_box_at(self, pos: QPoint) -> Optional[Box]:
        if not self.image:
            return None
        ix, iy = self.screen_to_image(pos)
        w, h = self.image.width(), self.image.height()
        if ix < 0 or ix > w or iy < 0 or iy > h:
            return None
        for box in self.boxes:
            if box.get_rect(w, h).contains(ix, iy):
                return box
        return None

    # ------------------------------------------------------------------
    #  Paint
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(*palette().CANVAS_BG))

        if not self.image:
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "Загрузите папку с изображениями")
            return

        scale, dx, dy = self.get_transform()
        inv = 1.0 / scale
        w_img, h_img = self.image.width(), self.image.height()

        painter.save()
        painter.translate(dx, dy)
        painter.scale(scale, scale)

        # Image
        painter.drawPixmap(0, 0, self.image)

        # Dimming overlay (darken only areas OUTSIDE boxes)
        if self.dim_non_boxes:
            full = QPainterPath()
            full.addRect(QRectF(0, 0, w_img, h_img))
            boxes_path = QPainterPath()
            for bx in self.boxes:
                boxes_path.addRect(bx.get_rect(w_img, h_img))
            outside = full.subtracted(boxes_path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.drawPath(outside)

        # Colour wheel for line membership
        line_colors = [
            QColor(0, 255, 255), QColor(255, 0, 255), QColor(255, 255, 0),
            QColor(50, 255, 50), QColor(255, 100, 255), QColor(100, 255, 255),
        ]
        red_color = QColor(255, 50, 50)

        for box in self.boxes:
            rect = box.get_rect(w_img, h_img)

            # Base colour by line membership (default line = free)
            if box.line_id and box.line_id not in self.default_line_ids:
                idx = next((i for i, ln in enumerate(self.lines) if ln.id == box.line_id), 0)
                base_color = line_colors[idx % len(line_colors)]
            else:
                base_color = red_color

            is_selected = box.id in self.multi_selected_boxes
            is_hover = box.id == self.hover_box_id
            pen_width = 2 * inv
            pen = QPen(base_color, pen_width)
            brush = QBrush(Qt.BrushStyle.NoBrush)

            if box.line_id and box.line_id not in self.default_line_ids:
                c = QColor(base_color)
                c.setAlpha(50)
                brush = QBrush(c)

            if is_hover:
                pen = QPen(Qt.GlobalColor.yellow, 3 * inv)

            # Block highlight
            if self.current_block_id is not None:
                in_block = False
                for blk in self.blocks:
                    if blk.id == self.current_block_id:
                        in_block = box.line_id in blk.lines
                        break
                if in_block:
                    if self.blink_visible:
                        pen = QPen(QColor(255, 152, 0), 4 * inv)
                        brush = QBrush(QColor(255, 193, 7, 120))
                    else:
                        pen = QPen(QColor(255, 152, 0), 2 * inv)
                        brush = QBrush(QColor(255, 193, 7, 40))
            elif self.current_line_id is not None and box.line_id == self.current_line_id:
                if self.blink_visible:
                    pen = QPen(base_color.lighter(150), 4 * inv)
                    c = QColor(base_color); c.setAlpha(180)
                    brush = QBrush(c)
                else:
                    pen = QPen(base_color, 2 * inv)
                    c = QColor(base_color); c.setAlpha(60)
                    brush = QBrush(c)

            if is_selected:
                pen = QPen(QColor(palette().PURPLE), 3 * inv)
                _pc = QColor(palette().PURPLE); _pc.setAlpha(80)
                brush = QBrush(_pc)

            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawRect(rect)

            # Text / index label
            painter.save()
            cx, cy = rect.center().x(), rect.center().y()
            painter.translate(cx, cy)
            painter.scale(inv, inv)
            box_half_w = rect.width() * scale / 2
            box_half_h = rect.height() * scale / 2

            if is_selected:
                order = self.multi_selected_boxes.index(box.id) + 1
                painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
                tr = QRectF(-50, -50, 100, 100)
                painter.setPen(QPen(Qt.GlobalColor.black, 2))
                painter.drawText(tr.adjusted(2, 2, 2, 2), Qt.AlignmentFlag.AlignCenter, str(order))
                painter.setPen(Qt.GlobalColor.white)
                painter.drawText(tr, Qt.AlignmentFlag.AlignCenter, str(order))

            should_hide = is_selected or is_hover or box.id == self.edit_box_id or not self.show_labels
            if not should_hide and box.text:
                target_h = box_half_h * 2 * 0.7
                fs = max(6, min(50, int(target_h)))
                fm = QFontMetrics(QFont("Arial", fs))
                avail_w = box_half_w * 2 * 0.9
                tw = fm.horizontalAdvance(box.text)
                if tw > avail_w and avail_w > 0:
                    fs = max(6, int(fs * avail_w / tw))

                painter.setFont(QFont("Arial", fs))
                pad_x, pad_y = box_half_w * 0.05, box_half_h * 0.1
                lr = QRectF(-box_half_w + pad_x, -box_half_h + pad_y,
                            box_half_w * 2 - pad_x * 2, box_half_h * 2 - pad_y * 2)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(0, 0, 0, 180))
                painter.drawRect(lr)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(lr, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, box.text)

            painter.restore()

        # New box being created
        if self.is_creating_box and self.create_start_pos:
            ix2, iy2 = self.screen_to_image(self.last_mouse_pos)
            x1, y1 = self.create_start_pos
            cr = QRectF(min(x1, ix2), min(y1, iy2), abs(ix2 - x1), abs(iy2 - y1))
            painter.setPen(QPen(QColor(0, 255, 0), 2 * inv, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(0, 255, 0, 50)))
            painter.drawRect(cr)

        # Connection arrows for current line — drawn outside box rects
        if self.current_line_id:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            for line in self.lines:
                if line.id != self.current_line_id:
                    continue
                line_boxes = [b for bid in line.boxes for b in self.boxes if b.id == bid]
                if len(line_boxes) < 2:
                    break
                # Use clipping to draw only outside boxes
                clip_path = QPainterPath()
                clip_path.addRect(QRectF(0, 0, w_img, h_img))
                for bx in line_boxes:
                    clip_path.addRect(bx.get_rect(w_img, h_img))
                clip_path.setFillRule(Qt.FillRule.OddEvenFill)
                painter.setClipPath(clip_path)
                # Arrow color: bright contrasting
                arrow_color = QColor(255, 200, 60, 240)
                painter.setPen(QPen(arrow_color, 3 * inv))
                painter.setBrush(QBrush(arrow_color))
                for i in range(len(line_boxes) - 1):
                    r1 = line_boxes[i].get_rect(w_img, h_img)
                    r2 = line_boxes[i + 1].get_rect(w_img, h_img)
                    p1 = r1.center()
                    p2 = r2.center()
                    painter.drawLine(p1, p2)
                    angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                    asz = 10 * inv
                    arrow = QPolygonF([
                        QPointF(p2.x(), p2.y()),
                        QPointF(p2.x() - asz * math.cos(angle - math.pi / 6),
                                p2.y() - asz * math.sin(angle - math.pi / 6)),
                        QPointF(p2.x() - asz * math.cos(angle + math.pi / 6),
                                p2.y() - asz * math.sin(angle + math.pi / 6)),
                    ])
                    painter.drawPolygon(arrow)
                painter.setClipping(False)

        painter.restore()

        # Handles for edit box (screen coords)
        if self.edit_box_id is not None:
            eb = next((b for b in self.boxes if b.id == self.edit_box_id), None)
            if eb:
                r = eb.get_rect(w_img, h_img)
                sr = QRectF(r.x() * scale + dx, r.y() * scale + dy,
                            r.width() * scale, r.height() * scale)
                painter.setPen(QPen(QColor(0, 255, 0), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(sr)
                for _, hr in self.get_handle_rects(eb).items():
                    painter.setPen(QPen(Qt.GlobalColor.white, 1))
                    painter.setBrush(QBrush(QColor(0, 150, 255)))
                    painter.drawRect(hr)

        # Multi-selection counter pill
        if self.multi_selected_boxes:
            from ..theme import palette as _pal, Font as _Font
            _pp = _pal()
            count = len(self.multi_selected_boxes)
            banner_text = f"  Выбрано: {count}  ·  Enter — создать строку  ·  Esc — отмена  "
            font = QFont(_Font.FAMILY, 11, QFont.Weight.DemiBold)
            painter.setFont(font)
            fm = painter.fontMetrics()
            tw = fm.horizontalAdvance(banner_text) + 28
            th = fm.height() + 12
            bx = (self.width() - tw) // 2
            by = 10
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 40))
            painter.drawRoundedRect(bx + 2, by + 2, tw, th, th // 2, th // 2)
            bg = QColor(_pp.PURPLE)
            bg.setAlpha(210)
            painter.setBrush(bg)
            painter.drawRoundedRect(bx, by, tw, th, th // 2, th // 2)
            painter.setPen(QColor(_pp.TEXT_ON_ACC))
            painter.drawText(bx, by, tw, th, Qt.AlignmentFlag.AlignCenter, banner_text)

    # ------------------------------------------------------------------
    #  Wheel
    # ------------------------------------------------------------------

    def wheelEvent(self, event: QWheelEvent):
        self.adjust_zoom(1.1 if event.angleDelta().y() > 0 else 0.9)

    # ------------------------------------------------------------------
    #  Mouse
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
        self.last_mouse_pos = event.pos()

        if event.button() == Qt.MouseButton.RightButton:
            self.is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        # Ctrl+LMB → multi-select
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            box = self.get_box_at(event.pos())
            if box:
                if self.edit_box_id is not None and self.edit_box_id not in self.multi_selected_boxes:
                    self.multi_selected_boxes.append(self.edit_box_id)
                self.edit_box_id = None
                self.current_line_id = None
                self.current_block_id = None
                self.is_ctrl_selection = True
                self.painted_boxes = set()
                if box.id in self.multi_selected_boxes:
                    self.multi_selected_boxes.remove(box.id)
                    self._painting_add_mode = False
                else:
                    self.multi_selected_boxes.append(box.id)
                    self._painting_add_mode = True
                self.painted_boxes.add(box.id)
                self.multi_selection_changed.emit(self.multi_selected_boxes.copy())
                self.update()
            return

        handle = self.get_handle_at(event.pos())
        if handle:
            self.active_handle = handle
            self.is_resizing = True
            self.setCursor(Qt.CursorShape.SizeFDiagCursor if handle in ("tl", "br")
                           else Qt.CursorShape.SizeBDiagCursor)
            return

        box = self.get_box_at(event.pos())
        if box:
            if self.multi_selected_boxes:
                self.multi_selected_boxes = []
                self.multi_selection_changed.emit([])
            if box.id == self.edit_box_id:
                self.is_moving_box = True
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.edit_box_id = box.id
                self.current_line_id = None
                self.current_block_id = None
                self.box_selected.emit(box.id)
                self.update()
        else:
            if self.multi_selected_boxes:
                self.multi_selected_boxes = []
                self.multi_selection_changed.emit([])
            self.edit_box_id = None
            self.current_line_id = None
            self.current_block_id = None
            self.selection_cleared.emit()
            ix, iy = self.screen_to_image(event.pos())
            if self.image and 0 <= ix <= self.image.width() and 0 <= iy <= self.image.height():
                self.is_creating_box = True
                self.create_start_pos = (ix, iy)
                self.setCursor(Qt.CursorShape.CrossCursor)
                self.update()
            else:
                self.is_panning = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            box = self.get_box_at(event.pos())
            if box:
                self.edit_box_id = box.id
                self.wants_text_edit = True
                self.box_selected.emit(box.id)
                self.update()
                self.box_changed.emit()

    def mouseMoveEvent(self, event: QMouseEvent):
        # Ctrl+LMB paint-select
        if self.is_ctrl_selection:
            box = self.get_box_at(event.pos())
            if box and box.id not in self.painted_boxes:
                self.painted_boxes.add(box.id)
                if self._painting_add_mode:
                    if box.id not in self.multi_selected_boxes:
                        self.multi_selected_boxes.append(box.id)
                else:
                    if box.id in self.multi_selected_boxes:
                        self.multi_selected_boxes.remove(box.id)
                self.multi_selection_changed.emit(self.multi_selected_boxes.copy())
                self.update()
            self.last_mouse_pos = event.pos()
            return

        if self.is_resizing and self.edit_box_id is not None:
            box = next((b for b in self.boxes if b.id == self.edit_box_id), None)
            if box and self.image:
                ix, iy = self.screen_to_image(event.pos())
                wi, hi = self.image.width(), self.image.height()
                r = box.get_rect(wi, hi)
                l, t, ri2, bt = r.left(), r.top(), r.right(), r.bottom()
                if self.active_handle == "tl": l, t = ix, iy
                elif self.active_handle == "tr": ri2, t = ix, iy
                elif self.active_handle == "bl": l, bt = ix, iy
                elif self.active_handle == "br": ri2, bt = ix, iy
                if ri2 - l < 10: ri2 = l + 10
                if bt - t < 10: bt = t + 10
                box.width = (ri2 - l) / wi
                box.height = (bt - t) / hi
                box.x_center = (l + ri2) / 2 / wi
                box.y_center = (t + bt) / 2 / hi
                self.update()

        elif self.is_moving_box and self.edit_box_id is not None:
            box = next((b for b in self.boxes if b.id == self.edit_box_id), None)
            if box and self.image:
                delta = event.pos() - self.last_mouse_pos
                s, _, _ = self.get_transform()
                box.x_center += delta.x() / s / self.image.width()
                box.y_center += delta.y() / s / self.image.height()
                self.last_mouse_pos = event.pos()
                self.update()

        elif self.is_creating_box:
            self.last_mouse_pos = event.pos()
            self.update()

        elif self.is_panning:
            self.pan_pos += event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.update()

        else:
            handle = self.get_handle_at(event.pos())
            if handle:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor if handle in ("tl", "br")
                               else Qt.CursorShape.SizeBDiagCursor)
            else:
                box = self.get_box_at(event.pos())
                new_hover = box.id if box else None
                if new_hover != self.hover_box_id:
                    self.hover_box_id = new_hover
                    self.update()
                self.setCursor(Qt.CursorShape.PointingHandCursor if self.hover_box_id
                               else Qt.CursorShape.ArrowCursor)
            self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            if self.is_panning:
                self.is_panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self.is_resizing and self.edit_box_id is not None:
            self.box_changed.emit()
            self.is_resizing = False
            self.active_handle = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

        elif self.is_moving_box and self.edit_box_id is not None:
            self.box_changed.emit()
            self.is_moving_box = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

        elif self.is_creating_box and self.create_start_pos:
            ix, iy = self.screen_to_image(event.pos())
            x1, y1 = self.create_start_pos
            if abs(ix - x1) > 10 and abs(iy - y1) > 10 and self.image:
                wi, hi = self.image.width(), self.image.height()
                l, t = min(x1, ix), min(y1, iy)
                r, b = max(x1, ix), max(y1, iy)
                self.new_box_data = ((l + r) / 2 / wi, (t + b) / 2 / hi,
                                     (r - l) / wi, (b - t) / hi)
                self.box_changed.emit()
            self.is_creating_box = False
            self.create_start_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

        elif self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

        elif self.is_ctrl_selection:
            self.is_ctrl_selection = False
            self.painted_boxes.clear()

    # ------------------------------------------------------------------
    #  Key events — forwarded to MainWindow
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent):
        parent = self.window()
        if parent and parent != self:
            QApplication.sendEvent(parent, event)
        else:
            super().keyPressEvent(event)
