"""
LineWidget & BlockWidget — container widgets for the structure panel.
"""
from typing import Optional

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QMimeData
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QDrag, QPolygon, QMouseEvent
from PyQt6 import sip

from ..theme import Styles, palette
from .base import DragGrip, StructurePanelMixin
from .chips import WordChip


# ======================================================================
#  LineWidget
# ======================================================================

class LineWidget(StructurePanelMixin, QFrame):
    """A row of word-chips representing one text line."""

    line_clicked = pyqtSignal(int)
    line_ctrl_clicked = pyqtSignal(int)
    word_clicked = pyqtSignal(int)
    word_double_clicked = pyqtSignal(int)
    word_ctrl_clicked = pyqtSignal(int)

    def __init__(self, line_id: int, text: str, draggable: bool = True, parent=None):
        super().__init__(parent)
        self.line_id = line_id
        self._selected = False
        self._draggable = draggable
        self._drag_start_pos = None
        self._was_dragged = False
        self._drop_insert_pos = -1
        self.setAcceptDrops(True)

        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 5, 10, 5)
        layout.setSpacing(5)

        if draggable and line_id >= 0:
            self.grip = DragGrip()
            self.grip.mousePressEvent = self._grip_pressed
            self.grip.mouseMoveEvent = self._grip_moved
            self.grip.mouseReleaseEvent = self._grip_released
            layout.addWidget(self.grip)

        self.words_layout = QHBoxLayout()
        self.words_layout.setSpacing(5)
        layout.addLayout(self.words_layout)
        layout.addStretch()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # -- Public API --

    def add_word(self, box_id: int, text: str):
        chip = WordChip(box_id, text)
        chip.clicked.connect(self.word_clicked.emit)
        chip.double_clicked.connect(self.word_double_clicked.emit)
        chip.ctrl_clicked.connect(self.word_ctrl_clicked.emit)
        self.words_layout.addWidget(chip)

    def setSelected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    # -- Style --

    def _apply_style(self):
        self.setStyleSheet(Styles.line_selected() if self._selected else Styles.line_normal())

    # -- Mouse on empty space --

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            # Walk up to check if the clicked widget is inside a WordChip or DragGrip
            w = child
            is_interactive = False
            while w is not None and w is not self:
                if isinstance(w, (WordChip, DragGrip)):
                    is_interactive = True
                    break
                w = w.parentWidget()
            # Emit line click only when clicking truly empty space
            if not is_interactive:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.line_ctrl_clicked.emit(self.line_id)
                else:
                    panel = self._find_structure_panel()
                    if not (panel and self.line_id in panel.multi_selected_line_ids):
                        self.line_clicked.emit(self.line_id)
                event.accept()
                return
        super().mousePressEvent(event)

    # -- Grip drag logic --

    def _grip_pressed(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.line_ctrl_clicked.emit(self.line_id)
            self._drag_start_pos = None
            self._was_dragged = False
        else:
            self._drag_start_pos = event.pos()
            self._was_dragged = False
            panel = self._find_structure_panel()
            if not (panel and self.line_id in panel.multi_selected_line_ids):
                self.line_clicked.emit(self.line_id)

    def _grip_released(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._was_dragged and self._drag_start_pos is not None:
                panel = self._find_structure_panel()
                if panel and self.line_id in panel.multi_selected_line_ids:
                    self.line_clicked.emit(self.line_id)
            self._drag_start_pos = None
            self._was_dragged = False

    def _grip_moved(self, event):
        if not self._draggable or not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return
        self._was_dragged = True
        try:
            if sip.isdeleted(self):
                return
            drag = QDrag(self)
            mime = QMimeData()

            panel = self._find_structure_panel()
            if panel and self.line_id in panel.multi_selected_line_ids:
                ids_str = ",".join(str(lid) for lid in panel.multi_selected_line_ids)
                mime.setText(f"lines:{ids_str}")
                pixmap = self._composite_lines_pixmap(panel)
            else:
                mime.setText(f"line:{self.line_id}")
                pixmap = self.grab()

            drag.setMimeData(mime)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(10, pixmap.height() // 2))
            drag.exec(Qt.DropAction.MoveAction)
        except RuntimeError:
            pass
        except Exception as e:
            print(f"[LineWidget] drag error: {e}")
        finally:
            self._drag_start_pos = None

    def _composite_lines_pixmap(self, panel) -> QPixmap:
        parts = []
        for lid in panel.multi_selected_line_ids:
            key = ("line", lid)
            if key in panel._widgets_map:
                parts.append(panel._widgets_map[key].grab())
        if not parts:
            return self.grab()
        max_w = max(p.width() for p in parts)
        total_h = sum(p.height() for p in parts)
        composite = QPixmap(max_w, total_h)
        composite.fill(Qt.GlobalColor.transparent)
        painter = QPainter(composite)
        y = 0
        for p in parts:
            painter.drawPixmap(0, y, p)
            y += p.height()
        painter.end()
        return composite

    # -- Drag-drop for words landing on this line --

    def _get_insert_position(self, x: float) -> int:
        for i in range(self.words_layout.count()):
            item = self.words_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if x < w.x() + w.width() / 2:
                    return i
        return self.words_layout.count()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("word:") or t.startswith("words:"):
                event.acceptProposedAction()
                self.setStyleSheet(Styles.line_drop_target())

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("word:") or t.startswith("words:"):
                event.acceptProposedAction()
                self._drop_insert_pos = self._get_insert_position(event.position().x())
                self.update()

    def dragLeaveEvent(self, event):
        self._drop_insert_pos = -1
        self._apply_style()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drop_insert_pos < 0:
            return
        painter = QPainter(self)
        dnd_color = QColor(palette().DND_LINE)
        painter.setPen(QPen(dnd_color, 3))
        # Calculate initial x from first widget or layout geometry
        first_item = self.words_layout.itemAt(0)
        x_pos = first_item.widget().x() - 2 if (first_item and first_item.widget()) else self.words_layout.geometry().x()
        for i in range(min(self._drop_insert_pos, self.words_layout.count())):
            item = self.words_layout.itemAt(i)
            if item and item.widget():
                x_pos = item.widget().x() + item.widget().width() + 2
        painter.drawLine(int(x_pos), 4, int(x_pos), self.height() - 4)
        painter.setBrush(dnd_color)
        painter.drawPolygon(QPolygon([
            QPoint(int(x_pos) - 5, 2),
            QPoint(int(x_pos) + 5, 2),
            QPoint(int(x_pos), 8),
        ]))
        painter.end()

    def dropEvent(self, event):
        insert_pos = self._drop_insert_pos if self._drop_insert_pos >= 0 else self._get_insert_position(event.position().x())
        self._drop_insert_pos = -1
        self._apply_style()
        try:
            text = event.mimeData().text()
            panel = self._find_structure_panel()
            if text.startswith("words:") and self.line_id >= 0:
                box_ids = [int(x) for x in text.split(":")[1].split(",")]
                if panel:
                    panel.words_dropped_on_line.emit(box_ids, self.line_id, insert_pos)
                event.acceptProposedAction()
            elif text.startswith("word:") and self.line_id >= 0:
                box_id = int(text.split(":")[1])
                if panel:
                    panel.word_dropped_on_line.emit(box_id, self.line_id, insert_pos)
                event.acceptProposedAction()
        except Exception as e:
            print(f"[LineWidget] drop error: {e}")


# ======================================================================
#  BlockWidget
# ======================================================================

class BlockWidget(StructurePanelMixin, QFrame):
    """Visual block — a titled container of LineWidgets."""

    block_clicked = pyqtSignal(int)
    block_double_clicked = pyqtSignal(int)
    line_clicked = pyqtSignal(int)
    line_ctrl_clicked = pyqtSignal(int)
    word_clicked = pyqtSignal(int)
    word_double_clicked = pyqtSignal(int)
    word_ctrl_clicked = pyqtSignal(int)

    def __init__(self, block_id: int, name: str, parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self._selected = False
        self._drag_start_pos = None
        self._drop_insert_pos = -1
        self._is_drag_over = False
        self.setAcceptDrops(True)
        self._apply_style()

        # Card elevation shadow
        from ..theme import shadow_color
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(shadow_color())
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        self.grip = DragGrip()
        self.grip.mousePressEvent = self._grip_pressed
        self.grip.mouseMoveEvent = self._grip_moved
        header_layout.addWidget(self.grip)

        self.header = QLabel(f"{name}")
        self.header.setStyleSheet(Styles.block_header())
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = lambda e: self.block_clicked.emit(self.block_id)
        self.header.mouseDoubleClickEvent = lambda e: self.block_double_clicked.emit(self.block_id)
        header_layout.addWidget(self.header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.lines_layout = QVBoxLayout()
        self.lines_layout.setSpacing(2)
        layout.addLayout(self.lines_layout)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # -- Public API --

    def add_line_widget(self, line_widget: "LineWidget"):
        line_widget.line_clicked.connect(self.line_clicked.emit)
        line_widget.line_ctrl_clicked.connect(self.line_ctrl_clicked.emit)
        line_widget.word_clicked.connect(self.word_clicked.emit)
        line_widget.word_double_clicked.connect(self.word_double_clicked.emit)
        line_widget.word_ctrl_clicked.connect(self.word_ctrl_clicked.emit)
        self.lines_layout.addWidget(line_widget)

        panel = self._find_structure_panel()
        if panel:
            panel._widgets_map[("line", line_widget.line_id)] = line_widget

    def setSelected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    # -- Style --

    def _apply_style(self):
        self.setStyleSheet(Styles.block_selected() if self._selected else Styles.block_normal())

    # -- Mouse --

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            if child is None or child == self.header or isinstance(child, DragGrip):
                self.block_clicked.emit(self.block_id)
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            if child is None or child == self.header or isinstance(child, DragGrip):
                self.block_double_clicked.emit(self.block_id)
                return
        super().mouseDoubleClickEvent(event)

    # -- Grip drag --

    def _grip_pressed(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.block_clicked.emit(self.block_id)

    def _grip_moved(self, event):
        if not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < 10:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"block:{self.block_id}")
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(QPoint(10, 15))
        drag.exec(Qt.DropAction.MoveAction)
        self._drag_start_pos = None

    # -- Drag-drop for lines landing on this block --

    def _get_insert_position(self, y: float) -> int:
        for i in range(self.lines_layout.count()):
            w = self.lines_layout.itemAt(i).widget()
            if w and y < w.y() + w.height() / 2:
                return i
        return self.lines_layout.count()

    def _find_line_widget(self, line_id: int) -> Optional["LineWidget"]:
        for i in range(self.lines_layout.count()):
            w = self.lines_layout.itemAt(i).widget()
            if isinstance(w, LineWidget) and w.line_id == line_id:
                return w
        return None

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("line:") or t.startswith("lines:") or t.startswith("word:"):
                event.acceptProposedAction()
                self._is_drag_over = True
                self._drop_insert_pos = -1
                self.setStyleSheet(Styles.block_drop_target())

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            t = event.mimeData().text()
            if t.startswith("line:") or t.startswith("lines:"):
                new_pos = self._get_insert_position(event.position().y())
                if new_pos != self._drop_insert_pos:
                    self._drop_insert_pos = new_pos
                    self.update()
                event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._is_drag_over = False
        self._drop_insert_pos = -1
        self._apply_style()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not (self._is_drag_over and self._drop_insert_pos >= 0 and self.lines_layout.count() > 0):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(palette().DND_BLOCK)
        painter.setPen(QPen(color, 2))
        painter.setBrush(color)

        margin_l, margin_r = 8, 8

        # Y coordinate of the indicator
        if self._drop_insert_pos == 0:
            first = self.lines_layout.itemAt(0).widget()
            indicator_y = first.y() - 2 if first else 0
        elif self._drop_insert_pos >= self.lines_layout.count():
            last = self.lines_layout.itemAt(self.lines_layout.count() - 1).widget()
            indicator_y = (last.y() + last.height() + 2) if last else 0
        else:
            w = self.lines_layout.itemAt(self._drop_insert_pos).widget()
            indicator_y = w.y() - 2 if w else 0

        left = margin_l
        right = self.width() - margin_r
        painter.drawLine(int(left), int(indicator_y), int(right), int(indicator_y))

        ts = 5
        painter.drawPolygon(QPolygon([
            QPoint(int(left), int(indicator_y)),
            QPoint(int(left - ts), int(indicator_y - ts)),
            QPoint(int(left - ts), int(indicator_y + ts)),
        ]))
        painter.drawPolygon(QPolygon([
            QPoint(int(right), int(indicator_y)),
            QPoint(int(right + ts), int(indicator_y - ts)),
            QPoint(int(right + ts), int(indicator_y + ts)),
        ]))
        painter.end()

    def dropEvent(self, event):
        self._is_drag_over = False
        self._drop_insert_pos = -1
        self._apply_style()
        self.update()
        try:
            text = event.mimeData().text()
            panel = self._find_structure_panel()

            if text.startswith("lines:") and panel:
                ids = [int(x) for x in text.split(":")[1].split(",")]
                panel.lines_dropped_on_block.emit(ids, self.block_id)
                event.acceptProposedAction()
            elif text.startswith("line:") and panel:
                line_id = int(text.split(":")[1])
                drop_y = event.position().y()
                insert_pos = self._get_insert_position(drop_y)

                existing = self._find_line_widget(line_id)
                if existing:
                    original_pos = -1
                    for i in range(self.lines_layout.count()):
                        w = self.lines_layout.itemAt(i).widget()
                        if isinstance(w, LineWidget) and w.line_id == line_id:
                            original_pos = i
                            break
                    if 0 <= original_pos < insert_pos:
                        insert_pos -= 1
                    panel.line_reorder.emit(line_id, self.block_id, insert_pos)
                else:
                    panel.line_dropped_on_block_at_pos.emit(line_id, self.block_id, insert_pos)
                event.acceptProposedAction()
        except Exception as e:
            print(f"[BlockWidget] drop error: {e}")
